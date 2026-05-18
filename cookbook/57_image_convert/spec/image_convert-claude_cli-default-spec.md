## Summary

This workflow converts a single image file from one raster format to another (PNG, JPEG, WebP, BMP, or GIF) using a deterministic codec library. No language model is involved; the SPL shell exists to provide a composable, auditable wrapper so any orchestrator can invoke the conversion as a typed, loggable, exception-safe step. Operations teams and pipeline authors benefit by getting a standard CALL-able component with structured error codes and log trails rather than a raw script.

---

## Detailed Specification

### 1. Purpose

Convert a source image file to a specified target format at a configurable quality level, returning the output file path and emitting structured logs, with named error handling for missing files and unsupported formats.

---

### 2. High-level Description

`image_convert` is a single-step WORKFLOW that wraps a deterministic codec operation in an SPL envelope, making it composable via CALL from any orchestrating workflow. Because the conversion is fully deterministic, the workflow contains no GENERATE calls and no LLM model is involved. Execution is linear: an INFO-level LOGGING statement records the intent (source path, target format, quality), then a single CALL to the `convert_image` tool performs the actual format conversion using Pillow and writes the result to the configured output directory, and a second LOGGING statement records the resulting file path. Two EXCEPTION handlers guard the workflow — WHEN FileNotFound logs an ERROR and RETURNs with `status='failed'`, and WHEN UnsupportedFormat does the same with a distinct message — so callers can branch on the status token. The workflow is designed to target both a local Python runtime and a Go runtime on an Intel Mini-PC via DODA compilation.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW image_convert` | `WORKFLOW <name>` | Top-level named workflow; no sub-workflows |
| `INPUT: @image, @target_format, @quality, @output_dir, @log_dir` | Typed `@var` declarations | Typed shared state; IMAGE and TEXT and INT types; all have defaults |
| `OUTPUT: @converted` | Typed `@var` declaration | IMAGE type; populated by the CALL |
| `LOGGING ... LEVEL INFO/ERROR` | `LOGGING` side-effect | Structured log emission; not a CALL but a built-in statement |
| `CALL convert_image(...) INTO @converted` | `CALL <tool>(...) INTO @<var>` | Side-effect tool call; drives actual Pillow I/O; stores result path |
| `EXCEPTION WHEN FileNotFound THEN` | `EXCEPTION WHEN <Type> THEN` | Named handler; intercepts missing source file |
| `EXCEPTION WHEN UnsupportedFormat THEN` | `EXCEPTION WHEN <Type> THEN` | Named handler; intercepts bad format string |
| `RETURN '[ERROR]...' WITH status='failed'` | `RETURN @<var> WITH <k>=<v>` | Non-trivial status token; callers can EVALUATE on `status='failed'` |

> No `GENERATE`, `CREATE FUNCTION`, `WHILE`, or `EVALUATE` constructs appear — this workflow contains no LLM calls and no conditional branching on model output.

---

### 4. Logical Functions / Prompts

**None.** This workflow is entirely deterministic. There are no `CREATE FUNCTION` prompt templates and no `GENERATE` LLM calls. The only computational step is the `convert_image` tool call, which delegates to the Pillow library. If an LLM-assisted variant were needed (e.g., auto-detecting format from content or generating alt-text post-conversion), a `GENERATE` step with an appropriate prompt function would be added.

---

### 5. Control Flow

```
START
  │
  ▼
LOGGING (INFO) — record source, target format, quality
  │
  ▼
CALL convert_image(@image, @target_format, @quality, @output_dir) INTO @converted
  │
  ├─[FileNotFound raised]──→ LOGGING (ERROR) → RETURN status='failed'
  ├─[UnsupportedFormat raised]─→ LOGGING (ERROR) → RETURN status='failed'
  │
  ▼
LOGGING (INFO) — record output path
  │
  ▼
RETURN @converted
```

No WHILE loop, no EVALUATE branch. The only non-linear paths are the two EXCEPTION exits, both of which emit `status='failed'` so a calling orchestrator can EVALUATE on that token to trigger a retry or alert.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Convert a source image file to a specified target format at a configurable quality level, returning the output file path and emitting structured logs, with named error handling for missing files and unsupported formats." --mode workflow

# Step 2 — compile to any target
spl3 splc compile image_convert.spl --lang python/pocketflow
spl3 splc compile image_convert.spl --lang python/langgraph
spl3 splc compile image_convert.spl --lang go
```