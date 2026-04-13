# Handoff: volunteer_id → professional_id rename
**From:** Cowork | **Date:** 2026-04-13 | **Priority:** P2

## Context
`volunteer` terminology was purged from seed.sql and user-facing strings (Session 94). But the DB column `volunteer_id` persists in 11 tables, 4 RPC functions, 138 code references across 15 Python files. This is tech debt — not user-facing now, but blocks clean onboarding of B2B clients who'd audit the schema.

## Scope

### Database columns (11 tables)
| Table | Column | Has FK? |
|-------|--------|---------|
| assessment_sessions | volunteer_id | → profiles.id |
| aura_scores | volunteer_id | → profiles.id |
| aura_scores_public | volunteer_id | (view or copy?) |
| evaluation_queue | volunteer_id | → profiles.id |
| expert_verifications | volunteer_id | → profiles.id |
| intro_requests | volunteer_id | → profiles.id |
| organization_ratings | volunteer_id | → profiles.id |
| registrations | volunteer_id | → profiles.id |
| volunteer_badges | volunteer_id | → profiles.id |
| volunteer_behavior_signals | volunteer_id | → profiles.id |
| volunteer_embeddings | volunteer_id | → profiles.id |

### RPC functions (4)
- `calculate_aura_score(p_volunteer_id)` — references aura_scores.volunteer_id
- `calculate_reliability_score(p_volunteer_id)` — references event_registrations.volunteer_id
- `match_volunteers(...)` — references volunteer_embeddings + aura_scores + profiles
- `upsert_aura_score(p_volunteer_id)` — heavy function, references aura_scores.volunteer_id throughout

### Python files (15 files, 138 references)
| File | Count | Notes |
|------|-------|-------|
| routers/organizations.py | 44 | Heaviest — org dashboard, member list, bulk assign |
| routers/assessment.py | 20 | Session CRUD, submit answer, complete |
| routers/events.py | 14 | Registration, check-in, AURA lookup |
| services/reeval_worker.py | 12 | Re-evaluation pipeline |
| services/notification_service.py | 8 | Profile view notifications |
| routers/activity.py | 8 | Activity feed queries |
| routers/badges.py | 8 | Credential/badge endpoints |
| routers/leaderboard.py | 7 | Global + org leaderboards |
| services/match_checker.py | 6 | Tribe matching |
| services/tribe_matching.py | 2 | Tribe AURA lookup |
| services/embeddings.py | 2 | Vector upsert |
| routers/skills.py | 2 | AURA lookup for skill gating |
| schemas/aura.py | 2 | Pydantic models |
| schemas/event.py | 2 | Pydantic models |
| schemas/verification.py | 1 | Verification request model |

### Also rename these tables
- `volunteer_badges` → `professional_badges` (or `user_badges`)
- `volunteer_behavior_signals` → `professional_behavior_signals`
- `volunteer_embeddings` → `professional_embeddings`

### RLS policies
Check and update any RLS policies that reference `volunteer_id` column name.

## Migration strategy
1. **Add new column** `user_id` (or `professional_id`) alongside `volunteer_id` in each table
2. **Copy data** `UPDATE table SET user_id = volunteer_id`
3. **Update RPC functions** to use new column name
4. **Update Python code** (138 refs → find-and-replace with verification)
5. **Update RLS policies**
6. **Drop old column** after verification period
7. **Rename tables** (volunteer_badges, volunteer_behavior_signals, volunteer_embeddings)

Alternative (simpler): Single migration with `ALTER TABLE ... RENAME COLUMN volunteer_id TO user_id` — faster but requires downtime or coordinated deploy (code + DB at same time).

## Acceptance Criteria
- [ ] AC1: Zero occurrences of `volunteer_id` in `apps/api/app/` (grep returns 0)
- [ ] AC2: Zero DB columns named `volunteer_id` in public schema
- [ ] AC3: All 4 RPC functions use new parameter name
- [ ] AC4: All 832 tests pass
- [ ] AC5: E2E bot completes full assessment cycle
- [ ] AC6: No tables named `volunteer_*` in public schema

## Risks
- **Downtime risk:** Rename-column approach needs code deploy simultaneously with migration
- **RLS breakage:** Policies may hardcode column name
- **Cached queries:** Supabase PostgREST may cache column metadata — restart needed
- **aura_scores_public:** May be a view — check before renaming underlying column

## Files to Read First
- This handoff (full reference map)
- `supabase/migrations/` — check existing FKs and constraints
- Each Python file listed above

## On Completion
1. Update sync/claudecode-state.md
2. Update sync/heartbeat.md
3. Update STATE.md — mark volunteer_id rename as DONE
4. Update SHIPPED.md
