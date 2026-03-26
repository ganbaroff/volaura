"""AURA score Pydantic schemas."""

from datetime import datetime
from typing import Literal

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


class UpdateVisibilityRequest(BaseModel):
    """Allow user to change their score visibility."""
    visibility: Literal["public", "badge_only", "hidden"]


class SharingPermissionRequest(BaseModel):
    """Grant/revoke sharing permission to an organization."""
    org_id: str
    permission_type: Literal["read_score", "read_full_eval", "export_report"]
    action: Literal["grant", "revoke"]
