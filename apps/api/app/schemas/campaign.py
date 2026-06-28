"""Screening campaign schemas (Pydantic v2) — B2B org screening flow.

Org creates a campaign (vacancy), shares one invite link, candidates join
via the link and take assigned assessments, org reads a ranked report.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

VALID_CAMPAIGN_STATUSES = ("active", "closed", "archived")


class CampaignCreate(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    competency_slugs: list[str] = Field(min_length=1, max_length=8)
    deadline_days: int = Field(default=14, ge=1, le=60)
    candidate_cap: int = Field(default=500, ge=1, le=2000)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Title must be at least 3 characters after trimming")
        return v

    @field_validator("description")
    @classmethod
    def normalize_description(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        return v or None

    @field_validator("competency_slugs")
    @classmethod
    def dedupe_slugs(cls, v: list[str]) -> list[str]:
        seen: list[str] = []
        for slug in v:
            slug = slug.strip().lower()
            if slug and slug not in seen:
                seen.append(slug)
        if not seen:
            raise ValueError("At least one competency is required")
        return seen


class CampaignUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in VALID_CAMPAIGN_STATUSES:
            raise ValueError(f"Status must be one of {VALID_CAMPAIGN_STATUSES}")
        return v


class CampaignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    org_id: str
    title: str
    description: str | None = None
    competency_slugs: list[str]
    invite_token: str
    status: str
    deadline_days: int
    candidate_cap: int
    created_at: datetime
    candidate_count: int = 0
    completed_count: int = 0


class PublicCampaignResponse(BaseModel):
    """Safe subset for the public invite landing page (no auth)."""

    title: str
    description: str | None = None
    org_name: str
    org_logo_url: str | None = None
    competency_slugs: list[str]
    status: str
    deadline_days: int
    is_full: bool = False


class JoinedSession(BaseModel):
    session_id: str
    competency_slug: str
    status: str


class CampaignJoinResponse(BaseModel):
    campaign_id: str
    already_joined: bool
    sessions: list[JoinedSession]


class CandidateReportRow(BaseModel):
    professional_id: str
    display_name: str | None = None
    username: str | None = None
    avatar_url: str | None = None
    joined_at: datetime
    completed_sessions: int
    assigned_sessions: int
    campaign_score: float | None = None
    badge_tier: str | None = None
    competency_scores: dict[str, float] = Field(default_factory=dict)


class CampaignReportResponse(BaseModel):
    campaign: CampaignResponse
    candidates: list[CandidateReportRow]
