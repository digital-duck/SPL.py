# Recipe-67: Momagrid Parallelization Design

## Motivation

The full experiment (10 models × 20 problems × 2 solver arms = 400 cells) runs
sequentially today. With one model finishing every ~12 s (Claude) to several
minutes (large Ollama models), the wall-clock time is 4–8 hours on a single
machine.

A Momagrid — a multi-worker job grid — can reduce that to the runtime of the
*slowest single model* (~40–80 min) by running all 10 models in parallel, one
worker per model.

---

## Key Constraint: Ollama Is Sequential Per Model

Ollama serves one request at a time on a single GPU. That makes
**model** the natural unit of parallelism, not the individual cell.

| Provider     | Parallelism available       |
|--------------|-----------------------------|
| Ollama       | One worker per model        |
| Claude CLI   | No local GPU limit — can fan out across all 40 cells if desired |

The design respects this by applying a **model-affinity constraint**: all cells
for `m002` go to the same worker, all cells for `m003` to another, etc.

---

## Architecture Overview

```
run_experiment.py --emit-jobs
        │
        ▼
    jobs.json          (one JSON object per cell, 400 entries)
        │
        ▼
  Momagrid dispatcher  (reads jobs.json, groups by mid, assigns workers)
     │        │  ...  │
  worker-m001 worker-m002 ... worker-m010   (10 parallel workers)
     │        │              │
     └────────┴──────────────┘
              │
        run_cell.py          (runs one cell, appends RESULT tag to shared log)
              │
        shared log file      (file-locked appends from all workers)
              │
              ▼
    run_analysis.py          (unchanged — works on any conforming log file)
```

---

## Changes Required

### 1. `run_experiment.py` — add `--emit-jobs` flag

**What it does:** When `--emit-jobs` is passed, instead of executing cells the
script serialises the full job manifest to a JSON file and exits. All existing
logic (model/problem filtering, solver mode expansion, `--dry-run`, `--list`)
is unchanged.

**New flag:**
```
--emit-jobs PATH   Write job manifest to PATH (e.g. jobs.json) and exit.
                   Each entry is one (model × problem × solver × run) cell.
```

**Output format** — one JSON object per cell:
```json
[
  {
    "mid":     "m002",
    "label":   "gemma3",
    "adapter": "ollama:gemma3",
    "provider":"ollama",
    "pid":     "p007",
    "tier":    "T3",
    "problem": "integrate the square root of (4 minus x squared)",
    "solver":  "true",
    "run":     1,
    "script":  "cookbook/67_symbolic_math/sympy_llm.spl"
  },
  ...
]
```

No other changes to `run_experiment.py`.

---

### 2. New `run_cell.py` — single-cell runner

Extracted from the existing `stream_run` + RESULT-tag logic inside
`run_experiment.py`. Runs exactly one cell and appends one
`<!-- RESULT ... -->` tag to a shared log file.

**Interface:**
```
python cookbook/67_symbolic_math/run_cell.py \
    --job     '{"mid":"m002","pid":"p007","solver":"true",...}'  \
    --log     cookbook/67_symbolic_math/logs-spl/run-<timestamp>.md \
    --log-dir cookbook/67_symbolic_math/logs-spl
```

Or via a job-file index:
```
python cookbook/67_symbolic_math/run_cell.py --jobs jobs.json --index 42 --log ...
```

**Responsibilities:**
- Build the `spl3` command from the job dict (identical to `run_experiment.py`)
- Stream stdout+stderr to console and log
- Parse `Status:`, `Output:`, `LLM calls:`, `Log:` lines (same `stream_run` logic)
- Append the `<!-- RESULT ... -->` tag to the shared log using a **file lock**
  (e.g. `fcntl.flock` on Linux) so concurrent workers don't interleave writes
- Exit 0 on success, non-zero on cell failure (so the grid can retry if needed)

**What it does NOT do:**
- Write log headers or section separators (the grid orchestrator writes those once)
- Analyse results (that stays in `run_analysis.py`)

---

### 3. Momagrid dispatch configuration

Two concepts the Momagrid config needs to express:

**a) Model-affinity grouping**

All cells with the same `mid` must run on the same worker. This is the only
hard constraint. Example grouping for 10 workers:

| Worker | Models assigned |
|--------|----------------|
| w01    | m001 (Claude — API, no GPU limit) |
| w02    | m002 (gemma3) |
| w03    | m003 (gemma4:12b) |
| …      | … |
| w10    | m010 (rnj-1) |

**b) Optional Claude fan-out**

Because `m001` uses the Claude API rather than a local GPU, its 40 cells can
each run in parallel on separate workers. If Momagrid supports a secondary
level of parallelism, `m001` cells can be dispatched as 40 independent jobs
with no affinity constraint.

---

### 4. `run_analysis.py` — no changes

The analysis script already reads any log file that contains
`<!-- RESULT ... -->` tags. The aggregated log produced by parallel
file-locked appends is structurally identical to the sequential log.

The only operational difference: cells in the log will appear in completion
order (non-deterministic across workers) rather than the canonical model →
problem → solver order. `run_analysis.py` groups by `mid`/`pid`/`solver` via
pandas, so order does not matter.

---

## Expected Speedup

| Mode           | Wall-clock estimate |
|----------------|---------------------|
| Sequential today | 4–8 hours          |
| Momagrid (10 model workers) | ~50–80 min (slowest single model) |
| Momagrid + Claude fan-out   | ~50–80 min (Claude finishes in ~10 min; Ollama is the bottleneck) |

---

## File Summary

| File | Status | Change |
|------|--------|--------|
| `run_experiment.py` | Modify | Add `--emit-jobs PATH` flag |
| `run_cell.py`       | New    | Single-cell runner with file-locked log append |
| `run_analysis.py`   | Unchanged | Already works on any conforming log |
| `sympy_llm.spl`     | Unchanged | Same SPL script, same `spl3` invocation |
| Momagrid config     | New    | Model-affinity grouping, optional Claude fan-out |

---

## Open Questions for Review

1. **Log header**: Should `run_cell.py` write a per-cell markdown header
   (the `## label — solver — run N` block), or should the grid orchestrator
   write it? Today `run_experiment.py` writes it before launching the cell.

2. **Retry policy**: If a cell fails (non-zero exit), should Momagrid retry
   once automatically, or surface it as a failure for manual re-run?

3. **Claude fan-out**: Is the secondary parallelism for `m001` worth the added
   config complexity, given it's already the fastest model?

4. **Shared log vs per-cell logs**: Alternative — each `run_cell.py` writes its
   own small log, and a final merge step concatenates them. Avoids file locking
   entirely. Tradeoff: merge step needed before `run_analysis.py` can run.
