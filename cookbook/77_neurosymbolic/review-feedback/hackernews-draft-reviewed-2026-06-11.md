# Neurosymbolic SPL: LLM Workflows Where SymPy Computes, SageMath Reaches Further, and Lean 4 Proves

*Companion to [recipe 77](readme.md) (`sympolic_tools.spl`) — the workflow this
document announces. [`hackernews-v0.1.md`](hackernews-v0.1.md) was an earlier,
deliberately narrower version of this story: a pre-registered benchmark design
for the SymPy-only pipeline of [recipe 67](../67_symbolic_math/readme.md). That
design still stands and will still be run. This document widens the claim it
was designed to test: the deterministic backend behind the same two SPL
constructs is no longer one engine — it's a ladder of three.*

## The claim in one paragraph

SPL (Structured Prompt Language) is a SQL-inspired declarative language for
LLM workflows: `GENERATE` steps are probabilistic (an LLM), `SOLVE`/`ASSERT`
steps are deterministic (a kernel). As of this release, the deterministic side
is a **verifier ladder** — numeric spot-check (NumPy) → exact symbolic instance
(SymPy / SageMath) → machine-checked proof (Lean 4 + mathlib) — and climbing it
required **zero new language constructs**. The same `SOLVE` that differentiates
a polynomial can compute the Galois group of `x⁵ − x − 1` over ℚ, and the same
`ASSERT` that rejects a malformed expression can require that a statement
typechecks against mathlib. No orchestration framework we know of offers
kernel-checked proof as a language-level verification primitive. That is the
ground this release stakes out — and the rest of this document is the
receipts, plus the honest limits.

## Where this started

