"""Tests for /api/aura endpoints."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.deps import get_supabase_admin, get_supabase_user, get_current_user_id

USER_ID = "uuid-aura-test"
NOW = datetime.utcnow().isoformat()

AURA_ROW = {
    "volunteer_id": USER_ID,
    "overall_score": 78.5,
    "badge_tier": "gold",
    "elite_status": False,
    "competency_scores": {
        "communication": 82.0,
        "reliability": 75.0,
        "english_proficiency": 80.0,
        "leadership": 70.0,
        "event_performance": 0.0,
        "tech_literacy": 65.0,
        "adaptability": 72.0,
        "empathy_safeguarding": 90.0,
    },
    "reliability_score": 55.0,
    "reliability_status": "behavioral",
    "events_attended": 0,
    "events_no_show": 0,
    "aura_history": [],
    "calculated_at": NOW,
}


def _admin_override(db):
    async def _dep():
        yield db
    return _dep


def _user_override(db):
    async def _dep():
        yield db
    return _dep


def _uid_override(uid=USER_ID):
    async def _dep():
        return uid
    return _dep


def _make_mock_db():
    db = MagicMock()
    db.table = MagicMock(return_value=db)
    db.select = MagicMock(return_value=db)
    db.eq = MagicMock(return_value=db)
    db.single = MagicMock(return_value=db)
    db.execute = AsyncMock()
    return db


@pytest.mark.asyncio
async def test_get_my_aura_found():
    db = _make_mock_db()
    db.execute = AsyncMock(return_value=MagicMock(data=AURA_ROW))

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/aura/me", headers={"Authorization": "Bearer fake"})

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["volunteer_id"] == USER_ID
    assert body["overall_score"] == 78.5
    assert body["badge_tier"] == "gold"
    assert body["elite_status"] is False


@pytest.mark.asyncio
async def test_get_my_aura_not_found():
    db = _make_mock_db()
    db.execute = AsyncMock(return_value=MagicMock(data=None))

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/aura/me", headers={"Authorization": "Bearer fake"})

    app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "AURA_NOT_FOUND"


@pytest.mark.asyncio
async def test_get_aura_by_id_found():
    target_id = "uuid-other-volunteer"
    aura_row = {**AURA_ROW, "volunteer_id": target_id}

    db = _make_mock_db()
    db.execute = AsyncMock(return_value=MagicMock(data=aura_row))

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get(f"/api/aura/{target_id}")

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["volunteer_id"] == target_id


@pytest.mark.asyncio
async def test_get_aura_by_id_not_found():
    db = _make_mock_db()
    db.execute = AsyncMock(return_value=MagicMock(data=None))

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/aura/uuid-nonexistent")

    app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "AURA_NOT_FOUND"
