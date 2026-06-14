#!/usr/bin/env python3
"""
migrate_pocketflow.py — PocketFlow → SPL migration CLI

Subcommands:
  migrate   Run S1→S2→S3 pipeline for selected recipes × model
  validate  Run spl3 validate on migrated .spl files
  report    Print model×recipe accuracy table from result logs

Examples:
  python migrate_pocketflow.py migrate --phase phase1
  python migrate_pocketflow.py migrate --recipe 001,002,003 --model qwen/qwen3.6-plus
  python migrate_pocketflow.py migrate --recipe all --adapter openrouter --model google/gemini-3-flash-preview
  python migrate_pocketflow.py validate --phase phase1
  python migrate_pocketflow.py report
"""

import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

import click

# ── Paths ────────────────────────────────────────────────────────────────────

_HERE    = Path(__file__).parent                          # cookbook-pocketflow/
_PF_BASE = Path.home() / "projects/wgong/PocketFlow/cookbook"
_RESULTS = _HERE / "logs" / "results.jsonl"

# ── Recipe registry ──────────────────────────────────────────────────────────
# Key: 3-digit number string.  Fields:
#   name   snake_case identifier → directory suffix and canonical .spl filename
#   pf     pocketflow-<subdir> name under PF_BASE
#   tier   1-5
#   diff   difficulty label
#   seeded True if already bootstrapped from NeurIPS lab (skip by default)

