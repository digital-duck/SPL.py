# 030 — Lead Generation  *(migrated from PocketFlow)*

**Source:** [pocketflow-lead-generation](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-lead-generation)
**Difficulty:** ★★☆
**Migrated by:** migrate_pocketflow.py — adapter=claude_cli model=claude-sonnet-4-6

## Run

```bash
conda activate spl123
cd ~/projects/digital-duck/SPL.py

spl3 run cookbook-pocketflow/030_lead_generation/lead_generation.spl \
    --tools cookbook/tools/ \
    --llm claude_cli:claude-sonnet-4-6
```

## Migrate artifacts

```
migrate/
├── S1-lead_generation-claude-sonnet-4-6-spec.md   # splc describe output
├── S2-lead_generation-claude-sonnet-4-6.mmd       # text2mmd Mermaid diagram
└── S3-lead_generation-claude-sonnet-4-6.spl       # raw mmd2spl output (= lead_generation.spl)
```

tools.spl (if present) — CREATE TOOL_API helpers ported from utils.py.
Recipes whose utils.py only wraps call_llm need no tools.spl.

> TODO: enrich this README — describe SPL pattern, key constructs, tool dependencies.
