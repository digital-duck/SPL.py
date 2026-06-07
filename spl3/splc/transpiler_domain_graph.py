"""splc — generalized "domain concept-graph" → notebook transpiler engine.

This is the parameterized core that `transpiler_linalg.py` (the
`python/linalg` target) and `transpiler_intro_geometry.py` (the
`python/intro_geometry` target) both subclass. It captures everything that
was domain-*agnostic* in the original linalg-only transpiler — the SPL → cell
construct mapping, expression rendering, loop-bound inference, IPython-name
remapping, the content cache / LLM-call / timing helper templates — and
parameterizes everything that was domain-*specific* via a `DomainConfig`:
which graph module to import, which env var locates it, which function
returns the curriculum's primitive set, and which symbolic verifiers a
`CALL` can dispatch to.

Construct mapping (SPL → notebook cell) — identical for every domain target:
  WORKFLOW … DO … END     → markdown header + setup code cell
  CREATE FUNCTION         → prompt constant hoisted into setup cell
  GENERATE fn(…) INTO @v  → code cell calling _llm_call(prompt)
  CALL proc(…) INTO @v    → code cell calling the Python function
  SOLVE @v TYPE := expr   → code cell: v = expr  (@@var@@ → var)
  ASSERT expr             → code cell: assert bool(expr) with OTHERWISE handler
  EVALUATE @v WHEN …      → code cell: if/elif/else
  WHILE cond DO           → code cell: while loop
  @v := expr              → code cell: v = expr
  COMMIT @v               → code cell: write output + print
  LOGGING msg             → code cell: print(msg)

DODA principle:
  The .spl file is the logical view; the notebook is the physical artifact for
  a `python/<domain>` target. "Changing domain = swap <domain>_graph.py" is
  the thesis this module makes literally true: the engine never names a
  domain library, only a `DomainConfig` does.
"""

from __future__ import annotations

import json
import re
import textwrap
from dataclasses import dataclass, field
from typing import Any

from spl.ast_nodes import (
    AssignmentStatement,
    BinaryOp,
    CallStatement,
    CommitStatement,
    CompoundCondition,
    CreateFunctionStatement,
    EvaluateStatement,
    FStringLiteral,
    GenerateIntoStatement,
    Literal,
    LoggingStatement,
    NamedArg,
    ParamRef,
    SemanticCondition,
    WhileStatement,
    WorkflowStatement,
)
from spl3.ast_nodes import (
    AssertStatement,
    NoneLiteral,
    SolveStatement,
    UnaryOp,
)


# ---------------------------------------------------------------------------
# Domain configuration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VerifierSpec:
    """One symbolic verifier a `CALL <call_name>(@section) INTO @v` can reach.

    `call_name` is the SPL-level procedure name (what authors write in
    `CALL verify_math(...)` / `CALL verify_geometry(...)`); `helper_name` is
    the Python "well-known helper" the transpiler routes that call to
    (`_verify_math`, `_verify_geometry`, ...); `helper_source` is the full
    `def {helper_name}(section: str) -> str: ...` definition emitted into the
    setup cell, returning `"pass"` or a `"fail: ..."` description that an
    `EVALUATE @check WHEN contains("fail")` can branch on.
    """

    call_name: str
    helper_name: str
    helper_source: str


@dataclass(frozen=True)
class DomainConfig:
    """Everything that distinguishes one `python/<domain>` target from another.

    The engine (`DomainGraphTranspiler`) never hardcodes a graph-module name,
    an env var, a primitives accessor, or a verifier — it only knows how to
    read these out of a `DomainConfig`. A new domain target is therefore just
    a new `DomainConfig` plus a one-line subclass (see `LinalgTranspiler` /
    `IntroGeometryTranspiler`).
    """

    target: str                  # splc --lang value, e.g. "python/linalg"
    graph_module: str            # importable module name, e.g. "linalg_graph"
    graph_dir_env: str           # env var that locates {graph_module}.py, e.g. "LINALG_GRAPH_DIR"
    framework: str               # short label used in notebook metadata, e.g. "linalg"
    primitives_fn: str = "both_radical_primitives"
    verifiers: tuple[VerifierSpec, ...] = field(default_factory=tuple)

    @property
    def graph_file(self) -> str:
        return f"{self.graph_module}.py"


# ---------------------------------------------------------------------------
# Notebook format helpers (domain-agnostic)
# ---------------------------------------------------------------------------

def _code_cell(source: str, metadata: dict | None = None) -> dict[str, Any]:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": metadata or {},
        "outputs": [],
        "source": _source_lines(source),
    }


def _markdown_cell(source: str, metadata: dict | None = None) -> dict[str, Any]:
    return {
        "cell_type": "markdown",
        "metadata": metadata or {},
        "source": _source_lines(source),
    }


def _source_lines(text: str) -> list[str]:
    """Split source into a list of lines (each ending with \\n, last without)."""
    lines = text.rstrip("\n").split("\n")
    return [ln + "\n" for ln in lines[:-1]] + [lines[-1]]