[Recipe 67's case study](../67_symbolic_math/case-2.md) ran one calculus
problem through a SymPy-backed SPL pipeline against nine LLMs. The
deterministic core was bit-identical every run; the interesting variance was
all at the probabilistic ends. The most important single observation: one
model produced a correct, fluent, `status=complete` answer **while the
verified chain never ran** — indistinguishable from the outside from a
correctly verified run. We named it *silent unverified success*, and it is the
failure mode this whole architecture exists to kill: not wrong answers, but
**unauditable** ones.

The fix is not a better model. It is a pipeline where the trustworthy parts
are deterministic, the LLM is confined to the two jobs it is actually good at
(translating intent in, narrating results out), and every claim that reaches
the user carries a machine-checkable record of *what* verified it. SymPy
proved that pattern works for calculus instances. The obvious question was:
how far up does it go?

## The ladder, rung by rung

| Rung | Engine | Verifies | Example |
|---|---|---|---|
| 1 | NumPy | a number, approximately | residual of `A·v − λ·v` near zero |
| 2 | SymPy | an **instance**, exactly | this `(λ, v)` satisfies `A·v = λ·v`, symbolically |
| 2+ | SageMath | an instance **SymPy can't reach** | Galois group over ℚ (PARI); rational point on a conic; Mordell–Weil rank of an elliptic curve (mwrank); exact factorization over ℚ (FLINT) |
| 3 | Lean 4 + mathlib | a **statement**, universally quantified | `∀ n m : Nat, n + m = m + n` — the theorem itself, kernel-checked, not one worked example |

Rungs 1–2 and rung 3 are epistemically different, and we keep them separate
all the way down to the trust model (below). A CAS check says *this example
works*. A Lean check says *the claim is true for all cases* — modulo one gap
we'll get to, because it's the part most announcements omit.

**Integration cost, honestly stated.** Sage entered through one constructor
parameter: SPL workflows already ran on a persistent Jupyter kernel, Sage
ships a kernel spec, so `spl3 run --kernel-name sagemath` swaps the entire CAS
under an unchanged workflow ([recipe 75](../75_sage_math/readme.md)). Lean is
not Python, so it enters one level down: a thin client inside the kernel
(`spl3.lean_bridge.LeanREPL`) holds a persistent `leanprover-community/repl`
process — mathlib imported once and amortized, every check in a fresh
environment forked from the warm base, timeout → transparent restart. Both are
pure backend work; the parser and AST never changed.

## What recipe 77 actually runs

[Recipe 67](../67_symbolic_math/readme.md) established the chain protocol: an
LLM decomposes a natural-language problem into terse `<expression>|<operation>`
steps, a kernel executes each step exactly, an LLM narrates the verified
trace. Recipe 77 keeps that protocol **byte-for-byte** and widens the dispatch:

- `solve_step_with_sympy` — the recipe-67 kernel, extended (series, partial
  fractions, limits, Laplace transforms, eigenvalues, systems).
- `solve_step_with_sage` — the same `<bare_result>|<readable_line>` contract,
  same `solver_error|…` sentinel, plus four operations that exist on no other
  rung: `galois`, `conic`, `rank`, `factor_qq`.
- The Lean stage — formalize → typecheck (capped repair loop) → an LLM
  faithfulness judge on the formalization → **citation-first** proof search
  (`exact?` against mathlib, Loogle as a network fallback whose every
  suggestion is kernel-checked before it counts) → LLM tactic proof as the
  last resort, also kernel-checked, also behind a capped repair loop.

One detail we consider load-bearing: the final theorem is assembled
*deterministically* — the verified statement is spliced in verbatim and the
LLM only ever contributes the tactic block. The LLM can fail to prove the
statement; it cannot quietly prove a *different* statement. That lesson came
directly from the recipe-67 failure taxonomy.

There is also an `solve_directly` baseline — the same problem handed to the
same LLM with no kernel behind it — because the v0.1 benchmark design's
central question (does the kernel do real work, or would the LLM have gotten
there anyway?) deserves a one-flag A/B, not an assumption.

## Trust badges, not a trust ladder

Verification grades live in a Layer 2 content cache, and we initially modeled
them as one ordinal ladder (`machine_generated → machine_verified →
ai_reviewed → human_verified`). That was wrong, and the bug is instructive:
under an ordinal, an LLM judge's `ai_reviewed` *outranked* — and therefore
satisfied a filter for — `machine_verified`. Prose review was silently
standing in for mathematical verification.

The shipped model is a badge **set** on two orthogonal axes:

| Axis | Badges (strictly ordered within axis) | Attests |
|---|---|---|
| claim | `machine_verified` < `machine_proved` | the mathematics |
| exposition | `ai_reviewed` < `human_verified` | the prose and pedagogy |

Across axes there is no ordering — a kernel-checked statement with confusing
exposition still needs review, and neither badge ever satisfies a requirement
on the other axis. `canonical` (★) is derived, never stored: top badge on both
axes. Every entry also records the **engine of record** (`sympy`, `sage`,
`lean`) — declared fallbacks like `verifier: "sage|sympy"` record which engine
actually ran, never a silent downgrade.

## Receipts (verified runs, 2026-06-11, live mathlib)

From [recipe 76](../76_lean_proof/readme.md), the proof-grade loop:

| Claim (prose) | Outcome | Badge |
|---|---|---|
| addition of naturals is commutative | citation path: `exact?` returned `Nat.add_comm` — **zero proof tokens spent** | `machine_proved` |
| for any natural n, n² ≥ n | LLM tactic `intro n; exact Nat.le_self_pow (by decide) n`, kernel-checked first try | `machine_proved` |
| (repair cap exhausted) | degraded to statement-checked; delivery not blocked | badge withheld |

From [recipe 71](../71_linalg_micro_textbook/readme.md)'s `lean_payoffs.spl`,
a post-pass over real micro-textbook entries: `rank_nullity` and
`diagonalization` were promoted to `machine_verified, machine_proved` with
kernel-checked mathlib citations and the audited statement stored;
`spectral_theorem` found no citation and **correctly stayed**
`machine_verified`. We consider the third row the most important one: failure
withholds the badge, it never blocks delivery and never fakes the badge.

From [recipe 75](../75_sage_math/readme.md): Galois group of `x⁵ − x − 1`
(S₅), rational-point decision on `x² + y² = 3z²` (none — Legendre), rank of
`y² + y = x³ − x² − 10x − 20` (0), all computed exactly under the Sage kernel
with the engine of record logged.

## The honest limit: the formalization-correspondence gap

`machine_proved` means "**this Lean statement** is kernel-checked." It does
not mean "the prose claim is proved." A statement can typecheck and prove
cleanly while being not what the prose says — a flipped quantifier, a vacuous
hypothesis, a degenerate specialization that is trivially true. The
informal↔formal correspondence is the one link in the chain nothing
machine-checks, and we'd rather name it than have a commenter name it for us.
Three mitigations ship:

1. **Side-by-side rendering** — wherever the badge appears (`spl3 cache
   show`), the prose claim and the Lean statement render together, so a human
   can audit correspondence at a glance.
2. **An LLM faithfulness judge** on the formalization — a probabilistic check
   on the one probabilistic link, which is the right tool for exactly that
   link and nothing else. In the textbook post-pass, UNFAITHFUL *gates* the
   badge.
3. **Citation-first** — a hit on a *named* mathlib lemma whose docstring
   matches the prose is far stronger correspondence evidence than a bespoke
   proof of a bespoke statement.

Scope is correspondingly narrow on purpose: claims that are instances or
light specializations of existing mathlib lemmas. We are not proving novel
theorems, not formalizing whole textbooks, and Lean is never on the default
pipeline path — it only ever adds a badge.

## Why we built it

The end state we want is a working mathematician's or physicist's daily loop —
*draft with an LLM, falsify with a CAS, formalize, search the literature* —
expressed in one declarative language and fully auditable:

```spl
WORKFLOW explore_conjecture
  GENERATE propose_lemma(@research_notes) INTO @claim          -- LLM drafts
  SOLVE @counterexample := sage_search(@@claim@@, bound=1000)   -- Sage hunts instances
  ASSERT @@counterexample@@ is None
      OTHERWISE RETURN @counterexample                          -- falsified: done
  GENERATE formalize_claim(@claim) INTO @lean_stmt              -- LLM formalizes
  ASSERT lean.statement_ok(@@lean_stmt@@)
      OTHERWISE RETRY GENERATE fix_formalization(@claim, @@lean.last_errors@@)
  SOLVE @mathlib_hit := lean.find(@@lean_stmt@@)                -- already proved?
  RETURN @mathlib_hit                                           -- cite or open problem
END
```

Draft → falsify → formalize → search mathlib: the conjecture-triage loop
researchers already run by hand, with the probabilistic and deterministic
steps composing in one file. The micro-textbook pipeline (recipes 70–74) is
the same architecture pointed at education — generated content that learners
only ever receive with a claim-axis badge on it — and that, not benchmark
wins, is the application we care most about.

## Try it

```bash
pip install 'spl-llm[sage]'                          # Sage via passagemath wheels — no source build
python -m sage.repl.ipython_kernel.install --user    # register the 'sagemath' kernel spec
cookbook/tools/lean/setup_lean.sh --with-mathlib     # elan + pinned Lean REPL (optional, ~5 GB oleans)

# Rung 2+: exact number theory under the Sage kernel
spl3 run cookbook/75_sage_math/basic_sagemath.spl \
    --adapter ollama --model gemma3 --kernel-name sagemath \
    --param problem="does x^2 + y^2 = 3*z^2 have a rational solution?"

# Rung 3: formalize → faithfulness gate → citation-first proof
spl3 run cookbook/76_lean_proof/lean_proof.spl --kernel --llm claude_cli \
    --param claim="for any natural number n, n^2 >= n"

# Inspect the badge set and the prose ↔ formal statement side by side
spl3 cache list --badge machine_proved
spl3 cache show <key>
```

Everything above is reproducible from `.spl` source plus CLI flags — no
custom harness. Sage and Lean are both strictly optional: every test that
needs them skips cleanly when they're absent, and every workflow degrades to
the rung it can reach.

## What we are not claiming

- Not that LLMs can do mathematics — the architecture exists precisely
  because, unverified, they confabulate fluently.
- Not that `machine_proved` closes the loop — the correspondence gap above is
  real, mitigated, and unsolved.
- Not that the recipe-67 anecdote generalizes — the pre-registered benchmark
  in [v0.1](hackernews-v0.1.md) exists to find out, and its predictions are
  written down before the data so the run can prove us wrong.

What we are claiming is narrower and checkable: two declarative constructs,
three epistemic grades of verification behind them, engine-of-record and
badge provenance on every cached claim, and a worked end-to-end path from
"an LLM said so" to "the Lean kernel checked it" — with every rung of that
path in this repository, runnable today.
