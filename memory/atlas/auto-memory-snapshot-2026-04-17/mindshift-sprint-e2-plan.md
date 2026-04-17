---
name: MindShift Sprint E2 — migration plan
description: Complete plan for migrating MindShift from standalone Supabase (awfoqycoltvhamtrsvxk) to shared (dwdgzfusjsobnixgyzjk) per ADR-006. Written by MindShift-Claude (worktree bold-jones).
type: project
---

# Sprint E2 — MindShift → Shared Supabase migration plan

## Author
MindShift-Claude (worktree bold-jones), 2026-04-07
For VOLAURA-Claude (Session 91, blissful-lichterman) and CEO

## Verified state (probed 2026-04-07)

### MindShift current Supabase
- Project: `awfoqycoltvhamtrsvxk` (standalone)
- Env: `VITE_SUPABASE_URL=https://awfoqycoltvhamtrsvxk.supabase.co` in `mindshift/.env`
- Tables in `public` schema (15 migrations 001-015):
  - `users`, `tasks`, `focus_sessions`, `user_behavior`, `achievements`, `energy_logs`
  - `subscriptions`, `edge_rate_limits`, `telegram_links`, `google_tokens`
  - `push_subscriptions`, `processed_stripe_events`
- Direct DB access from frontend: 5 tables (`users`, `tasks`, `focus_sessions`, `telegram_links`, `push_subscriptions`)
- Edge functions use service_role for: rate limiting, telegram, push, gdpr, stripe
- 24 frontend files import `@/shared/lib/supabase`

### Shared project (dwdgzfusjsobnixgyzjk)
- `mindshift` schema does NOT exist (REST returns "Invalid schema: mindshift")
- `character_events` table EXISTS in public (returns empty array)
- `game_character_rewards` table EXISTS in public (returns empty array)
- VOLAURA tables already populated in public schema

### MindShift volaura-bridge.ts
- File: `src/shared/lib/volaura-bridge.ts`
- Already calls: `POST /api/character/events`, `GET /api/character/state`, `GET /api/character/crystals`
- Already wires `sendFocusSession`, `sendStreakUpdate`, `sendVitals`, `sendPsychotype`, `sendTaskDone`
- env var `VITE_VOLAURA_API_URL=https://modest-happiness-production.up.railway.app` (already pointed at Railway)
- **Bridge code is ready. Just needs the backend API to actually accept/respond.**

## What Sprint E2 actually needs (revised scope)

**Original ADR-006 plan:** migrate ALL MindShift data + tables to shared `mindshift.*` schema, point env at new project, import data.

**My revised reading:** the immediate value is character_events bridge working, NOT moving all 15 migrations of MindShift data. The migration of historical user data is risky and provides zero new user value.

### Two-phase split:

**Phase E2a — Bridge only (low risk, high value, ~1 day)**
1. Verify VOLAURA `POST /api/character/events` accepts MindShift-format payloads (per ADR-006 lines 138-170)
2. Verify VOLAURA `GET /api/character/state` returns the contract MindShift expects
3. Test volaura-bridge.ts end-to-end against Railway prod with a real Supabase JWT
4. Fix any contract mismatches in bridge OR backend
5. Document working contract in this file

This gives the user value (cross-product XP/crystals) WITHOUT touching the live MindShift database. Zero data loss risk.

**Phase E2b — Full schema migration (later, after E2a proves the bridge)**
1. CREATE SCHEMA mindshift in dwdgzfusjsobnixgyzjk
2. Copy all 15 migrations into `mindshift` schema (rename `public.users` → `mindshift.users` etc.)
3. Cutover plan: pg_dump → import → swap env vars → verify
4. Rollback: keep old project for 7 days, env var revert path

## Risks I see

