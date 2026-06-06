# SPL Kernel-Backed Execution Layer — Design Note

Status: first slice implemented (`spl3/kernel.py` + executor integration).
Target: `spl/` + `spl3/` runtime in `digital-duck/SPL.py`.

## Core decision

Replace the current stateless deterministic-execution path (the `run_python` stdlib tool
and `CREATE TOOL_API` dispatch) with a **persistent Python kernel session owned by the
executor**. Deterministic capability then comes from **pip-installable packages imported
into the kernel namespace**, not from new entries in the SPL stdlib.

Organizing principle (the thing this whole design serves):

> SPL owns **orchestration, typed workflow state, and the IR**. The kernel owns
> **Python execution**. Do not reinvent the Python layer inside SPL.

The stdlib stops being a place where every new capability has to be re-wrapped as an
`@spl_tool`. Capability surface becomes "anything you can `pip install` and `import`."

## Why

Two problems are solved at once:

1. **stdlib bloat.** Today each new deterministic capability is a new built-in tool (the
   catalog is already at 64). That grows without bound and makes SPL responsible for
   maintaining wrappers around the entire Python ecosystem. With a kernel, a new capability
   is `pip install X` + `import X` in the kernel — zero SPL stdlib growth.
2. **Statelessness.** The current `run_python` spawns a fresh subprocess per call
   (`subprocess.run([sys.executable, "-c", code])`), discarding all state between steps.
   A persistent kernel keeps variables, imported packages, and helper objects alive across
   a workflow run — which maps naturally onto SPL's `@variable` flow and agentic loops
   (the `self_refine` / ReAct patterns all carry state across iterations).

## Where it hooks in

The kernel sits **strictly under the deterministic (Logic) layer**. Three integration
points in the codebase:

- **`spl3/executor.py` — `_load_tool_apis`:** `CREATE TOOL_API` bodies exec into the
  kernel namespace instead of an isolated throwaway dict. The kernel becomes the **single
  exec context** for all deterministic Python: tool definitions and `run_python` calls
  share the same namespace, so a tool can `import requests` at definition time and the
  import is still live when the tool is called ten steps later.
- **`spl/stdlib.py` — `run_python`:** when a kernel is active, the executor overrides
  the stdlib tool registration so `CALL run_python(...)` dispatches to
  `kernel.exec_code()` instead of a subprocess. The subprocess fallback remains active
  when no kernel is present.
- **`spl3/executor.py` — `_exec_call`:** the self-healing retry wrapper sits here,
  catching `ToolFailed` whose `__cause__` is `ModuleNotFoundError` and triggering
  `pip install` + retry (opt-in, dev mode only).
- `GENERATE` is untouched. It stays on the adapter path. The kernel never sees the
  stochastic/semantic layer.

This keeps the syntactic/semantic boundary enforced at the *code* level: prompts go to
adapters, deterministic Python goes to the kernel, and the two never mix.

## The state boundary (most important rule)

SPL already owns a typed variable system (`@var TYPE := expr`, TEXT/INT/etc.,
COMMIT-status mapping, JSON-AST serialization in `ir.py`). **Do not move `@variables`
into the kernel namespace as their source of truth** — that would hand workflow state to
Python and strip away the type system, the optimizer's visibility, and the IR's ability
to record the run faithfully.

Instead:

- **Executor stays the source of truth** for typed `@variables`.
- **Kernel namespace holds Python-level intermediate state** — imported packages, heavy
  objects, things that should not round-trip through SPL's variable layer.
- **Marshaling contract:** before a deterministic call the executor *pushes* the needed
  inputs into the kernel; after, it *pulls* the result back into a typed `@variable`.
  First-slice marshaling covers TEXT/INT/FLOAT/JSON only — IMAGE/AUDIO/VIDEO types are
  out of scope until the contract is extended.

If `@variables` and the kernel namespace both try to be authoritative, the two state
models fight and the IR stops being a faithful record of the run.

## Two execution modes

Same executor interface; swap the kernel backend behind a flag.

- **Interactive / development mode** — in-process persistent namespace (`KernelSession`
  with a Python `dict`). Fast, shares live objects, trivial namespace injection. Good for
  authoring and testing. No isolation, no clean restart — acceptable for trusted dev.
  **Self-healing is available in this mode only.**
