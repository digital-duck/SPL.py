"""SPL 3.0 CLI: spl

Commands:
  spl register <path>             Register workflows from .spl file(s) into Hub registry
  spl run <file.spl>              Run an orchestrator workflow
  spl describe <file.spl>         Generate a plain-English functional specification
  spl registry list               List registered workflows (local + Hub)
  spl peers list                  List peer Hubs and their workflow counts
  spl peers add <url>             Add a peer Hub (peering handshake)
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

import click

_log = logging.getLogger("spl.cli")

_SPL_LOG_DIR = Path.home() / ".spl" / "logs"


# ---------------------------------------------------------------------------
# Run-log helpers (parity with spl-go / spl-ts)
# ---------------------------------------------------------------------------

class _CapturingAdapter:
    """Thin wrapper that records the last prompt/model sent to the LLM."""
    def __init__(self, inner):
        self._inner = inner
        self.last_prompt = ""
        self.last_model = ""

    def __getattr__(self, name):
        return getattr(self._inner, name)

    async def generate(self, prompt: str = "", model: str = "", **kwargs):
        self.last_prompt = prompt
        self.last_model = model or getattr(self._inner, "default_model", "")
        return await self._inner.generate(prompt, model=model, **kwargs)


def _write_run_log(
    stem: str,
    adapter_name: str,
    model_name: str,
    source: str,
    last_prompt: str,
    result,
    started_at: datetime,
) -> Path:
    """Write a rich markdown run log matching spl-go / spl-ts format. Returns the log path."""
    _SPL_LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts_file  = started_at.strftime("%Y%m%d-%H%M%S")
    ts_human = started_at.strftime("%Y-%m-%d %H:%M:%S")

    filename = f"{stem}-{adapter_name}-{ts_file}.md"
    log_path = _SPL_LOG_DIR / filename

    # Support both WorkflowResult (spl3) and SPLResult / GenerationResult (spl2)
    in_tok  = (getattr(result, "total_input_tokens",  None)
               or getattr(result, "input_tokens",  0) or 0)
    out_tok = (getattr(result, "total_output_tokens", None)
               or getattr(result, "output_tokens", 0) or 0)
    latency = (getattr(result, "total_latency_ms",    None)
               or getattr(result, "latency_ms",    0) or 0)
    output  = (getattr(result, "committed_value", None)
               or getattr(result, "content", "") or "")

    lines = [
        f"# SPL Run: {stem}",
        "",
        f"- **Adapter:** {adapter_name}",
        f"- **Model:** {model_name}",
        f"- **Tokens:** {in_tok} in / {out_tok} out",
        f"- **Latency:** {latency:.0f}ms",
        f"- **Timestamp:** {ts_human}",
        "",
        "## SPL Source",
        "",
        "```spl",
        source.rstrip(),
        "```",
    ]

    if last_prompt:
        lines += ["", "## Final Prompt", "", "```prompt", last_prompt.rstrip(), "```"]

    lines += ["", "## Output", "", "```output", output.rstrip(), "```"]

    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return log_path


@click.group()
@click.option("--hub", default=None, envvar="SPL3_HUB", help="Momagrid Hub URL")
@click.option("--verbose", "-v", is_flag=True)
@click.pass_context
def main(ctx, hub, verbose):
    """SPL 3.0 — Declarative Structured Prompt Language."""
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)
    ctx.ensure_object(dict)
    ctx.obj["hub"] = hub


# ------------------------------------------------------------------ #
# spl run                                                             #
# ------------------------------------------------------------------ #

@main.command()
@click.argument("spl_file")
@click.option("--adapter", default="ollama", show_default=True)
@click.option("--model", default=None, show_default=True)
@click.option("--param", "-p", multiple=True, help="key=value workflow INPUT params")
@click.option(
    "--log-prompts", default=None, metavar="DIR",
    help=(
        "Write each fully-assembled prompt to DIR/<fn>_NNN.md before it is sent "
        "to the model. Each file contains a metadata header (model, max_tokens, "
        "temperature) followed by the raw prompt body — ready to paste into "
        "Google AI Studio, HuggingFace Chat, or any other playground."
    ),
)
@click.option("--tools", "tools_module", default=None, metavar="FILE",
              help="Python module to load as CALL-able tools (e.g. tools/my_tools.py).")
@click.option("--claude-allowed-tools", "allowed_tools", default=None, metavar="TOOLS",
              help="Comma-separated tools for the claude_cli adapter (e.g. WebSearch,Bash).")
@click.pass_context
def run(ctx, spl_file, adapter, model, param, log_prompts, tools_module, allowed_tools):
    """Run an orchestrator .spl workflow with workflow composition."""
    from pathlib import Path
    from spl3.registry import LocalRegistry
    from spl3._loader import load_workflows_from_file

    # Parse params: key=value pairs
    params = {}
    for p in param:
        if "=" not in p:
            raise click.BadParameter(f"Expected key=value, got: {p}")
        k, v = p.split("=", 1)
        params[k.strip()] = v.strip()

    path = Path(spl_file)
    if not path.exists():
        raise click.ClickException(f"File not found: {path}")

    hub_url = ctx.obj.get("hub")

    asyncio.run(_run_workflow(path, adapter, model, params, hub_url, log_prompts,
                              tools_module, allowed_tools))


async def _run_workflow(path, adapter_name, model, params, hub_url, log_prompts=None,
                        tools_module=None, allowed_tools=None):
    from spl3.registry import LocalRegistry, FederatedRegistry
    from spl3.composer import WorkflowComposer

    try:
        from spl3.executor import Executor
        from spl3.adapters import get_adapter
    except ImportError:
        raise click.ClickException("spl-llm 2.0 not installed: pip install spl-llm>=2.0.0")

    started_at = datetime.now()

    # Build registry: load all .spl files in the same directory
    local = LocalRegistry()
    local.load_dir(path.parent)
    click.echo(f"Registry: {local.list()}")

    # Optionally attach Hub registry
    registry = local
    if hub_url:
        from spl3.hub_registry import HubRegistry
        hub_reg = HubRegistry(hub_url)
        from spl3.registry import FederatedRegistry
        registry = FederatedRegistry(local, hub_reg)
        click.echo(f"Hub registry: {hub_url}")

    # Propagate --model into workflow @model param so USING MODEL @model picks it up.
    # Only set if the user hasn't already passed --param model=... explicitly.
    if model and "model" not in params:
        params["model"] = model

    # Build executor and attach composer for CALL workflow_name() dispatch
    adapter_kwargs = {"model": model} if model else {}
    if allowed_tools:
        adapter_kwargs["allowed_tools"] = [t.strip() for t in allowed_tools.split(",")]
    _inner_adapter = get_adapter(adapter_name, **adapter_kwargs)
    capturing = _CapturingAdapter(_inner_adapter)
    executor = Executor(adapter=capturing)
    executor.composer = WorkflowComposer(registry, executor)
    if log_prompts:
        executor.prompt_log_dir = log_prompts
        click.echo(f"Prompt logging → {log_prompts}/")

    # Load tools module (or auto-load tools.py from .spl directory)
    if tools_module:
        from spl.tools import load_tools_module
        loaded = load_tools_module(tools_module)
        for tool_name, tool_fn in loaded.items():
            executor.register_tool(tool_name, tool_fn)
        click.echo(f"Loaded {len(loaded)} tool(s) from {tools_module}")
    else:
        auto_tools = path.parent / "tools.py"
        if auto_tools.exists():
            from spl.tools import load_tools_module
            loaded = load_tools_module(str(auto_tools))
            for tool_name, tool_fn in loaded.items():
                executor.register_tool(tool_name, tool_fn)
            click.echo(f"Auto-loaded {len(loaded)} tool(s) from {auto_tools}")

    # Parse the file — needed for function registration and PROMPT fallback
    from spl.lexer import Lexer
    from spl.ast_nodes import CreateFunctionStatement, PromptStatement
    from spl3.parser import SPL3Parser
    from spl3._loader import load_workflows_from_file

    source = path.read_text(encoding="utf-8")
    _tokens = Lexer(source).tokenize()
    _program = SPL3Parser(_tokens).parse()

    # Register CREATE FUNCTION definitions so prompt templates are expanded
    for _stmt in _program.statements:
        if isinstance(_stmt, CreateFunctionStatement):
            executor.functions.register(_stmt)

    stem = path.stem.replace("-", "_")
    defns = load_workflows_from_file(path)

    if defns:
        # ── SPL 3.0 WORKFLOW path ──────────────────────────────────────────
        target = next((d for d in defns if d.name == stem), defns[-1])
        click.echo(f"Running workflow: {target.name}({list(params)})")

        result = await executor.execute_workflow(target.ast_node, params=params)

        resolved_model = capturing.last_model or model or ""
        click.echo(f"\nStatus:  {result.status}")
        click.echo(f"Output:  {result.committed_value or '(no COMMIT)'}")
        click.echo(f"LLM calls: {result.total_llm_calls}  "
                   f"Latency: {result.total_latency_ms:.0f}ms")
        log_result = result

    else:
        # ── SPL 2.0 PROMPT fallback ────────────────────────────────────────
        prompts = [s for s in _program.statements if isinstance(s, PromptStatement)]
        if not prompts:
            raise click.ClickException(
                f"No WORKFLOW or PROMPT definitions found in {path}"
            )

        from spl.analyzer import Analyzer
        analysis = Analyzer().analyze(_program)
        spl2_results = await executor.execute_program(analysis, params=params)

        for r in spl2_results:
            click.echo(f"\nStatus:     complete")
            click.echo(f"Output:     {getattr(r, 'content', '') or '(no output)'}")
            click.echo(f"LLM calls:  1")
            click.echo(f"Latency:    {getattr(r, 'latency_ms', 0):.0f}ms")
            toks_in  = getattr(r, "input_tokens",  0)
            toks_out = getattr(r, "output_tokens", 0)
            if toks_in:
                click.echo(f"Tokens:     {toks_in} in / {toks_out} out")

        resolved_model = capturing.last_model or model or getattr(spl2_results[0], "model", "") if spl2_results else model or ""
        log_result = spl2_results[-1] if spl2_results else None

    if log_result is not None:
        log_path = _write_run_log(
            stem=stem,
            adapter_name=adapter_name,
            model_name=resolved_model,
            source=source,
            last_prompt=capturing.last_prompt,
            result=log_result,
            started_at=started_at,
        )
        click.echo(f"Log:     {log_path}")


# ------------------------------------------------------------------ #
# spl registry                                                        #
# ------------------------------------------------------------------ #

@main.group()
def registry():
    """Manage the workflow registry."""


@registry.command("list")
@click.pass_context
def registry_list(ctx):
    """List all registered workflows."""
    hub_url = ctx.obj.get("hub")
    if hub_url:
        from spl3.hub_registry import HubRegistry
        reg = HubRegistry(hub_url)
        workflows = reg.list()
        click.echo(f"Hub {hub_url}: {len(workflows)} workflow(s)")
        for wf in workflows:
            click.echo(f"  {wf}")
    else:
        click.echo("No --hub specified. Use --hub <url> to query Hub registry.")


@main.command()
@click.argument("path")
@click.pass_context
def register(ctx, path):
    """Register workflows from a .spl file or directory into the Hub."""
    from pathlib import Path
    from spl3.registry import LocalRegistry

    hub_url = ctx.obj.get("hub")
    if not hub_url:
        raise click.ClickException("--hub <url> required for spl register")

    local = LocalRegistry()
    p = Path(path)
    if p.is_dir():
        count = local.load_dir(p)
    else:
        count = local.load_file(p)

    from spl3.hub_registry import HubRegistry
    hub_reg = HubRegistry(hub_url)

    # Push each workflow definition to the Hub
    from spl3.registry import WorkflowDefinition
    registered = 0
    for name in local.list():
        defn: WorkflowDefinition = local.get(name)
        try:
            hub_reg.register(defn.name, defn.source_text)
            click.echo(f"  Registered: {name}")
            registered += 1
        except Exception as e:
            click.echo(f"  Failed {name}: {e}", err=True)

    click.echo(f"\nRegistered {registered}/{count} workflow(s) on {hub_url}")


# ------------------------------------------------------------------ #
# spl peers                                                           #
# ------------------------------------------------------------------ #

@main.group()
def peers():
    """Manage Hub-to-Hub peering."""


@peers.command("list")
@click.pass_context
def peers_list(ctx):
    """List peer Hubs."""
    hub_url = ctx.obj.get("hub")
    if not hub_url:
        raise click.ClickException("--hub <url> required")
    import httpx
    try:
        resp = httpx.get(f"{hub_url}/peer/list", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        for peer in data.get("peers", []):
            click.echo(f"  {peer['url']}  tier={peer.get('tier','?')}  "
                       f"workflows={len(peer.get('workflows',[]))}")
    except Exception as e:
        raise click.ClickException(str(e))


@peers.command("add")
@click.argument("peer_url")
@click.pass_context
def peers_add(ctx, peer_url):
    """Add a peer Hub (peering handshake)."""
    hub_url = ctx.obj.get("hub")
    if not hub_url:
        raise click.ClickException("--hub <url> required")
    import httpx
    try:
        resp = httpx.post(
            f"{hub_url}/peer/add",
            json={"peer_url": peer_url},
            timeout=15,
        )
        resp.raise_for_status()
        click.echo(f"Peering established: {hub_url} <-> {peer_url}")
    except Exception as e:
        raise click.ClickException(str(e))


# ------------------------------------------------------------------ #
# spl test                                                            #
# ------------------------------------------------------------------ #

@main.command("test")
@click.argument("spl_file_or_dir")
@click.option("--adapter", default="ollama", show_default=True)
@click.option("--model", default=None, show_default=True)
@click.option("--verbose", "-v", is_flag=True)
@click.pass_context
def cmd_test(ctx, spl_file_or_dir, adapter, model, verbose):
    """Run pipeline-level tests for .spl workflows.

    Looks for test fixtures alongside .spl files:
      generate_code.spl          — workflow under test
      generate_code.test.yaml    — test cases (inputs + expected assertions)

    Test YAML format:
    \b
      - name: "basic generation"
        params:
          spec: "Write a hello-world function in Python"
        assert:
          contains: ["def ", "print"]
          status: complete
    """
    from pathlib import Path
    path = Path(spl_file_or_dir)
    if path.is_dir():
        spl_files = list(path.rglob("*.spl"))
    else:
        spl_files = [path]

    if not spl_files:
        click.echo("No .spl files found.")
        return

    asyncio.run(_run_tests(spl_files, adapter, model, verbose))


async def _run_tests(spl_files, adapter_name, model, verbose):
    import yaml
    from spl3.registry import LocalRegistry

    try:
        from spl3.executor import Executor
        from spl3.adapters import get_adapter
    except ImportError:
        raise click.ClickException("spl-llm 2.0 not installed: pip install spl-llm>=2.0.0")

    adapter_kwargs = {"model": model} if model else {}
    adapter = get_adapter(adapter_name, **adapter_kwargs)
    executor = Executor(adapter=adapter)

    total = passed = failed = skipped = 0

    for spl_file in sorted(spl_files):
        test_file = spl_file.with_suffix("").with_suffix(".test.yaml")
        if not test_file.exists():
            _log.debug("No test file for %s — skipping", spl_file.name)
            continue

        from spl3._loader import load_workflows_from_file
        defns = load_workflows_from_file(spl_file)
        if not defns:
            continue

        cases = yaml.safe_load(test_file.read_text(encoding="utf-8")) or []
        target = defns[-1]
        click.echo(f"\n{spl_file.name} [{target.name}]  ({len(cases)} test(s))")

        for case in cases:
            total += 1
            name = case.get("name", f"case-{total}")
            params = case.get("params", {})
            assertions = case.get("assert", {})

            try:
                result = await executor.execute_workflow(target.ast_node, params=params)
                output = str(result.committed_value or "")
                status = result.status

                ok = True
                failures = []
                for fragment in assertions.get("contains", []):
                    if fragment not in output:
                        ok = False
                        failures.append(f"output missing {fragment!r}")
                expected_status = assertions.get("status")
                if expected_status and status != expected_status:
                    ok = False
                    failures.append(f"status={status!r}, expected={expected_status!r}")

                if ok:
                    passed += 1
                    click.echo(f"  ✓ {name}")
                else:
                    failed += 1
                    click.echo(f"  ✗ {name}: {'; '.join(failures)}")
                    if verbose:
                        click.echo(f"    output: {output[:200]}")
            except Exception as exc:
                failed += 1
                click.echo(f"  ✗ {name}: {exc}")

    skipped = total - passed - failed
    click.echo(
        f"\n{'─'*50}\n"
        f"Results: {passed} passed, {failed} failed, {skipped} skipped  ({total} total)"
    )
    if failed:
        raise SystemExit(1)


# ------------------------------------------------------------------ #
# spl code-rag                                                        #
# ------------------------------------------------------------------ #

@main.group("code-rag")
def cmd_code_rag():
    """Manage the Code-RAG index for Text2SPL."""


@cmd_code_rag.command("seed")
@click.argument("cookbook_dir", default="cookbook")
@click.option("--storage-dir", default=".spl/code_rag", show_default=True,
              help="Directory for the RAG vector store.")
@click.option("--catalog", default=None,
              help="Seed from cookbook_catalog.json (curated one-liner descriptions).")
@click.option("--from-specs", is_flag=True, default=False,
              help=(
                  "Seed using Section 0 from describe-generated *-spec.md files. "
                  "Gives the richest SPL-aware descriptions. Run 'code-rag describe-all' first."
              ))
@click.option("--all-active/--no-filter", default=True, show_default=True,
              help="When seeding from catalog, skip inactive/disabled entries.")
def code_rag_seed(cookbook_dir, storage_dir, catalog, from_specs, all_active):
    """Seed the Code-RAG index from a cookbook directory.

    Three seeding modes (in increasing description quality):

    \b
    1. Default — file header comments as descriptions:
         spl3 code-rag seed cookbook/

    \b
    2. Catalog — curated one-liner descriptions from cookbook_catalog.json:
         spl3 code-rag seed --catalog cookbook/cookbook_catalog.json

    \b
    3. Specs — rich SPL-aware Section 0 from describe-generated spec files (best):
         spl3 code-rag describe-all cookbook/ --adapter claude_cli
         spl3 code-rag seed cookbook/ --from-specs
    """
    from spl3.code_rag import CodeRAGStore
    store = CodeRAGStore(storage_dir=storage_dir)

    if from_specs:
        count = store.seed_from_specs(cookbook_dir)
        click.echo(f"Seeded {count} workflow(s) from describe-spec files under {cookbook_dir}")
    elif catalog:
        count = store.seed_from_catalog(catalog, only_active=all_active)
        click.echo(f"Seeded {count} workflow(s) from catalog {catalog}")
    else:
        count = store.seed_from_dir(cookbook_dir)
        click.echo(f"Seeded {count} workflow(s) from directory {cookbook_dir}")

    click.echo(f"Total indexed: {store.count()}")


@cmd_code_rag.command("query")
@click.argument("query_text")
@click.option("--storage-dir", default=".spl/code_rag", show_default=True)
@click.option("--top-k", default=3, show_default=True)
def code_rag_query(query_text, storage_dir, top_k):
    """Query the Code-RAG index and print matching SPL examples."""
    from spl3.code_rag import CodeRAGStore
    store = CodeRAGStore(storage_dir=storage_dir)
    hits = store.retrieve(query_text, top_k=top_k)
    if not hits:
        click.echo("No results.")
        return
    for i, hit in enumerate(hits, 1):
        click.echo(f"\n── Example {i} (score={hit['score']:.3f}) ─────────────────")
        click.echo(f"Description: {hit['description']}")
        click.echo(hit["spl_source"][:500])


@cmd_code_rag.command("describe-all")
@click.argument("cookbook_dir", default="cookbook")
@click.option("--adapter", default="ollama", show_default=True,
              help="LLM adapter used to generate each spec.")
@click.option("--model", default=None, metavar="MODEL")
@click.option("--spec-dir", default=None, metavar="DIR",
              help="Write all spec files to DIR instead of alongside each .spl file.")
@click.option("--catalog", default=None,
              help="Restrict to active recipes listed in cookbook_catalog.json.")
@click.option("--skip-existing", is_flag=True, default=True, show_default=True,
              help="Skip recipes that already have a -spec.md file.")
def code_rag_describe_all(cookbook_dir, adapter, model, spec_dir, catalog, skip_existing):
    """Batch-generate describe specs for all canonical cookbook recipes.

    Runs 'spl3 describe' on each .spl file and writes a *-spec.md alongside it
    (or to --spec-dir). After this completes, run:

    \b
      spl3 code-rag seed cookbook/ --from-specs

    to index the rich Section 0 descriptions into the RAG store.

    \b
    Examples:
      spl3 code-rag describe-all cookbook/ --adapter claude_cli
      spl3 code-rag describe-all cookbook/ --adapter claude_cli --catalog cookbook/cookbook_catalog.json
    """
    import json as _json

    cookbook_path = Path(cookbook_dir)
    if not cookbook_path.is_dir():
        raise click.ClickException(f"Not a directory: {cookbook_dir}")

    # Build candidate file list
    if catalog:
        catalog_data = _json.loads(Path(catalog).read_text(encoding="utf-8"))
        entries = catalog_data if isinstance(catalog_data, list) else catalog_data.get("recipes", [])
        spl_files = []
        for entry in entries:
            if not entry.get("is_active", True):
                continue
            if entry.get("approval_status", "approved") in ("disabled", "rejected"):
                continue
            if "args" in entry and len(entry["args"]) > 2:
                # args[2] is project-root-relative, e.g. "./cookbook/05_.../self_refine.spl"
                p = Path(entry["args"][2].lstrip("./"))
                if p.exists():
                    spl_files.append(p)
    else:
        # All .spl files under cookbook_dir, excluding generated variants
        spl_files = [
            p for p in sorted(cookbook_path.rglob("*.spl"))
            if "generated-" not in str(p)
        ]

    total = len(spl_files)
    click.echo(f"Describing {total} recipe(s) with adapter={adapter} ...")

    try:
        from spl3.adapters import get_adapter
    except ImportError:
        raise click.ClickException("spl-llm 2.0 not installed: pip install spl-llm>=2.0.0")

    adapter_kwargs = {"model": model} if model else {}
    llm = get_adapter(adapter, **adapter_kwargs)

    done = skipped = failed = 0
    for spl_file in spl_files:
        stem = spl_file.stem
        if spec_dir:
            out_dir = Path(spec_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            spec_path = out_dir / f"{stem}-spec.md"
        else:
            spec_path = spl_file.parent / f"{stem}-spec.md"

        if skip_existing and spec_path.exists():
            click.echo(f"  [skip]  {spl_file.name}  (spec exists)")
            skipped += 1
            continue

        try:
            source = spl_file.read_text(encoding="utf-8")
            prompt = _DESCRIBE_PROMPT.format(source=source)
            result = asyncio.run(llm.generate(
                prompt, **({"model": model} if model else {})
            ))
            spec_text = result if isinstance(result, str) else getattr(result, "content", str(result))
            spec_path.write_text(spec_text, encoding="utf-8")
            click.echo(f"  [ok]    {spl_file.name}  -> {spec_path.name}")
            done += 1
        except Exception as exc:
            click.echo(f"  [fail]  {spl_file.name}: {exc}", err=True)
            failed += 1

    click.echo(f"\nDone: {done} generated, {skipped} skipped, {failed} failed  ({total} total)")
    if done:
        click.echo("\nNext step — seed RAG from specs:")
        click.echo(f"  spl3 code-rag seed {cookbook_dir} --from-specs")


@cmd_code_rag.command("stats")
@click.option("--storage-dir", default=".spl/code_rag", show_default=True)
def code_rag_stats(storage_dir):
    """Show Code-RAG index statistics."""
    from spl3.code_rag import CodeRAGStore
    store = CodeRAGStore(storage_dir=storage_dir)
    click.echo(f"Code-RAG store: {storage_dir}")
    click.echo(f"  Indexed pairs: {store.count()}")


# ------------------------------------------------------------------ #
# spl3 text2spl                                                       #
# ------------------------------------------------------------------ #

@main.command("text2spl")
@click.argument("description", required=False, default=None)
@click.option("--description", "-d", "description_opt", default=None, metavar="TEXT_OR_FILE",
              help="Natural language description, a file path, or a -spec.md file "
                   "(Section 0 is extracted automatically).")
@click.option("--adapter", default=None, metavar="NAME",
              help="Compiler adapter (default: ollama).")
@click.option("--model", "-m", default=None, metavar="MODEL",
              help="Compiler model.")
@click.option("--mode", type=click.Choice(["auto", "prompt", "workflow"]),
              default="auto", show_default=True,
              help="Generation mode.")
@click.option("--validate/--no-validate", default=True, show_default=True,
              help="Validate generated SPL code.")
@click.option("--output", "-o", default=None, metavar="FILE",
              help="Write generated SPL to FILE.")
@click.option("--prompt", "prompt_debug", is_flag=True, default=False,
              help="Display the LLM prompt and exit.")
def cmd_text2spl(description, description_opt, adapter, model, mode, validate, output, prompt_debug):
    """Compile natural language DESCRIPTION into SPL 3.0 code.

    DESCRIPTION may be:
      - a literal string passed as a positional argument or via --description
      - a path to a plain text / markdown file (full file used as description)
      - a path to a *-spec.md file (Section 0 is extracted automatically)

    \b
    Examples:
      spl3 text2spl "summarize a document with a 2000 token budget"
      spl3 text2spl --description flow-splc-python_pocketflow-spec.md --mode workflow -o agent.spl
      spl3 text2spl "build a review agent" --mode workflow -o review.spl
      spl3 text2spl "classify intent" --adapter ollama -m gemma3
    """
    import re as _re
    from spl.text2spl import Text2SPL
    from spl3.adapters import get_adapter

    # Resolve description: --description option takes precedence over positional arg
    raw = description_opt or description
    if not raw:
        raise click.UsageError(
            "Provide a description as a positional argument or via --description."
        )

    # If it looks like a file path, read it
    candidate = Path(raw)
    if candidate.exists() and candidate.is_file():
        content = candidate.read_text(encoding="utf-8")
        # If it's a -spec.md, extract Section 0
        if candidate.name.endswith("-spec.md") or candidate.suffix == ".md":
            # Match "## 0. ..." up to the next "## " heading or end of file
            m = _re.search(
                r"^##\s*0\..*?\n(.*?)(?=^##\s|\Z)",
                content,
                _re.MULTILINE | _re.DOTALL,
            )
            if m:
                section0 = m.group(1).strip()
                click.echo(f"Extracted Section 0 from {candidate.name} "
                           f"({len(section0)} chars)", err=True)
                raw = section0
            else:
                click.echo(f"No 'Section 0' heading found in {candidate.name} — "
                           "using full file content.", err=True)
                raw = content.strip()
        else:
            raw = content.strip()

    adapter = adapter or "ollama"
    try:
        llm = get_adapter(adapter, **({"model": model} if model else {}))
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    compiler = Text2SPL(adapter=llm)

    if prompt_debug:
        system, user = compiler.build_prompt(raw, mode=mode)
        click.echo("=" * 70)
        click.echo("LLM SYSTEM PROMPT:")
        click.echo("=" * 70)
        click.echo(system)
        click.echo("\n" + "=" * 70)
        click.echo("LLM USER PROMPT:")
        click.echo("=" * 70)
        click.echo(user)
        return

    try:
        spl_code = asyncio.run(compiler.compile(raw, mode=mode))
    except Exception as exc:
        raise click.ClickException(f"Compilation failed: {exc}") from exc

    spl_code = format_spl(spl_code)

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(spl_code, encoding="utf-8")
        click.echo(f"Written to {output}")
    else:
        click.echo(spl_code)

    # Always validate the generated SPL using the real parser
    try:
        from spl.lexer import Lexer
        from spl3.parser import SPL3Parser
        tokens = Lexer(spl_code).tokenize()
        SPL3Parser(tokens).parse()
        click.echo("Validation: OK")
    except Exception as exc:
        click.echo(f"Validation: FAILED — {exc}", err=True)
        click.echo("  Fix the .spl file or re-run text2spl.", err=True)


# ------------------------------------------------------------------ #
# SPL Formatter                                                        #
# ------------------------------------------------------------------ #

def format_spl(spl_code: str) -> str:
    """Apply cosmetic formatting to generated SPL source.

    Rules:
    1. Put RETURNS <type> AS $$ on its own line after the closing paren
       of a CREATE FUNCTION signature, for readability.
    2. Escape bare single quotes inside $$ prompt bodies as '' so the SPL
       lexer does not treat them as unterminated string literals.
    """
    import re as _re

    # Rule 1: split RETURNS onto its own line
    spl_code = _re.sub(
        r'\)\s+(RETURNS\s+\S+\s+AS\s+[$][$])',
        lambda m: ')\n' + m.group(1),
        spl_code,
    )

    # Rule 1b: strip spurious TYPE keyword in INPUT/OUTPUT declarations
    # LLMs sometimes emit "INPUT @var TYPE text" instead of "INPUT @var text"
    spl_code = _re.sub(r'\bTYPE\s+(?=\w)', '', spl_code)

    # Rule 1c: uppercase type names — LLMs emit lowercase (text, string, list…)
    # Covers: RETURNS <type> AS $$  and  INPUT/OUTPUT @var <type>
    _TYPES = r'(text|string|number|boolean|integer|float|list|matrix|vector|index|document|dict|any)'
    spl_code = _re.sub(r'\bRETURNS\s+' + _TYPES + r'\b',
                       lambda m: 'RETURNS ' + m.group(1).upper(), spl_code, flags=_re.IGNORECASE)
    spl_code = _re.sub(r'(@\w+)\s+' + _TYPES + r'\b',
                       lambda m: m.group(1) + ' ' + m.group(2).upper(), spl_code, flags=_re.IGNORECASE)

    # Rule 2: inside each $$ ... $$ block, replace lone ' with ''
    # A lone ' is one that is not already doubled (i.e. not preceded or
    # followed by another single quote).
    def _escape_quotes_in_body(m):
        body = m.group(1)
        # Replace single ' not already part of '' with ''
        body = _re.sub(r"(?<!')'(?!')", "''", body)
        return '$$' + body + '$$'

    spl_code = _re.sub(r'[$][$](.*?)[$][$]', _escape_quotes_in_body, spl_code,
                       flags=_re.DOTALL)

    return spl_code


def _rewrite_for_loops(spl_text: str) -> str:
    """Rewrite FOR @var IN @collection DO...END to index-based WHILE loop.

    Gemini (and some other LLMs) generate FOR loops for map-reduce patterns;
    SPL has no FOR construct.  The rewrite produces a WHILE loop with a
    fixed ceiling of 10 iterations — structurally equivalent for validation
    and S4/S5 describe runs.
    """
    import re as _re

    lines = spl_text.split('\n')
    result = []
    i = 0
    for_counter = 0

    while i < len(lines):
        line = lines[i]
        m = _re.match(r'^(\s*)FOR\s+(@\w+)\s+IN\s+(@\w+)\s+DO\s*$', line.rstrip(), _re.IGNORECASE)
        if not m:
            result.append(line)
            i += 1
            continue

        indent = m.group(1)
        loop_var = m.group(2)
        collection = m.group(3)
        for_counter += 1
        idx_var = f'@_for_idx_{for_counter}'

        # Collect body lines until the matching END, tracking nested blocks.
        body_lines = []
        i += 1
        depth = 1
        while i < len(lines):
            bl = lines[i]
            bs = bl.strip()
            # WHILE/FOR lines end with DO and open a new block
            if _re.search(r'\bDO\s*$', bs, _re.IGNORECASE):
                depth += 1
            # EVALUATE opens a block without DO
            elif _re.match(r'^EVALUATE\b', bs, _re.IGNORECASE):
                depth += 1
            elif _re.match(r'^END[;]?\s*$', bs, _re.IGNORECASE):
                depth -= 1
                if depth == 0:
                    i += 1   # consume END
                    break
            body_lines.append(bl)
            i += 1

        result.append(f'{indent}/* FOR {loop_var} IN {collection} — rewritten to WHILE */')
        result.append(f'{indent}{idx_var} := 0;')
        result.append(f'{indent}WHILE {idx_var} < 10 DO')
        result.extend(body_lines)
        result.append(f'{indent}    {idx_var} := {idx_var} + 1;')
        result.append(f'{indent}END')

    return '\n'.join(result)


# ------------------------------------------------------------------ #
# Mermaid Syntax Post-Processor                                        #
# ------------------------------------------------------------------ #

def _join_multiline_quoted(text: str) -> str:
    """Replace actual newlines inside double-quoted strings with <br/>.

    Handles both node labels  ["line1\nline2"]  and
    edge labels               |"line1\nline2"|
    """
    result = []
    in_quote = False
    for ch in text:
        if ch == '"':
            in_quote = not in_quote
            result.append(ch)
        elif ch == '\n' and in_quote:
            result.append('<br/>')
        else:
            result.append(ch)
    return ''.join(result)


def fix_mermaid_syntax(mermaid_text, style="flowchart"):
    """
    Rule-based post-processor to fix common LLM Mermaid syntax errors.

    Handles:
    - Actual newlines inside quoted labels/edge-labels  →  <br/>
    - Wrong bare arrow ->  →  -->
    - Unicode → inside labels  →  plain ->
    - Literal \\n inside unquoted node labels  →  quoted label with <br/>
    - Dotted edge with quoted label  -. "text" .-->  →  -.->|text|
    - Malformed dotted arrows  -.-->  -.--->  →  -.->
    - Unquoted node labels containing colons  [label: text]  →  ["label: text"]
    - Edge targeting a subgraph name  A --> SG  →  A --> first_node_inside_SG
    - Missing diagram declaration
    - Diagram declaration (flowchart/graph) kept at column 0 (no indent)
    """
    import re

    # Pre-pass: fix actual newlines inside quoted strings before line-splitting
    mermaid_text = _join_multiline_quoted(mermaid_text)

    # Strip trivial "RETURN default" edge labels — implicit linear advance, not a branch
    mermaid_text = re.sub(r'\|"RETURN default"\|', '', mermaid_text)
    mermaid_text = re.sub(r'\|RETURN default\|', '', mermaid_text)

    lines = mermaid_text.strip().split('\n')

    # ── Pass 1: collect subgraph names → first node inside each ──────────────
    subgraph_first_node: dict[str, str] = {}
    current_sg: str | None = None
    sg_depth = 0

    for raw in lines:
        s = raw.strip()
        m_sg = re.match(r'^subgraph\s+(\w+)', s)
        if m_sg:
            sg_id = m_sg.group(1)
            subgraph_first_node[sg_id] = ""   # placeholder
            current_sg = sg_id
            sg_depth += 1
            continue
        if s == "end":
            sg_depth = max(0, sg_depth - 1)
            if sg_depth == 0:
                current_sg = None
            continue
        # First node/edge line inside a subgraph → record the leading node ID
        if current_sg and not subgraph_first_node[current_sg] and s and not s.startswith(('%%', 'direction')):
            m_node = re.match(r'^(\w+)', s)
            if m_node:
                subgraph_first_node[current_sg] = m_node.group(1)

    # ── Pass 2: line-by-line fixes ────────────────────────────────────────────
    fixed_lines = []

    has_declaration = any(
        l.strip().startswith(('flowchart', 'graph', 'sequenceDiagram'))
        for l in lines
    )
    if not has_declaration:
        fixed_lines.append(f"{style} TD")

    def _fix_label_newlines(m):
        bracket, content, close = m.group(1), m.group(2), m.group(3)
        if r'\n' in content:
            content = content.replace(r'\n', '<br/>')
            if not (content.startswith('"') and content.endswith('"')):
                content = f'"{content}"'
        return f'{bracket}{content}{close}'

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Diagram declaration: must be at column 0, no indent
        if line.startswith(('flowchart', 'graph', 'sequenceDiagram')):
            fixed_lines.append(line)
            continue

        # Other structural keywords: indent once
        if line.startswith(('subgraph', 'end', 'direction')):
            fixed_lines.append("    " + line if not line.startswith('    ') else line)
            continue

        # Fix malformed dotted arrows: -.-> variants with extra dashes
        # e.g. -.-->, -.--> all normalise to -.->
        line = re.sub(r'-\.(-*>)', '-.->',  line)

        # Fix dotted edge with quoted label:  -. "text" .-->  →  -.->|text|
        line = re.sub(r'-\.\s+"([^"]+)"\s+\.-->', r'-.->|\1|', line)
        line = re.sub(r'-\.\s+\'([^\']+)\'\s+\.-->', r'-.->|\1|', line)

        # Simplify non-standard cylindrical/database shape [("text")] → ["text"]
        # Mermaid cylindrical shape is [(text)] not [("text")]
        line = re.sub(r'\[\("([^"]+)"\)\]', r'["\1"]', line)
        line = re.sub(r"\[\('([^']+)'\)\]", r"['\1']", line)

        # Fix bare -> arrow (not part of --> or -.->)
        # Lookbehind excludes . so that -.-> (dotted arrow) is not corrupted
        line = re.sub(r'(?<![=\-!.])->(?!>)', '-->', line)

        # Replace Unicode → inside labels
        line = line.replace('→', '->')

        # Fix \n inside unquoted square-bracket and curly-brace labels
        line = re.sub(r'(\[)([^\]]+?)(\])', _fix_label_newlines, line)
        line = re.sub(r'(\{)([^}]+?)(\})', _fix_label_newlines, line)

        # Auto-quote unquoted node labels that contain a colon (colon breaks Mermaid parser)
        # Matches:  NodeId[label: with colon]  →  NodeId["label: with colon"]
        def _quote_colon_label(m):
            bracket, content, close = m.group(1), m.group(2), m.group(3)
            if ':' in content and not (content.startswith('"') or content.startswith("'")):
                content = f'"{content}"'
            return f'{bracket}{content}{close}'
        line = re.sub(r'(\[)([^\]"\']+:[^\]]+)(\])', _quote_colon_label, line)

        # Redirect edges that target a subgraph name to its first interior node
        # Handles:  A --> SG,  A -->|label| SG,  A -.-> SG
        for sg_name, first_node in subgraph_first_node.items():
            if not first_node:
                continue
            # Edge with label:  -->|...|  SG_NAME  or  -.->|...| SG_NAME
            line = re.sub(
                r'(\|[^|]*\|)\s+' + re.escape(sg_name) + r'\b',
                r'\1 ' + first_node, line
            )
            # Plain edge ending in SG_NAME (word boundary, not inside a label)
            line = re.sub(
                r'(--?>|-.->)\s+' + re.escape(sg_name) + r'\b',
                r'\1 ' + first_node, line
            )

        # Indent
        if not line.startswith('    '):
            line = "    " + line

        fixed_lines.append(line)

    return '\n'.join(fixed_lines)

def fix_node_syntax(text, node_map, node_id_counter):
    """Fix individual node syntax"""
    import re

    text = text.strip()
    if not text:
        return text

    # Already properly formatted node: A[Label] or A{{Label}}
    if re.match(r'^[A-Z]\[.*\]$', text) or re.match(r'^[A-Z]\{\{.*\}\}$', text):
        return text

    # Decision node with proper ID but wrong braces: A{Label}
    decision_match = re.match(r'^([A-Z])\{([^}]+)\}$', text)
    if decision_match:
        node_id, label = decision_match.groups()
        return f"{node_id}{{{{{label}}}}}"

    # Node with proper ID: A[Label]
    node_match = re.match(r'^([A-Z])\[([^\]]+)\]$', text)
    if node_match:
        return text  # Already correct

    # Unbracketed text - need to assign ID and format
    if text not in node_map:
        node_id = chr(node_id_counter[0])
        node_map[text] = node_id
        node_id_counter[0] += 1
    else:
        node_id = node_map[text]

    # Determine if it should be a decision node (contains question words or ends with ?)
    if any(word in text.lower() for word in ['check', 'verify', 'validate', '?', 'ok', 'pass', 'fail', 'approved', 'decision']):
        return f"{node_id}{{{{{text}}}}}"
    else:
        return f"{node_id}[{text}]"


# ------------------------------------------------------------------ #
# spl3 text2mmd                                                       #
# ------------------------------------------------------------------ #

@main.command("text2mmd")
@click.argument("description", required=False, default=None)
@click.option("--description", "-d", "description_opt", default=None, metavar="TEXT_OR_FILE",
              help="Natural language workflow description or file path.")
@click.option("--adapter", default="ollama", show_default=True, metavar="NAME",
              help="LLM adapter to use.")
@click.option("--model", "-m", default=None, metavar="MODEL",
              help="Model override for the adapter.")
@click.option("--style", default="flowchart", show_default=True,
              type=click.Choice(["flowchart", "graph", "sequence"]),
              help="Mermaid diagram style.")
@click.option("--output", "-o", default=None, metavar="FILE",
              help="Write generated Mermaid to FILE.")
@click.option("--validate/--no-validate", default=True, show_default=True,
              help="Validate generated Mermaid syntax.")
@click.option("--preview", is_flag=True, default=True,
              help="Open diagram in browser preview.")
@click.option("--save-markdown", "--save-md", is_flag=True, default=True,
              help="Save as .md file with mermaid code blocks (VS Code compatible).")
@click.option("--save-html", is_flag=True, default=True,
              help="Save as .html file for browser viewing.")
@click.option("--save-png", is_flag=True, default=True,
              help="Save as .png image file using headless browser.")
@click.option("--out-dir", default=None, metavar="DIR",
              help="Output directory (default: $HOME/.spl/mermaid).")
@click.option("--no-defaults", is_flag=True, default=False,
              help="Disable default --save-html, --save-markdown, --preview.")
@click.option("--prompt", "prompt_debug", is_flag=True, default=False,
              help="Display the LLM prompt and exit.")
def cmd_text2mmd(description, description_opt, adapter, model, style, output, validate, preview, save_markdown, save_html, save_png, out_dir, no_defaults, prompt_debug):
    """Generate Mermaid flowchart from natural language workflow description.

    This creates a visual representation of the workflow that can be reviewed
    and edited before converting to SPL code.

    \b
    Examples:
      spl3 text2mmd "build a review agent that refines text until quality > 0.8"
      spl3 text2mmd --description "research workflow" -o research.mmd
      spl3 text2mmd "parallel code review" --style flowchart --preview
    """
    import re as _re
    import sys
    import os
    from pathlib import Path

    try:
        from spl3.adapters import get_adapter
    except ImportError:
        raise click.ClickException("spl adapters not available")

    # Handle --no-defaults flag
    if no_defaults:
        save_html = False
        save_markdown = False
        save_png = False
        preview = False

    # Setup output directory
    if out_dir is None:
        out_dir = Path.home() / ".spl" / "mermaid"
    else:
        out_dir = Path(out_dir)

    # Create output directory if it doesn't exist
    out_dir.mkdir(parents=True, exist_ok=True)

    # Setup default output file if not provided
    if output is None:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = out_dir / f"workflow_{timestamp}.mmd"
    else:
        # If output provided, use it but place in out_dir if it's just a filename
        output_path = Path(output)
        if not output_path.is_absolute() and output_path.parent == Path('.'):
            output = out_dir / output_path
        else:
            output = output_path

    # --description option takes precedence over positional arg
    raw = description_opt or description
    if not raw:
        raise click.ClickException("DESCRIPTION is required (positional arg or --description)")

    # Check if it's a file path
    if Path(raw).exists():
        desc_text = Path(raw).read_text(encoding="utf-8")
    else:
        desc_text = raw

    # Generate Mermaid diagram
    llm = get_adapter(adapter, **({"model": model} if model else {}))

    prompt = f"""Create a valid Mermaid {style} diagram from this workflow description.

