# cookbook-solver/

Isolated workspace for the **normalized solver recipes** and their regression
batch. This folder mirrors solver recipes from `cookbook/` in a cleaner, lower-
redundancy form so they can be refactored and validated without disturbing the
originals (which stay the regression baseline).

- **What / why / the full refactor plan:** [`readme-cleanup.md`](./readme-cleanup.md)
- **Recipe → solver source of truth:** `dd-research/docs/research/solver/SPL-solver-recipes.md`

> Run everything from the repo root (`~/projects/digital-duck/SPL.py`) in the
> `spl123` conda env.

---

## What "solver compute" is

Each recipe demonstrates SPL's deterministic/probabilistic boundary: an `.spl`
workflow uses the **LLM** to read a natural-language problem and formalize it
(probabilistic), hands that to a **real optimizer** — PuLP, OR-Tools, pymoo, Z3,
Pyomo, scipy, statsmodels, … (deterministic) — `ASSERT`s on a proven result, then
has the LLM interpret it. Every recipe supports an ablation:

- `--param use_solver=true` — solver path (proven/optimal)
- `--param use_solver=false` — LLM-only baseline with a back-substitution check

This solver-gated pattern is a distinguishing feature of SPL, so these recipes
are held to a first-class, low-boilerplate standard.

---

## Normalized convention (what makes these different from `cookbook/`)

| Aspect | `cookbook/` (original) | `cookbook-solver/` (normalized) |
|---|---|---|
| Tool exposure | ~7–12 `CREATE TOOL_API` wrapper blocks per `.spl` (~6–10 lines each) | none — `tools.py` functions decorated with `@spl_tool`, auto-loaded by name |
| JSON field access | recipe-local `json_get_field` | stdlib **`json_get`** |
| Fence stripping | `_strip_fences` copy-pasted per `tools.py` | stdlib **`strip_fences`** (`from spl.stdlib import strip_fences`) |
| Arg coercion | `int()`/`float()` in the wrapper | inside the function (SPL passes args as strings) |

Net: the 13 refactored `.spl` files shrank **3,592 → 2,607 lines (−27%)** with
identical behavior.

**Adding a tool** — just decorate it; no `.spl` wrapper needed:

```python
# tools.py
from spl.tools import spl_tool
from spl.stdlib import strip_fences
import json

@spl_tool
def solve_x(problem_json: str, n_points: str = "8") -> str:
    n = int(n_points)                              # args arrive as strings
    data = json.loads(strip_fences(problem_json))  # LLM JSON is often fenced
    ...
```

```sql
-- workflow.spl — call it directly, and use stdlib helpers
CALL solve_x(@problem_json, @n_points) INTO @front_json;
CALL json_get(@front_json, "n_points") INTO @n;
```

Helpers prefixed with `_` stay undecorated (internal only). Report formatters
(`format_report_solver_on/off`) stay recipe-local.

---

## Running the regression batch

```bash
# Inspect the catalog
python cookbook-solver/run_all.py --catalog          # the 13 ready recipes
python cookbook-solver/run_all.py --catalog --all    # all 39 (13 ready + 26 new)
python cookbook-solver/run_all.py --check            # env/ollama prereqs (see note)

# Run
python cookbook-solver/run_all.py                    # 13 ready recipes, sequential
python cookbook-solver/run_all.py --workers 4        # parallel
python cookbook-solver/run_all.py --ids 100,107,117  # a subset
python cookbook-solver/run_all.py --all              # also run the 26 inactive

# Capture a run log
python cookbook-solver/run_all.py --workers 4 2>&1 \
  | tee cookbook-solver/run_$(date +%Y%m%d_%H%M%S).md
```

Defaults: `--adapter claude_cli`, `--model ""` (adapter default). Each recipe
runs `use_solver=true`. Per-recipe logs are written to
`cookbook-solver/<dir>/logs/<log>_<timestamp>.md`; the SPL runtime also writes
its own log under `~/.spl/logs/`.

A run finishes with a summary table:

```
=== Summary: N/13 Success  (total …s) ===
ID    Recipe                        Status   Elapsed
98    Job-Shop Scheduling …         OK          …s
...
```

