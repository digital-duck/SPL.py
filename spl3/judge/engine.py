"""Single-judge and panel-judge engine."""

from __future__ import annotations
import asyncio
import json
import re
from typing import Optional

from spl3.judge.types import JudgeResult, PanelResult, Rubric
from spl3.judge.prompt import build_judge_prompt


def _parse_verdict(raw: str, rubric: Rubric, adapter: str, model: str) -> JudgeResult:
    """Extract structured JudgeResult from LLM response."""
    text = raw if isinstance(raw, str) else getattr(raw, "content", str(raw))

    # Try to extract the JSON block first
    m = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if not m:
        # Fall back to first bare JSON object
        m = re.search(r"\{.*\}", text, re.DOTALL)

    if m:
        try:
            data = json.loads(m.group(1) if "```" in m.group(0) else m.group(0))
            verdict = str(data.get("verdict", "ESCALATE")).upper()
            if verdict not in ("PASS", "FAIL", "ESCALATE"):
                verdict = "ESCALATE"
            score = float(data.get("score", 0.0))
            confidence = str(data.get("confidence", "LOW")).upper()
            if confidence not in ("HIGH", "MEDIUM", "LOW"):
                confidence = "LOW"
            criteria_scores: dict[str, float] = {
                c: float(data.get("criteria_scores", {}).get(c, 0.0))
                for c in rubric.criteria
            }
            return JudgeResult(
                verdict=verdict,
                score=score,
                confidence=confidence,
                reasoning=str(data.get("reasoning", "")),
                feedback=str(data.get("feedback", "")),
                criteria_scores=criteria_scores,
                model=model or "",
                adapter=adapter,
                rubric=rubric.name,
            )
        except (json.JSONDecodeError, ValueError, KeyError):
            pass

    # Fallback: parse prose heuristically
    verdict = "ESCALATE"
    for candidate in ("PASS", "FAIL", "ESCALATE"):
        if candidate in text.upper():
            verdict = candidate
            break

    score_m = re.search(r"overall score[:\s]+([0-9]+(?:\.[0-9]+)?)", text, re.IGNORECASE)
    score = float(score_m.group(1)) if score_m else 0.0

    confidence = "LOW"
    for c in ("HIGH", "MEDIUM", "LOW"):
        if c in text.upper():
            confidence = c
            break

    return JudgeResult(
        verdict=verdict,
        score=score,
        confidence=confidence,
        reasoning=text[:500],
        feedback="(parse error — see reasoning for raw LLM output)",
        criteria_scores={c: 0.0 for c in rubric.criteria},
        model=model or "",
        adapter=adapter,
        rubric=rubric.name,
    )


async def run_judge(
    content: str,
    rubric: Rubric,
    adapter_name: str,
    model: Optional[str] = None,
    swap_check: bool = False,
) -> JudgeResult:
    from spl3.adapters import get_adapter

    prompt = build_judge_prompt(content, rubric)
    llm = get_adapter(adapter_name, **({"model": model} if model else {}))
    raw = await llm.generate(prompt, **({"model": model} if model else {}))
    result = _parse_verdict(raw, rubric, adapter_name, model or "")

    if swap_check:
        result.swap_consistent = await _run_swap_check(content, rubric, llm, model, result)

    return result


async def run_panel(
    content: str,
    rubric: Rubric,
    members: list[tuple[str, Optional[str]]],
    aggregation: str = "majority",
    swap_check: bool = False,
) -> PanelResult:
    """Run multiple judges concurrently and aggregate into a PanelResult."""
    from spl3.judge.aggregators import aggregate

    tasks = [
        run_judge(content, rubric, adapter, model, swap_check)
        for adapter, model in members
    ]
    results = await asyncio.gather(*tasks)
    return aggregate(results, aggregation, rubric.name)


async def _run_swap_check(
    content: str,
    rubric: Rubric,
    llm,
    model: Optional[str],
    original: JudgeResult,
) -> bool:
    """Re-run judge with reversed criterion order; return True if verdict agrees."""
    reversed_rubric = Rubric(
        name=rubric.name,
        criteria=list(reversed(rubric.criteria)),
        pass_threshold=rubric.pass_threshold,
        weight=rubric.weight,
        prompt_template=rubric.prompt_template,
    )
    prompt = build_judge_prompt(content, reversed_rubric)
    raw2 = await llm.generate(prompt, **({"model": model} if model else {}))
    result2 = _parse_verdict(raw2, rubric, original.adapter, original.model)
    return result2.verdict == original.verdict
