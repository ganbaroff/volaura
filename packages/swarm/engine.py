"""
SwarmEngine v2 — full architecture:
  - Auto-discovery of all available models (14+ from discovered_models.json)
  - Tournament mode: 4 groups x 4 models for HIGH+ stakes
  - Skill augmentation: agents borrow skills from library
  - Agent memory: models learn from past experiences
  - Innovation field: every agent proposes 1 creative idea
  - Debate: triggered within groups on divergence > 50%
  - LLM synthesis: MoA-style cross-group aggregation
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from loguru import logger

from .agent_memory import AgentMemory
from .memory import DecisionMemory
from .pm import PMAgent
from .providers import ProviderRegistry
from .providers.base import LLMProvider
from .providers.dynamic import load_discovered_providers
from .skills import SkillLibrary
from .types import (
    CalibrationEntry,
    DomainTag,
    StakesLevel,
    SwarmConfig,
    SwarmReport,
)


class SwarmEngine:
    """Universal multi-model decision engine.

    Usage:
        engine = SwarmEngine()
        report = await engine.quick_decide("Redis vs Postgres?")
        print(report.winner, report.winner_score)
    """

    def __init__(
        self,
        env: dict[str, str] | None = None,
        data_dir: Path | None = None,
        project_root: Path | None = None,
    ):
        env = env or dict(os.environ)
        self.memory = DecisionMemory(data_dir)
        self.agent_memory = AgentMemory(data_dir)
        self.skills = SkillLibrary(project_root)

        # Auto-discover: try discovered_models.json first, fallback to static providers
        self.providers = load_discovered_providers(env)
        if not self.providers:
            self.registry = ProviderRegistry()
            self.providers = self.registry.discover(env)
        else:
            self.registry = ProviderRegistry()
            logger.info(
                "Loaded {n} providers from discovered_models.json",
                n=len(self.providers),
            )

        self.pm = PMAgent(self.registry, self.memory, self.skills, self.agent_memory)

        # Log summary
        free = [p for p in self.providers if p.is_free()]
        paid = [p for p in self.providers if not p.is_free()]
        logger.info(
            "SwarmEngine v2: {n} providers ({f} free, {p} paid)",
            n=len(self.providers), f=len(free), p=len(paid),
        )

    async def decide(self, config: SwarmConfig) -> SwarmReport:
        """Make a decision. Returns the full SwarmReport."""
        if not self.providers:
            logger.error("No providers available.")
            return SwarmReport(config=config)

        report = await self.pm.run(config, self.providers)

        # Store in memory
        decision_id = self.memory.store_decision(report)
        report.decision_id = decision_id

        # Log agent experiences
        for r in report.agent_results:
            if r.json_valid and not r.error:
                self.agent_memory.log_experience(
                    model=r.model,
                    task_summary=config.question[:200],
                    skill_used=r.raw_response[:50] if "skill_used" in r.raw_response else None,
                    skill_helpful=None,
                    chose_winner=r.winner,
                    was_correct=None,  # calibrate later
                    self_note=r.reason[:200],
                )

        logger.info(
            "Decision: winner={w} score={s}/50 agents={a}/{t} latency={ms}ms id={id}",
            w=report.winner, s=report.winner_score,
            a=report.agents_succeeded, t=report.agents_used,
            ms=report.total_latency_ms, id=decision_id,
        )

        return report

    async def quick_decide(
        self,
        question: str,
        stakes: str = "medium",
        context: str = "",
        domain: str = "general",
    ) -> SwarmReport:
        """Convenience: just a question, minimal config."""
        config = SwarmConfig(
            question=question,
            stakes=StakesLevel(stakes),
            context=context,
            domain=DomainTag(domain),
        )
        return await self.decide(config)

    def calibrate(
        self, decision_id: str, actual_outcome: str
    ) -> CalibrationEntry | None:
        """After observing outcome, calibrate model weights."""
        return self.memory.calibrate(decision_id, actual_outcome)

    def get_competency_matrix(self) -> dict[str, dict[str, float]]:
        return self.memory.get_competency_matrix()

    def get_available_providers(self) -> list[str]:
        return [p.get_provider_name() for p in self.providers]

    def get_provider_stats(self) -> list[dict[str, Any]]:
        return [
            {
                "name": p.get_provider_name(),
                "model": p.get_model_name(),
                "cost_per_mtok": p.get_cost_per_mtok(),
                "rate_limit_rpm": p.get_rate_limit_rpm(),
                "is_free": p.is_free(),
            }
            for p in self.providers
        ]

    def get_skill_improvements(self) -> list[dict]:
        """Get pending skill improvements suggested by agents."""
        return self.skills.get_pending_improvements()

    def get_agent_stats(self) -> dict[str, dict]:
        """Get experience stats for all models."""
        stats = {}
        for p in self.providers:
            model = p.get_model_name()
            stats[model] = self.agent_memory.get_model_stats(model)
        return stats
