"""
MiroFish Swarm Decision Engine v2
Universal multi-model AI decision maker with:
  - 14+ models from 8 families (auto-discovered)
  - Tournament groups for HIGH+ stakes
  - Skill augmentation (agents borrow skills from library)
  - Agent memory (models learn from past experiences)
  - Innovation field (every agent proposes 1 creative idea)
  - Self-learning calibration

Usage:
    from packages.swarm import SwarmEngine, SwarmConfig, StakesLevel
    engine = SwarmEngine()
    report = await engine.quick_decide("Redis vs Postgres?")
"""

from .engine import SwarmEngine
from .types import (
    AgentResult,
    CalibrationEntry,
    DimensionScores,
    DivergenceReport,
    DomainTag,
    ModelProfile,
    PathDefinition,
    StakesLevel,
    SwarmConfig,
    SwarmReport,
)

__all__ = [
    "SwarmEngine",
    "SwarmConfig",
    "StakesLevel",
    "DomainTag",
    "PathDefinition",
    "SwarmReport",
    "AgentResult",
    "DivergenceReport",
    "DimensionScores",
    "ModelProfile",
    "CalibrationEntry",
]
