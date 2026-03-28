#!/usr/bin/env python3
"""ADAS Meta-Agent Designer — designs new agent roles from failure archives.

Based on ADAS (Automatic Design of Agentic Systems), arXiv:2408.08435, ICLR 2025.
Meta-agent reads the failure archive (agent-feedback-log.md) and the career ladder
(career-ladder.md), then proposes 1 new agent role that would catch what existing
agents missed.

How it fits our swarm:
  - archive = agent-feedback-log.md (what went wrong, by session)
  - success record = career-ladder.md (what patterns got promoted)
  - output = .agent-proposal.md file in memory/swarm/skills/
  - CTO reviews → renames to .md + adds to agent-roster.md to activate

Run: python -m packages.swarm.adas_agent_designer
Runs: weekly via .github/workflows/swarm-adas.yml (Sundays 06:00 UTC)
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger

project_root = Path(__file__).parent.parent.parent
packages_path = str(project_root / "packages")
if packages_path not in sys.path:
    sys.path.insert(0, packages_path)

FEEDBACK_LOG = project_root / "memory" / "swarm" / "agent-feedback-log.md"
CAREER_LADDER = project_root / "memory" / "swarm" / "career-ladder.md"
SKILLS_DIR = project_root / "memory" / "swarm" / "skills"
AGENT_ROSTER = project_root / "memory" / "swarm" / "agent-roster.md"
PROPOSALS_DIR = project_root / "memory" / "swarm" / "skills"


def _read_file_tail(path: Path, chars: int = 3000) -> str:
    """Read the last `chars` characters of a file (most recent entries)."""
    if not path.exists():
        return ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return content[-chars:]
    except OSError:
        return ""


def _existing_agent_names() -> list[str]:
    """Extract existing agent names from agent-roster.md."""
    roster = _read_file_tail(AGENT_ROSTER, chars=5000)
    names = []
    for line in roster.split("\n"):
        if "|" in line and "Agent" in line:
            # Extract first column (agent name) from markdown table
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 2 and parts[1] and not parts[1].startswith("-"):
                names.append(parts[1])
    return names


async def _design_new_agent(
    feedback_summary: str,
    career_summary: str,
    existing_agents: list[str],
    gemini_key: str,
) -> dict | None:
    """Use Gemini to design 1 new agent role that fills a gap in the current team."""
    try:
        from google import genai
        client = genai.Client(api_key=gemini_key)

        prompt = f"""You are an ADAS meta-agent (Automatic Design of Agentic Systems).
Your job: read the failure archive and career ladder of an AI agent swarm, then design
1 new agent role that would catch what existing agents missed.

RECENT AGENT FAILURES (from agent-feedback-log.md):
{feedback_summary}

PROMOTED PATTERNS (from career-ladder.md):
{career_summary}

EXISTING AGENTS:
{chr(10).join(f'- {a}' for a in existing_agents[:15])}

Design 1 new agent role. Output JSON:
{{
    "agent_name": "PascalCase name (e.g. PrivacyAuditAgent)",
    "role_title": "Short title (e.g. Privacy Audit Specialist)",
    "domain": "product|engineering|security|research|ops",
    "trigger": "Exact conditions when this agent activates (2-3 sentences)",
    "specialty": "What unique perspective this agent brings that existing agents miss",
    "prompt_template": "The system prompt for this agent (3-5 sentences, first person)",
    "routing_rule": "When_to_call: [condition] → call [AgentName]",
    "gap_it_fills": "Specific failure pattern in the archive this agent would have caught",
    "expected_improvement": "What metric or outcome improves with this agent present"
}}

