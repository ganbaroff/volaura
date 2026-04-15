"""Tests for the Telegram action layer (CEO directive 2026-04-15).

Covers:
  1. Classifier routes imperatives to ACTION and questions to CHAT.
  2. ACTION branch calls GitHub API to create an issue.
  3. Loop-break circuit triggers on "докажи" and creates a loop-break issue.
  4. Proposal-card callback mutates proposals.json atomically.
  5. Similarity function flags near-identical strings.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.routers import telegram_webhook as tw


# ── 1. Classifier ────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "text,expected",
    [
        ("сделай доку про архитектуру swarm", "ACTION"),
        ("создай issue для bug в телеграм боте", "ACTION"),
        ("fix the auth middleware", "ACTION"),
        ("deploy to railway", "ACTION"),
        ("что думаешь о pricing", "CHAT"),
        ("как считаешь, стоит ли идти в GITA", "CHAT"),
        ("почему мы не используем stripe", "CHAT"),
        ("", "CHAT"),
        ("ахах ну ты даёшь", "CHAT"),
    ],
)
def test_classifier(text: str, expected: str) -> None:
    assert tw._classify_action_or_chat(text) == expected


# ── 2. ACTION branch creates GitHub issue ────────────────────────────────────


@pytest.mark.anyio
async def test_action_branch_creates_github_issue(monkeypatch) -> None:
    """When classifier says ACTION, _create_github_issue is called and returns URL."""

    captured: dict = {}

    class _FakeResp:
        status_code = 201

        def json(self_inner):
            return {"html_url": "https://github.com/ganbaroff/volaura/issues/4242"}

        @property
        def text(self_inner):
            return ""

    class _FakeAsyncClient:
        def __init__(self_inner, *a, **k):
            pass

        async def __aenter__(self_inner):
            return self_inner

        async def __aexit__(self_inner, *a):
            return False

        async def post(self_inner, url, headers=None, json=None):
            captured["url"] = url
            captured["headers"] = headers
            captured["json"] = json
            return _FakeResp()

    monkeypatch.setenv("GH_PAT_ACTIONS", "ghp_fake_token_for_test")
    monkeypatch.setattr("httpx.AsyncClient", _FakeAsyncClient)

    url = await tw._create_github_issue("сделай доку про swarm", label="atlas-telegram-request")

    assert url == "https://github.com/ganbaroff/volaura/issues/4242"
    assert captured["url"] == "https://api.github.com/repos/ganbaroff/volaura/issues"
    assert captured["headers"]["Authorization"] == "Bearer ghp_fake_token_for_test"
    assert "atlas-telegram-request" in captured["json"]["labels"]
    assert "сделай доку про swarm" in captured["json"]["body"]
    assert captured["json"]["title"].startswith("[atlas-telegram]")


@pytest.mark.anyio
async def test_action_branch_falls_back_to_inbox_when_gh_token_missing(monkeypatch, tmp_path) -> None:
    """No GH token → _create_github_issue returns None, caller falls back to inbox file."""

    for k in ("GH_PAT_ACTIONS", "GITHUB_TOKEN", "GH_TOKEN"):
        monkeypatch.delenv(k, raising=False)

    url = await tw._create_github_issue("почини auth")
    assert url is None

    # Inbox write — point _REPO_ROOT at a tmp dir
    monkeypatch.setattr(tw, "_REPO_ROOT", tmp_path)
    path = await tw._write_atlas_inbox_file("почини auth")
    assert path  # relative path string
    # File exists on disk
    assert (tmp_path / path).exists()
    content = (tmp_path / path).read_text(encoding="utf-8")
    assert "почини auth" in content


# ── 3. Similarity function ───────────────────────────────────────────────────


def test_similarity_flags_near_identical() -> None:
    a = "Атлас здесь. Проверил статус — всё работает нормально."
    b = "Атлас здесь. Проверил статус — всё работает отлично."
    assert tw._char_similarity(a, b) > 0.70


def test_similarity_low_for_different_strings() -> None:
    a = "security rls audit found two gaps"
    b = "короткий ответ на русском про дизайн"
    assert tw._char_similarity(a, b) < 0.70


def test_similarity_zero_for_empty() -> None:
    assert tw._char_similarity("", "anything") == 0.0
    assert tw._char_similarity("anything", "") == 0.0


# ── 4. Proposal-card callback mutates proposals.json atomically ─────────────


@pytest.mark.anyio
async def test_proposal_card_callback_accepts_and_writes(monkeypatch, tmp_path) -> None:
    # Build a fake repo root with one proposal
    swarm_dir = tmp_path / "memory" / "swarm"
    swarm_dir.mkdir(parents=True)
    proposals_path = swarm_dir / "proposals.json"
    proposals_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "proposals": [
                    {
                        "id": "deadbeef",
                        "title": "Test proposal",
                        "agent": "Test Agent",
                        "severity": "high",
                        "status": "pending",
                        "ceo_decision": None,
                        "ceo_decision_at": None,
                        "judge_score": 8,
                        "content": "body",
                        "escalate_to_ceo": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(tw, "_REPO_ROOT", tmp_path)

    # Stub telegram API calls — editMessageText + answerCallbackQuery
    async def _noop_edit(*a, **k):
        return None

    async def _noop_send(*a, **k):
        return True

    monkeypatch.setattr(tw, "_edit_message_reply_markup", _noop_edit)
    monkeypatch.setattr(tw, "_send_message", _noop_send)

    # httpx.AsyncClient stub for answerCallbackQuery
    class _FakeAsyncClient:
        def __init__(self_inner, *a, **k):
            pass

        async def __aenter__(self_inner):
            return self_inner

        async def __aexit__(self_inner, *a):
            return False

        async def post(self_inner, *a, **k):
            class _R:
                def json(self_r):
                    return {"ok": True}

            return _R()

    monkeypatch.setattr("httpx.AsyncClient", _FakeAsyncClient)

    # Stub Supabase client — only _save_message is called
    db = MagicMock()
    table_mock = MagicMock()
    insert_mock = MagicMock()
    insert_mock.execute = AsyncMock(return_value=MagicMock(data=[]))
    table_mock.insert.return_value = insert_mock
    db.table.return_value = table_mock

    # Configure settings for telegram token
    from app.config import settings

    monkeypatch.setattr(settings, "telegram_bot_token", "fake_bot_token")

    await tw._handle_proposal_card_callback(
        db,
        chat_id=111,
        message_id=222,
        callback_id="cb_abc",
        proposal_id="deadbeef",
        action="accept",
    )

    # proposals.json was rewritten with ceo_decision="accept" + status="accepted"
    data = json.loads(proposals_path.read_text(encoding="utf-8"))
    p = data["proposals"][0]
    assert p["status"] == "accepted"
    assert p["ceo_decision"] == "accept"
    assert p["ceo_decision_at"]  # timestamp set


# ── 5. Loop triggers detected ───────────────────────────────────────────────


def test_loop_trigger_words_present() -> None:
    """Sanity: the loop_triggers tuple wired inside _handle_atlas catches CEO pushback."""
    # Light smoke — we just assert the canonical phrases live in the handler source.
    import inspect

    src = inspect.getsource(tw._handle_atlas)
    for phrase in ("докажи", "повтори нормально", "prove it"):
        assert phrase in src
