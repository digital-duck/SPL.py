# Recipe 76 — Lean Proof: generate-then-verify at proof grade

> **Status: prepared, untested.** This recipe is written against the
> `lean_bridge` API planned in milestone **B-1**
> ([`docs/DEV/sage_lean_integration_plan.md`](../../docs/DEV/sage_lean_integration_plan.md) §B.2),
> which is being implemented in a parallel session. It parses clean
> (`spl3 validate`: OK, with the same linter-heuristic warnings as recipe 71)
> and will be exercised end-to-end once Part B lands. This is the **B-3**
> milestone recipe.

## What it demonstrates

The top rung of the **verifier ladder**: SymPy/Sage verify *instances*
(this eigenpair works); Lean verifies *statements* (the theorem itself).
The workflow is the conjecture-checking loop a mathematician runs by hand,
expressed declaratively:

```
@claim (prose)
   │ GENERATE formalize_claim          LLM        (probabilistic)
   ▼
@lean_stmt — theorem … := by sorry
   │ SOLVE lean_statement_ok           Lean       (deterministic gate)
   │   ↺ fail → GENERATE fix_formalization(claim, stmt, errors)   ≤ max_attempts
   ▼
   │ GENERATE write_proof              LLM        (probabilistic)
   ▼
@lean_proof — theorem … := <tactic proof>
   │ SOLVE lean_proof_ok               Lean kernel (deterministic gate)
   │   ↺ fail → GENERATE repair_proof(proof, errors)              ≤ max_attempts
   ▼
@verdict: machine_proved (lean) | unproved (keeps its CAS-level badge)
   │ SOLVE lean_find — mathlib citation (stretch, B-5)
   ▼
@report — prose claim and Lean statement side by side
```

Two design points carried over from the plan:

- **Repair loops are capped** (`@max_attempts`, default 3) and fed Lean's
  *actual error messages* — the generate-then-verify spine at proof grade.
  On exhaustion the claim keeps whatever CAS-level verification it has:
  Lean failure never blocks delivery, it only withholds the higher badge.
- **The faithfulness gap is surfaced, not hidden** (plan §B.4): the report
  renders the prose claim and the Lean statement side by side, because the
  informal↔formal correspondence is the one link nothing machine-checks.
  A kernel-checked proof means "this *Lean statement* is proved" — a human
  (or an `spl3 judge` faithfulness check, B-2) must audit that the statement
  says what the prose says.

## Kernel-side contract (for the B-1 implementation)

The `.spl` imports **bare names** from `lean_bridge` inside the kernel —
the SOLVE template parser does not support dotted calls (`lean.check(...)`),
the same constraint that gave recipe 71 its `_now()`/`_verify_math()`
wrappers. The recipe assumes:

| Helper | Contract |
|---|---|
| `start(project_dir: str)` | Spawn (or attach to) the persistent `leanprover-community/repl` with mathlib imported; idempotent per session. |
| `lean_statement_ok(stmt: str) -> str` | Elaborate the declaration (expecting a `sorry` body). Return `"ok"` iff it typechecks with only the sorry warning, else `"fail: <lean errors>"`. |
| `lean_proof_ok(code: str) -> str` | Kernel-check the full declaration. Return `"ok"` iff it compiles with **no** sorries and no errors, else `"fail: <lean errors>"`. |
| `lean_find(stmt: str) -> str` | `exact?`-style mathlib lookup. Return the suggestion / lemma name, or `"none"`. |

The string returns (`"ok"` / `"fail: ..."`) deliberately mirror the
`graph_lib` verifier shape (`pass (...)` / `fail: ...`) so the same
`EVALUATE ... WHEN contains("fail")` branching works at every ladder rung —
and so the engine-of-record can ride into cache provenance later
(`cache_put(..., verifier='lean')`, A-3 machinery).

Each call should run in a **fresh environment forked from the warm-up
mathlib env** (the REPL `env`-id hygiene requirement, plan §B.2) so checks
don't pollute each other.

## Run (once Part B lands)

```bash
# Default claim: "The sum of two even integers is even."
spl3 run cookbook/76_lean_proof/lean_proof.spl \
    --kernel --adapter claude_cli \
    -p lean_project="$HOME/lean/spl-mathlib"

# Your own claim
spl3 run cookbook/76_lean_proof/lean_proof.spl \
    --kernel --adapter claude_cli \
    -p claim="For any natural number n, n^2 >= n." \
    -p lean_project="$HOME/lean/spl-mathlib" \
    -p max_attempts=3
```

Prerequisites (B-1's environment, plan §B.3): `elan`, a `lake` project
pinned to a mathlib release with `lake exe cache get` run, and the
`leanprover-community/repl` binary built for that toolchain.

## Good first claims

Statements that are instances or light specializations of existing mathlib
lemmas (the in-scope band, plan §B.4):

- *The sum of two even integers is even.* (`Even.add`)
- *For any natural number n, n² ≥ n.* (`Nat.le_self_pow` territory / `omega`-provable)
- *The product of two odd integers is odd.* (`Odd.mul`)
- Recipe-71 payoff concepts, once B-2 wires this into the micro-textbook:
  rank–nullity, spectral theorem statement, diagonalizability criteria.

## Files

| File | Purpose |
|---|---|
| `lean_proof.spl` | The workflow (validated; constructs limited to those proven in recipe 71: `SOLVE`, `ASSERT`, `WHILE`, `EVALUATE`, `GENERATE`, `CALL run_python`, `LOGGING`, `COMMIT`) |
| `readme.md` | This file — including the kernel-side API contract for B-1 |

## Relation to the milestones

| Milestone | This recipe's role |
|---|---|
| B-1 (`lean_bridge`) | Consumer — defines the bare-name contract above |
| B-2 (statement checking) | Steps 1–2 of the workflow, standalone |
| **B-3 (proof + repair loop)** | **This recipe** |
| B-4 (`machine_proved` badge) | The `@verdict` string is the badge's seed; cache wiring follows |
| B-5 (mathlib citation) | The `lean_find` step (already in the workflow as a stretch) |
