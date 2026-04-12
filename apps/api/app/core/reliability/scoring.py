"""Behavioral reliability scoring engine.

6 signals aggregate into a reliability score (0-100).
Phases:
  - 0 events  → 100% behavioral
  - 1-4 events → blended (behavioral weight decreases linearly)
  - 5+ events  → 100% proven (event-history based)

Signal weights (must sum to 1.0):
  onboarding_velocity    15%
  assessment_completion  15%
  profile_completeness   10%
  sjt_reliability        30%  ← 3 masked SJT questions in assessment
  contact_verification   15%
  availability_specificity 15%
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ── Weights ───────────────────────────────────────────────────────────────────

SIGNAL_WEIGHTS: dict[str, float] = {
    "onboarding_velocity": 0.15,
    "assessment_completion": 0.15,
    "profile_completeness": 0.10,
    "sjt_reliability": 0.30,
    "contact_verification": 0.15,
    "availability_specificity": 0.15,
}

# Behavioral score range: 30–70 (neutral zone; no real event history yet)
BEHAVIORAL_MIN = 30.0
BEHAVIORAL_MAX = 70.0

# Phase transition thresholds
PHASE_FULL_PROVEN = 5  # 5+ events → 100% proven
PHASE_BLEND_START = 1  # 1 event → start blending

# No-show penalties (subtracted from proven score)
NO_SHOW_PENALTIES: dict[str, float] = {
    "ghost": -15.0,  # no contact at all
    "same_day": -10.0,  # cancelled same day
    "within_24h": -5.0,  # cancelled < 24 h before
    "within_48h": -2.0,  # cancelled 24–48 h before
    "advance": 0.0,  # cancelled 48 h+ before (no penalty)
}

# Recovery bonuses
FIRST_EVENT_BONUS = 5.0
SUCCESSFUL_ATTENDANCE_BONUS = 5.0


# ── Input models ──────────────────────────────────────────────────────────────


@dataclass
class BehavioralSignals:
    """Raw input signals collected during onboarding and assessment."""

    # Each in 0.0–1.0 range (fraction of completion / verification)
    onboarding_velocity: float = 0.5  # how quickly completed onboarding
    assessment_completion: float = 0.0  # fraction of competencies assessed
    profile_completeness: float = 0.0  # fraction of profile fields filled
    sjt_reliability: float = 0.5  # SJT masked question score
    contact_verification: float = 0.0  # email+phone verified = 1.0
    availability_specificity: float = 0.0  # how specific availability hours are


@dataclass
class EventHistory:
    """Aggregated event attendance record for proven scoring."""

    total_registered: int = 0
    total_attended: int = 0
    total_no_shows: int = 0
    no_show_types: list[str] = field(default_factory=list)
    # e.g. ["ghost", "same_day", "within_24h", "advance"]
    coordinator_avg_rating: float | None = None  # 1-5 or None


# ── Core functions ────────────────────────────────────────────────────────────


def behavioral_score(signals: BehavioralSignals) -> float:
    """Compute the behavioral reliability score (0–100) from input signals.

    Clamps to [BEHAVIORAL_MIN, BEHAVIORAL_MAX] to represent uncertainty.
    """
    raw = sum(getattr(signals, sig) * weight for sig, weight in SIGNAL_WEIGHTS.items())
    # Scale 0-1 → BEHAVIORAL_MIN to BEHAVIORAL_MAX
    scaled = BEHAVIORAL_MIN + raw * (BEHAVIORAL_MAX - BEHAVIORAL_MIN)
    return round(max(BEHAVIORAL_MIN, min(BEHAVIORAL_MAX, scaled)), 2)


def proven_score(history: EventHistory) -> float:
    """Compute the proven reliability score (0–100) from event history.

    Base = attendance rate * 100, then apply penalties and bonuses.
    """
    if history.total_registered == 0:
        return 50.0  # neutral default

    attendance_rate = history.total_attended / history.total_registered
    base = attendance_rate * 100.0

    # No-show penalties
    penalty = sum(NO_SHOW_PENALTIES.get(t, 0.0) for t in history.no_show_types)

    # Recovery bonuses
    bonus = 0.0
    if history.total_attended >= 1:
        bonus += FIRST_EVENT_BONUS
    if history.total_attended > 1:
        bonus += SUCCESSFUL_ATTENDANCE_BONUS * (history.total_attended - 1)

    # Coordinator rating bonus/penalty (±10 max)
    if history.coordinator_avg_rating is not None:
        rating_delta = (history.coordinator_avg_rating - 3.0) * 5.0  # 1→-10, 3→0, 5→+10
        base += rating_delta

    score = base + penalty + bonus
    return round(max(0.0, min(100.0, score)), 2)


def blended_score(
    b_score: float,
    p_score: float,
    events_attended: int,
) -> float:
    """Blend behavioral and proven scores based on events attended.

    0 events  → 100% behavioral
    1–4 events → linear blend toward proven
    5+ events → 100% proven
    """
    if events_attended <= 0:
        return b_score
    if events_attended >= PHASE_FULL_PROVEN:
        return p_score

    # Linear interpolation between phase start (1 event) and full proven (5)
    t = (events_attended - PHASE_BLEND_START) / (PHASE_FULL_PROVEN - PHASE_BLEND_START)
    t = max(0.0, min(1.0, t))
    return round(b_score * (1 - t) + p_score * t, 2)


def reliability_status(events_attended: int) -> str:
    """Return human-readable reliability phase label."""
    if events_attended >= PHASE_FULL_PROVEN:
        return "proven"
    if events_attended >= PHASE_BLEND_START:
        return "building"
    return "behavioral"


def calculate(
    signals: BehavioralSignals,
    history: EventHistory,
) -> dict[str, Any]:
    """Full reliability score calculation.

    Returns a dict compatible with the `aura_scores` table columns.
    """
    b = behavioral_score(signals)
    p = proven_score(history)
    final = blended_score(b, p, history.total_attended)
    status = reliability_status(history.total_attended)

    return {
        "reliability_score": final,
        "reliability_status": status,
        "events_attended": history.total_attended,
        "events_no_show": history.total_no_shows,
    }
