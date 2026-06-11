"""Tests for the classical_mechanics domain (mechanics_graph.yaml).

The first domain authored *after* the verifier ladder shipped — it exercises
Sage verifiers from day one: exact ℚ recomputation (momentum, energy),
symbolic differentiation (SHO), and a Sage-only manifolds node
(configuration_space → classical_mechanics_seed).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cookbook" / "74_domain_textbook"))

import graph_lib  # noqa: E402

YAML = "mechanics_graph.yaml"


def _sage_available() -> bool:
    try:
        import sage.all  # noqa: F401
        return True
    except Exception:
        return False


ENGINE = "sage" if _sage_available() else "sympy"


@pytest.fixture(scope="module")
def domain():
    return graph_lib.load_domain(YAML)


@pytest.fixture(scope="module")
def graph(domain):
    return graph_lib.build(domain)


class TestDomainShape:
    def test_domain_name(self, domain):
        assert domain["domain"] == "classical_mechanics"

    def test_two_radicals(self, domain):
        # First radical: kinematics. Second: dynamics.
        assert domain["first_radical_primitives"] == ["position", "time"]
        assert graph_lib.both_radical_primitives(domain) == [
            "position", "time", "mass", "force",
        ]

    def test_counts(self, domain, graph):
        assert len(domain["primitives"]) == 4
        assert len(domain["concepts"]) == 19
        assert len(domain["applications"]) == 5
        assert graph.number_of_nodes() == 28

    def test_target_concept_present(self, domain):
        assert "normal_modes" in domain["concepts"]


class TestGraphInvariants:
    def test_acyclic(self, graph):
        assert graph_lib.acyclic(graph)

    def test_reducible_from_both_radicals(self, domain, graph):
        assert graph_lib.reducible(graph, graph_lib.both_radical_primitives(domain))

    def test_not_reducible_from_kinematics_alone(self, domain, graph):
        # Physics fact encoded in the graph: dynamics (mass, force) is not
        # derivable from kinematics (position, time).
        assert not graph_lib.reducible(graph, graph_lib.first_radical_primitives(domain))

    def test_productivity_order_respects_dependencies(self, graph):
        order = graph_lib.productivity_order(graph, weight=1.5)
        idx = {n: i for i, n in enumerate(order)}
        assert idx["velocity"] < idx["acceleration"]
        assert idx["kinetic_energy"] < idx["lagrangian"]
        assert idx["harmonic_oscillator"] < idx["normal_modes"]
        assert idx["euler_lagrange_equations"] < idx["normal_modes"]

    def test_ancestors_of_target(self, graph):
        needed = graph_lib.ancestors(graph, "normal_modes")
        for concept in ("harmonic_oscillator", "euler_lagrange_equations",
                        "lagrangian", "newtons_second_law", "velocity"):
            assert concept in needed, concept

    def test_learning_path_scoping(self, graph):
        # A learner who knows kinematics + energy still needs the
        # configuration-space chain. gap() = ancestors(target) − mastered,
        # so the path excludes both mastered concepts and the target itself
        # (the target's own section is generated separately — recipe 71).
        known = {"velocity", "acceleration", "kinetic_energy", "potential_energy"}
        path = graph_lib.learning_path(graph, "lagrangian", known)
        assert "generalized_coordinates" in path
        assert "configuration_space" in path
        assert "velocity" not in path
        assert "lagrangian" not in path


class TestVerifierDeclarations:
    def test_fallback_tier_nodes(self, domain):
        concepts = domain["concepts"]
        for node in ("momentum", "energy_conservation",
                     "harmonic_oscillator", "normal_modes"):
            assert concepts[node]["verifier"] == "sage|sympy", node

    def test_sage_only_manifolds_node(self, domain):
        # configuration_space needs SageManifolds — the fail-fast case.
        assert domain["concepts"]["configuration_space"]["verifier"] == "sage"
        assert "classical_mechanics_seed" in domain["concepts"]["configuration_space"]["lab"]


class TestExactMechanicsVerifiers:
    def test_momentum_conservation_pass(self):
        # 2·3 + 1·0 == 2·1 + 1·4 == 6
        out = graph_lib.verify_momentum_conservation(2, 3, 1, 0, 1, 4)
        assert out == f"pass ({ENGINE})"

    def test_momentum_conservation_fail(self):
        out = graph_lib.verify_momentum_conservation(2, 3, 1, 0, 1, 5)
        assert out.startswith("fail:") and "6" in out and "7" in out

    def test_energy_conservation_pass(self):
        # m=2, g=10: drop from rest at h=5 → v=10 at h=0 (E = 100 exactly)
        out = graph_lib.verify_energy_conservation(2, 10, 0, 5, 10, 0)
        assert out == f"pass ({ENGINE})"

    def test_energy_conservation_rational_data(self):
        # Half-unit data stays exact: m=1/2, g=10, h₀=4/5 → v₁²=16, E=4
        out = graph_lib.verify_energy_conservation("1/2", 10, 0, "4/5", 4, 0)
        assert out == f"pass ({ENGINE})"

    def test_energy_conservation_fail(self):
        out = graph_lib.verify_energy_conservation(2, 10, 0, 5, 9, 0)
        assert out.startswith("fail:")

    def test_sho_general_solution(self):
        out = graph_lib.verify_sho_solution()  # A*cos(w*t) + B*sin(w*t)
        assert out == f"pass ({ENGINE})"

    def test_sho_wrong_frequency_fails_symbolically(self):
        out = graph_lib.verify_sho_solution("A*cos(2*w*t)")
        assert out.startswith("fail:")

    def test_forced_sympy_engine(self):
        assert graph_lib.verify_sho_solution(verifier="sympy") == "pass (sympy)"
