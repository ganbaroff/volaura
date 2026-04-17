"""Tests for app.services.tribe_streak_tracker — pure function coverage."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.services.tribe_streak_tracker import _iso_week


class TestIsoWeek:
    def test_known_date(self):
        dt = datetime(2026, 4, 18, 12, 0, 0, tzinfo=UTC)
        result = _iso_week(dt)
        iso = dt.isocalendar()
        assert result == f"{iso.year}-W{iso.week:02d}"

    def test_format_pattern(self):
        dt = datetime(2026, 1, 5, tzinfo=UTC)
        result = _iso_week(dt)
        assert result.startswith("202")
        assert "-W" in result
        week_num = int(result.split("-W")[1])
        assert 1 <= week_num <= 53

    def test_year_boundary_dec31(self):
        dt = datetime(2025, 12, 31, tzinfo=UTC)
        result = _iso_week(dt)
        assert "-W" in result

    def test_year_boundary_jan1(self):
        dt = datetime(2026, 1, 1, tzinfo=UTC)
        result = _iso_week(dt)
        assert "-W" in result

    def test_week_number_padded(self):
        dt = datetime(2026, 1, 5, tzinfo=UTC)
        result = _iso_week(dt)
        week_part = result.split("-W")[1]
        assert len(week_part) == 2

    @pytest.mark.parametrize(
        "month,day",
        [(3, 15), (6, 21), (9, 1), (12, 25)],
    )
    def test_various_dates(self, month: int, day: int):
        dt = datetime(2026, month, day, tzinfo=UTC)
        result = _iso_week(dt)
        assert isinstance(result, str)
        assert len(result) >= 7
