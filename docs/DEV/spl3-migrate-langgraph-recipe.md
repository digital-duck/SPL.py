# Curating LangGraph Recipes → SPL Agentic Workflow Registry

## Motivation

[LangGraph](https://github.com/langchain-ai/langgraph) is the leading production-grade
multi-agent orchestration framework and the primary reference implementation for
graph-based agentic patterns. Its tutorial and example catalog is the de-facto
curriculum for agentic AI engineers.

Where PocketFlow exposes *node-level* workflow primitives (shared across the full
LLM-framework ecosystem), LangGraph exposes *graph-level* orchestration patterns:
conditional edge routing, stateful subgraph composition, durable interrupt/resume,
and memory-across-conversations. These are the patterns SPL most needs to validate its
expressiveness and grow its registry.

This migration serves three purposes:

1. **Expand SPL pattern coverage.** LangGraph recipes exercise patterns not seen in
   PocketFlow: plan-and-execute agents, adaptive RAG, durable HITL, cross-turn memory,
   subgraph composition, and domain-specific pipelines (SQL, code gen, research). Porting
   them directly validates — and stress-tests — the SPL constructs built to cover them:
   `EVALUATE`, `CALL PARALLEL`, `CALL wait_for_approval`, `--persistence`, and `IMPORT`.

2. **Validate the persistence layer.** LangGraph's most distinctive feature —
   `interrupt()` / `checkpointer` durable execution — maps directly onto the
   `--persistence sqlite|postgres|dbos` layer implemented in SPL 3.0. Migrating
   LangGraph HITL and memory recipes will be the first real-world test of that layer
   end-to-end.

3. **Build the SPL agentic workflow registry.** Each migrated recipe is a registered,
   reusable workflow: `IMPORT 'langgraph/react_agent'` pulls in a battle-tested
   ReAct loop; `CALL plan_and_execute(@task) INTO @result` composes a plan–execute
   pipeline into a larger workflow. The registry is SPL's strategic moat — the richer
   it is, the lower the adoption barrier.

### Relationship to the PocketFlow migration

| Dimension | PocketFlow | LangGraph |
|-----------|-----------|-----------|
| Workflow model | Node graph (Python) | StateGraph with typed state |
| Primary patterns | ReAct, RAG, batch, supervisor | Same + durable HITL, memory, subgraphs |
| Source format | `.py` files | `.ipynb` notebooks + `.py` modules |
| Tool registration | `@spl_tool` / `utils.py` | `ToolNode` / `@tool` |
| Persistence | None native | `MemorySaver`, `SqliteSaver`, `interrupt()` |
| SPL mapping difficulty | Low–medium | Medium–high (state schema, interrupt) |
| New SPL patterns exercised | tool_api, while, evaluate, parallel | + persistence HITL, import/compose |

---

## Goal

Curate the LangGraph tutorial/example library into a dedicated **`cookbook-langgraph/`**
folder. Each recipe is a self-contained SPL workflow that:
- Demonstrates one primary LangGraph pattern translated to SPL
- Runs with any SPL adapter (`ollama`, `claude_cli`, `openrouter`, `momagrid`)
- Can be `IMPORT`-ed and `CALL`-ed by other workflows
- Is registered in the SPL local registry via `spl3 registry push`

```
~/projects/digital-duck/SPL.py/
├── cookbook/                     # original SPL recipes (01_*…77_*)
├── cookbook-pocketflow/          # PocketFlow migrations (001_*…064_*)
└── cookbook-langgraph/           # LangGraph migrations (001_*…)
```

Each recipe directory:

```
cookbook-langgraph/
└── 001_react_agent/
    ├── react_agent.spl           # migrated SPL workflow (the invariant)
    ├── tools.spl                 # CREATE TOOL_API helpers
    ├── README.md                 # pattern description + attribution
    └── migrate/
        ├── S1-*-spec.md          # splc describe output (notebook → spec)
        ├── S2-*.mmd              # text2mmd topology
        └── S3-*.spl              # raw mmd2spl before polish
```

`README.md` attribution header template:

```markdown
# 001 — ReAct Agent  *(migrated from LangGraph)*

**Source:** [langgraph/examples/react-agent](https://github.com/langchain-ai/langgraph/tree/main/examples)
**LangGraph pattern:** ReAct tool-call loop with ToolNode
**Difficulty:** 3/10
**SPL pattern:** `WHILE` + `EVALUATE tool_call` + `CALL tool` + `GENERATE`
**Persistence:** not required (stateless)
```

---

## Source Repositories

```bash
git clone https://github.com/langchain-ai/langgraph \
  ~/projects/langchain-ai/langgraph
```

| Source | What to mine |
|--------|-------------|
| `langgraph/examples/` | Jupyter notebook implementations of core patterns |
| `langgraph/docs/docs/tutorials/` | narrative-first notebooks with full explanations |
| `langchain-ai/langgraph-example` | standalone deployable agent templates |
| `langchain-ai/langchain/cookbook/` | notebooks that exercise LangGraph as a backend |

Notebook locations for the priority recipes:

| Recipe | Notebook path |
|--------|--------------|
| react_agent | `examples/react-agent/react_agent.ipynb` |
| plan_and_execute | `examples/plan-and-execute/plan-and-execute.ipynb` |
| reflection | `docs/docs/tutorials/reflection/reflection.ipynb` |
| self_corrective_rag | `docs/docs/tutorials/rag/langgraph_self_rag.ipynb` |
| multi_agent_supervisor | `docs/docs/tutorials/multi_agent/agent_supervisor.ipynb` |
| human_in_loop | `docs/docs/tutorials/human_in_the_loop/` |
| memory_agent | `docs/docs/tutorials/cross-thread-persistence.ipynb` |
| subgraph | `docs/docs/tutorials/subgraph.ipynb` |
| map_reduce | `docs/docs/tutorials/map-reduce.ipynb` |
| adaptive_rag | `docs/docs/tutorials/rag/langgraph_adaptive_rag.ipynb` |

---

## Numbering Scheme

LangGraph patterns cluster into five tiers, ordered by SPL translation complexity
and dependency on advanced features.

| Range | Tier | Focus |
|-------|------|-------|
| `001–009` | Core single-agent | ReAct, RAG, reflection, planning — validate S1→S3 pipeline on LangGraph source |
| `010–019` | Multi-agent | Supervisor, collaboration, handoff, debate |
| `020–029` | Memory & persistence | Cross-turn memory, durable HITL, time travel |
| `030–039` | Composition | Subgraph registry, map-reduce, streaming (adapter layer) |
| `040–049` | Domain pipelines | SQL agent, code gen, research (STORM), essay writer |
| `050–059` | Production | Guardrails, observability, deployment templates |

---

## Full Recipe Inventory

### Tier 1 — Core Single-Agent (001–009)

These recipes validate that the S1→S3 pipeline works on LangGraph `.ipynb` source.
Most patterns already exist in PocketFlow — the value here is a second, richer
implementation to cross-validate SPL's translation quality.

| # | Recipe | LangGraph pattern | SPL construct(s) | Difficulty | Status |
|---|--------|------------------|-----------------|-----------|--------|
| 001 | react_agent | ReAct tool-call loop + ToolNode | `WHILE` + `EVALUATE` + `CALL tool` | 3/10 | migrate |
| 002 | reflection | generate → critique → revise | `WHILE quality_gate` | 3/10 | migrate |
| 003 | plan_and_execute | planner sub-graph → executor | `CALL plan` + `CALL execute` | 4/10 | migrate |
| 004 | basic_rag | retrieve → grade → answer | `CALL embed` + `EVALUATE grade` | 3/10 | migrate |
| 005 | sql_agent | nl → sql → validate → execute | `CREATE TOOL_API` DB tools | 5/10 | migrate |
| 006 | structured_output | extraction into typed schema | `GENERATE` + `CALL parse_json` | 3/10 | migrate |
| 007 | code_generation | generate code → run → fix | `WHILE` + `CALL run_python` + `ASSERT` | 5/10 | migrate |
| 008 | essay_writer | outline → section generator → critic | multi-step `CALL` chain | 4/10 | migrate |
| 009 | chat_with_memory | single-turn memory retrieval | `CALL memory_get` + `CALL memory_put` | 3/10 | migrate |

### Tier 2 — Multi-Agent (010–019)

LangGraph's flagship use case. These directly exercise `CALL PARALLEL`, `EVALUATE`
routing, and sub-workflow composition.

| # | Recipe | LangGraph pattern | SPL construct(s) | Difficulty | Status |
|---|--------|------------------|-----------------|-----------|--------|
| 010 | supervisor | supervisor routes to N worker subgraphs | `EVALUATE` → multi-way `CALL` | 5/10 | migrate |
| 011 | agent_collab | two agents share scratchpad | `CALL PARALLEL` + `CALL merge` | 5/10 | migrate |
| 012 | network | peer-to-peer agent handoff mesh | chained `CALL` + `EVALUATE handoff` | 6/10 | migrate |
| 013 | debate | adversarial 2-agent + judge arbiter | `WHILE rounds` + `EVALUATE judge` | 5/10 | migrate |
| 014 | research_team | researcher + writer + critic loop | `WHILE quality_gate` + `CALL PARALLEL` | 6/10 | migrate |
| 015 | customer_support | domain router → specialist agents | `EVALUATE domain` → `CALL specialist` | 5/10 | migrate |
| 016 | extraction_team | extractor + reviewer + refinement | `WHILE approved` + `CALL extract` | 5/10 | migrate |

### Tier 3 — Memory & Persistence (020–029)

The most important tier for validating SPL's `--persistence` layer. LangGraph uses
`MemorySaver`, `SqliteSaver`, and `interrupt()` — the exact patterns the persistence
backend was designed to support.

| # | Recipe | LangGraph pattern | SPL construct(s) | Difficulty | Status |
|---|--------|------------------|-----------------|-----------|--------|
| 020 | cross_turn_memory | `MemorySaver` across conversations | `--persistence sqlite` + `@memory` | 5/10 | migrate |
| 021 | hitl_approval | `interrupt()` await human input | `CALL wait_for_approval` + `--persistence` | 6/10 | ⚠️ needs persistence |
| 022 | hitl_edit | interrupt + human edits state before resume | `CALL wait_for_approval` + merge | 6/10 | ⚠️ needs persistence |
| 023 | hitl_review_code | code → interrupt for review → continue | `CALL run_python` + HITL gate | 6/10 | ⚠️ needs persistence |
| 024 | durable_agent | crash-safe long-running research agent | `--persistence sqlite --workflow-id` | 7/10 | ⚠️ needs persistence |
| 025 | time_travel | rollback to past checkpoint + re-run | step-level replay via persistence | 8/10 | deferred |

> **Note:** Recipes 021–024 depend on the `--persistence` layer (implemented in
> `spl3/persistence/`). Use `--persistence sqlite` for local runs; `--persistence postgres`
> for production. Recipe 025 (time_travel) requires step-level checkpoint replay beyond
> current persistence semantics — deferred.

### Tier 4 — Composition (030–039)

Exercises SPL's `IMPORT`, registry-based `CALL`, and `CALL PARALLEL`.

| # | Recipe | LangGraph pattern | SPL construct(s) | Difficulty | Status |
|---|--------|------------------|-----------------|-----------|--------|
| 030 | subgraph_compose | nest workflow A inside workflow B | `IMPORT 'langgraph/react_agent'` + `CALL` | 5/10 | migrate |
| 031 | map_reduce | parallel fan-out over list → aggregate | `CALL PARALLEL` + reduce `CALL` | 4/10 | migrate |
| 032 | dynamic_breakpoint | runtime-computed interrupt condition | `EVALUATE condition` + `CALL wait_for_approval` | 7/10 | ⚠️ needs persistence |
| 033 | send_api | imperative branch dispatch at runtime | `EVALUATE` multi-way routing | 5/10 | migrate |
| 034 | configuration | runtime config injection via `--param` | SPL `INPUT` params + `--param` flags | 3/10 | migrate |

### Tier 5 — Domain Pipelines (040–049)

Rich end-to-end workflows with heavy tool use. These are the best candidates for
populating the registry with reusable named patterns.

| # | Recipe | LangGraph pattern | SPL construct(s) | Difficulty | Status |
|---|--------|------------------|-----------------|-----------|--------|
| 040 | adaptive_rag | query → route → retrieve or search → grade → answer | `EVALUATE route` + `CALL PARALLEL` | 6/10 | migrate |
| 041 | self_corrective_rag | retrieve → grade → rewrite if bad → answer | `WHILE grade_ok` + `CALL search` | 6/10 | migrate |
| 042 | corrective_rag | retrieval score → web fallback | `EVALUATE score` + `CALL search_web` | 5/10 | migrate |
| 043 | storm_research | multi-perspective research + synthesis | `CALL PARALLEL perspectives` + reduce | 7/10 | migrate |
| 044 | code_act | code generation + execution + self-repair | `WHILE tests_pass` + `CALL run_python` | 6/10 | migrate |
| 045 | lead_generation | scrape → enrich → score → draft email | pipeline `CALL` chain with tools | 6/10 | migrate |
| 046 | web_voyager | browser-use: screenshot + action loop | `WHILE done` + `CALL browser_action` | 7/10 | migrate |
| 047 | llm_compiler | parallel task scheduling + join | `CALL PARALLEL dynamic` + DAG merge | 7/10 | migrate |

### Tier 6 — Production (050–059)

| # | Recipe | Pattern | Status |
|---|--------|---------|--------|
| 050 | guardrail_input | safety check before main agent | `EVALUATE safe` before `CALL agent` | migrate |
| 051 | guardrail_output | post-generation safety filter | `EVALUATE safe` after `GENERATE` | migrate |
| 052 | observability | trace step inputs/outputs | `--log-prompts` + structured logging | migrate |
| 053 | retry_on_error | `EXCEPTION WHEN ToolFailed THEN retry` | `EXCEPTION` handler | migrate |
| 054 | rate_limit | backoff loop for API quota | `WHILE` + `CALL sleep` | migrate |

### Deferred

| Recipe | Reason |
|--------|--------|
| Streaming token output | Runtime/adapter concern; SPL abstracts it. Map to `--adapter` streaming flag when supported. |
| LangGraph Studio templates | UI deployment config; no SPL workflow logic |
| `langgraph-example` AWS/GCP deploy | Infrastructure; out of scope |
| Time travel (recipe 025) | Requires step-level checkpoint replay beyond current `PersistenceBackend` semantics |

---

## Pipeline: Notebook-First S1→S3

LangGraph source is primarily **Jupyter notebooks** (`.ipynb`). The S1 step must
handle this before the rest of the IR pipeline runs.

```
LangGraph .ipynb
    │
    ▼ (option A)  spl3 splc describe --lang ipynb  [future: native notebook support]
    │ (option B)  jupyter nbconvert --to script notebook.ipynb → notebook.py → spl3 splc describe
    │
    ▼ S1-spec.md
    │
    ▼ spl3 text2mmd S1-spec.md → S2.mmd
    │
    ▼ spl3 mmd2spl S2.mmd → S3.spl
    │
    ▼ spl3 validate + spl3 run smoke test
    │
    ▼ polish → react_agent.spl + tools.spl
    │
    ▼ spl3 registry push cookbook-langgraph/001_react_agent/
```

S4 (tools.spl) is required for almost every LangGraph recipe because LangGraph
uses `ToolNode`, `@tool`-decorated functions, and `MemorySaver` — all of which need
`CREATE TOOL_API` equivalents.

### Per-recipe commands

```bash
# Environment (set once per session)
export ADAPTER=claude_cli
export MODEL_ID=claude-sonnet-4-6
export MODEL=sonnet
export LG_ROOT=$HOME/projects/langchain-ai/langgraph

# Per recipe
export NUM=001
export RECIPE=react_agent
export SRC=$LG_ROOT/examples/react-agent         # or docs/docs/tutorials/...
export DEST=$HOME/projects/digital-duck/SPL.py/cookbook-langgraph/${NUM}_${RECIPE}
export OUT=$DEST/migrate

mkdir -p "$OUT"

# Pre-step: convert notebook to Python if needed
jupyter nbconvert --to script "$SRC/$RECIPE.ipynb" --output "$OUT/nb_$RECIPE.py" 2>/dev/null \
  || cp "$SRC"/*.py "$OUT/nb_$RECIPE.py"

# S1 — describe source → spec
spl3 splc describe "$OUT/nb_$RECIPE.py" \
    --include-docs \
    --adapter $ADAPTER --model $MODEL_ID \
    -o "$OUT/S1-$RECIPE-$MODEL-spec.md"

# ⚠️ HUMAN CHECKPOINT — verify spec covers StateGraph, conditional edges, ToolNode, tools

# S2 — spec → Mermaid topology
spl3 text2mmd "$OUT/S1-$RECIPE-$MODEL-spec.md" \
    --adapter $ADAPTER --model $MODEL_ID \
    --no-defaults \
    -o "$OUT/S2-$RECIPE-$MODEL.mmd"

# ⚠️ HUMAN CHECKPOINT — verify nodes match LangGraph graph structure; check edges

# S3 — Mermaid → SPL
spl3 mmd2spl "$OUT/S2-$RECIPE-$MODEL.mmd" \
    --adapter $ADAPTER --model $MODEL_ID \
    --validate \
    -o "$OUT/S3-$RECIPE-$MODEL.spl"

# ⚠️ HUMAN CHECKPOINT — validate + run; then promote
spl3 validate "$OUT/S3-$RECIPE-$MODEL.spl"
cp "$OUT/S3-$RECIPE-$MODEL.spl" "$DEST/$RECIPE.spl"

# S4 — write tools.spl (manual; required for almost all LangGraph recipes)
# Port each @tool / ToolNode function → CREATE TOOL_API block in $DEST/tools.spl

# Register
# spl3 registry push "$DEST/"
```

### Batch helper script

```bash
#!/usr/bin/env bash
# Usage: bash scripts/migrate_langgraph.sh <num> <recipe> <nb_path> [adapter] [model]
# Example: bash scripts/migrate_langgraph.sh 001 react_agent \
#   ~/projects/langchain-ai/langgraph/examples/react-agent/react_agent.ipynb
set -euo pipefail

NUM="${1:?Usage: $0 <num> <recipe> <notebook_path>}"
RECIPE="${2:?}"
NB_PATH="${3:?}"
ADAPTER="${4:-claude_cli}"
MODEL_ID="${5:-claude-sonnet-4-6}"
MODEL="${MODEL_ID##*/}"

DEST="$HOME/projects/digital-duck/SPL.py/cookbook-langgraph/${NUM}_$RECIPE"
OUT="$DEST/migrate"
mkdir -p "$OUT"

# Convert notebook → Python
echo "=== Converting notebook to Python ==="
jupyter nbconvert --to script "$NB_PATH" --output "$OUT/nb_$RECIPE" 2>/dev/null \
  && echo "  → $OUT/nb_$RECIPE.py" \
  || { echo "nbconvert failed — copying source directly"; cp "$NB_PATH" "$OUT/nb_$RECIPE.py"; }

echo "=== S1: splc describe ==="
spl3 splc describe "$OUT/nb_$RECIPE.py" --include-docs \
    --adapter "$ADAPTER" --model "$MODEL_ID" \
    -o "$OUT/S1-$RECIPE-$MODEL-spec.md"

echo "=== S2: text2mmd ==="
spl3 text2mmd "$OUT/S1-$RECIPE-$MODEL-spec.md" \
    --adapter "$ADAPTER" --model "$MODEL_ID" \
    --no-defaults \
    -o "$OUT/S2-$RECIPE-$MODEL.mmd"

echo ""
echo "⚠️  CHECKPOINT — review $OUT/S2-$RECIPE-$MODEL.mmd"
read -rp "Press Enter to continue to S3, Ctrl-C to abort..."

echo "=== S3: mmd2spl ==="
spl3 mmd2spl "$OUT/S2-$RECIPE-$MODEL.mmd" \
    --adapter "$ADAPTER" --model "$MODEL_ID" \
    --validate \
    -o "$OUT/S3-$RECIPE-$MODEL.spl"

echo ""
echo "⚠️  CHECKPOINT — spl3 validate + smoke test $OUT/S3-$RECIPE-$MODEL.spl"
read -rp "Press Enter to promote, Ctrl-C to abort..."

cp "$OUT/S3-$RECIPE-$MODEL.spl" "$DEST/$RECIPE.spl"
echo "Done → $DEST/$RECIPE.spl"
echo ""
echo "Next: write $DEST/tools.spl (required for ToolNode / @tool functions)"
```

---

## LangGraph-Specific Translation Challenges

These are unique to LangGraph — not encountered in the PocketFlow migration.

### 1. TypedDict state schema → `@var` naming

LangGraph defines a shared `TypedDict` state (e.g. `AgentState`) passed between all
nodes. SPL has no shared-state object — values pass explicitly via `CALL` arguments.

**Translation rule:** Each field of `AgentState` becomes a named `@var`. Node outputs
that write to the state become `INTO @varname`. Node inputs that read from the state
become `INPUT @varname` parameters.

```python
# LangGraph
class AgentState(TypedDict):
    messages: list[BaseMessage]
    plan: list[str]
    past_steps: list[tuple]
    response: str
```

```spl
-- SPL equivalent: explicit @var passing
WORKFLOW plan_and_execute
  INPUT @task TEXT
  OUTPUT @response TEXT
DO
  CALL plan_task(@task) INTO @plan;
  CALL execute_steps(@plan) INTO @past_steps;
  GENERATE synthesize_response(@task, @past_steps) INTO @response;
  RETURN @response WITH status = "complete";
END;
```

### 2. `ToolNode` → `CREATE TOOL_API`

LangGraph's `ToolNode` wraps a list of `@tool`-decorated functions and dispatches
based on the tool name in the last `AIMessage`. In SPL every tool is a
`CREATE TOOL_API` block with an explicit `CALL` in the workflow body.

```python
# LangGraph
@tool
def search_web(query: str) -> str:
    return tavily_client.search(query)

tools = [search_web]
tool_node = ToolNode(tools)
```

```spl
-- SPL equivalent
CREATE TOOL_API search_web(query TEXT) RETURNS TEXT AS PYTHON $
from tavily import TavilyClient
def search_web(query):
    return TavilyClient().search(query, max_results=3)["results"][0]["content"]
$;
```

### 3. Conditional edges → `EVALUATE`

LangGraph's `add_conditional_edges` maps a node output to a routing function that
returns the next node name. SPL uses `EVALUATE @routing_var WHEN ... ELSE`.

```python
# LangGraph
def should_continue(state):
    if state["messages"][-1].tool_calls:
        return "tools"
    return END

graph.add_conditional_edges("agent", should_continue)
```

```spl
-- SPL equivalent
GENERATE decide_action(@messages) INTO @next_action;
EVALUATE @next_action
  WHEN contains("call_tool") THEN
    CALL execute_tool(@next_action) INTO @tool_result;
  ELSE
    @done := "true";
END;
```

### 4. `MemorySaver` / checkpointer → `--persistence`

LangGraph's `MemorySaver` and `SqliteSaver` provide cross-invocation persistence.
SPL's `--persistence sqlite` backend provides the same: the workflow state (all `@var`
snapshots) is stored after every GENERATE/CALL step.

