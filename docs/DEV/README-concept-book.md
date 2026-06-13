# Concept-Book — Vision, Architecture & Implementation Plan

> Drafted 2026-06-13.  
> Context: SPL stack demo session — linalg concept graph visualized interactively,
> gram-schmidt learning path traced in 11 steps, HTML output validated in Chrome.  
> **Education is the first core application of the SPL stack.**

---

## 1. What Is a Concept-Book?

A **concept-book** is a graph-native learning artifact — a structured body of
knowledge whose curriculum, ordering, and inter-concept dependencies are all
derived from a **concept graph** (a directed acyclic graph of knowledge nodes),
not from a human author's chapter outline.

The term replaces "micro-textbook" across the SPL stack. The distinction is
fundamental, not cosmetic:

| Traditional Textbook | Concept-Book |
|---|---|
| Authored linearly by a human | Derived from a concept graph |
| Chapter order is editorial | Node order is topologically enforced |
| Fixed difficulty level | Personalized: gap(target, learner_state) |
| Static content | Regenerable: change the graph, regenerate |
| Math may be wrong (LLM) | Math is verified (SymPy / Sage / Lean) |
| One domain per book | Graph composition spans multiple domains |

The concept-book pipeline in one line:
```
YAML graph → learning navigator (HTML) → content generator (SPL) → verified lesson
```

---

## 2. Why Education First

Education is the application domain where:
- The verifier ladder matters most (wrong math harms students)
- Personalization has the highest leverage (one size fits nobody)
- The concept-graph structure is most natural (curricula ARE dependency graphs)
- The content is infinitely regenerable (different explanations, same verified math)
- The impact is universal (students everywhere, any language, any level)

SPL's unique combination — deterministic verification (SymPy/Sage/Lean) woven with
probabilistic narrative generation (LLM) — is precisely what education needs and
what no existing ed-tech stack can deliver.

---

## 3. Current State (what is already built)

### 3.1 Concept Graphs (YAML — first-class format)

Located in `cookbook/74_concept_book/`. Each `*_graph.yaml` is a self-contained
domain definition with nodes typed as `primitive | concept | application`, prereq
edges via `composed_of`/`needs`, and optional `verifier`, `lab`, `play` metadata.

Domains currently authored:
- `linalg_graph.yaml` — 37 nodes, 51 edges
- `geometry_graph.yaml`
- `mechanics_graph.yaml`
- `music_theory_graph.yaml`
- `chinese_characters_graph.yaml`
- `english_morphology_graph.yaml`
- `python_science_graph.yaml`
- `sage_learning_graph.yaml`
- `lean_proving_graph.yaml`
- `chemistry_elements_graph.yaml`

### 3.2 Graph Toolkit (`scripts/concept_graph.py`)

Full CLI for concept graphs:

```bash
# Inspect
python concept_graph.py --domain linalg_graph.yaml stats
python concept_graph.py --domain linalg_graph.yaml show eigenpair
python concept_graph.py --domain linalg_graph.yaml path spectral_theorem

# Visualize
python concept_graph.py --domain linalg_graph.yaml visualize --format html
python concept_graph.py --domain linalg_graph.yaml visualize --format mermaid

# Format conversion (YAML is canonical)
python concept_graph.py import linalg_graph.py          # any format → inspect
python concept_graph.py --domain linalg_graph.py convert linalg.yaml  # any → YAML
python concept_graph.py --domain linalg_graph.yaml export sub.yaml -t eigenpair
python concept_graph.py compose -d linalg.yaml -d mechanics.yaml hybrid.yaml

# Learning path
python concept_graph.py --domain linalg_graph.yaml path spectral_theorem \
    --know scalar_multiplication --know vector_addition
```

### 3.3 Interactive HTML Visualizer

`visualize --format html` generates a self-contained vis.js page where:
- Nodes are shaped by kind (◇ primitive, ○ concept, □ application)
- Click any node → learning path highlighted in the graph + listed in side panel
- Zero server required — open directly in any browser

**Validated:** clicking `gram_schmidt` correctly traces 11 prerequisites in
productivity order (topological + reach-weighted).

### 3.4 Content Generator (recipe 74)

`cookbook/74_concept_book/build_concept_book.spl` generates one verified section
per concept node: SymPy/Sage computes the math, LLM writes the narrative.
The `.spl` workflow is domain-agnostic — `@domain_yaml` selects the graph at runtime.

### 3.5 Verifier Ladder

- **SymPy** (recipes 67, 68, 71, 74) — symbolic algebra, exact answers
- **SageMath** (recipe 75) — Galois groups, elliptic curves, manifold geometry
- **Lean** (recipe 77, in progress) — proof-checked statements, mathlib citations

---

