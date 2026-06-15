# SPL Workflow State Management & Durable Execution

## Motivation

SPL workflows today are stateless across crashes. If a 100-step research workflow
fails at step 87 (session limit, network error, OOM), the user must restart from
zero. For long-running or expensive workflows this is unacceptable.

We want:

1. **Crash recovery** — resume from the last completed GENERATE / CALL step
2. **Exactly-once semantics** — completed steps are never re-executed
3. **HITL (human-in-the-loop)** — pause indefinitely waiting for human approval,
   survive restarts while waiting
4. **Observability** — audit log of every step, its inputs/outputs, and timing
5. **Pluggability** — not locked to one library; DBOS is the preferred backend
   but others (Temporal, Prefect, SQLite-local) should plug in cleanly

---

## Design Principle: Persistence is Physical, Not Logical

Following DODA, the `.spl` file must not change regardless of whether durable
execution is enabled. Persistence is a physical decision resolved at runtime:

```bash
# stateless (default)
spl3 run workflow.spl --adapter ollama -m gemma3

# durable local (SQLite, zero deps)
spl3 run workflow.spl --adapter ollama -m gemma3 --persistence sqlite

# durable cloud (DBOS + PostgreSQL)
spl3 run workflow.spl --adapter ollama -m gemma3 --persistence dbos \
  --workflow-id my-run-001

# resume crashed run from last checkpoint
spl3 run workflow.spl --adapter ollama -m gemma3 --persistence sqlite \
  --workflow-id my-run-001
```

The `.spl` file is identical in all four cases.

---

## Architecture

```
spl3 run --persistence <backend>
    │
    ▼
SPL3Executor
    ├── _exec_generate_into()   ← checkpoint after each GENERATE
    ├── _exec_call()            ← checkpoint after each CALL
    └── execute_workflow()      ← lifecycle: start / finish
            │
            ▼
    PersistenceBackend  (abstract interface)
            │
            ├── SQLitePersistenceBackend   (local, zero deps)
            ├── DBOSPersistenceBackend     (cloud, pip install dbos)
            ├── TemporalPersistenceBackend (future)
            └── PrefectPersistenceBackend  (future)
```

### Key design choices

| Choice | Rationale |
|--------|-----------|
| Opt-in via `--persistence` flag | Zero overhead when not needed; existing workflows unchanged |
| Abstract `PersistenceBackend` interface | Swap backends without touching executor or .spl |
| Checkpoint after GENERATE and CALL only | These are the expensive / non-idempotent operations; assignments and EVALUATE are cheap and deterministic |
| @var snapshot stored at each checkpoint | Enables resume with correct variable state, not just step skipping |
| `--workflow-id` user-supplied | Lets users name runs meaningfully; auto-UUID when omitted |

---

## Abstract Interface (`spl3/persistence/base.py`)

```python
class PersistenceBackend(ABC):

    # ── Lifecycle ───────────────────────────────────────────────────────
    async def start_workflow(
        self, workflow_id: str, workflow_name: str, params: dict[str, str]
    ) -> dict[str, str] | None:
        """Register or resume. Returns saved @var state if resuming, else None."""

    async def get_step_result(
        self, workflow_id: str, step_idx: int
    ) -> str | None:
        """Return cached result of step N (exactly-once), or None if not done."""

    async def checkpoint(
        self, workflow_id: str, step_idx: int, step_name: str,
        result: str, state_vars: dict[str, str]
    ) -> None:
        """Persist result + full @var snapshot after completing a step."""

    async def finish_workflow(
        self, workflow_id: str, result: str, status: str
    ) -> None:
        """Mark workflow done."""

    # ── HITL ────────────────────────────────────────────────────────────
    async def wait_for_event(
        self, workflow_id: str, event_key: str, timeout_seconds: float | None
    ) -> str:
        """Suspend until an external event arrives (human approval gate)."""

    async def send_event(
        self, workflow_id: str, event_key: str, value: str
    ) -> None:
        """Deliver an event to a waiting workflow from an external system."""
```

---

## Backends

### SQLite (built-in, zero dependencies)

- Stores state in `~/.spl/workflows.db`
- Tables: `workflows`, `steps`, `events`
- `wait_for_event` polls on `asyncio.sleep(1s)` interval
- Suitable for local dev and single-node production
- No external services required

```bash
spl3 run workflow.spl --persistence sqlite --workflow-id run-001
# crash mid-run, then:
spl3 run workflow.spl --persistence sqlite --workflow-id run-001  # resumes
```

### DBOS (cloud-grade, optional)

- Requires: `pip install dbos` + `DBOS_DATABASE_URL=postgresql://...`
- Maps SPL lifecycle onto `@DBOS.workflow` / `@DBOS.step` primitives
- `wait_for_event` → `DBOS.recv_event` (durable suspend, survives restarts)
- `send_event` → `DBOS.send_message` (from CLI, webhook, or dashboard)
- Native audit log, time-travel debugging, and Momagrid-compatible observability
- DBOS Cloud option for zero-infra deployment

### Future backends (interface is already defined)

