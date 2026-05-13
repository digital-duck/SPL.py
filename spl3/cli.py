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
    """LLM-executed end-to-end test against .test.yaml fixtures.

    Distinct from 'spl3 validate' (syntax only, no LLM). This command
    actually runs the workflow and asserts on the LLM output.

    \b
    Looks for test fixtures alongside .spl files:
      generate_code.spl          — workflow under test
      generate_code.test.yaml    — test cases (inputs + expected assertions)

    \b
    Test YAML format:
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
    from spl3.text2spl import Text2SPL
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
# Mermaid rendering helpers (shared by text2mmd and compare)          #
# ------------------------------------------------------------------ #

def _mmd_single_html(mmd_text: str, title: str, *, png_name: str | None = None) -> str:
    """Standalone HTML page for one Mermaid diagram.

    If png_name is provided the HTML embeds a static <img> tag (no CDN JS
    required, no browser-side Mermaid parse errors).  Falls back to inline
    Mermaid rendering only when png_name is None.
    """
    if png_name:
        diagram_block = (
            f'<div class="diagram"><img src="{png_name}" '
            f'alt="{title} diagram" style="max-width:100%;height:auto;'
            f'border:1px solid #eee;border-radius:4px"></div>'
        )
        script_block = ""
        mermaid_script = ""
    else:
        diagram_block = f'<div class="mermaid">{mmd_text}</div>'
        script_block = (
            '<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>'
        )
        mermaid_script = (
            "<script>mermaid.initialize({"
            "startOnLoad:true,theme:'default',securityLevel:'loose',errorLevel:'warn'"
            "});</script>"
        )

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  {script_block}
  <style>
    body{{font-family:Arial,sans-serif;margin:20px;background:#f5f5f5}}
    .container{{max-width:1400px;margin:0 auto;background:white;padding:20px;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,.1)}}
    .diagram,.mermaid{{text-align:center;margin:20px 0}}
    pre{{background:#f8f9fa;border:1px solid #e9ecef;border-radius:4px;padding:15px;font-family:monospace;white-space:pre-wrap}}
  </style>
</head>
<body>
  <div class="container">
    <h2>{title}</h2>
    {diagram_block}
    <details style="margin-top:20px"><summary style="cursor:pointer;color:#57606a">Source (.mmd)</summary>
      <pre>{mmd_text}</pre></details>
  </div>
  {mermaid_script}
</body>
</html>"""


