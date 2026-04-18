"""
MiroFish Swarm Decision Engine — Multi-provider AI coordination.

Core modules: engine.py (SwarmEngine), autonomous_run.py (daily agent runs),
coordinator.py (DAG task routing), backlog.py (task tracking).

Registry SSOT: the authoritative count of swarm perspectives is
`len(autonomous_run.PERSPECTIVES)` — currently 13 (5 wave-0, 4 wave-1,
3 wave-2, 1 wave-3). Use `registered_perspectives_count()` below to read
it without pulling in autonomous_run's heavy module-level side effects
(loguru, dotenv, sys.path manipulation). Any doc or code claiming a
different number (8, 44, "44 agents", "5 agents") is wrong unless it
explicitly refers to a different registry (skill files, .claude/agents/,
or the "44 AI agents" brand-positioning line used in public content).

Usage:
    from packages.swarm import SwarmEngine, SwarmConfig, StakesLevel
    from packages.swarm import registered_perspectives_count
    engine = SwarmEngine()
    report = await engine.quick_decide("Redis vs Postgres?")
    print(registered_perspectives_count())  # 13
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

def registered_perspectives_count() -> int:
    """Return the count of swarm perspectives registered in autonomous_run.PERSPECTIVES.

    SSOT for the "how many swarm agents do we have?" question. Lazy-imports
    autonomous_run to avoid pulling in its module-level side effects
    (dotenv, loguru, sys.path manipulation) at package load time.

    Returns:
        int: Current registered perspective count (expected: 13 as of 2026-04-18).
    """
    from .autonomous_run import PERSPECTIVES
    return len(PERSPECTIVES)


__all__ = [
    "HiveExaminer",
    "AgentProfile",
    "AgentStatus",
    "ExamResult",
    "ProgressSnapshot",
    "TeamLeadReport",
    "HiveStatus",
    "registered_perspectives_count",
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
