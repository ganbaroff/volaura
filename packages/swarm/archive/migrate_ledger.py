"""
migrate_ledger.py — One-time migration of all historical agent activity into task_ledger.jsonl.

Sources:
  1. memory/swarm/proposals.json        — all 110 proposals
  2. memory/swarm/swarm_coder_log.jsonl — 65 auto-fix attempts
  3. memory/swarm/agent-feedback-log.md — 57 manually tracked outcomes
  4. memory/swarm/outcome-log.jsonl     — 4 sprint task verifications
  5. packages/swarm/archive/*.json      — 16 DSP debate runs
  6. git log (swarm: commits)           — cron run commits

Run once: python -m packages.swarm.migrate_ledger
"""

import json
import sys
import os
import re
import subprocess
import glob
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from packages.swarm.task_ledger import write, LEDGER_PATH

# ── Clear existing ledger (idempotent re-run) ────────────────────────────────
if LEDGER_PATH.exists():
    LEDGER_PATH.unlink()
    print(f"Cleared existing ledger at {LEDGER_PATH}")

written = 0


def log(msg: str):
    print(f"  {msg}")


# ── 1. proposals.json ────────────────────────────────────────────────────────
print("\n[1] Migrating proposals.json...")
proposals_path = ROOT / "memory" / "swarm" / "proposals.json"
try:
    data = json.loads(proposals_path.read_text(encoding="utf-8", errors="replace"))
    for p in data.get("proposals", []):
        write(
            source="proposal",
            title=p.get("title", "untitled"),
            agent=p.get("agent", "unknown"),
            mode="daily-ideation",
            severity=p.get("severity", "medium"),
            status=p.get("status", "pending"),
            entry_id=p.get("id"),
            ts=p.get("timestamp"),
            note=p.get("ceo_decision", "")[:120] if p.get("ceo_decision") else None,
        )
        written += 1
    log(f"{len(data.get('proposals', []))} proposals migrated")
except Exception as e:
    log(f"SKIP: {e}")


# ── 2. swarm_coder_log.jsonl ─────────────────────────────────────────────────
print("\n[2] Migrating swarm_coder_log.jsonl...")
coder_log = ROOT / "memory" / "swarm" / "swarm_coder_log.jsonl"
coder_count = 0
try:
    for line in coder_log.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue

        result = d.get("result", {})
        ok = result.get("ok", False) if isinstance(result, dict) else False
        commit = (result.get("commit_hash", "") or "") if isinstance(result, dict) else ""
        error = result.get("error", "") if isinstance(result, dict) else ""
        stage = result.get("stage", "") if isinstance(result, dict) else ""

        if ok and commit:
            status = "committed"
        elif stage == "blocked_by_gate":
            status = "blocked"
        elif "timeout" in str(error):
            status = "timeout"
        elif "GEMINI_API_KEY" in str(error):
            status = "config_error"
        elif "GEMINI_API_KEY" in str(result):
            status = "config_error"
        else:
            status = "failed"

        write(
            source="auto_fix",
            title=d.get("proposal_title", "untitled")[:100],
            agent="swarm_coder",
            mode="auto_fix",
            severity=d.get("proposal_severity", "medium"),
            status=status,
            entry_id=d.get("proposal_id"),
            commit=commit or None,
            ts=d.get("ts"),
            note=str(error)[:120] if error and not ok else None,
        )
        written += 1
        coder_count += 1
    log(f"{coder_count} auto-fix attempts migrated")
except Exception as e:
    log(f"SKIP: {e}")


# ── 3. agent-feedback-log.md ─────────────────────────────────────────────────
print("\n[3] Migrating agent-feedback-log.md...")
feedback_log = ROOT / "memory" / "swarm" / "agent-feedback-log.md"
fb_count = 0
try:
    for line in feedback_log.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip().startswith("|"):
            continue
        parts = [p.strip() for p in line.split("|")]
        parts = [p for p in parts if p]
        # Format: | Session | Agent | Proposal ID | Short Title | Status | Outcome | Note |
        if len(parts) < 5:
            continue
        if parts[0] in ("Session", "---", "session"):
            continue
        try:
            session = parts[0]
            agent = parts[1]
            # find status (implemented/open/rejected/acknowledged/partial)
            status_raw = ""
            title = ""
            for i, p in enumerate(parts):
                if p.lower() in ("implemented", "open", "rejected", "acknowledged", "partial", "skipped", "done"):
                    status_raw = p.lower()
                    title = parts[i - 1] if i > 1 else parts[2] if len(parts) > 2 else "untitled"
                    break
            if not status_raw:
                continue

            status_map = {
                "implemented": "committed",
                "open": "pending",
                "rejected": "rejected",
                "acknowledged": "approved",
                "partial": "attempted",
                "skipped": "rejected",
                "done": "committed",
            }
            write(
                source="feedback_log",
                title=title[:100],
                agent=agent,
                mode="tracked",
                severity="medium",
                status=status_map.get(status_raw, status_raw),
                note=f"Session {session}",
            )
            written += 1
            fb_count += 1
        except Exception:
            continue
    log(f"{fb_count} feedback-log rows migrated")
