"""Intro Geometry concept graph — python/intro_geometry domain library.

Part of the ``python/intro_geometry`` splc target (Layer 2 of the
neurosymbolic SPL roadmap — see cookbook/71_linalg_micro_textbook for the
first instance of this pattern, ``linalg_graph.py``).  Loaded into the
IPython kernel at workflow start:

    CALL run_python('import sys; sys.path.insert(0, "/path/to/cookbook/73_intro_geometry")') INTO @_
    CALL run_python('import geometry_graph; graph = geometry_graph.build()') INTO @_

Public API
----------
build()                             → networkx.DiGraph (the full concept graph)
reducible(graph, primitives)        → bool
acyclic(graph)                      → bool
minimal(primitives)                 → bool
ancestors(graph, target)            → set[str]
restrict(graph, needed)             → networkx.DiGraph
productivity_order(graph, weight)   → list[str]
new_primitives(section, primitives) → int
in_graph(graph, target)             → bool
applications_of(graph, target)      → list[str]

Graph conventions
-----------------
Node attributes:
    kind       : "primitive" | "concept" | "application"
    tier       : int (0 = primitive floor; higher = more composed)
    defines    : str (one-line definition)
    composed_of: list[str] (direct prerequisites; empty for primitives)
    verifier   : str (tool that checks worked examples: "sympy")
    lab        : str (interactive tool for the student cell)
    play       : str (suggested exploration)
    introduced_in: str (module where this primitive first appears)
    domain     : str (for applications: the external field)

Edge direction:
    u → v  means  "u is a prerequisite of v"
    (primitives are sources; targets/applications are sinks)

Two radicals, one meeting point
-------------------------------
Mirroring linalg_graph's ⊕/⊙ vs ⟨·,·⟩ split, intro geometry has two
irreducible measurement primitives that *cannot* be reduced to one another:

    distance  — the metric radical: "how far apart?"   (first radical)
    angle     — the rotational radical: "how much turn?" (second radical)

They are independent — you can measure length without ever mentioning angle,
and vice versa — until **trigonometric_ratios**, where the ratio of two
side-lengths (distance) becomes a function of an angle measure (angle), and
that ratio turns out to be invariant under similarity.  That is this graph's
``spectral_theorem``: the concept where both radicals meet and a payoff
(navigation, surveying, astronomy, …) becomes possible.
"""

from __future__ import annotations

import heapq
from typing import Iterable

import networkx as nx


# ---------------------------------------------------------------------------
# Raw data — primitives, concepts, applications
# ---------------------------------------------------------------------------

# Primitive declarations: the irreducible "radicals".
# Below this floor we do not reduce (analogous to base SI dimensions).
_PRIMITIVES: dict[str, dict] = {
    "point": {
        "symbol": "P",
        "defines": "the floor for location — an undefined notion; everything else is built from collections of points",
        "tier": 0,
    },
    "line": {
        "symbol": "ℓ",
        "defines": "the floor for straightness — an undefined notion of infinite extent with no width",
        "tier": 0,
    },
    "plane": {
        "symbol": "π",
        "defines": "the floor for flatness — an undefined notion of two-dimensional extent; the ambient space everything else lives in",
        "tier": 0,
    },
    "distance": {
        "symbol": "d(A,B)",
        "defines": "first radical — the metric; assigns a non-negative number to every pair of points",
        "tier": 0,
    },
    "angle": {
        "symbol": "∠ABC",
        "defines": "second radical — rotation; assigns a measure to the turning between two rays sharing a vertex; not reducible to distance",
        "tier": 0,
        "introduced_in": "trigonometry",
    },
}

