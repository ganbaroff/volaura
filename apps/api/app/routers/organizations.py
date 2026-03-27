"""Organization management and volunteer search endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query, Request
from loguru import logger

from app.deps import CurrentUserId, SupabaseAdmin, SupabaseUser
from app.middleware.rate_limit import limiter, RATE_PROFILE_WRITE, RATE_DEFAULT
from app.schemas.organization import (
    AssignAssessmentRequest,
    AssignmentResponse,
    BadgeDistribution,
    OrgDashboardStats,
    OrgVolunteerRow,
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
    VolunteerSearchRequest,
    VolunteerSearchResult,
)
from app.services.embeddings import generate_embedding

router = APIRouter(prefix="/organizations", tags=["Organizations"])


# ── Org CRUD ──────────────────────────────────────────────────────────────────

@router.get("", response_model=list[OrganizationResponse])
async def list_organizations(db: SupabaseAdmin) -> list[OrganizationResponse]:
    """List all public organizations."""
    result = await db.table("organizations").select("*").order("name").execute()
    return [OrganizationResponse(**row) for row in (result.data or [])]


@router.get("/me", response_model=OrganizationResponse)
async def get_my_organization(db_admin: SupabaseAdmin, user_id: CurrentUserId) -> OrganizationResponse:
    """Get the organization owned by the current user."""
    result = await db_admin.table("organizations").select("*").eq("owner_id", user_id).single().execute()
    if not result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "ORG_NOT_FOUND", "message": "You do not have an organization"},
        )
    return OrganizationResponse(**result.data)


@router.post("", response_model=OrganizationResponse, status_code=201)
@limiter.limit(RATE_PROFILE_WRITE)
async def create_organization(
    request: Request,
    payload: OrganizationCreate,
    db: SupabaseUser,
    user_id: CurrentUserId,
    db_admin: SupabaseAdmin,
) -> OrganizationResponse:
    """Create an organization for the current user."""
    # One org per user
    existing = await db_admin.table("organizations").select("id").eq("owner_id", user_id).execute()
    if existing.data:
        raise HTTPException(
            status_code=409,
            detail={"code": "ORG_EXISTS", "message": "You already have an organization"},
        )

    result = await db.table("organizations").insert({
        "owner_id": user_id,
        **payload.model_dump(),
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail={"code": "CREATE_FAILED", "message": "Failed to create organization"})
    return OrganizationResponse(**result.data[0])


@router.put("/me", response_model=OrganizationResponse)
@limiter.limit(RATE_PROFILE_WRITE)
async def update_my_organization(
    request: Request,
    payload: OrganizationUpdate,
    db: SupabaseUser,
    user_id: CurrentUserId,
) -> OrganizationResponse:
    """Update the current user's organization."""
    update_data = payload.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=422, detail={"code": "NO_FIELDS", "message": "No fields to update"})

    result = await db.table("organizations").update(update_data).eq("owner_id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail={"code": "ORG_NOT_FOUND", "message": "Organization not found"})
    return OrganizationResponse(**result.data[0])


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(org_id: str, db: SupabaseAdmin) -> OrganizationResponse:
    """Get a public organization by ID."""
    result = await db.table("organizations").select("*").eq("id", org_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail={"code": "ORG_NOT_FOUND", "message": "Organization not found"})
    return OrganizationResponse(**result.data)


# ── Org dashboard ─────────────────────────────────────────────────────────────

@router.get("/me/dashboard", response_model=OrgDashboardStats)
async def get_org_dashboard(
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
) -> OrgDashboardStats:
    """Aggregate stats for the B2B org management dashboard.

    Returns assignment completion rates, avg AURA, badge distribution,
    and top 5 volunteers for the org owner's dashboard.
    """
    # Get org
    org_result = await db_admin.table("organizations").select("id, name").eq("owner_id", user_id).single().execute()
    if not org_result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "ORG_NOT_FOUND", "message": "You do not have an organization"},
        )
    org_id = org_result.data["id"]
    org_name = org_result.data["name"]

    # All sessions assigned by this org
    sessions_result = await db_admin.table("assessment_sessions").select(
        "volunteer_id, status"
    ).eq("assigned_by_org_id", org_id).execute()
    sessions = sessions_result.data or []

    total_assigned = len(sessions)
    completed_vols = {s["volunteer_id"] for s in sessions if s["status"] == "completed"}
    total_completed = len(completed_vols)
    completion_rate = round(total_completed / total_assigned, 3) if total_assigned > 0 else 0.0

    # AURA scores for completed volunteers
    badge_dist = BadgeDistribution()
    avg_aura: float | None = None
    top_volunteers: list[OrgVolunteerRow] = []

    if completed_vols:
        aura_result = await db_admin.table("aura_scores").select(
            "volunteer_id, total_score, badge_tier"
        ).in_("volunteer_id", list(completed_vols)).execute()
        aura_rows = aura_result.data or []

        if aura_rows:
            scores = [float(r["total_score"]) for r in aura_rows if r.get("total_score") is not None]
            avg_aura = round(sum(scores) / len(scores), 2) if scores else None

            for r in aura_rows:
                tier = (r.get("badge_tier") or "none").lower()
                if tier == "platinum":
                    badge_dist.platinum += 1
                elif tier == "gold":
                    badge_dist.gold += 1
                elif tier == "silver":
                    badge_dist.silver += 1
                elif tier == "bronze":
                    badge_dist.bronze += 1
                else:
                    badge_dist.none += 1

            # Top 5 by AURA
            top_ids = [r["volunteer_id"] for r in sorted(aura_rows, key=lambda x: float(x.get("total_score") or 0), reverse=True)[:5]]
            profiles_result = await db_admin.table("profiles").select(
                "id, username, display_name"
            ).in_("id", top_ids).execute()
            profile_map = {p["id"]: p for p in (profiles_result.data or [])}
            aura_map = {r["volunteer_id"]: r for r in aura_rows}

            # Count competencies completed per volunteer for this org
            comp_sessions = await db_admin.table("assessment_sessions").select(
                "volunteer_id"
            ).eq("assigned_by_org_id", org_id).eq("status", "completed").execute()
            comp_count: dict[str, int] = {}
            for s in (comp_sessions.data or []):
                comp_count[s["volunteer_id"]] = comp_count.get(s["volunteer_id"], 0) + 1

            for vid in top_ids:
                p = profile_map.get(vid, {})
                a = aura_map.get(vid, {})
                top_volunteers.append(OrgVolunteerRow(
                    volunteer_id=vid,
                    username=p.get("username", vid[:8]),
                    display_name=p.get("display_name"),
                    overall_score=float(a.get("total_score", 0)),
                    badge_tier=a.get("badge_tier"),
                    competencies_completed=comp_count.get(vid, 0),
                    last_activity=None,  # TODO: add completed_at to sessions
                ))

    return OrgDashboardStats(
        org_id=org_id,
        org_name=org_name,
        total_assigned=total_assigned,
        total_completed=total_completed,
        completion_rate=completion_rate,
        avg_aura_score=avg_aura,
        badge_distribution=badge_dist,
        top_volunteers=top_volunteers,
    )


