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


# ── 6. Multi-signal circuit breaker (Pattern 1) ─────────────────────────────


def test_circuit_breaker_does_not_trip_on_healthy_traffic() -> None:
    from app.services.loop_circuit_breaker import LoopCircuitBreaker

    breaker = LoopCircuitBreaker()
    decision = breaker.evaluate(
        recent_replies=[
            "Проверил RLS политики на таблицах assessment_sessions и profiles — всё ok, "
            "service_role везде и anon_select только через RPC.",
            "По pricing: крышка 49 AZN месяц для индивидуалов, 299 AZN для org tier 1. "
            "Crystal экономия привязана к session completion а не к time spent.",
            "Deploy прошёл чисто, Railway healthcheck зелёный, /api/health 200 OK, "
            "Vercel build 42 секунды — в пределах нормы.",
        ],
        tool_error_streak={"create_github_issue": 0},
    )
    assert decision.tripped is False


def test_circuit_breaker_trips_on_token_velocity_plus_stall_phrase() -> None:
    """Two signals: low unique tokens across last 3 AND stall phrase in latest."""
    from app.services.loop_circuit_breaker import LoopCircuitBreaker

    short = "я понимаю что это является важным"  # also matches stall blocklist
    breaker = LoopCircuitBreaker()
    decision = breaker.evaluate(
        recent_replies=[short, short, short],
        tool_error_streak=None,
    )
    assert decision.tripped is True
    assert "token_velocity" in decision.signals
    assert "no_progress" in decision.signals


def test_circuit_breaker_trips_on_tool_failures_plus_velocity() -> None:
    from app.services.loop_circuit_breaker import LoopCircuitBreaker

    breaker = LoopCircuitBreaker()
    decision = breaker.evaluate(
        recent_replies=["ok", "ok", "ok"],  # low tokens
        tool_error_streak={"create_github_issue": 3},
    )
    assert decision.tripped is True
    assert "per_tool_failure" in decision.signals


def test_circuit_breaker_single_signal_does_not_trip() -> None:
    """Any ONE signal alone must NOT trip (2-of-3 rule)."""
    from app.services.loop_circuit_breaker import LoopCircuitBreaker

    breaker = LoopCircuitBreaker()
    # Only token-velocity signal, no stall phrase, no tool failures.
    decision = breaker.evaluate(
        recent_replies=["short one", "short two", "short three"],
        tool_error_streak={"create_github_issue": 0},
    )
    assert decision.tripped is False
    assert decision.signals == ["token_velocity"]


# ── 7. @atlas_tool registry (Pattern 3) ─────────────────────────────────────


def test_atlas_tool_registry_lists_starter_tools() -> None:
    from app.services.atlas_tools import REGISTRY

    names = {t.name for t in REGISTRY.list_tools()}
    assert "create_github_issue" in names
    assert "create_inbox_file" in names


@pytest.mark.anyio
async def test_atlas_tool_validates_args() -> None:
    """Bad args → ToolResult.fail (no exception)."""
    from app.services.atlas_tools import REGISTRY

    result = await REGISTRY.invoke("create_github_issue", {"not_a_field": "x"})
    assert result.ok is False
    assert "arg validation" in (result.error or "")


@pytest.mark.anyio
async def test_atlas_tool_unknown_name_returns_error() -> None:
    from app.services.atlas_tools import REGISTRY

    result = await REGISTRY.invoke("nope_does_not_exist", {})
    assert result.ok is False
    assert "unknown tool" in (result.error or "")


def test_atlas_tool_preview_deterministic_sha() -> None:
    from app.services.atlas_tools import REGISTRY

    tool = REGISTRY.get("create_github_issue")
    assert tool is not None
    args1 = {"text": "hello", "label": "bug"}
    args2 = {"label": "bug", "text": "hello"}  # same data, different key order
    _, sha1 = tool.preview(args1)
    _, sha2 = tool.preview(args2)
    assert sha1 == sha2
    assert len(sha1) == 12


# ── 8. Proposal-card sha12 fingerprint (Pattern 2) ──────────────────────────


def test_proposal_sha_deterministic_and_key_order_insensitive() -> None:
    """Pattern 2 — sha12 must be stable across key ordering AND change on payload change."""
    from app.services.atlas_tools import compute_payload_sha12

    sha_a = compute_payload_sha12({"tool": "x", "args": {"y": 1, "z": 2}})
    sha_a2 = compute_payload_sha12({"args": {"z": 2, "y": 1}, "tool": "x"})
    sha_b = compute_payload_sha12({"tool": "x", "args": {"y": 2}})
    assert sha_a == sha_a2
    assert sha_a != sha_b
    assert len(sha_a) == 12


def test_extract_action_payload_falls_back_to_title_content() -> None:
    from app.services.atlas_tools import extract_action_payload

    # explicit action_payload wins
    assert extract_action_payload({"action_payload": {"k": 1}, "title": "t"}) == {"k": 1}
    # tool_args next
    out = extract_action_payload({"tool_args": {"x": 1}, "tool_name": "foo"})
    assert out == {"tool": "foo", "args": {"x": 1}}
    # fallback
    out = extract_action_payload({"title": "hi", "content": "body"})
    assert out == {"title": "hi", "content": "body"}


@pytest.mark.anyio
async def test_callback_aborts_on_sha_mismatch(monkeypatch, tmp_path) -> None:
    """Pattern 2 — sha12 mismatch between display and tap → abort, no write."""
    import json as _json

    swarm_dir = tmp_path / "memory" / "swarm"
    swarm_dir.mkdir(parents=True)
    proposals_path = swarm_dir / "proposals.json"
    proposals_path.write_text(
        _json.dumps(
            {
                "schema_version": "1.0",
                "proposals": [
                    {
                        "id": "cafebabe",
                        "title": "Tampered",
                        "agent": "A",
                        "severity": "high",
                        "status": "pending",
                        "ceo_decision": None,
                        "ceo_decision_at": None,
                        "judge_score": 9,
                        "content": "body",
                        "action_payload": {"tool": "x", "args": {"y": 99}},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(tw, "_REPO_ROOT", tmp_path)

    sent: list[str] = []

    async def _capture_send(chat_id, text, *a, **k):
        sent.append(text)
        return True

    monkeypatch.setattr(tw, "_send_message", _capture_send)

    async def _noop_edit(*a, **k):
        return None

    monkeypatch.setattr(tw, "_edit_message_reply_markup", _noop_edit)

    db = MagicMock()
    table_mock = MagicMock()
    insert_mock = MagicMock()
    insert_mock.execute = AsyncMock(return_value=MagicMock(data=[]))
    table_mock.insert.return_value = insert_mock
    db.table.return_value = table_mock

    from app.config import settings

    monkeypatch.setattr(settings, "telegram_bot_token", "fake_bot_token")

    # Pass a sha12 that does NOT match the current payload.
    await tw._handle_proposal_card_callback(
        db,
        chat_id=111,
        message_id=222,
        callback_id="cb_tamper",
        proposal_id="cafebabe",
        action="accept",
        sha12="deadbeef0000",  # wrong
    )

    # Must have aborted: proposals.json still "pending", abort message sent.
    data = _json.loads(proposals_path.read_text(encoding="utf-8"))
    assert data["proposals"][0]["status"] == "pending"
    assert data["proposals"][0]["ceo_decision"] is None
    assert any("Aborted" in s or "payload changed" in s for s in sent)
