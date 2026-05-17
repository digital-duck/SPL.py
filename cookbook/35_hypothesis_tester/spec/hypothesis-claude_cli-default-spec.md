## Summary

The Hypothesis Tester is a scientific reasoning workflow that takes a plain-language observation and guides a language model through the full arc of structured inquiry: formulating null and alternative hypotheses, designing a test plan, weighing evidence, and reaching a calibrated conclusion. It produces a written conclusion tagged with a machine-readable verdict and confidence score, making it useful for analysts, researchers, or product teams who want LLM-assisted hypothesis evaluation with traceable reasoning rather than a single ungrounded answer.

---

## Detailed Specification

### 1. Purpose

Given a natural-language observation and an optional domain label, this workflow produces a structured scientific conclusion—supported, inconclusive, or refuted—backed by hypothesis framing, a test plan, and evidence evaluation with a numeric confidence score.

---

### 2. High-level Description

The `hypothesis_tester` WORKFLOW implements a four-stage scientific reasoning pipeline over a single observation. Two CREATE FUNCTIONs—`hypothesis_framework` and `evidence_schema`—serve as format scaffolds injected into LLM calls to enforce structured output: the first provides a text template for H0/H1 framing; the second provides a JSON Schema that constrains evidence evaluation to typed arrays, a numeric confidence in [0,1], and an enumerated verdict token.

The pipeline opens by calling `formulate_hypotheses` to produce explicit null and alternative hypotheses, then calls `design_test` to produce a falsification-oriented test plan, then calls `evaluate_evidence` to produce structured JSON evidence graded against the schema, and finally calls `extract_confidence` to surface a scalar score from that JSON. A terminal EVALUATE block branches on that score against `@confidence_threshold` (default 0.7) and a hard floor of 0.4: scores at or above the threshold route to a `'confident'` conclusion and RETURN with `status='concluded', verdict='h1_supported'`; scores between 0.4 and the threshold route to an `'uncertain'` conclusion and RETURN with `status='inconclusive', verdict='needs_more_data'`; scores below 0.4 route to a `'refuted'` conclusion and RETURN with `status='concluded', verdict='h0_not_rejected'`. There is no WHILE loop; control is strictly linear until the terminal EVALUATE. An EXCEPTION handler for `GenerationError` provides a graceful fallback: if any GENERATE call fails, the workflow returns whatever hypotheses were produced with `status='hypotheses_only'` and a diagnostic reason string.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `hypothesis_tester` workflow class | `WORKFLOW hypothesis_tester` | Declares the named orchestration entry point |
| `hypothesis_framework()` prompt scaffold | `CREATE FUNCTION hypothesis_framework()` | Returns TEXT; injected as a formatting guide into `formulate_hypotheses` |
| `evidence_schema()` JSON Schema scaffold | `CREATE FUNCTION evidence_schema()` | Returns JSON Schema; injected into `evaluate_evidence` to enforce structured output |
| `formulate_hypotheses(...)` LLM call | `GENERATE formulate_hypotheses(...) INTO @hypotheses` | Stores H0/H1 formulation in shared state variable |
| `design_test(...)` LLM call | `GENERATE design_test(...) INTO @test_plan` | Stores falsification test plan |
| `evaluate_evidence(...)` LLM call | `GENERATE evaluate_evidence(...) INTO @evidence_json` | Stores structured JSON evidence graded by schema |
| `extract_confidence(...)` LLM call | `GENERATE extract_confidence(...) INTO @confidence` | Extracts scalar float from JSON evidence blob |
| `write_conclusion(...)` LLM call | `GENERATE write_conclusion(...) INTO @conclusion` | Called once inside each EVALUATE branch with a tone argument |
| Confidence-score branching | `EVALUATE @confidence WHEN >= ... THEN ... ELSE ... END` | Three-way branch: supported / inconclusive / refuted |
| Non-trivial status tokens | `RETURN @conclusion WITH status=..., verdict=..., confidence=...` | `'concluded'`, `'inconclusive'`, `'h1_supported'`, `'h0_not_rejected'`, `'needs_more_data'` all carry semantic meaning for callers |
| Partial-result fallback | `EXCEPTION WHEN GenerationError THEN RETURN @hypotheses WITH status='hypotheses_only'` | Returns early with whatever was computed before the failure |
| Shared pipeline state | `@hypotheses`, `@test_plan`, `@evidence_json`, `@confidence`, `@conclusion` | SPL `@var` slots carrying intermediate results through the pipeline |

