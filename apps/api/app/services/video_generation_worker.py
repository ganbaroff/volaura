"""Async video generation worker for BrandedBy AI Twin videos.

Polls brandedby.generations for queued jobs, calls ZeusVideoSkill (fal.ai
MuseTalk), and writes video_url back to the row on completion.

DESIGN (same constraints as reeval_worker.py):
  - No external queue — single Railway worker, asyncio.create_task in lifespan
  - Poll every POLL_INTERVAL_S seconds, process one job at a time (video gen
    is expensive — no parallel execution to avoid fal.ai rate limits)
  - Stale-lock recovery: items stuck in 'processing' for > STALE_TIMEOUT_S
    are reset to 'queued'. Handles Railway restarts mid-generation.
  - Only starts if settings.fal_api_key is set (graceful no-op without key)

FLOW:
  queued → (worker picks up) → processing → completed (video_url set)
                                          └→ failed    (error_message set)
"""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from loguru import logger
from supabase._async.client import AsyncClient
from supabase._async.client import create_client as acreate_client

from app.config import settings

# Ensure packages/ is importable (monorepo: packages/swarm/zeus_video_skill.py)
_project_root = Path(__file__).parent.parent.parent.parent.parent  # apps/api/.. → root
_packages_path = str(_project_root / "packages")
if _packages_path not in sys.path:
    sys.path.insert(0, _packages_path)

# ── Tuning constants ─────────────────────────────────────────────────────────

POLL_INTERVAL_S: float = 15.0       # seconds between queue drain cycles
STALE_TIMEOUT_S: float = 600.0      # 10 min — video gen can take up to 3 min
MAX_RETRIES: int = 2                 # fal.ai sometimes has transient failures


# ── Admin client singleton (background task can't use FastAPI Depends()) ──────

_admin_client: AsyncClient | None = None


async def _get_admin() -> AsyncClient:
    global _admin_client
    if _admin_client is None:
        _admin_client = await acreate_client(
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_service_key,
        )
    return _admin_client


# ── Stale lock recovery ───────────────────────────────────────────────────────


async def _recover_stale_jobs(db: AsyncClient) -> None:
    """Reset jobs stuck in 'processing' older than STALE_TIMEOUT_S → 'queued'."""
    stale_cutoff = (
        datetime.now(UTC) - timedelta(seconds=STALE_TIMEOUT_S)
    ).isoformat()
    try:
        result = (
            await db.schema("brandedby")
            .table("generations")
            .update({"status": "queued", "processing_started_at": None})
            .eq("status", "processing")
            .lt("processing_started_at", stale_cutoff)
            .execute()
        )
        count = len(result.data) if result.data else 0
        if count:
            logger.info("Recovered stale video generation jobs", count=count)
    except Exception as e:
        logger.warning("Stale job recovery failed", error=str(e)[:200])


# ── Fetch one queued job ──────────────────────────────────────────────────────


async def _fetch_next_job(db: AsyncClient) -> dict[str, Any] | None:
    """Return the oldest queued job (queue_position ASC), or None if empty."""
    try:
        result = (
            await db.schema("brandedby")
            .table("generations")
            .select("id, twin_id, user_id, gen_type, input_text, retry_count")
            .eq("status", "queued")
            .order("queue_position", desc=False)
            .order("created_at", desc=False)
            .limit(1)
            .execute()
        )
        if not result.data:
            return None
        job = result.data[0]
        # Skip if exhausted retries
        if (job.get("retry_count") or 0) >= MAX_RETRIES:
            return None
        return job
    except Exception as e:
        logger.warning("Failed to fetch next video job", error=str(e)[:200])
        return None


# ── Lock job (optimistic: prevents double-processing on restart) ──────────────


async def _lock_job(db: AsyncClient, gen_id: str) -> bool:
    """Set status='processing' + processing_started_at. Returns False if already locked."""
    try:
        result = (
            await db.schema("brandedby")
            .table("generations")
            .update({
                "status": "processing",
                "processing_started_at": datetime.now(UTC).isoformat(),
            })
            .eq("id", gen_id)
            .eq("status", "queued")  # only lock if still queued (optimistic)
            .execute()
        )
        return bool(result.data)
    except Exception as e:
        logger.warning("Failed to lock job", gen_id=gen_id, error=str(e)[:200])
        return False


# ── Mark complete / failed ────────────────────────────────────────────────────


async def _mark_completed(db: AsyncClient, gen_id: str, video_url: str) -> None:
    try:
        await (
            db.schema("brandedby")
            .table("generations")
            .update({
                "status": "completed",
                "output_url": video_url,
                "completed_at": datetime.now(UTC).isoformat(),
            })
            .eq("id", gen_id)
            .execute()
        )
    except Exception as e:
        logger.error("Failed to mark generation completed", gen_id=gen_id, error=str(e))


