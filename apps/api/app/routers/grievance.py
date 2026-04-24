"""Formal AURA grievance intake + admin review — Constitution G35 / ISO 10667-2 §7.

A user who disagrees with their AURA score must have a documented contest path.

User surface:
 • POST /api/aura/grievance — file a grievance
 • GET  /api/aura/grievance — list own grievances with status

Admin surface (platform admin only):
 • GET   /api/aura/grievance/admin/pending — list all non-resolved grievances
 • PATCH /api/aura/grievance/admin/{id} — transition status, set resolution
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field

from app.deps import CurrentUserId, SupabaseAdmin, require_platform_admin
from app.middleware.rate_limit import RATE_AUTH, RATE_DEFAULT, limiter

router = APIRouter(prefix="/aura", tags=["Grievance"])


class GrievanceCreate(BaseModel):
    subject: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    related_competency_slug: str | None = Field(default=None, max_length=50)
    related_session_id: str | None = None


class GrievanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    subject: str
    description: str
    related_competency_slug: str | None
    related_session_id: str | None
    status: str
    resolution: str | None
    created_at: str
    resolved_at: str | None


class GrievanceListResponse(BaseModel):
    data: list[GrievanceOut]


@router.post("/grievance", response_model=GrievanceOut, status_code=201)
@limiter.limit(RATE_AUTH)  # Tight limit — grievance endpoint should not be abused as log stream
async def file_grievance(
    request: Request,
    payload: GrievanceCreate,
    user_id: CurrentUserId,
    db: SupabaseAdmin,
) -> GrievanceOut:
    """File a formal grievance about an AURA score or assessment outcome.

    The user owns the grievance. Admin review happens async; the user can poll
    GET /api/aura/grievance to see status transitions (pending → reviewing →
    resolved | rejected).

    Audit note: this endpoint is the user-facing half of the ISO 10667-2 §7
    obligation for automated employment decision systems. Every grievance is
    persisted verbatim (no sanitization beyond length checks) so a regulator
    can read the original complaint.
    """
    try:
        result = await (
            db.table("grievances")
            .insert(
                {
                    "user_id": user_id,
                    "subject": payload.subject.strip(),
                    "description": payload.description.strip(),
                    "related_competency_slug": payload.related_competency_slug,
                    "related_session_id": payload.related_session_id,
                }
            )
            .execute()
        )
    except Exception as exc:
        logger.error("Grievance insert failed", user_id=str(user_id), error=str(exc)[:200])
        raise HTTPException(
            status_code=500,
            detail={"code": "GRIEVANCE_FAILED", "message": "Could not file grievance — please try again"},
        )

    rows = result.data or []
    if not rows:
        raise HTTPException(
            status_code=500,
            detail={"code": "GRIEVANCE_FAILED", "message": "Could not file grievance — please try again"},
        )
    row = rows[0]
    logger.info("Grievance filed", user_id=str(user_id), grievance_id=row.get("id"))
    return GrievanceOut(
        id=str(row["id"]),
        subject=row["subject"],
        description=row["description"],
        related_competency_slug=row.get("related_competency_slug"),
        related_session_id=(str(row["related_session_id"]) if row.get("related_session_id") else None),
        status=row["status"],
        resolution=row.get("resolution"),
        created_at=str(row["created_at"]),
        resolved_at=(str(row["resolved_at"]) if row.get("resolved_at") else None),
    )


@router.get("/grievance", response_model=GrievanceListResponse)
@limiter.limit(RATE_DEFAULT)
async def list_own_grievances(
    request: Request,
    user_id: CurrentUserId,
    db: SupabaseAdmin,
) -> GrievanceListResponse:
    """Return the caller's grievances ordered newest-first."""
    result = await (
        db.table("grievances")
        .select(
            "id, subject, description, related_competency_slug, related_session_id, "
            "status, resolution, created_at, resolved_at"
        )
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )
    items = []
    for row in result.data or []:
        items.append(
            GrievanceOut(
                id=str(row["id"]),
                subject=row["subject"],
                description=row["description"],
                related_competency_slug=row.get("related_competency_slug"),
                related_session_id=(str(row["related_session_id"]) if row.get("related_session_id") else None),
                status=row["status"],
                resolution=row.get("resolution"),
                created_at=str(row["created_at"]),
                resolved_at=(str(row["resolved_at"]) if row.get("resolved_at") else None),
            )
        )
    return GrievanceListResponse(data=items)