## 4. Implementation Plan

### Phase 1 — Branding & Terminology  *(done 2026-06-13)*

**Goal:** replace "micro-textbook" with "concept-book" everywhere for brand consistency.

- [x] Global text replacement in docs, readmes, comments
- [x] Rename `build_micro_textbook.spl` → `build_concept_book.spl` in recipes 71, 73, 74
- [x] Rename recipe directory `71_linalg_micro_textbook` → `71_linalg_concept_book`
- [x] Update transpiler target comment strings (keep `python/domain_textbook` as the
      internal target name for now — alias later)
- [x] Update `cookbook_catalog.json` descriptions

### Phase 2 — HTML-First Output  *(done 2026-06-13)*

**Goal:** the concept-book generator outputs HTML first; PDF and other formats are
derived from the HTML (browser print-to-PDF or headless Chrome).

Current transpiler (`transpiler_domain_textbook.py`) outputs a Jupyter notebook.
New direction:

```
YAML graph
    ↓  build_concept_book.spl (recipe 74)
    ↓  LLM generates section per node
    ↓  SymPy/Sage verifies each claim
    ↓  write_file() accumulates HTML sections
    → concept_book.html  (primary output)
    → concept_book.pdf   (via headless Chrome / weasyprint)
    → concept_book.ipynb (via nbformat, for interactive execution)
```

The HTML output will include:
- Full concept-book content (all sections in topological order)
- Embedded concept graph (vis.js, same as the visualizer)
- Clickable TOC that navigates via the graph
- Each section: definition → verified example → explanation → lab hint

### Phase 3 — 4-Panel Web App UI  *(done 2026-06-13)*

**Goal:** transform the current visualizer into a full learning environment.

Proposed layout (CSS grid):
```
┌──────────────────┬───────────────────────────┬─────────────────┐
│                  │                           │                 │
│  Left Sidebar    │   Concept Graph (vis.js)  │  Notes Sidebar  │
│  Learning Path   │   (primitives at top,     │                 │
│                  │    apps at bottom)        │  [ textarea ]   │
│  1. scalar mult  ├───────────────────────────│                 │
│  2. vector add   │   Explanation Panel       │  Saved notes:   │
│  3. lin combo    │   (selected node detail,  │  · eigenpair    │
│  ...             │    LLM-generated content) │  · gram schmidt │
│  ▶ gram schmidt  │                           │                 │
└──────────────────┴───────────────────────────┴─────────────────┘
```

Components:
- **Left sidebar** — learning path steps (ordered prerequisites), click to navigate
- **Graph panel** — vis.js Network, BFS levels (primitives top, apps bottom),
  click to select and highlight path
- **Explanation panel** — node definition, verified example, LLM explanation,
  lab/play hints, "Generate full lesson" button (calls SPL backend)
- **Notes sidebar** — per-node markdown notes, persisted in localStorage

Graph layout fix needed: compute vis.js `level` via BFS from source nodes
(not from the YAML `tier` attribute, which is often 0 for application nodes).

### Phase 4 — LLM Content in the UI  *(web app milestone)*

**Goal:** clicking "Generate lesson" in the explanation panel fires a real SPL
workflow and streams the result back into the page.

Architecture options:
- **A. Static pre-generation** — run `build_concept_book.spl` ahead of time, embed
  all sections as JSON in the HTML. Zero server required; content is fixed.
- **B. On-demand generation** — a lightweight FastAPI server wraps `spl3 run`;
  the browser calls `/generate?node=eigenpair&domain=linalg`. Content is live.
- **C. Hybrid** — pre-generate on first load, cache in localStorage,
  allow regeneration with different models.

**Recommendation:** start with A (simplest, works offline), add B as an option.

SPL backend call (option B):
```bash
spl3 run cookbook/74_concept_book/build_concept_book.spl \
    --llm claude_cli \
    --param domain_yaml=linalg_graph.yaml \
    --param target_node=eigenpair
```

### Phase 5 — Multi-Domain & Personalized Learning  *(research milestone)*

**Goal:** a learner specifies what they already know; the system generates a
personalized concept-book covering only the gap.

```bash
python concept_graph.py --domain linalg_graph.yaml path spectral_theorem \
    --know linear_combination --know subspace --know basis
# → 6-step personalized path (skips already-known prerequisites)
```

SPL workflow extension:
```
INPUT @learner_state  LIST := []   -- concepts already mastered
INPUT @target         TEXT         -- goal concept
...
CALL gap(@graph, @target, @learner_state) INTO @needed
CALL productivity_order(@needed) INTO @path
WHILE @concept IN @path DO
    -- generate + verify only the concepts in @needed
END
```

