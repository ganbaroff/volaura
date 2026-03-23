"""AURA score calculation.

Aggregates per-competency theta scores (0-100) into a single weighted AURA
score, assigns badge tier, and determines elite status.

Weights are FIXED per the spec — do not change without product sign-off.
"""

from __future__ import annotations

COMPETENCY_WEIGHTS: dict[str, float] = {
    "communication": 0.20,
    "reliability": 0.15,
    "english_proficiency": 0.15,
    "leadership": 0.15,
    "event_performance": 0.10,
    "tech_literacy": 0.10,
    "adaptability": 0.10,
    "empathy_safeguarding": 0.05,
}

# Badge tiers (overall AURA score thresholds)
BADGE_TIERS = [
    ("platinum", 90.0),
    ("gold", 75.0),
    ("silver", 60.0),
    ("bronze", 40.0),
]

# Elite requires overall ≥ 75 AND at least 2 competencies ≥ 75
ELITE_AURA_THRESHOLD = 75.0
ELITE_COMPETENCY_THRESHOLD = 75.0
ELITE_COMPETENCY_COUNT = 2


def calculate_overall(competency_scores: dict[str, float]) -> float:
    """Compute the weighted AURA score from per-competency scores (0-100).

    Missing competencies contribute 0 (not yet assessed).

    Returns:
        Overall AURA score 0.0–100.0.
    """
    total = 0.0
    for slug, weight in COMPETENCY_WEIGHTS.items():
        score = competency_scores.get(slug, 0.0)
        total += score * weight
    return round(max(0.0, min(100.0, total)), 2)


def get_badge_tier(overall: float) -> str:
    """Return badge tier string for a given overall AURA score."""
    for tier, threshold in BADGE_TIERS:
        if overall >= threshold:
            return tier
    return "none"


def is_elite(overall: float, competency_scores: dict[str, float]) -> bool:
    """Return True if the volunteer qualifies for elite status."""
    if overall < ELITE_AURA_THRESHOLD:
        return False
    high_count = sum(
        1 for score in competency_scores.values()
        if score >= ELITE_COMPETENCY_THRESHOLD
    )
    return high_count >= ELITE_COMPETENCY_COUNT