Workflow Description:
{desc_text}

MANDATORY SYNTAX RULES:
1. Every node must have an ID and a label: A[Label Text]
2. Decision/branch node: use SINGLE braces — C{{Decision?}}  (renders as a diamond)
3. Connections: A --> B  or  A -->|edge label| B  (always two dashes, never ->)
4. Multi-word labels: keep them short. If you need a line break, use a QUOTED label with <br/>:
   A["First line<br/>Second line"]
5. Do NOT use \\n inside labels — it renders as a literal backslash-n.
6. Do NOT use Unicode arrows (→) or other Unicode operators inside labels.
7. Subgraphs: connect edges to the FIRST NODE inside the subgraph, not to the subgraph name.
   CORRECT:  A --> B  (where B is the first node inside subgraph SG)
   WRONG:    A --> SG  (subgraph name as edge target)
8. Start with: {style} TD

CORRECT Examples:
- Process node:   A[Start],  B[Process Data],  C["Embed<br/>Documents"]
- Decision node:  D{{Quality OK?}},  E{{Approved?}}
- Connections:    A --> B,  C -->|Yes| D,  C -->|No| E

WRONG Examples (DO NOT USE):
- A[foo\\nbar]       ❌  (\\n in label — use <br/> inside quotes instead)
- A[foo → bar]      ❌  (Unicode arrow in label)
- A --> SubgraphID  ❌  (edge to subgraph name — target the first node inside)
- A[Start] -> B     ❌  (use --> not ->)

