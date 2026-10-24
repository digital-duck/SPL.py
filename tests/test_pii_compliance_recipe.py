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
def test_each_engine_matches_the_plain_evaluator_on_every_assignment(engine):
    ok, why = tools.engine_available(engine)
    if not ok:
        pytest.skip(why)
    for facts in ASSIGNMENTS:
        assert violated(facts, engine) == violated(facts, "plain"), facts


def test_the_known_cases():
    ssn_external = {"has_ssn": True, "has_ccn": False, "is_masked": False, "is_external": True}
    assert violated(ssn_external, "plain") == ["R1", "R2"]
    masked_ssn_external = {**ssn_external, "is_masked": True}
    assert violated(masked_ssn_external, "plain") == ["R2"]                 # masking does not make an SSN releasable
    internal = {"has_ssn": True, "has_ccn": False, "is_masked": False, "is_external": False}
    assert violated(internal, "plain") == []
    assert violated({**internal, "has_ssn": False, "has_ccn": True}, "plain") == ["R3"]


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
    assert facts == {"has_ssn": True, "has_ccn": False, "is_masked": False, "is_external": True}
    assert tools.derive_facts_from({"entities": []}, "internal_db")["is_masked"] is True      # nothing to mask


@pytest.mark.parametrize("raw", ["not json", '{"entities": "none"}', '{"people": []}', "", '{"entities": [1]}'])
def test_an_unreadable_pii_map_is_not_compliant(raw):
    result = tools.check_pii_map(tools.parse_pii_map_text(raw), "internal_db")
    assert result["compliant"] is False and result["violated"] == ["UNREADABLE_PII_MAP"]


def test_tool_results_are_json_and_engine_errors_are_a_failed_assert():
    ok = tools.check_compliance(json.dumps({"entities": []}), "internal_db", "plain", "")
    assert json.loads(ok)["compliant"] is True and tools.check_succeeded(ok) is True
    bad = tools.check_compliance("{", "internal_db", "plain", "")
    assert tools.check_succeeded(bad) is False and tools.check_succeeded("not json") is False


# ---- the workflows -----------------------------------------------------------------------------------------------------

def test_both_workflows_parse():
    from spl3._loader import load_workflows_from_file
    assert [d.name for d in load_workflows_from_file(RECIPE / "compliance_check.spl")] == ["compliance_check"]
    assert [d.name for d in load_workflows_from_file(RECIPE / "pii_compliance.spl")] == ["pii_compliance"]


@pytest.mark.parametrize("engine", ["plain", "sympy", "z3"])
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
