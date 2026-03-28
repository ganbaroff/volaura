"""Profile endpoints."""

import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from app.config import settings
from app.deps import CurrentUserId, SupabaseAdmin, SupabaseUser, get_supabase_admin
from app.middleware.rate_limit import limiter, RATE_PROFILE_WRITE, RATE_DEFAULT
from app.schemas.profile import (
    ProfileCreate,
    ProfileResponse,
    ProfileUpdate,
    PublicProfileResponse,
)
from app.schemas.verification import (
    CreateVerificationLinkRequest,
    CreateVerificationLinkResponse,
)
from app.services.embeddings import upsert_volunteer_embedding

router = APIRouter(prefix="/profiles", tags=["Profiles"])


@router.get("/me", response_model=ProfileResponse)
@limiter.limit(RATE_DEFAULT)
async def get_my_profile(
    request: Request,
    db: SupabaseUser,
    user_id: CurrentUserId,
) -> ProfileResponse:
    """Get the current authenticated user's profile."""
    # maybe_single() returns None instead of throwing APIError 406 when no row exists.
    # Same fix as auth.py — .single() crashes for new users who haven't completed onboarding.
    result = (
        await db.table("profiles")
        .select("*")
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Profile not found"},
        )
    return ProfileResponse(**result.data)


@router.post("/me", response_model=ProfileResponse, status_code=201)
@limiter.limit(RATE_PROFILE_WRITE)
async def create_my_profile(
    request: Request,
    payload: ProfileCreate,
    db: SupabaseUser,
    user_id: CurrentUserId,
) -> ProfileResponse:
    """Create a profile for the current user (called after registration)."""
    # Check username not taken
    existing = (
        await db.table("profiles")
        .select("id")
        .eq("username", payload.username)
        .execute()
    )
    if existing.data:
        raise HTTPException(
            status_code=409,
            detail={"code": "USERNAME_TAKEN", "message": "Username already taken"},
        )

    result = (
        await db.table("profiles")
        .insert({"id": user_id, **payload.model_dump()})
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=500, detail={"code": "CREATE_FAILED", "message": "Failed to create profile"})

    # Trigger embedding generation (fire-and-forget, don't block response)
    try:
        admin_client = await anext(get_supabase_admin())
        await upsert_volunteer_embedding(admin_client, user_id, result.data[0], aura=None)
        logger.info("Embedding generated for new profile", user_id=user_id)
    except Exception as e:
        logger.warning("Embedding generation failed on profile create: {err}", err=str(e)[:200])

    return ProfileResponse(**result.data[0])


@router.put("/me", response_model=ProfileResponse)
@limiter.limit(RATE_PROFILE_WRITE)
async def update_my_profile(
    request: Request,
    payload: ProfileUpdate,
    db: SupabaseUser,
    user_id: CurrentUserId,
    admin: SupabaseAdmin,
) -> ProfileResponse:
    """Update the current user's profile."""
    update_data = payload.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(
            status_code=422,
            detail={"code": "NO_FIELDS", "message": "No fields to update"},
        )

    result = (
        await db.table("profiles")
        .update(update_data)
        .eq("id", user_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Profile not found"},
        )

    # Trigger embedding re-generation with updated profile data
    try:
        aura_result = await admin.table("aura_scores").select("*").eq("volunteer_id", user_id).single().execute()
        aura_data = aura_result.data
    except Exception:
        aura_data = None

    try:
        await upsert_volunteer_embedding(admin, user_id, result.data[0], aura=aura_data)
        logger.info("Embedding updated after profile change", user_id=user_id)
    except Exception as e:
        logger.warning("Embedding update failed on profile update: {err}", err=str(e)[:200])

    return ProfileResponse(**result.data[0])


@router.post(
    "/{volunteer_id}/verification-link",
    response_model=CreateVerificationLinkResponse,
    status_code=201,
)
@limiter.limit(RATE_PROFILE_WRITE)
async def create_verification_link(
    request: Request,
    volunteer_id: str,
    payload: CreateVerificationLinkRequest,
    db: SupabaseAdmin,
    user_id: CurrentUserId,
) -> CreateVerificationLinkResponse:
    """Create a one-use verification link for a volunteer.

    Only the volunteer themselves can request verification links.
    The link is sent to an expert who rates the volunteer's competency.
    Token is valid for 7 days, single-use.
    """
    # CRIT-02 fix: only allow self-verification requests
    if volunteer_id != user_id:
        raise HTTPException(
            status_code=403,
            detail={"code": "FORBIDDEN", "message": "You can only request verification for your own profile"},
        )

    # Ensure target volunteer exists
    volunteer = (
        await db.table("profiles")
        .select("id")
        .eq("id", volunteer_id)
        .single()
        .execute()
    )
    if not volunteer.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "VOLUNTEER_NOT_FOUND", "message": "Volunteer not found"},
        )

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(tz=UTC) + timedelta(days=7)
    expires_at_iso = expires_at.isoformat()

    result = (
        await db.table("expert_verifications")
        .insert(
            {
                "volunteer_id": volunteer_id,
                "created_by": user_id,
                "verifier_name": payload.verifier_name,
                "verifier_org": payload.verifier_org,
                "competency_id": payload.competency_id,
                "token": token,
                "token_expires_at": expires_at_iso,
            }
        )
        .execute()
    )

    if not result.data:
        logger.error("Failed to create verification link", volunteer_id=volunteer_id)
        raise HTTPException(
            status_code=500,
            detail={"code": "CREATE_FAILED", "message": "Failed to create verification link"},
        )

    row = result.data[0]
    verify_url = f"{settings.app_url}/az/verify/{token}"

    logger.info(
        "Verification link created",
        volunteer_id=volunteer_id,
        created_by=user_id,
        competency=payload.competency_id,
    )

    return CreateVerificationLinkResponse(
        id=row["id"],
        token=token,
        verify_url=verify_url,
        expires_at=expires_at,
        verifier_name=payload.verifier_name,
        verifier_org=payload.verifier_org,
        competency_id=payload.competency_id,
    )


@router.get("/{username}", response_model=PublicProfileResponse)
@limiter.limit(RATE_DEFAULT)
async def get_public_profile(
    request: Request,
    username: str,
    db: SupabaseAdmin,
) -> PublicProfileResponse:
    """Get a public profile by username — no auth required."""
    result = (
        await db.table("profiles")
        .select("id, username, display_name, avatar_url, bio, location, languages, badge_issued_at")
        .eq("username", username)
        .eq("is_public", True)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Profile not found"},
        )
    return PublicProfileResponse(**result.data)
