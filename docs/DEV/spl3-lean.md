# SPL × Lean 4 — Proof-Grade Verification (Verifier Ladder, Part B)

> **Status:** **B-1 shipped, B-3 shipped, B-2 core shipped, B-5 seeded**
> (2026-06-11; 15/15 bridge tests green against the live REPL, recipe 76
> verified end-to-end on both proof paths). B-4 (`machine_proved` badge in
> cache provenance) is next. Design:
> [`sage_lean_integration_plan.md`](./sage_lean_integration_plan.md) §3.
> SageMath ([Part A, complete](./spl3-sagemath.md)) widens verification
> *coverage*; Lean raises the *ceiling*: SymPy/Sage verify **instances**
> (this eigenpair works), Lean verifies **statements** (the theorem itself).

---

## 1. What shipped (B-1) — `spl3/lean_bridge.py`

A thread-safe synchronous client around a persistent
[`leanprover-community/repl`](https://github.com/leanprover-community/repl)
process (JSON over stdin/stdout):

```
SOLVE/ASSERT ──► IPython kernel ──► lean_bridge.LeanREPL ──► repl (persistent)
```

| Piece | Behavior |
|---|---|
| `LeanREPL(project_dir=, imports=, timeout=60, warmup_timeout=120)` | `project_dir=None` (default) runs the repl **bare — Lean stdlib only**: cheap warm-up, sufficient for statement-shape checks and the test tier. Point `project_dir` at a lake project (launched via `lake env`) and `imports=["Mathlib"]` for the full library. |
| **env-id hygiene** (§B.2) | Warm-up elaborates the imports once and records the env id; **every later check runs in a fresh environment forked from that warm base** — `tests/test_lean_bridge.py::TestEnvIdHygiene` proves definitions don't leak between checks and the warm id is stable. |
| `statement_ok(stmt) -> bool` | Elaborates `example : <stmt> := by sorry` with `autoImplicit` off — hallucinated identifiers fail instead of being auto-bound. True iff only the sorry warning remains. |
| `check(code) -> dict` | Kernel-checks a full declaration; `['ok']` iff no errors **and no sorries**. |
| `feedback` / `last_errors` | Lean's diagnostics from the most recent call — the raw material for repair-loop prompts. |
| `find(stmt) -> str \| None` | `exact?` probe with suggestion parsing — the B-5 citation seed. |
| timeout → restart | A timed-out check restarts the repl transparently (re-paying the warm-up) and raises `LeanError`; a crashed repl recovers on the next call. `RLock` because restart→warmup→send re-enters on the same thread. |
| `repl_available()` / `ensure_repl()` | Toolchain probes; tests skip cleanly when absent, errors carry the setup command instead of a stack trace. |

**Revision pinning (D2):** the repl is cloned at `REPL_REVISION = "v4.30.0"`
and built with the toolchain named in its own `lean-toolchain` file — the
two move together. `setup_lean.sh` keeps its own copy of the pin and the
comment in both files says to keep them in sync.

Tests: `tests/test_lean_bridge.py` — 15 tests (not-found messaging, check
semantics incl. sorry-rejection, statement well-formedness, env hygiene,
timeout/crash recovery, `find`), all green **against the live REPL** in ~3.5 s.

---

## 2. Provisioning (one-time)

```bash
bash cookbook/tools/lean/setup_lean.sh                  # elan + pinned repl + spl_lean project
bash cookbook/tools/lean/setup_lean.sh --with-mathlib   # + mathlib (~5 GB olean cache)
python -c "from spl3.lean_bridge import repl_available; print(repl_available())"
```

Idempotent; installs user-space (`~/.elan`, repo-local checkout at
`cookbook/tools/lean/repl`). The `spl_lean` lake project is the
`project_dir` target; `--with-mathlib` un-comments its pinned
`[[require]]` block and pulls the olean cache (`lake exe cache get` —
never compile mathlib from source).

---

## 3. What shipped (B-2/B-3) — recipe 76 `lean_proof`

`cookbook/76_lean_proof/lean_proof.spl` — the generate-then-verify spine at
proof grade, alternating regimes:

| Stage | Regime | What |
|---|---|---|
| 1. formalize | LLM → **Lean gate** | prose claim → bare proposition; `statement_ok` typecheck with capped repair loop fed `feedback` |
| 2. judge | LLM | faithfulness: does the Lean prop say what the prose says? (§B.4 — the one link nothing machine-checks; FAITHFUL/UNFAITHFUL + reason in the report) |
| 3a. cite | **Lean** | `find`/`exact?` **before any proof-writing tokens**; a hit is kernel-checked as the proof (B-5 seed) |
| 3b. prove | LLM → **Lean kernel** | tactic script only — `make_theorem` splices the verified statement in verbatim (recipe 67's lesson: the checked artifact never round-trips through the LLM); capped kernel-check repair loop |
| 4. badge | — | `machine_proved` / `statement_checked` / `unverified` — proof failure withholds the badge, never blocks delivery (§B.2) |

Verified end-to-end 2026-06-11 (`spl3 run ... --kernel --llm claude_cli`):

- **Citation path:** default claim → `∀ n m : Nat, n + m = m + n` →
  `exact?` returned `Nat.add_comm` → kernel-checked → `machine_proved`,
  **2 LLM calls, zero proof tokens**.
- **LLM-proof path:** "for any natural number n, n² ≥ n" → `exact?` miss →
  `intro n; exact Nat.le_self_pow (by decide) n` first try → `machine_proved`,
  3 LLM calls.
- **Degradation path:** same claim before prompt hardening — model reached
  for `ring`, burned the 3-try cap (each round fed Lean's real diagnostics),
  finished `statement_checked` with exit 0.

---

## 4. Findings / decisions settled

- **Stdlib-only default is the right test tier.** Bare-repl warm-up is
  ~instant (15 tests in 3.5 s including process spawns) vs 10–40 s for a
  mathlib import — and stdlib already carries enough (`Nat.add_comm`,
  `Nat.le_self_pow`, `omega`, `decide`) for the recipe's in-scope band.
- **Prompts must state the tactic universe.** The single observed failure
  mode was the LLM assuming mathlib: `ring`/`linarith`/`norm_num` are
  *unknown tactics* in a bare repl. The proof prompts now say so explicitly
  and whitelist core tactics; with that constraint the model found the
  stdlib lemma route unaided.
- **LLM output discipline is the other leak**: one repair emitted prose
  commentary after the tactic script, which `strip_fences` doesn't remove.
  Prompts now end with "nothing after the final tactic"; a structural
  guard in `strip_fences` is a possible hardening if it recurs.
- **Citation-first pays immediately** — the default claim never spent a
  proof token, and a named-lemma hit is stronger correspondence evidence
  than a bespoke proof of a bespoke statement (§B.4).
- **`claude_cli` adapter timeout** (300 s) is the flakiest link, not Lean:
  one run died on a slow CLI response and succeeded verbatim on retry.

---

## 5. Next

- **B-4** — `machine_proved` as a cache-provenance badge: recipe 76's
  `@badge` string + side-by-side report are the seed; the A-3 `verifier`
  column machinery (`cache_put(..., verifier='lean')`) is the rail to ride.
- **B-2 remainder** — wire `statement_ok` + the faithfulness judge into
  recipe 71's payoff concepts (rank–nullity, spectral theorem statements).
- **B-5 remainder** — run against the mathlib `spl_lean` project
  (`--with-mathlib`), Loogle/LeanSearch as fallback search.
