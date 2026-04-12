#!/usr/bin/env python3
"""Heartbeat Gate — KAIROS binary decision: should the swarm run?

Prevents swarm from running on unchanged codebases, wasting tokens on
proposals that repeat already-shipped work.

Decision logic (3 checks, first match wins):
  1. URGENT   — HIGH/CRITICAL unacted proposals exist → always run
  2. ACTIVE   — Recent git activity (SESSION-DIFFS.jsonl < 8h) → run
  3. STALE    — No recent activity, no urgent items → skip

Usage:
    python -m packages.swarm.heartbeat_gate
    # Exits 0 if swarm should run, exits 1 if skip.

In GitHub Actions:
    python -m packages.swarm.heartbeat_gate || exit 0
    # If gate returns 1, Actions step "succeeds" but skips downstream steps.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────

project_root = Path(__file__).parent.parent.parent
PROPOSALS_FILE = project_root / "memory" / "swarm" / "proposals.json"
SESSION_DIFFS_FILE = project_root / "memory" / "swarm" / "SESSION-DIFFS.jsonl"
HEARTBEAT_LOG = project_root / "memory" / "swarm" / "heartbeat-log.jsonl"

# Configurable thresholds
RECENT_ACTIVITY_HOURS = 8    # SESSION-DIFFS entry younger than this = "active"
STALE_FLOOR_HOURS = 24       # Even if no activity, run at least every N hours


# ── Gate Logic ─────────────────────────────────────────────────────────────────

def _check_urgent_proposals() -> tuple[bool, str]:
    """Check 1: Any HIGH/CRITICAL unacted proposals in inbox?"""
    if not PROPOSALS_FILE.exists():
        return False, "no proposals file"

    try:
        with open(PROPOSALS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        proposals = data if isinstance(data, list) else data.get("proposals", [])
    except (json.JSONDecodeError, OSError):
        return False, "proposals file unreadable"

    urgent = [
        p for p in proposals
        if p.get("severity") in ("critical", "high")
        and p.get("status", "pending") == "pending"
    ]
    if urgent:
        titles = [p.get("title", "?")[:60] for p in urgent[:3]]
        return True, f"urgent_pending_proposals: {len(urgent)} HIGH/CRITICAL unacted — {'; '.join(titles)}"
    return False, "no urgent proposals"


def _check_recent_activity() -> tuple[bool, str]:
    """Check 2: Any git activity in the last RECENT_ACTIVITY_HOURS?"""
    if not SESSION_DIFFS_FILE.exists():
        return False, "no SESSION-DIFFS.jsonl"

    try:
        with open(SESSION_DIFFS_FILE, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
    except OSError:
        return False, "SESSION-DIFFS.jsonl unreadable"

    if not lines:
        return False, "SESSION-DIFFS.jsonl empty"

    try:
        last_entry = json.loads(lines[-1])
        ts_str = last_entry.get("timestamp", "")
        if not ts_str:
            return False, "last entry has no timestamp"
        # Handle both Z suffix and +00:00
        ts_str = ts_str.replace("Z", "+00:00")
        last_ts = datetime.fromisoformat(ts_str)
        age = datetime.now(timezone.utc) - last_ts
        hours_ago = age.total_seconds() / 3600

        if age < timedelta(hours=RECENT_ACTIVITY_HOURS):
            files_changed = last_entry.get("files_changed_count", "?")
            headline = last_entry.get("sprint_headline", "recent commit")
            return True, f"recent_git_activity: {hours_ago:.1f}h ago ({files_changed} files) — {headline}"
        else:
            return False, f"last activity was {hours_ago:.1f}h ago (threshold: {RECENT_ACTIVITY_HOURS}h)"
    except (json.JSONDecodeError, ValueError) as e:
        return False, f"could not parse last SESSION-DIFFS entry: {e}"


def _check_stale_floor() -> tuple[bool, str]:
    """Check 3: Has it been more than STALE_FLOOR_HOURS since last swarm run?"""
    if not HEARTBEAT_LOG.exists():
        return True, f"stale_floor: no heartbeat log — first run"

    try:
        with open(HEARTBEAT_LOG, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
    except OSError:
        return True, "stale_floor: heartbeat log unreadable — run anyway"

    if not lines:
        return True, "stale_floor: heartbeat log empty — first run"

    # Find last "RUN" decision
    last_run = None
    for raw_line in reversed(lines):
        try:
            entry = json.loads(raw_line)
            if entry.get("decision") == "RUN":
                ts_str = entry.get("timestamp", "").replace("Z", "+00:00")
                last_run = datetime.fromisoformat(ts_str)
                break
        except (json.JSONDecodeError, ValueError):
            continue

    if last_run is None:
        return True, "stale_floor: no previous RUN found — run now"

    age = datetime.now(timezone.utc) - last_run
    hours_ago = age.total_seconds() / 3600

    if age >= timedelta(hours=STALE_FLOOR_HOURS):
        return True, f"stale_floor: last run was {hours_ago:.1f}h ago (floor: {STALE_FLOOR_HOURS}h)"
    return False, f"stale_floor not reached: last run {hours_ago:.1f}h ago"


def _log_decision(decision: str, reason: str) -> None:
    """Append gate decision to heartbeat log."""
    HEARTBEAT_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "reason": reason,
    }
    with open(HEARTBEAT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def should_run_swarm(
    hours_threshold: int = RECENT_ACTIVITY_HOURS,
    log: bool = True,
) -> tuple[bool, str]:
    """Gate function. Returns (should_run, reason).

    Checks 3 conditions in priority order:
      1. Urgent pending HIGH/CRITICAL proposals → always run
      2. Recent git activity (< hours_threshold) → run
      3. Stale floor exceeded (> STALE_FLOOR_HOURS since last run) → run
      else → skip

    Args:
        hours_threshold: Override RECENT_ACTIVITY_HOURS (default: 8)
        log: Whether to write decision to heartbeat-log.jsonl

    Returns:
        (True, "reason why run") or (False, "reason why skip")
    """
    # Check 1: Urgent proposals
    urgent, urgent_reason = _check_urgent_proposals()
    if urgent:
        if log:
            _log_decision("RUN", urgent_reason)
        return True, urgent_reason

    # Check 2: Recent activity
    active, active_reason = _check_recent_activity()
    if active:
        if log:
            _log_decision("RUN", active_reason)
        return True, active_reason

    # Check 3: Stale floor
    stale, stale_reason = _check_stale_floor()
    if stale:
        if log:
            _log_decision("RUN", stale_reason)
        return True, stale_reason

    # All checks failed — skip
    skip_reason = f"SKIP: no urgent proposals, no recent activity, stale floor not reached. Detail: {active_reason} | {stale_reason}"
    if log:
        _log_decision("SKIP", skip_reason)
    return False, skip_reason


# ── CLI entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    should_run, reason = should_run_swarm()
    print(f"[heartbeat_gate] {'RUN' if should_run else 'SKIP'}: {reason}")

    if should_run:
        sys.exit(0)   # 0 = proceed
    else:
        sys.exit(1)   # 1 = skip (GitHub Actions: step fails but can be handled with || true)
