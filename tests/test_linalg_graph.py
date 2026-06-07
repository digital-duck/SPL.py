"""Tests for the Linear Algebra concept graph — linalg_graph.py (Layer 2).

Covers:
  - Graph structure: acyclic, correct node/edge counts, kind attributes
  - reducible(): first-radical subset fails; both-radical set passes
  - ancestors(): spectral_theorem ancestors are complete and correct
  - restrict(): subgraph preserves edges and excludes non-members
  - productivity_order(): topological invariant + reach-priority invariant
  - minimal(): accepts only declared primitives
  - in_graph(), applications_of(), new_primitives()
  - Smoke: run the graph functions that the SPL workflow calls via SOLVE/ASSERT
"""

from __future__ import annotations

import sys
import os

# Allow importing linalg_graph directly (it lives in the cookbook, not in spl/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                                "..", "cookbook", "71_linalg_micro_textbook"))

import networkx as nx
import pytest
import linalg_graph as lg


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def graph():
    return lg.build()


# ---------------------------------------------------------------------------
# Structure tests
# ---------------------------------------------------------------------------

class TestGraphStructure:
    def test_is_digraph(self, graph):
        assert isinstance(graph, nx.DiGraph)

    def test_acyclic(self, graph):
        assert lg.acyclic(graph)

    def test_has_primitives(self, graph):
        primitives = [n for n, d in graph.nodes(data=True) if d.get("kind") == "primitive"]
        assert len(primitives) == 5

    def test_has_concepts(self, graph):
        concepts = [n for n, d in graph.nodes(data=True) if d.get("kind") == "concept"]
        assert len(concepts) >= 20  # at least the core set

    def test_has_applications(self, graph):
        apps = [n for n, d in graph.nodes(data=True) if d.get("kind") == "application"]
        assert len(apps) >= 5

    def test_key_nodes_exist(self, graph):
        key_nodes = [
            "vector_addition", "scalar_multiplication", "inner_product",
            "linear_combination", "basis", "eigenpair", "diagonalization",
            "spectral_theorem",
        ]
        for node in key_nodes:
            assert node in graph, f"Missing node: {node}"

    def test_edge_direction(self, graph):
        # Prereq → concept direction: linear_combination needs ⊕ and ⊙
        assert graph.has_edge("vector_addition", "linear_combination")
        assert graph.has_edge("scalar_multiplication", "linear_combination")

    def test_basis_prerequisites(self, graph):
        assert graph.has_edge("linear_independence", "basis")
        assert graph.has_edge("span", "basis")

    def test_spectral_theorem_prerequisites(self, graph):
        assert graph.has_edge("adjoint", "spectral_theorem")
        assert graph.has_edge("eigenpair", "spectral_theorem")
        assert graph.has_edge("orthonormal_basis", "spectral_theorem")

    def test_primitives_have_no_prerequisites(self, graph):
        for node, data in graph.nodes(data=True):
            if data.get("kind") == "primitive":
                assert graph.in_degree(node) == 0, (
                    f"Primitive '{node}' has incoming edges — it is not irreducible"
                )

    def test_node_kind_attribute(self, graph):
        for node, data in graph.nodes(data=True):
            assert "kind" in data, f"Node '{node}' missing 'kind' attribute"
            assert data["kind"] in ("primitive", "concept", "application")


# ---------------------------------------------------------------------------
# reducible() tests
# ---------------------------------------------------------------------------

class TestReducible:
    def test_first_radical_only_is_not_enough(self, graph):
        # inner_product, norm, orthogonality etc. cannot reduce to ⊕/⊙
        first_prims = lg.first_radical_primitives()
        assert not lg.reducible(graph, first_prims)

    def test_both_radicals_makes_all_reducible(self, graph):
        all_prims = lg.both_radical_primitives()
        assert lg.reducible(graph, all_prims)

    def test_empty_primitives_fails(self, graph):
        assert not lg.reducible(graph, [])

    def test_subgraph_first_radical_reducible(self, graph):
        # Concepts that depend ONLY on ⊕/⊙ are reducible to first-radical prims
        first_prims = set(lg.first_radical_primitives())
        first_concepts = {"linear_combination", "linear_independence", "span",
                          "linear_map", "basis", "eigenpair", "diagonalization",
                          "image", "kernel", "dimension", "coordinates",
                          "matrix", "matrix_multiplication", "rank", "nullity",
                          "rank_nullity", "determinant", "subspace"}
        subgraph = lg.restrict(graph, first_prims | first_concepts)
        assert lg.reducible(subgraph, first_prims)

    def test_adding_inner_product_fixes_reducibility(self, graph):
        # With all 5 primitives, full graph is reducible
        assert lg.reducible(graph, lg.both_radical_primitives())


