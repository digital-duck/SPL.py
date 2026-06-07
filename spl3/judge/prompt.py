"""Judge prompt construction."""

from __future__ import annotations
from spl3.judge.types import Rubric


def build_judge_prompt(content: str, rubric: Rubric) -> str:
    criteria_list = "\n".join(
        f"  - {c} (weight: {rubric.effective_weight(c):.2f})"
        for c in rubric.criteria
    )
    custom_template = rubric.prompt_template.strip()
    rubric_context = f"\n\n{custom_template}" if custom_template else ""

    return f"""You are an expert evaluator. Assess the following content against the rubric \
"{rubric.name}".{rubric_context}

**Criteria to evaluate** (score each 1–10):
{criteria_list}

**Pass threshold:** {rubric.pass_threshold} / 10

**Content to evaluate:**
```
{content}
```

Follow this exact chain-of-thought structure in your response:

## Criteria Scores
For each criterion, write:
  <criterion>: <score>/10 — <one-sentence justification>

## Overall Assessment
Overall score: <weighted mean, one decimal>
Confidence: HIGH | MEDIUM | LOW
Verdict: PASS | FAIL | ESCALATE

Use ESCALATE only when the content is ambiguous or contradictory enough that a human \
reviewer is needed.

## Feedback
Provide up to 3 actionable bullet points for improvement (omit if verdict is PASS and \
score ≥ {rubric.pass_threshold + 1.0}).

## JSON Summary
Respond with this JSON block (required, parse-friendly):
```json
{{
  "verdict": "PASS|FAIL|ESCALATE",
  "score": <float>,
  "confidence": "HIGH|MEDIUM|LOW",
  "criteria_scores": {{{", ".join(f'"{c}": <float>' for c in rubric.criteria)}}},
  "reasoning": "<summary of chain-of-thought>",
  "feedback": "<actionable feedback, or empty string if none>"
}}
```"""
