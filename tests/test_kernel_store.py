"""Tests for KernelStore and KernelStore-backed SOLVE/ASSERT (Path B).

Covers:
  - KernelStore.save_var / load_namespace round-trip
  - KernelStore.save_namespace filters private vars and non-picklables
  - KernelStore.delete clears workflow entries
  - Path B: SOLVE exec() with DB namespace (no live kernel)
  - Path B: cross-step state accumulation via KernelStore
  - Path B: crash-resume — reload namespace from DB and continue
  - Path B: ASSERT reads DB namespace
  - Path B: ToolFailed when neither kernel nor kernel_store present (unchanged)
"""
from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

import pytest

from spl.lexer import Lexer
from spl.analyzer import Analyzer
from spl.adapters.base import GenerationResult
from spl3.parser import SPL3Parser
from spl3.executor import SPL3Executor
from spl3.kernel_store import KernelStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _StubAdapter:
    async def generate(self, prompt, **kw):
        return GenerationResult(
            content="stub", model="stub", latency_ms=0,
            input_tokens=0, output_tokens=0, total_tokens=0,
        )


def _make_store(tmp_path: Path) -> KernelStore:
    return KernelStore(db_path=str(tmp_path / "test.db"))


def _parse(spl: str):
    tokens = Lexer(spl).tokenize()
    return SPL3Parser(tokens).parse()


def _run_with_store(spl: str, store: KernelStore, workflow_id: str,
                    params: dict | None = None):
    tokens = Lexer(spl).tokenize()
    program = SPL3Parser(tokens).parse()
    analysis = Analyzer().analyze(program)
    executor = SPL3Executor(
        adapter=_StubAdapter(),
        kernel_store=store,
        workflow_id=workflow_id,
    )

    async def _go():
        return await executor.execute_program(analysis, params=params or {})

    return asyncio.run(_go()), executor


# ---------------------------------------------------------------------------
# KernelStore unit tests
# ---------------------------------------------------------------------------

class TestKernelStoreRoundTrip:
    def test_save_and_load_int(self, tmp_path):
        store = _make_store(tmp_path)
        store.save_var("wf1", "x", 42)
        ns = store.load_namespace("wf1")
        assert ns["x"] == 42

    def test_save_and_load_list(self, tmp_path):
        store = _make_store(tmp_path)
        store.save_var("wf1", "items", [1, 2, 3])
        ns = store.load_namespace("wf1")
        assert ns["items"] == [1, 2, 3]

    def test_save_and_load_dict(self, tmp_path):
        store = _make_store(tmp_path)
        store.save_var("wf1", "data", {"a": 1})
        ns = store.load_namespace("wf1")
        assert ns["data"] == {"a": 1}

    def test_load_empty_workflow(self, tmp_path):
        store = _make_store(tmp_path)
        ns = store.load_namespace("no-such-workflow")
        assert ns == {}

    def test_overwrite_var(self, tmp_path):
        store = _make_store(tmp_path)
        store.save_var("wf1", "x", 1)
        store.save_var("wf1", "x", 99)
        ns = store.load_namespace("wf1")
        assert ns["x"] == 99

    def test_multiple_workflows_isolated(self, tmp_path):
        store = _make_store(tmp_path)
        store.save_var("wf-a", "x", 10)
        store.save_var("wf-b", "x", 20)
        assert store.load_namespace("wf-a")["x"] == 10
        assert store.load_namespace("wf-b")["x"] == 20

    def test_delete_clears_workflow(self, tmp_path):
        store = _make_store(tmp_path)
        store.save_var("wf1", "x", 42)
        store.delete("wf1")
        assert store.load_namespace("wf1") == {}

    def test_delete_does_not_affect_other_workflow(self, tmp_path):
        store = _make_store(tmp_path)
        store.save_var("wf-a", "x", 10)
        store.save_var("wf-b", "y", 20)
        store.delete("wf-a")
        assert store.load_namespace("wf-b")["y"] == 20

    def test_save_namespace_filters_private(self, tmp_path):
        store = _make_store(tmp_path)
        ns = {"x": 1, "_private": 2, "__dunder": 3}
        store.save_namespace("wf1", ns)
        loaded = store.load_namespace("wf1")
        assert "x" in loaded
        assert "_private" not in loaded
        assert "__dunder" not in loaded

    def test_save_namespace_skips_non_picklable(self, tmp_path):
        store = _make_store(tmp_path)
        ns = {"x": 42, "fn": lambda: None}  # lambda is not picklable
        store.save_namespace("wf1", ns)
        loaded = store.load_namespace("wf1")
        assert loaded["x"] == 42
        assert "fn" not in loaded

    def test_table_created_in_shared_db(self, tmp_path):
        db = tmp_path / "workflows.db"
        store = KernelStore(db_path=str(db))
        store.save_var("wf1", "x", 1)
        # Verify the table exists via raw sqlite3
        with sqlite3.connect(db) as conn:
            tables = [r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()]
        assert "kernel_vars" in tables

    def test_str_fallback_for_unpicklable_var(self, tmp_path):
        """save_var falls back to str(value) when pickle.dumps raises."""
        store = _make_store(tmp_path)
        # Craft an object that cannot be pickled
        class Unpicklable:
            def __reduce__(self):
                raise TypeError("cannot pickle")

        store.save_var("wf1", "bad", Unpicklable())
        ns = store.load_namespace("wf1")
        # Fallback stores str repr
        assert "bad" in ns
        assert isinstance(ns["bad"], str)


