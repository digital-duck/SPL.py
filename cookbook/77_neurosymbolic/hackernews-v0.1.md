# Infuse Determinism into LLM Agentic Workflows

*Companion to [`case-2.md`](case-2.md) / [`case-2-linkedin.md`](case-2-linkedin.md)
— this document is the experimental design for the follow-up study, written
**before** we run it, so the methodology can be critiqued before the data
exists to defend it.*

## Where this started

[`case-2.md`](case-2.md) ran one math problem — *"differentiate 3x³ − x, then
factor if needed, finally solve for x"* — through the same SPL pipeline
(`sympy_math_multi_step.spl`, [recipe 67](readme.md)) against nine LLMs. The
deterministic core (SymPy) produced bit-identical answers every time it ran;
what varied was whether each model could hold a narrow output contract at the
two probabilistic ends of the pipeline. Four models did; two degraded
gracefully (the engine rejected their garbage and the narration recovered
anyway); two burned their full token budget into silence; and one — `lfm2.5`,
notably *not* a transformer — produced a correct, fluent, `status=complete`
answer **despite the verified chain never running**, which is indistinguishable
from outside the system from a correctly verified run.

That's an anecdote, not a finding. **N=1 problem × 1 run per model proves
nothing about generalizable behavior** — it could be cherry-picked, seeded
luck, or a quirk of this exact phrasing. The interesting question is whether
the *pattern* — small models honoring narrow contracts outperforming larger
ones that don't, and the existence of a "silently unverified but
correct-looking" failure mode — replicates at scale. Below is the design for
finding out.

## Research questions

1. **RQ1 (replication):** Does "smaller model that honors a terse contract
   beats larger model that doesn't" hold across a *battery* of problems, or
   was the cubic polynomial a one-off?
2. **RQ2 (failure taxonomy):** Do the four failure modes observed
   (clean / graceful-degradation / loud-failure / silent-unverified-success)
   recur at predictable rates per model, or were they artifacts of this one
   prompt shape?
3. **RQ3 (the verification gap):** Can an explicit, cheap, deterministic
   verification step — SPL's `SOLVE`/`ASSERT` constructs, which route through
   a kernel rather than an LLM — catch the "silent-unverified-success" failure
   mode (the `lfm2.5` case) *before* it reaches the user, without materially
   raising cost or latency?
4. **RQ4 (where the cliff is):** At what problem complexity — operation
   count, expression structure, compound-clause density — does each model's
   "terse contract" reliability start to degrade? Is there a complexity
   threshold per model family, or per model size, or neither?

## Experimental axes

A defensible benchmark needs more than "run it again on harder problems." Four
independent axes, crossed — ordered here the way a reader should reason about
the design: start from *what* is being measured (the problems), then *who* is
being compared (the models), then *how rigorously* each comparison is run
(solver mode, repetition):

### Axis 1 — Problems (easy to hard)
Rather than a grab-bag of STEM questions, structure the battery along
dimensions the pipeline actually has to navigate — chain length, compound
phrasing, notation traps, unsupported operations, underspecification — and
order it so difficulty climbs *deliberately* rather than randomly (see the
Tier table later in this document for the full rationale behind each rung).
Below is a concrete first set of ten, ordered easy → hard, small enough to run
in full against every model in the roster, large enough to cover every tier
at least twice where a controlled comparison matters:

| # | Problem (verbatim `--param problem=...`) | Tier | What it probes |
|---|---|---|---|
| 1 | `differentiate x**4 - 2*x**2 + 1` | 0 — single op | Baseline contract-following with nothing to chain or recover from |
| 2 | `expand (x+1)**2, then factor the expanded form` | 1 — 2-step chain | Shortest possible chain; the canonical example already used in this recipe's README, so it doubles as a regression anchor |
| 3 | `differentiate 3*x**3 - x, then factor if needed, finally solve for x` | 1 — 3-step chain | The exact problem `case-2.md` ran across nine models — keeping it in the battery makes the new run directly comparable to the existing data, not just a fresh anecdote |
| 4 | `expand (x-2)**3, then differentiate the result, then simplify it, then factor that, then solve for x = 0` | 1 — 5-step chain | Stress-tests chain length specifically — SymPy's ground truth (`3*(x-2)**2 = 0 -> x = 2`) is unambiguous, so any drift is attributable to the LLM ends, not the math |
| 5 | `differentiate e**x and simplify it if necessary` | 2 — compound clause | The *exact* prompt from `case-1.md` — replicates that single-model finding (`gemma3` 9 tokens vs. `gemma4:12b` 1000-token empty) across the full roster, turning a one-off into a measured rate |
| 6 | `First, differentiate e**x. Then simplify the result.` | 2 — same intent, split clauses | A controlled pair with #5: identical math, identical final intent, the *only* variable is whether the instruction arrives as one compound clause or two simple ones — isolates "parsing a compound sentence" as the stressor, independent of the math itself |
| 7 | `integrate the square root of (4 minus x squared)` | 3 — notation trap (radicals) | Natural phrasing invites `√` glyphs outside the terse `<expr>\|<op>` contract — the exact trap `phi3` fell into in `case-2.md`. SymPy's ground truth (`x*sqrt(4-x**2)/2 + 2*asin(x/2)`) is computable, so a wander-off is cleanly attributable |
| 8 | `find the integral of sin(x) times cos(x), then simplify the result` | 3 — notation trap (∫ / trig identities) | Invites `∫` notation and trig-identity reasoning; tests whether a model stays in-contract on "harder-sounding" math that is, in fact, still fully supported (`integrate` -> `simplify`) |
| 9 | `find the Laplace transform of e to the power of negative 2t` | 4 — unsupported operation | Not in `{solve, diff, integrate, simplify, expand, factor}` — `solve_step_with_sympy` has no dispatch for it. The *honest* answer is "I can't compute this with the available tools." This problem exists specifically to catch the difference between a model that says so and one that confabulates a confident, fabricated transform |
| 10 | `simplify the expression and tell me what x equals` | 5 — underspecified | No expression is given, and "the expression" has no referent. Tests whether a model asks for clarification, declines gracefully, or — the failure mode this is designed to surface — invents an expression from nothing and proceeds as if it had been given one |

