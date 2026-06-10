"""One-shot smoke test for the B2B screening campaign loop (2026-06-11).

Run from apps/api with its venv against a locally running API on :8787.
Creates one clearly-labeled smoke candidate in prod auth, joins the pilot
campaign, then reads the org report as the org owner. Prints NO secrets.
"""

import os
import sys
import uuid

import httpx
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

API = "http://127.0.0.1:8787/api"
TOKEN = "pilot-c9ddfe3a56b14e573ec7"
CAMPAIGN_ID = "a21c84d1-5ff4-443e-b692-a869ab494a37"

url = os.environ["SUPABASE_URL"]
service_key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ["SUPABASE_SERVICE_ROLE_KEY"]
anon_key = os.environ["SUPABASE_ANON_KEY"]

admin = create_client(url, service_key)
client = create_client(url, anon_key)

# ── 1. Create smoke candidate ────────────────────────────────────────────────
suffix = uuid.uuid4().hex[:8]
email = f"atlas-smoke-{suffix}@volaura-test.dev"
password = uuid.uuid4().hex + "Aa1!"

created = admin.auth.admin.create_user(
    {
        "email": email,
        "password": password,
        "email_confirm": True,
        "user_metadata": {
            "username": f"atlas_smoke_{suffix}",
            "account_type": "professional",
            "display_name": "Atlas Smoke Candidate",
        },
    }
)
candidate_id = created.user.id
print(f"1. candidate created: {candidate_id} ({email})")

# ── 2. Sign in candidate, join campaign ──────────────────────────────────────
session = client.auth.sign_in_with_password({"email": email, "password": password})
cand_token = session.session.access_token

r = httpx.post(
    f"{API}/campaigns/public/{TOKEN}/join",
    headers={"Authorization": f"Bearer {cand_token}"},
    timeout=30,
)
print(f"2. join: [{r.status_code}] {r.json()}")
if r.status_code != 200:
    sys.exit(1)

# Idempotency: join again
r2 = httpx.post(
    f"{API}/campaigns/public/{TOKEN}/join",
    headers={"Authorization": f"Bearer {cand_token}"},
    timeout=30,
)
body2 = r2.json()
print(f"3. re-join idempotent: [{r2.status_code}] already_joined={body2.get('already_joined')}")

# ── 3. Org owner: list campaigns + report ────────────────────────────────────
org = admin.table("organizations").select("owner_id, name").limit(1).execute().data[0]
owner = admin.auth.admin.get_user_by_id(org["owner_id"])
link = admin.auth.admin.generate_link({"type": "magiclink", "email": owner.user.email})
hashed = link.properties.hashed_token
owner_session = client.auth.verify_otp({"token_hash": hashed, "type": "magiclink"})
owner_token = owner_session.session.access_token
print(f"4. signed in as org owner of '{org['name']}'")

r3 = httpx.get(f"{API}/campaigns", headers={"Authorization": f"Bearer {owner_token}"}, timeout=30)
camps = r3.json()
mine = [c for c in camps if c["id"] == CAMPAIGN_ID]
print(f"5. owner campaign list: [{r3.status_code}] total={len(camps)} pilot_found={bool(mine)} "
      f"candidate_count={mine[0]['candidate_count'] if mine else '?'}")

r4 = httpx.get(
    f"{API}/campaigns/{CAMPAIGN_ID}/report",
    headers={"Authorization": f"Bearer {owner_token}"},
    timeout=30,
)
report = r4.json()
rows = report.get("candidates", [])
smoke_row = next((x for x in rows if x["professional_id"] == candidate_id), None)
print(f"6. report: [{r4.status_code}] candidates={len(rows)} smoke_candidate_in_report={bool(smoke_row)}")
if smoke_row:
    print(f"   row: assigned={smoke_row['assigned_sessions']} completed={smoke_row['completed_sessions']} "
          f"score={smoke_row['campaign_score']}")

# ── 4. Security: candidate must NOT read the report ──────────────────────────
r5 = httpx.get(
    f"{API}/campaigns/{CAMPAIGN_ID}/report",
    headers={"Authorization": f"Bearer {cand_token}"},
    timeout=30,
)
print(f"7. candidate blocked from report: [{r5.status_code}] (expect 403)")

ok = (
    r.status_code == 200
    and body2.get("already_joined") is True
    and r3.status_code == 200
    and bool(mine)
    and r4.status_code == 200
    and bool(smoke_row)
    and r5.status_code == 403
)
print("SMOKE RESULT:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
