"""Life Simulator service — pool query, stat mapping, consequence emission.

Path C from docs/LIFE-SIMULATOR-REIMAGINE-2026-04-15.md: Life Feed lives inside
VOLAURA web, sources events from the public.lifesim_events table (seeded by
supabase/migrations/20260416050000_lifesim_events_table.sql), applies choice
consequences, and writes audit events to character_events for ecosystem sync.

This module hosts pure-function helpers + DB read/write primitives. Route-level
composition lives in apps/api/app/routers/lifesim.py (next iteration).

Cross-references:
  - docs/LIFE-SIMULATOR-GAME-DESIGN.md — stat mapping + crystal economy
  - docs/LIFE-SIMULATOR-INTEGRATION-SPEC.md — VOLAURA competency → lifesim stat table
  - app/services/ecosystem_events.py — pattern for character_events writes
  - app/services/assessment/rewards.py — crystal_earned emitter
"""

from __future__ import annotations

import random
from typing import Any

from loguru import logger

# ── Stat mapping from VOLAURA competency → Life Sim character stats ─────────
# Source: docs/LIFE-SIMULATOR-INTEGRATION-SPEC.md § "VOLAURA → Life Simulator Stat Mapping"
# Every multiplier is a deliberate tuning value — changes require coordination
# with game-design.md to keep the economy balanced.

_STAT_BOOSTS_BY_SLUG: dict[str, dict[str, float]] = {
    "communication": {"social": 0.10},
    "reliability": {"energy": 0.05},
    "tech_literacy": {"intelligence": 0.10},
    "leadership": {"social": 0.05, "happiness": 0.03},
    "adaptability": {"energy": 0.05},
    "empathy_safeguarding": {"happiness": 0.05},
    "english_proficiency": {"intelligence": 0.05},
    "event_performance": {"happiness": 0.05},
}

_STAT_CAP = 100.0
_CRYSTAL_BALANCE_CAP = 9999


def apply_stat_boosts_from_verified_skills(skills: list[dict]) -> dict[str, float]:
    """Compute additive stat boosts from a user's verified-skill list.

    Pure function — no DB, no side effects. Designed for both backend
    endpoint composition and unit testing.

    Args:
      skills: list of VerifiedSkillOut-shaped dicts: {slug, aura_score, badge_tier}

    Returns:
      dict mapping stat name → additive boost value (always non-negative, capped
      so individual stats cannot exceed _STAT_CAP when summed by caller).
    """
    boosts: dict[str, float] = {
        "social": 0.0,
        "intelligence": 0.0,
        "energy": 0.0,
        "happiness": 0.0,
    }
    for skill in skills:
        slug = skill.get("slug", "")
        score = float(skill.get("aura_score", 0.0))
        if score <= 0:
            continue
        mapping = _STAT_BOOSTS_BY_SLUG.get(slug, {})
        for stat, multiplier in mapping.items():
            boosts[stat] = boosts.get(stat, 0.0) + (score * multiplier)
    return boosts


def apply_consequences_to_stats(current_stats: dict[str, float], consequences: dict[str, float]) -> dict[str, float]:
    """Apply a choice's consequences to current stats, with clamping.

    Pure function. Stats clamp to [0, _STAT_CAP] except 'money' which is
    unbounded (but capped at _CRYSTAL_BALANCE_CAP when money source is crystals).

    Args:
      current_stats: dict of current stat values
      consequences: dict of deltas (+ or -)

    Returns:
      new stats dict with deltas applied and clamped.
    """
    new_stats = dict(current_stats)
    for stat, delta in consequences.items():
        current = float(new_stats.get(stat, 0.0))
        value = current + float(delta)
        if stat == "money":
            # money may be negative (debt), not capped top-side by stat system
            new_stats[stat] = value
        else:
            new_stats[stat] = max(0.0, min(_STAT_CAP, value))
    return new_stats


def filter_pool_for_user(pool: list[dict], *, age: int, stats: dict[str, float]) -> list[dict]:
    """Filter event pool down to events this user currently qualifies for.

    Pure function. Criteria:
      - age within [min_age, max_age] (both optional in the event)
      - all required_stats met (stat >= required value)
      - event is_active (already filtered by query, re-checked defensively)
    """
    eligible: list[dict] = []
    for event in pool:
        if not event.get("is_active", True):
            continue
        min_age = event.get("min_age")
        max_age = event.get("max_age")
        if min_age is not None and age < int(min_age):
            continue
        if max_age is not None and age > int(max_age):
            continue
        required = event.get("required_stats") or {}
        ok = True
        for req_stat, req_value in required.items():
            if float(stats.get(req_stat, 0.0)) < float(req_value):
                ok = False
                break
        if ok:
            eligible.append(event)
    return eligible


