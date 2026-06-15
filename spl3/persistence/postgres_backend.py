"""PostgreSQL-backed persistence backend — production-grade durable execution.

Requires:
    pip install asyncpg
    export SPL_PG_DSN=postgresql://user:pass@host:5432/dbname
    # OR pass dsn= kwarg to get_backend("postgres", dsn="...")

Schema is identical to the SQLite backend (same column names / types) so that
audit tooling and the `spl3 workflow` CLI can target either backend without
changes.

`wait_for_event` uses LISTEN/NOTIFY for sub-second HITL delivery — no polling.
`send_event` inserts the event row and issues a NOTIFY so any listener wakes up
immediately.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
from .base import PersistenceBackend


def _pg_channel(workflow_id: str, event_key: str) -> str:
    """Build a safe PostgreSQL NOTIFY channel name (max 63 chars, identifier-safe)."""
    raw = f"spl_{workflow_id}_{event_key}".lower()
    safe = re.sub(r"[^a-z0-9_]", "_", raw)
    return safe[:63]

_DDL = """
CREATE TABLE IF NOT EXISTS workflows (
    workflow_id   TEXT PRIMARY KEY,
    workflow_name TEXT NOT NULL,
    params        TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'running',
    result        TEXT,
    created_at    DOUBLE PRECISION NOT NULL,
    updated_at    DOUBLE PRECISION NOT NULL
);

CREATE TABLE IF NOT EXISTS steps (
    workflow_id  TEXT NOT NULL,
    step_idx     INTEGER NOT NULL,
    step_name    TEXT NOT NULL,
    result       TEXT NOT NULL,
    state_vars   TEXT NOT NULL,
    completed_at DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (workflow_id, step_idx)
);

CREATE TABLE IF NOT EXISTS events (
    workflow_id TEXT NOT NULL,
    event_key   TEXT NOT NULL,
    value       TEXT NOT NULL,
    created_at  DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (workflow_id, event_key)
);
"""


class PostgresPersistenceBackend(PersistenceBackend):
    """Production PostgreSQL backend with LISTEN/NOTIFY for instant HITL delivery.

    Parameters
    ----------
    dsn          : PostgreSQL connection string (overrides SPL_PG_DSN env var)
    min_size     : connection pool minimum size
    max_size     : connection pool maximum size
    """

    def __init__(
        self,
        dsn: str | None = None,
        min_size: int = 1,
        max_size: int = 5,
    ):
        try:
            import asyncpg  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "asyncpg is not installed. Run: pip install asyncpg\n"
                "Then configure: export SPL_PG_DSN=postgresql://user:pass@host/db"
            ) from exc

        self._dsn = dsn or os.environ.get("SPL_PG_DSN", "")
        if not self._dsn:
            raise ValueError(
                "PostgreSQL DSN not provided. Pass dsn= or set SPL_PG_DSN env var."
            )
        self._min_size = min_size
        self._max_size = max_size
        self._pool = None

    async def _get_pool(self):
        if self._pool is None:
            import asyncpg
            self._pool = await asyncpg.create_pool(
                self._dsn, min_size=self._min_size, max_size=self._max_size
            )
            async with self._pool.acquire() as conn:
                await conn.execute(_DDL)
        return self._pool

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    async def start_workflow(
        self,
        workflow_id: str,
        workflow_name: str,
        params: dict[str, str],
    ) -> dict[str, str] | None:
        pool = await self._get_pool()
        now = time.time()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT status FROM workflows WHERE workflow_id = $1",
                workflow_id,
            )
            if row is None:
                await conn.execute(
                    "INSERT INTO workflows VALUES ($1,$2,$3,$4,$5,$6,$7)",
                    workflow_id, workflow_name, json.dumps(params),
                    "running", None, now, now,
                )
                return None

            if row["status"] == "complete":
                return None

            # Resume: load @var snapshot from last completed step
            last = await conn.fetchrow(
                "SELECT state_vars FROM steps"
                " WHERE workflow_id = $1 ORDER BY step_idx DESC LIMIT 1",
                workflow_id,
            )
            if last:
                return json.loads(last["state_vars"])
            # No steps yet — return original params
            orig = await conn.fetchrow(
                "SELECT params FROM workflows WHERE workflow_id = $1",
                workflow_id,
            )
            return json.loads(orig["params"]) if orig else None

    async def get_step_result(
        self,
        workflow_id: str,
        step_idx: int,
    ) -> str | None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT result FROM steps WHERE workflow_id = $1 AND step_idx = $2",
                workflow_id, step_idx,
            )
            return row["result"] if row else None

    async def checkpoint(
        self,
        workflow_id: str,
        step_idx: int,
        step_name: str,
        result: str,
        state_vars: dict[str, str],
    ) -> None:
        pool = await self._get_pool()
        now = time.time()
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO steps VALUES ($1,$2,$3,$4,$5,$6)"
                " ON CONFLICT (workflow_id, step_idx) DO UPDATE"
                " SET result=$4, state_vars=$5, completed_at=$6",
                workflow_id, step_idx, step_name,
                result, json.dumps(state_vars), now,
            )
            await conn.execute(
                "UPDATE workflows SET updated_at=$1 WHERE workflow_id=$2",
                now, workflow_id,
            )

    async def finish_workflow(
        self,
        workflow_id: str,
        result: str,
        status: str,
    ) -> None:
        pool = await self._get_pool()
        now = time.time()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE workflows SET status=$1, result=$2, updated_at=$3"
                " WHERE workflow_id=$4",
                status, result, now, workflow_id,
            )

    # ── HITL — LISTEN/NOTIFY for instant delivery ──────────────────────────────

    async def wait_for_event(
        self,
        workflow_id: str,
        event_key: str,
        timeout_seconds: float | None = None,
    ) -> str:
        """Block until an external event arrives via PostgreSQL LISTEN/NOTIFY.

        Pre-checks the events table in case the event arrived before we start
        listening (avoids the TOCTOU gap).
        """
        pool = await self._get_pool()
        channel = _pg_channel(workflow_id, event_key)
        future: asyncio.Future[str] = asyncio.get_event_loop().create_future()

        def _on_notify(_conn, _pid, _ch, payload):
            if not future.done():
                future.set_result(payload)

        async with pool.acquire() as listen_conn:
            # Pre-check: event may have arrived before we start listening
            row = await listen_conn.fetchrow(
                "SELECT value FROM events WHERE workflow_id=$1 AND event_key=$2",
                workflow_id, event_key,
            )
            if row:
                return row["value"]

            await listen_conn.add_listener(channel, _on_notify)
            try:
                return await asyncio.wait_for(future, timeout=timeout_seconds)
            except asyncio.TimeoutError:
                raise TimeoutError(
                    f"Event '{event_key}' not received within {timeout_seconds}s"
                )
            finally:
                await listen_conn.remove_listener(channel, _on_notify)

    async def send_event(
        self,
        workflow_id: str,
        event_key: str,
        value: str,
    ) -> None:
        pool = await self._get_pool()
        now = time.time()
        channel = _pg_channel(workflow_id, event_key)
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO events VALUES ($1,$2,$3,$4)"
                " ON CONFLICT (workflow_id, event_key)"
                " DO UPDATE SET value=$3, created_at=$4",
                workflow_id, event_key, value, now,
            )
            # pg_notify() accepts dynamic channel + payload as SQL parameters
            await conn.execute("SELECT pg_notify($1, $2)", channel, value)

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
