"""BrandedBy router — AI Twin CRUD + generation jobs (Sprint B1+B2).

POST /api/brandedby/twins                        — create user's AI Twin
GET  /api/brandedby/twins                        — get user's AI Twin
PATCH /api/brandedby/twins/{id}                  — update AI Twin
POST /api/brandedby/twins/{id}/refresh-personality — regenerate personality from character_state
POST /api/brandedby/twins/{id}/activate          — activate twin (draft → active)
POST /api/brandedby/generations                  — request a generation (video/audio/chat)
GET  /api/brandedby/generations                  — list user's generations
GET  /api/brandedby/generations/{id}             — get single generation

Security:
- All endpoints require valid Supabase JWT (CurrentUserId)
- user_id always from JWT, never from request body
- One AI Twin per user (MVP)
- RLS enforced at DB level
- Queue skip costs crystals (checked via character_events ledger)
"""

from fastapi import APIRouter, HTTPException, Query, Request
from loguru import logger

from app.deps import CurrentUserId, SupabaseAdmin
from app.middleware.rate_limit import RATE_DEFAULT, limiter
from app.schemas.brandedby import (
    AITwinCreate,
    AITwinOut,
    AITwinUpdate,
    GenerationCreate,
    GenerationOut,
)
from app.services.brandedby_personality import generate_twin_personality

router = APIRouter(prefix="/brandedby", tags=["BrandedBy"])

QUEUE_SKIP_CRYSTAL_COST = 25  # crystals to skip generation queue


# ── AI Twin CRUD ──────────────────────────────────────────────


@router.post("/twins", response_model=AITwinOut, status_code=201)
@limiter.limit(RATE_DEFAULT)
async def create_twin(
    request: Request,
    body: AITwinCreate,
    user_id: CurrentUserId,
    db: SupabaseAdmin,
) -> AITwinOut:
    """Create the user's AI Twin. One per user (MVP)."""
    # Check if user already has a twin
    existing = (
        await db.schema("brandedby")
        .table("ai_twins")
        .select("id")
        .eq("user_id", user_id)
        .execute()
    )
    if existing.data:
        raise HTTPException(
            status_code=409,
            detail={"code": "TWIN_EXISTS", "message": "You already have an AI Twin"},
        )

    row = {
        "user_id": user_id,
        "display_name": body.display_name,
        "tagline": body.tagline,
        "photo_url": body.photo_url,
        "status": "draft",
    }
    result = await db.schema("brandedby").table("ai_twins").insert(row).execute()

    if not result.data:
        logger.error("Failed to create AI Twin", user_id=user_id)
        raise HTTPException(
            status_code=500,
            detail={"code": "CREATE_FAILED", "message": "Failed to create AI Twin"},
        )

    logger.info("AI Twin created", user_id=user_id, twin_id=result.data[0]["id"])
    return AITwinOut(**result.data[0])


