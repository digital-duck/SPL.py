"""Unit tests for spl3.judge — Phase 1 + Phase 2."""

from __future__ import annotations
import asyncio
import json
import pytest

from spl3.judge.types import Rubric, JudgeResult, PanelResult
from spl3.judge.prompt import build_judge_prompt
from spl3.judge.engine import _parse_verdict, run_panel
from spl3.judge.report import render_judge_report
from spl3.judge.rubrics import load_rubric, list_rubrics
from spl3.judge.aggregators import majority_vote, confidence_weighted, unanimous, aggregate


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def clarity_rubric():
    return load_rubric("clarity")


@pytest.fixture
def correctness_rubric():
    return load_rubric("correctness")


@pytest.fixture
def spl_rubric():
    return load_rubric("spl-compliance")


@pytest.fixture
def simple_rubric():
    return Rubric(
        name="test",
        criteria=["quality", "relevance"],
        pass_threshold=7.0,
    )


@pytest.fixture
def pass_result(simple_rubric):
    return JudgeResult(
        verdict="PASS",
        score=8.5,
        confidence="HIGH",
        reasoning="The content is clear and relevant.",
        feedback="",
        criteria_scores={"quality": 9.0, "relevance": 8.0},
        model="test-model",
        adapter="echo",
        rubric="test",
    )


@pytest.fixture
def fail_result(simple_rubric):
    return JudgeResult(
        verdict="FAIL",
        score=4.2,
        confidence="MEDIUM",
        reasoning="The content lacks clarity.",
        feedback="- Add more detail\n- Fix logical gaps",
        criteria_scores={"quality": 4.0, "relevance": 4.4},
        model="test-model",
        adapter="echo",
        rubric="test",
    )


# ── Rubric loading ────────────────────────────────────────────────────────────

class TestRubricLoading:
    def test_load_clarity(self, clarity_rubric):
        assert clarity_rubric.name == "clarity"
        assert "prose_clarity" in clarity_rubric.criteria
        assert clarity_rubric.pass_threshold == 7.0

    def test_load_correctness(self, correctness_rubric):
        assert correctness_rubric.name == "correctness"
        assert "factual_accuracy" in correctness_rubric.criteria

    def test_load_spl_compliance(self, spl_rubric):
        assert spl_rubric.name == "spl-compliance"
        assert "generate_signatures" in spl_rubric.criteria
        assert spl_rubric.pass_threshold == 7.0

    def test_load_ai_review(self):
        r = load_rubric("ai_review")
        assert r.name == "ai_review"
        assert "helpfulness" in r.criteria

    def test_list_rubrics(self):
        rubrics = list_rubrics()
        assert "clarity" in rubrics
        assert "correctness" in rubrics
        assert "spl_compliance" in rubrics
        assert "ai_review" in rubrics

    def test_unknown_rubric_raises(self):
        with pytest.raises(ValueError, match="not found"):
            load_rubric("nonexistent_rubric_xyz")

    def test_custom_rubric_from_path(self, tmp_path):
        yaml_content = """
name: custom
criteria:
  - accuracy
  - brevity
pass_threshold: 6.5
"""
        p = tmp_path / "custom.yaml"
        p.write_text(yaml_content)
        r = load_rubric(str(p))
        assert r.name == "custom"
        assert r.criteria == ["accuracy", "brevity"]
        assert r.pass_threshold == 6.5


# ── Rubric weight helpers ─────────────────────────────────────────────────────

class TestRubricWeights:
    def test_equal_weight_default(self, simple_rubric):
        assert simple_rubric.effective_weight("quality") == pytest.approx(0.5)
        assert simple_rubric.effective_weight("relevance") == pytest.approx(0.5)

    def test_explicit_weights(self, spl_rubric):
        w = spl_rubric.effective_weight("generate_signatures")
        assert w == pytest.approx(0.30)
        total = sum(spl_rubric.effective_weight(c) for c in spl_rubric.criteria)
        assert total == pytest.approx(1.0, abs=1e-9)


# ── Prompt building ───────────────────────────────────────────────────────────

