"""`python/domain_textbook` — runtime-resolved domain target (recipe 74).

Unlike `python/linalg` / `python/intro_geometry`, where `DomainConfig` names a
*fixed* graph module baked in at compile time, `python/domain_textbook`
resolves WHICH domain's concept graph to load from a `@domain_yaml` workflow
INPUT at *notebook run time* — the same `.spl` source compiles once and runs
against `linalg_graph.yaml` or `geometry_graph.yaml` (or any future
`{domain}_graph.yaml` shaped the same way) depending only on that input.

This is possible because recipe 74 split the frozen `linalg_graph.py`/
`geometry_graph.py` pattern into `graph_lib.py` (one shared, YAML-driven
algorithm library — see `cookbook/74_domain_textbook/graph_lib.py`) plus a
declarative `{domain}_graph.yaml` per domain. The setup cell therefore imports
ONE fixed module (`graph_lib`) and defers the *data* choice to
`graph_lib.load_domain(domain_yaml)`.

`DomainGraphTranspiler` already does ~95% of the work — every SPL → cell
construct mapping (SOLVE/ASSERT/CALL/EVALUATE/WHILE/GENERATE/COMMIT/...) is
domain-agnostic. The only thing that genuinely differs is the setup cell's
shape, so this subclass plugs into the two extension points
`DomainConfig.extra_imports` / `DomainConfig.graph_bootstrap` added to the
engine for exactly this case, rather than overriding any cell-emitter method.
"""

from __future__ import annotations

from spl3.splc.transpiler_domain_graph import DomainConfig, DomainGraphTranspiler

DOMAIN_TEXTBOOK_CONFIG = DomainConfig(
    target="python/domain_textbook",
    graph_module="graph_lib",
    graph_dir_env="DOMAIN_TEXTBOOK_GRAPH_DIR",
    framework="domain_textbook",
    primitives_fn="both_radical_primitives",
    verifiers=(),
    # `load_domain`/`verify_content` exist only on `graph_lib` — neither
    # `linalg_graph` nor `geometry_graph` (frozen, untouched) export them, so
    # they can't live in the engine's shared import list. `verify_content` is
    # then just a regular bare-name function the generic CALL-cell dispatch
    # routes to directly (see DomainConfig.verifiers docstring: no per-domain
    # `_verify_*` helper needed — graph_lib.verify_content already dispatches
    # on domain_data["domain"] internally).
    extra_imports=("load_domain", "verify_content"),
    # Replaces the engine's default "import {graph_module}; graph = dg.build()"
    # bootstrap (which assumes graph_module names a domain-specific module
    # whose data is fixed at compile time) with the runtime-resolved sequence:
    # read @domain_yaml, load it, and build @graph/@primitives/@domain_data
    # from whatever it names. `domain_data` becomes available to the .spl body
    # as `@domain_data` — e.g. `CALL verify_content(@section, @domain_data)`.
    graph_bootstrap=(
        "# Resolve the domain at notebook *runtime* from @domain_yaml (already",
        "# bound above from the workflow INPUT) — the defining trait of",
        "# python/domain_textbook (see DomainConfig.graph_bootstrap): linalg_graph.yaml /",
        "# geometry_graph.yaml / a future {domain}_graph.yaml all load through",
        "# the SAME graph_lib.load_domain()+build() path.",
        "domain_data = dg.load_domain(domain_yaml)",
        "graph = dg.build(domain_data)",
        "primitives = dg.both_radical_primitives(domain_data)",
        'print(f"{domain_yaml} loaded — domain={domain_data.get(\'domain\')!r}: '
        '{graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")',
    ),
)


class DomainTextbookTranspiler(DomainGraphTranspiler):
    """Compiles `.spl` sources whose concept graph is chosen at runtime.

    Same two-line preset shape as `LinalgTranspiler`/`IntroGeometryTranspiler`
    — the only difference is which `DomainConfig` it wraps.
    """

    def __init__(self, recipe_name: str, spl_dir=None):
        super().__init__(recipe_name, DOMAIN_TEXTBOOK_CONFIG, spl_dir=spl_dir)
