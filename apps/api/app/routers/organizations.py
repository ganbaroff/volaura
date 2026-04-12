"""Organization management and volunteer search endpoints."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Query, Request
from loguru import logger

from app.deps import CurrentUserId, SupabaseAdmin, SupabaseUser
from app.middleware.rate_limit import RATE_DEFAULT, RATE_DISCOVERY, RATE_PROFILE_WRITE, limiter
from app.schemas.organization import (
    AssignAssessmentRequest,
    AssignmentResponse,
    BadgeDistribution,
    CollectiveAuraResponse,
    IntroRequestCreate,
    IntroRequestResponse,
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
    OrgDashboardStats,
    OrgVolunteerRow,
    SavedSearchCreate,
    SavedSearchOut,
    SavedSearchUpdate,
    VolunteerSearchRequest,
    VolunteerSearchResult,
)
from app.services.embeddings import generate_embedding

router = APIRouter(prefix="/organizations", tags=["Organizations"])


# ── Org CRUD ──────────────────────────────────────────────────────────────────


@router.get("", response_model=list[OrganizationResponse])
@limiter.limit(RATE_DEFAULT)
async def list_organizations(request: Request, db: SupabaseAdmin, user_id: CurrentUserId) -> list[OrganizationResponse]:
    """List all public organizations. Requires authentication to prevent unauthenticated enumeration."""
    result = (
        await db.table("organizations")
        .select("id, name, description, logo_url, type, website, is_active")
        .order("name")
        .execute()
    )
    return [OrganizationResponse(**row) for row in (result.data or [])]


@router.get("/me", response_model=OrganizationResponse)
@limiter.limit(RATE_DEFAULT)
async def get_my_organization(
    request: Request, db_admin: SupabaseAdmin, user_id: CurrentUserId
) -> OrganizationResponse:
    """Get the organization owned by the current user."""
    result = await db_admin.table("organizations").select("*").eq("owner_id", user_id).maybe_single().execute()
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

    result = (
        await db.table("organizations")
        .insert(
            {
                "owner_id": user_id,
                **payload.model_dump(),
            }
        )
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=500, detail={"code": "CREATE_FAILED", "message": "Failed to create organization"}
        )
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


# NOTE: /saved-searches GET placed here (before /{org_id}) to prevent route shadowing.
# FastAPI matches routes in declaration order — static paths must precede parameterized.
# Same fix class as Mistake #P0-ROUTE (Session 42).
@router.get(
    "/saved-searches",
    response_model=list[SavedSearchOut],
    summary="List saved searches",
)
@limiter.limit(RATE_DEFAULT)
async def list_saved_searches_early(
    request: Request,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
) -> list[SavedSearchOut]:
    """List all saved searches for the current user's organization.

    Defined before /{org_id} to prevent route shadowing.
    """
    org_id = await _get_org_id_for_user(db_admin, user_id)
    result = (
        await db_admin.table("org_saved_searches")
        .select("*")
        .eq("org_id", org_id)
        .order("created_at", desc=True)
        .execute()
    )
    return [SavedSearchOut(**row) for row in (result.data or [])]


@router.get("/{org_id}", response_model=OrganizationResponse)
@limiter.limit(RATE_DEFAULT)
async def get_organization(
    request: Request, org_id: str, db: SupabaseAdmin, user_id: CurrentUserId
) -> OrganizationResponse:
    """Get a public organization by ID. Requires authentication to prevent unauthenticated UUID enumeration."""
    result = await db.table("organizations").select("*").eq("id", org_id).maybe_single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail={"code": "ORG_NOT_FOUND", "message": "Organization not found"})
    return OrganizationResponse(**result.data)


# ── Collective AURA Ladders ───────────────────────────────────────────────────


@router.get("/{org_id}/collective-aura", response_model=CollectiveAuraResponse)
@limiter.limit(RATE_DEFAULT)
async def get_collective_aura(
    request: Request,
    org_id: str,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
) -> CollectiveAuraResponse:
    """Aggregated AURA talent pool metrics for an org's verified professionals.

    Ownership-gated (403 for non-owners). Supports Collective AURA Ladders feature.
    AURA is a global credential — a volunteer's score appears in all org pools they
    engaged with (this is intentional, matching the platform's open credential model).
    """
    # Fail-closed: verify ownership FIRST (Security Agent mandate — prevent Mistake #57)
    org_check = (
        await db_admin.table("organizations")
        .select("id")
        .eq("id", org_id)
        .eq("owner_id", user_id)
        .maybe_single()
        .execute()
    )
    if not org_check.data:
        raise HTTPException(status_code=403, detail={"code": "NOT_ORG_OWNER", "message": "Access denied"})

    # Get distinct volunteers who completed assessments for this org
    sessions = (
        await db_admin.table("assessment_sessions")
        .select("volunteer_id")
        .eq("organization_id", org_id)
        .eq("status", "completed")
        .execute()
    )
    volunteer_ids = list({row["volunteer_id"] for row in (sessions.data or [])})

    if not volunteer_ids:
        return CollectiveAuraResponse(org_id=org_id, count=0)

    # Fetch AURA scores for these volunteers
    aura_rows = (
        await db_admin.table("aura_scores")
        .select("volunteer_id, total_score")
        .in_("volunteer_id", volunteer_ids)
        .execute()
    )
    scores = [row["total_score"] for row in (aura_rows.data or []) if row.get("total_score") is not None]

    if not scores:
        return CollectiveAuraResponse(org_id=org_id, count=len(volunteer_ids))

    avg_aura = sum(scores) / len(scores)

    # Trend: compare to snapshot 30 days ago (use reward_logs or skip if unavailable)
    # Simplified: trend is None until historical snapshots are implemented
    trend: float | None = None

    return CollectiveAuraResponse(
        org_id=org_id,
        count=len(volunteer_ids),
        avg_aura=round(avg_aura, 1),
        trend=trend,
    )


# ── Org dashboard ─────────────────────────────────────────────────────────────


@router.get("/me/dashboard", response_model=OrgDashboardStats)
@limiter.limit(RATE_DEFAULT)
async def get_org_dashboard(
    request: Request,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
) -> OrgDashboardStats:
    """Aggregate stats for the B2B org management dashboard.

    Returns assignment completion rates, avg AURA, badge distribution,
    and top 5 volunteers for the org owner's dashboard.
    """
    # Get org
    org_result = (
        await db_admin.table("organizations").select("id, name").eq("owner_id", user_id).maybe_single().execute()
    )
    if not org_result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "ORG_NOT_FOUND", "message": "You do not have an organization"},
        )
    org_id = org_result.data["id"]
    org_name = org_result.data["name"]

    # All sessions assigned by this org — SEC-Q4 / BUG-005: capped at 2000 to prevent OOM.
    # Dashboard stats are approximations; full accuracy requires async aggregation (post-launch).
    _DASHBOARD_SESSION_CAP = 2000
    sessions_result = (
        await db_admin.table("assessment_sessions")
        .select("volunteer_id, status")
        .eq("assigned_by_org_id", org_id)
        .limit(_DASHBOARD_SESSION_CAP)
        .execute()
    )
    sessions = sessions_result.data or []
    if len(sessions) == _DASHBOARD_SESSION_CAP:
        logger.warning(
            "get_org_dashboard: session cap reached — stats are approximate", org_id=org_id, cap=_DASHBOARD_SESSION_CAP
        )

    total_assigned = len(sessions)
    completed_vols = {s["volunteer_id"] for s in sessions if s["status"] == "completed"}
    total_completed = len(completed_vols)
    completion_rate = round(total_completed / total_assigned, 3) if total_assigned > 0 else 0.0

    # AURA scores for completed volunteers
    badge_dist = BadgeDistribution()
    avg_aura: float | None = None
    top_volunteers: list[OrgVolunteerRow] = []

    if completed_vols:
        aura_result = (
            await db_admin.table("aura_scores")
            .select("volunteer_id, total_score, badge_tier")
            .in_("volunteer_id", list(completed_vols))
            .execute()
        )
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
            top_ids = [
                r["volunteer_id"]
                for r in sorted(aura_rows, key=lambda x: float(x.get("total_score") or 0), reverse=True)[:5]
            ]
            profiles_result = (
                await db_admin.table("profiles").select("id, username, display_name").in_("id", top_ids).execute()
            )
            profile_map = {p["id"]: p for p in (profiles_result.data or [])}
            aura_map = {r["volunteer_id"]: r for r in aura_rows}

            # Count competencies completed per volunteer for this org
            comp_sessions = (
                await db_admin.table("assessment_sessions")
                .select("volunteer_id")
                .eq("assigned_by_org_id", org_id)
                .eq("status", "completed")
                .execute()
            )
            comp_count: dict[str, int] = {}
            for s in comp_sessions.data or []:
                comp_count[s["volunteer_id"]] = comp_count.get(s["volunteer_id"], 0) + 1

            for vid in top_ids:
                p = profile_map.get(vid, {})
                a = aura_map.get(vid, {})
                top_volunteers.append(
                    OrgVolunteerRow(
                        volunteer_id=vid,
                        username=p.get("username", vid[:8]),
                        display_name=p.get("display_name"),
                        overall_score=float(a.get("total_score", 0)),
                        badge_tier=a.get("badge_tier"),
                        competencies_completed=comp_count.get(vid, 0),
                        last_activity=None,  # TODO: add completed_at to sessions
                    )
                )

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
@limiter.limit(RATE_DISCOVERY)
async def list_org_volunteers(
    request: Request,
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
    org_result = await db_admin.table("organizations").select("id").eq("owner_id", user_id).maybe_single().execute()
    if not org_result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "ORG_NOT_FOUND", "message": "You do not have an organization"},
        )
    org_id = org_result.data["id"]

    # Get distinct volunteer IDs assigned by this org
    # SEC-Q4 / BUG-005: cap at 10k sessions to prevent OOM on large orgs.
    # Pagination is applied at volunteer level after dedup — this cap bounds memory usage.
    _LIST_SESSION_CAP = 10_000
    q = db_admin.table("assessment_sessions").select("volunteer_id, status").eq("assigned_by_org_id", org_id)
    if status:
        valid_statuses = {"assigned", "completed", "in_progress"}
        if status not in valid_statuses:
            raise HTTPException(
                status_code=422,
                detail={"code": "INVALID_STATUS", "message": f"Status must be one of: {', '.join(valid_statuses)}"},
            )
        q = q.eq("status", status)

    sessions_result = await q.limit(_LIST_SESSION_CAP).execute()
    sessions = sessions_result.data or []
    if len(sessions) == _LIST_SESSION_CAP:
        logger.warning(
            "list_org_volunteers: session cap reached — pagination may be incomplete",
            org_id=org_id,
            cap=_LIST_SESSION_CAP,
        )

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
    paginated_ids = all_vol_ids[offset : offset + limit]

    # Fetch profiles + AURA in parallel
    profiles_result = (
        await db_admin.table("profiles").select("id, username, display_name").in_("id", paginated_ids).execute()
    )
    aura_result = (
        await db_admin.table("aura_scores")
        .select("volunteer_id, total_score, badge_tier")
        .in_("volunteer_id", paginated_ids)
        .execute()
    )

    profile_map = {p["id"]: p for p in (profiles_result.data or [])}
    aura_map = {r["volunteer_id"]: r for r in (aura_result.data or [])}

    rows: list[OrgVolunteerRow] = []
    for vid in paginated_ids:
        p = profile_map.get(vid, {})
        a = aura_map.get(vid, {})
        d = vol_data[vid]
        rows.append(
            OrgVolunteerRow(
                volunteer_id=vid,
                username=p.get("username", vid[:8]),
                display_name=p.get("display_name"),
                overall_score=float(a["total_score"]) if a.get("total_score") is not None else None,
                badge_tier=a.get("badge_tier"),
                competencies_completed=d["completed"],
                last_activity=None,
            )
        )

    # Sort: completed first, then by score desc
    rows.sort(key=lambda r: (-(r.overall_score or 0), -r.competencies_completed))
    return rows


# ── Volunteer search ──────────────────────────────────────────────────────────


@router.post("/search/volunteers", response_model=list[VolunteerSearchResult])
@limiter.limit(RATE_DISCOVERY)
async def search_volunteers(
    request: Request,
    payload: VolunteerSearchRequest,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
) -> list[VolunteerSearchResult]:
    """Semantic volunteer search using pgvector + rule-based fallback.

    Requires organization account. Uses Gemini embeddings for semantic search;
    falls back to rule-based filter if embedding unavailable or slow.
    """
    # Dual org-role check: account_type in profiles + owns an organization row
    caller = await db_admin.table("profiles").select("account_type").eq("id", str(user_id)).maybe_single().execute()
    if not caller.data or caller.data.get("account_type") != "organization":
        raise HTTPException(
            status_code=403,
            detail={"code": "ORG_REQUIRED", "message": "Only organization accounts can search volunteers"},
        )
    org_row = await db_admin.table("organizations").select("id").eq("owner_id", str(user_id)).maybe_single().execute()
    if not org_row.data:
        raise HTTPException(
            status_code=403,
            detail={"code": "ORG_REQUIRED", "message": "Create an organization profile before searching"},
        )

    # Validate non-empty query
    if not payload.query.strip():
        raise HTTPException(
            status_code=422,
            detail={"code": "QUERY_REQUIRED", "message": "Search query cannot be empty"},
        )

    # Attempt semantic embedding with timeout
    query_embedding = None
    try:
        query_embedding = await asyncio.wait_for(generate_embedding(payload.query), timeout=0.8)
    except TimeoutError:
        logger.warning(
            "Embedding timeout on volunteer search — using rule-based fallback", query_len=len(payload.query)
        )  # SEC-Q5: no raw query — may contain PII (names, emails)
    except Exception as e:
        logger.warning("Embedding error on volunteer search — using rule-based fallback", error=str(e)[:100])

    if query_embedding:
        rpc_result = await db_admin.rpc(
            "match_volunteers",
            {
                "query_embedding": query_embedding,
                "match_count": payload.limit + payload.offset,
                "min_aura": payload.min_aura,
            },
        ).execute()
        rows = (rpc_result.data or [])[payload.offset : payload.offset + payload.limit]
    else:
        # Rule-based fallback: fetch generously (5× limit), apply filters, then slice
        fetch_count = min(payload.limit * 5, 100)
        q = (
            db_admin.table("aura_scores")
            .select("volunteer_id, total_score, badge_tier, elite_status")
            .gte("total_score", payload.min_aura)
            # BUG-013 FIX: only return profiles with visibility=public — hidden/badge_only must not appear in org search
            .eq("visibility", "public")
        )
        if payload.badge_tier:
            q = q.eq("badge_tier", payload.badge_tier)
        aura_result = await q.limit(fetch_count).execute()
        all_rows = aura_result.data or []

        # Enrich with profile data to apply language/location pre-filter
        if all_rows and (payload.languages or payload.location):
            pids = [r["volunteer_id"] for r in all_rows]
            p_result = await db_admin.table("profiles").select("id, languages, location").in_("id", pids).execute()
            p_map = {p["id"]: p for p in (p_result.data or [])}
            filtered: list[dict] = []
            for row in all_rows:
                p = p_map.get(row["volunteer_id"], {})
                if payload.languages:
                    vol_langs = p.get("languages") or []
                    if not any(lang in vol_langs for lang in payload.languages):
                        continue
                if payload.location and payload.location.lower() not in (p.get("location") or "").lower():
                    continue
                filtered.append(row)
            all_rows = filtered

        rows = all_rows[payload.offset : payload.offset + payload.limit]

    if not rows:
        return []

    # BUG-013 FIX: post-filter by visibility=public (covers semantic/RPC path which can't filter in-query).
    # Rule-based path already has .eq("visibility","public") above — this is defense-in-depth.
    vis_result = (
        await db_admin.table("aura_scores")
        .select("volunteer_id")
        .eq("visibility", "public")
        .in_("volunteer_id", [r["volunteer_id"] for r in rows])
        .execute()
    )
    public_ids = {r["volunteer_id"] for r in (vis_result.data or [])}
    rows = [r for r in rows if r["volunteer_id"] in public_ids]

    if not rows:
        return []

    # Enrich with full profile data
    volunteer_ids = [r["volunteer_id"] for r in rows]
    profiles_result = (
        await db_admin.table("profiles")
        .select("id, username, display_name, location, languages")
        .in_("id", volunteer_ids)
        .execute()
    )
    profile_map = {p["id"]: p for p in (profiles_result.data or [])}

    results = []
    for row in rows:
        vid = row["volunteer_id"]
        p = profile_map.get(vid)
        if not p:
            # Profile missing — skip stale score row
            logger.warning("Volunteer in aura_scores but no profile found", volunteer_id=vid)
            continue

        sim_raw = row.get("similarity")
        results.append(
            VolunteerSearchResult(
                volunteer_id=vid,
                username=p["username"],
                display_name=p.get("display_name"),
                overall_score=float(row.get("total_score") or 0),
                badge_tier=row.get("badge_tier") or "none",
                elite_status=bool(row.get("elite_status", False)),
                location=p.get("location"),
                languages=p.get("languages") or [],
                similarity=float(sim_raw) if sim_raw is not None else None,
            )
        )

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
    org_result = (
        await db_admin.table("organizations").select("id, name").eq("owner_id", user_id).maybe_single().execute()
    )
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

    deadline = datetime.now(UTC) + timedelta(days=payload.deadline_days)
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
            existing = (
                await db_admin.table("assessment_sessions")
                .select("id")
                .eq("volunteer_id", vid)
                .eq("competency_id", comp_id)
                .eq("status", "assigned")
                .execute()
            )

            if existing.data:
                skipped += 1
                continue

            # Create assigned session
            session_id = str(uuid.uuid4())
            await (
                db_admin.table("assessment_sessions")
                .insert(
                    {
                        "id": session_id,
                        "volunteer_id": vid,
                        "competency_id": comp_id,
                        "status": "assigned",
                        "assigned_by_org_id": org_id,
                        "assigned_at": datetime.now(UTC).isoformat(),
                        "deadline": deadline.isoformat(),
                        "assignment_message": payload.message,
                        "theta_estimate": 0.0,
                        "theta_se": 1.5,
                        "answers": {},
                    }
                )
                .execute()
            )

            assignments.append(
                {
                    "session_id": session_id,
                    "volunteer_id": vid,
                    "competency_slug": slug,
                    "deadline": deadline.isoformat(),
                }
            )
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


# ── Intro Requests ─────────────────────────────────────────────────────────────


@router.post("/intro-requests", response_model=IntroRequestResponse, status_code=201)
@limiter.limit("5/hour")
async def create_intro_request(
    request: Request,
    payload: IntroRequestCreate,
    db: SupabaseAdmin,
    user_id: CurrentUserId,
) -> IntroRequestResponse:
    """Send an introduction request from an org to a volunteer.

    Requirements:
    - Caller must be account_type='organization' (dual-checked: this endpoint + DB)
    - Volunteer must have visible_to_orgs=True
    - Only one pending request per org-volunteer pair (DB unique constraint)
    Creates a notification for the volunteer.
    """
    # Dual org-role check: DB lookup on caller's account_type
    caller_result = (
        await db.table("profiles")
        .select("account_type, display_name, username")
        .eq("id", str(user_id))
        .maybe_single()
        .execute()
    )
    if not caller_result.data or caller_result.data.get("account_type") != "organization":
        raise HTTPException(
            status_code=403,
            detail={"code": "ORG_REQUIRED", "message": "Only organization accounts can send introduction requests"},
        )
    org_name = caller_result.data.get("display_name") or caller_result.data.get("username") or "An organization"

    # Verify volunteer is opted in and exists
    volunteer_result = (
        await db.table("profiles")
        .select("id, display_name, username, visible_to_orgs, account_type")
        .eq("id", payload.volunteer_id)
        .maybe_single()
        .execute()
    )
    if not volunteer_result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "VOLUNTEER_NOT_FOUND", "message": "Volunteer not found"},
        )
    vol = volunteer_result.data
    if not vol.get("visible_to_orgs"):
        raise HTTPException(
            status_code=403,
            detail={"code": "NOT_DISCOVERABLE", "message": "This volunteer has not opted in to org discovery"},
        )
    if vol.get("account_type") == "organization":
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_TARGET", "message": "Cannot send introduction request to an organization account"},
        )

    # Insert intro request (unique constraint handles duplicate pending)
    try:
        intro_result = (
            await db.table("intro_requests")
            .insert(
                {
                    "org_id": str(user_id),
                    "volunteer_id": payload.volunteer_id,
                    "project_name": payload.project_name,
                    "timeline": payload.timeline,
                    "message": payload.message,
                    "status": "pending",
                }
            )
            .execute()
        )
    except Exception as e:
        err_str = str(e)
        if "unique" in err_str.lower() or "duplicate" in err_str.lower():
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "REQUEST_ALREADY_PENDING",
                    "message": "You already have a pending introduction request for this volunteer",
                },
            ) from e
        logger.error("Failed to create intro request", error=err_str[:300])
        raise HTTPException(
            status_code=500, detail={"code": "CREATE_FAILED", "message": "Failed to create introduction request"}
        ) from e

    if not intro_result.data:
        raise HTTPException(
            status_code=500, detail={"code": "CREATE_FAILED", "message": "Failed to create introduction request"}
        )

    intro = intro_result.data[0]

    # Create notification for the volunteer (fire-and-forget)
    from app.services.notification_service import notify

    await notify(
        db,
        payload.volunteer_id,
        "intro_request",
        f"{org_name} wants to connect",
        body=f"Introduction request for: {payload.project_name}",
        reference_id=intro["id"],
    )

    logger.info(
        "Intro request created",
        org_id=str(user_id),
        volunteer_id=payload.volunteer_id,
        intro_id=intro["id"],
    )
    return IntroRequestResponse(**intro)


# ── Saved Searches (Sprint 8) ─────────────────────────────────────────────────

_MAX_SAVED_SEARCHES_PER_ORG = 20  # Anti-spam cap. Error message beats DB constraint.


async def _get_org_id_for_user(db_admin: SupabaseAdmin, user_id: str) -> str:
    """Returns org.id for the authenticated user. Raises 404 if user has no org."""
    result = await db_admin.table("organizations").select("id").eq("owner_id", user_id).maybe_single().execute()
    if not result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "ORG_NOT_FOUND", "message": "You do not have an organization"},
        )
    return result.data["id"]


async def _assert_search_ownership(db_admin: SupabaseAdmin, search_id: str, org_id: str) -> dict:
    """Returns the search row if it belongs to this org. Raises 404 otherwise.

    Security: prevents org A from reading/deleting org B's saved searches by
    checking both search_id AND org_id in the same query.
    """
    result = (
        await db_admin.table("org_saved_searches")
        .select("*")
        .eq("id", search_id)
        .eq("org_id", org_id)
        .maybe_single()
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "SEARCH_NOT_FOUND", "message": "Saved search not found"},
        )
    return result.data


@router.post(
    "/saved-searches",
    response_model=SavedSearchOut,
    status_code=201,
    summary="Save a talent search",
)
@limiter.limit(RATE_PROFILE_WRITE)
async def create_saved_search(
    request: Request,
    payload: SavedSearchCreate,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
) -> SavedSearchOut:
    """Save the current search filters under a name for later recall and match notifications.

    Security:
    - User must own an organization (org_id derived from JWT, never from body)
    - Cap: max 20 saved searches per org
    - Duplicate names rejected with 409
    """
    org_id = await _get_org_id_for_user(db_admin, user_id)

    # Enforce cap before insert
    count_res = await db_admin.table("org_saved_searches").select("id", count="exact").eq("org_id", org_id).execute()
    current_count = count_res.count or 0
    if current_count >= _MAX_SAVED_SEARCHES_PER_ORG:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "SAVED_SEARCH_LIMIT",
                "message": f"Maximum {_MAX_SAVED_SEARCHES_PER_ORG} saved searches per organization",
            },
        )

    insert_data = {
        "org_id": org_id,
        "name": payload.name,
        "filters": payload.filters.model_dump(exclude_none=True),
        "notify_on_match": payload.notify_on_match,
    }

    try:
        result = await db_admin.table("org_saved_searches").insert(insert_data).execute()
    except Exception as exc:
        err_str = str(exc)
        if "unique" in err_str.lower() or "duplicate" in err_str.lower():
            raise HTTPException(
                status_code=409,
                detail={"code": "DUPLICATE_NAME", "message": "A saved search with this name already exists"},
            )
        logger.error("Failed to create saved search", org_id=org_id, error=err_str)
        raise HTTPException(status_code=500, detail={"code": "CREATE_FAILED", "message": "Failed to save search"})

    if not result.data:
        raise HTTPException(status_code=500, detail={"code": "CREATE_FAILED", "message": "Failed to save search"})

    logger.info("Saved search created", org_id=org_id, name=payload.name)
    return SavedSearchOut(**result.data[0])


# list_saved_searches moved before /{org_id} — see list_saved_searches_early above.


@router.patch(
    "/saved-searches/{search_id}",
    response_model=SavedSearchOut,
    summary="Update a saved search",
)
@limiter.limit(RATE_PROFILE_WRITE)
async def update_saved_search(
    request: Request,
    search_id: str,
    payload: SavedSearchUpdate,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
) -> SavedSearchOut:
    """Update the name or notify_on_match setting for a saved search.

    Security: verifies the search belongs to the caller's org before updating.
    """
    # Validate UUID
    try:
        uuid.UUID(search_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={"code": "INVALID_ID", "message": "search_id must be a valid UUID"})

    org_id = await _get_org_id_for_user(db_admin, user_id)
    await _assert_search_ownership(db_admin, search_id, org_id)

    update_data = payload.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=422, detail={"code": "NO_FIELDS", "message": "No fields to update"})

    result = await db_admin.table("org_saved_searches").update(update_data).eq("id", search_id).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail={"code": "UPDATE_FAILED", "message": "Failed to update search"})
    return SavedSearchOut(**result.data[0])


@router.delete(
    "/saved-searches/{search_id}",
    status_code=204,
    summary="Delete a saved search",
)
@limiter.limit(RATE_PROFILE_WRITE)
async def delete_saved_search(
    request: Request,
    search_id: str,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
) -> None:
    """Delete a saved search. Ownership verified before delete.

    Security: double-check org ownership (search_id alone is not enough).
    Returns 204 No Content on success.
    """
    try:
        uuid.UUID(search_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={"code": "INVALID_ID", "message": "search_id must be a valid UUID"})

    org_id = await _get_org_id_for_user(db_admin, user_id)
    await _assert_search_ownership(db_admin, search_id, org_id)

    await db_admin.table("org_saved_searches").delete().eq("id", search_id).execute()
    logger.info("Saved search deleted", org_id=org_id, search_id=search_id)
