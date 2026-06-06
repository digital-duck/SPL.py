## 0. High-level Description

This workflow implements a **memory-augmented conversational agent** using a stateful, single-turn execution pattern: each invocation loads prior context, optionally updates it, generates a reply, then persists the new state. The key novelty is that persistent memory is declared as a first-class `INPUT` of type `STORAGE(sqlite, ...)`, making the storage backend injectable and portable rather than hardcoded. Three `CREATE FUNCTION` definitions divide responsibility cleanly: `extract_facts` extracts personal facts from the current user message and uses a sentinel token (`no_new_facts`) to signal the absence of new information; `merge_profile` maintains a deduplicated bullet-list user profile by merging new facts into an existing one without hallucinating; and `contextual_reply` produces a single-sentence answer grounded exclusively in the stored profile and recent history, falling back to a fixed disclaimer when a fact is absent. Control flow uses an `EVALUATE` branch on the exact sentinel string to gate profile updates — the `WHEN = 'no_new_facts'` path skips a `GENERATE` call entirely, saving LLM cost. A deterministic `CALL` to `trim_turns` (no LLM involved) caps history at ten turns before writing back to storage. `LOGGING` statements at `INFO` and `DEBUG` levels bracket every meaningful state change. The single `EXCEPTION` handler catches `BudgetExceeded` and returns a graceful in-character fallback rather than a hard error.

## 1. Purpose

Provide a stateful chat agent that remembers personal facts about the user across invocations by persisting a structured profile and rolling conversation history in a SQLite-backed storage variable.

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@user_input` | *(required)* | The user's current message text |
| `@memory` | `STORAGE(sqlite, '~/.spl/memory.db')` | Persistent key-value store; holds `chat_user_profile` and `chat_history` entries; path can be overridden at call time |

## 3. Process

1. Log the incoming `@user_input` at `INFO` level.
2. Load `@profile` from `@memory['chat_user_profile']` and `@chat_history` from `@memory['chat_history']`; log both at `DEBUG`.
3. `GENERATE extract_facts(@user_input)` — call the LLM to identify any personal facts in the message; store result in `@new_facts`; log at `DEBUG`.
4. `EVALUATE @new_facts`:
   - **`= 'no_new_facts'`** — log that the profile is unchanged and skip the merge.
   - **else** — log that new facts were detected, `GENERATE merge_profile(@profile, @new_facts)` to produce an updated bullet-list profile, store it back in `@profile`, and persist it to `@memory['chat_user_profile']`.
5. `GENERATE contextual_reply(@user_input, @profile, @chat_history)` — produce a one-sentence answer using the full available context; store in `@response`.
6. Append the current turn (`User: …` / `Assistant: …`) to `@chat_history` using string concatenation.
7. `CALL trim_turns(@chat_history, '10')` — deterministically truncate history to the last 10 turns (no LLM cost); store result back in `@chat_history`.
8. Persist the updated `@chat_history` to `@memory['chat_history']`.
9. Log `'Response ready'` at `INFO`.
10. `RETURN @response WITH status = 'complete'`.

## 4. Error Handling

- **`BudgetExceeded`** — catches any LLM generation that would exceed the spending limit; returns the in-character string `'I remember you! But I ran out of budget for this response.'` with `status = 'budget_limit'`, avoiding a hard crash and preserving conversational tone.

## 5. Output

| Field | Value |
|---|---|
| Return variable | `@response` — a single-sentence natural-language reply |
| `status` (normal) | `'complete'` |
| `status` (budget error) | `'budget_limit'` |

Side effects: `@memory['chat_user_profile']` and `@memory['chat_history']` are updated in the SQLite database on every turn where new facts are found or a reply is generated.