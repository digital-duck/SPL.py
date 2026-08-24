"""KernelStore — shared SQLite state between the SPL executor and Python kernel.

SPL writes SOLVE results here after each step.
The kernel (exec() or python3 subprocess) loads from here before each step.
Both sides stay in sync through the DB — the in-memory kernel namespace is a
cache, not the source of truth.  Survives kernel crashes and subprocess restarts.
"""

from __future__ import annotations

import logging
import pickle
import sqlite3
import time
from pathlib import Path

_log = logging.getLogger("spl.kernel_store")

_DDL = """
CREATE TABLE IF NOT EXISTS kernel_vars (
    workflow_id TEXT    NOT NULL,
    name        TEXT    NOT NULL,
    value_pkl   BLOB    NOT NULL,
    step_seq    INTEGER NOT NULL DEFAULT 0,
    updated_at  REAL    NOT NULL,
    PRIMARY KEY (workflow_id, name)
);
"""


class KernelStore:
    """Shared state DB between the SPL executor and Python kernel."""

    def __init__(self, db_path: str = "~/.spl/workflows.db") -> None:
        self._path = Path(db_path).expanduser()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._path) as conn:
            conn.executescript(_DDL)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        return conn

    def load_namespace(self, workflow_id: str) -> dict[str, object]:
        """Load the full kernel namespace for a workflow from DB.

        Called by the executor before each SOLVE/ASSERT execution.
        Returns an empty dict for a fresh workflow (no prior SOLVE steps).
        """
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT name, value_pkl FROM kernel_vars WHERE workflow_id = ?",
                (workflow_id,),
            ).fetchall()
        ns: dict[str, object] = {}
        for row in rows:
            try:
                ns[row["name"]] = pickle.loads(row["value_pkl"])
            except Exception as e:
                _log.warning(
                    "kernel_store: skipping unrestorable var %r: %s", row["name"], e
                )
        return ns

    def save_var(
        self,
        workflow_id: str,
        name: str,
        value: object,
        step_seq: int = 0,
    ) -> None:
        """Persist one SOLVE target variable to the shared DB.

        Called by the executor after each SOLVE step for the target @var.
        """
        try:
            pkl = pickle.dumps(value)
        except Exception as e:
            _log.warning(
                "kernel_store: cannot pickle %r (%s); storing str repr", name, e
            )
            pkl = pickle.dumps(str(value))
        now = time.time()
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO kernel_vars VALUES (?,?,?,?,?)",
                (workflow_id, name, pkl, step_seq, now),
            )

    def save_namespace(
        self,
        workflow_id: str,
        ns: dict[str, object],
        step_seq: int = 0,
        skip_prefix: str = "_",
    ) -> None:
        """Persist all picklable entries in ns atomically.

        Called after exec() to capture side-effect bindings (helper variables,
        imports cached as module objects, etc.) in addition to the SOLVE target.
        """
        now = time.time()
        rows = []
        for k, v in ns.items():
            if k.startswith(skip_prefix):
                continue
            try:
                rows.append((workflow_id, k, pickle.dumps(v), step_seq, now))
            except Exception:
                pass  # non-picklable (lambda, generator, file handle) — skip
        if rows:
            with self._conn() as conn:
                conn.executemany(
                    "INSERT OR REPLACE INTO kernel_vars VALUES (?,?,?,?,?)", rows
                )

    def delete(self, workflow_id: str) -> None:
        """Remove all kernel vars for a workflow.

        Call at workflow finish (success or terminal error) to free storage.
        Keep on non-terminal failure to allow forensic inspection or resume.
        """
        with self._conn() as conn:
            conn.execute(
                "DELETE FROM kernel_vars WHERE workflow_id = ?", (workflow_id,)
            )
