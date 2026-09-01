"""Recipe 113 — Bayesian Optimization (scikit-optimize).

Uses Gaussian Process regression + Expected Improvement (EI) acquisition
to find the optimum of a black-box function with minimum experiment cost.

Problem: Multi-parameter web page optimization — find (headline_score,
layout_score, cta_placement) combination that maximizes conversion rate
with a limited trial budget.

Comparison: Bayesian GP vs random/uniform search allocation.

Install: pip install scikit-optimize
"""

import json
import math
import random


# ── Synthetic conversion rate objective ──────────────────────────────────────

def _conversion_rate(headline: float, layout: float, cta: float) -> float:
    """Simulate a web page conversion rate (black box).

    Parameters are on [0, 1] scales:
      headline: 0=generic, 1=personalized
      layout:   0=cluttered, 1=clean
      cta:      0=bottom, 1=above-fold

    The true optimum is near (0.75, 0.85, 0.60) — not at corners or center.
    The function has a ridge and a local optimum near (0.3, 0.4, 0.8).
    """
    # Main peak
    main = math.exp(-8 * ((headline - 0.75) ** 2 + (layout - 0.85) ** 2 + (cta - 0.60) ** 2))
    # Local optimum (decoy)
    local = 0.55 * math.exp(-10 * ((headline - 0.3) ** 2 + (layout - 0.4) ** 2 + (cta - 0.8) ** 2))
    # Baseline + noise (deterministic seed for reproducibility)
    base = 0.05 + 0.12 * headline + 0.08 * layout + 0.06 * cta
    return round(min(0.35, max(0.02, base + 0.20 * main + 0.12 * local)), 4)


_DEFAULT_OPT_PROBLEM = {
    "problem_name": "Web Page Conversion Rate Optimizer",
    "description":  (
        "Maximize web page conversion rate by tuning three design parameters: "
        "headline_score (0=generic to 1=personalized), "
        "layout_score (0=cluttered to 1=clean), "
        "cta_placement (0=bottom to 1=above-fold). "
        "Budget: 25 experiment slots. "
        "Uniform/random baseline: tests parameters evenly, often wastes budget on losers. "
        "Bayesian GP: concentrates trials near the promising region found in early trials."
    ),
    "parameters": [
        {"name": "headline_score",  "low": 0.0, "high": 1.0},
        {"name": "layout_score",    "low": 0.0, "high": 1.0},
        {"name": "cta_placement",   "low": 0.0, "high": 1.0},
    ],
    "n_calls":          25,
    "n_random_starts":  5,
    "true_optimum":     {"headline_score": 0.75, "layout_score": 0.85, "cta_placement": 0.60},
    "true_max_rate":    None,
    "random_baseline":  {"n_calls": 25, "seed": 99},
}


def get_default_problem() -> str:
    p = dict(_DEFAULT_OPT_PROBLEM)
    opt = p["true_optimum"]
    p["true_max_rate"] = _conversion_rate(opt["headline_score"], opt["layout_score"], opt["cta_placement"])
    return json.dumps(p)


def run_bayesian_opt(problem_json: str) -> str:
    """Run scikit-optimize GP minimization (negated for maximization).

    Returns:
      {"problem_name": str, "best_params": {...}, "best_rate": float,
       "random_best_rate": float, "true_max_rate": float,
       "trials_to_best": int, "improvement_over_random": float,
       "top_trials": [{params, rate}], "status": "OK"|"ERROR"}
    """
    try:
        from skopt import gp_minimize  # type: ignore[import-untyped]
        from skopt.space import Real  # type: ignore[import-untyped]
    except ImportError:
        return json.dumps({"status": "ERROR",
                           "error": "scikit-optimize not installed — run: pip install scikit-optimize"})

    try:
        problem  = json.loads(problem_json)
        n_calls  = problem.get("n_calls", 25)
        n_rand   = problem.get("n_random_starts", 5)
        params   = problem["parameters"]

        space = [Real(p["low"], p["high"], name=p["name"]) for p in params]

        def neg_objective(x):
            return -_conversion_rate(x[0], x[1], x[2])

        result = gp_minimize(neg_objective, space, n_calls=n_calls,
                             n_initial_points=n_rand, random_state=42)

        best_params = {p["name"]: round(v, 4) for p, v in zip(params, result.x)}
        best_rate   = round(-result.fun, 4)

        # Random baseline: n_calls uniform random samples
        rng = random.Random(99)
        rand_rates  = [_conversion_rate(rng.random(), rng.random(), rng.random())
                       for _ in range(n_calls)]
        random_best = round(max(rand_rates), 4)

        # Find which trial achieved the best result
        all_rates = [-y for y in result.func_vals]
        trials_to_best = int(all_rates.index(max(all_rates))) + 1

        trial_list = [{"params": {p["name"]: round(x, 3) for p, x in zip(params, xs)},
                        "rate": round(-y, 4)}
                       for xs, y in zip(result.x_iters, result.func_vals)]
        top_trials = sorted(trial_list, key=lambda t: t["rate"], reverse=True)[:5]  # type: ignore[arg-type]

        improvement = round((best_rate - random_best) / random_best * 100, 1)

        return json.dumps({
            "problem_name":             problem.get("problem_name", "Problem"),
            "best_params":              best_params,
            "best_rate":                best_rate,
            "random_best_rate":         random_best,
            "true_max_rate":            problem.get("true_max_rate"),
            "trials_to_best":           trials_to_best,
            "n_calls":                  n_calls,
            "improvement_over_random":  improvement,
            "top_trials":               top_trials,
            "status":                   "OK",
        })

    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e)})


def bayesian_improved(result_json: str) -> bool:
    """ASSERT gate: Bayesian result beats random baseline."""
    try:
        data = json.loads(result_json)
        return data.get("status") == "OK" and data.get("improvement_over_random", 0) > 0
    except Exception:
        return False


def format_bayesian_report(result_json: str) -> str:
    """Markdown report of Bayesian optimization results."""
    try:
        data = json.loads(result_json)
        bp   = data.get("best_params", {})
        lines = [
            f"## Bayesian Optimization Report — {data.get('problem_name', 'Problem')}",
            "",
            f"**Budget:** {data.get('n_calls', '?')} experiment slots  ",
            f"**Best conversion rate (Bayesian):** {data.get('best_rate', '?'):.2%}  ",
            f"**Best conversion rate (random):** {data.get('random_best_rate', '?'):.2%}  ",
            f"**True optimum:** {data.get('true_max_rate', '?'):.2%}  ",
            f"**Improvement over random:** +{data.get('improvement_over_random', '?')}%  ",
            f"**Trials to find best:** {data.get('trials_to_best', '?')} / {data.get('n_calls', '?')}",
            "",
            "### Best Parameters Found",
            "",
            "| Parameter | Value |",
            "|---|---|",
        ]
        for k, v in bp.items():
            lines.append(f"| {k} | {v:.3f} |")

        lines += [
            "",
            "### Top 5 Trials",
            "",
            "| Rank | headline | layout | cta | Conversion Rate |",
            "|---|---|---|---|---|",
        ]
        for i, t in enumerate(data.get("top_trials", []), 1):
            p = t["params"]
            lines.append(
                f"| {i} | {p.get('headline_score', '?')} "
                f"| {p.get('layout_score', '?')} "
                f"| {p.get('cta_placement', '?')} "
                f"| {t['rate']:.2%} |"
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
