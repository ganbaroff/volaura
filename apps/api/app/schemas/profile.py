"""Profile Pydantic schemas (v2)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class ProfileBase(BaseModel):
    username: str
    display_name: str | None = None
    bio: str | None = None
    location: str | None = None
    languages: list[str] = []
    social_links: dict[str, Any] = {}
    is_public: bool = True


class ProfileCreate(ProfileBase):
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip().lower()
        if len(v) < 3 or len(v) > 30:
            raise ValueError("Username must be 3-30 characters")
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Username may only contain letters, numbers, hyphens, underscores")
        return v


class ProfileUpdate(BaseModel):
    display_name: str | None = None
    bio: str | None = None
    location: str | None = None
    languages: list[str] | None = None
    social_links: dict[str, Any] | None = None
    is_public: bool | None = None


class ProfileResponse(ProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    avatar_url: str | None = None
    badge_issued_at: datetime | None = None
    badge_open_badges_url: str | None = None
    created_at: datetime
    updated_at: datetime


class PublicProfileResponse(BaseModel):
    """Minimal public profile for sharing — no sensitive fields."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    display_name: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    location: str | None = None
    languages: list[str] = []
    badge_issued_at: datetime | None = None
