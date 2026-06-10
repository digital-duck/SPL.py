# SageMath + Lean Integration Plan — the Verifier Ladder

> Drafted 2026-06-10 against the current codebase (IPython kernel, `SOLVE`/`ASSERT`,
> `python/<domain>` splc targets, `spl3 judge`, `spl3 cache` all shipped).
> Companion design docs in the zinets repo:
> `zinets/docs/arxiv/micro-textbook/README.md` and
> `zinets/docs/arxiv/micro-textbook/ideas/neurosymbolic_spl_landscape_design_implementation.md`.

**One-line goal:** keep `SOLVE`/`ASSERT` exactly as they are, and widen what stands
behind them — SageMath widens verification *coverage* (more domains, stronger CAS),
Lean raises the verification *ceiling* (proof-checked statements, a new trust badge).

**End state in one breath:** draft → falsify (Sage) → formalize → search the
literature (mathlib) — the conjecture-triage loop researchers run by hand today,
expressed declaratively in SPL and fully auditable (§6).

---

## 0. Motivation (three-fold)

1. **Learning vehicle.** SageMath and Lean are new tools for the author. This plan
   is deliberately structured as *learning by building*: each milestone names the
   concepts to learn first and the canonical text to learn them from (§5). The
   integration work doubles as the guided curriculum the landscape doc calls for
   ("then breadth as needed: … Lean 4 with mathlib — a larger lift").

2. **Micro-textbook enhancement.** SymPy proved the generate-then-verify loop for
   Linear Algebra. Sage unlocks the next domain targets on the generalization path
   (`python/classical_mechanics` via SageManifolds, richer geometry, abstract
   algebra via GAP); Lean upgrades the strongest claims in a textbook from
   *instance-checked* to *proof-checked*, with mathlib as a machine-verified
   citation authority.

3. **SPL as a seamless deterministic + probabilistic orchestration language.**
   The ambitious goal: a working mathematician or physicist should be able to
   express their daily research workflow — *draft with an LLM, verify with a CAS,
   prove with a theorem prover, iterate* — in one declarative language, with the
   probabilistic (`GENERATE`) and deterministic (`SOLVE`/`ASSERT`) steps composing
   seamlessly. No orchestration framework offers machine-checked verification at
   the language level. The verifier ladder is SPL's claim to that ground, and the
   micro-textbook is its first end-to-end demonstration.

---

## 1. Framing: instances vs statements

The two integrations are epistemically different, and the plan keeps them separate:

| Backend | Verifies | Example | Trust badge produced |
|---|---|---|---|
| SymPy (today) | an **instance** | this `(λ, v)` satisfies `A·v = λ·v` | `machine_verified` |
| **SageMath** | an **instance**, in domains SymPy can't reach or handles weakly | conic classification over exact fields; Galois group of a polynomial; curvature on a manifold | `machine_verified` |
| **Lean 4 + mathlib** | a **statement** (universally quantified) | `∀` real symmetric `A`, eigenvalues are real — *the spectral theorem itself*, not one worked example | `machine_proved` *(new)* |

This is the **verifier ladder**: numeric spot-check (NumPy) → exact symbolic
instance (SymPy/Sage) → machine-checked proof (Lean). Same two SPL constructs at
every rung.

**Locked design decisions this plan must not violate** (from the micro-textbook README):

- No new SPL constructs. `SOLVE`/`ASSERT` are sufficient.
- The IPython kernel is the universal interface — native engines are thin-wrapped
  *inside* the kernel, never given their own adapter layer.
- Domain vocabulary lives in the Python target library (`graph_lib` /
  `<domain>_graph.py`), not in SPL grammar.

Both integrations are pure backend work: **zero parser/AST changes**.

---

## 2. Part A — SageMath

### A.1 Why Sage (what SymPy cannot do)

