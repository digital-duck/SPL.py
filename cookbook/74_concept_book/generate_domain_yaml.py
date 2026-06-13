"""One-shot generator: {domain}_graph.py → {domain}_graph.yaml

Run once to produce the YAML twins of recipe 71's `linalg_graph.py` and
recipe 73's `geometry_graph.py` data — losslessly, by importing the frozen
modules and dumping their `_PRIMITIVES`/`_CONCEPTS`/`_APPLICATIONS` dicts
plus `first_radical_primitives()` (a curated subset, not a derived quantity —
see graph_lib.first_radical_primitives's docstring) straight to YAML.

This is a generator script, not part of the runtime path — recipe 74's
notebooks load the *.yaml files via graph_lib.load_domain(), never these
source .py modules. Re-run only if linalg_graph.py / geometry_graph.py
content changes (they are frozen/"fully vested" today).

Usage:
    python generate_domain_yaml.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

HERE = Path(__file__).parent
ROOT = HERE.parent.parent  # .../SPL.py


def _dump(domain_name: str, module, out_path: Path) -> None:
    data = {
        "domain": domain_name,
        "primitives": module._PRIMITIVES,
        "first_radical_primitives": module.first_radical_primitives(),
        "concepts": module._CONCEPTS,
        "applications": module._APPLICATIONS,
    }
    with out_path.open("w", encoding="utf-8") as fh:
        yaml.dump(data, fh, sort_keys=False, allow_unicode=True, default_flow_style=False, width=100)
    print(f"Wrote {out_path}  ({len(module._PRIMITIVES)} primitives, "
          f"{len(module._CONCEPTS)} concepts, {len(module._APPLICATIONS)} applications)")


def main() -> None:
    sys.path.insert(0, str(ROOT / "cookbook" / "71_linalg_concept_book"))
    sys.path.insert(0, str(ROOT / "cookbook" / "73_intro_geometry"))

    import linalg_graph
    import geometry_graph

    _dump("linalg", linalg_graph, HERE / "linalg_graph.yaml")
    _dump("intro_geometry", geometry_graph, HERE / "geometry_graph.yaml")


if __name__ == "__main__":
    main()
