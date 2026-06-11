"""graph_lib — shared, YAML-driven concept-graph algorithm library.

Part of recipe 74 (`cookbook/74_domain_textbook/`) — the proof that the
"concept graph → micro-textbook" pattern recipes 71/73 each ship a frozen,
domain-specific copy of (`linalg_graph.py` / `geometry_graph.py`) is actually
ONE domain-agnostic algorithm library plus a thin per-domain *data* file.

Recipe 71's `linalg_graph.py` is "fully vested" — working, tested, frozen —
and deliberately left untouched here. Instead, `{domain}_graph.yaml` files
in this directory hold the SAME domain content (generated losslessly from
the existing modules — see `generate_domain_yaml.py`), and every algorithm
below is the domain-agnostic half of `linalg_graph.py`/`geometry_graph.py`,
generalized to take that loaded data as an explicit argument instead of
reading a module-level `_PRIMITIVES`/`_CONCEPTS`/`_APPLICATIONS` global.

Public API
----------
load_domain(yaml_path)              → dict   (raw domain data: primitives/concepts/applications/...)
build(domain_data)                  → networkx.DiGraph
acyclic(graph)                      → bool
reducible(graph, primitives)        → bool
minimal(primitives, domain_data)    → bool
in_graph(graph, target)             → bool
ancestors(graph, target)            → set[str]
restrict(graph, needed)             → networkx.DiGraph
applications_of(graph, target)      → list[str]
new_primitives(section, primitives) → int
productivity_order(graph, weight)   → list[str]
gap(graph, target, learner_state)   → set[str]
learning_path(graph, target, ...)   → list[str]
first_radical_primitives(domain_data) → list[str]
both_radical_primitives(domain_data)  → list[str]
concept_names(domain_data)            → list[str]
primitive_names(domain_data)          → list[str]
verify_content(section, domain_data)  → str   (single generic symbolic-check stub)

Graph conventions — IDENTICAL to linalg_graph.py / geometry_graph.py
--------------------------------------------------------------------
Node attributes:
    kind       : "primitive" | "concept" | "application"
    tier       : int (0 = primitive floor; higher = more composed)
    composed_of: list[str] (direct prerequisites; empty for primitives)
    ... plus whatever domain-specific keys the YAML carries through verbatim
        (symbol, defines, verifier, lab, play, introduced_in, domain, needs, ...)

Edge direction:
    u → v  means  "u is a prerequisite of v"
    (primitives are sources; targets/applications are sinks)
"""

from __future__ import annotations

import heapq
from pathlib import Path
from typing import Any, Iterable

import networkx as nx
import yaml


# ---------------------------------------------------------------------------
# Domain data loading
# ---------------------------------------------------------------------------

def load_domain(yaml_path: str | Path) -> dict[str, Any]:
    """Load a `{domain}_graph.yaml` file into the raw domain-data dict.

    Returns a dict shaped like::

        {
            "domain": "linalg",
            "primitives": {name: {attrs...}, ...},
            "concepts":   {name: {"composed_of": [...], attrs...}, ...},
            "applications": {name: {"needs": [...], attrs...}, ...},
            "first_radical_primitives": [name, ...],
        }

    — the same shape `build()` and the data-driven accessors below expect,
    generated losslessly from `_PRIMITIVES`/`_CONCEPTS`/`_APPLICATIONS` (see
    `generate_domain_yaml.py`). Resolved relative to this file's directory
    when given a bare filename, so callers don't need to know where recipe
    74 lives on disk.
    """
    path = Path(yaml_path)
    if not path.is_absolute() and not path.exists():
        path = Path(__file__).parent / path
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


# ---------------------------------------------------------------------------
# Graph builder — generalized from linalg_graph.build()/geometry_graph.build()
# ---------------------------------------------------------------------------

def build(domain_data: dict[str, Any]) -> nx.DiGraph:
    """Build and return the full concept graph for a loaded domain.

    Nodes carry all metadata from the raw data dicts plus a ``kind``
    attribute. Edges u → v mean "u is a prerequisite of v". Identical
    construction to `linalg_graph.build()` / `geometry_graph.build()`,
    generalized to read from `domain_data` instead of module globals.
    """
    G = nx.DiGraph()

    for name, attrs in domain_data.get("primitives", {}).items():
        G.add_node(name, kind="primitive", composed_of=[], **attrs)

    for name, attrs in domain_data.get("concepts", {}).items():
        composed_of = attrs.get("composed_of", [])
        node_attrs = {k: v for k, v in attrs.items() if k != "composed_of"}
        G.add_node(name, kind="concept", composed_of=composed_of, **node_attrs)
        for prereq in composed_of:
            G.add_edge(prereq, name)

    for name, attrs in domain_data.get("applications", {}).items():
        needs = attrs.get("needs", [])
        node_attrs = {k: v for k, v in attrs.items() if k != "needs"}
        G.add_node(name, kind="application", composed_of=needs, **node_attrs)
        for prereq in needs:
            G.add_edge(prereq, name)

    return G