---

### 4. Logical Functions / Prompts

**`hypothesis_framework`**
- Role: Format scaffold, not an LLM call. Returns a fixed TEXT block defining H0, H1, key variables, and testability criteria.
- Key conventions: Injected verbatim into the `formulate_hypotheses` prompt to constrain the LLM's output structure. Acts as a system-level instruction rather than a generative prompt.

**`formulate_hypotheses`**
- Role: Converts a raw observation into a structured scientific hypothesis pair (H0 and H1) within the specified domain.
- Key conventions: Receives `@observation`, `@domain`, and the `hypothesis_framework()` scaffold. Expected to produce labeled H0/H1 text with variable identification and falsifiability notes.

**`design_test`**
- Role: Produces a concrete test plan that could falsify H0, given the formulated hypotheses and domain context.
- Key conventions: Receives `@hypotheses` and `@domain`. Should articulate measurable criteria and methodology appropriate to the domain.

**`evaluate_evidence`**
- Role: Grades available evidence against the hypotheses and test plan, producing structured JSON output validated by `evidence_schema()`.
- Key conventions: Output must conform to the JSON Schema: `supports_h1` and `supports_h0` arrays, `confidence` float in [0,1], `verdict` enum (`reject_h0` / `fail_to_reject_h0` / `inconclusive`), optional `caveats`. The schema is injected to enforce this shape.

**`extract_confidence`**
- Role: Extracts the scalar `confidence` field from the JSON evidence blob into a standalone `@confidence` variable.
- Key conventions: Single numeric output; enables the downstream EVALUATE branch to operate on a plain float rather than parsing JSON inline.

**`write_conclusion`**
- Role: Writes a human-readable conclusion paragraph calibrated to the evidence strength.
- Key conventions: Receives `@hypotheses`, `@evidence_json`, `@test_plan`, and a tone argument (`'confident'`, `'uncertain'`, or `'refuted'`). The tone argument steers register and hedging language in the output.

---

### 5. Control Flow

Execution begins with a linear sequence of four GENERATE calls: `formulate_hypotheses` → `design_test` → `evaluate_evidence` → `extract_confidence`. Each result is stored in a named `@var` and passed forward; there is no looping.

After `@confidence` is populated, control reaches the terminal EVALUATE block, which branches on two numeric thresholds:

1. `@confidence >= @confidence_threshold` (default 0.7): calls `write_conclusion` with tone `'confident'`, then RETURN WITH `status='concluded'`, `verdict='h1_supported'`.
2. `@confidence >= 0.4` (the implicit middle band): calls `write_conclusion` with tone `'uncertain'`, then RETURN WITH `status='inconclusive'`, `verdict='needs_more_data'`.
3. ELSE (below 0.4): calls `write_conclusion` with tone `'refuted'`, then RETURN WITH `status='concluded'`, `verdict='h0_not_rejected'`.

If a `GenerationError` is raised at any point before the EVALUATE, the EXCEPTION handler fires and returns `@hypotheses` (whatever was computed) with `status='hypotheses_only'` and `reason='evidence_evaluation_failed'`.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Given a natural-language observation and an optional domain label, this workflow produces a structured scientific conclusion—supported, inconclusive, or refuted—backed by hypothesis framing, a test plan, and evidence evaluation with a numeric confidence score." --mode workflow

# Step 2 — compile to any target
spl3 splc compile hypothesis_tester.spl --lang python/pocketflow
spl3 splc compile hypothesis_tester.spl --lang python/langgraph
spl3 splc compile hypothesis_tester.spl --lang go
```