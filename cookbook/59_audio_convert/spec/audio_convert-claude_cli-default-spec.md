## Summary

This workflow wraps a deterministic audio format conversion operation (WAV, MP3, OGG, FLAC, M4A) in a composable, loggable SPL shell so it can be invoked via `CALL` from any higher-level orchestrator workflow. No LLM is involved; the SPL layer exists purely to provide structured logging, typed I/O, and named exception handling around an `ffmpeg`/`pydub` codec operation. Audio engineers and pipeline builders benefit by getting a reusable, observable building block rather than raw subprocess glue code.

---

## Detailed Specification

### 1. Purpose

Convert a source audio file to a specified target format with configurable bitrate and sample rate, returning the path of the converted file or a structured error status.

---

### 2. High-level Description

The `audio_convert` WORKFLOW accepts a source audio path, a target format string, bitrate, sample rate, an output directory, and a log directory as typed INPUT variables. Because the conversion is entirely deterministic — no language model judgment is required — the workflow contains no GENERATE calls; its core action is a single CALL to the `convert_audio` tool, which delegates to `pydub` and `ffmpeg` at the physical execution layer. Structured LOGGING statements bracket the CALL, recording the conversion parameters on entry and the output path on success at INFO level. There is no WHILE loop and no EVALUATE branch on the happy path; control flow is strictly linear from logging through CALL to RETURN of the converted file. Three named EXCEPTION handlers intercept `FileNotFound`, `UnsupportedFormat`, and `CodecError` conditions, each emitting an ERROR-level log and terminating with `RETURN … WITH status = 'failed'` so that any calling orchestrator can inspect the non-trivial status token and decide whether to retry, skip, or surface the failure. The workflow is designed as a composable primitive: it declares `OUTPUT: @converted AUDIO` so that a parent workflow (e.g. a voice-dialogue post-processor) can chain it with `CALL audio_convert(…) INTO @converted`.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW audio_convert` | `WORKFLOW audio_convert` | Top-level named workflow; composable via `CALL` from parent orchestrators |
| `INPUT:` block | Typed parameter declarations | Six typed inputs: `AUDIO`, `TEXT` (×3), `INT`; all carry DEFAULT values |
| `OUTPUT: @converted AUDIO` | Typed return declaration | Declares the single output variable and its type |
| `CALL convert_audio(…) INTO @converted` | `CALL <tool>(…) INTO @<var>` | Side-effect tool call; no LLM; delegates to pydub + ffmpeg |
| `LOGGING … LEVEL INFO/ERROR` | `LOGGING` statement | Structured log with f-string interpolation; INFO on happy path, ERROR in exceptions |
| `EXCEPTION WHEN FileNotFound THEN …` | `EXCEPTION WHEN <Type> THEN …` | Named handler for missing source file |
| `EXCEPTION WHEN UnsupportedFormat THEN …` | `EXCEPTION WHEN <Type> THEN …` | Named handler for unrecognised format string |
| `EXCEPTION WHEN CodecError THEN …` | `EXCEPTION WHEN <Type> THEN …` | Named handler for ffmpeg/codec failures |
| `RETURN … WITH status = 'failed'` | `RETURN @<var> WITH <k>=<v>` | Non-trivial status token; signals failure to calling orchestrator |
| `@audio`, `@target_format`, `@bitrate`, etc. | Shared `@<var>` state | Passed through to CALL and interpolated in LOGGING f-strings |

---

### 4. Logical Functions / Prompts

This workflow contains **no LLM prompt templates** (`CREATE FUNCTION` / `GENERATE`). The single callable is:

**`convert_audio` — codec tool**

- **Role:** Executes the actual format conversion; reads `@audio`, writes the result to `@output_dir`, returns the output file path into `@converted`.
- **Key conventions:** Accepts `@target_format` as a format-extension string (e.g. `'mp3'`), `@bitrate` as a codec bitrate string (e.g. `'192k'`), and `@sample_rate` as an integer Hz value. Raises typed exceptions (`FileNotFound`, `UnsupportedFormat`, `CodecError`) that map directly to the EXCEPTION handlers.

---

### 5. Control Flow

```
START
  │
  ├─ LOGGING (INFO): log source path, target format, bitrate, sample_rate
  │
  ├─ CALL convert_audio(…) INTO @converted
  │       │
  │       ├─ FileNotFound  → LOGGING (ERROR) → RETURN WITH status='failed'
  │       ├─ UnsupportedFormat → LOGGING (ERROR) → RETURN WITH status='failed'
  │       └─ CodecError    → LOGGING (ERROR) → RETURN WITH status='failed'
  │
  ├─ LOGGING (INFO): log output path
  │
  └─ RETURN @converted
```

There is no WHILE loop and no EVALUATE branch. The three EXCEPTION paths each terminate immediately with `status = 'failed'`, which is the only non-trivial status token in the workflow; the happy path returns the converted audio path with no explicit status metadata.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Convert a source audio file to a specified target format \
  with configurable bitrate and sample rate, returning the path of the converted file \
  or a structured error status." --mode workflow

# Step 2 — compile to any target
spl3 splc compile audio_convert.spl --lang python/pocketflow
spl3 splc compile audio_convert.spl --lang python/langgraph
spl3 splc compile audio_convert.spl --lang go
```