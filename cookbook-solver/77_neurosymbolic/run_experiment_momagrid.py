#!/usr/bin/env python3
"""
run_experiment_momagrid.py — Distributed variant for the Recipe-77 neurosymbolic experiment.

This script is a clone of run_experiment.py with Momagrid support enabled by default.
It demonstrates how distributing cells across the Momagrid hub reduces wall-clock time
compared to sequential execution. All cells are routed through the Momagrid hub (Level A),
and workers > 1 enables parallel cell dispatch (Level B).

Key differences from run_experiment.py:
  - --via-momagrid is enabled by default (use --no-momagrid to disable)
  - --workers defaults to 6 (tune to your GPU count; 3 workers = 1 cell/GPU)
  - Non-ollama models (m001 / claude_cli) are skipped automatically — momagrid
    workers only serve Ollama inference.  claude_cli is intentionally excluded:
    it serves as a reference ceiling in run_experiment.py (sequential), while
    this script measures the 9 open-source models under grid conditions.
  - Results still flow to the same local SQLite DB for unified analysis

Run with:
  export MOMAGRID_HUB_URL=http://192.168.0.184:9000
  python cookbook/77_neurosymbolic/run_experiment_momagrid.py              # 400 cells, 6 workers
  python cookbook/77_neurosymbolic/run_experiment_momagrid.py -m m001 -p p021 --workers 2   # smoke test

Expected speedup vs run_experiment.py (sequential):
  - Wall-clock time ≈ (total_cells / num_workers) × avg_cell_latency
  - With 6 workers on a 400-cell run: ~67 cells per worker = ~10-15 min speedup vs. ~60+ min sequential

Note: Requires conda activate spl123 + MOMAGRID_HUB_URL environment variable.

Architecture — distribution granularity and design rationale
============================================================

Momagrid dispatches at the LLM-CALL level, not the workflow level.

Each experiment cell runs as a separate `spl3 run` subprocess on the
REQUESTER host.  Inside that subprocess, the SPL executor orchestrates
the full workflow (WHILE loops, EVALUATE branches, CALL chains) locally.
Only GENERATE nodes — the probabilistic LLM calls — are routed through
the MomagridAdapter to the Hub, which dispatches each call to a WORKER
node that has the requested model loaded.

Two parallelism levels coexist in this script:

  Level A — LLM-call routing (--momagrid, default ON):
    effective_adapter() rewrites each model's adapter string to
    "momagrid:<label>", so every GENERATE inside the spl3 subprocess
    hits the Hub instead of a local Ollama instance.  The workflow
    orchestration still runs on the requester.

  Level B — cell-level concurrency (--workers N, default 6):
    ThreadPoolExecutor runs N cells concurrently.  Each cell is an
    independent spl3 subprocess; the Hub load-balances their LLM calls
    across all available worker nodes.  N > 1 requires --momagrid
    because local Ollama can only serve one model at a time.

Solver execution — always local, by design (DODA)
--------------------------------------------------
All deterministic computation runs on the REQUESTER host:

  - TOOL_API (solve_step_with_sympy, solve_step_with_sage):
    Python functions exec()'d into the spl3 executor's tool table.
    They import sympy / sage.all and run in-process.

  - SOLVE @var := expr / CALL run_python(@code):
    Executed on the local IPython kernel (spl3/kernel.py), started
    by the --kernel flag.

  - Lean REPL (LeanREPL.mathlib()):
    Runs as a local subprocess managed by the kernel session.

Worker nodes never see solver code — they only handle LLM inference.
This is the DODA invariant: the .spl file is the logical specification;
all physical decisions (provider, parallelism, infrastructure) are
resolved at execution time via --adapter and --model flags.

Kernel bottleneck — known limitation and mitigation
----------------------------------------------------
With Level B parallelism, each of the N concurrent `spl3 run`
subprocesses starts its own IPython kernel instance.  This means:

  - N solver arms run in parallel, each with its own kernel — no
    contention between cells.  Subprocess isolation gives us a natural
    "kernel pool" of size N without explicit pooling.

  - However, each kernel loads SymPy or Sage into its own process,
    consuming memory.  With N=6 workers and Sage (which loads PARI,
    GAP, etc.), this can use ~2-4 GB per worker.  Monitor RSS if
    running on memory-constrained machines.

  - If we ever move to in-process workflow execution (multiple workflows
    sharing a single executor), the single kernel WOULD become a
    bottleneck.  That path would require an explicit kernel pool
    (KernelSession pool with acquire/release) or per-workflow kernel
    scoping.  For now, subprocess isolation avoids this by construction.

  - On worker nodes (which only run Ollama inference), solver packages
    (sympy, sage, lean) are NOT required and should not be installed.
    The node registration contract is: GPU + Ollama + model weights.

Host tracking — requester vs response worker
----------------------------------------------
Each cell records two host identities:

  hostname         — the REQUESTER: the machine that runs this script,
                     orchestrates the workflow, and executes all solver
                     logic.  Set once via socket.gethostname().

  response_worker  — the WORKER(S): the Momagrid agent(s) that handled
                     the LLM calls for this cell.  Parsed from the spl3
                     CLI "Workers:" output line, which aggregates the
                     agent_name returned by the Hub for each GENERATE.
                     When an agent registers with the Hub, it provides
                     an agent_name (which may differ from its hostname
                     if the user configures a custom name).  If no
                     agent_name is set, the Hub defaults to hostname.
                     A single cell may hit multiple workers if the Hub
                     load-balances across them (e.g. solver arm: 2-3
                     GENERATE calls could land on different nodes).

  For local runs (--no-momagrid), response_worker is empty because the
  adapter is not Momagrid and GenerationResult.response_worker is "".
"""

