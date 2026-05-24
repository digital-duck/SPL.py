## Summary

This workflow extracts typed, structured data from free-form natural language text in a single LLM call. Given any prose — an employee bio, an invoice, a contract snippet — it returns a validated JSON object organized into four canonical entity categories: people, organizations, monetary amounts, and dates. Business analysts, data engineers, and document-processing pipelines benefit by eliminating hand-written parsers for unstructured input.

---

## Detailed Specification

### 1. Purpose

Extract all named entities and typed values from arbitrary free-form text and return them as a validated JSON document conforming to a predefined schema.

---

### 2. High-level Description

This workflow uses the Schema-Constrained Generation pattern: a `CREATE FUNCTION` defines a static JSON Schema that governs the exact structure the LLM must produce, and a single `GENERATE` call binds both the raw text and that schema into one extraction prompt. The `CREATE FUNCTION extract_entity_schema` acts as a pure schema fixture — it takes no parameters and emits a JSON Schema object declaring four top-level arrays (`people`, `organizations`, `amounts`, `dates`), each with typed, optionally required fields (e.g. `name` is required for people and organizations, `value` is required for amounts and dates). The `PROMPT extract_entities` sets a strict system role instructing the LLM to behave as a data extraction engine that returns only the JSON object with no surrounding explanation. The `GENERATE structured_extraction(text, schema)` call passes both the input text and the schema to the LLM and captures the result. There is no iterative refinement loop, no branching on output quality, and no side-effect tool calls — correctness is enforced entirely by the schema constraint embedded in the prompt.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `CREATE FUNCTION extract_entity_schema()` | `CREATE FUNCTION` | Returns a static JSON Schema literal; no `{param}` slots — used as a schema fixture, not a prompt template |
| `PROMPT extract_entities` | `WORKFLOW` (single-step) | Declares the extraction unit; binds `context.text` and the schema function into the generation call |
| `system_role(...)` | System prompt injection | Constrains LLM persona to strict JSON-only output; suppresses explanatory prose |
| `GENERATE structured_extraction(text, schema)` | `GENERATE ... INTO @var` | Single LLM call; result is the structured JSON document |
| `context.text` | `@text` (INPUT variable) | Supplied at runtime via `--param text="..."` CLI flag |
| `extract_entity_schema()` | Inline `@schema` binding | Schema value inlined at prompt construction time, not stored separately |

---

### 4. Logical Functions / Prompts

#### `extract_entity_schema`
- **Role:** Schema fixture. Returns the JSON Schema object that defines the required output structure.
- **Key conventions:**
  - Pure data function — no LLM call, no parameters.
  - Declares four arrays: `people` (name, age, role, salary, start_date), `organizations` (name, type, industry), `amounts` (value, currency, label), `dates` (value, label).
  - Required fields enforce minimum fidelity: `name` for entities, `value` for scalars.
  - `currency` defaults to `"USD"` when not mentioned in the source text.

#### `extract_entities` (via `GENERATE structured_extraction`)
- **Role:** Extraction prompt. Combines the input text with the schema and elicits a schema-conformant JSON response.
- **Key prompt conventions:**
  - System role: `"You are a precise data extraction engine."` — establishes zero-tolerance for hallucination or filler text.
  - Hard output constraint: `"Return only the JSON object, no explanation."` — acts as a sentinel suppressing markdown fences, prose, or apologies.
  - No scoring, no sentinel tokens, no multi-turn structure — single shot, schema governs validity.

---

### 5. Control Flow

```
Input: context.text (runtime CLI param)
  │
  ▼
CREATE FUNCTION resolves extract_entity_schema()   ← schema fixture, compile-time constant
  │
  ▼
GENERATE structured_extraction(text, schema)       ← single LLM call with system role + schema constraint
  │
  ▼
Output: JSON document (people / organizations / amounts / dates)
```

Execution is strictly linear and single-shot. There is no `WHILE` refinement loop, no `EVALUATE` branch on output quality, and no `EXCEPTION` handler. All correctness guarantees are delegated to the schema constraint passed inside the prompt.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl \
  --description "Extract all named entities and typed values from arbitrary free-form text and return them as a validated JSON document conforming to a predefined schema. Define a CREATE FUNCTION that returns a static JSON Schema with four arrays: people (name, age, role, salary, start_date), organizations (name, type, industry), amounts (value, currency defaulting to USD, label), and dates (value, label). Use a PROMPT with a strict system role instructing the LLM to return only the JSON object with no explanation. A single GENERATE call binds the input text and the schema, producing the structured output in one shot with no loops or branching." \
  --mode workflow

# Step 2 — compile to any target
spl3 splc compile structured_output.spl --lang python/langgraph
spl3 splc compile structured_output.spl --lang python/pocketflow
spl3 splc compile structured_output.spl --lang go
```