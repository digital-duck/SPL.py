"""SQLite-backed persistence backend — zero extra dependencies.

All workflow state is stored in ~/.spl/workflows.db (configurable).
Suitable for local development and single-node production use.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
import time
from pathlib import Path

from .base import PersistenceBackend

_DDL = """
CREATE TABLE IF NOT EXISTS workflows (
    workflow_id   TEXT PRIMARY KEY,
    workflow_name TEXT NOT NULL,
    params        TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'running',
    result        TEXT,
    created_at    REAL NOT NULL,
    updated_at    REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS steps (
    workflow_id  TEXT NOT NULL,
    step_idx     INTEGER NOT NULL,
    step_name    TEXT NOT NULL,
    result       TEXT NOT NULL,
    state_vars   TEXT NOT NULL,
    completed_at REAL NOT NULL,
    PRIMARY KEY (workflow_id, step_idx)
);

CREATE TABLE IF NOT EXISTS events (
    workflow_id TEXT NOT NULL,
    event_key   TEXT NOT NULL,
    value       TEXT NOT NULL,
    created_at  REAL NOT NULL,
    PRIMARY KEY (workflow_id, event_key)
);
"""


class SQLitePersistenceBackend(PersistenceBackend):
    """Local durable execution via SQLite.

    Parameters
    ----------
    db_path : path to the SQLite database file
    poll_interval : seconds between polls in wait_for_event
    """

    def __init__(
        self,
        db_path: str = "~/.spl/workflows.db",
        poll_interval: float = 1.0,
    ):
        self._db_path = Path(db_path).expanduser()
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._poll_interval = poll_interval
        with sqlite3.connect(self._db_path) as conn:
            conn.executescript(_DDL)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    async def start_workflow(
        self,
        workflow_id: str,
        workflow_name: str,
        params: dict[str, str],
    ) -> dict[str, str] | None:
        now = time.time()
        with self._conn() as conn:
            row = conn.execute(
                "SELECT status FROM workflows WHERE workflow_id = ?",
                (workflow_id,),
            ).fetchone()

            if row is None:
                # Fresh run
                conn.execute(
                    "INSERT INTO workflows VALUES (?,?,?,?,?,?,?)",
                    (workflow_id, workflow_name, json.dumps(params),
                     "running", None, now, now),
                )
                return None

            if row["status"] == "complete":
                return None  # already finished — caller decides what to do

            # Resume: load variable snapshot from the last completed step
            last = conn.execute(
                "SELECT state_vars FROM steps"
                " WHERE workflow_id = ? ORDER BY step_idx DESC LIMIT 1",
                (workflow_id,),
            ).fetchone()
            return json.loads(last["state_vars"]) if last else json.loads(
                conn.execute(
                    "SELECT params FROM workflows WHERE workflow_id = ?",
                    (workflow_id,),
                ).fetchone()["params"]
            )

    async def get_step_result(
        self,
        workflow_id: str,
        step_idx: int,
    ) -> str | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT result FROM steps WHERE workflow_id = ? AND step_idx = ?",
                (workflow_id, step_idx),
            ).fetchone()
            return row["result"] if row else None

    async def checkpoint(
        self,
        workflow_id: str,
        step_idx: int,
        step_name: str,
        result: str,
        state_vars: dict[str, str],
    ) -> None:
        now = time.time()
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO steps VALUES (?,?,?,?,?,?)",
                (workflow_id, step_idx, step_name,
                 result, json.dumps(state_vars), now),
            )
            conn.execute(
                "UPDATE workflows SET updated_at = ? WHERE workflow_id = ?",
                (now, workflow_id),
            )

    async def finish_workflow(
        self,
        workflow_id: str,
        result: str,
        status: str,
    ) -> None:
        now = time.time()
        with self._conn() as conn:
            conn.execute(
                "UPDATE workflows SET status=?, result=?, updated_at=?"
                " WHERE workflow_id=?",
                (status, result, now, workflow_id),
            )

    # ── HITL ──────────────────────────────────────────────────────────────────

    async def wait_for_event(
        self,
        workflow_id: str,
        event_key: str,
        timeout_seconds: float | None = None,
    ) -> str:
        deadline = time.time() + timeout_seconds if timeout_seconds else None
        while True:
            with self._conn() as conn:
                row = conn.execute(
                    "SELECT value FROM events"
                    " WHERE workflow_id = ? AND event_key = ?",
                    (workflow_id, event_key),
                ).fetchone()
                if row:
                    return row["value"]
            if deadline and time.time() > deadline:
                raise TimeoutError(
                    f"Event '{event_key}' not received within {timeout_seconds}s"
                )
            await asyncio.sleep(self._poll_interval)

    async def send_event(
        self,
        workflow_id: str,
        event_key: str,
        value: str,
    ) -> None:
        now = time.time()
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO events VALUES (?,?,?,?)",
                (workflow_id, event_key, value, now),
            )
