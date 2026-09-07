## Summary

`code_pipeline` is a fully autonomous code-generation system that takes a plain-English requirement, produces working source code in a chosen language, iteratively tests and repairs it, generates documentation, and optionally verifies that the final implementation still matches the original intent. It is designed for developers and teams who want a repeatable, auditable pipeline from specification to production-ready code without manual iteration.

---

## Detailed Specification

### 1. Purpose

Generate, test-gate, document, and optionally closure-verify source code in any supported language (Python, Go, TypeScript, JavaScript) from a plain-English specification, with automatic retry on test failures and per-task model routing.

---

### 2. High-level Description

`code_pipeline` is a WORKFLOW that orchestrates eight imported sub-workflows through a structured three-phase lifecycle. In Phase 0, it CALLs `analyze_spec` and uses EVALUATE to gate the pipeline on a `[READY]` sentinel token, returning early with `status='vague_spec'` if the specification is too ambiguous to proceed. In Phase 1, a WHILE loop bounded by `@max_cycles` drives a generate→review→improve→test cycle: `generate_code` produces initial source, `review_code` critiques it, `improve_code` applies the feedback, and `test_code` returns a verdict; an EVALUATE on the `[PASSED]` sentinel token either breaks the loop by setting `@test_passed := TRUE` or allows it to retry. Phase 2 finalises the artifact with `document_code` and then `extract_spec`, which reverse-engineers a spec from the finished implementation; a final EVALUATE on `@check_closure` conditionally CALLs `spec_judge` to compare the original and derived specs and appends a closure report to `@docs`. Per-task model selection is resolved at startup through a MAP input (`@task_models`) that overrides the global `@pipeline_model` for any named task key; absent keys fall back to the global default via EVALUATE equality checks. EXCEPTION handlers for `RefusalToAnswer` and `ModelUnavailable` provide declarative error termination with distinct status tokens (`refused`, `failed`). All intermediate artifacts are written to a structured log directory tree (`spec/`, `target/{lang}/`, `tests/{lang}/`) via CALL side-effects throughout the pipeline.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW` | `WORKFLOW code_pipeline` | Top-level orchestrator; eight sub-workflows IMPORTed without `.spl` extension (SPL 3.1+) |
| `CREATE FUNCTION` | `IMPORT '00_analyze_spec'` … `IMPORT '07_spec_judge'` | Each imported file exposes a named callable that acts as a reusable prompt template/sub-workflow |
| `GENERATE` / `CALL` | `CALL analyze_spec(…) INTO @analysis`, `CALL generate_code(…) INTO @code`, etc. | All eight sub-workflows are invoked as CALL side-effects that produce LLM-driven output; `CALL write_file(…)` is a pure side-effect with no meaningful return |
| `EVALUATE` (sentinel) | `EVALUATE @analysis WHEN contains('[READY]')` | Spec quality gate; `[READY]` advances, any other output aborts with `status='vague_spec'` |
| `EVALUATE` (sentinel) | `EVALUATE @test_result WHEN contains('[PASSED]')` | Test verdict inside retry loop; `[PASSED]` sets `@test_passed := TRUE` to exit WHILE |
| `EVALUATE` (bool) | `EVALUATE @check_closure WHEN = TRUE` | Optional closure branch; conditionally CALLs `spec_judge` and appends closure report to `@docs` |
| `EVALUATE` (fallback) | `EVALUATE @m_analyze WHEN = '' THEN @m_analyze := @pipeline_model END` (×8) | Per-task model resolution; missing MAP keys fall back to global default |
| `WHILE` | `WHILE NOT @test_passed AND @cycle < @max_cycles DO … END` | Test-gated retry; bounded by `@max_cycles` (default 3); exits early on `[PASSED]` verdict |
| `RETURN … WITH status=` | `RETURN @analysis WITH status='vague_spec'` | Early abort when spec gate fails |
| `RETURN … WITH status=` | `RETURN 'Refused.' WITH status='refused'` | Exception path for model refusal |
| `RETURN … WITH status=` | `RETURN '[ERROR] Model unavailable.' WITH status='failed'` | Exception path for model unavailability |
| `EXCEPTION WHEN` | `WHEN RefusalToAnswer THEN … WHEN ModelUnavailable THEN …` | Declarative error handlers with distinct status tokens |
| `@vars` (shared state) | `@code`, `@feedback`, `@test_result`, `@docs`, `@analysis`, `@out_spec`, `@closure_report`, `@cycle`, `@test_passed`, `@m_*` | All mutable workflow state; `@cycle` and `@test_passed` are loop-control sentinels |

---

### 4. Logical Functions / Prompts

**`analyze_spec` (00)**
- **Role**: Quality gate on the incoming specification before any code is generated.
- **Key conventions**: Must emit `[READY]` to advance; absence of the token signals a vague or unactionable spec and causes early pipeline termination with `status='vague_spec'`. Also produces a structured restatement written to `spec/analysis.md`.

**`generate_code` (01)**
- **Role**: Translates the validated specification into raw source code in `@lang`.
- **Key conventions**: Output is source code written to `target/{lang}/code.{ext}`; the extension is language-dependent (`.py`, `.go`, `.ts`, `.js`).

**`review_code` (02)**
- **Role**: Critiques the generated code for correctness, style, and completeness.
- **Key conventions**: Produces structured feedback written to `target/{lang}/review.md`; feedback is passed directly into `improve_code` as `@feedback`.

**`improve_code` (03)**
- **Role**: Applies the reviewer's feedback to produce a revised version of the code.
- **Key conventions**: Overwrites `target/{lang}/code.{ext}` with the improved version; takes the original `@code`, `@feedback`, and an optional patch context (passed as `''` here).

**`test_code` (04)**
- **Role**: Evaluates the improved code against the specification and emits a test verdict.
- **Key conventions**: Must emit `[PASSED]` to exit the retry loop; any other output triggers another cycle. Writes verdict to `tests/{lang}/result.md`.

**`document_code` (05)**
- **Role**: Generates user-facing documentation for the final code artifact.
- **Key conventions**: Output written to `target/{lang}/docs.md`; returned as `@docs`, the workflow's primary output.

**`extract_spec` (06)**
- **Role**: Reverse-engineers a plain-English specification from the finished implementation.
- **Key conventions**: Output written to `spec/extracted.md`; feeds the closure check as `@out_spec`.

**`spec_judge` (07)**
- **Role**: Compares the original user spec against the extracted spec and classifies the result.
- **Key conventions**: Emits `[CLOSED]` (implementation matches intent) or `[DIVERGED]` (semantic drift detected); verdict is appended to `@docs` as a Closure Report section. Only called when `@check_closure = TRUE`.

---

### 5. Control Flow

1. **Model resolution** — Eight EVALUATE equality checks resolve per-task model overrides from the `@task_models` MAP, falling back to `@pipeline_model` for any absent key.
2. **Spec gate (Step 0)** — `analyze_spec` is CALLed; EVALUATE checks for `[READY]`. If absent, `RETURN @analysis WITH status='vague_spec'` terminates the pipeline immediately.
3. **Retry loop (Steps 1–2)** — A WHILE loop (`NOT @test_passed AND @cycle < @max_cycles`) executes the four-step inner cycle: generate → review → improve → test. After each test, EVALUATE on `[PASSED]` either sets `@test_passed := TRUE` (exiting the loop) or logs a warning and retries. At exhaustion (`@cycle = @max_cycles`) the loop exits regardless of test outcome.
4. **Finalisation (Step 3)** — `document_code` and `extract_spec` run unconditionally. Then EVALUATE on `@check_closure` conditionally CALLs `spec_judge` and appends the closure report to `@docs`.
5. **Normal termination** — `RETURN @docs` with the full documentation (and optional closure appendix).
6. **Exception paths** — `RefusalToAnswer` returns `status='refused'`; `ModelUnavailable` returns `status='failed'`.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl \
  --description "Generate, test-gate, document, and optionally closure-verify \
source code in any supported language (Python, Go, TypeScript, JavaScript) from \
a plain-English specification, with automatic retry on test failures and \
per-task model routing." \
  --mode workflow

# Step 2 — compile to any target
spl3 splc compile code_pipeline.spl --lang python/pocketflow
spl3 splc compile code_pipeline.spl --lang python/langgraph
spl3 splc compile code_pipeline.spl --lang go
```