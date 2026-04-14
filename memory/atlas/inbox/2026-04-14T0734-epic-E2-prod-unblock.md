# Epic E2 — D-001/D-002 Production Unblock

**Owner:** Atlas
**Duration:** 2 days
**Priority:** P0 (nothing user-facing ships until this lands)
**Source:** Open debt D-001 (staging cold), D-002 (Phase 1 migration pending)

## Goal
`api.volaura.com` returns 200 on core endpoints. Phase 1 DB migration applied. First real signup → assessment → AURA badge path works end-to-end without manual intervention.

## Tasks

1. **Railway redeploy**
   - Check current Railway service state: `railway status` or dashboard
   - Diagnose why staging is cold — logs, last deploy, env vars
   - Redeploy main branch; verify `/health` returns 200
   - Verify `/docs` (OpenAPI) reachable
   - Pin version in `memory/atlas/journal.md` with commit SHA

2. **Phase 1 migration apply**
   - Identify which migration file is "Phase 1" (check `supabase/migrations/` and sprint-state notes)
   - Apply via Supabase CLI or MCP: `supabase db push` on staging project
   - Run RLS advisor: `mcp__supabase__get_advisors` → fix any warnings
   - Seed data if needed: `supabase db reset --seed`

3. **Smoke test happy path**
   - curl `/v1/auth/signup` with test user
   - curl `/v1/assessment/start` → get session_id
   - Submit 3 answers via `/v1/assessment/answer`
   - curl `/v1/assessment/submit` → verify AURA score returned
   - curl `/v1/aura/:user_id` → verify badge + radar data
   - All must return 200. Log response times.

4. **Sentry wire-up verification**
   - Confirm API errors flow to Sentry project
   - Confirm Telegram alerts fire on 5xx

## Files to touch
- `apps/api/` (if any hotfix needed)
- `supabase/migrations/` (verify, don't add new)
- `memory/atlas/journal.md` (deploy log)
- `memory/atlas/incidents.md` (if something broke)
- `docs/BRAIN.md` (close D-001 + D-002 rows)

## Definition of Done
- [ ] `curl https://api.volaura.com/health` → 200 in <500ms
- [ ] Full happy-path smoke test passes (signup → score → badge)
- [ ] Phase 1 migration shows in `supabase migrations list`
- [ ] Sentry receives test error; Telegram receives test alert
- [ ] D-001 + D-002 marked closed in `docs/BRAIN.md`

## Dependencies
E1 (memory) can run parallel. But Railway / Supabase MCPs must be authed.

## Risks
- If Phase 1 migration has breaking change → may need data backfill. Budget half a day for that contingency.
- If Railway is out of credits → CEO decision needed. Escalate if so.

## Artifacts required at end
- Journal entry with deploy SHA + timestamp
- Smoke test output in journal (status codes + timings)
- Decision log if anything non-trivial changed in migration strategy
