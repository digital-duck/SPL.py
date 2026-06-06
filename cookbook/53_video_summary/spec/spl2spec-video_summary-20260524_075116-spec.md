## Summary

This workflow accepts a video file or URL and produces one of four text outputs — a narrative summary, a verbatim transcript with timestamps, a structured list of key moments, or a chapter-style breakdown — depending on a caller-supplied mode flag. It exists to give developers and content teams a single, model-agnostic entry point for video understanding without writing any multimodal inference code themselves. Non-technical stakeholders benefit because the output format is always plain text, ready to paste into a document, feed into a downstream workflow, or display in a UI.

---

## Detailed Specification

### 1. Purpose

Analyse a video clip using a native multimodal LLM and return one of four structured text analyses — summary, transcript, key moments, or chapter breakdown — based on a caller-specified mode.

---

### 2. High-level Description

The `video_summary` WORKFLOW accepts a `VIDEO` input alongside four control parameters (`mode`, `style`, `model`, `output_budget`) and produces a single `TEXT` result. It delegates all analysis to one of four CREATE FUNCTIONs — `summarise_video`, `transcribe_video`, `key_moments`, or `chapter_breakdown` — each carrying a tightly-scoped system prompt that instructs the LLM to adopt a specific analyst persona. Control flow is expressed as a single EVALUATE branch on `@mode`, routing the VIDEO to exactly one GENERATE call with a configurable token budget and model; there is no iteration or refinement loop. The ELSE branch of EVALUATE falls back to `summarise_video` so the workflow never exits without a result under a valid model. Two EXCEPTION handlers cover the primary failure modes — `ModelUnavailable` and `FileNotFound` — both logging an error and returning a typed failure status via `RETURN WITH status='failed'`, allowing a calling WORKFLOW to detect and recover. The `VIDEO` type is a first-class SPL 3.0 type, so the executor dispatches to `generate_multimodal()` automatically; no caller-side codec work is required.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW video_summary` | `WORKFLOW` | Top-level named orchestration unit with `INPUT:`/`OUTPUT:` declarations |
| `CREATE FUNCTION summarise_video` | `CREATE FUNCTION` | Prompt template; `{style}` slot injected at call time |
| `CREATE FUNCTION transcribe_video` | `CREATE FUNCTION` | Fixed prompt; no parameterised slots beyond the VIDEO clip |
| `CREATE FUNCTION key_moments` | `CREATE FUNCTION` | Fixed prompt; requests numbered, timestamp-ordered list |
| `CREATE FUNCTION chapter_breakdown` | `CREATE FUNCTION` | Fixed prompt; requests structured Markdown output |
| `EVALUATE @mode WHEN = '...' THEN ... END` | `EVALUATE` | String-equality branch (not LLM-evaluated); routes to one of four GENERATE calls |
| `GENERATE fn(@clip, ...) INTO @result` | `GENERATE ... INTO @var` | Single multimodal LLM call; VIDEO type triggers `generate_multimodal()` dispatch |
| `WITH OUTPUT BUDGET @output_budget TOKENS` | token budget parameter | Passed through to the adapter as `max_tokens` |
| `USING MODEL @model` | model selection | Runtime model binding; default `gemma4:e4b` |
| `@clip`, `@mode`, `@result`, etc. | `@var` shared state | All variables live in the workflow frame; `@result` is the OUTPUT binding |
| `EXCEPTION WHEN ModelUnavailable THEN` | `EXCEPTION WHEN` | Named error handler; logs and returns typed failure |
| `EXCEPTION WHEN FileNotFound THEN` | `EXCEPTION WHEN` | Named error handler; logs and returns typed failure |
| `RETURN @result` | implicit OUTPUT binding | Linear exit; no status token, result bound to declared `OUTPUT:` var |
| `RETURN '...' WITH status='failed'` | `RETURN WITH status=` | Non-trivial status — signals failure to any calling WORKFLOW |

---

### 4. Logical Functions / Prompts

**`summarise_video(clip VIDEO, style TEXT)`**
- **Role:** Primary analysis function; produces a narrative overview of the video.
- **Key prompt conventions:** Instructs the LLM to adopt a "video analyst" persona. Uses a fixed five-point coverage list (subject, key events, setting, audio content, conclusion). The `{style}` slot lets the caller switch between "concise paragraph", "bullet points", or any free-text style directive. No sentinel tokens or scoring.

**`transcribe_video(clip VIDEO)`**
- **Role:** Speech-to-text extraction with timestamps; produces a verbatim transcript.
- **Key prompt conventions:** Persona is "accurate transcription engine". Output format is `[MM:SS] Speaker: text`. Defines two sentinel behaviours: `[?]` for unclear speech, `[NO SPEECH]` when audio contains no speech. No parameterised slots.

**`key_moments(clip VIDEO)`**
- **Role:** Editorial curation; identifies the most significant moments in the video.
- **Key prompt conventions:** Persona is "video editor". Output is a numbered list ordered by timestamp, each entry containing timestamp, one-line description, and significance rationale. No parameterised slots.

**`chapter_breakdown(clip VIDEO)`**
- **Role:** Navigation aid; divides video into logical chapters for indexing or playback UI.
- **Key prompt conventions:** Persona is "video producer". Each chapter includes start timestamp, a 3–6 word title, and a 1–2 sentence description. Output format is structured Markdown. No parameterised slots.

---

### 5. Control Flow

1. **Entry:** WORKFLOW receives `@clip`, `@mode`, `@style`, `@model`, `@output_budget`, `@log_dir`; logs the call parameters at INFO level.
2. **Branch (EVALUATE):** `@mode` is compared by string equality against `'summary'`, `'transcript'`, `'key_moments'`, and `'chapters'`. Exactly one matching arm executes its GENERATE call and writes the result into `@result`. If `@mode` matches none, the ELSE arm calls `summarise_video` as the safe default.
3. **GENERATE:** Each arm issues a single multimodal LLM call. The VIDEO input causes the executor to use `generate_multimodal()`; the token budget and model are passed as adapter kwargs.
4. **Exit (normal):** `@result` is logged (output length) and returned as the declared OUTPUT. No iteration; no quality gate.
5. **Exit (exception):** If `ModelUnavailable` fires (model not loaded or unreachable), or `FileNotFound` fires (clip path invalid), the handler logs an ERROR-level message and issues `RETURN WITH status='failed'`, giving the caller a typed signal to handle rather than an unhandled exception.

There is no WHILE loop and no iterative refinement — this is a single-shot inference workflow.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Analyse a video clip using a native multimodal LLM and return one of four structured text analyses — summary, transcript, key moments, or chapter breakdown — based on a caller-specified mode." --mode workflow

# Step 2 — compile to any target
spl3 splc compile video_summary.spl --lang python/ollama
spl3 splc compile video_summary.spl --lang python/langgraph
spl3 splc compile video_summary.spl --lang go
```