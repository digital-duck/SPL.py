## Summary

Data Extraction is a schema-constrained LLM workflow that pulls structured fields from messy, real-world text such as invoices, contracts, or general documents. It selects the appropriate JSON schema based on the document type, then instructs the model to extract only matching fields and return a clean JSON object. Business analysts, finance teams, and document processing pipelines benefit by getting machine-readable data from unstructured input without manual parsing.

---

## Detailed Specification

### 1. Purpose

Extract structured, schema-validated fields from noisy free-form text, producing a well-typed JSON object whose shape is determined by the declared document format (`invoice`, `contract`, or `general`).

### 2. High-level Description

The workflow uses a single-pass extraction pattern with no iterative refinement loop. A `CREATE FUNCTION` named `extraction_schema` acts as a schema resolver: given a `format` parameter, it returns one of three JSON Schema definitions — invoice (payment fields, line items, PO reference), contract (parties, dates, jurisdiction, obligations), or general (names, organizations, dates, amounts, references, locations). A `PROMPT` named `extract_fields` assembles the raw input text, the resolved schema, and a tightly scoped system role into a single LLM call using `GENERATE`, storing the result in a shared variable. The system role instructs the model to omit fields absent from the source text and return only the JSON object — no prose, no commentary. Because extraction succeeds or fails in one shot, there is no `WHILE` loop, no `EVALUATE` branch, and no non-default `RETURN` status; the workflow terminates immediately after the single `GENERATE` call and surfaces the extracted JSON to the caller.

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `CREATE FUNCTION extraction_schema(format)` | `CREATE FUNCTION` | Pure resolver — no LLM call; uses SQL `CASE` to pick the correct JSON Schema string at runtime |
| `PROMPT extract_fields` | Implicitly wraps a `GENERATE` call | Assembles `system_role`, `context.text`, resolved schema, and `format` into the LLM prompt |
| `GENERATE extract(text, schema)` | `GENERATE <fn>(...) INTO @<var>` | Single LLM call; result is the extracted JSON object stored in the output variable |
| `context.text`, `context.format` | SPL `@vars` / `context` bag | Runtime inputs passed via `--` CLI flags; accessed as named slots inside the prompt |
| `system_role(...)` | Prompt system-message convention | Scopes model behaviour to strict JSON-only output |

### 4. Logical Functions / Prompts

**`extraction_schema(format)`**
- **Role:** Schema resolver — selects and returns the appropriate JSON Schema definition based on `format`.
- **Key conventions:** No LLM involvement; deterministic SQL `CASE` expression. Falls back to the `general` schema for any unrecognised format value. Schemas are typed using JSON Schema `type`, `format`, and `properties` keywords to guide constrained generation.

**`extract_fields`**
- **Role:** Core extraction prompt — the single LLM call that reads free-form text and returns a JSON object conforming to the resolved schema.
- **Key conventions:**
  - `system_role` sentinel restricts model output to valid JSON only (no prose wrapper).
  - The schema is injected directly into context so the model can use it as a structural contract.
  - Absent fields must be omitted rather than null-filled, keeping output minimal and clean.
  - Output format is a plain JSON object; no markdown fences, no explanation.

### 5. Control Flow

The execution path is entirely linear:

1. **Input binding** — `context.text` and `context.format` (default `'general'`) are resolved from CLI arguments.
2. **Schema resolution** — `extraction_schema(context.format)` is evaluated, returning a JSON Schema string.
3. **Extraction** — `GENERATE extract(text, schema)` sends the assembled prompt to the LLM and captures the returned JSON object.
4. **Termination** — the workflow returns immediately with the extracted JSON; there is no loop, no branch, and no retry logic.

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Extract structured, schema-validated fields from noisy free-form text, producing a well-typed JSON object whose shape is determined by the declared document format (invoice, contract, or general)." --mode workflow

# Step 2 — compile to any target
spl3 splc compile data_extraction.spl --lang python/pocketflow
spl3 splc compile data_extraction.spl --lang python/langgraph
spl3 splc compile data_extraction.spl --lang go
```