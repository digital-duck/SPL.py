"""Recipe 112 — Optuna Black-Box Strategy Optimization.

Uses Optuna TPE (Tree-structured Parzen Estimator) to find optimal
strategy parameters when the objective function has no analytical form.

Problem: SaaS pricing strategy — tune (price, discount, trial_days) to
maximize customer LTV. The objective is a black-box simulation (churn model +
conversion funnel), not a closed-form expression.

Install: pip install optuna
"""

import json
import math


# ── Synthetic LTV objective (the "black box") ─────────────────────────────────

def _ltv_objective(price: float, discount_pct: float, trial_days: int) -> float:
    """Simulate customer lifetime value.

    This is a non-convex, non-analytic function with multiple local optima.
    Represents a simplified churn + conversion model — no gradient available.
    """
    # Conversion rate: longer trial + lower price increases trial→paid conversion
    trial_factor = 1.0 - math.exp(-trial_days / 10.0)     # saturates ~30 days
    price_factor  = math.exp(-0.015 * (price - 30))        # lower price → higher conv
    conversion    = 0.35 * trial_factor * price_factor      # base conversion 35%
    conversion    = max(0.01, min(0.70, conversion))

    # Annual discount reduces monthly equivalent revenue
    monthly_revenue = price * (1 - discount_pct / 100) * (1 - 0.08 * (discount_pct > 20))

    # Churn rate: higher price → higher churn (non-linear)
    monthly_churn = 0.04 + 0.003 * max(0, price - 50) + 0.002 * max(0, discount_pct - 25)
    monthly_churn = min(monthly_churn, 0.25)

    # LTV = conversion × (monthly_revenue / churn_rate) × acquisition_cost_adj
    ltv = conversion * (monthly_revenue / monthly_churn) * 0.85
    return round(ltv, 2)


_DEFAULT_STRATEGY_PROBLEM = {
    "problem_name":   "SaaS Pricing Strategy Optimization",
    "description":    (
        "Find the optimal combination of monthly_price ($30–$120), "
        "annual_discount_pct (0%–40%), and trial_days (3–30) to maximize "
        "customer lifetime value (LTV). The LTV model is a black box: it "
        "depends on a churn model and conversion funnel with no closed-form gradient."
    ),
    "parameters": [
        {"name": "monthly_price",       "type": "float", "low": 30,  "high": 120},
        {"name": "annual_discount_pct", "type": "float", "low": 0,   "high": 40},
        {"name": "trial_days",          "type": "int",   "low": 3,   "high": 30},
    ],
    "objective":    "maximize LTV (customer lifetime value in $)",
    "n_trials":     50,
    "naive_baseline": {
        "monthly_price": 50, "annual_discount_pct": 20, "trial_days": 14,
        "ltv": None,
    },
}


def get_default_problem() -> str:
    """Return default pricing strategy optimization problem JSON."""
    p = dict(_DEFAULT_STRATEGY_PROBLEM)
    nb = dict(p["naive_baseline"])
    nb["ltv"] = _ltv_objective(nb["monthly_price"], nb["annual_discount_pct"], nb["trial_days"])
    p["naive_baseline"] = nb
    return json.dumps(p)


