# SPL × SageMath — Kernel Integration (Verifier Ladder, Part A)

> **Status:** **Part A complete** — A-1…A-4 all shipped 2026-06-10 (spike-verified
> live, 738-test suite green). Part B (Lean) is next; see the plan §3.
> Design: [`sage_lean_integration_plan.md`](./sage_lean_integration_plan.md).
> SageMath widens `SOLVE`/`ASSERT` verification *coverage* (SageManifolds, GAP,
> PARI, Singular); Lean (Part B, separate doc to come) raises the *ceiling*.

---

## 1. What shipped (A-1)

Zero parser/AST changes — the kernel spec became configurable, everything else
was inherited:

| Change | Where |
|---|---|
| `IPythonKernel(kernel_name="python3")` parameter; `start()` launches that spec | `spl3/kernel.py` |
| `installed_kernelspecs()` / `kernelspec_installed()` / `ensure_kernelspec()` helpers; `KernelSpecNotFound` error with install instructions | `spl3/kernel.py` |
| `SPL3Executor(kernel_name=...)` pass-through | `spl3/executor.py` |
| `spl3 run --kernel-name NAME` — non-default value implies `--kernel`; kernelspec probed *before* the workflow starts (fail fast, no mid-run stack trace) | `spl3/cli.py` |
| `sage` optional extra (passagemath wheels) | `pyproject.toml` |
| Test suite parameterized over `python3` + `sagemath` (skip-guarded), plus `TestKernelSpec` and `TestSageSpike` | `tests/test_kernel.py` |
| USER-GUIDE §4 — `--kernel-name` option + install + preparser warning | `docs/GUIDE/USER-GUIDE.md` |

---

## 2. Install (the route matters)

```bash
pip install 'spl-llm[sage]'                          # passagemath wheels — no source build
python -m sage.repl.ipython_kernel.install --user    # register the 'sagemath' kernel spec
jupyter kernelspec list                              # verify
```

**Why passagemath and not `sagemath-standard`:** the plain `sagemath-standard`
PyPI package is a source build that compiles the entire Sage toolchain and
routinely fails. The passagemath fork ships real wheels — verified to resolve
`pip install --only-binary :all:` on Python 3.11 (75 wheels, full set: GAP, PARI,
Singular, Maxima, symbolics, plot, repl).

**Why the route matters — the spike's key finding:** the kernelspec that
passagemath registers is

```json
{"argv": ["python3", "-m", "sage.repl.ipython_kernel", ...], "display_name": "passagemath 10.8.4"}
```

i.e. the **same interpreter and site-packages as the SPL env**. The
"environment gap" the plan worried about (Sage's own Python unable to import
`graph_lib`/`linalg_graph`; a different bundled SymPy) closes *by construction*:
under the Sage kernel, the domain libraries, NetworkX, and SymPy are the env's
own. A conda-forge or distro Sage install **would** reintroduce the
separate-interpreter gap — which is why the pip extra is the primary documented
route for SPL use, and conda-forge is the fallback only.

---

## 3. Spike results (2026-06-10)

`pytest tests/test_kernel.py` with Sage installed: **32 passed in ~5 s** (one
skip: the missing-Sage error-message test, correctly unreachable). Kernel
startup is fast — no 5–15 s penalty materialized.

| Probe | Result |
|---|---|
| All 12 parity tests (basic exec, state persistence, SymPy, error handling) under the live Sage kernel | ✅ pass |
| SymPy tests **with the preparser on** | ✅ pass — Sage `Integer`s sympify cleanly (was an open question) |
| `test_preparser_semantics` — `2^3` | ✅ `8` (preparser confirmed active: `^` is power, int literals are Sage `Integer`s, `1/2` is `Rational`) |
| `test_domain_library_runs_under_sage_python` — path-located `linalg_graph` import; `acyclic()`, `reducible()` | ✅ pass |
| `test_sympy_verifier_with_preparser_off` — eigenpair check after `preparser(False)` | ✅ pass |

