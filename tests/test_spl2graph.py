"""spl2graph: SPL workflow -> GraphLang graph dict."""
from pathlib import Path

import pytest

from spl3.spl2graph import NoWorkflowError, graph_to_yaml, spl_to_graph

RECIPE = Path(__file__).resolve().parent.parent / "cookbook" / "005_self_refine" / "self_refine.spl"


def _graph():
    return spl_to_graph(RECIPE.read_text(), source_name=RECIPE.name, source_dir=RECIPE.parent)


def test_structure_and_wiring():
    g, warnings = _graph()
    assert g["version"] == "1.0-graph"
    ids = {n["id"]: n for n in g["nodes"]}
    assert ids["wf_entry"]["type"] == "INPUT" and ids["wf_exit"]["type"] == "OUTPUT"
    for e in g["edges"]:
        for end in (e["source"], e["target"]):
            node, port = end.split(".")
            assert port in ids[node]["ports"], end
    assert any(e["type"] == "triggers" and e["source"] == "wf_entry.entry" for e in g["edges"])
    assert any(n["type"] == "LOOP" for n in g["nodes"])
    # self_refine commits from inside its WHILE body (early exit), which a LOOP body cannot express yet
    assert all(w.startswith("COMMIT inside a WHILE body") for w in warnings)


def test_unknown_workflow_name():
    with pytest.raises(NoWorkflowError):
        spl_to_graph(RECIPE.read_text(), workflow="nope")


def test_yaml_roundtrip():
    import yaml
    g, _ = _graph()
    assert yaml.safe_load(graph_to_yaml(g)) == g


# --- graph2spl / round trip -------------------------------------------------

from spl3.graph2spl import graph_to_spl, roundtrip_diff  # noqa: E402

COOKBOOK = RECIPE.parent.parent


def _recipes():
    names = ["005_self_refine/self_refine.spl", "050_code_pipeline/04_test_code.spl",
             "050_code_pipeline/code_pipeline.spl", "007_safe_generation/safe_generation.spl",
             "063_parallel_code_review/parallel_code_review.spl"]
    return [COOKBOOK / n for n in names if (COOKBOOK / n).exists()]


@pytest.mark.parametrize("path", _recipes(), ids=lambda p: p.name)
def test_roundtrip_fixed_point(path):
    g, _ = spl_to_graph(path.read_text(), source_name=path.name, source_dir=path.parent)
    assert roundtrip_diff(g, path.name, path.parent) == []


def test_graph2spl_emits_parseable_structure():
    g, _ = _graph()
    text, _ = graph_to_spl(g)
    assert "WHILE @iteration < @max_iterations DO" in text
    assert "EVALUATE @feedback" in text and "WHEN contains('[APPROVED]') THEN" in text
    assert text.rstrip().endswith("END")


def test_graph2spl_rejects_non_workflow():
    from spl3.graph2spl import GraphToSPLError
    with pytest.raises(GraphToSPLError):
        graph_to_spl({"workflow": {"name": "x"}, "nodes": [], "edges": []})
