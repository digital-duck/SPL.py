#!/usr/bin/env python3
"""
SPL Cookbook Log Analyzer
Parses run_all batch logs and generates paper-ready reports.

Usage:
    # Latest spl3 run — paper stats to stdout
    python cookbook/analyze_logs.py --paper-stats

    # Specific run file
    python cookbook/analyze_logs.py --run cookbook/logs/exp1_spl3_single_20260419_121027.md --paper-stats

    # Full HTML report
    python cookbook/analyze_logs.py --html

    # Cross-runtime comparison table (§6.4) — specify one file per runtime
    python cookbook/analyze_logs.py --compare \\
        spl3=cookbook/logs/exp1_spl3_single_20260419_121027.md \\
        spl-go=cookbook/logs/run_all_go_20260419_140000.md \\
        spl-ts=cookbook/logs/run_all_ts_20260419_160000.md

    # All outputs
    python cookbook/analyze_logs.py --all
"""

from __future__ import annotations

import re
import json
import datetime
from pathlib import Path

import click

COOKBOOK_DIR = Path(__file__).resolve().parent
LOG_DIR      = COOKBOOK_DIR / "logs"        # batch run logs live here
OUT_DIR      = COOKBOOK_DIR / "out"         # HTML output

# ── Batch run_all log regexes ─────────────────────────────────────────────────

# Header: === SPL Cookbook Batch Run — 2026-04-19 12:10:27 ===
RUN_HEADER_RE = re.compile(r"=== SPL.*?Batch Run.*?([\d-]+ [\d:]+)")

# Adapter/model line: "    Adapter : ollama  |  Model : gemma3"
RUN_ADAPTER_RE = re.compile(r"Adapter\s*:\s*(\S+)")
RUN_MODEL_RE   = re.compile(r"Model\s*:\s*(\S+)")

# Per-recipe block start: [01] Hello World
RECIPE_BLOCK_RE = re.compile(r"^\[(\d+)\]\s+(.+)$", re.M)

# Result line: "     result: SUCCESS  (2.5s)"
RESULT_LINE_RE = re.compile(r"result:\s+(SUCCESS|FAILED|SKIP)\s+\(([\d.]+)s\)")

# Inline stats from embedded log dump (lines prefixed with "|")
BLOCK_CALLS_RE   = re.compile(r"\|\s*LLM calls:\s*(\d+)",              re.I)
BLOCK_TOKENS_RE  = re.compile(r"\|\s*Tokens?:\s*(\d+)\s+in\s*/\s*(\d+)\s+out", re.I)
BLOCK_MODEL_RE   = re.compile(r"\|\s*Model:\s*(.+)",                   re.I)
BLOCK_STATUS_RE  = re.compile(r"\|\s*Status:\s*(\S+)",                 re.I)

# Summary totals: === Summary: 41/52 Success  (total 1111.9s) ===
SUMMARY_TOT_RE = re.compile(
    r"=== Summary:\s+(\d+)/(\d+)\s+\w+\s+\(total\s+([\d.]+)s\)"
)

# ── Catalog ───────────────────────────────────────────────────────────────────

def load_catalog(catalog_file: str | None = None) -> dict:
    path = Path(catalog_file) if catalog_file else COOKBOOK_DIR / "cookbook_catalog.json"
    if not path.exists():
        return {}
    with open(path) as f:
        data = json.load(f)
    def _spl_path(r):
        for a in r.get("args", []):
            if a.endswith(".spl"):
                return a.lstrip("./")  # e.g. "cookbook/01_hello_world/hello.spl"
        return ""

    return {
        r["id"]: {
            "id":          r.get("id", "?"),
            "name":        r.get("name", ""),
            "category":    r.get("category", "-"),
            "description": r.get("description", ""),
            "dir":         r.get("dir", ""),
            "spl_path":    _spl_path(r),
        }
        for r in data.get("recipes", [])
        if r.get("is_active", True)
    }

# ── SPL type detection ────────────────────────────────────────────────────────