End-to-end through the CLI — a workflow whose `CALL run_python` executes native
Sage (`factor` and `^` are Sage semantics; zero LLM calls):

```
$ spl3 run sage_smoke.spl --kernel-name sagemath
IPython kernel: enabled (name=sagemath, scope=session, timeout=60.0s)
Status:  complete
Output:  3 * 11 * 31          ← factor(2^10 - 1), 1.2 s
```

If the kernelspec is missing, `spl3 run` fails fast with:

```
Error: Jupyter kernel spec 'sagemath' is not installed. Installed kernels: python3, ...
Install SageMath so its Jupyter kernel is registered — either
  pip install 'spl-llm[sage]'   # passagemath wheels, no source build
  python -m sage.repl.ipython_kernel.install --user
or
  conda install -c conda-forge sage
then verify with: jupyter kernelspec list
```

---

## 4. Decisions settled by the spike

- **D4 (environment-gap strategy): resolved** — none of the mitigation options
  (sys.path injection / install-into-Sage-env / source-over-the-wire) is needed;
  the same-interpreter kernelspec makes the gap vanish. Holds as long as the pip
  extra is the install route.
- **A-1 sizing:** stayed S — no growth from the spike.
- **Preparser policy:** pure-Python verifier code should be wrapped in
  `preparser(False)` … `preparser(True)` for *guaranteed* Python semantics, but
  in practice the existing SymPy verifiers pass even with preparsing on.

---

## 5. Usage

```bash
# Run any workflow's CALL run_python / SOLVE / ASSERT steps under Sage
spl3 run workflow.spl --kernel-name sagemath --adapter ollama
```

```spl
WORKFLOW sage_smoke
    OUTPUT: @answer TEXT
DO
    -- Sage preparser: ^ is exponentiation; factor() is Sage's own
    CALL run_python('print(factor(2^10 - 1))') INTO @answer
    RETURN @answer
END
```

---

## 6. What shipped (A-2)

The compiled notebook now carries its runtime (DODA), and the generic verifier
dispatches on an engine:

| Change | Where |
|---|---|
| `DomainConfig.kernel_name` (default `"python3"`) — run-level kernel selection, one kernelspec per notebook | `spl3/splc/transpiler_domain_graph.py` |
| `_notebook()` emits the kernelspec from `kernel_name` (`sagemath` → SageMath/sage) and records `splc.kernel_name` in notebook provenance metadata | `spl3/splc/transpiler_domain_graph.py` |
| `kernel_name` override parameter on the engine + all three domain transpilers | `transpiler_linalg.py`, `transpiler_intro_geometry.py`, `transpiler_domain_textbook.py` |
| `splc compile --kernel-name NAME` CLI option (domain notebook targets) | `spl3/splc/cli.py` |
| `graph_lib.verify_content(section, domain_data, verifier="")` — engine dispatch matching the per-node `verifier:` YAML attribute; `"sage"` branch; `"sage\|sympy"` prefers Sage, falls back to SymPy; engine-of-record in the return (`pass (sage)`) while the no-arg path stays plain `pass` (backward compatible with `EVALUATE ... WHEN contains("fail")`) | `cookbook/74_domain_textbook/graph_lib.py` |
| 10 tests: kernelspec emission (default / sagemath / unknown-name fallback / cells invariant) + verifier dispatch (default / explicit / unknown / fallback tier / live Sage) | `tests/test_sage_target.py` |

Verified end-to-end:

```
$ spl3 splc compile build_micro_textbook.spl --lang python/domain_textbook --kernel-name sagemath ...
kernelspec: {'display_name': 'SageMath', 'language': 'sage', 'name': 'sagemath'}
splc:       {'target': 'python/domain_textbook', 'domain_library': 'graph_lib.py', 'kernel_name': 'sagemath'}
```

---

## 7. What shipped (A-3)

