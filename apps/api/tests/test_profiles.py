"""Tests for /api/profiles endpoints."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.deps import get_supabase_admin, get_supabase_user, get_current_user_id

USER_ID = "uuid-profile-test"
NOW = datetime.utcnow().isoformat()

PROFILE_ROW = {
    "id": USER_ID,
    "username": "voluser",
    "display_name": "Vol User",
    "bio": "I help people",
    "location": "Baku",
    "languages": ["az", "en"],
    "social_links": {},
    "is_public": True,
    "avatar_url": None,
    "badge_issued_at": None,
    "badge_open_badges_url": None,
    "created_at": NOW,
    "updated_at": NOW,
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
    db.insert = MagicMock(return_value=db)
    db.update = MagicMock(return_value=db)
    db.eq = MagicMock(return_value=db)
    db.single = MagicMock(return_value=db)
    db.maybe_single = MagicMock(return_value=db)
    db.execute = AsyncMock()
    return db


@pytest.mark.asyncio
async def test_get_my_profile_found():
    db = _make_mock_db()
    db.execute = AsyncMock(return_value=MagicMock(data=PROFILE_ROW))

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/profiles/me", headers={"Authorization": "Bearer fake"})

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == "voluser"
    assert body["id"] == USER_ID


@pytest.mark.asyncio
async def test_get_my_profile_not_found():
    db = _make_mock_db()
    db.execute = AsyncMock(return_value=MagicMock(data=None))

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/profiles/me", headers={"Authorization": "Bearer fake"})

    app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "PROFILE_NOT_FOUND"


@pytest.mark.asyncio
async def test_create_my_profile_success():
    db = _make_mock_db()
    admin_db = _make_mock_db()
    # First call: username check returns empty (not taken)
    # Second call: insert returns the new row
    db.execute = AsyncMock(side_effect=[
        MagicMock(data=[]),          # username check
        MagicMock(data=[PROFILE_ROW]),  # insert result
    ])
    # Admin: used for upsert_volunteer_embedding (fire-and-forget, caught in try/except)
    admin_db.execute = AsyncMock(return_value=MagicMock(data=[]))

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_supabase_admin] = _admin_override(admin_db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/profiles/me",
            json={"username": "voluser"},
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 201
    assert resp.json()["username"] == "voluser"


@pytest.mark.asyncio
async def test_create_my_profile_username_taken():
    db = _make_mock_db()
    admin_db = _make_mock_db()
    db.execute = AsyncMock(return_value=MagicMock(data=[{"id": "other-id"}]))
    admin_db.execute = AsyncMock(return_value=MagicMock(data=[]))

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_supabase_admin] = _admin_override(admin_db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/profiles/me",
            json={"username": "taken"},
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "USERNAME_TAKEN"


@pytest.mark.asyncio
async def test_create_my_profile_invalid_username():
    db = _make_mock_db()
    admin_db = _make_mock_db()
    admin_db.execute = AsyncMock(return_value=MagicMock(data=[]))

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_supabase_admin] = _admin_override(admin_db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/profiles/me",
            json={"username": "ab"},  # too short
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 422  # Pydantic validation


@pytest.mark.asyncio
async def test_update_my_profile_success():
    updated_row = {**PROFILE_ROW, "bio": "Updated bio"}
    db = _make_mock_db()
    db.execute = AsyncMock(return_value=MagicMock(data=[updated_row]))
    admin_db = _make_mock_db()  # embedding update is best-effort (try/except)

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_supabase_admin] = _admin_override(admin_db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.put(
            "/api/profiles/me",
            json={"bio": "Updated bio"},
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["bio"] == "Updated bio"


@pytest.mark.asyncio
async def test_update_my_profile_no_fields():
    db = _make_mock_db()
    admin_db = _make_mock_db()

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_supabase_admin] = _admin_override(admin_db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.put(
            "/api/profiles/me",
            json={},
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "NO_FIELDS"


@pytest.mark.asyncio
async def test_get_public_profile_found():
    public_row = {
        "id": USER_ID,
        "username": "voluser",
        "display_name": "Vol User",
        "avatar_url": None,
        "bio": "I help people",
        "location": "Baku",
        "languages": ["az", "en"],
        "badge_issued_at": None,
    }
    db = _make_mock_db()
    db.execute = AsyncMock(return_value=MagicMock(data=public_row))

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/profiles/voluser")

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["username"] == "voluser"


@pytest.mark.asyncio
async def test_get_public_profile_not_found():
    db = _make_mock_db()
    db.execute = AsyncMock(return_value=MagicMock(data=None))

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/profiles/ghost")

    app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "PROFILE_NOT_FOUND"


# ── GROWTH-2: Invite attribution ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_profile_with_invite_attribution():
    """invited_by_org_id stored + matching invite marked accepted."""
    user_db = _make_mock_db()
    admin_db = _make_mock_db()
    ORG_ID = "org-uuid-123"

    # user db: username check empty, insert succeeds
    user_db.execute = AsyncMock(side_effect=[
        MagicMock(data=[]),             # username check
        MagicMock(data=[PROFILE_ROW]),  # insert
    ])

    # admin db: get_user_by_id returns email, then invite update
    mock_user_obj = MagicMock()
    mock_user_obj.user = MagicMock()
    mock_user_obj.user.email = "invitee@example.com"
    admin_db.auth = MagicMock()
    admin_db.auth.admin = MagicMock()
    admin_db.auth.admin.get_user_by_id = AsyncMock(return_value=mock_user_obj)
    admin_db.execute = AsyncMock(return_value=MagicMock(data=None))

    app.dependency_overrides[get_supabase_user] = _user_override(user_db)
    app.dependency_overrides[get_supabase_admin] = _admin_override(admin_db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/profiles/me",
            json={"username": "voluser", "invited_by_org_id": ORG_ID},
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 201
    assert resp.json()["username"] == "voluser"
    # get_user_by_id was called to fetch email for invite update
    admin_db.auth.admin.get_user_by_id.assert_called_once_with(USER_ID)


@pytest.mark.asyncio
async def test_create_profile_without_invite_attribution():
    """Normal profile creation without invite_code: get_user_by_id NOT called."""
    user_db = _make_mock_db()
    admin_db = _make_mock_db()
    admin_db.auth = MagicMock()
    admin_db.auth.admin = MagicMock()
    admin_db.auth.admin.get_user_by_id = AsyncMock()

    user_db.execute = AsyncMock(side_effect=[
        MagicMock(data=[]),
        MagicMock(data=[PROFILE_ROW]),
    ])
    admin_db.execute = AsyncMock(return_value=MagicMock(data=None))

    app.dependency_overrides[get_supabase_user] = _user_override(user_db)
    app.dependency_overrides[get_supabase_admin] = _admin_override(admin_db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/profiles/me",
            json={"username": "voluser"},
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 201
    admin_db.auth.admin.get_user_by_id.assert_not_called()
