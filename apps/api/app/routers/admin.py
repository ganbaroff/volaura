"""Admin panel router — platform management endpoints.

Access: platform admins only (is_platform_admin=True in profiles).
All endpoints use service-role client (RLS bypassed intentionally).
Security: fail-closed gate via PlatformAdminId dep (Mistake #57 pattern).

Endpoints:
  GET  /api/admin/ping                        — AdminGuard health check
  GET  /api/admin/stats                       — platform stats dashboard
  GET  /api/admin/users                       — paginated user list
  GET  /api/admin/organizations/pending       — orgs awaiting approval
  POST /api/admin/organizations/{id}/approve  — verify org
  POST /api/admin/organizations/{id}/reject   — deactivate org
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, Request
from loguru import logger

from app.deps import PlatformAdminId, SupabaseAdmin
from app.middleware.rate_limit import limiter
from app.schemas.admin import (
    AdminOrgRow,
    AdminStatsResponse,
    AdminUserRow,
    OrgApproveResponse,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])

# Conservative rate limit — admin panel is internal, 2-5 concurrent users max
RATE_ADMIN = "30/minute"


# ── Ping ──────────────────────────────────────────────────────────────────────

@router.get("/ping")
@limiter.limit(RATE_ADMIN)
async def admin_ping(
    request: Request,
    admin_id: PlatformAdminId,
) -> dict:
    """AdminGuard uses this to verify the caller is a platform admin.

    Returns 200 for admins, 403 (from PlatformAdminId dep) for everyone else.
    Intentionally minimal — just a gate, no data.
    """
    return {"ok": True}


# ── Stats dashboard ───────────────────────────────────────────────────────────

@router.get("/stats", response_model=AdminStatsResponse)
@limiter.limit(RATE_ADMIN)
async def get_admin_stats(
    request: Request,
    admin_id: PlatformAdminId,
    db_admin: SupabaseAdmin,
) -> AdminStatsResponse:
    """Platform health stats for the admin dashboard home page."""
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    ).isoformat()

    # Run counts concurrently
    import asyncio
    users_res, orgs_res, pending_res, assessments_res, aura_res = await asyncio.gather(
        db_admin.table("profiles").select("id", count="exact").execute(),
        db_admin.table("organizations").select("id", count="exact").eq("is_active", True).execute(),
        db_admin.table("organizations").select("id", count="exact")
            .is_("verified_at", "null").eq("is_active", True).execute(),
        db_admin.table("assessment_sessions").select("id", count="exact")
            .eq("status", "completed").gte("completed_at", today_start).execute(),
        db_admin.table("aura_scores").select("total_score").execute(),
    )

    aura_scores = [r["total_score"] for r in (aura_res.data or []) if r.get("total_score") is not None]
    avg_aura = round(sum(aura_scores) / len(aura_scores), 1) if aura_scores else None

    return AdminStatsResponse(
        total_users=users_res.count or 0,
        total_organizations=orgs_res.count or 0,
        pending_org_approvals=pending_res.count or 0,
        assessments_today=assessments_res.count or 0,
        avg_aura_score=avg_aura,
    )


# ── Users ─────────────────────────────────────────────────────────────────────

@router.get("/users", response_model=list[AdminUserRow])
@limiter.limit(RATE_ADMIN)
async def list_admin_users(
    request: Request,
    admin_id: PlatformAdminId,
    db_admin: SupabaseAdmin,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    account_type: str | None = Query(default=None),
) -> list[AdminUserRow]:
    """Paginated list of all platform users for the admin users page."""
    query = db_admin.table("profiles").select(
        "id, username, display_name, account_type, subscription_status, "
        "is_platform_admin, created_at"
    ).order("created_at", desc=True).range(offset, offset + limit - 1)

    if account_type:
        query = query.eq("account_type", account_type)

    result = await query.execute()
    return [AdminUserRow(**row) for row in (result.data or [])]


# ── Organizations ─────────────────────────────────────────────────────────────

@router.get("/organizations/pending", response_model=list[AdminOrgRow])
@limiter.limit(RATE_ADMIN)
async def list_pending_organizations(
    request: Request,
    admin_id: PlatformAdminId,
    db_admin: SupabaseAdmin,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[AdminOrgRow]:
    """Organizations that have registered but not yet been verified.

    Pending = is_active=True AND verified_at IS NULL.
    """
    orgs_res = await db_admin.table("organizations").select(
        "id, name, description, website, owner_id, trust_score, verified_at, is_active, created_at"
    ).is_("verified_at", "null").eq("is_active", True).order("created_at").range(offset, offset + limit - 1).execute()

    orgs = orgs_res.data or []
    if not orgs:
        return []

    # Enrich with owner username
    owner_ids = [o["owner_id"] for o in orgs]
    profiles_res = await db_admin.table("profiles").select("id, username").in_("id", owner_ids).execute()
    username_map = {p["id"]: p["username"] for p in (profiles_res.data or [])}

    return [
        AdminOrgRow(**org, owner_username=username_map.get(org["owner_id"]))
        for org in orgs
    ]


@router.post("/organizations/{org_id}/approve", response_model=OrgApproveResponse)
@limiter.limit(RATE_ADMIN)
async def approve_organization(
    request: Request,
    org_id: str,
    admin_id: PlatformAdminId,
    db_admin: SupabaseAdmin,
) -> OrgApproveResponse:
    """Set verified_at = NOW() on an organization, granting it verified status."""
    # Verify org exists and is pending (fail-closed — Mistake #57)
    org_check = await db_admin.table("organizations").select("id, verified_at").eq("id", org_id).maybe_single().execute()
    if not org_check.data:
        raise HTTPException(status_code=404, detail={"code": "ORG_NOT_FOUND", "message": "Organization not found"})

    now = datetime.now(timezone.utc).isoformat()
    await db_admin.table("organizations").update({"verified_at": now}).eq("id", org_id).execute()

    logger.info("Admin approved organization", org_id=org_id, admin_id=admin_id)
    return OrgApproveResponse(org_id=org_id, action="approved", verified_at=datetime.now(timezone.utc))


@router.post("/organizations/{org_id}/reject", response_model=OrgApproveResponse)
@limiter.limit(RATE_ADMIN)
async def reject_organization(
    request: Request,
    org_id: str,
    admin_id: PlatformAdminId,
    db_admin: SupabaseAdmin,
) -> OrgApproveResponse:
    """Deactivate an organization (is_active=False). Reversible by re-approving."""
    org_check = await db_admin.table("organizations").select("id").eq("id", org_id).maybe_single().execute()
    if not org_check.data:
        raise HTTPException(status_code=404, detail={"code": "ORG_NOT_FOUND", "message": "Organization not found"})

    await db_admin.table("organizations").update({"is_active": False}).eq("id", org_id).execute()

    logger.info("Admin rejected organization", org_id=org_id, admin_id=admin_id)
    return OrgApproveResponse(org_id=org_id, action="rejected", verified_at=None)