| Backend | Value-add over SQLite |
|---------|----------------------|
| **Temporal** | battle-tested at scale; TypeScript/Go SDKs if SPL expands |
| **Prefect** | data-pipeline native; good for ETL-style SPL workflows |
| **Redis** | sub-second polling for HITL; good for interactive workflows |
| **Momagrid** | native distributed state when running across grid nodes |

Adding a new backend = implement 6 methods in `PersistenceBackend` subclass.

---

## Executor Integration (`spl3/executor.py`)

Three overrides in `SPL3Executor` (no changes to `SPL2Executor`):

```python
class SPL3Executor(SPL2Executor):

    def __init__(self, ..., persistence=None, workflow_id=None):
        ...
        self._persistence = persistence      # PersistenceBackend | None
        self._workflow_id = workflow_id      # str | None
        self._step_counter = 0
        if persistence:
            self._register_hitl_tools()      # wait_for_approval, send_approval

    async def execute_workflow(self, stmt, params=None):
        # if persistence: start_workflow → warm state on resume → finish_workflow
        ...

    async def _exec_generate_into(self, stmt, state):
        # if persistence: get_step_result (skip if cached) → super() → checkpoint
        ...

    async def _exec_call(self, stmt, state):
        # if persistence: get_step_result (skip if cached) → super() → checkpoint
        ...
```

When `persistence=None` (default), all three methods delegate straight to `super()`
with zero overhead — the feature is completely invisible when not requested.

---

## HITL Pattern in SPL

No new keywords required. Human approval gates use standard `CALL`:

```spl
WORKFLOW review_and_publish
  INPUT @draft TEXT, @workflow_id TEXT
  OUTPUT @published TEXT
DO
  GENERATE edit_draft(@draft) INTO @polished;

  -- pause until a human approves (survives restarts)
  CALL wait_for_approval(@workflow_id, "approve_draft") INTO @decision;

  EVALUATE @decision
    WHEN contains("approved") THEN
      CALL publish(@polished) INTO @published;
    ELSE
      @published := "rejected";
  END;

  RETURN @published WITH status = "complete";
END;
```

External system (CLI, dashboard, webhook) unblocks the workflow:

```bash
spl3 workflow send-event --workflow-id run-001 --key approve_draft --value "approved"
```

Or from Python:
```python
backend = get_backend("sqlite")
await backend.send_event("run-001", "approve_draft", "approved")
```

---

## CLI Changes

Two new flags on `spl3 run`:

```
--persistence BACKEND   sqlite | dbos  (default: off)
--workflow-id ID        run identifier; auto-UUID when omitted
```

New subcommand for HITL:

```
spl3 workflow list                           # show all runs + status
spl3 workflow status --workflow-id ID        # steps completed, current state
spl3 workflow send-event --workflow-id ID --key KEY --value VALUE
spl3 workflow resume  --workflow-id ID ...   # shorthand for re-run with same ID
```

---

## Files to Create / Modify

| File | Action |
|------|--------|
| `spl3/persistence/__init__.py` | new — `get_backend(name)` factory |
| `spl3/persistence/base.py` | new — abstract `PersistenceBackend` |
| `spl3/persistence/sqlite_backend.py` | new — local zero-dep backend |
| `spl3/persistence/dbos_backend.py` | new — DBOS backend (optional install) |
| `spl3/executor.py` | modify — 3 method overrides + `__init__` params |
| `spl3/cli.py` | modify — `--persistence`, `--workflow-id` flags; `workflow` subcommand |
| `tests/test_persistence.py` | new — SQLite backend unit tests (no LLM calls) |

DBOS backend is gated behind `try: import dbos` — absence raises a clear
`ImportError` with install instructions, never silently degrades.

---

## Open Questions for Review

1. **Checkpoint granularity**: currently GENERATE + CALL only. Should assignments
   (`@var := expr`) inside a WHILE loop also checkpoint? Pro: finer resume
   granularity. Con: many cheap operations; SQLite write per iteration.

[WEN] ok at GENERATE + CALL level, we will refactor in future if finer checkpoint is required

2. **Sub-workflow step counting**: `step_counter` is per-executor instance.
   When `WorkflowComposer` spawns a child executor for a `CALL workflow_name()`
   sub-workflow, step indices restart at 0. Should we namespace by
   `workflow_id + "/" + workflow_name`, or use a global monotonic counter?

[WEN] will global counter be simpler for now?

3. **DBOS vs SQLite for HITL polling**: SQLite polls every 1s. For interactive
   dashboards this may feel slow. Redis pub/sub would give instant delivery —
   worth adding a Redis backend or is 1s acceptable?

[WEN] we use SQLite for developer mode, and PostgreSQL DB for production

4. **`spl3 workflow` subcommand scope**: list/status/send-event are immediately
   useful. `resume` is just `spl3 run --workflow-id ID` with saved params —
   should we store params in the DB so the user doesn't need to repeat them?

[WEN] yes

5. How should DBOS integration logic be re-used across local vs Momagrid deployment with minimum duplicate code

[WEN] we have to codebase - SPL.py and Momagrid