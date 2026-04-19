"""HTTP-level integration tests for BrandedBy router.

Uses TestClient (ASGITransport + AsyncClient) against the real FastAPI app.
Supabase calls and JWT auth are fully mocked via dependency_overrides.

Endpoints covered:
  POST   /api/brandedby/twins                         — create_twin
  GET    /api/brandedby/twins                         — get_my_twin
  PATCH  /api/brandedby/twins/{twin_id}               — update_twin
  POST   /api/brandedby/twins/{twin_id}/refresh-personality
  POST   /api/brandedby/twins/{twin_id}/activate
  POST   /api/brandedby/generations                   — create_generation
  GET    /api/brandedby/generations                   — list_generations
  GET    /api/brandedby/generations/{gen_id}          — get_generation
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin
from app.main import app
from app.routers.brandedby import QUEUE_SKIP_CRYSTAL_COST

# ── Constants ──────────────────────────────────────────────────────────────────

USER_ID = "bb000001-0000-0000-0000-000000000001"
OTHER_USER_ID = "bb000002-0000-0000-0000-000000000002"
TWIN_ID = str(uuid.uuid4())
GEN_ID = str(uuid.uuid4())
NOW = datetime.now(UTC).isoformat()

AUTH_HEADERS = {"Authorization": "Bearer test-token"}

# ── Override helpers ───────────────────────────────────────────────────────────


def _user_id_override(uid: str = USER_ID):
    async def _dep():
        return uid

    return _dep


def _admin_override(mock_client):
    async def _dep():
        yield mock_client

    return _dep


# ── Chainable Supabase mock ────────────────────────────────────────────────────

_BUILDER_METHODS = [
    "schema",
    "table",
    "select",
    "insert",
    "update",
    "delete",
    "upsert",
    "eq",
    "neq",
    "order",
    "range",
    "filter",
    "limit",
    "single",
    "maybe_single",
    "count",
]


def _make_chain(*execute_returns):
    """Chainable Supabase builder mock; supports multiple sequential execute() calls."""
    db = MagicMock()
    chain = MagicMock()

    for method in _BUILDER_METHODS:
        getattr(chain, method).return_value = chain
        getattr(db, method).return_value = chain

    if len(execute_returns) == 1:
        chain.execute = AsyncMock(return_value=execute_returns[0])
        db.execute = AsyncMock(return_value=execute_returns[0])
    else:
        chain.execute = AsyncMock(side_effect=list(execute_returns))
        db.execute = AsyncMock(side_effect=list(execute_returns))

    return db


def _make_chain_with_rpc(schema_returns: list, rpc_return=None):
    """Chainable mock with separate rpc() path."""
    db = _make_chain(*schema_returns)

    rpc_chain = MagicMock()
    rpc_chain.execute = AsyncMock(return_value=rpc_return or _r(data=[]))
    db.rpc = MagicMock(return_value=rpc_chain)

    return db


def _r(data=None, *, count: int | None = None) -> MagicMock:
    r = MagicMock()
    r.data = data
    r.count = count
    return r


# ── Row factories ──────────────────────────────────────────────────────────────


def _twin_row(**overrides) -> dict:
    base = {
        "id": TWIN_ID,
        "user_id": USER_ID,
        "display_name": "Test Twin",
        "tagline": "A tagline",
        "photo_url": "https://example.com/photo.jpg",
        "voice_id": None,
        "personality_prompt": "You are Test Twin.",
        "status": "draft",
        "created_at": NOW,
        "updated_at": NOW,
    }
    return {**base, **overrides}


def _gen_row(**overrides) -> dict:
    base = {
        "id": GEN_ID,
        "twin_id": TWIN_ID,
        "user_id": USER_ID,
        "gen_type": "video",
        "input_text": "Hello world test script",
        "output_url": None,
        "thumbnail_url": None,
        "status": "queued",
        "error_message": None,
        "queue_position": 1,
        "crystal_cost": 0,
        "duration_seconds": None,
        "processing_started_at": None,
        "completed_at": None,
        "created_at": NOW,
    }
    return {**base, **overrides}


# ── HTTP client helper ─────────────────────────────────────────────────────────


async def _call(method: str, path: str, *, db, uid: str = USER_ID, **kwargs):
    """Make one HTTP call with dependency overrides applied, then clear them."""
    app.dependency_overrides[get_current_user_id] = _user_id_override(uid)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            fn = getattr(ac, method)
            return await fn(path, headers=AUTH_HEADERS, **kwargs)
    finally:
        app.dependency_overrides.clear()


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/brandedby/twins
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_create_twin_happy_path():
    """201 with AITwinOut body on successful creation."""
    db = _make_chain(
        _r(data=[]),  # existing check — no twin
        _r(data=[_twin_row()]),  # insert
    )
    resp = await _call("post", "/api/brandedby/twins", db=db, json={"display_name": "Test Twin"})

    assert resp.status_code == 201
    body = resp.json()
    assert body["display_name"] == "Test Twin"
    assert body["status"] == "draft"
    assert "id" in body


@pytest.mark.asyncio
async def test_create_twin_no_auth_returns_401():
    """No Authorization header → 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/brandedby/twins", json={"display_name": "Twin"})

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_twin_already_exists_returns_409():
    """409 TWIN_EXISTS when user already has a twin."""
    db = _make_chain(_r(data=[{"id": TWIN_ID}]))  # existing check → has twin
    resp = await _call("post", "/api/brandedby/twins", db=db, json={"display_name": "Another Twin"})

    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "TWIN_EXISTS"