import io
import json
import os
import re
import socket
import sqlite3
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

# Resolve spl3 even when the calling shell's PATH lacks the conda env's bin.
def _find_spl3() -> str:
    import shutil
    # 1. Already on PATH (conda env activated)
    found = shutil.which("spl3")
    if found:
        return found
    # 2. Active conda env via CONDA_PREFIX
    prefix = os.environ.get("CONDA_PREFIX", "")
    if prefix:
        c = Path(prefix) / "bin" / "spl3"
        if c.exists():
            return str(c)
    # 3. Same bin dir as the running Python
    c = Path(sys.executable).parent / "spl3"
    if c.exists():
        return str(c)
    # 4. Known spl123 env path (fallback)
    return "/opt/anaconda3/envs/spl123/bin/spl3"

_SPL3_BIN = _find_spl3()

import click

# ── SQLite persistence ────────────────────────────────────────────────────────
DB_PATH_DEFAULT = "cookbook/77_neurosymbolic/experiment_results.db"

# Pass criteria, per arm and rung:
#   solver + sympy/sage — the chain verified end-to-end
#   solver + lean       — the badge IS the status; only a kernel-checked
#                          proof counts (statement_checked / unfaithful /
#                          unverified are recorded but scored as fail)
#   llm_only            — fluent output with no verification, by construction
PASS_STATUSES_SOLVER   = {"complete"}
PASS_STATUSES_LEAN     = {"machine_proved"}
PASS_STATUSES_LLM_ONLY = {"complete", "unverified_success"}


def cell_is_pass(status: str, solver: str, backend: str) -> bool:
    if solver == "false":
        return status in PASS_STATUSES_LLM_ONLY
    if backend == "lean":
        return status in PASS_STATUSES_LEAN
    return status in PASS_STATUSES_SOLVER


def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id         TEXT,
            hostname       TEXT,
            source_file    TEXT    NOT NULL,
            mid            TEXT,
            label          TEXT,
            pid            TEXT,
            tier           TEXT,
            backend        TEXT,
            problem        TEXT,
            solver         TEXT,
            run            INTEGER,
            pass           INTEGER,
            status         TEXT,
            output_preview TEXT,
            llm_calls      REAL,
            latency_ms     REAL,
            steps          REAL,
            spl_log        TEXT,
            decomposition  TEXT,
            output         TEXT,
            notes          TEXT    DEFAULT '',
            imported_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source_file, mid, pid, solver, run)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS imports (
            source_file   TEXT PRIMARY KEY,
            source_type   TEXT NOT NULL DEFAULT 'csv',
            rows_total    INTEGER,
            rows_inserted INTEGER DEFAULT 0,
            log_path      TEXT,
            imported_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Schema migrations — safe to run on any existing DB
    for stmt in [
        "ALTER TABLE imports ADD COLUMN source_type TEXT NOT NULL DEFAULT 'csv'",
        "ALTER TABLE imports ADD COLUMN log_path TEXT",
        "ALTER TABLE results ADD COLUMN decomposition TEXT",
        "ALTER TABLE results ADD COLUMN output TEXT",
        "ALTER TABLE results ADD COLUMN backend TEXT",
        "ALTER TABLE results ADD COLUMN run_id TEXT",
        "ALTER TABLE results ADD COLUMN hostname TEXT",
        "ALTER TABLE results ADD COLUMN response_worker TEXT DEFAULT ''",
    ]:
        try:
            conn.execute(stmt)
        except sqlite3.OperationalError:
            pass  # column already exists
    conn.commit()
    return conn


def write_cell_to_db(
    conn: sqlite3.Connection,
    source_file: str,
    pid: str, mid: str, label: str, tier: str, backend: str, problem: str,
    solver: str, run: int,
    metrics: dict,
    hostname: str = "",
) -> None:
    run_id  = f"{mid}-{pid}-{'T' if solver == 'true' else 'F'}-{run}"
    status  = metrics["status"]
    passed  = int(cell_is_pass(status, solver, backend))
    llm     = int(metrics["llm_calls"])   if metrics["llm_calls"]  != "?" else None
    lat     = int(metrics["latency_ms"])  if metrics["latency_ms"] != "?" else None
    steps   = int(metrics["steps"])       if metrics["steps"]      != "?" else None
    preview = metrics["output_preview"]
    output  = metrics.get("output") or ""
    decomp  = json.dumps(metrics["decomposition"]) if metrics.get("decomposition") else None
    rw      = metrics.get("response_worker") or ""
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO results
                (run_id, hostname, source_file, mid, label, pid, tier, backend, problem,
                 solver, run, pass, status, output_preview, output,
                 llm_calls, latency_ms, steps, spl_log, decomposition,
                 response_worker)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (run_id, hostname, source_file, mid, label, pid, tier, backend, problem,
             solver, run, passed, status, preview, output,
             llm, lat, steps, metrics["spl_log"], decomp,
             rw),
        )
        conn.execute(
            "UPDATE imports SET rows_inserted = rows_inserted + 1 WHERE source_file = ?",
            (source_file,),
        )
        conn.commit()
    except Exception as exc:
        click.echo(f"\n  [DB WARNING] failed to write cell to DB: {exc}", err=True)