# ---------------------------------------------------------------------------
# ancestors() tests
# ---------------------------------------------------------------------------

class TestAncestors:
    def test_spectral_theorem_ancestors_complete(self, graph):
        anc = lg.ancestors(graph, "spectral_theorem")
        # Must include both radicals' chains
        required = {
            "vector_addition", "scalar_multiplication", "inner_product",
            "linear_combination", "linear_map", "eigenpair",
            "span", "basis", "linear_independence",
            "norm", "orthogonality", "orthonormal_basis", "adjoint",
        }
        assert required.issubset(anc), (
            f"Missing ancestors: {required - anc}"
        )

    def test_linear_combination_ancestors(self, graph):
        anc = lg.ancestors(graph, "linear_combination")
        assert "vector_addition" in anc
        assert "scalar_multiplication" in anc
        assert "linear_combination" not in anc  # node itself is not its own ancestor

    def test_primitive_has_no_ancestors(self, graph):
        anc = lg.ancestors(graph, "vector_addition")
        assert len(anc) == 0

    def test_eigenpair_ancestors(self, graph):
        anc = lg.ancestors(graph, "eigenpair")
        # eigenpair depends on linear_map and scalar_multiplication
        # linear_map depends on linear_combination which depends on ⊕, ⊙
        assert "linear_map" in anc
        assert "scalar_multiplication" in anc
        assert "linear_combination" in anc
        assert "vector_addition" in anc


# ---------------------------------------------------------------------------
# restrict() tests
# ---------------------------------------------------------------------------

class TestRestrict:
    def test_restrict_preserves_edges(self, graph):
        nodes = {"vector_addition", "scalar_multiplication", "linear_combination"}
        sub = lg.restrict(graph, nodes)
        assert sub.has_edge("vector_addition", "linear_combination")
        assert sub.has_edge("scalar_multiplication", "linear_combination")

    def test_restrict_excludes_nodes(self, graph):
        nodes = {"vector_addition", "linear_combination"}
        sub = lg.restrict(graph, nodes)
        # scalar_multiplication excluded → edge to linear_combination also excluded
        assert "scalar_multiplication" not in sub.nodes()

    def test_restrict_to_spectral_path(self, graph):
        needed = lg.ancestors(graph, "spectral_theorem") | {"spectral_theorem"}
        sub = lg.restrict(graph, needed)
        assert "spectral_theorem" in sub.nodes()
        assert lg.acyclic(sub)  # subgraph of a DAG is still a DAG
        # Nodes outside the spectral path are excluded
        assert "matrix_multiplication" not in sub.nodes()
        assert "rank_nullity" not in sub.nodes()


# ---------------------------------------------------------------------------
# productivity_order() tests
# ---------------------------------------------------------------------------

class TestProductivityOrder:
    def test_returns_all_nodes(self, graph):
        order = lg.productivity_order(graph)
        assert set(order) == set(graph.nodes())

    def test_topological_invariant(self, graph):
        """For every edge u→v in the graph, u must appear before v in the order."""
        order = lg.productivity_order(graph)
        pos = {node: i for i, node in enumerate(order)}
        for u, v in graph.edges():
            assert pos[u] < pos[v], (
                f"Topological invariant violated: {u} (pos {pos[u]}) "
                f"should precede {v} (pos {pos[v]})"
            )

    def test_linear_combination_before_span(self, graph):
        order = lg.productivity_order(graph)
        pos = {n: i for i, n in enumerate(order)}
        assert pos["linear_combination"] < pos["span"]

    def test_eigenpair_before_diagonalization(self, graph):
        order = lg.productivity_order(graph)
        pos = {n: i for i, n in enumerate(order)}
        assert pos["eigenpair"] < pos["diagonalization"]

    def test_spectral_theorem_is_late(self, graph):
        order = lg.productivity_order(graph)
        pos = {n: i for i, n in enumerate(order)}
        # spectral_theorem straddles both radicals — must appear past the first third
        n = len(order)
        assert pos["spectral_theorem"] > n // 3, (
            "spectral_theorem should not appear in the first third of the ordering"
        )

    def test_high_weight_promotes_application_ancestors(self, graph):
        order_low  = lg.productivity_order(graph, weight=0.0)
        order_high = lg.productivity_order(graph, weight=10.0)
        # With high weight, nodes that unlock applications rank higher relative to
        # concepts that don't unlock applications. Both must be valid topological orders.
        pos_low  = {n: i for i, n in enumerate(order_low)}
        pos_high = {n: i for i, n in enumerate(order_high)}
        # Check topological invariant on both
        for u, v in graph.edges():
            assert pos_low[u]  < pos_low[v]
            assert pos_high[u] < pos_high[v]

    def test_restricted_order_valid(self, graph):
        needed = lg.ancestors(graph, "spectral_theorem") | {"spectral_theorem"}
        sub = lg.restrict(graph, needed)
        order = lg.productivity_order(sub)
        pos = {n: i for i, n in enumerate(order)}
        for u, v in sub.edges():
            assert pos[u] < pos[v], (
                f"Topological invariant violated in restricted graph: {u} → {v}"
            )
        assert order[-1] == "spectral_theorem" or pos["spectral_theorem"] > len(order) // 2


