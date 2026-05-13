"""Page 8: RT-Inspect — deterministic PocketFlow topology extraction.

Gate 3 of the Intent Engineering platform:
  Upload a compiled Python/PocketFlow file → extract topology → visualise as Mermaid
  Optionally compare against SPL-derived Mermaid → compute GED score.

No LLM required for topology extraction (rt-inspect mode).
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
import spl3_rag_bridge as spl3_rag

SPL30_ROOT = spl3_rag.spl3_root()

# ── Page config ────────────────────────────────────────────────────────────────

st.set_page_config(page_title="RT-Inspect", layout="wide", page_icon="🔍")
st.header("🔍 RT-Inspect — Runtime Topology Extraction")
st.caption(
    "**Gate 3 — Intent Engineering platform.**  "
    "Upload a compiled Python/PocketFlow file and deterministically extract "
    "its graph topology (no LLM required). "
    "Optionally compare against the SPL-derived Mermaid to compute an Intent Invariance score."
)

# ── Mermaid renderer (CDN) ─────────────────────────────────────────────────────

def _render_mermaid(mmd_text: str, height: int = 400) -> None:
    """Render Mermaid diagram inline via CDN."""
    import streamlit.components.v1 as components
    html = f"""
    <div class="mermaid" style="background:#fff; padding:16px; border-radius:8px;">
    {mmd_text}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>mermaid.initialize({{startOnLoad:true, theme:'default'}});</script>
    """
    components.html(html, height=height, scrolling=True)


# ── Sidebar: input options ─────────────────────────────────────────────────────

with st.sidebar:
    st.subheader("Input")
    input_mode = st.radio(
        "Source",
        ["Upload .py file", "Enter file path", "Use existing topology JSON"],
        index=0,
    )

    canonicalize = st.checkbox(
        "Canonicalize node names",
        value=True,
        help=(
            "Strip 'Node' suffix and convert CamelCase to snake_case "
            "(DraftNode → draft). Required for accurate GED comparison with SPL."
        ),
    )

    st.divider()
    st.subheader("GED Comparison (optional)")
    compare_mmd = st.text_area(
        "Paste SPL Mermaid (.mmd) here",
        height=150,
        placeholder="flowchart TD\n    A --> B\n    ...",
        help=(
            "Run 'spl3 spl2mmd <file.spl>' and paste the output here "
            "to compute the Graph Edit Distance between the SPL design and "
            "the PocketFlow implementation."
        ),
    )

# ── Main: input handling ───────────────────────────────────────────────────────

py_path: Path | None = None
topology_data: dict | None = None

if input_mode == "Upload .py file":
    uploaded = st.file_uploader("Upload Python/PocketFlow file", type=["py"])
    if uploaded:
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="wb") as tmp:
            tmp.write(uploaded.read())
            py_path = Path(tmp.name)

elif input_mode == "Enter file path":
    path_str = st.text_input(
        "Absolute path to .py file",
        placeholder="/home/user/project/self_refine_python_pocketflow.py",
    )
    if path_str and Path(path_str).exists():
        py_path = Path(path_str)
    elif path_str:
        st.warning(f"File not found: {path_str}")

elif input_mode == "Use existing topology JSON":
    json_str = st.text_area(
        "Paste topology JSON",
        height=200,
        placeholder='{"nodes": {...}, "edges": [...], "entry": "..."}',
    )
    if json_str.strip():
        try:
            topology_data = json.loads(json_str)
            st.success("JSON parsed successfully.")
        except json.JSONDecodeError as exc:
            st.error(f"Invalid JSON: {exc}")

# ── Run rt-inspect ─────────────────────────────────────────────────────────────

if py_path and topology_data is None:
    with st.spinner("Running rt-inspect (deterministic, no LLM) …"):
        try:
            from spl3.splc.rt_inspect import inspect_pocketflow_file
            result = inspect_pocketflow_file(py_path)
            topology_data = {
                "source": result["source"],
                "entry":  result["entry"],
                "nodes":  result["nodes"],
                "edges":  result["edges"],
            }
            st.success(
                f"Extracted topology: **{len(result['nodes'])} nodes**, "
                f"**{len(result['edges'])} edges** — entry: `{result['entry']}`"
            )
        except Exception as exc:
            st.error(f"rt-inspect failed: {exc}")

# ── Display topology ───────────────────────────────────────────────────────────

if topology_data:
    from spl3.splc.rt_inspect import topology_to_mermaid, canonicalize_node_id

    nodes = topology_data.get("nodes", {})
    edges = topology_data.get("edges", [])
    entry = topology_data.get("entry")

    if canonicalize:
        id_map = {nid: canonicalize_node_id(nid) for nid in nodes}
        nodes = {id_map[nid]: meta for nid, meta in nodes.items()}
        edges = [
            {"source": id_map.get(e["source"], e["source"]),
             "target": id_map.get(e["target"], e["target"]),
             "label":  e.get("label", "")}
            for e in edges
        ]
        entry = id_map.get(entry, entry) if entry else entry

    mmd_text = topology_to_mermaid(nodes, edges, entry)

    tab_graph, tab_json, tab_mmd = st.tabs(["Topology Graph", "JSON", "Mermaid code"])

    with tab_graph:
        _render_mermaid(mmd_text, height=450)

    with tab_json:
        st.json({"entry": entry, "nodes": nodes, "edges": edges})

    with tab_mmd:
        st.code(mmd_text, language="mermaid")
        st.download_button(
            "Download .mmd",
            data=mmd_text,
            file_name="rt-inspect-topology.mmd",
            mime="text/plain",
        )

    # ── GED comparison ─────────────────────────────────────────────────────────
    if compare_mmd.strip():
        st.divider()
        st.subheader("GED Comparison — Intent Invariance Score")

        col_spl, col_rt = st.columns(2)
        with col_spl:
            st.caption("SPL-derived Mermaid")
            st.code(compare_mmd, language="mermaid")
        with col_rt:
            st.caption("RT-Inspect Mermaid")
            st.code(mmd_text, language="mermaid")

        with st.spinner("Computing Graph Edit Distance …"):
            try:
                from spl3.compare.tiers.ged import compare_ged
                ged_result = compare_ged(compare_mmd, mmd_text)

                if isinstance(ged_result, str):
                    st.error(ged_result)
                else:
                    dist = ged_result.distance
                    norm = ged_result.normalized_distance
                    score = round((1.0 - norm) * 10, 2)

                    c1, c2, c3 = st.columns(3)
                    c1.metric("GED (raw)", f"{dist:.1f}")
                    c2.metric("GED (normalized)", f"{norm:.3f}")
                    c3.metric(
                        "Intent Invariance Score",
                        f"{score:.1f} / 10",
                        delta=None,
                        help="(1 - normalized_GED) × 10. Higher = better topology match.",
                    )

                    # Diagnostic matrix
                    st.subheader("Diagnosis")
                    if norm < 0.1:
                        st.success("Low GED — topology matches the SPL design. Structure is preserved.")
                    elif norm < 0.3:
                        st.warning("Moderate GED — some structural drift. Review Mermaid diagrams above.")
                    else:
                        st.error(
                            "High GED — significant topology mismatch. "
                            "The implementation structure diverges from the SPL design. "
                            "Check Gate 1 (Mermaid review) and recompile."
                        )

                    with st.expander("Full GED details"):
                        st.json({
                            "distance":            ged_result.distance,
                            "normalized_distance": ged_result.normalized_distance,
                            "node_counts":         ged_result.node_count,
                            "edge_counts":         ged_result.edge_count,
                            "node_types":          ged_result.node_types,
                        })
            except Exception as exc:
                st.error(f"GED computation failed: {exc}")

    # ── Download topology JSON ─────────────────────────────────────────────────
    st.divider()
    json_str = json.dumps({"entry": entry, "nodes": nodes, "edges": edges}, indent=2)
    st.download_button(
        "Download topology.json",
        data=json_str,
        file_name="rt-inspect-topology.json",
        mime="application/json",
    )
    st.caption(
        "Use this JSON with: `spl3 compare --mode ged <spl.mmd> rt-inspect-topology.json`"
    )

else:
    if input_mode != "Use existing topology JSON":
        st.info(
            "Upload or enter a Python/PocketFlow file above to extract its topology.  \n"
            "The rt-inspect engine loads the file, calls the `build_flow()` function, "
            "and traverses `node.successors` — no LLM required."
        )
