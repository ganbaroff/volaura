"""Tests for subscription status boundary conditions.

Focuses on trial auto-expiry timezone handling.
Key bug risk: timezone-naive vs timezone-aware datetime comparison crashes.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.deps import get_supabase_admin, get_supabase_user, get_current_user_id

MOCK_USER_ID = "00000000-0000-0000-0000-000000000001"


def _mock_execute(data=None):
    result = MagicMock()
    result.data = data
    return result


def _mock_chain(execute_result):
    chain = MagicMock()
    chain.select.return_value = chain
    chain.update.return_value = chain
    chain.eq.return_value = chain
    chain.single.return_value = chain
    chain.maybe_single.return_value = chain
    chain.execute = AsyncMock(return_value=execute_result)
    return chain


def _make_status_row(subscription_status: str, trial_ends_at=None):
    return {
        "subscription_status": subscription_status,
        "trial_ends_at": trial_ends_at,
        "subscription_ends_at": None,
        "stripe_customer_id": None,
    }


# ── Trial auto-expiry ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_trial_expired_when_past_trial_end(client):
    """Trial with trial_ends_at in the past is auto-expired."""
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    row = _make_status_row("trial", trial_ends_at=past)

    select_result = _mock_chain(_mock_execute(data=row))
    update_result = _mock_chain(_mock_execute(data=[{}]))

    call_count = {"n": 0}

    def table_side_effect(name):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return select_result  # SELECT subscription_status
        return update_result  # UPDATE subscription_status → expired

    mock_admin_db = MagicMock()
    mock_admin_db.table = MagicMock(side_effect=table_side_effect)

    async def _admin():
        yield mock_admin_db

    async def _uid():
        return MOCK_USER_ID

    app.dependency_overrides[get_supabase_admin] = _admin
    app.dependency_overrides[get_current_user_id] = _uid
    try:
        response = await client.get(
            "/api/subscription/status",
            headers={"Authorization": "Bearer test-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "expired"


@pytest.mark.asyncio
async def test_trial_not_expired_when_future_trial_end(client):
    """Trial with trial_ends_at in the future stays 'trial'."""
    future = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    row = _make_status_row("trial", trial_ends_at=future)

    select_result = _mock_chain(_mock_execute(data=row))

    mock_admin_db = MagicMock()
    mock_admin_db.table = MagicMock(return_value=select_result)

    async def _admin():
        yield mock_admin_db

    async def _uid():
        return MOCK_USER_ID

    app.dependency_overrides[get_supabase_admin] = _admin
    app.dependency_overrides[get_current_user_id] = _uid
    try:
        response = await client.get(
            "/api/subscription/status",
            headers={"Authorization": "Bearer test-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "trial"


@pytest.mark.asyncio
async def test_trial_exactly_at_boundary_is_expired(client):
    """Trial ending 1 second ago is expired (comparison is strict <)."""
    past = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    row = _make_status_row("trial", trial_ends_at=past)

    select_result = _mock_chain(_mock_execute(data=row))
    update_result = _mock_chain(_mock_execute(data=[{}]))

    call_count = {"n": 0}

    def table_side_effect(name):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return select_result
        return update_result

    mock_admin_db = MagicMock()
    mock_admin_db.table = MagicMock(side_effect=table_side_effect)

    async def _admin():
        yield mock_admin_db

    async def _uid():
        return MOCK_USER_ID

    app.dependency_overrides[get_supabase_admin] = _admin
    app.dependency_overrides[get_current_user_id] = _uid
    try:
        response = await client.get(
            "/api/subscription/status",
            headers={"Authorization": "Bearer test-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "expired"


@pytest.mark.asyncio
async def test_trial_without_end_date_stays_trial(client):
    """Trial with no trial_ends_at set is not auto-expired."""
    row = _make_status_row("trial", trial_ends_at=None)

    select_result = _mock_chain(_mock_execute(data=row))

    mock_admin_db = MagicMock()
    mock_admin_db.table = MagicMock(return_value=select_result)

    async def _admin():
        yield mock_admin_db

    async def _uid():
        return MOCK_USER_ID

    app.dependency_overrides[get_supabase_admin] = _admin
    app.dependency_overrides[get_current_user_id] = _uid
    try:
        response = await client.get(
            "/api/subscription/status",
            headers={"Authorization": "Bearer test-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "trial"


@pytest.mark.asyncio
async def test_trial_z_suffix_iso_string_parsed_correctly(client):
    """ISO string with Z suffix from Supabase is parsed to UTC without TypeError crash."""
    past_z = "2026-03-01T00:00:00Z"  # definitively in the past
    row = _make_status_row("trial", trial_ends_at=past_z)

    select_result = _mock_chain(_mock_execute(data=row))
    update_result = _mock_chain(_mock_execute(data=[{}]))

    call_count = {"n": 0}

    def table_side_effect(name):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return select_result
        return update_result

    mock_admin_db = MagicMock()
    mock_admin_db.table = MagicMock(side_effect=table_side_effect)

    async def _admin():
        yield mock_admin_db

    async def _uid():
        return MOCK_USER_ID

    app.dependency_overrides[get_supabase_admin] = _admin
    app.dependency_overrides[get_current_user_id] = _uid
    try:
        # Must not raise TypeError: can't compare offset-naive and offset-aware datetimes
        response = await client.get(
            "/api/subscription/status",
            headers={"Authorization": "Bearer test-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "expired"