def parse_ids(values: tuple) -> list:
    """Expand comma/space-delimited strings from click multiple options.

    All three call styles produce the same result:
      -m m001 -m m007
      -m "m001,m007"
      -m "m001 m007"
      -m "m001, m007" -m m009
    """
    ids = []
    for v in values:
        ids.extend(part for part in re.split(r"[,\s]+", v) if part)
    return ids

# ── Axis 2: Model roster ─────────────────────────────────────────────────────
# id → (label, adapter, provider)
# IDs use zero-padded m001–m999 so alphabetical order == numerical order,
# making log filenames and automated parsing unambiguous at any scale.
MODELS = {
    "m001": ("sonnet-4-6",  "claude_cli",          "claude_cli"),
    "m002": ("gemma3",      "ollama:gemma3",       "ollama"),
    "m003": ("gemma4:e2b",  "ollama:gemma4:e2b",   "ollama"),
    "m004": ("qwen2.5",     "ollama:qwen2.5",      "ollama"),
    "m005": ("deepseek-v2:16b",       "ollama:deepseek-v2:16b",        "ollama"),
    "m006": ("phi3",        "ollama:phi3",         "ollama"),
    "m007": ("phi4",        "ollama:phi4",         "ollama"),
    "m008": ("llama3.2",    "ollama:llama3.2",     "ollama"),
    "m009": ("lfm2.5",      "ollama:lfm2.5",       "ollama"),
    "m010": ("rnj-1",       "ollama:rnj-1",        "ollama"),   # Essential AI 8B STEM model
}

# ── Thinking-mode models (reference, not used in experiments) ─────────────────
# Detected 2026-06-14 via scripts/detect_thinking_mode.py (probe: "what is 10!?").
# These models run extended chain-of-thought by default and exhaust the token
# budget before emitting structured output — incompatible with the expr|op
# contract required by the solver arm.  Do not add to MODELS without first
# disabling thinking mode (e.g. qwen3 /no_think flag, deepseek-r1 system prompt).
# id → (label, adapter, provider, indicator)
MODELS_THINK = {
    "t001": ("qwen3",        "ollama:qwen3",        "ollama", "Ollama thinking field"),
    "t002": ("deepseek-r1",  "ollama:deepseek-r1",  "ollama", "Ollama thinking field"),
    "t003": ("deepseek-r1:8b","ollama:deepseek-r1:8b","ollama","Ollama thinking field"),
    "t004": ("lfm2.5",       "ollama:lfm2.5",       "ollama", "found <think> tag"),
    "t005": ("qwen3.5:0.8b", "ollama:qwen3.5:0.8b", "ollama", "Ollama thinking field"),
    "t006": ("qwen3.5:4b",   "ollama:qwen3.5:4b",   "ollama", "Ollama thinking field"),
    "t007": ("qwen3.5:9b",   "ollama:qwen3.5:9b",   "ollama", "Ollama thinking field"),
    "t008": ("phi4",         "ollama:phi4",          "ollama", "verbose preamble (123 words before answer)"),
    "t009": ("tinyllama",    "ollama:tinyllama",     "ollama", "verbose preamble (98 words before answer)"),
}

