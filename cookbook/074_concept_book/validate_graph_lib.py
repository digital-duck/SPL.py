"""Regression oracle: graph_lib + {domain}_graph.yaml ≡ the frozen domain modules.

Recipe 71's `linalg_graph.py` (and recipe 73's `geometry_graph.py`) are
"fully vested" — working, tested, frozen, deliberately untouched by this
recipe. This script is the proof obligation that the YAML-driven
generalization in `graph_lib.py` is *behaviorally identical*, not just
similar: for every algorithm and accessor, the YAML-driven path must produce
the exact same graph structure and the exact same outputs as the original
module's hardcoded path, for both domains.

Run:
    python validate_graph_lib.py

Exit code 0 and "ALL CHECKS PASSED" ⇒ graph_lib.py + {domain}_graph.yaml is a
provably faithful generalization of linalg_graph.py / geometry_graph.py —
recipe 71 (already validated, already running) becomes the oracle that
certifies the new generic path, exactly as the user intended.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent.parent

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "cookbook" / "71_linalg_concept_book"))
sys.path.insert(0, str(ROOT / "cookbook" / "73_intro_geometry"))

import graph_lib as gl  # noqa: E402


_FAILURES: list[str] = []


def _check(label: str, actual, expected) -> None:
    if actual == expected:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}")
        print(f"       actual:   {actual!r}")
        print(f"       expected: {expected!r}")
        _FAILURES.append(label)


def _graphs_equal(g1, g2) -> bool:
    """Structural equality: same nodes (+ attrs) and same edges."""
    if set(g1.nodes()) != set(g2.nodes()):
        return False
    if set(g1.edges()) != set(g2.edges()):
        return False
    for n in g1.nodes():
        if dict(g1.nodes[n]) != dict(g2.nodes[n]):
            print(f"       node attr mismatch on {n!r}:")
            print(f"         yaml-driven: {dict(g1.nodes[n])!r}")
            print(f"         frozen:      {dict(g2.nodes[n])!r}")
            return False
    return True


def validate_domain(domain_label: str, yaml_name: str, frozen_module,
                     sample_target: str, sample_learner_state: list[str]) -> None:
    print(f"\n=== {domain_label} ===")

    data = gl.load_domain(yaml_name)
    g_yaml = gl.build(data)
    g_frozen = frozen_module.build()

    _check(f"{domain_label}: graph structurally equal (nodes+edges+attrs)",
           _graphs_equal(g_yaml, g_frozen), True)
    _check(f"{domain_label}: node count", g_yaml.number_of_nodes(), g_frozen.number_of_nodes())
    _check(f"{domain_label}: edge count", g_yaml.number_of_edges(), g_frozen.number_of_edges())

    _check(f"{domain_label}: acyclic", gl.acyclic(g_yaml), frozen_module.acyclic(g_frozen))

    first_yaml = gl.first_radical_primitives(data)
    both_yaml = gl.both_radical_primitives(data)
    _check(f"{domain_label}: first_radical_primitives", first_yaml, frozen_module.first_radical_primitives())
    _check(f"{domain_label}: both_radical_primitives", both_yaml, frozen_module.both_radical_primitives())
    _check(f"{domain_label}: concept_names", gl.concept_names(data), frozen_module.concept_names())
    _check(f"{domain_label}: primitive_names", gl.primitive_names(data), frozen_module.primitive_names())

    _check(f"{domain_label}: reducible(first_radical)",
           gl.reducible(g_yaml, first_yaml), frozen_module.reducible(g_frozen, frozen_module.first_radical_primitives()))
    _check(f"{domain_label}: reducible(both_radical)",
           gl.reducible(g_yaml, both_yaml), frozen_module.reducible(g_frozen, frozen_module.both_radical_primitives()))
    _check(f"{domain_label}: minimal(both_radical)",
           gl.minimal(both_yaml, data), frozen_module.minimal(both_yaml))

    _check(f"{domain_label}: ancestors({sample_target!r})",
           gl.ancestors(g_yaml, sample_target), frozen_module.ancestors(g_frozen, sample_target))
    _check(f"{domain_label}: applications_of({sample_target!r})",
           gl.applications_of(g_yaml, sample_target), frozen_module.applications_of(g_frozen, sample_target))
    _check(f"{domain_label}: in_graph({sample_target!r})",
           gl.in_graph(g_yaml, sample_target), frozen_module.in_graph(g_frozen, sample_target))

    for weight in (1.0, 1.5, 2.0):
        _check(f"{domain_label}: productivity_order(weight={weight})",
               gl.productivity_order(g_yaml, weight=weight),
               frozen_module.productivity_order(g_frozen, weight=weight))

    _check(f"{domain_label}: gap({sample_target!r}, {sample_learner_state!r})",
           gl.gap(g_yaml, sample_target, sample_learner_state),
           frozen_module.gap(g_frozen, sample_target, sample_learner_state))
    _check(f"{domain_label}: learning_path({sample_target!r}, {sample_learner_state!r})",
           gl.learning_path(g_yaml, sample_target, sample_learner_state),
           frozen_module.learning_path(g_frozen, sample_target, sample_learner_state))

    sample_section = f"This section introduces {sample_target.replace('_', ' ')} and its primitives."
    _check(f"{domain_label}: new_primitives(sample_section, both_radical)",
           gl.new_primitives(sample_section, both_yaml),
           frozen_module.new_primitives(sample_section, frozen_module.both_radical_primitives()))


def main() -> None:
    import linalg_graph
    import geometry_graph

    validate_domain(
        "linalg", "linalg_graph.yaml", linalg_graph,
        sample_target="spectral_theorem",
        sample_learner_state=["vector_addition", "scalar_multiplication", "linear_combination"],
    )
    validate_domain(
        "intro_geometry", "geometry_graph.yaml", geometry_graph,
        sample_target="trigonometric_ratios",
        sample_learner_state=["point", "line", "distance"],
    )

    print()
    if _FAILURES:
        print(f"FAILED — {len(_FAILURES)} check(s) did not match:")
        for f in _FAILURES:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("ALL CHECKS PASSED — graph_lib.py + {domain}_graph.yaml ≡ frozen domain modules")


if __name__ == "__main__":
    main()
