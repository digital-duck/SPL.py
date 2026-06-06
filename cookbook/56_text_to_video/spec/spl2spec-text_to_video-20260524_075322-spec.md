## Summary

This workflow accepts a short text description and generates a video clip using cloud-based AI video models (Google Veo 2, RunwayML Gen-3, or Kling AI). Before sending the prompt to the video backend, it optionally uses a language model to enrich the description with cinematic detail, camera motion, and lighting cues. Non-technical users (creative directors, educators, researchers) benefit from a clean declarative interface that abstracts away provider-specific video APIs.

---

## Detailed Specification

### 1. Purpose

Convert a plain-text description into a short video clip by optionally enriching the prompt with an LLM and then delegating generation to a cloud video model.

---

### 2. High-level Description

The `text_to_video` WORKFLOW accepts six user-facing inputs — a base prompt, visual style, aspect ratio, duration in seconds, an enhancement toggle, and model selectors for both the language model and video backend — plus two path inputs for output and log directories. Control flow begins with an EVALUATE on the `@enhance` boolean: when TRUE, a GENERATE call invokes the `enhance_video_prompt` CREATE FUNCTION to produce a cinematic rewrite of the raw prompt (capped at 512 output tokens via an OUTPUT BUDGET constraint), storing the result in `@final_prompt`; when FALSE, `@final_prompt` is assigned the original prompt directly. The workflow then RETURNs `@final_prompt` to the physical runner (`run.py`), which is responsible for calling the chosen video backend and writing the resulting file to `@output_dir` — VIDEO generation is explicitly out-of-SPL-scope and handled at the infrastructure layer, consistent with the DODA principle. Two typed EXCEPTION handlers guard the pipeline: `ModelUnavailable` traps an unreachable video backend and RETURNs with `status = 'failed'`, while `BudgetExceeded` catches token-limit overruns during prompt enhancement and RETURNs the unenhanced original with `status = 'budget_limit'`.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `CREATE FUNCTION enhance_video_prompt` | `CREATE FUNCTION` | Prompt template with four `{param}` slots; returns TEXT; acts as the sole LLM-facing prompt |
| `WORKFLOW text_to_video` | `WORKFLOW` | Top-level orchestration unit with typed `INPUT:` / `OUTPUT:` declarations |
| `GENERATE enhance_video_prompt(...) INTO @final_prompt` | `GENERATE` | Single LLM call; result bound to `@final_prompt`; guarded by a 512-token OUTPUT BUDGET |
| `@final_prompt := @prompt` | shared state (`@var` assignment) | Direct variable assignment used in the ELSE branch; no LLM call |
| `EVALUATE @enhance WHEN = TRUE THEN ... ELSE ... END` | `EVALUATE` | Boolean branch driving whether the GENERATE step executes |
| `RETURN @final_prompt` | `RETURN` | Hands the enriched (or raw) prompt to the physical runner for video synthesis |
| `RETURN ... WITH status = 'failed'` | `RETURN WITH status=` | Non-trivial token; signals video-model failure to the caller |
| `RETURN @prompt WITH status = 'budget_limit'` | `RETURN WITH status=` | Non-trivial token; signals token-budget overrun; caller receives the unenriched prompt |
| `EXCEPTION WHEN ModelUnavailable` | `EXCEPTION WHEN` | Typed handler for unreachable video backend |
| `EXCEPTION WHEN BudgetExceeded` | `EXCEPTION WHEN` | Typed handler for prompt-enhancement token overflow |
| `LOGGING ... LEVEL INFO/DEBUG/WARN/ERROR` | side-effect (CALL equivalent) | Structured diagnostic emissions at four severity levels |

---

### 4. Logical Functions / Prompts

#### `enhance_video_prompt`

- **Role:** Rewrites a bare user prompt into a production-ready video generation prompt before it reaches the video model. This is the only LLM call in the workflow.
- **Key prompt conventions:**
  - Persona: "professional prompt engineer for AI video generation models."
  - Four injected parameters: `{prompt}`, `{style}`, `{duration}`, `{aspect}`.
  - Explicit instruction to describe **motion**, **camera movement**, **temporal progression**, **lighting**, and **camera angle** (wide shot, close-up, tracking shot).
  - Hard length cap: "under 250 words."
  - Sentinel instruction: "Return ONLY the enhanced prompt, no explanation" — prevents conversational wrapping that would corrupt the downstream video API call.
  - Output budget enforced at the SPL level: `WITH OUTPUT BUDGET 512 TOKENS`.

---

### 5. Control Flow

```
START
  │
  ├─ LOGGING: workflow entry (INFO)
  │
  ├─ EVALUATE @enhance
  │     ├─ TRUE  →  GENERATE enhance_video_prompt(...)
  │     │               WITH OUTPUT BUDGET 512 TOKENS
  │     │               USING MODEL @llm_model
  │     │               INTO @final_prompt
  │     │           LOGGING: prompt enhanced (DEBUG)
  │     │
  │     └─ FALSE →  @final_prompt := @prompt
  │
  ├─ LOGGING: video generation request (INFO)
  │
  └─ RETURN @final_prompt
        → physical runner (run.py) calls video backend, writes file to @output_dir

EXCEPTION WHEN ModelUnavailable
  └─ LOGGING (ERROR) → RETURN '[ERROR] ...' WITH status='failed'

EXCEPTION WHEN BudgetExceeded
  └─ LOGGING (WARN)  → RETURN @prompt WITH status='budget_limit'
```

There is no WHILE loop; the workflow is a single-pass linear pipeline with one conditional branch and two exception exits. The non-trivial RETURN status tokens (`'failed'`, `'budget_limit'`) are meaningful to the caller and must be handled upstream.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (paste Section 2 as text2spl input)
spl3 text2spl --description "Convert a plain-text description into a short video clip \
  by optionally enriching the prompt with an LLM and then delegating generation to a \
  cloud video model. The workflow accepts a base prompt, visual style, aspect ratio, \
  duration, an enhancement toggle, and model selectors. An EVALUATE on the enhance \
  boolean gates a GENERATE call to enhance_video_prompt (cinematic rewrite, 512-token \
  budget). The final prompt is RETURNed to an external runner. EXCEPTION handlers cover \
  ModelUnavailable (status=failed) and BudgetExceeded (status=budget_limit)." \
  --mode workflow --adapter ollama -m gemma3

# Step 2 — compile to any target
spl3 splc compile text_to_video.spl --lang python/pocketflow
spl3 splc compile text_to_video.spl --lang python/langgraph
spl3 splc compile text_to_video.spl --lang go
```