#!/usr/bin/env python3
"""Live RLS policy inspection via the zeus governance RPC.

PostgREST blocks direct access to pg_catalog (PGRST106 "Only public and
graphql_public schemas are exposed"), which means a plain Supabase SDK
call against pg_policies always fails. This script uses the RPC added in
20260411193900_zeus_governance.sql (public.inspect_table_policies) to
get the real live policies for a given table.

Usage:
    python scripts/check_rls_live.py character_events
    python scripts/check_rls_live.py assessment_sessions profiles aura_scores

Exit code 0 if every requested table has at least one policy and the
policies compile OK; 1 otherwise.
"""

from __future__ import annotations
import asyncio, os, sys
from supabase import acreate_client

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "") or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

DEFAULT_TABLES = ["character_events", "assessment_sessions", "aura_scores", "profiles"]


async def main() -> int:
    if not SUPABASE_URL or not SERVICE_KEY:
        print("SUPABASE_URL or SUPABASE_SERVICE_KEY missing")
        return 2

    tables = sys.argv[1:] or DEFAULT_TABLES
    admin = await acreate_client(SUPABASE_URL, SERVICE_KEY)

    failed = False
    for table in tables:
        print(f"\n=== {table} ===")
        try:
            r = await admin.rpc(
                "inspect_table_policies", {"p_table_name": table}
            ).execute()
            rows = r.data or []
            if not rows:
                print("  [WARN] no RLS policies found")
                continue
            for p in rows:
                print(f"  * {p['policyname']}  cmd={p['cmd']}  permissive={p['permissive']}")
                if p.get("qual"):
                    print(f"      USING: {p['qual']}")
                if p.get("with_check"):
                    print(f"      WITH CHECK: {p['with_check']}")
        except Exception as e:
            failed = True
            msg = str(e)
            if "PGRST202" in msg or "inspect_table_policies" in msg:
                print("  [FAIL] inspect_table_policies RPC not deployed yet — run supabase db push first")
            else:
                print(f"  [FAIL] {msg[:200]}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
