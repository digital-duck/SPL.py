"""Panel aggregation strategies for spl3 judge."""

from __future__ import annotations
from typing import Sequence

from spl3.judge.types import JudgeResult, PanelResult

_CONF_WEIGHT = {"HIGH": 3.0, "MEDIUM": 2.0, "LOW": 1.0}


def _consensus_label(verdicts: list[str], winning_verdict: str) -> str:
    if all(v == verdicts[0] for v in verdicts):
        return "UNANIMOUS"
    pass_count = verdicts.count("PASS")
    fail_count = verdicts.count("FAIL")
    esc_count  = verdicts.count("ESCALATE")
    majority_n = len(verdicts) / 2
    if max(pass_count, fail_count, esc_count) > majority_n:
        return "MAJORITY"
    return "SPLIT"


def _dissent_summary(results: Sequence[JudgeResult], winning_verdict: str) -> str | None:
    minority = [r for r in results if r.verdict != winning_verdict]
    if not minority:
        return None
    counts: dict[str, int] = {}
    for r in minority:
        counts[r.verdict] = counts.get(r.verdict, 0) + 1
    parts = [f"{v}×{n}" for v, n in sorted(counts.items())]
    sample_reasoning = minority[0].reasoning[:200] if minority[0].reasoning else ""
    summary = f"Minority ({', '.join(parts)})"
    if sample_reasoning:
        summary += f": {sample_reasoning}"
    return summary


def majority_vote(results: Sequence[JudgeResult], rubric_name: str) -> PanelResult:
    verdicts = [r.verdict for r in results]
    pass_n  = verdicts.count("PASS")
    fail_n  = verdicts.count("FAIL")
    esc_n   = verdicts.count("ESCALATE")
    total   = len(verdicts)

    if pass_n > total / 2:
        verdict = "PASS"
    elif fail_n > total / 2:
        verdict = "FAIL"
    else:
        verdict = "ESCALATE"  # tied or escalate majority

    consensus = _consensus_label(verdicts, verdict)
    score = sum(r.score for r in results) / total

    if consensus == "UNANIMOUS":
        confidence = "HIGH"
    elif verdict != "ESCALATE":
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    return PanelResult(
        verdict=verdict,
        score=round(score, 2),
        confidence=confidence,
        consensus=consensus,
        individual=list(results),
        rubric=rubric_name,
        aggregation="majority",
        dissent=_dissent_summary(results, verdict) if consensus != "UNANIMOUS" else None,
        swap_consistent=_panel_swap_consistent(results),
    )


def confidence_weighted(results: Sequence[JudgeResult], rubric_name: str) -> PanelResult:
    weights = [_CONF_WEIGHT.get(r.confidence, 1.0) for r in results]
    total_w = sum(weights)

    # Weighted vote per verdict
    vote: dict[str, float] = {"PASS": 0.0, "FAIL": 0.0, "ESCALATE": 0.0}
    for r, w in zip(results, weights):
        vote[r.verdict] = vote.get(r.verdict, 0.0) + w

    verdict = max(vote, key=lambda v: vote[v])
    # Tie → ESCALATE
    top_vals = sorted(vote.values(), reverse=True)
    if len(top_vals) >= 2 and top_vals[0] == top_vals[1]:
        verdict = "ESCALATE"

    score = sum(r.score * w for r, w in zip(results, weights)) / total_w
    verdicts = [r.verdict for r in results]
    consensus = _consensus_label(verdicts, verdict)
    confidence = "HIGH" if consensus == "UNANIMOUS" else "MEDIUM" if verdict != "ESCALATE" else "LOW"

    return PanelResult(
        verdict=verdict,
        score=round(score, 2),
        confidence=confidence,
        consensus=consensus,
        individual=list(results),
        rubric=rubric_name,
        aggregation="confidence_weighted",
        dissent=_dissent_summary(results, verdict) if consensus != "UNANIMOUS" else None,
        swap_consistent=_panel_swap_consistent(results),
    )


def unanimous(results: Sequence[JudgeResult], rubric_name: str) -> PanelResult:
    verdicts = [r.verdict for r in results]
    if all(v == "PASS" for v in verdicts):
        verdict    = "PASS"
        confidence = "HIGH"
        consensus  = "UNANIMOUS"
    else:
        verdict    = "ESCALATE"
        confidence = "HIGH" if all(v == verdicts[0] for v in verdicts) else "MEDIUM"
        consensus  = "UNANIMOUS" if all(v == verdicts[0] for v in verdicts) else (
            "MAJORITY" if any(verdicts.count(v) > len(verdicts) / 2 for v in set(verdicts))
            else "SPLIT"
        )

    score = min(r.score for r in results)  # conservative

    return PanelResult(
        verdict=verdict,
        score=round(score, 2),
        confidence=confidence,
        consensus=consensus,
        individual=list(results),
        rubric=rubric_name,
        aggregation="unanimous",
        dissent=_dissent_summary(results, verdict) if consensus != "UNANIMOUS" else None,
        swap_consistent=_panel_swap_consistent(results),
    )


def aggregate(
    results: Sequence[JudgeResult],
    strategy: str,
    rubric_name: str,
) -> PanelResult:
    if strategy == "confidence_weighted":
        return confidence_weighted(results, rubric_name)
    if strategy == "unanimous":
        return unanimous(results, rubric_name)
    return majority_vote(results, rubric_name)


def _panel_swap_consistent(results: Sequence[JudgeResult]) -> bool | None:
    """Aggregate swap_consistent: None if no judge ran swap-check; True only if all consistent."""
    checked = [r.swap_consistent for r in results if r.swap_consistent is not None]
    if not checked:
        return None
    return all(checked)
