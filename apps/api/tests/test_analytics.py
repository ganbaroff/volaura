"""Unit tests for analytics service + router schema.

Covers: TrackEventRequest validation, track_event payload construction,
fire-and-forget error swallowing.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from app.routers.analytics import TrackEventRequest
from app.services.analytics import track_event

# ── Schema validation ──────────────────────────────────────────────────────


class TestTrackEventRequest:
    def test_valid_minimal(self):
        r = TrackEventRequest(event_name="page_view")
        assert r.event_name == "page_view"
        assert r.properties is None
        assert r.session_id is None
        assert r.locale is None
        assert r.platform == "web"

    def test_valid_full(self):
        r = TrackEventRequest(
            event_name="assessment_completed",
            properties={"score": 85},
            session_id="sess-123",
            locale="az",
            platform="ios",
        )
        assert r.properties == {"score": 85}
        assert r.session_id == "sess-123"
        assert r.locale == "az"
        assert r.platform == "ios"

    def test_missing_event_name_raises(self):
        with pytest.raises(ValidationError):
            TrackEventRequest()

    def test_empty_event_name_allowed(self):
        r = TrackEventRequest(event_name="")
        assert r.event_name == ""

    def test_properties_must_be_dict_or_none(self):
        with pytest.raises(ValidationError):
            TrackEventRequest(event_name="x", properties="not-a-dict")

    def test_strict_rejects_int_for_string(self):
        with pytest.raises(ValidationError):
            TrackEventRequest(event_name=123)


# ── track_event service ───────────────────────────────────────────────────


def _mock_db(side_effect=None):
    db = MagicMock()
    table = MagicMock()
    insert = MagicMock()
    execute = AsyncMock(side_effect=side_effect)
    insert.execute = execute
    table.insert.return_value = insert
    db.table.return_value = table
    return db, table, insert, execute


class TestTrackEvent:
    @pytest.mark.asyncio
    async def test_basic_payload(self):
        db, table, insert, _ = _mock_db()
        await track_event(db=db, user_id="u1", event_name="page_view")
        table.insert.assert_called_once()
        payload = table.insert.call_args[0][0]
        assert payload["user_id"] == "u1"
        assert payload["event_name"] == "page_view"
        assert payload["properties"] == {}
        assert payload["platform"] == "web"
        assert "session_id" not in payload
        assert "locale" not in payload

    @pytest.mark.asyncio
    async def test_optional_fields_included(self):
        db, table, insert, _ = _mock_db()
        await track_event(
            db=db,
            user_id="u2",
            event_name="click",
            properties={"btn": "start"},
            session_id="s1",
            locale="en",
            platform="android",
        )
        payload = table.insert.call_args[0][0]
        assert payload["session_id"] == "s1"
        assert payload["locale"] == "en"
        assert payload["platform"] == "android"
        assert payload["properties"] == {"btn": "start"}

    @pytest.mark.asyncio
    async def test_none_properties_becomes_empty_dict(self):
        db, table, _, _ = _mock_db()
        await track_event(db=db, user_id="u3", event_name="ev", properties=None)
        payload = table.insert.call_args[0][0]
        assert payload["properties"] == {}

    @pytest.mark.asyncio
    async def test_db_failure_swallowed(self):
        db, _, _, _ = _mock_db(side_effect=Exception("connection lost"))
        await track_event(db=db, user_id="u4", event_name="boom")

    @pytest.mark.asyncio
    async def test_db_failure_logs_warning(self):
        db, _, _, _ = _mock_db(side_effect=RuntimeError("timeout"))
        with patch("app.services.analytics.logger") as mock_logger:
            await track_event(db=db, user_id="u5", event_name="fail")
            mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_id_none_excluded_from_payload(self):
        db, table, _, _ = _mock_db()
        await track_event(db=db, user_id="u6", event_name="ev", session_id=None)
        payload = table.insert.call_args[0][0]
        assert "session_id" not in payload

    @pytest.mark.asyncio
    async def test_locale_none_excluded_from_payload(self):
        db, table, _, _ = _mock_db()
        await track_event(db=db, user_id="u7", event_name="ev", locale=None)
        payload = table.insert.call_args[0][0]
        assert "locale" not in payload

    @pytest.mark.asyncio
    async def test_calls_analytics_events_table(self):
        db, _, _, _ = _mock_db()
        await track_event(db=db, user_id="u8", event_name="test")
        db.table.assert_called_once_with("analytics_events")
