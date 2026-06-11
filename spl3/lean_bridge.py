"""Lean 4 REPL bridge for SPL 3.0 — the third rung of the verifier ladder.

Implements B-1 of ``docs/DEV/sage_lean_integration_plan.md``: a thin Python
client around a persistent `leanprover-community/repl
<https://github.com/leanprover-community/repl>`_ process (JSON over
stdin/stdout), designed to live *inside* the IPython kernel so that
``SOLVE`` / ``ASSERT`` reach Lean without any new SPL constructs::

    SOLVE/ASSERT ──► IPython kernel ──► lean_bridge.LeanREPL ──► repl (persistent)

Why persistent: a cold ``lake env lean file.lean`` with mathlib costs
10–40 s per check; the REPL imports mathlib once and amortizes it — exactly
as the IPython kernel amortizes Python startup.  Same pattern, one level down.

**Env-id hygiene (§B.2, a correctness requirement).**  The REPL threads
environment state via ``env`` ids — every command returns a new one.  The
warm-up command's env id is captured once, and every subsequent check passes
that *same* id: each check gets a fresh environment with the warm imports
loaded, giving isolation *and* amortization.  Without this, definitions from
check N would leak into check N+1.

**Revision pinning (D2).**  The repl revision and the Lean toolchain move
together: the repl is cloned at :data:`REPL_REVISION` and built with the
toolchain named in its own ``lean-toolchain`` file.  A mathlib project, when
used, must pin the matching mathlib release tag.  Provisioning is scripted
in ``cookbook/tools/lean/setup_lean.sh``.

Usage::

    from spl3.lean_bridge import LeanREPL

    lean = LeanREPL().start()                      # stdlib-only, fast
    lean.check("theorem t : 1 + 1 = 2 := rfl")     # {"ok": True, ...}
    lean.statement_ok("∀ n : Nat, n + 0 = n")      # True (well-formed)
    lean.close()

    # With a lake project (e.g. mathlib pinned):
    lean = LeanREPL(project_dir="path/to/proj", imports=["Mathlib"]).start()

Strictly optional dependency: nothing here imports at SPL startup, and
:func:`repl_available` lets tests skip when the toolchain is absent.
This module must not touch ``spl3/cache/`` (B-4 is deferred until A-3 lands).
"""

from __future__ import annotations

import json
import logging
import os
import queue
import re
import subprocess
import threading
from pathlib import Path
from typing import Any, Optional

_log = logging.getLogger("spl.lean")

#: Pinned leanprover-community/repl revision (D2).  The Lean toolchain is
#: pinned transitively by the ``lean-toolchain`` file inside the repl checkout
#: at this tag — the two always move together.
REPL_REVISION = "v4.30.0"

#: Default location of the repl checkout (see setup_lean.sh).
_DEFAULT_REPL_DIR = Path(__file__).resolve().parent.parent / "cookbook" / "tools" / "lean" / "repl"


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class LeanError(RuntimeError):
    """Raised when the Lean REPL process misbehaves (crash, bad reply)."""


class LeanNotFound(RuntimeError):
    """Raised when the Lean toolchain / repl binary cannot be located."""


# ---------------------------------------------------------------------------
# Toolchain discovery
# ---------------------------------------------------------------------------

def _elan_bin_dir() -> Optional[Path]:
    """Directory containing elan-managed shims (lake, lean), if present."""
    d = Path.home() / ".elan" / "bin"
    return d if (d / "lake").exists() else None


def _subprocess_env() -> dict[str, str]:
    """Process environment with elan's shim directory prepended to PATH."""
    env = dict(os.environ)
    elan = _elan_bin_dir()
    if elan is not None:
        env["PATH"] = f"{elan}{os.pathsep}{env.get('PATH', '')}"
    return env


