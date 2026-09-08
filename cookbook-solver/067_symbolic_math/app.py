#!/usr/bin/env python3
"""
app.py — Streamlit UI for Recipe-67 experiment results.

Imports run_analysis.py CSV exports into a local SQLite database,
supports multiple idempotent imports (same file imported twice → all skipped),
and provides filtering, search, CRUD, and summary views.

Run from the SPL.py repo root:
  conda activate spl123
  streamlit run cookbook/67_symbolic_math/app.py
"""

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path("cookbook/67_symbolic_math/experiment_results.db")

# ── DB ────────────────────────────────────────────────────────────────────────

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
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
                notes          TEXT    DEFAULT '',
                imported_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source_file, mid, pid, solver, run)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS imports (
                source_file   TEXT PRIMARY KEY,
                rows_total    INTEGER,
                rows_inserted INTEGER,
                imported_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


# ── Import ────────────────────────────────────────────────────────────────────

def _coerce_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def import_csv(df: pd.DataFrame, source_file: str) -> tuple[int, int]:
    inserted = skipped = 0
    with get_conn() as conn:
        for _, row in df.iterrows():
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO results
                    (source_file, mid, label, pid, tier, problem,
                     solver, run, pass, status, output_preview,
                     llm_calls, latency_ms, steps, spl_log)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    source_file,
                    row.get("mid"), row.get("label"), row.get("pid"),
                    row.get("tier"), row.get("problem"),
                    row.get("solver"), int(row.get("run", 1)),
                    int(bool(row.get("pass"))), row.get("status"),
                    row.get("output_preview", ""),
                    _coerce_float(row.get("llm_calls")),
                    _coerce_float(row.get("latency_ms")),
                    _coerce_float(row.get("steps")),
                    row.get("spl_log", ""),
                ),
            )
            if cur.rowcount:
                inserted += 1
            else:
                skipped += 1
        conn.execute(
            "INSERT OR REPLACE INTO imports (source_file, rows_total, rows_inserted) VALUES (?,?,?)",
            (source_file, len(df), inserted),
        )
    return inserted, skipped


# ── Queries ───────────────────────────────────────────────────────────────────

@st.cache_data(ttl=5)
def load_all() -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql("SELECT * FROM results ORDER BY mid, pid, solver, run", conn)


@st.cache_data(ttl=5)
def load_imports() -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql("SELECT * FROM imports ORDER BY imported_at DESC", conn)


def apply_filters(df: pd.DataFrame, f: dict) -> pd.DataFrame:
    if f.get("models"):
        df = df[df["mid"].isin(f["models"])]
    if f.get("tiers"):
        df = df[df["tier"].isin(f["tiers"])]
    if f.get("solvers"):
        df = df[df["solver"].isin(f["solvers"])]
    if f.get("statuses"):
        df = df[df["status"].isin(f["statuses"])]
    if f.get("pass_filter") == "Pass":
        df = df[df["pass"] == 1]
    elif f.get("pass_filter") == "Fail":
        df = df[df["pass"] == 0]
    if f.get("search"):
        q = f["search"].lower()
        mask = (
            df["problem"].str.lower().str.contains(q, na=False)
            | df["output_preview"].str.lower().str.contains(q, na=False)
            | df["status"].str.lower().str.contains(q, na=False)
            | df["notes"].str.lower().str.contains(q, na=False)
        )
        df = df[mask]
    return df


