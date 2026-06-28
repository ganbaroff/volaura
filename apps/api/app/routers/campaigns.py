"""Screening campaigns — B2B org screening flow.

Org creates a campaign (vacancy) -> gets one shareable invite link ->
candidates join via the link and receive assigned assessments ->
org reads a ranked report of verified candidates.

Decision: memory/decisions/2026-06-11-b2b-pivot.md
"""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from app.config import settings
from app.deps import CurrentUserId, SupabaseAdmin
from app.middleware.rate_limit import limiter
from app.schemas.campaign import (
    CampaignCreate,
    CampaignJoinResponse,
    CampaignReportResponse,
    CampaignResponse,
    CampaignUpdate,
    CandidateReportRow,
    JoinedSession,
    PublicCampaignResponse,
)
from app.services.org_entitlements import org_has_report_access

router = APIRouter(prefix="/campaigns", tags=["Screening Campaigns"])

RATE_DEFAULT = "30/minute"
RATE_WRITE = "10/minute"
RATE_PUBLIC = "60/minute"


async def _get_owned_org(db_admin: SupabaseAdmin, user_id: str) -> dict:
    """Return the org owned by the caller or raise 403."""
    org_result = (
        await db_admin.table("organizations")
        .select("id, name, logo_url")
        .eq("owner_id", user_id)
        .maybe_single()
        .execute()
    )
    if not org_result or not org_result.data:
        raise HTTPException(
            status_code=403,
            detail={"code": "NOT_ORG_OWNER", "message": "You must own an organization to manage campaigns"},
        )
    return org_result.data


async def _get_campaign_by_token(db_admin: SupabaseAdmin, token: str) -> dict:
    if not token or len(token) > 64:
        raise HTTPException(status_code=422, detail={"code": "INVALID_TOKEN", "message": "Invalid invite token"})
    result = await db_admin.table("screening_campaigns").select("*").eq("invite_token", token).maybe_single().execute()
    if not result or not result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "CAMPAIGN_NOT_FOUND", "message": "This invite link is not valid"},
        )
    return result.data


async def _candidate_count(db_admin: SupabaseAdmin, campaign_id: str) -> int:
    result = (
        await db_admin.table("campaign_candidates").select("id", count="exact").eq("campaign_id", campaign_id).execute()
    )
    return result.count or 0


@router.post("", response_model=CampaignResponse, status_code=201)
@limiter.limit(RATE_WRITE)
async def create_campaign(
    request: Request,
    payload: CampaignCreate,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
) -> CampaignResponse:
    """Create a screening campaign and its shareable invite token."""
    org = await _get_owned_org(db_admin, user_id)

    # Validate competency slugs against DB
    comp_result = await db_admin.table("competencies").select("slug").eq("is_active", True).execute()
    valid_slugs = {c["slug"] for c in (comp_result.data or [])}
    invalid = [s for s in payload.competency_slugs if s not in valid_slugs]
    if invalid:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_COMPETENCY", "message": f"Unknown competencies: {', '.join(invalid)}"},
        )

    campaign_id = str(uuid.uuid4())
    invite_token = secrets.token_urlsafe(18)

    insert_result = (
        await db_admin.table("screening_campaigns")
        .insert(
            {
                "id": campaign_id,
                "org_id": org["id"],
                "created_by": user_id,
                "title": payload.title,
                "description": payload.description,
                "competency_slugs": payload.competency_slugs,
                "invite_token": invite_token,
                "status": "active",
                "deadline_days": payload.deadline_days,
                "candidate_cap": payload.candidate_cap,
            }
        )
        .execute()
    )
    if not insert_result.data:
        raise HTTPException(status_code=500, detail={"code": "CREATE_FAILED", "message": "Could not create campaign"})

    logger.info("Campaign created", campaign_id=campaign_id, org_id=org["id"], title=payload.title)
    return CampaignResponse(**insert_result.data[0])


