"""AURA score endpoints."""

from datetime import UTC

from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from app.core.assessment.aura_calc import apply_activity_boost, calculate_effective_score
from app.deps import CurrentUserId, SupabaseAdmin, SupabaseUser
from app.middleware.rate_limit import (
    RATE_DEFAULT,
    RATE_DISCOVERY,
    RATE_LLM,
    RATE_PROFILE_WRITE,
    limiter,
)
from app.schemas.aura import (
    AuraExplanationResponse,
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


def _with_effective_score(data: dict) -> dict:
    """Compute and inject effective_score (decay-adjusted) into AURA data dict."""
    last_updated = data.get("last_updated")
    raw_score = data.get("total_score", 0.0)
    if last_updated is not None and raw_score:
        if isinstance(last_updated, str):
            try:
                from datetime import datetime
                last_updated = datetime.fromisoformat(last_updated)
            except (ValueError, TypeError):
                last_updated = None
        if last_updated is not None:
            decayed = calculate_effective_score(raw_score, last_updated)
            # Activity boost: recent event participation counteracts decay
            events_recent = int(data.get("events_attended", 0))
            boosted = apply_activity_boost(decayed, events_recent)
            data = {**data, "effective_score": boosted}
    return data


@router.get("/me", response_model=AuraScoreResponse)
@limiter.limit(RATE_DEFAULT)
async def get_my_aura(
    request: Request,
    db: SupabaseUser,
    user_id: CurrentUserId,
) -> AuraScoreResponse:
    """Get the current user's AURA score."""
    result = (
        await db.table("aura_scores")
        .select("volunteer_id,total_score,badge_tier,elite_status,competency_scores,visibility,reliability_score,reliability_status,events_attended,events_no_show,percentile_rank,aura_history,last_updated")
        .eq("volunteer_id", user_id)
        .maybe_single()
        .execute()
    )
    if not result or not result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "AURA_NOT_FOUND", "message": "No AURA score yet — complete an assessment first"},
        )
    return AuraScoreResponse(**_with_effective_score(dict(result.data)))


@router.get("/me/explanation", response_model=AuraExplanationResponse)
@limiter.limit(RATE_LLM)
async def get_aura_explanation(
    request: Request,
    db: SupabaseUser,
    user_id: CurrentUserId,
):
    """Get detailed explanation of AURA score — per-competency breakdown with evaluation logs.
    Phase 2: Transparent Evaluation Logs — 'Show Your Work'.
    DeCE detail (quote + confidence) included when available from LLM evaluations.

    Route ordering: MUST be registered BEFORE /{volunteer_id} wildcard.
    FastAPI matches routes in registration order — if the wildcard is first,
    /me/explanation would match as volunteer_id="me" and return a 404.
    """
    # Get completed sessions with evaluation data
    sessions_result = (
        await db.table("assessment_sessions")
        .select("competency_id,answers,role_level,completed_at")
        .eq("volunteer_id", user_id)
        .eq("status", "completed")
        .order("completed_at", desc=True)
        .limit(10)  # Scaling: cap at 10 most recent — answers JSONB can be 5-10KB each
        .execute()
    )
    if not sessions_result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "NO_ASSESSMENTS", "message": "Complete an assessment first to see explanations"},
        )

    explanations = []
    pending_reeval_count = 0  # BUG-012: track degraded answers awaiting LLM re-eval
    for session in sessions_result.data:
        answers = session.get("answers", {})
        items = answers.get("items", [])
        # Collect evaluation logs from items
        item_explanations = []
        for item in items:
            eval_log = item.get("evaluation_log")
            if eval_log:
                # BUG-012: count degraded answers — these are queued for LLM re-eval
                if eval_log.get("evaluation_mode") == "degraded":
                    pending_reeval_count += 1
                # CRIT-05: Never expose internal model names — prevents calibration attacks.
                # Map model_used → evaluation_confidence (high/pattern_matched/unknown)
                raw_model = eval_log.get("model_used", "unknown")
                confidence = _MODEL_CONFIDENCE.get(raw_model, "unknown")
                explanation_entry: dict = {
                    "question_id": item.get("question_id"),
                    "concept_scores": {
                        k: v for k, v in eval_log.get("concept_scores", {}).items()
                        if isinstance(k, str) and isinstance(v, (int, float))
                    },
                    "evaluation_confidence": confidence,  # high | pattern_matched | unknown
                    "methodology": eval_log.get("methodology", "BARS"),
                }
                # DeCE: include per-concept breakdown with quotes when available
                dece_details = eval_log.get("concept_details")
                if dece_details and isinstance(dece_details, list):
                    explanation_entry["concept_details"] = dece_details
                item_explanations.append(explanation_entry)

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
        "has_pending_evaluations": pending_reeval_count > 0,  # BUG-012: LLM re-eval queued, scores will improve
        "pending_reeval_count": pending_reeval_count,         # BUG-012: how many answers are being re-evaluated
        "methodology_reference": "BARS (Behaviourally Anchored Rating Scale) aligned with ISO 10667-2",
        "explanations": explanations,
    }