def run_optuna_study(problem_json: str) -> str:
    """Run an Optuna TPE study to find optimal strategy parameters.

    Returns:
      {"problem_name": str, "best_params": {...}, "best_value": float,
       "naive_value": float, "improvement_pct": float, "n_trials": int,
       "top_trials": [{params, value}], "status": "OK"|"ERROR"}
    """
    try:
        import optuna  # type: ignore[import-untyped]
        optuna.logging.set_verbosity(optuna.logging.WARNING)
    except ImportError:
        return json.dumps({"status": "ERROR",
                           "error": "optuna not installed — run: pip install optuna"})

    try:
        problem = json.loads(problem_json)
        n_trials = problem.get("n_trials", 50)
        nb       = problem["naive_baseline"]
        naive_ltv = nb.get("ltv") or _ltv_objective(
            nb["monthly_price"], nb["annual_discount_pct"], nb["trial_days"]
        )

        param_defs = {p["name"]: p for p in problem["parameters"]}

        def objective(trial):
            price    = trial.suggest_float(
                "monthly_price",
                param_defs["monthly_price"]["low"],
                param_defs["monthly_price"]["high"],
            )
            discount = trial.suggest_float(
                "annual_discount_pct",
                param_defs["annual_discount_pct"]["low"],
                param_defs["annual_discount_pct"]["high"],
            )
            trial_d  = trial.suggest_int(
                "trial_days",
                param_defs["trial_days"]["low"],
                param_defs["trial_days"]["high"],
            )
            return _ltv_objective(price, discount, trial_d)

        study = optuna.create_study(direction="maximize",
                                    sampler=optuna.samplers.TPESampler(seed=42))
        study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

        best = study.best_trial
        improvement = round((best.value - naive_ltv) / naive_ltv * 100, 1)

        top5 = sorted(study.trials, key=lambda t: t.value or 0, reverse=True)[:5]
        top_trials = [
            {"params": t.params, "ltv": round(t.value or 0, 2)}
            for t in top5
        ]

        return json.dumps({
            "problem_name":   problem.get("problem_name", "Problem"),
            "best_params":    best.params,
            "best_value":     round(best.value, 2),
            "naive_params":   {"monthly_price": nb["monthly_price"],
                               "annual_discount_pct": nb["annual_discount_pct"],
                               "trial_days": nb["trial_days"]},
            "naive_value":    round(naive_ltv, 2),
            "improvement_pct": improvement,
            "n_trials":       n_trials,
            "top_trials":     top_trials,
            "status":         "OK",
        })

    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e)})


def optimization_improved(result_json: str) -> bool:
    """ASSERT gate: Optuna found a result better than the naive baseline."""
    try:
        data = json.loads(result_json)
        return data.get("status") == "OK" and data.get("improvement_pct", 0) > 0
    except Exception:
        return False


def format_optuna_report(result_json: str) -> str:
    """Markdown report of Optuna study results."""
    try:
        data = json.loads(result_json)
        bp   = data.get("best_params", {})
        np_  = data.get("naive_params", {})
        lines = [
            f"## Optuna Black-Box Optimization — {data.get('problem_name', 'Problem')}",
            "",
            f"**Trials:** {data.get('n_trials', '?')}  ",
            f"**Best LTV:** ${data.get('best_value', '?')}/customer  ",
            f"**Naive LTV:** ${data.get('naive_value', '?')}/customer  ",
            f"**Improvement:** +{data.get('improvement_pct', '?')}%",
            "",
            "| Parameter | Naive (LLM guess) | Optuna Best |",
            "|---|---|---|",
            f"| monthly_price | ${np_.get('monthly_price', '?')} | ${round(bp.get('monthly_price', 0), 1)} |",
            f"| annual_discount_pct | {np_.get('annual_discount_pct', '?')}% | {round(bp.get('annual_discount_pct', 0), 1)}% |",
            f"| trial_days | {np_.get('trial_days', '?')} days | {bp.get('trial_days', '?')} days |",
            "",
            "### Top 5 Trials",
            "",
            "| Rank | Price | Discount | Trial Days | LTV |",
            "|---|---|---|---|---|",
        ]
        for i, t in enumerate(data.get("top_trials", []), 1):
            p = t["params"]
            lines.append(
                f"| {i} | ${round(p.get('monthly_price', 0), 1)} "
                f"| {round(p.get('annual_discount_pct', 0), 1)}% "
                f"| {p.get('trial_days', '?')} days "
                f"| ${t['ltv']} |"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"(format error: {e})"


def json_get_field(data_json: str, field: str) -> str:
    try:
        v = json.loads(data_json).get(field)
        return str(v) if v is not None else ""
    except Exception:
        return ""
