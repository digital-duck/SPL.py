"""Recipe 108 — Robust Supply Chain MILP (python-mip).

Two-stage stochastic MILP:
  Stage 1 (now):    binary build-vs-lease capacity decision
  Stage 2 (later):  production + emergency sourcing for each demand scenario

The key story: naive expected-demand heuristic recommends BUILD,
but the MILP finds LEASE is cheaper once all scenarios are priced.
"""

import json


_DEFAULT_B5 = {
    "scenarios": [
        {"name": "Low",    "probability": 0.30, "demand": 100},
        {"name": "Normal", "probability": 0.50, "demand": 200},
        {"name": "High",   "probability": 0.20, "demand": 300},
    ],
    "capacity_own":   300,
    "capacity_lease": 150,
    "cost_build":    4000,
    "cost_produce":     8,
    "cost_emergency":  60,
}


def extract_robust_problem(problem_text: str) -> str:
    """Parse stochastic capacity problem into JSON.
    Falls back to default B5 if parsing fails."""
    import re

    text = problem_text.strip()

    # Try direct JSON passthrough
    try:
        parsed = json.loads(text)
        if "scenarios" in parsed:
            return json.dumps(parsed)
    except Exception:
        pass

    # Regex extraction (best-effort)
    try:
        scenarios = []
        # Match patterns like "Low demand 100 units (30% chance)" or "Low: 100 (0.3)"
        for m in re.finditer(
            r"(low|normal|medium|high|surge)\D{0,30}?(\d+)\s*units?\D{0,20}?"
            r"(\d+(?:\.\d+)?)\s*%",
            text, re.IGNORECASE
        ):
            name, demand, prob = m.group(1).capitalize(), float(m.group(2)), float(m.group(3)) / 100
            scenarios.append({"name": name, "probability": prob, "demand": demand})

        cap_own_m   = re.search(r"(?:own|build|factory)\D{0,20}?(\d+)\s*units?", text, re.I)
        cap_lease_m = re.search(r"(?:lease|rent)\D{0,20}?(\d+)\s*units?", text, re.I)
        cost_build_m   = re.search(r"(?:build|one.time|fixed)\D{0,20}?\$?([\d,]+)", text, re.I)
        cost_produce_m = re.search(r"produc\w+\D{0,10}?\$?(\d+)\s*/\s*unit", text, re.I)
        cost_emerg_m   = re.search(r"(?:emergency|urgent|spot)\D{0,15}?\$?(\d+)\s*/\s*unit", text, re.I)

        if scenarios and cap_own_m and cost_build_m:
            return json.dumps({
                "scenarios":       scenarios,
                "capacity_own":    float(cap_own_m.group(1)),
                "capacity_lease":  float(cap_lease_m.group(1)) if cap_lease_m else float(cap_own_m.group(1)) * 0.5,
                "cost_build":      float(cost_build_m.group(1).replace(",", "")),
                "cost_produce":    float(cost_produce_m.group(1)) if cost_produce_m else 8.0,
                "cost_emergency":  float(cost_emerg_m.group(1)) if cost_emerg_m else 60.0,
            })
    except Exception:
        pass

    return json.dumps(_DEFAULT_B5)


def solve_robust_milp(problem_json: str) -> str:
    """Two-stage stochastic MILP via python-mip.

    Stage 1: y ∈ {0,1} — build own factory (y=1) or lease (y=0)
    Stage 2: for each scenario s — x_s (own/leased production), z_s (emergency)

    Objective: minimize cost_build·y + Σ_s prob_s·(cost_prod·x_s + cost_emerg·z_s)

    Requires: pip install python-mip
    """
    import mip
    from mip import Model, xsum, minimize, BINARY, CONTINUOUS, OptimizationStatus

    try:
        data = json.loads(problem_json)
    except Exception as e:
        return json.dumps({"status": "PARSE_ERROR", "error": str(e)})

    scenarios    = data["scenarios"]
    cap_own      = float(data["capacity_own"])
    cap_lease    = float(data.get("capacity_lease", cap_own * 0.5))
    cost_build   = float(data["cost_build"])
    cost_produce = float(data["cost_produce"])
    cost_emerg   = float(data["cost_emergency"])

    m = Model("robust_supply")
    m.verbose = 0

    # Stage-1 variable
    y = m.add_var(name="build", var_type=BINARY)

    # Stage-2 variables (one pair per scenario)
    x = [m.add_var(name=f"produce_s{i}", lb=0, ub=cap_own, var_type=CONTINUOUS)
         for i in range(len(scenarios))]
    z = [m.add_var(name=f"emergency_s{i}", lb=0, var_type=CONTINUOUS)
         for i in range(len(scenarios))]

    # Objective
    m.objective = minimize(
        cost_build * y
        + xsum(s["probability"] * (cost_produce * x[i] + cost_emerg * z[i])
               for i, s in enumerate(scenarios))
    )

    # Scenario constraints
    for i, s in enumerate(scenarios):
        # Capacity depends on build decision:  x_s ≤ cap_own·y + cap_lease·(1−y)
        m += x[i] <= cap_own * y + cap_lease * (1 - y), f"cap_s{i}"
        # Demand must be met
        m += x[i] + z[i] >= s["demand"], f"demand_s{i}"

    m.optimize()

    if m.status == OptimizationStatus.OPTIMAL:
        build_flag = int(round(float(y.x or 0)))
        plans = []
        for i, s in enumerate(scenarios):
            prod  = float(x[i].x or 0)
            emerg = float(z[i].x or 0)
            sc_cost = cost_produce * prod + cost_emerg * emerg
            plans.append({
                "scenario":      s["name"],
                "probability":   s["probability"],
                "demand":        s["demand"],
                "production":    round(prod, 2),
                "emergency":     round(emerg, 2),
                "scenario_cost": round(sc_cost, 2),
            })
        return json.dumps({
            "status":        "OPTIMAL",
            "build_factory": build_flag,
            "capacity_used": cap_own if build_flag else cap_lease,
            "fixed_cost":    cost_build * build_flag,
            "expected_op_cost": round(
                sum(p["probability"] * p["scenario_cost"] for p in plans), 2),
            "expected_cost": round(float(m.objective_value), 2),
            "scenario_plans": plans,
            "objective":     round(float(m.objective_value), 2),
        })
    else:
        return json.dumps({"status": m.status.name, "objective": None})


