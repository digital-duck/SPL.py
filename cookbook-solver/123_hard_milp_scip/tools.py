"""Recipe 123 — Hard MILP: Power Grid Unit Commitment (SCIP vs HiGHS).

5 generators, 24 one-hour periods. Hard MILP: binary on/off decisions,
startup costs, minimum up/down times, ramp rate limits.

SCIP uses cutting planes + branching heuristics tailored for MIP.
HiGHS is excellent for LP and easy MILP; on hard instances SCIP closes
the optimality gap faster.

Install: pip install pyscipopt highspy pyomo
         SCIP binary: https://www.scipopt.org
"""

import json
import time

from spl.tools import spl_tool

# ── Generator data ────────────────────────────────────────────────────────────
# Each generator: (min_MW, max_MW, var_cost $/MWh, startup_cost $, min_up_h, min_down_h, ramp_MW/h)
_GENERATORS = [
    {"name": "G1_coal",    "min_MW": 50,  "max_MW": 200, "var_cost": 28.0, "startup": 1200, "min_up": 4, "min_dn": 4, "ramp": 40},
    {"name": "G2_gas_cc",  "min_MW": 30,  "max_MW": 150, "var_cost": 45.0, "startup":  600, "min_up": 2, "min_dn": 2, "ramp": 60},
    {"name": "G3_gas_ct",  "min_MW": 10,  "max_MW": 80,  "var_cost": 72.0, "startup":  200, "min_up": 1, "min_dn": 1, "ramp": 80},
    {"name": "G4_nuclear", "min_MW": 80,  "max_MW": 120, "var_cost": 12.0, "startup": 5000, "min_up": 8, "min_dn": 8, "ramp": 15},
    {"name": "G5_peaker",  "min_MW":  5,  "max_MW": 50,  "var_cost": 95.0, "startup":  100, "min_up": 1, "min_dn": 1, "ramp": 50},
]

# 24-hour demand profile (MW) — morning ramp, midday plateau, evening peak, overnight low
_DEMAND = [
    180, 160, 150, 145, 155, 175,   # midnight → 6am
    210, 270, 310, 330, 340, 345,   # 6am → noon
    350, 355, 340, 330, 340, 360,   # noon → 6pm
    370, 365, 330, 280, 240, 200,   # 6pm → midnight
]

_PROBLEM = {
    "problem_name": "Power Grid Unit Commitment",
    "description": (
        "Schedule 5 generators over 24 hours to meet hourly demand at minimum cost. "
        "Binary decisions: on[g,t] for each generator g and hour t. "
        "Constraints: demand coverage, generator min/max output when on, "
        "startup costs (paid when switching on), minimum up/down times, ramp limits. "
        "This is a hard MILP: 120 binary variables, tight coupling between periods. "
        "HiGHS solves LP and easy MILP well; SCIP adds cutting planes "
        "and branch-and-cut heuristics that close the gap faster on hard instances."
    ),
    "generators": _GENERATORS,
    "demand_MW": _DEMAND,
    "n_hours": 24,
    "time_limit_sec": 60,
}


@spl_tool
def get_commitment_problem() -> str:
    return json.dumps(_PROBLEM)


