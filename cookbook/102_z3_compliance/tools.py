"""Recipe 102 — Z3 SMT Compliance Checker.

Encodes business eligibility rules as Z3 SMT constraints and checks:
  SAT  → a qualifying customer profile exists (returns the profile)
  UNSAT → rules are contradictory — no customer can ever qualify

Supported query types: find_qualifying_profile, check_applicant, detect_contradiction
"""

import json


_DEFAULT_LOAN_POLICY = {
    "policy": "QuickLoan Eligibility Policy v2.1",
    "variables": [
        {"name": "age",             "type": "int",  "range": [0, 120]},
        {"name": "income",          "type": "int",  "range": [0, 1000000]},
        {"name": "credit_score",    "type": "int",  "range": [300, 850]},
        {"name": "months_employed", "type": "int",  "range": [0, 600]},
        {"name": "has_collateral",  "type": "bool"},
        {"name": "self_employed",   "type": "bool"},
    ],
    "rules": [
        {"id": "R1", "desc": "Must be 18+",
         "op": "gte", "var": "age", "value": 18},
        {"id": "R2", "desc": "Income >= $30K or has collateral",
         "op": "or", "args": [
             {"op": "gte", "var": "income", "value": 30000},
             {"op": "eq",  "var": "has_collateral", "value": True},
         ]},
        {"id": "R3", "desc": "Self-employed requires income >= $50K",
         "op": "implies",
         "condition": {"op": "eq", "var": "self_employed", "value": True},
         "then":      {"op": "gte", "var": "income", "value": 50000}},
        {"id": "R4", "desc": "Credit >= 650 or (credit >= 600 and income >= $80K)",
         "op": "or", "args": [
             {"op": "gte", "var": "credit_score", "value": 650},
             {"op": "and", "args": [
                 {"op": "gte", "var": "credit_score", "value": 600},
                 {"op": "gte", "var": "income",       "value": 80000},
             ]},
         ]},
        {"id": "R5", "desc": "Employed 12+ months or has collateral",
         "op": "or", "args": [
             {"op": "gte", "var": "months_employed", "value": 12},
             {"op": "eq",  "var": "has_collateral",  "value": True},
         ]},
    ],
    "query": "find_qualifying_profile",
}


def _build_constraint(rule: dict, z3_vars: dict):
    """Recursively translate a rule dict into a Z3 expression."""
    from z3 import And, Or, Not, Implies  # type: ignore[import-untyped]

    op = rule["op"]
    if op == "gte":
        return z3_vars[rule["var"]] >= rule["value"]
    if op == "lte":
        return z3_vars[rule["var"]] <= rule["value"]
    if op == "eq":
        return z3_vars[rule["var"]] == rule["value"]
    if op == "neq":
        return z3_vars[rule["var"]] != rule["value"]
    if op == "and":
        return And(*[_build_constraint(a, z3_vars) for a in rule["args"]])
    if op == "or":
        return Or(*[_build_constraint(a, z3_vars) for a in rule["args"]])
    if op == "not":
        return Not(_build_constraint(rule["arg"], z3_vars))
    if op == "implies":
        return Implies(
            _build_constraint(rule["condition"], z3_vars),
            _build_constraint(rule["then"], z3_vars),
        )
    raise ValueError(f"Unknown op: {op}")


def extract_policy(_: str) -> str:
    """Return the default loan policy JSON (used as the canonical problem)."""
    return json.dumps(_DEFAULT_LOAN_POLICY)


