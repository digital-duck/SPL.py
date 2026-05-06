The spec file doesn't exist yet at the referenced path. Based on the NeurIPS-26-lab experiment context (R4-thinking = structured chain-of-thought reasoning round) and the established pattern, I'll implement the thinking workflow now.

```python
#!/usr/bin/env python3
"""
R4-Thinking: Structured Chain-of-Thought Reasoning Workflow
PocketFlow implementation — multi-step thinking with reflection and quality gate.
"""

import os
import sys
import json
import re
import subprocess

# ---------------------------------------------------------------------------
# Minimal PocketFlow-compatible runtime (fallback if pocketflow not installed)
# ---------------------------------------------------------------------------
try:
    from pocketflow import Node, Flow
except ImportError:

    class Node:
        def __init__(self):
            self._successors: dict = {}

        def __rshift__(self, other):
            self._successors["default"] = other
            return other

        def __sub__(self, action: str):
            return _Edge(self, action)

        def prep(self, shared):
            return None

        def exec(self, prep_res):
            return None

        def post(self, shared, prep_res, exec_res):
            return "default"

        def run(self, shared):
            prep_res = self.prep(shared)
            exec_res = self.exec(prep_res)
            action = self.post(shared, prep_res, exec_res) or "default"
            return action

    class _Edge:
        def __init__(self, node, action):
            self._node = node
            self._action = action

        def __rshift__(self, other):
            self._node._successors[self._action] = other
            return other

    class Flow:
        def __init__(self, start):
            self._start = start

        def run(self, shared):
            node = self._start
            while node is not None:
                action = node.run(shared)
                node = node._successors.get(action)
            return shared


# ---------------------------------------------------------------------------
# LLM helper
# ---------------------------------------------------------------------------
LLM_MODEL = os.environ.get("LLM_MODEL", "claude-opus-4-5")
MAX_ITERATIONS = int(os.environ.get("MAX_THINKING_ITERATIONS", "3"))
QUALITY_THRESHOLD = float(os.environ.get("QUALITY_THRESHOLD", "7.0"))


def call_llm(prompt: str, model: str = None) -> str:
    """
    Call LLM.  Priority:
      1. Claude CLI  (USE_CLAUDE_CLI != "0")
      2. OpenRouter  (OPENROUTER_API_KEY set)
      3. OpenAI      (OPENAI_API_KEY set)
    """
    model = model or LLM_MODEL

    if os.environ.get("USE_CLAUDE_CLI", "1") != "0":
        try:
            args = ["claude", "-p", prompt]
            if model:
                args += ["--model", model]
            result = subprocess.run(
                args, capture_output=True, text=True, timeout=180
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")

    if openrouter_key or openai_key:
        import urllib.request

        api_key = openrouter_key or openai_key
        base_url = (
            "https://openrouter.ai/api/v1/chat/completions"
            if openrouter_key
            else "https://api.openai.com/v1/chat/completions"
        )
        payload = json.dumps(
            {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
            }
        ).encode()
        req = urllib.request.Request(
            base_url,
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"].strip()

    raise RuntimeError(
        "No LLM available. Set USE_CLAUDE_CLI=1 or OPENROUTER_API_KEY or OPENAI_API_KEY."
    )


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


class ProblemAnalysisNode(Node):
    """Decompose the problem into type, constraints, and candidate approaches."""

    def prep(self, shared):
        return shared.get("problem", "")

    def exec(self, problem: str) -> dict:
        prompt = f"""Analyze the following problem and respond with ONLY valid JSON (no markdown, no prose).

Problem:
{problem}

JSON schema:
{{
  "problem_type": "<math|logic|reasoning|factual|creative|multi-step>",
  "difficulty": "<easy|medium|hard>",
  "key_constraints": ["<constraint1>", ...],
  "candidate_approaches": ["<approach1>", ...],
  "relevant_domains": ["<domain1>", ...]
}}"""
        raw = call_llm(prompt)
        try:
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            return json.loads(m.group()) if m else {}
        except Exception:
            return {
                "problem_type": "general",
                "difficulty": "medium",
                "key_constraints": [],
                "candidate_approaches": [],
                "relevant_domains": [],
            }

    def post(self, shared, prep_res, exec_res):
        shared["analysis"] = exec_res
        shared["iteration"] = 0
        shared["thinking_history"] = []
        print(
            f"  [Analysis] type={exec_res.get('problem_type')}  "
            f"difficulty={exec_res.get('difficulty')}"
        )
        return "default"


class ThinkingNode(Node):
    """Generate structured chain-of-thought reasoning, incorporating previous reflection."""

    def prep(self, shared):
        return {
            "problem": shared.get("problem", ""),
            "analysis": shared.get("analysis", {}),
            "iteration": shared.get("iteration", 0),
            "reflection": shared.get("last_reflection", ""),
        }

    def exec(self, ctx: dict) -> str:
        reflection_block = ""
        if ctx["reflection"]:
            reflection_block = f"""
A previous reflection identified these issues:
{ctx["reflection"]}

Address ALL of the above issues in your revised reasoning.
"""
        a = ctx["analysis"]
        prompt = f"""You are solving a problem with structured chain-of-thought reasoning.

Problem:
{ctx["problem"]}

Problem context:
- Type        : {a.get("problem_type", "general")}
- Difficulty  : {a.get("difficulty", "unknown")}
- Constraints : {", ".join(a.get("key_constraints", [])) or "none stated"}
- Domains     : {", ".join(a.get("relevant_domains", [])) or "general"}
- Approaches  : {", ".join(a.get("candidate_approaches", [])) or "open"}
{reflection_block}
Thinking iteration {ctx["iteration"] + 1} of {MAX_ITERATIONS}.

Instructions:
1. Work step-by-step — label each step (Step 1, Step 2, …).
2. At each step state WHAT you are doing and WHY.
3. Flag any assumption you make with [ASSUMPTION].
4. If you spot an error mid-reasoning, correct it explicitly.
5. End with a PRELIMINARY ANSWER summarising your conclusion.
"""
        return call_llm(prompt)

    def post(self, shared, prep_res, exec_res):
        shared["current_thinking"] = exec_res
        shared["thinking_history"].append(
            {"iteration": prep_res["iteration"], "thinking": exec_res}
        )
        shared["iteration"] = prep_res["iteration"] + 1
        print(f"  [Thinking] iteration {prep_res['iteration'] + 1} complete")
        return "default"


class ReflectionNode(Node):
    """Critique the latest chain-of-thought and emit a numeric quality score."""

    def prep(self, shared):
        return {
            "problem": shared.get("problem", ""),
            "thinking": shared.get("current_thinking", ""),
        }

    def exec(self, ctx: dict) -> str:
        prompt = f"""You are a rigorous reasoning evaluator.

Original problem:
{ctx["problem"]}

Chain-of-thought to evaluate:
{ctx["thinking"]}

Evaluate on these dimensions:
1. Logical validity — are all inference steps sound?
2. Completeness    — does the reasoning cover all relevant cases?
3. Correctness     — is the preliminary answer correct?
4. Clarity         — is each step clearly explained?
5. Efficiency      — is there unnecessary complexity or repetition?

Respond in exactly this format (no extra text):
ISSUES: <comma-separated list of issues, or "none">
IMPROVEMENTS: <specific, actionable suggestions>
SCORE: <integer 1-10>
VERDICT: <one-sentence summary>

Scoring guide:
  1–3  Major errors; significant rethinking needed.
  4–6  Moderate issues; targeted refinement would help.
  7–8  Good reasoning; only minor polish needed.
  9–10 Excellent; essentially no improvement needed.
"""
        return call_llm(prompt)

    def post(self, shared, prep_res, exec_res):
        shared["last_reflection"] = exec_res
        score = 5.0
        m = re.search(r"SCORE:\s*(\d+(?:\.\d+)?)", exec_res)
        if m:
            score = min(10.0, max(0.0, float(m.group(1))))
        shared["quality_score"] = score
        print(
            f"  [Reflection] score={score:.1f}  "
            f"(threshold={QUALITY_THRESHOLD}, iter={shared['iteration']}/{MAX_ITERATIONS})"
        )
        return "default"


class QualityGateNode(Node):
    """Decide whether to refine the thinking or proceed to final synthesis."""

    def prep(self, shared):
        return {
            "score": shared.get("quality_score", 0.0),
            "iteration": shared.get("iteration", 0),
        }

    def exec(self, ctx):
        return ctx

    def post(self, shared, prep_res, exec_res):
        score = exec_res["score"]
        iteration = exec_res["iteration"]
        if score >= QUALITY_THRESHOLD or iteration >= MAX_ITERATIONS:
            print(
                f"  [QualityGate] → finalize  "
                f"(score={score:.1f}, iter={iteration})"
            )
            return "finalize"
        print(
            f"  [QualityGate] → refine  "
            f"(score={score:.1f} < {QUALITY_THRESHOLD})"
        )
        return "refine"


class FinalAnswerNode(Node):
    """Synthesise a clear final answer from the best reasoning chain."""

    def prep(self, shared):
        return {
            "problem": shared.get("problem", ""),
            "thinking": shared.get("current_thinking", ""),
            "reflection": shared.get("last_reflection", ""),
            "score": shared.get("quality_score", 0.0),
            "iterations": shared.get("iteration", 0),
        }

    def exec(self, ctx: dict) -> str:
        prompt = f"""You have completed a structured reasoning process.  Now write the final answer.

Original problem:
{ctx["problem"]}

Best reasoning chain (quality score {ctx["score"]:.1f}/10):
{ctx["thinking"]}

Reviewer feedback:
{ctx["reflection"]}

Write the FINAL ANSWER:
- State the answer directly and unambiguously in the first sentence.
- Provide a concise summary of the key reasoning steps (3–5 bullet points).
- Note any important caveats or edge cases.
- If the problem is ambiguous, explain any interpretations made.
"""
        return call_llm(prompt)

    def post(self, shared, prep_res, exec_res):
        shared["final_answer"] = exec_res
        shared["metadata"] = {
            "model": LLM_MODEL,
            "iterations": prep_res["iterations"],
            "final_quality_score": prep_res["score"],
            "max_iterations_allowed": MAX_ITERATIONS,
            "quality_threshold": QUALITY_THRESHOLD,
        }
        return "default"


# ---------------------------------------------------------------------------
# Flow builder
# ---------------------------------------------------------------------------


def build_flow() -> Flow:
    problem_analysis = ProblemAnalysisNode()
    thinking = ThinkingNode()
    reflection = ReflectionNode()
    quality_gate = QualityGateNode()
    final_answer = FinalAnswerNode()

    problem_analysis >> thinking
    thinking >> reflection
    reflection >> quality_gate
    (quality_gate - "finalize") >> final_answer
    (quality_gate - "refine") >> thinking

    return Flow(start=problem_analysis)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_thinking_workflow(problem: str) -> dict:
    """Run the structured thinking workflow and return the full result dict."""
    shared: dict = {"problem": problem}

    sep = "=" * 64
    print(f"\n{sep}")
    print("STRUCTURED THINKING WORKFLOW")
    print(f"Problem : {problem[:120]}{'...' if len(problem) > 120 else ''}")
    print(f"Model   : {LLM_MODEL}")
    print(f"MaxIter : {MAX_ITERATIONS}   Threshold : {QUALITY_THRESHOLD}/10")
    print(sep)

    flow = build_flow()
    flow.run(shared)

    print(f"\n{sep}")
    print("FINAL ANSWER")
    print(sep)
    print(shared.get("final_answer", "(no answer produced)"))
    print(f"\nMetadata: {json.dumps(shared.get('metadata', {}), indent=2)}")

    return {
        "problem": problem,
        "final_answer": shared.get("final_answer", ""),
        "thinking_history": shared.get("thinking_history", []),
        "analysis": shared.get("analysis", {}),
        "quality_score": shared.get("quality_score", 0.0),
        "iterations_used": shared.get("iteration", 0),
        "metadata": shared.get("metadata", {}),
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    default_problem = (
        "A snail is at the bottom of a 30-foot well. "
        "Each day it climbs 3 feet and each night it slides back 2 feet. "
        "How many days does it take for the snail to reach the top?"
    )
    problem = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else default_problem
    run_thinking_workflow(problem)