"""Tribe Streaks — Weekly Streak Tracker.

Runs every Sunday night via GitHub Actions cron (.github/workflows/tribe-matching.yml).
Uses SupabaseAdmin (service_role) exclusively.

Q2 decision (fading crystal model):
  - Any active week (≥1 assessment completed) → consecutive_misses_count = 0, streak++
  - Inactive week → consecutive_misses_count++
  - consecutive_misses_count >= 3 → streak resets to 0 (not suspended — reset)
"""

from __future__ import annotations

from datetime import UTC, datetime

from loguru import logger

# ── Public entry point ─────────────────────────────────────────────────────────


async def update_weekly_streaks(db) -> dict:
    """Update tribe streaks for the completed ISO week.

    Call on Sunday night (23:50 UTC) after the ISO week ends.
    Args:
        db: SupabaseAdmin client (service_role)
    Returns:
        Dict with streaks_extended, streaks_missed, streaks_reset, users_processed
    """
    now = datetime.now(UTC)
    # Get the just-completed ISO week (this week ends tonight)
    current_week = _iso_week(now)
    logger.info("Updating streaks for week {w}", w=current_week)

    # Get all users currently in active tribes
    active_members_result = await db.table("tribe_members").select("user_id").is_("opt_out_at", None).execute()
    active_user_ids = list({m["user_id"] for m in (active_members_result.data or [])})

    stats = {"streaks_extended": 0, "streaks_missed": 0, "streaks_reset": 0, "users_processed": 0}

    for user_id in active_user_ids:
        try:
            result = await _update_user_streak(db, user_id, current_week)
            stats["users_processed"] += 1
            stats[f"streaks_{result}"] += 1
        except Exception as e:
            logger.error("Failed to update streak for user {uid}: {e}", uid=user_id, e=str(e))

    logger.info("Streak update complete: {s}", s=stats)
    return stats


async def record_assessment_activity(db, user_id: str) -> None:
    """Mark a user as active for the current ISO week.

    Called from assessment complete endpoint — ensures streak credit happens
    immediately when assessment finishes, not just on Sunday cron.
    """
    now = datetime.now(UTC)
    current_week = _iso_week(now)

    try:
        streak_result = await db.table("tribe_streaks").select("*").eq("user_id", user_id).maybe_single().execute()
    except Exception:
        return  # table/view error or no row — user not in a tribe
    if not streak_result or not streak_result.data:
        return  # user not in a tribe — no streak to update

    existing = streak_result.data
    if existing.get("last_activity_week") == current_week:
        return  # already credited this week

    # Credit this week: extend streak, reset consecutive_misses
    new_streak = existing["current_streak"] + 1
    new_longest = max(new_streak, existing["longest_streak"])

    await (
        db.table("tribe_streaks")
        .update(
            {
                "current_streak": new_streak,
                "longest_streak": new_longest,
                "last_activity_week": current_week,
                "consecutive_misses_count": 0,
            }
        )
        .eq("user_id", user_id)
        .execute()
    )

    logger.info("Streak extended for user {uid}: {s} weeks", uid=user_id, s=new_streak)


# ── Internal helpers ───────────────────────────────────────────────────────────


async def _update_user_streak(db, user_id: str, current_week: str) -> str:
    """Update a single user's streak for the current week.

    Returns: "extended" | "missed" | "reset"
    """
    streak_result = await db.table("tribe_streaks").select("*").eq("user_id", user_id).maybe_single().execute()

    if not streak_result.data:
        # No streak row yet — create with 0s (will be populated at next tribe join)
        return "missed"

    existing = streak_result.data

    # Check if user was active this week (assessment completed)
    was_active = existing.get("last_activity_week") == current_week

    if was_active:
        # Already credited via record_assessment_activity — nothing more to do
        return "extended"

    # Inactive this week: increment consecutive_misses
    new_misses = existing["consecutive_misses_count"] + 1

    if new_misses >= 3:
        # Q2: 3 consecutive misses = streak resets to 0
        await (
            db.table("tribe_streaks")
            .update(
                {
                    "current_streak": 0,
                    "consecutive_misses_count": 0,
                    "last_activity_week": current_week,  # mark as processed
                }
            )
            .eq("user_id", user_id)
            .execute()
        )
        logger.info("Streak reset for user {uid} after 3 consecutive misses", uid=user_id)
        return "reset"
    else:
        # Crystal fades but streak survives
        await (
            db.table("tribe_streaks")
            .update(
                {
                    "consecutive_misses_count": new_misses,
                }
            )
            .eq("user_id", user_id)
            .execute()
        )
        return "missed"


def _iso_week(dt: datetime) -> str:
    """Return ISO week string in YYYY-Www format."""
    iso = dt.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"
