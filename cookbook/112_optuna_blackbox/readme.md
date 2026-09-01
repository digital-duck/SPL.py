# Recipe 112 — Optuna Black-Box Strategy Optimization

**The key story:** A SaaS team needs to tune (monthly_price, annual_discount_pct, trial_days) to maximize customer LTV. The LTV model is non-convex with no gradient. LLM guesses price=$50, 20% discount, 14-day trial → LTV=$172. Optuna TPE (50 trials) finds price≈$43, 28% discount, 7-day trial → LTV≈$218 — a 21% improvement the LLM missed because the objective has a non-obvious interaction between trial length and conversion.

## What it demonstrates

| Axis | solver=ON | solver=OFF |
|---|---|---|
| Engine | Optuna TPE (Tree-structured Parzen Estimator) | LLM heuristic reasoning |
| Guarantee | Global optimum approximation over 50 trials | Local intuition, misses parameter interactions |
| Objective | Non-convex black-box (churn + conversion model) | "Lower price = more customers = better LTV" |
| Verification | `ASSERT optimization_improved` (C1) | — |
| Solver class | C1 (improvement verified vs baseline) + C2 (LTV recomputed) | — |

## Why this objective is hard

The LTV function has three interacting non-linearities:
1. **Conversion**: `1 - exp(-trial_days/10)` — saturates at ~30 days; short trials not catastrophic
2. **Churn penalty**: jumps at `price > 50` and `discount > 25` — high-discount churners are cheap customers
3. **Revenue per customer**: discount × price interaction creates a valley at naive (50, 20%) parameters

No gradient. No closed form. Optuna samples where previous trials showed improvement.

## Default problem parameters

| Parameter | Range | Naive (LLM) | Optuna Best |
|---|---|---|---|
| monthly_price | $30–$120 | $50 | ~$43 |
| annual_discount_pct | 0%–40% | 20% | ~28% |
| trial_days | 3–30 | 14 | ~7 |
| **LTV** | — | **~$172** | **~$218** |

## Run commands

```bash
# solver=ON — Optuna 50-trial TPE study
spl3 run cookbook/112_optuna_blackbox/optuna_blackbox.spl \
    --adapter claude_cli --param use_solver=true

# solver=OFF — LLM heuristic guess
spl3 run cookbook/112_optuna_blackbox/optuna_blackbox.spl \
    --adapter ollama -m gemma3 --param use_solver=false

# More trials for higher accuracy
spl3 run cookbook/112_optuna_blackbox/optuna_blackbox.spl \
    --adapter claude_cli --param use_solver=true
```

## Install

```bash
conda activate spl123
pip install optuna
```

## TOOL_API reference

| Function | Purpose |
|---|---|
| `get_default_problem()` | Returns SaaS pricing problem JSON (params + naive baseline) |
| `run_optuna_study(problem_json)` | Optuna TPE study → best params + top 5 trials |
| `optimization_improved(result_json)` | ASSERT gate: best_value > naive_value |
| `format_optuna_report(result_json)` | Markdown comparison table + top 5 trials |

## When to use Optuna vs analytical optimization

| Situation | Use |
|---|---|
| Objective has gradient, convex | LP/QP solver (r78, r99) |
| Objective has gradient, non-convex | scipy.optimize, gradient descent |
| Objective is a black box (simulation, A/B test) | **Optuna TPE** (r112) |
| Objective + uncertainty (few trials budget) | Bayesian GP (r113) |
| Multiple competing objectives | pymoo NSGA-II (r107) |

## Related recipes

- r113: Ax Bayesian optimization (GP-based, fewer trials needed)
- r107: pymoo NSGA-II (multi-objective Pareto, not single-objective)
- r78: PuLP constraint optimization (analytical LP with gradient)
