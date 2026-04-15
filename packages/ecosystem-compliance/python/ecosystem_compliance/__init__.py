"""Ecosystem-wide GDPR Art.22 + AI Act compliance models.

Shared across volaura, mindshift, lifesim, brandedby, zeus.
Each product imports these Pydantic v2 models and inserts via its own
Supabase service_role client. RLS + table-level CHECK constraints on
source_product enforce cross-product isolation at the DB layer.
"""
from ecosystem_compliance.models import (
    SourceProduct,
    DocumentType,
    Locale,
    ConsentEventType,
    HumanReviewStatus,
    PolicyVersion,
    PolicyVersionCreate,
    ConsentEvent,
    ConsentEventCreate,
    AutomatedDecision,
    AutomatedDecisionCreate,
    HumanReviewRequest,
    HumanReviewRequestCreate,
)

__all__ = [
    "SourceProduct",
    "DocumentType",
    "Locale",
    "ConsentEventType",
    "HumanReviewStatus",
    "PolicyVersion",
    "PolicyVersionCreate",
    "ConsentEvent",
    "ConsentEventCreate",
    "AutomatedDecision",
    "AutomatedDecisionCreate",
    "HumanReviewRequest",
    "HumanReviewRequestCreate",
]

__version__ = "0.1.0"
