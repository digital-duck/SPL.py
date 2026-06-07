"""Tests for the python/linalg splc transpiler (Layer 3).

Covers:
  - SUPPORTED_LANGS registration
  - DETERMINISTIC_LANGS membership
  - Transpiler output: valid .ipynb JSON, correct cell count, correct cell types
  - SOLVE cells: @@var@@ substituted, correct Python variable assignment
  - ASSERT cells: bool(expr) assertion, OTHERWISE handler emitted
  - GENERATE cells: _llm_call() helper present, target variable assigned
  - CALL cells: function call present
  - EVALUATE cells: if/elif structure
  - LOGGING cells: print() present
  - COMMIT cells: output file write present
  - Header cell: markdown with workflow name
  - Setup cell: linalg_graph import + helper definitions + parameter defaults
  - CREATE FUNCTION → prompt constant in prompts cell
  - splc CLI: python/linalg listed in click.Choice options
"""

from __future__ import annotations

import json
import sys
import os

import pytest

# Ensure the spl123 package root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from spl.lexer import Lexer
from spl3.parser import SPL3Parser
from spl3.splc.transpiler_linalg import LinalgTranspiler
from spl3.splc.cli import SUPPORTED_LANGS, DETERMINISTIC_LANGS


# ---------------------------------------------------------------------------
# Minimal SPL source for most tests
# ---------------------------------------------------------------------------

_MINIMAL_SPL = """\
-- Minimal linalg workflow for transpiler tests
WORKFLOW query_graph
    INPUT:  @target TEXT, @payoff_weight FLOAT
    OUTPUT: @order TEXT
DO
    ASSERT acyclic(@graph)
    SOLVE @needed SET := ancestors(@graph, @target)
    SOLVE @order LIST := productivity_order(restrict(@graph, @needed), weight=@payoff_weight)
    LOGGING "Order: " + @order
    COMMIT @order
END
"""

_GENERATE_SPL = """\
WORKFLOW gen_workflow
    INPUT: @domain TEXT
    OUTPUT: @result TEXT
DO
    GENERATE propose_basis(@domain) INTO @primitives
    CALL verify_math(@primitives) INTO @check
    EVALUATE @check
        WHEN contains('fail') THEN
            GENERATE refine(@primitives, @check) INTO @primitives
    END
    COMMIT @primitives
END
"""

_FUNCTION_SPL = """\
CREATE FUNCTION propose_basis(domain TEXT)
RETURN TEXT
AS $$
Propose the primitive basis for the domain: {domain}.
List the irreducible fundamental operations from which all concepts are composed.
$$

WORKFLOW with_prompts
    INPUT: @domain TEXT
    OUTPUT: @result TEXT
DO
    GENERATE propose_basis(@domain) INTO @primitives
    COMMIT @primitives
END
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _transpile(spl_src: str, recipe_name: str = "test_workflow") -> dict:
    """Parse spl_src and transpile to notebook dict."""
    tokens = Lexer(spl_src).tokenize()
    program = SPL3Parser(tokens).parse()
    transpiler = LinalgTranspiler(recipe_name)
    nb_json = transpiler.transpile(program)
    return json.loads(nb_json)


def _cells(nb: dict) -> list[dict]:
    return nb["cells"]


def _code_cells(nb: dict) -> list[dict]:
    return [c for c in nb["cells"] if c["cell_type"] == "code"]


def _markdown_cells(nb: dict) -> list[dict]:
    return [c for c in nb["cells"] if c["cell_type"] == "markdown"]


def _cell_src(cell: dict) -> str:
    return "".join(cell["source"])


def _find_cells_with(nb: dict, tag: str) -> list[dict]:
    return [c for c in nb["cells"] if tag in c.get("metadata", {}).get("tags", [])]


# ---------------------------------------------------------------------------
# Registration tests
# ---------------------------------------------------------------------------

class TestRegistration:
    def test_python_linalg_in_supported_langs(self):
        assert "python/linalg" in SUPPORTED_LANGS

    def test_python_linalg_ext_is_ipynb(self):
        assert SUPPORTED_LANGS["python/linalg"]["ext"] == ".ipynb"

    def test_python_linalg_in_deterministic_langs(self):
        assert "python/linalg" in DETERMINISTIC_LANGS

    def test_label_contains_linalg(self):
        assert "linalg" in SUPPORTED_LANGS["python/linalg"]["label"].lower()

    def test_cli_choice_includes_python_linalg(self):
        """The click.Choice list for --lang includes python/linalg."""
        import click
        from click.testing import CliRunner
        from spl3.splc.cli import splc

        runner = CliRunner()
        result = runner.invoke(splc, ["compile", "--help"])
        assert "python/linalg" in result.output


# ---------------------------------------------------------------------------
# Notebook structure tests
# ---------------------------------------------------------------------------

class TestNotebookStructure:
    def test_valid_json(self):
        nb = _transpile(_MINIMAL_SPL)
        assert isinstance(nb, dict)

    def test_nbformat_4(self):
        nb = _transpile(_MINIMAL_SPL)
        assert nb["nbformat"] == 4

    def test_has_cells(self):
        nb = _transpile(_MINIMAL_SPL)
        assert len(nb["cells"]) >= 3

    def test_first_cell_is_markdown(self):
        nb = _transpile(_MINIMAL_SPL)
        assert nb["cells"][0]["cell_type"] == "markdown"

    def test_second_cell_is_code(self):
        nb = _transpile(_MINIMAL_SPL)
        assert nb["cells"][1]["cell_type"] == "code"

    def test_kernelspec_present(self):
        nb = _transpile(_MINIMAL_SPL)
        assert "kernelspec" in nb["metadata"]
        assert nb["metadata"]["kernelspec"]["language"] == "python"

    def test_splc_metadata_tag(self):
        nb = _transpile(_MINIMAL_SPL)
        assert nb["metadata"].get("splc", {}).get("target") == "python/linalg"

    def test_source_lines_format(self):
        """Each cell's source is a list of strings (nbformat requirement)."""
        nb = _transpile(_MINIMAL_SPL)
        for cell in nb["cells"]:
            assert isinstance(cell["source"], list)
            for line in cell["source"]:
                assert isinstance(line, str)


