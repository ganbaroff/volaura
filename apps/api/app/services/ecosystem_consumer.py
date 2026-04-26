"""Ecosystem event consumer — first real downstream loop.

WHY THIS EXISTS:
  character_events is written by VOLAURA (assessment_completed, aura_updated,
  badge_tier_changed) but no downstream product has ever had a server-side loop
  that reads those events and mutates state.  This service closes that gap for
  BrandedBy: when AURA updates or badge tier changes, BrandedBy's AI twin for
  that user is marked stale so the next refresh_personality call regenerates it
  with the new profile.

DESIGN:
  - Cursor-based: ecosystem_event_cursors.last_processed_at (TIMESTAMPTZ) used
    as the range boundary.  After each batch, cursor advances to the latest
    event's created_at.  last_event_id (UUID) is stored for audit trail and
    future deduplication.
  - Range query uses created_at — reliable ordering even with UUID primary keys.
    When last_processed_at is NULL (first run), all existing events are processed.
  - Batch size bounded (CONSUMER_BATCH_SIZE) — free-tier safe.
  - Idempotent: setting needs_personality_refresh=TRUE when it is already TRUE
    is a no-op on the twin row.  Cursor only advances after the batch is done.
  - Fire-forward: errors on individual twin updates are logged and skipped;
    they don't block cursor advance (repeated hard failures on the same event
    would loop forever otherwise — logged with full context for CTO inspection).

WIRE-UP:
  Called by admin cron trigger (POST /api/admin/ecosystem-consumer/run) or
  directly: python -m app.services.ecosystem_consumer

ADDING NEW PRODUCTS:
  1. Seed a row in ecosystem_event_cursors for the new product.
  2. Write a handler: async def _handle_<product>(db, event) -> bool
  3. Add a processor function following the process_brandedby_events pattern.
  4. Register it in run_once().
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from loguru import logger
from supabase._async.client import AsyncClient
from supabase._async.client import create_client as acreate_client

# ── Tuning ────────────────────────────────────────────────────────────────────

CONSUMER_BATCH_SIZE: int = int(os.environ.get("ECOSYSTEM_CONSUMER_BATCH_SIZE", "100"))

# Event types BrandedBy reacts to.
BRANDEDBY_EVENTS: frozenset[str] = frozenset({"aura_updated", "badge_tier_changed"})


# ── Admin client ──────────────────────────────────────────────────────────────


async def _admin() -> AsyncClient:
    from app.config import settings

    return await acreate_client(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_service_key,
    )


# ── Cursor helpers ────────────────────────────────────────────────────────────


async def _load_cursor(db: AsyncClient, product: str) -> dict[str, Any] | None:
    """Return the cursor row for *product*, or None if it doesn't exist."""
    result = (
        await db.table("ecosystem_event_cursors")
        .select("product,last_event_id,last_processed_at,events_processed_total,events_failed_total")
        .eq("product", product)
        .limit(1)
        .execute()
    )
    rows = result.data or []
    return rows[0] if rows else None


async def _advance_cursor(
    db: AsyncClient,
    product: str,
    last_event_id: str,
    last_processed_at: str,
    new_total: int,
    new_failed_total: int,
) -> None:
    """Advance cursor and update running totals in a single UPDATE."""
    await (
        db.table("ecosystem_event_cursors")
        .update(
            {
                "last_event_id": last_event_id,
                "last_processed_at": last_processed_at,
                "events_processed_total": new_total,
                "events_failed_total": new_failed_total,
            }
        )
        .eq("product", product)
        .execute()
    )


# ── Event fetch ───────────────────────────────────────────────────────────────


async def _fetch_events(
    db: AsyncClient,
    event_types: frozenset[str],
    after_timestamp: str | None,
    limit: int,
) -> list[dict[str, Any]]:
    """Fetch next batch of character_events for the given event types.

    Uses created_at for reliable ordering even with UUID primary keys.
    When after_timestamp is None (first ever run), fetches from the beginning.
    """
    q = (
        db.table("character_events")
        .select("id,user_id,event_type,payload,created_at")
        .in_("event_type", list(event_types))
        .order("created_at", desc=False)
        .order("id", desc=False)
        .limit(limit)
    )
    if after_timestamp is not None:
        q = q.gt("created_at", after_timestamp)
    result = await q.execute()
    return result.data or []


# ── BrandedBy handler ─────────────────────────────────────────────────────────