- **Measurement / verification mode** — out-of-process managed kernel (second slice,
  deferred). `restart_kernel()` gives a fresh "restart-and-run-all" per run, plus process
  isolation. This is the mode for ablation / round-trip experiments, and for safely
  running freshly generated (untrusted) code. **Self-healing is disabled unconditionally
  in this mode** — auto-installing packages mid-run would make the run non-reproducible
  and invalidate the ablation result.

The mode split is also the reproducibility discipline: measurement runs must restart the
kernel fresh each time, or stale state becomes an uncontrolled variable.

## Kernel backend options

| Option | Implementation | Isolation | Restart | Object sharing | Use for |
|---|---|---|---|---|---|
| In-process namespace | `dict` + `exec()` (current) | No | N/A | Direct | Dev / authoring |
| In-process IPython | `IPython.core.interactiveshell.InteractiveShell()` | No | No clean restart | `shell.push()` | Enhanced dev (future) |
| Out-of-process managed | `jupyter_client` `KernelManager` | Yes (separate process) | `restart_kernel()` | Serialized over ZeroMQ | Measurement / untrusted code |

**No-singleton rule (critical for batch execution):** the current implementation uses a
plain `dict` as the kernel namespace — one per `KernelSession` instance, fully isolated.
If/when the IPython backend is added, use `InteractiveShell()` (direct constructor),
**never** `InteractiveShell.instance()` (global singleton). SPL's batch runner
(`run_all.py`) uses `ThreadPoolExecutor` with up to 65+ simultaneous recipe runs; each
executor instance must have a completely independent kernel namespace.

## Kernel as deterministic/symbolic substrate

The two-layer split (`GENERATE` → adapter; deterministic → kernel) is forward-compatible
with delegating symbolic AI to the kernel. The kernel is not just "a place to run Python
scripts" — it is the **Logic substrate**: the execution home for any deterministic,
verifiable, or symbolic computation the workflow needs. Everything below is a
`pip install` away, zero SPL stdlib growth required.

### Constraint satisfaction and optimization

**Z3** (`pip install z3-solver`) — Microsoft's SMT solver (Satisfiability Modulo
Theories). Checks whether a set of logical/arithmetic constraints has a solution, and
finds one if so. In brief: you describe a problem in terms of variables and constraints
(`x + y == 10`, `x > 3`) and Z3 either finds values that satisfy all of them or proves
that no solution exists. Used heavily in formal verification, planning, and type
inference. A workflow step that must verify a logical property or find a valid assignment
can `import z3` in the kernel and use it directly — no SPL wrapper needed.

```python
# Example: verify that no integer x satisfies x^2 = -1
import z3
x = z3.Int('x')
s = z3.Solver()
s.add(x * x == -1)
print(s.check())  # unsat — correct
```

**OR-Tools** (`pip install ortools`) — Google's operations research toolkit. Includes a
CP-SAT solver (constraint programming), a linear/integer programming solver, and
specialized solvers for vehicle routing and scheduling. Where Z3 is about *logical*
satisfiability, OR-Tools is about *combinatorial optimization* — finding the best
assignment subject to constraints. Any problem SPL currently approximates with LLM
heuristics (scheduling, packing, assignment) can be handed to OR-Tools for an exact
solution.

```python
from ortools.sat.python import cp_model
model = cp_model.CpModel()
x = model.new_int_var(0, 100, 'x')
y = model.new_int_var(0, 100, 'y')
model.add(x + y == 50)
model.maximize(x - y)
solver = cp_model.CpSolver()
solver.solve(model)
print(solver.value(x), solver.value(y))  # 100, -50 (clamped: 100, 0 => depends on bounds)
```

### Logic programming and knowledge representation

**clingo** (`pip install clingo`) — Answer Set Programming (ASP) solver. You write
*facts* and *rules* in a Prolog-like language; the solver finds all *answer sets* (sets
of facts that satisfy all rules under the closed-world assumption). Natural fit for
planning problems, configuration validation, and knowledge bases where you want to
derive all valid conclusions from a set of premises.

