# SPL `CREATE TOOL_API` — Design & Implementation

> **Status:** Fully implemented across all three phases (language, generation, library/tooling).

---

## 1. Motivation

### 1.1 The gap

SPL had a **half-complete duality**:

```
Invocation        Definition              Runtime
────────────────  ──────────────────────  ──────────────────────────
GENERATE fn()  ←→ CREATE FUNCTION (NL)    LLM token generation  ✅
CALL tool()    ←→ ???                      Python execution       ❌
```

When `mmd2spl` or `text2spl` generated a workflow that included deterministic
operations (fetch stock data, plot a chart, compute statistics), the LLM had no
choice but to express those operations as `CREATE FUNCTION` prompt templates —
because `CREATE TOOL_API` did not yet exist. The result was probabilistic token
generation being used for operations that have a single correct answer.

### 1.2 The fix: `CREATE TOOL_API`

```spl
CREATE TOOL_API fetch_stock_data(ticker TEXT, years TEXT) RETURNS TEXT AS PYTHON $$
import yfinance as yf, pandas as pd

def fetch_stock_data(ticker: str, years: str) -> str:
    end = pd.Timestamp.today()
    start = end - pd.DateOffset(years=float(years))
    df = yf.download(ticker, start=start, end=end, auto_adjust=True)
    return "error: no data" if df.empty else df.to_csv()
$$;
```

This closes the matrix:

```
Invocation        Definition               Runtime
────────────────  ───────────────────────  ──────────────────────────
GENERATE fn()  ←→ CREATE FUNCTION (NL)     LLM token generation  ✅
CALL tool()    ←→ CREATE TOOL_API (Python) Python execution      ✅
```

---

## 2. The unifying principle

> **SPL integrates deterministic and probabilistic computation in a single unified
> programming model — at both design-time (authoring) and run-time (execution).**

The full 2×2:

|                  | Deterministic                                        | Probabilistic                                        |
|------------------|------------------------------------------------------|------------------------------------------------------|
| **Design-time**  | `CREATE TOOL_API` — LLM *writes* Python code         | `CREATE FUNCTION` — LLM *writes* NL prompt template  |
| **Run-time**     | `CALL` → Python execution (exact, reproducible)      | `GENERATE` → LLM inference (approximate, creative)   |

At design-time, the LLM acts as a **code generator** for both cells. At
run-time, each invocation is dispatched to the appropriate runtime.

No other orchestration framework (LangGraph, AutoGen, CrewAI, DSPy) unifies all
four quadrants in a single coherent syntax.

### 2.1 The regime principle (analogy from physics)

In physics, quantum mechanics is more fundamental than classical mechanics — but
no physicist solves the Schrödinger equation to predict a missile trajectory.
Choosing the wrong regime is not merely inefficient; it is a **category error**.

The same principle applies here:

- **Classical regime** → deterministic, single correct answer → `CREATE TOOL_API`
- **Probabilistic regime** → requires reasoning, judgment, generation → `CREATE FUNCTION`

Using `GENERATE` for `get_ticker_by_index()` is as wrong as solving Schrödinger's
equation for a missile: slower, more expensive, less reliable, and
conceptually misaligned.

### 2.2 Decision criterion for generation

When `mmd2spl` / `text2spl` assigns each operation to a construct, it asks:

> *Does this operation have a single correct answer expressible as code?*
> - **YES** → `CREATE TOOL_API` (classical regime)
> - **NO**  → `CREATE FUNCTION` (probabilistic regime)

**Classical indicators** (default to `TOOL_API`):
external API call, math / statistics, string manipulation, data transformation,
file I/O, sorting / filtering, format conversion — any operation a developer
could unit-test with exact expected values.

**Probabilistic indicators** (use `CREATE FUNCTION`):
summarization, judgment, interpretation, text generation, nuanced classification,
quality evaluation — any operation where "correct" depends on context that
requires reasoning.

---

## 3. Architecture

### 3.1 Self-contained SPL stack

With `CREATE TOOL_API` in place, a single `.spl` file plus a Python interpreter
plus an LLM adapter is sufficient to run any workflow. No external `tools.py`
sidecar is required.

```
┌─────────────────────────────────────────────────────────┐
│                  SPL orchestration layer                │
│    WORKFLOW / WHILE / EVALUATE / CALL / GENERATE        │
└──────────────────────┬──────────────────────────────────┘
                       │ dispatches to
          ┌────────────┴────────────┐
          ▼                         ▼
┌──────────────────┐      ┌──────────────────────┐
│   LLM runtime    │      │   Python runtime     │
│   GENERATE       │      │   CALL               │
│   ─────────────  │      │   ─────────────────  │
│   CREATE         │      │   CREATE             │
│   FUNCTION       │      │   TOOL_API           │
│   (NL prompt)    │      │   (Python code)      │
└──────────────────┘      └──────────────────────┘
```

