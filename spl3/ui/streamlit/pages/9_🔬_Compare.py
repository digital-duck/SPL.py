"""Page 9: Compare — multi-tier Intent Invariance comparison.

Gate 4 of the Intent Engineering platform:
  Compare two SPL files, two Mermaid diagrams, or an SPL design vs a
  rt-inspect topology JSON.  Runs GED + optional LLM + vector tiers and
  shows the Intent Invariance score with a diagnostic matrix.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
import spl3_rag_bridge as spl3_rag

SPL30_ROOT = spl3_rag.spl3_root()

st.set_page_config(page_title="Compare", layout="wide", page_icon="🔬")
st.header("🔬 Compare — Intent Invariance Score")
st.caption(
    "**Gate 4 — Intent Engineering platform.**  "
    "Compare two SPL designs, two Mermaid diagrams, or an SPL design vs a "
    "rt-inspect topology.  Computes Graph Edit Distance and Intent Invariance score."
)

# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.subheader("Input A — Reference (SPL design)")
    input_a_mode = st.radio("A source", ["Paste Mermaid (.mmd)", "Enter .spl file path"],
                            key="mode_a")
    if input_a_mode == "Paste Mermaid (.mmd)":
        content_a = st.text_area("Mermaid A", height=200,
                                 placeholder="flowchart TD\n  A --> B\n  ...",
                                 key="mmd_a")
    else:
        spl_a_path = st.text_input("Path to .spl file",
                                   placeholder="/path/to/design.spl", key="spl_a")
        content_a = ""
        if spl_a_path and Path(spl_a_path).exists():
            try:
                from spl3.spl2mmd import spl_to_mermaid
                content_a = spl_to_mermaid(Path(spl_a_path).read_text(encoding="utf-8"))
                st.success(f"Loaded and converted: {Path(spl_a_path).name}")
            except Exception as exc:
                st.error(f"spl2mmd failed: {exc}")
        elif spl_a_path:
            st.warning("File not found")

    st.divider()
    st.subheader("Input B — Implementation")
    input_b_mode = st.radio("B source",
                            ["Paste Mermaid (.mmd)", "Paste topology JSON", "Enter .py file path"],
                            key="mode_b")
    if input_b_mode == "Paste Mermaid (.mmd)":
        content_b = st.text_area("Mermaid B", height=200,
                                 placeholder="flowchart TD\n  A --> B\n  ...",
                                 key="mmd_b")
    elif input_b_mode == "Paste topology JSON":
        content_b = st.text_area("Topology JSON", height=200,
                                 placeholder='{"nodes": {...}, "edges": [...]}',
                                 key="json_b")
    else:
        py_b_path = st.text_input("Path to .py file",
                                  placeholder="/path/to/impl.py", key="py_b")
        content_b = ""
        if py_b_path and Path(py_b_path).exists():
            try:
                import tempfile
                from spl3.splc.rt_inspect import (
                    inspect_pocketflow_file, canonicalize_node_id, topology_to_mermaid
                )
                result = inspect_pocketflow_file(Path(py_b_path))
                nodes, edges, entry = result["nodes"], result["edges"], result["entry"]
                id_map = {nid: canonicalize_node_id(nid) for nid in nodes}
                c_nodes = {id_map[nid]: meta for nid, meta in nodes.items()}
                c_edges = [{"source": id_map.get(e["source"], e["source"]),
                            "target": id_map.get(e["target"], e["target"]),
                            "label": e.get("label", "")} for e in edges]
                c_entry = id_map.get(entry, entry) if entry else entry
                content_b = json.dumps({"entry": c_entry, "nodes": c_nodes, "edges": c_edges})
                st.success(f"rt-inspect: {len(c_nodes)} nodes, {len(c_edges)} edges")
            except NotImplementedError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"rt-inspect failed: {exc}")
        elif py_b_path:
            st.warning("File not found")

    st.divider()
    st.subheader("Tiers")
    run_ged    = st.checkbox("GED (topology)", value=True)
    run_llm    = st.checkbox("LLM (semantic)", value=False)
    run_vector = st.checkbox("Vector (embedding)", value=False)
    if run_llm or run_vector:
        llm_adapter = st.text_input("Adapter", value="anthropic", key="adapter")
        llm_model   = st.text_input("Model", value="", key="model")

# ── Main ───────────────────────────────────────────────────────────────────────

run_btn = st.button("▶  Run Comparison", type="primary",
                    disabled=not (content_a and content_b))

if not content_a or not content_b:
    st.info("Fill in both Input A and Input B in the sidebar, then click **Run Comparison**.")

if run_btn and content_a and content_b:
    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        st.caption("**Input A** (Reference)")
        display_a = content_a if not content_a.strip().startswith("{") else "(topology JSON)"
        st.code(display_a[:800] + ("…" if len(display_a) > 800 else ""), language="mermaid")
    with col_b:
        st.caption("**Input B** (Implementation)")
        display_b = content_b if not content_b.strip().startswith("{") else "(topology JSON)"
        st.code(display_b[:800] + ("…" if len(display_b) > 800 else ""), language="mermaid")

    st.divider()
    st.subheader("Results")

    score_cols = st.columns(4)
    ged_score = llm_score = vec_score = None

    # ── GED tier ──────────────────────────────────────────────────────────────
    if run_ged:
        with st.spinner("Computing Graph Edit Distance …"):
            try:
                from spl3.compare.tiers.ged import compare_ged
                ged_result = compare_ged(content_a, content_b)
                if isinstance(ged_result, str):
                    st.error(f"GED: {ged_result}")
                else:
                    dist  = ged_result.distance
                    norm  = ged_result.normalized_distance
                    ged_score = round((1.0 - norm) * 10, 2)
                    with score_cols[0]:
                        st.metric("GED raw", f"{dist:.1f}")
                    with score_cols[1]:
                        st.metric("GED normalized", f"{norm:.3f}")
                    with score_cols[2]:
                        st.metric("Intent Invariance (GED)", f"{ged_score:.1f}/10")

                    with st.expander("GED details"):
                        st.json({
                            "distance": dist,
                            "normalized_distance": norm,
                            "node_counts": ged_result.node_count,
                            "edge_counts": ged_result.edge_count,
                            "node_types":  ged_result.node_types,
                        })
            except Exception as exc:
                st.error(f"GED failed: {exc}")

    # ── LLM tier ──────────────────────────────────────────────────────────────
    if run_llm:
        with st.spinner("Running LLM comparison …"):
            try:
                from spl3.compare.tiers.llm import compare_llm
                llm_result = compare_llm(
                    content_a, content_b,
                    adapter=llm_adapter, model=llm_model or None,
                )
                if isinstance(llm_result, str):
                    st.error(f"LLM: {llm_result}")
                else:
                    llm_score = llm_result.score
                    with score_cols[3]:
                        st.metric("LLM Semantic Score", f"{llm_score:.1f}/10")
                    with st.expander("LLM details"):
                        st.write(llm_result.explanation)
            except Exception as exc:
                st.error(f"LLM comparison failed: {exc}")

    # ── Vector tier ───────────────────────────────────────────────────────────
    if run_vector:
        with st.spinner("Computing vector similarity …"):
            try:
                from spl3.compare.tiers.vector import compare_vector
                vec_result = compare_vector(
                    content_a, content_b,
                    adapter=llm_adapter, model=llm_model or None,
                )
                if isinstance(vec_result, str):
                    st.error(f"Vector: {vec_result}")
                else:
                    vec_score = vec_result.score
                    st.metric("Vector Similarity", f"{vec_score:.3f}")
            except Exception as exc:
                st.error(f"Vector comparison failed: {exc}")

    # ── Diagnostic matrix ─────────────────────────────────────────────────────
    st.divider()
    st.subheader("Diagnosis")
    if ged_score is not None:
        norm_ged = 1.0 - ged_score / 10.0
        if norm_ged < 0.1:
            st.success("✓ Low GED — topology matches design. Structure is preserved.")
        elif norm_ged < 0.3:
            st.warning("⚠ Moderate GED — some structural drift. Review diagrams above.")
        else:
            st.error(
                "✗ High GED — significant topology mismatch.  "
                "The implementation diverges from the SPL design. "
                "Check Gate 1 (Mermaid review) and recompile."
            )

        if llm_score is not None:
            st.markdown("**Root-cause matrix** (GED × LLM):")
            if norm_ged < 0.3 and llm_score >= 7:
                st.success("Low GED + High LLM → Structure and semantics both preserved. ✓")
            elif norm_ged < 0.3 and llm_score < 7:
                st.warning("Low GED + Low LLM → Structure preserved but semantic drift detected. "
                           "Likely prompt body changes.")
            elif norm_ged >= 0.3 and llm_score >= 7:
                st.warning("High GED + High LLM → Structure drifted but intent preserved. "
                           "Refactor may have changed topology without changing meaning.")
            else:
                st.error("High GED + Low LLM → Both structure and semantics diverged. "
                         "Full recompile recommended.")
    else:
        st.info("Run GED tier to see diagnosis.")
