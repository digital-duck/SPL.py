## Summary

Ollama Proxy is a minimal, universal LLM passthrough workflow that forwards any user-supplied prompt to any configured adapter and model, then returns the raw response. It exists to provide a single, adapter-agnostic entry point for one-shot LLM queries without any orchestration overhead. Developers, testers, and non-technical users benefit by being able to invoke any locally-running or cloud-hosted model through a single consistent interface.

---

## Detailed Specification

### 1. Purpose

Route a single user-provided prompt to any LLM adapter/model combination and return the generated response verbatim.

---

### 2. High-level Description

The workflow implements the simplest possible SPL pattern: a single PROMPT block that wraps one CREATE FUNCTION definition and issues one GENERATE call. The `answer` function is a pass-through prompt template that injects the user-supplied `{prompt}` text with no transformation or added structure. A fixed system role (`You are a helpful, knowledgeable assistant.`) is applied at the PROMPT level to give the model a stable behavioral baseline. Because all adapter and model selection is deferred to runtime flags (`--adapter`, `--model`), the `.spl` source is fully adapter-agnostic and works identically against Ollama, Anthropic, OpenRouter, Momagrid, or any other registered adapter. There is no WHILE loop, no EVALUATE branch, no CALL to external tools, and no EXCEPTION handler — the workflow is intentionally stateless and terminates after the single GENERATE step.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `PROMPT ollama_proxy` | `WORKFLOW ollama_proxy` | Top-level named execution unit; `PROMPT` is the v2 single-step shorthand |
| `CREATE FUNCTION answer(prompt TEXT)` | `CREATE FUNCTION answer` | Reusable prompt template with one `{prompt}` slot; body is the raw template string |
| `GENERATE answer(prompt)` | `GENERATE answer(prompt) INTO @result` | Single LLM call; result is the workflow's implicit output |
| `system_role(...)` | System message binding | Passed to the adapter as the `system` argument on every call |
| `context.prompt` | `INPUT: prompt TEXT` | Runtime parameter injected via `--param prompt=...` |

---

### 4. Logical Functions / Prompts

**`answer`**
- **Role:** The sole prompt template; acts as a transparent relay between the caller and the LLM.
- **Key conventions:**
  - Body is a single `{prompt}` interpolation — no prefix, no suffix, no sentinel tokens.
  - No scoring, no structured output format, no JSON envelope — the model's raw text is the final result.
  - The simplicity is intentional: this function is a baseline/diagnostic tool, not a task-specific prompt.

---

### 5. Control Flow

```
START
  └─ Bind context.prompt from --param flag
  └─ Apply system_role to adapter call
  └─ GENERATE answer(prompt)   ← single LLM call
  └─ Return generated text
END
```

Execution is strictly linear. There is no branching, no iteration, and no conditional logic. The workflow completes after exactly one LLM call.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl \
  --description "Route a single user-provided prompt to any LLM adapter/model combination and return the generated response verbatim. Use a single CREATE FUNCTION with a bare {prompt} slot, a fixed system role of 'You are a helpful, knowledgeable assistant.', and one GENERATE call. No loops, no branches, no tool calls." \
  --mode workflow

# Step 2 — compile to any target
spl3 splc compile output.spl --lang python/pocketflow
spl3 splc compile output.spl --lang python/langgraph
spl3 splc compile output.spl --lang go
```