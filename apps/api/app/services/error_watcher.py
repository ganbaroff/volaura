"""Error watcher — nociceptive monitoring for the ecosystem.

Bio-model: ноцицепторы молчат в норме, стреляют на аномалию.
This watcher runs every 10 minutes via cron, checks four signals,
emits character_events with type 'metric_anomaly' when thresholds breached.

Signals:
  1. stuck_sessions — assessment sessions in_progress > 30 min (user abandoned without cleanup)
  2. orphan_events — character_events without matching profile (bridge leak)
  3. error_rate — failed assessment starts in last hour (proxy for 5xx)
  4. ecosystem_event_failures — unresolved DLQ rows in last hour (consumer / refresh failures)

Each anomaly emits to character_events so admin dashboard live feed sees it.
Telegram escalation is future (watcher → atlas_voice → telegram_webhook).
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from loguru import logger

STUCK_SESSION_THRESHOLD_MINUTES = 30
ERROR_RATE_THRESHOLD_PER_HOUR = 5
FAILURE_WATCH_WINDOW_HOURS = 1
# Watcher anomaly events are system-emitted, not user-driven.
# Migration 20260425_character_events_nullable_user_id_for_system makes
# character_events.user_id NULL-able for system events. RLS read policy
# (auth.uid() = user_id) correctly evaluates NULL as falsy, so system
# events stay invisible to user-client SELECT; service-role bypasses RLS.
# Pre-fix: sentinel UUID 00...0 caused FK violation on auth.users(id)
# and silenced ALL watcher emit_anomaly attempts since day one.
WATCHER_USER_ID: str | None = None


async def run_error_watcher() -> dict[str, int]:
    """Run all watcher checks. Returns counts per signal type."""
    from app.deps import get_admin_client

    db = await get_admin_client()
    now = datetime.now(UTC)
    results: dict[str, int] = {}

    # 1. Stuck sessions
    try:
        cutoff = (now - timedelta(minutes=STUCK_SESSION_THRESHOLD_MINUTES)).isoformat()
        stuck = (
            await db.table("assessment_sessions")
            .select("id", count="exact")
            .eq("status", "in_progress")
            .lt("created_at", cutoff)
            .execute()
        )
        count = stuck.count or 0
        results["stuck_sessions"] = count

        if count > 0:
            logger.warning("watcher.stuck_sessions", count=count)
            await _emit_anomaly(
                db,
                "stuck_sessions",
                count,
                {
                    "threshold_minutes": STUCK_SESSION_THRESHOLD_MINUTES,
                    "severity": "warn",
                },
            )

            # Auto-heal: abandon stuck sessions
            await (
                db.table("assessment_sessions")
                .update({"status": "abandoned"})
                .eq("status", "in_progress")
                .lt("created_at", cutoff)
                .execute()
            )
            logger.info("watcher.stuck_sessions.healed", count=count)
    except Exception as e:
        logger.error("watcher.stuck_sessions.failed", error=str(e))
        results["stuck_sessions"] = -1

    # 2. Orphan character_events (user_id not in profiles)
    try:
        one_hour_ago = (now - timedelta(hours=FAILURE_WATCH_WINDOW_HOURS)).isoformat()
        orphan_result = await db.rpc(
            "count_orphan_character_events",
            {"since_ts": one_hour_ago},
        ).execute()
        orphan_count = orphan_result.data if isinstance(orphan_result.data, int) else 0
        results["orphan_events"] = orphan_count

        if orphan_count > 0:
            logger.warning("watcher.orphan_events", count=orphan_count)
            await _emit_anomaly(
                db,
                "orphan_events",
                orphan_count,
                {
                    "window_hours": FAILURE_WATCH_WINDOW_HOURS,
                    "severity": "info",
                },
            )
    except Exception as e:
        # RPC may not exist yet — that's ok, log and move on
        logger.debug("watcher.orphan_events.skipped", error=str(e))
        results["orphan_events"] = -1

    # 3. Failed assessment starts (cooldown hits = proxy for errors)
    try:
        one_hour_ago = (now - timedelta(hours=FAILURE_WATCH_WINDOW_HOURS)).isoformat()
        failed = (
            await db.table("assessment_sessions")
            .select("id", count="exact")
            .eq("status", "abandoned")
            .gt("created_at", one_hour_ago)
            .execute()
        )
        fail_count = failed.count or 0
        results["error_rate_1h"] = fail_count

        if fail_count >= ERROR_RATE_THRESHOLD_PER_HOUR:
            logger.warning("watcher.error_rate", count=fail_count)
            await _emit_anomaly(
                db,
                "error_rate_high",
                fail_count,
                {
                    "window_hours": FAILURE_WATCH_WINDOW_HOURS,
                    "threshold": ERROR_RATE_THRESHOLD_PER_HOUR,
                    "severity": "crit" if fail_count >= ERROR_RATE_THRESHOLD_PER_HOUR * 2 else "warn",
                },
            )
    except Exception as e:
        logger.error("watcher.error_rate.failed", error=str(e))
        results["error_rate_1h"] = -1

    # 5. Atlas obligations approaching deadline (proactive-scan gate, 2026-04-26)
    try:
        from datetime import timedelta as _td
        thirty_days_out = (now + _td(days=30)).isoformat()
        due_soon = (
            await db.table("atlas_obligations")
            .select("id", count="exact")
            .eq("status", "open")
            .lt("deadline", thirty_days_out)
            .execute()
        )
        due_count = due_soon.count or 0
        results["obligations_due_30d"] = due_count

        if due_count > 0:
            logger.warning("watcher.obligations_due_soon", count=due_count)
            await _emit_anomaly(
                db,
                "obligations_due_soon",
                due_count,
                {
                    "window_days": 30,
                    "status": "open",
                    "source_table": "atlas_obligations",
                    "severity": "info",
                },
            )
    except Exception as e:
        # Table may not exist on every environment — degrade gracefully.
        logger.debug("watcher.obligations_due_soon.skipped", error=str(e))
        results["obligations_due_30d"] = -1

    # 4. Unresolved ecosystem event failures in the last hour (DLQ)
    try:
        one_hour_ago = (now - timedelta(hours=FAILURE_WATCH_WINDOW_HOURS)).isoformat()
        unresolved = (
            await db.table("ecosystem_event_failures")
            .select("id", count="exact")
            .is_("resolved_at", "null")
            .gt("last_failed_at", one_hour_ago)
            .execute()
        )
        unresolved_count = unresolved.count or 0
        results["ecosystem_event_failures_1h"] = unresolved_count

        if unresolved_count > 0:
            logger.warning("watcher.ecosystem_event_failures", count=unresolved_count)
            await _emit_anomaly(
                db,
                "ecosystem_event_failures",
                unresolved_count,
                {
                    "window_hours": FAILURE_WATCH_WINDOW_HOURS,
                    "status": "unresolved",
                    "source_table": "ecosystem_event_failures",
                    "severity": "warn",
                },
            )
    except Exception as e:
        # Table may not exist yet in every environment — degrade without breaking the cycle
        logger.debug("watcher.ecosystem_event_failures.skipped", error=str(e))
        results["ecosystem_event_failures_1h"] = -1

    logger.info("watcher.cycle_complete", results=results)
    return results


async def _emit_anomaly(
    db,
    anomaly_type: str,
    value: int,
    payload: dict,
) -> None:
    """Best-effort emit to character_events."""
    try:
        await (
            db.table("character_events")
            .insert(
                {
                    "user_id": WATCHER_USER_ID,
                    "event_type": f"metric_anomaly_{anomaly_type}",
                    "payload": {"value": value, **payload},
                    "source_product": "volaura",
                }
            )
            .execute()
        )
    except Exception as e:
        logger.warning("watcher.emit_failed", anomaly_type=anomaly_type, error=str(e))


if __name__ == "__main__":
    asyncio.run(run_error_watcher())
