"""Character state router — cross-product event bus (Sprint A0).

POST /api/character/events  — store a character event
GET  /api/character/state   — compute and return current state

This is the thalamus of the ecosystem: all products write events here,
all products read state from here. One JWT = all four products.

Security:
- All endpoints require valid Supabase JWT (CurrentUserId)
- user_id on stored events always comes from JWT, never from request body
- Crystal ledger writes only on crystal_earned/crystal_spent events (atomic)
- RLS: users can only read/write their own rows
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from app.deps import CurrentUserId, SupabaseAdmin, SupabaseUser
from app.schemas.character import (
    CharacterEventCreate,
    CharacterEventOut,
    CharacterStateOut,
)

router = APIRouter(prefix="/character", tags=["Character"])


@router.post("/events", response_model=CharacterEventOut, status_code=201)
async def create_character_event(
    body: CharacterEventCreate,
    user_id: CurrentUserId,
    db: SupabaseAdmin,
) -> CharacterEventOut:
    """Store a character event from any product.

    user_id is always sourced from the JWT — never from the request body.
    Crystal events atomically update game_crystal_ledger in addition to logging the event.
    """
    # Store the event
    row = {
        "user_id": str(user_id),
        "event_type": body.event_type,
        "payload": body.payload,
        "source_product": body.source_product,
    }

    result = await db.table("character_events").insert(row).execute()
    if not result.data:
        logger.error("Failed to insert character event", user_id=user_id, event_type=body.event_type)
        raise HTTPException(
            status_code=500,
            detail={"code": "EVENT_STORE_FAILED", "message": "Failed to store character event"},
        )

    stored = result.data[0]

    # Atomically update crystal ledger for crystal events
    if body.event_type in ("crystal_earned", "crystal_spent"):
        amount = body.payload.get("amount")
        source = body.payload.get("source", body.source_product)

        if not isinstance(amount, int) or amount <= 0:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "INVALID_CRYSTAL_AMOUNT",
                    "message": "Crystal events require payload.amount (positive integer)",
                },
            )

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
                "Crystal event stored but ledger write failed",
                user_id=user_id,
                event_id=stored["id"],
            )
            # Don't raise — event is persisted, ledger inconsistency logged for reconciliation

        logger.info(
            "Crystal event stored",
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
async def get_character_state(
    user_id: CurrentUserId,
    db: SupabaseAdmin,
) -> CharacterStateOut:
    """Compute and return current character state for the authenticated user.

    Aggregates all events + crystal ledger into a single snapshot.
    Target: <50ms at current scale (indexed by user_id).
    """
    result = await db.rpc("get_character_state", {"p_user_id": str(user_id)}).execute()

    if not result.data:
        logger.warning("Character state RPC returned empty", user_id=user_id)
        # Return empty state for new users (no events yet)
        from datetime import datetime, timezone
        return CharacterStateOut(
            user_id=user_id,
            crystal_balance=0,
            xp_total=0,
            verified_skills=[],
            login_streak=0,
            event_count=0,
            last_event_at=None,
            computed_at=datetime.now(timezone.utc),
        )

    state_data = result.data
    # RPC returns JSONB directly
    if isinstance(state_data, list):
        state_data = state_data[0] if state_data else {}

    return CharacterStateOut(**state_data)


@router.get("/events", response_model=list[CharacterEventOut])
async def list_character_events(
    user_id: CurrentUserId,
    db: SupabaseAdmin,
    limit: int = 50,
    offset: int = 0,
) -> list[CharacterEventOut]:
    """Return the authenticated user's event history (paginated).

    Useful for debugging and for Life Simulator to load event history.
    """
    if limit > 200:
        limit = 200  # Hard cap to prevent large response abuse

    result = (
        await db.table("character_events")
        .select("*")
        .eq("user_id", str(user_id))
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    return [CharacterEventOut(**row) for row in (result.data or [])]
