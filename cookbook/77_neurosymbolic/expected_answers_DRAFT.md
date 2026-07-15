# Expected Answers — Draft for Review (2026-07-15)

Independently computed with SymPy (`compute_expected.py`, not derived from any LLM or solver-arm output being evaluated). Purpose: wire these into `PROBLEMS` in `run_experiment.py` as a Pattern-2 ground-truth `verify()` target, applied **post-hoc against the already-logged `decomposition` column in `experiment_results.db`** — no re-run of any LLM calls needed.

**Please review each row.** Columns: problem id / tier / statement / SymPy-computed expected answer / review flag.

| id | tier | problem | expected answer (SymPy) | flag |
|----|------|---------|--------------------------|------|
| p001 | T0 | differentiate x⁴ − 2x² + 1 | `4x³ − 4x` | — |
| p011 | T0 | simplify (x²−1)/(x−1) | `x + 1` | — |
| p002 | T1 | expand (x+1)², then factor | expand → `x² + 2x + 1`; factor → `(x+1)²` | two-part answer — verify() must check both intermediate and final |
| p003 | T1 | diff 3x³−x, factor, solve | diff → `9x² − 1`; factor → `(3x−1)(3x+1)`; solve → `x = −1/3, 1/3` | three-part chain |
| p004 | T1 | expand (x−2)³, diff, simplify, factor, solve=0 | expand → `x³−6x²+12x−8`; diff → `3x²−12x+12`; factor → `3(x−2)²`; solve → `x = 2` (double root) | **root multiplicity**: solve returns `[2]` once — confirm whether solver output is expected to report multiplicity 2 or just the root |
| p012 | T1 | partial fractions 1/(x²−1) | `1/(2(x−1)) − 1/(2(x+1))` | form-sensitive — `-1/(2(x+1)) + 1/(2(x-1))` is the same value in a different term order; verify() must compare by symbolic equality, not string match |
| p005 | T2 | differentiate exp(x) | `eˣ` | — |
| p006 | T2 | limit sin(x)/x as x→0 | `1` | — |
| p013 | T2 | Taylor series sin(x) deg 5 at x=0 | `x − x³/6 + x⁵/120` (+ O(x⁶)) | verify() must strip the `O(x⁶)` remainder term before comparing, or compare truncated polynomials only |
| p014 | T2 | simplify sin²(x)+cos²(x) | `1` | — |
| p007 | T3 | integrate √(4−x²) | `(x/2)√(4−x²) + 2·arcsin(x/2)` | **up to an additive constant** — indefinite integral, verify() must check equality of derivatives or allow a free constant, not exact match |
| p008 | T3 | integrate sin(x)cos(x), simplify | `sin²(x)/2` | **up to an additive constant** — the equally valid textbook form `−cos(2x)/4` differs by exactly `1/4`; confirmed by direct check. verify() must NOT use exact string/value equality here |
| p015 | T3 | solve x+y=5, x−y=1 | `x=3, y=2` | — |
| p016 | T3 | eigenvalues of [[1,2],[3,4]] | `(5−√33)/2` and `(5+√33)/2`, each multiplicity 1 | ordering not guaranteed — verify() must compare as a *set* of (value, multiplicity) pairs, not positional |
| p009 | T4 | Laplace transform of e^(−2t) | `1/(s+2)` | — |
| p017 | T4 | solve y'=y, y(0)=1 | `y(x) = eˣ` | — |
| p018 | T4 | Σ 1/n² from n=1 to ∞ | `π²/6` | — |
| p019 | T4 | roots of x⁴−1 | `{−1, 1, −i, i}` | ordering/format not guaranteed — verify() must compare as a set; also confirm whether the experiment expects real-only or all 4 complex roots (problem says "each root," implying all 4) |
| p010 | T5 | general solution y''−3y'+2y=0 | `y(x) = C1·eˣ + C2·e^(2x)` | **up to relabeling of constants** — SymPy nests this as `(C1+C2·eˣ)eˣ`, algebraically identical but not syntactically; verify() must expand/simplify before comparing, and must not require C1/C2 to bind to specific solver-output constant names |
| p020 | T5 | inverse Laplace of s/(s²+4), verify by re-transforming | `cos(2t)·u(t)` (u = unit step / Heaviside); re-Laplace-transforming gives back `s/(s²+4)` ✓ self-check passes | the `u(t)` (Heaviside/causality) factor may or may not appear in the solver's own output — confirm whether the experiment's expected form includes the causality flag or assumes t≥0 implicitly |

## Design note surfaced while drafting this

Several answers (p007, p008, p010, p012, p016, p019) cannot be checked with a naive string/value equality — they need either symbolic-equality-up-to-a-free-constant (indefinite integrals, ODE general solutions) or set-comparison instead of positional comparison (eigenvalues, roots). Appendix I's `verify()` sketch (`simplify(parsed_result - parsed_expected) == 0`) as currently written in the paper only handles the simple case; the real post-hoc script will need per-problem comparison logic, not one generic equality check. Worth a one-line caveat in the paper if this verification layer gets cited.

## Next step

Once you've signed off row-by-row (edit this file directly, or tell me which rows to change), I'll:
1. Wire the reviewed `expected` values into `PROBLEMS` in `run_experiment.py`.
2. Write the post-hoc verification script against `experiment_results.db` (no re-run).
3. Report what fraction of already-"complete" solver-arm rows also pass ground-truth verification.
