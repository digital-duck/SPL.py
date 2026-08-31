"""
Recipe 100 — Supply sourcing: multi-objective Pareto optimization (cost vs. fill rate).
TOOL_APIs called from supply_sourcing.spl.
"""

import json


# ── Default B1 problem ────────────────────────────────────────────────────────

_DEFAULT_B1 = {
    "suppliers": [
        {"name": "S1", "cost": 10.0, "fill_rate": 0.95, "capacity": 400.0},
        {"name": "S2", "cost":  7.0, "fill_rate": 0.80, "capacity": 500.0},
        {"name": "S3", "cost":  5.0, "fill_rate": 0.60, "capacity": 400.0},
    ],
    "demand": 1000.0,
}


# ── Tool functions ────────────────────────────────────────────────────────────

def extract_sourcing_problem(problem_text: str) -> str:
    """Parse supplier/demand data into JSON.

    Returns:
        {"suppliers": [{"name": str, "cost": float, "fill_rate": float, "capacity": float}], "demand": float}

    If the input is already valid JSON with the expected structure, normalise and return it.
    Otherwise attempt keyword-based extraction from plain text.
    If both fail, return the default B1 problem as JSON.
    """
    # Try: already a valid JSON blob
    try:
        data = json.loads(problem_text)
        suppliers = data.get("suppliers", [])
        demand = float(data.get("demand", 0))
        if suppliers and demand > 0:
            normalised = [
                {
                    "name": str(s.get("name", f"S{i+1}")),
                    "cost": float(s["cost"]),
                    "fill_rate": float(s["fill_rate"]),
                    "capacity": float(s["capacity"]),
                }
                for i, s in enumerate(suppliers)
            ]
            return json.dumps({"suppliers": normalised, "demand": demand})
    except Exception:
        pass

    # Try: lightweight keyword extraction from structured English
    try:
        import re

        demand_match = re.search(r"(\d[\d,]*)\s*units?\s*(?:demanded|needed|required)", problem_text, re.I)
        demand = float(demand_match.group(1).replace(",", "")) if demand_match else 0.0

        # Look for patterns like "S1: $10/unit, 95% fill rate, capacity 400"
        supplier_pattern = re.compile(
            r"(S\d+|supplier\s*\d+)[^.]*?\$\s*([\d.]+)\s*/\s*unit[^.]*?"
            r"([\d.]+)\s*%\s*fill[^.]*?capacity\s*([\d,]+)",
            re.I,
        )
        found = []
        for m in supplier_pattern.finditer(problem_text):
            found.append({
                "name": m.group(1).upper().replace(" ", ""),
                "cost": float(m.group(2)),
                "fill_rate": float(m.group(3)) / 100.0,
                "capacity": float(m.group(4).replace(",", "")),
            })

        if found and demand > 0:
            return json.dumps({"suppliers": found, "demand": demand})
    except Exception:
        pass

    # Fallback: return the default B1 problem
    return json.dumps(_DEFAULT_B1)


def sweep_pareto_front(problem_json: str, n_points: int = 8) -> str:
    """ε-constraint sweep: for each fill_rate threshold, minimize cost via PuLP.

    Returns:
        {"status": "OK", "n_points": int, "pareto_front":
            [{"cost": float, "fill_rate": float, "allocation": {name: amount}}]}

    Dominated points are stripped before returning.
    Requires: pip install pulp
    """
    import pulp  # deferred import — not at module level

    try:
        data = json.loads(problem_json)
    except Exception as e:
        return json.dumps({"status": "PARSE_ERROR", "error": str(e)})

    suppliers = data.get("suppliers", [])
    demand = float(data.get("demand", 1000))

    if not suppliers:
        return json.dumps({"status": "INVALID_INPUT", "error": "no suppliers"})

    names = [s["name"] for s in suppliers]
    costs = {s["name"]: float(s["cost"]) for s in suppliers}
    fill_rates = {s["name"]: float(s["fill_rate"]) for s in suppliers}
    capacities = {s["name"]: float(s["capacity"]) for s in suppliers}

    # Compute anchor fill-rate bounds
    # Min fill: allocate cheapest suppliers first
    sorted_by_cost = sorted(names, key=lambda n: costs[n])
    remaining = demand
    min_fill_units = 0.0
    for n in sorted_by_cost:
        alloc = min(remaining, capacities[n])
        min_fill_units += alloc * fill_rates[n]
        remaining -= alloc
        if remaining <= 0:
            break
    min_fill_rate = min_fill_units / demand

    # Max fill: allocate highest fill-rate suppliers first
    sorted_by_fill = sorted(names, key=lambda n: fill_rates[n], reverse=True)
    remaining = demand
    max_fill_units = 0.0
    for n in sorted_by_fill:
        alloc = min(remaining, capacities[n])
        max_fill_units += alloc * fill_rates[n]
        remaining -= alloc
        if remaining <= 0:
            break
    max_fill_rate = max_fill_units / demand

    # Build n_points thresholds from min to max fill_rate
    n_pts = max(2, int(n_points))
    step = (max_fill_rate - min_fill_rate) / max(n_pts - 1, 1)
    thresholds = [min_fill_rate + i * step for i in range(n_pts)]

    raw_points = []
    for threshold in thresholds:
        prob = pulp.LpProblem("supply_cost_min", pulp.LpMinimize)
        x = {n: pulp.LpVariable(f"x_{n}", lowBound=0, upBound=capacities[n]) for n in names}

        # Objective: minimize total cost
        prob += pulp.lpSum(costs[n] * x[n] for n in names)

        # Demand balance
        prob += pulp.lpSum(x[n] for n in names) == demand

        # Fill-rate constraint: blended fill rate >= threshold
        # sum(fill_rate_n * x_n) / demand >= threshold
        prob += pulp.lpSum(fill_rates[n] * x[n] for n in names) >= threshold * demand

        status = prob.solve(pulp.PULP_CBC_CMD(msg=False))

        if pulp.LpStatus[status] not in ("Optimal",):
            continue

        allocation = {n: round(float(pulp.value(x[n]) or 0.0), 2) for n in names}
        total_cost = sum(costs[n] * allocation[n] for n in names)
        blended_fill = sum(fill_rates[n] * allocation[n] for n in names) / demand

        raw_points.append({
            "cost": round(total_cost, 2),
            "fill_rate": round(blended_fill, 6),
            "allocation": allocation,
        })

    if not raw_points:
        return json.dumps({"status": "INFEASIBLE", "n_points": 0, "pareto_front": []})

    # Strip dominated points: A dominates B if A.cost <= B.cost AND A.fill >= B.fill
    # (strictly better on at least one dimension)
    def is_dominated(p, candidates):
        for q in candidates:
            if q is p:
                continue
            if q["cost"] <= p["cost"] and q["fill_rate"] >= p["fill_rate"]:
                if q["cost"] < p["cost"] or q["fill_rate"] > p["fill_rate"]:
                    return True
        return False

    pareto = [p for p in raw_points if not is_dominated(p, raw_points)]
    pareto.sort(key=lambda p: p["cost"])

    return json.dumps({
        "status": "OK",
        "n_points": len(pareto),
        "pareto_front": pareto,
    })


