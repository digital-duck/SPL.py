"""Recipe 127 — PII data-flow compliance with three deterministic engines.

An LLM reads a document and reports which kinds of personal data it contains (a PII map). Boolean facts are
derived from that map and the destination, and a set of Boolean rules decides whether the document may be sent.
The rules are checked by one of three engines that must agree:

  plain   a small evaluator in the standard library (the baseline: with concrete facts nothing needs solving)
  sympy   sympy.logic `satisfiable`
  z3      the Z3 SMT solver

A solver pays off on *search* questions (are the rules consistent? is there any compliant assignment?), so
`rules_consistent` asks one. The default rules are an ILLUSTRATION, not legal advice or a real GDPR/PCI rule set.

Rule format (JSON). A rule is {"id", "desc", "expr"}; an expression is one of
  {"var": name}   {"not": e}   {"and": [e, ...]}   {"or": [e, ...]}   {"implies": [a, b]}   {"const": true|false}
"""

import itertools
import json
import re

from spl.tools import spl_tool

EXTERNAL_DESTINATIONS = {"external_api", "third_party_vendor"}
ENGINES = ("plain", "sympy", "z3")
MAX_ENUMERATED_VARIABLES = 16

DEFAULT_RULES = {
    "name": "Illustrative PII data-flow policy (not legal advice)",
    "variables": ["has_ssn", "has_ccn", "is_masked", "is_external"],
    "rules": [
        {"id": "R1", "desc": "PII sent to an external destination must be masked",
         "expr": {"implies": [{"var": "is_external"}, {"var": "is_masked"}]}},
        {"id": "R2", "desc": "A social security number never leaves externally, even masked",
         "expr": {"not": {"and": [{"var": "has_ssn"}, {"var": "is_external"}]}}},
        {"id": "R3", "desc": "Card numbers must always be masked",
         "expr": {"implies": [{"var": "has_ccn"}, {"var": "is_masked"}]}},
    ],
}


# ── expressions ──────────────────────────────────────────────────────────────

def expr_variables(expr: dict) -> set:
    """Names of the variables an expression uses."""
    if "var" in expr:
        return {expr["var"]}
    if "const" in expr:
        return set()
    if "not" in expr:
        return expr_variables(expr["not"])
    for key in ("and", "or", "implies"):
        if key in expr:
            return set().union(*[expr_variables(e) for e in expr[key]])
    raise ValueError(f"unknown expression: {expr!r}")


def eval_expr(expr: dict, facts: dict) -> bool:
    """Evaluate an expression under a complete assignment (the plain engine)."""
    if "var" in expr:
        return bool(facts[expr["var"]])
    if "const" in expr:
        return bool(expr["const"])
    if "not" in expr:
        return not eval_expr(expr["not"], facts)
    if "and" in expr:
        return all(eval_expr(e, facts) for e in expr["and"])
    if "or" in expr:
        return any(eval_expr(e, facts) for e in expr["or"])
    if "implies" in expr:
        a, b = expr["implies"]
        return (not eval_expr(a, facts)) or eval_expr(b, facts)
    raise ValueError(f"unknown expression: {expr!r}")


def validate_rules(rules: dict) -> list:
    """The rules as a list, after checking the ids are unique and every variable is declared."""
    out = rules.get("rules")
    if not isinstance(out, list) or not out:
        raise ValueError("rules must be a non-empty list")
    declared, seen = set(rules.get("variables", [])), set()
    for rule in out:
        if not rule.get("id") or "expr" not in rule:
            raise ValueError(f"every rule needs an id and an expr: {rule!r}")
        if rule["id"] in seen:
            raise ValueError(f"duplicate rule id {rule['id']!r}")
        seen.add(rule["id"])
        unknown = expr_variables(rule["expr"]) - declared
        if unknown:
            raise ValueError(f"rule {rule['id']} uses undeclared variables {sorted(unknown)}")
    return out


# ── engines ──────────────────────────────────────────────────────────────────

