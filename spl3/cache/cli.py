from __future__ import annotations

import json
from pathlib import Path

import click

from .content import get_content_cache
from .types import PROVENANCE_TIERS


def _cache() -> "ContentCache":  # noqa: F821
    from .content import get_content_cache
    return get_content_cache()


@click.group("cache", short_help="Manage the Layer 2 content cache.")
def cmd_cache():
    """Inspect, invalidate, export, and import the Layer 2 content cache.

    The content cache stores verified generated sections keyed by a hash of
    their inputs (concept + params + rubric version + dependency hashes).
    Entries are write-once immutable; invalidation is input-driven, not TTL.
    """


# ------------------------------------------------------------------ #
# Inspect                                                              #
# ------------------------------------------------------------------ #

@cmd_cache.command("list")
@click.option("--concept", default=None, metavar="NAME", help="Filter by concept name.")
@click.option(
    "--provenance", default=None,
    type=click.Choice(PROVENANCE_TIERS), metavar="TIER",
    help="Filter by provenance tier.",
)
@click.option(
    "--format", "fmt", default="table",
    type=click.Choice(["table", "json"]),
    show_default=True,
)
def cmd_list(concept, provenance, fmt):
    """List cached entries."""
    cache = _cache()
    rows = cache._meta.export_rows()

    if concept:
        rows = [r for r in rows if r["concept"] == concept]
    if provenance:
        rows = [r for r in rows if r["provenance"] == provenance]

    if fmt == "json":
        click.echo(json.dumps(rows, indent=2))
        return

    if not rows:
        click.echo("No entries found.")
        return

    col_w = max(len(r["concept"]) for r in rows) + 2
    click.echo(f"\n  {'CONCEPT'.ljust(col_w)}  {'PROVENANCE'.ljust(20)}  STALE  HITS  TOKENS  KEY[:12]")
    click.echo(f"  {'-'*col_w}  {'─'*20}  ─────  ────  ──────  ────────────")
    for r in rows:
        stale = "yes" if r["stale"] else "no "
        click.echo(
            f"  {r['concept'].ljust(col_w)}  {r['provenance'].ljust(20)}  "
            f"{stale}    {r['hit_count']:<4}  {r['token_cost']:<6}  {r['key'][:12]}"
        )
    click.echo(f"\n  {len(rows)} entry/entries")


@cmd_cache.command("show")
@click.argument("key")
def cmd_show(key):
    """Show full details of a cache entry."""
    cache = _cache()
    meta = cache._meta.get_meta(key)
    if meta is None:
        raise click.ClickException(f"No entry with key: {key}")

    from dd_cache.utils import deserialize
    raw = cache._store.get(key)
    content = deserialize(raw) if isinstance(raw, bytes) else (raw or "")

    click.echo(json.dumps({**meta, "content_preview": content[:200]}, indent=2))


@cmd_cache.command("stats")
def cmd_stats():
    """Show cache statistics: hit rate, tokens saved, provenance breakdown."""
    cache = _cache()
    s = cache.stats()
    click.echo(f"\n  Total entries : {s.total_entries}")
    click.echo(f"  Stale         : {s.stale_count}")
    click.echo(f"  Total hits    : {s.total_hits}")
    click.echo(f"  Token cost    : {s.total_token_cost}")
    click.echo(f"  Tokens saved  : {s.estimated_tokens_saved}")
    click.echo(f"\n  By provenance:")
    for tier in PROVENANCE_TIERS:
        count = s.by_provenance.get(tier, 0)
        click.echo(f"    {tier.ljust(22)} {count}")
    click.echo(f"\n  Concepts ({len(s.concepts)}): {', '.join(s.concepts[:10])}"
               + (" …" if len(s.concepts) > 10 else ""))


# ------------------------------------------------------------------ #
# Invalidation                                                         #
# ------------------------------------------------------------------ #

@cmd_cache.command("invalidate")
@click.option("--concept", required=True, metavar="NAME", help="Concept to invalidate.")
@click.option("--cascade/--no-cascade", default=True, show_default=True,
              help="Propagate invalidation to all dependents via dep_graph.")
def cmd_invalidate(concept, cascade):
    """Mark a concept (and optionally its dependents) as stale."""
    cache = _cache()
    affected = cache.invalidate(concept, cascade=cascade)
    click.echo(f"Invalidated {len(affected)} concept(s): {', '.join(affected)}")


@cmd_cache.command("clear")
@click.option("--stale", "mode", flag_value="stale", help="Remove only stale-flagged entries.")
@click.option("--all", "mode", flag_value="all", help="Remove all entries (prompt cache unaffected).")
@click.option("--provenance", "mode", flag_value="provenance",
              help="Remove entries at a specific provenance tier.")
@click.option("--tier", default=None, type=click.Choice(PROVENANCE_TIERS),
              help="Tier to remove when --provenance is set.")
def cmd_clear(mode, tier):
    """Remove entries from the content cache."""
    if not mode:
        raise click.UsageError("Specify --stale, --all, or --provenance --tier TIER.")
    cache = _cache()
    if mode == "stale":
        n = cache.clear_stale()
        click.echo(f"Removed {n} stale entry/entries.")
    elif mode == "all":
        click.confirm("Remove ALL content cache entries?", abort=True)
        n = cache.clear_all()
        click.echo(f"Removed {n} entry/entries.")
    elif mode == "provenance":
        if not tier:
            raise click.UsageError("--tier required with --provenance.")
        n = cache.clear_by_provenance(tier)
        click.echo(f"Removed {n} entry/entries at provenance '{tier}'.")


# ------------------------------------------------------------------ #
# Portability                                                          #
# ------------------------------------------------------------------ #

@cmd_cache.command("export")
@click.option("-o", "--output", required=True, metavar="FILE",
              help="Output archive path (e.g. cache.tar.gz).")
def cmd_export(output):
    """Export all cache entries to a portable .tar.gz archive."""
    cache = _cache()
    out = Path(output)
    cache.export(out)
    s = cache.stats()
    click.echo(f"Exported {s.total_entries} entry/entries → {out}")


@cmd_cache.command("import")
@click.argument("archive")
@click.option("--merge/--no-merge", default=True, show_default=True,
              help="Skip conflicting keys (merge=True) or error on conflict.")
def cmd_import(archive, merge):
    """Import cache entries from a .tar.gz archive."""
    cache = _cache()
    n = cache.import_(Path(archive), merge=merge)
    click.echo(f"Imported {n} entry/entries from {archive}.")


# ------------------------------------------------------------------ #
# Promotion                                                            #
# ------------------------------------------------------------------ #

@cmd_cache.command("promote")
@click.argument("key")
@click.option("--to", "new_provenance", required=True,
              type=click.Choice(PROVENANCE_TIERS),
              help="Target provenance tier.")
def cmd_promote(key, new_provenance):
    """Manually promote a cache entry to a higher provenance tier."""
    cache = _cache()
    try:
        cache.promote(key, new_provenance)
        click.echo(f"Promoted {key[:12]}… → {new_provenance}")
    except (KeyError, ValueError) as exc:
        raise click.ClickException(str(exc))
