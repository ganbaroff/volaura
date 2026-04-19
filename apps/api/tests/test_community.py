"""Unit tests for app.routers.community.

Covers _unique_count helper, CommunitySignal schema, router registration,
and GET /community/signal endpoint behaviour via mocked Supabase.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_supabase_admin
from app.main import app
from app.routers.community import CommunitySignal, _unique_count, router

# ---------------------------------------------------------------------------
# _unique_count — pure unit tests (no DB, no HTTP)
# ---------------------------------------------------------------------------


def test_unique_count_empty_list():
    assert _unique_count([]) == 0


def test_unique_count_none_input():
    assert _unique_count(None) == 0


def test_unique_count_deduplicates():
    rows = [
        {"volunteer_id": "u1"},
        {"volunteer_id": "u1"},
        {"volunteer_id": "u2"},
    ]
    assert _unique_count(rows) == 2


def test_unique_count_all_unique():
    rows = [{"volunteer_id": f"u{i}"} for i in range(5)]
    assert _unique_count(rows) == 5


def test_unique_count_skips_none_volunteer_id():
    rows = [
        {"volunteer_id": "u1"},
        {"volunteer_id": None},
        {"volunteer_id": "u2"},
        {},
    ]
    assert _unique_count(rows) == 2


def test_unique_count_all_none_volunteer_ids():
    rows = [{"volunteer_id": None}, {"volunteer_id": None}]
    assert _unique_count(rows) == 0


def test_unique_count_mixed_valid_and_none():
    rows = [
        {"volunteer_id": "u1"},
        {"volunteer_id": None},
        {"volunteer_id": "u1"},
        {"volunteer_id": "u3"},
        {},
    ]
    assert _unique_count(rows) == 2


# ---------------------------------------------------------------------------
# CommunitySignal schema — Pydantic v2 validation
# ---------------------------------------------------------------------------


def test_community_signal_valid_construction():
    sig = CommunitySignal(
        professionals_today=5,
        professionals_this_week=20,
        total_professionals=100,
    )
    assert sig.professionals_today == 5
    assert sig.professionals_this_week == 20
    assert sig.total_professionals == 100


def test_community_signal_zero_values():
    sig = CommunitySignal(
        professionals_today=0,
        professionals_this_week=0,
        total_professionals=0,
    )
    assert sig.professionals_today == 0


def test_community_signal_from_attributes():
    """ConfigDict(from_attributes=True) must be present — allows ORM-style init."""
    assert CommunitySignal.model_config.get("from_attributes") is True


def test_community_signal_schema_keys():
    sig = CommunitySignal(
        professionals_today=1,
        professionals_this_week=2,
        total_professionals=3,
    )
    dumped = sig.model_dump()
    assert set(dumped.keys()) == {
        "professionals_today",
        "professionals_this_week",
        "total_professionals",
    }


# ---------------------------------------------------------------------------
# Router registration — prefix, tags, routes
# ---------------------------------------------------------------------------


def test_router_prefix():
    assert router.prefix == "/community"


def test_router_tags():
    assert "Community" in router.tags


def test_router_has_signal_route():
    paths = [r.path for r in router.routes]
    assert "/community/signal" in paths


def test_signal_route_is_get():
    for r in router.routes:
        if r.path == "/community/signal":
            assert "GET" in r.methods
            break
    else:
        pytest.fail("/community/signal route not found on router")


# ---------------------------------------------------------------------------
# Endpoint integration tests — mocked Supabase, no real DB
# ---------------------------------------------------------------------------


def _build_db_mock(today_rows: list, week_rows: list, total_count: int | None):
    """Build a synchronous-chain Supabase mock.

    The endpoint calls .table() three times in order:
      1. assessment_sessions → today
      2. assessment_sessions → week
      3. aura_scores         → total (head=True, count="exact")
    We track calls via a counter so the same table() stub can return
    different results per invocation.
    """
    call_counter = {"n": 0}

    def table_mock(_name: str):
        chain = MagicMock()
        chain.select = MagicMock(return_value=chain)
        for method in ("eq", "gte", "limit", "order", "range"):
            setattr(chain, method, MagicMock(return_value=chain))

        async def _execute():
            call_counter["n"] += 1
            if call_counter["n"] == 1:
                return MagicMock(data=today_rows, count=None)
            if call_counter["n"] == 2:
                return MagicMock(data=week_rows, count=None)
            return MagicMock(data=None, count=total_count)

        chain.execute = _execute
        return chain

    db = MagicMock()
    db.table = table_mock
    return db


@pytest.mark.anyio
async def test_endpoint_happy_path():
    """All three queries return data — counts computed correctly."""
    db = _build_db_mock(
        today_rows=[{"volunteer_id": "u1"}, {"volunteer_id": "u1"}, {"volunteer_id": "u2"}],
        week_rows=[{"volunteer_id": f"u{i}"} for i in range(7)],
        total_count=42,
    )

    async def _override():
        yield db

    app.dependency_overrides[get_supabase_admin] = _override
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/community/signal")
        assert resp.status_code == 200
        body = resp.json()
        assert body["professionals_today"] == 2
        assert body["professionals_this_week"] == 7
        assert body["total_professionals"] == 42
    finally:
        app.dependency_overrides.pop(get_supabase_admin, None)


@pytest.mark.anyio
async def test_endpoint_empty_db():
    """No sessions, no aura_scores — all three counts are zero."""
    db = _build_db_mock(today_rows=[], week_rows=[], total_count=0)

    async def _override():
        yield db

    app.dependency_overrides[get_supabase_admin] = _override
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/community/signal")
        assert resp.status_code == 200
        assert resp.json() == {
            "professionals_today": 0,
            "professionals_this_week": 0,
            "total_professionals": 0,
        }
    finally:
        app.dependency_overrides.pop(get_supabase_admin, None)


@pytest.mark.anyio
async def test_endpoint_none_data_handling():
    """aura_scores count=None falls back to 0 via 'count or 0'."""
    db = _build_db_mock(today_rows=[], week_rows=[], total_count=None)

    async def _override():
        yield db

    app.dependency_overrides[get_supabase_admin] = _override
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/community/signal")
        assert resp.status_code == 200
        assert resp.json()["total_professionals"] == 0
    finally:
        app.dependency_overrides.pop(get_supabase_admin, None)


@pytest.mark.anyio
async def test_endpoint_duplicate_volunteer_ids_in_today_and_week():
    """Same user appears multiple times in both today and week results."""
    rows = [{"volunteer_id": "alice"}, {"volunteer_id": "alice"}, {"volunteer_id": "bob"}]
    db = _build_db_mock(today_rows=rows, week_rows=rows, total_count=2)

    async def _override():
        yield db

    app.dependency_overrides[get_supabase_admin] = _override
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/community/signal")
        assert resp.status_code == 200
        body = resp.json()
        assert body["professionals_today"] == 2
        assert body["professionals_this_week"] == 2
        assert body["total_professionals"] == 2
    finally:
        app.dependency_overrides.pop(get_supabase_admin, None)


@pytest.mark.anyio
async def test_endpoint_response_schema_lock():
    """Response must contain exactly three keys, all non-negative integers."""
    db = _build_db_mock(
        today_rows=[{"volunteer_id": "u1"}],
        week_rows=[{"volunteer_id": "u1"}],
        total_count=1,
    )

    async def _override():
        yield db

    app.dependency_overrides[get_supabase_admin] = _override
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/community/signal")
        body = resp.json()
        assert set(body.keys()) == {
            "professionals_today",
            "professionals_this_week",
            "total_professionals",
        }
        for v in body.values():
            assert isinstance(v, int)
            assert v >= 0
    finally:
        app.dependency_overrides.pop(get_supabase_admin, None)
