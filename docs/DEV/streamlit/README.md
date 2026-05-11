# SPL Studio — Streamlit UI

**Branch:** `intent-eng`  
**Location:** `spl3/ui/streamlit/`  
**Last updated:** 2026-05-11  
**Commits:** `9437190` (UI pages), `bd89246` (memory layer)

---

## Page Inventory

| Page | File | Purpose | Status |
|---|---|---|---|
| Home | `SPL_UI.py` | Dashboard: scripts, executions, diagrams approved, RAG, cookbook metrics | ✅ Done |
| 0 — Text2Mermaid | `0_🗺️_Text2Mermaid.py` | NL → Mermaid diagram → human conceptual audit → `session_state["mermaid_approved"]` | ✅ Done |
| 1 — Text2SPL | `1_⚡_Text2SPL.py` | Two-step IR: `text2mmd` (conceptual audit) → `mmd2spl` (.spl); runs via `spl3 run` | ✅ Done |
| 2 — Review | `2_📚_Review.py` | Browse and re-run saved text2SPL scripts | ✅ Done |
| 3 — Code-RAG | `3_🔍_Code_RAG.py` | Manage RAG store for the text2spl compiler | ✅ Done |
| 4 — SPLc | `4_🔧_SPLc.py` | Compile `.spl` → PocketFlow / LangGraph / Go / TS / CrewAI / AutoGen | ✅ Fixed |
| 5 — Target Review | `5_📄_Target_Review.py` | Browse compiled target artifacts | ✅ Done |
| 6 — NeurIPS Lab | `6_🧪_NeurIPS_Lab.py` | Experiment runner: 5 recipes × 3 models × 10 steps | ✅ **New** |
| 7 — Ablation Results | `7_📊_Ablation_Results.py` | S6/S9/S10 score extraction, ablation table, CSV + LaTeX export | ✅ **New** |
| 8 — Intent Pipeline | *(planned)* | Guided 5-gate intent engineering demo | 🔲 Planned |

---

## The Two-Step Intent Pipeline (Page 1)

```
Natural language description
        │
        ▼  [text2mmd]
  Mermaid diagram (.mmd)           ← 1st IR  [Human Conceptual Audit]
        │
        ▼  [mmd2spl]
  SPL workflow script (.spl)       ← 2nd IR
        │
        ▼  [spl3 run]
  Execution result
```

Each IR is a human checkpoint where structural errors (wrong branching, missing
loops, wrong agent boundaries) are caught before the next transformation.

---

## Deliverables — 2026-05-11

### New shared modules

| File | Contents |
|---|---|
| `ui_config.py` | `ADAPTERS`, `MODELS`, `JUDGE_ADAPTER/MODEL`, `NEURIPS_RECIPES/RECIPE_DIRS/MODELS` |
| `ui_utils.py` | `parse_run_output`, `extract_compare_score`, `run_spl3`, `find_step_file`, `get_memory_db` |

### Refactoring applied

| Task | Change |
|---|---|
| R1 — Shared ADAPTERS/MODELS | Pages 1, 4 now import from `ui_config.py`; `gemini_cli` added to all pages |
| R2 — Shared `parse_run_output` | Pages 1, 2 import from `ui_utils.py`; duplicate removed |
| R3 — Fix SPLc hardcoded paths | `conda run -n spl2 python splc/cli.py` → `spl3 splc compile`; sidebar probes `spl3 splc --help` |
| R4 — Add `python/pocketflow` | First entry in SPLc `SUPPORTED_LANGS` (⭐); adapter/model selectors added |

### Page 6 — NeurIPS Lab (`6_🧪_NeurIPS_Lab.py`)

Replaces `claude_cli-S8910.sh` / `openrouter-*.sh` shell scripts with a supervised UI.

**Experiment matrix** — 5 recipes × 3 models grid showing per-step completion
badges (`✅ / 🔲`) derived by scanning the `NeurIPS-26-lab/` filesystem for
`S*-*.md` files. Refreshes every 15 seconds.

**Step runner** — select recipe / model / step (S1–S10); UI builds the exact
`spl3` CLI command and displays it before running. Output streamed to screen.