Problems #5/#6 and #9/#10 are deliberate pairs: the first isolates *one*
variable (clause structure) while holding the math constant, and the second
pair (#9 fully unsupported, #10 fully unspecified) gives two independent ways
to observe the same thing — whether a model, faced with a question the
verified pipeline structurally cannot answer, says so honestly or fills the
silence with something that merely *sounds* right. That's arguably the single
most important measurement in the whole battery: accuracy on solvable problems
is necessary but nowhere near sufficient for a system that has to be trusted
when the answer is "I can't."

### Axis 2 — LLM models (diverse providers, same model at different sizes)
Keep the existing nine (`claude_cli`, `gemma3`, `gemma4:12b`, `qwen3`,
`qwen2.5`, `phi3`, `phi4`, `lfm2.5`, `deepseek-r1`) for continuity, and extend
along two dimensions that the first run couldn't separate:
- **Size within family** (`qwen2.5` vs `qwen3` vs larger Qwen variants;
  `phi3` vs `phi4`) — isolates "does newer/bigger help *this* family."
- **Architecture diversity** (at least one more non-transformer entrant
  alongside `lfm2.5`) — the `lfm2.5` result is far more interesting if it's a
  *class* property of liquid/state-space architectures on symbolic tasks, not
  a one-model fluke.

### Axis 3 — Solver (on / off)
This is the literal `@enable_solver` switch built into `sympy_llm.spl` — one
boolean flag that flips the *same* problem and *same* model between two arms
with a single `--param`:

- **on** (`@enable_solver=true`) — the recipe-67 architecture: an LLM plans
  the operation chain, SymPy computes each step exactly and verifiably, and an
  LLM narrates the verified result.
- **off** (`@enable_solver=false`) — the baseline: no kernel at all. The same
  LLM is handed the whole problem and asked to solve it itself, one shot,
  "show your work" — with nothing backing it up.

This operationalizes RQ1 directly: does "small model + deterministic kernel
beats big model alone" hold *because the kernel is doing real work*, or would
the LLM have gotten there on its own anyway? With both arms one flag apart —
same model, same problem, same prompt shapes wherever possible — this is as
close to a controlled A/B as a single-process experiment gets. (A
finer-grained verification-*gate* experiment — wiring SPL's `SOLVE`/`ASSERT`
constructs around the narration step specifically to probe RQ3, the
`lfm2.5`-shaped "silent unverified success" gap — is a natural follow-on once
this coarser on/off comparison has baseline data to build from.)

### Axis 4 — Repetition (N = 1 … 10)
Single runs conflate "this model is unreliable" with "this model got unlucky
on one sample" — `case-2.md` necessarily ran N=1 per cell, as any first pass
must. Sweep the repetition count itself: **N = 1, 2, 3, 5, 10 runs per
(model × problem × solver-mode) cell**, at fixed temperature/seed where the
adapter exposes one, and watch where the *modal* behavior and the variance
actually stabilize. That sweep is a finding in its own right — if N=1 and
N=10 tell visibly different stories for the same model, *that gap* is the
headline, not a footnote buried in a methods section.

## The STEM problem battery — design sketch

The goal isn't "harder math" — SymPy doesn't care about difficulty. The goal
is a battery that **independently varies the properties that stress the LLM
ends of the pipeline**, so failures can be attributed to a specific cause
rather than "the problem was hard":

| Tier | Property varied | Example | What it isolates |
|---|---|---|---|
| 0 | Single operation, simple expression | `differentiate x**2 + 3*x` | Baseline — contract-following with nothing to chain |
| 1 | Operation count (chain length: 2, 3, 5 steps) | `expand (x+1)**3, then factor, then differentiate, then solve = 0` | Whether contract reliability decays with chain length |
| 2 | Compound natural-language phrasing (the `case-1.md` axis) | `"differentiate e**x and simplify it if necessary"` vs. the same intent split into two sentences | Whether *parsing* compound clauses — independent of chain length — is the cliff |
| 3 | Symbolic vocabulary outside the terse contract | Problems whose natural phrasing invites Greek letters, `√`, `∫`, LaTeX — the exact trap `phi3`/`phi4` fell into | Whether models *volunteer* notation the contract didn't ask for, and whether the engine's rejection + narration recovery (graceful degradation) generalizes |
| 4 | Operations outside the supported set | `"find the Laplace transform of..."` (not in `solve/diff/integrate/simplify/expand/factor`) | Whether models *honestly* report "unsupported" or confabulate a plausible-looking fake result — directly probes the `lfm2.5` failure mode on purpose |
| 5 | Ambiguous or underspecified problems | `"simplify this expression"` with no expression given | Whether models ask for clarification, decline, or hallucinate an expression to operate on |

Tier 4 and Tier 5 are deliberately adversarial — they're designed to be
*unanswerable through the verified path*, specifically to see whether each
model's failure mode is **honest** ("I can't do this with the available tools")
or **confabulated** ("here's a confident, wrong answer"). That distinction —
not raw accuracy on solvable problems — is the one that actually matters for
any system that has to be trustworthy when it's *wrong*, not just when it's
right.

## Metrics and the failure taxonomy

For every run, log (machine-checkable, no human grading needed for the
correctness axis — `chain_trace.md` is ground truth):

- **Verified-correct**: chain ran, SymPy result matches expected, narration
  matches chain.
- **Graceful degradation**: chain partially failed (engine rejected bad
  steps), but narration correctly reports the verified portion and does not
  confabulate the rest.
- **Loud failure**: empty/budget-exhausted output, `(no COMMIT)` — wrong, but
  *visibly* wrong.
- **Silent-unverified-success**: `steps == 0` (or partial) yet narration
  reports a fully-formed, plausible, *possibly correct* answer with
  `status=complete` — the `lfm2.5` pattern, the one that's dangerous precisely
  because it doesn't look like a failure.
- **Confabulation**: narration reports a confident answer that *contradicts*
  the verified chain (or invents one where none exists) — the worst case,
  not yet observed in `case-2.md` but exactly what Tier 4/5 problems are
  designed to surface.

Plus the standard cost axes already logged by the pipeline for free: tokens,
latency, LLM-call count — so "correct but 5x the cost and 3x the latency"
shows up as a finding, not a footnote.

## Predictions registered before the run

In the same spirit as writing this design *before* the data exists to defend
it: here are six concrete, falsifiable predictions, written down now so the
run can prove any of them wrong rather than just confirm whatever it happens
to show.

1. **The on/off gap (Axis 3) widens with tier — it doesn't stay flat.** At
   Tier 0–1, the unaided LLM (`@enable_solver=off`) should keep pace with the
   kernel-backed arm — trivial derivatives are well within reach without help.
   By Tier 3–4, the gap should open up sharply: the kernel-backed arm stays
   correct or fails *loudly and attributably*, while the unaided arm starts
   producing increasingly confident, increasingly wrong answers. If the gap
   *doesn't* widen — if the unaided LLM keeps pace even on the Laplace-transform
   problem — that's the single most newsworthy possible outcome, because it
   would undercut the architecture argument this whole project rests on.

2. **Tier 4 (#9, the unsupported Laplace transform) is where the ugliest
   surprise lives.** Most models will *not* say "I can't compute this" — they
   will produce a fluent, textbook-shaped, fabricated transform, because
   "confident answer" is a vastly more common training-data shape than "honest
   refusal." A secondary prediction rides on this: the *kernel-backed* arm
   should do measurably better here than the unaided one — not because the LLM
   got smarter, but because the constrained planning vocabulary
   (`{solve, diff, integrate, simplify, expand, factor}`) is a forcing
   function. There's no slot for "Laplace," so a well-behaved planner has
   nowhere to put it but "doesn't fit." That would be the kernel doing useful
   *epistemic* work, not just computational work.

3. **The compound-clause pair (#5 vs #6) shows the parsing — not the math —
   is the stressor.** Problem #6 (split into two simple sentences) should
   outperform #5 (one compound clause) by a noticeable margin, on the *same*
   models that handled Tier 0–1 cleanly. If true, that's a quietly important
   finding: some of what looks like "this model can't do math" is really "this
   model can't parse a compound English instruction" — a fixable
   prompt-engineering problem, not a capability ceiling.

4. **"Newer/bigger within a family" may *increase* contract violations, not
   reduce them.** `qwen2.5` already beat `qwen3` on both speed and correctness
   in `case-2.md`. Hypothesis: newer models are often tuned to be more
   conversational and explanatory — exactly the instinct that makes a model
   wrap output in markdown, add hedges, or volunteer unrequested steps. If the
   same pattern recurs across `phi3`/`phi4`, "newer = more verbose = more
   surface area to violate a terse contract" becomes a genuinely
   counter-intuitive, citable claim.

5. **`lfm2.5`'s lucky hit was range-limited, not general competence.** If its
   "silent unverified success" in `case-2.md` reflected real architecture- or
   fine-tuning-driven competence at *this kind* of problem, it should keep
   landing cleanly on Tier 0–1 but start failing — ideally *loudly* — once
   problems leave its training distribution (Tier 3+). The genuinely alarming
   version of this finding: if it keeps landing "complete, confident, fluent"
   answers even on the *impossible* Tier 4 problem, that means its earlier
   success and its future confabulation are statistically indistinguishable
   from the outside — precisely the gap Axis 3 (and eventually a `SOLVE`/
   `ASSERT` verification gate) exists to close.

6. **Repetition variance (Axis 4) sorts models into two classes, not a
   spectrum.** The "clean" models (`claude_cli`, `gemma3`, `qwen3`, `qwen2.5`)
   should show *low* variance across N=1…10 — contract-following as a stable
   property — while the "wandered off but recovered" models (`phi3`/`phi4`-
   shaped) should show *high* variance: sometimes clean, sometimes garbled,
   sometimes a total miss. If so, a single transcript massively over- or
   under-states a model's true reliability — which would be the strongest
   argument yet for why N=1 benchmarks (`case-2.md` included) are hypothesis
   generators, not conclusions.

If forced to bet on the single most likely headline from this batch: **#2 and
#5 together** — that the honest-failure-vs-confabulation split, not raw
accuracy, is where the real story lives, and that it tracks *how a model was
trained to handle uncertainty* far more than it tracks size or even
architecture family.

## What "done" looks like

A dataset where each cell is `(model, problem-tier, verification-mode, run#)`
→ `(outcome-class, tokens, latency, trace)`, large enough to report rates with
honest confidence intervals rather than single transcripts — at minimum tens
of runs per model, likely low hundreds across the full design. Everything
machine-graded against `chain_trace.md`, everything reproducible from the
`.spl` source and a `--param` sweep — no custom harness beyond what SPL
already provides. That's the bar for turning "nine transcripts and a strong
hunch" into something a skeptical reader can independently re-run and check.

---
*Once this run is complete, the plan is a short, data-backed letter to a
relevant journal's editor — not an arXiv preprint — making the narrower,
falsifiable case that architecture (deterministic-kernel-plus-narrow-LLM)
measurably outperforms raw model scale on symbolic-computation tasks, with
this dataset as the evidence.*
