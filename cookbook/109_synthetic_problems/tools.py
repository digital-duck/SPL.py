"""Recipe 109 — Synthetic Problem Generator.

Given a sample verified problem + domain, asks an LLM to generate N structural
variants (different numbers, same solver class), then batch-solves each one to
produce a labeled test suite: (problem_text, formal_spec, solver_status, optimal).

Supported domains (batch_solve router):
  "LP"              — linear programming (continuous variables, PuLP)
  "ILP"             — integer linear programming (PuLP integer vars)
  "supply-sourcing" — B1 pattern: cost vs fill rate, epsilon-constraint
"""

import json
import os
import re
from datetime import datetime


# ── JSON extraction ──────────────────────────────────────────────────────────

def _extract_json(text: str):
    """Pull the first JSON array or object from fenced or raw text."""
    for pat in [
        r'```(?:json)?\s*([\[{].*?)\s*```',   # fenced block
        r'((?:\[|\{)(?:.|\n)*(?:\]|\}))',       # bare JSON
    ]:
        m = re.search(pat, text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                continue
    raise ValueError("No parseable JSON found in LLM output")


# ── Variant parsing & validation ─────────────────────────────────────────────

_REQUIRED = {
    "lp":              {"id", "problem_text", "variables", "objective", "constraints"},
    "ilp":             {"id", "problem_text", "variables", "objective", "constraints"},
    "supply-sourcing": {"id", "problem_text", "suppliers", "total_demand"},
}


def parse_variants(variants_raw: str, domain: str) -> str:
    """Parse LLM-generated variant JSON and validate required fields.

    Returns:
      {"status": "OK"|"EMPTY"|"PARSE_ERROR", "n_valid": int, "n_errors": int,
       "errors": [str], "variants": [dict]}
    """
    try:
        data = _extract_json(variants_raw)
        if isinstance(data, dict):
            # Single variant or wrapper object {"variants": [...]}
            data = data.get("variants", [data])

        dom_key = domain.lower().replace(" ", "-")
        required = _REQUIRED.get(dom_key, _REQUIRED["lp"])

        valid, errors = [], []
        for i, v in enumerate(data):
            vid = v.get("id", f"v{i + 1:03d}")
            v["id"] = vid
            missing = required - set(v.keys())
            if missing:
                errors.append(f"{vid}: missing {sorted(missing)}")
            else:
                v["domain"] = dom_key
                valid.append(v)

        return json.dumps({
            "status":   "OK" if valid else "EMPTY",
            "n_valid":  len(valid),
            "n_errors": len(errors),
            "errors":   errors,
            "variants": valid,
        })
    except Exception as e:
        return json.dumps({
            "status": "PARSE_ERROR", "error": str(e),
            "n_valid": 0, "n_errors": 1,
            "errors": [str(e)], "variants": [],
        })


def has_valid_variants(variants_json: str) -> bool:
    """ASSERT gate: at least 1 variant parsed successfully."""
    try:
        return json.loads(variants_json).get("n_valid", 0) >= 1
    except Exception:
        return False


def get_parse_errors(variants_json: str) -> str:
    """Return error summary for the repair-loop prompt."""
    try:
        data = json.loads(variants_json)
        errors = data.get("errors", [])
        return "; ".join(errors) if errors else f"status={data.get('status')}"
    except Exception:
        return "JSON parse error"


# ── Domain solvers ───────────────────────────────────────────────────────────

def _solve_lp(spec: dict) -> dict:
    """Build and solve an LP/ILP from a structured spec dict via PuLP."""
    import pulp

    sense = (pulp.LpMaximize
             if spec["objective"].get("sense", "maximize") == "maximize"
             else pulp.LpMinimize)
    prob = pulp.LpProblem(f"variant_{spec['id']}", sense)

    vtype_map = {
        "continuous": pulp.LpContinuous,
        "integer":    pulp.LpInteger,
        "binary":     pulp.LpBinary,
    }
    lp_vars = {}
    for v in spec["variables"]:
        vtype = vtype_map.get(str(v.get("type", "continuous")).lower(), pulp.LpContinuous)
        lp_vars[v["name"]] = pulp.LpVariable(
            v["name"],
            lowBound=v.get("lb", 0),
            upBound=v.get("ub", None),
            cat=vtype,
        )

    coeffs = spec["objective"]["coefficients"]
    prob += pulp.lpSum(
        float(coeffs.get(n, 0)) * lp_vars[n]
        for n in lp_vars
        if n in coeffs
    )

    for c in spec.get("constraints", []):
        lhs = pulp.lpSum(
            float(c["lhs"].get(n, 0)) * lp_vars[n]
            for n in lp_vars
            if n in c["lhs"]
        )
        rhs = float(c["rhs"])
        op  = c.get("op", "<=")
        if   op == "<=": prob += lhs <= rhs
        elif op == ">=": prob += lhs >= rhs
        else:            prob += lhs == rhs

    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    status = pulp.LpStatus[prob.status]

    if status == "Optimal":
        raw_obj = pulp.value(prob.objective)
        obj  = round(float(raw_obj) if isinstance(raw_obj, float) else 0.0, 4)
        vals = {n: round(float(v) if isinstance(v := pulp.value(lp_vars[n]), float) else 0.0, 4)
                for n in lp_vars}
        return {"status": "OPTIMAL", "objective": obj, "variables": vals}
    return {"status": status, "objective": None, "variables": {}}


def _solve_supply_sourcing(spec: dict) -> dict:
    """Solve a supply-sourcing cost-minimization problem via PuLP."""
    import pulp

    suppliers = spec["suppliers"]
    demand    = float(spec["total_demand"])

    prob = pulp.LpProblem("supply_sourcing", pulp.LpMinimize)
    x = {
        s["name"]: pulp.LpVariable(f"x_{s['name']}", lowBound=0, upBound=float(s["capacity"]))
        for s in suppliers
    }

    prob += pulp.lpSum(float(s["cost"]) * x[s["name"]] for s in suppliers)
    prob += pulp.lpSum(x[s["name"]] for s in suppliers) == demand

    prob.solve(pulp.PULP_CBC_CMD(msg=False))

    if pulp.LpStatus[prob.status] == "Optimal":
        alloc = {s["name"]: round(float(v) if isinstance(v := pulp.value(x[s["name"]]), float) else 0.0, 2)
                 for s in suppliers}
        raw_cost = pulp.value(prob.objective)
        cost = round(float(raw_cost) if isinstance(raw_cost, float) else 0.0, 2)
        fill  = round(
            sum(float(s["fill_rate"]) * alloc[s["name"]] for s in suppliers) / demand, 4
        )
        return {"status": "OPTIMAL", "objective": cost,
                "fill_rate": fill, "allocation": alloc}
    return {"status": pulp.LpStatus[prob.status], "objective": None}


def batch_solve(variants_json: str, domain: str) -> str:
    """Solve all parsed variants; route by domain.

    Returns:
      {"status": "OK", "n_total": int, "n_optimal": int, "n_failed": int, "results": [...]}
    """
    try:
        data     = json.loads(variants_json)
        variants = data.get("variants", [])
        results  = []

        for v in variants:
            dom = v.get("domain", domain).lower()
            try:
                sol = _solve_supply_sourcing(v) if "supply" in dom else _solve_lp(v)
                results.append({
                    "id":            v["id"],
                    "domain":        dom,
                    "problem_text":  v.get("problem_text", ""),
                    "solver_status": sol["status"],
                    "optimal":       sol.get("objective"),
                    "variables":     sol.get("variables", {}),
                    "fill_rate":     sol.get("fill_rate"),
                })
            except Exception as e:
                results.append({
                    "id":            v["id"],
                    "domain":        dom,
                    "problem_text":  v.get("problem_text", ""),
                    "solver_status": "ERROR",
                    "error":         str(e),
                    "optimal":       None,
                    "variables":     {},
                })

        n_ok = sum(1 for r in results if r["solver_status"] == "OPTIMAL")
        return json.dumps({
            "status":    "OK",
            "n_total":   len(results),
            "n_optimal": n_ok,
            "n_failed":  len(results) - n_ok,
            "results":   results,
        })
    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e),
                           "n_total": 0, "n_optimal": 0, "n_failed": 0, "results": []})


