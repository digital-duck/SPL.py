# Recipe 74 — Generic Domain Micro-Textbook (`graph_lib` + `@domain_yaml`)

**Pattern:** ONE `.spl` workflow + ONE shared algorithm library (`graph_lib.py`)
+ declarative per-domain data (`{domain}_graph.yaml`) + a **runtime-resolved**
`splc` target (`python/domain_textbook`) that decides *which* domain to teach
from a `@domain_yaml` workflow input — compiled once, runs against either
linear algebra or intro geometry (or any future domain shaped the same way).

> **Status: implemented and validated end-to-end.** `graph_lib.py` is
> regression-tested against recipe 71's frozen `linalg_graph.py` (40/40 checks
> — see `validate_graph_lib.py`); `transpiler_domain_textbook.py` /
> `python/domain_textbook` compile `build_micro_textbook.spl` to a running
> notebook; the deterministic half of the pipeline (graph load → validate →
> teaching-order) has been executed against **both** `linalg_graph.yaml` and
> `geometry_graph.yaml` from the *same compiled artifact*.

## Why this recipe exists

Recipes 71 (`python/linalg`) and 73 (`python/intro_geometry`) each ship a
**frozen, domain-specific copy** of the same ~600-line concept-graph module —
`linalg_graph.py` / `geometry_graph.py` — differing only in:

1. ~30 lines of declarative *data* (`_PRIMITIVES`/`_CONCEPTS`/`_APPLICATIONS`
   dicts), and
2. which SymPy submodule their symbolic verifier(s) recompute against.

Everything else — the graph builder, all ~15 graph algorithms
(`acyclic`, `reducible`, `ancestors`, `productivity_order`, `gap`,
`learning_path`, …) — is **byte-for-byte identical** between the two modules.
That's the generalization opportunity this recipe proves out, **without**
touching either frozen module (per explicit instruction — `linalg_graph.py` is
"fully vested" and remains recipe 71's untouched regression oracle).

## The split

| | Recipe 71 / 73 (frozen) | Recipe 74 (this one) |
|---|---|---|
| Domain *data* | hardcoded `_PRIMITIVES`/`_CONCEPTS`/`_APPLICATIONS` dicts in `{domain}_graph.py` | declarative `{domain}_graph.yaml` — human-authorable, diffable, lossless twin (see `generate_domain_yaml.py`) |
| Graph *algorithms* | copied verbatim into each `{domain}_graph.py` | **one** shared `graph_lib.py`, generalized to take `domain_data: dict` explicitly instead of reading module globals |
| Symbolic verifier | `verify_math`+`shape_check` (linalg) **or** `verify_geometry` (geometry) — different `.spl` `CALL` targets per domain | **one** `graph_lib.verify_content(section, domain_data)`, dispatching on `domain_data["domain"]` internally — same `.spl` `CALL` for either domain |
| `splc` target | `python/linalg` / `python/intro_geometry` — `DomainConfig` is a **compile-time preset** (graph module name baked in) | `python/domain_textbook` — `DomainConfig` is **runtime-resolved**: the setup cell loads `@domain_yaml` via `graph_lib.load_domain()` when the notebook *runs*, not when it's compiled |

## `graph_lib.py` — shared, YAML-driven algorithm library

Of `linalg_graph.py`'s ~15 algorithm functions, exactly **3**
(`build`, `minimal`, `new_primitives`) referenced the module-level
`_PRIMITIVES`/`_CONCEPTS`/`_APPLICATIONS` globals; the other ~11
(`acyclic`, `reducible`, `in_graph`, `ancestors`, `restrict`,
`applications_of`, `productivity_order`, `gap`, `learning_path`, …) are
**pure functions** over a built `networkx.DiGraph` and copy verbatim with zero
changes. `graph_lib.py` generalizes the 3 stateful ones to take an explicit
`domain_data: dict` (loaded from YAML via `load_domain()`), and adds
`first_radical_primitives`/`both_radical_primitives`/`concept_names`/
`primitive_names` as `domain_data`-driven accessors plus the generic
`verify_content` dispatcher. See the module docstring for the full public API.

## `{domain}_graph.yaml` — lossless declarative twins

`generate_domain_yaml.py` is a one-shot generator: it imports the **frozen**
`linalg_graph`/`geometry_graph` modules and dumps their
`_PRIMITIVES`/`_CONCEPTS`/`_APPLICATIONS` dicts (plus the curated
`first_radical_primitives()` subset — genuine pedagogical *content*, not a
derived quantity) straight to YAML with `sort_keys=False` (preserves
declaration order — `concept_names()` depends on it) and `allow_unicode=True`
(preserves `⊕`/`⊙`/`⟨·,·⟩` without `\uXXXX` escaping). The result:
`linalg_graph.yaml` (267 lines, 5 primitives / 25 concepts / 7 applications)
and `geometry_graph.yaml` (238 lines, 5 / 19 / 5) — human-readable, diffable,
authorable without touching Python.

## `validate_graph_lib.py` — the regression oracle

The proof obligation: *"use the existing recipe #71 to validate our generic
approach"*. For each domain, `validate_graph_lib.py` runs ~20 comparisons —
graph structure (nodes+edges+attrs), `acyclic`, every primitives/concepts
accessor, `reducible`, `minimal`, `ancestors`, `applications_of`, `in_graph`,
`productivity_order` at three payoff weights, `gap`, `learning_path`,
`new_primitives` — between the **YAML-driven path** (`graph_lib.load_domain`
+ `graph_lib.build` + `graph_lib.*`) and the **frozen module's hardcoded
path** (`linalg_graph.build()` + `linalg_graph.*`). Result:

```
ALL CHECKS PASSED — graph_lib.py + {domain}_graph.yaml ≡ frozen domain modules
```

**40/40 checks pass** — the generalization is behaviorally identical, not just
similar, for both linalg and intro_geometry.

## `build_micro_textbook.spl` — one source, either domain

Structurally identical to recipe 71's validated workflow (timing
instrumentation, style resolution, graph validation, teaching-order
computation, content cache, capstone payoff, `COMMIT`) with exactly two
domain-generalizing changes:

1. A new `@domain_yaml TEXT DEFAULT 'linalg_graph.yaml'` workflow `INPUT` —
   the only thing that picks which domain gets taught.
2. The two-verifier sequence (`CALL verify_math` → `CALL shape_check`, recipe
   71) collapses to **one** generic call:

   ```
   CALL verify_content(@section, @domain_data) INTO @check
   EVALUATE @check
       WHEN contains("fail") THEN GENERATE refine_section(@section, @check, @style_guide) INTO @section
       ELSE LOGGING "Content verified" LEVEL INFO
   END
   ```

   `graph_lib.verify_content` dispatches on `domain_data["domain"]`
   internally (checking `sympy.geometry` vs. plain `sympy` presence today —
   both 71 and 73 still carry `# TODO: parse claims and recompute` stubs for
   the actual symbolic recompute, so this dispatcher generalizes the *shape*
   they already have, not a deeper oracle than they do). A third domain adds
   a branch inside `verify_content`, never a new `.spl` construct.

`spl3 validate` reports the same warning shape as recipe 71's already-running
source (12 vs. 13 — one fewer, from collapsing two `CALL`s into one) — spec-clean.

## `python/domain_textbook` — the runtime-resolved `splc` target

`transpiler_linalg.py`/`transpiler_intro_geometry.py` each wrap a **fixed**
`DomainConfig` (`graph_module="linalg_graph"` / `"geometry_graph"`, baked in at
*compile* time — the setup cell hardcodes `import linalg_graph as dg`).
`python/domain_textbook` can't do that: which domain to load is a *runtime*
decision (`@domain_yaml`). Two small, additive extension points were added to
the shared `DomainGraphTranspiler` engine (`transpiler_domain_graph.py`) —
fully backward-compatible; `LinalgTranspiler`/`IntroGeometryTranspiler`
default to the old behavior unchanged:

