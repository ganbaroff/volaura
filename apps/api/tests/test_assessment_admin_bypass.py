"""Unit tests for stale-session auto-expiry in start_assessment endpoint.

Strategy: use ASGI overrides and drive the endpoint to the point where
auto-expire logic runs. We return an existing in-progress session from
the conflict-check so the endpoint terminates with 409.

Call order inside start_assessment (with payment_enabled=False):
  1. get_competency_id(db_admin, slug)          → db_admin call #1
  2. GDPR policy_versions select                → db_admin call #2
  3. GDPR consent_events insert                 → db_admin call #3
  4. Zero-answer stale check (idx=0, <1h)       → db_admin call #4
  5. Zero-answer stale update (if rows)         → db_admin call #5
  6. 24h stale check                            → db_admin call #5/6
  7. 24h stale update (if rows)                 → db_admin call #6/7
  8. Conflict check db_user.assessment_sessions → db_user call #2
  9. ...session creation (not reached in most tests)
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin, get_supabase_user
from app.main import app

# ── constants ─────────────────────────────────────────────────────────────────
USER_ID = "00000000-aaaa-bbbb-cccc-111111111111"
STALE_SESSION_ID = str(uuid.uuid4())
COMPETENCY_UUID = "cccccccc-dddd-eeee-ffff-000000000000"

VALID_PAYLOAD = {
    "competency_slug": "communication",
    "automated_decision_consent": True,
}


# ── helpers ───────────────────────────────────────────────────────────────────


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


def _chainable(execute_return=None):
    m = MagicMock()
    for method in (
        "table",
        "select",
        "insert",
        "update",
        "upsert",
        "delete",
        "eq",
        "neq",
        "lt",
        "gt",
        "lte",
        "gte",
        "order",
        "limit",
        "single",
        "maybe_single",
        "rpc",
    ):
        getattr(m, method).return_value = m
    m.execute = AsyncMock(return_value=MagicMock(data=execute_return))
    return m


def _result(data):
    return MagicMock(data=data)


# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


# ── tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stale_cleanup_runs_for_non_admin():
    """Non-admin user with stale sessions → auto-expired before conflict check."""
    mock_admin = _chainable()
    mock_user = _chainable()

    stale_rows = [{"id": str(uuid.uuid4())}]

    admin_call_n = {"n": 0}

    async def admin_side_effect(*_a, **_kw):
        admin_call_n["n"] += 1
        if admin_call_n["n"] == 1:
            # get_competency_id
            return _result({"id": COMPETENCY_UUID})
        # Note: GDPR consent uses .is_() which is not in _chainable(),
        # so those calls run on a broken MagicMock chain and don't hit this side_effect.
        if admin_call_n["n"] == 2:
            # zero-answer stale check — no zero-answer stale rows
            return _result([])
        if admin_call_n["n"] == 3:
            # 24h stale check — return stale rows
            return _result(stale_rows)
        if admin_call_n["n"] == 4:
            # 24h stale update
            return _result(stale_rows)
        return _result(None)

    mock_admin.execute = AsyncMock(side_effect=admin_side_effect)

    user_call_n = {"n": 0}

    async def user_side_effect(*_a, **_kw):
        user_call_n["n"] += 1
        if user_call_n["n"] == 1:
            return _result({"is_platform_admin": False})
        if user_call_n["n"] == 2:
            return _result([{"id": STALE_SESSION_ID}])
        return _result(None)

    mock_user.execute = AsyncMock(side_effect=user_side_effect)

    app.dependency_overrides[get_supabase_admin] = _override_admin(mock_admin)
    app.dependency_overrides[get_supabase_user] = _override_user(mock_user)
    app.dependency_overrides[get_current_user_id] = _override_user_id()

    with patch("app.routers.assessment.logger") as mock_logger:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/assessment/start",
                json=VALID_PAYLOAD,
                headers={"Authorization": "Bearer fake"},
            )

    assert resp.status_code == 409
    assert admin_call_n["n"] == 4, (
        f"Expected 4 admin calls (competency + zero-stale + 24h-stale + update), got {admin_call_n['n']}"
    )
    mock_logger.info.assert_called_with(
        "Auto-expired stale sessions",
        user_id=USER_ID,
        count=len(stale_rows),
    )


@pytest.mark.asyncio
async def test_no_stale_sessions_skips_update():
    """Stale query returns empty → update must NOT be called."""
    mock_admin = _chainable()
    mock_user = _chainable()

    admin_call_n = {"n": 0}

    async def admin_side_effect(*_a, **_kw):
        admin_call_n["n"] += 1
        if admin_call_n["n"] == 1:
            # get_competency_id
            return _result({"id": COMPETENCY_UUID})
        # GDPR consent uses .is_() not in _chainable — skipped here
        if admin_call_n["n"] == 2:
            # zero-answer stale check — empty
            return _result([])
        if admin_call_n["n"] == 3:
            # 24h stale check — empty (no stale rows)
            return _result([])
        raise AssertionError(f"Unexpected admin call #{admin_call_n['n']}: update ran with no stale rows")

    mock_admin.execute = AsyncMock(side_effect=admin_side_effect)

    user_call_n = {"n": 0}

    async def user_side_effect(*_a, **_kw):
        user_call_n["n"] += 1
        if user_call_n["n"] == 1:
            return _result({"is_platform_admin": False})
        if user_call_n["n"] == 2:
            return _result([{"id": STALE_SESSION_ID}])
        return _result(None)

    mock_user.execute = AsyncMock(side_effect=user_side_effect)

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
    assert admin_call_n["n"] == 3, f"Expected 3 admin calls (competency + zero-stale + 24h-stale), got {admin_call_n['n']}"


@pytest.mark.asyncio
async def test_admin_with_stale_sessions_calls_update_and_logs():
    """Admin user with stale sessions → same auto-expire path, same log."""
    mock_admin = _chainable()
    mock_user = _chainable()

    stale_rows = [{"id": str(uuid.uuid4())}, {"id": str(uuid.uuid4())}]
    update_called = {"called": False}

    admin_call_n = {"n": 0}

    async def admin_side_effect(*_a, **_kw):
        admin_call_n["n"] += 1
        if admin_call_n["n"] == 1:
            return _result({"id": COMPETENCY_UUID})
        # GDPR consent uses .is_() not in _chainable — skipped
        if admin_call_n["n"] == 2:
            # zero-answer stale check — empty
            return _result([])
        if admin_call_n["n"] == 3:
            # 24h stale check — return stale rows
            return _result(stale_rows)
        if admin_call_n["n"] == 4:
            update_called["called"] = True
            return _result(stale_rows)
        return _result(None)

    mock_admin.execute = AsyncMock(side_effect=admin_side_effect)

    user_call_n = {"n": 0}

    async def user_side_effect(*_a, **_kw):
        user_call_n["n"] += 1
        if user_call_n["n"] == 1:
            return _result({"is_platform_admin": True})
        if user_call_n["n"] == 2:
            return _result([{"id": STALE_SESSION_ID}])
        return _result(None)

    mock_user.execute = AsyncMock(side_effect=user_side_effect)

    app.dependency_overrides[get_supabase_admin] = _override_admin(mock_admin)
    app.dependency_overrides[get_supabase_user] = _override_user(mock_user)
    app.dependency_overrides[get_current_user_id] = _override_user_id()

    with patch("app.routers.assessment.logger") as mock_logger:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/assessment/start",
                json=VALID_PAYLOAD,
                headers={"Authorization": "Bearer fake"},
            )

    assert resp.status_code == 409
    assert update_called["called"], "Stale update was never executed"
    assert admin_call_n["n"] == 4

    mock_logger.info.assert_called_with(
        "Auto-expired stale sessions",
        user_id=USER_ID,
        count=len(stale_rows),
    )


@pytest.mark.asyncio
async def test_stale_cutoff_is_24_hours():
    """The stale cutoff must be exactly 24 hours ago (±5s)."""
    mock_admin = _chainable()
    mock_user = _chainable()

    captured_lt_args: list[str] = []

    def capture_lt(col, val):
        if col == "created_at":
            captured_lt_args.append(val)
        return mock_admin

    mock_admin.lt = MagicMock(side_effect=capture_lt)

    admin_call_n = {"n": 0}

    async def admin_side_effect(*_a, **_kw):
        admin_call_n["n"] += 1
        if admin_call_n["n"] == 1:
            return _result({"id": COMPETENCY_UUID})
        if admin_call_n["n"] == 2:
            return _result([{"id": STALE_SESSION_ID}])
        return _result([])

    mock_admin.execute = AsyncMock(side_effect=admin_side_effect)

    user_call_n = {"n": 0}

    async def user_side_effect(*_a, **_kw):
        user_call_n["n"] += 1
        if user_call_n["n"] == 1:
            return _result({"is_platform_admin": False})
        if user_call_n["n"] == 2:
            return _result([{"id": STALE_SESSION_ID}])
        return _result(None)

    mock_user.execute = AsyncMock(side_effect=user_side_effect)

    app.dependency_overrides[get_supabase_admin] = _override_admin(mock_admin)
    app.dependency_overrides[get_supabase_user] = _override_user(mock_user)
    app.dependency_overrides[get_current_user_id] = _override_user_id()

    before = datetime.now(UTC) - timedelta(hours=24)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post(
            "/api/assessment/start",
            json=VALID_PAYLOAD,
            headers={"Authorization": "Bearer fake"},
        )

    after = datetime.now(UTC) - timedelta(hours=24)

    # Multiple lt("created_at", ...) calls: 1h tier (check+update) then 24h tier (check+update).
    # The 24h cutoff is the last unique value.
    assert len(captured_lt_args) >= 2, (
        f"Expected at least 2 lt('created_at', ...) calls, got {len(captured_lt_args)}"
    )

    cutoff_str = captured_lt_args[-1]  # last call = 24h cutoff (check or update)
    cutoff_dt = datetime.fromisoformat(cutoff_str)

    tolerance = timedelta(seconds=5)
    assert before - tolerance <= cutoff_dt <= after + tolerance, (
        f"Stale cutoff {cutoff_str!r} is not ~24 hours ago. "
        f"Expected between {before.isoformat()} and {after.isoformat()}."
    )