Generate ONLY the diagram code. No explanations. Follow the format exactly:

```mermaid
{style} TD
    A([Start]) --> B[Process Request]
    B --> C{{Quality Check?}}
    C -->|Pass| D[Approve]
    C -->|Fail| E[Reject]
    D --> F([End])
    E --> F
```"""

    if prompt_debug:
        click.echo("=" * 70)
        click.echo("LLM PROMPT:")
        click.echo("=" * 70)
        click.echo(prompt)
        return

    result = asyncio.run(llm.generate(prompt, **({"model": model} if model else {})))
    mermaid_text = result if isinstance(result, str) else getattr(result, "content", str(result))

    # Extract mermaid code from markdown if present
    if "```mermaid" in mermaid_text:
        mermaid_match = _re.search(r"```mermaid\s*\n(.*?)\n```", mermaid_text, _re.DOTALL)
        if mermaid_match:
            mermaid_text = mermaid_match.group(1).strip()

    # Apply rule-based post-processing to fix common LLM syntax errors
    mermaid_text = fix_mermaid_syntax(mermaid_text, style)

    # Validation: check for known bad patterns that survive post-processing
    if validate:
        validation_errors = []

        if not any(kw in mermaid_text for kw in ["flowchart", "graph", "sequenceDiagram"]):
            validation_errors.append("Missing diagram type declaration (flowchart/graph/sequenceDiagram)")

        for i, line in enumerate(mermaid_text.split('\n'), 1):
            s = line.strip()
            if not s or s.startswith(('flowchart', 'graph', 'sequenceDiagram', 'subgraph', 'end', 'direction', '%%')):
                continue
            # Raw \n in an unquoted label
            if r'\n' in s and '"' not in s:
                validation_errors.append(f"Line {i}: literal \\n in unquoted label — use quoted label with <br/>")
            # Unicode arrow in label
            if '→' in s:
                validation_errors.append(f"Line {i}: Unicode → in label — use -> instead")
            # Dotted edge with quoted label (wrong syntax)
            if _re.search(r'-\.\s+"', s):
                validation_errors.append(f"Line {i}: dotted edge with quoted label — use -.->|label| instead")

        if validation_errors:
            click.echo("Mermaid syntax warnings:", err=True)
            for error in validation_errors:
                click.echo("  - " + error, err=True)
            click.echo("Note: These may cause rendering issues in browsers", err=True)

    # Main .mmd output
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(mermaid_text, encoding="utf-8")
    click.echo("Mermaid diagram written to: " + str(output))
    base_name = output_path.stem
    output_dir = output_path.parent

    # Generate additional formats
    additional_files = []

    # Markdown format for VS Code preview
    if save_markdown:
        cmd_line = ' '.join(['spl3', 'text2mmd'] + sys.argv[2:])
        title = base_name.title().replace('_', ' ').replace('-', ' ')

        markdown_content = "# " + title + " Workflow\n\n"
        markdown_content += "Generated with [SPL](https://github.com/digital-duck/SPL) using: `" + cmd_line + "`\n\n"
        markdown_content += "## Mermaid Diagram\n\n"
        markdown_content += "```mermaid\n" + mermaid_text + "\n```\n\n"
        markdown_content += "## Usage Options\n\n"
        markdown_content += "### For SPL Development\n"
        markdown_content += "1. Review the workflow diagram above\n"
        markdown_content += "2. Edit the mermaid code if needed\n"
        markdown_content += "3. Generate SPL code: `spl3 mmd2spl " + str(output) + " -o " + base_name + ".spl`\n"
        markdown_content += "4. Validate: `spl3 validate " + base_name + ".spl`\n\n"
        markdown_content += "### For General Use\n"
        markdown_content += "1. Use the `.mmd` file with any Mermaid-compatible tool\n"
        markdown_content += "2. Copy the diagram code for documentation, presentations, or websites\n"
        markdown_content += "3. Edit the visual workflow and regenerate as needed\n\n"
        markdown_content += "---\n\n"
        markdown_content += "**Learn more**: [SPL Repository](https://github.com/digital-duck/SPL) | [Documentation](https://github.com/digital-duck/SPL#readme)\n"
        md_path = output_dir / (base_name + ".md")
        md_path.write_text(markdown_content, encoding="utf-8")
        additional_files.append("Markdown (VS Code): " + str(md_path))

    # HTML format for browser viewing
    if save_html or preview:
        title = base_name.title().replace('_', ' ').replace('-', ' ')
        filename = Path(output).name

        # Build HTML content with proper escaping
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            '    <meta charset="UTF-8">',
            '    <title>' + title + ' - Mermaid Workflow</title>',
            '    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>',
            "    <style>",
            "        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }",
            "        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }",
            "        .header { border-bottom: 2px solid #eee; margin-bottom: 20px; padding-bottom: 10px; }",
            "        .mermaid { text-align: center; margin: 20px 0; min-height: 200px; }",
            "        .footer { margin-top: 20px; padding-top: 10px; border-top: 1px solid #eee; color: #666; font-size: 0.9em; }",
            "        .raw-code { background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 4px; padding: 15px; margin: 20px 0; font-family: 'Courier New', monospace; white-space: pre-wrap; }",
            "        .error-info { background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; padding: 15px; margin: 20px 0; }",
            "    </style>",
            "</head>",
            "<body>",
            '    <div class="container">',
            '        <div class="header">',
            "            <h1>" + title + " Workflow</h1>",
            '            <p><strong>Generated with <a href="https://github.com/digital-duck/SPL" target="_blank">SPL</a></strong></p>',
            "            <p><strong>File:</strong> " + filename + " | <strong>Style:</strong> " + style + " | <strong>Adapter:</strong> " + adapter + "</p>",
            "        </div>",
            '        <div id="mermaid-container" class="mermaid">',
            mermaid_text,
            "        </div>",
            '        <div id="error-container" class="error-info" style="display: none;">',
            "            <h3>⚠️ Mermaid Syntax Error</h3>",
            "            <p>The diagram couldn't be rendered. This often happens due to:</p>",
            "            <ul>",
            "                <li>Invalid node naming (spaces without brackets)</li>",
            "                <li>Incorrect edge syntax</li>",
            "                <li>Circular references</li>",
            "            </ul>",
            "            <p><strong>Generated Code:</strong></p>",
            '            <div class="raw-code">' + mermaid_text + "</div>",
            "            <p>Please edit the <code>" + filename + "</code> file to fix syntax issues.</p>",
            "        </div>",
            '        <div class="footer">',
            "            <p><strong>Usage Options:</strong></p>",
            "            <p><strong>For SPL:</strong> Generate code with <code>spl3 mmd2spl " + filename + " -o " + base_name + ".spl</code></p>",
            "            <p><strong>For General Use:</strong> Copy diagram code for documentation, presentations, or other Mermaid tools</p>",
            '            <hr style="margin: 20px 0;">',
            '            <p><strong>About SPL:</strong> <a href="https://github.com/digital-duck/SPL" target="_blank">GitHub Repository</a> |',
            '               <a href="https://github.com/digital-duck/SPL#readme" target="_blank">Documentation</a></p>',
            '            <p><small>Visual workflow programming • General purpose workflow visualization tool</small></p>',
            "        </div>",
            "    </div>",
            "    <script>",
            "        mermaid.initialize({",
            "            startOnLoad: true,",
            "            theme: 'default',",
            "            securityLevel: 'loose',",
            "            errorLevel: 'warn'",
            "        });",
            "        window.addEventListener('error', function(e) {",
            "            if (e.message && e.message.toLowerCase().includes('mermaid')) {",
            "                document.getElementById('mermaid-container').style.display = 'none';",
            "                document.getElementById('error-container').style.display = 'block';",
            "            }",
            "        });",
            "        setTimeout(function() {",
            "            const container = document.getElementById('mermaid-container');",
            "            if (container && (container.innerHTML.includes('Syntax error') || container.innerHTML.includes('Parse error'))) {",
            "                container.style.display = 'none';",
            "                document.getElementById('error-container').style.display = 'block';",
            "            }",
            "        }, 2000);",
            "    </script>",
            "</body>",
            "</html>"
        ]
        html_content = "\n".join(html_parts)
        html_path = output_dir / (base_name + ".html")
        html_path.write_text(html_content, encoding="utf-8")
        additional_files.append("HTML (Browser): " + str(html_path))

        if preview:
            import webbrowser
            webbrowser.open("file://" + str(html_path.absolute()))
            click.echo("Preview opened in browser: " + str(html_path))

    # PNG format for images/presentations
    if save_png:
        png_path = output_dir / (base_name + ".png")
        try:
            png_generated = False
            import subprocess

            # Create a simple HTML for PNG generation
            png_html = """<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
