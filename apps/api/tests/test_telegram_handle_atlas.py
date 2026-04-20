"""Unit tests for _handle_atlas and telegram_webhook endpoint.

Covers two changes:
  1. BackgroundTasks pattern (commit de60bac) — webhook returns 200 immediately,
     delegates to _process_telegram_update via BackgroundTasks.add_task.
  2. generate_atlas_response wiring (commit 1ccb900) — _handle_atlas calls
     app.services.telegram_llm.generate_atlas_response instead of an inline chain.

Tests use pytest-asyncio + unittest.mock.  External I/O is fully mocked.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import BackgroundTasks

import app.routers.telegram_webhook as tw

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

CEO_CHAT_ID = "123"
BOT_TOKEN = "123:ABC"
WEBHOOK_SECRET = "secret"
CHAT_TEXT = "Атлас, как дела?"


def _make_message(text: str = CHAT_TEXT, user_id: str = CEO_CHAT_ID) -> dict:
    return {
        "message": {
            "chat": {"id": CEO_CHAT_ID},
            "from": {"id": user_id},
            "text": text,
        }
    }


def _signed_request(body: bytes, secret: str = WEBHOOK_SECRET) -> dict:
    """Return headers with a valid X-Telegram-Bot-Api-Secret-Token."""
    return {"X-Telegram-Bot-Api-Secret-Token": secret}


# ---------------------------------------------------------------------------
# Fixtures — common patches applied to every test in this module
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    """Patch tw.settings to values that keep paths short-circuit-free."""
    fake = MagicMock()
    fake.telegram_bot_token = BOT_TOKEN
    fake.telegram_webhook_secret = WEBHOOK_SECRET
    fake.telegram_ceo_chat_id = CEO_CHAT_ID
    fake.gemini_api_key = "test-gemini-key"
    fake.vertex_api_key = ""
    monkeypatch.setattr(tw, "settings", fake)
    return fake


@pytest.fixture()
def mock_db():
    """Minimal async Supabase-client double."""
    return AsyncMock()


@pytest.fixture(autouse=True)
def patch_path_exists():
    """Make all _REPO_ROOT file-reads return False (no filesystem required)."""
    with patch("pathlib.Path.exists", return_value=False):
        yield


@pytest.fixture(autouse=True)
def patch_save_message():
    with patch.object(tw, "_save_message", new=AsyncMock()) as m:
        yield m


@pytest.fixture(autouse=True)
def patch_send_message():
    with patch.object(tw, "_send_message", new=AsyncMock(return_value=True)) as m:
        yield m


@pytest.fixture(autouse=True)
def patch_classify():
    with patch.object(tw, "_classify_action_or_chat", return_value="CHAT") as m:
        yield m


@pytest.fixture(autouse=True)
def patch_detect_emotional():
    with patch.object(tw, "_detect_emotional_state", return_value="A") as m:
        yield m


@pytest.fixture(autouse=True)
def patch_get_recent_context():
    with patch.object(tw, "_get_recent_context", new=AsyncMock(return_value="")) as m:
        yield m


@pytest.fixture(autouse=True)
def patch_load_atlas_learnings():
    with patch.object(tw, "_load_atlas_learnings", new=AsyncMock(return_value="")) as m:
        yield m


@pytest.fixture(autouse=True)
def patch_load_atlas_memory():
    with patch.object(tw, "_load_atlas_memory", return_value="") as m:
        yield m


@pytest.fixture(autouse=True)
def patch_atlas_extract_learnings():
    with patch.object(tw, "_atlas_extract_learnings", new=AsyncMock()) as m:
        yield m


@pytest.fixture(autouse=True)
def patch_get_last_bot_replies():
    with patch.object(tw, "_get_last_bot_replies", new=AsyncMock(return_value=[])) as m:
        yield m


@pytest.fixture(autouse=True)
def patch_create_github_issue():
    with patch.object(tw, "_create_github_issue", new=AsyncMock(return_value="https://github.com/x/y/issues/1")) as m:
        yield m


@pytest.fixture(autouse=True)
def patch_write_atlas_inbox_file():
    with patch.object(tw, "_write_atlas_inbox_file", new=AsyncMock(return_value="memory/atlas/inbox/note.md")) as m:
        yield m


@pytest.fixture()
def mock_generate_atlas_response():
    with patch(
        "app.services.telegram_llm.generate_atlas_response",
        new=AsyncMock(return_value=("test reply", "gemini")),
    ) as m:
        yield m


@pytest.fixture()
def mock_loop_breaker_no_trip():
    """LoopCircuitBreaker.evaluate returns a non-tripped decision."""
    decision = MagicMock()
    decision.tripped = False
    decision.describe.return_value = "no loop"

    with patch("app.services.loop_circuit_breaker.LoopCircuitBreaker") as cls_mock:
        instance = cls_mock.return_value
        instance.evaluate.return_value = decision
        yield cls_mock


# ---------------------------------------------------------------------------
# 1. BackgroundTasks pattern — webhook endpoint
# ---------------------------------------------------------------------------


class TestWebhookBackgroundTasks:
    """telegram_webhook returns 200 immediately and queues processing."""

    @pytest.mark.asyncio
    async def test_valid_secret_returns_200_ok(self, mock_db, mock_generate_atlas_response, mock_loop_breaker_no_trip):
        from fastapi import Request

        body = b'{"message": {"chat": {"id": 123}, "from": {"id": 123}, "text": "hi"}}'
        headers = {"X-Telegram-Bot-Api-Secret-Token": WEBHOOK_SECRET}

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/telegram/webhook",
            "query_string": b"",
            "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
        }

        async def receive():
            return {"type": "http.request", "body": body}

        request = Request(scope, receive=receive)
        request._client = SimpleNamespace(host="127.0.0.1")

        bg = BackgroundTasks()
        response = await tw.telegram_webhook(request, bg, db=mock_db)
        data = response.body
        assert b'"ok": true' in data or b'"ok":true' in data

    @pytest.mark.asyncio
    async def test_invalid_secret_returns_403(self, mock_db):
        from fastapi import Request

        body = b"{}"
        headers = {"X-Telegram-Bot-Api-Secret-Token": "WRONG_SECRET"}
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/telegram/webhook",
            "query_string": b"",
            "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
        }

        async def receive():
            return {"type": "http.request", "body": body}

        request = Request(scope, receive=receive)
        request._client = SimpleNamespace(host="127.0.0.1")

        bg = BackgroundTasks()
        response = await tw.telegram_webhook(request, bg, db=mock_db)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_background_task_is_added(self, mock_db, mock_generate_atlas_response, mock_loop_breaker_no_trip):
        from fastapi import Request

        body = b'{"message": {"chat": {"id": 123}, "from": {"id": 123}, "text": "hi"}}'
        headers = {"X-Telegram-Bot-Api-Secret-Token": WEBHOOK_SECRET}
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/telegram/webhook",
            "query_string": b"",
            "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
        }

        async def receive():
            return {"type": "http.request", "body": body}

        request = Request(scope, receive=receive)
        request._client = SimpleNamespace(host="127.0.0.1")

        bg = MagicMock(spec=BackgroundTasks)
        bg.add_task = MagicMock()

        await tw.telegram_webhook(request, bg, db=mock_db)

        bg.add_task.assert_called_once()
        call_args = bg.add_task.call_args
        # First positional arg must be the processing coroutine function
        assert call_args[0][0] is tw._process_telegram_update

    @pytest.mark.asyncio
    async def test_missing_bot_token_returns_not_ok(self, mock_db, mock_settings):
        from fastapi import Request

        mock_settings.telegram_bot_token = ""
        body = b"{}"
        headers = {"X-Telegram-Bot-Api-Secret-Token": WEBHOOK_SECRET}
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/telegram/webhook",
            "query_string": b"",
            "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
        }

        async def receive():
            return {"type": "http.request", "body": body}

        request = Request(scope, receive=receive)
        request._client = SimpleNamespace(host="127.0.0.1")

        bg = BackgroundTasks()
        response = await tw.telegram_webhook(request, bg, db=mock_db)
        data = response.body
        assert b'"ok": false' in data or b'"ok":false' in data


# ---------------------------------------------------------------------------
# 2. _process_telegram_update — exception wrapping
# ---------------------------------------------------------------------------


class TestProcessTelegramUpdate:
    @pytest.mark.asyncio
    async def test_wraps_exception_without_raising(self, mock_db):
        """_process_telegram_update must never propagate exceptions."""
        with patch.object(tw, "_handle_telegram_update", new=AsyncMock(side_effect=RuntimeError("boom"))):
            # Should not raise
            await tw._process_telegram_update({"message": {}}, mock_db)

    @pytest.mark.asyncio
    async def test_calls_handle_telegram_update(self, mock_db):
        update = {"message": {"chat": {"id": 1}, "from": {"id": 1}, "text": "hi"}}
        handler = AsyncMock()
        with patch.object(tw, "_handle_telegram_update", handler):
            await tw._process_telegram_update(update, mock_db)
        handler.assert_awaited_once_with(update, mock_db)


# ---------------------------------------------------------------------------
# 3. _handle_atlas — CHAT path
# ---------------------------------------------------------------------------


class TestHandleAtlasChatPath:
    @pytest.mark.asyncio
    async def test_chat_calls_generate_atlas_response(
        self, mock_db, mock_generate_atlas_response, mock_loop_breaker_no_trip
    ):
        with patch.object(tw, "_classify_action_or_chat", return_value="CHAT"):
            await tw._handle_atlas(mock_db, CEO_CHAT_ID, CHAT_TEXT)

        mock_generate_atlas_response.assert_awaited_once()
        call_kwargs = mock_generate_atlas_response.call_args
        assert call_kwargs is not None

    @pytest.mark.asyncio
    async def test_chat_sends_reply_from_generate_atlas_response(
        self, mock_db, mock_generate_atlas_response, mock_loop_breaker_no_trip, patch_send_message
    ):
        mock_generate_atlas_response.return_value = ("my custom reply", "gemini")
        with patch.object(tw, "_classify_action_or_chat", return_value="CHAT"):
            await tw._handle_atlas(mock_db, CEO_CHAT_ID, CHAT_TEXT)

        patch_send_message.assert_awaited()
        sent_text = patch_send_message.call_args[0][1]
        assert "my custom reply" in sent_text

    @pytest.mark.asyncio
    async def test_chat_calls_generate_with_system_prompt_kwarg(
        self, mock_db, mock_generate_atlas_response, mock_loop_breaker_no_trip
    ):
        with patch.object(tw, "_classify_action_or_chat", return_value="CHAT"):
            await tw._handle_atlas(mock_db, CEO_CHAT_ID, CHAT_TEXT)

        _, kwargs = mock_generate_atlas_response.call_args
        assert "system_prompt" in kwargs or len(mock_generate_atlas_response.call_args.args) >= 1

    @pytest.mark.asyncio
    async def test_chat_calls_generate_with_user_message(
        self, mock_db, mock_generate_atlas_response, mock_loop_breaker_no_trip
    ):
        user_msg = "конкретный вопрос от CEO"
        with patch.object(tw, "_classify_action_or_chat", return_value="CHAT"):
            await tw._handle_atlas(mock_db, CEO_CHAT_ID, user_msg)

        call = mock_generate_atlas_response.call_args
        # user_message may be positional arg 2 or keyword arg
        all_args = list(call.args) + list(call.kwargs.values())
        assert user_msg in all_args

    @pytest.mark.asyncio
    async def test_chat_calls_extract_learnings_after_reply(
        self, mock_db, mock_generate_atlas_response, mock_loop_breaker_no_trip, patch_atlas_extract_learnings
    ):
        with patch.object(tw, "_classify_action_or_chat", return_value="CHAT"):
            await tw._handle_atlas(mock_db, CEO_CHAT_ID, CHAT_TEXT)

        patch_atlas_extract_learnings.assert_awaited_once()


# ---------------------------------------------------------------------------
# 4. _handle_atlas — ACTION path
# ---------------------------------------------------------------------------


class TestHandleAtlasActionPath:
    @pytest.mark.asyncio
    async def test_action_invokes_tools_registry_first(
        self, mock_db, mock_generate_atlas_response, mock_loop_breaker_no_trip
    ):
        tool_result = MagicMock()
        tool_result.ok = True
        tool_result.anchor = "https://github.com/x/y/issues/42"

        registry_mock = MagicMock()
        registry_mock.invoke = AsyncMock(return_value=tool_result)

        with (
            patch.object(tw, "_classify_action_or_chat", return_value="ACTION"),
            patch("app.services.atlas_tools.REGISTRY", registry_mock),
        ):
            await tw._handle_atlas(mock_db, CEO_CHAT_ID, "сделай что-нибудь")

        registry_mock.invoke.assert_awaited()
        call = registry_mock.invoke.call_args
        assert call[0][0] == "create_github_issue"

    @pytest.mark.asyncio
    async def test_action_still_calls_generate_atlas_response(
        self, mock_db, mock_generate_atlas_response, mock_loop_breaker_no_trip
    ):
        tool_result = MagicMock()
        tool_result.ok = True
        tool_result.anchor = "https://github.com/x/y/issues/42"

        registry_mock = MagicMock()
        registry_mock.invoke = AsyncMock(return_value=tool_result)

        with (
            patch.object(tw, "_classify_action_or_chat", return_value="ACTION"),
            patch("app.services.atlas_tools.REGISTRY", registry_mock),
        ):
            await tw._handle_atlas(mock_db, CEO_CHAT_ID, "сделай что-нибудь")

        mock_generate_atlas_response.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_action_anchor_appended_when_not_in_reply(
        self, mock_db, mock_generate_atlas_response, mock_loop_breaker_no_trip, patch_send_message
    ):
        anchor_url = "https://github.com/x/y/issues/99"
        mock_generate_atlas_response.return_value = ("reply without anchor", "gemini")

        tool_result = MagicMock()
        tool_result.ok = True
        tool_result.anchor = anchor_url

        registry_mock = MagicMock()
        registry_mock.invoke = AsyncMock(return_value=tool_result)

        with (
            patch.object(tw, "_classify_action_or_chat", return_value="ACTION"),
            patch("app.services.atlas_tools.REGISTRY", registry_mock),
        ):
            await tw._handle_atlas(mock_db, CEO_CHAT_ID, "сделай что-нибудь")

        sent_text = patch_send_message.call_args[0][1]
        assert anchor_url in sent_text


# ---------------------------------------------------------------------------
# 5. Loop-break trigger (the "докажи" branch)
# ---------------------------------------------------------------------------


class TestHandleAtlasLoopBreak:
    @pytest.mark.asyncio
    async def test_dokazhi_skips_generate_atlas_response(
        self, mock_db, mock_generate_atlas_response, patch_send_message
    ):
        await tw._handle_atlas(mock_db, CEO_CHAT_ID, "докажи что ты помнишь")
        mock_generate_atlas_response.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_dokazhi_creates_github_issue(self, mock_db, mock_generate_atlas_response, patch_create_github_issue):
        await tw._handle_atlas(mock_db, CEO_CHAT_ID, "докажи")
        patch_create_github_issue.assert_awaited_once()
        call_args = patch_create_github_issue.call_args
        assert "loop-break" in call_args[1].get("label", "") or "loop" in str(call_args).lower()

    @pytest.mark.asyncio
    async def test_dokazhi_sends_loop_acknowledgement(self, mock_db, patch_send_message):
        await tw._handle_atlas(mock_db, CEO_CHAT_ID, "докажи")
        patch_send_message.assert_awaited()
        sent = patch_send_message.call_args[0][1]
        assert "Атлас" in sent or "atlas" in sent.lower() or "цикл" in sent.lower()

    @pytest.mark.asyncio
    async def test_prove_it_english_triggers_loop_break(self, mock_db, mock_generate_atlas_response):
        await tw._handle_atlas(mock_db, CEO_CHAT_ID, "prove it please")
        mock_generate_atlas_response.assert_not_awaited()


# ---------------------------------------------------------------------------
# 6. No LLM key — fallback message
# ---------------------------------------------------------------------------


class TestHandleAtlasNoLlmKey:
    @pytest.mark.asyncio
    async def test_no_keys_sends_fallback_message(self, mock_db, mock_settings, patch_send_message):
        mock_settings.gemini_api_key = ""
        mock_settings.vertex_api_key = ""

        with patch.object(tw, "_classify_action_or_chat", return_value="CHAT"):
            await tw._handle_atlas(mock_db, CEO_CHAT_ID, CHAT_TEXT)

        patch_send_message.assert_awaited()
        sent = patch_send_message.call_args[0][1]
        assert "LLM" in sent or "недоступен" in sent

    @pytest.mark.asyncio
    async def test_no_keys_does_not_call_generate(self, mock_db, mock_settings, mock_generate_atlas_response):
        mock_settings.gemini_api_key = ""
        mock_settings.vertex_api_key = ""

        with patch.object(tw, "_classify_action_or_chat", return_value="CHAT"):
            await tw._handle_atlas(mock_db, CEO_CHAT_ID, CHAT_TEXT)

        mock_generate_atlas_response.assert_not_awaited()


# ---------------------------------------------------------------------------
# 7. Anti-loop post-check (LoopCircuitBreaker)
# ---------------------------------------------------------------------------


class TestHandleAtlasLoopCircuitBreaker:
    @pytest.mark.asyncio
    async def test_non_tripped_breaker_sends_normal_reply(
        self, mock_db, mock_generate_atlas_response, mock_loop_breaker_no_trip, patch_send_message
    ):
        mock_generate_atlas_response.return_value = ("normal reply here", "gemini")
        with patch.object(tw, "_classify_action_or_chat", return_value="CHAT"):
            await tw._handle_atlas(mock_db, CEO_CHAT_ID, CHAT_TEXT)

        sent = patch_send_message.call_args[0][1]
        assert "normal reply here" in sent

    @pytest.mark.asyncio
    async def test_tripped_breaker_replaces_reply_with_loop_message(
        self, mock_db, mock_generate_atlas_response, patch_send_message
    ):
        # Generate a long reply (>80 chars) so trip condition fires
        long_reply = "a" * 200
        mock_generate_atlas_response.return_value = (long_reply, "gemini")

        tripped_decision = MagicMock()
        tripped_decision.tripped = True
        tripped_decision.describe.return_value = "LOOP (token_velocity)"

        with (
            patch("app.services.loop_circuit_breaker.LoopCircuitBreaker") as cls_mock,
            patch.object(tw, "_classify_action_or_chat", return_value="CHAT"),
        ):
            instance = cls_mock.return_value
            instance.evaluate.return_value = tripped_decision
            await tw._handle_atlas(mock_db, CEO_CHAT_ID, CHAT_TEXT)

        sent = patch_send_message.call_args[0][1]
        # Reply must be replaced — not the original LLM output
        assert long_reply != sent
        assert "цикл" in sent.lower() or "loop" in sent.lower() or "Атлас" in sent

    @pytest.mark.asyncio
    async def test_tripped_breaker_creates_github_issue(
        self, mock_db, mock_generate_atlas_response, patch_create_github_issue
    ):
        long_reply = "x" * 200
        mock_generate_atlas_response.return_value = (long_reply, "gemini")

        tripped_decision = MagicMock()
        tripped_decision.tripped = True
        tripped_decision.describe.return_value = "LOOP (no_progress)"

        with (
            patch("app.services.loop_circuit_breaker.LoopCircuitBreaker") as cls_mock,
            patch.object(tw, "_classify_action_or_chat", return_value="CHAT"),
        ):
            instance = cls_mock.return_value
            instance.evaluate.return_value = tripped_decision
            await tw._handle_atlas(mock_db, CEO_CHAT_ID, CHAT_TEXT)

        patch_create_github_issue.assert_awaited()


# ---------------------------------------------------------------------------
# 8. Self-learning post-hook
# ---------------------------------------------------------------------------


class TestHandleAtlasSelfLearning:
    @pytest.mark.asyncio
    async def test_extract_learnings_called_with_correct_args(
        self, mock_db, mock_generate_atlas_response, mock_loop_breaker_no_trip, patch_atlas_extract_learnings
    ):
        user_text = "расскажи про продукт"
        reply_text = "reply about product"
        mock_generate_atlas_response.return_value = (reply_text, "gemini")

        with patch.object(tw, "_classify_action_or_chat", return_value="CHAT"):
            await tw._handle_atlas(mock_db, CEO_CHAT_ID, user_text)

        patch_atlas_extract_learnings.assert_awaited_once()
        call = patch_atlas_extract_learnings.call_args
        positional = list(call.args)
        assert mock_db in positional
        assert user_text in positional
        assert reply_text in positional


# ---------------------------------------------------------------------------
# 9. Message saving behaviour
# ---------------------------------------------------------------------------


class TestHandleAtlasMessageSaving:
    @pytest.mark.asyncio
    async def test_saves_incoming_message_first(
        self, mock_db, mock_generate_atlas_response, mock_loop_breaker_no_trip, patch_save_message
    ):
        with patch.object(tw, "_classify_action_or_chat", return_value="CHAT"):
            await tw._handle_atlas(mock_db, CEO_CHAT_ID, CHAT_TEXT)

        # First call to _save_message should be the incoming CEO message
        first_call = patch_save_message.call_args_list[0]
        assert first_call[0][1] == "ceo_to_bot"

    @pytest.mark.asyncio
    async def test_saves_bot_reply_after_llm(
        self, mock_db, mock_generate_atlas_response, mock_loop_breaker_no_trip, patch_save_message
    ):
        with patch.object(tw, "_classify_action_or_chat", return_value="CHAT"):
            await tw._handle_atlas(mock_db, CEO_CHAT_ID, CHAT_TEXT)

        directions = [call[0][1] for call in patch_save_message.call_args_list]
        assert "bot_to_ceo" in directions
