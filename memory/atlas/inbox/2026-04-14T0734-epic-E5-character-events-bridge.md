# Epic E5 — MindShift ↔ VOLAURA character_events Bridge (D-004)

**Owner:** Atlas
**Duration:** 2 days
**Priority:** P1 — ecosystem story needs proof-of-life
**Source:** D-004, SYNC §4 (ecosystem data flow), Crystal Law 5

## Goal
`character_events` table receives at least one row from MindShift AND one from VOLAURA, visible in a simple query. This is the first tangible ecosystem signal — "one user, many touchpoints, shared ledger."

## Tasks

1. **Schema verify / create**
   - Check current state of `character_events` table in Supabase
   - If missing: create via migration with columns:
     - `id UUID PK`, `user_id UUID FK → auth.users`, `product TEXT` (volaura/mindshift/lifesim/brandedby/zeus), `event_type TEXT`, `payload JSONB`, `crystal_delta INT DEFAULT 0`, `created_at TIMESTAMPTZ DEFAULT now()`
   - RLS: user can read own; service role writes
   - Index on (user_id, created_at DESC)

2. **VOLAURA emit**
   - On `POST /v1/assessment/submit` success → insert `character_events` row
   - event_type: `assessment_completed`
   - payload: `{ aura_score, badge_tier }`
   - crystal_delta: per Crystal Law formula (e.g., +10 for bronze, +25 gold, +50 platinum)

3. **MindShift emit**
   - Find MindShift codebase location (likely `packages/mindshift/` or separate repo)
   - On focus-session completion → insert row
   - event_type: `focus_session_completed`
   - payload: `{ duration_min, streak_day }`
   - crystal_delta: +1 per session, +5 on streak milestone

4. **Shared Supabase client**
   - Both products must write to SAME Supabase project (VOLAURA main)
   - If MindShift uses separate project → add service-role client pointing to VOLAURA

5. **Verification query**
   - Write `scripts/check-character-events.sql`:
     ```sql
     SELECT product, COUNT(*), MAX(created_at)
     FROM character_events
     WHERE user_id = '<test user>'
     GROUP BY product;
     ```
   - Must show ≥1 from volaura AND ≥1 from mindshift.

## Files to touch
- `supabase/migrations/YYYYMMDDHHMMSS_character_events.sql` (if missing)
- `apps/api/app/routers/assessment.py` (emit on submit)
- `apps/api/app/services/character_events.py` (new helper)
- MindShift focus-session completion handler (location TBD — Atlas discovers)
- `scripts/check-character-events.sql`

## Definition of Done
- [ ] `character_events` table exists with RLS
- [ ] VOLAURA assessment submit → row appears
- [ ] MindShift focus-session → row appears
- [ ] Verification query returns both products
- [ ] D-004 row in BRAIN.md updated

## Dependencies
E2 (staging live). E1 nice-to-have.

## Risks
- MindShift code location unclear → Atlas may need 30 min of discovery. Acceptable.
- If MindShift is on separate Supabase project → cross-project write needs service-role key. Budget extra half day.

## Artifacts
- Migration file
- Decision log `memory/decisions/2026-04-1X-character-events-bridge.md` if schema differs from spec
- Journal with verification query output
