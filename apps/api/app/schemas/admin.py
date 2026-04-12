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


class OrgApproveResponse(BaseModel):
    """Result of approving or rejecting an organization."""

    org_id: str
    action: str  # "approved" | "rejected"
    verified_at: datetime | None = None
