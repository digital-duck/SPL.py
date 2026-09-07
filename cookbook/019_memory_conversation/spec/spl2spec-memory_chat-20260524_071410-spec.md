## Summary

This workflow implements a stateful conversational agent that accumulates personal facts about the user across multiple turns by reading from and writing to a persistent SQLite memory store. Each invocation extracts new facts from the latest message, conditionally updates a user profile, then crafts a context-aware reply grounded in everything remembered so far. Non-technical stakeholders can think of it as a chat assistant that genuinely "remembers" who it is talking to without requiring a long-running server process.

---

## Detailed Specification

### 1. Purpose

Enable a turn-by-turn conversational agent that persists a user profile and chat history across independent invocations, so every response is grounded in facts the user has previously shared.

---

### 2. High-level Description

The workflow `memory_conversation` accepts two inputs: the current user message (`@user_input TEXT`) and an injected persistent storage backend (`@memory STORAGE(sqlite)`), making memory a first-class, portable workflow parameter rather than a hard-coded side-effect. At startup it loads two keys from storage — `chat_user_profile` and `chat_history` — into SPL variables `@profile` and `@chat_history`. It then invokes the `extract_facts` function via GENERATE to identify any personal facts (name, role, preferences, etc.) shared in the current message; the function returns the sentinel string `no_new_facts` when nothing actionable is found. An EVALUATE branch checks for that exact sentinel: when matched, the profile is left unchanged; in the ELSE branch, `merge_profile` is called via GENERATE to integrate the new facts and the result is written back to storage immediately. With an up-to-date profile in hand, `contextual_reply` is called via GENERATE to produce the final response, constrained to only cite facts present in the known profile and recent history. After generation, chat history is appended deterministically (no LLM cost) and trimmed to the last ten turns via a CALL to the `trim_turns` tool, then persisted back to storage. The workflow terminates with RETURN `@response` WITH `status = 'complete'`; a `BudgetExceeded` EXCEPTION handler provides a graceful fallback that returns a canned apology with `status = 'budget_limit'`.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `memory_conversation` node/flow class | `WORKFLOW memory_conversation` | Single named workflow; no sub-workflow composition |
| Prompt templates (`extract_facts`, `merge_profile`, `contextual_reply`) | `CREATE FUNCTION <name>(...) RETURN TEXT AS $$ ... $$` | Each encapsulates one LLM role; `{param}` slots are positional |
| LLM call → variable | `GENERATE <fn>(...) INTO @<var>` | Three GENERATE calls: facts, merged profile, reply |
| Sentinel-driven branch | `EVALUATE @new_facts WHEN = 'no_new_facts' THEN ... ELSE ... END` | Exact string equality check, not semantic; avoids spurious profile merges |
| Storage read | `@profile := @memory['chat_user_profile']` | STORAGE-typed input; key-value access like a dict |
| Storage write | `@memory['chat_user_profile'] := @profile` | Persists only when EVALUATE takes the ELSE branch |
| Deterministic tool call | `CALL trim_turns(@chat_history, '10') INTO @chat_history` | Side-effect helper; no LLM involved |
| Successful termination | `RETURN @response WITH status = 'complete'` | Non-trivial: callers or orchestrators can inspect `status` |
| Budget error path | `EXCEPTION WHEN BudgetExceeded THEN RETURN ... WITH status = 'budget_limit'` | Named exception type; returns a distinct status token |
| Shared mutable state | `@profile`, `@chat_history`, `@new_facts`, `@response` | SPL `@vars` accumulate state across steps within one invocation |

---

### 4. Logical Functions / Prompts

**`extract_facts(user_input TEXT)`**
- **Role:** Fact extraction gate — decides whether this turn contains any new personal information worth persisting.
- **Key conventions:** Returns the exact sentinel string `no_new_facts` (no variation, no punctuation) when nothing is found; otherwise returns a structured bullet list (`- Key: Value`). The sentinel is used downstream in an exact EVALUATE match, so prompt wording must enforce literal compliance.

**`merge_profile(existing_profile TEXT, new_facts TEXT)`**
- **Role:** Profile maintenance — idempotently integrates a bullet list of new facts into the running user profile.
- **Key conventions:** Handles a blank/empty existing profile gracefully (bootstraps a new one). Must not invent facts. Returns only the bullet list with no preamble, keeping prior facts unless directly contradicted by new ones.

**`contextual_reply(user_input TEXT, profile TEXT, history TEXT)`**
- **Role:** Response generation — answers the user's question using only what is in `@profile` and `@chat_history`.
- **Key conventions:** Answers in one sentence. Falls back to the literal phrase `"I don't have that in memory."` when the relevant fact is absent. Hard constraint against hallucinating facts not listed in the profile block.

---

### 5. Control Flow

1. **Load state** — `@profile` and `@chat_history` are read from the injected `@memory` STORAGE before any LLM call.
2. **Extract** — GENERATE `extract_facts` produces `@new_facts`.
3. **Conditional update** — EVALUATE `@new_facts`:
   - `= 'no_new_facts'` → skip profile update (profile and storage unchanged).
   - ELSE → GENERATE `merge_profile` → overwrite `@profile` → write to `@memory['chat_user_profile']`.
4. **Reply** — GENERATE `contextual_reply` with the (possibly updated) profile and history.
5. **History housekeeping** — append current turn to `@chat_history` via string concatenation; CALL `trim_turns` to enforce a 10-turn window; write back to `@memory['chat_history']`. No LLM cost.
6. **Terminate** — RETURN `@response` WITH `status = 'complete'`.
7. **Exception path** — if `BudgetExceeded` is raised at any point, execution jumps to the handler and exits with `status = 'budget_limit'`, bypassing history persistence.

There is no WHILE loop; the workflow is intentionally single-turn. Statefulness across turns is achieved by persisting to and reading from `@memory` on every invocation rather than keeping an in-process loop running.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (paste Section 2 as text2spl input)
spl3 text2spl \
  --description "A single-turn stateful conversational workflow that reads a user profile and chat history from a STORAGE-typed sqlite input, extracts personal facts from the current user message via a GENERATE call to extract_facts (returning sentinel 'no_new_facts' when absent), conditionally merges new facts into the profile via GENERATE merge_profile and persists the result, generates a grounded reply via GENERATE contextual_reply constrained to only cite known facts, deterministically appends and trims the chat history to 10 turns via CALL trim_turns, and returns the response with status='complete'; a BudgetExceeded EXCEPTION handler returns a canned fallback with status='budget_limit'." \
  --mode workflow

# Step 2 — compile to any target
spl3 splc compile memory_conversation.spl --lang python/pocketflow
spl3 splc compile memory_conversation.spl --lang python/langgraph
spl3 splc compile memory_conversation.spl --lang go
```