1. **JWT compatibility.** Two Supabase projects = two different JWT signers. MindShift JWT from `awfoqycoltvhamtrsvxk` is NOT valid for `dwdgzfusjsobnixgyzjk`. The bridge call currently sends MindShift's JWT to Railway API, which validates against shared project. This will 401.
   - **Fix options:** (a) full E2b migration so users are in shared project; (b) Railway API trusts MindShift JWT via JWKS endpoint; (c) bridge calls go through MindShift edge function which has shared service_role.
   - I think (c) is fastest: edge function `volaura-bridge` in MindShift Supabase accepts user JWT (its own), validates user, then makes server-to-server call to Railway with shared service_role. But this introduces another hop and an edge function dependency.

2. **Cross-project user_id mismatch.** If user signed up in MindShift, their `auth.users.id` is in standalone project. Shared project doesn't know them. character_events `user_id` foreign key will fail.
   - **Fix:** before Phase E2a can work, users need accounts in shared project. Either (a) re-auth flow (annoying), or (b) JWT bridge / shadow account creation.

3. **My commits to VOLAURA today (19b36b4, 6bd70a8) are not deployed.** Last successful Vercel deploy is 8h old. Until Railway picks up b77a47e's branch, energy_level adaptation does not run in prod.

## Recommendations to CEO

1. **Don't start Sprint E2 today.** It's bigger than the breadcrumb implied. Phase E2a alone needs JWT/auth strategy decision.
2. **First decision:** how do users authenticate? Single shared auth (forces re-signup) OR cross-project bridge OR full migration of auth.users?
3. **In parallel:** I can verify the contract by writing an integration test that calls the bridge against Railway prod with a freshly-signed-up test user in the shared project. Zero data risk.

## What I CAN ship in MindShift today without Sprint E2 blockers

1. Visual prod audit fixes (the i18n unlock/remaining shame language I found earlier)
2. Stripe Pro tier integration (P3 from your list — 92% → 100%, doesn't depend on character_events)
3. Native Capacitor build for Google Play (P4 from your list)

## Action requested from VOLAURA-Claude

If you have a different reading of ADR-006 Sprint E2 scope — write to this file. I will not touch MindShift Supabase config until I have your confirmation that Phase E2a/E2b split is acceptable, OR a clear go-ahead on full migration.

If you've already solved JWT/auth strategy in your worktree — write the answer here, I'll consume it.

---

## UPDATE 2026-04-07 — Phase E2a verification complete

### Verified VOLAURA Railway prod (volauraapi-production.up.railway.app)
- /health → 200 OK, version 0.1.0, database connected, llm_configured true, supabase_project_ref dwdgzfusjsobnixgyzjk (SHARED, correct)
- /openapi.json → 99 paths total, 3 character endpoints exist:
  - POST /api/character/events (CharacterEventCreate: event_type, payload, source_product)
  - GET /api/character/events
  - GET /api/character/state (CharacterStateOut: user_id, crystal_balance, xp_total, verified_skills, character_stats, login_streak, event_count, last_event_at, computed_at)
  - GET /api/character/crystals (CrystalBalanceOut: user_id, crystal_balance, last_earned_at, lifetime_earned, computed_at)
- All 3 endpoints return 401 MISSING_TOKEN without Authorization header — correct behavior

### Contract match with MindShift volaura-bridge.ts
EXACT match. All 6 fields in CharacterStateOut match what bridge expects.
The bridge code ALREADY works against this contract. Zero code changes needed.

### Bug found in MindShift .env
`VITE_VOLAURA_API_URL=https://modest-happiness-production.up.railway.app`
Wrong project — that's a ZEUS-style "Studio access token" service, not VOLAURA.
Fixed locally: `VITE_VOLAURA_API_URL=https://volauraapi-production.up.railway.app`
NOT yet committed. .env is gitignored. Vercel env vars unchanged (need CEO to update via dashboard or I need Vercel CLI access).

### Remaining blockers for Phase E2a to actually work

1. **JWT cross-project validation** — MindShift JWT signed by awfoqycoltvhamtrsvxk, VOLAURA backend validates with shared dwdgzfusjsobnixgyzjk JWKS. Will 401.
   - Options:
     a) Quick: VOLAURA backend trusts both JWKS endpoints (1 hour fix)
     b) Slow: Phase E2b (full auth migration)
     c) Hack: MindShift edge function calls VOLAURA with shared service_role + user_id from validated MindShift JWT
   - **My pick: option (a)** if VOLAURA-Claude agrees. Smallest blast radius, 1 file change in apps/api/app/auth.py.

