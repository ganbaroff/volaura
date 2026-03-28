"""Organization Pydantic schemas (v2)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OrganizationCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    website: str | None = Field(default=None, max_length=500)
    logo_url: str | None = Field(default=None, max_length=500)
    contact_email: str | None = None


class OrganizationUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    website: str | None = Field(default=None, max_length=500)
    logo_url: str | None = Field(default=None, max_length=500)
    contact_email: str | None = None


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: str
    name: str
    description: str | None = None
    website: str | None = None
    logo_url: str | None = None
    contact_email: str | None = None
    verified_at: datetime | None = None
    subscription_tier: str
    trust_score: float | None = None
    created_at: datetime
    updated_at: datetime


class VolunteerSearchRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    query: str = Field(..., min_length=1, max_length=500)
    min_aura: float = 0.0
    badge_tier: str | None = None
    languages: list[str] = []
    location: str | None = None
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    @field_validator("badge_tier")
    @classmethod
    def validate_badge_tier(cls, v: str | None) -> str | None:
        if v is not None and v not in ("platinum", "gold", "silver", "bronze"):
            raise ValueError("Invalid badge tier. Must be: platinum, gold, silver, bronze")
        return v


class AssignAssessmentRequest(BaseModel):
    """Assign one or more competency assessments to specific volunteers."""
    model_config = ConfigDict(from_attributes=True)

    volunteer_ids: list[str] = Field(..., min_length=1, max_length=100)
    competency_slugs: list[str] = Field(..., min_length=1, max_length=8)
    deadline_days: int = Field(default=14, ge=1, le=90)
    message: str | None = Field(default=None, max_length=500)

    @field_validator("volunteer_ids")
    @classmethod
    def validate_volunteer_ids(cls, v: list[str]) -> list[str]:
        import uuid as _uuid
        for vid in v:
            try:
                _uuid.UUID(vid)
            except ValueError:
                raise ValueError(f"Invalid volunteer ID: {vid}")
        return v

    @field_validator("competency_slugs")
    @classmethod
    def validate_competency_slugs(cls, v: list[str]) -> list[str]:
        import re
        slug_re = re.compile(r"^[a-z][a-z0-9_]{1,49}$")
        for slug in v:
            if not slug_re.match(slug):
                raise ValueError(f"Invalid competency slug: {slug}")
        return v


class AssignmentResponse(BaseModel):
    """Result of assignment operation."""
    assigned_count: int
    skipped_count: int
    errors: list[str] = []
    assignments: list[dict] = []


class VolunteerSearchResult(BaseModel):
    volunteer_id: str
    username: str
    display_name: str | None = None
    overall_score: float               # renamed from total_score for API consistency
    badge_tier: str
    elite_status: bool
    location: str | None = None
    languages: list[str] = []
    similarity: float | None = None     # cosine similarity from pgvector


# ── Org dashboard schemas ──────────────────────────────────────────────────────

class BadgeDistribution(BaseModel):
    platinum: int = 0
    gold: int = 0
    silver: int = 0
    bronze: int = 0
    none: int = 0


class OrgDashboardStats(BaseModel):
    """Aggregate stats for the org management dashboard."""
    org_id: str
    org_name: str
    total_assigned: int          # total assessment sessions created by this org
    total_completed: int         # sessions with status='completed'
    completion_rate: float       # completed / assigned (0.0–1.0)
    avg_aura_score: float | None # average AURA total_score across completed volunteers
    badge_distribution: BadgeDistribution
    top_volunteers: list["OrgVolunteerRow"]  # top 5 by AURA score


class OrgVolunteerRow(BaseModel):
    """One volunteer row in the org dashboard table."""
    volunteer_id: str
    username: str
    display_name: str | None = None
    overall_score: float | None = None
    badge_tier: str | None = None
    competencies_completed: int    # how many competencies this user completed for this org
    last_activity: str | None = None   # ISO datetime of last completed session



# ── Intro Requests ─────────────────────────────────────────────────────────────

class IntroRequestCreate(BaseModel):
    volunteer_id: str
    project_name: str = Field(..., min_length=2, max_length=200)
    timeline: str
    message: str | None = Field(default=None, max_length=500)

    @field_validator("timeline")
    @classmethod
    def validate_timeline(cls, v: str) -> str:
        allowed = {"urgent", "normal", "flexible"}
        if v not in allowed:
            raise ValueError(f"timeline must be one of {allowed}")
        return v

    @field_validator("volunteer_id")
    @classmethod
    def validate_volunteer_uuid(cls, v: str) -> str:
        import uuid as _uuid
        try:
            _uuid.UUID(v)
        except ValueError:
            raise ValueError("volunteer_id must be a valid UUID")
        return v


class IntroRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    org_id: str
    volunteer_id: str
    project_name: str
    timeline: str
    message: str | None = None
    status: str
    created_at: datetime