def _save_mmd_formats(
    mmd_path: "Path",
    out_dir: "Path",
    *,
    save_html: bool = True,
    save_png: bool = True,
    save_md: bool = False,
    save_pdf: bool = False,
) -> list[str]:
    """Save a .mmd file as HTML / PNG / MD / PDF. Returns saved-file descriptions.

    PNG is rendered first (via mmdc) so the HTML can reference the static image
    rather than embedding inline Mermaid — avoiding CDN parse errors at runtime.
    """
    import json, shutil, subprocess, tempfile
    saved: list[str] = []
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = mmd_path.stem
    mmd_text = mmd_path.read_text(encoding="utf-8")

    if save_md:
        md_path = out_dir / f"{stem}.md"
        md_path.write_text(f"# {stem}\n\n```mermaid\n{mmd_text}\n```\n", encoding="utf-8")
        saved.append(f"MD: {md_path}")

    # ── Render PNG / PDF via mmdc first so HTML can reference the PNG ──────
    png_generated: bool = False
    if save_png or save_pdf:
        mmdc = shutil.which("mmdc")
        if not mmdc:
            click.echo("! PNG skipped: mmdc not found (install @mermaid-js/mermaid-cli)", err=True)
        else:
            mmdc_base = [mmdc]
            # Puppeteer needs --no-sandbox on Linux with restricted user namespaces
            puppet_cfg = Path(tempfile.mktemp(suffix=".json"))
            puppet_cfg.write_text(json.dumps({"args": ["--no-sandbox"]}))
            try:
                for ext, flag in (("png", save_png), ("pdf", save_pdf)):
                    if not flag:
                        continue
                    out_path = out_dir / f"{stem}.{ext}"
                    args = mmdc_base + ["-i", str(mmd_path), "-o", str(out_path), "-p", str(puppet_cfg)]
                    try:
                        r = subprocess.run(args, capture_output=True, timeout=60)
                        if r.returncode == 0:
                            saved.append(f"{ext.upper()}: {out_path}")
                            if ext == "png":
                                png_generated = True
                        else:
                            err_text = r.stderr.decode(errors="replace").strip()
                            click.echo(f"Warning: mmdc failed for {mmd_path.name} → .{ext}: {err_text[:200]}", err=True)
                    except Exception as exc:
                        click.echo(f"Warning: {ext.upper()} render error — {exc}", err=True)
            finally:
                puppet_cfg.unlink(missing_ok=True)

    # ── HTML: embed PNG if available, else fall back to inline Mermaid ─────
    if save_html:
        html_path = out_dir / f"{stem}.html"
        png_name = f"{stem}.png" if png_generated else None
        html_path.write_text(_mmd_single_html(mmd_text, stem, png_name=png_name), encoding="utf-8")
        saved.append(f"HTML: {html_path}")

    return saved


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
    """NL description → Mermaid flowchart (for review before text2spl).

    Creates a visual representation of the workflow that can be reviewed
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

    # All rendering formats via shared helper
    for desc in _save_mmd_formats(
        output_path,
        output_dir,
        save_md=save_markdown,
        save_html=(save_html or preview),
        save_png=save_png,
        save_pdf=False,
    ):
        label, _, path_str = desc.partition(": ")
        additional_files.append(f"{label} (Browser): {path_str}" if label == "HTML" else desc)

    html_path = output_dir / (base_name + ".html") if (save_html or preview) else None

    if preview and html_path and html_path.exists():
        import webbrowser
        webbrowser.open("file://" + str(html_path.absolute()))
        click.echo("Preview opened in browser: " + str(html_path))

    # Report additional files
    if additional_files:
        click.echo("Additional formats generated:")
        for file_desc in additional_files:
            click.echo("  - " + file_desc)

    # Summary
    click.echo("\nAll files saved to: " + str(output_dir))


# ------------------------------------------------------------------ #
# spl3 img2mmd / img2text                                             #
# ------------------------------------------------------------------ #

def _resolve_output_path(
    image_path: str,
    out: str | None,
    out_dir: str | None,
    suffix: str,
    default_stem: str,
) -> "Path | None":
    """Resolve the output file path from --out / --out-dir options."""
    stem = Path(image_path).stem if not image_path.startswith("http") else default_stem
    if out:
        p = Path(out)
        if p.is_dir() or out.endswith(("/", "\\")):
            p.mkdir(parents=True, exist_ok=True)
            return p / f"{stem}{suffix}"
        p = p.with_suffix(p.suffix or suffix)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
    if out_dir:
        d = Path(out_dir)
        d.mkdir(parents=True, exist_ok=True)
        return d / f"{stem}{suffix}"
    return None


@main.command("img2mmd")
@click.argument("image_path")
@click.option("--adapter", default="openrouter", show_default=True,
              help="Multimodal adapter (openrouter, claude_cli, anthropic, google, openai).")
@click.option("--model", default=None, help="Model name override.")
@click.option("--out", "-o", default=None, metavar="FILE",
              help="Output .mmd file path (or directory).")
@click.option("--out-dir", default=None, metavar="DIR",
              help="Output directory; filename derived from image stem.")
def cmd_img2mmd(image_path, adapter, model, out, out_dir):
    """Extract Mermaid flowchart logic from an image (multimodal LLM).

    Analyzes the image and reconstructs the workflow/diagram as valid Mermaid
    code.  Handles flowcharts, architecture diagrams, pseudo-code sketches, etc.

    \b
    Default adapter: openrouter (requires OPENROUTER_API_KEY).
    Alternatives:    --adapter google  --adapter anthropic  --adapter claude_cli

    \b
    Examples:
      spl3 img2mmd workflow.png
      spl3 img2mmd screenshot.png -o output.mmd
      spl3 img2mmd diagram.jpg --out-dir ./diagrams --adapter google
    """
    from spl3.image_ops import img2mmd
    try:
        click.echo(f"Extracting Mermaid logic via {adapter}...", err=True)
        mmd = asyncio.run(img2mmd(image_path, adapter_name=adapter, model=model))
        target = _resolve_output_path(image_path, out, out_dir, ".mmd", "logic")
        if target and mmd != "(No workflow logic detected)":
            target.write_text(mmd, encoding="utf-8")
            click.echo(f"Saved to {target}")
        else:
            click.echo(mmd)
    except Exception as e:
        raise click.ClickException(str(e))


@main.command("img2text")
@click.argument("image_path")
@click.option("--adapter", default="openrouter", show_default=True,
              help="Multimodal adapter (openrouter, claude_cli, anthropic, google, openai).")
@click.option("--model", default=None, help="Model name override.")
@click.option("--out", "-o", default=None, metavar="FILE",
              help="Output .txt file path (or directory).")
@click.option("--out-dir", default=None, metavar="DIR",
              help="Output directory; filename derived from image stem.")
def cmd_img2text(image_path, adapter, model, out, out_dir):
    """Extract text / pseudo-code from an image (multimodal LLM OCR).

    Preserves indentation, code structure, headings, and formatting.
    Wraps detected code in fenced code blocks with inferred language tags.

    \b
    Default adapter: openrouter (requires OPENROUTER_API_KEY).
    Alternatives:    --adapter google  --adapter anthropic  --adapter claude_cli

    \b
    Examples:
      spl3 img2text screenshot.png
      spl3 img2text pseudocode.jpg -o extracted.txt
      spl3 img2text notes.png --out-dir ./extracted --adapter google
    """
    from spl3.image_ops import img2text
    try:
        click.echo(f"Extracting text via {adapter}...", err=True)
        text = asyncio.run(img2text(image_path, adapter_name=adapter, model=model))
        target = _resolve_output_path(image_path, out, out_dir, ".txt", "extracted")
        if target and text != "(No text detected)":
            target.write_text(text, encoding="utf-8")
            click.echo(f"Saved to {target}")
        else:
            click.echo(text)
    except Exception as e:
        raise click.ClickException(str(e))


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
@click.option("--save-svg/--no-save-svg", default=False, show_default=True,
              help="Save a vector .svg via mmdc (lossless, ideal for papers/zoom).")
@click.option("--save-pdf/--no-save-pdf", default=False, show_default=True,
              help="Save a print-ready .pdf via mmdc.")
@click.option("--paper", default="letter", show_default=True,
              type=click.Choice(["letter", "a4", "a3", "tabloid"], case_sensitive=False),
              help="Paper size for --save-pdf (letter=US default).")
@click.option("--save-spl/--no-save-spl", default=True, show_default=True,
              help="Copy the source .spl file into --out-dir alongside the other outputs.")
def cmd_spl2mmd(spl_files, out_dir, preview, save_html, save_markdown, save_png, save_svg, save_pdf, paper, save_spl):
    """Generate Mermaid flowchart from .spl file (AST-direct, no LLM).

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

        # ── .png (rendered before .html so HTML can reference the image) ───
        png_path = output_dir / (base_name + ".png")
        png_generated = False
        if save_png:
            import json as _json, tempfile as _tempfile
            _pup_cfg = _json.dumps({"args": ["--no-sandbox", "--disable-setuid-sandbox"]})
            _pup_file = _tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
            _pup_file.write(_pup_cfg)
            _pup_file.close()

            mmdc_exe = shutil.which("mmdc")
            if mmdc_exe:
                cmd_args = [mmdc_exe, "-i", str(mmd_path), "-o", str(png_path),
                            "-p", _pup_file.name, "-t", "default", "-b", "white"]
                try:
                    result = subprocess.run(cmd_args, capture_output=True, timeout=60)
                    if result.returncode == 0 and png_path.exists():
                        click.echo(f"  + PNG:      {png_path}")
                        png_generated = True
                    else:
                        err_text = result.stderr.decode(errors="replace").strip()
                        click.echo(f"  ! PNG failed: {err_text[:200]}", err=True)
                except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
                    click.echo(f"  ! PNG error: {exc}", err=True)
            else:
                click.echo("  ! PNG skipped: mmdc not found (install @mermaid-js/mermaid-cli)", err=True)

            import os as _os
            _os.unlink(_pup_file.name)

        # ── .html (uses PNG if available, else inline Mermaid) ────────────
        html_path = output_dir / (base_name + ".html")
        if save_html or preview:
            title = base_name.replace("_", " ").replace("-", " ").title()
            if png_generated:
                diagram_block = (
                    f'        <div class="diagram">'
                    f'<img src="{base_name}.png" alt="{title} Workflow diagram" '
                    f'style="max-width:100%;height:auto;border:1px solid #eee;border-radius:4px">'
                    f'</div>'
                )
                script_tag = ""
                init_script = ""
            else:
                diagram_block = f'        <div class="mermaid">\n{mermaid_text}\n        </div>'
                script_tag = '    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>'
                init_script = (
                    "    <script>\n"
                    "        mermaid.initialize({startOnLoad:true,theme:'default',securityLevel:'loose'});\n"
                    "    </script>"
                )
            rendered_by = "mmdc" if png_generated else "mermaid CDN"
            html_content = "\n".join([
                "<!DOCTYPE html>",
                "<html>",
                "<head>",
                '    <meta charset="UTF-8">',
                f"    <title>{title} — SPL Workflow</title>",
                script_tag,
                "    <style>",
                "        body{font-family:Arial,sans-serif;margin:30px;background:#f5f5f5}",
                "        .box{max-width:1200px;margin:0 auto;background:white;padding:24px;",
                "             border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,.1)}",
                "        h1{border-bottom:2px solid #eee;padding-bottom:8px}",
                "        .diagram,.mermaid{text-align:center;margin:20px 0}",
                "        .meta{color:#666;font-size:.9em}",
                "    </style>",
                "</head>",
                "<body>",
                '    <div class="box">',
                f"        <h1>{title} Workflow</h1>",
                f'        <p class="meta">Source: <code>{path.name}</code> &nbsp;|&nbsp; '
                f"Generated by <code>spl3 spl2mmd</code> (AST-direct) &nbsp;|&nbsp; Rendered by <code>{rendered_by}</code></p>",
                diagram_block,
                "    </div>",
                init_script,
                "</body>",
                "</html>",
            ])
            html_path.write_text(html_content, encoding="utf-8")
            if save_html:
                click.echo(f"  + HTML:     {html_path}")
            if preview:
                import webbrowser
                webbrowser.open("file://" + str(html_path))

        # ── .svg / .pdf — both via mmdc (vector, lossless zoom) ─────────────
        # SVG and PDF share the same mmdc puppeteer config; render together.
        if save_svg or save_pdf:
            import json as _json2, tempfile as _tempfile2, os as _os2
            _pup_cfg2 = _json2.dumps({
                "args": ["--no-sandbox", "--disable-setuid-sandbox"],
                "pdf": {"format": paper.capitalize()},
            })
            _pup_file2 = _tempfile2.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
            _pup_file2.write(_pup_cfg2)
            _pup_file2.close()

            mmdc_exe2 = shutil.which("mmdc")
            if not mmdc_exe2:
                click.echo("  ! SVG/PDF skipped: mmdc not found (install @mermaid-js/mermaid-cli)", err=True)
            else:
                for ext, flag, theme in (("svg", save_svg, "default"), ("pdf", save_pdf, "neutral")):
                    if not flag:
                        continue
                    out_path = output_dir / f"{base_name}.{ext}"
                    cmd_args = [mmdc_exe2, "-i", str(mmd_path), "-o", str(out_path),
                                "-p", _pup_file2.name, "-t", theme, "-b", "white"]
                    try:
                        result = subprocess.run(cmd_args, capture_output=True, timeout=90)
                        if result.returncode == 0 and out_path.exists():
                            size = out_path.stat().st_size
                            click.echo(f"  + {ext.upper():3s}:      {out_path}  ({size//1024}K)")
                        else:
                            err_text = result.stderr.decode(errors="replace").strip()
                            click.echo(f"  ! {ext.upper()} failed: {err_text[:200]}", err=True)
                    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
                        click.echo(f"  ! {ext.upper()} error: {exc}", err=True)

            _os2.unlink(_pup_file2.name)

    if errors:
        raise SystemExit(errors)


