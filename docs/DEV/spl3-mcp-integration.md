# SPL × MCP Integration Design

> **Status:** Design phase. Not yet implemented.
>
> **Depends on:** `spl3-tool-api.md` (CREATE TOOL_API — fully implemented),
> `spl3-workflow-registry.md` (workflow radicals — vision phase).

---

## 1. What MCP is and why it matters for SPL

MCP (Model Context Protocol) is a JSON-RPC protocol for connecting LLMs
to external tools and data sources. An MCP **server** exposes tools (with
typed JSON Schema parameters) and resources. An MCP **client** discovers
and invokes them. Transport: stdio (local subprocess) or HTTP+SSE (remote).

MCP is becoming the standard tool protocol — Claude Desktop, VS Code
Copilot, Cursor, and dozens of agent frameworks already speak it. There
are hundreds of existing MCP servers: filesystem, databases, web search,
GitHub, Slack, Kubernetes, and more.

SPL's `CREATE TOOL_API` already solved the *internal* tool problem — embed
Python in `.spl` files. MCP solves the *external* tool problem — connect
to tool servers that already exist, without writing Python wrappers.

The integration has three hooks, each independently useful:

| Hook | Direction | What it does |
|---|---|---|
| **Hook 1: `AS MCP`** | SPL → MCP server | SPL workflows consume MCP tools via `CALL` |
| **Hook 2: `IMPORT MCP`** | SPL → MCP server | Bulk-import all tools from an MCP server |
| **Hook 3: `spl3 serve --mcp`** | MCP client → SPL | Expose SPL workflows as MCP tools |

All three hooks register into `FunctionRegistry` and dispatch via `CALL` —
the same path as `AS PYTHON` tools, stdlib builtins, and SPL procedures.

---

## 2. Hook 1: `CREATE TOOL_API ... AS MCP`

### 2.1 Syntax

```spl
CREATE TOOL_API read_file(path TEXT) RETURNS TEXT
  AS MCP $$ filesystem: "npx @modelcontextprotocol/server-filesystem /tmp" $$;

CREATE TOOL_API query_db(sql TEXT) RETURNS TEXT
  AS MCP $$ sqlite: "uvx mcp-server-sqlite --db-path data.db" $$;
```

The `$$` body for `AS MCP` is a YAML-like config (parsed as key-value):

```
<server_name>: "<command to start the MCP server>"
```

- `server_name` — a label for lifecycle management (multiple TOOL_APIs
  can share a server by using the same name)
- The command string is what gets passed to `subprocess.Popen` (stdio
  transport)
- The tool name in the MCP server is inferred from the SPL function name.
  Override with an explicit `tool:` key if they differ.

### 2.2 Extended syntax — explicit tool name mapping

When the SPL name differs from the MCP tool name:

```spl
CREATE TOOL_API list_dir(path TEXT) RETURNS TEXT
  AS MCP $$
    server: "npx @modelcontextprotocol/server-filesystem /tmp"
    tool: "list_directory"
  $$;
```

### 2.3 How it fits the existing architecture

The integration point is `_load_tool_apis()` in `spl3/executor.py:530`:

```python
if stmt.runtime == "PYTHON":
    # ... existing exec() path ...
elif stmt.runtime == "MCP":
    fn = self._load_mcp_tool(stmt)
```

The `_load_mcp_tool` method:
1. Parses the `$$` body for server command and tool name
2. Starts the MCP server process (or reuses if already running with same
   server name)
3. Calls `tools/list` to verify the tool exists
4. Returns an async callable that wraps `tools/call`
5. Registers it via `self.register_tool(stmt.name, fn)`

From `CALL`'s perspective, the callable is identical to a Python tool —
it takes `str` arguments and returns `str`. The MCP bridge handles the
JSON-RPC serialization internally.

### 2.4 Server lifecycle

MCP servers are subprocesses. Lifecycle rules:

- **Start**: lazily on first `_load_mcp_tool` referencing that server name
- **Share**: multiple TOOL_APIs pointing to the same server name share one
  process (one `tools/list`, many `tools/call`)
