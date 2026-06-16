#!/usr/bin/env python3
"""
analyze_experiment.py — Generate paper-ready markdown tables from the Recipe-77 DB.

Works for any run count (-r 1, -r 3, -r 5): aggregates mean pass rate per
(model × problem × solver) cell across repetitions, then builds all tables.

Usage:
  python cookbook/77_neurosymbolic/analyze_experiment.py
  python cookbook/77_neurosymbolic/analyze_experiment.py --db path/to/db.sqlite
  python cookbook/77_neurosymbolic/analyze_experiment.py --source exp-20260615-073849
  python cookbook/77_neurosymbolic/analyze_experiment.py --out results.md --source exp-20260615-073849
  python cookbook/77_neurosymbolic/analyze_experiment.py --list-sources
"""

import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB_DEFAULT = Path("cookbook/77_neurosymbolic/experiment_results.db")

TIER_ORDER  = ["T0", "T1", "T2", "T3", "T4", "T5", "T6", "P1", "P2"]
BACKEND_MAP = {"sympy": "SymPy", "sage": "Sage", "lean": "Lean 4"}

# ── DB helpers ────────────────────────────────────────────────────────────────

def get_conn(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def list_sources(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT source_file, rows_total, rows_inserted, log_path, imported_at "
        "FROM imports ORDER BY imported_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def load_rows(conn: sqlite3.Connection, source: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM results WHERE source_file = ? ORDER BY mid, pid, solver, run",
        (source,),
    ).fetchall()
    return [dict(r) for r in rows]


# ── Aggregation (handles -r 1 / -r 3 / -r 5) ─────────────────────────────────

def aggregate(rows: list[dict]) -> dict:
    """
    Returns nested structure:
      cells[(mid, pid, solver)] = {label, tier, backend, problem, mean_pass,
                                   dominant_status, avg_lat_ms, avg_llm_calls,
                                   avg_steps, n_runs}
    """
    from collections import defaultdict

    buckets: dict = defaultdict(list)
    for r in rows:
        key = (r["mid"], r["pid"], r["solver"])
        buckets[key].append(r)

    cells = {}
    for key, rlist in buckets.items():
        r0 = rlist[0]
        n_runs_k = len(rlist)
        mean_pass = sum(r["pass"] for r in rlist) / n_runs_k
        # dominant status = most common non-complete status if any failure, else complete
        from collections import Counter
        status_counts = Counter(r["status"] for r in rlist)
        dominant = status_counts.most_common(1)[0][0]
        lats   = [r["latency_ms"] for r in rlist if r["latency_ms"] is not None]
        calls  = [r["llm_calls"]  for r in rlist if r["llm_calls"]  is not None]
        steps  = [r["steps"]      for r in rlist if r["steps"]      is not None]
        cells[key] = {
            "mid": key[0], "pid": key[1], "solver": key[2],
            "label":    r0["label"],
            "tier":     r0["tier"],
            "backend":  r0.get("backend") or "",
            "problem":  r0["problem"],
            "mean_pass": mean_pass,
            "dominant_status": dominant,
            "avg_lat_ms":    sum(lats)  / len(lats)  if lats  else None,
            "avg_llm_calls": sum(calls) / len(calls) if calls else None,
            "avg_steps":     sum(steps) / len(steps) if steps else None,
            "n_runs": n_runs_k,
        }

        # per-status breakdown
        for s, cnt in status_counts.items():
            cells[key][f"n_{s}"] = cnt

    return cells


# ── Formatting helpers ────────────────────────────────────────────────────────

def pct(v: float, *, denom: int = 1) -> str:
    return f"{v / denom * 100:.0f}%"


def lat_s(ms: float | None) -> str:
    if ms is None:
        return "?"
    return f"{ms / 1000:.1f}s"


def _sorted_models(cells: dict) -> list[tuple]:
    """Model tuples sorted by solver pass rate desc."""
    from collections import defaultdict
    solver_pass: dict = defaultdict(list)
    minfo: dict = {}
    for c in cells.values():
        if c["solver"] == "true":
            solver_pass[c["mid"]].append(c["mean_pass"])
        minfo[c["mid"]] = c["label"]
    return sorted(
        [(mid, minfo[mid]) for mid in solver_pass],
        key=lambda t: -sum(solver_pass[t[0]]) / max(len(solver_pass[t[0]]), 1),
    )


def _tiers_present(cells: dict) -> list[str]:
    found = {c["tier"] for c in cells.values()}
    return [t for t in TIER_ORDER if t in found]


# ── Table builders ────────────────────────────────────────────────────────────

def table_pass_rates(cells: dict, models: list[tuple], n_runs: int) -> str:
    """Overall pass rate by model and arm, sorted by solver desc."""
    from collections import defaultdict
    solver_pass: dict  = defaultdict(list)
    llm_pass: dict     = defaultdict(list)
    for c in cells.values():
        if c["solver"] == "true":
            solver_pass[c["mid"]].append(c["mean_pass"])
        else:
            llm_pass[c["mid"]].append(c["mean_pass"])

    lines = [
        "**Pass rates by model and arm**"
        + (f" (mean over {n_runs} runs/cell)" if n_runs > 1 else "") + ":",
        "",
        "| Model | LLM-only | Solver | Δ |",
        "|---|---|---|---|",
    ]
    for mid, label in models:
        s = sum(solver_pass[mid]) / len(solver_pass[mid]) * 100 if solver_pass[mid] else 0
        l = sum(llm_pass[mid])   / len(llm_pass[mid])   * 100 if llm_pass[mid]   else 0
        delta = s - l
        sign  = "+" if delta > 0 else ""
        lines.append(f"| {label} | {l:.0f}% | {s:.0f}% | {sign}{delta:.0f} |")
    return "\n".join(lines)


def table_latency(cells: dict, models: list[tuple]) -> str:
    from collections import defaultdict
    lat_s_arm: dict = defaultdict(lambda: defaultdict(list))
    for c in cells.values():
        if c["avg_lat_ms"] is not None:
            lat_s_arm[c["mid"]][c["solver"]].append(c["avg_lat_ms"])

    lines = [
        "**Average latency by model and arm:**",
        "",
        "| Model | LLM-only | Solver | Δ |",
        "|---|---|---|---|",
    ]
    for mid, label in models:
        t_lats = lat_s_arm[mid]["true"]
        f_lats = lat_s_arm[mid]["false"]
        t = sum(t_lats) / len(t_lats) if t_lats else None
        f = sum(f_lats) / len(f_lats) if f_lats else None
        if t is not None and f is not None and f > 0:
            delta_pct = (t - f) / f * 100
            sign = "+" if delta_pct > 0 else ""
            delta_str = f"{sign}{delta_pct:.0f}%"
        else:
            delta_str = "?"
        lines.append(f"| {label} | {lat_s(f)} | {lat_s(t)} | {delta_str} |")
    return "\n".join(lines)


def table_status_breakdown(cells: dict, models: list[tuple]) -> str:
    all_statuses = set()
    for c in cells.values():
        for k in c:
            if k.startswith("n_"):
                all_statuses.add(k[2:])
    # Only show solver arm
    STATUS_COL_ORDER = ["complete", "solver_error", "plan_error",
                        "plan_format_error", "plan_sanity_error",
                        "silent_failure", "llm_error", "unknown"]
    cols = [s for s in STATUS_COL_ORDER if s in all_statuses]
    remaining = sorted(all_statuses - set(cols))
    cols += remaining

    from collections import defaultdict
    totals: dict = defaultdict(lambda: defaultdict(float))
    for c in cells.values():
        if c["solver"] == "true":
            for s in cols:
                totals[c["mid"]][s] += c.get(f"n_{s}", 0)

    header_cols = " | ".join(f"`{s}`" for s in cols)
    sep_cols    = " | ".join("---" for _ in cols)
    lines = [
        "**Failure mode breakdown (solver arm, total across all runs):**",
        "",
        f"| Model | {header_cols} |",
        f"|---| {sep_cols} |",
    ]
    for mid, label in models:
        vals = " | ".join(f"{int(totals[mid].get(s, 0))}" for s in cols)
        lines.append(f"| {label} | {vals} |")
    return "\n".join(lines)


def table_per_tier_solver(cells: dict, models: list[tuple], tiers: list[str]) -> str:
    from collections import defaultdict
    # tier_model_pass[mid][tier] = [mean_pass, ...]
    data: dict = defaultdict(lambda: defaultdict(list))
    for c in cells.values():
        if c["solver"] == "true":
            data[c["mid"]][c["tier"]].append(c["mean_pass"])

    tier_totals: dict = defaultdict(list)
    for mid in data:
        for t in tiers:
            if data[mid][t]:
                tier_totals[t].extend(data[mid][t])

    tier_header = " | ".join(tiers)
    tier_sep    = " | ".join("---" for _ in tiers)
    lines = [
        "**Solver arm pass rate by model and tier (%):**",
        "",
        f"| Model | {tier_header} | Overall |",
        f"|---| {tier_sep} |---|",
    ]
    for mid, label in models:
        tier_vals = []
        all_passes = []
        for t in tiers:
            ps = data[mid][t]
            if ps:
                v = sum(ps) / len(ps) * 100
                tier_vals.append(f"{v:.0f}")
                all_passes.extend(ps)
            else:
                tier_vals.append("—")
        overall = f"{sum(all_passes)/len(all_passes)*100:.0f}" if all_passes else "—"
        lines.append(f"| {label} | {' | '.join(tier_vals)} | {overall} |")

    # Tier averages
    avg_vals = []
    for t in tiers:
        ps = tier_totals[t]
        avg_vals.append(f"**{sum(ps)/len(ps)*100:.0f}**" if ps else "—")
    lines.append(f"| **Tier avg** | {' | '.join(avg_vals)} | — |")
    return "\n".join(lines)


def table_per_tier_llm(cells: dict, models: list[tuple], tiers: list[str]) -> str:
    from collections import defaultdict
    data: dict = defaultdict(lambda: defaultdict(list))
    for c in cells.values():
        if c["solver"] == "false":
            data[c["mid"]][c["tier"]].append(c["mean_pass"])

    tier_header = " | ".join(tiers)
    tier_sep    = " | ".join("---" for _ in tiers)
    lines = [
        "**LLM-only arm pass rate by model and tier (%) — pass = non-empty response:**",
        "",
        f"| Model | {tier_header} | Overall |",
        f"|---| {tier_sep} |---|",
    ]
    for mid, label in models:
        tier_vals = []
        all_passes = []
        for t in tiers:
            ps = data[mid][t]
            if ps:
                v = sum(ps) / len(ps) * 100
                tier_vals.append(f"{v:.0f}")
                all_passes.extend(ps)
            else:
                tier_vals.append("—")
        overall = f"{sum(all_passes)/len(all_passes)*100:.0f}" if all_passes else "—"
        lines.append(f"| {label} | {' | '.join(tier_vals)} | {overall} |")
    return "\n".join(lines)


def table_backend_comparison(cells: dict) -> str:
    from collections import defaultdict
    data: dict = defaultdict(lambda: {"solver": [], "llm": []})
    for c in cells.values():
        b = c.get("backend") or "unknown"
        if c["solver"] == "true":
            data[b]["solver"].append(c["mean_pass"])
        else:
            data[b]["llm"].append(c["mean_pass"])

    lines = [
        "**Pass rate by backend:**",
        "",
        "| Backend | LLM-only | Solver | N cells |",
        "|---|---|---|---|",
    ]
    for backend in ["sympy", "sage", "lean"]:
        d = data.get(backend)
        if not d or not d["solver"]:
            continue
        s = sum(d["solver"]) / len(d["solver"]) * 100
        l = sum(d["llm"])    / len(d["llm"])    * 100 if d["llm"] else 0
        n = len(d["solver"])
        lines.append(f"| {BACKEND_MAP.get(backend, backend)} | {l:.0f}% | {s:.0f}% | {n} |")
    return "\n".join(lines)


# ── Markdown document builder ─────────────────────────────────────────────────

def build_markdown(source: str, rows: list[dict]) -> str:
    cells   = aggregate(rows)
    models  = _sorted_models(cells)
    tiers   = _tiers_present(cells)
    n_runs  = max((c["n_runs"] for c in cells.values()), default=1)
    n_cells = len(rows)
    n_models   = len({r["mid"] for r in rows})
    n_problems = len({r["pid"] for r in rows})
    backends = sorted({(c.get("backend") or "") for c in cells.values()} - {""})
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    sections = [
        f"# Recipe-77 Experiment Results",
        f"",
        f"**Session:** `{source}`  ",
        f"**Generated:** {now}  ",
        f"**Cells:** {n_cells}  ({n_models} models × {n_problems} problems"
        + (f" × 2 arms × {n_runs} runs" if n_runs > 1 else " × 2 arms")
        + f")  ",
        f"**Backends:** {', '.join(BACKEND_MAP.get(b, b) for b in backends)}  ",
        f"",
        "---",
        "",
        "## §6.2  Results",
        "",
        table_pass_rates(cells, models, n_runs),
        "",
        table_latency(cells, models),
        "",
        "---",
        "",
        "## Appendix E.3  Per-Tier Pass Rates",
        "",
        table_per_tier_solver(cells, models, tiers),
        "",
        table_per_tier_llm(cells, models, tiers),
        "",
        "---",
        "",
        "## Appendix E.4  Failure Mode Breakdown (Solver Arm)",
        "",
        table_status_breakdown(cells, models),
        "",
        "---",
        "",
        "## Backend Comparison",
        "",
        table_backend_comparison(cells),
        "",
    ]
    return "\n".join(sections)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--db", default=str(DB_DEFAULT),
                        help="Path to SQLite database (default: %(default)s)")
    parser.add_argument("--source", default=None,
                        help="Experiment source_file ID to analyze (default: latest)")
    parser.add_argument("--out", default=None,
                        help="Output .md path (default: stdout)")
    parser.add_argument("--list-sources", action="store_true",
                        help="List available experiment runs and exit")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        sys.exit(f"DB not found: {db_path}")

    conn = get_conn(db_path)
    sources = list_sources(conn)

    if args.list_sources or not sources:
        if not sources:
            print("No experiment runs in DB.")
            return
        print(f"{'Source':<32}  {'Total':>6}  {'Done':>6}  {'Imported'}")
        for s in sources:
            print(f"{s['source_file']:<32}  {s['rows_total'] or '?':>6}  "
                  f"{s['rows_inserted'] or '?':>6}  {s['imported_at']}")
        return

    source = args.source or sources[0]["source_file"]
    rows   = load_rows(conn, source)
    if not rows:
        sys.exit(f"No rows found for source: {source}")

    md = build_markdown(source, rows)

    if args.out:
        out_path = Path(args.out)
        out_path.write_text(md)
        print(f"Written: {out_path}  ({len(rows)} rows, {len(md)} chars)")
    else:
        print(md)


if __name__ == "__main__":
    main()
