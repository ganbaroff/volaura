"""Async re-evaluation worker for keyword_fallback answers.

WHY THIS EXISTS:
  keyword_fallback produces vocabulary scores (buzzword matching), not
  competency scores. ADR-010 flags these as evaluation_mode="degraded".
  This worker runs as a background asyncio task inside the FastAPI process,
  picks up degraded answers from the evaluation_queue table, re-evaluates
  them via Gemini, and silently updates the session answers + AURA score.

DESIGN CONSTRAINTS (beta, ~100 users):
  - No external queue (Celery, Redis, RQ) — single Railway worker, not worth it.
  - No pg_notify — adds driver complexity for marginal latency improvement.
  - Simple: poll every POLL_INTERVAL_S seconds, process up to BATCH_SIZE items.
  - Retry cap: 3 attempts. Failed items are left in status='failed' for audit.
  - Silent update: user sees the improved score on next page load. No push.
    Rationale: at beta scale, most users check results once. A score that
    improves silently over ~60 seconds is better UX than a "score pending"
    spinner that blocks the results page.

SAFETY:
  - Stale-lock recovery: items stuck in status='processing' for > STALE_TIMEOUT_S
    are reset to 'pending'. This handles Railway restarts mid-evaluation.
  - Optimistic AURA update: we only call upsert_aura_score if the session's
    current competency score was derived from the degraded answer we just fixed.
    We compare the session's stored competency_score to what we recorded as
    degraded_score at enqueue time. If they differ (another re-eval already ran,
    or user retook assessment), we skip the AURA update to avoid stomping a
    better score.
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta
from typing import Any

from loguru import logger
from supabase._async.client import AsyncClient
from supabase._async.client import create_client as acreate_client

from app.config import settings
from app.core.assessment.bars import EvaluationResult, evaluate_answer

# ── Tuning constants ──────────────────────────────────────────────────────────

POLL_INTERVAL_S: float = 60.0       # seconds between queue drain cycles
BATCH_SIZE: int = 10                 # max items processed per cycle
STALE_TIMEOUT_S: float = 300.0      # 5 min — reset 'processing' items this old
MAX_RETRIES: int = 3


# ── Admin client factory (module-level singleton for background task) ─────────

_admin_client: AsyncClient | None = None


async def _get_admin() -> AsyncClient:
    """Return a cached admin Supabase client for background use.

    Background tasks cannot use FastAPI Depends(), so we manage one long-lived
    admin client here. It's safe because the background task is a single
    asyncio coroutine — no concurrency issues within this module.
    """
    global _admin_client
    if _admin_client is None:
        _admin_client = await acreate_client(
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_service_key,
        )
    return _admin_client


# ── Queue helpers ─────────────────────────────────────────────────────────────


async def enqueue_degraded_answer(
    db: AsyncClient,
    *,
    session_id: str,
    volunteer_id: str,
    question_id: str,
    competency_slug: str,
    question_en: str,
    answer_text: str,
    expected_concepts: list[dict[str, Any]],
    degraded_score: float,
) -> str | None:
    """Insert one item into evaluation_queue. Returns the new queue item UUID.

    Called from assessment.py submit_answer() immediately after a
    keyword_fallback evaluation. The insert is best-effort — if it fails
    (e.g. table not yet migrated), we log and continue so the degraded score
    is still returned to the user.
    """
    try:
        result = await db.table("evaluation_queue").insert({
            "session_id": session_id,
            "volunteer_id": volunteer_id,
            "question_id": question_id,
            "competency_slug": competency_slug,
            "question_en": question_en,
            "answer_text": answer_text,
            "expected_concepts": expected_concepts,  # Supabase auto-serialises list→jsonb
            "degraded_score": degraded_score,
            "status": "pending",
        }).execute()
        item_id: str | None = result.data[0]["id"] if result.data else None
        logger.info(
            "Degraded answer queued for re-evaluation",
            item_id=item_id,
            session_id=session_id,
            competency_slug=competency_slug,
        )
        return item_id
    except Exception as e:
        # Non-fatal: degraded score still applied, just won't be improved later
        logger.warning(
            "Failed to enqueue degraded answer (table may not exist yet)",
            session_id=session_id,
            error=str(e)[:200],
        )
        return None


# ── Core worker loop ──────────────────────────────────────────────────────────


async def _recover_stale_items(db: AsyncClient) -> None:
    """Reset items stuck in 'processing' that are older than STALE_TIMEOUT_S.

    Handles Railway restarts: if the process crashed mid-evaluation, the item
    stays in 'processing' forever without this recovery step.
    """
    stale_cutoff = (
        datetime.now(UTC) - timedelta(seconds=STALE_TIMEOUT_S)
    ).isoformat()
    try:
        result = await db.table("evaluation_queue").update(
            {"status": "pending", "started_at": None}
        ).eq("status", "processing").lt("started_at", stale_cutoff).execute()
        count = len(result.data) if result.data else 0
        if count:
            logger.info("Recovered stale evaluation_queue items", count=count)
    except Exception as e:
        logger.warning("Stale item recovery failed", error=str(e)[:200])


async def _fetch_pending_batch(db: AsyncClient) -> list[dict[str, Any]]:
    """Fetch up to BATCH_SIZE pending items, oldest first."""
    try:
        result = await (
            db.table("evaluation_queue")
            .select("*")
            .eq("status", "pending")
            .lt("retry_count", MAX_RETRIES)
            .order("queued_at", desc=False)
            .limit(BATCH_SIZE)
            .execute()
        )
        return result.data or []
    except Exception as e:
        logger.error("Failed to fetch evaluation_queue batch", error=str(e)[:200])
        return []


async def _mark_processing(db: AsyncClient, item_id: str) -> None:
    await db.table("evaluation_queue").update({
        "status": "processing",
        "started_at": datetime.now(UTC).isoformat(),
    }).eq("id", item_id).eq("status", "pending").execute()


async def _process_item(db: AsyncClient, item: dict[str, Any]) -> None:
    """Re-evaluate one queued item and reconcile scores if successful."""
    item_id: str = item["id"]
    session_id: str = item["session_id"]
    volunteer_id: str = item["volunteer_id"]
    competency_slug: str = item["competency_slug"]
    degraded_score: float = float(item["degraded_score"])

    await _mark_processing(db, item_id)

    try:
        expected_concepts: list[dict[str, Any]] = (
            item["expected_concepts"]
            if isinstance(item["expected_concepts"], list)
            else json.loads(item["expected_concepts"])
        )

        eval_result: EvaluationResult = await evaluate_answer(  # type: ignore[assignment]
            question_en=item["question_en"],
            answer=item["answer_text"],
            expected_concepts=expected_concepts,
            return_details=True,
        )

        llm_score: float = eval_result.composite
        llm_model: str = eval_result.model_used
        score_delta: float = round(llm_score - degraded_score, 4)

        # ── Reconcile session answers ──────────────────────────────────────────
        # Find the specific ItemRecord in session.answers that has this question_id
        # and evaluation_mode="degraded", and replace its raw_score + evaluation_log.
        await _reconcile_session(
            db=db,
            session_id=session_id,
            question_id=item["question_id"],
            llm_score=llm_score,
            llm_model=llm_model,
            eval_result=eval_result,
        )

        # ── Reconcile AURA score ───────────────────────────────────────────────
        await _reconcile_aura(
            db=db,
            session_id=session_id,
            volunteer_id=volunteer_id,
            competency_slug=competency_slug,
            degraded_score=degraded_score,
            llm_score=llm_score,
        )

        # ── Mark done ─────────────────────────────────────────────────────────
        await db.table("evaluation_queue").update({
            "status": "done",
            "completed_at": datetime.now(UTC).isoformat(),
            "llm_score": llm_score,
            "llm_model": llm_model,
            "score_delta": score_delta,
        }).eq("id", item_id).execute()

        logger.info(
            "Re-evaluation complete",
            item_id=item_id,
            session_id=session_id,
            competency_slug=competency_slug,
            degraded_score=round(degraded_score, 3),
            llm_score=round(llm_score, 3),
            delta=score_delta,
            model=llm_model,
        )

    except Exception as e:
        # Increment retry_count; if >= MAX_RETRIES the item is excluded from future polls
        new_retry = int(item.get("retry_count", 0)) + 1
        new_status = "failed" if new_retry >= MAX_RETRIES else "pending"
        try:
            await db.table("evaluation_queue").update({
                "status": new_status,
                "retry_count": new_retry,
                "started_at": None,
                "error_detail": str(e)[:500],
            }).eq("id", item_id).execute()
        except Exception as inner_e:
            logger.error("Failed to update queue item after error", item_id=item_id, error=str(inner_e)[:200])

        logger.warning(
            "Re-evaluation failed",
            item_id=item_id,
            session_id=session_id,
            attempt=new_retry,
            error=str(e)[:300],
        )


async def _reconcile_session(
    db: AsyncClient,
    *,
    session_id: str,
    question_id: str,
    llm_score: float,
    llm_model: str,
    eval_result: EvaluationResult,
) -> None:
    """Update the ItemRecord in session.answers with the LLM score.

    The session.answers JSONB column stores a list of ItemRecord dicts.
    We find the entry for this question_id and patch its raw_score and
    evaluation_log. The IRT theta is NOT recalculated — that would require
    re-running full EAP estimation across the session, which is out of scope
    for beta. The score improvement is reflected in AURA but not in theta.

    This is the correct trade-off: theta is a latent variable estimated from
    all items jointly; a single-item patch would corrupt the estimate. AURA
    is what the user sees, so that's what we update.
    """
    try:
        session_result = await db.table("assessment_sessions").select("answers").eq("id", session_id).single().execute()
        if not session_result.data:
            logger.warning("Session not found during reconcile_session", session_id=session_id)
            return

        answers: list[dict[str, Any]] = session_result.data.get("answers") or []

        patched = False
        for item_record in answers:
            if item_record.get("question_id") == question_id:
                item_record["raw_score"] = llm_score
                # Replace the evaluation_log with the LLM version
                new_log = eval_result.to_log()
                # Mark as upgraded so the explanation endpoint can distinguish
                new_log["reeval_from"] = "keyword_fallback"
                new_log["reeval_model"] = llm_model
                item_record["evaluation_log"] = new_log
                patched = True
                break

        if not patched:
            logger.warning(
                "ItemRecord not found in session answers during reconcile",
                session_id=session_id,
                question_id=question_id,
            )
            return

        await db.table("assessment_sessions").update(
            {"answers": answers}
        ).eq("id", session_id).execute()

    except Exception as e:
        logger.error("reconcile_session failed", session_id=session_id, error=str(e)[:300])
        raise


async def _reconcile_aura(
    db: AsyncClient,
    *,
    session_id: str,
    volunteer_id: str,
    competency_slug: str,
    degraded_score: float,
    llm_score: float,
) -> None:
    """Recompute and upsert AURA score if the LLM score differs meaningfully.

    SAFETY CHECK: we only update AURA if the session's stored competency_score
    still reflects the degraded value (within 0.01 tolerance). If it doesn't,
    either:
      a) A fresh assessment was completed and already wrote a better score, or
      b) Another queue item for the same session already ran first.
    In both cases we skip — we never stomp a higher or fresher score.
    """
    try:
        # Read current aura_scores to get the full competency_scores JSONB
        aura_result = await db.table("aura_scores").select(
            "competency_scores"
        ).eq("volunteer_id", volunteer_id).maybe_single().execute()

        if not aura_result.data:
            # No AURA row yet — nothing to reconcile
            logger.debug("No aura_scores row found, skipping AURA reconcile", volunteer_id=volunteer_id)
            return

        current_comp_scores: dict[str, float] = aura_result.data.get("competency_scores") or {}
        current_slug_score = current_comp_scores.get(competency_slug)

        if current_slug_score is None:
            logger.debug(
                "competency_slug not in aura_scores, skipping reconcile",
                volunteer_id=volunteer_id,
                competency_slug=competency_slug,
            )
            return

        # Safety gate: only update if stored score matches degraded_score within tolerance
        # (Meaning: this degraded answer is still the source of truth for this competency)
        if abs(current_slug_score - degraded_score) > 0.01:
            logger.info(
                "Skipping AURA reconcile — stored score differs from degraded_score (fresher data exists)",
                volunteer_id=volunteer_id,
                competency_slug=competency_slug,
                stored=round(current_slug_score, 3),
                degraded=round(degraded_score, 3),
            )
            return

        # Patch the competency score with the LLM result
        updated_comp_scores = {**current_comp_scores, competency_slug: round(llm_score, 2)}

        # Re-upsert via the existing RPC — this recomputes total_score, badge_tier,
        # elite_status, percentile_rank, and appends to aura_history automatically.
        await db.rpc(
            "upsert_aura_score",
            {
                "p_volunteer_id": volunteer_id,
                "p_competency_scores": updated_comp_scores,
            },
        ).execute()

        logger.info(
            "AURA score reconciled after re-evaluation",
            volunteer_id=volunteer_id,
            competency_slug=competency_slug,
            old_score=round(degraded_score, 3),
            new_score=round(llm_score, 2),
        )

    except Exception as e:
        logger.error("reconcile_aura failed", volunteer_id=volunteer_id, error=str(e)[:300])
        raise


# ── Worker entrypoint ─────────────────────────────────────────────────────────


async def run_reeval_worker() -> None:
    """Long-running background task. Start via asyncio.create_task() at lifespan.

    Loop:
      1. Recover stale 'processing' items (crash safety).
      2. Fetch up to BATCH_SIZE pending items.
      3. Process each item sequentially (not parallel — Gemini rate limits).
      4. Sleep POLL_INTERVAL_S before next cycle.

    Sequential processing is intentional: at beta scale (100 users, <<10 degraded
    answers per hour), parallelism adds complexity without meaningful throughput gain.
    If the queue grows to thousands of items, switch to asyncio.gather() with a
    semaphore of 3-5 concurrent calls.
    """
    logger.info("Re-evaluation worker started", poll_interval_s=POLL_INTERVAL_S, batch_size=BATCH_SIZE)

    while True:
        try:
            db = await _get_admin()
            await _recover_stale_items(db)

            items = await _fetch_pending_batch(db)
            if items:
                logger.info("Processing re-evaluation batch", count=len(items))
                for item in items:
                    await _process_item(db, item)
            # else: queue is empty, nothing to log (would spam logs)

        except asyncio.CancelledError:
            logger.info("Re-evaluation worker cancelled, shutting down")
            break
        except Exception as e:
            # Outer catch: worker must NEVER die permanently on an unexpected error.
            # Log and continue — next cycle may succeed.
            logger.error("Re-evaluation worker cycle failed", error=str(e)[:500])

        await asyncio.sleep(POLL_INTERVAL_S)
