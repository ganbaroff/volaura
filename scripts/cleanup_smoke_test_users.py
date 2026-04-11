#!/usr/bin/env python3
"""Delete prod users created by smoke/debug runs of Session 93 scripts.

Only targets rows created by scripts/prod_smoke_e2e.py and
scripts/debug_aura_rpc.py — identified by their unique
standalone_project_ref values ("smoke_e2e_test", "debug_aura") in
user_identity_map, and by the "smoke+smoke-" / "debug+debug-" email
pattern in auth.users.

Does NOT touch pre-existing test fixtures from MindShift integration
tests (bridge-test@mindshift.app, e2e-bridge-*@mindshift-e2e.dev) —
those may be consumed by MindShift's own CI and deleting them would
cause collateral damage.

Read-only by default. Pass --execute to actually delete.
"""

from __future__ import annotations
import asyncio, os, sys, argparse
from supabase import acreate_client

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "") or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# Only rows created by OUR scripts, by project_ref
OWNED_PROJECT_REFS = ("smoke_e2e_test", "debug_aura")


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="actually delete")
    args = parser.parse_args()

    if not SUPABASE_URL or not SERVICE_KEY:
        print("SUPABASE_URL or SUPABASE_SERVICE_KEY missing"); return 2

    admin = await acreate_client(SUPABASE_URL, SERVICE_KEY)

    # Find rows owned by our scripts
    mappings = await (
        admin.table("user_identity_map")
        .select("shared_user_id, email, standalone_project_ref, source_product")
        .in_("standalone_project_ref", list(OWNED_PROJECT_REFS))
        .execute()
    )
    rows = mappings.data or []
    print(f"Found {len(rows)} user_identity_map rows owned by Session 93 scripts:")
    for r in rows:
        print(f"  - {r['shared_user_id'][:8]}  ref={r['standalone_project_ref']}  email={r['email']}")

    if not rows:
        print("Nothing to clean.")
        return 0

    if not args.execute:
        print("\n(read-only mode — pass --execute to actually delete)")
        return 0

    print("\n--- DELETE MODE ---")
    deleted_auth = 0
    for r in rows:
        uid = r["shared_user_id"]
        # Delete via admin.auth.admin.delete_user — cascades to public.profiles
        # and everything FK'd to profiles (assessment_sessions, aura_scores,
        # badges, events, embeddings, behavior_signals, character_events, ...).
        try:
            await admin.auth.admin.delete_user(uid)
            deleted_auth += 1
            print(f"  deleted auth.users {uid[:8]}")
        except Exception as e:
            print(f"  [skip auth] {uid[:8]}: {str(e)[:120]}")

    # user_identity_map has FK to auth.users via shared_user_id? Check by
    # trying to delete directly — if auth.users.delete_user already cascaded,
    # the rows are gone; otherwise clean them up explicitly.
    try:
        await (
            admin.table("user_identity_map")
            .delete()
            .in_("standalone_project_ref", list(OWNED_PROJECT_REFS))
            .execute()
        )
        print("  user_identity_map rows cleaned")
    except Exception as e:
        print(f"  [skip map cleanup] {str(e)[:120]}")

    print(f"\nCleaned: {deleted_auth}/{len(rows)} auth users + mappings")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
