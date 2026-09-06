"""Recipe 120 — Insurance Policy Z3 Inference Engine.

Uses Z3's Fixedpoint (Datalog) engine to prove or disprove insurance eligibility
claims via backward-chaining over Horn clause rules.

Key difference from r105 (Prolog): Z3 is a formal SMT solver — it applies only
facts explicitly present in the knowledge base (closed-world assumption).  It
cannot infer that catastrophic_event implies emergency_event from semantics; it
checks only what is stated.  This eliminates the semantic-drift failure observed
in r105's LLM explanation phase.

Finite domain: BitVecSort(8) — required by Z3's Datalog engine (IntSort is infinite).
"""

import json

_DEFAULT_POLICY = {
    "policy_name": "ComprehensiveAuto_v3",
    "description": (
        "Insurance eligibility for emergency_claim: requires comprehensive policy AND "
        "active status AND (deductible_met OR catastrophic_event) AND emergency_event. "
        "Alice: comprehensive, active, deductible_met, emergency_event. "
        "Bob: basic policy only (no comprehensive, no policy_active). "
        "Carol: comprehensive, active, catastrophic_event — but NO emergency_event."
    ),
    "predicates": [
        "has_comprehensive", "policy_active", "deductible_met",
        "emergency_event", "catastrophic_event",
        "claim_covered", "eligible_claim", "emergency_claim",
    ],
    "base_predicates": [
        "has_comprehensive", "policy_active", "deductible_met",
        "emergency_event", "catastrophic_event",
    ],
    "customers": ["alice", "bob", "carol"],
    "facts": [
        ["has_comprehensive", "alice"],
        ["policy_active",     "alice"],
        ["deductible_met",    "alice"],
        ["emergency_event",   "alice"],
        ["has_comprehensive", "carol"],
        ["policy_active",     "carol"],
        ["catastrophic_event","carol"],
    ],
    "rules": [
        {
            "id": "R2", "desc": "Covered if deductible is met",
            "head": "claim_covered", "body": ["deductible_met"],
        },
        {
            "id": "R3", "desc": "Covered if catastrophic event occurred",
            "head": "claim_covered", "body": ["catastrophic_event"],
        },
        {
            "id": "R1", "desc": "Eligible if comprehensive + active + covered",
            "head": "eligible_claim",
            "body": ["has_comprehensive", "policy_active", "claim_covered"],
        },
        {
            "id": "R4", "desc": "Emergency claim approved if eligible + emergency event",
            "head": "emergency_claim",
            "body": ["eligible_claim", "emergency_event"],
        },
    ],
    "query": "emergency_claim",
}


def _build_engine(policy: dict):
    """Build Z3 Fixedpoint engine from policy JSON.

    Returns (fp, preds, cust_val) where cust_val maps customer name → BitVecVal.
    Uses BitVecSort(8) — required by Z3 Datalog (IntSort is rejected as infinite).
    """
    from z3 import BitVecSort, BitVec, BitVecVal, BoolSort, Function, Fixedpoint, ForAll, And, Implies

    C = BitVecSort(8)
    x = BitVec("x", 8)

    fp = Fixedpoint()
    fp.set("engine", "datalog")

    preds: dict = {}
    for pred_name in policy["predicates"]:
        fn = Function(pred_name, C, BoolSort())
        fp.register_relation(fn)
        preds[pred_name] = fn

    cust_val = {c: BitVecVal(i, 8) for i, c in enumerate(policy["customers"])}

    for fact in policy["facts"]:
        pred_name, customer = fact[0], fact[1]
        fp.add_rule(preds[pred_name](cust_val[customer]))

    for rule in policy["rules"]:
        head_fn   = preds[rule["head"]]
        body_exprs = [preds[b](x) for b in rule["body"]]
        body_expr  = And(*body_exprs) if len(body_exprs) > 1 else body_exprs[0]
        fp.add_rule(ForAll([x], Implies(body_expr, head_fn(x))))

    return fp, preds, cust_val


def _check_all(fp, preds: dict, idx) -> dict:
    """Return {pred_name: provable} for all predicates for a given customer index."""
    from z3 import sat
    return {name: fp.query(fn(idx)) == sat for name, fn in preds.items()}


