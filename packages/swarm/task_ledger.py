"""
task_ledger.py — Unified task registry for all agent activity.

Every agent action (proposal generated, fix attempted, DSP run, commit made)
writes one entry here. Single source of truth for "what have agents done?"

Schema (one JSON object per line):
{
  "id":         str   — unique ID (proposal_id or generated)
  "ts":         str   — ISO timestamp
  "source":     str   — "proposal" | "auto_fix" | "dsp" | "cron_run" | "migrate"
  "project":    str   — "volaura" | "mindshift" | "ecosystem" | "swarm"
  "agent":      str   — agent name
  "mode":       str   — autonomous_run mode (daily-ideation, cto-audit, etc.)
  "title":      str   — task title
  "severity":   str   — critical | high | medium | low | info
  "status":     str   — generated | attempted | committed | approved | rejected | pending
  "commit":     str?  — git commit hash if auto_fix succeeded
  "tokens_in":  int?  — input tokens used
  "tokens_out": int?  — output tokens used
  "cost_usd":   float?
  "provider":   str?  — which LLM provider
  "note":       str?  — short human note
}
"""

from __future__ import annotations
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

LEDGER_PATH = Path(__file__).parent.parent.parent / "memory" / "swarm" / "task_ledger.jsonl"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _short_id() -> str:
    return str(uuid.uuid4())[:8]


def write(
    *,
    source: str,
    title: str,
    agent: str = "swarm",
    project: str = "volaura",
    mode: str = "",
    severity: str = "info",
    status: str = "generated",
    entry_id: Optional[str] = None,
    commit: Optional[str] = None,
    tokens_in: Optional[int] = None,
    tokens_out: Optional[int] = None,
    cost_usd: Optional[float] = None,
    provider: Optional[str] = None,
    note: Optional[str] = None,
    ts: Optional[str] = None,
) -> dict:
    """Append one entry to the ledger. Returns the written dict."""
    entry = {
        "id": entry_id or _short_id(),
        "ts": ts or _now(),
        "source": source,
        "project": project,
        "agent": agent,
        "mode": mode,
        "title": title,
        "severity": severity,
        "status": status,
    }
    if commit:     entry["commit"] = commit
    if tokens_in:  entry["tokens_in"] = tokens_in
    if tokens_out: entry["tokens_out"] = tokens_out
    if cost_usd:   entry["cost_usd"] = cost_usd
    if provider:   entry["provider"] = provider
    if note:       entry["note"] = note

    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def write_run_start(mode: str, n_agents: int, providers: list[str]) -> dict:
    return write(
        source="cron_run",
        title=f"Swarm run started — {mode} ({n_agents} agents)",
        agent="engine",
        mode=mode,
        severity="info",
        status="started",
        note=f"providers: {', '.join(providers)}",
    )


def write_proposal(proposal, mode: str = "") -> dict:
    """Write a Proposal object from autonomous_run to the ledger."""
    return write(
        source="proposal",
        title=proposal.title,
        agent=getattr(proposal, "agent_name", "unknown"),
        mode=mode,
        severity=getattr(proposal, "severity", {}).value if hasattr(getattr(proposal, "severity", None), "value") else str(getattr(proposal, "severity", "info")),
        status="generated",
        entry_id=getattr(proposal, "id", None),
        ts=getattr(proposal, "timestamp", None),
    )


def write_fix_attempt(proposal_id: str, title: str, result: dict, mode: str = "") -> dict:
    """Write the result of a swarm_coder auto-fix attempt."""
    ok = result.get("ok", False) if isinstance(result, dict) else False
    commit = result.get("commit_hash", "") if isinstance(result, dict) else ""
    error = result.get("error", "") if isinstance(result, dict) else str(result)

    if ok and commit:
        status = "committed"
    elif isinstance(result, dict) and result.get("stage") == "blocked_by_gate":
        status = "blocked"
    elif "timeout" in str(error):
        status = "timeout"
    elif "GEMINI_API_KEY" in str(error):
        status = "config_error"
    else:
        status = "failed"

    tokens_sent = result.get("tokens_sent", "") if isinstance(result, dict) else ""
    try:
        ti = int(str(tokens_sent).replace("k", "000").replace("?", "0")) if tokens_sent else None
    except Exception:
        ti = None

    return write(
        source="auto_fix",
        title=title,
        agent="swarm_coder",
        mode=mode,
        severity="medium",
        status=status,
        entry_id=proposal_id,
        commit=commit or None,
        tokens_in=ti,
        note=str(error)[:120] if not ok else None,
    )


def stats() -> dict:
    """Return summary stats from the ledger."""
    if not LEDGER_PATH.exists():
        return {"total": 0}

    from collections import Counter
    entries = []
    with open(LEDGER_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except Exception:
                    pass

    return {
        "total": len(entries),
        "by_source": dict(Counter(e["source"] for e in entries)),
        "by_status": dict(Counter(e["status"] for e in entries)),
        "by_project": dict(Counter(e["project"] for e in entries)),
        "by_severity": dict(Counter(e["severity"] for e in entries)),
        "commits": sum(1 for e in entries if e.get("commit")),
        "total_tokens_in": sum(e.get("tokens_in", 0) or 0 for e in entries),
        "total_tokens_out": sum(e.get("tokens_out", 0) or 0 for e in entries),
    }
