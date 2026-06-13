"""Tests for Layer 4 — cookbook recipes and linalg_graph additions.

Covers:
  - linalg_graph: gap() and learning_path() helper functions
  - build_concept_book.spl: parses, compiles to valid .ipynb, correct cell structure
  - answer_on_demand.spl: parses, compiles to valid .ipynb, correct cell structure
  - Transpiler fixes: _spl_expr handles FStringLiteral/BinaryOp, EVALUATE contains: prefix,
    GENERATE uses function param names for positional args, _spl_condition renders Condition
"""

from __future__ import annotations

import json
import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..",
                                "cookbook", "71_linalg_concept_book"))

import linalg_graph as lg
from spl.lexer import Lexer
from spl3.parser import SPL3Parser
from spl3.splc.transpiler_linalg import LinalgTranspiler
from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_COOKBOOK = Path(__file__).parent.parent / "cookbook" / "71_linalg_concept_book"


def _compile(recipe: str) -> dict:
    """Parse + transpile a recipe SPL file; return the parsed notebook dict."""
    spl_file = _COOKBOOK / f"{recipe}.spl"
    src = spl_file.read_text()
    tokens = Lexer(src).tokenize()
    program = SPL3Parser(tokens).parse()
    nb_json = LinalgTranspiler(recipe, spl_dir=_COOKBOOK).transpile(program)
    return json.loads(nb_json)


def _find_cells(nb: dict, tag: str) -> list[dict]:
    return [c for c in nb["cells"] if tag in c["metadata"].get("tags", [])]


def _cell_src(cell: dict) -> str:
    return "".join(cell["source"])


# ---------------------------------------------------------------------------
# A. linalg_graph additions: gap() and learning_path()
# ---------------------------------------------------------------------------

class TestGap:
    def setup_method(self):
        self.graph = lg.build()

    def test_gap_empty_learner_state_equals_ancestors(self):
        anc = lg.ancestors(self.graph, "eigenpair")
        gap = lg.gap(self.graph, "eigenpair", [])
        assert gap == anc

    def test_gap_removes_mastered_concepts(self):
        # If learner already knows linear_combination, it should not appear in gap
        gap = lg.gap(self.graph, "span", ["linear_combination"])
        assert "linear_combination" not in gap

    def test_gap_fully_mastered_returns_empty(self):
        anc = lg.ancestors(self.graph, "span")
        gap = lg.gap(self.graph, "span", anc)
        assert gap == set()

    def test_gap_returns_set(self):
        gap = lg.gap(self.graph, "eigenpair", [])
        assert isinstance(gap, set)

    def test_gap_ignores_unknown_mastered(self):
        # Unknown concepts in learner_state are silently ignored
        gap = lg.gap(self.graph, "span", ["not_a_real_concept", "also_fake"])
        expected = lg.ancestors(self.graph, "span")
        assert gap == expected

    def test_gap_partial_mastery(self):
        anc = lg.ancestors(self.graph, "eigenpair")
        mastered = list(anc)[:2]
        gap = lg.gap(self.graph, "eigenpair", mastered)
        assert len(gap) < len(anc)
        for m in mastered:
            assert m not in gap


class TestLearningPath:
    def setup_method(self):
        self.graph = lg.build()

    def test_learning_path_returns_list(self):
        path = lg.learning_path(self.graph, "span", [])
        assert isinstance(path, list)

    def test_learning_path_empty_when_fully_mastered(self):
        anc = lg.ancestors(self.graph, "span")
        path = lg.learning_path(self.graph, "span", anc)
        assert path == []

    def test_learning_path_subset_of_ancestors(self):
        path = lg.learning_path(self.graph, "eigenpair", [])
        anc = lg.ancestors(self.graph, "eigenpair")
        assert set(path) == anc

    def test_learning_path_topological_order(self):
        """Each concept appears before any concept that depends on it."""
        path = lg.learning_path(self.graph, "eigenpair", [])
        pos = {c: i for i, c in enumerate(path)}
        for u, v in self.graph.edges():
            if u in pos and v in pos:
                assert pos[u] < pos[v], f"{u} should come before {v}"

    def test_learning_path_partial_mastery_shorter(self):
        full = lg.learning_path(self.graph, "eigenpair", [])
        mastered = [full[0]]  # already know the first concept
        shorter = lg.learning_path(self.graph, "eigenpair", mastered)
        assert len(shorter) < len(full)

    def test_learning_path_weight_parameter_accepted(self):
        path = lg.learning_path(self.graph, "spectral_theorem", [], weight=2.0)
        assert isinstance(path, list)
        assert len(path) > 0


