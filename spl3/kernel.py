"""
SPL Kernel Session — persistent Python execution substrate.

Each SPL3Executor instance owns one KernelSession.  The session maintains a
persistent namespace across CALL dispatches within the same workflow run, so
CREATE TOOL_API bodies and run_python calls share imports and state.

The executor remains the source of truth for typed @variables; the kernel
holds Python-level intermediate state (imported packages, helper objects,
symbolic solvers, etc.).

Usage::

    executor = SPL3Executor(adapter_name="ollama", kernel_enabled=True)
    # run_python and CREATE TOOL_API now route through the kernel

Self-healing (dev mode only)::

    executor = SPL3Executor(
        adapter_name="ollama",
        kernel_enabled=True,
        self_healing=True,
    )
    # ModuleNotFoundError on CALL dispatch triggers pip install + retry

Backend tiers
─────────────
First slice  (no extra deps)  : plain dict namespace + exec()  ← current
Second slice (spl-llm[kernel]): IPython InteractiveShell()       (future)
Third slice  (spl-llm[kernel-full]): out-of-process KernelManager (future)
"""

from __future__ import annotations

import asyncio
import importlib
import io
import logging
import subprocess
import sys
import threading
from contextlib import redirect_stdout
from typing import Any

_log = logging.getLogger("spl.kernel")

# Serialises redirect_stdout across threads — prevents concurrent kernel
# sessions from interleaving captured output on the global sys.stdout.
_stdout_lock = threading.Lock()


class KernelSession:
    """Per-executor persistent Python execution context.

    Backed by an isolated namespace dict so concurrent executor instances
    (e.g. ThreadPoolExecutor batch runs) never share state.

    Parameters
    ----------
    mode:
        ``"dev"`` — persistent session; self_healing may be enabled (default).
        ``"measurement"`` — reserved for the future out-of-process restartable
        backend; self_healing is unconditionally disabled to preserve
        reproducibility.
    self_healing:
        When True *and* mode is ``"dev"``, a ModuleNotFoundError on CALL
        dispatch triggers automatic ``pip install`` + retry, with optional
        LLM escalation for non-obvious module→package mappings.
    """

    def __init__(self, mode: str = "dev", self_healing: bool = False) -> None:
        self.mode = mode
        self.self_healing = self_healing and mode == "dev"
        self._ns: dict[str, Any] = {}
        _log.debug(
            "KernelSession started (mode=%s, self_healing=%s)", mode, self.self_healing
        )

    # ------------------------------------------------------------------ #
    # Namespace I/O                                                        #
    # ------------------------------------------------------------------ #

    def push(self, variables: dict[str, Any]) -> None:
        """Inject values into the kernel namespace before a call."""
        self._ns.update(variables)

    def pull(self, names: list[str]) -> dict[str, Any]:
        """Extract named values from the kernel namespace after a call."""
        return {name: self._ns.get(name) for name in names}

    # ------------------------------------------------------------------ #
    # Code execution                                                       #
    # ------------------------------------------------------------------ #

    def exec_code(self, code: str, context: dict[str, Any] | None = None) -> str:
        """Execute a Python code string in the persistent namespace.

        Returns captured stdout, or an empty string if the code produced none.
        Raises the underlying exception directly if execution fails.
        """
        if context:
            self.push(context)
        buf = io.StringIO()
        with _stdout_lock, redirect_stdout(buf):
            exec(compile(code, "<spl-kernel>", "exec"), self._ns)  # noqa: S102
        return buf.getvalue().strip()

    async def exec_code_async(
        self, code: str, context: dict[str, Any] | None = None
    ) -> str:
        """Async wrapper — runs exec_code in a thread to avoid blocking the loop."""
        return await asyncio.to_thread(self.exec_code, code, context)

    # ------------------------------------------------------------------ #
    # Tool definition                                                      #
    # ------------------------------------------------------------------ #

    def define_tool(self, name: str, code: str) -> Any:
        """Exec a CREATE TOOL_API body into the kernel namespace.

        Returns the callable defined by the body.  The body must define a
        function (or callable) named *name* at the top level.

        Raises RuntimeError with a clear message if compilation, execution,
        or the name check fails.
        """
        try:
            exec(compile(code, f"<tool_api:{name}>", "exec"), self._ns)  # noqa: S102
        except Exception as exc:
            raise RuntimeError(
                f"CREATE TOOL_API '{name}': failed to compile/exec body — {exc}"
            ) from exc

        fn = self._ns.get(name)
        if fn is None:
            raise RuntimeError(
                f"CREATE TOOL_API '{name}': body must define a function "
                f"named '{name}' at the top level."
            )
        if not callable(fn):
            raise RuntimeError(
                f"CREATE TOOL_API '{name}': '{name}' is not callable "
                f"(got {type(fn).__name__})."
            )
        return fn

    # ------------------------------------------------------------------ #
    # Dependency management                                                #
    # ------------------------------------------------------------------ #

    def pip_install(self, package: str) -> bool:
        """Install *package* into the running Python environment.

        Returns True on success.  Invalidates the import system's path caches
        so the new package is immediately importable without restarting.
        """
        _log.info("KernelSession: pip install %s", package)
        proc = subprocess.run(
            [sys.executable, "-m", "pip", "install", package],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            _log.warning("pip install %s failed:\n%s", package, proc.stderr.strip())
            return False
        importlib.invalidate_caches()
        _log.info("KernelSession: %s installed successfully", package)
        return True
