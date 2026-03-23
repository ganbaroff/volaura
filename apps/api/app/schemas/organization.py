"""Organization Pydantic schemas (v2)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OrganizationCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    website_url: str | None = Field(default=None, max_length=500)
    logo_url: str | None = Field(default=None, max_length=500)
    contact_email: str | None = None
    is_verified: bool = False


class OrganizationUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    website_url: str | None = Field(default=None, max_length=500)
    logo_url: str | None = Field(default=None, max_length=500)
    contact_email: str | None = None


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: str
    name: str
    description: str | None = None
    website_url: str | None = None
    logo_url: str | None = None
    contact_email: str | None = None
    is_verified: bool
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


class VolunteerSearchResult(BaseModel):
    volunteer_id: str
    username: str
    display_name: str | None = None
    overall_score: float
    badge_tier: str
    elite_status: bool
    location: str | None = None
    languages: list[str] = []
    similarity: float | None = None     # cosine similarity from pgvector
