# Solver Recipe Cleanup & Normalization

**Status:** in progress · **Started:** 2026-09-06 · **Owner:** Wen + Claude

Isolated workspace for deep-refactoring the solver recipes without touching the
validated originals in `cookbook/`. Once refactoring is complete here, a single
unattended batch job validates all recipes at once, then results are promoted
back to `cookbook/`.

> **Do not edit `cookbook/` during this effort.** All work happens in
> `cookbook-solver/`. Originals remain the regression baseline.

---

## Why

Solver compute — the deterministic/probabilistic boundary where an `.spl`
workflow hands a formalized problem to a real optimizer (PuLP, OR-Tools, pymoo,
Z3, Pyomo, scipy, statsmodels) and gates on a proven result — is shaping up to
be a **unique, differentiating feature of SPL**. It deserves first-class,
low-redundancy, easy-to-maintain code. Today the recipes carry a large amount
of copy-paste boilerplate that makes them costly to maintain and error-prone
(e.g. the recurring `_strip_fences` / `json.loads` PARSE_ERROR bugs, the
`--llm` vs `--adapter` drift).

---

## Findings (redundancy audit)

Across the first 13 recipes in scope:

| Redundancy | Count | Notes |
|---|---|---|
| `CREATE TOOL_API` wrapper blocks | **90** | ~6–10 lines of *identical* boilerplate each |
| — of those, pure pass-through | **83** | just `from tools import X as _fn; return _fn(...)` |
| — of those, doing real coercion | **7** | `int()` / `float()` / extra-arg — in r99, r100, r101, r107, r114 |
| Local `json_get_field` duplicating stdlib `json_get` | **9 recipes** | r98, r99, r102, r107, r108, r109, r113, r117, r118 |
| Local `_strip_fences` redefined in tools.py | most | ~5–8 lines duplicated per recipe |

**Root cause of the wrapper boilerplate:** recipe `tools.py` functions are
**not** decorated with `@spl_tool`, so SPL's auto-loader (which registers only
`@spl_tool` functions — confirmed: the "Auto-loaded 89 tool(s)" line is exactly
the 89 stdlib tools) never sees them. The `CREATE TOOL_API` blocks are the
*only* thing making recipe functions callable. They are load-bearing today, but
entirely eliminable by decorating the functions instead.

---

## Target convention (normalized)

### tools.py

```python
from spl.tools import spl_tool
from spl.stdlib import strip_fences   # promoted stdlib helper (see below)

@spl_tool
def solve_x(problem_json: str, n_points: str = "8") -> str:
    n = int(n_points)                 # SPL passes all CALL args as strings —
    data = json.loads(strip_fences(problem_json))   # coerce inside the function
    ...
```

- Decorate every SPL-called function with `@spl_tool` (registers under its name).
- `_`-prefixed helpers stay undecorated (internal only).
- Move all `int()` / `float()` coercion **inside** the function (args arrive as
  strings). This retires the 7 coercion wrappers.

### .spl

- **Delete all `CREATE TOOL_API` wrapper blocks** — auto-load now registers the
  decorated functions directly by name.
- Keep `CREATE FUNCTION` prompt templates and `WORKFLOW`.
- Replace local `json_get_field` → stdlib **`json_get`**.
- Replace ad-hoc boolean coercions (`solver_enabled`, `is_empty_policy`) →
  stdlib **`normalize_bool`** where semantics match.
- Standardize on `--adapter` (not the deprecated `--llm`) in header comments.

**Net effect:** each `.spl` shrinks by ~40–60% (prompts + workflow only); each
`tools.py` loses its `_strip_fences` copy and gains one decorator line per tool.

---

## stdlib promotion candidates

Promote genuinely shared helpers into the runtime so recipes import rather than
redefine. `solver compute` being a headline feature justifies a small, curated
solver stdlib surface.

