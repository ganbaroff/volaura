"""AURA score calculation.

Aggregates per-competency theta scores (0-100) into a single weighted AURA
score, assigns badge tier, and determines elite status.

Weights are FIXED per the spec — do not change without product sign-off.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime

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

# Temporal decay constants — Ebbinghaus two-phase model (Gemini research, 2026-03-26)
# Phase 1 (0-30 days): rapid initial decay matching forgetting curve steepness
# Phase 2 (30+ days): slower long-term decay for consolidated knowledge
# Floor at 60% — inactivity cannot erase earned competency.
_DECAY_PHASE1_DAYS: float = 30.0  # boundary between fast and slow decay
_DECAY_PHASE1_RATE: float = 0.70  # retain 70% after 30 days (sharp Ebbinghaus drop)
_DECAY_FLOOR: float = 0.60

# Per-competency Phase 2 half-lives (days) — differentiated by skill decay research
# (Gemini/Kimi research, 2026-03-26: uniform 180-day scale frustrates Gen Z users)
# tech/event skills decay faster (practise-dependent), soft skills very durable.
# Formula: score retains 80% per HALF_LIFE days beyond day 30.
_COMPETENCY_HALF_LIVES: dict[str, float] = {
    "tech_literacy": 730.0,  # 2 yr — practice-dependent, but core knowledge durable
    "event_performance": 730.0,  # 2 yr — event-tied; resets naturally with participation
    "english_proficiency": 1095.0,  # 3 yr — language retention high once acquired
    "communication": 1460.0,  # 4 yr — core soft skill, very durable
    "reliability": 1460.0,  # 4 yr — behavioural trait, not easily forgotten
    "adaptability": 1460.0,  # 4 yr — dispositional, stable over time
    "leadership": 1640.0,  # 4.5 yr — identity-level competency, most durable
    "empathy_safeguarding": 1640.0,  # 4.5 yr — values-based, extremely stable
}

# Weighted-average half-life for overall total_score decay
# = sum(COMPETENCY_WEIGHTS[c] * _COMPETENCY_HALF_LIVES[c]) for all competencies
# Pre-computed: ~1295 days (~3.5 yr) — used when no specific competency slug given.
_DECAY_PHASE2_HALF_LIFE_DEFAULT: float = round(
    sum(COMPETENCY_WEIGHTS[c] * _COMPETENCY_HALF_LIVES[c] for c in COMPETENCY_WEIGHTS),
    1,
)


def clamp_competency_score(score: float) -> float:
    """Clamp a competency score to the valid [0, 100] range.

    S8.3: Prevents out-of-bounds values from reaching the RPC call.
    The IRT theta→score conversion can theoretically produce values outside
    [0, 100] due to floating-point edge cases or corrupted session data.
    This layer catches it before it propagates to the DB.
    """
    return max(0.0, min(100.0, score))


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
    high_count = sum(1 for score in competency_scores.values() if score >= ELITE_COMPETENCY_THRESHOLD)
    return high_count >= ELITE_COMPETENCY_COUNT


def calculate_effective_score(
    raw_score: float,
    last_updated: datetime | None,
    competency_slug: str | None = None,
) -> float:
    """Apply temporal decay to an AURA score based on inactivity period.

    Uses per-competency half-lives so soft skills decay slower than technical ones.
    (Research basis: Gemini/Kimi 2026-03-26 — uniform 180-day decay frustrates Gen Z.)

    Phase 1 (0-30 days): linear drop from 100% → 70% (Ebbinghaus initial steep drop)
    Phase 2 (>30 days): exponential, retaining 80% per competency-specific half-life.
    Floor at 60% — inactivity cannot fully erase earned competency.

    Args:
        raw_score: stored AURA total_score or per-competency score (0-100)
        last_updated: timestamp of last score update (UTC)
        competency_slug: optional competency identifier; if given, uses its specific
            half-life. If None, uses the weighted-average half-life for total_score.

    Returns:
        Effective score after decay applied (0-100).
    """
    if raw_score <= 0:
        return 0.0  # Guard: negative/zero scores don't propagate (data corruption safety)
    if last_updated is None:
        return raw_score

    now = datetime.now(UTC)
    # Normalise naive timestamps
    if last_updated.tzinfo is None:
        last_updated = last_updated.replace(tzinfo=UTC)

    days_inactive = max(0.0, (now - last_updated).total_seconds() / 86400.0)

    # Select half-life: per-competency if slug given and known, else weighted average
    if competency_slug and competency_slug not in _COMPETENCY_HALF_LIVES:
        from loguru import logger

        logger.warning("Unknown competency_slug for decay — using default", slug=competency_slug)
    half_life = _COMPETENCY_HALF_LIVES.get(competency_slug or "", _DECAY_PHASE2_HALF_LIFE_DEFAULT)

    # Two-phase Ebbinghaus decay:
    # Phase 1 (≤30 days): rapid initial forgetting — linear interpolation to 70% at day 30
    # Phase 2 (>30 days): slow consolidation — exponential from 70%, half-life per competency
    if days_inactive <= _DECAY_PHASE1_DAYS:
        # Linear drop from 1.0 at day 0 to PHASE1_RATE at day 30
        decay_factor = 1.0 - (1.0 - _DECAY_PHASE1_RATE) * (days_inactive / _DECAY_PHASE1_DAYS)
    else:
        # Start from phase1 endpoint, apply slow exponential beyond day 30
        days_beyond_phase1 = days_inactive - _DECAY_PHASE1_DAYS
        slow_decay = math.pow(0.80, days_beyond_phase1 / half_life)
        decay_factor = _DECAY_PHASE1_RATE * slow_decay

    decay_factor = max(_DECAY_FLOOR, decay_factor)

    return round(raw_score * decay_factor, 2)


def apply_activity_boost(score: float, events_attended_recent: int) -> float:
    """Boost AURA effective score based on recent event participation.

    Research basis (Kimi/Gemini, 2026-03-26): active volunteers retain skills
    better — event participation should counteract temporal decay.

    Each recent event (last 90 days) adds +5%, capped at +25% for 5+ events.
    Applied AFTER decay so active volunteers are rewarded, not just decay-resistant.

    Args:
        score: effective score after decay (output of calculate_effective_score)
        events_attended_recent: events attended in the last 90 days

    Returns:
        Boosted score, capped at 100.0
    """
    if events_attended_recent <= 0:
        return score
    boost_factor = 1.0 + 0.05 * min(events_attended_recent, 5)
    return min(100.0, round(score * boost_factor, 2))