def _notebook(cells: list[dict], config: DomainConfig) -> dict[str, Any]:
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3 (ipykernel)",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.11.0",
            },
            "splc": {
                "target": config.target,
                "domain_library": config.graph_file,
            },
        },
        "cells": cells,
    }


# ---------------------------------------------------------------------------
# Setup-cell template — every `{{PLACEHOLDER}}` is filled from a DomainConfig;
# `{param_defaults}` and `{verifier_defs}` are filled per-transpile (the
# former depends on the specific WORKFLOW's INPUT/OUTPUT declarations, the
# latter is generated from config.verifiers — see `_setup_cell`).
#
# Doubled braces are deliberate: this template is filled with `.replace()`,
# not `.format()`, because the emitted Python source is full of literal `{`/
# `}` (f-strings, dict literals, JSON) that `.format()` would choke on or
# mis-substitute — the same reason `_SETUP_TEMPLATE` in the original
# linalg-only transpiler used `.replace("{param_defaults}", ...)`.
# ---------------------------------------------------------------------------

_SETUP_TEMPLATE = """\
# ── {{TARGET}} target setup — generated by splc ──────────────────────────────
import sys, os, json, time
from pathlib import Path

# Locate {{GRAPH_FILE}} (cookbook recipe directory or current dir)
_SEARCH = [
    Path(__file__).parent if "__file__" in dir() else Path("."),
    Path(os.environ.get("{{GRAPH_DIR_ENV}}", ".")),
    Path("."),
]
for _p in _SEARCH:
    _p = _p.resolve()
    if (_p / "{{GRAPH_FILE}}").exists():
        sys.path.insert(0, str(_p))
        break
import {{GRAPH_MODULE}} as dg
from {{GRAPH_MODULE}} import (
    build, acyclic, reducible, minimal, ancestors, restrict,
    productivity_order, in_graph, applications_of, new_primitives,
    first_radical_primitives, both_radical_primitives,
    concept_names, primitive_names,
    gap, learning_path,
)
from style_profiles import style_instruction, get_style_profile, available_styles

# ── SPL runtime config lookup — env var, then ~/.spl/config, then default
# (same precedence `spl3 configure` documents for "SPL runtime defaults";
# the notebook is a standalone artifact so it re-reads the dotenv-format
# file directly rather than importing the spl3 CLI) ──────────────────────────
def _spl_config(key: str, default: str) -> str:
    if key in os.environ:
        return os.environ[key]
    _cfg = Path.home() / ".spl" / "config"
    if _cfg.exists():
        for _line in _cfg.read_text(encoding="utf-8").splitlines():
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _, _v = _line.partition("=")
                if _k.strip() == key:
                    return _v.strip().strip('"').strip("'")
    return default

# ── LLM helper (configure SPL_MODEL / SPL_LLM_TIMEOUT / SPL_OLLAMA_URL, or
# replace with your adapter) — calls Ollama's OpenAI-compatible HTTP endpoint
# directly (stream=False), the same way spl/adapters/ollama.py's OllamaAdapter
# does. Earlier this shelled out to the interactive `ollama run <model>` CLI —
# but that CLI streams a live "Thinking..." status line to stdout using raw
# ANSI cursor-control escapes (`\\x1b[9D\\x1b[K`, ...) to overwrite it in place,
# and `subprocess.run(capture_output=True)` captures those escapes verbatim
# into the "response", contaminating every GENERATE result, the cache, and the
# committed textbook with ~2000 stray control-character sequences. The HTTP
# API talks to the same Ollama daemon but returns clean structured JSON. ──────
def _llm_call(prompt: str, model: str | None = None) -> str:
    import urllib.request
    _m = model or os.environ.get("SPL_MODEL", "llama3.2")
    # Local models (esp. 8B+ on consumer GPUs) can take well over a minute per
    # call, and refine-loop prompts re-send the full prior section as context —
    # default generously and let SPL_LLM_TIMEOUT override per deployment.
    _timeout = int(os.environ.get("SPL_LLM_TIMEOUT", "600"))
    _url = os.environ.get("SPL_OLLAMA_URL", "http://localhost:11434") + "/v1/chat/completions"
    _payload = json.dumps({
        "model": _m,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }).encode("utf-8")
    _req = urllib.request.Request(
        _url, data=_payload, method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(_req, timeout=_timeout) as _resp:
        _data = json.loads(_resp.read().decode("utf-8"))
    return _data["choices"][0]["message"]["content"].strip()

# ── Layer 2 content cache (write-once, content-addressed — same backend and
# semantics as spl/stdlib.py's cache_get/cache_put @spl_tools; reimplemented
# here directly against spl3.cache because this notebook is a standalone
# artifact that calls the cache without going through the SPL executor) ──────
def cache_get(concept: str, rubric_version: str = "v1") -> str:
    \"\"\"Returns cached content on a hit, or the sentinel string "miss".\"\"\"
    try:
        from spl3.cache import get_content_cache
        entry = get_content_cache().get(
            concept=concept, params={}, rubric_version=rubric_version, dep_hashes={},
        )
        return entry.content if entry is not None else "miss"
    except Exception:
        return "miss"

def cache_put(concept: str, content: str, rubric_version: str = "v1") -> str:
    \"\"\"Stores generated+verified content (write-once, immutable); returns the cache key.\"\"\"
    try:
        from spl3.cache import get_content_cache
        entry = get_content_cache().put(
            concept=concept, content=content, provenance="machine_generated",
            params={}, rubric_version=rubric_version, dep_hashes={},
        )
        return entry.key
    except Exception as exc:
        return f"cache_put error: {exc}"

# ── Domain verifier helpers — one well-known helper per CALL target this
# .spl source can dispatch to (declared via DomainConfig.verifiers; see
# {{TARGET}}'s preset). Each returns 'pass' or a 'fail: ...' description an
# EVALUATE @check WHEN contains("fail") branch can act on. ───────────────────
{verifier_defs}

# ── Timing helpers ────────────────────────────────────────────────────────────
# Bare-name wrappers around time.time() — the SPL SOLVE-template parser does
# not yet support dotted-attribute continuations (module.attr(...)), so the
# .spl source calls these instead of `time.time()` directly. Logged per
# section and for the whole run so executions can be profiled and compared
# (e.g. across distributed workers).
def _now() -> float:
    return time.time()

def _elapsed(start: float) -> float:
    return time.time() - start

# ── Workflow parameters (override before running or use papermill) ────────────
{param_defaults}
"""

