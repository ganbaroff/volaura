"""Character state router — cross-product event bus (Sprint A0).

POST /api/character/events  — store a character event
GET  /api/character/state   — compute and return current state
GET  /api/character/events  — paginated event history

This is the thalamus of the ecosystem: all products write events here,
all products read state from here. One JWT = all four products.

Security:
- All endpoints require valid Supabase JWT (CurrentUserId)
- user_id on stored events always comes from JWT, never from request body
- Crystal ledger writes only on crystal_earned/crystal_spent events
- Balance checked before crystal_spent — cannot go negative
- Idempotency enforced via game_character_rewards for volaura_assessment source
- Daily cap enforced per source (daily_login: 15 crystals/day)
- RLS on all three tables (user-scoped reads)
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from app.deps import CurrentUserId, SupabaseAdmin
from app.middleware.rate_limit import RATE_DEFAULT, limiter
from app.schemas.character import (
    DAILY_CRYSTAL_CAP,
    CharacterEventCreate,
    CharacterEventOut,
    CharacterStateOut,
)

router = APIRouter(prefix="/character", tags=["Character"])

# Crystal events write-rate: tighter than default — prevents rapid-fire spam
RATE_CRYSTAL_WRITE = "30/minute"


@router.post("/events", response_model=CharacterEventOut, status_code=201)
@limiter.limit(RATE_CRYSTAL_WRITE)
async def create_character_event(
    request: Request,
    body: CharacterEventCreate,
    user_id: CurrentUserId,
    db: SupabaseAdmin,
) -> CharacterEventOut:
    """Store a character event from any product.

    user_id is always sourced from the JWT — never from the request body.
    Crystal events validate balance and idempotency BEFORE inserting.
    """
    # ── P0-2 FIX: Validate crystal payload BEFORE any DB write ──────────────
    if body.event_type in ("crystal_earned", "crystal_spent"):
        amount = body.payload.get("amount")
        if not isinstance(amount, int) or amount <= 0:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "INVALID_CRYSTAL_AMOUNT",
                    "message": "Crystal events require payload.amount as a positive integer",
                },
            )

    # ── P0-1 FIX: Balance check before crystal_spent ────────────────────────
    if body.event_type == "crystal_spent":
        balance_result = (
            await db.table("game_crystal_ledger")
            .select("amount")
            .eq("user_id", str(user_id))
            .execute()
        )
        current_balance = sum(row["amount"] for row in (balance_result.data or []))
        amount = body.payload["amount"]  # already validated above
        if current_balance < amount:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "INSUFFICIENT_CRYSTALS",
                    "message": f"Cannot spend {amount} crystals — balance is {current_balance}",
                },
            )

    # ── P0-3 FIX: Idempotency for volaura_assessment crystal rewards ─────────
    if (
        body.event_type == "crystal_earned"
        and body.payload.get("source") == "volaura_assessment"
        and body.payload.get("skill_slug")
    ):
        skill_slug = body.payload["skill_slug"]
        reward_result = (
            await db.table("game_character_rewards")
            .select("claimed")
            .eq("user_id", str(user_id))
            .eq("skill_slug", skill_slug)
            .execute()
        )
        if reward_result.data:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "REWARD_ALREADY_CLAIMED",
                    "message": f"Crystal reward for '{skill_slug}' already claimed",
                },
            )

    # ── P1-6 FIX: Daily cap per source ───────────────────────────────────────
    source = body.payload.get("source", body.source_product)
    if body.event_type == "crystal_earned" and source in DAILY_CRYSTAL_CAP:
        cap = DAILY_CRYSTAL_CAP[source]
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        daily_result = (
            await db.table("game_crystal_ledger")
            .select("amount")
            .eq("user_id", str(user_id))
            .eq("source", source)
            .gte("created_at", today_start.isoformat())
            .execute()
        )
        earned_today = sum(row["amount"] for row in (daily_result.data or []) if row["amount"] > 0)
        if earned_today >= cap:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "DAILY_CRYSTAL_CAP_REACHED",
                    "message": f"Daily limit of {cap} crystals from '{source}' already reached",
                },
            )

    # ── Store the event ───────────────────────────────────────────────────────
    row = {
        "user_id": str(user_id),
        "event_type": body.event_type,
        "payload": body.payload,
        "source_product": body.source_product,
    }

    result = await db.table("character_events").insert(row).execute()
    if not result.data:
        logger.error(
            "Failed to insert character event",
            user_id=user_id,
            event_type=body.event_type,
        )
        raise HTTPException(
            status_code=500,
            detail={"code": "EVENT_STORE_FAILED", "message": "Failed to store character event"},
        )

    stored = result.data[0]

    # ── Update crystal ledger (event already stored — log inconsistency if fails) ──
    if body.event_type in ("crystal_earned", "crystal_spent"):
        amount = body.payload["amount"]
        ledger_amount = amount if body.event_type == "crystal_earned" else -amount
        ledger_row = {
            "user_id": str(user_id),
            "amount": ledger_amount,
            "source": source,
            "reference_id": body.payload.get("reference_id"),
        }
        ledger_result = await db.table("game_crystal_ledger").insert(ledger_row).execute()
        if not ledger_result.data:
            logger.error(
                "Crystal event stored but ledger write failed — requires manual reconciliation",
                user_id=user_id,
                event_id=stored["id"],
                amount=ledger_amount,
            )

        # Mark reward as claimed for volaura_assessment (idempotency table)
        if (
            body.event_type == "crystal_earned"
            and body.payload.get("source") == "volaura_assessment"
            and body.payload.get("skill_slug")
        ):
            await db.table("game_character_rewards").upsert({
                "user_id": str(user_id),
                "skill_slug": body.payload["skill_slug"],
                "crystals": amount,
                "claimed": True,
                "claimed_at": datetime.now(timezone.utc).isoformat(),
            }).execute()

        logger.info(
            "Crystal ledger updated",
            user_id=user_id,
            event_type=body.event_type,
            amount=ledger_amount,
            source=source,
        )

    logger.info(
        "Character event stored",
        user_id=user_id,
        event_type=body.event_type,
        source_product=body.source_product,
    )

    return CharacterEventOut(**stored)


@router.get("/state", response_model=CharacterStateOut)
@limiter.limit(RATE_DEFAULT)
async def get_character_state(
    request: Request,
    user_id: CurrentUserId,
    db: SupabaseAdmin,
) -> CharacterStateOut:
    """Compute and return current character state for the authenticated user.

    Aggregates events + crystal ledger into a single snapshot via DB function.
    Returns empty state for new users with no events.
    """
    result = await db.rpc("get_character_state", {"p_user_id": str(user_id)}).execute()

    if not result.data:
        logger.warning("Character state RPC returned empty", user_id=user_id)
        return CharacterStateOut(
            user_id=user_id,
            crystal_balance=0,
            xp_total=0,
            verified_skills=[],
            character_stats={},
            login_streak=0,
            event_count=0,
            last_event_at=None,
            computed_at=datetime.now(timezone.utc),
        )

    state_data = result.data
    if isinstance(state_data, list):
        state_data = state_data[0] if state_data else {}

    return CharacterStateOut(**state_data)


@router.get("/events", response_model=list[CharacterEventOut])
@limiter.limit(RATE_DEFAULT)
async def list_character_events(
    request: Request,
    user_id: CurrentUserId,
    db: SupabaseAdmin,
    limit: int = 50,
    offset: int = 0,
) -> list[CharacterEventOut]:
    """Return the authenticated user's event history (paginated, newest first).

    Hard cap: 200 rows per request.
    """
    if limit > 200:
        limit = 200

    result = (
        await db.table("character_events")
        .select("*")
        .eq("user_id", str(user_id))
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    return [CharacterEventOut(**row) for row in (result.data or [])]
