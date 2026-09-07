# Recipe-67 rnj-1 run analysis — 20260612

Model: `rnj-1` (ollama) | Workflow: `sympy_llm_v2.spl` | solver=true | 20 problems

---

## Outcome summary

| Status | Count | Problems |
|--------|-------|---------|
| `complete` | 13 | p001, p011, p002, p003, p004, p005, p006, p013, p014, p007, p015, p018, p019, p020 |
| `plan_format_error` | 2 | p012, p009 |
| `plan_sanity_error` | 1 | p008 |
| `solver_error` | 2 | p016, p010 |
| `sanity_error` | 1 | p017 |

**Score: 13/20 (65%)**

By tier:

| Tier | Complete | Total |
|------|----------|-------|
| T0 | 2 | 2 |
| T1 | 3 | 4 |
| T2 | 4 | 4 |
| T3 | 3 | 4 |
| T4 | 2 | 4 |
| T5 | 1 | 2 |

LLM call budget per outcome: complete = 4 calls, plan_sanity_error = 2, plan_format_error = 1 (validate_plan is 0-token). Fast failures are working as designed.

---

## Failure analysis, checkpoint by checkpoint

### Checkpoint 2a — validate_plan (0-token, deterministic): caught 2

**p012** — partial fraction of `1/(x**2-1)`:
```
\boxed{(1/((x + 1)*(x - 1)))|apart}
```
Model wrapped the expression in LaTeX `\boxed{}`. After splitting on `|`, the op field becomes `apart}` (trailing `}`) — not in the allowed list. 1 LLM call, 1453ms. The `\boxed{}` decoration is a recurring rnj-1 signature.

**p009** — Laplace transform of `exp(-2*t)`:
```
laplace|PREV
```
Model reversed the columns — operation name in expression field, `PREV` in operation field. validate_plan catches it: `PREV` is not in the allowed ops list. 1 LLM call, 1044ms.

### Checkpoint 2b — sanity_check_plan (LLM): caught 1 (but for the wrong reason)

**p008** — integral of `sin(x)*cos(x)`, then simplify:
```
\boxed{sin(x)**2/2}|integrate
PREV|simplify
```
Two problems: (a) model **pre-computed** the answer `sin(x)**2/2` and used it as the starting expression instead of the input `sin(x)*cos(x)`, and (b) wrapped with `\boxed{}`.

`validate_plan` **passes** (structurally valid: one `|`, `integrate` is in allowed ops, first line not PREV). The plan sanity gate LLM then **hallucinated** that `sin(x)*cos(x)` was in the plan (it wasn't) and gave a verbose "pass" at 109 tokens / 455 chars instead of the required one-line verdict. `split_part('|', 1)` returns the entire verbose blob; after `lower()` it is not exactly `'pass'` → `IS NOT 'pass'` triggers → `plan_sanity_error`.

The gate caught it by verbosity-as-failure rather than semantic detection. The confusing log line `[ERROR] PLAN SANITY FAILURE — gate verdict: pass` is because the code logged `@plan_verdict_raw` (the full multi-line blob that starts with "pass") rather than `@plan_verdict` (the processed one-word field).

**Fix shipped**: log `@plan_verdict` in `sympy_llm_v2.spl`.

### Checkpoint 3 — kernel: caught 2

**p016** — eigenvalues of `[[1,2],[3,4]]`:
```
[[1, 2], [3, 4]]|eigenvalues
PREV|eigenvalues
```
Model added a redundant second `eigenvalues` step. After step 1 the running expression is a dict `{5/2 - sqrt(33)/2: 1, ...}` — passing a dict to `eigenvalues` fails: "Data type not understood; expecting list of lists". All gates passed (valid protocol; plan looks plausible). Only caught when the kernel fails at step 2.

**p010** — 2nd order ODE `y''(x) - 3*y'(x) + 2*y(x) = 0`:
```
y''(x) - 3*y'(x) + 2*y(x) = 00|solve
```
Model copied the problem statement literally with typo `= 00`, used `solve` (wrong — ODE needs `dsolve`). SymPy throws `SyntaxError: unterminated string literal` because of `y''` apostrophes. This is a **kernel vocabulary gap** — `dsolve` was not in the allowed operation list, so no correct plan was possible.

**Fix shipped**: added `dsolve` operation to kernel and allowed list.

### Checkpoint 4 — chain sanity gate: caught 1

**p017** — first-order ODE `y'(x) = y(x)`, IC `y(0)=1`:
```
exp(x)|solve
```
Model parroted `exp(x)` from the few-shot examples and used `solve` (wrong op). `validate_plan` passes (structurally ok). The **plan sanity gate also passed** — it approved `exp(x)|solve` for an ODE problem. The kernel runs `solve(exp(x) = 0) -> x = []` successfully (empty solution set). Then the **chain sanity gate** correctly fires: `fail | incorrect starting expression`. The chain gate added value the plan gate missed.

Note: same kernel vocabulary gap as p010. Even with correct formulation the result would be approximate without `dsolve`.

**Fix shipped**: added `dsolve` with `Eq(y(x).diff(x), ...)` SymPy notation and prompt example.

---

## Pattern: rnj-1's `\boxed{}` habit

Three of seven failures involved LaTeX `\boxed{}` decoration on what should be a raw SymPy expression (p012, p008, and reverse-column p009 which showed similar output-decoration thinking). The model is trained for formatted math output and bleeds that into the chain protocol.

**Fix shipped**: `validate_plan` now rejects any expression containing a backslash; `decompose_problem` adds a specific INCORRECT example for `\boxed{}`.

---

## Notable successes

- **p020** (T5) — inverse Laplace of `s/(s²+4)`, verify with Laplace forward: `cos(2*t)*Heaviside(t)` → `s/(s**2 + 4)`. Perfect round-trip.
- **p018** (T4) — sum of `1/n²` from 1 to ∞: `pi**2/6`. Correct.
- **p004** (T1) — 5-step chain (expand, diff, simplify, factor, solve): all correct.
- **p015** (T3) — solve_system used comma-separated form `x + y - 5, x - y - 1|solve_system` (no brackets) — SymPy handles both forms.

## Observation: p007 gratuitous `expand` step

p007 integrates `sqrt(4-x**2)` then appends `PREV|expand` — a no-op (expand returns the same expression). Not a failure but rnj-1 reflexively adds a cleanup step even when unneeded.

---

## Fixes applied after this run

| Issue | Fix location |
|-------|-------------|
| Log `@plan_verdict_raw` in plan_sanity_error path (shows "pass" in error) | `sympy_llm_v2.spl` |
| `validate_plan` passes LaTeX `\boxed{}` when trailing `}` is not in op field | `sympy_tools.spl` validate_plan |
| `dsolve` missing from kernel and allowed list (ODE vocab gap) | `sympy_tools.spl` kernel + validate_plan |
| No ODE example in `decompose_problem` prompt | `sympy_tools.spl` decompose_problem |
| No `\boxed{}` INCORRECT example in `decompose_problem` prompt | `sympy_tools.spl` decompose_problem |

Excluding the 2 ODE problems (p010, p017) that were unsolvable before the dsolve fix: **13/18 (72%)**.
