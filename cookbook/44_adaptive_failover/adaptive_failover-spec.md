## 0. High-level Description

This workflow implements an **adaptive failover** (resilience manager) pattern using a two-tier model strategy: a cheap/fast primary model is tried first, and a higher-quality fallback model is invoked transparently if the primary output fails a quality gate. The single CREATE FUNCTION `summarize` defines a senior-scientist persona prompt with a `{query}` slot, producing a detailed, technically accurate explanation covering core concepts, mechanisms, and practical significance. Control flow proceeds linearly — GENERATE into `@primary_output`, then a deterministic CALL to `check_quality` (incurring no LLM cost), followed by an EVALUATE branch that either promotes the primary output directly or re-runs the same `summarize` function via GENERATE on the fallback model. LOGGING is used throughout at INFO, DEBUG, and WARN levels to trace each decision point: model selection, quality validation result, and failover events. Two CALL side-effects write artifacts to disk (`write_file` for the raw query and the final response into `@log_dir`), creating a persistent audit trail. The single EXCEPTION handler catches `GenerationError` (covering failures from either model) and returns a degraded response with a `both_models_failed` reason rather than crashing.

---

## 1. Purpose

Answers a user query by attempting a fast, low-cost model first and automatically escalating to a stronger fallback model when the primary response fails a quality check, ensuring a reliable high-quality result without manual intervention.

---

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@query` | `'Write a detailed technical summary of quantum entanglement.'` | The question or topic to summarise |
| `@primary_model` | `'phi4-mini'` | Name of the cheap/fast model tried first |
| `@fallback_model` | `'gemma3'` | Name of the higher-quality model used if the primary fails the quality gate |
| `@log_dir` | `'cookbook/44_adaptive_failover/logs-spl'` | Directory path for writing query and response log files |

---

## 3. Process

1. Log the start of the attempt, identifying which primary model will be used (INFO).
2. CALL `write_file` to persist the raw `@query` to `<log_dir>/query.md` (no return value captured).
3. GENERATE `summarize(@query)` using `@primary_model`; store the result in `@primary_output`.
4. Log that primary generation is complete and validation is starting (DEBUG).
5. CALL `check_quality(@primary_output)` — a deterministic, zero-LLM-cost tool — storing the result string in `@quality_status`.
6. Log the quality check result (DEBUG).
7. EVALUATE `@quality_status`:
   - **WHEN** the value contains `'pass'`: log success (INFO), assign `@primary_output` directly to `@final_response`.
   - **ELSE** (quality insufficient): log a WARN with the fallback model name, then GENERATE `summarize(@query)` again using `@fallback_model` into `@final_response`, and log completion (INFO).
8. CALL `write_file` to persist `@final_response` to `<log_dir>/response.md`.
9. RETURN `@final_response` with metadata: `status='complete'`, `quality=@quality_status`, `model=@primary_model`.

---

## 4. Error Handling

- **`GenerationError`** — caught if either the primary or fallback GENERATE call fails; returns `@query` unchanged with `status='error'` and `reason='both_models_failed'`, preventing an unhandled crash while preserving the original input for diagnostics.

---

## 5. Output

| Field | Value / Source |
|---|---|
| Return value (`@final_response`) | The generated technical summary — sourced from `@primary_output` if it passed the quality gate, otherwise from the fallback model |
| `status` | `'complete'` on success; `'error'` if a `GenerationError` is caught |
| `quality` | The raw string returned by `check_quality` (e.g. `'pass'` or a failure descriptor) |
| `model` | Always set to `@primary_model`, regardless of which model actually produced the final answer |
| Side-effect: `<log_dir>/query.md` | Contains the original query string |
| Side-effect: `<log_dir>/response.md` | Contains the final response text |