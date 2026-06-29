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
from importlib.metadata import version as _pkg_version
from pathlib import Path

import click

try:
    _SPL_VERSION = _pkg_version("spl-llm")
except Exception:
    _SPL_VERSION = "unknown"

_log = logging.getLogger("spl.cli")

_SPL_LOG_DIR = Path.home() / ".spl" / "logs"


# ------------------------------------------------------------------ #
# Shared --llm / --adapter / --model option decorator                 #
# ------------------------------------------------------------------ #

def _parse_llm_spec(spec: str) -> tuple[str, str | None]:
    """Parse 'ADAPTER:MODEL' → (adapter, model). MODEL may contain '/'."""
    a, sep, m = spec.partition(":")
    return (a.strip(), m.strip() if sep else None)


def llm_options(default_adapter: str = "ollama"):
    """Decorator adding --llm / --adapter / --model to a Click command.

    --llm ADAPTER:MODEL takes precedence over --adapter/--model.
    The decorated function receives resolved ``adapter`` and ``model`` args
    (no ``llm_spec``).
    """
    import functools

    def decorator(fn):
        # Apply click options (reverse order — Click stacks bottom-up)
        fn = click.option("--model", "-m", default=None, metavar="MODEL",
                          help="Model override.")(fn)
        fn = click.option("--adapter", default=default_adapter, show_default=True,
                          metavar="NAME", help="LLM adapter.")(fn)
        fn = click.option("--llm", "llm_spec", default=None, metavar="ADAPTER:MODEL",
                          help="LLM spec as ADAPTER:MODEL (e.g. ollama:gemma3). "
                               "Wins over --adapter/--model.")(fn)

        @functools.wraps(fn)
        def wrapper(*args, llm_spec=None, adapter=default_adapter, model=None, **kwargs):
            if llm_spec:
                adapter, model = _parse_llm_spec(llm_spec)
            return fn(*args, adapter=adapter, model=model, **kwargs)

        return wrapper
    return decorator


