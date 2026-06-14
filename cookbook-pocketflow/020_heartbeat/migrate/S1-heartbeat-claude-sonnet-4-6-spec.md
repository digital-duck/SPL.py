## Summary

The Heartbeat Monitor is a continuously-running agent that polls a simulated email inbox on a fixed schedule, summarizes any new messages with an LLM, and suggests a reply action for each one. It demonstrates the "open claw" pattern: an outer timing loop keeps the agent alive across N cycles, while an inner conditional flow processes work only when it exists. Engineers and architects building always-on AI automation — email triage, deployment health checks, Slack watchers — can use this as a reusable structural template.

---

## Detailed Specification

### 1. Purpose

Execute a configurable number of timed polling cycles, and for each cycle that contains new email, invoke an LLM to summarize the message and recommend a reply action.

---

### 2. High-level Description

This workflow implements a periodic polling agent using two nested WORKFLOW scopes: an outer heartbeat loop and an inner email-processing subflow. The outer loop is driven by a WHILE construct that advances a cycle counter on each iteration, pauses for a fixed interval, and continues until the counter reaches `max_cycles`, at which point RETURN WITH status="done" halts the loop. Inside each iteration, the inner subflow is invoked as a nested CALL: a CheckEmail step reads from a simulated inbox and branches via EVALUATE — if no mail is found the inner flow exits silently; if mail is present it routes to ProcessEmail. ProcessEmail issues a GENERATE call for each message, passing a prompt that requests a one-sentence summary and a suggested reply action, accumulating results into a shared `@processed` list. No explicit EXCEPTION handler is defined, so LLM failures propagate naturally. The design cleanly separates lifecycle control (outer loop, cycle counter, sleep) from domain logic (inbox check, LLM summarisation), allowing the inner flow to be swapped for any other monitoring task without touching the outer heartbeat structure.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW heartbeat_monitor` | `create_heartbeat_flow()` + outer `Flow(start=wait)` | Top-level orchestration unit |
| `WORKFLOW email_processing` | `Flow(start=check)` (inner `email_flow`) | Nested subflow; invoked as a single node by the outer flow |
| `CALL email_processing() INTO @result` | `wait >> email_flow` / `email_flow >> wait` wiring | PocketFlow edge wires Flow-as-Node; SPL models it as a CALL |
| `WHILE @cycle < @max_cycles DO ... END` | `WaitNode.post` loop — continues until `shared["cycle"] >= max_cycles` | Loop termination driven by the "done" return |
| `RETURN @cycle WITH status="done"` | `WaitNode.post` returning `"done"` | Non-trivial token; stops the outer loop |
| `EVALUATE @inbox WHEN empty THEN ... ELSE RETURN "new_email" END` | `CheckEmail.post` — `None` vs `"new_email"` | Conditional branch inside inner flow |
| `GENERATE summarize_email(@email) INTO @summary` | `call_llm(prompt)` inside `ProcessEmail.exec` | One LLM call per email; results collected into list |
| `CREATE FUNCTION summarize_email` | Inline f-string prompt in `ProcessEmail.exec` | Prompt: "Summarize in one sentence and suggest a reply action" |
| `@shared` variables | `shared` dict (`cycle`, `max_cycles`, `emails`, `processed`) | Mutable state passed across all nodes |
| `time.sleep(interval)` | `WaitNode.exec` | No SPL equivalent; modelled as a side-effect CALL or built-in wait |

---

### 4. Logical Functions / Prompts

**`summarize_email`**
- **Role**: The only LLM-facing function; called once per email found in a cycle.
- **Prompt template**:
  ```
  Summarize this email in one sentence and suggest a reply action.
  From: {from}
  Subject: {subject}
  Body: {body}
  ```
- **Output format**: Free-form natural language; one sentence summary followed by a reply suggestion. No sentinel tokens or scoring — output is printed directly and stored in `@processed`.

---

### 5. Control Flow

```
START
  │
  ▼
WaitNode (increment @cycle, sleep 2 s)
  │
  ├─ @cycle < @max_cycles  ──► CALL email_processing
  │                                  │
  │                            CheckEmail
  │                                  │
  │                   ┌─── empty ───►│ (inner flow ends, no work done)
  │                   │              │
  │                   │         "new_email"
  │                   │              │
  │                   │         ProcessEmail
  │                   │         GENERATE summarize_email(@email) INTO @summary
  │                   │         append @summary → @processed
  │                   │              │
  │                   └─────────────►│ (inner flow exits)
  │
  │◄─────────────── loop back to WaitNode
  │
  └─ @cycle >= @max_cycles  ──► RETURN WITH status="done"  (loop terminates)

END  → print total emails processed from @processed
```

The only non-trivial branch point is `EVALUATE` inside `CheckEmail` ("new_email" vs silent exit) and `RETURN WITH status="done"` from `WaitNode` which is the sole loop-exit condition.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (use Section 2 as text2spl input)
spl3 text2spl --description "Execute a configurable number of timed polling cycles. \
On each cycle, increment a counter, pause for a fixed interval, then invoke an inner \
email-processing subflow. The inner subflow checks a simulated inbox: if empty, it exits; \
if emails are found, it calls GENERATE with a prompt requesting a one-sentence summary and \
reply-action suggestion for each message, accumulating results in @processed. \
After max_cycles cycles, RETURN WITH status=done terminates the outer WHILE loop." \
--mode workflow

# Step 2 — compile to any target
spl3 splc compile heartbeat_monitor.spl --lang python/pocketflow
spl3 splc compile heartbeat_monitor.spl --lang python/langgraph
spl3 splc compile heartbeat_monitor.spl --lang go
```