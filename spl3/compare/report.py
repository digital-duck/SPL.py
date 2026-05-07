"""Report rendering for spl3 compare."""

from __future__ import annotations
import html as _html_mod
import base64 as _b64
import json
from pathlib import Path
from typing import Optional

from spl3.compare.types import ComparisonResult, GEDResult, BERTScoreResult

_TIER_TITLES = {
    "ged":          "Tier 1 – Topological (GED)",
    "llm":          "Tier 2 – Semantic (LLM)",
    "vision":       "Tier 2 – Semantic (Vision)",
    "ast-diff":     "Tier 3 – Syntactic (AST-diff)",
    "structural":   "Tier 4 – Structural",
    "git-diff":     "Tier 5 – Character-level (git-diff)",
    "vector":       "Tier 6 – Embedding (vector)",
    "bert-score":   "Tier 6 – Embedding (BERTScore)",
    "llm_fallback": "LLM Fallback",
}

_VERDICT_ICON = {
    "EQUIVALENT": "✅", "REFACTORED": "🔄", "DEGRADED": "⚠️", "DIVERGED": "❌",
}


def render_report(res: ComparisonResult, output_format: str) -> str:
    if output_format == "json":
        return json.dumps({
            "file1":      res.file1,
            "file2":      res.file2,
            "ext":        res.ext,
            "timestamp":  res.timestamp,
            "modes":      res.modes,
            "results":    {k: _serialize(v) for k, v in res.results.items()},
            "synthesis":  res.synthesis,
        }, indent=2)

    if output_format == "text":
        lines = [f"Comparison: {Path(res.file1).name}  ↔  {Path(res.file2).name}"]
        if res.synthesis:
            syn = res.synthesis
            lines.append(f"Verdict: {syn.get('verdict', 'UNKNOWN')} ({syn.get('confidence', '?')})")
            lines.append(f"  {syn.get('key_finding', '')}")
        for mode in res.modes:
            lines.append(f"\n--- {mode.upper()} ---")
            lines.append(str(res.results.get(mode, "N/A")))
        return "\n".join(lines)

    if output_format == "html":
        return _render_html(res)

    return _render_markdown(res)


def _serialize(obj):
    if isinstance(obj, (GEDResult, BERTScoreResult)):
        return obj.__dict__
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return obj


# ── Markdown ──────────────────────────────────────────────────────────────────