# ------------------------------------------------------------------ #
# spl3 json2mmd                                                       #
# ------------------------------------------------------------------ #

@main.command("json2mmd")
@click.argument(
    "json_path",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
)
@click.option(
    "-o", "--output",
    default=None,
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    help="Write Mermaid output to FILE (default: <stem>-topology.mmd alongside the JSON).",
)
@click.option(
    "--stdout",
    is_flag=True,
    default=False,
    help="Print Mermaid to stdout instead of writing a file.",
)
@click.option(
    "--no-canonicalize",
    is_flag=True,
    default=False,
    help=(
        "Keep raw class names (e.g. DraftNode) instead of canonicalizing "
        "to snake_case (e.g. draft). Canonicalization is on by default so "
        "that GED comparison aligns with SPL node labels."
    ),
)
def cmd_json2mmd(json_path: Path, output: Path | None, stdout: bool, no_canonicalize: bool) -> None:
    """Convert a rt-inspect topology JSON file to a Mermaid flowchart.

    \b
    The topology JSON is produced by:
      spl3 splc describe <file.py> --mode rt-inspect

    Node names are canonicalized by default (DraftNode → draft, SearchWeb → search_web)
    so that GED comparison against SPL-derived Mermaid aligns on node labels.

    \b
    Examples:
      spl3 json2mmd self_refine-topology.json
      spl3 json2mmd self_refine-topology.json --stdout
      spl3 json2mmd self_refine-topology.json -o self_refine-rt.mmd --no-canonicalize
    """
    import json as _json

    try:
        data = _json.loads(json_path.read_text(encoding="utf-8"))
    except _json.JSONDecodeError as exc:
        raise click.ClickException(f"Invalid JSON in {json_path.name}: {exc}")

    nodes = data.get("nodes", {})
    edges = data.get("edges", [])
    entry = data.get("entry")

    if not nodes:
        raise click.ClickException(f"No nodes found in {json_path.name}. Is this a topology JSON?")

    from spl3.splc.rt_inspect import topology_to_mermaid, canonicalize_node_id

    if not no_canonicalize:
        # Remap node IDs to canonical snake_case names
        id_map = {nid: canonicalize_node_id(nid) for nid in nodes}
        nodes = {id_map[nid]: meta for nid, meta in nodes.items()}
        edges = [
            {"source": id_map.get(e["source"], e["source"]),
             "target": id_map.get(e["target"], e["target"]),
             "label":  e.get("label", "")}
            for e in edges
        ]
        entry = id_map.get(entry, entry) if entry else entry

    mmd = topology_to_mermaid(nodes, edges, entry)

    if stdout:
        click.echo(mmd)
        return

    if output:
        out_path = output
    else:
        stem = json_path.stem
        if stem.endswith("-topology"):
            stem = stem[: -len("-topology")]
        out_path = json_path.parent / f"{stem}-topology.mmd"

    out_path.write_text(mmd, encoding="utf-8")
    click.echo(f"Mermaid written to: {out_path}")
    click.echo()
    click.echo("Next steps:")
    click.echo(f"  spl3 compare --mode ged <spl.mmd> {out_path.name}")
    click.echo(f"  # Or paste into https://mermaid.live to visualise")


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
    """Syntax-check .spl file(s) — fast parse only, no LLM call.

    Distinct from 'spl3 test' which runs the full workflow against test fixtures.
    Use this for quick CI checks and pre-commit validation.

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
    """NL → working code + README + test data in one pass (no IR).

    Produces a complete, runnable implementation directly from a natural language
    description — no .mmd or .spl intermediate representations required. Works
    with any model via ollama (local) or openrouter (400+ cloud models).

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
    """Deprecated — use 'spl3 splc describe' instead.

    \b
    DEPRECATED: This command is consolidated into 'spl3 splc describe'.
    It still works, but prefer the unified form going forward:

      spl3 splc describe <file.spl>          # describe an SPL source file
      spl3 splc describe <file.py>           # describe a compiled implementation
      spl3 splc describe <file.py> --mode rt-inspect  # deterministic topology extraction

    \b
    Examples (legacy — still work):
      spl3 describe cookbook/05_self_refine/self_refine.spl
      spl3 describe cookbook/63_parallel_code_review/
    """
    click.echo(
        "NOTE: 'spl3 describe' is deprecated. "
        "Use 'spl3 splc describe' for all describe operations.",
        err=True,
    )
    path = Path(spl_path)
    if not path.exists():
        raise click.ClickException(f"Path not found: {path}")

    if path.is_dir():
        spl_files = sorted(path.glob("*.spl"))
        if not spl_files:
            raise click.ClickException(f"No .spl files found in {path}")
        parts = []
        for f in spl_files:
            parts.append(f"-- File: {f.name}\n" + f.read_text(encoding="utf-8"))
        source = "\n\n".join(parts)
        stem = path.resolve().name
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
@click.option("--mode", "modes", multiple=True, metavar="MODE",
              help=(
                  "Comparison tier(s). Repeatable, or comma-separated: --mode llm,git-diff. "
                  "Choices: llm, git-diff, vector, bert-score, ged, vision, ast-diff, structural. "
                  "Auto-detected from file extension when omitted: "
                  ".mmd/.json→ged  .md/.spl→llm  .py/.js/.ts→git-diff  .png/.jpg→vision"
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
@click.option("--out-dir", default=None, metavar="DIR",
              help="Write report to DIR/{stem1}_vs_{stem2}.{ext}. Mutually exclusive with --output.")
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
                adapter_synthesis, output, out_dir, output_format, focus, diff_style,
                no_color, synthesize, prompt_debug):

    """Multi-tier diff: GED, LLM, vector, git-diff, AST, vision.

    Automatically picks the best default tier(s) for each file type, then
    synthesizes all tier results into a single verdict:
    EQUIVALENT | REFACTORED | DEGRADED | DIVERGED.

    \b
    Tier mapping (auto-detected defaults):
      .mmd / .json    → ged          (graph edit distance, SPL-node-aware)
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
    import sys

    if output and out_dir:
        raise click.UsageError("--output and --out-dir are mutually exclusive.")

    path1 = Path(file1)
    path2 = Path(file2)
    if not path1.exists():
        raise click.ClickException(f"File not found: {file1}")
    if not path2.exists():
        raise click.ClickException(f"File not found: {file2}")

    ext1 = path1.suffix.lower()

    # ── Auto-detect comparison tier(s) from file extension ──────────────────
    _EXT_DEFAULTS: dict[str, list[str]] = {
        ".mmd":  ["ged"],
        ".json": ["ged"],
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
    _VALID_MODES = {"llm", "git-diff", "vector", "bert-score", "ged", "vision", "ast-diff", "structural"}
    # Flatten comma-separated values: --mode llm,git-diff is equivalent to --mode llm --mode git-diff
    active_modes = [m.strip() for raw in modes for m in raw.split(",") if m.strip()]
    invalid = [m for m in active_modes if m not in _VALID_MODES]
    if invalid:
        raise click.UsageError(
            f"Invalid mode(s): {', '.join(invalid)}. "
            f"Choose from: {', '.join(sorted(_VALID_MODES))}"
        )
    if not active_modes:
        active_modes = _EXT_DEFAULTS.get(ext1, ["llm", "git-diff"])
        click.echo(f"Auto-selected tier(s) for {ext1 or 'unknown'}: {', '.join(active_modes)}", err=True)

    # ── --prompt debug: show LLM prompt and exit ─────────────────────────────
    if prompt_debug:
        if "llm" not in active_modes:
            raise click.UsageError("--prompt requires --mode llm (or a file type that auto-selects llm).")
        from spl3.compare.tiers.semantic import build_semantic_prompt
        content1 = path1.read_text(encoding="utf-8")
        content2 = path2.read_text(encoding="utf-8")
        click.echo("=" * 70)
        click.echo("LLM PROMPT:")
        click.echo("=" * 70)
        click.echo(build_semantic_prompt(content1, content2, path1, path2, focus))
        return

    from spl3.compare.engine import run_comparison
    from spl3.compare.report import render_report

    result_obj = asyncio.run(run_comparison(
        path1=path1,
        path2=path2,
        active_modes=active_modes,
        adapter_name=adapter,
        model=model,
        adapter_embed=adapter_embed,
        model_embed=model_embed,
        adapter_synthesis=adapter_synthesis,
        focus=focus,
        diff_style=diff_style,
        no_color=no_color,
        output_format=output_format,
        is_terminal=sys.stdout.isatty() and not output and not out_dir,
        synthesize=synthesize,
    ))

    _FMT_EXT = {"markdown": "md", "json": "json", "text": "txt", "html": "html"}

    # Resolve destination directory first so per-file artifacts can be generated
    # before the report (PNGs are embedded as base64 in the HTML comparison report)
    if out_dir:
        dest_dir = Path(out_dir)
    elif output:
        dest_dir = Path(output).parent
    else:
        dest_dir = None

    # Copy original source files into dest_dir so the output folder is self-contained
    if dest_dir is not None:
        import shutil
        dest_dir.mkdir(parents=True, exist_ok=True)
        for src in (path1, path2):
            dst = dest_dir / src.name
            if dst.resolve() != src.resolve():
                shutil.copy2(src, dst)
                click.echo(f"  Copied: {dst}")

    # For .mmd: generate per-file artifacts (MD / HTML / PNG / PDF) first so the
    # PNG bytes are available for embedding in the HTML comparison report panels
    panel_pngs: tuple = (None, None)
    if dest_dir is not None and ext1 == ".mmd":
        dest_dir.mkdir(parents=True, exist_ok=True)
        for p in (path1, path2):
            for desc in _save_mmd_formats(p, dest_dir, save_md=True, save_html=True, save_png=True, save_pdf=True):
                click.echo(f"  {desc}")
        png1 = dest_dir / f"{path1.stem}.png"
        png2 = dest_dir / f"{path2.stem}.png"
        panel_pngs = (
            png1.read_bytes() if png1.exists() else None,
            png2.read_bytes() if png2.exists() else None,
        )

    # Render the comparison report (PNG bytes embedded in HTML panels if available)
    output_content = render_report(result_obj, output_format, panel_pngs=panel_pngs)

    # Strip trailing dots from stems (guards against filenames like "vibe_output..py")
    s1 = path1.stem.rstrip(".")
    s2 = path2.stem.rstrip(".")
    stem_vs = f"{s1}_vs_{s2}-{'+'.join(active_modes)}"

    if out_dir:
        out_path = dest_dir / f"{stem_vs}.{_FMT_EXT.get(output_format, 'md')}"
        out_path.write_text(output_content, encoding="utf-8")
        click.echo(f"Comparison report written to: {out_path}")
        # Always write the HTML comparison report regardless of --format
        if output_format != "html":
            html_report = render_report(result_obj, "html", panel_pngs=panel_pngs)
            html_path = dest_dir / f"{stem_vs}.html"
            html_path.write_text(html_report, encoding="utf-8")
            click.echo(f"Comparison report written to: {html_path}")
    elif output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output_content, encoding="utf-8")
        click.echo(f"Comparison report written to: {out_path}")
    else:
        click.echo(output_content)

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
