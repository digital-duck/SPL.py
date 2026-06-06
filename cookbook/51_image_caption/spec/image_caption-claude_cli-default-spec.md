## Summary

This workflow accepts an image and routes it through one of three vision-model prompts — question-answering caption, comprehensive description, or OCR text extraction — returning a single text result. It targets edge hardware running a local Gemma 4 vision model via Ollama, eliminating cloud API dependencies. Product teams, researchers, and developers who need privacy-preserving or offline image understanding benefit most.

---

## Detailed Specification

### 1. Purpose

Provide a single-pass, mode-selectable image understanding endpoint that answers a user question, produces a detailed scene description, or extracts visible text from a supplied image using a locally hosted vision model.

### 2. High-level Description

The `image_caption` WORKFLOW accepts five runtime parameters — an image path, a freeform question, an analysis mode, a model identifier, and an output token budget — and dispatches to one of three CREATE FUNCTIONs based on the mode. The `caption` function is a focused visual Q&A prompt that answers the caller-supplied question concisely. The `detailed_caption` function instructs the model to produce a structured multi-aspect scene description covering subjects, setting, lighting, mood, and visible text. The `ocr` function treats the model as a plain OCR engine and instructs it to return raw extracted text or the sentinel token `[NO TEXT FOUND]` when no text is present. Control flow is expressed as a single EVALUATE on `@mode`, branching to `caption`, `detailed_caption`, or `ocr`; an ELSE clause falls back to `caption` for any unrecognised mode value. Every GENERATE call respects the `@output_budget` token ceiling and the caller-supplied `@model` string, making the workflow model-agnostic at the SPL layer. A ModelUnavailable EXCEPTION handler catches failures from the Ollama runtime, logs a diagnostic message, and terminates via RETURN WITH `status='failed'`, ensuring callers receive a structured error rather than an unhandled exception.

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW image_caption` | `WORKFLOW image_caption` | Top-level orchestration unit; single execution pass, no loop |
| `CREATE FUNCTION caption` | `CREATE FUNCTION caption(photo IMAGE, question TEXT)` | Q&A prompt; parameterised by image and freeform question |
| `CREATE FUNCTION detailed_caption` | `CREATE FUNCTION detailed_caption(photo IMAGE)` | Structured scene description; image-only input |
| `CREATE FUNCTION ocr` | `CREATE FUNCTION ocr(photo IMAGE)` | Text extraction prompt; uses `[NO TEXT FOUND]` sentinel |
| `EVALUATE @mode WHEN … THEN … ELSE … END` | `EVALUATE @mode WHEN = '…' THEN … ELSE … END` | Three-way dispatch on runtime mode string |
| `GENERATE … WITH OUTPUT BUDGET … USING MODEL … INTO @result` | `GENERATE <fn>(…) WITH OUTPUT BUDGET @output_budget TOKENS USING MODEL @model INTO @result` | One GENERATE per branch; budget and model are runtime-parameterised |
| `EXCEPTION WHEN ModelUnavailable THEN … RETURN … WITH status='failed'` | `EXCEPTION WHEN ModelUnavailable THEN … RETURN … WITH status='failed'` | Non-trivial RETURN: signals error to caller and terminates the workflow |
| Shared state variables | `@photo`, `@question`, `@mode`, `@model`, `@output_budget`, `@log_dir`, `@result` | `@result` is the single output variable written by all branches |
| `LOGGING … LEVEL INFO/ERROR` | `LOGGING f'…' LEVEL INFO/ERROR` | Structured log entries at workflow entry, exit, and error path |

### 4. Logical Functions / Prompts

**`caption(photo IMAGE, question TEXT)`**
- **Role:** Default and fallback mode; answers a caller-supplied question about the image.
- **Prompt conventions:** Instructs the model to be "precise" and "concise and accurate"; the `{question}` slot is injected verbatim, so prompt quality depends on the caller's question string.

**`detailed_caption(photo IMAGE)`**
- **Role:** Comprehensive scene analysis mode; no question parameter — the prompt itself defines the output structure.
- **Prompt conventions:** Uses an implicit bulleted agenda (subjects, setting, colors/lighting/mood, visible text/signs) to elicit a consistently structured multi-aspect response. No sentinel tokens.

**`ocr(photo IMAGE)`**
- **Role:** OCR extraction mode; treats the vision model as a document scanner.
- **Prompt conventions:** Uses the sentinel string `[NO TEXT FOUND]` as the required no-text reply, enabling downstream callers to detect the empty case programmatically without parsing free text.

### 5. Control Flow

1. **Entry:** workflow logs input parameters (`@photo`, `@mode`, `@model`).
2. **Dispatch:** EVALUATE on `@mode` selects one branch — `'caption'` → `caption()`, `'detailed'` → `detailed_caption()`, `'ocr'` → `ocr()`, anything else → `caption()` (ELSE fallback).
3. **Execution:** the selected branch issues a single GENERATE call, storing the model's text output into `@result`.
4. **Normal exit:** workflow logs output length and returns `@result` (no status token; linear termination).
5. **Error exit:** if the Ollama runtime raises `ModelUnavailable` at any point, the EXCEPTION handler logs an actionable error message and issues RETURN WITH `status='failed'`, delivering a structured error string to the caller.

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Provide a single-pass, mode-selectable image understanding endpoint that answers a user question, produces a detailed scene description, or extracts visible text from a supplied image using a locally hosted vision model." --mode workflow

# Step 2 — compile to any target
spl3 splc compile image_caption.spl --lang python/liquid        # edge / Ollama
spl3 splc compile image_caption.spl --lang python/pocketflow
spl3 splc compile image_caption.spl --lang python/langgraph
spl3 splc compile image_caption.spl --lang go                   # Intel Mini-PC + Ollama
```