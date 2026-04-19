"""Unit tests for app.services.tribe_streak_tracker."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.tribe_streak_tracker import (
    _iso_week,
    _update_user_streak,
    record_assessment_activity,
    update_weekly_streaks,
)

USER_ID = "u-streak-01"


def _mock_db(
    tribe_members=None,
    streak_data=None,
):
    db = MagicMock()
    cache = {}

    def _get_table(name):
        if name not in cache:
            cache[name] = _make_table(name, tribe_members, streak_data)
        return cache[name]

    db.table = MagicMock(side_effect=_get_table)
    return db


def _make_table(name, tribe_members, streak_data):
    tbl = MagicMock()

    if name == "tribe_members":
        chain = MagicMock()
        chain.is_.return_value = chain
        chain.execute = AsyncMock(return_value=MagicMock(data=tribe_members or []))
        tbl.select.return_value = chain

    elif name == "tribe_streaks":
        select_chain = MagicMock()
        select_chain.eq.return_value = select_chain
        select_chain.maybe_single.return_value = select_chain
        select_chain.execute = AsyncMock(return_value=MagicMock(data=streak_data))
        tbl.select.return_value = select_chain

        update_chain = MagicMock()
        update_chain.eq.return_value = update_chain
        update_chain.execute = AsyncMock(return_value=MagicMock(data=[]))
        tbl.update.return_value = update_chain

    return tbl


# ── _iso_week ─────────────────────────────────────────────────────────────────


class TestIsoWeek:
    def test_known_date(self):
        dt = datetime(2026, 4, 19, tzinfo=UTC)  # Sunday
        assert _iso_week(dt) == "2026-W16"

    def test_jan_1_edge(self):
        dt = datetime(2026, 1, 1, tzinfo=UTC)  # Thursday
        assert _iso_week(dt) == "2026-W01"

    def test_dec_31_may_be_next_year_week(self):
        dt = datetime(2025, 12, 29, tzinfo=UTC)  # Monday
        result = _iso_week(dt)
        assert result.startswith("2026-W01") or result.startswith("2025-W")

    def test_format(self):
        dt = datetime(2026, 3, 2, tzinfo=UTC)
        result = _iso_week(dt)
        assert result.startswith("2026-W")
        week_num = int(result.split("W")[1])
        assert 1 <= week_num <= 53


# ── _update_user_streak ──────────────────────────────────────────────────────


class TestUpdateUserStreak:
    @pytest.mark.asyncio
    async def test_no_streak_row_returns_missed(self):
        db = _mock_db(streak_data=None)
        result = await _update_user_streak(db, USER_ID, "2026-W16")
        assert result == "missed"

    @pytest.mark.asyncio
    async def test_active_week_returns_extended(self):
        db = _mock_db(
            streak_data={
                "user_id": USER_ID,
                "current_streak": 3,
                "longest_streak": 5,
                "last_activity_week": "2026-W16",
                "consecutive_misses_count": 0,
            }
        )
        result = await _update_user_streak(db, USER_ID, "2026-W16")
        assert result == "extended"

    @pytest.mark.asyncio
    async def test_inactive_below_threshold_returns_missed(self):
        db = _mock_db(
            streak_data={
                "user_id": USER_ID,
                "current_streak": 5,
                "longest_streak": 5,
                "last_activity_week": "2026-W14",
                "consecutive_misses_count": 1,
            }
        )
        result = await _update_user_streak(db, USER_ID, "2026-W16")
        assert result == "missed"

    @pytest.mark.asyncio
    async def test_three_misses_resets_streak(self):
        db = _mock_db(
            streak_data={
                "user_id": USER_ID,
                "current_streak": 10,
                "longest_streak": 10,
                "last_activity_week": "2026-W12",
                "consecutive_misses_count": 2,
            }
        )
        result = await _update_user_streak(db, USER_ID, "2026-W16")
        assert result == "reset"

    @pytest.mark.asyncio
    async def test_reset_sets_streak_to_zero(self):
        db = _mock_db(
            streak_data={
                "user_id": USER_ID,
                "current_streak": 10,
                "longest_streak": 10,
                "last_activity_week": "2026-W12",
                "consecutive_misses_count": 2,
            }
        )
        await _update_user_streak(db, USER_ID, "2026-W16")

        streak_tbl = db.table("tribe_streaks")
        update_payload = streak_tbl.update.call_args[0][0]
        assert update_payload["current_streak"] == 0
        assert update_payload["consecutive_misses_count"] == 0

    @pytest.mark.asyncio
    async def test_missed_increments_misses(self):
        db = _mock_db(
            streak_data={
                "user_id": USER_ID,
                "current_streak": 5,
                "longest_streak": 5,
                "last_activity_week": "2026-W14",
                "consecutive_misses_count": 0,
            }
        )
        await _update_user_streak(db, USER_ID, "2026-W16")

        streak_tbl = db.table("tribe_streaks")
        update_payload = streak_tbl.update.call_args[0][0]
        assert update_payload["consecutive_misses_count"] == 1


# ── record_assessment_activity ────────────────────────────────────────────────


class TestRecordAssessmentActivity:
    @pytest.mark.asyncio
    async def test_no_streak_row_returns_early(self):
        db = _mock_db(streak_data=None)
        await record_assessment_activity(db, USER_ID)
        db.table("tribe_streaks").update.assert_not_called()

    @pytest.mark.asyncio
    async def test_already_credited_this_week_noop(self):
        current_week = _iso_week(datetime.now(UTC))
        db = _mock_db(
            streak_data={
                "user_id": USER_ID,
                "current_streak": 3,
                "longest_streak": 5,
                "last_activity_week": current_week,
                "consecutive_misses_count": 0,
            }
        )
        await record_assessment_activity(db, USER_ID)
        db.table("tribe_streaks").update.assert_not_called()

    @pytest.mark.asyncio
    async def test_extends_streak(self):
        db = _mock_db(
            streak_data={
                "user_id": USER_ID,
                "current_streak": 3,
                "longest_streak": 5,
                "last_activity_week": "2025-W01",
                "consecutive_misses_count": 1,
            }
        )
        await record_assessment_activity(db, USER_ID)

        streak_tbl = db.table("tribe_streaks")
        streak_tbl.update.assert_called_once()
        payload = streak_tbl.update.call_args[0][0]
        assert payload["current_streak"] == 4
        assert payload["consecutive_misses_count"] == 0

    @pytest.mark.asyncio
    async def test_updates_longest_streak(self):
        db = _mock_db(
            streak_data={
                "user_id": USER_ID,
                "current_streak": 5,
                "longest_streak": 5,
                "last_activity_week": "2025-W01",
                "consecutive_misses_count": 0,
            }
        )
        await record_assessment_activity(db, USER_ID)

        streak_tbl = db.table("tribe_streaks")
        payload = streak_tbl.update.call_args[0][0]
        assert payload["current_streak"] == 6
        assert payload["longest_streak"] == 6


# ── update_weekly_streaks ─────────────────────────────────────────────────────


class TestUpdateWeeklyStreaks:
    @pytest.mark.asyncio
    async def test_no_members_returns_zeros(self):
        db = _mock_db(tribe_members=[], streak_data=None)
        result = await update_weekly_streaks(db)
        assert result["users_processed"] == 0
        assert result["streaks_extended"] == 0

    @pytest.mark.asyncio
    async def test_deduplicates_user_ids(self):
        db = _mock_db(
            tribe_members=[
                {"user_id": USER_ID},
                {"user_id": USER_ID},
            ],
            streak_data=None,
        )
        result = await update_weekly_streaks(db)
        assert result["users_processed"] == 1

    @pytest.mark.asyncio
    async def test_handles_per_user_exception(self):
        db = AsyncMock()

        members_tbl = MagicMock()
        members_chain = MagicMock()
        members_chain.is_.return_value = members_chain
        members_chain.execute = AsyncMock(return_value=MagicMock(data=[{"user_id": USER_ID}]))
        members_tbl.select.return_value = members_chain

        streak_tbl = MagicMock()
        select_chain = MagicMock()
        select_chain.eq.return_value = select_chain
        select_chain.maybe_single.return_value = select_chain
        select_chain.execute = AsyncMock(side_effect=Exception("boom"))
        streak_tbl.select.return_value = select_chain

        db.table = MagicMock(side_effect=lambda n: members_tbl if n == "tribe_members" else streak_tbl)

        result = await update_weekly_streaks(db)
        assert result["users_processed"] == 0
