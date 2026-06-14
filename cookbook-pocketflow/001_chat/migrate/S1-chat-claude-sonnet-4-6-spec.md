## Summary

This is a terminal-based multi-turn chat application that keeps the LLM contextually aware by maintaining a rolling conversation history. A single self-looping node collects user input, calls the LLM with the last *N* messages, appends the reply, and repeats until the user types an exit keyword. It serves as the minimal PocketFlow pattern for any stateful conversational agent.

---

## Detailed Specification

### 1. Purpose

Deliver an interactive terminal chat session backed by an LLM, where each response is conditioned on a sliding window of recent conversation turns.

---

### 2. High-level Description

The workflow is implemented as a single `WORKFLOW chat` that loops via a `WHILE` construct until an exit condition is met. On each iteration, the workflow reads a line of user input; if the input matches an exit keyword (`exit`, `bye`, `quit`), the loop terminates with `RETURN @response WITH status="done"`. Otherwise, the user message is appended to a shared `@messages` list, and a `GENERATE chat_turn(@messages[-num_msg:]) INTO @response` call dispatches the sliding-window history to the LLM, producing a reply. The assistant reply is then appended to `@messages` so future turns inherit full context. The sliding window is controlled by a `num_msg` parameter (default 5), keeping token cost bounded while preserving short-term coherence. No `EVALUATE` branch on LLM output is needed because the only branching decision is the user-input exit check, which is a deterministic string match rather than a semantic judgment. There is no explicit `EXCEPTION` handler in this implementation; LLM errors would propagate uncaught.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW chat` | `Flow(start=chat_node)` + `ChatNode` class | The single node plus its self-loop define the whole workflow |
| `WHILE user_input not in exit_keywords DO` | `chat_node - "continue" >> chat_node` self-loop; `post()` returns `"continue"` to re-enter | Loop continues while user stays in session |
| `GENERATE chat_turn(...) INTO @response` | `call_llm(messages)` inside `exec()` | Dispatches last `num_msg` messages to LLM |
| `@messages` (shared state) | `shared["messages"]` list | Accumulates full history; both user and assistant turns |
| `@num_msg` (shared param) | `shared["num_msg"]` (default `2*NUM_MSG+1 = 5`) | Sliding-window size passed in at flow start |
| `RETURN @response WITH status="done"` | `post()` returns `None` when prep detects exit keyword | Non-default status that terminates the loop |

---

### 4. Logical Functions / Prompts

**`chat_turn` (inline message array)**

- **Role:** The sole LLM call in the workflow; produces the assistant's reply for one turn.
- **Input format:** A JSON-serialisable list of `{"role": "user"|"assistant", "content": "..."}` dicts — the last `num_msg` entries from `@messages`.
- **Output format:** Plain text assistant reply; no sentinel tokens or scoring.
- **Key convention:** The sliding window (`messages[-num_msg:]`) is sliced in `prep()` before being passed to `exec()`, so the LLM never sees the full unbounded history — only the most recent 5 turns by default.

---

### 5. Control Flow

```
START
  ↓
Initialize @messages = [] on first run
  ↓
┌─────────────────────────────────────────────────────┐
│ WHILE true DO                                       │
│   Read user_input from stdin                        │
│   IF user_input ∈ {exit, bye, quit}                 │
│       RETURN WITH status="done"  ← terminates loop  │
│   Append {role:user, content:user_input} → @messages│
│   GENERATE chat_turn(@messages[-num_msg:])          │
│       INTO @response                                │
│   Print @response to stdout                         │
│   Append {role:assistant, content:@response}        │
│       → @messages                                   │
│   CONTINUE  ← loop back                            │
└─────────────────────────────────────────────────────┘
```

Termination is driven by the user typing an exit keyword; only then does the workflow emit `status="done"` and halt.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (paste Section 2 as the description)
spl3 text2spl --description "The workflow is implemented as a single WORKFLOW chat \
that loops via a WHILE construct until an exit condition is met. On each iteration, \
the workflow reads a line of user input; if the input matches an exit keyword (exit, \
bye, quit), the loop terminates with RETURN @response WITH status=done. Otherwise, \
the user message is appended to a shared @messages list, and a GENERATE chat_turn \
call dispatches the sliding-window history to the LLM. The assistant reply is \
appended to @messages. The window size num_msg (default 5) keeps token cost bounded." \
--mode workflow

# Step 2 — compile to any target
spl3 splc compile chat.spl --lang python/pocketflow
spl3 splc compile chat.spl --lang python/langgraph
spl3 splc compile chat.spl --lang go
```