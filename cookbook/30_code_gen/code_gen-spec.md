## 0. High-level Description

This workflow implements a **sequential-generation with self-refine** pattern: it first generates a function implementation, subjects it to an LLM-powered review pass, conditionally repairs it via EVALUATE branching, then generates unit tests against the (possibly refined) implementation before assembling a final combined artifact. Two helper CREATE FUNCTIONs — `language_conventions` and `test_framework_guide` — act as inline lookup tables that inject language-specific style rules (e.g., PEP 8 + Google docstrings for Python, `Result<T,E>` idioms for Rust) and test-framework conventions (e.g., pytest fixtures and parametrize, Jest `describe/it` blocks) directly into the downstream GENERATE prompts. The EVALUATE step on `@review_notes` applies a content-pattern guard (`contains('issue') OR contains('error') OR contains('problem')`), triggering a `fix_implementation` GENERATE only when defects are detected, and logging a WARN when repairs are needed. A CALL to the external tool `load_spec` in Step 0 transparently resolves `@spec` from either an inline string or a file path before any generation begins. LOGGING statements bracket every major phase at INFO or DEBUG level, providing a structured execution trace. The single EXCEPTION handler for `GenerationError` enables graceful degradation: if test generation fails, the workflow returns the implementation alone rather than aborting entirely.

---

## 1. Purpose

Generate a language-idiomatic function implementation together with its unit tests from a plain-English specification, with an automatic self-review-and-fix pass to improve code quality before tests are written.

---

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@spec` | *(required)* | Either an inline text description of the function to implement, or a file path whose contents are loaded automatically via `load_spec()`. |
| `@language` | `'Python'` | Target programming language. Drives both style conventions and test framework defaults. Recognised values: `Python`, `Go`, `TypeScript`, `Rust`; any other value falls back to generic guidance. |
| `@test_framework` | `'default'` | Test framework to target. Combined with `@language` to select specific guidance (e.g., `Python:pytest`, `Go:testing`, `TypeScript:jest`). Falls back to a generic description when the combination is unrecognised. |

---

## 3. Process

1. **Log start.** Emit an INFO log recording `@language` and `@test_framework`.

2. **Resolve spec (Step 0).** CALL `load_spec(@spec)`, overwriting `@spec` in-place. If `@spec` was a file path the tool returns the file's contents; if it was inline text it passes through unchanged. Log the resolved value at DEBUG.

3. **Generate implementation (Step 1).** GENERATE `implement_function` with the resolved spec, the target language, and the inline style guide produced by `language_conventions(@language)`. Store the result in `@implementation`. Log completion at DEBUG.

4. **Self-review implementation (Step 2).** GENERATE `review_implementation` against `@implementation`, `@spec`, and `@language`, producing `@review_notes`. Log the full review text at DEBUG.

5. **Conditionally fix implementation (Step 3).** EVALUATE `@review_notes`:
   - **If** the text contains `'issue'`, `'error'`, or `'problem'`: log a WARN, GENERATE `fix_implementation(@implementation, @review_notes, @language)`, and replace `@implementation` with the fixed version.
   - **Else**: log that the implementation looks good and skip the fix step.

6. **Generate unit tests (Step 4).** GENERATE `generate_tests` using the (possibly refined) `@implementation`, `@spec`, `@language`, and the framework guidance from `test_framework_guide(@language, @test_framework)`. Store in `@tests`. Log completion at DEBUG.

7. **Verify test syntax (Step 5).** GENERATE `verify_test_syntax(@tests, @language)` to perform a static syntax/parse check on the generated tests. Store the result in `@syntax_ok` and log it at DEBUG.

8. **Assemble final output (Step 6).** GENERATE `assemble_output(@implementation, @tests, @language)` to combine the implementation and tests into a single formatted artifact stored in `@final_output`. Log at DEBUG.

9. **Return.** Log completion at INFO and RETURN `@final_output` with metadata: `status = 'complete'`, `language = @language`, `test_framework = @test_framework`.

---

## 4. Error Handling

- **`GenerationError`** — Caught when any GENERATE call fails (most likely during test generation in Steps 4–6). The workflow logs a WARN and returns `@implementation` (the last successfully generated implementation) with `status = 'implementation_only'` and `reason = 'test_generation_failed'`, ensuring the caller always receives at least the function code.

---

## 5. Output

| Field | Value / Description |
|---|---|
| Primary output | `@final_output` (TEXT) — a combined artifact containing the function implementation and its unit tests, formatted by `assemble_output` for the target language. On `GenerationError`, contains only `@implementation`. |
| `status` | `'complete'` on full success; `'implementation_only'` if test generation failed. |
| `language` | Echo of the `@language` input parameter. |
| `test_framework` | Echo of the `@test_framework` input parameter. |
| `reason` | Present only on `GenerationError` degraded path; value: `'test_generation_failed'`. |