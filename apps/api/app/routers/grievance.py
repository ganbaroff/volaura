"""Formal AURA grievance intake — Constitution G35 / ISO 10667-2 §7.

A user who disagrees with their AURA score (any competency, any session) must
have a documented contest path. This router owns the intake surface:
 • POST /api/aura/grievance — file a grievance
 • GET  /api/aura/grievance — list own grievances with status

Admin review / resolution happens server-side via service-role client on a
separate admin endpoint (not in this file — that lands in a later iteration).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field

from app.deps import CurrentUserId, SupabaseAdmin
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
    for row in (result.data or []):
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
