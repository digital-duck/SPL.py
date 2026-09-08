"""Recipe 117 — Two-Stage Stochastic Programming (Pyomo + GLPK).

Solves a two-stage stochastic LP/IP via Pyomo's Extensive Form (EF).
The core pattern: decide NOW (Stage 1) before uncertainty resolves,
then take optimal recourse actions (Stage 2) after observing each scenario.

Default problem: Seasonal inventory stocking (newsvendor extended to 3 scenarios).
  - Stage 1: Order Q units at $5/unit before knowing demand.
  - Stage 2: Per scenario — pay shortage penalty or holding cost.
  - 3 demand scenarios: Pessimistic=100 (p=0.3), Nominal=200 (p=0.5),
                        Optimistic=300 (p=0.2).

LLM baseline: "order the expected demand" → Q=190, E[cost]=$1,409.
Stochastic optimum: Q=200, E[cost]=$1,360 (VSS = $49).
Key insight: asymmetric costs (shortage $15 >> holding $2) mean the
optimal Q lies above the expected demand — ordering the mean is suboptimal.

ASSERT: status == "optimal" (Pyomo solver certified the solution).

Install: pip install pyomo && conda install -c conda-forge glpk
"""

import json


_DEFAULT_PROBLEM = {
    "problem_name": "Seasonal Inventory Stocking",
    "description": (
        "A retailer must order promotional merchandise BEFORE knowing seasonal demand. "
        "Demand depends on economic conditions: low, nominal, or high. "
        "The order decision is made once for the season (Stage 1). "
        "After demand is realized, shortages and excess inventory are handled (Stage 2). "
        "Costs: order=$5/unit, shortage=$15/unit (lost sales + expediting), "
        "holding=$2/unit (storage + obsolescence). "
        "Goal: minimize total expected cost across all demand scenarios."
    ),
    "scenarios": [
        {"name": "pessimistic", "demand": 100, "probability": 0.3},
        {"name": "nominal",     "demand": 200, "probability": 0.5},
        {"name": "optimistic",  "demand": 300, "probability": 0.2},
    ],
    "costs": {
        "order":    5,   # $/unit, paid in Stage 1
        "shortage": 15,  # $/unit unmet demand (Stage 2 recourse)
        "holding":  2,   # $/unit unsold inventory (Stage 2 recourse)
    },
    "capacity": 400,
    "known_optimal_qty": 200,
    "known_optimal_cost": 1360.0,
    "ev_baseline_qty": 190,      # expected demand: 0.3*100 + 0.5*200 + 0.2*300
    "ev_baseline_cost": 1409.0,
    "vss": 49.0,                 # Value of the Stochastic Solution
}


def get_problem_setup() -> str:
    return json.dumps(_DEFAULT_PROBLEM)