---

## The catalog (`cookbook_catalog.json`)

Single source of truth for the batch. Each entry:

```jsonc
{
  "id": "100",
  "name": "Supply Sourcing — Multi-Objective Pareto (cost vs fill rate)",
  "description": "…",
  "args": ["spl3", "run", "cookbook-solver/100_supply_sourcing/supply_sourcing.spl",
           "--adapter", "claude_cli", "--param", "use_solver=true"],
  "dir": "100_supply_sourcing",
  "log": "supply_sourcing",
  "is_active": true,
  "approval_status": "ready",   // 🧪 queued for this regression batch
  "category": "reasoning",
  "tier": 2,
  "requires": ["pulp"],
  "excluded_adapters": []
}
```

Status markers: 🧪 `ready` · ✅ `active` · 🆕 `new` · 🔧 `wip` · ⏸ `disabled` · ❌ `rejected`.

- **13 T1** recipes: `is_active: true`, `approval_status: "ready"` — run by default.
- **26 remaining** solver recipes: `approval_status: "new"`, `is_active: false` —
  listed for tracking, skipped until refactored into this folder.

The `--check` step only validates `env:`/`ollama:`-prefixed `requires`; bare pip
package names (`pulp`, `pymoo`, …) are **not** verified there — a missing solver
dependency surfaces as a recipe failure in the run log instead. All 13 ready
recipes' deps (+ the `glpsol` binary for Pyomo) are confirmed installed.

---

## Recipes in this batch (13 ready)

| ID | Recipe | Solver | Requires |
|---|---|---|---|
| r98  | Job-Shop Scheduling | OR-Tools CP-SAT | `ortools` |
| r99  | Portfolio Optimization | cvxpy (Markowitz) | `cvxpy`, `yfinance` |
| r100 | Supply Sourcing (Pareto) | PuLP ε-constraint | `pulp` |
| r101 | Production Sustainability | PuLP scalarization | `pulp` |
| r102 | Z3 Compliance Checker | Z3 SMT | `z3-solver` |
| r107 | Workforce 3-Objective | pymoo NSGA-II | `pymoo`, `pulp` |
| r108 | Robust Supply Chain MILP | python-mip | `mip` |
| r109 | Synthetic Problem Generator | PuLP CBC | `pulp` |
| r113 | Bayesian Optimization | scikit-optimize (GP+EI) | `scikit-optimize` |
| r114 | Scipy Nonlinear | scipy.optimize (SLSQP) | `scipy` |
| r117 | Two-Stage Stochastic Prog. | Pyomo + GLPK | `pyomo`, `glpk` |
| r118 | Trading Rule Verifier | Z3 SMT | `z3-solver` |
| r119 | Demand Forecasting | statsmodels UC | `statsmodels` |

The other 26 solver recipes (r67–r94, r103–r106, r110–r112, r115–r116) are in the
inventory table in [`readme-cleanup.md`](./readme-cleanup.md).

---

## Recipe layout

```
cookbook-solver/<id>_<name>/
├── <name>.spl        # workflow + CREATE FUNCTION prompt templates (no tool wrappers)
├── tools.py          # @spl_tool-decorated Python solver functions
├── readme.md         # per-recipe writeup (kept from the original)
└── logs/             # batch run outputs
```

---

## Adding / activating another recipe

1. Copy the recipe folder from `cookbook/` into `cookbook-solver/`.
2. Refactor to the convention above (decorate `tools.py`, drop `CREATE TOOL_API`
   wrappers, adopt stdlib `json_get` / `strip_fences` / `normalize_bool`).
3. `spl3 validate cookbook-solver/<dir>/<name>.spl` (static warnings about CALL
   targets are expected — the validator can't see `@spl_tool` registrations).
4. Smoke run both arms: `--param use_solver=true` and `use_solver=false`.
5. In `cookbook_catalog.json`, flip the entry to `is_active: true`,
   `approval_status: "ready"`.
6. Re-run the batch.

Once the whole batch is green, the normalized recipes are promoted back to
`cookbook/`.