def default_repl_dir() -> Path:
    """Resolve the repl checkout directory.

    Order: ``$SPL_LEAN_REPL_DIR``, then the in-repo default
    ``cookbook/tools/lean/repl``.
    """
    env_dir = os.environ.get("SPL_LEAN_REPL_DIR")
    return Path(env_dir) if env_dir else _DEFAULT_REPL_DIR


def repl_binary(repl_dir: Optional[Path] = None) -> Path:
    """Path of the built repl executable inside *repl_dir*."""
    d = Path(repl_dir) if repl_dir else default_repl_dir()
    return d / ".lake" / "build" / "bin" / "repl"


def repl_available(repl_dir: Optional[Path] = None) -> bool:
    """True if the pinned repl binary has been built (tests use this to skip)."""
    try:
        return repl_binary(repl_dir).exists()
    except Exception:
        return False


def ensure_repl(repl_dir: Optional[Path] = None) -> Path:
    """Return the repl binary path, or raise :class:`LeanNotFound` with an
    actionable provisioning hint (never a bare stack trace)."""
    binary = repl_binary(repl_dir)
    if binary.exists():
        return binary
    raise LeanNotFound(
        f"Lean REPL binary not found at {binary}.\n"
        f"Provision the pinned toolchain (repl {REPL_REVISION}) with:\n"
        f"  bash cookbook/tools/lean/setup_lean.sh\n"
        f"(add --with-mathlib for the mathlib project; ~5 GB olean cache)\n"
        f"or point SPL_LEAN_REPL_DIR at an existing repl checkout."
    )


# ---------------------------------------------------------------------------
# LeanREPL — persistent REPL session
# ---------------------------------------------------------------------------

