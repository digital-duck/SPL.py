"""spl2mmd_batch.py — Generate Mermaid diagrams from SPL cookbook recipes.

Delegates to `spl3 spl2mmd` for each recipe's .spl file, which by default
produces .mmd + .svg + .png + .pdf + .html + .md in a `mermaid/` subdir
alongside the .spl file.

The generated artifacts are ground-truth label data for seeding the Code RAG
vectorDB — specifically the mmd→spl compiler direction.

Usage examples:
    # Single recipe → cookbook/05_self_refine/mermaid/{svg,png,pdf,...}
    python cookbook/spl2mmd_batch.py --ids 05

    # Multiple recipes
    python cookbook/spl2mmd_batch.py --ids 05,09,16

    # All approved recipes
    python cookbook/spl2mmd_batch.py --all

    # Custom catalog
    python cookbook/spl2mmd_batch.py --catalog cookbook/cookbook_catalog.json --ids 05

    # Dry-run (print Mermaid, don't write files)
    python cookbook/spl2mmd_batch.py --ids 05 --dry-run

    # Skip existing files (overwrite is on by default)
    python cookbook/spl2mmd_batch.py --ids 05 --no-overwrite
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import click


def _find_spl(recipe_dir: Path) -> Path | None:
    """Return the primary .spl file in a recipe directory.

    Preference order:
    1. <dir_name_without_NN_prefix>.spl  (e.g. 05_self_refine → self_refine.spl)
    2. First .spl alphabetically
    """
    # Strip leading NN_ prefix to get the canonical stem
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
        # --all: return approved + new recipes that have spl3-run args
        return [
            r for r in recipes
            if r.get("approval_status") in ("approved", "new")
            and r.get("args", [""])[0] == "spl3"
        ]
    id_set = {i.strip() for i in ids}
    return [r for r in recipes if r["id"] in id_set]


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
    help="Comma-separated recipe IDs to process (e.g. '05,09,16'). Omit to use --all.",
)
@click.option(
    "--all", "run_all",
    is_flag=True,
    default=False,
    help="Process all approved/new spl3-run recipes in the catalog.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Print generated Mermaid to stdout; do not write .mmd files.",
)
@click.option(
    "--overwrite/--no-overwrite",
    default=True,
    show_default=True,
    help="Overwrite existing files (default: overwrite).",
)
@click.option(
    "--remove-function-nodes/--keep-function-nodes",
    default=False,
    show_default=True,
    help="Strip FUNCTION definition nodes from the diagram (post-processor).",
)
def main(
    catalog: str,
    ids: str | None,
    run_all: bool,
    dry_run: bool,
    overwrite: bool,
    remove_function_nodes: bool,
) -> None:
    """Generate Mermaid diagrams (mmd/svg/png/pdf/html/md) from SPL cookbook recipes."""
    if not ids and not run_all:
        click.echo("Specify --ids <id,...> or --all.", err=True)
        sys.exit(1)

    catalog_path = Path(catalog)
    cookbook_root = catalog_path.parent  # e.g. .../SPL.py/cookbook/

    recipes = _load_catalog(catalog_path)
    id_list = [i.strip() for i in ids.split(",")] if ids else None
    selected = _filter_recipes(recipes, id_list)

    if not selected:
        click.echo("No matching recipes found.", err=True)
        sys.exit(1)

    results: list[dict] = []

    for recipe in selected:
        rid = recipe["id"]
        name = recipe["name"]
        rdir = cookbook_root / recipe["dir"]

        spl_path = _find_spl(rdir)
        if spl_path is None:
            results.append({"id": rid, "name": name, "status": "SKIP (no .spl)", "path": ""})
            continue

        # Output dir: cookbook/<recipe_dir>/mermaid/  (spl3 spl2mmd default)
        mmd_dir = rdir / "mermaid"
        out_path = mmd_dir / (spl_path.stem + ".mmd")

        if dry_run:
            from spl3.spl2mmd import spl_to_mermaid, remove_function_nodes as _remove_fn
            try:
                mermaid = spl_to_mermaid(spl_path.read_text(encoding="utf-8"))
                if remove_function_nodes:
                    mermaid = _remove_fn(mermaid)
            except Exception as exc:
                results.append({"id": rid, "name": name, "status": f"ERROR: {exc}", "path": ""})
                continue
            click.echo(f"\n{'─'*60}")
            click.echo(f"Recipe {rid}: {name}  ({spl_path})")
            click.echo(f"Would write → {mmd_dir / (spl_path.stem + '.*')} (mmd/svg/png/pdf/html/md)")
            click.echo(f"{'─'*60}")
            click.echo(mermaid)
            results.append({"id": rid, "name": name, "status": "DRY-RUN", "path": str(out_path)})
            continue

        if out_path.exists() and not overwrite:
            results.append({"id": rid, "name": name, "status": "SKIP (exists)", "path": str(out_path)})
            continue

        # Delegate to `spl3 spl2mmd` — generates mmd/svg/png/pdf/html/md in mermaid/ subdir
        cmd = [sys.executable, "-m", "spl3.cli", "spl2mmd", str(spl_path), "--no-preview"]
        if remove_function_nodes:
            cmd.append("--remove-function-nodes")
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode == 0:
                results.append({"id": rid, "name": name, "status": "OK", "path": str(mmd_dir)})
                if proc.stdout.strip():
                    click.echo(proc.stdout.rstrip())
            else:
                err = (proc.stderr or proc.stdout).strip().splitlines()[0]
                results.append({"id": rid, "name": name, "status": f"ERROR: {err}", "path": ""})
        except Exception as exc:
            results.append({"id": rid, "name": name, "status": f"ERROR: {exc}", "path": ""})

    # Summary table
    if not dry_run:
        click.echo()
        click.echo(f"{'ID':<5}  {'Status':<20}  {'Name':<35}  Path")
        click.echo(f"{'─'*5}  {'─'*20}  {'─'*35}  {'─'*50}")
        for r in results:
            click.echo(f"{r['id']:<5}  {r['status']:<20}  {r['name']:<35}  {r['path']}")
        ok = sum(1 for r in results if r["status"] == "OK")
        skipped = sum(1 for r in results if r["status"].startswith("SKIP"))
        errors = sum(1 for r in results if r["status"].startswith("ERROR"))
        click.echo()
        click.echo(f"Done: {ok} written, {skipped} skipped, {errors} errors.")


if __name__ == "__main__":
    main()
