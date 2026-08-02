"""BOM / manifest batch comparison for `spl3 compare`.

Compare two directory trees anchored on a manifest — a Bill of Materials — by
running the multi-tier comparison per listed item and rolling the per-item
verdicts up into a single manifest-level verdict. This is the reusable batch tier
above single-file `spl3 compare`: it works for any two builds of the same manifest
(a GDW component graph, a ConceptBook domain, or a hand-authored file list).

Manifest format (YAML or JSON)::

    name: todo backend
    items:
      - name: todo_schema
        file: app/schemas.py        # resolved under --ref and --cand
      - name: api_routes
        file: app/main.py
      # or explicit per-item pair:
      - name: something
        file1: a/x.py
        file2: b/x.py
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from spl3.compare.engine import run_comparison
from spl3.compare.verdict import verdict_of

# worst-verdict ranking for the roll-up; UNKNOWN is treated as a mild concern.
_RANK = {"EQUIVALENT": 0, "REFACTORED": 1, "UNKNOWN": 1, "DEGRADED": 2,
         "DIVERGED": 3, "MISSING": 3}


def load_manifest(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".yaml", ".yml"):
        import yaml
        return yaml.safe_load(text)
    return json.loads(text)


def _resolve_pair(item: dict, ref: Optional[Path], cand: Optional[Path]) -> tuple[Path, Path]:
    if item.get("file1") and item.get("file2"):
        return Path(item["file1"]), Path(item["file2"])
    rel = item.get("file")
    if not rel:
        raise ValueError(f"manifest item {item!r} needs 'file' (with --ref/--cand) or 'file1'+'file2'")
    if ref is None or cand is None:
        raise ValueError("manifest items use 'file'; --ref and --cand directories are required")
    return ref / rel, cand / rel


def _rollup(items: list[dict]) -> dict:
    counts: dict[str, int] = {}
    worst = "EQUIVALENT"
    for it in items:
        v = it["verdict"]
        counts[v] = counts.get(v, 0) + 1
        if _RANK.get(v, 1) > _RANK.get(worst, 0):
            worst = v
    return {"verdict": worst, "counts": counts, "n": len(items)}


async def run_manifest(manifest: dict, ref: Optional[Path], cand: Optional[Path],
                       active_modes: list[str], adapter: str, model: Optional[str] = None,
                       synthesize: bool = False, adapter_synthesis: Optional[str] = None) -> dict:
    items_out: list[dict] = []
    for item in manifest.get("items", []):
        name = item.get("name") or item.get("file") or "?"
        f1, f2 = _resolve_pair(item, ref, cand)
        row: dict = {"name": name, "file": item.get("file", f"{f1.name} vs {f2.name}")}
        if not f1.exists() or not f2.exists():
            row["verdict"] = "MISSING"
            row["note"] = (("ref " if not f1.exists() else "") +
                           ("cand" if not f2.exists() else "")).strip() + " absent"
            items_out.append(row)
            continue
        if f1.read_bytes() == f2.read_bytes():
            row["verdict"], row["note"] = "EQUIVALENT", "byte-identical"
            items_out.append(row)
            continue
        res = await run_comparison(
            path1=f1, path2=f2, active_modes=active_modes, adapter_name=adapter,
            model=model, adapter_synthesis=adapter_synthesis, synthesize=synthesize)
        v = verdict_of(res)
        row["verdict"] = v.get("verdict", "UNKNOWN")
        row["note"] = v.get("key_finding", "")
        items_out.append(row)
    return {"name": manifest.get("name", "manifest"), "modes": active_modes,
            "items": items_out, "rollup": _rollup(items_out)}


def render_manifest(report: dict, output_format: str = "markdown") -> str:
    if output_format == "json":
        return json.dumps(report, indent=2)
    L = [f"# BOM comparison — {report['name']}", "",
         f"Tiers: {', '.join(report['modes'])}", "",
         "| Item | Verdict | Note |", "|------|---------|------|"]
    for it in report["items"]:
        L.append(f"| `{it['name']}` | {it['verdict']} | {it.get('note', '')} |")
    r = report["rollup"]
    tally = ", ".join(f"{k}×{v}" for k, v in sorted(r["counts"].items()))
    L += ["", f"**Roll-up verdict: {r['verdict']}**  ({tally}; n={r['n']})"]
    return "\n".join(L)
