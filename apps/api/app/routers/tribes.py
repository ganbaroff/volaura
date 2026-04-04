"""Tribe Streaks endpoints.

Anti-harassment design: all writes via service_role only (matching service).
Users can READ their tribe, SEND kudos, OPT OUT, and REQUEST renewal.
No user can create or modify tribe membership directly.

Security Agent checklist (approved before code):
  ✅ Matching uses service_role only
  ✅ Opted-out members invisible in GET /me
  ✅ Kudos count via SECURITY DEFINER RPC (no direct kudos SELECT)
  ✅ tribe_member_history never user-readable
  ✅ No score data exposed — activity status only (binary active/inactive)
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException, Request
from loguru import logger

from app.config import settings
from app.deps import CurrentUserId, SupabaseAdmin, SupabaseUser
from app.middleware.rate_limit import limiter, RATE_DEFAULT, RATE_PROFILE_WRITE
from app.schemas.tribes import (
    KudosResponse,
    OptOutResponse,
    PoolStatusOut,
    RenewalResponse,
    TribeMatchPreview,
    TribeOut,
    TribeMemberStatus,
    TribeStreakOut,
)
from app.services.tribe_matching import run_tribe_matching
from app.services.tribe_streak_tracker import record_assessment_activity, update_weekly_streaks

router = APIRouter(prefix="/tribes", tags=["Tribes"])


# ── GET /tribes/me ─────────────────────────────────────────────────────────────

@router.get("/me", response_model=TribeOut | None)
@limiter.limit(RATE_DEFAULT)
async def get_my_tribe(
    request: Request,
    db: SupabaseUser,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
) -> TribeOut | None:
    """Return the user's current active tribe.

    Returns null if user is not in an active tribe.
    Members are returned with activity status only (no scores — anti-harassment).
    Opted-out members are invisible.
    """
    # Find user's active tribe membership
    membership_result = await db.table("tribe_members").select(
        "tribe_id, tribes(id, expires_at, status)"
    ).eq("user_id", str(user_id)).is_("opt_out_at", None).maybe_single().execute()

    if not membership_result.data:
        return None

    tribe_data = membership_result.data
    tribe_info = tribe_data.get("tribes") or {}
    tribe_id = tribe_data["tribe_id"]

    if tribe_info.get("status") != "active":
        return None

    # Get all active members (excluding opted-out)
    members_result = await db_admin.table("tribe_members").select(
        "user_id, profiles(display_name, avatar_url)"
    ).eq("tribe_id", tribe_id).is_("opt_out_at", None).execute()

    # Determine who was active this ISO week
    current_week = _iso_week(datetime.now(timezone.utc))
    members: list[TribeMemberStatus] = []

    for m in (members_result.data or []):
        member_uid = m["user_id"]
        profile = m.get("profiles") or {}

        # Check activity for this week via tribe_streaks
        streak_result = await db_admin.table("tribe_streaks").select(
            "last_activity_week"
        ).eq("user_id", member_uid).maybe_single().execute()

        active_this_week = (
            streak_result.data is not None
            and streak_result.data.get("last_activity_week") == current_week
        )

        members.append(TribeMemberStatus(
            user_id=member_uid,
            display_name=profile.get("display_name") or "Member",
            avatar_url=profile.get("avatar_url"),
            active_this_week=active_this_week,
        ))

    # Get kudos count via SECURITY DEFINER RPC (anti-harassment: no direct kudos SELECT)
    try:
        kudos_result = await db.rpc("get_tribe_kudos_count", {"p_tribe_id": tribe_id}).execute()
        kudos_count = kudos_result.data or 0
    except Exception:
        kudos_count = 0  # fail silently — kudos are optional

    # Check if user already requested renewal
    renewal_result = await db.table("tribe_renewal_requests").select("tribe_id").eq(
        "tribe_id", tribe_id
    ).eq("user_id", str(user_id)).maybe_single().execute()
    renewal_requested = renewal_result.data is not None

    return TribeOut(
        tribe_id=tribe_id,
        expires_at=tribe_info["expires_at"],
        status=tribe_info["status"],
        members=members,
        kudos_count_this_week=kudos_count,
        renewal_requested=renewal_requested,
    )


# ── GET /tribes/me/streak ──────────────────────────────────────────────────────

@router.get("/me/streak", response_model=TribeStreakOut | None)
@limiter.limit(RATE_DEFAULT)
async def get_my_streak(
    request: Request,
    db: SupabaseUser,
    user_id: CurrentUserId,
) -> TribeStreakOut | None:
    """Return the user's personal tribe streak.

    Visible only to the user themselves (RLS: auth.uid() = user_id).
    consecutive_misses_count is used by frontend for crystal fade animation.
    """
    streak_result = await db.table("tribe_streaks").select("*").eq("user_id", str(user_id)).maybe_single().execute()

    if not streak_result.data:
        return None

    data = streak_result.data
    consecutive = data.get("consecutive_misses_count", 0)

    return TribeStreakOut(
        current_streak=data["current_streak"],
        longest_streak=data["longest_streak"],
        last_activity_week=data.get("last_activity_week"),
        consecutive_misses_count=consecutive,
        crystal_fade_level=min(consecutive, 2),
    )


# ── POST /tribes/me/kudos ──────────────────────────────────────────────────────

@router.post("/me/kudos", response_model=KudosResponse)
@limiter.limit("5/minute")  # anti-spam: 5 kudos/minute max
async def send_kudos(
    request: Request,
    db: SupabaseUser,
    user_id: CurrentUserId,
) -> KudosResponse:
    """Send anonymous kudos to your tribe.

    Security: tribe_id comes from the user's own active membership (not user-supplied).
    No sender_id stored. RLS INSERT policy verifies active membership.
    Q1: count=0 → frontend shows "Be the first to send kudos" (handled in GET /me).
    """
    # Get the user's current tribe_id (from their membership, not request body)
    membership = await db.table("tribe_members").select("tribe_id").eq(
        "user_id", str(user_id)
    ).is_("opt_out_at", None).maybe_single().execute()

    if not membership.data:
        raise HTTPException(status_code=400, detail={"code": "NOT_IN_TRIBE", "message": "You are not in an active tribe."})

    tribe_id = membership.data["tribe_id"]

    # INSERT via user JWT — RLS policy verifies active membership
    await db.table("tribe_kudos").insert({"tribe_id": tribe_id}).execute()

    return KudosResponse()


# ── POST /tribes/opt-out ───────────────────────────────────────────────────────

@router.post("/opt-out", response_model=OptOutResponse)
@limiter.limit(RATE_PROFILE_WRITE)
async def opt_out_of_tribe(
    request: Request,
    db: SupabaseUser,
    user_id: CurrentUserId,
) -> OptOutResponse:
    """Leave the current tribe silently.

    Q3: 2-person tribe continues until cycle end — remaining members are NOT notified.
    Opted-out member's streak is NOT reset (streak is personal, tribe-independent).
    No "X left the tribe" notification. Departed members are simply invisible in GET /me.
    """
    membership = await db.table("tribe_members").select("tribe_id").eq(
        "user_id", str(user_id)
    ).is_("opt_out_at", None).maybe_single().execute()

    if not membership.data:
        raise HTTPException(status_code=400, detail={"code": "NOT_IN_TRIBE", "message": "You are not in an active tribe."})

    now_iso = datetime.now(timezone.utc).isoformat()

    # Soft opt-out: set opt_out_at (RLS policy allows user to update own row)
    await db.table("tribe_members").update({"opt_out_at": now_iso}).eq(
        "tribe_id", membership.data["tribe_id"]
    ).eq("user_id", str(user_id)).execute()

    # Clean up any pending renewal request from this user
    await db.table("tribe_renewal_requests").delete().eq(
        "tribe_id", membership.data["tribe_id"]
    ).eq("user_id", str(user_id)).execute()

    logger.info("User {uid} opted out of tribe {tid}", uid=str(user_id), tid=membership.data["tribe_id"])

    # NOTE: streak is NOT touched here (approved change #10: opt-out ≠ streak penalty)
    return OptOutResponse()


# ── POST /tribes/renew ────────────────────────────────────────────────────────

@router.post("/renew", response_model=RenewalResponse)
@limiter.limit(RATE_PROFILE_WRITE)
async def request_tribe_renewal(
    request: Request,
    db: SupabaseUser,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
) -> RenewalResponse:
    """Request to renew the current tribe for another 4-week cycle.

    If all active members request renewal → matching service will extend tribe on next run.
    """
    membership = await db.table("tribe_members").select("tribe_id").eq(
        "user_id", str(user_id)
    ).is_("opt_out_at", None).maybe_single().execute()

    if not membership.data:
        raise HTTPException(status_code=400, detail={"code": "NOT_IN_TRIBE", "message": "You are not in an active tribe."})

    tribe_id = membership.data["tribe_id"]

    # Upsert renewal request (idempotent — safe to call multiple times)
    await db.table("tribe_renewal_requests").upsert({
        "tribe_id": tribe_id,
        "user_id": str(user_id),
    }).execute()

    # Check if all active members have now requested
    active_members_result = await db_admin.table("tribe_members").select("user_id").eq(
        "tribe_id", tribe_id
    ).is_("opt_out_at", None).execute()
    active_count = len(active_members_result.data or [])

    renewals_result = await db_admin.table("tribe_renewal_requests").select("user_id").eq("tribe_id", tribe_id).execute()
    renewal_count = len(renewals_result.data or [])

    all_requested = renewal_count >= active_count

    message = (
        "Your tribe will be renewed for another 4 weeks!"
        if all_requested
        else f"Renewal requested. Waiting for {active_count - renewal_count} more member(s)."
    )

    return RenewalResponse(
        renewal_requested=True,
        message=message,
        all_members_requested=all_requested,
    )


# ── POST /tribes/join-pool ────────────────────────────────────────────────────

@router.post("/join-pool", response_model=TribeMatchPreview)
@limiter.limit(RATE_PROFILE_WRITE)
async def join_matching_pool(
    request: Request,
    db: SupabaseUser,
    user_id: CurrentUserId,
) -> TribeMatchPreview:
    """Opt into tribe matching (user signals they want to be matched).

    Matching runs daily — user will be matched within 24 hours.
    Eligibility: must have AURA score > 0 and visible_to_orgs = True.
    If already in a tribe, returns current tribe info direction.
    """
    # Check already in tribe
    membership = await db.table("tribe_members").select("tribe_id").eq(
        "user_id", str(user_id)
    ).is_("opt_out_at", None).maybe_single().execute()

    if membership.data:
        raise HTTPException(
            status_code=400,
            detail={"code": "ALREADY_IN_TRIBE", "message": "You are already in an active tribe. Check /tribes/me."},
        )

    # Check eligibility: visible_to_orgs
    profile = await db.table("profiles").select("visible_to_orgs").eq("id", str(user_id)).maybe_single().execute()
    if not profile.data or not profile.data.get("visible_to_orgs"):
        raise HTTPException(
            status_code=400,
            detail={"code": "PROFILE_NOT_VISIBLE", "message": "Enable profile visibility to join tribe matching."},
        )

    # Upsert into tribe_matching_pool (idempotent — safe to call twice)
    await db.table("tribe_matching_pool").upsert({
        "user_id": str(user_id),
    }).execute()

    logger.info("User {uid} joined matching pool", uid=str(user_id))
    return TribeMatchPreview()


# ── GET /tribes/me/pool-status ─────────────────────────────────────────────────

@router.get("/me/pool-status", response_model=PoolStatusOut)
@limiter.limit(RATE_DEFAULT)
async def get_pool_status(
    request: Request,
    db: SupabaseUser,
    user_id: CurrentUserId,
) -> PoolStatusOut:
    """Return whether the user is currently waiting in the matching pool.

    Frontend uses this to show 'Finding your tribe...' across page refreshes
    instead of re-showing the join CTA after the user already clicked it.
    """
    result = await db.table("tribe_matching_pool").select("joined_at").eq(
        "user_id", str(user_id)
    ).maybe_single().execute()

    if not result or not result.data:
        return PoolStatusOut(in_pool=False)

    return PoolStatusOut(in_pool=True, joined_at=result.data["joined_at"])


# ── Cron endpoints (GitHub Actions — internal, secret-gated) ──────────────────

def _verify_cron_secret(x_cron_secret: str | None) -> None:
    """Raise 403 if CRON_SECRET env var is unset or header doesn't match."""
    if not settings.cron_secret or x_cron_secret != settings.cron_secret:
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Invalid or missing cron secret."})


