"""Organization invite schemas (Pydantic v2) for CSV bulk invite."""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


# Strict email regex — rejects formula injection patterns (=, +, -, @)
_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

# Characters that trigger formula injection in spreadsheets
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r", "\n")


def _sanitize_cell(value: str | None) -> str | None:
    """Strip formula injection prefixes and whitespace from CSV cell values."""
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    # Prefix dangerous characters with single quote (Excel convention)
    if value.startswith(_FORMULA_PREFIXES):
        value = f"'{value}"
    return value


class InviteRowInput(BaseModel):
    """Validates a single row from the CSV upload."""

    model_config = ConfigDict(from_attributes=True)

    email: str = Field(..., min_length=5, max_length=254)
    display_name: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=30)
    skills: str | None = Field(default=None, max_length=500)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not _EMAIL_RE.match(v):
            raise ValueError(f"Invalid email format: {v}")
        return v

    @field_validator("display_name", mode="before")
    @classmethod
    def sanitize_display_name(cls, v: str | None) -> str | None:
        return _sanitize_cell(v)

    @field_validator("phone", mode="before")
    @classmethod
    def sanitize_phone(cls, v: str | None) -> str | None:
        v = _sanitize_cell(v)
        if v is not None:
            # Strip non-phone characters except + and digits
            cleaned = re.sub(r"[^\d+\-() ]", "", v)
            if len(cleaned) < 7:
                raise ValueError(f"Phone too short: {v}")
            return cleaned
        return None

    @field_validator("skills", mode="before")
    @classmethod
    def sanitize_skills(cls, v: str | None) -> str | None:
        return _sanitize_cell(v)

    def to_skills_list(self) -> list[str]:
        """Parse pipe-delimited skills string into list."""
        if not self.skills:
            return []
        return [s.strip() for s in self.skills.split("|") if s.strip()]


class InviteRowResult(BaseModel):
    """Result for a single row in the bulk invite response."""

    row: int
    email: str
    status: str  # "created", "duplicate", "error"
    error: str | None = None


class BulkInviteResponse(BaseModel):
    """Aggregate response for the bulk invite endpoint."""

    batch_id: str
    total: int
    created: int
    duplicates: int
    errors: int
    results: list[InviteRowResult]


class InviteListResponse(BaseModel):
    """Single invite in list response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    display_name: str | None = None
    status: str
    created_at: datetime
    accepted_at: datetime | None = None
