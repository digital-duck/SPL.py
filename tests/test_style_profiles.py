"""Tests for style_profiles.py and style integration in the SPL recipes.

Covers:
  - style_profiles: all 5 profiles exist, correct fields, get_style_profile(),
    style_instruction(), available_styles()
  - build_concept_book.spl: @style INPUT, @style_guide SOLVE cell, all
    GENERATE calls pass style_guide to format()
  - answer_on_demand.spl: same; resolve_target is style-agnostic
  - Cross-style: different styles produce different style_guide strings but
    identical notebook structure (same cell count, same tags)
  - Transpiler setup cell: imports style_profiles symbols
"""

from __future__ import annotations

import json
import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..",
                                "cookbook", "71_linalg_concept_book"))

from style_profiles import (
    STYLE_PROFILES,
    get_style_profile,
    style_instruction,
    available_styles,
)
from spl.lexer import Lexer
from spl3.parser import SPL3Parser
from spl3.splc.transpiler_linalg import LinalgTranspiler
from pathlib import Path

_COOKBOOK = Path(__file__).parent.parent / "cookbook" / "71_linalg_concept_book"
_STYLES = ["textbook", "feynman", "flashcard", "instructor", "research"]


def _compile(recipe: str) -> dict:
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


def _all_src(nb: dict) -> str:
    return " ".join(_cell_src(c) for c in nb["cells"])


# ---------------------------------------------------------------------------
# A. style_profiles module
# ---------------------------------------------------------------------------

class TestStyleProfilesModule:
    def test_five_profiles_defined(self):
        assert len(STYLE_PROFILES) == 5

    def test_required_profiles_present(self):
        for name in _STYLES:
            assert name in STYLE_PROFILES, f"Missing profile: {name}"

    def test_each_profile_has_required_fields(self):
        required = {"label", "tone", "depth", "audience", "length", "structure"}
        for name, profile in STYLE_PROFILES.items():
            missing = required - set(profile.keys())
            assert not missing, f"Profile '{name}' missing fields: {missing}"

    def test_all_fields_are_non_empty_strings(self):
        for name, profile in STYLE_PROFILES.items():
            for field, value in profile.items():
                assert isinstance(value, str) and value.strip(), \
                    f"Profile '{name}' field '{field}' is empty or not a string"

    def test_get_style_profile_returns_dict(self):
        for name in _STYLES:
            p = get_style_profile(name)
            assert isinstance(p, dict)
            assert p["label"]

    def test_get_style_profile_raises_on_unknown(self):
        with pytest.raises(ValueError, match="Unknown style"):
            get_style_profile("nonexistent_style")

    def test_style_instruction_returns_string(self):
        for name in _STYLES:
            instr = style_instruction(name)
            assert isinstance(instr, str)
            assert len(instr) > 50

    def test_style_instruction_contains_style_guide_header(self):
        for name in _STYLES:
            instr = style_instruction(name)
            assert "STYLE GUIDE" in instr

    def test_style_instruction_contains_all_fields(self):
        for name in _STYLES:
            instr = style_instruction(name)
            p = get_style_profile(name)
            # Each field value should appear in the instruction
            assert p["tone"] in instr
            assert p["audience"] in instr
            assert p["structure"] in instr

    def test_styles_produce_different_instructions(self):
        instructions = [style_instruction(s) for s in _STYLES]
        # All instructions should be distinct
        assert len(set(instructions)) == len(_STYLES)

    def test_available_styles_returns_all_five(self):
        styles = available_styles()
        assert set(styles) == set(_STYLES)

    def test_available_styles_returns_list(self):
        assert isinstance(available_styles(), list)

    def test_feynman_tone_mentions_intuition(self):
        p = get_style_profile("feynman")
        assert "intuiti" in p["tone"].lower() or "story" in p["tone"].lower()

    def test_flashcard_length_is_short(self):
        p = get_style_profile("flashcard")
        assert "50" in p["length"] or "100" in p["length"]

    def test_textbook_audience_mentions_university(self):
        p = get_style_profile("textbook")
        assert "university" in p["audience"].lower() or "student" in p["audience"].lower()


