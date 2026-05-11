"""Page 7: Ablation Results — NeurIPS-26 round-trip closure experiment.

Scans the NeurIPS-26-lab/ filesystem for S6/S9/S10 result files, extracts
numeric scores, and builds the ablation comparison table for the paper.

Phase 1 (full IR pipeline):   S6 score = ΔS after S1→S2→S3→S4→S5→S6
Phase 2 (vibe bypass ablation): S9 score = ΔS after S1→S7→S8→S9
ΔIR = S6 − S9  (positive = IR pipeline added value)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from ui_config import NEURIPS_RECIPES, NEURIPS_RECIPE_DIRS, NEURIPS_MODELS
from ui_utils import extract_compare_score, get_memory_db

# ── Lab root ──────────────────────────────────────────────────────────────────

_HERE = Path(__file__).parent.parent.parent.parent.parent  # SPL.py root
LAB_ROOT = _HERE / "NeurIPS-26-lab"

st.set_page_config(page_title="Ablation Results", layout="wide")
st.header("NeurIPS-26 — Ablation Results Dashboard")
st.caption(
    "Round-trip closure scores across 5 recipes × 3 models. "
    "ΔIR = S6 (full IR pipeline) − S9 (vibe bypass). "
    "Positive ΔIR = intermediate representations add value."
)

if not LAB_ROOT.exists():
    st.error(f"NeurIPS-26-lab not found at `{LAB_ROOT}`. Check the path.")
    st.stop()

# ── Score extraction ──────────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def _load_scores() -> dict:
    """Scan S6/S9/S10 files and MemoryDB; merge results (filesystem wins on conflict)."""
    # Pre-load DB scores as fallback
    db_s6, db_s9 = {}, {}
    try:
        mdb = get_memory_db()
        for row in mdb.pipeline_scores_matrix("neurips_ndd", "S6"):
            db_s6[row["run_label"]] = row
        for row in mdb.pipeline_scores_matrix("neurips_ndd", "S9"):
            db_s9[row["run_label"]] = row
    except Exception:
        pass  # DB unavailable — filesystem-only mode

    scores: dict = {}
    for recipe in NEURIPS_RECIPES:
        scores[recipe] = {}
        recipe_dir = LAB_ROOT / NEURIPS_RECIPE_DIRS[recipe]
        for m in NEURIPS_MODELS:
            alias = m["alias"]
            adapter = m["adapter"]
            run_label = f"{recipe}/{alias}"
            out_dir = recipe_dir / "tests" / adapter / alias

            # S6: filesystem first, then DB
            s6_score, s6_path = None, None
            if out_dir.exists():
                for f in sorted(out_dir.glob("S6-*.md"), reverse=True):
                    if "ablation" in f.name or "vibe" in f.name:
                        continue
                    text = f.read_text(encoding="utf-8", errors="replace")
                    s6_score = extract_compare_score(text)
                    s6_path = f
                    if s6_score is not None:
                        break
            if s6_score is None and run_label in db_s6:
                s6_score = db_s6[run_label].get("score")

            # S9: filesystem first, then DB
            s9_score, s9_path = None, None
            if out_dir.exists():
                for f in sorted(out_dir.glob("S9-*.md"), reverse=True):
                    text = f.read_text(encoding="utf-8", errors="replace")
                    s9_score = extract_compare_score(text)
                    s9_path = f
                    if s9_score is not None:
                        break
            if s9_score is None and run_label in db_s9:
                s9_score = db_s9[run_label].get("score")

            # S10: filesystem only (narrative text, not just a score)
            s10_text = None
            if out_dir.exists():
                s10_files = sorted(out_dir.glob("S10-*.md"), reverse=True)
                s10_text = s10_files[0].read_text(encoding="utf-8", errors="replace") if s10_files else None

            # Checkpoint status from DB
            s6_checkpoint = db_s6.get(run_label, {}).get("checkpoint_passed", False)

            scores[recipe][alias] = {
                "s6": s6_score,
                "s9": s9_score,
                "s10_text": s10_text,
                "s6_path": str(s6_path) if s6_path else None,
                "s9_path": str(s9_path) if s9_path else None,
                "s6_checkpoint": bool(s6_checkpoint),
            }
    return scores


def _completion_stats(scores: dict) -> tuple[int, int, int]:
    total = len(NEURIPS_RECIPES) * len(NEURIPS_MODELS)
    p1_done = sum(
        1 for r in NEURIPS_RECIPES for m in NEURIPS_MODELS
        if scores[r][m["alias"]]["s6"] is not None
    )
    p2_done = sum(
        1 for r in NEURIPS_RECIPES for m in NEURIPS_MODELS
        if scores[r][m["alias"]]["s9"] is not None
    )
    return total, p1_done, p2_done


scores = _load_scores()
total, p1_done, p2_done = _completion_stats(scores)

# ── Completion tracker ────────────────────────────────────────────────────────

c1, c2, c3 = st.columns(3)
c1.metric("Total runs", total)
c2.metric("Phase 1 complete (S6)", f"{p1_done}/{total}")
c3.metric("Phase 2 complete (S9)", f"{p2_done}/{total}")

if st.button("🔄 Refresh scores", key="btn_refresh"):
    st.cache_data.clear()
    st.rerun()

st.divider()

# ── Ablation table ────────────────────────────────────────────────────────────

aliases = [m["alias"] for m in NEURIPS_MODELS]

rows = []
for recipe in NEURIPS_RECIPES:
    row: dict = {"Recipe": recipe}
    for alias in aliases:
        s = scores[recipe][alias]
        s6 = s["s6"]
        s9 = s["s9"]
        delta = round(s6 - s9, 3) if (s6 is not None and s9 is not None) else None
        row[f"{alias} S6"] = round(s6, 3) if s6 is not None else "—"
        row[f"{alias} S9"] = round(s9, 3) if s9 is not None else "—"
        row[f"{alias} ΔIR"] = (f"+{delta}" if delta and delta > 0 else str(delta)) if delta is not None else "—"
    rows.append(row)

# Mean row
mean_row: dict = {"Recipe": "**Mean**"}
for alias in aliases:
    s6_vals = [scores[r][alias]["s6"] for r in NEURIPS_RECIPES if scores[r][alias]["s6"] is not None]
    s9_vals = [scores[r][alias]["s9"] for r in NEURIPS_RECIPES if scores[r][alias]["s9"] is not None]
    mean_s6 = round(sum(s6_vals) / len(s6_vals), 3) if s6_vals else "—"
    mean_s9 = round(sum(s9_vals) / len(s9_vals), 3) if s9_vals else "—"
    if isinstance(mean_s6, float) and isinstance(mean_s9, float):
        d = round(mean_s6 - mean_s9, 3)
        mean_row[f"{alias} ΔIR"] = f"+{d}" if d > 0 else str(d)
    else:
        mean_row[f"{alias} ΔIR"] = "—"
    mean_row[f"{alias} S6"] = mean_s6
    mean_row[f"{alias} S9"] = mean_s9
rows.append(mean_row)

df = pd.DataFrame(rows)
st.subheader("Ablation Table")
st.caption("S6 = full IR pipeline · S9 = vibe bypass · ΔIR = S6 − S9")
st.dataframe(df.set_index("Recipe"), use_container_width=True)

# ── Export ────────────────────────────────────────────────────────────────────

st.divider()
col_csv, col_latex = st.columns(2)

with col_csv:
    csv = df.to_csv(index=False)
    st.download_button("Download CSV", csv, "ablation_results.csv", "text/csv", key="dl_csv")

with col_latex:
    # Build a simple LaTeX tabular
    cols = list(df.columns)
    header = " & ".join(f"\\textbf{{{c}}}" for c in cols) + " \\\\"
    lines = ["\\begin{tabular}{l" + "r" * (len(cols) - 1) + "}", "\\hline", header, "\\hline"]
    for _, row_data in df.iterrows():
        lines.append(" & ".join(str(v) for v in row_data.values) + " \\\\")
    lines += ["\\hline", "\\end{tabular}"]
    latex = "\n".join(lines)
    st.download_button("Download LaTeX", latex, "ablation_results.tex", "text/plain", key="dl_latex")

# ── Per-cell drill-down ───────────────────────────────────────────────────────

st.divider()
st.subheader("Drill-down — view report")

col_r, col_m, col_s = st.columns(3)
with col_r:
    sel_recipe = st.selectbox("Recipe", NEURIPS_RECIPES, key="dd_recipe")
with col_m:
    sel_alias = st.selectbox("Model", aliases, key="dd_model")
with col_s:
    sel_step = st.selectbox("Report", ["S6 (IR diff)", "S9 (vibe diff)", "S10 (ablation)"], key="dd_step")

sel_data = scores[sel_recipe][sel_alias]

def _read_or_none(path_str: str | None) -> str | None:
    if path_str and Path(path_str).exists():
        return Path(path_str).read_text(encoding="utf-8", errors="replace")
    return None

if sel_step.startswith("S6"):
    content = _read_or_none(sel_data["s6_path"])
elif sel_step.startswith("S9"):
    content = _read_or_none(sel_data["s9_path"])
else:
    content = sel_data["s10_text"]

if content:
    score_val = sel_data["s6"] if sel_step.startswith("S6") else sel_data["s9"]
    if score_val is not None and not sel_step.startswith("S10"):
        st.metric("Score", round(score_val, 3))
    st.markdown(content)
else:
    st.info(f"No {sel_step.split()[0]} file found for {sel_recipe} / {sel_alias}. Run the experiment first.")

# ── Missing runs list ─────────────────────────────────────────────────────────

with st.expander("Incomplete runs", expanded=False):
    missing = []
    for recipe in NEURIPS_RECIPES:
        for m in NEURIPS_MODELS:
            s = scores[recipe][m["alias"]]
            if s["s6"] is None:
                missing.append(f"Phase 1 missing: {recipe} / {m['alias']}")
            elif s["s9"] is None:
                missing.append(f"Phase 2 missing: {recipe} / {m['alias']}")
    if missing:
        for item in missing:
            st.write(f"- {item}")
    else:
        st.success("All runs complete!")