# Concept declarations: composed from primitives or other concepts.
# Each entry lists its immediate `composed_of` prerequisites.
_CONCEPTS: dict[str, dict] = {
    # ── First radical: distance ─────────────────────────────────────────
    "line_segment": {
        "composed_of": ["point", "line", "distance"],
        "defines": "bounded portion of a line between two endpoints; its length is the distance between them",
        "verifier": "sympy",
        "lab": "sympy.geometry",
        "play": "place two points; measure the segment; slide one and watch the length change",
        "tier": 1,
    },
    "ray": {
        "composed_of": ["point", "line"],
        "defines": "half-line: an endpoint together with all points of a line on one side of it",
        "verifier": "sympy",
        "lab": "sympy.geometry",
        "tier": 1,
    },
    # ── Second radical: angle ───────────────────────────────────────────
    "angle_measure": {
        "composed_of": ["angle"],
        "defines": "the numeric value of an angle (degrees); classified acute / right / obtuse / straight / reflex",
        "verifier": "sympy",
        "lab": "sympy.geometry",
        "tier": 1,
    },
    "parallel_lines": {
        "composed_of": ["line", "angle_measure"],
        "defines": "coplanar lines that never meet; a transversal makes corresponding and alternate-interior angles equal",
        "verifier": "sympy",
        "lab": "sympy.geometry",
        "tier": 2,
    },
    "polygon": {
        "composed_of": ["line_segment", "angle_measure"],
        "defines": "closed plane figure bounded by line segments — has vertices, sides, and interior angles",
        "verifier": "sympy",
        "lab": "sympy.geometry",
        "tier": 2,
    },
    "rigid_motion": {
        "composed_of": ["distance", "angle"],
        "defines": "a transformation of the plane (translation, rotation, reflection) that preserves both distance and angle measure — the floor for 'sameness of shape'",
        "verifier": "sympy",
        "lab": "sympy.geometry",
        "play": "translate, rotate, and reflect a triangle; verify side lengths and angles are unchanged",
        "tier": 2,
    },
    "triangle": {
        "composed_of": ["polygon"],
        "defines": "three-sided polygon; interior angles always sum to 180°",
        "verifier": "sympy",
        "lab": "sympy.geometry",
        "tier": 3,
    },
    "congruence": {
        "composed_of": ["rigid_motion"],
        "defines": "two figures related by a rigid motion — 'same size and same shape', written ≅",
        "verifier": "sympy",
        "lab": "sympy.geometry",
        "tier": 3,
    },
    "circle": {
        "composed_of": ["point", "distance"],
        "defines": "set of all points at a fixed distance (the radius) from a center point",
        "verifier": "sympy",
        "lab": "sympy.geometry",
        "play": "vary the radius; compute circumference and area; check the ratio C/d is always π",
        "tier": 3,
    },
    "triangle_congruence_criteria": {
        "composed_of": ["triangle", "congruence"],
        "defines": "SSS, SAS, ASA, AAS — minimal sets of equal measurements that force two triangles to be congruent",
        "verifier": "sympy",
        "lab": "sympy.geometry",
        "tier": 4,
    },
    "similarity": {
        "composed_of": ["rigid_motion", "angle_measure"],
        "defines": "rigid motion composed with a uniform scaling (dilation) — preserves angle measure and ratios of distances; 'same shape, possibly different size', written ∼",
        "verifier": "sympy",
        "lab": "sympy.geometry",
        "tier": 4,
    },
    "quadrilateral": {
        "composed_of": ["polygon", "parallel_lines"],
        "defines": "four-sided polygon — parallelograms, trapezoids, rectangles, rhombi, squares, classified by which sides/angles are equal or parallel",
        "verifier": "sympy",
        "lab": "sympy.geometry",
        "tier": 4,
    },
    "coordinate_plane": {
        "composed_of": ["point", "distance"],
        "defines": "Cartesian (x, y) representation of the plane — every point becomes an ordered pair of numbers",
        "verifier": "sympy",
        "lab": "sympy.geometry",
        "tier": 4,
    },
    "triangle_similarity_criteria": {
        "composed_of": ["triangle", "similarity"],
        "defines": "AA, SAS∼, SSS∼ — minimal sets of equal angles or proportional sides that force two triangles to be similar",
        "verifier": "sympy",
        "lab": "sympy.geometry",
        "tier": 5,
    },
    "area": {
        "composed_of": ["polygon", "distance"],
        "defines": "measure of the two-dimensional region enclosed by a polygon or circle",
        "verifier": "sympy",
        "lab": "sympy.geometry",
        "play": "decompose an irregular polygon into triangles; sum their areas; compare to the shoelace formula",
        "tier": 5,
    },
    "pythagorean_theorem": {
        "composed_of": ["triangle_congruence_criteria", "area"],
        "defines": "in a right triangle, a² + b² = c² — the metric radical (side lengths) meets the rotational radical (the right angle) for the first time",
        "verifier": "sympy",
        "lab": "sympy.geometry",
        "play": "build right triangles with integer sides; verify a**2 + b**2 == c**2 for Pythagorean triples",
        "tier": 6,
    },
    "circle_theorems": {
        "composed_of": ["circle", "angle_measure", "congruence"],
        "defines": "inscribed angle, central angle, tangent–chord, and arc–chord relationships — angle measure governs the geometry of circles",
        "verifier": "sympy",
        "lab": "sympy.geometry",
        "tier": 5,
    },
    "distance_formula": {
        "composed_of": ["coordinate_plane", "pythagorean_theorem"],
        "defines": "d = √((x₂−x₁)² + (y₂−y₁)²) — the Pythagorean theorem restated in coordinates",
        "verifier": "sympy",
        "lab": "sympy.geometry",
        "play": "plot two points; compute the distance both via the formula and via Point.distance(); compare",
        "tier": 7,
    },
    "trigonometric_ratios": {
        "composed_of": ["triangle_similarity_criteria", "pythagorean_theorem"],
        "defines": "sin, cos, tan — ratios of side lengths (distance) determined entirely by an acute angle (angle) in a right triangle; the ratio is invariant under similarity — both radicals meet here",
        "verifier": "sympy",
        "lab": "sympy.geometry",
        "play": "build similar right triangles at different scales; verify sin/cos/tan of the shared angle is the same in each",
        "tier": 8,
    },
}

