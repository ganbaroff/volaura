# VOLAURA FULL PLATFORM AUDIT — 2026-03-29

**Audited by:** 5 parallel agents (Security, Product, Architecture/DB, i18n, TypeSafety)
**Scope:** Every router, every page, every migration, every i18n key, every type
**Total findings:** 62

---

## SUMMARY BY SEVERITY

| Severity | Count | Description |
|----------|-------|-------------|
| **P0** | 8 | Platform broken / user sees wrong data / security hole |
| **P1** | 19 | Bad UX / data integrity risk / hardcoded strings |
| **P2** | 22 | Polish / inconsistency / technical debt |
| **P3** | 13 | Cosmetic / comments / low-priority cleanup |

---

## P0 — CRITICAL (fix before any new features)

### P0-01: Root layout title says "Elite Volunteer Talent Platform"
- **File:** `apps/web/src/app/[locale]/layout.tsx:18-20`
- **Issue:** Hardcoded `title: "Volaura — Elite Volunteer Talent Platform"` and description with "volunteer" — appears in browser tabs, SEO, social shares
- **Fix:** Create i18n keys `landing.metaTitle` / `landing.metaDescription`, use them in layout

### P0-02: 15+ direct fetch() calls bypass apiFetch client
- **Files:** callback/page.tsx, welcome/page.tsx, onboarding/page.tsx, assessment/page.tsx, assessment/[sessionId]/page.tsx, verify/[token]/page.tsx, organizations/[id]/page.tsx, u/[username]/page.tsx, card/route.tsx, my-organization/invite/page.tsx
- **Issue:** All bypass type validation, error handling, and auth header injection. If API response shape changes, these break silently.
- **Fix:** Convert all to `apiFetch()` from `@/lib/api/client`

### P0-03: 11x "as unknown as" type casts in query hooks
- **Files:** use-aura.ts (4x), use-profile.ts (3x), use-events.ts (4x+), use-organizations.ts (4x)
- **Issue:** Bypasses TypeScript — runtime errors if API response differs from expected shape
- **Fix:** Create type guard functions for each response type

### P0-04: Missing error state — my-organization page
- **File:** `apps/web/src/app/[locale]/(dashboard)/my-organization/page.tsx:97`
- **Issue:** No error UI when useMyOrganization fails — infinite spinner
- **Fix:** Add error handling like other dashboard pages

### P0-05: No 401 redirect on public events page
- **File:** `apps/web/src/app/[locale]/(public)/events/page.tsx:30-35`
- **Issue:** Fetches events without auth check — if API returns 401, no redirect
- **Fix:** Add auth check and 401 handler

### P0-06: BadgeDistribution + OrgDashboardStats duplicated
- **File:** `apps/web/src/lib/api/types.ts:135-162`
- **Issue:** Manual types duplicate generated types — will drift when API changes
- **Fix:** Re-export from `generated/types.gen.ts` instead of manual definition

### P0-07: overall_score vs total_score schema mismatch (DB)
- **File:** `apps/api/app/schemas/organization.py:110,145`
- **Issue:** Schema uses `overall_score` but DB column is `total_score` — Pydantic `from_attributes=True` will crash
- **Fix:** Change schema to use `total_score` or add `Field(alias='total_score')`

### P0-08: Character event pagination off-by-one
- **File:** `apps/api/app/routers/character.py:254`
- **Issue:** `range(offset, offset + limit - 1)` returns 49 rows when limit=50
- **Fix:** Change to `range(offset, offset + limit)`

---

## P1 — HIGH (fix this sprint)

### P1-01: Rate limit token hash truncated to 12 chars — collision risk
- **File:** `apps/api/app/middleware/rate_limit.py:37`
- **Fix:** Use 20+ char hash to eliminate collisions at scale

### P1-02: Telegram webhook file write TOCTOU race
- **File:** `apps/api/app/routers/telegram_webhook.py:260`
- **Fix:** Use atomic write (tempfile + rename) or migrate to DB

### P1-03: Discovery cursor pagination incomplete
- **File:** `apps/api/app/routers/discovery.py:18`
- **Fix:** Implement keyset pagination for sort_by=events/recent, or disable those sorts

### P1-04: Auth router logs PII (email in f-string)
- **File:** `apps/api/app/routers/auth.py:102`
- **Fix:** Hash email before logging