@router.get("/me/volunteers", response_model=list[OrgVolunteerRow])
async def list_org_volunteers(
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
    status: str | None = Query(default=None, description="Filter by session status: assigned|completed|in_progress"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[OrgVolunteerRow]:
    """List all volunteers assigned assessments by this org.

    Returns profile + AURA data for each volunteer.
    Supports filtering by session status (assigned/completed/in_progress).
    """
    org_result = await db_admin.table("organizations").select("id").eq("owner_id", user_id).single().execute()
    if not org_result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "ORG_NOT_FOUND", "message": "You do not have an organization"},
        )
    org_id = org_result.data["id"]

    # Get distinct volunteer IDs assigned by this org
    q = db_admin.table("assessment_sessions").select("volunteer_id, status").eq("assigned_by_org_id", org_id)
    if status:
        valid_statuses = {"assigned", "completed", "in_progress"}
        if status not in valid_statuses:
            raise HTTPException(
                status_code=422,
                detail={"code": "INVALID_STATUS", "message": f"Status must be one of: {', '.join(valid_statuses)}"},
            )
        q = q.eq("status", status)

    sessions_result = await q.execute()
    sessions = sessions_result.data or []

    # Distinct volunteers with completion counts
    vol_data: dict[str, dict] = {}
    for s in sessions:
        vid = s["volunteer_id"]
        if vid not in vol_data:
            vol_data[vid] = {"completed": 0, "total": 0}
        vol_data[vid]["total"] += 1
        if s["status"] == "completed":
            vol_data[vid]["completed"] += 1

    if not vol_data:
        return []

    all_vol_ids = list(vol_data.keys())
    # Pagination on volunteer level
    paginated_ids = all_vol_ids[offset: offset + limit]

    # Fetch profiles + AURA in parallel
    profiles_result = await db_admin.table("profiles").select(
        "id, username, display_name"
    ).in_("id", paginated_ids).execute()
    aura_result = await db_admin.table("aura_scores").select(
        "volunteer_id, total_score, badge_tier"
    ).in_("volunteer_id", paginated_ids).execute()

    profile_map = {p["id"]: p for p in (profiles_result.data or [])}
    aura_map = {r["volunteer_id"]: r for r in (aura_result.data or [])}

    rows: list[OrgVolunteerRow] = []
    for vid in paginated_ids:
        p = profile_map.get(vid, {})
        a = aura_map.get(vid, {})
        d = vol_data[vid]
        rows.append(OrgVolunteerRow(
            volunteer_id=vid,
            username=p.get("username", vid[:8]),
            display_name=p.get("display_name"),
            overall_score=float(a["total_score"]) if a.get("total_score") is not None else None,
            badge_tier=a.get("badge_tier"),
            competencies_completed=d["completed"],
            last_activity=None,
        ))

    # Sort: completed first, then by score desc
    rows.sort(key=lambda r: (-(r.overall_score or 0), -r.competencies_completed))
    return rows