# Application declarations: external edges — the payoff, pointing out of intro geometry.
_APPLICATIONS: dict[str, dict] = {
    "navigation_surveying": {
        "needs": ["trigonometric_ratios", "distance_formula"],
        "domain": "navigation and land surveying",
        "defines": "GPS trilateration and surveying triangulation both reduce to solving triangles with trigonometric ratios and the distance formula",
    },
    "architecture_construction": {
        "needs": ["pythagorean_theorem", "area", "similarity"],
        "domain": "architecture and structural engineering",
        "defines": "squaring foundations (3-4-5 triangles), computing material quantities (area), and scaling blueprints (similarity)",
    },
    "computer_graphics": {
        "needs": ["rigid_motion", "coordinate_plane", "similarity"],
        "domain": "computer graphics and game design",
        "defines": "every on-screen animation is a composition of rigid motions and similarity transformations on coordinate data",
    },
    "astronomy": {
        "needs": ["trigonometric_ratios", "circle_theorems"],
        "domain": "astronomy",
        "defines": "measuring distances to celestial objects via parallax and triangulation — trigonometric ratios applied at planetary scale",
    },
    "art_and_design": {
        "needs": ["rigid_motion", "congruence", "similarity"],
        "domain": "art, design, and architecture ornament",
        "defines": "tessellation, perspective drawing, and logo scaling are rigid motions and similarity transformations made visible",
    },
}


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build() -> nx.DiGraph:
    """Build and return the full intro-geometry concept graph.

    Nodes carry all metadata from the raw data dicts plus a ``kind`` attribute.
    Edges u → v mean "u is a prerequisite of v".

    Returns
    -------
    networkx.DiGraph
        The complete concept + application graph with all metadata attached
        as node attributes.
    """
    G = nx.DiGraph()

    # Add primitive nodes
    for name, attrs in _PRIMITIVES.items():
        G.add_node(name, kind="primitive", composed_of=[], **attrs)

    # Add concept nodes and edges
    for name, attrs in _CONCEPTS.items():
        composed_of = attrs.get("composed_of", [])
        node_attrs = {k: v for k, v in attrs.items() if k != "composed_of"}
        G.add_node(name, kind="concept", composed_of=composed_of, **node_attrs)
        for prereq in composed_of:
            G.add_edge(prereq, name)  # prereq → concept

    # Add application nodes and edges
    for name, attrs in _APPLICATIONS.items():
        needs = attrs.get("needs", [])
        node_attrs = {k: v for k, v in attrs.items() if k != "needs"}
        G.add_node(name, kind="application", composed_of=needs, **node_attrs)
        for prereq in needs:
            G.add_edge(prereq, name)  # prereq → application

    return G


