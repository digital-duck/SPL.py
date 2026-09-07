## Summary

This workflow takes a natural-language description of a function (or a path to a spec file) and produces both a complete implementation and a matching unit test suite in the requested programming language. It includes a built-in self-review step that detects and fixes problems before generating tests, ensuring higher-quality output. Developers and teams that want to bootstrap well-tested code from specs without manual scaffolding benefit most.

---

## Detailed Specification

### 1. Purpose

Generate a language-idiomatic function implementation together with a complete unit test suite from a plain-language specification, with an automated self-review and fix pass before tests are produced.

---

### 2. High-level Description

The `code_gen_with_tests` WORKFLOW accepts a function specification (either inline text or a file path), a target programming language, and an optional test framework name. It begins by invoking a `load_spec` CALL to resolve any file-path input into raw text. Two scalar helper functions — `language_conventions` and `test_framework_guide` — are defined as CREATE FUNCTIONs that return style-guide strings via CASE expressions; these strings are injected as context into subsequent LLM calls rather than being LLM calls themselves.

The core pipeline has six sequential GENERATE steps: `implement_function` produces the initial code using the spec and language conventions; `review_implementation` critically evaluates that code against the original spec; an EVALUATE block conditionally triggers `fix_implementation` if the review output contains the tokens "issue", "error", or "problem", otherwise skips refinement; `generate_tests` creates a test suite targeting the (possibly revised) implementation using the framework guide; `verify_test_syntax` performs a static syntax check on the generated tests; and `assemble_output` combines implementation and tests into a single formatted artifact. The WORKFLOW terminates with RETURN carrying `status='complete'` along with the language and framework metadata. An EXCEPTION handler for `GenerationError` catches failures in the test-generation phase and returns whatever implementation was produced, with `status='implementation_only'`.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW code_gen_with_tests` | `WORKFLOW` | Top-level orchestration; declares INPUT/OUTPUT vars |
| `CREATE FUNCTION language_conventions` | `CREATE FUNCTION` | Pure CASE lookup — not an LLM call; returns style guide string |
| `CREATE FUNCTION test_framework_guide` | `CREATE FUNCTION` | Pure CASE lookup on composite `language:framework` key |
| `CALL load_spec(@spec)` | `CALL` | Side-effect tool call; resolves file path → text, overwrites `@spec` |
| `GENERATE implement_function(...)` | `GENERATE` | LLM call; injects spec + conventions |
| `GENERATE review_implementation(...)` | `GENERATE` | LLM call; produces `@review_notes` |
| `EVALUATE @review_notes WHEN contains(...)` | `EVALUATE` | Branch: triggers fix GENERATE or skips |
| `GENERATE fix_implementation(...)` | `GENERATE` | Conditional LLM call inside EVALUATE THEN branch |
| `GENERATE generate_tests(...)` | `GENERATE` | LLM call; uses framework guide as context |
| `GENERATE verify_test_syntax(...)` | `GENERATE` | LLM call; static syntax check |
| `GENERATE assemble_output(...)` | `GENERATE` | LLM call; merges implementation + tests |
| `@spec, @language, @implementation, @tests, @review_notes, @syntax_ok, @final_output` | `@vars` | Shared mutable state across all steps |
| `RETURN @final_output WITH status='complete'` | `RETURN` | Non-trivial: carries metadata consumed by callers |
| `RETURN @implementation WITH status='implementation_only'` | `RETURN` | Non-trivial: degraded-mode exit from exception handler |
| `EXCEPTION WHEN GenerationError` | `EXCEPTION` | Catches test-generation failures; returns partial result |

---

### 4. Logical Functions / Prompts

**`language_conventions(language TEXT)`**
- Role: configuration helper — not an LLM call
- Provides language-specific style rules (PEP 8, Go idioms, strict TypeScript, idiomatic Rust, or a generic fallback) as a string injected into `implement_function`
- Key convention: CASE on language name; falls back to generic clean-code guidance

**`test_framework_guide(language TEXT, framework TEXT)`**
- Role: configuration helper — not an LLM call
- Returns framework-specific testing guidance (pytest fixtures, unittest.TestCase, Go table-driven tests, Jest mocks) keyed on a composite `language:framework` string
- Default value `'default'` causes the ELSE branch to fire, producing generic guidance

**`implement_function`**
- Role: primary code generator
- Inputs: resolved spec text, language name, style conventions string
- Expected output: a complete, runnable function in the target language following the provided conventions

**`review_implementation`**
- Role: self-critic — evaluates the generated code against the original spec
- Inputs: generated implementation, original spec, language
- Output: free-text review notes; the EVALUATE step watches for sentinel tokens `"issue"`, `"error"`, `"problem"` to decide whether refinement is needed

**`fix_implementation`**
- Role: conditional refiner — only invoked when review notes contain a problem sentinel
- Inputs: current implementation, review notes, language
- Output: revised implementation that replaces `@implementation` in-place

**`generate_tests`**
- Role: test suite generator
- Inputs: (refined) implementation, original spec, language, framework guide string
- Expected output: a complete test file covering happy path, edge cases, and error cases per the framework guide

**`verify_test_syntax`**
- Role: static validator — checks that generated tests are parseable/compilable
- Inputs: generated tests, language
- Output: `@syntax_ok` text; result is logged but does not currently gate further steps

**`assemble_output`**
- Role: formatter — combines implementation and tests into the final deliverable
- Inputs: implementation, tests, language
- Output: `@final_output` — the single artifact returned to the caller

---

### 5. Control Flow

```
load_spec(@spec)                          ← CALL (side-effect, resolves file paths)
    │
    ▼
implement_function(...)                   ← GENERATE → @implementation
    │
    ▼
review_implementation(...)                ← GENERATE → @review_notes
    │
    ▼
EVALUATE @review_notes
  WHEN contains('issue|error|problem')
    ├── TRUE  → fix_implementation(...)   ← GENERATE → @implementation (overwritten)
    └── FALSE → skip
    │
    ▼
generate_tests(...)                       ← GENERATE → @tests
    │
    ▼
verify_test_syntax(...)                   ← GENERATE → @syntax_ok (logged only)
    │
    ▼
assemble_output(...)                      ← GENERATE → @final_output
    │
    ▼
RETURN @final_output WITH status='complete', language=..., test_framework=...

── EXCEPTION path ──────────────────────────────────────────────────────────
GenerationError → RETURN @implementation WITH status='implementation_only',
                                              reason='test_generation_failed'
```

There is no WHILE loop; the fix step executes at most once. The EVALUATE branch is the only conditional control-flow decision. The EXCEPTION handler provides a single fallback exit for test-generation failures.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (paste Section 2 as the description)
spl3 text2spl --description "Generate a language-idiomatic function implementation \
  together with a complete unit test suite from a plain-language specification, with \
  an automated self-review and fix pass before tests are produced. The workflow \
  accepts a spec (inline text or file path), target language, and optional test \
  framework. It calls load_spec to resolve file paths, then sequentially calls \
  implement_function (with language conventions injected), review_implementation, \
  conditionally fix_implementation via EVALUATE on sentinel tokens, generate_tests \
  (with framework guide injected), verify_test_syntax, and assemble_output. \
  It returns status='complete' with metadata, or status='implementation_only' \
  on GenerationError." \
  --mode workflow

# Step 2 — compile to any target
spl3 splc compile code_gen_with_tests.spl --lang python/pocketflow
spl3 splc compile code_gen_with_tests.spl --lang python/langgraph
spl3 splc compile code_gen_with_tests.spl --lang go
```