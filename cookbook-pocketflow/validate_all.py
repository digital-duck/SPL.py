#!/usr/bin/env python3
"""
Batch validator for the PocketFlow migration cookbook.

Two modes:
  --parse-only   Fast syntax + semantic lint via `spl3 validate` (no LLM, default)
  --run          Full execution via `spl3 run` (requires adapter + model)

Examples:
  python cookbook-pocketflow/validate_all.py
  python cookbook-pocketflow/validate_all.py --ids 001,004,032
  python cookbook-pocketflow/validate_all.py --category agentic
  python cookbook-pocketflow/validate_all.py --run --adapter ollama --model gemma3
  python cookbook-pocketflow/validate_all.py --run --ids 001-010 --workers 4
"""

import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import click

CATALOG_FILE = os.path.join(os.path.dirname(__file__), "cookbook_catalog.json")
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load_catalog(catalog_file: str) -> list[dict]:
    with open(catalog_file) as f:
        data = json.load(f)
    return data["recipes"] if isinstance(data, dict) else data


def parse_id_filter(ids_str: str) -> set[str]:
    """Parse '001,004,010-015' into a set of zero-padded IDs."""
    result = set()
    for part in ids_str.split(","):
        part = part.strip()
        m = re.match(r"^(\d+)-(\d+)$", part)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
            result.update(f"{i:03d}" for i in range(lo, hi + 1))
        elif part:
            result.add(f"{int(part):03d}")
    return result


def apply_filters(
    recipes: list[dict],
    ids: str | None,
    category: str | None,
    active_only: bool,
) -> list[dict]:
    if ids:
        allowed = parse_id_filter(ids)
        recipes = [r for r in recipes if r["id"] in allowed]
    if category:
        recipes = [r for r in recipes if r.get("category") == category]
    if active_only:
        recipes = [r for r in recipes if r.get("is_active", False)]
    return recipes


def build_validate_cmd(recipe: dict) -> list[str]:
    """Build spl3 validate command for a recipe."""
    spl_path = recipe["args"][2]  # args[2] is always the .spl path
    return [sys.executable, "-m", "spl3.cli", "validate", spl_path]


def build_run_cmd(recipe: dict, adapter: str, model: str) -> list[str]:
    """Build spl3 run command with adapter/model override."""
    args = list(recipe["args"])
    # Replace --llm value with override
    if "--llm" in args:
        idx = args.index("--llm")
        args[idx + 1] = f"{adapter}:{model}"
    else:
        args += ["--llm", f"{adapter}:{model}"]
    # Replace spl3 with sys.executable -m spl3.cli
    args = [sys.executable, "-m", "spl3.cli"] + args[1:]
    return args


def run_recipe(recipe: dict, cmd: list[str], timeout: int = 120) -> dict:
    """Execute one recipe; return result dict."""
    start = time.time()
    result = {
        "id": recipe["id"],
        "name": recipe["name"],
        "cmd": " ".join(cmd[3:]),  # strip python -m spl3.cli for display
        "status": "unknown",
        "elapsed": 0.0,
        "stdout": "",
        "stderr": "",
    }
    try:
        proc = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        result["elapsed"] = round(time.time() - start, 1)
        result["stdout"] = proc.stdout[-2000:] if proc.stdout else ""
        result["stderr"] = proc.stderr[-2000:] if proc.stderr else ""
        result["returncode"] = proc.returncode
        if proc.returncode == 0:
            result["status"] = "PASS"
        else:
            result["status"] = "FAIL"
    except subprocess.TimeoutExpired:
        result["status"] = "TIMEOUT"
        result["elapsed"] = timeout
    except Exception as e:
        result["status"] = "ERROR"
        result["stderr"] = str(e)
    return result


def print_result(r: dict, verbose: bool) -> None:
    icon = {"PASS": "✓", "FAIL": "✗", "TIMEOUT": "⏱", "ERROR": "⚠", "SKIP": "—"}.get(r["status"], "?")
    click.echo(f"  {icon} {r['id']} {r['name']:30s}  {r['status']:7s}  {r['elapsed']:.1f}s")
    if verbose and r["status"] != "PASS":
        if r.get("stderr"):
            click.echo(f"      stderr: {r['stderr'][:300]}")
        if r.get("stdout"):
            click.echo(f"      stdout: {r['stdout'][:300]}")


