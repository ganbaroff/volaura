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

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from app.deps import CurrentUserId, SupabaseUser
from app.middleware.rate_limit import RATE_DEFAULT, limiter
from app.schemas.character import (
    DAILY_CRYSTAL_CAP,
    CharacterEventCreate,
    CharacterEventOut,
    CharacterStateOut,
    CrystalBalanceOut,
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
    db: SupabaseUser,
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

    # ── P0-3 FIX: Atomic crystal deduction (advisory lock — no TOCTOU race) ──
    # Old approach: SELECT balance → check → INSERT (2 separate async calls = race).
    # New approach: single RPC acquires pg_advisory_lock, checks, inserts atomically.
    # Ledger INSERT for crystal_spent is done INSIDE the RPC — skip manual insert below.
    _crystal_spent_handled_by_rpc = False
    if body.event_type == "crystal_spent":
        amount = body.payload["amount"]  # already validated above
        deduction = await db.rpc(
            "deduct_crystals_atomic",
            {
                "p_user_id": str(user_id),
                "p_amount": amount,
                "p_source": body.payload.get("source", body.source_product),
                "p_reference_id": body.payload.get("reference_id"),
            },
        ).execute()
        row0 = (deduction.data or [{}])[0]
        if not row0.get("success"):
            raise HTTPException(
                status_code=422,
                detail={
                    "code": row0.get("error_code", "CRYSTAL_DEDUCTION_FAILED"),
                    "message": row0.get("error_msg", "Crystal deduction failed"),
                },
            )
        _crystal_spent_handled_by_rpc = True

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
        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
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

    # ── Update crystal ledger (earned only — spent is handled atomically by RPC) ──
    if body.event_type in ("crystal_earned", "crystal_spent") and not _crystal_spent_handled_by_rpc:
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
            await (
                db.table("game_character_rewards")
                .upsert(
                    {
                        "user_id": str(user_id),
                        "skill_slug": body.payload["skill_slug"],
                        "crystals": amount,
                        "claimed": True,
                        "claimed_at": datetime.now(UTC).isoformat(),
                    }
                )
                .execute()
            )

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
    db: SupabaseUser,
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
            computed_at=datetime.now(UTC),
        )

    state_data = result.data
    if isinstance(state_data, list):
        state_data = state_data[0] if state_data else {}

    return CharacterStateOut(**state_data)


@router.get("/crystals", response_model=CrystalBalanceOut)
@limiter.limit(RATE_DEFAULT)
async def get_crystal_balance(
    request: Request,
    user_id: CurrentUserId,
    db: SupabaseUser,
) -> CrystalBalanceOut:
    """Return crystal balance for the authenticated user.

    Lightweight alternative to GET /state — used by MindShift to show the
    crystal counter in the focus session overlay without the cost of the full
    5-query get_character_state RPC.

    Implementation: single SUM over game_crystal_ledger (indexed on user_id).
    """
    result = await db.table("game_crystal_ledger").select("amount, created_at").eq("user_id", str(user_id)).execute()

    rows = result.data or []
    raw_balance = sum(row["amount"] for row in rows)
    balance = max(0, raw_balance)  # floor at 0 — consistent with CharacterStateOut guarantee
    lifetime_earned = sum(row["amount"] for row in rows if row["amount"] > 0)

    # last_earned_at: most recent row where amount > 0
    earned_rows = [row for row in rows if row["amount"] > 0]
    last_earned_at: datetime | None = None
    if earned_rows:
        latest = max(earned_rows, key=lambda r: r["created_at"])
        last_earned_at = datetime.fromisoformat(latest["created_at"].replace("Z", "+00:00"))

    logger.info("Crystal balance fetched", user_id=user_id, balance=balance)

    return CrystalBalanceOut(
        user_id=user_id,
        crystal_balance=balance,
        last_earned_at=last_earned_at,
        lifetime_earned=lifetime_earned,
        computed_at=datetime.now(UTC),
    )


@router.get("/events", response_model=list[CharacterEventOut])
@limiter.limit(RATE_DEFAULT)
async def list_character_events(
    request: Request,
    user_id: CurrentUserId,
    db: SupabaseUser,
    limit: int = 50,
    offset: int = 0,
    since: str | None = None,
) -> list[CharacterEventOut]:
    """Return the authenticated user's event history (paginated, newest first).

    Params:
      limit  — hard cap 200 rows per request.
      offset — page offset (used with limit for history scroll).
      since  — ISO 8601 timestamp. If set, returns ONLY events created after
               this instant (newest first within the slice). Designed for
               incremental polling from another product (Life Sim, MindShift,
               BrandedBy) — they store the latest `created_at` they saw and
               pass it as `since=` on the next poll.
    """
    if limit > 200:
        limit = 200

    query = db.table("character_events").select("*").eq("user_id", str(user_id)).order("created_at", desc=True)

    if since:
        try:
            cutoff = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "INVALID_SINCE",
                    "message": "`since` must be an ISO 8601 timestamp (e.g. 2026-04-14T12:00:00Z)",
                },
            )
        query = query.gt("created_at", cutoff.isoformat())

    result = await query.range(offset, offset + limit - 1).execute()

    return [CharacterEventOut(**row) for row in (result.data or [])]
