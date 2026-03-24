"""
MiroFish Swarm Decision Engine v5 — "Hive Architecture"
Universal multi-model AI decision maker with:
  - 14+ models from 8 families (auto-discovered)
  - Middleware architecture (loop detection, dedup, budget, timeout, token counting)
  - Parallel dispatch with per-provider timeouts + smart early exit
  - Skill augmentation (agents borrow skills from library)
  - Agent memory (models learn from past experiences)
  - Self-learning calibration (±5% domain weights)
  - Innovation field (every agent proposes 1 creative idea)

v4 additions (Eureka):
  - Reasoning Graph: agents see each other's structured reasoning between rounds
  - Structured Memory: 4-network system (World/Experience/Opinion/Failure)
  - Token Counting: real cost tracking per provider
  - Failure Network: cross-agent failure pattern learning (novel — no existing system does this)

v5 additions (Hive):
  - AgentHive: per-agent lifecycle management (PROBATIONARY→MEMBER→SENIOR→LEAD)
  - Competency exams: retrospective analysis at PROBATIONARY_DECISIONS and every 20 decisions
  - Onboarding: new agents receive World facts, Failure patterns, Opinions before first decision
  - Team leads: best performer per group elected dynamically, gets 1.2x weight
  - Progress history: append-only JSONL per agent showing development trajectory
  - Hive weight multipliers stacked on calibration weights in score aggregation

Usage:
    from packages.swarm import SwarmEngine, SwarmConfig, StakesLevel
    engine = SwarmEngine()
    report = await engine.quick_decide("Redis vs Postgres?")
    engine.print_hive_report()
    print(engine.get_agent_profile("gemini-2.5-flash"))
"""

from .autonomous_upgrade import AutonomousUpgradeProtocol, UpgradeProposal, UpgradeResult
from .prompts import load_prompt_module, get_team_context
from .research import WebResearcher, ResearchFindings, collect_and_prioritize_research, inject_findings_into_memory
from .agent_hive import (
    AgentProfile,
    AgentStatus,
    ExamResult,
    HiveExaminer,
    HiveStatus,
    ProgressSnapshot,
    TeamLeadReport,
)
from .engine import SwarmEngine
from .middleware import (
    ContextBudgetMiddleware,
    LoopDetectionMiddleware,
    MiddlewareChain,
    ResponseDedupMiddleware,
    SwarmMiddleware,
    TimeoutGuardMiddleware,
    TokenCountingMiddleware,
)
from .reasoning_graph import (
    GraphAggregation,
    ReasoningGraph,
    ReasoningNode,
    RevisionRecord,
)
from .structured_memory import (
    ExperienceEntry,
    FailureEntry,
    MemoryEntry,
    OpinionEntry,
    StructuredMemory,
    WorldFact,
)
from .types import (
    AgentResult,
    CalibrationEntry,
    DimensionScores,
    DivergenceReport,
    DomainTag,
    ModelProfile,
    PathDefinition,
    PathProposal,
    ResearchRequest,
    StakesLevel,
    SwarmConfig,
    SwarmReport,
)

__all__ = [
    # v5 Autonomous Upgrade
    "AutonomousUpgradeProtocol",
    "UpgradeProposal",
    "UpgradeResult",
    # v5 Hive
    "HiveExaminer",
    "AgentProfile",
    "AgentStatus",
    "ExamResult",
    "ProgressSnapshot",
    "TeamLeadReport",
    "HiveStatus",
    # Core
    "SwarmEngine",
    "SwarmConfig",
    "StakesLevel",
    "DomainTag",
    "PathDefinition",
    "PathProposal",
    "ResearchRequest",
    # v7 Research Autonomy
    "WebResearcher",
    "ResearchFindings",
    "collect_and_prioritize_research",
    "inject_findings_into_memory",
    "SwarmReport",
    "AgentResult",
    "DivergenceReport",
    "DimensionScores",
    "ModelProfile",
    "CalibrationEntry",
    # Middleware
    "MiddlewareChain",
    "SwarmMiddleware",
    "LoopDetectionMiddleware",
    "ResponseDedupMiddleware",
    "ContextBudgetMiddleware",
    "TimeoutGuardMiddleware",
    "TokenCountingMiddleware",
    # Reasoning Graph (v4)
    "ReasoningGraph",
    "ReasoningNode",
    "RevisionRecord",
    "GraphAggregation",
    # Structured Memory (v4)
    "StructuredMemory",
    "MemoryEntry",
    "WorldFact",
    "ExperienceEntry",
    "OpinionEntry",
    "FailureEntry",
]
