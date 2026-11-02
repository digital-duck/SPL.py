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


def test_yaml_writes_multiline_text_as_a_block():
    import yaml
    code = "def shout(text):\n    return text.upper() + '!'\n"
    odd = "trailing space \nsecond line"                         # a block cannot hold this exactly: it falls back to a quoted string
    text = graph_to_yaml({"config": {"code": code, "odd": odd, "one": "single line"}})
    assert "code: |\n    def shout(text):\n        return text.upper() + '!'\n" in text
    assert yaml.safe_load(text) == {"config": {"code": code, "odd": odd, "one": "single line"}}


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


# --- Python tools become kernel SOLVE nodes that carry their source ----------------------------------------------------

TOOLED = """
CREATE TOOL_API shout(text TEXT, suffix TEXT) RETURNS TEXT AS PYTHON $$
def shout(text: str, suffix: str) -> str:
    return text.strip().upper() + suffix
$$;

WORKFLOW w
    INPUT: @word TEXT DEFAULT 'hi'
    OUTPUT: @loud TEXT
DO
    CALL shout(@word, '!') INTO @loud
    RETURN @loud
END
"""


def test_a_tool_call_becomes_a_kernel_solve_with_the_tool_source():
    g, warnings = spl_to_graph(TOOLED)
    assert warnings == []
    cfg = _node(g, "tool_1")["config"]
    assert cfg["backend"] == "kernel" and cfg["tool"] == "shout" and cfg["result"] == "_spl_result"
    assert cfg["code"].rstrip().endswith("_spl_result = shout(word, '!')") and "def shout(text: str" in cfg["code"]
    assert cfg["out_type"] == "TEXT" and cfg["arguments"] == ["@word", "'!'"]
    assert _node(g, "tool_1")["ports"] == ["trigger", "complete", "in_word", "out_loud"]


def test_a_tool_roundtrips_with_its_definition():
    g, _ = spl_to_graph(TOOLED)
    text, _ = graph_to_spl(g)
    assert "CREATE TOOL_API shout(text TEXT, suffix TEXT)" in text and "CALL shout(@word, '!') INTO @loud" in text
    assert roundtrip_diff(g) == []


def test_a_builtin_tool_brings_its_source_and_a_broken_one_only_a_warning():
    g, warnings = spl_to_graph("""
WORKFLOW w
    INPUT: @p TEXT
    OUTPUT: @p TEXT
DO
    CALL write_file(@p, 'x') INTO NONE
    RETURN @p
END
""")
    cfg = _node(g, "tool_1")["config"]
    assert cfg["backend"] == "kernel" and cfg["tool_builtin"] and "def write_file" in cfg["code"] and "import pathlib" in cfg["code"]
    g, warnings = spl_to_graph(TOOLED.replace("return text.strip().upper() + suffix", "return ''x''"))
    cfg = _node(g, "tool_1")["config"]
    assert "backend" not in cfg and cfg["expression"] == "shout(@word, '!')" and "does not compile" in warnings[0]


# --- WHILE: a counter reads its first value as an input and later ones as state; a tool call in the condition runs twice ----

COUNTER = """
WORKFLOW counter
    INPUT: @x TEXT DEFAULT 'a'
    OUTPUT: @n INTEGER
DO
    @n := 0;
    WHILE @n < 3 DO
        @n := @n + 1;
    END;
    COMMIT @n
END
"""


def test_a_loop_variable_is_read_as_input_on_the_first_check_and_as_state_after():
    g, warnings = spl_to_graph(COUNTER)
    loop = next(n for n in g["nodes"] if n["type"] == "LOOP")
    assert warnings == [] and "in_n" in loop["ports"]
    assert loop["config"]["condition"] == "latest(@in_n, @n) < 3"
    assert loop["config"]["subgraph"]["nodes"][0]["config"]["expression"] == "@in_n + 1"      # assignments read their ports as @in_x
    assert roundtrip_diff(g) == []