# ---------------------------------------------------------------------------
# B. build_concept_book.spl — parse and compile
# ---------------------------------------------------------------------------

class TestBuildMicroTextbookParse:
    def test_file_exists(self):
        assert (_COOKBOOK / "build_concept_book.spl").exists()

    def test_parses_without_error(self):
        src = (_COOKBOOK / "build_concept_book.spl").read_text()
        tokens = Lexer(src).tokenize()
        program = SPL3Parser(tokens).parse()
        assert program is not None

    def test_has_three_create_functions(self):
        src = (_COOKBOOK / "build_concept_book.spl").read_text()
        tokens = Lexer(src).tokenize()
        program = SPL3Parser(tokens).parse()
        from spl.ast_nodes import CreateFunctionStatement
        fns = [s for s in program.statements if isinstance(s, CreateFunctionStatement)]
        assert len(fns) == 3

    def test_has_workflow_named_build_concept_book(self):
        src = (_COOKBOOK / "build_concept_book.spl").read_text()
        tokens = Lexer(src).tokenize()
        program = SPL3Parser(tokens).parse()
        from spl.ast_nodes import WorkflowStatement
        wfs = [s for s in program.statements if isinstance(s, WorkflowStatement)]
        assert len(wfs) == 1
        assert wfs[0].name == "build_concept_book"

    def test_workflow_inputs(self):
        src = (_COOKBOOK / "build_concept_book.spl").read_text()
        tokens = Lexer(src).tokenize()
        program = SPL3Parser(tokens).parse()
        from spl.ast_nodes import WorkflowStatement
        wf = next(s for s in program.statements if isinstance(s, WorkflowStatement))
        names = {p.name for p in wf.inputs}
        assert "target" in names
        assert "primitive_budget" in names
        assert "payoff_weight" in names

    def test_workflow_output(self):
        src = (_COOKBOOK / "build_concept_book.spl").read_text()
        tokens = Lexer(src).tokenize()
        program = SPL3Parser(tokens).parse()
        from spl.ast_nodes import WorkflowStatement
        wf = next(s for s in program.statements if isinstance(s, WorkflowStatement))
        assert any(p.name == "textbook" for p in wf.outputs)


