## Summary

This workflow implements a stateful conversational agent that remembers personal facts about the user across sessions using a persistent SQLite memory store. Each turn, it extracts any new facts from the user's message, merges them into a running profile, and answers using the full context of known facts and recent conversation history. Non-technical stakeholders can think of it as a chatbot that genuinely "knows" the user — accumulating knowledge turn by turn without re-reading the whole conversation each time.

---

## Detailed Specification

### 1. Purpose

Provide a memory-augmented single-turn conversation handler that loads, updates, and persists a user profile and chat history so that each LLM response is grounded in everything the user has shared across all prior sessions.

---

### 2. High-level Description

The `memory_conversation` WORKFLOW implements a single-turn, stateful conversational agent using a **Retrieve → Extract → Conditional Update → Respond → Persist** pattern. It takes two inputs: `@user_input` (TEXT) and `@memory` (a STORAGE-typed SQLite backend injected at call time), which act as the live context store for two named slots — `chat_user_profile` and `chat_history`.

At the start of each turn, the workflow reads the persisted profile and history from the injected storage backend into `@profile` and `@chat_history`. It then calls GENERATE with `extract_facts`, a prompt function that reads the raw user message and either returns the exact sentinel string `no_new_facts` or a bullet list of newly disclosed personal facts. An EVALUATE branch checks that sentinel: if facts were found, GENERATE calls `merge_profile` to fold them into the existing profile and immediately writes the result back to persistent storage; otherwise the profile is left unchanged. A third GENERATE call — `contextual_reply` — synthesises the final response from the combined profile, history, and current input, explicitly instructing the model to respond with `"I don't have that in memory."` when a requested fact is absent. After the LLM responds, history is appended deterministically and CALL `trim_turns` enforces a 10-turn rolling window at zero LLM cost before the updated history is written back to storage. The workflow terminates with RETURN `@response` WITH `status='complete'`, or — via an EXCEPTION handler — with a graceful fallback message and `status='budget_limit'` if a `BudgetExceeded` error is raised.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW memory_conversation` | `WORKFLOW` | Declares the named orchestration entry point |
| `INPUT @memory STORAGE(sqlite, ...)` | `WORKFLOW` input typed `STORAGE` | Memory backend is a first-class declared input, overridable at call time |
| `CREATE FUNCTION extract_facts` | `CREATE FUNCTION` | Prompt template with `{user_input}` slot; returns sentinel or bullet list |
| `CREATE FUNCTION merge_profile` | `CREATE FUNCTION` | Prompt template with `{existing_profile}` and `{new_facts}` slots |
| `CREATE FUNCTION contextual_reply` | `CREATE FUNCTION` | Prompt template with `{user_input}`, `{profile}`, `{history}` slots |
| `GENERATE extract_facts(...) INTO @new_facts` | `GENERATE` | LLM call; result stored in `@new_facts` |
| `GENERATE merge_profile(...) INTO @profile` | `GENERATE` | LLM call inside the EVALUATE branch; conditionally executed |
| `GENERATE contextual_reply(...) INTO @response` | `GENERATE` | Primary response generation |
| `EVALUATE @new_facts WHEN = 'no_new_facts'` | `EVALUATE` | Branches on exact sentinel string match |
| `CALL trim_turns(@chat_history, '10') INTO @chat_history` | `CALL` | Deterministic tool call (no LLM); enforces 10-turn window |
| `@memory['chat_user_profile'] := @profile` | `CALL` (storage write) | Side-effect: persists updated profile to SQLite backend |
| `@memory['chat_history'] := @chat_history` | `CALL` (storage write) | Side-effect: persists updated history to SQLite backend |
| `@profile`, `@chat_history`, `@new_facts`, `@response` | SPL `@vars` | Shared mutable workflow state across all steps |
| `RETURN @response WITH status='complete'` | `RETURN` | Non-trivial terminal status on the happy path |
| `RETURN ... WITH status='budget_limit'` | `RETURN` | Non-trivial terminal status on the exception path |
| `EXCEPTION WHEN BudgetExceeded` | `EXCEPTION` | Named handler; returns graceful fallback without re-raising |
| `LOGGING ... LEVEL INFO/DEBUG` | `LOGGING` | Structured runtime observability at multiple verbosity levels |

---

### 4. Logical Functions / Prompts

**`extract_facts(user_input)`**
- **Role:** Fact extraction gate — determines whether the user disclosed any new personal information in this turn.
- **Key conventions:** Returns the exact sentinel string `no_new_facts` (no whitespace variants) when nothing was found; otherwise returns a structured bullet list in the form `- Key: Value`, one fact per line. The sentinel enables a zero-cost EVALUATE branch that skips the merge step entirely.

**`merge_profile(existing_profile, new_facts)`**
- **Role:** Incremental profile maintenance — merges newly extracted facts into the accumulated user profile without hallucinating or duplicating facts.
- **Key conventions:** Treats an empty `existing_profile` as a blank-slate initialisation; otherwise merges additively, overriding only facts that are directly contradicted. Returns only the bullet list — no preamble, explanation, or commentary. Executed conditionally (only when `extract_facts` found new facts).

**`contextual_reply(user_input, profile, history)`**
- **Role:** Grounded response generation — answers the user's current message using only the known profile and conversation history.
- **Key conventions:** Explicitly constrained to facts present in the profile; if a requested fact is absent, must respond with `"I don't have that in memory."` — no inference or hallucination. One-sentence answer format keeps responses concise and history compact.

---

### 5. Control Flow

1. **Load state** — `@profile` and `@chat_history` are read from the STORAGE backend at turn start.
2. **Extract facts** — GENERATE `extract_facts` always runs; result goes to `@new_facts`.
3. **Conditional profile update** — EVALUATE `@new_facts`:
   - `= 'no_new_facts'`: no-op, profile unchanged.
   - `ELSE`: GENERATE `merge_profile` updates `@profile`; storage write persists immediately.
4. **Generate response** — GENERATE `contextual_reply` always runs with the (possibly updated) profile and history.
5. **Update and persist history** — history string is extended deterministically; CALL `trim_turns` enforces the 10-turn cap; storage write persists.
6. **Terminate** — RETURN `@response` WITH `status='complete'`.
7. **Exception path** — if `BudgetExceeded` is raised at any GENERATE step, the EXCEPTION handler returns a hardcoded fallback string WITH `status='budget_limit'`, bypassing all remaining steps.

There is no WHILE loop — this is a single-turn workflow. Across-session statefulness is achieved entirely through STORAGE reads and writes, not in-process iteration.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "<paste Section 2 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile memory_conversation.spl --lang python/pocketflow
spl3 splc compile memory_conversation.spl --lang python/langgraph
spl3 splc compile memory_conversation.spl --lang go
```