### P1-05: Bearer token empty string not validated
- **File:** `apps/api/app/deps.py:38-39`
- **Fix:** Add `if not token.strip(): raise HTTPException(401)`

### P1-06: Events draft visibility confusing for org owners
- **File:** `apps/api/app/routers/events.py:47`
- **Fix:** Return draft events to org owners, 404 for others

### P1-07: Verification token double-guard redundancy (documentation needed)
- **File:** `apps/api/app/routers/verification.py:198-203`
- **Fix:** Document the defensive guard pattern

### P1-08: Memory leak — welcome page missing isMounted check
- **File:** `apps/web/src/app/[locale]/welcome/page.tsx:85-97`
- **Fix:** Add isMounted check before setState calls

### P1-09: Hardcoded placeholder "Leyla Hasanova" in onboarding
- **File:** `apps/web/src/app/[locale]/(dashboard)/onboarding/page.tsx:281`
- **Fix:** Use i18n key or generic placeholder

### P1-10: Hardcoded "Baku, Azerbaijan" location placeholder
- **File:** `apps/web/src/app/[locale]/(dashboard)/onboarding/page.tsx:322`
- **Fix:** Use i18n key

### P1-11: Hardcoded "COP29 Volunteer Team" org placeholder
- **File:** `apps/web/src/app/[locale]/(dashboard)/my-organization/page.tsx:66`
- **Fix:** Use i18n key

### P1-12: Mock data contains hardcoded "volunteers" text
- **File:** `apps/web/src/lib/mock-data.ts:67,69`
- **Fix:** Replace with "professionals"

### P1-13: AZ locale "languageEnglish" not translated
- **File:** `apps/web/src/locales/az/common.json:302`
- **Issue:** Says "English" instead of "Ingilis dili"
- **Fix:** Translate to Azerbaijani

### P1-14: Intro requests silent deletion on org account delete
- **File:** `supabase/migrations/20260328240002_create_intro_requests.sql:7-8`
- **Fix:** Consider notification trigger when org deletes account

### P1-15: toAuraScore has unused verification_level field
- **File:** `apps/web/src/lib/api/types.ts:38`
- **Fix:** Remove from AuraScore type (never populated)

### P1-16: toProfile missing badge_tier mapping
- **File:** `apps/web/src/lib/api/types.ts:80`
- **Fix:** Remove badge_tier from Profile type (not in API response)

### P1-17: ActivityItem type conflict (API vs component)
- **File:** `apps/web/src/lib/api/types.ts:115`
- **Fix:** Rename to ApiActivityItem

### P1-18: Badge interface uses weak Record<string, unknown>
- **File:** `apps/web/src/lib/api/types.ts:105`
- **Fix:** Define concrete metadata type

### P1-19: Assessment page direct fetch with inline type cast
- **File:** `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/page.tsx:122,192,236`
- **Fix:** Use apiFetch + generated types

---

## P2 — MEDIUM (fix next 2 sprints)

