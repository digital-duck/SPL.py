"""Tests for the chinese_characters domain (chinese_characters_graph.yaml).

The first non-mathematical domain in recipe 74 — its oracle is the graph
itself (`verify_character_lego`, verifier: "structural"), not a CAS. The
load-bearing structural fact mirrors mechanics' kinematics/dynamics split:
the graph is NOT reducible from the 11 semantic pictograms (first radical)
alone — the sound-lender 马 (second radical) is irreducible content, which
is exactly the 形声 (phono-semantic) thesis machine-checked.
"""

import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cookbook" / "74_domain_textbook"))

import graph_lib  # noqa: E402

YAML = "chinese_characters_graph.yaml"


@pytest.fixture(scope="module")
def domain():
    return graph_lib.load_domain(YAML)


@pytest.fixture(scope="module")
def graph(domain):
    return graph_lib.build(domain)


class TestDomainShape:
    def test_domain_name(self, domain):
        assert domain["domain"] == "chinese_characters"

    def test_two_radicals(self, domain):
        # First radical: FORM (semantic pictograms). Second: SOUND (马).
        assert len(domain["first_radical_primitives"]) == 11
        assert "马" not in domain["first_radical_primitives"]
        both = graph_lib.both_radical_primitives(domain)
        assert len(both) == 12
        assert "马" in both

    def test_counts(self, domain, graph):
        assert len(domain["primitives"]) == 12
        assert len(domain["concepts"]) == 16  # 13 characters + 3 principles
        assert len(domain["applications"]) == 5
        assert graph.number_of_nodes() == 33
        assert graph.number_of_edges() == 42

    def test_target_concept_present(self, domain):
        assert "phono_semantic_principle" in domain["concepts"]


class TestGraphInvariants:
    def test_acyclic(self, graph):
        assert graph_lib.acyclic(graph)

    def test_reducible_from_both_radicals(self, domain, graph):
        assert graph_lib.reducible(graph, graph_lib.both_radical_primitives(domain))

    def test_not_reducible_from_semantic_bricks_alone(self, domain, graph):
        # Writing-system fact encoded in the graph: the phonetic series
        # (妈, 吗) is not derivable from FORM pictograms alone — the sound
        # lender 马 is genuinely new content, the way dynamics is not
        # derivable from kinematics in mechanics_graph.yaml.
        assert not graph_lib.reducible(graph, graph_lib.first_radical_primitives(domain))

    def test_productivity_order_respects_dependencies(self, graph):
        order = graph_lib.productivity_order(graph, weight=1.5)
        idx = {n: i for i, n in enumerate(order)}
        assert idx["林"] < idx["森"]
        assert idx["从"] < idx["众"]
        assert idx["妈"] < idx["phonetic_borrowing"]
        assert idx["semantic_composition"] < idx["phono_semantic_principle"]
        assert idx["phonetic_borrowing"] < idx["phono_semantic_principle"]

    def test_ancestors_of_target(self, graph):
        needed = graph_lib.ancestors(graph, "phono_semantic_principle")
        for node in ("semantic_composition", "phonetic_borrowing",
                     "妈", "沐", "休", "马", "木"):
            assert node in needed, node

    def test_learning_path_scoping(self, graph):
        # A learner who has the meaning-stacking characters still needs the
        # whole phonetic series. gap() = ancestors(target) − mastered, so the
        # path excludes both mastered characters and the target itself.
        known = {"休", "明", "好", "林", "从", "安", "字", "森", "众", "晶",
                 "semantic_composition"}
        path = graph_lib.learning_path(graph, "phono_semantic_principle", known)
        for node in ("沐", "妈", "吗", "phonetic_borrowing"):
            assert node in path, node
        assert "休" not in path
        assert "phono_semantic_principle" not in path


class TestVerifierDeclarations:
    def test_all_concepts_structural(self, domain):
        for name, attrs in domain["concepts"].items():
            assert attrs["verifier"] == "structural", name

    def test_lego_claim_lab_on_target(self, domain):
        assert "graph_lib.reducible" in domain["concepts"]["phono_semantic_principle"]["lab"]

    def test_character_labs_name_the_verifier(self, domain):
        assert "verify_character_lego" in domain["concepts"]["休"]["lab"]


class TestStructuralVerifier:
    def test_semantic_compound(self, domain):
        assert graph_lib.verify_character_lego("休", domain) == "pass (structural)"

    def test_tripling_multiset(self, domain):
        # 森: composed_of [木, 林] but pieces [木, 木, 木] — multiplicity
        # lives in pieces, the set cross-check is against the graph.
        assert graph_lib.verify_character_lego("森", domain) == "pass (structural)"

    def test_phono_semantic_compound(self, domain):
        assert graph_lib.verify_character_lego("妈", domain) == "pass (structural)"

    def test_primitive_is_its_own_decomposition(self, domain):
        assert graph_lib.verify_character_lego("木", domain) == "pass (structural)"

    def test_principle_node_without_pieces(self, domain):
        assert graph_lib.verify_character_lego(
            "phono_semantic_principle", domain) == "pass (structural)"

    def test_every_node_passes(self, domain, graph):
        # The LEGO claim, exhaustively: every node in the graph verifies.
        for node in graph.nodes():
            assert graph_lib.verify_character_lego(node, domain) == \
                "pass (structural)", node

    def test_unknown_character_fails(self, domain):
        out = graph_lib.verify_character_lego("猫", domain)
        assert out.startswith("fail:")

    def test_wrong_pieces_fail(self, domain):
        tampered = copy.deepcopy(domain)
        tampered["concepts"]["妈"]["pieces"] = ["女", "口"]
        out = graph_lib.verify_character_lego("妈", tampered)
        assert out.startswith("fail:") and "马" in out

    def test_undeclared_brick_fails(self, domain):
        tampered = copy.deepcopy(domain)
        tampered["concepts"]["休"]["pieces"] = ["人", "亻"]
        out = graph_lib.verify_character_lego("休", tampered)
        assert out.startswith("fail:") and "亻" in out

    def test_verify_content_structural_engine(self, domain):
        # The .spl-facing dispatcher must accept the per-node verifier
        # declaration without trying to import a CAS named "structural".
        out = graph_lib.verify_content("sample section", domain,
                                       verifier="structural")
        assert out == "pass (structural)"