@router.get("", response_model=list[CampaignResponse])
@limiter.limit(RATE_DEFAULT)
async def list_my_campaigns(
    request: Request,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
) -> list[CampaignResponse]:
    """List campaigns for the caller's organization with candidate counts."""
    org = await _get_owned_org(db_admin, user_id)

    campaigns_result = (
        await db_admin.table("screening_campaigns")
        .select("*")
        .eq("org_id", org["id"])
        .order("created_at", desc=True)
        .limit(100)
        .execute()
    )
    campaigns = campaigns_result.data or []
    if not campaigns:
        return []

    campaign_ids = [c["id"] for c in campaigns]

    candidates_result = (
        await db_admin.table("campaign_candidates").select("campaign_id").in_("campaign_id", campaign_ids).execute()
    )
    counts: dict[str, int] = {}
    for row in candidates_result.data or []:
        counts[row["campaign_id"]] = counts.get(row["campaign_id"], 0) + 1

    sessions_result = (
        await db_admin.table("assessment_sessions")
        .select("campaign_id, volunteer_id, status")
        .in_("campaign_id", campaign_ids)
        .execute()
    )
    completed: dict[str, set[str]] = {}
    for row in sessions_result.data or []:
        if row["status"] == "completed":
            completed.setdefault(row["campaign_id"], set()).add(row["volunteer_id"])

    return [
        CampaignResponse(
            **c,
            candidate_count=counts.get(c["id"], 0),
            completed_count=len(completed.get(c["id"], set())),
        )
        for c in campaigns
    ]


@router.patch("/{campaign_id}", response_model=CampaignResponse)
@limiter.limit(RATE_WRITE)
async def update_campaign(
    request: Request,
    campaign_id: str,
    payload: CampaignUpdate,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
) -> CampaignResponse:
    """Close or archive a campaign (org owner only)."""
    _validate_uuid(campaign_id)
    org = await _get_owned_org(db_admin, user_id)

    update_result = (
        await db_admin.table("screening_campaigns")
        .update({"status": payload.status, "updated_at": datetime.now(UTC).isoformat()})
        .eq("id", campaign_id)
        .eq("org_id", org["id"])
        .execute()
    )
    if not update_result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "CAMPAIGN_NOT_FOUND", "message": "Campaign not found"},
        )
    return CampaignResponse(**update_result.data[0])


@router.get("/public/{token}", response_model=PublicCampaignResponse)
@limiter.limit(RATE_PUBLIC)
async def get_public_campaign(
    request: Request,
    token: str,
    db_admin: SupabaseAdmin,
) -> PublicCampaignResponse:
    """Public campaign info for the invite landing page. No auth."""
    campaign = await _get_campaign_by_token(db_admin, token)

    org_result = (
        await db_admin.table("organizations")
        .select("name, logo_url")
        .eq("id", campaign["org_id"])
        .maybe_single()
        .execute()
    )
    org = org_result.data if org_result and org_result.data else {}

    count = await _candidate_count(db_admin, campaign["id"])

    return PublicCampaignResponse(
        title=campaign["title"],
        description=campaign.get("description"),
        org_name=org.get("name", ""),
        org_logo_url=org.get("logo_url"),
        competency_slugs=campaign["competency_slugs"],
        status=campaign["status"],
        deadline_days=campaign["deadline_days"],
        is_full=count >= campaign["candidate_cap"],
    )