def engine_available(engine: str) -> tuple:
    """(True, "") or (False, why)."""
    if engine == "plain":
        return True, ""
    try:
        if engine == "sympy":
            import sympy  # noqa: F401
        elif engine == "z3":
            import z3  # type: ignore[import-untyped]  # noqa: F401
        else:
            return False, f"unknown engine {engine!r}; choose from {list(ENGINES)}"
    except ImportError:
        package = "sympy" if engine == "sympy" else "z3-solver"
        return False, f"{engine} engine needs {package}: pip install {package}"
    return True, ""


def _sympy_expr(expr: dict, syms: dict):
    from sympy import And, Not, Or, Implies, true, false
    if "var" in expr:
        return syms[expr["var"]]
    if "const" in expr:
        return true if expr["const"] else false
    if "not" in expr:
        return Not(_sympy_expr(expr["not"], syms))
    if "and" in expr:
        return And(*[_sympy_expr(e, syms) for e in expr["and"]])
    if "or" in expr:
        return Or(*[_sympy_expr(e, syms) for e in expr["or"]])
    a, b = expr["implies"]
    return Implies(_sympy_expr(a, syms), _sympy_expr(b, syms))


def _z3_expr(expr: dict, bools: dict):
    import z3
    if "var" in expr:
        return bools[expr["var"]]
    if "const" in expr:
        return z3.BoolVal(bool(expr["const"]))
    if "not" in expr:
        return z3.Not(_z3_expr(expr["not"], bools))
    if "and" in expr:
        return z3.And(*[_z3_expr(e, bools) for e in expr["and"]])
    if "or" in expr:
        return z3.Or(*[_z3_expr(e, bools) for e in expr["or"]])
    a, b = expr["implies"]
    return z3.Implies(_z3_expr(a, bools), _z3_expr(b, bools))


def _check_plain(facts: dict, rules: list) -> dict:
    return {"violated": [r["id"] for r in rules if not eval_expr(r["expr"], facts)]}


def _check_sympy(facts: dict, rules: list) -> dict:
    from sympy import And, Not, Symbol
    from sympy.logic.inference import satisfiable
    syms = {name: Symbol(name) for name in facts}
    fact_formula = And(*[syms[n] if v else Not(syms[n]) for n, v in facts.items()])
    # a rule is violated when it cannot hold together with the facts
    violated = [r["id"] for r in rules if not satisfiable(And(fact_formula, _sympy_expr(r["expr"], syms)))]
    return {"violated": violated}


def _check_z3(facts: dict, rules: list) -> dict:
    import z3
    bools = {name: z3.Bool(name) for name in facts}
    solver = z3.Solver()
    for name, value in facts.items():
        solver.add(bools[name] == z3.BoolVal(bool(value)))
    violated = []
    for r in rules:                                   # each rule on its own with the facts, so the answer is
        solver.push()                                 # the same set the other engines report
        solver.add(_z3_expr(r["expr"], bools))
        if solver.check() == z3.unsat:
            violated.append(r["id"])
        solver.pop()
    core = []
    if violated:                                      # and the unsat core of all rules together, tracked by rule id
        tracked = z3.Solver()
        for name, value in facts.items():
            tracked.add(bools[name] == z3.BoolVal(bool(value)))
        for r in rules:
            tracked.assert_and_track(_z3_expr(r["expr"], bools), z3.Bool(f"rule_{r['id']}"))
        if tracked.check() == z3.unsat:
            core = sorted(str(c)[len("rule_"):] for c in tracked.unsat_core())
    return {"violated": violated, "core": core}


_CHECKERS = {"plain": _check_plain, "sympy": _check_sympy, "z3": _check_z3}


