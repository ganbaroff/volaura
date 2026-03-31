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
    account_type: str = "volunteer"
    visible_to_orgs: bool = False
    org_type: str | None = None
    invited_by_org_id: str | None = None  # GROWTH-2: org attribution from invite link

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip().lower()
        if len(v) < 3 or len(v) > 30:
            raise ValueError("Username must be 3-30 characters")
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Username may only contain letters, numbers, hyphens, underscores")
        return v

    @field_validator("account_type")
    @classmethod
    def validate_account_type(cls, v: str) -> str:
        if v not in ("volunteer", "organization"):
            raise ValueError("account_type must be 'volunteer' or 'organization'")
        return v

    @field_validator("org_type")
    @classmethod
    def validate_org_type(cls, v: str | None) -> str | None:
        if v is not None and v not in ("ngo", "corporate", "government", "startup", "academic", "other"):
            raise ValueError("Invalid org_type")
        return v


class ProfileUpdate(BaseModel):
    display_name: str | None = None
    bio: str | None = None
    location: str | None = None
    languages: list[str] | None = None
    social_links: dict[str, Any] | None = None
    is_public: bool | None = None
    visible_to_orgs: bool | None = None
    # Attribution — set once at registration, read from localStorage UTM capture
    referral_code: str | None = None
    utm_source: str | None = None
    utm_campaign: str | None = None


class ProfileResponse(ProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    avatar_url: str | None = None
    account_type: str = "volunteer"
    visible_to_orgs: bool = False
    org_type: str | None = None
    badge_issued_at: datetime | None = None
    badge_open_badges_url: str | None = None
    created_at: datetime
    updated_at: datetime
    registration_number: int | None = None
    registration_tier: str | None = None  # founding_100 | founding_1000 | early_adopter | standard
    # Subscription fields — present on all profile reads so frontend can gate features
    subscription_status: str = "trial"  # trial | active | expired | cancelled
    trial_ends_at: datetime | None = None
    is_subscription_active: bool = True  # True when status is 'trial' or 'active'


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
    registration_number: int | None = None
    registration_tier: str | None = None  # founding_100 | founding_1000 | early_adopter | standard
    percentile_rank: float | None = None  # GROW-M03: % of public users with lower AURA score


class DiscoverableVolunteer(BaseModel):
    """Volunteer profile visible to org users on the discovery page.

    Only includes volunteers who have opted in (visible_to_orgs=True).
    AURA score joined from aura_scores table.
    """
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    display_name: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    location: str | None = None
    languages: list[str] = []
    # AURA data (None if volunteer hasn't completed any assessment)
    total_score: float | None = None
    badge_tier: str | None = None
