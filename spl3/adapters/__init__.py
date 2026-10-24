"""SPL adapters — SPL30 extends the spl.adapters registry.

All providers come from dd-llm, wrapped by MultiModalDDLLMBridge so that
generate_multimodal() works.  ``echo`` is SPL's in-process test double.
SPL30 adds:
  - liquid  — Liquid AI LFM models (Ollama local or OpenRouter cloud)
  - snap    — placeholder (Ubuntu 26.04)
"""

from __future__ import annotations

import importlib as _importlib
import inspect as _inspect
from spl3.logging_config import get_logger
from pathlib import Path as _Path

# ── Extend __path__ to include spl/adapters/ ─────────────────────────────────
# In dev layout: spl3/adapters/ and spl/adapters/ are siblings inside SPL/
# In installed layout: both land in site-packages/ as spl3/ and spl/ siblings
# Try installed-package path first (3 levels up), then legacy monorepo path.
_spl_adapters = _Path(__file__).parent.parent.parent / "spl" / "adapters"
if _spl_adapters.exists():
    __path__ = list(__path__) + [str(_spl_adapters)]
else:
    _spl20_adapters = _Path(__file__).parent.parent.parent.parent / "SPL20" / "spl" / "adapters"
    if _spl20_adapters.exists():
        __path__ = list(__path__) + [str(_spl20_adapters)]

# ── Re-export base types ───────────────────────────────────────────────────────
# spl.adapters.base is always available — spl/ is co-installed with spl3/
from spl.adapters.base import LLMAdapter, GenerationResult  # noqa: F401

_log = get_logger("adapters")
_ADAPTER_REGISTRY: dict[str, type] = {}

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


# ── Public registry API (mirrors SPL20) ───────────────────────────────────────

def register_adapter(name: str, adapter_cls) -> None:
    """Register an LLM adapter by name (class or factory callable)."""
    _ADAPTER_REGISTRY[name] = adapter_cls


def _model_compatible(adapter_name: str, model: str) -> bool:
    """Return False when model is clearly wrong for the given adapter.

    Each entry is a set of lowercase prefixes that are *valid* for that adapter.
    A model that matches none of the valid prefixes for a *known* adapter is
    rejected so the caller can fall back to the adapter's default instead of
    making a doomed API call.
    """
    if not model:
        return True  # no model specified — adapter uses its own default
    m = model.lower()
    rules: dict[str, tuple[str, ...]] = {
        # Claude CLI and Anthropic API only speak Claude models
        "claude_cli":  ("claude-",),
        "anthropic":   ("claude-",),
        # Gemini CLI only speaks Gemini models
        "gemini_cli":  ("gemini-", "gemini"),
        # OpenAI only speaks gpt / o1 / o3 / text- models
        "openai":      ("gpt-", "o1", "o3", "text-", "davinci", "curie", "babbage", "ada"),
        # OpenRouter models always contain a slash (provider/model)
        "openrouter":  ("/",),
    }
    valid_prefixes = rules.get(adapter_name)
    if valid_prefixes is None:
        return True  # unknown adapter — don't second-guess it
    return any(m.startswith(p) or (p == "/" and "/" in m) for p in valid_prefixes)


def get_adapter(name: str, **kwargs) -> LLMAdapter:
    """Get an LLM adapter instance by name.

    If the requested model is incompatible with the adapter (e.g. an ollama
    model name passed to claude_cli), a warning is logged and the model kwarg
    is dropped so the adapter uses its own default.
    """
    if name not in _ADAPTER_REGISTRY:
        available = ", ".join(sorted(_ADAPTER_REGISTRY.keys())) or "(none)"
        raise ValueError(f"Unknown adapter '{name}'. Available: {available}")

    model = kwargs.get("model") or ""
    if model and not _model_compatible(name, model):
        try:
            entry_cls = _ADAPTER_REGISTRY[name]
            default = getattr(entry_cls, "DEFAULT_MODEL", None) or "(adapter default)"
        except Exception:
            default = "(adapter default)"

        _log.warning(
            "Model '%s' is not compatible with adapter '%s' — "
            "falling back to %s",
            model, name, default,
        )
        kwargs = {k: v for k, v in kwargs.items() if k != "model"}

    entry = _ADAPTER_REGISTRY[name]
    if _inspect.isclass(entry):
        sig = _inspect.signature(entry.__init__)
        supported = {k: v for k, v in kwargs.items() if k in sig.parameters}
        return entry(**supported)
    return entry(**kwargs)


def list_adapters() -> list[str]:
    """List registered adapter names (sorted)."""
    return sorted(_ADAPTER_REGISTRY.keys())


# ── Bootstrap ─────────────────────────────────────────────────────────────────

def _bootstrap() -> None:
    # 1. echo (in-process test double) + every dd-llm provider.
    #    Use SPL30's MultiModalDDLLMBridge so generate_multimodal() works.
    from spl.adapters.echo import EchoAdapter
    from spl3.adapters.dd_llm_bridge import MultiModalDDLLMBridge

    register_adapter("echo", EchoAdapter)
    for _spl_name, _dd_name in _DD_LLM_PROVIDERS.items():
        register_adapter(_spl_name, lambda p=_dd_name, **kw: MultiModalDDLLMBridge(p, **kw))
    _log.debug("dd-llm multimodal bridge registered: %s", ", ".join(_DD_LLM_PROVIDERS))

    # 2. SPL30 new adapters
    for _name, _mod, _cls in [
        ("liquid", "spl3.adapters.liquid", "LiquidAdapter"),
        ("snap",   "spl3.adapters.snap",   "SnapAdapter"),    # placeholder — Ubuntu 26.04
    ]:
        try:
            register_adapter(_name, getattr(_importlib.import_module(_mod), _cls))
        except (ImportError, AttributeError):
            _log.debug("SPL30 adapter '%s' not available", _name)


_bootstrap()
