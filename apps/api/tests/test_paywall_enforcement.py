"""Tests for paywall enforcement in assessment.py.

Verifies that expired/cancelled users receive HTTP 402 while trial/active users proceed.
Uses the same inline mock pattern as test_assessment_api_e2e.py.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.deps import get_supabase_admin, get_supabase_user, get_current_user_id
from app.middleware.rate_limit import limiter


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset in-memory rate limiter before each test to prevent cross-test pollution."""
    try:
        limiter._limiter.storage.reset()
    except Exception:
        pass
    yield


@pytest.fixture(autouse=True)
def enable_payment():
    """Enable payment gate for all paywall tests — default is False (beta mode)."""
    with patch("app.routers.assessment.settings") as mock_settings:
        mock_settings.payment_enabled = True
        # Pass through all other settings attributes used in start_assessment
        from app.config import settings as real_settings
        mock_settings.swarm_enabled = real_settings.swarm_enabled
        yield


async def _permissive_client():
    """AsyncClient that returns HTTP errors instead of re-raising server exceptions."""
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

MOCK_USER_ID = "00000000-0000-0000-0000-000000000001"
MOCK_COMPETENCY_ID = "00000000-0000-0000-0000-000000000010"


def _mock_execute(data=None):
    result = MagicMock()
    result.data = data
    return result


def _mock_chain(execute_result):
    chain = MagicMock()
    chain.select.return_value = chain
    chain.eq.return_value = chain
    chain.neq.return_value = chain
    chain.order.return_value = chain
    chain.limit.return_value = chain
    chain.single.return_value = chain
    chain.maybe_single.return_value = chain
    chain.in_.return_value = chain
    chain.gte.return_value = chain
    chain.execute = AsyncMock(return_value=execute_result)
    return chain


def _make_deps(user_db, admin_db):
    async def _user():
        yield user_db

    async def _admin():
        yield admin_db

    async def _uid():
        return MOCK_USER_ID

    return _user, _admin, _uid


