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

from uuid import uuid4

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


async def _get_atlas_note_for_user(user_id: str, db: SupabaseAdmin) -> str | None:
    """E5 concept seed: read top atlas_learning and compose a 1-sentence memory anchor.

    Fire-and-forget: caller wraps in try/except so failure never blocks the generation.
    Full LLM-composed twin briefing deferred to E7 sprint.
    """
    result = (
        await db.table("atlas_learnings")
        .select("content, category")
        .eq("user_id", user_id)
        .order("emotional_intensity", desc=True)
        .limit(1)
        .execute()
    )
    if not result.data:
        return None
    row = result.data[0]
    content: str = (row.get("content") or "").strip()
    category: str = (row.get("category") or "insight").replace("_", " ")
    if not content:
        return None
    # Trim long content to keep the note concise
    snippet = content[:120] + ("…" if len(content) > 120 else "")
    return f"Atlas {category}: {snippet}"


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
    existing = await db.table("brandedby_ai_twins").select("id").eq("user_id", user_id).execute()
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
    result = await db.table("brandedby_ai_twins").insert(row).execute()

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
    result = await db.table("brandedby_ai_twins").select("*").eq("user_id", user_id).maybe_single().execute()
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
        await db.table("brandedby_ai_twins").select("id, user_id").eq("id", twin_id).maybe_single().execute()
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

    result = await db.table("brandedby_ai_twins").update(updates).eq("id", twin_id).execute()

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
        await db.table("brandedby_ai_twins")
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
        await db.table("brandedby_ai_twins")
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
        await db.table("brandedby_ai_twins")
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

    result = await db.table("brandedby_ai_twins").update({"status": "active"}).eq("id", twin_id).execute()

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
        await db.table("brandedby_ai_twins")
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
        # P0-3 FIX (MED-08): Atomic crystal deduction via advisory-lock RPC.
        # Old pattern: SELECT balance → check → INSERT (2 async calls = TOCTOU race).
        # New pattern: deduct_crystals_atomic acquires pg_advisory_lock, checks balance,
        # and inserts into game_crystal_ledger atomically — no race window.
        # reference_id = uuid4() makes each HTTP request unique; advisory lock prevents
        # concurrent-request double-spend from the same user (multiple tabs).
        reference_id = str(uuid4())
        try:
            deduction = await db.rpc(
                "deduct_crystals_atomic",
                {
                    "p_user_id": str(user_id),
                    "p_amount": QUEUE_SKIP_CRYSTAL_COST,
                    "p_source": "brandedby_queue_skip",
                    "p_reference_id": reference_id,
                },
            ).execute()
            row0 = (deduction.data or [{}])[0]
            if not row0.get("success"):
                raise HTTPException(
                    status_code=402,
                    detail={
                        "code": row0.get("error_code", "INSUFFICIENT_CRYSTALS"),
                        "message": row0.get("error_msg", f"Need {QUEUE_SKIP_CRYSTAL_COST} crystals to skip queue"),
                    },
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Crystal deduction RPC failed", user_id=user_id, error=str(e))
            raise HTTPException(
                status_code=500,
                detail={"code": "CRYSTAL_DEDUCTION_FAILED", "message": "Failed to process crystal payment"},
            )

        # Audit trail: character_events records the spend action (game_crystal_ledger is
        # handled by the RPC — do NOT insert manually). Wrap in try/except: crystal already
        # spent, so a failed audit insert must not rollback the deduction.
        try:
            await (
                db.table("character_events")
                .insert(
                    {
                        "user_id": user_id,
                        "event_type": "crystal_spent",
                        "payload": {
                            "_schema_version": 1,
                            "amount": QUEUE_SKIP_CRYSTAL_COST,
                            "reason": "brandedby_queue_skip",
                            "generation_type": body.gen_type,
                            "reference_id": reference_id,
                        },
                        "source_product": "brandedby",
                    }
                )
                .execute()
            )
        except Exception as e:
            logger.error(
                "character_events audit insert failed (crystal already deducted)", user_id=user_id, error=str(e)
            )

        crystal_cost = QUEUE_SKIP_CRYSTAL_COST
        logger.info("Queue skip: crystals deducted atomically", user_id=user_id, cost=crystal_cost)

    # Calculate queue position (0 if skipped, otherwise count of queued jobs ahead)
    queue_position = 0
    if not body.skip_queue:
        queued = (
            await db.table("brandedby_generations")
            .select("id", count="exact")
            .eq("status", "queued")
            .execute()
        )
        queue_position = (queued.count or 0) + 1

    # E5: attach Atlas memory anchor (fire-and-forget — never blocks the generation)
    atlas_note: str | None = None
    try:
        atlas_note = await _get_atlas_note_for_user(user_id, db)
    except Exception as e:
        logger.debug("E5 atlas_note fetch skipped", user_id=user_id, error=str(e))

    row = {
        "twin_id": str(body.twin_id),
        "user_id": user_id,
        "gen_type": body.gen_type,
        "input_text": body.input_text,
        "status": "queued",
        "queue_position": queue_position,
        "crystal_cost": crystal_cost,
        "atlas_note": atlas_note,
    }
    result = await db.table("brandedby_generations").insert(row).execute()

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
        await db.table("brandedby_generations")
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
        await db.table("brandedby_generations")
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