def _render_markdown(res: ComparisonResult) -> str:
    p1, p2 = Path(res.file1), Path(res.file2)
    lines: list[str] = [
        f"# Comparison: `{p1.name}`  ↔  `{p2.name}`",
        "",
        f"- **File 1:** `{p1.name}` ({res.ext})",
        f"- **File 2:** `{p2.name}` ({Path(res.file2).suffix.lower()})",
        f"- **Tiers:** {', '.join(res.modes)}",
        f"- **Timestamp:** {res.timestamp}",
        "",
    ]

    # Synthesis verdict banner
    if res.synthesis and isinstance(res.synthesis, dict) and "verdict" in res.synthesis:
        syn = res.synthesis
        icon = _VERDICT_ICON.get(syn["verdict"], "🔍")
        lines += [
            f"## Synthesis Verdict: {icon} {syn['verdict']} ({syn.get('confidence', '?')} confidence)",
            "",
            f"> **Key finding:** {syn.get('key_finding', '')}",
            f">",
            f"> **Cross-tier insight:** {syn.get('cross_tier_insight', '')}",
            f">",
            f"> **Recommendation:** {syn.get('recommendation', '')}",
            "",
            "---",
            "",
        ]
    elif res.synthesis:
        lines += [f"## Synthesis\n\n{res.synthesis}\n\n---\n"]

    all_modes = res.modes + (["llm_fallback"] if "llm_fallback" in res.results else [])
    body_parts: list[str] = []

    for mode in all_modes:
        val = res.results.get(mode)
        if val is None:
            continue
        title = _TIER_TITLES.get(mode, mode)
        section: list[str] = [f"## {title}", ""]

        if isinstance(val, GEDResult):
            _nt = lambda d: "  ".join(f"{k}×{v}" for k, v in sorted(d.items())) if d else "—"
            section += [
                f"| Metric | File 1 | File 2 |",
                f"|---|---|---|",
                f"| Nodes | {val.node_count[0]} | {val.node_count[1]} |",
                f"| Edges | {val.edge_count[0]} | {val.edge_count[1]} |",
                f"| Node types | {_nt(val.node_types[0])} | {_nt(val.node_types[1])} |",
                "",
                f"**Graph Edit Distance: {val.distance:.1f}** "
                f"*(normalized: {val.normalized_distance:.3f} — "
                f"0=EQUIVALENT, <0.10=REFACTORED, <0.35=DEGRADED, else=DIVERGED)*",
            ]

        elif isinstance(val, BERTScoreResult):
            section += [
                f"- Precision: {val.precision:.4f}",
                f"- Recall:    {val.recall:.4f}",
                f"- **F1:      {val.f1:.4f}**",
            ]

        elif mode == "git-diff" and isinstance(val, str):
            section += ["```diff", val, "```"]

        elif mode == "ast-diff" and isinstance(val, dict):
            for key, d in sorted(val.items()):
                if not isinstance(d, dict):
                    continue
                status = "✓" if not d.get("removed") and not d.get("added") else "✗"
                section.append(f"**{key}** {status}")
                if d.get("common"):
                    section.append(f"  - common: {', '.join(f'`{x}`' for x in d['common'])}")
                if d.get("removed"):
                    section.append(f"  - removed: {', '.join(f'`{x}`' for x in d['removed'])}")
                if d.get("added"):
                    section.append(f"  - added: {', '.join(f'`{x}`' for x in d['added'])}")

        elif mode == "structural" and isinstance(val, dict):
            s1 = val.get("file1", {})
            s2 = val.get("file2", {})
            section += [
                "| | File 1 | File 2 |",
                "|---|---|---|",
            ]
            for key in sorted(set(s1) | set(s2)):
                if key == "type":
                    continue
                section.append(f"| {key} | {s1.get(key, '—')} | {s2.get(key, '—')} |")

        elif mode == "vector" and isinstance(val, float):
            section.append(f"Cosine similarity: **{val:.4f}**")

        elif mode == "llm_fallback" and isinstance(val, dict):
            section += [
                f"*Covers failed tiers: {val.get('covers_failed', [])}*",
                "",
                val.get("analysis", ""),
            ]

        else:
            section.append(str(val))

        body_parts.append("\n".join(section))

    lines.append("\n\n---\n\n".join(body_parts))
    lines.append("\n---\n\n*Generated by `spl3 compare` — multi-tier diff*")
    return "\n".join(lines)


# ── HTML ──────────────────────────────────────────────────────────────────────

