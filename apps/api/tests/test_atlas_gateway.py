"""Unit tests for Atlas Gateway router.

Covers:
- GET /api/atlas/health — healthcheck response
- POST /api/atlas/proposal — auth gates (503/403)
- POST /api/atlas/proposal — happy path, file append, corrupt-JSON recovery
- POST /api/atlas/proposal — OSError on write (Railway read-only FS)
- POST /api/atlas/proposal — empty body
- _PROPOSALS_PATH constant value
"""

from __future__ import annotations

import json
import pathlib
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

import app.routers.atlas_gateway as gw_module
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
