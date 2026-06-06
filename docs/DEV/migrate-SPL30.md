# SPL30 → SPL.py Migration Plan

**Date:** 2026-05-11  
**Branch:** `intent-eng`  
**Source:** `/home/papagame/projects/digital-duck/SPL30`  
**Target:** `/home/papagame/projects/digital-duck/SPL.py`  
**Status:** Pending — awaiting branch creation

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

#### M3 — SPL_UI.py dashboard metric (low value)

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

Work to be done on branch `intent-eng`.

### Task 1 — Copy Text2Mermaid page

```bash
cp /home/papagame/projects/digital-duck/SPL30/spl3/ui/streamlit/pages/0_🗺️_Text2Mermaid.py \
   /home/papagame/projects/digital-duck/SPL.py/spl3/ui/streamlit/pages/
```

Verify imports: the page uses `spl3.adapters` and `spl` CLI commands — confirm these
resolve correctly in the SPL.py package layout. The page calls `spl text2spl ...`; update
to `spl3 text2spl ...`.

### Task 2 — Re-add Mermaid context to Text2SPL page

In `spl3/ui/streamlit/pages/1_⚡_Text2SPL.py`, re-add:

1. Approved diagram banner section (~lines 207–217 in SPL30 version):
   ```python
   if st.session_state.get("mermaid_approved") and st.session_state.get("mermaid_diagram"):
       with st.expander("✓ Approved Mermaid diagram will be used as structural context", expanded=False):
           st.code(st.session_state["mermaid_diagram"], language="markdown")
           if st.button("Clear diagram context", key="btn_clear_mermaid"):
               st.session_state["mermaid_approved"] = False
               st.rerun()
   else:
       st.caption("Tip: approve a diagram on the **Text2Mermaid** page to guide compilation.")
   ```

2. Approved diagram augmentation at compile time (~lines 274–284 in SPL30 version):
   ```python
   approved_diagram = st.session_state.get("mermaid_approved") and st.session_state.get("mermaid_diagram", "")
   if approved_diagram:
       compile_desc = (
           f"{desc}\n\n"
           f"Use the following Mermaid diagram as the structural blueprint "
           f"(nodes → SPL steps, diamonds → EVALUATE, back-edges → WHILE loops):\n\n"
           f"{approved_diagram}"
       )
   else:
       compile_desc = desc
   ```

### Task 3 — Update SPL_UI.py dashboard

Add the "Diagrams approved" metric column in `spl3/ui/streamlit/SPL_UI.py`:
- Change `st.columns(5)` to `st.columns(6)`
- Add `n_diagrams` count from `data/diagrams/*.mmd`
- Insert `col1.metric("Diagrams approved", n_diagrams, ...)`

### Task 4 — Upgrade gemini_cli adapter

In `spl/adapters/gemini_cli.py`:
- Change base class from `LLMAdapter` to `MultiModalAdapter` (import from `spl3.adapters.base_multimodal`)
  - Note: verify `MultiModalAdapter` is accessible from `spl/` — may need to import from `spl3`
- Add `import time` and replace `self._measure_time()` with `time.perf_counter()`
- Add `import logging` and `logger = logging.getLogger(__name__)`
- Add `ModelOverloaded` raise on quota/rate-limit errors in stderr parsing
- Keep SPL.py's `spl.adapters.base` import path (not SPL30's `spl3.adapters.base`)

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

## Intent Engineering (next direction)

To be documented once the detailed plan is shared. The `intent-eng` branch will serve
as the working branch for both this migration and the new intent engineering features.
