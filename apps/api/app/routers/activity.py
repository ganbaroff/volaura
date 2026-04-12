"""Activity feed endpoint — aggregates from multiple tables.

No dedicated activity table needed. We query:
- assessment_sessions (completed assessments)
- badges (earned badges)
- volunteer_behavior_signals (reliability events)
- event_registrations (event participation)

Returns a unified, time-sorted feed of recent activity.
"""

from datetime import UTC

from fastapi import APIRouter, Query, Request
from loguru import logger

from app.deps import CurrentUserId, SupabaseUser
from app.middleware.rate_limit import RATE_DEFAULT, limiter

router = APIRouter(prefix="/activity", tags=["Activity"])


@router.get("/me")
@limiter.limit(RATE_DEFAULT)
async def get_my_activity(
    request: Request,
    db: SupabaseUser,
    user_id: CurrentUserId,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict:
    """Get activity feed for the current user.

    Aggregates from assessment_sessions, badges, behavior_signals,
    and event_registrations into a unified timeline.
    """
    items = []

    # 1. Completed assessments
    try:
        assessments = (
            await db.table("assessment_sessions")
            .select("id, competency_id, theta_estimate, status, completed_at")
            .eq("volunteer_id", user_id)
            .eq("status", "completed")
            .order("completed_at", desc=True)
            .limit(limit)
            .execute()
        )
        for row in assessments.data or []:
            items.append({
                "id": row["id"],
                "type": "assessment",
                "description": "Completed competency assessment",
                "created_at": row["completed_at"],
                "metadata": {
                    "competency_id": row["competency_id"],
                    "theta_estimate": row.get("theta_estimate"),
                },
            })
    except Exception as e:
        logger.warning("Failed to fetch assessment activity: {err}", err=str(e)[:200])

    # 2. Earned badges — volunteer_badges is the earned-badges table;
    #    badges is the catalog (no volunteer_id / tier columns on it).
    try:
        badges = (
            await db.table("volunteer_badges")
            .select("id, badge_id, earned_at, metadata, badges(badge_type, name_en)")
            .eq("volunteer_id", user_id)
            .order("earned_at", desc=True)
            .limit(limit)
            .execute()
        )
        for row in badges.data or []:
            badge_def = row.get("badges") or {}
            badge_type = badge_def.get("badge_type") or "achievement"
            items.append({
                "id": row["id"],
                "type": "badge",
                "description": f"Earned {badge_type} badge",
                "created_at": row["earned_at"],
                "metadata": {
                    "badge_type": badge_type,
                    "badge_id": row["badge_id"],
                },
            })
    except Exception as e:
        logger.warning("Failed to fetch badge activity: {err}", err=str(e)[:200])

    # 3. Event registrations
    try:
        registrations = (
            await db.table("registrations")
            .select("id, event_id, status, registered_at")
            .eq("volunteer_id", user_id)
            .order("registered_at", desc=True)
            .limit(limit)
            .execute()
        )
        for row in registrations.data or []:
            items.append({
                "id": row["id"],
                "type": "event",
                "description": "Registered for event",
                "created_at": row["registered_at"],
                "metadata": {
                    "event_id": row["event_id"],
                    "status": row["status"],
                },
            })
    except Exception as e:
        logger.warning("Failed to fetch event activity: {err}", err=str(e)[:200])

    # 4. Behavior signals (reliability events)
    try:
        signals = (
            await db.table("volunteer_behavior_signals")
            .select("id, signal_type, signal_value, measured_at, source")
            .eq("volunteer_id", user_id)
            .order("measured_at", desc=True)
            .limit(limit)
            .execute()
        )
        for row in signals.data or []:
            items.append({
                "id": row["id"],
                "type": "verification",
                "description": f"Behavior signal: {row['signal_type']}",
                "created_at": row["measured_at"],
                "metadata": {
                    "signal_type": row["signal_type"],
                    "signal_value": row["signal_value"],
                    "source": row["source"],
                },
            })
    except Exception as e:
        logger.warning("Failed to fetch behavior signal activity: {err}", err=str(e)[:200])

    # Sort all items by created_at descending, apply pagination
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    paginated = items[offset:offset + limit]

    return {
        "data": paginated,
        "meta": {
            "total": len(items),
            "limit": limit,
            "offset": offset,
        },
    }


@router.get("/stats/me")
@limiter.limit(RATE_DEFAULT)
async def get_my_stats(
    request: Request,
    db: SupabaseUser,
    user_id: CurrentUserId,
) -> dict:
    """Get dashboard stats for the current user.

    Returns: events_attended, total_hours (estimated), verified_skills, streak_days.
    """
    events_attended = 0
    verified_skills = 0
    streak_days = 0

    # Count events attended: approved registration + coordinator confirmed check-in.
    # Valid statuses: pending|approved|rejected|waitlisted|cancelled (schema constraint).
    # checked_in_at IS NOT NULL means coordinator physically verified attendance.
    try:
        result = (
            await db.table("registrations")
            .select("id", count="exact")
            .eq("volunteer_id", user_id)
            .eq("status", "approved")
            .not_.is_("checked_in_at", "null")
            .execute()
        )
        events_attended = result.count or 0
    except Exception as e:
        logger.warning("Failed to count events: {err}", err=str(e)[:200])

    # Count verified skills (completed assessment sessions)
    try:
        result = (
            await db.table("assessment_sessions")
            .select("competency_id")
            .eq("volunteer_id", user_id)
            .eq("status", "completed")
            .execute()
        )
        unique_competencies = {row["competency_id"] for row in (result.data or [])}
        verified_skills = len(unique_competencies)
    except Exception as e:
        logger.warning("Failed to count skills: {err}", err=str(e)[:200])

    # Calculate streak (consecutive days with any activity)
    # Simplified: count badges + assessments in last 7 days as proxy
    try:
        from datetime import datetime, timedelta
        seven_days_ago = (datetime.now(UTC) - timedelta(days=7)).isoformat()
        result = (
            await db.table("assessment_sessions")
            .select("completed_at")
            .eq("volunteer_id", user_id)
            .eq("status", "completed")
            .gte("completed_at", seven_days_ago)
            .execute()
        )
        active_days = {row["completed_at"][:10] for row in (result.data or []) if row.get("completed_at")}
        streak_days = len(active_days)
    except Exception as e:
        logger.warning("Failed to calculate streak: {err}", err=str(e)[:200])

    return {
        "data": {
            "events_attended": events_attended,
            "total_hours": events_attended * 4,  # estimate 4h per event avg
            "verified_skills": verified_skills,
            "streak_days": streak_days,
        },
    }