RECIPES: dict[str, dict] = {
    # ── Tier 1: basic single-LLM ☆☆☆ ────────────────────────────────────────
    "001": {"name": "chat",              "pf": "pocketflow-chat",              "tier": 1, "diff": "☆☆☆"},
    "002": {"name": "structured_output", "pf": "pocketflow-structured-output", "tier": 1, "diff": "☆☆☆"},
    "003": {"name": "workflow",          "pf": "pocketflow-workflow",           "tier": 1, "diff": "☆☆☆"},
    "004": {"name": "agent",             "pf": "pocketflow-agent",              "tier": 1, "diff": "☆☆☆", "seeded": True},
    "005": {"name": "rag",               "pf": "pocketflow-rag",               "tier": 1, "diff": "☆☆☆", "seeded": True},
    "006": {"name": "map_reduce",        "pf": "pocketflow-map-reduce",         "tier": 1, "diff": "☆☆☆"},
    "008": {"name": "chat_guardrail",    "pf": "pocketflow-chat-guardrail",     "tier": 1, "diff": "☆☆☆"},
    # ── Tier 2: multi-step / agentic ★☆☆ ────────────────────────────────────
    "010": {"name": "multi_agent",       "pf": "pocketflow-multi-agent",        "tier": 2, "diff": "★☆☆"},
    "011": {"name": "supervisor",        "pf": "pocketflow-supervisor",         "tier": 2, "diff": "★☆☆"},
    "012": {"name": "batch_node",        "pf": "pocketflow-batch-node",         "tier": 2, "diff": "★☆☆"},
    "013": {"name": "batch_flow",        "pf": "pocketflow-batch-flow",         "tier": 2, "diff": "★☆☆"},
    "014": {"name": "thinking",          "pf": "pocketflow-thinking",           "tier": 2, "diff": "★☆☆", "seeded": True},
    "015": {"name": "chat_memory",       "pf": "pocketflow-chat-memory",        "tier": 2, "diff": "★☆☆"},
    "016": {"name": "mcp",               "pf": "pocketflow-mcp",               "tier": 2, "diff": "★☆☆"},
    "017": {"name": "judge",             "pf": "pocketflow-judge",              "tier": 2, "diff": "★☆☆", "seeded": True},
    "018": {"name": "debate",            "pf": "pocketflow-debate",             "tier": 2, "diff": "★☆☆"},
    "019": {"name": "agentic_rag",       "pf": "pocketflow-agentic-rag",        "tier": 2, "diff": "★☆☆"},
    "020": {"name": "heartbeat",         "pf": "pocketflow-heartbeat",          "tier": 2, "diff": "★☆☆"},
    "021": {"name": "self_healing",      "pf": "pocketflow-self-healing-mermaid","tier": 2, "diff": "★☆☆"},
    # ── Tier 3: intermediate pipelines ★★☆ ───────────────────────────────────
    "030": {"name": "lead_generation",   "pf": "pocketflow-lead-generation",    "tier": 3, "diff": "★★☆"},
    "031": {"name": "invoice",           "pf": "pocketflow-invoice",            "tier": 3, "diff": "★★☆"},
    "032": {"name": "deep_research",     "pf": "pocketflow-deep-research",      "tier": 3, "diff": "★★☆", "seeded": True},
    "033": {"name": "text2sql",          "pf": "pocketflow-text2sql",           "tier": 3, "diff": "★★☆"},
    "034": {"name": "communication",     "pf": "pocketflow-communication",      "tier": 3, "diff": "★★☆"},
    # ── Tier 4: advanced / production ★★★ ────────────────────────────────────
    "040": {"name": "coding_agent",      "pf": "pocketflow-coding-agent",       "tier": 4, "diff": "★★★"},
    "041": {"name": "agent_skills",      "pf": "pocketflow-agent-skills",       "tier": 4, "diff": "★★★"},
    # ── Tier 5: extended catalog ──────────────────────────────────────────────
    "050": {"name": "a2a",               "pf": "pocketflow-a2a",               "tier": 5, "diff": "—"},
    "051": {"name": "async_basic",       "pf": "pocketflow-async-basic",        "tier": 5, "diff": "—"},
    "052": {"name": "batch",             "pf": "pocketflow-batch",              "tier": 5, "diff": "—"},
    "053": {"name": "cli_hitl",          "pf": "pocketflow-cli-hitl",           "tier": 5, "diff": "—"},
    "054": {"name": "code_generator",    "pf": "pocketflow-code-generator",     "tier": 5, "diff": "—"},
    "055": {"name": "flow",              "pf": "pocketflow-flow",               "tier": 5, "diff": "—"},
    "056": {"name": "majority_vote",     "pf": "pocketflow-majority-vote",      "tier": 5, "diff": "—"},
    "057": {"name": "tao",               "pf": "pocketflow-tao",               "tier": 5, "diff": "—"},
    "058": {"name": "tool_crawler",      "pf": "pocketflow-tool-crawler",       "tier": 5, "diff": "—"},
    "059": {"name": "tool_database",     "pf": "pocketflow-tool-database",      "tier": 5, "diff": "—"},
    "060": {"name": "tool_embeddings",   "pf": "pocketflow-tool-embeddings",    "tier": 5, "diff": "—"},
    "061": {"name": "tool_pdf_vision",   "pf": "pocketflow-tool-pdf-vision",    "tier": 5, "diff": "—"},
    "062": {"name": "tool_search",       "pf": "pocketflow-tool-search",        "tier": 5, "diff": "—"},
    "063": {"name": "tracing",           "pf": "pocketflow-tracing",            "tier": 5, "diff": "—"},
    "064": {"name": "visualization",     "pf": "pocketflow-visualization",      "tier": 5, "diff": "—"},
}

# Phase groups (exclude already-seeded by default)
_PHASES: dict[str, list[str]] = {
    "phase1": ["001", "002", "003", "006", "008"],
    "phase2": ["010", "011", "012", "013", "015", "016", "018", "019", "020", "021"],
    "phase3": ["030", "031", "033", "034"],
    "phase4": ["040", "041"],
    "phase5": ["050", "051", "052", "053", "054", "055", "056", "057",
               "058", "059", "060", "061", "062", "063", "064"],
    "seeded": ["004", "005", "014", "017", "032"],
}

# ── Helpers ──────────────────────────────────────────────────────────────────

def _resolve_recipes(recipe_spec: str, force: bool) -> list[str]:
    """Expand --recipe value to a sorted list of recipe keys."""
    spec = recipe_spec.strip().lower()
    if spec == "all":
        keys = list(RECIPES)
    elif spec in _PHASES:
        keys = _PHASES[spec]
    else:
        keys = [t.strip().zfill(3) for t in spec.split(",")]
        bad = [k for k in keys if k not in RECIPES]
        if bad:
            raise click.BadParameter(f"Unknown recipe(s): {bad}. "
                                     f"Use a 3-digit number or phase name.")
    if not force:
        keys = [k for k in keys if not RECIPES[k].get("seeded")]
    return sorted(set(keys))


