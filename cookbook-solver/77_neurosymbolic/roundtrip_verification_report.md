# Round-Trip Verification Report — Solver Arm (T0–T5 Math Problems)

**Script**: `verify_roundtrip.py` | **Run date**: 2026-07-16 | **Input**: `experiment_results.db` (no LLM re-run) | **Output**: `roundtrip_verification_results.csv`

## Method

For each of the 20 T0–T5 problems, the solver arm's already-logged `decomposition` trace (backend `sympy`/`sage`, `solver='true'`) is checked by **substituting the final result back into the original problem's defining relation** and confirming it holds — the "check your work" method (Wen, 2026-07-16), not a comparison against a precomputed canonical answer. E.g.: a `solve` result is plugged back into the equation and checked to equal zero; an `integrate` result is differentiated and checked against the original integrand; an ODE's general solution is substituted into the ODE and checked to satisfy it identically (and, for `p010`, checked to retain both independent constants a *general* 2nd-order solution requires — a particular solution like bare `exp(x)` satisfies the ODE but is not the general solution asked for). All checks are performed by SymPy itself — deterministic, no LLM involved in the check.

Three possible outcomes per completed run:
- **ROUNDTRIP_PASS** — result satisfies the defining relation
- **ROUNDTRIP_FAIL** — result does not (wrong answer, or the wrong operation entirely, e.g. Laplace-transforming twice)
- **UNPARSEABLE** — the logged final step could not be parsed into a symbolic expression at all (a logging/formatting artifact, not a correctness judgment — e.g. `p015`'s system-solve trace is truncated mid-render for many runs; recovered via a fallback regex over the workflow's natural-language `output` where possible)

Rows where Pattern 1 (kernel execution status) had already failed are excluded (`NOT_EXECUTED`) — there is no final result to check.

## Headline Result

Of the **1,749** solver-arm rows (20 problems × sympy/sage backends) that Pattern 1 already scored as `pass`:

| Outcome | Count | % of Pattern-1 pass |
|---|---|---|
| Round-trip verified (ROUNDTRIP_PASS) | 1,510 | 86.3% |
| **Round-trip FAILS despite Pattern-1 pass** | **171** | **9.8%** |
| Unparseable (excluded) | 68 | 3.9% |

**~1 in 10 solver-arm runs that Pattern 1 counts as "passed" does not actually satisfy the problem it was asked to solve.** Concrete examples pulled from the data: a Laplace-transform problem (`p009`) where the model transformed its own already-correct answer a second time (`1/((s+2)*s)` instead of `1/(s+2)`); a first-derivative problem (`p001`) where the model kept differentiating past the requested order (`24*x`, the 3rd derivative, instead of `4x³-4x`); an ODE general-solution problem (`p010`) where the returned function solved the ODE but was missing one of its two required independent constants.

## Per-Problem and Per-Model Breakdown

See `verify_roundtrip.py` output / `roundtrip_verification_results.csv` for full per-row detail. Round-trip-verified rate ranges from 56.9% (deepseek-v2:16b) to 96.6% (lfm2.5) across models, and from 0% (`p017`, ODE + initial condition — many runs applied the wrong operation, e.g. Laplace transform instead of `dsolve`) to 100% (`p005`, a trivial derivative) across problems. The lowest-verified problems (`p009`, `p010`, `p017`, `p020`) are exactly the ones with a genuine alternate operation to confuse with the intended one (transform vs. inverse-transform, particular vs. general ODE solution) — a plausible, checkable failure mode rather than noise.

## Known Limitations

- `p015` (2-equation linear system): the kernel decomposition trace is truncated for a meaningful fraction of runs (a pre-existing logging artifact, not introduced by this script); recovered via a regex fallback over the free-text `output` field where the trace itself is unusable.
- `p017`: initial-condition resolution (`y(0)=1`) is sometimes performed by the LLM's own algebra outside any logged kernel call, so it is not independently checkable from the decomposition trace alone; this check validates that the returned function satisfies the ODE itself, not that the constant was correctly resolved from the initial condition.
- The `UNPARSEABLE` bucket includes both genuine logging truncations and cases where a run pursued a visibly wrong operation in a format the parser doesn't recognize as any valid answer form (e.g. `p010` runs that solved a characteristic equation and returned `x = [1, 2]` instead of a function of `x`) — these are excluded from the denominator rather than asserted as fails, to avoid overclaiming precision the automated parser doesn't actually have.
