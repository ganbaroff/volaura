"""Scheduled workflow watchdog — catches silent red CRONs.

Why: Session 110 discovered Tribe Matching CRON had been failing every day
for 10+ days and nobody noticed. The push-CI path has a Session End Hook
that flags failures, but scheduled runs never triggered that path.

This script runs hourly (via atlas-watchdog.yml cron) and:
  1. Lists all scheduled workflows with `on.schedule`
  2. For each, gets the last 3 runs of its scheduled invocation
  3. If ≥ 2 consecutive scheduled failures → routes alert through notifier.py
  4. Alerts are cooldown-gated so we don't spam

Scope: read-only on GitHub API. Emits via notifier.py (category=error).
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

# Load notifier by direct file path to avoid packages/swarm/__init__.py pulling
# heavy deps (pydantic, loguru, the full swarm engine). notifier.py itself is
# stdlib-only; this import skips the init chain.
_NOTIFIER_PATH = Path(__file__).resolve().parents[1] / "packages" / "swarm" / "notifier.py"
_spec = importlib.util.spec_from_file_location("atlas_notifier", _NOTIFIER_PATH)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]
send_notification = _mod.send_notification


# Workflows whose scheduled-run health we care about. Explicit allowlist
# (not "all workflows") because some workflows run on-demand only and
# "no recent runs" isn't a failure for them.
WATCHED_WORKFLOWS = [
    "atlas-daily-digest.yml",
    "atlas-self-wake.yml",
    "tribe-matching.yml",
    "swarm-daily.yml",
    "match-checker.yml",
    "analytics-retention.yml",
    "post-deploy-agent.yml",
]

MIN_CONSECUTIVE_FAILS = 2  # 2 in a row → alert


def _list_runs(workflow: str, limit: int = 5) -> list[dict]:
    """Use `gh run list` to fetch the last N scheduled runs of a workflow."""
    try:
        result = subprocess.run(
            [
                "gh",
                "run",
                "list",
                "--workflow",
                workflow,
                "--event",
                "schedule",
                "--limit",
                str(limit),
                "--json",
                "conclusion,displayTitle,createdAt,databaseId",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode != 0:
            return []
        return json.loads(result.stdout or "[]")
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        return []


def _consecutive_failures(runs: list[dict]) -> int:
    """Count how many runs from the start are 'failure' in a row."""
    count = 0
    for run in runs:
        if run.get("conclusion") == "failure":
            count += 1
        else:
            break
    return count


def check() -> int:
    """Return 0 if all clear, 1 if any workflow alerted."""
    alerts = []
    for workflow in WATCHED_WORKFLOWS:
        runs = _list_runs(workflow, limit=5)
        if not runs:
            continue  # no scheduled runs yet — nothing to judge
        fails = _consecutive_failures(runs)
        if fails >= MIN_CONSECUTIVE_FAILS:
            latest = runs[0]
            alerts.append(
                {
                    "workflow": workflow,
                    "fails": fails,
                    "latest_run_id": latest.get("databaseId"),
                    "latest_title": latest.get("displayTitle", ""),
                }
            )

    if not alerts:
        print("All watched scheduled workflows green or single-flake.", flush=True)
        return 0

    # Compose one message per workflow, route through notifier cooldown gate.
    all_delivered = True
    for a in alerts:
        text = (
            f"Watchdog: workflow {a['workflow']} has {a['fails']} consecutive "
            f"scheduled failures (latest run {a['latest_run_id']}). "
            f"'{a['latest_title']}'. Check /actions."
        )
        delivered = send_notification(category="error", text=text, severity="warning")
        if not delivered:
            all_delivered = False
        print(f"[{a['workflow']}] alert: delivered={delivered}", flush=True)

    # Exit 0 when the alert path succeeded — the alert IS the signal, we don't
    # want this workflow to itself look "failed" and start feeding back into
    # monitoring. Exit 1 only if the notifier couldn't deliver (real problem).
    return 0 if all_delivered else 1


if __name__ == "__main__":
    sys.exit(check())