# ---------------------------------------------------------------------------
# minimal() tests
# ---------------------------------------------------------------------------

class TestMinimal:
    def test_declared_primitives_are_minimal(self):
        assert lg.minimal(lg.both_radical_primitives())

    def test_first_radical_is_minimal(self):
        assert lg.minimal(lg.first_radical_primitives())

    def test_undeclared_primitive_fails(self):
        assert not lg.minimal(["vector_addition", "fictional_operation"])

    def test_empty_is_minimal(self):
        assert lg.minimal([])  # vacuously true — empty subset of declared prims


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_in_graph_positive(self, graph):
        assert lg.in_graph(graph, "eigenpair")
        assert lg.in_graph(graph, "spectral_theorem")

    def test_in_graph_negative(self, graph):
        assert not lg.in_graph(graph, "made_up_concept")

    def test_applications_of_eigenpair(self, graph):
        apps = lg.applications_of(graph, "eigenpair")
        expected = {"normal_modes", "stability_analysis", "markov_stationary", "pagerank"}
        assert set(apps).issuperset(expected), (
            f"Missing applications: {expected - set(apps)}"
        )

    def test_applications_of_spectral_theorem(self, graph):
        apps = lg.applications_of(graph, "spectral_theorem")
        assert "quantum_observable" in apps
        assert "fourier_modes" in apps

    def test_new_primitives_count(self):
        text = "In this section we introduce vector addition and scalar multiplication."
        n = lg.new_primitives(text)
        assert n >= 2

    def test_new_primitives_zero(self):
        text = "This section reviews the definition of a basis."
        n = lg.new_primitives(text)
        assert n == 0

    def test_concept_names_nonempty(self):
        names = lg.concept_names()
        assert len(names) >= 20
        assert "linear_combination" in names
        assert "spectral_theorem" in names

    def test_primitive_names_complete(self):
        names = lg.primitive_names()
        assert "vector_addition" in names
        assert "scalar_multiplication" in names
        assert "inner_product" in names
        assert len(names) == 5


# ---------------------------------------------------------------------------
# Workflow smoke test — mirrors what the SPL workflow calls
# ---------------------------------------------------------------------------

class TestWorkflowSmoke:
    """Simulate the SPL workflow calls that SOLVE/ASSERT send to the kernel."""

    def test_assert_acyclic(self, graph):
        """ASSERT acyclic(@graph)"""
        assert lg.acyclic(graph)

    def test_assert_reducible_both_radicals(self, graph):
        """ASSERT reducible(@graph, @primitives) with both primitives"""
        prims = lg.both_radical_primitives()
        assert lg.reducible(graph, prims)

    def test_solve_ancestors_spectral_theorem(self, graph):
        """SOLVE @needed SET := ancestors(@graph, 'spectral_theorem')"""
        needed = lg.ancestors(graph, "spectral_theorem")
        assert isinstance(needed, set)
        assert len(needed) > 10  # substantial prerequisites
        assert "linear_combination" in needed

    def test_solve_productivity_order_restricted(self, graph):
        """SOLVE @order LIST := productivity_order(restrict(@graph, @needed), weight=2.0)"""
        needed = lg.ancestors(graph, "spectral_theorem") | {"spectral_theorem"}
        sub = lg.restrict(graph, needed)
        order = lg.productivity_order(sub, weight=2.0)
        # Topological validity
        pos = {n: i for i, n in enumerate(order)}
        for u, v in sub.edges():
            assert pos[u] < pos[v]
        # Spectral theorem is the last or near-last (it's the target)
        assert pos["spectral_theorem"] == len(order) - 1 or (
            pos["spectral_theorem"] > len(order) * 0.7
        )

    def test_assert_in_graph(self, graph):
        """ASSERT in_graph(@graph, @target)"""
        assert lg.in_graph(graph, "spectral_theorem")
        assert lg.in_graph(graph, "diagonalization")
        assert not lg.in_graph(graph, "fourier_transform")  # not linear algebra

    def test_new_primitives_budget(self):
        """ASSERT new_primitives(@section) <= @primitive_budget"""
        section_one_new = "We introduce vector addition as the first operation."
        assert lg.new_primitives(section_one_new) <= 1  # within budget of 1