# ── Admin surface ─────────────────────────────────────────────────────────────


class GrievanceAdminOut(GrievanceOut):
    """Admin view includes user id + admin_notes + updated_at — fields intake
    response does not expose to the owner."""

    user_id: str
    admin_notes: str | None
    updated_at: str


class GrievanceAdminListResponse(BaseModel):
    data: list[GrievanceAdminOut]


class GrievanceStatusUpdate(BaseModel):
    status: Literal["reviewing", "resolved", "rejected"]
    resolution: str | None = Field(default=None, max_length=5000)
    admin_notes: str | None = Field(default=None, max_length=5000)


def _to_admin_out(row: dict) -> GrievanceAdminOut:
    return GrievanceAdminOut(
        id=str(row["id"]),
        user_id=str(row["user_id"]),
        subject=row["subject"],
        description=row["description"],
        related_competency_slug=row.get("related_competency_slug"),
        related_session_id=(str(row["related_session_id"]) if row.get("related_session_id") else None),
        status=row["status"],
        resolution=row.get("resolution"),
        admin_notes=row.get("admin_notes"),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
        resolved_at=(str(row["resolved_at"]) if row.get("resolved_at") else None),
    )


@router.get("/grievance/admin/pending", response_model=GrievanceAdminListResponse)
@limiter.limit(RATE_DEFAULT)
async def admin_list_pending_grievances(
    request: Request,
    db: SupabaseAdmin,
    _admin_id: str = Depends(require_platform_admin),
) -> GrievanceAdminListResponse:
    """Admin view: list grievances not yet resolved or rejected.

    Sorted oldest-first so the queue is FIFO-ish (newest urgency first only
    when SLA tiers differ, which we do not yet implement).
    """
    result = await (
        db.table("grievances")
        .select("*")
        .in_("status", ["pending", "reviewing"])
        .order("created_at", desc=False)
        .limit(200)
        .execute()
    )
    return GrievanceAdminListResponse(data=[_to_admin_out(r) for r in (result.data or [])])


@router.get("/grievance/admin/history", response_model=GrievanceAdminListResponse)
@limiter.limit(RATE_DEFAULT)
async def admin_list_closed_grievances(
    request: Request,
    db: SupabaseAdmin,
    _admin_id: str = Depends(require_platform_admin),
    limit: int = 50,
) -> GrievanceAdminListResponse:
    """Admin view: list closed grievances (resolved + rejected).

    Sorted newest-first so the most recent resolutions are at the top. Capped
    at 200 rows per request. Used by the /admin/grievances history tab so
    admins can review past decisions without scrolling.
    """
    if limit > 200:
        limit = 200
    result = await (
        db.table("grievances")
        .select("*")
        .in_("status", ["resolved", "rejected"])
        .order("resolved_at", desc=True)
        .limit(limit)
        .execute()
    )
    return GrievanceAdminListResponse(data=[_to_admin_out(r) for r in (result.data or [])])


@router.patch("/grievance/admin/{grievance_id}", response_model=GrievanceAdminOut)
@limiter.limit(RATE_AUTH)
async def admin_transition_grievance(
    request: Request,
    grievance_id: str,
    payload: GrievanceStatusUpdate,
    db: SupabaseAdmin,
    admin_id: str = Depends(require_platform_admin),
) -> GrievanceAdminOut:
    """Transition a grievance to reviewing / resolved / rejected.

    Rules:
     • resolved + rejected are terminal — sets resolved_at timestamp
     • reviewing is transient — resolved_at stays NULL
     • resolution text is required when moving to resolved/rejected (otherwise
       the user gets a status change with no explanation — fails ISO 10667-2
       §7 transparency)
    """
    if payload.status in ("resolved", "rejected") and not (payload.resolution and payload.resolution.strip()):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "RESOLUTION_REQUIRED",
                "message": "Resolution text is required when closing a grievance (ISO 10667-2 §7)",
            },
        )

    now = datetime.now(UTC).isoformat()
    update_body: dict = {
        "status": payload.status,
        "updated_at": now,
    }
    if payload.resolution is not None:
        update_body["resolution"] = payload.resolution.strip()
    if payload.admin_notes is not None:
        update_body["admin_notes"] = payload.admin_notes.strip()
    if payload.status in ("resolved", "rejected"):
        update_body["resolved_at"] = now

    try:
        result = await db.table("grievances").update(update_body).eq("id", grievance_id).execute()
    except Exception as exc:
        logger.error("Grievance transition failed", admin_id=admin_id, grievance_id=grievance_id, error=str(exc)[:200])
        raise HTTPException(
            status_code=500,
            detail={"code": "GRIEVANCE_UPDATE_FAILED", "message": "Could not update grievance"},
        )

    rows = result.data or []
    if not rows:
        raise HTTPException(
            status_code=404,
            detail={"code": "GRIEVANCE_NOT_FOUND", "message": "Grievance not found"},
        )
    logger.info(
        "Grievance transitioned",
        admin_id=admin_id,
        grievance_id=grievance_id,
        new_status=payload.status,
    )
    return _to_admin_out(rows[0])


