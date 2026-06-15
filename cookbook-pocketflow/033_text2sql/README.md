# 033 — Text2Sql  *(migrated from PocketFlow)*

**Source:** [pocketflow-text2sql](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-text2sql)
**Difficulty:** ★★☆
**Migrated by:** migrate_pocketflow.py — adapter=claude_cli model=claude-sonnet-4-6

## Run

```bash
conda activate spl123
cd ~/projects/digital-duck/SPL.py

spl3 run cookbook-pocketflow/033_text2sql/text2sql.spl \
    --tools cookbook/tools/ \
    --llm claude_cli:claude-sonnet-4-6
```

## Migrate artifacts

```
migrate/
├── S1-text2sql-claude-sonnet-4-6-spec.md   # splc describe output
├── S2-text2sql-claude-sonnet-4-6.mmd       # text2mmd Mermaid diagram
└── S3-text2sql-claude-sonnet-4-6.spl       # raw mmd2spl output (= text2sql.spl)
```

tools.spl (if present) — CREATE TOOL_API helpers ported from utils.py.
Recipes whose utils.py only wraps call_llm need no tools.spl.

> TODO: enrich this README — describe SPL pattern, key constructs, tool dependencies.
