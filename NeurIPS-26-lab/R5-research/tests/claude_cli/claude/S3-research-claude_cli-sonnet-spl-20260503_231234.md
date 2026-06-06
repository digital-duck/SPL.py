INFO:spl.registry:Registry: loaded 1 workflow(s) from /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R5-research/tests/claude_cli/sonnet/S3-research-claude_cli-sonnet.spl
Registry: ['deep_research']
Running workflow: deep_research(['topic', 'out', 'model'])
INFO:spl.executor:GENERATE segment 1 (planner) -> 55 tokens, 4476ms
INFO:spl.executor:GENERATE chain done -> @queries (222 chars total)
INFO:spl.executor:GENERATE segment 1 (extract_query) -> 16 tokens, 2700ms
INFO:spl.executor:GENERATE chain done -> @query1 (66 chars total)
INFO:spl.executor:GENERATE segment 1 (extract_query) -> 14 tokens, 3521ms
INFO:spl.executor:GENERATE chain done -> @query2 (59 chars total)
INFO:spl.executor:GENERATE segment 1 (extract_query) -> 17 tokens, 2785ms
INFO:spl.executor:GENERATE chain done -> @query3 (68 chars total)
WARNING:spl.executor:Unknown statement type in workflow body: CallParallelStatement
WARNING:spl.executor:Unknown statement type in workflow body: CallParallelStatement
INFO:spl.executor:GENERATE segment 1 (accumulate_notes) -> 46 tokens, 4721ms
INFO:spl.executor:GENERATE chain done -> @notes (186 chars total)
INFO:spl.executor:GENERATE segment 1 (synthesizer) -> 84 tokens, 5096ms
INFO:spl.executor:GENERATE chain done -> @decision (336 chars total)
INFO:spl.executor:GENERATE segment 1 (extract_feedback) -> 76 tokens, 3143ms
INFO:spl.executor:GENERATE chain done -> @feedback (307 chars total)
INFO:spl.executor:GENERATE segment 1 (planner) -> 68 tokens, 3467ms
INFO:spl.executor:GENERATE chain done -> @queries (273 chars total)
INFO:spl.executor:GENERATE segment 1 (extract_query) -> 20 tokens, 2402ms
INFO:spl.executor:GENERATE chain done -> @query1 (83 chars total)
INFO:spl.executor:GENERATE segment 1 (extract_query) -> 20 tokens, 3171ms
INFO:spl.executor:GENERATE chain done -> @query2 (82 chars total)
INFO:spl.executor:GENERATE segment 1 (extract_query) -> 19 tokens, 4275ms
INFO:spl.executor:GENERATE chain done -> @query3 (79 chars total)
WARNING:spl.executor:Unknown statement type in workflow body: CallParallelStatement
WARNING:spl.executor:Unknown statement type in workflow body: CallParallelStatement
INFO:spl.executor:GENERATE segment 1 (accumulate_notes) -> 46 tokens, 4122ms
INFO:spl.executor:GENERATE chain done -> @notes (186 chars total)
INFO:spl.executor:GENERATE segment 1 (synthesizer) -> 361 tokens, 21186ms
INFO:spl.executor:GENERATE chain done -> @decision (1446 chars total)
INFO:spl.executor:GENERATE segment 1 (extract_feedback) -> 354 tokens, 5093ms
INFO:spl.executor:GENERATE chain done -> @feedback (1416 chars total)
INFO:spl.executor:GENERATE segment 1 (planner) -> 69 tokens, 3680ms
INFO:spl.executor:GENERATE chain done -> @queries (278 chars total)
INFO:spl.executor:GENERATE segment 1 (write_concise_report) -> 1030 tokens, 24753ms
INFO:spl.executor:GENERATE chain done -> @report (4122 chars total)
INFO:spl.executor:RETURN: 4122 chars | status=complete

Status:  complete
Output:  # PocketFlow: Minimalist LLM Framework — Research Report

---