@router.post("/public/{token}/join", response_model=CampaignJoinResponse)
@limiter.limit(RATE_WRITE)
async def join_campaign(
    request: Request,
    token: str,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
) -> CampaignJoinResponse:
    """Join a campaign via invite link: creates assigned assessment sessions."""
    campaign = await _get_campaign_by_token(db_admin, token)

    if campaign["status"] != "active":
        raise HTTPException(
            status_code=409,
            detail={"code": "CAMPAIGN_CLOSED", "message": "This screening is no longer accepting candidates"},
        )

    existing_membership = (
        await db_admin.table("campaign_candidates")
        .select("id")
        .eq("campaign_id", campaign["id"])
        .eq("professional_id", user_id)
        .maybe_single()
        .execute()
    )
    already_joined = bool(existing_membership and existing_membership.data)

    if not already_joined:
        count = await _candidate_count(db_admin, campaign["id"])
        if count >= campaign["candidate_cap"]:
            raise HTTPException(
                status_code=409,
                detail={"code": "CAMPAIGN_FULL", "message": "This screening has reached its candidate limit"},
            )
        await (
            db_admin.table("campaign_candidates")
            .insert({"campaign_id": campaign["id"], "professional_id": user_id})
            .execute()
        )

    # Map slugs -> competency ids
    comp_result = (
        await db_admin.table("competencies").select("id, slug").in_("slug", campaign["competency_slugs"]).execute()
    )
    slug_by_id = {c["id"]: c["slug"] for c in (comp_result.data or [])}

    # Existing sessions for this user in this campaign (idempotent join)
    existing_sessions = (
        await db_admin.table("assessment_sessions")
        .select("id, competency_id, status")
        .eq("volunteer_id", user_id)
        .eq("campaign_id", campaign["id"])
        .execute()
    )
    existing_by_comp = {s["competency_id"]: s for s in (existing_sessions.data or [])}

    deadline = datetime.now(UTC) + timedelta(days=campaign["deadline_days"])
    sessions: list[JoinedSession] = []

    for comp_id, slug in slug_by_id.items():
        if comp_id in existing_by_comp:
            s = existing_by_comp[comp_id]
            sessions.append(JoinedSession(session_id=s["id"], competency_slug=slug, status=s["status"]))
            continue

        session_id = str(uuid.uuid4())
        await (
            db_admin.table("assessment_sessions")
            .insert(
                {
                    "id": session_id,
                    "volunteer_id": user_id,
                    "competency_id": comp_id,
                    "status": "assigned",
                    "assigned_by_org_id": campaign["org_id"],
                    "assigned_at": datetime.now(UTC).isoformat(),
                    "deadline": deadline.isoformat(),
                    "assignment_message": campaign["title"],
                    "campaign_id": campaign["id"],
                    "theta_estimate": 0.0,
                    "theta_se": 1.5,
                    "answers": {},
                }
            )
            .execute()
        )
        sessions.append(JoinedSession(session_id=session_id, competency_slug=slug, status="assigned"))

    logger.info(
        "Candidate joined campaign",
        campaign_id=campaign["id"],
        user_id=user_id,
        already_joined=already_joined,
        sessions=len(sessions),
    )

    return CampaignJoinResponse(
        campaign_id=campaign["id"],
        already_joined=already_joined,
        sessions=sessions,
    )


