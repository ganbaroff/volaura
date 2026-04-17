"""AURA sync reconciler — closes ghost-audit P0-2.

WHY THIS EXISTS:
  When a user finishes an assessment, `complete_assessment` sets
  pending_aura_sync=TRUE *before* calling upsert_aura_score RPC (intent-
  before-action). On RPC success the flag is cleared. If anything fails —
  RPC error, network blip, Supabase cold start, or the process crashing
  mid-way — the flag stays TRUE and the session looks like a ghost:
  status='completed' but no AURA row, no badge tier change, no
  character_events emitted to the ecosystem.

  This reconciler runs on a cron (every 10 minutes) and re-runs the RPC
  for every such session until it succeeds. Idempotent: upsert_aura_score
  is safe to call repeatedly with the same (volunteer_id, competency_slug).

DESIGN:
  - Bounded batch per cycle (RECONCILE_BATCH_SIZE).
  - Bounded retry per session (MAX_RECONCILE_ATTEMPTS) — after the cap,
    the session's pending flag is cleared and a CRITICAL log is emitted
    so CTO/ops can investigate. Leaving the flag TRUE forever would fill
    the retry index and mask fresh failures.
  - Success criterion: RPC returns data. On success we clear the flag.
  - Never touches session answers, never recomputes competency_score —
    that was already persisted when the user completed. We only resync
    the AURA aggregate.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from loguru import logger
from supabase._async.client import AsyncClient
from supabase._async.client import create_client as acreate_client

# ── Tuning constants ──────────────────────────────────────────────────────────

RECONCILE_BATCH_SIZE: int = int(os.environ.get("AURA_RECONCILE_BATCH_SIZE", "50"))
MAX_RECONCILE_ATTEMPTS: int = int(os.environ.get("AURA_RECONCILE_MAX_ATTEMPTS", "5"))
RPC_RETRY_SLEEP_S: float = 1.5


async def _admin() -> AsyncClient:
    from app.config import settings

    return await acreate_client(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_service_key,
    )


async def _fetch_pending(db: AsyncClient, limit: int) -> list[dict[str, Any]]:
    """Return sessions needing AURA resync.

    Joined with competencies to get slug directly — avoids a second round-trip
    per session when the batch is large.
    """
    result = (
        await db.table("assessment_sessions")
        .select("id,volunteer_id,competency_id,competency_score,reconcile_attempts")
        .eq("pending_aura_sync", True)
        .eq("status", "completed")
        .order("completed_at", desc=False)
        .limit(limit)
        .execute()
    )
    return result.data or []


async def _get_slug(db: AsyncClient, competency_id: str) -> str | None:
    try:
        r = await db.table("competencies").select("slug").eq("id", competency_id).single().execute()
        return (r.data or {}).get("slug")
    except Exception as e:
        logger.error("reconcile: failed to load competency slug", competency_id=competency_id, error=str(e)[:200])
        return None


async def _reconcile_session(db: AsyncClient, row: dict[str, Any]) -> str:
    """Return 'ok' | 'retry' | 'gave_up'."""
    session_id: str = row["id"]
    user_id: str = row["volunteer_id"]
    competency_id: str = row["competency_id"]
    competency_score: float | None = row.get("competency_score")
    attempts: int = int(row.get("reconcile_attempts") or 0)

    if competency_score is None:
        logger.error(
            "reconcile: session has NULL competency_score — cannot resync AURA",
            session_id=session_id,
            user_id=user_id,
        )
        # Mark gave_up to stop pounding on a session that cannot recover here.
        await _mark_gave_up(db, session_id, "null_competency_score")
        return "gave_up"

    slug = await _get_slug(db, competency_id)
    if not slug:
        await _mark_gave_up(db, session_id, "no_slug")
        return "gave_up"

    rpc_params = {"p_volunteer_id": user_id, "p_competency_scores": {slug: competency_score}}
    try:
        rpc_result = await db.rpc("upsert_aura_score", rpc_params).execute()
        if rpc_result.data is None:
            raise RuntimeError("upsert_aura_score returned no data")
        # Success — clear flag, reset counter.
        await (
            db.table("assessment_sessions")
            .update({"pending_aura_sync": False, "reconcile_attempts": 0})
            .eq("id", session_id)
            .execute()
        )
        logger.info(
            "reconcile: AURA resynced",
            session_id=session_id,
            user_id=user_id,
            slug=slug,
            prior_attempts=attempts,
        )
        return "ok"
    except Exception as e:
        new_attempts = attempts + 1
        if new_attempts >= MAX_RECONCILE_ATTEMPTS:
            await _mark_gave_up(db, session_id, f"max_attempts:{e!s}"[:200])
            logger.error(
                "reconcile: gave up after max attempts",
                session_id=session_id,
                user_id=user_id,
                slug=slug,
                attempts=new_attempts,
                error=str(e)[:300],
            )
            return "gave_up"
        try:
            await (
                db.table("assessment_sessions")
                .update({"reconcile_attempts": new_attempts})
                .eq("id", session_id)
                .execute()
            )
        except Exception:
            pass  # don't let counter update failure block the main flow
        logger.warning(
            "reconcile: RPC failed, will retry next cycle",
            session_id=session_id,
            slug=slug,
            attempts=new_attempts,
            error=str(e)[:300],
        )
        return "retry"


async def _mark_gave_up(db: AsyncClient, session_id: str, reason: str) -> None:
    """Clear the flag so the session stops being picked up. A CRITICAL log is
    emitted upstream; the session's state is preserved (competency_score
    still there). Manual CTO inspection is expected."""
    try:
        await db.table("assessment_sessions").update({"pending_aura_sync": False}).eq("id", session_id).execute()
    except Exception as e:
        logger.error(
            "reconcile: failed to clear flag on gave-up session",
            session_id=session_id,
            reason=reason,
            error=str(e)[:200],
        )


async def run_once() -> dict[str, int]:
    """One reconciliation cycle. Returns counts for ops visibility."""
    db = await _admin()
    pending = await _fetch_pending(db, RECONCILE_BATCH_SIZE)
    stats = {"found": len(pending), "ok": 0, "retry": 0, "gave_up": 0}
    for row in pending:
        outcome = await _reconcile_session(db, row)
        stats[outcome] = stats.get(outcome, 0) + 1
        # Small breather — Supabase free tier rate-friendly, doesn't matter at batch 50.
        await asyncio.sleep(0.1)
    logger.info("aura_reconciler cycle complete", **stats)
    return stats


async def _main() -> None:
    """CLI entry used by the GitHub Actions cron."""
    stats = await run_once()
    logger.info("aura_reconciler CLI complete", **stats)


if __name__ == "__main__":
    asyncio.run(_main())
