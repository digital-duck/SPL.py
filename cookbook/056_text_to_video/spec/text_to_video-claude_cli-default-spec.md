## Summary

This workflow accepts a plain-text description and optional style parameters, optionally enriches the prompt through a language model, and hands the polished prompt to a cloud video-generation backend (Google Veo 2, RunwayML Gen-3, or Kling AI) to produce a short video clip. It exists because raw user prompts rarely contain the cinematic detail that video models need, so an LLM enhancement step bridges that gap automatically. Content creators and developers building multimodal pipelines are the primary beneficiaries.

---

## Detailed Specification

### 1. Purpose

Generate a short video clip from a user-supplied text prompt by optionally enriching it with a language model before dispatching it to a cloud video-generation service.

---

### 2. High-level Description

The `text_to_video` WORKFLOW accepts a text prompt, a visual style string, an aspect-ratio preference, a duration in seconds, a boolean enhancement flag, a choice of video-generation backend, and output/log directory paths. At startup it logs the incoming parameters at INFO level. It then performs an EVALUATE on the boolean `@enhance` flag: when TRUE it issues a GENERATE call to the `enhance_video_prompt` function using the configured LLM (default `gemma4`) with an output budget capped at 512 tokens, storing the enriched text in `@final_prompt`; when FALSE it assigns the original prompt directly to `@final_prompt`. The `enhance_video_prompt` CREATE FUNCTION is a structured prompt template that instructs the LLM to add motion, camera movement, lighting, mood, and temporal detail while keeping the result under 250 words and returning only the enhanced prompt with no surrounding explanation. After enhancement, the workflow logs a second INFO message and RETURNs `@final_prompt` to the physical runner (`run.py`), which calls the selected video-generation backend and persists the output file. Two named EXCEPTION handlers guard the workflow: `ModelUnavailable` logs an ERROR and RETURNs with `status='failed'`, and `BudgetExceeded` logs a WARN and RETURNs the raw original prompt with `status='budget_limit'`, allowing callers to distinguish hard failures from graceful degradation.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW text_to_video` | `WORKFLOW text_to_video` | Top-level orchestration unit; INPUT/OUTPUT declarations define typed interface |
| `CREATE FUNCTION enhance_video_prompt` | `CREATE FUNCTION enhance_video_prompt(prompt, style, duration, aspect)` | Reusable prompt template with four `{param}` slots; returns TEXT |
| `GENERATE enhance_video_prompt(...) INTO @final_prompt` | `GENERATE <fn>(...) INTO @<var>` | LLM call bounded by `WITH OUTPUT BUDGET 512 TOKENS USING MODEL @llm_model` |
| `EVALUATE @enhance WHEN = TRUE` | `EVALUATE @<var> WHEN ... THEN ... ELSE ... END` | Branches on a boolean flag, not LLM output; ELSE path is a direct assignment |
| `@final_prompt := @prompt` | shared-state `@<var>` assignment | SPL variable assignment within the ELSE branch |
| `LOGGING ... LEVEL INFO/DEBUG/WARN/ERROR` | `LOGGING` side-effect | Structured log emission; not a CALL tool but a built-in side-effect |
| `RETURN @final_prompt` | `RETURN @<var>` | Hands `@final_prompt` to the physical runner; no status token — implicit linear termination |
| `RETURN ... WITH status='failed'` | `RETURN @<var> WITH status=<value>` | Non-trivial status; signals hard model failure to the caller |
| `RETURN @prompt WITH status='budget_limit'` | `RETURN @<var> WITH status=<value>` | Non-trivial status; signals graceful degradation — raw prompt returned instead |
| `EXCEPTION WHEN ModelUnavailable` | `EXCEPTION WHEN <Type> THEN ...` | Named handler for backend unavailability |
| `EXCEPTION WHEN BudgetExceeded` | `EXCEPTION WHEN <Type> THEN ...` | Named handler for token-budget overflow during enhancement |

---

### 4. Logical Functions / Prompts

**`enhance_video_prompt`**

- **Role:** Pre-processing / prompt enrichment. Transforms a short, informal user description into a detailed cinematic prompt suitable for video-generation models.
- **Key prompt conventions:**
  - System persona: "professional prompt engineer for AI video generation models."
  - Four labelled input slots rendered inline: `Original prompt`, `Desired style`, `Duration`, `Aspect ratio`.
  - Explicit rules block: mandates motion/camera/temporal description, lighting and mood, camera angle taxonomy (wide shot, close-up, tracking shot), a 250-word hard cap, and a sentinel output constraint — "Return ONLY the enhanced prompt, no explanation" — to prevent wrapper text from polluting the video-model input.
  - Output format: plain TEXT, no JSON, no markdown.

---

### 5. Control Flow

1. **Entry:** WORKFLOW begins; INPUT variables are bound to supplied or default values.
2. **Logging:** INFO log records prompt, style, and duration.
3. **Branch (EVALUATE):** If `@enhance = TRUE`, a GENERATE call invokes `enhance_video_prompt` via `@llm_model`; on success, `@final_prompt` holds the enriched text and a DEBUG log is emitted. If `@enhance = FALSE`, `@final_prompt` is assigned the raw `@prompt` directly — no LLM call is made.
4. **Handoff:** INFO log records the chosen `@video_model`, duration, and aspect ratio; RETURN passes `@final_prompt` to the physical runner, which executes the actual video-generation API call and writes the output file to `@output_dir`.
5. **Exception — `ModelUnavailable`:** Intercepts backend failure; logs ERROR; RETURNs a literal error string with `status='failed'`.
6. **Exception — `BudgetExceeded`:** Intercepts token-budget overflow during the GENERATE step; logs WARN; RETURNs the original `@prompt` unchanged with `status='budget_limit'`, preserving the pipeline with degraded quality rather than failing entirely.

There is no WHILE loop; the workflow is a single-pass pipeline with one conditional branch and two exception exits.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "Generate a short video clip from a user-supplied text prompt by \
  optionally enriching it with a language model before dispatching it to a cloud \
  video-generation service. Use a CREATE FUNCTION enhance_video_prompt with params \
  (prompt, style, duration, aspect) that instructs the LLM to add cinematic detail, \
  motion, camera angle, lighting, and mood, capped at 250 words, returning only the \
  enhanced prompt. The WORKFLOW text_to_video takes @prompt, @style, @aspect, \
  @duration, @enhance, @video_model, @llm_model, @output_dir, @log_dir as INPUT and \
  outputs @video_path VIDEO. EVALUATE @enhance: when TRUE, GENERATE \
  enhance_video_prompt(...) WITH OUTPUT BUDGET 512 TOKENS USING MODEL @llm_model INTO \
  @final_prompt; ELSE assign @final_prompt := @prompt. RETURN @final_prompt to the \
  physical runner. Handle EXCEPTION ModelUnavailable with status='failed' and \
  EXCEPTION BudgetExceeded returning raw prompt with status='budget_limit'." \
  --mode workflow

# Step 2 — compile to any target
spl3 splc compile text_to_video.spl --lang python/pocketflow
spl3 splc compile text_to_video.spl --lang python/langgraph
spl3 splc compile text_to_video.spl --lang go
```