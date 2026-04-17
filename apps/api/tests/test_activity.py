"""Unit tests for activity feed — item construction, sorting, pagination, stats.

Tests the pure transformation logic inside get_my_activity and get_my_stats
by mocking Supabase queries.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


def _mock_table_chain(data=None, count=None, side_effect=None):
    """Build a fluent Supabase query chain mock."""
    result = MagicMock(data=data or [], count=count)
    if side_effect:
        execute = AsyncMock(side_effect=side_effect)
    else:
        execute = AsyncMock(return_value=result)
    chain = MagicMock()
    chain.select.return_value = chain
    chain.eq.return_value = chain
    chain.gte.return_value = chain
    chain.not_.is_.return_value = chain
    chain.not_.return_value = chain
    chain.order.return_value = chain
    chain.limit.return_value = chain
    chain.execute = execute
    return chain


def _mock_db(tables: dict | None = None):
    """Mock AsyncClient with per-table chain configs.

    tables: {"table_name": {"data": [...], "count": N, "side_effect": ...}}
    """
    db = MagicMock()
    tables = tables or {}

    def table_dispatch(name):
        cfg = tables.get(name, {})
        return _mock_table_chain(**cfg)

    db.table.side_effect = table_dispatch
    return db


# ── Activity feed item construction ────────────────────────────────────────


class TestActivityFeedItems:
    @pytest.mark.asyncio
    async def test_assessment_items_built_correctly(self):
        from app.routers.activity import get_my_activity

        db = _mock_db(
            {
                "assessment_sessions": {
                    "data": [
                        {
                            "id": "a1",
                            "competency_id": "c1",
                            "theta_estimate": 1.5,
                            "status": "completed",
                            "completed_at": "2026-04-17T10:00:00Z",
                        }
                    ]
                }
            }
        )
        request = MagicMock()
        result = await get_my_activity(request=request, db=db, user_id="u1", limit=20, offset=0)
        items = result["data"]
        assert any(i["type"] == "assessment" for i in items)
        a = next(i for i in items if i["type"] == "assessment")
        assert a["id"] == "a1"
        assert a["metadata"]["competency_id"] == "c1"
        assert a["metadata"]["theta_estimate"] == 1.5

    @pytest.mark.asyncio
    async def test_badge_items_built_correctly(self):
        from app.routers.activity import get_my_activity

        db = _mock_db(
            {
                "volunteer_badges": {
                    "data": [
                        {
                            "id": "b1",
                            "badge_id": "bd1",
                            "earned_at": "2026-04-16T08:00:00Z",
                            "metadata": {},
                            "badges": {"badge_type": "skill", "name_en": "Leader"},
                        }
                    ]
                }
            }
        )
        request = MagicMock()
        result = await get_my_activity(request=request, db=db, user_id="u1", limit=20, offset=0)
        items = result["data"]
        badge_items = [i for i in items if i["type"] == "badge"]
        assert len(badge_items) >= 1
        assert badge_items[0]["metadata"]["badge_type"] == "skill"

    @pytest.mark.asyncio
    async def test_event_registration_items(self):
        from app.routers.activity import get_my_activity

        db = _mock_db(
            {
                "registrations": {
                    "data": [
                        {
                            "id": "r1",
                            "event_id": "e1",
                            "status": "approved",
                            "registered_at": "2026-04-15T12:00:00Z",
                        }
                    ]
                }
            }
        )
        request = MagicMock()
        result = await get_my_activity(request=request, db=db, user_id="u1", limit=20, offset=0)
        event_items = [i for i in result["data"] if i["type"] == "event"]
        assert len(event_items) >= 1
        assert event_items[0]["metadata"]["event_id"] == "e1"

    @pytest.mark.asyncio
    async def test_behavior_signal_items(self):
        from app.routers.activity import get_my_activity

        db = _mock_db(
            {
                "volunteer_behavior_signals": {
                    "data": [
                        {
                            "id": "s1",
                            "signal_type": "punctuality",
                            "signal_value": 0.95,
                            "measured_at": "2026-04-14T09:00:00Z",
                            "source": "coordinator",
                        }
                    ]
                }
            }
        )
        request = MagicMock()
        result = await get_my_activity(request=request, db=db, user_id="u1", limit=20, offset=0)
        sig_items = [i for i in result["data"] if i["type"] == "verification"]
        assert len(sig_items) >= 1
        assert sig_items[0]["metadata"]["signal_type"] == "punctuality"


# ── Sorting + pagination ──────────────────────────────────────────────────


class TestActivitySortingPagination:
    @pytest.mark.asyncio
    async def test_items_sorted_descending_by_created_at(self):
        from app.routers.activity import get_my_activity

        db = _mock_db(
            {
                "assessment_sessions": {
                    "data": [
                        {
                            "id": "old",
                            "competency_id": "c1",
                            "theta_estimate": 1,
                            "status": "completed",
                            "completed_at": "2026-04-10T00:00:00Z",
                        },
                    ]
                },
                "registrations": {
                    "data": [
                        {"id": "new", "event_id": "e1", "status": "approved", "registered_at": "2026-04-17T00:00:00Z"},
                    ]
                },
            }
        )
        request = MagicMock()
        result = await get_my_activity(request=request, db=db, user_id="u1", limit=20, offset=0)
        items = result["data"]
        assert len(items) >= 2
        assert items[0]["id"] == "new"
        assert items[-1]["id"] == "old"

    @pytest.mark.asyncio
    async def test_offset_pagination(self):
        from app.routers.activity import get_my_activity

        db = _mock_db(
            {
                "assessment_sessions": {
                    "data": [
                        {
                            "id": f"a{i}",
                            "competency_id": "c1",
                            "theta_estimate": 1,
                            "status": "completed",
                            "completed_at": f"2026-04-{10 + i:02d}T00:00:00Z",
                        }
                        for i in range(5)
                    ]
                }
            }
        )
        request = MagicMock()
        result = await get_my_activity(request=request, db=db, user_id="u1", limit=2, offset=2)
        assert len(result["data"]) == 2
        assert result["meta"]["total"] == 5
        assert result["meta"]["offset"] == 2

    @pytest.mark.asyncio
    async def test_empty_feed(self):
        from app.routers.activity import get_my_activity

        db = _mock_db()
        request = MagicMock()
        result = await get_my_activity(request=request, db=db, user_id="u1", limit=20, offset=0)
        assert result["data"] == []
        assert result["meta"]["total"] == 0


# ── DB failure resilience ─────────────────────────────────────────────────


class TestActivityDBResilience:
    @pytest.mark.asyncio
    async def test_one_table_failure_doesnt_break_feed(self):
        from app.routers.activity import get_my_activity

        db = _mock_db(
            {
                "assessment_sessions": {"side_effect": Exception("db down")},
                "registrations": {
                    "data": [
                        {"id": "r1", "event_id": "e1", "status": "approved", "registered_at": "2026-04-15T12:00:00Z"},
                    ]
                },
            }
        )
        request = MagicMock()
        result = await get_my_activity(request=request, db=db, user_id="u1", limit=20, offset=0)
        assert any(i["type"] == "event" for i in result["data"])

    @pytest.mark.asyncio
    async def test_all_tables_fail_returns_empty(self):
        from app.routers.activity import get_my_activity

        db = _mock_db(
            {
                "assessment_sessions": {"side_effect": Exception("fail")},
                "volunteer_badges": {"side_effect": Exception("fail")},
                "registrations": {"side_effect": Exception("fail")},
                "volunteer_behavior_signals": {"side_effect": Exception("fail")},
            }
        )
        request = MagicMock()
        result = await get_my_activity(request=request, db=db, user_id="u1", limit=20, offset=0)
        assert result["data"] == []


# ── Stats endpoint ────────────────────────────────────────────────────────


class TestActivityStats:
    @pytest.mark.asyncio
    async def test_verified_skills_deduplicates_competencies(self):
        from app.routers.activity import get_my_stats

        db = _mock_db(
            {
                "assessment_sessions": {
                    "data": [
                        {"competency_id": "c1"},
                        {"competency_id": "c1"},
                        {"competency_id": "c2"},
                    ]
                },
                "registrations": {"data": [], "count": 0},
            }
        )
        request = MagicMock()
        result = await get_my_stats(request=request, db=db, user_id="u1")
        assert result["data"]["verified_skills"] == 2

    @pytest.mark.asyncio
    async def test_events_attended_uses_count(self):
        from app.routers.activity import get_my_stats

        db = _mock_db(
            {
                "registrations": {"data": [], "count": 3},
                "assessment_sessions": {"data": []},
            }
        )
        request = MagicMock()
        result = await get_my_stats(request=request, db=db, user_id="u1")
        assert result["data"]["events_attended"] == 3
        assert result["data"]["total_hours"] == 12

    @pytest.mark.asyncio
    async def test_streak_counts_unique_days(self):
        from app.routers.activity import get_my_stats

        db = _mock_db(
            {
                "assessment_sessions": {
                    "data": [
                        {"completed_at": "2026-04-17T10:00:00Z"},
                        {"completed_at": "2026-04-17T14:00:00Z"},
                        {"completed_at": "2026-04-16T08:00:00Z"},
                    ]
                },
                "registrations": {"data": [], "count": 0},
            }
        )
        request = MagicMock()
        result = await get_my_stats(request=request, db=db, user_id="u1")
        assert result["data"]["streak_days"] == 2

    @pytest.mark.asyncio
    async def test_all_stats_zero_on_failure(self):
        from app.routers.activity import get_my_stats

        db = _mock_db(
            {
                "registrations": {"side_effect": Exception("fail")},
                "assessment_sessions": {"side_effect": Exception("fail")},
            }
        )
        request = MagicMock()
        result = await get_my_stats(request=request, db=db, user_id="u1")
        assert result["data"]["events_attended"] == 0
        assert result["data"]["verified_skills"] == 0
        assert result["data"]["streak_days"] == 0
