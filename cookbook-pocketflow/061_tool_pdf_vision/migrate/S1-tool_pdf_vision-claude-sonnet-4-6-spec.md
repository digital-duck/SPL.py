## Summary

This workflow scans a directory of PDF files, converts each page to an image, and uses a multimodal Vision LLM (GPT-4 Vision) to perform OCR and text extraction on each page image. It is designed for organizations that need to digitize scanned documents at scale, producing structured, page-ordered Markdown output for each PDF. Non-technical users benefit because they simply drop PDFs into a folder and receive clean, formatted text output with no manual intervention.

---

## Detailed Specification

### 1. Purpose

Extract structured, page-ordered text from a directory of PDF files using a multimodal Vision LLM, and write the combined results to a Markdown file.

---

### 2. High-level Description

This workflow implements a **batch document OCR pipeline** using a two-level structure: an outer batch loop over all PDFs in a directory, and an inner linear three-step pipeline executed for each individual PDF.

The outer WORKFLOW (`ProcessPDFBatch`) enumerates all `.pdf` files found in the `pdfs/` subdirectory at startup, pairing each with a configurable `extraction_prompt` that defaults to a general layout-preserving OCR instruction. For each PDF, it dispatches an inner WORKFLOW (`ProcessSinglePDF`) that runs three sequential steps. First, `LoadPDF` invokes a deterministic CALL tool (`pdf_to_images`) that converts each page of the PDF to a size-constrained image (max 2000px), returning a list of `(image, page_number)` pairs. Second, `ExtractText` iterates over every page image and issues one GENERATE call per page to the Vision LLM, passing the image and the extraction prompt as multimodal input; this is the only LLM inference step in the pipeline. Third, `CombineResults` is a deterministic CALL that sorts extracted page texts by page number and concatenates them with `=== Page N ===` headers into a single string. After all PDFs are processed, the outer workflow collects per-PDF results (filename + combined text) into a results list, which the CLI driver writes to a Markdown output file. There is no conditional branching (EVALUATE) or iterative refinement (WHILE) — the control flow is entirely linear within each sub-workflow.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW ProcessPDFBatch` | `ProcessPDFBatchNode` (BatchNode) | Outer batch loop; `prep` builds item list, `exec` runs inner flow per item, `post` collects results |
| `WORKFLOW ProcessSinglePDF` | `create_single_pdf_flow()` + three Nodes | Inner linear pipeline per PDF; `LoadPDFNode >> ExtractTextNode >> CombineResultsNode` |
| `CREATE FUNCTION extract_text` | `extract_text_from_image(img, prompt)` in `tools/vision.py` | Multimodal prompt template; prompt is parameterized via `extraction_prompt` |
| `GENERATE extract_text(@image, @prompt) INTO @page_text` | `extract_text_from_image(img, prompt)` called per page in `ExtractTextNode.exec` | One Vision LLM call per page image; result is text string |
| `CALL pdf_to_images(@pdf_path) INTO @page_images` | `pdf_to_images(pdf_path)` in `tools/pdf.py` | Deterministic tool; no LLM involved; returns list of `(PIL.Image, int)` tuples |
| `CALL combine_pages(@extracted_text) INTO @final_text` | `CombineResultsNode.exec` | Deterministic sort + string join; no LLM; produces `=== Page N ===`-delimited output |
| `@shared` variables | `shared` dict passed through Node `prep`/`post` | `page_images`, `extracted_text`, `final_text`, `results` are all shared-state bindings |
| `CALL PARALLEL` (potential refactor) | Sequential `for img, page_num in images` loop in `ExtractTextNode.exec` | Currently serial per-page; natural candidate for `CALL PARALLEL` in SPL |

---

### 4. Logical Functions / Prompts

**`extract_text` (Vision LLM prompt)**
- **Role**: The sole inference step; performs OCR on a single PDF page image.
- **Key conventions**:
  - Input is multimodal: one page image + a text extraction prompt sent to GPT-4 Vision.
  - Default prompt: `"Extract all text from this document, preserving formatting and layout."`
  - Prompt is fully user-configurable via the `extraction_prompt` parameter, enabling specialized extraction (e.g., tables-only, structured fields).
  - Output is raw text with no sentinel tokens or scoring; the model is trusted to return well-formatted text directly.
  - Token limit is capped at 1000 tokens per response (enforced in `tools/vision.py`).
  - Image size limit: 20 MB per image (enforced before Vision API submission).

---

### 5. Control Flow

```
ProcessPDFBatch.prep
  → scan pdfs/ directory → build list of {pdf_path, extraction_prompt} items

for each PDF item (BatchNode parallelism):
  ProcessSinglePDF inner flow:
    LoadPDFNode
      → CALL pdf_to_images(pdf_path) → @page_images

    ExtractTextNode
      → for each (image, page_num) in @page_images:
          GENERATE extract_text(image, extraction_prompt) → append to @extracted_text

    CombineResultsNode
      → CALL combine_pages(@extracted_text) → @final_text

  → return {filename, final_text}

ProcessPDFBatch.post
  → collect all per-PDF results → shared["results"]

CLI driver
  → write results to Markdown output file
```

No WHILE loop, no EVALUATE branch, no exception handlers are present. The only non-trivial termination condition is an empty `pdfs/` directory, which causes `prep` to return an empty list and skip all processing with a printed warning.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "Batch PDF OCR pipeline: enumerate all PDFs in a directory, \
  convert each PDF's pages to images via a pdf_to_images tool, call a Vision LLM once per \
  page image using a configurable extraction_prompt to extract formatted text (GENERATE with \
  multimodal input), then combine page texts in page order with page-number headers into a \
  single document string, and collect per-PDF results into an output list." \
  --mode workflow

# Step 2 — compile to any target
spl3 splc compile pdf_ocr_pipeline.spl --lang python/pocketflow
spl3 splc compile pdf_ocr_pipeline.spl --lang python/langgraph
spl3 splc compile pdf_ocr_pipeline.spl --lang go
```