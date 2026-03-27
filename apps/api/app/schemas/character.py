"""Pydantic v2 schemas for character_state (cross-product event system).

Sprint A0: character_state as Thalamus.
Routes all cross-product events: Volaura, MindShift, Life Simulator, BrandedBy.
"""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# Valid event types — enforced at both API (here) and DB (CHECK constraint)
EventType = Literal[
    "crystal_earned",
    "crystal_spent",
    "skill_verified",
    "skill_unverified",   # revokes a previously verified skill
    "xp_earned",
    "stat_changed",       # Life Simulator character stat update
    "login_streak",
    "milestone_reached",
]

# Valid source products — enforced at both API and DB
SourceProduct = Literal["volaura", "mindshift", "lifesim", "brandedby"]

# Daily crystal cap per source — prevents login farming
DAILY_CRYSTAL_CAP: dict[str, int] = {
    "daily_login": 15,
}


class CharacterEventCreate(BaseModel):
    """Payload for POST /api/character/events."""

    model_config = ConfigDict(str_strip_whitespace=True)

    event_type: EventType
    payload: dict[str, Any] = Field(default_factory=dict)
    source_product: SourceProduct

    @field_validator("payload")
    @classmethod
    def inject_schema_version(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Always include schema version for forward compatibility."""
        v.setdefault("_schema_version", 1)
        return v


class CharacterEventOut(BaseModel):
    """Response for a stored character event."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    event_type: str
    payload: dict[str, Any]
    source_product: str
    created_at: datetime


class VerifiedSkillOut(BaseModel):
    """A single verified skill entry in the character state."""

    slug: str
    aura_score: float | None = None
    badge_tier: str | None = None


class CharacterStateOut(BaseModel):
    """Computed character state — derived from all events + crystal ledger.

    This is the 'thalamus' view: one read shows the full cross-product state.
    All four products read from this — Volaura, MindShift, Life Simulator, BrandedBy.
    """

    user_id: UUID
    crystal_balance: int = Field(
        ge=0,
        description="Current crystal balance (floored at 0 — prevented from going negative at write time)",
    )
    xp_total: int = Field(ge=0, description="Lifetime XP earned across all products")
    verified_skills: list[VerifiedSkillOut] = Field(
        default_factory=list,
        description="Volaura competency slugs verified by assessment, with score and badge tier",
    )
    character_stats: dict[str, int] = Field(
        default_factory=dict,
        description="Life Simulator character stats — latest value per stat key (e.g. strength, intelligence)",
    )
    login_streak: int = Field(ge=0, description="Current consecutive login days")
    event_count: int = Field(ge=0, description="Total events in history")
    last_event_at: datetime | None = None
    computed_at: datetime
