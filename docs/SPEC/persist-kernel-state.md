# Persistent Kernel State for SOLVE/ASSERT

**Status**: Implemented — 2026-08-24
**Build**: 43/43 tests pass (`conda run -n spl123 pytest tests/test_kernel_store.py tests/test_solve_assert.py`)
**Target**: `spl3/` — `_exec_solve` / `_exec_assert` in `spl3/executor.py`  
**Scope**: Add a `KernelStore` that acts as **shared state between SPL and the Python kernel** — both sides read and write the same SQLite table so they stay in sync across steps, crashes, and subprocess boundaries.

## Build status

### Files created
| File | Lines | Notes |
|---|---|---|
| `spl3/kernel_store.py` | 107 | `KernelStore` class — full spec impl |
| `tests/test_kernel_store.py` | ~290 | 22 tests: store round-trip + Path B executor |

### Files modified
| File | Change |
|---|---|
| `spl3/executor.py` | `kernel_store` param in `__init__`; `_exec_solve` → 3-path dispatch; `_exec_assert` → 3-path dispatch; `execute_workflow` cleanup on success |
| `spl3/cli.py` | `--kernel-store PATH` flag; auto-enable at `~/.spl/workflows.db` when `--persistence` is active; threaded through `_run_workflow` → `Executor` |

### Deviations from spec

- **Section 4.2 Path A typed retrieval**: The spec calls a helper `_kernel_eval_obj(self._kernel, "_spl_solve_result")` that doesn't exist in the codebase. Implemented inline: after the kernel executes, a second `execute()` call serialises `_spl_solve_result` via `pickle.dumps(...).hex()` and deserialises in-process. Falls back to `str` on any error.

- **Section 4.3 ASSERT restore**: Implemented identically for both `_exec_solve` (Path A) and `_exec_assert` (Path A) — both restore the saved namespace before executing, so a restarted kernel won't hit `NameError` on either statement type.

- **Section 8 (dsh-spl bridge)**: Not implemented here — TypeScript-side change lives in the `dsh-spl` repo. The Python DB schema (`kernel_vars` table) is in place and compatible.

- **`spl3/persistence/sqlite_backend.py` migration**: Spec listed this as optional. Not touched — `KernelStore.__init__` creates the table itself, so there's no dependency on `SQLitePersistenceBackend`.

### Test coverage (new)
| Class | Tests | What's covered |
|---|---|---|
| `TestKernelStoreRoundTrip` | 12 | save/load int, list, dict; overwrite; multi-workflow isolation; delete; namespace filtering; non-picklable skip; `str` fallback; table creation |
| `TestSolvePathB` | 6 | basic eval; persist to store; cross-step accumulation; INPUT var substitution; exec error → ToolFailed; crash-resume (pre-populated DB) |
| `TestAssertPathB` | 3 | passes with DB namespace; fails and raises; SOLVE→ASSERT integration |
| `TestNoKernelNoStore` | 1 | no kernel + no store → ToolFailed (regression) |

---

## 1. Problem

`_exec_solve` and `_exec_assert` route to `IPythonKernel` — an out-of-process Jupyter kernel.  State (imports, Python variables, SymPy symbols) accumulates in-memory across steps within a session.  Two failure modes:

1. **Crash/restart** — the kernel process dies; the SQLite persistence backend restores the SPL string-store `@vars` but the Python namespace is blank.  A resumed `SOLVE @y := x + 1` fails with `NameError: name 'x' is not defined` even though `@x` is in the checkpoint.

2. **dsh-spl subprocess model** — `DshBackend.solve()` in `dsh-spl` spawns a fresh `python3 -c` per step.  There is no shared kernel.  Cross-step kernel state is simply impossible without an external store.

The existing `SQLitePersistenceBackend` checkpoints SPL string-store snapshots (`state_vars: dict[str, str]`) after each GENERATE/CALL step, but makes no provision for Python-typed kernel variables.

---

## 2. Core Idea: DB as the shared state layer

The key insight: **use the SQLite DB as the canonical state for both SPL and the kernel**, not just for durability.

```
                  ┌──────────────────────────────────┐
                  │  ~/.spl/workflows.db              │
                  │                                   │
                  │  kernel_vars(workflow_id, name,   │
                  │              value_pkl, step_seq) │
                  └──────────┬───────────────┬────────┘
                             │               │
                    writes   │               │  reads
                      ↓      │               │      ↓
              ┌──────────────┴──┐       ┌────┴─────────────────┐
              │  SPL executor   │       │  Python kernel        │
              │  (_exec_solve)  │       │  (exec() or python3)  │
              │                 │       │                        │
              │  After SOLVE:   │       │  Before SOLVE:         │
              │  save target    │       │  load all kernel_vars  │
              │  var to DB      │       │  into namespace        │
              └─────────────────┘       └────────────────────────┘
```

Every SOLVE step:
1. SPL executor loads the kernel namespace from DB
2. Executes the Python expression in that namespace
3. Saves the result (and any side-effect bindings) back to DB
4. Writes the string repr to the SPL `@var` store as usual

