"""Tools for recipe 74 — concept-book generator.

build_html_page: convert the accumulated markdown textbook to a self-contained
HTML page with MathJax, a two-column layout (TOC sidebar + content), and clean
academic typography.  Called from build_concept_book.spl after all sections are
generated and verified.
"""
from __future__ import annotations

import re

from spl.tools import spl_tool


@spl_tool
def build_html_page(textbook_md: str, domain_yaml: str, target: str, language: str = "en") -> str:
    """Convert a markdown concept-book to a self-contained HTML file.

    Sections are separated by '\\n---\\n' dividers in textbook_md.  Each
    section is expected to begin with a '## concept_name' heading (added by the
    workflow via the accumulation step).  MathJax v3 renders all LaTeX.
    """
    domain = re.sub(r'(_graph)?\.(ya?ml|json|py)$', '', domain_yaml)
    domain_title = domain.replace('_', ' ').title()
    target_title = target.replace('_', ' ')
    lang_attr = f' lang="{language}"' if language and language != "en" else ' lang="en"'

    raw_parts = re.split(r'\n+---\n+', textbook_md)
    raw_parts = [p.strip() for p in raw_parts if p.strip()]

    toc_items: list[str] = []
    sections_html: list[str] = []

    for i, part in enumerate(raw_parts):
        m = re.match(r'^#+\s*(.+?)(?:\s*\n|$)', part)
        title = m.group(1).strip() if m else f'Section {i + 1}'
        slug = re.sub(r'\W+', '-', title.lower()).strip('-')
        toc_items.append(f'<li><a href="#{slug}">{_esc(title)}</a></li>')
        sections_html.append(f'<section id="{slug}">\n{_md_to_html(part)}\n</section>')

    toc_html = '<ol>\n' + '\n'.join(toc_items) + '\n</ol>'
    body_content = '\n\n'.join(sections_html)

    return _HTML_TEMPLATE.format(
        domain_title=domain_title,
        target_title=target_title,
        lang_attr=lang_attr,
        toc=toc_html,
        body=body_content,
    )


# ── internal helpers ──────────────────────────────────────────────────────────

def _esc(text: str) -> str:
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _inline_md(text: str) -> str:
    """Bold, italic, backtick-code.  Leaves $ LaTeX delimiters untouched."""
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'`([^`]+)`', lambda m: f'<code>{_esc(m.group(1))}</code>', text)
    return text


def _md_to_html(md: str) -> str:
    """Minimal Markdown → HTML.  Preserves $...$ and $$...$$ for MathJax."""
    lines = md.split('\n')
    out: list[str] = []
    in_code = False
    code_buf: list[str] = []
    para_buf: list[str] = []

    def flush_para() -> None:
        if para_buf:
            out.append(f'<p>{" ".join(para_buf)}</p>')
            para_buf.clear()

    for line in lines:
        # Fenced code blocks
        if line.startswith('```'):
            if in_code:
                out.append(f'<pre><code>{_esc(chr(10).join(code_buf))}</code></pre>')
                code_buf.clear()
                in_code = False
            else:
                flush_para()
                in_code = True
            continue
        if in_code:
            code_buf.append(line)
            continue

        # Headings
        m = re.match(r'^(#{1,6})\s+(.+)$', line)
        if m:
            flush_para()
            lvl = len(m.group(1))
            text = _inline_md(m.group(2))
            slug = re.sub(r'\W+', '-', m.group(2).lower()).strip('-')
            out.append(f'<h{lvl} id="{slug}">{text}</h{lvl}>')
            continue

        # List items (bullet or numbered)
        m = re.match(r'^(?:[-*]|\d+\.)\s+(.+)$', line)
        if m:
            flush_para()
            out.append(f'<li>{_inline_md(m.group(1))}</li>')
            continue

        # Display math (lines that are pure $$ ... $$)
        if re.match(r'^\s*\$\$', line):
            flush_para()
            out.append(line)
            continue

        # Horizontal rule
        if re.match(r'^---+$', line.strip()):
            flush_para()
            out.append('<hr>')
            continue

        # Blank line → paragraph break
        if not line.strip():
            flush_para()
            continue

        para_buf.append(_inline_md(line))

    flush_para()
    return '\n'.join(out)


_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html{lang_attr}>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Concept-Book: {target_title} — {domain_title}</title>
<script>
MathJax = {{
  tex: {{ inlineMath: [['$','$'],['\\\\(','\\\\)']], displayMath: [['$$','$$'],['\\\\[','\\\\]']] }},
  options: {{ skipHtmlTags: ['script','noscript','style','textarea','pre','code'] }}
}};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js" async></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:Georgia,serif;background:#fafaf8;color:#1a1a1a;line-height:1.7}}
.page{{display:grid;grid-template-columns:260px 1fr;min-height:100vh}}
nav{{position:sticky;top:0;height:100vh;overflow-y:auto;
     background:#1e3a5f;color:#e8f0fe;padding:24px 16px}}
nav h2{{font-size:.8rem;letter-spacing:.1em;text-transform:uppercase;
        color:#90b4e8;margin-bottom:14px}}
nav ol{{list-style:decimal inside;padding:0}}
nav li{{margin-bottom:7px;font-size:.85rem;line-height:1.4}}
nav a{{color:#a8c8f0;text-decoration:none}}
nav a:hover{{color:#fff}}
main{{padding:48px 64px;max-width:860px}}
h1.book-title{{font-size:2rem;color:#1e3a5f;margin-bottom:4px}}
.subtitle{{color:#666;margin-bottom:48px;font-size:1rem;font-style:italic}}
section{{margin-bottom:56px;border-top:1px solid #e0e0d8;padding-top:40px}}
section:first-of-type{{border-top:none;padding-top:0}}
h2{{font-size:1.45rem;color:#1e3a5f;margin-bottom:12px}}
h3{{font-size:1.1rem;color:#2e4a7f;margin:20px 0 8px}}
h4{{font-size:1rem;color:#3a5a8f;margin:16px 0 6px}}
p{{margin-bottom:16px;font-size:1rem}}
li{{margin-bottom:6px;margin-left:24px;font-size:1rem}}
pre{{background:#f4f4f0;border:1px solid #d8d8d0;border-radius:6px;
     padding:16px 20px;overflow-x:auto;margin:16px 0}}
code{{font-family:Menlo,Consolas,monospace;font-size:.87em}}
p code{{background:#f0f0ea;padding:1px 4px;border-radius:3px}}
@media(max-width:768px){{.page{{grid-template-columns:1fr}}
nav{{position:relative;height:auto}}}}
</style>
</head>
<body>
<div class="page">
  <nav>
    <h2>Contents</h2>
    {toc}
  </nav>
  <main>
    <h1 class="book-title">Concept-Book: {target_title}</h1>
    <p class="subtitle">Domain: {domain_title}&nbsp;&middot;&nbsp;Generated by SPL stack</p>
    {body}
  </main>
</div>
</body>
</html>"""
