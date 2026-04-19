"""Atlas notifier — single entry point for all Telegram pings from the swarm.

Closes E6 tasks 2 (6h cooldown per category) and 3 (vacation-mode gate).

Design:
  - One function: send_notification(category, text, severity='info') → bool
  - Three gates, in order, any returning False suppresses the send:
      1. Vacation mode active AND severity < CRITICAL → suppress (E-LAW 3)
      2. Same (category, severity < CRITICAL) fired within 6h → suppress cooldown
      3. No TELEGRAM_BOT_TOKEN → can't send, log only
  - Every call (suppressed or not) appends to notification-log.jsonl for audit.

Import from anywhere in swarm to avoid scattered "let's just curl Telegram" code.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal

REPO_ROOT = Path(__file__).resolve().parents[2]
VACATION_FILE = REPO_ROOT / "memory" / "atlas" / "vacation-mode.json"
NOTIFICATION_LOG = REPO_ROOT / "memory" / "atlas" / "notification-log.jsonl"

Category = Literal["escalation", "digest", "error", "proposal", "incident", "info"]
Severity = Literal["info", "warning", "error", "critical"]

# Categories allowed through vacation-mode / cooldown only if severity is critical.
_COOLDOWN_HOURS = 6
_SEVERITY_ORDER = {"info": 0, "warning": 1, "error": 2, "critical": 3}


def _vacation_active() -> bool:
    if not VACATION_FILE.exists():
        return False
    try:
        data = json.loads(VACATION_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    if not data.get("enabled"):
        return False
    until = data.get("until")
    if not until:
        return True  # indefinite vacation
    try:
        until_dt = datetime.fromisoformat(until.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return True
    return until_dt > datetime.now(UTC)


def _cooldown_blocks(category: Category) -> bool:
    """True if the category fired a non-critical notification within last 6h."""
    if not NOTIFICATION_LOG.exists():
        return False
    cutoff = datetime.now(UTC) - timedelta(hours=_COOLDOWN_HOURS)
    try:
        with NOTIFICATION_LOG.open("r", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return False
    # Read last N lines only — cooldown is recent, no need to scan months back.
    for line in reversed(lines[-500:]):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts_str = entry.get("timestamp")
        if not ts_str:
            continue
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except ValueError:
            continue
        if ts < cutoff:
            return False  # past cutoff — no match
        if (
            entry.get("category") == category
            and entry.get("delivered") is True
            and entry.get("severity") != "critical"
        ):
            return True
    return False


def _log(record: dict) -> None:
    NOTIFICATION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with NOTIFICATION_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _telegram_send(text: str) -> bool:
    # HARD KILL-SWITCH (2026-04-19): see error_alerting.py. Remove early-return
    # only after CEO says 'unlock telegram alerts'.
    return False

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CEO_CHAT_ID")
    if not token or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode(
        {"chat_id": chat_id, "text": text, "disable_web_page_preview": "true"}
    ).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except (urllib.error.URLError, TimeoutError):
        return False


def send_notification(
    category: Category,
    text: str,
    severity: Severity = "info",
) -> bool:
    """Send a Telegram ping through gate stack. Returns True if delivered.

    Rules:
      - Vacation mode + non-critical → suppressed
      - Same category fired non-critical within 6h → suppressed
      - No token → cannot send, logs only
      - Critical severity bypasses both gates
    """
    now_iso = datetime.now(UTC).isoformat()
    reason = None
    delivered = False

    is_critical = _SEVERITY_ORDER.get(severity, 0) >= _SEVERITY_ORDER["critical"]

    # Central telegram-gate: global rate-limit + dedup + kill-switch (2026-04-19).
    from .telegram_gate import allow_send as _gate_allow

    if _vacation_active() and not is_critical:
        reason = "vacation_mode"
    elif _cooldown_blocks(category) and not is_critical:
        reason = "cooldown"
    elif not _gate_allow(category=category, severity=severity, preview=text[:120]):
        reason = "telegram_gate_blocked"
    else:
        delivered = _telegram_send(text)
        if not delivered:
            reason = "telegram_send_failed_or_no_token"

    _log(
        {
            "timestamp": now_iso,
            "category": category,
            "severity": severity,
            "delivered": delivered,
            "suppression_reason": reason,
            "preview": text[:120],
        }
    )
    return delivered


__all__ = ["send_notification", "Category", "Severity"]
