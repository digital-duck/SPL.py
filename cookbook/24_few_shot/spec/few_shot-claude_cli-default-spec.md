## Summary

This workflow implements few-shot prompting — a technique that embeds curated examples directly in the prompt to guide an LLM toward a consistent output format without any model fine-tuning. It classifies arbitrary text into structured JSON by selecting domain-appropriate gold-standard examples at runtime. Data engineers, ML practitioners, and ops teams benefit by getting reliable, schema-consistent LLM output across finance, operations, and general-purpose domains.

---

## Detailed Specification

### 1. Purpose

Classify an input text into a structured JSON object by injecting domain-specific gold-standard examples into the prompt context, enabling in-context learning without fine-tuning.

---

### 2. High-level Description

This workflow applies the few-shot prompting pattern using two SPL constructs: a `CREATE FUNCTION` that selects domain-appropriate examples and a `PROMPT` template that assembles the full classifier context. The `few_shot_examples` function accepts a `domain` parameter (defaulting to `'general'`) and returns a formatted block of input/output pairs drawn from one of three domain branches — `finance`, `ops`, or the general fallback — covering tone, schema, and field conventions specific to each domain. The `few_shot_classifier` prompt composes a system role instruction, the example block from `few_shot_examples`, and the user-supplied `text` and `domain` values, then issues a single `GENERATE` call (`classify`) that produces the JSON result. There is no iterative loop or branching on LLM output; the workflow is a single-pass inference pipeline. Side effects are limited to returning the classified JSON to the caller. No explicit exception handling is declared, so runtime errors propagate to the invoking process.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW` | Implicit — single `PROMPT` block | No named `WORKFLOW` wrapper; the prompt itself is the entry point |
| `CREATE FUNCTION few_shot_examples(domain)` | `CREATE FUNCTION <name>` with `DEFAULT` param | Returns a `TEXT` block of examples; branched via `CASE` on `domain` |
| `PROMPT few_shot_classifier` | Named prompt template | Assembles `system_role`, examples, and user input into one LLM context |
| `GENERATE classify(text, examples)` | `GENERATE <fn>(...) INTO @<var>` | Single LLM inference call; result is the classified JSON |
| `system_role(...)` | SPL system-message slot | Sets LLM persona and output-format contract |
| `context.domain`, `context.text` | `@<var>` shared state | Runtime inputs passed through `context` object |
| `CASE domain WHEN ... ELSE ... END` | `EVALUATE` / branch logic | Static SQL-style dispatch, not a runtime LLM branch |

---

### 4. Logical Functions / Prompts

**`few_shot_examples(domain TEXT DEFAULT 'general')`**
- **Role:** Example provider — returns a Markdown-formatted block of labeled input/output pairs that calibrate the LLM's output schema and style.
- **Key conventions:**
  - Three domain branches: `finance` (sentiment + magnitude + topics), `ops` (status + severity + action_required), `general` (sentiment + magnitude + summary).
  - Each branch provides exactly two contrasting examples (positive/negative or healthy/incident) to establish both ends of the output spectrum.
  - Output format is always a compact JSON object on one line — no prose, no explanation.

**`few_shot_classifier`**
- **Role:** Primary classifier — binds the system role, example block, and user text into a single LLM prompt and issues the classification call.
- **Key conventions:**
  - `system_role` instructs the model to follow examples exactly, preserving field names and JSON structure.
  - `GENERATE classify(text, examples)` is the sole LLM call; the model must return only the JSON object with no surrounding text.
  - Domain is passed through both as an example selector (via `few_shot_examples`) and as a raw field in context, making it available for downstream use if needed.

---

### 5. Control Flow

Execution is strictly linear. The caller supplies `text` and optionally `domain` (default `'general'`). `few_shot_examples` evaluates the `CASE` branch at prompt-assembly time and returns the matching example block. `few_shot_classifier` assembles the full prompt and issues a single `GENERATE` call. The result — a JSON object — is returned directly to the caller. There is no `WHILE` loop, no `EVALUATE` on LLM output, and no retry logic.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Classify an input text into a structured JSON object by injecting domain-specific gold-standard examples into the prompt context, enabling in-context learning without fine-tuning." --mode workflow

# Step 2 — compile to any target
spl3 splc compile few_shot.spl --lang python/pocketflow
spl3 splc compile few_shot.spl --lang python/langgraph
spl3 splc compile few_shot.spl --lang go
```