# ---------------------------------------------------------------------------
# B. build_concept_book.spl — style integration
# ---------------------------------------------------------------------------

class TestBuildMicroTextbookStyle:
    def setup_method(self):
        self.nb = _compile("build_concept_book")
        self.all_src = _all_src(self.nb)

    def test_style_input_declared(self):
        src = (_COOKBOOK / "build_concept_book.spl").read_text()
        assert "@style TEXT" in src

    def test_style_guide_solve_cell_present(self):
        solve_cells = _find_cells(self.nb, "solve")
        srcs = [_cell_src(c) for c in solve_cells]
        assert any("style_instruction" in s and "style_guide" in s for s in srcs)

    def test_style_guide_solve_calls_style_instruction(self):
        solve_cells = _find_cells(self.nb, "solve")
        srcs = [_cell_src(c) for c in solve_cells]
        matching = [s for s in srcs if "style_guide = style_instruction(style)" in s]
        assert len(matching) == 1

    def test_write_section_prompt_includes_style_guide(self):
        assert "style_guide=style_guide" in self.all_src

    def test_all_generate_calls_pass_style_guide(self):
        import re
        # Find all .format( calls and verify style_guide is present
        format_calls = re.findall(r"\.format\(([^)]+)\)", self.all_src)
        content_calls = [c for c in format_calls if "style_guide" not in c
                         and any(k in c for k in ["section=", "concept=", "target="])]
        assert content_calls == [], \
            f"These format() calls are missing style_guide: {content_calls}"

    def test_refine_section_includes_style_guide(self):
        assert "REFINE_SECTION_PROMPT.format" in self.all_src
        import re
        refine_calls = re.findall(r"REFINE_SECTION_PROMPT\.format\(([^)]+)\)", self.all_src)
        for call in refine_calls:
            assert "style_guide" in call, f"refine call missing style_guide: {call}"

    def test_write_payoff_includes_style_guide(self):
        import re
        payoff_calls = re.findall(r"WRITE_PAYOFF_PROMPT\.format\(([^)]+)\)", self.all_src)
        assert payoff_calls, "No WRITE_PAYOFF_PROMPT.format call found"
        for call in payoff_calls:
            assert "style_guide" in call

    def test_setup_cell_imports_style_profiles(self):
        setup_src = _cell_src(self.nb["cells"][1])
        assert "style_profiles" in setup_src or "style_instruction" in setup_src

    def test_logging_mentions_style(self):
        log_cells = _find_cells(self.nb, "logging")
        srcs = [_cell_src(c) for c in log_cells]
        assert any("style" in s.lower() for s in srcs)


class TestBuildMicroTextbookStyleProfiles:
    """Verify different style inputs produce distinct notebooks with same structure."""

    def _compile_with_style_param(self, recipe: str, style: str) -> dict:
        """Compile recipe; the default param value is just for test inspection."""
        # The style value is baked into the SPL default — we just compile normally
        # and check that the parameter default is 'textbook' (the spl default).
        # Style is a runtime parameter, so the notebook structure is identical
        # across styles — only the default value differs.
        return _compile(recipe)

    def test_notebook_structure_is_style_invariant(self):
        """Compilation output has same cell count regardless of style input.
        Style is a runtime parameter — the structure is fixed at compile time."""
        nb = _compile("build_concept_book")
        # Cell count is deterministic (25 since the timing instrumentation —
        # SOLVE @t_*_start / @*_elapsed + LOGGING [timing] — was added)
        assert len(nb["cells"]) == 25

    def test_default_style_is_textbook(self):
        src = (_COOKBOOK / "build_concept_book.spl").read_text()
        assert "'textbook'" in src or '"textbook"' in src

    def test_setup_cell_has_style_param_default(self):
        nb = _compile("build_concept_book")
        setup_src = _cell_src(nb["cells"][1])
        # Params are now config-driven (env → ~/.spl/config → default) rather
        # than hardcoded literals; 'textbook' remains the default.
        assert "style = _spl_config('STYLE', 'textbook')" in setup_src


