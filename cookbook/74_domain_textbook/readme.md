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

## The micro-textbooks — seven domains, one compiled artifact

Every `{domain}_graph.yaml` below runs through the **same** checked-in
notebook (`targets/python_domain_textbook/build_micro_textbook_python_domain_textbook.ipynb`);
only the env vars change. The two-step review pipeline, run from
`targets/python_domain_textbook/`:

```bash
# 1. execute against the chosen domain
DOMAIN_YAML={domain}_graph.yaml TARGET={capstone} \
  jupyter nbconvert --to notebook --execute \
  build_micro_textbook_python_domain_textbook.ipynb --output {domain}_textbook.ipynb

# 2. render the review PDF (Chromium-based — renders ⊕ / ⟨·,·⟩ / 汉字 with no LaTeX setup)
jupyter nbconvert --to webpdf --allow-chromium-download {domain}_textbook.ipynb
```

(`--to pdf` via LaTeX also works where `xelatex` is installed; the
Chinese-characters book additionally needs the `xeCJK` package there —
`webpdf` needs neither. Note step 1 is a FULL run — graph validation and
teaching order are deterministic, but section drafting goes through the
LLM-driven `GENERATE` cells, so the configured model backend must be up.)

### 1. Linear Algebra — `linalg_graph.yaml`

