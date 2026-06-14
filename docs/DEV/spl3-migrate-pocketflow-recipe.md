# Migrating Agentic Workflow Recipes to SPL — `cookbook-pocketflow/` and beyond

## Motivation

[PocketFlow](https://github.com/The-Pocket/PocketFlow) is an open-source
minimalist LLM framework that has accumulated a rich library of ~68 workflow
recipes across difficulty levels — from basic single-LLM chains to advanced
multi-agent production systems.

SPL and PocketFlow share the same conceptual layer: both describe *what* an
agentic workflow does, not *how* the runtime executes it. PocketFlow expresses
workflows as Python node graphs; SPL expresses them as declarative `.spl`
scripts. The semantic content — prompt templates, control flow, tool use,
state passing — maps cleanly between the two.

This migration serves three purposes:

1. **Enrich the SPL cookbook.** PocketFlow's catalog covers workflow shapes
   (supervisor loops, agentic RAG, coding agents, heartbeat monitors, MCP
   tool use) not yet represented in the SPL `cookbook/`. Porting them gives
   SPL users a broader pattern library to learn from and adapt.

2. **Validate the IR pipeline.** Migrating real-world recipes through
   `splc describe → text2mmd → mmd2spl` stress-tests the full SPL toolchain
   and surfaces gaps in the compiler, prompt quality, and language coverage.
   The NeurIPS-26 experiment (5 recipes × 3 models) was the first systematic
   test; this migration extends that validation to the full catalog.

3. **Open-source reciprocity.** PocketFlow's recipes are MIT-licensed.
   Migrated SPL versions are kept in a dedicated `cookbook-pocketflow/`
   folder with explicit attribution, so the community can see both
   representations side-by-side and the work gives back to the ecosystem.

The guiding principle: 
- curate agentic workflow patterns from other framework such as pocketflow, langgraph
- enhance SPL's expressiveness as a language.
- build a SPL workflow registry 

---

## Goal

Port the PocketFlow cookbook (`~/projects/wgong/PocketFlow/cookbook/`) into a
dedicated **`cookbook-pocketflow/`** folder, keeping the PocketFlow lineage
explicit and preserving credit to the source project.

```
~/projects/digital-duck/SPL.py/
├── cookbook/                    # original SPL recipes (01_*…77_*)
└── cookbook-pocketflow/         # PocketFlow migrations (001_*…)
```

Each entry:

```
cookbook-pocketflow/
└── 004_agent/
    ├── agent.spl          # migrated SPL workflow
    ├── tools.spl          # CREATE TOOL_API helpers (if needed; replaces tools.py)
    ├── README.md          # what it demonstrates + attribution
    └── migrate/
        ├── S1-*-spec.md   # splc describe output (archived)
        ├── S2-*.mmd       # text2mmd Mermaid topology (archived)
        └── S3-*.spl       # raw mmd2spl output before polish
```

> **No `tools.py` / `@spl_tool` decorator approach.** All helper tools go in
> `tools.spl` as `CREATE TOOL_API` blocks so they run inside SPL's persistent
> kernel session — no separate Python module or decorator registry needed.

`README.md` header template for attribution:

```markdown
# 004 — Agent  *(migrated from PocketFlow)*

**Source:** [pocketflow-agent](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-agent)
**Difficulty:** ☆☆☆ Dummy
**SPL pattern:** ReAct loop — WHILE + EVALUATE + CALL tool
```

---

## Numbering Scheme — 3-digit labels

Recipes are grouped by difficulty tier with gaps for future additions.

| Range | Tier | Difficulty |
|-------|------|-----------|
| `001–009` | Basic single-LLM | ☆☆☆ Dummy |
| `010–029` | Multi-step / agentic | ★☆☆ Beginner |
| `030–039` | Intermediate pipelines | ★★☆ Intermediate |
| `040–049` | Advanced / production | ★★★ Advanced |
| `050–099` | Remaining PocketFlow catalog | varies |

---

## Full Recipe Inventory

### Tier 1 — Basic (001–009) ☆☆☆ Dummy

| # | Recipe | Key SPL pattern | NeurIPS | Status |
|---|--------|-----------------|---------|--------|
| 001 | pocketflow-chat | WHILE loop chatbot | — | migrate |
| 002 | pocketflow-structured-output | GENERATE + schema | — | migrate |
| 003 | pocketflow-workflow | linear multi-stage | — | migrate |
| 004 | pocketflow-agent | ReAct WHILE + CALL tool | R1 | ✅ seed |
| 005 | pocketflow-rag | embed + retrieve + GENERATE | R2 | ✅ seed |
| 006 | pocketflow-map-reduce | CALL PARALLEL + reduce | — | migrate |
| 007 | pocketflow-llm-streaming | streaming GENERATE | — | defer* |
| 008 | pocketflow-chat-guardrail | EVALUATE guardrail gate | — | migrate |

*007: streaming is a runtime concern; SPL abstracts it — defer unless a
streaming-specific GENERATE pattern is needed.

### Tier 2 — Multi-step / Agentic (010–029) ★☆☆ Beginner

| # | Recipe | Key SPL pattern | NeurIPS | Status |
|---|--------|-----------------|---------|--------|
| 010 | pocketflow-multi-agent | async 2-agent CALL PARALLEL | — | migrate |
| 011 | pocketflow-supervisor | supervisor→worker feedback loop | — | migrate |
| 012 | pocketflow-batch-node | node-level CALL PARALLEL batching | — | migrate |
| 013 | pocketflow-batch-flow | flow-level batch orchestration | — | migrate |
| 014 | pocketflow-thinking | chain-of-thought GENERATE chain | R4 | ✅ seed |
| 015 | pocketflow-chat-memory | short+long-term @memory pattern | — | migrate |
| 016 | pocketflow-mcp | CALL mcp_tool pattern | — | migrate |
| 017 | pocketflow-judge | evaluator-optimizer WHILE loop | R3 | ✅ seed |
| 018 | pocketflow-debate | adversarial 2-agent + judge | — | migrate |
| 019 | pocketflow-agentic-rag | agent decides which docs to read | — | migrate |
| 020 | pocketflow-heartbeat | periodic monitoring + nested WORKFLOW | — | migrate |
| 021 | pocketflow-self-healing-mermaid | self-repair WHILE + EVALUATE | — | migrate |

### Tier 3 — Intermediate Pipelines (030–039) ★★☆ Intermediate

| # | Recipe | Key SPL pattern | NeurIPS | Status |
|---|--------|-----------------|---------|--------|
| 030 | pocketflow-lead-generation | scrape→enrich→score→email pipeline | — | migrate |
| 031 | pocketflow-invoice | vision PDF + structured validation | — | migrate |
| 032 | pocketflow-deep-research | recursive map-reduce WHILE loop | R5 | ✅ seed |
| 033 | pocketflow-text2sql | nl→sql→execute→explain | — | migrate |
| 034 | pocketflow-communication | async inter-agent messaging | — | migrate |

### Tier 4 — Advanced / Production (040–049) ★★★ Advanced

| # | Recipe | Key SPL pattern | NeurIPS | Status |
|---|--------|-----------------|---------|--------|
| 040 | pocketflow-coding-agent | 6 tools + memory + patch subflow | — | migrate |
| 041 | pocketflow-agent-skills | skill registry + dynamic dispatch | — | migrate |

### Tier 5 — Extended PocketFlow Catalog (050–099)

Recipes in the directory but not in the PocketFlow README catalog.
Migrate after Tiers 1–4 are complete.

| # | Recipe | Notes |
|---|--------|-------|
| 050 | pocketflow-a2a | agent-to-agent protocol |
| 051 | pocketflow-async-basic | async primitives |
| 052 | pocketflow-batch | basic batch runner |
| 053 | pocketflow-cli-hitl | CLI human-in-the-loop |
| 054 | pocketflow-code-generator | code gen without agent loop |
| 055 | pocketflow-flow | basic flow wiring |
| 056 | pocketflow-majority-vote | ensemble voting |
| 057 | pocketflow-tao | TAO pattern |
| 058 | pocketflow-tool-crawler | web crawler tool |
| 059 | pocketflow-tool-database | DB tool integration |
| 060 | pocketflow-tool-embeddings | embeddings tool |
| 061 | pocketflow-tool-pdf-vision | PDF vision tool |
| 062 | pocketflow-tool-search | search tool |
| 063 | pocketflow-tracing | execution tracing / observability |
| 064 | pocketflow-visualization | graph visualization |

### Deferred indefinitely — framework/UI/runtime concerns

| Recipe | Reason |
|--------|--------|
| pocketflow-fastapi-{background,hitl,websocket} | FastAPI server wiring; no SPL workflow logic |
| pocketflow-gradio-hitl | UI framework; use 41_human_steering as SPL reference |
| pocketflow-streamlit-fsm | UI framework |
| pocketflow-voice-chat | Audio I/O; covered by cookbook/60_voice_dialogue |
| pocketflow-google-calendar | Generic tool; covered by cookbook/36_tool_use pattern |
| pocketflow-llm-streaming | Runtime concern; SPL abstracts streaming |

---

## Pipeline: 3-step IR path + optional S4

```
pocketflow-<recipe>/        S1-spec.md        S2.mmd          S3.spl          tools.spl
    spl3 splc describe   ──►  text2mmd   ──►  mmd2spl   ──►  promote   ──►  (S4 manual)
```

S4 is only needed when the source has non-LLM Python helpers in `utils.py`.
Port each helper into `tools.spl` as a `CREATE TOOL_API ... AS PYTHON $$ ... $$` block.
Skip S4 for recipes where `utils.py` only wraps `call_llm`.

> **Note:** Use `spl3 splc describe` (not `spl3 describe`) for Python source.
> `spl3 describe` generates a spec from an existing **`.spl` file**.
> `spl3 splc describe` reads any source folder (Python/PocketFlow) and is the
> correct S1 tool.

### Per-recipe commands

```bash
# Set environment once per session
export ADAPTER=claude_cli
export MODEL_ID=claude-sonnet-4-6
export MODEL=sonnet

# Set per recipe
export NUM=004
export RECIPE=agent
export PF=$HOME/projects/wgong/PocketFlow/cookbook/pocketflow-$RECIPE
export DEST=$HOME/projects/digital-duck/SPL.py/cookbook-pocketflow/${NUM}_$RECIPE
export OUT=$DEST/migrate

mkdir -p "$OUT"

# S1 — describe Python source → spec
spl3 splc describe "$PF" \
    --include-docs \
    --adapter $ADAPTER --model $MODEL_ID \
    -o "$OUT/S1-$RECIPE-$MODEL-spec.md"

# ⚠️ HUMAN CHECKPOINT — verify spec covers all functions, control flow, tools

# S2 — spec → Mermaid topology
spl3 text2mmd "$OUT/S1-$RECIPE-$MODEL-spec.md" \
    --adapter $ADAPTER --model $MODEL_ID \
    --no-defaults \
    -o "$OUT/S2-$RECIPE-$MODEL.mmd"

# ⚠️ HUMAN CHECKPOINT — verify diagram: nodes, back-edges, loops, no dangling nodes

# S3 — Mermaid → SPL workflow
spl3 mmd2spl "$OUT/S2-$RECIPE-$MODEL.mmd" \
    --adapter $ADAPTER --model $MODEL_ID \
    --validate \
    -o "$OUT/S3-$RECIPE-$MODEL.spl"

# ⚠️ HUMAN CHECKPOINT — spl3 validate + spl3 run smoke test; polish then promote
cp "$OUT/S3-$RECIPE-$MODEL.spl" "$DEST/$RECIPE.spl"

# S4 (optional) — port utils.py helpers into tools.spl using CREATE TOOL_API
# Only needed when the PocketFlow recipe has non-LLM Python helper functions.
# Recipes where utils.py only has call_llm (chat, structured_output, workflow,
# map_reduce, chat_guardrail) need no tools.spl — SPL handles LLM calls natively.
#
# For recipes with real tools (agent → search_web; rag → embed/chunk/faiss;
# thinking → YAML/thought helpers), create tools.spl manually:
#
# $DEST/tools.spl  →  one CREATE TOOL_API block per helper function
```

### Batch helper script

```bash
#!/usr/bin/env bash
# scripts/migrate_pocketflow.sh <num> <recipe> [adapter] [model_id]
# Example: bash scripts/migrate_pocketflow.sh 006 map-reduce
set -euo pipefail

NUM="${1:?Usage: $0 <num> <recipe-name>}"
RECIPE="${2:?Usage: $0 <num> <recipe-name>}"
ADAPTER="${3:-claude_cli}"
MODEL_ID="${4:-claude-sonnet-4-6}"
MODEL="${MODEL_ID##*/}"

PF="$HOME/projects/wgong/PocketFlow/cookbook/pocketflow-$RECIPE"
DEST="$HOME/projects/digital-duck/SPL.py/cookbook-pocketflow/${NUM}_$RECIPE"
OUT="$DEST/migrate"
mkdir -p "$OUT"

echo "=== S1: splc describe ==="
spl3 splc describe "$PF" --include-docs \
    --adapter "$ADAPTER" --model "$MODEL_ID" \
    -o "$OUT/S1-$RECIPE-$MODEL-spec.md"

echo "=== S2: text2mmd ==="
spl3 text2mmd "$OUT/S1-$RECIPE-$MODEL-spec.md" \
    --adapter "$ADAPTER" --model "$MODEL_ID" \
    --no-defaults \
    -o "$OUT/S2-$RECIPE-$MODEL.mmd"

echo ""
echo "⚠️  CHECKPOINT — review $OUT/S2-$RECIPE-$MODEL.mmd"
read -rp "Press Enter to continue to S3, Ctrl-C to abort..."

echo "=== S3: mmd2spl ==="
spl3 mmd2spl "$OUT/S2-$RECIPE-$MODEL.mmd" \
    --adapter "$ADAPTER" --model "$MODEL_ID" \
    --validate \
    -o "$OUT/S3-$RECIPE-$MODEL.spl"

echo ""
echo "⚠️  CHECKPOINT — review $OUT/S3-$RECIPE-$MODEL.spl"
read -rp "Press Enter to promote to cookbook-pocketflow, Ctrl-C to abort..."

cp "$OUT/S3-$RECIPE-$MODEL.spl" "$DEST/$RECIPE.spl"
echo "Done → $DEST/$RECIPE.spl"
```

### Known pipeline pitfalls (from NeurIPS-26-lab/notes.md)

| Step | Issue | Status |
|------|-------|--------|
| S2 | `\n` in node labels, Unicode `→`, wrong `{{}}` shape | fixed in spl3 |
| S3 | LLM preamble prose before ` ```spl ` fence | fixed in spl3 |
| S3 | Truncation when inner ` ```yaml ` fence hit by regex | fixed in spl3 |
| S3 | Semicolons after INPUT/OUTPUT declarations | fix prompt; remove manually |
| S3 | Nested `DO...END;` wrappers | fix prompt; remove extra `END;` |
| S3 | LLM preamble + `___SPL_BEGIN___` + truncated body | re-run S3 (regeneration usually fixes it) |

---

## Execution Order

```
Phase 0 (done)       Seed 5 NeurIPS recipes → 004, 005, 014, 017, 032  + tools.spl
Phase 1 (done)       Tier 1 remaining: 001, 002, 003, 006, 008  ✅ all validated
Phase 2 (week 2)     Tier 2: 010-021
Phase 3 (week 3)     Tier 3: 030-034 + Tier 4: 040-041
Phase 4 (ongoing)    Tier 5: 050-064 as needed
```

---

## Expanded Scope — Multi-Framework Registry

The guiding principle extends beyond PocketFlow to any open-source agentic workflow framework:

| Source framework | Location | Status |
|-----------------|----------|--------|
| PocketFlow | `cookbook-pocketflow/` | active (phases 0-1 done) |
| LangGraph | `cookbook-langgraph/` (planned) | not started |

### SPL Workflow Registry (planned)

Each migrated recipe is a candidate for the SPL workflow registry: a searchable catalog
of named workflows that can be `IMPORT`-ed or `CALL`-ed by other workflows.

Registry design principles:
- Each recipe's canonical `.spl` + `tools.spl` pair is the unit of registration.
- Registry key: `{framework}/{name}` (e.g. `pocketflow/agent`, `langgraph/react_agent`)
- `spl3 registry list` — enumerate available workflows
- `spl3 registry push <dir>` — promote a recipe to the registry
- `spl3 registry pull pocketflow/agent` — fetch and install locally

This is implemented in `spl3/hub_registry.py` for Momagrid-hosted workflows;
local registry support is in `spl3/registry.py`.

---

## Reference Materials

| Path | Contents |
|------|----------|
| `NeurIPS-26-lab/` | 5 validated recipes + notes.md |
| `NeurIPS-26-lab/notes.md` | Detailed issue log — mermaid bugs, SPL syntax fixes |
| `NeurIPS-26-lab/R*/tests/claude_cli/claude/S3-*.spl` | Best-quality seed .spl files |
| `PocketFlow/cookbook/README.md` | Full catalog with ☆/★ difficulty ratings |
| `PocketFlow/cookbook/pocketflow-deep-research/flow-splc-python_pocketflow-spec.md` | Example S1 spec |
