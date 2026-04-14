"""Organization Pydantic schemas (v2)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CollectiveAuraResponse(BaseModel):
    """Aggregated AURA talent pool metrics for an org. Used by Collective AURA Ladders."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    org_id: str
    count: int
    avg_aura: float | None = None  # None when count == 0
    trend: float | None = None  # delta vs 30 days ago; None when insufficient data


class OrganizationCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    website: str | None = Field(default=None, max_length=500)
    logo_url: str | None = Field(default=None, max_length=500)
    contact_email: str | None = None


class OrganizationUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    website: str | None = Field(default=None, max_length=500)
    logo_url: str | None = Field(default=None, max_length=500)
    contact_email: str | None = None


class OrganizationResponse(BaseModel):
    """Public organization response — owner_id intentionally excluded to prevent UUID enumeration."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    name: str
    description: str | None = None
    website: str | None = None
    logo_url: str | None = None
    contact_email: str | None = None
    type: str | None = None
    is_active: bool | None = None
    verified_at: datetime | None = None
    subscription_tier: str | None = None
    trust_score: float | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProfessionalSearchRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

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
    """Assign one or more competency assessments to specific professionals."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    professional_ids: list[str] = Field(..., min_length=1, max_length=100)
    competency_slugs: list[str] = Field(..., min_length=1, max_length=8)
    deadline_days: int = Field(default=14, ge=1, le=90)
    message: str | None = Field(default=None, max_length=500)

    @field_validator("professional_ids")
    @classmethod
    def validate_professional_ids(cls, v: list[str]) -> list[str]:
        import uuid as _uuid

        for pid in v:
            try:
                _uuid.UUID(pid)
            except ValueError:
                raise ValueError(f"Invalid professional ID: {pid}")
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


class ProfessionalSearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    professional_id: str = Field(validation_alias="volunteer_id")
    username: str
    display_name: str | None = None
    overall_score: float  # renamed from total_score for API consistency
    badge_tier: str
    elite_status: bool
    location: str | None = None
    languages: list[str] = []
    similarity: float | None = None  # cosine similarity from pgvector


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
    total_assigned: int  # total assessment sessions created by this org
    total_completed: int  # sessions with status='completed'
    completion_rate: float  # completed / assigned (0.0–1.0)
    avg_aura_score: float | None  # average AURA total_score across completed volunteers
    badge_distribution: BadgeDistribution
    top_professionals: list[OrgProfessionalRow]  # top 5 by AURA score


class OrgProfessionalRow(BaseModel):
    """One professional row in the org dashboard table."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    professional_id: str = Field(validation_alias="volunteer_id")
    username: str
    display_name: str | None = None
    overall_score: float | None = None
    badge_tier: str | None = None
    competencies_completed: int  # how many competencies this user completed for this org
    last_activity: str | None = None  # ISO datetime of last completed session


# ── Intro Requests ─────────────────────────────────────────────────────────────


class IntroRequestCreate(BaseModel):
    professional_id: str
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

    @field_validator("professional_id")
    @classmethod
    def validate_professional_uuid(cls, v: str) -> str:
        import uuid as _uuid

        try:
            _uuid.UUID(v)
        except ValueError:
            raise ValueError("professional_id must be a valid UUID")
        return v


# ── Saved Searches (Sprint 8) ─────────────────────────────────────────────────


class SavedSearchFilters(BaseModel):
    """Mirrors ProfessionalSearchRequest — the JSONB payload stored in org_saved_searches.filters.

    Keeping this as a dedicated model (not reusing VolunteerSearchRequest) prevents drift:
    saved filters never include pagination (limit/offset) and must be stable across versions.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    query: str = Field(default="", max_length=500)
    min_aura: float = Field(default=0.0, ge=0.0, le=100.0)
    badge_tier: str | None = None
    languages: list[str] = Field(default_factory=list)
    location: str | None = Field(default=None, max_length=200)

    @field_validator("badge_tier")
    @classmethod
    def validate_badge_tier(cls, v: str | None) -> str | None:
        if v is not None and v not in ("platinum", "gold", "silver", "bronze"):
            raise ValueError("badge_tier must be platinum, gold, silver, or bronze")
        return v

    @field_validator("languages")
    @classmethod
    def cap_languages(cls, v: list[str]) -> list[str]:
        """Prevent unbounded language arrays."""
        return [lang[:50] for lang in v[:10]]


class SavedSearchCreate(BaseModel):
    """Payload for POST /organizations/{org_id}/saved-searches."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=100)
    filters: SavedSearchFilters
    notify_on_match: bool = True


class SavedSearchUpdate(BaseModel):
    """Payload for PATCH /organizations/{org_id}/saved-searches/{search_id}."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=100)
    notify_on_match: bool | None = None


class SavedSearchOut(BaseModel):
    """Response for a saved search row."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    org_id: str
    name: str
    filters: dict  # JSONB returned as-is from DB
    notify_on_match: bool
    last_checked_at: datetime
    created_at: datetime


class SavedSearchMatchPreview(BaseModel):
    """Match result returned in CEO Telegram notification — lightweight professional summary."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    professional_id: str = Field(validation_alias="volunteer_id")
    display_name: str | None = None
    overall_score: float
    badge_tier: str
    top_competency: str | None = None  # highest-scoring competency slug


class SavedSearchMatchNotification(BaseModel):
    """Structured payload for match notifications — Telegram + ceo-inbox.md."""

    search_id: str
    search_name: str
    org_id: str
    org_name: str
    new_match_count: int
    matches: list[SavedSearchMatchPreview]
    checked_at: datetime


class IntroRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    org_id: str
    professional_id: str = Field(validation_alias="volunteer_id")
    project_name: str
    timeline: str
    message: str | None = None
    status: str
    created_at: datetime
