"""--llm ADAPTER[:MODEL] parsing is shared with dd-llm."""
import click
import pytest

from spl3.cli import _parse_llm_spec, _resolve_llm


@pytest.mark.parametrize("spec, expected", [
    ("claude_cli:claude-opus-4-6", ("claude_cli", "claude-opus-4-6")),
    ("ollama:gemma3:12b", ("ollama", "gemma3:12b")),
    ("openrouter:google/gemini-2.5-pro", ("openrouter", "google/gemini-2.5-pro")),
    ("echo", ("echo", None)),
])
def test_parse(spec, expected):
    assert _parse_llm_spec(spec) == expected


def test_missing_adapter_is_a_usage_error():
    with pytest.raises(click.BadParameter, match="ADAPTER"):
        _parse_llm_spec(":gpt-4o")


def test_resolve_panel_keeps_colons_in_models():
    assert _resolve_llm(("ollama:gemma3:12b", "echo"), "x", None) == [("ollama", "gemma3:12b"), ("echo", None)]
