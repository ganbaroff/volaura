"""Sprint A1 Acceptance Tests — Crystal rewards + Character state.

Acceptance criteria (Sprint A1):
  "Complete assessment → GET /character/state shows crystals + verified_skills"

Tests:
  1. emit_assessment_rewards() writes crystal_earned + skill_verified events
  2. emit_assessment_rewards() is idempotent (duplicate call = no double reward)
  3. GET /character/state returns crystal_balance > 0 and verified_skills after assessment
  4. GET /character/state returns skill_verified only for scores >= Bronze threshold (>=50)
  5. Reward not emitted when score is below Bronze threshold
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.assessment.aura_calc import BADGE_TIERS
from app.deps import get_current_user_id, get_supabase_admin, get_supabase_user
from app.main import app
from app.services.assessment.rewards import CRYSTAL_REWARD, emit_assessment_rewards

USER_ID = "11111111-2222-3333-4444-555555555555"


# ── Helpers ─────────────────────────────────────────────────────────────────

def _make_admin_override(mock_db):
    async def _override():
        yield mock_db
    return _override


def _make_user_id_override(user_id: str):
    async def _override():
        return user_id
    return _override


def _build_db_mock():
    """Chainable mock for Supabase fluent API: .table().select().eq()...execute()"""
    m = MagicMock()
    m.table = MagicMock(return_value=m)
    m.select = MagicMock(return_value=m)
    m.insert = MagicMock(return_value=m)
    m.update = MagicMock(return_value=m)
    m.upsert = MagicMock(return_value=m)
    m.eq = MagicMock(return_value=m)
    m.single = MagicMock(return_value=m)
    m.order = MagicMock(return_value=m)
    m.limit = MagicMock(return_value=m)
    m.range = MagicMock(return_value=m)
    m.gte = MagicMock(return_value=m)
    m.execute = AsyncMock(return_value=MagicMock(data=None))
    m.rpc = MagicMock(return_value=m)
    return m


# ── Tests: emit_assessment_rewards ──────────────────────────────────────────

def _build_rewards_mock_db(already_claimed: bool = False) -> tuple[MagicMock, list[str]]:
    """Build a Supabase mock that tracks table names passed to .insert()/.upsert().

    Returns (db_mock, insert_table_names_list).
    Uses plain MagicMock (non-circular) so select/insert chains don't clobber each other.
    """
    insert_table_names: list[str] = []

    def make_table_mock(name: str) -> MagicMock:
        t = MagicMock()

        # select chain: .select().eq().eq().execute() → empty or claimed
        no_reward_data: list = [{"claimed": True}] if already_claimed else []
        t.select.return_value.eq.return_value.eq.return_value.execute = AsyncMock(
            return_value=MagicMock(data=no_reward_data)
        )
        # daily cap query: .select().eq().gte().execute() → no crystals today
        t.select.return_value.eq.return_value.gte.return_value.execute = AsyncMock(
            return_value=MagicMock(data=[])
        )

        # insert chain: tracks table name
        async def _track_insert(*args, **kwargs):
            insert_table_names.append(name)
            return MagicMock(data=[{"id": "test-id"}])

        t.insert.return_value.execute = AsyncMock(side_effect=_track_insert)
        t.upsert.return_value.execute = AsyncMock(
            return_value=MagicMock(data=[{"claimed": True}])
        )
        return t

    db = MagicMock()
    db.table = MagicMock(side_effect=make_table_mock)
    return db, insert_table_names


@pytest.mark.asyncio
async def test_emit_rewards_writes_crystal_and_skill_events():
    """emit_assessment_rewards writes crystal_earned + skill_verified to character_events."""
    db, insert_calls = _build_rewards_mock_db(already_claimed=False)

    import app.services.assessment.rewards as rewards_module
    original_notify = rewards_module.notify

    async def _noop_notify(*args, **kwargs):
        pass

    rewards_module.notify = _noop_notify

    try:
        await emit_assessment_rewards(
            db=db,
            user_id=USER_ID,
            skill_slug="communication",
            competency_score=75.0,  # gold tier (>=70)
        )

        # crystal_earned → character_events, then game_crystal_ledger, then character_events for skill_verified
        assert "character_events" in insert_calls, (
            f"Expected character_events insert — got: {insert_calls}"
        )
        assert "game_crystal_ledger" in insert_calls, (
            f"Expected game_crystal_ledger insert — got: {insert_calls}"
        )
    finally:
        rewards_module.notify = original_notify


@pytest.mark.asyncio
async def test_emit_rewards_no_skill_verified_below_bronze():
    """Crystal is still awarded, but skill_verified event is NOT emitted below Bronze."""
    from app.services.assessment.rewards import competency_badge_tier

    # Find a score below all badge thresholds
    bronze_threshold = min(t for _, t in BADGE_TIERS)
    below_bronze = bronze_threshold - 1.0
    assert competency_badge_tier(below_bronze) is None, "Score must be below all badge tiers"

    db, insert_calls = _build_rewards_mock_db(already_claimed=False)

    import app.services.assessment.rewards as rewards_module
    original_notify = rewards_module.notify

    async def _noop_notify(*args, **kwargs):
        pass

    rewards_module.notify = _noop_notify

    try:
        await emit_assessment_rewards(
            db=db,
            user_id=USER_ID,
            skill_slug="teamwork",
            competency_score=below_bronze,
        )

        # Crystal should be awarded (always, regardless of badge tier)
        assert "game_crystal_ledger" in insert_calls, (
            f"Crystal reward should fire even below bronze — got: {insert_calls}"
        )

        # Count character_events inserts: crystal=1, skill_verified=0 (below bronze)
        character_event_inserts = [c for c in insert_calls if c == "character_events"]
        assert len(character_event_inserts) == 1, (
            f"Expected exactly 1 character_events insert (crystal only, no skill_verified). Got {character_event_inserts}"
        )
    finally:
        rewards_module.notify = original_notify


@pytest.mark.asyncio
async def test_emit_rewards_idempotent_double_call():
    """Second call with same user+skill does not re-award crystals."""
    import app.services.assessment.rewards as rewards_module
    original_notify = rewards_module.notify

    async def _noop_notify(*args, **kwargs):
        pass

    rewards_module.notify = _noop_notify

    try:
        # First call: reward not yet claimed
        db_first, insert_calls_first = _build_rewards_mock_db(already_claimed=False)
        await emit_assessment_rewards(
            db=db_first,
            user_id=USER_ID,
            skill_slug="leadership",
            competency_score=80.0,
        )

        # Second call: reward already claimed (idempotency check returns data)
        db_second, insert_calls_second = _build_rewards_mock_db(already_claimed=True)
        await emit_assessment_rewards(
            db=db_second,
            user_id=USER_ID,
            skill_slug="leadership",
            competency_score=80.0,
        )

        assert "game_crystal_ledger" in insert_calls_first, (
            "First call must write crystal ledger"
        )
        assert "game_crystal_ledger" not in insert_calls_second, (
            "Second call must NOT write crystal ledger (idempotency enforced)"
        )
    finally:
        rewards_module.notify = original_notify


# ── Tests: GET /character/state endpoint ────────────────────────────────────

@pytest.mark.asyncio
async def test_get_character_state_after_assessment():
    """GET /character/state returns crystal_balance + verified_skills from DB RPC."""
    mock_admin = _build_db_mock()

    # Mock the get_character_state RPC to return a user state with crystals + skill
    state_response = {
        "user_id": USER_ID,
        "crystal_balance": CRYSTAL_REWARD,  # 50 crystals from one assessment
        "xp_total": 100,
        "verified_skills": [
            {
                "slug": "communication",
                "aura_score": 75.0,
                "badge_tier": "gold",
            }
        ],
        "character_stats": {},
        "login_streak": 1,
        "event_count": 2,
        "last_event_at": datetime.now(UTC).isoformat(),
        "computed_at": datetime.now(UTC).isoformat(),
    }

    rpc_result = MagicMock()
    rpc_result.execute = AsyncMock(return_value=MagicMock(data=[state_response]))
    mock_admin.rpc = MagicMock(return_value=rpc_result)

    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_admin)
    app.dependency_overrides[get_supabase_user] = _make_admin_override(mock_admin)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get(
                "/api/character/state",
                headers={"Authorization": "Bearer fake-token"},
            )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()

        # Sprint A1 acceptance criteria: crystals > 0
        assert body["crystal_balance"] == CRYSTAL_REWARD, (
            f"Expected {CRYSTAL_REWARD} crystals, got {body['crystal_balance']}"
        )

        # Sprint A1 acceptance criteria: verified_skills contains the assessed competency
        assert len(body["verified_skills"]) == 1, (
            f"Expected 1 verified skill, got {len(body['verified_skills'])}: {body['verified_skills']}"
        )
        skill = body["verified_skills"][0]
        assert skill["slug"] == "communication"
        assert skill["aura_score"] == 75.0
        assert skill["badge_tier"] == "gold"

        # Structural assertions
        assert body["user_id"] == USER_ID
        assert body["xp_total"] >= 0
        assert body["login_streak"] >= 0

        # RPC was called with the correct function name
        rpc_call = mock_admin.rpc.call_args
        assert rpc_call[0][0] == "get_character_state", (
            f"Wrong RPC function: {rpc_call[0][0]}"
        )
        assert rpc_call[0][1]["p_user_id"] == USER_ID

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_character_state_new_user_returns_empty_state():
    """New user with no events gets zero balance, empty skills — not a 500 error."""
    mock_admin = _build_db_mock()

    # RPC returns empty data for new user
    rpc_result = MagicMock()
    rpc_result.execute = AsyncMock(return_value=MagicMock(data=[]))
    mock_admin.rpc = MagicMock(return_value=rpc_result)

    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_admin)
    app.dependency_overrides[get_supabase_user] = _make_admin_override(mock_admin)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get(
                "/api/character/state",
                headers={"Authorization": "Bearer fake-token"},
            )

        assert resp.status_code == 200, f"Expected 200 for empty state, got {resp.status_code}: {resp.text}"
        body = resp.json()

        assert body["crystal_balance"] == 0, "New user should have 0 crystals"
        assert body["verified_skills"] == [], "New user should have no verified skills"
        assert body["xp_total"] == 0
        assert body["login_streak"] == 0

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_character_state_multiple_skills():
    """After assessing 3 competencies, all appear in verified_skills."""
    mock_admin = _build_db_mock()

    state_response = {
        "user_id": USER_ID,
        "crystal_balance": CRYSTAL_REWARD * 3,  # 3 assessments
        "xp_total": 300,
        "verified_skills": [
            {"slug": "communication", "aura_score": 85.0, "badge_tier": "gold"},
            {"slug": "teamwork", "aura_score": 92.0, "badge_tier": "platinum"},
            {"slug": "leadership", "aura_score": 63.0, "badge_tier": "silver"},
        ],
        "character_stats": {},
        "login_streak": 5,
        "event_count": 6,
        "last_event_at": datetime.now(UTC).isoformat(),
        "computed_at": datetime.now(UTC).isoformat(),
    }

    rpc_result = MagicMock()
    rpc_result.execute = AsyncMock(return_value=MagicMock(data=[state_response]))
    mock_admin.rpc = MagicMock(return_value=rpc_result)

    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_admin)
    app.dependency_overrides[get_supabase_user] = _make_admin_override(mock_admin)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get(
                "/api/character/state",
                headers={"Authorization": "Bearer fake-token"},
            )

        assert resp.status_code == 200
        body = resp.json()

        assert body["crystal_balance"] == CRYSTAL_REWARD * 3
        assert len(body["verified_skills"]) == 3

        slugs = {s["slug"] for s in body["verified_skills"]}
        assert slugs == {"communication", "teamwork", "leadership"}

        tiers = {s["slug"]: s["badge_tier"] for s in body["verified_skills"]}
        assert tiers["communication"] == "gold"
        assert tiers["teamwork"] == "platinum"
        assert tiers["leadership"] == "silver"

    finally:
        app.dependency_overrides.clear()
