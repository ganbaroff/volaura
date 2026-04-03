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
from swarm.perspective_registry import PerspectiveRegistry

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
    {
        "name": "Risk Manager",
        "lens": "ISO 31000:2018 + COSO ERM. Score every open item by Likelihood×Impact (1-5 each). CRITICAL=20-25, HIGH=12-19, MEDIUM=6-11. Flag: unmitigated CRITICAL risks, missing rollback plans, single points of failure, launch blockers. Output a mini Risk Register entry for each finding.",
    },
    {
        "name": "Readiness Manager",
        "lens": "Google SRE + ITIL v4 + LRR standard. Score platform readiness across 5 dimensions: Functional (0-20), Operational (0-20), Security (0-20), UX (0-20), Rollback (0-20). LRL 1-7. A score <70/100 is a NO-GO for any public launch. Flag any dimension below 12/20 as a launch blocker.",
    },
]


def _route_skills_for_perspective(perspective_name: str, skills_dir: Path) -> list[str]:
    """Match skill files to a perspective by keyword overlap.

    Compares words in perspective_name against skill file stem words
    (hyphen-split). Returns matching skill file stems (without .md).
    Low-cost routing — no LLM call required.
    """
    if not skills_dir.exists():
        return []
    perspective_words = set(perspective_name.lower().split())
    matched = []
    for skill_file in sorted(skills_dir.glob("*.md")):
        skill_words = set(skill_file.stem.lower().replace("-", " ").split())
        if perspective_words & skill_words:
            matched.append(skill_file.stem)
    return matched


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

    # ── SESSION-DIFFS.jsonl — what actually changed recently ─────────────────
    # This closes the "42% already done" gap: agents see git-level changes, not
    # just static memory files. Updated on every push to main via session-end.yml.
    session_diffs_file = project_root / "memory" / "swarm" / "SESSION-DIFFS.jsonl"
    if session_diffs_file.exists():
        with open(session_diffs_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        # Read last 3 sessions (most recent first)
        recent_entries = []
        for raw_line in reversed(lines[-3:]):
            try:
                import json as _json
                entry = _json.loads(raw_line.strip())
                summary = (
                    f"[{entry.get('timestamp', '?')[:16]}] "
                    f"{entry.get('sprint_headline', '?')} | "
                    f"files changed: {entry.get('files_changed_count', '?')} | "
                    f"migrations: {entry.get('new_migrations', [])} | "
                    f"routes: {entry.get('new_routes', [])}"
                )
                recent_entries.append(summary)
                # Include diff_summary from most recent entry
                if not recent_entries[1:] and entry.get("diff_summary"):
                    recent_entries.append("DIFF:\n" + entry["diff_summary"][:1500])
            except Exception:
                pass
        if recent_entries:
            state_parts.append(
                "## RECENTLY SHIPPED (read this FIRST — prevents re-proposing done work)\n"
                + "\n".join(recent_entries)
            )

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
- If you have a complaint about CTO process, state it directly

STRATEGIC CONTEXT FOR THIS RUN (CEO directive):
The CEO wants to integrate ANUS (Autonomous Networked Utility System — an open-source
autonomous AI coding agent CLI, github.com/anus-dev/anus) as a PLATFORM FEATURE in Volaura/MindShift.
Vision: users assign a coding task via the platform → an ANUS agent runs on their local PC →
codes autonomously → reports back. Human presence verified via camera (SIMA-style, client-side
face detection) every 20 minutes to maintain legal oversight.

This is a new `agent-task-runner` skill in the Volaura skill library.
Key questions the CEO wants the team to resolve:
1. What is the minimum viable architecture for task dispatch (Supabase polling vs WebSocket vs other)?
2. How to sandbox ANUS so it can't read .env / system files?
3. What presence-check implementation is legally clean across AZ/EU/US?
4. What does the `agent_tasks` Supabase schema look like?
5. What is the biggest risk nobody is talking about?

Apply your specific lens to ONE of these questions and produce a concrete proposal."""
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
    elif mode == "weekly-audit":
        task = """YOUR TASK:
Weekly systemic audit. Look for PATTERNS, not individual issues.
1. What category of problems repeats most? (check mistakes.md CLASS frequencies)
2. What DORA metric is worst right now? (check quality-metrics.md)
3. What is the one systemic change that would prevent 50%+ of recurring issues?
4. Are any skill files becoming stale (not updated in 30+ days)?
5. Is the swarm itself working? (check if proposals are being acted on or ignored)

Output a SYSTEMIC recommendation — not "fix this file", but "change this process".
The CTO should implement this in the next batch.
Tag [ESCALATE] if a pattern is severe enough to require CEO awareness."""
    elif mode == "monthly-review":
        task = """YOUR TASK:
Monthly strategic review. Think at the product/business level.
1. What is VOLAURA's biggest strategic risk for the next 30 days?
2. Which feature produced the most real user/business value this month?
3. What should be REMOVED from the roadmap (over-engineered, unused, 0 users)?
4. Are we on track for first revenue? What is the single blocking item?
5. What would make the CEO's life 10x easier without requiring more of his time?

This report goes directly to CEO. Be strategic, not tactical.
Tag [ESCALATE] for any item requiring CEO strategic decision."""
    elif mode == "post-deploy":
        task = """YOUR TASK:
A new deployment just landed. Rapid security and health assessment.
You have 3 minutes. Focus only on CRITICAL and HIGH severity issues.

1. Did any new API endpoints land without security review? (check SESSION-DIFFS.jsonl for new routes)
2. Did any migration run? If yes, does it have RLS policies?
3. Are there new endpoints without rate limiting?
4. Did schema change without openapi.json update? (check pre-commit hook warning pattern)
5. Any CRITICAL risk that should block traffic right now?

Output a Go/No-Go verdict with specific blockers if No-Go.
Tag [ESCALATE] if this deploy should be rolled back immediately."""
    else:
        task = f"YOUR TASK: {mode}"

    weight_line = f"\nYOUR CALIBRATION: {perspective.get('weight_context', '')}" if perspective.get('weight_context') else ""
    skills_line = f"\nROUTED SKILLS: {', '.join(perspective.get('routed_skills', []))}" if perspective.get('routed_skills') else ""
    bound_files_line = f"\n\n{perspective.get('bound_files', '')}" if perspective.get('bound_files') else ""

    return f"""{team_context}

YOUR PERSPECTIVE: {perspective['name']}
YOUR LENS: {perspective['lens']}{weight_line}{skills_line}{bound_files_line}

{task}

CURRENT PROJECT STATE:
{project_state}

RESPONSE FORMAT (JSON only):
{{
    "title": "one-line summary of your proposal",
    "severity": "critical|high|medium|low",
    "type": "idea|escalation|complaint|code_review|security",
    "content": "IMPORTANT: this must be a plain STRING (not an object). Full proposal with specific details, file references, math — written as prose text.",
    "escalate_to_ceo": true,
    "confidence": 0.0-1.0
}}

CRITICAL: "content" field MUST be a string, NOT a JSON object or nested dict. Write it as plain text."""


async def _call_agent(
    prompt: str,
    perspective_name: str,
    env: dict[str, str],
) -> dict | None:
    """Call a single LLM agent and parse response.

    Model routing — NVIDIA NIM primary (added 2026-04-02):
      Heavy reasoning agents → nvidia/llama-3.1-nemotron-ultra-253b-v1
      Speed agents           → meta/llama-3.3-70b-instruct
      Fallback 1             → Groq llama-3.3-70b-versatile
      Fallback 2             → Gemini 2.5 Flash

    Asymmetric judging preserved: _judge_proposal() always uses Gemini
    regardless of generator — avoids self-favor inflation (Zheng et al. 2023).
    """
    import re

    # Agents that benefit most from deep reasoning
    _HEAVY = {"CTO Watchdog", "Risk Manager", "Readiness Manager"}
    _NVIDIA_BASE = "https://integrate.api.nvidia.com/v1"

    raw = ""

    # ── Primary: NVIDIA NIM ───────────────────────────────────────────────────
    nvidia_key = env.get("NVIDIA_API_KEY", "")
    if nvidia_key and not raw:
        try:
            from openai import AsyncOpenAI
            model = (
                "nvidia/llama-3.1-nemotron-ultra-253b-v1"
                if perspective_name in _HEAVY
                else "meta/llama-3.3-70b-instruct"
            )
            resp = await asyncio.wait_for(
                AsyncOpenAI(base_url=_NVIDIA_BASE, api_key=nvidia_key)
                .chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=1.0,
                    max_tokens=1000,
                ),
                timeout=45.0,  # heavy models need more time
            )
            raw = resp.choices[0].message.content or ""
            logger.debug(f"Agent {perspective_name} → NVIDIA {model.split('/')[-1]}")
        except Exception as e:
            logger.warning(f"NVIDIA NIM failed for {perspective_name}, falling back: {e}")

    # ── Fallback 1: Groq ──────────────────────────────────────────────────────
    groq_key = env.get("GROQ_API_KEY", "")
    if groq_key and not raw:
        try:
            from groq import AsyncGroq
            resp = await asyncio.wait_for(
                AsyncGroq(api_key=groq_key).chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=1.0,
                    max_tokens=1000,
                    response_format={"type": "json_object"},
                ),
                timeout=15.0,
            )
            raw = resp.choices[0].message.content or ""
            logger.debug(f"Agent {perspective_name} → Groq fallback")
        except Exception as e:
            logger.warning(f"Groq fallback failed for {perspective_name}: {e}")

    # ── Fallback 2: Gemini ────────────────────────────────────────────────────
    gemini_key = env.get("GEMINI_API_KEY", "")
    if gemini_key and not raw:
        try:
            from google import genai
            resp = await asyncio.wait_for(
                asyncio.to_thread(
                    genai.Client(api_key=gemini_key).models.generate_content,
                    model="gemini-2.5-flash",
                    contents=prompt,
                ),
                timeout=20.0,
            )
            raw = resp.text or ""
            logger.debug(f"Agent {perspective_name} → Gemini fallback")
        except Exception as e:
            logger.error(f"All LLM providers failed for {perspective_name}: {e}")

    if not raw:
        logger.warning(f"No API keys or all providers failed for agent {perspective_name}")
        return None

    # ── Parse JSON ────────────────────────────────────────────────────────────
    try:
        text = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`")
        # NVIDIA models sometimes wrap JSON in prose — extract first {...} block
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            text = match.group(0)
        data = json.loads(text)
        data["agent"] = perspective_name
        return data
    except Exception:
        logger.warning(f"Agent {perspective_name} returned non-JSON: {raw[:150]}")
        return None


async def _judge_proposal(
    proposal: Proposal,
    env: dict[str, str],
) -> None:
    """Cross-model judge: score a proposal on 5 criteria using a DIFFERENT model family.

    Asymmetric judging (MT-Bench / Zheng et al. 2023): if Groq generated → Gemini judges.
    Avoids 10-25% self-favor inflation measured in LLM-as-judge research.

    Scoring: binary pass/fail per criterion (not 1-5 scales which produce inaction).
    - Specificity: references actual files, functions, or endpoints (not vague advice)
    - Evidence: claims backed by observable facts from project state (not assumptions)
    - Actionability: CTO can act on this in <2h without clarification
    - Novelty: not already proposed, implemented, or documented
    - Impact: clear outcome metric defined (not "would be nice")

    Score = number of criteria passed (0–5). Stored in proposal for ranking.
    Does NOT block proposal storage — judge failure is graceful (score=None).
    """
    gemini_key = env.get("GEMINI_API_KEY", "")
    if not gemini_key:
        return  # Judge unavailable — don't block the run

    judge_prompt = f"""You are a proposal quality judge for an AI swarm system.
Score this proposal against 5 criteria. Reply with JSON only.

PROPOSAL:
Agent: {proposal.agent}
Severity: {proposal.severity.value}
Title: {proposal.title}
Content: {proposal.content[:800]}

SCORING CRITERIA (binary pass=true/fail=false per criterion):
1. specificity — References actual files, function names, or endpoints (NOT vague advice like "improve the code")
2. evidence — Claims backed by observable facts from the project (NOT pure speculation)
3. actionability — CTO can implement this in <2 hours without asking for clarification
4. novelty — This is a new finding, not something already documented or recently proposed
5. impact — A clear measurable outcome or metric is defined (NOT just "would be nice")

JSON format:
{{"specificity": true/false, "evidence": true/false, "actionability": true/false, "novelty": true/false, "impact": true/false, "reasoning": "1-2 sentences on the lowest-scoring area"}}"""

    try:
        from google import genai
        client = genai.Client(api_key=gemini_key)
        resp = await asyncio.wait_for(
            asyncio.to_thread(
                client.models.generate_content,
                model="gemini-2.0-flash",
                contents=judge_prompt,
                config={"response_mime_type": "application/json"},
            ),
            timeout=15.0,
        )
        raw = resp.text or ""
        data = json.loads(raw)

        criteria = {
            "specificity": bool(data.get("specificity")),
            "evidence": bool(data.get("evidence")),
            "actionability": bool(data.get("actionability")),
            "novelty": bool(data.get("novelty")),
            "impact": bool(data.get("impact")),
        }
        score = sum(1 for v in criteria.values() if v)

        proposal.judge_score = score
        proposal.judge_model = "gemini-2.0-flash"
        proposal.judge_reasoning = data.get("reasoning", "")[:300]
        proposal.judge_criteria = criteria

        logger.info(
            "Judge [{agent}]: {score}/5 — {title}",
            agent=proposal.agent, score=score, title=proposal.title[:60],
        )

    except Exception as e:
        logger.warning(f"Judge failed for '{proposal.title[:50]}': {e}")
        # Graceful — proposal still gets stored, just without a score


async def run_autonomous(mode: str = "daily-ideation") -> list[Proposal]:
    """Run all 5 agents in parallel, collect proposals, vote, store."""
    logger.info(f"Autonomous swarm run starting: mode={mode}")

    env = dict(os.environ)
    project_state = _read_project_state(project_root)
    inbox = InboxProtocol(project_root)
    registry = PerspectiveRegistry(project_root)
    skills_dir = project_root / "memory" / "swarm" / "skills"

    # ── Sprint 4: Pre-bind tasks to files using code index ───────────────────
    # Each perspective has a lens (a task description). Bind that lens to files
    # so agents know WHERE to look before they guess.
    try:
        from swarm.task_binder import bind_task_to_files
        from swarm.code_index import load_index
        _code_index = load_index(project_root)
        logger.info(f"Code index loaded: {_code_index.get('total_files', 0)} files")
    except Exception as e:
        logger.warning(f"Code index unavailable (non-blocking): {e}")
        _code_index = None

    # Launch all agents in parallel (weight context injected per perspective)
    tasks = []
    for perspective in PERSPECTIVES:
        weight_ctx = registry.inject_weight_context(perspective["name"])
        routed_skills = _route_skills_for_perspective(perspective["name"], skills_dir)

        # Bind lens to files (Sprint 4 — Context Intelligence)
        bound_files_section = ""
        if _code_index is not None:
            try:
                bound = bind_task_to_files(perspective["lens"], _code_index, project_root)
                if bound.primary_files:
                    bound_files_section = bound.to_briefing_section()
            except Exception:
                pass  # non-blocking

        enriched_perspective = {
            **perspective,
            "weight_context": weight_ctx,
            "routed_skills": routed_skills,
            "bound_files": bound_files_section,
        }
        prompt = _build_agent_prompt(enriched_perspective, project_state, mode)
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

    # Cross-model judge all proposals in parallel (B7 — Approach 1).
    # Gemini judges Groq-generated proposals (asymmetric — avoids self-favor bias).
    # Failures are graceful — judging never blocks proposal storage.
    judge_tasks = [_judge_proposal(p, env) for p in proposals]
    await asyncio.gather(*judge_tasks, return_exceptions=True)

    judged = sum(1 for p in proposals if p.judge_score is not None)
    if judged:
        avg_score = sum(p.judge_score for p in proposals if p.judge_score is not None) / judged
        logger.info(f"Judge complete: {judged}/{len(proposals)} proposals scored, avg={avg_score:.1f}/5")

    # Update PerspectiveRegistry weights based on judge scores
    for proposal in proposals:
        registry.update(proposal.agent, proposal.judge_score)

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
            judge_tag = f" [Quality: {p.judge_score}/5]" if p.judge_score is not None else ""
            msg = (
                f"{emoji} **Swarm {p.type.value.upper()}**{convergent_tag}{escalate_tag}{judge_tag}\n\n"
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


async def _write_run_log(
    proposals: list[Proposal],
    mode: str,
    duration_ms: int,
    trigger_meta: dict | None = None,
) -> None:
    """Write run summary to agent_run_log Supabase table (ADR-011).

    Non-blocking: if Supabase env vars are missing or write fails, log and continue.
    Uses service role key — never user JWT.
    """
    supabase_url = os.environ.get("SUPABASE_URL", "")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not supabase_url or not service_key:
        logger.debug("Supabase env vars not set — skipping agent_run_log write (non-blocking).")
        return

    from datetime import datetime, timezone
    import uuid
    run_id = f"{mode}-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"

    rows = []
    for p in proposals:
        rows.append({
            "run_id": run_id,
            "agent_id": p.agent,
            "trigger_type": "deploy" if mode == "post-deploy" else "scheduled",
            "trigger_meta": trigger_meta or {},
            "proposal_ids": [str(p.id)] if p.id else [],
            "duration_ms": duration_ms,
            "status": "completed",
        })

    # One summary row if no proposals (e.g. all agents returned None)
    if not rows:
        rows.append({
            "run_id": run_id,
            "agent_id": "swarm",
            "trigger_type": "deploy" if mode == "post-deploy" else "scheduled",
            "trigger_meta": trigger_meta or {},
            "proposal_ids": [],
            "duration_ms": duration_ms,
            "status": "partial",
            "error_message": "No proposals generated this run",
        })

    try:
        from supabase import create_client
        client = create_client(supabase_url, service_key)
        client.table("agent_run_log").insert(rows).execute()
        logger.info(f"agent_run_log: {len(rows)} rows written for run_id={run_id}")
    except Exception as e:
        logger.warning(f"agent_run_log write failed (non-blocking): {e}")


async def main():
    import time as _time
    parser = argparse.ArgumentParser(description="Autonomous Swarm Run")
    parser.add_argument("--mode", default="daily-ideation",
                        choices=["daily-ideation", "code-review", "cto-audit", "self-upgrade",
                                 "weekly-audit", "monthly-review", "post-deploy"])
    parser.add_argument("--skip-consolidation", action="store_true",
                        help="Skip memory consolidation (useful for quick runs)")
    parser.add_argument("--trigger-meta", default="{}",
                        help="JSON string with trigger metadata (e.g. deploy SHA)")
    args = parser.parse_args()

    if args.mode == "self-upgrade":
        # Self-upgrade execution requires: staging branch target, test gate before merge,
        # human approval gate for medium-risk patches, file-path constraint in patch schema.
        # Not yet implemented — blocked by Security Agent (DSP 2026-03-31, score 12/50).
        # See docs/DECISIONS.md for full risk register and hardening requirements.
        logger.warning(
            "self-upgrade mode is not yet active. "
            "Security gate not met: requires staging branch + test execution + human review loop. "
            "See DSP sprint gate result 2026-03-31."
        )
        print(
            "\n[self-upgrade] Mode registered but execution not yet active.\n"
            "Security requirement: patch system must target swarm-staging branch,\n"
            "run tests before merge, and require human approval for medium-risk patches.\n"
            "Implement hardening first — see docs/DECISIONS.md.\n"
        )
        return

    # Parse trigger metadata (for post-deploy and other event-driven runs)
    try:
        trigger_meta = json.loads(args.trigger_meta)
    except Exception:
        trigger_meta = {}

    _run_start = _time.monotonic()
    proposals = await run_autonomous(args.mode)
    _run_duration_ms = int((_time.monotonic() - _run_start) * 1000)

    # ── Sprint 1: Proposal Groundedness Check ─────────────────────────────────
    # Verify that file paths cited in proposals actually exist.
    # Ungrounded proposals are tagged [UNGROUNDED] — never silently dropped.
    try:
        from swarm.proposal_verifier import tag_proposal_if_ungrounded
        proposal_dicts = [
            {
                "title": p.title,
                "content": p.content,
                "agent": p.agent,
            }
            for p in proposals
        ]
        ungrounded_count = 0
        for i, p_dict in enumerate(proposal_dicts):
            verified = tag_proposal_if_ungrounded(p_dict, project_root)
            if "[UNGROUNDED]" in verified.get("title", ""):
                ungrounded_count += 1
                proposals[i].title = verified["title"]  # propagate tag to Proposal object
        if ungrounded_count:
            logger.warning(
                f"Groundedness check: {ungrounded_count}/{len(proposals)} proposals have invalid file references. "
                "Tagged [UNGROUNDED]. See memory/swarm/ungrounded-proposals.jsonl"
            )
        else:
            logger.info(f"Groundedness check: all {len(proposals)} proposals cite valid files (or no files)")
    except Exception as e:
        logger.warning(f"Proposal verifier failed (non-blocking): {e}")

    # Send Telegram notifications for HIGH/CRITICAL
    await send_telegram_notifications(proposals)

    # ── Sprint 6: Report Generator — structured batch close ──────────────────
    suggestions = []
    groundedness_score = 1.0
    ungrounded_count = 0

    # Gather groundedness from proposals (tagged by verifier above)
    ungrounded = sum(1 for p in proposals if "[UNGROUNDED]" in p.title)
    ungrounded_count = ungrounded
    groundedness_score = 1.0 - (ungrounded / max(len(proposals), 1))

    # Sprint 2: Predictive Next Actions
    try:
        from swarm.suggestion_engine import generate_suggestions
        proposal_list = [{"title": p.title, "content": p.content, "severity": p.severity.value} for p in proposals]
        suggestions = generate_suggestions(
            completed_proposals=proposal_list,
            project_root_override=project_root,
            env=dict(os.environ),
        )
        logger.info(f"Suggestion engine: {len(suggestions)} predicted next actions generated")
    except Exception as e:
        logger.warning(f"Suggestion engine failed (non-blocking): {e}")

    # Build structured report
    try:
        from swarm.report_generator import generate_batch_report, write_to_ceo_inbox, format_for_stdout
        report = generate_batch_report(
            proposals=proposals,
            groundedness_score=groundedness_score,
            ungrounded_count=ungrounded_count,
            predictions=suggestions,
            mode=args.mode,
        )
        # Write to ceo-inbox.md (replaces simple suggestion append)
        write_to_ceo_inbox(report)
        # Print structured stdout summary
        print(format_for_stdout(report))
        logger.info(f"Batch report written to ceo-inbox.md | Health: {report.health_indicator}")
    except Exception as e:
        # Fallback to plain print if report generator fails
        logger.warning(f"Report generator failed (non-blocking): {e}")
        print(f"\n{'='*60}")
        print(f"SWARM AUTONOMOUS RUN — {args.mode}")
        print(f"{'='*60}")
        print(f"Proposals: {len(proposals)}")
        for p in proposals:
            emoji = {"critical": "[CRIT]", "high": "[HIGH]", "medium": "[MED]", "low": "[LOW]"}
            print(f"  {emoji.get(p.severity.value, '[?]')} {p.title}")
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


    # ── ADR-011: Write run audit log to Supabase ────────────────────────────────
    # Non-blocking. Requires SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY in env.
    # GitHub Actions sets these via secrets. Local runs skip gracefully if missing.
    await _write_run_log(proposals, args.mode, _run_duration_ms, trigger_meta)

    # ── Pulse Emotional Core: update agent emotional states ───────────────────
    try:
        from swarm.emotional_core import PulseCognitiveLoop
        state_path = project_root / "memory" / "swarm" / "agent-state.json"
        pulse = PulseCognitiveLoop(state_path)
        pulse.load_emotions()
        for p in proposals:
            agent_name = p.get("agent", "unknown").lower().replace(" ", "-") + "-agent"
            severity = p.get("severity", "medium")
            event_type = "security" if severity == "critical" else "code_change"
            pulse.process_event(
                agent_name=agent_name,
                actor="agent",
                event_type=event_type,
                expected="no issues",
                actual=f"found: {p.get('title', '')}",
                confidence=0.7,
            )
        pulse.save_emotions()
        logger.info(f"Pulse: emotional states updated for {len(proposals)} proposals")
    except Exception as e:
        logger.warning(f"Pulse emotional core update failed (non-fatal): {e}")


if __name__ == "__main__":
    asyncio.run(main())
