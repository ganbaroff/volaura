"""Squad leaders — routing layer for the Coordinator.

Defines squads (domain teams) and their keyword-based routing.
Each squad has a leader agent, member agents, keywords, and a description.
The Coordinator uses this to break tasks into squad-level subtasks.

Squads map to the Category enum in contracts.py:
  SECURITY, QA, PRODUCT, GROWTH, INFRA, ECOSYSTEM
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Squad:
    name: str
    leader: str
    members: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    description: str = ""


SQUADS: list[Squad] = [
    Squad(
        name="SECURITY",
        leader="security-auditor",
        members=["rls-checker", "auth-reviewer"],
        keywords=["security", "auth", "rls", "injection", "xss", "csrf", "owasp", "vulnerability", "secret", "token"],
        description="Security audit: RLS policies, auth flows, input validation, OWASP top 10",
    ),
    Squad(
        name="QUALITY",
        leader="code-reviewer",
        members=["test-analyst", "lint-checker"],
        keywords=["quality", "lint", "test", "coverage", "bug", "fix", "refactor", "clean", "debt"],
        description="Code quality: test coverage, lint compliance, dead code, patterns",
    ),
    Squad(
        name="PRODUCT",
        leader="product-analyst",
        members=["ux-reviewer", "constitution-checker"],
        keywords=["feature", "ux", "user", "product", "assessment", "aura", "badge", "onboarding", "profile"],
        description="Product analysis: feature completeness, UX flows, Constitution compliance",
    ),
    Squad(
        name="GROWTH",
        leader="growth-strategist",
        members=["analytics-reviewer", "retention-analyst"],
        keywords=["growth", "retention", "funnel", "activation", "engagement", "churn", "referral", "marketing"],
        description="Growth analysis: activation funnel, retention curves, engagement metrics",
    ),
    Squad(
        name="INFRA",
        leader="devops-reviewer",
        members=["ci-checker", "deploy-analyst"],
        keywords=["deploy", "ci", "cd", "docker", "railway", "vercel", "infra", "monitoring", "sentry", "performance"],
        description="Infrastructure: CI/CD health, deployment readiness, monitoring, performance",
    ),
    Squad(
        name="ECOSYSTEM",
        leader="ecosystem-coordinator",
        members=["cross-product-reviewer", "constitution-auditor"],
        keywords=["ecosystem", "mindshift", "life simulator", "brandedby", "atlas", "crystal", "cross-product"],
        description="Ecosystem coherence: cross-product events, crystal economy, shared auth",
    ),
]

_SQUAD_MAP: dict[str, Squad] = {s.name: s for s in SQUADS}


def get_squad(name: str) -> Squad | None:
    return _SQUAD_MAP.get(name)


def route_to_squad(task_description: str) -> list[Squad]:
    task_lower = task_description.lower()
    matches = []
    for squad in SQUADS:
        score = sum(1 for kw in squad.keywords if kw in task_lower)
        if score > 0:
            matches.append((score, squad))
    matches.sort(key=lambda x: -x[0])
    return [squad for _, squad in matches[:3]]


def select_agents(squad: Squad, task_description: str, max_agents: int = 3) -> list[str]:
    agents = [squad.leader, *squad.members]
    return agents[:max_agents]