class TestBuildJudgePrompt:
    def test_prompt_contains_criteria(self, simple_rubric):
        prompt = build_judge_prompt("some content", simple_rubric)
        assert "quality" in prompt
        assert "relevance" in prompt

    def test_prompt_contains_content(self, simple_rubric):
        prompt = build_judge_prompt("hello world", simple_rubric)
        assert "hello world" in prompt

    def test_prompt_contains_threshold(self, simple_rubric):
        prompt = build_judge_prompt("content", simple_rubric)
        assert "7.0" in prompt

    def test_prompt_contains_json_block(self, simple_rubric):
        prompt = build_judge_prompt("content", simple_rubric)
        assert "```json" in prompt
        assert '"verdict"' in prompt

    def test_prompt_includes_custom_template(self):
        r = Rubric(
            name="custom",
            criteria=["a"],
            pass_threshold=5.0,
            prompt_template="Evaluate code quality specifically.",
        )
        prompt = build_judge_prompt("code here", r)
        assert "Evaluate code quality specifically." in prompt

    def test_spl_prompt_has_domain_context(self, spl_rubric):
        prompt = build_judge_prompt("WORKFLOW foo ...", spl_rubric)
        assert "GENERATE" in prompt or "SPL" in prompt


# ── Verdict parsing ───────────────────────────────────────────────────────────

_GOOD_JSON = """\
Some reasoning text here.

```json
{
  "verdict": "PASS",
  "score": 8.5,
  "confidence": "HIGH",
  "criteria_scores": {"quality": 9.0, "relevance": 8.0},
  "reasoning": "Well written.",
  "feedback": ""
}
```
"""

_FAIL_JSON = """\
```json
{
  "verdict": "FAIL",
  "score": 4.0,
  "confidence": "MEDIUM",
  "criteria_scores": {"quality": 4.0, "relevance": 4.0},
  "reasoning": "Lacks detail.",
  "feedback": "- Add examples"
}
```
"""

_ESCALATE_JSON = """\
```json
{
  "verdict": "ESCALATE",
  "score": 5.5,
  "confidence": "LOW",
  "criteria_scores": {"quality": 5.0, "relevance": 6.0},
  "reasoning": "Ambiguous.",
  "feedback": "Human review needed."
}
```
"""

_PROSE_ONLY = "The content looks good. PASS. Overall score: 8.0. HIGH confidence."

_BAD_JSON = "```json\n{invalid json here\n```"


class TestParseVerdict:
    def test_parse_pass(self, simple_rubric):
        r = _parse_verdict(_GOOD_JSON, simple_rubric, "echo", "test")
        assert r.verdict == "PASS"
        assert r.score == pytest.approx(8.5)
        assert r.confidence == "HIGH"
        assert r.criteria_scores["quality"] == pytest.approx(9.0)

    def test_parse_fail(self, simple_rubric):
        r = _parse_verdict(_FAIL_JSON, simple_rubric, "echo", "test")
        assert r.verdict == "FAIL"
        assert r.score == pytest.approx(4.0)
        assert r.feedback == "- Add examples"

    def test_parse_escalate(self, simple_rubric):
        r = _parse_verdict(_ESCALATE_JSON, simple_rubric, "echo", "test")
        assert r.verdict == "ESCALATE"
        assert r.confidence == "LOW"

    def test_prose_fallback(self, simple_rubric):
        r = _parse_verdict(_PROSE_ONLY, simple_rubric, "echo", "test")
        assert r.verdict == "PASS"
        assert r.score == pytest.approx(8.0)
        assert r.confidence == "HIGH"

    def test_bad_json_falls_back_to_prose(self, simple_rubric):
        r = _parse_verdict(_BAD_JSON, simple_rubric, "echo", "test")
        # No PASS/FAIL/ESCALATE in the prose → defaults to ESCALATE
        assert r.verdict in ("PASS", "FAIL", "ESCALATE")

    def test_unknown_verdict_normalised(self, simple_rubric):
        raw = '```json\n{"verdict": "UNKNOWN", "score": 5.0, "confidence": "HIGH", ' \
              '"criteria_scores": {}, "reasoning": "", "feedback": ""}\n```'
        r = _parse_verdict(raw, simple_rubric, "echo", "test")
        assert r.verdict == "ESCALATE"

    def test_unknown_confidence_normalised(self, simple_rubric):
        raw = '```json\n{"verdict": "PASS", "score": 8.0, "confidence": "VERY_HIGH", ' \
              '"criteria_scores": {}, "reasoning": "", "feedback": ""}\n```'
        r = _parse_verdict(raw, simple_rubric, "echo", "test")
        assert r.confidence == "LOW"

    def test_adapter_and_model_propagated(self, simple_rubric):
        r = _parse_verdict(_GOOD_JSON, simple_rubric, "claude_cli", "claude-opus-4-6")
        assert r.adapter == "claude_cli"
        assert r.model == "claude-opus-4-6"
        assert r.rubric == "test"


