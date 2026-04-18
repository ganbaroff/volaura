"""Unit tests for the admin stale-session bypass in the start_assessment endpoint.

Strategy: use ASGI overrides (same pattern as test_assessment_router.py) and drive
the endpoint to the point where bypass logic runs.  We intentionally return an existing
in-progress session from the conflict-check so the endpoint terminates with 409 — this
means we never need to mock the full session-creation path, keeping fixtures minimal.

Call order inside start_assessment (with payment_enabled=False):
  1. get_competency_id(db_admin, slug)          → db_admin call #1
  2. Admin check  db_user.profiles              → db_user call #1
  3. Stale check  db_admin.assessment_sessions  → db_admin call #2  (admin only)
  4. Stale update db_admin.assessment_sessions  → db_admin call #3  (admin + stale rows)
  5. Conflict check db_user.assessment_sessions → db_user call #2
  6. ...session creation (not reached in most tests)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
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
    """
    Build a Supabase-style fluent mock.

    All chaining methods return *self* so arbitrary chains work.
    `execute` is an AsyncMock whose return_value can be set per call
    using side_effect after construction.
    """
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
    """Ensure dependency overrides are cleaned up after every test."""
    yield
    app.dependency_overrides.clear()


# ── tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_admin_check_exception_treated_as_non_admin():
    """If the profiles query throws, is_admin=False (fail-closed) — no stale cleanup.

    The endpoint catches the exception inside the admin-check try/except, sets
    is_admin=False, and continues.  Stale check + update (admin calls #2 and #3)
    must NOT be called.  The subsequent user calls (conflict check) also use
    db_user, so we let those return a 409 to terminate the request cleanly.
    """
    mock_admin = _chainable()
    mock_user = _chainable()

    admin_call_n = {"n": 0}

    async def admin_side_effect(*_a, **_kw):
        admin_call_n["n"] += 1
        if admin_call_n["n"] == 1:
            # get_competency_id → returns the competency UUID
            return _result({"id": COMPETENCY_UUID})
        # Stale check / update must not be reached — fail loudly if they are
        raise AssertionError(
            f"Unexpected admin execute call #{admin_call_n['n']}: stale bypass ran despite admin check throwing"
        )

    mock_admin.execute = AsyncMock(side_effect=admin_side_effect)

    user_call_n = {"n": 0}

    async def user_side_effect(*_a, **_kw):
        user_call_n["n"] += 1
        if user_call_n["n"] == 1:
            # Admin-check profiles query: raise to simulate DB failure.
            # The endpoint's try/except catches this and sets is_admin=False.
            raise RuntimeError("DB connection lost")
        if user_call_n["n"] == 2:
            # Conflict check after fail-closed admin check: return existing session → 409
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

    # Fail-closed: admin check threw → is_admin=False → conflict check hits the
    # seeded existing session → 409 (not 500).
    assert resp.status_code == 409, (
        f"Expected 409 (conflict check after fail-closed admin), got {resp.status_code}: {resp.text}"
    )
    # Only get_competency_id hit the admin client — no stale logic ran
    assert admin_call_n["n"] == 1, (
        f"Expected only get_competency_id admin call (n=1), got n={admin_call_n['n']}. "
        "Stale update should not run when admin check throws."
    )


@pytest.mark.asyncio
async def test_non_admin_skips_stale_cleanup():
    """is_platform_admin=False → stale check and update never called.

    Stale sessions remain intact; the endpoint proceeds to conflict check
    and returns 409 (we seed an existing in-progress session to stop there).
    """
    mock_admin = _chainable()
    mock_user = _chainable()

    admin_call_n = {"n": 0}

    async def admin_side_effect(*_a, **_kw):
        admin_call_n["n"] += 1
        if admin_call_n["n"] == 1:
            return _result({"id": COMPETENCY_UUID})
        # Any further admin call = unexpected stale logic
        return _result(None)

    mock_admin.execute = AsyncMock(side_effect=admin_side_effect)

    user_call_n = {"n": 0}

    async def user_side_effect(*_a, **_kw):
        user_call_n["n"] += 1
        if user_call_n["n"] == 1:
            # Admin check: not an admin
            return _result({"is_platform_admin": False})
        if user_call_n["n"] == 2:
            # Conflict check: return existing session → 409
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
    # Only get_competency_id hit admin client — no stale check/update
    assert admin_call_n["n"] == 1, f"Non-admin triggered admin stale calls (n={admin_call_n['n']})"


@pytest.mark.asyncio
async def test_admin_no_stale_sessions_skips_update():
    """Admin user, but stale query returns empty → update must NOT be called.

    Call sequence: get_competency_id (admin #1) → stale check (admin #2, empty)
    → conflict check (user #2, existing session) → 409.
    No admin call #3 (update).
    """
    mock_admin = _chainable()
    mock_user = _chainable()

    admin_call_n = {"n": 0}

    async def admin_side_effect(*_a, **_kw):
        admin_call_n["n"] += 1
        if admin_call_n["n"] == 1:
            return _result({"id": COMPETENCY_UUID})
        if admin_call_n["n"] == 2:
            # Stale check: empty
            return _result([])
        # Call #3 would be the update — should not happen
        raise AssertionError("Unexpected admin execute call #3: stale update ran with no stale rows")

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

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/assessment/start",
            json=VALID_PAYLOAD,
            headers={"Authorization": "Bearer fake"},
        )

    assert resp.status_code == 409
    assert admin_call_n["n"] == 2, (
        f"Expected exactly 2 admin calls (get_competency_id + stale_check), got {admin_call_n['n']}"
    )


@pytest.mark.asyncio
async def test_admin_with_stale_sessions_calls_update_and_logs():
    """Admin user with stale sessions → update called with correct filters + logger fires.

    Verifies:
    - update() is chained with .eq("status", "in_progress")
    - logger.info called with "Admin bypass: expired stale sessions"
    - count= kwarg matches len(stale rows)
    - After expiry the conflict check proceeds normally (409 here due to seeded conflict)
    """
    mock_admin = _chainable()
    mock_user = _chainable()

    stale_rows = [{"id": str(uuid.uuid4())}, {"id": str(uuid.uuid4())}]
    update_called = {"called": False}

    admin_call_n = {"n": 0}

    async def admin_side_effect(*_a, **_kw):
        admin_call_n["n"] += 1
        if admin_call_n["n"] == 1:
            return _result({"id": COMPETENCY_UUID})
        if admin_call_n["n"] == 2:
            # Stale check: return 2 stale sessions
            return _result(stale_rows)
        if admin_call_n["n"] == 3:
            # Stale update
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
    assert admin_call_n["n"] == 3, (
        f"Expected 3 admin calls (competency + stale_check + update), got {admin_call_n['n']}"
    )

    # Logger must fire with the right message and count
    mock_logger.info.assert_called_once_with(
        "Admin bypass: expired stale sessions",
        user_id=USER_ID,
        count=len(stale_rows),
    )


@pytest.mark.asyncio
async def test_non_admin_stale_sessions_cause_409():
    """Non-admin with a real in-progress session gets 409; stale cleanup does NOT run.

    This confirms the bypass is admin-only: regular users hit the conflict gate.
    """
    mock_admin = _chainable()
    mock_user = _chainable()

    async def admin_side_effect(*_a, **_kw):
        return _result({"id": COMPETENCY_UUID})

    mock_admin.execute = AsyncMock(side_effect=admin_side_effect)

    user_call_n = {"n": 0}
    update_attempted = {"called": False}

    async def user_side_effect(*_a, **_kw):
        user_call_n["n"] += 1
        if user_call_n["n"] == 1:
            return _result({"is_platform_admin": False})
        if user_call_n["n"] == 2:
            # Conflict check: existing active session
            return _result([{"id": STALE_SESSION_ID}])
        return _result(None)

    mock_user.execute = AsyncMock(side_effect=user_side_effect)

    # Patch update at router level to detect unexpected calls
    original_update = mock_admin.update

    def guarded_update(*a, **kw):
        update_attempted["called"] = True
        return original_update(*a, **kw)

    mock_admin.update = MagicMock(side_effect=guarded_update)

    app.dependency_overrides[get_supabase_admin] = _override_admin(mock_admin)
    app.dependency_overrides[get_supabase_user] = _override_user(mock_user)
    app.dependency_overrides[get_current_user_id] = _override_user_id()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/assessment/start",
            json=VALID_PAYLOAD,
            headers={"Authorization": "Bearer fake"},
        )

    assert resp.status_code == 409, f"Expected 409 for non-admin conflict, got {resp.status_code}"
    assert not update_attempted["called"], "db_admin.update was called for non-admin — stale bypass leaked"
    detail = resp.json()["detail"]
    assert detail["code"] == "SESSION_IN_PROGRESS"


@pytest.mark.asyncio
async def test_stale_cutoff_is_24_hours():
    """The stale cutoff passed to the lt() filter must be exactly 24 hours ago (±5s).

    We capture the `lt` argument on the admin mock and verify it falls within
    the expected range, confirming no misconfiguration (e.g. 1 hour or 7 days).
    """
    mock_admin = _chainable()
    mock_user = _chainable()

    captured_lt_args: list[str] = []

    # Intercept the `lt` call to capture the cutoff value
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
            # Stale check: one stale row to trigger update path
            return _result([{"id": STALE_SESSION_ID}])
        return _result([])

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

    before = datetime.utcnow() - timedelta(hours=24)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post(
            "/api/assessment/start",
            json=VALID_PAYLOAD,
            headers={"Authorization": "Bearer fake"},
        )

    after = datetime.utcnow() - timedelta(hours=24)

    assert len(captured_lt_args) >= 1, "lt('created_at', ...) was never called — stale check did not run"

    # Both stale-check and stale-update share the same cutoff isoformat string;
    # verify at least the first captured value is within the 24-hour window ±5s tolerance.
    cutoff_str = captured_lt_args[0]
    cutoff_dt = datetime.fromisoformat(cutoff_str)

    tolerance = timedelta(seconds=5)
    assert before - tolerance <= cutoff_dt <= after + tolerance, (
        f"Stale cutoff {cutoff_str!r} is not ~24 hours ago. "
        f"Expected between {before.isoformat()} and {after.isoformat()}."
    )
