# Recipe 74 — Design Document

## The problem with recipes 71 and 73

Recipes 71 (`linalg_concept_book`) and 73 (`intro_geometry`) each shipped a
domain-specific Python module — `linalg_graph.py` / `geometry_graph.py` — as
part of the `splc` target. This created two problems:

1. **Domain code leaked into the SPL.py core codebase.** `transpiler_linalg.py`
   lives in `spl3/splc/` — the framework's own compilation pipeline — but it
   references `linalg_graph.py` by name. Adding a third domain would mean
   adding another file to `spl3/splc/`. The transpiler directory should contain
   general-purpose compilation logic, not per-domain knowledge.

2. **The domain data was hardcoded Python.** The ~30 lines that differ between
   linalg and geometry (`_PRIMITIVES`, `_CONCEPTS`, `_APPLICATIONS` dicts) were
   baked into a `.py` module, making them invisible to non-Python authors and
   impossible to diff across domains without reading code.

Recipes 71 and 73 remain **frozen as-is** — they are working prototypes and
regression oracles. Recipe 74 fixes the design without touching them.

---

## The recipe 74 design

Three layers, each with one responsibility:

```
.spl  (logical — invariant across all domains)
   ↓  param: @domain_yaml
graph_lib.py  (algorithms — domain-agnostic Python; lives in the recipe, not in spl3/)
   ↓  data: {domain}_graph.yaml
{domain}_graph.yaml  (data — human-authorable, no Python required)
```

### Layer 1 — `build_concept_book.spl` (the logical spec)

The `.spl` file is **completely domain-agnostic**. It takes one extra input
compared to recipe 71:

```
@domain_yaml TEXT DEFAULT 'linalg_graph.yaml'
```

That single parameter is the only thing that picks the domain. Every `CALL` and
`GENERATE` statement reads naturally for any domain — math or non-math:

```
CALL setup_domain(@domain_yaml, @target, @payoff_weight) INTO @_
CALL verify_section(@section, @domain_yaml) INTO @check
```

The two-verifier sequence of recipe 71 (`CALL verify_math` + `CALL shape_check`)
collapses to one generic call. A new domain adds a branch inside
`graph_lib.verify_content` — never a new `.spl` construct.

### Layer 2 — `graph_lib.py` (shared algorithm library)

One file, in the recipe directory (not in `spl3/`). It implements the ~15
graph algorithms that were byte-for-byte identical across `linalg_graph.py` and
`geometry_graph.py`, generalized to take `domain_data: dict` explicitly instead
of reading module-level globals:

| Function | What it does |
|---|---|
| `load_domain(yaml_path)` | loads YAML → `domain_data` dict |
| `build(domain_data)` | builds `networkx.DiGraph` from that data |
| `acyclic(graph)` | structural validation |
| `reducible(graph, primitives)` | all leaf nodes are declared primitives |
| `ancestors(graph, target)` | prerequisite closure |
| `productivity_order(graph, weight)` | Kahn's + reach-weighted heap → teaching order |
| `gap(graph, target, learner_state)` | concepts a learner still needs |
| `learning_path(graph, target, ...)` | ordered gap |
| `verify_content(section, domain_data)` | dispatches to the right verifier by `domain_data["domain"]` |
| `verify_character_lego(character, domain_data)` | structural decomposition check (no CAS; works for Chinese characters, Latin morphology, chemistry formulas) |
| `verify_momentum_conservation(...)` etc. | exact ℚ checks via Sage/SymPy for physics/math domains |

`validate_graph_lib.py` proves behavioral identity: 40/40 checks pass —
`graph_lib` + YAML produces the same graph, the same teaching order, the same
ancestor sets as the frozen `linalg_graph.py` module.

### Layer 3 — `{domain}_graph.yaml` (declarative domain data)

The only thing that differs per domain. Human-authorable, diffable YAML:

```yaml
domain: linalg
primitives:
  vector_addition:
    symbol: '⊕: V×V→V'
    defines: first radical — closed binary operation on V
    tier: 0
concepts:
  linear_combination:
    composed_of: [vector_addition, scalar_multiplication]
    defines: Σ αᵢ ⊙ vᵢ — ...
    verifier: sympy
    tier: 1
applications:
  pagerank:
    needs: [eigenpair]
    domain: networks
```

Adding a new domain = write a new YAML file. No Python, no changes to `spl3/`.

---

## How the `splc` target works

Recipe 71's `transpiler_linalg.py` used a **compile-time** `DomainConfig` —
it baked `graph_module="linalg_graph"` into the setup cell at compile time.
That's what required a domain-specific file in `spl3/splc/`.

Recipe 74's `python/domain_textbook` target uses a **runtime-resolved** config.
The setup cell in the compiled notebook does:

```python
domain_data = dg.load_domain(domain_yaml)   # domain_yaml bound from @domain_yaml at runtime
graph = dg.build(domain_data)
primitives = dg.both_radical_primitives(domain_data)
```

`domain_yaml` is just an env var or papermill parameter — the same compiled
notebook runs against any domain. No recompilation needed to switch domains.

Two small, backward-compatible extension points were added to the shared
`DomainGraphTranspiler` engine to support this:

- `DomainConfig.extra_imports` — additional names appended to the `from
  {graph_module} import (...)` block (used to expose `load_domain`,
  `verify_content`).
- `DomainConfig.graph_bootstrap` — when set, replaces the default
  `graph = dg.build(); primitives = dg.{fn}()` lines with custom bootstrap
  code. `python/domain_textbook` uses this to inject the YAML-driven setup.

`LinalgTranspiler` and `IntroGeometryTranspiler` are unaffected (both default
to the old behavior).

---

## Domains available today

| # | YAML file | Capstone | Verifier type |
|---|---|---|---|
| 1 | `linalg_graph.yaml` | `spectral_theorem` | SymPy (CAS) |
| 2 | `geometry_graph.yaml` | `trigonometric_ratios` | Sage/SymPy exact ℚ |
| 3 | `mechanics_graph.yaml` | `normal_modes` | Sage/SymPy exact ℚ |
| 4 | `sage_learning_graph.yaml` | `experimental_mathematics` | structural |
| 5 | `lean_proving_graph.yaml` | `ai_assisted_proving` | structural |
| 6 | `python_science_graph.yaml` | `reproducible_science` | structural |
| 7 | `chinese_characters_graph.yaml` | `phono_semantic_principle` | structural (graph-as-oracle) |
| 8 | `english_morphology_graph.yaml` | `morphological_decoding_principle` | structural (same verifier as #7) |

Adding a 9th domain: write `{domain}_graph.yaml`, run against the existing
compiled notebook, no code changes.

---

## What stays in `spl3/splc/` vs. what lives in the recipe

| Belongs in `spl3/splc/` | Belongs in `cookbook/74_concept_book/` |
|---|---|
| `transpiler_domain_graph.py` — generic SOLVE/ASSERT/CALL/GENERATE → cell mapping | `graph_lib.py` — domain-agnostic graph algorithms |
| `transpiler_domain_textbook.py` — the `python/domain_textbook` preset (thin, 2-line wrapper) | `{domain}_graph.yaml` — per-domain data |
| Generic `DomainConfig` / `DomainGraphTranspiler` engine | `tools.py` — SPL tool registrations that wrap `graph_lib` |
| | `style_profiles.py` — style menu |
| | `validate_graph_lib.py` — regression oracle |

The rule: if it references a domain name or a domain-specific module by string,
it does not belong in `spl3/`.
