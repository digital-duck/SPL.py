## Summary

This is a minimal "Hello World" SPL program that takes a user input string and a target language, then generates a friendly AI response in that language. It exists to demonstrate the two core SPL primitives — `CREATE FUNCTION` and `GENERATE` — in their simplest form. Developers learning SPL or scaffolding a new project use it as a starting point.

---

## Detailed Specification

### 1. Purpose

Accepts a natural-language input and an optional response language, then generates a contextually appropriate reply from a friendly AI assistant.

### 2. High-level Description

This implementation defines a single reusable prompt template via `CREATE FUNCTION greeting`, which accepts two parameters — `user_input` (defaulting to `"Explain SQL"`) and `lang` (defaulting to `"English"`) — and instructs the model to respond to the user's message in the specified language. The `PROMPT hello_world` block acts as the orchestration entry point: it establishes a system role via `system_role('You are a friendly assistant.')`, binds `context.user_input` and `context.lang` into the function's parameter slots, and issues a `GENERATE` call that invokes `greeting(user_input, lang)` to produce the model's response. There is no looping, branching, or exception handling — execution is strictly linear: bind inputs, call the model once, return the result. The design intentionally keeps the surface area minimal so the pattern of `CREATE FUNCTION` → `PROMPT` → `GENERATE` is immediately legible to a newcomer.

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `CREATE FUNCTION greeting(...)` | `CREATE FUNCTION <name>` | Defines a reusable prompt template with `{param}` slots; default values provided for both params |
| `PROMPT hello_world` | `WORKFLOW <name>` | Entry-point block that wires context into the function and triggers generation |
| `system_role(...)` | System prompt injection | Sets the assistant persona for the model call |
| `context.user_input`, `context.lang` | `@<var>` shared state | Runtime context values bound into the function's parameter slots |
| `GENERATE greeting(user_input, lang)` | `GENERATE <fn>(...) INTO @<var>` | Single LLM call; result is the workflow's output |

### 4. Logical Functions / Prompts

**`greeting`**
- **Role:** The sole prompt template; formats the model's instruction to reply to a user message in a specified language.
- **Key prompt conventions:**
  - Uses `{user_input}` and `{lang}` as interpolation slots.
  - Opens with a persona declaration (`You are an AI assistant.`) to anchor the model's behavior.
  - No sentinel tokens, scoring rubrics, or structured output format — free-text reply is the expected output.
  - Both parameters carry defaults (`"Explain SQL"` / `"English"`), making the function self-contained for testing without any runtime context.

### 5. Control Flow

```
START
  └─ PROMPT hello_world
       ├─ bind system_role("You are a friendly assistant.")
       ├─ bind user_input ← context.user_input
       ├─ bind lang       ← context.lang
       └─ GENERATE greeting(user_input, lang)
            └─ return model response
END
```

Execution is fully linear — one LLM call, no WHILE loop, no EVALUATE branch, no EXCEPTION handler. The result of `GENERATE` is the terminal output.

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "Accepts a natural-language user_input and an optional \
response language (lang), then generates a friendly AI reply using a single \
CREATE FUNCTION greeting with both parameters defaulted. A PROMPT block sets the \
system role, binds context variables into the function slots, and issues one \
GENERATE call. No looping, branching, or exception handling." --mode workflow

# Step 2 — compile to any target
spl3 splc compile hello_world.spl --lang python/pocketflow
spl3 splc compile hello_world.spl --lang python/langgraph
spl3 splc compile hello_world.spl --lang go
```