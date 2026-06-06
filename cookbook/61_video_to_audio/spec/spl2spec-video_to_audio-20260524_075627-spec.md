## Summary

This workflow extracts the audio track from a video file and saves it as a standalone audio file in a configurable format (MP3, WAV, or FLAC). It exists to bridge video content into audio-only pipelines — for example, feeding extracted audio into a transcription or summarization workflow. Media engineers, data scientists, and content pipeline builders benefit from having a composable, format-agnostic audio extraction step they can chain with downstream recipes.

---

## Detailed Specification

### 1. Purpose

Extract the audio track from a video file and return the path to the resulting audio file, ready for downstream consumption by audio-processing workflows.

### 2. High-level Description

This workflow implements a deterministic, LLM-free codec operation using a single CALL to a tool function (`extract_audio`) that delegates to ffmpeg. The WORKFLOW accepts a VIDEO input along with codec parameters — target format, bitrate, sample rate, and output directory — and returns an AUDIO output path. Because no LLM inference is involved, there are no GENERATE steps, no WHILE loops, and no EVALUATE branches; the control flow is a straight line: log → extract → log → RETURN. Three EXCEPTION handlers guard the failure modes that ffmpeg-based extraction can produce: a missing source file (`FileNotFound`), a video with no audio stream (`NoAudioTrack`), and a codec or installation failure (`CodecError`). Each exception terminates the workflow with a descriptive error string and `status = 'failed'`, allowing a calling orchestrator to detect failure via the non-trivial RETURN status. The workflow is designed as a composable building block: its AUDIO output can be piped directly into recipe 51 (audio summary) or recipe 55 (voice dialogue) via a CALL in a parent orchestrator workflow.

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW video_to_audio` | `WORKFLOW` | Single named workflow; no sub-workflows or PROCEDURE |
| `INPUT: @video VIDEO` | typed INPUT declaration | VIDEO type signals multimodal path; executor passes file path, not bytes |
| `INPUT: @target_format, @bitrate, @sample_rate, @output_dir` | TEXT / INT INPUT params | Codec parameters with sensible defaults; no LLM needed to resolve them |
| `OUTPUT: @audio AUDIO` | typed OUTPUT declaration | AUDIO type signals downstream recipes can consume via CALL |
| `CALL extract_audio(...) INTO @audio` | `CALL <tool>(...)` | Side-effecting tool call (ffmpeg via pydub/subprocess); no LLM |
| `LOGGING ... LEVEL INFO/WARN/ERROR` | `LOGGING` | Structured log emission at each stage boundary |
| `RETURN @audio` | `RETURN` | Linear termination; no status token needed on the happy path |
| `EXCEPTION WHEN FileNotFound THEN ... RETURN ... WITH status='failed'` | `EXCEPTION WHEN` + `RETURN WITH status=` | Non-trivial status — allows caller to branch on failure |
| `EXCEPTION WHEN NoAudioTrack` | `EXCEPTION WHEN` | Distinct from codec errors; video is valid but has no audio stream |
| `EXCEPTION WHEN CodecError` | `EXCEPTION WHEN` | Installation or format incompatibility in ffmpeg layer |

### 4. Logical Functions / Prompts

**`extract_audio`**
- **Role:** The sole execution unit in this workflow. It performs the actual codec operation — invoking ffmpeg (via pydub or subprocess) to demux the audio stream from the video container and transcode it to the requested format.
- **Key conventions:** Takes five positional arguments (`@video`, `@target_format`, `@bitrate`, `@sample_rate`, `@output_dir`). Returns a file path string (the AUDIO output). Raises typed exceptions (`FileNotFound`, `NoAudioTrack`, `CodecError`) that map directly to the EXCEPTION handlers in the workflow. No prompt template, no LLM call — purely deterministic.

> There are no CREATE FUNCTION / GENERATE steps in this workflow. It is intentionally prompt-free.

### 5. Control Flow

1. **Entry** — log the input video path and codec parameters at INFO level.
2. **Extract** — CALL `extract_audio(...)` INTO `@audio`; this is a blocking, synchronous tool call.
3. **Success exit** — log the output path at INFO level, then RETURN `@audio` (no status token; linear success).
4. **Failure exits** — any of three typed exceptions short-circuits the happy path:
   - `FileNotFound` → logs ERROR, RETURN with `status='failed'`
   - `NoAudioTrack` → logs WARN, RETURN with `status='failed'`
   - `CodecError` → logs ERROR, RETURN with `status='failed'`

   All failure RETURNs carry `status='failed'`, which is a non-trivial token — an orchestrator CALLing this workflow should inspect the status and handle it via its own EVALUATE or EXCEPTION block.

There is no WHILE loop (the operation is single-pass), no EVALUATE branch (no LLM output to interpret), and no CALL PARALLEL (one track extracted per invocation).

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Extract the audio track from a video file and return the path to the resulting audio file, ready for downstream consumption by audio-processing workflows." --mode workflow

# Step 2 — compile to any target
spl3 splc compile video_to_audio.spl --lang python/pocketflow
spl3 splc compile video_to_audio.spl --lang python/langgraph
spl3 splc compile video_to_audio.spl --lang go
```

> **Tip for regeneration:** The text2spl prompt alone may not capture the three-exception pattern or the AUDIO/VIDEO typed I/O. Paste the full **Section 2 (High-level Description)** as the `--description` argument for a more faithful reconstruction, then hand-edit the exception names (`FileNotFound`, `NoAudioTrack`, `CodecError`) and the typed INPUT/OUTPUT declarations if the generator emits generic `TEXT` types instead.