# ---------------------------------------------------------------------------
# Header cell
# ---------------------------------------------------------------------------

class TestHeaderCell:
    def test_header_contains_workflow_name(self):
        nb = _transpile(_MINIMAL_SPL)
        header = _cell_src(nb["cells"][0])
        assert "Query Graph" in header or "query_graph" in header.lower()

    def test_header_mentions_linalg_target(self):
        nb = _transpile(_MINIMAL_SPL)
        header = _cell_src(nb["cells"][0])
        assert "python/linalg" in header

    def test_header_lists_inputs(self):
        nb = _transpile(_MINIMAL_SPL)
        header = _cell_src(nb["cells"][0])
        assert "target" in header
        assert "payoff_weight" in header


# ---------------------------------------------------------------------------
# Setup cell
# ---------------------------------------------------------------------------

class TestSetupCell:
    def test_imports_linalg_graph(self):
        nb = _transpile(_MINIMAL_SPL)
        setup = _cell_src(nb["cells"][1])
        assert "import linalg_graph" in setup

    def test_defines_llm_call_helper(self):
        nb = _transpile(_MINIMAL_SPL)
        setup = _cell_src(nb["cells"][1])
        assert "def _llm_call" in setup

    def test_defines_verify_math_helper(self):
        nb = _transpile(_MINIMAL_SPL)
        setup = _cell_src(nb["cells"][1])
        assert "def _verify_math" in setup

    def test_parameter_defaults_in_setup(self):
        nb = _transpile(_MINIMAL_SPL)
        setup = _cell_src(nb["cells"][1])
        assert "target" in setup
        assert "payoff_weight" in setup

    def test_graph_build_in_setup(self):
        nb = _transpile(_MINIMAL_SPL)
        setup = _cell_src(nb["cells"][1])
        # alias is `dg` (domain graph) post-generalization — see
        # transpiler_domain_graph.py's _SETUP_TEMPLATE; behavior is identical,
        # only the import alias changed from the linalg-only `lg`.
        assert "graph = dg.build()" in setup

    def test_primitives_in_setup(self):
        nb = _transpile(_MINIMAL_SPL)
        setup = _cell_src(nb["cells"][1])
        assert "primitives = dg.both_radical_primitives()" in setup


# ---------------------------------------------------------------------------
# SOLVE cells
# ---------------------------------------------------------------------------

class TestSolveCells:
    def test_solve_cells_present(self):
        nb = _transpile(_MINIMAL_SPL)
        solve_cells = _find_cells_with(nb, "solve")
        assert len(solve_cells) == 2  # @needed and @order

    def test_solve_needed_cell_content(self):
        nb = _transpile(_MINIMAL_SPL)
        solve_cells = _find_cells_with(nb, "solve")
        needed_cell = next(c for c in solve_cells if "needed" in _cell_src(c))
        src = _cell_src(needed_cell)
        # bare name (from linalg_graph import ancestors) — no lg. prefix
        assert "needed = ancestors(graph, target)" in src
        assert "@@" not in src   # all @@markers@@ substituted

    def test_solve_order_cell_content(self):
        nb = _transpile(_MINIMAL_SPL)
        solve_cells = _find_cells_with(nb, "solve")
        order_cell = next(c for c in solve_cells if "order" in _cell_src(c) and "productivity" in _cell_src(c))
        src = _cell_src(order_cell)
        assert "order = productivity_order" in src
        assert "weight=payoff_weight" in src
        assert "@@" not in src

    def test_solve_cell_prints_result(self):
        nb = _transpile(_MINIMAL_SPL)
        for c in _find_cells_with(nb, "solve"):
            src = _cell_src(c)
            assert "print(" in src

    def test_solve_spl_comment_present(self):
        nb = _transpile(_MINIMAL_SPL)
        for c in _find_cells_with(nb, "solve"):
            src = _cell_src(c)
            assert "# SPL: SOLVE" in src


