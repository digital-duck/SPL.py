# 001 — Chat  *(migrated from PocketFlow)*

**Source:** [pocketflow-chat](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-chat)
**Difficulty:** ☆☆☆
**Category:** basics

## What it does

Implements a multi-turn conversational loop that reads user input at the CLI, maintains a sliding-window JSON message history, and generates a contextually aware reply with each turn. The workflow continues until the user sends an exit signal ("exit", "quit", "bye", or "goodbye"), then returns the full conversation history. This is the foundational pattern for any production chatbot built on SPL.

## Real-world use cases

- **Customer support**: Embed as the core interaction loop for a domain-scoped support bot, replacing stateless single-turn calls with full conversation context
- **Internal tooling**: Power interactive CLI assistants for DevOps teams that need to query infrastructure state across multiple turns without re-stating context
- **Education platforms**: Drive conversational tutoring sessions where the assistant tracks what a student has understood across the session
- **Personal productivity**: Build a long-running "thinking partner" CLI that maintains session memory for brainstorming or planning tasks

## Key SPL constructs

- `CREATE TOOL_API read_user_input()` — reads a line from stdin with graceful EOF/interrupt handling
- `CREATE TOOL_API is_exit_command(user_input)` — deterministic keyword check for exit signals
- `CREATE TOOL_API append_turn(history, role, content)` — appends a `{role, content}` pair to the JSON history array
- `WHILE @i < @max_turns DO` — bounded conversation loop with force-exit on exit command
- `EVALUATE @is_exit WHEN contains("true")` — branches to force-exit vs. continue
- `GENERATE chat_reply(@trimmed)` — LLM reply generation over the sliding-window context
- `LOGGING` — echoes the assistant reply to stdout during execution

## Workflow I/O

**Inputs:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `@max_turns` | INTEGER | 50 | Maximum conversation turns before auto-exit |
| `@last_n` | TEXT | "10" | Number of most-recent turns to pass as context |

**Output:** `@history TEXT` — full JSON array of all conversation turns

## Run

```bash
conda activate spl123
cd ~/projects/digital-duck/SPL.py

spl3 run cookbook-pocketflow/001_chat/chat.spl \
    --llm claude_cli:claude-sonnet-4-6
```

## Extend it

- Wrap with `CALL PARALLEL` to run multiple concurrent chatbot personas and compare outputs
- Replace `read_user_input` with a WebSocket or REST hook to drive web-based chat interfaces
- Add `EXCEPTION WHEN BudgetExceeded` to gracefully close the session when token limits approach
- Swap `--llm` flag at runtime to A/B test different models on the same conversation trace

## Migrate artifacts

For a detailed functional description, see the **[Functional Spec](migrate/S1-chat-claude-sonnet-4-6-spec.md)**.

```
migrate/
├── S1-chat-claude-sonnet-4-6-spec.md   # functional specification (deep-dive)
├── S2-chat-claude-sonnet-4-6.mmd       # text2mmd Mermaid diagram
└── S3-chat-claude-sonnet-4-6.spl       # raw mmd2spl output (= chat.spl)
```
