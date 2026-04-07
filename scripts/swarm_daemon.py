"""
swarm_daemon.py — Sprint S3 Step 3 — background autonomous coding daemon.

Polls memory/swarm/proposals.json on a schedule, picks approved proposals
that pass safety_gate at AUTO level, runs them through swarm_coder pipeline.

DESIGN:
- Stateless loop with persistent state file at memory/swarm/daemon_state.json
- Rate limit: max N commits per hour (default 5) to avoid runaway
- Skip already-processed proposals (tracked by id in state file)
- Skip proposals that have status != "approved"
- Skip proposals that fail pre-classification at AUTO
- Toggle via memory/swarm/daemon_state.json field "enabled"
  → bot /auto on / /auto off writes this field
- Graceful shutdown via SIGINT (Ctrl+C)
- Logs every poll cycle to memory/swarm/daemon_log.jsonl

USAGE:
    # Start daemon (foreground)
    python3 scripts/swarm_daemon.py

    # Background, custom poll interval
    python3 scripts/swarm_daemon.py --interval 300 &

    # Single iteration only (for testing)
    python3 scripts/swarm_daemon.py --once

    # Dry run (don't actually execute, just plan)
    python3 scripts/swarm_daemon.py --dry-run --once

SAFETY:
- Never starts in --execute mode by default for the daemon process. The bot
  must opt in via daemon_state.json {"enabled": true}.
- Hard rate limit: HOURLY_COMMIT_BUDGET prevents runaway aider invocations
- Hard total cap per session: TOTAL_COMMIT_CAP (default 20)
- Will not touch proposals with severity != "low" or "medium"
- Will refuse to run if no recent CEO interaction (TODO: check ambassador
  context recency — for now, always run when enabled)
"""

from __future__ import annotations

import argparse
import io
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


# UTF-8 streams (idempotent)
def _ensure_utf8(stream):
    enc = getattr(stream, "encoding", "") or ""
    if "utf" in enc.lower():
        return stream
    if hasattr(stream, "buffer"):
        return io.TextIOWrapper(stream.buffer, encoding="utf-8", errors="replace")
    return stream


sys.stdout = _ensure_utf8(sys.stdout)
sys.stderr = _ensure_utf8(sys.stderr)


# ── Paths ───────────────────────────────────────────────────────
def resolve_root() -> Path:
    cwd = Path.cwd()
    for c in [cwd, *cwd.parents]:
        if (c / "apps" / "api" / ".env").exists():
            return c
    return Path("C:/Projects/VOLAURA")


PROJECT_ROOT = resolve_root()
PROPOSALS_FILE = PROJECT_ROOT / "memory" / "swarm" / "proposals.json"
STATE_FILE = PROJECT_ROOT / "memory" / "swarm" / "daemon_state.json"
LOG_FILE = PROJECT_ROOT / "memory" / "swarm" / "daemon_log.jsonl"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"


# ── Limits ──────────────────────────────────────────────────────
DEFAULT_POLL_INTERVAL_SEC = 300  # 5 minutes
HOURLY_COMMIT_BUDGET = 5
TOTAL_COMMIT_CAP = 20
ALLOWED_SEVERITIES = {"low", "medium"}


# ── State management ───────────────────────────────────────────
def load_state() -> dict:
    """Load daemon state. Defaults: enabled=False, processed=[], commits=[]."""
    if not STATE_FILE.exists():
        return {
            "enabled": False,
            "processed_ids": [],
            "commit_timestamps": [],  # epoch seconds, last 24h
            "started_at": None,
            "total_commits": 0,
        }
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"enabled": False, "processed_ids": [], "commit_timestamps": [], "total_commits": 0}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def is_enabled() -> bool:
    return bool(load_state().get("enabled", False))


def set_enabled(value: bool) -> None:
    state = load_state()
    state["enabled"] = value
    if value and not state.get("started_at"):
        state["started_at"] = time.time()
    save_state(state)


