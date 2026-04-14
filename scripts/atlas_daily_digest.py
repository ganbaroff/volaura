"""Atlas daily digest — runs 23:00 UTC via GitHub Actions.

Design per E6 (E-LAWs + Vacation runtime, SYNC §3):
  - 3 bullets max: happened / pending / needs-decision
  - Calm tone, no urgency language unless P0 actually fires
  - Respects vacation.json: if enabled → writes digest to file, skips Telegram
  - Cooldown log: writes entry, lets notifier.py enforce 6h gate (E6 task 2)

Scope: read-only on the repo. Only writes digest-log.json and possibly a file digest.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
JOURNAL = REPO_ROOT / "memory" / "atlas" / "journal.md"
INBOX_DIR = REPO_ROOT / "memory" / "atlas" / "inbox"
PROPOSALS = REPO_ROOT / "memory" / "swarm" / "proposals.json"
VACATION = REPO_ROOT / "memory" / "atlas" / "vacation-mode.json"
DIGEST_LOG = REPO_ROOT / "memory" / "atlas" / "digest-log.jsonl"
DIGEST_OFFLINE = REPO_ROOT / "memory" / "atlas" / "digest-offline.md"

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def _vacation_active() -> tuple[bool, str | None]:
    """Return (active, until_iso). Active only if file exists, enabled=true,
    and until is in the future. Any parse error → treat as inactive."""
    if not VACATION.exists():
        return False, None
    try:
        data = json.loads(VACATION.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False, None
    if not data.get("enabled"):
        return False, None
    until = data.get("until")
    if not until:
        return True, None  # indefinite
    try:
        until_dt = datetime.fromisoformat(until.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return True, None
    return until_dt > datetime.now(UTC), until


def _journal_last_24h() -> str:
    """Extract the last journal entry that falls within the last 24h.
    Returns the entry's opening sentence or empty string."""
    if not JOURNAL.exists():
        return ""
    text = JOURNAL.read_text(encoding="utf-8")
    # Entries are separated by "---\n\n## YYYY-MM-DD"
    entries = re.split(r"^---\s*$", text, flags=re.MULTILINE)
    if len(entries) < 2:
        return ""
    last = entries[-1].strip()
    # First line after "## ..." is the title; grab the next non-empty paragraph's first sentence.
    lines = [ln.strip() for ln in last.splitlines() if ln.strip()]
    if len(lines) < 2:
        return ""
    # Skip the "## date - title" line; find first prose paragraph.
    for ln in lines[1:]:
        if ln.startswith("#") or ln.startswith("MEMORY-GATE"):
            continue
        # Return first sentence (up to ~120 chars)
        first_sentence = re.split(r"(?<=[.!?])\s+", ln, maxsplit=1)[0]
        return first_sentence[:150]
    return ""


def _pending_inbox_count() -> int:
    if not INBOX_DIR.exists():
        return 0
    count = 0
    for md in INBOX_DIR.glob("*.md"):
        try:
            content = md.read_text(encoding="utf-8")
        except OSError:
            continue
        if "Consumed by main Atlas: pending" in content:
            count += 1
    return count


def _open_proposals() -> tuple[int, int]:
    """Return (open_total, escalated_to_ceo)."""
    if not PROPOSALS.exists():
        return 0, 0
    try:
        data = json.loads(PROPOSALS.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return 0, 0
    props = data.get("proposals") or []
    open_status = {"open", "proposed", "pending", "new"}
    opens = [p for p in props if p.get("status") in open_status]
    escalated = [p for p in opens if p.get("escalate_to_ceo") is True]
    return len(opens), len(escalated)


def _slo_24h() -> tuple[int, int, float | None]:
    """Compute SLO over last 24h from digest-log.jsonl.

    Returns (successes, total, rate_pct). rate_pct is None if no data.
    Used by E6 task 4 — gives each digest a running reliability number.
    """
    if not DIGEST_LOG.exists():
        return 0, 0, None
    cutoff = datetime.now(UTC) - timedelta(hours=24)
    successes = 0
    total = 0
    try:
        with DIGEST_LOG.open("r", encoding="utf-8") as f:
            for line in f:
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
                    continue
                total += 1
                if entry.get("delivered_telegram") or entry.get("vacation_mode"):
                    successes += 1
    except OSError:
        return 0, 0, None
    if total == 0:
        return 0, 0, None
    return successes, total, (successes / total) * 100


def _build_digest() -> tuple[str, dict]:
    """Return (telegram-ready text, structured dict for log)."""
    journal_line = _journal_last_24h()
    inbox_pending = _pending_inbox_count()
    open_total, escalated = _open_proposals()
    slo_succ, slo_tot, slo_rate = _slo_24h()

    happened = journal_line or "(quiet — no new journal entry)"
    pending = (
        f"{inbox_pending} inbox, {open_total} proposals"
        if (inbox_pending or open_total)
        else "(clear)"
    )
    decide = (
        f"{escalated} escalated to CEO" if escalated else "(none)"
    )
    slo_line = (
        f"{slo_rate:.1f}% ({slo_succ}/{slo_tot}, target 99.0)"
        if slo_rate is not None
        else "(no data yet)"
    )

    ts = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    text = (
        f"Atlas digest — {ts}\n\n"
        f"• Happened: {happened}\n"
        f"• Pending:  {pending}\n"
        f"• Decide:   {decide}\n"
        f"• SLO 24h:  {slo_line}"
    )
    record = {
        "timestamp": datetime.now(UTC).isoformat(),
        "happened": happened,
        "pending_inbox": inbox_pending,
        "open_proposals": open_total,
        "escalated": escalated,
        "slo_24h_successes": slo_succ,
        "slo_24h_total": slo_tot,
        "slo_24h_rate_pct": slo_rate,
    }
    return text, record


def _send_telegram(text: str) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CEO_CHAT_ID")
    if not token or not chat_id:
        return False
    url = TELEGRAM_API.format(token=token)
    data = urllib.parse.urlencode(
        {"chat_id": chat_id, "text": text, "disable_web_page_preview": "true"}
    ).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except (urllib.error.URLError, TimeoutError):
        return False


def _append_log(record: dict, delivered: bool) -> None:
    record["delivered_telegram"] = delivered
    DIGEST_LOG.parent.mkdir(parents=True, exist_ok=True)
    with DIGEST_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _write_offline_digest(text: str) -> None:
    """When on vacation, persist digest to file so CEO can catch up later."""
    DIGEST_OFFLINE.parent.mkdir(parents=True, exist_ok=True)
    with DIGEST_OFFLINE.open("a", encoding="utf-8") as f:
        f.write("\n" + text + "\n---\n")


def _safe_print(text: str) -> None:
    """Print that degrades gracefully on narrow-encoding consoles (Windows cp1252)."""
    try:
        sys.stdout.write(text + "\n")
        sys.stdout.flush()
    except UnicodeEncodeError:
        sys.stdout.buffer.write(text.encode("utf-8", errors="replace") + b"\n")
        sys.stdout.flush()


def main() -> int:
    text, record = _build_digest()

    active, _until = _vacation_active()
    if active:
        _write_offline_digest(text)
        record["vacation_mode"] = True
        _append_log(record, delivered=False)
        _safe_print("Vacation mode active — wrote to file, skipped Telegram.")
        return 0

    delivered = _send_telegram(text)
    _append_log(record, delivered=delivered)
    _safe_print(text)
    _safe_print(f"\n(telegram delivered: {delivered})")
    return 0 if delivered else 1


if __name__ == "__main__":
    sys.exit(main())
