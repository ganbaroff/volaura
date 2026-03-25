"""AURA score endpoints."""

from fastapi import APIRouter, HTTPException

from app.deps import CurrentUserId, SupabaseAdmin, SupabaseUser
from app.schemas.aura import (
    AuraScoreResponse,
    SharingPermissionRequest,
    UpdateVisibilityRequest,
)

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
    """Get any volunteer's AURA score (public profiles only, respects visibility)."""
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
    # Respect visibility setting
    visibility = result.data.get("visibility", "public")
    if visibility == "hidden":
        raise HTTPException(
            status_code=404,
            detail={"code": "AURA_HIDDEN", "message": "This volunteer's score is private"},
        )
    if visibility == "badge_only":
        # Return only badge tier + total score, strip competency details
        return AuraScoreResponse(
            **{**result.data, "competency_scores": {}, "aura_history": []}
        )
    return AuraScoreResponse(**result.data)


@router.patch("/me/visibility")
async def update_visibility(
    body: UpdateVisibilityRequest,
    db: SupabaseUser,
    user_id: CurrentUserId,
):
    """Update own AURA score visibility (public/badge_only/hidden)."""
    result = (
        await db.table("aura_scores")
        .update({"visibility": body.visibility})
        .eq("volunteer_id", user_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "AURA_NOT_FOUND", "message": "No AURA score to update"},
        )
    return {"status": "ok", "visibility": body.visibility}


@router.post("/me/sharing")
async def manage_sharing_permission(
    body: SharingPermissionRequest,
    db: SupabaseUser,
    user_id: CurrentUserId,
):
    """Grant or revoke sharing permission to an organization."""
    if body.action == "grant":
        await (
            db.table("sharing_permissions")
            .upsert(
                {
                    "user_id": user_id,
                    "org_id": body.org_id,
                    "permission_type": body.permission_type,
                    "revoked_at": None,
                },
                on_conflict="user_id,org_id,permission_type",
            )
            .execute()
        )
        return {"status": "granted", "org_id": body.org_id, "permission_type": body.permission_type}
    else:
        # Revoke: set revoked_at
        from datetime import datetime, timezone
        await (
            db.table("sharing_permissions")
            .update({"revoked_at": datetime.now(timezone.utc).isoformat()})
            .eq("user_id", user_id)
            .eq("org_id", body.org_id)
            .eq("permission_type", body.permission_type)
            .execute()
        )
        return {"status": "revoked", "org_id": body.org_id, "permission_type": body.permission_type}