Graph composition for cross-domain learning:
```bash
python concept_graph.py compose \
    -d linalg_graph.yaml \
    -d mechanics_graph.yaml \
    hybrid.yaml
python concept_graph.py --domain hybrid.yaml path normal_modes \
    --know linear_combination
```

---

## 5. UI Design Specification

### 5.1 Graph Layout Rules

1. **Primitives at top** — tier 0, diamond shape, green fill
2. **Concepts in middle** — tier 1+, ellipse shape, blue fill
3. **Applications at bottom** — computed via BFS longest-path, rectangle shape, orange fill

The vis.js `level` must be computed from graph topology (BFS longest-path from
sources), not from the YAML `tier` attribute, because application nodes in YAML
often lack explicit tiers and default to 0 (which wrongly places them at the top).

Implementation in JS (to be added to `_to_html`):
```javascript
// Longest-path BFS from sources → correct level for every node
const bfsLevels = (() => {
  const levels = {};
  const successors = {};
  RAW.nodes.forEach(n => { levels[n.id] = -1; successors[n.id] = []; });
  RAW.edges.forEach(e => successors[e.from].push(e.to));
  const sources = RAW.nodes.filter(n =>
    !RAW.edges.some(e => e.to === n.id)
  );
  const queue = sources.map(n => n.id);
  queue.forEach(n => levels[n] = 0);
  let i = 0;
  while (i < queue.length) {
    const cur = queue[i++];
    for (const succ of successors[cur]) {
      const newLev = levels[cur] + 1;
      if (levels[succ] < newLev) { levels[succ] = newLev; queue.push(succ); }
    }
  }
  return levels;
})();
```

### 5.2 Color Language

| Node type   | Fill      | Border    | Shape   | In-path   | Target    |
|-------------|-----------|-----------|---------|-----------|-----------|
| primitive   | `#e8f5e9` | `#2e7d32` | diamond | `#fff9c4` | `#ffe082` |
| concept     | `#e3f2fd` | `#1565c0` | ellipse | `#fff9c4` | `#ffe082` |
| application | `#fff3e0` | `#ef6c00` | box     | `#fff9c4` | `#ffe082` |

### 5.3 Interaction Model

1. **Hover** — show tooltip with `defines` text
2. **Click** — select node: update learning path, explanation panel, notes textarea
3. **Path highlighting** — prerequisites turn yellow, target turns orange, path edges thicken
4. **Path list (left sidebar)** — numbered steps; click step to focus node in graph
5. **Notes (right sidebar)** — auto-save to `localStorage[domain_nodeId]` on input;
   export all notes as JSON for device portability

### 5.4 Explanation Panel Content

When a node is selected, the explanation panel shows:

```
[ concept badge ]  linear_combination  [ tier 1 ]

Definition
  Σ αᵢ ⊙ vᵢ — the atomic operation; almost all of linear algebra
  is a statement about this.

Prerequisites
  • scalar_multiplication  • vector_addition

Verifier: SymPy    Lab: sympy
Play: pick vectors and scalars; check the result is still in V

[ Generate full lesson ]   [ Copy definition ]
```

"Generate full lesson" (Phase 4) fires:
```bash
spl3 run build_concept_book.spl --param target_node=linear_combination
```

---

## 6. Concept Graph Format Reference

YAML is the **first-class format** for concept graphs in the SPL stack.
Reasons: supports inline comments, human-readable diffs, easy to author by hand.

### 6.1 Canonical YAML Structure

```yaml
domain: linalg          # required: domain identifier

primitives:             # irreducible foundation nodes (no prerequisites)
  vector_addition:
    defines: first radical — closed binary operation on V
    tier: 0

concepts:               # derived knowledge nodes
  linear_combination:
    defines: Σ αᵢ ⊙ vᵢ — the atomic operation
    tier: 1
    composed_of:
    - vector_addition
    - scalar_multiplication
    verifier: sympy     # which verifier certifies this concept
    lab: sympy          # interactive lab environment
    play: pick vectors and scalars; check the result is still in V

applications:           # real-world uses of concepts (no tier needed)
  pagerank:
    defines: stationary distribution of a random walk on the web graph
    needs:
    - eigenpair
    domain: networks
```

### 6.2 Format Conversion CLI

```bash
# Any format → YAML (canonical)
python concept_graph.py --domain linalg_graph.py  convert linalg.yaml
python concept_graph.py --domain hybrid.json       convert hybrid.yaml

# Inspect any format
python concept_graph.py import linalg_graph.yaml
python concept_graph.py import linalg_graph.py
python concept_graph.py import linalg.json

# Export subgraph (format inferred from extension)
python concept_graph.py --domain linalg.yaml export eigen.yaml -t eigenpair

# Compose multiple graphs into a hybrid
python concept_graph.py compose -d linalg.yaml -d mechanics.yaml hybrid.yaml
```

