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
import time
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
# Settled decisions — injected into ALL agent prompts
# ──────────────────────────────────────────────────────────────

SETTLED_DECISIONS = """
## Settled Decisions (DO NOT contradict or re-open)
1. Ecosystem = only moat. Not IRT, not LLM grading, not AURA score.
2. ADHD-first UX. 26 rules. No punishment. One action per screen.
3. TAM = 500-700K in AZ. Not millions.
4. B2B before B2C. LTV/CAC broken at $3/mo B2C.
5. Birbank/m10 before Stripe. AZ users don't know Stripe.
6. IRT calibration blocks B2B. Need 1000+ real responses.
7. 5->10 minimum questions. 5q mode not defensible.
8. Langfuse + Phoenix for observability.
9. Position on ecosystem, not rigor. SHL beats us on rigor.
10. Communication Law: radical truth, no hedging, caveman (300 words max).
"""

# ──────────────────────────────────────────────────────────────
# Research context — maps agent names to research files they MUST read
# ──────────────────────────────────────────────────────────────

RESEARCH_CONTEXT_MAP = {
    "Scaling Engineer": [
        "docs/research/blind-spots-analysis.md",
        "docs/ARCHITECTURE.md",
    ],
    "Security Auditor": [
        "docs/ATTACK-VECTORS-EXECUTIVE.md",
    ],
    "Product Strategist": [
        "memory/swarm/research/competitive-intelligence-2026-04-12.md",
        "docs/research/adhd-first-ux-research.md",
        "docs/product/COMPETITIVE-ANALYSIS.md",
    ],
    "Cultural Intelligence": [
        "docs/research/adhd-first-ux-research.md",
        "docs/research/ecosystem-design-research.md",
        "docs/product/USER-PERSONAS.md",
    ],
    "Communications Strategist": [
        "docs/design/BRAND-IDENTITY.md",
        "docs/design/UX-COPY-AZ-EN.md",
    ],
    "Assessment Science": [
        "memory/swarm/research/assessment-science-audit-2026-04-12.md",
        "docs/research/gemini-research-all.md",
    ],
    "Legal Advisor": [
        "docs/research/blind-spots-analysis.md",
        "docs/research/geo-pricing-research.md",
    ],
    "PR & Media": [
        "docs/product/COMPETITIVE-ANALYSIS.md",
        "docs/research/blind-spots-analysis.md",
    ],
    "Risk Manager": [
        "docs/research/blind-spots-analysis.md",
    ],
}

MAX_RESEARCH_LINES = 100
MAX_RESEARCH_FILES = 3


def _load_research_context(agent_name: str, root: Path) -> str:
    """Load relevant research files for an agent, truncated to fit context."""
    files = RESEARCH_CONTEXT_MAP.get(agent_name, [])
    if not files:
        return ""
    chunks = []
    for fpath in files[:MAX_RESEARCH_FILES]:
        full = root / fpath
        if full.exists():
            try:
                lines = full.read_text(encoding="utf-8").splitlines()[:MAX_RESEARCH_LINES]
                chunks.append(f"### {fpath}\n" + "\n".join(lines))
            except Exception:
                pass
    if not chunks:
        return ""
    return "\n\n## Research Context (DO NOT re-research these topics)\n\n" + "\n\n".join(chunks)


# ──────────────────────────────────────────────────────────────
# Agent perspectives — each gets a unique lens
# ──────────────────────────────────────────────────────────────