On resume after crash: step 1 just loads from DB — no kernel warmup needed.

---

## 3. KernelStore — new module `spl3/kernel_store.py`

Reuses the same `~/.spl/workflows.db` file as `SQLitePersistenceBackend` (one file for all workflow durability state).

### 3.1 Schema (add to existing DB)

```sql
CREATE TABLE IF NOT EXISTS kernel_vars (
    workflow_id TEXT    NOT NULL,
    name        TEXT    NOT NULL,
    value_pkl   BLOB    NOT NULL,   -- pickle.dumps(value)
    step_seq    INTEGER NOT NULL DEFAULT 0,
    updated_at  REAL    NOT NULL,
    PRIMARY KEY (workflow_id, name)
);
```

### 3.2 Implementation

```python
# spl3/kernel_store.py

import pickle
import sqlite3
import time
import logging
from pathlib import Path

_log = logging.getLogger("spl.kernel_store")

_DDL = """
CREATE TABLE IF NOT EXISTS kernel_vars (
    workflow_id TEXT NOT NULL,
    name        TEXT NOT NULL,
    value_pkl   BLOB NOT NULL,
    step_seq    INTEGER NOT NULL DEFAULT 0,
    updated_at  REAL NOT NULL,
    PRIMARY KEY (workflow_id, name)
);
"""


class KernelStore:
    """Shared state DB between the SPL executor and Python kernel.

    SPL writes SOLVE results here after each step.
    The kernel (exec() or python3 subprocess) loads from here before each step.
    Both sides stay in sync through the DB — the in-memory kernel is a cache,
    not the source of truth.
    """

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

        Called by the executor *before* each SOLVE/ASSERT execution.
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

        Called by the executor *after* each SOLVE step for the target @var.
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
        """Persist all picklable entries in *ns* atomically.

        Called after exec() to capture any side-effect bindings
        (helper variables, imports cached as module objects, etc.)
        in addition to the explicit SOLVE target.
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
```

---

## 4. Integration in `spl3/executor.py`

### 4.1 Constructor

```python
def __init__(self, *args, ..., kernel_store: "KernelStore | None" = None, **kwargs):
    ...
    self._kernel_store = kernel_store
```

### 4.2 `_exec_solve` — two execution paths

```python
async def _exec_solve(self, stmt: SolveStatement, state) -> None:
    code = self._resolve_python_template(stmt.python_template, state)

    if self._kernel is not None:
        # ── Path A: IPythonKernel (existing) ──────────────────────────
        kernel_code = (
            f"_spl_solve_result = {code}\n"
            f"print(str(_spl_solve_result))"
        )
        result = self._kernel.execute(kernel_code).strip()
        # Write SOLVE result to shared DB so it survives kernel restart
        if self._kernel_store and self._workflow_id:
            # Pull the typed object back from kernel for pickling
            typed = _kernel_eval_obj(self._kernel, "_spl_solve_result")
            self._kernel_store.save_var(
                self._workflow_id, stmt.target_variable, typed, self._step_counter
            )

    elif self._kernel_store is not None and self._workflow_id is not None:
        # ── Path B: stateless exec() with DB as shared namespace ──────
        # Load everything previously SOLVE'd into the local namespace
        ns = self._kernel_store.load_namespace(self._workflow_id)
        exec(compile(f"_spl_solve_result = {code}", "<spl-solve>", "exec"), ns)
        typed_result = ns["_spl_solve_result"]
        result = str(typed_result)
        # Write target var to shared DB (primary write)
        self._kernel_store.save_var(
            self._workflow_id, stmt.target_variable, typed_result, self._step_counter
        )
        # Write any side-effect bindings too (e.g. intermediate vars, imports)
        self._kernel_store.save_namespace(
            self._workflow_id, ns, self._step_counter
        )

    else:
        from spl.executor import ToolFailed
        raise ToolFailed(
            "SOLVE requires --kernel or --kernel-store; "
            "run with 'spl3 run --kernel-store ...'"
        )

    state.set_var(stmt.target_variable, result)
    _log.info("SOLVE @%s := %s -> %r", stmt.target_variable, code, result)
```

### 4.3 `_exec_assert` — restore namespace on kernel path

When the kernel restarts (crash recovery), its namespace is empty.  Restore from DB before asserting:

```python
async def _exec_assert(self, stmt: AssertStatement, state) -> None:
    code = self._resolve_python_template(stmt.python_template, state)

    if self._kernel is not None:
        # Restore any saved kernel state into a fresh kernel (no-op if already warm)
        if self._kernel_store and self._workflow_id:
            saved = self._kernel_store.load_namespace(self._workflow_id)
            if saved:
                self._kernel.execute(
                    f"_spl_restore = {repr(saved)}\n"
                    + "\n".join(f"{k} = _spl_restore[{k!r}]" for k in saved)
                    + "\ndel _spl_restore"
                )
        kernel_code = f"_spl_assert_result = bool({code})\nprint(_spl_assert_result)"
        result = self._kernel.execute(kernel_code)
        passed = result.strip() == "True"

    elif self._kernel_store is not None and self._workflow_id is not None:
        # Path B: load namespace from DB, eval in-process
        ns = self._kernel_store.load_namespace(self._workflow_id)
        ns.update(self.functions._builtins)
        ns.update(self.functions._tools)
        exec(compile(f"_spl_assert_result = bool({code})", "<spl-assert>", "exec"), ns)
        passed = bool(ns["_spl_assert_result"])

    else:
        # Existing kernel-free path: eval with tools namespace only
        ...  # unchanged from current code

    if not passed:
        ...  # OTHERWISE handling unchanged
```

### 4.4 Cleanup at workflow finish

```python
async def finish_workflow(self, workflow_id, result, status):
    await super().finish_workflow(workflow_id, result, status)
    if self._kernel_store and status == "complete":
        self._kernel_store.delete(workflow_id)
    # On error status: keep kernel vars for inspection/resume
```

---

## 5. Resume flow (crash recovery)

1. Operator restarts with `spl3 run --workflow-id abc123 --persistence --kernel-store`.
2. `start_workflow("abc123", ...)` returns last `state_vars` → executor restores SPL `@var` store.
3. Kernel is not started yet (or starts fresh — namespace is empty).
4. First SOLVE after restart: `load_namespace("abc123")` returns all previously persisted Python vars.
5. `exec(code, ns)` / `self._kernel.execute(restore_code + code)` sees them — no `NameError`.
6. DB is the source of truth; the in-memory kernel namespace is just a runtime cache.

---

## 6. CLI changes

```
spl3 run my.spl \
  --kernel-store ~/.spl/workflows.db \   # enable KernelStore (Path B by default)
  [--kernel]                             # optional: also start IPython kernel (Path A)
```

When `--persistence` is set and `--kernel-store` is not given, **auto-enable** `KernelStore` on the same DB path — zero extra config for users already using `--persistence`.

---

## 7. Serialization notes

- **`pickle`** handles numpy arrays, sympy expressions, custom dataclasses, tensors.  Use it; do not use `repr()`/`eval()` — they break on types without a faithful `repr`.
- **Non-picklable objects** (lambdas, file handles, generators, live connections) — skip silently with a `_log.debug` line.  These are re-created by re-running the code that produced them (imports etc. will be re-run from the namespace on the next step anyway).
- **Security** — `pickle.loads` is unsafe for untrusted data.  SPL specs are developer-authored trusted code (equivalent to a Makefile); the kernel store DB is local.  Do not expose the DB path to untrusted inputs.

---

## 8. dsh-spl bridge (Phase 1c)

`DshBackend.solve()` in `dsh-spl` currently calls `python3 -c ${JSON.stringify(script)}` — stateless.  To wire it to the shared DB:

```typescript
// In DshBackend
private kernelStorePath: string;  // e.g. ~/.spl/workflows.db
private workflowId: string;       // from runWorkflow opts

async solve(expr: string): Promise<string> {
  // Python preamble: load vars from DB, exec expr, save result back to DB
  const script = `
import sqlite3, pickle, sys
_db = sqlite3.connect(${JSON.stringify(this.kernelStorePath)})
_ns = {}
for _name, _pkl in _db.execute(
    "SELECT name, value_pkl FROM kernel_vars WHERE workflow_id=?",
    (${JSON.stringify(this.workflowId)},)):
    try: _ns[_name] = pickle.loads(_pkl)
    except: pass
exec(compile("_spl_result = ${expr.replace(/\\/g, '\\\\')}", "<spl>", "exec"), _ns)
print(_ns["_spl_result"])
_db.execute("INSERT OR REPLACE INTO kernel_vars VALUES (?,?,?,?,?)",
    (${JSON.stringify(this.workflowId)}, "_last_result",
     pickle.dumps(_ns["_spl_result"]), 0, __import__("time").time()))
_db.commit()
`;
  const result = await this.ctx.shell.run(
    this.ctx.shell.resolve({ command: `python3 -c ${JSON.stringify(script)}` }),
  );
  return result.stdout.text.trim();
}
```

This turns dsh-spl into a first-class kernel participant: it reads and writes the same `kernel_vars` table that spl3 uses.

---

## 9. Files to create / modify

| File | Change |
|---|---|
| `spl3/kernel_store.py` | **New** — `KernelStore` class |
| `spl3/executor.py` | Accept `kernel_store`, thread through `_exec_solve` / `_exec_assert` / finish |
| `spl3/persistence/sqlite_backend.py` | Add `kernel_vars` DDL migration in `__init__` (optional — `KernelStore.__init__` handles it) |
| `spl3/cli.py` | `--kernel-store` flag; auto-enable when `--persistence` is set |
| `tests/test_kernel_store.py` | **New** — unit tests for round-trip through `_exec_solve` (Path B) |
