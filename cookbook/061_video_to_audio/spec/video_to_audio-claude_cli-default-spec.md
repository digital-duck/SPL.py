## Summary

This workflow extracts the audio track from a video file and saves it as a standalone audio file in a configurable format (MP3, WAV, or FLAC). It is a deterministic, codec-based operation with no LLM involvement, designed to serve as a preprocessing step that feeds audio output into downstream workflows such as transcription or summarization. Media engineers, content pipelines, and archiving systems benefit from this as a clean, composable extraction primitive.

---

## Detailed Specification

### 1. Purpose

Extract the audio track from a source video file and write it to a target audio file at a specified format, bitrate, and sample rate.

---

### 2. High-level Description

The `video_to_audio` WORKFLOW accepts a video file path along with codec parameters (format, bitrate, sample rate) and an output directory, then delegates all work to a single deterministic tool call. A CALL to `extract_audio` performs the ffmpeg-based extraction and stores the resulting audio file path in the shared state variable `@audio`. No LLM GENERATE calls are used; this is a pure media-processing primitive. Structured LOGGING at INFO level brackets the CALL to record both the input parameters and the output path. Three named EXCEPTION handlers guard against the most common failure modes — a missing source file (FileNotFound), a video with no embedded audio track (NoAudioTrack), and an ffmpeg installation or codec failure (CodecError) — each returning a descriptive error string accompanied by `status = 'failed'` to signal failure to any orchestrating workflow. The workflow is designed to be composed via CALL from a higher-level orchestrator, piping `@audio` directly into downstream recipes such as audio summarization or voice dialogue.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW video_to_audio` | `WORKFLOW <name>` | Top-level named workflow; no sub-workflows |
| `INPUT: @video, @target_format, @bitrate, @sample_rate, @output_dir, @log_dir` | Typed `INPUT` block with `DEFAULT` values | Six parameters; `@video` is type `VIDEO`, others `TEXT` / `INT` |
| `OUTPUT: @audio AUDIO` | Typed `OUTPUT` declaration | Single output of SPL type `AUDIO` |
| `CALL extract_audio(...) INTO @audio` | `CALL <tool>(...) INTO @<var>` | Deterministic ffmpeg tool call; stores extracted audio path |
| `LOGGING ... LEVEL INFO/WARN/ERROR` | `LOGGING` statement | Structured log at multiple severity levels; no branching |
| `EXCEPTION WHEN FileNotFound THEN ... RETURN ... WITH status='failed'` | `EXCEPTION WHEN <Type> THEN` + `RETURN WITH status=` | Three typed handlers; non-trivial `status='failed'` drives failure signaling to callers |
| `EXCEPTION WHEN NoAudioTrack THEN ... RETURN ... WITH status='failed'` | `EXCEPTION WHEN <Type> THEN` + `RETURN WITH status=` | Handles absence of audio stream in source container |
| `EXCEPTION WHEN CodecError THEN ... RETURN ... WITH status='failed'` | `EXCEPTION WHEN <Type> THEN` + `RETURN WITH status=` | Guards against missing or broken ffmpeg installation |
| `@audio` | Shared state `@<var>` | Populated by CALL; passed to OUTPUT and available to callers |

---

### 4. Logical Functions / Prompts

**No LLM prompt functions are used in this workflow.** The sole callable is:

- **Name:** `extract_audio`
- **Role:** The single side-effecting operation; performs the actual codec work by invoking ffmpeg (via pydub or subprocess) to demux and encode the audio stream from the source video container into the target format.
- **Key conventions:** Accepts `(@video, @target_format, @bitrate, @sample_rate, @output_dir)` as positional arguments; returns the file path of the written audio file. No prompt template, no scoring, no sentinel tokens — this is a deterministic tool, not an LLM call.

---

### 5. Control Flow

Execution is strictly linear with no loops or branches in the happy path:

1. **Entry** — LOGGING records the source video path, target format, and bitrate at INFO level.
2. **Extraction** — CALL `extract_audio(...)` INTO `@audio` performs the ffmpeg codec operation and populates `@audio` with the output file path.
3. **Exit** — LOGGING records the output path at INFO level, then the workflow RETURNs `@audio`.

**Exception paths** (non-trivial RETURN WITH `status='failed'`):
- If the source video file does not exist → `FileNotFound` handler logs at ERROR and returns a sentinel error string with `status='failed'`.
- If the video container has no audio stream → `NoAudioTrack` handler logs at WARN and returns with `status='failed'`.
- If ffmpeg is absent or fails → `CodecError` handler logs at ERROR and returns with `status='failed'`.

There are no WHILE loops, no EVALUATE branches, and no LLM-driven control decisions in this workflow.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Extract the audio track from a source video file and write it to a target audio file at a specified format, bitrate, and sample rate." --mode workflow

# Step 2 — compile to any target
spl3 splc compile video_to_audio.spl --lang python/pocketflow
spl3 splc compile video_to_audio.spl --lang python/langgraph
spl3 splc compile video_to_audio.spl --lang go
```