# ---------------------------------------------------------------------------
# ASSERT cells
# ---------------------------------------------------------------------------

class TestAssertCells:
    def test_assert_cell_present(self):
        nb = _transpile(_MINIMAL_SPL)
        assert_cells = _find_cells_with(nb, "assert")
        assert len(assert_cells) == 1

    def test_assert_cell_uses_bool(self):
        nb = _transpile(_MINIMAL_SPL)
        src = _cell_src(_find_cells_with(nb, "assert")[0])
        assert "_assert_result = bool(" in src

    def test_assert_cell_raises_on_failure(self):
        nb = _transpile(_MINIMAL_SPL)
        src = _cell_src(_find_cells_with(nb, "assert")[0])
        assert "AssertionError" in src

    def test_assert_cell_prints_pass(self):
        nb = _transpile(_MINIMAL_SPL)
        src = _cell_src(_find_cells_with(nb, "assert")[0])
        assert "✓ ASSERT" in src

    def test_assert_no_markers(self):
        nb = _transpile(_MINIMAL_SPL)
        src = _cell_src(_find_cells_with(nb, "assert")[0])
        assert "@@" not in src

    def test_assert_spl_comment(self):
        nb = _transpile(_MINIMAL_SPL)
        src = _cell_src(_find_cells_with(nb, "assert")[0])
        assert "# SPL: ASSERT" in src

    def test_assert_with_otherwise_body(self):
        """ASSERT with OTHERWISE body emits the otherwise code block."""
        spl = """\
WORKFLOW otherwise_test
    INPUT: @domain TEXT
    OUTPUT: @result TEXT
DO
    ASSERT minimal(@primitives)
        OTHERWISE LOGGING "Assertion failed"
    COMMIT @domain
END
"""
        nb = _transpile(spl)
        assert_cells = _find_cells_with(nb, "assert")
        assert len(assert_cells) == 1
        src = _cell_src(assert_cells[0])
        # otherwise_body is present — no AssertionError raised; prints feedback instead
        assert "ASSERT failed" in src or "executing OTHERWISE" in src


# ---------------------------------------------------------------------------
# GENERATE cells
# ---------------------------------------------------------------------------

class TestGenerateCells:
    def test_generate_cell_present(self):
        nb = _transpile(_GENERATE_SPL)
        gen_cells = _find_cells_with(nb, "generate")
        assert len(gen_cells) >= 1

    def test_generate_calls_llm_helper(self):
        nb = _transpile(_GENERATE_SPL)
        src = _cell_src(_find_cells_with(nb, "generate")[0])
        assert "_llm_call(" in src

    def test_generate_assigns_target_variable(self):
        nb = _transpile(_GENERATE_SPL)
        src = _cell_src(_find_cells_with(nb, "generate")[0])
        assert "primitives = _llm_call(" in src

    def test_generate_spl_comment(self):
        nb = _transpile(_GENERATE_SPL)
        src = _cell_src(_find_cells_with(nb, "generate")[0])
        assert "# SPL: GENERATE" in src


# ---------------------------------------------------------------------------
# CALL cells
# ---------------------------------------------------------------------------

class TestCallCells:
    def test_call_cell_present(self):
        nb = _transpile(_GENERATE_SPL)
        call_cells = _find_cells_with(nb, "call")
        assert len(call_cells) >= 1

    def test_verify_math_routed_to_helper(self):
        nb = _transpile(_GENERATE_SPL)
        call_cells = _find_cells_with(nb, "call")
        verify_cell = next(c for c in call_cells if "verify_math" in _cell_src(c))
        src = _cell_src(verify_cell)
        assert "_verify_math(" in src

    def test_call_assigns_target(self):
        nb = _transpile(_GENERATE_SPL)
        call_cells = _find_cells_with(nb, "call")
        src = _cell_src(call_cells[0])
        assert "check = _verify_math(" in src

    def test_call_spl_comment(self):
        nb = _transpile(_GENERATE_SPL)
        src = _cell_src(_find_cells_with(nb, "call")[0])
        assert "# SPL: CALL" in src


