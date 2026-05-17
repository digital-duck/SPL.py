"""spl2spec_batch.py — Generate functional specs from SPL cookbook recipes.

Calls `spl3 splc describe <recipe.spl> --spec-dir <recipe_dir>/spec/` for each
selected recipe and saves the output as a Markdown spec file under:

    cookbook/<NN_recipe_name>/spec/<stem>-<adapter>-<model>-spec.md

Usage examples:
    # Single recipe
    python cookbook/spl2spec_batch.py --ids 05

    # Multiple recipes
    python cookbook/spl2spec_batch.py --ids 05,09,16

    # All approved/new recipes
    python cookbook/spl2spec_batch.py --all

    # Different adapter / model
    python cookbook/spl2spec_batch.py --all --adapter openai --model gpt-4o

    # Skip already-generated specs
    python cookbook/spl2spec_batch.py --all --no-overwrite

    # Dry-run (print what would be done, no LLM calls)
    python cookbook/spl2spec_batch.py --ids 05 --dry-run
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import click


# ── Helpers ───────────────────────────────────────────────────────────────────

def _find_spl(recipe_dir: Path) -> Path | None:
    """Return the primary .spl file in a recipe directory.

    Preference order:
    1. <dir_name_without_NN_prefix>.spl  (e.g. 05_self_refine → self_refine.spl)
    2. First .spl alphabetically
    """
    dir_stem = recipe_dir.name
    parts = dir_stem.split("_", 1)
    canonical = (parts[1] if len(parts) == 2 and parts[0].isdigit() else dir_stem) + ".spl"
    candidate = recipe_dir / canonical
    if candidate.exists():
        return candidate
    spls = sorted(recipe_dir.glob("*.spl"))
    return spls[0] if spls else None


def _load_catalog(catalog_path: Path) -> list[dict]:
    with catalog_path.open() as f:
        data = json.load(f)
    return data["recipes"]


def _filter_recipes(recipes: list[dict], ids: list[str] | None) -> list[dict]:
    if not ids:
        return [
            r for r in recipes
            if r.get("approval_status") in ("approved", "new")
            and r.get("args", [""])[0] == "spl3"
        ]
    id_set = {i.strip() for i in ids}
    return [r for r in recipes if r["id"] in id_set]


def _spec_exists(spec_dir: Path, spl_stem: str, adapter: str, model: str | None) -> bool:
    """Check if a spec file already exists for this adapter/model combo."""
    model_slug = (model or "default").lower().replace(" ", "_").replace("/", "_").replace(":", "-")
    pattern = f"{spl_stem}-{adapter}-{model_slug}-spec.md"
    return (spec_dir / pattern).exists()


# ── CLI ───────────────────────────────────────────────────────────────────────

@click.command()
@click.option(
    "--catalog",
    default="cookbook/cookbook_catalog.json",
    show_default=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Path to cookbook_catalog.json.",
)
@click.option(
    "--ids",
    default=None,
    help="Comma-separated recipe IDs (e.g. '05,09,16'). Omit to use --all.",
)
@click.option(
    "--all", "run_all",
    is_flag=True,
    default=False,
    help="Process all approved/new spl3-run recipes in the catalog.",
)
@click.option(
    "--adapter",
    default="ollama",
    show_default=True,
    help="LLM adapter for spec generation.",
)
@click.option(
    "--model",
    default=None,
    metavar="MODEL",
    help="Model override (adapter default if omitted).",
)
@click.option(
    "--include-docs",
    is_flag=True,
    default=False,
    help="Also feed README.md (if present) as intent context.",
)
@click.option(
    "--overwrite/--no-overwrite",
    default=True,
    show_default=True,
    help="Overwrite existing spec files (default: overwrite).",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Print what would be done; skip LLM calls.",
)
def main(
    catalog: str,
    ids: str | None,
    run_all: bool,
    adapter: str,
    model: str | None,
    include_docs: bool,
    overwrite: bool,
    dry_run: bool,
) -> None:
    """Generate functional specs from SPL cookbook recipes via `spl3 splc describe`."""
    if not ids and not run_all:
        click.echo("Specify --ids <id,...> or --all.", err=True)
        sys.exit(1)

    catalog_path = Path(catalog)
    cookbook_root = catalog_path.parent

    recipes = _load_catalog(catalog_path)
    id_list = [i.strip() for i in ids.split(",")] if ids else None
    selected = _filter_recipes(recipes, id_list)

    if not selected:
        click.echo("No matching recipes found.", err=True)
        sys.exit(1)

    click.echo(f"Generating specs for {len(selected)} recipe(s)  "
               f"[adapter={adapter}  model={model or 'default'}]")
    click.echo()

    results: list[dict] = []

    for recipe in selected:
        rid = recipe["id"]
        name = recipe["name"]
        rdir = cookbook_root / recipe["dir"]

        spl_path = _find_spl(rdir)
        if spl_path is None:
            results.append({"id": rid, "name": name, "status": "SKIP (no .spl)", "path": ""})
            click.echo(f"[{rid}] SKIP  {name}  — no .spl file found in {rdir.name}/")
            continue

        spec_dir = rdir / "spec"

        if dry_run:
            click.echo(f"[{rid}] DRY-RUN  {name}")
            click.echo(f"      spl: {spl_path}")
            click.echo(f"      out: {spec_dir}/")
            results.append({"id": rid, "name": name, "status": "DRY-RUN", "path": str(spec_dir)})
            continue

        if not overwrite and _spec_exists(spec_dir, spl_path.stem, adapter, model):
            results.append({"id": rid, "name": name, "status": "SKIP (exists)", "path": str(spec_dir)})
            click.echo(f"[{rid}] SKIP  {name}  — spec already exists")
            continue

        spec_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            sys.executable, "-m", "spl3.cli",
            "splc", "describe", str(spl_path),
            "--spec-dir", str(spec_dir),
            "--adapter", adapter,
        ]
        if model:
            cmd += ["--model", model]
        if include_docs:
            cmd.append("--include-docs")

        click.echo(f"[{rid}] {name}  ({spl_path.name}) ...")
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode == 0:
                # Find the written spec file to report its path
                spec_files = sorted(spec_dir.glob(f"{spl_path.stem}-*-spec.md"))
                spec_path = str(spec_files[-1]) if spec_files else str(spec_dir)
                results.append({"id": rid, "name": name, "status": "OK", "path": spec_path})
                if proc.stdout.strip():
                    for line in proc.stdout.strip().splitlines():
                        click.echo(f"      {line}")
            else:
                err = (proc.stderr or proc.stdout).strip().splitlines()
                err_msg = err[0] if err else "unknown error"
                results.append({"id": rid, "name": name, "status": f"ERROR: {err_msg}", "path": ""})
                click.echo(f"      ERROR: {err_msg}", err=True)
        except Exception as exc:
            results.append({"id": rid, "name": name, "status": f"ERROR: {exc}", "path": ""})
            click.echo(f"      ERROR: {exc}", err=True)

    # ── Summary table ─────────────────────────────────────────────────────────
    if not dry_run:
        click.echo()
        click.echo(f"{'ID':<5}  {'Status':<22}  {'Name':<35}  Path")
        click.echo(f"{'─'*5}  {'─'*22}  {'─'*35}  {'─'*60}")
        for r in results:
            click.echo(f"{r['id']:<5}  {r['status']:<22}  {r['name']:<35}  {r['path']}")
        ok      = sum(1 for r in results if r["status"] == "OK")
        skipped = sum(1 for r in results if r["status"].startswith("SKIP"))
        errors  = sum(1 for r in results if r["status"].startswith("ERROR"))
        click.echo()
        click.echo(f"Done: {ok} written, {skipped} skipped, {errors} errors.")


if __name__ == "__main__":
    main()
