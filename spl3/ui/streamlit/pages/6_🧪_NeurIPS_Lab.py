"""Page 6: NeurIPS Lab — supervised experiment runner for the NDD round-trip closure study.

Replaces the hand-edited shell scripts (claude_cli-S8910.sh, openrouter-*.sh) with a
UI that shows the full 15-run matrix (5 recipes × 3 models), lets you run individual
steps, tracks human checkpoint status, and streams CLI output live.

Pipeline reference:
  Phase 1 (full IR):   S1 → S2 → S3 → S4 → S5 → S6
  Phase 2 (ablation):  S7 → S8 → S9 → S10
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from ui_config import (
    NEURIPS_RECIPES, NEURIPS_RECIPE_DIRS, NEURIPS_MODELS,
    JUDGE_ADAPTER, JUDGE_MODEL,
)

# ── Lab root ──────────────────────────────────────────────────────────────────

_HERE = Path(__file__).parent.parent.parent.parent.parent  # SPL.py root
LAB_ROOT = _HERE / "NeurIPS-26-lab"

# ── Step definitions ──────────────────────────────────────────────────────────

# Each step entry: label, phase, has_human_checkpoint, automated
STEPS = {
    "S1":  ("Describe source → spec",          1, True),
    "S2":  ("Spec → Mermaid diagram",           1, True),
    "S3":  ("Mermaid → SPL script",             1, True),
    "S4":  ("SPL → PocketFlow Python",          1, True),
    "S5":  ("Describe generated code → spec",   1, False),
    "S6":  ("Compare spec1 vs spec2 (ΔS)",      1, True),
    "S7":  ("Vibe: spec → code (bypass IR)",    2, True),
    "S8":  ("Describe vibe code → spec",        2, False),
    "S9":  ("Compare spec1 vs vibe-spec (ΔS)",  2, False),
    "S10": ("Meta-compare S6 vs S9 (ΔIR)",      2, True),
}

STEP_EXTENSIONS = {
    "S1": "-1-spec.md", "S2": ".mmd", "S3": "-spl*.spl",
    "S4": ".py",        "S5": "-2-spec.md", "S6": "-spec-diff.md",
    "S7": "vibe/",      "S8": "-3-spec.md", "S9": "-vibe-diff.md",
    "S10": "-ablation.md",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _out_dir(recipe: str, adapter: str, alias: str) -> Path:
    return LAB_ROOT / NEURIPS_RECIPE_DIRS[recipe] / "tests" / adapter / alias


def _step_exists(recipe: str, adapter: str, alias: str, step: str) -> bool:
    d = _out_dir(recipe, adapter, alias)
    ext = STEP_EXTENSIONS.get(step, "")
    if ext.endswith("/"):
        return (d / ext.rstrip("/")).exists()
    if "*" in ext:
        return bool(list(d.glob(f"{step}-*{ext.split('*')[1]}")))
    return bool(list(d.glob(f"{step}-*{ext}")))


def _badge(recipe: str, adapter: str, alias: str, step: str) -> str:
    if _step_exists(recipe, adapter, alias, step):
        return "✅"
    return "🔲"


@st.cache_data(ttl=15)
def _build_matrix() -> list[list[str]]:
    """Return matrix[recipe_idx][model_idx] as a compact status string."""
    matrix = []
    for recipe in NEURIPS_RECIPES:
        row = []
        for m in NEURIPS_MODELS:
            alias, adapter = m["alias"], m["adapter"]
            badges = "".join(_badge(recipe, adapter, alias, s) for s in STEPS)
            row.append(badges)
        matrix.append(row)
    return matrix


def _build_cmd(recipe: str, adapter: str, alias: str, model_id: str, step: str) -> list[str] | None:
    """Build the spl3 CLI command for the given step."""
    out = _out_dir(recipe, adapter, alias)
    out.mkdir(parents=True, exist_ok=True)
    src_dir = LAB_ROOT / NEURIPS_RECIPE_DIRS[recipe] / "src"

    def p(pattern: str) -> str | None:
        """Find latest file matching pattern in out_dir."""
        hits = sorted(out.glob(pattern), reverse=True)
        return str(hits[0]) if hits else None

    if step == "S1":
        out_file = out / f"S1-{recipe}-{adapter}-{alias}-1-spec.md"
        return [
            "spl3", "splc", "describe", str(src_dir),
            "--adapter", adapter, "--model", model_id,
            "--include-docs", "-o", str(out_file),
        ]

    if step == "S2":
        s1 = p("S1-*-1-spec.md")
        if not s1:
            return None
        out_file = out / f"S2-{recipe}-{adapter}-{alias}.mmd"
        return [
            "spl3", "text2mmd", s1,
            "--adapter", adapter, "--model", model_id,
            "-o", str(out_file),
        ]

    if step == "S3":
        s2 = p("S2-*.mmd")
        if not s2:
            return None
        ts = time.strftime("%Y%m%d_%H%M%S")
        out_file = out / f"S3-{recipe}-{adapter}-{alias}-spl-{ts}.spl"
        return [
            "spl3", "mmd2spl", s2,
            "--adapter", adapter, "--model", model_id,
            "-o", str(out_file),
        ]

    if step == "S4":
        s3 = p("S3-*.spl")
        if not s3:
            return None
        out_dir_s4 = out / "python_pocketflow"
        return [
            "spl3", "splc", "compile", s3,
            "--lang", "python/pocketflow",
            "--adapter", adapter, "--model", model_id,
            "--out-dir", str(out_dir_s4), "--overwrite", "-v",
        ]

    if step == "S5":
        s4_dir = out / "python_pocketflow"
        if not s4_dir.exists():
            return None
        out_file = out / f"S5-{recipe}-{adapter}-{alias}-2-spec.md"
        return [
            "spl3", "splc", "describe", str(s4_dir),
            "--adapter", adapter, "--model", model_id,
            "-o", str(out_file),
        ]

    if step == "S6":
        s1 = p("S1-*-1-spec.md")
        s5 = p("S5-*-2-spec.md")
        if not s1 or not s5:
            return None
        out_file = out / f"S6-{recipe}-{adapter}-{alias}-spec-diff.md"
        return [
            "spl3", "compare", s1, s5,
            "--adapter", JUDGE_ADAPTER, "--model", JUDGE_MODEL,
            "-o", str(out_file),
        ]

    if step == "S7":
        s1 = p("S1-*-1-spec.md")
        if not s1:
            return None
        vibe_dir = out / "vibe"
        return [
            "spl3", "vibe", "--description", s1,
            "--out-dir", str(vibe_dir),
            "--adapter", adapter, "--model", model_id,
        ]

    if step == "S8":
        vibe_dir = out / "vibe" / "python_pocketflow"
        if not vibe_dir.exists():
            return None
        out_file = out / f"S8-{recipe}-{adapter}-{alias}-3-spec.md"
        return [
            "spl3", "splc", "describe", str(vibe_dir),
            "--adapter", adapter, "--model", model_id,
            "-o", str(out_file),
        ]

    if step == "S9":
        s1 = p("S1-*-1-spec.md")
        s8 = p("S8-*-3-spec.md")
        if not s1 or not s8:
            return None
        out_file = out / f"S9-{recipe}-{adapter}-{alias}-vibe-diff.md"
        return [
            "spl3", "compare", s1, s8,
            "--adapter", JUDGE_ADAPTER, "--model", JUDGE_MODEL,
            "-o", str(out_file),
        ]

    if step == "S10":
        s6 = p("S6-*-spec-diff.md")
        s9 = p("S9-*-vibe-diff.md")
        if not s6 or not s9:
            return None
        out_file = out / f"S10-{recipe}-{adapter}-{alias}-ablation.md"
        return [
            "spl3", "compare", s6, s9,
            "--adapter", JUDGE_ADAPTER, "--model", JUDGE_MODEL,
            "-o", str(out_file),
        ]

    return None


# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(page_title="NeurIPS Lab", layout="wide")
st.header("NeurIPS-26 Lab — Experiment Runner")
st.caption(
    "5 recipes × 3 models × 10 steps (S1–S10).  "
    "Phase 1: full IR pipeline (S1→S6).  "
    "Phase 2: ablation / vibe bypass (S7→S10)."
)

if not LAB_ROOT.exists():
    st.error(f"NeurIPS-26-lab not found at `{LAB_ROOT}`")
    st.stop()

# ── Matrix overview ───────────────────────────────────────────────────────────

st.subheader("Experiment Matrix")
st.caption("Each cell shows step completion: " + " ".join(STEPS.keys()) + " (✅ done / 🔲 missing)")

matrix = _build_matrix()
aliases = [m["alias"] for m in NEURIPS_MODELS]

header_cols = st.columns([2] + [3] * len(NEURIPS_MODELS))
header_cols[0].markdown("**Recipe**")
for i, alias in enumerate(aliases):
    header_cols[i + 1].markdown(f"**{alias}**")

for ri, recipe in enumerate(NEURIPS_RECIPES):
    row_cols = st.columns([2] + [3] * len(NEURIPS_MODELS))
    row_cols[0].markdown(f"`{recipe}`")
    for mi in range(len(NEURIPS_MODELS)):
        row_cols[mi + 1].code(matrix[ri][mi], language=None)

if st.button("🔄 Refresh matrix", key="btn_refresh_matrix"):
    st.cache_data.clear()
    st.rerun()

st.divider()

# ── Step runner ───────────────────────────────────────────────────────────────

st.subheader("Step Runner")

run_col1, run_col2, run_col3, run_col4 = st.columns(4)
with run_col1:
    sel_recipe = st.selectbox("Recipe", NEURIPS_RECIPES, key="run_recipe")
with run_col2:
    sel_alias = st.selectbox("Model", aliases, key="run_model")
with run_col3:
    sel_step = st.selectbox("Step", list(STEPS.keys()), key="run_step")
with run_col4:
    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button("▶ Run step", type="primary", key="btn_run_step")

# Show selected model metadata
sel_model_cfg = next(m for m in NEURIPS_MODELS if m["alias"] == sel_alias)
step_label, step_phase, step_checkpoint = STEPS[sel_step]
st.caption(
    f"**{sel_step}:** {step_label}  ·  "
    f"Phase {step_phase}  ·  "
    f"{'⚠ Human checkpoint' if step_checkpoint else '🤖 Automated'}"
)

# Build and show command preview
cmd = _build_cmd(sel_recipe, sel_model_cfg["adapter"], sel_model_cfg["alias"], sel_model_cfg["model_id"], sel_step)
if cmd:
    with st.expander("CLI command", expanded=False):
        st.code(" ".join(cmd), language="bash")
else:
    st.warning(f"Cannot build command for {sel_step} — prerequisite files missing. Run earlier steps first.")

# Execute
if run_btn and cmd and sel_alias:
    st.cache_data.clear()
    output_area = st.empty()
    with st.spinner(f"Running {sel_step} for {sel_recipe}/{sel_alias}…"):
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            output = proc.stdout + ("\n" + proc.stderr if proc.stderr.strip() else "")
            if proc.returncode == 0:
                st.success(f"{sel_step} completed successfully.")
            else:
                st.error(f"{sel_step} failed (exit {proc.returncode}).")
            output_area.code(output.strip() or "(no output)", language="text")
        except subprocess.TimeoutExpired:
            st.error("Step timed out after 600s.")

st.divider()

# ── Batch automated steps ─────────────────────────────────────────────────────

st.subheader("Batch Automated Steps")
st.caption("Run all pending S5 / S8 / S9 steps (no human checkpoint) for a selected model.")

batch_col1, batch_col2, batch_col3 = st.columns([2, 2, 2])
with batch_col1:
    batch_alias = st.selectbox("Model", aliases, key="batch_model")
with batch_col2:
    batch_phase = st.radio("Phase", ["Phase 1 (S5)", "Phase 2 (S8 + S9)", "Both"], key="batch_phase", horizontal=True)
with batch_col3:
    st.markdown("<br>", unsafe_allow_html=True)
    batch_btn = st.button("▶ Run batch", key="btn_batch")

if batch_btn and batch_alias:
    batch_model_cfg = next(m for m in NEURIPS_MODELS if m["alias"] == batch_alias)
    auto_steps = []
    if "1" in batch_phase or "Both" in batch_phase:
        auto_steps.append("S5")
    if "2" in batch_phase or "Both" in batch_phase:
        auto_steps += ["S8", "S9"]

    results = []
    for recipe in NEURIPS_RECIPES:
        for step in auto_steps:
            cmd = _build_cmd(recipe, batch_model_cfg["adapter"], batch_alias, batch_model_cfg["model_id"], step)
            if not cmd:
                results.append(f"⏭ {recipe}/{step} — skipped (missing prerequisites)")
                continue
            with st.spinner(f"{recipe} / {step}…"):
                try:
                    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                    if proc.returncode == 0:
                        results.append(f"✅ {recipe}/{step} — done")
                    else:
                        results.append(f"❌ {recipe}/{step} — failed: {proc.stderr[:100]}")
                except subprocess.TimeoutExpired:
                    results.append(f"⏰ {recipe}/{step} — timeout")

    st.cache_data.clear()
    for r in results:
        st.write(r)

st.divider()

# ── Artifact viewer ───────────────────────────────────────────────────────────

st.subheader("Artifact Viewer")
st.caption("Click to read any step output inline.")

view_col1, view_col2, view_col3 = st.columns(3)
with view_col1:
    view_recipe = st.selectbox("Recipe", NEURIPS_RECIPES, key="view_recipe")
with view_col2:
    view_alias = st.selectbox("Model", aliases, key="view_model")
with view_col3:
    view_step = st.selectbox("Step", list(STEPS.keys()), key="view_step")

view_model_cfg = next(m for m in NEURIPS_MODELS if m["alias"] == view_alias)
view_out = _out_dir(view_recipe, view_model_cfg["adapter"], view_model_cfg["alias"])
ext = STEP_EXTENSIONS.get(view_step, "")

if ext.endswith("/"):
    vibe_dir = view_out / ext.rstrip("/")
    if vibe_dir.exists():
        files = sorted(vibe_dir.rglob("*"), key=lambda f: f.name)
        files = [f for f in files if f.is_file()]
        if files:
            st.write(f"Files in `{vibe_dir.name}/`:")
            for f in files[:10]:
                with st.expander(f.name, expanded=False):
                    content = f.read_text(encoding="utf-8", errors="replace")
                    lang = "python" if f.suffix == ".py" else "markdown"
                    st.code(content, language=lang)
        else:
            st.info("Vibe output directory is empty.")
    else:
        st.info(f"Vibe directory not found for {view_recipe}/{view_alias}. Run S7 first.")
else:
    glob_pat = f"{view_step}-*{ext.split('*')[1] if '*' in ext else ext}"
    files = sorted(view_out.glob(glob_pat), reverse=True)
    if files:
        sel_file = files[0]
        st.caption(f"`{sel_file.name}`")
        content = sel_file.read_text(encoding="utf-8", errors="replace")
        if sel_file.suffix in (".spl", ".mmd"):
            st.code(content, language="sql")
        elif sel_file.suffix == ".py":
            st.code(content, language="python")
        else:
            st.markdown(content)
    else:
        st.info(f"No {view_step} output found for {view_recipe}/{view_alias}.")

# ── Human checkpoint notes ────────────────────────────────────────────────────

st.divider()
st.subheader("Human Checkpoint Notes")
st.caption("Append a note to notes.md for the selected recipe after reviewing a step.")

notes_col1, notes_col2 = st.columns([2, 4])
with notes_col1:
    note_recipe = st.selectbox("Recipe", NEURIPS_RECIPES, key="note_recipe")
    note_step   = st.selectbox("Step", [s for s, (_, _, chk) in STEPS.items() if chk], key="note_step")
with notes_col2:
    note_text = st.text_area(
        "Note (will be appended to notes.md)",
        placeholder="Describe issue found, fix applied, or approval rationale.",
        height=100,
        key="note_text",
    )
    if st.button("Append to notes.md", key="btn_append_note") and note_text.strip():
        notes_file = LAB_ROOT / NEURIPS_RECIPE_DIRS[note_recipe] / "notes.md"
        import time as _time
        entry = (
            f"\n\n## [{_time.strftime('%Y-%m-%d')}] {note_recipe} / {note_step} — UI checkpoint\n"
            f"{note_text.strip()}\n"
        )
        with open(notes_file, "a", encoding="utf-8") as fh:
            fh.write(entry)
        st.success(f"Appended to `{notes_file.name}`")
