"""
Recipe 101 — Production Sustainability: multi-objective Pareto optimization.
Maximize profit AND minimize carbon footprint via weighted-sum scalarization (PuLP).
TOOL_APIs called from production_sustainability.spl.
"""

import json


def extract_production_problem(problem_text: str) -> str:
    """
    Parse product/resource data from problem_text into JSON.
    Returns:
      {"products": [{"name": str, "profit": float, "carbon": float,
                     "labor": float, "material": float}],
       "resources": {"labor": float, "material": float}}
    Falls back to the canonical B3 problem on parse failure.
    """
    DEFAULT = {
        "products": [
            {"name": "A", "profit": 10.0, "carbon": 3.0, "labor": 2.0, "material": 3.0},
            {"name": "B", "profit":  6.0, "carbon": 1.0, "labor": 1.0, "material": 2.0},
        ],
        "resources": {"labor": 20.0, "material": 30.0},
    }

    try:
        text = problem_text.lower()

        # ── resource extraction ──────────────────────────────────────
        import re
        labor_m    = re.search(r"(\d+(?:\.\d+)?)\s*(?:labor.hours?|hr)", text)
        material_m = re.search(r"(\d+(?:\.\d+)?)\s*kg\s*material", text)
        if not labor_m or not material_m:
            return json.dumps(DEFAULT)

        resources = {
            "labor":    float(labor_m.group(1)),
            "material": float(material_m.group(1)),
        }

        # ── product extraction ──────────────────────────────────────
        # Look for lines/sentences containing "A:" or "B:" style patterns
        product_pattern = re.findall(
            r"product\s+([A-Za-z])[^.;]*"
            r"\$(\d+(?:\.\d+)?)\s*profit[^.;]*"
            r"(\d+(?:\.\d+)?)\s*kg\s*co[₂2][^.;]*"
            r"(\d+(?:\.\d+)?)\s*hr[^.;]*"
            r"(\d+(?:\.\d+)?)\s*kg\s*material",
            text,
        )

        if len(product_pattern) < 2:
            return json.dumps(DEFAULT)

        products = []
        for name, profit, carbon, labor, material in product_pattern:
            products.append({
                "name":     name.upper(),
                "profit":   float(profit),
                "carbon":   float(carbon),
                "labor":    float(labor),
                "material": float(material),
            })

        return json.dumps({"products": products, "resources": resources})

    except Exception:
        return json.dumps(DEFAULT)


def sweep_pareto_scalarization(problem_json: str, n_points: int = 10) -> str:
    """
    Weighted-sum scalarization: maximize λ·profit_norm - (1-λ)·carbon_norm
    Sweep λ from 0.0 to 1.0 in n_points steps.

    Anchor values (B3):
      max_profit = 100  (x=10, y=0)
      max_carbon  = 30  (x=10, y=0)
      min_carbon  = 15  (x=0,  y=15)

    Normalization: profit_norm = profit/100, carbon_norm = carbon/30

    Returns:
      {"status": "OK", "n_points": int,
       "pareto_front": [{"profit": float, "carbon": float, "x": float, "y": float}]}
    """
    import pulp

    MAX_PROFIT = 100.0   # anchor: x=10, y=0
    MAX_CARBON =  30.0   # anchor: x=10, y=0

    try:
        data = json.loads(problem_json)
        products  = data["products"]
        resources = data["resources"]

        labor_cap    = resources["labor"]
        material_cap = resources["material"]

        # Expect exactly 2 products in column order [A, B]
        pA = products[0]
        pB = products[1]

        raw_points: list[dict] = []

        # n_points steps: λ = 0.0, 1/(n-1), ..., 1.0
        n = max(int(n_points), 2)
        lambdas = [i / (n - 1) for i in range(n)]

        for lam in lambdas:
            prob = pulp.LpProblem("pareto_step", pulp.LpMaximize)
            x = pulp.LpVariable("x", lowBound=0)   # Product A units
            y = pulp.LpVariable("y", lowBound=0)   # Product B units

            profit = pA["profit"] * x + pB["profit"] * y
            carbon = pA["carbon"] * x + pB["carbon"] * y

            profit_norm = profit / MAX_PROFIT
            carbon_norm = carbon / MAX_CARBON

            # Maximize λ·profit_norm - (1-λ)·carbon_norm
            prob += lam * profit_norm - (1 - lam) * carbon_norm

            # Resource constraints
            prob += pA["labor"]    * x + pB["labor"]    * y <= labor_cap
            prob += pA["material"] * x + pB["material"] * y <= material_cap

            solver = pulp.PULP_CBC_CMD(msg=False)
            prob.solve(solver)

            if pulp.LpStatus[prob.status] == "Optimal":
                xv_raw = pulp.value(x); xv = max(0.0, xv_raw if isinstance(xv_raw, float) else 0.0)
                yv_raw = pulp.value(y); yv = max(0.0, yv_raw if isinstance(yv_raw, float) else 0.0)
                p  = round(pA["profit"] * xv + pB["profit"] * yv, 4)
                c  = round(pA["carbon"] * xv + pB["carbon"] * yv, 4)
                raw_points.append({"profit": p, "carbon": c,
                                   "x": round(xv, 4), "y": round(yv, 4)})

        # Strip dominated points: keep point P if no other Q has Q.profit >= P.profit AND Q.carbon <= P.carbon (strictly better on at least one)
        def dominates(q: dict, p: dict) -> bool:
            return (q["profit"] >= p["profit"] and q["carbon"] <= p["carbon"]
                    and (q["profit"] > p["profit"] or q["carbon"] < p["carbon"]))

        pareto: list[dict] = []
        for p in raw_points:
            if not any(dominates(q, p) for q in raw_points if q is not p):
                # Deduplicate by (profit, carbon) rounded to 2 dp
                key = (round(p["profit"], 2), round(p["carbon"], 2))
                if not any((round(q["profit"], 2), round(q["carbon"], 2)) == key
                           for q in pareto):
                    pareto.append(p)

        # Sort by descending profit
        pareto.sort(key=lambda p: -p["profit"])

        return json.dumps({"status": "OK", "n_points": len(pareto), "pareto_front": pareto})

    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e), "n_points": 0, "pareto_front": []})