except Exception as e:
    log(f"SKIP: {e}")


# ── 4. outcome-log.jsonl ─────────────────────────────────────────────────────
print("\n[4] Migrating outcome-log.jsonl...")
outcome_log = ROOT / "memory" / "swarm" / "outcome-log.jsonl"
oc_count = 0
try:
    for line in outcome_log.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        verdict = d.get("verdict", "unknown")
        status_map = {"pass": "committed", "partial": "attempted", "fail": "failed"}
        write(
            source="outcome_verify",
            title=d.get("task_title", "untitled"),
            agent="outcome_verifier",
            mode="sprint_verify",
            severity="info",
            status=status_map.get(verdict, verdict),
            ts=d.get("timestamp"),
            note="; ".join(d.get("gaps", []))[:120] if d.get("gaps") else None,
        )
        written += 1
        oc_count += 1
    log(f"{oc_count} outcome-log entries migrated")
except Exception as e:
    log(f"SKIP: {e}")


# ── 5. archive DSP runs ───────────────────────────────────────────────────────
print("\n[5] Migrating archive DSP runs...")
ar_count = 0
for f in sorted(glob.glob(str(ROOT / "packages" / "swarm" / "archive" / "*.json"))):
    try:
        d = json.load(open(f, encoding="utf-8", errors="replace"))
        fname = os.path.basename(f).replace(".json", "")

        # Extract token stats if present
        ts_data = {}
        def find_ts(obj, depth=0):
            if depth > 5 or not isinstance(obj, dict): return
            if "token_stats" in obj:
                ts_data.update(obj["token_stats"])
                return
            for v in obj.values(): find_ts(v, depth+1)
        find_ts(d)

        agents_used = d.get("agents_used", 0) if isinstance(d, dict) else 0
        agents_ok = d.get("agents_succeeded", 0) if isinstance(d, dict) else 0

        write(
            source="dsp",
            title=f"DSP run: {fname}",
            agent="dsp_engine",
            mode="dsp",
            severity="info",
            status="committed" if agents_ok > 0 else "attempted",
            tokens_in=ts_data.get("total_input_tokens"),
            tokens_out=ts_data.get("total_output_tokens"),
            cost_usd=ts_data.get("total_cost_usd"),
            note=f"agents: {agents_used} called / {agents_ok} succeeded" if agents_used else None,
        )
        written += 1
        ar_count += 1
    except Exception as e:
        pass
log(f"{ar_count} archive DSP runs migrated")


# ── 6. git log — swarm cron commits ──────────────────────────────────────────
print("\n[6] Migrating git swarm cron commits...")
git_count = 0
try:
    result = subprocess.run(
        ["git", "log", "--oneline", "--format=%H|%ai|%s", "--since=2026-03-01"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT
    )
    for line in result.stdout.splitlines():
        parts = line.split("|", 2)
        if len(parts) < 3:
            continue
        commit_hash, ts_raw, subject = parts
        if "swarm: daily" not in subject and "feat(swarm)" not in subject:
            continue
        try:
            ts = datetime.fromisoformat(ts_raw.strip()).astimezone(timezone.utc).isoformat()
        except Exception:
            ts = ts_raw.strip()
        write(
            source="cron_run",
            title=subject.strip()[:100],
            agent="engine",
            mode="daily-ideation",
            severity="info",
            status="committed",
            commit=commit_hash[:12],
            ts=ts,
        )
        written += 1
        git_count += 1
    log(f"{git_count} swarm git commits migrated")
except Exception as e:
    log(f"SKIP: {e}")


# ── Summary ───────────────────────────────────────────────────────────────────
print(f"\n{'='*50}")
print(f"MIGRATION COMPLETE — {written} entries written to task_ledger.jsonl")
print(f"{'='*50}")

from packages.swarm.task_ledger import stats
s = stats()
print(json.dumps(s, indent=2, ensure_ascii=False))