### 3.2 Library / promotion via registry

Tool API libraries are plain `.spl` files containing only `CREATE TOOL_API`
definitions, stored in `~/.spl/tool_apis/`:

```
~/.spl/tool_apis/
    finance.spl      -- fetch_ohlcv, compute_metrics, ...
    io.spl           -- read_csv, write_parquet, ...
    web.spl          -- scrape_page, rest_post, ...
```

They are loaded automatically before every `spl3 run` invocation via
`spl3/tool_api_registry.py:load_all_into_executor()`.

**Promotion** (`spl3 tool-api promote`, Phase 3 — implemented):

```bash
spl3 tool-api promote cookbook/65_stock_analysis/stock_analysis.spl --name finance
spl3 tool-api list
spl3 tool-api remove finance
```

### 3.3 Inline vs library — when to use each

| Use inline `CREATE TOOL_API` | Use library (`spl3 tool-api promote`) |
|---|---|
| Workflow-specific tool, not reused elsewhere | Tool shared across multiple workflows |
| During development / prototyping | Stable, tested implementation |
| Generated by `mmd2spl` / `text2spl` (always inline first) | After promotion |

---

## 4. Syntax

```
CREATE TOOL_API <name>(<param> <TYPE>, ...) RETURNS <TYPE>
  AS PYTHON $$
<python_body>
$$;
```

- `AS PYTHON` declares the runtime tag. Future runtimes: `AS GO`, `AS TS`.
- `<python_body>` is the full Python implementation, including imports.
- The function named `<name>` in the body is the entry point.
- Every parameter is passed as `str`; return value must also be `str`.
- On failure, return `"error: <message>"` — do not raise unhandled exceptions.
- `$$` is the existing dollar-string token (`TokenType.DOLLAR_DOLLAR`).

### 4.1 File structure order

Generated `.spl` files always follow this order:

```
1. CREATE TOOL_API blocks   -- deterministic Python tools
2. CREATE FUNCTION blocks   -- LLM prompt templates
3. WORKFLOW block
```

### 4.2 Example — stock analysis pipeline (complete, `cookbook/65_stock_analysis`)

```spl
-- Classical regime: deterministic Python tools
CREATE TOOL_API get_item(items TEXT, idx TEXT) RETURNS TEXT AS PYTHON $$
def get_item(items: str, idx: str) -> str:
    return [x.strip() for x in items.split(",")][int(idx)]
$$;

CREATE TOOL_API fetch_ohlcv(ticker TEXT, days TEXT) RETURNS TEXT AS PYTHON $$
import urllib.request, json, datetime

def fetch_ohlcv(ticker: str, days: str) -> str:
    try:
        n = int(days)
        end_ts = int(datetime.datetime.utcnow().timestamp())
        start_ts = end_ts - n * 86400
        url = (
            f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
            f"?period1={start_ts}&period2={end_ts}&interval=1d"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        result = data["chart"]["result"][0]
        times  = result["timestamp"]
        closes = result["indicators"]["quote"][0]["close"]
        rows   = []
        for t, c in zip(times, closes):
            if c is None:
                continue
            date = datetime.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d")
            rows.append(f"{date},{round(c, 2)}")
        return "date,close\n" + "\n".join(rows) if rows else "error: no data"
    except Exception as e:
        return f"error: {e}"
$$;

CREATE TOOL_API compute_metrics(csv_data TEXT) RETURNS TEXT AS PYTHON $$
def compute_metrics(csv_data: str) -> str:
    try:
        lines = [l for l in csv_data.strip().splitlines() if l and not l.startswith("date")]
        closes = [float(l.split(",")[1]) for l in lines if len(l.split(",")) >= 2]
        if len(closes) < 2:
            return "error: insufficient data"
        change = round((closes[-1] - closes[0]) / closes[0] * 100, 2)
        return f"start={closes[0]},end={closes[-1]},high={max(closes)},low={min(closes)},change_pct={change}"
    except Exception as e:
        return f"error: {e}"
$$;

-- Probabilistic regime: LLM reasoning required
CREATE FUNCTION interpret_metrics(ticker TEXT, metrics TEXT) RETURNS TEXT AS $$
  Analyze the price metrics for {ticker} and write a two-sentence summary covering
  trend direction and one key risk. Metrics: {metrics}
$$;

CREATE FUNCTION synthesize_report(tickers TEXT, summaries TEXT) RETURNS TEXT AS $$
  Given per-stock summaries for {tickers}, produce a 3–5 sentence portfolio outlook
  that identifies best/worst performers, correlated risks, and one actionable recommendation.
  Summaries: {summaries}
$$;

WORKFLOW stock_analysis
  INPUT @tickers TEXT := 'AAPL,MSFT,GOOGL'
  INPUT @days TEXT := '30'
  INPUT @max_tickers INTEGER := 3
  OUTPUT @report TEXT
DO
  @i := 0;
  @report := '';
  WHILE @i < @max_tickers DO
    CALL get_item(@tickers, @i) INTO @ticker;       -- deterministic
    CALL fetch_ohlcv(@ticker, @days) INTO @raw_data; -- deterministic
    CALL compute_metrics(@raw_data) INTO @metrics;   -- deterministic
    GENERATE interpret_metrics(@ticker, @metrics) INTO @insight; -- LLM
    @report := @report + @ticker + ': ' + @insight + '\n\n';
    @i := @i + 1;
  END;
  GENERATE synthesize_report(@tickers, @report) INTO @synthesis; -- LLM
  @report := @synthesis;
  RETURN @report WITH status = 'complete';
EXCEPTION
  WHEN BudgetExceeded THEN
    RETURN @report WITH status = 'budget_limit';
END;
```