# ── Logging ────────────────────────────────────────────────────
def log_event(event: dict) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    event["ts"] = time.time()
    event["iso"] = datetime.now(timezone.utc).isoformat()
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


# ── Rate limit ─────────────────────────────────────────────────
def commits_in_last_hour(state: dict) -> int:
    now = time.time()
    return sum(1 for ts in state.get("commit_timestamps", []) if now - ts < 3600)


def prune_old_timestamps(state: dict) -> None:
    now = time.time()
    state["commit_timestamps"] = [ts for ts in state.get("commit_timestamps", []) if now - ts < 86400]


def can_make_commit(state: dict) -> tuple[bool, str]:
    if state.get("total_commits", 0) >= TOTAL_COMMIT_CAP:
        return False, f"total commit cap reached ({TOTAL_COMMIT_CAP})"
    if commits_in_last_hour(state) >= HOURLY_COMMIT_BUDGET:
        return False, f"hourly budget reached ({HOURLY_COMMIT_BUDGET})"
    return True, ""


# ── Proposal selection ────────────────────────────────────────
def load_proposals() -> list[dict]:
    if not PROPOSALS_FILE.exists():
        return []
    try:
        with open(PROPOSALS_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("proposals", [])
    except Exception:
        return []


def select_next_proposal(state: dict) -> dict | None:
    """Pick the next approved AUTO-class proposal not yet processed."""
    processed = set(state.get("processed_ids", []))
    proposals = load_proposals()

    candidates = [
        p for p in proposals
        if p.get("status") == "approved"
        and p.get("id") not in processed
        and p.get("severity", "").lower() in ALLOWED_SEVERITIES
    ]
    # Sort: severity (medium first), then oldest first (FIFO)
    sev_order = {"medium": 0, "low": 1}
    candidates.sort(key=lambda p: (
        sev_order.get(p.get("severity", "").lower(), 99),
        p.get("timestamp", ""),
    ))
    return candidates[0] if candidates else None


# ── swarm_coder invocation ────────────────────────────────────
def run_swarm_coder(proposal_id: str, dry_run: bool = False) -> dict:
    """Invoke swarm_coder.py as subprocess. Return result dict."""
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "swarm_coder.py"),
        "--id", proposal_id,
    ]
    if not dry_run:
        cmd.append("--execute")

    sub_env = os.environ.copy()
    sub_env["PYTHONIOENCODING"] = "utf-8"

    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,
            env=sub_env,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "stage": "timeout", "tail": "swarm_coder >600s"}
    except Exception as e:
        return {"ok": False, "stage": "exception", "tail": str(e)}

    out = result.stdout or ""
    err = result.stderr or ""
    tail = (out + "\n" + err)[-1000:]

    if "Updating proposal status" in out:
        return {"ok": True, "stage": "implemented", "tail": tail}
    if "DRY RUN" in out or "dry_run" in out:
        return {"ok": True, "stage": "dry_run_planned", "tail": tail}
    if "REVERTED" in out or "reverted_unsafe" in out or "reverted_scope" in out:
        return {"ok": False, "stage": "reverted", "tail": tail}
    if "BLOCKED" in out or "blocked_by_gate" in out:
        return {"ok": False, "stage": "blocked", "tail": tail}
    if "AIDER FAILED" in out or "aider_failed" in out or "[FAIL]" in out:
        return {"ok": False, "stage": "aider_failed", "tail": tail}
    return {"ok": False, "stage": "unknown", "tail": tail}


# ── Main loop ─────────────────────────────────────────────────
_shutdown = False


def _handle_signal(signum, frame):
    global _shutdown
    _shutdown = True
    print(f"\n[DAEMON] received signal {signum}, shutting down after current iteration")


