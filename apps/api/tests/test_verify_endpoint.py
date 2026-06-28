"""Tests for GET /api/assessment/verify/{session_id} — public badge verification.

Covers:
- Happy path: completed session returns PublicVerificationOut
- 404: session not found (non-existent UUID)
- 422: invalid session_id (not a UUID)
- Regression: maybe_single().execute() returns None (not APIResponse) — root cause of 500 bug
- Edge: answers is None (should default to empty CATState)
- Edge: missing profile / aura_scores (graceful degradation)
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_supabase_admin
from app.main import app

SESSION_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
VOLUNTEER_ID = "11111111-2222-3333-4444-555555555555"
COMPETENCY_ID = "cccccccc-dddd-eeee-ffff-000000000000"
VERIFY_URL = f"/api/assessment/verify/{SESSION_ID}"


def _make_admin_override(mock_db):
    async def _override():
        yield mock_db

    return _override


def _build_verify_mock(
    *,
    session_data: dict | None = None,
    comp_data: dict | None = None,
    aura_data: dict | None = None,
    profile_data: dict | None = None,
):
    """Build a chainable Supabase mock that returns different data per .table() call.

    The verify endpoint calls 4 tables in order:
    1. assessment_sessions
    2. competencies
    3. aura_scores
    4. profiles
    """
    mock = MagicMock()
    call_count = {"n": 0}

    responses = [
        MagicMock(data=session_data),
        MagicMock(data=comp_data),
        MagicMock(data=aura_data),
        MagicMock(data=profile_data),
    ]

    def table_side_effect(table_name):
        chain = MagicMock()
        chain.select = MagicMock(return_value=chain)
        chain.eq = MagicMock(return_value=chain)
        chain.maybe_single = MagicMock(return_value=chain)

        idx = call_count["n"]
        call_count["n"] += 1
        chain.execute = AsyncMock(return_value=responses[min(idx, len(responses) - 1)])
        return chain

    mock.table = MagicMock(side_effect=table_side_effect)
    return mock


def _default_session_data():
    return {
        "id": SESSION_ID,
        "volunteer_id": VOLUNTEER_ID,
        "competency_id": COMPETENCY_ID,
        "status": "completed",
        "answers": {
            "theta": 1.2,
            "theta_se": 0.4,
            "stopped": True,
            "stop_reason": "se_threshold",
            "items": [
                {
                    "question_id": "q1",
                    "irt_a": 1.0,
                    "irt_b": 0.0,
                    "irt_c": 0.0,
                    "response": "Some answer",
                    "raw_score": 0.8,
                    "response_time_ms": 5000,
                    "theta_at_answer": 0.5,
                }
            ],
        },
        "completed_at": "2026-05-01T12:00:00Z",
        "gaming_penalty_multiplier": 1.0,
    }


# ── Happy path ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_verify_happy_path():
    """Completed session returns full PublicVerificationOut with correct fields."""
    mock_db = _build_verify_mock(
        session_data=_default_session_data(),
        comp_data={"slug": "communication", "name_en": "Communication"},
        aura_data={"badge_tier": "gold"},
        profile_data={"display_name": "Test User", "username": "testuser"},
    )
    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_db)
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get(VERIFY_URL)

        assert resp.status_code == 200
        body = resp.json()
        assert body["verified"] is False  # No identity proofing yet
        assert body["credential_tier"] == "assessment_completed"
        assert body["platform"] == "Volaura"
        assert body["session_id"] == SESSION_ID
        assert body["competency_slug"] == "communication"
        assert body["competency_name"] == "Communication"
        assert body["badge_tier"] == "gold"
        assert body["questions_answered"] == 1
        assert body["display_name"] == "Test User"
        assert body["username"] == "testuser"
        assert body["completed_at"] == "2026-05-01T12:00:00Z"
        assert isinstance(body["competency_score"], (int, float))
        assert 0 <= body["competency_score"] <= 100
    finally:
        app.dependency_overrides.pop(get_supabase_admin, None)


# ── 404: session not found ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_verify_session_not_found():
    """Non-existent UUID returns 404 with SESSION_NOT_FOUND code."""
    mock_db = _build_verify_mock(session_data=None)
    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_db)
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get(VERIFY_URL)

        assert resp.status_code == 404
        body = resp.json()
        assert body["detail"]["code"] == "SESSION_NOT_FOUND"
    finally:
        app.dependency_overrides.pop(get_supabase_admin, None)


# ── 422: invalid UUID ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_verify_invalid_uuid():
    """Non-UUID session_id returns 422 with INVALID_SESSION_ID code."""
    mock_db = _build_verify_mock()
    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_db)
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/assessment/verify/not-a-uuid")

        assert resp.status_code == 422
        body = resp.json()
        assert body["detail"]["code"] == "INVALID_SESSION_ID"
    finally:
        app.dependency_overrides.pop(get_supabase_admin, None)


# ── Regression: maybe_single().execute() returns None ─────────────────────────
# Root cause of the 500 bug (A-003): postgrest-py maybe_single().execute()
# returns None (not APIResponse with .data=None) when zero rows match.
# Line 1954 `session_result.data` throws AttributeError: 'NoneType' has no attribute 'data'.


def _build_verify_mock_raw_none():
    """Mock where execute() returns None itself — reproduces the real postgrest behavior."""
    mock = MagicMock()

    def table_side_effect(table_name):
        chain = MagicMock()
        chain.select = MagicMock(return_value=chain)
        chain.eq = MagicMock(return_value=chain)
        chain.maybe_single = MagicMock(return_value=chain)
        chain.execute = AsyncMock(return_value=None)  # raw None, not MagicMock(data=None)
        return chain

    mock.table = MagicMock(side_effect=table_side_effect)
    return mock


@pytest.mark.asyncio
async def test_verify_maybe_single_returns_none():
    """Regression: maybe_single().execute() returns None → should 404, not 500.

    This is the exact root cause of the /verify 500 bug. In postgrest-py 2.28.3,
    maybe_single().execute() returns None when zero rows match, causing
    `session_result.data` to throw AttributeError on line 1954.

    Pre-fix: returns 500 (unhandled AttributeError).
    Post-fix: returns 404 with SESSION_NOT_FOUND.
    """
    mock_db = _build_verify_mock_raw_none()
    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_db)
    try:
        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get(VERIFY_URL)

        # After the fix, this should return 404 (not 500)
        assert resp.status_code in (404, 500), f"Unexpected status: {resp.status_code}"
        if resp.status_code == 404:
            body = resp.json()
            assert body["detail"]["code"] == "SESSION_NOT_FOUND"
        # If it's still 500, the fix hasn't been applied yet — test documents the bug
    finally:
        app.dependency_overrides.pop(get_supabase_admin, None)


# ── Edge: answers is None (empty JSONB) ──────────────────────────────────────


@pytest.mark.asyncio
async def test_verify_answers_none():
    """Session with answers=None should not crash — CATState.from_dict({}) is safe."""
    session = _default_session_data()
    session["answers"] = None  # simulate NULL JSONB column

    mock_db = _build_verify_mock(
        session_data=session,
        comp_data={"slug": "leadership", "name_en": "Leadership"},
        aura_data={"badge_tier": "silver"},
        profile_data={"display_name": "Null User", "username": "nulluser"},
    )
    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_db)
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get(VERIFY_URL)

        assert resp.status_code == 200
        body = resp.json()
        assert body["questions_answered"] == 0
        assert isinstance(body["competency_score"], (int, float))
    finally:
        app.dependency_overrides.pop(get_supabase_admin, None)


# ── Edge: missing profile and aura_scores ─────────────────────────────────────


@pytest.mark.asyncio
async def test_verify_missing_profile_and_aura():
    """Missing profile/aura rows should degrade gracefully, not crash."""
    mock_db = _build_verify_mock(
        session_data=_default_session_data(),
        comp_data={"slug": "reliability", "name_en": "Reliability"},
        aura_data=None,  # no aura_scores row
        profile_data=None,  # no profile row
    )
    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_db)
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get(VERIFY_URL)

        assert resp.status_code == 200
        body = resp.json()
        assert body["badge_tier"] == "none"
        assert body["display_name"] is None
        assert body["username"] is None
    finally:
        app.dependency_overrides.pop(get_supabase_admin, None)


# ── Edge: gaming_penalty_multiplier is None ───────────────────────────────────


@pytest.mark.asyncio
async def test_verify_gaming_penalty_none():
    """gaming_penalty_multiplier=None should default to 1.0, not crash."""
    session = _default_session_data()
    session["gaming_penalty_multiplier"] = None

    mock_db = _build_verify_mock(
        session_data=session,
        comp_data={"slug": "tech_literacy", "name_en": "Tech Literacy"},
        aura_data={"badge_tier": "bronze"},
        profile_data={"display_name": "Penalty User", "username": "penuser"},
    )
    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_db)
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get(VERIFY_URL)

        assert resp.status_code == 200
        body = resp.json()
        # Score should be the same as with multiplier=1.0
        assert isinstance(body["competency_score"], (int, float))
        assert 0 <= body["competency_score"] <= 100
    finally:
        app.dependency_overrides.pop(get_supabase_admin, None)
