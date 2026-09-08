"""
Recipe 114 — Constrained nonlinear optimization via scipy.optimize.
TOOL_APIs called from scipy_nonlinear.spl.

Supported problem types:
  pricing   — maximize profit = (price - unit_cost) * demand(price) - fixed_cost
               where demand(price) = demand_scale * price ** (-elasticity)
  logistics — maximize profit = revenue(x) - cost(x)
               where revenue = revenue_scale * x - saturation * x^2
               and   cost    = fixed_cost + unit_cost * x + congestion * x^2
"""

import json
import math
import re


def _clean_json(text: str) -> str:
    """Strip markdown code fences that LLMs sometimes add around JSON output."""
    text = text.strip()
    m = re.match(r'^```(?:json)?\s*(.*?)\s*```$', text, re.DOTALL)
    return m.group(1) if m else text


def solve_nonlinear(problem_json: str,
                    method: str = "SLSQP",
                    max_iterations: int = 1000) -> str:
    """
    Solve a constrained nonlinear optimization problem using scipy.optimize.

    Args:
        problem_json:   JSON with keys: type, params, bounds, constraints (optional).
        method:         Scipy solver — "SLSQP" (default, handles constraints),
                        "Nelder-Mead" (derivative-free, bounds only),
                        "differential_evolution" (global search, bounds only).
                        Must be one of these three.
        max_iterations: Max solver iterations, must be in [100, 10000] (default 1000).

    Returns JSON: {success, method, x_opt, objective, n_iterations, message}
    """
    valid_methods = {"SLSQP", "Nelder-Mead", "differential_evolution"}
    if method not in valid_methods:
        return json.dumps({"success": False,
                           "error": f"method must be one of {sorted(valid_methods)}"})
    if not (100 <= max_iterations <= 10000):
        return json.dumps({"success": False,
                           "error": f"max_iterations {max_iterations} out of range [100, 10000]"})

    try:
        from scipy.optimize import minimize, differential_evolution

        prob = json.loads(_clean_json(problem_json))
        ptype = prob.get("type", "pricing")
        params = prob.get("params", {})
        bounds_raw = prob.get("bounds", {})
        x_min = float(bounds_raw.get("x_min", 1.0))
        x_max = float(bounds_raw.get("x_max", 100.0))

        if ptype == "pricing":
            demand_scale = float(params.get("demand_scale", 10000.0))
            elasticity   = float(params.get("elasticity", 1.5))
            unit_cost    = float(params.get("unit_cost", 5.0))
            fixed_cost   = float(params.get("fixed_cost", 50.0))
            min_demand   = float(params.get("min_demand", 0.0))

            def _neg_profit_pricing(p):
                demand = demand_scale * p[0] ** (-elasticity)
                return -((p[0] - unit_cost) * demand - fixed_cost)

            objective_fn = _neg_profit_pricing
            constraints = []
            if min_demand > 0:
                constraints.append({
                    "type": "ineq",
                    "fun": lambda p: demand_scale * p[0] ** (-elasticity) - min_demand,
                })

        elif ptype == "logistics":
            fixed_cost      = float(params.get("fixed_cost", 200.0))
            unit_cost       = float(params.get("unit_cost", 8.0))
            congestion      = float(params.get("congestion_factor", 0.05))
            revenue_scale   = float(params.get("revenue_scale", 20.0))
            saturation      = float(params.get("saturation_factor", 0.02))
            min_demand      = float(params.get("min_demand", 0.0))

            def _neg_profit_logistics(x):
                revenue = revenue_scale * x[0] - saturation * x[0] ** 2
                cost    = fixed_cost + unit_cost * x[0] + congestion * x[0] ** 2
                return -(revenue - cost)

            objective_fn = _neg_profit_logistics
            constraints = []
            if min_demand > 0:
                constraints.append({
                    "type": "ineq",
                    "fun": lambda x: x[0] - min_demand,
                })

        else:
            return json.dumps({"success": False,
                               "error": f"unknown problem type '{ptype}'; use 'pricing' or 'logistics'"})

        scipy_bounds = [(x_min, x_max)]
        x0 = [(x_min + x_max) / 2.0]

        if method == "differential_evolution":
            result = differential_evolution(
                objective_fn,
                bounds=scipy_bounds,
                maxiter=max_iterations,
                seed=42,
                tol=1e-8,
            )
            x_opt = float(result.x[0])
        else:
            result = minimize(
                objective_fn,
                x0,
                method=method,
                bounds=scipy_bounds,
                constraints=constraints if method == "SLSQP" else [],
                options={"maxiter": max_iterations, "ftol": 1e-10},
            )
            x_opt = float(result.x[0])

        objective = float(-result.fun)

        return json.dumps({
            "success": bool(result.success),
            "method": method,
            "problem_type": ptype,
            "x_opt": round(x_opt, 4),
            "objective": round(objective, 4),
            "n_iterations": int(result.nit) if hasattr(result, "nit") else None,
            "message": result.message,
        })

    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