- **Stop**: at executor shutdown (end of `execute_program`), all MCP
  server processes are terminated
- **Restart**: if a server process dies mid-run, the next `CALL` attempt
  detects the dead process and restarts it (one retry)

Server processes are managed by a new `MCPServerPool` class:

```python
class MCPServerPool:
    """Manages MCP server subprocess lifecycles for one executor run."""
    
    _servers: dict[str, MCPSession]   # server_name → live session
    
    async def get_or_start(self, name: str, command: str) -> MCPSession: ...
    async def call_tool(self, server: str, tool: str, args: dict) -> str: ...
    async def shutdown(self) -> None: ...
```

### 2.5 Parser changes

The parser already handles `AS <IDENTIFIER>` in `_parse_tool_api()`. The
runtime tag is stored in `ToolAPINode.runtime`. Currently only `"PYTHON"`
is accepted; adding `"MCP"` requires:

1. Accept `"MCP"` as a valid runtime identifier (one line in parser)
2. The `$$` body is already captured as `python_body` — rename the field
   to `body` (or keep the name and document that it holds the MCP config
   when `runtime == "MCP"`)

**Recommendation**: rename `ToolAPINode.python_body` → `ToolAPINode.body`
internally, since the field now holds runtime-specific content (Python
source for `AS PYTHON`, config for `AS MCP`). This is an internal-only
change — no public API or `.spl` syntax is affected. Add a `@property`
alias `python_body` that delegates to `body` so any existing code that
references the old name continues to work without modification.

### 2.6 Type mapping

SPL parameters are all strings. MCP parameters are typed JSON Schema.
The bridge maps:

| SPL type | MCP JSON Schema type | Conversion |
|---|---|---|
| `TEXT` | `string` | pass through |
| `INTEGER` / `INT` | `integer` or `number` | `str(int(value))` |
| `FLOAT` | `number` | `str(float(value))` |

MCP tool results are `content` arrays (text, image, resource). The bridge
extracts the first `text` content block and returns it as a string —
consistent with how all SPL tools return `str`.

---

## 3. Hook 2: `IMPORT MCP`

### 3.1 Syntax

```spl
-- Import all tools from a small server
IMPORT MCP "sqlite" FROM "uvx mcp-server-sqlite --db-path data.db"

-- Cherry-pick specific tools from a large server (avoids pollution)
IMPORT MCP "filesystem" FROM "npx @modelcontextprotocol/server-filesystem /tmp"
  ONLY read_file, write_file, list_directory

-- Exclude specific tools
IMPORT MCP "github" FROM "npx @modelcontextprotocol/server-github"
  EXCEPT create_issue, delete_branch
```

**Filtering is important.** Large MCP servers can expose dozens of tools.
Importing all of them pollutes the `FunctionRegistry` namespace and can
impact performance (every `CALL` resolution walks the registry). The
`ONLY` clause is the recommended default for production workflows —
import exactly what you need.

Without `ONLY` or `EXCEPT`, all tools are imported (convenient for
exploration, not recommended for production).

### 3.2 How it works

At parse time, `IMPORT MCP` produces a new AST node:

```python
@dataclass
class ImportMCPStatement:
    server_name: str      # "filesystem"
    command: str          # "npx @modelcontextprotocol/server-filesystem /tmp"
```

At load time (`_load_tool_apis` or a new `_load_mcp_imports`), the
executor:

1. Starts the MCP server subprocess
2. Calls `initialize` + `tools/list`
3. For each tool in the response, registers an async callable:
   ```python
   for tool in tools_response:
       async def call_mcp(server=server_name, tool_name=tool.name, **kwargs):
           return await self._mcp_pool.call_tool(server, tool_name, kwargs)
       self.register_tool(tool.name, call_mcp)
   ```
4. Logs all discovered tools at INFO level

### 3.3 Name collisions

If an MCP server exposes a tool named `read_file` and the stdlib also has
`read_file`, the load order determines who wins:

