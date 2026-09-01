# Recipe 114 — Constrained Nonlinear Optimization (scipy.optimize)

Given a nonlinear profit function (pricing or logistics), find the profit-maximizing
decision using `scipy.optimize` — and verify the result by independent back-substitution.

**DODA**: same `.spl` spec runs on any adapter; only `--param method=` changes the scipy solver.

## What it demonstrates

| Axis | solver=ON | solver=OFF |
|---|---|---|
| Engine | scipy.optimize (SLSQP / Nelder-Mead / differential_evolution) | LLM heuristic estimate |
| Guarantee | Locally/globally optimal (method-dependent) | Plausible estimate, unverified |
| Verification | `ASSERT is_optimal` + back-substitution | Back-substitution only |
| Solver class | C4 (Constrained nonlinear) | — |

## Default problems

### Pricing (power demand curve)
```
Demand:     D(p) = 10000 * p^(-1.5)
Unit cost:  $5    Fixed cost: $50/period
Price range: [$6, $150]
Analytical optimum: p* = $15, profit* ≈ $5,218
```

### Logistics (quadratic revenue / congestion cost)
```
Revenue:    20x - 0.02x²
Cost:       200 + 8x + 0.05x²
Volume range: [6, 150] units
Analytical optimum: x* ≈ 85.7, profit* ≈ $257
```

## Run commands

```bash
# Pricing — SLSQP (gradient-based, default)
spl3 run cookbook/114_scipy_nonlinear/scipy_nonlinear.spl \
  --adapter claude_cli \
  --param problem_type=pricing \
  --param method=SLSQP

# Pricing — differential_evolution (global search, no gradient needed)
spl3 run cookbook/114_scipy_nonlinear/scipy_nonlinear.spl \
  --adapter claude_cli \
  --param problem_type=pricing \
  --param method=differential_evolution

# Logistics — Nelder-Mead (derivative-free)
spl3 run cookbook/114_scipy_nonlinear/scipy_nonlinear.spl \
  --adapter claude_cli \
  --param problem_type=logistics \
  --param method=Nelder-Mead

# solver=OFF ablation — LLM estimates without scipy
spl3 run cookbook/114_scipy_nonlinear/scipy_nonlinear.spl \
  --adapter ollama -m gemma3 \
  --param problem_type=pricing \
  --param use_solver=false

# Custom pricing problem (higher elasticity)
spl3 run cookbook/114_scipy_nonlinear/scipy_nonlinear.spl \
  --adapter claude_cli \
  --param problem_type=pricing \
  --param demand_scale=50000 \
  --param elasticity=2.0 \
  --param unit_cost=10 \
  --param x_min=5 --param x_max=200
```

## Parameters

| Parameter | Default | Description |
|---|---|---|
| `problem_type` | `pricing` | `pricing` or `logistics` |
| `method` | `SLSQP` | `SLSQP`, `Nelder-Mead`, `differential_evolution` |
| `max_iterations` | `1000` | Solver iteration budget (100–10000) |
| `use_solver` | `true` | `false` → LLM heuristic only (ablation) |
| `demand_scale` | `10000` | Pricing: D(p) scale coefficient |
| `elasticity` | `1.5` | Pricing: price elasticity exponent |
| `revenue_scale` | `20` | Logistics: linear revenue coefficient |
| `saturation` | `0.02` | Logistics: quadratic revenue penalty |
| `congestion` | `0.05` | Logistics: quadratic cost penalty |
| `unit_cost` | `8` | Variable cost per unit |
| `fixed_cost` | `200` | Fixed cost per period |
| `x_min` / `x_max` | `6` / `150` | Decision variable bounds |
| `min_demand` | `0` | Minimum demand constraint (0 = none) |

## TOOL_API reference

| Function | Purpose |
|---|---|
| `solve_nonlinear(problem_json, method, max_iterations)` | scipy constrained nonlinear solve |
| `verify_solution(problem_json, solution_json)` | Back-substitution: recomputes objective at x_opt |
| `is_optimal(solution_json)` | Returns True when scipy reports success and finite objective |

## Optimization formulations

**Pricing:**
```
Maximize    (p - c) * S * p^(-ε) - F
Subject to  p ∈ [x_min, x_max]
            S * p^(-ε) ≥ min_demand   (optional)
```

**Logistics:**
```
Maximize    (r * x - α * x²) - (F + c * x + β * x²)
Subject to  x ∈ [x_min, x_max]
            x ≥ min_demand            (optional)
```

## Verification gate

`ASSERT is_optimal(@solution_json)` halts the workflow if scipy did not converge.
`verify_solution` then recomputes the objective independently and reports `PASS` / `FAIL` / `SKIP`.

The ASSERT + back-substitution pattern appears in all solver recipes (r78, r98, r99) —
see solver-research-plan.md §2 for the 4-pillar framework.

## Related recipes

- Recipe 78: LP / MILP via PuLP (linear & integer programs)
- Recipe 98: Job-shop scheduling via OR-Tools CP-SAT (constraint programming)
- Recipe 99: Portfolio optimization via cvxpy (convex QP)
- Recipe 109: Synthetic problem catalog (n05 / n10 / n20 scale testing)
