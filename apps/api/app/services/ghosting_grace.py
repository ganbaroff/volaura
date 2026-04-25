"""Ghosting Grace worker — Constitution VOLAURA Rule 30.

After signup, if a user has not completed any assessment within 48 hours,
send ONE warm re-entry email and mark the user so we never nudge twice.

Design:
 • Worker is idempotent — running it 100 times in a row is the same as running
   it once for any given user (column flips on first successful send).
 • Worker is silent under kill switch (email_enabled=False) — counts candidates
   but does not call Resend, does not flip the column. This means flipping the
   kill switch later does not lose the queue.
 • Worker batches at most BATCH_SIZE per call to keep cron cheap.
 • Caller decides scheduling — pg_cron, GitHub Actions, or manual trigger.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from loguru import logger

from app.config import settings
from app.services.email import send_ghosting_grace_email

GRACE_WINDOW_HOURS = 48
BATCH_SIZE = 50


async def _fetch_candidates(db: Any) -> list[dict]:
    """Return profiles eligible for the warm re-entry nudge.

    Eligibility:
      created_at  ≤ now - 48h
      ghosting_grace_sent_at IS NULL
      AND no completed assessment_session for this user
    """
    cutoff = (datetime.now(UTC) - timedelta(hours=GRACE_WINDOW_HOURS)).isoformat()

    profiles = await (
        db.table("profiles")
        .select("id, display_name, username")
        .lt("created_at", cutoff)
        .is_("ghosting_grace_sent_at", "null")
        .limit(BATCH_SIZE * 2)  # over-fetch — some will be filtered for completed assessments
        .execute()
    )
    rows = profiles.data or []
    if not rows:
        return []

    user_ids = [r["id"] for r in rows]

    completed = await (
        db.table("assessment_sessions")
        .select("volunteer_id")
        .in_("volunteer_id", user_ids)
        .eq("status", "completed")
        .execute()
    )
    completed_ids = {r["volunteer_id"] for r in (completed.data or [])}

    eligible = [r for r in rows if r["id"] not in completed_ids][:BATCH_SIZE]
    return eligible


async def _fetch_email(db: Any, user_id: str) -> str | None:
    """auth.users email is not in PostgREST without a view — use admin API instead."""
    try:
        result = await db.auth.admin.get_user_by_id(user_id)
        user = getattr(result, "user", None) or result
        return getattr(user, "email", None)
    except Exception as exc:
        logger.warning("ghosting_grace fetch_email failed", user_id=user_id, error=str(exc)[:150])
        return None


async def process_ghosting_grace(db: Any) -> dict:
    """Run one batch of the ghosting-grace worker.

    Returns a summary dict for the caller to log / return as JSON:
      {
        "candidates": int,        # eligible profiles found
        "sent": int,              # emails Resend accepted
        "skipped_kill_switch": int,
        "marked": int,            # profiles whose ghosting_grace_sent_at was set
        "errors": int,            # failed sends or DB errors
      }
    """
    summary = {"candidates": 0, "sent": 0, "skipped_kill_switch": 0, "marked": 0, "errors": 0}

    candidates = await _fetch_candidates(db)
    summary["candidates"] = len(candidates)
    if not candidates:
        return summary

    # Short-circuit on kill switch — count but don't flip the column so the
    # queue is preserved for when CEO turns email_enabled on.
    if not settings.email_enabled or not settings.resend_api_key:
        summary["skipped_kill_switch"] = len(candidates)
        logger.info(
            "ghosting_grace dry run — kill switch off",
            candidates=len(candidates),
            email_enabled=settings.email_enabled,
            has_resend_key=bool(settings.resend_api_key),
        )
        return summary

    now = datetime.now(UTC).isoformat()
    for row in candidates:
        user_id = row["id"]
        email = await _fetch_email(db, user_id)
        if not email:
            summary["errors"] += 1
            continue

        ok = await send_ghosting_grace_email(
            to_email=email,
            display_name=row.get("display_name") or row.get("username") or "",
            locale="en",
        )
        if not ok:
            summary["errors"] += 1
            continue

        summary["sent"] += 1
        try:
            await db.table("profiles").update({"ghosting_grace_sent_at": now}).eq("id", user_id).execute()
            summary["marked"] += 1
        except Exception as exc:
            logger.warning(
                "ghosting_grace mark failed — email sent but column not flipped",
                user_id=user_id,
                error=str(exc)[:200],
            )
            summary["errors"] += 1

    logger.info("ghosting_grace batch complete", **summary)
    return summary
