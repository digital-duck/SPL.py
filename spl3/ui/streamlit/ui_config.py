"""Shared constants for all SPL Studio Streamlit pages."""

from __future__ import annotations

ADAPTERS: list[str] = [
    "ollama",
    "claude_cli",
    "gemini_cli",
    "anthropic",
    "openai",
    "openrouter",
    "google",
    "deepseek",
    "qwen",
    "bedrock",
    "vertex",
    "azure_openai",
]

MODELS: dict[str, list[str]] = {
    "ollama":       ["gemma3", "llama3.2", "mistral", "phi3", "qwen2.5-coder", "deepseek-coder"],
    "claude_cli":   ["claude-sonnet-4-6", "claude-opus-4-6", "claude-haiku-4-5-20251001"],
    "gemini_cli":   ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-3-flash-preview"],
    "anthropic":    ["claude-sonnet-4-6", "claude-opus-4-6", "claude-haiku-4-5-20251001"],
    "openai":       ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
    "openrouter":   [
        "anthropic/claude-sonnet-4-6",
        "anthropic/claude-opus-4-6",
        "qwen/qwen3.6-plus",
        "google/gemini-3-flash-preview",
        "meta-llama/llama-3.3-70b-instruct",
    ],
    "google":       ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
    "deepseek":     ["deepseek-chat", "deepseek-coder"],
    "qwen":         ["qwen-max", "qwen-plus", "qwen-turbo"],
    "bedrock":      ["us.amazon.nova-pro-v1:0", "us.anthropic.claude-3-5-sonnet-20241022-v2:0"],
    "vertex":       ["gemini-2.0-flash-001", "gemini-1.5-pro-002", "gemini-1.5-flash-002"],
    "azure_openai": ["gpt-4o", "gpt-4o-mini"],
}

# Fixed judge model used for all spl3 compare calls in NeurIPS experiments
JUDGE_ADAPTER = "openrouter"
JUDGE_MODEL   = "anthropic/claude-opus-4-6"

# NeurIPS-26 experiment configuration
NEURIPS_RECIPES = ["agent", "rag", "judge", "thinking", "research"]
NEURIPS_RECIPE_DIRS = {
    "agent":    "R1-agent",
    "rag":      "R2-rag",
    "judge":    "R3-judge",
    "thinking": "R4-thinking",
    "research": "R5-research",
}
NEURIPS_MODELS = [
    {"alias": "claude", "adapter": "claude_cli",  "model_id": "claude-sonnet-4-6"},
    {"alias": "qwen",   "adapter": "openrouter",  "model_id": "qwen/qwen3.6-plus"},
    {"alias": "gemini", "adapter": "openrouter",  "model_id": "google/gemini-3-flash-preview"},
]