def test_a_tool_call_in_a_while_condition_runs_before_the_loop_and_again_at_the_end_of_the_body():
    g, _ = spl_to_graph("""
WORKFLOW w
    INPUT: @x TEXT
    OUTPUT: @x TEXT
DO
    WHILE NOT done(@x) DO
        @x := 'y';
    END;
    RETURN @x
END
""")
    loop = next(n for n in g["nodes"] if n["type"] == "LOOP")
    assert [n["id"] for n in g["nodes"] if n["id"].startswith("tool_")] == ["tool_1"]            # before the loop
    body = [n["id"] for n in loop["config"]["subgraph"]["nodes"]]
    assert "tool_2" in body and body[-1] == "tool_2"                                             # the last body step
    assert loop["config"]["condition"] == "NOT latest(@in_tool_1, @tool_2)"
    assert "in_tool_1" in loop["ports"] and loop["config"]["outputs"]["tool_2"]["from"] == "tool_2.out_tool_2"


# -- lessons from lifting the 47 cookbook-solver recipes -------------------------------------------------

_LOOP_SPL = '''
CREATE FUNCTION ask(problem TEXT, hint TEXT)
RETURNS TEXT AS $$
Solve: {problem}
Hint: {hint}
Return {{"answer": 1}}
$$;

WORKFLOW w
  INPUT: @problem_text TEXT, @n INTEGER := 1
  OUTPUT: @out TEXT
DO
  @i := 0;
  @out := '';
  WHILE @i < @n DO
    GENERATE ask(@problem_text, 'be brief') INTO @out;
    @i := @i + 1;
  END
  COMMIT @out WITH status = 'complete';
END
'''


def _gens(nodes):
    for n in nodes:
        if n["type"] == "GENERATE":
            yield n
        sub = n.get("config", {}).get("subgraph")
        if sub:
            yield from _gens(sub["nodes"])


def test_a_prompt_placeholder_and_its_port_are_named_after_the_variable_passed():
    """Inside a LOOP body an outer variable reaches a node by its own name; a port named after the parameter was never fed."""
    g, _ = spl_to_graph(_LOOP_SPL)
    (gen,) = list(_gens(g["nodes"]))
    assert "in_problem_text" in gen["ports"] and "in_problem" not in gen["ports"]
    assert "{{in_problem_text}}" in gen["config"]["prompt_inline"]
    assert '{{"answer": 1}}' in gen["config"]["prompt_inline"]                 # an escaped brace is not a placeholder
    assert gen["config"]["params"] == ["problem_text", "hint"]
    assert gen["config"]["phases"]["pre"]["defaults"] == {"in_hint": "be brief"}


def test_a_swap_of_parameter_and_variable_names_is_not_mixed_up():
    g, _ = spl_to_graph('''
CREATE FUNCTION f(a TEXT, b TEXT)
RETURNS TEXT AS $$
{a} then {b}
$$;
WORKFLOW w
  INPUT: @a TEXT, @b TEXT
  OUTPUT: @r TEXT
DO
  GENERATE f(@b, @a) INTO @r;
  COMMIT @r WITH status = 'complete';
END
''')
    (gen,) = list(_gens(g["nodes"]))
    assert gen["config"]["prompt_inline"] == "{{in_b}} then {{in_a}}"
    bound = {e["target"]: e["source"] for e in g["edges"] if e["type"] == "binds" and e["target"].startswith(gen["id"])}
    assert bound[f"{gen['id']}.in_b"] == "wf_entry.out_b" and bound[f"{gen['id']}.in_a"] == "wf_entry.out_a"


def test_a_tool_returns_what_its_annotation_says(tmp_path):
    from spl3.spl2graph import _module_tool

    (tmp_path / "tools.py").write_text("def ok(x) -> bool:\n    return True\n\ndef rows(x) -> list[dict]:\n    return []\n\ndef text(x):\n    return ''\n")
    got = {n: _module_tool(n, tmp_path / "tools.py").return_type for n in ("ok", "rows", "text")}
    assert got == {"ok": "BOOL", "rows": "JSON", "text": "TEXT"}