Run:

```bash
spl3 run cookbook/65_stock_analysis/stock_analysis.spl --adapter ollama -m gemma3
```

---

## 5. Implementation plan & status

### Phase 1 — Language & runtime ✅ Complete

| File | Change |
|------|--------|
| `spl3/ast_nodes.py` | Added `ToolAPINode` dataclass (`name`, `parameters`, `return_type`, `runtime`, `python_body`) |
| `spl3/parser.py` | Overrode `_parse_statement` to detect `CREATE TOOL_API`; added `_parse_tool_api()` method |
| `spl3/executor.py` | `_load_tool_apis(program)` exec()s each body, registers via `self.register_tool()` (not `_GLOBAL_TOOLS`) |
| `tests/test_tool_api.py` | 10 tests — parse, exec, errors, coexistence with GENERATE (all passing) |

**No changes to `spl/` (v2 base).** All additions are in `spl3/` via class inheritance.

### Phase 2 — Generation ✅ Complete

| File | Change |
|------|--------|
| `spl3/cli.py` → `_MMD2SPL_PROMPT` | Added regime classification block, `CREATE TOOL_API` syntax rules, file structure order rule, mixed-regime example (with `{{param}}` escaping for `.format()`) |
| `spl3/text2spl/__init__.py` → `SPL2_SYSTEM_PROMPT` | Full rewrite: regime classification, `CREATE TOOL_API` + `CREATE FUNCTION` side-by-side rules, three examples covering pure-LLM, mixed-regime, and exception handling |

### Phase 3 — Library / promotion ✅ Complete

| Component | Change |
|-----------|--------|
| `spl3/tool_api_registry.py` | New module: file-level (`list_libraries()`, `promote()`, `remove()`, `load_all_into_executor()`) + **function-level tool catalog** (`ToolParam`, `ToolSignature`, `list_tools()`, `available_tools_prompt_block()`, `_parse_tools_from_file()`, `_stdlib_tools()`) — registry at `~/.spl/tool_apis/` |
| `spl3/executor.py` → `execute_program` | Loads library tools first (from registry), then inline TOOL_API blocks (inline wins on collision) |
| `spl3/cli.py` | Added `spl3 tool-api` command group with `list [--tools] [--stdlib]`, `promote`, `remove` subcommands |
| `spl3/text2spl/__init__.py` → `_build_system_prompt()` | Injects `available_tools_prompt_block()` into system prompt before `== STRICT RULES ==` anchor |
| `spl3/cli.py` → `cmd_mmd2spl` | Injects `available_tools_prompt_block()` into `mmd2spl` prompt before `== MANDATORY SPL 3.0 CONVENTIONS` anchor |

### Additional completions

