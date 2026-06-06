INFO:spl.registry:Registry: loaded 1 workflow(s) from /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/claude_cli/sonnet/S3-agent-claude_cli-sonnet.spl
Registry: ['react_research_agent']
Running workflow: react_research_agent(['question', 'model'])
INFO:spl.executor:GENERATE segment 1 (decide_action) -> 61 tokens, 8839ms
INFO:spl.executor:GENERATE chain done -> @decision (247 chars total)
INFO:spl.executor:GENERATE segment 1 (fetch_results) -> 467 tokens, 29613ms
INFO:spl.executor:GENERATE chain done -> @snippets (1870 chars total)
INFO:spl.executor:GENERATE segment 1 (decide_action) -> 39 tokens, 3511ms
INFO:spl.executor:GENERATE chain done -> @decision (158 chars total)
INFO:spl.executor:GENERATE segment 1 (synthesize_answer) -> 406 tokens, 12530ms
INFO:spl.executor:GENERATE chain done -> @answer (1624 chars total)
INFO:spl.executor:RETURN: 1624 chars | status=done, iterations=1

Status:  complete
Output:  ## What is PocketFlow?

PocketFlow is a minimalist Python framework for orchestrating LLM-based applications. Its entire core fits in roughly 100 lines of code and has **zero mandatory dependencies** — you bring your own LLM SDKs (e.g., `anthropic`, `openai`) and database clients.

The framework's central abstraction is a **directed graph**:

- **Nodes** — individual computation units (e.g., "call an LLM", "retrieve from a vector DB", "parse output")
- **Flow** — a graph of connected nodes that defines the execution pipeline
- **Shared Store** — a dictionary passed between nodes for inter-step communication

This graph model is expressive enough to implement common LLM patterns out of the box: single-agent loops, RAG pipelines, and multi-agent workflows. The project's tagline is *"Let Agents build Agents."*

## Installation

The standard install is a single pip command:

```bash
pip install pocketflow
```

Because the core is ~100 lines with no required dependencies, an alternative approach is to **copy the source directly** into your project — useful if you want full control or are working in an environment without PyPI access.

After installing, you supply whatever LLM/embedding/DB SDKs your pipeline needs (e.g., `pip install anthropic` for Claude).

## Quick mental model

```
Flow
 └── Node A  →  Node B  →  Node C
       ↑__________________________|   (loop back if needed)

All nodes read/write a shared dict (Store)
```

This makes PocketFlow well-suited for research and experimentation where you want a lightweight scaffold without the overhead of larger frameworks like LangChain or LlamaIndex.
LLM calls: 4  Latency: 54493ms
Log:     /home/wengong/.spl/logs/S3_agent_claude_cli_sonnet-claude_cli-20260503-230820.md
