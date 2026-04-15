"""Pydantic v2 models mirroring the 4 compliance tables.

Read side: the full models (with id + created_at) come back from SELECT.
Write side: *Create models carry only the columns callers should supply;
DB defaults / triggers fill id, created_at, sha256, sla_deadline.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress

# ---------------------------------------------------------------------------
# Shared literal enums — mirror DB CHECK constraints exactly.
# ---------------------------------------------------------------------------
SourceProduct = Literal["volaura", "mindshift", "lifesim", "brandedby", "zeus"]

DocumentType = Literal[
    "privacy_policy",
    "terms_of_service",
    "ai_decision_notice",
    "cookie_policy",
    "data_processing_agreement",
]

Locale = Literal["az", "en", "ru"]

ConsentEventType = Literal[
    "consent_given",
    "consent_withdrawn",
    "consent_updated",
    "policy_reaccepted",
]

HumanReviewStatus = Literal[
    "pending",
    "in_review",
    "resolved_uphold",
    "resolved_overturn",
    "escalated_to_authority",
]


# ---------------------------------------------------------------------------
# 1. policy_versions
# ---------------------------------------------------------------------------
class PolicyVersionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_type: DocumentType
    version: str
    locale: Locale
    content_markdown: str
    effective_from: datetime
    superseded_by: Optional[UUID] = None
    # content_sha256 is computed by DB trigger; callers omit it.


class PolicyVersion(PolicyVersionCreate):
    id: UUID
    content_sha256: str
    created_at: datetime


# ---------------------------------------------------------------------------
# 2. consent_events
# ---------------------------------------------------------------------------
class ConsentEventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    source_product: SourceProduct
    event_type: ConsentEventType
    policy_version_id: UUID
    consent_scope: dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[IPvAnyAddress] = None
    user_agent: Optional[str] = None


class ConsentEvent(ConsentEventCreate):
    id: UUID
    created_at: datetime


# ---------------------------------------------------------------------------
# 3. automated_decision_log
# ---------------------------------------------------------------------------
class AutomatedDecisionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    source_product: SourceProduct
    decision_type: str
    decision_output: dict[str, Any]
    algorithm_version: str
    model_inputs_hash: Optional[str] = None
    explanation_text: Optional[str] = None
    human_reviewable: bool = True


class AutomatedDecision(AutomatedDecisionCreate):
    id: UUID
    created_at: datetime


# ---------------------------------------------------------------------------
# 4. human_review_requests
# ---------------------------------------------------------------------------
class HumanReviewRequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    automated_decision_id: UUID
    source_product: SourceProduct
    request_reason: str
    # requested_at + sla_deadline set by DB trigger; omit on insert.


class HumanReviewRequest(HumanReviewRequestCreate):
    id: UUID
    requested_at: datetime
    sla_deadline: datetime
    status: HumanReviewStatus = "pending"
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    reviewer_user_id: Optional[UUID] = None
