#!/usr/bin/env python3
"""daemon_task_seeder.py — generates tasks for the swarm daemon.

Runs periodically (via cron or GH Actions). Checks obligation deadlines,
open incidents, stale artifacts, and ceo_inbox — creates pending/ tasks
so the daemon never idles.

Usage:
    python scripts/daemon_task_seeder.py              # one-shot
    python scripts/daemon_task_seeder.py --dry-run    # preview only
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
QUEUE_PENDING = REPO_ROOT / "memory" / "atlas" / "work-queue" / "pending"
QUEUE_DONE = REPO_ROOT / "memory" / "atlas" / "work-queue" / "done"
COMPANY_STATE = REPO_ROOT / "memory" / "atlas" / "company-state.md"
INCIDENTS = REPO_ROOT / "memory" / "atlas" / "incidents.md"
CODE_INDEX = REPO_ROOT / "memory" / "swarm" / "code-index.json"
SHARED_CONTEXT = REPO_ROOT / "memory" / "swarm" / "shared-context.md"

TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")


def already_done(slug: str) -> bool:
    return (QUEUE_DONE / slug).exists()


def already_pending(slug: str) -> bool:
    return (QUEUE_PENDING / f"{slug}.md").exists()


def write_task(slug: str, task_type: str, title: str, body: str, dry_run: bool) -> bool:
    if already_done(slug) or already_pending(slug):
        return False
    QUEUE_PENDING.mkdir(parents=True, exist_ok=True)
    path = QUEUE_PENDING / f"{slug}.md"
    content = f"""---
type: {task_type}
title: {title}
perspectives: all
deadline_minutes: 30
---

{body}
"""
    if dry_run:
        print(f"[DRY-RUN] Would create: {path.name}")
        return True
    path.write_text(content, encoding="utf-8")
    print(f"[CREATED] {path.name}")
    return True


def check_code_index(dry_run: bool) -> int:
    if not CODE_INDEX.exists():
        return 0
    try:
        data = json.loads(CODE_INDEX.read_text(encoding="utf-8"))
        modules = len(data.get("modules", {}))
        endpoints = len(data.get("endpoints", []))
        if modules == 0 and endpoints == 0:
            return int(write_task(
                f"{TODAY}-code-index-empty",
                "audit",
                "code-index.json is empty — rebuild needed",
                "code-index.json has 0 modules and 0 endpoints despite a recent built_at timestamp. "
                "Investigate why the builder produced empty output and propose a fix. "
                "Check if packages/swarm/archive/code_index.py was moved to archive accidentally.",
                dry_run,
            ))
    except (json.JSONDecodeError, OSError):
        pass
    return 0


def check_shared_context_staleness(dry_run: bool) -> int:
    if not SHARED_CONTEXT.exists():
        return 0
    text = SHARED_CONTEXT.read_text(encoding="utf-8")[:500]
    if "2026-04-07" in text or "Session 91" in text:
        return int(write_task(
            f"{TODAY}-shared-context-stale",
            "audit",
            "shared-context.md is 3+ weeks stale",
            "Swarm shared-context.md still references Session 91 (2026-04-07). "
            "Current state is Session 124+, Path E, 4060+ tests. "
            "Every swarm agent reading this gets wrong project state. "
            "Propose updated content based on breadcrumb.md and heartbeat.md.",
            dry_run,
        ))
    return 0


def check_incidents(dry_run: bool) -> int:
    if not INCIDENTS.exists():
        return 0
    text = INCIDENTS.read_text(encoding="utf-8")
    open_count = text.lower().count("status: open") + text.lower().count("status unknown")
    if open_count >= 2:
        return int(write_task(
            f"{TODAY}-open-incidents-review",
            "audit",
            f"{open_count}+ open/unknown incidents need review",
            f"incidents.md has {open_count}+ entries with open/unknown status. "
            "Review each, determine if still relevant, propose closures or actions.",
            dry_run,
        ))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    created = 0
    created += check_code_index(args.dry_run)
    created += check_shared_context_staleness(args.dry_run)
    created += check_incidents(args.dry_run)

    print(f"\nSeeder complete. {created} new task(s) {'would be ' if args.dry_run else ''}created.")


if __name__ == "__main__":
    main()
