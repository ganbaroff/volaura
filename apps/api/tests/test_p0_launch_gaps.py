"""P0 launch-gap tests — three critical paths that were untested before 2026-03-30.

QA Agent identified these as gaps during Sprint A1 gate review:
  1. Duplicate username → must return 409 (not silently create or 500)
  2. complete_assessment with zero answers → must not crash (engine handles empty state)
  3. Public profile with no AURA score → must return 200 with null scores (not 500)

Run: pytest apps/api/tests/test_p0_launch_gaps.py -v
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin, get_supabase_user
from app.main import app
from app.middleware.rate_limit import limiter

# ── Constants ──────────────────────────────────────────────────────────────────

USER_A_ID = "p0aa0001-0000-0000-0000-000000000001"
USER_B_ID = "p0aa0002-0000-0000-0000-000000000002"
SESSION_ID = str(uuid.uuid4())
COMP_ID = "p0aa0010-0000-0000-0000-000000000010"
COMP_SLUG = "communication"
TAKEN_USERNAME = "leyla_taken"
PUBLIC_USERNAME = "nigar_public"
PUBLIC_USER_ID = "p0aa0020-0000-0000-0000-000000000020"

MOCK_PROFILE_NO_AURA = {
    "id": PUBLIC_USER_ID,
    "username": PUBLIC_USERNAME,
    "display_name": "Nigar Test",
    "avatar_url": None,
    "bio": "No aura yet",
    "location": "Baku",
    "languages": ["az"],
    "badge_issued_at": None,
    "registration_number": None,
    "registration_tier": None,
    "is_public": True,
}


# ── Helpers ────────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset in-memory rate limiter before each test."""
    try:
        limiter._limiter.storage.reset()
    except Exception:
        pass
    yield


def _make_dep_override(value):
    async def _override():
        yield value
    return _override


def _make_user_id_override(user_id: str):
    async def _override():
        return user_id
    return _override


def _build_chainable(execute_side_effects: list):
    """Build a Supabase-like chainable mock with a sequence of execute() responses.

    Matches the pattern established in test_beta_user_journey.py.
    """
    mock = MagicMock()
    for attr in [
        "table", "select", "insert", "update", "delete", "upsert",
        "eq", "neq", "gte", "lte", "gt", "lt",
        "order", "limit", "range", "filter", "not_", "in_",
        "single", "maybe_single", "rpc",
    ]:
        setattr(mock, attr, MagicMock(return_value=mock))

    responses = iter(execute_side_effects)

    async def _execute(*args, **kwargs):
        try:
            val = next(responses)
            if isinstance(val, MagicMock):
                return val
            return MagicMock(data=val, count=None)
        except StopIteration:
            return MagicMock(data=None, count=None)

    mock.execute = AsyncMock(side_effect=_execute)
    return mock


# ── Test 1: Duplicate username → 409 ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_duplicate_username_returns_409():
    """POST /api/profiles/me with a username that is already taken must return 409.

    Router: profiles.py create_my_profile — checks .eq("username", payload.username)
    and raises HTTPException(409, code=USERNAME_TAKEN) when existing.data is truthy.
    """
    # The first execute() call is the "check username taken" query.
    # Return a non-empty list → username IS taken → router raises 409.
    user = _build_chainable([
        [{"id": USER_A_ID}],   # username-taken check → row exists → conflict
    ])
    admin = _build_chainable([])

    app.dependency_overrides[get_supabase_user] = _make_dep_override(user)
    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_B_ID)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/profiles/me",
                json={
                    "username": TAKEN_USERNAME,
                    "display_name": "New User",
                    "account_type": "volunteer",
                },
            )
        assert resp.status_code == 409, (
            f"Expected 409 USERNAME_TAKEN, got {resp.status_code}: {resp.text}"
        )
        body = resp.json()
        detail = body.get("detail", {})
        assert detail.get("code") == "USERNAME_TAKEN", (
            f"Expected code=USERNAME_TAKEN in detail, got: {detail}"
        )
    finally:
        app.dependency_overrides.pop(get_supabase_user, None)
        app.dependency_overrides.pop(get_supabase_admin, None)
        app.dependency_overrides.pop(get_current_user_id, None)


