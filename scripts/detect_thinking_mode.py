#!/usr/bin/env python3
"""
detect_thinking_mode.py — Detect if Ollama local models run in thinking mode.

Asks each model "what is 10!?" via the Ollama REST API and checks for thinking
indicators (<think> tags, "Thinking...", long preamble before the numeric answer).
Thinking-mode models are excluded from SPL neurosymbolic experiments because
their token budget exhaustion is a model-interface issue, not a capability failure.

NL→expr decomposition is a probabilistic (translation) task. Thinking mode
misapplies deterministic deliberation to it, exhausting tokens before the
structured output is emitted — a fourth failure mode invisible to SPL status codes.

Usage:
    python scripts/detect_thinking_mode.py
    python scripts/detect_thinking_mode.py --timeout 45
    python scripts/detect_thinking_mode.py --json
    python scripts/detect_thinking_mode.py --models qwen3:latest,gemma3:latest
"""

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

OLLAMA_API = "http://localhost:11434"
PROBE = "what is 10!?"
EXPECTED_CONTAINS = "3628800"
THINKING_MARKERS = ["<think>", "</think>", "Thinking...", "<|thinking|>", "Thinking Process:"]
# >80 words before the numeric answer is a red flag for a trivial factorial question
VERBOSE_WORD_THRESHOLD = 80

# Ollama >= 0.30 separates thinking content into a dedicated JSON field
OLLAMA_THINKING_FIELD = "thinking"


@dataclass
class ModelResult:
    name: str
    thinking_mode: bool
    indicator: str
    response_time: float
    has_expected_answer: bool
    preview: str
    safe_for_experiment: bool
    error: str = ""


def get_ollama_models() -> list[str]:
    """Parse model names from `ollama list`."""
    try:
        out = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True, timeout=10
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        print(f"ERROR: cannot run `ollama list`: {e}", file=sys.stderr)
        sys.exit(1)

    if out.returncode != 0:
        print(f"ERROR: `ollama list` failed:\n{out.stderr}", file=sys.stderr)
        sys.exit(1)

    models = []
    for line in out.stdout.strip().splitlines()[1:]:  # skip header row
        parts = line.split()
        if parts:
            models.append(parts[0])
    return models


