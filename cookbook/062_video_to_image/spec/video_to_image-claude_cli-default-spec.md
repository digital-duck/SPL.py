## Summary

This workflow extracts one or more frames from a video file and optionally generates a natural-language caption for each extracted frame using a multimodal vision model. It serves as a bridge between the codec layer (FFmpeg) and the LLM layer (Gemma4 vision), converting video assets into annotated image artifacts. Media engineers, content pipelines, and downstream analysis tools benefit from a single, declarative entry point for video-to-image extraction with optional semantic labeling.

---

## Detailed Specification

### 1. Purpose

Extract one or more frames from a video file as image artifacts, with an optional vision-language captioning step that appends a concise natural-language description to the result.

---

### 2. High-level Description

The `video_to_image` WORKFLOW accepts a video file path and a set of extraction parameters, then dispatches to one of five extraction modes — `first`, `middle`, `last`, `timestamp`, or `sample` — using an EVALUATE branch that selects either a timestamp-targeted CALL or a mode-named CALL to the `extract_frame` codec tool, storing the result in the shared variable `@frame`. If the `@caption` flag is TRUE, a second EVALUATE branch invokes GENERATE on the `caption_frame` function, which sends the extracted frame and an optional context string to a configurable vision model (defaulting to `gemma4`) with an output budget capped at 256 tokens, storing the result in `@frame_caption`; when captioning is skipped, `@frame_caption` is set to an empty string. The workflow uses no WHILE loop because extraction is a single-shot operation regardless of mode. Three named EXCEPTION handlers cover the principal failure classes: `FileNotFound` and `InvalidTimestamp` both RETURN an error string WITH `status = 'failed'`, while `ModelUnavailable` performs a graceful degradation by returning the raw `@frame` WITH `status = 'partial'`, preserving the extracted image even when the caption model is offline. Throughout execution, structured LOGGING at INFO, DEBUG, and WARN levels traces each significant state transition, including the chosen mode, the extracted frame path, and the generated caption text.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW video_to_image` | `WORKFLOW <name>` | Top-level orchestration unit with typed INPUT/OUTPUT declarations |
| `CREATE FUNCTION caption_frame` | `CREATE FUNCTION <name>` | Reusable prompt template with `{frame}` and `{context}` slots; returns TEXT |
| `CALL extract_frame(...) INTO @frame` | `CALL <tool>(...) INTO @<var>` | Side-effect codec call (FFmpeg); not an LLM call |
| `GENERATE caption_frame(@frame, @context) INTO @frame_caption` | `GENERATE <fn>(...) INTO @<var>` | LLM inference call; uses `WITH OUTPUT BUDGET` and `USING MODEL` modifiers |
| `EVALUATE @mode WHEN = 'timestamp'` | `EVALUATE @<var> WHEN ... THEN ... ELSE ... END` | Dispatch on extraction mode string |
| `EVALUATE @caption WHEN = TRUE` | `EVALUATE @<var> WHEN ... THEN ... ELSE ... END` | Conditional captioning gate |
| `@frame`, `@frame_caption`, `@mode`, `@caption` | Shared state via SPL `@<var>` | All variables in shared workflow scope |
| `EXCEPTION WHEN FileNotFound` | `EXCEPTION WHEN <Type> THEN` | Hard failure; RETURN WITH `status = 'failed'` |
| `EXCEPTION WHEN InvalidTimestamp` | `EXCEPTION WHEN <Type> THEN` | Hard failure; RETURN WITH `status = 'failed'` |
| `EXCEPTION WHEN ModelUnavailable` | `EXCEPTION WHEN <Type> THEN` | Soft failure; RETURN WITH `status = 'partial'` (frame preserved, caption absent) |
| `RETURN @frame WITH status = 'partial'` | `RETURN @<var> WITH <k>=<v>` | Non-trivial status token drives caller-side degradation logic |
| `RETURN ... WITH status = 'failed'` | `RETURN @<var> WITH <k>=<v>` | Non-trivial status token signals hard error to caller |

---

### 4. Logical Functions / Prompts

#### `caption_frame`

- **Role**: Generates a concise natural-language description of a single extracted video frame using a multimodal (vision) model.
- **Key prompt conventions**:
  - Persona: "precise visual analyst."
  - Accepts an optional free-text `{context}` string describing the source video to ground the description.
  - Output structure: three implicit sub-questions (what is happening, key subjects/actions/environment, any text or notable details).
  - Hard length sentinel: "Keep the description under 100 words" — enforced at the prompt level, complemented by the SPL-level `OUTPUT BUDGET 256 TOKENS` cap.
  - Output format: plain prose TEXT; no JSON, no scoring, no structured tokens.
  - Model: configurable via `@model` (default `gemma4`); must support image input (vision-capable).

---

### 5. Control Flow

**Execution path:**

1. **Entry** — log the video path and selected mode at INFO level.
2. **Frame extraction branch** (`EVALUATE @mode`) — if `@mode = 'timestamp'`, CALL `extract_frame` with the literal `@timestamp` value; otherwise CALL `extract_frame` with the mode name as the position specifier. Both branches store the result in `@frame` and emit an INFO log.
3. **Caption gate** (`EVALUATE @caption`) — if `@caption = TRUE`, GENERATE `caption_frame(@frame, @context)` with a 256-token output budget on `@model`, storing the result in `@frame_caption` and emitting INFO; otherwise assign `@frame_caption := ''` with no LLM call.
4. **Termination** — log the final frame path at INFO, then RETURN `@frame` (the primary output; `@frame_caption` is a side artifact available in shared state).
5. **Exception paths** — `FileNotFound` and `InvalidTimestamp` short-circuit to RETURN WITH `status = 'failed'`; `ModelUnavailable` allows the workflow to complete with the extracted frame and RETURN WITH `status = 'partial'`.

There is no WHILE loop; the workflow is a single-pass pipeline with two conditional branches and three exception exits.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Extract one or more frames from a video file as image artifacts, with an optional vision-language captioning step that appends a concise natural-language description to the result." --mode workflow

# Step 2 — compile to any target
spl3 splc compile video_to_image.spl --lang python/pocketflow
spl3 splc compile video_to_image.spl --lang python/langgraph
spl3 splc compile video_to_image.spl --lang go
```