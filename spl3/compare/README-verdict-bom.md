# `spl3 compare` — deterministic verdict + BOM/manifest batch mode

Two additive enhancements (2026-08-02). Both are backward-compatible: no existing
flag, output field, or default behavior was removed.

## 1. Stable, deterministic top-level `verdict`

**Problem.** The verdict (`EQUIVALENT | REFACTORED | DEGRADED | DIVERGED`) only existed
inside `synthesis`, which is populated by the LLM synthesis pass. With `--no-synthesize`,
code files (`git-diff` tier) produced *no* verdict at all, so downstream tools had to
regex the diff to guess.

**Change.**
- New module `spl3/compare/verdict.py`:
  - `deterministic_verdict(res)` — derives a verdict with **no LLM**, from whichever tiers
    ran, in priority order: character identity → GED (topology) → structural skeleton →
    AST symbols → embedding/ROUGE bands. E.g. *same structural skeleton, different text →
    `REFACTORED`*; *symbols added/removed → `DIVERGED`*.
  - `verdict_of(res)` — prefers an existing LLM synthesis verdict, else falls back to the
    deterministic one.
- `engine._rule_based_synthesis` now delegates to `deterministic_verdict` (was GED-only).
- `report.py` `--format json` now always includes top-level **`verdict`** and
  **`verdict_basis`** (which tier decided it), alongside the existing `synthesis`.

**Effect.** `spl3 compare a.py b.py --mode git-diff,structural --no-synthesize --format json`
now returns a labeled verdict deterministically. `--synthesize` still overrides with the
richer LLM verdict.

## 2. `spl3 compare-bom` — manifest batch comparison

Compare two directory trees anchored on a **Bill of Materials** (manifest): run the
multi-tier compare per listed item and roll the per-item verdicts up to one verdict
(worst-case across items). The reusable batch tier above single-file `compare` — usable for
GDW component graphs, ConceptBook domains, or any two builds of the same manifest.

```bash
spl3 compare-bom bom.yaml --ref apps/Claude/todo --cand apps/SPL/todo \
    --mode git-diff,structural,ast-diff --no-synthesize
```

Manifest (YAML or JSON):

```yaml
name: todo backend
items:
  - {name: todo_schema, file: app/schemas.py}   # resolved under --ref and --cand
  - {name: api_routes,  file: app/main.py}
  # or an explicit pair, ignoring --ref/--cand:
  - {name: x, file1: a/x.py, file2: b/x.py}
```

New module `spl3/compare/manifest.py` (`load_manifest`, `run_manifest`, `render_manifest`);
CLI command `cmd_compare_bom` in `cli.py`. Deterministic by default (`--no-synthesize`);
`--synthesize` runs per-item LLM synthesis.

## Verification (2026-08-02)
- `pytest tests/ -k "compar or verdict or synth"` → 11 passed, no regressions.
- Single compare (Claude vs SPL `schemas.py`) → `verdict: REFACTORED (basis: structural)`.
- `compare-bom` on the todo backend → 4×REFACTORED + 1×DEGRADED (`api_routes`) → roll-up
  DEGRADED — correctly *localizes* the one structurally-divergent node.

## Rationale
Motivated by GDW variant comparison (`graph-driven-workflow/scripts/compare_variants.py`),
where graph.yaml is treated as a BOM and two builds are compared part-by-part. The verdict
schema removed that tool's fragile regex parsing; the manifest mode is the general form of
its per-node loop, pushed down into SPL so ConceptBook can reuse it.
