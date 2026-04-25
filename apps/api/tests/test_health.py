"""Health endpoint tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient

from app.deps import get_supabase_admin
from app.main import app


async def _mock_admin_for_health():
    """Mock SupabaseAdmin for health check — simulates empty DB (degraded is expected in tests)."""
    mock = AsyncMock()
    # Simulate empty competencies table → db_status = "empty" → status = "degraded"
    table_mock = MagicMock()
    select_mock = MagicMock()
    limit_mock = AsyncMock()
    limit_mock.execute = AsyncMock(return_value=MagicMock(count=0))
    select_mock.limit = MagicMock(return_value=limit_mock)
    table_mock.select = MagicMock(return_value=select_mock)
    mock.table = MagicMock(return_value=table_mock)
    yield mock


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    app.dependency_overrides[get_supabase_admin] = _mock_admin_for_health
    try:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        # In test environment (no real Supabase/Gemini), status may be "degraded" — that is expected.
        # In production (real services connected), status will be "ok".
        assert data["status"] in ("ok", "degraded"), f"Unexpected status: {data['status']}"
        assert data["version"] == "0.2.0"
        assert "database" in data
        assert "llm_configured" in data
        # INC-019 mitigation #4 — git_sha must be present so regression pack
        # can assert deployed SHA matches origin/main HEAD.
        assert "git_sha" in data
        assert isinstance(data["git_sha"], str)
        assert len(data["git_sha"]) <= 12
    finally:
        app.dependency_overrides.pop(get_supabase_admin, None)


@pytest.mark.asyncio
async def test_health_git_sha_from_railway_env(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
):
    """Railway injects RAILWAY_GIT_COMMIT_SHA at runtime; /health must echo it (truncated to 12)."""
    monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", "abcdef0123456789deadbeef")
    monkeypatch.delenv("GIT_SHA", raising=False)
    app.dependency_overrides[get_supabase_admin] = _mock_admin_for_health
    try:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["git_sha"] == "abcdef012345"
    finally:
        app.dependency_overrides.pop(get_supabase_admin, None)


@pytest.mark.asyncio
async def test_health_git_sha_fallback_to_dockerfile_arg(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
):
    """When RAILWAY_GIT_COMMIT_SHA absent, fall back to GIT_SHA (Dockerfile ARG)."""
    monkeypatch.delenv("RAILWAY_GIT_COMMIT_SHA", raising=False)
    monkeypatch.setenv("GIT_SHA", "1234567abcd")
    app.dependency_overrides[get_supabase_admin] = _mock_admin_for_health
    try:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["git_sha"] == "1234567abcd"
    finally:
        app.dependency_overrides.pop(get_supabase_admin, None)


@pytest.mark.asyncio
async def test_health_git_sha_unknown_when_no_env(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
):
    """Local-dev with no env vars: returns 'unknown', does not crash."""
    monkeypatch.delenv("RAILWAY_GIT_COMMIT_SHA", raising=False)
    monkeypatch.delenv("GIT_SHA", raising=False)
    app.dependency_overrides[get_supabase_admin] = _mock_admin_for_health
    try:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["git_sha"] == "unknown"
    finally:
        app.dependency_overrides.pop(get_supabase_admin, None)
