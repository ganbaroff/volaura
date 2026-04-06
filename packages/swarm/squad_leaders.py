"""Squad Leaders — hierarchical orchestration for 87 agents.

Flat pool doesn't scale past 10 agents. With 48 Python skills + 39 ZEUS agents,
we need supervisors. Each squad leader manages 10-15 agents in their domain.

Architecture (from team-structure.md):
  CEO → CTO → [5 Squad Leaders] → [agents within squad]

Squad leaders:
1. QUALITY — gates everything (QA, Security, Readiness)
2. PRODUCT — user-facing decisions (UX, BNE, Cultural, Onboarding)
3. ENGINEERING — build + maintain (Architecture, Performance, DevOps, Data)
4. GROWTH — acquisition + retention (Sales, Content, Community, University)
5. ECOSYSTEM — cross-product coherence (Ecosystem Auditor, Financial, Legal)

Each leader:
- Receives tasks routed by keyword matching
- Selects 2-3 agents from their squad
- Runs them via orchestrator with dependencies
- Synthesizes findings into squad report
- Posts to shared memory
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Squad:
    name: str
    leader: str
    description: str
    agents: list[str]
    keywords: list[str]  # routing keywords


SQUADS: list[Squad] = [
    Squad(
        name="QUALITY",
        leader="qa-quality-agent",
        description="Gates everything. Can block tasks. Toyota Jidoka.",
        agents=[
            "qa-quality-agent",
            "risk-manager",
            "readiness-manager",
            "assessment-science-agent",
        ],
        keywords=["quality", "test", "bug", "block", "gate", "dod", "acceptance", "deploy", "launch"],
    ),
    Squad(
        name="PRODUCT",
        leader="ux-research-agent",
        description="User-facing decisions. ADHD-first. AZ cultural context.",
        agents=[
            "ux-research-agent",
            "behavioral-nudge-engine",
            "cultural-intelligence-strategist",
            "onboarding-specialist-agent",
            "customer-success-agent",
            "accessibility-auditor",
        ],
        keywords=["ux", "user", "onboarding", "adhd", "cultural", "design", "page", "screen", "flow", "journey"],
    ),
    Squad(
        name="ENGINEERING",
        leader="architecture-review",
        description="Build + maintain. System coherence. Performance.",
        agents=[
            "architecture-review",
            "performance-engineer-agent",
            "devops-sre-agent",
            "data-engineer-agent",
            "technical-writer-agent",
        ],
        keywords=["code", "api", "database", "migration", "deploy", "railway", "vercel", "supabase", "performance", "scale"],
    ),
    Squad(
        name="GROWTH",
        leader="sales-deal-strategist",
        description="Acquisition, retention, content, partnerships.",
        agents=[
            "sales-deal-strategist",
            "sales-discovery-coach",
            "communications-strategist",
            "linkedin-content-creator",
            "community-manager-agent",
            "university-ecosystem-partner-agent",
            "pr-media-agent",
        ],
        keywords=["growth", "sales", "b2b", "org", "content", "linkedin", "post", "marketing", "retention", "acquisition"],
    ),
    Squad(
        name="ECOSYSTEM",
        leader="legal-advisor",
        description="Cross-product coherence. Legal. Financial. Constitution.",
        agents=[
            "legal-advisor",
            "financial-analyst-agent",
            "investor-board-agent",
            "competitor-intelligence-agent",
            "accelerator-grant-searcher",
        ],
        keywords=["ecosystem", "constitution", "legal", "gdpr", "finance", "crystal", "cross-product", "mindshift", "life-sim", "brandedby"],
    ),
]


def route_to_squad(task_description: str) -> Squad | None:
    """Route a task to the most relevant squad by keyword matching.

    Returns the squad with the most keyword hits, or None if no match.
    """
    task_lower = task_description.lower()
    best_squad = None
    best_score = 0

    for squad in SQUADS:
        score = sum(1 for kw in squad.keywords if kw in task_lower)
        if score > best_score:
            best_score = score
            best_squad = squad

    return best_squad if best_score > 0 else None


def get_squad(name: str) -> Squad | None:
    """Get squad by name."""
    for squad in SQUADS:
        if squad.name == name:
            return squad
    return None


def select_agents(squad: Squad, task_description: str, max_agents: int = 3) -> list[str]:
    """Select most relevant agents within a squad for a task.

    Leader is always included. Remaining slots filled by keyword matching.
    """
    selected = [squad.leader]
    task_lower = task_description.lower()

    # Score each non-leader agent
    scored = []
    for agent in squad.agents:
        if agent == squad.leader:
            continue
        agent_words = set(agent.replace("-", " ").split())
        score = sum(1 for w in agent_words if w in task_lower)
        scored.append((agent, score))

    scored.sort(key=lambda x: -x[1])
    for agent, _ in scored[:max_agents - 1]:
        selected.append(agent)

    return selected


def list_all_squads() -> str:
    """Human-readable summary of all squads and their agents."""
    lines = []
    for s in SQUADS:
        lines.append(f"## {s.name} (leader: {s.leader})")
        lines.append(f"  {s.description}")
        for a in s.agents:
            marker = "★" if a == s.leader else " "
            lines.append(f"  {marker} {a}")
        lines.append("")
    return "\n".join(lines)
