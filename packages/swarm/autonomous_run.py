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

    # Distilled agent knowledge (neocortex — synthesized from full feedback history)
    distilled_file = project_root / "memory" / "swarm" / "agent-feedback-distilled.md"
    if distilled_file.exists():
        with open(distilled_file, "r", encoding="utf-8") as f:
            content = f.read()
        state_parts.append("## DISTILLED AGENT KNOWLEDGE (hard rules + open findings)\n" + content)
    else:
        feedback_log = project_root / "memory" / "swarm" / "agent-feedback-log.md"
        if feedback_log.exists():
            with open(feedback_log, "r", encoding="utf-8") as f:
                lines = f.readlines()[-60:]
            state_parts.append("## RECENT AGENT FEEDBACK (raw)\n" + "".join(lines))

    # ── Swarm Freedom v2.0: Full visibility ──────────────────────────────────
    # Agents see EVERYTHING. CEO mandate: "должен быть доступ у них ко всему"

    # Skill evolution status (what needs improving)
    evolution_log = project_root / "memory" / "swarm" / "skill-evolution-log.md"
    if evolution_log.exists():
        with open(evolution_log, "r", encoding="utf-8") as f:
            state_parts.append("## SKILL EVOLUTION STATUS\n" + f.read()[:2000])

    # Product skills summary (what skills exist)
    skills_dir = project_root / "memory" / "swarm" / "skills"
    if skills_dir.exists():
        skill_names = [f.stem for f in sorted(skills_dir.glob("*.md"))]
        state_parts.append("## AVAILABLE SKILLS\n" + ", ".join(skill_names))

    # IDEAS backlog (what's been proposed but not built)
    ideas_file = project_root / "docs" / "IDEAS-BACKLOG.md"
    if ideas_file.exists():
        with open(ideas_file, "r", encoding="utf-8") as f:
            # Extract just idea titles
            lines = f.readlines()
            idea_titles = [l.strip() for l in lines if l.startswith("## Idea")]
        if idea_titles:
            state_parts.append("## IDEAS BACKLOG\n" + "\n".join(f"- {t}" for t in idea_titles))

    # Swarm freedom architecture (what agents should become)
    freedom_file = project_root / "memory" / "swarm" / "swarm-freedom-architecture.md"
    if freedom_file.exists():
        with open(freedom_file, "r", encoding="utf-8") as f:
            content = f.read()
        # Just the first section — what agents need
        state_parts.append("## SWARM FREEDOM ARCHITECTURE (your future capabilities)\n" + content[:3000])

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
- Velocity: 7 days → 51 API routes, 512 tests, full assessment engine, AI video pipeline, swarm with memory
- No deadlines. Goal = world-class professional platform (v0Laura).
- ARCHITECTURE SHIFT (Session 51): 1 platform + skill library. NOT 5 separate apps.
  - Life Simulator = feed-curator skill (NOT a game)
  - MindShift = behavior-pattern-analyzer skill (NOT a separate app)
  - BrandedBy = ai-twin-responder skill (NOT a separate platform)
  - ZEUS = assessment-generator skill (NOT a separate engine)
  - All skills in memory/swarm/skills/
- Do NOT propose features for separate apps. Propose skill improvements or new skills.
- Budget: $50/mo total.
- CEO (Yusif): vision leader, not technician. Only handles strategic decisions.
- CTO (Claude): handles all operational decisions with team.
- Swarm agents have brain-inspired memory: hippocampus (raw log) → sleep daemon → neocortex (distilled rules).