def check_z3_eligibility(policy_json: str) -> str:
    """Run Z3 on the policy and return SAT/UNSAT + a qualifying profile (if SAT).

    Returns:
      {"status": "SAT"|"UNSAT"|"UNKNOWN", "qualifying_profile": {...},
       "n_rules": int, "verdict": str}
    """
    try:
        from z3 import Int, Bool, Solver, sat, unsat  # type: ignore[import-untyped]
    except ImportError:
        return json.dumps({"status": "ERROR",
                           "error": "z3-solver not installed — run: pip install z3-solver"})

    policy = json.loads(policy_json)

    z3_vars: dict = {}
    for v in policy["variables"]:
        if v["type"] == "int":
            z3_vars[v["name"]] = Int(v["name"])
        elif v["type"] == "bool":
            z3_vars[v["name"]] = Bool(v["name"])

    s = Solver()
    for v in policy["variables"]:
        if v["type"] == "int" and "range" in v:
            z3_vars[v["name"]] = z3_vars[v["name"]]
            s.add(z3_vars[v["name"]] >= v["range"][0])
            s.add(z3_vars[v["name"]] <= v["range"][1])

    for rule in policy["rules"]:
        s.add(_build_constraint(rule, z3_vars))

    result = s.check()

    if result == sat:
        m = s.model()
        profile: dict = {}
        for v in policy["variables"]:
            val = m[z3_vars[v["name"]]]
            if val is None:
                continue
            if v["type"] == "bool":
                profile[v["name"]] = bool(val)
            else:
                try:
                    profile[v["name"]] = int(str(val))
                except Exception:
                    profile[v["name"]] = str(val)
        return json.dumps({
            "status": "SAT",
            "verdict": "Policy is satisfiable — a qualifying customer profile exists",
            "qualifying_profile": profile,
            "n_rules": len(policy["rules"]),
        })

    if result == unsat:
        return json.dumps({
            "status": "UNSAT",
            "verdict": "Policy is UNSATISFIABLE — no customer can ever qualify (contradictory rules)",
            "qualifying_profile": {},
            "n_rules": len(policy["rules"]),
        })

    return json.dumps({"status": "UNKNOWN",
                       "verdict": "Z3 could not determine satisfiability",
                       "n_rules": len(policy["rules"])})


def check_applicant(policy_json: str, applicant_json: str) -> str:
    """Check whether a specific applicant satisfies all eligibility rules.

    applicant_json: {"age": 25, "income": 45000, "credit_score": 680, ...}
    Returns: {"status": "ELIGIBLE"|"INELIGIBLE", "failed_rules": [...], "verdict": str}
    """
    try:
        from z3 import Int, Bool, Solver, sat  # type: ignore[import-untyped]
    except ImportError:
        return json.dumps({"status": "ERROR", "error": "z3-solver not installed"})

    policy   = json.loads(policy_json)
    applicant = json.loads(applicant_json)

    z3_vars: dict = {}
    for v in policy["variables"]:
        if v["type"] == "int":
            z3_vars[v["name"]] = Int(v["name"])
        elif v["type"] == "bool":
            z3_vars[v["name"]] = Bool(v["name"])

    failed = []
    for rule in policy["rules"]:
        s = Solver()
        # Fix applicant values
        for v in policy["variables"]:
            name = v["name"]
            if name in applicant:
                s.add(z3_vars[name] == applicant[name])
        # Negate the rule: if UNSAT then rule is satisfied; if SAT then rule can be violated
        from z3 import Not  # type: ignore[import-untyped]
        s.add(Not(_build_constraint(rule, z3_vars)))
        if s.check() == sat:
            # The applicant CAN violate this rule; check if they DO
            s2 = Solver()
            for v in policy["variables"]:
                name = v["name"]
                if name in applicant:
                    s2.add(z3_vars[name] == applicant[name])
            s2.add(_build_constraint(rule, z3_vars))
            if s2.check() != sat:
                failed.append({"rule_id": rule["id"], "desc": rule["desc"]})

    status = "ELIGIBLE" if not failed else "INELIGIBLE"
    return json.dumps({
        "status": status,
        "failed_rules": failed,
        "verdict": f"Applicant is {status}."
                   + (f" Failed: {[r['rule_id'] for r in failed]}" if failed else ""),
        "n_rules": len(policy["rules"]),
    })


def is_satisfiable(result_json: str) -> bool:
    """ASSERT gate: policy is SAT (eligibility rules are consistent)."""
    try:
        return json.loads(result_json).get("status") == "SAT"
    except Exception:
        return False


def format_z3_report(result_json: str, policy_json: str) -> str:
    """Markdown report of Z3 eligibility check."""
    try:
        res    = json.loads(result_json)
        policy = json.loads(policy_json)
        lines  = [
            f"## Z3 Eligibility Check — {policy.get('policy', 'Policy')}",
            "",
            f"**Status:** {res['status']}  ",
            f"**Verdict:** {res['verdict']}",
            f"**Rules checked:** {res.get('n_rules', '?')}",
            "",
        ]
        if res["status"] == "SAT" and res.get("qualifying_profile"):
            lines += ["### Qualifying Profile Found by Z3", ""]
            lines += ["| Variable | Value |", "|---|---|"]
            for k, v in res["qualifying_profile"].items():
                lines.append(f"| {k} | {v} |")
        elif res["status"] == "UNSAT":
            lines += [
                "### Contradiction Detected",
                "",
                "Z3 proved that no assignment of input variables can satisfy all rules simultaneously.",
                "This indicates a logical contradiction in the policy — review the rules for conflicting requirements.",
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