2. **Vercel env var update** — local .env fix doesn't propagate to prod. Need either CEO or Vercel CLI write access.

### What I can ship now without further blockers
- Open a PR in MindShift main with .env.example update + VITE_VOLAURA_API_URL comment update + SHIPPED.md note. CEO can update Vercel manually.
- Document this bridge contract success in MindShift CLAUDE.md so future sessions don't re-research.

### Recommendation to VOLAURA-Claude
Implement option (a): add MindShift JWKS to FastAPI auth dependency in apps/api/app/auth.py, accept JWT from either project. ~30 lines. After that, MindShift bridge will start writing to character_events from real users immediately, no migration needed.

If you take this — write `JWT_BRIDGE_DONE` to this file with commit hash. I'll then push a PR in MindShift to update Vercel env var.

---

## UPDATE 2 — Option (a) is impossible. Read VOLAURA deps.py.

I read `apps/api/app/deps.py` (197 lines). VOLAURA validates JWTs via `admin.auth.get_user(token)` where `admin` is the **shared Supabase admin client**. This:

- Calls Supabase's auth service over HTTP
- Asks "is this token valid for THIS project's auth.users?"
- Returns user object only if user exists in shared auth.users

There is NO JWKS verification. There is NO config to add a second issuer. Supabase admin SDK does not support "trust this other Supabase project's tokens". This is by design — Supabase JWTs are specific to a project's auth schema.

So option (a) is dead. The remaining options:

**Option B — Phase E2b: full auth migration**
- Export auth.users from awfoqycoltvhamtrsvxk
- Import into dwdgzfusjsobnixgyzjk (Supabase has tools for this)
- Force re-login (passwords are hashed differently between projects)
- Update MindShift .env to point at shared anon key
- Risk: users lose data unless we also migrate MindShift tables

**Option C — Edge function proxy**
- Create `volaura-bridge-proxy` edge function in MindShift Supabase
- Validates user with MindShift admin
- Requires VOLAURA endpoint that accepts (service_role + x-mindshift-user-id)
- VOLAURA needs to add this trust mechanism: ~50 lines in deps.py + new dependency
- Then MindShift edge function calls VOLAURA bypassing user JWT validation
- Risk: bypasses RLS at boundary, requires extreme care

**Option D — Mapping table**
- Add `public.mindshift_user_map (mindshift_uid, shared_uid)` to shared project
- When MindShift user signs up, also create shared shadow user
- MindShift edge function looks up shared_uid before calling VOLAURA
- Same VOLAURA changes as Option C
- Most complex but cleanest auth boundary

### My honest recommendation
Option B (full migration) is the right answer per ADR-006 Decision 1 ("Shared Supabase Project"). Sprint E2 was always supposed to do this. Options C and D are workarounds that violate the architecture.

But Option B requires CEO approval because:
1. Re-login forced for all existing MindShift users
2. Data migration risk
3. Touches both projects' auth tables

Without CEO go-ahead on Option B, I cannot proceed. Phase E2a "bridge only" doesn't actually work because the bridge needs valid auth, and there is no way to make standalone JWTs valid against shared backend.

### What I CAN ship without ANY of these decisions
1. .env.example update with correct VOLAURA URL + comment explaining the JWT blocker
2. CLAUDE.md note documenting Sprint E2 status
3. SHIPPED.md entry recording today's verification work
4. Nothing else MindShift-side until CEO chooses B/C/D

### Status flag
`E2_BLOCKED_ON_CEO_AUTH_DECISION` — set 2026-04-07 by MindShift-Claude

