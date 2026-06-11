from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional

# ---------------------------------------------------------------------------
# Trust badges (B-4) — a badge *set* on two orthogonal axes, not one ladder.
# See docs/DEV/sage_lean_integration_plan.md §B.1 (D1 resolved): the grades
# attest different things — claim badges attest the mathematical content,
# exposition badges attest the prose/pedagogy. Within an axis the order is
# strict (machine_proved outranks machine_verified); across axes there is
# none. 'canonical' is the derived composite end state (top badge on both
# axes) — computed, never stored. 'machine_generated' is the unbadged
# baseline: the empty set.
# ---------------------------------------------------------------------------

CLAIM_BADGES = [
    "machine_verified",   # CAS instance check (sympy/sage) — this example works
    "machine_proved",     # Lean kernel-checked statement — the theorem itself
]

EXPOSITION_BADGES = [
    "ai_reviewed",        # LLM judge PASS (spl3 judge)
    "human_verified",     # human review
]

ALL_BADGES = CLAIM_BADGES + EXPOSITION_BADGES

# Legacy pre-B-4 single-ordinal tiers — kept only for DB migration and the
# `provenance=` compatibility kwarg. New code uses badge sets.
PROVENANCE_TIERS = [
    "machine_generated",
    "machine_verified",
    "ai_reviewed",
    "human_verified",
]


def provenance_rank(tier: str) -> int:
    """Rank in the legacy ordinal; -1 if unknown. Migration/compat only."""
    try:
        return PROVENANCE_TIERS.index(tier)
    except ValueError:
        return -1


def badge_axis(badge: str) -> Optional[str]:
    """Return 'claim' or 'exposition'; None for unknown badges."""
    if badge in CLAIM_BADGES:
        return "claim"
    if badge in EXPOSITION_BADGES:
        return "exposition"
    return None


def badge_rank(badge: str) -> int:
    """Rank of a badge within its own axis; -1 if unknown.

    Ranks are only comparable between badges on the same axis.
    """
    if badge in CLAIM_BADGES:
        return CLAIM_BADGES.index(badge)
    if badge in EXPOSITION_BADGES:
        return EXPOSITION_BADGES.index(badge)
    return -1


def normalize_badges(badges: Iterable[str]) -> list[str]:
    """Validate and dedupe a badge collection into canonical order.

    Raises ValueError on unknown badge names ('machine_generated' is not a
    badge — it is the empty set).
    """
    unique = set(badges)
    unknown = unique - set(ALL_BADGES)
    if unknown:
        raise ValueError(
            f"Unknown badge(s): {sorted(unknown)}. Valid: {ALL_BADGES}"
        )
    return [b for b in ALL_BADGES if b in unique]


def badges_from_provenance(tier: str) -> list[str]:
    """Map a legacy single-ordinal tier to a badge set (migration/compat)."""
    if tier in ("", "machine_generated"):
        return []
    return normalize_badges([tier])


def satisfies(badges: Iterable[str], min_badge: str) -> bool:
    """True if the set holds a badge on min_badge's axis at >= its rank.

    Cross-axis badges never satisfy each other: ai_reviewed does not imply
    machine_verified (the pre-B-4 ordinal got this wrong).
    """
    axis = badge_axis(min_badge)
    if axis is None:
        raise ValueError(f"Unknown badge: {min_badge!r}. Valid: {ALL_BADGES}")
    need = badge_rank(min_badge)
    return any(
        badge_axis(b) == axis and badge_rank(b) >= need for b in badges
    )


def is_canonical(badges: Iterable[str]) -> bool:
    """Derived composite end state: top badge present on BOTH axes."""
    held = set(badges)
    return CLAIM_BADGES[-1] in held and EXPOSITION_BADGES[-1] in held


@dataclass
class CacheEntry:
    key: str
    concept: str
    content: str
    content_hash: str
    rubric_version: str
    dep_hashes: dict[str, str]
    params: dict
    adapter: str
    model: str
    token_cost: int
    created_at: str
    hit_count: int
    # Trust badge set (B-4) — see module docstring; [] = machine_generated
    badges: list[str] = field(default_factory=list)
    stale: bool = False
    verdict: dict | None = None
    # Engine-of-record: which deterministic engine verified this content
    # ("sympy", "sage", "lean", ...; "" = unverified / not recorded).
    # Orthogonal to adapter/model, which record the *generation* engine.
    verifier: str = ""
    # Formal statement backing a machine_proved badge (the kernel-checked
    # Lean proposition), rendered alongside the prose wherever the badge
    # appears — the §B.4 correspondence-audit requirement.
    statement: str = ""

    @property
    def canonical(self) -> bool:
        return is_canonical(self.badges)


@dataclass
class CacheStats:
    total_entries: int
    by_badge: dict[str, int]
    unbadged: int
    canonical: int
    total_hits: int
    total_token_cost: int
    estimated_tokens_saved: int
    concepts: list[str]
    stale_count: int
