#!/usr/bin/env python3
"""Session-End Hook — captures git diff → SESSION-DIFFS.jsonl → updates swarm context.

Run automatically via .github/workflows/session-end.yml on every push to main.
Closes the #1 swarm gap: 42% of proposals were "already done" because agents
couldn't see what changed since their last run.

Usage:
    python -m packages.swarm.session_end_hook
    python -m packages.swarm.session_end_hook --max-diff-lines=500
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
packages_path = str(project_root / "packages")
if packages_path not in sys.path:
    sys.path.insert(0, packages_path)

from loguru import logger

SESSION_DIFFS_FILE = project_root / "memory" / "swarm" / "SESSION-DIFFS.jsonl"
SHARED_CONTEXT_FILE = project_root / "memory" / "swarm" / "shared-context.md"
SPRINT_STATE_FILE = project_root / "memory" / "context" / "sprint-state.md"

DEFAULT_MAX_DIFF_LINES = 300


def _run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git"] + args,
        cwd=project_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def _get_session_commits() -> list[dict]:
    """Get commits from the last push (since the previous push marker or last 24h)."""
    # Get commits from last 24 hours as a proxy for "this session"
    raw = _run_git([
        "log",
        "--since=24 hours ago",
        "--pretty=format:%H|%s|%an|%ai",
        "--no-merges",
    ])
    if not raw:
        return []

    commits = []
    for line in raw.splitlines():
        parts = line.split("|", 3)
        if len(parts) == 4:
            commits.append({
                "hash": parts[0][:12],
                "message": parts[1],
                "author": parts[2],
                "timestamp": parts[3],
            })
    return commits


def _get_changed_files(since_ref: str = "HEAD~1") -> list[str]:
    """Get list of files changed since ref."""
    raw = _run_git(["diff", "--name-only", since_ref, "HEAD"])
    if not raw:
        return []
    return [f.strip() for f in raw.splitlines() if f.strip()]


def _get_diff_summary(changed_files: list[str], max_lines: int) -> str:
    """Get a truncated diff focused on key backend/frontend files."""
    # Prioritise: migrations, routers, schemas, tests — skip lockfiles/generated
    priority_patterns = [
        "supabase/migrations/",
        "apps/api/app/routers/",
        "apps/api/app/schemas/",
        "apps/api/app/core/",
        "apps/api/app/services/",
        "apps/api/tests/",
        "apps/web/src/app/",
        "apps/web/src/components/",
        "packages/swarm/",
        "docs/",
        "memory/",
    ]
    skip_patterns = [
        "pnpm-lock.yaml",
        "tsconfig.tsbuildinfo",
        "apps/web/src/lib/api/generated/",
        ".claude/",
        "node_modules/",
    ]

    priority_files = []
    other_files = []
    for f in changed_files:
        if any(s in f for s in skip_patterns):
            continue
        if any(p in f for p in priority_patterns):
            priority_files.append(f)
        else:
            other_files.append(f)

    # Get stat diff (lines added/removed per file)
    stat = _run_git(["diff", "--stat", "HEAD~1", "HEAD"])
    stat_lines = stat.splitlines()[:30]

    # Get actual diff for priority files only (truncated)
    diff_lines = []
    remaining = max_lines
    for f in priority_files[:10]:  # max 10 files
        if remaining <= 0:
            break
        file_diff = _run_git(["diff", "HEAD~1", "HEAD", "--", f])
        lines = file_diff.splitlines()[:remaining]
        diff_lines.extend(lines)
        diff_lines.append("")
        remaining -= len(lines)

    summary = "### STAT\n" + "\n".join(stat_lines)
    if diff_lines:
        summary += "\n\n### KEY DIFFS (priority files)\n" + "\n".join(diff_lines)
    if other_files:
        summary += f"\n\n### OTHER CHANGED FILES ({len(other_files)})\n" + "\n".join(other_files[:20])

    return summary


def _extract_new_migrations(changed_files: list[str]) -> list[str]:
    return [
        Path(f).name
        for f in changed_files
        if "supabase/migrations/" in f and f.endswith(".sql")
    ]


def _extract_new_tests(changed_files: list[str]) -> list[str]:
    return [
        Path(f).name
        for f in changed_files
        if "tests/" in f and f.startswith("apps/api/tests/")
    ]


def _extract_new_routes(changed_files: list[str]) -> list[str]:
    return [
        Path(f).stem
        for f in changed_files
        if "app/routers/" in f and f.endswith(".py")
    ]


def build_session_entry(max_diff_lines: int = DEFAULT_MAX_DIFF_LINES) -> dict:
    """Build a single session diff entry for SESSION-DIFFS.jsonl."""
    now = datetime.now(UTC).isoformat()
    commits = _get_session_commits()
    changed_files = _get_changed_files("HEAD~1")

    # Read sprint state headline
    sprint_headline = "unknown"
    if SPRINT_STATE_FILE.exists():
        with open(SPRINT_STATE_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("**Status:**"):
                    sprint_headline = line.replace("**Status:**", "").strip()
                    break

    entry = {
        "timestamp": now,
        "sprint_headline": sprint_headline,
        "commits": commits,
        "files_changed_count": len(changed_files),
        "new_migrations": _extract_new_migrations(changed_files),
        "new_tests": _extract_new_tests(changed_files),
        "new_routes": _extract_new_routes(changed_files),
        "diff_summary": _get_diff_summary(changed_files, max_diff_lines),
    }
    return entry


def append_session_diff(entry: dict) -> None:
    """Append entry to SESSION-DIFFS.jsonl (create if missing)."""
    SESSION_DIFFS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SESSION_DIFFS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    logger.info(f"Appended session diff to {SESSION_DIFFS_FILE}")


def update_shared_context_recently_shipped(new_migrations: list[str], new_routes: list[str]) -> None:
    """Inject a RECENTLY SHIPPED section at the top of shared-context.md."""
    if not SHARED_CONTEXT_FILE.exists():
        return
    if not new_migrations and not new_routes:
        return

    with open(SHARED_CONTEXT_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove old RECENTLY SHIPPED block if present
    import re
    content = re.sub(
        r"<!-- RECENTLY_SHIPPED_START -->.*?<!-- RECENTLY_SHIPPED_END -->\n\n",
        "",
        content,
        flags=re.DOTALL,
    )

    now_str = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"<!-- RECENTLY_SHIPPED_START -->"]
    lines.append(f"## ⚡ RECENTLY SHIPPED (last push — {now_str})")
    lines.append("**Read this FIRST — prevents proposing already-shipped work.**")
    if new_migrations:
        lines.append(f"\nNew migrations: {', '.join(new_migrations)}")
    if new_routes:
        lines.append(f"New/updated routers: {', '.join(new_routes)}")
    lines.append("<!-- RECENTLY_SHIPPED_END -->\n")

    updated = "\n".join(lines) + "\n" + content
    with open(SHARED_CONTEXT_FILE, "w", encoding="utf-8") as f:
        f.write(updated)
    logger.info("Updated shared-context.md with RECENTLY SHIPPED block")


def main() -> None:
    parser = argparse.ArgumentParser(description="Session-end hook: capture git diff for swarm")
    parser.add_argument("--max-diff-lines", type=int, default=DEFAULT_MAX_DIFF_LINES)
    parser.add_argument("--dry-run", action="store_true", help="Print entry without writing")
    args = parser.parse_args()

    entry = build_session_entry(max_diff_lines=args.max_diff_lines)

    if args.dry_run:
        print(json.dumps(entry, indent=2, ensure_ascii=False))
        return

    append_session_diff(entry)
    update_shared_context_recently_shipped(entry["new_migrations"], entry["new_routes"])

    logger.info(
        "Session hook complete",
        commits=len(entry["commits"]),
        files_changed=entry["files_changed_count"],
        new_migrations=entry["new_migrations"],
        new_routes=entry["new_routes"],
    )


if __name__ == "__main__":
    main()