```python
import clingo
ctl = clingo.Control()
ctl.add("base", [], """
    color(red). color(blue). color(green).
    different(X,Y) :- color(X), color(Y), X != Y.
""")
ctl.ground([("base", [])])
for model in ctl.solve(yield_=True):
    print(model)  # all pairs of different colors
```

**pyDatalog** (`pip install pyDatalog`) — Datalog engine in Python syntax. Logic
programming using Python decorators for rules and facts. Strong for recursive graph
queries, relational reasoning, and deriving new facts from existing ones — the kind of
reasoning that would otherwise require a graph database query.

```python
from pyDatalog import pyDatalog
pyDatalog.create_terms('parent, ancestor, X, Y, Z')
+parent('tom', 'bob')
+parent('bob', 'ann')
ancestor(X, Y) <= parent(X, Y)
ancestor(X, Y) <= parent(X, Z) & ancestor(Z, Y)
print(ancestor('tom', Y))  # [['bob'], ['ann']]
```

### Symbolic mathematics

**SymPy** (`pip install sympy`) — symbolic algebra, calculus, equation solving, number
theory, and combinatorics, all in pure Python. Unlike numerical libraries (numpy),
SymPy works with *exact* symbolic expressions. A workflow step that needs precise
mathematical reasoning (simplify an expression, solve an equation, compute an integral)
can delegate to SymPy for a guaranteed exact result.

```python
from sympy import symbols, solve, integrate, exp
x = symbols('x')
print(solve(x**2 - 4, x))          # [-2, 2]
print(integrate(exp(-x**2), (x, 0, 1)))  # sqrt(pi)*erf(1)/2
```

### Architectural consequence

The kernel's role is **Logic substrate** — not "Python script runner." The LLM adapter
handles stochastic/semantic reasoning; the kernel handles everything that can be computed
exactly: constraint satisfaction, logical inference, symbolic math, and standard Python
computation. As SPL workflows grow more sophisticated, the kernel absorbs the
deterministic half and the adapter concentrates on the irreducibly probabilistic half.

## Self-healing CALL (opt-in)

When a `CALL` to a kernel-registered tool raises `ModuleNotFoundError` (wrapped as
`ToolFailed` by the executor), the executor can automatically install the missing package
and retry. This is an **opt-in feature** enabled only in dev mode via
`SPL3Executor(kernel_enabled=True, self_healing=True)`.

### Retry protocol

1. Execute tool via `CALL` dispatch.
2. Catch `ToolFailed` where `isinstance(exc.__cause__, ModuleNotFoundError)`. Extract
   `exc.__cause__.name` (the missing module name, available since Python 3.3).
3. **First attempt:** `pip install <module_name>` directly. Works for the common case
   where the module name equals the package name: `requests`, `numpy`, `pandas`,
   `sympy`, `z3` → `z3-solver` (close enough for a first try).
4. **If retry still raises** `ModuleNotFoundError` (module name ≠ package name —
   `cv2`→`opencv-python`, `PIL`→`Pillow`, `sklearn`→`scikit-learn`,
   `bs4`→`beautifulsoup4`): escalate to the LLM adapter with a single micro-call:
   *"The Python module `cv2` is not installed. What is the exact pip package name?
   Reply with only the package name."* Install the answer; retry once more.
5. **Cap at 2 retries total.** If still failing, surface the original `ToolFailed` — do
   not loop.

### Why the LLM escalation is principled

The module-name ≠ package-name cases are a fixed, well-known mapping. The LLM call here
is not "ask the model to guess" — it uses the probabilistic layer to resolve a *lookup*
encoded in training data rather than in a static dict. A static dict in SPL would grow
and rot; the LLM call stays current for free. This is the **probabilistic layer assisting
the deterministic layer's self-repair**, not replacing it. One call, bounded retries,
clear fallback.

### Mode gate

| Mode | Self-healing |
|---|---|
| `mode="dev"`, `self_healing=True` | Enabled |
| `mode="dev"`, `self_healing=False` (default) | Disabled |
| `mode="measurement"` | Unconditionally disabled |

The IR logs each `pip_install` event (package name + success/failure) as an audit trail
so the run record remains faithful even when a package was auto-installed mid-run.

