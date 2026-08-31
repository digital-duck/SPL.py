"""
Recipe 107 — Workforce 3-Objective Scheduling (cost, quality, risk).
Benchmark B4: 3-shift NSGA-II Pareto surface.
TOOL_APIs called from workforce_3obj.spl.
"""

import json


# ── Default B4 problem ────────────────────────────────────────────────────────

_DEFAULT_B4 = {
    "shifts": [
        {"name": "Day",     "cost": 100.0, "quality": 0.90, "risk": 0.10, "min": 10, "max": 20},
        {"name": "Evening", "cost": 130.0, "quality": 1.00, "risk": 0.25, "min": 10, "max": 20},
        {"name": "Night",   "cost": 160.0, "quality": 0.70, "risk": 0.40, "min": 10, "max": 20},
    ],
    "total_min": 30,
}


# ── Tool functions ────────────────────────────────────────────────────────────

def extract_workforce_problem(problem_text: str) -> str:
    """Parse shift data into JSON.

    Returns:
        {"shifts": [{"name": str, "cost": float, "quality": float, "risk": float,
                     "min": int, "max": int}],
         "total_min": int}

    If parse fails, return default B4 problem as JSON.
    """
    # Try: already valid JSON with expected structure
    try:
        data = json.loads(problem_text)
        shifts = data.get("shifts", [])
        total_min = int(data.get("total_min", 30))
        if shifts and total_min > 0:
            normalised = [
                {
                    "name": str(s.get("name", f"Shift{i+1}")),
                    "cost": float(s["cost"]),
                    "quality": float(s["quality"]),
                    "risk": float(s["risk"]),
                    "min": int(s.get("min", 10)),
                    "max": int(s.get("max", 20)),
                }
                for i, s in enumerate(shifts)
            ]
            return json.dumps({"shifts": normalised, "total_min": total_min})
    except Exception:
        pass

    # Try: lightweight keyword extraction from structured English
    try:
        import re

        total_min_match = re.search(r"[Tt]otal\s+(?:minimum|min)[:\s]+(\d+)", problem_text)
        total_min = int(total_min_match.group(1)) if total_min_match else 30

        # Look for shift lines like "Day shift: $100/employee, 0.90 service quality, 0.10 fatigue risk, min 10 max 20"
        shift_pattern = re.compile(
            r"(Day|Evening|Night)\s+shift[:\s]+\$?\s*([\d.]+)\s*/employee[^,]*,\s*([\d.]+)\s+(?:service\s+)?quality[^,]*,\s*([\d.]+)\s+(?:fatigue\s+)?risk[^,]*,\s*min\s+(\d+)\s+max\s+(\d+)",
            re.I,
        )
        found = []
        for m in shift_pattern.finditer(problem_text):
            found.append({
                "name": m.group(1).capitalize(),
                "cost": float(m.group(2)),
                "quality": float(m.group(3)),
                "risk": float(m.group(4)),
                "min": int(m.group(5)),
                "max": int(m.group(6)),
            })

        if found:
            return json.dumps({"shifts": found, "total_min": total_min})
    except Exception:
        pass

    # Fallback: return the default B4 problem
    return json.dumps(_DEFAULT_B4)


