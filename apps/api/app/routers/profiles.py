"""Profile endpoints."""

import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Query, Request
from loguru import logger

from app.config import settings
from app.deps import CurrentUserId, SupabaseAdmin, SupabaseUser
from app.middleware.rate_limit import RATE_DEFAULT, RATE_DISCOVERY, RATE_PROFILE_WRITE, limiter
from app.schemas.profile import (
    DiscoverableProfessional,
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
from app.services.notification_service import notify

router = APIRouter(prefix="/profiles", tags=["Profiles"])


def _anonymize_name(display_name: str | None) -> str:
    """Server-side name anonymization for public talent listings.

    SEC-03: /profiles/public was returning raw display_name, letting orgs
    cross-reference with the anonymized /volunteers/discovery endpoint to
    deanonymize all professionals. Fixed by applying the same anonymization.

    Result: "Leyla A." (first name + last initial).
    """
    if not display_name or not display_name.strip():
        return "Professional"
    parts = display_name.strip().split()
    first = parts[0][:20]  # cap at 20 chars
    if len(parts) == 1:
        return first
    last_initial = parts[-1][0].upper()
    return f"{first} {last_initial}."


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
    # Explicit column list — excludes stripe_customer_id, stripe_subscription_id
    # (internal payment references that have no client-side use and must not leak).
    try:
        result = (
            await db.table("profiles")
            .select(
                "id, username, display_name, bio, avatar_url, location, languages, "
                "account_type, is_public, visible_to_orgs, org_type, registration_number, "
                "registration_tier, subscription_status, trial_started_at, trial_ends_at, "
                "subscription_started_at, subscription_ends_at, created_at, updated_at, "
                "age_confirmed, terms_version, terms_accepted_at"
            )
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )
    except Exception:
        result = None
    if not result or not result.data:
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
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
) -> ProfileResponse:
    """Create a profile for the current user (called after registration)."""
    # Check username not taken
    existing = await db.table("profiles").select("id").eq("username", payload.username).execute()
    if existing.data:
        raise HTTPException(
            status_code=409,
            detail={"code": "USERNAME_TAKEN", "message": "Username already taken"},
        )

    # GDPR consent capture — write terms_accepted_at at profile creation time.
    # The user already accepted terms at signup; profile creation happens immediately
    # after (onboarding flow). This timestamp is the audit trail required by GDPR Art. 7.
    insert_data = {"id": user_id, **payload.model_dump()}
    if payload.age_confirmed:
        insert_data["terms_accepted_at"] = datetime.now(UTC).isoformat()
    else:
        # age_confirmed=False at profile creation = non-compliant state.
        # Log for audit so we can identify accounts to follow up with.
        logger.warning(
            "Profile created without age confirmation — GDPR Art. 8 gap",
            user_id=user_id,
        )

    result = await db.table("profiles").insert(insert_data).execute()
    if not result or not result.data:
        raise HTTPException(status_code=500, detail={"code": "CREATE_FAILED", "message": "Failed to create profile"})

    # GROWTH-2: If invited by an org, mark matching invite as accepted
    if payload.invited_by_org_id:
        try:
            user_resp = await db_admin.auth.admin.get_user_by_id(user_id)
            user_email = user_resp.user.email if user_resp and user_resp.user else None
            if user_email:
                await (
                    db_admin.table("organization_invites")
                    .update(
                        {
                            "status": "accepted",
                            "accepted_at": datetime.now(UTC).isoformat(),
                        }
                    )
                    .eq("org_id", payload.invited_by_org_id)
                    .eq("email", user_email)
                    .eq("status", "pending")
                    .execute()
                )
        except Exception as e:
            logger.warning("Invite status update failed (non-fatal)", user_id=user_id, error=str(e)[:200])

    # Trigger embedding generation (fire-and-forget, don't block response)
    try:
        await upsert_volunteer_embedding(db_admin, user_id, result.data[0], aura=None)
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

    result = await db.table("profiles").update(update_data).eq("id", user_id).execute()
    if not result or not result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Profile not found"},
        )

    # Trigger embedding re-generation with updated profile data
    try:
        aura_result = await admin.table("aura_scores").select("*").eq("volunteer_id", user_id).maybe_single().execute()
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
    "/{professional_id}/verification-link",
    response_model=CreateVerificationLinkResponse,
    status_code=201,
)
@limiter.limit(RATE_PROFILE_WRITE)
async def create_verification_link(
    request: Request,
    professional_id: str,
    payload: CreateVerificationLinkRequest,
    db: SupabaseUser,
    user_id: CurrentUserId,
) -> CreateVerificationLinkResponse:
    """Create a one-use verification link for a professional.

    Only the professional themselves can request verification links.
    The link is sent to an expert who rates the professional's competency.
    Token is valid for 7 days, single-use.
    """
    # CRIT-02 fix: only allow self-verification requests
    if professional_id != user_id:
        raise HTTPException(
            status_code=403,
            detail={"code": "FORBIDDEN", "message": "You can only request verification for your own profile"},
        )

    # Ensure target professional exists (.maybe_single() returns None instead of raising 406)
    profile = await db.table("profiles").select("id").eq("id", professional_id).maybe_single().execute()
    if not profile.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Professional not found"},
        )

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(tz=UTC) + timedelta(days=7)
    expires_at_iso = expires_at.isoformat()

    result = (
        await db.table("expert_verifications")
        .insert(
            {
                "volunteer_id": professional_id,
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

    if not result or not result.data:
        logger.error("Failed to create verification link", professional_id=professional_id)
        raise HTTPException(
            status_code=500,
            detail={"code": "CREATE_FAILED", "message": "Failed to create verification link"},
        )

    row = result.data[0]
    verify_url = f"{settings.app_url}/{settings.default_locale}/verify/{token}"

    logger.info(
        "Verification link created",
        professional_id=professional_id,
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


@router.get("/public", response_model=list[DiscoverableProfessional])
@limiter.limit(RATE_DISCOVERY)
async def list_public_professionals(
    request: Request,
    db: SupabaseAdmin,
    user_id: CurrentUserId,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[DiscoverableProfessional]:
    """List professionals who have opted in to org discovery (visible_to_orgs=True).

    Requires authentication as an organization account (account_type='organization').
    Ordered by AURA score descending. Paginated.
    """
    # Dual org-role check: JWT (account_type in profile) + DB verification
    caller = await db.table("profiles").select("account_type").eq("id", str(user_id)).maybe_single().execute()
    if not caller.data or caller.data.get("account_type") != "organization":
        raise HTTPException(
            status_code=403,
            detail={"code": "ORG_REQUIRED", "message": "Only organization accounts can browse talent"},
        )

    # Fetch opted-in professionals joined with AURA score, ordered by score
    result = (
        await db.table("profiles")
        .select(
            "id, username, display_name, avatar_url, bio, location, languages, aura_scores(total_score, badge_tier)"
        )
        .eq("visible_to_orgs", True)
        .eq("is_public", True)
        .in_("account_type", ["professional", "volunteer"])
        .order("aura_scores(total_score)", desc=True, nulls_last=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    professionals: list[DiscoverableProfessional] = []
    for row in result.data or []:
        aura = row.get("aura_scores")
        # aura_scores is a list (one-to-many join result) — take first visible entry
        aura_row = aura[0] if isinstance(aura, list) and aura else aura if isinstance(aura, dict) else None
        professionals.append(
            DiscoverableProfessional(
                id=row["id"],
                username=row["username"],
                display_name=_anonymize_name(row.get("display_name")),  # SEC-03: never leak full name
                avatar_url=row.get("avatar_url"),
                bio=row.get("bio"),
                location=row.get("location"),
                languages=row.get("languages") or [],
                total_score=float(aura_row["total_score"])
                if aura_row and aura_row.get("total_score") is not None
                else None,
                badge_tier=aura_row.get("badge_tier") if aura_row else None,
            )
        )

    return professionals


@router.get("/{username}", response_model=PublicProfileResponse)
@limiter.limit(RATE_DISCOVERY)  # SEC-Q2: tighter limit — 10/min prevents username enumeration
async def get_public_profile(
    request: Request,
    username: str,
    db: SupabaseAdmin,
) -> PublicProfileResponse:
    """Get a public profile by username — no auth required."""
    result = (
        await db.table("profiles")
        .select(
            "id, username, display_name, avatar_url, bio, location, languages, "
            "badge_issued_at, registration_number, registration_tier"
        )
        .eq("username", username)
        .eq("is_public", True)
        .maybe_single()
        .execute()
    )
    if not result or not result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Profile not found"},
        )

    # GROW-M03: compute percentile rank — % of public users with a lower AURA score.
    # Two cheap COUNT queries; skipped entirely if the user has no aura_scores row.
    percentile_rank: float | None = None
    try:
        professional_id = result.data["id"]
        score_row = (
            await db.table("aura_scores")
            .select("total_score")
            .eq("volunteer_id", professional_id)
            .maybe_single()
            .execute()
        )
        if score_row.data and score_row.data.get("total_score") is not None:
            user_score: float = float(score_row.data["total_score"])
            # Count users with a lower score (public professionals only)
            # SEC-Q2: filter by visibility="public" so private/badge_only scores
            # don't leak aggregate platform stats via percentile_rank.
            lower_resp = (
                await db.table("aura_scores")
                .select("volunteer_id", count="exact")
                .lt("total_score", user_score)
                .eq("visibility", "public")
                .execute()
            )
            total_resp = (
                await db.table("aura_scores").select("volunteer_id", count="exact").eq("visibility", "public").execute()
            )
            lower_count: int = lower_resp.count or 0
            total_count: int = total_resp.count or 0
            if total_count > 0:
                percentile_rank = round((lower_count / total_count) * 100, 1)
    except Exception as exc:
        logger.warning("percentile_rank computation failed (non-fatal)", error=str(exc)[:200])

    return PublicProfileResponse(**result.data, percentile_rank=percentile_rank)


@router.post("/{username}/view", status_code=204)
@limiter.limit("20/minute")
async def record_profile_view(
    request: Request,
    username: str,
    db: SupabaseAdmin,
    user_id: CurrentUserId,
) -> None:
    """Record that an authenticated org viewed a professional's profile.

    Sends an `org_view` notification to the professional — deduped: at most 1 notification
    per (org, professional) pair per 24 hours. Silently returns 204 for non-org callers
    (no error, no notification — safe to call from any authenticated user).

    Security: org identity comes from JWT, never from request body.
    """
    # Verify caller is an org (dual check: JWT + DB)
    caller = (
        await db.table("profiles")
        .select("account_type, display_name, username")
        .eq("id", str(user_id))
        .maybe_single()
        .execute()
    )
    if not caller.data or caller.data.get("account_type") != "organization":
        return  # silently succeed — no error for professional-to-professional page views

    # Look up the professional being viewed
    target_profile = (
        await db.table("profiles")
        .select("id, display_name")
        .eq("username", username)
        .eq("is_public", True)
        .maybe_single()
        .execute()
    )
    if not target_profile.data:
        return  # professional deleted or set private — no notification

    professional_id = target_profile.data["id"]

    # Don't notify orgs viewing themselves
    if str(user_id) == professional_id:
        return

    # Dedup: skip if this org already sent an org_view notification for this professional in last 24h
    since = (datetime.now(tz=UTC) - timedelta(hours=24)).isoformat()
    existing = (
        await db.table("notifications")
        .select("id")
        .eq("user_id", professional_id)
        .eq("type", "org_view")
        .eq("reference_id", str(user_id))
        .gte("created_at", since)
        .execute()
    )
    if existing.data:
        return  # already notified — don't spam

    # Fire-and-forget notification
    org_name = caller.data.get("display_name") or caller.data.get("username") or "An organization"
    await notify(
        db,
        user_id=professional_id,
        notification_type="org_view",
        title=f"{org_name} viewed your profile",
        body="Organizations can request introductions if they're interested.",
        reference_id=str(user_id),  # org's user_id — used for dedup key
    )
    logger.info(
        "org_view notification sent",
        org_id=user_id,
        professional_id=professional_id,
    )


@router.get("/me/views")
@limiter.limit(RATE_PROFILE_WRITE)
async def get_my_profile_views(
    request: Request,
    db: SupabaseUser,
    user_id: CurrentUserId,
) -> dict:
    """Count how many orgs viewed my profile (based on org_view notifications).

    Returns: total views, views this week, list of org names who viewed (last 10).
    Professional-only — orgs see their own dashboard stats elsewhere.
    """
    now = datetime.now(tz=UTC)
    week_ago = (now - timedelta(days=7)).isoformat()

    # Total org_view notifications (= unique org views after dedup)
    total_result = (
        await db.table("notifications")
        .select("id", count="exact")
        .eq("user_id", str(user_id))
        .eq("type", "org_view")
        .execute()
    )
    total_views = total_result.count or 0

    # This week
    week_result = (
        await db.table("notifications")
        .select("id", count="exact")
        .eq("user_id", str(user_id))
        .eq("type", "org_view")
        .gte("created_at", week_ago)
        .execute()
    )
    week_views = week_result.count or 0

    # Recent viewers (last 10 — show org names)
    recent_result = (
        await db.table("notifications")
        .select("title, created_at")
        .eq("user_id", str(user_id))
        .eq("type", "org_view")
        .order("created_at", desc=True)
        .limit(10)
        .execute()
    )
    recent_viewers = [
        {"name": n.get("title", "").replace(" viewed your profile", ""), "at": n.get("created_at")}
        for n in (recent_result.data or [])
    ]

    return {"data": {"total_views": total_views, "week_views": week_views, "recent_viewers": recent_viewers}}


@router.get("/me/verifications")
@limiter.limit(RATE_PROFILE_WRITE)
async def get_my_verifications(
    request: Request,
    db: SupabaseUser,
    user_id: CurrentUserId,
) -> dict:
    """Return coordinator ratings for this professional — these are expert verifications.

    Data source: event_registrations where coordinator_rating is not null.
    Joins with events (for event name) and profiles (for coordinator name/org).
    """
    # Get all event registrations where this professional was rated by a coordinator
    regs_result = (
        await db.table("event_registrations")
        .select("id, event_id, coordinator_rating, coordinator_feedback, created_at")
        .eq("volunteer_id", str(user_id))
        .not_.is_("coordinator_rating", "null")
        .order("created_at", desc=True)
        .limit(20)
        .execute()
    )

    verifications = []
    for reg in regs_result.data or []:
        # Get event details
        event_result = (
            await db.table("events").select("title, organizer_id").eq("id", reg["event_id"]).maybe_single().execute()
        )
        event = event_result.data or {}

        # Get organizer profile
        organizer_name = "Coordinator"
        organizer_org = None
        if event.get("organizer_id"):
            org_result = (
                await db.table("profiles")
                .select("display_name, username")
                .eq("id", event["organizer_id"])
                .maybe_single()
                .execute()
            )
            if org_result.data:
                organizer_name = org_result.data.get("display_name") or org_result.data.get("username") or "Coordinator"

        verifications.append(
            {
                "id": reg["id"],
                "verifier_name": organizer_name,
                "verifier_org": organizer_org,
                "competency_id": "event_performance",
                "rating": reg.get("coordinator_rating", 0),
                "comment": reg.get("coordinator_feedback"),
                "verified_at": reg.get("created_at", ""),
            }
        )

    return {"data": verifications}