# ── Formatting & persistence ─────────────────────────────────────────────────

def format_test_suite(results_json: str) -> str:
    """Format batch-solve results as a markdown table."""
    try:
        data    = json.loads(results_json)
        results = data.get("results", [])
        lines   = [
            f"**{data.get('n_optimal', 0)}/{data.get('n_total', 0)} variants solved optimally**",
            "",
            "| ID | Domain | Status | Optimal | Problem (excerpt) |",
            "|---|---|---|---|---|",
        ]
        for r in results:
            excerpt = r["problem_text"][:80].replace("|", "/")
            opt     = str(r["optimal"]) if r["optimal"] is not None else "—"
            fill    = f"  fill={r['fill_rate']:.2%}" if r.get("fill_rate") else ""
            lines.append(
                f"| {r['id']} | {r['domain']} | {r['solver_status']} "
                f"| {opt}{fill} | {excerpt}… |"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"(format error: {e})"


def save_test_suite(results_json: str, domain: str) -> str:
    """Persist test suite JSON to cookbook/109_synthetic_problems/output/."""
    try:
        out_dir = os.path.join(
            os.getcwd(), "cookbook", "109_synthetic_problems", "output"
        )
        os.makedirs(out_dir, exist_ok=True)
        ts   = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        path = os.path.join(out_dir, f"{domain.lower()}_{ts}.json")
        with open(path, "w") as f:
            json.dump(json.loads(results_json), f, indent=2)
        return path
    except Exception as e:
        return f"save error: {e}"


def json_get_field(data_json: str, field: str) -> str:
    """Extract a top-level field from JSON as a string."""
    try:
        v = json.loads(data_json).get(field)
        return str(v) if v is not None else ""
    except Exception:
        return ""
