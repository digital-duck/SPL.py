## 0. High-level Description

This workflow implements a **prompt A/B testing** pattern that compares two prompt variants against the same task and automatically selects a winner using data-driven LLM scoring. The design is hybrid: deterministic CALL steps handle catalog loading and score extraction, while GENERATE steps invoke the LLM for response generation and evaluation. A single CREATE FUNCTION — `scoring_rubric` — defines a four-criterion rubric (clarity, completeness, relevance, engagement, each 0–10) and enforces a strict JSON-only output format with a `total` field and a one-sentence `rationale`; this function is passed inline as an argument to `evaluate_response`, making the rubric a reusable, composable prompt fragment rather than a hardcoded string. Control flow relies entirely on an EVALUATE branch rather than a WHILE loop: the difference `(@score_a - @score_b)` is tested against `@winner_threshold` in three branches — A wins, B wins, or tie — and each branch issues its own RETURN with structured metadata (`winner`, `score_a`, `score_b`, `margin`). There is no multi-model design; a single model drives all GENERATE calls, selected externally via `--adapter` and `--model` CLI flags. The workflow supports two operating modes — loading a pre-built experiment from a catalog via `experiment_id` (including a `list` sentinel value to discover available experiments) or supplying an ad-hoc `task`/`prompt_a`/`prompt_b` directly — with the CALL to `load_experiment` producing an empty context that is gracefully ignored in the latter case. A single EXCEPTION handler catches `GenerationError` and returns a short error string with `status = 'error'`, providing a minimal but explicit failure boundary around all LLM generation steps.

---

## 1. Purpose

Automatically compare two prompt variants on a given task by generating one response per variant, scoring both with an LLM rubric, and returning the higher-scoring response (or a formatted tie) together with numeric scores and margin metadata.

---

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@experiment_id` | `''` (empty string) | ID of a pre-built experiment in the catalog (`experiments.json`). Pass `list` to discover available experiments. Leave blank for ad-hoc mode. |
| `@task` | `''` | The task or question both prompt variants must answer. Used directly in ad-hoc mode; overridden by catalog data when `@experiment_id` is set. |
| `@prompt_a` | `''` | Variant A prompt instruction / framing. Used directly in ad-hoc mode; overridden by catalog data when `@experiment_id` is set. |
| `@prompt_b` | `''` | Variant B prompt instruction / framing. Used directly in ad-hoc mode; overridden by catalog data when `@experiment_id` is set. |
| `@winner_threshold` | `1.5` | Minimum score difference required to declare a winner. Differences within ±threshold are classified as a tie. |

---

## 3. Process

1. **Load experiment context** — CALL `load_experiment(@experiment_id)` into `@experiment_context`. This is a deterministic (non-LLM) tool call. If `@experiment_id` is blank, `@experiment_context` is empty and the raw `@task`/`@prompt_a`/`@prompt_b` inputs are used as-is in subsequent steps.
2. **Generate Variant A response** — GENERATE `run_variant_a(@task, @prompt_a, @experiment_context)` into `@response_a`. The LLM answers the task using the Variant A prompt framing and any catalog context.
3. **Generate Variant B response** — GENERATE `run_variant_b(@task, @prompt_b, @experiment_context)` into `@response_b`. Same as above using the Variant B framing.
4. **Score Variant A** — GENERATE `evaluate_response(@response_a, @task, scoring_rubric())` into `@score_a_json`. The LLM receives the rubric inline and returns a JSON object with four criterion scores, a `total`, and a `rationale`.
5. **Score Variant B** — GENERATE `evaluate_response(@response_b, @task, scoring_rubric())` into `@score_b_json`. Identical evaluation applied to Variant B.
6. **Extract numeric totals** — CALL `extract_score_total(@score_a_json)` into `@score_a` and CALL `extract_score_total(@score_b_json)` into `@score_b`. Deterministic JSON parsing; no LLM involved.
7. **Decide winner via EVALUATE** — compute `(@score_a - @score_b)` and branch:
   - **A wins**: difference `> @winner_threshold` → set `@winner_output = @response_a`, RETURN with `winner='A'`, both scores, and positive margin.
   - **B wins**: difference `< (0 - @winner_threshold)` → set `@winner_output = @response_b`, RETURN with `winner='B'`, both scores, and positive margin.
   - **Tie**: difference within ±threshold → CALL `format_tie_result(@response_a, @response_b, @score_a_json, @score_b_json)` into `@winner_output` (deterministic formatting), RETURN with `winner='tie'` and both scores.

---

## 4. Error Handling

- **`GenerationError`** — caught if any GENERATE step fails (e.g. model unavailable, malformed output). The workflow returns the string `'A/B test failed during generation.'` with metadata `status = 'error'`. No partial results are surfaced; execution halts immediately.

---

## 5. Output

The output variable `@winner_output` contains the full text of the winning response (Variant A or B), or a formatted side-by-side comparison string in the tie case.

Every RETURN path includes structured metadata:

| Scenario | `winner` | `score_a` | `score_b` | `margin` | `status` |
|---|---|---|---|---|---|
| Variant A wins | `'A'` | numeric | numeric | `score_a − score_b` | *(unset)* |
| Variant B wins | `'B'` | numeric | numeric | `score_b − score_a` | *(unset)* |
| Tie | `'tie'` | numeric | numeric | *(unset)* | *(unset)* |
| GenerationError | *(unset)* | *(unset)* | *(unset)* | *(unset)* | `'error'` |