def _run(cmd: list[str], logfile: Path) -> tuple[bool, float]:
    """Run a subprocess, tee stdout+stderr to logfile. Returns (ok, elapsed)."""
    t0 = time.monotonic()
    with logfile.open("a") as fh:
        fh.write(f"\n$ {' '.join(cmd)}\n")
        result = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT, text=True)
    elapsed = time.monotonic() - t0
    return result.returncode == 0, round(elapsed, 1)


def _model_tag(model_id: str) -> str:
    """Short tag for filenames: last component of model_id."""
    return model_id.split("/")[-1]


def _write_readme(dest: Path, num: str, meta: dict, adapter: str, model_id: str) -> None:
    name = meta["name"]
    pf   = meta["pf"]
    diff = meta["diff"]
    tag  = _model_tag(model_id)
    (dest / "README.md").write_text(f"""\
# {num} — {name.replace('_', ' ').title()}  *(migrated from PocketFlow)*

**Source:** [{pf}](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/{pf})
**Difficulty:** {diff}
**Migrated by:** migrate_pocketflow.py — adapter={adapter} model={model_id}

## Run

```bash
conda activate spl123
cd ~/projects/digital-duck/SPL.py

spl3 run cookbook-pocketflow/{num}_{name}/{name}.spl \\
    --tools cookbook/tools/ \\
    --llm {adapter}:{model_id}
```

## Migrate artifacts

```
migrate/
├── S1-{name}-{tag}-spec.md   # splc describe output
├── S2-{name}-{tag}.mmd       # text2mmd Mermaid diagram
└── S3-{name}-{tag}.spl       # raw mmd2spl output (= {name}.spl)
```

tools.spl (if present) — CREATE TOOL_API helpers ported from utils.py.
Recipes whose utils.py only wraps call_llm need no tools.spl.

> TODO: enrich this README — describe SPL pattern, key constructs, tool dependencies.
""", encoding="utf-8")


def _append_result(record: dict) -> None:
    _RESULTS.parent.mkdir(parents=True, exist_ok=True)
    with _RESULTS.open("a") as fh:
        fh.write(json.dumps(record) + "\n")


# ── CLI root ─────────────────────────────────────────────────────────────────

@click.group()
def cli():
    """PocketFlow → SPL migration tool."""


# ── migrate subcommand ────────────────────────────────────────────────────────

@cli.command()
@click.option("--recipe", "-r", default="phase1",
              help="Recipe(s): 3-digit number, comma-list, phase name "
                   "(phase1–phase5), or 'all'.  [default: phase1]")
@click.option("--adapter", "-a", default="claude_cli",
              show_default=True, help="LLM adapter (claude_cli, openrouter, ollama).")
@click.option("--model", "-m", "model_id", default="claude-sonnet-4-6",
              show_default=True, help="Model ID.")
@click.option("--steps", default="S1,S2,S3",
              show_default=True, help="Steps to run (comma-separated subset of S1,S2,S3).")
@click.option("--force", is_flag=True,
              help="Re-migrate already-seeded recipes (004,005,014,017,032).")
@click.option("--dry-run", "dry_run", is_flag=True,
              help="Print commands without executing.")
