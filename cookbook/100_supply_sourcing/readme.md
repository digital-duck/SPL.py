# Recipe 100 — Supply Sourcing (Multi-objective: cost vs. fill rate)

Given a set of suppliers with different cost, fill rate, and capacity profiles,
find allocations that trade off total cost against blended fill rate — using the
PuLP ε-constraint method to trace the full Pareto front.

**Benchmark B1** from the multi-objective benchmark suite.
**DODA**: same `.spl` spec runs on any adapter (ollama for exploration, claude_cli for production).

## What it demonstrates

| Axis | solver=ON | solver=OFF |
|---|---|---|
| Engine | PuLP ε-constraint sweep | LLM heuristic allocation |
| Guarantee | Provably Pareto-optimal front | Single plausible point, may violate constraints |
| Verification | `ASSERT` on front feasibility | `verify_sourcing_off` back-substitution |
| Solver class | C2 (LP, multi-objective) | — |

## Default problem (B1)

```
Demand: 1000 units

Supplier  Cost/unit  Fill rate  Capacity
S1        $10        95%        400 units   (premium)
S2        $ 7        80%        500 units   (standard)
S3        $ 5        60%        400 units   (budget)

Objectives: minimize total cost AND maximize blended fill rate
```

Known anchor points:
- Min-cost: x1=100, x2=500, x3=400 → cost=$6,500, fill=73.5%
- Max-fill: x1=400, x2=500, x3=100 → cost=$8,000, fill=84.0%

## Run commands

```bash
# solver=ON — PuLP ε-constraint sweep (default 8 Pareto points)
spl3 run cookbook/100_supply_sourcing/supply_sourcing.spl \
  --adapter claude_cli \
  --param use_solver=true

# solver=ON — custom n_points
spl3 run cookbook/100_supply_sourcing/supply_sourcing.spl \
  --adapter claude_cli \
  --param use_solver=true \
  --param n_points=12

# solver=OFF — LLM heuristic allocation with back-substitution check
spl3 run cookbook/100_supply_sourcing/supply_sourcing.spl \
  --adapter ollama -m gemma3 \
  --param use_solver=false

# Custom problem
spl3 run cookbook/100_supply_sourcing/supply_sourcing.spl \
  --adapter claude_cli \
  --param use_solver=true \
  --param "problem=A factory needs 2000 units. SupA: $12/unit, 98% fill rate, capacity 800. SupB: $8/unit, 75% fill rate, capacity 1200. SupC: $6/unit, 55% fill rate, capacity 900."
```

## TOOL_API reference

| Function | Purpose |
|---|---|
| `sweep_pareto_front(problem_json, n_points)` | PuLP ε-constraint sweep → Pareto front JSON |
| `is_pareto_feasible(front_json)` | ASSERT gate: status==OK and n_points >= 2 |
| `format_pareto_table(front_json)` | Pareto front → markdown table |
| `verify_sourcing_off(problem_json, solution_json)` | Arithmetic back-check for solver=OFF path |
| `json_get_field(data_json, field)` | Extract a field from JSON as string |

## Optimization formulation

```
For each fill-rate threshold ε_k ∈ [ε_min, ε_max]:

  Minimize    sum_i  cost_i * x_i
  Subject to  sum_i  x_i  = demand
              sum_i  fill_i * x_i  >=  ε_k * demand
              0  <=  x_i  <=  capacity_i   for each supplier i

Dominated points are removed; the result is the Pareto front.
```

## Verification (solver=OFF)

`verify_sourcing_off` checks:
1. **Demand balance**: sum(allocation) == demand (tolerance ±1 unit)
2. **Capacity**: each allocation <= supplier capacity
3. **Cost**: recompute from allocation; compare to claimed (tolerance ±$10)
4. **Fill rate**: recompute blended fill; compare to claimed (tolerance ±2 pp)

## Output metadata

The `RETURN` statement surfaces:
- `objective = @fill_rate_str` — number of Pareto points (solver=ON) or blended fill rate (solver=OFF)
- `verify = @verify_status` — PASS / FAIL / N/A

## Related recipes

- Recipe 78: LP / MILP via PuLP (single-objective constraint optimization)
- Recipe 99: Portfolio optimization via cvxpy (Markowitz mean-variance)
- Recipe 101: Multi-depot vehicle routing (coming soon)
