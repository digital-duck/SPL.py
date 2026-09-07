"""
Recipe 121 — Platypus MOEA 3-Objective Workforce Scheduling (S020).
Lighter alternative to pymoo (r107): same B4 problem, platypus NSGA-II.
TOOL_APIs called from platypus_moea.spl.
"""

import json
import random
from spl.tools import spl_tool
from spl.stdlib import strip_fences as _strip_fences


# ── Default B4 problem (same as r107 for direct comparison) ──────────────────

_DEFAULT_B4 = {
    "shifts": [
        {"name": "Day",     "cost": 100.0, "quality": 0.90, "risk": 0.10, "min": 10, "max": 20},
        {"name": "Evening", "cost": 130.0, "quality": 1.00, "risk": 0.25, "min": 10, "max": 20},
        {"name": "Night",   "cost": 160.0, "quality": 0.70, "risk": 0.40, "min": 10, "max": 20},
    ],
    "total_min": 30,
}


# ── Tool functions ────────────────────────────────────────────────────────────

@spl_tool
def extract_workforce_problem(problem_text: str) -> str:
    """Parse shift data into JSON. Falls back to default B4 problem on failure.

    Returns:
        {"shifts": [{"name", "cost", "quality", "risk", "min", "max"}], "total_min": int}
    """
    try:
        data = json.loads(_strip_fences(problem_text))
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

    try:
        import re
        total_min_match = re.search(r"[Tt]otal\s+(?:minimum|min)[:\s]+(\d+)", problem_text)
        total_min = int(total_min_match.group(1)) if total_min_match else 30
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

    return json.dumps(_DEFAULT_B4)


@spl_tool
def solve_workforce_platypus(problem_json: str, n_eval: str = "5000", pop_size: str = "100") -> str:
    """Run platypus NSGA-II on the 3-objective integer workforce problem.

    Returns:
        {"status": "OK", "n_points": int, "algorithm": "platypus-NSGA-II", "pareto_front": [
            {"xD": int, "xE": int, "xN": int, "cost": float, "quality": float, "risk": float}
        ]}

    Requires: pip install platypus-opt
    """
    from platypus import NSGAII, Problem, Integer, nondominated

    try:
        data = json.loads(_strip_fences(problem_json))
    except Exception as e:
        return json.dumps({"status": "PARSE_ERROR", "error": str(e)})

    shifts = data.get("shifts", [])
    total_min = int(data.get("total_min", 30))

    if len(shifts) < 2:
        return json.dumps({"status": "INVALID_INPUT", "error": "need at least 2 shifts"})

    costs_list = [s["cost"] for s in shifts]
    qualities_list = [s["quality"] for s in shifts]
    risks_list = [s["risk"] for s in shifts]

    def evaluate(variables):
        xs = [int(v) for v in variables]
        total = sum(xs)
        cost_v = sum(xs[i] * costs_list[i] for i in range(len(xs)))
        quality_v = -(sum(xs[i] * qualities_list[i] for i in range(len(xs))) / total)  # negate to minimize
        risk_v = sum(xs[i] * risks_list[i] for i in range(len(xs))) / total
        return [cost_v, quality_v, risk_v], [total - total_min]  # constraint >= 0

    try:
        n_var = len(shifts)
        problem = Problem(n_var, 3, 1)
        problem.types[:] = [Integer(s["min"], s["max"]) for s in shifts]
        problem.constraints[:] = ">=0"
        problem.function = evaluate

        random.seed(42)
        algorithm = NSGAII(problem, population_size=int(pop_size))
        algorithm.run(int(n_eval))

        front = nondominated(algorithm.result)

        # Decode binary-encoded integer variables and deduplicate
        pareto_points = []
        seen = set()
        for sol in front:
            if sol.feasible:
                xs = [problem.types[i].decode(sol.variables[i]) for i in range(n_var)]
                key = tuple(xs)
                if key in seen:
                    continue
                seen.add(key)
                total = sum(xs)
                if total < total_min:
                    continue
                cost_val = float(sum(xs[i] * costs_list[i] for i in range(n_var)))
                quality_val = float(sum(xs[i] * qualities_list[i] for i in range(n_var))) / total
                risk_val = float(sum(xs[i] * risks_list[i] for i in range(n_var))) / total
                point = {
                    "cost": round(cost_val, 2),
                    "quality": round(quality_val, 6),
                    "risk": round(risk_val, 6),
                }
                for i, s in enumerate(shifts):
                    point[f"x{s['name'][0]}"] = xs[i]
                pareto_points.append(point)

        pareto_points.sort(key=lambda p: p["cost"])

        return json.dumps({
            "status": "OK",
            "algorithm": "platypus-NSGA-II",
            "n_points": len(pareto_points),
            "pareto_front": pareto_points,
        })

    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e)})


