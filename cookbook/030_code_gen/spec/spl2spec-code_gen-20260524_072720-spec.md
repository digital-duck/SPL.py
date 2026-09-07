## Summary

This workflow takes a natural language description of a function (or a path to a spec file) and produces both a working implementation and its unit tests in one pass. It includes a self-review step that detects issues in the generated code and triggers an automatic fix before proceeding to test generation. Developers and teams benefit by getting a reviewable, testable code artifact without manual scaffolding.

---

## Detailed Specification

### 1. Purpose

Generate a language-idiomatic function implementation together with its unit test suite from a plain-text specification, with an automatic self-review and fix pass between the two generation steps.

---

### 2. High-level Description

The workflow `code_gen_with_tests` accepts a function specification (inline text or a file path resolved by a `CALL` to `load_spec`), a target language, and an optional test framework name. It opens by calling two inline `CREATE FUNCTION` templates — `language_conventions` and `test_framework_guide` — which are pure SQL-style CASE expressions that inject language- and framework-specific style rules as text into downstream prompts; they are not LLM calls. The first substantive GENERATE step, `implement_function`, produces the code artifact using the spec and the resolved conventions string. A second GENERATE step, `review_implementation`, acts as an LLM self-reviewer and returns prose notes about the implementation. An `EVALUATE` on those notes branches on sentinel keywords (`issue`, `error`, `problem`): when found, a third GENERATE call, `fix_implementation`, rewrites the implementation before continuing; otherwise that repair step is skipped entirely. The revised (or approved) implementation is then passed to `generate_tests` together with the original spec and the framework guide, producing the test suite. A lightweight `verify_test_syntax` GENERATE checks that the test output is syntactically coherent for the target language. Finally, `assemble_output` merges implementation and tests into a single formatted artifact returned as `@final_output` with `status = 'complete'`; a `GenerationError` exception handler provides a graceful fallback that returns just the implementation with `status = 'implementation_only'`.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `code_gen_with_tests` node class | `WORKFLOW code_gen_with_tests` | Declares the named, parameterized orchestration unit |
| `implement_function`, `review_implementation`, etc. | `GENERATE <fn>(...) INTO @var` | Each is a discrete LLM call whose result is bound to a named variable |
| `language_conventions`, `test_framework_guide` | `CREATE FUNCTION <name>` | Pure CASE-expression templates; return static text, not LLM output |
| `load_spec` tool | `CALL load_spec(@spec) INTO @spec` | Side-effect tool call that resolves a file path to its contents |
| Sentinel-keyword branch on review notes | `EVALUATE @review_notes WHEN contains('issue') OR contains('error') OR contains('problem') THEN ... ELSE ... END` | Real control-flow branch; triggers fix GENERATE or skips it |
| `fix_implementation` repair path | GENERATE inside EVALUATE THEN branch | Only executed when review notes flag a problem |
| `status = 'complete'` vs `status = 'implementation_only'` | `RETURN @var WITH status = '...'` | Non-trivial status tokens; drive exception vs. normal exit |
| `GenerationError` catch | `EXCEPTION WHEN GenerationError THEN` | Typed handler; returns partial result with explanatory metadata |
| `@spec`, `@implementation`, `@review_notes`, `@tests`, `@syntax_ok`, `@final_output` | SPL `@vars` | Shared mutable state threaded through each pipeline stage |

---

### 4. Logical Functions / Prompts

**`language_conventions(language)`**
- Role: Injects language-specific style rules into `implement_function`'s prompt.
- Convention: Pure CASE expression over known language strings; returns a single prose sentence of style constraints (e.g., "PEP 8 style. Type hints required."). Falls back to a generic guideline for unlisted languages.

**`test_framework_guide(language, framework)`**
- Role: Injects framework-specific testing conventions into `generate_tests`'s prompt.
- Convention: CASE over a composite key `language || ':' || framework`; falls back to "Standard test framework for \<language\>" for unknown combinations.

**`implement_function(@spec, @language, conventions)`**
- Role: Primary code generation; produces the full function implementation.
- Convention: Receives the raw spec, the target language, and the conventions string. Expected output: a single, complete, runnable code block.

**`review_implementation(@implementation, @spec, @language)`**
- Role: LLM self-review; evaluates the generated code against the original spec.
- Convention: Must surface problems using the sentinel words `issue`, `error`, or `problem` to trigger the EVALUATE branch; a clean review should contain none of these.

**`fix_implementation(@implementation, @review_notes, @language)`**
- Role: Repair pass; rewrites the implementation guided by the review notes.
- Convention: Receives both the flawed implementation and the reviewer's notes; expected output is a replacement implementation only (same format as `implement_function` output).

**`generate_tests(@implementation, @spec, @language, framework_guide)`**
- Role: Produces the unit test suite for the (possibly fixed) implementation.
- Convention: Has full visibility of the implementation so tests can reference real function signatures. The framework guide string controls assertion style, fixture patterns, and test organization.

**`verify_test_syntax(@tests, @language)`**
- Role: Static sanity check; confirms the test output is syntactically valid for the language.
- Convention: Result bound to `@syntax_ok` but not branched on in the current workflow; used for logging and future extension.

**`assemble_output(@implementation, @tests, @language)`**
- Role: Formatting step; merges implementation and tests into a single coherent document.
- Convention: Expected to add section headers, file boundaries, or language-appropriate packaging so the output is copy-paste ready.

---

### 5. Control Flow

1. **`CALL load_spec`** — resolves `@spec` to inline text (no-op if already text; reads file otherwise).
2. **`GENERATE implement_function`** — primary code artifact into `@implementation`.
3. **`GENERATE review_implementation`** — critique into `@review_notes`.
4. **`EVALUATE @review_notes`** — if review notes contain `issue`, `error`, or `problem`, a **`GENERATE fix_implementation`** overwrites `@implementation`; otherwise the branch is skipped.
5. **`GENERATE generate_tests`** — test suite into `@tests`, using the final (possibly fixed) `@implementation`.
6. **`GENERATE verify_test_syntax`** — syntax sanity check into `@syntax_ok` (informational).
7. **`GENERATE assemble_output`** — final merged artifact into `@final_output`.
8. **`RETURN @final_output WITH status = 'complete'`** — normal exit with language and framework metadata.
9. **`EXCEPTION WHEN GenerationError`** — if any GENERATE call raises, return `@implementation` with `status = 'implementation_only'` and `reason = 'test_generation_failed'`.

There is no WHILE loop; the fix pass is a single conditional detour, not a retry cycle.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (use Section 1 or Section 2 as text2spl input)
spl3 text2spl \
  --description "Generate a language-idiomatic function implementation together with its unit test suite from a plain-text specification, with an automatic self-review and fix pass between the two generation steps. Accept the spec as inline text or a file path. Resolve conventions and framework rules via CREATE FUNCTION templates. Use GENERATE implement_function, then GENERATE review_implementation, then EVALUATE to branch on sentinel keywords (issue, error, problem) — if found, GENERATE fix_implementation to rewrite the code. Then GENERATE generate_tests against the final implementation, GENERATE verify_test_syntax as a static check, and GENERATE assemble_output to produce the merged artifact. RETURN with status='complete'; on GenerationError, fall back to RETURN with status='implementation_only'." \
  --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```