"""Assessment reward emission — crystal + skill_verified character events.

Rule: This module NEVER imports from app.routers.*
All types come from app.schemas.*, app.deps, app.core.*, or stdlib.
"""

from __future__ import annotations

from datetime import datetime, timezone

from loguru import logger

from app.core.assessment.aura_calc import BADGE_TIERS
from app.deps import SupabaseAdmin

# Crystal reward per competency completion (completion-based, NOT score-based)
CRYSTAL_REWARD = 50


def competency_badge_tier(score: float) -> str | None:
    """Return badge tier name for a competency score using the same thresholds as AURA."""
    for tier_name, threshold in BADGE_TIERS:
        if score >= threshold:
            return tier_name
    return None


async def emit_assessment_rewards(
    db: SupabaseAdmin,
    user_id: str,
    skill_slug: str,
    competency_score: float,
) -> None:
    """Emit crystal_earned + skill_verified character events after assessment completion.

    Best-effort: logs errors but never raises — must not fail the complete_assessment response.
    Idempotency: game_character_rewards PRIMARY KEY (user_id, skill_slug) ensures one claim per user
    per competency. Anti-farming: idempotency check happens BEFORE any write.
    """
    # ── Idempotency check: already rewarded for this competency? ─────────────
    reward_check = (
        await db.table("game_character_rewards")
        .select("claimed")
        .eq("user_id", user_id)
        .eq("skill_slug", skill_slug)
        .execute()
    )
    crystals_already_claimed = bool(reward_check.data)

    # ── crystal_earned event (50 per competency, once only) ──────────────────
    if not crystals_already_claimed:
        try:
            await db.table("character_events").insert({
                "user_id": user_id,
                "event_type": "crystal_earned",
                "payload": {
                    "amount": CRYSTAL_REWARD,
                    "source": "volaura_assessment",
                    "skill_slug": skill_slug,
                    "_schema_version": 1,
                },
                "source_product": "volaura",
            }).execute()

            await db.table("game_crystal_ledger").insert({
                "user_id": user_id,
                "amount": CRYSTAL_REWARD,
                "source": "volaura_assessment",
                "reference_id": skill_slug,
            }).execute()

            await db.table("game_character_rewards").upsert({
                "user_id": user_id,
                "skill_slug": skill_slug,
                "crystals": CRYSTAL_REWARD,
                "claimed": True,
                "claimed_at": datetime.now(timezone.utc).isoformat(),
            }).execute()

            logger.info(
                "Crystal reward emitted",
                user_id=user_id,
                skill_slug=skill_slug,
                crystals=CRYSTAL_REWARD,
            )
        except Exception as exc:
            logger.error(
                "Failed to emit crystal reward — manual reconciliation needed",
                user_id=user_id,
                skill_slug=skill_slug,
                error=str(exc),
            )

    # ── skill_verified event (only if score >= Bronze threshold) ────────────
    badge_tier = competency_badge_tier(competency_score)
    if badge_tier is not None:
        try:
            await db.table("character_events").insert({
                "user_id": user_id,
                "event_type": "skill_verified",
                "payload": {
                    "skill_slug": skill_slug,
                    "aura_score": round(competency_score, 2),
                    "badge_tier": badge_tier,
                    "_schema_version": 1,
                },
                "source_product": "volaura",
            }).execute()

            logger.info(
                "Skill verified event emitted",
                user_id=user_id,
                skill_slug=skill_slug,
                score=competency_score,
                badge_tier=badge_tier,
            )
        except Exception as exc:
            logger.error(
                "Failed to emit skill_verified event",
                user_id=user_id,
                skill_slug=skill_slug,
                error=str(exc),
            )
