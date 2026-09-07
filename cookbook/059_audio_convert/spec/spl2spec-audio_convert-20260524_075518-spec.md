## Summary

`audio_convert` is a composable SPL workflow that converts an audio file from one format to another (WAV, MP3, OGG, FLAC, M4A) using deterministic codec tools — no LLM is involved. It exists as a reusable building block that any orchestrator workflow can invoke via `CALL`, providing a uniform, loggable interface to low-level ffmpeg/pydub operations. Audio pipeline engineers and voice-application developers benefit by composing format conversion into larger SPL workflows without re-implementing codec logic.

---

## Detailed Specification

### 1. Purpose

Convert a source audio file to a caller-specified target format, bitrate, and sample rate, returning the output file path as a typed `AUDIO` variable suitable for downstream SPL steps.

---

### 2. High-level Description

`audio_convert` is a thin, composable WORKFLOW wrapper around a single deterministic tool call; it contains no LLM calls (no GENERATE steps) and no iterative control flow. The workflow accepts six INPUT parameters — the source file as an `AUDIO` type, the target format, bitrate, sample rate, and output/log directories — and declares one OUTPUT of type `AUDIO`. Execution opens with a LOGGING statement that records the conversion intent at INFO level, then issues a single CALL to the `convert_audio` tool (implemented in `run.py` via pydub and ffmpeg), capturing the resulting file path into `@converted`. A second LOGGING statement confirms completion before the workflow terminates with RETURN. Three typed EXCEPTION handlers guard against the three failure modes a codec pipeline can raise — `FileNotFound`, `UnsupportedFormat`, and `CodecError` — each logging a structured ERROR message and issuing a RETURN WITH `status = 'failed'` so any calling orchestrator can detect and branch on the failure. Because the DODA principle applies, the `.spl` file is runtime-agnostic: the same workflow runs locally under Python/pydub or on an Intel Mini-PC via a Go/ffmpeg target without any change to the source.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW audio_convert` | `WORKFLOW` | Top-level named workflow; callable via `CALL audio_convert(...)` from any orchestrator |
| `INPUT: @audio AUDIO` | Typed INPUT declaration | `AUDIO` type signals to the executor that this variable carries a file path, not free text |
| `OUTPUT: @converted AUDIO` | Typed OUTPUT declaration | Caller receives a typed `AUDIO` handle, enabling downstream multimodal steps |
| `CALL convert_audio(...) INTO @converted` | `CALL <tool>(...) INTO @var` | Deterministic tool invocation (no LLM); side-effects the filesystem, returns output path |
| `LOGGING ... LEVEL INFO/ERROR` | `LOGGING` | Structured log emission; not a GENERATE call — purely observability |
| `RETURN @converted` | `RETURN` (linear termination) | Happy-path exit; no status token because there is no branch condition to drive |
| `RETURN '...' WITH status = 'failed'` | `RETURN WITH status=` | Non-trivial: signals failure to the calling orchestrator so it can EVALUATE and branch |
| `EXCEPTION WHEN FileNotFound THEN` | `EXCEPTION WHEN <Type> THEN` | Typed handler; maps to pydub/OS missing-file errors |
| `EXCEPTION WHEN UnsupportedFormat THEN` | `EXCEPTION WHEN <Type> THEN` | Typed handler; raised when `@target_format` is not in the supported codec set |
| `EXCEPTION WHEN CodecError THEN` | `EXCEPTION WHEN <Type> THEN` | Typed handler; catches ffmpeg binary errors (not installed, corrupt stream, etc.) |

---

### 4. Logical Functions / Prompts

This workflow contains **no LLM prompt functions** — it is entirely deterministic. The single callable unit is:

**`convert_audio`**
- **Role:** The sole executable step; performs the format conversion using pydub (Python target) or ffmpeg directly (Go target).
- **Inputs:** source path (`@audio`), `@target_format`, `@bitrate`, `@sample_rate`, `@output_dir`.
- **Output:** Absolute or relative path to the newly created file, bound into `@converted`.
- **Prompt conventions:** None. This is a `CALL` (tool), not a `GENERATE` (LLM). No sentinel tokens, no scoring, no natural-language output format.

---

### 5. Control Flow

```
START
  │
  ├─ LOGGING  [INFO] conversion intent
  │
  ├─ CALL convert_audio(...) INTO @converted
  │       │
  │       ├─ EXCEPTION FileNotFound   → LOG [ERROR] + RETURN status='failed'
  │       ├─ EXCEPTION UnsupportedFormat → LOG [ERROR] + RETURN status='failed'
  │       └─ EXCEPTION CodecError     → LOG [ERROR] + RETURN status='failed'
  │
  ├─ LOGGING  [INFO] conversion complete
  │
  └─ RETURN @converted
```

There is no WHILE loop and no EVALUATE branch on the happy path. The only non-trivial RETURN tokens are `status = 'failed'` inside the three EXCEPTION handlers, which allow a calling orchestrator to detect failure and route accordingly (e.g., retry with a different bitrate or surface an error to the user).

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (paste Section 2 as text2spl input)
spl3 text2spl \
  --description "Build a composable WORKFLOW named audio_convert that wraps a single CALL to a convert_audio tool. Accept INPUT parameters: @audio (AUDIO type, source file), @target_format (TEXT), @bitrate (TEXT, default 192k), @sample_rate (INT, default 44100), @output_dir (TEXT), @log_dir (TEXT). Declare OUTPUT @converted as AUDIO. Emit a LOGGING INFO statement before and after the CALL. Handle three typed EXCEPTIONs — FileNotFound, UnsupportedFormat, CodecError — each logging at ERROR level and issuing RETURN WITH status='failed'. No LLM calls; no WHILE or EVALUATE constructs." \
  --mode workflow \
  --adapter ollama -m gemma3

# Step 2 — compile to any target
spl3 splc compile audio_convert.spl --lang python      # local pydub/ffmpeg
spl3 splc compile audio_convert.spl --lang go          # Intel Mini-PC via ffmpeg binary
spl3 splc compile audio_convert.spl --lang langgraph   # LangGraph orchestration wrapper
```