def _render_html(res: ComparisonResult) -> str:
    path1, path2 = Path(res.file1), Path(res.file2)
    content1 = path1.read_text(encoding="utf-8")
    content2 = path2.read_text(encoding="utf-8")
    ext = res.ext

    _IMG_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
    _MIME_MAP  = {".png": "image/png", ".jpg": "image/jpeg",
                  ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}

    def _panel(path: Path, content: str, ext: str) -> str:
        if ext == ".mmd":
            return f'<div class="mermaid">\n{_html_mod.escape(content)}\n</div>'
        if ext in _IMG_EXTS:
            try:
                mime = _MIME_MAP.get(ext, "image/png")
                data = _b64.standard_b64encode(path.read_bytes()).decode()
                return f'<img src="data:{mime};base64,{data}" style="max-width:100%;max-height:100%">'
            except Exception:
                return f'<pre>{_html_mod.escape(content[:2000])}</pre>'
        return f'<pre>{_html_mod.escape(content)}</pre>'

    def _synthesis_html(syn: Optional[dict]) -> str:
        if not syn or not isinstance(syn, dict) or "verdict" not in syn:
            return f'<p>{_html_mod.escape(str(syn or ""))}</p>' if syn else ""
        icon = _VERDICT_ICON.get(syn.get("verdict", ""), "🔍")
        v    = _html_mod.escape(str(syn.get("verdict", "?")))
        conf = _html_mod.escape(str(syn.get("confidence", "?")))
        kf   = _html_mod.escape(str(syn.get("key_finding", "")))
        cti  = _html_mod.escape(str(syn.get("cross_tier_insight", "")))
        rec  = _html_mod.escape(str(syn.get("recommendation", "")))
        return (
            f'<div class="verdict {syn.get("verdict","")}">'
            f'<h2>{icon} {v} <small>({conf} confidence)</small></h2>'
            f'<p><strong>Key finding:</strong> {kf}</p>'
            f'<p><strong>Cross-tier insight:</strong> {cti}</p>'
            f'<p><strong>Recommendation:</strong> {rec}</p>'
            f'</div>'
        )

    def _tier_body(mode: str, val) -> str:
        if isinstance(val, GEDResult):
            nt = val.node_types
            _nt = lambda d: ", ".join(f"{k}×{v}" for k, v in sorted(d.items())) if d else "—"
            return (
                "<table>"
                "<tr><th></th><th>File 1</th><th>File 2</th></tr>"
                f"<tr><td>Nodes</td><td>{val.node_count[0]}</td><td>{val.node_count[1]}</td></tr>"
                f"<tr><td>Edges</td><td>{val.edge_count[0]}</td><td>{val.edge_count[1]}</td></tr>"
                f"<tr><td>Node types</td><td>{_nt(nt[0])}</td><td>{_nt(nt[1])}</td></tr>"
                f"<tr><td>Normalized GED</td><td colspan='2'><strong>{val.normalized_distance:.3f}</strong>"
                f" (raw: {val.distance:.1f})</td></tr>"
                "</table>"
            )
        if isinstance(val, BERTScoreResult):
            return (
                "<table>"
                "<tr><th>Metric</th><th>Value</th></tr>"
                f"<tr><td>Precision</td><td>{val.precision:.4f}</td></tr>"
                f"<tr><td>Recall</td><td>{val.recall:.4f}</td></tr>"
                f"<tr><td><strong>F1</strong></td><td><strong>{val.f1:.4f}</strong></td></tr>"
                "</table>"
            )
        if mode == "git-diff" and isinstance(val, str):
            return f"<pre class='diff'>{_html_mod.escape(val)}</pre>"
        if mode == "ast-diff" and isinstance(val, dict):
            rows = []
            for key, d in sorted(val.items()):
                if not isinstance(d, dict):
                    continue
                status = "✓" if not d.get("removed") and not d.get("added") else "✗"
                rows.append(
                    f"<tr><td>{_html_mod.escape(key)}</td><td>{status}</td>"
                    f"<td>{', '.join(_html_mod.escape(x) for x in d.get('removed',[]))}</td>"
                    f"<td>{', '.join(_html_mod.escape(x) for x in d.get('added',[]))}</td></tr>"
                )
            if rows:
                return (
                    "<table><tr><th>Key</th><th></th><th>Removed</th><th>Added</th></tr>"
                    + "".join(rows) + "</table>"
                )
            return "<p>No differences</p>"
        if mode == "structural" and isinstance(val, dict):
            s1, s2 = val.get("file1", {}), val.get("file2", {})
            rows = [
                f"<tr><td>{_html_mod.escape(k)}</td>"
                f"<td>{_html_mod.escape(str(s1.get(k,'—')))}</td>"
                f"<td>{_html_mod.escape(str(s2.get(k,'—')))}</td></tr>"
                for k in sorted(set(s1) | set(s2)) if k != "type"
            ]
            return (
                "<table><tr><th></th><th>File 1</th><th>File 2</th></tr>"
                + "".join(rows) + "</table>"
            )
        if mode == "llm_fallback" and isinstance(val, dict):
            return (
                f"<p><em>Covers: {_html_mod.escape(str(val.get('covers_failed', [])))}</em></p>"
                f"<p>{_html_mod.escape(val.get('analysis', ''))}</p>"
            )
        return f"<pre>{_html_mod.escape(str(val)[:2000])}</pre>"

    all_modes = res.modes + (["llm_fallback"] if "llm_fallback" in res.results else [])
    tier_blocks = []
    for mode in all_modes:
        val = res.results.get(mode)
        if val is None:
            continue
        title = _TIER_TITLES.get(mode, mode)
        body  = _tier_body(mode, val)
        tier_blocks.append(
            f'<details class="tier" open>'
            f'<summary>{_html_mod.escape(title)}</summary>'
            f'<div class="tier-content">{body}</div>'
            f'</details>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Compare: {_html_mod.escape(path1.name)} ↔ {_html_mod.escape(path2.name)}</title>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
  <style>
    :root{{--gap:12px;--border:#d0d7de;--radius:6px}}
    *{{box-sizing:border-box}}
    body{{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:14px;background:#f6f8fa;height:100vh;display:flex;flex-direction:column}}
    .top-row{{display:grid;grid-template-columns:1fr 1fr;gap:var(--gap);padding:var(--gap);flex:0 0 58vh;min-height:0}}
    .bottom-row{{padding:0 var(--gap) var(--gap);flex:1;overflow:auto}}
    .panel{{background:#fff;border:1px solid var(--border);border-radius:var(--radius);overflow:auto;padding:12px;display:flex;flex-direction:column}}
    .panel h3{{margin:0 0 8px;font-size:12px;color:#57606a;font-weight:600;border-bottom:1px solid var(--border);padding-bottom:6px;flex-shrink:0}}
    .panel-inner{{flex:1;overflow:auto}}
    .mermaid{{text-align:center}}
    pre{{font-family:'SFMono-Regular',Consolas,monospace;font-size:12px;line-height:1.5;white-space:pre-wrap;word-break:break-word;margin:0}}
    .verdict{{padding:12px 16px;border-radius:var(--radius);margin-bottom:12px;border-left:4px solid #ccc}}
    .verdict h2{{margin:0;font-size:16px}} .verdict p{{margin:3px 0 0;font-size:13px;opacity:.85}}
    .EQUIVALENT{{background:#dafbe1;color:#1a7f37;border-color:#2da44e}}
    .REFACTORED{{background:#ddf4ff;color:#0550ae;border-color:#0969da}}
    .DEGRADED  {{background:#fff8c5;color:#9a6700;border-color:#bf8700}}
    .DIVERGED  {{background:#ffebe9;color:#cf222e;border-color:#cf222e}}
    .tier{{border:1px solid var(--border);border-radius:var(--radius);margin-bottom:8px;overflow:hidden}}
    .tier summary{{padding:8px 12px;font-weight:600;cursor:pointer;background:#f6f8fa;list-style:none}}
    .tier summary:hover{{background:#eaeef2}}
    .tier-content{{padding:12px;background:#fff}}
    table{{border-collapse:collapse;width:100%}} th,td{{border:1px solid var(--border);padding:5px 9px;text-align:left;font-size:13px}} th{{background:#f6f8fa;font-weight:600}}
    .meta{{font-size:11px;color:#57606a;margin-bottom:10px}}
  </style>
</head>
<body>
  <div class="top-row">
    <div class="panel">
      <h3>📄 {_html_mod.escape(path1.name)}</h3>
      <div class="panel-inner">{_panel(path1, content1, ext)}</div>
    </div>
    <div class="panel">
      <h3>📄 {_html_mod.escape(path2.name)}</h3>
      <div class="panel-inner">{_panel(path2, content2, path2.suffix.lower())}</div>
    </div>
  </div>
  <div class="bottom-row">
    <p class="meta">Tiers: {_html_mod.escape(', '.join(res.modes))} &nbsp;|&nbsp; {_html_mod.escape(res.timestamp)}</p>
    {_synthesis_html(res.synthesis)}
    {''.join(tier_blocks)}
  </div>
  <script>mermaid.initialize({{startOnLoad:true,theme:'default',securityLevel:'loose'}});</script>
</body>
</html>"""
