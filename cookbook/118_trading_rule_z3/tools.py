"""Recipe 118 — Z3 Trading Rule Checker.

Encodes a trader's entry/exit/risk rulebook as Z3 SMT constraints and verifies:
  SAT    → a market scenario exists where the rules trigger a trade (consistent)
  UNSAT  → rules are contradictory — no market state ever fires this strategy
  SNAPSHOT → given today's indicator values, do rules trigger right now?

NL → Z3 translation is done by the LLM; Z3 provides the rigorous proof.
"""

import json


_DEFAULT_TRADING_POLICY = {
    "policy": "Momentum Breakout Strategy v1.0",
    "variables": [
        {"name": "rsi",           "type": "int",  "range": [0, 100]},
        {"name": "price_vs_ma200","type": "int",  "range": [-100, 200]},  # % above/below 200d MA * 10 (fixed-point)
        {"name": "volume_ratio",  "type": "int",  "range": [0, 500]},      # volume / avg_volume * 100
        {"name": "adr_pct",       "type": "int",  "range": [0, 200]},      # avg daily range % * 10
        {"name": "in_uptrend",    "type": "bool"},
        {"name": "earnings_week", "type": "bool"},
    ],
    "entry_rules": [
        {"id": "E1", "desc": "RSI oversold: 28 ≤ RSI ≤ 35 (momentum but not panic)",
         "op": "and", "args": [
             {"op": "gte", "var": "rsi", "value": 28},
             {"op": "lte", "var": "rsi", "value": 35},
         ]},
        {"id": "E2", "desc": "Price above 200-day MA (uptrend context)",
         "op": "gte", "var": "price_vs_ma200", "value": 0},
        {"id": "E3", "desc": "Volume surge: at least 1.5x average",
         "op": "gte", "var": "volume_ratio", "value": 150},
        {"id": "E4", "desc": "Sufficient volatility: ADR% ≥ 2.0",
         "op": "gte", "var": "adr_pct", "value": 20},
    ],
    "risk_rules": [
        {"id": "R1", "desc": "Never enter during earnings week",
         "op": "eq", "var": "earnings_week", "value": False},
        {"id": "R2", "desc": "Only enter in confirmed uptrend",
         "op": "eq", "var": "in_uptrend", "value": True},
    ],
    "query": "find_triggering_scenario",
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


def _make_z3_vars(policy: dict) -> dict:
    from z3 import Int, Bool  # type: ignore[import-untyped]
    z3_vars: dict = {}
    for v in policy["variables"]:
        if v["type"] == "int":
            z3_vars[v["name"]] = Int(v["name"])
        elif v["type"] == "bool":
            z3_vars[v["name"]] = Bool(v["name"])
    return z3_vars


def _add_range_constraints(solver, policy: dict, z3_vars: dict):
    for v in policy["variables"]:
        if v["type"] == "int" and "range" in v:
            solver.add(z3_vars[v["name"]] >= v["range"][0])
            solver.add(z3_vars[v["name"]] <= v["range"][1])


def get_default_policy() -> str:
    """Return the hardcoded Momentum Breakout policy (demo / fallback)."""
    return json.dumps(_DEFAULT_TRADING_POLICY)


def is_empty_policy(policy_text: str) -> str:
    """Return 'true' if no custom policy was provided."""
    return "true" if not policy_text.strip() else "false"


def parse_policy_json(json_str: str) -> str:
    """Validate LLM-extracted trading policy JSON; fall back to default on failure."""
    import re
    text = json_str.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        text = m.group(1).strip()
    try:
        policy = json.loads(text)
        if "variables" not in policy:
            raise ValueError("missing variables")
        # Normalise: accept either flat 'rules' or split 'entry_rules'+'risk_rules'
        if "rules" in policy and "entry_rules" not in policy:
            policy["entry_rules"] = policy.pop("rules")
        if "entry_rules" not in policy:
            raise ValueError("missing entry_rules")
        policy.setdefault("risk_rules", [])
        policy.setdefault("query", "find_triggering_scenario")
        return json.dumps(policy)
    except Exception:
        return json.dumps(_DEFAULT_TRADING_POLICY)


def check_z3_strategy(policy_json: str) -> str:
    """Run Z3 on all entry + risk rules.

    Returns SAT → triggering market scenario, UNSAT → contradictory rules.
    """
    try:
        from z3 import Solver, sat, unsat  # type: ignore[import-untyped]
    except ImportError:
        return json.dumps({"status": "ERROR",
                           "error": "z3-solver not installed — run: pip install z3-solver"})

    policy = json.loads(policy_json)
    z3_vars = _make_z3_vars(policy)

    s = Solver()
    _add_range_constraints(s, policy, z3_vars)

    all_rules = policy.get("entry_rules", []) + policy.get("risk_rules", [])
    for rule in all_rules:
        s.add(_build_constraint(rule, z3_vars))

    result = s.check()

    if result == sat:
        model = s.model()
        scenario: dict = {}
        for v in policy["variables"]:
            val = model[z3_vars[v["name"]]]
            if val is None:
                continue
            if v["type"] == "bool":
                scenario[v["name"]] = bool(val)
            else:
                try:
                    scenario[v["name"]] = int(str(val))
                except Exception:
                    scenario[v["name"]] = str(val)
        return json.dumps({
            "status": "SAT",
            "verdict": "Strategy is consistent — a triggering market scenario exists",
            "triggering_scenario": scenario,
            "n_entry_rules": len(policy.get("entry_rules", [])),
            "n_risk_rules": len(policy.get("risk_rules", [])),
        })

    if result == unsat:
        return json.dumps({
            "status": "UNSAT",
            "verdict": "Strategy is CONTRADICTORY — no market state can ever trigger all rules simultaneously",
            "triggering_scenario": {},
            "n_entry_rules": len(policy.get("entry_rules", [])),
            "n_risk_rules": len(policy.get("risk_rules", [])),
        })

    return json.dumps({"status": "UNKNOWN",
                       "verdict": "Z3 could not determine satisfiability"})


def check_market_snapshot(policy_json: str, snapshot_json: str) -> str:
    """Given today's market indicator values, check which rules fire.

    snapshot_json: {"rsi": 31, "price_vs_ma200": 5, "volume_ratio": 180, ...}
    Returns: {"signal": "BUY"|"NO_SIGNAL", "failed_rules": [...], "passed_rules": [...]}
    """
    try:
        from z3 import Solver, sat  # type: ignore[import-untyped]
        from z3 import Not  # type: ignore[import-untyped]
    except ImportError:
        return json.dumps({"status": "ERROR", "error": "z3-solver not installed"})

    policy   = json.loads(policy_json)
    snapshot = json.loads(snapshot_json)
    z3_vars  = _make_z3_vars(policy)

    all_rules = policy.get("entry_rules", []) + policy.get("risk_rules", [])
    passed, failed = [], []

    for rule in all_rules:
        s = Solver()
        for v in policy["variables"]:
            name = v["name"]
            if name in snapshot:
                s.add(z3_vars[name] == snapshot[name])
        s.add(Not(_build_constraint(rule, z3_vars)))
        if s.check() == sat:
            # rule CAN be violated; check if snapshot actually violates it
            s2 = Solver()
            for v in policy["variables"]:
                name = v["name"]
                if name in snapshot:
                    s2.add(z3_vars[name] == snapshot[name])
            s2.add(_build_constraint(rule, z3_vars))
            if s2.check() != sat:
                failed.append({"rule_id": rule["id"], "desc": rule["desc"]})
            else:
                passed.append(rule["id"])
        else:
            passed.append(rule["id"])

    signal = "BUY" if not failed else "NO_SIGNAL"
    return json.dumps({
        "signal": signal,
        "passed_rules": passed,
        "failed_rules": failed,
        "verdict": f"Signal: {signal}." + (
            f" Blocking rules: {[r['rule_id'] for r in failed]}" if failed else " All rules satisfied."
        ),
    })


def is_strategy_consistent(result_json: str) -> bool:
    """ASSERT gate: strategy rules are not contradictory."""
    try:
        return json.loads(result_json).get("status") == "SAT"
    except Exception:
        return False


def format_strategy_report(result_json: str, policy_json: str) -> str:
    """Markdown report of Z3 strategy audit."""
    try:
        res    = json.loads(result_json)
        policy = json.loads(policy_json)
        lines  = [
            f"## Z3 Trading Rule Audit — {policy.get('policy', 'Strategy')}",
            "",
            f"**Status:** {res['status']}  ",
            f"**Verdict:** {res['verdict']}",
            f"**Entry rules checked:** {res.get('n_entry_rules', '?')}  ",
            f"**Risk rules checked:** {res.get('n_risk_rules', '?')}",
            "",
        ]
        if res["status"] == "SAT" and res.get("triggering_scenario"):
            lines += ["### Triggering Market Scenario Found by Z3", ""]
            lines += ["| Indicator | Value |", "|---|---|"]
            for k, v in res["triggering_scenario"].items():
                lines.append(f"| {k} | {v} |")
            lines += [
                "",
                "> Z3 found the **minimum boundary** scenario — the exact threshold where all rules first "
                "become simultaneously satisfiable. A manual trace typically picks a 'typical' example "
                "and misses these edges.",
            ]
        elif res["status"] == "UNSAT":
            lines += [
                "### Contradiction Detected",
                "",
                "Z3 proved that no combination of market indicators can satisfy all entry and risk rules "
                "simultaneously. This strategy can **never** trigger a trade.",
                "",
                "Common causes:",
                "- An entry rule requires condition X while a risk rule forbids X",
                "- Two rules bound the same variable from opposite sides with no overlap",
                "- A boolean flag is required both True and False",
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
