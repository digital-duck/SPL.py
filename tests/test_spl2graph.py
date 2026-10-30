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


# --- function bodies become prompts, tool calls in conditions, IN, parallel branches ---------------------------------

CHAIN = """
CREATE FUNCTION research(topic TEXT)
RETURNS TEXT
AS $$
Research {topic}.
$$;

CREATE FUNCTION analyze(research TEXT, depth TEXT)
RETURNS TEXT
AS $$
Analyze at {depth} depth: {research}
$$;

WORKFLOW chain
    INPUT: @topic TEXT DEFAULT 'sails'
    OUTPUT: @out TEXT
DO
    GENERATE research(@topic) INTO @research
    GENERATE analyze(@research, 'shallow') INTO @out
    RETURN @out
END
"""


def _node(g, nid):
    return next(n for n in g["nodes"] if n["id"] == nid)


def test_a_function_body_is_the_prompt_and_a_literal_argument_is_a_port_default():
    g, warnings = spl_to_graph(CHAIN)
    assert warnings == []
    assert _node(g, "gen_1")["config"]["prompt_inline"] == "Research {{in_topic}}."
    gen2 = _node(g, "gen_2")
    assert gen2["config"]["prompt_inline"] == "Analyze at {{in_depth}} depth: {{in_research}}"
    assert gen2["config"]["phases"] == {"pre": {"defaults": {"in_depth": "shallow"}}}
    assert "in_depth" in gen2["ports"] and "in_research" in gen2["ports"]
    assert g["workflow"]["inputs"][0]["default"] == "sails"           # the value, not the quoted text


def test_chain_roundtrips_with_its_function_definitions():
    g, _ = spl_to_graph(CHAIN)
    text, _ = graph_to_spl(g)
    assert "CREATE FUNCTION analyze(research TEXT, depth TEXT)" in text and "Analyze at {depth} depth: {research}" in text
    assert roundtrip_diff(g) == []


def test_a_tool_call_in_an_assert_becomes_a_solve_that_runs_first():
    g, _ = spl_to_graph("""
WORKFLOW w
    INPUT: @x TEXT
    OUTPUT: @x TEXT
DO
    ASSERT known(@x);
    RETURN @x
END
""")
    tool = _node(g, "tool_1")
    assert tool["type"] == "SOLVE" and tool["config"]["expression"] == "known(@in_x)"
    assert _node(g, "assert_1")["config"]["condition"] == "@in_tool_1"


def test_parallel_branches_can_be_functions():
    g, _ = spl_to_graph("""
CREATE FUNCTION pro(claim TEXT) RETURNS TEXT AS $$ For: {claim} $$;
CREATE FUNCTION con(claim TEXT) RETURNS TEXT AS $$ Against: {claim} $$;

WORKFLOW w
    INPUT: @claim TEXT
    OUTPUT: @a TEXT
DO
    CALL PARALLEL
        pro(@claim) INTO @a,
        con(@claim) INTO @b
    END
    RETURN @a
END
""")
    assert {n["config"]["function"] for n in g["nodes"] if n["type"] == "GENERATE"} == {"pro", "con"}
