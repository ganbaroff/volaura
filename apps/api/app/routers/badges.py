"""Open Badges 3.0 endpoints.

Serves W3C Verifiable Credential JSON-LD for AURA badges.
Compatible with LinkedIn's digital credential import.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from app.deps import SupabaseAdmin
from app.middleware.rate_limit import RATE_DISCOVERY, limiter

router = APIRouter(prefix="/badges", tags=["Badges"])

# ── Open Badges 3.0 JSON-LD ───────────────────────────────────────────────────

@router.get("/{volunteer_id}/credential")
@limiter.limit(RATE_DISCOVERY)
async def get_open_badge_credential(
    volunteer_id: str,
    request: Request,
    db: SupabaseAdmin,
) -> dict:
    """Return an Open Badges 3.0 Verifiable Credential for a volunteer's AURA badge.

    The credential is publicly accessible — no auth required.
    Rate limited (RATE_DISCOVERY) to prevent volunteer enumeration.
    """
    # Validate UUID format before any DB call (SECURITY-REVIEW.md Point 2)
    try:
        UUID(volunteer_id)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_UUID", "message": "volunteer_id must be a valid UUID"},
        )

    # Fetch profile
    profile_result = await db.table("profiles").select(
        "id, username, display_name, badge_issued_at"
    ).eq("id", volunteer_id).eq("is_public", True).maybe_single().execute()

    if not profile_result.data:
        raise HTTPException(status_code=404, detail={"code": "PROFILE_NOT_FOUND", "message": "Profile not found"})

    profile = profile_result.data

    aura_result = await db.table("aura_scores").select(
        "total_score, badge_tier, elite_status, last_updated, visibility"
    ).eq("volunteer_id", volunteer_id).maybe_single().execute()

    if not aura_result.data:
        raise HTTPException(status_code=404, detail={"code": "AURA_NOT_FOUND", "message": "No AURA score found"})

    aura = aura_result.data

    # Respect visibility setting (CRIT-04 parity with aura.py /{volunteer_id})
    # Identical 404 for hidden vs nonexistent — prevents enumeration
    if aura.get("visibility") == "hidden":
        raise HTTPException(
            status_code=404,
            detail={"code": "AURA_NOT_FOUND", "message": "No AURA score found"},
        )
    base_url = str(request.base_url).rstrip("/")
    username = profile["username"]
    name = profile["display_name"] or username
    tier = aura["badge_tier"].capitalize()
    score = float(aura["total_score"])
    issued_at = aura.get("last_updated") or datetime.now(UTC).isoformat()

    # Open Badges 3.0 / W3C Verifiable Credential
    return {
        "@context": [
            "https://www.w3.org/2018/credentials/v1",
            "https://purl.imsglobal.org/spec/ob/v3p0/context-3.0.1.json",
        ],
        "id": f"{base_url}/api/badges/{volunteer_id}/credential",
        "type": ["VerifiableCredential", "OpenBadgeCredential"],
        "issuer": {
            "id": f"{base_url}/api/badges/issuer",
            "type": "Profile",
            "name": "Volaura",
            "url": "https://volaura.az",
            "email": "badges@volaura.az",
        },
        "issuanceDate": issued_at,
        "name": f"Volaura AURA {tier} Badge",
        "credentialSubject": {
            "id": f"{base_url}/u/{username}",
            "type": "AchievementSubject",
            "name": name,
            "achievement": {
                "id": f"{base_url}/api/badges/achievement/{aura['badge_tier']}",
                "type": "Achievement",
                "name": f"AURA {tier} Badge",
                "description": (
                    f"Awarded to {name} for achieving an AURA score of {score:.1f} "
                    f"on the Volaura verified talent platform."
                ),
                "criteria": {
                    "narrative": f"Professional completed verified competency assessments and achieved AURA score ≥ {_tier_threshold(aura['badge_tier'])}."
                },
                "image": {
                    "id": f"{base_url}/u/{username}/card",
                    "type": "Image",
                },
            },
            "result": [
                {
                    "type": "Result",
                    "resultDescription": "AURA Score",
                    "value": f"{score:.1f}",
                    "status": "Completed",
                }
            ],
        },
    }


@router.get("/issuer")
async def get_issuer_profile(request: Request) -> dict:
    """Open Badges issuer profile."""
    base_url = str(request.base_url).rstrip("/")
    return {
        "@context": "https://purl.imsglobal.org/spec/ob/v3p0/context-3.0.1.json",
        "id": f"{base_url}/api/badges/issuer",
        "type": "Profile",
        "name": "Volaura",
        "url": "https://volaura.az",
        "email": "badges@volaura.az",
        "description": "Verified Professional Talent Platform for Azerbaijan",
    }


def _tier_threshold(tier: str) -> int:
    return {"platinum": 90, "gold": 75, "silver": 60, "bronze": 40}.get(tier, 0)