def _make_out_stem(alias: str, input_stem: str) -> str:
    """Return a timestamped stem: <alias>-<input_stem>-<YYYYMMDD_HHMMSS>."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{alias}-{input_stem}-{ts}"


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
    result,
    started_at: datetime,
) -> Path:
    """Write a rich markdown run log matching spl-go / spl-ts format. Returns the log path."""
    _SPL_LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts_file  = started_at.strftime("%Y%m%d-%H%M%S")
    ts_human = started_at.strftime("%Y-%m-%d %H:%M:%S")

    model_slug = model_name.replace(":", "-").replace(" ", "_") if model_name else ""
    filename = (f"{stem}-{adapter_name}-{model_slug}-{ts_file}.md" if model_slug
                else f"{stem}-{adapter_name}-{ts_file}.md")
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
    ]

    lines += ["", "## Output", "", "```output", output.rstrip(), "```"]

    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return log_path


@click.group(
    help=f"SPL 3.0 — Declarative Structured Prompt Language (v{_SPL_VERSION}).",
    context_settings=dict(terminal_width=120),
)
@click.version_option(_SPL_VERSION, "--version", "-V", prog_name="spl3")
@click.option("--hub", default=None, envvar="SPL3_HUB", help="Momagrid Hub URL")
@click.option("--verbose", "-v", is_flag=True)
@click.pass_context
def main(ctx, hub, verbose):
    """SPL 3.0 — Declarative Structured Prompt Language."""
    _load_spl_config_into_env()
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)
    ctx.ensure_object(dict)
    ctx.obj["hub"] = hub


@main.command("help")
@click.pass_context
def cmd_help(ctx):
    """Show this help message and exit."""
    click.echo(ctx.parent.get_help())


# ------------------------------------------------------------------ #
# spl3 install-skill                                                  #
# ------------------------------------------------------------------ #

@main.command("install-skill", short_help="Install the /spl3 Claude Code skill.")
@click.option(
    "--global/--local", "global_", default=True,
    help="Install to ~/.claude (global, default) or ./.claude (project-local).",
)
@click.option("--dry-run", is_flag=True, help="Show what would be done without making changes.")
def cmd_install_skill(global_: bool, dry_run: bool):
    """Install the /spl3 Claude Code skill so you can type /spl3 in Claude Code.

    This copies SKILL.md to the Claude Code skills directory and adds the
    required registration block to CLAUDE.md.  Safe to re-run — it is
    idempotent.

    \b
    After installing, open a new Claude Code session and type:
        /spl3 --help
    """
    import shutil

    skill_src = Path(__file__).parent / "_skill" / "SKILL.md"
    if not skill_src.exists():
        raise click.ClickException(
            f"SKILL.md not found at {skill_src}. "
            "Re-install spl-llm: pip install --force-reinstall spl-llm"
        )

    claude_dir = Path.home() / ".claude" if global_ else Path.cwd() / ".claude"
    skill_dst  = claude_dir / "skills" / "spl3" / "SKILL.md"
    claude_md  = claude_dir / "CLAUDE.md"

    registration = (
        "\n# spl3\n"
        "- **spl3** (`~/.claude/skills/spl3/SKILL.md`) - Run, author, and manage SPL 3.0 workflows. Trigger: `/spl3`\n"
        'When the user types `/spl3`, invoke the Skill tool with `skill: "spl3"` before doing anything else.\n'
    )

    tag = "  (dry run)" if dry_run else ""

    # 1. Copy SKILL.md
    if dry_run:
        click.echo(f"  would create  {skill_dst}")
    else:
        skill_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(skill_src, skill_dst)
        click.echo(f"  ✓  {skill_dst}")

    # 2. Patch CLAUDE.md (idempotent)
    existing = claude_md.read_text(encoding="utf-8") if claude_md.exists() else ""
    if 'skill: "spl3"' in existing or "skill: 'spl3'" in existing:
        click.echo(f"  ✓  {claude_md}  (already registered){tag}")
    else:
        if dry_run:
            click.echo(f"  would append registration block to  {claude_md}")
        else:
            with claude_md.open("a", encoding="utf-8") as f:
                f.write(registration)
            click.echo(f"  ✓  {claude_md}  (registration added)")

    click.echo("")
    if not dry_run:
        click.echo("Done. Open a new Claude Code session and type /spl3 --help to verify.")
    else:
        click.echo("Dry run complete — no files were changed.")


# ------------------------------------------------------------------ #
# spl3 configure                                                      #
# ------------------------------------------------------------------ #

_SPL_CONFIG_FILE = Path.home() / ".spl" / "config"

# Named config sources.  "vibescope" path is discovered at runtime.
_CONFIG_SOURCES = {
    "spl":       _SPL_CONFIG_FILE,
}

# Candidate locations for the VibeSCOPE project .env, tried in order.
_VIBESCOPE_CANDIDATES = [
    Path.home() / "projects" / "digital-duck" / "vibescope" / ".env",
    Path.home() / "vibescope" / ".env",
    Path.home() / ".vibescope" / ".env",
]


def _resolve_source(name_or_path: str) -> Path:
    """Resolve a source name ('spl', 'vibescope') or a literal path to a Path."""
    if name_or_path == "spl":
        return _SPL_CONFIG_FILE
    if name_or_path == "vibescope":
        # Check VIBESCOPE_PROJECT_DIR env var or configured key first
        env_dir = (
            import_os().environ.get("VIBESCOPE_PROJECT_DIR")
            or _config_read_file(_SPL_CONFIG_FILE).get("VIBESCOPE_PROJECT_DIR")
        )
        if env_dir:
            p = Path(env_dir).expanduser() / ".env"
            if p.exists():
                return p
        for candidate in _VIBESCOPE_CANDIDATES:
            if candidate.exists():
                return candidate
        raise click.ClickException(
            "Cannot find VibeSCOPE .env file.\n"
            "Set VIBESCOPE_PROJECT_DIR in ~/.spl/config or as an env var, "
            "or pass the path directly: spl3 configure export --source path/to/.env"
        )
    # Treat as a literal file path
    p = Path(name_or_path).expanduser()
    if not p.exists():
        raise click.ClickException(f"Config file not found: {p}")
    return p


def import_os():
    import os
    return os


def _dotenv_parse(text: str) -> dict[str, str]:
    """Parse a .env / KEY=VALUE file, skipping comments and blank lines.
    Strips inline comments (# ...) and optional surrounding quotes from values.
    """
    result: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip()
        # Strip inline comment
        if " #" in v:
            v = v[: v.index(" #")]
        v = v.strip().strip('"').strip("'")
        if k:
            result[k] = v
    return result


def _config_read_file(path: Path) -> dict[str, str]:
    """Read a KEY=VALUE config file. Returns {} if the file doesn't exist."""
    if not path.exists():
        return {}
    return _dotenv_parse(path.read_text(encoding="utf-8"))


def _config_read() -> dict[str, str]:
    """Read ~/.spl/config."""
    return _config_read_file(_SPL_CONFIG_FILE)


def _config_write_file(path: Path, data: dict[str, str]) -> None:
    """Upsert key=value pairs into path, preserving comments and key order."""
    path.parent.mkdir(parents=True, exist_ok=True)
    remaining = dict(data)  # keys yet to be written
    lines: list[str] = []
    if path.exists():
        for raw in path.read_text(encoding="utf-8").splitlines():
            stripped = raw.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                k = stripped.partition("=")[0].strip()
                if k in remaining:
                    lines.append(f"{k}={remaining.pop(k)}")
                    continue
            lines.append(raw)
    # Append keys not already present in the file
    for k, v in remaining.items():
        lines.append(f"{k}={v}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _config_write(data: dict[str, str]) -> None:
    """Write to the default SPL config file."""
    _config_write_file(_SPL_CONFIG_FILE, data)


def _load_spl_config_into_env() -> None:
    """Load ~/.spl/config into os.environ so executor class-level defaults pick them up.

    Shell env vars already set take precedence — config file only fills gaps.
    Also loads .env from CWD when present, with the same no-overwrite rule.
    """
    import os
    for path in (_SPL_CONFIG_FILE, Path(".env")):
        for k, v in _config_read_file(path).items():
            if v and k not in os.environ:
                os.environ[k] = v


def _dotenv_format(data: dict[str, str], header: str = "") -> str:
    """Render a dict as .env-format text."""
    lines = []
    if header:
        lines.append(header)
        lines.append("")
    for k, v in data.items():
        lines.append(f"{k}={v}")
    return "\n".join(lines) + "\n"


@main.group("configure", short_help="Read and write persistent SPL configuration.")
def cmd_configure():
    """Read and write persistent SPL configuration stored in ~/.spl/config.

    \b
    Named config sources:
      spl        ~/.spl/config          (SPL runtime defaults, adapter keys)
      vibescope  <project>/.env         (VibeSCOPE server and UI settings)
      <path>     any explicit file path

    The VibeSCOPE .env is auto-discovered from VIBESCOPE_PROJECT_DIR or
    common locations. Override by setting VIBESCOPE_PROJECT_DIR in ~/.spl/config.
    """


@cmd_configure.command("init")
@click.option("--from", "from_file", default=None, metavar="FILE",
              help="Source .env file. Defaults to .env then example.env in CWD.")
@click.option("--overwrite", is_flag=True,
              help="Overwrite keys already present in ~/.spl/config.")
@click.option("--dry-run", is_flag=True,
              help="Show what would be written without modifying any file.")
def cmd_configure_init(from_file, overwrite, dry_run):
    """Bootstrap ~/.spl/config from example.env or a given .env file.

    Copies non-empty values from the source into ~/.spl/config, skipping
    keys already configured (use --overwrite to replace them).

    \b
      spl3 configure init                       # from example.env or .env in CWD
      spl3 configure init --from /path/.env     # explicit source
      spl3 configure init --overwrite           # replace existing keys too
      spl3 configure init --dry-run             # preview without writing
    """
    # Discover source file
    if from_file:
        src = Path(from_file).expanduser()
        if not src.exists():
            raise click.ClickException(f"File not found: {src}")
    else:
        for candidate in (Path(".env"), Path("example.env")):
            if candidate.exists():
                src = candidate
                break
        else:
            raise click.ClickException(
                "No .env or example.env found in the current directory.\n"
                "Pass an explicit file: spl3 configure init --from /path/to/example.env"
            )

    incoming = _config_read_file(src)
    # Strip blank values (template placeholders like KEY=)
    incoming = {k: v for k, v in incoming.items() if v}

    if not incoming:
        raise click.ClickException(f"No non-empty KEY=VALUE pairs found in {src}")

    existing = _config_read_file(_SPL_CONFIG_FILE)
    to_write: dict[str, str] = {}
    skipped: list[str] = []
    for k, v in incoming.items():
        if k in existing and not overwrite:
            skipped.append(k)
        else:
            to_write[k] = v

    tag = "  (dry-run)" if dry_run else ""
    click.echo(f"\n  Bootstrapping ~/.spl/config from {src}{tag}\n")
    col_w = max(len(k) for k in incoming) + 2
    if to_write:
        click.echo(f"  {'KEY'.ljust(col_w)}  VALUE")
        click.echo(f"  {'-' * col_w}  -----")
        for k, v in to_write.items():
            click.echo(f"  {k.ljust(col_w)}  {v}")
    if skipped:
        click.echo(f"\n  Skipped (already set — use --overwrite to replace):")
        for k in skipped:
            click.echo(f"    {k}")

    if to_write and not dry_run:
        _config_write_file(_SPL_CONFIG_FILE, to_write)
        click.echo(f"\n  Wrote {len(to_write)} key(s) → {_SPL_CONFIG_FILE}")
    elif dry_run:
        click.echo("\n  (dry-run: no files written)")


@cmd_configure.command("set")
@click.argument("pairs", nargs=-1, required=True, metavar="KEY=VALUE [KEY=VALUE ...]")
@click.option("--dest", default="spl", metavar="SOURCE",
              help="Config destination: spl (default), vibescope, or a file path.")
def cmd_configure_set(pairs, dest):
    """Set one or more configuration values.

    Accepts KEY=VALUE pairs as separate arguments or comma-separated in a
    single argument:

    \b
      spl3 configure set SPL_DEFAULT_ADAPTER=claude_cli
      spl3 configure set SPL_DEFAULT_ADAPTER=ollama SPL_DEFAULT_MODEL=gemma3
      spl3 configure set SPL_DEFAULT_ADAPTER=openrouter,SPL_DEFAULT_MODEL=qwen/qwen3-235b-a22b
      spl3 configure set VIBESCOPE_LOG_LEVEL=DEBUG --dest vibescope
    """
    updates: dict[str, str] = {}
    for token in pairs:
        for item in token.split(","):
            item = item.strip()
            if not item:
                continue
            if "=" not in item:
                raise click.BadParameter(
                    f"Expected KEY=VALUE, got: {item!r}", param_hint="pairs"
                )
            k, _, v = item.partition("=")
            k, v = k.strip(), v.strip()
            if not k:
                raise click.BadParameter(
                    f"Empty key in: {item!r}", param_hint="pairs"
                )
            updates[k] = v

    target = _resolve_source(dest) if dest != "spl" else _SPL_CONFIG_FILE
    _config_write_file(target, dict(updates))

    for k, v in updates.items():
        click.echo(f"  set  {k}={v}")
    click.echo(f"\nSaved to {target}")


@cmd_configure.command("get")
@click.argument("keys", nargs=-1, metavar="[KEY [KEY ...]]")
@click.option("--source", default="spl", metavar="SOURCE",
              help="Config source: spl (default), vibescope, or a file path.")
def cmd_configure_get(keys, source):
    """Show configuration values.

    With no arguments, prints all keys in a table.
    With one or more KEY names, prints only those keys.

    \b
      spl3 configure get
      spl3 configure get SPL_DEFAULT_ADAPTER
      spl3 configure get SPL_DEFAULT_ADAPTER SPL_DEFAULT_MODEL
      spl3 configure get --source vibescope
      spl3 configure get VIBESCOPE_LOG_LEVEL --source vibescope
    """
    src_path = _resolve_source(source) if source != "spl" else _SPL_CONFIG_FILE
    data = _config_read_file(src_path)

    import os
    if not data and not keys:
        click.echo(f"No configuration found in {src_path}")
        click.echo("  Run: spl3 configure init   (bootstrap from example.env / .env)")
        return

    if keys:
        requested: dict[str, str] = {}
        for k in keys:
            for k2 in k.split(","):
                k2 = k2.strip()
                if k2:
                    requested[k2] = data.get(k2, "(not set)")
        data = requested

    col_w   = max((len(k) for k in data), default=10) + 2
    val_w   = max((len(v) for v in data.values()), default=5) + 2
    click.echo(f"\n  {'KEY'.ljust(col_w)}  {'FILE VALUE'.ljust(val_w)}  EFFECTIVE (env)")
    click.echo(f"  {'-' * col_w}  {'-' * val_w}  ---------------")
    for k, v in data.items():
        effective = os.environ.get(k, "(not in env)")
        marker = "" if effective == v or v == "(not set)" else "  ← overridden"
        click.echo(f"  {k.ljust(col_w)}  {v.ljust(val_w)}  {effective}{marker}")
    click.echo(f"\n  Source: {src_path}")


@cmd_configure.command("export")
@click.option("--source", default="spl", metavar="SOURCE",
              help="Config source: spl (default), vibescope, or a file path.")
@click.option("-o", "--output", default=None, metavar="FILE",
              help="Write to FILE instead of stdout.")
@click.option("--keys", default=None, metavar="KEY[,KEY...]",
              help="Export only these comma-separated keys.")
def cmd_configure_export(source, output, keys):
    """Export configuration as a .env file.

    Reads from the named source and writes valid KEY=VALUE lines that can be
    sourced by a shell or consumed by dotenv-aware tools.

    \b
      spl3 configure export                         # SPL config → stdout
      spl3 configure export -o backup.env           # SPL config → file
      spl3 configure export --source vibescope      # VibeSCOPE .env → stdout
      spl3 configure export --source vibescope -o combined.env
      spl3 configure export --keys SPL_DEFAULT_ADAPTER,SPL_DEFAULT_MODEL
    """
    src_path = _resolve_source(source) if source != "spl" else _SPL_CONFIG_FILE
    data = _config_read_file(src_path)

    if not data:
        raise click.ClickException(f"No configuration found in {src_path}")

    if keys:
        wanted = {k.strip() for k in keys.split(",") if k.strip()}
        data = {k: v for k, v in data.items() if k in wanted}

    header = f"# Exported from {src_path}"
    text = _dotenv_format(data, header=header)

    if output:
        out_path = Path(output).expanduser()
        out_path.write_text(text, encoding="utf-8")
        click.echo(f"Exported {len(data)} key(s) → {out_path}")
    else:
        click.echo(text, nl=False)


@cmd_configure.command("import")
@click.argument("file", metavar="FILE")
@click.option("--dest", default="spl", metavar="SOURCE",
              help="Config destination: spl (default), vibescope, or a file path.")
@click.option("--keys", default=None, metavar="KEY[,KEY...]",
              help="Import only these comma-separated keys.")
@click.option("--dry-run", is_flag=True,
              help="Show what would be written without modifying any file.")
def cmd_configure_import(file, dest, keys, dry_run):
    """Import configuration from a .env file.

    Reads KEY=VALUE pairs from FILE (comments and blank lines are ignored)
    and merges them into the destination config, preserving existing keys
    and comments.

    \b
      spl3 configure import backup.env
      spl3 configure import .env.example --dest vibescope
      spl3 configure import combined.env --keys SPL_DEFAULT_ADAPTER,OPENROUTER_API_KEY
      spl3 configure import production.env --dry-run
    """
    src = Path(file).expanduser()
    if not src.exists():
        raise click.ClickException(f"File not found: {src}")

    data = _config_read_file(src)
    if not data:
        raise click.ClickException(f"No KEY=VALUE pairs found in {src}")

    if keys:
        wanted = {k.strip() for k in keys.split(",") if k.strip()}
        data = {k: v for k, v in data.items() if k in wanted}

    if not data:
        raise click.ClickException("No matching keys to import.")

    dest_path = _resolve_source(dest) if dest != "spl" else _SPL_CONFIG_FILE

    col_w = max(len(k) for k in data) + 2
    tag = "  (dry-run)" if dry_run else ""
    click.echo(f"\n  Importing {len(data)} key(s) from {src} → {dest_path}{tag}\n")
    click.echo(f"  {'KEY'.ljust(col_w)}  VALUE")
    click.echo(f"  {'-' * col_w}  -----")
    for k, v in data.items():
        click.echo(f"  {k.ljust(col_w)}  {v}")

    if not dry_run:
        _config_write_file(dest_path, data)
        click.echo(f"\n  Saved to {dest_path}")
    else:
        click.echo("\n  (dry-run: no files written)")


# ------------------------------------------------------------------ #
# spl run                                                             #
# ------------------------------------------------------------------ #

@main.command()
@click.argument("spl_file")
@llm_options()
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
@click.option("--kernel", is_flag=True, default=False,
              help="Enable persistent IPython kernel for CALL run_python() steps.")
@click.option("--kernel-scope", default="session",
              type=click.Choice(["session", "workflow"]), show_default=True,
              help="Kernel lifecycle scope: 'session' shares state; 'workflow' re-isolates.")
@click.option("--kernel-timeout", default=60.0, type=float, show_default=True,
              help="Per-cell execution timeout in seconds.")
@click.option("--kernel-name", default="python3", show_default=True, metavar="NAME",
              help="Jupyter kernel spec to run kernel steps under (e.g. 'sagemath' "
                   "for SageMath). A non-default value implies --kernel.")
@click.option("--persistence", default=None, metavar="BACKEND",
              type=click.Choice(["sqlite", "postgres", "dbos"]),
              help="Enable durable execution: 'sqlite' (local), 'postgres' (production), "
                   "or 'dbos' (cloud). Checkpoints every GENERATE/CALL step; "
                   "resume with --workflow-id.")
@click.option("--workflow-id", default=None, metavar="ID",
              help="Workflow run ID for persistence. Auto-generated UUID if omitted. "
                   "Pass the same ID to resume a crashed run from its last checkpoint.")
@click.option("--llm-max-output-tokens", "llm_max_output_tokens", default=None, type=int, metavar="N",
              help="Default max output tokens per GENERATE call (overrides built-in default of 1000).")
@click.pass_context
def run(ctx, spl_file, adapter, model, param, log_prompts, tools_module, allowed_tools,
        kernel, kernel_scope, kernel_timeout, kernel_name, persistence, workflow_id,
        llm_max_output_tokens):
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

    # A non-default kernel spec implies kernel mode; fail fast if it isn't installed.
    if kernel_name != "python3":
        kernel = True
    if kernel:
        from spl3.kernel import ensure_kernelspec, KernelSpecNotFound
        try:
            ensure_kernelspec(kernel_name)
        except KernelSpecNotFound as exc:
            raise click.ClickException(str(exc))

    # Persistence backend setup
    persistence_backend = None
    if persistence:
        import uuid as _uuid
        from spl3.persistence import get_backend
        if workflow_id is None:
            workflow_id = str(_uuid.uuid4())
            click.echo(f"[persistence] workflow-id: {workflow_id}")
        persistence_backend = get_backend(persistence)
        click.echo(f"[persistence] backend={persistence}  workflow-id={workflow_id}")

    asyncio.run(_run_workflow(path, adapter, model, params, hub_url, log_prompts,
                              tools_module, allowed_tools,
                              kernel=kernel, kernel_scope=kernel_scope,
                              kernel_timeout=kernel_timeout, kernel_name=kernel_name,
                              persistence=persistence_backend, workflow_id=workflow_id,
                              llm_max_output_tokens=llm_max_output_tokens))


async def _run_workflow(path, adapter_name, model, params, hub_url, log_prompts=None,
                        tools_module=None, allowed_tools=None,
                        kernel=False, kernel_scope="session", kernel_timeout=60.0,
                        kernel_name="python3",
                        persistence=None, workflow_id=None,
                        llm_max_output_tokens=None):
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

    # Build executor and attach composer for CALL workflow_name() dispatch
    from spl3.adapters import _model_compatible
    adapter_kwargs = {"model": model} if model else {}
    if allowed_tools:
        adapter_kwargs["allowed_tools"] = [t.strip() for t in allowed_tools.split(",")]
    _inner_adapter = get_adapter(adapter_name, **adapter_kwargs)

    # Resolve the effective model: if the requested model was incompatible,
    # the adapter dropped it and uses its default — reflect that here so
    # @model in the workflow gets the adapter's actual default, not an invalid name.
    effective_model = model if (model and _model_compatible(adapter_name, model)) else (
        getattr(_inner_adapter, "default_model", None)
        or getattr(_inner_adapter, "_default_model", None)
        or model or ""
    )
    if model and effective_model != model:
        click.echo(
            f"Note: model '{model}' is not compatible with adapter '{adapter_name}' "
            f"— using '{effective_model}' instead."
        )

    # Propagate effective model into workflow @model param so USING MODEL @model picks it up.
    # Only set if the user hasn't already passed --param model=... explicitly.
    if effective_model and "model" not in params:
        params["model"] = effective_model
    capturing = _CapturingAdapter(_inner_adapter)
    executor = Executor(adapter=capturing,
                        kernel=kernel, kernel_scope=kernel_scope,
                        kernel_timeout=kernel_timeout, kernel_name=kernel_name,
                        persistence=persistence, workflow_id=workflow_id)
    if llm_max_output_tokens is not None:
        executor.default_max_tokens = llm_max_output_tokens
    executor.composer = WorkflowComposer(registry, executor)
    if kernel:
        click.echo(f"IPython kernel: enabled (name={kernel_name}, scope={kernel_scope}, "
                   f"timeout={kernel_timeout}s)")
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

    # If kernel is enabled, re-register the kernel's run_python AFTER tool loading.
    # The stdlib registers a subprocess-based run_python globally; loading any
    # --tools module returns all global tools including that one, which would
    # override the kernel version. Re-registering here ensures the kernel wins.
    if kernel and executor._kernel is not None:
        executor._register_run_python()

    # Parse the file — needed for function registration and PROMPT fallback
    from spl.lexer import Lexer
    from spl.ast_nodes import CreateFunctionStatement, PromptStatement
    from spl3.parser import SPL3Parser
    from spl3._loader import load_definitions_from_file, load_workflows_from_file

    source = path.read_text(encoding="utf-8")
    _tokens = Lexer(source).tokenize()
    _program = SPL3Parser(_tokens).parse()

    # Register CREATE TOOL_API / CREATE FUNCTION definitions — both from this
    # file AND recursively through its IMPORTs (a shared 'tools.spl' imported
    # via IMPORT 'tools' previously registered nothing, since IMPORT only
    # loaded WORKFLOW definitions; CALLs to those tools silently fell back to
    # the LLM). load_definitions_from_file walks IMPORTs the same way
    # load_workflows_from_file does, with the importing file's own
    # declarations registered last so they win on name collisions.
    _imported_tool_apis, _imported_functions, _imported_procedures = load_definitions_from_file(path)

    for _stmt in _imported_functions:
        executor.functions.register(_stmt)
    for _stmt in _imported_procedures:
        executor.functions.register_procedure(_stmt)

    # Load promoted TOOL_API libraries from registry (~/.spl/tool_apis/)
    try:
        from spl3.tool_api_registry import load_all_into_executor
        _n_libs = load_all_into_executor(executor)
        if _n_libs:
            _log.debug("Loaded %d TOOL_API library file(s) from registry", _n_libs)
    except Exception as _exc:
        _log.warning("TOOL_API registry load failed (non-fatal): %s", _exc)

    # Inline TOOL_API blocks from the .spl file (override library tools on collision)
    from types import SimpleNamespace
    executor._load_tool_apis(SimpleNamespace(statements=_imported_tool_apis))

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
        if result.response_workers:
            click.echo(f"Workers: {', '.join(sorted(result.response_workers))}")
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
            result=log_result,
            started_at=started_at,
        )
        click.echo(f"Log:     {log_path}")


# ------------------------------------------------------------------ #
# spl workflow — durable run management                               #
# ------------------------------------------------------------------ #

@main.group()
def workflow():
    """Manage durable workflow runs (persistence required)."""


def _workflow_backend(backend_name: str, **kwargs):
    """Load a persistence backend or raise a helpful error."""
    try:
        from spl3.persistence import get_backend
        return get_backend(backend_name, **kwargs)
    except Exception as exc:
        raise click.ClickException(str(exc))


@workflow.command("list")
@click.option("--backend", default="sqlite", type=click.Choice(["sqlite", "postgres", "dbos"]),
              help="Persistence backend to query.")
@click.option("--status", "filter_status", default=None,
              help="Filter by status: running, complete, error.")
def workflow_list(backend, filter_status):
    """List all durable workflow runs."""
    import sqlite3, json
    from pathlib import Path

    if backend != "sqlite":
        raise click.ClickException(
            "workflow list currently supports 'sqlite' only. "
            "For postgres/dbos, query the workflows table directly."
        )
    db = Path("~/.spl/workflows.db").expanduser()
    if not db.exists():
        click.echo("No workflow database found. Run a workflow with --persistence sqlite first.")
        return
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    sql = "SELECT workflow_id, workflow_name, status, created_at, updated_at FROM workflows"
    args = []
    if filter_status:
        sql += " WHERE status = ?"
        args.append(filter_status)
    sql += " ORDER BY created_at DESC"
    rows = conn.execute(sql, args).fetchall()
    conn.close()
    if not rows:
        click.echo("No workflow runs found.")
        return
    click.echo(f"{'ID':<38}  {'NAME':<30}  {'STATUS':<10}  UPDATED")
    click.echo("-" * 90)
    for r in rows:
        import datetime
        ts = datetime.datetime.fromtimestamp(r["updated_at"]).strftime("%Y-%m-%d %H:%M:%S")
        click.echo(f"{r['workflow_id']:<38}  {r['workflow_name']:<30}  {r['status']:<10}  {ts}")


@workflow.command("status")
@click.option("--workflow-id", required=True, help="Workflow run ID.")
@click.option("--backend", default="sqlite", type=click.Choice(["sqlite", "postgres", "dbos"]))
def workflow_status(workflow_id, backend):
    """Show completed steps and current state for a workflow run."""
    import sqlite3
    from pathlib import Path

    if backend != "sqlite":
        raise click.ClickException("workflow status currently supports 'sqlite' only.")
    db = Path("~/.spl/workflows.db").expanduser()
    if not db.exists():
        raise click.ClickException("No workflow database found.")
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    wf = conn.execute(
        "SELECT * FROM workflows WHERE workflow_id = ?", (workflow_id,)
    ).fetchone()
    if not wf:
        raise click.ClickException(f"No run found with ID: {workflow_id}")

    click.echo(f"\nWorkflow : {wf['workflow_name']}  ({workflow_id})")
    click.echo(f"Status   : {wf['status']}")
    if wf["result"]:
        click.echo(f"Result   : {wf['result'][:200]}")

    steps = conn.execute(
        "SELECT step_idx, step_name, completed_at FROM steps"
        " WHERE workflow_id = ? ORDER BY step_idx",
        (workflow_id,),
    ).fetchall()
    conn.close()
    if steps:
        click.echo(f"\nCompleted steps ({len(steps)}):")
        for s in steps:
            import datetime
            ts = datetime.datetime.fromtimestamp(s["completed_at"]).strftime("%H:%M:%S")
            click.echo(f"  [{s['step_idx']:3d}] {s['step_name']:<50}  {ts}")
    else:
        click.echo("\nNo steps completed yet.")


@workflow.command("send-event")
@click.option("--workflow-id", required=True, help="Target workflow run ID.")
@click.option("--key", required=True, help="Event key (must match wait_for_approval key).")
@click.option("--value", required=True, help="Event value (e.g. 'approved' or 'rejected').")
@click.option("--backend", default="sqlite", type=click.Choice(["sqlite", "postgres", "dbos"]))
def workflow_send_event(workflow_id, key, value, backend):
    """Send a HITL event to a waiting workflow (unblocks wait_for_approval)."""
    async def _send():
        b = _workflow_backend(backend)
        await b.send_event(workflow_id, key, value)
        click.echo(f"Event sent: workflow={workflow_id}  key={key}  value={value}")

    asyncio.run(_send())


@workflow.command("resume")
@click.argument("spl_file")
@click.option("--workflow-id", required=True, help="Run ID to resume from its last checkpoint.")
@llm_options()
@click.option("--backend", default="sqlite", type=click.Choice(["sqlite", "postgres", "dbos"]),
              help="Persistence backend.")
@click.pass_context
def workflow_resume(ctx, spl_file, workflow_id, adapter, model, backend):
    """Resume a crashed or interrupted workflow from its last checkpoint.

    Equivalent to:
        spl3 run FILE --persistence BACKEND --workflow-id ID
    """
    from pathlib import Path
    from spl3.persistence import get_backend
    path = Path(spl_file)
    if not path.exists():
        raise click.ClickException(f"File not found: {path}")

    # Load saved params from DB to avoid re-specifying them
    persistence_backend = get_backend(backend)
    click.echo(f"[resume] workflow-id={workflow_id}  backend={backend}")
    asyncio.run(_run_workflow(path, adapter, model, {}, ctx.obj.get("hub"),
                              persistence=persistence_backend, workflow_id=workflow_id))


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
@llm_options()
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
    """Manage the Code-RAG index (used by text2spl and text2mmd)."""


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
@llm_options()
@click.option("--out-dir", "spec_dir", default=None, metavar="DIR",
              help="Write all spec files to DIR instead of alongside each .spl file.")
@click.option("--catalog", default=None,
              help="Restrict to active recipes listed in cookbook_catalog.json.")
@click.option("--skip-existing", is_flag=True, default=True, show_default=True,
              help="Skip recipes that already have a -spec.md file.")
def code_rag_describe_all(cookbook_dir, adapter, model, spec_dir, catalog, skip_existing):  # adapter/model from @llm_options
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

@main.command("text2spl", short_help="Compile workflow description in natural language into SPL code.")
@click.argument("description", required=False, default=None)
@click.option("--description", "-d", "description_opt", default=None, metavar="TEXT_OR_FILE",
              help="Natural language description, a file path, or a -spec.md file "
                   "(Section 0 is extracted automatically).")
@llm_options()
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

def _mmd_single_html(mmd_text: str, title: str) -> str:
    """Standalone HTML page that renders one mermaid diagram."""
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
  <style>
    body{{font-family:Arial,sans-serif;margin:20px;background:#f5f5f5}}
    .container{{max-width:1400px;margin:0 auto;background:white;padding:20px;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,.1)}}
    .mermaid{{text-align:center;margin:20px 0}}
    pre{{background:#f8f9fa;border:1px solid #e9ecef;border-radius:4px;padding:15px;font-family:monospace;white-space:pre-wrap}}
  </style>
</head>
<body>
  <div class="container">
    <h2>{title}</h2>
    <div class="mermaid">{mmd_text}</div>
    <details style="margin-top:20px"><summary style="cursor:pointer;color:#57606a">Source</summary>
      <pre>{mmd_text}</pre></details>
  </div>
  <script>mermaid.initialize({{startOnLoad:true,theme:'default',securityLevel:'loose',errorLevel:'warn'}});</script>
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
    """Save a .mmd file as HTML / PNG / MD / PDF. Returns saved-file descriptions."""
    import shutil, subprocess
    saved: list[str] = []
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = mmd_path.stem
    mmd_text = mmd_path.read_text(encoding="utf-8")

    if save_md:
        md_path = out_dir / f"{stem}.md"
        md_path.write_text(f"# {stem}\n\n```mermaid\n{mmd_text}\n```\n", encoding="utf-8")
        saved.append(f"MD: {md_path}")

    if save_html:
        html_path = out_dir / f"{stem}.html"
        html_path.write_text(_mmd_single_html(mmd_text, stem), encoding="utf-8")
        saved.append(f"HTML: {html_path}")

    # PNG and PDF both go through mmdc (supports -o *.png and -o *.pdf natively)
    if save_png or save_pdf:
        import json, tempfile
        mmdc = shutil.which("mmdc")
        mmdc_base = [mmdc] if mmdc else ["npx", "--yes", "@mermaid-js/mermaid-cli"]

        # Puppeteer needs --no-sandbox on Linux systems with restricted user namespaces
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
                    else:
                        click.echo(f"Warning: mmdc failed for {mmd_path.name} → .{ext}", err=True)
                except Exception as exc:
                    click.echo(f"Warning: {ext.upper()} render error — {exc}", err=True)
        finally:
            puppet_cfg.unlink(missing_ok=True)

    return saved


# ------------------------------------------------------------------ #
# spl3 text2mmd                                                       #
# ------------------------------------------------------------------ #

def _extract_mmd_sections(text: str, llm, model) -> str:
    """Delegate to _extract_spec_intro for consistent section extraction across commands."""
    return _extract_spec_intro(text, llm=llm, model=model)


@main.command("text2mmd", short_help="Generate a Mermaid flowchart from natural language.")
@click.argument("description", required=False, default=None)
@click.option("--description", "-d", "description_opt", default=None, metavar="TEXT_OR_FILE",
              help="Natural language workflow description or file path.")
@llm_options()
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

    # Generate Mermaid diagram
    llm = get_adapter(adapter, **({"model": model} if model else {}))

    # Check if it's a file path
    if Path(raw).exists():
        full_text = Path(raw).read_text(encoding="utf-8")
        desc_text = _extract_mmd_sections(full_text, llm, model)
    else:
        desc_text = raw

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


@main.command("img2mmd", short_help="Extract a Mermaid flowchart from an image.")
@click.argument("image_path")
@llm_options(default_adapter="openrouter")
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


@main.command("img2text", short_help="Extract text and pseudo-code from an image.")
@click.argument("image_path")
@llm_options(default_adapter="openrouter")
@click.option("--out", "-o", default=None, metavar="FILE",
              help="Output .txt file path (or directory).")
@click.option("--out-dir", default=None, metavar="DIR",
              help="Output directory; filename derived from image stem.")
def cmd_img2text(image_path, adapter, model, out, out_dir):
    """Extract text and pseudo-code from an image (OCR via multimodal LLM).

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

@main.command("spl2mmd", short_help="Generate a Mermaid flowchart for each .spl file.")
@click.argument("spl_files", nargs=-1, required=True, metavar="SPL_FILE...")
@click.option("--out-dir", default=None, metavar="DIR",
              help="Output directory for all generated files (default: mermaid/ subdir of each input's parent).")
@click.option("--preview/--no-preview", default=True, show_default=True,
              help="Open each diagram in the browser after generation.")
@click.option("--save-html/--no-save-html", default=True, show_default=True,
              help="Save an .html browser-viewable file alongside the .mmd.")
@click.option("--save-markdown/--no-save-markdown", "--save-md/--no-save-md",
              default=True, show_default=True,
              help="Save a .md file with a fenced mermaid code block.")
@click.option("--save-svg/--no-save-svg", default=True, show_default=True,
              help="Save a .svg vector image via mmdc.")
@click.option("--save-png/--no-save-png", default=True, show_default=True,
              help="Save a .png raster image via mmdc.")
@click.option("--save-pdf/--no-save-pdf", default=True, show_default=True,
              help="Save a print-ready .pdf via mmdc or Chrome headless.")
@click.option("--save-spl/--no-save-spl", default=True, show_default=True,
              help="Copy the source .spl file into --out-dir alongside the other outputs.")
@click.option("--remove-function-nodes/--keep-function-nodes", default=False, show_default=True,
              help="Strip FUNCTION definition nodes from the diagram (post-processor).")
def cmd_spl2mmd(spl_files, out_dir, preview, save_html, save_markdown, save_svg, save_png, save_pdf, save_spl, remove_function_nodes):
    """Generate a Mermaid flowchart for each .spl file (AST-direct, no LLM).

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
      spl3 spl2mmd workflow.spl                   # → workflow/mermaid/{svg,png,pdf,html,md,mmd}
      spl3 spl2mmd *.spl --out-dir diagrams/      # → diagrams/{svg,png,pdf,...}
      spl3 spl2mmd workflow.spl --no-preview      # all formats, no browser open
      spl3 spl2mmd workflow.spl --no-save-pdf     # skip pdf only
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
            if remove_function_nodes:
                from spl3.spl2mmd import remove_function_nodes as _remove_fn
                mermaid_text = _remove_fn(mermaid_text)
        except NoWorkflowError as exc:
            click.echo(f"WARN: {path.name} — {exc}", err=True)
            continue
        except Exception as exc:
            click.echo(f"FAILED: {spl_file} — {exc}", err=True)
            errors += 1
            continue

        output_dir = Path(out_dir).resolve() if out_dir else path.parent / "mermaid"
        output_dir.mkdir(parents=True, exist_ok=True)
        base_name = _make_out_stem("spl2mmd", path.stem) if out_dir else path.stem

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

        # ── .svg ─────────────────────────────────────────────────────────
        if save_svg:
            svg_path = output_dir / (base_name + ".svg")
            import json as _json, tempfile as _tempfile
            _pup_cfg_svg = _json.dumps({"args": ["--no-sandbox", "--disable-setuid-sandbox"]})
            _pup_file_svg = _tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
            _pup_file_svg.write(_pup_cfg_svg)
            _pup_file_svg.close()
            svg_generated = False
            for mmdc_cmd in ["mmdc", "npx"]:
                try:
                    cmd_args = (
                        [mmdc_cmd, "-i", str(mmd_path), "-o", str(svg_path),
                         "-p", _pup_file_svg.name, "-t", "default", "-b", "white"]
                        if mmdc_cmd == "mmdc"
                        else ["npx", "--yes", "@mermaid-js/mermaid-cli",
                              "-i", str(mmd_path), "-o", str(svg_path),
                              "-p", _pup_file_svg.name, "-t", "default", "-b", "white"]
                    )
                    result = subprocess.run(cmd_args, capture_output=True, timeout=60)
                    if result.returncode == 0 and svg_path.exists():
                        click.echo(f"  + SVG:      {svg_path}")
                        svg_generated = True
                        break
                    if mmdc_cmd == "npx":
                        break
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    if mmdc_cmd == "npx":
                        break
                    continue
            import os as _os
            _os.unlink(_pup_file_svg.name)
            if not svg_generated:
                click.echo("  ! SVG skipped: mmdc not found (install @mermaid-js/mermaid-cli)", err=True)

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
              help="Write generated SPL to FILE (overrides --out-dir).")
@click.option("--out-dir", default=None, metavar="DIR",
              help="Output directory; file named mmd2spl-<stem>-<datetime>.spl.")
@llm_options()
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
def cmd_mmd2spl(mermaid_file, output, out_dir, adapter, model, validate, template, pattern_hints, prompt_debug, timeout):
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

        # Inject available tools catalog (stdlib + registry) so the LLM knows
        # what already exists and reuses CALL instead of re-generating TOOL_API.
        try:
            from spl3.tool_api_registry import available_tools_prompt_block
            _tools_block = available_tools_prompt_block()
            if _tools_block:
                _TOOLS_ANCHOR = "== MANDATORY SPL 3.0 CONVENTIONS"
                if _TOOLS_ANCHOR in prompt_text:
                    prompt_text = prompt_text.replace(
                        _TOOLS_ANCHOR,
                        _tools_block + "\n" + _TOOLS_ANCHOR,
                        1,
                    )
        except Exception:
            pass   # non-fatal: generation proceeds without the catalog

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
                    spl_lines.append(f'  @{var_name} := "";')

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
                        f'        WHEN contains("complete") THEN',
                        f'          RETURN @{var_name} WITH status = "complete";',
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
                        f'    WHEN contains("condition") THEN',
                        f'      @result := "path_a";',
                        f"    ELSE",
                        f'      @result := "path_b";',
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
    elif out_dir:
        d = Path(out_dir).expanduser()
        d.mkdir(parents=True, exist_ok=True)
        stem = Path(mermaid_file).stem
        out_path = d / (_make_out_stem("mmd2spl", stem) + ".spl")
    else:
        out_path = None

    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(spl_code, encoding="utf-8")
        click.echo(f"SPL code written to: {out_path}")
        mmd_output = out_path.with_suffix(".mmd")
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
@click.option("--semantic/--no-semantic", default=True, show_default=True,
              help="Run semantic lint checks (undefined vars, unreachable code, WHILE exits, CALL targets)")
@click.option("--strict", is_flag=True, default=False,
              help="Exit non-zero if any WARN-level issues are found (default: only ERRORs count)")
def cmd_validate(spl_files, semantic, strict):
    """Validate SPL syntax and semantics of one or more .spl files.

    \b
    Syntax checks (always):
      - Lexer + parser — catches malformed tokens, unclosed blocks, unknown keywords

    Semantic checks (--semantic, on by default):
      - Undefined variable  @x used before GENERATE/CALL/assignment defines it
      - Unreachable code    statements after RETURN inside a workflow
      - Potential infinite  WHILE loop with no RETURN inside body and no max_iterations
      - Undefined CALL      procedure not in CREATE FUNCTION declarations or stdlib

    Examples:
      spl3 validate workflow.spl
      spl3 validate tests/claude_cli/sonnet/*.spl --strict
      spl3 validate workflow.spl --no-semantic
    """
    from pathlib import Path
    from spl.lexer import Lexer
    from spl3.parser import SPL3Parser
    from spl3.linter import lint_program

    errors = 0
    warnings = 0

    for spl_file in spl_files:
        path = Path(spl_file)
        if not path.exists():
            click.echo(f"MISSING: {path}", err=True)
            errors += 1
            continue
        source = path.read_text(encoding="utf-8")
        try:
            tokens = Lexer(source).tokenize()
            program = SPL3Parser(tokens).parse()
        except Exception as exc:
            click.echo(f"SYNTAX ERROR: {path} — {exc}", err=True)
            errors += 1
            continue

        # Semantic lint pass
        file_warns = 0
        if semantic:
            try:
                issues = lint_program(program)
                for issue in issues:
                    click.echo(f"  {issue}  ({path})", err=(issue.level == "ERROR"))
                    if issue.level == "ERROR":
                        errors += 1
                    else:
                        file_warns += 1
                        warnings += 1
            except Exception as exc:
                click.echo(f"  LINT ERROR: {path} — {exc}", err=True)

        if file_warns == 0 and errors == 0:
            click.echo(f"OK: {path}")
        elif file_warns > 0:
            click.echo(f"OK (with {file_warns} warning(s)): {path}")

    if errors or (strict and warnings):
        raise SystemExit(errors or 1)


# ------------------------------------------------------------------ #
# spl3 explain                                                        #
# ------------------------------------------------------------------ #

@main.command("explain")
@click.argument("spl_file")
def cmd_explain(spl_file):
    """Show execution plan for an .spl file (no LLM call)."""
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


def _extract_spec_intro(text: str, llm=None, model=None) -> str:
    """Extract the workflow-relevant intro from a spec file.

    Tries two naming conventions in order:
      1. Named sections: '## Summary' and/or '### 1. Purpose'
      2. Numbered sections: '## 0. ...' through end of '## 1. ...'
    If neither is found, falls back to LLM summarization (when llm is
    provided) or the first 1000 chars (when no llm is available).
    """
    import re

    def _extract_block(pattern: str, src: str) -> str | None:
        """Return the heading block matching pattern up to the next same-or-higher heading."""
        lines = src.splitlines(keepends=True)
        heading_re = re.compile(pattern, re.IGNORECASE)
        level = len(re.match(r"^(#+)", pattern.lstrip("^")).group(1))
        stop_re = re.compile(r"^#{1," + str(level) + r"}\s", re.MULTILINE)
        start = None
        for i, line in enumerate(lines):
            if heading_re.match(line.rstrip()):
                start = i
                break
        if start is None:
            return None
        for i, line in enumerate(lines[start + 1:], start + 1):
            if stop_re.match(line):
                return "".join(lines[start:i]).strip()
        return "".join(lines[start:]).strip()

    # Convention 1: named sections (## Summary, ### 1. Purpose)
    named_patterns = [r"^##\s+Summary\b", r"^###\s+1\.\s+Purpose\b"]
    named_blocks = [b for p in named_patterns if (b := _extract_block(p, text))]
    if named_blocks:
        return "\n\n".join(named_blocks)

    # Convention 2: numbered sections (## 0. ... ## 1. ...)
    sec0 = re.search(r'^#{1,6}\s+0[.\s]', text, re.MULTILINE)
    if sec0:
        sec2 = re.search(r'^#{1,6}\s+2[.\s]', text, re.MULTILINE)
        end = sec2.start() if sec2 else len(text)
        return text[sec0.start():end].strip()

    # Fallback: LLM summarization or first 1000 chars
    if llm is not None:
        import asyncio as _asyncio
        summary_prompt = (
            "Read the following document and write a concise (3–6 sentence) "
            "workflow description suitable for code generation. "
            "Focus on the steps, decisions, and data flow. Output ONLY the description.\n\n"
            f"{text}"
        )
        result = _asyncio.run(llm.generate(summary_prompt, **({"model": model} if model else {})))
        return result if isinstance(result, str) else getattr(result, "content", str(result))

    return text[:1000].strip()


@main.command("vibe", short_help="One-shot: NL description → working code + README.")
@click.argument("description", default=None, required=False, metavar="DESCRIPTION")
@click.option("--description", "-d", "description_opt", default=None, metavar="TEXT_OR_FILE",
              help="Natural language requirement or file path (overrides positional arg).")
@click.option("--spec", "spec_file", default=None, metavar="SPEC_FILE",
              help="Reverse-engineered spec file (e.g. S1-spec.md). Uses the full spec as the "
                   "authoritative requirement — bypasses Mermaid and SPL IR steps. "
                   "Mutually exclusive with --description / positional arg.")
@click.option("--target", "-t", "lang", default="python/pocketflow", show_default=True,
              help="Target language/framework (e.g. go, ts, python/langgraph).")
@llm_options()
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
def cmd_vibe(description, description_opt, spec_file, lang, adapter, model, output, out_dir, use_rag, rag_k, references, no_readme, verbose, prompt_debug):
    """One-shot prototype generator: NL description → working code + README + test data.

    Generates a complete, runnable implementation directly from a natural language
    description or spec file — no .mmd or .spl IR steps required. Outputs code,
    README.md, and test data in one pass. Works with any model available via
    ollama (local) or openrouter (400+ cloud models).

    \b
    Input modes (mutually exclusive):
      positional / --description   Free-form NL or file; extracts Summary/Purpose
                                   sections if present, otherwise summarizes.
      --spec SPEC_FILE             Full spec file (e.g. S1-spec.md from splc describe).
                                   Uses the complete content as the authoritative
                                   requirement — no section filtering. Intended for
                                   the NeurIPS S7 ablation step (bypass .mmd + .spl IR).

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

      # Spec-driven (ablation S7): full spec → code, bypassing .mmd and .spl IR
      spl3 vibe --spec S1-agent-spec.md --out-dir ./out \\
        --adapter claude_cli --model claude-sonnet-4-6

      # Preview prompt before sending
      spl3 vibe --spec S1-spec.md --adapter claude_cli --prompt
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

    # ── Resolve input ─────────────────────────────────────────────────────────
    # --spec: full spec file, used as-is (spec-driven coding, NeurIPS S7 ablation)
    # --description / positional: free text or file with section extraction
    if spec_file and (description_opt or description):
        raise click.UsageError("--spec is mutually exclusive with --description / positional arg.")

    if spec_file:
        spec_path = Path(spec_file)
        if not spec_path.exists() or not spec_path.is_file():
            raise click.UsageError(f"--spec file not found: {spec_file}")
        raw_desc = spec_path.read_text(encoding="utf-8")
        prompt_label = "Functional Specification"
        if verbose:
            click.echo(f"  Spec-driven mode: {spec_path.name} ({len(raw_desc)} chars) — full content used, no IR steps")
    else:
        raw = description_opt or description
        if not raw:
            raise click.UsageError(
                "Provide a description as a positional argument, --description, or --spec."
            )
        candidate = Path(raw)
        if candidate.exists() and candidate.is_file():
            try:
                from spl3.adapters import get_adapter as _get_adapter
                _llm = _get_adapter(adapter, **({"model": model} if model else {}))
            except Exception:
                _llm = None
            raw_desc = _extract_spec_intro(candidate.read_text(encoding="utf-8"), llm=_llm, model=model)
            if verbose:
                click.echo(f"  Spec extracted: {len(raw_desc)} chars (Summary/Purpose sections, numbered sections, or LLM summary)")
        else:
            raw_desc = raw
        prompt_label = "Requirement to Implement"

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
        f"# {prompt_label}\n\n"
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

== REGIME CLASSIFICATION — DO THIS FIRST ==

Before writing any construct, classify each operation in the diagram:

  DETERMINISTIC (single correct answer expressible as code)?
    → CREATE TOOL_API ... AS PYTHON $$ ... $$  +  CALL
  PROBABILISTIC (requires reasoning, judgment, or generation)?
    → CREATE FUNCTION ... AS $$ <prompt> $$    +  GENERATE

Classical / deterministic indicators — ALWAYS use TOOL_API:
  external API call, HTTP request, data fetch, math/statistics, string split/join/index,
  data transformation, file I/O, sorting/filtering, format conversion, chart/plot rendering,
  any operation a developer could unit-test with an exact expected value.

Probabilistic indicators — use CREATE FUNCTION:
  summarization, interpretation, nuanced classification, text generation, quality judgment,
  any operation where "correct" depends on context requiring reasoning.

Using GENERATE for a deterministic operation is a category error — like solving
Schrödinger''s equation to predict a missile trajectory. Use the right regime.

== MANDATORY SPL 3.0 CONVENTIONS (FOLLOW EXACTLY) ==

1. WORKFLOW declaration — INPUT/OUTPUT before DO, no semicolons on those lines:
   WORKFLOW <name>
     INPUT @param1 TYPE, @param2 TYPE := default
     OUTPUT @result TYPE
   DO
     ... statements ...
   END;
   Do NOT put semicolons after INPUT or OUTPUT lines.
   Do NOT wrap the body in a nested DO...END; block.

2. Variable sigils: Use @ for workflow variables (@input, @result, @i).

3. Variable assignment: @var := "value";

4. Deterministic tool definition and call (classical regime):
   -- Define at the top of the file, before CREATE FUNCTION and WORKFLOW:
   CREATE TOOL_API <name>(<param> TEXT, ...) RETURNS TEXT AS PYTHON $$
   import needed_library   -- imports go inside the body
   def <name>(<param>: str, ...) -> str:
       try:
           # real implementation — not a stub
           return result_as_string
       except Exception as e:
           return f"error: {{e}}"
   $$;
   -- Call inside WORKFLOW:
   CALL <name>(@arg1, @arg2) INTO @var;
   RULES:
   - Every parameter and return value is str (SPL passes everything as strings).
   - The function name inside $$ MUST match the TOOL_API name exactly.
   - Return "error: <msg>" on failure — never raise unhandled exceptions.
   - Include all imports inside the $$ body.
   - Use '' (two single quotes) for apostrophes inside $$ string literals.

5. LLM function definition and call (probabilistic regime):
   CREATE FUNCTION <name>(<param> TYPE, ...) RETURNS TYPE AS $$
     <natural language prompt using {{param}} template slots>
   $$;
   GENERATE <name>(@arg) INTO @var;
   RULES:
   - Function parameters do NOT use @ prefix.
   - Use {{param}} (curly braces) inside $$ bodies for template slots.
   - Use '' (two single quotes) for apostrophes inside $$ bodies.

6. Branching: EVALUATE @<var> WHEN contains("token") THEN ... ELSE ... END;
   WHEN clauses use contains("...") for string matching — never comparison operators.

7. Parallel execution:
   CALL PARALLEL
     branch_one(@arg) INTO @var1,
     branch_two(@arg) INTO @var2
   END;
   No CALL/GENERATE prefix on branch lines. Comma-separated, no semicolon on last branch.

8. Looping:
   WHILE @i < @max_iterations DO ... END;
   Never hardcode iteration limits — declare INPUT @max_iterations INTEGER := N.
   Use = (single equals) for comparisons. SPL has no == operator.

9. Return (top-level only — never inside WHILE or EVALUATE):
   RETURN @var WITH status = "complete";
   For quality-gated loops, force-exit by setting @i := @max_iterations inside EVALUATE,
   then RETURN after the loop closes.

10. Score/numeric comparisons: extract a categorical token first.
    WRONG: EVALUATE @score WHEN contains("0.8") THEN ...
    RIGHT: GENERATE gate_fn(@score) INTO @gate  -- returns "done" or "continue"
           EVALUATE @gate WHEN contains("done") THEN ...

== FILE STRUCTURE ORDER ==

1. CREATE TOOL_API blocks   (deterministic Python tools — classical regime)
2. CREATE FUNCTION blocks   (LLM prompt templates — probabilistic regime)
3. WORKFLOW block

== EXAMPLE — mixed regime (stock data pipeline) ==

CREATE TOOL_API get_ticker(ticker_list TEXT, idx TEXT) RETURNS TEXT AS PYTHON $$
def get_ticker(ticker_list: str, idx: str) -> str:
    return [t.strip() for t in ticker_list.split(",")][int(idx)]
$$;

CREATE TOOL_API fetch_ohlcv(ticker TEXT, years TEXT) RETURNS TEXT AS PYTHON $$
import yfinance as yf, pandas as pd
def fetch_ohlcv(ticker: str, years: str) -> str:
    try:
        end = pd.Timestamp.today()
        start = end - pd.DateOffset(years=float(years))
        df = yf.download(ticker, start=start, end=end, auto_adjust=True)
        return "error: no data" if df.empty else df.to_csv()
    except Exception as e:
        return f"error: {{e}}"
$$;

CREATE FUNCTION interpret_metrics(ticker TEXT, csv_data TEXT) RETURNS TEXT AS $$
  Analyze the OHLCV data for {{ticker}} and write a 2-sentence investment summary
  covering trend direction, volatility, and key risk. Data: {{csv_data}}
$$;

WORKFLOW stock_report
  INPUT @tickers TEXT := "GOOG,META,MSFT"
  INPUT @years TEXT := "2"
  INPUT @max_tickers INTEGER := 3
  OUTPUT @report TEXT
DO
  @i := 0;
  @report := "";
  WHILE @i < @max_tickers DO
    CALL get_ticker(@tickers, @i) INTO @ticker;
    CALL fetch_ohlcv(@ticker, @years) INTO @data;
    GENERATE interpret_metrics(@ticker, @data) INTO @summary;
    @report := @report + @ticker + ": " + @summary + "\n";
    @i := @i + 1;
  END;
  RETURN @report WITH status = "complete";
END;

The generated SPL must be complete, executable, and follow the diagram logic exactly.

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


@main.command("describe", short_help="Generate a plain-English spec for an .spl file or folder.")
@click.argument("spl_path")
@llm_options()
@click.option("--out-dir", "spec_dir", default=None, metavar="DIR",
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
      spl3 describe my_workflow.spl --adapter claude_cli --out-dir docs/specs
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
        spec_path = out_dir / (_make_out_stem("spl2spec", stem) + "-spec.md")
    else:
        spec_path = spec_parent / spec_filename

    spec_path.write_text(spec_text, encoding="utf-8")
    click.echo(f"Spec written to: {spec_path}")


# ------------------------------------------------------------------ #
# spl3 compare                                                        #
# ------------------------------------------------------------------ #

@main.command("compare", short_help="Multi-tier file diff with verdict synthesis.")
@click.argument("file1")
@click.argument("file2")
@click.option("--mode", "modes", multiple=True, metavar="MODE",
              help=(
                  "Comparison tier(s). Repeatable, or comma-separated: --mode llm,git-diff. "
                  "Choices: llm, git-diff, vector, bert-score, ged, vision, ast-diff, structural, rouge. "
                  "Auto-detected from file extension when omitted: "
                  ".mmd/.json→ged  .md/.spl→llm  .py/.js/.ts→git-diff  .png/.jpg→vision"
              ))
@llm_options()
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

    """Multi-tier diff: topology · semantic · syntactic · structural · character · embedding.

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
    _VALID_MODES = {"llm", "git-diff", "vector", "bert-score", "ged", "vision", "ast-diff", "structural", "rouge"}
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
        out_stem = _make_out_stem("compare", f"{s1}-vs-{s2}")
        out_path = dest_dir / f"{out_stem}.{_FMT_EXT.get(output_format, 'md')}"
        out_path.write_text(output_content, encoding="utf-8")
        click.echo(f"Comparison report written to: {out_path}")
        # Always write the HTML comparison report regardless of --format
        if output_format != "html":
            html_report = render_report(result_obj, "html", panel_pngs=panel_pngs)
            html_path = dest_dir / f"{out_stem}.html"
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
# spl3 judge                                                          #
# ------------------------------------------------------------------ #

def _resolve_llm(llm_specs: tuple[str, ...], adapter: str, model: str | None):
    """Resolve (adapter_name, model) pairs from --llm or --adapter/--model fallback.

    --llm takes precedence; --adapter/--model are the legacy fallback.
    Each --llm value is ADAPTER:MODEL-ID where MODEL-ID may contain '/'.
    """
    if llm_specs:
        pairs = []
        for spec in llm_specs:
            a, sep, m = spec.partition(":")
            pairs.append((a.strip(), m.strip() if sep else None))
        return pairs
    return [(adapter, model or None)]


@main.command("judge", short_help="Evaluate content against a rubric using an LLM judge.")
@click.argument("file")
@click.option("--criteria", default="clarity", show_default=True, metavar="BUILTIN|FILE",
              help="Built-in rubric name or path to a .yaml rubric file. "
                   "Built-ins: spl-compliance, correctness, clarity, ai-review.")
@click.option("--llm", "llm_specs", multiple=True, metavar="ADAPTER:MODEL",
              help="Judge spec as ADAPTER:MODEL (e.g. claude_cli:claude-opus-4-6). "
                   "Repeat to form a panel — judges run concurrently. "
                   "Wins over --adapter/--model.")
@click.option("--adapter", default="ollama", show_default=True, metavar="NAME",
              help="Legacy: judge adapter (used only when --llm is not given).")
@click.option("--model", default=None, metavar="MODEL",
              help="Legacy: judge model (used only when --llm is not given).")
@click.option("--aggregation", default="majority", show_default=True,
              type=click.Choice(["majority", "confidence_weighted", "unanimous"]),
              help="Panel aggregation strategy (ignored for single judge).")
@click.option("--swap-check", is_flag=True, default=False,
              help="Re-run each judge with reversed criterion order; flag if verdict disagrees.")
@click.option("--format", "output_format", default="markdown", show_default=True,
              type=click.Choice(["markdown", "json", "text"]),
              help="Output format.")
@click.option("--output", "-o", default=None, metavar="FILE",
              help="Write judge report to FILE.")
@click.option("--prompt", "prompt_debug", is_flag=True, default=False,
              help="Display the judge prompt and exit.")
@click.option("--cache-key", default=None, metavar="KEY",
              help="On PASS verdict, add the 'ai_reviewed' exposition badge to this "
                   "content-cache entry. Key is the hex digest from 'spl3 cache list'.")
def cmd_judge(file, criteria, llm_specs, adapter, model, aggregation,
              swap_check, output_format, output, prompt_debug, cache_key):
    """Evaluate FILE against a rubric using an LLM judge.

    Returns a structured verdict (PASS / FAIL / ESCALATE), per-criterion scores,
    chain-of-thought reasoning, and actionable feedback.

    Repeat --llm to run a panel of judges concurrently; results are aggregated
    via --aggregation (majority / confidence_weighted / unanimous).

    \b
    Examples:
      spl3 judge output.md --criteria clarity --llm claude_cli:claude-opus-4-6
      spl3 judge my_section.md --criteria correctness --llm openrouter:google/gemini-2.5-pro
      spl3 judge S5-spec.md --criteria spl-compliance --llm claude_cli:claude-opus-4-6 -o S6-judge.md
      spl3 judge output.md --criteria spl-compliance \\
          --llm claude_cli:claude-opus-4-6 \\
          --llm openrouter:google/gemini-2.5-pro \\
          --llm openrouter:qwen/qwen-max \\
          --aggregation majority --swap-check
      spl3 judge section.md --criteria correctness --llm ollama:llama3.2 --cache-key <hex>
    """
    from spl3.judge.rubrics import load_rubric
    from spl3.judge.engine import run_judge, run_panel
    from spl3.judge.prompt import build_judge_prompt
    from spl3.judge.report import render_judge_report

    path = Path(file)
    if not path.exists():
        raise click.ClickException(f"File not found: {path}")

    content = path.read_text(encoding="utf-8")

    try:
        rubric = load_rubric(criteria)
    except (ValueError, FileNotFoundError) as exc:
        raise click.ClickException(str(exc))

    if prompt_debug:
        prompt = build_judge_prompt(content, rubric)
        click.echo("=" * 70)
        click.echo("JUDGE PROMPT:")
        click.echo("=" * 70)
        click.echo(prompt)
        return

    pairs = _resolve_llm(llm_specs, adapter, model)

    if len(pairs) == 1:
        judge_adapter, judge_model = pairs[0]
        result = asyncio.run(run_judge(
            content=content,
            rubric=rubric,
            adapter_name=judge_adapter,
            model=judge_model,
            swap_check=swap_check,
        ))
    else:
        click.echo(
            f"Panel mode: {len(pairs)} judges, aggregation={aggregation}", err=True
        )
        result = asyncio.run(run_panel(
            content=content,
            rubric=rubric,
            members=pairs,
            aggregation=aggregation,
            swap_check=swap_check,
        ))

    report = render_judge_report(result, output_format=output_format)

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")
        click.echo(f"Judge report written to: {out_path}")
        click.echo(f"Verdict: {result.verdict}  Score: {result.score:.1f}/10  "
                   f"Confidence: {result.confidence}")
    else:
        click.echo(report)

    # ---- judge → cache promotion integration ----
    if cache_key:
        if result.verdict == "PASS":
            import dataclasses, json as _json
            from spl3.cache import get_content_cache
            verdict_dict = dataclasses.asdict(result)
            try:
                cache = get_content_cache()
                cache.promote(cache_key, "ai_reviewed", verdict=verdict_dict)
                click.echo(
                    f"Cache entry {cache_key[:16]}... promoted to ai_reviewed.", err=True
                )
            except Exception as exc:
                click.echo(f"Warning: cache promotion failed: {exc}", err=True)
        else:
            click.echo(
                f"Verdict {result.verdict} — cache entry not promoted "
                f"(promotion requires PASS).", err=True
            )


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


# ------------------------------------------------------------------ #
# spl3 cache                                                           #
# ------------------------------------------------------------------ #

from spl3.cache.cli import cmd_cache as _cache_command
main.add_command(_cache_command, name="cache")


# ------------------------------------------------------------------ #
# spl3 experiment                                                      #
# ------------------------------------------------------------------ #

@main.group("experiment", short_help="Batch runner and reporting for ablation studies.")
def cmd_experiment():
    """Batch experiment runner and reporting for NeurIPS-style ablation studies."""


# ── Helpers shared by run + report ────────────────────────────────────────────

def _exp_auto_alias(model: str) -> str:
    m = model.split(":")[0].split("/")[-1]
    parts = m.split("-")
    if parts[0] == "claude" and len(parts) > 1:
        return parts[1]
    if parts[0] == "gpt":
        return "".join(parts[:2])
    if parts[0] == "gemini":
        return parts[0]
    return parts[0]


def _exp_slug(recipe: str, adapter: str, model_alias: str) -> str:
    return f"{recipe}-{adapter}-{model_alias}"


def _exp_out(base: Path, step: str, slug: str, ts: str, suffix: str) -> Path:
    return base / f"{step}-{slug}-{ts}{suffix}"


def _exp_dir(base: Path, step: str, slug: str) -> Path:
    return base / f"{step}-{slug}"


def _exp_completed(base: Path, step: str, slug: str, ts: str, suffix: str) -> "Path | None":
    """Return the output path if the step is already done (any timestamp), else None."""
    # Exact-ts match first (fastest)
    exact = _exp_out(base, step, slug, ts, suffix)
    if exact.exists():
        return exact
    # Any existing file with this step+slug pattern (prior run checkpoint)
    pattern = f"{step}-{slug}-*{suffix}"
    matches = sorted(base.glob(pattern))
    return matches[-1] if matches else None


def _exp_dir_completed(base: Path, step: str, slug: str) -> "Path | None":
    d = _exp_dir(base, step, slug)
    if d.exists() and d.is_dir() and any(d.iterdir()):
        return d
    return None


# ── spl3 experiment run ────────────────────────────────────────────────────────

@cmd_experiment.command("run")
@click.option("--recipes", "-r", multiple=True, required=True, metavar="RECIPE",
              help="Recipe name(s). Repeatable. E.g. --recipes self_refine react")
@click.option("--spl-paths", multiple=True, metavar="PATH",
              help="Explicit .spl file paths matching --recipes order. "
                   "If omitted, looks for <recipe>.spl in --spl-root.")
@click.option("--spl-root", default=None, metavar="DIR",
              help="Root directory to search for <recipe>.spl files.")
@click.option("--adapters", "-a", multiple=True, required=True, metavar="ADAPTER",
              help="Adapter name(s). E.g. --adapters claude_cli openrouter")
@click.option("--models", "-m", multiple=True, required=True, metavar="MODEL",
              help="Model ID(s) matching --adapters order. E.g. --models claude-sonnet-4-6 google/gemini-3-flash-preview")
@click.option("--pipeline", default="S1,S2,S3,S4,S5,S6", show_default=True, metavar="STEPS",
              help="Comma-separated pipeline steps to run. E.g. S1,S2,S3,S4,S5,S6 or S1,S2,S3,S4,S5,S6,S7,S8,S9,S10")
@click.option("--judge-adapter", default="claude_cli", show_default=True,
              help="Adapter for compare (S6/S9/S10) judge steps.")
@click.option("--judge-model", default="claude-opus-4-6", show_default=True,
              help="Model for compare (S6/S9/S10) judge steps.")
@click.option("--base-dir", default="~/.vibescope/neurips", show_default=True, metavar="DIR",
              help="Output base directory.")
@click.option("--overwrite/--no-overwrite", default=False, show_default=True,
              help="Overwrite existing step outputs (skip checkpoint logic).")
@click.option("--dry-run", is_flag=True, default=False,
              help="Print commands without executing.")
def cmd_experiment_run(recipes, spl_paths, spl_root, adapters, models, pipeline,
                       judge_adapter, judge_model, base_dir, overwrite, dry_run):
    """Run a batch of NDD pipeline experiments across recipes × adapters × models.

    \b
    Each (recipe, adapter, model) combination runs the requested pipeline steps
    in sequence. Steps already completed are skipped (checkpoint/resume).

    \b
    Examples:
      spl3 experiment run \\
        --recipes self_refine react \\
        --adapters claude_cli openrouter \\
        --models claude-sonnet-4-6 google/gemini-3-flash-preview \\
        --pipeline S1,S2,S3,S4,S5,S6

      spl3 experiment run --recipes self_refine --adapters claude_cli \\
        --models claude-sonnet-4-6 --pipeline S7,S8,S9,S10 --dry-run
    """
    import subprocess
    from datetime import datetime as _dt

    if len(adapters) != len(models):
        raise click.UsageError(
            f"--adapters and --models must have the same count "
            f"(got {len(adapters)} adapters, {len(models)} models)"
        )

    steps = [s.strip() for s in pipeline.split(",") if s.strip()]
    base = Path(base_dir).expanduser()
    base.mkdir(parents=True, exist_ok=True)

    ts = _dt.now().strftime("%Y%m%d_%H%M%S")

    # Build recipe → spl path map
    recipe_spl: dict[str, Path | None] = {}
    for i, recipe in enumerate(recipes):
        if spl_paths and i < len(spl_paths):
            recipe_spl[recipe] = Path(spl_paths[i])
        elif spl_root:
            root = Path(spl_root).expanduser()
            candidates = list(root.rglob(f"{recipe}.spl")) + list(root.rglob(f"*{recipe}*.spl"))
            recipe_spl[recipe] = candidates[0] if candidates else None
        else:
            recipe_spl[recipe] = None

    total = len(recipes) * len(adapters)
    run_num = 0

    for recipe in recipes:
        spl_file = recipe_spl.get(recipe)
        for adapter, model in zip(adapters, models):
            run_num += 1
            model_alias = _exp_auto_alias(model)
            slug = _exp_slug(recipe, adapter, model_alias)
            click.echo(f"\n{'='*60}")
            click.echo(f"Run {run_num}/{total}: {recipe} / {adapter} / {model_alias}")
            click.echo(f"{'='*60}")

            # Resolve step input/output paths (updated as steps complete)
            paths: dict[str, Path] = {}

            def _resolve_input(step: str) -> str:
                """Return the best available input path for a step."""
                dep = {"S2": "S1", "S3": "S2", "S4": "S3", "S5": "S4",
                       "S6": ("S1", "S5"), "S7": "S1", "S8": "S7",
                       "S9": ("S1", "S8"), "S10": ("S6", "S9")}
                d = dep.get(step)
                if isinstance(d, tuple):
                    return tuple(str(paths.get(x, f"<{x}-missing>")) for x in d)
                return str(paths.get(d, f"<{d}-missing>")) if d else ""

            spl_arg = str(spl_file) if spl_file else f"{recipe}.spl"

            for step in steps:
                # Build the command for this step
                out_suffix = {
                    "S1": "-spec.md", "S2": ".mmd", "S3": ".spl",
                    "S5": "-spec.md", "S6": "-compare.md",
                    "S8": "-spec.md", "S9": "-compare.md", "S10": "-compare.md",
                }.get(step)
                is_dir_step = step in ("S4", "S7")

                # Checkpoint: skip if already done
                if not overwrite:
                    if is_dir_step:
                        done = _exp_dir_completed(base, step, slug)
                    else:
                        done = _exp_completed(base, step, slug, ts, out_suffix or "")
                    if done:
                        paths[step] = done
                        click.echo(f"  ✓ {step} already done → {done.name}")
                        continue

                # Build CLI command
                llm_flags = f"--adapter {adapter} --model {model}"
                judge_flags = f"--adapter {judge_adapter} --model {judge_model}"
                out_path = _exp_out(base, step, slug, ts, out_suffix or "")
                dir_path = _exp_dir(base, step, slug)

                if step == "S1":
                    cmd = (f"spl3 splc describe {spl_arg} --include-docs "
                           f"{llm_flags} -o {out_path}")
                elif step == "S2":
                    s1 = _resolve_input("S2")
                    cmd = f"spl3 text2mmd {s1} {llm_flags} -o {out_path}"
                elif step == "S3":
                    s2 = _resolve_input("S3")
                    cmd = f"spl3 mmd2spl {s2} {llm_flags} -o {out_path}"
                elif step == "S4":
                    s3 = _resolve_input("S4")
                    ow = "--overwrite" if overwrite else ""
                    cmd = (f"spl3 splc compile {s3} --lang python/pocketflow --use-llm "
                           f"{llm_flags} --out-dir {dir_path} {ow}").strip()
                elif step == "S5":
                    s4d = paths.get("S4", _exp_dir(base, "S4", slug))
                    cmd = f"spl3 splc describe {s4d}/ {llm_flags} -o {out_path}"
                elif step == "S6":
                    s1, s5 = _resolve_input("S6")
                    cmd = f"spl3 compare {s1} {s5} {judge_flags} -o {out_path}"
                elif step == "S7":
                    s1 = _resolve_input("S7")
                    cmd = f"spl3 vibe --spec {s1} {llm_flags} --out-dir {dir_path}"
                elif step == "S8":
                    s7d = paths.get("S7", _exp_dir(base, "S7", slug))
                    cmd = f"spl3 splc describe {s7d}/ {llm_flags} -o {out_path}"
                elif step == "S9":
                    s1, s8 = _resolve_input("S9")
                    cmd = f"spl3 compare {s1} {s8} {judge_flags} -o {out_path}"
                elif step == "S10":
                    s6, s9 = _resolve_input("S10")
                    cmd = f"spl3 compare {s6} {s9} {judge_flags} -o {out_path}"
                else:
                    click.echo(f"  ⚠ Unknown step {step} — skipping", err=True)
                    continue

                click.echo(f"  → {step}: {cmd}")
                if dry_run:
                    if is_dir_step:
                        paths[step] = dir_path
                    else:
                        paths[step] = out_path
                    continue

                result = subprocess.run(cmd, shell=True, text=True, cwd=str(Path.home()))
                if result.returncode != 0:
                    click.echo(f"  ✗ {step} FAILED (exit {result.returncode}) — stopping this run", err=True)
                    break

                # Record completed path
                if is_dir_step:
                    paths[step] = dir_path
                else:
                    # Find the actual output file (in case name differs slightly)
                    if out_path.exists():
                        paths[step] = out_path
                    else:
                        matches = sorted(base.glob(f"{step}-{slug}-*{out_suffix}"))
                        if matches:
                            paths[step] = matches[-1]
                        else:
                            paths[step] = out_path
                click.echo(f"  ✓ {step} done → {paths[step].name}")

    click.echo(f"\n✅ Experiment batch complete. Results in: {base}")


# ── spl3 experiment report ─────────────────────────────────────────────────────

@cmd_experiment.command("report")
@click.option("--base-dir", default="~/.vibescope/neurips", show_default=True, metavar="DIR",
              help="Directory to scan for compare results.")
@click.option("--steps", default="S6,S9,S10", show_default=True, metavar="STEPS",
              help="Comma-separated compare steps to include in the report.")
@click.option("--format", "output_format", default="markdown", show_default=True,
              type=click.Choice(["markdown", "csv", "json"]),
              help="Output format.")
@click.option("--output", "-o", default=None, metavar="FILE",
              help="Write report to FILE instead of stdout.")
def cmd_experiment_report(base_dir, steps, output_format, output):
    """Aggregate compare scores from completed experiments into a leaderboard.

    \b
    Scans --base-dir for S6/S9/S10 compare files, extracts Structure/Logic/Quality/Overall
    scores, and renders a ranked leaderboard table.

    \b
    Examples:
      spl3 experiment report
      spl3 experiment report --format csv -o leaderboard.csv
      spl3 experiment report --steps S6 --format json
    """
    import csv as _csv
    import io
    import re

    base = Path(base_dir).expanduser()
    if not base.exists():
        raise click.ClickException(f"Directory not found: {base}")

    target_steps = [s.strip() for s in steps.split(",") if s.strip()]

    # Filename: S{N}-{recipe}-{adapter}-{model_alias}-{ts}-compare.md
    FNAME_RE = re.compile(r"^(S\d+)-(.+?)-([^-]+)-([^-]+)-(\d{8}_\d{6})-compare\.md$")
    DIM_RE   = re.compile(
        r"\|\s*\*{0,2}(Structure|Logic|Quality|Overall)\*{0,2}\s*\|"
        r"\s*\*{0,2}([\d.]+)\*{0,2}\s*\|\s*\*{0,2}([\d.]+)\*{0,2}",
        re.IGNORECASE,
    )

    def _parse_scores(path: Path) -> dict:
        text = path.read_text(encoding="utf-8")
        dims: dict[str, tuple] = {}
        for m in DIM_RE.finditer(text):
            dim = m.group(1).capitalize()
            try:
                dims[dim] = (float(m.group(2)), float(m.group(3)))
            except ValueError:
                pass
        overall = dims.get("Overall")
        avg = round(sum(overall) / 2, 2) if overall else None
        return {"dims": dims, "overall_avg": avg}

    # Scan files, keep latest timestamp per (step, recipe, adapter, model_alias)
    runs: dict[tuple, dict] = {}
    for f in sorted(base.glob("S*-compare.md")):
        m = FNAME_RE.match(f.name)
        if not m:
            continue
        step, recipe, adapter, model_alias, ts = m.groups()
        if step not in target_steps:
            continue
        key = (recipe, adapter, model_alias)
        runs.setdefault(key, {})
        existing = runs[key].get(step)
        if existing is None or ts > existing["ts"]:
            runs[key][step] = {"ts": ts, "file": f, **_parse_scores(f)}

    if not runs:
        raise click.ClickException(
            f"No compare files found for steps {target_steps} in {base}\n"
            "Run the pipeline first with: spl3 experiment run ..."
        )

    def _score(run_step: dict, dim: str) -> str:
        if not run_step:
            return "—"
        pair = run_step.get("dims", {}).get(dim)
        return f"{pair[0]:.1f}/{pair[1]:.1f}" if pair else "—"

    def _overall(run_step: dict) -> float | None:
        return run_step.get("overall_avg") if run_step else None

    # Build rows
    rows = []
    for (recipe, adapter, model_alias), step_data in sorted(runs.items()):
        row: dict = {"recipe": recipe, "adapter": adapter, "model": model_alias}
        for step in target_steps:
            sd = step_data.get(step, {})
            row[f"{step}_structure"] = _score(sd, "Structure")
            row[f"{step}_logic"]     = _score(sd, "Logic")
            row[f"{step}_quality"]   = _score(sd, "Quality")
            row[f"{step}_overall"]   = f"{_overall(sd):.2f}" if _overall(sd) else "—"

        # ΔIR if both S6 and S9 available
        s6o = _overall(step_data.get("S6", {}))
        s9o = _overall(step_data.get("S9", {}))
        row["delta_ir"] = f"{s6o - s9o:+.2f}" if (s6o is not None and s9o is not None) else "—"
        row["_s6o"] = s6o
        row["_s9o"] = s9o
        row["_delta"] = (s6o - s9o) if (s6o is not None and s9o is not None) else None
        rows.append(row)

    # Sort by S6 overall desc, then ΔIR desc
    rows.sort(key=lambda r: (-(r["_s6o"] or 0), -(r["_delta"] or 0)))

    # ── Format ────────────────────────────────────────────────────────────────
    if output_format == "json":
        import json as _json
        clean = [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]
        text = _json.dumps(clean, indent=2)

    elif output_format == "csv":
        buf = io.StringIO()
        if rows:
            fieldnames = [k for k in rows[0] if not k.startswith("_")]
            writer = _csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        text = buf.getvalue()

    else:  # markdown
        # Build header
        step_cols = []
        for step in target_steps:
            step_cols += [f"{step} S", f"{step} L", f"{step} Q", f"{step} Ovr"]
        header = ["Recipe", "Adapter", "Model"] + step_cols
        if "S6" in target_steps and "S9" in target_steps:
            header.append("ΔIR")

        sep = ["---"] * len(header)
        md_rows = [header, sep]
        for r in rows:
            cells = [r["recipe"], r["adapter"], r["model"]]
            for step in target_steps:
                cells += [r[f"{step}_structure"], r[f"{step}_logic"],
                           r[f"{step}_quality"], r[f"{step}_overall"]]
            if "S6" in target_steps and "S9" in target_steps:
                cells.append(r["delta_ir"])
            md_rows.append(cells)

        # Summary
        delta_vals = [r["_delta"] for r in rows if r["_delta"] is not None]
        lines = ["# NeurIPS Experiment Leaderboard", ""]
        if delta_vals:
            avg_ir = sum(delta_vals) / len(delta_vals)
            ir_wins = sum(1 for d in delta_vals if d > 0)
            lines += [
                f"**Runs:** {len(rows)}  |  "
                f"**Avg ΔIR:** {avg_ir:+.2f}  |  "
                f"**IR wins:** {ir_wins}/{len(delta_vals)}  |  "
                f"**Max ΔIR:** {max(delta_vals):+.2f}",
                "",
            ]
        lines += [" | ".join(row) for row in md_rows]
        text = "\n".join(lines)

    if output:
        Path(output).write_text(text, encoding="utf-8")
        click.echo(f"Report written to: {output}")
    else:
        click.echo(text)


# ------------------------------------------------------------------ #
# spl3 migrate                                                         #
# ------------------------------------------------------------------ #

@main.command("migrate", short_help="Migrate a codebase to a new runtime via the DODA pipeline.")
@click.argument("source", metavar="SOURCE")
@click.option("--target", "-t", required=True,
              type=click.Choice(["python/pocketflow", "python/langgraph", "python/crewai",
                                 "python/autogen", "python/liquid", "go", "ts", "python"]),
              help="Target runtime to compile to.")
@llm_options(default_adapter="claude_cli")
@click.option("--judge-adapter", default="claude_cli", show_default=True,
              help="Adapter for the final fidelity compare step.")
@click.option("--judge-model", default="claude-opus-4-6", show_default=True,
              help="Model for the final fidelity compare step.")
@click.option("--out-dir", default=None, metavar="DIR",
              help="Output directory for all artifacts. Defaults to ./migrate-<stem>-<ts>/")
@click.option("--name", default=None, metavar="NAME",
              help="Short name used in filenames (default: stem of SOURCE path).")
@click.option("--include-docs/--no-include-docs", default=True, show_default=True,
              help="Pass --include-docs to splc describe (pulls in README if present).")
@click.option("--no-rag", is_flag=True, default=False,
              help="Disable RAG context for compile and vibe steps.")
@click.option("--skip-compare", is_flag=True, default=False,
              help="Skip the final fidelity compare step.")
@click.option("--auto", is_flag=True, default=False,
              help="Non-interactive: skip human checkpoint prompts (CI / dry-run use).")
@click.option("--dry-run", is_flag=True, default=False,
              help="Print commands without executing.")
def cmd_migrate(source, target, adapter, model, judge_adapter, judge_model,
                out_dir, name, include_docs, no_rag, skip_compare, auto, dry_run):
    """Migrate an existing implementation to a new runtime via the DODA pipeline.

    \b
    Chains four steps with human checkpoints at the two IR stages:

      SOURCE  →  splc describe  →  spec.md
              →  text2mmd       →  .mmd       ⚠️  HUMAN CHECKPOINT: review topology
              →  mmd2spl        →  .spl       ⚠️  HUMAN CHECKPOINT: review IR + validate
              →  splc compile   →  target code
              →  spl3 compare   →  fidelity score

    \b
    Human checkpoints are interactive pauses (press Enter to continue, Ctrl-C to abort).
    Use --auto to skip them (non-interactive / CI mode).

    \b
    Examples:
      # Migrate a PocketFlow recipe to LangGraph
      spl3 migrate cookbook/05_self_refine/ --target python/langgraph \\
        --adapter claude_cli --model claude-sonnet-4-6 --out-dir ./migrate-self_refine/

      # Migrate single file, dry-run to preview commands
      spl3 migrate agent.py --target go --adapter claude_cli --dry-run

      # Non-interactive (e.g. batch migration script)
      spl3 migrate src/ --target python/pocketflow --adapter openrouter \\
        --model google/gemini-3-flash-preview --auto
    """
    import subprocess
    from datetime import datetime as _dt

    src_path = Path(source).expanduser().resolve()
    if not src_path.exists():
        raise click.ClickException(f"SOURCE not found: {src_path}")

    stem = name or src_path.stem
    ts   = _dt.now().strftime("%Y%m%d_%H%M%S")

    if out_dir:
        work = Path(out_dir).expanduser()
    else:
        work = Path.cwd() / f"migrate-{stem}-{ts}"
    work.mkdir(parents=True, exist_ok=True)

    llm_flags   = f"--adapter {adapter}" + (f" --model {model}" if model else "")
    judge_flags = f"--adapter {judge_adapter} --model {judge_model}"
    rag_flag    = "--no-rag" if no_rag else ""

    def _run(cmd: str, label: str) -> bool:
        click.echo(f"\n  → {cmd}")
        if dry_run:
            return True
        result = subprocess.run(cmd, shell=True, text=True)
        if result.returncode != 0:
            click.echo(f"  ✗ {label} failed (exit {result.returncode})", err=True)
            return False
        return True

    def _checkpoint(step: str, path: str, instruction: str) -> None:
        """Pause for human review. Skipped in --auto mode."""
        click.echo(f"\n{'='*60}")
        click.echo(f"  ⚠️  HUMAN CHECKPOINT — {step}")
        click.echo(f"{'='*60}")
        click.echo(f"  File : {path}")
        click.echo(f"  Task : {instruction}")
        click.echo()
        if not auto and not dry_run:
            click.prompt(
                "  Review the file, make any edits, then press Enter to continue "
                "(Ctrl-C to abort)",
                default="", show_default=False,
            )

    # ── Step 1: splc describe → spec.md ──────────────────────────────────────
    spec_file = work / f"{stem}-spec.md"
    click.echo(f"\n{'='*60}")
    click.echo(f"  MIGRATE: {src_path.name}  →  {target}")
    click.echo(f"  Output : {work}")
    click.echo(f"{'='*60}")

    click.echo("\n[ Step 1/4 ] splc describe → spec.md")
    docs_flag = "--include-docs" if include_docs else ""
    cmd1 = f"spl3 splc describe {src_path} {docs_flag} {llm_flags} -o {spec_file}".strip()
    if not _run(cmd1, "splc describe"):
        raise SystemExit(1)

    # ── Step 2: text2mmd → .mmd  (HUMAN CHECKPOINT) ──────────────────────────
    mmd_file = work / f"{stem}.mmd"
    click.echo("\n[ Step 2/4 ] text2mmd → Mermaid diagram")
    cmd2 = f"spl3 text2mmd {spec_file} {llm_flags} -o {mmd_file}"
    if not _run(cmd2, "text2mmd"):
        raise SystemExit(1)

    _checkpoint(
        "Mermaid diagram",
        str(mmd_file),
        "Verify: all nodes present, edges correct, loop back-edge present, no dangling nodes.\n"
        "  Edit the .mmd file directly to fix any issues before continuing.",
    )

    # ── Step 3: mmd2spl → .spl  (HUMAN CHECKPOINT) ───────────────────────────
    spl_file = work / f"{stem}.spl"
    click.echo("\n[ Step 3/4 ] mmd2spl → SPL IR")
    cmd3 = f"spl3 mmd2spl {mmd_file} {llm_flags} -o {spl_file}"
    if not _run(cmd3, "mmd2spl"):
        raise SystemExit(1)

    # Auto-validate after mmd2spl
    click.echo(f"  Validating {spl_file.name} …")
    val_cmd = f"spl3 validate {spl_file}"
    click.echo(f"  → {val_cmd}")
    if not dry_run:
        subprocess.run(val_cmd, shell=True, text=True)  # non-fatal — user reviews next

    _checkpoint(
        "SPL IR",
        str(spl_file),
        "Check: CREATE FUNCTION bodies use {{param}} single-braces, WHILE loops have exits,\n"
        "  all GENERATE calls reference declared functions, no invented keywords.\n"
        "  Fix any issues in the .spl file before continuing.",
    )

    # ── Step 4: splc compile → target ─────────────────────────────────────────
    target_dir = work / "target"
    target_dir.mkdir(exist_ok=True)
    click.echo(f"\n[ Step 4/4 ] splc compile → {target}")
    llm_compile = "--use-llm" if target not in ("python/pocketflow", "python/langgraph", "go", "ts") else ""
    cmd4 = (
        f"spl3 splc compile {spl_file} --lang {target} {llm_compile} "
        f"{llm_flags} --out-dir {target_dir} {rag_flag} --overwrite"
    ).strip()
    if not _run(cmd4, "splc compile"):
        raise SystemExit(1)

    # ── Optional: fidelity compare ────────────────────────────────────────────
    if not skip_compare:
        # Describe the target output to get spec2, then compare spec1 vs spec2
        spec2_file  = work / f"{stem}-spec2.md"
        score_file  = work / f"{stem}-migration-score.md"
        click.echo("\n[ Bonus ] Fidelity compare: describe target → compare specs")
        cmd5a = f"spl3 splc describe {target_dir}/ {llm_flags} -o {spec2_file}"
        if _run(cmd5a, "splc describe target"):
            cmd5b = (
                f"spl3 compare {spec_file} {spec2_file} "
                f"{judge_flags} -o {score_file}"
            )
            _run(cmd5b, "compare fidelity")

    # ── Summary ───────────────────────────────────────────────────────────────
    click.echo(f"\n{'='*60}")
    click.echo(f"  ✅ Migration complete")
    click.echo(f"{'='*60}")
    artifacts = [
        ("Spec (source)",  spec_file),
        ("Mermaid IR",     mmd_file),
        ("SPL IR",         spl_file),
        ("Target code",    target_dir),
    ]
    if not skip_compare:
        artifacts += [
            ("Spec (target)",  work / f"{stem}-spec2.md"),
            ("Fidelity score", work / f"{stem}-migration-score.md"),
        ]
    for label, path in artifacts:
        exists = "✓" if (dry_run or Path(path).exists()) else "✗"
        click.echo(f"  {exists}  {label:16}  {path}")

    if not skip_compare and not dry_run:
        score_path = work / f"{stem}-migration-score.md"
        if score_path.exists():
            click.echo(f"\n  Fidelity report → {score_path}")


# ── spl3 tool-api ────────────────────────────────────────────────────────────

@main.group("tool-api", short_help="Manage the CREATE TOOL_API library registry.")
def cmd_tool_api():
    """List, promote, and remove deterministic TOOL_API libraries.

    TOOL_API libraries are .spl files stored in ~/.spl/tool_apis/.
    They are loaded automatically before each workflow execution so any
    CALL statement can dispatch to their deterministic Python functions.

    \b
    Workflow:
        spl3 tool-api promote my_recipe.spl --name finance_tools   # register
        spl3 tool-api list                                          # inspect
        spl3 tool-api remove finance_tools                          # remove
    """


@cmd_tool_api.command("list", short_help="List registered TOOL_API libraries.")
@click.option("--tools", "show_tools", is_flag=True,
              help="Show individual function signatures inside each library.")
@click.option("--stdlib", is_flag=True,
              help="Also list built-in stdlib tools (web_search, http_get, ...).")
def cmd_tool_api_list(show_tools, stdlib):
    """Show all .spl files registered in the TOOL_API library (~/.spl/tool_apis/).

    \b
    Examples:
        spl3 tool-api list                  # file-level summary
        spl3 tool-api list --tools          # show function signatures
        spl3 tool-api list --tools --stdlib # include stdlib tools too
    """
    from spl3.tool_api_registry import list_libraries, list_tools, registry_dir

    if show_tools:
        # Function-level view
        tools = list_tools(include_stdlib=stdlib)
        if not tools:
            msg = "No TOOL_API tools found"
            if not stdlib:
                msg += " in registry (use --stdlib to include built-in tools)"
            click.echo(msg)
            return

        # Group by source
        by_source: dict[str, list] = {}
        for t in tools:
            by_source.setdefault(t.source, []).append(t)

        if stdlib and "stdlib" in by_source:
            click.echo("Stdlib tools (built-in, always available):")
            for t in by_source.pop("stdlib"):
                click.echo(f"  CALL {t.spl_signature()}")
            click.echo()

        if by_source:
            click.echo(f"User library tools in {registry_dir()}:")
            for lib_name, sigs in sorted(by_source.items()):
                click.echo(f"\n  [{lib_name}.spl]")
                for t in sigs:
                    click.echo(f"    CALL {t.spl_signature()}")
        elif not stdlib:
            click.echo(f"No library tools in {registry_dir()}")
            click.echo("Use `spl3 tool-api promote <file.spl>` to add one.")
    else:
        # File-level view (original behaviour)
        libs = list_libraries()
        if not libs:
            click.echo(f"No TOOL_API libraries registered in {registry_dir()}")
            click.echo("Use `spl3 tool-api promote <file.spl>` to add one.")
            return
        click.echo(f"TOOL_API libraries in {registry_dir()}:\n")
        for lib in libs:
            click.echo(
                f"  {lib['name']:<30}  {lib['tool_count']} tool(s)  "
                f"({lib['size']:,} bytes)  {lib['path']}"
            )


@cmd_tool_api.command("promote", short_help="Add a .spl file to the TOOL_API library.")
@click.argument("spl_file", metavar="FILE")
@click.option("--name", "-n", default=None,
              help="Registry name (default: stem of FILE).")
@click.option("--force", is_flag=True,
              help="Overwrite existing library entry with the same name.")
def cmd_tool_api_promote(spl_file, name, force):
    """Promote a .spl file containing CREATE TOOL_API blocks to the shared library.

    The file is copied to ~/.spl/tool_apis/<name>.spl.
    All future `spl3 run` invocations will load these tools automatically.

    \b
    Example:
        spl3 tool-api promote cookbook/65_stock_analysis/stock_analysis.spl --name finance
        spl3 tool-api list
    """
    from pathlib import Path as _Path
    from spl3.tool_api_registry import promote, registry_dir

    src = _Path(spl_file)
    if not src.exists():
        click.echo(f"Error: file not found: {spl_file}", err=True)
        raise SystemExit(1)

    dest_name = name or src.stem
    dest = registry_dir() / f"{dest_name}.spl"
    if dest.exists() and not force:
        click.echo(
            f"Error: library '{dest_name}' already exists. "
            f"Use --force to overwrite.", err=True
        )
        raise SystemExit(1)

    try:
        dest_path = promote(src, name=dest_name)
        click.echo(f"✓  Promoted → {dest_path}")
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@cmd_tool_api.command("search", short_help="Search TOOL_API functions by name or keyword.")
@click.argument("query", metavar="QUERY")
@click.option("--stdlib", is_flag=True,
              help="Also search built-in stdlib tools.")
def cmd_tool_api_search(query, stdlib):
    """Search registered TOOL_API functions whose name or parameter names
    contain QUERY (case-insensitive).

    \b
    Examples:
        spl3 tool-api search log
        spl3 tool-api search csv --stdlib
    """
    from spl3.tool_api_registry import list_tools

    q = query.lower()
    hits: list = []
    for t in list_tools(include_stdlib=stdlib):
        searchable = t.name.lower()
        for p in t.parameters:
            searchable += " " + p.name.lower()
        if q in searchable:
            hits.append(t)

    if not hits:
        click.echo(f"No tools matching '{query}'.")
        if not stdlib:
            click.echo("Tip: add --stdlib to include built-in tools.")
        return

    by_source: dict[str, list] = {}
    for t in hits:
        by_source.setdefault(t.source, []).append(t)

    click.echo(f"{len(hits)} tool(s) matching '{query}':\n")
    for src, sigs in sorted(by_source.items()):
        label = "stdlib (built-in)" if src == "stdlib" else f"{src}.spl"
        click.echo(f"  [{label}]")
        for t in sigs:
            click.echo(f"    CALL {t.spl_signature()}")
        click.echo()


@cmd_tool_api.command("remove", short_help="Remove a library from the registry.")
@click.argument("name", metavar="NAME")
def cmd_tool_api_remove(name):
    """Remove a registered TOOL_API library by its registry name (no .spl suffix).

    \b
    Example:
        spl3 tool-api remove finance
    """
    from spl3.tool_api_registry import remove
    if remove(name):
        click.echo(f"✓  Removed TOOL_API library: {name}")
    else:
        click.echo(f"Not found: no library named '{name}' in the registry.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
