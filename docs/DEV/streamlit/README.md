# SPL Studio — Streamlit UI Plan

**Date:** 2026-05-11  
**Branch:** `intent-eng`  
**Location:** `spl3/ui/streamlit/`

---

## Current Pages (as-is)

| Page | File | Purpose | Status |
|---|---|---|---|
| Home | `SPL_UI.py` | Dashboard metrics (scripts, executions, diagrams, RAG) | Good as-is |
| 0 — Text2Mermaid | `0_🗺️_Text2Mermaid.py` | NL → Mermaid diagram → human conceptual audit → `session_state["mermaid_approved"]` | Good as-is |
| 1 — Text2SPL | `1_⚡_Text2SPL.py` | **Two-step IR pipeline:** (a) `text2mmd` — generate Mermaid from description, human reviews conceptual audit; (b) `mmd2spl` — compile approved `.mmd` (1st IR) into `.spl` script (2nd IR). The approved diagram is injected as structural context into the compiler. | Good as-is |
| 2 — Review | `2_📚_Review.py` | Browse and manage saved text2SPL scripts | No experiment linkage |
| 3 — Code-RAG | `3_🔍_Code_RAG.py` | Manage RAG store for the text2spl compiler | Good as-is |
| 4 — SPLc | `4_🔧_SPLc.py` | Compile `.spl` → target language (LangGraph, Go, TS, etc.) | Missing `python/pocketflow`; hardcoded paths |
| 5 — Target Review | `5_📄_Target_Review.py` | Browse compiled target artifacts | No score display |

### The Two-Step Intent Pipeline (Page 1 detail)

The Text2SPL page now implements the first two gates of the intent engineering pipeline:

```
Natural language description
        │
        ▼  [text2mmd]
  Mermaid diagram (.mmd)           ← 1st IR
        │
        ▼  [Human Conceptual Audit]
  Approved diagram in session_state
        │
        ▼  [mmd2spl]
  SPL workflow script (.spl)       ← 2nd IR
        │
        ▼  [spl3 run]
  Execution result
```

Each IR is a checkpoint where structural errors (wrong branching, missing loops,
wrong agent boundaries) can be caught before the next transformation.

---

## Proposed New Pages

### Page 6 — NeurIPS Lab ⭐ (high priority)

**Purpose:** Replace the hand-edited shell scripts (`claude_cli-S8910.sh`,
`openrouter-claude-S8910.sh`, etc.) with a supervised UI that makes it easy
to execute, track, and checkpoint the full 15-run experiment matrix.

**Context:** The NeurIPS-26 NDD round-trip closure experiment runs a 10-step
pipeline (S1→S10) across 5 recipes × 3 models. Phase 1 (S1–S6) is the full
IR pipeline; Phase 2 (S7–S10) is the ablation study comparing IR vs direct
vibe coding. S6 files exist for all 15 runs; ablation (S7–S10) is partially
complete and ongoing — this page is needed to continue those experiments.

**Features:**

1. **Experiment matrix grid**
   - Rows: recipes R1–R5 (agent, rag, judge, thinking, research)
   - Columns: models (claude / qwen / gemini)
   - Cells: per-step completion badge — `✅ done | ⏳ running | ❌ failed | 🔲 not started`
   - Cell data derived by scanning the `NeurIPS-26-lab/` filesystem for `S*-*.md` files

2. **Step runner**
   - Select recipe + model + step (S1–S10) from dropdowns
   - UI constructs and displays the exact `spl3` CLI command
   - Execute button streams stdout/stderr live
   - Output saved to the canonical path (`$OUT/S{N}-...`)

3. **Human checkpoint panel**
   - Steps S1, S2, S3, S4, S6, S7, S10 require human review
   - After a step completes, shows the artifact inline (spec, Mermaid, .spl, diff report)
   - "Mark reviewed + passed" button sets checkpoint status
   - Optional notes field appended to `notes.md` automatically

4. **Batch automated steps**
   - S5, S8, S9 have no human checkpoint
   - "Run all pending automated steps" button for a selected model

5. **Step output viewer**
   - Click any matrix cell to read the full artifact inline
   - Supports `.md`, `.spl`, `.mmd`, `.py` files

**Step reference:**

| Step | Command | Checkpoint? |
|---|---|---|
| S1 | `spl3 splc describe $SRC --include-docs` | ✅ Human |
| S2 | `spl3 text2mmd $S1_spec` | ✅ Human |
| S3 | `spl3 mmd2spl $S2_mmd` | ✅ Human |
| S4 | `spl3 splc compile --target python/pocketflow --llm` | ✅ Human |
| S5 | `spl3 splc describe $S4_py` | Automated |
| S6 | `spl3 compare $S1_spec $S5_spec` | ✅ Human |
| S7 | `spl3 vibe --description $S1_spec` | ✅ Human |
| S8 | `spl3 splc describe $S7_dir` | Automated |
| S9 | `spl3 compare $S1_spec $S8_spec` | Automated |
| S10 | `spl3 compare $S6_diff $S9_diff` | ✅ Human |

---

### Page 7 — Ablation Results Dashboard ⭐ (high priority)

**Purpose:** Scan all existing S6/S9/S10 result files, extract scores, build
the NeurIPS ablation table automatically, and export it for the paper.

**Context:** This page is the direct output for the NeurIPS-26 paper's main
results section. The ablation tests are not yet complete — this UI is designed
to work incrementally as more runs finish, showing partial results at any time.