| Component | Change |
|-----------|--------|
| `spl3/linter.py` | Collects `ToolAPINode` names; adds to `all_known` CALL targets so linter does not flag TOOL_API CALLs as undefined |
| `spl3/splc/transpiler_langgraph.py` | Collects `tool_apis`; `_gen_tool_apis()` emits Python bodies verbatim at module scope; `_emit_call_stmt()` routes CALL to TOOL_API via direct Python call (uses `_expr_py` for args, not `_spl_arg`); wired into all four node generators |
| `spl3/splc/transpiler_go.py` | Collects `tool_apis`; `_gen_tool_api_stub()` emits Go stub with Python body as `//` comment; CALL dispatch routes to stub |
| `spl3/splc/transpiler_ts.py` | Same as Go: TS stub function + Python reference comment; CALL dispatch routes to sync stub (no `await`) |
| `spl3/spl2mmd.py` | Added `"toolapi"` green style (`#d1fae5`); pre-pass collects `ToolAPINode` names; `_stmt()` renders TOOL_API-backed CALL nodes in green vs amber for sub-workflow CALLs and blue for GENERATE |
| `cookbook/65_stock_analysis/` | New recipe: canonical 2×2 mixed-regime demo (`fetch_ohlcv`, `compute_metrics`, `get_item` as TOOL_API + `interpret_metrics`, `synthesize_report` as CREATE FUNCTION); added to `cookbook_catalog.json` |

---

## 6. Runtime detail

### 6.1 Load-time registration

```python
# spl3/executor.py
def _load_tool_apis(self, program) -> None:
    """exec() each CREATE TOOL_API body and register the function."""
    for stmt in program.statements:
        if not isinstance(stmt, ToolAPINode):
            continue
        if stmt.runtime != "PYTHON":
            _log.warning("CREATE TOOL_API '%s': runtime '%s' not supported yet — skipped", ...)
            continue
        namespace: dict = {}
        try:
            exec(compile(stmt.python_body, f"<tool_api:{stmt.name}>", "exec"), namespace)
        except Exception as exc:
            raise RuntimeError(
                f"CREATE TOOL_API '{stmt.name}': failed to compile/exec body — {exc}"
            ) from exc
        fn = namespace.get(stmt.name)
        if fn is None:
            raise RuntimeError(
                f"CREATE TOOL_API '{stmt.name}': body must define a Python function "
                f"named '{stmt.name}' at the top level."
            )
        # Register in this executor's FunctionRegistry — NOT _GLOBAL_TOOLS
        # (_GLOBAL_TOOLS is snapshotted at __init__ time and is too late)
        self.register_tool(stmt.name, fn)
        _log.debug("Registered TOOL_API '%s' -> %r", stmt.name, fn)
```

> **Critical design note:** The original draft used `_GLOBAL_TOOLS[stmt.name] = fn`,
> which silently failed because `_GLOBAL_TOOLS` is snapshotted at executor `__init__` time.
> The fix is `self.register_tool()`, which writes into the per-executor `FunctionRegistry`
> instance that `CALL` dispatch reads from at runtime.

### 6.2 Execution order

```python
async def execute_program(self, analysis, params=None):
    # 1. Library tools from ~/.spl/tool_apis/ (promoted shared libraries)
    from spl3.tool_api_registry import load_all_into_executor
    load_all_into_executor(self)

    # 2. Inline TOOL_API blocks from the current .spl file (override library tools)
    self._load_tool_apis(analysis.ast)

    return await super().execute_program(analysis, params=params)
```

Load order is **library first, inline second** — so inline definitions always win
on name collision. This allows a workflow to shadow a library tool with a
workflow-specific override.

### 6.3 Security model

`exec()` runs in an unrestricted namespace — same trust level as `tools.py` loaded
via `--tools`. Both require the user to supply the code; no sandbox is needed for
the local-execution use case.

---

## 7. Token changes

`CREATE TOOL_API` is parsed using existing tokens:
- `TokenType.CREATE` (already a keyword)
- `tool_api` — treated as a plain `IDENTIFIER` token (no new keywords needed)
- `AS`, `PYTHON` — also plain identifiers (no keyword conflict)
- `TokenType.DOLLAR_DOLLAR` + `TokenType.STRING` — already used by `CREATE FUNCTION`

**Zero changes to the lexer / token types.**

---

## 8. Backward compatibility

- All existing `.spl` files parse and run unchanged.
- `CREATE TOOL_API` is additive — files that don't use it are unaffected.
- `tools.py` loaded via `--tools` continues to work exactly as before; `CREATE TOOL_API`
  and `--tools` tools are both registered in the `FunctionRegistry` and are
  interchangeable from `CALL`'s perspective.

---

## 9. `splc` transpiler behaviour by target

When compiling a `.spl` file that contains `CREATE TOOL_API` blocks:

### 9.1 LangGraph (Python output)

Python is the native runtime — TOOL_API bodies are emitted **verbatim** as
module-level helper functions. No translation needed.

```python
# ── Tool APIs (mirrors CREATE TOOL_API blocks in .spl) ──────────────────

# SPL: CREATE TOOL_API fetch_ohlcv
import urllib.request, json, datetime

def fetch_ohlcv(ticker: str, days: str) -> str:
    ...

# SPL: CREATE TOOL_API compute_metrics
def compute_metrics(csv_data: str) -> str:
    ...
```

CALL dispatch routes to direct Python calls:

```python
# SPL: CALL fetch_ohlcv(@ticker, @days) INTO @raw_data
raw_data = fetch_ohlcv(state["ticker"], state["days"])
```

### 9.2 Go output

Go cannot execute Python. Each TOOL_API becomes a **Go stub function** with
the Python reference implementation as a `//` comment block. The stub compiles
and returns a clear error until the implementor ports the logic.

```go
// SPL: CREATE TOOL_API fetch_ohlcv — Python reference implementation.
// Port the logic below to Go for production use.
//
// Python reference:
//   import urllib.request, json, datetime
//   def fetch_ohlcv(ticker: str, days: str) -> str:
//       ...
func fetchOhlcv(ticker string, days string) (string, error) {
  // TODO: implement in Go (see Python reference above)
  return "", fmt.Errorf("TOOL_API fetch_ohlcv: not yet ported to Go")
}
```

CALL dispatch:

```go
// SPL: CALL fetch_ohlcv(@ticker, @days) INTO @raw_data
raw_data, err = fetchOhlcv(ticker, days)
if err != nil { return "", "error", 0, err }
```

### 9.3 TypeScript output

Same pattern as Go — TS stub functions with Python reference as `//` comments.

```typescript
// SPL: CREATE TOOL_API fetch_ohlcv — Python reference implementation.
// Port the logic below to TypeScript for production use.
//
// Python reference:
//   import urllib.request, json, datetime
//   def fetch_ohlcv(ticker: str, days: str) -> str:
//       ...
function fetchOhlcv(ticker: string, days: string): string {
  // TODO: implement in TypeScript (see Python reference above)
  throw new Error('TOOL_API fetch_ohlcv: not yet ported to TypeScript');
}
```

---

## 10. `spl2mmd` visual distinction

The Mermaid diagram generator (`spl3/spl2mmd.py`) renders TOOL_API-backed CALL
nodes distinctly from both LLM GENERATE nodes and sub-workflow CALL nodes:

| Node type | Shape | Colour | Class |
|---|---|---|---|
| `GENERATE fn()` | parallelogram `[/ /]` | blue `#dbeafe` | `llm` |
| `CALL sub_workflow()` | subroutine `[[ ]]` | amber `#fef3c7` | `proc` |
| `CALL tool_api()` | subroutine `[[ ]]` | green `#d1fae5` | `toolapi` |

The pre-pass in `ASTToMermaid.convert()` collects all `ToolAPINode` names from
the program and stores them in `self._tool_api_names`. The `_stmt()` handler for
`CallStatement` checks whether `stmt.procedure_name in self._tool_api_names` and
assigns the `toolapi` class accordingly.

Example output for `cookbook/65_stock_analysis`:

```mermaid
flowchart TD
    ...
    SUB5[["TOOL_API get_item(@tickers, @i) -> @ticker"]]
    SUB6[["TOOL_API fetch_ohlcv(@ticker, @days) -> @raw_data"]]
    SUB7[["TOOL_API compute_metrics(@raw_data) -> @metrics"]]
    GEN8[/"GENERATE interpret_metrics(@ticker, @metrics) -> @insight"/]
    ...
    class SUB5 toolapi
    class SUB6 toolapi
    class SUB7 toolapi
    class GEN8 llm
    classDef toolapi fill:#d1fae5,stroke:#10b981,color:#064e3b
    classDef llm fill:#dbeafe,stroke:#3b82f6,color:#1e3a5f
```

---

## 11. `spl3 tool-api` CLI commands

```
spl3 tool-api --help

Commands:
  list     List registered TOOL_API libraries (or functions with --tools)
  promote  Add a .spl file to the TOOL_API library
  remove   Remove a library from the registry
```

### Usage

