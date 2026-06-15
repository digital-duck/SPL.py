# cookbook-langgraph — Curation & Migration Plan

## Guiding Principle

Same as cookbook-pocketflow: curate exemplar agentic patterns from open-source frameworks,
translate them to SPL, and deposit them into the SPL workflow registry.

LangGraph recipes are complementary to PocketFlow — they expose patterns at the
graph/orchestration level (conditional edges, subgraphs, checkpointing, HITL) rather than
the node level. The goal is to expand SPL's expressive coverage and stress-test constructs
that PocketFlow did not exercise.

---

## Source Repositories

| Repo | What to mine |
|------|-------------|
| `langchain-ai/langgraph` | `examples/` and `docs/docs/tutorials/` — canonical patterns |
| `langchain-ai/langgraph-example` | standalone agent templates |
| `langchain-ai/langchain` | `cookbook/` notebooks that use LangGraph |
| `langchain-ai/langgraph-studio` | production deployment templates |

```bash
git clone https://github.com/langchain-ai/langgraph ~/projects/langchain-ai/langgraph
ls ~/projects/langchain-ai/langgraph/examples/
```

---

## SPL Coverage Analysis

| LangGraph pattern | SPL construct | Status |
|---|---|---|
| Conditional edges | `EVALUATE` | covered |
| Cycles / retries | `WHILE` | covered |
| Subgraphs | `CALL workflow_name()` | covered |
| Fan-out / fan-in | `CALL PARALLEL` | covered |
| Tool calling | `CREATE TOOL_API` | covered |
| Checkpointing (soft) | `COMMIT @var WITH STATUS` | covered |
| Human-in-the-loop pause | `CREATE TOOL_API` (approval gate) | covered via TOOL_API |
| Shared state across agents | pass-by-value via `CALL` chain | sufficient for most cases |
| Streaming intermediate outputs | adapter concern, not SPL | out-of-scope for .spl |
| **Durable interrupt / resume** | **DBOS adapter** | adapter layer (see below) |
| Time travel / branch rollback | deferred | deferred |

### DBOS for durable execution

LangGraph's "interrupt/resume" pattern — pause a workflow mid-graph, wait for human input,
resume from exact state — is **not** a new SPL language construct. It is a physical
infrastructure concern. The same `.spl` file should run identically on a local process or
a DBOS durable-execution engine.

Planned approach:
- Add `spl3/adapters/dbos.py` — a DBOS-backed adapter that wraps LLM calls with durable
  function decorators (`@DBOS.workflow`, `@DBOS.step`)
- `CALL human_approval(@draft) INTO @decision` becomes a DBOS `send_event` / `recv_event`
  pair under the hood — zero changes to the `.spl` file
- Invoked with: `spl3 run workflow.spl --adapter dbos`
- DBOS provides crash recovery, exactly-once execution, and an audit log for free

This is pure DODA: the `.spl` is the invariant; DBOS is one more physical execution target,
no different from `--adapter momagrid` or `--adapter ollama`.

---

## Starter Recipe Set

Priority is patterns **new relative to PocketFlow** — skip duplicates like basic chat or
vanilla RAG unless the LangGraph version exercises a meaningfully different SPL structure.

| # | Recipe | LangGraph pattern | Difficulty | Notes |
|---|--------|------------------|-----------|-------|
| 001 | react_agent | ReAct tool-call loop | 3/10 | baseline — validate pipeline on LangGraph source |
| 002 | plan_and_execute | two-phase: planner sub-graph → executor sub-graph | 4/10 | CALL chaining |
| 003 | reflection | generate → critique → revise loop | 3/10 | WHILE + EVALUATE |
| 004 | self_corrective_rag | retrieve → grade → rewrite → answer | 5/10 | branching retrieve path |
| 005 | multi_agent_supervisor | supervisor routes to specialized sub-agents | 6/10 | EVALUATE dispatch + CALL |
| 006 | human_in_loop | approval gate via TOOL_API | 5/10 | wait for DBOS adapter |
| 007 | parallelization | fan-out research → synthesize | 4/10 | CALL PARALLEL |
| 008 | corrective_rag | web fallback when retrieval score low | 5/10 | EVALUATE + search_web stdlib |
| 009 | subgraph_composition | nested graphs as reusable CALL targets | 5/10 | registry composition |
| 010 | time_travel | rollback to checkpoint and re-run branch | 7/10 | deferred — needs deeper design |

Recipes 001–005, 007–009 can be migrated with the existing S1→S3 pipeline.
Recipe 006 (human_in_loop) waits for the DBOS adapter.
Recipe 010 (time_travel) is deferred pending SPL checkpointing semantics.

---

## Migration Pipeline

Same S1→S3 automation as cookbook-pocketflow; only the source root changes.

```bash
# Run spl3 splc describe on LangGraph source directly:
spl3 splc describe ~/projects/langchain-ai/langgraph/examples/react-agent \
  --include-docs --adapter claude_cli \
  -o cookbook-langgraph/001_react_agent/migrate/S1-spec.md
```

S4 (tools.spl) will require more hand-work than PocketFlow because LangGraph uses
`TypedDict` state schemas, `ToolNode`, and `MemorySaver` — none of which have stdlib
equivalents. Expect most recipes to need a `tools.spl`.

---

## Progress Tracker

| # | Recipe | Status | Difficulty | tools.spl | Notes |
|---|--------|--------|-----------|-----------|-------|
| 001 | react_agent | — | 3/10 | | |
| 002 | plan_and_execute | — | 4/10 | | |
| 003 | reflection | — | 3/10 | | |
| 004 | self_corrective_rag | — | 5/10 | | |
| 005 | multi_agent_supervisor | — | 6/10 | | |
| 006 | human_in_loop | deferred | 5/10 | | wait for DBOS adapter |
| 007 | parallelization | — | 4/10 | | |
| 008 | corrective_rag | — | 5/10 | | |
| 009 | subgraph_composition | — | 5/10 | | |
| 010 | time_travel | deferred | 7/10 | | needs SPL checkpointing design |

---

## Next Steps

- [ ] Clone `langchain-ai/langgraph` and scan `examples/` for candidate source dirs
- [ ] Create `cookbook-langgraph/migrate_langgraph.py` (adapt from migrate_pocketflow.py — change source root and catalog)
- [ ] Migrate 001–005, 007–009 (no DBOS dependency)
- [ ] Design and implement `spl3/adapters/dbos.py`
- [ ] Migrate 006 (human_in_loop) once DBOS adapter is ready
- [ ] Defer 010 (time_travel) until SPL checkpointing semantics are defined