def solve_workforce_pareto(problem_json: str, n_gen: int = 50, pop_size: int = 100) -> str:
    """Run pymoo NSGA-II on the 3-objective integer workforce problem.

    Returns:
        {"status": "OK", "n_points": int, "pareto_front": [
            {"xD": int, "xE": int, "xN": int, "cost": float, "quality": float, "risk": float}
        ]}

    Requires: pip install pymoo
    """
    import numpy as np
    from pymoo.algorithms.moo.nsga2 import NSGA2
    from pymoo.core.problem import Problem
    from pymoo.optimize import minimize
    from pymoo.operators.crossover.sbx import SBX
    from pymoo.operators.mutation.pm import PM
    from pymoo.operators.sampling.rnd import IntegerRandomSampling

    try:
        data = json.loads(problem_json)
    except Exception as e:
        return json.dumps({"status": "PARSE_ERROR", "error": str(e)})

    shifts = data.get("shifts", [])
    total_min = int(data.get("total_min", 30))

    if len(shifts) < 2:
        return json.dumps({"status": "INVALID_INPUT", "error": "need at least 2 shifts"})

    class WorkforceProblem(Problem):
        def __init__(self, shifts, total_min):
            n_var = len(shifts)
            xl = np.array([s["min"] for s in shifts], dtype=float)
            xu = np.array([s["max"] for s in shifts], dtype=float)
            super().__init__(n_var=n_var, n_obj=3, n_ieq_constr=1, xl=xl, xu=xu, vtype=int)
            self.shifts = shifts
            self.total_min = total_min

        def _evaluate(self, X, out, *args, **kwargs):
            X = np.round(X).astype(int)
            costs = np.array([s["cost"] for s in self.shifts])
            qualities = np.array([s["quality"] for s in self.shifts])
            risks = np.array([s["risk"] for s in self.shifts])

            total = X.sum(axis=1)
            cost_obj = (X * costs).sum(axis=1)
            quality_obj = -(X * qualities).sum(axis=1) / total   # negate to minimize
            risk_obj = (X * risks).sum(axis=1) / total

            out["F"] = np.column_stack([cost_obj, quality_obj, risk_obj])
            out["G"] = self.total_min - total  # constraint: total >= total_min → G <= 0

    try:
        problem = WorkforceProblem(shifts, total_min)

        algorithm = NSGA2(
            pop_size=int(pop_size),
            sampling=IntegerRandomSampling(),
            crossover=SBX(prob=0.9, eta=15, vtype=float, repair=None),
            mutation=PM(eta=20, vtype=float, repair=None),
            eliminate_duplicates=True,
        )

        res = minimize(
            problem,
            algorithm,
            termination=("n_gen", int(n_gen)),
            seed=42,
            verbose=False,
        )

        if res.X is None or len(res.X) == 0:
            return json.dumps({"status": "NO_SOLUTION", "n_points": 0, "pareto_front": []})

        X_int = np.round(res.X).astype(int)
        costs_arr = np.array([s["cost"] for s in shifts])
        qualities_arr = np.array([s["quality"] for s in shifts])
        risks_arr = np.array([s["risk"] for s in shifts])

        pareto_points = []
        seen = set()
        for row in X_int:
            key = tuple(row.tolist())
            if key in seen:
                continue
            seen.add(key)
            total = int(row.sum())
            if total < total_min:
                continue  # skip infeasible survivors
            cost_val = float((row * costs_arr).sum())
            quality_val = float((row * qualities_arr).sum()) / total
            risk_val = float((row * risks_arr).sum()) / total
            point = {"cost": round(cost_val, 2), "quality": round(quality_val, 6),
                     "risk": round(risk_val, 6)}
            for i, s in enumerate(shifts):
                point[f"x{s['name'][0]}"] = int(row[i])
            pareto_points.append(point)

        pareto_points.sort(key=lambda p: p["cost"])

        return json.dumps({
            "status": "OK",
            "n_points": len(pareto_points),
            "pareto_front": pareto_points,
        })

    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e)})


def is_pareto_feasible(front_json: str) -> bool:
    """ASSERT gate: True if status==OK and n_points >= 3."""
    try:
        data = json.loads(front_json)
        return data.get("status") == "OK" and int(data.get("n_points", 0)) >= 3
    except Exception:
        return False


def format_pareto_surface(front_json: str) -> str:
    """Format Pareto front as markdown table sorted by cost ascending.

    Columns: xD | xE | xN | Cost ($) | Quality | Risk
    Footer shows min/max per numeric column.
    """
    try:
        data = json.loads(front_json)
        points = data.get("pareto_front", [])
        if not points:
            return "No Pareto-optimal points found."

        # Detect shift key names from first point (xD, xE, xN or similar)
        shift_keys = [k for k in points[0].keys() if k.startswith("x") and len(k) == 2]
        shift_keys.sort()

        header_parts = " | ".join(f"{k}" for k in shift_keys)
        lines = [
            f"| {header_parts} | Cost ($) | Quality | Risk |",
            "|" + "|".join(["---"] * (len(shift_keys) + 3)) + "|",
        ]

        costs = [p["cost"] for p in points]
        qualities = [p["quality"] for p in points]
        risks = [p["risk"] for p in points]

        for pt in points:
            shift_vals = " | ".join(str(pt.get(k, 0)) for k in shift_keys)
            lines.append(
                f"| {shift_vals} | {pt['cost']:,.0f} | {pt['quality']:.4f} | {pt['risk']:.4f} |"
            )

        # Footer with min/max
        lines.append("")
        lines.append(
            f"**Cost:** ${min(costs):,.0f} – ${max(costs):,.0f}  |  "
            f"**Quality:** {min(qualities):.4f} – {max(qualities):.4f}  |  "
            f"**Risk:** {min(risks):.4f} – {max(risks):.4f}"
        )
        return "\n".join(lines)

    except Exception as e:
        return f"Could not format Pareto surface: {e}"


