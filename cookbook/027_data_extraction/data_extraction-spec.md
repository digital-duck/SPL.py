## 0. High-level Description

This workflow implements a **schema-constrained extraction** pattern, using a single GENERATE call to pull structured fields from arbitrary unstructured or semi-structured text. The core design revolves around two SPL constructs: a `CREATE FUNCTION extraction_schema` that acts as a schema router, and a `PROMPT extract_fields` that wires the routed schema into an LLM extraction call. The `extraction_schema` function takes a `format` discriminator and returns one of three hardcoded JSON Schema objects — `invoice` (financial document with line items, dates, PO reference, and payment terms), `contract` (multi-party agreement with obligations, jurisdiction, and value), or a catch-all `general` schema covering names, organizations, dates, amounts, references, and locations as typed arrays. The `PROMPT extract_fields` injects a tightly scoped `system_role` instruction — "return valid JSON matching the schema exactly; omit absent fields; return only the JSON object" — to enforce strict, hallucination-resistant output with no extraneous prose. Control flow is deliberately minimal: no WHILE loop or EVALUATE branch is present, making this a single-shot extraction pipeline that terminates immediately after the GENERATE call. No CALL side-effects, LOGGING statements, or EXCEPTION handlers are declared, so error propagation is left to the runtime's default behavior.

## 1. Purpose

Extract structured, schema-validated JSON fields from noisy real-world text (invoices, contracts, or general documents) using a format-aware prompt that constrains the LLM to a predefined JSON Schema.

## 2. Inputs

| Parameter | Default | Description |
|-----------|---------|-------------|
| `text` | *(required)* | The raw input text to extract data from (e.g. invoice body, contract clause, free-form message) |
| `format` | `'general'` | Schema selector; accepted values are `invoice`, `contract`, or any other value (falls through to `general`) |

## 3. Process

1. **Schema selection** — `extraction_schema(format)` is evaluated. Based on the `format` value, one of three JSON Schema objects is returned:
   - `invoice`: fields for `invoice_number`, `vendor`, `amount`, `currency`, `issue_date`, `due_date`, `line_items`, `payment_terms`, `po_reference`.
   - `contract`: fields for `parties`, `effective_date`, `expiry_date`, `value`, `currency`, `jurisdiction`, `key_obligations`.
   - *(anything else)*: a general NER-style schema capturing `names`, `organizations`, `dates`, `amounts`, `references`, and `locations` as typed arrays.
2. **Prompt assembly** — `extract_fields` binds the input `text`, the selected `schema`, and the `format` label into a prompt context alongside a system role that instructs the model to output only a valid JSON object, omitting any fields not present in the source text.
3. **LLM generation** — `GENERATE extract(text, schema)` calls the model (configured externally via `--adapter` and `--model` CLI flags), passing the assembled prompt and schema constraint.
4. **Return** — The raw JSON object produced by the model is returned as the workflow output.

## 4. Error Handling

No EXCEPTION handlers are declared in this workflow. All error conditions (malformed JSON output, model overload, context overflow, etc.) are propagated to the SPL runtime's default exception handling.

## 5. Output

The workflow returns a single JSON object whose shape matches the selected schema:

| Scenario | Returned structure |
|----------|--------------------|
| `format = 'invoice'` | Object with invoice financial fields; absent fields omitted |
| `format = 'contract'` | Object with contract party and obligation fields; absent fields omitted |
| `format = 'general'` (default) | Object with named-entity arrays (names, orgs, dates, amounts, references, locations) |

No explicit RETURN metadata (status codes, iteration counts) is declared; the output is the raw extraction result passed through from the GENERATE call.