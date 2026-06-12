# Neurosymbolic SPL: SymPy, SageMath, and Lean 4 Behind Two Keywords

*Repo: https://github.com/digital-duck/SPL.py — this document lives at
`cookbook/77_neurosymbolic/`, next to the workflow it describes. Lineage:
[`hackernews-v0.1.md`](hackernews-v0.1.md) is the pre-registered,
SymPy-only benchmark design (it still stands and will still be run); this
v0.2 is the full-ladder announcement, revised per the critique in
[`review-feedback/fable-review-2026-06-11.md`](review-feedback/fable-review-2026-06-11.md)
(the reviewed draft is archived alongside the review).*

## The bug that started this

Last week I ran one calculus problem through a SymPy-backed LLM pipeline
against nine models ([recipe 67](../67_symbolic_math/readme.md), raw runs in
[`case-2-log.md`](../67_symbolic_math/case-2-log.md)). The
deterministic core was bit-identical on every run. The interesting variance
was at the probabilistic ends, and the single most important observation was
this: one model, `lfm2.5` (a liquid foundation model, not a transformer),
produced a correct, fluent, `status=complete` answer **while the verified
chain never executed**. Zero solver steps ran. From outside the system, that
run is indistinguishable from a correctly verified one.

I call that failure mode *silent unverified success*, and it is the thing
this architecture exists to kill. Not wrong answers. **Unauditable** ones.

The fix is not a better model. It is a pipeline where the trustworthy parts
are deterministic, the LLM is confined to the two jobs it is good at
(translating intent in, narrating results out), and every claim that reaches
the user carries a machine-checkable record of what verified it, and with
which engine. SymPy proved the pattern works for calculus instances. This
release answers the next question: how far up does it go?

## The answer: a ladder, behind two keywords

SPL (Structured Prompt Language) is a SQL-inspired declarative language for
LLM workflows. `GENERATE` steps are probabilistic (an LLM). `SOLVE` and
`ASSERT` steps are deterministic (a kernel). As of this release the
deterministic side is a **verifier ladder**, and climbing it required zero
new language constructs:

| Rung | Engine | Verifies | Example |
|---|---|---|---|
| 1 | NumPy | a number, approximately | residual of `A·v − λ·v` near zero |
| 2 | SymPy | an **instance**, exactly | this `(λ, v)` satisfies `A·v = λ·v`, symbolically |
| 2+ | SageMath | an instance SymPy can't reach | Galois group over ℚ (PARI); rational point on a conic; Mordell–Weil rank of an elliptic curve (mwrank); exact factorization over ℚ (FLINT) |
| 3 | Lean 4 + mathlib | a **statement**, universally quantified | `∀ n m : Nat, n + m = m + n`. The theorem itself, kernel-checked, not one worked example |

The same `SOLVE` that differentiates a polynomial computes the Galois group
of `x⁵ − x − 1`. The same `ASSERT` that rejects a malformed expression can
require that a statement typechecks against mathlib.

Integration cost, honestly stated: Sage entered through one constructor
parameter. SPL workflows already ran on a persistent Jupyter kernel, Sage
ships a kernel spec, so `spl3 run --kernel-name sagemath` swaps the entire
CAS under an unchanged workflow ([recipe 75](../75_sage_math/readme.md)).
Lean is not Python, so it enters one level down: a thin client inside the
kernel (`spl3.lean_bridge.LeanREPL`) holds a persistent
`leanprover-community/repl` process. Mathlib is imported once and amortized;
every check runs in a fresh environment forked from the warm base; a timeout
triggers a transparent restart. Both integrations are pure backend work. The
parser and AST never changed.

## Prior art, and the actual claim

Coupling LLMs to Lean is a well-developed research area: Draft-Sketch-Prove,
LeanDojo and ReProver, llmstep, AlphaProof, Sagredo, and Terence Tao's
documented mathlib workflows all predate this. On the other side, any
general orchestrator (LangChain and its descendants) can shell out to `lake`
like it can shell out to anything.