```bash
# List all registered libraries (file-level view)
spl3 tool-api list

# List all known tool functions — stdlib + all registered libraries
spl3 tool-api list --tools

# Only show registered library tools (no stdlib)
spl3 tool-api list --tools --no-stdlib

# Show stdlib tools only (useful for checking what's always available)
spl3 tool-api list --tools --stdlib

# Promote a .spl file (copies to ~/.spl/tool_apis/finance.spl)
spl3 tool-api promote cookbook/65_stock_analysis/stock_analysis.spl --name finance

# Overwrite an existing library entry
spl3 tool-api promote updated_finance.spl --name finance --force

# Remove a library
spl3 tool-api remove finance
```

`list` file-level output:

```
TOOL_API libraries in /home/user/.spl/tool_apis:

  finance                         3 tool(s)  (5,343 bytes)  /home/user/.spl/tool_apis/finance.spl
```

`list --tools` function-level output:

```
All known TOOL_API functions (stdlib + registered libraries):

  [stdlib] web_search(@query TEXT) RETURNS TEXT
  [stdlib] http_get(@url TEXT) RETURNS TEXT
  [stdlib] read_file(@path TEXT) RETURNS TEXT
  ... (65 total)

  [finance] fetch_ohlcv(@ticker TEXT, @days TEXT) RETURNS TEXT
  [finance] compute_metrics(@csv_data TEXT) RETURNS TEXT
  [finance] get_item(@items TEXT, @idx TEXT) RETURNS TEXT
```

---

## 12. `spl3/tool_api_registry.py` module API

### 12.1 File-level API

```python
from spl3.tool_api_registry import (
    registry_dir,           # → Path  ~/.spl/tool_apis/ (creates if needed)
    list_libraries,         # → list[dict]  name/path/size/tool_count/tools
    promote,                # (source_path, name=None) → Path
    remove,                 # (name) → bool
    load_all_into_executor, # (executor) → int  (number of library files loaded)
)
```

`load_all_into_executor` is called automatically from `SPL3Executor.execute_program()`
before any workflow runs. External callers rarely need to invoke it directly.

### 12.2 Function-level catalog API

```python
from spl3.tool_api_registry import (
    list_tools,                  # (include_stdlib=True) → list[ToolSignature]
    available_tools_prompt_block, # (include_stdlib=True) → str
)
from spl3.tool_api_registry import ToolSignature, ToolParam
```

`list_tools()` returns all known TOOL_API functions — stdlib built-ins (via
`inspect.signature()` on `spl/tools.py` functions) plus every function defined
in any registered `~/.spl/tool_apis/*.spl` library.

`available_tools_prompt_block()` formats the catalog as a multi-line string
injected into `text2spl` and `mmd2spl` system prompts (see §13).

### 12.3 Data model

```python
@dataclass
class ToolParam:
    name: str
    param_type: str = "TEXT"   # TEXT | INTEGER | FLOAT | BOOL

@dataclass
class ToolSignature:
    name: str
    parameters: list[ToolParam]
    return_type: str = "TEXT"
    source: str = "stdlib"       # "stdlib" or library stem, e.g. "finance"
    source_file: str | None = None
    python_body: str = ""

    def spl_signature(self) -> str:
        # → "fetch_ohlcv(@ticker TEXT, @days TEXT) RETURNS TEXT"
        ...
```

---

## 13. Lookup-before-generate (generation catalog)

### 13.1 The problem

Without this feature, every `text2spl` or `mmd2spl` invocation would regenerate
`CREATE TOOL_API` blocks for tools that already exist — either in the stdlib
(`web_search`, `http_get`, …) or in a promoted user library (`fetch_ohlcv`, …).
The LLM had no way to know what was available.

### 13.2 The solution: inject known tools before asking the LLM to generate

The `available_tools_prompt_block()` function builds a formatted catalog of every
known TOOL_API function and injects it into both generation system prompts.
The injected block instructs the LLM to use `CALL` directly for listed operations
and only emit `CREATE TOOL_API` for operations NOT already covered.

#### Injected block format

```
== AVAILABLE TOOL_API FUNCTIONS ==

The following deterministic tools already exist. When you need one of
these operations, use CALL directly — do NOT generate a new CREATE TOOL_API.
Only generate CREATE TOOL_API for operations NOT listed here.

Stdlib tools (built-in, always available):
  CALL web_search(@query TEXT) RETURNS TEXT
  CALL http_get(@url TEXT) RETURNS TEXT
  CALL read_file(@path TEXT) RETURNS TEXT
  ...

User library tools (~/.spl/tool_apis/):
  # library: finance.spl
  CALL fetch_ohlcv(@ticker TEXT, @days TEXT) RETURNS TEXT
  CALL compute_metrics(@csv_data TEXT) RETURNS TEXT
  CALL get_item(@items TEXT, @idx TEXT) RETURNS TEXT
```

