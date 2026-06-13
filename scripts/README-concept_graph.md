# concept_graph.py — generic concept-graph CLI

A standalone command-line tool that inspects, visualizes, shares, and
composes *any* concept graph produced for the concept-book framework
(see [cookbook recipe 71](../cookbook/71_linalg_concept_book/readme.md)) —
without the domain graph's module needing to import or know about this tool.

## The contract

Any "domain module" — a plain importable Python module or `.py` file — works
with this CLI as long as it exposes:

```python
build() -> networkx.DiGraph
```

whose nodes carry at least `kind` (`"primitive" | "concept" | "application"`),
`tier`, `defines`, and `composed_of`, and whose edges `u → v` mean "u is a
prerequisite of v". `cookbook/71_linalg_concept_book/linalg_graph.py` and
`cookbook/73_intro_geometry/geometry_graph.py` are worked examples.

Domain modules stay **fully self-contained** by design — each owns its own
copy of the graph algorithms (`ancestors`, `reducible`, `productivity_order`,
…) so that two domains' notions of e.g. "ancestors" can never silently
diverge (see `cookbook/70_linalg_core_concepts/readme.md` for the rationale).
`concept_graph.py` is the deliberate exception: a pure *reporting and
sharing* layer every domain gets "mixed in" for free, purely by exposing
`build()` — no import, no coupling, no per-domain CLI to write or maintain.

## Pointing at a domain

`--domain` (or `-d`) accepts any of:

| Form | Example |
|---|---|
| Importable module name (resolved on `sys.path` / cwd) | `--domain linalg_graph` |
| Path to a `.py` file | `--domain ../cookbook/73_intro_geometry/geometry_graph.py` |
| Path to a `.json` graph from `export`/`compose` | `--domain hybrid.json` |

## Commands

```bash
# Inspect
python concept_graph.py --domain linalg_graph stats
python concept_graph.py --domain linalg_graph list --kind concept
python concept_graph.py --domain linalg_graph show spectral_theorem
python concept_graph.py --domain linalg_graph ancestors gram_schmidt

# Curriculum ordering
python concept_graph.py --domain linalg_graph order --weight 2.0
python concept_graph.py --domain linalg_graph path spectral_theorem -k norm -k orthogonality

# Visualize — no plotting libraries required
python concept_graph.py --domain linalg_graph visualize --format mermaid -o graph.mmd
python concept_graph.py --domain linalg_graph visualize --format dot --target pca
python concept_graph.py --domain linalg_graph visualize --format ascii

# Share — round-trips through plain JSON
python concept_graph.py --domain linalg_graph export shared.json --target spectral_theorem
python concept_graph.py import shared.json          # no --domain needed

# Compose a hybrid, multi-domain concept graph
python concept_graph.py compose -d linalg_graph -d geometry_graph hybrid.json
python concept_graph.py --domain hybrid.json stats   # analyze the result
```

`visualize --format mermaid` produces a flowchart that renders inline on
GitHub and most markdown viewers; `--format dot` produces Graphviz DOT
(`dot -Tpng -o graph.png graph.dot`); `--format ascii` is a tiered outline
readable in any terminal — none of these need matplotlib/graphviz/pyvis
installed.

## Why `compose`

Hand-authoring a concept graph that spans multiple fields is exactly the
kind of task no single publisher takes on — `compose` is the framework's
first mechanical step toward making that tractable: it unions the domains'
nodes and edges into one graph and writes it out in the same shareable JSON
shape `export` produces, so the result flows straight back through
`stats`/`show`/`visualize`/... via `--domain hybrid.json`.

It's kept deliberately simple for now: nodes merge by name, the last domain
wins on attribute conflicts, and every name collision across domains is
*reported* so the author can resolve it (rename one side, or confirm the
overlap is intentional and should become a bridging point). Smarter merge
strategies — explicit bridging edges, namespacing, alias maps — can layer on
top once real hybrid graphs show what's actually needed.
