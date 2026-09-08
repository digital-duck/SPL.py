## 0. High-level Description

This script implements a **schema-constrained entity extraction** pattern using two SPL constructs: a `CREATE FUNCTION` that returns a static JSON Schema object (`extract_entity_schema`), and a `PROMPT` block (`extract_entities`) that combines a `system_role` instruction, the raw input text, and the schema into a single `GENERATE` call. The `system_role` directive explicitly instructs the LLM to act as a "precise data extraction engine" and to return *only* valid JSON with no surrounding explanation — a sentinel-free, format-constrained output convention. The generated call `structured_extraction(text, schema)` passes both the free-form text and the schema to the model, making the schema itself part of the prompt context so the LLM is bound to its structure at inference time. There is no WHILE loop, EVALUATE branch, EXCEPTION handling, or CALL side-effect in this script; it is a single-pass, stateless extraction designed for direct invocation via the `spl3 run` CLI with `--adapter` and `--model` flags selecting the underlying LLM.

---

## 1. Purpose

Extract typed, structured JSON data (people, organizations, monetary amounts, and dates) from a single free-form text string using a schema-constrained LLM generation call.

---

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `text` | *(required)* | Free-form natural-language text from which entities are to be extracted; passed via `context.text` at runtime |

---

## 3. Process

1. **Define the extraction schema** — `CREATE FUNCTION extract_entity_schema()` is evaluated, returning a static JSON Schema object describing four top-level arrays: `people`, `organizations`, `amounts`, and `dates`, each with typed property definitions and `required` field constraints.
2. **Assemble the prompt** — The `PROMPT extract_entities` block constructs the LLM prompt from three components:
   - A `system_role` that frames the model as a data extraction engine and enforces JSON-only output.
   - `context.text` — the runtime input text to be parsed.
   - The output of `extract_entity_schema()` — the schema the model must conform to.
3. **Generate structured output** — `GENERATE structured_extraction(text, schema)` sends the assembled prompt to the configured LLM backend (selected at CLI invocation via `--adapter` and `--model`). The model is expected to return a single valid JSON object matching the schema, with no prose wrapper.

---

## 4. Error Handling

*No `EXCEPTION` blocks are declared in this script.* There is no explicit handling for malformed JSON output, missing required fields, model overload, or context length limits. Error handling is delegated entirely to the SPL runtime and the invoking caller.

---

## 5. Output

The workflow returns the raw JSON object produced by `GENERATE structured_extraction`. The expected structure is:

```json
{
  "people":        [ { "name": "...", "age": 0, "role": "...", "salary": 0.0, "start_date": "YYYY-MM-DD" } ],
  "organizations": [ { "name": "...", "type": "...", "industry": "..." } ],
  "amounts":       [ { "value": 0.0, "currency": "USD", "label": "..." } ],
  "dates":         [ { "value": "...", "label": "..." } ]
}
```

There is no `RETURN` statement with explicit status codes or metadata fields; the output is the bare generation result. Arrays for entity types not present in the input text are expected to be empty or omitted by the model.