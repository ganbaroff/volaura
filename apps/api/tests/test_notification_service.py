"""Unit tests for app.services.notification_service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.notification_service import (
    _PROFILE_VIEW_THROTTLE_HOURS,
    notify,
    notify_profile_viewed,
)

USER_ID = "u-0001"
ORG_ID = "org-0001"
ORG_NAME = "Test Corp"


def _mock_db(select_data=None):
    db = MagicMock()
    tbl = MagicMock()
    db.table.return_value = tbl

    insert_chain = MagicMock()
    insert_chain.execute = AsyncMock(return_value=MagicMock(data=[{"id": "n-1"}]))
    tbl.insert.return_value = insert_chain

    select_chain = MagicMock()
    select_chain.eq.return_value = select_chain
    select_chain.gte.return_value = select_chain
    select_chain.limit.return_value = select_chain
    select_chain.execute = AsyncMock(return_value=MagicMock(data=select_data or []))
    tbl.select.return_value = select_chain

    return db, tbl


# ── notify() ──────────────────────────────────────────────────────────────────


class TestNotify:
    @pytest.mark.asyncio
    async def test_inserts_notification(self):
        db, tbl = _mock_db()
        await notify(db, USER_ID, "badge_earned", "Gold!", body="Comm Gold")

        tbl.insert.assert_called_once()
        payload = tbl.insert.call_args[0][0]
        assert payload["user_id"] == USER_ID
        assert payload["type"] == "badge_earned"
        assert payload["title"] == "Gold!"
        assert payload["body"] == "Comm Gold"

    @pytest.mark.asyncio
    async def test_optional_fields_default_none(self):
        db, tbl = _mock_db()
        await notify(db, USER_ID, "test", "Title")

        payload = tbl.insert.call_args[0][0]
        assert payload["body"] is None
        assert payload["reference_id"] is None

    @pytest.mark.asyncio
    async def test_reference_id_passed(self):
        db, tbl = _mock_db()
        await notify(db, USER_ID, "test", "T", reference_id="ref-42")

        payload = tbl.insert.call_args[0][0]
        assert payload["reference_id"] == "ref-42"

    @pytest.mark.asyncio
    async def test_never_raises_on_db_error(self):
        db, tbl = _mock_db()
        insert_chain = MagicMock()
        insert_chain.execute = AsyncMock(side_effect=Exception("db down"))
        tbl.insert.return_value = insert_chain

        await notify(db, USER_ID, "test", "T")  # should not raise

    @pytest.mark.asyncio
    async def test_returns_none(self):
        db, _ = _mock_db()
        result = await notify(db, USER_ID, "test", "T")
        assert result is None


# ── notify_profile_viewed() ──────────────────────────────────────────────────


class TestNotifyProfileViewed:
    @pytest.mark.asyncio
    async def test_sends_when_no_recent(self):
        db, tbl = _mock_db(select_data=[])
        result = await notify_profile_viewed(db, USER_ID, ORG_ID, ORG_NAME)

        assert result is True
        tbl.insert.assert_called_once()
        payload = tbl.insert.call_args[0][0]
        assert payload["type"] == "org_view"
        assert payload["user_id"] == USER_ID
        assert payload["reference_id"] == ORG_ID
        assert ORG_NAME in payload["title"]

    @pytest.mark.asyncio
    async def test_throttled_when_recent_exists(self):
        db, tbl = _mock_db(select_data=[{"id": "existing"}])
        result = await notify_profile_viewed(db, USER_ID, ORG_ID, ORG_NAME)

        assert result is False
        tbl.insert.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_false_on_select_error(self):
        db, tbl = _mock_db()
        select_chain = MagicMock()
        select_chain.eq.return_value = select_chain
        select_chain.gte.return_value = select_chain
        select_chain.limit.return_value = select_chain
        select_chain.execute = AsyncMock(side_effect=Exception("timeout"))
        tbl.select.return_value = select_chain

        result = await notify_profile_viewed(db, USER_ID, ORG_ID, ORG_NAME)
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_on_insert_error(self):
        db, tbl = _mock_db(select_data=[])
        insert_chain = MagicMock()
        insert_chain.execute = AsyncMock(side_effect=Exception("constraint"))
        tbl.insert.return_value = insert_chain

        result = await notify_profile_viewed(db, USER_ID, ORG_ID, ORG_NAME)
        assert result is False

    @pytest.mark.asyncio
    async def test_throttle_window_uses_correct_hours(self):
        assert _PROFILE_VIEW_THROTTLE_HOURS == 24

    @pytest.mark.asyncio
    async def test_throttle_check_queries_correct_filters(self):
        db, tbl = _mock_db(select_data=[])
        await notify_profile_viewed(db, USER_ID, ORG_ID, ORG_NAME)

        select_chain = tbl.select.return_value
        eq_calls = [c.args for c in select_chain.eq.call_args_list]
        assert ("user_id", USER_ID) in eq_calls
        assert ("type", "org_view") in eq_calls
        assert ("reference_id", ORG_ID) in eq_calls
