"""IPython kernel integration for SPL 3.0.

Two backends are provided:

``IPythonKernel`` (primary)
    Out-of-process IPython kernel via ``jupyter_client``.  Captures both
    stdout *and* expression results (``text/plain`` repr), mirroring a
    Jupyter notebook cell.  Requires ``jupyter_client`` + ``ipykernel``.

    Every ``CALL run_python(@code) INTO @result`` routes through this kernel.
    State (imports, variables, SymPy symbols) persists across CALL steps
    within the same session.  All pip-installed packages are immediately
    available — no ``@spl_tool`` registration needed.

    Usage::

        kernel = IPythonKernel()
        kernel.start()
        result = kernel.execute("1 + 1")       # -> "2"
        kernel.execute("import sympy; x = sympy.Symbol('x')")
        print(kernel.execute("sympy.diff(x**3, x)"))  # -> "3*x**2"
        kernel.shutdown()

    Or via context manager::

        with IPythonKernel() as k:
            print(k.execute("2 ** 10"))        # -> "1024"

``KernelSession`` (lightweight alternative)
    In-process ``exec()``-backed persistent namespace.  No extra deps.
    Returns captured stdout only (not expression results).  Useful for
    simple tool dispatch and ``CREATE TOOL_API`` bodies when the full
    IPython kernel is not needed.

Scope
-----
``scope="session"`` (default) — one kernel shared across all CALL steps
within an executor session; state is cumulative.

``scope="workflow"`` — caller is responsible for restarting between
workflow runs when isolation is needed.
"""

from __future__ import annotations

import asyncio
import importlib
import io
import logging
import queue
import re
import subprocess
import sys
import threading
from contextlib import redirect_stdout
from typing import Any, Optional

_log = logging.getLogger("spl.kernel")

_ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')

# Serialises redirect_stdout across threads for KernelSession.
_stdout_lock = threading.Lock()


# ---------------------------------------------------------------------------
# KernelSession — lightweight in-process backend (no extra deps)
# ---------------------------------------------------------------------------

