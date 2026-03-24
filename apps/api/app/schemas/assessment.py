"""Assessment Pydantic schemas (v2).

Input sanitization applied:
- competency_slug: alphanumeric + underscore only, max 50 chars
- session_id/question_id: UUID format validated
- answer: max 5000 chars, HTML tags stripped
- response_time_ms: 0-600000 (10 minutes max)
- language: enum validated (en/az only)
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, field_validator


# Allowed competency slugs pattern
SLUG_RE = re.compile(r"^[a-z][a-z0-9_]{1,49}$")

# Strip HTML tags from open-ended answers (prevent XSS in LLM prompts)
HTML_TAG_RE = re.compile(r"<[^>]+>")


def _validate_uuid(value: str, field_name: str) -> str:
    """Validate that a string is a valid UUID."""
    try:
        uuid.UUID(value)
    except (ValueError, AttributeError):
        raise ValueError(f"{field_name} must be a valid UUID")
    return value


# ── Request schemas ───────────────────────────────────────────────────────────

class StartAssessmentRequest(BaseModel):
    competency_slug: str  # e.g. "communication"
    language: Literal["en", "az"] = "en"

    @field_validator("competency_slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        v = v.strip().lower()
        if not SLUG_RE.match(v):
            raise ValueError("Invalid competency slug: lowercase letters, numbers, underscore only (2-50 chars)")
        return v


class SubmitAnswerRequest(BaseModel):
    session_id: str
    question_id: str
    answer: str           # text for open-ended; option key for MCQ
    response_time_ms: int

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        return _validate_uuid(v.strip(), "session_id")

    @field_validator("question_id")
    @classmethod
    def validate_question_id(cls, v: str) -> str:
        return _validate_uuid(v.strip(), "question_id")

    @field_validator("answer")
    @classmethod
    def sanitize_answer(cls, v: str) -> str:
        """Strip HTML tags and limit length to prevent prompt injection + XSS."""
        v = v.strip()
        if len(v) > 5000:
            raise ValueError("Answer must be at most 5000 characters")
        if len(v) == 0:
            raise ValueError("Answer cannot be empty")
        # Strip HTML tags (basic XSS prevention, also protects LLM prompt)
        v = HTML_TAG_RE.sub("", v)
        return v

    @field_validator("response_time_ms")
    @classmethod
    def validate_timing(cls, v: int) -> int:
        if v < 0:
            raise ValueError("response_time_ms must be non-negative")
        if v > 600_000:
            raise ValueError("response_time_ms cannot exceed 10 minutes (600000ms)")
        return v


# ── Response schemas ──────────────────────────────────────────────────────────

class QuestionOut(BaseModel):
    """A single question as served to the frontend."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    question_type: str        # "mcq" | "open_ended" | "sjt"
    question_en: str
    question_az: str
    options: list[dict] | None = None  # MCQ options (key/text_en/text_az dicts); None for open-ended
    # IRT params are NOT exposed to the client
    competency_id: str


class SessionOut(BaseModel):
    """Lightweight session state returned after start/answer.

    NOTE: theta and theta_se are intentionally NOT exposed to the client.
    Exposing IRT ability estimates enables reverse-engineering the CAT algorithm
    and predicting upcoming questions. (Security audit P1, 2026-03-24)
    """
    session_id: str
    competency_slug: str
    questions_answered: int
    is_complete: bool
    stop_reason: str | None = None
    next_question: QuestionOut | None = None


class AnswerFeedback(BaseModel):
    """Immediate feedback after submitting an answer.

    NOTE: raw_score intentionally NOT exposed to client (security audit CRIT-03).
    Exposing BARS scores enables calibration attacks — users can reverse-engineer
    what answer patterns score highest by submitting variations.
    """
    session_id: str
    question_id: str
    # raw_score REMOVED — security audit CRIT-03 (2026-03-25)
    timing_warning: str | None = None
    session: SessionOut


class AssessmentResultOut(BaseModel):
    """Full results after session completion.

    NOTE: theta/theta_se intentionally NOT exposed to client (security audit P1).
    Exposing IRT ability estimates enables reverse-engineering the CAT algorithm.
    """
    session_id: str
    competency_slug: str
    # theta/theta_se REMOVED — security audit P1 (2026-03-24)
    competency_score: float   # 0–100 (theta mapped via sigmoid)
    questions_answered: int
    stop_reason: str | None = None
    aura_updated: bool = False
    gaming_flags: list[str] = []
    completed_at: datetime | None = None
