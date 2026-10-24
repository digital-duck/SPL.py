"""Tests for SPL 2.0 adapters — LLM backend registry and echo adapter."""

import asyncio
import pytest
from spl.adapters import get_adapter, list_adapters, register_adapter
from spl.adapters.base import LLMAdapter, GenerationResult
from spl.adapters.echo import EchoAdapter


class TestAdapterRegistry:
    def test_list_includes_builtin(self):
        adapters = list_adapters()
        assert "echo" in adapters
        assert "claude_cli" in adapters

    def test_get_echo_adapter(self):
        adapter = get_adapter("echo")
        assert isinstance(adapter, EchoAdapter)

    def test_get_unknown_adapter(self):
        with pytest.raises(ValueError, match="Unknown adapter"):
            get_adapter("nonexistent_adapter_xyz")

    @pytest.mark.parametrize("name", [
        "anthropic", "openai", "ollama", "openrouter", "claude_cli", "gemini_cli",
        "google", "deepseek", "qwen", "bedrock", "vertex", "azure_openai", "momagrid",
    ])
    def test_dd_llm_providers_registered(self, name):
        assert name in list_adapters()

    def test_provider_names_exist_in_dd_llm(self):
        import dd_llm
        from spl.adapters import _DD_LLM_PROVIDERS
        assert set(_DD_LLM_PROVIDERS.values()) <= set(dd_llm.list_adapters())


class TestEchoAdapter:
    def test_generate(self):
        adapter = EchoAdapter()
        result = asyncio.run(adapter.generate("Hello world"))
        assert isinstance(result, GenerationResult)
        assert "[Echo]" in result.content
        assert "Hello world" in result.content
        assert result.model == "echo"
        assert result.cost_usd == 0.0
        assert result.input_tokens > 0
        assert result.output_tokens > 0

    def test_generate_with_system(self):
        adapter = EchoAdapter()
        result = asyncio.run(adapter.generate("test", system="Be helpful"))
        assert isinstance(result, GenerationResult)

    def test_count_tokens(self):
        adapter = EchoAdapter()
        count = adapter.count_tokens("Hello world")
        assert count > 0

    def test_list_models(self):
        models = EchoAdapter().list_models()
        assert "echo" in models

    def test_max_tokens_truncation(self):
        adapter = EchoAdapter()
        result = asyncio.run(adapter.generate("x" * 10000, max_tokens=10))
        # Echo adapter respects max_tokens * 4 chars
        assert len(result.content) <= 10 * 4 + 20  # [Echo] prefix + truncated