Rules:
- Do NOT propose a duplicate of an existing agent
- The gap_it_fills must reference a REAL pattern from the failure archive above
- The agent must have a unique lens (not just 'another reviewer')
- The prompt_template must make the agent adversarial and specific, not generic"""

        resp = await asyncio.wait_for(
            client.aio.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config={"response_mime_type": "application/json"},
            ),
            timeout=30.0,
        )
        raw = resp.text or ""
        return json.loads(raw)

    except Exception as e:
        logger.error(f"ADAS agent design failed: {e}")
        return None


def _write_agent_proposal(design: dict) -> Path:
    """Write the agent design as a .agent-proposal.md file.

    CTO reviews and renames to .md + updates agent-roster.md to activate.
    """
    PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    name = design.get("agent_name", "UnknownAgent")
    safe_name = name.replace("Agent", "").lower().strip()
    filename = f"{safe_name}-agent.agent-proposal.md"
    path = PROPOSALS_DIR / filename

    lines = [
        f"<!-- ADAS PROPOSAL — {now} — requires CTO review to activate -->",
        f"<!-- Gap filled: {design.get('gap_it_fills', '?')} -->",
        "",
        f"# {design.get('role_title', name)}",
        "",
        "## Agent Identity",
        f"- **Name:** `{name}`",
        f"- **Domain:** {design.get('domain', '?')}",
        f"- **Specialty:** {design.get('specialty', '')}",
        "",
        "## Trigger",
        design.get("trigger", ""),
        "",
        "## System Prompt Template",
        "```",
        design.get("prompt_template", ""),
        "```",
        "",
        "## Routing Rule",
        f"`{design.get('routing_rule', '')}`",
        "",
        "## Gap This Fills",
        design.get("gap_it_fills", ""),
        "",
        "## Expected Improvement",
        design.get("expected_improvement", ""),
        "",
        "---",
        "",
        "**To activate:** CTO reviews → renames file to `.md` → adds row to `agent-roster.md`.",
    ]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return path


async def _send_telegram(token: str, chat_id: str, text: str) -> None:
    """Send design summary to CEO via Telegram."""
    try:
        from telegram import Bot
        bot = Bot(token=token)
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
    except Exception as e:
        logger.warning(f"Telegram delivery failed: {e}")


async def run_adas(gemini_key: str | None = None) -> dict:
    """Main ADAS run — design 1 new agent from failure archive.

    Returns summary dict.
    """
    logger.info("ADAS meta-agent designer starting...")

    gemini_key = gemini_key or os.environ.get("GEMINI_API_KEY", "")
    if not gemini_key:
        logger.error("GEMINI_API_KEY not set — cannot run ADAS")
        return {"status": "error", "reason": "no gemini key"}

    feedback = _read_file_tail(FEEDBACK_LOG)
    career = _read_file_tail(CAREER_LADDER)
    existing = _existing_agent_names()

    if not feedback:
        logger.warning("agent-feedback-log.md is empty — no failure archive to read")
        return {"status": "skipped", "reason": "empty feedback log"}

    logger.info(f"Archive: {len(feedback)} chars feedback, {len(career)} chars career, {len(existing)} agents")

    design = await _design_new_agent(feedback, career, existing, gemini_key)
    if not design:
        return {"status": "error", "reason": "LLM design failed"}

    proposal_path = _write_agent_proposal(design)
    logger.success(f"ADAS proposal written: {proposal_path.name}")

    # Optional Telegram notification
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    tg_chat = os.environ.get("TELEGRAM_CEO_CHAT_ID", "")
    if tg_token and tg_chat:
        name = design.get("agent_name", "?")
        role = design.get("role_title", "?")
        gap = design.get("gap_it_fills", "?")[:120]
        msg = (
            f"🤖 *ADAS Weekly Proposal*\n\n"
            f"*New agent:* {name} — {role}\n"
            f"*Gap filled:* {gap}\n\n"
            f"File: `memory/swarm/skills/{proposal_path.name}`\n"
            f"Rename to `.md` + update `agent-roster.md` to activate."
        )
        await _send_telegram(tg_token, tg_chat, msg)

    return {
        "status": "ok",
        "agent_name": design.get("agent_name"),
        "role_title": design.get("role_title"),
        "domain": design.get("domain"),
        "file": str(proposal_path),
        "gap_filled": design.get("gap_it_fills"),
    }


def main() -> None:
    """CLI entry point."""
    from dotenv import load_dotenv
    load_dotenv(project_root / "apps" / "api" / ".env")

    result = asyncio.run(run_adas())
    if result["status"] == "ok":
        print(f"\nADAS proposal: {result['agent_name']} — {result['role_title']}")
        print(f"Gap filled: {result['gap_filled']}")
        print(f"File: {result['file']}")
    else:
        print(f"\nADAS: {result['status']} — {result.get('reason', '')}")


if __name__ == "__main__":
    main()
