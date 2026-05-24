## Summary

Bedrock Quickstart fans a single user prompt out to three AWS Bedrock models simultaneously, collects their independent answers, and then runs a neutral judge evaluation that identifies the most accurate, most concise, and best production-ready response. It exists to give engineers and architects a fast, side-by-side quality baseline when selecting a Bedrock model for a new use case. Any team evaluating AWS-hosted LLMs benefits without writing custom comparison scaffolding.

---

## Detailed Specification

### 1. Purpose

Fan a single prompt to three AWS Bedrock models in parallel and produce a structured judge evaluation identifying the strongest response for accuracy, concision, and production suitability.

---

### 2. High-level Description

This workflow implements the **multi-model fan-out + judge** pattern entirely within SPL. On entry, `WORKFLOW bedrock_quickstart` accepts a free-text `@prompt` and three Bedrock model identifiers (`@model_1`, `@model_2`, `@model_3`), all with sensible defaults (Claude Sonnet 4, Claude Haiku 4.5, Amazon Nova Pro). It dispatches the identical prompt to all three models concurrently via a `CALL PARALLEL` fan-out expressed as SQL-style CTEs, capturing each answer into `@answer_1`, `@answer_2`, and `@answer_3`. Once all three branches complete, a single `GENERATE` call invokes the `compare_models` function — a neutral evaluator prompt that reproduces each raw response verbatim and then provides a comparative verdict on accuracy, concision, and production readiness — storing the result in `@comparison`. The workflow terminates with `RETURN @comparison WITH status='complete'` and emits the three model identifiers as metadata. If any Bedrock call fails, an `EXCEPTION WHEN GenerationError` handler intercepts the error and returns a diagnostic message with `status='error'`, guiding the user to check region settings, model-access grants, and IAM permissions.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW bedrock_quickstart` | `WORKFLOW` | Top-level named orchestration unit with `INPUT:` / `OUTPUT:` declarations |
| `CREATE FUNCTION compare_models(...)` | `CREATE FUNCTION` | Reusable prompt template with `{param}` slots; produces the judge evaluation |
| `WITH response_1 AS (...), response_2 AS (...), response_3 AS (...)` | `CALL PARALLEL ... END` | Concurrent fan-out; all three Bedrock calls are dispatched simultaneously via `asyncio.gather` |
| `GENERATE answer(prompt) USING MODEL @model_N` (per CTE branch) | `GENERATE <fn>(...) INTO @var` | One LLM call per branch; model binding is runtime-resolved from the `@model_N` variable |
| `GENERATE compare_models(...) INTO @comparison` | `GENERATE <fn>(...) INTO @var` | Aggregation step; judge model receives all three raw answers |
| `@prompt`, `@model_1–3`, `@answer_1–3`, `@comparison` | SPL `@vars` | Shared mutable state passed across parallel branches and sequential steps |
| `RETURN @comparison WITH status='complete', model_1=..., model_2=..., model_3=...` | `RETURN @var WITH k=v, ...` | Workflow exit with metadata; `status='complete'` signals success to any calling workflow |
| `EXCEPTION WHEN GenerationError THEN ... WITH status='error'` | `EXCEPTION WHEN <Type> THEN` | Typed error recovery; `status='error'` propagates failure to the caller |

---

### 4. Logical Functions / Prompts

#### `compare_models`

- **Role:** Judge / aggregator. Runs after the parallel fan-out completes and receives all three raw answers.
- **Key prompt conventions:**
  - Instructs the model to reproduce each raw response verbatim under a labeled delimiter (`=== {model_id} ===`) before evaluating — preventing hallucinated paraphrasing.
  - Asks three distinct evaluative sub-questions (most accurate, most concise, best for production + justification), keeping the evaluation structured and skimmable.
  - Uses a neutral framing ("You are a neutral evaluator") to reduce anchoring bias toward any single provider family.
  - No sentinel tokens or numeric scores — output is free-form prose suitable for direct human consumption.

#### Implicit per-branch prompt (CTE branches)

- **Role:** Worker / answer generator. Each of the three parallel branches sends the raw `@prompt` with a generic helpful-assistant system role.
- **Key prompt conventions:**
  - Identical system role across all three branches ensures that model personality differences — not prompt engineering differences — drive divergent answers.
  - No output-format constraints; each model answers in its natural style, which the judge then compares.

---

### 5. Control Flow

The execution path is a two-stage pipeline with no loops or semantic branching in the happy path:

1. **Parallel fan-out** — All three `GENERATE answer(prompt) USING MODEL @model_N` calls are issued concurrently. The workflow waits until all three complete before advancing.
2. **Sequential aggregation** — `GENERATE compare_models(...)` runs once, serially, after all three answers are bound.
3. **Termination** — `RETURN @comparison WITH status='complete'` exits the workflow, emitting model-identifier metadata alongside the result.
4. **Error path** — If `GenerationError` is raised at any point (parallel or aggregation), the `EXCEPTION` handler short-circuits execution and returns a human-readable error string with `status='error'`.

There is no `WHILE` loop and no `EVALUATE` branch — the workflow is deliberately stateless and single-pass to maximize speed and reproducibility as an evaluation baseline.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "Fan a single prompt to three AWS Bedrock models in parallel \
and produce a structured judge evaluation identifying the strongest response for accuracy, \
concision, and production suitability." --mode workflow

# Step 2 — compile to any target
spl3 splc compile bedrock_quickstart.spl --lang python/pocketflow
spl3 splc compile bedrock_quickstart.spl --lang python/langgraph
spl3 splc compile bedrock_quickstart.spl --lang go

# Step 3 — run against Bedrock directly
spl3 run bedrock_quickstart.spl --adapter bedrock \
    prompt="Explain the CAP theorem in two sentences."

# Step 4 — override models at runtime (no .spl edits needed)
spl3 run bedrock_quickstart.spl --adapter bedrock \
    model_1="anthropic.claude-opus-4-0-20250514-v1:0" \
    model_2="anthropic.claude-3-5-haiku-20241022-v1:0" \
    model_3="amazon.nova-lite-v1:0" \
    prompt="What are the main trade-offs between SQL and NoSQL databases?"
```