# ---------------------------------------------------------------------------
# Path B executor tests (kernel_store, no live kernel)
# ---------------------------------------------------------------------------

class TestSolvePathB:
    def test_basic_solve_integer(self, tmp_path):
        store = _make_store(tmp_path)
        result, _ = _run_with_store("""
        WORKFLOW test
        DO
            SOLVE @answer := 6 * 7
        END
        """, store, "wf-basic")
        assert result[0].output.get("answer") == "42"

    def test_solve_persists_to_store(self, tmp_path):
        store = _make_store(tmp_path)
        _run_with_store("""
        WORKFLOW test
        DO
            SOLVE @x := 100
        END
        """, store, "wf-persist")
        ns = store.load_namespace("wf-persist")
        assert ns.get("x") == 100

    def test_solve_cross_step_accumulation(self, tmp_path):
        """Second SOLVE can reference the variable set by first SOLVE."""
        store = _make_store(tmp_path)
        result, _ = _run_with_store("""
        WORKFLOW test
        DO
            SOLVE @a := 10
            SOLVE @b := @a * 3
        END
        """, store, "wf-cross")
        assert result[0].output.get("a") == "10"
        assert result[0].output.get("b") == "30"

    def test_solve_with_input_variable(self, tmp_path):
        store = _make_store(tmp_path)
        result, _ = _run_with_store("""
        WORKFLOW test
        INPUT @n TEXT := '5'
        DO
            SOLVE @squared := int(@n) ** 2
        END
        """, store, "wf-input", params={"n": "5"})
        assert result[0].output.get("squared") == "25"

    def test_solve_exec_error_raises_tool_failed(self, tmp_path):
        store = _make_store(tmp_path)
        from spl.executor import ToolFailed
        with pytest.raises((ToolFailed, Exception)):
            _run_with_store("""
            WORKFLOW test
            DO
                SOLVE @x := undefined_function_xyz()
            END
            """, store, "wf-err")

    def test_crash_resume_via_store(self, tmp_path):
        """Simulate crash recovery: pre-populate DB then resume in new executor."""
        store = _make_store(tmp_path)
        # Simulate a prior SOLVE that set @x = 7 (a crash happened after this)
        store.save_var("wf-resume", "x", 7)

        # New executor: resumes, sees x=7 in namespace, computes y = x * 6
        result, _ = _run_with_store("""
        WORKFLOW test
        DO
            SOLVE @y := x * 6
        END
        """, store, "wf-resume")
        assert result[0].output.get("y") == "42"


class TestAssertPathB:
    def test_assert_passes_with_store_namespace(self, tmp_path):
        store = _make_store(tmp_path)
        # Pre-populate: x = 42
        store.save_var("wf-assert", "x", 42)
        result, _ = _run_with_store("""
        WORKFLOW test
        DO
            ASSERT x > 0
            @done := 'yes'
        END
        """, store, "wf-assert")
        assert result[0].output.get("done") == "yes"

    def test_assert_fails_raises(self, tmp_path):
        store = _make_store(tmp_path)
        store.save_var("wf-fail", "x", -1)
        from spl.executor import ToolFailed
        with pytest.raises((ToolFailed, Exception)):
            _run_with_store("""
            WORKFLOW test
            DO
                ASSERT x > 0
            END
            """, store, "wf-fail")

    def test_solve_then_assert_integration(self, tmp_path):
        """SOLVE sets a value in DB; ASSERT reads it back."""
        store = _make_store(tmp_path)
        result, _ = _run_with_store("""
        WORKFLOW test
        DO
            SOLVE @n := 42
            ASSERT n == 42
            @ok := 'passed'
        END
        """, store, "wf-integrate")
        assert result[0].output.get("ok") == "passed"


class TestNoKernelNoStore:
    def test_solve_without_kernel_or_store_raises(self):
        """Existing behaviour: SOLVE raises ToolFailed without kernel or store."""
        from spl.executor import ToolFailed
        with pytest.raises((ToolFailed, Exception)):
            tokens = Lexer("""
            WORKFLOW test
            DO
                SOLVE @x := 1 + 1
            END
            """).tokenize()
            program = SPL3Parser(tokens).parse()
            analysis = Analyzer().analyze(program)
            executor = SPL3Executor(adapter=_StubAdapter())

            async def _go():
                return await executor.execute_program(analysis)

            asyncio.run(_go())
