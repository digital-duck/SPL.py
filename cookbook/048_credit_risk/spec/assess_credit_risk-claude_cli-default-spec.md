## Summary

This workflow automates credit risk assessment for loan applicants by combining deterministic score-based routing with LLM-driven qualitative analysis. It eliminates unnecessary LLM calls for clear-cut cases (very low or very high scores) while applying natural-language risk analysis only when the credit score falls in an ambiguous range. Loan underwriters and risk operations teams benefit from faster, consistent, and cost-efficient credit decisions.

---

## Detailed Specification

### 1. Purpose

Evaluate an applicant's credit risk and return one of three routing decisions — APPROVED, REJECTED, or MANUAL_REVIEW — by combining deterministic score thresholds with LLM-generated qualitative analysis.

---

### 2. High-level Description

The `credit_risk_assessment` WORKFLOW accepts an applicant data payload and a numeric credit score, then routes the decision through two sequential EVALUATE branches to minimize LLM cost. The first EVALUATE inspects `@credit_score` directly: scores below 600 immediately RETURN with `reason = 'REJECTED: score_below_threshold'` and scores at or above 750 immediately RETURN with `reason = 'APPROVED: score_excellent'`, both without any LLM invocation. Scores in the gray zone (600–749) proceed to a GENERATE call that invokes the `analyze_risk_factors` CREATE FUNCTION — a senior credit analyst persona prompt — which produces a structured risk report ending with a sentinel line `RISK_RATING: <low|medium|high>`. The full report is persisted as a side effect via a CALL to `write_file`. A second deterministic CALL to `extract_risk_rating` parses the sentinel from the report into `@risk_rating`, and a second EVALUATE on that value routes the final decision: `high` → RETURN REJECTED, `medium` → RETURN MANUAL_REVIEW, otherwise → RETURN APPROVED, each carrying the full report in `@decision`. The WORKFLOW handles infrastructure failures through an EXCEPTION WHEN `ConnectionError` block that logs the error and returns a `PENDING: system_error` holding status.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW credit_risk_assessment` | `WORKFLOW <name>` | Named workflow; inputs are `@applicant_data`, `@credit_score`, `@log_dir` (with DEFAULT); output is `@decision` |
| `CREATE FUNCTION analyze_risk_factors` | `CREATE FUNCTION <name>({param})` | Single `{applicant_data}` slot; analyst persona prompt with sentinel output requirement |
| `GENERATE analyze_risk_factors(...) INTO @risk_report` | `GENERATE <fn>(...) INTO @<var>` | Only LLM call in the workflow; invoked only for gray-zone scores |
| `CALL write_file(...) INTO NONE` | `CALL <tool>(...) INTO NONE` | Side-effect file writes for `risk_report.md` and `risk_rating.md`; no return value consumed |
| `CALL extract_risk_rating(@risk_report) INTO @risk_rating` | `CALL <tool>(...) INTO @<var>` | Deterministic string extraction from the sentinel line; zero LLM cost |
| `EVALUATE @credit_score WHEN < 600 ...` | `EVALUATE @<var> WHEN <cond> THEN ... ELSE ... END` | Numeric threshold branching; two early-exit paths before any LLM call |
| `EVALUATE @risk_rating WHEN 'high' ...` | `EVALUATE @<var> WHEN '<literal>' THEN ... END` | String-literal branching on extracted sentinel value |
| `RETURN ... WITH reason = '...'` | `RETURN @<var> WITH <k>=<v>, ...` | Every RETURN carries a non-trivial `reason` token (REJECTED, APPROVED, MANUAL_REVIEW, PENDING) that encodes the final routing decision |
| `EXCEPTION WHEN ConnectionError` | `EXCEPTION WHEN <Type> THEN ...` | Catches external connectivity failures; emits PENDING holding status |
| `@risk_report`, `@risk_rating`, `@decision` | shared state `@<var>` | Pipeline variables passing data between GENERATE, CALL, and EVALUATE steps |
| `LOGGING ... LEVEL INFO/WARN/DEBUG/ERROR` | `LOGGING <msg> LEVEL <level>` | Observability side effects at each major decision point |

---

### 4. Logical Functions / Prompts

**`analyze_risk_factors`**
- **Role:** The sole LLM function in the workflow; performs qualitative credit risk analysis when the numeric score is inconclusive (600–749).
- **Persona:** Senior credit risk analyst at a Tier-1 bank.
- **Input:** Full `{applicant_data}` text (JSON or structured record).
- **Output format:** A structured prose report covering (1) key risk signals, (2) mitigating factors, and (3) an overall rating. The report must terminate with the sentinel line `RISK_RATING: <low|medium|high>` — this exact format enables downstream deterministic parsing by `extract_risk_rating` without a second LLM call.
- **Sentinel convention:** `RISK_RATING:` is the extraction anchor; the token after it is constrained to exactly one of `low`, `medium`, or `high`.

---

### 5. Control Flow

```
START
  │
  ▼
LOGGING (INFO) — log score and start
  │
  ▼
EVALUATE @credit_score
  ├─ < 600  → LOGGING WARN → RETURN 'REJECTED'  WITH reason='score_below_threshold'  [TERMINATE]
  ├─ >= 750 → LOGGING INFO → RETURN 'APPROVED'  WITH reason='score_excellent'         [TERMINATE]
  └─ ELSE   → LOGGING INFO — enter qualitative path
                │
                ▼
            GENERATE analyze_risk_factors(@applicant_data) INTO @risk_report
                │
                ▼
            CALL write_file(risk_report.md) INTO NONE
                │
                ▼
            CALL extract_risk_rating(@risk_report) INTO @risk_rating
                │
                ▼
            LOGGING DEBUG — log extracted rating
                │
                ▼
            CALL write_file(risk_rating.md) INTO NONE
                │
                ▼
            EVALUATE @risk_rating
              ├─ 'high'   → RETURN @risk_report WITH reason='REJECTED: qualitative_risk_high'   [TERMINATE]
              ├─ 'medium' → RETURN @risk_report WITH reason='MANUAL_REVIEW: qualitative_risk_medium' [TERMINATE]
              └─ ELSE     → RETURN @risk_report WITH reason='APPROVED: qualitative_risk_low'    [TERMINATE]

EXCEPTION WHEN ConnectionError
  → LOGGING ERROR → RETURN @error_message WITH reason='PENDING: system_error'         [TERMINATE]
```

There is no WHILE loop; every path terminates at a RETURN. The two EVALUATE branches are the sole control-flow decisions; all other steps are linear.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Evaluate an applicant's credit risk and return one of three routing decisions — APPROVED, REJECTED, or MANUAL_REVIEW — by combining deterministic score thresholds with LLM-generated qualitative analysis." --mode workflow

# Step 2 — compile to any target
spl3 splc compile credit_risk_assessment.spl --lang python/pocketflow
spl3 splc compile credit_risk_assessment.spl --lang python/langgraph
spl3 splc compile credit_risk_assessment.spl --lang go
```