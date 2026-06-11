"""A-2 tests — SageMath in the domain-notebook targets.

Covers (see docs/DEV/sage_lean_integration_plan.md §A.2–A.3):
  - `DomainConfig.kernel_name` → emitted `.ipynb` kernelspec metadata
    (the artifact carries its runtime — DODA)
  - `graph_lib.verify_content` engine dispatch: `verifier: "sage"` and the
    `"sage|sympy"` fallback-tiering policy, with engine-of-record in the
    return value
"""

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cookbook" / "74_domain_textbook"))

import graph_lib  # noqa: E402
from spl.lexer import Lexer  # noqa: E402
from spl3.parser import SPL3Parser  # noqa: E402
from spl3.splc.transpiler_linalg import LinalgTranspiler  # noqa: E402
from spl3.splc.transpiler_domain_textbook import DomainTextbookTranspiler  # noqa: E402

_MINIMAL_SPL = """\
WORKFLOW test_workflow
    OUTPUT: @result TEXT
DO
    SOLVE @result TEXT := str(2 + 2)
    RETURN @result
END
"""


def _sage_available() -> bool:
    try:
        import sage.all  # noqa: F401
        return True
    except Exception:
        return False


def _transpile(transpiler_cls, kernel_name=None) -> dict:
    tokens = Lexer(_MINIMAL_SPL).tokenize()
    program = SPL3Parser(tokens).parse()
    transpiler = transpiler_cls("test_workflow", kernel_name=kernel_name)
    return json.loads(transpiler.transpile(program))


class TestKernelspecEmission:
    def test_default_kernelspec_is_python3(self):
        nb = _transpile(LinalgTranspiler)
        ks = nb["metadata"]["kernelspec"]
        assert ks["name"] == "python3"
        assert ks["language"] == "python"
        assert nb["metadata"]["splc"]["kernel_name"] == "python3"

    def test_sagemath_kernelspec_emitted(self):
        nb = _transpile(LinalgTranspiler, kernel_name="sagemath")
        ks = nb["metadata"]["kernelspec"]
        assert ks == {"display_name": "SageMath", "language": "sage", "name": "sagemath"}
        assert nb["metadata"]["splc"]["kernel_name"] == "sagemath"

    def test_sagemath_kernelspec_domain_textbook(self):
        nb = _transpile(DomainTextbookTranspiler, kernel_name="sagemath")
        assert nb["metadata"]["kernelspec"]["name"] == "sagemath"

    def test_unknown_kernel_name_falls_back_to_name_as_display(self):
        nb = _transpile(LinalgTranspiler, kernel_name="julia-1.10")
        ks = nb["metadata"]["kernelspec"]
        assert ks["name"] == "julia-1.10"
        assert ks["display_name"] == "julia-1.10"

    def test_cells_unchanged_by_kernel_name(self):
        default = _transpile(LinalgTranspiler)
        sage = _transpile(LinalgTranspiler, kernel_name="sagemath")
        assert default["cells"] == sage["cells"]


class TestVerifyContentDispatch:
    DOMAIN = {"domain": "linalg"}

    def test_domain_default_unchanged(self):
        # No verifier arg → pre-A-2 behavior, plain "pass"
        assert graph_lib.verify_content("section text", self.DOMAIN) == "pass"

    def test_explicit_sympy_engine_records_engine(self):
        out = graph_lib.verify_content("section text", self.DOMAIN, verifier="sympy")
        assert out == "pass (sympy)"

    def test_unknown_engine_fails(self):
        out = graph_lib.verify_content("section text", self.DOMAIN,
                                       verifier="no_such_engine_xyz")
        assert out.startswith("fail:")

    def test_fallback_tier_prefers_first_available(self):
        # "sage|sympy": sage when installed, else sympy — never a hard fail
        out = graph_lib.verify_content("section text", self.DOMAIN, verifier="sage|sympy")
        expected = "pass (sage)" if _sage_available() else "pass (sympy)"
        assert out == expected

    @pytest.mark.skipif(not _sage_available(), reason="SageMath not installed")
    def test_sage_engine(self):
        out = graph_lib.verify_content("section text", self.DOMAIN, verifier="sage")
        assert out == "pass (sage)"