# ---------------------------------------------------------------------------
# C. answer_on_demand.spl — style integration
# ---------------------------------------------------------------------------

class TestAnswerOnDemandStyle:
    def setup_method(self):
        self.nb = _compile("answer_on_demand")
        self.all_src = _all_src(self.nb)

    def test_style_input_declared(self):
        src = (_COOKBOOK / "answer_on_demand.spl").read_text()
        assert "@style TEXT" in src

    def test_style_guide_solve_cell_present(self):
        solve_cells = _find_cells(self.nb, "solve")
        srcs = [_cell_src(c) for c in solve_cells]
        assert any("style_guide = style_instruction(style)" in s for s in srcs)

    def test_resolve_target_is_style_agnostic(self):
        """resolve_target should NOT receive style_guide — it finds a concept name."""
        import re
        resolve_calls = re.findall(r"RESOLVE_TARGET_PROMPT\.format\(([^)]+)\)", self.all_src)
        assert resolve_calls, "No RESOLVE_TARGET_PROMPT.format call found"
        for call in resolve_calls:
            assert "style_guide" not in call, \
                f"resolve_target should not receive style_guide: {call}"

    def test_write_section_includes_style_guide(self):
        import re
        ws_calls = re.findall(r"WRITE_SECTION_PROMPT\.format\(([^)]+)\)", self.all_src)
        assert ws_calls
        for call in ws_calls:
            assert "style_guide" in call

    def test_refine_section_includes_style_guide(self):
        import re
        ref_calls = re.findall(r"REFINE_SECTION_PROMPT\.format\(([^)]+)\)", self.all_src)
        for call in ref_calls:
            assert "style_guide" in call

    def test_default_style_is_textbook(self):
        src = (_COOKBOOK / "answer_on_demand.spl").read_text()
        assert "'textbook'" in src or '"textbook"' in src

    def test_setup_cell_imports_style_profiles(self):
        setup_src = _cell_src(self.nb["cells"][1])
        assert "style_instruction" in setup_src


# ---------------------------------------------------------------------------
# D. Transpiler — style_profiles import in setup cell
# ---------------------------------------------------------------------------

class TestTranspilerStyleImport:
    def _transpile(self, spl_src: str) -> dict:
        tokens = Lexer(spl_src).tokenize()
        program = SPL3Parser(tokens).parse()
        nb_json = LinalgTranspiler("test_style").transpile(program)
        return json.loads(nb_json)

    def test_setup_cell_imports_style_instruction(self):
        spl = """\
WORKFLOW test
    INPUT: @style TEXT
    OUTPUT: @out TEXT
DO
    SOLVE @style_guide TEXT := style_instruction(@style)
    COMMIT @out
END
"""
        nb = self._transpile(spl)
        setup_src = _cell_src(nb["cells"][1])
        assert "style_instruction" in setup_src

    def test_solve_style_instruction_compiles_correctly(self):
        spl = """\
WORKFLOW test
    INPUT: @style TEXT
    OUTPUT: @out TEXT
DO
    SOLVE @style_guide TEXT := style_instruction(@style)
    COMMIT @out
END
"""
        nb = self._transpile(spl)
        solve_cells = _find_cells(nb, "solve")
        src = _cell_src(solve_cells[0])
        assert "style_guide = style_instruction(style)" in src

    def test_style_guide_passed_to_generate_format(self):
        spl = """\
CREATE FUNCTION write_section(concept TEXT, style_guide TEXT)
RETURN TEXT
AS $$
{style_guide}
Write about: {concept}
$$;

WORKFLOW test
    INPUT: @concept TEXT, @style TEXT
    OUTPUT: @section TEXT
DO
    SOLVE @style_guide TEXT := style_instruction(@style)
    GENERATE write_section(@concept, @style_guide) INTO @section
    COMMIT @section
END
"""
        nb = self._transpile(spl)
        gen_cells = _find_cells(nb, "generate")
        src = _cell_src(gen_cells[0])
        assert "style_guide=style_guide" in src
