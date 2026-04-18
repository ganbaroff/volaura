"""Tests for app.deps — FastAPI dependency injection (auth, Supabase clients).

Covers: get_supabase_user, get_current_user_id, get_optional_user_id,
require_platform_admin, _get_or_create_admin_client singleton pattern.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app import deps

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_request(auth_header: str | None = None) -> MagicMock:
    r = MagicMock()
    headers = {}
    if auth_header is not None:
        headers["authorization"] = auth_header
    r.headers = headers
    return r


async def _exhaust(gen):
    """Drive an async-generator and return the yielded value."""
    val = await gen.__anext__()
    try:
        await gen.__anext__()
    except StopAsyncIteration:
        pass
    return val


# ---------------------------------------------------------------------------
# get_supabase_user
# ---------------------------------------------------------------------------


class TestGetSupabaseUser:
    @pytest.mark.asyncio
    async def test_missing_auth_header_raises_401(self):
        req = _make_request()
        with pytest.raises(HTTPException) as exc:
            await _exhaust(get_supabase_user(req))
        assert exc.value.status_code == 401
        assert exc.value.detail["code"] == "MISSING_TOKEN"

    @pytest.mark.asyncio
    async def test_non_bearer_raises_401(self):
        req = _make_request("Basic abc123")
        with pytest.raises(HTTPException) as exc:
            await _exhaust(get_supabase_user(req))
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_empty_bearer_raises_401(self):
        req = _make_request("Bearer ")
        with pytest.raises(HTTPException) as exc:
            await _exhaust(get_supabase_user(req))
        assert exc.value.status_code == 401
        assert exc.value.detail["code"] == "EMPTY_TOKEN"

    @pytest.mark.asyncio
    @patch("app.deps.acreate_client", new_callable=AsyncMock)
    async def test_valid_bearer_creates_client(self, mock_create):
        mock_client = AsyncMock()
        mock_client.postgrest = MagicMock()
        mock_create.return_value = mock_client
        req = _make_request("Bearer valid-jwt-token")

        client = await _exhaust(get_supabase_user(req))

        assert client is mock_client
        mock_client.postgrest.auth.assert_called_once_with("valid-jwt-token")

    @pytest.mark.asyncio
    @patch("app.deps.acreate_client", new_callable=AsyncMock, side_effect=RuntimeError("conn"))
    async def test_client_creation_failure_raises_500(self, _mock):
        req = _make_request("Bearer valid")
        with pytest.raises(HTTPException) as exc:
            await _exhaust(get_supabase_user(req))
        assert exc.value.status_code == 500
        assert exc.value.detail["code"] == "DB_CLIENT_ERROR"


# ---------------------------------------------------------------------------
# get_current_user_id
# ---------------------------------------------------------------------------


def _make_admin_with_user(user_id: str = "test-uuid"):
    admin = AsyncMock()
    admin.auth.get_user.return_value = SimpleNamespace(user=SimpleNamespace(id=user_id))
    return admin


def _make_admin_no_user():
    admin = AsyncMock()
    admin.auth.get_user.return_value = SimpleNamespace(user=None)
    return admin


def _make_admin_raises(exc):
    admin = AsyncMock()
    admin.auth.get_user.side_effect = exc
    return admin


# Alias the actual function under test
get_supabase_user = deps.get_supabase_user
get_current_user_id = deps.get_current_user_id
get_optional_user_id = deps.get_optional_user_id
require_platform_admin = deps.require_platform_admin


class TestGetCurrentUserId:
    @pytest.mark.asyncio
    async def test_missing_header_raises_401(self):
        req = _make_request()
        with pytest.raises(HTTPException) as exc:
            await get_current_user_id(req, _make_admin_with_user())
        assert exc.value.status_code == 401
        assert exc.value.detail["code"] == "MISSING_TOKEN"

    @pytest.mark.asyncio
    async def test_valid_token_returns_user_id(self):
        req = _make_request("Bearer good-token")
        uid = await get_current_user_id(req, _make_admin_with_user("abc-123"))
        assert uid == "abc-123"

    @pytest.mark.asyncio
    async def test_null_user_raises_401(self):
        req = _make_request("Bearer bad-token")
        with pytest.raises(HTTPException) as exc:
            await get_current_user_id(req, _make_admin_no_user())
        assert exc.value.status_code == 401
        assert exc.value.detail["code"] == "INVALID_TOKEN"

    @pytest.mark.asyncio
    async def test_none_response_raises_401(self):
        admin = AsyncMock()
        admin.auth.get_user.return_value = None
        req = _make_request("Bearer token")
        with pytest.raises(HTTPException) as exc:
            await get_current_user_id(req, admin)
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_exception_raises_401(self):
        admin = _make_admin_raises(RuntimeError("network"))
        req = _make_request("Bearer token")
        with pytest.raises(HTTPException) as exc:
            await get_current_user_id(req, admin)
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_http_exception_propagated(self):
        admin = _make_admin_raises(HTTPException(status_code=403, detail="custom"))
        req = _make_request("Bearer token")
        with pytest.raises(HTTPException) as exc:
            await get_current_user_id(req, admin)
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_bearer_whitespace_stripped(self):
        req = _make_request("Bearer   spaced-token   ")
        admin = _make_admin_with_user("uid")
        uid = await get_current_user_id(req, admin)
        assert uid == "uid"
        admin.auth.get_user.assert_called_once_with("  spaced-token   ")


# ---------------------------------------------------------------------------
# get_optional_user_id
# ---------------------------------------------------------------------------


class TestGetOptionalUserId:
    @pytest.mark.asyncio
    async def test_no_header_returns_none(self):
        req = _make_request()
        result = await get_optional_user_id(req, _make_admin_with_user())
        assert result is None

    @pytest.mark.asyncio
    async def test_non_bearer_returns_none(self):
        req = _make_request("Basic cred")
        result = await get_optional_user_id(req, _make_admin_with_user())
        assert result is None

    @pytest.mark.asyncio
    async def test_empty_bearer_returns_none(self):
        req = _make_request("Bearer   ")
        result = await get_optional_user_id(req, _make_admin_with_user())
        assert result is None

    @pytest.mark.asyncio
    async def test_valid_token_returns_user_id(self):
        req = _make_request("Bearer good")
        result = await get_optional_user_id(req, _make_admin_with_user("u-1"))
        assert result == "u-1"

    @pytest.mark.asyncio
    async def test_invalid_token_returns_none(self):
        req = _make_request("Bearer bad")
        result = await get_optional_user_id(req, _make_admin_no_user())
        assert result is None

    @pytest.mark.asyncio
    async def test_exception_returns_none(self):
        req = _make_request("Bearer bad")
        result = await get_optional_user_id(req, _make_admin_raises(RuntimeError("x")))
        assert result is None


# ---------------------------------------------------------------------------
# require_platform_admin
# ---------------------------------------------------------------------------


def _make_admin_chain(data):
    """Build a MagicMock admin where .table().select().eq().maybe_single().execute() returns data."""
    admin = MagicMock()
    execute_mock = AsyncMock(return_value=SimpleNamespace(data=data))
    chain = admin.table.return_value.select.return_value.eq.return_value.maybe_single.return_value
    chain.execute = execute_mock
    return admin


class TestRequirePlatformAdmin:
    @pytest.mark.asyncio
    async def test_admin_returns_user_id(self):
        admin = _make_admin_chain({"is_platform_admin": True})
        uid = await require_platform_admin(user_id="ceo-id", admin=admin)
        assert uid == "ceo-id"

    @pytest.mark.asyncio
    async def test_non_admin_raises_403(self):
        admin = _make_admin_chain({"is_platform_admin": False})
        with pytest.raises(HTTPException) as exc:
            await require_platform_admin(user_id="user", admin=admin)
        assert exc.value.status_code == 403
        assert exc.value.detail["code"] == "NOT_PLATFORM_ADMIN"

    @pytest.mark.asyncio
    async def test_no_profile_raises_403(self):
        admin = _make_admin_chain(None)
        with pytest.raises(HTTPException) as exc:
            await require_platform_admin(user_id="ghost", admin=admin)
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_missing_field_raises_403(self):
        admin = _make_admin_chain({})
        with pytest.raises(HTTPException) as exc:
            await require_platform_admin(user_id="user", admin=admin)
        assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# _get_or_create_admin_client singleton
# ---------------------------------------------------------------------------


class TestAdminClientSingleton:
    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        original = deps._admin_client
        deps._admin_client = None
        yield
        deps._admin_client = original

    @pytest.mark.asyncio
    @patch("app.deps.acreate_client", new_callable=AsyncMock)
    async def test_creates_once(self, mock_create):
        mock_create.return_value = AsyncMock()
        c1 = await deps._get_or_create_admin_client()
        c2 = await deps._get_or_create_admin_client()
        assert c1 is c2
        mock_create.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.deps.acreate_client", new_callable=AsyncMock)
    async def test_returns_existing_fast_path(self, mock_create):
        sentinel = AsyncMock()
        deps._admin_client = sentinel
        result = await deps._get_or_create_admin_client()
        assert result is sentinel
        mock_create.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.deps.acreate_client", new_callable=AsyncMock)
    async def test_get_supabase_admin_yields_singleton(self, mock_create):
        mock_create.return_value = AsyncMock()
        client = await _exhaust(deps.get_supabase_admin())
        assert client is deps._admin_client


# ---------------------------------------------------------------------------
# get_supabase_anon
# ---------------------------------------------------------------------------


class TestGetSupabaseAnon:
    @pytest.mark.asyncio
    @patch("app.deps.acreate_client", new_callable=AsyncMock)
    async def test_creates_anon_client(self, mock_create):
        mock_client = AsyncMock()
        mock_create.return_value = mock_client
        client = await _exhaust(deps.get_supabase_anon())
        assert client is mock_client
        mock_create.assert_called_once()