```python
# LangGraph
from langgraph.checkpoint.sqlite import SqliteSaver
memory = SqliteSaver.from_conn_string("~/.langgraph/memory.db")
graph = graph.compile(checkpointer=memory)
graph.invoke({"messages": [...]}, config={"thread_id": "abc"})
```

```bash
# SPL equivalent
spl3 run memory_agent.spl \
  --adapter claude_cli \
  --persistence sqlite \
  --workflow-id thread-abc \
  -p messages="user asked about..."
```

### 5. `interrupt()` → `CALL wait_for_approval`

LangGraph's `interrupt(value)` call inside a node suspends the graph until the host
calls `graph.invoke(None, config, command=Command(resume=value))`. In SPL this is:

```spl
-- Suspend until external approval event
CALL wait_for_approval(@workflow_id, "approve_plan") INTO @human_input;
```

```bash
# External system sends the event (CLI, webhook, dashboard)
spl3 workflow send-event \
  --workflow-id my-run-001 \
  --key approve_plan \
  --value "approved"
```

The workflow was started with `--persistence sqlite --workflow-id my-run-001` and
survives process restarts while waiting.

### 6. Notebook source preprocessing

LangGraph examples are `.ipynb` Jupyter notebooks. Before `spl3 splc describe`
can process them, convert to Python:

```bash
# Option A: nbconvert (recommended)
jupyter nbconvert --to script notebook.ipynb --output notebook

# Option B: strip markdown cells manually, keep code cells
# Option C: use spl3 splc describe --lang ipynb (future — not yet implemented)
```

Known issue: `nbconvert` includes all markdown cells as `# In[N]:` comments. The
`splc describe` LLM ignores them correctly, but the spec can be noisy. Use
`--include-docs` selectively — `--no-include-docs` for notebooks with heavy prose.

---

## Known Pipeline Pitfalls

| Step | Issue | Mitigation |
|------|-------|-----------|
| Pre-S1 | `nbconvert` produces cell-boundary noise (`# In[N]:`) | `splc describe` handles well; use `--no-include-docs` if spec is too long |
| Pre-S1 | Cell execution order matters; cells reference variables defined elsewhere | Concatenate all code cells linearly before passing to `splc describe` |
| S1 | LangGraph imports (`from langgraph.graph import StateGraph`) confuse `splc describe` | The `--lang python` label tells the model this is Python, not a generic file |
| S1 | `TypedDict` state schema appears as a class — LLM may describe it as a data model rather than workflow state | Prompt improvement: "Treat TypedDict subclasses as workflow state variables, not data classes" |
| S2 | Conditional edge routing produces complex graph shapes hard to represent in flowchart Mermaid | Use `graph TD` not `flowchart TD`; use `{decision}` diamond nodes explicitly |
| S3 | LLM generates `SHARED STATE @state_dict :=` (inventing a non-existent construct) | Fix prompt: "Use explicit `@var` passing; there is no shared state in SPL" |
| S3 | `WHILE` body too large when a multi-node subgraph gets inlined | Extract subgraph into a `WORKFLOW` and use `CALL` |
| S4 | `ToolNode` dispatch logic depends on `AIMessage.tool_calls` JSON structure | Simplify: `CREATE TOOL_API` functions operate on plain strings; route with `EVALUATE` |
| S4 | `MemorySaver` / `SqliteSaver` constructor args | Replace with `--persistence sqlite` at run time; no tools.spl entry needed |
| All | `--persistence` required at runtime for HITL recipes but not in `.spl` | Document in each recipe's README; `.spl` file is unchanged |

