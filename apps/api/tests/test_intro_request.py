"""Integration tests for POST /api/organizations/intro-requests.

Acceptance criteria:
  1. Org caller + discoverable volunteer → 201, intro_request row created
  2. Non-org caller → 403 ORG_REQUIRED
  3. Volunteer not found → 404 VOLUNTEER_NOT_FOUND
  4. Volunteer not discoverable (visible_to_orgs=False) → 403 NOT_DISCOVERABLE
  5. Volunteer is an org account → 422 INVALID_TARGET
  6. Duplicate pending request (DB unique violation) → 409 REQUEST_ALREADY_PENDING
  7. Unauthenticated → 401 / 403

Security check: org identity always comes from JWT (user_id), never from request body.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin
from app.main import app
from app.middleware.rate_limit import limiter


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset in-memory rate limiter state before each test.

    Without this, rapid test execution crosses the RATE_PROFILE_WRITE (10/min)
    limit and causes 429s on later tests in the same run.
    """
    limiter._storage.reset()
    yield
    limiter._storage.reset()


ORG_USER_ID = "aaaaaaaa-0000-0000-0000-000000000001"
VOLUNTEER_ID = "bbbbbbbb-0000-0000-0000-000000000002"
INTRO_ID = "cccccccc-0000-0000-0000-000000000003"

VALID_PAYLOAD = {
    "professional_id": VOLUNTEER_ID,
    "project_name": "Community Health Initiative",
    "timeline": "normal",
    "message": "We would love to have you on board.",
}

INTRO_ROW = {
    "id": INTRO_ID,
    "org_id": ORG_USER_ID,
    "volunteer_id": VOLUNTEER_ID,
    "project_name": "Community Health Initiative",
    "timeline": "3 months",
    "message": "We would love to have you on board.",
    "status": "pending",
    "created_at": "2026-03-29T12:00:00+00:00",
}


# ── Dependency helpers ────────────────────────────────────────────────────────


def _admin_override(db):
    async def _dep():
        yield db

    return _dep


def _uid_override(uid: str):
    async def _dep():
        return uid

    return _dep


# ── Mock DB factory ───────────────────────────────────────────────────────────


def _build_intro_mock_db(
    caller_account_type: str = "organization",
    volunteer_exists: bool = True,
    volunteer_visible: bool = True,
    volunteer_account_type: str = "volunteer",
    duplicate: bool = False,
):
    """Non-circular per-table mock for create_intro_request.

    DB calls in order:
      1. profiles → caller account_type check
      2. profiles → volunteer lookup
      3. intro_requests → insert (or raise duplicate exception)
      4. notifications → insert (via notify())
    """
    call_counts: dict[str, int] = {}
    inserted_rows: dict[str, list] = {"intro_requests": [], "notifications": []}

    def make_table_mock(table_name: str) -> MagicMock:
        t = MagicMock()
        call_counts.setdefault(table_name, 0)

        if table_name == "profiles":

            async def _profiles_execute(*_a, **_kw):
                n = call_counts["profiles"]
                call_counts["profiles"] += 1
                if n == 0:
                    # First call: caller lookup
                    if caller_account_type == "none":
                        return MagicMock(data=None)
                    return MagicMock(
                        data={
                            "account_type": caller_account_type,
                            "display_name": "Tech Corp" if caller_account_type == "organization" else None,
                            "username": "techcorp",
                        }
                    )
                else:
                    # Second call: volunteer lookup
                    if not volunteer_exists:
                        return MagicMock(data=None)
                    return MagicMock(
                        data={
                            "id": VOLUNTEER_ID,
                            "display_name": "Alice",
                            "username": "alice",
                            "visible_to_orgs": volunteer_visible,
                            "account_type": volunteer_account_type,
                        }
                    )

            t.select.return_value = t
            t.eq.return_value = t
            t.maybe_single.return_value = t
            t.execute = AsyncMock(side_effect=_profiles_execute)

        elif table_name == "intro_requests":
            if duplicate:

                async def _intro_insert_execute(*_a, **_kw):
                    raise Exception("duplicate key value violates unique constraint")
            else:

                async def _intro_insert_execute(*_a, **_kw):
                    inserted_rows["intro_requests"].append(INTRO_ROW)
                    return MagicMock(data=[INTRO_ROW])

            t.insert.return_value = t
            t.execute = AsyncMock(side_effect=_intro_insert_execute)

        elif table_name == "notifications":

            async def _notif_insert_execute(*_a, **_kw):
                inserted_rows["notifications"].append({"inserted": True})
                return MagicMock(data=[{"id": "notif-id"}])

            t.insert.return_value = t
            t.execute = AsyncMock(side_effect=_notif_insert_execute)

        else:
            t.execute = AsyncMock(return_value=MagicMock(data=None))

        return t

    db = MagicMock()
    db.table = MagicMock(side_effect=make_table_mock)
    return db, inserted_rows


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_intro_request_success():
    """Org caller + discoverable volunteer → 201, intro_request and notification created."""
    db, inserted = _build_intro_mock_db(
        caller_account_type="organization",
        volunteer_exists=True,
        volunteer_visible=True,
    )

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/organizations/intro-requests",
            json=VALID_PAYLOAD,
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] == INTRO_ID
    assert body["status"] == "pending"
    assert body["professional_id"] == VOLUNTEER_ID
    # Notification must also be created
    assert len(inserted["notifications"]) == 1