def migrate(recipe, adapter, model_id, steps, force, dry_run):
    """Run S1→S2→S3 migration pipeline for selected recipes."""
    try:
        keys = _resolve_recipes(recipe, force)
    except click.BadParameter as e:
        raise click.ClickException(str(e))

    run_steps = {s.strip().upper() for s in steps.split(",")}
    tag       = _model_tag(model_id)
    ts        = datetime.now().strftime("%Y%m%dT%H%M%S")

    click.echo(f"adapter : {adapter}")
    click.echo(f"model   : {model_id}")
    click.echo(f"steps   : {', '.join(sorted(run_steps))}")
    click.echo(f"recipes : {keys}")
    if dry_run:
        click.echo("(dry-run — no commands executed)")

    totals = {"pass": 0, "fail": 0, "skip": 0}

    for num in keys:
        meta  = RECIPES[num]
        name  = meta["name"]
        pf    = meta["pf"]
        src   = _PF_BASE / pf
        dest  = _HERE / f"{num}_{name}"
        out   = dest / "migrate"

        click.echo(f"\n── {num}_{name} " + "─" * max(0, 40 - len(num) - len(name)))

        if not src.is_dir():
            click.echo(f"  ✗ source not found: {src}")
            totals["skip"] += 1
            _append_result({"ts": ts, "recipe": f"{num}_{name}", "adapter": adapter,
                            "model": model_id, "overall": "skip", "reason": "source missing"})
            continue

        out.mkdir(parents=True, exist_ok=True)
        log_file = _HERE / "logs" / f"{num}_{name}-{tag}-{ts}.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        s1 = out / f"S1-{name}-{tag}-spec.md"
        s2 = out / f"S2-{name}-{tag}.mmd"
        s3 = out / f"S3-{name}-{tag}.spl"

        record: dict = {"ts": ts, "recipe": f"{num}_{name}", "adapter": adapter,
                        "model": model_id, "steps": {}, "overall": "pass"}
        ok = True

        # S1 ─ splc describe
        if "S1" in run_steps:
            cmd = ["spl3", "splc", "describe", str(src),
                   "--include-docs", "--adapter", adapter, "--model", model_id,
                   "-o", str(s1)]
            if dry_run:
                click.echo(f"  [S1] {' '.join(cmd)}")
            else:
                passed, elapsed = _run(cmd, log_file)
                record["steps"]["S1"] = {"status": "pass" if passed else "fail",
                                         "elapsed": elapsed}
                click.echo(f"  {'✓' if passed else '✗'} S1 ({elapsed}s)")
                ok = ok and passed

        # S2 ─ text2mmd
        if "S2" in run_steps and (ok or "S1" not in run_steps):
            src2 = s1 if s1.exists() else None
            if src2 is None:
                click.echo("  ✗ S2 skipped — S1 output missing")
                ok = False
            else:
                cmd = ["spl3", "text2mmd", str(src2),
                       "--adapter", adapter, "--model", model_id,
                       "--no-defaults", "-o", str(s2)]
                if dry_run:
                    click.echo(f"  [S2] {' '.join(cmd)}")
                else:
                    passed, elapsed = _run(cmd, log_file)
                    record["steps"]["S2"] = {"status": "pass" if passed else "fail",
                                             "elapsed": elapsed}
                    click.echo(f"  {'✓' if passed else '✗'} S2 ({elapsed}s)")
                    ok = ok and passed

        # S3 ─ mmd2spl
        if "S3" in run_steps and (ok or "S2" not in run_steps):
            src3 = s2 if s2.exists() else None
            if src3 is None:
                click.echo("  ✗ S3 skipped — S2 output missing")
                ok = False
            else:
                cmd = ["spl3", "mmd2spl", str(src3),
                       "--adapter", adapter, "--model", model_id,
                       "--validate", "-o", str(s3)]
                if dry_run:
                    click.echo(f"  [S3] {' '.join(cmd)}")
                else:
                    passed, elapsed = _run(cmd, log_file)
                    record["steps"]["S3"] = {"status": "pass" if passed else "fail",
                                             "elapsed": elapsed}
                    click.echo(f"  {'✓' if passed else '✗'} S3 ({elapsed}s)")
                    ok = ok and passed

        if not dry_run:
            # Promote canonical .spl if S3 succeeded
            if ok and s3.exists():
                canonical = dest / f"{name}.spl"
                canonical.write_bytes(s3.read_bytes())
                _write_readme(dest, num, meta, adapter, model_id)
                click.echo(f"  → promoted to {canonical.name}")
            record["overall"] = "pass" if ok else "fail"
            _append_result(record)

        totals["pass" if ok else "fail"] += 1

    # Summary
    click.echo(f"\n{'═'*48}")
    click.echo(f"  passed: {totals['pass']}  failed: {totals['fail']}  skipped: {totals['skip']}")
    if not dry_run:
        click.echo(f"  results → {_RESULTS}")
        click.echo(f"  logs    → {_HERE / 'logs'}/")


# ── validate subcommand ───────────────────────────────────────────────────────

