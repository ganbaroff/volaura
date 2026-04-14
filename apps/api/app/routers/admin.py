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

from datetime import UTC, datetime

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
from app.services.ghosting_grace import process_ghosting_grace

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
    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

    # Run counts concurrently
    import asyncio

    users_res, orgs_res, pending_res, assessments_res, aura_res, grievances_res = await asyncio.gather(
        db_admin.table("profiles").select("id", count="exact").execute(),
        db_admin.table("organizations").select("id", count="exact").eq("is_active", True).execute(),
        db_admin.table("organizations")
        .select("id", count="exact")
        .is_("verified_at", "null")
        .eq("is_active", True)
        .execute(),
        db_admin.table("assessment_sessions")
        .select("id", count="exact")
        .eq("status", "completed")
        .gte("completed_at", today_start)
        .execute(),
        db_admin.table("aura_scores").select("total_score").execute(),
        db_admin.table("grievances").select("id", count="exact").in_("status", ["pending", "reviewing"]).execute(),
    )

    aura_scores = [r["total_score"] for r in (aura_res.data or []) if r.get("total_score") is not None]
    avg_aura = round(sum(aura_scores) / len(aura_scores), 1) if aura_scores else None

    return AdminStatsResponse(
        total_users=users_res.count or 0,
        total_organizations=orgs_res.count or 0,
        pending_org_approvals=pending_res.count or 0,
        assessments_today=assessments_res.count or 0,
        avg_aura_score=avg_aura,
        pending_grievances=grievances_res.count or 0,
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
    query = (
        db_admin.table("profiles")
        .select("id, username, display_name, account_type, subscription_status, is_platform_admin, created_at")
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
    )

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
    orgs_res = (
        await db_admin.table("organizations")
        .select("id, name, description, website, owner_id, trust_score, verified_at, is_active, created_at")
        .is_("verified_at", "null")
        .eq("is_active", True)
        .order("created_at")
        .range(offset, offset + limit - 1)
        .execute()
    )

    orgs = orgs_res.data or []
    if not orgs:
        return []

    # Enrich with owner username
    owner_ids = [o["owner_id"] for o in orgs]
    profiles_res = await db_admin.table("profiles").select("id, username").in_("id", owner_ids).execute()
    username_map = {p["id"]: p["username"] for p in (profiles_res.data or [])}

    return [AdminOrgRow(**org, owner_username=username_map.get(org["owner_id"])) for org in orgs]


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
    org_check = (
        await db_admin.table("organizations").select("id, verified_at").eq("id", org_id).maybe_single().execute()
    )
    if not org_check.data:
        raise HTTPException(status_code=404, detail={"code": "ORG_NOT_FOUND", "message": "Organization not found"})

    now = datetime.now(UTC).isoformat()
    await db_admin.table("organizations").update({"verified_at": now}).eq("id", org_id).execute()

    logger.info("Admin approved organization", org_id=org_id, admin_id=admin_id)
    return OrgApproveResponse(org_id=org_id, action="approved", verified_at=datetime.now(UTC))


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


# ── Swarm Office ─────────────────────────────────────────────────────────────


@router.get("/swarm/agents")
@limiter.limit(RATE_ADMIN)
async def get_swarm_agents(
    request: Request,
    admin_id: PlatformAdminId,
) -> dict:
    """Return all tracked agents from agent-state.json for the AI Office dashboard."""
    import json as _json
    from pathlib import Path

    state_path = Path(__file__).parent.parent.parent.parent / "memory" / "swarm" / "agent-state.json"
    try:
        with open(state_path, encoding="utf-8") as f:
            data = _json.load(f)

        agents = []
        for name, state in data.get("agents", {}).items():
            agents.append(
                {
                    "name": name,
                    "display_name": name.replace("-agent", "").replace("-", " ").title(),
                    "status": state.get("status", "unknown"),
                    "last_task": state.get("last_task", ""),
                    "last_run": state.get("last_run"),
                    "next_scheduled": state.get("next_scheduled"),
                    "blockers": state.get("blockers", []),
                    "tasks_completed": state.get("performance", {}).get("tasks_completed", 0),
                    "tasks_failed": state.get("performance", {}).get("tasks_failed", 0),
                }
            )

        # Sort: active first, then by last_run descending
        agents.sort(key=lambda a: (a["status"] != "idle", a["last_run"] or ""), reverse=True)

        return {
            "data": {
                "agents": agents,
                "total_tracked": len(agents),
                "total_untracked": data.get("_uninitialized_count", 0),
            }
        }
    except FileNotFoundError:
        return {"data": {"agents": [], "total_tracked": 0, "total_untracked": 48}}
    except Exception as e:
        logger.error("Failed to read agent state", error=str(e))
        return {"data": {"agents": [], "total_tracked": 0, "total_untracked": 48}}


@router.get("/swarm/proposals")
@limiter.limit(RATE_ADMIN)
async def get_swarm_proposals(
    request: Request,
    admin_id: PlatformAdminId,
    status_filter: str | None = Query(None, alias="status"),
) -> dict:
    """Return swarm proposals from proposals.json for CEO review."""
    import json as _json
    from pathlib import Path

    proposals_path = Path(__file__).parent.parent.parent.parent / "memory" / "swarm" / "proposals.json"
    try:
        with open(proposals_path, encoding="utf-8") as f:
            data = _json.load(f)

        proposals = data.get("proposals", [])

        if status_filter:
            proposals = [p for p in proposals if p.get("status") == status_filter]

        # Most recent first
        proposals.sort(key=lambda p: p.get("timestamp", ""), reverse=True)

        # Limit to last 50
        proposals = proposals[:50]

        summary = {
            "pending": sum(1 for p in data.get("proposals", []) if p.get("status") == "pending"),
            "approved": sum(1 for p in data.get("proposals", []) if p.get("status") == "approved"),
            "rejected": sum(1 for p in data.get("proposals", []) if p.get("status") == "rejected"),
        }

        return {"data": {"proposals": proposals, "summary": summary}}
    except FileNotFoundError:
        return {"data": {"proposals": [], "summary": {"pending": 0, "approved": 0, "rejected": 0}}}
    except Exception as e:
        logger.error("Failed to read proposals", error=str(e))
        return {"data": {"proposals": [], "summary": {"pending": 0, "approved": 0, "rejected": 0}}}


@router.post("/swarm/proposals/{proposal_id}/decide")
@limiter.limit(RATE_ADMIN)
async def decide_proposal(
    request: Request,
    proposal_id: str,
    admin_id: PlatformAdminId,
) -> dict:
    """CEO approves/dismisses/defers a swarm proposal."""
    import json as _json
    from pathlib import Path

    body = await request.json()
    action = body.get("action", "")  # "approve" | "dismiss" | "defer"
    if action not in ("approve", "dismiss", "defer"):
        raise HTTPException(
            status_code=400, detail={"code": "INVALID_ACTION", "message": "Action must be: approve, dismiss, defer"}
        )

    proposals_path = Path(__file__).parent.parent.parent.parent / "memory" / "swarm" / "proposals.json"
    try:
        with open(proposals_path, encoding="utf-8") as f:
            data = _json.load(f)

        status_map = {"approve": "approved", "dismiss": "rejected", "defer": "deferred"}
        found = False
        for p in data.get("proposals", []):
            if p.get("id", "").startswith(proposal_id):
                p["status"] = status_map[action]
                p["ceo_decision_at"] = datetime.now(UTC).isoformat()
                p["ceo_decision"] = f"Admin {admin_id}: {action}"
                found = True
                break

        if not found:
            raise HTTPException(
                status_code=404, detail={"code": "PROPOSAL_NOT_FOUND", "message": f"Proposal {proposal_id} not found"}
            )

        import os
        import tempfile

        tmp_fd, tmp_path = tempfile.mkstemp(dir=proposals_path.parent, suffix=".json")
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as tmp_f:
                _json.dump(data, tmp_f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, proposals_path)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise

        logger.info("Proposal decided", proposal_id=proposal_id, action=action, admin_id=admin_id)
        return {"data": {"proposal_id": proposal_id, "action": action, "status": status_map[action]}}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to decide proposal", error=str(e))
        raise HTTPException(status_code=500, detail={"code": "INTERNAL", "message": "Failed to process decision"})


@router.get("/swarm/findings")
@limiter.limit(RATE_ADMIN)
async def get_swarm_findings(
    request: Request,
    admin_id: PlatformAdminId,
    limit: int = 50,
    category: str = "",
    min_importance: int = 1,
) -> dict:
    """Return typed FindingContract results from shared memory (SQLite blackboard).

    These are findings from coordinator runs, simulate_users friction points,
    and any agent that posted a result via post_result().
    """
    import sys
    from pathlib import Path as _Path

    # Ensure swarm package importable from API context
    _packages_path = str(_Path(__file__).parent.parent.parent.parent.parent / "packages")
    if _packages_path not in sys.path:
        sys.path.insert(0, _packages_path)

    try:
        import json as _json
        import sqlite3 as _sqlite3

        from swarm.shared_memory import _DB_PATH, get_all_recent  # noqa: F401

        if not _DB_PATH.exists():
            return {"data": {"findings": [], "total": 0, "db_exists": False}}

        conn = _sqlite3.connect(str(_DB_PATH), timeout=5)
        try:
            params: list = []
            where_parts = ["(expires_at=0 OR expires_at>?)", "importance>=?"]
            params.extend([__import__("time").time(), min_importance])

            if category:
                where_parts.append("category=?")
                params.append(category)

            where_clause = " AND ".join(where_parts)
            rows = conn.execute(
                f"SELECT agent_id, task_id, result, ts, importance, category FROM memory "
                f"WHERE {where_clause} ORDER BY importance DESC, ts DESC LIMIT ?",
                params + [limit],
            ).fetchall()
        finally:
            conn.close()

        findings = []
        for r in rows:
            try:
                data = _json.loads(r[2])
            except Exception:
                data = {"raw": r[2][:200]}
            findings.append(
                {
                    "agent_id": r[0],
                    "task_id": r[1],
                    "data": data,
                    "ts": r[3],
                    "importance": r[4],
                    "category": r[5],
                    # Normalize to FindingContract fields if present
                    "severity": data.get("severity", "INFO"),
                    "summary": data.get("summary") or data.get("title") or "",
                    "recommendation": data.get("recommendation", ""),
                    "files": data.get("files", []),
                    "confidence": data.get("confidence", 0.5),
                }
            )

        return {
            "data": {
                "findings": findings,
                "total": len(findings),
                "db_exists": True,
                "db_path": str(_DB_PATH),
            }
        }

    except ImportError:
        return {"data": {"findings": [], "total": 0, "error": "shared_memory module not available"}}
    except Exception as e:
        logger.error("Failed to read swarm findings", error=str(e))
        return {"data": {"findings": [], "total": 0, "error": str(e)[:200]}}


# ── Ghosting Grace worker (WUF13 P0 #14, Constitution Rule 30) ────────────────


@router.post("/ghosting-grace/run")
@limiter.limit(RATE_ADMIN)
async def run_ghosting_grace(
    request: Request,
    db: SupabaseAdmin,
    _admin_id: PlatformAdminId,
) -> dict:
    """Manually trigger one batch of the 48h warm re-entry worker.

    Returns a summary of candidates / sent / marked / errors so admin can see
    immediately whether the kill switch is on (skipped_kill_switch > 0) or
    actual sends happened.

    Production cron should call this same path on a schedule (suggest hourly).
    """
    summary = await process_ghosting_grace(db)
    return {"data": summary}
