# 015 — Chat Memory  *(migrated from PocketFlow)*

**Source:** [pocketflow-chat-memory](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-chat-memory)
**Difficulty:** ★☆☆
**Category:** memory

## What it does

Extends a multi-turn chat loop with a two-tier memory architecture: a sliding window holds the most recent messages for immediate context, and a semantic archive stores older messages indexed by a TF-IDF embedding approximation. On each turn, the archive is searched by cosine similarity to the current query and the most relevant past messages are injected into context alongside the window. This pattern prevents context-window overflow while keeping long-term conversational references accessible.

## Real-world use cases

- **Customer support continuity**: Maintain a coherent conversation with a customer across dozens of turns without exceeding context limits, surfacing relevant past issues even from early in the session
- **Personal AI assistants**: Recall facts the user mentioned many turns ago ("my daughter starts college in September") without requiring the user to repeat themselves
- **Research assistants**: Keep the active discussion focused (sliding window) while being able to reference earlier hypotheses or findings (semantic archive)
- **Training session tutors**: Track what a student has already learned earlier in a long session without re-explaining covered material

## Key SPL constructs

- `CREATE TOOL_API embed_text(text)` — produces a TF-IDF-based vector representation of a message
- `CREATE TOOL_API archive_search(archive_json, query_embedding, top_k)` — cosine similarity search over the archive
- `CREATE TOOL_API window_load(window_file)` / `window_append` / `window_is_full` / `window_evict_oldest` — sliding window management
- `CREATE TOOL_API archive_add(archive_file, role, content, embedding)` — adds an evicted message to the semantic archive
- `CREATE TOOL_API build_context(window_json, retrieved_json)` — merges window and archive hits into a single prompt context
- `CREATE TOOL_API get_query(window_json)` — extracts the latest user message for archive search
- `WHILE @active = "true" DO` — main conversation loop with graceful exit on "quit"

## Workflow I/O

**Inputs:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `@window_file` | TEXT | `"window.json"` | Path to the sliding window state file |
| `@archive_file` | TEXT | `"archive.json"` | Path to the semantic archive state file |
| `@window_size` | INTEGER | 3 | Number of recent messages in the sliding window |

**Output:** `@response TEXT` — final assistant message (last turn before quit)

## Run

```bash
conda activate spl123
cd ~/projects/digital-duck/SPL.py

spl3 run cookbook-pocketflow/015_chat_memory/chat_memory.spl \
    --llm claude_cli:claude-sonnet-4-6
```

## Extend it

- Replace the TF-IDF embedding with a real embedding model (e.g., via `ollama embed`) for higher-quality semantic search
- Persist `window.json` and `archive.json` across sessions to create a truly long-term memory agent
- Add a GENERATE step to summarize the archive periodically, replacing clusters of similar messages with a compressed summary
- Instrument with `CALL write_file` to log each memory retrieval for inspection and quality tuning

## Migrate artifacts

For a detailed functional description, see the **[Functional Spec](migrate/S1-chat_memory-claude-sonnet-4-6-spec.md)**.

```
migrate/
├── S1-chat_memory-claude-sonnet-4-6-spec.md   # splc describe output
├── S2-chat_memory-claude-sonnet-4-6.mmd       # text2mmd Mermaid diagram
└── S3-chat_memory-claude-sonnet-4-6.spl       # raw mmd2spl output (= chat_memory.spl)
```

tools.spl (if present) — CREATE TOOL_API helpers ported from utils.py.
Recipes whose utils.py only wraps call_llm need no tools.spl.