# ── Report rendering ──────────────────────────────────────────────────────────

class TestRenderJudgeReport:
    def test_json_format(self, pass_result):
        report = render_judge_report(pass_result, "json")
        data = json.loads(report)
        assert data["verdict"] == "PASS"
        assert data["score"] == pytest.approx(8.5)
        assert "criteria_scores" in data

    def test_text_format(self, pass_result):
        report = render_judge_report(pass_result, "text")
        assert "PASS" in report
        assert "8.5" in report
        assert "HIGH" in report

    def test_markdown_format(self, pass_result):
        report = render_judge_report(pass_result, "markdown")
        assert "# Judge Report" in report
        assert "PASS" in report
        assert "| quality |" in report

    def test_markdown_fail_shows_feedback(self, fail_result):
        report = render_judge_report(fail_result, "markdown")
        assert "FAIL" in report
        assert "Feedback" in report
        assert "Add more detail" in report

    def test_swap_consistent_shown(self, pass_result):
        pass_result.swap_consistent = True
        report = render_judge_report(pass_result, "markdown")
        assert "Swap-consistent" in report

    def test_json_swap_consistent_none(self, pass_result):
        data = json.loads(render_judge_report(pass_result, "json"))
        assert data["swap_consistent"] is None

    def test_default_format_is_markdown(self, pass_result):
        report = render_judge_report(pass_result)
        assert "# Judge Report" in report


# ── CLI smoke tests ───────────────────────────────────────────────────────────

