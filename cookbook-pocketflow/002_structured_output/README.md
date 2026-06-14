# 002 — structured output  *(migrated from PocketFlow)*

**Source:** [pocketflow-structured-output](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-structured-output)
**Difficulty:** ☆☆☆
**Migrated by:** phase1_migrate.sh — adapter=claude_cli model=claude-sonnet-4-6

## Run

```bash
conda activate spl123
cd ~/projects/digital-duck/SPL.py

spl3 run cookbook-pocketflow/002_structured_output/structured_output.spl \
    --tools cookbook/tools/ \
    --llm claude_cli:claude-sonnet-4-6
```

## Migrate artifacts

```
migrate/
├── S1-structured_output-claude-sonnet-4-6-spec.md   # splc describe output
├── S2-structured_output-claude-sonnet-4-6.mmd       # text2mmd Mermaid diagram
└── S3-structured_output-claude-sonnet-4-6.spl       # raw mmd2spl output (= structured_output.spl)
```

tools.spl (if present) — CREATE TOOL_API helpers ported from utils.py.
Phase-1 recipes only wrap call_llm in utils.py, so no tools.spl needed.

> TODO: enrich this README — describe SPL pattern, key constructs, tool dependencies.
