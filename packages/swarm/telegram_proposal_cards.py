"""Telegram Proposal Cards — cron-safe script.

Reads memory/swarm/proposals.json, finds escalated+judged proposals that have
NOT yet been pinged to CEO, and posts one Telegram message per proposal with
an inline keyboard: [Accept] [Reject] [Defer] [Details].

Tracking file: memory/swarm/proposals-sent.json — atomic write (mkstemp + replace)
so two concurrent cron runs never double-ping.

Eligibility filter:
    escalate_to_ceo == True
    AND judge_score is not None
    AND judge_score >= 7
    AND status == "pending"
    AND id NOT in proposals-sent.json

Env:
    TELEGRAM_BOT_TOKEN — required
    TELEGRAM_CEO_CHAT_ID — required
    PROPOSAL_MIN_JUDGE_SCORE — optional (default 7)

Exit codes:
    0 — success (even when zero cards sent)
    2 — missing config
    3 — proposals.json unreadable
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

import hashlib

import httpx
from loguru import logger

REPO_ROOT = Path(__file__).parent.parent.parent
PROPOSALS_PATH = REPO_ROOT / "memory" / "swarm" / "proposals.json"
SENT_PATH = REPO_ROOT / "memory" / "swarm" / "proposals-sent.json"

DEFAULT_MIN_JUDGE_SCORE = 7


def _atomic_write_json(path: Path, data: dict) -> None:
    """Write JSON atomically via mkstemp + os.replace (cross-platform)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), suffix=".json")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, str(path))
    except Exception:
        if os.path.exists(tmp_path):
            with __import__("contextlib").suppress(Exception):
                os.remove(tmp_path)
        raise


def _load_sent() -> dict:
    if not SENT_PATH.exists():
        return {"schema_version": "1.0", "sent": {}}
    try:
        with open(SENT_PATH, encoding="utf-8") as f:
            data = json.load(f)
        if "sent" not in data:
            data["sent"] = {}
        return data
    except Exception as e:
        logger.warning("Could not read proposals-sent.json: {e}", e=str(e))
        return {"schema_version": "1.0", "sent": {}}


def _load_proposals() -> dict:
    with open(PROPOSALS_PATH, encoding="utf-8") as f:
        return json.load(f)


def _eligible(p: dict, min_score: int) -> bool:
    if p.get("status") != "pending":
        return False
    if not p.get("escalate_to_ceo"):
        return False
    score = p.get("judge_score")
    if score is None:
        return False
    try:
        return float(score) >= float(min_score)
    except (TypeError, ValueError):
        return False


def compute_payload_sha12(payload: dict) -> str:
    """Canonical sha256(payload) → first 12 hex chars.

    Shared helper so the card formatter AND the callback handler compute the
    same fingerprint over the same JSON representation (Pattern 2 — defeats
    Lies-in-the-Loop payload swapping between display and execution).
    """
    canon = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()[:12]


def _extract_action_payload(p: dict) -> dict:
    """Pull the JSON payload that WILL run on Accept.

    Preference order:
      1. explicit `p["action_payload"]` (set by agent authors)
      2. `p["tool_args"]` (Pattern-3 atlas_tool invocations)
      3. fallback: {title, content} — at minimum CEO sees what gets recorded.
    """
    if isinstance(p.get("action_payload"), dict):
        return p["action_payload"]
    if isinstance(p.get("tool_args"), dict):
        return {"tool": p.get("tool_name", "?"), "args": p["tool_args"]}
    return {
        "title": p.get("title", ""),
        "content": (p.get("content") or "")[:1000],
    }


def _format_card(p: dict) -> tuple[str, str]:
    """Format a proposal into a Telegram Markdown card.

    Returns (card_text, sha12). The sha12 MUST match what the callback handler
    recomputes when CEO taps Accept — mismatch aborts the action.
    """
    sev_emoji = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢",
    }.get(str(p.get("severity", "")).lower(), "⚪")
    pid = p.get("id", "?")
    title = p.get("title", "(no title)")[:200]
    agent = p.get("agent", "?")
    severity = p.get("severity", "?")
    score = p.get("judge_score", "?")
    reasoning = (p.get("judge_reasoning") or "")[:400]
    content = (p.get("content") or "")[:400]

    # Pattern 2 — exact payload rendered inline + sha12 footer.
    payload = _extract_action_payload(p)
    sha12 = compute_payload_sha12(payload)
    payload_json = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
    if len(payload_json) > 1500:
        payload_json = payload_json[:1500] + "\n  …(truncated — tap Details for full)"

    lines = [
        f"{sev_emoji} *Swarm proposal* `{pid}`",
        f"*{title}*",
        "",
        f"Agent: _{agent}_ · Severity: *{severity}* · Judge: *{score}/10*",
    ]
    if reasoning:
        lines.append("")
        lines.append(f"Judge says: {reasoning}")
    if content:
        lines.append("")
        lines.append(content)
    lines.extend(
        [
            "",
            "*Will run on Accept:*",
            "```json",
            payload_json,
            "```",
            f"`payload_sha: {sha12}`",
        ]
    )
    return "\n".join(lines), sha12