class KernelSession:
    """Per-executor persistent Python execution context.

    Backed by an isolated namespace dict so concurrent executor instances
    never share state.  Returns captured stdout; does not capture expression
    results (use ``IPythonKernel`` for that).

    Parameters
    ----------
    mode:
        ``"dev"`` — persistent session; self_healing may be enabled.
        ``"measurement"`` — self_healing unconditionally disabled.
    self_healing:
        When True and mode is ``"dev"``, a ModuleNotFoundError triggers
        automatic ``pip install`` + retry.
    """

    def __init__(self, mode: str = "dev", self_healing: bool = False) -> None:
        self.mode = mode
        self.self_healing = self_healing and mode == "dev"
        self._ns: dict[str, Any] = {}
        _log.debug("KernelSession started (mode=%s, self_healing=%s)", mode, self.self_healing)

    def push(self, variables: dict[str, Any]) -> None:
        """Inject values into the kernel namespace before a call."""
        self._ns.update(variables)

    def pull(self, names: list[str]) -> dict[str, Any]:
        """Extract named values from the kernel namespace after a call."""
        return {name: self._ns.get(name) for name in names}

    def exec_code(self, code: str, context: dict[str, Any] | None = None) -> str:
        """Execute code in the persistent namespace; returns captured stdout."""
        if context:
            self.push(context)
        buf = io.StringIO()
        with _stdout_lock, redirect_stdout(buf):
            exec(compile(code, "<spl-kernel>", "exec"), self._ns)  # noqa: S102
        return buf.getvalue().strip()

    async def exec_code_async(self, code: str, context: dict[str, Any] | None = None) -> str:
        """Async wrapper — runs exec_code in a thread."""
        return await asyncio.to_thread(self.exec_code, code, context)

    def define_tool(self, name: str, code: str) -> Any:
        """Exec a CREATE TOOL_API body; returns the callable named *name*."""
        try:
            exec(compile(code, f"<tool_api:{name}>", "exec"), self._ns)  # noqa: S102
        except Exception as exc:
            raise RuntimeError(f"CREATE TOOL_API '{name}': failed to compile/exec — {exc}") from exc
        fn = self._ns.get(name)
        if fn is None:
            raise RuntimeError(f"CREATE TOOL_API '{name}': body must define a function named '{name}'.")
        if not callable(fn):
            raise RuntimeError(f"CREATE TOOL_API '{name}': '{name}' is not callable ({type(fn).__name__}).")
        return fn

    def pip_install(self, package: str) -> bool:
        """Install *package* and invalidate import caches. Returns True on success."""
        _log.info("KernelSession: pip install %s", package)
        proc = subprocess.run(
            [sys.executable, "-m", "pip", "install", package],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            _log.warning("pip install %s failed:\n%s", package, proc.stderr.strip())
            return False
        importlib.invalidate_caches()
        _log.info("KernelSession: %s installed successfully", package)
        return True


# ---------------------------------------------------------------------------
# KernelExecutionError
# ---------------------------------------------------------------------------

class KernelExecutionError(RuntimeError):
    """Raised when the IPython kernel returns an error reply."""


# ---------------------------------------------------------------------------
# IPythonKernel — full out-of-process IPython kernel (primary backend)
# ---------------------------------------------------------------------------

class IPythonKernel:
    """Persistent IPython kernel session via jupyter_client.

    Parameters
    ----------
    scope:
        ``"session"`` or ``"workflow"``.  Informational; lifecycle managed
        by the caller.
    timeout:
        Seconds to wait per cell execution.  Default 60 s.
    """

    def __init__(self, scope: str = "session", timeout: float = 60.0) -> None:
        self.scope    = scope
        self.timeout  = timeout
        self._km      = None
        self._kc      = None
        self._lock    = threading.Lock()
        self._started = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Launch the kernel process and connect the blocking client."""
        if self._started:
            return
        from jupyter_client import KernelManager
        _log.info("IPythonKernel: starting (scope=%s, timeout=%.0fs)", self.scope, self.timeout)
        self._km = KernelManager(kernel_name="python3")
        self._km.start_kernel()
        self._kc = self._km.blocking_client()
        self._kc.start_channels()
        self._kc.wait_for_ready(timeout=30)
        self._started = True
        _log.info("IPythonKernel: ready")

    def shutdown(self) -> None:
        """Stop channels and kill the kernel process."""
        if not self._started:
            return
        try:
            if self._kc is not None:
                self._kc.stop_channels()
            if self._km is not None:
                self._km.shutdown_kernel(now=True)
        except Exception:
            _log.debug("IPythonKernel: error during shutdown (ignored)", exc_info=True)
        finally:
            self._kc = None
            self._km = None
            self._started = False
            _log.info("IPythonKernel: shut down")

    def restart(self) -> None:
        """Restart the kernel, clearing all session state."""
        self.shutdown()
        self.start()

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute(self, code: str) -> str:
        """Execute *code* and return the result as a string.

        Returns the ``text/plain`` repr of the last expression, or captured
        stdout.  Empty string if there is no output.

        Raises
        ------
        KernelExecutionError
            On Python exceptions inside the kernel.
        TimeoutError
            If the cell does not finish within ``self.timeout`` seconds.
        """
        if not self._started:
            self.start()
        with self._lock:
            return self._run(code)

    def _run(self, code: str) -> str:
        kc = self._kc
        msg_id = kc.execute(code, silent=False, store_history=True)

        stdout_parts: list[str] = []
        execute_result: Optional[str] = None
        error_text: Optional[str] = None

        while True:
            try:
                msg = kc.get_iopub_msg(timeout=self.timeout)
            except queue.Empty:
                raise TimeoutError(f"IPython kernel did not respond within {self.timeout}s")

            if msg.get("parent_header", {}).get("msg_id") != msg_id:
                continue

            msg_type = msg["msg_type"]
            content  = msg.get("content", {})

            if msg_type == "stream" and content.get("name") == "stdout":
                stdout_parts.append(content.get("text", ""))

            elif msg_type in ("execute_result", "display_data"):
                execute_result = content.get("data", {}).get("text/plain", "")

            elif msg_type == "error":
                tb = "\n".join(content.get("traceback", []))
                error_text = (
                    f"{content.get('ename', 'Error')}: "
                    f"{content.get('evalue', '')}\n"
                    f"{_ANSI_RE.sub('', tb)}"
                )

            elif msg_type == "status":
                if content.get("execution_state") == "idle":
                    break

        if error_text is not None:
            raise KernelExecutionError(error_text)

        if execute_result is not None:
            return execute_result.strip()
        return "".join(stdout_parts).rstrip("\n")

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "IPythonKernel":
        self.start()
        return self

    def __exit__(self, *_) -> None:
        self.shutdown()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        return self._started
