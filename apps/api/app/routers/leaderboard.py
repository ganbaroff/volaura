"""Leaderboard endpoint — top volunteers by AURA score.

Public endpoint (no auth required).
Rank > 10: display_name anonymized to protect volunteer privacy.
"""

from fastapi import APIRouter, HTTPException, Query, Request
from loguru import logger
from pydantic import BaseModel, ConfigDict

from app.deps import SupabaseAdmin
from app.middleware.rate_limit import limiter, RATE_DISCOVERY

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])


class LeaderboardEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rank: int
    display_name: str
    total_score: float
    badge_tier: str
    username: str | None
    is_current_user: bool = False  # Cannot determine without auth — always False


class LeaderboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    entries: list[LeaderboardEntry]
    period: str
    total_count: int


def _anonymize_name(display_name: str) -> str:
    """Anonymize display_name to 'First L.' format for rank > 10."""
    parts = display_name.strip().split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[1][0]}."
    # Single name — return as-is (no second word to abbreviate)
    return display_name


@router.get("", response_model=LeaderboardResponse)
@limiter.limit(RATE_DISCOVERY)
async def get_leaderboard(
    request: Request,
    db: SupabaseAdmin,
    period: str = Query(default="all_time", pattern="^(weekly|monthly|all_time)$"),
    limit: int = Query(default=50, ge=1, le=100),
) -> LeaderboardResponse:
    """Get top volunteers ranked by AURA score.

    Public endpoint — no auth required.
    Volunteers ranked > 10 have their display_name anonymized to protect privacy.
    """
    try:
        # Build query: aura_scores JOIN profiles
        query = (
            db.table("aura_scores")
            .select("volunteer_id, total_score, badge_tier, updated_at, profiles(display_name, username)")
            .eq("visibility", "public")
            .not_.is_("total_score", "null")
        )

        # Period filter on aura_scores.updated_at
        if period in ("weekly", "monthly"):
            from datetime import datetime, timedelta, timezone
            days = 7 if period == "weekly" else 30
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            query = query.gte("updated_at", cutoff)

        result = await (
            query
            .order("total_score", desc=True)
            .limit(limit)
            .execute()
        )

        entries: list[LeaderboardEntry] = []
        for rank, row in enumerate(result.data or [], start=1):
            profile = row.get("profiles") or {}
            raw_name = profile.get("display_name") or "Anonymous"
            username = profile.get("username")

            # Anonymize for rank > 10
            display_name = raw_name if rank <= 10 else _anonymize_name(raw_name)
            visible_username = username if rank <= 10 else None

            entries.append(LeaderboardEntry(
                rank=rank,
                display_name=display_name,
                total_score=float(row.get("total_score", 0)),
                badge_tier=row.get("badge_tier") or "none",
                username=visible_username,
                is_current_user=False,
            ))

        return LeaderboardResponse(
            entries=entries,
            period=period,
            total_count=len(entries),
        )

    except Exception:
        logger.exception("Leaderboard query failed")
        # Return empty list rather than 500 — public endpoint should degrade gracefully
        return LeaderboardResponse(entries=[], period=period, total_count=0)
