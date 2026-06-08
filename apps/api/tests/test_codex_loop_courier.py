"""Unit tests for the codex-loop courier core.

Covers the signed handoff layer in ``scripts/codex_loop_courier.py``:
- append writes a signed block and records the replay ledger
- read skips legacy unsigned entries without breaking
- verify_by_nonce and integrity mismatches behave as expected
- basic input validation stays strict

These tests use ``tmp_path`` so they never touch the real journal.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import codex_loop_courier as courier


BakuTime = datetime(2026, 6, 7, 2, 5, tzinfo=timezone(timedelta(hours=4)))
UTC_TS = "2026-06-06T22:05:00+00:00"
NONCE_1 = UUID("11111111-1111-1111-1111-111111111111")
NONCE_2 = UUID("22222222-2222-2222-2222-222222222222")
NONCE_3 = UUID("33333333-3333-3333-3333-333333333333")
NONCE_4 = UUID("44444444-4444-4444-4444-444444444444")


@pytest.fixture()
def sandbox(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> tuple[Path, Path]:
    """Point the courier at tmp_path-backed journal and ledger files."""
    loop_path = tmp_path / "memory" / "atlas" / "codex-loop.md"
    ledger_path = tmp_path / "memory" / "atlas" / "courier-replay-ledger.jsonl"
    monkeypatch.setattr(courier, "CODEX_LOOP", loop_path)
    monkeypatch.setattr(courier, "REPLAY_LEDGER", ledger_path)
    monkeypatch.setattr(courier, "_baku_now", lambda: BakuTime)
    monkeypatch.setattr(courier, "_iso_now", lambda: UTC_TS)
    return loop_path, ledger_path


def _signed_block(
    *,
    baku_label: str,
    sender: str,
    topic: str,
    nonce: UUID,
    intent: str,
    body: str,
) -> str:
    sha = courier._hash_body(body)
    return (
        f"## {baku_label} · {sender} · {topic}\n"
        f"<!-- signed: sha256={sha} nonce={nonce} sender={sender} "
        f"ts={UTC_TS} intent={intent} spec=courier-protocol-v1 -->\n\n"
        f"{body}\n\n---\n\n"
    )


def _seed_loop(loop_path: Path, content: str) -> None:
    loop_path.parent.mkdir(parents=True, exist_ok=True)
    loop_path.write_text(content, encoding="utf-8")


def test_append_signed_entry_writes_signed_block_and_ledger(sandbox, monkeypatch):
    loop_path, ledger_path = sandbox
    _seed_loop(loop_path, "# Atlas ↔ Codex — Architect Loop Journal\n\n")
    monkeypatch.setattr(courier.uuid, "uuid4", lambda: NONCE_1)

    entry = courier.append_signed_entry(
        topic="handoff",
        sender="atlas",
        intent="decision-record",
        body="Ship the courier core.",
    )

    text = loop_path.read_text(encoding="utf-8")
    assert text.startswith("# Atlas ↔ Codex — Architect Loop Journal\n\n## 2026-06-07 02:05 Baku · atlas · handoff\n")
    assert "<!-- signed: sha256=" in text
    assert "Ship the courier core." in text
    assert entry.nonce == str(NONCE_1)
    assert entry.topic == "handoff"
    assert entry.intent == "decision-record"

    ledger = ledger_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(ledger) == 1
    record = json.loads(ledger[0])
    assert record["nonce"] == str(NONCE_1)
    assert record["sender"] == "atlas"
    assert record["topic"] == "handoff"
    assert record["intent"] == "decision-record"
    assert record["sha256"] == entry.sha256


def test_append_rejects_invalid_sender(sandbox):
    loop_path, _ = sandbox
    _seed_loop(loop_path, "# Journal\n\n")

    with pytest.raises(ValueError, match="sender must be one of"):
        courier.append_signed_entry(topic="handoff", sender="ghost", intent="decision", body="ok")


def test_append_rejects_empty_topic(sandbox):
    loop_path, _ = sandbox
    _seed_loop(loop_path, "# Journal\n\n")

    with pytest.raises(ValueError, match="topic cannot be empty"):
        courier.append_signed_entry(topic="   ", sender="atlas", intent="decision", body="ok")


def test_append_rejects_empty_body(sandbox):
    loop_path, _ = sandbox
    _seed_loop(loop_path, "# Journal\n\n")

    with pytest.raises(ValueError, match="body cannot be empty"):
        courier.append_signed_entry(topic="handoff", sender="atlas", intent="decision", body="   ")


def test_read_skips_legacy_unsigned_entries_and_keeps_newest_first(sandbox, monkeypatch):
    loop_path, _ = sandbox
    legacy_unsigned = (
        "## 2026-06-05 18:00 Baku · atlas · legacy unsigned\n"
        "This block is intentionally unsigned legacy journal text.\n\n"
        "---\n\n"
    )
    older_signed = _signed_block(
        baku_label="2026-06-06 18:00 Baku",
        sender="codex",
        topic="older signed",
        nonce=NONCE_2,
        intent="review",
        body="Older signed body.",
    )
    _seed_loop(
        loop_path,
        "# Atlas ↔ Codex — Architect Loop Journal\n\n" + legacy_unsigned + older_signed,
    )
    monkeypatch.setattr(courier.uuid, "uuid4", lambda: NONCE_1)

    courier.append_signed_entry(
        topic="fresh handoff",
        sender="atlas",
        intent="decision-record",
        body="Fresh signed body.",
    )

    entries = courier.read_recent_entries(limit=10)
    assert len(entries) == 2
    assert [e.topic for e in entries] == ["fresh handoff", "older signed"]
    assert all(e.verified for e in entries)
    assert entries[0].sender == "atlas"
    assert entries[1].sender == "codex"
    assert "legacy unsigned" not in {e.topic for e in entries}


def test_read_recent_entries_limit_honors_requested_count(sandbox, monkeypatch):
    loop_path, _ = sandbox
    older_signed = _signed_block(
        baku_label="2026-06-06 17:45 Baku",
        sender="codex",
        topic="older",
        nonce=NONCE_2,
        intent="decision-record",
        body="Older body.",
    )
    _seed_loop(loop_path, "# Atlas ↔ Codex — Architect Loop Journal\n\n" + older_signed)
    monkeypatch.setattr(courier.uuid, "uuid4", lambda: NONCE_1)

    courier.append_signed_entry(
        topic="newest",
        sender="atlas",
        intent="decision-record",
        body="Newest body.",
    )

    entries = courier.read_recent_entries(limit=1)
    assert len(entries) == 1
    assert entries[0].topic == "newest"
    assert entries[0].verified


def test_verify_entry_by_nonce_succeeds_for_appended_entry(sandbox, monkeypatch):
    loop_path, _ = sandbox
    _seed_loop(loop_path, "# Atlas ↔ Codex — Architect Loop Journal\n\n")
    monkeypatch.setattr(courier.uuid, "uuid4", lambda: NONCE_3)

    entry = courier.append_signed_entry(
        topic="proof",
        sender="atlas",
        intent="decision-record",
        body="Proof body.",
    )

    ok, reason = courier.verify_entry_by_nonce(entry.nonce)
    assert ok is True
    assert "OK" in reason
    assert "sender=atlas" in reason


def test_verify_entry_by_nonce_missing_returns_not_found(sandbox):
    loop_path, _ = sandbox
    _seed_loop(loop_path, "# Atlas ↔ Codex — Architect Loop Journal\n\n")

    ok, reason = courier.verify_entry_by_nonce(str(NONCE_4))
    assert ok is False
    assert "not found" in reason


def test_read_recent_entries_flags_tampered_body(sandbox):
    loop_path, _ = sandbox
    tampered = _signed_block(
        baku_label="2026-06-06 16:30 Baku",
        sender="codex",
        topic="tampered",
        nonce=NONCE_2,
        intent="review",
        body="original body text",
    ).replace("original body text", "tampered body text", 1)
    _seed_loop(loop_path, "# Atlas ↔ Codex — Architect Loop Journal\n\n" + tampered)

    entries = courier.read_recent_entries(limit=10)
    assert len(entries) == 1
    assert entries[0].verified is False
    assert "sha256 mismatch" in entries[0].verify_reason


def test_check_replay_detects_recent_nonce(sandbox, monkeypatch):
    loop_path, _ = sandbox
    _seed_loop(loop_path, "# Atlas ↔ Codex — Architect Loop Journal\n\n")
    monkeypatch.setattr(courier.uuid, "uuid4", lambda: NONCE_1)

    entry = courier.append_signed_entry(
        topic="replay",
        sender="atlas",
        intent="decision-record",
        body="Replay body.",
    )

    ledger = courier._load_ledger()
    is_replay, why = courier._check_replay(entry.nonce, ledger)
    assert is_replay is True
    assert entry.nonce in why
