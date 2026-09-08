## 0. High-level Description

This workflow implements a **prompt self-tuning (meta-programming)** technique — an automated one-shot A/B optimization loop that improves a baseline prompt by analyzing a known failure case. Two `CREATE FUNCTION` definitions drive the core logic: `variation_prompt`, a meta-prompting template that instructs the LLM to act as a "meta-prompting expert" and generate exactly one improved prompt variant (identified by `variant_num`) with strict output constraints (prompt text only — no explanation, label, or quotes); and `test_prompt`, a transparent pass-through template that executes an arbitrary prompt against a test input by injecting `prompt_text` directly as the instruction preamble. Control flow is entirely linear — no WHILE loop is used; instead, two sequential GENERATE calls produce variants V1 and V2, two further GENERATE calls test each against the failing case, and two CALL invocations to `check_quality` produce pass/fail scores. Winner selection uses nested EVALUATE branches: if `@score_v1` contains `'pass'`, V1 wins; else if `@score_v2` contains `'pass'`, V2 wins; else the baseline is retained (logged at WARN level). A final CALL to `write_file` persists the winning prompt to `{log_dir}/winning_prompt.md`. LOGGING is used throughout at INFO, DEBUG, and WARN levels to trace variant text, scores, and selection outcome. The single EXCEPTION handler catches `GenerationError` and falls back to returning the original baseline prompt with a diagnostic status field.

## 1. Purpose

Automatically improve a failing LLM prompt by generating two targeted variants via meta-prompting, scoring each against the known failure case, and returning (and persisting) the best-performing prompt.

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@baseline_prompt` | `'Summarize this technical document.'` | The original prompt to be improved |
| `@failed_case` | `'The document describes a complex quantum algorithm.'` | The specific input on which the baseline prompt underperforms |
| `@log_dir` | `'cookbook/43_prompt_self_tuning/logs-spl'` | Directory path where the winning prompt file is written |

## 3. Process

1. LOG at INFO: announce variant generation for the failing case.
2. GENERATE `variation_prompt(@baseline_prompt, @failed_case, '1')` → `@v1` — ask the LLM (as meta-prompting expert) to produce an improved prompt variant 1.
3. GENERATE `variation_prompt(@baseline_prompt, @failed_case, '2')` → `@v2` — same, for variant 2.
4. LOG both variants at DEBUG level.
5. LOG at INFO: announce the A/B test phase.
6. GENERATE `test_prompt(@v1, @failed_case)` → `@result_v1` — run variant 1 against the failing case.
7. CALL `check_quality(@result_v1)` → `@score_v1` — score the output (expected to return a string containing `'pass'` or not).
8. LOG `@score_v1` at DEBUG.
9. GENERATE `test_prompt(@v2, @failed_case)` → `@result_v2` — run variant 2 against the failing case.
10. CALL `check_quality(@result_v2)` → `@score_v2` — score the output.
11. LOG `@score_v2` at DEBUG.
12. EVALUATE `@score_v1`: if it contains `'pass'`, LOG "Winner: variant 1" at INFO and assign `@winning_prompt := @v1`.
13. Otherwise, EVALUATE `@score_v2`: if it contains `'pass'`, LOG "Winner: variant 2" at INFO and assign `@winning_prompt := @v2`.
14. Otherwise (neither passed), LOG "No variant passed — retaining baseline prompt" at WARN and assign `@winning_prompt := @baseline_prompt`.
15. CALL `write_file('{@log_dir}/winning_prompt.md', @winning_prompt)` → NONE — persist the winning prompt to disk.
16. RETURN `@winning_prompt` with metadata `status = 'complete'`.

## 4. Error Handling

- **`GenerationError`** — if any GENERATE step fails, the workflow immediately returns the original `@baseline_prompt` with `status = 'baseline_fallback'` and `reason = 'generation_error'`, ensuring the caller always receives a usable prompt even when the LLM is unavailable or produces an error.

## 5. Output

| Field | Value / Type |
|---|---|
| Return value (`@winning_prompt`) | `TEXT` — the best prompt found: variant 1, variant 2, or the original baseline |
| `status` (success path) | `'complete'` |
| `status` (error path) | `'baseline_fallback'` |
| `reason` (error path only) | `'generation_error'` |
| Side-effect | File written to `{log_dir}/winning_prompt.md` containing the winning prompt text |