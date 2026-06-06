## Summary

This workflow extracts typed, structured data from free-form natural language text by constraining the LLM to return a JSON object that conforms to a predefined schema. It is useful for developers and data engineers who need to parse unstructured inputs—such as employee records, invoices, or contracts—into machine-readable form without writing brittle regex or parsing logic. The schema-constrained generation approach guarantees the output is valid JSON with typed fields.

---

## Detailed Specification

### 1. Purpose

Extract structured, typed entity data (people, organizations, monetary amounts, and dates) from arbitrary free-form text by generating a schema-conformant JSON object in a single LLM call.

### 2. High-level Description

This workflow implements a **schema-constrained single-shot extraction** pattern using SPL. A `CREATE FUNCTION` named `extract_entity_schema` defines the JSON Schema that governs what the LLM must produce; it declares four top-level arrays—`people`, `organizations`, `amounts`, and `dates`—each with typed properties and required fields. A second construct, the `PROMPT extract_entities` block, acts as a `CREATE FUNCTION`-style prompt template that injects the input text and the schema into a `GENERATE` call named `structured_extraction`. The system role instructs the model to act as a "precise data extraction engine" and to return only the raw JSON object with no surrounding explanation, which is a common sentinel convention for structured output. There is no iterative loop (`WHILE`) or conditional branching (`EVALUATE`) in this recipe—control flow is linear: schema definition → prompt assembly → single generation → result. The result is stored in an implicit output variable (`@result`) and returned to the caller. No file writes or external tool calls (`CALL`) are involved.

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW` | Implicit single-prompt workflow | No explicit `WORKFLOW` block; the recipe is a self-contained extraction unit |
| `CREATE FUNCTION extract_entity_schema()` | `CREATE FUNCTION` | Returns a static JSON Schema literal; no `{param}` slots needed |
| `PROMPT extract_entities` | `CREATE FUNCTION` (prompt template) | Assembles system role, input text, and schema for the generation call |
| `GENERATE structured_extraction(text, schema)` | `GENERATE <fn>(...) INTO @<var>` | Single LLM call; output is the structured JSON result |
| Shared state | `@text`, `@schema` | Input text passed via `context.text`; schema injected via function return |
| `system_role(...)` | Prompt convention | Instructs model to return only raw JSON—acts as output-format sentinel |

### 4. Logical Functions / Prompts

**`extract_entity_schema`**
- **Role:** Schema provider — defines the contract the LLM output must satisfy.
- **Key conventions:** Returns a pure JSON Schema object with `type: object` at the root. Four typed arrays (`people`, `organizations`, `amounts`, `dates`) each have `required` fields to anchor extraction. No LLM call is made; this is a deterministic data function.

**`extract_entities` / `structured_extraction`**
- **Role:** Core extraction prompt — binds input text and schema, then calls the LLM.
- **Key conventions:**
  - `system_role` sets the persona as "a precise data extraction engine."
  - Explicit instruction: *"Return only the JSON object, no explanation."* This is the sentinel that suppresses markdown fences, prose, or chain-of-thought leakage.
  - `context.text` is injected as the raw input; `extract_entity_schema()` is injected as the structural constraint.
  - Output format: valid JSON object conforming to the schema.

### 5. Control Flow

Execution is strictly linear:

1. **Schema definition** — `extract_entity_schema()` is evaluated, producing the JSON Schema object.
2. **Prompt assembly** — `extract_entities` binds `context.text` and the schema into the generation context.
3. **Single generation** — `GENERATE structured_extraction(text, schema)` sends one request to the LLM and captures the JSON result.
4. **Termination** — the result is returned to the caller; no retry, loop, or branch occurs.

There are no `WHILE` loops, `EVALUATE` branches, or non-trivial `RETURN` statuses in this workflow.

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Extract structured, typed entity data (people, organizations, monetary amounts, and dates) from arbitrary free-form text by generating a schema-conformant JSON object in a single LLM call." --mode workflow

# Step 2 — compile to any target
spl3 splc compile structured_output.spl --lang python/pocketflow
spl3 splc compile structured_output.spl --lang python/langgraph
spl3 splc compile structured_output.spl --lang go
```