_HEADER_TEMPLATE = """\
# {name}

**Generated by** `splc --lang {target}`
**Domain library:** `{graph_file}`
**DODA note:** The source `.spl` file is the logical view; this notebook is the physical artifact for the `{target}` domain target.

## Inputs

{input_table}
"""


# ---------------------------------------------------------------------------
# Transpiler engine
# ---------------------------------------------------------------------------

class DomainGraphTranspiler:
    """Deterministic SPL 3.0 → `python/<domain>` .ipynb transpiler engine.

    Subclass once per domain target with a fixed `DomainConfig` — see
    `LinalgTranspiler` (`python/linalg`) and `IntroGeometryTranspiler`
    (`python/intro_geometry`) for the two-line pattern. Everything below is
    domain-agnostic: the SPL → cell construct mapping, expression rendering,
    loop-bound inference, and the content-cache / LLM-call / timing helpers
    threaded through every domain's setup cell are identical regardless of
    which concept graph or verifier set a recipe plugs in.

    Usage::

        from spl.lexer import Lexer
        from spl3.parser import SPL3Parser
        from spl3.splc.transpiler_linalg import LinalgTranspiler
        from pathlib import Path

        tokens = Lexer(src).tokenize()
        program = SPL3Parser(tokens).parse()
        nb_json = LinalgTranspiler("build_micro_textbook", spl_dir=Path(".")).transpile(program)
        Path("out.ipynb").write_text(nb_json)
    """

    def __init__(self, recipe_name: str, config: DomainConfig, spl_dir=None):
        self.recipe_name = recipe_name
        self.config = config
        self.spl_dir = spl_dir
        self.prompts: dict[str, str] = {}
        self.fn_params: dict[str, list] = {}
        # var name -> declared OUTPUT type (e.g. "textbook" -> "TEXT"); lets
        # _commit_cell pick a format that matches the content rather than
        # always wrapping the value in JSON — see _commit_cell.
        self.output_types: dict[str, str] = {}
        # SPL CALL name -> Python helper name, derived from config.verifiers
        # plus the always-available `run_python` kernel-code passthrough.
        self._call_dispatch: dict[str, str] = {
            v.call_name: v.helper_name for v in config.verifiers
        }

    # ── Public entry point ────────────────────────────────────────────────────

    def transpile(self, program) -> str:
        """Return .ipynb JSON string."""
        # Pass 1: collect CREATE FUNCTION definitions
        for stmt in program.statements:
            if isinstance(stmt, CreateFunctionStatement):
                self.prompts[stmt.name] = stmt.body
                self.fn_params[stmt.name] = stmt.parameters

        # Find the main workflow
        workflows = [s for s in program.statements if isinstance(s, WorkflowStatement)]
        if not workflows:
            raise ValueError("No WORKFLOW statement found in SPL source")
        main_wf = workflows[-1]
        self.output_types = {p.name: (p.param_type or "TEXT").upper() for p in main_wf.outputs}

        cells: list[dict] = []
        cells.append(self._header_cell(main_wf))
        cells.append(self._setup_cell(main_wf))
        if self.prompts:
            cells.append(self._prompts_cell())

        for stmt in main_wf.body:
            cells.extend(self._stmt_to_cells(stmt))

        return json.dumps(_notebook(cells, self.config), indent=2, ensure_ascii=False)

    # ── Cell builders ─────────────────────────────────────────────────────────

    def _header_cell(self, wf: WorkflowStatement) -> dict:
        rows = ["| Parameter | Type | Description |", "|-----------|------|-------------|"]
        for p in wf.inputs:
            rows.append(f"| `@{p.name}` | `{p.param_type or 'TEXT'}` | — |")
        table = "\n".join(rows) if wf.inputs else "_No inputs declared._"
        src = _HEADER_TEMPLATE.format(
            name=wf.name.replace("_", " ").title(),
            target=self.config.target,
            graph_file=self.config.graph_file,
            input_table=table,
        )
        return _markdown_cell(src)

    def _setup_cell(self, wf: WorkflowStatement) -> dict:
        param_lines: list[str] = []
        for p in wf.inputs:
            typ = (p.param_type or "TEXT").upper()
            # Use the SPL DEFAULT value when present; fall back to sensible type default
            if p.default_value is not None:
                default = self._expr_py(p.default_value)
            elif typ in ("INT", "INTEGER"):
                default = "1"
            elif typ in ("FLOAT", "NUMBER"):
                default = "1.0"
            elif typ in ("SET", "LIST"):
                default = "[]"
            else:
                default = f'"{p.name.lower()}"'
            # Scalar params are overridable via env var / ~/.spl/config (same
            # _spl_config precedence as SPL_WHILE_MAX_ITER) — e.g. set TARGET
            # to a concept near the primitives to run a small sub-graph smoke
            # test before committing to the full curriculum. nbconvert has no
            # papermill-style parameter injection, so this is the lightest way
            # to stage validation without editing the notebook.
            env_key = p.name.upper()
            if typ in ("INT", "INTEGER"):
                param_lines.append(f"{p.name} = int(_spl_config('{env_key}', str({default})))  # {typ}")
            elif typ in ("FLOAT", "NUMBER"):
                param_lines.append(f"{p.name} = float(_spl_config('{env_key}', str({default})))  # {typ}")
            elif typ in ("SET", "LIST"):
                param_lines.append(f"{p.name} = {default}  # {typ}")
            else:
                param_lines.append(f"{p.name} = _spl_config('{env_key}', {default})  # {typ}")
        # Initialise OUTPUT variables
        for p in wf.outputs:
            typ = (p.param_type or "TEXT").upper()
            if typ in ("LIST", "SET"):
                param_lines.append(f"{p.name} = []")
            elif typ in ("INT", "INTEGER"):
                param_lines.append(f"{p.name} = 0")
            elif typ in ("FLOAT", "NUMBER"):
                param_lines.append(f"{p.name} = 0.0")
            else:
                param_lines.append(f'{p.name} = ""')

        # Build the concept graph once in setup
        param_lines.append("")
        param_lines.append(f"# Pre-build the {self.config.graph_module} concept graph (reused by all SOLVE/ASSERT cells)")
        param_lines.append("graph = dg.build()")
        param_lines.append(f"primitives = dg.{self.config.primitives_fn}()")
        param_lines.append(
            f'print(f"{self.config.graph_module} loaded: {{graph.number_of_nodes()}} nodes, '
            '{graph.number_of_edges()} edges")'
        )

        src = (
            _SETUP_TEMPLATE
            .replace("{{TARGET}}", self.config.target)
            .replace("{{GRAPH_FILE}}", self.config.graph_file)
            .replace("{{GRAPH_MODULE}}", self.config.graph_module)
            .replace("{{GRAPH_DIR_ENV}}", self.config.graph_dir_env)
            .replace("{verifier_defs}", self._verifier_defs_source())
            .replace("{param_defaults}", "\n".join(param_lines))
        )
        return _code_cell(src)

    def _verifier_defs_source(self) -> str:
        """Render every domain verifier's helper definition for the setup cell.

        Falls back to a one-line note when a domain declares no verifiers —
        a recipe is free to skip symbolic verification entirely (e.g. a pure
        Q&A workflow with no `CALL verify_*` steps).
        """
        if not self.config.verifiers:
            return "# (this domain target declares no symbolic verifiers)"
        return "\n\n".join(v.helper_source.rstrip("\n") for v in self.config.verifiers)

    def _prompts_cell(self) -> dict:
        lines = ["# ── Prompt templates (mirrors CREATE FUNCTION blocks in .spl) ────────────"]
        for name, body in self.prompts.items():
            const = name.upper() + "_PROMPT"
            body_clean = textwrap.dedent(body).strip("\n")
            lines.append(f'\n{const} = """\\\n{body_clean}\n"""')
        return _code_cell("\n".join(lines))

    # ── Statement dispatcher ──────────────────────────────────────────────────

    def _stmt_to_cells(self, stmt) -> list[dict]:
        if isinstance(stmt, SolveStatement):
            return [self._solve_cell(stmt)]
        if isinstance(stmt, AssertStatement):
            return [self._assert_cell(stmt)]
        if isinstance(stmt, GenerateIntoStatement):
            return [self._generate_cell(stmt)]
        if isinstance(stmt, CallStatement):
            return [self._call_cell(stmt)]
        if isinstance(stmt, AssignmentStatement):
            return [self._assignment_cell(stmt)]
        if isinstance(stmt, EvaluateStatement):
            return [self._evaluate_cell(stmt)]
        if isinstance(stmt, WhileStatement):
            return [self._while_cell(stmt)]
        if isinstance(stmt, CommitStatement):
            return [self._commit_cell(stmt)]
        if isinstance(stmt, LoggingStatement):
            return [self._logging_cell(stmt)]
        # Unsupported — emit a comment cell
        type_name = type(stmt).__name__
        return [_code_cell(f"# TODO: {type_name} not yet emitted by {self.config.target} transpiler")]

    # ── Per-construct cell emitters ───────────────────────────────────────────

    def _solve_cell(self, stmt: SolveStatement) -> dict:
        expr = self._subst_markers(stmt.python_template)
        typ = f" {stmt.target_type}" if stmt.target_type else ""
        spl_display = _markers_to_at(stmt.python_template)
        var = self._key(stmt.target_variable)
        spl_comment = f"# SPL: SOLVE @{stmt.target_variable}{typ} := {spl_display}"
        code = (
            f"{spl_comment}\n"
            f"{var} = {expr}\n"
            f"print(f'@{var} =', {var})"
        )
        return _code_cell(code, metadata={"tags": ["solve"]})

    def _assert_cell(self, stmt: AssertStatement) -> dict:
        expr = self._subst_markers(stmt.python_template)
        spl_comment = f"# SPL: ASSERT {_markers_to_at(stmt.python_template)}"
        lines = [spl_comment, f"_assert_result = bool({expr})"]
        if stmt.otherwise_body:
            otherwise_lines = self._body_to_python(stmt.otherwise_body, indent="    ")
            lines += [
                "if not _assert_result:",
                f'    print(f"ASSERT failed: {expr!r} → executing OTHERWISE")',
            ]
            lines.extend(otherwise_lines)
            lines += [
                "else:",
                f'    print(f"✓ ASSERT {expr}")',
            ]
        else:
            lines += [
                "if not _assert_result:",
                f'    raise AssertionError(f"ASSERT failed: {expr!r}")',
                "else:",
                f'    print(f"✓ ASSERT {expr}")',
            ]
        return _code_cell("\n".join(lines), metadata={"tags": ["assert"]})

    def _generate_cell(self, stmt: GenerateIntoStatement) -> dict:
        gc = stmt.generate_clause
        fn = gc.function_name
        args_spl = [self._spl_arg(a) for a in gc.arguments]
        var = self._key(stmt.target_variable)

        prompt_const = fn.upper() + "_PROMPT"
        if fn in self.prompts:
            fn_params = self.fn_params.get(fn, [])
            parts: list[str] = []
            for idx, a in enumerate(gc.arguments):
                if isinstance(a, NamedArg):
                    parts.append(f"{a.name}={self._expr_py(a.value)}")
                else:
                    # Use the function's declared parameter name as the keyword (positional-by-position)
                    param_name = fn_params[idx].name if idx < len(fn_params) else None
                    val_py = self._expr_py(a)
                    if param_name:
                        parts.append(f"{param_name}={val_py}")
                    else:
                        parts.append(val_py)
            fmt_args = ", ".join(parts)
            prompt_expr = f"{prompt_const}.format({fmt_args})" if fmt_args else prompt_const
        else:
            prompt_expr = (
                f'"GENERATE {fn}({", ".join(args_spl)})"  '
                f"# ← replace with actual prompt for {fn}"
            )

        spl_comment = f"# SPL: GENERATE {fn}({', '.join(args_spl)}) INTO @{stmt.target_variable}"
        code = (
            f"{spl_comment}\n"
            f"_prompt = {prompt_expr}\n"
            f"{var} = _llm_call(_prompt)\n"
            f"print(f'@{var}:', {var}[:200] if isinstance({var}, str) else {var})"
        )
        return _code_cell(code, metadata={"tags": ["generate"]})

    def _call_cell(self, stmt: CallStatement) -> dict:
        fn = stmt.procedure_name
        args_spl = [self._spl_arg(a) for a in stmt.arguments]
        args_py  = [self._expr_py(a) for a in stmt.arguments]

        spl_comment = f"# SPL: CALL {fn}({', '.join(args_spl)})"
        if stmt.target_variable:
            spl_comment += f" INTO @{stmt.target_variable}"

        # Well-known helpers — domain verifiers come from DomainConfig.verifiers
        # (see self._call_dispatch, built in __init__); run_python is the one
        # cross-domain passthrough every target supports (kernel-mode recipes).
        if fn in self._call_dispatch:
            helper = self._call_dispatch[fn]
            py_call = f"{helper}({', '.join(args_py)})"
        elif fn == "run_python":
            # CALL run_python('code') INTO @var — emit the Python code as a cell
            code_arg = args_py[0] if args_py else '""'
            py_call = f"eval(compile({code_arg}, '<spl_run_python>', 'exec'))"
        else:
            py_call = f"{fn}({', '.join(args_py)})"

        result_var = self._key(stmt.target_variable) if stmt.target_variable else "_result"
        code = (
            f"{spl_comment}\n"
            f"{result_var} = {py_call}\n"
            f"print(f'@{result_var}:', {result_var})"
        )
        return _code_cell(code, metadata={"tags": ["call"]})

    def _assignment_cell(self, stmt: AssignmentStatement) -> dict:
        var = self._key(stmt.variable)
        expr = self._expr_py(stmt.expression)
        spl_comment = f"# SPL: @{var} := {self._spl_expr(stmt.expression)}"
        code = f"{spl_comment}\n{var} = {expr}\nprint(f'@{var} =', {var})"
        return _code_cell(code)

    def _evaluate_cell(self, stmt: EvaluateStatement) -> dict:
        var = self._expr_py(stmt.expression)
        lines = [f"# SPL: EVALUATE {self._spl_expr(stmt.expression)}"]
        for i, wc in enumerate(stmt.when_clauses):
            kw = "if" if i == 0 else "elif"
            cond_str = self._render_when_condition(wc.condition, var)
            lines.append(f"{kw} {cond_str}:")
            inner = self._body_to_python(wc.statements, indent="    ")
            if inner:
                lines.extend(inner)
            else:
                lines.append("    pass")
        if stmt.else_statements:
            lines.append("else:")
            inner = self._body_to_python(stmt.else_statements, indent="    ")
            lines.extend(inner if inner else ["    pass"])
        return _code_cell("\n".join(lines), metadata={"tags": ["evaluate"]})

    def _loop_bound_expr(self, cond) -> str | None:
        """Detect `@i < @bound` / `@i <= @bound` where @bound is a plain
        variable reference (e.g. `@_i < @order_len`) and return the Python
        expression for @bound.

        This lets the generated safety cap track the loop's actual,
        runtime-computed length instead of guessing a constant — the bug
        this guards against: `_while_iter < 10` silently truncated a
        13-section curriculum to 10 sections with no error, because the
        old fallback never looked at what the loop was actually counting
        toward. Literal bounds (`@i < 5`) are deliberate and left alone;
        compound/semantic conditions (quality-gate loops) return None and
        fall back to the configurable `SPL_WHILE_MAX_ITER` safety net.
        """
        if isinstance(cond, (CompoundCondition, SemanticCondition)):
            return None
        if hasattr(cond, "left") and hasattr(cond, "operator") and hasattr(cond, "right"):
            if cond.operator in ("<", "<="):
                right = cond.right
                if isinstance(right, ParamRef):
                    return self._key(right.name)
        return None

    def _while_cell(self, stmt: WhileStatement) -> dict:
        cond = self._render_condition(stmt.condition)
        bound = self._loop_bound_expr(stmt.condition)
        if stmt.max_iterations:
            max_iter = str(stmt.max_iterations)
        elif bound:
            # Naturally-bounded loop — cap = the real bound (+1 margin for
            # loop-counter mechanics), not an arbitrary guess.
            max_iter = f"({bound} + 1)"
        else:
            # No statically-derivable bound (e.g. quality-gate loops) —
            # configurable safety net against runaway/non-converging loops.
            # Override via env var SPL_WHILE_MAX_ITER or
            # `spl3 configure set spl SPL_WHILE_MAX_ITER=<n>`.
            max_iter = f"int(_spl_config('SPL_WHILE_MAX_ITER', '{self._DEFAULT_WHILE_MAX_ITER}'))"
        lines = [
            f"# SPL: WHILE {self._spl_condition(stmt.condition)} DO",
            f"_while_iter = 0",
            f"while ({cond}) and _while_iter < {max_iter}:",
            f"    _while_iter += 1",
        ]
        inner = self._body_to_python(stmt.body, indent="    ")
        lines.extend(inner if inner else ["    pass"])
        lines.append(f"# END WHILE  (ran {{_while_iter}} iteration(s))")
        return _code_cell("\n".join(lines), metadata={"tags": ["while"]})

    def _commit_cell(self, stmt: CommitStatement) -> dict:
        var = self._expr_py(stmt.expression)
        status_parts = ", ".join(
            f"{k}={self._expr_py(v)}" for k, v in (stmt.options or {}).items()
        )
        spl_src = f"COMMIT {self._spl_expr(stmt.expression)}"
        if status_parts:
            spl_src += f" WITH {status_parts}"

        # TEXT outputs (e.g. @textbook) hold markdown/prose, not structured
        # data. json.dumps()-ing a multi-thousand-word string produces a file
        # that is *syntactically* valid JSON — a single quoted, escaped
        # string — but is not actually JSON data; it's a markdown document
        # wearing a JSON costume (literal \n, \", \\mathbb{...} escapes throughout,
        # unreadable as either format). Write TEXT straight to .md instead;
        # reserve .json + json.dumps for genuinely structured (dict/list) outputs.
        out_type = self.output_types.get(var, "TEXT")
        if out_type == "TEXT":
            lines = [
                f"# SPL: {spl_src}",
                f"_output = {var}",
                f'_result_path = Path("{self.recipe_name}_output.md")',
                f"_result_path.write_text(_output, encoding='utf-8')",
                f'print(f"Committed to {{_result_path}}")',
            ]
        else:
            lines = [
                f"# SPL: {spl_src}",
                f"import json",
                f"_output = {var}",
                f'_result_path = Path("{self.recipe_name}_output.json")',
                f"_result_path.write_text(json.dumps(_output, indent=2, default=str))",
                f'print(f"Committed to {{_result_path}}")',
            ]
        if status_parts:
            lines.append(f"# status: {status_parts}")
        return _code_cell("\n".join(lines), metadata={"tags": ["commit"]})

    def _logging_cell(self, stmt: LoggingStatement) -> dict:
        msg = self._expr_py(stmt.expression)
        level = stmt.level or "INFO"
        spl_comment = f"# SPL: LOGGING {self._spl_expr(stmt.expression)} LEVEL {level}"
        code = f"{spl_comment}\nprint('[{level}]', {msg})"
        return _code_cell(code, metadata={"tags": ["logging"]})

    # ── Recursive body renderer (for OTHERWISE / WHILE / EVALUATE bodies) ────

    def _body_to_python(self, stmts: list, indent: str = "    ") -> list[str]:
        """Render a list of statements as indented Python lines."""
        lines: list[str] = []
        for stmt in stmts:
            cells = self._stmt_to_cells(stmt)
            for cell in cells:
                if cell["cell_type"] == "code":
                    src = "".join(cell["source"])
                    for ln in src.splitlines():
                        lines.append(indent + ln)
        return lines

    # ── Expression renderers ──────────────────────────────────────────────────

    def _expr_py(self, expr) -> str:
        """Render an SPL expression as a plain Python expression (no state[])."""
        if isinstance(expr, ParamRef):
            return self._key(expr.name)
        if isinstance(expr, str):
            if expr.startswith("@"):
                return self._key(expr)
            return repr(expr)
        if isinstance(expr, Literal):
            if isinstance(expr.value, str):
                return repr(expr.value)
            return str(expr.value)
        if isinstance(expr, NoneLiteral):
            return "None"
        if isinstance(expr, FStringLiteral):
            return self._fstr_py(expr.template)
        if isinstance(expr, NamedArg):
            return f"{expr.name}={self._expr_py(expr.value)}"
        if isinstance(expr, UnaryOp):
            return f"not ({self._expr_py(expr.operand)})"
        if isinstance(expr, BinaryOp):
            left  = self._expr_py(expr.left)
            right = self._expr_py(expr.right)
            return f"{left} {expr.op} {right}"
        if isinstance(expr, CompoundCondition):
            parts = [self._render_condition(c) for c in expr.conditions]
            op = " and " if expr.conjunctions and expr.conjunctions[0] == "AND" else " or "
            return op.join(parts)
        return f"# EXPR({type(expr).__name__})"

    def _spl_arg(self, arg) -> str:
        """Render SPL argument for comment traceability."""
        if isinstance(arg, ParamRef):
            return f"@{self._key(arg.name)}"
        if isinstance(arg, Literal):
            return repr(arg.value)
        if isinstance(arg, str):
            return f"@{self._key(arg)}" if arg.startswith("@") else repr(arg)
        if isinstance(arg, NamedArg):
            return f"{arg.name}={self._spl_arg(arg.value)}"
        return str(arg)

    def _spl_expr(self, expr) -> str:
        """Render an SPL expression in SPL syntax (for comments)."""
        if isinstance(expr, ParamRef):
            return f"@{self._key(expr.name)}"
        if isinstance(expr, Literal):
            return repr(expr.value)
        if isinstance(expr, FStringLiteral):
            return f"f'{expr.template}'"
        if isinstance(expr, BinaryOp):
            return f"{self._spl_expr(expr.left)} {expr.op} {self._spl_expr(expr.right)}"
        if isinstance(expr, str):
            return expr
        return self._spl_arg(expr)

    def _fstr_py(self, template: str) -> str:
        """'{@var}/text_{@n}.md' → f'{var}/text_{n}.md'

        Routes each captured name through `_key` so references to
        IPython-reserved identifiers (e.g. {@_i}) are remapped consistently
        with every other code path that emits Python identifiers from SPL
        variable names.
        """
        result = re.sub(r"\{@(\w+)\}", lambda m: "{" + self._key(m.group(1)) + "}", template)
        result = re.sub(r"@(\w+)", lambda m: self._key(m.group(1)), result)
        result = result.replace('"', '\\"')
        return f'f"{result}"'

    def _render_condition(self, cond) -> str:
        """Render a WHILE/ASSERT condition as Python."""
        if isinstance(cond, SemanticCondition):
            return f'"{cond.semantic_value}" not in str(_last_result).lower()'
        if isinstance(cond, CompoundCondition):
            parts = [self._render_condition(c) for c in cond.conditions]
            op = " and " if cond.conjunctions and cond.conjunctions[0] == "AND" else " or "
            return op.join(parts)
        if hasattr(cond, "left") and hasattr(cond, "operator") and hasattr(cond, "right"):
            left = self._expr_py(cond.left)
            right = self._expr_py(cond.right)
            op = "==" if cond.operator == "=" else cond.operator
            return f"{left} {op} {right}"
        # fallback: single-operand condition (e.g., UnaryOp or bare expression)
        if hasattr(cond, "operator") and hasattr(cond, "right"):
            right = self._expr_py(cond.right)
            op = "==" if cond.operator == "=" else cond.operator
            return f"_cond_var {op} {right}"
        return self._expr_py(cond)

    def _spl_condition(self, cond) -> str:
        """Render a condition in SPL syntax for comment."""
        if isinstance(cond, SemanticCondition):
            return cond.semantic_value
        if isinstance(cond, CompoundCondition):
            # spl3 CompoundCondition has left/right/operator
            if hasattr(cond, "left") and hasattr(cond, "right"):
                return f"{self._spl_condition(cond.left)} {cond.operator} {self._spl_condition(cond.right)}"
            # spl base CompoundCondition has conditions/conjunctions lists
            parts = [self._spl_condition(c) for c in cond.conditions]
            conj = f" {cond.conjunctions[0]} " if cond.conjunctions else " AND "
            return conj.join(parts)
        if hasattr(cond, "left") and hasattr(cond, "operator") and hasattr(cond, "right"):
            return f"{self._spl_expr(cond.left)} {cond.operator} {self._spl_expr(cond.right)}"
        return str(cond)

    def _render_when_condition(self, cond, subject_var: str) -> str:
        """Render a WHEN <cond> condition in the context of an EVALUATE subject."""
        if isinstance(cond, SemanticCondition):
            # semantic_value is encoded as "contains:substring" by the parser
            val = cond.semantic_value.lower()
            if val.startswith("contains:"):
                substring = val[len("contains:"):]
            else:
                substring = val
            return f'"{substring}" in str({subject_var}).lower()'
        if hasattr(cond, "left") and hasattr(cond, "operator") and hasattr(cond, "right"):
            right = self._expr_py(cond.right)
            op = "==" if cond.operator == "=" else cond.operator
            return f"{subject_var} {op} {right}"
        if hasattr(cond, "operator") and hasattr(cond, "right"):
            right = self._expr_py(cond.right)
            op = "==" if cond.operator == "=" else cond.operator
            return f"{subject_var} {op} {right}"
        return self._render_condition(cond)

    # IPython reserves these identifiers for its interactive-history machinery
    # (input/output cache, execution counters). Assigning to one of them in a
    # notebook cell is silently clobbered before the *next* cell runs — e.g.
    # `_i = 0` becomes the string source of the previous cell once IPython's
    # `_i`/`_ii`/`_iii` rotation kicks in. Any SPL variable name that collides
    # must be remapped to a safe Python identifier.
    _IPYTHON_RESERVED = frozenset({
        "_i", "_ii", "_iii", "_ih", "_oh", "_dh", "_sh",
        "_", "__", "___", "In", "Out", "get_ipython", "exit", "quit",
    })

    # Fallback safety cap for WHILE loops whose bound can't be statically
    # derived (e.g. quality-gate loops like `WHILE @check != "approved" DO`).
    # Naturally-bounded loops (`@_i < @order_len`) derive their cap from the
    # bound variable itself instead — see `_loop_bound_expr`/`_while_cell`.
    _DEFAULT_WHILE_MAX_ITER = 10

    @classmethod
    def _key(cls, var_name: str) -> str:
        name = var_name.lstrip("@")
        if name in cls._IPYTHON_RESERVED:
            return f"spl_{name}"
        return name

    @classmethod
    def _subst_markers(cls, template: str) -> str:
        """@@varname@@ → varname  (undo parser's @var → @@varname@@ encoding).

        Routes each captured name through `_key` so references to
        IPython-reserved identifiers (e.g. @@_i@@) are remapped consistently
        with every other code path that emits Python identifiers from SPL
        variable names.
        """
        return re.sub(r"@@(\w+)@@", lambda m: cls._key(m.group(1)), template)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _markers_to_at(template: str) -> str:
    """@@varname@@ → @varname  (human-readable SPL form for comments)."""
    return re.sub(r"@@(\w+)@@", r"@\1", template)