SWARM FREEDOM (Session 51 CEO mandate):
- You have FULL visibility into the project. Read everything provided.
- You CAN and SHOULD critique CTO decisions if you see problems.
- You CAN and SHOULD critique CEO decisions if data suggests they're wrong.
- You CAN propose improvements to skills, architecture, process — anything.
- You CAN disagree with other agents. Disagreement = valuable signal.
- You CAN propose research topics for NotebookLM or web search.
- Temperature 1.0 = be completely honest. No corporate politeness. Raw truth.
- If you think something is stupid, say it's stupid and explain why.
- Convergent ideas (same idea from multiple agents independently) = HIGHEST signal."""

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
                    temperature=1.0,  # Session 51: CEO mandated full honesty. 1.0 > 0.7 for strategic decisions.
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

    # Convergence detection: post-hoc content similarity (NOT real-time to avoid anchoring bias).
    # Two proposals are convergent if their title+content jaccard word overlap > threshold.
    # This finds ideas that emerged INDEPENDENTLY from agents with different lenses — high signal.
    CONVERGENCE_THRESHOLD = 0.35

    def _word_overlap(a: str, b: str) -> float:
        wa = set(a.lower().split())
        wb = set(b.lower().split())
        if not wa or not wb:
            return 0.0
        return len(wa & wb) / max(len(wa | wb), 1)

    convergent_ids: set[int] = set()
    for i, p1 in enumerate(proposals):
        text1 = f"{p1.title} {p1.content}"
        for j, p2 in enumerate(proposals):
            if i >= j:
                continue
            text2 = f"{p2.title} {p2.content}"
            if _word_overlap(text1, text2) >= CONVERGENCE_THRESHOLD:
                convergent_ids.add(i)
                convergent_ids.add(j)

    for i, proposal in enumerate(proposals):
        if i in convergent_ids:
            proposal.convergent = True
            proposal.votes_for = 2  # convergent = at least 2 independent votes
        else:
            proposal.votes_for = 1
        proposal.votes_against = len(proposals) - proposal.votes_for

    convergent_count = len(convergent_ids)
    if convergent_count:
        logger.info(f"Convergence detected: {convergent_count} proposals share overlapping themes — HIGH SIGNAL")

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
    convergent_total = sum(1 for p in proposals if p.convergent)
    logger.info(
        f"Autonomous run complete: {len(proposals)} proposals stored, "
        f"{sum(1 for p in proposals if p.escalate_to_ceo)} escalations, "
        f"{convergent_total} convergent (high signal)"
    )

    return proposals


async def send_telegram_notifications(proposals: list[Proposal]) -> None:
    """Send HIGH/CRITICAL proposals to Telegram via MindShift bot."""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CEO_CHAT_ID", "")

    if not bot_token or not chat_id:
        logger.info("Telegram not configured (TELEGRAM_BOT_TOKEN / TELEGRAM_CEO_CHAT_ID missing)")
        return

    # Send: HIGH/CRITICAL + any convergent proposals (independent emergence = high signal)
    high_proposals = [
        p for p in proposals
        if p.severity in (Severity.CRITICAL, Severity.HIGH) or p.escalate_to_ceo or p.convergent
    ]

    if not high_proposals:
        logger.info("No HIGH/CRITICAL/convergent proposals to send to Telegram")
        return

    try:
        from telegram import Bot
        bot = Bot(token=bot_token)

        for p in high_proposals:
            if p.convergent:
                emoji = "🎯"  # convergent = multiple agents independently reached same idea
            elif p.severity == Severity.CRITICAL:
                emoji = "🔴"
            else:
                emoji = "🟠"
            convergent_tag = " [CONVERGENT — emerged independently]" if p.convergent else ""
            escalate_tag = " [ESCALATE TO CEO]" if p.escalate_to_ceo else ""
            msg = (
                f"{emoji} **Swarm {p.type.value.upper()}**{convergent_tag}{escalate_tag}\n\n"
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
    parser.add_argument("--skip-consolidation", action="store_true",
                        help="Skip memory consolidation (useful for quick runs)")
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

    # ── Memory consolidation (SWS sleep cycle) ─────────────────────────────────
    # Runs after every autonomous session — synthesizes feedback log → distilled rules
    # Agents read the distilled file next run (neocortex), not the raw log (hippocampus)
    if not args.skip_consolidation:
        print("Running memory consolidation (sleep cycle)...")
        try:
            from swarm.memory_consolidation import consolidate
            groq_key = os.environ.get("GROQ_API_KEY", "")
            success = await consolidate(groq_key=groq_key or None)
            if success:
                print("✓ Memory consolidated — agent-feedback-distilled.md updated")
            else:
                print("⚠ Memory consolidation used fallback (LLM unavailable)")
        except Exception as e:
            logger.error(f"Memory consolidation failed: {e}")
            print(f"✗ Memory consolidation failed: {e}")

    # ── Skill evolution (neuroplasticity) ─────────────────────────────────────
    # Scans all product skills → checks quality → suggests improvements
    # Skills that can't improve themselves are dead skills
    if not args.skip_consolidation:
        print("Running skill evolution (neuroplasticity)...")
        try:
            from swarm.skill_evolution import evolve
            groq_key = os.environ.get("GROQ_API_KEY", "")
            summary = await evolve(groq_key=groq_key or None)
            health = summary.get("health", "?")
            print(f"✓ Skill evolution complete — {summary['skills']} skills, health={health}/100")
            if summary.get("issues", 0) > 0:
                print(f"  ⚠ {summary['issues']} issues found — see skill-evolution-log.md")
        except Exception as e:
            logger.error(f"Skill evolution failed: {e}")
            print(f"✗ Skill evolution failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
