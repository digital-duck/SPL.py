"""Tests for the tool-advocacy concept-book domains.

E-book concept graphs (publisher: Digital Duck) — the trilogy
"Book I finds it, Book II proves it, Book III measures it":
  - sage_learning_graph.yaml  — "Doing Math in SageMath Lab"      (2026-06-10)
  - lean_proving_graph.yaml   — "Proving Math the Lean Way"       (2026-06-10)
  - python_science_graph.yaml — "Doing Science with Python"       (2026-06-11)

Both compile through recipe 74 (build_concept_book.spl --lang
python/domain_textbook) with zero engine changes — the test of the
generalization claim is that *authoring a textbook is writing YAML*.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cookbook" / "74_concept_book"))

import graph_lib  # noqa: E402

DOMAINS = {
    "sage_learning_graph.yaml": {
        "domain": "sage_learning",
        "first_radical": ["exact_integer", "exact_rational"],
        "target": "experimental_mathematics",
        "target_needs": ["conjecture_loop", "manifolds_geometry", "group_theory_sage"],
    },
    "lean_proving_graph.yaml": {
        "domain": "lean_proving",
        "first_radical": ["type", "term"],
        "target": "ai_assisted_proving",
        "target_needs": ["formalization_gap", "automation_tactics", "sorry_first_workflow"],
    },
    "python_science_graph.yaml": {
        "domain": "python_science",
        "first_radical": ["array", "floating_point"],
        "target": "reproducible_science",
        "target_needs": ["model_validation", "numerical_integration_odes", "visualization"],
    },
}


@pytest.fixture(scope="module", params=sorted(DOMAINS))
def case(request):
    yaml_name = request.param
    data = graph_lib.load_domain(yaml_name)
    return DOMAINS[yaml_name], data, graph_lib.build(data)


class TestDomainShape:
    def test_domain_name(self, case):
        expect, data, _ = case
        assert data["domain"] == expect["domain"]

    def test_radicals(self, case):
        expect, data, _ = case
        assert data["first_radical_primitives"] == expect["first_radical"]
        assert len(data["primitives"]) == 4

    def test_target_present_with_dependencies(self, case):
        expect, data, _ = case
        target = data["concepts"][expect["target"]]
        assert target["composed_of"] == expect["target_needs"]

    def test_every_application_needs_known_nodes(self, case):
        _, data, _ = case
        known = set(data["primitives"]) | set(data["concepts"])
        for app, attrs in data["applications"].items():
            for need in attrs["needs"]:
                assert need in known, f"{app} needs unknown node {need}"


class TestGraphInvariants:
    def test_acyclic(self, case):
        _, _, graph = case
        assert graph_lib.acyclic(graph)

    def test_reducible_from_both_radicals(self, case):
        _, data, graph = case
        assert graph_lib.reducible(graph, graph_lib.both_radical_primitives(data))

    def test_not_reducible_from_first_radical_alone(self, case):
        # Same structural fact in all three 2026-06-10 domains: the second
        # radical (structure / proofs) is genuinely independent of the first.
        _, data, graph = case
        assert not graph_lib.reducible(graph, graph_lib.first_radical_primitives(data))

    def test_target_pulls_most_of_the_graph(self, case):
        # The capstone should require the bulk of the curriculum.
        expect, data, graph = case
        needed = graph_lib.ancestors(graph, expect["target"])
        assert len(needed) >= len(data["concepts"]) * 2 // 3

    def test_productivity_order_covers_all_nodes(self, case):
        _, _, graph = case
        order = graph_lib.productivity_order(graph, weight=1.5)
        assert len(order) == graph.number_of_nodes()


class TestVerifierDeclarations:
    def test_sage_domain_is_sage_first(self):
        data = graph_lib.load_domain("sage_learning_graph.yaml")
        verifiers = {c["verifier"] for c in data["concepts"].values()}
        assert verifiers <= {"sage", "sage|sympy"}

    def test_lean_domain_declares_lean_fallback(self):
        data = graph_lib.load_domain("lean_proving_graph.yaml")
        for name, c in data["concepts"].items():
            assert c["verifier"] == "lean|sympy", name

    def test_lean_engine_dispatch(self):
        # "lean|sympy": lean when spl3.lean_bridge is importable (Part B),
        # sympy fallback otherwise — never a hard fail either way.
        out = graph_lib.verify_content(
            "section", {"domain": "lean_proving"}, verifier="lean|sympy"
        )
        assert out in ("pass (lean)", "pass (sympy)")

    def test_python_science_each_concept_verified_by_its_own_library(self):
        # The book's signature: every concept's verifier IS the library it
        # teaches, and the generic engine dispatch resolves each one.
        data = graph_lib.load_domain("python_science_graph.yaml")
        allowed = {"numpy", "sympy", "scipy", "pandas", "sklearn", "matplotlib"}
        for name, c in data["concepts"].items():
            assert c["verifier"] in allowed, name
            out = graph_lib.verify_content(
                "section", {"domain": "python_science"}, verifier=c["verifier"]
            )
            assert out == f"pass ({c['verifier']})", name
