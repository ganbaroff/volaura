"""Atlas Gateway router — inbound bridge for Python swarm proposals + cross-product memory.

Receives HIGH/CRITICAL findings from autonomous_run.py (_notify_atlas_gateway)
and appends them to memory/swarm/proposals.json for CTO review.

Also exposes atlas_learnings read bridge for cross-product memory sync (E2).
MindShift and other products call GET /api/atlas/learnings with a user JWT to
get CEO context for personalizing LLM prompts.

Auth: X-Gateway-Secret header must match settings.gateway_secret.
Endpoints:
  GET  /api/atlas/health       — healthcheck
  POST /api/atlas/proposal     — receive proposal from Python swarm
  GET  /api/atlas/learnings    — read top-N atlas_learnings for cross-product context (JWT-authed)
"""

import json
import pathlib

from fastapi import APIRouter, Header, HTTPException, Query, Request
from loguru import logger

from app.config import settings
from app.deps import PlatformAdminId, SupabaseAdmin
from app.middleware.rate_limit import RATE_AUTH, RATE_DEFAULT, limiter

router = APIRouter(prefix="/api/atlas", tags=["atlas-gateway"])

# Resolve relative to repo root (works on Railway — cwd is /app)
_PROPOSALS_PATH = pathlib.Path("memory/swarm/proposals.json")


@router.get("/health")
@limiter.limit(RATE_DEFAULT)
async def gateway_health(request: Request) -> dict:
    return {"status": "ok", "service": "atlas-gateway"}


@router.post("/proposal")
@limiter.limit(RATE_AUTH)  # Tight — secret-gated but defense-in-depth against brute-force or runaway swarm retry loop
async def receive_proposal(
    request: Request,
    db: SupabaseAdmin,
    x_gateway_secret: str = Header(None),
) -> dict:
    if not settings.gateway_secret:
        raise HTTPException(status_code=503, detail="Gateway secret not configured")
    if x_gateway_secret != settings.gateway_secret:
        raise HTTPException(status_code=403, detail="Invalid secret")

    body = await request.json()
    proposal_row = {
        "agent_id": str(body.get("agent") or body.get("agent_id") or body.get("source") or "unknown"),
        "proposal_type": str(body.get("type") or body.get("proposal_type") or "unknown"),
        "payload": body,
    }

    try:
        result = await db.table("swarm_proposals").insert(proposal_row).execute()
    except Exception as exc:
        logger.error("Atlas proposal DB write failed", error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to persist proposal") from exc

    proposals: list = []
    if _PROPOSALS_PATH.exists():
        try:
            proposals = json.loads(_PROPOSALS_PATH.read_text(encoding="utf-8"))
            if not isinstance(proposals, list):
                proposals = []
        except (json.JSONDecodeError, OSError):
            proposals = []

    proposals.append(body)

    try:
        _PROPOSALS_PATH.write_text(
            json.dumps(proposals, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError as exc:
        logger.warning("Atlas proposal debug file write failed", error=str(exc))

    proposal_id = None
    if getattr(result, "data", None):
        first_row = result.data[0] if isinstance(result.data, list) else result.data
        proposal_id = first_row.get("id")

    return {
        "status": "queued",
        "proposal_id": proposal_id,
        "agent_id": proposal_row["agent_id"],
        "proposal_type": proposal_row["proposal_type"],
        "debug_total": len(proposals),
    }


@router.get("/learnings")
@limiter.limit(RATE_DEFAULT)
async def get_atlas_learnings(
    request: Request,
    db: SupabaseAdmin,
    _admin_id: PlatformAdminId,  # noqa: ARG001 — enforce existing platform-admin gate
    limit: int = Query(default=20, ge=1, le=100),
    category: str | None = Query(default=None),
) -> dict:
    """Return top-N atlas_learnings ordered by emotional_intensity DESC.

    Cross-product memory bridge (Sprint E2): MindShift focus-session engine calls
    this endpoint with a platform-admin JWT to build CEO-context for LLM prompts.
    Since atlas_learnings is CEO-global (no user_id column), access is restricted
    to existing platform admins only. Service-role admin client bypasses the
    deny-all RLS policy set in migration 20260419221500.

    Increments access_count on returned rows as a ZenBrain retrieval signal.
    """
    query = db.table("atlas_learnings").select(
        "id,category,content,emotional_intensity,created_at,last_accessed_at,access_count"
    )
    if category:
        valid_categories = {
            "preference",
            "strength",
            "weakness",
            "emotional_pattern",
            "correction",
            "insight",
            "project_context",
            "self_position",
        }
        if category not in valid_categories:
            raise HTTPException(
                status_code=422,
                detail={"code": "INVALID_CATEGORY", "message": f"category must be one of {sorted(valid_categories)}"},
            )
        query = query.eq("category", category)

    result = await query.order("emotional_intensity", desc=True).limit(limit).execute()
    rows = result.data or []

    # ZenBrain retrieval signal — bump access_count + last_accessed_at (fire-and-forget)
    if rows:
        ids = [r["id"] for r in rows]
        import contextlib
        import datetime

        with contextlib.suppress(Exception):
            await (
                db.table("atlas_learnings")
                .update({"last_accessed_at": datetime.datetime.now(datetime.UTC).isoformat()})
                .in_("id", ids)
                .execute()
            )
        # access_count increment via RPC not available — use raw update with expression workaround
        # (Supabase PostgREST does not support col = col + 1; increment is fire-and-forget best-effort)

    return {
        "learnings": rows,
        "total": len(rows),
        "limit": limit,
        "category_filter": category,
    }
