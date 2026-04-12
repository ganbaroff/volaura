"""AURA score Pydantic schemas."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class CompetencyScore(BaseModel):
    slug: str
    name_en: str
    name_az: str
    score: float
    weight: float


class AuraScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    volunteer_id: str
    total_score: float  # DB column name — was "overall_score" mismatch
    badge_tier: str
    elite_status: bool
    competency_scores: dict[str, float]
    visibility: str = "public"  # public | badge_only | hidden
    reliability_score: float = 0.0
    reliability_status: str = "pending"
    events_attended: int = 0
    events_no_show: int = 0
    percentile_rank: float | None = None
    effective_score: float | None = None  # decay-adjusted score (computed at request time, not stored)
    aura_history: list = []
    last_updated: datetime | None = None


class AuraEvaluationItem(BaseModel):
    """Per-question evaluation log entry from a completed assessment session."""

    model_config = ConfigDict(from_attributes=True)

    question_id: str | None = None
    concept_scores: dict[str, float]
    evaluation_confidence: str  # high | pattern_matched | unknown
    methodology: str
    concept_details: list[Any] | None = None  # DeCE per-concept breakdown, present when LLM produced quotes


class AuraCompetencyExplanation(BaseModel):
    """Aggregated evaluation data for one competency session."""

    model_config = ConfigDict(from_attributes=True)

    competency_id: str | None = None
    role_level: str
    completed_at: str | None = None
    items_evaluated: int
    evaluations: list[AuraEvaluationItem]


class AuraExplanationResponse(BaseModel):
    """Response for GET /aura/me/explanation — transparent per-competency breakdown."""

    model_config = ConfigDict(from_attributes=True)

    volunteer_id: str
    explanation_count: int
    has_pending_evaluations: bool  # BUG-012: True when degraded answers are queued for LLM re-eval
    pending_reeval_count: int  # BUG-012: number of answers awaiting re-evaluation
    methodology_reference: str
    explanations: list[AuraCompetencyExplanation]


class UpdateVisibilityRequest(BaseModel):
    """Allow user to change their score visibility."""

    visibility: Literal["public", "badge_only", "hidden"]


class SharingPermissionRequest(BaseModel):
    """Grant/revoke sharing permission to an organization."""

    org_id: str
    permission_type: Literal["read_score", "read_full_eval", "export_report"]
    action: Literal["grant", "revoke"]