# ---------------------------------------------------------------------------
# Graph algorithms — copied verbatim from linalg_graph.py (domain-agnostic;
# operate purely on the built nx.DiGraph, never on raw domain data)
# ---------------------------------------------------------------------------

def acyclic(graph: nx.DiGraph) -> bool:
    """Return True if the graph has no cycles (valid composition hierarchy)."""
    return nx.is_directed_acyclic_graph(graph)


def reducible(graph: nx.DiGraph, primitives: Iterable[str]) -> bool:
    """Return True if every concept/application reduces transitively to primitives.

    A node is reducible iff every "leaf" (in-degree 0 node) in its ancestor
    closure is a declared primitive. Any undeclared leaf signals a concept
    that claims to be primitive but was not declared.
    """
    prim_set = set(primitives)
    for node in graph.nodes():
        if graph.nodes[node].get("kind") == "primitive":
            continue
        anc = nx.ancestors(graph, node)
        sources = {n for n in anc if graph.in_degree(n) == 0}
        if not sources.issubset(prim_set):
            return False
    return True


def minimal(primitives: Iterable[str], domain_data: dict[str, Any]) -> bool:
    """Return True if all supplied names are declared primitives for this domain.

    Generalized from `linalg_graph.minimal()`, which checked against the
    module-level `_PRIMITIVES` global — here the declared set comes from the
    loaded `domain_data` instead.
    """
    prim_set = set(primitives)
    declared = set(domain_data.get("primitives", {}).keys())
    return prim_set.issubset(declared)


def in_graph(graph: nx.DiGraph, target: str) -> bool:
    """Return True if target names a node in the graph."""
    return target in graph.nodes()


def ancestors(graph: nx.DiGraph, target: str) -> set[str]:
    """Return the composed-of closure — all nodes that transitively feed target."""
    return nx.ancestors(graph, target)


def restrict(graph: nx.DiGraph, needed: Iterable[str]) -> nx.DiGraph:
    """Return the subgraph induced by the given node set.

    Only nodes in *needed* are kept; edges between them are preserved.
    """
    return graph.subgraph(set(needed)).copy()


def applications_of(graph: nx.DiGraph, target: str) -> list[str]:
    """Return applications that directly depend on target."""
    return [
        n for n in graph.successors(target)
        if graph.nodes[n].get("kind") == "application"
    ]


def new_primitives(section: str, primitives: Iterable[str]) -> int:
    """Count how many primitive names appear in a section text.

    Used to enforce the ``primitive_budget`` rule: a section should not
    introduce more new radicals than the budget allows. Generalized from
    `linalg_graph.new_primitives()` — `primitives` is now a required
    argument (was an optional fallback to the module-level `_PRIMITIVES`
    global; callers pass `both_radical_primitives(domain_data)` instead).
    """
    section_lower = section.lower()
    count = 0
    for prim in primitives:
        canonical = prim.replace("_", " ")
        if canonical in section_lower or prim in section_lower:
            count += 1
    return count


# ---------------------------------------------------------------------------
# productivity_order — reach-weighted topological sort (verbatim)
# ---------------------------------------------------------------------------

def productivity_order(graph: nx.DiGraph, weight: float = 1.0) -> list[str]:
    """Return concepts in order: topological, tie-broken by payoff-weighted reach.

    reach(c) = (# concepts c is ancestor of) + weight * (# applications c is ancestor of)

    A concept with high reach "unlocks" many downstream concepts and
    applications when learned — it should be taught as early as topology
    allows. Implementation: modified Kahn's algorithm with a max-heap
    priority queue. Identical to `linalg_graph.productivity_order()`.
    """
    reach: dict[str, float] = {}
    for node in graph.nodes():
        desc = nx.descendants(graph, node)
        n_concepts = sum(1 for d in desc if graph.nodes[d].get("kind") == "concept")
        n_apps = sum(1 for d in desc if graph.nodes[d].get("kind") == "application")
        reach[node] = n_concepts + weight * n_apps

    in_deg: dict[str, int] = dict(graph.in_degree())
    heap: list[tuple[float, str]] = []
    for n, d in in_deg.items():
        if d == 0:
            heapq.heappush(heap, (-reach[n], n))

    result: list[str] = []
    while heap:
        _, node = heapq.heappop(heap)
        result.append(node)
        for succ in graph.successors(node):
            in_deg[succ] -= 1
            if in_deg[succ] == 0:
                heapq.heappush(heap, (-reach[succ], succ))

    return result


def gap(graph: nx.DiGraph, target: str, learner_state: Iterable[str]) -> set[str]:
    """Concepts needed to reach target that the learner has not yet mastered.

    Returns ancestors(graph, target) minus learner_state.
    """
    return ancestors(graph, target).difference(set(learner_state))