@pytest.mark.asyncio
async def test_create_twin_db_insert_fails_returns_500():
    """500 CREATE_FAILED when DB insert returns empty data."""
    db = _make_chain(
        _r(data=[]),  # no existing twin
        _r(data=[]),  # insert fails
    )
    resp = await _call("post", "/api/brandedby/twins", db=db, json={"display_name": "Broken Twin"})

    assert resp.status_code == 500
    assert resp.json()["detail"]["code"] == "CREATE_FAILED"


@pytest.mark.asyncio
async def test_create_twin_with_optional_fields():
    """Optional tagline and photo_url are reflected in response."""
    row = _twin_row(tagline="My tagline", photo_url="https://img.example.com/face.jpg")
    db = _make_chain(_r(data=[]), _r(data=[row]))
    resp = await _call(
        "post",
        "/api/brandedby/twins",
        db=db,
        json={
            "display_name": "Full Twin",
            "tagline": "My tagline",
            "photo_url": "https://img.example.com/face.jpg",
        },
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["tagline"] == "My tagline"
    assert body["photo_url"] == "https://img.example.com/face.jpg"


@pytest.mark.asyncio
async def test_create_twin_missing_display_name_returns_422():
    """422 Unprocessable Entity when display_name is missing."""
    db = _make_chain(_r(data=[]))
    resp = await _call("post", "/api/brandedby/twins", db=db, json={})

    assert resp.status_code == 422


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/brandedby/twins
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_get_my_twin_happy_path():
    """200 with AITwinOut body when twin exists."""
    db = _make_chain(_r(data=_twin_row()))
    resp = await _call("get", "/api/brandedby/twins", db=db)

    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == TWIN_ID
    assert body["display_name"] == "Test Twin"


@pytest.mark.asyncio
async def test_get_my_twin_no_auth_returns_401():
    """No Authorization header → 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/brandedby/twins")

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_my_twin_returns_null_when_no_twin():
    """200 with null body when user has no twin."""
    db = _make_chain(_r(data=None))
    resp = await _call("get", "/api/brandedby/twins", db=db)

    assert resp.status_code == 200
    assert resp.json() is None


@pytest.mark.asyncio
async def test_get_my_twin_active_status():
    """Returns twin with active status."""
    db = _make_chain(_r(data=_twin_row(status="active")))
    resp = await _call("get", "/api/brandedby/twins", db=db)

    assert resp.status_code == 200
    assert resp.json()["status"] == "active"


# ══════════════════════════════════════════════════════════════════════════════
# PATCH /api/brandedby/twins/{twin_id}
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_update_twin_happy_path():
    """200 with updated twin on successful PATCH."""
    updated = _twin_row(display_name="Updated Name")
    db = _make_chain(
        _r(data={"id": TWIN_ID, "user_id": USER_ID}),  # ownership check
        _r(data=[updated]),  # update result
    )
    resp = await _call(
        "patch", f"/api/brandedby/twins/{TWIN_ID}", db=db, json={"display_name": "Updated Name"}
    )

    assert resp.status_code == 200
    assert resp.json()["display_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_update_twin_no_auth_returns_401():
    """No Authorization header → 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.patch(f"/api/brandedby/twins/{TWIN_ID}", json={"display_name": "x"})

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_update_twin_not_found_returns_404():
    """404 TWIN_NOT_FOUND when no twin with that id."""
    db = _make_chain(_r(data=None))
    resp = await _call(
        "patch", f"/api/brandedby/twins/{TWIN_ID}", db=db, json={"display_name": "x"}
    )

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "TWIN_NOT_FOUND"


@pytest.mark.asyncio
async def test_update_twin_not_owner_returns_403():
    """403 NOT_OWNER when user doesn't own the twin."""
    db = _make_chain(_r(data={"id": TWIN_ID, "user_id": OTHER_USER_ID}))
    resp = await _call(
        "patch", f"/api/brandedby/twins/{TWIN_ID}", db=db, json={"display_name": "x"}
    )

    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "NOT_OWNER"


@pytest.mark.asyncio
async def test_update_twin_no_fields_returns_400():
    """400 NO_CHANGES when body has no updatable fields."""
    db = _make_chain(_r(data={"id": TWIN_ID, "user_id": USER_ID}))
    resp = await _call("patch", f"/api/brandedby/twins/{TWIN_ID}", db=db, json={})

    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "NO_CHANGES"


@pytest.mark.asyncio
async def test_update_twin_db_fail_returns_500():
    """500 UPDATE_FAILED when update returns empty data."""
    db = _make_chain(
        _r(data={"id": TWIN_ID, "user_id": USER_ID}),
        _r(data=[]),  # update fails
    )
    resp = await _call(
        "patch", f"/api/brandedby/twins/{TWIN_ID}", db=db, json={"tagline": "New tagline"}
    )

    assert resp.status_code == 500
    assert resp.json()["detail"]["code"] == "UPDATE_FAILED"


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/brandedby/twins/{twin_id}/refresh-personality
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_refresh_personality_happy_path():
    """200 with updated twin including personality_prompt."""
    twin_data = {"id": TWIN_ID, "user_id": USER_ID, "display_name": "Test Twin"}
    updated = _twin_row(personality_prompt="You are Test Twin, an expert...")
    db = _make_chain_with_rpc(
        schema_returns=[_r(data=twin_data), _r(data=[updated])],
        rpc_return=_r(data=[{"verified_skills": ["python"], "aura_score": 80}]),
    )

    with patch(
        "app.routers.brandedby.generate_twin_personality",
        new=AsyncMock(return_value="You are Test Twin, an expert..."),
    ):
        resp = await _call(
            "post", f"/api/brandedby/twins/{TWIN_ID}/refresh-personality", db=db
        )

    assert resp.status_code == 200
    assert resp.json()["personality_prompt"] == "You are Test Twin, an expert..."


@pytest.mark.asyncio
async def test_refresh_personality_no_auth_returns_401():
    """No Authorization header → 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(f"/api/brandedby/twins/{TWIN_ID}/refresh-personality")

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_personality_not_found_returns_404():
    """404 TWIN_NOT_FOUND when twin doesn't exist."""
    db = _make_chain_with_rpc(schema_returns=[_r(data=None)])
    resp = await _call("post", f"/api/brandedby/twins/{TWIN_ID}/refresh-personality", db=db)

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "TWIN_NOT_FOUND"


@pytest.mark.asyncio
async def test_refresh_personality_not_owner_returns_403():
    """403 NOT_OWNER when different user tries to refresh."""
    twin_data = {"id": TWIN_ID, "user_id": OTHER_USER_ID, "display_name": "Other Twin"}
    db = _make_chain_with_rpc(schema_returns=[_r(data=twin_data)])
    resp = await _call("post", f"/api/brandedby/twins/{TWIN_ID}/refresh-personality", db=db)

    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "NOT_OWNER"


@pytest.mark.asyncio
async def test_refresh_personality_store_fail_returns_500():
    """500 UPDATE_FAILED when personality store step fails."""
    twin_data = {"id": TWIN_ID, "user_id": USER_ID, "display_name": "Test Twin"}
    db = _make_chain_with_rpc(
        schema_returns=[_r(data=twin_data), _r(data=[])],  # update fails
        rpc_return=_r(data=[]),
    )

    with patch(
        "app.routers.brandedby.generate_twin_personality",
        new=AsyncMock(return_value="Generated personality"),
    ):
        resp = await _call("post", f"/api/brandedby/twins/{TWIN_ID}/refresh-personality", db=db)

    assert resp.status_code == 500
    assert resp.json()["detail"]["code"] == "UPDATE_FAILED"


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/brandedby/twins/{twin_id}/activate
# ══════════════════════════════════════════════════════════════════════════════


def _activatable_twin(**overrides) -> dict:
    base = {
        "id": TWIN_ID,
        "user_id": USER_ID,
        "status": "draft",
        "photo_url": "https://example.com/photo.jpg",
        "personality_prompt": "You are Test Twin.",
    }
    return {**base, **overrides}


@pytest.mark.asyncio
async def test_activate_twin_happy_path():
    """200 with status=active after activation."""
    activated = _twin_row(status="active")
    db = _make_chain(
        _r(data=_activatable_twin()),  # check twin
        _r(data=[activated]),  # update to active
    )
    resp = await _call("post", f"/api/brandedby/twins/{TWIN_ID}/activate", db=db)

    assert resp.status_code == 200
    assert resp.json()["status"] == "active"


@pytest.mark.asyncio
async def test_activate_twin_no_auth_returns_401():
    """No Authorization header → 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(f"/api/brandedby/twins/{TWIN_ID}/activate")

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_activate_twin_not_found_returns_404():
    """404 TWIN_NOT_FOUND when twin doesn't exist."""
    db = _make_chain(_r(data=None))
    resp = await _call("post", f"/api/brandedby/twins/{TWIN_ID}/activate", db=db)

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "TWIN_NOT_FOUND"


@pytest.mark.asyncio
async def test_activate_twin_not_owner_returns_403():
    """403 NOT_OWNER when different user tries to activate."""
    db = _make_chain(_r(data=_activatable_twin(user_id=OTHER_USER_ID)))
    resp = await _call("post", f"/api/brandedby/twins/{TWIN_ID}/activate", db=db)

    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "NOT_OWNER"


@pytest.mark.asyncio
async def test_activate_twin_already_active_returns_409():
    """409 ALREADY_ACTIVE when twin is already active."""
    db = _make_chain(_r(data=_activatable_twin(status="active")))
    resp = await _call("post", f"/api/brandedby/twins/{TWIN_ID}/activate", db=db)

    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "ALREADY_ACTIVE"


@pytest.mark.asyncio
async def test_activate_twin_missing_photo_returns_400():
    """400 MISSING_PHOTO when photo_url is None."""
    db = _make_chain(_r(data=_activatable_twin(photo_url=None)))
    resp = await _call("post", f"/api/brandedby/twins/{TWIN_ID}/activate", db=db)

    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "MISSING_PHOTO"


@pytest.mark.asyncio
async def test_activate_twin_missing_personality_returns_400():
    """400 MISSING_PERSONALITY when personality_prompt is absent."""
    db = _make_chain(_r(data=_activatable_twin(personality_prompt=None)))
    resp = await _call("post", f"/api/brandedby/twins/{TWIN_ID}/activate", db=db)

    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "MISSING_PERSONALITY"


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/brandedby/generations
# ══════════════════════════════════════════════════════════════════════════════

_GEN_BODY = {
    "twin_id": TWIN_ID,
    "gen_type": "video",
    "input_text": "Please generate this test video",
}

_ACTIVE_TWIN = {"id": TWIN_ID, "user_id": USER_ID, "status": "active"}


@pytest.mark.asyncio
async def test_create_generation_happy_path():
    """201 with GenerationOut body on successful creation."""
    row = _gen_row(queue_position=1, crystal_cost=0)
    db = _make_chain(
        _r(data=_ACTIVE_TWIN),  # twin check
        _r(data=[], count=0),  # queued count
        _r(data=[row]),  # insert
    )
    resp = await _call("post", "/api/brandedby/generations", db=db, json=_GEN_BODY)

    assert resp.status_code == 201
    body = resp.json()
    assert body["gen_type"] == "video"
    assert body["crystal_cost"] == 0
    assert body["queue_position"] == 1


@pytest.mark.asyncio
async def test_create_generation_no_auth_returns_401():
    """No Authorization header → 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/brandedby/generations", json=_GEN_BODY)

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_generation_twin_not_found_returns_404():
    """404 TWIN_NOT_FOUND when twin doesn't exist."""
    db = _make_chain(_r(data=None))
    resp = await _call("post", "/api/brandedby/generations", db=db, json=_GEN_BODY)

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "TWIN_NOT_FOUND"


@pytest.mark.asyncio
async def test_create_generation_not_owner_returns_403():
    """403 NOT_OWNER when user doesn't own the twin."""
    twin = {"id": TWIN_ID, "user_id": OTHER_USER_ID, "status": "active"}
    db = _make_chain(_r(data=twin))
    resp = await _call("post", "/api/brandedby/generations", db=db, json=_GEN_BODY)

    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "NOT_OWNER"


@pytest.mark.asyncio
async def test_create_generation_twin_not_active_returns_400():
    """400 TWIN_NOT_ACTIVE when twin is in draft status."""
    twin = {"id": TWIN_ID, "user_id": USER_ID, "status": "draft"}
    db = _make_chain(_r(data=twin))
    resp = await _call("post", "/api/brandedby/generations", db=db, json=_GEN_BODY)

    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "TWIN_NOT_ACTIVE"


@pytest.mark.asyncio
async def test_create_generation_skip_queue_deducts_crystals():
    """201 with crystal_cost=25 when skip_queue=True."""
    row = _gen_row(queue_position=0, crystal_cost=QUEUE_SKIP_CRYSTAL_COST)

    db = MagicMock()
    chain = MagicMock()
    for method in _BUILDER_METHODS:
        getattr(chain, method).return_value = chain
        getattr(db, method).return_value = chain

    chain.execute = AsyncMock(
        side_effect=[
            _r(data=_ACTIVE_TWIN),  # twin check
            _r(data=[{"id": "audit-id"}]),  # character_events audit insert
            _r(data=[row]),  # generation insert
        ]
    )
    rpc_chain = MagicMock()
    rpc_chain.execute = AsyncMock(return_value=_r(data=[{"success": True, "new_balance": 75}]))
    db.rpc = MagicMock(return_value=rpc_chain)

    body = {**_GEN_BODY, "skip_queue": True}
    resp = await _call("post", "/api/brandedby/generations", db=db, json=body)

    assert resp.status_code == 201
    assert resp.json()["crystal_cost"] == QUEUE_SKIP_CRYSTAL_COST
    assert resp.json()["queue_position"] == 0


@pytest.mark.asyncio
async def test_create_generation_insufficient_crystals_returns_402():
    """402 INSUFFICIENT_CRYSTALS when deduct_crystals_atomic returns success=False."""
    db = MagicMock()
    chain = MagicMock()
    for method in _BUILDER_METHODS:
        getattr(chain, method).return_value = chain
        getattr(db, method).return_value = chain

    chain.execute = AsyncMock(return_value=_r(data=_ACTIVE_TWIN))
    rpc_chain = MagicMock()
    rpc_chain.execute = AsyncMock(
        return_value=_r(
            data=[
                {
                    "success": False,
                    "error_code": "INSUFFICIENT_CRYSTALS",
                    "error_msg": "Not enough crystals",
                }
            ]
        )
    )
    db.rpc = MagicMock(return_value=rpc_chain)

    body = {**_GEN_BODY, "skip_queue": True}
    resp = await _call("post", "/api/brandedby/generations", db=db, json=body)

    assert resp.status_code == 402
    assert resp.json()["detail"]["code"] == "INSUFFICIENT_CRYSTALS"


@pytest.mark.asyncio
async def test_create_generation_insert_fail_returns_500():
    """500 CREATE_FAILED when generation insert returns empty data."""
    db = _make_chain(
        _r(data=_ACTIVE_TWIN),
        _r(data=[], count=0),
        _r(data=[]),  # insert fails
    )
    resp = await _call("post", "/api/brandedby/generations", db=db, json=_GEN_BODY)

    assert resp.status_code == 500
    assert resp.json()["detail"]["code"] == "CREATE_FAILED"


@pytest.mark.asyncio
async def test_create_generation_short_text_returns_422():
    """422 when input_text is fewer than 3 words (schema validator)."""
    body = {**_GEN_BODY, "input_text": "hi"}
    db = _make_chain(_r(data=_ACTIVE_TWIN))
    resp = await _call("post", "/api/brandedby/generations", db=db, json=body)

    assert resp.status_code == 422


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/brandedby/generations
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_list_generations_happy_path():
    """200 with list of generations."""
    rows = [_gen_row(), _gen_row(id=str(uuid.uuid4()), status="completed")]
    db = _make_chain(_r(data=rows))
    resp = await _call("get", "/api/brandedby/generations", db=db)

    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) == 2