def check(facts: dict, rules: dict, engine: str = "plain") -> dict:
    """Do the facts satisfy every rule? {"status": "OK", "compliant": bool, "violated": [rule ids], ...}."""
    ok, why = engine_available(engine)
    if not ok:
        return {"status": "ERROR", "engine": engine, "error": why}
    try:
        rule_list = validate_rules(rules)
        missing = set(rules.get("variables", [])) - set(facts)
        if missing:
            raise ValueError(f"facts are missing {sorted(missing)}")
        found = _CHECKERS[engine]({k: bool(facts[k]) for k in rules["variables"]}, rule_list)
    except (ValueError, KeyError) as e:
        return {"status": "ERROR", "engine": engine, "error": str(e)}
    return {"status": "OK", "engine": engine, "compliant": not found["violated"], **found}


def consistent(rules: dict, engine: str = "plain") -> dict:
    """Search question: is there any assignment that satisfies all the rules? Returns an example if so."""
    ok, why = engine_available(engine)
    if not ok:
        return {"status": "ERROR", "engine": engine, "error": why}
    try:
        rule_list = validate_rules(rules)
    except ValueError as e:
        return {"status": "ERROR", "engine": engine, "error": str(e)}
    names = list(rules["variables"])
    if engine == "plain":
        if len(names) > MAX_ENUMERATED_VARIABLES:
            return {"status": "ERROR", "engine": engine,
                    "error": f"the plain engine enumerates assignments and handles up to {MAX_ENUMERATED_VARIABLES} variables"}
        for values in itertools.product([False, True], repeat=len(names)):
            assignment = dict(zip(names, values))
            if all(eval_expr(r["expr"], assignment) for r in rule_list):
                return {"status": "OK", "engine": engine, "consistent": True, "example": assignment}
        return {"status": "OK", "engine": engine, "consistent": False, "example": None}
    if engine == "sympy":
        from sympy import And, Symbol
        from sympy.logic.inference import satisfiable
        syms = {n: Symbol(n) for n in names}
        model = satisfiable(And(*[_sympy_expr(r["expr"], syms) for r in rule_list]))
        if not model:
            return {"status": "OK", "engine": engine, "consistent": False, "example": None}
        return {"status": "OK", "engine": engine, "consistent": True,
                "example": {n: bool(model.get(syms[n], False)) for n in names}}
    import z3
    bools = {n: z3.Bool(n) for n in names}
    solver = z3.Solver()
    solver.add(*[_z3_expr(r["expr"], bools) for r in rule_list])
    if solver.check() != z3.sat:
        return {"status": "OK", "engine": engine, "consistent": False, "example": None}
    model = solver.model()
    return {"status": "OK", "engine": engine, "consistent": True,
            "example": {n: bool(z3.is_true(model.eval(bools[n], model_completion=True))) for n in names}}


# ── facts from the LLM's PII map ─────────────────────────────────────────────

def parse_pii_map_text(raw: str) -> dict:
    """The PII map from LLM output (code fences allowed). Unreadable output gives {"entities": [], "parse_error": ...}
    so the caller can fail closed instead of treating a broken reply as 'no PII'."""
    text = str(raw).strip()
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fenced:
        text = fenced.group(1).strip()
    try:
        data = json.loads(text)
        entities = data["entities"]
        if not isinstance(entities, list) or not all(isinstance(e, dict) and "type" in e for e in entities):
            raise ValueError("entities must be a list of objects with a type")
        return {"entities": [{"type": str(e["type"]).upper(), "masked": bool(e.get("masked", False))} for e in entities]}
    except (ValueError, KeyError, TypeError) as e:
        return {"entities": [], "parse_error": f"{type(e).__name__}: {e}"}


def derive_facts_from(pii_map: dict, destination: str) -> dict:
    entities = pii_map.get("entities", [])
    return {
        "has_ssn": any(e["type"] == "SSN" for e in entities),
        "has_ccn": any(e["type"] in ("CCN", "CREDIT_CARD") for e in entities),
        "is_masked": all(e.get("masked", False) for e in entities),     # no entities: nothing to mask
        "is_external": str(destination).strip().lower() in EXTERNAL_DESTINATIONS,
    }