class TestBuildMicroTextbookNotebook:
    def setup_method(self):
        self.nb = _compile("build_concept_book")

    def test_valid_nbformat4(self):
        assert self.nb["nbformat"] == 4

    def test_has_cells(self):
        assert len(self.nb["cells"]) > 5

    def test_first_cell_is_markdown_header(self):
        cell = self.nb["cells"][0]
        assert cell["cell_type"] == "markdown"
        src = _cell_src(cell)
        assert "build concept" in src.lower()

    def test_setup_cell_imports_linalg_graph(self):
        setup = self.nb["cells"][1]
        src = _cell_src(setup)
        # Engine generalization (transpiler_domain_graph) renamed the alias lg → dg
        assert "import linalg_graph as dg" in src
        assert "graph = dg.build()" in src
        assert "gap" in src
        assert "learning_path" in src

    def test_assert_acyclic_cell(self):
        assert_cells = _find_cells(self.nb, "assert")
        srcs = ["".join(c["source"]) for c in assert_cells]
        assert any("acyclic" in s for s in srcs)

    def test_assert_reducible_cell(self):
        assert_cells = _find_cells(self.nb, "assert")
        srcs = ["".join(c["source"]) for c in assert_cells]
        assert any("reducible" in s for s in srcs)

    def test_solve_needed_cell(self):
        solve_cells = _find_cells(self.nb, "solve")
        srcs = ["".join(c["source"]) for c in solve_cells]
        assert any("ancestors" in s and "needed" in s for s in srcs)

    def test_solve_order_cell(self):
        solve_cells = _find_cells(self.nb, "solve")
        srcs = ["".join(c["source"]) for c in solve_cells]
        assert any("productivity_order" in s and "order" in s for s in srcs)

    def test_has_while_cell(self):
        while_cells = _find_cells(self.nb, "while")
        assert len(while_cells) >= 1

    def test_while_loops_over_order(self):
        while_cells = _find_cells(self.nb, "while")
        src = _cell_src(while_cells[0])
        assert "_i < order_len" in src
        assert "_while_iter" in src

    def test_while_body_contains_generate_write_section(self):
        while_cells = _find_cells(self.nb, "while")
        src = _cell_src(while_cells[0])
        assert "write_section" in src.lower() or "WRITE_SECTION_PROMPT" in src

    def test_while_body_verify_math(self):
        while_cells = _find_cells(self.nb, "while")
        src = _cell_src(while_cells[0])
        assert "_verify_math" in src

    def test_while_body_shape_check(self):
        while_cells = _find_cells(self.nb, "while")
        src = _cell_src(while_cells[0])
        assert "_shape_check" in src

    def test_while_evaluate_contains_fail(self):
        """WHEN contains('fail') should compile to 'fail' in str(check).lower()."""
        while_cells = _find_cells(self.nb, "while")
        src = _cell_src(while_cells[0])
        assert '"fail" in str(' in src

    def test_generate_write_payoff_cell(self):
        gen_cells = _find_cells(self.nb, "generate")
        srcs = [_cell_src(c) for c in gen_cells]
        assert any("write_payoff" in s.lower() or "WRITE_PAYOFF_PROMPT" in s for s in srcs)

    def test_commit_cell_present(self):
        commit_cells = _find_cells(self.nb, "commit")
        assert len(commit_cells) >= 1
        src = _cell_src(commit_cells[0])
        assert "textbook" in src

    def test_generate_format_uses_param_names(self):
        """format() calls must not have positional args mixed with keyword args."""
        all_src = " ".join(_cell_src(c) for c in self.nb["cells"])
        import re
        # Find all .format( calls and verify no bare strings before keyword args
        format_calls = re.findall(r"\.format\(([^)]+)\)", all_src)
        for call in format_calls:
            parts = [p.strip() for p in call.split(",")]
            saw_keyword = False
            for part in parts:
                is_kw = "=" in part and not part.startswith('"') and not part.startswith("'")
                if is_kw:
                    saw_keyword = True
                elif saw_keyword:
                    pytest.fail(f"Positional arg after keyword in .format({call})")


class TestBuildMicroTextbookPrompts:
    def setup_method(self):
        self.nb = _compile("build_concept_book")

    def test_prompts_cell_exists(self):
        cell = self.nb["cells"][2]
        assert cell["cell_type"] == "code"
        src = _cell_src(cell)
        assert "PROMPT" in src

    def test_write_section_prompt_present(self):
        src = " ".join(_cell_src(c) for c in self.nb["cells"])
        assert "WRITE_SECTION_PROMPT" in src

    def test_refine_section_prompt_present(self):
        src = " ".join(_cell_src(c) for c in self.nb["cells"])
        assert "REFINE_SECTION_PROMPT" in src

    def test_write_payoff_prompt_present(self):
        src = " ".join(_cell_src(c) for c in self.nb["cells"])
        assert "WRITE_PAYOFF_PROMPT" in src


# ---------------------------------------------------------------------------
# C. answer_on_demand.spl — parse and compile
# ---------------------------------------------------------------------------

