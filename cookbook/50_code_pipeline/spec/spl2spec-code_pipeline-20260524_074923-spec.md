## Summary

`code_pipeline` is a fully autonomous code generation system that takes a natural language specification and produces tested, documented source code in a target programming language. It gates on spec clarity before investing compute, iteratively improves code until tests pass, and optionally verifies that the final implementation still faithfully captures the original intent — a property called *closure*. Development teams and individual engineers benefit by getting reliable, auditable code artifacts with no manual review loop required.

---

## Detailed Specification

### 1. Purpose

Transform a natural language code specification into tested, documented source code in a configurable target language, with quality-gated retry and optional semantic fidelity verification between the original intent and the final implementation.

---

### 2. High-level Description

The `code_pipeline` WORKFLOW orchestrates eight imported sub-workflows across four sequential phases. In Phase 0, it CALLs `analyze_spec` and EVALUATEs the result for the sentinel token `[READY]`; if absent, the pipeline RETURNs immediately with `status = 'vague_spec'`, avoiding wasted compute on underspecified inputs. Phases 1 and 2 execute inside a WHILE loop bounded by `@max_cycles`: each iteration CALLs `generate_code` to produce initial source, `review_code` to surface feedback, and `improve_code` to apply that feedback; it then CALLs `test_code` and EVALUATEs for the sentinel `[PASSED]`, setting a boolean flag to exit the loop on success or continuing to retry on failure. Phase 3 CALLs `document_code` unconditionally, then `extract_spec` to reverse-engineer a derived specification from the final implementation; an optional closure check (controlled by the boolean `@check_closure`) EVALUATEs whether to CALL `spec_judge`, which compares original and derived specs and appends a structured `## Closure Report` to the output. Two EXCEPTION handlers provide declarative error recovery for `RefusalToAnswer` and `ModelUnavailable`, each RETURNing a non-trivial status token. Per-task model routing is resolved at startup via eight EVALUATE statements that read from the `@task_models` MAP and fall back to `@pipeline_model` for any absent key, enabling lightweight models to handle fast tasks while reserving capable models for generation and judging.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| Pipeline orchestrator | `WORKFLOW code_pipeline` | Top-level entry point; imports 8 sub-workflows via `IMPORT` |
| Sub-workflow dispatch | `CALL <name>(...) INTO @var` | All 8 phases dispatch this way; Hub registry resolves names |
| Spec clarity gate | `EVALUATE @analysis WHEN contains('[READY]') THEN ... ELSE RETURN @analysis WITH status='vague_spec' END` | Sentinel token `[READY]` guards pipeline entry |
| Test-gated retry loop | `WHILE NOT @test_passed AND @cycle < @max_cycles DO ... END` | Exits on `[PASSED]` sentinel or cycle exhaustion |
| Test verdict branch | `EVALUATE @test_result WHEN contains('[PASSED]') THEN @test_passed := TRUE END` | Sets the WHILE loop exit flag |
| Optional closure check | `EVALUATE @check_closure WHEN = TRUE THEN CALL spec_judge(...) ... END` | Boolean input parameter drives the CALL |
| Per-task model fallback | `EVALUATE @m_X WHEN = '' THEN @m_X := @pipeline_model END` | Applied to all 8 task slots at startup |
| Shared mutable state | SPL `@var` bindings | `@cycle`, `@test_passed`, `@code`, `@feedback`, `@docs`, `@out_spec` |
| Artifact persistence | `CALL write_file(...) INTO NONE` | Writes `spec/input.md` after gate passes; sub-workflows write their own artifacts |
| Content refusal recovery | `EXCEPTION WHEN RefusalToAnswer THEN RETURN 'Refused.' WITH status='refused'` | Declarative; halts pipeline cleanly |
| Model failure recovery | `EXCEPTION WHEN ModelUnavailable THEN RETURN '[ERROR]...' WITH status='failed'` | Declarative; surfaces infrastructure errors |

---

### 4. Logical Functions / Prompts

**analyze_spec** (`00_analyze_spec`)
- Role: Validates that the input specification is concrete enough to implement before any code is generated.
- Key conventions: Emits the sentinel token `[READY]` in its output when the spec is actionable. Absence of `[READY]` is the vagueness signal. Writes `spec/analysis.md` with a structured restatement of the spec.

