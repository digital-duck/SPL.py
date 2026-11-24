"""`spl3 docs`: write documents about a codebase (a folder or a repository url), one per style. Ported from `graf docs`.

    spl3 docs . --style demo                                       # a slide deck: ./<folder>.demo.html
    spl3 docs . --style demo,tutorial,user-guide --out-dir docs/spl3-docs     # three files in one folder
    spl3 docs https://github.com/org/repo --style tutorial --format markdown  # cloned to the temp area first: ./repo.tutorial.md
    spl3 docs ./proj --style custom --prompt "a one-page FAQ"      # your own instructions (--prompt TEXT or @FILE)

The default format is html (the Markdown styles are converted to a page, `md2html.py`); `--format markdown` keeps Markdown (a deck is html only).
A program reads the codebase into a digest (`gather.py`), the SPL workflow `doc_it.spl` plans and writes (two model calls), a program assembles
and checks the page (`assemble.py`), and if the check fails the workflow's `doc_fix` fixes it once (one more call). The styles are files
(`spl3/docs/styles/*.md`): edit them to change a style.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional, Tuple

import click

HERE = Path(__file__).resolve().parent
STYLES_DIR = HERE / "styles"
WORKFLOW = HERE / "doc_it.spl"
STYLES = ("demo", "tutorial", "user-guide", "custom")
URL = re.compile(r"^(https?://|git@|ssh://|git://)|\.git$")


def work_root() -> Path:
    return Path(tempfile.gettempdir()) / "spl3-docs"


def is_url(source: str) -> bool:
    return bool(URL.search(source))


def repo_name(url: str) -> str:
    return re.sub(r"\.git$", "", url.rstrip("/").split("/")[-1].split(":")[-1]) or "repo"


def clone(url: str, ref: Optional[str]) -> Path:
    """Shallow-clone `url` into the temp area (a fresh copy each time) and return the folder."""
    dest = work_root() / f"{repo_name(url)}-{hashlib.sha1((url + (ref or '')).encode()).hexdigest()[:8]}"
    if dest.exists():
        shutil.rmtree(dest)                                  # only ever a folder this function made under work_root()
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["git", "clone", "--depth", "1"] + (["--branch", ref] if ref else []) + ["--", url, str(dest)]
    done = subprocess.run(cmd, capture_output=True, text=True)
    if done.returncode != 0:
        raise click.ClickException(f"git clone failed: {(done.stderr or done.stdout).strip().splitlines()[-1] if (done.stderr or done.stdout).strip() else 'no output'}")
    return dest


def style_file(style: str, prompt: Optional[str], fmt: Optional[str], folder: Path) -> Tuple[Path, str]:
    """The style file to give the recipe, and its format. A built-in style is used as it is; `custom` is built from --prompt."""
    if style != "custom":
        if prompt:
            raise click.UsageError("--prompt goes with --style custom")
        path = STYLES_DIR / f"{style}.md"
        got = re.search(r"^format:\s*(\w+)", path.read_text(encoding="utf-8"), re.M)
        return path, got.group(1) if got else "markdown"
    if not prompt:
        raise click.UsageError("--style custom needs --prompt TEXT (or --prompt @FILE) saying how the document should be built and structured")
    text = Path(prompt[1:]).expanduser().read_text(encoding="utf-8") if prompt.startswith("@") else prompt
    fmt = "markdown"      # a model writes Markdown; an HTML page is made from it (spl3/docs/md2html.py)
    body = (STYLES_DIR / "custom.md").read_text(encoding="utf-8").replace("{{PROMPT}}", text.strip())
    path = folder / "custom.md"
    path.write_text(f"---\nformat: {fmt}\nmin_sections: 2\n---\n{body}", encoding="utf-8")
    return path, fmt


def safe_name(name: str) -> str:
    """A --name as a file-name part: no folders, no spaces."""
    got = re.sub(r"[^\w.\-]+", "-", name.strip()).strip("-.")
    if not got:
        raise click.UsageError("--name has no usable characters (letters, digits, - _ . )")
    return got


def run_script(script: str, job: dict) -> dict:
    """Run one of the deterministic programs (gather.py, assemble.py): JSON on stdin, JSON on stdout, no model."""
    done = subprocess.run([sys.executable, "-I", str(HERE / script)], input=json.dumps(job), capture_output=True, text=True)
    if done.returncode != 0:
        raise click.ClickException((done.stderr or f"{script} failed").strip())
    return json.loads(done.stdout)


def run_spl(main: str, llm: str, params: dict, log: Path) -> None:
    """Run one workflow of doc_it.spl through `spl3 run` (checkpoints off: a document is cheap to redo)."""
    cmd = [sys.executable, "-c", "from spl3.cli import main; main()", "run", str(WORKFLOW), "--main", main, "--llm", llm,
           "--persistence", "none", "--no-log"]
    for k, v in params.items():
        cmd += ["-p", f"{k}={v}"]
    done = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    log.write_text(done.stdout, encoding="utf-8")
    if done.returncode != 0:
        raise click.ClickException(f"the {main} run failed (log {log}):\n" + "\n".join(done.stdout.strip().splitlines()[-12:]))


@click.command("docs", short_help="Write documents (deck, tutorial, user guide, or your own) about a codebase.")
@click.argument("source")
@click.option("--style", "styles", default="demo", show_default=True,
              help="one or more, comma separated: demo (a slide deck, HTML only), tutorial, user-guide, custom (your --prompt); e.g. demo,tutorial,user-guide")
@click.option("--prompt", default=None, help="with --style custom: how the document should be built and structured (text, or @FILE)")
@click.option("--format", "fmt", type=click.Choice(["html", "markdown"]), default="html", show_default=True,
              help="html pages (a PDF is one print away) or markdown; a deck is always html; a --out ending in .md/.html decides for itself")
@click.option("--name", default=None, help="what to call the project in file names and titles (default: the folder's name, or the repository's name for a url)")
@click.option("--out-dir", "out_dir", default=None, type=click.Path(file_okay=False), help="the folder for the files, one per style: <name>.<style>.html|md (default: the current folder; made if missing)")
@click.option("--out", "-o", default=None, help="one style only: the file to write (instead of --out-dir)")
@click.option("--force", is_flag=True, help="overwrite files that exist")
@click.option("--ref", default=None, help="for a repository url: the branch or tag to clone")
@click.option("--llm", "llm", default="claude_cli:claude-sonnet-5-5", show_default=True, metavar="ADAPTER:MODEL", help="the model (billed)")
@click.option("--budget", type=int, default=60000, show_default=True, help="characters of the source to put in the digest")
@click.option("--margin", type=float, default=0.5, show_default=True, help="safety margin on the model-call cap (cap = ceil(calls x (1 + margin)))")
@click.option("--max-calls", type=int, default=None, help="refuse to run a style when its cap on model calls is above this")
@click.option("--dry-run", is_flag=True, help="read the codebase and print the plan (files, size, model calls, output files); no model is called")
def cmd_docs(source, styles, prompt, fmt, name, out_dir, out, force, ref, llm, budget, margin, max_calls, dry_run):
    """Write one document per style about SOURCE (a folder or a repository url)."""
    wanted = list(dict.fromkeys(x.strip() for x in styles.split(",") if x.strip()))
    bad = [x for x in wanted if x not in STYLES]
    if not wanted or bad:
        raise click.UsageError(f"unknown style {', '.join(bad) or '(none)'}; choose from {', '.join(STYLES)} (comma separated for several)")
    if out and len(wanted) > 1:
        raise click.UsageError("--out names one file; with several styles use --out-dir")
    if out and out_dir:
        raise click.UsageError("give --out or --out-dir, not both")
    if prompt and "custom" not in wanted:
        raise click.UsageError("--prompt goes with --style custom")
    if is_url(source):
        if dry_run:
            click.echo(f"(cloning {source} into {work_root()} to read it)")
        root = clone(source, ref)
    else:
        if ref:
            raise click.UsageError("--ref goes with a repository url")
        root = Path(source).expanduser().resolve()
        if not root.is_dir():
            raise click.ClickException(f"no such folder: {source}")
    failed = []
    for style in wanted:
        if len(wanted) > 1:
            click.echo(f"\n== {style} ==")
        try:
            make_one(root, source, style, prompt, fmt, name, out_dir, out, force, llm, budget, margin, max_calls, dry_run)
        except click.ClickException as e:
            if len(wanted) == 1:
                raise
            click.echo(f"error: {e.format_message()}")
            failed.append(style)
    if failed:
        raise click.ClickException(f"not written: {', '.join(failed)}")


CALLS = 3          # plan, write, and (only if the check fails) fix


def make_one(root, source, style, prompt, fmt, name, out_dir, out, force, llm, budget, margin, max_calls, dry_run):
    """One style: plan, run the workflow, check, fix once if needed, convert if an HTML page was asked for, write the file."""
    import math

    folder = work_root() / f"run-{time.strftime('%Y%m%d-%H%M%S')}-{style}"
    folder.mkdir(parents=True, exist_ok=True)
    guide, kind = style_file(style, prompt, None, folder)       # kind: the format the workflow writes (a deck: html; the others: markdown)
    title, name = (name.strip(), safe_name(name)) if name else (root.name, root.name)      # title: as typed; name: the file-name part
    if out and Path(out).suffix.lower() in (".md", ".html", ".htm"):
        want = "html" if Path(out).suffix.lower() in (".html", ".htm") else "markdown"
    else:
        want = fmt
    if kind == "html":
        if want == "markdown":
            raise click.ClickException(f"style {style} is a slide deck and only comes as html (use --format html, or drop it from --style)")
        want = "html"
    ext = "html" if want == "html" else "md"
    if out:
        target = Path(out)
        if target.suffix.lower() not in (".html", ".htm", ".md"):
            target = target.with_name(target.name + f".{ext}")
        elif kind == "html" and target.suffix.lower() == ".md":
            target = target.with_suffix(".html")
            click.echo(f"note: style {style} writes html, so the file is {target.name}")
    else:
        target = Path(out_dir or ".").expanduser().resolve() / f"{name}.{style}.{ext}"
    to_html = kind != "html" and want == "html"      # a Markdown style, an HTML page wanted: convert at the end
    if target.exists() and not force:
        raise click.ClickException(f"{target} exists (use --force to overwrite, or another --out-dir)")

    cap = math.ceil(CALLS * (1 + margin))
    info = run_script("gather.py", {"source": str(root), "style_guide": str(guide), "budget": budget, "name": title})
    click.echo("plan")
    click.echo(f"  source       {root}" + (f"  (cloned from {source})" if is_url(source) else ""))
    click.echo(f"  style        {style}  ({want})")
    click.echo(f"  reads        {len(info['files'])} file(s), {len(info['digest'])} characters of digest")
    click.echo(f"  model calls  {CALLS} expected (2 when the check passes), cap {cap}")
    click.echo(f"  writes       {target}")
    if max_calls is not None and cap > max_calls:
        raise click.ClickException(f"the cap {cap} is above --max-calls {max_calls}")
    if dry_run:
        click.echo("dry run: nothing was run")
        for f in info["files"]:
            click.echo(f"    {f}")
        return

    guide_file, digest_file, body_file = folder / "style_guide.txt", folder / "digest.txt", folder / "body.txt"
    guide_file.write_text(info["style_guide"], encoding="utf-8")
    digest_file.write_text(info["digest"], encoding="utf-8")
    gathered = json.dumps(info)
    base = {"guide_file": guide_file, "digest_file": digest_file, "body_file": body_file}
    click.echo(f"running ({CALLS} model calls at most) ...")
    run_spl("doc_draft", llm, base, folder / "draft.log")
    result = run_script("assemble.py", {"body": body_file.read_text(encoding="utf-8"), "gathered": gathered, "source": str(root)})
    if not result.get("ok"):
        problems = folder / "problems.txt"
        problems.write_text("\n".join(map(str, result.get("errors", []) + result.get("warnings", []))), encoding="utf-8")
        click.echo("the check found problems; fixing once ...")
        run_spl("doc_fix", llm, {**base, "problems_file": problems}, folder / "fix.log")
        result = run_script("assemble.py", {"body": body_file.read_text(encoding="utf-8"), "gathered": gathered, "source": str(root)})
    target.parent.mkdir(parents=True, exist_ok=True)
    document = result["document"]
    if to_html:
        from .md2html import convert
        document = convert(document, title)
    target.write_text(document, encoding="utf-8")
    for w in result.get("warnings", []):
        click.echo(f"warning: {w}")
    for e in result.get("errors", []):
        click.echo(f"error: {e}")
    click.echo(f"wrote {target}  ({result.get('sections', 0)} sections; run folder {folder})")
    if not result.get("ok"):
        raise click.ClickException("the document was written but it did not pass the check (see the errors above)")