# ---------------------------------------------------------------------------
# EVALUATE cells
# ---------------------------------------------------------------------------

class TestEvaluateCells:
    def test_evaluate_cell_present(self):
        nb = _transpile(_GENERATE_SPL)
        eval_cells = _find_cells_with(nb, "evaluate")
        assert len(eval_cells) == 1

    def test_evaluate_uses_if(self):
        nb = _transpile(_GENERATE_SPL)
        src = _cell_src(_find_cells_with(nb, "evaluate")[0])
        assert "if " in src

    def test_evaluate_when_fail_condition(self):
        nb = _transpile(_GENERATE_SPL)
        src = _cell_src(_find_cells_with(nb, "evaluate")[0])
        assert "fail" in src.lower()


# ---------------------------------------------------------------------------
# LOGGING cells
# ---------------------------------------------------------------------------

class TestLoggingCells:
    def test_logging_cell_present(self):
        nb = _transpile(_MINIMAL_SPL)
        log_cells = _find_cells_with(nb, "logging")
        assert len(log_cells) == 1

    def test_logging_uses_print(self):
        nb = _transpile(_MINIMAL_SPL)
        src = _cell_src(_find_cells_with(nb, "logging")[0])
        assert "print(" in src


# ---------------------------------------------------------------------------
# COMMIT cells
# ---------------------------------------------------------------------------

class TestCommitCells:
    def test_commit_cell_present(self):
        nb = _transpile(_MINIMAL_SPL)
        commit_cells = _find_cells_with(nb, "commit")
        assert len(commit_cells) == 1

    def test_commit_writes_file(self):
        nb = _transpile(_MINIMAL_SPL)
        src = _cell_src(_find_cells_with(nb, "commit")[0])
        assert "write_text" in src or "json.dumps" in src

    def test_commit_prints_confirmation(self):
        nb = _transpile(_MINIMAL_SPL)
        src = _cell_src(_find_cells_with(nb, "commit")[0])
        assert "Committed" in src


# ---------------------------------------------------------------------------
# CREATE FUNCTION → prompts cell
# ---------------------------------------------------------------------------

class TestPromptsCells:
    def test_prompts_cell_present_when_functions_defined(self):
        nb = _transpile(_FUNCTION_SPL)
        # There should be a code cell with _PROMPT constant
        code_srcs = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
        assert any("PROPOSE_BASIS_PROMPT" in s for s in code_srcs)

    def test_generate_uses_prompt_constant(self):
        nb = _transpile(_FUNCTION_SPL)
        gen_cells = _find_cells_with(nb, "generate")
        assert len(gen_cells) >= 1
        src = _cell_src(gen_cells[0])
        assert "PROPOSE_BASIS_PROMPT" in src


# ---------------------------------------------------------------------------
# Round-trip smoke: parse → transpile → valid JSON → correct structure
# ---------------------------------------------------------------------------

class TestRoundTrip:
    def test_full_workflow_all_constructs(self):
        spl = """\
CREATE FUNCTION write_section(concept TEXT, graph TEXT)
RETURN TEXT
AS $$
Write a micro-textbook section for the concept: {concept}.
$$

WORKFLOW build_textbook
    INPUT:  @target TEXT, @payoff_weight FLOAT
    OUTPUT: @textbook TEXT
DO
    ASSERT acyclic(@graph)
    SOLVE @needed SET := ancestors(@graph, @target)
    SOLVE @order LIST := productivity_order(restrict(@graph, @needed), weight=@payoff_weight)
    LOGGING "Building sections for: " + @order
    GENERATE write_section(@target, @order) INTO @section
    CALL verify_math(@section) INTO @check
    EVALUATE @check
        WHEN contains('fail') THEN
            GENERATE write_section(@target, @check) INTO @section
    END
    COMMIT @textbook
END
"""
        nb = _transpile(spl, "build_textbook")
        assert nb["nbformat"] == 4
        assert len(nb["cells"]) >= 6  # header + setup + prompts + 5+ statement cells
        # No @@markers@@ should survive into the final notebook
        full_src = " ".join("".join(c["source"]) for c in nb["cells"])
        assert "@@" not in full_src

    def test_output_is_valid_nbformat(self):
        """The generated notebook satisfies basic nbformat 4 structural requirements."""
        nb = _transpile(_MINIMAL_SPL)
        assert nb["nbformat"] == 4
        assert nb["nbformat_minor"] >= 0
        assert "metadata" in nb
        assert "cells" in nb
        for cell in nb["cells"]:
            assert "cell_type" in cell
            assert cell["cell_type"] in ("code", "markdown", "raw")
            assert "source" in cell
            assert isinstance(cell["source"], list)
