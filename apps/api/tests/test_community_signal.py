"""Unit tests for /api/community/signal — anonymous aggregate social proof (G44).

Pins the invariant that response contains only three integer counts and never
any per-user data (no ids, no usernames, no session timestamps). That invariant
is the difference between "social proof" and "leaderboard".
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_supabase_admin
from app.main import app


def _make_db(today_rows: list, week_rows: list, total_count: int):
    """Supabase-async chain mock — returns different rows per select call."""
    call_counter = {"n": 0}

    def table_mock(_name: str):
        chain = MagicMock()
        select_mock = MagicMock(return_value=chain)
        chain.select = select_mock

        # Chain stubs — all return self so .eq().gte().execute() works
        for method in ("eq", "gte", "limit", "order", "range"):
            setattr(chain, method, MagicMock(return_value=chain))

        async def _execute():
            call_counter["n"] += 1
            # 1st call = today, 2nd = week, 3rd = total (head+count=exact)
            if call_counter["n"] == 1:
                return MagicMock(data=today_rows)
            if call_counter["n"] == 2:
                return MagicMock(data=week_rows)
            return MagicMock(data=None, count=total_count)

        chain.execute = _execute
        return chain

    db = MagicMock()
    db.table = table_mock
    return db


@pytest.mark.anyio
async def test_signal_returns_three_unique_counts():
    db = _make_db(
        today_rows=[{"volunteer_id": "u1"}, {"volunteer_id": "u1"}, {"volunteer_id": "u2"}],  # 2 unique
        week_rows=[{"volunteer_id": f"u{i}"} for i in range(5)],
        total_count=27,
    )

    async def _override_db():
        yield db

    app.dependency_overrides[get_supabase_admin] = _override_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/community/signal")
        assert resp.status_code == 200
        body = resp.json()
        assert body["professionals_today"] == 2, "duplicate volunteer_id counts once"
        assert body["professionals_this_week"] == 5
        assert body["total_professionals"] == 27
    finally:
        app.dependency_overrides.pop(get_supabase_admin, None)


@pytest.mark.anyio
async def test_signal_never_exposes_ids_or_usernames():
    """Regression: response payload must contain exactly 3 keys, all ints."""
    db = _make_db(today_rows=[{"volunteer_id": "u1"}], week_rows=[{"volunteer_id": "u1"}], total_count=1)

    async def _override_db():
        yield db

    app.dependency_overrides[get_supabase_admin] = _override_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/community/signal")
        body = resp.json()
        # Schema lock — exactly these 3 keys, nothing else
        assert set(body.keys()) == {"professionals_today", "professionals_this_week", "total_professionals"}
        # All values are non-negative integers
        for v in body.values():
            assert isinstance(v, int)
            assert v >= 0
    finally:
        app.dependency_overrides.pop(get_supabase_admin, None)


@pytest.mark.anyio
async def test_signal_handles_empty_db():
    """Zero signal — first minute after deploy, no completed sessions yet."""
    db = _make_db(today_rows=[], week_rows=[], total_count=0)

    async def _override_db():
        yield db

    app.dependency_overrides[get_supabase_admin] = _override_db
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