@router.get("/{campaign_id}/report", response_model=CampaignReportResponse)
@limiter.limit(RATE_DEFAULT)
async def get_campaign_report(
    request: Request,
    campaign_id: str,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
) -> CampaignReportResponse:
    """Ranked candidate report for a campaign (org owner only)."""
    _validate_uuid(campaign_id)
    org = await _get_owned_org(db_admin, user_id)

    campaign_result = (
        await db_admin.table("screening_campaigns")
        .select("*")
        .eq("id", campaign_id)
        .eq("org_id", org["id"])
        .maybe_single()
        .execute()
    )
    if not campaign_result or not campaign_result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "CAMPAIGN_NOT_FOUND", "message": "Campaign not found"},
        )
    campaign = campaign_result.data
    campaign_slugs: list[str] = campaign["competency_slugs"]

    # ── Paywall gate (refounding pivot 2026-06-11) ────────────────────────────
    # The ranked report is the paid B2B deliverable. When org_billing_enabled is
    # False the report is free (design-partner phase). When True, the org needs an
    # active subscription OR a one-time unlock for this campaign — otherwise 402.
    if settings.org_billing_enabled and not await org_has_report_access(db_admin, org["id"], campaign_id):
        raise HTTPException(
            status_code=402,
            detail={
                "code": "PAYMENT_REQUIRED",
                "message": "Unlock this campaign's ranked report to view verified candidates.",
                "campaign_id": campaign_id,
                "subscribe_url": "/api/org-billing/subscribe",
                "unlock_url": f"/api/org-billing/campaigns/{campaign_id}/unlock",
            },
        )

    members_result = (
        await db_admin.table("campaign_candidates")
        .select("professional_id, joined_at")
        .eq("campaign_id", campaign_id)
        .order("joined_at")
        .limit(2000)
        .execute()
    )
    members = members_result.data or []
    if not members:
        return CampaignReportResponse(
            campaign=CampaignResponse(**campaign, candidate_count=0, completed_count=0),
            candidates=[],
        )

    member_ids = [m["professional_id"] for m in members]
    joined_at_by_id = {m["professional_id"]: m["joined_at"] for m in members}

    profiles_result = (
        await db_admin.table("profiles")
        .select("id, display_name, username, avatar_url")
        .in_("id", member_ids)
        .execute()
    )
    profile_by_id = {p["id"]: p for p in (profiles_result.data or [])}

    aura_result = (
        await db_admin.table("aura_scores")
        .select("volunteer_id, badge_tier, competency_scores")
        .in_("volunteer_id", member_ids)
        .execute()
    )
    aura_by_id = {a["volunteer_id"]: a for a in (aura_result.data or [])}

    sessions_result = (
        await db_admin.table("assessment_sessions")
        .select("volunteer_id, status")
        .eq("campaign_id", campaign_id)
        .in_("volunteer_id", member_ids)
        .execute()
    )
    assigned_by_id: dict[str, int] = {}
    completed_by_id: dict[str, int] = {}
    for s in sessions_result.data or []:
        vid = s["volunteer_id"]
        assigned_by_id[vid] = assigned_by_id.get(vid, 0) + 1
        if s["status"] == "completed":
            completed_by_id[vid] = completed_by_id.get(vid, 0) + 1

    rows: list[CandidateReportRow] = []
    for vid in member_ids:
        profile = profile_by_id.get(vid, {})
        aura = aura_by_id.get(vid, {})
        all_scores = aura.get("competency_scores") or {}
        relevant = {
            slug: float(all_scores[slug]) for slug in campaign_slugs if isinstance(all_scores.get(slug), (int, float))
        }
        campaign_score = round(sum(relevant.values()) / len(relevant), 1) if relevant else None

        rows.append(
            CandidateReportRow(
                professional_id=vid,
                display_name=profile.get("display_name"),
                username=profile.get("username"),
                avatar_url=profile.get("avatar_url"),
                joined_at=joined_at_by_id[vid],
                completed_sessions=completed_by_id.get(vid, 0),
                assigned_sessions=assigned_by_id.get(vid, 0),
                campaign_score=campaign_score,
                badge_tier=aura.get("badge_tier"),
                competency_scores=relevant,
            )
        )

    # Rank: most completed first, then campaign score desc, then earliest joined
    rows.sort(
        key=lambda r: (
            -r.completed_sessions,
            -(r.campaign_score if r.campaign_score is not None else -1.0),
            r.joined_at,
        )
    )

    completed_candidates = len([r for r in rows if r.assigned_sessions and r.completed_sessions == r.assigned_sessions])

    return CampaignReportResponse(
        campaign=CampaignResponse(**campaign, candidate_count=len(rows), completed_count=completed_candidates),
        candidates=rows,
    )


def _validate_uuid(value: str) -> None:
    try:
        uuid.UUID(value)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=422, detail={"code": "INVALID_UUID", "message": "Invalid id format"})
