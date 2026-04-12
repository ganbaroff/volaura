#!/usr/bin/env python3
"""Report Generator — Sprint 6: Social Delivery Pipeline.

Produces structured batch-close reports from swarm run results.
Replaces ad-hoc print statements with a rich, consistent format.

Three outputs per report:
  1. ceo-inbox.md update    → structured markdown (replaces plain log)
  2. Telegram message       → formatted with sections + emoji (Markdown)
  3. Stdout summary         → for GitHub Actions logs

Report structure:
  ## SWARM RUN — {date}
  **Status:** {N proposals} | {M escalations} | {K convergent}
  **Groundedness:** {X%} of file references verified
  ### HIGH/CRITICAL Items
  - [agent] Title (quality: N/5)
  ### Predicted Next Actions
  1. [reason] → action (~Xh)
  ### Skill Evolution
  - N improvements applied, M kept after A/B test

Usage:
    from swarm.report_generator import generate_batch_report, format_for_telegram

    report = generate_batch_report(
        proposals=proposals,
        groundedness_score=0.97,
        predictions=suggestions,
        skill_evolution_results=[],
    )
    telegram_msg = format_for_telegram(report)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

project_root = Path(__file__).parent.parent.parent
CEO_INBOX = project_root / "memory" / "swarm" / "ceo-inbox.md"


# ── Data types ────────────────────────────────────────────────────────────────

@dataclass
class BatchReport:
    """Structured report from one autonomous swarm run."""
    timestamp: str
    mode: str
    total_proposals: int
    escalations: int
    convergent: int
    groundedness_score: float         # 0.0 – 1.0
    ungrounded_count: int
    high_critical: list[dict]         # proposals with severity in (high, critical)
    predictions: list[Any]            # Suggestion objects from suggestion_engine
    skill_evolution: list[dict]       # {skill, improvement, kept, delta}
    model_recommendations: list[str]  # next sprint model suggestions
    agent_scores: dict[str, float]    # {agent_name: judge_score}

    @property
    def health_indicator(self) -> str:
        """Traffic light based on escalations + groundedness."""
        if self.escalations > 2 or self.groundedness_score < 0.7:
            return "RED"
        if self.escalations > 0 or self.groundedness_score < 0.9:
            return "YELLOW"
        return "GREEN"

    @property
    def health_emoji(self) -> str:
        return {"GREEN": "[GREEN]", "YELLOW": "[YELLOW]", "RED": "[RED]"}[self.health_indicator]


# ── Builder ───────────────────────────────────────────────────────────────────

def generate_batch_report(
    proposals: list[Any],           # Proposal objects from autonomous_run.py
    groundedness_score: float = 1.0,
    ungrounded_count: int = 0,
    predictions: list[Any] | None = None,
    skill_evolution_results: list[dict] | None = None,
    mode: str = "daily-ideation",
) -> BatchReport:
    """Build a BatchReport from raw swarm run data.

    Args:
        proposals: List of Proposal objects (with .severity, .title, .agent, etc.)
        groundedness_score: From proposal_verifier (0.0–1.0)
        ungrounded_count: Number of proposals tagged [UNGROUNDED]
        predictions: Suggestion objects from suggestion_engine
        skill_evolution_results: List of {skill, improvement, kept, delta}
        mode: Swarm run mode

    Returns:
        BatchReport
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    # Gather HIGH/CRITICAL proposals
    high_critical = []
    agent_scores: dict[str, list[float]] = {}
    escalations = 0
    convergent = 0

    for p in proposals:
        sev = getattr(p, "severity", None)
        sev_val = sev.value if hasattr(sev, "value") else str(sev)

        if sev_val in ("critical", "high") or getattr(p, "escalate_to_ceo", False):
            high_critical.append({
                "title": getattr(p, "title", ""),
                "agent": getattr(p, "agent", ""),
                "severity": sev_val,
                "judge_score": getattr(p, "judge_score", None),
                "convergent": getattr(p, "convergent", False),
                "content_preview": str(getattr(p, "content", ""))[:200],
            })

        if getattr(p, "escalate_to_ceo", False):
            escalations += 1
        if getattr(p, "convergent", False):
            convergent += 1

        # Track agent scores
        agent = getattr(p, "agent", "unknown")
        score = getattr(p, "judge_score", None)
        if score is not None:
            agent_scores.setdefault(agent, []).append(float(score))

    avg_agent_scores = {
        agent: round(sum(scores) / len(scores), 2)
        for agent, scores in agent_scores.items()
    }

    return BatchReport(
        timestamp=timestamp,
        mode=mode,
        total_proposals=len(proposals),
        escalations=escalations,
        convergent=convergent,
        groundedness_score=groundedness_score,
        ungrounded_count=ungrounded_count,
        high_critical=high_critical,
        predictions=predictions or [],
        skill_evolution=skill_evolution_results or [],
        model_recommendations=[],
        agent_scores=avg_agent_scores,
    )


