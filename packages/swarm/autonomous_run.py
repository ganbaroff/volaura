#!/usr/bin/env python3
"""Autonomous Swarm Run — daily ideation + review + escalation.

Called by GitHub Actions (.github/workflows/swarm-daily.yml) or manually.
Runs 5 agents with diverse perspectives against current project state.
Writes proposals to memory/swarm/proposals.json via InboxProtocol.
Sends HIGH/CRITICAL to Telegram via MindShift bot.

Usage:
    python -m packages.swarm.autonomous_run --mode=daily-ideation
    python -m packages.swarm.autonomous_run --mode=code-review
    python -m packages.swarm.autonomous_run --mode=cto-audit
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

# Ensure packages/ is importable
project_root = Path(__file__).parent.parent.parent
packages_path = str(project_root / "packages")
if packages_path not in sys.path:
    sys.path.insert(0, packages_path)

from dotenv import load_dotenv
load_dotenv(project_root / "apps" / "api" / ".env")

from loguru import logger

from swarm.inbox_protocol import (
    InboxProtocol,
    Proposal,
    ProposalStatus,
    ProposalType,
    Severity,
)

# ──────────────────────────────────────────────────────────────
# Agent perspectives — each gets a unique lens
# ──────────────────────────────────────────────────────────────

PERSPECTIVES = [
    {
        "name": "Scaling Engineer",
        "lens": "What breaks at 10x users? What bottleneck exists that nobody sees? Focus on database, API latency, and infrastructure limits.",
    },
    {
        "name": "Security Auditor",
        "lens": "What vulnerability exists right now? Check: RLS gaps, unvalidated inputs, missing rate limits, exposed secrets, OWASP top 10.",
    },
    {
        "name": "Product Strategist",
        "lens": "What feature or improvement would have the biggest impact on user acquisition and retention? Think about the AURA score, assessment UX, org admin experience.",
    },
    {
        "name": "Code Quality Engineer",
        "lens": "What technical debt is accumulating? What pattern violations exist? What would make the codebase more maintainable?",
    },
    {
        "name": "CTO Watchdog",
        "lens": "Is the CTO (Claude) following process? Check: are plans going through agents? Are memory files updated? Is protocol v4.0 being followed? Flag any process violations. You can escalate directly to CEO.",
    },
]


def _read_project_state(project_root: Path) -> str:
    """Read current project state for agent context."""
    state_parts = []

    # Sprint state
    sprint_file = project_root / "memory" / "context" / "sprint-state.md"
    if sprint_file.exists():
        with open(sprint_file, "r", encoding="utf-8") as f:
            # First 100 lines only
            lines = f.readlines()[:100]
            state_parts.append("## SPRINT STATE\n" + "".join(lines))

    # Recent mistakes
    mistakes_file = project_root / "memory" / "context" / "mistakes.md"
    if mistakes_file.exists():
        with open(mistakes_file, "r", encoding="utf-8") as f:
            lines = f.readlines()[-50:]  # Last 50 lines = most recent
            state_parts.append("## RECENT MISTAKES\n" + "".join(lines))

    # Recent decisions
    decisions_file = project_root / "docs" / "DECISIONS.md"
    if decisions_file.exists():
        with open(decisions_file, "r", encoding="utf-8") as f:
            lines = f.readlines()[-30:]
            state_parts.append("## RECENT DECISIONS\n" + "".join(lines))

    # Previous proposals (so agents don't repeat)
    inbox = InboxProtocol(project_root)
    pending = inbox.get_pending()
    if pending:
        titles = [p["title"] for p in pending[:10]]
        state_parts.append(
            "## ALREADY PROPOSED (don't repeat)\n" + "\n".join(f"- {t}" for t in titles)
        )

    return "\n\n".join(state_parts) if state_parts else "No project state files found."


def _build_agent_prompt(perspective: dict, project_state: str, mode: str) -> str:
    """Build prompt for a single autonomous agent."""

    team_context = """TEAM CONTEXT:
- Velocity: 72 hours → 31 API endpoints, 27 pages, 158 tests, full deploy
- No deadlines. Goal = quality launch of Volaura.
- Swarm/AI backend = PRODUCT, not tooling.
- Calculate in our speed, not human-developer-hours.
- Budget: $50/mo total.
- CEO (Yusif): vision leader, not technician. Only handles strategic decisions.
- CTO (Claude): handles all operational decisions with team."""

    if mode == "daily-ideation":
        task = """YOUR TASK:
Generate exactly 1 concrete improvement proposal for the Volaura project.
Requirements:
- Must be specific (file names, function names, concrete changes)
- Must include math justification (time to implement, expected impact)
- Must be actionable THIS WEEK (not a future vision)
- If you believe the CTO missed something critical, add [ESCALATE] tag
- If you have a complaint about CTO process, state it directly"""
    elif mode == "code-review":
        task = """YOUR TASK:
Review the current codebase state and find 1 concrete issue.
Requirements:
- Specific file + line/function reference
- Severity: CRITICAL (breaks production), HIGH (security/data), MEDIUM (quality), LOW (nice-to-have)
- If CRITICAL or HIGH → tag [ESCALATE] for CEO visibility"""
    elif mode == "cto-audit":
        task = """YOUR TASK:
Audit the CTO's (Claude's) work process. Check:
1. Are plans going through agent review? (check DECISIONS.md)
2. Are memory files being updated? (check sprint-state.md timestamps)
3. Are mistakes being repeated? (check mistakes.md for patterns)
4. Is protocol v4.0 being followed?
Tag [ESCALATE] if you find process violations."""
    else:
        task = f"YOUR TASK: {mode}"

    return f"""{team_context}

YOUR PERSPECTIVE: {perspective['name']}
YOUR LENS: {perspective['lens']}

{task}

CURRENT PROJECT STATE:
{project_state}

