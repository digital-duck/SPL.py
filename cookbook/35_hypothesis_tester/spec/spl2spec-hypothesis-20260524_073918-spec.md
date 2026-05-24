## Summary

The Hypothesis Tester workflow encodes the scientific method as an LLM orchestration pipeline: given a plain-English observation, it formulates null and alternative hypotheses, designs a test plan, weighs evidence, and delivers a structured conclusion with a calibrated confidence score. It exists to bring disciplined, falsifiability-first reasoning to situations where informal intuition would otherwise dominate. Data analysts, product managers, and researchers benefit by getting a rigorous framing of their observations without requiring a statistics background.

---

## Detailed Specification

### 1. Purpose

Given a natural-language observation, this workflow produces a structured scientific conclusion — hypothesis pair, evidence assessment, verdict, and confidence score — using a four-step LLM reasoning pipeline with confidence-gated branching.

---

### 2. High-level Description

The `hypothesis_tester` WORKFLOW accepts an `@observation` (what was noticed), an optional `@domain` (defaults to `'general'`), and an optional `@confidence_threshold` float (defaults to `0.7`). It uses two CREATE FUNCTIONs as structured prompt scaffolds: `hypothesis_framework()` injects a scientific template defining H0, H1, key variables, and falsifiability criteria into the first GENERATE call; `evidence_schema()` supplies a strict JSON schema (with required `confidence` and `verdict` fields, and arrays for supporting, refuting, and inconclusive evidence) into the third GENERATE call to enforce machine-readable output. The pipeline advances through four sequential GENERATE steps — hypothesis formulation, test-plan design, evidence evaluation, and confidence extraction — each binding its result into a named `@var` for downstream consumption. After confidence is extracted from the JSON evidence object, an EVALUATE block gates the final GENERATE call for `write_conclusion` across three branches: high confidence (`>= @confidence_threshold`) yields a `status='concluded'` / `verdict='h1_supported'` RETURN; medium confidence (`>= 0.4`) yields `status='inconclusive'` / `verdict='needs_more_data'`; low confidence falls through to `status='concluded'` / `verdict='h0_not_rejected'`. An EXCEPTION WHEN `GenerationError` handler provides graceful degradation, returning the partially-completed `@hypotheses` with `status='hypotheses_only'` if the evidence evaluation stage fails.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `hypothesis_tester` node class | `WORKFLOW hypothesis_tester` | Top-level named workflow with INPUT/OUTPUT declarations |
| `hypothesis_framework()` prompt template | `CREATE FUNCTION hypothesis_framework() RETURN TEXT` | Injected as a structural scaffold into the first GENERATE call |
| `evidence_schema()` JSON schema | `CREATE FUNCTION evidence_schema() RETURN JSON` | Enforces machine-readable output with required `confidence` and `verdict` fields |
| LLM call → formulate hypotheses | `GENERATE formulate_hypotheses(@observation, @domain, hypothesis_framework()) INTO @hypotheses` | Seed step; produces H0/H1 pair |
| LLM call → design test | `GENERATE design_test(@hypotheses, @domain) INTO @test_plan` | Operationalizes how to falsify H0 |
| LLM call → evaluate evidence | `GENERATE evaluate_evidence(@observation, @hypotheses, @test_plan, evidence_schema()) INTO @evidence_json` | JSON-constrained output with confidence float and verdict enum |
| LLM call → extract score | `GENERATE extract_confidence(@evidence_json) INTO @confidence` | Parses the float from structured JSON |
| Confidence-gated dispatch | `EVALUATE @confidence WHEN >= ... THEN ... WHEN >= ... THEN ... ELSE ... END` | Three-branch terminal decision; each branch calls `write_conclusion` with a different tone argument |
| Partial-failure recovery | `EXCEPTION WHEN GenerationError THEN RETURN @hypotheses WITH status='hypotheses_only'` | Returns hypothesis text if evidence evaluation stage fails |
| Shared pipeline state | `@observation`, `@hypotheses`, `@test_plan`, `@evidence_json`, `@confidence`, `@conclusion` | SPL `@var` bindings thread data through all five stages |
| `RETURN ... WITH status=, verdict=, confidence=` | `RETURN @conclusion WITH status=..., verdict=..., confidence=...` | All three EVALUATE branches emit non-default status tokens that carry verdict and score metadata |

