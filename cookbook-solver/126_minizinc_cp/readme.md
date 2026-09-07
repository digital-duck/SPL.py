# Recipe 126 — MiniZinc CP: Backend-Agnostic Nurse Scheduling

**Solver class:** Constraint Programming (CP), backend-agnostic via MiniZinc  
**Backend:** MiniZinc → CP-SAT (via OR-Tools) or Gecode  
**Dependency:** `pip install minizinc` + MiniZinc binary from https://www.minizinc.org

## What it demonstrates

**"DODA for constraint programming."** MiniZinc separates the constraint *model* (`.mzn`)
from the *solver backend* (CP-SAT, Gecode, Choco, Gurobi CP) — the same model runs on
any backend by changing one parameter. This is the same invariance principle as SPL:

```
.spl file : LLM adapter  ≡  .mzn model : CP backend
```

Both are invariant specifications. The execution engine is swappable without modifying
the spec.

| | solver=ON (MiniZinc → CP-SAT) | solver=OFF (LLM heuristic) |
|---|---|---|
| Hard constraint satisfaction | **Proved** (CP propagation) | Approximate reasoning |
| Night→Morning violations | 0 (enforced) | 2 in 7 days (typical) |
| Coverage guarantees | Proved ≥ minimum per shift | Best-effort |
| Preference score | Maximized (soft obj) | Heuristic |

## The problem: 7-day nurse scheduling

**8 nurses** (N1, N2 are senior), **7 days**, **3 shifts** (Morning/Afternoon/Night) + Off.

| Constraint | Type | Rule |
|---|---|---|
| Morning coverage | Hard | ≥ 2 nurses, at least 1 senior (N1 or N2) |
| Afternoon coverage | Hard | ≥ 2 nurses |
| Night coverage | Hard | ≥ 1 nurse |
| Max work days | Hard | ≤ 5 days per week per nurse |
| Rest rule | Hard | No Night on day D and Morning on day D+1 |
| N3 prefers morning | Soft | +3 per morning shift |
| N7 avoids nights | Soft | −3 per night shift |
| N8 prefers days off | Soft | +2 per day off |

**Why LLM fails:** The night→morning rest rule interacts with the coverage requirement.
A nurse needed for morning on Monday (to meet coverage) might have worked night Sunday —
but the LLM doesn't track all constraint interactions simultaneously. It sees "need 2 on
Monday morning" and assigns N3 without checking N3's Sunday assignment.

## Run

```bash
# solver=ON: MiniZinc → CP-SAT (or Gecode) backend
spl3 run cookbook-solver/126_minizinc_cp/minizinc_cp.spl \
    --adapter claude_cli --param use_solver=true

# solver=OFF: LLM scheduling heuristic + constraint violation check
spl3 run cookbook-solver/126_minizinc_cp/minizinc_cp.spl \
    --adapter ollama -m gemma3 --param use_solver=false
```

## Install

```bash
pip install minizinc

# MiniZinc binary (required for all solvers):
# https://www.minizinc.org/software.html
# (includes CP-SAT via OR-Tools on most platforms)

# Gecode backend (optional, faster for some models):
# conda install -c conda-forge gecode
```

## The MiniZinc model (the invariant)

The `.mzn` model is embedded in `tools.py` and generated at runtime. Key structure:
```minizinc
array[1..n_nurses, 1..n_days] of var 0..3: sched;
% 0=Morning, 1=Afternoon, 2=Night, 3=Off

% Night→Morning rest (the constraint LLM misses)
constraint forall(n, d) (
    not (sched[n,d] == 2 /\ sched[n,d+1] == 0)
);

solve maximize pref_score;
```

The same model text runs on CP-SAT (Google OR-Tools) by passing `solver="com.google.ortools.sat"`
or on Gecode by passing `solver="org.gecode.gecode"` — zero model changes.

## Background: constraint propagation vs LP relaxation

**LP relaxation** (used by MILP solvers): relax binary/integer variables to continuous,
solve LP, branch on fractional solutions. Strong when constraints are nearly LP-feasible.

**Constraint propagation** (used by CP): for each constraint, reduce the domain of
variables based on what values are compatible. Forward-check: if assigning N3 to Morning
on Monday would make it impossible to satisfy the rest rule (because N3 worked Night on
Sunday), eliminate Monday Morning from N3's domain immediately.

CP is particularly strong for scheduling problems because:
- Hard constraints reduce domains rapidly (forward checking)
- Symmetry breaking and global constraints (e.g., `alldifferent`) prune large sub-trees
- No need for a continuous relaxation that may be far from the feasible region

## Key ASSERT

```
ASSERT schedule_hard_constraints_met(@result_json);
```

Passes when:
- `violations["night_morning"] == 0` (no rest rule violations)
- `violations["coverage_shortage"] == 0` (all shifts covered)

Preference score is not asserted — it is maximized as a soft objective.

## DODA stacked

This recipe demonstrates two levels of DODA simultaneously:
1. The `.spl` workflow is invariant across LLM adapters (claude_cli, ollama, openrouter)
2. The `.mzn` model is invariant across CP backends (CP-SAT, Gecode, Choco)

Both the LLM adapter and the CP backend are runtime parameters. The specs — the `.spl`
workflow and the `.mzn` constraint model — never change.
