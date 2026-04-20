"""HTTP endpoint tests for the activity router.

Covers:
- GET /api/activity/me  — activity feed with pagination
- GET /api/activity/stats/me — dashboard stats

Uses AsyncClient + app.dependency_overrides pattern (same as test_new_endpoints.py).
Each test class owns its overrides and cleans up in finally blocks.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_user
from app.main import app

# ── Constants ──────────────────────────────────────────────────────────────────

USER_ID = str(uuid4())
AUTH_HEADERS = {"Authorization": "Bearer test-token-activity"}


# ── Helpers ────────────────────────────────────────────────────────────────────


def make_client() -> AsyncClient:
    """Return a fresh async test client."""
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def make_chain(data=None, count=None, side_effect=None) -> MagicMock:
    """Build a mock Supabase query chain that returns data.

    Supports the full chain used by both activity endpoints:
      .table().select().eq().order().limit().execute()
      .table().select().eq().eq().not_.is_("...").execute()
      .table().select().eq().eq().gte().execute()
    """
    result = MagicMock()
    result.data = data if data is not None else []
    result.count = count

    if side_effect:
        execute = AsyncMock(side_effect=side_effect)
    else:
        execute = AsyncMock(return_value=result)

    chain = MagicMock()
    for method in ("select", "eq", "order", "limit", "gte"):
        getattr(chain, method).return_value = chain
    # not_ chain: .not_.is_("col", "null") → chain
    chain.not_.is_.return_value = chain
    chain.not_.return_value = chain
    chain.execute = execute
    return chain


def make_db(tables: dict | None = None) -> MagicMock:
    """Build a mock Supabase client with per-table chain dispatch.

    tables: {
        "table_name": {"data": [...], "count": N}  |  {"side_effect": Exception}
    }
    """
    db = MagicMock()
    tables = tables or {}

    def dispatch(name: str) -> MagicMock:
        cfg = tables.get(name, {})
        return make_chain(**cfg)

    db.table.side_effect = dispatch
    return db


def user_dep(db: MagicMock):
    """FastAPI override for get_supabase_user (async generator, no args)."""

    async def _override():
        yield db

    return _override


def user_id_dep(uid: str = USER_ID):
    """FastAPI override for get_current_user_id (plain async function)."""

    async def _override():
        return uid

    return _override


# ── GET /api/activity/me ───────────────────────────────────────────────────────


class TestActivityFeedEndpoint:
    """HTTP-level tests for GET /api/activity/me."""

    @pytest.mark.asyncio
    async def test_returns_200_with_empty_feed(self):
        """All tables return empty → 200 with empty data list."""
        db = make_db()
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.get("/api/activity/me", headers=AUTH_HEADERS)
            assert response.status_code == 200
            body = response.json()
            assert body["data"] == []
            assert body["meta"]["total"] == 0
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_assessments_in_feed(self):
        """Completed assessments appear as type='assessment' items."""
        db = make_db(
            {
                "assessment_sessions": {
                    "data": [
                        {
                            "id": "as-1",
                            "competency_id": "communication",
                            "theta_estimate": 1.2,
                            "status": "completed",
                            "completed_at": "2026-04-17T10:00:00Z",
                        }
                    ]
                }
            }
        )
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.get("/api/activity/me", headers=AUTH_HEADERS)
            assert response.status_code == 200
            items = response.json()["data"]
            assessment_items = [i for i in items if i["type"] == "assessment"]
            assert len(assessment_items) == 1
            assert assessment_items[0]["id"] == "as-1"
            assert assessment_items[0]["metadata"]["competency_id"] == "communication"
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_badges_in_feed(self):
        """Earned badges appear as type='badge' items with badge_type metadata."""
        db = make_db(
            {
                "volunteer_badges": {
                    "data": [
                        {
                            "id": "vb-1",
                            "badge_id": "bd-gold",
                            "earned_at": "2026-04-16T08:00:00Z",
                            "metadata": {},
                            "badges": {"badge_type": "gold", "name_en": "Gold Leader"},
                        }
                    ]
                }
            }
        )
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.get("/api/activity/me", headers=AUTH_HEADERS)
            assert response.status_code == 200
            items = response.json()["data"]
            badge_items = [i for i in items if i["type"] == "badge"]
            assert len(badge_items) == 1
            assert badge_items[0]["id"] == "vb-1"
            assert badge_items[0]["metadata"]["badge_type"] == "gold"
            assert badge_items[0]["metadata"]["badge_id"] == "bd-gold"
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_event_registrations_in_feed(self):
        """Event registrations appear as type='event' items."""
        db = make_db(
            {
                "registrations": {
                    "data": [
                        {
                            "id": "reg-1",
                            "event_id": "ev-abc",
                            "status": "approved",
                            "registered_at": "2026-04-15T12:00:00Z",
                        }
                    ]
                }
            }
        )
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.get("/api/activity/me", headers=AUTH_HEADERS)
            assert response.status_code == 200
            items = response.json()["data"]
            event_items = [i for i in items if i["type"] == "event"]
            assert len(event_items) == 1
            assert event_items[0]["id"] == "reg-1"
            assert event_items[0]["metadata"]["event_id"] == "ev-abc"
            assert event_items[0]["metadata"]["status"] == "approved"
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_behavior_signals_in_feed(self):
        """Behavior signals appear as type='verification' items."""
        db = make_db(
            {
                "volunteer_behavior_signals": {
                    "data": [
                        {
                            "id": "sig-1",
                            "signal_type": "punctuality",
                            "signal_value": 0.95,
                            "measured_at": "2026-04-14T09:00:00Z",
                            "source": "coordinator",
                        }
                    ]
                }
            }
        )
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.get("/api/activity/me", headers=AUTH_HEADERS)
            assert response.status_code == 200
            items = response.json()["data"]
            sig_items = [i for i in items if i["type"] == "verification"]
            assert len(sig_items) == 1
            assert sig_items[0]["id"] == "sig-1"
            assert sig_items[0]["metadata"]["signal_type"] == "punctuality"
            assert sig_items[0]["metadata"]["source"] == "coordinator"
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_mixed_items_sorted_by_created_at_descending(self):
        """Items from multiple tables are sorted newest-first in the response."""
        db = make_db(
            {
                "assessment_sessions": {
                    "data": [
                        {
                            "id": "old-assessment",
                            "competency_id": "leadership",
                            "theta_estimate": 0.5,
                            "status": "completed",
                            "completed_at": "2026-04-10T00:00:00Z",
                        }
                    ]
                },
                "registrations": {
                    "data": [
                        {
                            "id": "new-event",
                            "event_id": "ev-xyz",
                            "status": "approved",
                            "registered_at": "2026-04-17T00:00:00Z",
                        }
                    ]
                },
            }
        )
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.get("/api/activity/me", headers=AUTH_HEADERS)
            assert response.status_code == 200
            items = response.json()["data"]
            assert len(items) >= 2
            assert items[0]["id"] == "new-event"
            assert items[-1]["id"] == "old-assessment"
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_pagination_custom_limit_and_offset(self):
        """limit=2 offset=1 returns correct slice and meta."""
        sessions = [
            {
                "id": f"a{i}",
                "competency_id": "reliability",
                "theta_estimate": float(i),
                "status": "completed",
                "completed_at": f"2026-04-{10 + i:02d}T00:00:00Z",
            }
            for i in range(4)
        ]
        db = make_db({"assessment_sessions": {"data": sessions}})
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.get(
                    "/api/activity/me",
                    params={"limit": 2, "offset": 1},
                    headers=AUTH_HEADERS,
                )
            assert response.status_code == 200
            body = response.json()
            assert len(body["data"]) == 2
            assert body["meta"]["total"] == 4
            assert body["meta"]["limit"] == 2
            assert body["meta"]["offset"] == 1
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_default_limit_20_offset_0(self):
        """Without query params, meta reflects limit=20 offset=0."""
        db = make_db()
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.get("/api/activity/me", headers=AUTH_HEADERS)
            assert response.status_code == 200
            meta = response.json()["meta"]
            assert meta["limit"] == 20
            assert meta["offset"] == 0
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_db_error_on_one_source_does_not_break_feed(self):
        """assessment_sessions failure is swallowed; event registrations still returned."""
        db = make_db(
            {
                "assessment_sessions": {"side_effect": RuntimeError("DB timeout")},
                "registrations": {
                    "data": [
                        {
                            "id": "reg-ok",
                            "event_id": "ev-ok",
                            "status": "approved",
                            "registered_at": "2026-04-15T12:00:00Z",
                        }
                    ]
                },
            }
        )
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.get("/api/activity/me", headers=AUTH_HEADERS)
            assert response.status_code == 200
            items = response.json()["data"]
            event_items = [i for i in items if i["type"] == "event"]
            assert len(event_items) == 1
            assert event_items[0]["id"] == "reg-ok"
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_requires_authentication(self):
        """No Authorization header → 401 (dependency raises HTTPException)."""
        # No overrides — real get_current_user_id fires and rejects missing token
        try:
            async with make_client() as client:
                response = await client.get("/api/activity/me")
            assert response.status_code == 401
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)


# ── GET /api/activity/stats/me ─────────────────────────────────────────────────


class TestActivityStatsEndpoint:
    """HTTP-level tests for GET /api/activity/stats/me."""

    @pytest.mark.asyncio
    async def test_returns_200_with_zero_stats_empty_tables(self):
        """Empty tables → 200 with all stats at zero."""
        db = make_db(
            {
                "registrations": {"data": [], "count": 0},
                "assessment_sessions": {"data": []},
            }
        )
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.get("/api/activity/stats/me", headers=AUTH_HEADERS)
            assert response.status_code == 200
            data = response.json()["data"]
            assert data["events_attended"] == 0
            assert data["total_hours"] == 0
            assert data["verified_skills"] == 0
            assert data["streak_days"] == 0
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_events_attended_correct_count(self):
        """events_attended reflects the count returned by the registrations query."""
        db = make_db(
            {
                "registrations": {"data": [], "count": 5},
                "assessment_sessions": {"data": []},
            }
        )
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.get("/api/activity/stats/me", headers=AUTH_HEADERS)
            assert response.status_code == 200
            data = response.json()["data"]
            assert data["events_attended"] == 5
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_verified_skills_deduped_by_competency_id(self):
        """Three rows with two distinct competency_ids → verified_skills == 2."""
        db = make_db(
            {
                "registrations": {"data": [], "count": 0},
                "assessment_sessions": {
                    "data": [
                        {"competency_id": "communication"},
                        {"competency_id": "communication"},
                        {"competency_id": "leadership"},
                    ]
                },
            }
        )
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.get("/api/activity/stats/me", headers=AUTH_HEADERS)
            assert response.status_code == 200
            data = response.json()["data"]
            assert data["verified_skills"] == 2
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_total_hours_equals_events_attended_times_4(self):
        """total_hours = events_attended * 4 (4h per event estimate)."""
        db = make_db(
            {
                "registrations": {"data": [], "count": 3},
                "assessment_sessions": {"data": []},
            }
        )
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.get("/api/activity/stats/me", headers=AUTH_HEADERS)
            assert response.status_code == 200
            data = response.json()["data"]
            assert data["total_hours"] == data["events_attended"] * 4
            assert data["total_hours"] == 12
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_streak_days_counts_unique_days_in_last_7(self):
        """Two sessions on same day count as 1 streak day; two different days → 2."""
        db = make_db(
            {
                "registrations": {"data": [], "count": 0},
                "assessment_sessions": {
                    "data": [
                        {"completed_at": "2026-04-17T10:00:00Z"},
                        {"completed_at": "2026-04-17T15:30:00Z"},
                        {"completed_at": "2026-04-16T08:00:00Z"},
                    ]
                },
            }
        )
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.get("/api/activity/stats/me", headers=AUTH_HEADERS)
            assert response.status_code == 200
            data = response.json()["data"]
            assert data["streak_days"] == 2
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_stats_requires_authentication(self):
        """No Authorization header → 401."""
        try:
            async with make_client() as client:
                response = await client.get("/api/activity/stats/me")
            assert response.status_code == 401
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_stats_response_has_required_keys(self):
        """Response body must contain all four expected stat keys."""
        db = make_db(
            {
                "registrations": {"data": [], "count": 0},
                "assessment_sessions": {"data": []},
            }
        )
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.get("/api/activity/stats/me", headers=AUTH_HEADERS)
            assert response.status_code == 200
            data = response.json()["data"]
            for key in ("events_attended", "total_hours", "verified_skills", "streak_days"):
                assert key in data, f"Missing key '{key}' in stats response"
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_stats_all_zero_when_all_queries_fail(self):
        """DB errors on all queries → 200 with all stats at zero (resilient)."""
        db = make_db(
            {
                "registrations": {"side_effect": Exception("DB down")},
                "assessment_sessions": {"side_effect": Exception("DB down")},
            }
        )
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.get("/api/activity/stats/me", headers=AUTH_HEADERS)
            assert response.status_code == 200
            data = response.json()["data"]
            assert data["events_attended"] == 0
            assert data["total_hours"] == 0
            assert data["verified_skills"] == 0
            assert data["streak_days"] == 0
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)
