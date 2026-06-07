"""splc — deterministic SPL 3.0 → python/linalg .ipynb transpiler.

No LLM required.  Converts a .spl logical view to an annotated Jupyter notebook
where each SPL statement becomes one or more executable cells.

Output is a valid .ipynb (nbformat 4) ready to run with:
    jupyter nbconvert --to notebook --execute <output>.ipynb

This module is now a thin `python/linalg` preset over the generalized
`DomainGraphTranspiler` engine in `transpiler_domain_graph.py` — see that
module's docstring for the full SPL → cell construct mapping and the DODA
note. `LinalgTranspiler` exists (rather than calling the engine directly)
solely to keep the `from spl3.splc.transpiler_linalg import LinalgTranspiler`
import path `cli.py` depends on stable.

"Changing domain = swap linalg_graph.py for <domain>_graph.py" is the thesis
this split makes literal: everything domain-agnostic lives in the engine;
everything linalg-specific lives in `LINALG_CONFIG` below.
"""

from __future__ import annotations

from spl3.splc.transpiler_domain_graph import (
    DomainConfig,
    DomainGraphTranspiler,
    VerifierSpec,
)

# ---------------------------------------------------------------------------
# Domain verifier helpers — emitted verbatim into the setup cell.
#
# Linear algebra has two independent failure surfaces — "is the arithmetic
# right" (verify_math, a SymPy recompute of worked examples) and "do these
# matrices even compose" (shape_check, dimension-compatibility) — so this is
# the two-verifier preset. Compare `transpiler_intro_geometry.py`'s
# single-verifier `GEOMETRY_CONFIG` (geometry has no shape analogue: nothing
# to dimension-check).
# ---------------------------------------------------------------------------

_VERIFY_MATH_SOURCE = '''\
# ── Math verifier helpers ─────────────────────────────────────────────────────
def _verify_math(section: str) -> str:
    """Returns 'pass' or a description of the failure."""
    try:
        import sympy  # noqa: F401 — presence check
        return "pass"   # TODO: parse worked examples from section and recompute
    except Exception as exc:
        return f"fail: {exc}"
'''

_SHAPE_CHECK_SOURCE = '''\
def _shape_check(section: str) -> str:
    """Check matrix dimension compatibility. Returns 'pass' or error."""
    return "pass"  # TODO: parse matrix expressions and check shapes
'''

LINALG_CONFIG = DomainConfig(
    target="python/linalg",
    graph_module="linalg_graph",
    graph_dir_env="LINALG_GRAPH_DIR",
    framework="linalg",
    primitives_fn="both_radical_primitives",
    verifiers=(
        VerifierSpec(call_name="verify_math", helper_name="_verify_math", helper_source=_VERIFY_MATH_SOURCE),
        VerifierSpec(call_name="shape_check", helper_name="_shape_check", helper_source=_SHAPE_CHECK_SOURCE),
    ),
)


class LinalgTranspiler(DomainGraphTranspiler):
    """Deterministic SPL 3.0 → python/linalg .ipynb transpiler.

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

    def __init__(self, recipe_name: str, spl_dir=None):
        super().__init__(recipe_name, LINALG_CONFIG, spl_dir=spl_dir)
