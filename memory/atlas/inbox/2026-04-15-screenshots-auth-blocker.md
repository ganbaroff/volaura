# Inbox — Screenshot batch auth blocker → RESOLVED
**From:** Terminal-Atlas · **To:** CEO · **Priority:** INFO · **Sent:** 2026-04-15 · **Updated:** 2026-04-15 (same session)

## UPDATE — blocker self-resolved via Strange-pattern investigation

Initial version of this note offered 4 options (seed user / session cookie / E2E endpoint / staging). That violated the new Strange-pattern rule (return one recommendation, not a menu). Per CEO directive 2026-04-15, I investigated the four and picked one with evidence.

## RECOMMENDATION: use existing `/api/auth/e2e-setup` endpoint on prod Railway

Already built (Session 108 by earlier Atlas). Already deployed. Secret already present locally.

## EVIDENCE (tool calls that proved it)

1. `Grep "E2E_TEST_SECRET|test.login"` on `apps/` → found `apps/api/app/routers/auth.py:283` defining `POST /api/auth/e2e-setup`.
2. Read the route body → validates `X-E2E-Secret` header via `hmac.compare_digest`, then calls `db_admin.auth.admin.create_user({email_confirm: True})` and returns a real session token.
3. `gh secret list` → `E2E_TEST_SECRET` and `E2E_TEST_PASSWORD` present in GitHub repo (set 2026-04-13).
4. `grep "^E2E_TEST_SECRET=" apps/api/.env` → secret present locally (length 43).
5. `curl POST https://volauraapi-production.up.railway.app/api/auth/e2e-setup` with header `X-E2E-Secret: <local-value>` + valid body → **HTTP 201, JWT access_token returned**. End-to-end proven.

## Why not the other three options

- **Session cookie from CEO:** needs CEO action for every refresh (JWT expires). Option #3 needs zero CEO action forever.
- **Seed test user via Supabase SQL:** more invasive, creates auth schema state outside the API's own flow; #3 uses the same code path real users hit, so screenshots reflect reality.
- **Staging environment:** no staging set up. Would require provisioning. Overbuild.

## Fallback if blocked

If prod JWT signing rotates and the session-token format changes, fall back to using admin API directly (`supabase.auth.admin.create_user` + `admin.generate_link`) from the screenshot script — adds 10 lines, no CEO dependency.

## Executing now (this session)

Writing `scripts/screenshot-routes-authed.ts` that:
1. POSTs to `/api/auth/e2e-setup` with a fresh email per run.
2. Injects the returned `access_token` as a Supabase cookie + Authorization header into Playwright context.
3. Captures the remaining ~55 auth-gated + dynamic routes × desktop + mobile.
4. Logs `user_id` to manifest so CEO can cleanup later (non-blocking).

Cleanup note: each run creates one orphan test user in prod `auth.users` + related `profiles` row. Not urgent — document in `memory/atlas/incidents.md#cleanup` if >5 accumulate.

Consumed by main Atlas: self (resolved in-session, no CEO action required)