def fmt_lat(v) -> str:
    return f"{v/1000:.1f}s" if pd.notna(v) else "?"


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(page_title="Recipe-67 Results", layout="wide")
    init_db()

    st.title("Recipe-67  ·  Symbolic Math Experiment Results")

    # ── Sidebar: import + filters ──────────────────────────────────────────────
    with st.sidebar:
        st.header("Import CSV")

        uploaded = st.file_uploader("Upload CSV file", type="csv", key="uploader")
        path_txt = st.text_input(
            "Or enter local path",
            placeholder="cookbook/67_symbolic_math/logs-spl/….csv",
        )

        if st.button("Import", type="primary", use_container_width=True):
            try:
                if uploaded:
                    df_csv = pd.read_csv(uploaded)
                    src = uploaded.name
                elif path_txt.strip():
                    df_csv = pd.read_csv(path_txt.strip())
                    src = Path(path_txt.strip()).name
                else:
                    st.warning("Provide a file or a path.")
                    df_csv = None
                    src = None

                if df_csv is not None:
                    ins, skip = import_csv(df_csv, src)
                    st.success(f"✓ {ins} inserted · {skip} skipped (already in DB)")
                    st.cache_data.clear()
            except Exception as exc:
                st.error(f"Import failed: {exc}")

        st.divider()
        st.header("Filters")

        all_df = load_all()
        if all_df.empty:
            model_opts, tier_opts, status_opts, model_labels = [], [], [], {}
        else:
            model_opts   = sorted(all_df["mid"].dropna().unique())
            tier_opts    = sorted(all_df["tier"].dropna().unique())
            status_opts  = sorted(all_df["status"].dropna().unique())
            model_labels = all_df.drop_duplicates("mid").set_index("mid")["label"].to_dict()

        sel_models   = st.multiselect(
            "Model", model_opts,
            format_func=lambda m: f"{m}  ({model_labels.get(m, '')})",
        )
        sel_tiers    = st.multiselect("Tier", tier_opts)
        sel_solvers  = st.multiselect("Solver arm", ["true", "false"])
        sel_statuses = st.multiselect("Status", status_opts)
        pass_filter  = st.radio("Pass / Fail", ["All", "Pass", "Fail"], horizontal=True)
        search       = st.text_input("Search", placeholder="problem · output · status · notes")

    filters = dict(
        models=sel_models, tiers=sel_tiers, solvers=sel_solvers,
        statuses=sel_statuses, pass_filter=pass_filter, search=search,
    )
    df = apply_filters(all_df, filters)

    # ── KPI strip ─────────────────────────────────────────────────────────────
    if not df.empty:
        total  = len(df)
        passed = int(df["pass"].sum())
        failed = total - passed
        rate   = f"{passed/total*100:.0f}%"
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Cells",   total)
        k2.metric("Pass",    passed)
        k3.metric("Fail",    failed)
        k4.metric("Pass rate", rate)

    # ── Tabs ───────────────────────────────────────────────────────────────────
    tab_res, tab_sum, tab_log, tab_edit, tab_batches = st.tabs(
        ["Results", "Summary", "Log Viewer", "Edit / Notes", "Imported Batches"]
    )

    # ── Results ────────────────────────────────────────────────────────────────
    with tab_res:
        if df.empty:
            st.info("No results — import a CSV or adjust filters.")
        else:
            display = df[[
                "id", "mid", "label", "pid", "tier", "solver", "run",
                "pass", "status", "output_preview",
                "llm_calls", "latency_ms", "steps", "notes",
            ]].copy()
            display["pass"]       = display["pass"].map({1: "✓", 0: "✗"})
            display["latency_ms"] = display["latency_ms"].apply(fmt_lat)
            display["llm_calls"]  = display["llm_calls"].apply(
                lambda v: f"{v:.0f}" if pd.notna(v) else "?"
            )
            display["steps"] = display["steps"].apply(
                lambda v: f"{v:.0f}" if pd.notna(v) else "?"
            )
            st.dataframe(display, use_container_width=True, hide_index=True)

    # ── Summary ────────────────────────────────────────────────────────────────
    with tab_sum:
        if df.empty:
            st.info("No data.")
        else:
            col_m, col_t = st.columns(2)

            with col_m:
                st.subheader("By model")
                mg = (
                    df.groupby(["mid", "label"])
                    .agg(cells=("pass", "count"), passed=("pass", "sum"),
                         avg_lat=("latency_ms", "mean"),
                         avg_calls=("llm_calls", "mean"))
                    .reset_index()
                )
                mg["pass_rate"] = (mg["passed"] / mg["cells"] * 100).map("{:.0f}%".format)
                mg["avg_lat"]   = mg["avg_lat"].apply(fmt_lat)
                mg["avg_calls"] = mg["avg_calls"].apply(
                    lambda v: f"{v:.1f}" if pd.notna(v) else "?"
                )
                st.dataframe(
                    mg[["mid", "label", "cells", "passed", "pass_rate", "avg_lat", "avg_calls"]],
                    hide_index=True, use_container_width=True,
                )

            with col_t:
                st.subheader("By problem tier")
                tg = (
                    df.groupby(["tier", "pid"])
                    .agg(cells=("pass", "count"), passed=("pass", "sum"),
                         avg_lat=("latency_ms", "mean"))
                    .reset_index()
                )
                tg["pass_rate"] = (tg["passed"] / tg["cells"] * 100).map("{:.0f}%".format)
                tg["avg_lat"]   = tg["avg_lat"].apply(fmt_lat)
                st.dataframe(
                    tg[["tier", "pid", "cells", "passed", "pass_rate", "avg_lat"]],
                    hide_index=True, use_container_width=True,
                )

            st.subheader("Pass-rate heatmap  ·  model × tier  (solver=true only)")
            true_df = df[df["solver"] == "true"]
            if true_df.empty:
                st.info("No solver=true rows in current filter.")
            else:
                hm = (
                    true_df.groupby(["label", "tier"])["pass"]
                    .mean()
                    .unstack(fill_value=float("nan"))
                    * 100
                )
                st.dataframe(
                    hm.style
                    .background_gradient(cmap="RdYlGn", vmin=0, vmax=100, axis=None)
                    .format("{:.0f}%", na_rep="—"),
                    use_container_width=True,
                )

            st.subheader("Status breakdown")
            status_counts = (
                df.groupby(["status", "solver"]).size()
                .unstack(fill_value=0)
                .reset_index()
            )
            st.dataframe(status_counts, hide_index=True, use_container_width=True)

    # ── Log Viewer ────────────────────────────────────────────────────────────
    with tab_log:
        st.subheader("Raw SPL log viewer")
        st.caption("Select a row by ID to read its spl3 execution trace.")

        if df.empty:
            st.info("No data.")
        else:
            # Quick-filter to suspicious cells so user doesn't have to hunt
            c_id, c_quick = st.columns([1, 3])
            with c_id:
                log_row_id = st.number_input("Row ID", min_value=1, step=1,
                                             value=int(df["id"].iloc[0]),
                                             key="log_row_id")
            with c_quick:
                st.markdown("**Quick filters — jump to suspicious rows:**")
                qf1, qf2, qf3 = st.columns(3)
                with qf1:
                    if st.button("solver=true passes (steps=0)"):
                        suspect = df[
                            (df["solver"] == "true") &
                            (df["pass"]   == 1) &
                            (df["steps"]  == 0)
                        ]
                        if not suspect.empty:
                            st.session_state["log_jump"] = int(suspect["id"].iloc[0])
                            st.info(f"{len(suspect)} rows — first ID {suspect['id'].iloc[0]}")
                        else:
                            st.success("None found — no suspicious passes.")
                with qf2:
                    if st.button("plan_error as unverified_success"):
                        suspect = df[
                            (df["status"]         == "unverified_success") &
                            (df["solver"]         == "true") &
                            (df["output_preview"].str.contains("PLAN.FAILURE", na=False))
                        ]
                        if not suspect.empty:
                            st.session_state["log_jump"] = int(suspect["id"].iloc[0])
                            st.info(f"{len(suspect)} rows — first ID {suspect['id'].iloc[0]}")
                        else:
                            st.success("None found.")
                with qf3:
                    if st.button("solver=true 100%-model sample"):
                        perfect = df[
                            (df["solver"] == "true") &
                            (df["pass"]   == 1) &
                            (df["tier"].isin(["T4", "T5"]))
                        ]
                        if not perfect.empty:
                            st.session_state["log_jump"] = int(perfect["id"].iloc[0])
                            st.info(f"{len(perfect)} T4/T5 passes — first ID {perfect['id'].iloc[0]}")

            # Apply jump if set by a quick-filter button
            if "log_jump" in st.session_state:
                log_row_id = st.session_state.pop("log_jump")

            with get_conn() as conn:
                raw = conn.execute(
                    "SELECT * FROM results WHERE id = ?", (int(log_row_id),)
                ).fetchone()

            if raw:
                row = dict(raw)
                st.markdown(
                    f"**{row['mid']} / {row['pid']} / solver={row['solver']} / run={row['run']}**  "
                    f"· status=`{row['status']}` · pass=`{bool(row['pass'])}` "
                    f"· steps=`{row['steps']}` · tier=`{row['tier']}`"
                )
                st.markdown(f"_Problem:_ {row['problem']}")
                if row.get("output_preview"):
                    st.markdown(
                        f"_Output preview:_ `{row['output_preview'].replace('_', ' ')[:120]}`"
                    )

                spl_log = (row.get("spl_log") or "").strip()
                if spl_log and spl_log != "?":
                    log_path = Path(spl_log)
                    if log_path.exists():
                        raw_text = log_path.read_text(errors="replace")
                        st.text_area(
                            f"spl3 trace  ·  {log_path.name}",
                            value=raw_text,
                            height=500,
                            key="log_content",
                        )
                        # Highlight interesting lines
                        flags = []
                        for line in raw_text.splitlines():
                            ls = line.strip()
                            if any(kw in ls for kw in (
                                "SOLVER FAILURE", "PLAN FAILURE", "NARRATION FAILURE",
                                "sympy_error", "Status:", "Output:", "steps=",
                            )):
                                flags.append(ls)
                        if flags:
                            with st.expander("Key lines (Status / errors / steps)"):
                                for f in flags:
                                    st.code(f)
                    else:
                        st.warning(f"Log file not found on disk: `{spl_log}`")
                else:
                    st.info("No spl_log path recorded for this cell (unknown/crashed run).")
            else:
                st.warning(f"No row with ID {log_row_id}.")

    # ── Edit / Notes ───────────────────────────────────────────────────────────
    with tab_edit:
        st.subheader("Edit a row")

        if df.empty:
            st.info("No data.")
        else:
            row_id = st.number_input("Row ID (see Results tab)", min_value=1, step=1, value=1)

            with get_conn() as conn:
                raw = conn.execute("SELECT * FROM results WHERE id = ?", (int(row_id),)).fetchone()

            if raw:
                row = dict(raw)
                st.markdown(
                    f"**{row['mid']} / {row['pid']} / solver={row['solver']} / run={row['run']}**  \n"
                    f"Status: `{row['status']}`  ·  Pass: `{bool(row['pass'])}`  \n"
                    f"Problem: _{row['problem']}_"
                )
                if row.get("output_preview"):
                    with st.expander("Output preview"):
                        st.write(row["output_preview"].replace("_", " "))

                STATUS_OPTS = [
                    "complete", "unverified_success", "solver_error",
                    "plan_error", "silent_failure", "llm_error", "unknown",
                ]
                cur_status = row["status"] if row["status"] in STATUS_OPTS else "unknown"
                new_status = st.selectbox("Status", STATUS_OPTS, index=STATUS_OPTS.index(cur_status))
                new_pass   = st.checkbox("Pass", value=bool(row["pass"]))
                new_notes  = st.text_area("Notes", value=row["notes"] or "", height=100)

                c_save, c_del, _ = st.columns([1, 1, 4])
                with c_save:
                    if st.button("Save", type="primary"):
                        with get_conn() as conn:
                            conn.execute(
                                "UPDATE results SET status=?, pass=?, notes=? WHERE id=?",
                                (new_status, int(new_pass), new_notes, int(row_id)),
                            )
                        st.success("Saved.")
                        st.cache_data.clear()
                with c_del:
                    if st.button("Delete row"):
                        with get_conn() as conn:
                            conn.execute("DELETE FROM results WHERE id = ?", (int(row_id),))
                        st.success(f"Row {row_id} deleted.")
                        st.cache_data.clear()
            else:
                st.warning(f"No row with ID {row_id}.")

    # ── Imported Batches ───────────────────────────────────────────────────────
    with tab_batches:
        st.subheader("Imported batches")
        imp_df = load_imports()

        if imp_df.empty:
            st.info("No imports yet.")
        else:
            st.dataframe(imp_df, hide_index=True, use_container_width=True)

            st.divider()
            st.subheader("Delete a batch")
            st.caption("Removes all rows from that CSV import — does not affect other batches.")
            to_delete = st.selectbox("Batch to delete", imp_df["source_file"].tolist())
            if st.button("Delete batch", type="secondary"):
                with get_conn() as conn:
                    conn.execute("DELETE FROM results WHERE source_file = ?", (to_delete,))
                    conn.execute("DELETE FROM imports  WHERE source_file = ?", (to_delete,))
                st.success(f"Deleted: {to_delete}")
                st.cache_data.clear()
                st.rerun()


if __name__ == "__main__":
    main()
