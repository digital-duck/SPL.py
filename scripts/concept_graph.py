"""Generic concept-graph toolkit — a CLI that inspects, visualizes, shares,
and composes *any* domain-specific concept graph, without that graph's
module needing to import or know about this one.

A "domain module" is any importable Python module (or ``.py`` file) that
exposes::

    build() -> networkx.DiGraph

whose nodes carry at least:
    kind        : "primitive" | "concept" | "application"
    tier        : int (0 = primitive floor; higher = more composed)
    defines     : str (one-line definition)
    composed_of : list[str] (direct prerequisites; empty for primitives)

and whose edges u → v mean "u is a prerequisite of v".  ``linalg_graph.py``
(cookbook/71_linalg_micro_textbook) and ``geometry_graph.py``
(cookbook/73_intro_geometry) are worked examples — each is fully
self-contained (by design: see cookbook/70's readme on why domain libraries
duplicate their graph algorithms rather than share an implementation that
two domains' notions of e.g. "ancestors" could silently diverge from). This
module is the deliberate exception: a *reporting and sharing* layer that
every domain module gets "mixed in" for free, purely by exposing build() —
no import, no coupling, no per-domain CLI to write or maintain.

CLI usage
---------
    python concept_graph.py --domain linalg_graph stats
    python concept_graph.py --domain linalg_graph show spectral_theorem
    python concept_graph.py --domain linalg_graph visualize --format mermaid
    python concept_graph.py --domain linalg_graph export domain.json -t pca
    python concept_graph.py --domain linalg_graph import domain.json
    python concept_graph.py compose -d linalg_graph -d geometry_graph hybrid.json
    python concept_graph.py --domain hybrid.json stats

``--domain`` accepts an importable module name (resolved on ``sys.path`` /
the current directory), a path to a ``.py`` file, or a path to a ``.json``
graph previously written by ``export``/``compose`` — so any concept graph,
wherever it lives and however it was produced, flows through the same CLI.

Authoring a concept graph that spans multiple fields by hand is exactly the
kind of task no single publisher takes on; ``compose`` is the framework's
first mechanical step toward making that tractable — see its docstring.
"""

from __future__ import annotations

import heapq
import importlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Iterable

import click
import networkx as nx


# ---------------------------------------------------------------------------
# Generic graph algorithms — pure functions of (graph [, params]); no
# knowledge of any particular domain's concepts.
# ---------------------------------------------------------------------------

def acyclic(graph: nx.DiGraph) -> bool:
    """Return True if the graph has no cycles (valid composition hierarchy)."""
    return nx.is_directed_acyclic_graph(graph)


def reducible(graph: nx.DiGraph, primitives: Iterable[str]) -> bool:
    """Return True if every concept/application reduces transitively to primitives.

    A node is reducible iff every "leaf" (in-degree 0 node) in its ancestor
    closure is in *primitives*.  Any undeclared leaf signals a node that
    claims to be primitive but was not declared as such.
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


def minimal(graph: nx.DiGraph, primitives: Iterable[str]) -> bool:
    """Return True if every supplied name is a node declared `kind="primitive"`.

    A minimal basis uses only the graph's own irreducible radicals — no
    concept is claimed to be primitive if the graph composes it from others.
    """
    declared = {n for n, d in graph.nodes(data=True) if d.get("kind") == "primitive"}
    return set(primitives).issubset(declared)


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
    """Return application nodes that directly depend on target."""
    return [
        n for n in graph.successors(target)
        if graph.nodes[n].get("kind") == "application"
    ]


def gap(graph: nx.DiGraph, target: str, learner_state: Iterable[str]) -> set[str]:
    """Concepts needed to reach target that the learner has not yet mastered.

    Returns ancestors(graph, target) minus learner_state.
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


