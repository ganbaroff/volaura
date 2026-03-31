"""Expert verification Pydantic schemas (v2)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

VALID_COMPETENCY_IDS = frozenset({
    "communication",
    "reliability",
    "english_proficiency",
    "leadership",
    "event_performance",
    "tech_literacy",
    "adaptability",
    "empathy_safeguarding",
})


class CreateVerificationLinkRequest(BaseModel):
    """Request body for POST /api/profiles/{volunteer_id}/verification-link."""

    verifier_name: str = Field(..., min_length=2, max_length=100)
    verifier_org: str | None = Field(None, max_length=100)
    competency_id: str

    @field_validator("verifier_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("verifier_org")
    @classmethod
    def validate_org(cls, v: str | None) -> str | None:
        return v.strip() if v else None

    @field_validator("competency_id")
    @classmethod
    def validate_competency(cls, v: str) -> str:
        if v not in VALID_COMPETENCY_IDS:
            raise ValueError(f"Invalid competency_id. Must be one of: {sorted(VALID_COMPETENCY_IDS)}")
        return v


class CreateVerificationLinkResponse(BaseModel):
    """Returned when a verification link is created."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    token: str
    verify_url: str          # Full URL to share: https://volaura.az/{locale}/verify/{token}
    expires_at: datetime
    verifier_name: str
    verifier_org: str | None
    competency_id: str


class VerificationTokenInfo(BaseModel):
    """Returned by GET /api/verify/{token} — public, no auth required."""
    model_config = ConfigDict(from_attributes=True)

    volunteer_display_name: str
    volunteer_username: str
    volunteer_avatar_url: str | None
    verifier_name: str
    verifier_org: str | None
    competency_id: str


class SubmitVerificationRequest(BaseModel):
    """Request body for POST /api/verify/{token}."""

    rating: float = Field(..., ge=1.0, le=5.0)
    comment: str | None = Field(None, max_length=500)

    @field_validator("comment")
    @classmethod
    def sanitize_comment(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        return v if v else None


class SubmitVerificationResponse(BaseModel):
    """Returned after successful verification submission."""

    status: Literal["verified"] = "verified"
    volunteer_display_name: str
    competency_id: str
    rating: float


class TokenErrorCode(BaseModel):
    """Structured error for token validation failures."""

    code: Literal[
        "TOKEN_INVALID",
        "TOKEN_EXPIRED",
        "TOKEN_ALREADY_USED",
    ]
    message: str
