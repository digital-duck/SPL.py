"""Tests for spl3.kernel — IPython kernel integration."""

import pytest
from spl3.kernel import IPythonKernel, KernelExecutionError


@pytest.fixture(scope="module")
def kernel():
    """Single kernel shared across all tests in this module (session scope)."""
    k = IPythonKernel(timeout=30)
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
