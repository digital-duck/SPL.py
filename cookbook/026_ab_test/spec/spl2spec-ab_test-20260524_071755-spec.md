## Summary

This workflow automates prompt A/B testing by generating two LLM responses to the same task using different prompt strategies, scoring both against a multi-criterion rubric, and declaring a winner based on a configurable margin. It eliminates subjective human judgement from prompt comparison, making prompt engineering decisions data-driven and reproducible. Product teams, prompt engineers, and researchers benefit from fast, objective selection between competing prompt variants.

---

## Detailed Specification

### 1. Purpose

Run a fully automated, LLM-judged head-to-head comparison between two prompt variants applied to the same task, returning the winning response along with numeric scores and margin metadata.

---

### 2. High-level Description

The `ab_test` WORKFLOW accepts either a pre-registered experiment ID (resolved against a catalog via a deterministic tool CALL) or raw ad-hoc inputs (task, prompt\_a, prompt\_b) and a configurable `winner_threshold` float. It uses two GENERATE calls — `run_variant_a` and `run_variant_b` — to produce independent LLM responses under each prompt strategy, then scores both with a third and fourth GENERATE call to `evaluate_response`, which applies the `scoring_rubric` CREATE FUNCTION (a reusable prompt template encoding a 0–10 JSON rubric across clarity, completeness, relevance, and engagement). Numeric totals are extracted from the JSON scores via deterministic tool CALLs (`extract_score_total`), keeping score parsing outside the LLM. A final EVALUATE branch compares the score delta against `winner_threshold`: if Variant A leads by more than the threshold it RETURNs with `winner='A'`; if Variant B leads it RETURNs with `winner='B'`; if scores are too close, a deterministic `format_tie_result` CALL formats both responses and the workflow RETURNs with `winner='tie'`. A top-level EXCEPTION handler catches `GenerationError` from any GENERATE step and returns a clean error status without crashing the caller.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW ab_test` | `WORKFLOW` | Top-level named workflow with typed INPUT/OUTPUT declarations |
| `CREATE FUNCTION scoring_rubric()` | `CREATE FUNCTION` | Reusable prompt template; injected as an argument to `evaluate_response` — no LLM call at definition time |
| `CALL load_experiment(...)` | `CALL` (deterministic tool) | Reads experiments.json catalog; no LLM involved |
| `GENERATE run_variant_a/b(...)` | `GENERATE ... INTO @var` | LLM calls with different prompt strategies; results captured in `@response_a` / `@response_b` |
| `GENERATE evaluate_response(...)` | `GENERATE ... INTO @var` | LLM-as-judge call; receives the rubric template inline via `scoring_rubric()` |
| `CALL extract_score_total(...)` | `CALL` (deterministic tool) | JSON parsing — deliberately kept out of the LLM path |
| `CALL format_tie_result(...)` | `CALL` (deterministic tool) | Deterministic formatting of tie output |
| `EVALUATE (@score_a - @score_b) WHEN > ... WHEN < ... ELSE` | `EVALUATE` | Three-way branch on numeric delta; drives the RETURN status token |
| `RETURN @winner_output WITH winner='A'/'B'/'tie'` | `RETURN ... WITH` | Non-trivial status tokens — each drives a distinct downstream interpretation |
| `@experiment_context`, `@response_a/b`, `@score_a/b_json`, `@score_a/b` | `@vars` (shared workflow state) | Intermediate results threaded through the pipeline |
| `EXCEPTION WHEN GenerationError` | `EXCEPTION WHEN` | Catches LLM generation failures and surfaces a structured error status |

---

### 4. Logical Functions / Prompts

**`scoring_rubric()`**
- **Role:** Reusable rubric template injected into the judge prompt. Defines the scoring contract.
- **Key conventions:** Returns strict JSON with fields `clarity`, `completeness`, `relevance`, `engagement`, `total` (each 0–10) plus a `rationale` string. The instruction "Return valid JSON only — no prose outside the JSON" is a sentinel to prevent free-text contamination and make deterministic `extract_score_total` parsing reliable.

**`run_variant_a(task, prompt_a, experiment_context)`**
- **Role:** Generates the Variant A LLM response using `prompt_a` as the system/framing instruction applied to `task`, optionally enriched by catalog context.
- **Key conventions:** Output is free-form text; it becomes the judge's input in `evaluate_response`.

**`run_variant_b(task, prompt_b, experiment_context)`**
- **Role:** Symmetric counterpart to `run_variant_a`, using the competing `prompt_b` strategy. Kept as a separate GENERATE call to ensure independent LLM invocations with no cross-contamination.

**`evaluate_response(response, task, rubric)`**
- **Role:** LLM-as-judge; scores one response against the task using the rubric template. Called twice — once per variant — producing `@score_a_json` and `@score_b_json`.
- **Key conventions:** Receives the full rubric text inline; expected output is the same JSON schema defined by `scoring_rubric()`.

---

### 5. Control Flow

```
load_experiment  →  run_variant_a  →  run_variant_b
    →  evaluate_response(A)  →  evaluate_response(B)
    →  extract_score_total(A)  →  extract_score_total(B)
    →  EVALUATE (score_a - score_b):
          WHEN delta > threshold  → RETURN winner='A'
          WHEN delta < -threshold → RETURN winner='B'
          ELSE                    → format_tie_result → RETURN winner='tie'

EXCEPTION WHEN GenerationError → RETURN status='error'
```

The workflow is linear until the terminal EVALUATE, which is the only branching point. There is no WHILE loop — this is a single-pass, single-comparison run by design. All three RETURN paths carry non-trivial status tokens (`winner='A'`, `winner='B'`, `winner='tie'`) that callers can use to route, log, or display results differently. The `winner_threshold` parameter (default `1.5`) makes the tie band configurable without modifying the workflow.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl \
  --description "Run a fully automated, LLM-judged head-to-head comparison between two
prompt variants applied to the same task. Accept either a pre-registered experiment ID
resolved from a catalog tool call or raw ad-hoc inputs (task, prompt_a, prompt_b, winner_threshold).
Use two GENERATE calls to produce independent LLM responses under each prompt strategy, then
score both with a GENERATE call to an evaluate_response function that applies a scoring_rubric
CREATE FUNCTION encoding a 0-10 JSON rubric across clarity, completeness, relevance, and
engagement. Extract numeric totals via deterministic CALL tools. Use a three-way EVALUATE branch
on the score delta versus winner_threshold to RETURN winner='A', winner='B', or winner='tie'.
Handle GenerationError with an EXCEPTION block returning status='error'." \
  --mode workflow

# Step 2 — compile to any target
spl3 splc compile ab_test.spl --lang python/pocketflow
spl3 splc compile ab_test.spl --lang python/langgraph
spl3 splc compile ab_test.spl --lang go
```