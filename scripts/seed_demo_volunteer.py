"""Seed a demo volunteer profile for org cold-search visits.

Run ONCE from the project root:
    python scripts/seed_demo_volunteer.py

Requirements:
    - SUPABASE_URL and SUPABASE_SERVICE_KEY set in environment or apps/api/.env
    - Supabase project must be running (local or remote)

What it creates:
    - auth.users entry: demo@volaura.app (email, confirmed)
    - profiles row: display_name="Natavan Hasanova", account_type=volunteer, visible_to_orgs=True
    - aura_scores row: Gold badge, 82/100, competency_scores for 3 skills
    - assessment_sessions row: completed adaptability session (30 questions)

Demo user details:
    - email: demo@volaura.app
    - username: volaura-demo
    - UUID: fixed (00000000-0000-0000-0000-000000000001)

Safe to run multiple times — upserts everywhere.
"""

import asyncio
import os
import sys
from pathlib import Path

# Load .env from apps/api/.env if not already set
env_path = Path(__file__).parent.parent / "apps" / "api" / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set.")
    sys.exit(1)

DEMO_UUID = "00000000-0000-0000-0000-000000000001"
DEMO_EMAIL = "demo@volaura.app"
DEMO_USERNAME = "volaura-demo"
DEMO_PASSWORD = "VolauraDemo2026!"  # not used in prod; just for local dev access


async def seed() -> None:
    from supabase._async.client import AsyncClient, create_client  # type: ignore

    client: AsyncClient = await create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    print("1. Creating demo auth user...")
    try:
        resp = await client.auth.admin.create_user({
            "email": DEMO_EMAIL,
            "password": DEMO_PASSWORD,
            "email_confirm": True,
            "user_metadata": {"display_name": "Natavan Hasanova"},
            "id": DEMO_UUID,
        })
        if resp.user:
            print(f"   Created: {resp.user.id}")
        else:
            print("   Already exists or creation silently skipped.")
    except Exception as e:
        err = str(e)
        if "already been registered" in err or "already exists" in err or "duplicate" in err.lower():
            print("   Already exists — skipping.")
        else:
            print(f"   WARNING: {err[:200]}")

    print("2. Upserting profile...")
    profile_data = {
        "id": DEMO_UUID,
        "account_type": "volunteer",
        "username": DEMO_USERNAME,
        "display_name": "Natavan Hasanova",
        "bio": "Event organizer with 3 years of volunteer experience across Baku. "
               "Passionate about community development and youth programs.",
        "city": "Baku",
        "country": "AZ",
        "visible_to_orgs": True,
        "subscription_status": "free",
    }
    await client.table("profiles").upsert(profile_data, on_conflict="id").execute()
    print("   Done.")

    print("3. Upserting aura_scores...")
    aura_data = {
        "volunteer_id": DEMO_UUID,
        "total_score": 82.0,
        "badge_tier": "gold",
        "visibility": "public",
        "competency_scores": {
            "adaptability": 84.5,
            "communication": 79.0,
            "teamwork": 83.0,
        },
        "percentile_rank": 72,
        "last_updated": "2026-04-01T10:00:00Z",
        "pending_aura_sync": False,
    }
    await client.table("aura_scores").upsert(aura_data, on_conflict="volunteer_id").execute()
    print("   Done.")

    print("4. Upserting completed assessment session (adaptability)...")
    # Fetch competency ID for adaptability
    comp_resp = await client.table("competencies").select("id").eq(
        "slug", "adaptability"
    ).maybe_single().execute()
    competency_id = (comp_resp.data or {}).get("id")
    if competency_id:
        session_data = {
            "id": "00000000-0000-0000-0000-000000000002",
            "volunteer_id": DEMO_UUID,
            "competency_id": competency_id,
            "status": "completed",
            "theta_estimate": 0.85,
            "theta_se": 0.28,
            "answers": [],
            "pending_aura_sync": False,
        }
        await client.table("assessment_sessions").upsert(
            session_data, on_conflict="id"
        ).execute()
        print("   Done.")
    else:
        print("   WARNING: adaptability competency not found — skipping session seed.")
        print("   Run seed_questions migration first.")

    print("\n✅ Demo volunteer seeded.")
    print(f"   Profile: {SUPABASE_URL.replace('https://', 'https://app.supabase.com/project/')}")
    print(f"   Username: {DEMO_USERNAME}")
    print(f"   Visible in org search: YES (visible_to_orgs=True, badge=Gold)")
    print(f"\n   Org visitors at /az/volunteers will now see at least 1 result.")


if __name__ == "__main__":
    asyncio.run(seed())