```
1. Library tools (~/.spl/tool_apis/)     ← lowest priority
2. MCP imports (IMPORT MCP)
3. Inline TOOL_API blocks (AS PYTHON)    ← highest priority
```

Inline always wins. MCP imports override library tools. This is consistent
with the existing "local wins" principle.

### 3.4 Namespace prefixing (optional)

To avoid collisions, an optional `AS` clause adds a prefix:

```spl
IMPORT MCP "filesystem" FROM "..." AS fs
-- registers: fs_read_file, fs_write_file, fs_list_directory, ...
```

Without `AS`, tools are registered with their native MCP names.

### 3.5 Generation-time awareness

`available_tools_prompt_block()` in `tool_api_registry.py` should also
list MCP-imported tools so `text2spl` / `mmd2spl` can reference them.
This requires the MCP server config to be registered persistently (see
§5 — MCP server registry).

---

## 4. Hook 3: `spl3 serve --mcp` — SPL as MCP server

### 4.1 The value

Every SPL workflow with typed `INPUT`/`OUTPUT` already has the metadata
an MCP tool schema needs. Exposing workflows as MCP tools means:

- Claude Desktop can `CALL` an SPL workflow as a tool
- Other agent frameworks (LangChain, CrewAI, AutoGen) can invoke SPL
  workflows via MCP without knowing SPL exists
- The workflow registry (§ spl3-workflow-registry.md) becomes a
  discoverable tool catalog

### 4.2 CLI

```bash
# Serve all promoted workflows as MCP tools
spl3 serve --mcp

# Serve a specific .spl file
spl3 serve --mcp cookbook/05_self_refine/self_refine.spl

# Serve with a specific adapter for GENERATE steps
spl3 serve --mcp --adapter ollama -m gemma3

# Specify transport (default: stdio)
spl3 serve --mcp --transport stdio
spl3 serve --mcp --transport sse --port 8080
```

### 4.3 Mapping: SPL workflow → MCP tool

```spl
WORKFLOW verify_math
  INPUT  @problem TEXT
  INPUT  @backend TEXT := "sympy"
  OUTPUT @result  TEXT
DO
  ...
END
```

becomes:

```json
{
  "name": "verify_math",
  "description": "SPL workflow: verify_math",
  "inputSchema": {
    "type": "object",
    "properties": {
      "problem": { "type": "string", "description": "TEXT parameter" },
      "backend": { "type": "string", "default": "sympy", "description": "TEXT parameter (default: sympy)" }
    },
    "required": ["problem"]
  }
}
```

Rules:
- Each `INPUT` param → a JSON Schema property
- Params with default values → not in `required`
- `OUTPUT` → the tool result (returned as text content)
- SPL types map: `TEXT` → `string`, `INT`/`INTEGER` → `integer`,
  `FLOAT` → `number`

### 4.4 What `tools/call` does

When an MCP client calls the `verify_math` tool:

1. The MCP server receives `tools/call` with `name: "verify_math"` and
   `arguments: {"problem": "differentiate 3x^3 - x"}`
2. It loads the `.spl` file, creates an `SPL3Executor` with the
   configured adapter
3. Maps MCP arguments → SPL `--param` flags
4. Runs `execute_program()` (the same path as `spl3 run`)
5. Extracts the `OUTPUT` variable and returns it as a text content block

### 4.5 Workflow discovery

The MCP server's `tools/list` response includes:

1. All workflows in the registry (`~/.spl/workflows/`)
2. Any `.spl` files passed via CLI arguments
3. Optionally, all promoted TOOL_API libraries (exposed as individual
   tool functions, not as workflows)

### 4.6 Adapter configuration

The MCP server needs an LLM adapter for `GENERATE` steps. Options:

```bash
# Explicit adapter — all GENERATE steps use this
spl3 serve --mcp --adapter ollama -m gemma3

# Environment variable fallback
export SPL_DEFAULT_ADAPTER=ollama
export SPL_DEFAULT_MODEL=gemma3
spl3 serve --mcp

# Per-workflow override (future: workflow metadata in registry)
```