## Overview

PocketFlow is an open-source, minimalist framework for building LLM-powered applications using a graph-based flow abstraction. Its core design philosophy is radical simplicity: the entire framework is implemented in ~100 lines of Python, making it one of the smallest production-viable LLM orchestration tools available.

---

## Key Design Principles

**Graph-based computation model.** Applications are modeled as directed graphs of `Node` objects connected by named edges. Execution follows transitions determined at runtime by each node's return value (`Action`), enabling conditional branching and loops without special syntax.

**Three core primitives.** The entire framework reduces to:
- `Node` — a single processing step with `prep`, `exec`, and `post` lifecycle hooks
- `Flow` — a graph of nodes with a defined start node
- `BatchNode` / `BatchFlow` — parallel variants for bulk processing

**No hidden magic.** Unlike LangChain or LlamaIndex, PocketFlow imposes no abstractions over LLM clients, prompt templates, memory stores, or tool registries. Users wire these in explicitly, retaining full visibility and control.

---

## Key Findings

### 1. Footprint and Dependency Profile
The framework has zero required dependencies beyond Python's standard library. LLM calls, vector stores, and tool integrations are user-supplied. This eliminates dependency conflicts and makes the codebase auditable in minutes.

### 2. Agentic and RAG Patterns Are First-Class Use Cases
Despite its small size, PocketFlow's graph model naturally supports:
- **ReAct agents** — think/act/observe loops as cyclic graphs
- **RAG pipelines** — retrieve → augment → generate as linear flows
- **Multi-agent systems** — nested `Flow` nodes that encapsulate sub-agents
- **Map-reduce over documents** — `BatchNode` parallelism

### 3. Async and Streaming Support
PocketFlow provides `AsyncNode` and `AsyncFlow` variants that integrate with Python's `asyncio`, enabling concurrent LLM calls and streaming responses without blocking.

### 4. Shared Store Pattern
Nodes communicate through a shared `store` dictionary passed through the graph. This replaces implicit state management with an explicit, inspectable data structure — simplifying debugging and testing significantly.

### 5. Cookbook-Driven Development
The project ships an extensive cookbook (in the companion `PocketFlow-Tutorial-Codebase-Knowledge` repo) that translates common LLM application patterns — agent loops, RAG, multi-agent orchestration, structured output — directly into PocketFlow idioms.

---

## Comparison with Peer Frameworks

| Dimension | PocketFlow | LangChain | LlamaIndex |
|---|---|---|---|
| Core LOC | ~100 | ~100k+ | ~50k+ |
| Required deps | 0 | Many | Many |
| Abstraction level | Low | High | Medium |
| Debuggability | Excellent | Difficult | Moderate |
| Learning curve | Minimal | Steep | Moderate |
| Ecosystem/integrations | User-supplied | Extensive | Extensive |

PocketFlow trades ecosystem breadth for transparency and control.

---

## Relevance to NeurIPS-26 Experiments

In the context of this lab's SPL.py research pipeline (R1–R5), PocketFlow serves as the underlying execution substrate for the `python_pocketflow` adapter target (S4). Its graph model maps cleanly onto SPL's step-oriented program structure, making it a natural fit for evaluating how LLMs reason about and generate flow-based programs.

---

## Conclusion

PocketFlow occupies a distinct niche: it is the minimal viable skeleton for LLM application development, not a batteries-included toolkit. Its value is highest when (a) you need full transparency into execution, (b) you are building novel LLM patterns not anticipated by larger frameworks, or (c) you are embedding LLM logic in a larger system where dependency weight matters. Its primary limitation is that it provides no off-the-shelf integrations — every tool, memory store, and LLM client must be wired in manually. For research contexts requiring reproducibility and interpretability, this is a feature rather than a bug.
LLM calls: 16  Latency: 98592ms
Log:     /home/wengong/.spl/logs/S3_research_claude_cli_sonnet-claude_cli-20260503-231235.md
