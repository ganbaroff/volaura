#!/usr/bin/env python3
"""One-shot debug: call upsert_aura_score directly with admin client.

Creates a fresh bridged user via API, then queries Supabase directly with
service_role to check whether the RPC actually inserts a row. Separates
"RPC path is broken" from "Python SDK aura_updated detection is broken".
"""

from __future__ import annotations
import asyncio, os, sys, time, uuid, httpx
from supabase import acreate_client

BASE_URL = os.getenv("VOLAURA_PROD_URL", "").rstrip("/")
BRIDGE_SECRET = os.getenv("EXTERNAL_BRIDGE_SECRET", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "") or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")


async def main() -> int:
    if not all([BASE_URL, BRIDGE_SECRET, SUPABASE_URL, SERVICE_KEY]):
        missing = [k for k, v in {
            "VOLAURA_PROD_URL": BASE_URL,
            "EXTERNAL_BRIDGE_SECRET": BRIDGE_SECRET,
            "SUPABASE_URL": SUPABASE_URL,
            "SUPABASE_SERVICE_KEY": SERVICE_KEY,
        }.items() if not v]
        print(f"Missing env: {missing}")
        return 2

    # Step 1: create a bridged user via prod
    standalone_id = f"debug-aura-{int(time.time())}-{uuid.uuid4().hex[:8]}"
    email = f"debug+{standalone_id}@volaura.app"
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        r = await client.post(
            "/api/auth/from_external",
            headers={"X-Bridge-Secret": BRIDGE_SECRET},
            json={
                "standalone_user_id": standalone_id,
                "standalone_project_ref": "debug_aura",
                "email": email,
                "source_product": "debug",
            },
        )
        if r.status_code != 200:
            print(f"bridge FAIL {r.status_code}: {r.text[:200]}")
            return 1
        user_id = r.json()["shared_user_id"]
        print(f"bridged user_id = {user_id}")

    # Step 2: direct admin queries
    admin = await acreate_client(SUPABASE_URL, SERVICE_KEY)

    prof = await admin.table("profiles").select("id,username").eq("id", user_id).execute()
    print(f"profiles row: {prof.data}")

    aura_before = await admin.table("aura_scores").select("*").eq("volunteer_id", user_id).execute()
    print(f"aura_scores BEFORE rpc: {aura_before.data}")

    # Step 3: call upsert_aura_score directly
    try:
        rpc_result = await admin.rpc(
            "upsert_aura_score",
            {"p_volunteer_id": user_id, "p_competency_scores": {"communication": 42.5}},
        ).execute()
        print(f"RPC .data type: {type(rpc_result.data).__name__}")
        print(f"RPC .data value: {rpc_result.data}")
    except Exception as e:
        print(f"RPC EXCEPTION: {type(e).__name__}: {str(e)[:500]}")

    aura_after = await admin.table("aura_scores").select("*").eq("volunteer_id", user_id).execute()
    print(f"aura_scores AFTER rpc: {aura_after.data}")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
