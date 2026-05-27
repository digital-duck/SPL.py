"""SPL 3.0 TOOL_API library registry.

The registry serves two distinct roles:

**Runtime role** — load tool implementations into the executor before each run.
Libraries are ``.spl`` files in ``~/.spl/tool_apis/`` that contain
``CREATE TOOL_API`` blocks.  ``load_all_into_executor()`` is called automatically
from ``SPL3Executor.execute_program()``.

**Generation role** — tell the LLM what already exists so it doesn't regenerate
tools that are already available.  ``available_tools_prompt_block()`` enumerates
stdlib tools (from ``spl/tools.py``) plus all registered library tools, and
formats them as a prompt section that ``text2spl`` and ``mmd2spl`` inject before
asking the LLM to generate new code.

Storage: ``~/.spl/tool_apis/``

Promotion workflow::

    spl3 tool-api promote my_recipe.spl --name finance_tools
    # → copies to ~/.spl/tool_apis/finance_tools.spl

    spl3 tool-api list                    # file-level view
    spl3 tool-api list --tools            # function-level view

    # At executor init time, load_all_into_executor() is called automatically
    # to make library tools available to every CALL statement.

Design note
-----------
Promoted libraries are loaded into the executor's per-instance ``FunctionRegistry``
via ``executor._load_tool_apis()``.  They do NOT touch ``_GLOBAL_TOOLS`` (which is
snapshotted at import time) — the per-executor injection is intentional so that
each run context is isolated.

Load order (later entries win on name collision):
  1. ``~/.spl/tool_apis/`` library files
  2. Inline ``CREATE TOOL_API`` blocks in the current ``.spl`` file

This means an inline definition always overrides a library definition — local wins.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass   # avoid circular imports; executor type hint omitted

_log = logging.getLogger("spl3.tool_api_registry")

# Default library directory
_REGISTRY_DIR = Path.home() / ".spl" / "tool_apis"


# ── Tool catalog data model ───────────────────────────────────────────────────

@dataclass
class ToolParam:
    """One parameter of a registered TOOL_API function."""
    name: str
    param_type: str = "TEXT"   # TEXT | INTEGER | FLOAT | BOOL


@dataclass
class ToolSignature:
    """Metadata for one registered TOOL_API function.

    Attributes:
        name:        The function name as used in ``CALL <name>(...)``.
        parameters:  Ordered list of parameters.
        return_type: SPL type of the return value (almost always ``TEXT``).
        source:      ``"stdlib"`` for built-in tools, otherwise the library
                     stem name (e.g. ``"finance"`` for ``finance.spl``).
        source_file: Absolute path to the ``.spl`` file, or ``None`` for stdlib.
        python_body: The raw Python implementation (empty for stdlib tools).
    """
    name: str
    parameters: list[ToolParam] = field(default_factory=list)
    return_type: str = "TEXT"
    source: str = "stdlib"
    source_file: str | None = None
    python_body: str = ""

    def spl_signature(self) -> str:
        """Return a terse CALL-style signature for use in prompts.

        Example: ``fetch_ohlcv(@ticker TEXT, @days TEXT) RETURNS TEXT``
        """
        if self.parameters:
            params = ", ".join(
                f"@{p.name} {p.param_type}" for p in self.parameters
            )
        else:
            params = ""
        return f"{self.name}({params}) RETURNS {self.return_type}"


# ── Public helpers — file-level ───────────────────────────────────────────────

def registry_dir() -> Path:
    """Return (and create if needed) the TOOL_API library directory."""
    _REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    return _REGISTRY_DIR


def list_libraries() -> list[dict]:
    """Return file-level metadata for all registered TOOL_API library files.

    Returns a list of dicts with keys: ``name``, ``path``, ``size``,
    ``tool_count``, ``tools`` (list of ToolSignature for the file).
    """
    d = _REGISTRY_DIR
    if not d.exists():
        return []

    result: list[dict] = []
    for f in sorted(d.glob("*.spl")):
        tools = _parse_tools_from_file(f)
        result.append({
            "name":       f.stem,
            "path":       str(f),
            "size":       f.stat().st_size,
            "tool_count": len(tools),
            "tools":      tools,
        })
    return result


def promote(source_path: str | Path, name: str | None = None) -> Path:
    """Promote a ``.spl`` file containing ``CREATE TOOL_API`` blocks to the registry.

    The file is copied to ``~/.spl/tool_apis/<name>.spl``.

    Args:
        source_path: Path to the source ``.spl`` file.
        name:        Registry name (stem, no extension). Defaults to the source stem.

    Returns:
        The destination ``Path`` after copying.

    Raises:
        FileNotFoundError: if ``source_path`` does not exist.
        ValueError: if the source file contains no ``CREATE TOOL_API`` blocks.
    """
    src = Path(source_path)
    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    text = src.read_text(encoding="utf-8")
    if "CREATE TOOL_API" not in text.upper():
        raise ValueError(
            f"No CREATE TOOL_API blocks found in {src.name}. "
            f"Only files with TOOL_API definitions can be promoted."
        )

    dest_name = name or src.stem
    dest = registry_dir() / f"{dest_name}.spl"
    dest.write_text(text, encoding="utf-8")
    _log.info("Promoted %s → %s", source_path, dest)
    return dest


def remove(name: str) -> bool:
    """Remove a library from the registry by name (stem).

    Returns ``True`` if removed, ``False`` if not found.
    """
    target = _REGISTRY_DIR / f"{name}.spl"
    if target.exists():
        target.unlink()
        _log.info("Removed TOOL_API library: %s", name)
        return True
    return False


# ── Public helpers — tool-level catalog ──────────────────────────────────────

def list_tools(include_stdlib: bool = True) -> list[ToolSignature]:
    """Return all known TOOL_API functions: stdlib + all registered libraries.

    This is the **tool-level** catalog used by:
    - ``available_tools_prompt_block()`` — to tell the LLM what already exists
    - ``spl3 tool-api list --tools`` — for human inspection

    Args:
        include_stdlib: Whether to include the built-in stdlib tools
                        (``web_search``, ``http_get``, etc.).  Default ``True``.

    Returns:
        List of :class:`ToolSignature`, stdlib tools first, then library tools
        sorted by library name then function name.
    """
    tools: list[ToolSignature] = []

    # 1. Stdlib tools — Python functions registered via @spl_tool
    if include_stdlib:
        tools.extend(_stdlib_tools())

    # 2. Library tools — parsed from ~/.spl/tool_apis/*.spl
    d = _REGISTRY_DIR
    if d.exists():
        for lib_file in sorted(d.glob("*.spl")):
            for sig in _parse_tools_from_file(lib_file):
                tools.append(sig)

    return tools


def available_tools_prompt_block(include_stdlib: bool = True) -> str:
    """Build a formatted prompt section listing all available TOOL_API tools.

    This is injected into ``text2spl`` and ``mmd2spl`` system prompts so the
    LLM knows what already exists and can use ``CALL`` directly instead of
    regenerating a ``CREATE TOOL_API`` block.

    The rule injected with the block:
        *If the operation is covered, use ``CALL`` directly.
        Only emit ``CREATE TOOL_API`` for operations NOT in this list.*

    Args:
        include_stdlib: Whether to include stdlib tools (default ``True``).

    Returns:
        A formatted multi-line string ready for prompt injection, or an empty
        string if no tools are registered and stdlib is excluded.
    """
    tools = list_tools(include_stdlib=include_stdlib)
    if not tools:
        return ""

    stdlib_tools = [t for t in tools if t.source == "stdlib"]
    lib_tools    = [t for t in tools if t.source != "stdlib"]

    lines = [
        "== AVAILABLE TOOL_API FUNCTIONS ==",
        "",
        "The following deterministic tools already exist. When you need one of",
        "these operations, use CALL directly — do NOT generate a new CREATE TOOL_API.",
        "Only generate CREATE TOOL_API for operations NOT listed here.",
        "",
    ]

    if stdlib_tools:
        lines.append("Stdlib tools (built-in, always available):")
        for t in stdlib_tools:
            lines.append(f"  CALL {t.spl_signature()}")
        lines.append("")

    if lib_tools:
        # Group by source library
        by_lib: dict[str, list[ToolSignature]] = {}
        for t in lib_tools:
            by_lib.setdefault(t.source, []).append(t)

        lines.append("User library tools (~/.spl/tool_apis/):")
        for lib_name, lib_sigs in sorted(by_lib.items()):
            lines.append(f"  # library: {lib_name}.spl")
            for t in lib_sigs:
                lines.append(f"  CALL {t.spl_signature()}")
        lines.append("")

    return "\n".join(lines)


# ── Runtime loading ───────────────────────────────────────────────────────────

def load_all_into_executor(executor) -> int:
    """Load all registered TOOL_API libraries into an executor instance.

    Called automatically from ``SPL3Executor.execute_program()`` before the
    workflow runs.  Libraries registered later (via ``promote``) are available
    on the *next* run — not retroactively in an already-running executor.

    Returns the number of library files loaded (not the number of tools).
    """
    d = _REGISTRY_DIR
    if not d.exists():
        return 0

    from spl.lexer import Lexer
    from spl3.parser import SPL3Parser

    count = 0
    for lib_file in sorted(d.glob("*.spl")):
        try:
            src = lib_file.read_text(encoding="utf-8")
            tokens = Lexer(src).tokenize()
            program = SPL3Parser(tokens).parse()
            executor._load_tool_apis(program)
            count += 1
            _log.debug("Loaded TOOL_API library: %s", lib_file.name)
        except Exception as exc:
            _log.warning(
                "Failed to load TOOL_API library %s: %s — skipping", lib_file.name, exc
            )

    return count


# ── Private helpers ───────────────────────────────────────────────────────────

def _parse_tools_from_file(lib_file: Path) -> list[ToolSignature]:
    """Parse all ToolAPINode definitions from a single .spl library file."""
    try:
        from spl.lexer import Lexer
        from spl3.parser import SPL3Parser
        from spl3.ast_nodes import ToolAPINode

        src = lib_file.read_text(encoding="utf-8")
        tokens = Lexer(src).tokenize()
        program = SPL3Parser(tokens).parse()

        result = []
        for stmt in program.statements:
            if not isinstance(stmt, ToolAPINode):
                continue
            params = [
                ToolParam(
                    name=p.name,
                    param_type=getattr(p, "param_type", None) or "TEXT",
                )
                for p in (stmt.parameters or [])
            ]
            result.append(ToolSignature(
                name=stmt.name,
                parameters=params,
                return_type=getattr(stmt, "return_type", None) or "TEXT",
                source=lib_file.stem,
                source_file=str(lib_file),
                python_body=stmt.python_body or "",
            ))
        return result
    except Exception as exc:
        _log.warning("Could not index library %s: %s", lib_file.name, exc)
        return []


def _stdlib_tools() -> list[ToolSignature]:
    """Return ToolSignature entries for all stdlib tools from spl/tools.py."""
    import inspect

    try:
        from spl.tools import get_global_tools
        stdlib = get_global_tools()
    except Exception:
        return []

    result = []
    for name, fn in sorted(stdlib.items()):
        try:
            sig = inspect.signature(fn)
            params = [
                ToolParam(name=pname, param_type="TEXT")
                for pname, p in sig.parameters.items()
                if pname not in ("self", "cls", "kwargs", "args")
                and p.kind not in (
                    inspect.Parameter.VAR_POSITIONAL,
                    inspect.Parameter.VAR_KEYWORD,
                )
            ]
        except (ValueError, TypeError):
            params = []

        result.append(ToolSignature(
            name=name,
            parameters=params,
            return_type="TEXT",
            source="stdlib",
            source_file=None,
            python_body="",
        ))
    return result