<style>body{margin:0;padding:20px;background:white;font-family:Arial,sans-serif}
.mermaid{text-align:center}</style></head>
<body><div class="mermaid">""" + mermaid_text + """</div>
<script>mermaid.initialize({startOnLoad:true,theme:'default',securityLevel:'loose'});</script>
</body></html>"""

            png_html_path = output_dir / (base_name + "_temp.html")
            png_html_path.write_text(png_html, encoding="utf-8")

            # Try Chrome/Chromium browsers
            for chrome_cmd in ["google-chrome", "chromium-browser", "chromium", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]:
                try:
                    result = subprocess.run([
                        chrome_cmd, "--headless", "--disable-gpu",
                        "--window-size=1200,800", "--screenshot=" + str(png_path),
                        "file://" + str(png_html_path.absolute())
                    ], capture_output=True, timeout=30)

                    if result.returncode == 0 and png_path.exists():
                        png_html_path.unlink()  # Clean up
                        additional_files.append("PNG Image: " + str(png_path))
                        png_generated = True
                        break
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue

            # Clean up temp file
            if png_html_path.exists():
                png_html_path.unlink()

            if not png_generated:
                click.echo("Warning: PNG generation requires Chrome/Chromium browser", err=True)

        except Exception as e:
            click.echo("Warning: PNG generation failed: " + str(e), err=True)

    # Report additional files
    if additional_files:
        click.echo("Additional formats generated:")
        for file_desc in additional_files:
            click.echo("  - " + file_desc)

    # Summary
    click.echo("\nAll files saved to: " + str(output_dir))


# ------------------------------------------------------------------ #
# spl3 spl2mmd                                                        #
# ------------------------------------------------------------------ #

@main.command("spl2mmd")
@click.argument("spl_files", nargs=-1, required=True, metavar="SPL_FILE...")
@click.option("--out-dir", default=None, metavar="DIR",
              help="Output directory for all generated files (default: same directory as each input).")
@click.option("--preview/--no-preview", default=True, show_default=True,
              help="Open each diagram in the browser after generation.")
@click.option("--save-html/--no-save-html", default=True, show_default=True,
              help="Save an .html browser-viewable file alongside the .mmd.")
@click.option("--save-markdown/--no-save-markdown", "--save-md/--no-save-md",
              default=True, show_default=True,
              help="Save a .md file with a fenced mermaid code block.")
@click.option("--save-png/--no-save-png", default=True, show_default=True,
              help="Save a .png image via headless Chrome/Chromium (requires browser).")
@click.option("--save-pdf/--no-save-pdf", default=False, show_default=True,
              help="Save a print-ready .pdf (tries mmdc then Chrome headless).")
@click.option("--save-spl/--no-save-spl", default=True, show_default=True,
              help="Copy the source .spl file into --out-dir alongside the other outputs.")
def cmd_spl2mmd(spl_files, out_dir, preview, save_html, save_markdown, save_png, save_pdf, save_spl):
    """Generate a Mermaid flowchart for each SPL_FILE (AST-direct, no LLM).

    Each .spl file is parsed and its workflow/procedure AST nodes are converted
    to a standalone Mermaid flowchart.  Multi-file projects (workflows that CALL
    each other) are rendered as one diagram per file — inter-file calls appear as
    CALL subroutine nodes, showing what is invoked without inlining the callee.

    By default saves .mmd + .html + .md and opens a browser preview.
    Use --no-preview / --no-save-html etc. to suppress individual outputs.

    Node shapes reflect statement types:
      parallelogram — GENERATE (LLM call)
      subroutine    — CALL (procedure dispatch)
      diamond       — WHILE / EVALUATE / exception handler
      cylinder      — STORE / storage-assign
      stadium       — Start / End / RETURN / RAISE
      flag          — LOGGING

    \b
    Examples:
      spl3 spl2mmd workflow.spl
      spl3 spl2mmd *.spl --out-dir diagrams/
      spl3 spl2mmd workflow.spl --no-preview --no-save-html
      spl3 spl2mmd workflow.spl --save-pdf --out-dir diagrams/
      spl3 spl2mmd workflow.spl --save-png --save-pdf --out-dir diagrams/
    """
    import shutil
    import subprocess
    from pathlib import Path
    from spl3.spl2mmd import spl_to_mermaid, NoWorkflowError

    errors = 0
    for spl_file in spl_files:
        path = Path(spl_file).resolve()
        if not path.exists():
            click.echo(f"MISSING: {spl_file}", err=True)
            errors += 1
            continue

        source = path.read_text(encoding="utf-8")
        try:
            mermaid_text = spl_to_mermaid(source)
        except NoWorkflowError as exc:
            click.echo(f"WARN: {path.name} — {exc}", err=True)
            continue
        except Exception as exc:
            click.echo(f"FAILED: {spl_file} — {exc}", err=True)
            errors += 1
            continue

        output_dir = Path(out_dir).resolve() if out_dir else path.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        base_name = path.stem

        # ── .mmd ──────────────────────────────────────────────────────────
        mmd_path = output_dir / (base_name + ".mmd")
        mmd_path.write_text(mermaid_text, encoding="utf-8")
        click.echo(f"OK: {spl_file}")
        click.echo(f"  + MMD:      {mmd_path}")

        # ── .spl copy ─────────────────────────────────────────────────────
        if save_spl and path.parent != output_dir:
            spl_copy = output_dir / path.name
            shutil.copy2(path, spl_copy)
            click.echo(f"  + SPL:      {spl_copy}")

        # ── .md ───────────────────────────────────────────────────────────
        if save_markdown:
            title = base_name.replace("_", " ").replace("-", " ").title()
            md_content = (
                f"# {title} Workflow\n\n"
                f"Generated from `{path.name}` via `spl3 spl2mmd` (AST-direct, no LLM).\n\n"
                "## Mermaid Diagram\n\n"
                f"```mermaid\n{mermaid_text}\n```\n"
            )
            md_path = output_dir / (base_name + ".md")
            md_path.write_text(md_content, encoding="utf-8")
            click.echo(f"  + Markdown: {md_path}")

        # ── .html ─────────────────────────────────────────────────────────
        html_path = output_dir / (base_name + ".html")
        if save_html or preview or save_png or save_pdf:
            title = base_name.replace("_", " ").replace("-", " ").title()
            html_content = "\n".join([
                "<!DOCTYPE html>",
                "<html>",
                "<head>",
                '    <meta charset="UTF-8">',
                f"    <title>{title} — SPL Workflow</title>",
                '    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>',
                "    <style>",
                "        body{font-family:Arial,sans-serif;margin:30px;background:#f5f5f5}",
                "        .box{max-width:1200px;margin:0 auto;background:white;padding:24px;",
                "             border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,.1)}",
                "        h1{border-bottom:2px solid #eee;padding-bottom:8px}",
                "        .mermaid{text-align:center;margin:20px 0}",
                "        .meta{color:#666;font-size:.9em}",
                "    </style>",
                "</head>",
                "<body>",
                '    <div class="box">',
                f"        <h1>{title} Workflow</h1>",
                f'        <p class="meta">Source: <code>{path.name}</code> &nbsp;|&nbsp; '
                "Generated by <code>spl3 spl2mmd</code> (AST-direct)</p>",
                '        <div class="mermaid">',
                mermaid_text,
                "        </div>",
                "    </div>",
                "    <script>",
                "        mermaid.initialize({startOnLoad:true,theme:'default',securityLevel:'loose'});",
                "    </script>",
                "</body>",
                "</html>",
            ])
            html_path.write_text(html_content, encoding="utf-8")
            if save_html:
                click.echo(f"  + HTML:     {html_path}")
            if preview:
                import webbrowser
                webbrowser.open("file://" + str(html_path))

        # ── .png ─────────────────────────────────────────────────────────
        if save_png:
            png_path = output_dir / (base_name + ".png")
            png_generated = False

            # Build a puppeteer config for mmdc that enables --no-sandbox
            # (required on Linux when not running as root).
            import json as _json, tempfile as _tempfile
            _pup_cfg = _json.dumps({"args": ["--no-sandbox", "--disable-setuid-sandbox"]})
            _pup_file = _tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            )
            _pup_file.write(_pup_cfg)
            _pup_file.close()

            # Try mmdc first — renders the full diagram at natural size.
            for mmdc_cmd in ["mmdc", "npx", "@mermaid-js/mermaid-cli"]:
                try:
                    cmd_args = (
                        [mmdc_cmd, "-i", str(mmd_path), "-o", str(png_path),
                         "-p", _pup_file.name, "-t", "default", "-b", "white"]
                        if mmdc_cmd == "mmdc"
                        else ["npx", "--yes", "@mermaid-js/mermaid-cli",
                              "-i", str(mmd_path), "-o", str(png_path),
                              "-p", _pup_file.name, "-t", "default", "-b", "white"]
                    )
                    result = subprocess.run(cmd_args, capture_output=True, timeout=60)
                    if result.returncode == 0 and png_path.exists():
                        click.echo(f"  + PNG:      {png_path}")
                        png_generated = True
                        break
                    if mmdc_cmd == "npx":
                        break
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    if mmdc_cmd == "npx":
                        break
                    continue

            import os as _os
            _os.unlink(_pup_file.name)

            if not png_generated:
                click.echo("  ! PNG skipped: mmdc not found (install @mermaid-js/mermaid-cli)", err=True)

        # ── .pdf ─────────────────────────────────────────────────────────
        if save_pdf:
            pdf_path = output_dir / (base_name + ".pdf")
            pdf_generated = False

            # Build a print-optimised HTML page (A4 landscape, neutral theme,
            # no interactive chrome — suited for paper/publication).
            title = base_name.replace("_", " ").replace("-", " ").title()
            print_html = "\n".join([
                "<!DOCTYPE html>",
                "<html>",
                "<head>",
                '    <meta charset="UTF-8">',
                f"    <title>{title} — SPL Workflow</title>",
                '    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>',
                "    <style>",
                "        @page { size: A4 landscape; margin: 1.5cm; }",
                "        body { font-family: Arial, sans-serif; margin: 0; background: white; }",
                "        h2 { font-size: 14pt; margin: 0 0 4px 0; }",
                "        .meta { font-size: 9pt; color: #555; margin-bottom: 14px; }",
                "        .mermaid { text-align: center; }",
                "        svg { max-width: 100%; height: auto; }",
                "    </style>",
                "</head>",
                "<body>",
                f"    <h2>{title} Workflow</h2>",
                f'    <p class="meta">Source: {path.name} &nbsp;|&nbsp; '
                "Generated by spl3 spl2mmd (AST-direct)</p>",
                '    <div class="mermaid">',
                mermaid_text,
                "    </div>",
                "    <script>",
                "        mermaid.initialize({startOnLoad: true, theme: 'neutral', securityLevel: 'loose'});",
                "    </script>",
                "</body>",
                "</html>",
            ])
            print_html_path = output_dir / (base_name + "_print.html")
            print_html_path.write_text(print_html, encoding="utf-8")

            # 1. Try mmdc (mermaid-cli) — native vector PDF, best quality
            try:
                result = subprocess.run(
                    ["mmdc", "-i", str(mmd_path), "-o", str(pdf_path),
                     "-t", "neutral", "-b", "white"],
                    capture_output=True, timeout=60,
                )
                if result.returncode == 0 and pdf_path.exists():
                    click.echo(f"  + PDF:      {pdf_path}  (via mmdc)")
                    pdf_generated = True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

            # 2. Fall back to Chrome headless --print-to-pdf
            if not pdf_generated:
                for chrome_cmd in [
                    "google-chrome", "chromium-browser", "chromium",
                    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                ]:
                    try:
                        result = subprocess.run(
                            [chrome_cmd, "--headless", "--disable-gpu",
                             "--no-sandbox",
                             f"--print-to-pdf={pdf_path}",
                             "--print-to-pdf-no-header",
                             "--virtual-time-budget=8000",
                             "file://" + str(print_html_path)],
                            capture_output=True, timeout=60,
                        )
                        if result.returncode == 0 and pdf_path.exists():
                            click.echo(f"  + PDF:      {pdf_path}  (via Chrome)")
                            pdf_generated = True
                            break
                    except (subprocess.TimeoutExpired, FileNotFoundError):
                        continue

            # Clean up the temporary print HTML
            if print_html_path.exists():
                print_html_path.unlink()

            if not pdf_generated:
                click.echo(
                    "  ! PDF skipped: install mmdc (`npm i -g @mermaid-js/mermaid-cli`) "
                    "or Chrome/Chromium",
                    err=True,
                )

    if errors:
        raise SystemExit(errors)


# ------------------------------------------------------------------ #
# spl3 mmd2spl                                                    #
# ------------------------------------------------------------------ #

@main.command("mmd2spl")
@click.argument("mermaid_file")
@click.option("--output", "-o", default=None, metavar="FILE",
              help="Write generated SPL to FILE.")
@click.option("--adapter", default=None, metavar="NAME",
              help="LLM adapter to use for generation (e.g. claude_cli, ollama).")
@click.option("--model", "-m", default=None, metavar="MODEL",
              help="Model override for the adapter.")
@click.option("--validate/--no-validate", default=True, show_default=True,
              help="Validate generated SPL syntax.")
@click.option("--template", default="workflow", show_default=True,
              type=click.Choice(["workflow", "function"]),
              help="Base SPL template type.")
@click.option("--pattern-hints", default=None, metavar="HINTS",
              help="Comma-separated hints for SPL patterns (e.g., 'linear,parallel').")
@click.option("--prompt", "prompt_debug", is_flag=True, default=False,
              help="Display the LLM prompt and exit.")
@click.option("--timeout", default=600, show_default=True, metavar="SECONDS",
              help="LLM call timeout in seconds.")
def cmd_mmd2spl(mermaid_file, output, adapter, model, validate, template, pattern_hints, prompt_debug, timeout):
    """Generate SPL workflow from Mermaid flowchart diagram.

    Converts a Mermaid flowchart into executable SPL code, mapping visual
    elements to SPL constructs like GENERATE, EVALUATE, WHILE, and CALL PARALLEL.

    \b
    Examples:
      spl3 mmd2spl workflow.mmd -o workflow.spl
      spl3 mmd2spl diagram.mmd --template function --validate
      spl3 mmd2spl review.mmd --pattern-hints "iterative,quality-gate"
    """
    import re as _re
    from pathlib import Path

    # Read Mermaid file
    if not Path(mermaid_file).exists():
        raise click.ClickException(f"Mermaid file not found: {mermaid_file}")

    mermaid_content = Path(mermaid_file).read_text(encoding="utf-8")
    workflow_name = Path(mermaid_file).stem.replace("-", "_")

    if prompt_debug and not adapter:
        raise click.UsageError("--prompt requires --adapter to be specified.")

    if adapter:
        # LLM-powered generation
        try:
            from spl3.adapters import get_adapter
        except ImportError:
            raise click.ClickException("spl-llm 2.0 not installed: pip install spl-llm>=2.0.0")

        llm = get_adapter(adapter, timeout=timeout, **({"model": model} if model else {}))
        prompt_text = _MMD2SPL_PROMPT.format(mermaid=mermaid_content)
        
        if prompt_debug:
            click.echo("=" * 70)
            click.echo("LLM PROMPT:")
            click.echo("=" * 70)
            click.echo(prompt_text)
            return

        click.echo(f"Generating SPL from {mermaid_file} using {adapter}...")
        result = asyncio.run(llm.generate(prompt_text, **({"model": model} if model else {})))
        spl_code = result if isinstance(result, str) else getattr(result, "content", str(result))
        
        # Extract SPL between custom markers (preferred) or markdown fences.
        # Custom markers are robust: no inner-fence ambiguity, no preamble bleed.
        lines = spl_code.splitlines()
        SPL_BEGIN = "___SPL_BEGIN___"
        SPL_END   = "___SPL_END___"
        begin_idx = next((i for i, l in enumerate(lines) if l.strip() == SPL_BEGIN), None)
        end_idx   = next((i for i, l in enumerate(lines) if l.strip() == SPL_END),   None)
        if begin_idx is not None and end_idx is not None and end_idx > begin_idx:
            lines = lines[begin_idx + 1:end_idx]
        # Always strip markdown fences — LLM sometimes wraps inside markers too
        open_idx = next(
            (i for i, l in enumerate(lines) if _re.match(r"^```(spl)?\s*$", l.strip())),
            None,
        )
        if open_idx is not None:
            lines = lines[open_idx + 1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        spl_code = "\n".join(lines).strip()
        spl_code = format_spl(spl_code)
    else:
        # Basic Mermaid parsing - extract nodes and connections
        nodes = {}
        edges = []

        # Parse flowchart nodes: A[Label] or A{Decision} or A(Process)
        node_pattern = r'(\\w+)(?:\\[(.*?)\\]|\\{(.*?)\\}|\\((.*?)\\))'
        for match in _re.finditer(node_pattern, mermaid_content):
            node_id = match.group(1)
            label = match.group(2) or match.group(3) or match.group(4) or node_id

            # Determine node type from syntax
            if match.group(3):  # {label} = decision
                node_type = "decision"
            elif any(keyword in label.lower() for keyword in ["start", "begin"]):
                node_type = "start"
            elif any(keyword in label.lower() for keyword in ["end", "finish", "return"]):
                node_type = "end"
            else:
                node_type = "process"

            nodes[node_id] = {"label": label, "type": node_type}

        # Parse edges: A --> B or A -->|label| B
        edge_pattern = r'(\\w+)\\s*(?:-->|->)\\s*(?:\\|([^|]*)\\|\\s*)?(\\w+)'
        for match in _re.finditer(edge_pattern, mermaid_content):
            from_node = match.group(1)
            edge_label = match.group(2)
            to_node = match.group(3)
            edges.append({"from": from_node, "to": to_node, "label": edge_label})

        # Generate SPL based on structure
        # Detect patterns
        has_loops = any(
            any(e2["from"] == edge["to"] and e2["to"] == edge["from"] for e2 in edges)
            for edge in edges
        )

        has_decisions = any(node["type"] == "decision" for node in nodes.values())
        has_parallel = len([n for n in nodes.values() if n["type"] == "process"]) > 3

        # Build SPL
        spl_lines = []

        if template == "workflow":
            spl_lines.extend([
                f"WORKFLOW {workflow_name}",
                "  INPUT @input TEXT",
                "  OUTPUT @result TEXT",
                "DO"
            ])

            # Add variables
            for node_id, node in nodes.items():
                if node["type"] == "process":
                    var_name = _re.sub(r'\W+', '_', node["label"].lower())
                    spl_lines.append(f"  @{var_name} := '';")

            # Add main logic
            process_nodes = [n for n in nodes.values() if n["type"] == "process"]
            decision_nodes = [n for n in nodes.values() if n["type"] == "decision"]

            if has_loops and decision_nodes:
                # Iterative pattern
                spl_lines.extend([
                    "  @iteration := 0;",
                    "  @max_iterations := 3;",
                    "",
                    "  WHILE @iteration < @max_iterations DO",
                    "    DO"
                ])

                for node in process_nodes[:2]:  # Main processes
                    var_name = _re.sub(r'\W+', '_', node["label"].lower())
                    func_name = _re.sub(r'\W+', '_', node["label"].lower()).strip('_')
                    # Avoid reserved keywords
                    if func_name in ['input', 'output', 'result', 'return', 'end', 'do', 'while', 'evaluate', 'when', 'then', 'else']:
                        func_name = f"process_{func_name}"
                    spl_lines.append(f"      GENERATE {func_name}(@input) INTO @{var_name};")

                # Add decision logic
                if decision_nodes:
                    decision = decision_nodes[0]
                    spl_lines.extend([
                        f"      EVALUATE @{var_name}",
                        f"        WHEN contains('complete') THEN",
                        f"          RETURN @{var_name} WITH status = 'complete';",
                        f"        ELSE",
                        f"          @iteration := @iteration + 1;",
                        "      END;"
                    ])

                spl_lines.extend([
                    "    END;",
                    "  END;",
                ])

            elif has_decisions:
                # Conditional pattern
                for node in process_nodes:
                    var_name = _re.sub(r'\W+', '_', node["label"].lower())
                    func_name = _re.sub(r'\W+', '_', node["label"].lower()).strip('_')
                    # Avoid reserved keywords
                    if func_name in ['input', 'output', 'result', 'return', 'end', 'do', 'while', 'evaluate', 'when', 'then', 'else']:
                        func_name = f"process_{func_name}"
                    spl_lines.append(f"  GENERATE {func_name}(@input) INTO @{var_name};")

                if decision_nodes:
                    decision = decision_nodes[0]
                    spl_lines.extend([
                        f"  EVALUATE @{var_name}",
                        f"    WHEN contains('condition') THEN",
                        f"      @result := 'path_a';",
                        f"    ELSE",
                        f"      @result := 'path_b';",
                        "  END;"
                    ])

            elif has_parallel:
                # Parallel pattern
                spl_lines.append("  CALL PARALLEL")
                for i, node in enumerate(process_nodes[:3]):  # Limit to 3 parallel
                    var_name = _re.sub(r'\W+', '_', node["label"].lower())
                    func_name = _re.sub(r'\W+', '_', node["label"].lower()).strip('_')
                    # Avoid reserved keywords
                    if func_name in ['input', 'output', 'result', 'return', 'end', 'do', 'while', 'evaluate', 'when', 'then', 'else']:
                        func_name = f"process_{func_name}"
                    comma = "," if i < min(2, len(process_nodes) - 1) else ""
                    spl_lines.append(f"    {func_name}(@input) INTO @{var_name}{comma}")
                spl_lines.append("  END")

            else:
                # Linear pattern
                for node in process_nodes:
                    var_name = _re.sub(r'\W+', '_', node["label"].lower())
                    func_name = _re.sub(r'\W+', '_', node["label"].lower()).strip('_')
                    # Avoid reserved keywords
                    if func_name in ['input', 'output', 'result', 'return', 'end', 'do', 'while', 'evaluate', 'when', 'then', 'else']:
                        func_name = f"process_{func_name}"
                    spl_lines.append(f"  GENERATE {func_name}(@input) INTO @{var_name};")

            spl_lines.extend([
                "  RETURN @result;",
                "END;"
            ])

        else:  # function template
            func_name = workflow_name
            spl_lines.extend([
                f"CREATE FUNCTION {func_name}(input TEXT) RETURNS TEXT AS $$",
                f"Process the input through {workflow_name} workflow.",
                "$$;"
            ])

        spl_code = "\n".join(spl_lines)

    # Post-process: rewrite LLM-generated constructs not in SPL grammar
    spl_code = _rewrite_for_loops(spl_code)

    # Output
    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(spl_code, encoding="utf-8")
        click.echo(f"SPL code written to: {output}")

        # Also generate .mmd file for reference
        mmd_output = out_path.with_suffix('.mmd')
        mmd_output.write_text(mermaid_content, encoding="utf-8")
        click.echo(f"Mermaid reference saved to: {mmd_output}")
    else:
        click.echo(spl_code)

    # Always validate the generated SPL using the real parser
    try:
        from spl.lexer import Lexer
        from spl3.parser import SPL3Parser
        tokens = Lexer(spl_code).tokenize()
        SPL3Parser(tokens).parse()
        click.echo("Validation: OK")
    except Exception as exc:
        click.echo(f"Validation: FAILED — {exc}", err=True)
        click.echo("  Fix the .spl file or re-run mmd2spl.", err=True)


# ------------------------------------------------------------------ #
# spl3 validate                                                       #
# ------------------------------------------------------------------ #

@main.command("validate")
@click.argument("spl_files", nargs=-1, required=True)
def cmd_validate(spl_files):
    """Validate SPL syntax of one or more SPL_FILES.

    \b
    Examples:
      spl3 validate workflow.spl
      spl3 validate tests/claude_cli/sonnet/*.spl
    """
    from pathlib import Path
    from spl.lexer import Lexer
    from spl3.parser import SPL3Parser

    errors = 0
    for spl_file in spl_files:
        path = Path(spl_file)
        if not path.exists():
            click.echo(f"MISSING: {path}", err=True)
            errors += 1
            continue
        source = path.read_text(encoding="utf-8")
        try:
            tokens = Lexer(source).tokenize()
            SPL3Parser(tokens).parse()
            click.echo(f"OK: {path}")
        except Exception as exc:
            click.echo(f"FAILED: {path} — {exc}", err=True)
            errors += 1

    if errors:
        raise SystemExit(errors)


# ------------------------------------------------------------------ #
# spl3 explain                                                        #
# ------------------------------------------------------------------ #

@main.command("explain")
@click.argument("spl_file")
def cmd_explain(spl_file):
    """Show execution plan for SPL_FILE (no LLM call)."""
    from pathlib import Path
    from spl.lexer import Lexer
    from spl.analyzer import Analyzer
    from spl.optimizer import Optimizer
    from spl.explain import explain_plans
    from spl3.parser import SPL3Parser

    path = Path(spl_file)
    if not path.exists():
        raise click.ClickException(f"File not found: {path}")
    source = path.read_text(encoding="utf-8")
    try:
        tokens = Lexer(source).tokenize()
        ast = SPL3Parser(tokens).parse()
        analysis = Analyzer().analyze(ast)
        plans = Optimizer().optimize(analysis)
        click.echo(explain_plans(plans))
    except click.ClickException:
        raise
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc


def _extract_spec_intro(text: str, max_fallback: int = 1000) -> str:
    """Extract sections 0 and 1 from a splc-describe spec file.

    Sections are headings like '## 0. Title' or '## 1. Title'.
    Returns sections 0+1 when found; falls back to first max_fallback chars.
    """
    import re
    # Locate section 0 heading (any # level, number 0 followed by . or space)
    sec0 = re.search(r'^#{1,6}\s+0[.\s]', text, re.MULTILINE)
    if not sec0:
        return text[:max_fallback].strip()
    # Locate section 2 heading — that marks the end of what we need
    sec2 = re.search(r'^#{1,6}\s+2[.\s]', text, re.MULTILINE)
    end = sec2.start() if sec2 else len(text)
    return text[sec0.start():end].strip()


@main.command("vibe")
@click.argument("description", default=None, required=False, metavar="DESCRIPTION")
@click.option("--description", "-d", "description_opt", default=None, metavar="TEXT_OR_FILE",
              help="Natural language requirement or file path (overrides positional arg).")
@click.option("--target", "-t", "lang", default="python/pocketflow", show_default=True,
              help="Target language/framework (e.g. go, ts, python/langgraph).")
@click.option("--adapter", default="ollama", show_default=True,
              help="LLM adapter to use for generation.")
@click.option("--model", "-m", default=None, metavar="MODEL",
              help="Model override for the adapter.")
@click.option("--output", "-o", default=None, metavar="FILE",
              help="Write generated code to FILE (single-file mode).")
@click.option("--out-dir", default=None, metavar="DIR",
              help="Write all outputs (code, README.md, test_data.py) to DIR (folder mode).")
@click.option("--rag/--no-rag", "use_rag", default=True, show_default=True,
              help="Include RAG examples from the shared SPL recipe store.")
@click.option("--rag-k", default=3, show_default=True, type=click.IntRange(1, 10),
              help="Number of RAG examples to include when --rag is on.")
@click.option("--references", multiple=True, metavar="URL_OR_PATH",
              help="Reference codebase(s) to ground the output.")
@click.option("--no-readme", is_flag=True, default=False,
              help="Skip generating readme section.")
@click.option("-v", "--verbose", "verbose", is_flag=True, default=False,
              help="Print progress and token counts.")
@click.option("--prompt", "prompt_debug", is_flag=True, default=False,
              help="Display the LLM prompt and exit.")
def cmd_vibe(description, description_opt, lang, adapter, model, output, out_dir, use_rag, rag_k, references, no_readme, verbose, prompt_debug):
    """One-shot prototype generator: NL description → working code + README + test data.

    Generates a complete, runnable implementation directly from a natural language
    description or spec file — no .mmd or .spl IR steps required. Outputs code,
    README.md, and test data in one pass. Works with any model available via
    ollama (local) or openrouter (400+ cloud models).

    \b
    Use cases:
      • Rapid prototyping — get a working skeleton in seconds
      • Multi-model comparison — run the same spec through claude, qwen, gemini
      • Ablation baseline — compare against the full IR pipeline (S1→S6) to
        quantify the value of the Mermaid + SPL intermediate representations

    \b
    Output (folder mode --out-dir):
      {dir}/vibe_output.py     generated implementation
      {dir}/README.md          setup, usage, expected output
      {dir}/test_data.py       2-3 realistic test inputs

    \b
    Examples:
      # Quick prototype to a folder (recommended)
      spl3 vibe "build a ReAct research agent" --out-dir ./out

      # Against a spec file, specific model via openrouter
      spl3 vibe --description spec.md --out-dir ./out \\
        --adapter openrouter -m qwen/qwen3.6-plus

      # Local model via ollama
      spl3 vibe "self-refine writing agent" --out-dir ./out \\
        --adapter ollama -m gemma3

      # Single-file mode (legacy)
      spl3 vibe "rag pipeline" -o out.py --adapter claude_cli

      # Preview prompt before sending
      spl3 vibe --description spec.md --adapter openrouter -m qwen/qwen3.6-plus --prompt
    """
    from pathlib import Path
    from spl3.splc.cli import (
        SUPPORTED_LANGS, VIBE_SYSTEM_PROMPT, VIBE_README_INSTRUCTION,
        _fetch_rag_examples, _fetch_references, compile_llm_code
    )

    if lang not in SUPPORTED_LANGS:
        available = ", ".join(SUPPORTED_LANGS.keys())
        raise click.UsageError(f"Invalid target '{lang}'. Supported: {available}")

    lang_meta = SUPPORTED_LANGS[lang]

    # --description option takes precedence over positional arg
    raw = description_opt or description
    if not raw:
        raise click.UsageError(
            "Provide a description as a positional argument or via --description."
        )

    # If it looks like a file path, read it and extract the relevant intro
    candidate = Path(raw)
    if candidate.exists() and candidate.is_file():
        raw_desc = _extract_spec_intro(candidate.read_text(encoding="utf-8"))
        if verbose:
            click.echo(f"  Spec extracted: {len(raw_desc)} chars (sections 0+1 or first 1000)")
    else:
        raw_desc = raw

    # ── Fetch references ──────────────────────────────────────────────────────
    ref_context = _fetch_references(references, verbose=verbose)

    # ── RAG few-shot examples ─────────────────────────────────────────────────
    rag_context = ""
    if use_rag:
        # Pass raw_desc as the RAG query directly — bypasses _spl_to_query()
        # which is designed for SPL syntax and would return "SPL workflow" for
        # natural language input.
        rag_context = _fetch_rag_examples(raw_desc, lang, k=rag_k, verbose=verbose, query=raw_desc)

    # ── Build prompt ──────────────────────────────────────────────────────────
    readme_instruction = "" if no_readme else VIBE_README_INSTRUCTION

    vibe_system = VIBE_SYSTEM_PROMPT.format(
        lang_label   = lang_meta["label"],
        readme_instr = readme_instruction,
    )

    prompt_parts = [vibe_system]
    if rag_context:
        prompt_parts.append(rag_context)
    if ref_context:
        prompt_parts.append(ref_context)

    prompt_parts.append(
        f"# Requirement to Implement\n\n"
        f"{raw_desc}\n\n"
        f"Generate the {lang_meta['label']} code now."
    )

    full_prompt = "\n\n---\n\n".join(prompt_parts)

    if prompt_debug:
        click.echo("=" * 70)
        click.echo("LLM PROMPT:")
        click.echo("=" * 70)
        click.echo(full_prompt)
        click.echo(f"\n[Prompt length: {len(full_prompt)} chars / ~{len(full_prompt)//4} tokens]")
        return

    click.echo(f"Vibing {lang} code using {adapter}...")
    # vibe prompts are large — double the default timeout for claude_cli
    impl_code, readme_text, test_data = compile_llm_code(
        full_prompt, adapter=adapter, model=model, verbose=verbose, timeout=600
    )

    ext = lang_meta.get("ext", ".py").lstrip(".")  # strip leading dot: ".py" → "py"

    if out_dir:
        # ── Folder mode: write code + README.md + test_data.py to out_dir ──
        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        # derive a clean stem from the description or lang
        stem = Path(output).stem if output else "vibe_output"
        code_file = out_path / f"{stem}.{ext}"
        code_file.write_text(impl_code, encoding="utf-8")
        click.echo(f"Code    → {code_file}")
        if readme_text and not no_readme:
            readme_file = out_path / "README.md"
            readme_file.write_text(readme_text, encoding="utf-8")
            click.echo(f"Readme  → {readme_file}")
        if test_data:
            test_file = out_path / f"test_data.{ext}"
            test_file.write_text(test_data, encoding="utf-8")
            click.echo(f"Tests   → {test_file}")
    elif output:
        # ── Single-file mode ─────────────────────────────────────────────────
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(impl_code, encoding="utf-8")
        click.echo(f"Code written to: {output}")
        if readme_text and not no_readme:
            readme_path = out_path.with_name(out_path.stem + "-readme.md")
            readme_path.write_text(readme_text, encoding="utf-8")
            click.echo(f"Readme written to: {readme_path}")
        if test_data:
            test_path = out_path.with_name(out_path.stem + f"-test_data.{ext}")
            test_path.write_text(test_data, encoding="utf-8")
            click.echo(f"Test data written to: {test_path}")
    else:
        click.echo(impl_code)
        if readme_text:
            click.echo("\n--- README ---\n")
            click.echo(readme_text)
        if test_data:
            click.echo("\n--- TEST DATA ---\n")
            click.echo(test_data)


# ------------------------------------------------------------------ #
# spl3 describe                                                       #
# ------------------------------------------------------------------ #

_MMD2SPL_PROMPT = """\
Convert the following Mermaid flowchart diagram into valid SPL 3.0 source code.

Mermaid Diagram:
```mermaid
{mermaid}
```

MANDATORY SPL 3.0 CONVENTIONS (FOLLOW EXACTLY):
1. WORKFLOW declaration syntax — INPUT/OUTPUT come BEFORE DO, no semicolons, one END;:
   WORKFLOW <name>
     INPUT @param1 TYPE, @param2 TYPE := default
     OUTPUT @result TYPE
   DO
     ... statements ...
   END;
   IMPORTANT: Do NOT put semicolons after INPUT or OUTPUT lines.
   IMPORTANT: Do NOT wrap the body in a nested DO...END; block — DO opens the body and END; closes the whole WORKFLOW.
2. Variable sigils: Use @ for workflow variables (e.g., @input, @result, @temp).
3. Variable assignment: Use := (e.g., @var := "value";).
4. LLM calls: Use GENERATE <fn>(<args>) INTO @<var>;
5. Tool calls: Use CALL <tool>(<args>) INTO @<var>;
6. Branching: Use EVALUATE @<var> WHEN contains("string") THEN ... ELSE ... END;
   IMPORTANT: EVALUATE must target a variable with @ prefix.
   IMPORTANT: WHEN clauses must use the contains("...") function for string matching.
7. Parallel execution: Use CALL PARALLEL ... END; for concurrent branches.
   Branches are comma-separated with NO CALL/GENERATE prefix and NO semicolons on each line:
   CALL PARALLEL
     branch_one(@arg) INTO @var1,
     branch_two(@arg) INTO @var2,
     branch_three(@arg) INTO @var3
   END;
   IMPORTANT: Do NOT write CALL or GENERATE before branch names inside CALL PARALLEL.
   IMPORTANT: Separate branches with commas, not semicolons. No semicolon on the last branch.
8. Looping: Use WHILE <condition> DO ... END;
   IMPORTANT: <condition> should include loop protection "@iteration < 3" to prevent infinite loops.
   IMPORTANT: Use = (single equals) for comparisons, NOT == (double equals). SPL has no == operator.
9. Helper functions: Define CREATE FUNCTION <name>(<params>) RETURNS <type> AS $$ <prompt> $$; at the top of the file.
   Note: Function parameters in CREATE FUNCTION do NOT use @ prefix.
   IMPORTANT: Inside $$ prompt bodies, use '' (two single quotes) instead of ' (apostrophe/single quote)
   to avoid string literal parsing errors. E.g. write "don''t" not "don't", "it''s" not "it's".
10. Return: Use RETURN @<var> WITH status = "complete";

The generated SPL must be complete, executable, and follow the logic of the diagram exactly.

OUTPUT FORMAT — REQUIRED:
Wrap the SPL code between these exact markers (nothing outside them):
___SPL_BEGIN___
<spl code here>
___SPL_END___
"""


_VIBE_PROMPT = """\
You are an expert software engineer. Your task is to generate complete, production-ready source code
for a {target} application based on the following requirement.

Requirement:
{description}

MANDATORY CONSTRAINTS:
1. Generate ONLY the source code. No explanations, no preambles, no markdown fences.
2. The code must be complete and executable.
3. If using Python/PocketFlow, ensure the workflow implements robust error handling and follows the
   latest patterns for node-based orchestration.
4. Include all necessary imports and a main execution block for testing.

Generate the code now.
"""


_DESCRIBE_PROMPT = """\
You are an expert in SPL (Structured Prompt Language), a declarative language for orchestrating
LLM workflows. SPL key constructs are:

  WORKFLOW <name>          — declares a named orchestration workflow
  INPUT @<var> <TYPE>      — input parameter declaration with optional default (:= value)
  OUTPUT @<var> <TYPE>     — output variable declaration
  CREATE FUNCTION <name>   — defines a reusable prompt template with {{parameter}} slots
  GENERATE <fn>(...) INTO @<var>   — calls an LLM using a prompt function, stores result
  CALL <tool>(...) INTO @<var>     — invokes a side-effect tool (e.g. write_file, http_get)
  WHILE <cond> DO ... END  — loop until condition is false
  EVALUATE @<var> WHEN <pattern> THEN ... ELSE ... END  — branch on variable content
  LOGGING <msg> LEVEL <INFO|DEBUG|WARN|ERROR>  — emit a structured log message
  RETURN @<var> WITH <k>=<v>, ...  — return value with metadata (status, iteration count, etc.)
  EXCEPTION WHEN <Type> THEN ...   — catch named exception types
  Exception types: MaxIterationsReached, BudgetExceeded, HallucinationDetected,
                   QualityBelowThreshold, ContextLengthExceeded, ModelOverloaded

Read the following SPL script and produce a functional specification in plain English.

Structure your output as Markdown with these sections IN ORDER:

## 0. High-level Description
Write 4-6 sentences of flowing prose (no bullet points) that form a self-contained description
rich enough to serve as a prompt for regenerating this workflow from scratch.
IMPORTANT: anchor your description using the SPL construct names above wherever they apply.
Cover ALL of the following that are present in the script:
- Pattern or technique (e.g. "self-refine", "map-reduce", "chain-of-thought")
- Every CREATE FUNCTION — name, role, and any notable prompt convention (sentinel tokens,
  scoring instructions, output format constraints)
- Control flow expressed in SPL terms: WHILE condition, EVALUATE branch, RETURN metadata
- Multi-model or multi-role design (which INPUT param drives each model choice)
- CALL side-effects (file writes, external tools) and LOGGING strategy
- Resource-limit strategy: EXCEPTION types handled and what each does

## 1. Purpose
One sentence summarising what the script accomplishes for the end user.

## 2. Inputs
A Markdown table — columns: Parameter | Default | Description.
List every INPUT variable declared in the workflow.

## 3. Process
Numbered steps in plain language following actual execution order.

## 4. Error Handling
Bullet list of each EXCEPTION case and the workflow's response.

## 5. Output
What is returned, including status codes and any metadata fields.

SPL Script:
```spl
{source}
```

Write the specification now.
"""


@main.command("describe")
@click.argument("spl_path")
@click.option("--adapter", default="ollama", show_default=True,
              help="LLM adapter to use for generation.")
@click.option("--model", default=None, metavar="MODEL",
              help="Model override for the adapter.")
@click.option("--spec-dir", default=None, metavar="DIR",
              help="Directory to write the spec file (default: same dir as input).")
@click.option("--prompt", "prompt_debug", is_flag=True, default=False,
              help="Display the LLM prompt and exit.")
def cmd_describe(spl_path, adapter, model, spec_dir, prompt_debug):
    """Generate a plain-English functional specification for a .spl file or folder.

    \b
    SPL_PATH can be:
      - a single .spl file  → spec named <stem>-spec.md
      - a folder            → all *.spl files in the folder are gathered and
                              described together as one recipe unit;
                              spec named <folder>-spec.md

    \b
    Examples:
      spl3 describe cookbook/05_self_refine/self_refine.spl
      spl3 describe cookbook/63_parallel_code_review/
      spl3 describe my_workflow.spl --adapter claude_cli --spec-dir docs/specs
    """
    path = Path(spl_path)
    if not path.exists():
        raise click.ClickException(f"Path not found: {path}")

    if path.is_dir():
        spl_files = sorted(path.glob("*.spl"))
        if not spl_files:
            raise click.ClickException(f"No .spl files found in {path}")
        # Concatenate all sources with file headers so the LLM sees the full recipe
        parts = []
        for f in spl_files:
            parts.append(f"-- File: {f.name}\n" + f.read_text(encoding="utf-8"))
        source = "\n\n".join(parts)
        stem = path.resolve().name          # folder name → spec stem
        spec_parent = path
    else:
        source = path.read_text(encoding="utf-8")
        stem = path.stem
        spec_parent = path.parent

    prompt = _DESCRIBE_PROMPT.format(source=source)

    if prompt_debug:
        click.echo("=" * 70)
        click.echo("LLM PROMPT:")
        click.echo("=" * 70)
        click.echo(prompt)
        return

    if path.is_dir():
        click.echo(f"Describing {len(spl_files)} .spl file(s) in {path.name}/: "
                   f"{', '.join(f.name for f in spl_files)}")
    else:
        click.echo(f"Generating spec for {path.name} ...")

    try:
        from spl3.adapters import get_adapter
    except ImportError:
        raise click.ClickException("spl-llm 2.0 not installed: pip install spl-llm>=2.0.0")

    llm = get_adapter(adapter, **({"model": model} if model else {}))
    result = asyncio.run(llm.generate(prompt, **({"model": model} if model else {})))
    spec_text = result if isinstance(result, str) else getattr(result, "content", str(result))

    spec_filename = f"{stem}-spec.md"
    if spec_dir:
        out_dir = Path(spec_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        spec_path = out_dir / spec_filename
    else:
        spec_path = spec_parent / spec_filename

    spec_path.write_text(spec_text, encoding="utf-8")
    click.echo(f"Spec written to: {spec_path}")


# ------------------------------------------------------------------ #
# spl3 compare                                                        #
# ------------------------------------------------------------------ #

@main.command("compare")
@click.argument("file1")
@click.argument("file2")
@click.option("--mode", "modes", multiple=True,
              type=click.Choice(["llm", "git-diff", "vector", "bert-score", "ged",
                                  "vision", "ast-diff", "structural"]),
              help=(
                  "Comparison tier(s). Repeatable. "
                  "Auto-detected from file extension when omitted: "
                  ".mmd→ged  .md/.spl→llm  .py/.js/.ts→git-diff  .png/.jpg→vision"
              ))
@click.option("--adapter", default="ollama", show_default=True,
              help="LLM adapter for all analysis (semantic, vision, synthesis, fallback).")
@click.option("--model", default=None, metavar="MODEL",
              help="Model override for the adapter.")
@click.option("--adapter-embed", default=None, metavar="NAME",
              help="Adapter for embedding modes (vector, bert-score). Defaults to --adapter.")
@click.option("--model-embed", default=None, metavar="MODEL",
              help="Model for embedding.")
@click.option("--adapter-synthesis", default=None, metavar="NAME",
              help="Adapter for synthesis pass. Defaults to --adapter.")
@click.option("--output", "-o", default=None, metavar="FILE",
              help="Write comparison report to FILE.")
@click.option("--format", "output_format", default="markdown", show_default=True,
              type=click.Choice(["markdown", "json", "text", "html"]),
              help="Output format. 'html' renders a 3-panel side-by-side report.")
@click.option("--focus", default="all", show_default=True,
              type=click.Choice(["all", "structure", "logic", "quality", "syntax", "spl"]),
              help="Focus for LLM semantic analysis. 'spl' uses SPL-domain-aware prompt.")
@click.option("--diff-style", default="unified", show_default=True,
              type=click.Choice(["unified", "context", "side-by-side"]),
              help="Style for git-diff output.")
@click.option("--no-color", is_flag=True, default=False,
              help="Disable ANSI color in diff output.")
@click.option("--synthesize/--no-synthesize", default=True, show_default=True,
              help="Run synthesis LLM pass to integrate all tier results into a verdict.")
@click.option("--prompt", "prompt_debug", is_flag=True, default=False,
              help="Display the LLM prompt and exit (mode=llm).")
def cmd_compare(file1, file2, modes, adapter, model, adapter_embed, model_embed,
                adapter_synthesis, output, output_format, focus, diff_style,
                no_color, synthesize, prompt_debug):

    """Multi-tier diff: topology · semantic · syntactic · structural · character · embedding.

    Automatically picks the best default tier(s) for each file type, then
    synthesizes all tier results into a single verdict:
    EQUIVALENT | REFACTORED | DEGRADED | DIVERGED.

    \b
    Tier mapping (auto-detected defaults):
      .mmd            → ged          (graph edit distance, SPL-node-aware)
      .md / .spl      → llm          (semantic intent analysis)
      .py / .js / .ts → git-diff     (character-level, upgradeable with --mode llm)
      .png / .jpg     → vision       (PIL pixel-diff; LLM vision if adapter supports it)

    \b
    Examples:
      spl3 compare orig.mmd roundtrip.mmd
      spl3 compare v1.spl v2.spl --mode llm --mode ast-diff
      spl3 compare old.py new.py --mode git-diff --mode structural
      spl3 compare a.png b.png --mode vision
      spl3 compare f1.md f2.md --mode llm --mode vector --format json
    """
    from pathlib import Path
    import json as _json
    import difflib
    import sys
    from datetime import datetime

    # Validate input files
    path1 = Path(file1)
    path2 = Path(file2)

    if not path1.exists():
        raise click.ClickException(f"File not found: {file1}")
    if not path2.exists():
        raise click.ClickException(f"File not found: {file2}")

    # Read file contents
    content1 = path1.read_text(encoding="utf-8")
    content2 = path2.read_text(encoding="utf-8")

    ext1 = path1.suffix.lower()
    ext2 = path2.suffix.lower()

    # Unspecified sub-adapters fall back to the main adapter — one setting covers most users.
    _adapter_embed     = adapter_embed     or adapter
    _adapter_synthesis = adapter_synthesis or adapter

    # ── Auto-detect comparison tier(s) from file extension ──────────────────
    _EXT_DEFAULTS: dict[str, list[str]] = {
        ".mmd":  ["ged"],
        ".md":   ["llm"],
        ".spl":  ["llm"],
        ".py":   ["git-diff"],
        ".js":   ["git-diff"],
        ".ts":   ["git-diff"],
        ".go":   ["git-diff"],
        ".rs":   ["git-diff"],
        ".png":  ["vision"],
        ".jpg":  ["vision"],
        ".jpeg": ["vision"],
        ".webp": ["vision"],
        ".svg":  ["llm"],
        ".txt":  ["git-diff"],
    }
    active_modes = list(modes)
    if not active_modes:
        primary_ext = ext1 if ext1 == ext2 else ext1
        active_modes = _EXT_DEFAULTS.get(primary_ext, ["llm", "git-diff"])
        click.echo(f"Auto-selected tier(s) for {primary_ext or 'unknown'}: {', '.join(active_modes)}")

    results = {}
    # ── Git Diff Mode ────────────────────────────────────────────────────────
    if "git-diff" in active_modes:
        lines1 = content1.splitlines(keepends=True)
        lines2 = content2.splitlines(keepends=True)
        mechanical_diff = ""

        if diff_style == "unified":
            diff_lines = list(difflib.unified_diff(
                lines1, lines2,
                fromfile=f"a/{path1.name}",
                tofile=f"b/{path2.name}",
                lineterm=""
            ))

            if not no_color and sys.stdout.isatty() and not output:
                # Add ANSI color codes for terminal output
                colored_diff = []
                for line in diff_lines:
                    if line.startswith('+++') or line.startswith('---'):
                        colored_diff.append(f"\033[1m{line}\033[0m")  # Bold
                    elif line.startswith('@@'):
                        colored_diff.append(f"\033[36m{line}\033[0m")  # Cyan
                    elif line.startswith('+'):
                        colored_diff.append(f"\033[32m{line}\033[0m")  # Green
                    elif line.startswith('-'):
                        colored_diff.append(f"\033[31m{line}\033[0m")  # Red
                    else:
                        colored_diff.append(line)
                mechanical_diff = "\n".join(colored_diff)
            else:
                mechanical_diff = "\n".join(diff_lines)

        elif diff_style == "context":
            diff_lines = list(difflib.context_diff(
                lines1, lines2,
                fromfile=f"a/{path1.name}",
                tofile=f"b/{path2.name}",
                lineterm=""
            ))
            mechanical_diff = "\n".join(diff_lines)

        elif diff_style == "side-by-side":
            # Create side-by-side diff
            if output_format == "markdown":
                # For markdown, create a simple side-by-side table
                side_by_side_lines = []
                side_by_side_lines.append(f"| {path1.name} | {path2.name} |")
                side_by_side_lines.append("|---|---|")

                # Get line-by-line differences
                for i, (l1, l2) in enumerate(zip(lines1, lines2)):
                    l1_clean = l1.rstrip('\n\r').replace('|', '\\|')
                    l2_clean = l2.rstrip('\n\r').replace('|', '\\|')
                    if l1 != l2:
                        side_by_side_lines.append(f"| **{l1_clean}** | **{l2_clean}** |")
                    else:
                        side_by_side_lines.append(f"| {l1_clean} | {l2_clean} |")

                # Handle different file lengths
                max_len = max(len(lines1), len(lines2))
                for i in range(min(len(lines1), len(lines2)), max_len):
                    if i < len(lines1):
                        l1_clean = lines1[i].rstrip('\n\r').replace('|', '\\|')
                        side_by_side_lines.append(f"| **{l1_clean}** | *[missing]* |")
                    else:
                        l2_clean = lines2[i].rstrip('\n\r').replace('|', '\\|')
                        side_by_side_lines.append(f"| *[missing]* | **{l2_clean}** |")

                mechanical_diff = "\n".join(side_by_side_lines)
            else:
                # side-by-side is only supported for markdown; fall back to unified diff
                click.echo("Warning: side-by-side diff is only supported with --format markdown. Falling back to unified.", err=True)
                diff_lines = list(difflib.unified_diff(
                    lines1, lines2,
                    fromfile=f"a/{path1.name}",
                    tofile=f"b/{path2.name}",
                    lineterm=""
                ))
                mechanical_diff = "\n".join(diff_lines)

        # If no differences found
        if not mechanical_diff.strip():
            mechanical_diff = "No mechanical differences found - files are identical."
        
        results["git-diff"] = mechanical_diff

    # ── LLM Semantic Mode ────────────────────────────────────────────────────
    if "llm" in active_modes:
        # Build comparison prompt based on focus
        focus_prompts = {
            "all":      "Provide a comprehensive comparison covering structure, logic, quality, and syntax.",
            "structure":"Focus on architectural and organizational differences.",
            "logic":    "Focus on logical flow, decision points, and process sequences.",
            "quality":  "Focus on completeness, sophistication, and best practices.",
            "syntax":   "Focus on syntax correctness, formatting, and technical accuracy.",
            "spl":      (
                "Focus on SPL-specific semantics: "
                "WORKFLOW/PROCEDURE identity (are the same workflows present?); "
                "GENERATE function signatures — these are the semantic heart (what the LLM is asked to do); "
                "CALL dependencies (which sub-workflows are invoked); "
                "WHILE/EVALUATE conditions (control-flow logic); "
                "EXCEPTION handlers (safety contracts — their presence or absence matters); "
                "@variable names (consistency of data flow). "
                "Treat operation signatures as primary evidence; syntax details as secondary."
            ),
        }

        prompt = f"""Compare these two files semantically and provide a detailed analysis.

**File 1**: {path1.name} ({ext1})
**File 2**: {path2.name} ({ext2})
**Focus**: {focus_prompts[focus]}

**File 1 Content:**
```
{content1}
```

**File 2 Content:**
```
{content2}
```

Please provide a structured comparison analysis with the following sections:

## Summary
Brief overview of the main differences and which file is stronger overall.

## Content Analysis
### File 1 Strengths
- Key advantages and well-implemented aspects

### File 2 Strengths
- Key advantages and well-implemented aspects

### Common Elements
- Shared concepts, structures, or approaches

## Detailed Comparison
### Structure & Organization
Compare the overall structure, flow, and organization.

### Logic & Completeness
Analyze logical flow, decision points, error handling, and completeness.

### Quality & Sophistication
Evaluate complexity, depth, best practices, and professional quality.

### Syntax & Technical Accuracy
Review syntax correctness, formatting, and technical implementation.

## Recommendations
1. **Best Choice**: Which file is better and why
2. **Improvements**: Specific suggestions to enhance the weaker file
3. **Hybrid Approach**: How to combine strengths from both files

## Scoring
Rate each file (1-10) on:
- Structure: [File1]/10, [File2]/10
- Logic: [File1]/10, [File2]/10
- Quality: [File1]/10, [File2]/10
- Overall: [File1]/10, [File2]/10

Provide actionable insights for choosing between or improving these files."""

        if prompt_debug:
            click.echo("=" * 70)
            click.echo("LLM PROMPT:")
            click.echo("=" * 70)
            click.echo(prompt)
            return

        try:
            from spl3.adapters import get_adapter
        except ImportError:
            raise click.ClickException("spl-llm 2.0 not installed: pip install spl-llm>=2.0.0")

        llm = get_adapter(adapter, **({"model": model} if model else {}))
        
        click.echo(f"Performing semantic comparison using {adapter}...")
        result = asyncio.run(llm.generate(prompt, **({"model": model} if model else {})))
        comparison_text = result if isinstance(result, str) else getattr(result, "content", str(result))
        results["llm"] = comparison_text

    # ── Vector Similarity Mode ───────────────────────────────────────────────
    if "vector" in active_modes:
        click.echo(f"Calculating vector similarity using {adapter_embed}...")
        try:
            try:
                from dd_embed import get_adapter as get_embed_adapter
            except ImportError:
                raise ImportError("dd-embed not installed: pip install dd-embed")
            embed_llm = get_embed_adapter(_adapter_embed, model_name=model_embed)
            
            # Simple average embedding for files (might need chunking for large files)
            emb1 = embed_llm.embed([content1]).embeddings[0]
            emb2 = embed_llm.embed([content2]).embeddings[0]
            
            # Cosine similarity
            import numpy as np
            norm1 = np.linalg.norm(emb1)
            norm2 = np.linalg.norm(emb2)
            similarity = np.dot(emb1, emb2) / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0.0
            results["vector"] = similarity
        except Exception as e:
            click.echo(f"Warning: Vector similarity failed: {e}", err=True)
            results["vector"] = f"Error: {e}"

    # ── BERTScore Mode ───────────────────────────────────────────────────────
    if "bert-score" in active_modes:
        click.echo("Calculating BERTScore...")
        try:
            try:
                import bert_score
                import torch
            except ImportError:
                raise ImportError("bert-score not installed: pip install bert-score torch")
            # Force CPU usage
            device = "cpu"
            # bert_score.score returns (P, R, F1) tensors
            P, R, F1 = bert_score.score([content2], [content1], lang="en", verbose=False, device=device)
            results["bert-score"] = {
                "precision": float(P[0]),
                "recall": float(R[0]),
                "f1": float(F1[0])
            }
        except Exception as e:
            click.echo(f"Warning: BERTScore failed: {e}", err=True)
            results["bert-score"] = f"Error: {e}"

    # ── GED Mode ─────────────────────────────────────────────────────────────
    if "ged" in active_modes:
        if ext1 != ".mmd" or ext2 != ".mmd":
            click.echo("Warning: GED mode is only meaningful for .mmd files. Skipping.", err=True)
            results["ged"] = "Skipped: GED requires .mmd input files."
        else:
            click.echo("Calculating Graph Edit Distance (GED)...")
            try:
                try:
                    import networkx as nx
                except ImportError:
                    raise ImportError("networkx not installed: pip install networkx")
                g1 = _parse_mermaid_to_nx(content1)
                g2 = _parse_mermaid_to_nx(content2)

                import difflib as _dl

                def _node_subst_cost(a1: dict, a2: dict) -> float:
                    """SPL-aware cost: type mismatch + label edit distance."""
                    t1, t2 = a1.get("node_type", ""), a2.get("node_type", "")
                    type_cost = (
                        0.0 if t1 == t2 else
                        0.5 if any(t1 in g and t2 in g
                                   for g in ({"llm","proc"}, {"ctrl"}, {"term"}, {"assign","log"}))
                        else 1.5
                    )
                    l1, l2 = a1.get("label", ""), a2.get("label", "")
                    if l1 and l2:
                        sim = _dl.SequenceMatcher(None, l1, l2).ratio()
                        label_cost = (1.0 - sim) * 0.5
                    else:
                        label_cost = 0.0
                    return type_cost + label_cost

                def _edge_subst_cost(e1: dict, e2: dict) -> float:
                    """Edge labels carry control-flow semantics (WHEN x, ELSE, True)."""
                    l1 = (e1.get("label") or "").strip()
                    l2 = (e2.get("label") or "").strip()
                    if l1 == l2:
                        return 0.0
                    if bool(l1) != bool(l2):
                        return 1.0
                    return (1.0 - _dl.SequenceMatcher(None, l1, l2).ratio()) * 0.5

                distance = nx.graph_edit_distance(
                    g1, g2,
                    node_subst_cost=_node_subst_cost,
                    edge_subst_cost=_edge_subst_cost,
                    timeout=15,
                )
                if distance is None:
                    results["ged"] = "GED: Timeout (graph too complex)"
                else:
                    def _type_counts(g):
                        counts: dict[str, int] = {}
                        for _, attrs in g.nodes(data=True):
                            t = attrs.get("node_type", "unknown")
                            counts[t] = counts.get(t, 0) + 1
                        return counts
                    n1, n2 = len(g1.nodes), len(g2.nodes)
                    results["ged"] = {
                        "distance":            float(distance),
                        "normalized_distance": round(float(distance) / (n1 + n2), 3) if (n1 + n2) > 0 else 0.0,
                        "node_count":          [n1, n2],
                        "edge_count":          [len(g1.edges), len(g2.edges)],
                        "node_types":          [_type_counts(g1), _type_counts(g2)],
                    }
            except Exception as e:
                click.echo(f"Warning: GED failed: {e}", err=True)
                results["ged"] = f"Error: {e}"

    # ── Structural Mode ──────────────────────────────────────────────────────
    if "structural" in active_modes:
        import re as _re_s

        def _extract_structure(text: str, ext: str) -> dict:
            if ext == ".md":
                headings = _re_s.findall(r'^(#{1,6})\s+(.+)$', text, _re_s.MULTILINE)
                return {"type": "markdown", "headings": [(len(h), t.strip()) for h, t in headings]}
            elif ext == ".py":
                import ast as _ast
                try:
                    tree = _ast.parse(text)
                    return {
                        "type":      "python",
                        "classes":   [n.name for n in _ast.walk(tree) if isinstance(n, _ast.ClassDef)],
                        "functions": [n.name for n in _ast.walk(tree) if isinstance(n, _ast.FunctionDef)],
                    }
                except SyntaxError as exc:
                    return {"type": "python", "error": str(exc)}
            elif ext in (".js", ".ts"):
                fns = _re_s.findall(
                    r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\()', text
                )
                return {
                    "type":      ext[1:],
                    "classes":   _re_s.findall(r'class\s+(\w+)', text),
                    "functions": [f[0] or f[1] for f in fns],
                }
            elif ext == ".spl":
                return {
                    "type":       "spl",
                    "workflows":  _re_s.findall(r'^\s*WORKFLOW\s+(\w+)',  text, _re_s.MULTILINE | _re_s.IGNORECASE),
                    "procedures": _re_s.findall(r'^\s*PROCEDURE\s+(\w+)', text, _re_s.MULTILINE | _re_s.IGNORECASE),
                }
            elif ext == ".mmd":
                node_classes = _re_s.findall(r'^\s+class\s+\w+\s+(\w+)\s*$', text, _re_s.MULTILINE)
                type_counts: dict[str, int] = {}
                for t in node_classes:
                    if t in ("llm", "ctrl", "term", "assign", "proc", "log"):
                        type_counts[t] = type_counts.get(t, 0) + 1
                return {
                    "type":       "mermaid",
                    "workflows":  _re_s.findall(r'subgraph\s+SG_\w+\["(?:WORKFLOW|PROCEDURE):\s+(\w+)"\]', text),
                    "node_types": type_counts,
                }
            else:
                lines = text.splitlines()
                return {"type": "text", "lines": len(lines), "chars": len(text)}

        s1 = _extract_structure(content1, ext1)
        s2 = _extract_structure(content2, ext2)
        results["structural"] = {"file1": s1, "file2": s2}

    # ── AST-Diff Mode ────────────────────────────────────────────────────────
    if "ast-diff" in active_modes:
        import re as _re_a

        def _ast_inventory(text: str, ext: str) -> dict:
            if ext == ".py":
                import ast as _ast
                try:
                    tree = _ast.parse(text)
                    return {
                        "classes":    [n.name for n in _ast.walk(tree) if isinstance(n, _ast.ClassDef)],
                        "functions":  [n.name for n in _ast.walk(tree) if isinstance(n, _ast.FunctionDef)],
                        "async_fns":  [n.name for n in _ast.walk(tree) if isinstance(n, _ast.AsyncFunctionDef)],
                    }
                except SyntaxError as exc:
                    return {"error": str(exc)}
            elif ext == ".spl":
                try:
                    from spl.lexer import Lexer as _Lex
                    from spl3.parser import SPL3Parser as _P3
                    from spl.ast_nodes import WorkflowStatement as _WS, ProcedureStatement as _PS
                    _tokens = _Lex(text).tokenize()
                    _tree   = _P3(_tokens).parse()
                    return {
                        "workflows":  [s.name for s in _tree.statements if isinstance(s, _WS)],
                        "procedures": [s.name for s in _tree.statements if isinstance(s, _PS)],
                        "generates":  _re_a.findall(r'\bGENERATE\s+(\w+)\s*\(', text, _re_a.IGNORECASE),
                        "calls":      _re_a.findall(r'\bCALL\s+(\w+)\s*\(',      text, _re_a.IGNORECASE),
                    }
                except Exception as exc:
                    return {"error": str(exc)}
            else:
                return {"note": f"ast-diff not supported for {ext}"}

        inv1 = _ast_inventory(content1, ext1)
        inv2 = _ast_inventory(content2, ext2)

        ast_diff_result: dict[str, dict] = {}
        for key in sorted((set(inv1) | set(inv2)) - {"error", "note"}):
            v1 = sorted(set(inv1.get(key, [])))
            v2 = sorted(set(inv2.get(key, [])))
            ast_diff_result[key] = {
                "common":  sorted(set(v1) & set(v2)),
                "removed": sorted(set(v1) - set(v2)),
                "added":   sorted(set(v2) - set(v1)),
            }
        results["ast-diff"] = ast_diff_result

    # ── Vision Mode ──────────────────────────────────────────────────────────
    if "vision" in active_modes:
        _IMG_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
        if ext1 not in _IMG_EXTS or ext2 not in _IMG_EXTS:
            click.echo("Warning: vision mode expects image files. Skipping.", err=True)
            results["vision"] = "Skipped: non-image files."
        else:
            click.echo("Performing vision comparison...")
            vision_result: dict = {}
            try:
                from PIL import Image as _PIL_Image
                import numpy as _np
                im1 = _PIL_Image.open(path1)
                im2 = _PIL_Image.open(path2)
                vision_result["metadata"] = {
                    "file1": {"size": list(im1.size), "mode": im1.mode},
                    "file2": {"size": list(im2.size), "mode": im2.mode},
                }
                if im1.size == im2.size:
                    arr1 = _np.array(im1.convert("RGB")).astype(float)
                    arr2 = _np.array(im2.convert("RGB")).astype(float)
                    diff = _np.abs(arr1 - arr2)
                    vision_result["pixel_diff"] = {
                        "mean_delta":          round(float(diff.mean()), 3),
                        "max_delta":           round(float(diff.max()), 1),
                        "changed_pixels_pct":  round(float((diff.sum(axis=2) > 10).mean() * 100), 2),
                    }
                    # Histogram cosine similarity (cheap semantic proxy)
                    def _hist(arr):
                        import numpy as _np2
                        h = _np2.histogram(arr.ravel(), bins=64, range=(0, 256))[0].astype(float)
                        n = _np2.linalg.norm(h)
                        return h / n if n > 0 else h
                    import numpy as _np2
                    sim = float(_np2.dot(_hist(arr1), _hist(arr2)))
                    vision_result["histogram_similarity"] = round(sim, 4)
            except ImportError:
                vision_result["note"] = "Install Pillow for pixel-level comparison: pip install Pillow"
            except Exception as exc:
                vision_result["error"] = str(exc)

            # Try LLM vision if adapter available
            if adapter:
                try:
                    import base64 as _b64
                    _MIME = {".png": "image/png", ".jpg": "image/jpeg",
                             ".jpeg": "image/jpeg", ".webp": "image/webp"}
                    _img1_b64 = _b64.standard_b64encode(path1.read_bytes()).decode()
                    _img2_b64 = _b64.standard_b64encode(path2.read_bytes()).decode()
                    _vision_prompt = (
                        f"Compare these two diagrams: '{path1.name}' (Image 1) vs '{path2.name}' (Image 2).\n\n"
                        "Analyze: (1) structural elements present in one but absent in the other, "
                        "(2) flow/control differences — loops, branches, exception handlers, "
                        "(3) label/operation differences — function names, variable names, conditions, "
                        "(4) overall verdict: EQUIVALENT, REFACTORED, DEGRADED, or DIVERGED.\n\n"
                        "Focus on logical/semantic differences, not visual styling."
                    )
                    from spl3.adapters import get_adapter as _ga
                    _llm_v = _ga(adapter, **({"model": model} if model else {}))
                    if hasattr(_llm_v, "generate_vision"):
                        _mime1 = _MIME.get(ext1, "image/png")
                        _mime2 = _MIME.get(ext2, "image/png")
                        _raw_v = asyncio.run(_llm_v.generate_vision(
                            _vision_prompt,
                            images=[(_img1_b64, _mime1), (_img2_b64, _mime2)],
                        ))
                        vision_result["llm_analysis"] = (
                            _raw_v if isinstance(_raw_v, str)
                            else getattr(_raw_v, "content", str(_raw_v))
                        )
                except Exception:
                    pass  # vision LLM is best-effort

            results["vision"] = vision_result

    # ── LLM Fallback for failed/unavailable modes ────────────────────────────
    # When a mode-specific tier fails (missing dep, wrong file type, etc.) and
    # an LLM adapter is available, run a targeted LLM analysis covering those
    # aspects rather than silently leaving them blank.
    _FALLBACK_ASPECTS = {
        "ged":        "topological graph structure — nodes, edges, and control-flow paths",
        "vector":     "semantic similarity and embedding-space proximity",
        "bert-score": "token-level semantic overlap and textual similarity",
        "vision":     "visual layout and structural differences",
        "structural": "document/code skeleton — sections, function names, workflow names",
        "ast-diff":   "syntactic AST-level differences — renamed/added/removed constructs",
    }
    _failed = [
        m for m in active_modes
        if m in _FALLBACK_ASPECTS
        and isinstance(results.get(m), str)
        and (results[m].startswith("Error:") or results[m].startswith("Skipped:"))
    ]
    if _failed and adapter and "llm" not in active_modes:
        _aspects = "; ".join(_FALLBACK_ASPECTS[m] for m in _failed)
        _fb_prompt = (
            f"The following comparison tiers were unavailable: {_failed}.\n\n"
            f"As a fallback, compare these two {ext1} files focusing on: {_aspects}.\n\n"
            f"File 1 ({path1.name}):\n{content1[:3000]}"
            f"{'...(truncated)' if len(content1) > 3000 else ''}\n\n"
            f"File 2 ({path2.name}):\n{content2[:3000]}"
            f"{'...(truncated)' if len(content2) > 3000 else ''}\n\n"
            "Provide a structured analysis covering what each failed tier would have measured."
        )
        try:
            from spl3.adapters import get_adapter as _ga_fb
            click.echo(f"Running LLM fallback for {_failed}...")
            _llm_fb = _ga_fb(adapter, **({"model": model} if model else {}))
            _raw_fb = asyncio.run(_llm_fb.generate(_fb_prompt))
            results["llm_fallback"] = {
                "covers_failed": _failed,
                "analysis": (_raw_fb if isinstance(_raw_fb, str)
                             else getattr(_raw_fb, "content", str(_raw_fb))),
            }
        except Exception:
            pass  # best-effort

    # ── Synthesis ────────────────────────────────────────────────────────────
    # Integrate all tier results into a single verdict via LLM reasoning.
    # Runs when synthesize=True and at least one tier produced a result.
    if synthesize and results and _adapter_synthesis:
        _TIER_LABELS = {
            "ged":        "Tier 1 – Topological (GED)",
            "llm":        "Tier 2 – Semantic (LLM)",
            "vision":     "Tier 2 – Semantic (Vision)",
            "ast-diff":   "Tier 3 – Syntactic (AST-diff)",
            "structural": "Tier 4 – Structural",
            "git-diff":   "Tier 5 – Character-level (git-diff)",
            "vector":     "Tier 6 – Embedding (vector cosine)",
            "bert-score": "Tier 6 – Embedding (BERTScore)",
        }

        def _tier_summary(results: dict, active_modes: list) -> str:
            parts = []
            for mode in active_modes:
                r = results.get(mode)
                if r is None:
                    continue
                label = _TIER_LABELS.get(mode, mode)
                if mode == "ged" and isinstance(r, dict):
                    nt = r.get("node_types", [{}, {}])
                    parts.append(
                        f"{label}: distance={r['distance']:.1f}, "
                        f"nodes={r['node_count'][0]}→{r['node_count'][1]}, "
                        f"edges={r['edge_count'][0]}→{r['edge_count'][1]}, "
                        f"node_types: {nt[0]} → {nt[1]}"
                    )
                elif mode == "vector" and isinstance(r, float):
                    parts.append(f"{label}: cosine_similarity={r:.4f}")
                elif mode == "bert-score" and isinstance(r, dict):
                    parts.append(f"{label}: F1={r['f1']:.4f}, precision={r['precision']:.4f}, recall={r['recall']:.4f}")
                elif mode == "structural" and isinstance(r, dict):
                    parts.append(f"{label}: file1={r.get('file1')}, file2={r.get('file2')}")
                elif mode == "ast-diff" and isinstance(r, dict):
                    diffs = []
                    for key, d in r.items():
                        if isinstance(d, dict):
                            if d.get("removed"):
                                diffs.append(f"{key} removed={d['removed']}")
                            if d.get("added"):
                                diffs.append(f"{key} added={d['added']}")
                    parts.append(f"{label}: {'; '.join(diffs) or 'no differences'}")
                elif mode == "git-diff" and isinstance(r, str):
                    plus  = sum(1 for l in r.splitlines() if l.startswith('+') and not l.startswith('+++'))
                    minus = sum(1 for l in r.splitlines() if l.startswith('-') and not l.startswith('---'))
                    parts.append(f"{label}: +{plus} lines, -{minus} lines")
                elif mode in ("llm", "vision") and isinstance(r, (str, dict)):
                    excerpt = str(r)[:400].replace('\n', ' ')
                    parts.append(f"{label}: {excerpt}...")
                else:
                    parts.append(f"{label}: {str(r)[:200]}")
            return "\n".join(parts)

        synthesis_prompt = f"""You are the synthesis layer of a multi-tier comparison system.
Your task is NOT to summarize each tier independently — it is to reason ACROSS tiers:
what do agreements reveal? what do contradictions expose?

Files compared: "{path1.name}"  vs  "{path2.name}"  (type: {ext1})

Tier measurements:
{_tier_summary(results, active_modes)}

Cross-tier interpretation guide:
- GED low + semantic similar  → topologically and logically equivalent
- GED high + semantic similar → same vocabulary, restructured control flow (refactor)
- GED low + semantic diverges → structural copy but intent changed
- Character diff large + AST diff small → style/rename refactor, logic unchanged
- Embedding high + GED high  → familiar words, divergent structure — possible regression
- Any tier shows node loss (node_count drops, ast-diff removes items) → DEGRADED

Verdict options (choose exactly one):
  EQUIVALENT  — functionally and semantically the same (surface noise allowed)
  REFACTORED  — structure/intent preserved, presentation changed
  DEGRADED    — one file is a lossy version of the other (information lost)
  DIVERGED    — genuinely different intent, logic, or purpose

Respond with JSON only — no prose before or after:
{{
  "verdict":           "EQUIVALENT|REFACTORED|DEGRADED|DIVERGED",
  "confidence":        "HIGH|MEDIUM|LOW",
  "key_finding":       "single sentence — the most important insight from across tiers",
  "cross_tier_insight":"what the agreement or contradiction between tiers reveals that no single tier could",
  "recommendation":    "concrete next step (or 'none needed' if EQUIVALENT)"
}}"""

        try:
            from spl3.adapters import get_adapter as _ga_s
            _llm_s = _ga_s(_adapter_synthesis, **({"model": model} if model else {}))
            click.echo(f"Synthesizing tier results via {_adapter_synthesis}...")
            _raw_s = asyncio.run(_llm_s.generate(synthesis_prompt))
            _syn_text = _raw_s if isinstance(_raw_s, str) else getattr(_raw_s, "content", str(_raw_s))
            # Extract JSON from response
            import re as _re_syn
            _json_m = _re_syn.search(r'\{[^{}]*\}', _syn_text, _re_syn.DOTALL)
            if _json_m:
                import json as _json_s
                results["synthesis"] = _json_s.loads(_json_m.group())
            else:
                results["synthesis"] = {"raw": _syn_text}
        except Exception as exc:
            results["synthesis"] = {"error": str(exc)}

    elif synthesize and results and not _adapter_synthesis:
        # Rule-based verdict when no LLM is available — uses GED thresholds
        _syn_rule: dict = {}
        if "ged" in results and isinstance(results["ged"], dict):
            nd = results["ged"].get("normalized_distance", 1.0)
            _syn_rule = {
                "verdict":     "EQUIVALENT"  if nd == 0.0
                          else "REFACTORED"  if nd < 0.10
                          else "DEGRADED"    if nd < 0.35
                          else "DIVERGED",
                "confidence":  "MEDIUM",
                "key_finding": (
                    f"Rule-based from GED: normalized distance = {nd:.3f} "
                    f"(0 → EQUIVALENT, < 0.10 → REFACTORED, < 0.35 → DEGRADED, else DIVERGED)"
                ),
                "cross_tier_insight": "Single-tier rule-based — add --adapter for LLM synthesis.",
                "recommendation":     "Add --adapter for richer multi-tier synthesis verdict.",
            }
        if _syn_rule:
            results["synthesis"] = _syn_rule

    # ── Format Output ────────────────────────────────────────────────────────
    if output_format == "json":
        json_output = {
            "files": {
                "file1": {"name": path1.name, "type": ext1},
                "file2": {"name": path2.name, "type": ext2}
            },
            "results": results,
            "metadata": {
                "adapter":           adapter,
                "model":             model or "default",
                "adapter_embed":     _adapter_embed,
                "adapter_synthesis": _adapter_synthesis,
                "model_embed":       model_embed or "default",
                "focus": focus,
                "timestamp": datetime.now().isoformat(),
                "active_modes": active_modes
            }
        }
        output_content = _json.dumps(json_output, indent=2)

    elif output_format == "text":
        output_parts = [f"Comparison: {path1.name}  ↔  {path2.name}"]
        if "synthesis" in results and isinstance(results["synthesis"], dict):
            syn = results["synthesis"]
            output_parts.append(f"\nVERDICT: {syn.get('verdict','?')} ({syn.get('confidence','?')})")
            output_parts.append(f"  {syn.get('key_finding','')}")
        for mode in active_modes:
            output_parts.append(f"\n--- {mode.upper()} ---")
            output_parts.append(str(results.get(mode, "N/A")))
        output_content = "\n".join(output_parts)

    elif output_format in ("markdown", None):  # markdown (default)
        # ── Synthesis verdict banner (always first) ──────────────────────────
        syn_section = ""
        if "synthesis" in results:
            syn = results["synthesis"]
            if isinstance(syn, dict) and "verdict" in syn:
                _VERDICT_ICON = {
                    "EQUIVALENT": "✅", "REFACTORED": "🔄",
                    "DEGRADED": "⚠️",  "DIVERGED": "❌",
                }
                icon = _VERDICT_ICON.get(syn["verdict"], "🔍")
                syn_section = (
                    f"\n## Synthesis Verdict: {icon} {syn['verdict']} "
                    f"({syn.get('confidence','?')} confidence)\n\n"
                    f"> **Key finding:** {syn.get('key_finding', '')}\n>\n"
                    f"> **Cross-tier insight:** {syn.get('cross_tier_insight', '')}\n>\n"
                    f"> **Recommendation:** {syn.get('recommendation', '')}\n\n---\n"
                )
            else:
                syn_section = f"\n## Synthesis\n\n{syn}\n\n---\n"

        header = (
            f"# Comparison: `{path1.name}`  ↔  `{path2.name}`\n\n"
            f"- **File 1:** `{path1.name}` ({ext1})\n"
            f"- **File 2:** `{path2.name}` ({ext2})\n"
            f"- **Tiers:** {', '.join(active_modes)}\n"
            f"- **Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"{syn_section}"
        )

        body_parts = []

        if "ged" in results:
            res = results["ged"]
            if isinstance(res, dict):
                nt = res.get("node_types", [{}, {}])
                _nt_fmt = lambda d: "  ".join(f"{k}×{v}" for k, v in sorted(d.items()))
                body_parts.append(
                    f"## Tier 1 – Topological (GED)\n\n"
                    f"| Metric | File 1 | File 2 |\n|---|---|---|\n"
                    f"| Nodes | {res['node_count'][0]} | {res['node_count'][1]} |\n"
                    f"| Edges | {res['edge_count'][0]} | {res['edge_count'][1]} |\n"
                    f"| Node types | {_nt_fmt(nt[0])} | {_nt_fmt(nt[1])} |\n\n"
                    f"**Graph Edit Distance: {res['distance']:.1f}** "
                    f"*(SPL-node-aware cost; lower = more similar)*"
                )
            else:
                body_parts.append(f"## Tier 1 – Topological (GED)\n\n{res}")

        if "llm" in results:
            body_parts.append(
                f"## Tier 2 – Semantic (LLM)\n\n"
                f"*Adapter: {adapter}  |  Model: {model or 'default'}*\n\n"
                f"{results['llm']}"
            )

        if "vision" in results:
            res = results["vision"]
            if isinstance(res, dict):
                meta = res.get("metadata", {})
                pdiff = res.get("pixel_diff", {})
                hist_sim = res.get("histogram_similarity")
                llm_a = res.get("llm_analysis", "")
                lines = ["## Tier 2 – Semantic (Vision)\n"]
                if meta:
                    lines.append(
                        f"| | File 1 | File 2 |\n|---|---|---|\n"
                        f"| Size | {meta.get('file1',{}).get('size')} | {meta.get('file2',{}).get('size')} |\n"
                        f"| Mode | {meta.get('file1',{}).get('mode')} | {meta.get('file2',{}).get('mode')} |"
                    )
                if pdiff:
                    lines.append(
                        f"\n**Pixel diff:** mean Δ={pdiff.get('mean_delta')}  "
                        f"max Δ={pdiff.get('max_delta')}  "
                        f"changed pixels={pdiff.get('changed_pixels_pct')}%"
                    )
                if hist_sim is not None:
                    lines.append(f"\n**Histogram similarity:** {hist_sim:.4f}")
                if llm_a:
                    lines.append(f"\n**LLM vision analysis:**\n\n{llm_a}")
                body_parts.append("\n".join(lines))
            else:
                body_parts.append(f"## Tier 2 – Semantic (Vision)\n\n{res}")

        if "ast-diff" in results:
            res = results["ast-diff"]
            if isinstance(res, dict):
                lines = ["## Tier 3 – Syntactic (AST-diff)\n"]
                for key, d in res.items():
                    if not isinstance(d, dict):
                        continue
                    common  = d.get("common",  [])
                    removed = d.get("removed", [])
                    added   = d.get("added",   [])
                    status = "✓" if not removed and not added else "✗"
                    lines.append(f"**{key}** {status}")
                    if common:
                        lines.append(f"  - common: {', '.join(f'`{x}`' for x in common)}")
                    if removed:
                        lines.append(f"  - removed (file1 only): {', '.join(f'`{x}`' for x in removed)}")
                    if added:
                        lines.append(f"  - added (file2 only): {', '.join(f'`{x}`' for x in added)}")
                body_parts.append("\n".join(lines))
            else:
                body_parts.append(f"## Tier 3 – Syntactic (AST-diff)\n\n{res}")

        if "structural" in results:
            res = results["structural"]
            if isinstance(res, dict):
                s1 = res.get("file1", {})
                s2 = res.get("file2", {})
                lines = [f"## Tier 4 – Structural\n\n| | File 1 | File 2 |\n|---|---|---|"]
                for key in sorted(set(s1) | set(s2)):
                    if key == "type":
                        continue
                    v1 = s1.get(key, "—")
                    v2 = s2.get(key, "—")
                    lines.append(f"| {key} | {v1} | {v2} |")
                body_parts.append("\n".join(lines))
            else:
                body_parts.append(f"## Tier 4 – Structural\n\n{res}")

        if "git-diff" in results:
            body_parts.append(
                f"## Tier 5 – Character-level (git-diff)\n\n"
                f"```diff\n{results['git-diff']}\n```"
            )

        if "vector" in results:
            sim = results["vector"]
            body_parts.append(
                f"## Tier 6 – Embedding (Vector)\n\n"
                f"Cosine similarity: **{sim:.4f}**" if isinstance(sim, float)
                else f"## Tier 6 – Embedding (Vector)\n\n{sim}"
            )

        if "bert-score" in results:
            res = results["bert-score"]
            if isinstance(res, dict):
                body_parts.append(
                    f"## Tier 6 – Embedding (BERTScore)\n\n"
                    f"- Precision: {res['precision']:.4f}\n"
                    f"- Recall: {res['recall']:.4f}\n"
                    f"- **F1: {res['f1']:.4f}**"
                )
            else:
                body_parts.append(f"## Tier 6 – Embedding (BERTScore)\n\n{res}")

        if "llm_fallback" in results:
            fb = results["llm_fallback"]
            body_parts.append(
                f"## LLM Fallback\n\n"
                f"*Covering failed tiers: {fb.get('covers_failed', [])}*\n\n"
                f"{fb.get('analysis', '')}"
            )

        footer = "\n---\n\n*Generated by `spl3 compare` — multi-tier diff*"
        output_content = header + "\n---\n\n".join(body_parts) + footer

    elif output_format == "html":
        import html as _html
        import base64 as _b64

        _IMG_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
        _MIME_MAP  = {".png": "image/png", ".jpg": "image/jpeg",
                      ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}

        def _panel_content(path: "Path", content: str, ext: str) -> str:
            if ext == ".mmd":
                return f'<div class="mermaid">\n{_html.escape(content)}\n</div>'
            elif ext in _IMG_EXTS:
                try:
                    _mime = _MIME_MAP.get(ext, "image/png")
                    _data = _b64.standard_b64encode(path.read_bytes()).decode()
                    return f'<img src="data:{_mime};base64,{_data}" style="max-width:100%;max-height:100%">'
                except Exception:
                    return f'<pre>{_html.escape(content[:2000])}</pre>'
            else:
                return f'<pre>{_html.escape(content)}</pre>'

        def _synthesis_html(syn: dict) -> str:
            if not isinstance(syn, dict) or "verdict" not in syn:
                return f'<p>{_html.escape(str(syn))}</p>'
            _V_ICON = {"EQUIVALENT": "✅", "REFACTORED": "🔄",
                       "DEGRADED": "⚠️", "DIVERGED": "❌"}
            icon  = _V_ICON.get(syn["verdict"], "🔍")
            v     = _html.escape(syn.get("verdict", "?"))
            conf  = _html.escape(syn.get("confidence", "?"))
            kf    = _html.escape(syn.get("key_finding", ""))
            cti   = _html.escape(syn.get("cross_tier_insight", ""))
            rec   = _html.escape(syn.get("recommendation", ""))
            return (
                f'<div class="verdict {syn.get("verdict","")}">'
                f'<div><h2>{icon} {v} <small>({conf} confidence)</small></h2>'
                f'<p><strong>Key finding:</strong> {kf}</p>'
                f'<p><strong>Cross-tier insight:</strong> {cti}</p>'
                f'<p><strong>Recommendation:</strong> {rec}</p></div>'
                f'</div>'
            )

        def _tiers_html(results: dict, active_modes: list) -> str:
            _TIER_TITLES = {
                "ged":        "Tier 1 – Topological (GED)",
                "llm":        "Tier 2 – Semantic (LLM)",
                "vision":     "Tier 2 – Semantic (Vision)",
                "ast-diff":   "Tier 3 – Syntactic (AST-diff)",
                "structural": "Tier 4 – Structural",
                "git-diff":   "Tier 5 – Character-level (git-diff)",
                "vector":     "Tier 6 – Embedding (vector)",
                "bert-score": "Tier 6 – Embedding (BERTScore)",
                "llm_fallback": "LLM Fallback",
            }
            parts = []
            for mode in list(active_modes) + (["llm_fallback"] if "llm_fallback" in results else []):
                r = results.get(mode)
                if r is None:
                    continue
                title = _TIER_TITLES.get(mode, mode)
                if mode == "ged" and isinstance(r, dict):
                    nt = r.get("node_types", [{}, {}])
                    _nt = lambda d: ", ".join(f"{k}×{v}" for k, v in sorted(d.items()))
                    body = (
                        f"<table><tr><th></th><th>File 1</th><th>File 2</th></tr>"
                        f"<tr><td>Nodes</td><td>{r['node_count'][0]}</td><td>{r['node_count'][1]}</td></tr>"
                        f"<tr><td>Edges</td><td>{r['edge_count'][0]}</td><td>{r['edge_count'][1]}</td></tr>"
                        f"<tr><td>Node types</td><td>{_nt(nt[0])}</td><td>{_nt(nt[1])}</td></tr>"
                        f"<tr><td>Normalized distance</td><td colspan='2'><strong>{r.get('normalized_distance','?')}</strong>"
                        f" (raw: {r['distance']:.1f})</td></tr>"
                        f"</table>"
                    )
                elif mode == "git-diff" and isinstance(r, str):
                    body = f"<pre class='diff'>{_html.escape(r)}</pre>"
                elif mode == "ast-diff" and isinstance(r, dict):
                    rows = []
                    for key, d in r.items():
                        if not isinstance(d, dict):
                            continue
                        status = "✓" if not d.get("removed") and not d.get("added") else "✗"
                        rows.append(f"<tr><td>{key}</td><td>{status}</td>"
                                    f"<td>{', '.join(d.get('removed',[]))}</td>"
                                    f"<td>{', '.join(d.get('added',[]))}</td></tr>")
                    body = (
                        "<table><tr><th>Key</th><th></th><th>Removed</th><th>Added</th></tr>"
                        + "".join(rows) + "</table>"
                    ) if rows else "<p>No differences</p>"
                elif mode == "llm_fallback" and isinstance(r, dict):
                    body = (
                        f"<p><em>Covers failed tiers: {r.get('covers_failed', [])}</em></p>"
                        f"<p>{_html.escape(r.get('analysis',''))}</p>"
                    )
                else:
                    body = f"<p>{_html.escape(str(r)[:1000])}</p>"
                parts.append(
                    f'<details class="tier" open>'
                    f'<summary>{title}</summary>'
                    f'<div class="tier-content">{body}</div>'
                    f'</details>'
                )
            return "\n".join(parts)

        syn = results.get("synthesis", {})
        from datetime import datetime as _dt
        output_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Compare: {_html.escape(path1.name)} ↔ {_html.escape(path2.name)}</title>
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
    pre.diff .add{{color:#1a7f37}} pre.diff .del{{color:#cf222e}}
    .verdict{{padding:12px 16px;border-radius:var(--radius);margin-bottom:12px;border-left:4px solid}}
    .verdict h2{{margin:0;font-size:16px}} .verdict p{{margin:3px 0 0;font-size:13px;opacity:.85}}
    .EQUIVALENT{{background:#dafbe1;color:#1a7f37;border-color:#2da44e}}
    .REFACTORED{{background:#ddf4ff;color:#0550ae;border-color:#0969da}}
    .DEGRADED  {{background:#fff8c5;color:#9a6700;border-color:#bf8700}}
    .DIVERGED  {{background:#ffebe9;color:#cf222e;border-color:#cf222e}}
    .tier{{border:1px solid var(--border);border-radius:var(--radius);margin-bottom:8px;overflow:hidden}}
    .tier summary{{padding:8px 12px;font-weight:600;cursor:pointer;background:#f6f8fa;list-style:none;display:flex;align-items:center;gap:6px}}
    .tier summary:hover{{background:#eaeef2}}
    .tier-content{{padding:12px}}
    table{{border-collapse:collapse;width:100%}} th,td{{border:1px solid var(--border);padding:5px 9px;text-align:left;font-size:13px}} th{{background:#f6f8fa;font-weight:600}}
    .meta{{font-size:11px;color:#57606a;margin-bottom:10px}}
  </style>
</head>
<body>
  <div class="top-row">
    <div class="panel">
      <h3>📄 {_html.escape(path1.name)}</h3>
      <div class="panel-inner">{_panel_content(path1, content1, ext1)}</div>
    </div>
    <div class="panel">
      <h3>📄 {_html.escape(path2.name)}</h3>
      <div class="panel-inner">{_panel_content(path2, content2, ext2)}</div>
    </div>
  </div>
  <div class="bottom-row">
    <p class="meta">Tiers: {', '.join(active_modes)} &nbsp;|&nbsp; {_dt.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    {_synthesis_html(syn)}
    {_tiers_html(results, active_modes)}
  </div>
  <script>mermaid.initialize({{startOnLoad:true,theme:'default',securityLevel:'loose'}});</script>
</body>
</html>"""

    # Output results
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_content, encoding="utf-8")
        click.echo(f"Comparison report written to: {output_path}")
    else:
        click.echo(output_content)


def _parse_mermaid_to_nx(mermaid_content: str):
    """Parse Mermaid flowchart into a NetworkX DiGraph with SPL-aware node types.

    Reads the ``class <id> <type>`` annotations emitted by spl2mmd to attach
    the SPL node type (llm, ctrl, term, assign, proc, log) as a node attribute,
    enabling type-aware GED substitution costs.
    """
    import re as _re
    import networkx as nx

    g = nx.DiGraph()

    # ── Pass 1: extract node labels from all Mermaid shape syntaxes ─────────
    # Parallelogram: GEN3[/"label"/]  or  SUB5[/"label"/]
    for m in _re.finditer(r'^\s+(\w+)\[/"(.*?)"/\]', mermaid_content, _re.MULTILINE):
        g.add_node(m.group(1), label=m.group(2), node_type="unknown")

    # Diamond: WHILE4{"label"}  EVAL6{"label"}  EXC13{"label"}
    for m in _re.finditer(r'^\s+(\w+)\{"(.*?)"\}', mermaid_content, _re.MULTILINE):
        g.add_node(m.group(1), label=m.group(2), node_type="unknown")

    # Stadium/rounded terminal: START1(["label"])  RET8(["label"])
    for m in _re.finditer(r'^\s+(\w+)\(\["(.*?)"\]\)', mermaid_content, _re.MULTILINE):
        g.add_node(m.group(1), label=m.group(2), node_type="unknown")

    # Rectangle: A2["label"]  (assign, merge placeholders)
    for m in _re.finditer(r'^\s+(\w+)\["(.*?)"\]', mermaid_content, _re.MULTILINE):
        if m.group(1) not in g:
            g.add_node(m.group(1), label=m.group(2), node_type="unknown")

    # ── Pass 2: apply SPL node types from `class <id> <type>` annotations ───
    _SPL_TYPES = {"llm", "ctrl", "term", "assign", "proc", "log"}
    for m in _re.finditer(r'^\s+class\s+(\w+)\s+(\w+)\s*$', mermaid_content, _re.MULTILINE):
        node_id, css_class = m.group(1), m.group(2)
        if css_class in _SPL_TYPES and node_id in g:
            g.nodes[node_id]["node_type"] = css_class

    # ── Pass 3: edges  A --> B  or  A -->|label| B  or  A -.-> B ───────────
    for m in _re.finditer(
        r'(\w+)\s*(?:-->|-\.->)\s*(?:\|([^|]*)\|\s*)?(\w+)',
        mermaid_content
    ):
        src, edge_label, dst = m.group(1), m.group(2), m.group(3)
        if src in g and dst in g:
            g.add_edge(src, dst, label=edge_label or "")

    return g


# ------------------------------------------------------------------ #
# spl3 show                                                           #
# ------------------------------------------------------------------ #

@main.command("show")
@click.option("--adapter", is_flag=False, flag_value="__list_all__", default=None,
              help="List all adapters (no value) or specify adapter name")
@click.option("--model", is_flag=True, default=False,
              help="List available models (requires --adapter <name>)")
@click.option("--tool", is_flag=False, flag_value="__list_all__", default=None,
              metavar="NAME",
              help="List all stdlib tools (no value) or show detail for a specific tool")
def cmd_show(adapter, model, tool):
    """List available adapters, models, and stdlib tools.

    \b
    Examples:
      spl3 show --adapter                     # List all available adapters
      spl3 show --adapter ollama --model      # List models for ollama adapter
      spl3 show --adapter claude_cli --model  # List models for claude_cli adapter
      spl3 show --tool                        # List all stdlib tools
      spl3 show --tool web_search             # Show detail for a specific tool
    """
    from spl3.adapters import list_adapters, get_adapter

    # Case 1: --adapter used as flag (list all adapters)
    if adapter == "__list_all__":
        if model:
            raise click.ClickException("Cannot use --model when listing all adapters")

        adapter_list = list_adapters()
        if not adapter_list:
            click.echo("No adapters available")
            return

        click.echo("Available adapters:")
        for adapter_name in adapter_list:
            click.echo(f"  {adapter_name}")

        click.echo(f"\nTotal: {len(adapter_list)} adapter(s)")
        click.echo("Use 'spl3 show --adapter <name> --model' to list models for a specific adapter")
        return

    # Case 2: --adapter has value and --model is used
    if adapter and adapter != "__list_all__" and model:
        adapter_list = list_adapters()
        if adapter not in adapter_list:
            available = ", ".join(sorted(adapter_list)) if adapter_list else "(none)"
            raise click.ClickException(f"Unknown adapter '{adapter}'. Available: {available}")

        try:
            adapter_instance = get_adapter(adapter)
            model_list = sorted(adapter_instance.list_models())

            if not model_list:
                click.echo(f"No models available for adapter '{adapter}'")
                return

            click.echo(f"Available models for '{adapter}':")
            for model_name in model_list:
                click.echo(f"  {model_name}")

            click.echo(f"\nTotal: {len(model_list)} model(s)")

        except Exception as e:
            raise click.ClickException(f"Failed to list models for adapter '{adapter}': {e}")
        return

    # Case 3: Invalid combinations
    if model and not adapter:
        raise click.ClickException("--model flag requires --adapter <name> to specify which adapter to query")

    if adapter and not model:
        raise click.ClickException(f"Use --model to list models for adapter '{adapter}', or use --adapter alone to list all adapters")

    # Case: --tool
    if tool is not None:
        from spl.tools import get_global_tools

        # Category order and membership — matches stdlib.py section comments
        _CATEGORIES = [
            ("Type conversion",   ["to_int", "to_float", "to_text", "to_bool"]),
            ("String",            ["upper", "lower", "trim", "ltrim", "rtrim", "length",
                                   "len_val", "substr", "replace", "concat", "instr",
                                   "lpad", "rpad", "split_part", "reverse"]),
            ("Pattern matching",  ["like", "startswith", "endswith", "contains", "regexp_match"]),
            ("Numeric",           ["abs_val", "round_val", "ceil_val", "floor_val",
                                   "mod_val", "power_val", "sqrt_val", "sign_val", "clamp"]),
            ("Conditional",       ["coalesce", "nullif", "iif"]),
            ("Null / empty",      ["isnull", "nvl", "isblank"]),
            ("Text aggregates",   ["word_count", "char_count", "line_count"]),
            ("JSON",              ["json_get", "json_set", "json_keys", "json_pretty",
                                   "json_length"]),
            ("Date / time",       ["now_iso", "date_format_val", "date_diff_days"]),
            ("Hashing",           ["md5_hash", "sha256_hash"]),
            ("List / array",      ["list_get", "list_length", "list_join", "list_contains",
                                   "trim_turns"]),
            ("File I/O",          ["write_file", "read_file", "file_exists", "make_dir",
                                   "path_join"]),
            ("Agentic / Network", ["web_search", "http_get", "run_python"]),
        ]

        all_tools = get_global_tools()

        if tool == "__list_all__":
            # Assign each tool to its category; uncategorised tools go last
            categorised = {name for names in _CATEGORIES for name in names[1]}
            uncategorised = sorted(k for k in all_tools if k not in categorised)

            total = 0
            for cat_name, cat_tools in _CATEGORIES:
                present = [t for t in cat_tools if t in all_tools]
                if not present:
                    continue
                click.echo(f"\n{cat_name}:")
                for name in present:
                    fn = all_tools[name]
                    doc = (fn.__doc__ or "").strip().splitlines()[0]
                    click.echo(f"  {name:<22}  {doc}")
                    total += 1

            if uncategorised:
                click.echo("\nOther:")
                for name in uncategorised:
                    fn = all_tools[name]
                    doc = (fn.__doc__ or "").strip().splitlines()[0]
                    click.echo(f"  {name:<22}  {doc}")
                    total += 1

            click.echo(f"\nTotal: {total} tool(s)  — use 'spl3 show --tool <name>' for detail")
            return

        # --tool <name>: show full docstring
        if tool not in all_tools:
            available = ", ".join(sorted(all_tools))
            raise click.ClickException(
                f"Unknown tool '{tool}'.\nAvailable: {available}"
            )
        fn = all_tools[tool]
        click.echo(f"Tool: {tool}")
        click.echo(f"{'─' * (len(tool) + 6)}")
        click.echo(fn.__doc__ or "(no docstring)")
        return

    # Case 4: No options provided
    raise click.ClickException(
        "Use --adapter to list adapters, --adapter <name> --model to list models, "
        "or --tool to list stdlib tools"
    )


# ------------------------------------------------------------------ #
# spl3 splc                                                           #
# ------------------------------------------------------------------ #

from spl3.splc.cli import splc as _splc_command
main.add_command(_splc_command, name="splc")


if __name__ == "__main__":
    main()
