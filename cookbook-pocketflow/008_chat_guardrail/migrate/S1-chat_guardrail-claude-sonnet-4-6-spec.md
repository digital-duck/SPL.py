## Summary

This is a travel-focused conversational chatbot that enforces topic guardrails before answering user queries. It validates every user message — first with simple heuristics, then with an LLM judge — and rejects anything unrelated to travel before forwarding valid queries to a travel-advisor LLM. Non-technical stakeholders benefit from a focused, on-topic customer experience without manual moderation.

---

## Detailed Specification

### 1. Purpose

Provide an interactive, multi-turn travel-advisor chat that silently enforces topic relevance through an LLM-powered guardrail before answering any user query.

---

### 2. High-level Description

This workflow implements a **guardrail-gated multi-turn chat** pattern using three cooperating logical functions. The conversation runs as an unbounded WHILE loop anchored at user input: each iteration collects a query, validates it, and either rejects it or answers it. A `UserInputNode` function reads from stdin and holds shared conversation history in `@messages`; if the user types `exit`, the loop terminates with an implicit RETURN. A `GuardrailNode` function first applies deterministic checks (empty or too-short strings), then issues a GENERATE call to an LLM judge whose output is parsed as YAML with `valid: true/false` and `reason:` fields; an EVALUATE on the `valid` flag either routes to RETURN WITH `status=retry` (loops back to input, prints rejection message) or RETURN WITH `status=process` (advances to the answer node). The `LLMNode` function injects a system prompt declaring the travel-advisor persona on the first turn, then issues a GENERATE call over the full `@messages` history, appends the assistant reply to `@messages`, and returns WITH `status=continue` to restart the loop. EXCEPTION handling covers malformed YAML from the guardrail LLM via assertion guards. The adapter is OpenAI GPT-4o (shimmed to any SPL-compatible adapter via `SPL_ADAPTER` / `SPL_MODEL` env vars), and all inter-node state flows through a single shared `@messages` list.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW chat_with_guardrail` | `Flow(start=user_input_node)` + `flow.run(shared)` | Top-level orchestration object |
| `CREATE FUNCTION guardrail_prompt` | Inline f-string in `GuardrailNode.exec()` | YAML-format evaluation prompt |
| `CREATE FUNCTION travel_advisor_system` | Hard-coded string in `LLMNode.prep()` | System persona injected on first turn |
| `GENERATE guardrail_prompt(...) INTO @validation` | `call_llm(messages)` in `GuardrailNode.exec()` | Returns YAML block; parsed with `yaml.safe_load` |
| `GENERATE travel_advisor(...) INTO @reply` | `call_llm(messages)` in `LLMNode.exec()` | Full conversation history passed as context |
| `EVALUATE @validation WHEN valid=true THEN ... ELSE ...` | `if not is_valid: return "retry"` / `return "process"` in `GuardrailNode.post()` | Binary branch on LLM judge verdict |
| `WHILE user_input != 'exit' DO ... END` | `user_input_node - "continue" >> user_input_node` cycle in Flow | Loop terminates when `UserInputNode.post()` returns `None` |
| `RETURN WITH status='retry'` | `return "retry"` in `GuardrailNode.post()` | Routes back to `UserInputNode`; rejection printed inline |
| `RETURN WITH status='process'` | `return "process"` in `GuardrailNode.post()` | Advances to `LLMNode` after appending user turn to `@messages` |
| `RETURN WITH status='continue'` | `return "continue"` in `LLMNode.post()` | Loops back to `UserInputNode` to accept next query |
| `@messages` (shared variable) | `shared["messages"]` dict key | Accumulates full conversation history across loop iterations |
| `@user_input` (shared variable) | `shared["user_input"]` dict key | Passes raw text from input node to guardrail node |
| `EXCEPTION WHEN ParseError THEN ...` | `assert result is not None` / `assert "valid" in result` in `GuardrailNode.exec()` | Guards against malformed YAML from guardrail LLM |

---

### 4. Logical Functions / Prompts

**`guardrail_prompt`**
- **Role:** Topic classifier / input validator. Acts as a gatekeeper before any travel-advisor call is made.
- **Key conventions:**
  - Instructs the LLM to evaluate whether the user query relates to travel advice, destinations, planning, or travel topics.
  - Output format is a YAML fenced block with exactly two keys: `valid: true/false` and `reason: <explanation>`.
  - The `reason` value is surfaced directly to the user as the rejection message when `valid: false`.
  - Sentinel pattern: extracts content between ` ```yaml ` and ` ``` ` delimiters before parsing.

**`travel_advisor_system`**
- **Role:** Persona declaration for the answer LLM. Defines scope and style of responses.
- **Key conventions:**
  - Injected once as a `system` role message into `@messages` on the first turn (guarded by `any(msg["role"] == "system" ...)`).
  - Constrains the assistant to travel-related topics only and caps response length at ~100 words.
  - Uses the full accumulated `@messages` list to maintain multi-turn conversational context.

---

### 5. Control Flow

```
START
  └─► UserInputNode
        ├── [exit typed]  → print farewell → TERMINATE
        └── [query entered] → store in @user_input → RETURN validate
              └─► GuardrailNode
                    ├── [empty / too short]       → print error  → RETURN retry → UserInputNode
                    ├── [LLM judge: valid=false]  → print reason → RETURN retry → UserInputNode
                    └── [LLM judge: valid=true]   → append to @messages → RETURN process
                          └─► LLMNode
                                └── GENERATE over @messages → append reply → RETURN continue
                                      └─► UserInputNode  (next iteration)
```

The WHILE condition is `user_input.lower() != 'exit'` evaluated implicitly at `UserInputNode.post()`. The `retry` branch is a partial loop that bypasses `LLMNode` and re-enters `UserInputNode` without modifying `@messages`. The `continue` branch is the normal loop back after a successful answer. Loop depth is unbounded; termination is user-driven.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (use Section 2 above as text2spl input)
spl3 text2spl --description "Provide an interactive, multi-turn travel-advisor chat that enforces topic relevance through an LLM-powered guardrail before answering any user query. The workflow runs as an unbounded WHILE loop. A guardrail function applies heuristic checks then issues a GENERATE call returning YAML with valid and reason fields; EVALUATE on the valid flag returns status=retry to loop back or status=process to advance. An LLM answer function injects a travel-advisor system prompt on the first turn, GENERATEs over full @messages history, and returns status=continue to restart. EXCEPTION handling covers malformed guardrail YAML. Shared state: @messages accumulates conversation history, @user_input holds the current raw query." --mode workflow

# Step 2 — compile to any target
spl3 splc compile travel_advisor_chat.spl --lang python/pocketflow
spl3 splc compile travel_advisor_chat.spl --lang python/langgraph
spl3 splc compile travel_advisor_chat.spl --lang go
```