# ── Formatters ─────────────────────────────────────────────────────────────────

def format_for_markdown(report: BatchReport) -> str:
    """Format report as markdown for ceo-inbox.md."""
    ts = report.timestamp[:16].replace("T", " ")
    lines = [
        f"## SWARM RUN — {ts} UTC ({report.mode})",
        "",
        f"**Health:** {report.health_indicator} | "
        f"**Proposals:** {report.total_proposals} | "
        f"**Escalations:** {report.escalations} | "
        f"**Convergent:** {report.convergent}",
        f"**Groundedness:** {report.groundedness_score:.0%} "
        f"({report.ungrounded_count} ungrounded tagged)",
        "",
    ]

    # HIGH/CRITICAL items
    if report.high_critical:
        lines.append("### Action Required")
        lines.append("")
        for item in report.high_critical[:5]:
            score_tag = f" [quality: {item['judge_score']}/5]" if item["judge_score"] is not None else ""
            conv_tag = " [CONVERGENT]" if item["convergent"] else ""
            sev_tag = f"[{item['severity'].upper()}]"
            lines.append(f"- {sev_tag} **{item['title'][:70]}**{conv_tag}{score_tag}")
            lines.append(f"  _{item['agent']}_ — {item['content_preview'][:120]}")
        lines.append("")

    # Predictions
    if report.predictions:
        lines.append("### Predicted Next Actions")
        lines.append("")
        for i, s in enumerate(report.predictions[:3], 1):
            priority = getattr(s, "priority", "medium")
            title = getattr(s, "title", str(s))
            hours = getattr(s, "estimated_hours", 2.0)
            reason = getattr(s, "trigger_reason", "")
            lines.append(f"{i}. **{title}** (~{hours:.1f}h) [{priority.upper()}]")
            if reason:
                lines.append(f"   _Trigger: {reason}_")
        lines.append("")

    # Skill evolution
    if report.skill_evolution:
        kept = [r for r in report.skill_evolution if r.get("kept")]
        lines.append(f"### Skill Evolution")
        lines.append(f"{len(report.skill_evolution)} improvements tested, {len(kept)} kept after A/B test.")
        lines.append("")

    # Agent scores
    if report.agent_scores:
        lines.append("### Agent Quality Scores (avg judge score)")
        for agent, score in sorted(report.agent_scores.items(), key=lambda x: -x[1]):
            lines.append(f"- {agent}: {score:.1f}/5")
        lines.append("")

    lines += ["---", ""]
    return "\n".join(lines)


def format_for_telegram(report: BatchReport, max_chars: int = 1000) -> str:
    """Format report as Telegram Markdown message.

    Telegram limitations:
      - 4096 chars max per message
      - Markdown: *bold*, _italic_, `code`, [link](url)
      - No nested bold/italic
    """
    ts = report.timestamp[:10]
    health_label = {"GREEN": "OK", "YELLOW": "ATTENTION", "RED": "ALERT"}[report.health_indicator]

    lines = [
        f"*Swarm Run {ts}* | {health_label}",
        f"Mode: {report.mode}",
        f"Proposals: {report.total_proposals} | Escalations: {report.escalations} | "
        f"Convergent: {report.convergent}",
        f"Groundedness: {report.groundedness_score:.0%}",
        "",
    ]

    if report.high_critical:
        lines.append("*Action Required:*")
        for item in report.high_critical[:3]:
            sev = item["severity"].upper()
            lines.append(f"[{sev}] {item['title'][:60]}")
        lines.append("")

    if report.predictions:
        lines.append("*Predicted Next:*")
        for i, s in enumerate(report.predictions[:2], 1):
            title = getattr(s, "title", str(s))
            hours = getattr(s, "estimated_hours", 2.0)
            lines.append(f"{i}. {title[:55]} (~{hours:.0f}h)")
        lines.append("")

    if report.convergent > 0:
        lines.append(f"*{report.convergent} CONVERGENT ideas* (independently reached by 2+ agents — highest signal)")

    msg = "\n".join(lines)
    if len(msg) > max_chars:
        msg = msg[:max_chars - 3] + "..."
    return msg