def solve_two_stage_sp(problem_json: str) -> str:
    """Formulate and solve the two-stage stochastic program as an Extensive Form.

    The EF duplicates Stage 2 variables for each scenario and optimizes
    jointly, weighted by probability.

    Returns:
      {"status", "order_qty", "expected_cost", "per_scenario", "solver", ...}
    """
    try:
        import pyomo.environ as pyo  # type: ignore[import-untyped]
    except ImportError:
        return json.dumps({"status": "ERROR",
                           "error": "pyomo not installed — run: pip install pyomo"})

    try:
        prob = json.loads(problem_json)
        scenarios = prob["scenarios"]
        c = prob["costs"]
        cap = prob["capacity"]

        model = pyo.ConcreteModel(name="two_stage_inventory")

        # Stage 1: order quantity (integer, bounded by warehouse capacity)
        model.order = pyo.Var(domain=pyo.NonNegativeIntegers, bounds=(0, cap))

        # Stage 2: recourse variables per scenario
        snames = [s["name"] for s in scenarios]
        model.shortage = pyo.Var(snames, domain=pyo.NonNegativeReals)
        model.excess    = pyo.Var(snames, domain=pyo.NonNegativeReals)

        # Objective: E[total cost] = order cost + expected recourse cost
        model.obj = pyo.Objective(
            expr=(
                c["order"] * model.order
                + sum(
                    s["probability"] * (
                        c["shortage"] * model.shortage[s["name"]]
                        + c["holding"]  * model.excess[s["name"]]
                    )
                    for s in scenarios
                )
            ),
            sense=pyo.minimize,
        )

        # Stage 2 balance constraints: shortage + sales = demand; excess = order - sales
        def shortage_rule(m, sname):
            d = next(s["demand"] for s in scenarios if s["name"] == sname)
            return m.shortage[sname] >= d - m.order

        def excess_rule(m, sname):
            d = next(s["demand"] for s in scenarios if s["name"] == sname)
            return m.excess[sname] >= m.order - d

        model.shortage_con = pyo.Constraint(snames, rule=shortage_rule)
        model.excess_con   = pyo.Constraint(snames, rule=excess_rule)

        # Try solvers in priority order
        result = None
        solver_name = None
        for candidate in ("glpk", "cbc", "highs", "appsi_highs"):
            solver = pyo.SolverFactory(candidate)
            if solver.available():
                result = solver.solve(model, tee=False)
                solver_name = candidate
                break

        if result is None:
            return json.dumps({"status": "ERROR",
                               "error": "No LP/MIP solver found. Install glpk: "
                                        "conda install -c conda-forge glpk"})

        term_cond = str(result.solver.termination_condition)
        if "optimal" not in term_cond.lower():
            return json.dumps({"status": "ERROR",
                               "error": f"Solver did not find optimum: {term_cond}"})

        order_qty    = int(round(pyo.value(model.order)))
        expected_cost = round(pyo.value(model.obj), 2)

        per_scenario = []
        for s in scenarios:
            sn  = s["name"]
            d   = s["demand"]
            p   = s["probability"]
            qty = order_qty
            sh  = max(0, d - qty)
            ex  = max(0, qty - d)
            sc  = c["order"] * qty + c["shortage"] * sh + c["holding"] * ex
            per_scenario.append({
                "scenario":    sn,
                "demand":      d,
                "probability": p,
                "order":       qty,
                "shortage":    sh,
                "excess":      ex,
                "scenario_cost": round(sc, 2),
                "weighted_cost": round(p * sc, 2),
            })

        return json.dumps({
            "status":        "optimal",
            "order_qty":     order_qty,
            "expected_cost": expected_cost,
            "per_scenario":  per_scenario,
            "solver":        solver_name,
            "costs":         c,
        })

    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e)})


def compute_ev_baseline(problem_json: str) -> str:
    """Compute the LLM-style EV baseline: order the expected demand.

    EV = Expected Value solution — ignores scenario spread, orders the mean.
    Returns the EV order quantity and its expected cost under all scenarios.
    """
    try:
        prob = json.loads(problem_json)
        scenarios = prob["scenarios"]
        c = prob["costs"]

        ev_qty = round(sum(s["demand"] * s["probability"] for s in scenarios))

        per_scenario = []
        total_cost = c["order"] * ev_qty
        for s in scenarios:
            d  = s["demand"]
            p  = s["probability"]
            sh = max(0, d - ev_qty)
            ex = max(0, ev_qty - d)
            sc = c["order"] * ev_qty + c["shortage"] * sh + c["holding"] * ex
            total_cost += p * (c["shortage"] * sh + c["holding"] * ex)
            per_scenario.append({
                "scenario": s["name"], "demand": d, "probability": p,
                "shortage": sh, "excess": ex, "scenario_cost": round(sc, 2),
                "weighted_cost": round(p * sc, 2),
            })

        return json.dumps({
            "ev_qty":        ev_qty,
            "expected_cost": round(total_cost, 2),
            "per_scenario":  per_scenario,
        })

    except Exception as e:
        return json.dumps({"error": str(e), "ev_qty": 0, "expected_cost": 0.0})