class TestAnswerOnDemandParse:
    def test_file_exists(self):
        assert (_COOKBOOK / "answer_on_demand.spl").exists()

    def test_parses_without_error(self):
        src = (_COOKBOOK / "answer_on_demand.spl").read_text()
        tokens = Lexer(src).tokenize()
        program = SPL3Parser(tokens).parse()
        assert program is not None

    def test_has_three_create_functions(self):
        src = (_COOKBOOK / "answer_on_demand.spl").read_text()
        tokens = Lexer(src).tokenize()
        program = SPL3Parser(tokens).parse()
        from spl.ast_nodes import CreateFunctionStatement
        fns = [s for s in program.statements if isinstance(s, CreateFunctionStatement)]
        assert len(fns) == 3

    def test_has_workflow_named_answer_on_demand(self):
        src = (_COOKBOOK / "answer_on_demand.spl").read_text()
        tokens = Lexer(src).tokenize()
        program = SPL3Parser(tokens).parse()
        from spl.ast_nodes import WorkflowStatement
        wfs = [s for s in program.statements if isinstance(s, WorkflowStatement)]
        assert len(wfs) == 1
        assert wfs[0].name == "answer_on_demand"

    def test_workflow_inputs(self):
        src = (_COOKBOOK / "answer_on_demand.spl").read_text()
        tokens = Lexer(src).tokenize()
        program = SPL3Parser(tokens).parse()
        from spl.ast_nodes import WorkflowStatement
        wf = next(s for s in program.statements if isinstance(s, WorkflowStatement))
        names = {p.name for p in wf.inputs}
        assert "question" in names
        assert "learner_state" in names


class TestAnswerOnDemandNotebook:
    def setup_method(self):
        self.nb = _compile("answer_on_demand")

    def test_valid_nbformat4(self):
        assert self.nb["nbformat"] == 4

    def test_first_cell_is_markdown_header(self):
        cell = self.nb["cells"][0]
        assert cell["cell_type"] == "markdown"
        src = _cell_src(cell)
        assert "answer on demand" in src.lower()

    def test_setup_cell_imports_gap_and_learning_path(self):
        setup = self.nb["cells"][1]
        src = _cell_src(setup)
        assert "gap" in src
        assert "learning_path" in src

    def test_solve_concept_list_cell(self):
        solve_cells = _find_cells(self.nb, "solve")
        srcs = [_cell_src(c) for c in solve_cells]
        assert any("concept_names" in s and "concept_list" in s for s in srcs)

    def test_generate_resolve_target_cell(self):
        gen_cells = _find_cells(self.nb, "generate")
        srcs = [_cell_src(c) for c in gen_cells]
        assert any("resolve_target" in s.lower() or "RESOLVE_TARGET_PROMPT" in s for s in srcs)

    def test_assert_in_graph_cell(self):
        assert_cells = _find_cells(self.nb, "assert")
        srcs = [_cell_src(c) for c in assert_cells]
        assert any("in_graph" in s for s in srcs)

    def test_solve_learning_path_cell(self):
        solve_cells = _find_cells(self.nb, "solve")
        srcs = [_cell_src(c) for c in solve_cells]
        assert any("learning_path" in s and "order" in s for s in srcs)

    def test_has_while_cell(self):
        while_cells = _find_cells(self.nb, "while")
        assert len(while_cells) >= 1

    def test_while_body_generate_write_section(self):
        while_cells = _find_cells(self.nb, "while")
        src = _cell_src(while_cells[0])
        assert "write_section" in src.lower() or "WRITE_SECTION_PROMPT" in src

    def test_while_evaluate_contains_fail(self):
        while_cells = _find_cells(self.nb, "while")
        src = _cell_src(while_cells[0])
        assert '"fail" in str(' in src

    def test_capstone_generate_write_section_for_target(self):
        gen_cells = _find_cells(self.nb, "generate")
        srcs = [_cell_src(c) for c in gen_cells]
        # The capstone generates write_section(@target, @target)
        assert any("capstone" in s for s in srcs)

    def test_commit_cell_present(self):
        commit_cells = _find_cells(self.nb, "commit")
        assert len(commit_cells) >= 1
        src = _cell_src(commit_cells[0])
        assert "lesson" in src


# ---------------------------------------------------------------------------
# D. Transpiler fix regression tests
# ---------------------------------------------------------------------------

