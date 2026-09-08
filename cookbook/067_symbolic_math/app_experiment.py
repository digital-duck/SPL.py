#!/usr/bin/env python3
"""
app_experiment.py — Streamlit UI for Recipe-67 experiment results.

Reads from the SQLite database written by run_experiment.py.

  conda activate spl123
  streamlit run cookbook/67_symbolic_math/app_experiment.py
"""

import json
import sqlite3
from pathlib import Path
from typing import Any, cast

import pandas as pd
import streamlit as st

_HERE   = Path(__file__).parent
DB_PATH = _HERE / "experiment_results.db"

# ── DB ─────────────────────────────────────────────────────────────────────────

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                source_file    TEXT    NOT NULL,
                mid            TEXT,
                label          TEXT,
                pid            TEXT,
                tier           TEXT,
                problem        TEXT,
                solver         TEXT,
                run            INTEGER,
                pass           INTEGER,
                status         TEXT,
                output_preview TEXT,
                llm_calls      REAL,
                latency_ms     REAL,
                steps          REAL,
                spl_log        TEXT,
                decomposition  TEXT,
                output         TEXT,
                notes          TEXT DEFAULT '',
                imported_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source_file, mid, pid, solver, run)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                source_file  TEXT PRIMARY KEY,
                rows_total   INTEGER,
                rows_written INTEGER DEFAULT 0,
                log_path     TEXT,
                started_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Migrate existing DBs
        for stmt in [
            "ALTER TABLE results ADD COLUMN decomposition TEXT",
            "ALTER TABLE results ADD COLUMN output TEXT",
        ]:
            try:
                conn.execute(stmt)
            except sqlite3.OperationalError:
                pass


# ── Data loading ───────────────────────────────────────────────────────────────

@st.cache_data(ttl=5)
def load_all() -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql(
            "SELECT * FROM results ORDER BY source_file, mid, pid, solver, run", conn
        )


@st.cache_data(ttl=5)
def load_runs() -> pd.DataFrame:
    with get_conn() as conn:
        # Derive run summary directly from results when runs table is empty
        try:
            runs = pd.read_sql("SELECT * FROM runs ORDER BY started_at DESC", conn)
        except Exception:
            runs = pd.DataFrame()
        if runs.empty:
            # Fall back: aggregate from results
            runs = pd.read_sql("""
                SELECT source_file,
                       COUNT(*) AS rows_written,
                       NULL     AS rows_total,
                       NULL     AS log_path,
                       MIN(imported_at) AS started_at
                FROM results
                GROUP BY source_file
                ORDER BY started_at DESC
            """, conn)
        return runs


def apply_filters(df: pd.DataFrame, f: dict) -> pd.DataFrame:
    r: Any = df
    if f.get("sources"):
        r = r[r["source_file"].isin(f["sources"])]
    if f.get("models"):
        r = r[r["mid"].isin(f["models"])]
    if f.get("tiers"):
        r = r[r["tier"].isin(f["tiers"])]
    if f.get("solvers"):
        r = r[r["solver"].isin(f["solvers"])]
    if f.get("statuses"):
        r = r[r["status"].isin(f["statuses"])]
    if f.get("pass_filter") == "Pass":
        r = r[r["pass"] == 1]
    elif f.get("pass_filter") == "Fail":
        r = r[r["pass"] == 0]
    if f.get("search"):
        q = f["search"].lower()
        mask = (
            r["problem"].str.lower().str.contains(q, na=False)
            | r["output_preview"].str.lower().str.contains(q, na=False)
            | r["status"].str.lower().str.contains(q, na=False)
            | r["notes"].str.lower().str.contains(q, na=False)
            | r["mid"].str.lower().str.contains(q, na=False)
            | r["pid"].str.lower().str.contains(q, na=False)
        )
        r = r[mask]
    return cast(pd.DataFrame, r)


