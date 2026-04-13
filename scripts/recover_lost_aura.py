"""Recover AURA scores for completed sessions that leaked through the pipeline.

Finds assessment_sessions WHERE status='completed' AND no matching aura_scores row.
Recalculates competency score from stored answers, calls upsert_aura_score RPC.

Usage:
  DRY_RUN=1 python scripts/recover_lost_aura.py   # preview only
  python scripts/recover_lost_aura.py              # actually fix
"""

import asyncio
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "api"))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "apps", "api", ".env"))


async def main():
    from supabase import acreate_client

    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    dry_run = os.environ.get("DRY_RUN", "0") == "1"

    db = await acreate_client(url, key)

    completed = (
        await db.table("assessment_sessions")
        .select("id, volunteer_id, competency_id, answers, theta_estimate, gaming_penalty_multiplier")
        .eq("status", "completed")
        .execute()
    )

    aura_rows = (
        await db.table("aura_scores")
        .select("volunteer_id")
        .execute()
    )
    has_aura = {r["volunteer_id"] for r in (aura_rows.data or [])}

    leaked = [s for s in (completed.data or []) if s["volunteer_id"] not in has_aura]

    if not leaked:
        print("No leaked sessions found. All completed sessions have AURA scores.")
        return

    print(f"Found {len(leaked)} leaked sessions:")
    for s in leaked:
        print(f"  session={s['id']} user={s['volunteer_id']} theta={s.get('theta_estimate')}")

    for s in leaked:
        theta = s.get("theta_estimate") or 0.0
        penalty = float(s.get("gaming_penalty_multiplier") or 1.0)

        raw_score = 50 + 50 * (2 / (1 + math.exp(-1.7 * theta)) - 1)
        score = round(min(100, max(0, raw_score)) * penalty, 2)

        comp = (
            await db.table("competencies")
            .select("slug")
            .eq("id", s["competency_id"])
            .single()
            .execute()
        )
        slug = comp.data["slug"] if comp.data else None

        if not slug:
            print(f"  SKIP session={s['id']} — no competency slug found")
            continue

        print(f"  FIX session={s['id']} user={s['volunteer_id']} {slug}={score}")

        if not dry_run:
            try:
                result = await db.rpc(
                    "upsert_aura_score",
                    {
                        "p_volunteer_id": s["volunteer_id"],
                        "p_competency_scores": {slug: score},
                    },
                ).execute()
                status = "OK" if result.data is not None else "NO_DATA"
                print(f"    → upsert_aura_score: {status}")
            except Exception as e:
                print(f"    → ERROR: {e}")

    if dry_run:
        print("\nDRY RUN — no changes made. Remove DRY_RUN=1 to fix.")
    else:
        print(f"\nRecovered {len(leaked)} sessions.")


if __name__ == "__main__":
    asyncio.run(main())
