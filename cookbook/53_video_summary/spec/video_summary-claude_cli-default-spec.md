## Summary

Recipe 60 is a multimodal video-understanding workflow that accepts a video file and a processing mode, then dispatches a single LLM call to produce a human-readable result — either a narrative summary, a verbatim timestamped transcript, a ranked key-moments list, or a chapter breakdown. It is built for local execution on Ollama-hosted models (gemma4) and targets both Python and Go runtimes on low-power hardware. Content creators, researchers, and media teams benefit by automating video comprehension without sending footage to external cloud services.

---

## Detailed Specification

### 1. Purpose

Analyse a user-supplied video clip using a locally hosted multimodal model and return a structured text output in one of four styles: concise summary, verbatim transcript, key moments, or chapter markers.

---

### 2. High-level Description

The workflow `video_summary` accepts a `VIDEO` input alongside four configuration parameters — `@mode`, `@style`, `@model`, and `@output_budget` — and routes each request through a single EVALUATE branch before issuing one GENERATE call. Four CREATE FUNCTIONs serve as prompt templates: `summarise_video` instructs the model to narrate the main subject, chronological events, setting, and audio content in a caller-specified style; `transcribe_video` demands verbatim speech output formatted as `[MM:SS] Speaker: text` with `[?]` and `[NO SPEECH]` sentinel tokens for uncertain or absent audio; `key_moments` elicits a numbered, timestamp-ordered list of significant moments with a significance rationale for each; and `chapter_breakdown` produces structured Markdown chapter markers with titles and short descriptions. The EVALUATE on `@mode` dispatches to the matching GENERATE call (`'summary'`, `'transcript'`, `'key_moments'`, `'chapters'`), with the `ELSE` clause falling back to `summarise_video` for unrecognised modes. Every GENERATE call is constrained by `@output_budget` tokens and targets the `gemma4` multimodal model served via Ollama. Structured logging bookends execution at INFO level, and two EXCEPTION handlers catch `ModelUnavailable` and `FileNotFound`, each logging at ERROR level and RETURNing a literal error string with `status = 'failed'`.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW video_summary` | `WORKFLOW` | Single named workflow; inputs declared with defaults, output typed as `TEXT` |
| `CREATE FUNCTION summarise_video` | `CREATE FUNCTION` | Prompt template for narrative summary; `{style}` param slot controls register |
| `CREATE FUNCTION transcribe_video` | `CREATE FUNCTION` | Prompt template for verbatim transcript; uses `[?]` and `[NO SPEECH]` sentinel tokens |
| `CREATE FUNCTION key_moments` | `CREATE FUNCTION` | Prompt template for timestamped key-moment extraction |
| `CREATE FUNCTION chapter_breakdown` | `CREATE FUNCTION` | Prompt template for Markdown chapter markers |
| `EVALUATE @mode WHEN = '...' THEN ... ELSE ... END` | `EVALUATE` | Four-way dispatch on `@mode`; ELSE provides safe fallback to summary |
| `GENERATE <fn>(...) INTO @result` | `GENERATE` | Single LLM call per request; result stored in `@result` shared variable |
| `WITH OUTPUT BUDGET @output_budget TOKENS` | `GENERATE` option | Token cap applied uniformly across all branches |
| `USING MODEL @model` | `GENERATE` option | Model identity injected at runtime (default: `gemma4:e4b` via Ollama) |
| `@clip, @mode, @style, @model, @output_budget, @log_dir` | `@vars` (shared state) | Workflow-scoped variables threaded through EVALUATE and GENERATE |
| `LOGGING ... LEVEL INFO/ERROR` | `LOGGING` | Structured log lines at workflow entry, exit, and exception paths |
| `EXCEPTION WHEN ModelUnavailable THEN ... RETURN WITH status='failed'` | `EXCEPTION` | Named handler; non-trivial RETURN status drives failure signalling |
| `EXCEPTION WHEN FileNotFound THEN ... RETURN WITH status='failed'` | `EXCEPTION` | Named handler; same failure-status pattern for missing video file |

---

### 4. Logical Functions / Prompts

**`summarise_video(clip VIDEO, style TEXT)`**
- Role: Primary summary path; generates a narrative account of the video.
- Key conventions: The `{style}` slot (e.g. `'concise paragraph'`, `'bullet points'`) controls register and format. Instructs the model to cover subject, chronological events, setting/visual tone, audio content (summarised, not verbatim), and conclusion. No sentinel tokens.

**`transcribe_video(clip VIDEO)`**
- Role: Verbatim speech extraction with timestamps.
- Key conventions: Output format is `[MM:SS] Speaker (if identifiable): text`. Sentinel tokens: `[?]` marks unclear speech; `[NO SPEECH]` is output when the video contains no speech. These tokens are parseable by downstream consumers.

**`key_moments(clip VIDEO)`**
- Role: Editorial distillation — surfaces the most significant moments.
- Key conventions: Numbered list ordered by timestamp `[MM:SS]`. Each entry includes a one-line description and an explicit significance rationale. No sentinel tokens; structure is prose-list.

**`chapter_breakdown(clip VIDEO)`**
- Role: Chapter-marker generation for navigation and indexing.
- Key conventions: Output is structured Markdown. Each chapter entry contains a start timestamp, a concise title (3–6 words), and a 1–2 sentence description. Suitable for direct injection into video players or documentation systems.

---

### 5. Control Flow

1. **Entry** — workflow starts, logs `clip`, `mode`, and `model` at INFO level.
2. **EVALUATE `@mode`** — single branch decision:
   - `'summary'` → GENERATE `summarise_video(@clip, @style)` INTO `@result`
   - `'transcript'` → GENERATE `transcribe_video(@clip)` INTO `@result`
   - `'key_moments'` → GENERATE `key_moments(@clip)` INTO `@result`
   - `'chapters'` → GENERATE `chapter_breakdown(@clip)` INTO `@result`
   - `ELSE` → GENERATE `summarise_video(@clip, @style)` INTO `@result` (safe default)
3. **Exit logging** — logs output length at INFO level.
4. **RETURN `@result`** — implicit success, no status token (linear termination).
5. **EXCEPTION `ModelUnavailable`** — logs error, RETURNs literal error string WITH `status = 'failed'`.
6. **EXCEPTION `FileNotFound`** — logs error, RETURNs literal error string WITH `status = 'failed'`.

There is no WHILE loop; this is a single-pass, single-LLM-call workflow. The only non-trivial RETURN tokens are `status = 'failed'` in the two exception handlers.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "<paste Section 2 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile video_summary.spl --lang python/ollama
spl3 splc compile video_summary.spl --lang python/pocketflow
spl3 splc compile video_summary.spl --lang go
```