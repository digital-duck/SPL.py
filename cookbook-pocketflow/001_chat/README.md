# 001 — chat  *(migrated from PocketFlow)*

**Source:** [pocketflow-chat](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-chat)
**Difficulty:** ☆☆☆
**Migrated by:** phase1_migrate.sh — adapter=claude_cli model=claude-sonnet-4-6

## Run

```bash
conda activate spl123
cd ~/projects/digital-duck/SPL.py

spl3 run cookbook-pocketflow/001_chat/chat.spl \
    --tools cookbook/tools/ \
    --llm claude_cli:claude-sonnet-4-6
```

## Migrate artifacts

```
migrate/
├── S1-chat-claude-sonnet-4-6-spec.md   # splc describe output
├── S2-chat-claude-sonnet-4-6.mmd       # text2mmd Mermaid diagram
└── S3-chat-claude-sonnet-4-6.spl       # raw mmd2spl output (= chat.spl)
```

tools.spl (if present) — CREATE TOOL_API helpers ported from utils.py.
Phase-1 recipes only wrap call_llm in utils.py, so no tools.spl needed.

> TODO: enrich this README — describe SPL pattern, key constructs, tool dependencies.
