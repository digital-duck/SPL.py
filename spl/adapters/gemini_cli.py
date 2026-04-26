"""Gemini CLI adapter: wraps the `gemini` CLI for development use.

Leverages Gemini CLI for zero marginal cost during development (if using a 
subscription or free tier). Invokes `gemini -p ""` via subprocess, 
feeding the prompt through stdin.
"""

from __future__ import annotations
import asyncio
import os
import subprocess
from spl.adapters.base import LLMAdapter, GenerationResult


class GeminiCLIAdapter(LLMAdapter):
    """LLM adapter that wraps the Gemini CLI.

    Usage:
        adapter = GeminiCLIAdapter()
        result = await adapter.generate("What is 2+2?")

    This adapter is designed for development use, leveraging existing
    Gemini CLI configuration and authentication.
    """

    DEFAULT_MODEL = "gemini-2.0-flash"

    def __init__(
        self,
        cli_path: str = "gemini",
        default_model: str = DEFAULT_MODEL,
        timeout: int = 300,
    ):
        self.cli_path = cli_path
        self.default_model = default_model
        self.timeout = timeout

    async def generate(
        self,
        prompt: str,
        model: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: str | None = None,
    ) -> GenerationResult:
        """Generate response by invoking gemini CLI."""
        start = self._measure_time()

        # Build the full prompt with system message if provided
        full_prompt = prompt
        if system:
            full_prompt = f"System: {system}\n\nUser: {prompt}"

        # Build CLI command
        effective_model = model or self.default_model
        
        # gemini -p "" --output-format text reads prompt from stdin
        cmd = [
            self.cli_path, 
            "-p", "", 
            "--output-format", "text",
            "--model", effective_model
        ]

        # Strip vars that might interfere with clean CLI execution if needed.
        # For now, we'll keep the environment as is, but we might want to 
        # filter session-specific vars if they cause issues with nested calls.
        _STRIP_VARS = {
            "GEMINI_CLI_SESSION_ID",
        }
        env = {k: v for k, v in os.environ.items() if k not in _STRIP_VARS}

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=full_prompt.encode("utf-8")),
                timeout=self.timeout,
            )
        except FileNotFoundError:
            raise RuntimeError(
                f"Gemini CLI not found at '{self.cli_path}'. "
                "Install Gemini CLI."
            )
        except asyncio.TimeoutError:
            raise RuntimeError(f"Gemini CLI timed out after {self.timeout}s")

        stderr_text = stderr.decode('utf-8', errors='replace').strip()

        if proc.returncode != 0:
            low_stderr = stderr_text.lower()
            # Detect rate limit or quota issues
            if any(m in low_stderr for m in ["rate limit", "quota", "exhausted"]):
                from spl.executor import ModelOverloaded
                raise ModelOverloaded(f"Gemini CLI limit reached: {stderr_text}")
            
            raise RuntimeError(f"Gemini CLI error (exit {proc.returncode}): {stderr_text}")

        content = stdout.decode('utf-8', errors='replace').strip()
        latency = self._elapsed_ms(start)

        if not content:
            hint = f" stderr: {stderr_text[:300]}" if stderr_text else " (no stderr either)"
            raise RuntimeError(
                f"Gemini CLI returned empty response (rc=0, latency={latency:.0f}ms).{hint}"
            )

        # Estimate tokens
        input_tokens = len(full_prompt) // 4
        output_tokens = len(content) // 4

        return GenerationResult(
            content=content,
            model=effective_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency_ms=latency,
            cost_usd=0.0,
        )

    def count_tokens(self, text: str, model: str = "") -> int:
        """Estimate tokens using character-based heuristic (~4 chars/token)."""
        if not text:
            return 0
        return max(1, len(text) // 4)

    def list_models(self) -> list[str]:
        """Return a selection of common Gemini models."""
        return [
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ]