# ── Test 2: complete_assessment with zero answers → not 500 ───────────────────

@pytest.mark.asyncio
async def test_complete_with_zero_answers_does_not_crash():
    """POST /api/assessment/complete/{session_id} where session.answers={} must not 500.

    Engine path: CATState.from_dict({}) → theta=0.0, items=[], anti-gaming analyse([])
    → theta_to_score(0.0) → valid float → AssessmentResultOut returned (200).
    No divide-by-zero in IRT engine when items list is empty.
    """
    empty_session = {
        "id": SESSION_ID,
        "volunteer_id": USER_A_ID,
        "status": "in_progress",
        "competency_id": COMP_ID,
        "answers": {},          # zero answers — the critical edge case
        "answer_version": 0,
        "expires_at": None,
        "question_delivered_at": None,
        "gaming_flags": [],
        "gaming_penalty_multiplier": 1.0,
        "theta_estimate": 0.0,
        "coaching_note": None,
        "pending_aura_sync": False,
        "role_level": "volunteer",
    }

    user = _build_chainable([
        empty_session,    # db_user.select("*").eq(session_id).single() → session row
    ])
    admin = _build_chainable([
        empty_session,    # db_admin.update(status=completed) → return session
        {"slug": COMP_SLUG},                # competencies.select("slug") → slug
        {"id": "aura-rpc-result"},          # rpc("upsert_aura_score") → success
        None,                               # crystal emit (non-fatal, if any)
    ])

    app.dependency_overrides[get_supabase_user] = _make_dep_override(user)
    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_A_ID)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(f"/api/assessment/complete/{SESSION_ID}")

        # Must not 500 — engine handles empty answers gracefully
        assert resp.status_code != 500, (
            f"complete_assessment crashed with 500 on zero-answer session: {resp.text}"
        )
        # 200 or 4xx are both acceptable — 500 is the only failure mode we guard against
        assert resp.status_code in (200, 400, 404, 410, 422), (
            f"Unexpected status {resp.status_code}: {resp.text}"
        )
    finally:
        app.dependency_overrides.pop(get_supabase_user, None)
        app.dependency_overrides.pop(get_supabase_admin, None)
        app.dependency_overrides.pop(get_current_user_id, None)


# ── Test 3: Public profile with no AURA score → 200 with null fields ──────────

@pytest.mark.asyncio
async def test_public_profile_no_aura_returns_200():
    """GET /api/profiles/{username} for user with is_public=True but no aura_scores row.

    Router path (profiles.py get_public_profile):
      1. SELECT profile → found
      2. SELECT aura_scores WHERE volunteer_id → no row (score_row.data is None)
      3. percentile_rank computation is skipped entirely (no score → early exit)
      4. Returns PublicProfileResponse with percentile_rank=None — no 500

    This guards against a regression where None aura_scores row causes AttributeError.
    """
    admin = _build_chainable([
        MOCK_PROFILE_NO_AURA,   # profiles SELECT → profile found
        None,                   # aura_scores SELECT by volunteer_id → no row
        # No further execute() calls because score_row.data is None → loop exits early
    ])

    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get(f"/api/profiles/{PUBLIC_USERNAME}")

        assert resp.status_code == 200, (
            f"Expected 200 for public profile with no AURA, got {resp.status_code}: {resp.text}"
        )
        body = resp.json()
        # Confirm the response is not a 500 body masquerading as success
        assert "username" in body or "detail" not in body, (
            f"Response missing username field: {body}"
        )
        assert body.get("username") == PUBLIC_USERNAME, (
            f"Username mismatch: {body}"
        )
        # percentile_rank must be null (no score → no computation)
        assert body.get("percentile_rank") is None, (
            f"Expected null percentile_rank for user with no AURA, got: {body.get('percentile_rank')}"
        )
    finally:
        app.dependency_overrides.pop(get_supabase_admin, None)
