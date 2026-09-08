## Summary

This workflow extracts one or more frames from a video file and, optionally, generates a concise natural-language caption for each extracted frame using a vision-capable language model. It bridges a codec operation (ffmpeg frame extraction) with an LLM captioning step in a single declarative pipeline, making it easy to index, search, or describe video content without manual inspection. Data engineers, media archivists, and application developers building video-understanding pipelines are the primary beneficiaries.

---

## Detailed Specification

### 1. Purpose

Extract a frame (or set of frames) from a video file and optionally produce a short visual description of the extracted frame using a multimodal LLM, returning the frame path as the primary output.

---

### 2. High-level Description

`video_to_image` is a linear media-processing WORKFLOW that chains a codec side-effect with an optional LLM vision call. The workflow accepts a VIDEO input along with extraction parameters — mode, timestamp, fps, and max-frames — and dispatches to a `CALL extract_frame(...)` tool via an `EVALUATE @mode` branch that covers five named modes: `first`, `middle`, `last`, `timestamp`, and `sample`; the `timestamp` branch passes the explicit `@timestamp` argument, while all other modes pass the mode string itself. A second `EVALUATE @caption` branch then conditionally fires a `GENERATE caption_frame(...)` call using the `caption_frame` CREATE FUNCTION, which instructs a vision model to produce a sub-100-word description of the frame in context; when captioning is disabled, the caption variable is assigned an empty string. Three typed EXCEPTION handlers provide graceful degradation: `FileNotFound` and `InvalidTimestamp` both `RETURN` with `status = 'failed'`, while `ModelUnavailable` falls back to returning the raw frame with `status = 'partial'`, preserving the codec output even when the LLM tier is unavailable. The DODA principle is respected throughout — the `.spl` file never names a specific ffmpeg command or model endpoint; physical execution details live entirely in `run.py` and the `--model` parameter.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW video_to_image` | `WORKFLOW` | Top-level named workflow; takes VIDEO input, emits IMAGE output |
| `CREATE FUNCTION caption_frame` | `CREATE FUNCTION` | Reusable prompt template; parameterized over `frame IMAGE` and `context TEXT` |
| `CALL extract_frame(...) INTO @frame` | `CALL` | Side-effect tool call; performs ffmpeg extraction, binds result path to `@frame` |
| `GENERATE caption_frame(...) INTO @frame_caption` | `GENERATE` | LLM call with budget cap (256 tokens) and dynamic `@model` selection |
| `EVALUATE @mode WHEN = 'timestamp' THEN ... ELSE ... END` | `EVALUATE` | Branches on extraction mode; two arms cover timestamp vs. all keyword modes |
| `EVALUATE @caption WHEN = TRUE THEN ... ELSE ... END` | `EVALUATE` | Boolean gate for optional captioning step |
| `@frame_caption := ''` | shared state (`@var` assignment) | Direct variable assignment when caption is skipped |
| `RETURN @frame WITH status = 'failed'` | `RETURN WITH status=` | Non-trivial termination status — drives error signalling to callers |
| `RETURN @frame WITH status = 'partial'` | `RETURN WITH status=` | Partial-success path when vision model is unavailable |
| `EXCEPTION WHEN FileNotFound THEN ...` | `EXCEPTION` | Typed handler for missing video file |
| `EXCEPTION WHEN InvalidTimestamp THEN ...` | `EXCEPTION` | Typed handler for out-of-range timestamp |
| `EXCEPTION WHEN ModelUnavailable THEN ...` | `EXCEPTION` | Typed handler for caption model failure; returns frame without caption |
| `LOGGING ... LEVEL INFO/DEBUG/WARN/ERROR` | `LOGGING` | Structured observability at each stage; no effect on data flow |

---

### 4. Logical Functions / Prompts

#### `caption_frame`

- **Role:** Produces a concise visual description of a single extracted video frame for downstream indexing, search, or display.
- **Prompt conventions:**
  - System persona: "precise visual analyst."
  - Accepts `{context}` slot — free-text description of the video (e.g. title, scene metadata) to anchor the model's interpretation.
  - Output format: prose, under 100 words; covers subjects, actions, environment, visible text, and notable details.
  - Output budget: capped at 256 tokens via `WITH OUTPUT BUDGET 256 TOKENS` to enforce brevity.
  - Model is runtime-configurable via `@model` (default `gemma4`), so any vision-capable Ollama model can be substituted without changing the spec.

---

### 5. Control Flow

1. **Entry** — log the video path and extraction mode.
2. **Frame extraction** — `EVALUATE @mode`: if `@mode = 'timestamp'`, `CALL extract_frame(@video, @timestamp, @output_dir)` into `@frame`; otherwise `CALL extract_frame(@video, @mode, @output_dir)` into `@frame`. Both arms emit an INFO log.
3. **Caption gate** — `EVALUATE @caption`: if `TRUE`, `GENERATE caption_frame(@frame, @context)` into `@frame_caption` (DEBUG log before, INFO log after); if `FALSE`, assign `@frame_caption := ''`.
4. **Normal termination** — log completion, `RETURN @frame` (caption is available in `@frame_caption` as side state but the declared OUTPUT is the IMAGE path).
5. **Exception paths:**
   - `FileNotFound` → log ERROR, `RETURN '[ERROR] ...' WITH status = 'failed'`
   - `InvalidTimestamp` → log ERROR, `RETURN '[ERROR] ...' WITH status = 'failed'`
   - `ModelUnavailable` → log WARN, `RETURN @frame WITH status = 'partial'` (frame is preserved; caption is absent)

There is no WHILE loop; execution is a single linear pass with two conditional branches.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (paste Section 2, High-level Description, as input)
spl3 text2spl --description "video_to_image is a linear media-processing WORKFLOW that chains
a codec side-effect with an optional LLM vision call. The workflow accepts a VIDEO input along
with extraction parameters — mode, timestamp, fps, and max-frames — and dispatches to a
CALL extract_frame(...) tool via an EVALUATE @mode branch that covers five named modes: first,
middle, last, timestamp, and sample. A second EVALUATE @caption branch conditionally fires a
GENERATE caption_frame(...) call using a CREATE FUNCTION that instructs a vision model to
produce a sub-100-word frame description. Three typed EXCEPTION handlers cover FileNotFound,
InvalidTimestamp (both return status=failed), and ModelUnavailable (returns frame with
status=partial)." --mode workflow

# Step 2 — compile to any target
spl3 splc compile video_to_image.spl --lang python/pocketflow
spl3 splc compile video_to_image.spl --lang python/langgraph
spl3 splc compile video_to_image.spl --lang go
```