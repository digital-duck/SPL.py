## 0. High-level Description

This workflow implements a **deterministic routing with selective LLM escalation** pattern for credit risk assessment, deliberately minimizing LLM cost by front-loading two zero-cost decision gates. The WORKFLOW `credit_risk_assessment` accepts raw applicant data and a numeric credit score, then applies a two-stage EVALUATE branching strategy: the first EVALUATE checks `@credit_score` against hard thresholds to either auto-reject (< 600) or auto-approve (>= 750) before any LLM call is made, while the "gray zone" cases (600–749) are escalated to the single CREATE FUNCTION `analyze_risk_factors`, which instructs an LLM persona — a senior Tier-1 bank credit analyst — to produce a structured risk report ending with the sentinel token `RISK_RATING: <low|medium|high>`. After the GENERATE call stores the narrative report in `@risk_report`, two CALL side-effects serialize results to disk (`write_file`), and a second deterministic CALL (`extract_risk_rating`) parses the sentinel token into `@risk_rating` without an additional LLM round-trip. A second EVALUATE on `@risk_rating` then routes to one of three RETURN outcomes — `APPROVED`, `MANUAL_REVIEW`, or `REJECTED` — each carrying a `reason` metadata field. LOGGING statements at INFO, WARN, DEBUG, and ERROR levels trace every branching point, and a `ConnectionError` EXCEPTION handler catches upstream data-source failures, returning a `PENDING` status rather than crashing.

## 1. Purpose

Automatically approve, reject, or flag for manual review a credit applicant by first applying deterministic credit-score thresholds and, only for borderline cases, invoking an LLM-based qualitative risk analysis to extract a structured rating.

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@applicant_data` | *(required)* | Full applicant profile as raw text (e.g., JSON blob) passed to the LLM risk analysis function |
| `@credit_score` | *(required)* | Numeric credit score used for deterministic threshold routing before any LLM call |
| `@log_dir` | `cookbook/48_credit_risk/logs-spl` | Directory path where intermediate artefacts (`risk_report.md`, `risk_rating.md`) are written |

## 3. Process

1. **Log intake.** Emit an INFO log recording the applicant's credit score.
2. **Score fast-path (EVALUATE #1).** Branch on `@credit_score`:
   - If **< 600**: log a WARN, immediately RETURN `'REJECTED'` with `reason = 'score_below_threshold'` — no LLM invoked.
   - If **>= 750**: log INFO, immediately RETURN `'APPROVED'` with `reason = 'score_excellent'` — no LLM invoked.
   - Otherwise (600–749): log INFO that the score is in the gray zone and continue.
3. **Qualitative analysis (GENERATE).** Call `analyze_risk_factors(@applicant_data)` — the LLM adopts a senior analyst persona, identifies risk signals, mitigating factors, and appends a `RISK_RATING: <low|medium|high>` sentinel line. Result stored in `@risk_report`.
4. **Persist report.** CALL `write_file` to write `@risk_report` to `<log_dir>/risk_report.md` (result discarded with `INTO NONE`).
5. **Extract rating (CALL).** CALL `extract_risk_rating(@risk_report)` — a deterministic parser that reads the sentinel token — storing the single word into `@risk_rating`. Log the extracted value at DEBUG level.
6. **Persist rating.** CALL `write_file` to write `@risk_rating` to `<log_dir>/risk_rating.md`.
7. **Final routing (EVALUATE #2).** Branch on `@risk_rating`:
   - `'high'` → RETURN `@risk_report` with `reason = 'REJECTED: qualitative_risk_high'`
   - `'medium'` → RETURN `@risk_report` with `reason = 'MANUAL_REVIEW: qualitative_risk_medium'`
   - Anything else (`'low'`) → RETURN `@risk_report` with `reason = 'APPROVED: qualitative_risk_low'`

## 4. Error Handling

- **`ConnectionError`** — Triggered when the workflow cannot reach an external data source. Sets `@error_message` to a descriptive string, logs it at ERROR level, and RETURNs that message with `reason = 'PENDING: system_error'`, allowing the calling system to retry rather than treating the case as a hard decision.

## 5. Output

The OUTPUT variable `@decision TEXT` is returned under all paths. Every RETURN carries a `reason` metadata field; score-based fast paths additionally carry a `score` field.

| Path | Returned Value | `reason` | Notes |
|---|---|---|---|
| Score < 600 | `'REJECTED'` | `score_below_threshold` | Also returns `score` field |
| Score >= 750 | `'APPROVED'` | `score_excellent` | Also returns `score` field |
| LLM rating `high` | full `@risk_report` text | `REJECTED: qualitative_risk_high` | |
| LLM rating `medium` | full `@risk_report` text | `MANUAL_REVIEW: qualitative_risk_medium` | |
| LLM rating `low` | full `@risk_report` text | `APPROVED: qualitative_risk_low` | |
| ConnectionError | error message string | `PENDING: system_error` | Signals a retriable system fault |