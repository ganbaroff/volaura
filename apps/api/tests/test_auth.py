"""Tests for /api/auth endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.deps import get_supabase_admin, get_supabase_user, get_current_user_id


def _make_admin_override(mock_db):
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
    db.execute = AsyncMock()
    return db


@pytest.fixture
async def client(mock_admin_db):
    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_admin_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac, mock_admin_db
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
        "password": "secret123",
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
        "password": "secret123",
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
        "password": "secret123",
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
        "password": "secret123",
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
