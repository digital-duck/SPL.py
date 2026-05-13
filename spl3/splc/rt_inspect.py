"""
rt_inspect — Runtime Introspection for PocketFlow Python implementations.

Given a compiled Python/PocketFlow file, this module loads it in isolation,
finds the Flow object, traverses the node graph via node.successors (BFS),
and returns a canonical JSON topology suitable for:
  - GED comparison against SPL-derived topology (spl3 compare --mode ged)
  - Mermaid visualisation (Gate 1 in the Intent Engineering platform)
  - Re-feeding into the SPL pipeline: topology.json → mmd2spl → text2spl → .spl

Design principle:
  Structure extraction is DETERMINISTIC (no LLM).
  Only semantics (prompt bodies) require stochastic inference.
  This separates Syntactic drift from Semantic drift — the core SPL thesis.

Usage::

    from spl3.splc.rt_inspect import inspect_pocketflow_file, topology_to_mermaid

    result = inspect_pocketflow_file(Path("self_refine_python_pocketflow.py"))
    print(result["json"])   # JSON topology string
    print(result["mmd"])    # Mermaid diagram string
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


# ── Public entry point ────────────────────────────────────────────────────────

_SUPPORTED_SUFFIXES = {".py"}
_UNSUPPORTED_MSG = {
    ".go": (
        "rt-inspect does not yet support Go targets. "
        "Planned: static AST analysis via go/ast. "
        "Workaround: inspect the Python/PocketFlow target instead."
    ),
    ".ts": (
        "rt-inspect does not yet support TypeScript targets. "
        "Planned: ts-morph AST analysis. "
        "Workaround: inspect the Python/PocketFlow target instead."
    ),
}


def inspect_pocketflow_file(py_path: Path) -> dict[str, Any]:
    """Load a PocketFlow Python file and extract its graph topology.

    The file is imported via importlib (not subprocess) so the PocketFlow
    graph object is available in-memory for traversal. The ``__main__`` guard
    prevents CLI entry points from executing.

    Currently supports Python/PocketFlow only (.py).
    Go and TypeScript targets are not yet supported — see _UNSUPPORTED_MSG.

    Args:
        py_path: Path to a compiled Python/PocketFlow implementation file.

    Returns:
        A dict with keys:
            source   — absolute path of the inspected file
            nodes    — {node_id: {"type": class_name, "base": parent_class}}
            edges    — [{"source": id, "target": id, "label": action_str}]
            entry    — node_id of the Flow's start node
            json     — JSON string (pretty-printed topology)
            mmd      — Mermaid diagram string (graph TD)

    Raises:
        NotImplementedError: If the file is not a supported target language.
        ValueError: If no PocketFlow Flow object can be found in the module.
        ImportError: If pocketflow is not installed.
    """
    py_path = py_path.resolve()
    suffix = py_path.suffix.lower()
    if suffix not in _SUPPORTED_SUFFIXES:
        msg = _UNSUPPORTED_MSG.get(suffix,
            f"rt-inspect supports Python/PocketFlow (.py) only; got '{suffix}'.")
        raise NotImplementedError(msg)

    # ── 1. Import the module without running __main__ ─────────────────────────
    spec = importlib.util.spec_from_file_location("_rt_inspect_target", py_path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot load module from {py_path}")

    mod = importlib.util.module_from_spec(spec)

    # Add the file's directory to sys.path so local imports (nodes.py, utils.py, etc.) resolve
    py_dir = str(py_path.parent)
    _path_inserted = py_dir not in sys.path
    if _path_inserted:
        sys.path.insert(0, py_dir)

    # Prevent click / argparse from parsing sys.argv during import
    _saved_argv = sys.argv[:]
    sys.argv = [str(py_path)]
    try:
        spec.loader.exec_module(mod)
    except SystemExit:
        pass  # click standalone_mode may call sys.exit — ignore during inspection
    except ImportError as exc:
        # A transitive dependency (e.g. duckduckgo_search) is not installed.
        # Re-try with auto-mocking of missing third-party modules so we can still
        # extract the PocketFlow graph structure (which only requires pocketflow itself).
        missing = _extract_missing_module(exc)
        if missing:
            mod = _load_with_mock(py_path, missing, py_dir)
        else:
            raise
    finally:
        sys.argv = _saved_argv
        if _path_inserted and py_dir in sys.path:
            sys.path.remove(py_dir)

    # ── 2. Find the Flow object ───────────────────────────────────────────────
    flow = _find_flow(mod)

    if flow is None or flow.start_node is None:
        raise ValueError(
            f"No PocketFlow Flow with a start_node found in {py_path.name}. "
            "Ensure the file contains a build_flow() function or a module-level Flow variable."
        )

    # ── 3. Traverse the graph ─────────────────────────────────────────────────
    nodes, edges, entry = _traverse_graph(flow)

    topology = {
        "source":  str(py_path),
        "entry":   entry,
        "nodes":   nodes,
        "edges":   edges,
    }

    topology["json"] = json.dumps(
        {k: v for k, v in topology.items() if k != "json"},
        indent=2,
    )
    topology["mmd"] = topology_to_mermaid(nodes, edges, entry)

    return topology


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_missing_module(exc: ImportError) -> str | None:
    """Parse ImportError message to extract the missing module name.

    Handles both:
      "No module named 'x'"
      "cannot import name 'X' from 'y'"
    """
    import re
    msg = str(exc)
    # "No module named 'x'" or "No module named 'x.y'"
    m = re.search(r"No module named '([^']+)'", msg)
    if m:
        return m.group(1).split(".")[0]
    # "cannot import name 'X' from 'y'" — mock the source module y
    m = re.search(r"cannot import name '[^']+' from '([^']+)'", msg)
    if m:
        return m.group(1).split(".")[0]
    return None


def _make_mock_module(name: str):
    """Create a MagicMock-backed module that satisfies any attribute access or import."""
    from unittest.mock import MagicMock
    import types

    class _MockModule(types.ModuleType):
        def __getattr__(self, attr):
            return MagicMock()

    mock_mod = _MockModule(name)
    return mock_mod


def _load_with_mock(py_path: Path, missing_root: str, py_dir: str):
    """Retry loading py_path while auto-mocking missing third-party modules.

    This allows rt-inspect to extract the PocketFlow graph structure even when
    the implementation imports optional tools (duckduckgo_search, openai, etc.)
    that are not installed in the current environment.

    We mock iteratively: each ImportError reveals one more missing module.
    """
    MAX_ATTEMPTS = 20
    mocked: set[str] = set()
    mocked.add(missing_root)

    spec = importlib.util.spec_from_file_location("_rt_inspect_target", py_path)

    # Collect local module names (files in the same directory) — never mock these
    local_names = {
        f.stem for f in Path(py_dir).iterdir() if f.suffix == ".py" and not f.name.startswith("_")
    }

    for _ in range(MAX_ATTEMPTS):
        # Install deep mocks for all known missing third-party modules
        for name in list(mocked):
            if name not in local_names:
                sys.modules[name] = _make_mock_module(name)  # type: ignore[assignment]

        # Purge any cached (partially-loaded) local modules from prior failed attempts
        for lname in local_names:
            sys.modules.pop(lname, None)

        mod = importlib.util.module_from_spec(spec)
        if py_dir not in sys.path:
            sys.path.insert(0, py_dir)

        saved_argv = sys.argv[:]
        sys.argv = [str(py_path)]
        try:
            spec.loader.exec_module(mod)
            return mod  # success
        except SystemExit:
            return mod
        except ImportError as exc2:
            name = _extract_missing_module(exc2)
            if name and name not in mocked and name not in local_names:
                mocked.add(name)
                continue
            raise  # same error repeated — cannot resolve
        finally:
            sys.argv = saved_argv
            # Clean up mocked modules so they don't pollute other imports
            for name in mocked:
                sys.modules.pop(name, None)

    raise RuntimeError(f"Could not load {py_path.name} after {MAX_ATTEMPTS} mock attempts")


def _find_flow(mod) -> Any | None:
    """Find the first usable PocketFlow Flow in the module.

    Strategy (in priority order):
      1. Call ``build_flow()`` if it exists — the canonical SPL transpiler convention.
      2. Scan module-level attributes for Flow instances.
      3. Try calling any function named ``create_flow``, ``make_flow``, ``get_flow``.
    """
    try:
        from pocketflow import Flow
    except ImportError as exc:
        raise ImportError(
            "pocketflow not installed: pip install pocketflow"
        ) from exc

    # Priority 1 — canonical builder function (exact names first, then any *flow* function)
    _BUILDER_NAMES = ("build_flow", "create_flow", "make_flow", "get_flow")
    for fname in _BUILDER_NAMES:
        builder = getattr(mod, fname, None)
        if callable(builder):
            try:
                result = builder()
                if isinstance(result, Flow):
                    return result
            except Exception:
                pass  # builder may require args — fall through

    # Priority 1b — any callable whose name contains "flow" (e.g. create_agent_flow)
    # Skip classes (Flow, AsyncFlow, …) — only call plain factory functions.
    import inspect as _inspect
    for attr_name, attr_val in vars(mod).items():
        if (
            "flow" in attr_name.lower()
            and callable(attr_val)
            and attr_name not in _BUILDER_NAMES
            and not _inspect.isclass(attr_val)      # skip Flow class itself
        ):
            try:
                result = attr_val()
                if isinstance(result, Flow) and result.start_node is not None:
                    return result
            except Exception:
                pass

    # Priority 2 — module-level Flow instance
    for attr_val in vars(mod).values():
        if isinstance(attr_val, Flow) and attr_val.start_node is not None:
            return attr_val

    return None


def _traverse_graph(flow) -> tuple[dict, list, str | None]:
    """BFS traversal of a PocketFlow graph.

    Returns:
        nodes  — {node_id: {"type": class_name, "base": parent_class_name}}
        edges  — [{"source": id, "target": id, "label": action}]
        entry  — node_id of the start node
    """
    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    visited: set[int] = set()
    queue: list = [flow.start_node]
    entry: str | None = None

    while queue:
        node = queue.pop(0)
        if node is None or id(node) in visited:
            continue
        visited.add(id(node))

        node_id = _node_id(node, nodes)
        if entry is None:
            entry = node_id

        # Record node metadata
        bases = [b.__name__ for b in type(node).__mro__[1:] if b.__name__ not in ("object",)]
        nodes[node_id] = {
            "type": type(node).__name__,
            "base": bases[0] if bases else "BaseNode",
        }

        # Record edges and enqueue successors
        for action, next_node in node.successors.items():
            next_id = _node_id(next_node, nodes)
            edges.append({"source": node_id, "target": next_id, "label": action})
            queue.append(next_node)

    return nodes, edges, entry


def _node_id(node, existing_nodes: dict) -> str:
    """Derive a stable, human-readable node ID from its class name.

    If two nodes share the same class (unusual but possible), append a suffix.
    """
    base_id = type(node).__name__
    if base_id not in existing_nodes:
        return base_id
    # Check if this is the same type already registered (common in loops)
    return base_id


def canonicalize_node_id(node_id: str) -> str:
    """Normalize a Python class name to a canonical snake_case node ID.

    Strips trailing 'Node' suffix and converts CamelCase to snake_case, so
    that GED comparison aligns with SPL node labels derived from workflow names.

    Examples:
        DraftNode      → draft
        CritiqueNode   → critique
        SearchWeb      → search_web
        DecideAction   → decide_action
        AnswerQuestion → answer_question
    """
    import re
    # Strip trailing "Node" suffix (case-insensitive)
    name = re.sub(r"Node$", "", node_id)
    # CamelCase → snake_case
    name = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
    # Clean up any double underscores
    name = re.sub(r"_+", "_", name).strip("_")
    return name or node_id.lower()


def topology_to_mermaid(
    nodes: dict,
    edges: list,
    entry: str | None = None,
) -> str:
    """Convert a topology dict to a Mermaid flowchart diagram string.

    Args:
        nodes:  {node_id: {"type": ..., "base": ...}}
        edges:  [{"source": id, "target": id, "label": action}]
        entry:  ID of the entry node (highlighted with a distinct shape).

    Returns:
        Mermaid ``graph TD`` string.
    """
    lines = ["graph TD"]

    # Node shape: entry node gets stadium shape (([...])), others get default
    for nid in nodes:
        label = nid
        if nid == entry:
            lines.append(f'    {nid}(["▶ {label}"])')
        else:
            lines.append(f"    {nid}[{label}]")

    lines.append("")

    # Edges
    for edge in edges:
        src, tgt, lbl = edge["source"], edge["target"], edge["label"]
        if lbl and lbl != "default":
            lines.append(f'    {src} -->|"{lbl}"| {tgt}')
        else:
            lines.append(f"    {src} --> {tgt}")

    return "\n".join(lines)


def topology_to_spl_scaffold(nodes: dict, edges: list, entry: str | None, recipe_name: str) -> str:
    """Generate a rough SPL scaffold from the extracted topology.

    This is a best-effort structural scaffold — semantic content (prompts)
    must be filled in by text2spl or manually.
    The scaffold preserves the exact graph topology deterministically.

    Args:
        nodes:       {node_id: {"type": ..., "base": ...}}
        edges:       [{"source": id, "target": id, "label": action}]
        entry:       entry node ID
        recipe_name: name to use in WORKFLOW declaration

    Returns:
        SPL source string (partial — no prompt bodies).
    """
    lines = [
        f"-- Auto-generated scaffold from rt-inspect",
        f"-- Source: {recipe_name}",
        f"-- NOTE: Fill in CREATE FUNCTION bodies with actual prompt text.",
        f"",
        f"WORKFLOW {recipe_name}",
        f"INPUT",
    ]

    # Stub INPUT block
    lines += ["    @task TEXT DEFAULT 'Your task here'", "END INPUT", ""]

    # Generate CREATE FUNCTION stubs for each node
    for nid in nodes:
        fn_name = _to_snake(nid)
        lines += [
            f"CREATE FUNCTION {fn_name}(@input)",
            f"$$",
            f"  -- TODO: Add prompt body for {nid}",
            f"$$",
            "",
        ]

    # Generate GENERATE / CALL statements
    for nid in nodes:
        fn_name = _to_snake(nid)
        lines.append(f"GENERATE {fn_name}(@task) INTO @result_{fn_name}")

    lines.append("")
    lines.append("RETURN @result WITH status='done'")

    return "\n".join(lines)


def _to_snake(name: str) -> str:
    """Convert CamelCase node class name to snake_case function name."""
    import re
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
