## Summary

This workflow implements a supervised research agent that answers user questions by combining web search with LLM reasoning. An inner agent iteratively decides whether to search or answer, while an outer supervisor validates each candidate answer and forces a retry if the response is nonsensical or fabricated. The design benefits product teams that need reliable, citation-grounded answers from an otherwise unreliable LLM — the supervisor acts as a quality gate, not just a filter.

---

## Detailed Specification

### 1. Purpose

Produce a verified, high-quality answer to any user question by wrapping an unreliable research agent with a supervisor that rejects nonsensical responses and reruns the full research cycle until an acceptable answer is produced.

---

### 2. High-level Description

The workflow is structured as two nested WORKFLOW blocks. The inner `research_agent` WORKFLOW uses a WHILE loop to drive a ReAct-style search-or-answer cycle: a `decide_action` CREATE FUNCTION prompts the LLM to emit a YAML decision block choosing either `search` (with a query) or `answer`; if search, a CALL to `search_web` appends results to a growing `@context` variable and the loop continues; if answer, a `generate_answer` CREATE FUNCTION produces a candidate stored in `@answer`, ending the inner loop. The outer `supervised_agent` WORKFLOW calls the inner flow, then passes `@answer` to a `check_quality` CREATE FUNCTION that inspects the text for hardcoded nonsense markers (no LLM call needed); if the check fails, the supervisor appends a rejection note to `@context`, clears `@answer`, and issues RETURN WITH status="retry", which drives a WHILE loop that reruns the entire inner agent. When the supervisor approves, the outer loop exits and `@answer` is the final result. The inner agent intentionally simulates unreliability — a 50 % random branch in `generate_answer` substitutes a dummy string — making the supervisor's retry logic the load-bearing correctness mechanism. No multimodal input or EXCEPTION handlers are present in this implementation; error recovery is handled entirely by the retry loop.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW research_agent` | `create_agent_inner_flow()` + `DecideAction`, `SearchWeb`, `UnreliableAnswerNode` nodes | Inner ReAct loop |
| `WORKFLOW supervised_agent` | `create_agent_flow()` + `SupervisorNode` | Outer quality-gate loop |
| `CREATE FUNCTION decide_action` | `DecideAction.exec()` prompt string | Emits YAML block with `action`, `search_query`, `thinking` fields |
| `CREATE FUNCTION generate_answer` | `UnreliableAnswerNode.exec()` prompt string | Has a 50 % random branch that substitutes a dummy nonsense string |
| `CREATE FUNCTION check_quality` | `SupervisorNode.exec()` marker scan | Keyword-match, not an LLM call; returns `{valid, reason}` |
| `GENERATE decide_action(...) INTO @decision` | `call_llm(prompt)` inside `DecideAction.exec()` | YAML parsed; regex fallback when YAML is malformed |
| `GENERATE generate_answer(...) INTO @answer` | `call_llm(prompt)` inside `UnreliableAnswerNode.exec()` | Skipped on the 50 % dummy branch |
| `CALL search_web(@query) INTO @results` | `search_web(search_query)` via DuckDuckGo DDGS | Side-effecting tool call; results appended to `@context` |
| `EVALUATE @decision WHEN action == "search"` | `DecideAction.post()` returning `"search"` or `"answer"` | Routes to `SearchWeb` or `UnreliableAnswerNode` |
| `WHILE @answer not valid DO ... END` | `supervisor - "retry" >> agent_flow` cycle in `create_agent_flow()` | Outer retry loop; exits when supervisor approves |
| `WHILE not answered DO ... END` | `search - "decide" >> decide` back-edge in `create_agent_inner_flow()` | Inner ReAct loop; exits when action == "answer" |
| `RETURN WITH status="retry"` | `SupervisorNode.post()` returning `"retry"` | Only non-default token that drives a real branch |
| `@context`, `@answer`, `@question` | `shared` dict keys `"context"`, `"answer"`, `"question"` | Single mutable shared store threaded through all nodes |

---

### 4. Logical Functions / Prompts

**`decide_action`**
- Role: ReAct decision hub — the LLM chooses the next atomic action each iteration.
- Prompt conventions: Supplies `question` and `Previous Research` (accumulated `@context`) in a `### CONTEXT` block; lists a numbered `### ACTION SPACE` with typed parameters; instructs the LLM to respond in a fenced YAML block with fields `thinking`, `action`, `reason`, `search_query`. A regex fallback extracts `action` and `search_query` line-by-line when the YAML is malformed (common with smaller models like gemma3 that omit the block-scalar `|` indicator).

**`generate_answer`**
- Role: Synthesizes a final prose answer from accumulated research context.
- Prompt conventions: Supplies `question` and `Research` in a `### CONTEXT` block; asks for a "comprehensive answer." No structured output format — free-form prose. Has a non-prompt 50 % random branch that bypasses the LLM entirely and returns a fixed nonsense string to exercise the supervisor.

**`check_quality`**
- Role: Supervisor gate — determines whether the candidate answer is acceptable.
- Prompt conventions: No LLM call. Performs substring matching against a fixed allowlist of nonsense markers (`"coffee break"`, `"purple unicorns"`, `"made up"`, `"42"`, `"Who knows?"`). Returns a `{valid: bool, reason: str}` struct. If invalid, appends `"NOTE: Previous answer attempt was rejected by supervisor."` to `@context` before issuing retry.

---

### 5. Control Flow

```
START: outer WHILE loop begins (answer not yet valid)
  │
  └─► inner WHILE loop begins (action not yet "answer")
        │
        └─► GENERATE decide_action(@question, @context) INTO @decision
              │
              EVALUATE @decision
                WHEN action == "search":
                  CALL search_web(@search_query) INTO @results
                  append to @context
                  → loop back to decide_action
                WHEN action == "answer":
                  GENERATE generate_answer(@question, @context) INTO @answer
                  → exit inner loop
      │
  └─► check_quality(@answer)   ← no LLM; keyword scan
        │
        EVALUATE result
          WHEN valid == True:
            → exit outer loop → RETURN @answer (workflow complete)
          WHEN valid == False:
            clear @answer, append rejection note to @context
            RETURN WITH status="retry"
            → restart inner loop from decide_action
```

Termination is guaranteed only probabilistically: each outer retry gives the inner agent a fresh chance to produce a non-dummy answer (50 % per attempt). No hard iteration cap exists in this implementation; an SPL equivalent should add a `MAX_RETRIES` guard.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (paste Section 2 above as text2spl input)
spl3 text2spl --description "The workflow is structured as two nested WORKFLOW blocks. \
The inner research_agent WORKFLOW uses a WHILE loop to drive a ReAct-style \
search-or-answer cycle: a decide_action CREATE FUNCTION prompts the LLM to emit a \
YAML decision block choosing either search (with a query) or answer; if search, a \
CALL to search_web appends results to a growing @context variable and the loop \
continues; if answer, a generate_answer CREATE FUNCTION produces a candidate stored \
in @answer, ending the inner loop. The outer supervised_agent WORKFLOW calls the \
inner flow, then passes @answer to a check_quality CREATE FUNCTION that inspects \
the text for hardcoded nonsense markers; if the check fails, the supervisor appends \
a rejection note to @context, clears @answer, and issues RETURN WITH status=retry, \
which drives a WHILE loop that reruns the entire inner agent. When the supervisor \
approves, the outer loop exits and @answer is the final result." \
--mode workflow

# Step 2 — compile to any target
spl3 splc compile output.spl --lang python/pocketflow
spl3 splc compile output.spl --lang python/langgraph
spl3 splc compile output.spl --lang go
```