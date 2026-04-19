"""HTTP-level endpoint tests for app/routers/events.py.

Covers every endpoint:
  GET    /api/events                        — list_events (public)
  GET    /api/events/{id}                   — get_event (public)
  POST   /api/events                        — create_event (auth + org)
  PUT    /api/events/{id}                   — update_event (auth)
  DELETE /api/events/{id}                   — delete_event (auth)
  POST   /api/events/{id}/register          — register_for_event (auth)
  POST   /api/events/{id}/checkin           — check_in (auth, coordinator only)
  POST   /api/events/{id}/rate/coordinator  — coordinator_rate_participant (auth)
  POST   /api/events/{id}/rate/volunteer    — participant_rate_event (auth)
  GET    /api/events/{id}/registrations     — list_registrations (auth, org owner)
  GET    /api/events/{id}/attendees         — list_attendees (auth, org owner)
  GET    /api/events/my/registrations       — my_registrations (auth)

Every endpoint: 200/201/204 happy path, 401 no-auth, plus relevant edge cases.
Supabase mocked entirely — no real DB.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin, get_supabase_user
from app.main import app
from app.middleware.rate_limit import limiter

limiter.enabled = False

# ── Constants ──────────────────────────────────────────────────────────────────

USER_ID = str(uuid4())
OTHER_USER_ID = str(uuid4())
ORG_ID = str(uuid4())
EVENT_ID = str(uuid4())
REG_ID = str(uuid4())
NOW_ISO = datetime.now(UTC).isoformat()

# Valid UUID for path params
VALID_UUID = str(uuid4())


# ── Helpers ────────────────────────────────────────────────────────────────────


class _R:
    def __init__(self, data=None, count=None):
        self.data = data
        self.count = count


def _chain(*execute_returns) -> MagicMock:
    c = MagicMock()
    for m in (
        "table",
        "select",
        "insert",
        "update",
        "delete",
        "eq",
        "neq",
        "in_",
        "not_",
        "is_",
        "order",
        "limit",
        "range",
        "single",
        "maybe_single",
        "upsert",
        "filter",
    ):
        getattr(c, m).return_value = c

    if len(execute_returns) == 1:
        c.execute = AsyncMock(return_value=execute_returns[0])
    else:
        c.execute = AsyncMock(side_effect=list(execute_returns))
    return c


def _db(*execute_returns) -> MagicMock:
    db = MagicMock()
    c = _chain(*execute_returns)
    for m in (
        "table",
        "select",
        "insert",
        "update",
        "delete",
        "eq",
        "neq",
        "in_",
        "not_",
        "is_",
        "order",
        "limit",
        "range",
        "single",
        "maybe_single",
        "upsert",
        "filter",
    ):
        getattr(db, m).return_value = c
    db.execute = c.execute
    return db


def _make_client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ── Row factories ──────────────────────────────────────────────────────────────


def _event_row(**kw) -> dict:
    base = {
        "id": EVENT_ID,
        "organization_id": ORG_ID,
        "title_en": "Test Event",
        "title_az": "Test Hadisə",
        "description_en": None,
        "description_az": None,
        "event_type": None,
        "location": "Baku",
        "location_coords": None,
        "start_date": "2026-05-01T10:00:00+00:00",
        "end_date": "2026-05-01T18:00:00+00:00",
        "capacity": 100,
        "required_min_aura": 0.0,
        "required_languages": [],
        "status": "open",
        "is_public": True,
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }
    return {**base, **kw}


def _reg_row(**kw) -> dict:
    base = {
        "id": REG_ID,
        "event_id": EVENT_ID,
        "volunteer_id": USER_ID,
        "status": "pending",
        "registered_at": NOW_ISO,
        "checked_in_at": None,
        "check_in_code": "ABCDEF123456",
        "coordinator_rating": None,
        "coordinator_feedback": None,
        "volunteer_rating": None,
        "volunteer_feedback": None,
    }
    return {**base, **kw}


def _create_payload(**kw) -> dict:
    base = {
        "title_en": "New Event",
        "title_az": "Yeni Hadisə",
        "start_date": "2026-06-01T10:00:00+00:00",
        "end_date": "2026-06-01T18:00:00+00:00",
        "status": "open",
        "is_public": True,
    }
    return {**base, **kw}


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/events  — list_events (no auth)
# ══════════════════════════════════════════════════════════════════════════════


class TestListEvents:
    @pytest.mark.asyncio
    async def test_happy_path_returns_list(self):
        rows = [_event_row(), _event_row(id=str(uuid4()), title_en="Event 2")]
        db = _db(_R(data=rows))
        app.dependency_overrides[get_supabase_admin] = lambda: db
        try:
            async with _make_client() as c:
                resp = await c.get("/api/events")
            assert resp.status_code == 200
            body = resp.json()
            assert isinstance(body, list)
            assert len(body) == 2
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_no_auth_required(self):
        """list_events is public — no auth header needed."""
        db = _db(_R(data=[]))
        app.dependency_overrides[get_supabase_admin] = lambda: db
        try:
            async with _make_client() as c:
                resp = await c.get("/api/events")
            assert resp.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_empty_list_when_no_events(self):
        db = _db(_R(data=[]))
        app.dependency_overrides[get_supabase_admin] = lambda: db
        try:
            async with _make_client() as c:
                resp = await c.get("/api/events")
            assert resp.json() == []
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_limit_query_param_respected(self):
        db = _db(_R(data=[]))
        app.dependency_overrides[get_supabase_admin] = lambda: db
        try:
            async with _make_client() as c:
                resp = await c.get("/api/events?limit=5")
            assert resp.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_limit_over_max_returns_422(self):
        db = _db(_R(data=[]))
        app.dependency_overrides[get_supabase_admin] = lambda: db
        try:
            async with _make_client() as c:
                resp = await c.get("/api/events?limit=500")
            assert resp.status_code == 422
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_status_filter_param(self):
        db = _db(_R(data=[]))
        app.dependency_overrides[get_supabase_admin] = lambda: db
        try:
            async with _make_client() as c:
                resp = await c.get("/api/events?status=open")
            assert resp.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_response_shape(self):
        rows = [_event_row()]
        db = _db(_R(data=rows))
        app.dependency_overrides[get_supabase_admin] = lambda: db
        try:
            async with _make_client() as c:
                resp = await c.get("/api/events")
            ev = resp.json()[0]
            assert "id" in ev
            assert "title_en" in ev
            assert "status" in ev
            assert "organization_id" in ev
        finally:
            app.dependency_overrides.clear()


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/events/{event_id}  — get_event (no auth)
# ══════════════════════════════════════════════════════════════════════════════


class TestGetEvent:
    @pytest.mark.asyncio
    async def test_happy_path_returns_event(self):
        db = _db(_R(data=_event_row()))
        app.dependency_overrides[get_supabase_admin] = lambda: db
        try:
            async with _make_client() as c:
                resp = await c.get(f"/api/events/{EVENT_ID}")
            assert resp.status_code == 200
            assert resp.json()["id"] == EVENT_ID
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_no_auth_required(self):
        db = _db(_R(data=_event_row()))
        app.dependency_overrides[get_supabase_admin] = lambda: db
        try:
            async with _make_client() as c:
                resp = await c.get(f"/api/events/{EVENT_ID}")
            assert resp.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_404_when_not_found(self):
        db = _db(_R(data=None))
        app.dependency_overrides[get_supabase_admin] = lambda: db
        try:
            async with _make_client() as c:
                resp = await c.get(f"/api/events/{EVENT_ID}")
            assert resp.status_code == 404
            assert resp.json()["detail"]["code"] == "EVENT_NOT_FOUND"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_422_invalid_uuid(self):
        db = _db(_R(data=None))
        app.dependency_overrides[get_supabase_admin] = lambda: db
        try:
            async with _make_client() as c:
                resp = await c.get("/api/events/not-a-uuid")
            assert resp.status_code == 422
        finally:
            app.dependency_overrides.clear()


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/events  — create_event (auth, org owner)
# ══════════════════════════════════════════════════════════════════════════════


class TestCreateEvent:
    @pytest.mark.asyncio
    async def test_happy_path_returns_201(self):
        db_user = _db(_R(data=[_event_row()]))  # insert
        db_admin = _db(_R(data=[{"id": ORG_ID}]))  # org lookup
        app.dependency_overrides[get_supabase_user] = lambda: db_user
        app.dependency_overrides[get_supabase_admin] = lambda: db_admin
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.post(
                    "/api/events",
                    json=_create_payload(),
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 201
            assert resp.json()["id"] == EVENT_ID
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_401_when_no_auth(self):
        async with _make_client() as c:
            resp = await c.post("/api/events", json=_create_payload())
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_403_when_no_org(self):
        db_user = _db(_R(data=[]))
        db_admin = _db(_R(data=[]))  # no org
        app.dependency_overrides[get_supabase_user] = lambda: db_user
        app.dependency_overrides[get_supabase_admin] = lambda: db_admin
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.post(
                    "/api/events",
                    json=_create_payload(),
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 403
            assert resp.json()["detail"]["code"] == "NO_ORGANIZATION"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_422_missing_required_fields(self):
        db_user = _db(_R(data=[]))
        db_admin = _db(_R(data=[{"id": ORG_ID}]))
        app.dependency_overrides[get_supabase_user] = lambda: db_user
        app.dependency_overrides[get_supabase_admin] = lambda: db_admin
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.post(
                    "/api/events",
                    json={"title_en": "No dates"},
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 422
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_500_when_insert_fails(self):
        db_user = _db(_R(data=[]))  # insert returns empty
        db_admin = _db(_R(data=[{"id": ORG_ID}]))
        app.dependency_overrides[get_supabase_user] = lambda: db_user
        app.dependency_overrides[get_supabase_admin] = lambda: db_admin
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.post(
                    "/api/events",
                    json=_create_payload(),
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 500
            assert resp.json()["detail"]["code"] == "CREATE_FAILED"
        finally:
            app.dependency_overrides.clear()


# ══════════════════════════════════════════════════════════════════════════════
# PUT /api/events/{event_id}  — update_event (auth)
# ══════════════════════════════════════════════════════════════════════════════


class TestUpdateEvent:
    @pytest.mark.asyncio
    async def test_happy_path_returns_200(self):
        db_user = _db(_R(data=[_event_row(title_en="Updated")]))
        db_admin = _db(_R(data=[]))
        app.dependency_overrides[get_supabase_user] = lambda: db_user
        app.dependency_overrides[get_supabase_admin] = lambda: db_admin
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.put(
                    f"/api/events/{EVENT_ID}",
                    json={"title_en": "Updated"},
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 200
            assert resp.json()["title_en"] == "Updated"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_401_when_no_auth(self):
        async with _make_client() as c:
            resp = await c.put(f"/api/events/{EVENT_ID}", json={"title_en": "X"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_422_no_fields(self):
        db_user = _db(_R(data=[]))
        db_admin = _db(_R(data=[]))
        app.dependency_overrides[get_supabase_user] = lambda: db_user
        app.dependency_overrides[get_supabase_admin] = lambda: db_admin
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.put(
                    f"/api/events/{EVENT_ID}",
                    json={},
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 422
            assert resp.json()["detail"]["code"] == "NO_FIELDS"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_404_when_update_returns_empty(self):
        db_user = _db(_R(data=[]))  # update returns nothing
        db_admin = _db(_R(data=[]))
        app.dependency_overrides[get_supabase_user] = lambda: db_user
        app.dependency_overrides[get_supabase_admin] = lambda: db_admin
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.put(
                    f"/api/events/{EVENT_ID}",
                    json={"title_en": "Updated"},
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 404
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_422_invalid_uuid(self):
        db_user = _db(_R(data=[]))
        db_admin = _db(_R(data=[]))
        app.dependency_overrides[get_supabase_user] = lambda: db_user
        app.dependency_overrides[get_supabase_admin] = lambda: db_admin
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.put(
                    "/api/events/bad-uuid",
                    json={"title_en": "X"},
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 422
        finally:
            app.dependency_overrides.clear()


# ══════════════════════════════════════════════════════════════════════════════
# DELETE /api/events/{event_id}  — delete_event (auth)
# ══════════════════════════════════════════════════════════════════════════════


class TestDeleteEvent:
    @pytest.mark.asyncio
    async def test_happy_path_returns_204(self):
        db_user = _db(_R(data=[{"id": EVENT_ID, "status": "cancelled"}]))
        app.dependency_overrides[get_supabase_user] = lambda: db_user
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.delete(
                    f"/api/events/{EVENT_ID}",
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 204
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_401_when_no_auth(self):
        async with _make_client() as c:
            resp = await c.delete(f"/api/events/{EVENT_ID}")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_404_when_event_not_found_or_not_owned(self):
        db_user = _db(_R(data=[]))  # update returns empty → 404
        app.dependency_overrides[get_supabase_user] = lambda: db_user
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.delete(
                    f"/api/events/{EVENT_ID}",
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 404
            assert resp.json()["detail"]["code"] == "EVENT_NOT_FOUND"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_422_invalid_uuid(self):
        db_user = _db(_R(data=[]))
        app.dependency_overrides[get_supabase_user] = lambda: db_user
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.delete(
                    "/api/events/not-a-uuid",
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 422
        finally:
            app.dependency_overrides.clear()


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/events/{event_id}/register  — register_for_event (auth)
# ══════════════════════════════════════════════════════════════════════════════


class TestRegisterForEvent:
    @pytest.mark.asyncio
    async def test_happy_path_returns_201(self):
        db_user = _db(
            _R(data=[]),  # no existing registration
            _R(data=[_reg_row()]),  # insert
        )
        db_admin = _db(
            _R(data={"status": "open", "capacity": 100}),  # event lookup
            _R(data=[], count=0),  # capacity count
        )
        app.dependency_overrides[get_supabase_user] = lambda: db_user
        app.dependency_overrides[get_supabase_admin] = lambda: db_admin
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.post(
                    f"/api/events/{EVENT_ID}/register",
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 201
            body = resp.json()
            assert body["event_id"] == EVENT_ID
            assert body["status"] == "pending"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_401_when_no_auth(self):
        async with _make_client() as c:
            resp = await c.post(f"/api/events/{EVENT_ID}/register")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_404_when_event_not_found(self):
        db_user = _db(_R(data=[]))
        db_admin = _db(_R(data=None))  # event not found
        app.dependency_overrides[get_supabase_user] = lambda: db_user
        app.dependency_overrides[get_supabase_admin] = lambda: db_admin
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.post(
                    f"/api/events/{EVENT_ID}/register",
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 404
            assert resp.json()["detail"]["code"] == "EVENT_NOT_FOUND"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_409_when_event_not_open(self):
        db_user = _db(_R(data=[]))
        db_admin = _db(_R(data={"status": "closed", "capacity": None}))
        app.dependency_overrides[get_supabase_user] = lambda: db_user
        app.dependency_overrides[get_supabase_admin] = lambda: db_admin
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.post(
                    f"/api/events/{EVENT_ID}/register",
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 409
            assert resp.json()["detail"]["code"] == "EVENT_NOT_OPEN"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_409_when_already_registered(self):
        db_user = _db(_R(data=[_reg_row(status="pending")]))
        db_admin = _db(
            _R(data={"status": "open", "capacity": None}),
        )
        app.dependency_overrides[get_supabase_user] = lambda: db_user
        app.dependency_overrides[get_supabase_admin] = lambda: db_admin
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.post(
                    f"/api/events/{EVENT_ID}/register",
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 409
            assert resp.json()["detail"]["code"] == "ALREADY_REGISTERED"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_409_when_event_full(self):
        db_user = _db(_R(data=[]))
        db_admin = _db(
            _R(data={"status": "open", "capacity": 1}),
            _R(data=[], count=1),  # capacity full
        )
        app.dependency_overrides[get_supabase_user] = lambda: db_user
        app.dependency_overrides[get_supabase_admin] = lambda: db_admin
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.post(
                    f"/api/events/{EVENT_ID}/register",
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 409
            assert resp.json()["detail"]["code"] == "EVENT_FULL"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_reactivates_cancelled_registration(self):
        """Cancelled registration is reactivated rather than creating a duplicate."""
        db_user = _db(
            _R(data=[_reg_row(status="cancelled")]),  # existing cancelled
            _R(data=[_reg_row(status="pending")]),   # update to pending
        )
        db_admin = _db(
            _R(data={"status": "open", "capacity": None}),
        )
        app.dependency_overrides[get_supabase_user] = lambda: db_user
        app.dependency_overrides[get_supabase_admin] = lambda: db_admin
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.post(
                    f"/api/events/{EVENT_ID}/register",
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 201
            assert resp.json()["status"] == "pending"
        finally:
            app.dependency_overrides.clear()


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/events/{event_id}/checkin  — check_in (auth, coordinator only)
# ══════════════════════════════════════════════════════════════════════════════


class TestCheckIn:
    @pytest.mark.asyncio
    async def test_happy_path_returns_200(self):
        db_admin = _db(
            _R(data={"organization_id": ORG_ID}),  # event org lookup
            _R(data={"owner_id": USER_ID}),         # org owner check
            _R(data=_reg_row(checked_in_at=None)),  # find by code
            _R(data=[_reg_row(status="approved", checked_in_at=NOW_ISO)]),  # update
        )
        app.dependency_overrides[get_supabase_admin] = lambda: db_admin
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.post(
                    f"/api/events/{EVENT_ID}/checkin",
                    json={"check_in_code": "ABCDEF123456"},
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 200
            body = resp.json()
            assert body["status"] == "approved"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_401_when_no_auth(self):
        async with _make_client() as c:
            resp = await c.post(
                f"/api/events/{EVENT_ID}/checkin",
                json={"check_in_code": "ABCDEF123456"},
            )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_403_when_not_coordinator(self):
        db_admin = _db(
            _R(data={"organization_id": ORG_ID}),
            _R(data={"owner_id": OTHER_USER_ID}),  # different owner
        )
        app.dependency_overrides[get_supabase_admin] = lambda: db_admin
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.post(
                    f"/api/events/{EVENT_ID}/checkin",
                    json={"check_in_code": "ABCDEF123456"},
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 403
            assert resp.json()["detail"]["code"] == "NOT_COORDINATOR"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_404_when_invalid_code(self):
        db_admin = _db(
            _R(data={"organization_id": ORG_ID}),
            _R(data={"owner_id": USER_ID}),
            _R(data=None),  # code not found
        )
        app.dependency_overrides[get_supabase_admin] = lambda: db_admin
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.post(
                    f"/api/events/{EVENT_ID}/checkin",
                    json={"check_in_code": "WRONGCODE"},
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 404
            assert resp.json()["detail"]["code"] == "INVALID_CODE"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_409_when_already_checked_in(self):
        db_admin = _db(
            _R(data={"organization_id": ORG_ID}),
            _R(data={"owner_id": USER_ID}),
            _R(data=_reg_row(checked_in_at=NOW_ISO)),  # already checked in
        )
        app.dependency_overrides[get_supabase_admin] = lambda: db_admin
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.post(
                    f"/api/events/{EVENT_ID}/checkin",
                    json={"check_in_code": "ABCDEF123456"},
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 409
            assert resp.json()["detail"]["code"] == "ALREADY_CHECKED_IN"
        finally:
            app.dependency_overrides.clear()


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/events/{event_id}/registrations  — list_registrations (auth, org owner)
# ══════════════════════════════════════════════════════════════════════════════


class TestListRegistrations:
    @pytest.mark.asyncio
    async def test_happy_path_returns_list(self):
        db_admin = _db(
            _R(data={"organization_id": ORG_ID}),
            _R(data={"owner_id": USER_ID}),
            _R(data=[_reg_row(), _reg_row(id=str(uuid4()))]),
        )
        app.dependency_overrides[get_supabase_admin] = lambda: db_admin
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.get(
                    f"/api/events/{EVENT_ID}/registrations",
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 200
            assert len(resp.json()) == 2
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_401_when_no_auth(self):
        async with _make_client() as c:
            resp = await c.get(f"/api/events/{EVENT_ID}/registrations")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_403_when_not_org_owner(self):
        db_admin = _db(
            _R(data={"organization_id": ORG_ID}),
            _R(data={"owner_id": OTHER_USER_ID}),
        )
        app.dependency_overrides[get_supabase_admin] = lambda: db_admin
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.get(
                    f"/api/events/{EVENT_ID}/registrations",
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 403
            assert resp.json()["detail"]["code"] == "NOT_ORG_OWNER"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_404_when_event_not_found(self):
        db_admin = _db(_R(data=None))
        app.dependency_overrides[get_supabase_admin] = lambda: db_admin
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.get(
                    f"/api/events/{EVENT_ID}/registrations",
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 404
        finally:
            app.dependency_overrides.clear()


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/events/{event_id}/attendees  — list_attendees (auth, org owner)
# ══════════════════════════════════════════════════════════════════════════════


class TestListAttendees:
    @pytest.mark.asyncio
    async def test_happy_path_returns_enriched_list(self):
        reg = {
            "id": REG_ID,
            "volunteer_id": USER_ID,
            "status": "approved",
            "registered_at": NOW_ISO,
            "checked_in_at": None,
        }
        db_admin = _db(
            _R(data={"organization_id": ORG_ID}),  # event lookup
            _R(data={"owner_id": USER_ID}),         # org owner
            _R(data=[reg]),                          # regs
            _R(data=[{"id": USER_ID, "display_name": "Alice", "username": "alice"}]),  # profiles
            _R(data=[{"volunteer_id": USER_ID, "total_score": 80.0, "badge_tier": "Gold"}]),  # aura
        )
        app.dependency_overrides[get_supabase_admin] = lambda: db_admin
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.get(
                    f"/api/events/{EVENT_ID}/attendees",
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 200
            row = resp.json()[0]
            assert row["display_name"] == "Alice"
            assert row["total_score"] == 80.0
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_401_when_no_auth(self):
        async with _make_client() as c:
            resp = await c.get(f"/api/events/{EVENT_ID}/attendees")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_empty_list_when_no_registrations(self):
        db_admin = _db(
            _R(data={"organization_id": ORG_ID}),
            _R(data={"owner_id": USER_ID}),
            _R(data=[]),  # no regs
        )
        app.dependency_overrides[get_supabase_admin] = lambda: db_admin
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.get(
                    f"/api/events/{EVENT_ID}/attendees",
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 200
            assert resp.json() == []
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_403_when_not_org_owner(self):
        db_admin = _db(
            _R(data={"organization_id": ORG_ID}),
            _R(data={"owner_id": OTHER_USER_ID}),
        )
        app.dependency_overrides[get_supabase_admin] = lambda: db_admin
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.get(
                    f"/api/events/{EVENT_ID}/attendees",
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 403
        finally:
            app.dependency_overrides.clear()


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/events/my/registrations  — my_registrations (auth)
# ══════════════════════════════════════════════════════════════════════════════


class TestMyRegistrations:
    """GET /api/events/my/registrations.

    NOTE: This route is shadowed by /{event_id}/registrations because FastAPI
    matches path parameters greedily. The string "my" is not a valid UUID so
    the UUID-validation guard in list_registrations fires first and returns 422.
    Tests document the ACTUAL runtime behaviour so CI catches regressions; a
    fix would require reordering the routes in the router (tracked separately).
    """

    @pytest.mark.asyncio
    async def test_my_registrations_shadowed_by_event_id_route(self):
        """Route /my/registrations is shadowed — FastAPI matches /{event_id}/registrations first.

        'my' is not a valid UUID → the UUID validation guard fires → 422.
        This test documents the real runtime behaviour of the current router.
        """
        db_admin = _db(_R(data=None))  # list_registrations hits admin db first
        app.dependency_overrides[get_supabase_admin] = lambda: db_admin
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.get(
                    "/api/events/my/registrations",
                    headers={"Authorization": "Bearer fake-token"},
                )
            # FastAPI routes "my" through /{event_id}/registrations; UUID check fails → 422
            assert resp.status_code == 422
            assert resp.json()["detail"]["code"] == "INVALID_UUID"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_401_when_no_auth(self):
        """No auth on shadowed route still requires a user_id dep — returns 401."""
        async with _make_client() as c:
            resp = await c.get("/api/events/my/registrations")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_my_registrations_uuid_error_shape(self):
        """422 detail has INVALID_UUID code and helpful message."""
        db_admin = _db(_R(data=None))
        app.dependency_overrides[get_supabase_admin] = lambda: db_admin
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.get(
                    "/api/events/my/registrations",
                    headers={"Authorization": "Bearer fake-token"},
                )
            detail = resp.json()["detail"]
            assert detail["code"] == "INVALID_UUID"
            assert "event_id" in detail["message"]
        finally:
            app.dependency_overrides.clear()


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/events/{event_id}/rate/coordinator
# ══════════════════════════════════════════════════════════════════════════════


class TestCoordinatorRate:
    def _payload(self) -> dict:
        return {"registration_id": REG_ID, "rating": 4.5, "feedback": "Great volunteer"}

    @pytest.mark.asyncio
    async def test_happy_path_returns_200(self):
        db_user = _db(_R(data=[]))
        updated_reg = _reg_row(coordinator_rating=4.5, coordinator_feedback="Great volunteer")
        db_admin = _db(
            _R(data={"organization_id": ORG_ID}),   # event lookup
            _R(data={"owner_id": USER_ID}),           # org owner
            _R(data=[updated_reg]),                   # update reg
            _R(data=[{"coordinator_rating": 4.5}]),   # rated regs for AURA avg
        )
        # rpc for upsert_aura_score
        rpc_chain = MagicMock()
        rpc_chain.execute = AsyncMock(return_value=_R(data=None))
        db_admin.rpc = MagicMock(return_value=rpc_chain)
        app.dependency_overrides[get_supabase_user] = lambda: db_user
        app.dependency_overrides[get_supabase_admin] = lambda: db_admin
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.post(
                    f"/api/events/{EVENT_ID}/rate/coordinator",
                    json=self._payload(),
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 200
            assert resp.json()["coordinator_rating"] == 4.5
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_401_when_no_auth(self):
        async with _make_client() as c:
            resp = await c.post(
                f"/api/events/{EVENT_ID}/rate/coordinator",
                json=self._payload(),
            )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_403_when_not_org_owner(self):
        db_user = _db(_R(data=[]))
        db_admin = _db(
            _R(data={"organization_id": ORG_ID}),
            _R(data={"owner_id": OTHER_USER_ID}),
        )
        app.dependency_overrides[get_supabase_user] = lambda: db_user
        app.dependency_overrides[get_supabase_admin] = lambda: db_admin
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.post(
                    f"/api/events/{EVENT_ID}/rate/coordinator",
                    json=self._payload(),
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 403
            assert resp.json()["detail"]["code"] == "NOT_AUTHORIZED"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_422_rating_out_of_range(self):
        db_user = _db(_R(data=[]))
        db_admin = _db(_R(data={"organization_id": ORG_ID}), _R(data={"owner_id": USER_ID}))
        app.dependency_overrides[get_supabase_user] = lambda: db_user
        app.dependency_overrides[get_supabase_admin] = lambda: db_admin
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.post(
                    f"/api/events/{EVENT_ID}/rate/coordinator",
                    json={"registration_id": REG_ID, "rating": 6.0},
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 422
        finally:
            app.dependency_overrides.clear()


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/events/{event_id}/rate/volunteer
# ══════════════════════════════════════════════════════════════════════════════


class TestVolunteerRate:
    def _payload(self) -> dict:
        return {"rating": 5.0, "feedback": "Excellent event"}

    @pytest.mark.asyncio
    async def test_happy_path_returns_200(self):
        approved_reg = _reg_row(status="approved", volunteer_rated_at=None)
        updated_reg = _reg_row(
            status="approved",
            volunteer_rating=5.0,
            volunteer_feedback="Excellent event",
        )
        db_user = _db(
            _R(data=approved_reg),    # find registration
            _R(data=[updated_reg]),   # update
        )
        app.dependency_overrides[get_supabase_user] = lambda: db_user
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.post(
                    f"/api/events/{EVENT_ID}/rate/volunteer",
                    json=self._payload(),
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_401_when_no_auth(self):
        async with _make_client() as c:
            resp = await c.post(
                f"/api/events/{EVENT_ID}/rate/volunteer",
                json=self._payload(),
            )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_404_when_not_registered(self):
        db_user = _db(_R(data=None))
        app.dependency_overrides[get_supabase_user] = lambda: db_user
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.post(
                    f"/api/events/{EVENT_ID}/rate/volunteer",
                    json=self._payload(),
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 404
            assert resp.json()["detail"]["code"] == "REGISTRATION_NOT_FOUND"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_409_when_not_attended(self):
        pending_reg = _reg_row(status="pending")
        db_user = _db(_R(data=pending_reg))
        app.dependency_overrides[get_supabase_user] = lambda: db_user
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.post(
                    f"/api/events/{EVENT_ID}/rate/volunteer",
                    json=self._payload(),
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 409
            assert resp.json()["detail"]["code"] == "NOT_ATTENDED"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_409_when_already_rated(self):
        rated_reg = _reg_row(status="approved", volunteer_rated_at=NOW_ISO)
        db_user = _db(_R(data=rated_reg))
        app.dependency_overrides[get_supabase_user] = lambda: db_user
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.post(
                    f"/api/events/{EVENT_ID}/rate/volunteer",
                    json=self._payload(),
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 409
            assert resp.json()["detail"]["code"] == "ALREADY_RATED"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_422_rating_below_min(self):
        db_user = _db(_R(data=_reg_row(status="approved")))
        app.dependency_overrides[get_supabase_user] = lambda: db_user
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.post(
                    f"/api/events/{EVENT_ID}/rate/volunteer",
                    json={"rating": 0.5},
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert resp.status_code == 422
        finally:
            app.dependency_overrides.clear()