**Features:**

1. **Score extraction**
   - Scans `NeurIPS-26-lab/R{1-5}-*/tests/*/*/S6*.md`, `S9*.md`, `S10*.md`
   - Extracts numeric scores using the pattern that `spl3 compare` outputs
   - Handles missing files gracefully (shows `—` for incomplete cells)

2. **Ablation table**
   ```
   Recipe     | claude S6 | claude S9 | ΔIR | qwen S6 | qwen S9 | ΔIR | gemini S6 | gemini S9 | ΔIR
   R1-agent   |   0.87    |   0.71    | +0.16 |  ...
   R2-rag     |   0.82    |   ...
   ...
   Mean       |   ...
   ```
   - ΔIR = S6 score − S9 score (positive = IR pipeline adds value)
   - Color coding: green ΔIR > 0, red ΔIR < 0

3. **Per-cell drill-down**
   - Click any score cell to read the full S6, S9, or S10 report inline

4. **Export**
   - CSV export (one click)
   - LaTeX `\tabular` export ready to paste into the NeurIPS paper

5. **Completion tracker**
   - Shows "N/15 runs complete (Phase 1)" and "M/15 runs complete (Phase 2)"
   - Lists which recipe × model combinations still need S7–S10

---

### Page 8 — Intent Engineering Pipeline (medium priority)

**Purpose:** A guided 5-gate walkthrough for a single workflow — the showpiece
demo for the intent engineering paper and conference talks.

**Context:** Demonstrates that one natural language description can flow through
the full intent engineering pipeline and produce equivalent behaviour in two
runtimes (PocketFlow and LangGraph), with ΔS measured at the end.

**Features:**

1. **Stepper UI** — gate-by-gate progress indicator
2. **Gate 1** (Conceptual Audit): Text2Mermaid → human approval → links to page 0
3. **Gate 2** (Synthesis): text2mmd + mmd2spl → shows `.mmd` and `.spl` side by side
4. **Gate 3** (Compile): `splc` → generates both PocketFlow and LangGraph Python
5. **Gate 4** (Functional Grounding): runs both targets with same test input; shows side-by-side outputs
6. **Gate 5** (Cross-runtime ΔS): `spl3 compare` on both outputs; displays score
7. **Export demo report** — shareable markdown summary of the full run (for paper figures / appendix)

---

## Refactoring Tasks

### R1 — Shared constants: `ui_config.py`

`ADAPTERS` and `MODELS` dicts are copy-pasted across pages 0, 1, and 4 with
subtle differences (page 0 is missing `gemini_cli`; page 4 has a different
model list). Extract to `spl3/ui/streamlit/ui_config.py`.

```python
# ui_config.py
ADAPTERS = ["ollama", "claude_cli", "gemini_cli", "anthropic", ...]
MODELS: dict[str, list[str]] = { ... }
```

### R2 — Shared `_parse_run_output()`: `ui_utils.py`

`_parse_run_output()` is duplicated verbatim in pages 1 and 2. Move to
`spl3/ui/streamlit/ui_utils.py` alongside `db.py`.

### R3 — Fix page 4 (SPLc) hardcoded paths

```python
# Current — brittle
SPLC_CLI = SPL_DIR / "splc" / "cli.py"

# Fix — use installed CLI, same as all other pages
subprocess.run(["spl3", "splc", "--target", target, ...])
```

### R4 — Add `python/pocketflow` to SPLc page

`SUPPORTED_LANGS` in page 4 has `python/langgraph`, `python/crewai`,
`python/autogen` but is missing `python/pocketflow` — now the primary target
for all NeurIPS experiments.

```python
SUPPORTED_LANGS = {
    "python/pocketflow": "Python — PocketFlow (ETL-style, lightweight)",  # add
    "python/langgraph":  "Python — LangGraph",
    ...
}
```

### R5 — Page renumbering (cosmetic, do last)

Current numbering has page 0 inserted before the original 1–5 sequence.
Proposed logical order reflecting the intent engineering pipeline:

| New # | Page | Role in pipeline |
|---|---|---|
| 0 | Text2Mermaid | Gate 1: Conceptual Audit |
| 1 | Text2SPL | Gate 2: Synthesis (text2mmd + mmd2spl) |
| 2 | SPLc | Gate 3: Compile to target |
| 3 | Target Review | Gate 3 output viewer |
| 4 | Review | Script knowledge base |
| 5 | Code-RAG | RAG store |
| 6 | NeurIPS Lab | Experiment runner |
| 7 | Ablation Results | Paper table builder |
| 8 | Intent Pipeline | Full 5-gate demo |

---

## Priority Order

| Priority | Item | Rationale |
|---|---|---|
| 1 | **Page 7 — Ablation Results** | S6 files exist for all 15 runs; unblocks paper table now |
| 2 | **Page 6 — NeurIPS Lab** | Replaces shell scripts; needed to complete remaining S7–S10 runs |
| 3 | **R4 — Add pocketflow to SPLc** | 5-minute fix; needed for lab page and intent-eng demo |
| 4 | **R1/R2 — Shared constants + utils** | Clean up before adding more pages |
| 5 | **Page 8 — Intent Engineering Pipeline** | Demo showpiece; build after lab + results pages stable |
| 6 | **R3/R5 — Path fix + renumbering** | Before paper screenshots or public demo |