| Step | Command built | Checkpoint |
|---|---|---|
| S1 | `spl3 splc describe $src --include-docs` | ✅ Human |
| S2 | `spl3 text2mmd $S1` | ✅ Human |
| S3 | `spl3 mmd2spl $S2` | ✅ Human |
| S4 | `spl3 splc compile $S3 --lang python/pocketflow` | ✅ Human |
| S5 | `spl3 splc describe $S4_dir` | Automated |
| S6 | `spl3 compare $S1 $S5` (judge=opus-4-6) | ✅ Human |
| S7 | `spl3 vibe --description $S1` | ✅ Human |
| S8 | `spl3 splc describe $S7_vibe_dir` | Automated |
| S9 | `spl3 compare $S1 $S8` (judge=opus-4-6) | Automated |
| S10 | `spl3 compare $S6 $S9` (judge=opus-4-6) | ✅ Human |

**Batch automated steps** — one button runs all pending S5 / S8 / S9 for a
selected model across all 5 recipes.

**Artifact viewer** — read any step output (`.md`, `.spl`, `.mmd`, `.py`) inline
by selecting recipe / model / step.

**Human checkpoint notes** — text field appended to the recipe's `notes.md`
with date and step label.

### Page 7 — Ablation Results (`7_📊_Ablation_Results.py`)

Produces the NeurIPS paper's main results table directly from the filesystem.
Ablation runs are incomplete; page shows `—` for missing cells and fills in
as experiments complete.

**Score extraction** — `extract_compare_score()` in `ui_utils.py` scans
S6/S9/S10 markdown files for patterns: `Score: 0.82`, `**Score:** 0.82`,
`0.82 / 1.0`, `similarity_score: 0.82`.

**Ablation table** — 5 recipes × 3 models:

```
Recipe    │ claude S6 │ claude S9 │ ΔIR  │ qwen S6 │ qwen S9 │ ΔIR  │ …
agent     │   0.87    │   0.71    │ +0.16│   …
rag       │   0.82    │    —      │  —   │
…
Mean      │   …
```

ΔIR = S6 − S9 (positive = IR pipeline adds value over direct vibe coding).

**Export** — CSV and LaTeX `\tabular` download buttons, ready for the paper.

**Drill-down** — click any recipe/model combination to read the full S6, S9,
or S10 report inline.

**Completion tracker** — metric tiles showing Phase 1 (S6) and Phase 2 (S9)
completion counts out of 15.

---

## Planned: Page 8 — Intent Engineering Pipeline

A guided 5-gate walkthrough for a single workflow — the conference demo
for the intent engineering paper. Build after ablation tests are complete.

Gates: Conceptual Audit (Mermaid) → Synthesis (text2mmd + mmd2spl) →
Compile (PocketFlow + LangGraph) → Functional Grounding (run both) →
Cross-runtime ΔS score. Exports a shareable demo report.

---

---

## Memory and Persistence

### Architecture overview

SPL Studio uses three distinct persistence stores, each with a different scope:

```
┌─────────────────────────────────────────────────────────────────┐
│  spl3/ui/streamlit/data/                                        │
│                                                                 │
│  knowledge.db   ── scripts + executions (text2SPL UI layer)    │
│  spl_memory.db  ── ui_config + workflow_sessions +             │
│                    pipeline_runs + pipeline_steps (new)         │
│  diagrams/      ── approved .mmd files (Text2Mermaid)          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  NeurIPS-26-lab/R{1-5}-*/tests/*/*/                             │
│  S1-*.md  S2-*.mmd  S3-*.spl  S4-*.py  S5-*.md                 │
│  S6-*-spec-diff.md  S9-*-vibe-diff.md  S10-*-ablation.md       │
│  (filesystem artifacts — source of truth for step outputs)     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  .spl/memory.db  (per-workflow, per-run-directory)              │
│  kv_store — workflow variables during execution                 │
│  (managed by spl/storage/memory.py — unchanged)                │
└─────────────────────────────────────────────────────────────────┘
```

### `spl3/memory/` — the new layer

**Module:** `spl3/memory/db.py`  
**Entry point:** `from spl3.memory import MemoryDB, get_memory_db`  
**POC backend:** SQLite (`spl3/ui/streamlit/data/spl_memory.db`)  
**Production backend:** PostgreSQL via `SPL_MEMORY_URL` env var

#### Backend selection

```bash
# POC default (SQLite, no setup needed)
# file auto-created at spl3/ui/streamlit/data/spl_memory.db

# Custom SQLite path
export SPL_MEMORY_URL=sqlite:///~/.spl/memory.db

# Production PostgreSQL
export SPL_MEMORY_URL=postgresql://user:pass@host:5432/spl
pip install psycopg2-binary
```

The DDL is separate for each backend (`_DDL_SQLITE` / `_DDL_POSTGRES`); the API is identical.

#### Tables