# ── Paywall blocks ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_start_assessment_blocked_when_expired(client):
    """Expired users receive HTTP 402 SUBSCRIPTION_REQUIRED."""
    expired_profile = _mock_chain(_mock_execute(data={"subscription_status": "expired"}))
    comp_found = _mock_chain(_mock_execute(data={"id": MOCK_COMPETENCY_ID}))

    mock_user_db = MagicMock()
    mock_user_db.table = MagicMock(return_value=expired_profile)

    mock_admin_db = MagicMock()
    mock_admin_db.table = MagicMock(return_value=comp_found)

    _user, _admin, _uid = _make_deps(mock_user_db, mock_admin_db)

    app.dependency_overrides[get_supabase_user] = _user
    app.dependency_overrides[get_supabase_admin] = _admin
    app.dependency_overrides[get_current_user_id] = _uid
    try:
        response = await client.post(
            "/api/assessment/start",
            json={"competency_slug": "communication"},
            headers={"Authorization": "Bearer test-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 402
    body = response.json()
    assert body["detail"]["code"] == "SUBSCRIPTION_REQUIRED"


@pytest.mark.asyncio
async def test_start_assessment_blocked_when_cancelled(client):
    """Cancelled users receive HTTP 402 SUBSCRIPTION_REQUIRED."""
    cancelled_profile = _mock_chain(_mock_execute(data={"subscription_status": "cancelled"}))
    comp_found = _mock_chain(_mock_execute(data={"id": MOCK_COMPETENCY_ID}))

    mock_user_db = MagicMock()
    mock_user_db.table = MagicMock(return_value=cancelled_profile)

    mock_admin_db = MagicMock()
    mock_admin_db.table = MagicMock(return_value=comp_found)

    _user, _admin, _uid = _make_deps(mock_user_db, mock_admin_db)

    app.dependency_overrides[get_supabase_user] = _user
    app.dependency_overrides[get_supabase_admin] = _admin
    app.dependency_overrides[get_current_user_id] = _uid
    try:
        response = await client.post(
            "/api/assessment/start",
            json={"competency_slug": "communication"},
            headers={"Authorization": "Bearer test-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 402
    body = response.json()
    assert body["detail"]["code"] == "SUBSCRIPTION_REQUIRED"


# ── Paywall does not block ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_start_assessment_allowed_when_trial():
    """Trial users can pass the paywall gate (not blocked with 402)."""
    trial_profile = _mock_chain(_mock_execute(data={"subscription_status": "trial"}))
    comp_found = _mock_chain(_mock_execute(data={"id": MOCK_COMPETENCY_ID}))
    no_data = _mock_chain(_mock_execute(data=[]))

    call_count = {"user": 0}

    def user_side_effect(name):
        call_count["user"] += 1
        if call_count["user"] == 1:
            return trial_profile  # paywall check
        return no_data

    mock_user_db = MagicMock()
    mock_user_db.table = MagicMock(side_effect=user_side_effect)

    mock_admin_db = MagicMock()
    mock_admin_db.table = MagicMock(return_value=comp_found)

    _user, _admin, _uid = _make_deps(mock_user_db, mock_admin_db)

    app.dependency_overrides[get_supabase_user] = _user
    app.dependency_overrides[get_supabase_admin] = _admin
    app.dependency_overrides[get_current_user_id] = _uid
    try:
        async for c in _permissive_client():
            response = await c.post(
                "/api/assessment/start",
                json={"competency_slug": "communication"},
                headers={"Authorization": "Bearer test-token"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code != 402, f"Trial user should not be paywalled, got {response.status_code}"


@pytest.mark.asyncio
async def test_start_assessment_allowed_when_active():
    """Active subscribers pass the paywall gate (not blocked with 402)."""
    active_profile = _mock_chain(_mock_execute(data={"subscription_status": "active"}))
    comp_found = _mock_chain(_mock_execute(data={"id": MOCK_COMPETENCY_ID}))
    no_data = _mock_chain(_mock_execute(data=[]))

    call_count = {"user": 0}

    def user_side_effect(name):
        call_count["user"] += 1
        if call_count["user"] == 1:
            return active_profile
        return no_data

    mock_user_db = MagicMock()
    mock_user_db.table = MagicMock(side_effect=user_side_effect)

    mock_admin_db = MagicMock()
    mock_admin_db.table = MagicMock(return_value=comp_found)

    _user, _admin, _uid = _make_deps(mock_user_db, mock_admin_db)

    app.dependency_overrides[get_supabase_user] = _user
    app.dependency_overrides[get_supabase_admin] = _admin
    app.dependency_overrides[get_current_user_id] = _uid
    try:
        async for c in _permissive_client():
            response = await c.post(
                "/api/assessment/start",
                json={"competency_slug": "communication"},
                headers={"Authorization": "Bearer test-token"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code != 402


@pytest.mark.asyncio
async def test_start_assessment_blocked_when_no_profile_row(client):
    """Missing profile row blocks assessment (fail-closed security — no profile = 402).

    Changed 2026-03-30: previously skipped paywall on missing profile. Now fail-closed:
    a missing profile row cannot be a free pass to unlimited assessments.
    Onboarding always creates the profile row; missing = something went wrong.
    """
    no_profile = _mock_chain(_mock_execute(data=None))
    comp_found = _mock_chain(_mock_execute(data={"id": MOCK_COMPETENCY_ID}))

    mock_user_db = MagicMock()
    mock_user_db.table = MagicMock(return_value=no_profile)

    mock_admin_db = MagicMock()
    mock_admin_db.table = MagicMock(return_value=comp_found)

    _user, _admin, _uid = _make_deps(mock_user_db, mock_admin_db)

    app.dependency_overrides[get_supabase_user] = _user
    app.dependency_overrides[get_supabase_admin] = _admin
    app.dependency_overrides[get_current_user_id] = _uid
    try:
        response = await client.post(
            "/api/assessment/start",
            json={"competency_slug": "communication"},
            headers={"Authorization": "Bearer test-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 402
    assert response.json()["detail"]["code"] == "SUBSCRIPTION_REQUIRED"


# ── Error shape ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_subscription_required_error_shape(client):
    """HTTP 402 response has correct JSON shape for frontend parsing."""
    expired_profile = _mock_chain(_mock_execute(data={"subscription_status": "expired"}))
    comp_found = _mock_chain(_mock_execute(data={"id": MOCK_COMPETENCY_ID}))

    mock_user_db = MagicMock()
    mock_user_db.table = MagicMock(return_value=expired_profile)

    mock_admin_db = MagicMock()
    mock_admin_db.table = MagicMock(return_value=comp_found)

    _user, _admin, _uid = _make_deps(mock_user_db, mock_admin_db)

    app.dependency_overrides[get_supabase_user] = _user
    app.dependency_overrides[get_supabase_admin] = _admin
    app.dependency_overrides[get_current_user_id] = _uid
    try:
        response = await client.post(
            "/api/assessment/start",
            json={"competency_slug": "communication"},
            headers={"Authorization": "Bearer test-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 402
    body = response.json()
    assert "detail" in body
    assert body["detail"]["code"] == "SUBSCRIPTION_REQUIRED"
    assert "message" in body["detail"]


# ── /answer paywall gate (SEC-ANSWER-01) ──────────────────────────────────────

MOCK_SESSION_ID = "00000000-0000-0000-0000-000000000099"
MOCK_QUESTION_ID = "00000000-0000-0000-0000-000000000088"

_IN_PROGRESS_SESSION = {
    "id": MOCK_SESSION_ID,
    "volunteer_id": MOCK_USER_ID,
    "status": "in_progress",
    "competency_id": MOCK_COMPETENCY_ID,
    "current_question_id": MOCK_QUESTION_ID,
    "answers": {},
    "answer_version": 0,
    "expires_at": None,
    "question_delivered_at": None,
    "gaming_flags": [],
    "gaming_penalty_multiplier": 1.0,
}


@pytest.mark.asyncio
async def test_submit_answer_blocked_when_expired(client):
    """Expired users receive HTTP 402 on POST /answer — SEC-ANSWER-01.

    Attack vector: start session while on trial, let subscription expire,
    keep submitting answers to get unlimited Gemini evaluations for free.
    """
    session_chain = _mock_chain(_mock_execute(data=_IN_PROGRESS_SESSION))
    expired_profile = _mock_chain(_mock_execute(data={"subscription_status": "expired"}))

    call_count = {"user": 0}

    def user_side_effect(table_name):
        call_count["user"] += 1
        if call_count["user"] == 1:
            return session_chain   # assessment_sessions lookup
        return expired_profile     # profiles subscription check

    mock_user_db = MagicMock()
    mock_user_db.table = MagicMock(side_effect=user_side_effect)

    mock_admin_db = MagicMock()
    mock_admin_db.table = MagicMock(return_value=_mock_chain(_mock_execute(data=None)))

    _user, _admin, _uid = _make_deps(mock_user_db, mock_admin_db)

    app.dependency_overrides[get_supabase_user] = _user
    app.dependency_overrides[get_supabase_admin] = _admin
    app.dependency_overrides[get_current_user_id] = _uid
    try:
        response = await client.post(
            "/api/assessment/answer",
            json={
                "session_id": MOCK_SESSION_ID,
                "question_id": MOCK_QUESTION_ID,
                "answer": "test answer",
                "response_time_ms": 3000,
            },
            headers={"Authorization": "Bearer test-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 402, f"Expired user should be blocked on /answer, got {response.status_code}: {response.text}"
    body = response.json()
    assert body["detail"]["code"] == "SUBSCRIPTION_REQUIRED"


@pytest.mark.asyncio
async def test_submit_answer_blocked_when_cancelled(client):
    """Cancelled users receive HTTP 402 on POST /answer — SEC-ANSWER-01."""
    session_chain = _mock_chain(_mock_execute(data=_IN_PROGRESS_SESSION))
    cancelled_profile = _mock_chain(_mock_execute(data={"subscription_status": "cancelled"}))

    call_count = {"user": 0}

    def user_side_effect(table_name):
        call_count["user"] += 1
        if call_count["user"] == 1:
            return session_chain    # assessment_sessions lookup
        return cancelled_profile    # profiles subscription check

    mock_user_db = MagicMock()
    mock_user_db.table = MagicMock(side_effect=user_side_effect)

    mock_admin_db = MagicMock()
    mock_admin_db.table = MagicMock(return_value=_mock_chain(_mock_execute(data=None)))

    _user, _admin, _uid = _make_deps(mock_user_db, mock_admin_db)

    app.dependency_overrides[get_supabase_user] = _user
    app.dependency_overrides[get_supabase_admin] = _admin
    app.dependency_overrides[get_current_user_id] = _uid
    try:
        response = await client.post(
            "/api/assessment/answer",
            json={
                "session_id": MOCK_SESSION_ID,
                "question_id": MOCK_QUESTION_ID,
                "answer": "test answer",
                "response_time_ms": 3000,
            },
            headers={"Authorization": "Bearer test-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 402, f"Cancelled user should be blocked on /answer, got {response.status_code}: {response.text}"
    body = response.json()
    assert body["detail"]["code"] == "SUBSCRIPTION_REQUIRED"
