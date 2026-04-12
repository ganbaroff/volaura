"""
MiroFish Swarm Decision Engine — Multi-provider AI coordination.

Core modules: engine.py (SwarmEngine), autonomous_run.py (daily agent runs),
coordinator.py (DAG task routing), backlog.py (task tracking).

Usage:
    from packages.swarm import SwarmEngine, SwarmConfig, StakesLevel
    engine = SwarmEngine()
    report = await engine.quick_decide("Redis vs Postgres?")
"""

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
from .prompts import get_team_context, load_prompt_module
from .research import (
    ResearchFindings,
    WebResearcher,
    collect_and_prioritize_research,
    inject_findings_into_memory,
)
from .structured_memory import (
    ExperienceEntry,
    FailureEntry,
    MemoryEntry,
    OpinionEntry,
    StructuredMemory,
    WorldFact,
)
from .swarm_types import (
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
    "HiveExaminer",
    "AgentProfile",
    "AgentStatus",
    "ExamResult",
    "ProgressSnapshot",
    "TeamLeadReport",
    "HiveStatus",
    "SwarmEngine",
    "SwarmConfig",
    "StakesLevel",
    "DomainTag",
    "PathDefinition",
    "PathProposal",
    "ResearchRequest",
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
    "MiddlewareChain",
    "SwarmMiddleware",
    "LoopDetectionMiddleware",
    "ResponseDedupMiddleware",
    "ContextBudgetMiddleware",
    "TimeoutGuardMiddleware",
    "TokenCountingMiddleware",
    "StructuredMemory",
    "MemoryEntry",
    "WorldFact",
    "ExperienceEntry",
    "OpinionEntry",
    "FailureEntry",
]
