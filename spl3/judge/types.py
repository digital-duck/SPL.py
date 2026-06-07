"""Core types for spl3 judge."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Rubric:
    name: str
    criteria: list[str]
    pass_threshold: float
    weight: dict[str, float] = field(default_factory=dict)
    prompt_template: str = ""

    def effective_weight(self, criterion: str) -> float:
        if self.weight:
            return self.weight.get(criterion, 1.0 / len(self.criteria))
        return 1.0 / len(self.criteria)


@dataclass
class JudgeResult:
    verdict: str                        # "PASS" | "FAIL" | "ESCALATE"
    score: float                        # 0.0 – 10.0
    confidence: str                     # "HIGH" | "MEDIUM" | "LOW"
    reasoning: str
    feedback: str
    criteria_scores: dict[str, float]
    model: str
    adapter: str
    rubric: str
    swap_consistent: Optional[bool] = None


@dataclass
class PanelResult:
    verdict: str                        # aggregated: "PASS" | "FAIL" | "ESCALATE"
    score: float                        # aggregated score
    confidence: str                     # "HIGH" | "MEDIUM" | "LOW"
    consensus: str                      # "UNANIMOUS" | "MAJORITY" | "SPLIT"
    individual: list[JudgeResult]       # one per panel member
    rubric: str
    aggregation: str                    # "majority" | "confidence_weighted" | "unanimous"
    dissent: Optional[str] = None       # minority summary when SPLIT
    swap_consistent: Optional[bool] = None  # None if swap check not run
