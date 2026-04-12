"""Public platform statistics endpoint.

No auth required — used for landing page social proof.
Queries are COUNT aggregates only — fast and safe on free-tier Supabase.
"""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Request
from loguru import logger
from pydantic import BaseModel, ConfigDict

from app.deps import CurrentUserId, SupabaseAdmin
from app.middleware.rate_limit import RATE_DEFAULT, limiter

router = APIRouter(prefix="/stats", tags=["Stats"])


class PublicStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_volunteers: int
    total_assessments: int
    total_events: int
    avg_aura_score: float


@router.get("/public", response_model=PublicStatsResponse)
@limiter.limit(RATE_DEFAULT)
async def get_public_stats(
    request: Request,
    db: SupabaseAdmin,
) -> PublicStatsResponse:
    """Get platform-wide public statistics.

    Returns volunteer count, completed assessments, active events, and average AURA score.
    All counts use exact=True for accurate results. Designed to remain fast on free-tier.
    """
    total_volunteers = 0
    total_assessments = 0
    total_events = 0
    avg_aura_score = 0.0

    # Count total volunteers (profiles table)
    try:
        result = (
            await db.table("profiles")
            .select("id", count="exact")
            .execute()
        )
        total_volunteers = result.count or 0
    except Exception as e:
        logger.warning("Failed to count volunteers: {err}", err=str(e)[:200])

    # Count completed assessments
    try:
        result = (
            await db.table("assessment_sessions")
            .select("id", count="exact")
            .eq("status", "completed")
            .execute()
        )
        total_assessments = result.count or 0
    except Exception as e:
        logger.warning("Failed to count assessments: {err}", err=str(e)[:200])

    # Count non-cancelled events
    try:
        result = (
            await db.table("events")
            .select("id", count="exact")
            .neq("status", "cancelled")
            .execute()
        )
        total_events = result.count or 0
    except Exception as e:
        logger.warning("Failed to count events: {err}", err=str(e)[:200])

    # Average AURA score — computed server-side via PostgreSQL AVG() RPC.
    # Old approach: fetch ALL rows into Python memory → O(n) bandwidth, wrong at scale.
    # New approach: avg_aura_score() returns a single float — O(1) bandwidth.
    try:
        result = await db.rpc("avg_aura_score").execute()
        if result.data is not None:
            avg_aura_score = round(float(result.data), 1)
    except Exception as e:
        logger.warning("Failed to compute avg AURA via RPC: {err}", err=str(e)[:200])

    return PublicStatsResponse(
        total_volunteers=total_volunteers,
        total_assessments=total_assessments,
        total_events=total_events,
        avg_aura_score=avg_aura_score,
    )


class BetaFunnelStats(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sessions_started: int
    sessions_completed: int
    sessions_abandoned: int   # in_progress AND updated_at < 24h ago (proxy metric)
    completion_rate: float    # completed / started (0.0–1.0)
    abandonment_rate: float   # abandoned / started
    registrations: int        # total profiles created
    aura_scores_generated: int


@router.get("/beta-funnel", response_model=BetaFunnelStats)
@limiter.limit("10/minute")
async def get_beta_funnel_stats(
    request: Request,
    db: SupabaseAdmin,
    user_id: CurrentUserId,
) -> BetaFunnelStats:
    """Beta funnel health metrics — for the failure protocol.

    SEC-Q3: Restricted to organization accounts only. Volunteers have no use for
    this data, and exposing completion/abandonment rates to all users leaks operational
    intelligence (platform health, abuse detection timing, user count signals).

    Abandonment proxy: sessions with status='in_progress' AND updated_at < 24h ago.
    This is not perfect (some users may still be in progress) but is a good signal.
    """
    # SEC-Q3: org-only guard — volunteers get 403
    caller_row = (
        await db.table("profiles")
        .select("account_type")
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )
    account_type = (caller_row.data or {}).get("account_type", "volunteer")
    if account_type == "volunteer":
        raise HTTPException(
            status_code=403,
            detail={"code": "FORBIDDEN", "message": "This endpoint is restricted to organization accounts"},
        )

    cutoff = (datetime.now(UTC) - timedelta(hours=24)).isoformat()

    started = completed = abandoned = registrations = aura_generated = 0

    try:
        r = await db.table("assessment_sessions").select("id", count="exact").execute()
        started = r.count or 0
    except Exception as e:
        logger.warning("beta_funnel: count started failed", error=str(e)[:100])

    try:
        r = await db.table("assessment_sessions").select("id", count="exact").eq("status", "completed").execute()
        completed = r.count or 0
    except Exception as e:
        logger.warning("beta_funnel: count completed failed", error=str(e)[:100])

    try:
        r = await (
            db.table("assessment_sessions")
            .select("id", count="exact")
            .eq("status", "in_progress")
            .lt("updated_at", cutoff)
            .execute()
        )
        abandoned = r.count or 0
    except Exception as e:
        logger.warning("beta_funnel: count abandoned failed", error=str(e)[:100])

    try:
        r = await db.table("profiles").select("id", count="exact").execute()
        registrations = r.count or 0
    except Exception as e:
        logger.warning("beta_funnel: count registrations failed", error=str(e)[:100])

    try:
        r = await db.table("aura_scores").select("volunteer_id", count="exact").execute()
        aura_generated = r.count or 0
    except Exception as e:
        logger.warning("beta_funnel: count aura_scores failed", error=str(e)[:100])

    completion_rate = round(completed / started, 3) if started > 0 else 0.0
    abandonment_rate = round(abandoned / started, 3) if started > 0 else 0.0

    return BetaFunnelStats(
        sessions_started=started,
        sessions_completed=completed,
        sessions_abandoned=abandoned,
        completion_rate=completion_rate,
        abandonment_rate=abandonment_rate,
        registrations=registrations,
        aura_scores_generated=aura_generated,
    )