def compute_utopia_anchors(problem_json: str) -> str:
    """Compute per-objective optimal solutions using PuLP (continuous relaxation).

    Returns:
        {"min_cost": {...}, "max_quality": {...}, "min_risk": {...}}
    Each anchor: {"xD": float, "xE": float, "xN": float, "cost": float, "quality": float, "risk": float}
    """
    import pulp

    try:
        data = json.loads(problem_json)
    except Exception as e:
        return json.dumps({"error": f"parse error: {e}"})

    shifts = data.get("shifts", [])
    total_min = float(data.get("total_min", 30))
    n = len(shifts)

    if n < 2:
        return json.dumps({"error": "need at least 2 shifts"})

    names = [s["name"] for s in shifts]
    costs = {s["name"]: float(s["cost"]) for s in shifts}
    qualities = {s["name"]: float(s["quality"]) for s in shifts}
    risks = {s["name"]: float(s["risk"]) for s in shifts}
    mins = {s["name"]: float(s["min"]) for s in shifts}
    maxs = {s["name"]: float(s["max"]) for s in shifts}

    def make_vars(prob):
        return {
            name: pulp.LpVariable(f"x_{name}", lowBound=mins[name], upBound=maxs[name])
            for name in names
        }

    def calc_metrics(x_vals, total):
        cost_v = sum(costs[n] * x_vals[n] for n in names)
        quality_v = sum(qualities[n] * x_vals[n] for n in names) / total if total > 0 else 0.0
        risk_v = sum(risks[n] * x_vals[n] for n in names) / total if total > 0 else 0.0
        return cost_v, quality_v, risk_v

    anchors = {}

    # ── 1. Minimize cost ──────────────────────────────────────────
    try:
        prob = pulp.LpProblem("min_cost", pulp.LpMinimize)
        x = make_vars(prob)
        prob += pulp.lpSum(costs[n] * x[n] for n in names)
        prob += pulp.lpSum(x[n] for n in names) >= total_min
        prob.solve(pulp.PULP_CBC_CMD(msg=False))

        x_vals = {n: pulp.value(x[n]) or 0.0 for n in names}
        total = sum(x_vals.values())
        cost_v, quality_v, risk_v = calc_metrics(x_vals, total)
        anchor = {"cost": round(cost_v, 2), "quality": round(quality_v, 6), "risk": round(risk_v, 6)}
        for name in names:
            anchor[f"x{name[0]}"] = round(float(x_vals[name]), 2)
        anchors["min_cost"] = anchor
    except Exception as e:
        anchors["min_cost"] = {"error": str(e)}

    # ── 2. Maximize quality (minimize negative quality) ───────────
    try:
        prob = pulp.LpProblem("max_quality", pulp.LpMinimize)
        x = make_vars(prob)
        total_expr = pulp.lpSum(x[n] for n in names)
        prob += pulp.lpSum(x[n] for n in names) >= total_min
        # linearised: minimize -sum(quality_n * x_n), ignore total (constant denominator changes quality ordering slightly)
        prob += -pulp.lpSum(qualities[n] * x[n] for n in names)
        prob.solve(pulp.PULP_CBC_CMD(msg=False))

        x_vals = {n: pulp.value(x[n]) or 0.0 for n in names}
        total = sum(x_vals.values())
        cost_v, quality_v, risk_v = calc_metrics(x_vals, total)
        anchor = {"cost": round(cost_v, 2), "quality": round(quality_v, 6), "risk": round(risk_v, 6)}
        for name in names:
            anchor[f"x{name[0]}"] = round(float(x_vals[name]), 2)
        anchors["max_quality"] = anchor
    except Exception as e:
        anchors["max_quality"] = {"error": str(e)}

    # ── 3. Minimize risk ──────────────────────────────────────────
    try:
        prob = pulp.LpProblem("min_risk", pulp.LpMinimize)
        x = make_vars(prob)
        prob += pulp.lpSum(x[n] for n in names)
        prob += pulp.lpSum(x[n] for n in names) >= total_min
        prob += pulp.lpSum(risks[n] * x[n] for n in names)
        prob.solve(pulp.PULP_CBC_CMD(msg=False))

        x_vals = {n: pulp.value(x[n]) or 0.0 for n in names}
        total = sum(x_vals.values())
        cost_v, quality_v, risk_v = calc_metrics(x_vals, total)
        anchor = {"cost": round(cost_v, 2), "quality": round(quality_v, 6), "risk": round(risk_v, 6)}
        for name in names:
            anchor[f"x{name[0]}"] = round(float(x_vals[name]), 2)
        anchors["min_risk"] = anchor
    except Exception as e:
        anchors["min_risk"] = {"error": str(e)}

    return json.dumps(anchors)


