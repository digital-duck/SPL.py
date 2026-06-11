"""Tests for spl3.kernel — IPython kernel integration.

The shared ``kernel`` fixture is parameterized over kernel specs: the
``python3`` leg always runs; the ``sagemath`` leg runs only when SageMath's
Jupyter kernel is installed (A-1 parity requirement — see
docs/DEV/sage_lean_integration_plan.md §A.3).
"""

from pathlib import Path

import pytest
from spl3.kernel import (
    IPythonKernel,
    KernelExecutionError,
    KernelSpecNotFound,
    installed_kernelspecs,
    kernelspec_installed,
)

SAGE_MISSING = not kernelspec_installed("sagemath")

KERNEL_SPECS = [
    "python3",
    pytest.param(
        "sagemath",
        marks=pytest.mark.skipif(SAGE_MISSING, reason="SageMath kernel not installed"),
    ),
]


@pytest.fixture(scope="module", params=KERNEL_SPECS)
def kernel(request):
    """One kernel per spec, shared across all tests in this module."""
    k = IPythonKernel(timeout=60, kernel_name=request.param)
    k.start()
    yield k
    k.shutdown()


class TestBasicExecution:
    def test_integer_expression(self, kernel):
        assert kernel.execute("1 + 1") == "2"

    def test_string_expression(self, kernel):
        assert kernel.execute("'hello'") == "'hello'"

    def test_stdout(self, kernel):
        assert kernel.execute("print('hi')") == "hi"

    def test_assignment_returns_empty(self, kernel):
        result = kernel.execute("x = 42")
        assert result == ""

    def test_assignment_then_read(self, kernel):
        kernel.execute("y = 99")
        assert kernel.execute("y") == "99"


class TestStatePeristence:
    def test_import_persists(self, kernel):
        kernel.execute("import math")
        assert kernel.execute("math.floor(3.7)") == "3"

    def test_variable_persists_across_calls(self, kernel):
        kernel.execute("counter = 0")
        kernel.execute("counter += 1")
        kernel.execute("counter += 1")
        assert kernel.execute("counter") == "2"


class TestSymPy:
    def test_sympy_diff(self, kernel):
        kernel.execute("import sympy; x = sympy.Symbol('x')")
        result = kernel.execute("sympy.diff(x**3, x)")
        assert result == "3*x**2"

    def test_sympy_eigenpair_check(self, kernel):
        code = """
import sympy
A = sympy.Matrix([[2, 0], [0, 3]])
lam, v = 3, sympy.Matrix([0, 1])
(A * v == lam * v)
"""
        assert kernel.execute(code) == "True"


class TestErrorHandling:
    def test_python_exception_raises(self, kernel):
        with pytest.raises(KernelExecutionError, match="ZeroDivisionError"):
            kernel.execute("1 / 0")

    def test_name_error_raises(self, kernel):
        with pytest.raises(KernelExecutionError, match="NameError"):
            kernel.execute("undefined_variable_xyz")

    def test_kernel_recovers_after_error(self, kernel):
        try:
            kernel.execute("raise ValueError('test')")
        except KernelExecutionError:
            pass
        assert kernel.execute("2 + 2") == "4"


class TestContextManager:
    def test_context_manager(self):
        with IPythonKernel(timeout=30) as k:
            assert k.execute("2 ** 10") == "1024"
        assert not k.is_running


class TestKernelSpec:
    def test_default_kernel_name(self):
        assert IPythonKernel().kernel_name == "python3"

    def test_python3_spec_installed(self):
        assert "python3" in installed_kernelspecs()

    def test_kernelspec_installed_false_for_unknown(self):
        assert not kernelspec_installed("no_such_kernel_xyz_123")

    def test_missing_kernelspec_raises(self):
        k = IPythonKernel(kernel_name="no_such_kernel_xyz_123")
        with pytest.raises(KernelSpecNotFound, match="no_such_kernel_xyz_123"):
            k.start()
        assert not k.is_running

    def test_missing_sagemath_message_has_install_hint(self):
        if not SAGE_MISSING:
            pytest.skip("SageMath installed — error path not reachable")
        k = IPythonKernel(kernel_name="sagemath")
        with pytest.raises(KernelSpecNotFound, match="conda-forge"):
            k.start()


@pytest.mark.skipif(SAGE_MISSING, reason="SageMath kernel not installed")
class TestSageSpike:
    """A-1 environment-gap spike (sage_lean_integration_plan.md §A.2).

    Answers the three residual risks in one go: Sage's Python can run the
    path-located domain library, Sage's bundled SymPy passes an existing
    verifier check, and the preparser semantics are what we documented.
    """

    @pytest.fixture(scope="class")
    def sage(self):
        k = IPythonKernel(timeout=120, kernel_name="sagemath")
        k.start()
        yield k
        k.shutdown()

    def test_preparser_semantics(self, sage):
        # The sagemath kernel preparses cell code: ^ is power, not XOR.
        assert sage.execute("2^3") == "8"

    def test_domain_library_runs_under_sage_python(self, sage):
        lib = Path(__file__).resolve().parents[1] / "cookbook" / "71_linalg_micro_textbook"
        sage.execute(f"import sys; sys.path.insert(0, {str(lib)!r})")
        sage.execute("import linalg_graph; G = linalg_graph.build()")
        assert sage.execute("linalg_graph.acyclic(G)") == "True"
        assert sage.execute(
            "linalg_graph.reducible(G, linalg_graph.primitive_names())"
        ) == "True"

    def test_sympy_verifier_with_preparser_off(self, sage):
        # The documented mitigation: preparser(False) before pure-Python verifier code.
        sage.execute("preparser(False)")
        try:
            code = """
import sympy
A = sympy.Matrix([[2, 0], [0, 3]])
lam, v = 3, sympy.Matrix([0, 1])
(A * v == lam * v)
"""
            assert sage.execute(code) == "True"
        finally:
            sage.execute("preparser(True)")
