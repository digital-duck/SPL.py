"""LLM adapter registry and factory for SPL.

All providers are implemented in dd-llm and exposed through ``DDLLMBridge``
(async wrapper over dd-llm's synchronous ``call()``).  Only ``echo`` (an
in-process test double) is implemented here.
"""

import inspect
import logging

from spl.adapters.base import LLMAdapter, GenerationResult

_log = logging.getLogger("spl.adapters")
_ADAPTER_REGISTRY: dict[str, type[LLMAdapter]] = {}

# SPL adapter name -> dd-llm provider name ("google" maps to dd-llm's "gemini").
_DD_LLM_PROVIDERS: dict[str, str] = {
    "anthropic":    "anthropic",
    "openai":       "openai",
    "ollama":       "ollama",
    "openrouter":   "openrouter",
    "claude_cli":   "claude_cli",
    "gemini_cli":   "gemini_cli",
    "google":       "gemini",
    "deepseek":     "deepseek",
    "qwen":         "qwen",
    "bedrock":      "bedrock",
    "vertex":       "vertex",
    "azure_openai": "azure_openai",
    "momagrid":     "momagrid",
}


def register_adapter(name: str, adapter_cls):
    """Register an LLM adapter by name (class or factory callable)."""
    _ADAPTER_REGISTRY[name] = adapter_cls


def get_adapter(name: str, **kwargs) -> LLMAdapter:
    """Get an LLM adapter instance by name."""
    if name not in _ADAPTER_REGISTRY:
        available = ", ".join(sorted(_ADAPTER_REGISTRY.keys())) or "(none)"
        raise ValueError(f"Unknown adapter '{name}'. Available: {available}")
    entry = _ADAPTER_REGISTRY[name]
    # Support both class constructors and factory callables.
    if inspect.isclass(entry):
        sig = inspect.signature(entry.__init__)
        supported = {k: v for k, v in kwargs.items() if k in sig.parameters}
        return entry(**supported)
    return entry(**kwargs)


def list_adapters() -> list[str]:
    """List registered adapter names."""
    return list(_ADAPTER_REGISTRY.keys())


def _register_builtin_adapters():
    """Register echo plus every dd-llm provider via DDLLMBridge."""
    from spl.adapters.echo import EchoAdapter
    from spl.adapters.dd_llm_bridge import DDLLMBridge

    register_adapter("echo", EchoAdapter)
    for spl_name, dd_name in _DD_LLM_PROVIDERS.items():
        register_adapter(spl_name, lambda p=dd_name, **kw: DDLLMBridge(p, **kw))
    _log.debug("dd-llm bridge registered for: %s", ", ".join(_DD_LLM_PROVIDERS))


_register_builtin_adapters()
