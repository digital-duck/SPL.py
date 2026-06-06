## Summary

Ollama Proxy is a minimal, general-purpose LLM gateway that forwards any user-supplied prompt to any configured adapter and model, then returns the response. It exists to provide a single, reusable entry point for ad-hoc LLM queries without workflow logic or post-processing. Developers and power users benefit by being able to swap backends (Ollama, Anthropic, etc.) at runtime without changing the prompt code.

---

## Detailed Specification

### 1. Purpose

Forward a user-supplied free-text prompt to a configurable LLM adapter/model and return the raw response.

### 2. High-level Description

This implementation defines a single-step WORKFLOW using the Ollama Proxy pattern: a CREATE FUNCTION named `answer` accepts a `prompt` text parameter and passes it through unchanged as the LLM instruction. The PROMPT block `ollama_proxy` sets a fixed system role ("You are a helpful, knowledgeable assistant.") and binds `context.prompt` as the user input. A single GENERATE call invokes `answer(prompt)` against the runtime-selected adapter and model, storing the LLM response. There is no looping, branching, or side-effect tooling — the workflow is intentionally stateless and transparent. The adapter and model are injected at invocation time via CLI flags (`--adapter`, `--model`), making this a true runtime-configurable proxy rather than a hardcoded integration.

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW` | `PROMPT ollama_proxy` | Single-prompt workflow; no multi-step orchestration |
| `CREATE FUNCTION answer(prompt TEXT)` | `CREATE FUNCTION` | Identity template — passes prompt through verbatim |
| `system_role(...)` | System message injection | Fixed persona: "helpful, knowledgeable assistant" |
| `context.prompt` | Runtime parameter binding | Supplied via `--prompt` CLI argument |
| `GENERATE answer(prompt)` | `GENERATE` | Single LLM call; result is the final output |

### 4. Logical Functions / Prompts

**`answer(prompt TEXT)`**
- **Role:** Identity pass-through template. Wraps the raw user prompt with no additional framing, instructions, or output format constraints.
- **Key conventions:** No sentinel tokens, no scoring, no structured output format. The template body is exactly `{prompt}` — whatever the user supplies becomes the full LLM instruction.

**`ollama_proxy` (PROMPT block)**
- **Role:** Execution context. Attaches the system persona and routes `context.prompt` into the `answer` function for generation.
- **Key conventions:** System role is static and generic. No chain-of-thought, no few-shot examples, no output schema enforcement.

### 5. Control Flow

Execution is strictly linear with no branching or looping:

1. Runtime binds `context.prompt` from the CLI `--prompt` argument.
2. `ollama_proxy` sets the system role and invokes GENERATE `answer(prompt)`.
3. The LLM response is returned directly as output.

There are no WHILE loops, EVALUATE branches, or non-trivial RETURN status tokens. Termination is immediate after the single GENERATE call.

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Forward a user-supplied free-text prompt to a configurable LLM adapter/model and return the raw response. Use a single CREATE FUNCTION named answer that passes the prompt through verbatim. Set a fixed system role of 'You are a helpful, knowledgeable assistant.' and bind the user input from context.prompt. Use a single GENERATE call with no looping, branching, or side effects. The adapter and model are injected at runtime." --mode workflow

# Step 2 — compile to any target
spl3 splc compile ollama_proxy.spl --lang python/pocketflow
spl3 splc compile ollama_proxy.spl --lang python/langgraph
spl3 splc compile ollama_proxy.spl --lang go
```