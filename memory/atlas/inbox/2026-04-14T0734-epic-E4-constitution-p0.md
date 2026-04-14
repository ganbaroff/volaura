# Epic E4 — Constitution P0 Pre-Launch Blockers (D-007)

**Owner:** Atlas
**Duration:** 3 days
**Priority:** P0 for public launch
**Source:** `docs/ECOSYSTEM-CONSTITUTION.md` v1.7, `docs/PRE-LAUNCH-BLOCKERS-STATUS.md`, D-007

## Goal
Close 4 of the 5 key Constitution P0 blockers. 1 may slip with written rationale. These gate public launch, not MVP; but Vision Canon says we don't ship something half-legal.

## Key P0 items (full list in PRE-LAUNCH-BLOCKERS-STATUS.md — 19 total; these are the 5 structural ones)

1. **Energy picker** (overlap with E3 — likely closes there)
2. **Pre-Assessment Layer** — consent, psychotype hint, safety copy before first question
3. **DIF audit** — Differential Item Functioning on seeded questions (fairness across demographic groups)
4. **Grievance mechanism** — how user contests a score
5. **SADPP registration** — Azerbaijan State Agency for Data Protection registration

## Tasks

1. **Pre-Assessment Layer**
   - File: `apps/web/app/[locale]/assessment/pre/page.tsx`
   - Copy: consent to adaptive assessment, psychotype note, "you can pause anytime"
   - Required before first question; stored in `assessment_sessions.consent_at`
   - i18n AZ/RU/EN

2. **DIF audit**
   - Run: `packages/swarm/skills/assessment-science-agent.md` protocol
   - Input: current seeded question bank (`supabase/seed.sql`)
   - Output: `docs/audits/dif-audit-2026-04.md` with per-item DIF scores
   - Action: flag items with DIF > 0.4 for review; remove or reword 3 worst

3. **Grievance mechanism**
   - Endpoint: `POST /v1/score/grievance` — user submits score ID + complaint text
   - DB: `score_grievances` table with RLS (user can insert own)
   - Admin route: internal only for now; Telegram notification on new grievance
   - UI: button on badge page "Contest this score"

4. **SADPP registration**
   - Research: current filing requirements (Cowork can do this in parallel → `docs/research/sadpp/raw.md`)
   - Action: file application; cost < $50 expected
   - CEO notification only if cost > $50 or legal review needed

5. **Shame-free language audit**
   - grep across `apps/web/messages/*.json` for banned phrases
   - Banned list: "you haven't", "incomplete", "missing", profile % indicators
   - Replace per Constitution Law 3

## Files to touch
- `apps/web/app/[locale]/assessment/pre/**`
- `apps/web/app/[locale]/aura/[userId]/grievance-button.tsx`
- `apps/api/app/routers/grievances.py` (new)
- `apps/api/app/schemas/grievance.py` (new)
- `supabase/migrations/YYYYMMDDHHMMSS_add_score_grievances.sql`
- `apps/web/messages/*.json`
- `docs/audits/dif-audit-2026-04.md` (new)
- `docs/research/sadpp/` (Cowork)

## Definition of Done
- [ ] Pre-Assessment page exists, blocks first question until consent_at set
- [ ] DIF audit doc exists with action items
- [ ] 3 worst-DIF items replaced in seed
- [ ] Grievance endpoint + table + UI button live on staging
- [ ] SADPP: either filed (with receipt) or research doc concludes "not needed / waiting for X"
- [ ] No banned-phrase hits in messages/*.json
- [ ] D-007 row in BRAIN.md updated with closed-item count

## Dependencies
E2 (staging) must be live to test endpoints. E1 can run parallel.

## Artifacts
- DIF audit doc
- Decision log `memory/decisions/2026-04-1X-constitution-p0-partial-close.md`
- Journal entries
