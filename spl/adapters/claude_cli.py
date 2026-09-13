"""Claude Code CLI adapter: wraps the `claude` CLI for development use.

Leverages Claude Code subscription billing for zero marginal cost during development.
Invokes `claude --print` via subprocess, feeding the prompt through stdin.
"""

from __future__ import annotations
import asyncio
import os
import subprocess
from spl.adapters.base import LLMAdapter, GenerationResult


class ClaudeCLIAdapter(LLMAdapter):
    """LLM adapter that wraps the Claude Code CLI.

    Usage:
        adapter = ClaudeCLIAdapter()
        result = await adapter.generate("What is 2+2?")

    This adapter is designed for development use, leveraging existing
    Claude Code subscription (flat billing = zero marginal cost per call).
    """

    DEFAULT_MODEL = "claude-sonnet-5"

    def __init__(
        self,
        cli_path: str = "claude",
        default_model: str = DEFAULT_MODEL,
        model: str = "",
        timeout: int | None = None,
        allowed_tools: list[str] | None = None,
    ):
        self.cli_path = cli_path
        self.default_model = model or default_model
        # WebSearch and other tools add latency — use a larger default when tools are active
        self.timeout = timeout if timeout is not None else (1200 if allowed_tools else 1200)  # 1200s default; override with --llm-timeout
        self.allowed_tools = allowed_tools or []

    async def generate(
        self,
        prompt: str,
        model: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: str | None = None,
    ) -> GenerationResult:
        """Generate response by invoking claude CLI."""
        start = self._measure_time()

        # Build the full prompt with system message if provided
        full_prompt = prompt
        if system:
            full_prompt = f"System: {system}\n\nUser: {prompt}"

        # Build CLI command
        effective_model = model or self.default_model
        # Pass prompt via stdin (not -p arg) to avoid OS arg-length limits
        # with large prompts (e.g. review/fix steps that embed generated code).
        cmd = [self.cli_path, "--print", "--no-session-persistence",
               "--model", effective_model]
        if self.allowed_tools:
            cmd += ["--allowedTools", ",".join(self.allowed_tools)]
        else:
            # No tools needed — disabling avoids loading tool schemas and
            # permission checks, which cuts ~50s of startup overhead.
            cmd += ["--tools", ""]

        # Strip vars that would route requests to the paid API instead of
        # the Claude Code subscription.  If ANTHROPIC_API_KEY is present in
        # the environment, claude -p uses the API (and charges per token).
        # Removing it forces the CLI to use its locally-stored OAuth token.
        # Also strip session markers so nested invocations are accepted.
        _STRIP_VARS = {
            "ANTHROPIC_API_KEY",       # paid API — must NOT be used here
            "ANTHROPIC_BASE_URL",      # API base URL — not needed for CLI auth
            "CLAUDECODE",              # nested-session guard
            "CLAUDE_CODE_ENTRYPOINT",  # nested-session guard
        }
        env = {k: v for k, v in os.environ.items() if k not in _STRIP_VARS}

        # Feed prompt via stdin using communicate(input=...) — avoids OS arg-length
        # limits and eliminates the file-handle race in the temp-file approach.
        #
        # Self-healing retry: `create_subprocess_exec` can raise OSError
        # (FileNotFoundError, PermissionError, "Text file busy", etc.) for
        # reasons that have nothing to do with the LLM call itself — e.g.
        # the Claude Code CLI's own auto-updater briefly rewriting the
        # binary/symlink mid-run. Observed in practice: 20+ consecutive
        # successful calls in one process, then one FileNotFoundError,
        # then success again immediately after — the classic signature of
        # a transient environment race, not a real "CLI missing" state.
        # Retrying a couple of times with a short pause rides out that
        # window; a genuinely missing/broken CLI still fails after that.
        max_launch_attempts = 3  # 1 initial try + 2 retries
        last_oserror: OSError | None = None
        proc = None
        stdout = stderr = b""
        for attempt in range(1, max_launch_attempts + 1):
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
                last_oserror = None
                break
            except asyncio.TimeoutError:
                # NOTE: asyncio.TimeoutError is a OSError subclass (it's an
                # alias for the builtin TimeoutError as of Python 3.11) —
                # this branch must come before `except OSError` or a real
                # hang would be silently retried as if it were a launch
                # failure. A slow/stuck generation isn't the "environment
                # hiccup" this retry loop targets, so it fails immediately.
                raise RuntimeError(f"Claude CLI timed out after {self.timeout}s")
            except OSError as e:
                last_oserror = e
                if attempt < max_launch_attempts:
                    await asyncio.sleep(1.5 * attempt)
                    continue

        if last_oserror is not None:
            if isinstance(last_oserror, FileNotFoundError):
                raise RuntimeError(
                    f"Claude CLI not found at '{self.cli_path}' "
                    f"(after {max_launch_attempts} attempts). "
                    "Install Claude Code: https://docs.anthropic.com/en/docs/claude-code"
                )
            raise RuntimeError(
                f"Claude CLI failed to launch after {max_launch_attempts} attempts: {last_oserror}"
            )
        assert proc is not None

        stderr_text = stderr.decode('utf-8', errors='replace').strip()
        stdout_text = stdout.decode('utf-8', errors='replace').strip()

        if proc.returncode != 0:
            # The claude CLI often writes errors to stdout rather than stderr.
            error_detail = stderr_text or stdout_text or "(no output)"
            low_detail = error_detail.lower()
            # Detect session limit, rate limit, or quota issues
            if any(m in low_detail for m in ["session limit", "rate limit", "quota"]):
                # Use local import to avoid circular dependency at module load time.
                # The executor will catch this and handle it via EXCEPTION WHEN ModelOverloaded.
                from spl.executor import ModelOverloaded
                raise ModelOverloaded(f"Claude CLI limit reached: {error_detail}")

            raise RuntimeError(f"Claude CLI error (exit {proc.returncode}): {error_detail}")

        content = stdout_text
        latency = self._elapsed_ms(start)

        if not content:
            hint = f" stderr: {stderr_text[:300]}" if stderr_text else " (no stderr either)"
            raise RuntimeError(
                f"Claude CLI returned empty response (rc=0, latency={latency:.0f}ms).{hint}"
            )

        # Estimate tokens (Claude doesn't expose tokenizer publicly)
        input_tokens = len(full_prompt) // 4
        output_tokens = len(content) // 4

        return GenerationResult(
            content=content,
            model=effective_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency_ms=latency,
            cost_usd=0.0,  # Subscription billing
        )

    async def generate_multimodal(
        self,
        content: list[dict],
        model: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: str | None = None,
    ) -> GenerationResult:
        """Generate from content including images using the Anthropic SDK directly.

        The `claude` CLI accepts only text via stdin and has no flag for binary
        image data.  For vision calls this method bypasses the CLI and calls the
        Anthropic Messages API via the Python SDK, which requires ANTHROPIC_API_KEY.
        """
        try:
            import anthropic as _anthropic
        except ImportError:
            raise ImportError(
                "pip install anthropic  — required for multimodal calls via claude_cli adapter"
            )

        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is required for multimodal (vision) calls.\n"
                "ClaudeCLIAdapter uses the Anthropic SDK for image input because the\n"
                "claude CLI has no binary image flag.  Set ANTHROPIC_API_KEY, or use\n"
                "--adapter anthropic / --adapter google instead."
            )

        effective_model = model or self.default_model

        api_content: list[dict] = []
        for part in content:
            ptype = part.get("type")
            if ptype == "text":
                api_content.append({"type": "text", "text": part.get("text", "")})
            elif ptype == "image":
                if part.get("source") == "base64":
                    api_content.append({
                        "type": "image",
                        "source": {
                            "type":       "base64",
                            "media_type": part.get("media_type", "image/png"),
                            "data":       part.get("data", ""),
                        },
                    })
                elif part.get("source") == "url":
                    api_content.append({
                        "type": "image",
                        "source": {"type": "url", "url": part.get("url", "")},
                    })

        kwargs: dict = {
            "model":      effective_model,
            "max_tokens": max_tokens,
            "messages":   [{"role": "user", "content": api_content}],
        }
        if system:
            kwargs["system"] = system

        start  = self._measure_time()
        client = _anthropic.AsyncAnthropic(api_key=api_key)
        try:
            response = await client.messages.create(**kwargs)
        finally:
            await client.close()

        latency = self._elapsed_ms(start)
        text    = "".join(b.text for b in response.content if b.type == "text")

        return GenerationResult(
            content=text,
            model=effective_model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            latency_ms=latency,
            cost_usd=0.0,
        )

    def count_tokens(self, text: str, model: str = "") -> int:
        """Estimate tokens using character-based heuristic (~3.5 chars/token for Claude)."""
        if not text:
            return 0
        return max(1, len(text) // 4)

    def list_models(self) -> list[str]:
        """Return available Claude models supported by the CLI."""
        return [
            "claude-haiku-4-5-20251001",
            "claude-opus-4-6",
            "claude-sonnet-5",
        ]
