"""Event and Registration Pydantic schemas (v2)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


# ── Events ────────────────────────────────────────────────────────────────────

class EventCreate(BaseModel):
    title_en: str
    title_az: str
    description_en: str | None = None
    description_az: str | None = None
    event_type: str | None = None
    location: str | None = None
    location_coords: dict[str, float] | None = None
    start_date: datetime
    end_date: datetime
    capacity: int | None = None
    required_min_aura: float = 0.0
    required_languages: list[str] = []
    status: str = "draft"
    is_public: bool = True

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"draft", "open", "closed", "cancelled", "completed"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


class EventUpdate(BaseModel):
    title_en: str | None = None
    title_az: str | None = None
    description_en: str | None = None
    description_az: str | None = None
    event_type: str | None = None
    location: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    capacity: int | None = None
    required_min_aura: float | None = None
    required_languages: list[str] | None = None
    status: str | None = None
    is_public: bool | None = None


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    title_en: str
    title_az: str
    description_en: str | None = None
    description_az: str | None = None
    event_type: str | None = None
    location: str | None = None
    location_coords: dict[str, Any] | None = None
    start_date: datetime
    end_date: datetime
    capacity: int | None = None
    required_min_aura: float = 0.0
    required_languages: list[str] = []
    status: str
    is_public: bool
    created_at: datetime
    updated_at: datetime


# ── Registrations ─────────────────────────────────────────────────────────────

class RegistrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_id: str
    volunteer_id: str
    status: str
    registered_at: datetime
    checked_in_at: datetime | None = None
    check_in_code: str | None = None
    coordinator_rating: int | None = None
    coordinator_feedback: str | None = None
    volunteer_rating: int | None = None
    volunteer_feedback: str | None = None


class CheckInRequest(BaseModel):
    check_in_code: str


class EventAttendeeRow(BaseModel):
    """Enriched attendee for org dashboard — joins profile + AURA."""
    model_config = ConfigDict(from_attributes=True)

    registration_id: str
    volunteer_id: str
    status: str
    registered_at: datetime
    checked_in_at: datetime | None = None
    display_name: str | None = None
    username: str | None = None
    total_score: float | None = None
    badge_tier: str | None = None


class CoordinatorRatingRequest(BaseModel):
    registration_id: str
    rating: int
    feedback: str | None = None

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: int) -> int:
        if not 1 <= v <= 5:
            raise ValueError("rating must be between 1 and 5")
        return v


class VolunteerRatingRequest(BaseModel):
    rating: int
    feedback: str | None = None

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: int) -> int:
        if not 1 <= v <= 5:
            raise ValueError("rating must be between 1 and 5")
        return v
