# SPL × Lean 4 — Proof-Grade Verification (Verifier Ladder, Part B)

> **Status:** **B-1…B-5 all shipped** (2026-06-11; 29/29 bridge tests green
> including the live-mathlib tier, recipe 76 verified end-to-end on both
> proof paths, recipe 71's `lean_payoffs.spl` post-pass lands the first
> two-axis badge sets in cache provenance). Design:
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
| `LeanREPL.mathlib(**kw)` | Constructor preset for the `spl_lean` mathlib project (`--with-mathlib`): `imports=["Mathlib"]`, warm-up budget sized for the olean import; raises with the setup command when the project is absent (`mathlib_available()` is the test guard). |
| `find_citation(stmt, fallback=True) -> str \| None` | B-5 citation search: local `exact?` first; on a miss, queries Loogle (`loogle_pattern()` derives the query from the proposition's conclusion) and **kernel-checks every candidate** before returning it — the network is a search hint, never a trust source. Loogle down/unreachable degrades to the local result. |
| timeout → restart | A timed-out check restarts the repl transparently (re-paying the warm-up) and raises `LeanError`; a crashed repl recovers on the next call. `RLock` because restart→warmup→send re-enters on the same thread. |
| `repl_available()` / `ensure_repl()` | Toolchain probes; tests skip cleanly when absent, errors carry the setup command instead of a stack trace. |

**Revision pinning (D2):** the repl is cloned at `REPL_REVISION = "v4.30.0"`
and built with the toolchain named in its own `lean-toolchain` file — the
two move together. `setup_lean.sh` keeps its own copy of the pin and the
comment in both files says to keep them in sync.

Tests: `tests/test_lean_bridge.py` — 29 tests (not-found messaging, check
semantics incl. sorry-rejection, statement well-formedness, env hygiene,
timeout/crash recovery, `find`, Loogle pattern/parsing/soft-miss semantics,
`find_citation` fallback paths, plus a **live-mathlib tier** — mathlib
vocabulary elaboration, dot-notation misuse caught, `find` against the full
library — guarded by `mathlib_available()`), all green against the live REPL.

---

## 2. Provisioning (one-time)

```bash
bash cookbook/tools/lean/setup_lean.sh                  # elan + pinned repl + spl_lean project
bash cookbook/tools/lean/setup_lean.sh --with-mathlib   # + mathlib (~5 GB olean cache)
python -c "from spl3.lean_bridge import repl_available; print(repl_available())"
```

Idempotent; installs user-space (`~/.elan`, repo-local checkout at
`cookbook/tools/lean/repl` by default). The whole stack is relocatable —
`ELAN_HOME`, `SPL_LEAN_REPL_DIR`, and `SPL_LEAN_PROJECT_DIR` redirect
both the install and the bridge's run-time discovery (see
`docs/GUIDE/SETUP.md` §6 for the `/opt/lean` layout). The `spl_lean`
lake project is the `project_dir` target; `--with-mathlib` un-comments
its pinned `[[require]]` block and pulls the olean cache
(`lake exe cache get` — never compile mathlib from source).

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

## 4. What shipped (B-4) — `machine_proved` in cache provenance

The pre-B-4 cache assumed one provenance ordinal (`machine_generated →
machine_verified → ai_reviewed → human_verified`) — which let `ai_reviewed`
*satisfy* a `machine_verified` threshold despite attesting a different
thing. B-4 replaces it with the badge-*set* model (plan §B.1, D1):

| Piece | Behavior |
|---|---|
| `cache.types` | `CLAIM_BADGES = [machine_verified, machine_proved]`, `EXPOSITION_BADGES = [ai_reviewed, human_verified]`; `satisfies()` is **axis-local** — requiring `machine_verified` is met by `machine_proved`, never by exposition badges; `is_canonical()` derives ★ (top badge on both axes, never stored) |
| `promote()` | adds a badge to the set (no ladder, no downgrade; duplicate add is an error); `spl3 judge --cache-key` adds `ai_reviewed` |
| `statement` column | the kernel-checked Lean proposition stored with the entry; `spl3 cache show` renders it under the prose preview — the §B.4 correspondence-audit requirement |
| `spl3 cache` CLI | `list`/`stats`/`clear --badge` are badge-aware; ★ marks canonical entries |
| recipe 76 | on a kernel-checked proof: `CALL cache_put(@claim, @report, badges='machine_proved', verifier='lean', statement=@lean_stmt)` — verified end-to-end 2026-06-11 |
| migration | pre-B-4 DBs and exports convert automatically; each legacy tier becomes the badge set attesting only what it attested (`machine_generated` → empty set) |

Recipe 76's `statement_checked` stays recipe-internal: it attests
well-formedness, not truth, so it maps to *no* claim badge — the entry
simply isn't cached above the baseline.

**Found while wiring:** SPL 2.0's tool dispatch flattened `CALL` named
arguments into the positional list, so `cache_put(..., verifier='lean',
statement=...)` bound `'lean'` to `rubric_version`. Fixed in
`spl/executor.py` (`_exec_call` now passes kwargs by name; regression
tests in `tests/test_executor.py::TestToolCallBinding`) — the stdlib had
advertised `verifier='sage'` since A-3, but nothing had exercised it.

---

## 5. Findings / decisions settled

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

## 6. What shipped (B-2/B-5 remainders) — recipe 71 `lean_payoffs`

`cookbook/71_linalg_micro_textbook/lean_payoffs.spl` — the B-2 post-pass:
statement-level Lean checking for the micro-textbook's payoff concepts,
run *after* a `build_micro_textbook` run so Lean stays off the default
pipeline path (§B.4 scope discipline). Same stage spine as recipe 76, with
two deliberate differences:

- **UNFAITHFUL gates the badge** (recipe 76 only reports it) — these are
  real textbook entries being promoted, so a formalization the judge calls
  unfaithful never earns `machine_proved`.
- **Promotion, not insertion** — on a kernel-checked citation the concept's
  *existing* cached section (which already holds `machine_verified` from
  the build run's CAS checks) gets `cache_promote(..., 'machine_proved',
  statement=...)` — producing the first real two-axis badge sets.

Verified end-to-end 2026-06-11 against the live mathlib REPL
(`spl3 run ... --kernel --llm claude_cli`, exit 0; 89/89 bridge+cache
tests green):

| concept | outcome |
|---|---|
| `rank_nullity` | formalized in mathlib vocabulary (`Module.finrank`/`LinearMap.range`/`LinearMap.ker`), FAITHFUL, citation kernel-checked → badges `machine_verified, machine_proved`, statement stored for side-by-side audit |
| `diagonalization` | `Matrix.det (Matrix.diagonal d) = ∏ i, d i`, FAITHFUL, citation kernel-checked → badges `machine_verified, machine_proved` |
| `spectral_theorem` | no library citation found → correctly stayed `machine_verified` (statement-checked is recipe-internal; §B.2 — failure withholds the badge, never blocks delivery) |

---

## 7. Next

- **Loogle hardening** — the fallback derives its query from the
  conclusion only; specializing the pattern (head constant + key
  arguments) would raise hit rates on harder statements like the spectral
  theorem.
- **LeanSearch** (semantic search) as a second fallback tier behind
  Loogle, same kernel-check discipline.
- Graduate `lean_bridge` patterns into stdlib `TOOL_API`s once a third
  recipe needs them (the §B.4 graduation rule).
