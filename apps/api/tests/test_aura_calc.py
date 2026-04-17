"""Unit tests for app.core.assessment.aura_calc — AURA score calculation."""

from datetime import UTC, datetime, timedelta

import pytest

from app.core.assessment.aura_calc import (
    _COMPETENCY_HALF_LIVES,
    _DECAY_FLOOR,
    _DECAY_PHASE1_DAYS,
    _DECAY_PHASE1_RATE,
    COMPETENCY_WEIGHTS,
    ELITE_AURA_THRESHOLD,
    ELITE_COMPETENCY_THRESHOLD,
    apply_activity_boost,
    calculate_effective_score,
    calculate_overall,
    clamp_competency_score,
    get_badge_tier,
    is_elite,
)

# ── clamp_competency_score ──────────────────────────────────────────────────


class TestClampCompetencyScore:
    def test_within_range(self):
        assert clamp_competency_score(50.0) == 50.0

    def test_below_zero(self):
        assert clamp_competency_score(-10.0) == 0.0

    def test_above_hundred(self):
        assert clamp_competency_score(110.0) == 100.0

    def test_zero(self):
        assert clamp_competency_score(0.0) == 0.0

    def test_hundred(self):
        assert clamp_competency_score(100.0) == 100.0


# ── calculate_overall ───────────────────────────────────────────────────────


class TestCalculateOverall:
    def test_all_perfect_scores(self):
        scores = {slug: 100.0 for slug in COMPETENCY_WEIGHTS}
        assert calculate_overall(scores) == 100.0

    def test_all_zero_scores(self):
        scores = {slug: 0.0 for slug in COMPETENCY_WEIGHTS}
        assert calculate_overall(scores) == 0.0

    def test_missing_competencies_contribute_zero(self):
        result = calculate_overall({"communication": 100.0})
        assert result == pytest.approx(100.0 * 0.20, abs=0.01)

    def test_empty_scores(self):
        assert calculate_overall({}) == 0.0

    def test_weights_sum_to_one(self):
        assert sum(COMPETENCY_WEIGHTS.values()) == pytest.approx(1.0)

    def test_specific_score(self):
        scores = {
            "communication": 80.0,
            "reliability": 70.0,
            "english_proficiency": 90.0,
            "leadership": 60.0,
            "event_performance": 50.0,
            "tech_literacy": 85.0,
            "adaptability": 75.0,
            "empathy_safeguarding": 65.0,
        }
        expected = sum(scores[k] * COMPETENCY_WEIGHTS[k] for k in COMPETENCY_WEIGHTS)
        assert calculate_overall(scores) == pytest.approx(round(expected, 2), abs=0.01)

    def test_clamped_below(self):
        scores = {slug: -50.0 for slug in COMPETENCY_WEIGHTS}
        assert calculate_overall(scores) == 0.0


# ── get_badge_tier ──────────────────────────────────────────────────────────


class TestGetBadgeTier:
    def test_platinum(self):
        assert get_badge_tier(95.0) == "platinum"

    def test_gold(self):
        assert get_badge_tier(80.0) == "gold"

    def test_silver(self):
        assert get_badge_tier(65.0) == "silver"

    def test_bronze(self):
        assert get_badge_tier(45.0) == "bronze"

    def test_none(self):
        assert get_badge_tier(30.0) == "none"

    def test_exact_platinum_boundary(self):
        assert get_badge_tier(90.0) == "platinum"

    def test_exact_gold_boundary(self):
        assert get_badge_tier(75.0) == "gold"

    def test_exact_silver_boundary(self):
        assert get_badge_tier(60.0) == "silver"

    def test_exact_bronze_boundary(self):
        assert get_badge_tier(40.0) == "bronze"

    def test_just_below_bronze(self):
        assert get_badge_tier(39.99) == "none"

    def test_zero(self):
        assert get_badge_tier(0.0) == "none"

    def test_hundred(self):
        assert get_badge_tier(100.0) == "platinum"


# ── is_elite ────────────────────────────────────────────────────────────────


