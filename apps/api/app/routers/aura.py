"""AURA score endpoints."""

from fastapi import APIRouter, HTTPException

from app.deps import CurrentUserId, SupabaseAdmin, SupabaseUser
from app.schemas.aura import AuraScoreResponse

router = APIRouter(prefix="/aura", tags=["AURA"])


@router.get("/me", response_model=AuraScoreResponse)
async def get_my_aura(
    db: SupabaseUser,
    user_id: CurrentUserId,
) -> AuraScoreResponse:
    """Get the current user's AURA score."""
    result = (
        await db.table("aura_scores")
        .select("*")
        .eq("volunteer_id", user_id)
        .maybe_single()
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "AURA_NOT_FOUND", "message": "No AURA score yet — complete an assessment first"},
        )
    return AuraScoreResponse(**result.data)


@router.get("/{volunteer_id}", response_model=AuraScoreResponse)
async def get_aura_by_id(
    volunteer_id: str,
    db: SupabaseAdmin,
) -> AuraScoreResponse:
    """Get any volunteer's AURA score (public — for profile pages)."""
    result = (
        await db.table("aura_scores")
        .select("*")
        .eq("volunteer_id", volunteer_id)
        .maybe_single()
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "AURA_NOT_FOUND", "message": "AURA score not found"},
        )
    return AuraScoreResponse(**result.data)