# ── Volunteer search ──────────────────────────────────────────────────────────

@router.post("/search/volunteers", response_model=list[VolunteerSearchResult])
@limiter.limit(RATE_DEFAULT)
async def search_volunteers(
    request: Request,
    payload: VolunteerSearchRequest,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
) -> list[VolunteerSearchResult]:
    """Semantic volunteer search using pgvector + rule-based fallback.

    Requires B2B auth. Uses Gemini embeddings for semantic search;
    falls back to rule-based filter if embedding unavailable.
    """
    # Attempt semantic search
    query_embedding = await generate_embedding(payload.query)

    if query_embedding:
        rpc_result = await db_admin.rpc(
            "match_volunteers",
            {
                "query_embedding": query_embedding,
                "match_count": payload.limit + payload.offset,
                "min_aura": payload.min_aura,
            },
        ).execute()
        rows = (rpc_result.data or [])[payload.offset: payload.offset + payload.limit]
    else:
        # Rule-based fallback: filter aura_scores + profiles
        q = (
            db_admin.table("aura_scores")
            .select("volunteer_id, total_score, badge_tier, elite_status")
            .gte("total_score", payload.min_aura)
        )
        if payload.badge_tier:
            q = q.eq("badge_tier", payload.badge_tier)

        aura_result = await q.limit(payload.limit + payload.offset).execute()
        rows = (aura_result.data or [])[payload.offset:]

    if not rows:
        return []

    # Enrich with profile data
    volunteer_ids = [r["volunteer_id"] for r in rows]
    profiles_result = await db_admin.table("profiles").select(
        "id, username, display_name, location, languages"
    ).in_("id", volunteer_ids).execute()

    profile_map = {p["id"]: p for p in (profiles_result.data or [])}

    results = []
    for row in rows:
        vid = row["volunteer_id"]
        p = profile_map.get(vid, {})

        # Apply post-filter for languages and location
        if payload.languages:
            vol_langs = p.get("languages") or []
            if not any(lang in vol_langs for lang in payload.languages):
                continue
        if payload.location and payload.location.lower() not in (p.get("location") or "").lower():
            continue

        results.append(VolunteerSearchResult(
            volunteer_id=vid,
            username=p.get("username", vid[:8]),
            display_name=p.get("display_name"),
            overall_score=float(row.get("total_score", 0)),
            badge_tier=row.get("badge_tier", "none"),
            elite_status=bool(row.get("elite_status", False)),
            location=p.get("location"),
            languages=p.get("languages") or [],
            similarity=row.get("similarity"),
        ))

    return results


