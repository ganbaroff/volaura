"""HTTP endpoint tests for the community router.

Covers:
- GET /api/community/signal — aggregate social proof counters
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_supabase_admin
from app.main import app


def make_client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def make_chain(data=None, count=None, side_effect=None) -> MagicMock:
    result = MagicMock()
    result.data = data
    result.count = count

    execute = AsyncMock(side_effect=side_effect) if side_effect else AsyncMock(return_value=result)

    chain = MagicMock()
    for method in ("select", "eq", "neq", "in_", "gte", "order", "limit", "update", "insert", "upsert"):
        getattr(chain, method).return_value = chain
    chain.maybe_single.return_value = chain
    chain.execute = execute
    return chain


def admin_dep(db: MagicMock):
    async def _override():
        yield db

    return _override


def make_signal_db(
    today_data: list | None = None,
    week_data: list | None = None,
    total_count: int = 0,
) -> MagicMock:
    """Build a DB mock that returns different data per table query.

    assessment_sessions is queried twice (today + week). We track call order
    and return the right result per call. aura_scores returns a count.
    """
    db = MagicMock()
    assessment_call_count = 0

    def make_assessment_chain():
        nonlocal assessment_call_count

        call_index = assessment_call_count
        assessment_call_count += 1

        data_for_call = today_data if call_index == 0 else week_data

        result = MagicMock()
        result.data = data_for_call
        result.count = None
        execute = AsyncMock(return_value=result)

        chain = MagicMock()
        for method in ("select", "eq", "gte", "neq", "in_", "order", "limit"):
            getattr(chain, method).return_value = chain
        chain.maybe_single.return_value = chain
        chain.execute = execute
        return chain

    aura_result = MagicMock()
    aura_result.data = None
    aura_result.count = total_count
    aura_execute = AsyncMock(return_value=aura_result)

    aura_chain = MagicMock()
    for method in ("select", "eq", "gte", "neq", "in_", "order", "limit"):
        getattr(aura_chain, method).return_value = aura_chain
    aura_chain.maybe_single.return_value = aura_chain
    aura_chain.execute = aura_execute

    def dispatch(name: str) -> MagicMock:
        if name == "assessment_sessions":
            return make_assessment_chain()
        if name == "aura_scores":
            return aura_chain
        return make_chain(data=[])

    db.table.side_effect = dispatch
    return db


# ── GET /api/community/signal ─────────────────────────────────────────────────


class TestGetCommunitySignal:
    @pytest.mark.asyncio
    async def test_returns_200_with_signal_fields(self):
        db = make_signal_db(today_data=[], week_data=[], total_count=0)
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        try:
            async with make_client() as client:
                r = await client.get("/api/community/signal")
            assert r.status_code == 200
            body = r.json()
            assert "professionals_today" in body
            assert "professionals_this_week" in body
            assert "total_professionals" in body
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_zero_counts_when_no_activity(self):
        db = make_signal_db(today_data=[], week_data=[], total_count=0)
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        try:
            async with make_client() as client:
                r = await client.get("/api/community/signal")
            body = r.json()
            assert body["professionals_today"] == 0
            assert body["professionals_this_week"] == 0
            assert body["total_professionals"] == 0
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_today_count_deduplicated_by_volunteer(self):
        """Same volunteer completing 3 assessments today = count 1, not 3."""
        vol_id = "volunteer-uuid-1"
        today_rows = [
            {"volunteer_id": vol_id},
            {"volunteer_id": vol_id},
            {"volunteer_id": vol_id},
        ]
        db = make_signal_db(today_data=today_rows, week_data=today_rows, total_count=1)
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        try:
            async with make_client() as client:
                r = await client.get("/api/community/signal")
            body = r.json()
            assert body["professionals_today"] == 1
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_week_count_includes_multiple_distinct_volunteers(self):
        week_rows = [
            {"volunteer_id": "vol-1"},
            {"volunteer_id": "vol-2"},
            {"volunteer_id": "vol-3"},
            {"volunteer_id": "vol-1"},  # duplicate — should not count twice
        ]
        db = make_signal_db(today_data=[], week_data=week_rows, total_count=3)
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        try:
            async with make_client() as client:
                r = await client.get("/api/community/signal")
            body = r.json()
            assert body["professionals_this_week"] == 3
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_total_comes_from_aura_scores_count(self):
        db = make_signal_db(today_data=[], week_data=[], total_count=142)
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        try:
            async with make_client() as client:
                r = await client.get("/api/community/signal")
            body = r.json()
            assert body["total_professionals"] == 142
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_today_count_with_multiple_volunteers(self):
        today_rows = [
            {"volunteer_id": "vol-a"},
            {"volunteer_id": "vol-b"},
        ]
        db = make_signal_db(today_data=today_rows, week_data=today_rows, total_count=2)
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        try:
            async with make_client() as client:
                r = await client.get("/api/community/signal")
            body = r.json()
            assert body["professionals_today"] == 2
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_public_endpoint_no_auth_needed(self):
        """No Authorization header — must still succeed (public endpoint)."""
        db = make_signal_db(today_data=[], week_data=[], total_count=0)
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        try:
            async with make_client() as client:
                r = await client.get("/api/community/signal")
            assert r.status_code == 200
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_none_volunteer_id_ignored_in_count(self):
        """Rows with None volunteer_id must be excluded from distinct count."""
        today_rows = [
            {"volunteer_id": None},
            {"volunteer_id": "vol-1"},
            {"volunteer_id": None},
        ]
        db = make_signal_db(today_data=today_rows, week_data=today_rows, total_count=1)
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        try:
            async with make_client() as client:
                r = await client.get("/api/community/signal")
            body = r.json()
            assert body["professionals_today"] == 1
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_response_schema_types(self):
        db = make_signal_db(today_data=[], week_data=[], total_count=5)
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        try:
            async with make_client() as client:
                r = await client.get("/api/community/signal")
            body = r.json()
            assert isinstance(body["professionals_today"], int)
            assert isinstance(body["professionals_this_week"], int)
            assert isinstance(body["total_professionals"], int)
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_week_count_gte_today_count(self):
        """Weekly window is a superset of today — week count >= today count."""
        today_rows = [{"volunteer_id": "vol-1"}]
        week_rows = [{"volunteer_id": "vol-1"}, {"volunteer_id": "vol-2"}, {"volunteer_id": "vol-3"}]
        db = make_signal_db(today_data=today_rows, week_data=week_rows, total_count=10)
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        try:
            async with make_client() as client:
                r = await client.get("/api/community/signal")
            body = r.json()
            assert body["professionals_this_week"] >= body["professionals_today"]
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