Sage is an umbrella CAS wrapping Maxima, GAP, Singular, PARI, FLINT — and it
*includes* SymPy, so every existing verifier runs unchanged inside it. What it adds:

- **`python/intro_geometry` upgrades** — exact projective geometry, conic
  classification over ℚ; `sympy.geometry` is thin here.
- **`python/classical_mechanics`** — SageManifolds for differential geometry /
  tensor calculus (Lagrangian mechanics payoff concepts).
- **Future domains** — abstract algebra (GAP: a group-theory micro-textbook),
  number theory (PARI), commutative algebra (Singular). Each is just a new
  `<domain>_graph.yaml` with `verifier: "sage"` nodes; the SPL workflow is unchanged.

### A.2 Integration mechanism: a kernel spec, not an adapter

Sage installs its own Jupyter kernel spec (`sagemath`). `jupyter_client`'s
`KernelManager` can launch any installed spec — and `spl3/kernel.py:184` currently
hardcodes `KernelManager(kernel_name="python3")`. **That one line is the
integration point.** The kernel architecture (lazy start, thread-safety, error
bridging via `KernelExecutionError → ToolFailed`, `--kernel-scope`) is inherited
for free.

> ⚠️ **Environment gap — the hidden work in A-1/A-2 (narrower than it first
> looks).** The Sage kernel runs **Sage's own Python**, not `spl123`'s. The
> *import* side of this is already solved by the existing design, verified in
> code: the transpiler emits verifier helpers **verbatim into the setup cell**
> (`transpiler_domain_graph.py`), and the generated notebook locates
> `linalg_graph.py` by path ("cookbook recipe directory or current dir") — there
> is no package install to break. The residual risks are:
>
> 1. **Sage's Python version** — the path-located domain lib must run on it
>    (pure Python, stdlib + NetworkX/SymPy only today, so likely fine — verify).
> 2. **Sage's bundled SymPy version** — "Sage includes SymPy" means *Sage's*
>    SymPy at *Sage's* version; existing verifiers must pass against it.
> 3. **The Sage preparser** — semantic, not import, breakage (see the
>    granularity note below).
>
> The A-1 spike answers all three at once: run one existing SymPy verifier under
> the Sage kernel. This can still grow A-1 from S to M — size after the spike,
> not before.

Changes, in dependency order:

1. **`kernel.py`** — `IPythonKernel(kernel_name: str = "python3", ...)`; thread
   through scope/pool handling. (`KernelSession`, the in-process fallback, stays
   python3-only — document that.)
2. **CLI** — `spl3 run --kernel --kernel-name sagemath`. Probe
   `jupyter kernelspec list` on startup; missing spec → actionable error with
   install instructions (conda-forge `sage` or distro package), never a stack trace.
3. **`DomainConfig`** (`splc/transpiler_domain_textbook.py`) — new `kernel_name`
   field, sourced from the domain YAML. The emitted `.ipynb` sets
   `metadata.kernelspec` accordingly, so the learner's notebook opens under the
   Sage kernel — *the artifact carries its runtime*, consistent with DODA.
4. **`graph_lib`** — accept `verifier: "sage"` per node (today: `"sympy" | "z3" |
   "numpy"`); the generic verifier shape gains a Sage branch (`from sage.all
   import ...` thin wrappers, e.g. `verify_conic_class`, `verify_curvature`).