@pytest.mark.asyncio
async def test_list_generations_no_auth_returns_401():
    """No Authorization header → 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/brandedby/generations")

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_generations_empty():
    """200 with empty list when user has no generations."""
    db = _make_chain(_r(data=[]))
    resp = await _call("get", "/api/brandedby/generations", db=db)

    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_generations_pagination_params():
    """Query params limit and offset are accepted (no 422)."""
    db = _make_chain(_r(data=[]))
    resp = await _call("get", "/api/brandedby/generations?limit=5&offset=10", db=db)

    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_list_generations_limit_too_large_returns_422():
    """422 when limit exceeds max allowed (100)."""
    db = _make_chain(_r(data=[]))
    resp = await _call("get", "/api/brandedby/generations?limit=999", db=db)

    assert resp.status_code == 422


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/brandedby/generations/{gen_id}
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_get_generation_happy_path():
    """200 with GenerationOut body."""
    db = _make_chain(_r(data=_gen_row()))
    resp = await _call("get", f"/api/brandedby/generations/{GEN_ID}", db=db)

    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == GEN_ID
    assert body["status"] == "queued"


@pytest.mark.asyncio
async def test_get_generation_no_auth_returns_401():
    """No Authorization header → 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/brandedby/generations/{GEN_ID}")

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_generation_not_found_returns_404():
    """404 GENERATION_NOT_FOUND when no row returned."""
    db = _make_chain(_r(data=None))
    resp = await _call("get", f"/api/brandedby/generations/{GEN_ID}", db=db)

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "GENERATION_NOT_FOUND"