# ── Human review requests (GDPR Art.22(3)) ────────────────────────────────────


class HumanReviewRequestCreate(BaseModel):
    automated_decision_id: str = Field(..., min_length=1, max_length=64)
    request_reason: str = Field(..., min_length=10, max_length=5000)
    source_product: Literal["volaura", "mindshift", "lifesim", "brandedby", "zeus"] = "volaura"


class HumanReviewRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    automated_decision_id: str
    source_product: str
    request_reason: str
    requested_at: str
    sla_deadline: str
    status: str
    resolved_at: str | None
    resolution_notes: str | None
    reviewer_user_id: str | None


class HumanReviewRequestListResponse(BaseModel):
    data: list[HumanReviewRequestOut]


class HumanReviewRequestStatusUpdate(BaseModel):
    status: Literal["in_review", "resolved_uphold", "resolved_overturn", "escalated_to_authority"]
    resolution_notes: str | None = Field(default=None, max_length=5000)


class AutomatedDecisionOut(BaseModel):
    id: str
    decision_type: str
    created_at: str
    human_reviewable: bool


class AutomatedDecisionListResponse(BaseModel):
    data: list[AutomatedDecisionOut]


def _to_human_review_out(row: dict) -> HumanReviewRequestOut:
    return HumanReviewRequestOut(
        id=str(row["id"]),
        user_id=str(row["user_id"]),
        automated_decision_id=str(row["automated_decision_id"]),
        source_product=row["source_product"],
        request_reason=row["request_reason"],
        requested_at=str(row["requested_at"]),
        sla_deadline=str(row["sla_deadline"]),
        status=row["status"],
        resolved_at=(str(row["resolved_at"]) if row.get("resolved_at") else None),
        resolution_notes=row.get("resolution_notes"),
        reviewer_user_id=(str(row["reviewer_user_id"]) if row.get("reviewer_user_id") else None),
    )


