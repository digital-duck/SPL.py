"""Linear Algebra concept graph — python/linalg domain library.

Part of the ``python/linalg`` splc target (Layer 2 of the neurosymbolic SPL
roadmap).  Loaded into the IPython kernel at workflow start:

    CALL run_python('import sys; sys.path.insert(0, "/path/to/cookbook/71_linalg_micro_textbook")') INTO @_
    CALL run_python('import linalg_graph; graph = linalg_graph.build()') INTO @_

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
    verifier   : str (tool that checks worked examples: "sympy" | "z3" | "numpy")
    lab        : str (interactive tool for the student cell)
    play       : str (suggested exploration)
    shape_typed: bool (subject to matrix-dimension shape check)
    introduced_in: str (module where this primitive first appears)
    domain     : str (for applications: the external field)

Edge direction:
    u → v  means  "u is a prerequisite of v"
    (primitives are sources; targets/applications are sinks)
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
    "field_of_scalars": {
        "symbol": "F",
        "defines": "the floor for scalars — we do not reduce the field",
        "tier": 0,
    },
    "carrier_set": {
        "symbol": "V",
        "defines": "the floor for vectors — set theory is below the floor",
        "tier": 0,
    },
    "vector_addition": {
        "symbol": "⊕: V×V→V",
        "defines": "first radical — closed binary operation on V",
        "tier": 0,
    },
    "scalar_multiplication": {
        "symbol": "⊙: F×V→V",
        "defines": "first radical — scalar scaling of a vector",
        "tier": 0,
    },
    "inner_product": {
        "symbol": "⟨·,·⟩: V×V→F",
        "defines": "second radical — geometry on V; not reducible to ⊕, ⊙",
        "tier": 0,
        "introduced_in": "geometry",
    },
}

# Concept declarations: composed from primitives or other concepts.
# Each entry lists its immediate `composed_of` prerequisites.
_CONCEPTS: dict[str, dict] = {
    # ── First radical: ⊕ and ⊙ ──────────────────────────────────────────
    "linear_combination": {
        "composed_of": ["vector_addition", "scalar_multiplication"],
        "defines": "Σ αᵢ ⊙ vᵢ — the atomic operation; almost all of linear algebra is a statement about this",
        "verifier": "sympy",
        "lab": "sympy",
        "play": "pick vectors and scalars; check the result is still in V",
        "tier": 1,
    },
    "subspace": {
        "composed_of": ["linear_combination"],
        "defines": "subset of V closed under linear_combination",
        "verifier": "sympy",
        "lab": "sympy",
        "tier": 2,
    },
    "span": {
        "composed_of": ["linear_combination"],
        "defines": "set of all linear combinations of a given set S — the smallest subspace containing S",
        "verifier": "sympy",
        "lab": "sympy",
        "play": "build A; A.columnspace()",
        "tier": 2,
    },
    "linear_independence": {
        "composed_of": ["linear_combination"],
        "defines": "no non-trivial linear combination is zero — uniqueness of the trivial combination",
        "verifier": "sympy",
        "lab": "sympy",
        "tier": 2,
    },
    "basis": {
        "composed_of": ["linear_independence", "span"],
        "defines": "linearly independent spanning set — minimal generator or maximal independent set",
        "verifier": "sympy",
        "lab": "sympy",
        "tier": 3,
    },
    "dimension": {
        "composed_of": ["basis"],
        "defines": "|basis| — well-defined by the exchange lemma (all bases have the same size)",
        "verifier": "sympy",
        "lab": "sympy",
        "tier": 4,
    },
    "coordinates": {
        "composed_of": ["basis"],
        "defines": "unique coefficients of a vector over a basis — isomorphism V ≅ Fⁿ",
        "verifier": "sympy",
        "lab": "sympy",
        "tier": 4,
    },
    "linear_map": {
        "composed_of": ["linear_combination"],
        "defines": "function f: V→W preserving linear_combination — f(αu+βv) = αf(u)+βf(v)",
        "verifier": "sympy",
        "lab": "sympy",
        "tier": 2,
    },
    "matrix": {
        "composed_of": ["linear_map", "coordinates"],
        "defines": "coordinate representation of a linear_map relative to chosen bases",
        "verifier": "sympy",
        "lab": "sympy",
        "shape_typed": True,
        "tier": 5,
    },
    "matrix_multiplication": {
        "composed_of": ["matrix", "linear_map"],
        "defines": "coordinate form of map composition — definition is forced by (g∘f) → [g][f]",
        "verifier": "sympy",
        "lab": "sympy",
        "shape_typed": True,
        "tier": 6,
    },
    "image": {
        "composed_of": ["span", "linear_map"],
        "defines": "span of columns — {f(v) : v in domain}; the range of the map",
        "verifier": "sympy",
        "lab": "sympy",
        "tier": 3,
    },
    "kernel": {
        "composed_of": ["linear_map"],
        "defines": "{v : f(v) = 0} — the 'lost information' subspace",
        "verifier": "sympy",
        "lab": "sympy",
        "tier": 3,
    },
    "rank": {
        "composed_of": ["dimension", "image"],
        "defines": "dimension of the image — how much information is preserved",
        "verifier": "sympy",
        "lab": "sympy",
        "tier": 5,
    },
    "nullity": {
        "composed_of": ["dimension", "kernel"],
        "defines": "dimension of the kernel — how much information is lost",
        "verifier": "sympy",
        "lab": "sympy",
        "tier": 5,
    },
    "rank_nullity": {
        "composed_of": ["rank", "nullity", "dimension"],
        "defines": "rank + nullity = dim(domain) — information is neither created nor destroyed",
        "verifier": "sympy",
        "lab": "sympy",
        "tier": 6,
    },
    "determinant": {
        "composed_of": ["linear_map"],
        "defines": "alternating multilinear form — signed volume scale factor of the map",
        "verifier": "sympy",
        "lab": "sympy",
        "tier": 3,
    },
    "eigenpair": {
        "composed_of": ["linear_map", "scalar_multiplication"],
        "defines": "(λ, v≠0) with f(v) = λ ⊙ v — direction the map acts as pure ⊙",
        "verifier": "sympy",
        "lab": "sympy",
        "play": "build A; A.eigenvects(); perturb an entry; watch λ move",
        "tier": 3,
    },
    "diagonalization": {
        "composed_of": ["basis", "eigenpair"],
        "defines": "basis of eigenpairs — operator decouples into independent ⊙'s along eigenbasis",
        "verifier": "sympy",
        "lab": "sympy",
        "play": "P, D = A.diagonalize(); verify A == P * D * P**(-1)",
        "tier": 4,
    },
    # ── Second radical: ⟨·,·⟩ ───────────────────────────────────────────
    "norm": {
        "composed_of": ["inner_product"],
        "defines": "√⟨v,v⟩ — length induced by the inner product",
        "verifier": "sympy",
        "lab": "sympy",
        "tier": 1,
    },
    "orthogonality": {
        "composed_of": ["inner_product"],
        "defines": "⟨u,v⟩ = 0 — generalised perpendicularity",
        "verifier": "sympy",
        "lab": "sympy",
        "tier": 1,
    },
    "projection": {
        "composed_of": ["orthogonality", "span"],
        "defines": "orthogonal projection onto a subspace — nearest-point map",
        "verifier": "sympy",
        "lab": "sympy",
        "tier": 3,
    },
    "orthonormal_basis": {
        "composed_of": ["basis", "orthogonality", "norm"],
        "defines": "basis with ⟨bᵢ, bⱼ⟩ = δᵢⱼ — coordinate geometry at its simplest",
        "verifier": "sympy",
        "lab": "sympy",
        "tier": 4,
    },
    "gram_schmidt": {
        "composed_of": ["projection", "orthonormal_basis"],
        "defines": "algorithm producing orthonormal basis from any independent set",
        "verifier": "sympy",
        "lab": "sympy",
        "play": "take a random basis; apply Gram-Schmidt; verify columns are orthonormal",
        "tier": 5,
    },
    "adjoint": {
        "composed_of": ["inner_product", "linear_map"],
        "defines": "f* such that ⟨f(v), w⟩ = ⟨v, f*(w)⟩ for all v, w",
        "verifier": "sympy",
        "lab": "sympy",
        "tier": 3,
    },
    "spectral_theorem": {
        "composed_of": ["adjoint", "eigenpair", "orthonormal_basis"],
        "defines": "self-adjoint operator has orthonormal eigenbasis — both radicals meet here",
        "verifier": "sympy",
        "lab": "sympy",
        "play": "build Hermitian A; verify A.diagonalize() columns are orthonormal",
        "tier": 5,
    },
}

# Application declarations: external edges — the payoff, pointing out of linear algebra.
_APPLICATIONS: dict[str, dict] = {
    "normal_modes": {
        "needs": ["eigenpair"],
        "domain": "classical mechanics",
        "defines": "coupled oscillators → independent normal modes via eigenpairs",
    },
    "stability_analysis": {
        "needs": ["eigenpair"],
        "domain": "dynamical systems",
        "defines": "sign of eigenvalue determines stability of a fixed point",
    },
    "markov_stationary": {
        "needs": ["eigenpair"],
        "domain": "probability",
        "defines": "stationary distribution = eigenvector with eigenvalue 1",
    },
    "pagerank": {
        "needs": ["eigenpair"],
        "domain": "networks",
        "defines": "dominant eigenvector of the (damped) link matrix",
    },
    "pca": {
        "needs": ["eigenpair", "inner_product"],
        "domain": "statistics",
        "defines": "principal components = eigenvectors of the covariance matrix",
    },
    "quantum_observable": {
        "needs": ["spectral_theorem"],
        "domain": "quantum mechanics",
        "defines": "observables are self-adjoint; spectral theorem guarantees real eigenvalues",
    },
    "fourier_modes": {
        "needs": ["spectral_theorem"],
        "domain": "signals and analysis",
        "defines": "Fourier basis = orthonormal eigenbasis of the derivative operator",
    },
}


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build() -> nx.DiGraph:
    """Build and return the full linear algebra concept graph.

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
    """Return the primitives of the first radical (⊕/⊙) only."""
    return ["field_of_scalars", "carrier_set", "vector_addition", "scalar_multiplication"]


def both_radical_primitives() -> list[str]:
    """Return primitives for both radicals (⊕/⊙ and ⟨·,·⟩)."""
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
# Quick smoke-test (python linalg_graph.py)
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
    anc = ancestors(graph, "spectral_theorem")
    print(f"\nAncestors of spectral_theorem ({len(anc)}): {sorted(anc)}")