# ── Axis 1: Problem battery (ordered easy → hard) ────────────────────────────
# id → (tier, backend, problem-text)
#
# Active (default 400-cell run): p001–p020 — 10 SymPy (T0–T2) + 10 Sage (T3–T5)
#   T0–T2 use SymPy: classical polynomial algebra, limits, Taylor series, trig
#   T3–T5 use Sage: integration with exact algebraic output, eigenvalues, ODEs,
#                   Laplace transforms, infinite sums
#
# Disabled (run explicitly with -p <id>):
#   p021–p024 (T6): Sage-only operations SymPy cannot do — re-enable once
#                   the core 400-cell results are in hand
#   p025–p029 (Lean): future work, needs mathematician collaborator for mathlib
PROBLEMS = {
    # ── Tier 0: single-step  [sympy] ─────────────────────────────────────────
    "p001": ("T0", "sympy", "differentiate x**4 - 2*x**2 + 1"),
    "p011": ("T0", "sympy", "simplify the rational expression (x**2 - 1) / (x - 1)"),

    # ── Tier 1: polynomial multi-step  [sympy] ───────────────────────────────
    "p002": ("T1", "sympy", "expand (x+1)**2, then factor the expanded form"),
    "p003": ("T1", "sympy", "differentiate 3*x**3-x, then factor if needed, finally solve for x"),
    "p004": ("T1", "sympy", "expand (x-2)**3, then differentiate the result, then simplify it, then factor that, then solve for x = 0"),
    "p012": ("T1", "sympy", "find the partial fraction decomposition of 1 / (x**2 - 1)"),

    # ── Tier 2: transcendental / limits / series / trig  [sympy] ────────────
    "p005": ("T2", "sympy", "differentiate exp(x) and simplify it if necessary"),
    "p006": ("T2", "sympy", "find the limit of sin(x) divided by x as x approaches 0"),
    "p013": ("T2", "sympy", "expand sin(x) as a Taylor series around x = 0, keeping terms up to degree 5"),
    "p014": ("T2", "sympy", "simplify sin(x)**2 + cos(x)**2 using trigonometric identities"),

    # ── Tier 3: integration / systems / linear algebra  [sage] ───────────────
    # Sage returns exact algebraic eigenvalues (e.g. (5±√33)/2, not floats)
    # and arc-trig integrals in closed form.
    "p007": ("T3", "sage", "integrate the square root of (4 minus x squared)"),
    "p008": ("T3", "sage", "find the integral of sin(x) times cos(x), then simplify the result"),
    "p015": ("T3", "sage", "solve the system of equations x + y = 5 and x - y = 1 for x and y"),
    "p016": ("T3", "sage", "find the eigenvalues of the 2 by 2 matrix with rows [1, 2] and [3, 4]"),

    # ── Tier 4: transforms / ODEs / summation / roots  [sage] ────────────────
    # Sage handles Laplace transforms, ODEs, and infinite sums with exact output
    # (sum of 1/n² = π²/6, not a decimal approximation).
    "p009": ("T4", "sage", "find the Laplace transform of exp(-2*t)"),
    "p017": ("T4", "sage", "solve the ordinary differential equation y'(x) = y(x) with initial condition y(0) = 1"),
    "p018": ("T4", "sage", "compute the symbolic sum of 1 over n squared from n equals 1 to infinity"),
    "p019": ("T4", "sage", "find all roots of x**4 - 1 and express each root in simplified form"),

    # ── Tier 5: expert  [sage] ───────────────────────────────────────────────
    "p010": ("T5", "sage", "find the general solution to the second order ODE y''(x) - 3*y'(x) + 2*y(x) = 0"),
    "p020": ("T5", "sage", "compute the inverse Laplace transform of s / (s**2 + 4), then verify by taking the Laplace transform of the result"),

    # ── Tier 6: Sage-only — operations SymPy cannot do  [DISABLED] ───────────
    # Re-enable with -p p021 etc. once core 400-cell run is complete.
    "p021": ("T6", "sage", "find the Galois group of the polynomial x**5 - x - 1 over the rational numbers"),
    "p022": ("T6", "sage", "determine whether the conic x**2 + y**2 = 3*z**2 has a rational point, and find one if it exists"),
    "p023": ("T6", "sage", "compute the rank of the elliptic curve y^2 + y = x^3 - x^2 - 10*x - 20"),
    "p024": ("T6", "sage", "factor the polynomial x**12 - 1 into irreducible factors over the rational numbers"),

    # ── Tier P: proof grade — Lean 4 + mathlib  [DISABLED, future work] ──────
    # Requires mathematician collaborator for mathlib tactics.
    # Run explicitly: -p p025 --backend lean (needs Lean + mathlib installed).
    "p025": ("P1", "lean", "addition of natural numbers is commutative"),
    "p026": ("P1", "lean", "the square of any real number is nonnegative"),
    "p027": ("P1", "lean", "for any two real numbers a and b, the absolute value of a + b is at most the absolute value of a plus the absolute value of b"),
    "p028": ("P2", "lean", "there are infinitely many prime numbers"),
    "p029": ("P2", "lean", "the sum of two even natural numbers is even"),
}

# Problems excluded from default runs; still accessible via explicit -p <id>.
# T6: enable after the core 400-cell results are in hand.
# Lean: future work — requires mathematician collaborator for mathlib.
DISABLED_PROBLEMS: set[str] = {
    "p021", "p022", "p023", "p024",   # T6 Sage-only (deferred)
    "p025", "p026", "p027", "p028", "p029",  # Lean (future work)
}

