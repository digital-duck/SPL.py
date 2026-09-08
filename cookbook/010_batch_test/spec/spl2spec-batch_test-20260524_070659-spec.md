## Summary

Batch Test automates quality assurance across key cookbook recipes by running each recipe simultaneously against two configurable LLM models and producing a structured PASS/FAIL report. It replaces a manual shell script with a declarative SPL workflow that fans out six LLM calls in parallel, then uses a judge model to evaluate and summarize the results. QA engineers and CI/CD pipelines benefit by getting a fast, consistent signal on whether the target models are functioning correctly.

---

## Detailed Specification

### 1. Purpose

Run three canonical cookbook recipes against two user-specified LLM models in parallel and produce a concise, structured PASS/FAIL report that indicates whether each model handled each recipe correctly.

---

### 2. High-level Description

The workflow `batch_test` accepts two model identifiers as `INPUT` parameters (`@model_1` defaulting to `gemma3`, `@model_2` defaulting to `llama3.2`) and produces a `@report TEXT` as `OUTPUT`. Using a parallel CTE fan-out — the SPL equivalent of `CALL PARALLEL` — it dispatches six LLM calls simultaneously: each of the three recipes (Hello World, Ollama Proxy, Multilingual) is invoked once per model, with inline `PROMPT … GENERATE … USING MODEL` blocks bound to either `@model_1` or `@model_2`. All six results are collected into named `@vars` via a single `SELECT … INTO` clause. A single `GENERATE summarize_results(…) INTO @report` call then feeds all six raw outputs along with both model names into the `summarize_results` prompt template, which acts as an LLM judge: it applies a PASS/FAIL criterion (non-empty and coherent = PASS; empty, erroneous, or nonsensical = FAIL) and formats one result line per recipe–model pair, ending with a totals summary. The workflow concludes with `RETURN @report WITH status='complete'` on success, or with `status='error'` in the `EXCEPTION WHEN GenerationError` handler if any generation call fails.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW batch_test` | `WORKFLOW` | Named workflow with `INPUT:` / `OUTPUT:` declarations |
| `INPUT: @model_1, @model_2 … DEFAULT` | `@var` with default binding | Parameters are resolved at call time; defaults used when not supplied |
| `CREATE FUNCTION summarize_results(…)` | `CREATE FUNCTION` | Prompt template with `{param}` slots; acts as LLM judge for PASS/FAIL scoring |
| `WITH … (PROMPT … GENERATE … USING MODEL)` | `CALL PARALLEL` | Six-branch parallel fan-out; each CTE is an independent LLM call dispatched concurrently |
| `GENERATE summarize_results(…) INTO @report` | `GENERATE … INTO @var` | Single aggregation call; LLM judge synthesizes all six raw outputs into report |
| `SELECT … INTO @hello_m1, …, @multi_m2` | `@var` shared state | Six result variables bound from the parallel CTE outputs into workflow scope |
| `RETURN @report WITH status='complete'` | `RETURN WITH status=` | Non-trivial status token; distinguishes successful completion from error path |
| `RETURN … WITH status='error'` | `RETURN WITH status=` | Exception exit path; status token drives caller-side error handling |
| `EXCEPTION WHEN GenerationError THEN` | `EXCEPTION WHEN` | Typed error recovery; catches any generation failure across the parallel fan-out |

---

### 4. Logical Functions / Prompts

**`summarize_results`**

- **Role:** LLM judge / report aggregator. Receives all six raw model outputs and both model names, then evaluates each output against a binary PASS/FAIL criterion and emits a formatted report.
- **Key prompt conventions:**
  - Criterion is explicit and binary: PASS = non-empty + coherent; FAIL = empty, error, or nonsensical.
  - Output format is strictly specified: one `PASS/FAIL  recipe_name  (model)` line per result, followed by a mandatory totals line (`Results: X/Y passed, Z failed`).
  - No scoring rubric or partial credit — the sentinel token is the verdict word (`PASS` / `FAIL`) at the start of each line, enabling downstream parsing.

**Inline recipe prompts (within CTEs)**

Three inline prompt patterns, each instantiated twice (once per model):

| Recipe | System role | Prompt input |
|---|---|---|
| `hello_world` | "helpful assistant, say hello briefly" | No user input; calls `greeting()` |
| `ollama_proxy` | "helpful, knowledgeable assistant" | `'hello'` as `prompt` |
| `multilingual` | "multilingual assistant" | `'hello'` as `user_input`, `'English'` as `lang` |

These are smoke-test prompts — intentionally minimal so any coherent response constitutes a PASS.

---

### 5. Control Flow

The execution path is a **fan-out / aggregate** pattern with no iterative loop:

1. **Parallel fan-out** — all six CTE branches (`hello_m1`, `hello_m2`, `proxy_m1`, `proxy_m2`, `multi_m1`, `multi_m2`) execute concurrently via the parallel CTE block. Results are collected into six `@vars`.
2. **Aggregate** — `GENERATE summarize_results(…) INTO @report` submits all six outputs plus both model names to the judge model in a single call.
3. **Termination** — `RETURN @report WITH status='complete'` exits the workflow. If any generation call raises `GenerationError`, the `EXCEPTION WHEN GenerationError` handler intercepts it and returns a fixed error string with `status='error'`, bypassing the report generation step entirely.

There is no `WHILE` loop and no `EVALUATE` branch — the control flow is a single linear pass: parallel execution → judge call → return.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Run three canonical cookbook recipes against two \
user-specified LLM models in parallel and produce a concise, structured PASS/FAIL \
report that indicates whether each model handled each recipe correctly." \
--mode workflow

# Step 2 — compile to any target
spl3 splc compile batch_test.spl --lang python/pocketflow
spl3 splc compile batch_test.spl --lang python/langgraph
spl3 splc compile batch_test.spl --lang go
```