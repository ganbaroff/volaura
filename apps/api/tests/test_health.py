"""Health endpoint tests."""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.deps import get_supabase_admin


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
        assert data["version"] == "0.1.0"
        assert "database" in data
        assert "llm_configured" in data
    finally:
        app.dependency_overrides.pop(get_supabase_admin, None)