def _build_keyboard(pid: str, sha12: str) -> dict:
    """Inline keyboard with sha12 bound to each callback.

    Format: `propose:{id}:{action}:{sha12}` — handler recomputes the sha from
    the stored payload and rejects the action if they don't match.
    """
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Accept", "callback_data": f"propose:{pid}:accept:{sha12}"},
                {"text": "❌ Reject", "callback_data": f"propose:{pid}:reject:{sha12}"},
            ],
            [
                {"text": "⏸ Defer", "callback_data": f"propose:{pid}:defer:{sha12}"},
                {"text": "📖 Details", "callback_data": f"propose:{pid}:details:{sha12}"},
            ],
        ]
    }


def _send_card(token: str, chat_id: str, text: str, keyboard: dict) -> dict | None:
    """Send one Telegram message. Returns the API response dict or None on failure."""
    # Central telegram-gate (2026-04-19 spam kill).
    try:
        from .telegram_gate import allow_send as _gate_allow
        if not _gate_allow(category="proposal", severity="info", preview=text[:120]):
            logger.info("telegram_gate blocked proposal card send")
            return {"ok": False, "gate_blocked": True}
    except ImportError:
        pass

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload: dict = {
        "chat_id": chat_id,
        "text": text[:4000],
        "parse_mode": "Markdown",
        "reply_markup": keyboard,
    }
    try:
        resp = httpx.post(url, json=payload, timeout=15)
        data = resp.json()
        if not data.get("ok"):
            # Retry without Markdown if parse failed
            payload.pop("parse_mode", None)
            resp = httpx.post(url, json=payload, timeout=15)
            data = resp.json()
        return data
    except Exception as e:
        logger.error("Telegram send failed for card: {e}", e=str(e))
        return None


def main() -> int:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CEO_CHAT_ID", "").strip()
    min_score = int(os.environ.get("PROPOSAL_MIN_JUDGE_SCORE", DEFAULT_MIN_JUDGE_SCORE))

    if not token or not chat_id:
        logger.error("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CEO_CHAT_ID")
        return 2

    if not PROPOSALS_PATH.exists():
        logger.info("No proposals.json yet at {p}", p=str(PROPOSALS_PATH))
        return 0

    try:
        proposals_data = _load_proposals()
    except Exception as e:
        logger.error("Cannot read proposals.json: {e}", e=str(e))
        return 3

    sent_data = _load_sent()
    sent_ids: dict = sent_data.get("sent", {})

    eligible = [p for p in proposals_data.get("proposals", []) if _eligible(p, min_score)]
    to_send = [p for p in eligible if p.get("id") not in sent_ids]

    logger.info(
        "Proposals: total={t} eligible={e} to_send={s}",
        t=len(proposals_data.get("proposals", [])),
        e=len(eligible),
        s=len(to_send),
    )

    for p in to_send:
        pid = p.get("id")
        if not pid:
            continue
        card, sha12 = _format_card(p)
        kb = _build_keyboard(pid, sha12)
        resp = _send_card(token, chat_id, card, kb)
        if resp and resp.get("ok"):
            message_id = resp.get("result", {}).get("message_id")
            sent_ids[pid] = {
                "message_id": message_id,
                "chat_id": chat_id,
                "sent_at": datetime.now(UTC).isoformat(),
                "judge_score": p.get("judge_score"),
                "severity": p.get("severity"),
                "payload_sha12": sha12,  # Pattern 2 — tamper evidence
            }
            logger.info("Sent card for {pid} (msg_id={mid})", pid=pid, mid=message_id)
            # Tiny gap between sends to avoid Telegram flood limits.
            time.sleep(0.3)
        else:
            logger.warning("Failed to send card for {pid}", pid=pid)

    sent_data["sent"] = sent_ids
    sent_data["schema_version"] = sent_data.get("schema_version", "1.0")
    sent_data["last_run_at"] = datetime.now(UTC).isoformat()
    try:
        _atomic_write_json(SENT_PATH, sent_data)
    except Exception as e:
        logger.error("Could not write proposals-sent.json: {e}", e=str(e))
        return 3

    return 0


if __name__ == "__main__":
    sys.exit(main())