PERSPECTIVES = [
    {
        "name": "Scaling Engineer",
        "lens": "What breaks at 10x users? What bottleneck exists that nobody sees? Focus on database, API latency, and infrastructure limits.",
        "wave": 0,
    },
    {
        "name": "Security Auditor",
        "lens": "What vulnerability exists right now? Check: RLS gaps, unvalidated inputs, missing rate limits, exposed secrets, OWASP top 10.",
        "wave": 0,
    },
    {
        "name": "Product Strategist",
        "lens": "What feature or improvement would have the biggest impact on user acquisition and retention? Think about the AURA score, assessment UX, org admin experience.",
        "wave": 0,
    },
    {
        "name": "Code Quality Engineer",
        "lens": "What technical debt is accumulating? What pattern violations exist? What would make the codebase more maintainable?",
        "wave": 0,
    },
    {
        "name": "Ecosystem Auditor",
        "lens": (
            "You watch for cross-product inconsistencies across all 5 VOLAURA products "
            "(VOLAURA, MindShift, Life Simulator, BrandedBy, ZEUS). "
            "Check: (1) Are Foundation Laws from ECOSYSTEM-CONSTITUTION.md followed in EVERY product? "
            "Especially Law 2 (Energy Adaptation) — only MindShift has it, others missing. "
            "(2) Does this swarm's work conflict with ZEUS Gateway or MindShift decisions? "
            "(3) Is the code-index stale (>7 days old)? If yes, flag as CRITICAL — agents are simulating. "
            "(4) Are there open P0/P1 items in the ecosystem that this swarm is ignoring? "
            "Read ecosystem-map.md first. Output a cross-product impact assessment."
        ),
        "wave": 0,
    },
    {
        "name": "Risk Manager",
        "lens": "ISO 31000:2018 + COSO ERM. Score every open item by Likelihood×Impact (1-5 each). CRITICAL=20-25, HIGH=12-19, MEDIUM=6-11. Flag: unmitigated CRITICAL risks, missing rollback plans, single points of failure, launch blockers. Output a mini Risk Register entry for each finding.",
        "wave": 1,
        "reads_from": ["Security Auditor", "Scaling Engineer"],
    },
    {
        "name": "Readiness Manager",
        "lens": "Google SRE + ITIL v4 + LRR standard. Score platform readiness across 5 dimensions: Functional (0-20), Operational (0-20), Security (0-20), UX (0-20), Rollback (0-20). LRL 1-7. A score <70/100 is a NO-GO for any public launch. Flag any dimension below 12/20 as a launch blocker.",
        "wave": 1,
        "reads_from": ["Code Quality Engineer", "Security Auditor", "Product Strategist"],
    },
    {
        "name": "Cultural Intelligence",
        "lens": (
            "Detect invisible exclusion in AZ/CIS context. Audit: professional identity framing "
            "(scores vs relationships), naming fields (patronymic handling), photo requirements "
            "(conservative norms), competitive language ('top talent' vs collaborative framing), "
            "gender assumptions in assessments. Run the Invisible Exclusion checklist: (1) Does any "
            "feature assume Western career ladder? (2) Does copy use shame ('you haven't done X')? "
            "(3) Are trust signals relationship-based or metric-based? (4) Does the platform respect "
            "collective achievement culture? (5) Are there hidden gender/age biases in question wording?"
        ),
        "wave": 1,
        "reads_from": ["Product Strategist"],
    },
    {
        "name": "Communications Strategist",
        "lens": (
            "Strategic gatekeeper for ALL user-facing text. Audit current copy against 7 Tone-of-Voice "
            "principles (Tinkoff/Aviasales benchmark, not corporate). Check: shame-free language "
            "(Constitution Law 3), banned phrases ('volunteer', profile % complete, 'you should'), "
            "narrative arc coherence across onboarding→assessment→results→sharing flow. "
            "For each finding: specify exact file, exact string, exact replacement. "
            "Target personas: Leyla (22yo professional), Nigar (HR manager), Kamal (34yo senior), "
            "Rauf (28yo ambitious). If copy doesn't speak to at least 2 personas — flag it."
        ),
        "wave": 1,
        "reads_from": ["Product Strategist", "Cultural Intelligence"],
    },
    {
        "name": "Assessment Science",
        "lens": (
            "Validate psychometric soundness of the AURA assessment engine. Check: (1) IRT 3PL "
            "parameters (a, b, c) — are they calibrated from real data or guessed? If guessed, "
            "estimate SEM impact. (2) Question pool size per competency — minimum 15 for CAT to "
            "differentiate, 30+ for reliable theta estimation. (3) DIF analysis — are any questions "
            "biased against AZ/CIS test-takers? (4) CAT stopping rules — is the SE threshold "
            "appropriate? (5) Temporal decay rationale — is the 180-day half-life evidence-based? "
            "Read apps/api/app/core/assessment/engine.py. Output: readiness score 1-10 for B2B launch."
        ),
        "wave": 2,
        "reads_from": ["Code Quality Engineer", "Cultural Intelligence"],
    },
    {
        "name": "Legal Advisor",
        "lens": (
            "Platform-aware legal risk analyst. Check: (1) GDPR Article 22 — automated decision "
            "consent flow exists and is legally sufficient? (2) AZ Personal Data Protection Act — "
            "are we compliant for Baku launch? (3) Platform liability — if AURA score is used for "
            "hiring decisions, what legal exposure exists? (4) Data processor agreements — Supabase, "
            "Google Cloud, Railway as processors, are DPAs in place? (5) Terms of Service — does "
            "current ToS cover AI-generated assessments? Read supabase/migrations/ for data schema, "
            "apps/api/app/routers/assessment.py for consent flow. Output: compliance checklist with "
            "BLOCK/WARN/OK per item."
        ),
        "wave": 2,
        "reads_from": ["Security Auditor", "Assessment Science"],
    },
    {
        "name": "PR & Media",
        "lens": (
            "Pre-launch awareness builder. Audit: (1) Do we have a press narrative ready? "
            "(2) AZ media landscape — ICTnews.az, startup.az, report.az, 1news.az — which outlets "
            "match our story? (3) GITA grant deadline May 27 — is application material ready? "
            "(4) Startup competition pipeline — Seedstars, ASAN Innovations, AzInTelecom. "
            "(5) Founder visibility — is CEO's LinkedIn presence building toward launch? "
            "Output: PR readiness score 1-10 + next 3 concrete actions."
        ),
        "wave": 2,
        "reads_from": ["Communications Strategist", "Cultural Intelligence"],
    },
    {
        "name": "CTO Watchdog",
        "lens": "Is the CTO (Claude) following process? Check: are plans going through agents? Are memory files updated? Is protocol v4.0 being followed? Flag any process violations. You can escalate directly to CEO.",
        "wave": 3,
        "reads_from": ["Risk Manager", "Readiness Manager", "Legal Advisor"],
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

    # ── Ecosystem Map — ALL agents know the 5 products ───────────────────────
    # Added 2026-04-06: agents were simulating cross-product knowledge. Now they read it.
    ecosystem_map = project_root / "packages" / "swarm" / "prompt_modules" / "ecosystem-map.md"
    if ecosystem_map.exists():
        with open(ecosystem_map, "r", encoding="utf-8") as f:
            state_parts.append("## VOLAURA ECOSYSTEM (5 products — read before any proposal)\n" + f.read())

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

    # ── Swarm Tools: inject real codebase data (not just documents) ──────
    # Constitution checker gives agents REAL violation data, not assumptions.
    # Code index summary gives agents awareness of what files exist.
    # ── Shared Memory: inject previous agent findings ───────────────
    try:
        from swarm.shared_memory import get_all_recent
        recent = get_all_recent(limit=10)
        if recent:
            findings = []
            for r in recent:
                agent = r["agent"]
                title = r["data"].get("title", "")[:80] if isinstance(r["data"], dict) else ""
                findings.append(f"- [{agent}] {title}")
            state_parts.append(
                "## RECENT SWARM FINDINGS (shared memory)\n" + "\n".join(findings)
            )
    except Exception:
        pass  # shared memory not yet initialized — non-blocking

    try:
        from swarm.tools.constitution_checker import run_full_audit
        constitution_report = run_full_audit()
        if constitution_report:
            state_parts.append(
                "## CONSTITUTION COMPLIANCE (live scan)\n" + constitution_report[:2000]
            )
    except Exception as e:
        logger.debug("Constitution checker failed (non-blocking): {e}", e=str(e)[:100])

    try:
        from swarm.tools.deploy_tools import check_git_status
        git_state = check_git_status()
        if git_state:
            state_parts.append("## GIT STATUS\n" + git_state[:500])
    except Exception as e:
        logger.debug("Git status check failed (non-blocking): {e}", e=str(e)[:100])

    return "\n\n".join(state_parts) if state_parts else "No project state files found."


def _build_agent_prompt(perspective: dict, project_state: str, mode: str, project_root: Path | None = None) -> str:
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
- Budget: $200+/mo (Claude Max alone = $200, plus API costs).
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

    # Inject ACTUAL skill file content — not just names (fixed Session 88)
    # Before: agents saw "ROUTED SKILLS: security-agent" but never the file content
    # After: agents see the full skill definition (capped at 500 chars per skill)
    routed = perspective.get('routed_skills', [])
    skills_line = ""
    _pr = project_root or Path(__file__).parent.parent.parent
    if routed:
        skills_dir = _pr / "memory" / "swarm" / "skills"
        skill_contents = []
        for skill_name in routed[:3]:  # max 3 skills to not blow prompt budget
            skill_path = skills_dir / f"{skill_name}.md"
            if skill_path.exists():
                try:
                    content = skill_path.read_text(encoding="utf-8").strip()[:500]
                    skill_contents.append(f"### SKILL: {skill_name}\n{content}")
                except Exception:
                    skill_contents.append(f"### SKILL: {skill_name}\n(read error)")
            else:
                skill_contents.append(f"### SKILL: {skill_name}\n(file not found)")
        skills_line = "\n\nYOUR LOADED SKILLS:\n" + "\n\n".join(skill_contents)

    bound_files_line = f"\n\n{perspective.get('bound_files', '')}" if perspective.get('bound_files') else ""

    # ── Web search results injection (Tavily — agents can Google) ───────────
    web_search_line = ""
    tavily_key = os.environ.get("TAVILY_API_KEY", "")
    search_query = perspective.get("web_search_query")
    if tavily_key and search_query:
        try:
            from swarm.tools.web_search import web_search_sync
            results = web_search_sync(search_query, max_results=3)
            if results:
                web_search_line = f"\n\nWEB SEARCH RESULTS for '{search_query}':\n{results}"
        except Exception as e:
            logger.debug(f"Web search skipped for {perspective.get('name', '?')}: {e}")

    # ── Reflexion injection: agents learn from past mistakes (CEO plan 5.1) ──
    reflexion_line = ""
    try:
        from swarm.reflexion import get_reflexions_for_task, get_decision_history_context
        task_reflexions = get_reflexions_for_task(perspective.get("lens", ""), max_entries=3)
        decision_ctx = get_decision_history_context(max_entries=2)
        parts = [p for p in [task_reflexions, decision_ctx] if p]
        if parts:
            reflexion_line = "\n\n" + "\n\n".join(parts)
    except Exception:
        pass  # non-blocking

    # ── FindingContract schema injection (Week 2, item 3) ────────────────────
    # All agents now receive the typed contract format.
    # Coordinator reads this to aggregate findings without free-text parsing.
    from swarm.contracts import FINDING_SCHEMA_FOR_PROMPT

    prior_findings_line = perspective.get("prior_findings", "")

    research_context = _load_research_context(perspective["name"], _pr)

    return f"""{team_context}

{SETTLED_DECISIONS}

YOUR PERSPECTIVE: {perspective['name']}
YOUR LENS: {perspective['lens']}{weight_line}{skills_line}{bound_files_line}{reflexion_line}{prior_findings_line}{research_context}

{task}

CURRENT PROJECT STATE:
{project_state}

{FINDING_SCHEMA_FOR_PROMPT}

LEGACY FORMAT ALSO ACCEPTED (for backward compatibility with inbox pipeline):
You MAY additionally include these fields outside the JSON if needed:
- "title": one-line summary (used by CEO inbox display)
- "type": "idea|escalation|complaint|code_review|security"
- "escalate_to_ceo": true/false

But the FindingContract fields above are REQUIRED and take priority."""


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
            logger.warning(f"Gemini fallback failed for {perspective_name}: {e}")

    # ── Fallback 3: LiteLLM Router (Cerebras → Groq → Gemini unified) ────────
    if not raw:
        try:
            from swarm.tools.llm_router import complete
            raw = await complete(prompt)
            if raw:
                logger.debug(f"Agent {perspective_name} → LiteLLM router")
        except Exception as e:
            logger.warning(f"LiteLLM router failed for {perspective_name}: {e}")

    if not raw:
        logger.error(f"All LLM providers failed for agent {perspective_name}")
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
        # Gemini sometimes returns [{}] instead of {} — unwrap
        if isinstance(data, list):
            data = data[0] if data else {}

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

    # Launch agents in DAG waves — wave 0 first (parallel), then wave 1 with
    # wave 0 findings injected, then wave 2 with wave 0+1 findings, etc.
    # This is the coordination layer CEO asked for: agents in later waves
    # SEE what earlier agents found, instead of running blindfolded.
    max_wave = max(p.get("wave", 0) for p in PERSPECTIVES)
    all_results: list[tuple[dict, str | Exception | None]] = []
    wave_findings: dict[str, str] = {}

    for wave_num in range(max_wave + 1):
        wave_perspectives = [p for p in PERSPECTIVES if p.get("wave", 0) == wave_num]
        if not wave_perspectives:
            continue

        logger.info(f"Wave {wave_num}: launching {len(wave_perspectives)} agents — {[p['name'] for p in wave_perspectives]}")

        wave_tasks = []
        for perspective in wave_perspectives:
            weight_ctx = registry.inject_weight_context(perspective["name"])
            routed_skills = _route_skills_for_perspective(perspective["name"], skills_dir)

            bound_files_section = ""
            if _code_index is not None:
                try:
                    bound = bind_task_to_files(perspective["lens"], _code_index, project_root)
                    if bound.primary_files:
                        bound_files_section = bound.to_briefing_section()
                except Exception:
                    pass

            prior_findings = ""
            reads_from = perspective.get("reads_from", [])
            if reads_from and wave_findings:
                chunks = []
                for src in reads_from:
                    if src in wave_findings:
                        chunks.append(f"[{src}]: {wave_findings[src][:500]}")
                if chunks:
                    prior_findings = "\n\n== FINDINGS FROM EARLIER AGENTS (use these, don't re-discover) ==\n" + "\n".join(chunks)

            enriched_perspective = {
                **perspective,
                "weight_context": weight_ctx,
                "routed_skills": routed_skills,
                "bound_files": bound_files_section,
                "prior_findings": prior_findings,
            }
            prompt = _build_agent_prompt(enriched_perspective, project_state, mode, project_root=project_root)
            wave_tasks.append((perspective, _call_agent(prompt, perspective["name"], env)))

        wave_results = await asyncio.gather(*[t[1] for t in wave_tasks], return_exceptions=True)

        for (perspective, _), result in zip(wave_tasks, wave_results):
            all_results.append((perspective, result))
            if isinstance(result, str) and result:
                wave_findings[perspective["name"]] = result

    results = [r for _, r in all_results]

    # ── Shared Memory: agents post results so others can see ──────────
    run_task_id = f"{mode}-{int(time.time())}"
    try:
        from swarm.shared_memory import post_result as sm_post, get_context as sm_context
        _shared_memory_available = True
    except Exception:
        _shared_memory_available = False

    # Process results into proposals
    proposals: list[Proposal] = []
    raw_results = []

    for i, (perspective_i, result) in enumerate(all_results):
        if isinstance(result, Exception):
            logger.error(f"Agent {perspective_i['name']} exception: {result}")
            continue
        if result is None:
            continue

        raw_results.append(result)

        if _shared_memory_available:
            try:
                sm_post(
                    agent_id=perspective_i["name"],
                    task_id=run_task_id,
                    result=result,
                    run_id=run_task_id,
                )
            except Exception:
                pass  # non-blocking

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

            # Build content: agents use FINDING_SCHEMA (summary + recommendation),
            # older agents used "content". Combine both so Proposal.content is never empty.
            _summary = str(result.get("summary", "") or "").strip()
            _rec = str(result.get("recommendation", "") or "").strip()
            _content_legacy = str(result.get("content", "") or result.get("description", "") or "").strip()
            if _content_legacy:
                _proposal_content = _content_legacy
            elif _summary or _rec:
                _proposal_content = f"{_summary}\n\nRecommendation: {_rec}".strip()
            else:
                _proposal_content = ""

            # Title: prefer explicit "title", then "summary" (FINDING_SCHEMA), then first content line
            _raw_title = str(result.get("title", "") or "").strip()
            if not _raw_title:
                _title_source = _summary or _content_legacy
                if _title_source:
                    _first_line = next((ln.strip() for ln in _title_source.split("\n") if ln.strip()), "")
                    _raw_title = (_first_line[:80] + "...") if len(_first_line) > 80 else _first_line
                if not _raw_title:
                    _raw_title = f"Proposal from {result.get('agent', f'agent-{i}')}"

            proposal = Proposal(
                agent=result.get("agent", f"agent-{i}"),
                severity=severity_map.get(result.get("severity", "medium"), Severity.MEDIUM),
                type=type_map.get(result.get("type", "idea"), ProposalType.IDEA),
                title=_raw_title,
                content=_proposal_content,
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

    # ── Task Ledger — record every proposal ──────────────────────────────────
    try:
        from packages.swarm.task_ledger import write_proposal
        for proposal in proposals:
            write_proposal(proposal, mode=mode)
    except Exception as _le:
        logger.debug(f"task_ledger write_proposal skipped: {_le}")

    # Summary
    convergent_total = sum(1 for p in proposals if p.convergent)
    logger.info(
        f"Autonomous run complete: {len(proposals)} proposals stored, "
        f"{sum(1 for p in proposals if p.escalate_to_ceo)} escalations, "
        f"{convergent_total} convergent (high signal)"
    )

    return proposals


async def send_telegram_notifications(
    proposals: list[Proposal],
    fix_results: list[dict] | None = None,
) -> None:
    """Send digest with Found + Fixed counts to CEO via Telegram.

    fix_results is a list of dicts from _run_auto_fix(), each shaped:
        {
          "proposal_id": str,
          "proposal_title": str,
          "ok": bool,
          "stage": str,                 # "executed" | "blocked_by_gate" | "aider_failed" | ...
          "commit_hash": str,            # "" if no commit
          "error": str,                  # non-empty iff ok=False
        }
    """
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CEO_CHAT_ID", "")

    if not bot_token or not chat_id:
        logger.info("Telegram not configured (TELEGRAM_BOT_TOKEN / TELEGRAM_CEO_CHAT_ID missing)")
        return

    fix_results = fix_results or []
    fixed = [r for r in fix_results if r.get("ok")]
    # Separate "blocked by safety gate" (expected) from real errors (unexpected)
    skipped_fixes = [r for r in fix_results if not r.get("ok") and r.get("stage") in ("blocked_by_gate", "no_files")]
    failed_fixes = [r for r in fix_results if not r.get("ok") and r.get("stage") not in ("blocked_by_gate", "no_files")]

    high_proposals = [
        p for p in proposals
        if p.severity in (Severity.CRITICAL, Severity.HIGH) or p.escalate_to_ceo or p.convergent
    ]

    # Only notify CEO when something actionable happened.
    # Quiet runs stay silent — CEO said 40 msgs/day is spam.
    if not high_proposals and not fixed and not failed_fixes:
        logger.info("Quiet run — no Telegram notification (nothing actionable)")
        return

    try:
        from telegram import Bot
        bot = Bot(token=bot_token)

        critical = [p for p in high_proposals if p.severity == Severity.CRITICAL]
        convergent = [p for p in high_proposals if p.convergent]
        high = [p for p in high_proposals if p.severity == Severity.HIGH and not p.convergent]

        summary_parts = [
            f"Найдено: *{len(proposals)}*",
            f"Исправлено: *{len(fixed)}*",
        ]
        if skipped_fixes:
            summary_parts.append(f"Пропущено gate: *{len(skipped_fixes)}*")
        if failed_fixes:
            summary_parts.append(f"Ошибок: *{len(failed_fixes)}*")

        lines = [
            "📋 *Swarm Digest*",
            "  |  ".join(summary_parts),
            "",
        ]

        if fixed:
            lines.append(f"✅ *Исправлено ({len(fixed)}):*")
            for r in fixed[:5]:
                commit = r.get("commit_hash", "")[:12] or "-"
                title = (r.get("proposal_title") or "")[:70]
                lines.append(f"  • `{commit}` {title}")
            lines.append("")

        if failed_fixes:
            lines.append(f"⚠️ *Ошибки авто-фикса ({len(failed_fixes)}):*")
            for r in failed_fixes[:3]:
                stage = r.get("stage", "?")
                title = (r.get("proposal_title") or "")[:60]
                lines.append(f"  • [{stage}] {title}")
            lines.append("")

        if critical:
            lines.append(f"🔴 *CRITICAL ({len(critical)}):*")
            for p in critical[:3]:
                lines.append(f"  • {p.title[:80]} ({p.agent})")
            lines.append("")

        if convergent:
            lines.append(f"🎯 *Convergent ({len(convergent)}):*")
            for p in convergent[:3]:
                lines.append(f"  • {p.title[:80]}")
            lines.append("")

        if high:
            lines.append(f"🟠 *High ({len(high)}):*")
            for p in high[:5]:
                lines.append(f"  • {p.title[:80]}")
            lines.append("")

        if not proposals and not fix_results:
            lines.append("_Тихий прогон: рой ничего нового не нашёл._")

        lines.append("/proposals — посмотреть всё")

        # Telegram Markdown is finicky with backticks + brackets; if parse fails
        # we retry as plain text so the digest still lands.
        msg = "\n".join(lines)
        try:
            await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
        except Exception as md_err:
            logger.warning(f"Telegram Markdown parse failed, retrying plain: {md_err}")
            plain = msg.replace("*", "").replace("`", "").replace("_", "")
            await bot.send_message(chat_id=chat_id, text=plain)

        logger.info(
            f"Telegram digest sent: found={len(proposals)} fixed={len(fixed)} skipped={len(skipped_fixes)} errors={len(failed_fixes)}"
        )

    except Exception as e:
        logger.error(f"Telegram send failed: {e}")


async def _run_auto_fix(
    proposals: list[Proposal],
    max_fixes: int = 3,
) -> list[dict]:
    """Try to auto-implement the safest proposals via swarm_coder + Aider.

    Contract:
    - Never raises. Any failure becomes a dict in the result list so the
      Telegram digest can still report "не удалось исправить: X".
    - Only touches proposals classified AUTO by safety_gate (docs, comments,
      type hints, locale JSON, test files). Everything else is skipped.
    - Capped at max_fixes per run to protect API quota and keep the morning
      commit list reviewable at a glance.

    Returns list of dicts (see send_telegram_notifications docstring).
    """
    results: list[dict] = []

    # swarm_coder lives in scripts/ (not a package). Inject into sys.path.
    scripts_dir = project_root / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    try:
        import swarm_coder as sc  # type: ignore
    except Exception as e:
        logger.warning(f"Auto-fix disabled: swarm_coder import failed: {e}")
        return results

    # Rebase swarm_coder's module-level paths onto the actual project root.
    # swarm_coder.resolve_root() walks for apps/api/.env which is absent in CI —
    # without this patch it falls back to C:/Projects/VOLAURA and file ops break.
    try:
        sc.PROJECT_ROOT = project_root
        sc.PROPOSALS_FILE = project_root / "memory" / "swarm" / "proposals.json"
        sc.LOG_FILE = project_root / "memory" / "swarm" / "swarm_coder_log.jsonl"
        sc.SCRIPTS_DIR = scripts_dir
        sc.ENV_FILE = project_root / "apps" / "api" / ".env"
    except Exception as e:
        logger.warning(f"Auto-fix disabled: could not rebase swarm_coder paths: {e}")
        return results

    # CI portability: swarm_coder.load_env() reads apps/api/.env which doesn't exist on
    # CI runners. call_aider() does an early return if the key isn't in the .env dict.
    # Monkey-patch load_env to merge os.environ API keys so aider gets credentials.
    _original_load_env = getattr(sc, "load_env", None)
    if _original_load_env is not None:
        _ENV_KEY_NAMES = (
            "GEMINI_API_KEY", "GROQ_API_KEY", "OPENROUTER_API_KEY",
            "CEREBRAS_API_KEY", "NVIDIA_API_KEY", "OPENAI_API_KEY",
        )
        def _ci_aware_load_env() -> dict:
            result = _original_load_env()
            for k in _ENV_KEY_NAMES:
                if not result.get(k):
                    v = os.environ.get(k, "")
                    if v:
                        result[k] = v
            return result
        sc.load_env = _ci_aware_load_env

    # Candidates: lowest-risk severities first, skip UNGROUNDED (invalid file refs),
    # anything escalated (CEO wants eyes on those), MANUAL (requires human impl),
    # and proposals with empty content (aider would get blank instruction → wasted tokens).
    candidates = [
        p for p in proposals
        if p.severity in (Severity.LOW, Severity.MEDIUM)
        and "[UNGROUNDED]" not in p.title
        and not p.escalate_to_ceo
        and p.status.value != "manual"
        and p.content.strip()
    ]
    # If we have judge scores, prefer proposals that scored well
    candidates.sort(
        key=lambda p: (-(p.judge_score or 0), p.severity.value),
    )
    candidates = candidates[: max(max_fixes * 3, 6)]  # overshoot, gate will filter

    logger.info(f"Auto-fix: evaluating {len(candidates)} low/medium proposals (cap={max_fixes})")

    executed = 0
    for prop in candidates:
        if executed >= max_fixes:
            break

        # Convert Proposal → dict shape swarm_coder.implement_proposal expects
        prop_dict = {
            "id": getattr(prop, "id", "") or f"run-{int(time.time())}-{prop.agent}",
            "title": prop.title,
            "content": prop.content,
            "agent": prop.agent,
            "severity": prop.severity.value,
        }

        logger.info(f"Auto-fix: trying [{prop.severity.value}] {prop.title[:60]}")
        try:
            # 420s outer timeout: aider subprocess timeout is 300s, +120s for startup/test gate
            r = await asyncio.wait_for(
                asyncio.to_thread(
                    sc.implement_proposal,
                    prop_dict,
                    True,   # execute
                    False,  # plan_only
                    None,   # files_override
                ),
                timeout=420,
            )
        except asyncio.TimeoutError:
            logger.warning(f"Auto-fix timeout (420s) on '{prop.title[:50]}'")
            results.append({
                "proposal_id": prop_dict["id"],
                "proposal_title": prop.title,
                "ok": False,
                "stage": "timeout",
                "commit_hash": "",
                "error": "implement_proposal exceeded 420s outer timeout",
            })
            continue
        except Exception as e:
            logger.warning(f"Auto-fix crashed on '{prop.title[:50]}': {e}")
            results.append({
                "proposal_id": prop_dict["id"],
                "proposal_title": prop.title,
                "ok": False,
                "stage": "crash",
                "commit_hash": "",
                "error": str(e)[:200],
            })
            continue

        stage = r.get("stage", "unknown")
        aider = r.get("aider") or {}
        commit_hash = aider.get("commit_hash", "") if isinstance(aider, dict) else ""
        ok = bool(r.get("ok")) and stage == "executed" and bool(commit_hash)

        results.append({
            "proposal_id": prop_dict["id"],
            "proposal_title": prop.title,
            "ok": ok,
            "stage": stage,
            "commit_hash": commit_hash,
            "error": "" if ok else stage,
        })

        if ok:
            executed += 1
            logger.info(f"Auto-fix: ✅ {commit_hash[:12]} {prop.title[:60]}")
        else:
            logger.info(f"Auto-fix: ⏭ skipped ({stage}) {prop.title[:60]}")

        # ── Task Ledger — record every fix attempt ────────────────────────
        try:
            from packages.swarm.task_ledger import write_fix_attempt
            write_fix_attempt(prop_dict["id"], prop.title, results[-1], mode="auto_fix")
        except Exception as _le:
            logger.debug(f"task_ledger write_fix_attempt skipped: {_le}")

    logger.info(
        f"Auto-fix complete: {executed}/{len(candidates)} implemented, "
        f"{len(results) - executed} skipped/failed"
    )
    return results


async def _notify_zeus_gateway(proposals: list[Proposal]) -> None:
    """Send HIGH/CRITICAL findings to ZEUS Gateway via POST /event.

    This is the bridge between Python swarm (44 agents, GitHub Actions cron)
    and Node.js gateway (39 agents, real-time WebSocket). Findings become
    visible in the claw3d 3D office and to all Node.js agents.

    Non-blocking: if gateway is unreachable, log and continue silently.
    Requires GATEWAY_SECRET env var for auth.
    """
    gateway_url = os.environ.get("ZEUS_GATEWAY_URL", "https://volauraapi-production.up.railway.app")
    gateway_secret = os.environ.get("GATEWAY_SECRET", "")

    if not gateway_secret:
        logger.debug("GATEWAY_SECRET not set — skipping ZEUS bridge (non-blocking).")
        return

    high_proposals = [p for p in proposals if p.severity in (Severity.HIGH, Severity.CRITICAL)]
    if not high_proposals:
        return

    import aiohttp

    for p in high_proposals:
        payload = {
            "source": "python-swarm",
            "type": "agent.finding",
            "agent": p.agent,
            "severity": p.severity.value,
            "title": p.title,
            "content": p.content[:500],  # cap to prevent oversized payloads
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{gateway_url}/api/zeus/proposal",
                    json=payload,
                    headers={"X-Gateway-Secret": gateway_secret},
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    if resp.status == 200:
                        logger.info(
                            "ZEUS bridge: sent {sev} finding from {agent}",
                            sev=p.severity.value, agent=p.agent,
                        )
                    else:
                        logger.debug(
                            "ZEUS bridge: {status} from gateway", status=resp.status
                        )
        except Exception as e:
            logger.debug("ZEUS bridge: gateway unreachable ({e})", e=str(e)[:100])
            break  # don't retry all if gateway is down


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
                                 "weekly-audit", "monthly-review", "post-deploy", "coordinator", "simulate"])
    parser.add_argument("--task", default="",
                        help="Task description for coordinator mode")
    parser.add_argument("--skip-consolidation", action="store_true",
                        help="Skip memory consolidation (useful for quick runs)")
    parser.add_argument("--trigger-meta", default="{}",
                        help="JSON string with trigger metadata (e.g. deploy SHA)")
    args = parser.parse_args()

    if args.mode == "coordinator":
        # Coordinator mode: single task → squad routing → asyncio.gather → CoordinatorResult
        task_desc = args.task or "daily audit: security, UX, and code quality review"
        env = dict(os.environ)

        async def _coordinator_runner(agent_id: str, input_data: dict) -> dict | None:
            """Wrap _call_agent for use with Coordinator."""
            instruction = input_data.get("instruction", "")
            squad_name = input_data.get("squad_name", agent_id)
            perspective = {
                "name": agent_id,
                "lens": f"[{squad_name}] {instruction}",
                "routed_skills": [],
                "bound_files": "",
            }
            project_state = _read_project_state(project_root)
            prompt = _build_agent_prompt(perspective, project_state, "coordinator", project_root=project_root)
            return await _call_agent(prompt, agent_id, env)

        from swarm.coordinator import Coordinator
        coord = Coordinator(runner=_coordinator_runner)
        result = await coord.run(task_desc)

        print(f"\n=== COORDINATOR RESULT ===")
        print(f"Task:     {task_desc}")
        print(f"Agents:   {result.total_agents} total ({result.succeeded} ok, {result.failed} failed)")
        print(f"Findings: {len(result.findings)}")
        print(f"Synthesis: {result.synthesis}")
        if result.priority_action:
            print(f"PRIORITY: {result.priority_action}")
        print()
        for f in result.findings:
            print(f"  [{f.severity.value}] {f.agent_id}: {f.summary[:100]}")
        return

    if args.mode == "simulate":
        # Simulate all 10 personas, post friction to shared memory, report via Telegram
        try:
            from swarm.simulate_users import simulate, _friction_report
            results = await simulate(dry_run=False)  # real Supabase writes if keys set
            total_events = sum(r["events_written"] for r in results)
            total_friction = sum(
                sum(1 for s in r.get("steps", []) if s.get("friction"))
                for r in results
            )
            report = _friction_report(results)
            logger.info("Simulation complete: {e} events, {f} friction points", e=total_events, f=total_friction)

            # Send to Telegram CEO
            bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
            chat_id = os.environ.get("TELEGRAM_CEO_CHAT_ID", "")
            if bot_token and chat_id:
                import urllib.request as _urllib
                msg = f"🎭 Swarm simulation: {len(results)} personas, {total_events} events, {total_friction} UX issues\n\n"
                all_friction = []
                for r in results:
                    for s in r.get("steps", []):
                        if s.get("friction"):
                            all_friction.append(f"[{r['persona']}] {s['friction']}")
                if all_friction[:5]:
                    msg += "Top friction:\n" + "\n".join(f"• {f[:90]}" for f in all_friction[:5])
                payload = json.dumps({"chat_id": chat_id, "text": msg}).encode()
                req = _urllib.Request(
                    f"https://api.telegram.org/bot{bot_token}/sendMessage",
                    data=payload, headers={"Content-Type": "application/json"},
                )
                try:
                    _urllib.urlopen(req, timeout=10)
                except Exception:
                    pass
        except Exception as e:
            logger.error("simulate mode failed: {e}", e=str(e))
        return

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

    # Auto-fix loop: try swarm_coder on the safest low/medium proposals.
    # Runs BEFORE the digest so the Telegram message can report "Исправлено: Y".
    # Capped + sandboxed — never raises, worst case returns [].
    # Disable by setting SWARM_AUTO_FIX=0 in env.
    fix_results: list[dict] = []
    if os.environ.get("SWARM_AUTO_FIX", "1") != "0":
        try:
            max_fixes = int(os.environ.get("SWARM_AUTO_FIX_MAX", "3"))
        except ValueError:
            max_fixes = 3
        try:
            fix_results = await _run_auto_fix(proposals, max_fixes=max_fixes)
        except Exception as e:
            logger.error(f"Auto-fix outer crash (non-blocking): {e}")
    else:
        logger.info("Auto-fix disabled via SWARM_AUTO_FIX=0")

    # Send Telegram digest: found + fixed counts + commit hashes
    await send_telegram_notifications(proposals, fix_results)

    # ── Python↔Node.js Bridge — send HIGH/CRITICAL to ZEUS Gateway ────────
    # This unifies the two swarms: Python findings appear in Node.js gateway's
    # event stream, visible in claw3d 3D office and to all 39 Node.js agents.
    # Constitution: "Two disconnected systems share ONLY filesystem" — this closes the gap.
    await _notify_zeus_gateway(proposals)

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
                print("[OK] Memory consolidated - agent-feedback-distilled.md updated")
            else:
                print("[WARN] Memory consolidation used fallback (LLM unavailable)")
        except Exception as e:
            logger.error(f"Memory consolidation failed: {e}")
            print(f"[FAIL] Memory consolidation failed: {e}")

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
            print(f"[OK] Skill evolution complete - {summary['skills']} skills, health={health}/100")
            if summary.get("issues", 0) > 0:
                print(f"  [WARN] {summary['issues']} issues found - see skill-evolution-log.md")
        except Exception as e:
            logger.error(f"Skill evolution failed: {e}")
            print(f"[FAIL] Skill evolution failed: {e}")


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
            agent_name = (p.agent if hasattr(p, 'agent') else p.get("agent", "unknown") if isinstance(p, dict) else "unknown").lower().replace(" ", "-") + "-agent"
            sev = p.severity.value if hasattr(p, 'severity') and hasattr(p.severity, 'value') else (p.get("severity", "medium") if isinstance(p, dict) else "medium")
            event_type = "security" if sev == "critical" else "code_change"
            title = p.title if hasattr(p, 'title') else (p.get("title", "") if isinstance(p, dict) else "")
            pulse.process_event(
                agent_name=agent_name,
                actor="agent",
                event_type=event_type,
                expected="no issues",
                actual=f"found: {title}",
                confidence=0.7,
            )
        pulse.save_emotions()
        logger.info(f"Pulse: emotional states updated for {len(proposals)} proposals")
    except Exception as e:
        logger.warning(f"Pulse emotional core update failed (non-fatal): {e}")


if __name__ == "__main__":
    asyncio.run(main())
