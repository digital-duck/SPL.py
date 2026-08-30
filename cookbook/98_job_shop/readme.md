# Recipe 98 — Job-Shop Scheduling (OR-Tools CP-SAT)

Classic job-shop scheduling: N jobs × M machines, each job has a fixed sequence of operations.  
OR-Tools CP-SAT finds the optimal schedule (minimum makespan) in milliseconds.

## What it demonstrates

| Axis | solver=ON | solver=OFF |
|---|---|---|
| Engine | OR-Tools CP-SAT (constraint programming) | LLM heuristic reasoning |
| Guarantee | Proven optimal or proven infeasible | Plausible schedule, may violate constraints |
| Verification | `ASSERT` on CP-SAT status | `verify_job_shop` back-substitution |
| Solver class | C5 (Constraint propagation / CP-SAT) | — |

## Default problem (n=3 jobs × 3 machines)

```
Job 1: M1(3) → M2(2) → M3(2)   (three operations in sequence)
Job 2: M2(2) → M1(3) → M3(1)
Job 3: M3(2) → M2(1) → M1(2)
Known optimal makespan: 8
```

## Run commands

```bash
# solver=ON, claude_cli
spl3 run cookbook/98_job_shop/job_shop.spl \
  --adapter claude_cli \
  --param use_solver=ON \
  --param problem="3 jobs, 3 machines. Job1: M1(3)→M2(2)→M3(2). Job2: M2(2)→M1(3)→M3(1). Job3: M3(2)→M2(1)→M1(2). Minimize makespan." \
  --param capital=0 --param tickers="" --param period=1y

# solver=OFF, ollama/gemma3
spl3 run cookbook/98_job_shop/job_shop.spl \
  --adapter ollama -m gemma3 \
  --param use_solver=OFF \
  --param problem="3 jobs, 3 machines. Job1: M1(3)→M2(2)→M3(2). Job2: M2(2)→M1(3)→M3(1). Job3: M3(2)→M2(1)→M1(2). Minimize makespan."
```

## TOOL_API reference

| Function | Purpose |
|---|---|
| `parse_job_shop_problem(problem)` | Normalise LLM-extracted JSON |
| `solve_job_shop(problem_json)` | OR-Tools CP-SAT → `{status, makespan, schedule}` |
| `verify_job_shop(problem_json, solution_json)` | Back-substitute: check no-overlap + precedence |
| `format_gantt(solution_json)` | ASCII Gantt chart |

## Verification (solver=OFF)

`verify_job_shop` checks:
1. **No-overlap**: no two jobs assigned to the same machine at the same time
2. **Precedence**: each job's operations run in the specified order
3. **Makespan consistency**: claimed makespan matches max end-time in schedule

## Scale sensitivity

| n | Difficulty | Comment |
|---|---|---|
| 3×3 | Easy | LLM can enumerate feasible schedules |
| 5×5 | Medium | dispatching heuristics degrade |
| 10×10 | Hard | near-optimal solutions require branch-and-bound |

## Related recipes

- Recipe 78: LP / MILP via PuLP (recipe 78a–d ablation study)
- Recipe 99: Portfolio optimization via cvxpy (convex QP)
