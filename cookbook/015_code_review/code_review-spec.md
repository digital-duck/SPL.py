## 0. High-level Description

This workflow implements a **multi-pass code review** pattern, decomposing the analysis problem into four independent specialist passes — security audit, performance analysis, style/best-practices, and bug detection — before synthesizing all findings into a final structured report. The single CREATE FUNCTION declared in the script, `detect_lang`, acts as a lightweight, deterministic-style LLM probe that returns only a bare language name, using a tightly bounded output constraint ("Reply with only the language name — nothing else") to keep the result clean for downstream interpolation. Four additional GENERATE calls (`security_audit`, `performance_review`, `style_review`, `bug_detection`) execute in strict sequential order, each scoped to the detected language, and their outputs are immediately persisted to disk via CALL `write_file` side-effects into per-category Markdown files under `@log_dir`. After the four analysis passes, three separate GENERATE `severity_score` calls assign a numeric score to the security, performance, and bug findings, which drives the final EVALUATE branch: a security score above 8 triggers a `critical_issues / block` verdict with a WARN-level log, a score above 5 produces `needs_fixes / request_changes`, and anything lower yields `approved / approve`. Two EXCEPTION types are handled: `ContextLengthExceeded` gracefully degrades by summarising the code first and running a single `quick_review` instead of four passes, while `BudgetExceeded` short-circuits after the security pass only, returning whatever security findings were completed and flushing them to disk.

---

## 1. Purpose

Automatically review a code snippet or file through four specialist LLM passes (security, performance, style, bugs), score the severity of each category, synthesize a final structured report, and return a machine-readable verdict indicating whether the code should be approved, revised, or blocked.

---

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@code` | *(required)* | Either raw source code text or a file path to be read from disk |
| `@log_dir` | `cookbook/15_code_review/logs` | Directory where per-pass Markdown log files and the final report are written |

---

## 3. Process

1. **Resolve code source** — CALL `read_file(@code)` into `@file_content`. EVALUATE the result: if non-empty, log that a file is being read and set `@code_to_review := @file_content`; otherwise log that raw input is being reviewed and set `@code_to_review := @code`.

2. **Detect language** — GENERATE `detect_lang(@code_to_review)` into `@language`, then trim whitespace. Log the detected language at INFO level.

3. **Pass 1 — Security audit** — GENERATE `security_audit(@code_to_review, @language)` into `@security_findings`. Log findings at DEBUG level. CALL `write_file` to persist as `security.md`.

4. **Pass 2 — Performance review** — GENERATE `performance_review(@code_to_review, @language)` into `@perf_findings`. Log at DEBUG. CALL `write_file` → `performance.md`.

5. **Pass 3 — Style review** — GENERATE `style_review(@code_to_review, @language)` into `@style_findings`. Log at DEBUG. CALL `write_file` → `style.md`.

6. **Pass 4 — Bug detection** — GENERATE `bug_detection(@code_to_review, @language)` into `@bug_findings`. Log at DEBUG. CALL `write_file` → `bugs.md`.

7. **Severity scoring** — GENERATE `severity_score` separately for security, performance, and bug findings to produce `@sec_score`, `@perf_score`, and `@bug_score`. Log all three scores together at INFO level.

8. **Synthesize report** — GENERATE `synthesize_review(...)` passing all four findings plus their three scores into `@review`. CALL `write_file` → `review.md`.

9. **Verdict decision** — EVALUATE `@sec_score`:
   - `> 8` → log a WARN, RETURN `@review` with `status = 'critical_issues'`, `verdict = 'block'`
   - `> 5` → RETURN `@review` with `status = 'needs_fixes'`, `verdict = 'request_changes'`
   - otherwise → RETURN `@review` with `status = 'approved'`, `verdict = 'approve'`

---

## 4. Error Handling

- **`ContextLengthExceeded`** — The code is too large for a full multi-pass review. The workflow degrades gracefully: GENERATE `summarize_code(@code_to_review)` to compress the input, then GENERATE `quick_review(@summary, @language)` to produce a single combined review. The result is written to `review.md` and returned with `status = 'partial_large_file'`.

- **`BudgetExceeded`** — Token or cost budget was exhausted mid-run (after at least the security pass completed). The workflow short-circuits: CALL `write_file` to flush whatever `@security_findings` exist to `security.md`, then RETURN `@security_findings` directly with `status = 'security_only'`, prioritising the highest-risk findings over a complete review.

---

## 5. Output

The OUTPUT variable `@review` is a synthesized Markdown code-review report. It is always written to `{@log_dir}/review.md` on disk (except in the `BudgetExceeded` path, which returns raw security findings). The RETURN statement carries the following metadata fields depending on outcome:

| Condition | `status` | `verdict` |
|---|---|---|
| Security score > 8 | `critical_issues` | `block` |
| Security score > 5 | `needs_fixes` | `request_changes` |
| Security score ≤ 5 | `approved` | `approve` |
| Code too large | `partial_large_file` | *(absent)* |
| Budget exhausted | `security_only` | *(absent)* |