## Summary

Data Extraction is a schema-constrained LLM workflow that pulls structured fields from messy, unstructured text — names, dates, monetary amounts, references, and more. It supports three target schemas (invoice, contract, general) selected at runtime, so the same workflow handles diverse document types without modification. Business analysts, finance teams, and data engineers benefit by turning raw documents or payment notes into clean, validated JSON without writing custom parsers.

---

## Detailed Specification

### 1. Purpose

Extract structured, schema-validated JSON fields from arbitrary noisy text input, with the schema selected dynamically based on the document format at call time.

---

### 2. High-level Description

This workflow uses a single-pass extraction pattern: a `CREATE FUNCTION` named `extraction_schema` acts as a schema selector, returning one of three JSON Schema definitions — `invoice`, `contract`, or `general` — based on the `format` parameter (defaulting to `general`). The `PROMPT` block `extract_fields` wires the input text and the resolved schema together, injecting a specialist system role that instructs the LLM to return only a JSON object matching the schema exactly, omitting any field not present in the source text. A single `GENERATE` call invokes the LLM with both the raw text and the schema, producing structured output captured into a result variable. There is no iterative refinement loop (no `WHILE`) and no conditional branching (no `EVALUATE`) — the workflow is intentionally linear and single-shot, keeping latency minimal for high-throughput document processing pipelines. Exception handling and multi-model routing are left to the caller or adapter layer.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `CREATE FUNCTION extraction_schema(format)` | `CREATE FUNCTION` | Pure schema-selection function; returns a JSON Schema string based on a CASE dispatch on the `format` argument; no LLM call involved |
| `PROMPT extract_fields` | `WORKFLOW` (single-step) | Declares the extraction prompt template with system role, input bindings, and the schema function call |
| `system_role(...)` | System message injection | Specialist persona: "data extraction specialist"; instructs JSON-only output, field omission on absence |
| `GENERATE extract(text, schema)` | `GENERATE ... INTO @var` | Single LLM call; passes raw text and resolved schema; captures structured JSON result |
| `context.text`, `context.format` | `@var` (INPUT bindings) | Runtime-supplied inputs — `text` is the raw document content, `format` selects the schema branch |
| `extraction_schema(context.format)` | Function call inside `GENERATE` | Resolves at execution time; binds schema string into the prompt context before the LLM call |

---

### 4. Logical Functions / Prompts

**`extraction_schema(format)`**
- **Role:** Schema resolver — not an LLM call. A pure SQL-style CASE expression that maps a document-type string to a JSON Schema definition.
- **Output formats:**
  - `invoice` — fields: `invoice_number`, `vendor`, `amount`, `currency`, `issue_date`, `due_date`, `line_items`, `payment_terms`, `po_reference`
  - `contract` — fields: `parties`, `effective_date`, `expiry_date`, `value`, `currency`, `jurisdiction`, `key_obligations`
  - `general` (default) — fields: `names`, `organizations`, `dates`, `amounts`, `references`, `locations` — all as typed arrays to handle multi-value extraction
- **Key convention:** Arrays are used for fields that may appear multiple times; typed sub-objects (e.g. `{"value": ..., "label": ...}`) preserve labeling context for dates and amounts.

**`extract_fields`**
- **Role:** Core extraction prompt — the single LLM-facing step. Combines the raw text, the resolved schema, and a strict instruction to return only valid JSON.
- **Key prompt conventions:**
  - System role enforces specialist persona and output discipline ("return only the JSON object")
  - Explicit omission rule: fields absent from source text must be omitted, not null-filled — prevents hallucination of missing data
  - No sentinel tokens, no scoring, no chain-of-thought — output is pure JSON, machine-parseable without post-processing

---

### 5. Control Flow

Execution is strictly linear and single-pass:

1. **Input binding** — `context.text` (the raw document) and `context.format` (schema selector, default `general`) are bound from the caller's parameters.
2. **Schema resolution** — `extraction_schema(context.format)` evaluates the CASE expression and returns the appropriate JSON Schema string.
3. **LLM call** — `GENERATE extract(text, schema)` sends the combined prompt (system role + text + schema) to the configured adapter and captures the JSON response.
4. **Termination** — the extracted JSON is returned to the caller. No loop, no branch, no retry.

There is no `WHILE` loop, no `EVALUATE` branch, and no `EXCEPTION` handler declared in this recipe — the design prioritizes throughput and simplicity over self-correction.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Extract structured, schema-validated JSON fields from arbitrary noisy text input, with the schema selected dynamically based on the document format at call time. Support three schemas: invoice (invoice_number, vendor, amount, currency, dates, line_items, payment_terms, po_reference), contract (parties, dates, value, currency, jurisdiction, key_obligations), and general (names, organizations, dates, amounts, references, locations). Use a CREATE FUNCTION for schema selection and a single GENERATE call with a specialist system role that returns only JSON, omitting absent fields." --mode workflow

# Step 2 — compile to any target
spl3 splc compile data_extraction.spl --lang python/pocketflow
spl3 splc compile data_extraction.spl --lang python/langgraph
spl3 splc compile data_extraction.spl --lang go
```