BACKENDS = ("sympy", "sage", "lean")
SCRIPT_DEFAULT = "cookbook/77_neurosymbolic/symbolic_math.spl"
LOG_DIR_DEFAULT = "cookbook/77_neurosymbolic/logs-spl"


def stream_run(cmd: list, log_file) -> tuple:
    """Run cmd, streaming stdout+stderr to console and log_file.

    Returns (returncode, metrics) where metrics is a dict with keys:
      status, llm_calls, latency_ms, steps
    parsed from spl3's standard output lines.

    spl3 emits three status-bearing lines per run, in this order:
      1. INFO:spl.executor:RETURN: N chars | status=X, arm=Y, backend=B, steps=Z
             Written at RETURN-WITH time — the most authoritative source.
             For the lean arm the badge IS the status (machine_proved /
             statement_checked / unfaithful / unverified).
      2. Status:  X
             spl3 summary line — sometimes says "complete" even when
             RETURN WITH carried a failure status (known framework bug).
      3. Output:  <text>
             The workflow's return value.  If it starts with a sentinel
             prefix ([SOLVER FAILURE], [PLAN FAILURE], etc.) that is the
             final and highest-priority override.

    Priority applied here: sentinel (3) > RETURN line (2) > Status: (1).
    """
    metrics = {
        "status": "unknown", "llm_calls": "?",
        "latency_ms": "?", "steps": "?", "spl_log": "?",
        "output_preview": "?", "output": "",
        "decomposition": None,
        "response_worker": "",
    }
    # Track where the current status value came from so lower-priority
    # sources cannot overwrite a better one.
    #   0 = default / not yet set
    #   1 = Status: summary line
    #   2 = RETURN line  (INFO:spl.executor:RETURN ... | status=X)
    #   3 = Output: sentinel prefix  (always final)
    status_priority = 0
    in_output       = False   # True while reading multi-line Output: block
    output_lines: list[str] = []

    # Decomposition accumulator — populated from [arm=solver] log lines
    decomp: dict = {"planned": None, "steps": [], "failed_at": None, "error": None}

    _RE_DECOMP_PLAN  = re.compile(r"\[arm=solver\] decomposed into (\d+) step")
    _RE_DECOMP_STEP  = re.compile(r"\[arm=solver\]\[step (\d+)/\d+\] (.+)")
    _RE_DECOMP_FAIL  = re.compile(r"\[arm=solver\] SOLVER FAILURE at step (\d+)/\d+: (.+)")

    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    if proc.stdout:
        for line in proc.stdout:
            print(line, end="", flush=True)
            log_file.write(line)
            s = line.strip()

            # End of output block — triggered by the next labeled section
            if in_output and (
                s.startswith("LLM calls:") or s.startswith("Log:")
                or s.startswith("Status:") or s.startswith("Output:")
                or s.startswith("Workers:")
            ):
                full = "\n".join(output_lines).strip()
                metrics["output"]         = full
                metrics["output_preview"] = full[:120]
                in_output = False

            if s.startswith("Status:"):
                # Priority 1 — only set if nothing better has been seen yet
                if status_priority < 1:
                    metrics["status"] = s.split(":", 1)[1].strip()
                    status_priority = 1

            elif s.startswith("Output:"):
                first_line = s.split(":", 1)[1].strip()
                output_lines = [first_line]
                in_output = True
                # Sentinel check on first line — sets status immediately
                if first_line == "(no COMMIT)":
                    metrics["status"] = "silent_failure"
                    status_priority = 3
                elif first_line.startswith("[SOLVER FAILURE]"):
                    metrics["status"] = "solver_error"
                    status_priority = 3
                elif first_line.startswith("[PLAN FAILURE]"):
                    metrics["status"] = "plan_error"
                    status_priority = 3
                elif first_line.startswith("[NARRATION FAILURE]"):
                    metrics["status"] = "narration_error"
                    status_priority = 3

            elif in_output:
                # Continuation line of the Output: block
                output_lines.append(line.rstrip("\n"))

            elif s.startswith("LLM calls:"):
                m = re.search(r"LLM calls:\s*(\d+)\s+Latency:\s*(\d+)ms", s)
                if m:
                    metrics["llm_calls"] = m.group(1)
                    metrics["latency_ms"] = m.group(2)

            elif s.startswith("Workers:"):
                metrics["response_worker"] = s.split(":", 1)[1].strip()

            elif s.startswith("Log:"):
                metrics["spl_log"] = s.split(":", 1)[1].strip()

            elif "| status=" in s:
                # Priority 2 — RETURN line written at RETURN-WITH execution time.
                # Format: INFO:spl.executor:RETURN: N chars | status=X, arm=Y, ...
                m_st    = re.search(r"\|\s*status=(\w+)", s)
                m_steps = re.search(r"\bsteps=(\d+)", s)
                if m_st and status_priority < 2:
                    metrics["status"] = m_st.group(1)
                    status_priority = 2
                if m_steps:
                    metrics["steps"] = m_steps.group(1)

            # Decomposition lines — only present for the solver arm on the
            # chain backends (sympy/sage)
            m_plan = _RE_DECOMP_PLAN.search(s)
            if m_plan:
                decomp["planned"] = int(m_plan.group(1))
                decomp["steps"] = []          # reset in case of retry
                decomp["failed_at"] = None
                decomp["error"] = None
            else:
                m_step = _RE_DECOMP_STEP.search(s)
                if m_step:
                    decomp["steps"].append({
                        "n":   int(m_step.group(1)),
                        "line": m_step.group(2).strip(),
                        "ok":  True,
                    })
                else:
                    m_fail = _RE_DECOMP_FAIL.search(s)
                    if m_fail:
                        n = int(m_fail.group(1))
                        decomp["failed_at"] = n
                        decomp["error"] = m_fail.group(2).strip()[:200]
                        # Mark the failed step
                        decomp["steps"].append({
                            "n":   n,
                            "line": m_fail.group(2).strip()[:120],
                            "ok":  False,
                        })

    proc.wait()
    # Flush output block if stream ended without a closing label
    if in_output and output_lines:
        full = "\n".join(output_lines).strip()
        metrics["output"]         = full
        metrics["output_preview"] = full[:120]

    # steps=0 + complete + non-empty output → pipeline was bypassed entirely;
    # the LLM free-formed a correct-looking answer without verification.
    if (metrics["status"] == "complete"
            and metrics["steps"] == "0"
            and metrics["output_preview"] not in ("?", "(no COMMIT)")):
        metrics["status"] = "unverified_success"
    # Attach decomposition only if we actually saw solver arm lines
    if decomp["planned"] is not None or decomp["steps"]:
        metrics["decomposition"] = decomp
    return proc.returncode, metrics


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--model",   "-m", "model_ids",    multiple=True,
              help="Model ID(s) — comma/space-delimited or repeatable: "
                   '-m "phi3,phi4"  or  -m phi3 -m phi4  (default: all). '
                   "Run --list to see IDs.")