def is_pareto_feasible(front_json: str) -> bool:
    """ASSERT gate: True if front has status==OK and n_points >= 2."""
    try:
        data = json.loads(front_json)
        return data.get("status") == "OK" and int(data.get("n_points", 0)) >= 2
    except Exception:
        return False


def format_pareto_table(front_json: str) -> str:
    """Format Pareto front as a markdown table: Cost ($) | Fill rate (%) | Allocation."""
    try:
        data = json.loads(front_json)
        points = data.get("pareto_front", [])
        if not points:
            return "No Pareto-optimal points found."

        # Collect supplier names from first point
        sample_alloc = points[0].get("allocation", {})
        supplier_names = sorted(sample_alloc.keys())
        alloc_header = "  |  ".join(supplier_names)

        lines = [
            f"| Cost ($) | Fill rate (%) | {alloc_header} |",
            "|---|---|" + "|".join(["---"] * len(supplier_names)) + "|",
        ]
        for pt in points:
            cost = f"{pt['cost']:,.2f}"
            fill = f"{pt['fill_rate'] * 100:.1f}"
            alloc_vals = "  |  ".join(
                str(int(pt["allocation"].get(n, 0))) for n in supplier_names
            )
            lines.append(f"| {cost} | {fill} | {alloc_vals} |")

        return "\n".join(lines)
    except Exception as e:
        return f"Could not format Pareto table: {e}"


def verify_sourcing_off(problem_json: str, solution_json: str) -> str:
    """Verify LLM-proposed allocation arithmetic.

    Checks:
    - demand balance: sum(allocation) == demand (±1)
    - capacity: each allocation <= supplier capacity
    - cost: recompute from allocation and compare to claimed
    - fill_rate: recompute and compare to claimed

    Returns {"verdict": "PASS"/"FAIL", "notes": str}
    """
    try:
        problem = json.loads(problem_json)
        sol = json.loads(solution_json)
    except Exception as e:
        return json.dumps({"verdict": "FAIL", "notes": f"parse error: {e}"})

    suppliers = {s["name"]: s for s in problem.get("suppliers", [])}
    demand = float(problem.get("demand", 1000))
    allocation = sol.get("allocation", {})

    notes = []
    ok = True

    # Demand balance
    total_alloc = sum(float(v) for v in allocation.values())
    if abs(total_alloc - demand) > 1.0:
        notes.append(f"demand balance: allocated {total_alloc:.1f} vs demanded {demand:.1f}")
        ok = False

    # Capacity check
    for name, amount in allocation.items():
        amount = float(amount)
        if name in suppliers:
            cap = float(suppliers[name]["capacity"])
            if amount > cap + 0.5:
                notes.append(f"{name}: allocated {amount:.1f} exceeds capacity {cap:.1f}")
                ok = False

    # Recompute cost
    recomputed_cost = sum(
        float(suppliers[n]["cost"]) * float(v)
        for n, v in allocation.items()
        if n in suppliers
    )
    claimed_cost = sol.get("cost")
    if claimed_cost is not None:
        if abs(float(claimed_cost) - recomputed_cost) > 10.0:
            notes.append(
                f"cost mismatch: claimed={float(claimed_cost):.2f}, recomputed={recomputed_cost:.2f}"
            )
            ok = False

    # Recompute fill_rate
    recomputed_fill = (
        sum(
            float(suppliers[n]["fill_rate"]) * float(v)
            for n, v in allocation.items()
            if n in suppliers
        )
        / demand
    )
    claimed_fill = sol.get("fill_rate")
    if claimed_fill is not None:
        if abs(float(claimed_fill) - recomputed_fill) > 0.02:
            notes.append(
                f"fill_rate mismatch: claimed={float(claimed_fill):.4f}, recomputed={recomputed_fill:.4f}"
            )
            ok = False

    return json.dumps({
        "verdict": "PASS" if ok else "FAIL",
        "recomputed_cost": round(recomputed_cost, 2),
        "recomputed_fill_rate": round(recomputed_fill, 4),
        "notes": "; ".join(notes) if notes else "all checks passed",
    })


def json_get_field(data_json: str, field: str) -> str:
    """Extract a field from JSON as string."""
    try:
        data = json.loads(data_json)
        return str(data.get(field, ""))
    except Exception:
        return ""