# ---------------------------------------------------------------------------
# Verifier functions (deterministic — the symbolic half of the workflow)
# ---------------------------------------------------------------------------
#
# These eleven functions (through `learning_path`) are domain-agnostic graph
# algorithms — byte-for-byte the same operations linalg_graph.py runs, just
# against this graph's data.  That repetition is intentional, not laziness:
# cookbook/70's readme makes the same case for "two near-identical scripts"
# (each domain library must be runnable standalone, with no shared-module
# coupling that could let two domains' notions of "ancestors" silently
# diverge).  If a third domain library repeats them again, *that* is the
# signal to factor this block into a shared `concept_graph_ops.py` —
# three is the line between "duplication that protects independence" and
# "duplication that should be a library".

def acyclic(graph: nx.DiGraph) -> bool:
    """Return True if the graph has no cycles (valid composition hierarchy)."""
    return nx.is_directed_acyclic_graph(graph)


def reducible(graph: nx.DiGraph, primitives: Iterable[str]) -> bool:
    """Return True if every concept/application reduces transitively to primitives.

    A node is reducible iff every "leaf" (in-degree 0 node) in its ancestor
    closure is a declared primitive.  Any undeclared leaf signals a concept
    that claims to be primitive but was not declared.

    Parameters
    ----------
    graph     : the concept graph (as returned by build())
    primitives: the declared primitive names to accept as irreducible leaves
    """
    prim_set = set(primitives)
    for node in graph.nodes():
        if graph.nodes[node].get("kind") == "primitive":
            continue
        # ancestors(graph, node) = all nodes from which `node` is reachable
        anc = nx.ancestors(graph, node)
        # Sources in the ancestor closure = nodes with no incoming edges there
        sources = {n for n in anc if graph.in_degree(n) == 0}
        if not sources.issubset(prim_set):
            return False
    return True


def minimal(primitives: Iterable[str]) -> bool:
    """Return True if all supplied names are declared primitives.

    A minimal basis uses only the declared irreducible radicals — no concept
    is claimed to be primitive if it can be composed from others.
    """
    prim_set = set(primitives)
    declared = set(_PRIMITIVES.keys())
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


def new_primitives(section: str, primitives: Iterable[str] | None = None) -> int:
    """Count how many primitive names appear in a section text.

    Used to enforce the ``primitive_budget`` rule: a section should not
    introduce more new radicals than the budget allows.
    """
    if primitives is None:
        primitives = list(_PRIMITIVES.keys())
    section_lower = section.lower()
    count = 0
    for prim in primitives:
        canonical = prim.replace("_", " ")
        if canonical in section_lower or prim in section_lower:
            count += 1
    return count


# ---------------------------------------------------------------------------
# productivity_order — reach-weighted topological sort
# ---------------------------------------------------------------------------

