"""inbox_consumer.py — T3.3 inbox consumer loop.

Scans memory/atlas/inbox/*.md for files tagged
  Consumed by main Atlas: pending
in their footer, classifies each ceo_to_bot message (code_fix / content /
analysis), logs a routing decision to memory/atlas/inbox/router-log-<date>.md,
and marks each file consumed by replacing the footer line.

Design constraints (swarm verdict 2026-04-20):
- model_router (T3.1) does NOT exist yet — classifier is keyword-based only.
- No LLM calls in this module.
- Does NOT re-fire dispatch — only LOGS routing decisions.
  Actual dispatch already happened (or will happen) via telegram-execute workflow.
- One bad file never blocks the rest; exceptions per-file.

Run:  python -m packages.swarm.inbox_consumer
"""

from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Repo root ─────────────────────────────────────────────────────────────────
# packages/swarm/inbox_consumer.py → parents[2] = repo root
_REPO_ROOT = Path(__file__).resolve().parents[2]
_INBOX_DIR = _REPO_ROOT / "memory" / "atlas" / "inbox"

# ── Sentinel text (must match what inbox-sync.yml writes) ─────────────────────
_PENDING_MARKER = "Consumed by main Atlas: pending"

# ── Intent classifier — ported from apps/api/app/routers/telegram_webhook.py ──

_ACTION_VERBS = (
    # Russian imperatives
    "сделай", "создай", "почини", "напиши", "проверь", "запусти",
    "собери", "найди", "добавь", "исправь", "удали", "перепиши",
    "разверни", "задеплой", "деплой", "сделать", "создать", "починить",
    # English
    "fix", "build", "create", "deploy", "write a", "add a", "add the",
    "remove", "run ", "implement", "ship",
)

_QUESTION_MARKERS = (
    "что думаешь", "как считаешь", "почему", "стоит ли", "что лучше",
    "what do you think", "should i", "what if", "a что если", "а что если",
)

_CONTENT_KEYWORDS = (
    "пост", "статья", "контент", "linkedin", "тикток", "telegram channel",
    "write a post", "write post", "caption", "marketing", "social",
)

_ANALYSIS_KEYWORDS = (
    "проанализируй", "analyze", "analyse", "compare", "объясни",
    "расскажи", "explain", "review", "оцени", "evaluate", "что происходит",
    "разберись", "посмотри", "check",
)


def classify_intent(text: str) -> tuple[str, str]:
    """Return (intent, reason) for a CEO message.

    intents: code_fix | content | analysis | chat
    Mirrors the keyword heuristics in telegram_webhook._classify_action_or_chat
    extended with content / analysis sub-intents.
    """
    t = (text or "").strip().lower()
    if not t:
        return "chat", "empty message"

    # Question → chat (not an action)
    if any(q in t for q in _QUESTION_MARKERS):
        return "chat", "question marker found"

    head = t[:300]

    # Content — social / marketing writing
    if any(kw in head for kw in _CONTENT_KEYWORDS):
        return "content", "content keyword in head"

    # Analysis / explanation requests
    if any(kw in head for kw in _ANALYSIS_KEYWORDS):
        return "analysis", "analysis keyword in head"

    # Code fix — explicit action verb
    if any(verb in head for verb in _ACTION_VERBS):
        return "code_fix", "action verb in head"

    return "chat", "no strong signal → default chat"


# ── File parser ───────────────────────────────────────────────────────────────

