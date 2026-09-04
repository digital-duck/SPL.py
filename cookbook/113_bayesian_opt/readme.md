# Recipe 113 — Bayesian Optimization (scikit-optimize)

**The key story:** A product team has 25 experiments to tune (headline_score, layout_score, cta_placement) to maximize conversion rate. Random/uniform search finds ≈11% conversion. Bayesian GP + Expected Improvement finds ≈18–19% — 60%+ relative improvement — by concentrating trials near the promising region discovered in the first 5 random samples. The true optimum is at (0.75, 0.85, 0.60), not at any corner, which is why "maximize all parameters" intuition fails.

## What it demonstrates

| Axis | solver=ON | solver=OFF |
|---|---|---|
| Engine | scikit-optimize GP + Expected Improvement | LLM heuristic CRO reasoning |
| Strategy | Model uncertainty → sample where EI is highest | "Clean layout + personalized headline + CTA above fold" |
| Budget efficiency | ~15 trials to find near-optimum | All 25 trials, many wasted on explored regions |
| Verification | `ASSERT bayesian_improved` (C1) | — |
| Solver class | C1 (improvement over random baseline) | — |

## Why Bayesian beats random on tight budgets

After 5 random samples, the GP has a posterior over the conversion rate surface. The EI acquisition function identifies where `E[max(f(x) - f_best, 0)]` is largest — balancing **exploration** (uncertain regions) and **exploitation** (near the current best). Each new trial updates the posterior, steering subsequent trials toward the optimum.

Random search has no memory — trial 20 is as uninformed as trial 1.

## Default problem

| Parameter | Range | Meaning |
|---|---|---|
| headline_score | 0–1 | Generic (0) → personalized (1) |
| layout_score | 0–1 | Cluttered (0) → clean (1) |
| cta_placement | 0–1 | Bottom (0) → above fold (1) |

**True optimum**: (0.75, 0.85, 0.60) — personalized headline, clean layout, but CTA only 60% above fold (not fully above fold — users need to see content first).  
**True max conversion**: ~20%

## Run commands

```bash
# solver=ON — Bayesian GP optimization
spl3 run cookbook/113_bayesian_opt/bayesian_opt.spl \
    --llm claude_cli \
    --param use_solver=true

# solver=OFF — LLM heuristic guess
spl3 run cookbook/113_bayesian_opt/bayesian_opt.spl \
    --llm claude_cli \
    --param use_solver=false
```

## Install

```bash
conda activate spl123
pip install scikit-optimize
```

## TOOL_API reference

| Function | Purpose |
|---|---|
| `get_default_problem()` | Returns web page optimization problem JSON |
| `run_bayesian_opt(problem_json)` | GP+EI 25-trial study vs random baseline |
| `bayesian_improved(result_json)` | ASSERT gate: Bayesian > random baseline |
| `format_bayesian_report(result_json)` | Markdown: comparison table + top 5 trials |

## Bayesian vs Optuna TPE (r112)

| | r112 (Optuna TPE) | r113 (Bayesian GP) |
|---|---|---|
| Model | Tree-structured density model | Gaussian Process (probabilistic) |
| Acquisition | Adaptive bandwidth | Expected Improvement / LCB |
| Best for | Discrete + mixed types, large budgets | Continuous, small budgets (≤100 trials) |
| Overhead | Low (no matrix inversion) | O(n³) per step — gets slow > 1000 trials |
| Uncertainty | Implicit (density ratio) | Explicit (posterior variance) |

## Related recipes

- r112: Optuna TPE (same class of problem, different sampler — better for large budgets)
- r110: Nash equilibrium (strategic interaction — not parameter optimization)
- r107: pymoo NSGA-II (multi-objective Pareto — when there are competing objectives)