async def _mark_failed(
    db: AsyncClient, gen_id: str, error: str, retry_count: int
) -> None:
    """Mark as failed. If retry_count < MAX_RETRIES - 1, requeue instead."""
    new_retry = retry_count + 1
    if new_retry < MAX_RETRIES:
        # Requeue with incremented retry_count — will be picked up next cycle
        new_status = "queued"
        logger.warning(
            "Video generation failed, requeueing",
            gen_id=gen_id,
            retry=new_retry,
            error=error[:200],
        )
    else:
        new_status = "failed"
        logger.error(
            "Video generation permanently failed",
            gen_id=gen_id,
            retries=new_retry,
            error=error[:200],
        )
    try:
        await (
            db.schema("brandedby")
            .table("generations")
            .update({
                "status": new_status,
                "error_message": error[:500],
                "retry_count": new_retry,
            })
            .eq("id", gen_id)
            .execute()
        )
    except Exception as e:
        logger.error("Failed to mark generation failed", gen_id=gen_id, error=str(e))


# ── Process one job ───────────────────────────────────────────────────────────


async def _process_job(db: AsyncClient, job: dict[str, Any]) -> None:
    """Generate video for one queued job. Updates Supabase on completion/failure."""
    from swarm.zeus_video_skill import ZeusVideoSkill

    gen_id: str = job["id"]
    twin_id: str = job["twin_id"]
    script: str = job.get("input_text") or ""
    retry_count: int = job.get("retry_count") or 0

    logger.info(
        "Processing video generation job",
        gen_id=gen_id,
        twin_id=twin_id,
        script_length=len(script),
        retry=retry_count,
    )

    # Get twin's photo_url
    try:
        twin_result = (
            await db.schema("brandedby")
            .table("ai_twins")
            .select("photo_url, personality_prompt")
            .eq("id", twin_id)
            .single()
            .execute()
        )
        photo_url: str = twin_result.data.get("photo_url") or ""
        personality_prompt: str = twin_result.data.get("personality_prompt") or ""
    except Exception as e:
        await _mark_failed(db, gen_id, f"Twin lookup failed: {e}", retry_count)
        return

    if not photo_url:
        await _mark_failed(db, gen_id, "AI Twin has no photo_url", retry_count)
        return

    # Use personality_prompt as script preamble if no explicit input_text
    if not script and personality_prompt:
        # Fallback: first 2 sentences of personality as spoken intro
        sentences = personality_prompt.split(". ")
        script = ". ".join(sentences[:2]) + "."

    if not script:
        await _mark_failed(db, gen_id, "No script or personality prompt available", retry_count)
        return

    # Call ZeusVideoSkill
    try:
        skill = ZeusVideoSkill(fal_api_key=settings.fal_api_key)
        video_url = await skill.generate(
            photo_url=photo_url,
            script=script,
            generation_id=gen_id,
        )
        await _mark_completed(db, gen_id, video_url)
        logger.info("Video generation complete", gen_id=gen_id, video_url=video_url[:60])
    except Exception as e:
        await _mark_failed(db, gen_id, str(e), retry_count)


# ── Main worker loop ──────────────────────────────────────────────────────────


async def run_video_generation_worker() -> None:
    """Background worker — polls brandedby.generations and processes queued jobs.

    Only starts if FAL_API_KEY is configured. Silently exits otherwise.
    Called from main.py lifespan as asyncio.create_task().
    """
    if not settings.fal_api_key:
        logger.info(
            "Video generation worker disabled (FAL_API_KEY not set). "
            "Set FAL_API_KEY to enable AI Twin video generation."
        )
        return

    logger.info("BrandedBy video generation worker started", poll_interval=POLL_INTERVAL_S)
    db = await _get_admin()

    while True:
        try:
            # Recover any jobs stuck mid-generation (Railway restarts)
            await _recover_stale_jobs(db)

            # Pick up next queued job
            job = await _fetch_next_job(db)
            if job:
                locked = await _lock_job(db, job["id"])
                if locked:
                    await _process_job(db, job)
                else:
                    # Race condition: another worker instance grabbed it (shouldn't
                    # happen in single-process Railway, but safe to handle)
                    logger.debug("Job already locked, skipping", gen_id=job["id"])

        except asyncio.CancelledError:
            logger.info("Video generation worker shutting down...")
            raise
        except Exception as e:
            # Never crash the worker — log and continue
            logger.error("Video generation worker error", error=str(e), exc_info=True)

        await asyncio.sleep(POLL_INTERVAL_S)
