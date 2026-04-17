"""Unit tests for app.services.ghosting_grace — worker, candidates, email fetch."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ghosting_grace import (
    BATCH_SIZE,
    GRACE_WINDOW_HOURS,
    _fetch_candidates,
    _fetch_email,
    process_ghosting_grace,
)


class TestConstants:
    def test_grace_window_hours(self):
        assert GRACE_WINDOW_HOURS == 48

    def test_batch_size(self):
        assert BATCH_SIZE == 50

    def test_grace_window_is_int(self):
        assert isinstance(GRACE_WINDOW_HOURS, int)

    def test_batch_size_is_int(self):
        assert isinstance(BATCH_SIZE, int)


def _chain_mock(data=None):
    """Build a MagicMock that supports Supabase chaining with async .execute()."""
    chain = MagicMock()
    chain.select.return_value = chain
    chain.lt.return_value = chain
    chain.is_.return_value = chain
    chain.limit.return_value = chain
    chain.in_.return_value = chain
    chain.eq.return_value = chain
    chain.update.return_value = chain
    chain.execute = AsyncMock(return_value=MagicMock(data=data if data is not None else []))
    return chain


def _make_db(profiles=None, completed_sessions=None):
    db = MagicMock()

    profile_chain = _chain_mock(profiles)
    session_chain = _chain_mock(completed_sessions)

    def table_router(name):
        if name == "assessment_sessions":
            return session_chain
        return profile_chain

    db.table = MagicMock(side_effect=table_router)
    db.auth = MagicMock()
    return db


def _make_candidate(uid="u1", display_name="Test User", username="testuser"):
    return {"id": uid, "display_name": display_name, "username": username}


def _make_process_db():
    """DB mock for process_ghosting_grace tests (update chain only)."""
    db = MagicMock()
    update_chain = _chain_mock()
    db.table = MagicMock(return_value=update_chain)
    return db, update_chain


class TestFetchCandidates:
    @pytest.mark.asyncio
    async def test_no_profiles_returns_empty(self):
        db = _make_db(profiles=[])
        result = await _fetch_candidates(db)
        assert result == []

    @pytest.mark.asyncio
    async def test_none_data_returns_empty(self):
        db = _make_db(profiles=None)
        result = await _fetch_candidates(db)
        assert result == []

    @pytest.mark.asyncio
    async def test_filters_completed_sessions(self):
        profiles = [_make_candidate("u1"), _make_candidate("u2")]
        completed = [{"volunteer_id": "u1"}]
        db = _make_db(profiles=profiles, completed_sessions=completed)
        result = await _fetch_candidates(db)
        assert len(result) == 1
        assert result[0]["id"] == "u2"

    @pytest.mark.asyncio
    async def test_all_completed_returns_empty(self):
        profiles = [_make_candidate("u1"), _make_candidate("u2")]
        completed = [{"volunteer_id": "u1"}, {"volunteer_id": "u2"}]
        db = _make_db(profiles=profiles, completed_sessions=completed)
        result = await _fetch_candidates(db)
        assert result == []

    @pytest.mark.asyncio
    async def test_no_completed_returns_all(self):
        profiles = [_make_candidate("u1"), _make_candidate("u2")]
        db = _make_db(profiles=profiles, completed_sessions=[])
        result = await _fetch_candidates(db)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_respects_batch_size(self):
        profiles = [_make_candidate(f"u{i}") for i in range(BATCH_SIZE + 20)]
        db = _make_db(profiles=profiles, completed_sessions=[])
        result = await _fetch_candidates(db)
        assert len(result) == BATCH_SIZE

    @pytest.mark.asyncio
    async def test_over_fetch_limit(self):
        db = _make_db(profiles=[_make_candidate("u1")])
        await _fetch_candidates(db)
        profile_chain = db.table("profiles")
        profile_chain.limit.assert_called_with(BATCH_SIZE * 2)

    @pytest.mark.asyncio
    async def test_queries_correct_tables(self):
        profiles = [_make_candidate("u1")]
        db = _make_db(profiles=profiles)
        await _fetch_candidates(db)
        calls = [c.args[0] for c in db.table.call_args_list]
        assert "profiles" in calls
        assert "assessment_sessions" in calls

    @pytest.mark.asyncio
    async def test_preserves_candidate_fields(self):
        profiles = [_make_candidate("u1", "Alice", "alice99")]
        db = _make_db(profiles=profiles)
        result = await _fetch_candidates(db)
        assert result[0]["display_name"] == "Alice"
        assert result[0]["username"] == "alice99"

    @pytest.mark.asyncio
    async def test_selects_correct_columns(self):
        db = _make_db(profiles=[_make_candidate("u1")])
        await _fetch_candidates(db)
        profile_chain = db.table("profiles")
        profile_chain.select.assert_called_once_with("id, display_name, username")


class TestFetchEmail:
    @pytest.mark.asyncio
    async def test_returns_email(self):
        db = MagicMock()
        user_obj = MagicMock()
        user_obj.email = "test@example.com"
        result_obj = MagicMock()
        result_obj.user = user_obj
        db.auth.admin.get_user_by_id = AsyncMock(return_value=result_obj)

        email = await _fetch_email(db, "u1")
        assert email == "test@example.com"

    @pytest.mark.asyncio
    async def test_returns_none_on_exception(self):
        db = MagicMock()
        db.auth.admin.get_user_by_id = AsyncMock(side_effect=Exception("boom"))
        email = await _fetch_email(db, "u1")
        assert email is None

    @pytest.mark.asyncio
    async def test_handles_no_user_attr(self):
        db = MagicMock()
        result_obj = MagicMock(spec=[])
        result_obj.email = "direct@example.com"
        db.auth.admin.get_user_by_id = AsyncMock(return_value=result_obj)

        email = await _fetch_email(db, "u1")
        assert email == "direct@example.com"

    @pytest.mark.asyncio
    async def test_returns_none_when_no_email_attr(self):
        db = MagicMock()
        result_obj = MagicMock(spec=[])
        db.auth.admin.get_user_by_id = AsyncMock(return_value=result_obj)

        email = await _fetch_email(db, "u1")
        assert email is None

    @pytest.mark.asyncio
    async def test_passes_user_id_to_admin_api(self):
        db = MagicMock()
        user_obj = MagicMock()
        user_obj.email = "x@y.com"
        result_obj = MagicMock()
        result_obj.user = user_obj
        db.auth.admin.get_user_by_id = AsyncMock(return_value=result_obj)

        await _fetch_email(db, "uid-abc-123")
        db.auth.admin.get_user_by_id.assert_awaited_once_with("uid-abc-123")


class TestProcessGhostingGrace:
    @pytest.mark.asyncio
    @patch("app.services.ghosting_grace._fetch_candidates", new_callable=AsyncMock)
    async def test_no_candidates(self, mock_fetch):
        mock_fetch.return_value = []
        db = MagicMock()
        summary = await process_ghosting_grace(db)
        assert summary["candidates"] == 0
        assert summary["sent"] == 0
        assert summary["skipped_kill_switch"] == 0
        assert summary["marked"] == 0
        assert summary["errors"] == 0

    @pytest.mark.asyncio
    @patch("app.services.ghosting_grace._fetch_candidates", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace.settings")
    async def test_kill_switch_email_disabled(self, mock_settings, mock_fetch):
        mock_fetch.return_value = [_make_candidate("u1"), _make_candidate("u2")]
        mock_settings.email_enabled = False
        mock_settings.resend_api_key = "re_xxx"
        db = MagicMock()
        summary = await process_ghosting_grace(db)
        assert summary["candidates"] == 2
        assert summary["skipped_kill_switch"] == 2
        assert summary["sent"] == 0

    @pytest.mark.asyncio
    @patch("app.services.ghosting_grace._fetch_candidates", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace.settings")
    async def test_kill_switch_no_resend_key(self, mock_settings, mock_fetch):
        mock_fetch.return_value = [_make_candidate("u1")]
        mock_settings.email_enabled = True
        mock_settings.resend_api_key = ""
        db = MagicMock()
        summary = await process_ghosting_grace(db)
        assert summary["skipped_kill_switch"] == 1
        assert summary["sent"] == 0

    @pytest.mark.asyncio
    @patch("app.services.ghosting_grace._fetch_candidates", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace.settings")
    async def test_kill_switch_none_resend_key(self, mock_settings, mock_fetch):
        mock_fetch.return_value = [_make_candidate("u1")]
        mock_settings.email_enabled = True
        mock_settings.resend_api_key = None
        db = MagicMock()
        summary = await process_ghosting_grace(db)
        assert summary["skipped_kill_switch"] == 1

    @pytest.mark.asyncio
    @patch("app.services.ghosting_grace._fetch_candidates", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace.settings")
    async def test_kill_switch_does_not_mark(self, mock_settings, mock_fetch):
        mock_fetch.return_value = [_make_candidate("u1")]
        mock_settings.email_enabled = False
        mock_settings.resend_api_key = "re_xxx"
        db = MagicMock()
        summary = await process_ghosting_grace(db)
        assert summary["marked"] == 0
        assert summary["errors"] == 0

    @pytest.mark.asyncio
    @patch("app.services.ghosting_grace.send_ghosting_grace_email", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace._fetch_email", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace._fetch_candidates", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace.settings")
    async def test_happy_path_send_and_mark(
        self, mock_settings, mock_fetch, mock_email, mock_send
    ):
        mock_settings.email_enabled = True
        mock_settings.resend_api_key = "re_xxx"
        mock_fetch.return_value = [_make_candidate("u1")]
        mock_email.return_value = "user@test.com"
        mock_send.return_value = True

        db, update_chain = _make_process_db()

        summary = await process_ghosting_grace(db)
        assert summary["sent"] == 1
        assert summary["marked"] == 1
        assert summary["errors"] == 0

    @pytest.mark.asyncio
    @patch("app.services.ghosting_grace.send_ghosting_grace_email", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace._fetch_email", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace._fetch_candidates", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace.settings")
    async def test_email_fetch_fails(
        self, mock_settings, mock_fetch, mock_email, mock_send
    ):
        mock_settings.email_enabled = True
        mock_settings.resend_api_key = "re_xxx"
        mock_fetch.return_value = [_make_candidate("u1")]
        mock_email.return_value = None

        db = MagicMock()
        summary = await process_ghosting_grace(db)
        assert summary["errors"] == 1
        assert summary["sent"] == 0
        mock_send.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.services.ghosting_grace.send_ghosting_grace_email", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace._fetch_email", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace._fetch_candidates", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace.settings")
    async def test_email_send_fails(
        self, mock_settings, mock_fetch, mock_email, mock_send
    ):
        mock_settings.email_enabled = True
        mock_settings.resend_api_key = "re_xxx"
        mock_fetch.return_value = [_make_candidate("u1")]
        mock_email.return_value = "user@test.com"
        mock_send.return_value = False

        db = MagicMock()
        summary = await process_ghosting_grace(db)
        assert summary["errors"] == 1
        assert summary["sent"] == 0
        assert summary["marked"] == 0

    @pytest.mark.asyncio
    @patch("app.services.ghosting_grace.send_ghosting_grace_email", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace._fetch_email", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace._fetch_candidates", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace.settings")
    async def test_mark_fails_after_send(
        self, mock_settings, mock_fetch, mock_email, mock_send
    ):
        mock_settings.email_enabled = True
        mock_settings.resend_api_key = "re_xxx"
        mock_fetch.return_value = [_make_candidate("u1")]
        mock_email.return_value = "user@test.com"
        mock_send.return_value = True

        db = MagicMock()
        update_chain = _chain_mock()
        update_chain.execute = AsyncMock(side_effect=Exception("db down"))
        db.table = MagicMock(return_value=update_chain)

        summary = await process_ghosting_grace(db)
        assert summary["sent"] == 1
        assert summary["marked"] == 0
        assert summary["errors"] == 1

    @pytest.mark.asyncio
    @patch("app.services.ghosting_grace.send_ghosting_grace_email", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace._fetch_email", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace._fetch_candidates", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace.settings")
    async def test_multiple_candidates_mixed(
        self, mock_settings, mock_fetch, mock_email, mock_send
    ):
        mock_settings.email_enabled = True
        mock_settings.resend_api_key = "re_xxx"
        mock_fetch.return_value = [
            _make_candidate("u1"),
            _make_candidate("u2"),
            _make_candidate("u3"),
        ]
        mock_email.side_effect = ["a@test.com", None, "c@test.com"]
        mock_send.side_effect = [True, True]

        db, _ = _make_process_db()

        summary = await process_ghosting_grace(db)
        assert summary["candidates"] == 3
        assert summary["sent"] == 2
        assert summary["errors"] == 1
        assert summary["marked"] == 2

    @pytest.mark.asyncio
    @patch("app.services.ghosting_grace.send_ghosting_grace_email", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace._fetch_email", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace._fetch_candidates", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace.settings")
    async def test_display_name_fallback_to_username(
        self, mock_settings, mock_fetch, mock_email, mock_send
    ):
        mock_settings.email_enabled = True
        mock_settings.resend_api_key = "re_xxx"
        mock_fetch.return_value = [
            {"id": "u1", "display_name": None, "username": "fallback_user"}
        ]
        mock_email.return_value = "user@test.com"
        mock_send.return_value = True

        db, _ = _make_process_db()

        await process_ghosting_grace(db)
        mock_send.assert_called_once()
        call_kwargs = mock_send.call_args[1]
        assert call_kwargs["display_name"] == "fallback_user"

    @pytest.mark.asyncio
    @patch("app.services.ghosting_grace.send_ghosting_grace_email", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace._fetch_email", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace._fetch_candidates", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace.settings")
    async def test_display_name_and_username_both_none(
        self, mock_settings, mock_fetch, mock_email, mock_send
    ):
        mock_settings.email_enabled = True
        mock_settings.resend_api_key = "re_xxx"
        mock_fetch.return_value = [
            {"id": "u1", "display_name": None, "username": None}
        ]
        mock_email.return_value = "user@test.com"
        mock_send.return_value = True

        db, _ = _make_process_db()

        await process_ghosting_grace(db)
        call_kwargs = mock_send.call_args[1]
        assert call_kwargs["display_name"] == ""

    @pytest.mark.asyncio
    @patch("app.services.ghosting_grace.send_ghosting_grace_email", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace._fetch_email", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace._fetch_candidates", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace.settings")
    async def test_locale_always_en(
        self, mock_settings, mock_fetch, mock_email, mock_send
    ):
        mock_settings.email_enabled = True
        mock_settings.resend_api_key = "re_xxx"
        mock_fetch.return_value = [_make_candidate("u1")]
        mock_email.return_value = "user@test.com"
        mock_send.return_value = True

        db, _ = _make_process_db()

        await process_ghosting_grace(db)
        call_kwargs = mock_send.call_args[1]
        assert call_kwargs["locale"] == "en"

    @pytest.mark.asyncio
    @patch("app.services.ghosting_grace._fetch_candidates", new_callable=AsyncMock)
    async def test_summary_keys_present(self, mock_fetch):
        mock_fetch.return_value = []
        db = MagicMock()
        summary = await process_ghosting_grace(db)
        assert set(summary.keys()) == {
            "candidates", "sent", "skipped_kill_switch", "marked", "errors"
        }

    @pytest.mark.asyncio
    @patch("app.services.ghosting_grace.send_ghosting_grace_email", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace._fetch_email", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace._fetch_candidates", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace.settings")
    async def test_update_calls_correct_table(
        self, mock_settings, mock_fetch, mock_email, mock_send
    ):
        mock_settings.email_enabled = True
        mock_settings.resend_api_key = "re_xxx"
        mock_fetch.return_value = [_make_candidate("u1")]
        mock_email.return_value = "user@test.com"
        mock_send.return_value = True

        db, _ = _make_process_db()

        await process_ghosting_grace(db)
        db.table.assert_called_with("profiles")

    @pytest.mark.asyncio
    @patch("app.services.ghosting_grace.send_ghosting_grace_email", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace._fetch_email", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace._fetch_candidates", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace.settings")
    async def test_update_sets_ghosting_grace_sent_at(
        self, mock_settings, mock_fetch, mock_email, mock_send
    ):
        mock_settings.email_enabled = True
        mock_settings.resend_api_key = "re_xxx"
        mock_fetch.return_value = [_make_candidate("u1")]
        mock_email.return_value = "user@test.com"
        mock_send.return_value = True

        db, update_chain = _make_process_db()

        await process_ghosting_grace(db)
        update_call = update_chain.update.call_args[0][0]
        assert "ghosting_grace_sent_at" in update_call

    @pytest.mark.asyncio
    @patch("app.services.ghosting_grace.send_ghosting_grace_email", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace._fetch_email", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace._fetch_candidates", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace.settings")
    async def test_update_filters_by_user_id(
        self, mock_settings, mock_fetch, mock_email, mock_send
    ):
        mock_settings.email_enabled = True
        mock_settings.resend_api_key = "re_xxx"
        mock_fetch.return_value = [_make_candidate("u42")]
        mock_email.return_value = "user@test.com"
        mock_send.return_value = True

        db, update_chain = _make_process_db()

        await process_ghosting_grace(db)
        update_chain.eq.assert_called_with("id", "u42")

    @pytest.mark.asyncio
    @patch("app.services.ghosting_grace.send_ghosting_grace_email", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace._fetch_email", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace._fetch_candidates", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace.settings")
    async def test_all_emails_fail_no_sends(
        self, mock_settings, mock_fetch, mock_email, mock_send
    ):
        mock_settings.email_enabled = True
        mock_settings.resend_api_key = "re_xxx"
        mock_fetch.return_value = [_make_candidate("u1"), _make_candidate("u2")]
        mock_email.return_value = None

        db = MagicMock()
        summary = await process_ghosting_grace(db)
        assert summary["errors"] == 2
        assert summary["sent"] == 0
        assert summary["marked"] == 0
        mock_send.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.services.ghosting_grace.send_ghosting_grace_email", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace._fetch_email", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace._fetch_candidates", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace.settings")
    async def test_display_name_empty_string_uses_username(
        self, mock_settings, mock_fetch, mock_email, mock_send
    ):
        mock_settings.email_enabled = True
        mock_settings.resend_api_key = "re_xxx"
        mock_fetch.return_value = [
            {"id": "u1", "display_name": "", "username": "myuser"}
        ]
        mock_email.return_value = "user@test.com"
        mock_send.return_value = True

        db, _ = _make_process_db()

        await process_ghosting_grace(db)
        call_kwargs = mock_send.call_args[1]
        assert call_kwargs["display_name"] == "myuser"

    @pytest.mark.asyncio
    @patch("app.services.ghosting_grace.send_ghosting_grace_email", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace._fetch_email", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace._fetch_candidates", new_callable=AsyncMock)
    @patch("app.services.ghosting_grace.settings")
    async def test_send_called_with_correct_email(
        self, mock_settings, mock_fetch, mock_email, mock_send
    ):
        mock_settings.email_enabled = True
        mock_settings.resend_api_key = "re_xxx"
        mock_fetch.return_value = [_make_candidate("u1")]
        mock_email.return_value = "specific@addr.com"
        mock_send.return_value = True

        db, _ = _make_process_db()

        await process_ghosting_grace(db)
        call_kwargs = mock_send.call_args[1]
        assert call_kwargs["to_email"] == "specific@addr.com"
