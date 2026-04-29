"""Ecosystem event emitter — assessment data flows to ALL 5 products.

Emits structured events to `character_events` table so MindShift, Life Simulator,
BrandedBy, and Atlas can react to assessment outcomes without knowing assessment internals.

Events:
  - assessment_completed: a competency test was finished (score, energy, items)
  - aura_updated:         total AURA score recalculated (total, badge, competencies)
  - badge_tier_changed:   user earned a new badge tier (old → new)

Design:
  - Fire-and-forget: NEVER blocks the /complete response
  - All errors caught and logged — ecosystem integration must not break core flow
  - Schema versioned (_schema_version: 1) for backward-compatible evolution
  - source_product always "volaura" — other products emit their own events

Cross-references:
  - character_events table: supabase/migrations/*_character_events.sql
  - Existing emitters: app/services/assessment/rewards.py (crystal_earned, skill_verified)
  - Cross-product bridge: app/services/cross_product_bridge.py (MindShift push)
  - Architecture: docs/research/ASSESSMENT-ARCHITECTURE-RESEARCH-2026-04-13.md Part 2
"""

from __future__ import annotations

from typing import Any

from loguru import logger


async def emit_assessment_completed(
    db: Any,
    user_id: str,
    competency_slug: str,
    competency_score: float,
    items_answered: int,
    energy_level: str,
    stop_reason: str | None,
    gaming_flags: list[str] | None = None,
) -> bool:
    """Emit assessment_completed event to the ecosystem bus.

    Returns True on success, False on failure. Caller must check return value
    before marking ecosystem_events step as done.

    Consumed by:
      - MindShift: adapts coaching path based on competency + score
      - Life Simulator: triggers character stat update
      - Atlas: updates agent context for next user interaction
    """
    try:
        await (
            db.table("character_events")
            .insert(
                {
                    "user_id": user_id,
                    "event_type": "assessment_completed",
                    "payload": {
                        "competency_slug": competency_slug,
                        "competency_score": round(competency_score, 2),
                        "items_answered": items_answered,
                        "energy_level": energy_level,
                        "stop_reason": stop_reason,
                        "gaming_flags": gaming_flags or [],
                        "_schema_version": 1,
                    },
                    "source_product": "volaura",
                }
            )
            .execute()
        )
        logger.info(
            "Ecosystem event: assessment_completed",
            user_id=user_id,
            competency_slug=competency_slug,
            score=round(competency_score, 2),
        )
        return True
    except Exception as exc:
        logger.error(
            "Failed to emit assessment_completed event",
            user_id=user_id,
            error=str(exc)[:200],
        )
        return False


async def emit_aura_updated(
    db: Any,
    user_id: str,
    total_score: float,
    badge_tier: str,
    competency_scores: dict[str, float],
    elite_status: bool,
    percentile_rank: float | None,
) -> bool:
    """Emit aura_updated event after AURA score recalculation.

    Returns True on success, False on failure.

    Consumed by:
      - Life Simulator: updates character base stats from competency_scores
      - BrandedBy: checks if new content templates should unlock
      - Atlas: refreshes agent's knowledge of user capability profile
    """
    try:
        await (
            db.table("character_events")
            .insert(
                {
                    "user_id": user_id,
                    "event_type": "aura_updated",
                    "payload": {
                        "total_score": round(total_score, 2),
                        "badge_tier": badge_tier,
                        "competency_scores": {k: round(v, 2) for k, v in competency_scores.items()},
                        "elite_status": elite_status,
                        "percentile_rank": round(percentile_rank, 1) if percentile_rank else None,
                        "_schema_version": 1,
                    },
                    "source_product": "volaura",
                }
            )
            .execute()
        )
        logger.info(
            "Ecosystem event: aura_updated",
            user_id=user_id,
            total_score=round(total_score, 2),
            badge_tier=badge_tier,
        )
        return True
    except Exception as exc:
        logger.error(
            "Failed to emit aura_updated event",
            user_id=user_id,
            error=str(exc)[:200],
        )
        return False


async def emit_badge_tier_changed(
    db: Any,
    user_id: str,
    old_tier: str | None,
    new_tier: str,
    total_score: float,
) -> bool:
    """Emit badge_tier_changed event when a user's badge tier transitions.

    Only emitted when old_tier != new_tier. Skipped on first assessment (no previous tier).
    Returns True on success, False on failure.

    Consumed by:
      - BrandedBy: unlocks "Verified Professional" content templates at Silver+
      - Life Simulator: triggers character visual upgrade animation
      - Atlas: agent congratulates user on next interaction
    """
    if old_tier == new_tier:
        return True  # no change — skip, not a failure

    try:
        await (
            db.table("character_events")
            .insert(
                {
                    "user_id": user_id,
                    "event_type": "badge_tier_changed",
                    "payload": {
                        "old_tier": old_tier,
                        "new_tier": new_tier,
                        "total_score": round(total_score, 2),
                        "_schema_version": 1,
                    },
                    "source_product": "volaura",
                }
            )
            .execute()
        )
        logger.info(
            "Ecosystem event: badge_tier_changed",
            user_id=user_id,
            old_tier=old_tier,
            new_tier=new_tier,
        )
        return True
    except Exception as exc:
        logger.error(
            "Failed to emit badge_tier_changed event",
            user_id=user_id,
            error=str(exc)[:200],
        )
        return False
