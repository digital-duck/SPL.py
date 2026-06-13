"""Tests for the english_morphology domain (english_morphology_graph.yaml).

Sibling pilot to chinese_characters_graph.yaml — two writing systems, one
schema, ONE verifier: `verify_character_lego` checks both with zero code
changes (Structured Word Inquiry's "word sums" ARE the `pieces` lists). The
load-bearing structural fact is the same theorem 马 proves for Chinese: the
graph is NOT reducible from the 5 roots (first radical, FORM) alone — the
affix system (second radical, OPERATOR) is irreducible content.
"""

import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cookbook" / "74_concept_book"))

import graph_lib  # noqa: E402

YAML = "english_morphology_graph.yaml"


@pytest.fixture(scope="module")
def domain():
    return graph_lib.load_domain(YAML)


@pytest.fixture(scope="module")
def graph(domain):
    return graph_lib.build(domain)


class TestDomainShape:
    def test_domain_name(self, domain):
        assert domain["domain"] == "english_morphology"

    def test_two_radicals(self, domain):
        # First radical: FORM (roots). Second: OPERATOR (prefixes + suffixes).
        assert domain["first_radical_primitives"] == [
            "spect", "port", "dict", "struct", "ject",
        ]
        both = graph_lib.both_radical_primitives(domain)
        assert len(both) == 13
        for affix in ("re-", "in-", "con-", "trans-", "pre-", "-ion", "-or", "-able"):
            assert affix in both, affix

    def test_counts(self, domain, graph):
        assert len(domain["primitives"]) == 13  # 5 roots + 5 prefixes + 3 suffixes
        assert len(domain["concepts"]) == 18  # 14 words + 3 principles + capstone
        assert len(domain["applications"]) == 5
        assert graph.number_of_nodes() == 36
        assert graph.number_of_edges() == 51

    def test_target_concept_present(self, domain):
        assert "morphological_decoding_principle" in domain["concepts"]


class TestGraphInvariants:
    def test_acyclic(self, graph):
        assert graph_lib.acyclic(graph)

    def test_reducible_from_both_radicals(self, domain, graph):
        assert graph_lib.reducible(graph, graph_lib.both_radical_primitives(domain))

    def test_not_reducible_from_roots_alone(self, domain, graph):
        # Writing-system fact encoded in the graph: no pile of roots ever
        # yields "inspection" — the affix system is genuinely new content,
        # the way 马 is for Chinese and dynamics is for mechanics.
        assert not graph_lib.reducible(graph, graph_lib.first_radical_primitives(domain))

    def test_productivity_order_respects_dependencies(self, graph):
        order = graph_lib.productivity_order(graph, weight=1.5)
        idx = {n: i for i, n in enumerate(order)}
        assert idx["inspect"] < idx["inspection"]
        assert idx["construct"] < idx["construction"] < idx["reconstruction"]
        assert idx["import"] < idx["allomorphy"]
        assert idx["allomorphy"] < idx["morphological_decoding_principle"]
        assert idx["suffix_derivation"] < idx["morphological_decoding_principle"]

    def test_ancestors_of_target(self, graph):
        needed = graph_lib.ancestors(graph, "morphological_decoding_principle")
        for node in ("prefix_root_composition", "suffix_derivation", "allomorphy",
                     "inspect", "import", "inspection", "spect", "in-", "-ion"):
            assert node in needed, node

    def test_learning_path_scoping(self, graph):
        # A learner who owns the tier-1 words still needs the derived layer
        # and all three principles; mastered words and the target itself are
        # excluded (gap() = ancestors(target) − mastered).
        known = {"inspect", "transport", "predict", "construct", "reject", "portable"}
        path = graph_lib.learning_path(graph, "morphological_decoding_principle", known)
        for node in ("import", "inspection", "inspector", "allomorphy",
                     "prefix_root_composition", "suffix_derivation"):
            assert node in path, node
        assert "inspect" not in path
        assert "morphological_decoding_principle" not in path


class TestVerifierDeclarations:
    def test_all_concepts_structural(self, domain):
        for name, attrs in domain["concepts"].items():
            assert attrs["verifier"] == "structural", name

    def test_lego_claim_lab_on_target(self, domain):
        assert "graph_lib.reducible" in \
            domain["concepts"]["morphological_decoding_principle"]["lab"]

    def test_word_labs_name_the_verifier(self, domain):
        assert "verify_character_lego" in domain["concepts"]["inspect"]["lab"]


class TestStructuralVerifier:
    def test_prefix_root_word(self, domain):
        assert graph_lib.verify_character_lego("inspect", domain) == "pass (structural)"

    def test_suffix_stacking_multiset(self, domain):
        # inspection: composed_of [inspect, -ion] but pieces [in-, spect, -ion]
        # — the word sum is the full brick multiset, the graph cross-check is
        # against the derived primitive set.
        assert graph_lib.verify_character_lego("inspection", domain) == "pass (structural)"

    def test_double_prefix_word(self, domain):
        # reconstruction: four bricks via [re-, construction] — the 森 of
        # this graph.
        assert graph_lib.verify_character_lego("reconstruction", domain) == "pass (structural)"

    def test_allomorph_word(self, domain):
        # import: pieces say [in-, port] even though the surface says im- —
        # the brick is the unit, not its spelling.
        assert graph_lib.verify_character_lego("import", domain) == "pass (structural)"

    def test_primitive_is_its_own_decomposition(self, domain):
        assert graph_lib.verify_character_lego("spect", domain) == "pass (structural)"

    def test_principle_node_without_pieces(self, domain):
        assert graph_lib.verify_character_lego(
            "morphological_decoding_principle", domain) == "pass (structural)"

    def test_every_node_passes(self, domain, graph):
        # The LEGO claim, exhaustively: every word sum in the graph verifies.
        for node in graph.nodes():
            assert graph_lib.verify_character_lego(node, domain) == \
                "pass (structural)", node

    def test_wrong_word_sum_fails(self, domain):
        tampered = copy.deepcopy(domain)
        tampered["concepts"]["inspection"]["pieces"] = ["in-", "spect"]  # dropped -ion
        out = graph_lib.verify_character_lego("inspection", tampered)
        assert out.startswith("fail:") and "-ion" in out

    def test_undeclared_brick_fails(self, domain):
        tampered = copy.deepcopy(domain)
        tampered["concepts"]["reject"]["pieces"] = ["re-", "iact"]  # not a declared brick
        out = graph_lib.verify_character_lego("reject", tampered)
        assert out.startswith("fail:") and "iact" in out

    def test_verify_content_structural_engine(self, domain):
        out = graph_lib.verify_content("sample section", domain,
                                       verifier="structural")
        assert out == "pass (structural)"
