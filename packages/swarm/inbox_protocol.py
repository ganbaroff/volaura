"""Swarm Inbox Protocol — manages proposals, votes, routing, and CEO escalations.

This is the canonical record system for autonomous agent output.
Telegram is the delivery layer; this is the source of truth.

Architecture B (Session 21, voted A+C hybrid by 5 agents):
- Agents write ALL proposals to proposals.json
- HIGH/CRITICAL get forwarded to Telegram
- CEO replies (act/dismiss/defer) → status updates here
- Claude Code surfaces pending items at session start
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ProposalType(str, Enum):
    IDEA = "idea"
    ESCALATION = "escalation"
    COMPLAINT = "complaint"
    CODE_REVIEW = "code_review"
    SECURITY = "security"


class ProposalStatus(str, Enum):
    PENDING = "pending"
    ACTED = "acted"
    DISMISSED = "dismissed"
    DEFERRED = "deferred"


class Proposal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    agent: str  # model name or agent_id
    severity: Severity
    type: ProposalType
    status: ProposalStatus = ProposalStatus.PENDING
    title: str  # one-line summary
    content: str  # full proposal text
    votes_for: int = 0
    votes_against: int = 0
    vote_details: list[dict[str, Any]] = Field(default_factory=list)
    escalate_to_ceo: bool = False
    convergent: bool = False  # True if 2+ agents independently proposed similar idea
    ceo_decision: str | None = None
    ceo_decision_at: str | None = None

    # Cross-model judge scores (B7 — Approach 1, LLM-as-judge, arXiv 2306.05685)
    # Judge model is ALWAYS different family from generator (asymmetric — avoids 10-25% self-favor bias)
    judge_score: int | None = None        # 0-5: number of criteria passed (binary per criterion)
    judge_model: str | None = None        # which model judged this (e.g. "gemini-2.5-flash-preview-04-17")
    judge_reasoning: str | None = None    # brief explanation of score
    judge_criteria: dict | None = None    # {criterion: pass/fail} for each of 5 criteria


class InboxProtocol:
    """Manages the canonical proposal store."""

    def __init__(self, project_root: Path | None = None):
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent
        self.inbox_dir = project_root / "memory" / "swarm"
        self.proposals_file = self.inbox_dir / "proposals.json"
        self.ceo_inbox_file = self.inbox_dir / "ceo-inbox.md"
        self.inbox_dir.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict:
        if self.proposals_file.exists():
            with open(self.proposals_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"schema_version": "1.0", "proposals": []}

    def _save(self, data: dict) -> None:
        with open(self.proposals_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_proposal(self, proposal: Proposal) -> str:
        """Add a new proposal to the canonical store. Returns proposal ID."""
        data = self._load()
        data["proposals"].append(proposal.model_dump())
        self._save(data)

        # If escalation → also write to CEO inbox
        if proposal.escalate_to_ceo or proposal.severity == Severity.CRITICAL:
            self._write_ceo_escalation(proposal)

        return proposal.id

    def _write_ceo_escalation(self, proposal: Proposal) -> None:
        """Append escalation to CEO inbox markdown file."""
        entry = (
            f"\n---\n"
            f"## [{proposal.severity.value.upper()}] {proposal.title}\n"
            f"**Agent:** {proposal.agent} | **Time:** {proposal.timestamp} | **ID:** {proposal.id}\n\n"
            f"{proposal.content}\n\n"
            f"**Action:** Reply with `act {proposal.id}` / `dismiss {proposal.id}` / `defer {proposal.id}`\n"
        )
        with open(self.ceo_inbox_file, "a", encoding="utf-8") as f:
            f.write(entry)

    def get_pending(self, min_severity: Severity | None = None) -> list[dict]:
        """Get all pending proposals, optionally filtered by severity."""
        data = self._load()
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        min_level = severity_order.get(min_severity.value, 3) if min_severity else 3

        pending = [
            p for p in data["proposals"]
            if p["status"] == "pending"
            and severity_order.get(p["severity"], 3) <= min_level
        ]
        # Sort: critical first, then by timestamp
        pending.sort(key=lambda p: (severity_order.get(p["severity"], 3), p["timestamp"]))
        return pending

    def get_escalations(self) -> list[dict]:
        """Get all pending escalations for CEO."""
        data = self._load()
        return [
            p for p in data["proposals"]
            if p["status"] == "pending" and p.get("escalate_to_ceo", False)
        ]

    def update_status(
        self,
        proposal_id: str,
        status: ProposalStatus,
        ceo_decision: str | None = None,
    ) -> bool:
        """Update proposal status. Returns True if found."""
        data = self._load()
        for p in data["proposals"]:
            if p["id"] == proposal_id:
                p["status"] = status.value
                if ceo_decision:
                    p["ceo_decision"] = ceo_decision
                    p["ceo_decision_at"] = datetime.now(timezone.utc).isoformat()
                self._save(data)
                return True
        return False

    def record_vote(
        self,
        proposal_id: str,
        agent: str,
        vote: Literal["for", "against"],
        reason: str = "",
    ) -> None:
        """Record an agent's vote on a proposal."""
        data = self._load()
        for p in data["proposals"]:
            if p["id"] == proposal_id:
                if vote == "for":
                    p["votes_for"] = p.get("votes_for", 0) + 1
                else:
                    p["votes_against"] = p.get("votes_against", 0) + 1
                p.setdefault("vote_details", []).append({
                    "agent": agent,
                    "vote": vote,
                    "reason": reason,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                self._save(data)
                return

    def get_session_digest(self) -> str:
        """Generate a human-readable digest for session start."""
        pending = self.get_pending()
        escalations = self.get_escalations()

        if not pending and not escalations:
            return "Swarm inbox: no pending proposals."

        lines = []
        if escalations:
            lines.append(f"**{len(escalations)} ESCALATION(s) for CEO:**")
            for e in escalations[:3]:
                lines.append(f"  [{e['severity'].upper()}] {e['title']} (by {e['agent']}, ID: {e['id']})")

        non_esc = [p for p in pending if not p.get("escalate_to_ceo")]
        if non_esc:
            lines.append(f"\n**{len(non_esc)} pending proposal(s):**")
            for p in non_esc[:5]:
                votes = f"+{p.get('votes_for', 0)}/-{p.get('votes_against', 0)}"
                lines.append(f"  [{p['severity'].upper()}] {p['title']} ({votes} votes, ID: {p['id']})")

        return "\n".join(lines)

    def cleanup_stale(self, days: int = 30) -> int:
        """Auto-dismiss proposals that have been pending longer than N days.

        Prevents CEO cognitive overload from an ever-growing inbox of
        proposals that were never acted on. Returns count of dismissed proposals.
        """
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        data = self._load()
        count = 0
        for p in data["proposals"]:
            if p["status"] == "pending":
                try:
                    created = datetime.fromisoformat(p["timestamp"])
                    # Make timezone-aware if naive (legacy records)
                    if created.tzinfo is None:
                        created = created.replace(tzinfo=timezone.utc)
                    if created < cutoff:
                        p["status"] = ProposalStatus.DISMISSED.value
                        p["ceo_decision"] = f"Auto-dismissed: pending > {days} days"
                        p["ceo_decision_at"] = datetime.now(timezone.utc).isoformat()
                        count += 1
                except (ValueError, KeyError):
                    pass
        if count:
            self._save(data)
        return count

    def get_stats(self) -> dict:
        """Get inbox statistics."""
        data = self._load()
        all_proposals = data["proposals"]
        return {
            "total": len(all_proposals),
            "pending": len([p for p in all_proposals if p["status"] == "pending"]),
            "acted": len([p for p in all_proposals if p["status"] == "acted"]),
            "dismissed": len([p for p in all_proposals if p["status"] == "dismissed"]),
            "deferred": len([p for p in all_proposals if p["status"] == "deferred"]),
            "escalations": len([p for p in all_proposals if p.get("escalate_to_ceo")]),
        }
