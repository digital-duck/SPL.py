"""Shared content-safety/quality helpers for generated concept-book HTML.

Single source of truth for two things that used to be duplicated (and
could silently drift apart) between the live generation path
(spl/tools.py's _md_to_html/_inline_md) and the standalone repair script
(scripts/sanitize_html_content.py):

1. What counts as "safe" generated inline markup (ALLOWED_INLINE_TAGS) vs.
   injected content (see docs/README-todo.md's "Content-injection fix in
   generated HTML").
2. Malformed-LaTeX delimiter detection — a single `$` opened but closed
   with `$$` (or vice versa) breaks MathJax rendering, AND was the exact
   shape that confused sanitize_html_content.py's first-draft `$$...$$`
   pairing regex into swallowing real page structure (see that file's
   _STRUCTURAL_TAGS docstring). Surfacing this at generation time, not
   only in a later standalone scan, is the point of pulling it out here.

No dependency on spl_tool/the SPL workflow engine — deliberately a plain
leaf module so both spl/tools.py (which already has its own
`from spl.tools import spl_tool` self-import quirk) and a standalone
script under scripts/ can import it without fighting that.
"""
from __future__ import annotations

import re

# ── HTML escaping ──────────────────────────────────────────────────────────

def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ── Tag allowlists (content-injection detection) ────────────────────────────

# The only tags _inline_md can legitimately produce inside a
# <p>/<li>/<h#> block's own text. Anything else found nested inside one of
# these blocks did not come from this generator's own markdown formatting.
# "a" covers the research-style reference links _inline_md renders from
# `[text](url)` markdown (see style_profiles.py's RESEARCH_REFERENCE_RULE).
ALLOWED_INLINE_TAGS = {"strong", "em", "code", "a"}

# Tags the generator would never legitimately nest inside a
# <p>/<li>/<h#>/$$...$$ block. Finding one isn't itself proof of real
# injected content — it's more often a mismatched-$-delimiter typo (see
# find_malformed_latex below) confusing a regex-based scan into pairing
# with the wrong closing delimiter far downstream and swallowing real
# page structure in between. Route a match containing one of these to
# manual review rather than auto-fixing it.
STRUCTURAL_TAGS = {
    "p", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6",
    "section", "div", "main", "nav", "footer", "header", "table",
    "tr", "td", "th", "pre",
}

_TAG_RE = re.compile(r"</?([a-zA-Z][a-zA-Z0-9-]*)")


def offending_tags(inner: str) -> list[str]:
    """Tag names found in `inner` that aren't in ALLOWED_INLINE_TAGS."""
    return sorted({t for t in _TAG_RE.findall(inner) if t.lower() not in ALLOWED_INLINE_TAGS})


# ── Malformed LaTeX delimiter detection ─────────────────────────────────────

# A single `$` opened but closed with `$$` (e.g. "...$b \in \{0, 1\}$$)...",
# confirmed live in a real generated page — the LLM meant `$...$` inline
# math but typoed the closing delimiter), or the mirror case ($$ opened,
# single $ closed). Capped length + no newlines crossed, so this only
# matches a plausible same-sentence typo, not an accidental huge span.
_SINGLE_OPEN_DOUBLE_CLOSE = re.compile(r"\$(?!\$)([^$\n]{1,300}?)\$\$")
_DOUBLE_OPEN_SINGLE_CLOSE = re.compile(r"\$\$([^$\n]{1,300}?)\$(?!\$)")


def find_malformed_latex(text: str) -> list[dict]:
    """Returns a list of {kind, snippet} for each likely mismatched-$
    delimiter found in `text`. Advisory only — a heuristic, not a LaTeX
    parser, so false positives are possible (e.g. a genuine currency `$`
    near unrelated math); callers should report these, not auto-fix them,
    since a correct fix requires knowing what the author actually meant.
    """
    findings = []
    for m in _SINGLE_OPEN_DOUBLE_CLOSE.finditer(text):
        findings.append({"kind": "single-$-opened-double-$$-closed", "snippet": m.group(0).strip()[:160]})
    for m in _DOUBLE_OPEN_SINGLE_CLOSE.finditer(text):
        findings.append({"kind": "double-$$-opened-single-$-closed", "snippet": m.group(0).strip()[:160]})
    return findings
