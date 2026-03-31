"""Tests for /api/auth endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.deps import get_supabase_admin, get_supabase_user, get_current_user_id, get_supabase_anon


def _make_admin_override(mock_db):
    async def _override():
        yield mock_db
    return _override


def _make_anon_override(mock_db):
    async def _override():
        yield mock_db
    return _override


def _make_user_override(mock_db):
    async def _override():
        yield mock_db
    return _override


def _make_user_id_override(user_id: str):
    async def _override():
        return user_id
    return _override


@pytest.fixture
def mock_admin_db():
    db = MagicMock()
    db.auth = MagicMock()
    db.table = MagicMock(return_value=db)
    db.select = MagicMock(return_value=db)
    db.eq = MagicMock(return_value=db)
    db.single = MagicMock(return_value=db)
    db.maybe_single = MagicMock(return_value=db)
    db.execute = AsyncMock()
    return db


@pytest.fixture
def mock_anon_db():
    db = MagicMock()
    db.auth = MagicMock()
    return db


@pytest.fixture
async def client(mock_admin_db, mock_anon_db):
    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_admin_db)
    app.dependency_overrides[get_supabase_anon] = _make_anon_override(mock_anon_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac, mock_anon_db
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_register_success(client):
    ac, db = client

    mock_session = MagicMock()
    mock_session.access_token = "tok_abc"
    mock_session.expires_in = 3600

    mock_user = MagicMock()
    mock_user.id = "uuid-1234"

    auth_resp = MagicMock()
    auth_resp.session = mock_session
    auth_resp.user = mock_user

    db.auth.sign_up = AsyncMock(return_value=auth_resp)

    resp = await ac.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "Secret123",
        "username": "testuser",
    })

    assert resp.status_code == 201
    body = resp.json()
    assert body["access_token"] == "tok_abc"
    assert body["token_type"] == "bearer"
    assert body["user_id"] == "uuid-1234"


@pytest.mark.asyncio
async def test_register_email_confirmation_required(client):
    ac, db = client

    auth_resp = MagicMock()
    auth_resp.session = None
    auth_resp.user = MagicMock()
    db.auth.sign_up = AsyncMock(return_value=auth_resp)

    resp = await ac.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "Secret123",
        "username": "testuser",
    })

    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "EMAIL_CONFIRMATION_REQUIRED"


@pytest.mark.asyncio
async def test_register_failure(client):
    ac, db = client
    db.auth.sign_up = AsyncMock(side_effect=Exception("Email already registered"))

    resp = await ac.post("/api/auth/register", json={
        "email": "dup@example.com",
        "password": "Secret123",
        "username": "dupuser",
    })

    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "REGISTRATION_FAILED"


@pytest.mark.asyncio
async def test_login_success(client):
    ac, db = client

    mock_session = MagicMock()
    mock_session.access_token = "tok_xyz"
    mock_session.expires_in = 3600

    mock_user = MagicMock()
    mock_user.id = "uuid-5678"

    auth_resp = MagicMock()
    auth_resp.session = mock_session
    auth_resp.user = mock_user

    db.auth.sign_in_with_password = AsyncMock(return_value=auth_resp)

    resp = await ac.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "Secret123",
    })

    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"] == "tok_xyz"
    assert body["user_id"] == "uuid-5678"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    ac, db = client
    db.auth.sign_in_with_password = AsyncMock(side_effect=Exception("Invalid login"))

    resp = await ac.post("/api/auth/login", json={
        "email": "wrong@example.com",
        "password": "wrongpass",
    })

    assert resp.status_code == 401
    assert resp.json()["detail"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_get_me_with_profile(mock_admin_db):
    user_id = "uuid-me"
    mock_admin_db.execute = AsyncMock(return_value=MagicMock(data={
        "id": user_id,
        "username": "meuser",
        "display_name": "Me User",
        "avatar_url": None,
    }))

    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_admin_db)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(user_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer fake-token"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["user_id"] == user_id
    assert body["profile"]["username"] == "meuser"


@pytest.mark.asyncio
async def test_get_me_no_profile(mock_admin_db):
    user_id = "uuid-noprofile"
    mock_admin_db.execute = AsyncMock(return_value=MagicMock(data=None))

    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_admin_db)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(user_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer fake-token"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["user_id"] == user_id
    assert body["profile"] is None


# ── BUG-016: Logout / token revocation ───────────────────────────────────────

@pytest.mark.asyncio
async def test_logout_revokes_token(mock_admin_db):
    """Logout must call admin.auth.admin.sign_out to revoke the token server-side."""
    user_id = "uuid-logout"
    mock_admin_db.auth.admin = MagicMock()
    mock_admin_db.auth.admin.sign_out = AsyncMock(return_value=None)

    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_admin_db)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(user_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/auth/logout",
            headers={"Authorization": "Bearer test-token-to-revoke"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["message"] == "Logged out"
    # Critical: sign_out must have been called with the bearer token
    mock_admin_db.auth.admin.sign_out.assert_called_once_with("test-token-to-revoke")


@pytest.mark.asyncio
async def test_logout_succeeds_even_if_revocation_fails(mock_admin_db):
    """Token revocation failure is non-fatal — logout still returns 200."""
    user_id = "uuid-logout-fail"
    mock_admin_db.auth.admin = MagicMock()
    mock_admin_db.auth.admin.sign_out = AsyncMock(side_effect=Exception("Supabase unreachable"))

    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_admin_db)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(user_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/auth/logout",
            headers={"Authorization": "Bearer some-token"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["message"] == "Logged out"


# ── Invite gate (RISK-014) ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_signup_status_open():
    """GET /auth/signup-status returns open_signup from settings."""
    from unittest.mock import patch

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        with patch("app.routers.auth.settings") as mock_settings:
            mock_settings.open_signup = True
            resp = await ac.get("/api/auth/signup-status")

    assert resp.status_code == 200
    assert resp.json()["open_signup"] is True


@pytest.mark.asyncio
async def test_signup_status_closed():
    """GET /auth/signup-status returns open_signup=False when gate is active."""
    from unittest.mock import patch

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        with patch("app.routers.auth.settings") as mock_settings:
            mock_settings.open_signup = False
            resp = await ac.get("/api/auth/signup-status")

    assert resp.status_code == 200
    assert resp.json()["open_signup"] is False


@pytest.mark.asyncio
async def test_validate_invite_correct_code():
    """POST /auth/validate-invite returns valid=True for matching code."""
    from unittest.mock import patch

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        with patch("app.routers.auth.settings") as mock_settings:
            mock_settings.beta_invite_code = "VOLAURA2026"
            resp = await ac.post("/api/auth/validate-invite", json={"invite_code": "VOLAURA2026"})

    assert resp.status_code == 200
    assert resp.json()["valid"] is True


@pytest.mark.asyncio
async def test_validate_invite_case_insensitive():
    """Invite code comparison is case-insensitive."""
    from unittest.mock import patch

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        with patch("app.routers.auth.settings") as mock_settings:
            mock_settings.beta_invite_code = "VOLAURA2026"
            resp = await ac.post("/api/auth/validate-invite", json={"invite_code": "volaura2026"})

    assert resp.status_code == 200
    assert resp.json()["valid"] is True


@pytest.mark.asyncio
async def test_validate_invite_wrong_code():
    """POST /auth/validate-invite returns valid=False for wrong code."""
    from unittest.mock import patch

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        with patch("app.routers.auth.settings") as mock_settings:
            mock_settings.beta_invite_code = "VOLAURA2026"
            resp = await ac.post("/api/auth/validate-invite", json={"invite_code": "WRONG"})

    assert resp.status_code == 200
    assert resp.json()["valid"] is False


@pytest.mark.asyncio
async def test_validate_invite_no_code_configured():
    """When BETA_INVITE_CODE is empty, always returns valid=False (gate armed, no valid code)."""
    from unittest.mock import patch

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        with patch("app.routers.auth.settings") as mock_settings:
            mock_settings.beta_invite_code = ""
            resp = await ac.post("/api/auth/validate-invite", json={"invite_code": "anything"})

    assert resp.status_code == 200
    assert resp.json()["valid"] is False