def productivity_order(graph: nx.DiGraph, weight: float = 1.0) -> list[str]:
    """Return concepts in order: topological, tie-broken by payoff-weighted reach.

    reach(c) = (# concepts c is ancestor of) + weight * (# applications c is ancestor of)

    A concept with high reach "unlocks" many downstream concepts and applications
    when learned — it should be taught as early as topology allows.

    Implementation: modified Kahn's algorithm with a max-heap priority queue.
    Primitives (in-degree 0) are always first; within each topological tier,
    nodes with higher reach are preferred.

    Parameters
    ----------
    graph  : concept graph (directed; edges u→v mean "u is prerequisite of v")
    weight : multiplier for application-node reach (default 1.0)
             set > 1 to prioritise concepts that unlock cross-domain payoffs

    Returns
    -------
    list[str]
        All node names in topological-then-reach-priority order.
        Passes the topological ordering invariant: if u→v in graph, u appears
        before v in the returned list.
    """
    # Step 1: compute reach for every node
    reach: dict[str, float] = {}
    for node in graph.nodes():
        desc = nx.descendants(graph, node)
        n_concepts = sum(
            1 for d in desc if graph.nodes[d].get("kind") == "concept"
        )
        n_apps = sum(
            1 for d in desc if graph.nodes[d].get("kind") == "application"
        )
        reach[node] = n_concepts + weight * n_apps

    # Step 2: modified Kahn's (max-heap; negate reach for Python's min-heap)
    in_deg: dict[str, int] = dict(graph.in_degree())
    heap: list[tuple[float, str]] = []
    for n, d in in_deg.items():
        if d == 0:
            heapq.heappush(heap, (-reach[n], n))  # stable: break ties by name

    result: list[str] = []
    while heap:
        _, node = heapq.heappop(heap)
        result.append(node)
        for succ in graph.successors(node):
            in_deg[succ] -= 1
            if in_deg[succ] == 0:
                heapq.heappush(heap, (-reach[succ], succ))

    return result


# ---------------------------------------------------------------------------
# Convenience: named subsets used by the SPL workflow
# ---------------------------------------------------------------------------

def first_radical_primitives() -> list[str]:
    """Return the primitives of the first radical (distance / the metric) only."""
    return ["point", "line", "plane", "distance"]


def both_radical_primitives() -> list[str]:
    """Return primitives for both radicals (distance and angle)."""
    return list(_PRIMITIVES.keys())


def concept_names() -> list[str]:
    """Return all concept names in declaration order."""
    return list(_CONCEPTS.keys())


def primitive_names() -> list[str]:
    """Return all primitive names."""
    return list(_PRIMITIVES.keys())


def gap(graph: nx.DiGraph, target: str, learner_state: Iterable[str]) -> set[str]:
    """Concepts needed to reach target that the learner has not yet mastered.

    Returns ancestors(graph, target) minus learner_state.  The result is the
    minimal set of new concepts the learner must cover to understand target.
    """
    return ancestors(graph, target).difference(set(learner_state))


def learning_path(graph: nx.DiGraph, target: str, learner_state: Iterable[str],
                  weight: float = 1.0) -> list[str]:
    """Productivity-ordered list of concepts a learner still needs for target.

    Equivalent to productivity_order(restrict(graph, gap(graph, target, learner_state))).
    Handles the empty-gap case (all prerequisites already mastered) gracefully.
    """
    needed = gap(graph, target, learner_state)
    if not needed:
        return []
    return productivity_order(restrict(graph, needed), weight=weight)


# ---------------------------------------------------------------------------
# Quick smoke-test (python geometry_graph.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    graph = build()
    print(f"Nodes: {graph.number_of_nodes()}  Edges: {graph.number_of_edges()}")
    print(f"Acyclic: {acyclic(graph)}")
    prims = first_radical_primitives()
    print(f"Reducible (first radical): {reducible(graph, prims)}")
    prims_all = both_radical_primitives()
    print(f"Reducible (both radicals): {reducible(graph, prims_all)}")
    order = productivity_order(graph, weight=2.0)
    print(f"\nProductivity order ({len(order)} nodes):")
    for i, n in enumerate(order, 1):
        kind = graph.nodes[n].get("kind", "?")
        r = sum(1 for d in nx.descendants(graph, n)) + 2.0 * sum(
            1 for d in nx.descendants(graph, n)
            if graph.nodes[d].get("kind") == "application"
        )
        print(f"  {i:2}. [{kind:12}] {n:30}  reach={r:.1f}")
    anc = ancestors(graph, "trigonometric_ratios")
    print(f"\nAncestors of trigonometric_ratios ({len(anc)}): {sorted(anc)}")
