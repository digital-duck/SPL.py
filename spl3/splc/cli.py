"""
splc — SPL Compiler CLI
Translates a .spl logical-view script into a physical implementation
in a target language / framework.

Design principle (DODA):
  The .spl file is the invariant logical view.
  splc produces a hardware/framework-specific physical artifact.
  Changing the deployment target only requires re-running splc.

Usage examples:
  # Compile to Go (LLM's pretrained knowledge only)
  splc --spl cookbook/05_self_refine/self_refine.spl --lang go

  # Compile to LangGraph Python with a reference codebase
  splc --spl cookbook/05_self_refine/self_refine.spl --lang python/langgraph \\
       --references https://github.com/langchain-ai/langgraph

  # Compile with multiple references, custom output dir, stronger model
  splc --spl my_workflow.spl --lang python/crewai \\
       --references https://github.com/crewAIInc/crewAI \\
       --references https://github.com/langchain-ai/langchain \\
       --out-dir ./targets/python/crewai \\
       --model claude-opus-4-6

  # Dry-run: print the prompt without calling the LLM
  splc --spl my_workflow.spl --lang go --dry-run

  # Compile without RAG examples (faster, less context)
  splc --spl my_workflow.spl --lang python/langgraph --no-rag
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import click

# ── Constants ─────────────────────────────────────────────────────────────────

SUPPORTED_LANGS: dict[str, dict] = {
    "go": {
        "label":     "Go (stdlib + Ollama REST API)",
        "ext":       ".go",
        "extras":    ["go.mod"],
        "framework": None,
    },
    "python": {
        "label":     "Python (plain, minimal deps)",
        "ext":       ".py",
        "extras":    ["requirements.txt"],
        "framework": None,
    },
    "python/langgraph": {
        "label":     "Python — LangGraph",
        "ext":       ".py",
        "extras":    ["requirements.txt"],
        "framework": "langgraph",
    },
    "python/crewai": {
        "label":     "Python — CrewAI",
        "ext":       ".py",
        "extras":    ["requirements.txt"],
        "framework": "crewai",
    },
    "python/autogen": {
        "label":     "Python — AutoGen",
        "ext":       ".py",
        "extras":    ["requirements.txt"],
        "framework": "autogen",
    },
    "python/liquid": {
        "label":     "Python — Liquid AI (LFM via Ollama / OpenRouter)",
        "ext":       ".py",
        "extras":    ["requirements.txt"],
        "framework": "liquid",
    },
    "python/pocketflow": {
        "label":     "Python — PocketFlow (minimalist ETL-style LLM orchestration)",
        "ext":       ".py",
        "extras":    ["requirements.txt"],
        "framework": "pocketflow",
    },
    "ts": {
        "label":     "TypeScript (Node 18+ / fetch + Ollama REST API)",
        "ext":       ".ts",
        "extras":    [],
        "framework": None,
    },
    # Planned — not yet implemented
    # "swift":  {...},
    # "snap":   {...},
    # "edge":   {...},
}

# Languages with a deterministic rule-based transpiler — default path (no LLM needed).
# All other languages fall through to LLM compilation.
DETERMINISTIC_LANGS: set[str] = {"go", "ts", "python/langgraph", "python/pocketflow"}

SUPPORTED_MODELS = [
    "claude-sonnet-4-6",
    "claude-opus-4-6",
]

SPL30_ROOT    = Path(__file__).resolve().parents[2]   # spl/splc/cli.py → SPL30/
RAG_STORE_DIR = SPL30_ROOT / "spl" / "rag" / ".chroma"


def _make_out_stem(alias: str, input_stem: str) -> str:
    """Return a timestamped stem: <alias>-<input_stem>-<YYYYMMDD_HHMMSS>."""
    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{alias}-{input_stem}-{ts}"


# ── CLI group ─────────────────────────────────────────────────────────────────

@click.group(name="splc", context_settings={"help_option_names": ["-h", "--help"]})
def splc():
    """splc — SPL Compiler: translate .spl logical views into physical implementations.

    \b
    Subcommands:
      compile   Compile a .spl file to a target language / framework.
      describe  Describe a compiled target implementation as a -spec.md file.
                The spec feeds back into text2spl → .spl → splc (reverse pipeline).
    """


@splc.command(name="compile", context_settings={"help_option_names": ["-h", "--help"]})

# ── Positional ────────────────────────────────────────────────────────────────
@click.argument(
    "spl_path",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
)

# ── Required option ───────────────────────────────────────────────────────────
@click.option(
    "--lang",
    required=True,
    type=click.Choice(list(SUPPORTED_LANGS), case_sensitive=False),
    help=(
        "Target language / framework. "
        f"Supported: {', '.join(SUPPORTED_LANGS)}."
    ),
)

# ── With defaults ─────────────────────────────────────────────────────────────
@click.option(
    "--out-dir", "out_dir",
    default=None,
    type=click.Path(file_okay=False, writable=True, path_type=Path),
    help=(
        "Output directory for generated files. "
        "Default: targets/<lang>/ relative to the .spl file's parent."
    ),
)
@click.option(
    "--adapter",
    default="claude_cli",
    show_default=True,
    metavar="NAME",
    help="LLM adapter to use for --llm compilation (default: claude_cli).",
)
@click.option(
    "--model",
    default=None,
    metavar="MODEL",
    help="Model override for the adapter (default: adapter's own default).",
)
@click.option(
    "--rag/--no-rag",
    "use_rag",
    default=True,
    show_default=True,
    help=(
        "Include RAG examples from the shared SPL recipe store as few-shot context. "
        "Requires the store to be indexed (run spl/rag/index_recipes.py first)."
    ),
)
@click.option(
    "--rag-k",
    default=3,
    show_default=True,
    type=click.IntRange(1, 10),
    help="Number of RAG examples to include when --rag is on.",
)

# ── Optional ──────────────────────────────────────────────────────────────────
@click.option(
    "--references", "references",
    multiple=True,
    metavar="URL_OR_PATH",
    help=(
        "Reference codebase(s) to ground the LLM's output. "
        "Accepts GitHub URLs or local directory paths. "
        "Repeat to add multiple references. "
        "If omitted, compilation relies on the LLM's pretrained knowledge."
    ),
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite existing files in --out-dir. Default: abort if files exist.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Print the compiled prompt without calling the LLM. Useful for debugging.",
)
@click.option(
    "--no-readme",
    is_flag=True,
    default=False,
    help="Skip generating readme.md alongside the implementation.",
)
@click.option(
    "--llm",
    is_flag=True,
    default=False,
    help=(
        "Force LLM compilation even when a deterministic transpiler is available. "
        f"Required for targets without a deterministic transpiler "
        f"({', '.join(sorted(set(SUPPORTED_LANGS) - DETERMINISTIC_LANGS))})."
    ),
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    default=False,
    help="Print progress and token counts.",
)
@click.option(
    "--prompt", "prompt_debug",
    is_flag=True,
    default=False,
    help="Display the LLM prompt and exit.",
)
def cmd_compile(
    spl_path:   Path,
    lang:       str,
    out_dir:    Path | None,
    adapter:    str,
    model:      str | None,
    use_rag:    bool,
    rag_k:      int,
    references: tuple[str, ...],
    overwrite:  bool,
    dry_run:    bool,
    no_readme:  bool,
    llm:        bool,
    verbose:    bool,
    prompt_debug: bool,
) -> None:
    """splc — SPL Compiler: translate a .spl logical view into a physical implementation."""

    lang_meta = SUPPORTED_LANGS[lang]

    # Deterministic transpiler is the default for supported langs; --llm opts into LLM.
    use_deterministic = lang in DETERMINISTIC_LANGS and not llm

    # ── Resolve output directory ──────────────────────────────────────────────
    if out_dir is None:
        # Default: targets/<lang-slug>/ next to the .spl file
        lang_slug = lang.replace("/", "_")
        out_dir = spl_path.parent / "targets" / lang_slug
    out_dir.mkdir(parents=True, exist_ok=True)

    recipe_name   = spl_path.stem                  # e.g. "self_refine"
    impl_filename = f"{recipe_name}_{lang.replace('/', '_')}{lang_meta['ext']}"
    impl_path     = out_dir / impl_filename
    readme_path   = out_dir / "readme.md"
    manifest_path = out_dir / "splc_manifest.json"

    # ── Overwrite guard ───────────────────────────────────────────────────────
    if not overwrite and impl_path.exists():
        click.echo(
            f"ERROR: {impl_path} already exists. "
            "Use --overwrite to replace it.",
            err=True,
        )
        sys.exit(1)

    spl_source = spl_path.read_text(encoding="utf-8")

    if use_deterministic:
        from spl.lexer import Lexer
        from spl3.parser import SPL3Parser

        tokens = Lexer(spl_source).tokenize()
        program = SPL3Parser(tokens).parse()

        if lang == "go":
            from spl3.splc.transpiler_go import GoTranspiler

            if verbose:
                click.echo(f"splc: using deterministic Go transpiler for {spl_path.name}")

            transpiler = GoTranspiler(recipe_name)
            impl_code = transpiler.transpile(program)
            readme_text = f"# {recipe_name} (Deterministic Go)\n\nGenerated by splc --deterministic"

        elif lang == "python/langgraph":
            from spl3.splc.transpiler_langgraph import LangGraphTranspiler

            if verbose:
                click.echo(
                    f"splc: using deterministic LangGraph transpiler for {spl_path.name}"
                )

            transpiler = LangGraphTranspiler(recipe_name, spl_dir=spl_path.parent)
            impl_code = transpiler.transpile(program)
            readme_text = (
                f"# {recipe_name} (Deterministic Python/LangGraph)\n\n"
                f"Generated by splc --deterministic --lang python/langgraph"
            )

        elif lang == "ts":
            from spl3.splc.transpiler_ts import TypeScriptTranspiler

            if verbose:
                click.echo(f"splc: using deterministic TypeScript transpiler for {spl_path.name}")

            transpiler = TypeScriptTranspiler(recipe_name)
            impl_code = transpiler.transpile(program)
            readme_text = (
                f"# {recipe_name} (Deterministic TypeScript)\n\n"
                f"Generated by splc --deterministic --lang ts\n\n"
                f"## Run\n\n"
                f"```bash\nnpx tsx {recipe_name}_ts.ts --task \"What are the benefits of meditation?\"\n```"
            )

        elif lang == "python/pocketflow":
            from spl3.splc.transpiler_pocketflow import PocketFlowTranspiler

            if verbose:
                click.echo(
                    f"splc: using deterministic PocketFlow transpiler for {spl_path.name}"
                )

            transpiler = PocketFlowTranspiler(recipe_name)
            impl_code = transpiler.transpile(program)
            readme_text = (
                f"# {recipe_name} (Deterministic Python/PocketFlow)\n\n"
                f"Generated by splc --deterministic --lang python/pocketflow\n\n"
                f"## Install\n\n"
                f"```bash\npip install pocketflow click\n```\n\n"
                f"## Run\n\n"
                f"```bash\npython {recipe_name}_python_pocketflow.py --task \"Your task here\"\n```\n\n"
                f"## ETL Mapping\n\n"
                f"| PocketFlow | ETL role | SPL construct |\n"
                f"|------------|----------|---------------|\n"
                f"| `prep(shared)` | Extract | read `@variables` from shared store |\n"
                f"| `exec(prep_res)` | Transform | `GENERATE` / LLM call |\n"
                f"| `post(shared, prep_res, exec_res)` | Load | write results back + return action |\n"
                f"| `shared` dict | Staging area | SPL `@variable` scope |\n"
                f"| `Flow(start=...)` | Pipeline DAG | `WORKFLOW` + control flow |\n"
            )

        else:
            click.echo(f"ERROR: Deterministic transpiler not available for {lang}.", err=True)
            sys.exit(1)
    else:
        if verbose:
            click.echo(f"splc: {spl_path.name}  →  {lang}  ({lang_meta['label']})")
            click.echo(f"      model={model}  rag={use_rag}(k={rag_k})  refs={len(references)}")

        # ── Fetch references ──────────────────────────────────────────────────────
        ref_context = _fetch_references(references, verbose=verbose)

        # ── RAG few-shot examples ─────────────────────────────────────────────────
        rag_context = ""
        if use_rag:
            rag_context = _fetch_rag_examples(spl_source, lang, k=rag_k, verbose=verbose)

        # ── Build prompt ──────────────────────────────────────────────────────────
        prompt = _build_prompt(
            spl_source   = spl_source,
            spl_filename = spl_path.name,
            lang         = lang,
            lang_meta    = lang_meta,
            ref_context  = ref_context,
            rag_context  = rag_context,
            recipe_name  = recipe_name,
            gen_readme   = not no_readme,
        )

        if dry_run or prompt_debug:
            label = "DRY RUN" if dry_run else "LLM PROMPT"
            click.echo("=" * 70)
            click.echo(f"{label} — prompt that would be sent to the LLM:")
            click.echo("=" * 70)
            click.echo(prompt)
            click.echo(f"\n[Prompt length: {len(prompt)} chars / ~{len(prompt)//4} tokens]")
            return

        # ── Call LLM ──────────────────────────────────────────────────────────────
        if verbose:
            click.echo(f"Calling {adapter} / {model or '(default)'} ...")

        impl_code, readme_text, _test_data = compile_llm_code(prompt, adapter=adapter, model=model, verbose=verbose)

    # ── Write output files ────────────────────────────────────────────────────
    impl_path.write_text(impl_code, encoding="utf-8")
    click.echo(f"  Written: {impl_path}")

    if not no_readme and readme_text:
        readme_path.write_text(readme_text, encoding="utf-8")
        click.echo(f"  Written: {readme_path}")

    _write_manifest(
        manifest_path = manifest_path,
        spl_path      = spl_path,
        lang          = lang,
        adapter       = adapter,
        model         = model,
        references    = list(references),
        use_rag       = use_rag,
        rag_k         = rag_k,
        impl_path     = impl_path,
    )
    click.echo(f"  Written: {manifest_path}")
    click.echo(f"\nsplc done: {spl_path.name} → {lang} [{lang_meta['label']}]")


# ── Reference fetcher ─────────────────────────────────────────────────────────

def _fetch_references(refs: tuple[str, ...], *, verbose: bool) -> str:
    """Fetch reference content from URLs or local paths.

    GitHub repo URLs: fetch README.md + key source files (heuristic top-level *.py/*.go).
    Local paths:      read all source files matching the target extension.
    Returns a formatted block for injection into the prompt.
    """
    if not refs:
        return ""

    parts: list[str] = []
    for ref in refs:
        if verbose:
            click.echo(f"  Fetching reference: {ref}")
        try:
            content = _fetch_one_reference(ref)
            if content:
                parts.append(f"## Reference: {ref}\n\n{content}")
        except Exception as exc:
            click.echo(f"  WARN: could not fetch reference {ref}: {exc}", err=True)

    if not parts:
        return ""

    return "# Reference Codebases\n\n" + "\n\n---\n\n".join(parts)


def _fetch_one_reference(ref: str) -> str:
    """Fetch a single reference. Returns text content."""
    import urllib.request

    if ref.startswith("http://") or ref.startswith("https://"):
        # GitHub URL → convert to raw README fetch
        # e.g. https://github.com/langchain-ai/langgraph
        #   →  https://raw.githubusercontent.com/langchain-ai/langgraph/main/README.md
        raw_url = _github_to_raw_readme(ref)
        with urllib.request.urlopen(raw_url, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace")[:8000]  # cap at 8k chars
    else:
        # Local path — read all source files
        p = Path(ref)
        if not p.exists():
            raise FileNotFoundError(f"Reference path not found: {p}")
        if p.is_file():
            return p.read_text(encoding="utf-8")[:8000]
        # Directory: read README + source files
        parts = []
        for readme in sorted(p.glob("README*")):
            parts.append(readme.read_text(encoding="utf-8")[:4000])
        for src in sorted(p.rglob("*.py"))[:5]:   # first 5 source files
            parts.append(f"# {src.name}\n" + src.read_text(encoding="utf-8")[:2000])
        return "\n\n".join(parts)[:10000]


def _github_to_raw_readme(url: str) -> str:
    """Convert a GitHub repo URL to a raw README URL."""
    # https://github.com/owner/repo → https://raw.githubusercontent.com/owner/repo/main/README.md
    url = url.rstrip("/")
    if "github.com" in url and "raw.githubusercontent.com" not in url:
        url = url.replace("github.com", "raw.githubusercontent.com")
        return url + "/main/README.md"
    return url


# ── RAG examples ─────────────────────────────────────────────────────────────

def _fetch_rag_examples(spl_source: str, lang: str, *, k: int, verbose: bool, query: str | None = None) -> str:
    """Retrieve k similar recipes already compiled to the target lang from the RAG store.

    Args:
        spl_source: SPL source text (used to derive query via _spl_to_query if query is None).
        query:      Override the RAG query directly (e.g. when calling from vibe with natural language).
    """
    if not RAG_STORE_DIR.exists():
        if verbose:
            click.echo("  RAG store not found — skipping few-shot examples.")
            click.echo("  Run: python spl/rag/index_recipes.py")
        return ""

    try:
        spl_dir = str(SPL30_ROOT / "spl")
        if spl_dir not in sys.path:
            sys.path.insert(0, spl_dir)
        from rag.search import search_recipes
    except ImportError:
        if verbose:
            click.echo("  WARN: spl.rag not importable — skipping RAG context.")
        return ""

    # Use the provided query directly, or derive one from the SPL source
    query = query or _spl_to_query(spl_source)
    if verbose:
        click.echo(f"  RAG query: {query[:60]}...")

    hits = search_recipes(query, k=k)
    if not hits:
        return ""

    lang_label = SUPPORTED_LANGS[lang]["label"]
    parts = [f"# Similar SPL Recipes (few-shot context)\n"
             f"The following recipes implement similar patterns. "
             f"Use them to understand the SPL idioms before generating {lang_label} code.\n"]
    for h in hits:
        parts.append(
            f"## Example: {h.name}  [score={h.score:.3f}]\n"
            f"{h.description}\n\n"
            f"```spl\n{h.spl_source[:2000]}\n```"
        )
    return "\n\n".join(parts)


def _spl_to_query(spl_source: str) -> str:
    """Extract a short natural-language query from a .spl file for RAG retrieval.

    Skips generic header lines ("Recipe Name:", "File:", "Author:") and returns
    the first meaningful description comment or the WORKFLOW name.
    """
    _SKIP_PREFIXES = ("recipe name", "file:", "author:", "date:", "version:")
    for line in spl_source.splitlines():
        stripped = line.strip()
        if not stripped.startswith("--"):
            continue
        text = stripped.lstrip("- ").strip()
        if len(text) < 10:
            continue
        if any(text.lower().startswith(p) for p in _SKIP_PREFIXES):
            continue
        return text
    # Fall back to WORKFLOW name
    import re
    m = re.search(r"WORKFLOW\s+(\w+)", spl_source, re.IGNORECASE)
    return m.group(1).replace("_", " ") if m else "SPL workflow"


# ── Prompt builder ────────────────────────────────────────────────────────────

def _build_prompt(
    spl_source:   str,
    spl_filename: str,
    lang:         str,
    lang_meta:    dict,
    ref_context:  str,
    rag_context:  str,
    recipe_name:  str,
    gen_readme:   bool,
) -> str:
    """Construct the full compilation prompt sent to the LLM."""

    readme_instruction = (
        "\n\nAfter the implementation, output a `readme.md` section "
        "(starting with `--- README ---` on its own line) that includes: "
        "setup instructions, run command, expected output pattern, "
        "and a table mapping each SPL construct to its equivalent in the target."
        if gen_readme else ""
    )

    sections = [
        _SYSTEM_PROMPT.format(
            lang_label    = lang_meta["label"],
            lang          = lang,
            recipe_name   = recipe_name,
            spl_filename  = spl_filename,
            readme_instr  = readme_instruction,
        ),
    ]

    if rag_context:
        sections.append(rag_context)

    if ref_context:
        sections.append(ref_context)

    sections.append(
        f"# SPL Source to Compile\n\n"
        f"File: `{spl_filename}`\n\n"
        f"```spl\n{spl_source}\n```\n\n"
        f"Generate the {lang_meta['label']} implementation now."
    )

    return "\n\n---\n\n".join(sections)


_SYSTEM_PROMPT = """\
You are `splc`, the SPL Compiler. Your job is to translate a `.spl` script
(the SPL logical view — declarative, hardware-agnostic) into a working
{lang_label} implementation (the physical view).

Rules:
1. Every SPL construct must map to an equivalent in {lang}. Add a comment
   on each translated block showing the original SPL line(s), e.g.:
   `# SPL: GENERATE critique(@current) INTO @feedback`
2. Preserve ALL workflow semantics: WHILE loops, EVALUATE conditions,
   EXCEPTION handlers, CALL sub-workflows, LOGGING statements.
3. Use only the target language's standard patterns for {lang_label}.
   Do not introduce dependencies not required by the SPL logic.
4. Match the INPUT parameter names, types, and defaults exactly.
5. Output ONLY the implementation file content — no explanation before it.
   The file should be ready to run without modification.
6. Use the recipe name `{recipe_name}` as the basis for file/class/function names.
{readme_instr}

Target: {lang_label}
Source file: {spl_filename}\
"""


VIBE_SYSTEM_PROMPT = """\
You are an expert software engineer. Your task is to translate a natural language REQUIREMENT
directly into a working {lang_label} implementation in a single pass.

Rules:
1. The code must be COMPLETE and EXECUTABLE — no placeholder functions, no "TODO" stubs,
   no missing imports. A user must be able to run it immediately after reading the README.
2. Use only the target language's standard patterns for {lang_label}.
3. If using an orchestration framework (PocketFlow, LangGraph, etc.), ensure correct
   node wiring, shared state management, and robust error handling.
4. Preserve ALL workflow semantics implied by the requirement: loops, conditional branches,
   sub-workflow calls, exception handling, and logging.
5. Provide a `__main__` block (or equivalent entry point) that demonstrates the workflow
   end-to-end with a concrete example input.
6. For LLM calls, use a `call_llm(prompt: str, model: str = None) -> str` helper at the
   top of the file. Read the model from an environment variable (e.g. `LLM_MODEL`) with
   a sensible default so users can swap models without editing code.
7. Read API keys from environment variables (e.g. `OPENROUTER_API_KEY`, `OPENAI_API_KEY`).
   Never hardcode credentials.
8. Output ONLY the implementation file content first — no explanation, no preamble.
   The file should be ready to run without modification.
{readme_instr}

Target: {lang_label}
"""


VIBE_README_INSTRUCTION = """\


MANDATORY OUTPUT STRUCTURE — you MUST include all three sections in this exact order:

1. The complete implementation code (first, no preamble).

2. A README section starting with exactly this line on its own:
--- README ---
   Include: overview, requirements (pip install ...), setup (env vars),
   usage with example command and expected output, and a step-by-step
   description of the workflow logic.

3. A TEST DATA section starting with exactly this line on its own:
--- TEST DATA ---
   Provide 2-3 realistic test inputs as a Python dict or JSON array that
   can be passed directly to the main entry point. If the workflow takes
   a question or query, provide example queries. If it takes a document,
   provide a short sample document. Omit only if the workflow has no
   meaningful test inputs (e.g. it generates data from scratch).

ALL THREE SECTIONS ARE REQUIRED. Do not omit any section even if the code is long.\
"""


# ── LLM caller ───────────────────────────────────────────────────────────────

def compile_llm_code(prompt: str, *, adapter: str, model: str | None, verbose: bool, timeout: int | None = None) -> tuple[str, str, str]:
    """Call the specified adapter and return (implementation, readme, test_data)."""
    import asyncio
    try:
        from spl3.adapters import get_adapter
    except ImportError:
        click.echo("ERROR: spl3.adapters not found. Ensure SPL.py is installed.", err=True)
        sys.exit(1)

    adapter_kwargs: dict = {}
    if model:
        adapter_kwargs["model"] = model
    if timeout is not None:
        adapter_kwargs["timeout"] = timeout

    try:
        llm = get_adapter(adapter, **adapter_kwargs)
    except ValueError as exc:
        click.echo(f"ERROR: {exc}", err=True)
        sys.exit(1)

    async def _run() -> str:
        result = await llm.generate(prompt, **({"model": model} if model else {}))
        return result if isinstance(result, str) else getattr(result, "content", str(result))

    raw = asyncio.run(_run())

    if verbose:
        click.echo(f"  LLM response: {len(raw)} chars")

    # Split implementation, readme, and test data (all optional but requested)
    test_data = ""
    if "--- TEST DATA ---" in raw:
        raw, _, test_data = raw.partition("--- TEST DATA ---")
        test_data = test_data.strip()
    if "--- README ---" in raw:
        impl_part, _, readme_part = raw.partition("--- README ---")
        return strip_fences(impl_part), readme_part.strip(), test_data
    return strip_fences(raw), "", test_data


def strip_fences(text: str) -> str:
    """Remove leading/trailing markdown code fences from LLM output."""
    import re
    text = text.strip()
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return text.strip()


# ── Manifest writer ───────────────────────────────────────────────────────────

def _write_manifest(
    manifest_path: Path,
    spl_path:      Path,
    lang:          str,
    adapter:       str,
    model:         str | None,
    references:    list[str],
    use_rag:       bool,
    rag_k:         int,
    impl_path:     Path,
) -> None:
    """Write a splc_manifest.json capturing provenance of the compiled artifact."""
    manifest = {
        "splc_version":    "0.1.0",
        "generated_at":    datetime.now(timezone.utc).isoformat(),
        "source": {
            "spl_file":    str(spl_path.resolve()),
            "spl_sha256":  _sha256(spl_path),
        },
        "target": {
            "lang":        lang,
            "label":       SUPPORTED_LANGS[lang]["label"],
            "output_file": str(impl_path.resolve()),
        },
        "compilation": {
            "adapter":     adapter,
            "model":       model,
            "references":  references,
            "rag_enabled": use_rag,
            "rag_k":       rag_k if use_rag else 0,
        },
        "doda_note": (
            "This file is a splc-compiled physical artifact. "
            "The source .spl file is the invariant logical view. "
            "To retarget, run: splc --spl <source.spl> --lang <new-target>"
        ),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def _sha256(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


# ── splc describe ─────────────────────────────────────────────────────────────

_SPLC_DESCRIBE_PROMPT = """\
You are an expert in SPL (Structured Prompt Language) and LLM workflow orchestration.
SPL key constructs are:

  WORKFLOW <name>          — declares a named multi-step LLM orchestration workflow
  CREATE FUNCTION <name>   — reusable prompt template with {{param}} slots
  GENERATE <fn>(...) INTO @<var>   — LLM call, stores result in a variable
  CALL <tool>(...) INTO @<var>     — side-effect tool call (file write, HTTP, etc.)
  WHILE <cond> DO ... END  — loop until condition is false
  EVALUATE @<var> WHEN contains('...') THEN ... ELSE ... END  — branch on LLM output
  RETURN @<var> WITH <k>=<v>, ...  — return with metadata (status, iterations, etc.)
  EXCEPTION WHEN <Type> THEN ...   — named exception handler

IMPORTANT — suppress trivial "default" transitions:
  In PocketFlow and similar frameworks, nodes return a `"default"` action token simply
  to advance to the next node in a linear chain. This is NOT a meaningful control-flow
  decision and must NOT appear in the spec or construct mapping as "RETURN default".
  Only mention RETURN when the status value is non-trivial (e.g. "done", "retry",
  "error", "continue") AND it drives a real branch or loop condition.

You are given a {lang_label} implementation of an LLM workflow.
Your task is to produce a functional specification in plain English that:
  (a) is rich enough to regenerate the equivalent SPL workflow using text2spl
  (b) documents the mapping from {lang_label} idioms back to SPL constructs

Structure your output as Markdown with these sections IN ORDER:

## Summary
2-3 sentences of plain English. What this does, why it exists, and who benefits.
No jargon, no bullet points. Readable by a non-technical stakeholder.

## Detailed Specification

### 1. Purpose
One sentence: what this implementation accomplishes for the end user.

### 2. High-level Description
Write 4-6 sentences of flowing prose (no bullet points).
Describe what this workflow does using SPL construct names wherever they apply.
Cover: pattern/technique, each logical function (and its prompt role), control flow
expressed as WHILE/EVALUATE/RETURN (only when non-trivial), multi-model design,
side-effects, exception handling. Do NOT mention "default" action tokens — omit them
entirely; they are implicit linear flow, not worth documenting.
This section will be used directly as the text2spl input prompt — make it complete.

### 3. SPL ↔ {lang_label} Construct Mapping
A Markdown table — columns: SPL Construct | {lang_label} Equivalent | Notes.
Cover every major mapping: WORKFLOW→, CREATE FUNCTION→, GENERATE→, EVALUATE→,
WHILE→, EXCEPTION→, shared state (SPL @vars)→.
Only include RETURN→ if a non-default status token (e.g. "done", "retry") drives
a real branch or terminates a loop. Skip it for linear chains where every node
simply returns "default".

### 4. Logical Functions / Prompts
For each logical function (prompt template) found in the implementation:
  - Name
  - Role in the workflow
  - Key prompt conventions (sentinel tokens, scoring, output format)

### 5. Control Flow
Describe the execution path: initial step → loop condition → branch logic → termination.
Use SPL construct names (WHILE, EVALUATE, RETURN WITH status=) only when non-trivial.
Do NOT say "each step returns default" — that is implicit and adds no information.

### 6. How to Regenerate as SPL
```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "<paste Section 1 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```

{lang_label} Implementation:
```
{source}
```

Write the specification now.
"""

_DESCRIBE_TEXT_PROMPT = """\
You are a precise and concise technical writer.

Your task is to read the following text and produce a well-structured summary and analysis.

Structure your output as Markdown with these sections IN ORDER:

## Summary
2-3 sentences of plain English capturing the core message, argument, or finding.
Readable by a non-technical audience. No jargon unless essential.

## Key Points
Bullet list of 3-7 most important ideas, facts, or conclusions from the text.

## Details
A more thorough analysis covering:
- Main themes or topics
- Supporting evidence or methodology (if applicable)
- Any notable structure, framing, or rhetorical choices
- Gaps, limitations, or open questions (if applicable)

## One-line Takeaway
A single sentence someone could tweet.

Text to analyse:
```
{source}
```

Write the summary and analysis now.
"""

# File extensions we recognise as source code (use code prompt)
_CODE_EXTENSIONS = {
    ".py":   "Python",
    ".ts":   "TypeScript",
    ".go":   "Go",
    ".js":   "JavaScript",
    ".spl":  "SPL",
    ".mmd":  "Mermaid",
    ".cpp":  "C++",
    ".c":    "C",
    ".java": "Java",
    ".rs":   "Rust",
    ".rb":   "Ruby",
    ".cs":   "C#",
    ".kt":   "Kotlin",
    ".swift": "Swift",
    ".sql":  "SQL",
    ".sh":   "Shell",
}

# File extensions we recognise as target implementations (for splc describe CLI)
_IMPL_EXTENSIONS = {
    ".py":  "Python",
    ".ts":  "TypeScript",
    ".go":  "Go",
    ".js":  "JavaScript",
}


def _lang_label_from_path(path: Path) -> str:
    """Infer a human-readable lang label from the file path / name."""
    name = path.stem.lower()
    if "pocketflow" in name:
        return "Python — PocketFlow"
    if "langgraph" in name:
        return "Python — LangGraph"
    if "crewai" in name:
        return "Python — CrewAI"
    if "autogen" in name:
        return "Python — AutoGen"
    ext = path.suffix.lower()
    # Prefer broader _CODE_EXTENSIONS so .spl, .mmd, .rs, etc. get proper labels
    return _CODE_EXTENSIONS.get(ext, _IMPL_EXTENSIONS.get(ext, "Unknown"))


@splc.command(name="describe", context_settings={"help_option_names": ["-h", "--help"]})
@click.argument(
    "impl_path",
    type=click.Path(exists=True, readable=True, path_type=Path),
)
@click.option(
    "--lang", "lang_label",
    default=None,
    metavar="LABEL",
    help=(
        "Human-readable target label, e.g. 'Python — PocketFlow'. "
        "Auto-detected from filename if omitted."
    ),
)
@click.option(
    "--adapter",
    default="ollama",
    show_default=True,
    help="LLM adapter to use for generation.",
)
@click.option(
    "--model",
    default=None,
    metavar="MODEL",
    help="Model override for the adapter.",
)
@click.option(
    "--out-dir",
    "spec_dir",
    default=None,
    type=click.Path(file_okay=False, writable=True, path_type=Path),
    help="Output directory for the spec file (default: same directory as IMPL_PATH).",
)
@click.option(
    "-o", "--output",
    "output_path",
    default=None,
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    help="Full output path for the spec file (overrides --spec-dir and auto-generated name).",
)
@click.option(
    "--include-docs",
    is_flag=True,
    default=False,
    help="Also include README.md (if present) to give the LLM original intent context.",
)
@click.option(
    "--prompt", "prompt_debug",
    is_flag=True,
    default=False,
    help="Display the LLM prompt and exit.",
)
def cmd_describe(impl_path: Path, lang_label: str | None, adapter: str, model: str | None, spec_dir: Path | None, output_path: Path | None, include_docs: bool, prompt_debug: bool) -> None:
    """Describe any source file or folder as a structured spec / summary.

    \b
    SOURCE can be:
      - a single file: .spl, .mmd, .py, .ts, .go, .js, .cpp, .java, .rs, and more
      - a directory — all recognised source files are gathered and described together
      - code files  → functional spec (Summary + Detailed Specification)
      - other files → structured summary (Summary + Key Points + …)

    \b
    The generated spec feeds into the reverse pipeline:
      text2spl (Section 1 → .spl) → splc compile → any target

    \b
    Examples:
      spl3 splc describe cookbook/05_self_refine/self_refine.spl
      spl3 splc describe targets/python_pocketflow/self_refine_python_pocketflow.py
      spl3 splc describe targets/python_pocketflow/  --lang "Python — PocketFlow"
      spl3 splc describe langgraph/self_refine_langgraph.py --adapter claude_cli
      spl3 splc describe paper.pdf --out-dir spec/
    """
    import asyncio

    if impl_path.is_dir():
        impl_files = sorted(
            f for f in impl_path.iterdir()
            if f.suffix.lower() in _CODE_EXTENSIONS and not f.name.startswith(".")
        )
        if not impl_files:
            raise click.ClickException(
                f"No recognised source files found in {impl_path}. "
                f"Expected extensions: {', '.join(_CODE_EXTENSIONS)}"
            )
        parts = []
        if include_docs:
            for name in ("README.md", "readme.md"):
                readme = impl_path / name
                if readme.exists():
                    parts.append(f"# File: {readme.name}\n\n" + readme.read_text(encoding="utf-8"))
                    click.echo(f"  + {readme.name} (intent context)")
                    break
        for f in impl_files:
            parts.append(f"# File: {f.name}\n\n" + f.read_text(encoding="utf-8"))
        source = "\n\n".join(parts)
        detected_label = lang_label or _lang_label_from_path(impl_files[0])
        # Derive recipe stem from first file, stripping lang suffix (e.g. _python_pocketflow)
        stem = impl_files[0].stem
        for suffix in ("_python_pocketflow", "_python_langgraph", "_python_crewai",
                       "_python_autogen", "_langgraph", "_pocketflow", "_ts", "_go"):
            if stem.endswith(suffix):
                stem = stem[: -len(suffix)]
                break
        spec_parent = impl_path
        click.echo(
            f"Describing {len(impl_files)} file(s) in {impl_path.name}/: "
            f"{', '.join(f.name for f in impl_files)}"
        )
    else:
        source = impl_path.read_text(encoding="utf-8")
        detected_label = lang_label or _lang_label_from_path(impl_path)
        # Strip trailing _python_pocketflow / _langgraph etc. for cleaner stem
        stem = impl_path.stem
        for suffix in ("_python_pocketflow", "_python_langgraph", "_python_crewai",
                       "_python_autogen", "_langgraph", "_pocketflow", "_ts", "_go"):
            if stem.endswith(suffix):
                stem = stem[: -len(suffix)]
                break
        spec_parent = impl_path.parent
        click.echo(f"Generating splc spec for {impl_path.name} ({detected_label}) ...")

    # Route to code spec or general text summary based on file extension
    is_code = (
        impl_path.is_dir()
        or impl_path.suffix.lower() in _CODE_EXTENSIONS
    )
    if is_code:
        prompt = _SPLC_DESCRIBE_PROMPT.format(lang_label=detected_label, source=source)
    else:
        prompt = _DESCRIBE_TEXT_PROMPT.format(source=source)

    if prompt_debug:
        click.echo("=" * 70)
        click.echo("LLM PROMPT:")
        click.echo("=" * 70)
        click.echo(prompt)
        return

    try:
        from spl3.adapters import get_adapter
    except ImportError:
        raise click.ClickException("spl3 adapters not found: ensure spl3 is installed.")

    llm = get_adapter(adapter, **({"model": model} if model else {}))
    result = asyncio.run(llm.generate(prompt, **({"model": model} if model else {})))
    spec_text = result if isinstance(result, str) else getattr(result, "content", str(result))

    # Name: <recipe>-<adapter>-<model>-spec.md
    import re as _re
    _m = (model or "default").lower()
    if adapter == "openrouter":
        _m = _m.split("/", 1)[-1]          # drop provider prefix (google/...)
        _m = _re.sub(r"(\d)\.(\d)", r"\1\2", _m)   # 3.1 → 31
        _m = _re.sub(r"-(preview|latest|turbo|instruct|exp)$", "", _m)  # strip trailing tags
    model_slug = _m.replace(" ", "_").replace("/", "_").replace(":", "-")
    spec_filename = f"{stem}-{adapter}-{model_slug}-spec.md"
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        spec_path = output_path
    elif spec_dir:
        spec_dir.mkdir(parents=True, exist_ok=True)
        spec_path = spec_dir / (_make_out_stem("spl2spec", stem) + "-spec.md")
    else:
        spec_path = spec_parent / spec_filename

    spec_path.write_text(spec_text, encoding="utf-8")
    click.echo(f"Spec written to: {spec_path}")
    click.echo()
    click.echo("Reverse pipeline:")
    click.echo(f"  spl3 text2spl --description \"<Section 0 from {spec_path.name}>\" --mode workflow")
    click.echo(f"  spl3 splc compile <output.spl> --lang python/pocketflow")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    splc()