---

### 4. Logical Functions / Prompts

**`hypothesis_framework()`**
- Role: Structural scaffold injected into `formulate_hypotheses`; constrains the LLM to produce a complete scientific hypothesis pair rather than free-form text.
- Key conventions: Enumerates four required elements — H0, H1, key variables (independent/dependent/confounding), and a falsifiability statement. No sentinel tokens; output is human-readable prose.

**`evidence_schema()`**
- Role: JSON Schema injected into `evaluate_evidence`; forces the LLM to produce structured, machine-parseable output.
- Key conventions: Requires `confidence` (float 0–1) and `verdict` (enum: `reject_h0` | `fail_to_reject_h0` | `inconclusive`). Also accepts optional arrays `supports_h1`, `supports_h0`, `inconclusive`, and `caveats`.

**`formulate_hypotheses`**
- Role: Translates the raw observation into a rigorous H0/H1 pair using the framework scaffold.
- Key conventions: Receives `@observation`, `@domain`, and the `hypothesis_framework()` template text. Output is free-form scientific prose.

**`design_test`**
- Role: Produces an empirical test plan that specifies how H0 could be falsified.
- Key conventions: Receives `@hypotheses` and `@domain`. Output scopes what data, comparisons, or experiments would constitute a valid test.

**`evaluate_evidence`**
- Role: The central reasoning step; assesses available evidence against the hypotheses and emits a structured verdict.
- Key conventions: Constrained by `evidence_schema()` to produce a JSON object. The `confidence` float and `verdict` enum are required and drive downstream branching.

**`extract_confidence`**
- Role: Parses the float confidence score out of the JSON blob for use in the EVALUATE condition.
- Key conventions: Receives `@evidence_json`; outputs a scalar float. Acts as a type-bridge between the JSON evidence and the numeric comparison in EVALUATE.

**`write_conclusion`**
- Role: Generates the final human-readable conclusion, tone-adjusted by the branch taken.
- Key conventions: Called three times with a tone argument — `'confident'`, `'uncertain'`, or `'refuted'` — to calibrate language strength to evidential weight. Receives `@hypotheses`, `@evidence_json`, and `@test_plan` for full context.

---

### 5. Control Flow

The workflow is a **linear pipeline terminating in a confidence-gated three-way branch**:

1. `formulate_hypotheses` → `@hypotheses`
2. `design_test` → `@test_plan`
3. `evaluate_evidence` → `@evidence_json`
4. `extract_confidence` → `@confidence`
5. **EVALUATE `@confidence`**:
   - `>= @confidence_threshold` → `write_conclusion(..., 'confident')` → `RETURN WITH status='concluded', verdict='h1_supported'`
   - `>= 0.4` (and below threshold) → `write_conclusion(..., 'uncertain')` → `RETURN WITH status='inconclusive', verdict='needs_more_data'`
   - `ELSE` → `write_conclusion(..., 'refuted')` → `RETURN WITH status='concluded', verdict='h0_not_rejected'`

There is no WHILE loop — the evidence weighting is a single-pass judgment, not an iterative refinement. The EXCEPTION WHEN `GenerationError` handler fires only if a GENERATE call raises; it short-circuits directly to a partial RETURN without entering the EVALUATE block.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Given a natural-language observation, this workflow produces a structured scientific conclusion — hypothesis pair, evidence assessment, verdict, and confidence score — using a four-step LLM reasoning pipeline with confidence-gated branching." --mode workflow

# Step 2 — compile to any target
spl3 splc compile hypothesis_tester.spl --lang python/pocketflow
spl3 splc compile hypothesis_tester.spl --lang python/langgraph
spl3 splc compile hypothesis_tester.spl --lang go
```