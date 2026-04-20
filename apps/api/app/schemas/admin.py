"""Admin panel Pydantic schemas (v2).

All admin responses use service-role data — never exposed to regular users.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AdminUserRow(BaseModel):
    """Minimal user row for the admin users table."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    display_name: str | None = None
    account_type: str
    subscription_status: str
    is_platform_admin: bool = False
    created_at: datetime


class AdminOrgRow(BaseModel):
    """Organization row for the admin approval queue."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None = None
    website: str | None = None
    owner_id: str
    owner_username: str | None = None
    trust_score: float | None = None
    verified_at: datetime | None = None
    is_active: bool
    created_at: datetime


class AdminStatsResponse(BaseModel):
    """Platform health stats for the admin dashboard."""

    total_users: int
    total_organizations: int
    pending_org_approvals: int
    assessments_today: int
    avg_aura_score: float | None = None
    pending_grievances: int = 0


class OrgApproveResponse(BaseModel):
    """Result of approving or rejecting an organization."""

    org_id: str
    action: str  # "approved" | "rejected"
    verified_at: datetime | None = None


# ── Ecosystem overview (M1, 2026-04-18) ──────────────────────────────────────
# See docs/engineering/ADMIN-DASHBOARD-SPEC.md §7 (Strange v2 pivot)
# Activation-first, pre-PMF-appropriate. MRR/NRR/CAC stubbed until revenue exists.


class AdminActivationFunnel(BaseModel):
    """One product's activation funnel (signup → key action)."""

    product: str  # "volaura" | "mindshift"
    signups_24h: int
    activated_24h: int  # completed first key action
    activation_rate: float  # 0.0-1.0; activated / signups (0 when signups=0)


class AdminPresenceMatrix(BaseModel):
    """Cross-product presence counts. Replaces Sankey (premature at <100 users)."""

    volaura_only: int
    mindshift_only: int
    both_products: int
    total_users: int


class AdminOverviewResponse(BaseModel):
    """Tier-1 exec scorecard + Tier-2 cross-product presence.

    Activation-first founder dashboard: pre-PMF stage prioritises activation
    and retention over MRR/NRR/CAC. See ADMIN-DASHBOARD-SPEC.md §7.
    """

    # Tier 1 scorecard (5 cards)
    activation_rate_24h: float  # new signups → first-assessment-started in 24h
    w4_retention: float | None  # % of users active W0 still active W4 (null if insufficient history)
    dau_wau_ratio: float  # stickiness: DAU / WAU (0 when WAU=0)
    errors_24h: int  # 5xx + failed assessments + orphan events
    runway_months: float | None  # manual CEO-editable via env PLATFORM_RUNWAY_MONTHS

    # Tier 2 cross-product
    presence: AdminPresenceMatrix
    funnels: list[AdminActivationFunnel]

    # Meta
    computed_at: datetime
    stale_after_seconds: int = 60


class AdminActivityEvent(BaseModel):
    """Single row in the live activity feed (character_events tail)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    product: str  # "volaura" | "mindshift" | "lifesim" | "brandedby" | "zeus"
    event_type: str
    user_id_prefix: str  # first 8 chars of UUID; full id would leak in admin logs
    created_at: datetime
    payload_summary: str | None = None  # truncated preview, <=120 chars


# ── AARRR Growth Funnel (M2, 2026-04-18) ─────────────────────────────────────
# 7-day acquisition/activation/retention signal for the /admin/growth page.
# auth.users queried via service role (db_admin) — RLS bypassed intentionally.


class AdminGrowthFunnel(BaseModel):
    """AARRR funnel data for last 7 days."""

    # Acquisition
    signups_7d: int
    # Activation
    profiles_created_7d: int
    # Engagement step 1
    assessments_started_7d: int
    # Engagement step 2 (completion)
    assessments_completed_7d: int
    # Retention signal
    aura_scores_7d: int
    # Meta
    computed_at: datetime