| Helper | Today | Proposed | Rationale |
|---|---|---|---|
| `strip_fences(text)` | redefined in ~every tools.py | ✅ landed in `spl/stdlib.py` — Python-importable **and** `@spl_tool` (SPL-callable) | Ubiquitous; source of recurring PARSE_ERROR bugs |
| `json_get(json, field)` | already stdlib | adopt everywhere | Retires 9× `json_get_field` |
| `normalize_bool(x)` | already stdlib | adopt everywhere | Retires `solver_enabled` / `is_empty_policy` variants |
| `status_ok(json, field?, expected?)` | 8 bespoke predicates (`is_optimal`, `is_scheduled`, `is_pareto_feasible`, `sp_optimal`, `is_satisfiable`, …) | *evaluate* a generic status-gate builtin | Many are just `data["status"] in {OK, optimal}`; some carry extra conditions (n_points≥2, beats_naive) — keep those bespoke |

Report formatters (`format_report_solver_on/off`) stay recipe-local — too
domain-specific to generalize usefully.

---

## Process

1. **Plan** — this document. ✅
2. **POC one recipe** (r113). ✅ both arms green.
3. **Review POC** with Wen; lock the convention. ← *pending sign-off*
4. **Apply broadly** to the in-scope recipes. ✅ all 13 T1 done.
5. **stdlib promotion** — `strip_fences` landed. ✅ (`status_ok` still proposed.)
6. **Batch validate** — unattended run over all `cookbook-solver/` recipes. ← next
7. **Promote back** to `cookbook/` after green batch.

---

## Scope — full solver recipe inventory (39 recipes)

Source of truth: `dd-research/docs/research/solver/SPL-solver-recipes.md`
(reverse index). Every built solver recipe is tracked here so each is checked
off during the regression batch.

- **Refac** — refactored to the normalized convention (`@spl_tool`, no wrappers,
  stdlib helpers). `—` = audit pending (may already be clean / no wrappers).
- **Batch** — passed the unattended regression run in `cookbook-solver/`.
- **T1** — the 13 initially listed (confirmed to carry the wrapper redundancy).
- **OrigValid** — was the *original* recipe validated (from the index Valid
  column)? Blank ones were never validated even as originals — flag for a
  first-time validation pass, separate from the refactor.

