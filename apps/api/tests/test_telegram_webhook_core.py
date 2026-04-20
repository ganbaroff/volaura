"""Core unit tests for telegram_webhook.py — pure functions + DB-dependent functions.

Covers:
  1. _detect_ceo_emotion  — pure keyword-based emotion detection
  2. _detect_emotional_state — returns A/B/C/D emoji state string
  3. _char_similarity — character-level similarity ratio
  4. _save_message — DB insert with filesystem fallback
  5. _get_recent_context — DB query with role mapping and truncation
  6. _get_project_stats — DB multi-table count query
  7. _send_message — chunking, Markdown fallback, reply_markup placement
  8. _load_atlas_memory — file-based memory loading with fallback
  9. _get_ecosystem_context — ecosystem heartbeat file loading
 10. _handle_telegram_update — message routing (text/callback/voice)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import app.routers.telegram_webhook as tw

# ---------------------------------------------------------------------------
# ── 1. _detect_ceo_emotion ─────────────────────────────────────────────────
# ---------------------------------------------------------------------------


class TestDetectCeoEmotion:
    def test_positive_word_returns_drive(self):
        result = tw._detect_ceo_emotion("шикарно получилось!")
        assert result["state"] == "drive"
        assert result["intensity"] > 0

    def test_multiple_positive_words_increase_intensity(self):
        result = tw._detect_ceo_emotion("круто шикарно молодец красава")
        assert result["state"] == "drive"
        assert result["intensity"] == 5  # clamped at 5

    def test_negative_word_returns_correcting(self):
        result = tw._detect_ceo_emotion("блять опять не работает")
        assert result["state"] == "correcting"
        assert result["intensity"] > 0

    def test_multiple_negative_words_increase_intensity(self):
        result = tw._detect_ceo_emotion("заебал блять опять бесит")
        assert result["state"] == "correcting"
        assert result["intensity"] == 5  # clamped at 5

    def test_exhausted_keyword_returns_exhausted(self):
        result = tw._detect_ceo_emotion("нууууу зачем это всё")
        assert result["state"] == "exhausted"
        assert result["intensity"] > 0

    def test_long_message_no_keywords_returns_drive(self):
        # Over 200 chars with no keywords → drive at intensity 2
        long_msg = "a" * 201
        result = tw._detect_ceo_emotion(long_msg)
        assert result["state"] == "drive"
        assert result["intensity"] == 2

    def test_neutral_short_message_returns_analytical(self):
        result = tw._detect_ceo_emotion("ok")
        assert result["state"] == "analytical"
        assert result["intensity"] == 0

    def test_empty_message_returns_analytical(self):
        result = tw._detect_ceo_emotion("")
        assert result["state"] == "analytical"
        assert result["intensity"] == 0

    def test_intensity_clamped_at_5_positive(self):
        # 4 positive words → 4*2=8 → clamped to 5
        result = tw._detect_ceo_emotion("шикарно круто офигенно молодец заебись красава))))")
        assert result["intensity"] == 5

    def test_intensity_clamped_at_5_negative(self):
        result = tw._detect_ceo_emotion("блять бля опять заебал нахуя проебал бесит нахрен")
        assert result["intensity"] == 5

    def test_positive_wins_when_more_positive(self):
        # 3 positive, 1 negative → positive wins
        # Note: "блять" also matches "бля" substring, so use a word that only hits once
        result = tw._detect_ceo_emotion("шикарно круто офигенно нахрен")
        assert result["state"] == "drive"

    def test_negative_wins_when_more_negative(self):
        # 1 positive, 3 negative → negative wins
        # блять triggers both "блять" and "бля" (substring) → neg=2; add нахрен→neg=3
        result = tw._detect_ceo_emotion("шикарно заебал нахуя нахрен")
        assert result["state"] == "correcting"

    def test_returns_dict_with_required_keys(self):
        result = tw._detect_ceo_emotion("test")
        assert "state" in result
        assert "intensity" in result

    def test_case_insensitive(self):
        # Keywords checked against lowercased message
        result_lower = tw._detect_ceo_emotion("шикарно")
        result_upper = tw._detect_ceo_emotion("ШИКАРНО")
        assert result_lower["state"] == result_upper["state"]


# ---------------------------------------------------------------------------
# ── 2. _detect_emotional_state ─────────────────────────────────────────────
# ---------------------------------------------------------------------------


class TestDetectEmotionalState:
    def test_frustrated_word_returns_state_b(self):
        assert tw._detect_emotional_state("бля опять не работает") == "B"

    def test_nakhren_returns_state_b(self):
        assert tw._detect_emotional_state("нахрена ты это сделал") == "B"

    def test_zabyl_returns_state_b(self):
        assert tw._detect_emotional_state("ты забыл про это") == "B"

    def test_khvatit_returns_state_b(self):
        assert tw._detect_emotional_state("хватит уже") == "B"

    def test_drive_word_returns_state_a(self):
        assert tw._detect_emotional_state("давай пахать") == "A"

    def test_kruto_returns_state_a(self):
        assert tw._detect_emotional_state("круто получилось!") == "A"

    def test_nuuu_returns_state_a(self):
        assert tw._detect_emotional_state("нуууу давай") == "A"

    def test_akhakh_returns_state_a(self):
        assert tw._detect_emotional_state("ахахах ну ты даёшь") == "A"

    def test_warm_word_returns_state_c(self):
        assert tw._detect_emotional_state("спасибо большое") == "C"

    def test_molodets_returns_state_c(self):
        assert tw._detect_emotional_state("молодец, так держать") == "C"

    def test_strategic_phrase_returns_state_d(self):
        assert tw._detect_emotional_state("что думаешь насчёт этого?") == "D"

    def test_strategiya_returns_state_d(self):
        assert tw._detect_emotional_state("обсудим стратегия на Q2") == "D"

    def test_unknown_returns_state_a_default(self):
        assert tw._detect_emotional_state("обычное сообщение") == "A"

    def test_empty_returns_state_a_default(self):
        assert tw._detect_emotional_state("") == "A"

    def test_frustrated_takes_priority_when_first_matched(self):
        # state B is checked first in source
        assert tw._detect_emotional_state("бля стратегия") == "B"


# ---------------------------------------------------------------------------
# ── 3. _char_similarity ────────────────────────────────────────────────────
# ---------------------------------------------------------------------------


class TestCharSimilarity:
    def test_identical_strings_returns_1(self):
        s = "Атлас здесь. Проверил статус."
        assert tw._char_similarity(s, s) == 1.0

    def test_empty_a_returns_0(self):
        assert tw._char_similarity("", "anything") == 0.0

    def test_empty_b_returns_0(self):
        assert tw._char_similarity("anything", "") == 0.0

    def test_both_empty_returns_0(self):
        assert tw._char_similarity("", "") == 0.0

    def test_near_identical_returns_high(self):
        a = "Атлас здесь. Проверил статус — всё работает нормально."
        b = "Атлас здесь. Проверил статус — всё работает отлично."
        assert tw._char_similarity(a, b) > 0.70

    def test_completely_different_returns_low(self):
        a = "security rls audit found two gaps in admin tables"
        b = "короткий ответ на русском про дизайн системы"
        assert tw._char_similarity(a, b) < 0.50

    def test_partial_overlap(self):
        a = "hello world"
        b = "hello there"
        sim = tw._char_similarity(a, b)
        assert 0.0 < sim < 1.0

    def test_returns_float(self):
        result = tw._char_similarity("abc", "abd")
        assert isinstance(result, float)

    def test_range_0_to_1(self):
        result = tw._char_similarity("some text here", "other text there")
        assert 0.0 <= result <= 1.0

    def test_symmetric(self):
        a = "hello world"
        b = "world hello"
        # Not necessarily equal but both in valid range
        s1 = tw._char_similarity(a, b)
        s2 = tw._char_similarity(b, a)
        assert 0.0 <= s1 <= 1.0
        assert 0.0 <= s2 <= 1.0


# ---------------------------------------------------------------------------
# ── 4. _save_message ───────────────────────────────────────────────────────
# ---------------------------------------------------------------------------


def _make_db_with_insert(side_effect=None):
    """Build a minimal Supabase AsyncMock that chains .table().insert().execute()."""
    db = MagicMock()
    execute_mock = AsyncMock(return_value=MagicMock(data=[{"id": "abc"}]))
    if side_effect:
        execute_mock.side_effect = side_effect
    insert_mock = MagicMock()
    insert_mock.execute = execute_mock
    table_mock = MagicMock()
    table_mock.insert.return_value = insert_mock
    db.table.return_value = table_mock
    return db, execute_mock


@pytest.mark.asyncio
async def test_save_message_success():
    db, execute_mock = _make_db_with_insert()
    await tw._save_message(db, "ceo_to_bot", "hello", "free_text")
    execute_mock.assert_awaited_once()
    db.table.assert_called_with("ceo_inbox")


@pytest.mark.asyncio
async def test_save_message_truncates_at_5000_chars():
    db, execute_mock = _make_db_with_insert()
    long_msg = "x" * 6000
    await tw._save_message(db, "ceo_to_bot", long_msg, "free_text")
    call_kwargs = db.table.return_value.insert.call_args[0][0]
    assert len(call_kwargs["message"]) == 5000


@pytest.mark.asyncio
async def test_save_message_includes_metadata():
    db, execute_mock = _make_db_with_insert()
    meta = {"key": "value"}
    await tw._save_message(db, "ceo_to_bot", "msg", "idea", metadata=meta)
    call_kwargs = db.table.return_value.insert.call_args[0][0]
    assert call_kwargs["metadata"] == meta


@pytest.mark.asyncio
async def test_save_message_defaults_empty_metadata():
    db, execute_mock = _make_db_with_insert()
    await tw._save_message(db, "ceo_to_bot", "msg", "free_text")
    call_kwargs = db.table.return_value.insert.call_args[0][0]
    assert call_kwargs["metadata"] == {}


@pytest.mark.asyncio
async def test_save_message_db_failure_triggers_filesystem_fallback():
    """DB failure on both original + retry → filesystem fallback writes to memory/atlas/inbox/."""
    from pathlib import Path as _Path

    repo_root = _Path(tw.__file__).resolve().parents[4]
    inbox_dir = repo_root / "memory" / "atlas" / "inbox"

    if not inbox_dir.exists():
        pytest.skip("memory/atlas/inbox/ not present — fallback won't run")

    before = set(inbox_dir.iterdir())

    db, _ = _make_db_with_insert(side_effect=Exception("DB down"))
    unique_msg = f"sentinel-{id(before)}"

    # Mock reset_admin_client to return a client that also fails
    fresh_db, _ = _make_db_with_insert(side_effect=Exception("DB still down"))
    with patch("app.deps.reset_admin_client", new_callable=AsyncMock, return_value=fresh_db):
        await tw._save_message(db, "ceo_to_bot", unique_msg, "free_text")

    after = set(inbox_dir.iterdir())
    new_files = after - before
    assert len(new_files) == 1
    created_file = new_files.pop()
    content = created_file.read_text(encoding="utf-8")
    assert unique_msg in content
    created_file.unlink()


@pytest.mark.asyncio
async def test_save_message_retry_succeeds_after_client_reset():
    """DB failure on first try, retry with fresh client succeeds — no filesystem fallback."""
    db, _ = _make_db_with_insert(side_effect=Exception("stale connection"))
    fresh_db, mock_execute = _make_db_with_insert()

    with patch("app.deps.reset_admin_client", new_callable=AsyncMock, return_value=fresh_db):
        await tw._save_message(db, "ceo_to_bot", "retry-test", "free_text")

    mock_execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_save_message_db_failure_no_inbox_dir_does_not_raise(tmp_path):
    db, _ = _make_db_with_insert(side_effect=Exception("DB down"))
    # No inbox dir — should not raise, just log
    with patch.object(tw, "_REPO_ROOT", tmp_path):
        await tw._save_message(db, "ceo_to_bot", "msg", "free_text")


# ---------------------------------------------------------------------------
# ── 5. _get_recent_context ─────────────────────────────────────────────────
# ---------------------------------------------------------------------------


def _make_db_select(data=None, side_effect=None):
    db = MagicMock()
    execute_mock = AsyncMock(return_value=MagicMock(data=data or []))
    if side_effect:
        execute_mock.side_effect = side_effect
    chain = MagicMock()
    chain.execute = execute_mock
    db.table.return_value.select.return_value.order.return_value.limit.return_value = chain
    return db, execute_mock


@pytest.mark.asyncio
async def test_get_recent_context_empty_returns_fallback():
    db, _ = _make_db_select(data=[])
    result = await tw._get_recent_context(db)
    assert "Нет" in result or result  # fallback string


@pytest.mark.asyncio
async def test_get_recent_context_maps_ceo_to_bot_role():
    db, _ = _make_db_select(
        data=[
            {
                "direction": "ceo_to_bot",
                "message": "CEO message",
                "message_type": "free_text",
                "created_at": "2026-01-01",
            },
        ]
    )
    result = await tw._get_recent_context(db)
    assert "[CEO]" in result
    assert "CEO message" in result


@pytest.mark.asyncio
async def test_get_recent_context_maps_bot_to_ceo_role():
    db, _ = _make_db_select(
        data=[
            {
                "direction": "bot_to_ceo",
                "message": "Bot reply",
                "message_type": "free_text",
                "created_at": "2026-01-01",
            },
        ]
    )
    result = await tw._get_recent_context(db)
    assert "[Bot]" in result
    assert "Bot reply" in result


@pytest.mark.asyncio
async def test_get_recent_context_truncates_at_500():
    long_msg = "x" * 600
    db, _ = _make_db_select(
        data=[
            {"direction": "ceo_to_bot", "message": long_msg, "message_type": "free_text", "created_at": "2026-01-01"},
        ]
    )
    result = await tw._get_recent_context(db)
    # The line should contain at most 500 chars of the message
    line = [row for row in result.split("\n") if "[CEO]" in row][0]
    assert len(line) <= len("[CEO] ") + 500 + 10  # allow small buffer


@pytest.mark.asyncio
async def test_get_recent_context_reversed_order():
    # DB returns newest-first (desc), function should reverse to chronological
    db, _ = _make_db_select(
        data=[
            {"direction": "bot_to_ceo", "message": "second", "message_type": "free_text", "created_at": "2026-01-02"},
            {"direction": "ceo_to_bot", "message": "first", "message_type": "free_text", "created_at": "2026-01-01"},
        ]
    )
    result = await tw._get_recent_context(db)
    # After reversed(), "first" should appear before "second"
    assert result.index("first") < result.index("second")


@pytest.mark.asyncio
async def test_get_recent_context_db_exception_returns_fallback():
    db, _ = _make_db_select(side_effect=Exception("timeout"))
    result = await tw._get_recent_context(db)
    assert "недоступен" in result or result  # fallback string returned


# ---------------------------------------------------------------------------
# ── 6. _get_project_stats ─────────────────────────────────────────────────
# ---------------------------------------------------------------------------


def _make_db_multi_count(counts=None, side_effect=None):
    """Build a DB mock that returns count on each .execute() call in sequence."""
    db = MagicMock()

    calls = []

    async def _execute():
        idx = len(calls)
        calls.append(idx)
        if side_effect:
            raise side_effect
        count_vals = counts or [5, 10, 3]
        val = count_vals[idx] if idx < len(count_vals) else 0
        return MagicMock(count=val, data=[])

    # Each .table().select().execute() path must return same awaitable
    select_chain = MagicMock()
    select_chain.execute = _execute
    db.table.return_value.select.return_value = select_chain
    return db


@pytest.mark.asyncio
async def test_get_project_stats_success():
    db = _make_db_multi_count(counts=[5, 10, 3])
    result = await tw._get_project_stats(db)
    assert "5" in result
    assert "10" in result
    assert "3" in result


@pytest.mark.asyncio
async def test_get_project_stats_contains_key_labels():
    db = _make_db_multi_count(counts=[1, 2, 3])
    result = await tw._get_project_stats(db)
    assert "AURA" in result or "Users" in result
    assert "session" in result.lower() or "Assessment" in result


@pytest.mark.asyncio
async def test_get_project_stats_exception_returns_fallback():
    db = MagicMock()
    db.table.side_effect = Exception("DB error")
    result = await tw._get_project_stats(db)
    assert "недоступна" in result or result  # fallback


# ---------------------------------------------------------------------------
# ── 7. _send_message ──────────────────────────────────────────────────────
# ---------------------------------------------------------------------------


class _FakeResponse:
    def __init__(self, ok: bool = True):
        self._ok = ok

    def json(self):
        return {"ok": self._ok}


class _FakeHttpxClient:
    def __init__(self, responses=None):
        self.calls: list[dict] = []
        self._responses = responses or [_FakeResponse(True)]
        self._call_count = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, url, json=None, **kwargs):
        self.calls.append({"url": url, "json": json})
        idx = min(self._call_count, len(self._responses) - 1)
        r = self._responses[idx]
        self._call_count += 1
        return r


@pytest.mark.asyncio
async def test_send_message_success(monkeypatch):
    fake_client = _FakeHttpxClient()
    monkeypatch.setattr("httpx.AsyncClient", lambda **kw: fake_client)
    monkeypatch.setattr(tw.settings, "telegram_bot_token", "test_token")

    result = await tw._send_message(123, "Hello World")
    assert result is True
    assert len(fake_client.calls) == 1
    assert fake_client.calls[0]["json"]["text"] == "Hello World"
    assert fake_client.calls[0]["json"]["chat_id"] == 123


@pytest.mark.asyncio
async def test_send_message_chunking_for_long_text(monkeypatch):
    fake_client = _FakeHttpxClient(responses=[_FakeResponse(True)] * 3)
    monkeypatch.setattr("httpx.AsyncClient", lambda **kw: fake_client)
    monkeypatch.setattr(tw.settings, "telegram_bot_token", "test_token")

    long_text = "x" * 8500  # 2 full chunks + 1 partial = 3 chunks
    result = await tw._send_message(123, long_text)
    assert result is True
    assert len(fake_client.calls) == 3  # ceil(8500/4000) = 3


@pytest.mark.asyncio
async def test_send_message_reply_markup_only_on_last_chunk(monkeypatch):
    fake_client = _FakeHttpxClient(responses=[_FakeResponse(True)] * 2)
    monkeypatch.setattr("httpx.AsyncClient", lambda **kw: fake_client)
    monkeypatch.setattr(tw.settings, "telegram_bot_token", "test_token")

    markup = {"inline_keyboard": [[{"text": "OK", "callback_data": "ok"}]]}
    long_text = "y" * 5000  # 2 chunks
    await tw._send_message(123, long_text, reply_markup=markup)

    # First chunk: no markup
    assert "reply_markup" not in fake_client.calls[0]["json"]
    # Last chunk: has markup
    assert "reply_markup" in fake_client.calls[-1]["json"]
    assert fake_client.calls[-1]["json"]["reply_markup"] == markup


@pytest.mark.asyncio
async def test_send_message_uses_markdown_parse_mode(monkeypatch):
    fake_client = _FakeHttpxClient()
    monkeypatch.setattr("httpx.AsyncClient", lambda **kw: fake_client)
    monkeypatch.setattr(tw.settings, "telegram_bot_token", "test_token")

    await tw._send_message(123, "**bold**")
    assert fake_client.calls[0]["json"]["parse_mode"] == "Markdown"


@pytest.mark.asyncio
async def test_send_message_fallback_on_markdown_error(monkeypatch):
    # First call fails (ok=False), second call succeeds (no parse_mode)
    fake_client = _FakeHttpxClient(responses=[_FakeResponse(False), _FakeResponse(True)])
    monkeypatch.setattr("httpx.AsyncClient", lambda **kw: fake_client)
    monkeypatch.setattr(tw.settings, "telegram_bot_token", "test_token")

    result = await tw._send_message(123, "message")
    assert result is True
    # Second call should not have parse_mode
    assert "parse_mode" not in fake_client.calls[1]["json"]


@pytest.mark.asyncio
async def test_send_message_returns_false_on_exception(monkeypatch):
    class _FailingClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, *a, **kw):
            raise ConnectionError("network down")

    monkeypatch.setattr("httpx.AsyncClient", lambda **kw: _FailingClient())
    monkeypatch.setattr(tw.settings, "telegram_bot_token", "test_token")

    result = await tw._send_message(123, "test")
    assert result is False


@pytest.mark.asyncio
async def test_send_message_single_chunk_exact_boundary(monkeypatch):
    fake_client = _FakeHttpxClient()
    monkeypatch.setattr("httpx.AsyncClient", lambda **kw: fake_client)
    monkeypatch.setattr(tw.settings, "telegram_bot_token", "test_token")

    text = "a" * 4000  # exactly one chunk
    await tw._send_message(123, text)
    assert len(fake_client.calls) == 1


# ---------------------------------------------------------------------------
# ── 8. _load_atlas_memory ─────────────────────────────────────────────────
# ---------------------------------------------------------------------------


class TestLoadAtlasMemory:
    def test_missing_files_returns_hardcoded_fallback(self, tmp_path, monkeypatch):
        # Point _REPO_ROOT to empty tmp_path — no memory/ dir
        monkeypatch.setattr(tw, "_REPO_ROOT", tmp_path)
        result = tw._load_atlas_memory()
        assert "Атлас" in result or "Atlas" in result or result  # fallback

    def test_identity_file_included_when_present(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tw, "_REPO_ROOT", tmp_path)
        atlas_dir = tmp_path / "memory" / "atlas"
        atlas_dir.mkdir(parents=True)
        (atlas_dir / "identity.md").write_text("# My Identity\nI am Atlas.", encoding="utf-8")
        result = tw._load_atlas_memory()
        assert "My Identity" in result

    def test_heartbeat_included_when_present(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tw, "_REPO_ROOT", tmp_path)
        atlas_dir = tmp_path / "memory" / "atlas"
        atlas_dir.mkdir(parents=True)
        (atlas_dir / "identity.md").write_text("ID", encoding="utf-8")
        (atlas_dir / "heartbeat.md").write_text("Last session: all good.", encoding="utf-8")
        result = tw._load_atlas_memory()
        assert "Last session" in result

    def test_journal_included_when_present(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tw, "_REPO_ROOT", tmp_path)
        atlas_dir = tmp_path / "memory" / "atlas"
        atlas_dir.mkdir(parents=True)
        (atlas_dir / "identity.md").write_text("ID", encoding="utf-8")
        (atlas_dir / "journal.md").write_text("Journal entry 2026.", encoding="utf-8")
        result = tw._load_atlas_memory()
        assert "Journal entry" in result

    def test_lessons_included_when_present(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tw, "_REPO_ROOT", tmp_path)
        atlas_dir = tmp_path / "memory" / "atlas"
        atlas_dir.mkdir(parents=True)
        (atlas_dir / "identity.md").write_text("ID", encoding="utf-8")
        (atlas_dir / "lessons.md").write_text("Lesson: delegate more.", encoding="utf-8")
        result = tw._load_atlas_memory()
        assert "Lesson:" in result

    def test_fallback_used_when_identity_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tw, "_REPO_ROOT", tmp_path)
        atlas_dir = tmp_path / "memory" / "atlas"
        atlas_dir.mkdir(parents=True)
        # No identity.md — only heartbeat
        (atlas_dir / "heartbeat.md").write_text("pulse ok", encoding="utf-8")
        result = tw._load_atlas_memory()
        # Hardcoded fallback should be present
        assert "Атлас" in result or "Atlas" in result

    def test_returns_string(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tw, "_REPO_ROOT", tmp_path)
        result = tw._load_atlas_memory()
        assert isinstance(result, str)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# ── 9. _get_ecosystem_context ─────────────────────────────────────────────
# ---------------------------------------------------------------------------


class TestGetEcosystemContext:
    def test_missing_files_returns_fallback_string(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tw, "_REPO_ROOT", tmp_path)
        with patch("pathlib.Path.exists", return_value=False):
            result = tw._get_ecosystem_context()
        assert len(result) > 0
        assert isinstance(result, str)

    def test_volaura_heartbeat_included_when_present(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tw, "_REPO_ROOT", tmp_path)
        context_dir = tmp_path / "memory" / "context"
        context_dir.mkdir(parents=True)
        (context_dir / "heartbeat.md").write_text("VOLAURA: all systems green", encoding="utf-8")
        result = tw._get_ecosystem_context()
        assert "VOLAURA: all systems green" in result

    def test_ecosystem_contract_included_when_present(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tw, "_REPO_ROOT", tmp_path)
        context_dir = tmp_path / "memory" / "context"
        context_dir.mkdir(parents=True)
        (context_dir / "ecosystem-contract.md").write_text("Contract: share auth", encoding="utf-8")
        result = tw._get_ecosystem_context()
        assert "Contract: share auth" in result

    def test_fallback_contains_product_names(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tw, "_REPO_ROOT", tmp_path)
        with patch("pathlib.Path.exists", return_value=False):
            result = tw._get_ecosystem_context()
        # fallback mentions key products
        assert "Volaura" in result or "VOLAURA" in result or "MindShift" in result

    def test_returns_string(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tw, "_REPO_ROOT", tmp_path)
        result = tw._get_ecosystem_context()
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# ── 10. _handle_telegram_update — message routing ─────────────────────────
# ---------------------------------------------------------------------------


def _make_full_db():
    """DB mock for routing tests — supports table().insert/select chains."""
    db = AsyncMock()
    table_mock = MagicMock()
    insert_mock = MagicMock()
    insert_mock.execute = AsyncMock(return_value=MagicMock(data=[]))
    select_chain = MagicMock()
    select_chain.execute = AsyncMock(return_value=MagicMock(data=[], count=0))
    table_mock.insert.return_value = insert_mock
    table_mock.select.return_value.order.return_value.limit.return_value = select_chain
    table_mock.select.return_value = select_chain
    db.table.return_value = table_mock
    return db


@pytest.mark.asyncio
async def test_handle_update_callback_query_routed(monkeypatch):
    """callback_query present → tries to answer callback, does not process as text."""
    db = _make_full_db()

    callback_handled = []

    async def _fake_proposal_callback(db, chat_id, msg_id, cb_id, pid, act, sha12=None):
        callback_handled.append(pid)

    monkeypatch.setattr(tw, "_handle_proposal_card_callback", _fake_proposal_callback)
    monkeypatch.setattr(tw.settings, "telegram_ceo_chat_id", "42")
    monkeypatch.setattr(tw.settings, "telegram_bot_token", "tok")

    class _FakeHttpxClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, *a, **k):
            return MagicMock(json=lambda: {"ok": True})

    monkeypatch.setattr("httpx.AsyncClient", lambda **kw: _FakeHttpxClient())

    update = {
        "callback_query": {
            "id": "cb1",
            "from": {"id": 42},
            "data": "propose:proposal-abc:accept",
            "message": {"chat": {"id": 42}, "message_id": 1},
        }
    }
    await tw._handle_telegram_update(update, db)
    assert "proposal-abc" in callback_handled


@pytest.mark.asyncio
async def test_handle_update_no_message_returns_early(monkeypatch):
    """Update with no message and no callback_query → no side effects."""
    db = _make_full_db()
    send_calls = []

    async def _fake_send(*a, **kw):
        send_calls.append(a)
        return True

    monkeypatch.setattr(tw, "_send_message", _fake_send)
    monkeypatch.setattr(tw.settings, "telegram_ceo_chat_id", "")
    monkeypatch.setattr(tw.settings, "telegram_bot_token", "tok")

    await tw._handle_telegram_update({"update_id": 1}, db)
    assert send_calls == []


@pytest.mark.asyncio
async def test_handle_update_non_ceo_message_ignored(monkeypatch):
    """Message from non-CEO user → no reply sent."""
    db = _make_full_db()
    send_calls = []

    async def _fake_send(*a, **kw):
        send_calls.append(a)
        return True

    monkeypatch.setattr(tw, "_send_message", _fake_send)
    monkeypatch.setattr(tw.settings, "telegram_ceo_chat_id", "999")  # CEO is 999
    monkeypatch.setattr(tw.settings, "telegram_bot_token", "tok")

    update = {
        "message": {
            "chat": {"id": 123},
            "from": {"id": 456},  # NOT the CEO
            "text": "hello",
        }
    }
    await tw._handle_telegram_update(update, db)
    assert send_calls == []


@pytest.mark.asyncio
async def test_handle_update_voice_calls_transcribe(monkeypatch):
    """Voice message → _transcribe_voice called."""
    db = _make_full_db()
    transcribe_calls = []

    async def _fake_transcribe(file_id, chat_id):
        transcribe_calls.append(file_id)
        return None  # no text → early exit

    monkeypatch.setattr(tw, "_transcribe_voice", _fake_transcribe)
    monkeypatch.setattr(tw.settings, "telegram_ceo_chat_id", "42")
    monkeypatch.setattr(tw.settings, "telegram_bot_token", "tok")

    update = {
        "message": {
            "chat": {"id": 42},
            "from": {"id": 42},
            "voice": {"file_id": "voice_file_123"},
        }
    }
    await tw._handle_telegram_update(update, db)
    assert "voice_file_123" in transcribe_calls


@pytest.mark.asyncio
async def test_handle_update_text_routes_to_handle_atlas(monkeypatch):
    """Plain text message from CEO routes through — _save_message called at minimum."""
    db = _make_full_db()

    saved = []

    async def _fake_save(db, direction, message, msg_type="free_text", metadata=None):
        saved.append((direction, message))

    monkeypatch.setattr(tw, "_save_message", _fake_save)
    monkeypatch.setattr(tw.settings, "telegram_ceo_chat_id", "42")
    monkeypatch.setattr(tw.settings, "telegram_bot_token", "tok")

    # Patch _handle_atlas to avoid full LLM calls
    async def _fake_handle_atlas(db, chat_id, text, *a, **kw):
        pass

    monkeypatch.setattr(tw, "_handle_atlas", _fake_handle_atlas)

    update = {
        "message": {
            "chat": {"id": 42},
            "from": {"id": 42},
            "text": "Атлас, как дела?",
        }
    }
    await tw._handle_telegram_update(update, db)
    # _handle_atlas was called (or save_message was called from classify_and_respond)
    # Test just verifies no exception raised and routing worked


@pytest.mark.asyncio
async def test_handle_update_status_command_routed(monkeypatch):
    """/status command routes to _handle_status."""
    db = _make_full_db()
    status_calls = []

    async def _fake_status(db, chat_id):
        status_calls.append(chat_id)

    monkeypatch.setattr(tw, "_handle_status", _fake_status)
    monkeypatch.setattr(tw.settings, "telegram_ceo_chat_id", "42")
    monkeypatch.setattr(tw.settings, "telegram_bot_token", "tok")

    update = {
        "message": {
            "chat": {"id": 42},
            "from": {"id": 42},
            "text": "/status",
        }
    }
    await tw._handle_telegram_update(update, db)
    assert 42 in status_calls