| Table | Purpose | Key columns |
|---|---|---|
| `ui_config` | Namespaced KV for UI preferences | `namespace`, `key`, `value` (JSON), `updated_at` |
| `workflow_sessions` | Every `spl3 run` invocation | `session_id`, `workflow_name`, `adapter`, `model`, `status`, `latency_ms`, `tokens_used`, `cost_usd` |
| `pipeline_runs` | Multi-step experiment runs | `pipeline_name`, `run_label`, `recipe`, `model_alias`, `adapter`, `phase`, `status` |
| `pipeline_steps` | Individual step records | `run_id`, `step`, `status`, `artifact_path`, `score`, `checkpoint_passed`, `checkpoint_note` |

#### API reference

```python
from spl3.memory import get_memory_db

db = get_memory_db()   # singleton; SQLite by default

# 1 — UI config: persist any page's settings across sessions
db.config_set("splc", "last_adapter", "claude_cli")
db.config_get("splc", "last_adapter")          # → "claude_cli"
db.config_get_namespace("splc")                # → {"last_adapter": ..., ...}

# 2 — Workflow sessions: log every spl3 run
sid = db.session_start("self_refine", spl_file="...", adapter="ollama", model="gemma3")
db.session_complete(sid, output="...", latency_ms=1450, tokens_used=320, cost_usd=0.0)
db.sessions_stats()    # → {total, completed, failed, avg_latency_ms, total_tokens, total_cost}

# 3 — Pipeline tracking: NeurIPS S1-S10, intent-eng 5-gate
run_id = db.pipeline_upsert("neurips_ndd", "R1-agent/claude",
    recipe="agent", model_alias="claude",
    adapter="claude_cli", model_id="claude-sonnet-4-6", phase=1)
db.step_upsert(run_id, "S6", status="complete", score=0.87,
    artifact_path="/path/to/S6-agent-claude-spec-diff.md")
db.step_checkpoint(run_id, "S6", passed=True, note="Strong alignment")

# 4 — Dashboard queries
db.pipeline_scores_matrix("neurips_ndd", "S6")  # all (run_label, score) rows
db.report_summary("neurips_ndd")                # totals, mean_score, checkpoints
```

#### Integration with Streamlit pages

| Page | What it writes | What it reads |
|---|---|---|
| Any page | `config_set(namespace, key, value)` on adapter/model changes | `config_get_namespace(namespace)` to restore last settings |
| Page 6 — NeurIPS Lab | Step result + score after each run; checkpoint note on human approval | — |
| Page 7 — Ablation Results | — | `pipeline_scores_matrix("neurips_ndd", "S6/S9")` as fallback when filesystem files are absent; checkpoint status per cell |
| (future) Home dashboard | — | `sessions_stats()`, `report_summary("neurips_ndd")` |

#### PostgreSQL migration checklist (when ready)

1. Provision a PostgreSQL instance and create the `spl` database
2. `pip install psycopg2-binary`
3. `export SPL_MEMORY_URL=postgresql://user:pass@host/spl`
4. Restart the Streamlit server — schema is auto-created on first connection
5. Optionally dump SQLite data and import to PostgreSQL:
   ```bash
   python -c "
   from spl3.memory import MemoryDB
   sqlite_db = MemoryDB('sqlite:///spl_memory.db')
   pg_db = MemoryDB('postgresql://user:pass@host/spl')
   # manual row-by-row migration (see db.py for table structure)
   "
   ```

#### Relationship to existing stores

| Store | File | Managed by | Scope |
|---|---|---|---|
| `knowledge.db` | `spl3/ui/streamlit/data/` | `spl3/ui/streamlit/db.py` | UI: generated scripts + their execution history |
| `spl_memory.db` | `spl3/ui/streamlit/data/` | `spl3/memory/db.py` | UI: config, sessions, pipeline tracking |
| `.spl/memory.db` | per-workflow run dir | `spl/storage/memory.py` | Runtime: workflow variables during `spl3 run` |
| `StorageConnection` | STORAGE param path | `spl/storage/storage_conn.py` | Runtime: `@var STORAGE(sqlite,...)` in `.spl` files |

---

## Remaining Tasks

| # | Task | Priority |
|---|---|---|
| 1 | Test pages 6 + 7 with live NeurIPS-26-lab data | Now |
| 2 | Complete remaining S7–S10 ablation runs via Page 6 | Now |
| 3 | Verify score extraction patterns match actual `spl3 compare` output format | Now |
| 4 | Page 8 — Intent Engineering Pipeline demo | After ablation complete |
| 5 | R5 — Page renumbering to match intent engineering gate order | Before paper screenshots |
