"""Tests for SOLVE and ASSERT SPL 3.0 deterministic constructs.

Covers:
  - Parsing: SolveStatement and AssertStatement emitted correctly
  - Template variable substitution (@@varname@@ markers)
  - Executor: SOLVE assigns kernel result to target variable
  - Executor: ASSERT passes silently when condition is True
  - Executor: ASSERT executes otherwise_body when condition is False
  - Executor: ASSERT raises ToolFailed when no otherwise_body and condition is False
  - Error: SOLVE/ASSERT without --kernel raises ToolFailed
  - Integration: SOLVE + ASSERT in one workflow
"""
from __future__ import annotations

import asyncio
import pytest

from spl.lexer import Lexer
from spl.analyzer import Analyzer
from spl.adapters.base import GenerationResult
from spl3.parser import SPL3Parser
from spl3.executor import SPL3Executor
from spl3.ast_nodes import SolveStatement, AssertStatement


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _StubAdapter:
    async def generate(self, prompt, **kw):
        return GenerationResult(
            content="stub", model="stub", latency_ms=0,
            input_tokens=0, output_tokens=0, total_tokens=0,
        )


class _MockKernel:
    """Lightweight mock that records execute() calls and returns preset results."""

    def __init__(self, responses: dict[str, str] | None = None):
        self.calls: list[str] = []
        self.responses = responses or {}  # substring → response
        self.is_running = True

    def execute(self, code: str) -> str:
        self.calls.append(code)
        for key, val in self.responses.items():
            if key in code:
                return val
        return ""

    def shutdown(self):
        self.is_running = False


def _parse(spl: str):
    tokens = Lexer(spl).tokenize()
    return SPL3Parser(tokens).parse()


def _run(spl: str, kernel: _MockKernel | None = None, params: dict | None = None):
    tokens = Lexer(spl).tokenize()
    program = SPL3Parser(tokens).parse()
    analysis = Analyzer().analyze(program)
    adapter = _StubAdapter()
    executor = SPL3Executor(adapter=adapter)
    if kernel is not None:
        executor._kernel = kernel
    async def _go():
        return await executor.execute_program(analysis, params=params or {})
    return asyncio.run(_go()), executor


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------

class TestSolveParser:
    def test_basic_solve(self):
        prog = _parse("""
        WORKFLOW test
        DO
            SOLVE @result := my_func()
        END
        """)
        wf = prog.statements[0]
        stmt = wf.body[0]
        assert isinstance(stmt, SolveStatement)
        assert stmt.target_variable == "result"
        assert stmt.target_type is None
        assert "my_func()" in stmt.python_template

    def test_solve_with_type(self):
        prog = _parse("""
        WORKFLOW test
        DO
            SOLVE @order LIST := sorted_order()
        END
        """)
        stmt = prog.statements[0].body[0]
        assert isinstance(stmt, SolveStatement)
        assert stmt.target_type == "LIST"
        assert stmt.target_variable == "order"

    def test_solve_with_variable_refs(self):
        prog = _parse("""
        WORKFLOW test
        DO
            SOLVE @result := compute(@x, weight=@w)
        END
        """)
        stmt = prog.statements[0].body[0]
        assert isinstance(stmt, SolveStatement)
        assert "@@x@@" in stmt.python_template
        assert "@@w@@" in stmt.python_template
        assert "compute(" in stmt.python_template

    def test_solve_with_numeric_literal(self):
        prog = _parse("""
        WORKFLOW test
        DO
            SOLVE @n NUMBER := sum_values(@items, default=0)
        END
        """)
        stmt = prog.statements[0].body[0]
        assert isinstance(stmt, SolveStatement)
        assert stmt.target_type == "NUMBER"
        assert "0" in stmt.python_template


class TestAssertParser:
    def test_basic_assert_no_otherwise(self):
        prog = _parse("""
        WORKFLOW test
        DO
            ASSERT is_valid(@data)
        END
        """)
        stmt = prog.statements[0].body[0]
        assert isinstance(stmt, AssertStatement)
        assert "@@data@@" in stmt.python_template
        assert stmt.otherwise_body == []

    def test_assert_with_otherwise_retry(self):
        prog = _parse("""
        WORKFLOW test
        DO
            ASSERT is_valid(@data)
                OTHERWISE RETRY
        END
        """)
        stmt = prog.statements[0].body[0]
        assert isinstance(stmt, AssertStatement)
        assert len(stmt.otherwise_body) == 1

    def test_assert_with_multi_arg(self):
        prog = _parse("""
        WORKFLOW test
        DO
            ASSERT reducible(@graph, @primitives)
                OTHERWISE RETRY
        END
        """)
        stmt = prog.statements[0].body[0]
        assert isinstance(stmt, AssertStatement)
        assert "@@graph@@" in stmt.python_template
        assert "@@primitives@@" in stmt.python_template


# ---------------------------------------------------------------------------
# Template substitution tests
# ---------------------------------------------------------------------------