@router.get("/{volunteer_id}", response_model=AuraScoreResponse)
@limiter.limit(RATE_DISCOVERY)
async def get_aura_by_id(
    request: Request,
    volunteer_id: str,
    db: SupabaseAdmin,
) -> AuraScoreResponse:
    """Get any volunteer's AURA score (public profiles only, respects visibility).

    Public endpoint — no auth required. Called by /u/[username] for anonymous visitors.
    Rate limited to RATE_DISCOVERY (10/min) to prevent bulk enumeration scraping.

    Uses service-role client (SupabaseAdmin) to check existence before enforcing
    visibility — intentional for public discovery of non-hidden profiles.

    Security (CRIT-04): Identical 404 response for hidden vs nonexistent profiles
    to prevent volunteer existence enumeration attacks.

    Profile view notifications are emitted via the dedicated endpoint:
    POST /api/profiles/{username}/view — called explicitly by the frontend.

    Route ordering: MUST come AFTER /me and /me/explanation — wildcard captures anything.
    """
    result = (
        await db.table("aura_scores")
        .select("*")
        .eq("volunteer_id", volunteer_id)
        .maybe_single()
        .execute()
    )
    if not result or not result.data:
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
        # Return only badge tier + total score — strip ALL private fields
        _PRIVATE_FIELDS = {"competency_scores", "aura_history", "last_updated",
                           "events_attended", "events_no_show", "events_late",
                           "reliability_score", "reliability_status"}
        badge_data = {k: v for k, v in result.data.items() if k not in _PRIVATE_FIELDS}
        badge_data["competency_scores"] = {}
        badge_data["aura_history"] = []
        return AuraScoreResponse(**_with_effective_score(badge_data))
    # Strip last_updated from public view — prevents assessment timing inference (Security P2)
    public_data = dict(result.data)
    public_data.pop("last_updated", None)
    return AuraScoreResponse(**_with_effective_score(public_data))


@router.get("/me/visibility")
@limiter.limit(RATE_DEFAULT)
async def get_visibility(
    request: Request,
    db: SupabaseUser,
    user_id: CurrentUserId,
):
    """Get current AURA score visibility setting.

    Settings page seeds the radio buttons from this endpoint — prevents
    silently overriding the user's saved preference (Leyla simulation P0 fix).
    Returns {"visibility": "public"|"badge_only"|"hidden"} or 404 if no score yet.
    """
    result = (
        await db.table("aura_scores")
        .select("visibility")
        .eq("volunteer_id", user_id)
        .maybe_single()
        .execute()
    )
    if not result or not result.data:
        # No score yet — return default so frontend can still render the setting
        return {"visibility": "public"}
    return {"visibility": result.data.get("visibility", "public")}


@router.patch("/me/visibility")
@limiter.limit(RATE_PROFILE_WRITE)
async def update_visibility(
    request: Request,
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
    if not result or not result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "AURA_NOT_FOUND", "message": "No AURA score to update"},
        )
    # HIGH-06 FIX: audit log for visibility changes
    logger.info("AURA visibility changed", user_id=user_id, visibility=body.visibility)
    return {"status": "ok", "visibility": body.visibility}


@router.post("/me/sharing")
@limiter.limit(RATE_PROFILE_WRITE)
async def manage_sharing_permission(
    request: Request,
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
        from datetime import datetime
        await (
            db.table("sharing_permissions")
            .update({"revoked_at": datetime.now(UTC).isoformat()})
            .eq("user_id", user_id)
            .eq("org_id", body.org_id)
            .eq("permission_type", body.permission_type)
            .execute()
        )
        return {"status": "revoked", "org_id": body.org_id, "permission_type": body.permission_type}
