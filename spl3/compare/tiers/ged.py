"""Topological comparison using Graph Edit Distance (GED)."""

from __future__ import annotations
import difflib as _dl
from spl3.compare.utils import parse_mermaid_to_nx
from spl3.compare.types import GEDResult

def compare_ged(content1: str, content2: str) -> GEDResult | str:
    try:
        import networkx as nx
    except ImportError:
        return "Error: networkx not installed: pip install networkx"

    try:
        g1 = parse_mermaid_to_nx(content1)
        g2 = parse_mermaid_to_nx(content2)

        def _node_subst_cost(a1: dict, a2: dict) -> float:
            """SPL-aware cost: type mismatch + label edit distance."""
            t1, t2 = a1.get("node_type", ""), a2.get("node_type", "")
            type_cost = (
                0.0 if t1 == t2 else
                0.5 if any(t1 in g and t2 in g
                           for g in ({"llm","proc"}, {"ctrl"}, {"term"}, {"assign","log"}))
                else 1.5
            )
            l1, l2 = a1.get("label", ""), a2.get("label", "")
            if l1 and l2:
                sim = _dl.SequenceMatcher(None, l1, l2).ratio()
                label_cost = (1.0 - sim) * 0.5
            else:
                label_cost = 0.0
            return type_cost + label_cost

        def _edge_subst_cost(e1: dict, e2: dict) -> float:
            """Edge labels carry control-flow semantics."""
            l1 = (e1.get("label") or "").strip()
            l2 = (e2.get("label") or "").strip()
            if l1 == l2:
                return 0.0
            if bool(l1) != bool(l2):
                return 1.0
            return (1.0 - _dl.SequenceMatcher(None, l1, l2).ratio()) * 0.5

        distance = nx.graph_edit_distance(
            g1, g2,
            node_subst_cost=_node_subst_cost,
            edge_subst_cost=_edge_subst_cost,
            timeout=15,
        )
        
        if distance is None:
            return "Error: GED timeout (graph too complex)"

        def _type_counts(g):
            counts: dict[str, int] = {}
            for _, attrs in g.nodes(data=True):
                t = attrs.get("node_type", "unknown")
                counts[t] = counts.get(t, 0) + 1
            return counts

        n1, n2 = len(g1.nodes), len(g2.nodes)
        return GEDResult(
            distance=float(distance),
            normalized_distance=round(float(distance) / (n1 + n2), 3) if (n1 + n2) > 0 else 0.0,
            node_count=[n1, n2],
            edge_count=[len(g1.edges), len(g2.edges)],
            node_types=[_type_counts(g1), _type_counts(g2)]
        )
    except Exception as e:
        return f"Error: {e}"
