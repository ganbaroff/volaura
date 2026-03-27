"""Pydantic v2 schemas for character_state (cross-product event system).

Sprint A0: character_state as Thalamus.
Routes all cross-product events: Volaura, MindShift, Life Simulator, BrandedBy.
"""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# Valid event types — enforced at API layer
EventType = Literal[
    "crystal_earned",
    "crystal_spent",
    "skill_verified",
    "xp_earned",
    "stat_changed",
    "login_streak",
    "milestone_reached",
]

# Valid source products
SourceProduct = Literal["volaura", "mindshift", "lifesim", "brandedby"]


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


class CharacterStateOut(BaseModel):
    """Computed character state — derived from all events + crystal ledger.

    This is the 'thalamus' view: one read shows the full cross-product state.
    """

    user_id: UUID
    crystal_balance: int = Field(ge=0, description="Current crystal balance from ledger")
    xp_total: int = Field(ge=0, description="Lifetime XP earned across all products")
    verified_skills: list[str] = Field(
        default_factory=list,
        description="Volaura competency slugs verified by assessment",
    )
    login_streak: int = Field(ge=0, description="Current consecutive login days")
    event_count: int = Field(ge=0, description="Total events in history")
    last_event_at: datetime | None = None
    computed_at: datetime
