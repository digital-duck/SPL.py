## Summary

Multilingual Greeting is a single-step LLM workflow that translates or reformulates a user-provided message into one or more target languages. It exists to demonstrate how SPL parameterizes context — injecting both free-text input and a configurable language list into a single prompt call. Non-technical users, educators, and developers exploring SPL basics benefit from its simplicity.

---

## Detailed Specification

### 1. Purpose

Translate a user-supplied message into one or more specified languages via a single parameterized LLM call.

### 2. High-level Description

This workflow uses a single `CREATE FUNCTION` named `greeting` that accepts a text input and a list of target languages, embedding both into a prompt that instructs the LLM to act as a friendly assistant and produce translations. A `PROMPT` block named `multilingual_greeting` binds runtime context variables (`context.user_input` and `context.lang`) to the function's parameters and issues one `GENERATE` call to produce the result. There is no iterative refinement, no branching, and no exception handling — the workflow is a pure linear single-shot pattern intended as a pedagogical demonstration of parametric context injection in SPL. The language list parameter accepts any number of target languages, making the workflow trivially reusable across localization scenarios without modifying the prompt template. Output is returned directly from the single LLM generation with no post-processing or storage side-effects.

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `CREATE FUNCTION greeting(...)` | `CREATE FUNCTION` | Defines a reusable prompt template with `{input}` and `{lang}` slots |
| `PROMPT multilingual_greeting` | `WORKFLOW` (single-step) | Declares the named execution unit; no sub-workflows or `CALL` |
| `GENERATE greeting(input, lang)` | `GENERATE <fn>(...) INTO @<var>` | Single LLM call; result is the workflow's terminal output |
| `context.user_input`, `context.lang` | SPL `@vars` | Runtime-bound context variables injected from CLI `--param` flags |
| `lang List` parameter | typed parameter slot | Accepts a Python list literal; rendered inline into the prompt |

### 4. Logical Functions / Prompts

**`greeting`**
- **Role:** The sole prompt template; drives the entire workflow.
- **Prompt conventions:**
  - System persona set inline: *"You are a friendly assistant."*
  - `{input}` slot receives the raw user message verbatim.
  - `{lang}` slot receives a list (e.g. `['Chinese', 'English']`); the LLM is expected to produce one translation per listed language.
  - No sentinel tokens, scoring rubrics, or structured output format are specified — the model is free to format multi-language output naturally.
  - Default values (`input = 'hello'`, `lang = ['Chinese', 'English']`) allow the function to run without CLI overrides.

### 5. Control Flow

Execution is strictly linear and single-pass:

1. The `PROMPT multilingual_greeting` block resolves `context.user_input` and `context.lang` from the runtime context.
2. A single `GENERATE greeting(input, lang)` call is issued to the configured LLM adapter.
3. The LLM response is returned as the workflow output.

There are no `WHILE` loops, no `EVALUATE` branches, no `EXCEPTION` handlers, and no `RETURN WITH status=` declarations. This is the minimal SPL pattern: one function, one generation, one result.

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Translate a user-supplied message into one or more specified languages via a single parameterized LLM call, using a reusable prompt function that accepts a text input and a language list and instructs the model to act as a friendly assistant producing translations for each listed language." --mode workflow

# Step 2 — compile to any target
spl3 splc compile multilingual_greeting.spl --lang python/pocketflow
spl3 splc compile multilingual_greeting.spl --lang python/langgraph
spl3 splc compile multilingual_greeting.spl --lang go
```