def check_pii_map(pii_map: dict, destination: str, engine: str = "plain", rules: "dict | None" = None) -> dict:
    """Facts from the PII map and destination, then `check`. A map that could not be read is NOT compliant."""
    if pii_map.get("parse_error"):
        return {"status": "OK", "engine": engine, "compliant": False, "violated": ["UNREADABLE_PII_MAP"],
                "error": pii_map["parse_error"], "facts": {}}
    facts = derive_facts_from(pii_map, destination)
    result = check(facts, rules or DEFAULT_RULES, engine)
    result["facts"] = facts
    return result


# ── SPL tools ────────────────────────────────────────────────────────────────

@spl_tool
def default_rules() -> str:
    """The illustrative default rules as JSON."""
    return json.dumps(DEFAULT_RULES)


@spl_tool
def normalize_engine(engine: str) -> str:
    """plain | sympy | z3 (case-insensitive); anything else falls back to plain."""
    e = str(engine).strip().lower()
    return e if e in ENGINES else "plain"


@spl_tool
def parse_pii_map(raw: str) -> str:
    """Clean the LLM's PII map reply into JSON; unreadable replies are marked so the check fails closed."""
    return json.dumps(parse_pii_map_text(raw))


@spl_tool
def check_compliance(pii_map_json: str, destination: str, engine: str, rules_json: str = "") -> str:
    """Check a PII map against the rules with the chosen engine. Returns JSON:
    {"status": "OK"|"ERROR", "engine", "compliant", "violated": [rule ids], "facts": {...}}."""
    try:
        rules = json.loads(rules_json) if str(rules_json).strip() else None
        result = check_pii_map(json.loads(pii_map_json), destination, normalize_engine(engine), rules)
    except (ValueError, TypeError) as e:
        result = {"status": "ERROR", "error": f"{type(e).__name__}: {e}"}
    return json.dumps(result)


@spl_tool
def check_succeeded(result_json: str) -> bool:
    """ASSERT gate: the engine ran (a violation is a result, not a failure; an engine error is a failure)."""
    try:
        return json.loads(result_json).get("status") == "OK"
    except (ValueError, AttributeError):
        return False


@spl_tool
def rules_consistent(rules_json: str, engine: str) -> str:
    """Search question: can the rules all hold at once? JSON with an example assignment if so."""
    try:
        rules = json.loads(rules_json) if str(rules_json).strip() else DEFAULT_RULES
        return json.dumps(consistent(rules, normalize_engine(engine)))
    except (ValueError, TypeError) as e:
        return json.dumps({"status": "ERROR", "error": f"{type(e).__name__}: {e}"})


@spl_tool
def format_report(result_json: str, destination: str, rules_json: str = "") -> str:
    """A short Markdown report of a compliance check."""
    try:
        res = json.loads(result_json)
        rules = {r["id"]: r["desc"] for r in (json.loads(rules_json) if str(rules_json).strip() else DEFAULT_RULES)["rules"]}
    except (ValueError, KeyError, TypeError):
        return f"(could not format: {result_json})"
    if res.get("status") != "OK":
        return f"## Compliance check\n\n**Engine error:** {res.get('error', 'unknown')}"
    lines = ["## Compliance check", "", f"**Destination:** {destination}  ",
             f"**Engine:** {res['engine']}  ", f"**Verdict:** {'COMPLIANT' if res['compliant'] else 'NOT COMPLIANT'}", ""]
    if res.get("error"):
        lines += [f"The PII map could not be read ({res['error']}), so the document is treated as not compliant.", ""]
    for rule_id in res.get("violated", []):
        lines.append(f"- {rule_id}: {rules.get(rule_id, 'the PII map was unreadable')}")
    return "\n".join(lines)


@spl_tool
def format_llm_report(llm_verdict: str, destination: str) -> str:
    """Report for the solver=OFF ablation: the LLM's own verdict, labelled as unverified."""
    return (f"## Compliance check (LLM judgement, unverified)\n\n**Destination:** {destination}  \n"
            f"**LLM verdict:** {str(llm_verdict).strip()}\n\n"
            "Run with --param use_solver=true to check the rules deterministically.")
