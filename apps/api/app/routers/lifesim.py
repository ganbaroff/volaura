"""Life Simulator Life Feed — MVP endpoints (Path C from reimagine doc).

User surface:
 • GET  /api/lifesim/feed         — recent lifesim events for timeline
 • GET  /api/lifesim/next-choice  — pick one eligible event from the pool
 • POST /api/lifesim/choice       — apply choice consequences + log
 • POST /api/lifesim/purchase     — spend crystals on a shop item

Reads pool from `lifesim_events` table (seeded by
supabase/migrations/20260416050000_lifesim_events_table.sql).

Writes audit + cross-product events to `character_events` so MindShift,
BrandedBy, and Atlas Telegram can react (ecosystem bus — ADR-006).

Service composition: see app/services/lifesim.py for pure logic + DB helpers.
"""

from __future__ import annotations

import random

from fastapi import APIRouter, HTTPException, Query, Request
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field

from app.deps import CurrentUserId, SupabaseAdmin
from app.middleware.rate_limit import RATE_DEFAULT, RATE_PROFILE_WRITE, limiter
from app.services.lifesim import (
    apply_consequences_to_stats,
    emit_lifesim_choice_event,
    emit_lifesim_crystal_spent_event,
    filter_pool_for_user,
    query_event_pool,
)

router = APIRouter(prefix="/lifesim", tags=["LifeSim"])

# ── Crystal Shop catalogue (from LIFE-SIMULATOR-GAME-DESIGN.md § Crystal Economy) ──
# Hardcoded in code for MVP. Future iteration: move to lifesim_shop_items table
# so game designers can adjust pricing without migration.
_CRYSTAL_SHOP: dict[str, dict] = {
    "premium_training_course": {"cost": 50, "boost": {"intelligence": 10.0}},
    "social_event_ticket": {"cost": 30, "boost": {"social": 5.0, "happiness": 5.0}},
    "health_insurance": {"cost": 100, "boost": {"health": 10.0}},
    "career_coach": {"cost": 75, "boost": {"career_bonus_flag": 1.0}},
}

_FEED_DEFAULT_LIMIT = 50
_FEED_MAX_LIMIT = 200


# ── Schemas ────────────────────────────────────────────────────────────────


class ChoicePayload(BaseModel):
    event_id: str = Field(..., min_length=1, max_length=64)
    choice_index: int = Field(..., ge=0, le=9)
    stats_before: dict[str, float] = Field(default_factory=dict)


class ChoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: str
    choice_index: int
    consequences: dict
    stats_after: dict[str, float]


class PurchasePayload(BaseModel):
    shop_item: str = Field(..., min_length=1, max_length=64)
    current_crystals: int = Field(..., ge=0)


class PurchaseResponse(BaseModel):
    shop_item: str
    cost: int
    remaining_crystals: int
    stat_boost: dict[str, float]


class FeedItem(BaseModel):
    id: str
    event_type: str
    payload: dict
    created_at: str


class FeedResponse(BaseModel):
    data: list[FeedItem]


class NextChoiceResponse(BaseModel):
    event: dict | None
    pool_size: int


# ── Endpoints ──────────────────────────────────────────────────────────────