def run_iteration(dry_run: bool = False) -> dict:
    """One poll cycle: check enabled, pick proposal, run, update state."""
    state = load_state()

    if not state.get("enabled", False):
        log_event({"event": "iteration_skipped", "reason": "disabled"})
        return {"action": "skipped", "reason": "daemon disabled"}

    can_commit, reason = can_make_commit(state)
    if not can_commit:
        log_event({"event": "iteration_skipped", "reason": reason})
        return {"action": "skipped", "reason": reason}

    proposal = select_next_proposal(state)
    if not proposal:
        log_event({"event": "iteration_skipped", "reason": "no candidates"})
        return {"action": "skipped", "reason": "no approved AUTO proposals"}

    pid = proposal.get("id", "?")
    title = proposal.get("title", "?")[:80]
    print(f"[DAEMON] processing proposal {pid[:12]}: {title}")
    log_event({"event": "iteration_started", "proposal_id": pid, "title": title, "dry_run": dry_run})

    result = run_swarm_coder(pid, dry_run=dry_run)

    # Update state regardless of outcome (don't retry forever)
    state["processed_ids"].append(pid)
    if result["ok"] and not dry_run:
        state["commit_timestamps"].append(time.time())
        state["total_commits"] = state.get("total_commits", 0) + 1
        prune_old_timestamps(state)
    save_state(state)

    log_event({
        "event": "iteration_finished",
        "proposal_id": pid,
        "stage": result["stage"],
        "ok": result["ok"],
        "tail_len": len(result.get("tail", "")),
    })

    return {
        "action": "processed",
        "proposal_id": pid,
        "title": title,
        "result": result,
    }


def main_loop(interval: int, dry_run: bool, once: bool) -> None:
    print(f"[DAEMON] starting (interval={interval}s, dry_run={dry_run}, once={once})")
    print(f"[DAEMON] state file: {STATE_FILE}")
    print(f"[DAEMON] log file:   {LOG_FILE}")
    print(f"[DAEMON] enabled:    {is_enabled()}")

    signal.signal(signal.SIGINT, _handle_signal)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handle_signal)

    while not _shutdown:
        try:
            result = run_iteration(dry_run=dry_run)
            print(f"[DAEMON] {result.get('action')}: {result.get('reason') or result.get('proposal_id', '')}")
        except Exception as e:
            print(f"[DAEMON] iteration error: {e}", file=sys.stderr)
            log_event({"event": "iteration_error", "error": str(e)})

        if once:
            break

        # Sleep with shutdown check
        for _ in range(interval):
            if _shutdown:
                break
            time.sleep(1)

    print("[DAEMON] shutdown complete")


# ── CLI ───────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="Sprint S3: background autonomous coding daemon")
    parser.add_argument("--interval", type=int, default=DEFAULT_POLL_INTERVAL_SEC,
                        help=f"Poll interval seconds (default: {DEFAULT_POLL_INTERVAL_SEC})")
    parser.add_argument("--once", action="store_true", help="Run one iteration then exit")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually execute proposals")
    parser.add_argument("--enable", action="store_true", help="Set daemon enabled=true and exit")
    parser.add_argument("--disable", action="store_true", help="Set daemon enabled=false and exit")
    parser.add_argument("--status", action="store_true", help="Print state and exit")
    parser.add_argument("--reset", action="store_true", help="Clear processed_ids and commit history")
    args = parser.parse_args()

    if args.enable:
        set_enabled(True)
        print("[DAEMON] enabled=true")
        return
    if args.disable:
        set_enabled(False)
        print("[DAEMON] enabled=false")
        return
    if args.status:
        s = load_state()
        print(json.dumps(s, indent=2))
        return
    if args.reset:
        s = load_state()
        s["processed_ids"] = []
        s["commit_timestamps"] = []
        s["total_commits"] = 0
        save_state(s)
        print("[DAEMON] state reset")
        return

    main_loop(interval=args.interval, dry_run=args.dry_run, once=args.once)


if __name__ == "__main__":
    main()
