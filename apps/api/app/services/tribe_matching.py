"""Tribe Streaks — Matching Service.

Runs daily via GitHub Actions cron (.github/workflows/tribe-matching.yml).
Uses SupabaseAdmin (service_role) exclusively — never exposed to user JWT.

Algorithm:
  1. Find users eligible for matching (active, no current tribe, opted in)
  2. Sort by AURA score
  3. Cluster by score proximity (±15 points)
  4. Match in triplets within each cluster
  5. Create tribe + tribe_members + tribe_streaks rows
  6. Record co-member history (prevents repeat pairing)
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

from loguru import logger

# ── Constants ──────────────────────────────────────────────────────────────────
TRIBE_SIZE = 3
SCORE_PROXIMITY = 15.0       # max AURA score difference within a tribe
TRIBE_DURATION_WEEKS = 4     # 4-week cycle
MATCHING_POOL_DAYS = 30      # user must have an assessment in last 30 days to be eligible
RENEWAL_THRESHOLD = 3        # all 3 members must request renewal to extend


# ── Public entry points ────────────────────────────────────────────────────────

async def run_tribe_matching(db) -> dict:
    """Main entry point for GitHub Actions cron.

    Args:
        db: SupabaseAdmin client (service_role — RLS bypassed, required for matching)

    Returns:
        Dict with tribes_created, users_matched, users_renewed, users_skipped
    """
    logger.info("Tribe matching run started")
    now = datetime.now(timezone.utc)

    # Step 1: Expire tribes whose time is up
    expired_count = await _expire_old_tribes(db, now)
    logger.info("Expired {n} tribes", n=expired_count)

    # Step 2: Renew tribes where all members requested renewal
    renewed_count = await _renew_requesting_tribes(db, now)
    logger.info("Renewed {n} tribes", n=renewed_count)

    # Step 3: Find users eligible for new matching
    candidates = await _get_matching_candidates(db, now)
    logger.info("Found {n} matching candidates", n=len(candidates))

    if len(candidates) < 2:
        logger.info("Not enough candidates for matching (need ≥2)")
        return {"tribes_created": 0, "users_matched": 0, "users_renewed": renewed_count, "users_skipped": len(candidates)}

    # Step 4: Match into triplets (or pairs if odd remainder)
    groups = _cluster_and_match(candidates)
    logger.info("Formed {n} groups", n=len(groups))

    # Step 5: Create tribes in DB
    tribes_created = 0
    users_matched = 0
    for group in groups:
        if len(group) < 2:
            continue
        try:
            await _create_tribe(db, group, now)
            tribes_created += 1
            users_matched += len(group)
        except Exception as e:
            logger.error("Failed to create tribe for group {g}: {e}", g=[u["user_id"] for u in group], e=str(e))

    logger.info("Tribe matching complete: {t} tribes, {u} users matched", t=tribes_created, u=users_matched)
    return {
        "tribes_created": tribes_created,
        "users_matched": users_matched,
        "users_renewed": renewed_count,
        "users_skipped": len(candidates) - users_matched,
    }


# ── Internal helpers ───────────────────────────────────────────────────────────

async def _expire_old_tribes(db, now: datetime) -> int:
    """Mark tribes past their expiry as 'expired'. Record co-member history."""
    result = await db.table("tribes").select("id, tribe_members(user_id)").eq("status", "active").lt("expires_at", now.isoformat()).execute()
    expired = result.data or []

    for tribe in expired:
        tribe_id = tribe["id"]
        members = [m["user_id"] for m in (tribe.get("tribe_members") or [])]

        # Record co-member history (for "no repeat tribes" filter)
        history_rows = [
            {"user_id": uid, "co_member_id": co_id, "tribe_id": tribe_id, "cycle_ended_at": now.isoformat()}
            for uid in members
            for co_id in members
            if uid != co_id
        ]
        if history_rows:
            await db.table("tribe_member_history").insert(history_rows).execute()

        # Delete renewal requests for this tribe (expired = no longer relevant)
        await db.table("tribe_renewal_requests").delete().eq("tribe_id", tribe_id).execute()

        # Mark tribe expired
        await db.table("tribes").update({"status": "expired"}).eq("id", tribe_id).execute()

    return len(expired)


async def _renew_requesting_tribes(db, now: datetime) -> int:
    """Renew tribes where all active members have requested renewal."""
    # Find tribes expiring within 48h with at least one renewal request
    cutoff = (now + timedelta(hours=48)).isoformat()
    result = await db.table("tribes").select("id").eq("status", "active").lt("expires_at", cutoff).execute()
    tribes = result.data or []

    renewed = 0
    for tribe in tribes:
        tribe_id = tribe["id"]

        # Count active members
        members_result = await db.table("tribe_members").select("user_id").eq("tribe_id", tribe_id).is_("opt_out_at", None).execute()
        active_member_ids = {m["user_id"] for m in (members_result.data or [])}

        if len(active_member_ids) < 2:
            continue

        # Count renewal requests from active members
        renewals_result = await db.table("tribe_renewal_requests").select("user_id").eq("tribe_id", tribe_id).execute()
        requesting_ids = {r["user_id"] for r in (renewals_result.data or [])} & active_member_ids

        # All active members requested renewal
        if requesting_ids == active_member_ids:
            new_expiry = (now + timedelta(weeks=TRIBE_DURATION_WEEKS)).isoformat()
            await db.table("tribes").update({"expires_at": new_expiry}).eq("id", tribe_id).execute()
            await db.table("tribe_renewal_requests").delete().eq("tribe_id", tribe_id).execute()
            renewed += 1
            logger.info("Tribe {tid} renewed for 4 more weeks", tid=tribe_id)

    return renewed


async def _get_matching_candidates(db, now: datetime) -> list[dict]:
    """Find users eligible for new tribe matching.

    Eligible criteria:
    - Not in an active tribe (no active tribe_members row)
    - visible_to_orgs = True (proxy for "wants platform visibility")
    - Has a total_score > 0 (has completed at least one assessment)
    - Active recently (aura_scores.last_updated within 30 days)
    """
    cutoff = (now - timedelta(days=MATCHING_POOL_DAYS)).isoformat()

    # Subquery approach: get all users currently in active tribes
    active_tribes_result = await db.table("tribe_members").select("user_id").is_("opt_out_at", None).execute()
    excluded_user_ids = {m["user_id"] for m in (active_tribes_result.data or [])}

    # Get candidates: has AURA score + recently active + visible
    candidates_result = await db.table("aura_scores").select(
        "volunteer_id, total_score, last_updated"
    ).gt("total_score", 0).gt("last_updated", cutoff).execute()

    candidates = []
    for row in (candidates_result.data or []):
        uid = row["volunteer_id"]
        if uid in excluded_user_ids:
            continue

        # Check visible_to_orgs
        profile_result = await db.table("profiles").select("id").eq("id", uid).eq("visible_to_orgs", True).maybe_single().execute()
        if not profile_result.data:
            continue

        # Get co-member history (for no-repeat filter)
        history_result = await db.table("tribe_member_history").select("co_member_id").eq("user_id", uid).execute()
        previous_ids = [h["co_member_id"] for h in (history_result.data or [])]

        candidates.append({
            "user_id": uid,
            "aura_score": float(row["total_score"]),
            "previous_co_member_ids": previous_ids,
        })

    return candidates


def _cluster_and_match(candidates: list[dict]) -> list[list[dict]]:
    """Group candidates into triplets by AURA score proximity.

    Algorithm:
    1. Sort by AURA score ascending
    2. Greedy matching: take first user, find 2 closest within ±15 points
       (excluding previous co-members)
    3. Remove matched users from pool, repeat
    4. Remainder of 1 = skip (can't form tribe solo)
    5. Remainder of 2 = form pair (Q3: 2-person tribe is valid)
    """
    sorted_candidates = sorted(candidates, key=lambda u: u["aura_score"])
    remaining = list(sorted_candidates)
    groups: list[list[dict]] = []

    while len(remaining) >= 2:
        anchor = remaining[0]
        anchor_score = anchor["aura_score"]
        anchor_excluded = set(anchor["previous_co_member_ids"])

        # Find compatible candidates within score range, not previously co-members
        compatible = [
            u for u in remaining[1:]
            if abs(u["aura_score"] - anchor_score) <= SCORE_PROXIMITY
            and u["user_id"] not in anchor_excluded
        ]

        if not compatible:
            # No compatible match in score range — skip anchor (goes to next run)
            remaining.pop(0)
            continue

        if len(compatible) >= 2:
            # Form a triplet
            group = [anchor, compatible[0], compatible[1]]
        else:
            # Only 1 compatible — form a pair (Q3: 2-person tribe valid)
            group = [anchor, compatible[0]]

        groups.append(group)

        # Remove matched users from remaining pool
        matched_ids = {u["user_id"] for u in group}
        remaining = [u for u in remaining if u["user_id"] not in matched_ids]

    return groups


async def _create_tribe(db, group: list[dict], now: datetime) -> str:
    """Create tribe + tribe_members + upsert tribe_streaks. Returns tribe_id."""
    expires_at = (now + timedelta(weeks=TRIBE_DURATION_WEEKS)).isoformat()

    # Create tribe
    tribe_result = await db.table("tribes").insert({
        "expires_at": expires_at,
        "status": "active",
    }).execute()

    tribe_id = tribe_result.data[0]["id"]

    # Create tribe_members rows
    member_rows = [
        {"tribe_id": tribe_id, "user_id": u["user_id"]}
        for u in group
    ]
    await db.table("tribe_members").insert(member_rows).execute()

    # Upsert tribe_streaks (preserve existing streak; reset consecutive_misses on new cycle)
    for u in group:
        existing = await db.table("tribe_streaks").select("*").eq("user_id", u["user_id"]).maybe_single().execute()
        if existing.data:
            # New cycle: reset consecutive_misses, update cycle_started_at
            await db.table("tribe_streaks").update({
                "consecutive_misses_count": 0,
                "cycle_started_at": now.isoformat(),
            }).eq("user_id", u["user_id"]).execute()
        else:
            # First ever tribe — create streak row
            await db.table("tribe_streaks").insert({
                "user_id": u["user_id"],
                "current_streak": 0,
                "longest_streak": 0,
                "consecutive_misses_count": 0,
                "cycle_started_at": now.isoformat(),
            }).execute()

    # Clear matched users from the matching pool (they're now in a tribe)
    matched_user_ids = [u["user_id"] for u in group]
    for uid in matched_user_ids:
        await db.table("tribe_matching_pool").delete().eq("user_id", uid).execute()

    logger.info("Created tribe {tid} with {n} members", tid=tribe_id, n=len(group))
    return tribe_id
