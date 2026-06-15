"""Unit tests for the SPL persistence layer.

Tests use the SQLite backend only — no LLM calls, no external services.
Run:
    pytest tests/test_persistence.py -v
"""

from __future__ import annotations

import asyncio
import json
import pytest
import tempfile
from pathlib import Path


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_db(tmp_path):
    return str(tmp_path / "test_workflows.db")


@pytest.fixture
def backend(tmp_db):
    from spl3.persistence.sqlite_backend import SQLitePersistenceBackend
    return SQLitePersistenceBackend(db_path=tmp_db)


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ── start_workflow ─────────────────────────────────────────────────────────────

def test_start_workflow_fresh(backend):
    result = run(backend.start_workflow("wf-001", "test_wf", {"task": "hello"}))
    assert result is None  # fresh run returns None


def test_start_workflow_resume_no_steps(backend):
    """Resume before any step completes returns original params."""
    run(backend.start_workflow("wf-001", "test_wf", {"task": "hello"}))
    # Simulate crash before any checkpoint
    result = run(backend.start_workflow("wf-001", "test_wf", {}))
    assert result == {"task": "hello"}


def test_start_workflow_resume_with_checkpoint(backend):
    """Resume after a checkpoint returns the last @var snapshot."""
    run(backend.start_workflow("wf-001", "test_wf", {"task": "hello"}))
    run(backend.checkpoint("wf-001", 0, "GENERATE:step0", "result0",
                           {"task": "hello", "output": "result0"}))
    result = run(backend.start_workflow("wf-001", "test_wf", {}))
    assert result == {"task": "hello", "output": "result0"}


def test_start_workflow_complete_noop(backend):
    """Resuming a completed workflow returns None — caller decides."""
    run(backend.start_workflow("wf-001", "test_wf", {"x": "1"}))
    run(backend.finish_workflow("wf-001", "done", "complete"))
    result = run(backend.start_workflow("wf-001", "test_wf", {}))
    assert result is None


# ── get_step_result / checkpoint ───────────────────────────────────────────────

def test_get_step_result_miss(backend):
    run(backend.start_workflow("wf-001", "test_wf", {}))
    result = run(backend.get_step_result("wf-001", 0))
    assert result is None


def test_checkpoint_and_retrieve(backend):
    run(backend.start_workflow("wf-001", "test_wf", {}))
    run(backend.checkpoint("wf-001", 0, "GENERATE:summarize", "my summary",
                           {"draft": "my summary"}))
    result = run(backend.get_step_result("wf-001", 0))
    assert result == "my summary"


def test_checkpoint_idempotent(backend):
    """Re-checkpointing the same step_idx overwrites (OR REPLACE)."""
    run(backend.start_workflow("wf-001", "test_wf", {}))
    run(backend.checkpoint("wf-001", 0, "GENERATE:x", "v1", {"x": "v1"}))
    run(backend.checkpoint("wf-001", 0, "GENERATE:x", "v2", {"x": "v2"}))
    result = run(backend.get_step_result("wf-001", 0))
    assert result == "v2"


def test_multiple_steps(backend):
    run(backend.start_workflow("wf-001", "test_wf", {}))
    for i in range(5):
        run(backend.checkpoint("wf-001", i, f"GENERATE:step{i}", f"result{i}", {}))
    for i in range(5):
        assert run(backend.get_step_result("wf-001", i)) == f"result{i}"


# ── finish_workflow ────────────────────────────────────────────────────────────

def test_finish_workflow(tmp_db):
    import sqlite3
    from spl3.persistence.sqlite_backend import SQLitePersistenceBackend
    b = SQLitePersistenceBackend(db_path=tmp_db)
    run(b.start_workflow("wf-001", "test_wf", {}))
    run(b.finish_workflow("wf-001", "final output", "complete"))
    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT status, result FROM workflows WHERE workflow_id='wf-001'").fetchone()
    conn.close()
    assert row["status"] == "complete"
    assert row["result"] == "final output"


# ── HITL: send_event / wait_for_event ─────────────────────────────────────────

def test_send_and_receive_event(backend):
    run(backend.start_workflow("wf-001", "test_wf", {}))
    run(backend.send_event("wf-001", "approve", "approved"))
    result = run(backend.wait_for_event("wf-001", "approve"))
    assert result == "approved"


def test_wait_event_timeout(backend):
    run(backend.start_workflow("wf-001", "test_wf", {}))
    with pytest.raises(TimeoutError):
        run(backend.wait_for_event("wf-001", "approve", timeout_seconds=0.1))


def test_send_then_wait_concurrent(backend):
    """Send arrives before wait — wait returns immediately."""
    async def _test():
        await backend.start_workflow("wf-002", "test_wf", {})
        await backend.send_event("wf-002", "gate", "go")
        # wait should resolve immediately since event already exists
        val = await backend.wait_for_event("wf-002", "gate", timeout_seconds=1.0)
        assert val == "go"

    asyncio.get_event_loop().run_until_complete(_test())


def test_concurrent_wait_and_send(backend):
    """Sender arrives after waiter starts — waiter wakes up."""
    async def _test():
        await backend.start_workflow("wf-003", "test_wf", {})

        async def _sender():
            await asyncio.sleep(0.2)
            await backend.send_event("wf-003", "gate", "approved")

        wait_task = asyncio.create_task(
            backend.wait_for_event("wf-003", "gate", timeout_seconds=2.0)
        )
        send_task = asyncio.create_task(_sender())
        result = await wait_task
        await send_task
        assert result == "approved"

    asyncio.get_event_loop().run_until_complete(_test())


# ── factory ───────────────────────────────────────────────────────────────────

def test_get_backend_sqlite(tmp_path):
    from spl3.persistence import get_backend
    b = get_backend("sqlite", db_path=str(tmp_path / "factory.db"))
    from spl3.persistence.sqlite_backend import SQLitePersistenceBackend
    assert isinstance(b, SQLitePersistenceBackend)


def test_get_backend_unknown():
    from spl3.persistence import get_backend
    with pytest.raises(ValueError, match="Unknown"):
        get_backend("redis")


def test_get_backend_dbos_missing():
    """DBOS backend raises ImportError when dbos is not installed."""
    import sys
    # Temporarily hide dbos if it happens to be installed
    dbos_mod = sys.modules.pop("dbos", None)
    try:
        from spl3.persistence import get_backend
        with pytest.raises(ImportError, match="pip install dbos"):
            get_backend("dbos")
    finally:
        if dbos_mod is not None:
            sys.modules["dbos"] = dbos_mod
