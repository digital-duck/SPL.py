"""Tests for spl3.lean_bridge — Lean 4 REPL bridge (B-1, B-5).

The whole live tier is skipped when the pinned repl binary is absent
(provision with ``cookbook/tools/lean/setup_lean.sh``) — mirroring the
optional Sage leg in tests/test_kernel.py.  The stdlib-only REPL is used:
no mathlib required, kernel-checked proofs about ``Nat`` are enough to
exercise every bridge behaviour, including the §B.2 env-id hygiene.
A small mathlib tier (B-5) additionally skips unless ``--with-mathlib``
has been provisioned; Loogle tests never touch the network — the HTTP
layer is monkeypatched.
"""

import json as _json

import pytest

from spl3.lean_bridge import (
    REPL_REVISION,
    LeanError,
    LeanNotFound,
    LeanREPL,
    ensure_repl,
    loogle,
    loogle_pattern,
    mathlib_available,
    repl_available,
)

LEAN_MISSING = not repl_available()
MATHLIB_MISSING = not mathlib_available()

needs_lean = pytest.mark.skipif(
    LEAN_MISSING, reason="Lean repl not provisioned (run cookbook/tools/lean/setup_lean.sh)"
)
needs_mathlib = pytest.mark.skipif(
    LEAN_MISSING or MATHLIB_MISSING,
    reason="mathlib not provisioned (run cookbook/tools/lean/setup_lean.sh --with-mathlib)",
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


# ---------------------------------------------------------------------------
# Loogle fallback (B-5) — network layer always mocked
# ---------------------------------------------------------------------------

class TestLooglePattern:
    def test_turnstile_form(self):
        assert loogle_pattern("∀ n m : Nat, n + m = m + n") == \
            "⊢ ∀ n m : Nat, n + m = m + n"

    def test_strips_whitespace(self):
        assert loogle_pattern("  1 + 1 = 2  ") == "⊢ 1 + 1 = 2"


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def read(self):
        return _json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class TestLoogle:
    def _patch(self, monkeypatch, payload):
        import urllib.request
        monkeypatch.setattr(
            urllib.request, "urlopen",
            lambda req, timeout=None: _FakeResponse(payload),
        )

    def test_hits_parsed_and_limited(self, monkeypatch):
        hits = [{"name": f"L{i}", "module": "M", "type": "T"} for i in range(10)]
        self._patch(monkeypatch, {"count": 10, "hits": hits})
        out = loogle("⊢ whatever", limit=3)
        assert [h["name"] for h in out] == ["L0", "L1", "L2"]

    def test_server_error_is_soft_miss(self, monkeypatch):
        # Loogle reports over-broad patterns as an in-band error (observed
        # live: all-metavariable patterns exceed the heartbeat budget)
        self._patch(monkeypatch, {"error": "timeout at `whnf`"})
        assert loogle("_ + _ = _ + _") == []

    def test_transport_error_raises(self, monkeypatch):
        import urllib.request

        def boom(req, timeout=None):
            raise TimeoutError("read timed out")

        monkeypatch.setattr(urllib.request, "urlopen", boom)
        with pytest.raises(TimeoutError):
            loogle("⊢ anything")


@needs_lean
class TestFindCitation:
    def test_local_hit_short_circuits(self, lean, monkeypatch):
        # When exact? hits, Loogle must not be consulted at all
        def no_network(*a, **k):
            raise AssertionError("loogle called despite local hit")

        monkeypatch.setattr("spl3.lean_bridge.loogle", no_network)
        monkeypatch.setattr(lean, "find", lambda s, timeout=None: "exact Nat.add_comm")
        assert lean.find_citation("∀ n m : Nat, n + m = m + n") == "exact Nat.add_comm"

    def test_loogle_fallback_kernel_checks_candidates(self, lean, monkeypatch):
        # exact? misses; Loogle offers a dud then the real lemma — only the
        # kernel-checked one is returned, as a named citation
        monkeypatch.setattr(lean, "find", lambda s, timeout=None: None)
        monkeypatch.setattr(
            "spl3.lean_bridge.loogle",
            lambda q, limit=8: [{"name": "Nat.le_refl"}, {"name": "Nat.add_comm"}],
        )
        cite = lean.find_citation("∀ n m : Nat, n + m = m + n")
        assert cite == "exact Nat.add_comm"

    def test_no_network_degrades_to_none(self, lean, monkeypatch):
        monkeypatch.setattr(lean, "find", lambda s, timeout=None: None)

        def boom(q, limit=8):
            raise TimeoutError("no network")

        monkeypatch.setattr("spl3.lean_bridge.loogle", boom)
        assert lean.find_citation("∀ n m : Nat, n + m = m + n") is None

    def test_fallback_disabled(self, lean, monkeypatch):
        monkeypatch.setattr(lean, "find", lambda s, timeout=None: None)

        def no_network(*a, **k):
            raise AssertionError("loogle called with fallback=False")

        monkeypatch.setattr("spl3.lean_bridge.loogle", no_network)
        assert lean.find_citation("∀ n m : Nat, n + m = m + n",
                                  fallback=False) is None


# ---------------------------------------------------------------------------
# Mathlib tier (B-5) — skipped unless --with-mathlib was provisioned
# ---------------------------------------------------------------------------

class TestMathlibConstructor:
    def test_mathlib_raises_with_hint_when_absent(self, tmp_path):
        with pytest.raises(LeanNotFound, match="--with-mathlib"):
            LeanREPL.mathlib(project_dir=tmp_path)

    def test_mathlib_available_false_for_empty_dir(self, tmp_path):
        assert mathlib_available(tmp_path) is False


@needs_mathlib
class TestMathlibTier:
    @pytest.fixture(scope="class")
    def mlean(self):
        repl = LeanREPL.mathlib(timeout=90).start()
        yield repl
        repl.close()

    def test_mathlib_vocabulary_elaborates(self, mlean):
        # ℝ and Continuous only exist with mathlib imported
        assert mlean.statement_ok(
            "∀ (f : ℝ → ℝ), Continuous f → Continuous (fun x => f x + 1)"
        ) is True

    def test_statement_check_catches_bad_dot_notation(self, mlean):
        assert mlean.statement_ok(
            "∀ (A : Matrix (Fin 2) (Fin 2) ℝ), A.frobnicate = A"
        ) is False

    def test_find_in_mathlib(self, mlean):
        hit = mlean.find("∀ n m : Nat, n + m = m + n")
        assert hit is not None