class TestIsElite:
    def test_qualifies(self):
        scores = {
            "communication": 80.0,
            "reliability": 80.0,
            "leadership": 80.0,
        }
        assert is_elite(80.0, scores) is True

    def test_overall_too_low(self):
        scores = {"communication": 80.0, "reliability": 80.0}
        assert is_elite(70.0, scores) is False

    def test_not_enough_high_competencies(self):
        scores = {"communication": 80.0, "reliability": 50.0}
        assert is_elite(80.0, scores) is False

    def test_exactly_at_thresholds(self):
        scores = {
            "communication": ELITE_COMPETENCY_THRESHOLD,
            "reliability": ELITE_COMPETENCY_THRESHOLD,
        }
        assert is_elite(ELITE_AURA_THRESHOLD, scores) is True

    def test_empty_scores(self):
        assert is_elite(80.0, {}) is False


# ── calculate_effective_score (temporal decay) ──────────────────────────────


class TestCalculateEffectiveScore:
    def test_no_last_updated(self):
        assert calculate_effective_score(80.0, None) == 80.0

    def test_zero_score(self):
        assert calculate_effective_score(0.0, datetime.now(UTC)) == 0.0

    def test_negative_score(self):
        assert calculate_effective_score(-5.0, datetime.now(UTC)) == 0.0

    def test_no_decay_recent(self):
        now = datetime.now(UTC)
        result = calculate_effective_score(80.0, now)
        assert result == pytest.approx(80.0, abs=0.1)

    def test_phase1_decay_at_30_days(self):
        now = datetime.now(UTC)
        thirty_days_ago = now - timedelta(days=30)
        result = calculate_effective_score(100.0, thirty_days_ago)
        assert result == pytest.approx(100.0 * _DECAY_PHASE1_RATE, abs=1.0)

    def test_phase1_linear_at_15_days(self):
        now = datetime.now(UTC)
        fifteen_days_ago = now - timedelta(days=15)
        expected_factor = 1.0 - (1.0 - _DECAY_PHASE1_RATE) * (15.0 / _DECAY_PHASE1_DAYS)
        result = calculate_effective_score(100.0, fifteen_days_ago)
        assert result == pytest.approx(100.0 * expected_factor, abs=1.0)

    def test_floor_at_extreme_inactivity(self):
        ancient = datetime(2020, 1, 1, tzinfo=UTC)
        result = calculate_effective_score(100.0, ancient)
        assert result == pytest.approx(100.0 * _DECAY_FLOOR, abs=0.01)

    def test_naive_timestamp_handled(self):
        naive = datetime.now().replace(tzinfo=None)
        result = calculate_effective_score(80.0, naive)
        assert result == pytest.approx(80.0, abs=0.5)

    def test_competency_specific_decay(self):
        now = datetime.now(UTC)
        old = now - timedelta(days=365)
        tech = calculate_effective_score(100.0, old, "tech_literacy")
        leadership = calculate_effective_score(100.0, old, "leadership")
        assert tech <= leadership

    def test_unknown_competency_uses_default(self):
        now = datetime.now(UTC)
        old = now - timedelta(days=60)
        result = calculate_effective_score(100.0, old, "nonexistent_slug")
        assert 0 < result < 100

    def test_all_competencies_have_half_lives(self):
        for slug in COMPETENCY_WEIGHTS:
            assert slug in _COMPETENCY_HALF_LIVES


# ── apply_activity_boost ────────────────────────────────────────────────────


class TestApplyActivityBoost:
    def test_no_events_no_boost(self):
        assert apply_activity_boost(80.0, 0) == 80.0

    def test_negative_events_no_boost(self):
        assert apply_activity_boost(80.0, -1) == 80.0

    def test_one_event_boost(self):
        result = apply_activity_boost(80.0, 1)
        assert result == pytest.approx(80.0 * 1.05, abs=0.01)

    def test_five_events_max_boost(self):
        result = apply_activity_boost(80.0, 5)
        assert result == pytest.approx(80.0 * 1.25, abs=0.01)

    def test_more_than_five_capped(self):
        result_5 = apply_activity_boost(80.0, 5)
        result_10 = apply_activity_boost(80.0, 10)
        assert result_5 == result_10

    def test_capped_at_100(self):
        result = apply_activity_boost(95.0, 5)
        assert result <= 100.0
