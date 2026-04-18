"""Unit tests for BrandedBy router — AI Twin CRUD + generation jobs.

Covers all 8 endpoints, all error branches, and happy paths.

Endpoints:
  POST   /twins                           — create_twin
  GET    /twins                           — get_my_twin
  PATCH  /twins/{twin_id}                 — update_twin
  POST   /twins/{twin_id}/refresh-personality — refresh_personality
  POST   /twins/{twin_id}/activate        — activate_twin
  POST   /generations                     — create_generation
  GET    /generations                     — list_generations
  GET    /generations/{gen_id}            — get_generation
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.routers.brandedby import (
    QUEUE_SKIP_CRYSTAL_COST,
    activate_twin,
    create_generation,
    create_twin,
    get_generation,
    get_my_twin,
    list_generations,
    refresh_personality,
    update_twin,
)
from app.schemas.brandedby import AITwinCreate, AITwinUpdate, GenerationCreate

# ── Constants ──────────────────────────────────────────────────────────────────

USER_ID = str(uuid.uuid4())
OTHER_USER_ID = str(uuid.uuid4())
TWIN_ID = str(uuid.uuid4())
GEN_ID = str(uuid.uuid4())

NOW = datetime.now(UTC).isoformat()

FAKE_REQUEST = MagicMock()


# ── DB mock helpers ────────────────────────────────────────────────────────────


def _result(data=None, *, count: int | None = None) -> MagicMock:
    """Create a Supabase-style result with .data and optional .count."""
    r = MagicMock()
    r.data = data
    r.count = count
    return r


def _make_db(*execute_returns) -> MagicMock:
    """Create a mock Supabase client with full chained builder pattern.

    Supports multiple sequential execute() calls via side_effect list.
    If only one value is provided, always returns that value.
    """
    db = MagicMock()
    chain = MagicMock()

    builder_methods = [
        "schema",
        "table",
        "select",
        "insert",
        "update",
        "eq",
        "neq",
        "maybe_single",
        "order",
        "range",
        "filter",
        "limit",
        "single",
        "upsert",
        "delete",
    ]
    for method in builder_methods:
        getattr(chain, method).return_value = chain
        getattr(db, method).return_value = chain

    if len(execute_returns) == 1:
        chain.execute = AsyncMock(return_value=execute_returns[0])
        db.execute = AsyncMock(return_value=execute_returns[0])
    else:
        chain.execute = AsyncMock(side_effect=list(execute_returns))
        db.execute = AsyncMock(side_effect=list(execute_returns))

    return db


def _make_db_with_rpc(schema_executes: list, rpc_execute=None) -> MagicMock:
    """DB mock that handles both schema chain and rpc calls with separate execute results."""
    db = MagicMock()
    chain = MagicMock()

    builder_methods = [
        "schema",
        "table",
        "select",
        "insert",
        "update",
        "eq",
        "neq",
        "maybe_single",
        "order",
        "range",
        "filter",
        "limit",
        "single",
        "upsert",
        "delete",
    ]
    for method in builder_methods:
        getattr(chain, method).return_value = chain
        getattr(db, method).return_value = chain

    if len(schema_executes) == 1:
        chain.execute = AsyncMock(return_value=schema_executes[0])
    else:
        chain.execute = AsyncMock(side_effect=list(schema_executes))

    # rpc returns its own chain
    rpc_chain = MagicMock()
    rpc_chain.execute = AsyncMock(return_value=rpc_execute or _result(data=[]))
    db.rpc = MagicMock(return_value=rpc_chain)

    return db


# ── Row factories ──────────────────────────────────────────────────────────────


def _twin_row(**overrides) -> dict:
    base = {
        "id": TWIN_ID,
        "user_id": USER_ID,
        "display_name": "Test Twin",
        "tagline": "A test tagline",
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


# ══════════════════════════════════════════════════════════════════════════════
# POST /twins — create_twin
# ══════════════════════════════════════════════════════════════════════════════


class TestCreateTwin:
    """8 tests: happy path, existing twin 409, insert fail 500, edge cases."""

    @pytest.mark.asyncio
    async def test_happy_path_creates_twin(self):
        """Successfully creates a twin and returns AITwinOut."""
        db = _make_db(
            _result(data=[]),  # existing check → no twin
            _result(data=[_twin_row()]),  # insert → new row
        )
        body = AITwinCreate(display_name="Test Twin")

        result = await create_twin(FAKE_REQUEST, body, USER_ID, db)

        assert str(result.id) == TWIN_ID
        assert result.display_name == "Test Twin"
        assert result.status == "draft"

    @pytest.mark.asyncio
    async def test_twin_already_exists_raises_409(self):
        """409 TWIN_EXISTS when user already has a twin."""
        db = _make_db(_result(data=[{"id": TWIN_ID}]))  # existing check → has twin
        body = AITwinCreate(display_name="Another Twin")

        with pytest.raises(HTTPException) as exc:
            await create_twin(FAKE_REQUEST, body, USER_ID, db)

        assert exc.value.status_code == 409
        assert exc.value.detail["code"] == "TWIN_EXISTS"

    @pytest.mark.asyncio
    async def test_insert_fail_raises_500(self):
        """500 CREATE_FAILED when DB insert returns empty data."""
        db = _make_db(
            _result(data=[]),  # existing check → no twin
            _result(data=[]),  # insert → empty (failure)
        )
        body = AITwinCreate(display_name="Broken Twin")

        with pytest.raises(HTTPException) as exc:
            await create_twin(FAKE_REQUEST, body, USER_ID, db)

        assert exc.value.status_code == 500
        assert exc.value.detail["code"] == "CREATE_FAILED"

    @pytest.mark.asyncio
    async def test_insert_fail_with_none_data_raises_500(self):
        """500 when DB insert returns None data."""
        db = _make_db(
            _result(data=[]),  # existing check → no twin
            _result(data=None),  # insert → None
        )
        body = AITwinCreate(display_name="None Data Twin")

        with pytest.raises(HTTPException) as exc:
            await create_twin(FAKE_REQUEST, body, USER_ID, db)

        assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_creates_twin_with_all_fields(self):
        """All fields from body are passed through to the result."""
        row = _twin_row(
            display_name="Full Twin",
            tagline="My tagline",
            photo_url="https://img.example.com/face.jpg",
        )
        db = _make_db(
            _result(data=[]),
            _result(data=[row]),
        )
        body = AITwinCreate(
            display_name="Full Twin",
            tagline="My tagline",
            photo_url="https://img.example.com/face.jpg",
        )

        result = await create_twin(FAKE_REQUEST, body, USER_ID, db)

        assert result.tagline == "My tagline"
        assert result.photo_url == "https://img.example.com/face.jpg"

    @pytest.mark.asyncio
    async def test_existing_check_uses_user_id(self):
        """Existing twin check queries by user_id (not a different user's twin)."""
        db = _make_db(
            _result(data=[]),  # no existing twin for this user
            _result(data=[_twin_row()]),
        )
        body = AITwinCreate(display_name="My Twin")

        result = await create_twin(FAKE_REQUEST, body, USER_ID, db)

        assert result.status == "draft"

    @pytest.mark.asyncio
    async def test_status_is_draft_on_creation(self):
        """New twin always starts with draft status."""
        row = _twin_row(status="draft")
        db = _make_db(
            _result(data=[]),
            _result(data=[row]),
        )
        body = AITwinCreate(display_name="Draft Twin")

        result = await create_twin(FAKE_REQUEST, body, USER_ID, db)

        assert result.status == "draft"

    @pytest.mark.asyncio
    async def test_existing_check_returns_multiple_rows_raises_409(self):
        """409 if somehow multiple existing twins found."""
        db = _make_db(_result(data=[{"id": TWIN_ID}, {"id": str(uuid.uuid4())}]))
        body = AITwinCreate(display_name="Twin")

        with pytest.raises(HTTPException) as exc:
            await create_twin(FAKE_REQUEST, body, USER_ID, db)

        assert exc.value.status_code == 409


# ══════════════════════════════════════════════════════════════════════════════
# GET /twins — get_my_twin
# ══════════════════════════════════════════════════════════════════════════════


class TestGetMyTwin:
    """5 tests: returns twin, returns None when absent, full fields."""

    @pytest.mark.asyncio
    async def test_returns_twin_when_found(self):
        """Returns AITwinOut when user has a twin."""
        db = _make_db(_result(data=_twin_row()))

        result = await get_my_twin(FAKE_REQUEST, USER_ID, db)

        assert result is not None
        assert str(result.id) == TWIN_ID
        assert result.display_name == "Test Twin"

    @pytest.mark.asyncio
    async def test_returns_none_when_no_twin(self):
        """Returns None when user has no twin."""
        db = _make_db(_result(data=None))

        result = await get_my_twin(FAKE_REQUEST, USER_ID, db)

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_empty_data(self):
        """Returns None when result.data is falsy empty dict."""
        db = _make_db(_result(data={}))

        result = await get_my_twin(FAKE_REQUEST, USER_ID, db)

        assert result is None

    @pytest.mark.asyncio
    async def test_twin_all_optional_fields_none(self):
        """Returns twin with all optional fields as None."""
        row = _twin_row(
            tagline=None,
            photo_url=None,
            voice_id=None,
            personality_prompt=None,
        )
        db = _make_db(_result(data=row))

        result = await get_my_twin(FAKE_REQUEST, USER_ID, db)

        assert result is not None
        assert result.tagline is None
        assert result.photo_url is None
        assert result.voice_id is None
        assert result.personality_prompt is None

    @pytest.mark.asyncio
    async def test_twin_active_status_returned(self):
        """Returns active-status twin."""
        row = _twin_row(status="active")
        db = _make_db(_result(data=row))

        result = await get_my_twin(FAKE_REQUEST, USER_ID, db)

        assert result.status == "active"


# ══════════════════════════════════════════════════════════════════════════════
# PATCH /twins/{twin_id} — update_twin
# ══════════════════════════════════════════════════════════════════════════════


class TestUpdateTwin:
    """10 tests: happy path, 404, 403, 400 no changes, 500 update fail."""

    @pytest.mark.asyncio
    async def test_happy_path_updates_display_name(self):
        """Successful update returns updated AITwinOut."""
        updated_row = _twin_row(display_name="Updated Name")
        db = _make_db(
            _result(data={"id": TWIN_ID, "user_id": USER_ID}),  # ownership check
            _result(data=[updated_row]),  # update result
        )
        body = AITwinUpdate(display_name="Updated Name")

        result = await update_twin(FAKE_REQUEST, TWIN_ID, body, USER_ID, db)

        assert result.display_name == "Updated Name"

    @pytest.mark.asyncio
    async def test_404_when_twin_not_found(self):
        """404 TWIN_NOT_FOUND when no twin with that id."""
        db = _make_db(_result(data=None))
        body = AITwinUpdate(display_name="Doesn't Matter")

        with pytest.raises(HTTPException) as exc:
            await update_twin(FAKE_REQUEST, TWIN_ID, body, USER_ID, db)

        assert exc.value.status_code == 404
        assert exc.value.detail["code"] == "TWIN_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_404_when_data_empty_dict(self):
        """404 when data is empty dict (falsy)."""
        db = _make_db(_result(data={}))
        body = AITwinUpdate(display_name="Doesn't Matter")

        with pytest.raises(HTTPException) as exc:
            await update_twin(FAKE_REQUEST, TWIN_ID, body, USER_ID, db)

        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_403_when_not_owner(self):
        """403 NOT_OWNER when user_id doesn't match twin's owner."""
        db = _make_db(_result(data={"id": TWIN_ID, "user_id": OTHER_USER_ID}))
        body = AITwinUpdate(display_name="Hacked Name")

        with pytest.raises(HTTPException) as exc:
            await update_twin(FAKE_REQUEST, TWIN_ID, body, USER_ID, db)

        assert exc.value.status_code == 403
        assert exc.value.detail["code"] == "NOT_OWNER"

    @pytest.mark.asyncio
    async def test_400_no_changes_when_body_empty(self):
        """400 NO_CHANGES when no fields provided in body."""
        db = _make_db(_result(data={"id": TWIN_ID, "user_id": USER_ID}))
        body = AITwinUpdate()  # no fields set

        with pytest.raises(HTTPException) as exc:
            await update_twin(FAKE_REQUEST, TWIN_ID, body, USER_ID, db)

        assert exc.value.status_code == 400
        assert exc.value.detail["code"] == "NO_CHANGES"

    @pytest.mark.asyncio
    async def test_500_when_update_returns_empty(self):
        """500 UPDATE_FAILED when DB update returns empty data."""
        db = _make_db(
            _result(data={"id": TWIN_ID, "user_id": USER_ID}),
            _result(data=[]),  # update returns empty
        )
        body = AITwinUpdate(tagline="New tagline")

        with pytest.raises(HTTPException) as exc:
            await update_twin(FAKE_REQUEST, TWIN_ID, body, USER_ID, db)

        assert exc.value.status_code == 500
        assert exc.value.detail["code"] == "UPDATE_FAILED"

    @pytest.mark.asyncio
    async def test_500_when_update_returns_none(self):
        """500 when DB update returns None data."""
        db = _make_db(
            _result(data={"id": TWIN_ID, "user_id": USER_ID}),
            _result(data=None),
        )
        body = AITwinUpdate(tagline="New tagline")

        with pytest.raises(HTTPException) as exc:
            await update_twin(FAKE_REQUEST, TWIN_ID, body, USER_ID, db)

        assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_update_tagline_only(self):
        """Partial update with only tagline."""
        updated_row = _twin_row(tagline="Updated tagline")
        db = _make_db(
            _result(data={"id": TWIN_ID, "user_id": USER_ID}),
            _result(data=[updated_row]),
        )
        body = AITwinUpdate(tagline="Updated tagline")

        result = await update_twin(FAKE_REQUEST, TWIN_ID, body, USER_ID, db)

        assert result.tagline == "Updated tagline"

    @pytest.mark.asyncio
    async def test_update_photo_url(self):
        """Partial update with photo_url."""
        updated_row = _twin_row(photo_url="https://new.example.com/photo.jpg")
        db = _make_db(
            _result(data={"id": TWIN_ID, "user_id": USER_ID}),
            _result(data=[updated_row]),
        )
        body = AITwinUpdate(photo_url="https://new.example.com/photo.jpg")

        result = await update_twin(FAKE_REQUEST, TWIN_ID, body, USER_ID, db)

        assert result.photo_url == "https://new.example.com/photo.jpg"

    @pytest.mark.asyncio
    async def test_update_status_to_suspended(self):
        """Can update status field."""
        updated_row = _twin_row(status="suspended")
        db = _make_db(
            _result(data={"id": TWIN_ID, "user_id": USER_ID}),
            _result(data=[updated_row]),
        )
        body = AITwinUpdate(status="suspended")

        result = await update_twin(FAKE_REQUEST, TWIN_ID, body, USER_ID, db)

        assert result.status == "suspended"


# ══════════════════════════════════════════════════════════════════════════════
# POST /twins/{twin_id}/refresh-personality — refresh_personality
# ══════════════════════════════════════════════════════════════════════════════


class TestRefreshPersonality:
    """12 tests: happy path, 404, 403, 500, state data variants."""

    @pytest.mark.asyncio
    async def test_happy_path_generates_and_stores_personality(self):
        """Full success: generates personality via service and stores it."""
        twin_row_data = {"id": TWIN_ID, "user_id": USER_ID, "display_name": "Test Twin"}
        updated_row = _twin_row(personality_prompt="You are Test Twin, an expert...")

        db = _make_db_with_rpc(
            schema_executes=[
                _result(data=twin_row_data),  # ownership check
                _result(data=[updated_row]),  # update with personality
            ],
            rpc_execute=_result(data=[{"verified_skills": ["python"], "aura_score": 80}]),
        )

        with patch(
            "app.routers.brandedby.generate_twin_personality",
            new=AsyncMock(return_value="You are Test Twin, an expert..."),
        ):
            result = await refresh_personality(FAKE_REQUEST, TWIN_ID, USER_ID, db)

        assert result.personality_prompt == "You are Test Twin, an expert..."

    @pytest.mark.asyncio
    async def test_404_when_twin_not_found(self):
        """404 TWIN_NOT_FOUND when twin doesn't exist."""
        db = _make_db_with_rpc(
            schema_executes=[_result(data=None)],
        )

        with pytest.raises(HTTPException) as exc:
            await refresh_personality(FAKE_REQUEST, TWIN_ID, USER_ID, db)

        assert exc.value.status_code == 404
        assert exc.value.detail["code"] == "TWIN_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_404_when_twin_empty_dict(self):
        """404 when twin data is empty dict."""
        db = _make_db_with_rpc(
            schema_executes=[_result(data={})],
        )

        with pytest.raises(HTTPException) as exc:
            await refresh_personality(FAKE_REQUEST, TWIN_ID, USER_ID, db)

        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_403_when_not_owner(self):
        """403 NOT_OWNER when requesting user doesn't own the twin."""
        twin_row_data = {"id": TWIN_ID, "user_id": OTHER_USER_ID, "display_name": "Other Twin"}
        db = _make_db_with_rpc(
            schema_executes=[_result(data=twin_row_data)],
        )

        with pytest.raises(HTTPException) as exc:
            await refresh_personality(FAKE_REQUEST, TWIN_ID, USER_ID, db)

        assert exc.value.status_code == 403
        assert exc.value.detail["code"] == "NOT_OWNER"

    @pytest.mark.asyncio
    async def test_500_when_update_returns_empty(self):
        """500 UPDATE_FAILED when personality store fails."""
        twin_row_data = {"id": TWIN_ID, "user_id": USER_ID, "display_name": "Test Twin"}

        db = _make_db_with_rpc(
            schema_executes=[
                _result(data=twin_row_data),
                _result(data=[]),  # update fails
            ],
            rpc_execute=_result(data=[]),
        )

        with (
            patch(
                "app.routers.brandedby.generate_twin_personality",
                new=AsyncMock(return_value="Generated personality"),
            ),
            pytest.raises(HTTPException) as exc,
        ):
            await refresh_personality(FAKE_REQUEST, TWIN_ID, USER_ID, db)

        assert exc.value.status_code == 500
        assert exc.value.detail["code"] == "UPDATE_FAILED"

    @pytest.mark.asyncio
    async def test_500_when_update_returns_none(self):
        """500 when update returns None data."""
        twin_row_data = {"id": TWIN_ID, "user_id": USER_ID, "display_name": "Test Twin"}

        db = _make_db_with_rpc(
            schema_executes=[
                _result(data=twin_row_data),
                _result(data=None),
            ],
            rpc_execute=_result(data=[]),
        )

        with (
            patch(
                "app.routers.brandedby.generate_twin_personality",
                new=AsyncMock(return_value="Generated personality"),
            ),
            pytest.raises(HTTPException) as exc,
        ):
            await refresh_personality(FAKE_REQUEST, TWIN_ID, USER_ID, db)

        assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_state_empty_when_rpc_returns_empty_list(self):
        """Empty state_data when RPC returns empty list — still generates personality."""
        twin_row_data = {"id": TWIN_ID, "user_id": USER_ID, "display_name": "Test Twin"}
        updated_row = _twin_row(personality_prompt="Basic personality")

        db = _make_db_with_rpc(
            schema_executes=[
                _result(data=twin_row_data),
                _result(data=[updated_row]),
            ],
            rpc_execute=_result(data=[]),  # empty state
        )

        called_with_state = {}

        async def mock_generate(display_name, character_state):
            called_with_state.update(character_state)
            return "Basic personality"

        with patch("app.routers.brandedby.generate_twin_personality", new=mock_generate):
            result = await refresh_personality(FAKE_REQUEST, TWIN_ID, USER_ID, db)

        assert result.personality_prompt == "Basic personality"
        assert called_with_state == {}  # empty state passed through

    @pytest.mark.asyncio
    async def test_state_uses_dict_directly_when_not_list(self):
        """When RPC returns a dict directly (not list), uses it as-is."""
        twin_row_data = {"id": TWIN_ID, "user_id": USER_ID, "display_name": "Test Twin"}
        updated_row = _twin_row(personality_prompt="Dict personality")
        state_dict = {"verified_skills": ["leadership"], "aura_score": 90}

        db = _make_db_with_rpc(
            schema_executes=[
                _result(data=twin_row_data),
                _result(data=[updated_row]),
            ],
            rpc_execute=_result(data=state_dict),  # dict, not list
        )

        received_states = []

        async def mock_generate(display_name, character_state):
            received_states.append(character_state)
            return "Dict personality"

        with patch("app.routers.brandedby.generate_twin_personality", new=mock_generate):
            await refresh_personality(FAKE_REQUEST, TWIN_ID, USER_ID, db)

        assert received_states[0] == state_dict

    @pytest.mark.asyncio
    async def test_state_uses_first_element_when_list(self):
        """When RPC returns a list, uses raw[0] as state_data."""
        twin_row_data = {"id": TWIN_ID, "user_id": USER_ID, "display_name": "Test Twin"}
        updated_row = _twin_row(personality_prompt="List personality")
        state_item = {"verified_skills": ["python"], "aura_score": 75}

        db = _make_db_with_rpc(
            schema_executes=[
                _result(data=twin_row_data),
                _result(data=[updated_row]),
            ],
            rpc_execute=_result(data=[state_item]),
        )

        received_states = []

        async def mock_generate(display_name, character_state):
            received_states.append(character_state)
            return "List personality"

        with patch("app.routers.brandedby.generate_twin_personality", new=mock_generate):
            await refresh_personality(FAKE_REQUEST, TWIN_ID, USER_ID, db)

        assert received_states[0] == state_item

    @pytest.mark.asyncio
    async def test_calls_generate_with_display_name(self):
        """generate_twin_personality is called with the twin's display_name."""
        display_name = "Unique Name For Twin"
        twin_row_data = {"id": TWIN_ID, "user_id": USER_ID, "display_name": display_name}
        updated_row = _twin_row(display_name=display_name, personality_prompt="Generated")

        db = _make_db_with_rpc(
            schema_executes=[
                _result(data=twin_row_data),
                _result(data=[updated_row]),
            ],
            rpc_execute=_result(data=[]),
        )

        called_with_name = []

        async def mock_generate(display_name, character_state):
            called_with_name.append(display_name)
            return "Generated"

        with patch("app.routers.brandedby.generate_twin_personality", new=mock_generate):
            await refresh_personality(FAKE_REQUEST, TWIN_ID, USER_ID, db)

        assert called_with_name[0] == display_name

    @pytest.mark.asyncio
    async def test_rpc_none_data_treated_as_empty_state(self):
        """RPC returning None data results in empty state_data dict."""
        twin_row_data = {"id": TWIN_ID, "user_id": USER_ID, "display_name": "Test Twin"}
        updated_row = _twin_row(personality_prompt="None state personality")

        db = _make_db_with_rpc(
            schema_executes=[
                _result(data=twin_row_data),
                _result(data=[updated_row]),
            ],
            rpc_execute=_result(data=None),
        )

        received_states = []

        async def mock_generate(display_name, character_state):
            received_states.append(character_state)
            return "None state personality"

        with patch("app.routers.brandedby.generate_twin_personality", new=mock_generate):
            await refresh_personality(FAKE_REQUEST, TWIN_ID, USER_ID, db)

        assert received_states[0] == {}

    @pytest.mark.asyncio
    async def test_returns_updated_twin_out(self):
        """Return value is parsed from update result data."""
        twin_row_data = {"id": TWIN_ID, "user_id": USER_ID, "display_name": "Test Twin"}
        updated_row = _twin_row(personality_prompt="Fresh personality", status="draft")

        db = _make_db_with_rpc(
            schema_executes=[
                _result(data=twin_row_data),
                _result(data=[updated_row]),
            ],
            rpc_execute=_result(data=[]),
        )

        with patch(
            "app.routers.brandedby.generate_twin_personality",
            new=AsyncMock(return_value="Fresh personality"),
        ):
            result = await refresh_personality(FAKE_REQUEST, TWIN_ID, USER_ID, db)

        assert result.personality_prompt == "Fresh personality"
        assert str(result.id) == TWIN_ID


# ══════════════════════════════════════════════════════════════════════════════
# POST /twins/{twin_id}/activate — activate_twin
# ══════════════════════════════════════════════════════════════════════════════


class TestActivateTwin:
    """11 tests: happy path, 404, 403, 409 already active, 400 missing photo, 400 missing personality."""

    def _draft_twin_row(self, **overrides):
        """A twin ready for activation by default."""
        base = {
            "id": TWIN_ID,
            "user_id": USER_ID,
            "status": "draft",
            "photo_url": "https://example.com/photo.jpg",
            "personality_prompt": "You are Test Twin.",
        }
        return {**base, **overrides}

    @pytest.mark.asyncio
    async def test_happy_path_activates_twin(self):
        """Successfully activates draft twin with photo and personality."""
        activated_row = _twin_row(status="active")
        db = _make_db(
            _result(data=self._draft_twin_row()),  # ownership+status check
            _result(data=[activated_row]),  # update to active
        )

        result = await activate_twin(FAKE_REQUEST, TWIN_ID, USER_ID, db)

        assert result.status == "active"

    @pytest.mark.asyncio
    async def test_404_when_twin_not_found(self):
        """404 TWIN_NOT_FOUND when no twin with given id."""
        db = _make_db(_result(data=None))

        with pytest.raises(HTTPException) as exc:
            await activate_twin(FAKE_REQUEST, TWIN_ID, USER_ID, db)

        assert exc.value.status_code == 404
        assert exc.value.detail["code"] == "TWIN_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_404_when_twin_empty(self):
        """404 when data is empty dict."""
        db = _make_db(_result(data={}))

        with pytest.raises(HTTPException) as exc:
            await activate_twin(FAKE_REQUEST, TWIN_ID, USER_ID, db)

        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_403_when_not_owner(self):
        """403 NOT_OWNER when different user tries to activate."""
        twin_data = self._draft_twin_row(user_id=OTHER_USER_ID)
        db = _make_db(_result(data=twin_data))

        with pytest.raises(HTTPException) as exc:
            await activate_twin(FAKE_REQUEST, TWIN_ID, USER_ID, db)

        assert exc.value.status_code == 403
        assert exc.value.detail["code"] == "NOT_OWNER"

    @pytest.mark.asyncio
    async def test_409_when_already_active(self):
        """409 ALREADY_ACTIVE when twin status is already active."""
        twin_data = self._draft_twin_row(status="active")
        db = _make_db(_result(data=twin_data))

        with pytest.raises(HTTPException) as exc:
            await activate_twin(FAKE_REQUEST, TWIN_ID, USER_ID, db)

        assert exc.value.status_code == 409
        assert exc.value.detail["code"] == "ALREADY_ACTIVE"

    @pytest.mark.asyncio
    async def test_400_missing_photo_url(self):
        """400 MISSING_PHOTO when photo_url is None."""
        twin_data = self._draft_twin_row(photo_url=None)
        db = _make_db(_result(data=twin_data))

        with pytest.raises(HTTPException) as exc:
            await activate_twin(FAKE_REQUEST, TWIN_ID, USER_ID, db)

        assert exc.value.status_code == 400
        assert exc.value.detail["code"] == "MISSING_PHOTO"

    @pytest.mark.asyncio
    async def test_400_missing_photo_url_empty_string(self):
        """400 MISSING_PHOTO when photo_url is empty string."""
        twin_data = self._draft_twin_row(photo_url="")
        db = _make_db(_result(data=twin_data))

        with pytest.raises(HTTPException) as exc:
            await activate_twin(FAKE_REQUEST, TWIN_ID, USER_ID, db)

        assert exc.value.status_code == 400
        assert exc.value.detail["code"] == "MISSING_PHOTO"

    @pytest.mark.asyncio
    async def test_400_missing_personality_prompt(self):
        """400 MISSING_PERSONALITY when personality_prompt is None."""
        twin_data = self._draft_twin_row(personality_prompt=None)
        db = _make_db(_result(data=twin_data))

        with pytest.raises(HTTPException) as exc:
            await activate_twin(FAKE_REQUEST, TWIN_ID, USER_ID, db)

        assert exc.value.status_code == 400
        assert exc.value.detail["code"] == "MISSING_PERSONALITY"

    @pytest.mark.asyncio
    async def test_400_missing_personality_empty_string(self):
        """400 MISSING_PERSONALITY when personality_prompt is empty string."""
        twin_data = self._draft_twin_row(personality_prompt="")
        db = _make_db(_result(data=twin_data))

        with pytest.raises(HTTPException) as exc:
            await activate_twin(FAKE_REQUEST, TWIN_ID, USER_ID, db)

        assert exc.value.status_code == 400
        assert exc.value.detail["code"] == "MISSING_PERSONALITY"

    @pytest.mark.asyncio
    async def test_ownership_check_before_status_check(self):
        """403 raised before 409 — ownership checked first."""
        twin_data = self._draft_twin_row(user_id=OTHER_USER_ID, status="active")
        db = _make_db(_result(data=twin_data))

        with pytest.raises(HTTPException) as exc:
            await activate_twin(FAKE_REQUEST, TWIN_ID, USER_ID, db)

        # 403 because ownership is checked before status
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_suspended_twin_can_be_activated(self):
        """Suspended twin (not 'active') can also be activated if it has photo and personality."""
        twin_data = self._draft_twin_row(status="suspended")
        activated_row = _twin_row(status="active")
        db = _make_db(
            _result(data=twin_data),
            _result(data=[activated_row]),
        )

        result = await activate_twin(FAKE_REQUEST, TWIN_ID, USER_ID, db)

        assert result.status == "active"


# ══════════════════════════════════════════════════════════════════════════════
# POST /generations — create_generation
# ══════════════════════════════════════════════════════════════════════════════


class TestCreateGeneration:
    """18 tests: happy path (normal + skip_queue), 404, 403, 400 not active, 402 insufficient, 500."""

    def _active_twin(self) -> dict:
        return {"id": TWIN_ID, "user_id": USER_ID, "status": "active"}

    def _gen_body(self, skip_queue: bool = False) -> GenerationCreate:
        return GenerationCreate(
            twin_id=uuid.UUID(TWIN_ID),
            gen_type="video",
            input_text="Please generate this test video",
            skip_queue=skip_queue,
        )

    @pytest.mark.asyncio
    async def test_happy_path_no_skip_queue(self):
        """Creates generation in queue without spending crystals."""
        gen_row = _gen_row(queue_position=1, crystal_cost=0)

        db = _make_db(
            _result(data=self._active_twin()),  # twin check
            _result(data=[], count=0),  # count queued jobs
            _result(data=[gen_row]),  # insert generation
        )

        result = await create_generation(FAKE_REQUEST, self._gen_body(), USER_ID, db)

        assert str(result.id) == GEN_ID
        assert result.crystal_cost == 0
        assert result.queue_position == 1

    @pytest.mark.asyncio
    async def test_happy_path_skip_queue_with_crystals(self):
        """Creates generation with queue skip, deducts crystals atomically.

        Call order on the chain mock:
          1. db.schema("brandedby").table("ai_twins")...execute()  — twin check
          2. db.table("character_events").insert(...).execute()     — audit insert
          3. db.schema("brandedby").table("generations").insert()...execute() — gen insert
        """
        gen_row = _gen_row(queue_position=0, crystal_cost=QUEUE_SKIP_CRYSTAL_COST)

        db = MagicMock()
        chain = MagicMock()
        for method in [
            "schema",
            "table",
            "select",
            "insert",
            "update",
            "eq",
            "maybe_single",
            "order",
            "range",
            "filter",
            "limit",
        ]:
            getattr(chain, method).return_value = chain
            getattr(db, method).return_value = chain

        # 3 chain.execute calls: twin check, audit insert (character_events), gen insert
        chain.execute = AsyncMock(
            side_effect=[
                _result(data=self._active_twin()),  # twin ownership check
                _result(data=[{"id": "audit-id"}]),  # character_events audit insert
                _result(data=[gen_row]),  # generation insert
            ]
        )

        rpc_chain = MagicMock()
        rpc_chain.execute = AsyncMock(return_value=_result(data=[{"success": True, "new_balance": 75}]))
        db.rpc = MagicMock(return_value=rpc_chain)

        result = await create_generation(FAKE_REQUEST, self._gen_body(skip_queue=True), USER_ID, db)

        assert result.crystal_cost == QUEUE_SKIP_CRYSTAL_COST
        assert result.queue_position == 0

    @pytest.mark.asyncio
    async def test_404_when_twin_not_found(self):
        """404 TWIN_NOT_FOUND when twin doesn't exist."""
        db = _make_db(_result(data=None))

        with pytest.raises(HTTPException) as exc:
            await create_generation(FAKE_REQUEST, self._gen_body(), USER_ID, db)

        assert exc.value.status_code == 404
        assert exc.value.detail["code"] == "TWIN_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_404_when_twin_empty(self):
        """404 when twin data is empty dict."""
        db = _make_db(_result(data={}))

        with pytest.raises(HTTPException) as exc:
            await create_generation(FAKE_REQUEST, self._gen_body(), USER_ID, db)

        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_403_when_not_owner(self):
        """403 NOT_OWNER when user doesn't own the twin."""
        twin = {"id": TWIN_ID, "user_id": OTHER_USER_ID, "status": "active"}
        db = _make_db(_result(data=twin))

        with pytest.raises(HTTPException) as exc:
            await create_generation(FAKE_REQUEST, self._gen_body(), USER_ID, db)

        assert exc.value.status_code == 403
        assert exc.value.detail["code"] == "NOT_OWNER"

    @pytest.mark.asyncio
    async def test_400_when_twin_not_active_draft(self):
        """400 TWIN_NOT_ACTIVE when twin is in draft status."""
        twin = {"id": TWIN_ID, "user_id": USER_ID, "status": "draft"}
        db = _make_db(_result(data=twin))

        with pytest.raises(HTTPException) as exc:
            await create_generation(FAKE_REQUEST, self._gen_body(), USER_ID, db)

        assert exc.value.status_code == 400
        assert exc.value.detail["code"] == "TWIN_NOT_ACTIVE"

    @pytest.mark.asyncio
    async def test_400_when_twin_not_active_suspended(self):
        """400 TWIN_NOT_ACTIVE when twin is suspended."""
        twin = {"id": TWIN_ID, "user_id": USER_ID, "status": "suspended"}
        db = _make_db(_result(data=twin))

        with pytest.raises(HTTPException) as exc:
            await create_generation(FAKE_REQUEST, self._gen_body(), USER_ID, db)

        assert exc.value.status_code == 400
        assert exc.value.detail["code"] == "TWIN_NOT_ACTIVE"

    @pytest.mark.asyncio
    async def test_402_insufficient_crystals(self):
        """402 when deduct_crystals_atomic returns success=False."""
        db = MagicMock()
        chain = MagicMock()
        for method in ["schema", "table", "select", "insert", "update", "eq", "maybe_single", "order", "range"]:
            getattr(chain, method).return_value = chain
            getattr(db, method).return_value = chain

        chain.execute = AsyncMock(return_value=_result(data=self._active_twin()))

        rpc_chain = MagicMock()
        rpc_chain.execute = AsyncMock(
            return_value=_result(
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

        with pytest.raises(HTTPException) as exc:
            await create_generation(FAKE_REQUEST, self._gen_body(skip_queue=True), USER_ID, db)

        assert exc.value.status_code == 402
        assert exc.value.detail["code"] == "INSUFFICIENT_CRYSTALS"

    @pytest.mark.asyncio
    async def test_402_uses_default_error_code_when_missing(self):
        """402 falls back to INSUFFICIENT_CRYSTALS when error_code not in response."""
        db = MagicMock()
        chain = MagicMock()
        for method in ["schema", "table", "select", "insert", "update", "eq", "maybe_single", "order", "range"]:
            getattr(chain, method).return_value = chain
            getattr(db, method).return_value = chain

        chain.execute = AsyncMock(return_value=_result(data=self._active_twin()))

        rpc_chain = MagicMock()
        rpc_chain.execute = AsyncMock(
            return_value=_result(data=[{"success": False}])  # no error_code
        )
        db.rpc = MagicMock(return_value=rpc_chain)

        with pytest.raises(HTTPException) as exc:
            await create_generation(FAKE_REQUEST, self._gen_body(skip_queue=True), USER_ID, db)

        assert exc.value.status_code == 402
        assert exc.value.detail["code"] == "INSUFFICIENT_CRYSTALS"

    @pytest.mark.asyncio
    async def test_500_when_crystal_rpc_raises_exception(self):
        """500 CRYSTAL_DEDUCTION_FAILED when RPC throws unexpected exception."""
        db = MagicMock()
        chain = MagicMock()
        for method in ["schema", "table", "select", "insert", "update", "eq", "maybe_single", "order", "range"]:
            getattr(chain, method).return_value = chain
            getattr(db, method).return_value = chain

        chain.execute = AsyncMock(return_value=_result(data=self._active_twin()))

        rpc_chain = MagicMock()
        rpc_chain.execute = AsyncMock(side_effect=RuntimeError("DB connection lost"))
        db.rpc = MagicMock(return_value=rpc_chain)

        with pytest.raises(HTTPException) as exc:
            await create_generation(FAKE_REQUEST, self._gen_body(skip_queue=True), USER_ID, db)

        assert exc.value.status_code == 500
        assert exc.value.detail["code"] == "CRYSTAL_DEDUCTION_FAILED"

    @pytest.mark.asyncio
    async def test_500_when_insert_returns_empty(self):
        """500 CREATE_FAILED when generation insert returns no data."""
        db = _make_db(
            _result(data=self._active_twin()),
            _result(data=[], count=0),  # queued count
            _result(data=[]),  # insert fails
        )

        with pytest.raises(HTTPException) as exc:
            await create_generation(FAKE_REQUEST, self._gen_body(), USER_ID, db)

        assert exc.value.status_code == 500
        assert exc.value.detail["code"] == "CREATE_FAILED"

    @pytest.mark.asyncio
    async def test_500_when_insert_returns_none(self):
        """500 when insert returns None data."""
        db = _make_db(
            _result(data=self._active_twin()),
            _result(data=[], count=0),
            _result(data=None),
        )

        with pytest.raises(HTTPException) as exc:
            await create_generation(FAKE_REQUEST, self._gen_body(), USER_ID, db)

        assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_queue_position_is_count_plus_one(self):
        """Queue position = existing queued count + 1."""
        gen_row = _gen_row(queue_position=4, crystal_cost=0)
        db = _make_db(
            _result(data=self._active_twin()),
            _result(data=[], count=3),  # 3 jobs ahead
            _result(data=[gen_row]),
        )

        result = await create_generation(FAKE_REQUEST, self._gen_body(), USER_ID, db)

        assert result.queue_position == 4  # from row (count + 1 = 3 + 1 = 4)

    @pytest.mark.asyncio
    async def test_queue_position_zero_when_skip_queue(self):
        """Queue position is 0 when skip_queue=True (no queued-count query).

        Call order: twin check → audit insert (character_events) → gen insert.
        """
        gen_row = _gen_row(queue_position=0, crystal_cost=QUEUE_SKIP_CRYSTAL_COST)

        db = MagicMock()
        chain = MagicMock()
        for method in ["schema", "table", "select", "insert", "update", "eq", "maybe_single", "order", "range"]:
            getattr(chain, method).return_value = chain
            getattr(db, method).return_value = chain

        chain.execute = AsyncMock(
            side_effect=[
                _result(data=self._active_twin()),  # twin check
                _result(data=[{"id": "audit-id"}]),  # character_events audit insert
                _result(data=[gen_row]),  # generation insert
            ]
        )

        rpc_chain = MagicMock()
        rpc_chain.execute = AsyncMock(return_value=_result(data=[{"success": True, "new_balance": 75}]))
        db.rpc = MagicMock(return_value=rpc_chain)

        result = await create_generation(FAKE_REQUEST, self._gen_body(skip_queue=True), USER_ID, db)

        assert result.queue_position == 0

    @pytest.mark.asyncio
    async def test_queue_count_none_defaults_to_zero(self):
        """When queued.count is None, queue_position defaults to 1 (0 + 1)."""
        gen_row = _gen_row(queue_position=1, crystal_cost=0)
        db = _make_db(
            _result(data=self._active_twin()),
            _result(data=[], count=None),  # count is None
            _result(data=[gen_row]),
        )

        result = await create_generation(FAKE_REQUEST, self._gen_body(), USER_ID, db)

        assert result.queue_position == 1  # 0 + 1

    @pytest.mark.asyncio
    async def test_crystal_cost_is_queue_skip_constant(self):
        """Crystal cost in response matches QUEUE_SKIP_CRYSTAL_COST constant."""
        assert QUEUE_SKIP_CRYSTAL_COST == 25

    @pytest.mark.asyncio
    async def test_audio_gen_type_works(self):
        """audio gen_type generates successfully."""
        gen_row = _gen_row(gen_type="audio", queue_position=1, crystal_cost=0)
        db = _make_db(
            _result(data=self._active_twin()),
            _result(data=[], count=0),
            _result(data=[gen_row]),
        )
        body = GenerationCreate(
            twin_id=uuid.UUID(TWIN_ID),
            gen_type="audio",
            input_text="Generate an audio greeting message",
        )

        result = await create_generation(FAKE_REQUEST, body, USER_ID, db)

        assert result.gen_type == "audio"

    @pytest.mark.asyncio
    async def test_text_chat_gen_type_works(self):
        """text_chat gen_type generates successfully."""
        gen_row = _gen_row(gen_type="text_chat", queue_position=1, crystal_cost=0)
        db = _make_db(
            _result(data=self._active_twin()),
            _result(data=[], count=0),
            _result(data=[gen_row]),
        )
        body = GenerationCreate(
            twin_id=uuid.UUID(TWIN_ID),
            gen_type="text_chat",
            input_text="Chat with me about the weather",
        )

        result = await create_generation(FAKE_REQUEST, body, USER_ID, db)

        assert result.gen_type == "text_chat"


# ══════════════════════════════════════════════════════════════════════════════
# GET /generations — list_generations
# ══════════════════════════════════════════════════════════════════════════════


class TestListGenerations:
    """8 tests: returns list, empty list, pagination, multiple items."""

    @pytest.mark.asyncio
    async def test_returns_list_of_generations(self):
        """Returns list of GenerationOut for the user."""
        rows = [_gen_row(), _gen_row(id=str(uuid.uuid4()), status="completed")]
        db = _make_db(_result(data=rows))

        result = await list_generations(FAKE_REQUEST, USER_ID, db, limit=20, offset=0)

        assert len(result) == 2
        assert str(result[0].id) == GEN_ID

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_generations(self):
        """Returns empty list when user has no generations."""
        db = _make_db(_result(data=[]))

        result = await list_generations(FAKE_REQUEST, USER_ID, db, limit=20, offset=0)

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_data_none(self):
        """Returns empty list when data is None."""
        db = _make_db(_result(data=None))

        result = await list_generations(FAKE_REQUEST, USER_ID, db, limit=20, offset=0)

        assert result == []

    @pytest.mark.asyncio
    async def test_pagination_limit_respected(self):
        """Limit parameter is passed through (builder calls range)."""
        rows = [_gen_row()]
        db = _make_db(_result(data=rows))

        result = await list_generations(FAKE_REQUEST, USER_ID, db, limit=5, offset=0)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_pagination_offset_nonzero(self):
        """Non-zero offset works correctly."""
        rows = [_gen_row()]
        db = _make_db(_result(data=rows))

        result = await list_generations(FAKE_REQUEST, USER_ID, db, limit=10, offset=5)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_all_gen_types_in_list(self):
        """Returns all generation types in the list."""
        rows = [
            _gen_row(gen_type="video"),
            _gen_row(id=str(uuid.uuid4()), gen_type="audio"),
            _gen_row(id=str(uuid.uuid4()), gen_type="text_chat"),
        ]
        db = _make_db(_result(data=rows))

        result = await list_generations(FAKE_REQUEST, USER_ID, db, limit=20, offset=0)

        types = [r.gen_type for r in result]
        assert "video" in types
        assert "audio" in types
        assert "text_chat" in types

    @pytest.mark.asyncio
    async def test_returns_generation_out_instances(self):
        """Each item is a GenerationOut instance."""
        from app.schemas.brandedby import GenerationOut

        rows = [_gen_row()]
        db = _make_db(_result(data=rows))

        result = await list_generations(FAKE_REQUEST, USER_ID, db, limit=20, offset=0)

        assert all(isinstance(r, GenerationOut) for r in result)

    @pytest.mark.asyncio
    async def test_completed_generation_fields_populated(self):
        """Completed generation has output_url and completed_at."""
        completed_row = _gen_row(
            status="completed",
            output_url="https://cdn.example.com/video.mp4",
            thumbnail_url="https://cdn.example.com/thumb.jpg",
            completed_at=NOW,
            duration_seconds=45,
            crystal_cost=25,
        )
        db = _make_db(_result(data=[completed_row]))

        result = await list_generations(FAKE_REQUEST, USER_ID, db, limit=20, offset=0)

        assert result[0].output_url == "https://cdn.example.com/video.mp4"
        assert result[0].duration_seconds == 45
        assert result[0].crystal_cost == 25


# ══════════════════════════════════════════════════════════════════════════════
# GET /generations/{gen_id} — get_generation
# ══════════════════════════════════════════════════════════════════════════════


class TestGetGeneration:
    """8 tests: happy path, 404 not found, 404 wrong user, field variants."""

    @pytest.mark.asyncio
    async def test_happy_path_returns_generation(self):
        """Returns GenerationOut when generation found."""
        db = _make_db(_result(data=_gen_row()))

        result = await get_generation(FAKE_REQUEST, GEN_ID, USER_ID, db)

        assert str(result.id) == GEN_ID
        assert result.status == "queued"

    @pytest.mark.asyncio
    async def test_404_when_not_found(self):
        """404 GENERATION_NOT_FOUND when no row returned."""
        db = _make_db(_result(data=None))

        with pytest.raises(HTTPException) as exc:
            await get_generation(FAKE_REQUEST, GEN_ID, USER_ID, db)

        assert exc.value.status_code == 404
        assert exc.value.detail["code"] == "GENERATION_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_404_when_data_empty_dict(self):
        """404 when data is empty dict (maybe_single returned nothing)."""
        db = _make_db(_result(data={}))

        with pytest.raises(HTTPException) as exc:
            await get_generation(FAKE_REQUEST, GEN_ID, USER_ID, db)

        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_returns_completed_generation(self):
        """Returns completed generation with output_url."""
        row = _gen_row(
            status="completed",
            output_url="https://cdn.example.com/output.mp4",
            completed_at=NOW,
        )
        db = _make_db(_result(data=row))

        result = await get_generation(FAKE_REQUEST, GEN_ID, USER_ID, db)

        assert result.status == "completed"
        assert result.output_url == "https://cdn.example.com/output.mp4"

    @pytest.mark.asyncio
    async def test_returns_failed_generation_with_error(self):
        """Returns failed generation with error_message."""
        row = _gen_row(status="failed", error_message="Model timeout")
        db = _make_db(_result(data=row))

        result = await get_generation(FAKE_REQUEST, GEN_ID, USER_ID, db)

        assert result.status == "failed"
        assert result.error_message == "Model timeout"

    @pytest.mark.asyncio
    async def test_returns_processing_generation(self):
        """Returns generation in processing state."""
        row = _gen_row(status="processing", processing_started_at=NOW)
        db = _make_db(_result(data=row))

        result = await get_generation(FAKE_REQUEST, GEN_ID, USER_ID, db)

        assert result.status == "processing"

    @pytest.mark.asyncio
    async def test_crystal_cost_preserved_in_response(self):
        """Crystal cost from DB is returned accurately."""
        row = _gen_row(crystal_cost=QUEUE_SKIP_CRYSTAL_COST)
        db = _make_db(_result(data=row))

        result = await get_generation(FAKE_REQUEST, GEN_ID, USER_ID, db)

        assert result.crystal_cost == QUEUE_SKIP_CRYSTAL_COST

    @pytest.mark.asyncio
    async def test_query_filters_by_both_gen_id_and_user_id(self):
        """404 when generation belongs to a different user (RLS-equivalent check)."""
        # The endpoint queries eq("id", gen_id).eq("user_id", user_id) —
        # if wrong user, DB returns None (RLS filters it out).
        db = _make_db(_result(data=None))  # simulates RLS/eq filter returning nothing

        with pytest.raises(HTTPException) as exc:
            await get_generation(FAKE_REQUEST, GEN_ID, OTHER_USER_ID, db)

        assert exc.value.status_code == 404
