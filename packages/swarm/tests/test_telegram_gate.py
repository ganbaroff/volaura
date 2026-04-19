"""Tests for telegram_gate — central choke point against agent spam.

Gate rules (2026-04-19):
  1. silence-file kill-switch (bypassable only by emergency=True)
  2. global hourly rate limit (bypassable only by severity=critical)
  3. dedup window 60 min by preview hash (bypassable only by severity=critical)
"""
from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest


@pytest.fixture
def tmp_gate(tmp_path, monkeypatch):
    """Reroute gate-log and silence-file into a temp dir for test isolation."""
    from packages.swarm import telegram_gate as mod

    monkeypatch.setattr(mod, "GATE_LOG", tmp_path / "gate.jsonl")
    monkeypatch.setattr(mod, "SILENCE_FILE", tmp_path / "silenced-until.txt")
    # Reset hourly limit env each test
    monkeypatch.setenv("TELEGRAM_GATE_HOURLY_LIMIT", "10")
    mod._HOURLY_LIMIT = 10  # re-read
    yield mod


class TestKillSwitch:
    def test_no_silence_file_allows_send(self, tmp_gate):
        allowed = tmp_gate.allow_send(
            category="info", severity="info", preview="hello"
        )
        assert allowed is True

    def test_active_silence_blocks_non_critical(self, tmp_gate):
        tmp_gate.silence(hours=1, reason="test")
        allowed = tmp_gate.allow_send(
            category="error", severity="warning", preview="test"
        )
        assert allowed is False

    def test_active_silence_blocks_even_critical(self, tmp_gate):
        """CEO retains silence authority even over criticals (only emergency bypasses)."""
        tmp_gate.silence(hours=1, reason="test")
        allowed = tmp_gate.allow_send(
            category="error", severity="critical", preview="critical error"
        )
        assert allowed is False

    def test_emergency_bypasses_silence(self, tmp_gate):
        tmp_gate.silence(hours=1, reason="test")
        allowed = tmp_gate.allow_send(
            category="error",
            severity="warning",
            preview="83(b) deadline in 6 hours",
            emergency=True,
        )
        assert allowed is True

    def test_expired_silence_file_is_ignored(self, tmp_gate):
        past = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
        tmp_gate.SILENCE_FILE.write_text(f"{past}\nexpired", encoding="utf-8")
        allowed = tmp_gate.allow_send(
            category="info", severity="info", preview="msg"
        )
        assert allowed is True

    def test_lift_silence_removes_file(self, tmp_gate):
        tmp_gate.silence(hours=1)
        assert tmp_gate.SILENCE_FILE.exists()
        tmp_gate.lift_silence()
        assert not tmp_gate.SILENCE_FILE.exists()


class TestHourlyRateLimit:
    def test_hits_limit_blocks_next(self, tmp_gate):
        for i in range(10):
            assert tmp_gate.allow_send(
                category="info", severity="info", preview=f"msg-{i}"
            ) is True
        # 11th blocked
        assert tmp_gate.allow_send(
            category="info", severity="info", preview="msg-11"
        ) is False

    def test_critical_bypasses_rate_limit(self, tmp_gate):
        for i in range(10):
            tmp_gate.allow_send(
                category="info", severity="info", preview=f"msg-{i}"
            )
        # Critical still passes
        assert tmp_gate.allow_send(
            category="error", severity="critical", preview="pager fire"
        ) is True


class TestDedup:
    def test_same_preview_within_window_blocked(self, tmp_gate):
        assert tmp_gate.allow_send(
            category="error", severity="warning", preview="DB timeout"
        ) is True
        # Same preview immediately → dedup
        assert tmp_gate.allow_send(
            category="error", severity="warning", preview="DB timeout"
        ) is False

    def test_different_previews_not_dedup(self, tmp_gate):
        assert tmp_gate.allow_send(
            category="error", severity="warning", preview="DB timeout"
        ) is True
        assert tmp_gate.allow_send(
            category="error", severity="warning", preview="Auth failure"
        ) is True

    def test_critical_bypasses_dedup(self, tmp_gate):
        tmp_gate.allow_send(
            category="error", severity="warning", preview="same preview"
        )
        # Critical with identical preview still passes
        assert tmp_gate.allow_send(
            category="error", severity="critical", preview="same preview"
        ) is True


class TestLogging:
    def test_log_records_allow_and_block(self, tmp_gate):
        tmp_gate.allow_send(
            category="info", severity="info", preview="first"
        )
        tmp_gate.allow_send(
            category="info", severity="info", preview="first"
        )  # dedup block
        tail = tmp_gate._read_log_tail(100)
        assert len(tail) == 2
        assert tail[0]["decision"] == "allow"
        assert tail[1]["decision"] == "block"
        assert tail[1]["reason"] == "dedup"