@cli.command()
@click.option("--recipe", "-r", default="phase1",
              help="Same selector as migrate (phase name, number, list, 'all').")
def validate(recipe):
    """Run spl3 validate on migrated .spl files."""
    try:
        keys = _resolve_recipes(recipe, force=True)
    except click.BadParameter as e:
        raise click.ClickException(str(e))
    passed = failed = missing = 0

    for num in keys:
        meta = RECIPES[num]
        name = meta["name"]
        spl  = _HERE / f"{num}_{name}" / f"{name}.spl"

        if not spl.exists():
            click.echo(f"  — {num}_{name}: not migrated yet")
            missing += 1
            continue

        result = subprocess.run(
            ["spl3", "validate", str(spl)],
            capture_output=True, text=True,
        )
        ok = result.returncode == 0
        status = "✓" if ok else "✗"
        click.echo(f"  {status} {num}_{name}")
        if not ok:
            for line in (result.stdout + result.stderr).splitlines():
                click.echo(f"      {line}")
            failed += 1
        else:
            passed += 1

    click.echo(f"\n  valid: {passed}  invalid: {failed}  missing: {missing}")


# ── report subcommand ─────────────────────────────────────────────────────────

@cli.command()
@click.option("--phase", default=None,
              help="Filter to a phase (phase1–phase5).  Default: all results.")
def report(phase):
    """Print model × recipe migration result table from logs/results.jsonl."""
    if not _RESULTS.exists():
        click.echo("No results yet — run `migrate` first.")
        return

    records: list[dict] = []
    with _RESULTS.open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    if phase:
        allowed = set(_PHASES.get(phase, []))
        records = [r for r in records if r["recipe"].split("_")[0] in allowed]

    if not records:
        click.echo("No matching records.")
        return

    # Build: recipe → model_tag → latest overall status
    table: dict[str, dict[str, str]] = {}
    models: set[str] = set()
    for r in records:
        recipe = r["recipe"]
        mtag   = f"{r['adapter']}/{r['model'].split('/')[-1]}"
        status = r.get("overall", "?")
        steps  = r.get("steps", {})
        detail = "".join(
            f"S{i}{'✓' if steps.get(f'S{i}', {}).get('status') == 'pass' else '✗'}"
            for i in (1, 2, 3) if f"S{i}" in steps
        )
        cell = f"{'✓' if status == 'pass' else '✗'} {detail}"
        table.setdefault(recipe, {})[mtag] = cell
        models.add(mtag)

    model_cols = sorted(models)
    col_w      = max(20, *(len(m) for m in model_cols)) + 2
    row_w      = 26

    # Header
    header = f"{'Recipe':<{row_w}}" + "".join(f"{m:<{col_w}}" for m in model_cols)
    click.echo("\n" + header)
    click.echo("─" * len(header))

    for recipe in sorted(table):
        row = f"{recipe:<{row_w}}"
        for m in model_cols:
            row += f"{table[recipe].get(m, '—'):<{col_w}}"
        click.echo(row)

    click.echo(f"\n{len(table)} recipe(s)  ·  {len(model_cols)} model(s)")
    click.echo(f"Source: {_RESULTS}\n")


# ── list subcommand ───────────────────────────────────────────────────────────

@cli.command("list")
@click.option("--phase", default=None, help="Filter by phase (phase1–phase5).")
@click.option("--tier",  default=None, type=int, help="Filter by tier (1–5).")
def list_recipes(phase, tier):
    """List all recipes in the registry."""
    keys = _PHASES.get(phase, list(RECIPES)) if phase else list(RECIPES)
    click.echo(f"\n{'#':<6}{'Name':<22}{'PocketFlow source':<36}{'Tier':<7}{'Diff':<8}{'Seeded'}")
    click.echo("─" * 85)
    for k in sorted(keys):
        m = RECIPES[k]
        if tier and m["tier"] != tier:
            continue
        seeded = "✓" if m.get("seeded") else ""
        click.echo(f"{k:<6}{m['name']:<22}{m['pf']:<36}{m['tier']:<7}{m['diff']:<8}{seeded}")
    click.echo()


if __name__ == "__main__":
    cli()
