# Recipe 76 — Lean Proof: generate-then-verify at proof grade

The **B-3** milestone recipe of
[`docs/DEV/sage_lean_integration_plan.md`](../../docs/DEV/sage_lean_integration_plan.md):
the top rung of the **verifier ladder**. SymPy/Sage verify *instances*
(this eigenpair works); Lean verifies *statements* (the theorem itself).
The workflow is the conjecture-checking loop a mathematician runs by hand,
expressed declaratively.

> **Status: implemented.** Built on `spl3/lean_bridge.py` (milestone B-1,
> 15/15 tests green against the live REPL). An earlier prepared-but-untested
> draft of this recipe — written against a *planned* B-1 API — is preserved
> in git history (commit `00f1c2b`); this version is rewritten against the
> API that actually landed.

## What it demonstrates

```
@claim (prose)
   │ GENERATE formalize_claim                LLM   (probabilistic)
   ▼
@lean_stmt — a bare Lean 4 proposition
   │ statement_ok — does `example : <stmt> := by sorry` elaborate?
   │                                         Lean  (deterministic gate)
   │   ↺ fail → GENERATE fix_formalization(claim, stmt, lean feedback)  ≤ max_tries
   ▼
   │ GENERATE judge_faithfulness             LLM   (probabilistic — §B.4:
   │           does the Lean prop say what the prose says? the one link
   │           nothing machine-checks)
   ▼
   │ find — exact? probe: is this already a known lemma?
   │                                         Lean  (deterministic, zero tokens)
   │   hit → the suggestion IS the proof (citation path, B-5 seed)
   │   miss ↓
   │ GENERATE write_tactics                  LLM   (probabilistic — ONLY the
   │           tactic block; make_theorem splices the verified statement in
   │           verbatim, so the LLM can never prove a different statement)
   ▼
@proof — theorem spl_claim : <stmt> := by <tactics>
   │ check — kernel-check                    Lean  (deterministic gate)
   │   ↺ fail → GENERATE repair_tactics(stmt, tactics, lean feedback)   ≤ max_tries
   ▼
@badge: machine_proved | statement_checked | unverified
   ▼
@report — prose claim and Lean statement side by side
```

Design points carried over from the plan:

- **Repair loops are capped** (`@max_tries`, default 3) and fed Lean's
  *actual diagnostics* (`_spl_lean.feedback`) — the generate-then-verify
  spine at proof grade. On exhaustion the claim keeps its lower badge:
  **Lean failure never blocks delivery, it only withholds the higher badge**
  (§B.2).
- **The faithfulness gap is surfaced, not hidden** (§B.4): a kernel-checked
  proof means "this *Lean statement* is proved" — the informal↔formal
  correspondence is judged by a separate LLM call (FAITHFUL/UNFAITHFUL +
  reason) and rendered in the report next to the prose claim for human audit.
- **Citation before proving** (§B.4/B-5): `exact?` runs before any
  proof-writing LLM call. On a hit, the library lemma is the proof — zero
  tokens, and a citation into a curated library is stronger correspondence
  evidence than a bespoke proof of a bespoke statement.
- **The verified statement never round-trips through the LLM** (recipe 67's
  lesson): `make_theorem` assembles `theorem spl_claim : <stmt> := by <tactics>`
  deterministically in-process.

## Kernel-side API (`spl3/lean_bridge.py`, milestone B-1)

The recipe drives one persistent `LeanREPL` instance (`_spl_lean`) inside
the IPython kernel via `CALL run_python(...)`:

| Call | Contract |
|---|---|
| `LeanREPL().start()` | Spawn the persistent `leanprover-community/repl` (pinned `v4.30.0`), warm up a base environment; stdlib-only by default — pass `project_dir=`/`imports=` for mathlib. |
| `statement_ok(stmt) -> bool` | Elaborate `example : <stmt> := by sorry` in a fresh env forked from the warm base (env-id hygiene, §B.2). `True` iff it typechecks with only the sorry warning. |
| `check(code) -> dict` | Kernel-check a full declaration; `['ok']` is `True` iff no errors and no sorries. |
| `feedback -> str` | Lean's diagnostics from the most recent call — fed back into the repair prompts. |
| `find(stmt) -> str \| None` | `exact?` probe; returns the suggested term/lemma or `None`. |
| `repl_available() -> bool` | Toolchain probe; lets tests skip when the REPL is absent. |

Timeouts restart the REPL transparently; crashes recover on the next call
(see `tests/test_lean_bridge.py::TestTimeoutAndRestart`).

## Setup (one-time)

```bash
bash cookbook/tools/lean/setup_lean.sh   # elan + pinned repl v4.30.0, built with lake
```

## Run

```bash
# Default claim: "addition of natural numbers is commutative"
spl3 run cookbook/76_lean_proof/lean_proof.spl --kernel --llm claude_cli

# Your own claim
spl3 run cookbook/76_lean_proof/lean_proof.spl --kernel --llm claude_cli \
    --param claim="for any natural number n, n^2 >= n" \
    --param max_tries=3

# Local model
spl3 run cookbook/76_lean_proof/lean_proof.spl --kernel \
    --adapter ollama --model gemma3
```

## Good first claims

Stdlib-decidable or simple-tactic territory (the default REPL is
stdlib-only; point it at a mathlib project for the full library):

- *addition of natural numbers is commutative* (`Nat.add_comm`)
- *for any natural number n, n² ≥ n* (`omega`/`induction` territory)
- *n + 0 = n for every natural number* (`rfl`)

## Files

| File | Purpose |
|---|---|
| `lean_proof.spl` | The workflow (validated; warnings are linter heuristics — the WHILE loops are bounded by `@tries < @max_tries`) |
| `readme.md` | This file |

## Relation to the milestones

| Milestone | This recipe's role |
|---|---|
| B-1 (`lean_bridge`) | Consumer — drives the persistent `LeanREPL` from the kernel |
| B-2 (statement checking) | Stage 1 + the faithfulness judge (Stage 2) |
| **B-3 (proof + repair loop)** | **This recipe** (Stage 3b) |
| B-4 (`machine_proved` badge) | The `@badge` string is the badge's seed; cache wiring follows |
| B-5 (mathlib citation) | Stage 3a — the `find`/`exact?` citation path |