def stream_generate(model: str, timeout: int) -> tuple[str, float]:
    """
    Call /api/generate with streaming. Collects tokens until:
      - done flag received, OR
      - thinking marker detected (early exit to avoid waiting for full thinking trace), OR
      - timeout exceeded.
    Returns (accumulated_text, elapsed_seconds).
    """
    payload = json.dumps({
        "model": model,
        "prompt": PROBE,
        "stream": True,
        "options": {
            "num_predict": 300,   # cap tokens; thinking models burn this in <think> content
            "temperature": 0.0,
        },
    }).encode()

    req = urllib.request.Request(
        f"{OLLAMA_API}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    collected = ""
    thinking_content = ""
    start = time.time()

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            for raw_line in resp:
                if time.time() - start > timeout:
                    collected += " [TIMEOUT]"
                    break
                try:
                    chunk = json.loads(raw_line.decode())
                except json.JSONDecodeError:
                    continue

                # Ollama >= 0.30 puts thinking in a separate field; response is empty while thinking
                think_tok = chunk.get(OLLAMA_THINKING_FIELD, "") or ""
                response_tok = chunk.get("response", "") or ""
                thinking_content += think_tok
                collected += response_tok

                # Early exit: dedicated thinking field present → confirmed thinking model
                if thinking_content:
                    return f"[THINKING_FIELD]{thinking_content[:200]}", time.time() - start

                # Fallback: thinking markers embedded in response text
                for marker in THINKING_MARKERS:
                    if marker in collected:
                        return collected, time.time() - start

                if chunk.get("done"):
                    break

    except urllib.error.URLError as e:
        return f"[API ERROR: {e}]", time.time() - start
    except TimeoutError:
        return collected + " [TIMEOUT]", time.time() - start

    return collected, time.time() - start


def detect_thinking(text: str) -> tuple[bool, str]:
    """Return (is_thinking, reason_string)."""
    # Ollama >= 0.30 dedicated thinking field (highest confidence)
    if text.startswith("[THINKING_FIELD]"):
        excerpt = text[len("[THINKING_FIELD]"):].replace("\n", " ")[:80]
        return True, f"Ollama thinking field: \"{excerpt}\""

    for marker in THINKING_MARKERS:
        if marker in text:
            return True, f'found "{marker}"'

    # Heuristic: many words before the expected answer is a thinking-preamble signal
    words_before_answer = text.split(EXPECTED_CONTAINS)[0] if EXPECTED_CONTAINS in text else text
    word_count = len(words_before_answer.split())
    if word_count > VERBOSE_WORD_THRESHOLD:
        return True, f"verbose preamble ({word_count} words before answer)"

    return False, ""


def probe_model(model: str, timeout: int) -> ModelResult:
    raw, elapsed = stream_generate(model, timeout)
    is_api_err = raw.startswith("[API ERROR")
    is_timeout = "[TIMEOUT]" in raw

    if is_api_err:
        return ModelResult(
            name=model, thinking_mode=False, indicator="", response_time=elapsed,
            has_expected_answer=False, preview=raw[:80], safe_for_experiment=False,
            error=raw,
        )

    thinking, indicator = detect_thinking(raw)
    has_answer = EXPECTED_CONTAINS in raw
    preview = raw[:120].replace("\n", " ").strip()
    safe = (not thinking) and (not is_timeout) and (not is_api_err)

    return ModelResult(
        name=model,
        thinking_mode=thinking,
        indicator=indicator,
        response_time=round(elapsed, 1),
        has_expected_answer=has_answer,
        preview=preview,
        safe_for_experiment=safe,
        error="TIMEOUT" if is_timeout else "",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Detect Ollama thinking-mode models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--timeout", type=int, default=60,
        help="Seconds to wait per model (default 60)",
    )
    parser.add_argument(
        "--json", action="store_true", dest="output_json",
        help="Print results as JSON after the table",
    )
    parser.add_argument(
        "--models",
        help="Comma-separated model names to probe (default: all from `ollama list`)",
    )
    args = parser.parse_args()

    if args.models:
        models = [m.strip() for m in args.models.split(",") if m.strip()]
    else:
        models = get_ollama_models()

    if not models:
        print("No models found. Run `ollama pull <model>` first.")
        sys.exit(0)

    print(f"Probe: '{PROBE}'  (expected: {EXPECTED_CONTAINS})")
    print(f"Models: {len(models)}   Timeout: {args.timeout}s\n")

    hdr = f"{'Model':<38} {'Mode':^9} {'Ans':^5} {'Time':>6}  Info"
    print(hdr)
    print("-" * 90)

    results: list[ModelResult] = []
    safe_models: list[str] = []

    for model in models:
        r = probe_model(model, args.timeout)
        results.append(r)

        if r.error:
            status = "ERROR"
            info = r.error[:50]
        elif r.thinking_mode:
            status = "THINKING"
            info = r.indicator
        else:
            status = "normal"
            info = r.preview[:55]

        ans_flag = "yes" if r.has_expected_answer else "no "
        print(f"{r.name:<38} {status:^9} {ans_flag:^5} {r.response_time:>5.1f}s  {info}")

        if r.safe_for_experiment:
            safe_models.append(r.name)

    print("\n" + "=" * 90)
    thinking_models = [r.name for r in results if r.thinking_mode]

    print(f"\nThinking models ({len(thinking_models)}) — excluded from neurosymbolic experiments:")
    for m in thinking_models:
        print(f"  {m}")

    print(f"\nSafe models ({len(safe_models)}) — ok for neurosymbolic experiments:")
    for m in safe_models:
        print(f"  {m}")

    if args.output_json:
        out = [{
            "model": r.name,
            "thinking_mode": r.thinking_mode,
            "indicator": r.indicator,
            "response_time_s": r.response_time,
            "has_expected_answer": r.has_expected_answer,
            "safe_for_experiment": r.safe_for_experiment,
            "error": r.error,
        } for r in results]
        print("\n" + json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
