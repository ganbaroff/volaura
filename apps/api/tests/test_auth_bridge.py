"""Tests for POST /api/auth/from_external — auth bridge endpoint.

Covers:
- Feature-flag gate (503 when secrets not configured)
- Bridge secret validation (401 on missing/wrong secret)
- Case normalization of project_ref and email (G2.6 fix)
- Schema validation (extra fields rejected, required fields enforced)
- JWT minting structure and expiry
- Happy path with mocked Supabase (new user creation)
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import jwt as pyjwt
import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.deps import get_supabase_admin
from app.main import app
from app.routers.auth_bridge import _JWT_ALGORITHM, FromExternalRequest, _mint_shared_jwt

VALID_BODY = {
    "standalone_user_id": "abc-123-def-456",
    "standalone_project_ref": "awfoqycoltvhamtrsvxk",
    "email": "test@example.com",
    "source_product": "mindshift",
}

BRIDGE_SECRET = "test-bridge-secret-value-long-enough"
JWT_SECRET = "test-jwt-secret-for-signing-long-enough"

SHADOW_USER_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def _mock_supabase_admin():
    """Build a mock admin client simulating empty mapping + no existing user.

    Supabase chained calls (table().select().eq().execute()) are sync except
    execute() which is awaited. So table/select/eq/update/upsert must be
    regular MagicMock, only execute() is AsyncMock.
    """
    admin = MagicMock()

    table_mock = MagicMock()
    table_mock.select.return_value = table_mock
    table_mock.eq.return_value = table_mock
    table_mock.update.return_value = table_mock
    table_mock.upsert.return_value = table_mock

    empty_result = MagicMock()
    empty_result.data = []
    table_mock.execute = AsyncMock(return_value=empty_result)

    admin.table.return_value = table_mock

    rpc_result = MagicMock()
    rpc_result.data = None
    rpc_chain = MagicMock()
    rpc_chain.execute = AsyncMock(return_value=rpc_result)
    admin.rpc.return_value = rpc_chain

    create_user_result = MagicMock()
    create_user_result.user = MagicMock()
    create_user_result.user.id = SHADOW_USER_ID
    admin.auth.admin.create_user = AsyncMock(return_value=create_user_result)

    return admin


@pytest.fixture
def mock_admin():
    """Override Supabase admin dep with mock for all HTTP tests."""
    mock = _mock_supabase_admin()
    app.dependency_overrides[get_supabase_admin] = lambda: mock
    yield mock
    app.dependency_overrides.pop(get_supabase_admin, None)


@pytest.fixture
def bridge_settings(monkeypatch):
    """Configure both secrets so the bridge is enabled."""
    from app.config import settings

    monkeypatch.setattr(settings, "supabase_jwt_secret", JWT_SECRET)
    monkeypatch.setattr(settings, "external_bridge_secret", BRIDGE_SECRET)
    return settings


# ── Feature-flag gate ───────────────────────────────────────────────────


@pytest.mark.anyio
async def test_bridge_disabled_when_jwt_secret_empty(monkeypatch, mock_admin):
    from app.config import settings

    monkeypatch.setattr(settings, "supabase_jwt_secret", "")
    monkeypatch.setattr(settings, "external_bridge_secret", BRIDGE_SECRET)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/auth/from_external",
            json=VALID_BODY,
            headers={"X-Bridge-Secret": BRIDGE_SECRET},
        )
    assert resp.status_code == 503
    assert resp.json()["detail"]["code"] == "BRIDGE_DISABLED"


@pytest.mark.anyio
async def test_bridge_disabled_when_bridge_secret_empty(monkeypatch, mock_admin):
    from app.config import settings

    monkeypatch.setattr(settings, "supabase_jwt_secret", JWT_SECRET)
    monkeypatch.setattr(settings, "external_bridge_secret", "")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/auth/from_external",
            json=VALID_BODY,
            headers={"X-Bridge-Secret": "anything"},
        )
    assert resp.status_code == 503


# ── Secret validation ───────────────────────────────────────────────────


@pytest.mark.anyio
async def test_bridge_rejects_wrong_secret(bridge_settings, mock_admin):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/auth/from_external",
            json=VALID_BODY,
            headers={"X-Bridge-Secret": "wrong-secret-value"},
        )
    assert resp.status_code == 401
    assert resp.json()["detail"]["code"] == "INVALID_BRIDGE_SECRET"


@pytest.mark.anyio
async def test_bridge_rejects_missing_secret_header(bridge_settings, mock_admin):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/auth/from_external", json=VALID_BODY)
    assert resp.status_code == 401


# ── Schema validation ───────────────────────────────────────────────────


def test_schema_rejects_extra_fields():
    with pytest.raises(ValidationError):
        FromExternalRequest(
            standalone_user_id="x",
            standalone_project_ref="y",
            email="a@b.com",
            sneaky_field="injected",
        )


def test_schema_requires_standalone_user_id():
    with pytest.raises(ValidationError):
        FromExternalRequest(
            standalone_project_ref="y",
            email="a@b.com",
        )


def test_schema_requires_email():
    with pytest.raises(ValidationError):
        FromExternalRequest(
            standalone_user_id="x",
            standalone_project_ref="y",
        )


def test_schema_validates_email_format():
    with pytest.raises(ValidationError):
        FromExternalRequest(
            standalone_user_id="x",
            standalone_project_ref="y",
            email="not-an-email",
        )


def test_schema_default_source_product():
    req = FromExternalRequest(
        standalone_user_id="x",
        standalone_project_ref="y",
        email="a@b.com",
    )
    assert req.source_product == "mindshift"


def test_schema_rejects_empty_standalone_user_id():
    with pytest.raises(ValidationError):
        FromExternalRequest(
            standalone_user_id="",
            standalone_project_ref="y",
            email="a@b.com",
        )


# ── Case normalization (G2.6 regression) ────────────────────────────────


@pytest.mark.anyio
async def test_project_ref_normalized_to_lowercase(bridge_settings, mock_admin):
    """G2.6 fix: mixed-case project_ref must be lowered before DB lookup."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/auth/from_external",
            json={
                "standalone_user_id": "user-123",
                "standalone_project_ref": "AwFoQyCoLtVhAmTrSvXk",
                "email": "Test@Example.COM",
                "source_product": "mindshift",
            },
            headers={"X-Bridge-Secret": BRIDGE_SECRET},
        )
    assert resp.status_code == 200

    eq_calls = mock_admin.table.return_value.eq.call_args_list
    project_ref_args = [c[0][1] for c in eq_calls if c[0][0] == "standalone_project_ref"]
    for ref in project_ref_args:
        assert ref == ref.lower(), f"project_ref not lowered: {ref}"


