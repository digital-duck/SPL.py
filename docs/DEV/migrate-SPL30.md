# SPL30 → SPL.py Migration Plan

**Date:** 2026-05-11  
**Branch:** `intent-eng`  
**Source:** `/home/papagame/projects/digital-duck/SPL30`  
**Target:** `/home/papagame/projects/digital-duck/SPL.py`  
**Status:** ✅ Migration complete — all 4 tasks done on `intent-eng`

---

## Background

SPL.py is the canonical repo going forward. SPL30 is being deprecated. This document
records what is worth migrating and what can be left behind.

---

## Analysis Summary

### Items in SPL30 missing from SPL.py

#### M1 — Text2Mermaid Streamlit page (high value)

**File:** `spl3/ui/streamlit/pages/0_🗺️_Text2Mermaid.py` (454 lines)

A full Streamlit page that converts a natural language workflow description into a
Mermaid diagram for **human visual approval before SPL compilation**. This is a
pre-compilation intent validation step: the user sees the structural diagram (nodes,
branches, loops) and can approve or refine it before the expensive text2spl step runs.

Pipeline:
```
description → [LLM] → Mermaid diagram → user approves
                                              │
                                   session_state["mermaid_approved"]
                                              │
                                    Text2SPL page uses it as structural context
```

Entirely absent from SPL.py.

#### M2 — Mermaid approval context in Text2SPL page (high value)

**File:** `spl3/ui/streamlit/pages/1_⚡_Text2SPL.py` (12 lines to re-add)

SPL30's Text2SPL page reads `session_state["mermaid_approved"]` and, when set,
passes the approved Mermaid diagram as a structural blueprint to the text2spl compiler:
```
"Use the following Mermaid diagram as the structural blueprint
 (nodes → SPL steps, diamonds → EVALUATE, back-edges → WHILE loops):\n\n{diagram}"
```
SPL.py's version of this page was stripped of this integration. Also, SPL30 calls
`spl` (v2 CLI) instead of `spl3` in the run command — SPL.py already has the correct
`spl3` call.

#### M3 — SPL_UI.py dashboard metric (high value)

**File:** `spl3/ui/streamlit/SPL_UI.py`

SPL30 shows a 6th column "Diagrams approved" on the dashboard home. Minor cosmetic
addition once M1/M2 are in place.

#### M4 — GeminiCLI adapter improvements (medium value)

**Files:**
- SPL30: `spl3/adapters/gemini_cli.py`
- SPL.py: `spl/adapters/gemini_cli.py` (exists but is simpler)

SPL30's version has improvements over SPL.py's:
- Inherits `MultiModalAdapter` (not just `LLMAdapter`) — enables multimodal paths
- Uses `time.perf_counter()` for accurate latency measurement
- Raises `ModelOverloaded` on quota/rate-limit errors (enables `EXCEPTION WHEN ModelOverloaded` in .spl files)
- Adds `logging` via `logger = logging.getLogger(__name__)`

Action: merge these improvements into `spl/adapters/gemini_cli.py` (not copy the SPL30
file wholesale — SPL.py's base class path is `spl.adapters.base`, SPL30's was `spl3.adapters.base`).

---

### SPL.py already ahead of SPL30 (no migration needed)

| Component | SPL30 | SPL.py status |
|---|---|---|
| `transpiler_pocketflow.py` | 712 lines | **1308 lines** — pattern detection (react/self_refine/linear) |
| `transpiler_langgraph.py` | 777 lines | **1049 lines** — fan-out/merge, IMPORT resolution, CALL PARALLEL |
| `spl3/cli.py` (text2spl) | basic | `--prompt` debug flag, `format_spl()`, real parser validation |
| `spl3/parser.py` | no trailing comma | trailing commas in arg lists, proper NONE token |
| `spl3/executor.py` | numeric EVALUATE only | string `=`/`!=` in EVALUATE conditions |
| `spl3/adapters/__init__.py` | routes to spl3 path | proper `spl/` path, momagrid always-available |
| `spl3/compare/` | absent | present (engine, report, tiers) |
| `spl3/image_ops.py` | absent | present |
| `spl3/spl2mmd.py` | absent | present |
| `spl3/text2spl/` | empty stub | full module |
| `cookbook/` recipes | 50–64 only | 00–49, 50–65 |
| `cookbook/tools/` | no file_tools, finance_helpers | both present |
| Core files (composer, registry, hub_registry, peer, types, event, status, ast_nodes, code_rag) | same or older | same or newer |

---

## Migration Tasks

All tasks completed on branch `intent-eng` on 2026-05-11.

### Task 1 — Copy Text2Mermaid page ✅

Copied `SPL30/spl3/ui/streamlit/pages/0_🗺️_Text2Mermaid.py` to
`SPL.py/spl3/ui/streamlit/pages/`. No import fixes needed — the page already
tries `spl3.adapters` first and falls back to `spl.adapters`, and contains no
direct `spl` CLI calls.

### Task 2 — Re-add Mermaid context to Text2SPL page ✅

In `spl3/ui/streamlit/pages/1_⚡_Text2SPL.py`, re-added:

1. **Approved diagram banner** — shown above the compile button when a diagram
   has been approved on the Text2Mermaid page; includes a "Clear diagram context"
   button and a tip caption when no diagram is approved.

2. **`compile_desc` augmentation** — at compile time, if `mermaid_approved` is set,
   the description passed to `spl3 text2spl` is extended with the approved diagram
   as a structural blueprint:
   ```
   Use the following Mermaid diagram as the structural blueprint
   (nodes → SPL steps, diamonds → EVALUATE, back-edges → WHILE loops):
   ```
   Otherwise `compile_desc = desc` (no change to existing behaviour).

### Task 3 — Update SPL_UI.py dashboard ✅

In `spl3/ui/streamlit/SPL_UI.py`:
- Added `n_diagrams` count from `data/diagrams/*.mmd`
- Changed `st.columns(5)` → `st.columns(6)`
- Inserted `col1.metric("Diagrams approved", n_diagrams, ...)` as the first column
- Shifted existing metrics to `col2`–`col6`

### Task 4 — Upgrade gemini_cli adapter ✅

In `spl/adapters/gemini_cli.py`:
- Added `import logging` and `logger = logging.getLogger(__name__)`
- Added `logger.warning(...)` on timeout and quota/rate-limit errors
- Added `logger.error(...)` on non-zero exit code

**Not changed:** base class remains `LLMAdapter` (consistent with all other `spl/`
adapters — none use `MultiModalAdapter`). Timing already uses `time.perf_counter()`
via `_measure_time()` / `_elapsed_ms()` in the base class. `ModelOverloaded` raise
on quota errors was already present in SPL.py's version.

---

## Not Migrating

The following SPL30 artifacts are logs, benchmark results, and generated files
with no code value:
- `cookbook/05_self_refine/logging/` — execution logs
- `cookbook/05_self_refine/targets/` and `targets-ref/` — generated transpiler outputs
- `cookbook/05_self_refine/benchmark-*.{sh,md}` — benchmark scripts and results
- `review.spl` — scratch file in repo root
- `approval-fixed.{html,mmd}` — scratch diagram exports

---


## Git commit

```bash
git add .
git commit -m "migrate and deprecate SPL30 repo"

git push --set-upstream origin intent-eng
```

## Intent Engineering (next direction)

To be documented once the detailed plan is shared. The `intent-eng` branch serves
as the working branch for both this completed migration and upcoming intent engineering
features.