def format_for_stdout(report: BatchReport) -> str:
    """Format compact summary for GitHub Actions stdout."""
    lines = [
        "=" * 60,
        f"SWARM AUTONOMOUS RUN — {report.mode}",
        "=" * 60,
        f"Health:      {report.health_indicator}",
        f"Proposals:   {report.total_proposals}",
        f"Escalations: {report.escalations}",
        f"Convergent:  {report.convergent}",
        f"Grounded:    {report.groundedness_score:.0%} ({report.ungrounded_count} ungrounded)",
        "",
    ]

    for item in report.high_critical[:5]:
        sev = {"critical": "[CRIT]", "high": "[HIGH]"}.get(item["severity"], "[????]")
        lines.append(f"  {sev} {item['title'][:65]}")

    if report.predictions:
        lines.append("")
        lines.append("Predicted next:")
        for s in report.predictions[:2]:
            lines.append(f"  -> {getattr(s, 'title', str(s))[:60]}")

    lines.append("=" * 60)
    return "\n".join(lines)


# ── CEO inbox writer ──────────────────────────────────────────────────────────

def write_to_ceo_inbox(
    report: BatchReport,
    inbox_path: Path | None = None,
    max_entries: int = 20,
) -> None:
    """Write report to ceo-inbox.md. Trims to max_entries to prevent bloat.

    Args:
        report: BatchReport to write
        inbox_path: Override path (default: memory/swarm/ceo-inbox.md)
        max_entries: Maximum number of run sections to keep
    """
    path = inbox_path or CEO_INBOX
    path.parent.mkdir(parents=True, exist_ok=True)

    md = format_for_markdown(report)

    if not path.exists():
        header = "# CEO Inbox — Swarm Reports\n\n_Auto-generated. Most recent at top._\n\n"
        path.write_text(header + md, encoding="utf-8")
        return

    existing = path.read_text(encoding="utf-8")

    # Count existing run sections
    run_count = existing.count("## SWARM RUN —")
    if run_count >= max_entries:
        # Trim oldest entry (last occurrence of "## SWARM RUN —")
        last_idx = existing.rfind("## SWARM RUN —")
        if last_idx > 0:
            existing = existing[:last_idx]

    # Prepend new report (most recent at top) after header
    header_end = existing.find("## SWARM RUN —")
    if header_end == -1:
        path.write_text(existing + "\n" + md, encoding="utf-8")
    else:
        path.write_text(existing[:header_end] + md + "\n" + existing[header_end:], encoding="utf-8")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Demo: generate a mock report
    class MockProposal:
        def __init__(self, title, sev, agent, escalate=False, convergent=False, judge_score=None, content=""):
            self.title = title
            self.severity = type("S", (), {"value": sev})()
            self.agent = agent
            self.escalate_to_ceo = escalate
            self.convergent = convergent
            self.judge_score = judge_score
            self.content = content

    mock_proposals = [
        MockProposal("Add WebSocket support for ANUS integration", "high", "Product Strategist",
                     convergent=True, judge_score=4),
        MockProposal("Fix rate limiting on /answer endpoint", "high", "Security Auditor",
                     judge_score=5, content="The /answer endpoint has no per-user rate limit..."),
        MockProposal("Optimize discovery query", "medium", "Scaling Engineer", judge_score=3),
    ]

    report = generate_batch_report(
        proposals=mock_proposals,
        groundedness_score=0.967,
        ungrounded_count=1,
        mode="daily-ideation",
    )

    print("=== STDOUT FORMAT ===")
    print(format_for_stdout(report))
    print()
    print("=== TELEGRAM FORMAT ===")
    print(format_for_telegram(report))
    print()
    print(f"Health: {report.health_indicator}")