What I have not seen elsewhere, and the narrow claim I am actually making:
a **workflow language** in which proof checking is a typed verification
construct rather than a tool call. The difference is structural. In an
agent framework, the prover's output is text that a probabilistic agent
interprets, and may ignore. Here, `ASSERT` failure deterministically takes
the declared `OTHERWISE` branch; the result is recorded as provenance
(engine of record, trust badge, the checked statement itself) in a content
cache; and the compiled artifact (a Jupyter notebook) declares the kernel it
ran under. The LLM never gets to summarize whether verification happened.
That property is the whole point, given the bug that started this.

## Why a language and not a Python script?

The mandatory question for any DSL, so here is the direct answer. A Python
script can do everything described above. What the language buys:

1. **You can grep what's verified.** Probabilistic and deterministic steps
   are syntactically distinct (`GENERATE` vs `SOLVE`/`ASSERT`), so the audit
   question "which parts of this pipeline are LLM output?" is answerable by
   reading the file, not by tracing code.
2. **Provenance is structural, not convention.** Badge writes, engine of
   record, and statement storage happen at the language level. A script can
   do this too, until someone forgets.
3. **Repair loops are first-class.** `OTHERWISE RETRY GENERATE
   fix_formalization(...)` with the checker's diagnostics fed back is one
   line, and capped.
4. **The artifact carries its runtime.** The same `.spl` compiles to a
   notebook whose kernelspec records what actually ran.

The honest counterpoint: if you don't need the audit trail, a Python script
is fine and simpler. SPL's bet is that for generated content with claims in
it (textbooks, in my case), the audit trail *is* the product.

## What recipe 77 runs

[Recipe 77](readme.md) is the capstone: one workflow,
[`symbolic_math.spl`](symbolic_math.spl), routing on a single `@backend`
parameter across all three rungs. The shared tool library is
[`sympolic_tools.spl`](sympolic_tools.spl) (yes, "sympolic" — SymPy +
symbolic, my portmanteau, filed before anyone reports the typo). The chain
protocol is unchanged from recipe 67: an LLM decomposes a natural-language
problem into terse `<expression>|<operation>` steps, a kernel executes each
step exactly, an LLM narrates the verified trace.

- `backend=sympy`: the recipe-67 kernel, extended (series, partial
  fractions, limits, Laplace transforms, eigenvalues, systems).
- `backend=sage`: the same step contract and the same error sentinel, plus
  four operations that exist on no other rung: `galois`, `conic`, `rank`,
  `factor_qq`.
- `backend=lean`: formalize → typecheck (capped repair loop) → an LLM
  faithfulness gate → **citation-first** proof search (`exact?` against
  mathlib, with Loogle as a network fallback whose every suggestion is
  kernel-checked before it counts) → LLM tactic proof as last resort, also
  kernel-checked, also behind a capped repair loop. The run returns its
  badge as its status: `machine_proved`, `statement_checked`, `unfaithful`
  (the judge gated it), or `unverified`. A failed proof never blocks
  delivery; it only withholds the badge.

One detail I consider load-bearing: the final theorem is assembled
deterministically. The verified statement is spliced in verbatim and the LLM
only ever contributes the tactic block. The LLM can fail to prove the
statement; it cannot quietly prove a *different* statement. That lesson came
directly from the recipe-67 failure taxonomy.

There is also `enable_solver=false`, the baseline arm: the same problem
handed to the same LLM with no kernel behind it. The pre-registered
benchmark in [v0.1](hackernews-v0.1.md) is built on that A/B, because "does
the kernel do real work, or would the LLM have gotten there anyway?"
deserves data, not an assumption. The harness ships in this directory
(`run_experiment.py`: 20 problems from the original battery, 4 Sage-only
problems, 5 Lean claims, crossed with models × solver on/off × repetitions).

## Trust badges, not a trust ladder

Verification grades live in a content cache, and I initially modeled them as
one ordinal ladder (`machine_generated → machine_verified → ai_reviewed →
human_verified`). That was wrong, and the bug is instructive: under an
ordinal, an LLM judge's `ai_reviewed` outranked, and therefore satisfied a
filter for, `machine_verified`. Prose review was silently standing in for
mathematical verification.

The shipped model is a badge **set** on two orthogonal axes:

| Axis | Badges (strictly ordered within axis) | Attests |
|---|---|---|
| claim | `machine_verified` < `machine_proved` | the mathematics |
| exposition | `ai_reviewed` < `human_verified` | the prose and pedagogy |

Across axes there is no ordering. A kernel-checked statement with confusing
exposition still needs review, and neither axis ever satisfies a requirement
on the other. `canonical` (★) is derived, never stored: top badge on both
axes. Every entry also records the engine of record (`sympy`, `sage`,
`lean`); declared fallbacks like `verifier: "sage|sympy"` record which
engine actually ran, never a silent downgrade.

## Receipts (verified runs, 2026-06-11, pinned toolchain: Lean REPL v4.30.0, mathlib pinned by the lake project)

From recipe 77's smoke runs across all three rungs:

| Run | Outcome |
|---|---|
| Galois group of `x⁵ − x − 1` (`backend=sage`) | `Transitive group number 5 of degree 5` (= S₅), exact, `complete` |
| "addition of natural numbers is commutative" (`backend=lean`) | citation path: `exact?` returned `Nat.add_comm`, kernel-checked, zero proof tokens → `machine_proved` |
| 3-step calculus chain (`backend=sage`, then `backend=sympy` override) | identical verified results through both engines; Sage's `^`-printed output re-parses cleanly when fed back as `PREV` |

From [recipe 76](../76_lean_proof/readme.md): "for any natural n, n² ≥ n"
proved by an LLM tactic script (`intro n; exact Nat.le_self_pow (by decide)
n`), kernel-checked on the first try; and a repair-cap exhaustion run that
correctly degraded to statement-checked with the badge withheld and delivery
not blocked. From
[recipe 71](../71_linalg_micro_textbook/readme.md)'s `lean_payoffs.spl`, a
post-pass over real micro-textbook entries: `rank_nullity` and
`diagonalization` promoted to `machine_verified, machine_proved` with
kernel-checked mathlib citations and the audited statement stored;
`spectral_theorem` found no citation and **correctly stayed**
`machine_verified`. I consider that last result the most important row in
this section. Failure withholds the badge. It never fakes one.

### Plumbing, not mathematics

Before anyone says it: yes, `n + m = m + n` is a toy, and two of the
`machine_proved` wins are `exact?` citation hits, which you could call grep
over mathlib with a kernel check attached. The demos are deliberately
trivial *as mathematics* because what they demonstrate is plumbing: the
formalize → gate → cite-or-prove → badge path, end to end, with honest
degradation at every exit. And for the actual application (generated
textbook claims, which are instances or light specializations of known
results by construction), a kernel-checked citation into a curated library
is precisely the artifact you want. It is stronger correspondence evidence
than a bespoke proof of a bespoke statement, and it costs near-zero proof
tokens. The system's job is not to do new mathematics. Its job is to make
"an LLM said so" auditable.

## A run from this morning, and a hypothesis about training targets

