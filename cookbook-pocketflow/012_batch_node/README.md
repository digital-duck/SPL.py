# 012 — Batch Node  *(migrated from PocketFlow)*

**Source:** [pocketflow-batch-node](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-batch-node)
**Difficulty:** ★☆☆
**Migrated by:** migrate_pocketflow.py — adapter=claude_cli model=claude-sonnet-4-6

## Run

```bash
conda activate spl123
cd ~/projects/digital-duck/SPL.py

spl3 run cookbook-pocketflow/012_batch_node/batch_node.spl \
    --tools cookbook/tools/ \
    --llm claude_cli:claude-sonnet-4-6
```

## Migrate artifacts

```
migrate/
├── S1-batch_node-claude-sonnet-4-6-spec.md   # splc describe output
├── S2-batch_node-claude-sonnet-4-6.mmd       # text2mmd Mermaid diagram
└── S3-batch_node-claude-sonnet-4-6.spl       # raw mmd2spl output (= batch_node.spl)
```

tools.spl (if present) — CREATE TOOL_API helpers ported from utils.py.
Recipes whose utils.py only wraps call_llm need no tools.spl.

> TODO: enrich this README — describe SPL pattern, key constructs, tool dependencies.
