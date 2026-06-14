# 019 — Agentic Rag  *(migrated from PocketFlow)*

**Source:** [pocketflow-agentic-rag](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-agentic-rag)
**Difficulty:** ★☆☆
**Migrated by:** migrate_pocketflow.py — adapter=claude_cli model=claude-sonnet-4-6

## Run

```bash
conda activate spl123
cd ~/projects/digital-duck/SPL.py

spl3 run cookbook-pocketflow/019_agentic_rag/agentic_rag.spl \
    --tools cookbook/tools/ \
    --llm claude_cli:claude-sonnet-4-6
```

## Migrate artifacts

```
migrate/
├── S1-agentic_rag-claude-sonnet-4-6-spec.md   # splc describe output
├── S2-agentic_rag-claude-sonnet-4-6.mmd       # text2mmd Mermaid diagram
└── S3-agentic_rag-claude-sonnet-4-6.spl       # raw mmd2spl output (= agentic_rag.spl)
```

tools.spl (if present) — CREATE TOOL_API helpers ported from utils.py.
Recipes whose utils.py only wraps call_llm need no tools.spl.

> TODO: enrich this README — describe SPL pattern, key constructs, tool dependencies.