### 4.7 Concurrency

MCP allows concurrent `tools/call` requests. The server should:

- Create a fresh `SPL3Executor` per request (executors are not
  thread-safe)
- Share the adapter instance (adapters are stateless HTTP clients)
- Rate-limit based on adapter capacity (e.g., Ollama has a concurrency
  limit)

---

## 5. MCP server registry

For persistent MCP server configuration (so `IMPORT MCP` servers don't
need to be declared in every `.spl` file), add a registry alongside the
existing tool registry:

```
~/.spl/
    tool_apis/          # existing — CREATE TOOL_API libraries
    mcp_servers/        # new — MCP server configs
        filesystem.json
        sqlite.json
```

Each config file:

```json
{
  "name": "filesystem",
  "command": "npx @modelcontextprotocol/server-filesystem /tmp",
  "transport": "stdio",
  "env": {},
  "tools_prefix": ""
}
```

CLI:

```bash
spl3 mcp add filesystem "npx @modelcontextprotocol/server-filesystem /tmp"
spl3 mcp add sqlite "uvx mcp-server-sqlite --db-path data.db"
spl3 mcp list
spl3 mcp remove filesystem
```

Registered MCP servers are auto-loaded at executor startup (like library
tools), making their tools available to every `CALL` without explicit
`IMPORT MCP` in the `.spl` file.

---

## 6. Implementation plan

### Phase 1: MCP client bridge (Hook 1 + Hook 2)

| File | Change |
|---|---|
| `spl3/mcp_bridge.py` | **New module.** `MCPServerPool` (lifecycle), `MCPToolWrapper` (callable), config parsing |
| `spl3/ast_nodes.py` | Rename `python_body` → `body` in `ToolAPINode`. Add `ImportMCPStatement` dataclass |
| `spl3/parser.py` | Accept `"MCP"` as runtime tag. Parse `IMPORT MCP "name" FROM "command"` |
| `spl3/executor.py` | `_load_tool_apis`: add `elif stmt.runtime == "MCP"` branch. Add `_load_mcp_imports`. Shutdown pool in `execute_program` finally block |
| `spl3/tool_api_registry.py` | `list_tools()` includes MCP-registered tools. `available_tools_prompt_block()` shows them |
| `pyproject.toml` | Add `mcp` extra: `pip install spl-llm[mcp]` installs `mcp>=1.0` |
| `tests/test_mcp_bridge.py` | Tests with a mock MCP server (in-process, no subprocess) |

**Dependency**: the `mcp` Python SDK (`pip install mcp`). Made optional
via extras so `pip install spl-llm` (no MCP) still works.

### Phase 2: MCP server (Hook 3)

[WEN] postpone

| File | Change |
|---|---|
| `spl3/mcp_server.py` | **New module.** MCP server implementation: workflow discovery, `tools/list`, `tools/call` → `execute_program` |
| `spl3/cli.py` | Add `spl3 serve --mcp` command |
| `spl3/mcp_server_registry.py` | **New module.** `~/.spl/mcp_servers/` config management |

### Phase 3: CLI and registry

[WEN] postpone

| File | Change |
|---|---|
| `spl3/cli.py` | Add `spl3 mcp add/list/remove` commands |
| `spl3/linter.py` | Recognize MCP-imported tools so linter doesn't flag them |
| `spl3/splc/` | Transpilers emit MCP config as comments (like Go/TS stubs for AS PYTHON) |

---

## 7. DODA and MCP

DODA — **Design Once, Deploy Anywhere** — is the principle that a `.spl`
file is a logical specification that never changes regardless of runtime,
adapter, or deployment target. MCP integration strengthens DODA because
MCP tools, like LLM adapters, are a deployment-time binding:

- The `.spl` file says `CALL read_file(@path)` — *what* to do.
- Whether `read_file` is an inline Python function, an MCP server tool,
  or a stdlib builtin is resolved at load time — *how* to do it.
