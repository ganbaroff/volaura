"""Tests for /api/auth endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin, get_supabase_anon
from app.main import app


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

    resp = await ac.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "Secret123",
            "username": "testuser",
        },
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["access_token"] == "tok_abc"
    assert body["token_type"] == "bearer"
    assert body["user_id"] == "uuid-1234"


@pytest.mark.asyncio
async def test_register_forwards_gdpr_consent_to_user_metadata(client):
    """Consent fields (age_confirmed, terms_version, terms_accepted_at) must land in
    user_metadata — the onboarding POST /profiles/me handler reads them from there
    into the profiles row. See docs/research/gdpr-article-22/summary.md."""
    ac, db = client

    mock_session = MagicMock()
    mock_session.access_token = "tok_consent"
    mock_session.expires_in = 3600
    mock_user = MagicMock()
    mock_user.id = "uuid-consent"
    auth_resp = MagicMock()
    auth_resp.session = mock_session
    auth_resp.user = mock_user

    db.auth.sign_up = AsyncMock(return_value=auth_resp)

    resp = await ac.post(
        "/api/auth/register",
        json={
            "email": "consent@example.com",
            "password": "Secret123",
            "username": "consentuser",
            "age_confirmed": True,
            "terms_version": "1.0",
            "terms_accepted_at": "2026-04-15T21:00:00+00:00",
        },
    )

    assert resp.status_code == 201
    # Inspect the payload that was sent to Supabase sign_up
    call_args = db.auth.sign_up.await_args
    meta = call_args[0][0]["options"]["data"]
    assert meta["age_confirmed"] is True
    assert meta["terms_version"] == "1.0"
    assert meta["terms_accepted_at"] == "2026-04-15T21:00:00+00:00"


@pytest.mark.asyncio
async def test_register_consent_defaults_when_client_omits(client):
    """If a client forgets to send consent fields, backend fills sane defaults
    (age_confirmed=False, terms_version='1.0', terms_accepted_at=now()) so
    user_metadata is never missing the keys downstream code reads."""
    ac, db = client

    mock_session = MagicMock()
    mock_session.access_token = "tok_default"
    mock_session.expires_in = 3600
    mock_user = MagicMock()
    mock_user.id = "uuid-default"
    auth_resp = MagicMock()
    auth_resp.session = mock_session
    auth_resp.user = mock_user

    db.auth.sign_up = AsyncMock(return_value=auth_resp)

    resp = await ac.post(
        "/api/auth/register",
        json={
            "email": "default@example.com",
            "password": "Secret123",
            "username": "defaultuser",
        },
    )

    assert resp.status_code == 201
    meta = db.auth.sign_up.await_args[0][0]["options"]["data"]
    assert "age_confirmed" in meta and meta["age_confirmed"] is False
    assert meta["terms_version"] == "1.0"
    assert meta["terms_accepted_at"]  # non-empty ISO timestamp


@pytest.mark.asyncio
async def test_register_email_confirmation_required(client):
    ac, db = client

    auth_resp = MagicMock()
    auth_resp.session = None
    auth_resp.user = MagicMock()
    db.auth.sign_up = AsyncMock(return_value=auth_resp)

    resp = await ac.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "Secret123",
            "username": "testuser",
        },
    )

    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "EMAIL_CONFIRMATION_REQUIRED"


@pytest.mark.asyncio
async def test_register_failure(client):
    ac, db = client
    db.auth.sign_up = AsyncMock(side_effect=Exception("Email already registered"))

    resp = await ac.post(
        "/api/auth/register",
        json={
            "email": "dup@example.com",
            "password": "Secret123",
            "username": "dupuser",
        },
    )

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

    resp = await ac.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "Secret123",
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"] == "tok_xyz"
    assert body["user_id"] == "uuid-5678"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    ac, db = client
    db.auth.sign_in_with_password = AsyncMock(side_effect=Exception("Invalid login"))

    resp = await ac.post(
        "/api/auth/login",
        json={
            "email": "wrong@example.com",
            "password": "wrongpass",
        },
    )

    assert resp.status_code == 401
    assert resp.json()["detail"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_get_me_with_profile(mock_admin_db):
    user_id = "uuid-me"
    mock_admin_db.execute = AsyncMock(
        return_value=MagicMock(
            data={
                "id": user_id,
                "username": "meuser",
                "display_name": "Me User",
                "avatar_url": None,
            }
        )
    )

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

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        with patch("app.routers.auth.settings") as mock_settings:
            mock_settings.beta_invite_code = ""
            resp = await ac.post("/api/auth/validate-invite", json={"invite_code": "anything"})

    assert resp.status_code == 200
    assert resp.json()["valid"] is False


# ── GDPR consent_events logging on register ──────────────────────────────────


@pytest.fixture
async def consent_client(mock_admin_db, mock_anon_db):
    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_admin_db)
    app.dependency_overrides[get_supabase_anon] = _make_anon_override(mock_anon_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac, mock_anon_db, mock_admin_db
    app.dependency_overrides.clear()


def _setup_successful_signup(mock_anon_db):
    mock_session = MagicMock()
    mock_session.access_token = "tok_consent_test"
    mock_session.expires_in = 3600
    mock_user = MagicMock()
    mock_user.id = "uuid-consent-test"
    auth_resp = MagicMock()
    auth_resp.session = mock_session
    auth_resp.user = mock_user
    mock_anon_db.auth.sign_up = AsyncMock(return_value=auth_resp)
    return auth_resp


def _setup_policy_chain(mock_admin_db, policy_id="policy-uuid-1"):
    chain = MagicMock()
    chain.select = MagicMock(return_value=chain)
    chain.eq = MagicMock(return_value=chain)
    chain.is_ = MagicMock(return_value=chain)
    chain.order = MagicMock(return_value=chain)
    chain.limit = MagicMock(return_value=chain)
    chain.maybe_single = MagicMock(return_value=chain)
    result = MagicMock()
    result.data = {"id": policy_id} if policy_id else None
    chain.execute = AsyncMock(return_value=result)

    insert_chain = MagicMock()
    insert_chain.insert = MagicMock(return_value=insert_chain)
    insert_chain.execute = AsyncMock()

    def table_router(name):
        if name == "policy_versions":
            return chain
        if name == "consent_events":
            return insert_chain
        return MagicMock()

    mock_admin_db.table = MagicMock(side_effect=table_router)
    return chain, insert_chain


REGISTER_PAYLOAD = {
    "email": "consent-test@example.com",
    "password": "Secret123",
    "username": "consenttest",
    "age_confirmed": True,
    "terms_version": "1.0",
}


@pytest.mark.asyncio
async def test_register_logs_consent_event_when_policy_exists(consent_client):
    ac, anon_db, admin_db = consent_client
    _setup_successful_signup(anon_db)
    _chain, insert_chain = _setup_policy_chain(admin_db, policy_id="pol-123")

    resp = await ac.post("/api/auth/register", json=REGISTER_PAYLOAD)

    assert resp.status_code == 201
    insert_chain.insert.assert_called_once()
    row = insert_chain.insert.call_args[0][0]
    assert row["user_id"] == "uuid-consent-test"
    assert row["source_product"] == "volaura"
    assert row["event_type"] == "consent_given"
    assert row["policy_version_id"] == "pol-123"
    assert row["consent_scope"]["age_confirmed"] is True
    assert row["consent_scope"]["terms_version"] == "1.0"


@pytest.mark.asyncio
async def test_register_skips_consent_when_no_policy(consent_client):
    ac, anon_db, admin_db = consent_client
    _setup_successful_signup(anon_db)
    _chain, insert_chain = _setup_policy_chain(admin_db, policy_id=None)

    resp = await ac.post("/api/auth/register", json=REGISTER_PAYLOAD)

    assert resp.status_code == 201
    insert_chain.insert.assert_not_called()


@pytest.mark.asyncio
async def test_register_succeeds_even_if_consent_logging_fails(consent_client):
    ac, anon_db, admin_db = consent_client
    _setup_successful_signup(anon_db)

    chain = MagicMock()
    chain.select = MagicMock(return_value=chain)
    chain.eq = MagicMock(return_value=chain)
    chain.is_ = MagicMock(return_value=chain)
    chain.order = MagicMock(return_value=chain)
    chain.limit = MagicMock(return_value=chain)
    chain.maybe_single = MagicMock(return_value=chain)
    chain.execute = AsyncMock(side_effect=Exception("DB connection error"))
    admin_db.table = MagicMock(return_value=chain)

    resp = await ac.post("/api/auth/register", json=REGISTER_PAYLOAD)

    assert resp.status_code == 201
    assert resp.json()["user_id"] == "uuid-consent-test"