5. **Fallback tiering** (same honesty principle as the adapter-tiered constrained
   generation design): a node may declare `verifier: "sage|sympy"` — if the
   `sagemath` kernelspec is absent, fall back to the SymPy check where one exists;
   record *which engine actually verified* in the cell annotation / cache
   provenance. No silent downgrade: Sage-only nodes fail fast with an install hint.

   **Granularity note.** Kernel selection is a *run-level* decision
   (`DomainConfig.kernel_name`, one kernelspec per `.ipynb`), while `verifier:`
   declarations are *node-level*. The reconciliation policy, explicitly: if any
   node in the domain requires Sage, the whole notebook runs under the Sage
   kernel. SymPy nodes still run there (Sage bundles SymPy) — **but not
   unchanged**: the Sage kernel applies its *preparser*, so `^` means power (not
   XOR), integer literals become Sage `Integer`s, and `1/2` is a `Rational`, not
   a float. Mitigation: emit `preparser(False)` in the setup cell before any
   pure-Python verifier code, or explicitly test the verifiers under preparsing.
   The entire domain also then hard-requires the heavy Sage dependency; that is
   the price of a single mixed domain and should be a conscious YAML-author
   choice. In the
   fallback case the whole notebook runs under `python3`: `"sage|sympy"` nodes
   downgrade per above, `"sage"`-only nodes fail fast. The emitted `.ipynb`
   kernelspec metadata records the kernel that **actually ran** — engine-of-record
   applies to the artifact, not just the cache.

**Alternative considered:** install Sage via conda-forge into the `spl123` env and
`from sage.all import *` under the ordinary `python3` kernel. Workable, but the
kernel-spec route is preferred because the `.ipynb` deliverable then declares the
right kernel for learners, and it keeps the heavy Sage dependency out of the core
env. Document the conda route as a developer convenience only.

### A.3 Milestones

| ID | Deliverable | Size |
|---|---|---|
| A-1 | `kernel_name` plumbing + CLI flag + kernelspec probe + environment-gap spike (see §A.2 box) + tests (skipped when Sage absent) | S/M — size after the spike |
| A-2 | `verifier: "sage"` in `graph_lib` + `DomainConfig.kernel_name` + `.ipynb` kernelspec emission | M |
| A-3 | Fallback policy (`"sage|sympy"`) + engine-of-record in provenance | S |
| A-4 | End-to-end demo: upgrade 3–5 geometry-domain nodes (conics, projective duality) to Sage verifiers; one SageManifolds cell as the `classical_mechanics` seed | M |

Parity checks for A-1: state persistence across `CALL` steps and exception recovery
must pass under the Sage kernel exactly as under python3 (reuse `tests/test_kernel.py`
parameterized over kernel specs). **Plus the test that will actually fail first:
import the domain library and run one existing SymPy verifier under the Sage
kernel** — this is what proves the environment-gap decision works. Mark the Sage
leg of the parameterized suite as a separate slow/optional tier (Sage kernel
startup is 5–15 s); the default test loop stays fast.

*A-4 naming check:* the repo's canonical artifact is `geometry_graph.py`
(cookbook/73) plus the YAML generator in cookbook/74 — target whichever is
canonical at implementation time, not the filename written here.

---

## 3. Part B — Lean 4 + mathlib

### B.1 Role: proof-grade verification and mathlib as citation authority

Three concrete uses inside the micro-textbook pipeline, in increasing ambition:

1. **Statement checking** — the LLM formalizes a textbook claim as a Lean
   statement; we elaborate `example : <stmt> := by sorry`. If it typechecks (only
   the `sorry` warning), the *formalization* is well-formed. Catches a whole class
   of subtly-wrong claims at near-zero proof effort.
2. **Proof checking** — the LLM (or a human author) supplies a proof term/tactic
   script; Lean checks it. Success ⇒ the claim is `machine_proved`.
3. **mathlib citation** (stretch) — run `exact?` against the statement; a hit means
   the textbook claim *is* a named mathlib lemma (e.g. the spectral-theorem family
   around `Matrix.IsHermitian.eigenvalues_real`). Surface the mathlib name as a
   provenance link — an authoritative, machine-checked citation in the notebook.
   *Caveat:* `exact?` returns a proof **term**, not a citation — extracting "the
   mathlib lemma name" requires parsing the suggestion, and multi-lemma terms are
   common. For the citation use case specifically, Loogle / LeanSearch over HTTP
   may be cheaper and more precise than local `exact?` proof search (at the cost
   of a network dependency — note it as an alternative, not the default).

