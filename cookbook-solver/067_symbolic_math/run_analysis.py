#!/usr/bin/env python3
"""
run_analysis.py — Analyze a Recipe-67 experiment log and print a readable report.

Must be run from the SPL.py repo root:
  cd ~/projects/digital-duck/SPL.py

Requires: conda activate spl123

Usage:
  python cookbook/67_symbolic_math/run_analysis.py                  # most recent log
  python cookbook/67_symbolic_math/run_analysis.py --log <path.md>  # specific log

Output:
  - Terminal report: results table, per-model summary, per-tier summary, failures
  - CSV file:        same name as the log, with .csv extension (one row per cell)

The log file must have been produced by run_experiment.py — each cell must
contain a <!-- RESULT ... --> tag written by that script.
"""

import re
from pathlib import Path

import click
import pandas as pd

# Import registries so the CSV includes human-readable problem text
from run_experiment import MODELS, PROBLEMS

LOG_DIR_DEFAULT = "cookbook/67_symbolic_math/logs-spl"

RESULT_RE = re.compile(
    r"<!-- RESULT\s+"
    r"pid=(?P<pid>\S+)\s+"
    r"mid=(?P<mid>\S+)\s+"
    r"label=(?P<label>\S+)\s+"
    r"tier=(?P<tier>\S+)\s+"
    r"solver=(?P<solver>\S+)\s+"
    r"run=(?P<run>\d+)\s+"
    r"status=(?P<status>\S+)\s+"
    r"llm_calls=(?P<llm_calls>\S+)\s+"
    r"latency_ms=(?P<latency_ms>\S+)\s+"
    r"steps=(?P<steps>\S+)\s+"
    r"spl_log=(?P<spl_log>\S+)"
    r"(?:\s+output_preview=(?P<output_preview>.*?))?"
    r"\s+-->"
)

# Statuses that count as a pass, per solver arm:
#   solver=true  → "complete" only (kernel ran and verified)
#   solver=false → "complete" OR "unverified_success" (LLM-only arm has no
#                  kernel by design, so steps=0 / unverified is expected)
PASS_STATUSES_SOLVER   = {"complete"}
PASS_STATUSES_LLM_ONLY = {"complete", "unverified_success"}


def find_latest_log(log_dir: str) -> Path:
    logs = sorted(Path(log_dir).glob("case-2-log-rerun-*.md"))
    if not logs:
        raise click.ClickException(f"No log files found in {log_dir}")
    return logs[-1]


def parse_log(log_path: Path) -> list:
    text = log_path.read_text()
    rows = []
    for m in RESULT_RE.finditer(text):
        r = m.groupdict()
        # output_preview absent in logs generated before it was added to the tag
        r["output_preview"] = (r["output_preview"] or "?").replace("_", " ")
        # Reclassify from output_preview sentinel prefixes — the SPL framework
        # sometimes emits Status: complete even when RETURN WITH carries a
        # different status; the Output line content is authoritative for these.
        preview = r["output_preview"]
        if preview.startswith("[SOLVER FAILURE]"):
            r["status"] = "solver_error"
        elif preview.startswith("[PLAN FAILURE]"):
            r["status"] = "plan_error"
        elif preview.startswith("[NARRATION FAILURE]"):
            r["status"] = "narration_error"
        # Reclassify: steps=0 + complete means pipeline was bypassed entirely —
        # the LLM free-formed an answer without SymPy verification.
        elif r["status"] == "complete" and r["steps"] == "0":
            r["status"] = "unverified_success"
        pass_set = PASS_STATUSES_LLM_ONLY if r.get("solver") == "false" else PASS_STATUSES_SOLVER
        r["pass"] = r["status"] in pass_set
        r["run"]         = int(r["run"])
        r["llm_calls"]   = int(r["llm_calls"])  if r["llm_calls"]  != "?" else None
        r["latency_ms"]  = int(r["latency_ms"]) if r["latency_ms"] != "?" else None
        r["steps"]       = int(r["steps"])       if r["steps"]      != "?" else None
        # Enrich with full problem text from registry
        r["problem"]     = PROBLEMS.get(r["pid"], ("?", "?"))[1]
        rows.append(r)
    return rows


def fmt_latency(ms) -> str:
    if ms is None:
        return "?"
    return f"{ms/1000:.1f}s"


def print_section(title: str):
    click.echo(f"\n{'─'*62}")
    click.echo(f"  {title}")
    click.echo(f"{'─'*62}")


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--log", "log_path", default=None,
              help="Path to experiment log .md file. "
                   "Defaults to the most recent file in logs-spl/.")
