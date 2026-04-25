"""BrandedBy personality refresh worker — G3.3, the last piece of the ecosystem loop.

WHY THIS EXISTS:
  ecosystem_consumer.py reacts to character_events (aura_updated, badge_tier_changed)
  and sets brandedby.ai_twins.needs_personality_refresh = true for affected users.
  This worker closes the loop: it reads stale twins and regenerates their personality
  prompt via Gemini so the AI Twin always reflects current verified skills.

DESIGN:
  - Batch-bounded (REFRESH_BATCH_SIZE) — free-tier safe.
  - Uses two SECURITY DEFINER RPCs in public schema:
      brandedby_get_stale_twins(p_limit INT) → (id, user_id, display_name)
      brandedby_apply_twin_personality(p_twin_id UUID, p_personality TEXT) → void
    The brandedby schema is not exposed via PostgREST; RPCs cross the boundary at
    the postgres layer.
  - get_character_state RPC loads verified skills + AURA data for each twin's user.
    If character state is missing the twin is skipped (user may have been deleted).
  - Fire-forward: per-twin errors are logged and counted but never block other twins.
  - Fallback personality: generate_twin_personality has its own LLM fallback; this
    worker only needs to catch unexpected exceptions from that call.

WIRE-UP:
  Called by GitHub Actions cron (every hour) or:
  python -m app.services.brandedby_refresh_worker
"""

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass, field

from loguru import logger
from supabase._async.client import AsyncClient
from supabase._async.client import create_client as acreate_client

from app.services.brandedby_personality import generate_twin_personality

# ── Tuning ─────────────────────────────────────────────────────────────────────

REFRESH_BATCH_SIZE: int = int(os.environ.get("BRANDEDBY_REFRESH_BATCH_SIZE", "20"))


# ── Stats dataclass ────────────────────────────────────────────────────────────


@dataclass
class RefreshStats:
    refreshed: int = 0
    skipped: int = 0
    errors: int = 0
    latency_ms: float = 0
    provider: str = "unknown"


# ── Admin client ───────────────────────────────────────────────────────────────


async def _admin() -> AsyncClient:
    from app.config import settings

    return await acreate_client(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_service_key,
    )


# ── Core worker ────────────────────────────────────────────────────────────────


async def run_brandedby_refresh(db: AsyncClient | None = None) -> RefreshStats:
    """Fetch stale AI twins and regenerate personality prompts.

    Returns RefreshStats(refreshed, skipped, errors).
    Each twin is processed independently; errors on one twin never block others.
    """
    if db is None:
        db = await _admin()

    stats = RefreshStats()

    # 1. Fetch stale twins (SECURITY DEFINER RPC — brandedby schema not in PostgREST)
    try:
        twins_result = await db.rpc(
            "brandedby_claim_stale_twins",
            {"p_limit": REFRESH_BATCH_SIZE, "p_lock_ttl_minutes": 30},
        ).execute()
    except Exception as exc:
        logger.error(
            "brandedby_refresh_worker: failed to fetch stale twins",
            error=str(exc)[:300],
        )
        return stats

    twins: list[dict] = twins_result.data or []

    if not twins:
        logger.debug("brandedby_refresh_worker: no stale twins found")
        return stats

    logger.info("brandedby_refresh_worker: processing stale twins", count=len(twins))

    for twin in twins:
        twin_id: str = twin["id"]
        user_id: str = twin["user_id"]
        display_name: str = twin.get("display_name") or "Professional"

        # 2. Load character state for this user
        try:
            state_result = await db.rpc(
                "get_character_state",
                {"p_user_id": user_id},
            ).execute()
            character_state: dict = state_result.data or {}
            if not character_state:
                logger.warning(
                    "brandedby_refresh_worker: empty character state, skipping twin",
                    twin_id=twin_id,
                    user_id=user_id,
                )
                stats.skipped += 1
                continue
        except Exception as exc:
            logger.error(
                "brandedby_refresh_worker: get_character_state failed",
                twin_id=twin_id,
                user_id=user_id,
                error=str(exc)[:300],
            )
            stats.errors += 1
            continue

        # 3. Generate personality prompt
        _meta: dict = {}
        t_gen_start = time.monotonic()
        try:
            personality = await generate_twin_personality(display_name, character_state, _meta=_meta)
        except Exception as exc:
            logger.error(
                "brandedby_refresh_worker: generate_twin_personality raised",
                twin_id=twin_id,
                display_name=display_name,
                error=str(exc)[:300],
            )
            # Release lock so this twin is retried on next run
            try:
                await db.rpc("brandedby_release_twin_lock", {"p_twin_id": twin_id}).execute()
            except Exception:
                pass
            stats.errors += 1
            continue

        gen_latency_ms = round((time.monotonic() - t_gen_start) * 1000)
        provider = _meta.get("provider", "unknown")
        latency_ms = _meta.get("latency_ms", gen_latency_ms)
        token_estimate = len(personality) // 4
        # Telemetry inlined into message string — default loguru format does not render extras
        logger.info(
            f"brandedby_refresh_worker: twin personality generated "
            f"twin_id={twin_id} provider={provider} latency_ms={latency_ms} "
            f"prompt_len={len(personality)} token_estimate={token_estimate}",
            twin_id=twin_id,
            provider=provider,
            latency_ms=latency_ms,
            prompt_len=len(personality),
            token_estimate=token_estimate,
        )

        # 4. Apply personality and reset the stale flag
        try:
            await db.rpc(
                "brandedby_apply_twin_personality",
                {"p_twin_id": twin_id, "p_personality": personality},
            ).execute()
            stats.refreshed += 1
            logger.info(
                "brandedby_refresh_worker: twin personality refreshed",
                twin_id=twin_id,
                user_id=user_id,
                personality_len=len(personality),
            )
        except Exception as exc:
            logger.error(
                "brandedby_refresh_worker: apply_twin_personality failed",
                twin_id=twin_id,
                user_id=user_id,
                error=str(exc)[:300],
            )
            # Release lock so this twin is retried on next run
            try:
                await db.rpc("brandedby_release_twin_lock", {"p_twin_id": twin_id}).execute()
            except Exception:
                pass
            stats.errors += 1

    logger.info(
        "brandedby_refresh_worker: batch complete",
        refreshed=stats.refreshed,
        skipped=stats.skipped,
        errors=stats.errors,
    )
    return stats


# ── CLI entrypoint ─────────────────────────────────────────────────────────────


async def _main() -> None:
    stats = await run_brandedby_refresh()
    logger.info(
        "brandedby_refresh_worker CLI complete",
        refreshed=stats.refreshed,
        skipped=stats.skipped,
        errors=stats.errors,
    )


if __name__ == "__main__":
    asyncio.run(_main())
