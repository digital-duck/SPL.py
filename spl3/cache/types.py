from __future__ import annotations

from dataclasses import dataclass

PROVENANCE_TIERS = [
    "machine_generated",
    "machine_verified",
    "ai_reviewed",
    "human_verified",
]


def provenance_rank(tier: str) -> int:
    """Return numeric rank of a provenance tier; -1 if unknown."""
    try:
        return PROVENANCE_TIERS.index(tier)
    except ValueError:
        return -1


@dataclass
class CacheEntry:
    key: str
    concept: str
    content: str
    content_hash: str
    provenance: str
    rubric_version: str
    dep_hashes: dict[str, str]
    params: dict
    adapter: str
    model: str
    token_cost: int
    created_at: str
    hit_count: int
    stale: bool = False
    verdict: dict | None = None


@dataclass
class CacheStats:
    total_entries: int
    by_provenance: dict[str, int]
    total_hits: int
    total_token_cost: int
    estimated_tokens_saved: int
    concepts: list[str]
    stale_count: int
