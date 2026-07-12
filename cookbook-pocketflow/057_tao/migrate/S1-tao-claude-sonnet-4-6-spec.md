## Summary

This workflow implements the Thought-Action-Observation (TAO) agentic loop, a pattern where an AI agent iteratively reasons about a problem, executes a tool action, and synthesizes the result before deciding whether to continue or conclude. It is useful for research, multi-step reasoning, and any task requiring iterative problem-solving with real-world tool use. Product teams and researchers benefit by getting a reliable, inspectable agent scaffold without building control flow from scratch.

---

## Detailed Specification

### 1. Purpose

Implements an iterative TAO reasoning agent that accepts a natural-language query, autonomously decides which tool action to take, executes it, observes the result, and repeats until the agent judges it has a sufficient final answer.

---

### 2. High-level Description

The TAO workflow is a WHILE-style agentic loop driven by an LLM judge embedded in the Think step. On each iteration, a `think` GENERATE call receives the original query plus all accumulated observations, then returns a structured YAML block containing a `thinking` rationale, an `action` name, an `action_input` string, and an `is_final` boolean. If `is_final` is false, the workflow dispatches a CALL to one of the registered tools (`search`, `calculate`, or `answer`) and stores the raw tool result in shared state. An `observe` GENERATE call then synthesizes the tool output into a concise natural-language observation, appending it to the running observations list. Control returns to `think`, which now has richer context. When `is_final` is true, the Think node sets `final_answer` in shared state and the workflow exits via RETURN WITH status="done". EVALUATE drives the branch between continuing the loop ("action" path) and terminating ("end" path) based on the `is_final` field in the LLM's YAML response. Shared state (@vars) threads `query`, `thoughts`, `observations`, `current_action`, `current_action_input`, and `final_answer` across all steps without re-passing arguments through function signatures.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW tao_agent` | `create_tao_flow()` + `Flow(start=think)` | Top-level orchestration; shared dict is the SPL execution frame |
| `CREATE FUNCTION think_prompt` | `ThinkNode.exec()` prompt string | Injects `query` and formatted `observations_text`; expects YAML out |
| `CREATE FUNCTION observe_prompt` | `ObserveNode.exec()` prompt string | Injects `action`, `action_input`, `action_result`; asks for concise observation |
| `GENERATE think_prompt(...) INTO @thought_data` | `call_llm(prompt)` + `yaml.safe_load(...)` in `ThinkNode.exec` | Parses structured YAML; result fields drive branch logic |
| `GENERATE observe_prompt(...) INTO @observation` | `call_llm(prompt)` in `ObserveNode.exec` | Unstructured prose; appended to `shared["observations"]` |
| `CALL tool(action, action_input) INTO @action_result` | `ActionNode.exec()` dispatch (`search_web`, `calculate`, `eval`) | Side-effecting tool invocation; result is raw string |
| `EVALUATE @thought_data WHEN is_final=true THEN RETURN WITH status="done" ELSE CONTINUE` | `ThinkNode.post()` returning `"end"` or `"action"` | Only non-trivial branch in the workflow; drives loop termination |
| `WHILE NOT is_final DO ... END` | `think - "think" >> think` via `observe - "think" >> think` back-edge | Loop body is Think → Action → Observe; exit condition is `is_final` in YAML |
| `@query`, `@thoughts`, `@observations`, `@final_answer` | `shared["query"]`, `shared["thoughts"]`, etc. | Mutable dict passed by reference across all nodes |
| `RETURN @final_answer WITH status="done"` | `ThinkNode.post()` returning `"end"` after setting `shared["final_answer"]` | Workflow termination; `EndNode` is a no-op sentinel |

---

### 4. Logical Functions / Prompts

**`think_prompt` (ThinkNode)**
- **Role:** The reasoning core. Given the query and all prior observations, the LLM decides whether to take another tool action or emit a final answer.
- **Key conventions:** Output must be a fenced `yaml` block containing exactly four keys: `thinking` (free-form rationale), `action` (tool name string), `action_input` (tool argument string), `is_final` (boolean). The `is_final` field is the sentinel that controls loop termination. A thought number is injected for traceability.

**`observe_prompt` (ObserveNode)**
- **Role:** Converts raw tool output into a concise, neutral natural-language observation for the next Think step to consume.
- **Key conventions:** Explicitly instructs the LLM to describe only what it sees, not to make decisions. Output is unstructured prose; no parsing step. Truncated to 50 chars in console output for readability.

---

### 5. Control Flow

```
query (INPUT)
  │
  ▼
[Think] — GENERATE think_prompt → @thought_data (YAML)
  │
  EVALUATE @thought_data.is_final
  ├── true  → RETURN @final_answer WITH status="done"  ──► END
  └── false →
        │
        ▼
      [Action] — CALL tool(@current_action, @current_action_input) INTO @action_result
        │
        ▼
      [Observe] — GENERATE observe_prompt → @observation
        │         appends to @observations list
        └──────────────────────────────────────────────► [Think]  (loop)
```

The loop has no hard iteration cap in this implementation (the README notes `max_attempt` as a planned extension). Termination is entirely LLM-driven via the `is_final` sentinel.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Implements an iterative TAO reasoning agent that accepts \
a natural-language query, autonomously decides which tool action to take (search, \
calculate, or answer), executes it, observes the result, and repeats until the agent \
judges it has a sufficient final answer. Uses a WHILE loop driven by an is_final flag \
returned by the think LLM call in YAML format. Shared state tracks query, thoughts, \
observations, and the final answer across steps." --mode workflow

# Step 2 — compile to any target
spl3 splc compile tao_web_search_agent.spl --lang python/pocketflow
spl3 splc compile tao_web_search_agent.spl --lang python/langgraph
spl3 splc compile tao_web_search_agent.spl --lang go
```