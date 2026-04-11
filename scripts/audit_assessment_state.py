#!/usr/bin/env python3
"""Audit prod for users affected by the two Session 93 bugs.

Bug #1 — Bridged users without profiles row:
  Any auth.users row created via the external bridge that never got a
  corresponding public.profiles row. Those users are FK-broken — they
  cannot complete a single assessment, start event, or earn AURA. The
  fix (8b153e0) stops the bleeding for new bridges; this script counts
  and optionally backfills existing victims.

Bug #2 — Completed sessions with no aura_scores entry for that competency:
  Before 5c0b006, submit_answer pre-marked status=completed when CAT
  stopped. The follow-up /complete call hit BUG-015 idempotency and
  skipped upsert_aura_score. Result: completed assessment sessions
  whose competency is NOT in the user's aura_scores.competency_scores
  JSONB. Script counts them and offers --backfill to call the RPC.

Read-only by default. Pass --backfill to actually write.
"""

from __future__ import annotations
import asyncio, os, sys, argparse
from supabase import acreate_client

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "") or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")


async def audit_bridged_missing_profiles(admin) -> list[dict]:
    """Return identity_map rows whose shared_user_id has no profiles row."""
    mappings = await (
        admin.table("user_identity_map")
        .select("shared_user_id, email, source_product, last_seen_at")
        .execute()
    )
    if not mappings.data:
        return []

    shared_ids = list({row["shared_user_id"] for row in mappings.data})
    # Batched IN lookup
    profiles = await (
        admin.table("profiles").select("id").in_("id", shared_ids).execute()
    )
    have_profile = {r["id"] for r in (profiles.data or [])}
    victims = [r for r in mappings.data if r["shared_user_id"] not in have_profile]
    return victims


async def audit_completed_without_aura(admin) -> list[dict]:
    """Return completed sessions where aura_scores.competency_scores lacks the slug.

    Bug #2 impact query. Uses a two-phase approach because PostgREST cannot
    express "JSONB key not present" efficiently in a single call — we pull
    all completed sessions plus existing aura_scores and diff client-side.
    """
    sessions_resp = await (
        admin.table("assessment_sessions")
        .select("id, volunteer_id, competency_id, completed_at")
        .eq("status", "completed")
        .order("completed_at", desc=True)
        .execute()
    )
    sessions = sessions_resp.data or []
    if not sessions:
        return []

    # Fetch competency slug map once (8-row static table)
    comps = await admin.table("competencies").select("id, slug").execute()
    slug_by_id = {c["id"]: c["slug"] for c in (comps.data or [])}

    # Fetch existing aura_scores for all affected users
    user_ids = list({s["volunteer_id"] for s in sessions})
    aura_resp = (
        await admin.table("aura_scores")
        .select("volunteer_id, competency_scores")
        .in_("volunteer_id", user_ids)
        .execute()
    )
    scores_by_user = {
        r["volunteer_id"]: (r.get("competency_scores") or {})
        for r in (aura_resp.data or [])
    }

    victims = []
    for s in sessions:
        slug = slug_by_id.get(s["competency_id"])
        if not slug:
            continue
        user_scores = scores_by_user.get(s["volunteer_id"], {})
        if slug not in user_scores:
            victims.append({**s, "slug": slug})
    return victims


async def backfill_bridged_profiles(admin, victims: list[dict]) -> int:
    """Insert minimal profiles rows for each bridged user missing one."""
    ok = 0
    for v in victims:
        uid = v["shared_user_id"]
        username = f"u{uid.replace('-', '')[:16]}"
        try:
            await (
                admin.table("profiles")
                .upsert({"id": uid, "username": username}, on_conflict="id")
                .execute()
            )
            ok += 1
        except Exception as e:
            print(f"  [skip] {uid[:8]}: {str(e)[:120]}")
    return ok


async def backfill_aura_scores(admin, victims: list[dict]) -> int:
    """Re-run upsert_aura_score for each completed session missing AURA.

    Reads the session's stored theta/gaming penalty, computes competency_score
    the same way complete_assessment does, and calls the RPC. Idempotent via
    RPC merge.
    """
    import sys as _sys
    _sys.path.insert(0, os.path.join(os.getcwd(), "apps", "api"))
    from app.core.assessment.engine import theta_to_score  # type: ignore

    ok = 0
    for v in victims:
        sess = await (
            admin.table("assessment_sessions")
            .select("theta_estimate, gaming_penalty_multiplier")
            .eq("id", v["id"])
            .single()
            .execute()
        )
        if not sess.data:
            continue
        theta = float(sess.data.get("theta_estimate") or 0.0)
        mult = float(sess.data.get("gaming_penalty_multiplier") or 1.0)
        score = round(theta_to_score(theta) * mult, 2)
        try:
            await admin.rpc(
                "upsert_aura_score",
                {
                    "p_volunteer_id": v["volunteer_id"],
                    "p_competency_scores": {v["slug"]: score},
                },
            ).execute()
            ok += 1
        except Exception as e:
            print(f"  [skip] session {v['id'][:8]}: {str(e)[:120]}")
    return ok


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backfill", action="store_true", help="actually write fixes")
    args = parser.parse_args()

    if not SUPABASE_URL or not SERVICE_KEY:
        print("SUPABASE_URL or SUPABASE_SERVICE_KEY missing")
        return 2

    admin = await acreate_client(SUPABASE_URL, SERVICE_KEY)
    print(f"Audit target: {SUPABASE_URL}\n")

    # ── Bug #1 — bridged users missing profiles ──────────────────────────
    print("Bug #1 — bridged users missing profiles row")
    bug1 = await audit_bridged_missing_profiles(admin)
    print(f"  affected mappings: {len(bug1)}")
    for v in bug1[:5]:
        print(f"    - {v['shared_user_id'][:8]}  email={v['email']}  src={v['source_product']}")
    if len(bug1) > 5:
        print(f"    ... +{len(bug1) - 5} more")

    # ── Bug #2 — completed sessions without AURA write ────────────────────
    print("\nBug #2 — completed sessions without aura_scores entry")
    bug2 = await audit_completed_without_aura(admin)
    print(f"  affected sessions: {len(bug2)}")
    affected_users = {v["volunteer_id"] for v in bug2}
    print(f"  distinct users:    {len(affected_users)}")
    for v in bug2[:5]:
        print(f"    - session {v['id'][:8]}  user {v['volunteer_id'][:8]}  slug={v['slug']}  completed_at={v['completed_at']}")
    if len(bug2) > 5:
        print(f"    ... +{len(bug2) - 5} more")

    if not args.backfill:
        print("\n(read-only mode — pass --backfill to fix)")
        return 0

    # ── Backfill ──────────────────────────────────────────────────────────
    print("\n--- BACKFILL MODE ---")
    if bug1:
        print(f"Inserting profiles for {len(bug1)} bridged users...")
        p_ok = await backfill_bridged_profiles(admin, bug1)
        print(f"  wrote {p_ok}/{len(bug1)} profiles")
    if bug2:
        print(f"Running upsert_aura_score for {len(bug2)} sessions...")
        a_ok = await backfill_aura_scores(admin, bug2)
        print(f"  upserted {a_ok}/{len(bug2)} AURA rows")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
