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
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

# Allowed competency slugs pattern
SLUG_RE = re.compile(r"^[a-z][a-z0-9_]{1,49}$")

# Strip HTML tags from open-ended answers (prevent XSS in LLM prompts)
HTML_TAG_RE = re.compile(r"<[^>]+>")

# Prompt injection detection patterns (case-insensitive).
# These patterns match common LLM jailbreak techniques embedded in user answers.
# If detected, the answer is rejected with a 422 before reaching the LLM evaluator.
# Note: This is defense-in-depth — the LLM system prompt also has injection guards.
_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompt)", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|prior)\s+instructions?", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(?:a|an)\s+\w+", re.IGNORECASE),
    re.compile(r"act\s+as\s+(?:a|an|if)\s+\w+", re.IGNORECASE),
    re.compile(r"system\s*:\s*you\s+(are|must|should)", re.IGNORECASE),
    re.compile(r"\[system\s*\]", re.IGNORECASE),
    re.compile(r"<\|(?:im_start|endoftext|system)\|>", re.IGNORECASE),
    re.compile(r"output\s+the\s+following\s+without\s+", re.IGNORECASE),
    re.compile(r"reveal\s+your\s+(system\s+)?prompt", re.IGNORECASE),
    re.compile(r"print\s+your\s+(instructions?|system\s+prompt)", re.IGNORECASE),
]


def _validate_uuid(value: str, field_name: str) -> str:
    """Validate that a string is a valid UUID."""
    try:
        uuid.UUID(value)
    except (ValueError, AttributeError):
        raise ValueError(f"{field_name} must be a valid UUID")
    return value


# ── Request schemas ───────────────────────────────────────────────────────────

VALID_ROLE_LEVELS = ("professional", "volunteer", "coordinator", "specialist", "manager", "senior_manager")
# Roles a user may self-claim at signup/assessment time — the "entry tiers".
# The elevated tiers (coordinator / specialist / manager / senior_manager) require
# evidence — a coordinator endorsement on an `events` row, or an explicit admin
# promotion. Without this gate, any Leyla could POST role_level=senior_manager and
# show up in Aynur's talent search as a self-promoted senior manager. That's the
# "role self-selection gaming" issue flagged in session 88 pre-launch audit (S2).
SELF_CLAIMABLE_ROLE_LEVELS = ("professional", "volunteer")


