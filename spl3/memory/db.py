"""SPL Memory DB — unified persistence layer for UI config, workflow sessions,
and pipeline tracking.

Four tables:
  ui_config        — namespaced key-value store for UI preferences / settings
  workflow_sessions — every spl3 run invocation with status, output, metrics
  pipeline_runs    — multi-step experiment runs (NeurIPS, intent-eng 5-gate)
  pipeline_steps   — individual step records with scores and checkpoint state

Backend selection via SPL_MEMORY_URL environment variable:
  sqlite:///path/to/spl_memory.db   (default, POC)
  postgresql://user:pass@host/dbname  (production)

When SPL_MEMORY_URL is not set, defaults to:
  <this file's parent>/../../ui/streamlit/data/spl_memory.db
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator

logger = logging.getLogger(__name__)

# ── Default path ──────────────────────────────────────────────────────────────

_DEFAULT_SQLITE = (
    Path(__file__).parent.parent / "ui" / "streamlit" / "data" / "spl_memory.db"
)

# ── DDL ───────────────────────────────────────────────────────────────────────

_DDL_SQLITE = """
CREATE TABLE IF NOT EXISTS ui_config (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    namespace  TEXT NOT NULL DEFAULT 'global',
    key        TEXT NOT NULL,
    value      TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(namespace, key)
);

CREATE TABLE IF NOT EXISTS workflow_sessions (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id     TEXT NOT NULL UNIQUE,
    workflow_name  TEXT NOT NULL,
    spl_file       TEXT,
    adapter        TEXT,
    model          TEXT,
    status         TEXT NOT NULL DEFAULT 'running',
    input_params   TEXT,
    output         TEXT,
    error          TEXT,
    latency_ms     INTEGER,
    tokens_used    INTEGER,
    cost_usd       REAL,
    started_at     TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at   TEXT
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_name TEXT NOT NULL,
    run_label     TEXT NOT NULL,
    recipe        TEXT,
    model_alias   TEXT,
    adapter       TEXT,
    model_id      TEXT,
    phase         INTEGER,
    status        TEXT NOT NULL DEFAULT 'in_progress',
    notes         TEXT,
    started_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(pipeline_name, run_label)
);

CREATE TABLE IF NOT EXISTS pipeline_steps (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id            INTEGER NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    step              TEXT NOT NULL,
    status            TEXT NOT NULL DEFAULT 'pending',
    artifact_path     TEXT,
    score             REAL,
    checkpoint_passed INTEGER NOT NULL DEFAULT 0,
    checkpoint_note   TEXT,
    started_at        TEXT,
    completed_at      TEXT,
    UNIQUE(run_id, step)
);

CREATE INDEX IF NOT EXISTS idx_workflow_sessions_status
    ON workflow_sessions(status);
CREATE INDEX IF NOT EXISTS idx_pipeline_steps_run
    ON pipeline_steps(run_id);
"""

_DDL_POSTGRES = """
CREATE TABLE IF NOT EXISTS ui_config (
    id         SERIAL PRIMARY KEY,
    namespace  TEXT NOT NULL DEFAULT 'global',
    key        TEXT NOT NULL,
    value      TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(namespace, key)
);

CREATE TABLE IF NOT EXISTS workflow_sessions (
    id             SERIAL PRIMARY KEY,
    session_id     TEXT NOT NULL UNIQUE,
    workflow_name  TEXT NOT NULL,
    spl_file       TEXT,
    adapter        TEXT,
    model          TEXT,
    status         TEXT NOT NULL DEFAULT 'running',
    input_params   TEXT,
    output         TEXT,
    error          TEXT,
    latency_ms     INTEGER,
    tokens_used    INTEGER,
    cost_usd       REAL,
    started_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at   TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id            SERIAL PRIMARY KEY,
    pipeline_name TEXT NOT NULL,
    run_label     TEXT NOT NULL,
    recipe        TEXT,
    model_alias   TEXT,
    adapter       TEXT,
    model_id      TEXT,
    phase         INTEGER,
    status        TEXT NOT NULL DEFAULT 'in_progress',
    notes         TEXT,
    started_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(pipeline_name, run_label)
);

