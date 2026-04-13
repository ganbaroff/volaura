"""Professional discovery schemas — Phase 3 org talent search."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ── Request ────────────────────────────────────────────────────────────────────

VALID_SORT_BY = Literal["score", "events", "recent"]
VALID_ROLE_LEVELS = Literal["professional", "volunteer", "coordinator", "specialist", "manager", "senior_manager"]
VALID_BADGE_TIERS = Literal["Bronze", "Silver", "Gold", "Platinum"]

COMPETENCY_SLUGS = {
    "communication",
    "reliability",
    "english_proficiency",
    "leadership",
    "event_performance",
    "tech_literacy",
    "adaptability",
    "empathy_safeguarding",
}


class DiscoveryRequest(BaseModel):
    """Query parameters for volunteer discovery."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    competency: str | None = Field(
        default=None,
        description="Filter by competency slug. Must be a valid Volaura competency.",
        examples=["communication", "leadership"],
    )
    score_min: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Minimum competency score (0-100). Only applied if `competency` is set.",
    )
    role_level: VALID_ROLE_LEVELS | None = Field(
        default=None,
        description="Filter by highest role level the volunteer has been assessed at.",
    )
    badge_tier: VALID_BADGE_TIERS | None = Field(
        default=None,
        description="Filter by badge tier.",
    )
    sort_by: VALID_SORT_BY = Field(
        default="score",
        description="Sort order: score (total AURA desc), events (events attended desc), recent (last updated desc).",
    )
    # Cursor-based pagination — prevents enumeration attacks
    # Cursor encodes (total_score, volunteer_id) of the LAST item on the previous page.
    after_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Cursor: total_score of last item from previous page.",
    )
    after_id: str | None = Field(
        default=None,
        description="Cursor: professional_id of last item (tiebreaker). Required if after_score provided.",
    )
    limit: int = Field(default=20, ge=1, le=50)

    @field_validator("competency")
    @classmethod
    def validate_competency(cls, v: str | None) -> str | None:
        if v is not None and v not in COMPETENCY_SLUGS:
            raise ValueError(f"Invalid competency slug '{v}'. Valid: {sorted(COMPETENCY_SLUGS)}")
        return v

    @field_validator("after_id")
    @classmethod
    def validate_after_id(cls, v: str | None) -> str | None:
        if v is not None:
            import uuid as _uuid

            try:
                _uuid.UUID(v)
            except ValueError:
                raise ValueError("after_id must be a valid UUID")
        return v


# ── Response ───────────────────────────────────────────────────────────────────


class DiscoveryProfessional(BaseModel):
    """Single professional in discovery results.

    Security (agent review 2026-03-25):
    - display_name: server-side anonymized to "First L." — never trust user-controlled field
    - competency_score: only the REQUESTED competency — not full competency_scores JSONB
    - professional_id: exposed intentionally — used by POST /organizations/{id}/assign-assessments
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    professional_id: str = Field(validation_alias="volunteer_id")
    display_name: str  # server-anonymized: "Leyla A."
    badge_tier: str
    total_score: float
    competency_score: float | None = None  # score for queried competency; null if no filter
    role_level: str | None = None  # most recent assessed role
    events_attended: int = 0
    last_updated: datetime | None = None


class DiscoveryMeta(BaseModel):
    """Pagination metadata for discovery results."""

    returned: int  # items in this page
    limit: int
    has_more: bool  # True if there are more pages
    # Cursors for next page — which fields are populated depends on sort_by:
    #   sort_by=score  → next_after_score + next_after_id
    #   sort_by=events → next_after_events + next_after_id
    #   sort_by=recent → next_after_updated + next_after_id
    next_after_score: float | None = None
    next_after_events: int | None = None
    next_after_updated: str | None = None  # ISO datetime string
    next_after_id: str | None = None


class DiscoveryResponse(BaseModel):
    """Wrapped discovery response following {data, meta} envelope."""

    data: list[DiscoveryProfessional]
    meta: DiscoveryMeta