def print_summary(results: list[dict]) -> None:
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = [r for r in results if r["status"] == "FAIL"]
    timeouts = [r for r in results if r["status"] == "TIMEOUT"]
    errors = [r for r in results if r["status"] == "ERROR"]
    total = len(results)

    click.echo("\n" + "=" * 60)
    click.echo(f"Summary: {passed}/{total} passed")
    if failed:
        click.echo(f"  FAIL ({len(failed)}): " + ", ".join(r["id"] for r in failed))
    if timeouts:
        click.echo(f"  TIMEOUT ({len(timeouts)}): " + ", ".join(r["id"] for r in timeouts))
    if errors:
        click.echo(f"  ERROR ({len(errors)}): " + ", ".join(r["id"] for r in errors))
    click.echo("=" * 60)


def write_log(results: list[dict], mode: str) -> str:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"validate-{mode}-{ts}.md")
    lines = [f"# PocketFlow Validation — {mode} — {ts}\n"]
    for r in results:
        lines.append(f"## {r['id']} {r['name']} — {r['status']} ({r['elapsed']:.1f}s)")
        if r.get("stderr"):
            lines.append(f"```\n{r['stderr'][:500]}\n```")
        lines.append("")
    with open(log_path, "w") as f:
        f.write("\n".join(lines))
    return log_path


@click.command()
@click.option("--run", "mode", flag_value="run", help="Full spl3 run (requires adapter + model)")
@click.option("--parse-only", "mode", flag_value="parse", default=True, help="Parse-only validate (default, no LLM)")
@click.option("--ids", default=None, help="Comma-separated IDs or ranges e.g. 001,004,010-015")
@click.option("--category", default=None, help="Filter by category (basics, agentic, ...)")
@click.option("--active-only", is_flag=True, default=False, help="Only run is_active=true recipes")
@click.option("--adapter", default="ollama", show_default=True, help="Adapter for --run mode")
@click.option("--model", default="gemma3", show_default=True, help="Model for --run mode")
@click.option("--workers", default=1, show_default=True, help="Parallel workers (use >1 carefully with --run)")
@click.option("--timeout", default=120, show_default=True, help="Per-recipe timeout in seconds")
@click.option("--catalog-file", default=CATALOG_FILE, help="Path to cookbook_catalog.json")
@click.option("--list", "do_list", is_flag=True, default=False, help="List matching recipes and exit")
@click.option("-v", "--verbose", is_flag=True, default=False, help="Show stderr/stdout on failure")
@click.option("--log", "write_log_flag", is_flag=True, default=False, help="Write results to logs/ directory")
def main(
    mode, ids, category, active_only, adapter, model, workers,
    timeout, catalog_file, do_list, verbose, write_log_flag,
):
    recipes = load_catalog(catalog_file)
    recipes = apply_filters(recipes, ids, category, active_only)

    if not recipes:
        click.echo("No recipes match the given filters.")
        sys.exit(0)

    if do_list:
        click.echo(f"{'ID':6} {'Name':30} {'Category':20} {'Active'}")
        click.echo("-" * 70)
        for r in recipes:
            active = "yes" if r.get("is_active") else "no"
            click.echo(f"{r['id']:6} {r['name']:30} {r.get('category',''):20} {active}")
        click.echo(f"\n{len(recipes)} recipe(s)")
        return

    click.echo(f"PocketFlow validation — mode={mode}, {len(recipes)} recipe(s)")
    if mode == "run":
        click.echo(f"  adapter={adapter}  model={model}  workers={workers}  timeout={timeout}s")
    click.echo()

    results = []

    def process(recipe: dict) -> dict:
        if mode == "parse":
            cmd = build_validate_cmd(recipe)
        else:
            cmd = build_run_cmd(recipe, adapter, model)
        return run_recipe(recipe, cmd, timeout=timeout)

    if workers > 1:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(process, r): r for r in recipes}
            for fut in as_completed(futures):
                r = fut.result()
                results.append(r)
                print_result(r, verbose)
    else:
        for recipe in recipes:
            r = process(recipe)
            results.append(r)
            print_result(r, verbose)

    results.sort(key=lambda r: r["id"])
    print_summary(results)

    if write_log_flag:
        log_path = write_log(results, mode)
        click.echo(f"Log written: {log_path}")

    failed = sum(1 for r in results if r["status"] != "PASS")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