| Recipe | Folder | Solver | T1 | OrigValid | Refac | Batch |
|:---:|---|---|:---:|:---:|:---:|:---:|
| r67  | 67_symbolic_math              | SymPy (S010)               |   | ✓ | — | ☐ |
| r75  | 75_sage_math                  | SageMath (S011)            |   | ✓ | — | ☐ |
| r76  | 76_lean_proof                 | Lean 4 (no Sxxx)           |   |   | — | ☐ |
| r77  | 77_neurosymbolic              | SymPy+SageMath (S010,S011) |   | ✓ | — | ☐ |
| r78  | 78_constraint_opt             | PuLP+CBC (S001)            |   | ✓ | — | ☐ |
| r79  | 79_code_pytest                | pytest (S008)              |   | ✓ | — | ☐ |
| r81  | 81_graph_reasoning            | networkx (S004)            |   | ✓ | — | ☐ |
| r82  | 82_logic_puzzle_solver        | python-constraint (S003)   |   | ✓ | — | ☐ |
| r83  | 83_unit_dimensional_check     | pint (S005)                |   | ✓ | — | ☐ |
| r84  | 84_sql_verifier               | sqlite3 (S006)             |   | ✓ | — | ☐ |
| r85  | 85_property_based_code_verify | Hypothesis/pytest (S008)   |   | ✓ | — | ☐ |
| r86  | 86_financial_calc_verifier    | decimal (S007)             |   | ✓ | — | ☐ |
| r87  | 87_route_optimization         | OR-Tools routing (S002)    |   | ✓ | — | ☐ |
| r90  | 90_compsci_physics            | NumPy (S009)               |   | ✓ | — | ☐ |
| r92  | 92_compsci_materials          | NumPy (S009)               |   | ✓ | — | ☐ |
| r93  | 93_auto_planning              | mini-VAL STRIPS (no Sxxx)  |   | ✓ | — | ☐ |
| r94  | 94_data_eng_text2spl          | sqlite3 (S006)             |   | ✓ | — | ☐ |
| r98  | 98_job_shop                   | OR-Tools CP-SAT (S012)     | ✓ | ✓ | ✅ | ☐ |
| r99  | 99_portfolio_opt              | cvxpy (S013)               | ✓ | ✓ | ✅ | ☐ |
| r100 | 100_supply_sourcing           | PuLP+CBC (S001)            | ✓ | ✓ | ✅ | ☐ |
| r101 | 101_production_sustainability | PuLP+CBC (S001)            | ✓ | ✓ | ✅ | ☐ |
| r102 | 102_z3_compliance             | Z3 (S014)                  | ✓ | ✓ | ✅ | ☐ |
| r103 | 103_data_quality              | Great Expectations (S015)  |   |   | — | ☐ |
| r104 | 104_pandera_schema            | pandera (S016)             |   |   | — | ☐ |
| r105 | 105_prolog_inference          | SWI-Prolog (S017)          |   |   | — | ☐ |
| r106 | 106_shapely_geo               | Shapely (S018)             |   |   | — | ☐ |
| r107 | 107_workforce_3obj            | pymoo NSGA-II (S019)       | ✓ | ✓ | ✅ | ☐ |
| r108 | 108_robust_milp               | python-mip (S022)          | ✓ | ✓ | ✅ | ☐ |
| r109 | 109_synthetic_problems        | PuLP+CBC (S001)            | ✓ | ✓ | ✅ | ☐ |
| r110 | 110_nash_game_theory          | nashpy (S023)              |   |   | — | ☐ |
| r111 | 111_stackelberg_game          | pure-Python (no Sxxx)      |   |   | — | ☐ |
| r112 | 112_optuna_blackbox           | optuna (S026)              |   |   | — | ☐ |
| r113 | 113_bayesian_opt              | scikit-optimize (S027)     | ✓ | ✓ | ✅ | ☐ |
| r114 | 114_scipy_nonlinear           | scipy.optimize (S028)      | ✓ | ✓ | ✅ | ☐ |
| r115 | 115_gambit_3player            | pygambit (S024)            |   |   | — | ☐ |
| r116 | 116_openspiel_cfr             | OpenSpiel CFR (S025)       |   |   | — | ☐ |
| r117 | 117_pyomo_stochastic          | Pyomo+GLPK (S021)          | ✓ | ✓ | ✅ | ☐ |
| r118 | 118_trading_rule_z3           | Z3 (S014)                  | ✓ | ✓ | ✅ | ☐ |
| r119 | 119_demand_forecast           | statsmodels (S029)         | ✓ | ✓ | ✅ | ☐ |

**Order of attack:** T1 first (13, confirmed redundant) → then audit + refactor
the remaining 26. Recipes with blank **OrigValid** (r76, r103, r104, r105, r106,
r110, r111, r112, r115, r116) need a first-time validation on their originals
too — track that alongside the refactor so the batch run isn't the first time
they're exercised.

---

## Testing strategy

- `spl3 validate` per `.spl` — cheap structural/semantic check (catches
  unresolved CALL targets, parse errors) with no LLM cost.
