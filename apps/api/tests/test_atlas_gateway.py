"""Unit tests for Atlas Gateway router.

Covers:
- GET /api/atlas/health — healthcheck response
- POST /api/atlas/proposal — auth gates (503/403)
- POST /api/atlas/proposal — happy path, file append, corrupt-JSON recovery
- POST /api/atlas/proposal — OSError on write (Railway read-only FS)
- POST /api/atlas/proposal — empty body
- _PROPOSALS_PATH constant value
- GET /api/atlas/learnings — cross-product memory bridge (E2)
"""

from __future__ import annotations

import json
import pathlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

import app.routers.atlas_gateway as gw_module
from app.deps import get_current_user_id, get_supabase_admin
from app.main import app

GATEWAY_SECRET = "test-gateway-secret-abc123"

# ── helpers ────────────────────────────────────────────────────────────────


def _make_client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _proposal_path(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path / "proposals.json"


# ── constant sanity check ──────────────────────────────────────────────────


def test_proposals_path_constant():
    """_PROPOSALS_PATH must point to memory/swarm/proposals.json."""
    assert pathlib.Path("memory/swarm/proposals.json") == gw_module._PROPOSALS_PATH


# ── GET /api/atlas/health ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_health_returns_200():
    async with _make_client() as ac:
        resp = await ac.get("/api/atlas/health")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_health_body():
    async with _make_client() as ac:
        resp = await ac.get("/api/atlas/health")
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "atlas-gateway"


# ── POST /api/atlas/proposal — auth gates ─────────────────────────────────


@pytest.mark.asyncio
async def test_proposal_503_when_gateway_secret_not_configured(tmp_path, monkeypatch):
    """503 when settings.gateway_secret is empty string."""
    from app.config import settings

    monkeypatch.setattr(settings, "gateway_secret", "")

    with patch.object(gw_module, "_PROPOSALS_PATH", _proposal_path(tmp_path)):
        async with _make_client() as ac:
            resp = await ac.post(
                "/api/atlas/proposal",
                json={"title": "test"},
                headers={"X-Gateway-Secret": "anything"},
            )
    assert resp.status_code == 503
    assert "not configured" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_proposal_403_on_wrong_secret(tmp_path, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "gateway_secret", GATEWAY_SECRET)

    with patch.object(gw_module, "_PROPOSALS_PATH", _proposal_path(tmp_path)):
        async with _make_client() as ac:
            resp = await ac.post(
                "/api/atlas/proposal",
                json={"title": "test"},
                headers={"X-Gateway-Secret": "wrong-secret"},
            )
    assert resp.status_code == 403
    assert "invalid" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_proposal_403_on_missing_secret_header(tmp_path, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "gateway_secret", GATEWAY_SECRET)

    with patch.object(gw_module, "_PROPOSALS_PATH", _proposal_path(tmp_path)):
        async with _make_client() as ac:
            resp = await ac.post(
                "/api/atlas/proposal",
                json={"title": "test"},
                # no X-Gateway-Secret header
            )
    assert resp.status_code == 403


# ── POST /api/atlas/proposal — happy path ─────────────────────────────────


@pytest.mark.asyncio
async def test_proposal_happy_path_queued(tmp_path, monkeypatch):
    """Correct secret → 200, proposal written to file."""
    from app.config import settings

    monkeypatch.setattr(settings, "gateway_secret", GATEWAY_SECRET)
    proposals_file = _proposal_path(tmp_path)

    with patch.object(gw_module, "_PROPOSALS_PATH", proposals_file):
        async with _make_client() as ac:
            resp = await ac.post(
                "/api/atlas/proposal",
                json={"title": "ship it", "priority": "high"},
                headers={"X-Gateway-Secret": GATEWAY_SECRET},
            )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "queued"
    assert data["total"] == 1

    written = json.loads(proposals_file.read_text(encoding="utf-8"))
    assert len(written) == 1
    assert written[0]["title"] == "ship it"


@pytest.mark.asyncio
async def test_proposal_appends_to_existing_file(tmp_path, monkeypatch):
    """Second proposal appends to list; total reflects both entries."""
    from app.config import settings

    monkeypatch.setattr(settings, "gateway_secret", GATEWAY_SECRET)
    proposals_file = _proposal_path(tmp_path)

    # Pre-seed one proposal
    proposals_file.write_text(
        json.dumps([{"title": "first"}], ensure_ascii=False),
        encoding="utf-8",
    )

    with patch.object(gw_module, "_PROPOSALS_PATH", proposals_file):
        async with _make_client() as ac:
            resp = await ac.post(
                "/api/atlas/proposal",
                json={"title": "second"},
                headers={"X-Gateway-Secret": GATEWAY_SECRET},
            )

    assert resp.status_code == 200
    assert resp.json()["total"] == 2

    written = json.loads(proposals_file.read_text(encoding="utf-8"))
    assert written[0]["title"] == "first"
    assert written[1]["title"] == "second"


# ── POST /api/atlas/proposal — corrupt / non-list existing file ────────────


@pytest.mark.asyncio
async def test_proposal_handles_corrupt_json_in_file(tmp_path, monkeypatch):
    """Corrupt JSON in existing file → reset to [] and still queue the proposal."""
    from app.config import settings

    monkeypatch.setattr(settings, "gateway_secret", GATEWAY_SECRET)
    proposals_file = _proposal_path(tmp_path)
    proposals_file.write_text("{{{broken json", encoding="utf-8")

    with patch.object(gw_module, "_PROPOSALS_PATH", proposals_file):
        async with _make_client() as ac:
            resp = await ac.post(
                "/api/atlas/proposal",
                json={"title": "after corrupt"},
                headers={"X-Gateway-Secret": GATEWAY_SECRET},
            )

    assert resp.status_code == 200
    assert resp.json()["total"] == 1

    written = json.loads(proposals_file.read_text(encoding="utf-8"))
    assert written == [{"title": "after corrupt"}]


@pytest.mark.asyncio
async def test_proposal_handles_non_list_json_in_file(tmp_path, monkeypatch):
    """Non-list JSON (e.g. a dict) in existing file → reset to [] and queue."""
    from app.config import settings

    monkeypatch.setattr(settings, "gateway_secret", GATEWAY_SECRET)
    proposals_file = _proposal_path(tmp_path)
    proposals_file.write_text(json.dumps({"oops": "a dict"}), encoding="utf-8")

    with patch.object(gw_module, "_PROPOSALS_PATH", proposals_file):
        async with _make_client() as ac:
            resp = await ac.post(
                "/api/atlas/proposal",
                json={"title": "after non-list"},
                headers={"X-Gateway-Secret": GATEWAY_SECRET},
            )

    assert resp.status_code == 200
    assert resp.json()["total"] == 1


# ── POST /api/atlas/proposal — OSError on write ────────────────────────────


@pytest.mark.asyncio
async def test_proposal_write_oserror_still_returns_queued(tmp_path, monkeypatch):
    """OSError during file write (Railway read-only FS) → still returns queued."""
    from app.config import settings

    monkeypatch.setattr(settings, "gateway_secret", GATEWAY_SECRET)
    proposals_file = _proposal_path(tmp_path)

    # Patch write_text on pathlib.Path so the router's write call raises OSError.
    original_write_text = pathlib.Path.write_text

    def _raise_on_target(self, *args, **kwargs):
        if self == proposals_file:
            raise OSError("Read-only file system")
        return original_write_text(self, *args, **kwargs)

    with (
        patch.object(gw_module, "_PROPOSALS_PATH", proposals_file),
        patch.object(pathlib.Path, "write_text", _raise_on_target),
    ):
        async with _make_client() as ac:
            resp = await ac.post(
                "/api/atlas/proposal",
                json={"title": "volatile"},
                headers={"X-Gateway-Secret": GATEWAY_SECRET},
            )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "queued"
    assert data["total"] == 1


# ── POST /api/atlas/proposal — empty body ─────────────────────────────────


@pytest.mark.asyncio
async def test_proposal_empty_body_accepted(tmp_path, monkeypatch):
    """Empty JSON object body is valid — router accepts any dict."""
    from app.config import settings

    monkeypatch.setattr(settings, "gateway_secret", GATEWAY_SECRET)
    proposals_file = _proposal_path(tmp_path)

    with patch.object(gw_module, "_PROPOSALS_PATH", proposals_file):
        async with _make_client() as ac:
            resp = await ac.post(
                "/api/atlas/proposal",
                json={},
                headers={"X-Gateway-Secret": GATEWAY_SECRET},
            )

    assert resp.status_code == 200
    assert resp.json()["total"] == 1

    written = json.loads(proposals_file.read_text(encoding="utf-8"))
    assert written == [{}]


# ── GET /api/atlas/learnings — cross-product memory bridge (E2) ────────────

_SAMPLE_LEARNINGS = [
    {
        "id": "aaa",
        "category": "preference",
        "content": "CEO ненавидит длинные списки",
        "emotional_intensity": 4.0,
        "created_at": "2026-04-12T10:00:00+00:00",
        "last_accessed_at": "2026-04-20T09:00:00+00:00",
        "access_count": 5,
    },
    {
        "id": "bbb",
        "category": "insight",
        "content": "CEO prefers storytelling over tables",
        "emotional_intensity": 3.0,
        "created_at": "2026-04-13T10:00:00+00:00",
        "last_accessed_at": "2026-04-20T09:00:00+00:00",
        "access_count": 2,
    },
]


def _make_admin_mock(rows: list | None = None) -> AsyncMock:
    """Build a mock Supabase admin client that returns `rows` for any chained query."""
    rows = rows if rows is not None else _SAMPLE_LEARNINGS
    result = MagicMock()
    result.data = rows

    chain = AsyncMock()
    chain.execute = AsyncMock(return_value=result)
    chain.order = MagicMock(return_value=chain)
    chain.limit = MagicMock(return_value=chain)
    chain.eq = MagicMock(return_value=chain)
    chain.in_ = MagicMock(return_value=chain)
    chain.update = MagicMock(return_value=chain)
    chain.select = MagicMock(return_value=chain)

    mock_admin = AsyncMock()
    mock_admin.table = MagicMock(return_value=chain)
    return mock_admin


@pytest.mark.asyncio
async def test_learnings_401_without_auth():
    """No JWT → 401 Unauthorized."""
    mock_admin = _make_admin_mock()
    app.dependency_overrides[get_supabase_admin] = lambda: mock_admin
    try:
        async with _make_client() as ac:
            resp = await ac.get("/api/atlas/learnings")
    finally:
        app.dependency_overrides.pop(get_supabase_admin, None)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_learnings_happy_path():
    """Authenticated call → 200 with learnings list."""
    mock_admin = _make_admin_mock()

    app.dependency_overrides[get_supabase_admin] = lambda: mock_admin
    app.dependency_overrides[get_current_user_id] = lambda: "user-123"
    try:
        async with _make_client() as ac:
            resp = await ac.get("/api/atlas/learnings")
    finally:
        app.dependency_overrides.pop(get_supabase_admin, None)
        app.dependency_overrides.pop(get_current_user_id, None)

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert data["limit"] == 20
    assert data["category_filter"] is None
    assert data["learnings"][0]["category"] == "preference"


@pytest.mark.asyncio
async def test_learnings_empty_when_no_rows():
    """DB returns empty list → 200 with total=0."""
    mock_admin = _make_admin_mock(rows=[])

    app.dependency_overrides[get_supabase_admin] = lambda: mock_admin
    app.dependency_overrides[get_current_user_id] = lambda: "user-123"
    try:
        async with _make_client() as ac:
            resp = await ac.get("/api/atlas/learnings")
    finally:
        app.dependency_overrides.pop(get_supabase_admin, None)
        app.dependency_overrides.pop(get_current_user_id, None)

    assert resp.status_code == 200
    assert resp.json()["total"] == 0
    assert resp.json()["learnings"] == []


@pytest.mark.asyncio
async def test_learnings_category_filter():
    """?category=preference → 200, category_filter echoed in response."""
    mock_admin = _make_admin_mock(rows=[_SAMPLE_LEARNINGS[0]])

    app.dependency_overrides[get_supabase_admin] = lambda: mock_admin
    app.dependency_overrides[get_current_user_id] = lambda: "user-123"
    try:
        async with _make_client() as ac:
            resp = await ac.get("/api/atlas/learnings?category=preference")
    finally:
        app.dependency_overrides.pop(get_supabase_admin, None)
        app.dependency_overrides.pop(get_current_user_id, None)

    assert resp.status_code == 200
    assert resp.json()["category_filter"] == "preference"
    assert resp.json()["total"] == 1


@pytest.mark.asyncio
async def test_learnings_invalid_category_422():
    """?category=unknown → 422 with INVALID_CATEGORY code."""
    app.dependency_overrides[get_supabase_admin] = lambda: _make_admin_mock()
    app.dependency_overrides[get_current_user_id] = lambda: "user-123"
    try:
        async with _make_client() as ac:
            resp = await ac.get("/api/atlas/learnings?category=unknown_bad")
    finally:
        app.dependency_overrides.pop(get_supabase_admin, None)
        app.dependency_overrides.pop(get_current_user_id, None)

    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "INVALID_CATEGORY"


@pytest.mark.asyncio
async def test_learnings_limit_param():
    """?limit=5 → limit echoed in response."""
    mock_admin = _make_admin_mock()

    app.dependency_overrides[get_supabase_admin] = lambda: mock_admin
    app.dependency_overrides[get_current_user_id] = lambda: "user-123"
    try:
        async with _make_client() as ac:
            resp = await ac.get("/api/atlas/learnings?limit=5")
    finally:
        app.dependency_overrides.pop(get_supabase_admin, None)
        app.dependency_overrides.pop(get_current_user_id, None)

    assert resp.status_code == 200
    assert resp.json()["limit"] == 5


@pytest.mark.asyncio
async def test_learnings_limit_too_large_422():
    """?limit=200 → 422 (exceeds max=100)."""
    app.dependency_overrides[get_supabase_admin] = lambda: _make_admin_mock()
    app.dependency_overrides[get_current_user_id] = lambda: "user-123"
    try:
        async with _make_client() as ac:
            resp = await ac.get("/api/atlas/learnings?limit=200")
    finally:
        app.dependency_overrides.pop(get_supabase_admin, None)
        app.dependency_overrides.pop(get_current_user_id, None)

    assert resp.status_code == 422