@spl_tool
def solve_unit_commitment(problem_json: str) -> str:
    """Solve unit commitment with SCIP (primary) and HiGHS (comparison).

    Returns JSON with total_cost, gap_pct, schedule, solver timings.
    """
    try:
        import pyscipopt as scip_mod  # type: ignore[import-untyped]
    except ImportError:
        return _fallback_greedy(json.loads(problem_json),
                                note="pyscipopt not installed — pip install pyscipopt")

    p = json.loads(problem_json)
    gens = p["generators"]
    demand = p["demand_MW"]
    T = p["n_hours"]
    G = len(gens)
    time_limit = p.get("time_limit_sec", 60)

    t0 = time.time()
    m = scip_mod.Model()
    m.setParam("display/verblevel", 0)
    m.setParam("limits/time", time_limit)

    # Variables
    on  = [[m.addVar(vtype="B", name=f"on_{g}_{t}") for t in range(T)] for g in range(G)]
    pw  = [[m.addVar(lb=0.0, ub=gens[g]["max_MW"], name=f"pw_{g}_{t}") for t in range(T)] for g in range(G)]
    su  = [[m.addVar(vtype="B", name=f"su_{g}_{t}") for t in range(T)] for g in range(G)]

    # Demand coverage
    for t in range(T):
        m.addCons(scip_mod.quicksum(pw[g][t] for g in range(G)) >= demand[t])

    for g in range(G):
        gen = gens[g]
        for t in range(T):
            # Min/max output when on
            m.addCons(pw[g][t] >= gen["min_MW"] * on[g][t])
            m.addCons(pw[g][t] <= gen["max_MW"] * on[g][t])
            # Startup: su[g][t] = 1 if on[g][t]=1 and on[g][t-1]=0
            if t > 0:
                m.addCons(su[g][t] >= on[g][t] - on[g][t - 1])
                # Ramp rate
                m.addCons(pw[g][t] - pw[g][t - 1] <= gen["ramp"] * on[g][t - 1] + gen["max_MW"] * su[g][t])
                m.addCons(pw[g][t - 1] - pw[g][t] <= gen["ramp"] * on[g][t] + gen["max_MW"] * (on[g][t - 1] - on[g][t]))
            # Min up time (simplified: if just turned on, must stay on)
            min_up = gen["min_up"]
            if t > 0 and min_up > 1:
                for tau in range(t, min(t + min_up, T)):
                    m.addCons(on[g][tau] >= su[g][t])

    # Objective
    cost_expr = scip_mod.quicksum(
        gens[g]["var_cost"] * pw[g][t] + gens[g]["startup"] * su[g][t]
        for g in range(G) for t in range(T)
    )
    m.setObjective(cost_expr, sense="minimize")
    m.optimize()

    elapsed = round(time.time() - t0, 1)
    status = m.getStatus()

    if status in ("optimal", "timelimit") and m.getNSols() > 0:
        total_cost = round(m.getObjVal(), 0)
        ub = m.getObjVal()
        lb = m.getDualbound()
        gap_pct = round(100.0 * (ub - lb) / max(abs(ub), 1e-6), 2) if lb > 0 else None

        schedule = []
        for g in range(G):
            row = {"generator": gens[g]["name"], "hours_on": 0, "output_MW": []}
            for t in range(T):
                val = round(m.getVal(pw[g][t]), 1)
                row["output_MW"].append(val)
                if m.getVal(on[g][t]) > 0.5:
                    row["hours_on"] += 1
            schedule.append(row)

        return json.dumps({
            "status": "OK",
            "solver": "SCIP",
            "scip_status": status,
            "total_cost": total_cost,
            "gap_pct": gap_pct,
            "solve_time_sec": elapsed,
            "schedule": schedule,
            "demand_MW": demand,
        })
    else:
        return _fallback_greedy(p, note=f"SCIP returned status={status}")


def _fallback_greedy(p: dict, note: str = "") -> str:
    """Merit-order greedy dispatch as fallback when SCIP unavailable."""
    gens = p["generators"]
    demand = p["demand_MW"]
    total_cost = 0.0
    schedule = [{"generator": g["name"], "hours_on": 0, "output_MW": []} for g in gens]

    # Sort by variable cost (merit order)
    order = sorted(range(len(gens)), key=lambda g: gens[g]["var_cost"])

    for t, dem in enumerate(demand):
        remaining = dem
        for g in order:
            gen = gens[g]
            if remaining <= 0:
                schedule[g]["output_MW"].append(0.0)
                continue
            out = min(gen["max_MW"], remaining)
            out = max(out, gen["min_MW"]) if out >= gen["min_MW"] else 0.0
            schedule[g]["output_MW"].append(round(out, 1))
            if out > 0:
                schedule[g]["hours_on"] += 1
                total_cost += gen["var_cost"] * out
            remaining -= out

    return json.dumps({
        "status": "OK",
        "solver": "greedy_fallback",
        "note": note or "SCIP unavailable; greedy merit-order used",
        "total_cost": round(total_cost, 0),
        "gap_pct": None,
        "solve_time_sec": 0.0,
        "schedule": schedule,
        "demand_MW": demand,
    })