def sp_optimal(result_json: str) -> bool:
    """ASSERT gate: Pyomo solver certified an optimal solution."""
    try:
        return json.loads(result_json).get("status") == "optimal"
    except Exception:
        return False


def solver_enabled(use_solver: str) -> str:
    """Return 'run_solver' or 'run_llm' for unambiguous EVALUATE matching."""
    if use_solver.strip().lower() in ("true", "1", "yes", "on"):
        return "run_solver"
    return "run_llm"


def format_sp_report(result_json: str, baseline_json: str) -> str:
    """Markdown report comparing stochastic optimum vs EV baseline."""
    try:
        r  = json.loads(result_json)
        bl = json.loads(baseline_json)
        c  = r.get("costs", {})
        vss = round(bl["expected_cost"] - r["expected_cost"], 2)

        lines = [
            "## Two-Stage Stochastic Programming — Inventory Stocking",
            "",
            f"**Solver:** Pyomo + {r.get('solver', 'glpk')}  ",
            f"**Status:** {r.get('status', '?')}",
            "",
            "### Stage 1 Decision",
            "",
            "| Method | Order Quantity | Expected Cost | vs. Optimum |",
            "|---|---|---|---|",
            f"| **Pyomo stochastic optimum** | **{r['order_qty']} units** "
            f"| **${r['expected_cost']:,.0f}** | — |",
            f"| EV baseline (order E[demand]) | {bl['ev_qty']} units "
            f"| ${bl['expected_cost']:,.0f} | +${vss:,.0f} worse |",
            "",
            f"> **Value of the Stochastic Solution (VSS) = ${vss:,.0f}**",
            f"> Ordering the expected demand instead of Q* costs ${vss:,.0f} more",
            f"> because the asymmetric penalties (shortage=${c.get('shortage',15)}/unit >> "
            f"holding=${c.get('holding',2)}/unit) push the optimal quantity above the mean.",
            "",
            "### Per-Scenario Breakdown (Stochastic Optimum)",
            "",
            "| Scenario | Demand | Prob | Shortage | Excess | Scenario Cost | Weighted |",
            "|---|---|---|---|---|---|---|",
        ]
        for s in r.get("per_scenario", []):
            lines.append(
                f"| {s['scenario']} | {s['demand']} | {s['probability']:.1f} "
                f"| {s['shortage']} | {s['excess']} "
                f"| ${s['scenario_cost']:,} | ${s['weighted_cost']:,} |"
            )
        lines += [
            "",
            "### Per-Scenario Breakdown (EV Baseline — order expected demand)",
            "",
            "| Scenario | Demand | Prob | Shortage | Excess | Scenario Cost | Weighted |",
            "|---|---|---|---|---|---|---|",
        ]
        for s in bl.get("per_scenario", []):
            lines.append(
                f"| {s['scenario']} | {s['demand']} | {s['probability']:.1f} "
                f"| {s['shortage']} | {s['excess']} "
                f"| ${s['scenario_cost']:,} | ${s['weighted_cost']:,} |"
            )
        lines += [
            "",
            "### Critical Ratio Insight",
            "",
            "The optimal Q* satisfies: **P(demand ≤ Q*) = (c_shortage − c_order) / (c_shortage + c_holding)**",
            f"= ({c.get('shortage',15)} − {c.get('order',5)}) / "
            f"({c.get('shortage',15)} + {c.get('holding',2)}) = **0.833**",
            "",
            "This means: stock enough to satisfy demand in **83.3% of scenarios** — "
            "much higher than the 50th percentile, because shortages cost 7.5× more than overstock.",
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"(format error: {e})"


def json_get_field(data_json: str, field: str) -> str:
    try:
        v = json.loads(data_json).get(field)
        return str(v) if v is not None else ""
    except Exception:
        return ""