**Trust model — badges, not a ladder (D1 resolved).** Earlier drafts framed this
as one linear chain (`machine_generated → machine_verified → machine_proved →
ai_reviewed → canonical`). That's wrong, because the grades attest **different
things on orthogonal axes**:

| Axis | Badges | Attests |
|---|---|---|
| **Claim trust** | `machine_verified` (CAS instance) → `machine_proved` (kernel-checked statement) | the mathematical content |
| **Exposition trust** | `ai_reviewed`, human review | the prose, pedagogy, narrative |

A section can carry any combination — a kernel-checked statement with confusing
exposition still needs review, and human review need not wait for AI review (the
micro-textbook process is agile, not a waterfall). `canonical` remains the
composite end state: strongest available badge on *both* axes. Within the claim
axis the ordering is strict (`machine_proved` outranks `machine_verified`);
across axes there is no ordering. B-4 implements this as a badge *set* in cache
provenance and the notebook rendering, not a single ordinal. **Confirmed in
code:** the cache *does* assume one ordinal today — `PROVENANCE_TIERS =
[machine_generated, machine_verified, ai_reviewed, human_verified]` in
`spl3/cache/types.py` with rank-based `promote()` that refuses downgrade
(`meta.py`), and `spl3 judge --cache-key` promotes along it. That refactor is
the first thing B-4 changes, and it touches `cache/types|meta|content|cli` plus
the judge wiring. Note also a naming drift to reconcile there: the code's top
tier is `human_verified`, while the micro-textbook docs say `canonical`.

### B.2 Integration mechanism: kernel-resident client → persistent Lean REPL

Lean is not Python, but the locked decision stands: the IPython kernel remains the
universal interface. The bridge is a thin Python client *inside* the kernel that
talks to a persistent **`leanprover-community/repl`** process (JSON over
stdin/stdout):

```
SOLVE/ASSERT ──► IPython kernel ──► lean_bridge.LeanREPL ──► lake env repl (mathlib loaded, persistent)
```

Why persistent: a cold `lake env lean file.lean` with mathlib costs 10–40 s per
check; the REPL imports mathlib once and amortizes it — exactly as the IPython
kernel amortizes Python startup. Same pattern, one level down.

New module `spl3/lean_bridge.py` (prototype can start in `cookbook/tools/`):

- `LeanREPL.start(project_dir)` — spawn `lake env repl`, warm up with
  `{"cmd": "import Mathlib"}`; restart-on-crash mirroring the kernel's
  `self_healing` mode.
- `lean_check(code, timeout=60) -> {"ok": bool, "errors": [...], "sorries": [...]}`
- `lean_statement_ok(stmt)` — use case 1 above.
- `lean_find(stmt)` — `exact?` probe, use case 3.

**REPL state hygiene (B-1 requirement, not a nice-to-have).** The REPL threads
environment state via `env` ids — every command returns a new one. If `lean_check`
doesn't manage these, sequential checks pollute each other (definitions from check
N visible in check N+1). The pattern: capture the `env` id returned by the warm-up
`import Mathlib`, then pass that **same** id with every check — each check gets a
fresh environment with mathlib loaded, giving isolation *and* amortization. Also
pin the REPL revision to the Lean toolchain version (they move together); fold
this into D2.

Loaded like any domain library — no grammar change:

```spl
CALL run_python('import lean_bridge; lean = lean_bridge.LeanREPL.start("@@lean_project@@")') INTO @_

GENERATE formalize_claim(@claim) INTO @lean_stmt
ASSERT lean.statement_ok(@@lean_stmt@@)
    OTHERWISE RETRY GENERATE fix_formalization(@claim, @@lean.last_errors@@)

GENERATE write_proof(@lean_stmt) INTO @proof
ASSERT lean.check(@@proof@@)
    OTHERWISE RETRY GENERATE repair_proof(@proof, @@lean.last_errors@@)
```

