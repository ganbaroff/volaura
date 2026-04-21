"""HTTP-level integration tests for /api/analytics router.

Covers:
- POST /api/analytics/event — auth required, 204 on success, various payloads
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_user
from app.main import app

USER_ID = str(uuid4())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class MockResult:
    def __init__(self, data=None, count: int | None = None):
        self.data = data
        self.count = count


def make_client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _make_user_db() -> MagicMock:
    """User-scoped DB mock — only analytics_events insert needed."""
    db = MagicMock()
    insert_result = MockResult(data=[{"id": str(uuid4())}])
    db.table.return_value.insert.return_value.execute = AsyncMock(return_value=insert_result)
    return db


_VALID_BODY = {
    "event_name": "page_view",
    "properties": {"page": "/dashboard"},
    "session_id": "sess-abc",
    "locale": "az",
    "platform": "web",
}


# ---------------------------------------------------------------------------
# POST /api/analytics/event — happy paths
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ingest_event_returns_204():
    db = _make_user_db()
    app.dependency_overrides[get_supabase_user] = lambda: db
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    try:
        async with make_client() as client:
            resp = await client.post(
                "/api/analytics/event",
                json=_VALID_BODY,
                headers={"Authorization": f"Bearer fake-{USER_ID}"},
            )
        assert resp.status_code == 204
        assert resp.content == b""
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_ingest_event_minimal_body():
    """Only event_name is required — all other fields are optional."""
    db = _make_user_db()
    app.dependency_overrides[get_supabase_user] = lambda: db
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    try:
        async with make_client() as client:
            resp = await client.post(
                "/api/analytics/event",
                json={"event_name": "button_click"},
                headers={"Authorization": "Bearer fake"},
            )
        assert resp.status_code == 204
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_ingest_event_with_null_optional_fields():
    db = _make_user_db()
    app.dependency_overrides[get_supabase_user] = lambda: db
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    try:
        async with make_client() as client:
            resp = await client.post(
                "/api/analytics/event",
                json={
                    "event_name": "assessment_started",
                    "properties": None,
                    "session_id": None,
                    "locale": None,
                    "platform": "web",
                },
                headers={"Authorization": "Bearer fake"},
            )
        assert resp.status_code == 204
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_ingest_event_mobile_platform():
    db = _make_user_db()
    app.dependency_overrides[get_supabase_user] = lambda: db
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    try:
        async with make_client() as client:
            resp = await client.post(
                "/api/analytics/event",
                json={"event_name": "app_open", "platform": "mobile"},
                headers={"Authorization": "Bearer fake"},
            )
        assert resp.status_code == 204
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_ingest_event_calls_track_event_with_correct_args():
    """Verify track_event is called with the right user_id and event_name."""
    db = _make_user_db()
    app.dependency_overrides[get_supabase_user] = lambda: db
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID

    captured: dict = {}

    async def fake_track_event(**kwargs):
        captured.update(kwargs)

    try:
        with patch("app.routers.analytics.track_event", side_effect=fake_track_event):
            async with make_client() as client:
                await client.post(
                    "/api/analytics/event",
                    json={"event_name": "quiz_completed", "locale": "en"},
                    headers={"Authorization": "Bearer fake"},
                )
        assert captured["user_id"] == USER_ID
        assert captured["event_name"] == "quiz_completed"
        assert captured["locale"] == "en"
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /api/analytics/event — auth failures
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ingest_event_401_when_no_auth_header():
    """No Authorization header → 401 from get_supabase_user dep."""
    try:
        async with make_client() as client:
            resp = await client.post("/api/analytics/event", json=_VALID_BODY)
        assert resp.status_code == 401
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_ingest_event_401_when_bearer_token_empty():
    """'Bearer ' with no token value → 401."""
    try:
        async with make_client() as client:
            resp = await client.post(
                "/api/analytics/event",
                json=_VALID_BODY,
                headers={"Authorization": "Bearer "},
            )
        assert resp.status_code == 401
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_ingest_event_401_when_not_bearer_scheme():
    """Non-Bearer auth scheme → 401."""
    try:
        async with make_client() as client:
            resp = await client.post(
                "/api/analytics/event",
                json=_VALID_BODY,
                headers={"Authorization": "Basic dXNlcjpwYXNz"},
            )
        assert resp.status_code == 401
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /api/analytics/event — validation / bad input
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ingest_event_422_when_event_name_missing():
    """Missing required field event_name → 422 Unprocessable Entity."""
    db = _make_user_db()
    app.dependency_overrides[get_supabase_user] = lambda: db
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    try:
        async with make_client() as client:
            resp = await client.post(
                "/api/analytics/event",
                json={"properties": {"x": 1}},
                headers={"Authorization": "Bearer fake"},
            )
        assert resp.status_code == 422
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_ingest_event_422_when_body_is_empty_json():
    db = _make_user_db()
    app.dependency_overrides[get_supabase_user] = lambda: db
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    try:
        async with make_client() as client:
            resp = await client.post(
                "/api/analytics/event",
                json={},
                headers={"Authorization": "Bearer fake"},
            )
        assert resp.status_code == 422
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /api/analytics/event — fire-and-forget error handling
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ingest_event_still_204_when_db_insert_fails():
    """track_event never raises — DB failure must not surface as 500."""
    db = _make_user_db()
    db.table.return_value.insert.return_value.execute = AsyncMock(side_effect=Exception("DB down"))
    app.dependency_overrides[get_supabase_user] = lambda: db
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    try:
        async with make_client() as client:
            resp = await client.post(
                "/api/analytics/event",
                json=_VALID_BODY,
                headers={"Authorization": "Bearer fake"},
            )
        # fire-and-forget: service swallows error, endpoint still returns 204
        assert resp.status_code == 204
    finally:
        app.dependency_overrides.clear()
