#!/usr/bin/env python3
"""run_all.py — SPL Cookbook batch runner (unified SPL 3.0 + SPL 3.0).

Recipes are defined in cookbook/cookbook_catalog.json. Edit that file to add,
remove, or update recipes without touching Python code.

Usage
-----
  # List / inspect
  python cookbook/run_all.py --list
  python cookbook/run_all.py --list --category agentic
  python cookbook/run_all.py --list --tier 1
  python cookbook/run_all.py --catalog
  python cookbook/run_all.py --catalog --status new
  python cookbook/run_all.py --check            # verify env vars + Ollama models
  python cookbook/run_all.py --check --tier 2

  # Run
  python cookbook/run_all.py                                    # all active recipes
  python cookbook/run_all.py --adapter ollama --model gemma3
  python cookbook/run_all.py --adapter momagrid --workers 5
  python cookbook/run_all.py --ids 04,08,13
  python cookbook/run_all.py --ids 50-55
  python cookbook/run_all.py --tier 1                           # Ollama-only recipes
  python cookbook/run_all.py --tier 1,2
  python cookbook/run_all.py --category multimodal
  python cookbook/run_all.py --all                              # include inactive

  # Alternate catalog (Go / TypeScript runtime)
  python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog-go.json
  python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog-ts.json

  # Save output
  python cookbook/run_all.py 2>&1 | tee cookbook/out/run_all_$(date +%Y%m%d_%H%M%S).md

Tier legend
-----------
  1 = Ollama only (no API keys required)
  2 = OpenAI key
  3 = OpenRouter key
  4 = OpenAI + OpenRouter + Ollama

conda activate spl3
cd ~/projects/digital-duck/SPL
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import shutil
import click

COOKBOOK_DIR = Path(__file__).resolve().parent
REPO_ROOT    = COOKBOOK_DIR.parent

# Resolve SPL binary paths relative to the active Python interpreter so that
# subprocess.Popen finds them even when the conda env bin isn't in shell PATH.
_ENV_BIN = Path(sys.executable).parent

def _resolve_bin(name: str) -> str:
    """Return full path to a binary, preferring the active env's bin dir.

    For spl3: always resolved as [sys.executable, -m, spl3.cli] to guarantee
    the right interpreter is used regardless of shell PATH.
    For spl-go / spl-ts: tries env bin dir then shutil.which.
    """
    if name == "spl3":
        return name  # sentinel; caller uses _spl3_cmd() instead
    candidate = _ENV_BIN / name
    if candidate.exists():
        return str(candidate)
    found = shutil.which(name)
    return found if found else name

def _spl3_cmd(rest: list[str]) -> list[str]:
    """Build a guaranteed-working spl3 invocation using sys.executable."""
    return [sys.executable, "-m", "spl3.cli"] + rest

STATUS_APPROVED = "approved"
STATUS_NEW      = "new"
STATUS_WIP      = "wip"
STATUS_DISABLED = "disabled"
STATUS_REJECTED = "rejected"

MARKERS = {
    "active":         "✅",
    STATUS_NEW:       "🆕",
    STATUS_WIP:       "🔧",
    STATUS_DISABLED:  "⏸ ",
    STATUS_REJECTED:  "❌",
}

TIER_LABELS = {
    1: "Ollama only",
    2: "OpenAI key",
    3: "OpenRouter key",
    4: "OpenAI + OpenRouter + Ollama",
}


# ── Catalog ───────────────────────────────────────────────────────────────────

def load_catalog(catalog_file: str = "") -> list[dict]:
    path = Path(catalog_file) if catalog_file else COOKBOOK_DIR / "cookbook_catalog.json"
    if catalog_file and not path.is_absolute():
        path = Path.cwd() / path
    with open(path) as f:
        data = json.load(f)
    return data["recipes"]


def parse_id_filter(ids: str) -> set[str]:
    """Parse comma-separated IDs / ranges like '1-4,10' into zero-padded strings."""
    result: set[str] = set()
    for part in ids.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, hi = part.split("-", 1)
            for n in range(int(lo.strip()), int(hi.strip()) + 1):
                result.add(f"{n:02d}")
        else:
            result.add(f"{int(part):02d}" if part.isdigit() else part)
    return result


def parse_tier_filter(tiers: str) -> set[int]:
    result: set[int] = set()
    for part in tiers.split(","):
        part = part.strip()
        if part:
            result.add(int(part))
    return result


def apply_filters(
    recipes: list[dict],
    category: str,
    status: str,
    tiers: set[int],
    ids: set[str],
    include_inactive: bool,
) -> list[dict]:
    out = []
    for r in recipes:
        if ids and r["id"] not in ids:
            continue
        if not include_inactive and not r.get("is_active"):
            continue
        if category and r.get("category") != category:
            continue
        if status and r.get("approval_status") != status:
            continue
        if tiers and r.get("tier") not in tiers:
            continue
        out.append(r)
    return out


def status_marker(r: dict) -> str:
    if r.get("is_active"):
        return MARKERS["active"]
    return MARKERS.get(r.get("approval_status", ""), "  ")


# ── Prerequisite check ────────────────────────────────────────────────────────

def check_prerequisites(recipes: list[dict]) -> tuple[bool, list[str]]:
    """Check env vars and Ollama models declared in recipe `requires` fields."""
    issues: list[str] = []
    needed_envs:   set[str] = set()
    needed_models: set[str] = set()

    for r in recipes:
        for req in r.get("requires", []):
            if req.startswith("env:"):
                needed_envs.add(req[4:])
            elif req.startswith("ollama:"):
                needed_models.add(req[7:])

    for var in sorted(needed_envs):
        if not os.environ.get(var):
            issues.append(f"  ✗  env {var} not set")
        else:
            print(f"  ✓  env {var} SET")

    if needed_models:
        try:
            import httpx
            resp = httpx.get("http://localhost:11434/api/tags", timeout=3)
            available = {m["name"] for m in resp.json().get("models", [])}
            for model in sorted(needed_models):
                if model in available:
                    print(f"  ✓  ollama {model} available")
                else:
                    base = model.split(":")[0]
                    matches = [m for m in available if m.startswith(base)]
                    if matches:
                        print(f"  ~  ollama {model} → using {matches[0]}")
                    else:
                        issues.append(f"  ✗  ollama {model} not pulled  (ollama pull {model})")
        except Exception:
            issues.append("  ✗  Ollama not reachable (ollama serve)")

    return len(issues) == 0, issues


# ── Recipe execution ──────────────────────────────────────────────────────────

def apply_overrides(cmd_args: list[str], adapter: str, model: str) -> list[str]:
    """Inject --adapter, --model, and --param overrides into an spl3 run command."""
    if not cmd_args:
        return cmd_args

    if cmd_args[0] in ("spl", "spl3"):
        result = ["spl3"] + cmd_args[1:]
    elif cmd_args[0] in ("spl-go", "spl-ts"):
        result = [_resolve_bin(cmd_args[0])] + cmd_args[1:]
    else:
        result = list(cmd_args)

    # spl3 requires --param key=value; catalog stores bare key=value — inject prefix.
    # Only applies to spl3/spl commands (not bash/python runners).
    import re
    _param_re = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*=')
    if Path(result[0]).name in ("spl3", "spl-go", "spl-ts"):
        expanded: list[str] = []
        known_flags = {"--adapter", "--model", "--llm", "--tools", "--hub", "--log-prompts",
                       "--claude-allowed-tools", "--spl-bin", "-a", "-m", "-p"}
        i = 0
        while i < len(result):
            tok = result[i]
            if tok in known_flags:
                expanded.append(tok)
                if i + 1 < len(result):
                    expanded.append(result[i + 1])
                    i += 2
                else:
                    i += 1
            elif tok == "--param":
                expanded.append(tok)
                if i + 1 < len(result):
                    expanded.append(result[i + 1])
                    i += 2
                else:
                    i += 1
                continue
            elif not tok.startswith("-") and _param_re.match(tok):
                expanded.append("--param")
                expanded.append(tok)
                i += 1
            else:
                expanded.append(tok)
                i += 1
        result = expanded

    # Only inject --adapter / --model for subcommands that accept them (run, execute).
    # Commands like validate, splc compile don't support these flags.
    _has_run_subcmd = any(tok in ("run", "execute") for tok in result)

    if adapter and _has_run_subcmd and "--llm" not in result:
        if "--adapter" in result:
            result[result.index("--adapter") + 1] = adapter
        else:
            for i in range(len(result)):
                if result[i].endswith(".spl"):
                    result.insert(i, "--adapter")
                    result.insert(i + 1, adapter)
                    break

    is_spl_cmd = Path(result[0]).name in ("spl3", "spl-go", "spl-ts")
    if model and is_spl_cmd and _has_run_subcmd and "--llm" not in result:
        found = False
        for i in range(len(result)):
            if result[i] == "--model":
                result[i + 1] = model
                found = True
                break
        if not found:
            for i in range(len(result)):
                if result[i] in ("run", "execute"):
                    result.insert(i + 1, "--model")
                    result.insert(i + 2, model)
                    found = True
                    break
        if not found:
            result.extend(["--model", model])

    return result


def _to_exec(cmd_args: list[str]) -> list[str]:
    """Convert display cmd_args to an executable command.

    spl3 → [sys.executable, -m, spl3.cli, ...] so the right interpreter is
    used regardless of whether the conda env is in the shell PATH.
    """
    if cmd_args and Path(cmd_args[0]).name == "spl3":
        return _spl3_cmd(cmd_args[1:])
    return cmd_args


def run_recipe_sequential(cmd_args: list[str], log_path: Path) -> tuple[bool, float]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    start = datetime.now()
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO_ROOT)
        with open(log_path, "w") as log_file:
            process = subprocess.Popen(
                _to_exec(cmd_args), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, cwd=str(REPO_ROOT), env=env,
            )
            state = "normal"
            for line in (process.stdout or []):
                log_file.write(line)
                s = line.rstrip("\n")
                if state == "in_fence":
                    sys.stdout.write(s + "\n")
                    if s.strip() == "```":
                        state = "normal"
                else:
                    if s.strip().startswith("```") and s.strip() != "```":
                        sys.stdout.write(s + "\n")
                        state = "in_fence"
                    else:
                        sys.stdout.write(f"     | {s}\n")
            process.wait()
            ok = process.returncode == 0
    except Exception as e:
        print(f"     | ERROR: {e}")
        ok = False
    return ok, (datetime.now() - start).total_seconds()


def run_recipe_parallel(recipe: dict, cmd_args: list[str], log_path: Path) -> dict:
    rid, name = recipe["id"], recipe["name"]
    log_path.parent.mkdir(parents=True, exist_ok=True)
    start = datetime.now()
    print(f"[{rid}] {name}  →  started")
    sys.stdout.flush()
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO_ROOT)
        with open(log_path, "w") as log_file:
            proc = subprocess.Popen(
                _to_exec(cmd_args), stdout=log_file, stderr=subprocess.STDOUT,
                text=True, cwd=str(REPO_ROOT), env=env,
            )
            proc.wait()
        ok = proc.returncode == 0
    except Exception as e:
        print(f"[{rid}] ERROR: {e}")
        ok = False
    elapsed = (datetime.now() - start).total_seconds()
    print(f"[{rid}] {name}  →  {'SUCCESS' if ok else 'FAILED'}  ({elapsed:.1f}s)")
    sys.stdout.flush()
    return {"id": rid, "name": name, "ok": ok, "elapsed": elapsed}


# ── Display ───────────────────────────────────────────────────────────────────

def print_list(recipes: list[dict]) -> None:
    print(f"\n{'ID':<6} {'':2} {'Name':<28} {'Tier':<6} {'Category':<14} {'Status':<12} Description")
    print("-" * 110)
    for r in recipes:
        tier = str(r.get("tier", "-"))
        print(
            f"{r['id']:<6} {status_marker(r)} {r['name']:<28} {tier:<6} "
            f"{r.get('category',''):<14} {r.get('approval_status',''):<12} "
            f"{r.get('description','')}"
        )


def print_catalog(recipes: list[dict]) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    counts: dict[str, int] = {}
    for r in recipes:
        if r.get("is_active"):
            counts["active"] = counts.get("active", 0) + 1
        s = r.get("approval_status", "")
        counts[s] = counts.get(s, 0) + 1

    print(f"=== SPL Cookbook Catalog — {now} ===")
    print(
        f"    Total: {len(recipes)} recipes  |  {counts.get('active', 0)} active  |  "
        f"{counts.get(STATUS_NEW, 0)} new  |  {counts.get(STATUS_WIP, 0)} wip  |  "
        f"{counts.get(STATUS_DISABLED, 0)} disabled\n"
    )
    print(f"{'ID':<6} {'':2} {'Name':<28} {'Tier':<5} {'Category':<14} {'Status':<12} Description")
    print("-" * 115)
    for r in recipes:
        tier = str(r.get("tier", "-"))
        print(
            f"{r['id']:<6} {status_marker(r)} {r['name']:<28} {tier:<5} "
            f"{r.get('category',''):<14} {r.get('approval_status',''):<12} "
            f"{r.get('description','')}"
        )
    print()
    print("Markers: ✅ active  🆕 new  🔧 wip  ⏸  disabled  ❌ rejected")
    cat_counts: dict[str, int] = {}
    for r in recipes:
        c = r.get("category", "")
        cat_counts[c] = cat_counts.get(c, 0) + 1
    print(f"Categories: {'  '.join(f'{c}({n})' for c, n in sorted(cat_counts.items()))}\n")


def print_summary(results: list[dict], start_all: datetime) -> None:
    total_elapsed = (datetime.now() - start_all).total_seconds()
    passed = sum(1 for r in results if r["ok"])
    print(f"\n=== Summary: {passed}/{len(results)} Success  (total {total_elapsed:.1f}s) ===\n")
    print(f"{'ID':<6} {'Recipe':<28} {'Status':<8} {'Elapsed':>8}")
    print("-" * 56)
    for r in results:
        print(f"{r['id']:<6} {r['name']:<28} {'OK' if r['ok'] else 'FAILED':<8} {r['elapsed']:>7.1f}s")
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

@click.command()
@click.option("--adapter",      "-a", default="ollama", show_default=True,
              help="Override LLM adapter for all recipes (e.g. ollama, momagrid)")
@click.option("--model",        "-m", default="gemma3", show_default=True,
              help="Override model for all recipes")
@click.option("--ids",          default="", help="Comma-separated recipe IDs or ranges (e.g. '04,08,50-55')")
@click.option("--tier",         default="", help="Comma-separated tier numbers (e.g. '1,2')")
@click.option("--workers",      "-w", default=0, show_default=True, type=int,
              help="Parallel workers (0 = sequential, >1 = parallel)")
@click.option("--category",     default="", help="Only run recipes in this category")
@click.option("--status",       default="", help="Only run recipes with this approval status")
@click.option("--all",          "include_all", is_flag=True, help="Include inactive recipes")
@click.option("--list",         "list_recipes", is_flag=True, help="Print recipe list and exit")
@click.option("--catalog",      is_flag=True, help="Print full catalog table and exit")
@click.option("--check",        is_flag=True, help="Verify env vars + Ollama models and exit")
@click.option("--catalog-file", "catalog_file", default="",
              help="Path to alternate catalog JSON (e.g. cookbook/cookbook_catalog-go.json)")
def main(adapter, model, ids, tier, workers, category, status, include_all,
         list_recipes, catalog, check, catalog_file) -> None:
    """SPL Cookbook batch runner (SPL 3.0 + SPL 3.0)."""
    recipes  = load_catalog(catalog_file)
    id_set   = parse_id_filter(ids)   if ids   else set()
    tier_set = parse_tier_filter(tier) if tier else set()

    filtered = apply_filters(
        recipes,
        category=category,
        status=status,
        tiers=tier_set,
        ids=id_set,
        include_inactive=include_all or bool(id_set) or bool(tier_set),
    )

    if catalog:
        print_catalog(filtered)
        return

    if list_recipes:
        print_list(filtered)
        print(f"\n{len(filtered)} recipe(s) shown")
        return

    if check:
        print(f"\nChecking prerequisites for {len(filtered)} recipe(s)...\n")
        ok, issues = check_prerequisites(filtered)
        if issues:
            print("\nIssues found:")
            for issue in issues:
                print(issue)
            sys.exit(1)
        else:
            print("\nAll prerequisites satisfied.")
        return

    if not filtered:
        print("No recipes match the filter. Use --all to include inactive recipes.")
        return

    use_parallel = workers > 1 or adapter == "momagrid"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    start_all = datetime.now()

    print(f"=== SPL Cookbook Batch Run — {start_all.strftime('%Y-%m-%d %H:%M:%S')} ===")
    print(f"    Adapter : {adapter}  |  Model : {model}")
    if use_parallel:
        print(f"    Mode    : parallel  (workers={workers or len(filtered)})")
    print()

    active: list[tuple[dict, list[str], Path]] = []
    for r in filtered:
        if not id_set and not r.get("is_active"):
            print(f"[{r['id']}] {r['name']}  (skipping — {r.get('approval_status','').upper()})")
            continue
        cmd_args = apply_overrides(r["args"], adapter, model)
        log_path = COOKBOOK_DIR / r["dir"] / "logs" / f"{r['log']}_{ts}.md"
        active.append((r, cmd_args, log_path))

    if not active:
        print("No active recipes to run.")
        return

    results: list[dict] = []

    if use_parallel:
        n_workers = workers or len(active)
        print(f"Submitting {len(active)} recipe(s) with {n_workers} parallel worker(s)...\n")
        with ThreadPoolExecutor(max_workers=n_workers) as pool:
            futures = {
                pool.submit(run_recipe_parallel, r, cmd_args, log_path): r
                for r, cmd_args, log_path in active
            }
            for f in as_completed(futures):
                results.append(f.result())
        results.sort(key=lambda x: x["id"])
    else:
        for r, cmd_args, log_path in active:
            tier_label = TIER_LABELS.get(r.get("tier", 0), "")
            suffix = f"  ({tier_label})" if tier_label else ""
            print(f"[{r['id']}] {r['name']}{suffix}")
            print(f"     cmd : {' '.join(cmd_args)}")
            print(f"     log : {log_path}")
            ok, elapsed = run_recipe_sequential(cmd_args, log_path)
            print(f"     result: {'SUCCESS' if ok else 'FAILED'}  ({elapsed:.1f}s)\n")
            results.append({"id": r["id"], "name": r["name"], "ok": ok, "elapsed": elapsed})

    print_summary(results, start_all)


if __name__ == "__main__":
    main()