The `OTHERWISE RETRY GENERATE` loop with Lean error messages fed back is the
generate-then-verify spine at proof grade. Cap retries (2–3); on exhaustion the
section keeps its CAS-level `machine_verified` tier — Lean failure never blocks
delivery, it only withholds the higher badge.

### B.3 Environment and operations

- **Toolchain:** `elan` + a `lake` project pinned to a mathlib release tag;
  `lake exe cache get` pulls prebuilt oleans (~5 GB). Strictly optional dependency:
  all Lean tests `skipif` when `elan`/project absent; the bridge lazy-starts.
- **Caching:** a Lean check is deterministic given (toolchain version, mathlib rev,
  code) — store results in `spl3 cache` Layer 2 with the mathlib rev as a
  dependency hash. Warm re-runs of a textbook build pay zero Lean time; bumping
  mathlib cascades invalidation through the existing dep-graph machinery.
- **Timeouts:** per-check default 60 s (`exact?` proof search capped tighter);
  restart the REPL on timeout to clear stuck elaboration. Note a restart re-pays
  the 10–40 s mathlib import — for batch textbook builds, consider warming the
  replacement REPL while the old one drains, so one stuck elaboration doesn't
  stall the whole build.

### B.4 Scope discipline (honest limits)

Per the landscape doc, neurosymbolic wins concentrate where formal structure is
crisp — and autoformalization of arbitrary prose is an open research problem. So:

- **In scope:** claims that are instances or light specializations of existing
  mathlib lemmas. Linear algebra over ℝ/ℂ is well covered in mathlib — start with
  the recipe-71 payoff concepts (rank–nullity, spectral theorem statement,
  diagonalizability criteria).
- **Out of scope:** proving novel theorems; formalizing whole sections; any Lean
  requirement on the default pipeline path.

**The formalization-correspondence gap (the honest limit of `machine_proved`).**
Statement checking verifies *well-formedness*, and proof checking verifies *the
Lean statement* — but a statement can typecheck and prove cleanly while being
**not what the prose claims**: a flipped quantifier, a vacuous hypothesis, a
degenerate specialization that's trivially true. The informal↔formal
correspondence is the one link in the chain nothing machine-checks. The
`machine_proved` badge therefore means "this Lean statement is kernel-checked,"
not "the textbook claim is proved." Mitigations, all in scope:

1. **Render the Lean statement alongside the prose claim** wherever the badge
   appears — a human can audit correspondence at a glance. (B-4 requirement.)
2. **LLM-judge faithfulness check** — "does this formalization capture this prose
   claim?" via the existing `spl3 judge`, wired into B-2. The right tool: a
   probabilistic check on the one probabilistic link.
3. **Prefer the citation path** — a hit on a *named* mathlib lemma (B-5) whose
   docstring matches the prose is much stronger correspondence evidence than a
   bespoke proof of a bespoke statement.

### B.5 Milestones

| ID | Deliverable | Size |
|---|---|---|
| B-1 | `lean_bridge` prototype: REPL session mgmt (incl. `env`-id hygiene, §B.2), `lean_check`, timeout/restart, tests | M |
| B-2 | Statement-level checking (`lean_statement_ok`) wired into recipe 71 for 3–5 payoff concepts, + `spl3 judge` faithfulness check on the formalization (§B.4) | M |
| B-3 | Proof checking + `OTHERWISE RETRY` repair-loop recipe (`cookbook/7x_lean_verify/`) | M |
| B-4 | `machine_proved` badge: badge-*set* model refactor across `cache/types|meta|content|cli` + `judge --cache-key` (ordinal today — §B.1), tier-naming reconciliation (`human_verified` vs `canonical`), prose+statement side-by-side rendering | M |
| B-5 | *(stretch)* mathlib-citation mode — `exact?` with suggestion parsing, or Loogle/LeanSearch (§B.1 caveat); claims link to mathlib lemma names | M/R |