## Multi-language kernel dispatch (future)

The `runtime` field in `CREATE TOOL_API ... AS PYTHON $$ ... $$` is already parsed and
stored in `ToolAPINode.runtime`. This is the natural dispatch hook for future non-Python
kernels: `AS GO $$ ... $$` → Go kernel; `AS TYPESCRIPT $$ ... $$` → TypeScript kernel.

The long-term design is a **KernelDispatcher** — a dict of live sessions keyed by
runtime, lazily started on first use. `CREATE TOOL_API` routes to the matching session;
`CALL <tool>` dispatches to whichever session owns that tool's registration.

**Why deferred:** Go (`gophernotes`) and TypeScript (`tslab`) Jupyter kernels are
substantially less mature than the Python equivalent, and the companion runtimes
(`SPL.go`, `SPL.ts`) are behind `SPL.py` in feature coverage. First slice is
Python-only. The `KernelSession` abstraction is designed so Go/TS sessions slot in
without touching the executor logic.

**The splc validation win (when ready):** once mature Go/TS kernels are live, the
cross-runtime equivalence test (§ "Kernel as transpiler-validation harness") becomes
kernel-native: execute `splc`-generated Go in the Go kernel, compare execution traces
with the Python run in the Python kernel — no subprocess orchestration, single harness.

## stdlib shrink strategy

- **Stays SPL-native:** the genuine SPL primitives — `GENERATE`/`SELECT`/`EVALUATE`/
  `CALL`/`WHILE` semantics, token `OPTIMIZE`, the storage/RAG layer, adapter glue, the
  IR. These are not "Python," they are SPL.
- **Migrates to kernel + removal from stdlib:** utilities that are just Python wearing an
  `@spl_tool` hat — `http_get`, file I/O, numeric math, hashing. In a kernel these are
  `import requests`, `import pathlib`, `import math` inside a `CREATE TOOL_API` block.
  No separate package needed; the replacement is user-written TOOL_API definitions.

Deprecation schedule (everything stays in `spl-llm`, no separate package):
- v3.1: `run_python`, `http_get` soft-deprecated with doc notes.
- v3.2: file I/O group (`write_file`, `read_file`, `file_exists`, `make_dir`,
  `path_join`) and numeric math (`abs_val`, `round_val`, `ceil_val`, `floor_val`,
  `mod_val`, `power_val`, `sqrt_val`, `sign_val`, `clamp`) removed; users write
  `CREATE TOOL_API` with `pathlib`/`math` instead.
- Long-term: `run_python`, `http_get` removed entirely.

Net effect: the stdlib stops growing; the deterministic capability surface becomes PyPI.

## Kernel as transpiler-validation harness

Two distinct relationships between the kernel and `splc` targets — keep them separate:

- **Runtime dependency (forbidden):** generated LangGraph/Go/TS code must not depend on
  the kernel to run. Generated artifacts must be self-contained.
- **Test harness (encouraged):** the kernel *executes and checks* generated code in a
  validation loop. The artifact does not depend on the kernel; the kernel drives
  validation.

### Cross-runtime equivalence as a measurement

Run the same `.spl` two ways — natively through the executor, and through the
`splc`-generated target — on identical inputs **with the semantic (GENERATE) layer mocked
to fixed responses**, then diff execution traces. A match is empirical evidence that
transpilation preserves behavior: "runtime is a coordinate choice" becomes a measured
result rather than an assertion.

### Python vs non-Python targets

- **LangGraph (Python) target:** the kernel imports and runs it in-process.
- **Go / TypeScript targets:** the kernel acts as orchestrating harness — subprocess out
  to compile/run the binary, capture outputs, diff against native run.

## Boundaries and cautions

- **Kernel must not leak into the transpilers.** `spl3/splc/` emits standalone framework
  code that runs without a kernel. Keep "kernel in the native runtime" and "what the
  transpiler emits" as two separate stories.
- **Security.** A kernel executes arbitrary (possibly LLM-generated) Python. In-process
  only for trusted development; out-of-process + resource limits for measurement /
  untrusted code (second slice).
