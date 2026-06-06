## 0. High-level Description

This workflow implements a **parallel fan-out / aggregate-report** pattern to batch-test three cookbook recipes across two configurable LLM models simultaneously. It uses SPL's `WITH` CTE syntax to issue all six recipe × model combinations — `hello_world`, `ollama_proxy`, and `multilingual` — as concurrent `GENERATE` calls, each driven by either the `@model_1` or `@model_2` INPUT parameter, so no combination blocks another. The six results are projected via `SELECT … INTO` a matching set of OUTPUT variables, then fed into a single `CREATE FUNCTION summarize_results` prompt template that instructs an LLM acting as a "test reporter" to evaluate each output against a simple coherence criterion (non-empty, non-erroneous, non-nonsensical) and emit structured `PASS`/`FAIL` lines followed by a summary tally. The workflow `RETURN`s the report text with `status = 'complete'` and echoes back both model names as metadata, giving callers a self-contained audit record. A single `EXCEPTION WHEN GenerationError` guard catches any LLM-level failure across the entire fan-out phase and short-circuits to a `status = 'error'` return, avoiding partial or misleading reports.

## 1. Purpose

Automatically exercises three SPL cookbook recipes against two user-supplied models in parallel and produces a single structured `PASS`/`FAIL` report summarising the results.

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@model_1` | `gemma3` | First LLM model identifier passed to every recipe CTE |
| `@model_2` | `llama3.2` | Second LLM model identifier passed to every recipe CTE |

## 3. Process

1. **Fan out in parallel** — Six CTEs execute concurrently via `WITH`:
   - `hello_m1` / `hello_m2`: each sends a brief "say hello" system role prompt to `@model_1` / `@model_2` respectively, `GENERATE`-ing a `greeting`.
   - `proxy_m1` / `proxy_m2`: each sends the literal string `'hello'` as a user prompt to a general-purpose assistant role, `GENERATE`-ing an `answer`.
   - `multi_m1` / `multi_m2`: each asks a multilingual assistant to respond to `'hello'` in English, `GENERATE`-ing a `response`.
2. **Collect results** — A `SELECT … INTO` projects all six CTE outputs into variables `@hello_m1`, `@hello_m2`, `@proxy_m1`, `@proxy_m2`, `@multi_m1`, `@multi_m2`.
3. **Generate report** — `GENERATE summarize_results(…) INTO @report` calls the `summarize_results` function, passing both model names and all six outputs. The function's prompt instructs the LLM to classify each result as `PASS` (non-empty, coherent) or `FAIL` (empty, erroneous, or nonsensical), format each judgement as `PASS|FAIL  recipe_name  (model)`, and conclude with a `Results: X/Y passed, Z failed` summary line.
4. **Return** — `RETURN @report WITH status = 'complete', model_1 = @model_1, model_2 = @model_2`.

## 4. Error Handling

- **`GenerationError`** — If any `GENERATE` call in the fan-out phase or the report-generation step raises a generation-level error, the workflow immediately returns the string `'Batch test failed during generation.'` with `status = 'error'`, discarding any partial results.

## 5. Output

| Field | Value / Type |
|---|---|
| `@report` | `TEXT` — multi-line `PASS`/`FAIL` report followed by a tally line |
| `status` | `'complete'` on success; `'error'` on `GenerationError` |
| `model_1` | Echo of the `@model_1` input (success path only) |
| `model_2` | Echo of the `@model_2` input (success path only) |