def parse_inbox_file(path: Path) -> dict | None:
    """Parse a pending inbox markdown file.

    Returns dict with keys: direction, message_type, created_at, body
    or None if parse fails.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"[inbox_consumer] READ ERROR {path.name}: {exc}", file=sys.stderr)
        return None

    # Direction: look for "Direction: ceo_to_bot" or "**Direction:** ceo_to_bot"
    direction_match = re.search(r"\*{0,2}Direction\*{0,2}:\s*(\S+)", raw, re.IGNORECASE)
    direction = direction_match.group(1).strip("*· ").lower() if direction_match else "unknown"

    # message_type
    type_match = re.search(r"\*{0,2}Type\*{0,2}:\s*(\S+)", raw, re.IGNORECASE)
    message_type = type_match.group(1).strip("*· ").lower() if type_match else "unknown"

    # created_at / captured
    ts_match = re.search(
        r"\*{0,2}Captured\*{0,2}:\s*([^\n]+)", raw, re.IGNORECASE
    ) or re.search(
        r"\*{0,2}Received\*{0,2}:\s*([^\n]+)", raw, re.IGNORECASE
    ) or re.search(
        r"\*{0,2}When\*{0,2}:\s*([^\n]+)", raw, re.IGNORECASE
    )
    created_at = ts_match.group(1).strip() if ts_match else "unknown"

    # Body: everything between ## Message and ## Metadata (or end of file)
    body_match = re.search(r"##\s*Message\s*\n+([\s\S]+?)(?:##|\Z)", raw)
    body = body_match.group(1).strip() if body_match else raw[:500]

    return {
        "direction": direction,
        "message_type": message_type,
        "created_at": created_at,
        "body": body,
        "raw": raw,
    }


# ── Router log ────────────────────────────────────────────────────────────────

def _router_log_path() -> Path:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return _INBOX_DIR / f"router-log-{today}.md"


def append_router_log(
    log_path: Path,
    file_path: Path,
    intent: str,
    reason: str,
    direction: str,
    created_at: str,
) -> None:
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entry = (
        f"\n---\n"
        f"**File:** `{file_path.name}`\n"
        f"**Consumed-at:** {ts}\n"
        f"**Direction:** {direction}\n"
        f"**Message-created:** {created_at}\n"
        f"**Intent:** {intent}\n"
        f"**Reason:** {reason}\n"
        f"**Would-dispatch-to:** "
        + {
            "code_fix":  "telegram-execute workflow (Aider code path)",
            "content":   "atlas_content_run.py (content engine)",
            "analysis":  "coordinator.py swarm analysis run",
            "chat":      "atlas_telegram._handle_atlas (conversational reply)",
        }.get(intent, "unknown")
        + "\n"
    )

    if not log_path.exists():
        header = (
            f"# Inbox Router Log — {log_path.stem.replace('router-log-', '')}\n\n"
            f"Auto-generated by inbox_consumer.py. "
            f"Dispatch is LOGGED, not re-fired (prevents duplicate workflow triggers).\n"
        )
        log_path.write_text(header + entry, encoding="utf-8")
    else:
        with log_path.open("a", encoding="utf-8") as f:
            f.write(entry)


# ── Footer updater ────────────────────────────────────────────────────────────

def mark_consumed(path: Path, intent: str) -> bool:
    """Replace the pending footer line with consumed stamp. Returns True on success."""
    try:
        raw = path.read_text(encoding="utf-8")
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        new_raw = raw.replace(
            _PENDING_MARKER,
            f"Consumed by inbox-consumer: {ts} · intent={intent}",
        )
        if new_raw == raw:
            # Marker not found (edge case: consumed between scan and write)
            return False
        path.write_text(new_raw, encoding="utf-8")
        return True
    except Exception as exc:
        print(f"[inbox_consumer] WRITE ERROR {path.name}: {exc}", file=sys.stderr)
        return False


# ── Main scan loop ────────────────────────────────────────────────────────────

def run() -> int:
    """Scan inbox, classify pending files, log + mark consumed.

    Returns count of files processed.
    """
    if not _INBOX_DIR.exists():
        print(f"[inbox_consumer] Inbox dir not found: {_INBOX_DIR}", file=sys.stderr)
        return 0

    pending_files = [
        p for p in sorted(_INBOX_DIR.glob("*.md"))
        if not p.name.startswith("router-log-")
        and _PENDING_MARKER in p.read_text(encoding="utf-8", errors="replace")
    ]

    total = len(pending_files)
    print(f"[inbox_consumer] Found {total} pending file(s)")

    if not total:
        return 0

    log_path = _router_log_path()
    processed = 0

    for fpath in pending_files:
        print(f"[inbox_consumer] Processing: {fpath.name}")
        parsed = parse_inbox_file(fpath)
        if parsed is None:
            # parse_inbox_file already printed the error
            continue

        direction = parsed["direction"]

        # Skip bot_to_ceo — those are our own outputs, nothing to consume
        if "bot_to_ceo" in direction:
            print(f"[inbox_consumer]   SKIP (bot_to_ceo) {fpath.name}")
            # Still mark as consumed so the scanner doesn't repeat this
            mark_consumed(fpath, "skip_bot_to_ceo")
            continue

        intent, reason = classify_intent(parsed["body"])

        try:
            append_router_log(
                log_path=log_path,
                file_path=fpath,
                intent=intent,
                reason=reason,
                direction=direction,
                created_at=parsed["created_at"],
            )
        except Exception as exc:
            print(
                f"[inbox_consumer] LOG ERROR {fpath.name}: {exc}", file=sys.stderr
            )
            # Continue — don't block the mark step over a logging failure

        success = mark_consumed(fpath, intent)
        if success:
            processed += 1
            print(f"[inbox_consumer]   intent={intent} | marked consumed")
        else:
            print(
                f"[inbox_consumer]   WARN: marker not found in {fpath.name}",
                file=sys.stderr,
            )

    print(f"[inbox_consumer] Done. Processed {processed}/{total}.")
    return processed


if __name__ == "__main__":
    count = run()
    sys.exit(0 if count >= 0 else 1)