@click.option("--log-dir", default=LOG_DIR_DEFAULT, show_default=True,
              help="Directory to search for the most recent log (used when --log is omitted).")
def main(log_path, log_dir):
    """Analyse a run_experiment.py log and print a report + export a CSV."""

    path = Path(log_path) if log_path else find_latest_log(log_dir)
    if not path.exists():
        raise click.ClickException(f"Log file not found: {path}")

    rows = parse_log(path)
    if not rows:
        raise click.ClickException(
            "No <!-- RESULT --> tags found in the log.\n"
            "Re-run the experiment with the current run_experiment.py "
            "(older logs lack the RESULT tag)."
        )

    df = pd.DataFrame(rows)

    # ── CSV export ────────────────────────────────────────────────────────────
    csv_path = path.with_suffix(".csv")
    csv_cols = [
        "mid", "label", "pid", "tier", "problem",
        "solver", "run",
        "pass", "status", "output_preview",
        "llm_calls", "latency_ms", "steps",
        "spl_log",
    ]
    df[csv_cols].to_csv(csv_path, index=False)

    # ── Header ────────────────────────────────────────────────────────────────
    click.echo(f"\n{'='*62}")
    click.echo(f"  Recipe-67 Experiment Report")
    click.echo(f"  Log : {path.name}")
    click.echo(f"  CSV : {csv_path.name}")
    click.echo(f"  Cells: {len(df)}  |  Pass: {df['pass'].sum()}  |  Fail: {(~df['pass']).sum()}")
    click.echo(f"{'='*62}")

    # ── Full results table ────────────────────────────────────────────────────
    print_section("Results — all cells")

    display = df.copy()
    display["pass/fail"] = display["pass"].map({True: "✓ pass", False: "✗ fail"})
    display["latency"]   = display["latency_ms"].apply(fmt_latency)
    display["llm_calls"] = display["llm_calls"].fillna("?").astype(str)
    display["steps"]     = display["steps"].fillna("?").astype(str)

    click.echo(
        display[["mid", "label", "pid", "tier", "solver", "run",
                  "pass/fail", "status", "output_preview",
                  "llm_calls", "latency", "steps",
                  "spl_log"]].to_string(index=False)
    )

    # ── Per-model summary ─────────────────────────────────────────────────────
    print_section("Summary — by model")

    model_grp = df.groupby(["mid", "label"]).agg(
        cells        = ("pass", "count"),
        passed       = ("pass", "sum"),
        avg_latency  = ("latency_ms", "mean"),
        avg_calls    = ("llm_calls",  "mean"),
    ).reset_index()
    model_grp["pass_rate"]     = (model_grp["passed"] / model_grp["cells"] * 100).map("{:.0f}%".format)
    model_grp["avg_latency"]   = model_grp["avg_latency"].apply(lambda x: fmt_latency(x) if pd.notna(x) else "?")
    model_grp["avg_llm_calls"] = model_grp["avg_calls"].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "?")

    click.echo(
        model_grp[["mid", "label", "cells", "passed", "pass_rate",
                    "avg_latency", "avg_llm_calls"]].to_string(index=False)
    )

    # ── Per-tier summary ──────────────────────────────────────────────────────
    print_section("Summary — by problem tier")

    tier_grp = df.groupby(["tier", "pid"]).agg(
        cells       = ("pass", "count"),
        passed      = ("pass", "sum"),
        avg_latency = ("latency_ms", "mean"),
    ).reset_index()
    tier_grp["pass_rate"]   = (tier_grp["passed"] / tier_grp["cells"] * 100).map("{:.0f}%".format)
    tier_grp["avg_latency"] = tier_grp["avg_latency"].apply(lambda x: fmt_latency(x) if pd.notna(x) else "?")

    click.echo(
        tier_grp[["tier", "pid", "cells", "passed", "pass_rate",
                   "avg_latency"]].to_string(index=False)
    )

    # ── Failures detail ───────────────────────────────────────────────────────
    failures = df[~df["pass"]]
    if failures.empty:
        print_section("Failures — none  ✓")
    else:
        print_section(f"Failures — {len(failures)} cell(s)")
        fail_display = failures.copy()
        fail_display["latency"] = fail_display["latency_ms"].apply(fmt_latency)
        click.echo(
            fail_display[["mid", "label", "pid", "tier", "solver", "run",
                           "status", "output_preview", "latency", "steps",
                           "spl_log"]].to_string(index=False)
        )

    click.echo(f"\n  Log : {path}")
    click.echo(f"  CSV : {csv_path}\n")


if __name__ == "__main__":
    main()