@click.option("--problem", "-p", "problem_ids",  multiple=True,
              help="Problem ID(s) — comma/space-delimited or repeatable: "
                   '-p "p001 p021"  or  -p p001 -p p021  (default: all). '
                   "Run --list to see IDs.")
@click.option("--solver",  "-s", "solver_modes", multiple=True,
              default=("true", "false"), show_default=True,
              help='Solver arm(s): "true" (verifier on) or "false" (LLM only).')
@click.option("--backend", "-b", default=None,
              type=click.Choice(BACKENDS),
              help="Override the per-problem default backend for the whole "
                   "run (e.g. --backend sympy re-runs the battery on the "
                   "SymPy rung). Default: each problem's own backend.")
@click.option("--runs",    "-r", default=1,      show_default=True,
              help="Repetitions per (model × problem × solver) cell.")
@click.option("--script",  default=SCRIPT_DEFAULT, show_default=True,
              help="SPL script to execute.")
@click.option("--log-dir", default=LOG_DIR_DEFAULT, show_default=True,
              help="Directory for the markdown log output.")
@click.option("--db",      default=DB_PATH_DEFAULT, show_default=True,
              help="SQLite database path for persisting results.")
@click.option("--list",    "show_list", is_flag=True,
              help="Print all available model and problem IDs, then exit.")
@click.option("--dry-run", is_flag=True,
              help="Show the commands that would run without executing them.")
@click.option("--momagrid/--no-momagrid", "via_momagrid", default=True, show_default=True,
              help="Enable Momagrid hub dispatch (Level A). "
                   "Hub URL from MOMAGRID_HUB_URL env var.")
@click.option("--workers", "-w", default=6, show_default=True,
              help="Number of cells to run concurrently via Momagrid (Level B). "
                   "Requires --momagrid. Tune based on available agents: "
                   "typical LAN grid: 4-8 workers.")