def productivity_order(graph: nx.DiGraph, weight: float = 1.0) -> list[str]:
    """Return nodes in order: topological, tie-broken by payoff-weighted reach.

    reach(c) = (# concepts c is ancestor of) + weight * (# applications c is ancestor of)

    A node with high reach "unlocks" many downstream concepts and
    applications when learned — it should be taught as early as topology
    allows.

    Implementation: modified Kahn's algorithm with a max-heap priority queue.
    Primitives (in-degree 0) are always first; within each topological tier,
    nodes with higher reach are preferred.  Passes the topological ordering
    invariant: if u→v in graph, u appears before v in the returned list.
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
# Visualization renderers — text formats that need no plotting dependencies
# ---------------------------------------------------------------------------

_KIND_STYLE = {
    "primitive": "fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20",
    "concept": "fill:#e3f2fd,stroke:#1565c0,color:#0d47a1",
    "application": "fill:#fff3e0,stroke:#ef6c00,color:#e65100",
}
_KIND_FILL = {"primitive": "#e8f5e9", "concept": "#e3f2fd", "application": "#fff3e0"}


def _to_mermaid(graph: nx.DiGraph) -> str:
    """Render as a Mermaid flowchart (renders inline on GitHub/most markdown viewers)."""
    lines = ["graph TD"]
    for kind, style in _KIND_STYLE.items():
        lines.append(f"    classDef {kind} {style}")
    for node, attrs in graph.nodes(data=True):
        label = node.replace("_", " ")
        lines.append(f'    {node}["{label}"]:::{attrs.get("kind", "concept")}')
    for u, v in graph.edges():
        lines.append(f"    {u} --> {v}")
    return "\n".join(lines)


def _to_dot(graph: nx.DiGraph) -> str:
    """Render as Graphviz DOT (render with: dot -Tpng -o graph.png graph.dot)."""
    lines = ["digraph concepts {", "    rankdir=LR;", "    node [shape=box, style=filled];"]
    for node, attrs in graph.nodes(data=True):
        fill = _KIND_FILL.get(attrs.get("kind", "concept"), "#ffffff")
        lines.append(f'    "{node}" [fillcolor="{fill}"];')
    for u, v in graph.edges():
        lines.append(f'    "{u}" -> "{v}";')
    lines.append("}")
    return "\n".join(lines)


def _to_ascii(graph: nx.DiGraph) -> str:
    """Render as a plain-text outline grouped by tier — readable in any terminal."""
    by_tier: dict[int, list[str]] = {}
    for node, attrs in graph.nodes(data=True):
        by_tier.setdefault(attrs.get("tier", 0), []).append(node)

    lines = []
    for tier in sorted(by_tier):
        lines.append(f"Tier {tier}")
        for node in sorted(by_tier[tier]):
            attrs = graph.nodes[node]
            prereqs = attrs.get("composed_of") or []
            arrow = f"  ← {', '.join(prereqs)}" if prereqs else ""
            lines.append(f"  [{attrs.get('kind', '?'):11}] {node}{arrow}")
            if attrs.get("defines"):
                lines.append(f"               {attrs['defines']}")
        lines.append("")
    return "\n".join(lines).rstrip()


_RENDERERS = {"mermaid": _to_mermaid, "dot": _to_dot, "ascii": _to_ascii}


# ---------------------------------------------------------------------------
# Domain loading — `--domain linalg_graph`, `--domain path/to/graph.py`, or
# `--domain hybrid.json` (an exported / composed graph — see `compose` below)
# ---------------------------------------------------------------------------

class _GraphModule:
    """Wraps a pre-built graph so it satisfies the `build()` domain contract.

    Lets exported/composed JSON graphs flow back through the same --domain
    pipeline as Python domain modules — `compose` writes one of these, and
    `stats`/`show`/`visualize`/... can immediately analyze it.
    """

    def __init__(self, graph: nx.DiGraph):
        self._graph = graph

    def build(self) -> nx.DiGraph:
        return self._graph


def _load_domain(domain: str):
    """Load a domain module by import name, ``.py`` file path, or ``.json`` graph."""
    path = Path(domain)
    if domain.endswith(".json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        return _GraphModule(nx.node_link_graph(data, directed=True, multigraph=False))
    if domain.endswith(".py") or path.exists():
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec is None or spec.loader is None:
            raise click.ClickException(f"Cannot load domain module from {domain!r}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    try:
        return importlib.import_module(domain)
    except ImportError as exc:
        raise click.ClickException(f"Cannot import domain module {domain!r}: {exc}")


# ---------------------------------------------------------------------------
# CLI — `python concept_graph.py --domain <module_or_path> <command> ...`
# ---------------------------------------------------------------------------

class _Domain:
    """Lazily resolves --domain to a built graph.

    Lazy because `import` only inspects an exported JSON file — it has no
    need for a domain graph, so it shouldn't be forced to require --domain.
    """

    def __init__(self, name: str | None):
        self._name = name
        self._graph: nx.DiGraph | None = None

    @property
    def graph(self) -> nx.DiGraph:
        graph = self._graph
        if graph is None:
            if not self._name:
                raise click.ClickException("This command requires --domain MODULE_OR_PATH")
            module = _load_domain(self._name)
            if not hasattr(module, "build"):
                raise click.ClickException(
                    f"{self._name!r} has no build() — not a concept-graph domain module")
            graph = module.build()
            self._graph = graph
        return graph


@click.group()
@click.option("--domain", "-d", default=None,
              help="Domain module to analyze — an importable module name "
                   "(e.g. linalg_graph) or a path to its .py file. "
                   "Required by every command except `import`.")
@click.pass_context
def cli(ctx, domain):
    """Inspect, visualize, and share any concept graph exposing build()."""
    ctx.obj = _Domain(domain)


@cli.command()
@click.pass_obj
def stats(domain):
    """Print node/edge counts and the structural verifier checks."""
    graph = domain.graph
    click.echo(f"Nodes: {graph.number_of_nodes()}  Edges: {graph.number_of_edges()}")
    click.echo(f"Acyclic: {acyclic(graph)}")
    primitives = [n for n, d in graph.nodes(data=True) if d.get("kind") == "primitive"]
    click.echo(f"Reducible (to its {len(primitives)} declared primitives): "
               f"{reducible(graph, primitives)}")
    by_kind: dict[str, int] = {}
    for _, attrs in graph.nodes(data=True):
        by_kind[attrs.get("kind", "?")] = by_kind.get(attrs.get("kind", "?"), 0) + 1
    for kind, count in sorted(by_kind.items()):
        click.echo(f"  {kind:11}: {count}")


@cli.command(name="list")
@click.option("--kind", type=click.Choice(["primitive", "concept", "application"]),
              default=None, help="Restrict to one node kind.")
@click.pass_obj
def list_nodes(domain, kind):
    """List nodes ordered by tier, optionally filtered by --kind."""
    graph = domain.graph
    rows = [
        (attrs.get("tier", 0), name, attrs.get("kind"))
        for name, attrs in graph.nodes(data=True)
        if kind is None or attrs.get("kind") == kind
    ]
    for tier, name, k in sorted(rows):
        click.echo(f"  tier {tier}  [{k:11}] {name}")


@cli.command()
@click.argument("node")
@click.pass_obj
def show(domain, node):
    """Show full metadata for one node (definition, prerequisites, applications)."""
    graph = domain.graph
    if not in_graph(graph, node):
        raise click.ClickException(f"Unknown node: {node!r}")
    attrs = graph.nodes[node]
    click.echo(f"{node}  [{attrs.get('kind')}]  tier={attrs.get('tier')}")
    if attrs.get("defines"):
        click.echo(f"  defines : {attrs['defines']}")
    if attrs.get("composed_of"):
        click.echo(f"  needs   : {', '.join(attrs['composed_of'])}")
    apps = applications_of(graph, node)
    if apps:
        click.echo(f"  unlocks : {', '.join(apps)}")
    for key in ("verifier", "lab", "play", "domain"):
        if attrs.get(key):
            click.echo(f"  {key:8}: {attrs[key]}")


@cli.command(name="ancestors")
@click.argument("target")
@click.pass_obj
def ancestors_cmd(domain, target):
    """List everything `target` transitively depends on."""
    graph = domain.graph
    if not in_graph(graph, target):
        raise click.ClickException(f"Unknown node: {target!r}")
    anc = ancestors(graph, target)
    click.echo(f"Ancestors of {target} ({len(anc)}):")
    for n in sorted(anc):
        click.echo(f"  {n}")


@cli.command()
@click.argument("target")
@click.option("--know", "-k", "known", multiple=True,
              help="Concept the learner already knows (repeatable).")
@click.option("--weight", default=1.0, show_default=True,
              help="Application-reach weight used to order the remaining steps.")
@click.pass_obj
def path(domain, target, known, weight):
    """Print the productivity-ordered steps still needed to reach `target`."""
    graph = domain.graph
    if not in_graph(graph, target):
        raise click.ClickException(f"Unknown node: {target!r}")
    remaining = learning_path(graph, target, known, weight=weight)
    if not remaining:
        click.echo(f"Nothing left to learn — {target} is already reachable from your known set.")
        return
    click.echo(f"Learning path to {target} ({len(remaining)} steps):")
    for i, n in enumerate(remaining, 1):
        click.echo(f"  {i:2}. {n}")


@cli.command()
@click.option("--weight", default=1.0, show_default=True,
              help="Application-reach weight used to break topological ties.")
@click.pass_obj
def order(domain, weight):
    """Print every node in productivity (topological + reach-weighted) order."""
    graph = domain.graph
    for i, n in enumerate(productivity_order(graph, weight=weight), 1):
        kind = graph.nodes[n].get("kind", "?")
        click.echo(f"  {i:2}. [{kind:11}] {n}")


@cli.command()
@click.option("--format", "fmt", type=click.Choice(sorted(_RENDERERS)), default="mermaid",
              show_default=True, help="Output format.")
@click.option("--target", "-t", default=None,
              help="Restrict to the ancestor closure of this node (instead of the full graph).")
@click.option("--output", "-o", type=click.Path(dir_okay=False, writable=True), default=None,
              help="Write to a file instead of stdout.")
@click.pass_obj
def visualize(domain, fmt, target, output):
    """Render the concept graph as mermaid / graphviz-dot / a tiered ascii outline."""
    graph = domain.graph
    if target:
        if not in_graph(graph, target):
            raise click.ClickException(f"Unknown node: {target!r}")
        graph = restrict(graph, ancestors(graph, target) | {target})

    text = _RENDERERS[fmt](graph)
    if output:
        Path(output).write_text(text, encoding="utf-8")
        click.echo(f"Wrote {fmt} graph ({graph.number_of_nodes()} nodes) to {output}")
    else:
        click.echo(text)


@cli.command()
@click.argument("output", type=click.Path(dir_okay=False, writable=True))
@click.option("--target", "-t", multiple=True,
              help="Export only the ancestor closure of these nodes (repeatable). "
                   "Default: export the full graph.")
@click.pass_obj
def export(domain, output, target):
    """Export the graph (or a domain-specific subgraph) to JSON for sharing."""
    graph = domain.graph
    if target:
        keep = set(target)
        for t in target:
            if not in_graph(graph, t):
                raise click.ClickException(f"Unknown node: {t!r}")
            keep |= ancestors(graph, t)
        graph = restrict(graph, keep)

    data = nx.node_link_data(graph)
    Path(output).write_text(json.dumps(data, indent=2), encoding="utf-8")
    click.echo(f"Exported {graph.number_of_nodes()} nodes / {graph.number_of_edges()} "
               f"edges to {output}")


@cli.command()
@click.option("--domain", "-d", "domains", multiple=True, required=True,
              help="A domain to fold in (repeatable — give at least two, "
                   "e.g. -d linalg_graph -d geometry_graph).")
@click.argument("output", type=click.Path(dir_okay=False, writable=True))
def compose(domains, output):
    """Compose several domain graphs into one hybrid concept graph.

    Authoring a concept graph that spans multiple fields by hand is exactly
    the kind of "too daunting to publish" task the micro-textbook framework
    exists to make tractable — `compose` takes that first mechanical step:
    union the domains' nodes and edges into one graph and write it out as
    JSON (the same shareable shape `export` produces, so the result flows
    straight back into `stats`/`show`/`visualize`/... via --domain hybrid.json).

    Kept deliberately simple for now: nodes are merged by name, last domain
    wins on attribute conflicts, and every name collision across domains is
    reported so the author can resolve it (rename one side, or confirm the
    overlap is intentional and should become a bridging point). Smarter
    merge strategies — explicit bridging edges, namespacing, alias maps —
    can layer on top once real hybrid graphs show what's actually needed.
    """
    if len(domains) < 2:
        raise click.ClickException("compose needs at least two --domain values")

    combined = nx.DiGraph()
    owner: dict[str, str] = {}
    collisions: list[tuple[str, str, str]] = []
    for name in domains:
        graph = _Domain(name).graph
        for node in graph.nodes():
            if node in owner and owner[node] != name:
                collisions.append((node, owner[node], name))
            owner[node] = name
        combined = nx.compose(combined, graph)

    data = nx.node_link_data(combined)
    Path(output).write_text(json.dumps(data, indent=2), encoding="utf-8")
    click.echo(f"Composed {len(domains)} domains ({', '.join(domains)}) into "
               f"{combined.number_of_nodes()} nodes / {combined.number_of_edges()} "
               f"edges → {output}")
    if collisions:
        click.echo(f"\n{len(collisions)} name collision(s) — later domain's node wins:")
        for node, first, second in collisions:
            click.echo(f"  {node!r}: declared by both {first!r} and {second!r}")


@cli.command(name="import")
@click.argument("input_file", type=click.Path(exists=True, dir_okay=False))
def import_cmd(input_file):
    """Load a previously exported concept graph and report on its shape.

    Unlike the other commands, this one needs no --domain — it reports
    purely on the JSON file being inspected.
    """
    data = json.loads(Path(input_file).read_text(encoding="utf-8"))
    loaded = nx.node_link_graph(data, directed=True, multigraph=False)

    click.echo(f"Loaded {loaded.number_of_nodes()} nodes / {loaded.number_of_edges()} "
               f"edges from {input_file}")
    click.echo(f"Acyclic: {acyclic(loaded)}")
    by_kind: dict[str, int] = {}
    for _, attrs in loaded.nodes(data=True):
        by_kind[attrs.get("kind", "?")] = by_kind.get(attrs.get("kind", "?"), 0) + 1
    for kind, count in sorted(by_kind.items()):
        click.echo(f"  {kind:11}: {count}")


if __name__ == "__main__":
    cli()
