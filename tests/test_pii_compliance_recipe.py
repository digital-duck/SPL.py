"""Recipe 127 (cookbook-solver/127_pii_compliance): three engines that must agree, fail-closed behaviour,
and the two workflows parse and run. SymPy and Z3 tests skip when the package is not installed."""
import importlib.util
import itertools
import json
from pathlib import Path

import pytest
from click.testing import CliRunner

RECIPE = Path(__file__).resolve().parent.parent / "cookbook-solver" / "127_pii_compliance"


def _load_tools():
    spec = importlib.util.spec_from_file_location("recipe127_tools", RECIPE / "tools.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tools = _load_tools()
RULES = tools.DEFAULT_RULES
ASSIGNMENTS = [dict(zip(RULES["variables"], v)) for v in itertools.product([False, True], repeat=len(RULES["variables"]))]
AVAILABLE = [e for e in tools.ENGINES if tools.engine_available(e)[0]]


def violated(facts, engine):
    return tools.check(facts, RULES, engine)["violated"]


# ---- the rules ---------------------------------------------------------------------------------------------------

def test_default_rules_are_valid_and_consistent_in_every_available_engine():
    assert [r["id"] for r in tools.validate_rules(RULES)] == ["R1", "R2", "R3"]
    for engine in AVAILABLE:
        found = tools.consistent(RULES, engine)
        assert found["consistent"] is True and all(tools.eval_expr(r["expr"], found["example"]) for r in RULES["rules"])


def test_a_contradiction_is_found_by_every_available_engine():
    contradiction = {"variables": ["a"], "rules": [{"id": "X", "expr": {"var": "a"}}, {"id": "Y", "expr": {"not": {"var": "a"}}}]}
    for engine in AVAILABLE:
        assert tools.consistent(contradiction, engine)["consistent"] is False


def test_bad_rules_are_reported_not_raised():
    for bad in ({"variables": ["a"], "rules": []},
                {"variables": ["a"], "rules": [{"id": "X", "expr": {"var": "b"}}]},
                {"variables": ["a"], "rules": [{"id": "X", "expr": {"var": "a"}}, {"id": "X", "expr": {"var": "a"}}]}):
        assert tools.check({"a": True}, bad)["status"] == "ERROR"


# ---- the engines agree -------------------------------------------------------------------------------------------

@pytest.mark.parametrize("engine", ["sympy", "z3"])
def test_each_engine_matches_the_stdlib_evaluator_on_every_assignment(engine):
    ok, why = tools.engine_available(engine)
    if not ok:
        pytest.skip(why)
    for facts in ASSIGNMENTS:
        assert violated(facts, engine) == violated(facts, "stdlib"), facts


def test_the_known_cases():
    ssn_external = {"has_ssn": True, "has_ccn": False, "is_masked": False, "is_external": True}
    assert violated(ssn_external, "stdlib") == ["R1", "R2"]
    masked_ssn_external = {**ssn_external, "is_masked": True}
    assert violated(masked_ssn_external, "stdlib") == ["R2"]                 # masking does not make an SSN releasable
    internal = {"has_ssn": True, "has_ccn": False, "is_masked": False, "is_external": False}
    assert violated(internal, "stdlib") == []
    assert violated({**internal, "has_ssn": False, "has_ccn": True}, "stdlib") == ["R3"]


def test_z3_reports_an_unsat_core_of_rule_ids():
    ok, why = tools.engine_available("z3")
    if not ok:
        pytest.skip(why)
    result = tools.check({"has_ssn": True, "has_ccn": False, "is_masked": False, "is_external": True}, RULES, "z3")
    assert set(result["core"]) <= set(result["violated"]) and result["core"]


def test_a_missing_package_says_what_to_install(monkeypatch):
    monkeypatch.setitem(__import__("sys").modules, "z3", None)
    monkeypatch.setitem(__import__("sys").modules, "sympy", None)
    assert "pip install z3-solver" in tools.check(ASSIGNMENTS[0], RULES, "z3")["error"]
    assert "pip install sympy" in tools.check(ASSIGNMENTS[0], RULES, "sympy")["error"]


# ---- facts from the LLM's PII map; failing closed ------------------------------------------------------------------

def test_facts_come_from_the_pii_map_and_the_destination():
    pii = tools.parse_pii_map_text('```json\n{"entities": [{"type": "ssn", "masked": false}, {"type": "EMAIL", "masked": true}]}\n```')
    facts = tools.derive_facts_from(pii, "External_API")
    assert {k: facts[k] for k in ("has_ssn", "has_ccn", "has_email", "is_masked", "is_external")} == {
        "has_ssn": True, "has_ccn": False, "has_email": True, "is_masked": False, "is_external": True}
    assert tools.derive_facts_from({"entities": []}, "internal_db")["is_masked"] is True      # nothing to mask


@pytest.mark.parametrize("raw", ["not json", '{"entities": "none"}', '{"people": []}', "", '{"entities": [1]}'])
def test_an_unreadable_pii_map_is_not_compliant(raw):
    result = tools.check_pii_map(tools.parse_pii_map_text(raw), "internal_db")
    assert result["compliant"] is False and result["violated"] == ["UNREADABLE_PII_MAP"]


def test_tool_results_are_json_and_engine_errors_are_a_failed_assert():
    ok = tools.check_compliance(json.dumps({"entities": []}), "internal_db", "stdlib", "")
    assert json.loads(ok)["compliant"] is True and tools.check_succeeded(ok) is True
    bad = tools.check_compliance(json.dumps({"entities": []}), "internal_db", "stdlib", "{ not rules")
    assert json.loads(bad)["status"] == "ERROR" and tools.check_succeeded(bad) is False and tools.check_succeeded("not json") is False


def test_the_check_accepts_the_models_raw_reply_and_stays_closed_on_garbage():
    """GraphLang passes the raw reply of the extraction step straight to the check."""
    fenced = '```json\n{"entities": [{"type": "SSN", "masked": false}]}\n```'
    assert json.loads(tools.check_compliance(fenced, "external_api", "stdlib", ""))["violated"] == ["R1", "R2"]
    garbage = json.loads(tools.check_compliance("Sure! Here you go.", "internal_db", "stdlib", ""))
    assert garbage["compliant"] is False and garbage["violated"] == ["UNREADABLE_PII_MAP"] and garbage["status"] == "OK"
    again = tools.parse_pii_map_text(tools.parse_pii_map(garbage_input := "nope"))
    assert again.get("parse_error")                                    # parsing a parse_error result keeps it unreadable


# ---- the workflows -----------------------------------------------------------------------------------------------------

def test_both_workflows_parse():
    from spl3._loader import load_workflows_from_file
    assert [d.name for d in load_workflows_from_file(RECIPE / "compliance_check.spl")] == ["compliance_check"]
    assert [d.name for d in load_workflows_from_file(RECIPE / "pii_compliance.spl")] == ["pii_compliance"]


@pytest.mark.parametrize("engine", ["stdlib", "sympy", "z3"])
def test_the_deterministic_workflow_runs_with_the_echo_adapter(engine):
    ok, why = tools.engine_available(engine)
    if not ok:
        pytest.skip(why)
    from spl3.cli import main
    result = CliRunner().invoke(main, [
        "run", str(RECIPE / "compliance_check.spl"), "--adapter", "echo", "--no-log",
        "--param", 'pii_map={"entities":[{"type":"SSN","masked":false}]}',
        "--param", "destination=external_api", "--param", f"engine={engine}"])
    assert result.exit_code == 0, result.output
    verdict = next(line for line in result.output.splitlines() if line.startswith("Output:")).removeprefix("Output:").strip()
    assert json.loads(verdict)["violated"] == ["R1", "R2"]


def test_the_llm_workflow_fails_closed_when_the_reply_is_not_a_pii_map():
    from spl3.cli import main
    result = CliRunner().invoke(main, ["run", str(RECIPE / "pii_compliance.spl"), "--adapter", "echo", "--no-log"])
    assert result.exit_code == 0, result.output
    assert "NOT COMPLIANT" in result.output and "UNREADABLE_PII_MAP" in result.output


# ---- your own rules: rules.json ---------------------------------------------------------------------------------------

CUSTOM = {
    "name": "Customer test policy",
    "external_destinations": ["partner_api"],
    "variables": ["has_email", "has_pii", "is_masked", "is_external"],
    "rules": [
        {"id": "E1", "desc": "No email address may go to a partner", "expr": {"not": {"and": [{"var": "has_email"}, {"var": "is_external"}]}}},
        {"id": "E2", "desc": "Anything personal sent out must be masked",
         "expr": {"implies": [{"and": [{"var": "has_pii"}, {"var": "is_external"}]}, {"var": "is_masked"}]}},
    ],
}


def test_the_default_rules_come_from_rules_json_next_to_the_tools():
    assert tools.RULES_FILE == RECIPE / "rules.json" and tools.DEFAULT_RULES == json.loads((RECIPE / "rules.json").read_text())
    assert tools.DEFAULT_RULES["external_destinations"] == ["external_api", "third_party_vendor"]


def test_custom_rules_use_more_facts_and_their_own_external_destinations(tmp_path):
    path = tmp_path / "mine.json"
    path.write_text(json.dumps(CUSTOM))
    rules = tools.load_rules_file(str(path))
    pii = {"entities": [{"type": "email", "masked": False}]}
    for engine in AVAILABLE:
        partner = tools.check_pii_map(pii, "partner_api", engine, rules)
        assert partner["violated"] == ["E1", "E2"], engine                       # partner_api is external in THIS file
        assert tools.check_pii_map(pii, "external_api", engine, rules)["compliant"] is True   # but external_api is not
        masked = tools.check_pii_map({"entities": [{"type": "EMAIL", "masked": True}]}, "partner_api", engine, rules)
        assert masked["violated"] == ["E1"]


def test_a_bad_rules_file_is_reported_not_replaced_by_the_defaults(tmp_path):
    cases = {"missing.json": None, "notjson.json": "{ nope", "unknown_fact.json": json.dumps({**CUSTOM, "variables": ["has_nope"]}),
             "no_rules.json": json.dumps({"variables": [], "rules": []})}
    for name, text in cases.items():
        path = tmp_path / name
        if text is not None:
            path.write_text(text)
        with pytest.raises(ValueError):
            tools.load_rules_file(str(path))
        loaded = tools.load_rules(str(path))
        assert "error" in json.loads(loaded)
        verdict = json.loads(tools.check_compliance(json.dumps({"entities": []}), "internal_db", "stdlib", loaded))
        assert verdict["status"] == "ERROR" and verdict["error"] and tools.check_succeeded(json.dumps(verdict)) is False


def test_the_workflow_runs_with_a_rules_file_parameter(tmp_path):
    from spl3.cli import main
    path = tmp_path / "mine.json"
    path.write_text(json.dumps(CUSTOM))
    result = CliRunner().invoke(main, [
        "run", str(RECIPE / "compliance_check.spl"), "--adapter", "echo", "--no-log",
        "--param", 'pii_map={"entities":[{"type":"EMAIL","masked":false}]}', "--param", "destination=partner_api",
        "--param", f"rules_file={path}"])
    assert result.exit_code == 0, result.output
    verdict = next(line for line in result.output.splitlines() if line.startswith("Output:")).removeprefix("Output:").strip()
    assert json.loads(verdict)["violated"] == ["E1", "E2"]


def test_tools_py_checks_a_rules_file_from_the_command_line(tmp_path):
    import subprocess
    import sys
    good = subprocess.run([sys.executable, str(RECIPE / "tools.py")], capture_output=True, text=True)
    assert good.returncode == 0 and "3 rules" in good.stdout and "[stdlib] consistent" in good.stdout
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({**CUSTOM, "variables": ["has_nope"]}))
    bad = subprocess.run([sys.executable, str(RECIPE / "tools.py"), str(path)], capture_output=True, text=True)
    assert bad.returncode == 1 and "INVALID" in bad.stdout and "undeclared" in bad.stdout
