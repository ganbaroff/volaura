"""Volunteer discovery endpoint — Phase 3 org talent search.

Security hardening (post agent review 2026-03-25):
- Cursor-based pagination (not offset) → prevents volunteer enumeration attack
- Rate limit: 10/minute (RATE_DISCOVERY, not RATE_DEFAULT=60)
- display_name: server-side anonymized ("First L.") — never trust user-controlled field
- Returns only queried competency score, not full competency_scores JSONB
- competency slug validated against known slugs (422 if invalid slug)
- RLS via SupabaseUser: only visibility='public' scores returned
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.deps import CurrentUserId, SupabaseAdmin, SupabaseUser
from app.middleware.rate_limit import limiter, RATE_DISCOVERY
from app.schemas.discovery import (
    COMPETENCY_SLUGS,
    DiscoveryMeta,
    DiscoveryRequest,
    DiscoveryResponse,
    DiscoveryVolunteer,
)

router = APIRouter(prefix="/volunteers", tags=["Discovery"])


# ── Helpers ────────────────────────────────────────────────────────────────────


def _anonymize_name(display_name: str | None) -> str:
    """Server-side name anonymization — never trust user-controlled display_name.

    Result: "Leyla A." (first name + last initial)
    Security: prevents re-identification via full name in public search results.
    """
    if not display_name or not display_name.strip():
        return "Volunteer"
    parts = display_name.strip().split()
    first = parts[0][:20]  # cap first name at 20 chars
    if len(parts) == 1:
        return first
    last_initial = parts[-1][0].upper()
    return f"{first} {last_initial}."


# ── Endpoint ───────────────────────────────────────────────────────────────────


@router.get("/discovery", response_model=DiscoveryResponse)
@limiter.limit(RATE_DISCOVERY)
async def discover_volunteers(
    request: Request,
    db: SupabaseUser,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
    # Query params — not using Depends(DiscoveryRequest) because FastAPI
    # handles Pydantic models as body, not query. Using explicit Query params.
    competency: str | None = Query(default=None),
    score_min: float = Query(default=0.0, ge=0.0, le=100.0),
    role_level: str | None = Query(default=None),
    badge_tier: str | None = Query(default=None),
    sort_by: str = Query(default="score", pattern="^(score|events|recent)$"),
    after_score: float | None = Query(default=None, ge=0.0, le=100.0),
    after_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
) -> DiscoveryResponse:
    """Search public volunteer profiles by competency, score, role, and badge.

    Returns cursor-paginated results. Use `next_after_score` + `next_after_id`
    from meta to get the next page.

    **Contact volunteers:** Use the returned `volunteer_id` with
    `POST /api/organizations/{org_id}/assign-assessments`.
    """
    # Validate competency slug (422 if invalid — agent recommendation)
    if competency is not None and competency not in COMPETENCY_SLUGS:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "INVALID_COMPETENCY",
                "message": f"Invalid competency slug '{competency}'. Valid: {sorted(COMPETENCY_SLUGS)}",
            },
        )

    # Validate role_level
    valid_roles = {"volunteer", "coordinator", "specialist", "manager", "senior_manager"}
    if role_level is not None and role_level not in valid_roles:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_ROLE_LEVEL", "message": f"Invalid role_level. Valid: {sorted(valid_roles)}"},
        )

    # Validate badge_tier
    valid_badges = {"Bronze", "Silver", "Gold", "Platinum"}
    if badge_tier is not None and badge_tier not in valid_badges:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_BADGE_TIER", "message": f"Invalid badge_tier. Valid: {sorted(valid_badges)}"},
        )

    # ── Step 1: Get visible aura_scores (RLS enforces visibility='public') ────
    # SupabaseUser client: RLS policy allows visibility='public' OR own record.
    # Unauthenticated callers blocked at FastAPI auth layer (CurrentUserId).

    aura_query = (
        db.table("aura_scores")
        .select("volunteer_id,total_score,badge_tier,competency_scores,events_attended,events_no_show,last_updated")
        .eq("visibility", "public")
    )

    # badge_tier filter
    if badge_tier:
        aura_query = aura_query.eq("badge_tier", badge_tier)

    # Cursor-based pagination — prevents enumeration attack.
    # Cursor: (total_score DESC, volunteer_id ASC) — stable keyset.
    # For sort_by=score: cursor on (total_score, volunteer_id).
    # For sort_by=events: cursor on (events_attended, volunteer_id) — TODO v2.
    # For sort_by=recent: cursor on (last_updated, volunteer_id) — TODO v2.
    # v1: cursor only implemented for sort_by=score.
    if sort_by == "score":
        aura_query = aura_query.order("total_score", desc=True).order("volunteer_id", desc=False)
        if after_score is not None and after_id is not None:
            # Keyset: WHERE (total_score < after_score) OR (total_score = after_score AND volunteer_id > after_id)
            # Supabase SDK doesn't support complex OR in single call — fetch with total_score <= after_score
            # and filter in Python. Small page sizes make this efficient.
            aura_query = aura_query.lte("total_score", after_score)
    elif sort_by == "events":
        aura_query = aura_query.order("events_attended", desc=True).order("volunteer_id", desc=False)
    else:  # recent
        aura_query = aura_query.order("last_updated", desc=True).order("volunteer_id", desc=False)

    # Fetch limit+1 to detect has_more
    aura_query = aura_query.limit(limit + 1)

    aura_result = await aura_query.execute()
    aura_rows = aura_result.data or []

    # ── Step 2: Filter by competency score (in Python — JSONB cast safety) ───
    # Architecture agent: test JSONB syntax. Safest approach: fetch rows,
    # filter competency score in Python. Avoids cast errors at DB level.
    if competency and score_min > 0.0:
        aura_rows = [
            row for row in aura_rows
            if float((row.get("competency_scores") or {}).get(competency, 0.0)) >= score_min
        ]

    # ── Step 3: Filter by role_level (via assessment_sessions) ───────────────
    # role_level filtering: volunteers who have ANY completed assessment at this role.
    if role_level:
        # Get set of volunteer_ids that have completed at least one session at this role_level
        role_result = await (
            db_admin.table("assessment_sessions")
            .select("volunteer_id")
            .eq("role_level", role_level)
            .eq("status", "completed")
            .execute()
        )
        eligible_ids = {row["volunteer_id"] for row in (role_result.data or [])}
        aura_rows = [row for row in aura_rows if row["volunteer_id"] in eligible_ids]

    # ── Step 4: Cursor tiebreaker for sort_by=score ───────────────────────────
    if sort_by == "score" and after_score is not None and after_id is not None:
        # Remove items where (score == after_score AND volunteer_id <= after_id)
        # This handles the exact-score tiebreaker correctly
        aura_rows = [
            row for row in aura_rows
            if not (row["total_score"] == after_score and row["volunteer_id"] <= after_id)
        ]

    # ── Step 5: Detect has_more, trim to limit ────────────────────────────────
    has_more = len(aura_rows) > limit
    aura_rows = aura_rows[:limit]

    # ── Step 6: Get display_names from profiles (batch lookup) ───────────────
    volunteer_ids = [row["volunteer_id"] for row in aura_rows]
    profile_map: dict[str, str | None] = {}

    if volunteer_ids:
        profiles_result = await (
            db_admin.table("profiles")
            .select("id,display_name")
            .in_("id", volunteer_ids)
            .execute()
        )
        for p in (profiles_result.data or []):
            profile_map[p["id"]] = p.get("display_name")

    # ── Step 7: Get role_levels for result set (most recent session per volunteer) ──
    role_map: dict[str, str | None] = {}
    if volunteer_ids:
        sessions_result = await (
            db_admin.table("assessment_sessions")
            .select("volunteer_id,role_level,completed_at")
            .in_("volunteer_id", volunteer_ids)
            .eq("status", "completed")
            .order("completed_at", desc=True)
            .execute()
        )
        # Take most recent role_level per volunteer
        for s in (sessions_result.data or []):
            vid = s["volunteer_id"]
            if vid not in role_map:  # first = most recent (ordered desc)
                role_map[vid] = s.get("role_level")

    # ── Step 8: Build response ────────────────────────────────────────────────
    results: list[DiscoveryVolunteer] = []
    for row in aura_rows:
        vid = row["volunteer_id"]
        raw_name = profile_map.get(vid)
        comp_scores = row.get("competency_scores") or {}
        c_score = float(comp_scores.get(competency, 0.0)) if competency else None

        results.append(DiscoveryVolunteer(
            volunteer_id=vid,
            display_name=_anonymize_name(raw_name),
            badge_tier=row.get("badge_tier", "None"),
            total_score=round(float(row.get("total_score", 0.0)), 1),
            competency_score=round(c_score, 3) if c_score is not None else None,
            role_level=role_map.get(vid),
            events_attended=int(row.get("events_attended", 0)),
            events_no_show=int(row.get("events_no_show", 0)),
            last_updated=row.get("last_updated"),
        ))

    # Build next-page cursor from last item
    next_after_score: float | None = None
    next_after_id: str | None = None
    if has_more and results:
        last = results[-1]
        if sort_by == "score":
            next_after_score = last.total_score
            next_after_id = last.volunteer_id

    return DiscoveryResponse(
        data=results,
        meta=DiscoveryMeta(
            returned=len(results),
            limit=limit,
            has_more=has_more,
            next_after_score=next_after_score,
            next_after_id=next_after_id,
        ),
    )
