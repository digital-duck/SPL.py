## 0. High-level Description

This workflow implements a **structured scientific reasoning** pattern — sometimes called "hypothesis-test-evaluate" — in which an observed phenomenon is systematically converted into a falsifiable hypothesis, a test plan, and a weighted evidence verdict before a final conclusion is drawn. Two CREATE FUNCTIONs provide reusable prompt scaffolding: `hypothesis_framework()` injects a plain-text template that forces the model to articulate null and alternative hypotheses, identify independent/dependent/confounding variables, and specify a falsification strategy; `evidence_schema()` supplies a JSON Schema that constrains the evidence-evaluation response to structured arrays of supporting, refuting, and inconclusive points alongside a 0–1 confidence score and an enumerated verdict (`reject_h0`, `fail_to_reject_h0`, `inconclusive`). Control flow is linear through four GENERATE calls — formulate hypotheses, design a test plan, evaluate evidence, extract confidence — followed by a three-branch EVALUATE that compares `@confidence` against `@confidence_threshold` (≥ threshold → "concluded/h1_supported"), an intermediate band (≥ 0.4 → "inconclusive/needs_more_data"), and a low-confidence floor (else → "concluded/h0_not_rejected"); each branch calls `write_conclusion()` with a distinct tone argument (`'confident'`, `'uncertain'`, or `'refuted'`). LOGGING statements at INFO level bookend the workflow with domain and threshold metadata, while DEBUG-level entries trace each intermediate generation step. The single EXCEPTION handler catches `GenerationError` and gracefully degrades by returning whatever hypotheses were produced before failure, preserving partial work rather than aborting silently.

---

## 1. Purpose

Given a plain-language empirical observation, the workflow formulates null and alternative hypotheses, designs a test plan, evaluates available evidence, and returns a confidence-weighted scientific conclusion that either supports, refutes, or defers judgment on the hypothesis.

---

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@observation` | *(required)* | Plain-text description of the phenomenon or empirical claim to investigate |
| `@domain` | `'general'` | Subject domain (e.g. `'product'`, `'biology'`) used to contextualise hypothesis framing and test design |
| `@confidence_threshold` | `0.7` | Minimum confidence score (0–1) required to declare H1 supported; scores below this but ≥ 0.4 are inconclusive |

---

## 3. Process

1. **Log start** — emit an INFO-level log recording `@domain` and `@confidence_threshold`.
2. **Formulate hypotheses** — GENERATE `formulate_hypotheses(@observation, @domain, hypothesis_framework())` INTO `@hypotheses`; the `hypothesis_framework()` prompt template guides the model to produce H0, H1, key variables, and a falsification approach.
3. **Log debug** — emit DEBUG "Hypotheses formulated".
4. **Design test plan** — GENERATE `design_test(@hypotheses, @domain)` INTO `@test_plan`; produces a domain-aware methodology for testing the hypotheses.
5. **Log debug** — emit DEBUG "Test plan designed".
6. **Evaluate evidence** — GENERATE `evaluate_evidence(@observation, @hypotheses, @test_plan, evidence_schema())` INTO `@evidence_json`; the `evidence_schema()` JSON Schema constrains the output to structured supporting/refuting/inconclusive evidence arrays, a confidence float, a verdict enum, and caveats.
7. **Log debug** — emit DEBUG "Evidence evaluated".
8. **Extract confidence** — GENERATE `extract_confidence(@evidence_json)` INTO `@confidence`; parses or derives the numeric confidence value from the evidence JSON.
9. **Log confidence** — emit INFO-level log with the extracted score and threshold.
10. **Branch on confidence** via EVALUATE `@confidence`:
    - **≥ `@confidence_threshold`** → GENERATE `write_conclusion(..., 'confident')` INTO `@conclusion`; RETURN with `status='concluded'`, `verdict='h1_supported'`.
    - **≥ 0.4** (but below threshold) → GENERATE `write_conclusion(..., 'uncertain')` INTO `@conclusion`; RETURN with `status='inconclusive'`, `verdict='needs_more_data'`.
    - **Else** (< 0.4) → GENERATE `write_conclusion(..., 'refuted')` INTO `@conclusion`; RETURN with `status='concluded'`, `verdict='h0_not_rejected'`.

---

## 4. Error Handling

- **`GenerationError`** — caught at workflow level; returns `@hypotheses` (whatever was produced before the failure) with `status='hypotheses_only'` and `reason='evidence_evaluation_failed'`, allowing partial results to surface rather than a hard abort.

---

## 5. Output

The primary output is `@conclusion` (TEXT) — a prose scientific conclusion whose tone (`'confident'`, `'uncertain'`, or `'refuted'`) matches the evidence strength.

Each RETURN path carries the following metadata:

| Field | Possible Values | Meaning |
|---|---|---|
| `status` | `'concluded'`, `'inconclusive'`, `'hypotheses_only'` | Workflow completion state |
| `verdict` | `'h1_supported'`, `'needs_more_data'`, `'h0_not_rejected'` | Scientific outcome |
| `confidence` | Float 0–1 | Raw confidence score extracted from evidence evaluation |
| `reason` | `'evidence_evaluation_failed'` | Present only on error-path returns |