- The workflow author writes it once. The deployment decides the tool
  backend.

This is the same separation SPL already applies to LLM providers
(`--adapter ollama` vs `--adapter momagrid`), now extended to
deterministic tools. One workflow, multiple tool backends, zero code
changes — Design Once, Deploy Anywhere.

| What the `.spl` says | What resolves it at deploy time |
|---|---|
| `GENERATE fn()` | `--adapter` flag (ollama / momagrid / openrouter) |
| `CALL tool()` | FunctionRegistry (AS PYTHON / AS MCP / stdlib) |
| `SOLVE expr` | `--kernel-name` flag (python3 / sagemath) |

The `.spl` file is the invariant. Everything else is a deployment
decision.

---

## 8. End-to-end example

A workflow that uses all three tool sources:

```spl
-- MCP server: filesystem access
IMPORT MCP "filesystem" FROM "npx @modelcontextprotocol/server-filesystem ."

-- Inline Python tool
CREATE TOOL_API word_count(text TEXT) RETURNS TEXT AS PYTHON $$
def word_count(text: str) -> str:
    return str(len(text.split()))
$$;

-- LLM prompt template
CREATE FUNCTION summarize(content TEXT) RETURNS TEXT AS $$
  Summarize the following document in 3 bullet points: {content}
$$;

WORKFLOW analyze_document
  INPUT  @filepath TEXT
  OUTPUT @report TEXT
DO
  -- Deterministic: MCP tool reads the file (no Python wrapper needed)
  CALL read_file(@filepath) INTO @content

  -- Deterministic: inline Python counts words
  CALL word_count(@content) INTO @wc

  -- Probabilistic: LLM summarizes
  GENERATE summarize(@content) INTO @summary

  @report := "Words: " + @wc + "\n\nSummary:\n" + @summary
  RETURN @report WITH status = "complete"
END
```

Three tool sources — MCP, inline Python, LLM — unified under one `CALL`
/ `GENERATE` dispatch. The workflow author doesn't care where the tool
lives. Same file runs on any adapter.

---

## 9. Relation to other design docs

| Doc | Connection |
|---|---|
| `spl3-tool-api.md` | MCP extends the `CREATE TOOL_API` construct with a new runtime tag. The 2×2 matrix (design-time × run-time) gains a third column for MCP tools |
| `spl3-workflow-registry.md` | Hook 3 exposes registered workflow radicals as MCP tools — the registry is the catalog, MCP is the transport |
| `spl3-plugin.md` | MCP servers are a standardized alternative to the plugin system; both provide external tool integration |
| `ROADMAP.md` | MCP integration is a natural next step after CREATE TOOL_API |

---

## 10. The unified dispatch table

After MCP integration, `CALL` resolves through this chain:

```
CALL name(args) INTO @var
  │
  ├─ 1. Python tool (FunctionRegistry)
  │     ├── @spl_tool stdlib          (spl/stdlib.py)
  │     ├── --tools file              (user Python module)
  │     ├── ~/.spl/tool_apis/ library (promoted TOOL_API)
  │     ├── inline AS PYTHON          (CREATE TOOL_API in .spl)
  │     └── MCP wrapper               (AS MCP or IMPORT MCP)  ← NEW
  │
  ├─ 2. Built-in function (FunctionRegistry builtins)
  │     └── lower, upper, trim, split_part, ...
  │
  └─ 3. SPL PROCEDURE (FunctionRegistry procedures)
        ├── WORKFLOW / PROCEDURE in current file
        └── ~/.spl/workflows/ registry                        ← NEW
```

All sources converge at step 1 — a Python callable in `FunctionRegistry`.
MCP tools are async callables that wrap `MCPServerPool.call_tool()`.
The dispatch chain in `_exec_call` does not change; it already handles
both sync and async callables via `inspect.iscoroutinefunction()`.

That is the design invariant: **new tool sources register callables, they
do not change the dispatch chain.** This is why MCP integration is a
module addition, not an architecture change.