**generate_code** (`01_generate_code`)
- Role: Produces an initial implementation in the requested target language directly from the spec.
- Key conventions: Accepts `@spec`, `@lang`, resolved model, and `@log_dir`; writes `target/{lang}/code.{ext}` where `ext` is language-dependent (`py`, `go`, `ts`, `js`, …). Called once per loop cycle.

**review_code** (`02_review_code`)
- Role: Produces structured critique of the generated code covering correctness, style, and completeness.
- Key conventions: Writes `target/{lang}/review.md`; its output is passed directly as `@feedback` into `improve_code`. Scoped to the current `@lang`.

**improve_code** (`03_improve_code`)
- Role: Applies the reviewer's feedback to produce a refined version of the code.
- Key conventions: Accepts both `@code` and `@feedback`; overwrites `target/{lang}/code.{ext}` in-place. The updated `@code` variable propagates into `test_code` and subsequent iterations.

**test_code** (`04_test_code`)
- Role: Exercises the improved code against the original spec and determines whether it passes.
- Key conventions: Emits the sentinel token `[PASSED]` or `[FAILED]` to drive the WHILE loop. Writes `tests/{lang}/result.md` with the verdict and failure details for debugging.

**document_code** (`05_document_code`)
- Role: Generates user-facing documentation from the final passing implementation and original spec.
- Key conventions: Writes `target/{lang}/docs.md`; its output becomes the primary `@docs` return value of the entire pipeline.

**extract_spec** (`06_extract_spec`)
- Role: Reverse-engineers a plain-English specification from the final code — a derived artifact used only by the closure check.
- Key conventions: Writes `spec/extracted.md`. Does not use the original `@spec` as input; the LLM derives intent purely from the implementation.

**spec_judge** (`07_spec_judge`)
- Role: Compares the original user spec against the derived spec and emits a semantic fidelity verdict.
- Key conventions: Emits `[CLOSED]` when the implementation faithfully captures the original intent, or `[DIVERGED]` when semantic drift is detected. Its full output is appended to `@docs` as a `## Closure Report` section containing both specs and the verdict.

---

### 5. Control Flow

**Startup — model resolution:** Eight EVALUATE statements resolve each task slot from `@task_models`; any absent or empty key falls back to `@pipeline_model`. This happens before any LLM call.

**Step 0 — spec gate:** CALL `analyze_spec`. EVALUATE output for `[READY]`. If the token is absent, RETURN with `status = 'vague_spec'` — pipeline terminates here. On success, `spec/input.md` is written via `CALL write_file`.

**Steps 1+2 — WHILE loop:** Loop condition: `NOT @test_passed AND @cycle < @max_cycles`. Each iteration increments `@cycle`, then sequentially CALLs `generate_code` → `review_code` → `improve_code` → `test_code`. After `test_code`, EVALUATE `@test_result` for `[PASSED]`: if found, set `@test_passed := TRUE` (loop exits naturally on next condition check); otherwise the loop retries. If `@max_cycles` is exhausted without `[PASSED]`, the pipeline continues to Step 3 with whatever code was produced last.

**Step 3a — documentation:** CALL `document_code` unconditionally; result stored in `@docs`.

**Step 3b — spec extraction:** CALL `extract_spec` on final `@code`; result stored in `@out_spec`.

**Step 3c — closure check:** EVALUATE `@check_closure`: if TRUE, CALL `spec_judge` and concatenate the full closure report (original spec, derived spec, verdict) into `@docs`. If FALSE, skip silently.

**Termination:** RETURN `@docs` (successful completion). EXCEPTION handlers intercept `RefusalToAnswer` → `status='refused'` and `ModelUnavailable` → `status='failed'` at any point in the pipeline.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Transform a natural language code specification into tested, \
documented source code in a configurable target language, with quality-gated retry and \
optional semantic fidelity verification between the original intent and the final implementation." \
--mode workflow

# Step 2 — compile to any target
spl3 splc compile code_pipeline.spl --lang python/pocketflow
spl3 splc compile code_pipeline.spl --lang python/langgraph
spl3 splc compile code_pipeline.spl --lang go
```