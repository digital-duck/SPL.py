## 0. High-level Description

This script implements the **few-shot prompting** (in-context learning) pattern: rather than fine-tuning a model, it embeds gold-standard input/output pairs directly in the prompt to calibrate the model's output format and style. The single `CREATE FUNCTION` — `few_shot_examples` — acts as a domain-aware example bank, using a SQL-style `CASE` expression keyed on a `domain` parameter to return one of three curated example sets: `finance` (sentiment/magnitude/topics/summary JSON), `ops` (status/severity/action_required/summary JSON), or a general fallback (sentiment/magnitude/summary JSON). The `PROMPT few_shot_classifier` block assembles the full LLM context declaratively via a `SELECT`, composing a strict `system_role` instruction, the domain-matched examples from `few_shot_examples(context.domain)`, and the raw input text from `context.domain` and `context.text`. A single `GENERATE classify(text, examples)` call then invokes the configured LLM adapter and model (supplied at runtime via CLI flags) to produce structured JSON output. This script contains no `WHILE` loop, no `EVALUATE` branch, no `RETURN` metadata, no `CALL` side-effects, no `LOGGING`, and no `EXCEPTION` handlers — it is intentionally a lean, single-shot classification primitive.

---

## 1. Purpose

Classify an arbitrary text string into a structured JSON object (sentiment, severity, topics, etc.) by priming the LLM with domain-specific gold-standard examples, requiring no model fine-tuning.

---

## 2. Inputs

| Parameter | Default | Description |
|-----------|---------|-------------|
| `text` | *(required)* | The raw text string to be classified |
| `domain` | `'general'` | Controls which example set is injected: `finance`, `ops`, or the general fallback |
| `--adapter` | *(CLI flag)* | LLM backend adapter (e.g. `ollama`) |
| `--model` | *(CLI flag)* | Specific model to use with the adapter (e.g. `gemma3`) |

> `text` and `domain` are passed via CLI `--key=value` flags and surfaced as `context.text` / `context.domain` inside the prompt block. `adapter` and `model` are runtime harness flags, not declared `INPUT` variables.

---

## 3. Process

1. **Resolve examples** — `few_shot_examples(context.domain)` evaluates the `CASE` expression:
   - `'finance'` → two annotated finance examples with `sentiment`, `magnitude`, `topics`, `summary` fields.
   - `'ops'` → two annotated ops examples with `status`, `severity`, `action_required`, `summary` fields.
   - anything else → two general examples with `sentiment`, `magnitude`, `summary` fields.

2. **Assemble prompt** — The `PROMPT few_shot_classifier` SELECT constructs the LLM context from three parts:
   - A `system_role` instruction ordering the model to follow the examples exactly, match field names, and return only the JSON object.
   - The domain-matched example block (labelled `examples`).
   - The user-supplied text (labelled `text`) and domain tag (labelled `domain`).

3. **Generate output** — `GENERATE classify(text, examples)` dispatches the assembled prompt to the configured LLM adapter/model and receives a single JSON object matching the schema implied by the injected examples.

---

## 4. Error Handling

*No `EXCEPTION` handlers are declared in this script.* Any model errors, adapter failures, or malformed outputs propagate as unhandled runtime exceptions to the calling harness (`spl3 run`).

---

## 5. Output

The workflow produces the raw JSON object emitted by the LLM — structured according to the domain branch matched:

| Domain | JSON fields returned |
|--------|----------------------|
| `finance` | `sentiment`, `magnitude`, `topics[]`, `summary` |
| `ops` | `status`, `severity`, `action_required` (bool), `summary` |
| `general` | `sentiment`, `magnitude`, `summary` |

There is no `RETURN` statement, so no explicit `status` code or workflow-level metadata is attached. The output is the raw `GENERATE` result passed directly to stdout by the `spl3` harness.