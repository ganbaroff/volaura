"""Integration tests for POST /api/profiles/{username}/view.

Acceptance criteria:
  1. Org viewer → volunteer's profile → notification inserted (204)
  2. Non-org viewer (volunteer) → silently returns 204, no notification
  3. Org viewer within 24h dedup window → 204, no second notification
  4. Org viewing their own profile (self-view) → 204, no notification
  5. Volunteer not found / private → 204, no notification

All Supabase calls are mocked — tests run offline.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.deps import get_supabase_admin, get_current_user_id

ORG_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
VOLUNTEER_ID = "11111111-2222-3333-4444-555555555555"
VOLUNTEER_USERNAME = "alice"


# ── Dependency helpers ────────────────────────────────────────────────────────

def _admin_override(db):
    async def _dep():
        yield db
    return _dep


def _uid_override(uid: str):
    async def _dep():
        return uid
    return _dep


# ── Mock DB factory ───────────────────────────────────────────────────────────

def _build_view_mock_db(
    caller_account_type: str = "organization",
    volunteer_exists: bool = True,
    is_self_view: bool = False,
    dedup_exists: bool = False,
):
    """Build a non-circular mock DB for the profile view endpoint.

    The endpoint makes these calls in order:
      1. profiles.select(caller) — account_type check
      2. profiles.select(volunteer) — volunteer lookup
      3. notifications.select(dedup) — 24h dedup check
      4. notifications.insert(notification) — fire notification

    Using a per-table call-counter so sequential calls to the same table
    return different results without circular mock clobbering.
    """
    org_display_name = "Tech Corp"

    # Track how many times each table mock has had execute() called
    call_counts: dict[str, int] = {}
    inserted_notifications: list[dict] = []

    def make_table_mock(table_name: str) -> MagicMock:
        t = MagicMock()
        call_counts.setdefault(table_name, 0)

        async def _execute_for_profiles(*_args, **_kwargs):
            n = call_counts["profiles"]
            call_counts["profiles"] += 1
            if n == 0:
                # First call: caller account_type check
                if caller_account_type == "none":
                    return MagicMock(data=None)
                return MagicMock(data={
                    "account_type": caller_account_type,
                    "display_name": org_display_name if caller_account_type == "organization" else None,
                    "username": "techcorp" if caller_account_type == "organization" else "volunteer_viewer",
                })
            else:
                # Second call: volunteer lookup
                if not volunteer_exists:
                    return MagicMock(data=None)
                volunteer_id = ORG_ID if is_self_view else VOLUNTEER_ID
                return MagicMock(data={"id": volunteer_id, "display_name": "Alice"})

        async def _execute_for_notifications(*_args, **_kwargs):
            n = call_counts["notifications"]
            call_counts["notifications"] += 1
            if n == 0:
                # Dedup check
                return MagicMock(data=[{"id": "existing-notif"}] if dedup_exists else [])
            else:
                # Insert notification
                inserted_notifications.append({"inserted": True})
                return MagicMock(data=[{"id": "new-notif-id"}])

        if table_name == "profiles":
            # Wire all fluent chain methods to return t itself, execute to async side_effect
            t.select.return_value = t
            t.eq.return_value = t
            t.maybe_single.return_value = t
            t.execute = AsyncMock(side_effect=_execute_for_profiles)
        elif table_name == "notifications":
            t.select.return_value = t
            t.insert.return_value = t
            t.eq.return_value = t
            t.gte.return_value = t
            t.execute = AsyncMock(side_effect=_execute_for_notifications)
        else:
            # Unexpected table — return empty to avoid test hangs
            t.execute = AsyncMock(return_value=MagicMock(data=None))

        return t

    db = MagicMock()
    db.table = MagicMock(side_effect=make_table_mock)
    return db, inserted_notifications


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_org_view_sends_notification():
    """Org viewer → public volunteer → notification inserted, 204 returned."""
    db, inserted = _build_view_mock_db(
        caller_account_type="organization",
        volunteer_exists=True,
        dedup_exists=False,
    )

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_ID)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            f"/api/profiles/{VOLUNTEER_USERNAME}/view",
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 204
    assert len(inserted) == 1, "Notification must be inserted for org view"


@pytest.mark.asyncio
async def test_non_org_viewer_silently_204():
    """Volunteer viewing another volunteer → 204, zero notifications."""
    db, inserted = _build_view_mock_db(
        caller_account_type="volunteer",
        volunteer_exists=True,
        dedup_exists=False,
    )

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_ID)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            f"/api/profiles/{VOLUNTEER_USERNAME}/view",
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 204
    assert len(inserted) == 0, "Non-org viewer must not trigger notification"


@pytest.mark.asyncio
async def test_org_view_dedup_within_24h():
    """Org already notified volunteer within 24h → 204, no duplicate notification."""
    db, inserted = _build_view_mock_db(
        caller_account_type="organization",
        volunteer_exists=True,
        dedup_exists=True,
    )

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_ID)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            f"/api/profiles/{VOLUNTEER_USERNAME}/view",
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 204
    assert len(inserted) == 0, "Dedup: second notification within 24h must be suppressed"


@pytest.mark.asyncio
async def test_self_view_suppressed():
    """Org viewing their own profile → 204, no notification."""
    db, inserted = _build_view_mock_db(
        caller_account_type="organization",
        volunteer_exists=True,
        is_self_view=True,
        dedup_exists=False,
    )

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    # Caller ID == volunteer ID (self-view)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_ID)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            f"/api/profiles/{VOLUNTEER_USERNAME}/view",
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 204
    assert len(inserted) == 0, "Self-view must not produce a notification"


@pytest.mark.asyncio
async def test_volunteer_not_found_silently_204():
    """Volunteer doesn't exist or set profile private → 204, no notification."""
    db, inserted = _build_view_mock_db(
        caller_account_type="organization",
        volunteer_exists=False,
        dedup_exists=False,
    )

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_ID)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            f"/api/profiles/ghost_user/view",
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 204
    assert len(inserted) == 0, "Missing volunteer must not produce a notification"


@pytest.mark.asyncio
async def test_unauthenticated_returns_401():
    """No auth header → 401 from get_current_user_id before endpoint logic.

    get_supabase_admin is overridden to prevent real Supabase client creation.
    get_current_user_id still runs (not overridden) and returns 401 for missing Bearer.
    """
    mock_admin = MagicMock()
    mock_admin.auth = MagicMock()
    app.dependency_overrides[get_supabase_admin] = _admin_override(mock_admin)

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(f"/api/profiles/{VOLUNTEER_USERNAME}/view")
        assert resp.status_code in (401, 403), f"Expected auth error, got {resp.status_code}"
    finally:
        app.dependency_overrides.clear()