### 13.3 Injection points

The block is injected **after** regime classification rules (so the LLM first
understands the classical/probabilistic distinction) and **before** strict syntax
rules (so it knows what already exists before seeing what it must generate).

#### `text2spl` — `spl3/text2spl/__init__.py`

```python
def _build_system_prompt(self, description: str) -> str:
    system = SPL2_SYSTEM_PROMPT   # base prompt (already formatted — no {vars})
    # Inject tools catalog at anchor point
    try:
        from spl3.tool_api_registry import available_tools_prompt_block
        tools_block = available_tools_prompt_block()
        if tools_block:
            _ANCHOR = "== STRICT RULES =="
            if _ANCHOR in system:
                system = system.replace(_ANCHOR, tools_block + "\n" + _ANCHOR, 1)
    except Exception:
        pass   # non-fatal; LLM proceeds without catalog
    # Code-RAG example replacement (as before) …
```

#### `mmd2spl` — `spl3/cli.py` → `cmd_mmd2spl`

```python
# Call .format() FIRST (fills {mermaid}), THEN inject tools block via .replace()
prompt_text = _MMD2SPL_PROMPT.format(mermaid=mermaid_content)
try:
    from spl3.tool_api_registry import available_tools_prompt_block
    _tools_block = available_tools_prompt_block()
    if _tools_block:
        _ANCHOR = "== MANDATORY SPL 3.0 CONVENTIONS"
        if _ANCHOR in prompt_text:
            prompt_text = prompt_text.replace(
                _ANCHOR, _tools_block + "\n" + _ANCHOR, 1,
            )
except Exception:
    pass
```

> **Why `.replace()` after `.format()`?** The tools block itself may contain
> `{` or `}` characters (Python dict literals, template strings), which would
> break `.format()`. Injecting via `.replace()` on the already-formatted string
> avoids this escaping problem entirely.

### 13.4 The dual-purpose registry

`spl3/tool_api_registry.py` serves two distinct roles:

| Role | Triggered by | Purpose |
|------|-------------|---------|
| **Generation** | `text2spl`, `mmd2spl` | Tell the LLM what already exists → reuse via `CALL` |
| **Runtime** | `execute_program()` | Load library tools into executor → available for `CALL` dispatch |

Both roles are served from the same source of truth: `~/.spl/tool_apis/*.spl`
files plus the stdlib tool registry in `spl/tools.py`.

### 13.5 Stdlib introspection

Stdlib tools (functions decorated with `@spl_tool` in `spl/tools.py`) are
enumerated via `inspect.signature()` — no modification to stdlib code is
required. This gives accurate parameter names and types for catalog entries.

```python
def _stdlib_tools() -> list[ToolSignature]:
    from spl.tools import get_global_tools
    stdlib = get_global_tools()
    result = []
    for name, fn in sorted(stdlib.items()):
        sig = inspect.signature(fn)
        params = [
            ToolParam(name=pname, param_type="TEXT")
            for pname, p in sig.parameters.items()
            if pname not in ("self", "cls", "kwargs", "args")
            and p.kind not in (VAR_POSITIONAL, VAR_KEYWORD)
        ]
        result.append(ToolSignature(name=name, parameters=params, source="stdlib"))
    return result
```

---

## Appendix A — How the SPL runtime is constructed

### A.1 It is entirely Python

The package `spl-llm` (installed as the `spl3` CLI) is a **pure Python application**
running on CPython 3.11+. There is no compiled native code, no JVM, no separate
runtime process.

### A.2 Full stack, layer by layer