def learning_path(graph: nx.DiGraph, target: str, learner_state: Iterable[str],
                  weight: float = 1.0) -> list[str]:
    """Productivity-ordered list of concepts a learner still needs for target.

    Equivalent to productivity_order(restrict(graph, gap(graph, target, learner_state))).
    """
    needed = gap(graph, target, learner_state)
    if not needed:
        return []
    return productivity_order(restrict(graph, needed), weight=weight)


# ---------------------------------------------------------------------------
# Domain-data accessors — generalized from linalg_graph.py's module-global
# convenience functions (`first_radical_primitives`, `both_radical_primitives`,
# `concept_names`, `primitive_names`) to read from the loaded `domain_data`
# instead. Behavior is identical; only the source of truth moved from a
# Python module global to a YAML-loaded dict.
# ---------------------------------------------------------------------------

def first_radical_primitives(domain_data: dict[str, Any]) -> list[str]:
    """Return the curated "first radical only" primitive subset for this domain.

    This is genuinely domain-specific *content* (a hand-picked subset, not a
    derived quantity) — e.g. linalg's `[field_of_scalars, carrier_set,
    vector_addition, scalar_multiplication]` or geometry's `[point, line,
    plane, distance]` — so it is declared explicitly in the YAML rather than
    computed.
    """
    return list(domain_data.get("first_radical_primitives", []))


def both_radical_primitives(domain_data: dict[str, Any]) -> list[str]:
    """Return all declared primitives for this domain (both radicals)."""
    return list(domain_data.get("primitives", {}).keys())


def concept_names(domain_data: dict[str, Any]) -> list[str]:
    """Return all concept names in declaration order."""
    return list(domain_data.get("concepts", {}).keys())


def primitive_names(domain_data: dict[str, Any]) -> list[str]:
    """Return all primitive names in declaration order."""
    return list(domain_data.get("primitives", {}).keys())


# ---------------------------------------------------------------------------
# Generic verifier — the single symbolic-check shape every domain plugs into
# ---------------------------------------------------------------------------

def verify_content(section: str, domain_data: dict[str, Any],
                   verifier: str = "") -> str:
    """Domain-dispatched symbolic check. Returns 'pass' or a failure description.

    Recipes 71/73 each declare their own verifier(s) (`verify_math` +
    `shape_check`, `verify_geometry`) because their oracles are genuinely
    different SymPy submodules. Recipe 74's whole point is ONE `.spl` source
    compiling against *either* domain, so it needs ONE verifier shape; this
    dispatches on `domain_data["domain"]` to the right SymPy presence-check —
    proving the *shape* generalizes even though the oracle's specifics
    (worked-example recompute, geometry recompute, ...) remain TODO stubs in
    71/73 too. A third domain adds a branch here, not a new `.spl` construct.

    `verifier` (optional) is an explicit engine override, matching the
    per-node `verifier:` YAML attribute ("sympy" | "z3" | "numpy" | "sage" |
    "sage|sympy"). "sage" dispatches to SageMath; "sage|sympy" prefers Sage
    and falls back to SymPy when Sage is absent (the fallback-tiering policy —
    see SPL.py/docs/DEV/sage_lean_integration_plan.md §A.2). When empty, the
    domain default applies.
    """
    engines = [e.strip() for e in verifier.split("|") if e.strip()] or ["_domain_default"]
    last_exc: Exception | None = None
    for engine in engines:
        try:
            if engine == "sage":
                import sage.all  # noqa: F401 — presence check
            elif engine == "_domain_default":
                if domain_data.get("domain", "") == "intro_geometry":
                    import sympy.geometry  # noqa: F401 — presence check
                else:
                    import sympy  # noqa: F401 — presence check
            else:  # sympy / z3 / numpy
                __import__("sympy" if engine == "sympy" else engine)
            # TODO: parse claims from section and recompute per-domain
            return "pass" if engine == "_domain_default" else f"pass ({engine})"
        except Exception as exc:
            last_exc = exc
    return f"fail: {last_exc}"


# ---------------------------------------------------------------------------
# Quick smoke-test (python graph_lib.py <domain_yaml>)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    yaml_name = sys.argv[1] if len(sys.argv) > 1 else "linalg_graph.yaml"
    data = load_domain(yaml_name)
    graph = build(data)
    print(f"Domain: {data.get('domain')}")
    print(f"Nodes: {graph.number_of_nodes()}  Edges: {graph.number_of_edges()}")
    print(f"Acyclic: {acyclic(graph)}")
    first = first_radical_primitives(data)
    both = both_radical_primitives(data)
    print(f"Reducible (first radical {first}): {reducible(graph, first)}")
    print(f"Reducible (both radicals {both}): {reducible(graph, both)}")
    order = productivity_order(graph, weight=2.0)
    print(f"\nProductivity order ({len(order)} nodes):")
    for i, n in enumerate(order, 1):
        kind = graph.nodes[n].get("kind", "?")
        print(f"  {i:2}. [{kind:12}] {n}")
