"""
Team Lead delegation system for MiroFish swarm.
Each TeamLead knows which models to call for their domain and which to avoid.

Usage:
    from packages.swarm.team_leads import get_tilead_for_domain
    tilead = get_tilead_for_domain(DomainTag.BUSINESS)
    preferred = tilead.filter_providers(available_providers)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from packages.swarm.swarm_types import DomainTag


@dataclass
class TeamLead:
    """Base class. Each tilead knows their domain and team preferences."""

    domain: str
    description: str
    preferred_models: list[str] = field(default_factory=list)
    avoid_models: list[str] = field(default_factory=list)
    contrarian_models: list[str] = field(default_factory=list)  # Use for adversarial check

    def filter_providers(self, available_providers: list) -> list:
        """
        Filter available providers to those preferred for this domain.
        Falls back to full list if no preferred models are available.
        """
        if not self.preferred_models:
            return available_providers

        preferred = [
            p for p in available_providers
            if any(m in p.get_model_name() for m in self.preferred_models)
        ]
        avoided = [
            p for p in available_providers
            if any(m in p.get_model_name() for m in self.avoid_models)
        ]

        # Return preferred pool, excluding explicitly avoided models
        filtered = [p for p in preferred if p not in avoided]

        # Fallback: if filtering removed everyone, return all minus avoided
        if not filtered:
            return [p for p in available_providers if p not in avoided] or available_providers

        return filtered

    def get_contrarian_pool(self, available_providers: list) -> list:
        """Return the adversarial review pool for this domain."""
        if not self.contrarian_models:
            return available_providers[:2]
        return [
            p for p in available_providers
            if any(m in p.get_model_name() for m in self.contrarian_models)
        ] or available_providers[:1]


# ─── DOMAIN-SPECIFIC TEAM LEADS ──────────────────────────────────────────────

class ContentTeamLead(TeamLead):
    """
    Routes content, LinkedIn, tone-of-voice, and brand tasks.
    Best models: fast Gemini variants for volume + deepseek for adversarial check.
    Reference: docs/MODEL-ROSTER.md#for-content--linkedin--tov-tasks
    """

    def __init__(self):
        super().__init__(
            domain="business",
            description="Content, LinkedIn, ToV, brand voice — creative and editorial tasks",
            preferred_models=[
                "gemini-2.5-flash-lite",
                "gemini-1.5-flash",
                "gemini-flash-lite-latest",
                "gemini-3.1-flash-lite-preview",
            ],
            avoid_models=[],  # All Gemini variants fine for content
            contrarian_models=["deepseek-chat"],  # Best at: "what's wrong with this?"
        )


class BusinessTeamLead(TeamLead):
    """
    Routes strategy, pricing, market analysis, and business decisions.
    Reference: docs/MODEL-ROSTER.md#for-business--strategy--pricing-tasks
    """

    def __init__(self):
        super().__init__(
            domain="business",
            description="Business strategy, pricing, market analysis, grant decisions",
            preferred_models=[
                "gemini-1.5-flash",
                "gemini-2.5-flash-lite",
                "gemini-2.5-pro",
                "deepseek-chat",
            ],
            avoid_models=["gemini-flash-lite-latest"],  # Weak in business domain (hive exam)
            contrarian_models=["deepseek-chat"],
        )


class SecurityTeamLead(TeamLead):
    """
    Routes security reviews, RLS audits, and risk assessments.
    Reference: docs/MODEL-ROSTER.md#for-security--risk-assessment-tasks
    """

    def __init__(self):
        super().__init__(
            domain="security",
            description="Security review, RLS policies, auth flows, risk assessment",
            preferred_models=[
                "deepseek-chat",      # Best: identifies THE specific risk, not a list
                "gemini-2.5-pro",     # Best: deep reasoning on implications
                "gemini-1.5-flash",   # Support: balanced perspective
            ],
            avoid_models=["gemini-flash-lite-latest"],  # Weak in security (hive exam)
            contrarian_models=["deepseek-chat"],
        )


class ArchitectureTeamLead(TeamLead):
    """
    Routes architecture decisions, code review, technical design.
    Reference: docs/MODEL-ROSTER.md#for-architecture--code-review-tasks
    """

    def __init__(self):
        super().__init__(
            domain="architecture",
            description="Architecture decisions, system design, code review, API design",
            preferred_models=[
                "gemini-2.5-pro",    # Slowest but deepest reasoning
                "deepseek-chat",     # Finds specific code flaws
                "gemini-1.5-flash",  # Support
            ],
            avoid_models=["gemini-flash-lite-latest"],  # Failed architecture hive exam
            contrarian_models=["deepseek-chat"],
        )


class SpeedTeamLead(TeamLead):
    """
    For latency-critical tasks needing fast responses (<10s).
    Sacrifices depth for speed.
    Reference: docs/MODEL-ROSTER.md#for-speed-critical--quick-decisions
    """

    def __init__(self):
        super().__init__(
            domain="general",
            description="Speed-critical tasks — quick evaluations, obvious decisions",
            preferred_models=[
                "gemini-flash-lite-latest",   # ~590ms — fastest
                "gemini-2.5-flash-lite",      # ~795ms — fast with quality
                "gemini-1.5-flash",           # ~852ms — reliable fallback
            ],
            avoid_models=[
                "gemini-2.5-pro",    # ~2760ms — too slow
                "deepseek-chat",     # ~2204ms — too slow
            ],
            contrarian_models=[],
        )


# ─── REGISTRY ────────────────────────────────────────────────────────────────

_TILEAD_REGISTRY: dict[str, TeamLead] = {
    "code": ArchitectureTeamLead(),
    "security": SecurityTeamLead(),
    "business": BusinessTeamLead(),
    "ux": ContentTeamLead(),
    "architecture": ArchitectureTeamLead(),
    "operations": BusinessTeamLead(),
    "data": ArchitectureTeamLead(),
    "general": SpeedTeamLead(),
    "content": ContentTeamLead(),
    "linkedin": ContentTeamLead(),
}


def get_tilead_for_domain(domain) -> TeamLead:
    """
    Get the appropriate team lead for a given domain.

    Args:
        domain: DomainTag enum value or string

    Returns:
        TeamLead instance with preferred_models for that domain
    """
    domain_str = domain.value if hasattr(domain, "value") else str(domain)
    return _TILEAD_REGISTRY.get(domain_str, SpeedTeamLead())


def list_tileads() -> dict[str, str]:
    """Return a summary of all team leads and their domains."""
    return {
        name: lead.description
        for name, lead in _TILEAD_REGISTRY.items()
    }
