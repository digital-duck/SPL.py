The spec file doesn't exist yet — the path is the target output location. Based on the NeurIPS-26-lab R3-judge context and the round's purpose (LLM-as-judge evaluation), I'll implement the judge workflow now.

```python
#!/usr/bin/env python3
"""
LLM-as-a-Judge evaluation workflow using PocketFlow.
Evaluates a question/response pair on multiple criteria using an LLM judge.
"""

import os
import re
import json
import textwrap
from typing import Any

# ---------------------------------------------------------------------------
# PocketFlow minimal runtime (inline — no external dep beyond pocketflow pkg)
# ---------------------------------------------------------------------------
try:
    from pocketflow import Node, Flow
except ImportError:
    # Minimal PocketFlow implementation if package not installed
    class Node:
        def __init__(self): self.successors = {}
        def prep(self, shared): return None
        def exec(self, prep_res): return None
        def post(self, shared, prep_res, exec_res): return "default"
        def __rshift__(self, other):
            self.successors["default"] = other
            return other
        def __sub__(self, label):
            class _Edge:
                def __init__(self, src, lbl): self._src, self._lbl = src, lbl
                def __rshift__(self_, other):
                    self_._src.successors[self_._lbl] = other
                    return other
            return _Edge(self, label)

    class Flow:
        def __init__(self, start): self.start = start
        def run(self, shared):
            node = self.start
            while node:
                prep_res = node.prep(shared)
                exec_res = node.exec(prep_res)
                action = node.post(shared, prep_res, exec_res)
                node = node.successors.get(action or "default")
            return shared

# ---------------------------------------------------------------------------
# LLM helper
# ---------------------------------------------------------------------------
_LLM_MODEL = os.environ.get("LLM_MODEL", "claude-opus-4-7")
_LLM_MAX_TOKENS = int(os.environ.get("LLM_MAX_TOKENS", "2048"))


def call_llm(prompt: str, model: str = None, system: str = None) -> str:
    """Call the LLM via the claude CLI adapter (subprocess) or openrouter."""
    model = model or _LLM_MODEL

    adapter = os.environ.get("LLM_ADAPTER", "claude_cli")

    if adapter == "claude_cli":
        return _call_claude_cli(prompt, model, system)
    elif adapter == "openrouter":
        return _call_openrouter(prompt, model, system)
    else:
        raise ValueError(f"Unknown adapter: {adapter}. Set LLM_ADAPTER=claude_cli or openrouter")


def _call_claude_cli(prompt: str, model: str, system: str = None) -> str:
    import subprocess, shlex
    cmd = ["claude", "-p", prompt, "--model", model, "--max-tokens", str(_LLM_MAX_TOKENS)]
    if system:
        cmd += ["--system-prompt", system]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"claude CLI error: {result.stderr.strip()}")
    return result.stdout.strip()


def _call_openrouter(prompt: str, model: str, system: str = None) -> str:
    import urllib.request
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        raise EnvironmentError("OPENROUTER_API_KEY not set")
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": _LLM_MAX_TOKENS,
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"].strip()


# ---------------------------------------------------------------------------
# Judge rubric
# ---------------------------------------------------------------------------
JUDGE_CRITERIA = [
    ("correctness",   "Is the response factually accurate and logically sound?"),
    ("completeness",  "Does it fully address all aspects of the question?"),
    ("clarity",       "Is the response clear, well-structured, and easy to follow?"),
    ("conciseness",   "Is it appropriately concise without omitting important detail?"),
    ("helpfulness",   "Would this response genuinely help someone with the question?"),
]

JUDGE_SYSTEM = textwrap.dedent("""\
    You are an impartial, rigorous judge evaluating LLM-generated responses.
    You must provide structured scores and reasoning. Be critical and calibrated:
    a score of 5/5 should be rare and reserved for truly exceptional responses.
    Always output valid JSON as instructed.
""")

JUDGE_PROMPT_TEMPLATE = textwrap.dedent("""\
    Evaluate the following RESPONSE to the given QUESTION.

    ---
    QUESTION:
    {question}

    ---
    RESPONSE:
    {response}

    ---
    Score each criterion from 1 (very poor) to 5 (excellent).
    Provide a one-sentence rationale for each score.

    Criteria:
    {criteria_list}

    Return ONLY a JSON object with this exact schema:
    {{
      "scores": {{
        "correctness":  {{"score": <1-5>, "rationale": "<one sentence>"}},
        "completeness": {{"score": <1-5>, "rationale": "<one sentence>"}},
        "clarity":      {{"score": <1-5>, "rationale": "<one sentence>"}},
        "conciseness":  {{"score": <1-5>, "rationale": "<one sentence>"}},
        "helpfulness":  {{"score": <1-5>, "rationale": "<one sentence>"}}
      }},
      "overall_score": <float 1.0-5.0, weighted mean>,
      "verdict": "<pass|borderline|fail>",
      "summary": "<2-3 sentence overall assessment>"
    }}
""")


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

class ValidateInputNode(Node):
    """Validate that question and response are present and non-empty."""

    def prep(self, shared: dict) -> dict:
        return {
            "question": shared.get("question", "").strip(),
            "response": shared.get("response", "").strip(),
        }

    def exec(self, prep_res: dict) -> str:
        if not prep_res["question"]:
            return "missing_question"
        if not prep_res["response"]:
            return "missing_response"
        return "ok"

    def post(self, shared: dict, prep_res: dict, exec_res: str) -> str:
        if exec_res != "ok":
            shared["error"] = exec_res
            return "error"
        shared["question"] = prep_res["question"]
        shared["response"] = prep_res["response"]
        return "default"


class JudgeEvalNode(Node):
    """Call the judge LLM to evaluate the response on all criteria at once."""

    def prep(self, shared: dict) -> dict:
        criteria_list = "\n".join(
            f"  - {name}: {desc}" for name, desc in JUDGE_CRITERIA
        )
        prompt = JUDGE_PROMPT_TEMPLATE.format(
            question=shared["question"],
            response=shared["response"],
            criteria_list=criteria_list,
        )
        return {"prompt": prompt}

    def exec(self, prep_res: dict) -> str:
        return call_llm(prep_res["prompt"], system=JUDGE_SYSTEM)

    def post(self, shared: dict, prep_res: dict, exec_res: str) -> str:
        shared["raw_judge_output"] = exec_res
        return "default"


class ParseScoresNode(Node):
    """Parse the JSON output from the judge LLM; retry once on failure."""

    def prep(self, shared: dict) -> str:
        return shared["raw_judge_output"]

    def exec(self, prep_res: str) -> dict | None:
        # Strip markdown fences if present
        text = re.sub(r"```(?:json)?\s*", "", prep_res).strip().rstrip("`").strip()
        # Extract first {...} block
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            return None
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            return None

    def post(self, shared: dict, prep_res: str, exec_res: dict | None) -> str:
        if exec_res is None:
            shared["parse_attempts"] = shared.get("parse_attempts", 0) + 1
            if shared["parse_attempts"] < 2:
                # Patch the raw output with a repair instruction and retry
                shared["raw_judge_output"] = call_llm(
                    f"The following text should be valid JSON but is malformed. "
                    f"Return ONLY corrected JSON, nothing else:\n\n{prep_res}",
                    system="Output only valid JSON. No explanation.",
                )
                return "retry"
            shared["error"] = "Failed to parse judge output after retry"
            return "error"
        shared["evaluation"] = exec_res
        return "default"


class ComputeFinalVerdictNode(Node):
    """Recompute the overall_score in-process for auditability; enrich output."""

    def prep(self, shared: dict) -> dict:
        return shared["evaluation"]

    def exec(self, prep_res: dict) -> dict:
        scores_block = prep_res.get("scores", {})
        raw_scores = [
            scores_block[name]["score"]
            for name, _ in JUDGE_CRITERIA
            if name in scores_block
        ]
        computed_mean = round(sum(raw_scores) / len(raw_scores), 2) if raw_scores else 0.0

        # Honour the judge's own overall_score but also record our computation
        llm_overall = prep_res.get("overall_score", computed_mean)

        verdict = prep_res.get("verdict", "borderline")
        if verdict not in ("pass", "borderline", "fail"):
            verdict = "pass" if computed_mean >= 4.0 else ("borderline" if computed_mean >= 2.5 else "fail")

        return {
            "scores": scores_block,
            "overall_score_llm": llm_overall,
            "overall_score_computed": computed_mean,
            "verdict": verdict,
            "summary": prep_res.get("summary", ""),
        }

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        shared["result"] = exec_res
        return "default"


class FormatOutputNode(Node):
    """Pretty-print the final result and write JSON to shared['output']."""

    def prep(self, shared: dict) -> dict:
        return shared.get("result", {})

    def exec(self, prep_res: dict) -> str:
        lines = ["=" * 60, "  LLM JUDGE EVALUATION REPORT", "=" * 60]
        scores = prep_res.get("scores", {})
        for name, _ in JUDGE_CRITERIA:
            entry = scores.get(name, {})
            score = entry.get("score", "N/A")
            rationale = entry.get("rationale", "")
            lines.append(f"  {name.upper():14s}  {score}/5   {rationale}")
        lines.append("-" * 60)
        lines.append(f"  OVERALL (LLM)    : {prep_res.get('overall_score_llm', 'N/A'):.2f}/5.0")
        lines.append(f"  OVERALL (COMPUTED): {prep_res.get('overall_score_computed', 'N/A'):.2f}/5.0")
        lines.append(f"  VERDICT          : {prep_res.get('verdict', 'N/A').upper()}")
        lines.append("=" * 60)
        lines.append("  SUMMARY:")
        for line in textwrap.wrap(prep_res.get("summary", ""), width=56):
            lines.append(f"  {line}")
        lines.append("=" * 60)
        return "\n".join(lines)

    def post(self, shared: dict, prep_res: dict, exec_res: str) -> str:
        print(exec_res)
        shared["output"] = json.dumps(
            {
                "question": shared.get("question", ""),
                "response": shared.get("response", ""),
                **shared.get("result", {}),
            },
            indent=2,
        )
        return "default"


class ErrorNode(Node):
    """Handles validation and parse errors gracefully."""

    def prep(self, shared: dict) -> str:
        return shared.get("error", "unknown error")

    def exec(self, prep_res: str) -> None:
        print(f"[ERROR] Judge workflow failed: {prep_res}")

    def post(self, shared: dict, prep_res: str, exec_res: None) -> str:
        shared["output"] = json.dumps({"error": prep_res})
        return "default"


# ---------------------------------------------------------------------------
# Build the flow
# ---------------------------------------------------------------------------

def build_judge_flow() -> Flow:
    validate = ValidateInputNode()
    judge    = JudgeEvalNode()
    parse    = ParseScoresNode()
    verdict  = ComputeFinalVerdictNode()
    fmt      = FormatOutputNode()
    error    = ErrorNode()

    # Happy path
    validate >> judge >> parse >> verdict >> fmt

    # Error exits from validate and parse
    validate - "error" >> error
    parse    - "error" >> error

    # Retry loop from parse back to itself (up to 1 extra attempt)
    parse - "retry" >> parse

    return Flow(start=validate)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_judge(question: str, response: str) -> dict:
    """Run the judge flow and return the parsed result dict."""
    shared = {"question": question, "response": response}
    build_judge_flow().run(shared)
    output = shared.get("output", "{}")
    return json.loads(output)


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 3:
        q = sys.argv[1]
        r = sys.argv[2]
    else:
        q = "What is the difference between a process and a thread in operating systems?"
        r = (
            "A process is an independent program in execution with its own memory space, "
            "while a thread is a lighter-weight unit of execution that shares memory with "
            "other threads within the same process. Processes are isolated from each other, "
            "making them safer but slower to communicate; threads share the same address space, "
            "enabling faster communication at the cost of requiring synchronisation (e.g. locks) "
            "to avoid race conditions."
        )

    result = run_judge(q, r)
    print("\nJSON output saved to shared['output']")