@spl_tool
def is_pareto_feasible(front_json: str) -> bool:
    """ASSERT gate: True if status==OK and n_points >= 3."""
    try:
        data = json.loads(front_json)
        return data.get("status") == "OK" and int(data.get("n_points", 0)) >= 3
    except Exception:
        return False


@spl_tool
def format_pareto_surface(front_json: str) -> str:
    """Format Pareto front as markdown table sorted by cost ascending.

    Columns: xD | xE | xN | Cost ($) | Quality | Risk
    """
    try:
        data = json.loads(front_json)
        points = data.get("pareto_front", [])
        algo = data.get("algorithm", "platypus-NSGA-II")
        if not points:
            return "No Pareto-optimal points found."

        shift_keys = sorted(k for k in points[0].keys() if k.startswith("x") and len(k) == 2)
        header_parts = " | ".join(shift_keys)
        lines = [
            f"| {header_parts} | Cost ($) | Quality | Risk | Algorithm |",
            "|" + "|".join(["---"] * (len(shift_keys) + 4)) + "|",
        ]

        costs = [p["cost"] for p in points]
        qualities = [p["quality"] for p in points]
        risks = [p["risk"] for p in points]

        for pt in points:
            shift_vals = " | ".join(str(pt.get(k, 0)) for k in shift_keys)
            lines.append(
                f"| {shift_vals} | {pt['cost']:,.0f} | {pt['quality']:.4f} | {pt['risk']:.4f} | {algo} |"
            )

        lines.append("")
        lines.append(
            f"**Cost:** ${min(costs):,.0f} – ${max(costs):,.0f}  |  "
            f"**Quality:** {min(qualities):.4f} – {max(qualities):.4f}  |  "
            f"**Risk:** {min(risks):.4f} – {max(risks):.4f}"
        )
        return "\n".join(lines)

    except Exception as e:
        return f"Could not format Pareto surface: {e}"


@spl_tool
def compute_utopia_anchors(problem_json: str) -> str:
    """Compute per-objective optimal solutions via PuLP (continuous relaxation).

    Returns:
        {"min_cost": {...}, "max_quality": {...}, "min_risk": {...}}
    """
    import pulp

    try:
        data = json.loads(_strip_fences(problem_json))
    except Exception as e:
        return json.dumps({"error": f"parse error: {e}"})

    shifts = data.get("shifts", [])
    total_min = float(data.get("total_min", 30))
    names = [s["name"] for s in shifts]

    if len(shifts) < 2:
        return json.dumps({"error": "need at least 2 shifts"})

    costs = {s["name"]: float(s["cost"]) for s in shifts}
    qualities = {s["name"]: float(s["quality"]) for s in shifts}
    risks = {s["name"]: float(s["risk"]) for s in shifts}
    mins = {s["name"]: float(s["min"]) for s in shifts}
    maxs = {s["name"]: float(s["max"]) for s in shifts}

    def make_vars(prob):
        return {n: pulp.LpVariable(f"x_{n}", lowBound=mins[n], upBound=maxs[n]) for n in names}

    def calc_metrics(x_vals, total):
        cost_v = sum(costs[n] * x_vals[n] for n in names)
        quality_v = sum(qualities[n] * x_vals[n] for n in names) / total if total > 0 else 0.0
        risk_v = sum(risks[n] * x_vals[n] for n in names) / total if total > 0 else 0.0
        return cost_v, quality_v, risk_v

    anchors = {}
    for label, sense, objective_fn in [
        ("min_cost", pulp.LpMinimize, lambda x: pulp.lpSum(costs[n] * x[n] for n in names)),
        ("max_quality", pulp.LpMinimize, lambda x: -pulp.lpSum(qualities[n] * x[n] for n in names)),
        ("min_risk", pulp.LpMinimize, lambda x: pulp.lpSum(risks[n] * x[n] for n in names)),
    ]:
        try:
            prob = pulp.LpProblem(label, sense)
            x = make_vars(prob)
            prob += objective_fn(x)
            prob += pulp.lpSum(x[n] for n in names) >= total_min
            prob.solve(pulp.PULP_CBC_CMD(msg=False))
            x_vals = {n: pulp.value(x[n]) or 0.0 for n in names}
            total = sum(x_vals.values())
            cost_v, quality_v, risk_v = calc_metrics(x_vals, total)
            anchor = {"cost": round(cost_v, 2), "quality": round(quality_v, 6), "risk": round(risk_v, 6)}
            for name in names:
                anchor[f"x{name[0]}"] = round(float(x_vals[name]), 2)
            anchors[label] = anchor
        except Exception as e:
            anchors[label] = {"error": str(e)}

    return json.dumps(anchors)


