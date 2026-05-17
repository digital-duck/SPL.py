## Summary

This workflow runs a controlled A/B experiment on two prompt variants by having an LLM answer the same task under each variant, then scoring both answers against a structured rubric. It automatically declares a winner (or a tie) based on a configurable score margin. Prompt engineers and product teams use it to make data-driven decisions about which phrasing, style, or instruction set produces better LLM output.

---

## Detailed Specification

### 1. Purpose

Automatically compare two prompt variants against a shared task, score each LLM response on a four-criterion rubric, and return the winning response with metadata—or a formatted tie report—so prompt engineers can pick the better variant without manual review.

---

### 2. High-level Description

The `ab_test` WORKFLOW implements a single-pass prompt comparison pattern with no iterative loop. It begins by invoking a deterministic CALL to `load_experiment`, which resolves a named experiment from a catalog file (`experiments.json`) or falls through to ad-hoc inputs when no `experiment_id` is supplied. Two independent GENERATE calls—`run_variant_a` and `run_variant_b`—send the same task to the LLM under their respective prompt framings, producing `@response_a` and `@response_b`. A reusable CREATE FUNCTION named `scoring_rubric` supplies a four-criterion JSON rubric (clarity, completeness, relevance, engagement, total) that is embedded verbatim into two GENERATE calls to `evaluate_response`, one per variant; both calls return structured JSON scores. Two deterministic CALL steps (`extract_score_total`) parse the numeric totals from each JSON blob without involving the LLM. The workflow concludes with a three-branch EVALUATE on the score delta: if the margin exceeds `@winner_threshold` in either direction, the winning response is returned via RETURN WITH metadata (`winner`, `score_a`, `score_b`, `margin`); if the margin falls within the threshold, a deterministic CALL to `format_tie_result` assembles a combined report that is returned with `winner = 'tie'`. A top-level EXCEPTION handler catches any GenerationError and returns a fixed error string with `status = 'error'`.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW ab_test` | `WORKFLOW ab_test` | Single-pass, no loop; five typed inputs with defaults |
| `CREATE FUNCTION scoring_rubric` | `CREATE FUNCTION scoring_rubric()` | Parameterless; returns the full rubric text block for inline embedding |
| `CALL load_experiment(...)` | `CALL load_experiment(@experiment_id) INTO @experiment_context` | Deterministic; reads `experiments.json` or returns empty context |
| `GENERATE run_variant_a/b(...)` | `GENERATE run_variant_a(@task, @prompt_a, @experiment_context) INTO @response_a` | Two independent LLM calls under different prompt framings |
| `GENERATE evaluate_response(...)` | `GENERATE evaluate_response(@response_X, @task, scoring_rubric()) INTO @score_X_json` | Scoring call; rubric injected via function reference |
| `CALL extract_score_total(...)` | `CALL extract_score_total(@score_X_json) INTO @score_X` | Deterministic JSON parsing; no LLM |
| `EVALUATE (expr) WHEN > / < / ELSE` | `EVALUATE (@score_a - @score_b) WHEN > @winner_threshold THEN ... WHEN < (0 - @winner_threshold) THEN ... ELSE ...` | Three-way branch on numeric delta |
| `RETURN @var WITH k=v, ...` | `RETURN @winner_output WITH winner='A'/'B'/'tie', score_a=, score_b=, margin=` | Non-trivial status tokens drive the winner/tie distinction |
| `EXCEPTION WHEN GenerationError` | `EXCEPTION WHEN GenerationError THEN RETURN '...' WITH status='error'` | Catches LLM call failures; returns fixed message |
| Shared state (`@vars`) | `@response_a/b`, `@score_a/b_json`, `@score_a/b`, `@winner_output` | Passed between steps via named workflow variables |

---

### 4. Logical Functions / Prompts

**`scoring_rubric()`**
- **Role:** Reusable prompt fragment; not called as an LLM step itself but embedded as an argument into `evaluate_response`.
- **Key conventions:** Defines four integer criteria (0–10 each) plus a `total` field and a one-sentence `rationale`. Requires the LLM to return valid JSON only—no prose outside the object. The sentinel instruction "Return valid JSON only — no prose outside the JSON" guards downstream deterministic parsing.

**`run_variant_a` / `run_variant_b`**
- **Role:** Execute the same task under prompt variant A or B, respectively, using the experiment context (or ad-hoc inputs) to frame the system/user prompt.
- **Key conventions:** Accept `@task`, the variant's prompt text, and `@experiment_context`; output is free-form text (the LLM's answer).

**`evaluate_response`**
- **Role:** Score a single response against the task using the rubric.
- **Key conventions:** Takes the response text, the original task, and the rubric block; must return a JSON object matching `{"clarity": N, "completeness": N, "relevance": N, "engagement": N, "total": N, "rationale": "..."}`. Output feeds directly into the deterministic `extract_score_total` CALL.

---

### 5. Control Flow

1. **Load experiment** — CALL `load_experiment` resolves the named experiment or passes through ad-hoc inputs; no LLM involved.
2. **Generate responses** — Two parallel GENERATE calls produce `@response_a` and `@response_b` independently.
3. **Score responses** — Two GENERATE calls to `evaluate_response` (with the rubric injected) produce JSON score blobs.
4. **Extract totals** — Two deterministic CALL steps parse the numeric `total` from each JSON blob.
5. **Branch on margin** — EVALUATE computes `@score_a - @score_b`:
   - `> @winner_threshold` → RETURN `@response_a` WITH `winner='A'`
   - `< (0 - @winner_threshold)` → RETURN `@response_b` WITH `winner='B'`
   - ELSE → CALL `format_tie_result` to combine both outputs, RETURN WITH `winner='tie'`
6. **Error path** — Any GenerationError in steps 2–4 is caught by EXCEPTION and returns a fixed error string with `status='error'`.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Automatically compare two prompt variants against a shared task, score each LLM response on a four-criterion rubric (clarity, completeness, relevance, engagement), and return the winning response with metadata—or a formatted tie report—so prompt engineers can pick the better variant without manual review." --mode workflow

# Step 2 — compile to any target
spl3 splc compile ab_test.spl --lang python/pocketflow
spl3 splc compile ab_test.spl --lang python/langgraph
spl3 splc compile ab_test.spl --lang go
```