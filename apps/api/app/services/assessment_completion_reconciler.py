"""Assessment completion reconciler.

WHY THIS EXISTS:
  `POST /api/assessment/complete/{session_id}` now writes durable
  `assessment_completion_jobs` rows, but a partial failure can still leave
  downstream side effects unfinished until someone calls `/complete` again.

  This reconciler closes that gap. It scans incomplete completion jobs and
  re-runs only the missing side effects:
    - rewards
    - tribe streak
    - analytics
    - email
    - ecosystem events
    - aura events
    - automated decision log

  AURA RPC durability remains covered by `pending_aura_sync` +
  `app.services.aura_reconciler`. This worker complements that lane and marks
  the durable completion job itself finished once the remaining work lands.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from loguru import logger
from supabase._async.client import AsyncClient

from app.deps import get_admin_client
from app.routers.assessment import _log_assessment_automated_decision
from app.services.analytics import track_event
from app.services.assessment.completion_jobs import (
    all_side_effects_complete,
    is_side_effect_complete,
    mark_side_effect,
    normalize_side_effects,
    save_completion_job,
)
from app.services.assessment.rewards import emit_assessment_rewards
from app.services.ecosystem_events import (
    emit_assessment_completed,
    emit_aura_updated,
    emit_badge_tier_changed,
)
from app.services.email import send_aura_ready_email
from app.services.tribe_streak_tracker import record_assessment_activity

RECONCILE_BATCH_SIZE: int = int(os.environ.get("ASSESSMENT_COMPLETION_RECONCILE_BATCH_SIZE", "25"))
MAX_RECONCILE_ATTEMPTS: int = int(os.environ.get("ASSESSMENT_COMPLETION_RECONCILE_MAX_ATTEMPTS", "6"))


async def _admin() -> AsyncClient:
    return await get_admin_client()


async def _fetch_incomplete_jobs(db: AsyncClient, limit: int) -> list[dict[str, Any]]:
    result = (
        await db.table("assessment_completion_jobs")
        .select("*")
        .in_("status", ["pending", "processing", "partial"])
        .order("updated_at", desc=False)
        .limit(limit)
        .execute()
    )
    return result.data or []


async def _fetch_session(db: AsyncClient, session_id: str) -> dict[str, Any] | None:
    result = await db.table("assessment_sessions").select("*").eq("id", session_id).maybe_single().execute()
    return result.data or None


async def _fetch_aura_snapshot(db: AsyncClient, user_id: str) -> dict[str, Any] | None:
    result = (
        await db.table("aura_scores")
        .select("total_score, badge_tier, competency_scores, elite_status, percentile_rank")
        .eq("volunteer_id", user_id)
        .maybe_single()
        .execute()
    )
    data = result.data or {}
    if not data:
        return None
    comp_scores = data.get("competency_scores") or {}
    return {
        "total_score": float(data.get("total_score", 0)),
        "badge_tier": data.get("badge_tier", "bronze"),
        "competency_scores": {k: float(v) for k, v in comp_scores.items()},
        "elite_status": bool(data.get("elite_status", False)),
        "percentile_rank": float(data["percentile_rank"]) if data.get("percentile_rank") else None,
    }


async def _mark_terminal(
    db: AsyncClient,
    job: dict[str, Any],
    *,
    side_effects: dict[str, Any],
    result_context: dict[str, Any],
    last_error: str | None,
) -> dict[str, Any]:
    final_status = "completed" if all_side_effects_complete(side_effects) else "partial"
    return await save_completion_job(
        db,
        job,
        side_effects=side_effects,
        result_context=result_context,
        status=final_status,
        last_error=None if final_status == "completed" else last_error,
        completed_at=(job.get("completed_at") or result_context.get("completed_at")) if final_status == "completed" else job.get("completed_at"),
    )


async def _reconcile_job(db: AsyncClient, job: dict[str, Any]) -> str:
    session_id = job["session_id"]
    user_id = job["volunteer_id"]
    attempts = int(job.get("attempts") or 0)

    if attempts >= MAX_RECONCILE_ATTEMPTS:
        logger.error("completion_reconciler: max attempts exceeded", session_id=session_id, attempts=attempts)
        await save_completion_job(
            db,
            job,
            status="partial",
            last_error=f"max_attempts_exceeded:{attempts}",
        )
        return "gave_up"

    session = await _fetch_session(db, session_id)
    if not session or session.get("status") != "completed":
        logger.warning("completion_reconciler: session missing or not completed", session_id=session_id)
        await save_completion_job(
            db,
            job,
            status="partial",
            last_error="session_missing_or_not_completed",
        )
        return "retry"

    side_effects = normalize_side_effects(job.get("side_effects"))
    result_context = dict(job.get("result_context") or {})
    last_error: str | None = None
    slug = result_context.get("competency_slug") or job.get("competency_slug") or ""
    competency_score = float(result_context.get("competency_score") or 0)
    questions_answered = int(result_context.get("questions_answered") or len((session.get("answers") or {}).get("items", [])))
    stop_reason = result_context.get("stop_reason")
    gaming_flags = list(result_context.get("gaming_flags") or session.get("gaming_flags") or [])
    crystals_earned = int(result_context.get("crystals_earned") or 0)
    aura_updated = bool(result_context.get("aura_updated", False))
    energy_level = result_context.get("energy_level", "full")
    old_badge_tier = result_context.get("old_badge_tier")
    aura_snapshot = result_context.get("aura_snapshot")

    job = await save_completion_job(db, job, status="processing", increment_attempts=True, result_context=result_context)

    if not slug:
        side_effects = mark_side_effect(side_effects, "rewards", status="skipped", increment_attempts=False)
        side_effects = mark_side_effect(side_effects, "email", status="skipped", increment_attempts=False)
        side_effects = mark_side_effect(side_effects, "ecosystem_events", status="skipped", increment_attempts=False)
        side_effects = mark_side_effect(side_effects, "aura_events", status="skipped", increment_attempts=False)
        side_effects = mark_side_effect(side_effects, "decision_log", status="skipped", increment_attempts=False)

    if not is_side_effect_complete(side_effects, "rewards") and slug:
        try:
            crystals_earned = int(
                await emit_assessment_rewards(
                    db=db,
                    user_id=str(user_id),
                    skill_slug=slug,
                    competency_score=competency_score,
                    user_jwt=None,
                )
                or 0
            )
            result_context["crystals_earned"] = crystals_earned
            side_effects = mark_side_effect(side_effects, "rewards", status="done")
        except Exception as exc:
            last_error = str(exc)[:300]
            side_effects = mark_side_effect(side_effects, "rewards", status="failed", error=last_error)

    if not is_side_effect_complete(side_effects, "streak"):
        try:
            await record_assessment_activity(db=db, user_id=str(user_id))
            side_effects = mark_side_effect(side_effects, "streak", status="done")
        except Exception as exc:
            last_error = str(exc)[:300]
            side_effects = mark_side_effect(side_effects, "streak", status="failed", error=last_error)

    if not is_side_effect_complete(side_effects, "analytics"):
        try:
            await track_event(
                db=db,
                user_id=str(user_id),
                event_name="assessment_completed",
                session_id=session_id,
                properties={
                    "competency_slug": slug,
                    "competency_score": competency_score,
                    "questions_answered": questions_answered,
                    "stop_reason": stop_reason,
                    "aura_updated": aura_updated,
                    "crystals_earned": crystals_earned,
                    "gaming_flags": gaming_flags,
                },
            )
            side_effects = mark_side_effect(side_effects, "analytics", status="done")
        except Exception as exc:
            last_error = str(exc)[:300]
            side_effects = mark_side_effect(side_effects, "analytics", status="failed", error=last_error)

    if not is_side_effect_complete(side_effects, "email") and slug:
        try:
            user_resp = await db.auth.admin.get_user_by_id(str(user_id))
            user_email = user_resp.user.email if user_resp and user_resp.user else None
            if user_email:
                badge_resp = (
                    await db.table("aura_scores").select("badge_tier").eq("volunteer_id", str(user_id)).maybe_single().execute()
                )
                badge_tier = (badge_resp.data or {}).get("badge_tier", "bronze")
                prof_resp = await db.table("profiles").select("display_name").eq("id", str(user_id)).maybe_single().execute()
                display_name = (prof_resp.data or {}).get("display_name") or ""
                await send_aura_ready_email(
                    to_email=user_email,
                    display_name=display_name,
                    competency_slug=slug,
                    competency_score=competency_score,
                    badge_tier=badge_tier,
                    crystals_earned=crystals_earned,
                )
            side_effects = mark_side_effect(side_effects, "email", status="done")
        except Exception as exc:
            last_error = str(exc)[:300]
            side_effects = mark_side_effect(side_effects, "email", status="failed", error=last_error)

    if not is_side_effect_complete(side_effects, "ecosystem_events") and slug:
        try:
            await emit_assessment_completed(
                db=db,
                user_id=str(user_id),
                competency_slug=slug,
                competency_score=competency_score,
                items_answered=questions_answered,
                energy_level=energy_level,
                stop_reason=stop_reason,
                gaming_flags=gaming_flags,
            )
            side_effects = mark_side_effect(side_effects, "ecosystem_events", status="done")
        except Exception as exc:
            last_error = str(exc)[:300]
            side_effects = mark_side_effect(side_effects, "ecosystem_events", status="failed", error=last_error)

    if not is_side_effect_complete(side_effects, "aura_events"):
        if aura_updated and slug:
            try:
                aura_snapshot = aura_snapshot or await _fetch_aura_snapshot(db, str(user_id))
                result_context["aura_snapshot"] = aura_snapshot
                if aura_snapshot:
                    await emit_aura_updated(
                        db=db,
                        user_id=str(user_id),
                        total_score=float(aura_snapshot["total_score"]),
                        badge_tier=str(aura_snapshot["badge_tier"]),
                        competency_scores=dict(aura_snapshot["competency_scores"]),
                        elite_status=bool(aura_snapshot["elite_status"]),
                        percentile_rank=aura_snapshot.get("percentile_rank"),
                    )
                    await emit_badge_tier_changed(
                        db=db,
                        user_id=str(user_id),
                        old_tier=old_badge_tier,
                        new_tier=str(aura_snapshot["badge_tier"]),
                        total_score=float(aura_snapshot["total_score"]),
                    )
                side_effects = mark_side_effect(side_effects, "aura_events", status="done")
            except Exception as exc:
                last_error = str(exc)[:300]
                side_effects = mark_side_effect(side_effects, "aura_events", status="failed", error=last_error)
        else:
            side_effects = mark_side_effect(side_effects, "aura_events", status="skipped", increment_attempts=False)

    if not is_side_effect_complete(side_effects, "decision_log"):
        if slug:
            logged = await _log_assessment_automated_decision(
                db,
                user_id=str(user_id),
                session_id=session_id,
                competency_slug=slug,
                competency_score=competency_score,
                questions_answered=questions_answered,
                stop_reason=stop_reason,
                aura_updated=aura_updated,
                gaming_flags=gaming_flags,
                crystals_earned=crystals_earned,
                aura_snapshot=aura_snapshot,
            )
            if logged:
                side_effects = mark_side_effect(side_effects, "decision_log", status="done")
            else:
                last_error = "automated_decision_log insert failed"
                side_effects = mark_side_effect(side_effects, "decision_log", status="failed", error=last_error)
        else:
            side_effects = mark_side_effect(side_effects, "decision_log", status="skipped", increment_attempts=False)

    job = await _mark_terminal(
        db,
        job,
        side_effects=side_effects,
        result_context=result_context,
        last_error=last_error,
    )

    if job.get("status") == "completed":
        logger.info("completion_reconciler: job completed", session_id=session_id, user_id=str(user_id))
        return "ok"

    logger.warning("completion_reconciler: job still partial", session_id=session_id, user_id=str(user_id))
    return "retry"


async def run_once() -> dict[str, int]:
    db = await _admin()
    jobs = await _fetch_incomplete_jobs(db, RECONCILE_BATCH_SIZE)
    stats = {"found": len(jobs), "ok": 0, "retry": 0, "gave_up": 0}
    for job in jobs:
        outcome = await _reconcile_job(db, job)
        stats[outcome] = stats.get(outcome, 0) + 1
        await asyncio.sleep(0.1)
    logger.info("assessment_completion_reconciler cycle complete", **stats)
    return stats


async def _main() -> None:
    stats = await run_once()
    logger.info("assessment_completion_reconciler CLI complete", **stats)


if __name__ == "__main__":
    asyncio.run(_main())