---

## 7. Transpiler Direction

Current: `splc --lang python/domain_textbook` → Jupyter notebook (`.ipynb`)

New direction (Phase 2):
- Primary output: `.html` (self-contained, no server needed, embeds vis.js graph)
- Secondary: `.pdf` via `weasyprint` or headless Chrome (`--headless --print-to-pdf`)
- The Jupyter notebook remains as an optional "executable" artifact for lab sessions

The concept-book HTML makes the graph the table of contents — clicking a concept
node navigates directly to its generated section and back.

---

## 8. Open Questions (for review)

1. **Backend for on-demand generation** — FastAPI wrapper around `spl3 run`, or
   purely static pre-generation? Student use case likely needs static (offline,
   no server costs). Teacher/author use case benefits from live regeneration.

   > **Decision (2026-06-13):** Start with static pre-generation (option A — works
   > offline, zero server cost). FastAPI wrapper around `spl3 run` is deferred to
   > the hosted `concept-book` web-app phase.

2. **Multi-language support** — YAML metadata is English; LLM narrative can be
   any language. Should `@language` be an input to `build_concept_book.spl`?

   > **Decision (2026-06-13):** Yes — add `@language TEXT DEFAULT 'en'` to
   > `build_concept_book.spl`. Vision is full multi-lang + multi-modal support.
   > YAML graph metadata stays English (structural); LLM narrative is generated
   > in `@language`. *(Implemented.)*

3. **Difficulty levels** — `style_profiles.py` (elementary/undergraduate/research)
   is already wired into recipes 71/73. Should this be a first-class graph attribute
   (`difficulty: easy|medium|hard` per node) or stay as a workflow parameter?

   > **Decision (2026-06-13):** Workflow parameter (`@style`) — keep it
   > customisable at run time, not baked into the graph. Same content, different
   > register depending on who is running it.

4. **Sharing / publishing** — a concept-book HTML is a single self-contained file.
   Should `concept_graph.py` have a `publish` command that bundles graph + generated
   content into a shareable zip or deploys to GitHub Pages?

   > **Decision (2026-06-13):** Split into two commands:
   > - `share` — informal distribution: bundles graph + HTML into a `.zip` (or
   >   copies to a shareable path). Low ceremony, no vetting required.
   > - `publish` — formal distribution: content has been vetted and is ready for
   >   wide distribution (GitHub Pages, school portal, public website).
   > *(``share`` to be implemented in `concept_graph.py`.)*

5. **Student progress tracking** — notes in localStorage are device-local. A simple
   JSON export/import of notes (no backend needed) would allow device portability.
   Worth adding to the notes sidebar?

   > **Decision (2026-06-13):** Defer full progress tracking to the `concept-book`
   > web-app repo (new repo, not yet created). The SPL.py recipe is the prototype;
   > the web-app will be hostable at a school or public website.
   >
   > Context: `zinets_vis` (`Proj-ZiNets/zinets_vis`) is the precedent — a
   > domain-specific web app for learning Chinese characters. The generalisation is
   > `concept_net` (any knowledge domain); `concept-book` is the content generation
   > engine that powers it. Architecture:
   > ```
   > concept-book (SPL.py recipe)  →  content + graph
   >     ↓
   > concept_net (web app repo)    →  hosted learning portal
   >     ↓
   > Momagrid                      →  distributed inference backend
   > ```

6. **School Momagrid integration** — student grids (zero-cost, private, LAN-based)
   could run the content generation backend locally. A concept-book server that runs
   on a school Raspberry Pi / mini-PC would make this fully offline-capable.

   > **Decision (2026-06-13):** Momagrid is the **inference infrastructure** layer;
   > `concept-book` + `concept-net` are the **application layer** that gives
   > Momagrid its educational use-cases. The school Raspberry Pi / mini-PC running
   > Momagrid + a concept-book server is the target deployment for zero-cost,
   > fully-offline student learning.
---

## 9. Related Files

| Path | Role |
|---|---|
| `scripts/concept_graph.py` | Graph toolkit CLI (import/export/convert/visualize) |
| `cookbook/74_concept_book/` | Domain graphs + concept-book generator workflow |
| `cookbook/74_concept_book/graph_lib.py` | Shared graph algorithms (verify, teaching order) |
| `cookbook/74_concept_book/build_concept_book.spl` | Content generator (to rename Phase 1) |
| `spl3/splc/transpiler_domain_textbook.py` | Jupyter notebook transpiler |
| `docs/DEV/sage_lean_integration_plan.md` | Verifier ladder design |
| `docs/DEV/ROADMAP.md` | Overall SPL roadmap |
