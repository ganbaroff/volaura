"""Validate the fix-of-fix hotspot detector against 90 days of merged PRs.

Research verdict: if INC-001 / INC-017 / INC-002 files light up, detector works
on known ground truth. Runs entirely against local `git log`; does not hit
GitHub. Prints a markdown-ish report to stdout.

Usage:
    python scripts/validate_hotspot_detector.py [--since 90] [--threshold 3]

Output:
    For every file touched in the last N days, list how many commits in the
    same window matched the fix-* pattern. Sort desc. Highlight the three
    canonical incident files (telegram_webhook.py, callback/page.tsx,
    packages/swarm/__init__.py) so CEO can verify detector sanity.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

FIX_PATTERN = re.compile(r"^(fix|hotfix|bugfix|inc-|correct|restore)", re.IGNORECASE)

CANONICAL_INCIDENT_FILES = [
    ("INC-017", "apps/web/src/app/[locale]/callback/page.tsx"),
    ("INC-001/INC-008", "apps/api/app/routers/telegram_webhook.py"),
    ("INC-002", "packages/swarm/__init__.py"),
]


def _run(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True, encoding="utf-8", errors="replace")


def collect(since_days: int) -> tuple[dict[str, int], dict[str, list[str]]]:
    since_date = (datetime.now(timezone.utc) - timedelta(days=since_days)).strftime("%Y-%m-%d")
    # All commits in window with subject + file list (one commit per block).
    raw = _run(
        [
            "git",
            "log",
            f"--since={since_date}",
            "--pretty=format:===%h|%s",
            "--name-only",
        ]
    )
    fix_touches: Counter[str] = Counter()
    fix_commits: dict[str, list[str]] = defaultdict(list)

    current_subject: str | None = None
    current_sha: str | None = None
    is_fix = False
    for line in raw.splitlines():
        if line.startswith("==="):
            # New commit header: ===<sha>|<subject>
            parts = line[3:].split("|", 1)
            current_sha = parts[0]
            current_subject = parts[1] if len(parts) > 1 else ""
            is_fix = bool(FIX_PATTERN.match(current_subject or ""))
            continue
        if not line.strip():
            continue
        if is_fix and current_subject and current_sha:
            fix_touches[line] += 1
            fix_commits[line].append(f"{current_sha} {current_subject}")
    return dict(fix_touches), fix_commits


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--since", type=int, default=90, help="days to look back (default 90)")
    p.add_argument("--threshold", type=int, default=3, help="min fix-touches to report (default 3)")
    args = p.parse_args()

    print(f"# fix-of-fix backfill — last {args.since} days — threshold >= {args.threshold}\n")
    touches, commits = collect(args.since)
    hot = sorted(touches.items(), key=lambda kv: (-kv[1], kv[0]))
    hot = [(f, n) for f, n in hot if n >= args.threshold]

    if not hot:
        print("_No files met the threshold._")
    else:
        print(f"## Top hotspots ({len(hot)})")
        for f, n in hot:
            print(f"\n### {f}  — {n} fix-touches")
            for c in commits[f][:10]:
                print(f"  - {c}")

    print("\n## Canonical incidents — sanity check")
    for label, path in CANONICAL_INCIDENT_FILES:
        n = touches.get(path, 0)
        mark = "✅" if n >= args.threshold else "❌"
        print(f"- {mark} **{label}** `{path}` → {n} fix-touches")

    print("\n_Detector validates if all three canonical rows show ✅._")
    return 0


if __name__ == "__main__":
    sys.exit(main())