---

## Execution Phases

```
Phase 0 (setup)     Clone langgraph repo; verify nbconvert works; run S1→S3 on react_agent
Phase 1 (week 1)    Tier 1: 001–009 (core single-agent patterns) — validate S1→S3 pipeline
Phase 2 (week 2)    Tier 2: 010–016 (multi-agent) — validate CALL PARALLEL + EVALUATE routing
Phase 3 (week 3)    Tier 3: 020–024 (memory + persistence) — validate --persistence layer
Phase 4 (week 4)    Tier 4: 030–034 (composition) — validate IMPORT + registry push
Phase 5 (ongoing)   Tier 5: 040–047 (domain pipelines) + Tier 6: 050–054 (production)
```

Phase 0 gate: `spl3 run cookbook-langgraph/001_react_agent/react_agent.spl --adapter ollama`
completes successfully with a meaningful tool call → response cycle.

Phase 3 gate: `spl3 run cookbook-langgraph/021_hitl_approval/hitl_approval.spl --persistence sqlite --workflow-id test-001` pauses at `CALL wait_for_approval`, survives a process restart, and resumes after `spl3 workflow send-event`.

---

## SPL Language Gaps Identified

Each recurring translation workaround is a signal to improve SPL. Gaps surfaced
during the PocketFlow migration and confirmed/extended by LangGraph patterns:

