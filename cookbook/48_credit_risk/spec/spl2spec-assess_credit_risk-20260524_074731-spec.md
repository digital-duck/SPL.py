## Summary

This workflow automates consumer credit decisions by combining deterministic score thresholds with qualitative LLM analysis, eliminating unnecessary AI calls for clear-cut cases. A senior credit analyst prompt evaluates borderline applicants and produces a structured risk report with an explicit rating token that drives the final routing. Risk officers and loan-processing systems benefit from faster, auditable, cost-controlled decisions with full log artifacts.

---

## Detailed Specification

### 1. Purpose

Assess a loan applicant's credit risk and return one of three decisions — APPROVED, MANUAL_REVIEW, or REJECTED — by combining deterministic score gates with a single LLM qualitative review for borderline cases.

---

### 2. High-level Description

The workflow implements a **hybrid deterministic-plus-LLM credit decision pipeline**. It opens with a score-based EVALUATE gate on `@credit_score`: applicants below 600 are immediately rejected and applicants at 750 or above are immediately approved, both paths returning structured metadata with no LLM cost. Applicants in the 600–749 gray zone proceed to a GENERATE call against `analyze_risk_factors`, a CREATE FUNCTION prompt that instructs an LLM (acting as a Tier-1 bank senior analyst) to identify risk signals, mitigating factors, and emit a sentinel line `RISK_RATING: <low|medium|high>` at the end of its report. The raw report is persisted to disk via a CALL to `write_file`, and a second deterministic CALL to `extract_risk_rating` parses out the sentinel token — keeping LLM token cost at exactly one call per gray-zone applicant. A final EVALUATE on `@risk_rating` routes to REJECTED, MANUAL_REVIEW, or APPROVED with the full report as output. A top-level EXCEPTION handler for `ConnectionError` returns a PENDING status and logs the failure, ensuring the caller always receives a well-formed response.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW credit_risk_assessment` | `WORKFLOW` | Top-level orchestration unit; declares INPUT/OUTPUT contract |
| `CREATE FUNCTION analyze_risk_factors` | `CREATE FUNCTION` | Reusable prompt template with `{applicant_data}` slot; instructs LLM to act as senior analyst |
| `GENERATE analyze_risk_factors(...) INTO @risk_report` | `GENERATE` | Single LLM call, result bound to `@risk_report`; only reached for gray-zone scores |
| `CALL write_file(...) INTO NONE` | `CALL` (side-effect) | Persists risk report and extracted rating to disk; no return value consumed |
| `CALL extract_risk_rating(...) INTO @risk_rating` | `CALL` (deterministic tool) | Regex/string extraction of `RISK_RATING:` sentinel; zero LLM cost |
| `EVALUATE @credit_score WHEN < 600 / >= 750` | `EVALUATE` (numeric gate) | First branch; drives fast-path RETURN before any LLM call |
| `EVALUATE @risk_rating WHEN 'high'/'medium'/ELSE` | `EVALUATE` (string match) | Second branch; maps extracted rating to final decision token |
| `RETURN '...' WITH reason=, score=` | `RETURN … WITH` | Non-trivial status tokens (REJECTED, APPROVED, MANUAL_REVIEW, PENDING) carry decision metadata |
| `@applicant_data`, `@credit_score`, `@risk_report`, `@risk_rating` | `@vars` (shared state) | Pipeline state threaded through all steps without global mutation |
| `EXCEPTION WHEN ConnectionError THEN` | `EXCEPTION WHEN` | Typed handler; converts infra failure into a structured PENDING response |
| `LOGGING … LEVEL INFO/WARN/DEBUG/ERROR` | `LOGGING` | Audit trail at each decision point; level reflects decision severity |

---

### 4. Logical Functions / Prompts

**`analyze_risk_factors`**
- **Role:** The sole LLM call in the workflow; performs qualitative credit analysis for gray-zone applicants (600–749).
- **Prompt conventions:**
  - Persona framing: "senior credit risk analyst at a Tier-1 bank" — anchors tone and expected depth.
  - Structured output sections: (1) key risk signals, (2) mitigating factors, (3) overall rating.
  - **Sentinel token:** the final line must be `RISK_RATING: <low|medium|high>` exactly — this is the machine-readable anchor consumed downstream by `extract_risk_rating`.
  - Output format: free-form prose report terminated by the sentinel; the entire text becomes `@risk_report`.

---

### 5. Control Flow

```
START
  │
  ├─ EVALUATE @credit_score
  │     < 600  ──→ RETURN 'REJECTED'  (reason=score_below_threshold)   [terminal]
  │     >= 750 ──→ RETURN 'APPROVED'  (reason=score_excellent)          [terminal]
  │     ELSE   ──→ continue (gray zone)
  │
  ├─ GENERATE analyze_risk_factors(@applicant_data) INTO @risk_report
  ├─ CALL write_file(risk_report.md)
  ├─ CALL extract_risk_rating(@risk_report) INTO @risk_rating
  │
  ├─ EVALUATE @risk_rating
  │     'high'   ──→ RETURN @risk_report  (reason=REJECTED: qualitative_risk_high)
  │     'medium' ──→ RETURN @risk_report  (reason=MANUAL_REVIEW: qualitative_risk_medium)
  │     ELSE     ──→ RETURN @risk_report  (reason=APPROVED: qualitative_risk_low)
  │
EXCEPTION ConnectionError ──→ RETURN @error_message (reason=PENDING: system_error)
```

There is no WHILE loop — this is a single-pass pipeline. All branching is via EVALUATE; termination is always a RETURN with a non-trivial status that the caller uses to route the applicant.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (paste Section 1 above as text2spl input)
spl3 text2spl --description \
  "Assess a loan applicant's credit risk and return one of three decisions — \
APPROVED, MANUAL_REVIEW, or REJECTED — by combining deterministic score gates \
with a single LLM qualitative review for borderline cases." \
  --mode workflow

# Step 2 — compile to any target
spl3 splc compile credit_risk_assessment.spl --lang python/pocketflow
spl3 splc compile credit_risk_assessment.spl --lang python/langgraph
spl3 splc compile credit_risk_assessment.spl --lang go
```