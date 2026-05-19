"""Common types and result structures for spl3 compare."""

from __future__ import annotations
from typing import Any, Optional, Union
from dataclasses import dataclass, field

@dataclass
class ComparisonResult:
    """Consolidated comparison result across all tiers."""
    file1: str
    file2: str
    ext: str
    timestamp: str
    modes: list[str]
    results: dict[str, Any] = field(default_factory=dict)
    synthesis: Optional[dict[str, Any]] = None

@dataclass
class GEDResult:
    distance: float
    normalized_distance: float
    node_count: list[int]
    edge_count: list[int]
    node_types: list[dict[str, int]]

@dataclass
class BERTScoreResult:
    precision: float
    recall: float
    f1: float

@dataclass
class RougeResult:
    rouge1_precision: float
    rouge1_recall: float
    rouge1_f1: float
    rouge2_precision: float
    rouge2_recall: float
    rouge2_f1: float
    rougeL_precision: float
    rougeL_recall: float
    rougeL_f1: float
