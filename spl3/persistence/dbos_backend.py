"""DBOS-backed persistence backend — cloud-grade durable execution.

Requires:
    pip install dbos
    export DBOS_DATABASE_URL=postgresql://user:pass@host:5432/dbname

DBOS provides:
- Exactly-once step execution (each GENERATE / CALL is a @DBOS.step)
- Automatic crash recovery with resume from last checkpoint
- Built-in audit log and time-travel debugging
- Native HITL via send_event / recv_event

Architecture mapping
--------------------
SPL construct          → DBOS primitive
─────────────────────────────────────────
WORKFLOW execution     → @DBOS.workflow
GENERATE ... INTO @var → @DBOS.step  (LLM call)
CALL tool() INTO @var  → @DBOS.step  (tool call)
CALL wait_for_approval → DBOS.recv_event
CALL send_approval     → DBOS.send_event
"""

from __future__ import annotations

import json
import time
from .base import PersistenceBackend


class DBOSPersistenceBackend(PersistenceBackend):
    """DBOS-backed durable execution for SPL workflows.

    DBOS manages exactly-once step execution and crash recovery natively.
    This backend acts as the bridge: SPL's persistence hook calls land here
    and are delegated to DBOS primitives.

    Parameters
    ----------
    app_name  : DBOS application name (used in audit log and dashboard)
    """

    def __init__(self, app_name: str = "spl-workflow"):
        try:
            from dbos import DBOS  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "DBOS is not installed. Run: pip install dbos\n"
                "Then configure: export DBOS_DATABASE_URL=postgresql://..."
            ) from exc
        self._app_name = app_name
        self._dbos_initialized = False

    def _ensure_dbos(self):
        if not self._dbos_initialized:
            from dbos import DBOS
            DBOS(name=self._app_name)
            self._dbos_initialized = True

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    async def start_workflow(
        self,
        workflow_id: str,
        workflow_name: str,
        params: dict[str, str],
    ) -> dict[str, str] | None:
        """DBOS handles resume natively via SetWorkflowID context.

        For SPL's purposes we store initial params in DBOS workflow input;
        resume state is managed entirely by DBOS — returning None here signals
        that the SPL executor should let DBOS step-replay handle skipping.
        """
        self._ensure_dbos()
        # DBOS workflow context is set by the caller (spl3 run --workflow-id).
        # Nothing to do here; DBOS replays completed steps automatically.
        return None

    async def get_step_result(
        self,
        workflow_id: str,
        step_idx: int,
    ) -> str | None:
        """DBOS replays steps automatically — SPL should not skip manually.

        Return None always; let DBOS's @step replay handle idempotency.
        The caller (SPL executor) must be invoked inside a @DBOS.workflow
        context for this to take effect.
        """
        return None

    async def checkpoint(
        self,
        workflow_id: str,
        step_idx: int,
        step_name: str,
        result: str,
        state_vars: dict[str, str],
    ) -> None:
        """DBOS persists step output automatically after each @DBOS.step.

        We store a lightweight state-vars snapshot as a DBOS event so that
        the executor can read @var values on resume without re-executing steps.
        """
        from dbos import DBOS
        # Store snapshot as a named event keyed by step index
        DBOS.set_event(f"state:{step_idx}", json.dumps(state_vars))

    async def finish_workflow(
        self,
        workflow_id: str,
        result: str,
        status: str,
    ) -> None:
        from dbos import DBOS
        DBOS.set_event("workflow:result", json.dumps({"result": result, "status": status}))

    # ── HITL ──────────────────────────────────────────────────────────────────

    async def wait_for_event(
        self,
        workflow_id: str,
        event_key: str,
        timeout_seconds: float | None = None,
    ) -> str:
        """Block the workflow until an external event arrives.

        Example SPL usage:
            CALL wait_for_approval(@workflow_id, "approve_draft") INTO @decision;
        External system approves via:
            backend.send_event(workflow_id, "approve_draft", "approved")
        """
        from dbos import DBOS
        # DBOS.recv_event suspends the workflow durably — survives restarts
        timeout_ms = int(timeout_seconds * 1000) if timeout_seconds else None
        value = DBOS.recv_event(event_key, timeout_seconds=timeout_seconds)
        if value is None:
            raise TimeoutError(
                f"HITL event '{event_key}' not received within {timeout_seconds}s"
            )
        return str(value)

    async def send_event(
        self,
        workflow_id: str,
        event_key: str,
        value: str,
    ) -> None:
        """Send an event to a suspended workflow (from CLI, webhook, or dashboard)."""
        from dbos import DBOS
        DBOS.send_message(workflow_id, event_key, value)