@router.get("/twins", response_model=AITwinOut | None)
@limiter.limit(RATE_DEFAULT)
async def get_my_twin(
    request: Request,
    user_id: CurrentUserId,
    db: SupabaseAdmin,
) -> AITwinOut | None:
    """Get the current user's AI Twin (or null if none)."""
    result = (
        await db.schema("brandedby")
        .table("ai_twins")
        .select("*")
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    if not result.data:
        return None
    return AITwinOut(**result.data)


@router.patch("/twins/{twin_id}", response_model=AITwinOut)
@limiter.limit(RATE_DEFAULT)
async def update_twin(
    request: Request,
    twin_id: str,
    body: AITwinUpdate,
    user_id: CurrentUserId,
    db: SupabaseAdmin,
) -> AITwinOut:
    """Update the user's AI Twin. Only owner can update."""
    # Verify ownership
    existing = (
        await db.schema("brandedby")
        .table("ai_twins")
        .select("id, user_id")
        .eq("id", twin_id)
        .maybe_single()
        .execute()
    )
    if not existing.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "TWIN_NOT_FOUND", "message": "AI Twin not found"},
        )
    if existing.data["user_id"] != user_id:
        raise HTTPException(
            status_code=403,
            detail={"code": "NOT_OWNER", "message": "You can only update your own AI Twin"},
        )

    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=400,
            detail={"code": "NO_CHANGES", "message": "No fields to update"},
        )

    result = (
        await db.schema("brandedby")
        .table("ai_twins")
        .update(updates)
        .eq("id", twin_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=500,
            detail={"code": "UPDATE_FAILED", "message": "Failed to update AI Twin"},
        )

    logger.info("AI Twin updated", twin_id=twin_id, fields=list(updates.keys()))
    return AITwinOut(**result.data[0])


@router.post("/twins/{twin_id}/refresh-personality", response_model=AITwinOut)
@limiter.limit("5/minute")
async def refresh_personality(
    request: Request,
    twin_id: str,
    user_id: CurrentUserId,
    db: SupabaseAdmin,
) -> AITwinOut:
    """Regenerate AI Twin personality from current character_state.

    Reads verified skills, AURA scores, XP from character_events → generates
    a personality prompt via Gemini → stores in ai_twins.personality_prompt.

    This is BrandedBy's core moat: verified data → intelligent persona.
    """
    # Verify ownership + get display_name
    twin = (
        await db.schema("brandedby")
        .table("ai_twins")
        .select("id, user_id, display_name")
        .eq("id", twin_id)
        .maybe_single()
        .execute()
    )
    if not twin.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "TWIN_NOT_FOUND", "message": "AI Twin not found"},
        )
    if twin.data["user_id"] != user_id:
        raise HTTPException(
            status_code=403,
            detail={"code": "NOT_OWNER", "message": "You can only update your own AI Twin"},
        )

    # Get character_state
    state_result = await db.rpc("get_character_state", {"p_user_id": user_id}).execute()
    state_data = {}
    if state_result.data:
        raw = state_result.data
        state_data = raw[0] if isinstance(raw, list) else raw

    # Generate personality
    personality = await generate_twin_personality(
        display_name=twin.data["display_name"],
        character_state=state_data,
    )

    # Store in twin record
    result = (
        await db.schema("brandedby")
        .table("ai_twins")
        .update({"personality_prompt": personality})
        .eq("id", twin_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=500,
            detail={"code": "UPDATE_FAILED", "message": "Failed to store personality"},
        )

    logger.info(
        "AI Twin personality refreshed",
        twin_id=twin_id,
        user_id=user_id,
        skill_count=len(state_data.get("verified_skills", [])),
    )
    return AITwinOut(**result.data[0])


@router.post("/twins/{twin_id}/activate", response_model=AITwinOut)
@limiter.limit(RATE_DEFAULT)
async def activate_twin(
    request: Request,
    twin_id: str,
    user_id: CurrentUserId,
    db: SupabaseAdmin,
) -> AITwinOut:
    """Activate the AI Twin (draft → active). Requires a photo and personality_prompt.

    Once active, the twin can accept generation requests.
    """
    twin = (
        await db.schema("brandedby")
        .table("ai_twins")
        .select("id, user_id, status, photo_url, personality_prompt")
        .eq("id", twin_id)
        .maybe_single()
        .execute()
    )
    if not twin.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "TWIN_NOT_FOUND", "message": "AI Twin not found"},
        )
    if twin.data["user_id"] != user_id:
        raise HTTPException(
            status_code=403,
            detail={"code": "NOT_OWNER", "message": "You can only activate your own AI Twin"},
        )
    if twin.data["status"] == "active":
        raise HTTPException(
            status_code=409,
            detail={"code": "ALREADY_ACTIVE", "message": "AI Twin is already active"},
        )
    if not twin.data.get("photo_url"):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "MISSING_PHOTO",
                "message": "Upload a portrait photo before activating",
            },
        )
    if not twin.data.get("personality_prompt"):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "MISSING_PERSONALITY",
                "message": "Generate personality first via /refresh-personality",
            },
        )

    result = (
        await db.schema("brandedby")
        .table("ai_twins")
        .update({"status": "active"})
        .eq("id", twin_id)
        .execute()
    )

    logger.info("AI Twin activated", twin_id=twin_id, user_id=user_id)
    return AITwinOut(**result.data[0])


# ── Generation Jobs ───────────────────────────────────────────