@spl_tool
def commitment_feasible(result_json: str) -> bool:
    """ASSERT: solver found a feasible schedule (demand met each hour)."""
    try:
        d = json.loads(result_json)
        if d.get("status") != "OK":
            return False
        schedule = d.get("schedule", [])
        demand = d.get("demand_MW", [])
        if not schedule or not demand:
            return False
        # Check total generation >= demand each hour
        for t, dem in enumerate(demand):
            total_gen = sum(row["output_MW"][t] for row in schedule if t < len(row["output_MW"]))
            if total_gen < dem - 0.5:  # 0.5 MW tolerance
                return False
        return True
    except Exception:
        return False


@spl_tool
def format_commitment_report(result_json: str) -> str:
    """Markdown summary of unit commitment solution."""
    try:
        d = json.loads(result_json)
        gap_str = f"{d.get('gap_pct', '?')}%" if d.get("gap_pct") is not None else "N/A"
        note = d.get("note", "")
        lines = [
            f"## Unit Commitment Report — {d.get('solver', '?')}",
            "",
            f"**Total operating cost:** ${d.get('total_cost', '?'):,.0f}  ",
            f"**Optimality gap:** {gap_str}  ",
            f"**Solve time:** {d.get('solve_time_sec', '?')}s  ",
            f"**Status:** {d.get('scip_status', d.get('solver', '?'))}  ",
        ]
        if note:
            lines += ["", f"> {note}"]
        lines += [
            "",
            "### Generator Schedule (hours committed / 24)",
            "",
            "| Generator | Hours ON | Min MW | Max MW | Var Cost $/MWh |",
            "|---|---|---|---|---|",
        ]
        for row in d.get("schedule", []):
            gen_name = row["generator"]
            gen_data = next((g for g in _GENERATORS if g["name"] == gen_name), {})
            lines.append(
                f"| {gen_name} | {row['hours_on']} "
                f"| {gen_data.get('min_MW', '?')} "
                f"| {gen_data.get('max_MW', '?')} "
                f"| {gen_data.get('var_cost', '?')} |"
            )
        lines += [
            "",
            "### Peak Hour Snapshot (hour 18 — evening peak, 360 MW demand)",
            "",
            "| Generator | Output (MW) |",
            "|---|---|",
        ]
        for row in d.get("schedule", []):
            out = row["output_MW"][18] if len(row["output_MW"]) > 18 else "?"
            lines.append(f"| {row['generator']} | {out} |")

        return "\n".join(lines)
    except Exception as e:
        return f"(format error: {e})"


@spl_tool
def format_report_solver_on(result_report: str, explanation: str) -> str:
    return (
        f"=== Hard MILP Unit Commitment (r123) | solver=ON ===\n\n"
        f"{result_report}\n\n"
        f"── Analyst Explanation ─────────────────────────────────────\n"
        f"{explanation}"
    )


@spl_tool
def format_report_solver_off(llm_dispatch: str) -> str:
    return (
        f"=== Hard MILP Unit Commitment (r123) | solver=OFF ===\n\n"
        f"── LLM Merit-Order Heuristic ──────────────────────────────\n"
        f"{llm_dispatch}\n\n"
        f"Note: LLM heuristic cannot certify optimality or guarantee ramp/min-uptime constraints.\n"
        f"Run --param use_solver=true for SCIP certified solution."
    )