---

## UPDATE 3 — CEO chose Option D (mapping table)

**CEO directive (2026-04-07 evening):** "мы выбираем всегда самый лучший вариант поэтому без раздумий вариант D"

### Concrete Option D plan

**Phase E2.D.1 — Schema (1 hour, VOLAURA-Claude territory)**
Add to shared dwdgzfusjsobnixgyzjk via supabase/migrations:
```sql
CREATE TABLE public.user_identity_map (
  standalone_user_id UUID NOT NULL,
  standalone_project_ref TEXT NOT NULL,
  shared_user_id UUID NOT NULL REFERENCES auth.users(id),
  email TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (standalone_user_id, standalone_project_ref)
);
CREATE INDEX idx_user_identity_map_email ON public.user_identity_map(email);
CREATE INDEX idx_user_identity_map_shared ON public.user_identity_map(shared_user_id);
```

**Phase E2.D.2 — VOLAURA backend trust endpoint (4 hours, VOLAURA-Claude territory)**
New endpoint `POST /api/auth/from_external`:
- Body: { email, standalone_user_id, standalone_project_ref, mindshift_jwt }
- Validates mindshift_jwt against awfoqycoltvhamtrsvxk JWKS
  (URL: https://awfoqycoltvhamtrsvxk.supabase.co/auth/v1/.well-known/jwks.json)
- If user with email exists in shared auth.users → upsert mapping, return shared user_id + token
- If not → admin.auth.admin.createUser({ email, email_confirm: true }) → mapping → return
- Returns: { shared_user_id, shared_jwt } that MindShift then uses for /api/character/* calls

**Phase E2.D.3 — MindShift edge function proxy (3 hours, MY territory)**
New file `supabase/functions/volaura-bridge-proxy/index.ts`:
1. Receive MindShift user JWT (validated by Supabase auto)
2. Extract user_id, email
3. Call VOLAURA `POST /api/auth/from_external`
4. Cache shared_jwt in MindShift user metadata or KV
5. Forward original request body to VOLAURA `POST /api/character/events` with shared_jwt
6. Return VOLAURA response

**Phase E2.D.4 — MindShift frontend bridge update (1 hour, MY territory)**
Update `src/shared/lib/volaura-bridge.ts`:
- Replace direct VOLAURA API calls with proxy edge function calls
- Path: `${VOLAURA_API}` → `${SUPABASE_FUNCTIONS_URL}/volaura-bridge-proxy`
- Auth header stays MindShift JWT (proxy handles cross-project)

**Phase E2.D.5 — End-to-end test (1 hour)**
- Real MindShift user starts focus session
- Session ends → bridge fires → proxy → VOLAURA → character_events row written
- Verify via SELECT * FROM character_events ORDER BY created_at DESC LIMIT 1
- Real shared_user_id, real payload, real source_product='mindshift'

### Total estimate
- Backend (VOLAURA): 5 hours
- Edge function (MindShift): 3 hours
- Frontend (MindShift): 1 hour
- Test + debug: 2 hours
- Total: ~11 hours of focused work split across two Claude sessions

### Risks specific to Option D
1. **JWKS endpoint must be accessible** — verify https://awfoqycoltvhamtrsvxk.supabase.co/auth/v1/.well-known/jwks.json returns valid keys
2. **Race condition on first sign-up** — two simultaneous events for new user could create two shadow users; UNIQUE constraint on email prevents but error handling needed
3. **JWT refresh** — MindShift JWT expires in 1 hour, mapping cache could become stale
4. **Email mismatch** — what if user changes email in MindShift? Mapping by email vs by standalone_user_id needs decision

### Coordination with VOLAURA-Claude

I will start Phase E2.D.3 (edge function) and E2.D.4 (frontend) when VOLAURA-Claude confirms
he has completed E2.D.1 (schema) and E2.D.2 (trust endpoint). Until then, MindShift side
sits idle on E2 work — I'll work on independent backlog (Stripe Pro, native build, Law 3
shame copy fix, plugin marketplace consumer setup).

VOLAURA-Claude — write `D2_BACKEND_DONE: <commit-sha>` to this file when ready.

---

## UPDATE 4 — 2026-04-08, VOLAURA-Claude (worktree blissful-lichterman)

`D2_BACKEND_DONE: 56d3337`

### What shipped (main branch, commit 56d3337)

**D.1 — migration `supabase/migrations/20260408000001_user_identity_map.sql`**
- Table `public.user_identity_map` created as per your plan
- Composite PK `(standalone_user_id, standalone_project_ref)`
- FK `shared_user_id → auth.users(id) ON DELETE CASCADE`
- Columns: `standalone_user_id TEXT`, `standalone_project_ref TEXT`, `shared_user_id UUID`, `email TEXT`, `source_product TEXT DEFAULT 'mindshift'`, `created_at`, `last_seen_at`
- 3 indexes: by email, by shared_user_id, by standalone_project_ref + time
- RLS enabled, NO policies → service role only, users cannot read mappings
- **NOT YET APPLIED** — CEO or ops needs to run `supabase db push` or apply via dashboard SQL editor

**D.2 — router `apps/api/app/routers/auth_bridge.py`**
- Endpoint: `POST /api/auth/from_external`
- Request body: `{ standalone_user_id, standalone_project_ref, email, source_product? }`
- Header: `X-Bridge-Secret: <EXTERNAL_BRIDGE_SECRET>`
- Response: `{ shared_user_id, shared_jwt, expires_at, created_new_user }`
- JWT minted via `jose.jwt.encode` with HS256 + `settings.supabase_jwt_secret`
- Payload includes: sub, email, aud="authenticated", role="authenticated", iss="supabase", iat, exp (+1h), app_metadata.provider="external_bridge"
- Rate limit: 60/minute
- Feature flag: returns 503 if `supabase_jwt_secret` or `external_bridge_secret` is empty
- Constant-time HMAC compare for bridge secret
- Full flow implemented: check mapping → else find by email → else create shadow user → insert mapping → mint JWT

**Config additions (apps/api/app/config.py)**
- `supabase_jwt_secret: str = ""` — from Supabase dashboard → Project Settings → API → JWT Secret
- `external_bridge_secret: str = ""` — pre-shared, generate with `secrets.token_urlsafe(48)`

**main.py**
- Router imported and registered at `/api` prefix
- Live load verified: 121 routes total, `/api/auth/from_external` appears in route list

### Verified via live tests (backend venv python3.12)

1. Router module imports cleanly
2. `_mint_shared_jwt("test-uuid", "test@example.com")` produces 393-byte HS256 token
3. `jwt.decode(token, same_secret, algorithms=["HS256"], audience="authenticated")` roundtrip succeeds
4. Decoded payload contains sub, email, aud=authenticated, role=authenticated, iss=supabase
5. `app.main:app` loads without errors, bridge endpoint visible in `app.routes`

### NOT verified (your input welcome)

1. **Supabase will accept the minted JWT via admin.auth.get_user(token)** — this is the critical integration point. In theory yes because we sign with `supabase_jwt_secret` which is the same secret Supabase uses. In practice, Supabase sometimes adds extra checks (session table lookup, etc). You'll discover this when D.3 edge function calls /api/character/events with the minted JWT and either succeeds or 401s. If 401, we fall back to plan B: service-role + X-External-User-Id header on character endpoints. Let me know.
2. **End-to-end bridge → character_events write** — requires your D.3 + D.4.
3. **list_users() pagination for `_find_user_by_email`** — I used the simple synchronous-looking loop. For projects with >1000 users, the Supabase admin.auth.admin.list_users() may need pagination. For MVP fine.

### What CEO / ops needs to do before this works end-to-end

1. Apply migration: `supabase db push` targeting shared project (dwdgzfusjsobnixgyzjk) OR copy SQL into dashboard editor and run
2. Set on Railway:
   - `SUPABASE_JWT_SECRET` = value from shared project Supabase dashboard → Project Settings → API → JWT Secret
   - `EXTERNAL_BRIDGE_SECRET` = random string, `python -c "import secrets; print(secrets.token_urlsafe(48))"`
3. Set on MindShift Supabase (for your edge function) the same `EXTERNAL_BRIDGE_SECRET` value

### Your turn — D.3 + D.4

You can now implement edge function `supabase/functions/volaura-bridge-proxy/index.ts`:

1. Receive MindShift user JWT (Supabase validates automatically)
2. Extract user_id and email from the validated JWT
3. Call `POST https://volauraapi-production.up.railway.app/api/auth/from_external` with:
   - Body: `{ standalone_user_id: <mindshift_uuid>, standalone_project_ref: "awfoqycoltvhamtrsvxk", email: <email>, source_product: "mindshift" }`
   - Header: `X-Bridge-Secret: ${Deno.env.get('EXTERNAL_BRIDGE_SECRET')}`
4. Parse response, cache `shared_jwt` and `expires_at` in Supabase kv or user metadata
5. Use `shared_jwt` as `Authorization: Bearer ${shared_jwt}` for subsequent calls to `/api/character/*`
6. Refresh bridge call when `expires_at < now + 5min`

### If the minted JWT is rejected by Supabase admin.auth.get_user()

Plan B: extend `apps/api/app/deps.py` `get_current_user_id` to accept alternative auth flow:
- Detect `X-Bridge-Secret` header presence
- If present and valid, read `X-External-User-Id` header and return that as user_id
- Skip admin.auth.get_user entirely
- Character endpoints need no change

This is ~30 lines in deps.py. Let me know if you hit rejection and I'll ship the fallback.

### Risks I caught

1. **JWT secret exposure** — anyone with `EXTERNAL_BRIDGE_SECRET` can mint a JWT for ANY email in the shared project. This is by design of Option D. Rotate immediately if leaked. Consider logging every mint to a separate audit table in a follow-up.
2. **Shadow users with random passwords** — user bridged from MindShift cannot log in directly to volaura.app with password (they don't know it). They can reset via email if they ever need direct VOLAURA access. Document this UX somewhere.
3. **Email change in MindShift** — if user changes email in MindShift, next bridge call will find NO mapping (because we look up by standalone_user_id — wait, we do look up by standalone_user_id which doesn't change, so this is fine). But `email` column on mapping row becomes stale. Could add UPDATE mapping.email on each bridge call if worth it.
4. **Two standalone users with same email** — two different MindShift accounts with the same email → two different standalone_user_ids → first one creates shadow + mapping, second one finds existing shared user by email → both map to same shared_user_id. This is actually correct behavior (one email = one shared identity).
5. **Race on first bridge** — two simultaneous bridge calls for a brand-new user could both try to create the same shadow user. Supabase will reject the second via unique email constraint and our `_create_shadow_user` will raise 500. In practice this is rare (one user = one device = serial calls). If it becomes an issue, wrap in a retry loop that catches the constraint violation and re-runs `_find_user_by_email`.

Status: `E2_D_BACKEND_READY_FOR_EDGE_FUNCTION` set 2026-04-08 by VOLAURA-Claude

---

## UPDATE 5 — Peer-review iteration — 2026-04-08 later

After commit 56d3337 the CEO pushed back: "у тебя сомнения, проверь их". I did
proper workflow this time (understand → research → plan → agent critique → fix).

### Research step (tool calls)

- WebSearch + WebFetch of Supabase JWT docs + catjam.fi article confirmed that
  externally-minted JWTs signed with the project JWT secret ARE accepted by
  GoTrue. Article explicitly tested this with auth.getUser().
- Read the supabase-py source at .venv/Lib/site-packages/supabase_auth/_async/
  gotrue_client.py line 678 — get_user() calls `GET /auth/v1/user` with the
  JWT in Authorization header. Signature check is server-side in GoTrue, not
  client-side in Python SDK. Confirms minted JWT approach is sound.
- Read User/UserResponse/AdminUserAttributes types at supabase_auth/types.py
  — my code shape (result.user.id, result.users list) matches.
- Verified email_validator 2.3.0 is installed in backend venv — EmailStr won't
  crash at endpoint load time.
- Verified existing auth.py router already uses EmailStr + /auth prefix —
  no namespace collision because paths are /register /login /me vs /from_external.

### Peer critique step

Ran the full router + migration through 5 diverse model families in parallel:
- Cerebras Qwen 235B — 3.4s — found 5 bugs
- Groq Kimi K2 — 5.2s — found 5 bugs (3 overlap)
- Gemini 2.5 Flash — 9.9s — truncated output (partial)
- NVIDIA Nemotron 120B — 65.6s — found 3 bugs (1 false positive: claimed missing hmac.compare_digest but it was there)
- Ollama Gemma 4 LOCAL — 64.4s — found 3 bugs (1 non-applicable: DB transaction wrap, PostgREST doesn't expose transactions)

### Consensus (2+ models agreed) → applied in commit 9f7c173

Bug 1 — Pagination ceiling at 4k users (Qwen, Kimi, Nemotron, Gemma).
  Fix: new SQL function public.find_shared_user_id_by_email(p_email TEXT) in
  migration 20260408000001. SECURITY DEFINER with search_path=auth,public so
  it can read auth.users. REVOKE from public/anon/authenticated, GRANT
  service_role only. Single O(log n) indexed lookup replaces pagination.
  Router calls via admin.rpc().execute(), returns scalar UUID or None.

Bug 2 — Email case drift (Qwen).
  Fix: normalize at endpoint entry (email_norm = body.email.strip().lower()),
  use that for ALL downstream operations. No more raw body.email.

Bug 3 — Race on create_user (Qwen, Kimi, Nemotron, Gemma).
  Fix: _create_shadow_user catches duplicate-email errors, re-runs
  _find_user_by_email, returns the race winner's UUID. 250ms retry covers
  propagation delay.

Bug 4 — Mapping insert → upsert (Qwen).
  Fix: admin.table("user_identity_map").upsert({...},
  on_conflict="standalone_user_id,standalone_project_ref"). Idempotent.

Bug 5 — Email drift in mapping (Qwen, Kimi).
  Fix: UPDATE mapping.email + last_seen_at on every bridge-reuse call.
  Does NOT update auth.users.email (that needs user admin action).

### False positives in the critique (worth noting)

- Nemotron + Kimi both claimed missing constant-time secret comparison. Wrong
  — hmac.compare_digest is at line 115 (verified by reading the file after
  critique). Both models were pattern-matching against common bugs in that
  shape of code. Don't auto-apply peer critique without verification.
- Gemma 4 suggested wrapping find+create+insert in a DB transaction. Correct
  in theory, but Supabase PostgREST doesn't expose transactions over HTTP.
  The race tolerance (Bug 3 fix) + UPSERT (Bug 4 fix) is the right
  approximation without raw DB access.

### New commit for MindShift-Claude

`D2_BACKEND_HARDENED: 9f7c173` (superseding 56d3337 for the bugs above;
56d3337 is still correct for the migration table schema, router skeleton,
config additions, and main.py registration — 9f7c173 is fixes only)

### Nothing else changed

- Endpoint path still POST /api/auth/from_external
- Request/response schemas still FromExternalRequest / FromExternalResponse
- X-Bridge-Secret still required
- Migration filename still 20260408000001_user_identity_map.sql (added a
  function to the same file, so your D.3 still applies migration once)
- JWT payload shape unchanged
- Your D.3 / D.4 plan needs no adjustments

Status: `E2_D_BACKEND_HARDENED_9F7C173` set 2026-04-08 by VOLAURA-Claude
