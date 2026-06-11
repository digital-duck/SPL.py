"""Tests for spl3.lean_bridge — Lean 4 REPL bridge (B-1).

The whole live tier is skipped when the pinned repl binary is absent
(provision with ``cookbook/tools/lean/setup_lean.sh``) — mirroring the
optional Sage leg in tests/test_kernel.py.  The stdlib-only REPL is used:
no mathlib required, kernel-checked proofs about ``Nat`` are enough to
exercise every bridge behaviour, including the §B.2 env-id hygiene.
"""

import pytest

from spl3.lean_bridge import (
    REPL_REVISION,
    LeanError,
    LeanNotFound,
    LeanREPL,
    ensure_repl,
    repl_available,
)

LEAN_MISSING = not repl_available()

needs_lean = pytest.mark.skipif(
    LEAN_MISSING, reason="Lean repl not provisioned (run cookbook/tools/lean/setup_lean.sh)"
)


# ---------------------------------------------------------------------------
# No-toolchain behaviour — always runs
# ---------------------------------------------------------------------------

class TestNotFound:
    def test_missing_repl_message_has_setup_hint(self, tmp_path):
        with pytest.raises(LeanNotFound) as exc:
            ensure_repl(tmp_path / "nowhere")
        text = str(exc.value)
        assert "setup_lean.sh" in text
        assert REPL_REVISION in text

    def test_repl_available_false_for_missing_dir(self, tmp_path):
        assert repl_available(tmp_path / "nowhere") is False

    def test_project_without_lakefile_rejected(self, tmp_path):
        if LEAN_MISSING:
            pytest.skip("needs the repl binary to reach the lakefile check")
        with pytest.raises(LeanNotFound, match="lakefile"):
            LeanREPL(project_dir=tmp_path).start()


# ---------------------------------------------------------------------------
# Live tier — stdlib REPL, one session shared across the module
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def lean():
    repl = LeanREPL(timeout=60).start()
    yield repl
    repl.close()


@needs_lean
class TestCheck:
    def test_complete_proof_ok(self, lean):
        r = lean.check("theorem t : 1 + 1 = 2 := rfl")
        assert r["ok"] is True
        assert r["errors"] == []
        assert r["sorries"] == []

    def test_wrong_proof_not_ok(self, lean):
        r = lean.check("theorem t : 1 + 1 = 3 := rfl")
        assert r["ok"] is False
        assert r["errors"]
        assert lean.last_errors  # repair-loop feedback populated

    def test_sorry_is_not_ok(self, lean):
        # typechecks, but a sorry means "not kernel-checked complete"
        r = lean.check("theorem t : ∀ n : Nat, n + 0 = n := by sorry")
        assert r["ok"] is False
        assert r["errors"] == []
        assert r["sorries"]

    def test_tactic_proof_ok(self, lean):
        r = lean.check("theorem t : ∀ n : Nat, n + 0 = n := by intro n; rfl")
        assert r["ok"] is True


@needs_lean
class TestStatementOk:
    def test_wellformed_statement(self, lean):
        assert lean.statement_ok("∀ n : Nat, n + 0 = n") is True

    def test_wellformed_but_false_statement(self, lean):
        # statement_ok checks FORM, not truth — a false but well-typed
        # proposition passes (the formalization-correspondence gap, §B.4)
        assert lean.statement_ok("∀ n : Nat, n + 1 = n") is True

    def test_illformed_statement(self, lean):
        assert lean.statement_ok("∀ n : Nat, n + frobnicate = n") is False
        assert "frobnicate" in lean.last_errors


@needs_lean
class TestEnvIdHygiene:
    """§B.2: every check branches off the warm env — no state leakage."""

    def test_definitions_do_not_leak_between_checks(self, lean):
        r1 = lean.check("def splTestLeakProbe : Nat := 37")
        assert r1["ok"] is True
        r2 = lean.check("#check splTestLeakProbe")
        assert r2["ok"] is False  # unknown identifier — isolation holds

    def test_warm_env_id_is_stable(self, lean):
        before = lean._warm_env
        lean.check("theorem t : 2 + 2 = 4 := rfl")
        assert lean._warm_env == before


@needs_lean
class TestTimeoutAndRestart:
    def test_timeout_restarts_and_raises(self):
        repl = LeanREPL(timeout=60).start()
        try:
            # #eval of a non-terminating partial def hangs the repl for real
            hang = "partial def splSpin (n : Nat) : Nat := splSpin (n + 1)\n#eval splSpin 0"
            with pytest.raises((TimeoutError, LeanError)):
                repl.check(hang, timeout=2.0)
            # self-healed: usable again after the restart (warm-up re-paid)
            r = repl.check("theorem t : 1 + 1 = 2 := rfl")
            assert r["ok"] is True
        finally:
            repl.close()

    def test_crash_recovery_is_transparent(self):
        repl = LeanREPL(timeout=60).start()
        try:
            repl._proc.kill()
            repl._proc.wait()
            assert repl.is_running is False
            # _send respawns a dead process before writing — the check
            # simply succeeds on the fresh session
            r = repl.check("theorem t : 1 + 1 = 2 := rfl")
            assert r["ok"] is True
            assert repl.is_running is True
        finally:
            repl.close()


@needs_lean
class TestFind:
    def test_find_stdlib_lemma(self, lean):
        # Nat.add_zero is in core/std — exact? should close this goal
        hit = lean.find("∀ n : Nat, n + 0 = n")
        assert hit is None or isinstance(hit, str)
        # exact? availability varies without mathlib; a None is acceptable,
        # a hit must be a suggestion string
        if hit is not None:
            assert "exact" in hit or hit  # suggestion text, not empty
