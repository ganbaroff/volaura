"""Expert verification endpoints.

Public flow (no auth required):
  GET  /api/verify/{token}  → validate token, return professional + competency info
  POST /api/verify/{token}  → submit rating + comment, mark token as used

Authenticated flow:
  POST /api/profiles/{volunteer_id}/verification-link  (in profiles.py)

AURA integration:
  On successful submission, blends the verification rating into the professional's
  competency scores and calls upsert_aura_score() to refresh the AURA total.
  Blend formula: existing_score * 0.6 + verification_score * 0.4
  If no prior assessment: verification_score * 0.85 (slight discount)
  Rating → score: (rating / 5.0) * 100  →  1=20, 2=40, 3=60, 4=80, 5=100
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Request
from loguru import logger

from app.deps import SupabaseAdmin
from app.middleware.rate_limit import limiter
from app.schemas.verification import (
    SubmitVerificationRequest,
    SubmitVerificationResponse,
    VerificationTokenInfo,
)

router = APIRouter(prefix="/verify", tags=["Verification"])


async def _get_valid_token_row(token: str, db: SupabaseAdmin) -> dict:
    """Fetch token row and raise structured 4xx if invalid/expired/used.

    Uses admin client because this is a public endpoint with no user JWT.
    The token itself IS the auth credential for this flow.
    """
    result = (
        await db.table("expert_verifications")
        .select(
            "id, token_used, token_expires_at, competency_id, verifier_name, verifier_org, "
            "volunteer_id, profiles!expert_verifications_volunteer_id_fkey"
            "(display_name, username, avatar_url)"
        )
        .eq("token", token)
        .single()
        .execute()
    )

    if not result.data:
        logger.warning("Verification token not found", token_prefix=token[:8])
        raise HTTPException(
            status_code=404,
            detail={
                "code": "TOKEN_INVALID",
                "message": "This link is invalid. It may have been mistyped or removed.",
            },
        )

    row = result.data

    if row["token_used"]:
        logger.info("Verification token already used", token_prefix=token[:8])
        raise HTTPException(
            status_code=409,
            detail={
                "code": "TOKEN_ALREADY_USED",
                "message": "This verification has already been submitted. Thank you!",
            },
        )

    expires_at = datetime.fromisoformat(row["token_expires_at"].replace("Z", "+00:00"))
    if expires_at < datetime.now(tz=UTC):
        logger.info("Verification token expired", token_prefix=token[:8])
        raise HTTPException(
            status_code=410,
            detail={
                "code": "TOKEN_EXPIRED",
                "message": "This link has expired. Links are valid for 7 days. Contact the professional for a new link.",
            },
        )

    return row


def _rating_to_score(rating: int) -> float:
    """Convert 1-5 rating to 0-100 AURA-compatible score.

    Linear scale: 1→20, 2→40, 3→60, 4→80, 5→100.
    Not starting at 0 because even a "Poor" rating still indicates
    the expert knows the professional and chose to verify them.
    """
    return round((rating / 5.0) * 100, 2)


async def _update_aura_after_verification(
    volunteer_id: str,
    competency_id: str,
    rating: int,
    db: SupabaseAdmin,
) -> None:
    """Blend verification rating into AURA score and persist.

    Does not raise — failures are logged but not propagated to the caller.
    The verification itself is already committed; AURA recalc is best-effort.
    """
    try:
        verification_score = _rating_to_score(rating)

        # Fetch current competency scores
        aura_result = (
            await db.table("aura_scores")
            .select("competency_scores")
            .eq("volunteer_id", volunteer_id)
            .single()
            .execute()
        )

        if aura_result.data and aura_result.data.get("competency_scores"):
            existing_scores: dict = dict(aura_result.data["competency_scores"])
            existing = float(existing_scores.get(competency_id, 0) or 0)
            if existing > 0:
                blended = round(existing * 0.6 + verification_score * 0.4, 2)
            else:
                # No prior assessment for this competency
                blended = round(verification_score * 0.85, 2)
            existing_scores[competency_id] = blended
            updated_scores = existing_scores
        else:
            # Professional has no AURA record yet — create one from this verification
            updated_scores = {competency_id: round(verification_score * 0.85, 2)}

        await db.rpc(
            "upsert_aura_score",
            {
                "p_volunteer_id": volunteer_id,
                "p_competency_scores": updated_scores,
            },
        ).execute()

        logger.info(
            "AURA updated after verification",
            volunteer_id=volunteer_id,
            competency=competency_id,
            verification_score=verification_score,
        )

    except Exception as exc:  # noqa: BLE001
        # Non-fatal: verification row is already saved, log and continue
        logger.error(
            "AURA recalculation failed after verification",
            volunteer_id=volunteer_id,
            error=str(exc),
        )


TokenParam = Annotated[str, Path(max_length=100, description="One-use verification token")]


@router.get("/{token}", response_model=VerificationTokenInfo)
@limiter.limit("10/minute")
async def get_verification_info(
    request: Request,
    token: TokenParam,
    db: SupabaseAdmin,
) -> VerificationTokenInfo:
    """Validate token and return professional + competency info for the rating UI.

    Public endpoint — no auth header required.
    Attacker note: only non-sensitive professional info is returned (display_name, username, avatar).
    The token is single-use and time-limited — no brute-force risk beyond rate limiting.
    """
    row = await _get_valid_token_row(token, db)

    profile = row.get("profiles") or {}
    return VerificationTokenInfo(
        volunteer_display_name=profile.get("display_name") or profile.get("username", "Professional"),
        volunteer_username=profile.get("username", ""),
        volunteer_avatar_url=profile.get("avatar_url"),
        verifier_name=row["verifier_name"],
        verifier_org=row.get("verifier_org"),
        competency_id=row["competency_id"],
    )


@router.post("/{token}", response_model=SubmitVerificationResponse, status_code=201)
@limiter.limit("5/minute")
async def submit_verification(
    request: Request,
    token: TokenParam,
    payload: SubmitVerificationRequest,
    db: SupabaseAdmin,
) -> SubmitVerificationResponse:
    """Submit a rating for a professional and mark the token as used.

    This is atomic: we update token_used=TRUE in the same row as the rating.
    If two concurrent requests hit this endpoint with the same token, the second
    will get TOKEN_ALREADY_USED from _get_valid_token_row.
    Note: There is a small TOCTOU window — mitigated by the UNIQUE constraint on
    token + a DB-level check trigger if needed in production.
    """
    row = await _get_valid_token_row(token, db)

    now_iso = datetime.now(tz=UTC).isoformat()
    update_result = (
        await db.table("expert_verifications")
        .update(
            {
                "rating": payload.rating,
                "comment": payload.comment,
                "token_used": True,
                "verified_at": now_iso,
            }
        )
        .eq("token", token)
        .eq("token_used", False)  # extra guard against TOCTOU
        .execute()
    )

    if not update_result.data:
        # Another request beat us — treat as already used
        logger.warning("Concurrent verification submission detected", token_prefix=token[:8])
        raise HTTPException(
            status_code=409,
            detail={
                "code": "TOKEN_ALREADY_USED",
                "message": "This verification has already been submitted. Thank you!",
            },
        )

    profile = row.get("profiles") or {}
    professional_name = profile.get("display_name") or profile.get("username", "Professional")

    logger.info(
        "Verification submitted",
        token_prefix=token[:8],
        competency=row["competency_id"],
        rating=payload.rating,
    )

    # Recalculate AURA score — best-effort, non-fatal
    await _update_aura_after_verification(
        volunteer_id=row["volunteer_id"],
        competency_id=row["competency_id"],
        rating=payload.rating,
        db=db,
    )

    return SubmitVerificationResponse(
        status="verified",
        volunteer_display_name=professional_name,
        competency_id=row["competency_id"],
        rating=payload.rating,
    )