class TestTranspilerFixes:
    """Regression tests for the four transpiler fixes applied during Layer 4."""

    def _transpile(self, spl_src: str) -> dict:
        tokens = Lexer(spl_src).tokenize()
        program = SPL3Parser(tokens).parse()
        nb_json = LinalgTranspiler("test_wf").transpile(program)
        return json.loads(nb_json)

    def test_fstring_logging_comment_rendered_correctly(self):
        """LOGGING with f-string should produce readable comment, not FStringLiteral(...)."""
        spl = """\
WORKFLOW test
    INPUT: @n INT
    OUTPUT: @out TEXT
DO
    LOGGING f'Count: {@n}' LEVEL INFO
    COMMIT @out
END
"""
        nb = self._transpile(spl)
        log_cells = _find_cells(nb, "logging")
        src = _cell_src(log_cells[0])
        assert "FStringLiteral" not in src
        assert "SPL: LOGGING f'" in src

    def test_binary_op_assignment_comment_rendered(self):
        """@x := @a + @b assignment comment should not show BinaryOp(...)."""
        spl = """\
WORKFLOW test
    INPUT: @a TEXT, @b TEXT
    OUTPUT: @x TEXT
DO
    @x := @a + @b
    COMMIT @x
END
"""
        nb = self._transpile(spl)
        all_src = " ".join(_cell_src(c) for c in nb["cells"])
        assert "BinaryOp" not in all_src

    def test_evaluate_contains_strips_contains_prefix(self):
        """WHEN contains('fail') should compile to 'fail' in str(v), not 'contains:fail' in str(v)."""
        spl = """\
WORKFLOW test
    INPUT: @result TEXT
    OUTPUT: @out TEXT
DO
    EVALUATE @result
        WHEN contains('fail') THEN
            LOGGING 'bad' LEVEL INFO
        ELSE
            LOGGING 'ok' LEVEL INFO
    END
    COMMIT @out
END
"""
        nb = self._transpile(spl)
        eval_cells = _find_cells(nb, "evaluate")
        src = _cell_src(eval_cells[0])
        assert '"fail" in str(' in src
        assert "contains:fail" not in src

    def test_while_condition_comment_readable(self):
        """WHILE @i < @n DO comment should show '@i < @n', not Condition(...)."""
        spl = """\
WORKFLOW test
    INPUT: @n INT
    OUTPUT: @out TEXT
DO
    @i := 0
    WHILE @i < @n DO
        @i := @i + 1
    END
    COMMIT @out
END
"""
        nb = self._transpile(spl)
        while_cells = _find_cells(nb, "while")
        src = _cell_src(while_cells[0])
        assert "Condition(" not in src
        assert "SPL: WHILE @i < @n DO" in src

    def test_generate_literal_arg_uses_param_name(self):
        """Literal args to GENERATE should use CREATE FUNCTION param name, not positional."""
        spl = """\
CREATE FUNCTION greet(name TEXT, style TEXT)
RETURN TEXT
AS $$
Hello {name} in {style} style.
$$;

WORKFLOW test
    INPUT: @who TEXT
    OUTPUT: @out TEXT
DO
    GENERATE greet(@who, 'formal') INTO @out
    COMMIT @out
END
"""
        nb = self._transpile(spl)
        gen_cells = _find_cells(nb, "generate")
        src = _cell_src(gen_cells[0])
        assert "style='formal'" in src
        # Must not have 'formal' as a bare positional arg after a keyword arg
        assert "name=who, style='formal'" in src

    def test_generate_two_paramref_args_correct_param_names(self):
        """Two ParamRef args map to their declared param names, not their variable names."""
        spl = """\
CREATE FUNCTION write_section(concept TEXT, context TEXT)
RETURN TEXT
AS $$
Section: {concept}  Context: {context}
$$;

WORKFLOW test
    INPUT: @concept TEXT
    OUTPUT: @section TEXT
DO
    GENERATE write_section(@concept, @concept) INTO @section
    COMMIT @section
END
"""
        nb = self._transpile(spl)
        gen_cells = _find_cells(nb, "generate")
        src = _cell_src(gen_cells[0])
        # concept is param 0, context is param 1 — even if same variable
        assert "concept=concept, context=concept" in src

    def test_assert_in_graph_renders_correct_python(self):
        """ASSERT in_graph(@graph, @target) should call bool(in_graph(graph, target))."""
        spl = """\
WORKFLOW test
    INPUT: @target TEXT
    OUTPUT: @out TEXT
DO
    ASSERT in_graph(@graph, @target)
    COMMIT @out
END
"""
        nb = self._transpile(spl)
        assert_cells = _find_cells(nb, "assert")
        src = _cell_src(assert_cells[0])
        assert "bool(in_graph(graph, target))" in src
