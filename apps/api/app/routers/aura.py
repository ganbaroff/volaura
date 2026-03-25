"""AURA score endpoints."""

from fastapi import APIRouter, HTTPException, Request

from app.deps import CurrentUserId, SupabaseAdmin, SupabaseUser
from app.middleware.rate_limit import limiter, RATE_DEFAULT
from app.schemas.aura import (
    AuraScoreResponse,
    SharingPermissionRequest,
    UpdateVisibilityRequest,
)

router = APIRouter(prefix="/aura", tags=["AURA"])

# Confidence label mapping — never expose internal model names to clients
# Security: exposing model names enables calibration attacks (adversarial prompting)
_MODEL_CONFIDENCE: dict[str, str] = {
    "gemini-2.5-flash": "high",
    "gpt-4o-mini": "high",
    "keyword_fallback": "pattern_matched",
    "swarm": "high",
    "unknown": "unknown",
}


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
@limiter.limit(RATE_DEFAULT)
async def get_aura_by_id(
    request: Request,
    volunteer_id: str,
    db: SupabaseAdmin,
) -> AuraScoreResponse:
    """Get any volunteer's AURA score (public profiles only, respects visibility).

    Uses service-role client (SupabaseAdmin) to check existence before enforcing
    visibility — intentional for public discovery of non-hidden profiles.

    Security (CRIT-04): Identical 404 response for hidden vs nonexistent profiles
    to prevent volunteer existence enumeration attacks.
    """
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
    # CRIT-04: Use identical error code for hidden AND nonexistent — prevents enumeration
    visibility = result.data.get("visibility", "public")
    if visibility == "hidden":
        raise HTTPException(
            status_code=404,
            detail={"code": "AURA_NOT_FOUND", "message": "AURA score not found"},
        )
    if visibility == "badge_only":
        # Return only badge tier + total score, strip competency details
        return AuraScoreResponse(
            **{**result.data, "competency_scores": {}, "aura_history": []}
        )
    return AuraScoreResponse(**result.data)


@router.get("/me/explanation")
async def get_aura_explanation(
    db: SupabaseUser,
    user_id: CurrentUserId,
):
    """Get detailed explanation of AURA score — per-competency breakdown with evaluation logs.
    Phase 2: Transparent Evaluation Logs — 'Show Your Work'.
    """
    # Get completed sessions with evaluation data
    sessions_result = (
        await db.table("assessment_sessions")
        .select("competency_id,answers,role_level,completed_at")
        .eq("volunteer_id", user_id)
        .eq("status", "completed")
        .order("completed_at", desc=True)
        .execute()
    )
    if not sessions_result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "NO_ASSESSMENTS", "message": "Complete an assessment first to see explanations"},
        )

    explanations = []
    for session in sessions_result.data:
        answers = session.get("answers", {})
        items = answers.get("items", [])
        # Collect evaluation logs from items
        item_explanations = []
        for item in items:
            eval_log = item.get("evaluation_log")
            if eval_log:
                # CRIT-05: Never expose internal model names — prevents calibration attacks.
                # Map model_used → evaluation_confidence (high/pattern_matched/unknown)
                raw_model = eval_log.get("model_used", "unknown")
                confidence = _MODEL_CONFIDENCE.get(raw_model, "unknown")
                item_explanations.append({
                    "question_id": item.get("question_id"),
                    "raw_score": round(item.get("raw_score", 0), 3),
                    "concept_scores": eval_log.get("concept_scores", {}),
                    "evaluation_confidence": confidence,  # high | pattern_matched | unknown
                    "methodology": eval_log.get("methodology", "BARS"),
                })

        if item_explanations:
            explanations.append({
                "competency_id": session.get("competency_id"),
                "role_level": session.get("role_level", "volunteer"),
                "completed_at": session.get("completed_at"),
                "items_evaluated": len(item_explanations),
                "evaluations": item_explanations,
            })

    return {
        "volunteer_id": user_id,
        "explanation_count": len(explanations),
        "methodology_reference": "BARS (Behaviourally Anchored Rating Scale) aligned with ISO 10667-2",
        "explanations": explanations,
    }


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
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
):
    """Grant or revoke sharing permission to an organization."""
    # HIGH-05: Validate org exists before creating permission record.
    # Prevents phantom permissions to nonexistent orgs.
    org_check = (
        await db_admin.table("organizations")
        .select("id")
        .eq("id", body.org_id)
        .maybe_single()
        .execute()
    )
    if not org_check.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "ORG_NOT_FOUND", "message": "Organization not found"},
        )

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