### P2-01: Leaderboard swallows exceptions, returns 200
- `apps/api/app/routers/leaderboard.py:106` — Return 503 on failure
### P2-02: Badges .single() instead of .maybe_single()
- `apps/api/app/routers/badges.py:45` — Returns 406 instead of 404
### P2-03: Skills hardcoded rate limit "5/minute"
- `apps/api/app/routers/skills.py:202` — Use RATE_LLM constant
### P2-04: Event capacity counts pending+approved but not waitlisted
- `apps/api/app/routers/events.py:149` — Clarify capacity semantics
### P2-05: Embeddings failure silent — no logging
- `apps/api/app/services/embeddings.py:14` — Add error details to log
### P2-06: LLM timeout uses f-string instead of structured logging
- `apps/api/app/services/llm.py:43` — Use keyword args
### P2-07: Notification service no retry logic
- `apps/api/app/services/notification_service.py` — Add retry for critical types
### P2-08: scenario_ru fallback not hardened in assessment router
- `apps/api/app/routers/assessment.py` — Add `scenario_ru or scenario_en` fallback
### P2-09: 'assigned' status transition logic unverified
- `apps/api/app/routers/assessment.py` — Verify engine handles assigned→in_progress
### P2-10: Notifications table missing updated_at trigger
- `supabase/migrations/20260328240001` — Add trigger + column
### P2-11: Supabase client per-request never explicitly closed
- `apps/api/app/deps.py:48-53` — Document lifecycle
### P2-12: Config anon key hardcoded needs warning comment
- `apps/api/app/config.py:16-22` — Add warning about RLS implications
### P2-13: Invites _validate_uuid duplicated across routers
- `apps/api/app/routers/invites.py:321` — Move to shared utils
### P2-14: Organizations /me/dashboard incomplete audit
- `apps/api/app/routers/organizations.py:115` — Full code review needed
### P2-15: Missing auth guard on public org page
- `apps/web/src/app/[locale]/(public)/organizations/page.tsx:100`
### P2-16: No loading skeleton for activity feed header
- `apps/web/src/app/[locale]/(dashboard)/dashboard/page.tsx:220`
### P2-17: Leaderboard avatar fallback produces "#" symbol
- `apps/web/src/hooks/queries/use-leaderboard.ts:49`
### P2-18: My org stats grid not responsive on mobile
- `apps/web/src/app/[locale]/(dashboard)/my-organization/page.tsx:191`
### P2-19: DashboardStats custom type unverified against backend
- `apps/web/src/lib/api/types.ts:124` — Verify fields exist in API
### P2-20: Card route makes 2 aura fetches instead of 1
- `apps/web/src/app/u/[username]/card/route.tsx:65`
### P2-21: Character events payload unindexed (GIN needed at scale)
- `supabase/migrations/20260327000031` — Add before 1K users
### P2-22: Percentile NULL on launch (expected but confusing UX)
- `supabase/migrations/20260327190500:49-68` — Add UX fallback

---

## P3 — LOW (backlog)

### P3-01: Invites duplicate count calculation
- `apps/api/app/routers/invites.py:226`
### P3-02: Telegram file handling — proposals.json may not exist
- `apps/api/app/routers/telegram_webhook.py:218`
### P3-03: Router inclusion order undocumented
- `apps/api/app/main.py:127-145`
### P3-04: Security header comment misleading
- `apps/api/app/middleware/security_headers.py:35`
### P3-05: Unused isMounted ref in dashboard
- `apps/web/src/app/[locale]/(dashboard)/dashboard/page.tsx:62-67`
### P3-06: Hardcoded API_URL in card/route.tsx
- `apps/web/src/app/u/[username]/card/route.tsx:13`
### P3-07: API variable names use volunteer_id (technical debt)
- Multiple files — API contract, keep as-is, document
### P3-08: Test email "volunteer@volaura.az" in test fixtures
- `apps/web/src/app/[locale]/__tests__/auth-flows.test.tsx:151`
### P3-09: Internal hook names use "volunteer" (e.g., useAuraScoreByVolunteer)
- Multiple hooks — rename in future cleanup
### P3-10: Onboarding AccountType = "volunteer" | "organization"
- `apps/web/src/app/[locale]/(dashboard)/onboarding/page.tsx:10`
### P3-11: Competency can_retake has no audit trail
- `supabase/migrations/20260328230000` — Deferred to Phase 2
### P3-12: Percentile formula uses +1 denominator
- `supabase/migrations/20260327190500:49` — Mathematically correct but confusing
### P3-13: get_character_state missing SET search_path
- `supabase/migrations/20260327000031` — Minor, no cross-schema access

---

## GREEN FLAGS (working well)

- RLS is fortress-grade (comprehensive audit in migration 000015)
- Atomic crystal deduction (advisory lock prevents double-spend)
- AURA weights correct (sum=1.0, 8 competencies)
- Seed data production-ready (IRT params reasonable)
- Decay math scientifically sound (per-competency Ebbinghaus)
- Assessment anti-gaming gates (4 multiplicative penalties)
- i18n coverage: 588 keys EN = 588 keys AZ (complete match)
- All timestamps TIMESTAMPTZ
- All IDs UUID
- Snake_case everywhere
- Retake cooldown server-side (7 days, not bypassable)

---

## RECOMMENDED WORK ORDER

### Batch 1: P0 fixes (2-3 hours, 8 tasks)
All micro/small. Ship immediately. No new features until these are done.

### Batch 2: P1 fixes (4-6 hours, 19 tasks)
Mix of micro and small. Most are 1-line fixes. Group by domain.

### Batch 3: P2 fixes (1-2 days, 22 tasks)
Technical debt + polish. Can run parallel with feature work.

### Batch 4: P3 (backlog)
Fix opportunistically when touching related files.
