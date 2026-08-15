"""Abstract persistence backend for SPL workflow durability."""

from __future__ import annotations
from abc import ABC, abstractmethod


class PersistenceBackend(ABC):
    """Contract that all persistence backends must satisfy.

    Lifecycle
    ---------
    1. ``start_workflow``  — called once at workflow entry; returns saved
       variable state if resuming, None if this is a fresh run.
    2. ``get_step_result`` — called before each GENERATE / CALL step; if a
       cached result exists the executor skips the LLM call and reuses it
       (exactly-once semantics).
    3. ``checkpoint``      — called after each GENERATE / CALL step with the
       result and the full @var snapshot, so a crash can be recovered from
       that point.
    4. ``finish_workflow`` — called when the workflow reaches RETURN or an
       unhandled exception.

    HITL
    ----
    ``wait_for_event`` / ``send_event`` implement the human-in-the-loop
    gate pattern:
        CALL wait_for_approval(@workflow_id, "approve_draft") INTO @decision
    An external system (CLI, web hook, dashboard) calls ``send_event`` to
    unblock the waiting workflow.
    """

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    @abstractmethod
    async def start_workflow(
        self,
        workflow_id: str,
        workflow_name: str,
        params: dict[str, str],
    ) -> dict[str, str] | None:
        """Register or resume a workflow run.

        Returns
        -------
        dict  : saved @var state from the last checkpoint — executor should
                warm its WorkflowState from this dict (resume path).
        None  : no prior state — this is a new run.
        """

    @abstractmethod
    async def get_step_result(
        self,
        workflow_id: str,
        step_idx: int,
        signature: str | None = None,
    ) -> str | None:
        """Return the cached result of step ``step_idx``, or None if not yet done.

        ``signature`` is a content hash of the step's unevaluated arguments
        plus its prompt template / tool source (see
        ``spl3.executor._content_signature``). When given and it doesn't
        match the signature stored at checkpoint time, the cached result is
        stale (the .spl script or the called tool changed since this
        workflow_id was last checkpointed) — treat it as a miss (return
        None) rather than serving the old result, so the step genuinely
        re-executes.
        """

    @abstractmethod
    async def checkpoint(
        self,
        workflow_id: str,
        step_idx: int,
        step_name: str,
        result: str,
        state_vars: dict[str, str],
        signature: str | None = None,
    ) -> None:
        """Persist the result of a completed step + current @var snapshot."""

    @abstractmethod
    async def finish_workflow(
        self,
        workflow_id: str,
        result: str,
        status: str,
    ) -> None:
        """Mark the workflow as finished (status = 'complete' | 'error' | …)."""

    # ── HITL ──────────────────────────────────────────────────────────────────

    @abstractmethod
    async def wait_for_event(
        self,
        workflow_id: str,
        event_key: str,
        timeout_seconds: float | None = None,
    ) -> str:
        """Block until an external event arrives; return its payload string."""

    @abstractmethod
    async def send_event(
        self,
        workflow_id: str,
        event_key: str,
        value: str,
    ) -> None:
        """Deliver an event to a waiting workflow (called from external system)."""
