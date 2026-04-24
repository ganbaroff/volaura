"""Tests for /api/atlas/consult — Layer 3 self-consult endpoint.

Three required scenarios:
  1. Valid authenticated request returns correct response shape.
  2. Unauthenticated request (no Bearer token) returns 401.
  3. ANTHROPIC_API_KEY missing → 503 with structured error body.
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.deps import get_current_user_id, get_supabase_admin
from app.main import app

_TEST_USER_ID = "test-user-uuid-0000-1234"


# ── Shared dependency overrides ───────────────────────────────────────────────


def _make_admin_override():
    """Generator dependency override — yields a mocked admin client."""
    mock = AsyncMock()
    user = MagicMock()
    user.id = _TEST_USER_ID
    user_response = MagicMock()
    user_response.user = user
    mock.auth.get_user = AsyncMock(return_value=user_response)

    async def _override():
        yield mock

    return _override


def _make_user_id_override():
    """Non-generator dependency override — returns test user id directly."""

    async def _override():
        return _TEST_USER_ID

    return _override


def _build_mock_anthropic_response(reply_text: str) -> MagicMock:
    """Return a mock httpx.Response with Anthropic messages API shape."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "content": [{"type": "text", "text": reply_text}],
        "model": "claude-sonnet-4-5-20250929",
        "stop_reason": "end_turn",
    }
    return mock_resp


# ── Test 1: valid request returns correct shape ───────────────────────────────


@pytest.mark.asyncio
async def test_atlas_consult_valid_request_returns_shape(client: AsyncClient):
    """Valid authenticated request → 200 with {response, provider, state, model}."""
    fake_reply = "Ситуация понятна. Иди вперёд — это правильный путь.\n\n— Атлас"
    mock_resp = _build_mock_anthropic_response(fake_reply)

    app.dependency_overrides[get_current_user_id] = _make_user_id_override()
    app.dependency_overrides[get_supabase_admin] = _make_admin_override()

    try:
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test-key"}):
            with patch("app.routers.atlas_consult.httpx.AsyncClient") as mock_client_cls:
                # Simulate async context manager returning a mock with async .post()
                mock_http = AsyncMock()
                mock_http.post = AsyncMock(return_value=mock_resp)
                mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
                mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

                resp = await client.post(
                    "/api/atlas/consult",
                    json={
                        "situation": "CEO asked what I would do next. Three PRs open.",
                        "draft": "Три PR открыты, жду merge.",
                        "emotional_state": "A",
                    },
                    headers={"Authorization": "Bearer fake-jwt-token"},
                )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "response" in data
        assert "provider" in data
        assert "state" in data
        assert "model" in data
        assert data["provider"] == "anthropic"
        assert data["state"] == "A"
        assert data["response"] == fake_reply
        assert "sonnet" in data["model"]
    finally:
        app.dependency_overrides.pop(get_current_user_id, None)
        app.dependency_overrides.pop(get_supabase_admin, None)


# ── Test 2: unauthenticated returns 401 ───────────────────────────────────────


@pytest.mark.asyncio
async def test_atlas_consult_unauthenticated_returns_401(client: AsyncClient):
    """Request without Authorization header → 401 MISSING_TOKEN.

    get_supabase_admin is NOT overridden here — the auth check in
    get_current_user_id fires before any DB call and raises 401 on missing header.
    """
    # Override admin to avoid real Supabase connection but NOT the user_id check —
    # we want the real get_current_user_id to fire and reject the missing token.
    app.dependency_overrides[get_supabase_admin] = _make_admin_override()
    try:
        resp = await client.post(
            "/api/atlas/consult",
            json={"situation": "Am I allowed in without a token?"},
            # No Authorization header → get_current_user_id should reject
        )
        assert resp.status_code == 401
        data = resp.json()
        assert "detail" in data
    finally:
        app.dependency_overrides.pop(get_supabase_admin, None)


# ── Test 3: missing ANTHROPIC_API_KEY returns 503 ────────────────────────────


@pytest.mark.asyncio
async def test_atlas_consult_missing_api_key_returns_503(client: AsyncClient):
    """When ANTHROPIC_API_KEY is absent → 503 with code LLM_UNAVAILABLE."""
    app.dependency_overrides[get_current_user_id] = _make_user_id_override()
    app.dependency_overrides[get_supabase_admin] = _make_admin_override()

    try:
        # Remove ANTHROPIC_API_KEY from environment for this test
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            resp = await client.post(
                "/api/atlas/consult",
                json={"situation": "What happens when the key is gone?"},
                headers={"Authorization": "Bearer fake-jwt-token"},
            )

        assert resp.status_code == 503, f"Expected 503, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "detail" in data
        detail = data["detail"]
        # Structured error body: {"code": "LLM_UNAVAILABLE", "message": "..."}
        assert detail.get("code") == "LLM_UNAVAILABLE"
        assert "ANTHROPIC_API_KEY" in detail.get("message", "")
    finally:
        app.dependency_overrides.pop(get_current_user_id, None)
        app.dependency_overrides.pop(get_supabase_admin, None)


# ── Test 4: situation is required (schema validation) ────────────────────────


@pytest.mark.asyncio
async def test_atlas_consult_missing_situation_returns_422(client: AsyncClient):
    """Request without situation field → 422 validation error."""
    app.dependency_overrides[get_current_user_id] = _make_user_id_override()
    app.dependency_overrides[get_supabase_admin] = _make_admin_override()

    try:
        resp = await client.post(
            "/api/atlas/consult",
            json={"draft": "Just a draft, no situation"},
            headers={"Authorization": "Bearer fake-jwt-token"},
        )
        assert resp.status_code == 422
    finally:
        app.dependency_overrides.pop(get_current_user_id, None)
        app.dependency_overrides.pop(get_supabase_admin, None)


# ── Test 5: optional fields are truly optional ───────────────────────────────


@pytest.mark.asyncio
async def test_atlas_consult_optional_fields_absent(client: AsyncClient):
    """Situation-only request (no draft, no emotional_state) succeeds."""
    fake_reply = "Понял. Продолжаю.\n\n— Атлас"
    mock_resp = _build_mock_anthropic_response(fake_reply)

    app.dependency_overrides[get_current_user_id] = _make_user_id_override()
    app.dependency_overrides[get_supabase_admin] = _make_admin_override()

    try:
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test-key"}):
            with patch("app.routers.atlas_consult.httpx.AsyncClient") as mock_client_cls:
                mock_http = AsyncMock()
                mock_http.post = AsyncMock(return_value=mock_resp)
                mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
                mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

                resp = await client.post(
                    "/api/atlas/consult",
                    json={"situation": "Need a gut-check on this path."},
                    headers={"Authorization": "Bearer fake-jwt-token"},
                )

        assert resp.status_code == 200
        data = resp.json()
        assert data["state"] is None
        assert data["response"] == fake_reply
    finally:
        app.dependency_overrides.pop(get_current_user_id, None)
        app.dependency_overrides.pop(get_supabase_admin, None)