def is_optimal(solution_json: str) -> bool:
    """ASSERT gate: True when python-mip reports OPTIMAL."""
    try:
        return json.loads(solution_json).get("status") == "OPTIMAL"
    except Exception:
        return False


def format_scenario_report(solution_json: str) -> str:
    """Format scenario plans as a markdown table."""
    try:
        data   = json.loads(solution_json)
        plans  = data.get("scenario_plans", [])
        build  = data.get("build_factory", "?")
        cap    = data.get("capacity_used", "?")
        fixed  = data.get("fixed_cost", 0)
        exp_op = data.get("expected_op_cost", "?")
        exp    = data.get("expected_cost", "?")

        decision = f"**Build own factory** (capacity {cap} units, fixed cost ${fixed:,.0f})" \
                   if build else f"**Lease facility** (capacity {cap} units, no fixed cost)"

        lines = [
            f"Decision: {decision}",
            "",
            "| Scenario | Prob | Demand | Own/Lease prod | Emergency | Scenario cost |",
            "|---|---|---|---|---|---|",
        ]
        for p in plans:
            lines.append(
                f"| {p['scenario']} | {p['probability']:.0%} | {p['demand']:.0f} |"
                f" {p['production']:.0f} | {p['emergency']:.0f} |"
                f" ${p['scenario_cost']:,.0f} |"
            )
        lines += [
            "",
            f"**Fixed cost:** ${fixed:,.0f}  ",
            f"**Expected operational cost:** ${exp_op:,.0f}  ",
            f"**Total expected cost:** ${exp:,.0f}",
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"Error formatting report: {e}"


def solve_naive_heuristic(problem_json: str) -> str:
    """Solver=OFF baseline: use expected demand to make the build decision.

    This is the heuristic a non-expert might apply — it often gives the
    wrong answer because it ignores the asymmetry between scenarios.
    """
    try:
        data = json.loads(problem_json)
    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e)})

    scenarios    = data["scenarios"]
    cap_own      = float(data["capacity_own"])
    cap_lease    = float(data.get("capacity_lease", cap_own * 0.5))
    cost_build   = float(data["cost_build"])
    cost_produce = float(data["cost_produce"])
    cost_emerg   = float(data["cost_emergency"])

    exp_demand = sum(s["probability"] * s["demand"] for s in scenarios)

    # Naive rule: build if expected demand exceeds lease capacity
    build = 1 if exp_demand > cap_lease else 0
    cap   = cap_own if build else cap_lease

    plans = []
    for s in scenarios:
        prod  = min(cap, s["demand"])
        emerg = max(0.0, s["demand"] - prod)
        sc_cost = cost_produce * prod + cost_emerg * emerg
        plans.append({
            "scenario":      s["name"],
            "probability":   s["probability"],
            "demand":        s["demand"],
            "production":    round(prod, 2),
            "emergency":     round(emerg, 2),
            "scenario_cost": round(sc_cost, 2),
        })

    fixed  = cost_build * build
    exp_op = sum(p["probability"] * p["scenario_cost"] for p in plans)
    return json.dumps({
        "status":           "HEURISTIC",
        "build_factory":    build,
        "capacity_used":    cap,
        "fixed_cost":       fixed,
        "expected_op_cost": round(exp_op, 2),
        "expected_cost":    round(fixed + exp_op, 2),
        "expected_demand":  round(exp_demand, 1),
        "scenario_plans":   plans,
        "objective":        round(fixed + exp_op, 2),
    })


def verify_robust_off(problem_json: str, solution_json: str) -> str:
    """Verify that the heuristic solution satisfies all scenario constraints."""
    try:
        data = json.loads(problem_json)
        sol  = json.loads(solution_json)
    except Exception as e:
        return json.dumps({"verdict": "ERROR", "error": str(e)})

    cap_own   = float(data["capacity_own"])
    cap_lease = float(data.get("capacity_lease", cap_own * 0.5))
    build     = sol.get("build_factory", 0)
    capacity  = cap_own if build else cap_lease
    plans     = sol.get("scenario_plans", [])

    violations = []
    for p in plans:
        prod  = float(p.get("production", 0))
        emerg = float(p.get("emergency", 0))
        demand = float(p.get("demand", 0))
        if prod > capacity + 1e-6:
            violations.append(
                f"{p['scenario']}: production {prod:.1f} > capacity {capacity:.1f}")
        if prod + emerg < demand - 1e-6:
            violations.append(
                f"{p['scenario']}: supply {prod+emerg:.1f} < demand {demand:.1f}")

    if violations:
        return json.dumps({"verdict": "FAIL", "notes": "; ".join(violations)})
    return json.dumps({"verdict": "PASS",
                       "notes": f"All {len(plans)} scenario constraints satisfied"})


def json_get_field(data_json: str, field: str) -> str:
    """Extract a field from JSON as string."""
    try:
        v = json.loads(data_json).get(field)
        return str(v) if v is not None else ""
    except Exception:
        return ""
