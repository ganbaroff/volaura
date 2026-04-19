"""Central telegram-gate — single choke point for every Telegram send.

Why this exists
---------------
CEO report 2026-04-19: 'агенты спамят мне в Telegram'. Root cause: 5 direct
`urllib`/`httpx.post(api.telegram.org)` call sites bypass `notifier.py`
entirely:
    - apps/api/app/middleware/error_alerting.py   (5xx middleware)
    - apps/api/app/routers/webhooks_sentry.py     (Sentry regression alerts)
    - apps/api/app/services/match_checker.py      (org-match notifier)
    - apps/api/app/core/assessment/bars.py        (assessment timing bars)
    - packages/swarm/telegram_proposal_cards.py   (hourly cron)

Every emitter enforces its own cooldown. None enforces the union. Result:
5 independent timers × N messages = spam.

This module is the UNION. Every send must pass through `allow_send()`
before hitting the Telegram API. The gate:

  1. Checks the kill-switch file `memory/atlas/telegram-silenced-until.txt`.
     If present and its ISO-8601 timestamp is in the future, ALL non-critical
     sends are blocked. File written by `silence(hours=N)` helper.

  2. Enforces a GLOBAL hourly rate limit (default: 10 messages per rolling
     60-minute window across every category + severity). Hard cap, logs to
     `memory/atlas/telegram-gate-log.jsonl`.

  3. Deduplicates by message-preview hash inside a 1-hour window. Same
     preview fired twice → second silently dropped.

Severity == 'critical' bypasses #2 and #3 but NOT #1 — CEO retains the
authority to silence everything including criticals when he is asleep or
in a meeting. 83(b)-tier deadlines should be `emergency=True` which
bypasses #1 as well.

Usage
-----
    from packages.swarm.telegram_gate import allow_send, silence

    # Before sending, check gate:
    if not allow_send(category='error', severity='warning', preview=text[:120]):
        return False  # blocked — do not call Telegram API

    # To silence for 24h (CEO command):
    silence(hours=24, reason='CEO asked agents to stop spamming')

This module is stdlib-only. Safe to import from both FastAPI and cron contexts.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal

REPO_ROOT = Path(__file__).resolve().parents[2]
SILENCE_FILE = REPO_ROOT / "memory" / "atlas" / "telegram-silenced-until.txt"
GATE_LOG = REPO_ROOT / "memory" / "atlas" / "telegram-gate-log.jsonl"

Severity = Literal["info", "warning", "error", "critical"]

_HOURLY_LIMIT = int(os.environ.get("TELEGRAM_GATE_HOURLY_LIMIT", "10"))
_DEDUP_WINDOW_MIN = 60


def _now() -> datetime:
    return datetime.now(UTC)


def _hash(preview: str) -> str:
    return hashlib.sha256(preview.encode("utf-8", errors="replace")).hexdigest()[:16]


def _read_log_tail(lines: int = 200) -> list[dict]:
    if not GATE_LOG.exists():
        return []
    try:
        with GATE_LOG.open("r", encoding="utf-8") as f:
            tail = f.readlines()[-lines:]
    except OSError:
        return []
    out: list[dict] = []
    for line in tail:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _append_log(record: dict) -> None:
    GATE_LOG.parent.mkdir(parents=True, exist_ok=True)
    try:
        with GATE_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass


def is_silenced() -> tuple[bool, str | None]:
    """Returns (silenced, reason). Silence expires when file timestamp passes."""
    if not SILENCE_FILE.exists():
        return False, None
    try:
        raw = SILENCE_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return False, None
    # First line is ISO-8601 timestamp, optional second line is reason.
    parts = raw.split("\n", 1)
    if not parts or not parts[0]:
        return False, None
    try:
        until = datetime.fromisoformat(parts[0].replace("Z", "+00:00"))
    except ValueError:
        return False, None
    if until <= _now():
        return False, None
    reason = parts[1] if len(parts) > 1 else "silenced"
    return True, reason


def silence(hours: int, reason: str = "CEO command") -> None:
    """Write silence-until file. Blocks non-emergency sends until expiry."""
    until = _now() + timedelta(hours=hours)
    SILENCE_FILE.parent.mkdir(parents=True, exist_ok=True)
    SILENCE_FILE.write_text(f"{until.isoformat()}\n{reason}\n", encoding="utf-8")


def lift_silence() -> None:
    """Remove silence-until file immediately."""
    if SILENCE_FILE.exists():
        SILENCE_FILE.unlink()


def allow_send(
    *,
    category: str,
    severity: Severity,
    preview: str,
    emergency: bool = False,
) -> bool:
    """Gate decision. True = caller may send. False = drop silently.

    Args:
        category: logical channel (e.g. 'error', 'digest', 'proposal')
        severity: 'info' | 'warning' | 'error' | 'critical'
        preview: first ~120 chars of the intended message (used for dedup)
        emergency: True bypasses silence-file (e.g. 83(b)-tier deadline)

    Always logs the decision to `telegram-gate-log.jsonl` for audit.
    """
    now = _now()
    is_critical = severity == "critical"
    silenced, silence_reason = is_silenced()
    tail = _read_log_tail(500)

    reason: str | None = None

    if silenced and not emergency:
        reason = f"silenced:{silence_reason}"
    else:
        one_hour_ago = now - timedelta(minutes=60)
        dedup_window = now - timedelta(minutes=_DEDUP_WINDOW_MIN)
        preview_hash = _hash(preview)

        recent_sent = 0
        seen_same_hash = False
        for entry in reversed(tail):
            ts_str = entry.get("timestamp")
            if not ts_str:
                continue
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except ValueError:
                continue
            if ts < one_hour_ago:
                break
            if entry.get("decision") != "allow":
                continue
            recent_sent += 1
            if ts >= dedup_window and entry.get("preview_hash") == preview_hash:
                seen_same_hash = True

        if not is_critical and seen_same_hash:
            reason = "dedup"
        elif not is_critical and recent_sent >= _HOURLY_LIMIT:
            reason = f"hourly_limit:{recent_sent}/{_HOURLY_LIMIT}"

    decision = "allow" if reason is None else "block"
    _append_log({
        "timestamp": now.isoformat(),
        "category": category,
        "severity": severity,
        "decision": decision,
        "reason": reason,
        "preview": preview[:120],
        "preview_hash": _hash(preview),
        "emergency": emergency,
    })
    return decision == "allow"


__all__ = ["allow_send", "silence", "lift_silence", "is_silenced"]
