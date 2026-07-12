## Summary

This workflow implements a single-pass MCP (Model Context Protocol) agent that answers user questions by dynamically discovering available math tools, delegating to an LLM to select the right tool and extract its parameters, then invoking that tool to produce a final answer. It exists to demonstrate how an LLM can drive tool selection via MCP as an alternative to hard-coded function calling. Developers evaluating MCP adoption benefit from its built-in toggle that switches between MCP-hosted and locally-embedded tool implementations without changing the agent logic.

---

## Detailed Specification

### 1. Purpose

Execute a user's math question end-to-end by discovering available tools at runtime, using an LLM to choose and parameterize the correct tool, and returning the computed answer.

---

### 2. High-level Description

The workflow is a three-step linear orchestration with a single LLM call and two deterministic CALL steps. First, a `get_tools` CALL contacts an MCP server (or a local stub, controlled by a runtime flag) to retrieve the catalog of available math operations along with their parameter schemas. Second, a `decide_tool` CREATE FUNCTION composes a structured prompt that presents the tool catalog and the user's question, instructs the LLM to reason step-by-step, and demands a YAML-fenced response containing the selected tool name, extracted numeric parameters, and a brief rationale; the result is captured via GENERATE into `@decision`. Third, a `call_tool` CALL dispatches to the chosen tool using the extracted parameters and stores the numeric result in `@answer`. If the LLM output cannot be parsed as valid YAML, an EXCEPTION is raised and the workflow terminates without a result. On success, the workflow exits via RETURN with `status="done"` and `@answer` bound to the final numeric result. The MCP-vs-local toggle is a deployment-time adapter concern and does not alter the SPL logical specification.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW mcp_agent` | `create_mcp_flow()` + `Flow(start=...)` | Top-level orchestration unit |
| `CALL get_tools(...) INTO @tools` | `GetToolsNode.exec(server_path)` | Deterministic tool-discovery; no LLM |
| `CALL format_tool_info(@tools) INTO @tool_info` | `GetToolsNode.post(...)` loop | Formats schema into human-readable string |
| `CREATE FUNCTION decide_tool` | `DecideToolNode.prep(shared)` | Prompt template parameterized by `@tool_info` and `@question` |
| `GENERATE decide_tool(@tool_info, @question) INTO @decision` | `DecideToolNode.exec(prompt)` → `call_llm(prompt)` | Single LLM call |
| `CALL parse_yaml(@decision) INTO @tool_name, @parameters` | `yaml.safe_load(...)` in `DecideToolNode.post` | Extracts structured fields from fenced YAML |
| `CALL execute_tool(@tool_name, @parameters) INTO @answer` | `ExecuteToolNode.exec(inputs)` → `call_tool(...)` | Deterministic tool execution via MCP or local stub |
| `EXCEPTION WHEN ParseError THEN ...` | `except Exception as e: return None` in `DecideToolNode.post` | Terminates workflow when YAML parse fails |
| `RETURN @answer WITH status="done"` | `ExecuteToolNode.post(...)` → `return "done"` | Terminal exit with bound result |
| Shared state `@question`, `@tools`, `@tool_info`, `@tool_name`, `@parameters`, `@answer` | `shared` dict passed through all nodes | PocketFlow's cross-node state bus |

---

### 4. Logical Functions / Prompts

**`decide_tool`**
- **Role:** The sole LLM call in the workflow. Given the tool catalog and the user's question, it reasons about which tool applies, extracts numeric arguments, and emits a structured decision.
- **Key prompt conventions:**
  - Provides a numbered `ACTION SPACE` listing each tool's name, description, and typed parameters with required/optional status.
  - Demands output in a fenced `yaml` block with four keys: `thinking` (pipe-literal multi-line reasoning), `tool` (tool name string), `reason` (brief justification), and `parameters` (key-value map of argument names to extracted values).
  - Explicit formatting rules: 4-space indentation, `|` for multi-line fields, proper YAML indentation — reducing parse failures.
  - No scoring or sentinel tokens; correctness is enforced by downstream YAML parse + EXCEPTION.

---

### 5. Control Flow

```
INPUT: @question (string)
  │
  ▼
CALL get_tools("simple_server.py") INTO @tools          ← MCP or local stub
  │
  ▼
CALL format_tool_info(@tools) INTO @tool_info           ← deterministic formatting
  │
  ▼
GENERATE decide_tool(@tool_info, @question) INTO @decision   ← single LLM call
  │
  ├─[YAML parse fails]──► EXCEPTION ParseError → workflow terminates (no result)
  │
  ▼
CALL parse_yaml(@decision) INTO @tool_name, @parameters
  │
  ▼
CALL execute_tool(@tool_name, @parameters) INTO @answer ← MCP or local stub
  │
  ▼
RETURN @answer WITH status="done"
```

There is no WHILE loop and no EVALUATE branch. The only non-linear transition is the EXCEPTION on YAML parse failure. The `status="done"` token is the sole terminal marker; all intermediate action tokens (`"decide"`, `"execute"`) are implicit linear wiring and carry no semantic weight.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from the Description section above
spl3 text2spl --description "Execute a user's math question end-to-end by discovering available tools at runtime via a CALL to an MCP server, using a GENERATE step with a decide_tool CREATE FUNCTION to select the right tool and extract its parameters as YAML, then a CALL to execute the chosen tool and RETURN the answer with status=done. Raise an EXCEPTION when the LLM output cannot be parsed as valid YAML." --mode workflow

# Step 2 — compile to any target
spl3 splc compile mcp_web_search_agent.spl --lang python/pocketflow
spl3 splc compile mcp_web_search_agent.spl --lang python/langgraph
spl3 splc compile mcp_web_search_agent.spl --lang go
```