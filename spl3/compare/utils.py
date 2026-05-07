"""Helper utilities for spl3 compare."""

from __future__ import annotations
import re as _re

def parse_mermaid_to_nx(mermaid_content: str):
    """Parse Mermaid flowchart into a NetworkX DiGraph with SPL-aware node types.

    Reads the ``class <id> <type>`` annotations emitted by spl2mmd to attach
    the SPL node type (llm, ctrl, term, assign, proc, log) as a node attribute.
    """
    try:
        import networkx as nx
    except ImportError:
        raise ImportError("networkx not installed: pip install networkx")

    g = nx.DiGraph()

    # Pass 1: extract node labels from all Mermaid shape syntaxes
    for m in _re.finditer(r'^\s+(\w+)\[/"(.*?)"/\]', mermaid_content, _re.MULTILINE):
        g.add_node(m.group(1), label=m.group(2), node_type="unknown")

    for m in _re.finditer(r'^\s+(\w+)\{"(.*?)"\}', mermaid_content, _re.MULTILINE):
        g.add_node(m.group(1), label=m.group(2), node_type="unknown")

    for m in _re.finditer(r'^\s+(\w+)\(\["(.*?)"\]\)', mermaid_content, _re.MULTILINE):
        g.add_node(m.group(1), label=m.group(2), node_type="unknown")

    for m in _re.finditer(r'^\s+(\w+)\["(.*?)"\]', mermaid_content, _re.MULTILINE):
        if m.group(1) not in g:
            g.add_node(m.group(1), label=m.group(2), node_type="unknown")

    # Pass 2: apply SPL node types from `class <id> <type>` annotations
    _SPL_TYPES = {"llm", "ctrl", "term", "assign", "proc", "log"}
    for m in _re.finditer(r'^\s+class\s+(\w+)\s+(\w+)\s*$', mermaid_content, _re.MULTILINE):
        node_id, css_class = m.group(1), m.group(2)
        if css_class in _SPL_TYPES and node_id in g:
            g.nodes[node_id]["node_type"] = css_class

    # Pass 3: edges
    for m in _re.finditer(
        r'(\w+)\s*(?:-->|-\.->)\s*(?:\|([^|]*)\|\s*)?(\w+)',
        mermaid_content
    ):
        src, edge_label, dst = m.group(1), m.group(2), m.group(3)
        if src in g and dst in g:
            g.add_edge(src, dst, label=edge_label or "")

    return g