def _explain_failure(provable: dict, policy: dict) -> list:
    """Goal-directed diagnosis: find which predicates block the top query."""
    query = policy["query"]
    blocking = []
    for rule in policy["rules"]:
        if rule["head"] != query:
            continue
        for body_pred in rule["body"]:
            if provable.get(body_pred):
                continue
            # Recurse one level into sub-rules
            sub_reasons = []
            for sub_rule in policy["rules"]:
                if sub_rule["head"] != body_pred:
                    continue
                for sub_body in sub_rule["body"]:
                    if not provable.get(sub_body):
                        sub_reasons.append(sub_body)
            if sub_reasons:
                blocking.append(f"{body_pred} (blocked by: {', '.join(sub_reasons)})")
            else:
                blocking.append(body_pred)
    return blocking or [f"{query} not derivable"]


def get_default_policy() -> str:
    """Return the ComprehensiveAuto_v3 policy JSON."""
    return json.dumps(_DEFAULT_POLICY)


def run_z3_inference(policy_json: str) -> str:
    """Z3 Fixedpoint (Datalog) inference for all customers in the policy.

    For each customer returns:
      - eligible: bool
      - provable: list of predicates Z3 derived
      - missing: list of blocking predicates for NOT ELIGIBLE customers

    Returns:
      {"policy_name", "query", "n_customers", "n_eligible", "status", "results"}
    """
    try:
        from z3 import sat
    except ImportError:
        return json.dumps({"status": "ERROR",
                           "error": "z3-solver not installed — run: pip install z3-solver"})

    try:
        policy    = json.loads(policy_json)
        fp, preds, cust_val = _build_engine(policy)
        query_fn  = preds[policy["query"]]
        results   = []

        for customer in policy["customers"]:
            idx      = cust_val[customer]
            eligible = fp.query(query_fn(idx)) == sat
            provable = _check_all(fp, preds, idx)

            proved_list  = [p for p in policy["predicates"] if provable.get(p)]
            missing_list = (_explain_failure(provable, policy) if not eligible else [])

            results.append({
                "customer": customer,
                "eligible": eligible,
                "verdict":  f"{customer}: {'ELIGIBLE' if eligible else 'NOT ELIGIBLE'} for {policy['query']}",
                "proved":   proved_list,
                "missing":  missing_list,
            })

        n_eligible = sum(1 for r in results if r["eligible"])
        return json.dumps({
            "policy_name": policy.get("policy_name", "Policy"),
            "query":       policy["query"],
            "n_customers": len(results),
            "n_eligible":  n_eligible,
            "status":      "OK",
            "results":     results,
        })

    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e)})


def inference_verified(result_json: str) -> bool:
    """ASSERT gate: Z3 ran successfully and produced results for all customers."""
    try:
        data = json.loads(result_json)
        return data.get("status") == "OK" and data.get("n_customers", 0) > 0
    except Exception:
        return False


def format_z3_report(result_json: str) -> str:
    """Markdown report: per-customer verdicts, proof paths, and missing facts."""
    try:
        data   = json.loads(result_json)
        status = data.get("status", "ERROR")

        if status == "ERROR":
            return (
                f"## Z3 Inference Report — Error\n\n"
                f"**Error:** {data.get('error', 'unknown')}\n\n"
                "Run `pip install z3-solver` if Z3 is not installed."
            )

        results = data.get("results", [])
        lines = [
            f"## Z3 Inference Report — {data.get('policy_name', 'Policy')}",
            "",
            f"**Query:** `{data.get('query', '?')}`  ",
            f"**Customers:** {data.get('n_customers', '?')}  ",
            f"**Eligible:** {data.get('n_eligible', '?')}",
            "",
            "| Customer | Eligible | Z3 Proved | Missing / Blocking |",
            "|---|---|---|---|",
        ]
        for r in results:
            mark    = "✓" if r["eligible"] else "✗"
            proved  = ", ".join(r.get("proved", [])) or "—"
            missing = "; ".join(r.get("missing", [])) or "—"
            lines.append(f"| {r['customer']} | {mark} | {proved} | {missing} |")
        return "\n".join(lines)
    except Exception as e:
        return f"(format error: {e})"


def json_get_field(data_json: str, field: str) -> str:
    try:
        v = json.loads(data_json).get(field)
        return str(v) if v is not None else ""
    except Exception:
        return ""
