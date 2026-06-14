# 006 — map reduce  *(migrated from PocketFlow)*

**Source:** [pocketflow-map-reduce](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-map-reduce)
**Difficulty:** ☆☆☆
**Migrated by:** phase1_migrate.sh — adapter=claude_cli model=claude-sonnet-4-6

## Run

```bash
conda activate spl123
cd ~/projects/digital-duck/SPL.py

spl3 run cookbook-pocketflow/006_map_reduce/map_reduce.spl \
    --tools cookbook/tools/ \
    --llm claude_cli:claude-sonnet-4-6
```

## Migrate artifacts

```
migrate/
├── S1-map_reduce-claude-sonnet-4-6-spec.md   # splc describe output
├── S2-map_reduce-claude-sonnet-4-6.mmd       # text2mmd Mermaid diagram
└── S3-map_reduce-claude-sonnet-4-6.spl       # raw mmd2spl output (= map_reduce.spl)
```

tools.spl (if present) — CREATE TOOL_API helpers ported from utils.py.
Phase-1 recipes only wrap call_llm in utils.py, so no tools.spl needed.

> TODO: enrich this README — describe SPL pattern, key constructs, tool dependencies.
