from __future__ import annotations

import json
from pathlib import Path

import click

from .content import get_content_cache
from .types import ALL_BADGES, is_canonical


def _cache() -> "ContentCache":  # noqa: F821
    from .content import get_content_cache
    return get_content_cache()


def _fmt_badges(badges: list[str]) -> str:
    """Render a badge set for table output; ★ marks the canonical composite."""
    if not badges:
        return "—"
    label = ",".join(badges)
    return f"★ {label}" if is_canonical(badges) else label


@click.group("cache", short_help="Manage the Layer 2 content cache.")
def cmd_cache():
    """Inspect, invalidate, export, and import the Layer 2 content cache.

    The content cache stores verified generated sections keyed by a hash of
    their inputs (concept + params + rubric version + dependency hashes).
    Entries are write-once immutable; invalidation is input-driven, not TTL.

    Trust is a badge set on two orthogonal axes (B-4): claim badges
    (machine_verified → machine_proved) attest the math, exposition badges
    (ai_reviewed → human_verified) attest the prose. ★ marks 'canonical' —
    the derived composite of the top badge on both axes.
    """


# ------------------------------------------------------------------ #
# Inspect                                                              #
# ------------------------------------------------------------------ #

@cmd_cache.command("list")
@click.option("--concept", default=None, metavar="NAME", help="Filter by concept name.")
@click.option(
    "--badge", default=None,
    type=click.Choice(ALL_BADGES + ["unbadged"]), metavar="BADGE",
    help="Filter by trust badge ('unbadged' = machine_generated baseline).",
)
@click.option(
    "--format", "fmt", default="table",
    type=click.Choice(["table", "json"]),
    show_default=True,
)
def cmd_list(concept, badge, fmt):
    """List cached entries."""
    cache = _cache()
    rows = cache._meta.export_rows()
    for r in rows:
        r["badges"] = json.loads(r["badges"])

    if concept:
        rows = [r for r in rows if r["concept"] == concept]
    if badge == "unbadged":
        rows = [r for r in rows if not r["badges"]]
    elif badge:
        rows = [r for r in rows if badge in r["badges"]]

    if fmt == "json":
        click.echo(json.dumps(rows, indent=2))
        return

    if not rows:
        click.echo("No entries found.")
        return

    col_w = max(len(r["concept"]) for r in rows) + 2
    badge_w = max([len(_fmt_badges(r["badges"])) for r in rows] + [len("BADGES")]) + 2
    click.echo(f"\n  {'CONCEPT'.ljust(col_w)}  {'BADGES'.ljust(badge_w)}  STALE  HITS  TOKENS  VERIFIER  KEY[:12]")
    click.echo(f"  {'-'*col_w}  {'─'*badge_w}  ─────  ────  ──────  ────────  ────────────")
    for r in rows:
        stale = "yes" if r["stale"] else "no "
        key_id = r["key"].rsplit(":", 1)[-1][:12]
        click.echo(
            f"  {r['concept'].ljust(col_w)}  {_fmt_badges(r['badges']).ljust(badge_w)}  "
            f"{stale}    {r['hit_count']:<4}  {r['token_cost']:<6}  "
            f"{(r.get('verifier') or '—').ljust(8)}  {key_id}"
        )
    click.echo(f"\n  {len(rows)} entry/entries")


@cmd_cache.command("show")
@click.argument("key")
def cmd_show(key):
    """Show full details of a cache entry.

    When the entry carries a formal statement (machine_proved), the prose
    and the Lean statement are rendered together so their correspondence —
    the one link nothing machine-checks — can be audited at a glance.
    """
    cache = _cache()
    meta = cache._meta.get_meta(key)
    if meta is None:
        raise click.ClickException(f"No entry with key: {key}")

    from dd_cache.utils import deserialize
    raw = cache._store.get(key)
    content = deserialize(raw) if isinstance(raw, bytes) else (raw or "")

    meta = dict(meta)
    meta["badges"] = json.loads(meta["badges"])
    meta["canonical"] = is_canonical(meta["badges"])
    click.echo(json.dumps({**meta, "content_preview": content[:200]}, indent=2))

    if meta.get("statement"):
        click.echo("\n  ── prose (preview) " + "─" * 40)
        click.echo("  " + content[:200].replace("\n", "\n  "))
        click.echo("\n  ── formal statement (kernel-checked) " + "─" * 22)
        click.echo("  " + meta["statement"].replace("\n", "\n  "))


@cmd_cache.command("stats")
def cmd_stats():
    """Show cache statistics: hit rate, tokens saved, badge breakdown."""
    cache = _cache()
    s = cache.stats()
    click.echo(f"\n  Total entries : {s.total_entries}")
    click.echo(f"  Stale         : {s.stale_count}")
    click.echo(f"  Total hits    : {s.total_hits}")
    click.echo(f"  Token cost    : {s.total_token_cost}")
    click.echo(f"  Tokens saved  : {s.estimated_tokens_saved}")
    click.echo(f"\n  By badge:")
    click.echo(f"    {'(unbadged)'.ljust(22)} {s.unbadged}")
    for b in ALL_BADGES:
        click.echo(f"    {b.ljust(22)} {s.by_badge.get(b, 0)}")
    click.echo(f"    {'★ canonical'.ljust(22)} {s.canonical}")
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
@click.option("--badge", default=None, type=click.Choice(ALL_BADGES + ["unbadged"]),
              help="Remove entries holding this badge ('unbadged' = badge-less baseline).")
def cmd_clear(mode, badge):
    """Remove entries from the content cache."""
    if not mode and not badge:
        raise click.UsageError("Specify --stale, --all, or --badge BADGE.")
    cache = _cache()
    if badge:
        n = cache.clear_by_badge(badge)
        click.echo(f"Removed {n} entry/entries holding badge '{badge}'.")
    elif mode == "stale":
        n = cache.clear_stale()
        click.echo(f"Removed {n} stale entry/entries.")
    elif mode == "all":
        click.confirm("Remove ALL content cache entries?", abort=True)
        n = cache.clear_all()
        click.echo(f"Removed {n} entry/entries.")


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
@click.option("--to", "badge", required=True,
              type=click.Choice(ALL_BADGES),
              help="Trust badge to add (claim axis: machine_verified, "
                   "machine_proved; exposition axis: ai_reviewed, human_verified).")
def cmd_promote(key, badge):
    """Add a trust badge to a cache entry."""
    cache = _cache()
    try:
        badges = cache.promote(key, badge)
        star = " ★ canonical" if is_canonical(badges) else ""
        key_id = key.rsplit(":", 1)[-1][:12]
        click.echo(f"Promoted {key_id}… → {{{', '.join(badges)}}}{star}")
    except (KeyError, ValueError) as exc:
        raise click.ClickException(str(exc))
