## 0. High-level Description

`code_pipeline` implements a **spec-gated, test-driven code generation lifecycle** using SPL 3.0 workflow composition. The pipeline begins with a mandatory spec-analysis gate (via CALL to the `analyze_spec` sub-workflow): if the INPUT `@spec` does not yield a `[READY]` sentinel token, the WORKFLOW aborts immediately with `status = 'vague_spec'`, preventing wasted compute on underspecified requests. Passing the gate triggers a WHILE-loop (bounded by INPUT `@max_cycles`) that chains four sub-workflow CALLs per iteration — `generate_code`, `review_code`, `improve_code`, and `test_code` — where the loop continues only while the test result lacks a `[PASSED]` sentinel token, forming a **self-refine / test-gated retry** pattern. After the loop exits (on pass or exhaustion), two unconditional CALLs produce documentation (`document_code`) and reverse-engineer a derived spec from the generated implementation (`extract_spec`); an optional **closure check** is then triggered by EVALUATE on the BOOL INPUT `@check_closure`, which CALLs `spec_judge` to compare the original and derived specs and appends a structured closure report to the OUTPUT. Multi-model routing is handled by resolving each of eight per-task model slots from the INPUT MAP `@task_models`, with each slot falling back to the global `@pipeline_model` default via EVALUATE when empty, enabling fine-grained assignment of lighter models (e.g. `gemma3`) to fast tasks like analysis or judging without changing the main pipeline model. LOGGING is emitted at INFO for lifecycle milestones, WARN for gate failures and test retries, DEBUG for model-routing diagnostics, and ERROR for fatal infrastructure faults; two EXCEPTION handlers cover `RefusalToAnswer` (soft abort with `status = 'refused'`) and `ModelUnavailable` (hard abort with `status = 'failed'`).

---

## 1. Purpose

Transforms a plain-text specification into reviewed, tested, documented source code in a chosen target language, with an optional self-consistency check that verifies the implementation still matches the original intent.

---

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@spec` | *(required)* | Plain-text description of the code to generate |
| `@lang` | `'python'` | Target language; supported values: `python`, `go`, `ts`, `js` |
| `@pipeline_model` | `'gemma4'` | Global fallback LLM for any task not overridden in `@task_models` |
| `@task_models` | `{}` | Map of per-task model overrides; keys: `analyze`, `generate`, `review`, `improve`, `test`, `document`, `extract`, `judge` |
| `@max_cycles` | `3` | Maximum generate→review→improve→test retry iterations before proceeding regardless of test outcome |
| `@check_closure` | `TRUE` | Whether to run the spec-vs-derived-spec closure check at the end |
| `@log_dir` | `'cookbook/50_code_pipeline/logs-spl'` | Root directory for all file artifacts written during the run |

---

## 3. Process

1. **Resolve per-task models.** For each of the eight task slots (`analyze`, `generate`, `review`, `improve`, `test`, `document`, `extract`, `judge`), read from `@task_models`; if the value is empty, substitute `@pipeline_model`. This produces eight resolved model variables used throughout.

2. **Emit startup logs.** Log pipeline parameters at INFO level and the full model-routing table at DEBUG level.

3. **Step 0 — Spec analysis gate.** CALL `analyze_spec` with `@spec`, the resolved analyze-model, and `@log_dir`. Inspect the result:
   - If it contains `[READY]`: log success and continue.
   - Otherwise: log a WARN, and RETURN the analysis immediately with `status = 'vague_spec'` — the pipeline halts here.

4. **Persist input spec.** CALL `write_file` to write `@spec` to `{@log_dir}/spec/input.md`.

5. **Initialise loop state.** Set `@cycle := 0` and `@test_passed := FALSE`.

6. **Steps 1 + 2 — Generate → Review → Improve → Test loop.** Repeat while tests have not passed AND `@cycle < @max_cycles`:
   - Increment `@cycle`.
   - CALL `generate_code` → stores code in `target/{lang}/code.{ext}`.
   - CALL `review_code` on the generated code → stores feedback in `target/{lang}/review.md`.
   - CALL `improve_code` with the code and feedback → overwrites `target/{lang}/code.{ext}`.
   - CALL `test_code` on the improved code → stores verdict in `tests/{lang}/result.md`.
   - EVALUATE test result: if it contains `[PASSED]`, set `@test_passed := TRUE` and exit the loop; otherwise log a WARN and retry.

7. **Step 3a — Document.** CALL `document_code` with the final code and spec → writes `target/{lang}/docs.md`, result stored in `@docs`.

8. **Step 3b — Extract spec from implementation.** CALL `extract_spec` on the final code → writes `spec/extracted.md`, result stored in `@out_spec`.

9. **Step 3c — Closure check (conditional).** EVALUATE `@check_closure`:
   - If `TRUE`: CALL `spec_judge` comparing `@spec` against `@out_spec`, then append a formatted `## Closure Report` section (original spec, derived spec, and judge verdict) to `@docs`.
   - If `FALSE`: log at DEBUG that the check was skipped.

10. **Complete.** Log a final INFO summary (language, cycle count, test pass status, closure flag) and RETURN `@docs`.

---

## 4. Error Handling

- **`RefusalToAnswer`** — Logged at WARN. Pipeline aborts and returns the string `'Refused.'` with `status = 'refused'`. Triggered if a model declines to generate code (e.g. policy refusal).
- **`ModelUnavailable`** — Logged at ERROR. Pipeline aborts and returns `'[ERROR] Model unavailable.'` with `status = 'failed'`. Triggered if the designated LLM endpoint cannot be reached or is overloaded.
- **Vague spec (inline, not an EXCEPTION)** — Detected in Step 3 via the absence of `[READY]` in `analyze_spec` output; handled by an EVALUATE branch that returns early with `status = 'vague_spec'` before any code generation begins.

---

## 5. Output

The primary OUTPUT is `@docs` (TEXT), which is the generated documentation for the final implementation. When `@check_closure = TRUE`, `@docs` is extended with an appended `## Closure Report` section containing the original spec, the reverse-engineered spec extracted from the code, and the judge's verdict on their semantic alignment.

| Scenario | Return value | `status` metadata |
|---|---|---|
| Normal completion | Documentation string (+ optional closure report) | *(no explicit status set — success implied)* |
| Spec too vague | Raw `analyze_spec` output | `'vague_spec'` |
| Model refused generation | `'Refused.'` | `'refused'` |
| Model unreachable | `'[ERROR] Model unavailable.'` | `'failed'` |

Additional runtime artifacts are written to the filesystem under `@log_dir` across six files: `spec/input.md`, `spec/analysis.md`, `spec/extracted.md`, `target/{lang}/code.{ext}`, `target/{lang}/review.md`, `target/{lang}/docs.md`, and `tests/{lang}/result.md`.