@router.get("/feed", response_model=FeedResponse)
@limiter.limit(RATE_DEFAULT)
async def get_feed(
    request: Request,
    user_id: CurrentUserId,
    db: SupabaseAdmin,
    limit: int = Query(default=_FEED_DEFAULT_LIMIT, ge=1, le=_FEED_MAX_LIMIT),
) -> FeedResponse:
    """Return recent lifesim events for the user — timeline rendering input.

    Filters to lifesim_* event types (choice + crystal_spent) from
    character_events so the client gets a clean Life Feed without all
    other ecosystem noise.
    """
    result = await (
        db.table("character_events")
        .select("id, event_type, payload, created_at")
        .eq("user_id", str(user_id))
        .in_("event_type", ["lifesim_choice", "lifesim_crystal_spent"])
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    rows = result.data or []
    return FeedResponse(data=[FeedItem(**row) for row in rows])


@router.get("/next-choice", response_model=NextChoiceResponse)
@limiter.limit(RATE_DEFAULT)
async def get_next_choice(
    request: Request,
    user_id: CurrentUserId,
    db: SupabaseAdmin,
    age: int = Query(..., ge=6, le=100, description="Character age for pool filter"),
    category: str | None = Query(default=None, max_length=32),
    intelligence: float = Query(default=50, ge=0, le=100),
    social: float = Query(default=50, ge=0, le=100),
    energy: float = Query(default=50, ge=0, le=100),
    happiness: float = Query(default=50, ge=0, le=100),
    health: float = Query(default=50, ge=0, le=100),
    money: float = Query(default=0, description="Unbounded — may be negative for debt"),
    work_experience: float = Query(default=0, ge=0, le=100),
) -> NextChoiceResponse:
    """Pick one eligible event from the pool for presentation.

    Age + stats come from query params — frontend maintains session state
    between chapters. Future iteration: aggregate from character_events
    server-side to remove client-side truth dependence.

    Returns None event if the pool yielded no eligible row; client should
    show an empty-chapter state in that case.
    """
    stats = {
        "intelligence": intelligence,
        "social": social,
        "energy": energy,
        "happiness": happiness,
        "health": health,
        "money": money,
        "work_experience": work_experience,
    }
    pool = await query_event_pool(db, category=category, limit=_FEED_MAX_LIMIT)
    eligible = filter_pool_for_user(pool, age=age, stats=stats)
    if not eligible:
        return NextChoiceResponse(event=None, pool_size=0)
    picked = random.choice(eligible)
    return NextChoiceResponse(event=picked, pool_size=len(eligible))


@router.post("/choice", response_model=ChoiceResponse, status_code=201)
@limiter.limit(RATE_PROFILE_WRITE)
async def submit_choice(
    request: Request,
    payload: ChoicePayload,
    user_id: CurrentUserId,
    db: SupabaseAdmin,
) -> ChoiceResponse:
    """Apply the chosen choice's consequences and log the event.

    Validates event + choice exist in the pool, computes new stats via
    pure-function helper, then fires the character_events emit (non-blocking).
    """
    result = await (
        db.table("lifesim_events").select("id, choices, is_active").eq("id", payload.event_id).single().execute()
    )
    event = getattr(result, "data", None) or {}
    if not event or not event.get("is_active"):
        raise HTTPException(
            status_code=404,
            detail={"code": "EVENT_NOT_FOUND", "message": "Event not in active pool"},
        )
    choices = event.get("choices") or []
    if payload.choice_index >= len(choices):
        raise HTTPException(
            status_code=422,
            detail={"code": "CHOICE_OUT_OF_RANGE", "message": "choice_index beyond event.choices"},
        )
    consequences = choices[payload.choice_index].get("consequences") or {}
    stats_after = apply_consequences_to_stats(payload.stats_before, consequences)

    await emit_lifesim_choice_event(
        db,
        user_id=str(user_id),
        event_id=payload.event_id,
        choice_index=payload.choice_index,
        consequences=consequences,
    )

    return ChoiceResponse(
        event_id=payload.event_id,
        choice_index=payload.choice_index,
        consequences=consequences,
        stats_after=stats_after,
    )


@router.post("/purchase", response_model=PurchaseResponse, status_code=201)
@limiter.limit(RATE_PROFILE_WRITE)
async def purchase_shop_item(
    request: Request,
    payload: PurchasePayload,
    user_id: CurrentUserId,
    db: SupabaseAdmin,
) -> PurchaseResponse:
    """Spend crystals on a Life Feed Crystal Shop item.

    Validates item + balance, fires a crystal_spent event (for the shared
    crystal ledger) AND a lifesim_crystal_spent event (for Life Feed surface
    context). Client applies stat_boost optimistically; server is the truth.
    """
    item = _CRYSTAL_SHOP.get(payload.shop_item)
    if not item:
        raise HTTPException(
            status_code=404,
            detail={"code": "SHOP_ITEM_NOT_FOUND", "message": "Unknown shop_item"},
        )
    cost = int(item["cost"])
    if payload.current_crystals < cost:
        raise HTTPException(
            status_code=422,
            detail={"code": "INSUFFICIENT_CRYSTALS", "message": f"Need {cost} crystals"},
        )

    # Write the canonical crystal_spent event (shared ledger — same row shape as
    # brandedby.py uses for skip-queue purchases). Reason signals Life Feed context.
    try:
        await (
            db.table("character_events")
            .insert(
                {
                    "user_id": str(user_id),
                    "event_type": "crystal_spent",
                    "payload": {
                        "amount": cost,
                        "reason": "lifesim_shop",
                        "shop_item": payload.shop_item,
                        "_schema_version": 1,
                    },
                    "source_product": "volaura",
                }
            )
            .execute()
        )
    except Exception as exc:
        logger.error(
            "crystal_spent insert failed",
            user_id=str(user_id),
            shop_item=payload.shop_item,
            error=str(exc)[:200],
        )
        raise HTTPException(
            status_code=500,
            detail={"code": "SPEND_FAILED", "message": "Crystal spend could not be recorded"},
        )

    # Fire-and-forget lifesim surface event so the feed can show the purchase card
    await emit_lifesim_crystal_spent_event(
        db,
        user_id=str(user_id),
        shop_item=payload.shop_item,
        crystals_spent=cost,
        stat_boost=item["boost"],
    )

    return PurchaseResponse(
        shop_item=payload.shop_item,
        cost=cost,
        remaining_crystals=payload.current_crystals - cost,
        stat_boost=item["boost"],
    )
