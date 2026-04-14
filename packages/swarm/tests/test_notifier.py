"""Tests for packages.swarm.notifier — vacation-mode gate + 6h cooldown.

Does not hit Telegram. Patches urlopen and the log/vacation paths to tmp files.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

import packages.swarm.notifier as notifier


@pytest.fixture(autouse=True)
def _isolate_log_and_vacation(tmp_path, monkeypatch):
    """Re-point the module's globals at temp files so tests don't touch real state."""
    log = tmp_path / "notification-log.jsonl"
    vacation = tmp_path / "vacation-mode.json"
    monkeypatch.setattr(notifier, "NOTIFICATION_LOG", log)
    monkeypatch.setattr(notifier, "VACATION_FILE", vacation)
    # Default env: pretend we have credentials so _telegram_send would otherwise try.
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("TELEGRAM_CEO_CHAT_ID", "123456")
    return log, vacation


def _force_deliver(monkeypatch, success: bool = True):
    """Stub urlopen so _telegram_send returns success without a real HTTP call."""
    fake_resp = MagicMock()
    fake_resp.status = 200 if success else 500
    fake_resp.__enter__ = lambda self: self
    fake_resp.__exit__ = lambda *a: False
    monkeypatch.setattr(
        notifier.urllib.request, "urlopen", lambda *a, **k: fake_resp
    )


def test_sends_when_no_vacation_no_cooldown(monkeypatch, _isolate_log_and_vacation):
    _force_deliver(monkeypatch, success=True)
    result = notifier.send_notification("digest", "first ping", severity="info")
    assert result is True


def test_vacation_suppresses_non_critical(_isolate_log_and_vacation, monkeypatch):
    _, vacation = _isolate_log_and_vacation
    vacation.write_text(json.dumps({"enabled": True}), encoding="utf-8")
    _force_deliver(monkeypatch, success=True)
    result = notifier.send_notification("digest", "vacation test", severity="info")
    assert result is False

    # Audit line recorded with suppression_reason
    log, _ = _isolate_log_and_vacation
    entry = json.loads(log.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert entry["suppression_reason"] == "vacation_mode"
    assert entry["delivered"] is False


def test_vacation_allows_critical(_isolate_log_and_vacation, monkeypatch):
    _, vacation = _isolate_log_and_vacation
    vacation.write_text(json.dumps({"enabled": True}), encoding="utf-8")
    _force_deliver(monkeypatch, success=True)
    result = notifier.send_notification("error", "critical alert", severity="critical")
    assert result is True


def test_expired_vacation_does_not_suppress(_isolate_log_and_vacation, monkeypatch):
    _, vacation = _isolate_log_and_vacation
    past = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
    vacation.write_text(json.dumps({"enabled": True, "until": past}), encoding="utf-8")
    _force_deliver(monkeypatch, success=True)
    result = notifier.send_notification("digest", "post-vacation", severity="info")
    assert result is True


def test_cooldown_suppresses_second_non_critical(_isolate_log_and_vacation, monkeypatch):
    _force_deliver(monkeypatch, success=True)
    # First call lands; second in same category within 6h must be suppressed.
    first = notifier.send_notification("digest", "1st", severity="info")
    assert first is True
    second = notifier.send_notification("digest", "2nd", severity="info")
    assert second is False

    log, _ = _isolate_log_and_vacation
    entries = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert entries[-1]["suppression_reason"] == "cooldown"


def test_cooldown_does_not_block_different_category(_isolate_log_and_vacation, monkeypatch):
    _force_deliver(monkeypatch, success=True)
    a = notifier.send_notification("digest", "digest-line", severity="info")
    b = notifier.send_notification("incident", "incident-line", severity="info")
    assert a is True
    assert b is True


def test_cooldown_bypassed_by_critical(_isolate_log_and_vacation, monkeypatch):
    _force_deliver(monkeypatch, success=True)
    notifier.send_notification("error", "first", severity="error")
    # Critical in same category should still land.
    result = notifier.send_notification("error", "critical follow-up", severity="critical")
    assert result is True


def test_failed_delivery_does_not_set_cooldown_anchor(_isolate_log_and_vacation, monkeypatch):
    # First send fails (HTTP 500). Second should NOT be cooldown-blocked.
    _force_deliver(monkeypatch, success=False)
    first = notifier.send_notification("digest", "failing ping", severity="info")
    assert first is False
    # Now allow success — second must go through (no successful anchor for cooldown).
    _force_deliver(monkeypatch, success=True)
    second = notifier.send_notification("digest", "retry ping", severity="info")
    assert second is True


def test_no_token_still_logs(_isolate_log_and_vacation, monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    result = notifier.send_notification("info", "no-token path", severity="info")
    assert result is False
    log, _ = _isolate_log_and_vacation
    content = log.read_text(encoding="utf-8")
    assert "no-token path" in content