A fresh receipt (2026-06-12), this one a *caught failure*. I ran the
recipe-67 v2 harness — same chain protocol, now with sanity gates — using
`rnj-1`, Essential AI's 8B model trained specifically for STEM, on the
case-2 cubic ("differentiate 3x³ − x, then factor if needed, finally solve
for x"). The decomposition came back:

```
exp(x)|diff
PREV|factor
x**2 - 4|solve
```

Look closely: every fragment is copied verbatim from the prompt's few-shot
examples. The model didn't misread the problem — it never read it. It
assembled an answer-shaped plan out of the exemplars. The kernel then
verified each step flawlessly (the steps were valid math, just nobody's
question), a plan-level LLM gate — the same model judging its own plan —
waved it through, and only the chain-level gate caught it: `fail | wrong
starting expression: step 1 differentiates exp(x) but problem asks to
differentiate 3*x**3-x`. Status `sanity_error`, explanation withheld,
verified trace preserved. The taxonomy worked; it just worked two LLM calls
later than it should have.

What shipped because of this run: a **deterministic, zero-token plan
validator** now runs before any LLM gate. The chain protocol is mechanically
checkable — line 1 carries the expression, every later line must be
`PREV|<operation>`, every operation from a fixed vocabulary — and this exact
plan dies at line 3 (`x**2 - 4` where `PREV` is required) in microseconds,
for free. The failure taxonomy now separates `plan_format_error`
(deterministic, protocol violated) from `plan_sanity_error` (LLM gate,
plan ≠ intent) from `solver_error` (kernel rejected a step). Defense in
depth, cheapest check first.

The hypothesis this run suggests — held loosely, N=1, written down before
the data as usual: the model did not fail at mathematics. The kernel does
the mathematics. It failed at *transcription* and *protocol citizenship* —
exactly the two jobs the dual-processing architecture actually needs from
the LLM. Optimizing models for STEM is a mission I agree with; the open
question is the target. **Training toward end-to-end answer production may
optimize the wrong target; the same budget aimed at faithful formalization
and routing would be worth more.** A model rewarded for emitting
answer-shaped output may even be actively worse at emitting a plan and
stopping — benchmark-style tuning and pipeline citizenship could be in
tension, not alignment.

That sentence is falsifiable with the instrument already in this repo: the
taxonomy separates "couldn't translate" (`plan_*_error` rates) from
"couldn't compute" (`solver_error`, and the solver-off baseline arm). Run
STEM-tuned and general instruction-tuned models at comparable size across
the same battery: if the general models out-translate the STEM-tuned one
while both lean on the kernel, the architecture-vs-scale question from the
v0.1 benchmark acquires a sharper sibling — **architecture vs training
target**.

## The honest limits

**The formalization-correspondence gap.** `machine_proved` means "this Lean
statement is kernel-checked." It does not mean "the prose claim is proved."
A statement can typecheck and prove cleanly while being not what the prose
says: a flipped quantifier, a vacuous hypothesis, a degenerate
specialization. The informal↔formal correspondence is the one link nothing
machine-checks. Mitigations that ship: (1) wherever the badge appears,
`spl3 cache show` renders the prose claim and the Lean statement side by
side for human audit; (2) an LLM faithfulness judge gates the badge in the
textbook pipeline; (3) citation-first, because a named mathlib lemma whose
docstring matches the prose does not depend on the judge at all.

**Yes, the judge is an LLM.** Its authority is deliberately one-directional:
it can only *withhold* a badge, never grant one. Badges are granted by the
kernel. If the judge hallucinates, the failure mode is a withheld badge on a
true claim, not a granted badge on a false one.

**The eval surface.** The kernels evaluate LLM-emitted expression strings
(`sympify`, `sage_eval`). The threat model is a local research tool running
the operator's own model on the operator's machine, where the kernel
already executes arbitrary code by design. Do not point this at untrusted
input; that is not the deployment story, and I won't pretend it is.

**Scope.** Claims that are instances or light specializations of existing
mathlib lemmas. Not novel theorems, not whole-textbook formalization, and
Lean is never on the default pipeline path. It only ever adds a badge.

## Where this is going

The end state I want is a working mathematician's or physicist's daily
loop, draft → falsify → formalize → search the literature, in one auditable
file. (SPL sigils, for reading the snippet: `@x` names a workflow variable;
`@@x@@` splices its value into code or prompt text.)

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

To be precise about status: **this exact file does not run today.** The
missing piece is `sage_search`, the bounded counterexample hunt; every other
line is shipped and exercised in recipes 76 and 77. I am labeling the gap
rather than hiding it, because the gap between "runs today" and "vision
slide" is exactly what this project is about measuring.

### The training-side dual: a referral network, not a polymath

The rnj-1 section above ends in a hypothesis about training *targets*. Here
is its constructive form. Medicine deliberately separates diagnosis-and-
referral from specialist practice — we do not ask every doctor to be
generalist and specialist at once, because the combined role fails at both.
The model worth training is the **general practitioner**: not a network that
computes Galois groups in its weights, but one with deep knowledge of the
*solver ecosystem* — what each deterministic engine can verify, in which
formalism, at what cost — whose skills are triage ("this is an
elliptic-curve rank question"), referral ("that is Sage/mwrank, not SymPy —
and definitely not me"), translation into the specialist's dialect, reading
the lab report back, and the Tier-4 skill nothing currently rewards: knowing
when *no* specialist covers it and saying so.

The nearest prior art is Berkeley's Gorilla — an LLM trained on API
documentation to emit correct API calls — and today's function-calling
fine-tunes. But those treat tools as flat JSON schemas. SymPy, Sage, Z3,
and Lean/mathlib are not schemas; they are formalisms with semantics,
capability boundaries, and naming cultures. And the referral network does
not stop at deterministic engines: Lean tactic-writing is itself a
*specialist LLM* skill (the ReProver/llmstep niche), so the realistic end
state is a generalist router in front of small specialist models in front
of kernels — Gorilla's idea, extended from APIs to solvers to models
themselves. MCP standardized how agents *discover* tools; what is missing
is a model trained to be good at the discovery-and-referral job itself.
Two design consequences follow. Concepts belong in weights, signatures
belong in retrieval: solver APIs drift, so the GP should read capability
manifests at run time (RAG over the specialist directory) rather than
memorize version-bound signatures — the same logical/physical split SPL
already applies to workflows. And triage happens at every logical level:
which formalism, which engine, which model, which cached result — routing
all the way down.

The part that makes this more than a position piece: **the training data is
free and self-verifying.** Sample an expression, compute ground truth with
the engine, render the problem back into natural language — a verified
(problem → engine → formulation → result) tuple with zero human labeling.
And the verifier ladder is a graded, unfakeable reward function:
`validate_plan` passes or fails deterministically, the kernel accepts or
rejects, the gates rule on faithfulness. The harness this repo built to
*measure* models is, structurally, the harness you would use to *train*
this one — and the cookbook is accidentally its textbook: dozens of worked
referrals, each one (problem shape → engine → protocol → verified outcome).

The application I care most about is not benchmarks. It is the
micro-textbook pipeline (recipes 70–74): generated educational content that
learners only ever receive with a claim-axis badge on it, built to be
re-runnable by anyone, anywhere, on local models. That is the long game.

## Try it

```bash
pip install 'spl-llm[sage]'                          # Sage via passagemath wheels, no source build
python -m sage.repl.ipython_kernel.install --user    # register the 'sagemath' kernel spec
cookbook/tools/lean/setup_lean.sh --with-mathlib     # elan + pinned Lean REPL (optional, ~5 GB oleans)

# Rung 2+ (default backend): math SymPy cannot do
spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm claude_cli \
    --param problem="find the Galois group of x**5 - x - 1 over the rationals"

# Rung 3: a CLAIM, kernel-checked against mathlib, citation-first
spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm claude_cli \
    --param backend=lean --param problem="the square of any real number is nonnegative"

# Baseline arm: same problem, no verifier (the A/B from the benchmark design)
spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm claude_cli \
    --param backend=lean --param enable_solver=false \
    --param problem="the square of any real number is nonnegative"

# Inspect badges, engine of record, and the prose ↔ formal statement side by side
spl3 cache list --badge machine_proved
spl3 cache show <key>
```

(`--llm ADAPTER[:MODEL]` is shorthand; `--adapter NAME --model ID` is the
equivalent legacy spelling. Both appear in the cookbook.)

Everything above reproduces from `.spl` source plus CLI flags. Sage and Lean
are both strictly optional: tests that need them skip cleanly when absent,
and every workflow degrades to the rung it can reach.

## What I am not claiming

- Not that LLMs can do mathematics. The architecture exists precisely
  because, unverified, they confabulate fluently.
- Not that `machine_proved` closes the loop. The correspondence gap is real,
  mitigated, and unsolved.
- Not that the recipe-67 anecdote generalizes. The pre-registered benchmark
  in [v0.1](hackernews-v0.1.md) exists to find out, and its predictions are
  written down before the data so the run can prove me wrong.
- Not that one `rnj-1` run indicts STEM-tuned models. It is a single
  transcript that generated a falsifiable hypothesis about training
  *targets*, plus the instrument to test it — nothing more.

The claim is narrower and checkable: two declarative constructs, three
epistemic grades of verification behind them, engine-of-record and badge
provenance on every cached claim, and a worked end-to-end path from "an LLM
said so" to "the Lean kernel checked it", with every rung of that path in
this repository, runnable today.