@pytest.mark.asyncio
async def test_get_generation_wrong_user_returns_404():
    """404 when generation belongs to a different user (RLS-equivalent)."""
    # endpoint queries eq("user_id", user_id) — wrong user → DB returns None
    db = _make_chain(_r(data=None))
    resp = await _call("get", f"/api/brandedby/generations/{GEN_ID}", db=db, uid=OTHER_USER_ID)

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_generation_completed_fields():
    """Completed generation includes output_url and duration_seconds."""
    row = _gen_row(
        status="completed",
        output_url="https://cdn.example.com/video.mp4",
        duration_seconds=45,
        completed_at=NOW,
    )
    db = _make_chain(_r(data=row))
    resp = await _call("get", f"/api/brandedby/generations/{GEN_ID}", db=db)

    assert resp.status_code == 200
    body = resp.json()
    assert body["output_url"] == "https://cdn.example.com/video.mp4"
    assert body["duration_seconds"] == 45


@pytest.mark.asyncio
async def test_get_generation_failed_includes_error_message():
    """Failed generation includes error_message field."""
    row = _gen_row(status="failed", error_message="Model timeout")
    db = _make_chain(_r(data=row))
    resp = await _call("get", f"/api/brandedby/generations/{GEN_ID}", db=db)

    assert resp.status_code == 200
    assert resp.json()["error_message"] == "Model timeout"
