"""Community Signal endpoint — anonymous aggregate social proof (G44).

Constitution G44: "Show N professionals took this assessment today" without
leaderboard framing. Constitution Crystal Law 5 (2026-04-14): no competitive
ranking, no per-user reveal. Just three counts the visitor can take or leave.

Public endpoint. No auth. Rate-limited to prevent enumeration abuse (RATE_DISCOVERY).
Returns aggregate only — zero IDs, zero usernames, zero timing clues per user.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict

from app.deps import SupabaseAdmin
from app.middleware.rate_limit import RATE_DISCOVERY, limiter

router = APIRouter(prefix="/community", tags=["Community"])


class CommunitySignal(BaseModel):
    """Aggregate-only social proof counters."""

    model_config = ConfigDict(from_attributes=True)

    professionals_today: int
    professionals_this_week: int
    total_professionals: int


@router.get("/signal", response_model=CommunitySignal)
@limiter.limit(RATE_DISCOVERY)
async def get_community_signal(
    request: Request,
    db: SupabaseAdmin,
) -> CommunitySignal:
    """Return three aggregate counts for landing / widget display.

    Buckets count distinct professionals with at least one COMPLETED assessment
    in the window. A single user who completed 3 competencies today still counts
    as 1 in "today" (we use the user id as the aggregation key, not session count
    — avoids making it look busier than reality).
    """
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    week_start = (now - timedelta(days=7)).isoformat()

    # Supabase SDK does not expose COUNT DISTINCT directly — fetch minimal
    # projection then dedupe in Python. Sessions table is modest scale at
    # launch; acceptable until traffic makes an RPC worthwhile.
    today_res = (
        await db.table("assessment_sessions")
        .select("volunteer_id")
        .eq("status", "completed")
        .gte("completed_at", today_start)
        .execute()
    )
    week_res = (
        await db.table("assessment_sessions")
        .select("volunteer_id")
        .eq("status", "completed")
        .gte("completed_at", week_start)
        .execute()
    )
    total_res = await db.table("aura_scores").select("volunteer_id", count="exact", head=True).execute()

    def _unique_count(rows: list[dict] | None) -> int:
        return len({r.get("volunteer_id") for r in (rows or []) if r.get("volunteer_id")})

    return CommunitySignal(
        professionals_today=_unique_count(today_res.data),
        professionals_this_week=_unique_count(week_res.data),
        total_professionals=total_res.count or 0,
    )