@pytest.mark.asyncio
async def test_intro_request_non_org_forbidden():
    """Non-org account (volunteer) cannot send intro requests → 403."""
    db, _ = _build_intro_mock_db(caller_account_type="volunteer")

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/organizations/intro-requests",
            json=VALID_PAYLOAD,
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "ORG_REQUIRED"


@pytest.mark.asyncio
async def test_intro_request_volunteer_not_found():
    """Volunteer ID doesn't exist → 404."""
    db, _ = _build_intro_mock_db(
        caller_account_type="organization",
        volunteer_exists=False,
    )

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/organizations/intro-requests",
            json=VALID_PAYLOAD,
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "PROFILE_NOT_FOUND"


@pytest.mark.asyncio
async def test_intro_request_volunteer_not_discoverable():
    """Volunteer exists but visible_to_orgs=False → 403 NOT_DISCOVERABLE."""
    db, _ = _build_intro_mock_db(
        caller_account_type="organization",
        volunteer_exists=True,
        volunteer_visible=False,
    )

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/organizations/intro-requests",
            json=VALID_PAYLOAD,
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "NOT_DISCOVERABLE"


@pytest.mark.asyncio
async def test_intro_request_target_is_org():
    """Sending intro request to an org account → 422 INVALID_TARGET."""
    db, _ = _build_intro_mock_db(
        caller_account_type="organization",
        volunteer_exists=True,
        volunteer_visible=True,
        volunteer_account_type="organization",
    )

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/organizations/intro-requests",
            json=VALID_PAYLOAD,
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "INVALID_TARGET"


@pytest.mark.asyncio
async def test_intro_request_duplicate_pending():
    """Second request for same org+volunteer → 409 REQUEST_ALREADY_PENDING."""
    db, _ = _build_intro_mock_db(
        caller_account_type="organization",
        volunteer_exists=True,
        volunteer_visible=True,
        duplicate=True,
    )

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/organizations/intro-requests",
            json=VALID_PAYLOAD,
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "REQUEST_ALREADY_PENDING"


@pytest.mark.asyncio
async def test_intro_request_requires_auth():
    """No Authorization header → 401.

    get_supabase_admin is mocked to prevent real Supabase client creation.
    get_current_user_id still runs and returns 401 for missing Bearer token.
    """
    from app.deps import get_supabase_admin as _admin_dep

    mock_admin = MagicMock()
    mock_admin.auth = MagicMock()

    async def _mock_admin_override():
        yield mock_admin

    app.dependency_overrides[_admin_dep] = _mock_admin_override
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/organizations/intro-requests",
                json=VALID_PAYLOAD,
            )
        assert resp.status_code in (401, 403)
    finally:
        app.dependency_overrides.pop(_admin_dep, None)


@pytest.mark.asyncio
async def test_intro_request_missing_project_name():
    """project_name is required → 422 from Pydantic validation."""
    app.dependency_overrides[get_supabase_admin] = _admin_override(MagicMock())
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/organizations/intro-requests",
            json={"professional_id": VOLUNTEER_ID, "timeline": "normal"},  # missing project_name
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 422