@spl_tool
def verify_workforce_off(problem_json: str, solution_json: str) -> str:
    """Verify LLM-proposed schedule: integer feasibility, bounds, total, cost/quality/risk.

    Returns {"verdict": "PASS"/"FAIL"/"PARTIAL", "notes": str}
    """
    try:
        problem = json.loads(_strip_fences(problem_json))
        sol = json.loads(_strip_fences(solution_json))
    except Exception as e:
        return json.dumps({"verdict": "FAIL", "notes": f"parse error: {e}"})

    shifts = problem.get("shifts", [])
    total_min = int(problem.get("total_min", 30))
    shift_map = {s["name"]: s for s in shifts}
    notes = []
    ok = True
    partial = False

    x_vals = {}
    for s in shifts:
        key = f"x{s['name'][0]}"
        val = sol.get(key)
        if val is None:
            notes.append(f"missing {key}")
            ok = False
            x_vals[s["name"]] = 0
            continue
        try:
            float_val = float(val)
            int_val = int(round(float_val))
            if abs(float_val - int_val) > 0.01:
                notes.append(f"{key}={val} not integer")
                partial = True
            x_vals[s["name"]] = int_val
        except Exception:
            notes.append(f"{key} not numeric: {val}")
            ok = False
            x_vals[s["name"]] = 0

    for s in shifts:
        v = x_vals.get(s["name"], 0)
        if v < s["min"] or v > s["max"]:
            notes.append(f"x{s['name'][0]}={v} out of bounds [{s['min']}, {s['max']}]")
            ok = False

    total = sum(x_vals.values())
    if total < total_min:
        notes.append(f"total staff {total} < minimum {total_min}")
        ok = False

    recomp_cost = recomp_quality = recomp_risk = None
    if total > 0:
        recomp_cost = sum(shift_map[n]["cost"] * v for n, v in x_vals.items() if n in shift_map)
        recomp_quality = sum(shift_map[n]["quality"] * v for n, v in x_vals.items() if n in shift_map) / total
        recomp_risk = sum(shift_map[n]["risk"] * v for n, v in x_vals.items() if n in shift_map) / total
        if sol.get("cost") is not None and abs(float(sol["cost"]) - recomp_cost) > 5.0:
            notes.append(f"cost mismatch: claimed={float(sol['cost']):.0f}, actual={recomp_cost:.0f}")
            ok = False
        if sol.get("quality") is not None and abs(float(sol["quality"]) - recomp_quality) > 0.01:
            notes.append(f"quality mismatch: claimed={float(sol['quality']):.4f}, actual={recomp_quality:.4f}")
            partial = True
        if sol.get("risk") is not None and abs(float(sol["risk"]) - recomp_risk) > 0.01:
            notes.append(f"risk mismatch: claimed={float(sol['risk']):.4f}, actual={recomp_risk:.4f}")
            partial = True

    verdict = "PASS" if ok and not partial else ("PARTIAL" if partial and ok else "FAIL")
    return json.dumps({
        "verdict": verdict,
        "total_staff": total,
        "recomputed_cost": round(recomp_cost, 2) if recomp_cost is not None else None,
        "recomputed_quality": round(recomp_quality, 4) if recomp_quality is not None else None,
        "recomputed_risk": round(recomp_risk, 4) if recomp_risk is not None else None,
        "notes": "; ".join(notes) if notes else "all checks passed",
    })




@spl_tool
def format_report_solver_on(problem: str, anchors_json: str, n_points_str: str, surface_table: str, interpretation: str, llm_calls: str) -> str:
    return f"""=== Platypus MOEA Workforce Scheduling (r121) | solver=ON ===

Problem:
{problem}

Utopia Anchors (per-objective best):
{anchors_json}

Pareto Surface ({n_points_str} non-dominated points):
{surface_table}

Interpretation:
{interpretation}

LLM calls: {llm_calls}"""


@spl_tool
def format_report_solver_off(problem: str, anchors_json: str, schedule_text: str, solution_json: str, verify_result: str, llm_calls: str) -> str:
    return f"""=== Platypus MOEA Workforce Scheduling (r121) | solver=OFF ===

Problem:
{problem}

Utopia Anchors (reference):
{anchors_json}

LLM Proposed Schedule:
{schedule_text}

Extracted Schedule (JSON):
{solution_json}

Verification:
{verify_result}

LLM calls: {llm_calls}"""