```
┌──────────────────────────────────────────────────────────────┐
│  spl3 CLI  (Click app — spl3/cli.py)                         │
│  entry point: pyproject.toml  spl3 = "spl3.cli:main"         │
└──────────────────────┬───────────────────────────────────────┘
                       │ reads .spl source text
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  Lexer  (spl/lexer.py)  ~368 lines                           │
│  Pure Python — regex + character scan                        │
│  .spl text  →  list[Token]                                   │
└──────────────────────┬───────────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  Parser  (spl/parser.py ← spl3/parser.py)  ~1771 + 369 lines │
│  Hand-written recursive descent — no parser generator used   │
│  list[Token]  →  AST (Python dataclass tree)                 │
└──────────────────────┬───────────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  Analyzer  (spl/analyzer.py)  ~382 lines                     │
│  Semantic checks — undefined vars, unreachable code, etc.    │
│  AST  →  AnalysisResult (warnings + validated AST)           │
└──────────────────────┬───────────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  Executor  (spl/executor.py ← spl3/executor.py)  ~1453+510 L │
│  asyncio-based tree-walk interpreter                         │
│  Walks AST nodes, dispatches each statement:                 │
│    GENERATE  →  adapter.generate()     [LLM call, async]     │
│    CALL      →  FunctionRegistry       [Python fn, sync/async]│
│    WHILE     →  Python while loop                            │
│    EVALUATE  →  string match or LLM judge                    │
│    RETURN    →  raises WorkflowComplete sentinel             │
└───────────┬──────────────────────┬───────────────────────────┘
            │                      │
            ▼                      ▼
┌───────────────────┐  ┌───────────────────────────────────────┐
│  LLMAdapter       │  │  FunctionRegistry  (spl/functions.py) │
│  (spl/adapters/)  │  │                                       │
│                   │  │  get_tool(name) → Python callable     │
│  Abstract base +  │  │  Populated at executor.__init__ from: │
│  14 concrete impls│  │    spl/stdlib.py     (@spl_tool deco) │
│                   │  │    --tools file      (@spl_tool deco) │
│  ollama           │  │    ~/.spl/tool_apis/ (registry libs)  │
│  anthropic        │  │    CREATE TOOL_API   (exec() body) ←NEW
│  openrouter       │  │                                       │
│  claude_cli       │  │  call_builtin(name, *args)            │
│  momagrid + 9 more│  │  get_procedure(name) → AST node       │
│                   │  └───────────────────────────────────────┘
│  generate()       │
│   → httpx POST    │
│   → subprocess    │
│   → GenerationResult(content: str, ...)
└───────────────────┘
```

### A.3 The two inheritance chains

The rule "never modify `spl/` to add v3 features" is enforced through Python
class inheritance:

```python
# spl3/parser.py
class SPL3Parser(SPL2Parser): ...   # SPL2Parser = spl/parser.py:Parser

# spl3/executor.py
class SPL3Executor(SPL2Executor): ... # SPL2Executor = spl/executor.py:Executor
```

SPL 2.0 (`spl/`) is the stable base. SPL 3.0 (`spl3/`) overrides specific
methods to add `IMPORT`, `CALL PARALLEL`, `CREATE TOOL_API`, numeric type
coercion — without touching v2.

### A.4 What "running a .spl file" looks like in Python

```python
source = Path("workflow.spl").read_text()

# 1. Lex — pure Python string scanning
tokens = Lexer(source).tokenize()           # → list[Token]

# 2. Parse — recursive descent, produces Python dataclass tree
program = SPL3Parser(tokens).parse()        # → Program(statements=[...])

# 3. Analyze — semantic validation
analysis = Analyzer().analyze(program)      # → AnalysisResult

# 4. Execute — asyncio tree-walk interpreter
executor = SPL3Executor(adapter=get_adapter("ollama"))
results = asyncio.run(
    executor.execute_program(analysis)      # → list[WorkflowResult]
)
```

### A.5 What each statement compiles to at runtime

| SPL statement | Python equivalent |
|---|---|
| `GENERATE fn(@var) INTO @out` | `prompt = registry.render("fn", state); result = await adapter.generate(prompt); state["out"] = result.content` |
| `CALL tool(@a, @b) INTO @out` | `fn = registry.get_tool("tool"); state["out"] = str(fn(state["a"], state["b"]))` |
| `WHILE @i < @max DO` | `while int(state["i"]) < int(state["max"]):` |
| `EVALUATE @v WHEN contains("x")` | `if "x" in state["v"]:` |
| `RETURN @r WITH status="complete"` | `raise WorkflowComplete(state["r"], status="complete")` |
| `CALL PARALLEL a(), b()` | `await asyncio.gather(run_a(), run_b())` |
| `CREATE TOOL_API f() AS PYTHON $$` | `exec(body, ns); registry.register_tool("f", ns["f"])` |

### A.6 What is NOT Python

- The `.spl` source files (the SPL language itself)
- The LLM weights on whatever server the adapter points to
- The `splc` compilation *output* (Go, TypeScript, LangGraph Python) — the compiler
  itself is Python, but what it produces is target-language code

**In summary**: the SPL runtime is a Python interpreter for the SPL language —
a ~2,000-line hand-written recursive-descent parser and async tree-walking
executor, using Python `asyncio` for concurrent branch dispatch and
`httpx`/subprocess for LLM I/O.
