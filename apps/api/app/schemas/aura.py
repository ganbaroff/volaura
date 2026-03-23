"""AURA score Pydantic schemas."""

from datetime import datetime

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
    overall_score: float
    badge_tier: str
    elite_status: bool
    competency_scores: dict[str, float]
    reliability_score: float = 0.0
    reliability_status: str = "behavioral"
    events_attended: int = 0
    events_no_show: int = 0
    percentile_rank: float | None = None
    aura_history: list = []
    calculated_at: datetime | None = None