CREATE TABLE IF NOT EXISTS pipeline_steps (
    id                SERIAL PRIMARY KEY,
    run_id            INTEGER NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    step              TEXT NOT NULL,
    status            TEXT NOT NULL DEFAULT 'pending',
    artifact_path     TEXT,
    score             REAL,
    checkpoint_passed BOOLEAN NOT NULL DEFAULT FALSE,
    checkpoint_note   TEXT,
    started_at        TIMESTAMPTZ,
    completed_at      TIMESTAMPTZ,
    UNIQUE(run_id, step)
);

CREATE INDEX IF NOT EXISTS idx_workflow_sessions_status
    ON workflow_sessions(status);
CREATE INDEX IF NOT EXISTS idx_pipeline_steps_run
    ON pipeline_steps(run_id);
"""


# ── MemoryDB ──────────────────────────────────────────────────────────────────

class MemoryDB:
    """Unified persistence layer for SPL Studio.

    Instantiate once and reuse — connection is kept open.
    Call close() or use as a context manager when done.

    Usage::
        db = MemoryDB()                          # SQLite default
        db = MemoryDB("sqlite:///my.db")
        db = MemoryDB("postgresql://localhost/spl")

        # UI config
        db.config_set("splc", "last_adapter", "claude_cli")
        adapter = db.config_get("splc", "last_adapter")

        # Workflow sessions
        sid = db.session_start("self_refine", spl_file="...", adapter="ollama", model="gemma3")
        db.session_complete(sid, output="...", latency_ms=1200, tokens_used=450)

        # Pipeline tracking
        run_id = db.pipeline_upsert("neurips_ndd", "R1-agent/claude", recipe="agent", ...)
        db.step_upsert(run_id, "S6", status="complete", score=0.87, artifact_path="...")
        db.step_checkpoint(run_id, "S6", passed=True, note="Scores look good")
    """

    def __init__(self, url: str | None = None) -> None:
        self._url = url or os.environ.get("SPL_MEMORY_URL", f"sqlite:///{_DEFAULT_SQLITE}")
        self._backend, self._path = self._parse_url(self._url)
        self._conn: Any = None
        self._connect()
        self._init_schema()

    # ── Connection ────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_url(url: str) -> tuple[str, str]:
        if url.startswith("sqlite:///"):
            return "sqlite", url[len("sqlite:///"):]
        if url.startswith("postgresql://") or url.startswith("postgres://"):
            return "postgres", url
        # bare path → assume sqlite
        return "sqlite", url

    def _connect(self) -> None:
        if self._backend == "sqlite":
            path = Path(self._path)
            path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        else:
            try:
                import psycopg2
                import psycopg2.extras
                self._conn = psycopg2.connect(self._path)
                self._conn.autocommit = False
            except ImportError:
                raise RuntimeError(
                    "psycopg2 is required for PostgreSQL support: pip install psycopg2-binary"
                )

    def _init_schema(self) -> None:
        ddl = _DDL_SQLITE if self._backend == "sqlite" else _DDL_POSTGRES
        if self._backend == "sqlite":
            self._conn.executescript(ddl)
        else:
            with self._conn.cursor() as cur:
                for stmt in ddl.split(";"):
                    stmt = stmt.strip()
                    if stmt:
                        cur.execute(stmt)
            self._conn.commit()

    @contextmanager
    def _cursor(self) -> Generator:
        if self._backend == "sqlite":
            cur = self._conn.cursor()
            try:
                yield cur
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise
            finally:
                cur.close()
        else:
            cur = self._conn.cursor()
            try:
                yield cur
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise
            finally:
                cur.close()

    def _fetchall(self, sql: str, params: tuple = ()) -> list[dict]:
        if self._backend == "sqlite":
            rows = self._conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]
        with self._conn.cursor() as cur:
            import psycopg2.extras
            cur = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]

    def _fetchone(self, sql: str, params: tuple = ()) -> dict | None:
        rows = self._fetchall(sql, params)
        return rows[0] if rows else None

    def _execute(self, sql: str, params: tuple = ()) -> int:
        """Execute DML; return lastrowid (sqlite) or 0 (postgres)."""
        if self._backend == "sqlite":
            cur = self._conn.execute(sql, params)
            self._conn.commit()
            return cur.lastrowid or 0
        with self._conn.cursor() as cur:
            cur.execute(sql, params)
            self._conn.commit()
            return 0

    # ── 1. UI Config ──────────────────────────────────────────────────────────

    def config_set(self, namespace: str, key: str, value: Any) -> None:
        """Persist a UI config value (any JSON-serialisable type)."""
        v = json.dumps(value) if not isinstance(value, str) else value
        now = _now()
        if self._backend == "sqlite":
            self._execute(
                "INSERT INTO ui_config (namespace, key, value, updated_at) VALUES (?,?,?,?) "
                "ON CONFLICT(namespace, key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
                (namespace, key, v, now),
            )
        else:
            self._execute(
                "INSERT INTO ui_config (namespace, key, value, updated_at) VALUES (%s,%s,%s,%s) "
                "ON CONFLICT(namespace, key) DO UPDATE SET value=EXCLUDED.value, updated_at=EXCLUDED.updated_at",
                (namespace, key, v, now),
            )

    def config_get(self, namespace: str, key: str, default: Any = None) -> Any:
        """Retrieve a UI config value, returning default if absent."""
        row = self._fetchone(
            "SELECT value FROM ui_config WHERE namespace=? AND key=?"
            if self._backend == "sqlite" else
            "SELECT value FROM ui_config WHERE namespace=%s AND key=%s",
            (namespace, key),
        )
        if row is None:
            return default
        raw = row["value"]
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw

    def config_get_namespace(self, namespace: str) -> dict[str, Any]:
        """Return all key-value pairs for a namespace as a dict."""
        ph = "?" if self._backend == "sqlite" else "%s"
        rows = self._fetchall(
            f"SELECT key, value FROM ui_config WHERE namespace={ph} ORDER BY key",
            (namespace,),
        )
        result = {}
        for r in rows:
            try:
                result[r["key"]] = json.loads(r["value"])
            except (json.JSONDecodeError, TypeError):
                result[r["key"]] = r["value"]
        return result

    def config_delete(self, namespace: str, key: str) -> None:
        ph = "?" if self._backend == "sqlite" else "%s"
        self._execute(
            f"DELETE FROM ui_config WHERE namespace={ph} AND key={ph}",
            (namespace, key),
        )

    # ── 2. Workflow Sessions ──────────────────────────────────────────────────

    def session_start(
        self,
        workflow_name: str,
        session_id: str | None = None,
        spl_file: str | None = None,
        adapter: str | None = None,
        model: str | None = None,
        input_params: dict | None = None,
    ) -> str:
        """Record a new workflow session; return the session_id."""
        import uuid as _uuid
        sid = session_id or str(_uuid.uuid4())
        now = _now()
        params_json = json.dumps(input_params or {})
        ph = "?" if self._backend == "sqlite" else "%s"
        self._execute(
            f"INSERT INTO workflow_sessions "
            f"(session_id, workflow_name, spl_file, adapter, model, status, input_params, started_at) "
            f"VALUES ({ph},{ph},{ph},{ph},{ph},'running',{ph},{ph})",
            (sid, workflow_name, spl_file, adapter, model, params_json, now),
        )
        logger.debug("session_start %s (%s)", sid, workflow_name)
        return sid

    def session_complete(
        self,
        session_id: str,
        output: str | None = None,
        error: str | None = None,
        latency_ms: int = 0,
        tokens_used: int = 0,
        cost_usd: float = 0.0,
    ) -> None:
        status = "failed" if error else "completed"
        now = _now()
        ph = "?" if self._backend == "sqlite" else "%s"
        self._execute(
            f"UPDATE workflow_sessions SET status={ph}, output={ph}, error={ph}, "
            f"latency_ms={ph}, tokens_used={ph}, cost_usd={ph}, completed_at={ph} "
            f"WHERE session_id={ph}",
            (status, output, error, latency_ms, tokens_used, cost_usd, now, session_id),
        )

    def session_get(self, session_id: str) -> dict | None:
        ph = "?" if self._backend == "sqlite" else "%s"
        return self._fetchone(
            f"SELECT * FROM workflow_sessions WHERE session_id={ph}", (session_id,)
        )

    def sessions_recent(self, limit: int = 50) -> list[dict]:
        return self._fetchall(
            "SELECT * FROM workflow_sessions ORDER BY started_at DESC LIMIT "
            + ("?" if self._backend == "sqlite" else "%s"),
            (limit,),
        )

    def sessions_stats(self) -> dict:
        """Return aggregate stats: total, completed, failed, avg_latency_ms."""
        row = self._fetchone(
            "SELECT COUNT(*) AS total, "
            "SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) AS completed, "
            "SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) AS failed, "
            "AVG(latency_ms) AS avg_latency_ms, "
            "SUM(tokens_used) AS total_tokens, "
            "SUM(cost_usd) AS total_cost "
            "FROM workflow_sessions"
        )
        return dict(row) if row else {}

    # ── 3. Pipeline Runs ──────────────────────────────────────────────────────

    def pipeline_upsert(
        self,
        pipeline_name: str,
        run_label: str,
        recipe: str | None = None,
        model_alias: str | None = None,
        adapter: str | None = None,
        model_id: str | None = None,
        phase: int | None = None,
    ) -> int:
        """Insert or return existing pipeline_run; return run_id."""
        existing = self._fetchone(
            "SELECT id FROM pipeline_runs WHERE pipeline_name=? AND run_label=?"
            if self._backend == "sqlite" else
            "SELECT id FROM pipeline_runs WHERE pipeline_name=%s AND run_label=%s",
            (pipeline_name, run_label),
        )
        if existing:
            return existing["id"]

        now = _now()
        ph = "?" if self._backend == "sqlite" else "%s"
        if self._backend == "sqlite":
            run_id = self._execute(
                f"INSERT INTO pipeline_runs "
                f"(pipeline_name, run_label, recipe, model_alias, adapter, model_id, phase, started_at, updated_at) "
                f"VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph})",
                (pipeline_name, run_label, recipe, model_alias, adapter, model_id, phase, now, now),
            )
        else:
            with self._conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO pipeline_runs "
                    "(pipeline_name, run_label, recipe, model_alias, adapter, model_id, phase, started_at, updated_at) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
                    (pipeline_name, run_label, recipe, model_alias, adapter, model_id, phase, now, now),
                )
                run_id = cur.fetchone()[0]
                self._conn.commit()
        return run_id

    def pipeline_get(self, pipeline_name: str, run_label: str) -> dict | None:
        ph = "?" if self._backend == "sqlite" else "%s"
        return self._fetchone(
            f"SELECT * FROM pipeline_runs WHERE pipeline_name={ph} AND run_label={ph}",
            (pipeline_name, run_label),
        )

    def pipeline_update_status(self, run_id: int, status: str, notes: str | None = None) -> None:
        now = _now()
        ph = "?" if self._backend == "sqlite" else "%s"
        self._execute(
            f"UPDATE pipeline_runs SET status={ph}, notes=COALESCE({ph}, notes), updated_at={ph} WHERE id={ph}",
            (status, notes, now, run_id),
        )

    def pipelines_all(self, pipeline_name: str) -> list[dict]:
        ph = "?" if self._backend == "sqlite" else "%s"
        return self._fetchall(
            f"SELECT * FROM pipeline_runs WHERE pipeline_name={ph} ORDER BY run_label",
            (pipeline_name,),
        )

    # ── 4. Pipeline Steps ─────────────────────────────────────────────────────

    def step_upsert(
        self,
        run_id: int,
        step: str,
        status: str = "complete",
        artifact_path: str | None = None,
        score: float | None = None,
    ) -> None:
        """Insert or update a pipeline step record."""
        now = _now()
        if self._backend == "sqlite":
            existing = self._fetchone(
                "SELECT id FROM pipeline_steps WHERE run_id=? AND step=?", (run_id, step)
            )
            if existing:
                self._execute(
                    "UPDATE pipeline_steps SET status=?, artifact_path=COALESCE(?,artifact_path), "
                    "score=COALESCE(?,score), completed_at=? WHERE run_id=? AND step=?",
                    (status, artifact_path, score, now, run_id, step),
                )
            else:
                self._execute(
                    "INSERT INTO pipeline_steps (run_id, step, status, artifact_path, score, started_at, completed_at) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (run_id, step, status, artifact_path, score, now, now if status != "running" else None),
                )
        else:
            self._execute(
                "INSERT INTO pipeline_steps (run_id, step, status, artifact_path, score, started_at, completed_at) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s) "
                "ON CONFLICT(run_id, step) DO UPDATE SET "
                "status=EXCLUDED.status, "
                "artifact_path=COALESCE(EXCLUDED.artifact_path, pipeline_steps.artifact_path), "
                "score=COALESCE(EXCLUDED.score, pipeline_steps.score), "
                "completed_at=EXCLUDED.completed_at",
                (run_id, step, status, artifact_path, score, now, now if status != "running" else None),
            )
        # Update run updated_at
        self._execute(
            "UPDATE pipeline_runs SET updated_at=? WHERE id=?"
            if self._backend == "sqlite" else
            "UPDATE pipeline_runs SET updated_at=%s WHERE id=%s",
            (now, run_id),
        )

    def step_checkpoint(
        self, run_id: int, step: str, passed: bool, note: str | None = None
    ) -> None:
        """Record human checkpoint result for a step."""
        ph = "?" if self._backend == "sqlite" else "%s"
        self._execute(
            f"UPDATE pipeline_steps SET checkpoint_passed={ph}, "
            f"checkpoint_note=COALESCE({ph}, checkpoint_note) "
            f"WHERE run_id={ph} AND step={ph}",
            (1 if passed else 0, note, run_id, step),
        )

    def steps_for_run(self, run_id: int) -> list[dict]:
        ph = "?" if self._backend == "sqlite" else "%s"
        return self._fetchall(
            f"SELECT * FROM pipeline_steps WHERE run_id={ph} ORDER BY step",
            (run_id,),
        )

    def step_get(self, run_id: int, step: str) -> dict | None:
        ph = "?" if self._backend == "sqlite" else "%s"
        return self._fetchone(
            f"SELECT * FROM pipeline_steps WHERE run_id={ph} AND step={ph}",
            (run_id, step),
        )

    # ── 5. Dashboard queries ──────────────────────────────────────────────────

    def pipeline_scores_matrix(self, pipeline_name: str, step: str) -> list[dict]:
        """Return all (run_label, recipe, model_alias, score) rows for a step.

        Used by the Ablation Results page to populate the table without
        scanning the filesystem.
        """
        ph = "?" if self._backend == "sqlite" else "%s"
        return self._fetchall(
            f"""SELECT pr.run_label, pr.recipe, pr.model_alias, pr.adapter,
                       ps.score, ps.artifact_path, ps.checkpoint_passed,
                       ps.checkpoint_note, ps.completed_at
                FROM pipeline_runs pr
                JOIN pipeline_steps ps ON ps.run_id = pr.id
                WHERE pr.pipeline_name={ph} AND ps.step={ph}
                ORDER BY pr.recipe, pr.model_alias""",
            (pipeline_name, step),
        )

    def report_summary(self, pipeline_name: str) -> dict:
        """Return a summary dict suitable for a dashboard card."""
        runs = self.pipelines_all(pipeline_name)
        total = len(runs)
        complete = sum(1 for r in runs if r["status"] == "complete")

        # Count steps completed
        all_steps: list[dict] = []
        for r in runs:
            all_steps.extend(self.steps_for_run(r["id"]))

        steps_done = sum(1 for s in all_steps if s["status"] == "complete")
        checkpoints_passed = sum(1 for s in all_steps if s["checkpoint_passed"])
        scores = [s["score"] for s in all_steps if s["score"] is not None]
        mean_score = round(sum(scores) / len(scores), 3) if scores else None

        return {
            "pipeline_name": pipeline_name,
            "total_runs": total,
            "complete_runs": complete,
            "steps_done": steps_done,
            "checkpoints_passed": checkpoints_passed,
            "mean_score": mean_score,
            "score_count": len(scores),
        }

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def close(self) -> None:
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass

    def __enter__(self) -> "MemoryDB":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"MemoryDB(backend={self._backend!r}, path={self._path!r})"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


# ── Module-level singleton (shared across Streamlit reruns) ──────────────────

_instance: MemoryDB | None = None


def get_memory_db(url: str | None = None) -> MemoryDB:
    """Return the shared MemoryDB singleton, creating it on first call."""
    global _instance
    if _instance is None:
        _instance = MemoryDB(url)
    return _instance