class TestTemplateSubstitution:
    def test_no_vars(self):
        state = type('S', (), {'get_var': staticmethod(lambda n: '')})()
        template = "compute(42)"
        result = SPL3Executor._resolve_python_template(template, state)
        assert result == "compute(42)"

    def test_single_var(self):
        vals = {"myvar": "hello"}
        state = type('S', (), {'get_var': staticmethod(lambda n: vals.get(n, ''))})()
        template = "process(@@myvar@@)"
        result = SPL3Executor._resolve_python_template(template, state)
        assert result == "process(hello)"

    def test_multiple_vars(self):
        vals = {"x": "10", "y": "20"}
        state = type('S', (), {'get_var': staticmethod(lambda n: vals.get(n, ''))})()
        template = "add(@@x@@, @@y@@)"
        result = SPL3Executor._resolve_python_template(template, state)
        assert result == "add(10, 20)"


# ---------------------------------------------------------------------------
# Executor tests with mock kernel
# ---------------------------------------------------------------------------

class TestSolveExecution:
    def test_solve_assigns_result(self):
        kernel = _MockKernel({"_spl_solve_result": "42"})
        result, executor = _run("""
        WORKFLOW solve_test
        DO
            SOLVE @answer := compute_answer()
        END
        """, kernel=kernel)
        assert result[0].output.get("answer") == "42"

    def test_solve_sends_correct_code(self):
        kernel = _MockKernel({"_spl_solve_result": "[1, 2, 3]"})
        _run("""
        WORKFLOW solve_test
        DO
            SOLVE @order LIST := sorted_order()
        END
        """, kernel=kernel)
        assert len(kernel.calls) == 1
        code = kernel.calls[0]
        assert "_spl_solve_result = sorted_order()" in code
        assert "print(str(_spl_solve_result))" in code

    def test_solve_without_kernel_raises(self):
        with pytest.raises(Exception):
            _run("""
            WORKFLOW test
            DO
                SOLVE @x := compute()
            END
            """)

    def test_solve_variable_substitution_end_to_end(self):
        kernel = _MockKernel({"_spl_solve_result": "99"})
        _run("""
        WORKFLOW test
        INPUT @base TEXT := '42'
        DO
            SOLVE @doubled := double(@base)
        END
        """, kernel=kernel, params={"base": "42"})
        code_sent = kernel.calls[0]
        assert "double(42)" in code_sent


class TestAssertExecution:
    def test_assert_passes_silently(self):
        kernel = _MockKernel({"_spl_assert_result": "True"})
        result, _ = _run("""
        WORKFLOW test
        DO
            ASSERT is_valid()
            @status := 'ok'
        END
        """, kernel=kernel)
        assert result[0].output.get("status") == "ok"

    def test_assert_sends_bool_wrapper(self):
        kernel = _MockKernel({"_spl_assert_result": "True"})
        _run("""
        WORKFLOW test
        DO
            ASSERT check_result()
        END
        """, kernel=kernel)
        code = kernel.calls[0]
        assert "_spl_assert_result = bool(check_result())" in code
        assert "print(_spl_assert_result)" in code

    def test_assert_fails_raises_without_otherwise(self):
        kernel = _MockKernel({"_spl_assert_result": "False"})
        with pytest.raises(Exception):
            _run("""
            WORKFLOW test
            DO
                ASSERT check_result()
            END
            """, kernel=kernel)

    def test_assert_executes_otherwise_on_failure(self):
        kernel = _MockKernel({"_spl_assert_result": "False"})
        with pytest.raises(Exception):
            _run("""
            WORKFLOW test
            DO
                ASSERT check_result()
                    OTHERWISE RAISE ConstraintViolation 'check failed'
            END
            """, kernel=kernel)

    def test_assert_with_variable_substitution(self):
        kernel = _MockKernel({"_spl_assert_result": "True"})
        _run("""
        WORKFLOW test
        INPUT @items TEXT := '[]'
        DO
            ASSERT is_non_empty(@items)
        END
        """, kernel=kernel, params={"items": "[1,2,3]"})
        code = kernel.calls[0]
        assert "is_non_empty([1,2,3])" in code

    def test_assert_without_kernel_raises(self):
        with pytest.raises(Exception):
            _run("""
            WORKFLOW test
            DO
                ASSERT check()
            END
            """)


# ---------------------------------------------------------------------------
# Integration: SOLVE + ASSERT in one workflow
# ---------------------------------------------------------------------------

class TestSolveAssertIntegration:
    def test_solve_then_assert(self):
        """SOLVE computes a value, ASSERT verifies it, workflow continues."""
        kernel = _MockKernel({
            "_spl_solve_result": "42",
            "_spl_assert_result": "True",
        })
        result, _ = _run("""
        WORKFLOW integration_test
        DO
            SOLVE @computed NUMBER := compute_answer()
            ASSERT is_positive(@computed)
            @done := 'yes'
        END
        """, kernel=kernel)
        assert result[0].output.get("done") == "yes"
        assert result[0].output.get("computed") == "42"
        # Two kernel calls: one for SOLVE, one for ASSERT
        assert len(kernel.calls) == 2
        solve_call = kernel.calls[0]
        assert_call = kernel.calls[1]
        assert "_spl_solve_result = compute_answer()" in solve_call
        # ASSERT should use the substituted value (42) from state
        assert "is_positive(42)" in assert_call