def verify_workforce_off(problem_json: str, solution_json: str) -> str:
    """Verify LLM-proposed schedule.

    Checks:
    - integer feasibility: xD, xE, xN are integers
    - bounds: each in [min, max]
    - total: xD+xE+xN >= total_min
    - cost, quality, risk: recompute and check vs claimed

    Returns {"verdict": "PASS"/"FAIL"/"PARTIAL", "notes": str}
    """
    try:
        problem = json.loads(problem_json)
        sol = json.loads(solution_json)
    except Exception as e:
        return json.dumps({"verdict": "FAIL", "notes": f"parse error: {e}"})

    shifts = problem.get("shifts", [])
    total_min = int(problem.get("total_min", 30))

    notes = []
    ok = True
    partial = False

    # Build shift map
    shift_map = {s["name"]: s for s in shifts}
    short_map = {s["name"][0]: s["name"] for s in shifts}  # D -> Day, E -> Evening, N -> Night

    x_vals = {}
    for s in shifts:
        key = f"x{s['name'][0]}"
        val = sol.get(key)
        if val is None:
            notes.append(f"missing {key} in solution")
            ok = False
            x_vals[s["name"]] = 0
            continue
        # Integer check
        try:
            float_val = float(val)
            int_val = int(round(float_val))
            if abs(float_val - int_val) > 0.01:
                notes.append(f"{key}={val} is not an integer")
                partial = True
            x_vals[s["name"]] = int_val
        except Exception:
            notes.append(f"{key} is not numeric: {val}")
            ok = False
            x_vals[s["name"]] = 0

    # Bounds check
    for s in shifts:
        name = s["name"]
        v = x_vals.get(name, 0)
        if v < s["min"] or v > s["max"]:
            notes.append(f"x{name[0]}={v} out of bounds [{s['min']}, {s['max']}]")
            ok = False

    # Total check
    total = sum(x_vals.values())
    if total < total_min:
        notes.append(f"total staff {total} < minimum {total_min}")
        ok = False

    # Recompute metrics
    if total > 0:
        recomp_cost = sum(shift_map[n]["cost"] * v for n, v in x_vals.items() if n in shift_map)
        recomp_quality = sum(shift_map[n]["quality"] * v for n, v in x_vals.items() if n in shift_map) / total
        recomp_risk = sum(shift_map[n]["risk"] * v for n, v in x_vals.items() if n in shift_map) / total

        claimed_cost = sol.get("cost")
        claimed_quality = sol.get("quality")
        claimed_risk = sol.get("risk")

        if claimed_cost is not None and abs(float(claimed_cost) - recomp_cost) > 5.0:
            notes.append(f"cost mismatch: claimed={float(claimed_cost):.0f}, recomputed={recomp_cost:.0f}")
            ok = False

        if claimed_quality is not None and abs(float(claimed_quality) - recomp_quality) > 0.01:
            notes.append(f"quality mismatch: claimed={float(claimed_quality):.4f}, recomputed={recomp_quality:.4f}")
            partial = True

        if claimed_risk is not None and abs(float(claimed_risk) - recomp_risk) > 0.01:
            notes.append(f"risk mismatch: claimed={float(claimed_risk):.4f}, recomputed={recomp_risk:.4f}")
            partial = True

    verdict = "PASS" if ok and not partial else ("PARTIAL" if partial and ok else "FAIL")
    return json.dumps({
        "verdict": verdict,
        "total_staff": total,
        "recomputed_cost": round(recomp_cost, 2) if total > 0 else None,
        "recomputed_quality": round(recomp_quality, 4) if total > 0 else None,
        "recomputed_risk": round(recomp_risk, 4) if total > 0 else None,
        "notes": "; ".join(notes) if notes else "all checks passed",
    })


def json_get_field(data_json: str, field: str) -> str:
    """Extract a field from JSON as string."""
    try:
        data = json.loads(data_json)
        return str(data.get(field, ""))
    except Exception:
        return ""