# ── Assessment Assignment ────────────────────────────────────────────────────

@router.post("/assign-assessments", response_model=AssignmentResponse)
@limiter.limit(RATE_PROFILE_WRITE)
async def assign_assessments(
    request: Request,
    payload: AssignAssessmentRequest,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
) -> AssignmentResponse:
    """Assign competency assessments to specific volunteers.

    Security checks:
    1. Caller must own an organization
    2. Max 100 volunteers per request (rate limit on endpoint too)
    3. Competency slugs validated against DB
    4. Duplicate assignments skipped (not error)
    """
    # Verify caller owns an org
    org_result = await db_admin.table("organizations").select("id, name").eq("owner_id", user_id).single().execute()
    if not org_result.data:
        raise HTTPException(
            status_code=403,
            detail={"code": "NOT_ORG_OWNER", "message": "You must own an organization to assign assessments"},
        )
    org_id = org_result.data["id"]
    org_name = org_result.data["name"]

    # Validate competency slugs exist
    comp_result = await db_admin.table("competencies").select("id, slug").execute()
    valid_slugs = {c["slug"]: c["id"] for c in (comp_result.data or [])}
    invalid_slugs = [s for s in payload.competency_slugs if s not in valid_slugs]
    if invalid_slugs:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_COMPETENCY", "message": f"Unknown competencies: {', '.join(invalid_slugs)}"},
        )

    # Validate volunteer IDs exist
    vol_result = await db_admin.table("profiles").select("id").in_("id", payload.volunteer_ids).execute()
    existing_ids = {p["id"] for p in (vol_result.data or [])}
    missing_ids = [vid for vid in payload.volunteer_ids if vid not in existing_ids]

    deadline = datetime.now(timezone.utc) + timedelta(days=payload.deadline_days)
    assigned = 0
    skipped = 0
    errors: list[str] = []
    assignments: list[dict] = []

    for vid in payload.volunteer_ids:
        if vid in missing_ids:
            errors.append(f"Volunteer {vid[:8]}... not found")
            skipped += 1
            continue

        for slug in payload.competency_slugs:
            comp_id = valid_slugs[slug]

            # Check for existing in-progress session (skip duplicate)
            existing = await db_admin.table("assessment_sessions").select("id").eq(
                "volunteer_id", vid
            ).eq("competency_id", comp_id).eq("status", "assigned").execute()

            if existing.data:
                skipped += 1
                continue

            # Create assigned session
            session_id = str(uuid.uuid4())
            await db_admin.table("assessment_sessions").insert({
                "id": session_id,
                "volunteer_id": vid,
                "competency_id": comp_id,
                "status": "assigned",
                "assigned_by_org_id": org_id,
                "assigned_at": datetime.now(timezone.utc).isoformat(),
                "deadline": deadline.isoformat(),
                "assignment_message": payload.message,
                "theta_estimate": 0.0,
                "theta_se": 1.5,
                "answers": {},
            }).execute()

            assignments.append({
                "session_id": session_id,
                "volunteer_id": vid,
                "competency_slug": slug,
                "deadline": deadline.isoformat(),
            })
            assigned += 1

    logger.info(
        "Assessments assigned",
        org_id=org_id,
        org_name=org_name,
        assigned=assigned,
        skipped=skipped,
        errors=len(errors),
    )

    return AssignmentResponse(
        assigned_count=assigned,
        skipped_count=skipped,
        errors=errors,
        assignments=assignments,
    )