- `DomainConfig.extra_imports: tuple[str, ...]` — names appended to the
  `from {graph_module} import (...)` block. `graph_lib` uniquely exports
  `load_domain`/`verify_content` (neither frozen module does), so
  `DOMAIN_TEXTBOOK_CONFIG` adds them here.
- `DomainConfig.graph_bootstrap: tuple[str, ...] | None` — when set, REPLACES
  the engine's default `graph = dg.build(); primitives = dg.{fn}()` lines
  wholesale. `python/domain_textbook` plugs in:

  ```python
  domain_data = dg.load_domain(domain_yaml)   # domain_yaml already bound from @domain_yaml INPUT
  graph = dg.build(domain_data)
  primitives = dg.both_radical_primitives(domain_data)
  ```

  making `@domain_data` available to the `.spl` body (e.g.
  `CALL verify_content(@section, @domain_data)`) the same way `@graph`/
  `@primitives` already are.

`DomainTextbookTranspiler` itself is the same two-line preset shape as its
siblings — `__init__` just passes `DOMAIN_TEXTBOOK_CONFIG`. No cell-emitter
method needed overriding; every SPL → cell construct mapping
(`SOLVE`/`ASSERT`/`CALL`/`EVALUATE`/`WHILE`/`GENERATE`/`COMMIT`/...) is
inherited unchanged from `DomainGraphTranspiler`.

## End-to-end validation

The compiled notebook (`build_micro_textbook_python_domain_textbook.ipynb`)
was executed cell-by-cell (setup through teaching-order computation — the
deterministic half, before LLM-driven `GENERATE`) under both domains, **from
the same compiled artifact**, by setting `DOMAIN_YAML`:

```
DOMAIN_YAML=linalg_graph.yaml    TARGET=spectral_theorem
  → domain='linalg'         37 nodes / 51 edges, 13-concept teaching order, ASSERTs pass
DOMAIN_YAML=geometry_graph.yaml  TARGET=trigonometric_ratios
  → domain='intro_geometry' 29 nodes / 50 edges, 15-concept teaching order, ASSERTs pass
```

`verify_content("sample text", domain_data)` returns `'pass'` for both —
correctly dispatching to `sympy.geometry` vs. plain `sympy` per
`domain_data["domain"]`.

## Run it

```bash
# Compile (already checked in under targets/, but to regenerate):
splc compile cookbook/74_domain_textbook/build_micro_textbook.spl --lang python/domain_textbook

# Run against either domain — only the env var changes:
DOMAIN_YAML=linalg_graph.yaml \
  jupyter nbconvert --to notebook --execute build_micro_textbook_python_domain_textbook.ipynb

DOMAIN_YAML=geometry_graph.yaml TARGET=trigonometric_ratios \
  jupyter nbconvert --to notebook --execute build_micro_textbook_python_domain_textbook.ipynb
```

## Files

| File | Role |
|---|---|
| `graph_lib.py` | shared, YAML-driven graph builder + ~15 algorithms + generic `verify_content` |
| `linalg_graph.yaml` / `geometry_graph.yaml` | lossless declarative domain-data twins |
| `generate_domain_yaml.py` | one-shot generator: frozen `{domain}_graph.py` → `{domain}_graph.yaml` |
| `validate_graph_lib.py` | regression oracle: `graph_lib` + YAML ≡ frozen modules (40/40 checks) |
| `build_micro_textbook.spl` | the one `.spl` source — `@domain_yaml`-parameterized |
| `style_profiles.py` | shared style menu (superset copy — see its docstring) |
| `targets/python_domain_textbook/` | compiled notebook + readme + manifest |

## Relationship to recipes 71 / 73

**Nothing in `cookbook/71_linalg_micro_textbook/` or
`cookbook/73_intro_geometry/` was modified.** `linalg_graph.py` remains
"fully vested" and frozen — it is now *also* this recipe's regression oracle.
Recipe 74 doesn't replace 71/73; it's the proof that their shared shape can
collapse into one generic engine, with 71's already-validated behavior as the
ground truth that certifies the collapse is faithful.
