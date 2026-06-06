## 0. High-level Description

This workflow implements a **model showdown** (parallel fan-out + judge) pattern in which the same user prompt is dispatched simultaneously to three distinct Ollama-backed models using a parallel CTE construct, then a neutral evaluator synthesizes all three responses into a single comparative report. Two CREATE FUNCTIONs drive the pipeline: `answer`, a minimal pass-through template that forwards the raw prompt verbatim to each model, and `compare_responses`, a structured evaluator prompt that first reproduces each model's raw output under a named sentinel banner (`=== {model_name} ===`) and then delivers per-model assessments of quality, strengths, and weaknesses before naming a winner. The three `answer` GENERATEs execute inside named CTE branches (`response_1`, `response_2`, `response_3`), each bound to a different model via `USING MODEL @model_N`, and their results are collected into `@answer_1`, `@answer_2`, `@answer_3` before being passed together to a single `compare_responses` GENERATE that runs on the default (or caller-supplied) model. The RETURN carries a `status = 'complete'` flag alongside the three model-name metadata fields so callers can identify which models participated. A single EXCEPTION handler catches `GenerationError` — any model failure during generation — and short-circuits to a `status = 'error'` RETURN with a human-readable message rather than propagating a hard crash.

## 1. Purpose

Send an identical prompt to three configurable Ollama models in parallel, then produce a side-by-side comparative evaluation that identifies the most helpful response.

## 2. Inputs

| Parameter | Default | Description |
|-----------|---------|-------------|
| `@prompt` | `'What is the meaning of life?'` | The question or instruction sent verbatim to all three models |
| `@model_1` | `'gemma3'` | Name of the first Ollama model to query |
| `@model_2` | `'phi4'` | Name of the second Ollama model to query |
| `@model_3` | `'qwen2.5'` | Name of the third Ollama model to query |

## 3. Process

1. **Parallel generation** — Three CTE branches (`response_1`, `response_2`, `response_3`) each invoke the `answer` function with `@prompt` as their sole argument. Each branch sets the system role to `"You are a helpful, knowledgeable assistant."` and targets a different model via `USING MODEL @model_1 / @model_2 / @model_3`. Because they are expressed as parallel CTEs, all three GENERATE calls are dispatched concurrently.
2. **Result collection** — The SELECT projection pulls `answer` out of each CTE and binds the three values INTO `@answer_1`, `@answer_2`, `@answer_3`.
3. **Comparative evaluation** — A single GENERATE call invokes `compare_responses` with all six arguments (`@prompt`, the three model names, and their three answers). This prompt instructs the evaluator to: (a) reproduce each raw response verbatim under its sentinel header, (b) assess each response for quality, strengths, and weaknesses, and (c) declare a winner with justification. The result is stored INTO `@comparison`.
4. **Return** — The workflow RETURNs `@comparison` with metadata: `status = 'complete'` and the resolved names of all three models.

## 4. Error Handling

- **`GenerationError`** — If any of the three parallel model queries (or the evaluator GENERATE) raises a generation error, the workflow catches it and returns the string `'One or more models failed to respond.'` with `status = 'error'`. No partial results are surfaced; the entire run is treated as failed.

## 5. Output

| Field | Value |
|-------|-------|
| Return variable | `@comparison` — full Markdown/text report containing raw responses (under sentinel banners) and the evaluator's comparative analysis |
| `status` | `'complete'` on success; `'error'` on GenerationError |
| `model_1` | Resolved name of the first model used |
| `model_2` | Resolved name of the second model used |
| `model_3` | Resolved name of the third model used |