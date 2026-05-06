## R4-Thinking: Structured Chain-of-Thought Reasoning Workflow

### Overview

This PocketFlow workflow implements **structured chain-of-thought (CoT) reasoning with iterative self-reflection and a quality gate**. It mirrors the reasoning style of extended-thinking models (DeepSeek-R1, Claude thinking, OpenAI o1) without requiring a special model API — any LLM can be used.

The workflow decomposes a problem, generates step-by-step reasoning, critiques its own output, and iterates until a quality threshold is reached before producing a final answer.

### Requirements

```bash
pip install pocketflow        # optional — a minimal fallback is bundled
```

No other third-party packages are required. The LLM is invoked via the Claude CLI, OpenRouter, or OpenAI API.

### Setup — environment variables

| Variable | Default | Purpose |
|---|---|---|
| `LLM_MODEL` | `claude-opus-4-5` | Model name passed to the LLM backend |
| `USE_CLAUDE_CLI` | `1` | Set to `0` to skip the Claude CLI |
| `OPENROUTER_API_KEY` | — | OpenRouter API key (fallback) |
| `OPENAI_API_KEY` | — | OpenAI API key (fallback) |
| `MAX_THINKING_ITERATIONS` | `3` | Maximum refinement loops |
| `QUALITY_THRESHOLD` | `7.0` | Minimum reflection score (1–10) to accept |

For Claude CLI usage (default), ensure the `claude` binary is installed and authenticated:

```bash
# Claude CLI must be installed and logged in
claude --version
```

For OpenRouter:

```bash
export USE_CLAUDE_CLI=0
export OPENROUTER_API_KEY=sk-or-...
export LLM_MODEL=anthropic/claude-opus-4-5
```

### Usage

```bash
# Default built-in problem
python flow.py

# Custom problem via CLI
python flow.py "If a train leaves Chicago at 60 mph and another leaves New York at 80 mph, and they are 900 miles apart, when do they meet?"

# Adjust iteration limits
MAX_THINKING_ITERATIONS=5 QUALITY_THRESHOLD=8.0 python flow.py "Prove that √2 is irrational."
```

### Expected output

```
================================================================
STRUCTURED THINKING WORKFLOW
Problem : A snail is at the bottom of a 30-foot well...
Model   : claude-opus-4-5
MaxIter : 3   Threshold : 7.0/10
================================================================
  [Analysis] type=math  difficulty=medium
  [Thinking] iteration 1 complete
  [Reflection] score=8.5  (threshold=7.0, iter=1/3)
  [QualityGate] → finalize  (score=8.5, iter=1)

================================================================
FINAL ANSWER
================================================================
The snail reaches the top on day 28.

Key reasoning:
• Net progress per full day-night cycle: +1 foot
• After 27 cycles the snail is at 27 feet
• On day 28 it climbs 3 feet to 30 feet and exits before sliding back

Metadata: {
  "model": "claude-opus-4-5",
  "iterations": 1,
  "final_quality_score": 8.5,
  ...
}
```

### Workflow step-by-step

```
Input problem
      │
      ▼
ProblemAnalysisNode
  • Calls LLM to classify problem type, difficulty,
    constraints, candidate approaches, relevant domains.
  • Emits JSON analysis stored in shared["analysis"].
      │
      ▼
ThinkingNode  ◄──────────────────────────────────────┐
  • Generates numbered step-by-step CoT reasoning.   │
  • Incorporates prior reflection if this is a       │
    refinement iteration.                            │
  • Appends result to shared["thinking_history"].    │
      │                                              │
      ▼                                              │
ReflectionNode                                       │
  • Critiques the reasoning on 5 dimensions.         │
  • Emits structured ISSUES / IMPROVEMENTS /         │
    SCORE / VERDICT.                                 │
  • Parses numeric score into shared["quality_score"].│
      │                                              │
      ▼                                              │
QualityGateNode                                      │
  • score >= threshold OR iterations >= max  →  "finalize"
  • otherwise                               →  "refine" ──┘
      │
   "finalize"
      ▼
FinalAnswerNode
  • Synthesises the final answer from the best
    reasoning chain + reviewer feedback.
  • Stores result in shared["final_answer"].
      │
      ▼
    Output
```