RESPONSE FORMAT (JSON only):
{{
    "title": "one-line summary of your proposal",
    "severity": "critical|high|medium|low",
    "type": "idea|escalation|complaint|code_review|security",
    "content": "full proposal with specific details, file references, math",
    "escalate_to_ceo": true/false,
    "confidence": 0.0-1.0
}}"""


async def _call_agent(
    prompt: str,
    perspective_name: str,
    env: dict[str, str],
) -> dict | None:
    """Call a single LLM agent and parse response."""
    try:
        # Try Groq first (fastest, free)
        groq_key = env.get("GROQ_API_KEY", "")
        if groq_key:
            from groq import AsyncGroq
            client = AsyncGroq(api_key=groq_key)
            resp = await asyncio.wait_for(
                client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=1000,
                    response_format={"type": "json_object"},
                ),
                timeout=15.0,
            )
            raw = resp.choices[0].message.content or ""
        else:
            # Fallback to Gemini
            gemini_key = env.get("GEMINI_API_KEY", "")
            if not gemini_key:
                logger.warning(f"No API keys for agent {perspective_name}")
                return None
            from google import genai
            client = genai.Client(api_key=gemini_key)
            resp = await asyncio.wait_for(
                asyncio.to_thread(
                    client.models.generate_content,
                    model="gemini-2.5-flash",
                    contents=prompt,
                ),
                timeout=20.0,
            )
            raw = resp.text or ""

        # Parse JSON
        import re
        text = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`")
        if text.startswith("{"):
            data = json.loads(text)
            data["agent"] = perspective_name
            return data
        else:
            logger.warning(f"Agent {perspective_name} returned non-JSON: {raw[:100]}")
            return None

    except Exception as e:
        logger.error(f"Agent {perspective_name} failed: {e}")
        return None


async def run_autonomous(mode: str = "daily-ideation") -> list[Proposal]:
    """Run all 5 agents in parallel, collect proposals, vote, store."""
    logger.info(f"Autonomous swarm run starting: mode={mode}")

    env = dict(os.environ)
    project_state = _read_project_state(project_root)
    inbox = InboxProtocol(project_root)

    # Launch all agents in parallel
    tasks = []
    for perspective in PERSPECTIVES:
        prompt = _build_agent_prompt(perspective, project_state, mode)
        tasks.append(_call_agent(prompt, perspective["name"], env))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results into proposals
    proposals: list[Proposal] = []
    raw_results = []

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Agent {PERSPECTIVES[i]['name']} exception: {result}")
            continue
        if result is None:
            continue

        raw_results.append(result)

        try:
            severity_map = {
                "critical": Severity.CRITICAL,
                "high": Severity.HIGH,
                "medium": Severity.MEDIUM,
                "low": Severity.LOW,
            }
            type_map = {
                "idea": ProposalType.IDEA,
                "escalation": ProposalType.ESCALATION,
                "complaint": ProposalType.COMPLAINT,
                "code_review": ProposalType.CODE_REVIEW,
                "security": ProposalType.SECURITY,
            }

            proposal = Proposal(
                agent=result.get("agent", f"agent-{i}"),
                severity=severity_map.get(result.get("severity", "medium"), Severity.MEDIUM),
                type=type_map.get(result.get("type", "idea"), ProposalType.IDEA),
                title=result.get("title", "Untitled proposal"),
                content=result.get("content", ""),
                escalate_to_ceo=result.get("escalate_to_ceo", False),
            )
            proposals.append(proposal)
        except Exception as e:
            logger.warning(f"Failed to create proposal from agent output: {e}")

    # Cross-voting: each agent votes on others' proposals
    # (simplified: if same severity/type pattern → vote for)
    for proposal in proposals:
        supporting = sum(
            1 for r in raw_results
            if r.get("agent") != proposal.agent
            and r.get("severity") == proposal.severity.value
        )
        proposal.votes_for = 1 + supporting  # self + similar severity
        proposal.votes_against = len(raw_results) - proposal.votes_for

    # Store all proposals
    stored_ids = []
    for proposal in proposals:
        pid = inbox.add_proposal(proposal)
        stored_ids.append(pid)
        logger.info(
            f"Stored: [{proposal.severity.value}] {proposal.title} "
            f"(+{proposal.votes_for}/-{proposal.votes_against}, escalate={proposal.escalate_to_ceo})"
        )

    # Summary
    logger.info(
        f"Autonomous run complete: {len(proposals)} proposals stored, "
        f"{sum(1 for p in proposals if p.escalate_to_ceo)} escalations"
    )

    return proposals


async def send_telegram_notifications(proposals: list[Proposal]) -> None:
    """Send HIGH/CRITICAL proposals to Telegram via MindShift bot."""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CEO_CHAT_ID", "")

    if not bot_token or not chat_id:
        logger.info("Telegram not configured (TELEGRAM_BOT_TOKEN / TELEGRAM_CEO_CHAT_ID missing)")
        return

    high_proposals = [
        p for p in proposals
        if p.severity in (Severity.CRITICAL, Severity.HIGH) or p.escalate_to_ceo
    ]

    if not high_proposals:
        logger.info("No HIGH/CRITICAL proposals to send to Telegram")
        return

    try:
        from telegram import Bot
        bot = Bot(token=bot_token)

        for p in high_proposals:
            emoji = "🔴" if p.severity == Severity.CRITICAL else "🟠"
            escalate_tag = " [ESCALATE TO CEO]" if p.escalate_to_ceo else ""
            msg = (
                f"{emoji} **Swarm {p.type.value.upper()}**{escalate_tag}\n\n"
                f"**{p.title}**\n"
                f"Agent: {p.agent}\n"
                f"Votes: +{p.votes_for}/-{p.votes_against}\n\n"
                f"{p.content[:500]}\n\n"
                f"Reply: `act {p.id}` / `dismiss {p.id}` / `defer {p.id}`"
            )
            await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
            logger.info(f"Telegram sent: {p.title}")

    except Exception as e:
        logger.error(f"Telegram send failed: {e}")


async def main():
    parser = argparse.ArgumentParser(description="Autonomous Swarm Run")
    parser.add_argument("--mode", default="daily-ideation",
                        choices=["daily-ideation", "code-review", "cto-audit"])
    args = parser.parse_args()

    proposals = await run_autonomous(args.mode)

    # Send Telegram notifications for HIGH/CRITICAL
    await send_telegram_notifications(proposals)

    # Print summary to stdout (for GitHub Actions logs)
    print(f"\n{'='*60}")
    print(f"SWARM AUTONOMOUS RUN — {args.mode}")
    print(f"{'='*60}")
    print(f"Agents: {len(PERSPECTIVES)}")
    print(f"Proposals: {len(proposals)}")
    print(f"Escalations: {sum(1 for p in proposals if p.escalate_to_ceo)}")
    for p in proposals:
        emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
        print(f"  {emoji.get(p.severity.value, '⚪')} [{p.severity.value}] {p.title}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