class TestJudgeCLI:
    def test_judge_help(self):
        from click.testing import CliRunner
        from spl3.cli import main
        runner = CliRunner()
        result = runner.invoke(main, ["judge", "--help"])
        assert result.exit_code == 0
        assert "--criteria" in result.output
        assert "--llm" in result.output
        assert "--swap-check" in result.output

    def test_judge_prompt_debug(self, tmp_path, clarity_rubric):
        from click.testing import CliRunner
        from spl3.cli import main
        f = tmp_path / "input.md"
        f.write_text("This is a test document.")
        runner = CliRunner()
        result = runner.invoke(main, [
            "judge", str(f),
            "--criteria", "clarity",
            "--adapter", "echo",
            "--prompt",
        ])
        assert result.exit_code == 0
        assert "JUDGE PROMPT" in result.output
        assert "prose_clarity" in result.output

    def test_judge_missing_file(self):
        from click.testing import CliRunner
        from spl3.cli import main
        runner = CliRunner()
        result = runner.invoke(main, ["judge", "nonexistent_file.md", "--adapter", "echo"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "Error" in result.output

    def test_judge_unknown_rubric(self, tmp_path):
        from click.testing import CliRunner
        from spl3.cli import main
        f = tmp_path / "input.md"
        f.write_text("content")
        runner = CliRunner()
        result = runner.invoke(main, [
            "judge", str(f),
            "--criteria", "nonexistent_rubric_xyz",
            "--adapter", "echo",
        ])
        assert result.exit_code != 0

    def test_judge_panel_two_llm_specs(self, tmp_path):
        from click.testing import CliRunner
        from spl3.cli import main
        f = tmp_path / "input.md"
        f.write_text("content")
        runner = CliRunner()
        result = runner.invoke(main, [
            "judge", str(f),
            "--llm", "echo:model-a",
            "--llm", "echo:model-b",
            "--prompt",  # just show the prompt so no LLM call needed
        ])
        # --prompt only shows single-judge prompt; panel + prompt exits cleanly
        assert result.exit_code == 0

    def test_resolve_llm_prefers_llm_over_adapter(self):
        from spl3.cli import _resolve_llm
        pairs = _resolve_llm(("claude_cli:claude-opus-4-6",), "ollama", "llama3")
        assert pairs == [("claude_cli", "claude-opus-4-6")]

    def test_resolve_llm_openrouter_model_slash(self):
        from spl3.cli import _resolve_llm
        pairs = _resolve_llm(("openrouter:google/gemini-2.5-pro",), "ollama", None)
        assert pairs == [("openrouter", "google/gemini-2.5-pro")]

    def test_resolve_llm_fallback_to_adapter(self):
        from spl3.cli import _resolve_llm
        pairs = _resolve_llm((), "ollama", "llama3")
        assert pairs == [("ollama", "llama3")]

    def test_resolve_llm_no_model(self):
        from spl3.cli import _resolve_llm
        pairs = _resolve_llm(("echo",), "ollama", None)
        assert pairs == [("echo", None)]

    def test_cache_key_pass_promotes(self, tmp_path):
        """--cache-key + PASS verdict calls cache.promote with 'ai_reviewed'."""
        from unittest.mock import patch, MagicMock
        from click.testing import CliRunner
        from spl3.cli import main
        from spl3.judge.types import JudgeResult

        f = tmp_path / "section.md"
        f.write_text("A vector space is a set with two operations.")

        pass_result = JudgeResult(
            verdict="PASS", score=8.5, confidence="HIGH",
            reasoning="Good.", feedback="None.", criteria_scores={},
            model="llama3", adapter="ollama", rubric="correctness",
        )
        mock_cache = MagicMock()
        runner = CliRunner()
        with patch("spl3.judge.engine.run_judge", return_value=pass_result), \
             patch("spl3.cache.get_content_cache", return_value=mock_cache):
            result = runner.invoke(main, [
                "judge", str(f),
                "--criteria", "correctness",
                "--adapter", "ollama",
                "--cache-key", "deadbeef1234",
            ])
        assert result.exit_code == 0
        mock_cache.promote.assert_called_once()
        call_args = mock_cache.promote.call_args
        assert call_args[0][0] == "deadbeef1234"
        assert call_args[0][1] == "ai_reviewed"

    def test_cache_key_fail_no_promote(self, tmp_path):
        """--cache-key + FAIL verdict does NOT call cache.promote."""
        from unittest.mock import patch, MagicMock
        from click.testing import CliRunner
        from spl3.cli import main
        from spl3.judge.types import JudgeResult

        f = tmp_path / "section.md"
        f.write_text("Incorrect content.")

        fail_result = JudgeResult(
            verdict="FAIL", score=3.0, confidence="HIGH",
            reasoning="Poor.", feedback="Fix it.", criteria_scores={},
            model="llama3", adapter="ollama", rubric="correctness",
        )
        mock_cache = MagicMock()
        runner = CliRunner()
        with patch("spl3.judge.engine.run_judge", return_value=fail_result), \
             patch("spl3.cache.get_content_cache", return_value=mock_cache):
            result = runner.invoke(main, [
                "judge", str(f),
                "--criteria", "correctness",
                "--adapter", "ollama",
                "--cache-key", "deadbeef1234",
            ])
        assert result.exit_code == 0
        mock_cache.promote.assert_not_called()


# ── Phase 2: aggregators ──────────────────────────────────────────────────────

def _make_result(verdict: str, score: float, confidence: str = "HIGH") -> JudgeResult:
    return JudgeResult(
        verdict=verdict, score=score, confidence=confidence,
        reasoning="", feedback="",
        criteria_scores={"quality": score, "relevance": score},
        model="test", adapter="echo", rubric="test",
    )


class TestMajorityVote:
    def test_unanimous_pass(self):
        results = [_make_result("PASS", 9.0), _make_result("PASS", 8.0), _make_result("PASS", 8.5)]
        p = majority_vote(results, "test")
        assert p.verdict == "PASS"
        assert p.consensus == "UNANIMOUS"
        assert p.confidence == "HIGH"
        assert p.score == pytest.approx(8.5)

    def test_majority_pass(self):
        results = [_make_result("PASS", 8.0), _make_result("PASS", 7.5), _make_result("FAIL", 4.0)]
        p = majority_vote(results, "test")
        assert p.verdict == "PASS"
        assert p.consensus == "MAJORITY"
        assert p.confidence == "MEDIUM"
        assert p.dissent is not None

    def test_majority_fail(self):
        results = [_make_result("FAIL", 3.0), _make_result("FAIL", 4.0), _make_result("PASS", 8.0)]
        p = majority_vote(results, "test")
        assert p.verdict == "FAIL"
        assert p.consensus == "MAJORITY"

    def test_split_becomes_escalate(self):
        results = [_make_result("PASS", 8.0), _make_result("FAIL", 4.0)]
        p = majority_vote(results, "test")
        assert p.verdict == "ESCALATE"
        assert p.consensus == "SPLIT"
        assert p.confidence == "LOW"

    def test_score_is_mean(self):
        results = [_make_result("PASS", 8.0), _make_result("PASS", 6.0)]
        p = majority_vote(results, "test")
        assert p.score == pytest.approx(7.0)

    def test_rubric_name_propagated(self):
        results = [_make_result("PASS", 8.0)]
        p = majority_vote(results, "clarity")
        assert p.rubric == "clarity"
        assert p.aggregation == "majority"


class TestConfidenceWeighted:
    def test_high_confidence_wins(self):
        # One HIGH FAIL vs two LOW PASS — FAIL has more weight
        results = [
            _make_result("FAIL", 3.0, "HIGH"),
            _make_result("PASS", 8.0, "LOW"),
            _make_result("PASS", 8.0, "LOW"),
        ]
        p = confidence_weighted(results, "test")
        # HIGH=3 FAIL vs LOW+LOW=2 PASS → FAIL wins
        assert p.verdict == "FAIL"

    def test_weighted_score(self):
        results = [
            _make_result("PASS", 9.0, "HIGH"),   # weight=3
            _make_result("PASS", 6.0, "LOW"),    # weight=1
        ]
        p = confidence_weighted(results, "test")
        expected = (9.0 * 3 + 6.0 * 1) / 4
        assert p.score == pytest.approx(expected, abs=0.01)

    def test_aggregation_label(self):
        results = [_make_result("PASS", 8.0)]
        p = confidence_weighted(results, "test")
        assert p.aggregation == "confidence_weighted"


class TestUnanimous:
    def test_all_pass_gives_pass(self):
        results = [_make_result("PASS", 9.0), _make_result("PASS", 8.0)]
        p = unanimous(results, "test")
        assert p.verdict == "PASS"
        assert p.consensus == "UNANIMOUS"
        assert p.confidence == "HIGH"

    def test_one_fail_escalates(self):
        results = [_make_result("PASS", 9.0), _make_result("FAIL", 3.0)]
        p = unanimous(results, "test")
        assert p.verdict == "ESCALATE"

    def test_score_is_min(self):
        results = [_make_result("PASS", 9.0), _make_result("PASS", 6.0)]
        p = unanimous(results, "test")
        assert p.score == pytest.approx(6.0)

    def test_aggregation_label(self):
        results = [_make_result("PASS", 8.0)]
        p = unanimous(results, "test")
        assert p.aggregation == "unanimous"


class TestAggregate:
    def test_default_is_majority(self):
        results = [_make_result("PASS", 8.0)]
        p = aggregate(results, "majority", "test")
        assert p.aggregation == "majority"

    def test_dispatches_confidence_weighted(self):
        results = [_make_result("PASS", 8.0)]
        p = aggregate(results, "confidence_weighted", "test")
        assert p.aggregation == "confidence_weighted"

    def test_dispatches_unanimous(self):
        results = [_make_result("PASS", 8.0)]
        p = aggregate(results, "unanimous", "test")
        assert p.aggregation == "unanimous"


class TestSwapConsistentPanel:
    def test_all_consistent_returns_true(self):
        r1 = _make_result("PASS", 8.0); r1.swap_consistent = True
        r2 = _make_result("PASS", 7.0); r2.swap_consistent = True
        p = majority_vote([r1, r2], "test")
        assert p.swap_consistent is True

    def test_any_inconsistent_returns_false(self):
        r1 = _make_result("PASS", 8.0); r1.swap_consistent = True
        r2 = _make_result("PASS", 7.0); r2.swap_consistent = False
        p = majority_vote([r1, r2], "test")
        assert p.swap_consistent is False

    def test_none_checked_returns_none(self):
        results = [_make_result("PASS", 8.0), _make_result("PASS", 7.0)]
        p = majority_vote(results, "test")
        assert p.swap_consistent is None


# ── Phase 2: panel report rendering ──────────────────────────────────────────

@pytest.fixture
def panel_pass():
    r1 = _make_result("PASS", 9.0, "HIGH")
    r1.adapter, r1.model = "claude_cli", "claude-opus-4-6"
    r1.criteria_scores = {"quality": 9.0, "relevance": 9.0}
    r2 = _make_result("PASS", 8.0, "MEDIUM")
    r2.adapter, r2.model = "openrouter", "google/gemini-2.5-pro"
    r2.criteria_scores = {"quality": 8.0, "relevance": 8.0}
    return majority_vote([r1, r2], "clarity")


@pytest.fixture
def panel_split():
    r1 = _make_result("PASS", 8.0); r1.adapter, r1.model = "echo", "a"
    r2 = _make_result("FAIL", 4.0); r2.adapter, r2.model = "echo", "b"
    return majority_vote([r1, r2], "correctness")


class TestPanelReport:
    def test_json_has_individual(self, panel_pass):
        data = json.loads(render_judge_report(panel_pass, "json"))
        assert data["verdict"] == "PASS"
        assert data["consensus"] == "UNANIMOUS"
        assert len(data["individual"]) == 2

    def test_json_aggregation_field(self, panel_pass):
        data = json.loads(render_judge_report(panel_pass, "json"))
        assert data["aggregation"] == "majority"

    def test_text_shows_members(self, panel_pass):
        report = render_judge_report(panel_pass, "text")
        assert "claude_cli:claude-opus-4-6" in report
        assert "openrouter:google/gemini-2.5-pro" in report

    def test_markdown_has_panel_header(self, panel_pass):
        report = render_judge_report(panel_pass, "markdown")
        assert "# Panel Judge Report" in report
        assert "UNANIMOUS" in report

    def test_markdown_split_shows_dissent(self, panel_split):
        report = render_judge_report(panel_split, "markdown")
        assert "SPLIT" in report
        assert "Dissent" in report

    def test_markdown_criteria_mean_table(self, panel_pass):
        report = render_judge_report(panel_pass, "markdown")
        assert "Criteria Scores (mean across panel)" in report

    def test_default_format_is_markdown(self, panel_pass):
        report = render_judge_report(panel_pass)
        assert "# Panel Judge Report" in report


# ── Phase 2: run_panel integration (echo adapter) ────────────────────────────

class TestRunPanel:
    def test_run_panel_returns_panel_result(self, simple_rubric):
        from spl3.judge.types import PanelResult
        result = asyncio.run(run_panel(
            content="test content",
            rubric=simple_rubric,
            members=[("echo", None), ("echo", None)],
            aggregation="majority",
        ))
        assert isinstance(result, PanelResult)
        assert len(result.individual) == 2
        assert result.verdict in ("PASS", "FAIL", "ESCALATE")

    def test_run_panel_single_member(self, simple_rubric):
        from spl3.judge.types import PanelResult
        result = asyncio.run(run_panel(
            content="test content",
            rubric=simple_rubric,
            members=[("echo", None)],
        ))
        assert isinstance(result, PanelResult)
        assert result.individual[0].adapter == "echo"