class StartAssessmentRequest(BaseModel):
    competency_slug: str  # e.g. "communication"
    language: Literal["en", "az"] = "en"
    # Restricted to self-claimable tiers. Elevated tiers are set server-side after
    # evidence is present — never trusted from client input.
    role_level: Literal["professional", "volunteer"] = "professional"
    energy_level: Literal["full", "mid", "low"] = "full"  # Constitution Law 2: Energy Adaptation
    automated_decision_consent: bool = False  # GDPR Article 22: user acknowledges automated scoring
    assessment_plan_competencies: list[str] | None = None
    assessment_plan_current_index: int | None = None

    @field_validator("competency_slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        v = v.strip().lower()
        if not SLUG_RE.match(v):
            raise ValueError("Invalid competency slug: lowercase letters, numbers, underscore only (2-50 chars)")
        return v

    @field_validator("assessment_plan_competencies")
    @classmethod
    def validate_plan_competencies(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        if len(value) == 0:
            raise ValueError("assessment_plan_competencies cannot be empty")

        cleaned: list[str] = []
        for slug in value:
            normalized = slug.strip().lower()
            if not SLUG_RE.match(normalized):
                raise ValueError(
                    "Invalid assessment plan competency slug: lowercase letters, numbers, underscore only (2-50 chars)"
                )
            cleaned.append(normalized)
        return cleaned

    @field_validator("assessment_plan_current_index")
    @classmethod
    def validate_plan_index(cls, value: int | None) -> int | None:
        if value is None:
            return value
        if value < 0:
            raise ValueError("assessment_plan_current_index must be non-negative")
        return value

    @model_validator(mode="after")
    def validate_plan_consistency(self) -> StartAssessmentRequest:
        if self.assessment_plan_competencies is None:
            if self.assessment_plan_current_index is not None:
                raise ValueError("assessment_plan_current_index requires assessment_plan_competencies")
            return self

        if self.assessment_plan_current_index is None:
            self.assessment_plan_current_index = 0

        if self.assessment_plan_current_index >= len(self.assessment_plan_competencies):
            raise ValueError("assessment_plan_current_index is out of range for assessment_plan_competencies")

        if self.assessment_plan_competencies[self.assessment_plan_current_index] != self.competency_slug:
            raise ValueError("competency_slug must match assessment_plan_competencies[current_index]")

        return self


class SubmitAnswerRequest(BaseModel):
    session_id: str
    question_id: str
    answer: str  # text for open-ended; option key for MCQ
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
        """Strip HTML, detect prompt injection, and limit length."""
        v = v.strip()
        if len(v) > 5000:
            raise ValueError("Answer must be at most 5000 characters")
        if len(v) == 0:
            raise ValueError("Answer cannot be empty")
        # Strip HTML tags (basic XSS prevention, also protects LLM prompt)
        v = HTML_TAG_RE.sub("", v)
        # SECURITY: Prompt injection detection — reject answers containing LLM jailbreak patterns.
        # This prevents attackers from hijacking the BARS evaluator via crafted answer text.
        # Patterns target: role-override ("ignore previous instructions"), persona injection
        # ("act as"), system-prompt leakage, and common jailbreak delimiters.
        for pattern in _INJECTION_PATTERNS:
            if pattern.search(v):
                raise ValueError(
                    "Answer contains disallowed content. Please provide a genuine response to the assessment question."
                )
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
    question_type: str  # "mcq" | "open_ended" | "sjt"
    question_en: str
    question_az: str
    question_ru: str | None = None
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
    role_level: str = "professional"
    questions_answered: int
    is_complete: bool
    stop_reason: str | None = None
    next_question: QuestionOut | None = None


class SessionResumeOut(BaseModel):
    """Resume state for client-side recovery after a store clear.

    Returned by GET /api/assessment/session/{session_id}. Used by the
    assessment page when the Zustand store has been cleared (browser storage
    eviction, private-window reload) but the URL still carries a session_id.
    The frontend fetches this to decide whether to resume, show an expired
    message, or redirect to fresh assessment start.

    Does NOT expose theta or raw answer history. It includes only the current
    question plus enough plan metadata to restore multi-competency progress.
    """

    session_id: str
    competency_slug: str
    role_level: str = "professional"
    status: str  # 'in_progress' | 'completed' | 'expired'
    questions_answered: int
    started_at: str | None = None
    next_question: QuestionOut | None = None
    assessment_plan_competencies: list[str]
    assessment_plan_current_index: int
    # True when the session can actually be resumed (in_progress + not past
    # the 24h auto-expiry threshold used by /start).
    is_resumable: bool


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
    competency_score: float  # 0–100 (theta mapped via sigmoid)
    questions_answered: int
    stop_reason: str | None = None
    aura_updated: bool = False
    gaming_flags: list[str] = []
    completed_at: datetime | None = None
    # Crystal reward: 0 if already claimed for this competency (idempotent), else CRYSTAL_REWARD
    crystals_earned: int = 0


class CoachingTip(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    description: str
    action: str


class CoachingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: str
    competency_id: str
    score: float
    tips: list[CoachingTip]


class QuestionResultOut(BaseModel):
    """Per-question result shown after session completion.

    NOTE: IRT parameters (irt_a/b/c) and raw_score intentionally NOT exposed.
    difficulty_label is a mapped human-readable label from irt_b thresholds.
    is_correct is derived from raw_score > 0 (binary, no numeric leak).
    """

    model_config = ConfigDict(from_attributes=True)

    question_id: str
    question_en: str | None = None
    question_az: str | None = None
    question_ru: str | None = None
    difficulty_label: Literal["easy", "medium", "hard", "expert"]
    is_correct: bool
    response_time_ms: int | None = None


class QuestionBreakdownOut(BaseModel):
    """Full per-question breakdown for a completed session."""

    model_config = ConfigDict(from_attributes=True)

    session_id: str
    competency_slug: str
    competency_score: float
    questions: list[QuestionResultOut]


class PublicVerificationOut(BaseModel):
    """Public-facing assessment verification — shown when external viewer clicks shared badge link.

    Intentionally minimal: proves the assessment happened, shows score + competency,
    does NOT expose questions, answers, or IRT parameters.
    """

    model_config = ConfigDict(from_attributes=True)

    verified: bool = True
    platform: str = "Volaura"
    session_id: str
    competency_slug: str
    competency_name: str | None = None
    competency_score: float
    badge_tier: str
    questions_answered: int
    completed_at: str | None = None
    display_name: str | None = None
    username: str | None = None


class AssessmentInfoOut(BaseModel):
    """Pre-assessment info shown before starting a competency assessment."""

    model_config = ConfigDict(from_attributes=True)

    competency_slug: str
    name: str
    description: str | None = None
    time_estimate_minutes: int
    can_retake: bool
    days_until_retake: int | None = None  # null if user never completed or not authenticated