def is_pareto_feasible(front_json: str) -> bool:
    """ASSERT gate: True when status==OK and at least 2 Pareto points exist."""
    try:
        data = json.loads(front_json)
        return data.get("status") == "OK" and data.get("n_points", 0) >= 2
    except Exception:
        return False


def format_pareto_table(front_json: str) -> str:
    """Format Pareto front as a markdown table."""
    try:
        data  = json.loads(front_json)
        front = data.get("pareto_front", [])
        if not front:
            return "(no Pareto points)"

        header = "| Profit ($) | Carbon (kg) | Product A (units) | Product B (units) |"
        sep    = "|---|---|---|---|"
        rows   = [header, sep]
        for pt in front:
            rows.append(
                f"| {pt['profit']:.1f} | {pt['carbon']:.1f} "
                f"| {pt['x']:.2f} | {pt['y']:.2f} |"
            )
        return "\n".join(rows)
    except Exception as e:
        return f"(table error: {e})"


def verify_production_off(problem_json: str, solution_json: str) -> str:
    """
    Verify LLM-proposed (x, y) against the B3 constraints and claimed objectives.
    Checks: feasibility, profit arithmetic, carbon arithmetic.
    Returns {"verdict": "PASS"/"FAIL", "notes": str}
    """
    TOLS = {"arith": 0.5}   # dollar / kg tolerance

    try:
        prob = json.loads(problem_json)
        sol  = json.loads(solution_json)

        products  = prob["products"]
        resources = prob["resources"]
        pA = products[0]
        pB = products[1]

        x = float(sol.get("x", 0))
        y = float(sol.get("y", 0))
        claimed_profit = float(sol.get("profit", 0))
        claimed_carbon = float(sol.get("carbon", 0))

        notes: list[str] = []
        ok = True

        # Feasibility
        labor_used    = pA["labor"]    * x + pB["labor"]    * y
        material_used = pA["material"] * x + pB["material"] * y
        if labor_used > resources["labor"] + 1e-6:
            notes.append(f"labor violated: {labor_used:.2f} > {resources['labor']}")
            ok = False
        if material_used > resources["material"] + 1e-6:
            notes.append(f"material violated: {material_used:.2f} > {resources['material']}")
            ok = False
        if x < -1e-6 or y < -1e-6:
            notes.append(f"non-negativity violated: x={x}, y={y}")
            ok = False

        # Arithmetic
        actual_profit = pA["profit"] * x + pB["profit"] * y
        actual_carbon = pA["carbon"] * x + pB["carbon"] * y

        if abs(actual_profit - claimed_profit) > TOLS["arith"]:
            notes.append(
                f"profit mismatch: computed={actual_profit:.2f}, claimed={claimed_profit:.2f}"
            )
            ok = False
        if abs(actual_carbon - claimed_carbon) > TOLS["arith"]:
            notes.append(
                f"carbon mismatch: computed={actual_carbon:.2f}, claimed={claimed_carbon:.2f}"
            )
            ok = False

        return json.dumps({
            "verdict": "PASS" if ok else "FAIL",
            "x": x, "y": y,
            "actual_profit": round(actual_profit, 2),
            "actual_carbon": round(actual_carbon, 2),
            "notes": "; ".join(notes) if notes else "all checks passed",
        })

    except Exception as e:
        return json.dumps({"verdict": "FAIL", "notes": f"parse error: {e}"})


def json_get_field(data_json: str, field: str) -> str:
    """Extract a top-level field from a JSON object as a string."""
    try:
        data = json.loads(data_json)
        return str(data.get(field, ""))
    except Exception:
        return ""
