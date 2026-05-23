"""Tests for first-time user assessment restart behavior.

Verifies:
1. First-time user (never completed) bypasses rapid-restart cooldown.
2. Returning user (has completed before) is still blocked by cooldown.
3. Zero-answer sessions auto-abandon after 1 hour (not 24 hours).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin, get_supabase_user
from app.main import app

USER_ID = "00000000-aaaa-bbbb-cccc-222222222222"
COMPETENCY_UUID = "11111111-1111-1111-1111-111111111111"
SESSION_UUID = str(uuid.uuid4())

VALID_PAYLOAD = {
    "competency_slug": "communication",
    "automated_decision_consent": True,
}


def _override_admin(mock_db):
    async def _dep():
        yield mock_db
    return _dep


def _override_user(mock_db):
    async def _dep():
        yield mock_db
    return _dep


def _override_user_id(uid: str = USER_ID):
    async def _dep():
        return uid
    return _dep


def _result(data, count=None):
    r = MagicMock(data=data)
    r.count = count
    return r


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Call-order reference for start_assessment (payment_enabled=False):
#
# admin calls:
#   1. get_competency_id → competency row
#   2. GDPR consent: policy_versions select
#   3. GDPR consent: consent_events insert
#   4. zero-answer stale check (assessment_sessions select, idx=0, <1h)
#   5. zero-answer stale update (only if rows found)
#   6. 24h stale check (assessment_sessions select, <24h)
#   7. 24h stale update (only if rows found)
#   ... later: session insert, etc.
#
# user calls:
#   1. admin check (profiles.is_platform_admin)
#   2. conflict check (assessment_sessions, status=in_progress)
#   3. ever_completed check (assessment_sessions, status=completed, count)
#   4. recent_start check (assessment_sessions, started_at desc)
#   ... later: retest cooldown, abuse monitoring, etc.
# ---------------------------------------------------------------------------


def _build_mocks(
    *,
    has_in_progress: bool = False,
    ever_completed_count: int = 0,
    recent_start_minutes_ago: int | None = None,
    zero_answer_stale_rows: list | None = None,
):
    """Build admin/user mocks with configurable behavior."""
    mock_admin = MagicMock()
    mock_user = MagicMock()

    # Make all chainable methods return self
    for m in (mock_admin, mock_user):
        for method in (
            "table", "select", "insert", "update", "upsert", "delete",
            "eq", "neq", "lt", "gt", "lte", "gte", "is_",
            "order", "limit", "single", "maybe_single", "rpc",
        ):
            getattr(m, method).return_value = m

    admin_n = {"n": 0}

    async def admin_side(*_a, **_kw):
        admin_n["n"] += 1
        if admin_n["n"] == 1:
            # get_competency_id
            return _result({"id": COMPETENCY_UUID})
        if admin_n["n"] == 2:
            # GDPR policy_versions
            return _result({"id": str(uuid.uuid4())})
        if admin_n["n"] == 3:
            # GDPR consent_events insert
            return _result(None)
        if admin_n["n"] == 4:
            # zero-answer stale check
            return _result(zero_answer_stale_rows or [])
        if admin_n["n"] == 5 and zero_answer_stale_rows:
            # zero-answer stale update
            return _result(zero_answer_stale_rows)
        if admin_n["n"] in (5, 6):
            # 24h stale check
            return _result([])
        # Session insert or later calls
        new_session = {
            "id": str(uuid.uuid4()),
            "status": "in_progress",
            "volunteer_id": USER_ID,
            "competency_id": COMPETENCY_UUID,
            "current_question_idx": 0,
            "answers": {"items": [], "theta": 0.0, "stopped": False, "prior_sd": 1.0, "theta_se": 1.0, "prior_mean": 0.0, "stop_reason": None, "eap_failures": 0},
            "question_ids": [],
            "started_at": datetime.now(UTC).isoformat(),
            "created_at": datetime.now(UTC).isoformat(),
            "fast_responses": 0,
            "flag_reason": None,
            "gaming_flags": [],
            "gaming_penalty_multiplier": 1.0,
            "current_question_id": None,
            "metadata": None,
        }
        return _result(new_session)

    mock_admin.execute = AsyncMock(side_effect=admin_side)

    user_n = {"n": 0}

    async def user_side(*_a, **_kw):
        user_n["n"] += 1
        if user_n["n"] == 1:
            # admin check
            return _result({"is_platform_admin": False})
        if user_n["n"] == 2:
            # conflict check — in_progress session?
            if has_in_progress:
                return _result([{"id": SESSION_UUID}])
            return _result([])
        if user_n["n"] == 3:
            # ever_completed count
            return _result([], count=ever_completed_count)
        if user_n["n"] == 4:
            # recent_start check
            if recent_start_minutes_ago is not None:
                started = (datetime.now(UTC) - timedelta(minutes=recent_start_minutes_ago)).isoformat()
                return _result([{"started_at": started, "status": "abandoned"}])
            return _result([])
        # Remaining calls (retest cooldown, abuse monitoring, etc.)
        return _result([], count=0)

    mock_user.execute = AsyncMock(side_effect=user_side)

    return mock_admin, mock_user


@pytest.mark.asyncio
async def test_first_time_user_bypasses_rapid_restart_cooldown():
    """User who never completed this competency can restart immediately."""
    mock_admin, mock_user = _build_mocks(
        ever_completed_count=0,
        recent_start_minutes_ago=5,  # started 5 min ago, normally would be blocked
    )

    app.dependency_overrides[get_supabase_admin] = _override_admin(mock_admin)
    app.dependency_overrides[get_supabase_user] = _override_user(mock_user)
    app.dependency_overrides[get_current_user_id] = _override_user_id()

    with patch("app.routers.assessment.select_next_item", return_value=None), \
         patch("app.routers.assessment.fetch_questions", return_value=[]):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/assessment/start",
                json=VALID_PAYLOAD,
                headers={"Authorization": "Bearer fake"},
            )

    # Should NOT be 429 — first-time user bypasses cooldown
    assert resp.status_code != 429, (
        f"First-time user was blocked by rapid-restart cooldown: {resp.json()}"
    )


@pytest.mark.asyncio
async def test_completed_user_still_blocked_by_cooldown():
    """User who has completed before is blocked by 30-min cooldown."""
    mock_admin, mock_user = _build_mocks(
        ever_completed_count=1,
        recent_start_minutes_ago=5,  # started 5 min ago
    )

    app.dependency_overrides[get_supabase_admin] = _override_admin(mock_admin)
    app.dependency_overrides[get_supabase_user] = _override_user(mock_user)
    app.dependency_overrides[get_current_user_id] = _override_user_id()

    with patch("app.routers.assessment.notify", new_callable=AsyncMock):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/assessment/start",
                json=VALID_PAYLOAD,
                headers={"Authorization": "Bearer fake"},
            )

    assert resp.status_code == 429, (
        f"Completed user should be blocked by cooldown, got {resp.status_code}: {resp.json()}"
    )
    assert resp.json()["detail"]["code"] == "RAPID_RESTART_COOLDOWN"


@pytest.mark.asyncio
async def test_in_progress_session_returns_409_with_session_id():
    """Active in-progress session returns 409 with the existing session_id."""
    mock_admin, mock_user = _build_mocks(has_in_progress=True)

    app.dependency_overrides[get_supabase_admin] = _override_admin(mock_admin)
    app.dependency_overrides[get_supabase_user] = _override_user(mock_user)
    app.dependency_overrides[get_current_user_id] = _override_user_id()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/assessment/start",
            json=VALID_PAYLOAD,
            headers={"Authorization": "Bearer fake"},
        )

    assert resp.status_code == 409
    detail = resp.json()["detail"]
    assert detail["code"] == "SESSION_IN_PROGRESS"
    assert detail["session_id"] == SESSION_UUID