The original domain (recipe 71's content, losslessly YAML-ized) and the
regression oracle for everything else here. 5 primitives / 25 concepts /
7 applications — 37 nodes, 51 edges. Capstone: `spectral_theorem`.

```bash
DOMAIN_YAML=linalg_graph.yaml TARGET=spectral_theorem \
  jupyter nbconvert --to notebook --execute \
  build_micro_textbook_python_domain_textbook.ipynb --output linalg_textbook.ipynb
jupyter nbconvert --to webpdf linalg_textbook.ipynb        # → linalg_textbook.pdf
```

### 2. Intro Geometry — `geometry_graph.yaml`

Recipe 73's content, upgraded to the exact-verifier ladder: Pythagorean,
distance-formula, and shoelace-area worked examples recomputed over ℚ
(`sage|sympy` — Sage preferred, SymPy fallback). 5 / 19 / 5 — 29 nodes,
50 edges. Capstone: `trigonometric_ratios`.

```bash
DOMAIN_YAML=geometry_graph.yaml TARGET=trigonometric_ratios \
  jupyter nbconvert --to notebook --execute \
  build_micro_textbook_python_domain_textbook.ipynb --output geometry_textbook.ipynb
jupyter nbconvert --to webpdf geometry_textbook.ipynb      # → geometry_textbook.pdf
```

### 3. Classical Mechanics — `mechanics_graph.yaml`

First domain authored *after* the verifier ladder shipped — exact ℚ momentum
and energy ledgers, a symbolic SHO check (x″ + ω²x ≡ 0), and a Sage-only
manifolds node (`configuration_space` → `classical_mechanics_seed.py`). The
graph encodes a physics fact: dynamics is not reducible from kinematics
alone. 4 / 19 / 5 — 28 nodes, 49 edges. Capstone: `normal_modes`.
Tests: `tests/test_mechanics_domain.py`.

```bash
DOMAIN_YAML=mechanics_graph.yaml TARGET=normal_modes \
  jupyter nbconvert --to notebook --execute \
  build_micro_textbook_python_domain_textbook.ipynb --output mechanics_textbook.ipynb
jupyter nbconvert --to webpdf mechanics_textbook.ipynb     # → mechanics_textbook.pdf
```

### 4. *Doing Math in SageMath Lab* — `sage_learning_graph.yaml` (trilogy Book I)

Free e-book, publisher Digital Duck: mathematics as an experimental science,
on a CAS anyone can install for $0. 4 / 18 / 5 — 27 nodes, 43 edges.
Capstone: `experimental_mathematics`. Tests: `tests/test_tool_domains.py`.

```bash
DOMAIN_YAML=sage_learning_graph.yaml TARGET=experimental_mathematics \
  jupyter nbconvert --to notebook --execute \
  build_micro_textbook_python_domain_textbook.ipynb --output sage_learning_textbook.ipynb
jupyter nbconvert --to webpdf sage_learning_textbook.ipynb # → sage_learning_textbook.pdf
```

### 5. *Proving Math the Lean Way* — `lean_proving_graph.yaml` (trilogy Book II)

Free e-book: Lean 4 + mathlib, the proof assistant Terence Tao champions for
doing mathematics with AI. 4 / 19 / 5 — 28 nodes, 45 edges. Capstone:
`ai_assisted_proving`. Tests: `tests/test_tool_domains.py`.

```bash
DOMAIN_YAML=lean_proving_graph.yaml TARGET=ai_assisted_proving \
  jupyter nbconvert --to notebook --execute \
  build_micro_textbook_python_domain_textbook.ipynb --output lean_proving_textbook.ipynb
jupyter nbconvert --to webpdf lean_proving_textbook.ipynb  # → lean_proving_textbook.pdf
```

### 6. *Doing Science with Python* — `python_science_graph.yaml` (trilogy Book III)

Free e-book: the scientific Python stack — NumPy, SymPy, SciPy, pandas,
scikit-learn, matplotlib — ending at the reproducible scientific pipeline.
(Book I finds it, Book II proves it, Book III measures it.) 4 / 19 / 5 —
28 nodes, 43 edges. Capstone: `reproducible_science`.
Tests: `tests/test_tool_domains.py`.

```bash
DOMAIN_YAML=python_science_graph.yaml TARGET=reproducible_science \
  jupyter nbconvert --to notebook --execute \
  build_micro_textbook_python_domain_textbook.ipynb --output python_science_textbook.ipynb
jupyter nbconvert --to webpdf python_science_textbook.ipynb # → python_science_textbook.pdf
```

### 7. *Learning Chinese Characters the LEGO Way* — `chinese_characters_graph.yaml`

The first non-mathematical domain, companion to the ZiNets portal
(digital-duck/zinets_vis). Its oracle is the graph itself
(`verifier: structural` → `graph_lib.verify_character_lego`), and its
load-bearing structural fact mirrors mechanics' kinematics/dynamics split:
the graph is NOT reducible from the 11 semantic pictograms (first radical,
FORM) alone — the sound-lender 马 (second radical, SOUND) is irreducible
content, which is the 形声 phono-semantic thesis machine-checked.
12 / 16 / 5 — 33 nodes, 42 edges. Capstone: `phono_semantic_principle`.
Tests: `tests/test_chinese_characters_domain.py`.

```bash
DOMAIN_YAML=chinese_characters_graph.yaml TARGET=phono_semantic_principle \
  jupyter nbconvert --to notebook --execute \
  build_micro_textbook_python_domain_textbook.ipynb --output chinese_characters_textbook.ipynb
jupyter nbconvert --to webpdf chinese_characters_textbook.ipynb # → chinese_characters_textbook.pdf
```

## Candidate domains — what the LEGO schema teaches next

The chinese_characters pilot proved the schema works for *structural*
(non-CAS) domains, and `verify_character_lego` is already domain-agnostic —
it only reads `composed_of` / `pieces` / declared primitives, never anything
Chinese-specific. Each candidate below is therefore **pure data-authoring**:
a new `{domain}_graph.yaml`, zero new code (at most one exact-verifier
function where the domain offers a numeric oracle). The authoring discipline,
in parity with the radical-based pilot:

- **primitives** — a curated brick set, small enough to actually learn;
- **a two-radical split** that encodes a real irreducibility fact
  (`reducible(first_radical) == False` must be a *theorem of the domain*,
  not an artifact of the slice);
- **`pieces`** — the brick multiset of each composite (multiplicity lives
  here, since graph edges cannot repeat — 林's two 木);
- **a capstone principle** with the "learn ~N bricks + 1 principle, decode
  thousands" payoff shape.

### Latin & Greek morphology — `english_morphology_graph.yaml`

The closest sibling of the Chinese pilot — English academic vocabulary IS a
phono-semantic-style composition system, it just hides it better.

- **Primitives:** a comprehensive brick inventory in three families —
  prefixes (`re-`, `pre-`, `sub-`, `trans-`, `ex-`, `in-`, …), roots
  (`spect`, `port`, `dict`, `struct`, `mit/miss`, `duc/duct`, `graph`,
  `bio`, …), suffixes (`-ion`, `-or`, `-able`, `-ology`, …). Realistic
  production scale: ~50 + ~120 + ~50 bricks.
- **Two-radical split:** roots are FORM (the semantic core — first radical);
  affixes are the OPERATORS (second radical). The irreducibility theorem:
  no pile of roots ever yields *inspection* — `in- + spect + -ion` needs
  the affix system, exactly as 妈 needs 马.
- **`pieces` multiset:** `reconstruction` = `[re-, con-, struct, -ion]`;
  double-prefix words play the role 森's tripling plays in the pilot.
- **Bonus parallel:** allomorphy (`in-` → `im-`/`il-`/`ir-` before labials/
  liquids) is the 水→氵 variant-form story, one-for-one.
- **Capstone:** `morphological_decoding_principle` — ~220 bricks + 1
  principle decode tens of thousands of academic, scientific, legal, and
  medical words. The equity stake is identical to the Chinese pilot's:
  morphological awareness is the single best-documented lever on the
  academic-vocabulary gap, and it is rarely taught explicitly.
- **Verifier:** `structural` — `verify_character_lego` works unchanged.

### Periodic table — `chemistry_elements_graph.yaml`

Chemistry is the domain where the schema's `pieces` convention stops being a
metaphor: **a chemical formula IS a pieces multiset.** H₂O is literally
`pieces: [H, H, O]` — the same multiplicity-in-pieces rule as 林's two 木,
written by nature.

- **Primitives:** a curated element brick set (H, C, N, O, Na, Mg, Cl, Ca,
  Fe, …, ~20 elements) plus the structural primitives that organize them —
  `proton_count` (what *makes* an element) and `valence_electron` (what makes
  it *bond*).
- **Two-radical split:** elements alone are FORM; the valence/octet rule is
  the second radical. The irreducibility theorem: no list of elements
  predicts that Na + Cl → NaCl but Ne bonds with nothing — bonding behavior
  is genuinely new content, not derivable from element identity, just as
  sound-lending is not derivable from pictograms.
- **Concepts:** ions and compounds (`H2O`, `CO2`, `NaCl`, `CH4`, `H2SO4`),
  then the principle nodes: `ionic_bonding`, `covalent_bonding`, and the
  periodic law itself — the periodic table as *the LEGO sorting of the brick
  set*.
- **Capstone:** `stoichiometry` — and here the verifier ladder climbs past
  `structural`: formula composition is graph-checked, while molar-mass and
  equation-balancing worked examples get **exact ℚ recomputation**
  (`verify_balanced_equation` — conservation of each element's count across
  an equation is integer linear algebra, the same `sage|sympy` shape as
  `verify_momentum_conservation`). Chemistry is the first candidate that
  exercises *both* rungs in one domain.
- **Payoff shape:** ~20 bricks + 2 bonding rules decode the formulas on
  every label, every equation in a first chemistry course.

### Further afield (same shape, unclaimed)

Music theory (12 pitch-class bricks → intervals → chords → progressions;
structural + exact integer arithmetic mod 12) and molecular genetics
(4 nucleotide bricks → 64 codons → the genetic-code table as capstone) both
fit the schema with no code changes — noted here so the pattern's reach is
on record.

## Files

| File | Role |
|---|---|
| `graph_lib.py` | shared, YAML-driven graph builder + ~15 algorithms + generic `verify_content` + exact ℚ/symbolic verifiers + structural `verify_character_lego` |
| `linalg_graph.yaml` / `geometry_graph.yaml` | lossless declarative domain-data twins of recipes 71/73 |
| `mechanics_graph.yaml` | classical mechanics (exact Sage/SymPy verifiers; Sage-only manifolds node) |
| `sage_learning_graph.yaml` / `lean_proving_graph.yaml` / `python_science_graph.yaml` | the Digital Duck e-book trilogy (Books I–III) |
| `chinese_characters_graph.yaml` | ZiNets companion — structural (graph-as-oracle) domain |
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