- **Dependency weight.** The first-slice kernel (`dict` + `exec()`) adds zero new
  dependencies. The IPython-backed dev enhancement (`pip install spl-llm[kernel]`) adds
  `ipython>=8.0`. The full measurement backend (future `spl-llm[kernel-full]`) adds
  `ipykernel` + `jupyter_client`. Keep the tiers separate so the core install stays lean.
- **stdout capture and threads.** `exec_code` captures stdout via `redirect_stdout`,
  which modifies the process-global `sys.stdout`. A module-level lock serializes captures
  across concurrent kernel sessions. For sequential async workflows this is a non-issue;
  for high-concurrency batch runs it is a brief serialization point, not a correctness
  hazard. The IPython backend (`capture_output()`) handles this internally.
- **Hidden-state hazard.** Persistent kernels accumulate stale state. Measurement mode
  restarts fresh per run; never measure on a warm kernel.

## Integration points

1. `spl3/kernel.py` — `KernelSession`: persistent namespace, `exec_code`,
   `define_tool`, `pip_install`.
2. `spl3/executor.py` — `SPL3Executor.__init__`: creates `KernelSession` when
   `kernel_enabled=True`; overrides `run_python` tool registration.
3. `spl3/executor.py` — `_load_tool_apis`: routes `CREATE TOOL_API` bodies through
   `kernel.define_tool()` when kernel is active.
4. `spl3/executor.py` — `_exec_call` / `_exec_call_inner`: self-healing retry wrapper.
5. `spl/ir.py` — how `@variables` serialize; defines the marshaling contract at the
   kernel boundary.
6. `spl3/splc/` — must remain kernel-free; confirm no transpiler path imports
   `spl3.kernel`.

## Open decisions

| Decision | Status |
|---|---|
| Default dev backend | **Resolved:** plain `dict` namespace (zero deps); IPython enhancement deferred |
| Batch safety | **Resolved:** per-executor `KernelSession` instance, no shared state |
| `CREATE TOOL_API` scope | **Resolved:** kernel is the exec context for all TOOL_API bodies |
| Marshaling format (in-process) | **Resolved:** direct Python object passing via namespace dict |
| Marshaling types (first slice) | **Resolved:** TEXT/INT/FLOAT/JSON; IMAGE/AUDIO/VIDEO deferred |
| Multi-language kernel | **Resolved:** Python-only first; Go/TS kernels deferred |
| Self-healing | **Resolved:** opt-in (`self_healing=True`), dev mode only |
| Kernel lifecycle | **Resolved:** one `KernelSession` per executor instance |
| `run_python` fate | **Resolved:** kernel override registered in `__init__`; subprocess fallback when no kernel |
| `@spl_tool` registration | **Resolved:** stdlib tools stay in `FunctionRegistry`; TOOL_API tools go to kernel |
| Language surface | **Resolved:** kernel stays runtime-internal; no new SPL syntax |
| IPython enhancement | Deferred to second slice (`spl-llm[kernel]` optional extra, `ipython>=8.0`) |
| Out-of-process backend | Deferred to third slice (`spl-llm[kernel-full]`, `ipykernel` + `jupyter_client`) |

## Minimal first slice (implemented)

1. `spl3/kernel.py` — `KernelSession`: plain `dict` namespace, `exec_code` (stdout
   capture with threading lock), `define_tool`, `pip_install`.
2. `SPL3Executor.__init__` — `kernel_enabled: bool`, `self_healing: bool` params;
   creates `KernelSession` and overrides `run_python` tool when `kernel_enabled=True`.
3. `_load_tool_apis` — routes `CREATE TOOL_API` bodies through `kernel.define_tool()`
   when kernel is active; falls back to isolated `exec()` when not.
4. `_exec_call` — self-healing retry wrapper (2 attempts, `ToolFailed.__cause__`
   inspection, LLM escalation on second attempt).
5. `_exec_call_inner` — the original dispatch logic extracted for retry support.
6. `pyproject.toml` — `kernel` optional extra (`ipython>=8.0`) for the future IPython
   backend; first-slice kernel needs no new deps.

Next slice: IPython-backed `KernelSession` (richer output, magic commands, `%pip`).
After that: out-of-process restartable backend for measurement mode.