def fmt_lat(v) -> str:
    return f"{v/1000:.1f}s" if pd.notna(v) and v is not None else "?"


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(page_title="Recipe-67 Experiments", layout="wide")
    init_db()

    st.title("Recipe-67  ·  Symbolic Math Experiments")

    all_df  = load_all()
    runs_df = load_runs()

    # ── Sidebar ────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.header("Filters")

        src_opts = runs_df["source_file"].tolist() if not runs_df.empty else []
        sel_sources = st.multiselect("Experiment run", src_opts)

        if all_df.empty:
            model_opts   = tier_opts = status_opts = []
            model_labels: dict = {}
        else:
            model_opts   = sorted(all_df["mid"].dropna().unique())
            tier_opts    = sorted(all_df["tier"].dropna().unique())
            status_opts  = sorted(all_df["status"].dropna().unique())
            model_labels = (all_df.drop_duplicates("mid")
                            .set_index("mid")["label"].to_dict())

        sel_models = st.multiselect(
            "Model", model_opts,
            format_func=lambda m: f"{m}  ({model_labels.get(m, '')})",
        )
        sel_tiers    = st.multiselect("Tier", tier_opts)
        sel_solvers  = st.multiselect("Solver arm", ["true", "false"])
        sel_statuses = st.multiselect("Status", status_opts)
        pass_filter  = st.radio("Pass / Fail", ["All", "Pass", "Fail"], horizontal=True)
        search       = st.text_input("Search", placeholder="model · problem · status · notes")

        if st.button("Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    filters = dict(
        sources=sel_sources, models=sel_models, tiers=sel_tiers,
        solvers=sel_solvers, statuses=sel_statuses,
        pass_filter=pass_filter, search=search,
    )
    df = apply_filters(all_df, filters)

    # ── KPI strip ──────────────────────────────────────────────────────────────
    if not df.empty:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Cells",     len(df))
        k2.metric("Pass",      int(df["pass"].sum()))
        k3.metric("Fail",      int((~df["pass"].astype(bool)).sum()))
        k4.metric("Pass rate", f"{df['pass'].mean()*100:.0f}%")

    # ── Tabs ───────────────────────────────────────────────────────────────────
    tab_runs, tab_res, tab_log, tab_analysis, tab_edit = st.tabs([
        "Runs", "Results", "Log Viewer", "Analysis", "Edit / Notes",
    ])

    # ── Runs ───────────────────────────────────────────────────────────────────
    with tab_runs:
        st.subheader("Experiment runs")
        if runs_df.empty:
            st.info("No runs yet — run run_experiment.py to populate the database.")
        else:
            exp_rows = []
            for _, r in runs_df.iterrows():
                sf   = r["source_file"]
                sub  = cast(pd.DataFrame, all_df[all_df["source_file"] == sf]) if not all_df.empty else pd.DataFrame()
                done = len(sub)
                passed = int(sub["pass"].sum()) if done else 0
                exp_rows.append({
                    "source":     sf,
                    "planned":    r.get("rows_total") or "—",
                    "recorded":   done,
                    "passed":     passed,
                    "pass_rate":  f"{passed/done*100:.0f}%" if done else "—",
                    "log_path":   r.get("log_path") or "—",
                    "started_at": r.get("started_at", ""),
                })
            runs_display = pd.DataFrame(exp_rows)
            st.caption(f"{len(runs_display)} runs  · click a row to select for deletion")
            runs_sel = st.dataframe(  # pyright: ignore[reportCallIssue]
                runs_display, hide_index=True, use_container_width=True,
                on_select="rerun", selection_mode="single-row",
            )
            selected_run_rows = (runs_sel.selection.rows  # type: ignore[union-attr]
                                 if runs_sel and hasattr(runs_sel, "selection") else [])
            if selected_run_rows:
                run_row_idx = selected_run_rows[0]
                to_del = str(cast(pd.Series, runs_display["source"]).iloc[run_row_idx])
                st.divider()
                st.caption(f"Selected: **{to_del}**  — removes all result rows for this run.")
                if st.button("Delete run", type="secondary"):
                    with get_conn() as conn:
                        conn.execute("DELETE FROM results WHERE source_file=?", (to_del,))
                        conn.execute("DELETE FROM runs    WHERE source_file=?", (to_del,))
                    st.success(f"Deleted: {to_del}")
                    st.cache_data.clear()
                    st.rerun()

    # ── Results ────────────────────────────────────────────────────────────────
    with tab_res:
        if df.empty:
            st.info("No results — run an experiment or adjust filters.")
        else:
            def _decomp_summary(raw) -> str:
                if not raw:
                    return ""
                try:
                    d = json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    return "?"
                lines = []
                for s in d.get("steps", []):
                    mark = "✓" if s.get("ok") else "✗"
                    lines.append(f"[{mark}{s['n']}] {s['line']}")
                return "\n".join(lines)

            display: pd.DataFrame = cast(pd.DataFrame, df[[
                "id", "source_file", "mid", "label", "pid", "tier",
                "solver", "run", "pass", "status",
                "llm_calls", "latency_ms", "steps", "decomposition", "output_preview", "notes",
            ]].copy())
            cast(pd.Series, display["pass"]).replace({1: "✓", 0: "✗"}, inplace=True)
            display["latency_ms"]    = cast(pd.Series, display["latency_ms"]).apply(fmt_lat)
            display["llm_calls"]     = cast(pd.Series, display["llm_calls"]).apply(
                lambda v: f"{v:.0f}" if pd.notna(v) else "?")
            display["steps"]         = cast(pd.Series, display["steps"]).apply(
                lambda v: f"{v:.0f}" if pd.notna(v) else "?")
            display["decomposition"] = cast(pd.Series, display["decomposition"]).apply(
                _decomp_summary)
            st.caption(f"{len(df)} rows  · click a row to see full output below")
            sel = st.dataframe(  # pyright: ignore[reportCallIssue]
                display, use_container_width=True, hide_index=True,
                on_select="rerun", selection_mode="single-row",
                column_config={"decomposition": st.column_config.TextColumn(
                    "decomposition", width="large",
                )},
            )
            selected_rows = (sel.selection.rows  # type: ignore[union-attr]
                             if sel and hasattr(sel, "selection") else [])
            if selected_rows:
                row_idx = selected_rows[0]
                row_id  = int(cast(pd.Series, display["id"]).iloc[row_idx])
                with get_conn() as conn:
                    full = conn.execute(
                        "SELECT * FROM results WHERE id = ?", (row_id,)
                    ).fetchone()
                if full:
                    full_row = dict(full)
                    st.divider()
                    st.markdown(
                        f"**{full_row['mid']} / {full_row['pid']}"
                        f" / solver={full_row['solver']} / run={full_row['run']}**  "
                        f"· status=`{full_row['status']}` · pass=`{bool(full_row['pass'])}`"
                    )

                    # ① Original problem
                    st.markdown("**① Problem**")
                    st.text(full_row["problem"])

                    # ② Decomposition (solver=true only)
                    st.markdown("**② Decomposition for SymPy**")
                    raw_decomp = (full_row.get("decomposition") or "").strip()
                    if raw_decomp:
                        try:
                            d = json.loads(raw_decomp)
                            planned   = d.get("planned", "?")
                            failed_at = d.get("failed_at")
                            icon = "🔴" if failed_at else "🟢"
                            st.markdown(
                                f"{icon} planned **{planned}** step(s)"
                                + (f" — failed at step **{failed_at}**" if failed_at else "")
                            )
                            for si in d.get("steps", []):
                                mark = "✓" if si.get("ok") else "✗"
                                st.code(f"[{mark}] step {si['n']}: {si['line']}")
                            if d.get("error"):
                                st.error(d["error"][:300])
                        except (json.JSONDecodeError, KeyError):
                            st.code(raw_decomp)
                    elif full_row.get("solver") == "true":
                        st.caption("No decomposition recorded.")
                    else:
                        st.caption("solver=false — no SymPy decomposition.")

                    # ③ LLM output
                    st.markdown("**③ LLM Output**")
                    full_output = (full_row.get("output") or "").strip()
                    if not full_output:
                        full_output = (full_row.get("output_preview") or "").replace("_", " ")
                    st.write(full_output)

    # ── Log Viewer ─────────────────────────────────────────────────────────────
    with tab_log:
        st.subheader("Individual SPL run log viewer")
        if df.empty:
            st.info("No data.")
        else:
            c_id, c_quick = st.columns([1, 3])
            with c_id:
                log_row_id = st.number_input(
                    "Row ID", min_value=1, step=1,
                    value=int(cast(pd.Series, df["id"]).iloc[0]), key="log_row_id",
                )
            with c_quick:
                st.markdown("**Quick filters:**")
                qf1, qf2, qf3 = st.columns(3)
                with qf1:
                    if st.button("solver=true ghost passes?"):
                        s = cast(pd.DataFrame, df[
                            (df["solver"] == "true") & (df["pass"] == 1) &
                            (df["steps"].fillna(0) > 0) & (~df["status"].isin(["complete"]))
                        ])
                        if not s.empty:
                            st.session_state["log_jump"] = int(cast(pd.Series, s["id"]).iloc[0])
                            st.info(f"{len(s)} rows")
                        else:
                            st.success("None found.")
                with qf2:
                    if st.button("SOLVER/PLAN FAILURE in output"):
                        s = cast(pd.DataFrame, df[
                            df["output_preview"].str.contains(
                                r"\[SOLVER FAILURE\]|\[PLAN FAILURE\]", na=False)
                        ])
                        if not s.empty:
                            st.session_state["log_jump"] = int(cast(pd.Series, s["id"]).iloc[0])
                            st.info(f"{len(s)} rows")
                        else:
                            st.success("None found.")
                with qf3:
                    if st.button("decomposition mismatch?"):
                        # Rows where decomposition failed but status=complete (status reclassification missed it)
                        s = cast(pd.DataFrame, df[
                            (df["decomposition"].str.contains('"failed_at"', na=False)) &
                            (df["status"] == "complete")
                        ])
                        if not s.empty:
                            st.session_state["log_jump"] = int(cast(pd.Series, s["id"]).iloc[0])
                            st.info(f"{len(s)} rows")
                        else:
                            st.success("None found.")

            if "log_jump" in st.session_state:
                log_row_id = st.session_state.pop("log_jump")

            with get_conn() as conn:
                raw = conn.execute(
                    "SELECT * FROM results WHERE id = ?", (int(log_row_id),)
                ).fetchone()

            if raw:
                row = dict(raw)
                st.markdown(
                    f"**{row['mid']} / {row['pid']} / solver={row['solver']}"
                    f" / run={row['run']}**  "
                    f"· status=`{row['status']}` · pass=`{bool(row['pass'])}` "
                    f"· steps=`{row['steps']}` · tier=`{row['tier']}`  \n"
                    f"_Problem:_ {row['problem']}  \n"
                    f"_Source:_ `{row['source_file']}`"
                )
                if row.get("output_preview"):
                    st.markdown(f"_Output:_ `{row['output_preview'][:160]}`")

                # Decomposition chain (solver=true only)
                raw_decomp = (row.get("decomposition") or "").strip()
                if raw_decomp:
                    try:
                        d          = json.loads(raw_decomp)
                        planned    = d.get("planned", "?")
                        failed_at  = d.get("failed_at")
                        error_msg  = (d.get("error") or "")
                        steps_data = d.get("steps", [])
                        icon = "🔴" if failed_at else "🟢"
                        st.markdown(
                            f"{icon} **Decomposition** — planned {planned} step(s)"
                            + (f", **failed at step {failed_at}**" if failed_at else "")
                        )
                        for si in steps_data:
                            mark = "✓" if si.get("ok") else "✗"
                            st.code(f"[{mark}] step {si['n']}: {si['line']}")
                        if error_msg:
                            st.error(f"SymPy error: {error_msg[:300]}")
                    except (json.JSONDecodeError, KeyError):
                        st.code(raw_decomp)
                elif row.get("solver") == "true":
                    st.info("No decomposition recorded (run predates this feature).")

                spl_log = (row.get("spl_log") or "").strip()
                if spl_log and spl_log != "?":
                    log_path = Path(spl_log)
                    if log_path.exists():
                        raw_text = log_path.read_text(errors="replace")
                        st.text_area(
                            f"spl3 trace · {log_path.name}",
                            value=raw_text, height=500, key="log_content",
                        )
                        flags = [
                            ln.strip() for ln in raw_text.splitlines()
                            if any(kw in ln for kw in (
                                "SOLVER FAILURE", "PLAN FAILURE", "NARRATION FAILURE",
                                "sympy_error", "Status:", "Output:", "RETURN:",
                                "decomposed into", "[arm=solver][step",
                            ))
                        ]
                        if flags:
                            with st.expander("Key lines"):
                                for fl in flags:
                                    st.code(fl)
                    else:
                        st.warning(f"Log file not found: `{spl_log}`")
                else:
                    st.info("No spl_log path for this cell.")
            else:
                st.warning(f"No row with ID {log_row_id}.")

    # ── Analysis ───────────────────────────────────────────────────────────────
    with tab_analysis:
        if df.empty:
            st.info("No data.")
        else:
            col_m, col_t = st.columns(2)

            with col_m:
                st.subheader("By model")
                mg = (
                    df.groupby(["mid", "label"])
                    .agg(cells=("pass","count"), passed=("pass","sum"),
                         avg_lat=("latency_ms","mean"), avg_calls=("llm_calls","mean"))
                    .reset_index()
                )
                mg["pass_rate"] = (mg["passed"]/mg["cells"]*100).map("{:.0f}%".format)
                mg["avg_lat"]   = mg["avg_lat"].apply(fmt_lat)
                mg["avg_calls"] = mg["avg_calls"].apply(
                    lambda v: f"{v:.1f}" if pd.notna(v) else "?")
                st.dataframe(
                    mg[["mid","label","cells","passed","pass_rate","avg_lat","avg_calls"]],
                    hide_index=True, use_container_width=True,
                )

            with col_t:
                st.subheader("By tier")
                tg = (
                    df.groupby(["tier","pid"])
                    .agg(cells=("pass","count"), passed=("pass","sum"),
                         avg_lat=("latency_ms","mean"))
                    .reset_index()
                )
                tg["pass_rate"] = (tg["passed"]/tg["cells"]*100).map("{:.0f}%".format)
                tg["avg_lat"]   = tg["avg_lat"].apply(fmt_lat)
                st.dataframe(
                    tg[["tier","pid","cells","passed","pass_rate","avg_lat"]],
                    hide_index=True, use_container_width=True,
                )

            st.subheader("Pass-rate heatmap · model × tier (solver=true)")
            true_df: Any = df[df["solver"] == "true"]
            if cast(pd.DataFrame, true_df).empty:
                st.info("No solver=true rows in current filter.")
            else:
                hm = (
                    true_df.groupby(["label","tier"])["pass"]
                    .mean().unstack(fill_value=float("nan")) * 100
                )

                def _rg_color(val):
                    if pd.isna(val):
                        return ""
                    v = float(val) / 100.0
                    r, g = int(255 * (1 - v)), int(200 * v)
                    return f"background-color: rgb({r},{g},60); color: white"

                st.dataframe(
                    hm.style
                    .map(_rg_color)
                    .format("{:.0f}%", na_rep="—"),
                    use_container_width=True,
                )

            st.subheader("Status breakdown · solver arm")
            sc = (
                df.groupby(["status","solver"]).size()
                .unstack(fill_value=0).reset_index()
            )
            st.dataframe(sc, hide_index=True, use_container_width=True)

            st.subheader("Decomposition failures · solver=true")
            solver_true: Any = df[df["solver"] == "true"]
            decomp_rows = []
            for _, r in cast(pd.DataFrame, solver_true).iterrows():
                raw = (r.get("decomposition") or "")
                if not raw:
                    continue
                try:
                    d = json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    continue
                decomp_rows.append({
                    "id":        r["id"],
                    "mid":       r["mid"],
                    "pid":       r["pid"],
                    "tier":      r["tier"],
                    "planned":   d.get("planned", "?"),
                    "failed_at": d.get("failed_at"),
                    "status":    r["status"],
                    "pass":      bool(r["pass"]),
                    "error":     (d.get("error") or "")[:80],
                })
            if decomp_rows:
                ddf = pd.DataFrame(decomp_rows)
                st.dataframe(ddf, hide_index=True, use_container_width=True)
            else:
                st.info("No decomposition data yet.")

    # ── Edit / Notes ───────────────────────────────────────────────────────────
    with tab_edit:
        st.subheader("Edit a row")
        if df.empty:
            st.info("No data.")
        else:
            row_id = st.number_input("Row ID", min_value=1, step=1, value=1)
            with get_conn() as conn:
                raw = conn.execute(
                    "SELECT * FROM results WHERE id = ?", (int(row_id),)
                ).fetchone()
            if raw:
                row = dict(raw)
                st.markdown(
                    f"**{row['mid']} / {row['pid']} / solver={row['solver']}"
                    f" / run={row['run']}**  status=`{row['status']}`  \n"
                    f"_Problem:_ {row['problem']}"
                )
                STATUS_OPTS = ["complete","unverified_success","solver_error",
                               "plan_error","silent_failure","llm_error","unknown"]
                cur_status  = row["status"] if row["status"] in STATUS_OPTS else "unknown"
                new_status  = st.selectbox("Status", STATUS_OPTS,
                                           index=STATUS_OPTS.index(cur_status))
                new_pass    = st.checkbox("Pass", value=bool(row["pass"]))
                new_notes   = st.text_area("Notes", value=row["notes"] or "", height=80)
                c1, c2, _   = st.columns([1, 1, 4])
                with c1:
                    if st.button("Save", type="primary"):
                        with get_conn() as conn:
                            conn.execute(
                                "UPDATE results SET status=?, pass=?, notes=? WHERE id=?",
                                (new_status, int(new_pass), new_notes, int(row_id)),
                            )
                        st.success("Saved.")
                        st.cache_data.clear()
                with c2:
                    if st.button("Delete row"):
                        with get_conn() as conn:
                            conn.execute("DELETE FROM results WHERE id=?", (int(row_id),))
                        st.success(f"Row {row_id} deleted.")
                        st.cache_data.clear()
            else:
                st.warning(f"No row with ID {row_id}.")


if __name__ == "__main__":
    main()