The engine-of-record now persists beyond the cell output, and kernel downgrade
is loud instead of silent:

| Change | Where |
|---|---|
| `CacheEntry.verifier` — which deterministic engine checked the content (`"sympy"`, `"sage"`, `""` = unverified). Orthogonal to `adapter`/`model` (the *generation* engine) | `spl3/cache/types.py` |
| `verifier TEXT` column + automatic `ALTER TABLE` migration for pre-A-3 cache DBs | `spl3/cache/meta.py` |
| `ContentCache.put(..., verifier=)` → stored and returned on `get()`; visible in `spl3 cache show` and `list --format json` | `spl3/cache/content.py` |
| stdlib `cache_put(..., verifier='sage')` `@spl_tool` — recipes pass the engine from the verify step's `pass (<engine>)` result | `spl/stdlib.py` |
| Notebook-emitted `cache_put` helper gains the same parameter | `spl3/splc/transpiler_domain_graph.py` |
| **Kernel-check banner** appended to the setup cell of any notebook compiled for a non-`python3` kernel: probes the engine at runtime, prints a WARNING when absent (`sage`-only nodes fail fast; `sage\|sympy` nodes fall back to sympy) — never blocks execution | `spl3/splc/transpiler_domain_graph.py` |

The `"sage|sympy"` fallback dispatch itself landed in A-2
(`graph_lib.verify_content`); A-3 made its outcome *durable* — engine-of-record
flows cell output → cache provenance → (future) trust badges in B-4.

---

## 8. What shipped (A-4) — Part A complete

First *real mathematics* in the verifier path — exact recomputation over ℚ, not
presence checks. (Scope note: the plan said "conics, projective duality", but
the intro-geometry domain is school geometry — the upgrade targeted its actual
concepts instead.)

| Change | Where |
|---|---|
| `verify_right_triangle(a,b,c)` — exact a²+b²=c² over ℚ | `cookbook/74_domain_textbook/graph_lib.py` |
| `verify_distance_squared(x1,y1,x2,y2,d²)` — distance formula, d² keeps everything rational | `graph_lib.py` |
| `verify_polygon_area(vertices, claimed)` — exact shoelace; handles `"1/2"`-style rational coords | `graph_lib.py` |
| All three: sage→sympy **absence** fallback with engine-of-record (`pass (sage)`); a wrong claim fails with the first available engine — fallback never masks a verdict | `graph_lib.py` |
| `pythagorean_theorem`, `distance_formula`, `area` nodes → `verifier: sage\|sympy`, `lab:` points at the verifier function | `geometry_graph.yaml` |
| **SageManifolds seed** — `sphere_scalar_curvature(r)`: round S² built with charts + metric, Ricci scalar computed symbolically, equals **2/r² exactly** (`2` at r=1, `1/2` at r=2). Sage-only by nature → the `verifier: "sage"` fail-fast case. Verifier-shaped wrapper included | `cookbook/74_domain_textbook/classical_mechanics_seed.py` |
| 10 tests (exact pass/fail, rational coords, forced-engine, YAML declarations, live curvature) | `tests/test_sage_target.py` |

The seed is the proof that the differential-geometry machinery the future
`mechanics_graph.yaml` needs (charts, metrics, curvature — `configuration_space`,
`lagrangian`, `geodesic`, `normal_modes` nodes) runs in this environment today.

---

## 9. Next

Part A is done. The remaining Sage-track work is *domain authoring*, not
integration: write `mechanics_graph.yaml` (a new domain YAML, zero engine
changes) when the classical-mechanics micro-textbook becomes the focus. Part B
(Lean 4 + mathlib, milestones B-1…B-5) is the next integration phase — see
[`sage_lean_integration_plan.md`](./sage_lean_integration_plan.md) §3.

See the full milestone tables and granularity policy (run-level kernel vs
node-level verifier) in
[`sage_lean_integration_plan.md`](./sage_lean_integration_plan.md) §A.2–A.3.
