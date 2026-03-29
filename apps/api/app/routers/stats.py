"""Public platform statistics endpoint.

No auth required — used for landing page social proof.
Queries are COUNT aggregates only — fast and safe on free-tier Supabase.
"""

from fastapi import APIRouter, Request
from loguru import logger
from pydantic import BaseModel, ConfigDict

from app.deps import SupabaseAdmin
from app.middleware.rate_limit import limiter, RATE_DEFAULT

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
            avg_aura_score = float(result.data) if result.data is not None else 0.0
    except Exception as e:
        logger.warning("Failed to compute avg AURA via RPC: {err}", err=str(e)[:200])

    return PublicStatsResponse(
        total_volunteers=total_volunteers,
        total_assessments=total_assessments,
        total_events=total_events,
        avg_aura_score=avg_aura_score,
    )
