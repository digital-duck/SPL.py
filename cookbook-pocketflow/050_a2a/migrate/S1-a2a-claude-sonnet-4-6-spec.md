## Summary

This is a web-research question-answering agent that autonomously decides whether it needs to search the internet or can answer directly from context it has already gathered. It operates as a ReAct-style loop (Reason → Act → Observe) and is additionally wrapped behind an Agent-to-Agent (A2A) JSON-RPC server so that other agents or clients can invoke it over HTTP without knowing its internal structure. Product teams and developers building multi-agent systems benefit from the clean separation: the workflow logic stays unchanged while the A2A layer handles discovery, routing, and protocol compliance.

---

## Detailed Specification

### 1. Purpose

Given a free-text question, autonomously gather web evidence through iterative search-and-reason cycles and return a final synthesized answer — exposed both as a direct CLI tool and as an A2A-compliant HTTP service.

---

### 2. High-level Description

This implementation follows the **ReAct (Reason + Act)** agentic pattern expressed as an SPL WORKFLOW with a WHILE-style loop driven by an EVALUATE branch. The workflow maintains a shared accumulator (`@context`) that grows with each search round and is read by every subsequent LLM call, giving the agent memory across iterations.

The first logical function, **DecideAction**, receives the original question and whatever context has been accumulated so far, then issues a GENERATE call whose prompt elicits a structured YAML block containing `action` (either `"search"` or `"answer"`), a `search_query` if searching is needed, and chain-of-thought `thinking`. The EVALUATE on the result drives a binary branch: the `"search"` branch routes to **SearchWeb**, a CALL to a DuckDuckGo tool that appends title/URL/snippet tuples to `@context`, after which control loops back to DecideAction; the `"answer"` branch routes to **AnswerQuestion**, which issues a second GENERATE call that synthesises `@context` into a final prose response stored in `@answer`, then terminates with `RETURN @answer WITH status="done"`.

The A2A server layer wraps this workflow in a JSON-RPC HTTP endpoint: incoming `tasks/send` requests are unpacked by `PocketFlowTaskManager`, the user query is extracted and passed to the workflow as `@question`, and the finished `@answer` is repackaged as an A2A `Artifact`. EXCEPTION handling in the task manager catches any flow-level failure and returns a structured A2A error response with `state=FAILED`. Streaming (`on_send_task_subscribe`) is declared unsupported and returns `UnsupportedOperationError` immediately.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW research_agent` | `create_agent_flow()` + `Flow(start=decide)` | Top-level orchestration unit |
| `CREATE FUNCTION decide_action` | `DecideAction.exec()` | YAML-structured prompt; parses `action`, `search_query`, `thinking` |
| `CREATE FUNCTION synthesise_answer` | `AnswerQuestion.exec()` | Synthesis prompt consuming `@context` |
| `GENERATE decide_action(...) INTO @decision` | `call_llm(prompt)` in `DecideAction.exec` | Returns raw text; YAML parsed in `post()` |
| `GENERATE synthesise_answer(...) INTO @answer` | `call_llm(prompt)` in `AnswerQuestion.exec` | Final prose answer |
| `CALL search_web(@query) INTO @results` | `search_web(search_query)` in `SearchWeb.exec` | DuckDuckGo DDGS, max 5 results; side-effect tool |
| `EVALUATE @decision WHEN action="search" THEN ... ELSE ... END` | `DecideAction.post()` returning `"search"` or `"answer"` | YAML field drives PocketFlow edge routing |
| `WHILE action = "search" DO ... END` | `decide → search → decide` cycle in Flow | Loop terminates when DecideAction returns `"answer"` |
| `@context` (shared accumulator) | `shared["context"]` dict key | Appended after each SearchWeb; read by both DecideAction and AnswerQuestion |
| `@question` (input var) | `shared["question"]` | Set before flow starts; never mutated |
| `RETURN @answer WITH status="done"` | `AnswerQuestion.post()` returning `"done"` | Terminates the loop; non-trivial status |
| `EXCEPTION WHEN ExecutionError THEN ...` | `try/except Exception` in `PocketFlowTaskManager.on_send_task` | Sets A2A task state to `FAILED`; returns `InternalError` |
| `CALL a2a_server(...)` (infrastructure) | `A2AServer` + `PocketFlowTaskManager` | Transport layer; maps JSON-RPC `tasks/send` → workflow invocation |

---

### 4. Logical Functions / Prompts

**DecideAction**
- Role: The agent's reasoning hub — decides each iteration whether more evidence is needed or the question can be answered.
- Prompt conventions: Formats available actions as a numbered action space (`[1] search`, `[2] answer`) with typed parameters. Requires the LLM to respond in a fenced ` ```yaml ``` ` block with fields `thinking` (pipe-literal multi-line), `action`, `reason`, `answer`, and `search_query`. The sentinel delimiters ` ```yaml ` / ` ``` ` are used to reliably extract the structured block for `yaml.safe_load` parsing, avoiding brittle regex.

**SearchWeb** (tool, not LLM)
- Role: Executes the web search decided by DecideAction; not an LLM call. Returns up to 5 DuckDuckGo results formatted as `Title / URL / Snippet` triples, concatenated and appended to `@context`.

**AnswerQuestion**
- Role: Terminal synthesis step — reads the full accumulated `@context` and produces a comprehensive natural-language answer.
- Prompt conventions: Simple two-section prompt (`CONTEXT` with question + research, `YOUR ANSWER` directive). No structured output required; free-form prose is expected. No sentinel or scoring — this is a terminal generation with no downstream parser.

---

### 5. Control Flow

```
START
  └─► DecideAction  (GENERATE decide_action; parse YAML)
         │
         EVALUATE action
         ├─ "search" ──► SearchWeb  (CALL search_web; append to @context)
         │                    └─► back to DecideAction          ← WHILE loop
         │
         └─ "answer" ──► AnswerQuestion  (GENERATE synthesise_answer INTO @answer)
                              └─► RETURN @answer WITH status="done"   ← termination
```

The loop has no explicit iteration cap in the Python code; DecideAction is responsible for self-regulating by choosing `"answer"` once sufficient context exists. The A2A wrapper adds a surrounding try/except that converts any unhandled exception into `status=FAILED` before the loop reaches the client.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl \
  --description "A ReAct web-research agent that maintains a shared @context accumulator. \
A WHILE loop driven by EVALUATE on a YAML-structured GENERATE call (DecideAction) \
alternates between CALL search_web() tool invocations (appending results to @context) \
and a terminal GENERATE synthesise_answer call (AnswerQuestion) that returns the final \
answer WITH status=done. Exception handling wraps the entire flow." \
  --mode workflow

# Step 2 — compile to any target
spl3 splc compile research_web_search_agent.spl --lang python/pocketflow
spl3 splc compile research_web_search_agent.spl --lang python/langgraph
spl3 splc compile research_web_search_agent.spl --lang go
```