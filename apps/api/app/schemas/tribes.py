"""Pydantic v2 schemas for Tribe Streaks."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TribeMemberStatus(BaseModel):
    """Public view of a tribe member — activity only, no scores."""
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    display_name: str
    avatar_url: str | None = None
    active_this_week: bool  # True if completed ≥1 assessment in current ISO week
    # NOTE: no AURA score, no competency details — activity status only (anti-harassment safeguard Risk 1)


class TribeOut(BaseModel):
    """A user's current tribe."""
    model_config = ConfigDict(from_attributes=True)

    tribe_id: str
    expires_at: datetime
    status: Literal["active", "expired", "dissolved"]
    members: list[TribeMemberStatus]  # includes self (always 2-3 members)
    kudos_count_this_week: int  # Q1: 0 = frontend shows "Be the first" CTA, not "0 kudos"
    renewal_requested: bool  # has the current user already requested renewal?


class TribeStreakOut(BaseModel):
    """A user's personal tribe streak — visible only to themselves."""
    model_config = ConfigDict(from_attributes=True)

    current_streak: int
    longest_streak: int
    last_activity_week: str | None  # YYYY-Www
    consecutive_misses_count: int  # 0-2 = crystal fading; 3 = reset happened
    # UI hint: frontend uses consecutive_misses_count to determine crystal fade level
    # 0 = bright crystal, 1 = slightly dim, 2 = dimmer, 3 = just reset (briefly show "streak lost")
    crystal_fade_level: Literal[0, 1, 2]  # computed: min(consecutive_misses_count, 2)


class KudosResponse(BaseModel):
    sent: bool = True
    message: str = "Kudos sent to your tribe."


class OptOutResponse(BaseModel):
    success: bool = True
    message: str = "You have left the tribe. Find a new tribe to continue your streak."


class RenewalResponse(BaseModel):
    renewal_requested: bool = True
    message: str
    all_members_requested: bool = False  # True = tribe will be renewed at expiry


class TribeMatchPreview(BaseModel):
    """Returned to user when they join the matching pool."""
    in_pool: bool = True
    estimated_wait: str = "Your tribe will be matched within 24 hours."


class PoolStatusOut(BaseModel):
    """Whether the user is currently waiting in the matching pool.

    Used by GET /api/tribes/me/pool-status so the frontend can show
    'Finding your tribe...' across page refreshes instead of the join CTA.
    """
    in_pool: bool
    joined_at: str | None = None  # ISO 8601 — None when not in pool


# ── Internal (service-level, not API responses) ───────────────────────────────

class TribeMatchCandidate(BaseModel):
    """Used internally by matching service."""
    user_id: str
    aura_score: float
    assessments_last_30d: int
    previous_co_member_ids: list[str] = Field(default_factory=list)
