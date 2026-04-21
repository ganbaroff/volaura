"""HTTP endpoint tests for the notifications router.

Covers:
- GET  /api/notifications             — list notifications (paginated)
- GET  /api/notifications/unread-count — sidebar badge count
- PATCH /api/notifications/read-all   — mark all read
- PATCH /api/notifications/{id}/read  — mark single notification read

Uses AsyncClient + app.dependency_overrides pattern (same as test_activity_endpoints.py).
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
NOTIF_ID = str(uuid4())
AUTH_HEADERS = {"Authorization": "Bearer test-token-notifications"}


# ── Helpers ────────────────────────────────────────────────────────────────────


def make_client() -> AsyncClient:
    """Return a fresh async test client."""
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def make_chain(data=None, count=None, side_effect=None) -> MagicMock:
    """Build a mock Supabase query chain.

    Supports chains used by the notifications router:
      .table().select().eq().eq().execute()                 (unread-count)
      .table().select().eq().order().range().execute()      (list)
      .table().update().eq().eq().execute()                 (mark-read, read-all)
    """
    result = MagicMock()
    result.data = data if data is not None else []
    result.count = count

    if side_effect:
        execute = AsyncMock(side_effect=side_effect)
    else:
        execute = AsyncMock(return_value=result)

    chain = MagicMock()
    for method in ("select", "eq", "order", "range", "update", "not_"):
        getattr(chain, method).return_value = chain
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


def _sample_notification(
    notif_id: str | None = None,
    is_read: bool = False,
) -> dict:
    return {
        "id": notif_id or str(uuid4()),
        "type": "badge_earned",
        "title": "You earned a badge!",
        "body": "Congratulations on your Gold badge.",
        "is_read": is_read,
        "reference_id": str(uuid4()),
        "created_at": "2026-04-19T10:00:00Z",
    }


# ── GET /api/notifications/unread-count ───────────────────────────────────────


class TestUnreadCountEndpoint:
    """HTTP-level tests for GET /api/notifications/unread-count."""

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_unread(self):
        """count=0 from DB → unread_count=0 in response."""
        db = make_db({"notifications": {"data": [], "count": 0}})
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.get("/api/notifications/unread-count", headers=AUTH_HEADERS)
            assert response.status_code == 200
            assert response.json()["unread_count"] == 0
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_correct_unread_count(self):
        """count=5 from DB → unread_count=5 in response."""
        db = make_db({"notifications": {"data": [], "count": 5}})
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.get("/api/notifications/unread-count", headers=AUTH_HEADERS)
            assert response.status_code == 200
            assert response.json()["unread_count"] == 5
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_requires_authentication(self):
        """No Authorization header → 401."""
        try:
            async with make_client() as client:
                response = await client.get("/api/notifications/unread-count")
            assert response.status_code == 401
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_null_count_returns_zero(self):
        """DB returns count=None (no rows at all) → unread_count=0, not crash."""
        db = make_db({"notifications": {"data": [], "count": None}})
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.get("/api/notifications/unread-count", headers=AUTH_HEADERS)
            assert response.status_code == 200
            assert response.json()["unread_count"] == 0
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)


# ── GET /api/notifications ────────────────────────────────────────────────────


class TestListNotificationsEndpoint:
    """HTTP-level tests for GET /api/notifications."""

    @pytest.mark.asyncio
    async def test_returns_200_with_empty_list(self):
        """No notifications → 200 with empty list and zero counts."""
        db = make_db({"notifications": {"data": [], "count": 0}})
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.get("/api/notifications", headers=AUTH_HEADERS)
            assert response.status_code == 200
            body = response.json()
            assert body["notifications"] == []
            assert body["unread_count"] == 0
            assert body["total"] == 0
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_notifications_list(self):
        """Two notifications returned from DB → appear in response with correct fields."""
        notifs = [_sample_notification(), _sample_notification(is_read=True)]
        db = make_db({"notifications": {"data": notifs, "count": 2}})
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.get("/api/notifications", headers=AUTH_HEADERS)
            assert response.status_code == 200
            body = response.json()
            assert len(body["notifications"]) == 2
            assert body["total"] == 2
            # first notification is unread → unread_count derived from page
            assert body["unread_count"] == 1
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_notification_schema_fields(self):
        """Response notification objects contain all required schema fields."""
        notif = _sample_notification(notif_id=NOTIF_ID)
        db = make_db({"notifications": {"data": [notif], "count": 1}})
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.get("/api/notifications", headers=AUTH_HEADERS)
            assert response.status_code == 200
            item = response.json()["notifications"][0]
            for field in ("id", "type", "title", "body", "is_read", "reference_id", "created_at"):
                assert field in item, f"Missing field '{field}' in notification object"
            assert item["id"] == NOTIF_ID
            assert item["type"] == "badge_earned"
            assert item["is_read"] is False
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_unread_count_derived_from_page(self):
        """unread_count reflects only unread items on the fetched page."""
        notifs = [
            _sample_notification(is_read=False),
            _sample_notification(is_read=False),
            _sample_notification(is_read=True),
        ]
        db = make_db({"notifications": {"data": notifs, "count": 10}})
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.get("/api/notifications", headers=AUTH_HEADERS)
            assert response.status_code == 200
            body = response.json()
            assert body["unread_count"] == 2
            assert body["total"] == 10
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_pagination_limit_param_accepted(self):
        """limit query param is forwarded; response honours the constraint."""
        notifs = [_sample_notification() for _ in range(5)]
        db = make_db({"notifications": {"data": notifs[:3], "count": 5}})
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.get(
                    "/api/notifications",
                    params={"limit": 3, "offset": 0},
                    headers=AUTH_HEADERS,
                )
            assert response.status_code == 200
            body = response.json()
            assert len(body["notifications"]) == 3
            assert body["total"] == 5
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_pagination_limit_max_50(self):
        """limit > 50 → 422 Unprocessable Entity."""
        db = make_db()
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.get(
                    "/api/notifications",
                    params={"limit": 100},
                    headers=AUTH_HEADERS,
                )
            assert response.status_code == 422
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_pagination_negative_offset_rejected(self):
        """offset < 0 → 422 Unprocessable Entity."""
        db = make_db()
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.get(
                    "/api/notifications",
                    params={"offset": -1},
                    headers=AUTH_HEADERS,
                )
            assert response.status_code == 422
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_null_total_count_returns_zero(self):
        """DB count=None → total=0 without crashing."""
        db = make_db({"notifications": {"data": [], "count": None}})
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.get("/api/notifications", headers=AUTH_HEADERS)
            assert response.status_code == 200
            assert response.json()["total"] == 0
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_requires_authentication(self):
        """No Authorization header → 401."""
        try:
            async with make_client() as client:
                response = await client.get("/api/notifications")
            assert response.status_code == 401
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)


# ── PATCH /api/notifications/read-all ────────────────────────────────────────


class TestMarkAllReadEndpoint:
    """HTTP-level tests for PATCH /api/notifications/read-all."""

    @pytest.mark.asyncio
    async def test_returns_200_with_zero_unread(self):
        """Happy path → 200 with unread_count=0."""
        db = make_db({"notifications": {"data": [], "count": 0}})
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.patch("/api/notifications/read-all", headers=AUTH_HEADERS)
            assert response.status_code == 200
            assert response.json()["unread_count"] == 0
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_always_returns_zero_unread_after_mark_all(self):
        """Even when DB has many records, response unread_count is always 0."""
        db = make_db({"notifications": {"data": [_sample_notification() for _ in range(10)], "count": 10}})
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.patch("/api/notifications/read-all", headers=AUTH_HEADERS)
            assert response.status_code == 200
            assert response.json()["unread_count"] == 0
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_requires_authentication(self):
        """No Authorization header → 401."""
        try:
            async with make_client() as client:
                response = await client.patch("/api/notifications/read-all")
            assert response.status_code == 401
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)


# ── PATCH /api/notifications/{id}/read ───────────────────────────────────────


class TestMarkSingleReadEndpoint:
    """HTTP-level tests for PATCH /api/notifications/{notification_id}/read."""

    @pytest.mark.asyncio
    async def test_returns_updated_notification(self):
        """DB returns updated row → 200 with notification object."""
        updated = _sample_notification(notif_id=NOTIF_ID, is_read=True)
        db = make_db({"notifications": {"data": [updated]}})
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.patch(f"/api/notifications/{NOTIF_ID}/read", headers=AUTH_HEADERS)
            assert response.status_code == 200
            body = response.json()
            assert body["id"] == NOTIF_ID
            assert body["is_read"] is True
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_404_when_notification_not_found(self):
        """DB returns empty data (wrong user or missing ID) → 404."""
        db = make_db({"notifications": {"data": []}})
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.patch(f"/api/notifications/{NOTIF_ID}/read", headers=AUTH_HEADERS)
            assert response.status_code == 404
            detail = response.json()["detail"]
            assert detail["code"] == "NOTIFICATION_NOT_FOUND"
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_404_error_message_present(self):
        """404 response includes a human-readable message."""
        db = make_db({"notifications": {"data": []}})
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.patch(f"/api/notifications/{NOTIF_ID}/read", headers=AUTH_HEADERS)
            assert response.status_code == 404
            assert "message" in response.json()["detail"]
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_response_contains_all_notification_fields(self):
        """Updated notification response includes all NotificationOut fields."""
        updated = _sample_notification(notif_id=NOTIF_ID, is_read=True)
        db = make_db({"notifications": {"data": [updated]}})
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.patch(f"/api/notifications/{NOTIF_ID}/read", headers=AUTH_HEADERS)
            assert response.status_code == 200
            body = response.json()
            for field in ("id", "type", "title", "body", "is_read", "reference_id", "created_at"):
                assert field in body, f"Missing field '{field}' in PATCH /read response"
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_requires_authentication(self):
        """No Authorization header → 401."""
        try:
            async with make_client() as client:
                response = await client.patch(f"/api/notifications/{NOTIF_ID}/read")
            assert response.status_code == 401
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_notification_id_in_path_is_arbitrary_string(self):
        """UUID path param works; any non-empty string is accepted by FastAPI."""
        custom_id = "custom-notif-123"
        updated = _sample_notification(notif_id=custom_id, is_read=True)
        db = make_db({"notifications": {"data": [updated]}})
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                response = await client.patch(f"/api/notifications/{custom_id}/read", headers=AUTH_HEADERS)
            assert response.status_code == 200
            assert response.json()["id"] == custom_id
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)