@router.get("/human-review/decisions", response_model=AutomatedDecisionListResponse)
@limiter.limit(RATE_DEFAULT)
async def list_my_automated_decisions(
    request: Request,
    user_id: CurrentUserId,
    db: SupabaseAdmin,
    limit: int = 20,
) -> AutomatedDecisionListResponse:
    """List caller's recent automated decisions that can be contested."""
    if limit > 100:
        limit = 100
    result = await (
        db.table("automated_decision_log")
        .select("id,decision_type,created_at,human_reviewable")
        .eq("user_id", str(user_id))
        .eq("human_reviewable", True)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    items = [
        AutomatedDecisionOut(
            id=str(r["id"]),
            decision_type=r["decision_type"],
            created_at=str(r["created_at"]),
            human_reviewable=bool(r.get("human_reviewable", True)),
        )
        for r in (result.data or [])
    ]
    return AutomatedDecisionListResponse(data=items)


@router.post("/human-review", response_model=HumanReviewRequestOut, status_code=201)
@limiter.limit(RATE_AUTH)
async def create_human_review_request(
    request: Request,
    payload: HumanReviewRequestCreate,
    user_id: CurrentUserId,
    db: SupabaseAdmin,
) -> HumanReviewRequestOut:
    """Create a formal human review request for an automated decision."""
    try:
        exists = (
            await db.table("automated_decision_log")
            .select("id,user_id")
            .eq("id", payload.automated_decision_id)
            .maybe_single()
            .execute()
        )
        if not exists.data:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "DECISION_NOT_FOUND",
                    "message": "Automated decision not found",
                },
            )
        if str(exists.data["user_id"]) != str(user_id):
            raise HTTPException(
                status_code=403,
                detail={"code": "DECISION_NOT_OWNED", "message": "You can only request review for your own decisions"},
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Human review lookup failed", user_id=str(user_id), error=str(exc)[:200])
        raise HTTPException(
            status_code=500,
            detail={"code": "HUMAN_REVIEW_CREATE_FAILED", "message": "Could not create review request"},
        )

    try:
        result = await (
            db.table("human_review_requests")
            .insert(
                {
                    "user_id": str(user_id),
                    "automated_decision_id": payload.automated_decision_id,
                    "source_product": payload.source_product,
                    "request_reason": payload.request_reason.strip(),
                }
            )
            .execute()
        )
    except Exception as exc:
        logger.error("Human review insert failed", user_id=str(user_id), error=str(exc)[:200])
        raise HTTPException(
            status_code=500,
            detail={"code": "HUMAN_REVIEW_CREATE_FAILED", "message": "Could not create review request"},
        )

    rows = result.data or []
    if not rows:
        raise HTTPException(
            status_code=500,
            detail={"code": "HUMAN_REVIEW_CREATE_FAILED", "message": "Could not create review request"},
        )
    return _to_human_review_out(rows[0])


@router.get("/human-review", response_model=HumanReviewRequestListResponse)
@limiter.limit(RATE_DEFAULT)
async def list_my_human_review_requests(
    request: Request,
    user_id: CurrentUserId,
    db: SupabaseAdmin,
) -> HumanReviewRequestListResponse:
    """List caller's human review requests newest-first."""
    result = await (
        db.table("human_review_requests")
        .select("*")
        .eq("user_id", str(user_id))
        .order("requested_at", desc=True)
        .limit(100)
        .execute()
    )
    return HumanReviewRequestListResponse(data=[_to_human_review_out(r) for r in (result.data or [])])


@router.get("/human-review/admin/pending", response_model=HumanReviewRequestListResponse)
@limiter.limit(RATE_DEFAULT)
async def admin_list_pending_human_review_requests(
    request: Request,
    db: SupabaseAdmin,
    _admin_id: str = Depends(require_platform_admin),
) -> HumanReviewRequestListResponse:
    """Admin queue: pending + in_review human review requests."""
    result = await (
        db.table("human_review_requests")
        .select("*")
        .in_("status", ["pending", "in_review"])
        .order("requested_at", desc=False)
        .limit(200)
        .execute()
    )
    return HumanReviewRequestListResponse(data=[_to_human_review_out(r) for r in (result.data or [])])


@router.patch("/human-review/admin/{request_id}", response_model=HumanReviewRequestOut)
@limiter.limit(RATE_AUTH)
async def admin_transition_human_review_request(
    request: Request,
    request_id: str,
    payload: HumanReviewRequestStatusUpdate,
    db: SupabaseAdmin,
    admin_id: str = Depends(require_platform_admin),
) -> HumanReviewRequestOut:
    """Admin transition for human review requests."""
    if payload.status in ("resolved_uphold", "resolved_overturn") and not (
        payload.resolution_notes and payload.resolution_notes.strip()
    ):
        raise HTTPException(
            status_code=422,
            detail={"code": "RESOLUTION_REQUIRED", "message": "resolution_notes is required for resolved statuses"},
        )

    update_body: dict = {
        "status": payload.status,
        "reviewer_user_id": admin_id,
    }
    if payload.resolution_notes is not None:
        update_body["resolution_notes"] = payload.resolution_notes.strip()
    if payload.status in ("resolved_uphold", "resolved_overturn"):
        update_body["resolved_at"] = datetime.now(UTC).isoformat()

    try:
        result = await db.table("human_review_requests").update(update_body).eq("id", request_id).execute()
    except Exception as exc:
        logger.error(
            "Human review transition failed", admin_id=str(admin_id), request_id=request_id, error=str(exc)[:200]
        )
        raise HTTPException(
            status_code=500,
            detail={"code": "HUMAN_REVIEW_UPDATE_FAILED", "message": "Could not update review request"},
        )

    rows = result.data or []
    if not rows:
        raise HTTPException(
            status_code=404,
            detail={"code": "HUMAN_REVIEW_NOT_FOUND", "message": "Review request not found"},
        )
    return _to_human_review_out(rows[0])