@router.post("/generations", response_model=GenerationOut, status_code=201)
@limiter.limit("10/minute")
async def create_generation(
    request: Request,
    body: GenerationCreate,
    user_id: CurrentUserId,
    db: SupabaseAdmin,
) -> GenerationOut:
    """Request a new video/audio/chat generation.

    If skip_queue=true, spends crystals via character_events ledger.
    """
    # Verify twin ownership
    twin = (
        await db.schema("brandedby")
        .table("ai_twins")
        .select("id, user_id, status")
        .eq("id", str(body.twin_id))
        .maybe_single()
        .execute()
    )
    if not twin.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "TWIN_NOT_FOUND", "message": "AI Twin not found"},
        )
    if twin.data["user_id"] != user_id:
        raise HTTPException(
            status_code=403,
            detail={"code": "NOT_OWNER", "message": "You can only generate for your own AI Twin"},
        )
    if twin.data["status"] != "active":
        raise HTTPException(
            status_code=400,
            detail={
                "code": "TWIN_NOT_ACTIVE",
                "message": "AI Twin must be active to generate content",
            },
        )

    crystal_cost = 0
    if body.skip_queue:
        # SECURITY NOTE (MED-08 / TOCTOU): The balance check and deduction below
        # are NOT atomic. A concurrent request could pass the balance check before
        # the deduction is committed, resulting in a crystal double-spend.
        # Proper fix: use a PostgreSQL RPC function that performs
        # SELECT ... FOR UPDATE on game_crystal_ledger rows for this user_id,
        # then checks balance and inserts the deduction atomically inside a
        # single transaction. Until that RPC exists, this race window remains
        # open under concurrent requests from the same user.

        # Check crystal balance via character_state RPC
        state = await db.rpc(
            "get_character_state", {"p_user_id": user_id}
        ).execute()
        balance = state.data[0]["crystal_balance"] if state.data else 0

        if balance < QUEUE_SKIP_CRYSTAL_COST:
            raise HTTPException(
                status_code=402,
                detail={
                    "code": "INSUFFICIENT_CRYSTALS",
                    "message": f"Need {QUEUE_SKIP_CRYSTAL_COST} crystals, have {balance}",
                },
            )

        # Deduct crystals via character event
        await db.table("character_events").insert({
            "user_id": user_id,
            "event_type": "crystal_spent",
            "payload": {
                "_schema_version": 1,
                "amount": QUEUE_SKIP_CRYSTAL_COST,
                "reason": "brandedby_queue_skip",
                "generation_type": body.gen_type,
            },
            "source_product": "brandedby",
        }).execute()

        # Double-entry ledger
        await db.table("game_crystal_ledger").insert({
            "user_id": user_id,
            "amount": -QUEUE_SKIP_CRYSTAL_COST,
            "source": "brandedby_queue_skip",
        }).execute()

        crystal_cost = QUEUE_SKIP_CRYSTAL_COST
        logger.info("Queue skip: crystals deducted", user_id=user_id, cost=crystal_cost)

    # Calculate queue position (0 if skipped, otherwise count of queued jobs ahead)
    queue_position = 0
    if not body.skip_queue:
        queued = (
            await db.schema("brandedby")
            .table("generations")
            .select("id", count="exact")
            .eq("status", "queued")
            .execute()
        )
        queue_position = (queued.count or 0) + 1

    row = {
        "twin_id": str(body.twin_id),
        "user_id": user_id,
        "gen_type": body.gen_type,
        "input_text": body.input_text,
        "status": "queued",
        "queue_position": queue_position,
        "crystal_cost": crystal_cost,
    }
    result = await db.schema("brandedby").table("generations").insert(row).execute()

    if not result.data:
        logger.error("Failed to create generation", user_id=user_id)
        raise HTTPException(
            status_code=500,
            detail={"code": "CREATE_FAILED", "message": "Failed to create generation job"},
        )

    logger.info(
        "Generation created",
        user_id=user_id,
        gen_id=result.data[0]["id"],
        gen_type=body.gen_type,
        queue_position=queue_position,
    )
    return GenerationOut(**result.data[0])


@router.get("/generations", response_model=list[GenerationOut])
@limiter.limit(RATE_DEFAULT)
async def list_generations(
    request: Request,
    user_id: CurrentUserId,
    db: SupabaseAdmin,
    limit: int = Query(20, le=100, ge=1),
    offset: int = Query(0, ge=0),
) -> list[GenerationOut]:
    """List the current user's generation jobs (newest first)."""
    result = (
        await db.schema("brandedby")
        .table("generations")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return [GenerationOut(**row) for row in (result.data or [])]


@router.get("/generations/{gen_id}", response_model=GenerationOut)
@limiter.limit(RATE_DEFAULT)
async def get_generation(
    request: Request,
    gen_id: str,
    user_id: CurrentUserId,
    db: SupabaseAdmin,
) -> GenerationOut:
    """Get a single generation job by ID."""
    result = (
        await db.schema("brandedby")
        .table("generations")
        .select("*")
        .eq("id", gen_id)
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "GENERATION_NOT_FOUND", "message": "Generation not found"},
        )
    return GenerationOut(**result.data)
