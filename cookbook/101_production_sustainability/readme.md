# Recipe 101 — Production Sustainability (Multi-objective: profit vs. carbon)

Given a factory producing two products with different profitability and emissions profiles,
find the set of non-dominated production plans that simultaneously maximize profit and minimize
carbon footprint — the Pareto front.

**Benchmark B3** from the multi-objective optimization suite.  
**DODA**: the same `.spl` spec runs on any adapter; only the solver flag changes behavior.

## What it demonstrates

| Axis | solver=ON | solver=OFF |
|---|---|---|
| Engine | PuLP weighted-sum scalarization (CBC) | LLM heuristic (x, y) selection |
| Guarantee | Correct Pareto front via LP at each λ | Plausible plan, may not be Pareto-optimal |
| Verification | `ASSERT is_pareto_feasible` (≥2 points) | `verify_production_off` back-substitution |
| Solver class | C2 (Multi-objective LP / scalarization) | — |
| LLM role | Interpret tradeoff, recommend operating points | Propose plan + reasoning |

## Default problem (B3)

Two products, two objectives, two resource constraints:

| Product | Profit ($/unit) | Carbon (kg/unit) | Labor (hr/unit) | Material (kg/unit) |
|---|---|---|---|---|
| A (standard) | $10 | 3.0 kg | 2 hr | 3 kg |
| B (green)    |  $6 | 1.0 kg | 1 hr | 2 kg |

Available resources: **20 labor-hours**, **30 kg material**

Known anchor points:

- **Max-profit only**: x=10, y=0 → profit=$100, carbon=30 kg
- **Min-carbon only**: x=0,  y=15 → profit=$90,  carbon=15 kg

The tension: Product A is more profitable but dirtier; Product B is greener but less profitable.

## Run commands

```bash
# solver=ON — PuLP Pareto sweep, claude_cli
spl3 run cookbook/101_production_sustainability/production_sustainability.spl \
  --adapter claude_cli \
  --param use_solver=true \
  --param n_points=10

# solver=ON — finer sweep (20 λ steps)
spl3 run cookbook/101_production_sustainability/production_sustainability.spl \
  --adapter claude_cli \
  --param use_solver=true \
  --param n_points=20

# solver=OFF — LLM heuristic, ollama/gemma3
spl3 run cookbook/101_production_sustainability/production_sustainability.spl \
  --adapter ollama -m gemma3 \
  --param use_solver=false
```

## Optimization formulation

**Scalarized LP** (solved once per λ value):

```
Maximize    λ · (profit / 100) − (1−λ) · (carbon / 30)

Subject to  2x + y  ≤ 20    (labor hours)
            3x + 2y ≤ 30    (kg material)
            x ≥ 0,  y ≥ 0

where  profit = 10x + 6y
       carbon =  3x +  y
       λ swept from 0.0 (minimize carbon only) to 1.0 (maximize profit only)
```

Normalization anchors: max_profit=100 (x=10, y=0); max_carbon=30 (same anchor).  
Dominated points are stripped after the sweep to yield the true Pareto front.

## TOOL_API reference

| Function | Purpose |
|---|---|
| `sweep_pareto_scalarization(problem_json, n_points)` | PuLP LP sweep over λ ∈ [0,1]; returns Pareto front JSON |
| `is_pareto_feasible(front_json)` | ASSERT gate: status==OK and ≥2 non-dominated points |
| `format_pareto_table(front_json)` | Renders Pareto front as markdown table |
| `verify_production_off(problem_json, solution_json)` | Checks feasibility and arithmetic for LLM-proposed plan |
| `json_get_field(data_json, field)` | Extracts a field from any JSON object |

## Verification (solver=OFF)

`verify_production_off` checks three things:

1. **Feasibility**: 2x+y ≤ 20, 3x+2y ≤ 30, x ≥ 0, y ≥ 0
2. **Profit arithmetic**: recompute 10x+6y vs. LLM-claimed profit (tolerance ±$0.50)
3. **Carbon arithmetic**: recompute 3x+y vs. LLM-claimed carbon (tolerance ±0.50 kg)

## Output metadata

The `RETURN` statement surfaces:

- `objective` — solver=ON: number of Pareto points found; solver=OFF: claimed profit ($)
- `verify` — solver=ON: N/A; solver=OFF: PASS / FAIL

## Related recipes

- Recipe 78: Single-objective LP/MILP via PuLP (constraint optimization)
- Recipe 99: Markowitz portfolio optimization via cvxpy (convex QP)
- Recipe 100: Supply sourcing (mixed-integer LP)