def detect_spl_type(recipe_dir: Path) -> str:
    spl_files = [f for f in recipe_dir.glob("*.spl")
                 if "variant" not in str(f) and f.parent == recipe_dir]
    if not spl_files:
        return "unknown"
    content = spl_files[0].read_text(errors="replace")
    for line in content.splitlines():
        s = line.strip()
        if s.startswith("--"):
            continue
        if re.match(r"^WORKFLOW\b", s, re.I):
            return "workflow"
        if re.match(r"^PROMPT\b", s, re.I):
            return "prompt"
    return "unknown"

# ── Batch run file discovery ──────────────────────────────────────────────────

def find_run_files(runtime: str | None = None) -> list[Path]:
    """Return batch log files sorted newest-first, optionally filtered by runtime tag."""
    if not LOG_DIR.exists():
        return []
    candidates = sorted(LOG_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    if runtime:
        candidates = [p for p in candidates if runtime in p.name]
    return candidates


def latest_run_file(runtime: str | None = None) -> Path | None:
    files = find_run_files(runtime)
    return files[0] if files else None

# ── Batch run file parser ─────────────────────────────────────────────────────

def parse_run_file(run_path: Path) -> dict:
    """
    Returns:
      {
        "timestamp": str, "adapter": str, "model": str,
        "passed": int, "total": int, "wall_time_s": float,
        "recipes": {
          recipe_id (int): {
            "name": str, "status": "SUCCESS"|"FAILED"|"SKIP",
            "elapsed_s": float, "llm_calls": int,
            "tokens_in": int, "tokens_out": int, "model": str,
            "spl_status": str   # the SPL workflow status string
          }
        }
      }
    """
    content = run_path.read_text(errors="replace")

    m = RUN_HEADER_RE.search(content)
    timestamp = m.group(1) if m else "unknown"

    m = RUN_ADAPTER_RE.search(content)
    adapter = m.group(1) if m else "?"

    m = RUN_MODEL_RE.search(content)
    model_default = m.group(1) if m else "?"

    m = SUMMARY_TOT_RE.search(content)
    passed      = int(m.group(1))   if m else 0
    total_count = int(m.group(2))   if m else 0
    wall_time   = float(m.group(3)) if m else 0.0

    # Split on recipe block boundaries
    recipe_data: dict[int, dict] = {}
    parts = re.split(r"\n(?=\[\d+\] )", content)
    for part in parts:
        m_head = RECIPE_BLOCK_RE.match(part.lstrip("\n"))
        if not m_head:
            continue
        rid  = int(m_head.group(1))
        name = m_head.group(2).strip()
        # Strip section label suffixes like "  (Ollama only)"
        name = re.sub(r"\s+\(.*?\)$", "", name)

        m_res = RESULT_LINE_RE.search(part)
        status    = m_res.group(1) if m_res else "UNKNOWN"
        elapsed_s = float(m_res.group(2)) if m_res else 0.0

        calls_all  = BLOCK_CALLS_RE.findall(part)
        tokens_all = BLOCK_TOKENS_RE.findall(part)
        model_all  = BLOCK_MODEL_RE.findall(part)
        status_all = BLOCK_STATUS_RE.findall(part)

        llm_calls  = int(calls_all[-1])        if calls_all  else 1
        tokens_in  = int(tokens_all[-1][0])    if tokens_all else 0
        tokens_out = int(tokens_all[-1][1])    if tokens_all else 0
        model      = model_all[-1].strip()     if model_all  else model_default
        spl_status = status_all[-1].strip()    if status_all else "-"

        recipe_data[rid] = {
            "name":       name,
            "status":     status,
            "elapsed_s":  elapsed_s,
            "llm_calls":  llm_calls,
            "tokens_in":  tokens_in,
            "tokens_out": tokens_out,
            "model":      model,
            "spl_status": spl_status,
        }

    return {
        "timestamp":   timestamp,
        "adapter":     adapter,
        "model":       model_default,
        "passed":      passed,
        "total":       total_count,
        "wall_time_s": wall_time,
        "recipes":     recipe_data,
    }

# ── Individual recipe log lookup ──────────────────────────────────────────────

def get_latest_recipe_log(recipe_dir: Path) -> Path | None:
    logs_dir = recipe_dir / "logs"
    if not logs_dir.exists():
        return None
    candidates = sorted(logs_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None

# ── Paper stats (aggregate metrics) ──────────────────────────────────────────

def print_paper_stats(run: dict, catalog: dict, runtime_label: str = "spl3"):
    recipes = run["recipes"]

    type_map: dict[int, str] = {}
    for rid in recipes:
        cat = catalog.get(str(rid).zfill(2)) or catalog.get(str(rid))
        if cat and cat.get("dir"):
            subdir = COOKBOOK_DIR / cat["dir"]
            type_map[rid] = detect_spl_type(subdir)
        else:
            type_map[rid] = "unknown"

    successful = {rid: r for rid, r in recipes.items() if r["status"] == "SUCCESS"}
    failed     = {rid: r for rid, r in recipes.items() if r["status"] == "FAILED"}
    prompt_ok  = [rid for rid in successful if type_map.get(rid) == "prompt"]
    workflow_ok = [rid for rid in successful if type_map.get(rid) == "workflow"]

    print(f"\n=== {runtime_label} — Cookbook Validation Metrics ===\n")
    print(f"  Run timestamp   : {run['timestamp']}")
    print(f"  Adapter / Model : {run['adapter']} / {run['model']}")
    print(f"  Pass rate       : {run['passed']}/{run['total']}  "
          f"({100*run['passed']//run['total'] if run['total'] else 0}%)")
    print(f"  Total wall time : {run['wall_time_s']:,.1f}s  "
          f"({run['wall_time_s']/60:.1f} min)")

    if prompt_ok:
        lats = [recipes[r]["elapsed_s"] for r in prompt_ok]
        print(f"\n  PROMPT recipes  : {len(prompt_ok)}")
        print(f"    avg latency   : {sum(lats)/len(lats):.1f}s  "
              f"(range {min(lats):.1f}s – {max(lats):.1f}s)")

    if workflow_ok:
        lats  = [recipes[r]["elapsed_s"] for r in workflow_ok]
        calls = [recipes[r]["llm_calls"]  for r in workflow_ok]
        print(f"\n  WORKFLOW recipes: {len(workflow_ok)}")
        print(f"    avg latency   : {sum(lats)/len(lats):.1f}s  "
              f"(range {min(lats):.1f}s – {max(lats):.1f}s)")
        print(f"    avg LLM calls : {sum(calls)/len(calls):.1f}  "
              f"(range {min(calls)} – {max(calls)})")

        fastest_id = min(workflow_ok, key=lambda r: recipes[r]["elapsed_s"])
        slowest_id = max(workflow_ok, key=lambda r: recipes[r]["elapsed_s"])
        print(f"    fastest       : [{fastest_id:02d}] {recipes[fastest_id]['name']}  "
              f"{recipes[fastest_id]['elapsed_s']:.1f}s")
        print(f"    slowest       : [{slowest_id:02d}] {recipes[slowest_id]['name']}  "
              f"{recipes[slowest_id]['elapsed_s']:.1f}s")

    if successful:
        max_id = max(successful, key=lambda r: successful[r]["tokens_in"] + successful[r]["tokens_out"])
        r = successful[max_id]
        if r["tokens_in"] + r["tokens_out"] > 0:
            print(f"\n  Max tokens      : {r['tokens_in']:,} in / {r['tokens_out']:,} out"
                  f"  — [{max_id:02d}] {r['name']}")

    if failed:
        print(f"\n  Failed ({len(failed)}): " +
              ", ".join(f"[{rid:02d}] {r['name']}" for rid, r in sorted(failed.items())))
    print()

# ── Per-recipe markdown table ─────────────────────────────────────────────────

def print_paper_summary(run: dict, catalog: dict, runtime_label: str = "spl3"):
    recipes  = run["recipes"]
    passed   = run["passed"]
    total    = run["total"]

    print(f"\n=== {runtime_label} — Per-Recipe Results "
          f"({passed}/{total}) ===\n")
    print(f"| ID | Recipe | Category | Status | Elapsed | LLM Calls | Tokens in/out |")
    print(f"|----|--------|----------|--------|---------|-----------|---------------|")

    for rid in sorted(recipes):
        r   = recipes[rid]
        cat = catalog.get(str(rid).zfill(2)) or catalog.get(str(rid)) or {}
        ok  = "✅" if r["status"] == "SUCCESS" else "❌"
        tok = (f"{r['tokens_in']:,}/{r['tokens_out']:,}"
               if r["tokens_in"] or r["tokens_out"] else "—")
        print(f"| {rid:02d} | {r['name']:<30} | {cat.get('category','-'):<12} "
              f"| {ok} {r['status']:<7} | {r['elapsed_s']:>6.1f}s "
              f"| {r['llm_calls']:>5} | {tok:>13} |")

    print()

# ── Cross-runtime comparison (§6.4) ──────────────────────────────────────────

def print_cross_runtime_table(runs: dict[str, dict], catalog: dict):
    """
    runs: {"spl3": run_dict, "spl-go": run_dict, "spl-ts": run_dict, ...}
    Prints the §6.4 conformance matrix for the NeurIPS paper.
    """
    labels  = list(runs.keys())
    all_ids = sorted(set(rid for r in runs.values() for rid in r["recipes"]))

    # Status symbol
    def sym(run_dict, rid):
        r = run_dict["recipes"].get(rid)
        if r is None:
            return "—"
        return "✅" if r["status"] == "SUCCESS" else "❌"

    print("\n=== Cross-Runtime Conformance Matrix (§6.4) ===\n")

    # Header
    col_w = 10
    header = f"| {'ID':<4} | {'Recipe':<30} | {'Category':<12} |"
    header += "".join(f" {lb:<{col_w}} |" for lb in labels)
    print(header)

    sep = f"|{'-'*5}|{'-'*32}|{'-'*14}|"
    sep += "".join(f"{'-'*(col_w+2)}|" for _ in labels)
    print(sep)

    approved = []
    for rid in all_ids:
        cat  = catalog.get(str(rid).zfill(2)) or catalog.get(str(rid)) or {}
        name = next((r["recipes"][rid]["name"]
                     for r in runs.values() if rid in r["recipes"]),
                    cat.get("name", f"Recipe {rid}"))
        syms = [sym(runs[lb], rid) for lb in labels]
        row = (f"| {rid:02d}   | {name:<30} | {cat.get('category','-'):<12} |"
               + "".join(f" {s:<{col_w}} |" for s in syms))
        print(row)
        if all(s == "✅" for s in syms):
            approved.append(rid)

    # Summary row
    print(sep)
    totals = f"| {'TOTAL':<4} | {'':<30} | {'':<12} |"
    for lb in labels:
        r = runs[lb]
        totals += f" {r['passed']}/{r['total']:<{col_w-3}} |"
    print(totals)

    wall_row = f"| {'TIME':<4} | {'':<30} | {'':<12} |"
    for lb in labels:
        r = runs[lb]
        wall_row += f" {r['wall_time_s']:>{col_w-1}.0f}s |"
    print(wall_row)

    print()
    print(f"Approved across all {len(labels)} runtimes: "
          f"{len(approved)}/{len(all_ids)} recipes")
    if approved:
        print(f"  IDs: {', '.join(f'{i:02d}' for i in approved)}")
    print()

    # Paper-ready aggregate table
    print("### Table — Validation Summary\n")
    print(f"| Runtime | Pass | Total | Pass Rate | Wall Time |")
    print(f"|---------|------|-------|-----------|-----------|")
    for lb in labels:
        r = runs[lb]
        pct = f"{100*r['passed']//r['total']}%" if r["total"] else "—"
        mins = f"{r['wall_time_s']/60:.1f} min"
        print(f"| {lb:<7} | {r['passed']:>4} | {r['total']:>5} | {pct:>9} | {mins:>9} |")
    print()

# ── HTML report ───────────────────────────────────────────────────────────────

def generate_html(run: dict, catalog: dict, runtime_label: str = "spl3") -> Path:
    import html as _html

    OUT_DIR.mkdir(exist_ok=True)
    ts_str   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stamp    = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"spl-cookbook-{runtime_label}-{stamp}.html"
    out_path = OUT_DIR / filename

    recipes = run["recipes"]
    passed  = run["passed"]
    total   = run["total"]

    def status_txt(r): return "OK" if r["status"] == "SUCCESS" else "FAIL"
    def fmt_tokens(r):
        if r["tokens_in"] or r["tokens_out"]:
            return f"{r['tokens_in']:,} / {r['tokens_out']:,}"
        return "—"

    # Build rows — embed SPL source as data-src attribute (JSON-escaped)
    rows_html = ""
    for rid in sorted(recipes):
        r        = recipes[rid]
        cat      = catalog.get(str(rid).zfill(2)) or catalog.get(str(rid)) or {}
        ok       = r["status"] == "SUCCESS"
        spl_path = cat.get("spl_path", "")
        abs_spl  = COOKBOOK_DIR.parent / spl_path if spl_path else None

        if abs_spl and abs_spl.exists():
            src_escaped = _html.escape(abs_spl.read_text(errors="replace"), quote=True)
            name_cell = (
                f'<a href="#" class="src-link" '
                f'data-title="{_html.escape(spl_path)}" '
                f'data-src="{src_escaped}">'
                f'<strong>{_html.escape(r["name"])}</strong></a>'
            )
        else:
            name_cell = f"<strong>{_html.escape(r['name'])}</strong>"

        rows_html += (
            f'<tr data-status="{r["status"]}" '
            f'data-elapsed="{r["elapsed_s"]}" '
            f'data-calls="{r["llm_calls"]}" '
            f'data-tokens="{r["tokens_in"] + r["tokens_out"]}">\n'
            f'  <td class="mono" data-val="{rid}">{rid:02d}</td>\n'
            f'  <td>{name_cell}</td>\n'
            f'  <td class="cat" data-val="{_html.escape(cat.get("category",""))}">'
            f'{_html.escape(cat.get("category","-"))}</td>\n'
            f'  <td class="{"ok" if ok else "fail"}" data-val="{r["status"]}">'
            f'{"✅" if ok else "❌"} {status_txt(r)}</td>\n'
            f'  <td class="mono">{_html.escape(r["model"])}</td>\n'
            f'  <td class="mono" data-val="{r["elapsed_s"]}">{r["elapsed_s"]:.1f}s</td>\n'
            f'  <td class="mono" style="text-align:center" data-val="{r["llm_calls"]}">'
            f'{r["llm_calls"]}</td>\n'
            f'  <td class="mono" data-val="{r["tokens_in"]+r["tokens_out"]}">'
            f'{fmt_tokens(r)}</td>\n'
            f'  <td class="spl-status">{_html.escape(r["spl_status"])}</td>\n'
            f'</tr>\n'
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>SPL Cookbook — {runtime_label}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    body     {{ font-family: 'Segoe UI', Tahoma, sans-serif;
               background: #0e1117; color: #e6edf3; margin: 0; padding: 32px 48px; }}
    h1       {{ color: #4f8ef7; border-bottom: 2px solid #21262d;
               padding-bottom: 10px; margin-bottom: 6px; }}
    .meta    {{ color: #8b949e; margin-bottom: 24px; font-size: .95em; }}
    .meta b  {{ color: #3fb950; }}

    /* ── Table ── */
    .tbl-wrap {{ overflow-x: auto; border-radius: 10px;
                box-shadow: 0 4px 20px rgba(0,0,0,.5); }}
    table    {{ width: 100%; border-collapse: collapse; background: #161b22; }}
    th, td   {{ padding: 9px 13px; text-align: left;
               border-bottom: 1px solid #30363d; white-space: nowrap; }}
    th       {{ background: #21262d; color: #8b949e; font-size: 11px;
               font-weight: 700; text-transform: uppercase; letter-spacing: .5px;
               cursor: pointer; user-select: none; position: sticky; top: 0; }}
    th:hover {{ color: #e6edf3; background: #2d333b; }}
    th .arrow {{ margin-left: 4px; opacity: .4; font-size: 10px; }}
    th.asc  .arrow::after {{ content: "▲"; opacity: 1; }}
    th.desc .arrow::after {{ content: "▼"; opacity: 1; }}
    th:not(.asc):not(.desc) .arrow::after {{ content: "⇅"; }}
    tr:hover {{ background: #1c2128; }}
    .ok      {{ color: #3fb950; font-weight: 600; }}
    .fail    {{ color: #f85149; font-weight: 600; }}
    .mono    {{ font-family: 'SFMono-Regular', Consolas, monospace; font-size: 12px; }}
    .cat     {{ font-size: 11px; color: #8b949e; }}
    .spl-status {{ font-size: 11px; color: #a5d6ff; font-style: italic; }}
    a        {{ color: #79c0ff; text-decoration: none; }}
    a:hover  {{ text-decoration: underline; }}

    /* ── Filter bar ── */
    .filters {{ display: flex; gap: 12px; margin-bottom: 14px; flex-wrap: wrap; }}
    .filters input, .filters select {{
      background: #161b22; color: #e6edf3; border: 1px solid #30363d;
      border-radius: 6px; padding: 6px 10px; font-size: 13px; }}
    .filters input:focus, .filters select:focus {{
      outline: none; border-color: #4f8ef7; }}

    /* ── Modal ── */
    #modal-backdrop {{
      display: none; position: fixed; inset: 0;
      background: rgba(0,0,0,.75); z-index: 100;
      align-items: center; justify-content: center; }}
    #modal-backdrop.open {{ display: flex; }}
    #modal {{
      background: #161b22; border: 1px solid #30363d; border-radius: 10px;
      width: min(860px, 92vw); max-height: 82vh;
      display: flex; flex-direction: column;
      box-shadow: 0 8px 40px rgba(0,0,0,.7); }}
    #modal-header {{
      display: flex; justify-content: space-between; align-items: center;
      padding: 12px 18px; border-bottom: 1px solid #30363d; }}
    #modal-title {{ font-weight: 600; color: #79c0ff; font-size: 13px; }}
    #modal-close {{
      background: none; border: none; color: #8b949e; font-size: 20px;
      cursor: pointer; line-height: 1; padding: 0 4px; }}
    #modal-close:hover {{ color: #f85149; }}
    #modal-body {{
      overflow-y: auto; padding: 0; flex: 1; }}
    #modal-body pre {{
      margin: 0; padding: 18px 20px;
      font-family: 'SFMono-Regular', Consolas, monospace;
      font-size: 13px; line-height: 1.6; color: #e6edf3;
      white-space: pre; tab-size: 4; }}

    .footer {{ margin-top: 32px; font-size: 12px; color: #8b949e; text-align: center; }}
  </style>
</head>
<body>
  <h1>SPL Cookbook — Batch Run Report <span style="color:#8b949e;font-size:.7em">({runtime_label})</span></h1>
  <div class="meta">
    Generated: {ts_str} &nbsp;|&nbsp;
    Runtime: <b>{runtime_label}</b> &nbsp;|&nbsp;
    Adapter: <b>{run['adapter']}</b> &nbsp;|&nbsp;
    Model: <b>{run['model']}</b> &nbsp;|&nbsp;
    Pass: <b>{passed}/{total}</b> &nbsp;|&nbsp;
    Wall time: <b>{run['wall_time_s']:.0f}s</b>
  </div>

  <div class="filters">
    <input id="f-search" type="search" placeholder="🔍  Search recipe…" style="flex:1;min-width:180px">
    <select id="f-status">
      <option value="">All statuses</option>
      <option value="SUCCESS">✅ OK only</option>
      <option value="FAILED">❌ Failed only</option>
    </select>
    <select id="f-cat"><option value="">All categories</option></select>
  </div>

  <div class="tbl-wrap">
  <table id="main-table">
    <thead>
      <tr>
        <th data-col="0">#<span class="arrow"></span></th>
        <th>Recipe</th>
        <th data-col="2">Category<span class="arrow"></span></th>
        <th data-col="3">Status<span class="arrow"></span></th>
        <th>Model</th>
        <th data-col="5">Elapsed<span class="arrow"></span></th>
        <th data-col="6">LLM Calls<span class="arrow"></span></th>
        <th data-col="7">Tokens in/out<span class="arrow"></span></th>
        <th>SPL Status</th>
      </tr>
    </thead>
    <tbody id="tbody">
{rows_html}    </tbody>
  </table>
  </div>

  <div id="modal-backdrop">
    <div id="modal">
      <div id="modal-header">
        <span id="modal-title"></span>
        <button id="modal-close">✕</button>
      </div>
      <div id="modal-body"><pre id="modal-pre"></pre></div>
    </div>
  </div>

  <div class="footer">
    SPL 3.0 — Declarative Agentic Workflow Language &nbsp;|&nbsp;
    Digital Duck © 2026 &nbsp;|&nbsp; Apache 2.0
  </div>

<script>
(function() {{
  // ── Sorting ──────────────────────────────────────────────────────────────
  const tbody  = document.getElementById('tbody');
  const ths    = document.querySelectorAll('th[data-col]');
  let sortCol  = null, sortAsc = true;

  function cellVal(row, col) {{
    const td = row.children[col];
    return td.dataset.val !== undefined ? td.dataset.val : td.textContent.trim();
  }}

  function sortBy(col) {{
    sortAsc = (sortCol === col) ? !sortAsc : true;
    sortCol = col;
    ths.forEach(th => {{ th.classList.remove('asc','desc'); }});
    const th = [...ths].find(t => +t.dataset.col === col);
    if (th) th.classList.add(sortAsc ? 'asc' : 'desc');

    const rows = [...tbody.querySelectorAll('tr')];
    rows.sort((a, b) => {{
      let av = cellVal(a, col), bv = cellVal(b, col);
      const an = parseFloat(av), bn = parseFloat(bv);
      if (!isNaN(an) && !isNaN(bn)) {{ av = an; bv = bn; }}
      if (av < bv) return sortAsc ? -1 : 1;
      if (av > bv) return sortAsc ?  1 : -1;
      return 0;
    }});
    rows.forEach(r => tbody.appendChild(r));
  }}

  ths.forEach(th => th.addEventListener('click', () => sortBy(+th.dataset.col)));

  // ── Filtering ────────────────────────────────────────────────────────────
  const fSearch = document.getElementById('f-search');
  const fStatus = document.getElementById('f-status');
  const fCat    = document.getElementById('f-cat');

  // Populate category dropdown
  const cats = [...new Set([...tbody.querySelectorAll('td:nth-child(3)')].map(td => td.textContent.trim()))].sort();
  cats.forEach(c => {{ const o = document.createElement('option'); o.value = o.text = c; fCat.appendChild(o); }});

  function applyFilters() {{
    const q   = fSearch.value.toLowerCase();
    const st  = fStatus.value;
    const cat = fCat.value;
    tbody.querySelectorAll('tr').forEach(row => {{
      const name   = row.children[1].textContent.toLowerCase();
      const status = row.dataset.status;
      const rowCat = row.children[2].textContent.trim();
      const show   = (!q || name.includes(q))
                  && (!st  || status === st)
                  && (!cat || rowCat === cat);
      row.style.display = show ? '' : 'none';
    }});
  }}

  [fSearch, fStatus, fCat].forEach(el => el.addEventListener('input', applyFilters));

  // ── Source modal ─────────────────────────────────────────────────────────
  const backdrop = document.getElementById('modal-backdrop');
  const title    = document.getElementById('modal-title');
  const pre      = document.getElementById('modal-pre');

  document.getElementById('modal-close').addEventListener('click', () => backdrop.classList.remove('open'));
  backdrop.addEventListener('click', e => {{ if (e.target === backdrop) backdrop.classList.remove('open'); }});
  document.addEventListener('keydown', e => {{ if (e.key === 'Escape') backdrop.classList.remove('open'); }});

  document.addEventListener('click', e => {{
    const link = e.target.closest('.src-link');
    if (!link) return;
    e.preventDefault();
    title.textContent = link.dataset.title;
    pre.textContent   = link.dataset.src;
    backdrop.classList.add('open');
  }});
}})();
</script>
</body>
</html>"""

    out_path.write_text(html, encoding="utf-8")
    return out_path

# ── CLI ───────────────────────────────────────────────────────────────────────

@click.command(context_settings={"max_content_width": 100})
@click.option("--run", "run_path", default=None, metavar="FILE",
              help="Batch run log file (default: latest in cookbook/logs/)")
@click.option("--runtime", default="spl3", show_default=True,
              help="Runtime label for reports (spl3 | spl-go | spl-ts)")
@click.option("--catalog-file", default=None, metavar="FILE",
              help="Catalog JSON file (default: cookbook_catalog.json)")
@click.option("--paper-stats",  is_flag=True,
              help="Print aggregate metrics for the NeurIPS paper")
@click.option("--summary",      is_flag=True,
              help="Print per-recipe markdown table")
@click.option("--html",         is_flag=True,
              help="Generate HTML report in cookbook/out/")
@click.option("--compare", multiple=True, metavar="RUNTIME=FILE",
              help="Cross-runtime comparison: --compare spl3=run1.md --compare spl-go=run2.md")
@click.option("--all", "include_all", is_flag=True,
              help="HTML + per-recipe table + aggregate stats")
def main(run_path, runtime, catalog_file,
         paper_stats, summary, html, compare, include_all):
    """Analyze SPL cookbook batch run logs and generate paper-ready reports."""

    catalog = load_catalog(catalog_file)

    # ── Cross-runtime comparison mode ─────────────────────────────────────────
    if compare:
        runs: dict[str, dict] = {}
        for spec in compare:
            if "=" not in spec:
                raise click.BadParameter(f"Expected RUNTIME=FILE, got: {spec!r}")
            label, fpath = spec.split("=", 1)
            p = Path(fpath)
            if not p.exists():
                raise click.ClickException(f"Run file not found: {fpath}")
            runs[label] = parse_run_file(p)
            click.echo(f"  Loaded {label}: {p.name}  "
                       f"({runs[label]['passed']}/{runs[label]['total']} passed)")
        print_cross_runtime_table(runs, catalog)
        return

    # ── Single-runtime mode ────────────────────────────────────────────────────
    path = Path(run_path) if run_path else latest_run_file(runtime)
    if path is None or not path.exists():
        raise click.ClickException(
            f"No run log found for runtime={runtime!r} in {LOG_DIR}/\n"
            "Run:  python cookbook/run_all.py --adapter ollama"
        )

    run = parse_run_file(path)
    click.echo(f"Loaded: {path.name}  "
               f"({run['passed']}/{run['total']} passed, {run['wall_time_s']:.0f}s)")

    if include_all:
        out = generate_html(run, catalog, runtime)
        click.echo(f"HTML:   {out}")
        print_paper_summary(run, catalog, runtime)
        print_paper_stats(run, catalog, runtime)
    elif html:
        out = generate_html(run, catalog, runtime)
        click.echo(f"HTML:   {out}")
    elif summary:
        print_paper_summary(run, catalog, runtime)
    elif paper_stats:
        print_paper_stats(run, catalog, runtime)
    else:
        # Default: stats to stdout
        print_paper_stats(run, catalog, runtime)


if __name__ == "__main__":
    main()
