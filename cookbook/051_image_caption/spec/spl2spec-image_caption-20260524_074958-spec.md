## Summary

This workflow accepts an image file and produces a text description, targeted answer, or extracted text using a vision-capable language model (Gemma 4 via Ollama). It exists to provide a single, model-agnostic entry point for three distinct multimodal analysis modes — general captioning, detailed description, and OCR — without requiring the caller to manage prompt logic. Non-technical users and pipeline authors benefit from a clean `mode` switch that hides all prompt engineering details.

---

## Detailed Specification

### 1. Purpose

Analyze an input image and return a text result using one of three vision modes — concise captioning, comprehensive description, or optical character recognition — dispatched by a single `@mode` parameter.

### 2. High-level Description

The `image_caption` WORKFLOW accepts an `IMAGE` input alongside three control parameters (`@mode`, `@model`, `@output_budget`) and routes execution through an `EVALUATE` branch to one of three CREATE FUNCTIONs. The `caption` function instructs the model to answer a specific `@question` about the image concisely. The `detailed_caption` function requests a comprehensive visual description covering subjects, setting, color, lighting, and any visible text. The `ocr` function treats the model as a pure OCR engine, extracting all visible text verbatim or returning a sentinel token `[NO TEXT FOUND]` when none is present. All three branches invoke `GENERATE ... INTO @result` with a shared `OUTPUT BUDGET` and `USING MODEL` directive, so the same `.spl` file works against any vision-capable model without modification. Structured logging is emitted at entry and exit via `LOGGING` statements that record the active photo path, mode, model name, and output length. An `EXCEPTION WHEN ModelUnavailable` handler catches the case where Ollama is not running or the model is not pulled, logs an error, and returns a safe error string with `status = 'failed'`.

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `CREATE FUNCTION caption(...)` | `CREATE FUNCTION` | Prompt template for question-answering against the image; `{question}` slot injected at call time |
| `CREATE FUNCTION detailed_caption(...)` | `CREATE FUNCTION` | Prompt template for full visual description; no question slot — structured coverage list in prompt body |
| `CREATE FUNCTION ocr(...)` | `CREATE FUNCTION` | Prompt template for text extraction; sentinel `[NO TEXT FOUND]` defined inside the prompt |
| `WORKFLOW image_caption` | `WORKFLOW` | Named, parameterized entry point with `INPUT:` / `OUTPUT:` declarations |
| `@photo IMAGE` | SPL `@var` with type `IMAGE` | Passed to `generate_multimodal()` at runtime; encoded by the codec layer |
| `EVALUATE @mode WHEN = '...' THEN ... ELSE ... END` | `EVALUATE` | Selects which CREATE FUNCTION to invoke; `ELSE` falls back to `caption` |
| `GENERATE fn(...) INTO @result` | `GENERATE ... INTO @var` | Single LLM call per branch; captures response into shared output variable |
| `WITH OUTPUT BUDGET @output_budget TOKENS` | `GENERATE` output budget | Token cap applied uniformly across all three branches |
| `USING MODEL @model` | `GENERATE` model directive | Model resolved at execution time; keeps `.spl` hardware-agnostic |
| `LOGGING ... LEVEL INFO/ERROR` | `LOGGING` | Side-effect log emission; not a tool call, no `INTO` binding |
| `RETURN @result` | `RETURN` | Linear exit with no status token — implicit success |
| `RETURN '...' WITH status = 'failed'` | `RETURN WITH status=` | Non-trivial status; signals failure to caller or pipeline orchestrator |
| `EXCEPTION WHEN ModelUnavailable THEN ... END` | `EXCEPTION WHEN` | Typed handler for missing or offline vision model |

### 4. Logical Functions / Prompts

**`caption(photo IMAGE, question TEXT)`**
- Role: general-purpose Q&A against the image; the default and fallback mode
- Prompt conventions: direct instruction to answer `{question}` concisely and accurately; no output format constraints; `{question}` is the only injected slot

**`detailed_caption(photo IMAGE)`**
- Role: exhaustive visual description for documentation, accessibility, or indexing use cases
- Prompt conventions: structured coverage checklist embedded in the prompt body (subjects, setting, colors/lighting, visible text/signs); no question slot; no sentinel token

**`ocr(photo IMAGE)`**
- Role: treats the LLM as a character-level OCR engine
- Prompt conventions: instructs verbatim extraction of all visible text; sentinel `[NO TEXT FOUND]` defined explicitly to ensure a parseable, non-empty result even on images with no text

### 5. Control Flow

1. **Entry** — `LOGGING` records `@photo`, `@mode`, and `@model`.
2. **Dispatch** — `EVALUATE @mode` branches on string equality:
   - `'caption'` → `GENERATE caption(@photo, @question) INTO @result`
   - `'detailed'` → `GENERATE detailed_caption(@photo) INTO @result`
   - `'ocr'` → `GENERATE ocr(@photo) INTO @result`
   - `ELSE` → falls back to `caption`, matching the `DEFAULT 'caption'` declared on `@mode`
3. **Exit** — `LOGGING` records output length; `RETURN @result` with no status token (implicit success).
4. **Error path** — if `ModelUnavailable` is raised at any point, the `EXCEPTION` handler logs the error and `RETURN`s with `status = 'failed'`, terminating the workflow without propagating the exception to the caller.

There is no `WHILE` loop; the workflow is a single-shot LLM call with no iterative refinement.

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Analyze an input image and return a text result using one of three vision modes — concise captioning, comprehensive description, or optical character recognition — dispatched by a single @mode parameter." --mode workflow

# Step 2 — compile to any target
spl3 splc compile image_caption.spl --lang python/pocketflow
spl3 splc compile image_caption.spl --lang python/langgraph
spl3 splc compile image_caption.spl --lang go
```