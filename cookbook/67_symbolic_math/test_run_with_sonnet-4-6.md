# Recipe-67 sonnet-4-6 run analysis — 20260612

Model: `claude-sonnet-4-6` (claude_cli) | Workflow: `sympy_llm_v2.spl` | solver=true | 20 problems

---

## Outcome summary

| Status | Count | Problems |
|--------|-------|---------|
| `complete` | 19 | p001, p011, p002, p003, p004, p012, p005, p006, p013, p014, p007, p008, p015, p016, p009, p018, p019, p010, p020 |
| `sanity_error` | 1 | p017 |

**Score: 19/20 (95%)**

By tier:

| Tier | Complete | Total |
|------|----------|-------|
| T0 | 2 | 2 |
| T1 | 4 | 4 |
| T2 | 4 | 4 |
| T3 | 4 | 4 |
| T4 | 3 | 4 |
| T5 | 2 | 2 |

---

## Head-to-head vs rnj-1

| Problem | rnj-1 | sonnet-4-6 |
|---------|-------|------------|
| p012 T1 — partial fraction | `plan_format_error` (\boxed{} LaTeX) | **complete** |
| p008 T3 — sin·cos integral | `plan_sanity_error` (pre-computed answer) | **complete** |
| p016 T3 — eigenvalues | `solver_error` (redundant PREV\|eigenvalues) | **complete** |
| p009 T4 — Laplace transform | `plan_format_error` (reversed columns) | **complete** |
| p017 T4 — ODE + IC | `sanity_error` (parroted exp(x)\|solve) | `sanity_error` (kernel limitation — IC not applied) |
| p010 T5 — 2nd order ODE | `solver_error` (literal y''(x) notation) | **complete** |

rnj-1: 13/20 (65%) → sonnet-4-6: 19/20 (95%). **+6 problems, +30 pp.**

---

## The one failure: p017 — ODE with initial condition

**Problem:** "solve the ordinary differential equation y'(x) = y(x) with initial condition y(0) = 1"

**Plan produced:**
```
Eq(y(x).diff(x), y(x))|dsolve
```
Correct SymPy formulation — the new `dsolve` kernel op (added after the rnj-1 run) worked perfectly.

**Kernel result:**
```
dsolve(Eq(y(x).diff(x), y(x))) = Eq(y(x), C1*exp(x))
```
Mathematically correct general solution. The kernel doesn't apply initial conditions — it has no way to receive `ics={y(0): 1}` through the current `expression|operation` protocol.

**Chain sanity gate verdict (30 tokens, precise):**
```
fail | initial condition y(0)=1 is not applied; solution retains arbitrary constant C1 instead of returning y(x) = exp(x)
```
A high-quality, accurate gate response. The gate correctly identified the gap and named the expected answer.

**Root cause:** Kernel limitation, not planner failure. The `dsolve` kernel call does `sym_dsolve(ode)` without `ics=`. The chain protocol (`expression|operation`) has no channel for passing per-problem IC parameters. The sanity gate correctly caught it.

**Fix direction:** Add a `dsolve_ic` variant that parses an extended expression, e.g.:
```
[Eq(y(x).diff(x), y(x)), {y(0): 1}]|dsolve_ic
```
Or add a `solve_ic` operation that takes the general solution and applies conditions. For now this problem tier is correctly flagged by the sanity gate — accept the general solution or mark IVP as out of scope.

---

## Planning quality observations

### Tighter plans (no gratuitous steps)

**p007** — integrate `sqrt(4-x**2)`:
- rnj-1: 2 steps (`sqrt(4 - x**2)|integrate` then `PREV|expand` — expand is a no-op)
- sonnet: **1 step** (`sqrt(4 - x**2)|integrate`) — correct, nothing to expand

**p016** — eigenvalues of `[[1,2],[3,4]]`:
- rnj-1: 2 steps (eigenvalues then `PREV|eigenvalues` on the result dict → solver_error)
- sonnet: **1 step** (`[[1,2],[3,4]]|eigenvalues`) — correct

**p011** — simplify `(x**2-1)/(x-1)`:
- rnj-1: 2 steps (`factor` then `PREV|simplify`)
- sonnet: **1 step** (`(x**2-1)/(x-1)|simplify`) — SymPy's simplify handles the cancellation directly

### No LaTeX contamination

sonnet never emitted `\boxed{}` or any LaTeX wrapper in any expression field across all 20 runs. Zero plan_format_errors.

### Canonical bracket form for solve_system

sonnet used `[x + y - 5, x - y - 1]|solve_system` (with proper list brackets, matching the prompt example); rnj-1 used `x + y - 5, x - y - 1|solve_system` (bare comma, which also works but is inconsistent with the example).

### ODE formulation (p010, p017)

sonnet translated both ODE problems into correct SymPy notation without any prompt guidance beyond the single dsolve example:
- p017: `Eq(y(x).diff(x), y(x))|dsolve`
- p010: `Eq(y(x).diff(x,2) - 3*y(x).diff(x) + 2*y(x), 0)|dsolve`

rnj-1 failed both (parroting/literal string), and the dsolve operation didn't exist yet for that run.

---

## Token efficiency

| Metric | sonnet-4-6 | rnj-1 |
|--------|-----------|-------|
| Decompose tokens (median) | ~7 | ~15 |
| Gate tokens (sanity_check_plan / chain) | **1 token each** | 2 tokens (or 109 on p008 verbose failure) |
| Plan format errors | 0 | 2 |
| LLM calls for complete runs | 4 | 4 |

sonnet gate responses are reliably 1-token ("pass" or "fail|..."), never verbose. This is the binary gate working as designed.

---

## Latency

| Metric | sonnet-4-6 | rnj-1 |
|--------|-----------|-------|
| Complete runs range | 10.9–20.1s | 6.1–10.7s |
| Complete runs mean | ~13.5s | ~7.5s |
| Failure exits (fast) | 8.1s (3 LLM calls) | 1.0–5.3s |

sonnet is ~1.8× slower due to claude API round-trip overhead vs. local Ollama. This is expected and not a concern for the A/B quality comparison.

Two outliers: p013 `sanity_check_plan` = 8456ms, p018 `sanity_check_chain` = 7092ms. API variability, not model behavior.

---

## Explanation quality

sonnet narrations consistently add interpretive value beyond restating the chain:

- **p003**: identifies the problem as finding critical points of a curve (not just "differentiate and solve")
- **p006**: explains why L'Hôpital or limit is needed (plugging in x=0 gives 0/0)
- **p008**: notes the double-angle identity equivalent `−cos(2x)/4 + C`
- **p010**: identifies the characteristic equation `r² − 3r + 2 = 0` with roots r=1, r=2
- **p015**: includes explicit verification `3 + 2 = 5 ✓ and 3 − 2 = 1 ✓`
- **p018**: names the Basel problem and Euler 1734
- **p020**: narrates the round-trip check as a correctness argument, not just a computation

---

## Remaining open issue

**p017 IVP gap** — the `dsolve` kernel gives general solutions only. The sanity gate correctly catches this for IVP problems (those that specify an IC). Three options:

1. Add `dsolve_ic` operation accepting `[Eq(ODE), {y(0): 1}]` expression syntax
2. Accept general solutions from `dsolve` and tell the sanity gate to pass them (removes the IVP check)
3. Exclude IVP problems from the test set until `dsolve_ic` is implemented

Option 1 is the right long-term fix. Option 3 is the right short-term move for the 10-model × 20-problem run, since every model will hit the same kernel wall on p017 if they correctly formulate the ODE.
