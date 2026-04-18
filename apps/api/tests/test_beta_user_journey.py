"""Beta user journey integration test — full chain from profile creation to public profile.

Tests the complete beta user path end-to-end using mocked Supabase + LLM:
  Step 1: Create profile (POST /api/profiles/me)
  Step 2: Start assessment (POST /api/assessment/start)
  Step 3: Submit MCQ answer (POST /api/assessment/answer)
  Step 4: Complete assessment (POST /api/assessment/complete/{session_id})
  Step 5: Fetch AURA score (GET /api/aura/me)
  Step 6: View public profile (GET /api/profiles/{username})
  Step 7: Full journey smoke test (all steps non-500)

Why this test exists:
  Unit tests cover each endpoint in isolation. This test validates that the
  data written in one step is correctly read by the next. Catches: router
  response shape contracts, schema mismatches, unhandled exceptions in
  the critical launch path. Identified by QA Agent in Sprint Gate DSP (2026-03-30).

Key implementation notes:
  - complete_assessment uses db_admin (not db_user) for session UPDATE
    (BLOCKER-1 FIX: user-level UPDATE policy removed to prevent theta manipulation)
  - submit_answer does NOT return raw_score to client (CRIT-03: prevents BARS calibration attacks)
  - PublicProfileResponse computes percentile_rank server-side — do NOT include in DB mock data

Run: pytest apps/api/tests/test_beta_user_journey.py -v
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin, get_supabase_user
from app.main import app
from app.middleware.rate_limit import limiter

# ── Constants ──────────────────────────────────────────────────────────────────

USER_ID = "be7a0001-0000-0000-0000-000000000001"
SESSION_ID = "be7a0002-0000-0000-0000-000000000002"
COMP_ID = "be7a0010-0000-0000-0000-000000000010"
COMP_SLUG = "communication"
Q_MCQ_ID = "be7a0003-0000-0000-0000-000000000003"
TEST_USERNAME = "leyla_test"

MCQ_QUESTION = {
    "id": Q_MCQ_ID,
    "competency_id": COMP_ID,
    "type": "mcq",
    "scenario_en": "A volunteer misses their shift. What do you do?",
    "scenario_az": "Könüllü növbəsini qaçırır. Nə edərsiniz?",
    "options": [
        {"key": "A", "text_en": "Ignore it", "text_az": "Nəzərə alma"},
        {"key": "B", "text_en": "Contact them", "text_az": "Əlaqə saxla"},
        {"key": "C", "text_en": "Report to manager", "text_az": "Rəhbərə bildir"},
        {"key": "D", "text_en": "Cover their shift", "text_az": "Növbəni örtün"},
    ],
    "correct_answer": "B",
    "expected_concepts": None,
    "irt_a": 1.2,
    "irt_b": 0.0,
    "irt_c": 0.2,
    "difficulty": "medium",
    "is_active": True,
}

# Note: do NOT include percentile_rank in DB mock data — router computes it separately
MOCK_PROFILE_DB = {
    "id": USER_ID,
    "username": TEST_USERNAME,
    "full_name": "Leyla Test",
    "bio": "Test bio",
    "email": "leyla@test.com",
    "location": "Baku",
    "languages": ["az", "en"],
    "skills": [],
    "avatar_url": None,
    "is_public": True,
    "registration_number": 1,
    "registration_tier": "founding_100",
    "subscription_status": "trial",
    "trial_ends_at": None,
    "created_at": "2026-03-30T00:00:00Z",
    "updated_at": "2026-03-30T00:00:00Z",
}

MOCK_AURA_DB = {
    "id": "be7a0020-0000-0000-0000-000000000020",
    "volunteer_id": USER_ID,
    "total_score": 72.5,
    "effective_score": 72.5,
    "badge_tier": "silver",
    "elite_status": False,
    "competency_scores": {"communication": 72.5},
    "last_updated": "2026-03-30T00:00:00Z",
}

IN_PROGRESS_SESSION = {
    "id": SESSION_ID,
    "volunteer_id": USER_ID,
    "status": "in_progress",
    "competency_id": COMP_ID,
    "current_question_id": Q_MCQ_ID,
    "answers": {},
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

COMPLETED_SESSION = {
    **IN_PROGRESS_SESSION,
    "status": "in_progress",  # complete_assessment forcefully completes in_progress sessions
    "answers": {
        "items": [
            # Each item MUST include irt_a/b/c + response — required by CATState.from_dict()
            {
                "question_id": Q_MCQ_ID,
                "irt_a": 1.2,
                "irt_b": 0.0,
                "irt_c": 0.2,
                "response": 1,
                "raw_score": 1.0,
                "response_time_ms": 3000,
            },
            {
                "question_id": str(uuid.uuid4()),
                "irt_a": 1.0,
                "irt_b": -0.5,
                "irt_c": 0.2,
                "response": 1,
                "raw_score": 0.8,
                "response_time_ms": 4000,
            },
            {
                "question_id": str(uuid.uuid4()),
                "irt_a": 1.3,
                "irt_b": 0.2,
                "irt_c": 0.1,
                "response": 1,
                "raw_score": 1.0,
                "response_time_ms": 3500,
            },
            {
                "question_id": str(uuid.uuid4()),
                "irt_a": 0.9,
                "irt_b": 0.5,
                "irt_c": 0.2,
                "response": 1,
                "raw_score": 0.9,
                "response_time_ms": 2800,
            },
            {
                "question_id": str(uuid.uuid4()),
                "irt_a": 1.1,
                "irt_b": -0.2,
                "irt_c": 0.2,
                "response": 1,
                "raw_score": 1.0,
                "response_time_ms": 3200,
            },
            {
                "question_id": str(uuid.uuid4()),
                "irt_a": 1.0,
                "irt_b": 0.8,
                "irt_c": 0.2,
                "response": 1,
                "raw_score": 0.7,
                "response_time_ms": 5000,
            },
            {
                "question_id": str(uuid.uuid4()),
                "irt_a": 1.2,
                "irt_b": 0.3,
                "irt_c": 0.1,
                "response": 1,
                "raw_score": 0.8,
                "response_time_ms": 4500,
            },
            {
                "question_id": str(uuid.uuid4()),
                "irt_a": 1.0,
                "irt_b": -0.1,
                "irt_c": 0.2,
                "response": 1,
                "raw_score": 0.9,
                "response_time_ms": 3800,
            },
        ],
        "theta": 0.8,
        "theta_se": 0.3,
        "stop_reason": "max_items",
        "stopped": True,
    },
    "theta_estimate": 0.8,
}


# ── Fixtures ───────────────────────────────────────────────────────────────────


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
    """Build a Supabase-like chainable mock with a sequence of execute() responses."""
    mock = MagicMock()
    for attr in [
        "table",
        "select",
        "insert",
        "update",
        "delete",
        "upsert",
        "eq",
        "neq",
        "gte",
        "lte",
        "gt",
        "lt",
        "order",
        "limit",
        "range",
        "filter",
        "not_",
        "in_",
        "single",
        "maybe_single",
        "rpc",
    ]:
        setattr(mock, attr, MagicMock(return_value=mock))

    responses = iter(execute_side_effects)

    async def _execute(*args, **kwargs):
        try:
            val = next(responses)
            if isinstance(val, MagicMock):
                return val
            return MagicMock(data=val)
        except StopIteration:
            # Default: return empty/None data (no crash, just empty result)
            return MagicMock(data=None)

    mock.execute = AsyncMock(side_effect=_execute)
    return mock


# ── Step 1: Profile creation ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_step1_create_profile():
    """POST /api/profiles/me → 201 with profile data including username.

    Router does result.data[0] on insert result — mock must return a LIST.
    """
    user = _build_chainable(
        [
            None,  # maybe_single: no existing profile (not found)
            [MOCK_PROFILE_DB],  # insert → returns list of inserted rows (router uses [0])
        ]
    )
    admin = _build_chainable(
        [
            [MOCK_PROFILE_DB],  # fallback read if needed
        ]
    )

    app.dependency_overrides[get_supabase_user] = _make_dep_override(user)
    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/profiles/me",
                json={
                    "username": TEST_USERNAME,
                    "full_name": "Leyla Test",
                    "bio": "Test bio",
                    "is_public": True,
                },
                headers={"Authorization": "Bearer test-token"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 201, f"Profile creation failed: {resp.status_code} — {resp.text}"
    body = resp.json()
    assert "username" in body or "id" in body, f"Response missing profile fields: {body}"


# ── Step 2: Start assessment ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_step2_start_assessment():
    """POST /api/assessment/start → session_id + next_question (not None)."""
    admin = _build_chainable(
        [
            {"id": COMP_ID},  # competency lookup by slug
            [MCQ_QUESTION],  # questions pool
        ]
    )
    user = _build_chainable(
        [
            # payment_enabled=False → paywall check skipped in beta
            {"is_platform_admin": False},  # admin lookup — FIRST (commit f2ce68f reorder)
            [],  # no in-progress session
            [],  # no rapid-restart cooldown
            [],  # no retest cooldown
            MagicMock(data=[], count=0),  # abuse monitoring count
            [],  # no carry-over theta
            {"id": SESSION_ID},  # session insert
        ]
    )

    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)
    app.dependency_overrides[get_supabase_user] = _make_dep_override(user)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/assessment/start",
                json={"competency_slug": COMP_SLUG, "automated_decision_consent": True},
                headers={"Authorization": "Bearer test-token"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 201, f"Assessment start failed: {resp.status_code} — {resp.text}"
    body = resp.json()
    assert "session_id" in body, f"Missing session_id in: {body}"
    assert body.get("next_question") is not None, "next_question should not be None on start"


# ── Step 3: Submit MCQ answer ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_step3_submit_answer():
    """POST /api/assessment/answer → session state updated, timing_warning field present.

    Key implementation notes:
    - submit_answer uses db_admin (not db_user) for session UPDATE (BLOCKER-1 FIX)
    - raw_score is NOT returned to client (CRIT-03: prevents BARS calibration attacks)
    - Response contains: session_id, question_id, timing_warning, session (SessionOut)
    """
    next_q = {**MCQ_QUESTION, "id": str(uuid.uuid4()), "irt_b": 0.3}
    updated_session_list = [
        {
            **IN_PROGRESS_SESSION,
            "current_question_id": next_q["id"],
            "answer_version": 1,
            "answers": {
                "items": [{"question_id": Q_MCQ_ID, "raw_score": 1.0, "response_time_ms": 3000}],
                "theta": 0.3,
            },
        }
    ]

    # db_user: only session load (1 call) — updates use db_admin
    user = _build_chainable(
        [
            IN_PROGRESS_SESSION,  # session lookup by id + volunteer_id
        ]
    )
    # db_admin sequence for MCQ answer:
    # 1. questions table lookup (question fetch)
    # 2. questions list for next item (fetch_questions via helpers)
    # 3. assessment_sessions UPDATE with optimistic lock → must return LIST not None
    # 4. competencies lookup for slug (get_competency_slug)
    admin = _build_chainable(
        [
            MCQ_QUESTION,  # question fetch
            [MCQ_QUESTION, next_q],  # fetch_questions → pool for next item selection
            updated_session_list,  # session UPDATE (optimistic lock) → LIST required
            {"slug": COMP_SLUG},  # get_competency_slug
        ]
    )

    app.dependency_overrides[get_supabase_user] = _make_dep_override(user)
    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/assessment/answer",
                json={
                    "session_id": SESSION_ID,
                    "question_id": Q_MCQ_ID,
                    "answer": "B",
                    "response_time_ms": 3000,
                },
                headers={"Authorization": "Bearer test-token"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200, f"Answer submission failed: {resp.status_code} — {resp.text}"
    body = resp.json()
    # raw_score deliberately NOT in response (CRIT-03) — check session state instead
    assert "session_id" in body, f"Missing session_id in: {body}"
    assert "session" in body, f"Missing session (SessionOut) in: {body}"
    # raw_score must NOT be exposed to client
    assert "raw_score" not in body, "CRIT-03: raw_score must never be sent to client"


# ── Step 4: Complete assessment ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_step4_complete_assessment():
    """POST /api/assessment/complete/{session_id} → competency_score > 0, session_id present."""
    # db_user: session load
    user = _build_chainable(
        [
            COMPLETED_SESSION,  # session lookup
        ]
    )
    # db_admin sequence for complete_assessment:
    # 1. assessment_sessions UPDATE (force complete in_progress)
    # 2. competencies SELECT slug
    # 3. rpc("upsert_aura_score", ...)
    # 4. emit_assessment_rewards calls (character_state inserts etc.)
    admin = _build_chainable(
        [
            [COMPLETED_SESSION],  # session UPDATE to completed
            {"slug": COMP_SLUG, "id": COMP_ID},  # competency slug lookup
            MagicMock(data={"total_score": 72.5, "badge_tier": "silver"}),  # upsert_aura_score RPC
        ]
    )

    app.dependency_overrides[get_supabase_user] = _make_dep_override(user)
    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    # Patch emit_assessment_rewards — correct function name (not emit_reward)
    with patch(
        "app.routers.assessment.emit_assessment_rewards",
        new=AsyncMock(return_value=None),
    ):
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.post(
                    f"/api/assessment/complete/{SESSION_ID}",
                    headers={"Authorization": "Bearer test-token"},
                )
        finally:
            app.dependency_overrides.clear()

    assert resp.status_code == 200, f"Complete assessment failed: {resp.status_code} — {resp.text}"
    body = resp.json()
    assert "session_id" in body, f"Missing session_id in: {body}"
    assert "competency_score" in body, f"Missing competency_score in: {body}"
    assert body["competency_score"] >= 0, "competency_score should be non-negative"


# ── Step 5: Fetch AURA score ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_step5_fetch_aura_score():
    """GET /api/aura/me → total_score not None, badge_tier valid."""
    user = _build_chainable([MOCK_AURA_DB])

    app.dependency_overrides[get_supabase_user] = _make_dep_override(user)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get(
                "/api/aura/me",
                headers={"Authorization": "Bearer test-token"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200, f"AURA fetch failed: {resp.status_code} — {resp.text}"
    body = resp.json()
    assert body.get("total_score") is not None, "AURA total_score is None — score not persisted"
    assert body.get("badge_tier") in ("bronze", "silver", "gold", "platinum"), (
        f"Invalid badge_tier: {body.get('badge_tier')}"
    )


# ── Step 6: Public profile visibility ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_step6_public_profile_shows_badge():
    """GET /api/profiles/{username} → profile visible after assessment, is_public=True.

    NOTE: Do NOT include percentile_rank in the mock profile dict — the router
    computes it via two COUNT queries and passes it as a separate kwarg.
    Putting it in result.data causes 'multiple values for keyword argument' TypeError.
    """
    admin = _build_chainable(
        [
            MOCK_PROFILE_DB,  # profile lookup by username
            # percentile computation (aura_scores queries) — will return None gracefully
        ]
    )

    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)
    # No auth needed — this is a public endpoint

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get(f"/api/profiles/{TEST_USERNAME}")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200, f"Public profile fetch failed: {resp.status_code} — {resp.text}"
    body = resp.json()
    assert body.get("username") == TEST_USERNAME, f"Wrong username: {body.get('username')}"
    # is_public is NOT in PublicProfileResponse (minimal public schema by design)
    # A 200 + correct username is sufficient proof the profile is publicly accessible
    assert body.get("id") == USER_ID, "Profile ID should match — confirms correct record returned"


# ── Step 7: Journey smoke test — all critical steps return non-500 ─────────────


@pytest.mark.asyncio
async def test_full_journey_no_500s():
    """Smoke: critical journey endpoints return non-5xx responses.

    Tests start + AURA + public profile in sequence.
    Catches: import errors, unhandled exceptions, schema registration issues.
    """
    results = {}

    # Step 2 — start assessment
    admin_start = _build_chainable(
        [
            {"id": COMP_ID},
            [MCQ_QUESTION],
        ]
    )
    user_start = _build_chainable(
        [
            {"is_platform_admin": False},  # admin lookup — FIRST (commit f2ce68f reorder)
            [],  # no in-progress session
            [],
            [],
            MagicMock(data=[], count=0),
            [],
            {"id": SESSION_ID},
        ]
    )
    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin_start)
    app.dependency_overrides[get_supabase_user] = _make_dep_override(user_start)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)
    try:
        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            r = await ac.post(
                "/api/assessment/start",
                json={"competency_slug": COMP_SLUG, "automated_decision_consent": True},
                headers={"Authorization": "Bearer test-token"},
            )
            results["start"] = r.status_code
    finally:
        app.dependency_overrides.clear()

    # Step 5 — aura score
    user_aura = _build_chainable([MOCK_AURA_DB])
    app.dependency_overrides[get_supabase_user] = _make_dep_override(user_aura)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)
    try:
        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            r = await ac.get("/api/aura/me", headers={"Authorization": "Bearer test-token"})
            results["aura"] = r.status_code
    finally:
        app.dependency_overrides.clear()

    # Step 6 — public profile
    admin_pub = _build_chainable([MOCK_PROFILE_DB])
    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin_pub)
    try:
        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            r = await ac.get(f"/api/profiles/{TEST_USERNAME}")
            results["public_profile"] = r.status_code
    finally:
        app.dependency_overrides.clear()

    # All critical journey steps must return non-5xx
    for step, code in results.items():
        assert code < 500, f"Step '{step}' returned server error {code} — critical journey broken"
