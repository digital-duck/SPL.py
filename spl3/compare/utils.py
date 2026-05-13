"""Helper utilities for spl3 compare."""

from __future__ import annotations
import json as _json
import re as _re

# Mermaid keywords that must never be treated as node IDs
_MMD_KEYWORDS = {
    "flowchart", "graph", "subgraph", "end", "direction", "class", "style",
    "click", "linkStyle", "classDef", "sequenceDiagram", "participant",
    "TD", "LR", "RL", "BT", "TB",
}


def parse_mermaid_to_nx(mermaid_content: str):
    """Parse Mermaid flowchart into a NetworkX DiGraph with SPL-aware node types.

    Handles both quoted and unquoted labels across all common Mermaid shape
    syntaxes: rectangle, stadium, decision (single/double curly), trapezoid.
    """
    try:
        import networkx as nx
    except ImportError:
        raise ImportError("networkx not installed: pip install networkx")

    g = nx.DiGraph()

    def _add(node_id: str, label: str, ntype: str = "unknown") -> None:
        if node_id in _MMD_KEYWORDS:
            return
        label = label.replace("\\n", " ").strip()
        if node_id not in g:
            g.add_node(node_id, label=label, node_type=ntype)

    # ── Pass 1: extract nodes from all Mermaid shape syntaxes ──────────────
    # Order matters: most specific patterns first to avoid partial matches.

    # double-curly decision  E{{text}}  or  E{{"text"}}
    for m in _re.finditer(r'\b(\w+)\{\{(?:"([^"]+)"|([^}]+))\}\}', mermaid_content):
        _add(m.group(1), m.group(2) or m.group(3))

    # SPL trapezoid  A[/"text"/]
    for m in _re.finditer(r'\b(\w+)\[/"([^"]+)"/\]', mermaid_content):
        _add(m.group(1), m.group(2))

    # stadium  A(["text"])  or  A([text])
    for m in _re.finditer(r'\b(\w+)\(\[(?:"([^"]+)"|([^\]]+))\]\)', mermaid_content):
        _add(m.group(1), m.group(2) or m.group(3))

    # rectangle  A["text"]  or  A[text]
    # Exclude { to avoid double-curly re-match; exclude /"] to avoid trapezoid re-match
    for m in _re.finditer(r'\b(\w+)\[(?:"([^"]+)"|([^\]\[{"]+(?<!/")))\]', mermaid_content):
        _add(m.group(1), m.group(2) or m.group(3))

    # single-curly decision  A{"text"}  or  A{text}
    for m in _re.finditer(r'\b(\w+)\{(?:"([^"]+)"|([^{}]+))\}', mermaid_content):
        _add(m.group(1), m.group(2) or m.group(3))

    # Fallback: pick up bare node IDs that appear only in edge lines
    _EDGE_RE = _re.compile(
        r'(\w+)(?:\s*[\[({]).*?(?:-->|-\.->|--\w*->)|(?:-->|-\.->|--\w*->)\s*(?:\|[^|]*\|\s*)?(\w+)'
    )
    for line in mermaid_content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(('%', 'style', 'class', 'linkStyle', 'classDef')):
            continue
        # src node of an edge
        m = _re.match(r'(\w+)\s*(?:-->|-\.->|--)', stripped)
        if m and m.group(1) not in _MMD_KEYWORDS and m.group(1) not in g:
            g.add_node(m.group(1), label=m.group(1), node_type="unknown")
        # dst node of an edge
        for m2 in _re.finditer(r'(?:-->|-\.->|--\w*->)\s*(?:\|[^|]*\|\s*)?(\w+)', stripped):
            nid = m2.group(1)
            if nid not in _MMD_KEYWORDS and nid not in g:
                g.add_node(nid, label=nid, node_type="unknown")

    # ── Pass 2: apply SPL node types from `class <id> <type>` annotations ──
    _SPL_TYPES = {"llm", "ctrl", "term", "assign", "proc", "log"}
    for m in _re.finditer(r'^\s*class\s+(\w+)\s+(\w+)\s*$', mermaid_content, _re.MULTILINE):
        node_id, css_class = m.group(1), m.group(2)
        if css_class in _SPL_TYPES and node_id in g:
            g.nodes[node_id]["node_type"] = css_class

    # ── Pass 3: edges ───────────────────────────────────────────────────────
    for m in _re.finditer(
        r'(\w+)\s*(?:-->|-\.->|--\w*->)\s*(?:\|([^|]*)\|\s*)?(\w+)',
        mermaid_content,
    ):
        src, edge_label, dst = m.group(1), m.group(2), m.group(3)
        if src in g and dst in g:
            g.add_edge(src, dst, label=edge_label or "")

    return g


def parse_topology_json_to_nx(json_content: str, *, canonicalize: bool = True):
    """Parse a rt-inspect topology JSON into a NetworkX DiGraph.

    The topology JSON is produced by:
      spl3 splc describe <file.py> --mode rt-inspect

    Args:
        json_content: JSON string with keys: nodes, edges, entry.
        canonicalize: Strip 'Node' suffix and lowercase node IDs so they align
                      with SPL node labels for accurate GED comparison.

    Returns:
        nx.DiGraph with node attrs: label, node_type; edge attrs: label.
    """
    try:
        import networkx as nx
    except ImportError:
        raise ImportError("networkx not installed: pip install networkx")

    try:
        from spl3.splc.rt_inspect import canonicalize_node_id
    except ImportError:
        def canonicalize_node_id(s):
            return _re.sub(r"Node$", "", s).lower()

    data = _json.loads(json_content)
    nodes: dict = data.get("nodes", {})
    edges: list = data.get("edges", [])

    g = nx.DiGraph()

    id_map: dict[str, str] = {}
    for nid, meta in nodes.items():
        canonical = canonicalize_node_id(nid) if canonicalize else nid
        id_map[nid] = canonical
        base = meta.get("base", "Node")
        # Map PocketFlow base classes to SPL node types for cost computation
        ntype = {
            "Node": "llm",
            "BatchNode": "proc",
            "Flow": "ctrl",
            "AsyncNode": "llm",
            "AsyncFlow": "ctrl",
        }.get(base, "llm")
        g.add_node(canonical, label=canonical, node_type=ntype)

    for edge in edges:
        src = id_map.get(edge["source"], edge["source"])
        tgt = id_map.get(edge["target"], edge["target"])
        lbl = edge.get("label", "")
        if src in g and tgt in g:
            g.add_edge(src, tgt, label=lbl)

    return g
