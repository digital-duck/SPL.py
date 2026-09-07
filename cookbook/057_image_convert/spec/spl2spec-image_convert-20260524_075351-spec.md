## Summary

This workflow converts an image from one format to another (PNG, JPEG, WebP, BMP, GIF) using a deterministic codec — no LLM is involved. It exists to give any orchestrator workflow a single, composable, loggable unit for image conversion that handles errors cleanly. Developers building multi-step media pipelines benefit by being able to `CALL image_convert(...)` without reimplementing codec logic inline.

---

## Detailed Specification

### 1. Purpose

Convert a source image file to a specified target format at a given quality level and write the result to an output directory, returning the converted file path.

---

### 2. High-level Description

`image_convert` is a SPL WORKFLOW that wraps a deterministic Pillow-based codec operation as a composable unit callable via `CALL` from any orchestrator workflow. On entry, the workflow emits a structured INFO log via LOGGING, then executes a single CALL to the `convert_image` tool function, which performs the actual format conversion (PNG ↔ JPEG ↔ WebP ↔ BMP ↔ GIF) at the requested quality level and writes the output file to the specified directory. A second LOGGING statement records the output path on success before the workflow RETURNs the converted image path as the OUTPUT variable `@converted`. Because the operation is deterministic and single-pass, there is no WHILE loop and no EVALUATE branch on the happy path. Two typed EXCEPTION handlers guard against failure: `WHEN FileNotFound` logs an ERROR and RETURNs a sentinel error string with `status = 'failed'`; `WHEN UnsupportedFormat` does the same for unrecognised target format tokens, making error states explicit and machine-readable to callers.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW image_convert` | `WORKFLOW` | Top-level named unit; callable via `CALL image_convert(...)` from any parent workflow |
| `INPUT: @image IMAGE ...` | Typed INPUT declaration | `IMAGE` type signals multimodal path; `INT` and `TEXT` cover numeric and string params |
| `OUTPUT: @converted IMAGE` | Typed OUTPUT declaration | Caller receives a file path typed as IMAGE |
| `CALL convert_image(...) INTO @converted` | `CALL <tool>(...) INTO @var` | Side-effect tool call (Pillow codec); result bound to `@converted` |
| `LOGGING ... LEVEL INFO/ERROR` | `LOGGING` | Structured log emission; not an LLM call |
| `RETURN @converted` | `RETURN @var` | Happy-path exit; no status metadata needed |
| `EXCEPTION WHEN FileNotFound THEN ...` | `EXCEPTION WHEN <Type> THEN` | Typed error handler; overrides default exception propagation |
| `EXCEPTION WHEN UnsupportedFormat THEN ...` | `EXCEPTION WHEN <Type> THEN` | Second typed handler for codec-level format rejection |
| `RETURN '...' WITH status = 'failed'` | `RETURN WITH status=` | Non-trivial status token; signals failure to the calling workflow so it can branch or abort |
| `@image`, `@target_format`, `@quality`, `@output_dir`, `@log_dir`, `@converted` | SPL `@vars` | Shared mutable state passed through the workflow frame |

---

### 4. Logical Functions / Prompts

There are no LLM prompt templates in this workflow. The single callable is:

**`convert_image`**
- **Role:** Physical codec tool; performs the format conversion using Pillow and writes the output file.
- **Key conventions:** Accepts `(@image, @target_format, @quality, @output_dir)`. Returns the output file path as a string. No prompt, no model invocation — this is a deterministic side-effect function registered as an SPL tool in `tools.py`.

---

### 5. Control Flow

1. **Entry** — log the source image, target format, and quality level at INFO.
2. **Execute** — `CALL convert_image(...)` performs the conversion and binds the output path to `@converted`.
3. **Exit** — log the output path at INFO, then RETURN `@converted`.
4. **Error paths (EXCEPTION handlers, evaluated only on failure):**
   - `FileNotFound` → log ERROR, RETURN with `status = 'failed'`; the non-default status allows a calling workflow to detect and react to the failure via EVALUATE.
   - `UnsupportedFormat` → same pattern.

There is no WHILE loop and no EVALUATE branch; the happy path is strictly linear.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Convert a source image file to a specified target format at a given quality level and write the result to an output directory, returning the converted file path." --mode workflow

# Step 2 — compile to any target
spl3 splc compile image_convert.spl --lang python/pocketflow
spl3 splc compile image_convert.spl --lang python/langgraph
spl3 splc compile image_convert.spl --lang go
```