class LeanREPL:
    """Persistent Lean 4 REPL session (JSON over stdin/stdout).

    Parameters
    ----------
    project_dir:
        A lake project whose dependencies (e.g. mathlib) the REPL should
        see; the repl is launched via ``lake env`` from this directory.
        ``None`` (default) runs the repl bare — Lean stdlib only, which is
        cheap and sufficient for statement-shape checks and the test tier.
    repl_dir:
        Checkout containing the built repl binary.  Defaults to
        :func:`default_repl_dir`.
    imports:
        Modules imported once in the warm-up environment (e.g.
        ``["Mathlib"]``).  Every later check branches off this environment.
        ``None`` warms up an empty (stdlib) environment.
    timeout:
        Seconds to wait per check.  Default 60.  The warm-up gets
        ``warmup_timeout`` (mathlib import can take 10–40 s).
    """

    def __init__(self, project_dir: Optional[str | Path] = None,
                 repl_dir: Optional[str | Path] = None,
                 imports: Optional[list[str]] = None,
                 timeout: float = 60.0,
                 warmup_timeout: float = 120.0) -> None:
        self.project_dir    = Path(project_dir) if project_dir else None
        self.repl_dir       = Path(repl_dir) if repl_dir else default_repl_dir()
        self.imports        = list(imports) if imports else []
        self.timeout        = timeout
        self.warmup_timeout = warmup_timeout

        self._proc: Optional[subprocess.Popen] = None
        self._lines: "queue.Queue[Optional[str]]" = queue.Queue()
        self._reader: Optional[threading.Thread] = None
        # RLock, not Lock: a timeout inside _send (which holds the lock)
        # triggers restart() → _warmup() → _send() on the same thread.
        self._lock = threading.RLock()
        self._warm_env: Optional[int] = None

        #: Human-readable errors from the most recent check — fed back into
        #: `OTHERWISE RETRY GENERATE repair_proof(@proof, @@lean.last_errors@@)`.
        self.last_errors: str = ""
        #: Full parsed reply of the most recent check.
        self.last: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> "LeanREPL":
        """Spawn the repl process and warm up the base environment."""
        if self.is_running:
            return self
        binary = ensure_repl(self.repl_dir)

        if self.project_dir is not None:
            if not (self.project_dir / "lakefile.toml").exists() and \
               not (self.project_dir / "lakefile.lean").exists():
                raise LeanNotFound(
                    f"{self.project_dir} is not a lake project (no lakefile). "
                    f"See cookbook/tools/lean/setup_lean.sh."
                )
            cmd, cwd = ["lake", "env", str(binary)], self.project_dir
        else:
            cmd, cwd = [str(binary)], self.repl_dir

        _log.info("LeanREPL: starting %s (cwd=%s, imports=%s, repl %s)",
                  cmd[0], cwd, self.imports or "stdlib", REPL_REVISION)
        self._proc = subprocess.Popen(
            cmd, cwd=cwd, env=_subprocess_env(),
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, bufsize=1,
        )
        self._lines = queue.Queue()
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()
        self._warmup()
        _log.info("LeanREPL: ready (warm env id %s)", self._warm_env)
        return self

    def close(self) -> None:
        """Terminate the repl process."""
        if self._proc is not None:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=5)
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass
            finally:
                self._proc = None
                self._warm_env = None
                _log.info("LeanREPL: closed")

    def restart(self) -> "LeanREPL":
        """Restart the repl, re-paying the warm-up (used after timeout/crash)."""
        _log.warning("LeanREPL: restarting (warm-up will be re-paid)")
        self.close()
        return self.start()

    @property
    def is_running(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def __enter__(self) -> "LeanREPL":
        return self.start()

    def __exit__(self, *_) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Wire protocol — one JSON object out, one JSON object back, each
    # terminated by a blank line.
    # ------------------------------------------------------------------

    def _read_loop(self) -> None:
        proc = self._proc
        try:
            for line in proc.stdout:          # type: ignore[union-attr]
                self._lines.put(line)
        except Exception:
            pass
        self._lines.put(None)                 # EOF sentinel

    def _read_reply(self, timeout: float) -> dict[str, Any]:
        """Accumulate stdout lines until a blank line terminates the reply."""
        parts: list[str] = []
        while True:
            try:
                line = self._lines.get(timeout=timeout)
            except queue.Empty:
                raise TimeoutError(
                    f"Lean REPL did not reply within {timeout}s"
                )
            if line is None:
                raise LeanError(
                    "Lean REPL process exited unexpectedly"
                    + (f" (rc={self._proc.poll()})" if self._proc else "")
                )
            if line.strip() == "" and parts:
                break
            if line.strip() != "":
                parts.append(line)
        text = "".join(parts)
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise LeanError(f"Unparseable Lean REPL reply: {text!r}") from exc

    def _send(self, payload: dict[str, Any], timeout: Optional[float] = None) -> dict[str, Any]:
        """Send one command, return the parsed reply.

        On timeout or crash the repl is restarted (mirroring the kernel's
        self-healing) and the original exception is re-raised so the caller
        — typically an ``ASSERT ... OTHERWISE`` — can react.
        """
        if not self.is_running:
            self.start()
        with self._lock:
            try:
                assert self._proc is not None and self._proc.stdin is not None
                self._proc.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n\n")
                self._proc.stdin.flush()
                return self._read_reply(timeout or self.timeout)
            except (TimeoutError, LeanError, BrokenPipeError):
                self.restart()
                raise

    # ------------------------------------------------------------------
    # Checks
    # ------------------------------------------------------------------

    def _warmup(self) -> None:
        code = "\n".join(f"import {m}" for m in self.imports) or "-- spl warmup"
        reply = self._send({"cmd": code}, timeout=self.warmup_timeout)
        msgs = _messages(reply, "error")
        if msgs:
            raise LeanError(f"Lean warm-up failed:\n" + "\n".join(msgs))
        self._warm_env = reply.get("env")
        if self._warm_env is None:
            raise LeanError(f"Lean warm-up returned no env id: {reply!r}")

    def check(self, code: str, timeout: Optional[float] = None) -> dict[str, Any]:
        """Elaborate *code* in a fresh child of the warm environment.

        Returns ``{"ok", "errors", "sorries", "env", "messages"}`` where
        ``ok`` means *kernel-checked and complete*: no error-severity
        messages **and** no ``sorry`` placeholders.  Sets
        :attr:`last_errors` for repair-loop prompts.
        """
        reply = self._send({"cmd": code, "env": self._warm_env}, timeout)
        errors  = _messages(reply, "error")
        sorries = reply.get("sorries", [])
        ok = not errors and not sorries
        self.last = reply
        self.last_errors = "\n".join(errors)
        result = {
            "ok": ok,
            "errors": errors,
            "sorries": sorries,
            "env": reply.get("env"),
            "messages": reply.get("messages", []),
        }
        _log.info("LeanREPL.check: ok=%s errors=%d sorries=%d",
                  ok, len(errors), len(sorries))
        return result

    def statement_ok(self, stmt: str, timeout: Optional[float] = None) -> bool:
        """Use case 1 (§B.1): is *stmt* a well-formed Lean proposition?

        Elaborates ``example : <stmt> := by sorry``.  True iff it typechecks
        — the only acceptable diagnostic is the ``sorry`` warning.  This
        verifies the *formalization*, not the claim (see §B.4 on the
        formalization-correspondence gap).

        ``autoImplicit`` is disabled: with it on (Lean's default), an
        unbound identifier — a typo, or an LLM-hallucinated name — is
        silently auto-bound as an implicit argument and the statement
        *typechecks*.  Exactly the failure mode this check exists to catch.
        """
        reply = self._send(
            {"cmd": "set_option autoImplicit false in\n"
                    f"example : {stmt} := by sorry",
             "env": self._warm_env},
            timeout,
        )
        errors = _messages(reply, "error")
        self.last = reply
        self.last_errors = "\n".join(errors)
        ok = not errors
        _log.info("LeanREPL.statement_ok: %s", ok)
        return ok

    @property
    def feedback(self) -> str:
        """Repair-loop feedback for the most recent check: error diagnostics,
        or a note about remaining ``sorry`` placeholders, or ``""`` if clean.
        Designed to be fed straight back into a repair ``GENERATE`` prompt."""
        if self.last_errors:
            return self.last_errors
        if self.last.get("sorries"):
            return "the proof still contains sorry placeholder(s)"
        return ""

    def find(self, stmt: str, timeout: Optional[float] = None) -> Optional[str]:
        """Use case 3 (§B.1, stretch): probe mathlib for an existing proof.

        Runs ``example : <stmt> := by exact?`` and returns the suggestion
        text (a proof *term* — possibly multi-lemma; parsing out a single
        citation name is the caller's problem), or ``None`` if the search
        failed.  Cap *timeout* tighter than proof checking — search is
        open-ended.
        """
        reply = self._send(
            {"cmd": f"example : {stmt} := by exact?", "env": self._warm_env},
            timeout or min(self.timeout, 30.0),
        )
        self.last = reply
        for msg in reply.get("messages", []):
            data = msg.get("data", "")
            if "Try this:" in data:
                suggestion = data.split("Try this:", 1)[1].strip()
                # drop a leading editor-action tag like "[apply] "
                suggestion = re.sub(r"^\[\w+\]\s*", "", suggestion)
                _log.info("LeanREPL.find: %s", suggestion)
                return suggestion
        self.last_errors = "\n".join(_messages(reply, "error"))
        _log.info("LeanREPL.find: no hit")
        return None


def _messages(reply: dict[str, Any], severity: str) -> list[str]:
    """Extract formatted diagnostics of *severity* from a repl reply."""
    out = []
    for m in reply.get("messages", []):
        if m.get("severity") == severity:
            pos = m.get("pos") or {}
            loc = f"{pos.get('line', '?')}:{pos.get('column', '?')}"
            out.append(f"{loc}: {m.get('data', '')}")
    return out
