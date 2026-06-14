## Summary

This workflow extracts structured data from a PDF invoice using a vision-capable LLM, then validates the arithmetic of that data using pure deterministic computation. It exists to automate accounts-payable intake — eliminating manual re-keying of invoice figures and catching math discrepancies before payment. Finance teams and AP automation pipelines are the primary beneficiaries.

---

## Detailed Specification

### 1. Purpose

Given a PDF invoice file, extract all key fields (vendor, customer, line items, tax, and total) via LLM vision and confirm that every numeric relationship in the document is arithmetically correct.

---

### 2. High-level Description

The workflow is a two-step linear pipeline with no loops or branches. The first step, `extract_invoice_fields`, is a GENERATE call that accepts a multimodal IMAGE input: the first page of the PDF is rasterized to PNG at 200 DPI using PyMuPDF, base64-encoded, and submitted alongside a structured YAML extraction prompt to a vision-capable LLM (GPT-4o or Gemini 2.0 Flash). The LLM response is parsed from a fenced YAML block and stored as a structured dictionary in the shared variable `@extracted`. Numeric fields that the LLM may return as comma-formatted strings are coerced to float during post-processing. The second step, `validate_invoice_math`, is a deterministic CALL (no LLM) that checks four arithmetic invariants: each line-item amount equals quantity × unit price, the subtotal equals the sum of all line-item amounts, the tax amount equals the subtotal multiplied by the tax rate, and the grand total equals subtotal plus tax. All discrepancies larger than one cent are collected into `@validation_errors`. If `ExtractFields` fails during LLM extraction, the node retries up to three times with a five-second wait between attempts, mapping to an EXCEPTION handler with retry semantics. The final status — PASSED or FAILED with an error count — is written to a Markdown output file.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW invoice_processor` | `create_invoice_flow()` + `main()` | Flow definition + CLI entry point |
| `INPUT @pdf_path IMAGE` | `shared["pdf_path"]` passed to `ExtractFields.prep()` | PDF rasterized to PNG before LLM call |
| `GENERATE extract_invoice_fields(@image) INTO @extracted` | `ExtractFields.exec()` → `call_llm_with_image()` | Multimodal call; output parsed from fenced YAML |
| `CALL validate_invoice_math(@extracted) INTO @validation_errors` | `Validate.exec()` | Pure Python arithmetic; no LLM involved |
| `@extracted` | `shared["extracted"]` | Structured dict: invoice fields + line items |
| `@validation_errors` | `shared["validation_errors"]` | List of error strings; empty = PASSED |
| `EXCEPTION WHEN GenerationError THEN retry` | `max_retries=3, wait=5` on `ExtractFields` | PocketFlow node-level retry on exec failure |
| `CREATE FUNCTION extract_invoice_fields` | Inline prompt string in `ExtractFields.exec()` | YAML fence sentinel `\`\`\`yaml` / `\`\`\`` used to delimit structured output |

---

### 4. Logical Functions / Prompts

**`extract_invoice_fields`**
- **Role**: Vision extraction — the sole LLM call in the workflow. Converts an invoice image into a machine-readable YAML structure.
- **Input**: Base64-encoded PNG of invoice page 0, rasterized at 200 DPI.
- **Prompt conventions**: Instructs the model to output *only* YAML inside a fenced block. The schema is fully specified in the prompt (all field names, types, and placeholder values), leaving zero ambiguity about structure. The sentinel pattern ` ```yaml ... ``` ` is used to extract the response reliably via string splitting.
- **Output format**: YAML with fields `invoice_number`, `vendor`, `customer`, `date`, `due_date`, `line_items[]` (description, quantity, unit_price, amount), `subtotal`, `tax_rate`, `tax_amount`, `total`.
- **Post-processing**: Numeric fields coerced from string (handles commas and `$` symbols from LLM formatting drift).

**`validate_invoice_math`** *(deterministic — no LLM)*
- **Role**: Arithmetic auditor. Applies four validation rules against `@extracted` and accumulates discrepancies.
- **Rules**: line item × unit_price = amount (±$0.01); sum(amounts) = subtotal (±$0.01); subtotal × tax_rate% = tax_amount (±$0.01); subtotal + tax_amount = total (±$0.01).
- **Tax rate normalization**: Handles both percentage (e.g., 8.5) and decimal (e.g., 0.085) representations from the LLM.

---

### 5. Control Flow

```
[START] → ExtractFields (GENERATE, multimodal IMAGE) → @extracted
        → Validate (CALL, deterministic math) → @validation_errors
        → [END] write Markdown report
```

Execution is strictly linear. `ExtractFields` carries `max_retries=3` — if the vision call or YAML parse fails, it retries up to three times before propagating the exception. `Validate` is unconditional: it always runs on whatever `@extracted` contains and always produces a (possibly empty) error list. There is no WHILE loop, no EVALUATE branch, and no conditional termination — the workflow always completes in exactly two node executions.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "Extract all fields from a PDF invoice using a vision LLM \
  (rasterize page 0 to PNG, send as IMAGE input with a YAML schema prompt, parse the \
  fenced YAML response into @extracted), then call a deterministic validator that checks \
  four arithmetic invariants: line-item amounts, subtotal, tax, and grand total, \
  collecting errors into @validation_errors. Retry extraction up to 3 times on failure." \
  --mode workflow

# Step 2 — compile to any target
spl3 splc compile invoice_processor.spl --lang python/pocketflow
spl3 splc compile invoice_processor.spl --lang python/langgraph
spl3 splc compile invoice_processor.spl --lang go
```