async def _handle_brandedby_event(db: AsyncClient, event: dict[str, Any]) -> bool:
    """React to aura_updated or badge_tier_changed: mark the AI twin stale.

    Returns True on success (including "no twin found — user not in BrandedBy"),
    False only on unexpected DB errors. On False the caller writes the event to
    ecosystem_event_failures (DLQ) so the cursor can advance without losing it.
    The update is idempotent: setting needs_personality_refresh=TRUE when it's
    already TRUE is safe.
    """
    user_id: str = event["user_id"]
    event_type: str = event["event_type"]
    event_id: str = event["id"]

    try:
        # brandedby schema is not exposed via PostgREST — use SECURITY DEFINER RPC
        # (public.ecosystem_mark_twin_stale) which runs as postgres and can write
        # to brandedby.ai_twins directly.
        result = await db.rpc(
            "ecosystem_mark_twin_stale",
            {"p_user_id": user_id, "p_reason": event_type},
        ).execute()
        updated_count = int(result.data or 0)
        if updated_count == 0:
            # User has no AI twin — not onboarded to BrandedBy yet.  Not an error.
            logger.debug(
                "ecosystem_consumer: no ai_twin for user, skipping",
                user_id=user_id,
                event_id=event_id,
                event_type=event_type,
            )
        else:
            logger.info(
                "ecosystem_consumer: ai_twin marked stale",
                user_id=user_id,
                event_id=event_id,
                event_type=event_type,
                rows_updated=updated_count,
            )
        return True
    except Exception as exc:
        logger.error(
            "ecosystem_consumer: failed to update ai_twin",
            user_id=user_id,
            event_id=event_id,
            event_type=event_type,
            error=str(exc)[:300],
        )
        # DLQ: persist failure so the cursor can move forward without losing
        # the event. Replay tooling reads ecosystem_event_failures later.
        try:
            await db.rpc(
                "ecosystem_record_event_failure",
                {
                    "p_product": "brandedby",
                    "p_event_id": event_id,
                    "p_user_id": user_id,
                    "p_event_type": event_type,
                    "p_error": str(exc)[:1000],
                },
            ).execute()
        except Exception as dlq_exc:
            # Belt-and-suspenders: if DLQ insert itself fails, we still don't
            # block the queue — but log loudly so error_watcher can pick it up.
            logger.error(
                "ecosystem_consumer: DLQ insert failed (silent loss possible)",
                event_id=event_id,
                primary_error=str(exc)[:200],
                dlq_error=str(dlq_exc)[:200],
            )
        return False


# ── Main processor ────────────────────────────────────────────────────────────


async def process_brandedby_events(db: AsyncClient | None = None) -> dict[str, int]:
    """One processing cycle for the BrandedBy product cursor.

    Returns stats dict:
      found       — events fetched from character_events
      handled     — successful handler calls (twin updated or skipped — no twin)
      errors      — handler calls that raised an unexpected DB error
      cursor_at   — 1 if cursor was advanced, 0 if no events found
    """
    if db is None:
        db = await _admin()

    cursor = await _load_cursor(db, "brandedby")
    if cursor is None:
        logger.warning(
            "ecosystem_consumer: brandedby cursor row missing — "
            "run migration 20260424110000_ecosystem_event_cursors.sql"
        )
        return {"found": 0, "handled": 0, "errors": 0, "cursor_at": 0}

    after_ts: str | None = cursor.get("last_processed_at")
    prior_total: int = int(cursor.get("events_processed_total") or 0)
    prior_failed_total: int = int(cursor.get("events_failed_total") or 0)

    events = await _fetch_events(db, BRANDEDBY_EVENTS, after_ts, CONSUMER_BATCH_SIZE)
    stats: dict[str, int] = {"found": len(events), "handled": 0, "errors": 0, "cursor_at": 0}

    if not events:
        logger.debug("ecosystem_consumer: brandedby — no new events", after_ts=after_ts)
        return stats

    last_event_id: str = events[-1]["id"]
    last_processed_at: str = events[-1]["created_at"]

    for event in events:
        ok = await _handle_brandedby_event(db, event)
        if ok:
            stats["handled"] += 1
        else:
            stats["errors"] += 1

    # Always advance cursor — including when some handlers errored.
    # Failed events are persisted to ecosystem_event_failures by the handler,
    # so cursor advance does NOT lose them; replay reads the DLQ table.
    await _advance_cursor(
        db,
        "brandedby",
        last_event_id,
        last_processed_at,
        prior_total + stats["handled"],
        prior_failed_total + stats["errors"],
    )
    stats["cursor_at"] = 1

    logger.info(
        "ecosystem_consumer: brandedby cycle complete",
        **stats,
        prior_total=prior_total,
        new_total=prior_total + stats["handled"],
        new_failed_total=prior_failed_total + stats["errors"],
    )
    return stats


async def run_once() -> dict[str, dict[str, int]]:
    """Run all registered product consumers once.  Returns per-product stats."""
    db = await _admin()
    results: dict[str, dict[str, int]] = {}
    results["brandedby"] = await process_brandedby_events(db)
    return results


async def _main() -> None:
    stats = await run_once()
    for product, s in stats.items():
        logger.info("ecosystem_consumer CLI complete", product=product, **s)


if __name__ == "__main__":
    asyncio.run(_main())
