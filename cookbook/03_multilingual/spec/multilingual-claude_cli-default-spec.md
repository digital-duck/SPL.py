## Summary

Multilingual Greeting is a single-step SPL workflow that accepts a user message and a list of target languages, then produces a translated greeting in each language. It demonstrates how SPL's parametric context works when a function argument is a list rather than a scalar. Non-technical stakeholders can think of it as a "translate and greet" button that works for any combination of languages in one call.

---

## Detailed Specification

### 1. Purpose

Accept a user-supplied message and an ordered list of target languages, then produce a single LLM response that renders the message in every requested language simultaneously.

### 2. High-level Description

This workflow uses a single CREATE FUNCTION named `greeting` whose prompt instructs the model to act as a friendly assistant and translate the caller's message into every language supplied via the `lang` parameter. The function signature declares `input` as TEXT (defaulting to `"hello"`) and `lang` as a List (defaulting to `["Chinese", "English"]`), making both parameters optional at the call site. A PROMPT block named `multilingual_greeting` binds runtime context — `context.user_input` into `input` and `context.lang` into `lang` — before issuing a GENERATE call to `greeting`. Because translation of all languages is collapsed into one LLM call rather than one call per language, there is no WHILE loop and no EVALUATE branch; control flow is strictly linear. The workflow has no file-write or HTTP side-effects and no EXCEPTION handlers, relying on the SPL runtime's default error propagation. The intended execution target is an Ollama-backed adapter, though the SPL is adapter-agnostic.

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW <name>` | Implicit — scoped to the `PROMPT multilingual_greeting` block | No explicit `WORKFLOW` keyword; the named PROMPT acts as the workflow entry point |
| `CREATE FUNCTION <name>` | `CREATE FUNCTION greeting(input TEXT, lang List)` | Defines the reusable prompt template with `{input}` and `{lang}` slots |
| `GENERATE <fn>(…) INTO @<var>` | `GENERATE greeting(input, lang)` | Single LLM call; result is the workflow output (no explicit `INTO` variable shown) |
| Shared state (`@vars`) | `context.user_input`, `context.lang` | Runtime context bindings injected into the PROMPT SELECT clause |
| `WHILE … DO … END` | *(absent)* | No looping — single-shot generation |
| `EVALUATE … WHEN … THEN … ELSE … END` | *(absent)* | No branching on LLM output |
| `EXCEPTION WHEN <Type> THEN …` | *(absent)* | No explicit error handling; runtime defaults apply |

### 4. Logical Functions / Prompts

**`greeting`**
- **Role:** The sole prompt template in the workflow. Sets the model persona ("friendly assistant"), passes the original user message, and instructs the model to translate it into every language in the `lang` list within a single response.
- **Key prompt conventions:**
  - Uses `{input}` and `{lang}` interpolation slots matching the function parameter names.
  - `lang` is a List, so the model receives the full list and is expected to produce one translation per element without explicit iteration in SPL.
  - No sentinel tokens, scoring rubrics, or structured output format are specified — free-form multilingual text is the expected output.

### 5. Control Flow

1. **Entry:** The `multilingual_greeting` PROMPT block is invoked with `user_input` and `lang` from the runtime context.
2. **Binding:** The SELECT clause maps `context.user_input → input` and `context.lang → lang`.
3. **Generation:** A single GENERATE call executes `greeting(input, lang)` against the configured LLM adapter.
4. **Termination:** The LLM response is returned as the workflow result. There are no loops, branches, or retries.

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Accept a user-supplied message and an ordered list of target languages, then produce a single LLM response that renders the message in every requested language simultaneously." --mode workflow

# Step 2 — compile to any target
spl3 splc compile multilingual_greeting.spl --lang python/pocketflow
spl3 splc compile multilingual_greeting.spl --lang python/langgraph
spl3 splc compile multilingual_greeting.spl --lang go
```