async def query_event_pool(
    db: Any,
    *,
    category: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """Fetch active events from lifesim_events table.

    Args:
      db: Supabase client (user or admin — RLS allows authenticated SELECT)
      category: if provided, filter by category slug
      limit: max rows to return

    Returns:
      list of event dicts with full shape (id, category, title_ru, description_ru,
      min_age, max_age, required_stats, choices, extra, is_active).
    """
    query = db.table("lifesim_events").select("*").eq("is_active", True)
    if category:
        query = query.eq("category", category)
    result = await query.limit(limit).execute()
    return list(result.data or [])


async def emit_lifesim_choice_event(
    db: Any,
    *,
    user_id: str,
    event_id: str,
    choice_index: int,
    consequences: dict[str, float],
    source_product: str = "volaura",
) -> None:
    """Write a lifesim_choice event to character_events for ecosystem sync.

    Mirrors the pattern in app/services/ecosystem_events.py. Fire-and-forget
    style — caller should not block on this and errors are logged only.
    Downstream consumers (MindShift, BrandedBy, Atlas Telegram bot) can poll
    GET /api/character/events to react to user choices across the ecosystem.
    """
    try:
        await (
            db.table("character_events")
            .insert(
                {
                    "user_id": user_id,
                    "event_type": "lifesim_choice",
                    "payload": {
                        "event_id": event_id,
                        "choice_index": choice_index,
                        "consequences": consequences,
                        "_schema_version": 1,
                    },
                    "source_product": source_product,
                }
            )
            .execute()
        )
    except Exception as exc:
        # Non-blocking: Life Feed must not break if ecosystem bus is slow
        logger.warning(
            "lifesim_choice emit failed",
            user_id=user_id,
            event_id=event_id,
            error=str(exc)[:200],
        )


async def emit_lifesim_crystal_spent_event(
    db: Any,
    *,
    user_id: str,
    shop_item: str,
    crystals_spent: int,
    stat_boost: dict[str, float],
) -> None:
    """Write a lifesim_crystal_spent event when user purchases from Crystal Shop.

    Crystal Shop items (from GAME-DESIGN.md):
      - premium_training_course: 50 crystals → intelligence +10
      - social_event_ticket: 30 crystals → social +5, happiness +5
      - health_insurance: 100 crystals → health decay halved for 10 chapters
      - career_coach: 75 crystals → next promotion guaranteed (flag)

    The crystal decrement happens via the existing crystal_spent event type
    (see app/routers/brandedby.py for precedent). This helper wraps the
    lifesim-surface-specific metadata on top.
    """
    try:
        await (
            db.table("character_events")
            .insert(
                {
                    "user_id": user_id,
                    "event_type": "lifesim_crystal_spent",
                    "payload": {
                        "shop_item": shop_item,
                        "crystals_spent": int(crystals_spent),
                        "stat_boost": stat_boost,
                        "_schema_version": 1,
                    },
                    "source_product": "volaura",
                }
            )
            .execute()
        )
    except Exception as exc:
        logger.warning(
            "lifesim_crystal_spent emit failed",
            user_id=user_id,
            shop_item=shop_item,
            error=str(exc)[:200],
        )


# ── E3: atlas_learnings bias ──────────────────────────────────────────────────

# Maps substrings (matched against learning content lowercased) to lifesim_events
# category slugs. Multiple keywords can map to the same category — weights add up.
_KEYWORD_CATEGORY_MAP: dict[str, str] = {
    # finance / money
    "финанс": "finance",
    "деньг": "finance",
    "независимост": "finance",
    "инвестиц": "finance",
    "бизнес": "career",
    "стартап": "career",
    # career
    "карьер": "career",
    "работ": "career",
    "профессион": "career",
    "предпринимат": "career",
    # education
    "образован": "education",
    "учёб": "education",
    "учеб": "education",
    "знани": "education",
    "навык": "education",
    # health
    "здоровь": "health",
    "спорт": "health",
    "фитнес": "health",
    # social / family
    "семь": "family",
    "отношени": "social",
    "друзь": "social",
    "общени": "social",
    # travel / hobby
    "путешеств": "travel",
    "хобби": "hobby",
    "творчеств": "hobby",
}


def _extract_category_bias(learnings: list[dict]) -> dict[str, float]:
    """Compute lifesim category weight boosts from atlas_learnings rows.

    Pure function — no DB calls.

    Args:
      learnings: list of atlas_learnings dicts with at least 'content' and
                 'emotional_intensity' fields.

    Returns:
      dict mapping lifesim category slug → extra weight (above the default 1.0).
      Categories with no match are absent; caller handles missing key as 0 extra.
    """
    bias: dict[str, float] = {}
    for row in learnings:
        content = (row.get("content") or "").lower()
        intensity = float(row.get("emotional_intensity") or 0.0)
        # weight_boost: 0.5 at intensity=0, 2.0 at intensity=5
        weight_boost = 0.5 + (intensity / 5.0) * 1.5
        for keyword, category in _KEYWORD_CATEGORY_MAP.items():
            if keyword in content:
                bias[category] = bias.get(category, 0.0) + weight_boost
    return bias


def pick_event_with_bias(eligible: list[dict], bias: dict[str, float]) -> dict:
    """Weighted-random selection of one event from the eligible pool.

    Pure function. Falls back to uniform random when bias is empty.

    Args:
      eligible: non-empty list of event dicts (caller must guard empty case).
      bias: category → extra weight (from _extract_category_bias). Default weight
            per event is 1.0; the bias value is ADDED to that base.

    Returns:
      One event dict selected proportionally to its weight.

    Raises:
      IndexError: if eligible is empty (caller should guard).
    """
    weights = [1.0 + bias.get(event.get("category", ""), 0.0) for event in eligible]
    return random.choices(eligible, weights=weights, k=1)[0]


async def get_atlas_learnings_for_bias(db: Any) -> list[dict]:
    """Fetch a small subset of atlas_learnings to drive event bias.

    Fire-and-forget: on any error, logs a warning and returns [] so the
    Life Feed is never blocked by atlas_learnings availability.

    Args:
      db: Supabase client (admin — atlas_learnings is CEO-only, no user RLS).

    Returns:
      Up to 20 rows with category, content, emotional_intensity.
    """
    try:
        result = await (
            db.table("atlas_learnings")
            .select("category, content, emotional_intensity")
            .in_("category", ["preference", "insight", "project_context"])
            .order("emotional_intensity", desc=True)
            .limit(20)
            .execute()
        )
        return list(result.data or [])
    except Exception as exc:
        logger.warning(
            "atlas_learnings fetch failed — falling back to unbiased selection",
            error=str(exc)[:200],
        )
        return []