def test_a_solve_statement_is_a_kernel_node_in_the_named_kernel():
    src = '''
WORKFLOW w
  INPUT: @expr TEXT
  OUTPUT: @r TEXT
DO
  SOLVE @r TEXT := str(factor(QQ['x'](@expr)));
  ASSERT len(str(_spl_solve_result)) > 0;
  COMMIT @r WITH status = 'complete';
END
'''
    g, _ = spl_to_graph(src, kernel_name="sagemath")
    solve = next(n for n in g["nodes"] if n["type"] == "SOLVE")
    assert solve["config"] == {"backend": "kernel", "code": "", "result": "str(factor(QQ['x'](expr)))", "out_type": "TEXT", "kernel_name": "sagemath"}
    assert "in_expr" in solve["ports"]
    assert_ = next(n for n in g["nodes"] if n["type"] == "ASSERT")
    assert "@in__spl_solve_result" in assert_["config"]["condition"]
    assert any(e["target"] == f"{assert_['id']}.in__spl_solve_result" for e in g["edges"])


def test_files_the_graph_needs_are_reported(tmp_path):
    (tmp_path / "helper.spl").write_text("CREATE FUNCTION h(x TEXT)\nRETURNS TEXT AS $$\n{x}\n$$;\n\nWORKFLOW helper\n  INPUT: @x TEXT\n  OUTPUT: @y TEXT\nDO\n  GENERATE h(@x) INTO @y;\n  COMMIT @y WITH status = 'complete';\nEND\n")
    (tmp_path / "tools.spl").write_text("")
    main = "IMPORT 'tools';\n\nWORKFLOW main\n  INPUT: @x TEXT\n  OUTPUT: @y TEXT\nDO\n  CALL helper(@x) INTO @y;\n  COMMIT @y WITH status = 'complete';\nEND\n"
    _, warnings = spl_to_graph(main, source_name="main.spl", source_dir=tmp_path)
    assert any("helper.spl" in w and "next to the graph" in w for w in warnings)
    assert any("tools.spl" in w for w in warnings)


def test_tool_types_come_from_the_annotation_run_python_stays_in_the_kernel_and_runtime_counters_are_not_inputs():
    src = '''
CREATE TOOL_API ok(x TEXT)
RETURNS TEXT AS PYTHON $$
def ok(x: str) -> bool:
    return True
$$;

CREATE TOOL_API metrics(a TEXT, b TEXT, c TEXT)
RETURNS TEXT AS PYTHON $$
def metrics(a, b, c) -> str:
    return a
$$;

WORKFLOW w
  INPUT: @x TEXT
  OUTPUT: @r TEXT
DO
  CALL ok(@x) INTO @good;
  CALL metrics(@x, @_total_input_tokens, @_total_output_tokens) INTO @r;
  CALL run_python('print(1)') INTO @out;
  COMMIT @r WITH status = 'complete';
END
'''
    g, _ = spl_to_graph(src)
    tools = {n["config"]["tool"]: n for n in g["nodes"] if n["type"] == "SOLVE"}
    assert tools["ok"]["config"]["out_type"] == "BOOL"
    m = tools["metrics"]
    assert "globals().get('_total_input_tokens', 0)" in m["config"]["code"]
    assert not any("_total" in p for p in m["ports"]) and not any("_total" in e["source"] for e in g["edges"])
    assert "exec(str(code), globals())" in tools["run_python"]["config"]["code"]


def test_a_text_result_compared_with_a_number_is_read_as_a_number():
    g, _ = spl_to_graph(_LOOP_SPL.replace("WHILE @i < @n DO", "WHILE @i < @limit DO").replace("  @i := 0;", "  GENERATE ask(@problem_text, 'x') INTO @limit;\n  @i := 0;"))
    loop = next(n for n in g["nodes"] if n["type"] == "LOOP")
    assert "float(" in loop["config"]["condition"] and "limit" in loop["config"]["condition"]