def verify_solution(problem_json: str, solution_json: str) -> str:
    """
    Independent back-substitution verifier.
    Recomputes the objective from scratch at x_opt and checks it matches.

    Args:
        problem_json:  Same JSON passed to solve_nonlinear.
        solution_json: JSON output from solve_nonlinear.

    Returns JSON: {verdict, x_opt, recomputed_objective, reported_objective, delta, notes}
    """
    try:
        prob = json.loads(_clean_json(problem_json))
        sol  = json.loads(_clean_json(solution_json))

        if not sol.get("success"):
            return json.dumps({"verdict": "SKIP", "notes": "solver did not succeed"})

        ptype  = prob.get("type", "pricing")
        params = prob.get("params", {})
        x_opt  = float(sol["x_opt"])
        reported = float(sol["objective"])
        notes: list[str] = []

        if ptype == "pricing":
            demand_scale = float(params.get("demand_scale", 10000.0))
            elasticity   = float(params.get("elasticity", 1.5))
            unit_cost    = float(params.get("unit_cost", 5.0))
            fixed_cost   = float(params.get("fixed_cost", 50.0))
            demand       = demand_scale * x_opt ** (-elasticity)
            recomputed   = round((x_opt - unit_cost) * demand - fixed_cost, 4)

        elif ptype == "logistics":
            fixed_cost    = float(params.get("fixed_cost", 200.0))
            unit_cost     = float(params.get("unit_cost", 8.0))
            congestion    = float(params.get("congestion_factor", 0.05))
            revenue_scale = float(params.get("revenue_scale", 20.0))
            saturation    = float(params.get("saturation_factor", 0.02))
            revenue       = revenue_scale * x_opt - saturation * x_opt ** 2
            cost          = fixed_cost + unit_cost * x_opt + congestion * x_opt ** 2
            recomputed    = round(revenue - cost, 4)

        else:
            return json.dumps({"verdict": "SKIP", "notes": f"unknown type '{ptype}'"})

        delta = abs(recomputed - reported)
        if delta > 0.01:
            notes.append(f"objective mismatch: recomputed={recomputed}, reported={reported}, Δ={delta:.4f}")

        bounds_raw = prob.get("bounds", {})
        x_min = float(bounds_raw.get("x_min", 1.0))
        x_max = float(bounds_raw.get("x_max", 100.0))
        if not (x_min <= x_opt <= x_max):
            notes.append(f"x_opt={x_opt} outside bounds [{x_min}, {x_max}]")

        ok = len(notes) == 0
        return json.dumps({
            "verdict": "PASS" if ok else "FAIL",
            "x_opt": x_opt,
            "recomputed_objective": recomputed,
            "reported_objective": reported,
            "delta": round(delta, 6),
            "notes": "; ".join(notes) if notes else "all checks passed",
        })

    except Exception as e:
        return json.dumps({"verdict": "ERROR", "notes": str(e)})


def is_optimal(solution_json: str) -> bool:
    """Return True when scipy reports success and objective is finite."""
    try:
        data = json.loads(solution_json)
        return (data.get("success") is True
                and data.get("objective") is not None
                and math.isfinite(float(data["objective"])))
    except Exception:
        return False


def solver_enabled(use_solver: str) -> str:
    """Return 'run_solver' or 'run_llm' — distinctive strings for unambiguous EVALUATE matching."""
    if use_solver.strip().lower() in ("true", "1", "yes", "on"):
        return "run_solver"
    return "run_llm"


def save_report(report: str, out_dir: str, filename: str) -> str:
    """Write report text to out_dir/filename, creating the directory if needed."""
    import os
    from pathlib import Path
    out = Path(out_dir) if os.path.isabs(out_dir) else Path(os.getcwd()) / out_dir
    out.mkdir(parents=True, exist_ok=True)
    dest = out / filename
    dest.write_text(report, encoding="utf-8")
    return str(dest)
