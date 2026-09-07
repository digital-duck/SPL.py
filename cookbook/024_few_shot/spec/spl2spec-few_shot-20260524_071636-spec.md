## Summary

Few-Shot Prompting is a workflow that classifies arbitrary text into a structured JSON response by embedding gold-standard input/output examples directly in the LLM prompt. It requires no model fine-tuning — the examples themselves teach the model the expected output schema and tone at inference time. Content analysts, operations engineers, and developers benefit by getting consistent, schema-conformant classifications across domains without retraining.

---

## Detailed Specification

### 1. Purpose

Classify an input text into a domain-specific structured JSON object by guiding the LLM with embedded gold-standard examples, ensuring consistent output format without fine-tuning.

### 2. High-level Description

This workflow implements the in-context learning (few-shot prompting) pattern using two SPL constructs: a `CREATE FUNCTION` that supplies domain-calibrated examples, and a `GENERATE` step that performs the classification. The `CREATE FUNCTION few_shot_examples` accepts a `domain` parameter (`finance`, `ops`, or `general`) and returns a block of curated input/output pairs that establish the expected JSON schema, field names, and tone for that domain. The `PROMPT few_shot_classifier` assembles a context object combining a strict system role instruction, the domain examples, and the raw input text, then issues a single `GENERATE` call to produce the classified JSON output. Control flow is entirely linear — one function lookup followed by one LLM call — with no loops or branches. The system role pins the model to exact structural compliance ("Return only the JSON object"), making the examples the sole format signal. The domain parameter allows the same workflow to serve finance teams (sentiment + magnitude + topics), operations engineers (status + severity + action_required), and general users (sentiment + magnitude + summary) without any code changes.

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `CREATE FUNCTION few_shot_examples(domain)` | `CREATE FUNCTION` | Parameterized template returning domain-keyed example blocks; `domain` defaults to `'general'` |
| `SELECT CASE domain WHEN ... END` | Conditional inside `CREATE FUNCTION` body | Selects the correct example block at call time based on the `domain` parameter |
| `PROMPT few_shot_classifier` | `WORKFLOW` (single-step) | Declares the named classification prompt unit; assembles context from function output + input variables |
| `system_role(...)` | System prompt slot in `GENERATE` | Instructs the model to follow examples exactly and return only JSON |
| `GENERATE classify(text, examples)` | `GENERATE ... INTO @var` | Single LLM call; result is the structured JSON classification |
| `context.domain`, `context.text` | SPL `@vars` | Shared state carrying the runtime inputs through the prompt assembly step |

### 4. Logical Functions / Prompts

**`few_shot_examples(domain TEXT DEFAULT 'general')`**
- **Role:** Example bank / format calibrator. Supplies the LLM with 2 gold-standard input→output pairs for the requested domain, establishing the exact JSON schema and value conventions before the real input is presented.
- **Key conventions:**
  - Uses a `### Examples` sentinel header to delimit the example block from the main instruction.
  - Each example follows a strict `Input: "..." / Output: {...}` two-line pattern.
  - Finance domain: fields `sentiment`, `magnitude` (0–1 float), `topics` (array), `summary`.
  - Ops domain: fields `status`, `severity`, `action_required` (bool), `summary`.
  - General domain: fields `sentiment`, `magnitude`, `summary`.

**`few_shot_classifier`**
- **Role:** The classification prompt. Combines the system role, the domain example block, and the input text into a single LLM context, then generates the JSON output.
- **Key conventions:**
  - `system_role` enforces strict format compliance ("Follow the examples exactly — same JSON structure, same field names. Return only the JSON object.").
  - No chain-of-thought, no explanation — pure structured output.
  - Domain is forwarded into context so downstream consumers know which schema applies.

### 5. Control Flow

Execution is strictly linear. At invocation, the runtime binds `context.text` and `context.domain` (defaulting to `'general'` if omitted). The `few_shot_examples` function is evaluated immediately, selecting the matching `CASE` branch to produce the example block. The `PROMPT few_shot_classifier` then assembles the full context — system role + examples + input text — and issues a single `GENERATE` call to the configured LLM adapter. The result (a JSON object) is returned directly. There are no `WHILE` loops, no `EVALUATE` branches, and no `EXCEPTION` handlers; the workflow terminates after the single generation step.

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Classify an input text into a domain-specific structured JSON object by guiding the LLM with embedded gold-standard examples, ensuring consistent output format without fine-tuning. Use a CREATE FUNCTION that accepts a domain parameter (finance, ops, general) and returns two curated input/output example pairs that establish the expected JSON schema for that domain. Use a PROMPT with a strict system_role instruction and a single GENERATE call that combines the domain examples with the input text to produce the classified JSON output." --mode workflow

# Step 2 — compile to any target
spl3 splc compile few_shot.spl --lang python/pocketflow
spl3 splc compile few_shot.spl --lang python/langgraph
spl3 splc compile few_shot.spl --lang go
```