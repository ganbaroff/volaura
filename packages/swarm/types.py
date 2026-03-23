"""
Swarm Decision Engine — Type Definitions
All Pydantic v2 models for the universal multi-model decision engine.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StakesLevel(str, Enum):
    LOW = "low"            # 3-5 agents
    MEDIUM = "medium"      # 7-10 agents
    HIGH = "high"          # 10-15 agents
    CRITICAL = "critical"  # 15+ agents


class DomainTag(str, Enum):
    CODE = "code"
    SECURITY = "security"
    BUSINESS = "business"
    UX = "ux"
    ARCHITECTURE = "architecture"
    OPERATIONS = "operations"
    DATA = "data"
    GENERAL = "general"


class PathDefinition(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    description: str
    best_case: str = ""
    worst_case: str = ""
    effort: str = ""  # S / M / L / XL


class SwarmConfig(BaseModel):
    question: str
    context: str = ""
    constraints: str = ""
    paths: dict[str, PathDefinition] | None = None  # None = agents generate paths
    stakes: StakesLevel = StakesLevel.MEDIUM
    domain: DomainTag = DomainTag.GENERAL
    temperature: float = 0.7
    max_agents: int = 15
    timeout_seconds: float = 30.0
    use_calibration: bool = True


class DimensionScores(BaseModel):
    technical: float = 0.0
    user_impact: float = 0.0
    dev_speed: float = 0.0
    flexibility: float = 0.0
    risk: float = 0.0  # 0 = catastrophic failure likely, 10 = very safe

    def total(self) -> float:
        return (
            self.technical
            + self.user_impact
            + self.dev_speed
            + self.flexibility
            + self.risk
        )


class AgentResult(BaseModel):
    agent_id: str              # e.g. "gemini-0", "groq-1"
    provider: str              # e.g. "gemini", "groq"
    model: str                 # e.g. "gemini-2.5-flash", "llama-3.3-70b"
    perspective: str = ""      # e.g. "pragmatist", "security"
    scores: dict[str, DimensionScores] = {}
    concerns: dict[str, str] = {}
    winner: str = ""
    reason: str = ""
    confidence: float = 0.0
    latency_ms: int = 0
    cost_estimate: float = 0.0
    json_valid: bool = False
    error: str | None = None
    raw_response: str = ""


class DivergenceReport(BaseModel):
    winner_votes: dict[str, int] = {}
    top_winner: str = ""
    consensus_strength: float = 0.0  # 0.0-1.0
    is_genuine_consensus: bool = False
    high_divergence: bool = False     # > 0.6 threshold
    split_paths: list[str] = []


class ScalingEvent(BaseModel):
    round: int
    reason: str           # e.g. "divergence 0.65 > 0.6"
    agents_added: int
    provider_used: str


class SwarmReport(BaseModel):
    decision_id: str = ""
    config: SwarmConfig
    agents_used: int = 0
    agents_succeeded: int = 0
    agent_results: list[AgentResult] = []
    weighted_scores: dict[str, float] = {}  # path_id -> 0-50
    divergence: DivergenceReport = Field(default_factory=DivergenceReport)
    winner: str = ""
    winner_score: float = 0.0
    passed_confidence_gate: bool = False    # score >= 35
    scaling_events: list[ScalingEvent] = []
    synthesis: dict[str, Any] | None = None     # LLM synthesis result (MoA-style)
    provider_latencies: dict[str, float] = {}  # provider -> avg ms
    total_cost_estimate: float = 0.0
    total_latency_ms: int = 0
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ModelProfile(BaseModel):
    model_name: str
    provider: str
    base_weight: float = 1.0
    domain_weights: dict[str, float] = {}  # DomainTag.value -> weight
    total_evaluations: int = 0
    correct_predictions: int = 0
    accuracy: float = 0.5
    avg_latency_ms: float = 0.0
    avg_json_compliance: float = 1.0
    last_updated: str = ""

    def get_weight(self, domain: DomainTag) -> float:
        """Get effective weight for a domain. Falls back to base_weight."""
        return self.domain_weights.get(domain.value, self.base_weight)


class CalibrationEntry(BaseModel):
    decision_id: str
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    domain: DomainTag = DomainTag.GENERAL
    predicted_winner: str = ""
    predicted_score: float = 0.0
    actual_outcome: str = ""  # "better" | "worse" | "as_expected"
    models_correct: list[str] = []
    models_wrong: list[str] = []


class ProviderInfo(BaseModel):
    """Metadata about a provider's capabilities and limits."""
    name: str
    model: str
    cost_per_mtok_input: float = 0.0
    cost_per_mtok_output: float = 0.0
    rate_limit_rpm: int = 15
    is_free: bool = True
    supports_json_mode: bool = True
    priority: int = 0  # lower = preferred (free first)
