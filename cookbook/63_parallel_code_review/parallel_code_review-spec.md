## 0. High-level Description

This workflow implements a **parallel fan-out + merge** pattern for automated code review. Using `CALL PARALLEL`, it dispatches three independent sub-workflows — `style_review`, `security_audit`, and `test_generator` — concurrently against the same input code snippet; each sub-workflow is loaded via `IMPORT` and writes exclusively to its own `INTO @var`, eliminating interference. Once all three parallel branches complete, a single `GENERATE` call invokes the `merge_reviews` function, which instructs the LLM to act as a senior engineering lead consolidating the three reports into a structured output with prioritised action items (CRITICAL → MODERATE → LOW), verbatim test cases under a code block, and a production-readiness summary paragraph capped at 150 words for the action section. The `INPUT` parameter `@review_model` drives the model choice uniformly across all four LLM calls (the three sub-workflows and the merge), making the entire pipeline swappable via a single argument. `LOGGING` at `INFO` level bookends each major phase (start, parallel-complete, done) with structured context fields, and the `EXCEPTION` block handles two failure modes: `ModelUnavailable` (hard failure, returns an error sentinel) and `BudgetExceeded` (soft failure, returns whatever was generated with a `truncated` status).

---

## 1. Purpose

Runs style, security, and test-generation reviews of a code snippet in parallel, then merges all three into a single prioritised action plan ready for developer consumption.

---

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@code` | *(required)* | The source code snippet to review |
| `@lang` | `'python'` | Programming language of the snippet, passed to all sub-workflows |
| `@review_model` | `'gemma4'` | LLM model identifier used by all sub-workflows and the merge step |
| `@log_dir` | `'cookbook/63_parallel_code_review/logs-spl'` | Directory path forwarded to sub-workflows for log output |

---

## 3. Process

1. **Log start** — emit an `INFO` log recording `@lang` and `@review_model`.
2. **Parallel fan-out** — launch three sub-workflows concurrently via `CALL PARALLEL`:
   - `style_review` → checks style and correctness; result stored in `@style_fb`
   - `security_audit` → scans for security issues; result stored in `@sec_fb`
   - `test_generator` → produces test cases; result stored in `@test_fb`
   - All three receive identical arguments: `@code`, `@lang`, `@review_model`, `@log_dir`
3. **Log parallel completion** — emit an `INFO` log once all three branches have returned.
4. **Merge** — call `GENERATE merge_reviews(@style_fb, @sec_fb, @test_fb)` using `@review_model`, capped at **1024 output tokens**, storing the consolidated report in `@report`. The prompt instructs the model to produce:
   - **Action Items** — numbered, severity-ordered (CRITICAL → MODERATE → LOW), ≤150 words
   - **Test Coverage** — verbatim generated tests in a fenced code block
   - **Summary** — one paragraph production-readiness assessment
5. **Log completion** — emit an `INFO` log with the character length of `@report`.
6. **Return** `@report`.

---

## 4. Error Handling

- **`ModelUnavailable`** — logs an `ERROR` with the model name, then returns the literal string `'[ERROR] Model unavailable.'` with `status = 'failed'`. The report is not partially returned; the workflow terminates hard.
- **`BudgetExceeded`** — logs a `WARN` indicating the token budget was exceeded during the merge step, then returns whatever content was accumulated in `@report` with `status = 'truncated'`. Partial output is preserved rather than discarded.

---

## 5. Output

| Field | Value |
|---|---|
| `@report` | Full consolidated review report (Markdown with three sections) |
| `status` | *(absent on success)* · `'failed'` on `ModelUnavailable` · `'truncated'` on `BudgetExceeded` |

On success no metadata is attached; the report is returned directly. On `BudgetExceeded` the report may be incomplete but is still returned. On `ModelUnavailable` the report is replaced by an error string.