@router.post("/cron/run-matching", include_in_schema=False)
async def cron_run_matching(
    request: Request,
    db_admin: SupabaseAdmin,
    x_cron_secret: str | None = Header(default=None),
) -> dict:
    """Trigger tribe matching. Called by GitHub Actions daily at 07:00 UTC.

    Guards: CRON_SECRET header must match Railway env var.
    """
    _verify_cron_secret(x_cron_secret)
    result = await run_tribe_matching(db=db_admin)
    logger.info("Tribe matching cron complete: {result}", result=result)
    return {"ok": True, **result}


@router.post("/cron/run-streak-update", include_in_schema=False)
async def cron_run_streak_update(
    request: Request,
    db_admin: SupabaseAdmin,
    x_cron_secret: str | None = Header(default=None),
) -> dict:
    """Update weekly tribe streaks. Called by GitHub Actions Sunday 23:50 UTC.

    Guards: CRON_SECRET header must match Railway env var.
    """
    _verify_cron_secret(x_cron_secret)
    result = await update_weekly_streaks(db=db_admin)
    logger.info("Tribe streak update cron complete: {result}", result=result)
    return {"ok": True, **result}


# ── Internal helper ────────────────────────────────────────────────────────────

def _iso_week(dt: datetime) -> str:
    iso = dt.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"
