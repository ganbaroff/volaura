"""Tests for the Telegram silence threshold (CEO directive 2026-05-09).

Goal: prove that a swarm task where most perspectives failed does NOT
trigger a Telegram notification, but tasks with critical findings or
whistleblower flags always do — regardless of responded ratio.

Reference: codex-loop.md 2026-05-09 «Telegram silence one small commit».
"""
from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_daemon():
    script_path = Path("C:/Projects/VOLAURA/scripts/atlas_swarm_daemon.py")
    spec = importlib.util.spec_from_file_location("atlas_swarm_daemon_telegram_silence", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


# ── _should_send_telegram ─────────────────────────────────────────────────────

def test_send_when_full_response(monkeypatch):
    daemon = _load_daemon()
    monkeypatch.delenv("ATLAS_NOTIFY_DISABLE", raising=False)
    monkeypatch.delenv("ATLAS_NOTIFY_MIN_RESPONDED_RATIO", raising=False)
    ok, reason = daemon._should_send_telegram(responded=17, dispatched=17, crits=0, flags_count=0)
    assert ok and reason == ""


def test_suppress_when_below_threshold_default(monkeypatch):
    """Default threshold 0.4 — 2/17 = 0.118 ratio, must suppress."""
    daemon = _load_daemon()
    monkeypatch.delenv("ATLAS_NOTIFY_DISABLE", raising=False)
    monkeypatch.delenv("ATLAS_NOTIFY_MIN_RESPONDED_RATIO", raising=False)
    monkeypatch.setenv("ATLAS_NOTIFY_FORCE_ON_CRITICAL", "true")
    monkeypatch.setenv("ATLAS_NOTIFY_FORCE_ON_WHISTLEBLOWER", "true")
    ok, reason = daemon._should_send_telegram(responded=2, dispatched=17, crits=0, flags_count=0)
    assert not ok
    assert "ratio" in reason and "threshold" in reason


def test_force_send_on_critical(monkeypatch):
    """Even 2/17 must SEND if there is a critical finding."""
    daemon = _load_daemon()
    monkeypatch.delenv("ATLAS_NOTIFY_DISABLE", raising=False)
    monkeypatch.setenv("ATLAS_NOTIFY_FORCE_ON_CRITICAL", "true")
    ok, _ = daemon._should_send_telegram(responded=2, dispatched=17, crits=1, flags_count=0)
    assert ok


def test_force_send_on_whistleblower(monkeypatch):
    daemon = _load_daemon()
    monkeypatch.delenv("ATLAS_NOTIFY_DISABLE", raising=False)
    monkeypatch.setenv("ATLAS_NOTIFY_FORCE_ON_WHISTLEBLOWER", "true")
    ok, _ = daemon._should_send_telegram(responded=2, dispatched=17, crits=0, flags_count=1)
    assert ok


def test_disable_kill_switch(monkeypatch):
    """ATLAS_NOTIFY_DISABLE=true beats everything."""
    daemon = _load_daemon()
    monkeypatch.setenv("ATLAS_NOTIFY_DISABLE", "true")
    ok, reason = daemon._should_send_telegram(responded=17, dispatched=17, crits=5, flags_count=3)
    assert not ok
    assert "ATLAS_NOTIFY_DISABLE" in reason


def test_custom_threshold(monkeypatch):
    """Operator can lower threshold (e.g. 0.1) to allow weak responses through."""
    daemon = _load_daemon()
    monkeypatch.delenv("ATLAS_NOTIFY_DISABLE", raising=False)
    monkeypatch.setenv("ATLAS_NOTIFY_MIN_RESPONDED_RATIO", "0.1")
    monkeypatch.setenv("ATLAS_NOTIFY_FORCE_ON_CRITICAL", "false")
    monkeypatch.setenv("ATLAS_NOTIFY_FORCE_ON_WHISTLEBLOWER", "false")
    # 2/17 = 0.117 > 0.1 -> send
    ok, _ = daemon._should_send_telegram(responded=2, dispatched=17, crits=0, flags_count=0)
    assert ok
    # 1/17 = 0.058 < 0.1 -> suppress
    ok2, _ = daemon._should_send_telegram(responded=1, dispatched=17, crits=0, flags_count=0)
    assert not ok2


def test_invalid_threshold_falls_back_to_default(monkeypatch):
    """Bad env var value should not crash; fallback to 0.4."""
    daemon = _load_daemon()
    monkeypatch.delenv("ATLAS_NOTIFY_DISABLE", raising=False)
    monkeypatch.setenv("ATLAS_NOTIFY_MIN_RESPONDED_RATIO", "not_a_number")
    monkeypatch.setenv("ATLAS_NOTIFY_FORCE_ON_CRITICAL", "false")
    monkeypatch.setenv("ATLAS_NOTIFY_FORCE_ON_WHISTLEBLOWER", "false")
    ok, _ = daemon._should_send_telegram(responded=2, dispatched=17, crits=0, flags_count=0)
    assert not ok  # 2/17=0.117 < 0.4 default


def test_threshold_clamped_to_unit_interval(monkeypatch):
    """Operator passing 5.0 should clamp to 1.0; -1 should clamp to 0."""
    daemon = _load_daemon()
    monkeypatch.delenv("ATLAS_NOTIFY_DISABLE", raising=False)
    monkeypatch.setenv("ATLAS_NOTIFY_FORCE_ON_CRITICAL", "false")
    monkeypatch.setenv("ATLAS_NOTIFY_FORCE_ON_WHISTLEBLOWER", "false")
    # threshold 5.0 -> clamp 1.0; even 17/17=1.0 should pass (not strictly less than 1.0)
    monkeypatch.setenv("ATLAS_NOTIFY_MIN_RESPONDED_RATIO", "5.0")
    ok_full, _ = daemon._should_send_telegram(responded=17, dispatched=17, crits=0, flags_count=0)
    assert ok_full  # 1.0 ratio not < 1.0 threshold
    # 16/17 < 1.0 -> suppress
    ok_one_short, _ = daemon._should_send_telegram(responded=16, dispatched=17, crits=0, flags_count=0)
    assert not ok_one_short

    # threshold -1 -> clamp 0.0; everything passes
    monkeypatch.setenv("ATLAS_NOTIFY_MIN_RESPONDED_RATIO", "-1")
    ok_zero, _ = daemon._should_send_telegram(responded=0, dispatched=17, crits=0, flags_count=0)
    # 0/17 = 0 not < 0 -> ok
    assert ok_zero


def test_zero_dispatched_suppresses(monkeypatch):
    """Defensive: a task with 0 perspectives dispatched is meaningless to notify about."""
    daemon = _load_daemon()
    monkeypatch.delenv("ATLAS_NOTIFY_DISABLE", raising=False)
    monkeypatch.setenv("ATLAS_NOTIFY_FORCE_ON_CRITICAL", "false")
    monkeypatch.setenv("ATLAS_NOTIFY_FORCE_ON_WHISTLEBLOWER", "false")
    ok, reason = daemon._should_send_telegram(responded=0, dispatched=0, crits=0, flags_count=0)
    assert not ok
    assert "no perspectives dispatched" in reason


def test_force_critical_off_allows_suppress(monkeypatch):
    """Operator can disable critical override (e.g. during noise debugging)."""
    daemon = _load_daemon()
    monkeypatch.delenv("ATLAS_NOTIFY_DISABLE", raising=False)
    monkeypatch.setenv("ATLAS_NOTIFY_FORCE_ON_CRITICAL", "false")
    monkeypatch.setenv("ATLAS_NOTIFY_FORCE_ON_WHISTLEBLOWER", "false")
    monkeypatch.setenv("ATLAS_NOTIFY_MIN_RESPONDED_RATIO", "0.4")
    ok, _ = daemon._should_send_telegram(responded=2, dispatched=17, crits=10, flags_count=10)
    assert not ok  # critical and whistleblower both ignored, ratio dominates
