"""Tests for /api/notifications endpoints.

Covers:
  GET  /notifications/unread-count  — returns count of unread notifications
  GET  /notifications                — list notifications, newest first, paginated
  PATCH /notifications/read-all      — marks all unread as read → count = 0
  PATCH /notifications/{id}/read     — marks single notification as read
  PATCH /notifications/{id}/read     — 404 when notification doesn't belong to user
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_user
from app.main import app

USER_ID = "aaaaaaaa-bbbb-cccc-dddd-000000000001"
NOTIF_ID = "notif-uuid-1111"

NOTIF_ROW = {
    "id": NOTIF_ID,
    "type": "org_view",
    "title": "Tech Corp viewed your profile",
    "body": "Organizations can request introductions if they're interested.",
    "is_read": False,
    "reference_id": "org-uuid",
    "created_at": "2026-03-29T10:00:00+00:00",
}

NOTIF_ROW_READ = {**NOTIF_ROW, "is_read": True}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _user_override(db):
    async def _dep():
        yield db
    return _dep


def _uid_override(uid: str = USER_ID):
    async def _dep():
        return uid
    return _dep


def _make_chain_mock():
    """Circular chainable mock for simple single-call endpoints."""
    m = MagicMock()
    m.table = MagicMock(return_value=m)
    m.select = MagicMock(return_value=m)
    m.insert = MagicMock(return_value=m)
    m.update = MagicMock(return_value=m)
    m.eq = MagicMock(return_value=m)
    m.order = MagicMock(return_value=m)
    m.range = MagicMock(return_value=m)
    m.execute = AsyncMock()
    return m


# ── GET /notifications/unread-count ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_unread_count_returns_count():
    """Returns the exact count of unread notifications."""
    db = _make_chain_mock()
    result_mock = MagicMock()
    result_mock.count = 3
    db.execute = AsyncMock(return_value=result_mock)

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/notifications/unread-count", headers={"Authorization": "Bearer fake"})

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["unread_count"] == 3


@pytest.mark.asyncio
async def test_unread_count_zero_when_none():
    """Returns 0 when no unread notifications exist (count = None from Supabase)."""
    db = _make_chain_mock()
    result_mock = MagicMock()
    result_mock.count = None
    db.execute = AsyncMock(return_value=result_mock)

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/notifications/unread-count", headers={"Authorization": "Bearer fake"})

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["unread_count"] == 0


# ── GET /notifications ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_notifications_returns_items():
    """Returns list of notifications with total and unread_count."""
    db = _make_chain_mock()

    # The endpoint makes two DB calls: list (data) then unread count (count)
    list_result = MagicMock()
    list_result.data = [NOTIF_ROW]
    list_result.count = 1

    unread_result = MagicMock()
    unread_result.count = 1

    db.execute = AsyncMock(side_effect=[list_result, unread_result])

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/notifications", headers={"Authorization": "Bearer fake"})

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["unread_count"] == 1
    assert len(body["notifications"]) == 1
    assert body["notifications"][0]["id"] == NOTIF_ID
    assert body["notifications"][0]["type"] == "org_view"


@pytest.mark.asyncio
async def test_list_notifications_empty():
    """Returns empty list and zero counts when user has no notifications."""
    db = _make_chain_mock()

    empty_result = MagicMock()
    empty_result.data = []
    empty_result.count = 0

    unread_result = MagicMock()
    unread_result.count = 0

    db.execute = AsyncMock(side_effect=[empty_result, unread_result])

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/notifications", headers={"Authorization": "Bearer fake"})

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 0
    assert body["unread_count"] == 0
    assert body["notifications"] == []


@pytest.mark.asyncio
async def test_list_notifications_pagination():
    """Limit/offset query params are accepted without error."""
    db = _make_chain_mock()

    empty_result = MagicMock()
    empty_result.data = []
    empty_result.count = 0
    unread_result = MagicMock()
    unread_result.count = 0

    db.execute = AsyncMock(side_effect=[empty_result, unread_result])

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get(
            "/api/notifications?limit=5&offset=10",
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_list_notifications_limit_above_max_rejected():
    """limit > 50 is rejected with 422."""
    app.dependency_overrides[get_supabase_user] = _user_override(MagicMock())
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get(
            "/api/notifications?limit=200",
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 422


# ── PATCH /notifications/read-all ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_mark_all_read_returns_zero():
    """PATCH /read-all updates all unread rows and returns unread_count=0."""
    db = _make_chain_mock()
    db.execute = AsyncMock(return_value=MagicMock(data=[]))

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.patch("/api/notifications/read-all", headers={"Authorization": "Bearer fake"})

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["unread_count"] == 0


# ── PATCH /notifications/{id}/read ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_mark_single_notification_read():
    """PATCH /{id}/read returns the updated notification with is_read=True."""
    db = _make_chain_mock()
    db.execute = AsyncMock(return_value=MagicMock(data=[NOTIF_ROW_READ]))

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.patch(
            f"/api/notifications/{NOTIF_ID}/read",
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == NOTIF_ID
    assert body["is_read"] is True


@pytest.mark.asyncio
async def test_mark_notification_read_not_found():
    """PATCH /{id}/read returns 404 when notification doesn't belong to user."""
    db = _make_chain_mock()
    # Supabase RLS returns empty data for rows not owned by this user
    db.execute = AsyncMock(return_value=MagicMock(data=[]))

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.patch(
            "/api/notifications/non-existent-id/read",
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "NOTIFICATION_NOT_FOUND"


@pytest.mark.asyncio
async def test_notifications_require_auth():
    """All notification endpoints require authentication."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        count_resp = await ac.get("/api/notifications/unread-count")
        list_resp = await ac.get("/api/notifications")
        read_all_resp = await ac.patch("/api/notifications/read-all")

    assert count_resp.status_code in (401, 403)
    assert list_resp.status_code in (401, 403)
    assert read_all_resp.status_code in (401, 403)
