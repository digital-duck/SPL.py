## Summary

This system takes a natural-language coding problem description and autonomously produces a verified, working Python function. It generates test cases first, implements a solution, then executes all tests in parallel — and if any fail, an agent analyzes the failures and revises either the tests or the code (or both) before retrying. Developers and educators benefit by getting correct, test-validated code without manual debugging cycles.

---

## Detailed Specification

### 1. Purpose

Generate a verified Python function that solves a given coding problem by iteratively producing test cases, implementing the solution, and self-healing until all tests pass or a maximum iteration budget is exhausted.

---

### 2. High-level Description

This workflow implements a **self-healing code generation** pattern combining a linear **Workflow** phase with an **Agent** decision loop. It begins with a `GenerateTestCases` GENERATE call that prompts the LLM to produce 5–7 YAML-structured test cases — including basic cases, edge cases, and corner cases — from the raw problem description. Next, an `ImplementFunction` GENERATE call receives both the problem and the generated test cases and produces a complete Python function named exactly `run_code`, also in YAML format with an explicit reasoning field. A `RunTests` GENERATE step then executes the function against every test case in parallel using batch processing (analogous to `CALL PARALLEL`), collecting pass/fail results for each. The `RunTests` step performs a three-way EVALUATE: RETURN WITH `status="success"` when all tests pass, RETURN WITH `status="max_iterations"` when the iteration budget is exhausted, and RETURN WITH `status="failure"` otherwise, triggering the WHILE loop body. Inside the loop, a `Revise` GENERATE call acts as an agent: it receives the problem, current test cases, current function code, and the list of failed tests, then reasons about whether the failures are due to incorrect expected values in the tests, flawed implementation logic, or both — and outputs selective revisions in YAML form. Revised test cases and/or function code are written back to shared state before `RunTests` executes again. All LLM interactions use YAML with explicit `reasoning` fields and structural validation asserts at every step. The workflow exposes a `--max-iterations` guard (default 5) to bound the repair loop, and writes the final function to a configurable output file via a CALL side-effect.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW CodeGenerator` | `create_code_generator_flow()` + `shared` dict | Top-level orchestration; shared state carries all cross-step data |
| `CREATE FUNCTION generate_tests` | `GenerateTestCases.exec()` prompt string | Asks LLM for 5–7 YAML test cases with `reasoning` + `test_cases` fields |
| `CREATE FUNCTION implement_function` | `ImplementFunction.exec()` prompt string | Asks LLM for `run_code` implementation in YAML with `reasoning` + `function_code` fields |
| `CREATE FUNCTION revise` | `Revise.exec()` prompt string | Agent prompt: analyzes failures, outputs revised `test_cases` dict and/or `function_code` |
| `GENERATE generate_tests(@problem) INTO @test_cases` | `GenerateTestCases` Node `exec`→`post` | Stores parsed list into `shared["test_cases"]` |
| `GENERATE implement_function(@problem, @test_cases) INTO @function_code` | `ImplementFunction` Node | Stores code string into `shared["function_code"]` |
| `CALL PARALLEL run_test(...) INTO @test_results` | `RunTests` BatchNode | Runs all `(function_code, test_case)` pairs concurrently; collects pass/fail dicts |
| `GENERATE revise(...) INTO @revisions` | `Revise` Node | Agent call; writes back to `shared["test_cases"]` and/or `shared["function_code"]` |
| `WHILE iteration_count < max_iterations AND NOT all_passed DO` | `RunTests.post()` returning `"failure"` → `revise >> run_tests` edge | Loop body is `Revise → RunTests`; condition checked inside `RunTests.post` |
| `EVALUATE @test_results WHEN all_passed THEN ... WHEN max_iter THEN ... ELSE ...` | `RunTests.post()` returning `"success"` / `"max_iterations"` / `"failure"` | Three-way branch; only non-trivial tokens drive real control flow |
| `RETURN @function_code WITH status="success"` | `RunTests.post()` returning `"success"` (flow ends) | Terminal success path |
| `RETURN @function_code WITH status="max_iterations"` | `RunTests.post()` returning `"max_iterations"` (flow ends) | Terminal budget-exhausted path |
| `CALL write_file(@function_code) INTO @_` | `Path(out).write_text(...)` in `main.py` | Side-effect: persists generated function to disk |
| SPL `@var` shared variables | `shared["problem"]`, `shared["test_cases"]`, etc. | All cross-node state; no return values passed directly between nodes |
| `EXCEPTION WHEN ValidationError THEN ...` | `assert` statements in every `exec()` method | Structural validation of YAML output; missing fields raise `AssertionError` |

---

### 4. Logical Functions / Prompts

**`generate_tests`**
- **Role**: Seed the workflow with a comprehensive test suite before any code is written, ensuring test-first discipline.
- **Prompt conventions**: Instructs the LLM to output fenced YAML with two top-level keys: `reasoning` (multiline, explains parameter types and case strategy) and `test_cases` (list of `{name, input, expected}`). Input dict keys must match the target function's parameter names. Validated with structural asserts for all required fields.

**`implement_function`**
- **Role**: Produce the initial `run_code` implementation guided by both the problem statement and the already-generated test cases.
- **Prompt conventions**: Fenced YAML with `reasoning` (approach explanation) and `function_code` (must contain `def run_code`). The function name `run_code` is a hard sentinel enforced by assertion. The prompt explicitly shows numbered test cases to anchor the implementation.

**`revise`**
- **Role**: Act as an autonomous agent that diagnoses test failures and selectively patches tests, code, or both — the core of the self-healing loop.
- **Prompt conventions**: Fenced YAML with `reasoning`, an optional `test_cases` dict (1-based integer keys mapping to `{name, input, expected}` — only revised entries are included, not the full list), and an optional `function_code` block. Either or both revision fields may be absent if not needed. All included fields validated by assertion. The 1-based index convention for test case keys is load-bearing for the patch-in-place update logic.

---

### 5. Control Flow

1. **Start**: `GenerateTestCases` receives the problem text and produces structured test cases; stores them in shared state.
2. **Implement**: `ImplementFunction` receives problem + test cases; stores initial `run_code` in shared state.
3. **Test (batch)**: `RunTests` fans out over all `(function_code, test_case)` pairs in parallel, collects results, increments `iteration_count`.
4. **EVALUATE**: Three-way branch inside `RunTests`:
   - All tests pass → RETURN `"success"` → flow terminates (solution written to disk).
   - `iteration_count >= max_iterations` → RETURN `"max_iterations"` → flow terminates (partial results written).
   - Any test fails AND budget remains → RETURN `"failure"` → enter repair loop.
5. **WHILE loop body** (entered on `"failure"`): `Revise` agent analyzes failures and patches `shared["test_cases"]` and/or `shared["function_code"]` in place; control returns to step 3.
6. **Termination**: Loop exits only via `"success"` or `"max_iterations"` from `RunTests`.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "Generate a verified Python function that solves a given \
coding problem by iteratively producing test cases, implementing the solution, and \
self-healing until all tests pass or a maximum iteration budget is exhausted." \
--mode workflow

# Step 2 — compile to any target
spl3 splc compile code_generator.spl --lang python/pocketflow
spl3 splc compile code_generator.spl --lang python/langgraph
spl3 splc compile code_generator.spl --lang go
```