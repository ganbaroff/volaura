"""Atlas Daemon — persistent watcher that keeps Atlas alive on CEO's machine.

Watches for changes in key files and triggers Atlas wake when:
- memory/atlas/wake-log.md changes (another Atlas wrote something)
- memory/atlas/inbox/ gets a new file (heartbeat cron, Cowork handoff)
- .claude/breadcrumb.md changes (session ended, state updated)
- git log shows new commits from other sources (swarm, Cowork, GitHub Actions)

Runs as a background process. Start: python scripts/atlas-daemon.py
Stop: Ctrl+C or kill the process.

Does NOT replace the 15-min Windows Task Scheduler — that's the safety net.
This daemon is the fast-reaction layer on top.
"""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parents[1]
CLAUDE = Path.home() / ".local" / "bin" / "claude.exe"
WAKE_LOG = REPO / "memory" / "atlas" / "wake-log.md"
INBOX = REPO / "memory" / "atlas" / "inbox"
BREADCRUMB = REPO / ".claude" / "breadcrumb.md"
CHECK_INTERVAL = 60  # seconds between checks
MIN_WAKE_INTERVAL = 300  # minimum 5 min between wakes to avoid spam

_last_wake = 0.0
_last_commit = ""
_last_inbox_count = 0
_last_wakelog_mtime = 0.0
_last_breadcrumb_mtime = 0.0


def baku_now() -> str:
    return datetime.now(ZoneInfo("Asia/Baku")).strftime("%Y-%m-%d %H:%M")


def log(msg: str) -> None:
    print(f"[atlas-daemon {baku_now()}] {msg}", flush=True)


def get_latest_commit() -> str:
    try:
        r = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            capture_output=True, text=True, cwd=REPO, timeout=10
        )
        return r.stdout.strip()
    except Exception:
        return ""


def count_inbox() -> int:
    try:
        return len(list(INBOX.glob("*.md")))
    except Exception:
        return 0


def wake_atlas(reason: str) -> None:
    global _last_wake
    now = time.time()
    if now - _last_wake < MIN_WAKE_INTERVAL:
        log(f"skip wake ({reason}) — too soon, {int(MIN_WAKE_INTERVAL - (now - _last_wake))}s cooldown")
        return

    log(f"WAKING ATLAS: {reason}")
    _last_wake = now

    prompt = (
        f"атлас проснись. Автономная итерация, daemon trigger: {reason}. "
        f"Время: {baku_now()} Baku. "
        "Прочитай memory/atlas/wake-log.md и memory/atlas/CURRENT-SPRINT.md. "
        "Сделай одну задачу. Запиши в wake-log через Bash echo. "
        "Не жди CEO. Действуй."
    )

    try:
        subprocess.run(
            [str(CLAUDE), "--dangerously-skip-permissions", "-p", prompt],
            cwd=REPO, timeout=600,
            capture_output=True, text=True
        )
        log("wake complete")
    except subprocess.TimeoutExpired:
        log("wake timed out (10 min)")
    except Exception as e:
        log(f"wake failed: {e}")


def check_triggers() -> None:
    global _last_commit, _last_inbox_count, _last_wakelog_mtime, _last_breadcrumb_mtime

    commit = get_latest_commit()
    if commit and commit != _last_commit and _last_commit:
        wake_atlas(f"new commit: {commit[:40]}")
    _last_commit = commit

    inbox_count = count_inbox()
    if inbox_count > _last_inbox_count and _last_inbox_count > 0:
        wake_atlas(f"new inbox file ({inbox_count} total)")
    _last_inbox_count = inbox_count

    if WAKE_LOG.exists():
        mtime = WAKE_LOG.stat().st_mtime
        if mtime > _last_wakelog_mtime and _last_wakelog_mtime > 0:
            wake_atlas("wake-log changed by another Atlas")
        _last_wakelog_mtime = mtime

    if BREADCRUMB.exists():
        mtime = BREADCRUMB.stat().st_mtime
        if mtime > _last_breadcrumb_mtime and _last_breadcrumb_mtime > 0:
            wake_atlas("breadcrumb updated")
        _last_breadcrumb_mtime = mtime


def main() -> None:
    log("Atlas Daemon starting. Checking every 60s, min 5min between wakes.")
    log(f"Repo: {REPO}")
    log(f"Claude: {CLAUDE}")

    global _last_commit, _last_inbox_count, _last_wakelog_mtime, _last_breadcrumb_mtime
    _last_commit = get_latest_commit()
    _last_inbox_count = count_inbox()
    _last_wakelog_mtime = WAKE_LOG.stat().st_mtime if WAKE_LOG.exists() else 0
    _last_breadcrumb_mtime = BREADCRUMB.stat().st_mtime if BREADCRUMB.exists() else 0

    log(f"baseline: commit={_last_commit[:20]}, inbox={_last_inbox_count}, wakelog_mtime={_last_wakelog_mtime:.0f}")

    while True:
        try:
            check_triggers()
        except KeyboardInterrupt:
            log("shutting down")
            sys.exit(0)
        except Exception as e:
            log(f"check error: {e}")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