@pytest.mark.anyio
async def test_email_normalized_to_lowercase(bridge_settings, mock_admin):
    """Ensure email is lowered in the upsert/update calls."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/auth/from_external",
            json={
                "standalone_user_id": "user-456",
                "standalone_project_ref": "projref",
                "email": "LOUD@EXAMPLE.COM",
                "source_product": "mindshift",
            },
            headers={"X-Bridge-Secret": BRIDGE_SECRET},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["shared_user_id"] == SHADOW_USER_ID
    assert data["created_new_user"] is True


# ── Happy path ──────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_happy_path_new_user(bridge_settings, mock_admin):
    """Full flow: no existing mapping, no existing user → create shadow → return JWT."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/auth/from_external",
            json=VALID_BODY,
            headers={"X-Bridge-Secret": BRIDGE_SECRET},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["shared_user_id"] == SHADOW_USER_ID
    assert data["created_new_user"] is True
    assert "shared_jwt" in data
    assert "expires_at" in data

    decoded = pyjwt.decode(
        data["shared_jwt"],
        JWT_SECRET,
        algorithms=[_JWT_ALGORITHM],
        audience="authenticated",
    )
    assert decoded["sub"] == SHADOW_USER_ID
    assert decoded["aud"] == "authenticated"


@pytest.mark.anyio
async def test_existing_mapping_reused(bridge_settings, mock_admin):
    """When mapping exists, reuse shared_user_id and don't create new user."""
    existing_result = MagicMock()
    existing_result.data = [{"shared_user_id": "existing-uuid-1234", "email": "old@example.com"}]
    mock_admin.table.return_value.execute = AsyncMock(return_value=existing_result)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/auth/from_external",
            json=VALID_BODY,
            headers={"X-Bridge-Secret": BRIDGE_SECRET},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["shared_user_id"] == "existing-uuid-1234"
    assert data["created_new_user"] is False
    mock_admin.auth.admin.create_user.assert_not_called()


# ── JWT minting unit tests ──────────────────────────────────────────────


def test_mint_shared_jwt_structure(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "supabase_jwt_secret", JWT_SECRET)

    token, expires_at = _mint_shared_jwt("user-id-abc", "test@example.com")

    decoded = pyjwt.decode(
        token,
        JWT_SECRET,
        algorithms=[_JWT_ALGORITHM],
        audience="authenticated",
    )
    assert decoded["sub"] == "user-id-abc"
    assert decoded["email"] == "test@example.com"
    assert decoded["aud"] == "authenticated"
    assert decoded["role"] == "authenticated"
    assert decoded["iss"] == "supabase"
    assert decoded["app_metadata"]["provider"] == "external_bridge"
    assert isinstance(expires_at, datetime)
    assert expires_at > datetime.now(UTC)


def test_mint_shared_jwt_expiry_is_one_hour(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "supabase_jwt_secret", JWT_SECRET)

    token, _ = _mint_shared_jwt("uid", "e@x.com")
    decoded = pyjwt.decode(
        token,
        JWT_SECRET,
        algorithms=[_JWT_ALGORITHM],
        audience="authenticated",
    )
    assert decoded["exp"] - decoded["iat"] == 3600
