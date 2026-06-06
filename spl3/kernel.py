"""IPython kernel integration for SPL 3.0.

Provides a persistent IPython kernel session that runs alongside the SPL
executor.  Every ``CALL run_python(@code) INTO @result`` routes through
this kernel rather than spawning a fresh subprocess, so:

  - State (imports, variables, SymPy symbols) persists across CALL steps
    within the same session.
  - All pip-installed packages are available via ``import`` — no
    ``@spl_tool`` registration needed.

Usage
-----
::

    kernel = IPythonKernel()
    kernel.start()
    result = kernel.execute("1 + 1")       # -> "2"
    kernel.execute("import sympy; x = sympy.Symbol('x')")
    print(kernel.execute("sympy.diff(x**3, x)"))  # -> "3*x**2"
    kernel.shutdown()

Or via context manager::

    with IPythonKernel() as k:
        print(k.execute("2 ** 10"))        # -> "1024"

Scope
-----
``scope="session"`` (default) — one kernel shared across all CALL steps
within an executor session; state is cumulative.

``scope="workflow"`` — caller is responsible for restarting between
workflow runs when isolation is needed.

Return value
------------
``execute()`` returns the ``text/plain`` repr of the last expression
(``execute_result`` message), mirroring a Jupyter notebook cell.
If the last statement produces no expression result, stdout is returned.
Empty string if there is no output.

Errors
------
Any Python exception in the kernel raises ``KernelExecutionError``.
The SPL executor maps this to ``ToolFailed``.
"""

from __future__ import annotations

import logging
import queue
import re
import threading
from typing import Optional

_log = logging.getLogger("spl.kernel")

_ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')


class KernelExecutionError(RuntimeError):
    """Raised when the kernel returns an error reply (user-code exception)."""


class IPythonKernel:
    """Persistent IPython kernel session.

    Parameters
    ----------
    scope:
        ``"session"`` or ``"workflow"``.  Informational; lifecycle is
        managed by the caller.
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
        _log.info("IPythonKernel: starting (scope=%s, timeout=%.0fs)",
                  self.scope, self.timeout)
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

        Returns the ``text/plain`` repr of the last expression, or
        captured stdout if there is no expression result.

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
                raise TimeoutError(
                    f"IPython kernel did not respond within {self.timeout}s"
                )

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