| Gap | Current workaround | Future SPL feature |
|-----|-------------------|-------------------|
| No shared state object | Explicit `@var` threading through all `CALL` chains | Sufficient for most cases; may need `SCOPE` block for deeply nested agents |
| Multi-way conditional edge routing | `EVALUATE @var WHEN "A" THEN ... WHEN "B" THEN ...` | Already in SPL — just needs better LLM prompting in S3 |
| Dynamic tool dispatch (tool name in LLM output) | `EVALUATE @tool_call WHEN contains("search") THEN CALL search_web` | `CALL @tool_name(...)` dynamic dispatch (future) |
| Step-level replay for time travel | Not yet implemented | `spl3 workflow replay --workflow-id ID --to-step N` |
| Cross-workflow shared memory store | `CREATE TOOL_API memory_get/put` pattern | `STORE @key := @value` + `SELECT @var FROM @key` (exists in SPL 2.0 — reuse) |
| Notebook source in `splc describe` | `nbconvert` preprocessing | `spl3 splc describe --lang ipynb` native notebook support |

---

## Registry Strategy

Each recipe in `cookbook-langgraph/` is a candidate for the SPL workflow registry:

| Registry key | Workflow | CALL signature |
|-------------|---------|---------------|
| `langgraph/react_agent` | ReAct loop with tools | `CALL react_agent(@task, @tools) INTO @result` |
| `langgraph/plan_and_execute` | Plan then execute | `CALL plan_and_execute(@task) INTO @result` |
| `langgraph/supervisor` | Supervisor routes to workers | `CALL supervisor(@task, @workers) INTO @result` |
| `langgraph/adaptive_rag` | Route → retrieve → grade | `CALL adaptive_rag(@query, @index) INTO @answer` |
| `langgraph/code_act` | Generate → run → fix | `CALL code_act(@spec) INTO @code` |
| `langgraph/hitl_approval` | Pause for human review | `CALL hitl_approval(@draft, @workflow_id) INTO @approved` |