---

## 4. Sequencing and recommendation

**Sage first, Lean second.**

- Sage (A-1…A-4) is a small lift — one constructor parameter plus YAML/transpiler
  plumbing, everything else inherited — and immediately unblocks the
  `classical_mechanics` and richer-geometry domain targets (the stated
  generalization path).
- Lean (B-1…B-4) is the bigger lift (toolchain ops, REPL bridge, repair-loop
  prompting) but the bigger claim: the verifier ladder gives the neurosymbolic-SPL
  paper a clean §9 story — *same two constructs, three epistemic grades of
  verification* — and `machine_proved` is a differentiator no orchestration
  framework offers at the language level.
- A-1 (kernel_name plumbing) is pure infrastructure that any future kernel
  (Julia for numerics, R for statistics domains) reuses — do it first regardless.

**Decision points** (none block starting):

- **D1** — ~~`machine_proved` placement in the trust-tier order~~ **Resolved:**
  badges on orthogonal axes, not a linear ladder — see §B.1. Claim-trust and
  exposition-trust grade different things; the process is agile, not waterfall.
- **D2** — mathlib pin policy: fixed release per textbook build (recommended) vs
  tracking latest. Includes pinning the `repl` revision to the toolchain version
  (§B.2).
- **D3** — whether `lean_bridge` lives in `spl3/` from day one or graduates from
  `cookbook/tools/` after B-2 (recommended: graduate after B-2, the same path
  `linalg_graph` took).
- **D4** *(new, gates A-1 sizing)* — environment-gap strategy for the Sage kernel:
  `sys.path` injection vs install-into-Sage-env vs source-over-the-wire (§A.2 box).
  Settle with a spike at the start of A-1.

---

## 5. Learning path woven into the milestones

Since both tools are new, each milestone names what to learn first and where.
The rule: *never learn ahead of the milestone that needs it.*

| Milestone | Learn first | Source |
|---|---|---|
| A-1 | Jupyter kernel specs, `jupyter_client` lifecycle (already familiar from `kernel.py`) | `jupyter kernelspec list`; jupyter_client docs |
| A-2 | Sage basics: `sage.all`, exact rings (ℚ, ℝ algebraic), symbolic vs numeric; how Sage wraps SymPy | Sage tutorial — https://doc.sagemath.org/html/en/tutorial/ |
| A-4 | `sage.geometry` (conics, projective space); SageManifolds first steps (charts, metrics, curvature) | SageManifolds examples — https://sagemanifolds.obspm.fr/examples.html |
| B-1 | Lean 4 syntax, the proof-state model, `example`/`theorem`/`sorry`; running `lake` | *Theorem Proving in Lean 4* (free) — https://leanprover.github.io/theorem_proving_in_lean4/ |
| B-2 | mathlib naming conventions, `exact?`/`apply?`, searching mathlib (Loogle, Moogle) | *Mathematics in Lean* (free) — https://leanprover-community.github.io/mathematics_in_lean/ |
| B-3 | Basic tactics (`simp`, `ring`, `linarith`, `norm_num`), reading Lean error messages (this feeds the repair-loop prompts) | *Mathematics in Lean* ch. 2–5; Lean Zulip archive |

The payoff structure mirrors the micro-textbook's own thesis: the verifier you
build to check the author's content *is* the lab the learner plays in. Here, the
integration you build to check SPL workflows is the curriculum you learn Sage and
Lean through.

---

## 6. End-state vision: SPL for research workflows

When A and B land, this is a valid daily-driver workflow for a mathematician or
physicist — one language, probabilistic and deterministic steps interleaved:

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

Draft → falsify → formalize → search the literature (mathlib) — the
conjecture-triage loop researchers run by hand today, expressed declaratively and
fully auditable. That is the target motivation (3) points at.