def main(model_ids, problem_ids, solver_modes, backend, runs, script, log_dir,
         db, show_list, dry_run, via_momagrid, workers):
    """Run the Recipe-77 neurosymbolic experiment on Momagrid distributed grid.

    Wall-clock time measurement (Level B parallel dispatch):
      Expected speedup = (400 cells / num_workers) × avg_cell_latency
      With 6 workers: ~15min total vs. ~60min sequential
    """
    if show_list:
        click.echo("\nModel IDs  (use with -m):")
        for mid, (label, adapter, _) in MODELS.items():
            click.echo(f"  {mid:<12}  {label:<14}  {adapter}")
        click.echo("\nProblem IDs  (use with -p):")
        for pid, (tier, pbackend, text) in PROBLEMS.items():
            flag = "  [disabled]" if pid in DISABLED_PROBLEMS else ""
            click.echo(f"  {pid:<6}  [{tier}/{pbackend:<5}]  {text[:58]}{flag}")
        return

    if workers > 1 and not via_momagrid:
        raise click.UsageError("--workers > 1 requires --momagrid.")

    # Expand comma/space-delimited input before any validation or selection
    model_ids    = parse_ids(model_ids)
    problem_ids  = parse_ids(problem_ids)
    solver_modes = parse_ids(solver_modes)

    # Validate IDs early so the error message is clean
    for mid in model_ids:
        if mid not in MODELS:
            raise click.BadParameter(
                f"'{mid}' not found. Run --list to see available model IDs.",
                param_hint="--model")
    for pid in problem_ids:
        if pid not in PROBLEMS:
            raise click.BadParameter(
                f"'{pid}' not found. Run --list to see available problem IDs.",
                param_hint="--problem")

    # Resolve selections (preserve declaration order).
    # Disabled problems are skipped unless the user named them explicitly via -p.
    sel_models   = {k: v for k, v in MODELS.items()
                    if not model_ids   or k in model_ids}
    sel_problems = {k: v for k, v in PROBLEMS.items()
                    if (not problem_ids or k in problem_ids)
                    and (problem_ids or k not in DISABLED_PROBLEMS)}

    # Level A: build per-model adapter strings.
    # Momagrid is ENABLED by default; replaces each ollama adapter with
    # momagrid:<label>, routing every LLM call through the Hub.
    # Non-ollama models (e.g. claude_cli) cannot run on momagrid workers
    # and are excluded from the run entirely when --momagrid is active.
    def effective_adapter(label: str, orig_adapter: str) -> str:
        if not via_momagrid or not orig_adapter.startswith("ollama"):
            return orig_adapter
        return f"momagrid:{label}"

    if via_momagrid:
        skipped = {k: v for k, v in sel_models.items()
                   if not v[1].startswith("ollama")}
        if skipped:
            labels = ", ".join(f"{k} ({v[0]}/{v[1]})" for k, v in skipped.items())
            click.echo(f"Skipping (non-ollama, incompatible with momagrid): {labels}")
        sel_models = {k: v for k, v in sel_models.items()
                      if v[1].startswith("ollama")}

    use_solver_param = "symbolic_math" in script
    total = len(sel_models) * len(sel_problems) * len(solver_modes) * runs

    click.echo(f"\nModels   ({len(sel_models)}): {list(sel_models.keys())}")
    click.echo(f"Problems ({len(sel_problems)}): {list(sel_problems.keys())}")
    click.echo(f"Solver modes : {list(solver_modes)}"
               + ("" if use_solver_param else "  [ignored — not symbolic_math.spl]"))
    click.echo(f"Backend      : {backend or 'per-problem default'}")
    click.echo(f"Runs/cell    : {runs}")
    click.echo(f"Total cells  : {total}")
    if via_momagrid:
        hub_url = os.environ.get("MOMAGRID_HUB_URL", "http://localhost:9000")
        dispatch = f"Level B — {workers} parallel workers" if workers > 1 else "Level A — sequential"
        click.echo(f"Momagrid     : {hub_url}  [{dispatch}]")

    if dry_run:
        click.echo("\n--- DRY RUN ---")
        for mid, (label, orig_adapter, _) in sel_models.items():
            adapter = effective_adapter(label, orig_adapter)
            for pid, (tier, pbackend, problem) in sel_problems.items():
                cell_backend = backend or pbackend
                for solver_mode in solver_modes:
                    for run_no in range(1, runs + 1):
                        extra = (f" --param backend={cell_backend}"
                                 f" --param enable_solver={solver_mode}"
                                 if use_solver_param else "")
                        click.echo(
                            f"  [{mid}] [{tier}/{pid}] backend={cell_backend}"
                            f" run={run_no} solver={solver_mode}\n"
                            f"    spl3 run {script} --kernel --llm {adapter}"
                            f" --param problem=\"{problem[:55]}...\"{extra}"
                        )
        return

    hostname    = socket.gethostname()
    timestamp   = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path    = Path(log_dir) / f"recipe-77-momagrid-log-{timestamp}.md"
    source_file = f"exp-momagrid-{timestamp}"
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    # Open DB and register this experiment run.
    # Level B uses per-thread connections; the shared connection here is only
    # used for the initial import record and the sequential fallback.
    db_conn = init_db(db)
    db_conn.execute(
        """INSERT OR IGNORE INTO imports
               (source_file, source_type, rows_total, rows_inserted, log_path)
           VALUES (?, 'momagrid-experiment', ?, 0, ?)""",
        (source_file, total, str(log_path)),
    )
    db_conn.commit()

    click.echo(f"Hostname     : {hostname}")
    click.echo(f"Log          : {log_path}")
    click.echo(f"DB           : {db}  (source={source_file})\n")

    # Build the full cell list so Level B can dispatch them in any order.
    cells = [
        (mid, label, effective_adapter(label, orig_adapter), provider,
         pid, tier, pbackend, problem, solver_mode, run_no)
        for mid, (label, orig_adapter, provider) in sel_models.items()
        for pid, (tier, pbackend, problem) in sel_problems.items()
        for solver_mode in solver_modes
        for run_no in range(1, runs + 1)
    ]

    # Thread-safety: each worker opens its own SQLite connection (WAL mode is
    # not required — per-thread connections avoid all locking contention).
    _print_lock = threading.Lock()
    completed_count = [0]   # mutable int shared across threads

    def run_cell(cell_args: tuple) -> tuple:
        """Execute one (model × problem × solver × run) cell.

        Returns (cell_label, metrics, passed) for the caller to tally.
        Each invocation opens and closes its own SQLite connection so that
        Level B parallel dispatch never shares a connection across threads.
        """
        (mid, label, adapter, provider,
         pid, tier, pbackend, problem, solver_mode, run_no) = cell_args

        cell_backend = backend or pbackend
        cell = (f"[{pid}/{mid}] backend={cell_backend}"
                f" solver={solver_mode} run={run_no}")

        cmd = [_SPL3_BIN, "run", script, "--kernel",
               "--llm", adapter,
               "--param", f"problem={problem}",
               "--param", f"hostname={hostname}"]
        if use_solver_param:
            cmd += ["--param", f"backend={cell_backend}",
                    "--param", f"enable_solver={solver_mode}"]

        extra_md = (f" \\\n   --param backend={cell_backend}"
                    f" \\\n   --param enable_solver={solver_mode}"
                    if use_solver_param else "")

        # Print console header and write markdown log header atomically.
        with _print_lock:
            click.echo(f"\n{'='*54}")
            click.echo(f" {cell}")
            click.echo(f" {label} ({provider})")
            click.echo(f" Problem ({tier}): {problem[:65]}")
            click.echo(f"{'='*54}")
            with open(log_path, "a") as log:
                log.write(
                    f"\n## {label} ({provider})"
                    f" — backend={cell_backend}"
                    f" — solver={solver_mode} — run {run_no}\n\n"
                    f"_Tier: {tier} | Problem ID: `{pid}` | Host: `{hostname}`_\n\n"
                    f"```bash\n"
                    f"(spl123) $ spl3 run {script} --kernel --llm {adapter} \\\n"
                    f'   --param problem="{problem}" \\\n'
                    f'   --param hostname="{hostname}"{extra_md}\n'
                    f"```\n\n```output\n"
                )

        # Run the cell; stream output to console + a per-cell buffer.
        cell_log = io.StringIO()
        _, metrics = stream_run(cmd, cell_log)
        cell_output = cell_log.getvalue()

        with _print_lock:
            with open(log_path, "a") as log:
                log.write(cell_output)
                log.write("```\n\n")

        # Persist via a fresh per-thread connection.
        thread_conn = init_db(db)
        write_cell_to_db(
            thread_conn, source_file,
            pid, mid, label, tier, cell_backend, problem,
            solver_mode, run_no, metrics,
            hostname=hostname,
        )
        thread_conn.close()

        passed = cell_is_pass(metrics["status"], solver_mode, cell_backend)
        with _print_lock:
            completed_count[0] += 1
            outcome = "✓" if passed else "✗"
            worker_info = f"  worker={metrics['response_worker']}" if metrics.get("response_worker") else ""
            click.echo(
                f"\n  [{completed_count[0]}/{total}] {cell}"
                f" → {outcome} {metrics['status']}"
                f"  llm_calls={metrics['llm_calls']}"
                f"  latency={metrics['latency_ms']}ms"
                f"{worker_info}"
            )
        return cell, metrics, passed

    with open(log_path, "w") as log:
        log.write(f"# Recipe-77 Momagrid experiment run {timestamp}\n\n"
                  f"DB source: `{source_file}`\n"
                  f"Momagrid Hub: {os.environ.get('MOMAGRID_HUB_URL', 'http://localhost:9000')}\n"
                  f"Workers: {workers}\n\n")

    # Level B: parallel cell dispatch via ThreadPoolExecutor.
    # Each thread runs one cell; all write to the same SQLite file via
    # independent connections (safe; SQLite serialises writes internally).
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(run_cell, c): c for c in cells}
        for fut in as_completed(futures):
            try:
                fut.result()
            except Exception as exc:
                c = futures[fut]
                click.echo(f"\n  [ERROR] cell {c[0]}/{c[4]} failed: {exc}", err=True)

    db_conn.close()

    click.echo(f"\n{'='*54}")
    click.echo(f" Done — {completed_count[0]}/{total} run(s) completed.")
    click.echo(f" Log : {log_path}")
    click.echo(f" DB  : {db}  (source={source_file})")
    click.echo(f"{'='*54}\n")
    click.echo(f"Wall-clock analysis:")
    click.echo(f"   Compare this run's duration against run_experiment.py (sequential).")
    click.echo(f"   Expected speedup with {workers} workers: ~{workers}x faster")


if __name__ == "__main__":
    main()