Once registered, any SPL workflow can compose these patterns without reimplementing them:

```spl
IMPORT 'langgraph/react_agent';
IMPORT 'langgraph/adaptive_rag';

WORKFLOW research_and_answer
  INPUT @question TEXT
  OUTPUT @answer TEXT
DO
  CALL adaptive_rag(@question, "knowledge_base") INTO @context;
  CALL react_agent(@question, "search,calculate,lookup") INTO @raw;
  GENERATE synthesize(@question, @context, @raw) INTO @answer;
  RETURN @answer WITH status = "complete";
END;
```

---

## Reference Materials

| Path | Contents |
|------|----------|
| `docs/DEV/spl3-migrate-pocketflow-recipe.md` | Pocketflow migration plan — S1→S3 pipeline reference |
| `docs/DEV/spl3-state-management-dbos.md` | Persistence layer design — HITL, SQLite, PostgreSQL, DBOS |
| `cookbook-pocketflow/readme-migration.md` | Full recipe status table + pitfall log |
| `cookbook-langgraph/readme-migration.md` | This project's lightweight progress tracker |
| `spl3/persistence/` | SQLite, PostgreSQL, DBOS backends |
| `spl3/registry.py` | Local workflow registry (`spl3 registry push/pull`) |
| `spl3/hub_registry.py` | Momagrid Hub registry (remote `CALL`) |
| `~/projects/langchain-ai/langgraph/examples/` | Source notebooks |
| `~/projects/langchain-ai/langgraph/docs/docs/tutorials/` | Narrative tutorial notebooks |