- Per-recipe smoke run `--adapter claude_cli --param use_solver=true|false`.
- **Batch harness (ready):** `cookbook-solver/run_all.py` +
  `cookbook-solver/cookbook_catalog.json` (39 recipes; 13 T1 `is_active`+
  `approval_status:"ready"` 🧪, other 26 `new`/inactive). Defaults to
  `--adapter claude_cli`. Run from repo root:

  ```bash
  python cookbook-solver/run_all.py --catalog        # inspect (add --all for 39)
  python cookbook-solver/run_all.py                  # run the 13 ready recipes
  python cookbook-solver/run_all.py --workers 4      # parallel
  python cookbook-solver/run_all.py 2>&1 | tee cookbook-solver/run_$(date +%Y%m%d_%H%M%S).md
  ```

  Per-recipe logs land in `cookbook-solver/<dir>/logs/`. Verified end-to-end on
  r100 (SUCCESS, 35.5s). All 13 recipes' solver deps + `glpsol` confirmed
  installed. Note: `--check` only validates `env:`/`ollama:` requires, not pip
  solver packages — the run itself surfaces any missing dep as a recipe failure.
  As each of the 26 is refactored, copy it into `cookbook-solver/`, flip its
  catalog entry to `is_active:true` / `approval_status:"ready"`, and re-batch.

---

## POC result (r113, 2026-09-06)

Refactored r113: `.spl` 156 → 100 lines (5 `CREATE TOOL_API` blocks removed);
tools.py gained 4 `@spl_tool` decorators, lost its `json_get_field`.

- `spl3 validate` → OK (with expected warnings: static validator does not
  auto-load tools.py, so it cannot see `@spl_tool` registrations and warns on
  the CALL targets — harmless; runtime resolves them).
- `--adapter claude_cli --param use_solver=true` → **ran clean**; ASSERT gate on
  `bayesian_improved` fired; report generated (2 LLM calls).
- `--adapter claude_cli --param use_solver=false` → **ran clean** (3 LLM calls).
- **`Auto-loaded 93 tool(s)`** = 89 stdlib + exactly 4 decorated recipe
  functions → decoration/auto-load mechanism confirmed precisely.

**Convention proven. Ready to apply broadly.**

---

## Progress checklist

- [x] Plan documented
- [x] Full 39-recipe inventory added (see Scope table — per-recipe check-off)
- [x] POC: r113 refactored + validated + run (both arms green)
- [x] `strip_fences` promoted to stdlib (`spl/stdlib.py`, `@spl_tool` + importable)
- [x] **All 13 T1 recipes refactored** (see results below)
- [ ] Convention locked with Wen
- [ ] Remaining 26 audited + refactored
- [ ] Batch validation green (all 39)
- [ ] Promoted back to `cookbook/`

---

## Refactor results — T1 (2026-09-06)

All 13 T1 recipes refactored to the normalized convention and structurally
validated. `strip_fences` landed in `spl/stdlib.py` (not a separate `spl/solver.py`
— reused the existing stdlib surface; importable as
`from spl.stdlib import strip_fences`, callable as `CALL strip_fences(@x)`).

**Reduction:** `.spl` total **3,592 → 2,607 lines (−985, −27%)**; 90 `CREATE
TOOL_API` wrapper blocks removed; 9× `json_get_field` and 4× `_strip_fences`
retired in favor of stdlib.

**Verification:**
- `spl3 validate` → OK on all 13 (only expected "CALL target not found"
  warnings — static validator can't see `@spl_tool` registrations).
- Python import of every transformed `tools.py` → clean; tool counts confirm
  decoration (e.g. `Auto-loaded 96–97 tool(s)` = 89 stdlib + recipe fns).
- Runtime smoke runs (`--adapter claude_cli`), covering each risk area:
  - r113 ON+OFF · r100 ON (int coercion + stdlib strip_fences + PuLP)
  - r117 ON (solver_enabled + multi-workflow + glpk) · r102 ON (is_empty_policy + z3)
  - r101 OFF (verify_off + strip_fences) — all `status=complete`.
- r108 OFF not smoke-run to completion (slow: naive + silent MILP + LLM compare)
  — left for the batch.

**Deferred (not blocking):** `solver_enabled` / `is_empty_policy` kept as
decorated recipe tools (no longer wrapper-duplicated). `is_empty_policy` is an
emptiness check, *not* `normalize_bool` semantics; `solver_enabled` → possible
future `normalize_bool` swap. `status_ok` generic gate — still just a proposal.
