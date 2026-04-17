"""Unit tests for stats router schemas and rate computation logic."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.routers.stats import BetaFunnelStats, PublicStatsResponse


class TestPublicStatsResponse:
    def test_valid(self):
        r = PublicStatsResponse(
            total_professionals=150,
            total_assessments=42,
            total_events=5,
            avg_aura_score=73.2,
        )
        assert r.total_professionals == 150
        assert r.avg_aura_score == 73.2

    def test_zeros(self):
        r = PublicStatsResponse(
            total_professionals=0,
            total_assessments=0,
            total_events=0,
            avg_aura_score=0.0,
        )
        assert r.total_professionals == 0

    def test_missing_field_rejected(self):
        with pytest.raises(ValidationError):
            PublicStatsResponse(
                total_professionals=10,
                total_assessments=5,
                total_events=3,
            )


class TestBetaFunnelStats:
    def test_valid(self):
        r = BetaFunnelStats(
            sessions_started=100,
            sessions_completed=60,
            sessions_abandoned=15,
            completion_rate=0.6,
            abandonment_rate=0.15,
            registrations=200,
            aura_scores_generated=55,
        )
        assert r.completion_rate == 0.6
        assert r.abandonment_rate == 0.15

    def test_zero_started(self):
        r = BetaFunnelStats(
            sessions_started=0,
            sessions_completed=0,
            sessions_abandoned=0,
            completion_rate=0.0,
            abandonment_rate=0.0,
            registrations=0,
            aura_scores_generated=0,
        )
        assert r.completion_rate == 0.0

    def test_missing_field_rejected(self):
        with pytest.raises(ValidationError):
            BetaFunnelStats(
                sessions_started=10,
                sessions_completed=5,
            )


class TestCompletionRateLogic:
    @pytest.mark.parametrize(
        "started,completed,expected_rate",
        [
            (100, 60, 0.6),
            (100, 0, 0.0),
            (100, 100, 1.0),
            (3, 1, 0.333),
            (0, 0, 0.0),
        ],
    )
    def test_completion_rate_formula(self, started: int, completed: int, expected_rate: float):
        rate = round(completed / started, 3) if started > 0 else 0.0
        assert rate == expected_rate

    @pytest.mark.parametrize(
        "started,abandoned,expected_rate",
        [
            (100, 15, 0.15),
            (100, 0, 0.0),
            (0, 0, 0.0),
            (200, 50, 0.25),
        ],
    )
    def test_abandonment_rate_formula(self, started: int, abandoned: int, expected_rate: float):
        rate = round(abandoned / started, 3) if started > 0 else 0.0
        assert rate == expected_rate
