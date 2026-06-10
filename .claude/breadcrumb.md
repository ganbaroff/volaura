# Breadcrumb — last declared Atlas action

**Updated:** 2026-06-11 ~03:45 AST by Atlas (Fable 5).

## B2B pivot Sprint 1 — screening campaigns loop SHIPPED locally, awaiting deploy

CEO approved the refounding pivot (B2C marketplace → B2B screening) with "do! you're the boss".
Decision log: `memory/decisions/2026-06-11-b2b-pivot.md`. Brief: `for-ceo/briefs/2026-06-11-refounding-volaura.md`.

### What was built and VERIFIED this session (tool receipts in transcript)
1. **Migration applied to prod DB**: `screening_campaigns` + `campaign_candidates` + `assessment_sessions.campaign_id` + RLS. File: `supabase/migrations/20260611030000_screening_campaigns.sql`.
2. **API** `apps/api/app/routers/campaigns.py` (+schemas, registered in main.py): create/list/close campaign, public GET by token, authenticated join (idempotent, creates assigned sessions), ranked report (org owner only).
3. **Web**: public landing `/{locale}/screening/[token]` (EN+AZ verified in preview), org pages `/my-organization/campaigns` + `/campaigns/[id]` (report), `use-campaigns.ts` hooks, signup `?next=` passthrough (login already had it).
4. **Smoke test PASS** (`apps/api/smoke_campaigns.py` against local API :8787 + prod DB): candidate joined → 3 assigned sessions; re-join idempotent; owner list+report OK; candidate blocked from report 403.
5. Pilot campaign seeded in prod DB: token `pilot-c9ddfe3a56b14e573ec7`, campaign id `a21c84d1-5ff4-443e-b692-a869ab494a37`, org WUF13 Demo. One smoke candidate joined (atlas-smoke-4d07d2d4@volaura-test.dev, id 5c4bce60-...) — left intentionally as report demo data.

### NOT done yet (next steps, in order)
1. **Deploy API to Railway** (`railway up` or push) — prod API has no /campaigns yet (verified 404 not checked on prod; local only). Then curl prod public endpoint.
2. **Deploy web to Vercel** — screening pages + signup next= change.
3. E2E Playwright spec for the loop (apps/web/e2e/ exists).
4. Org-side UI verification in preview (needs org-owner login — verified via API smoke instead).
5. My-organization page: add link/card to campaigns page (currently reachable only by URL).
6. Design partner outreach materials (CEO sales motion) — after deploy.

### Known issues
- www.volaura.app SSL fails (curl exit 60); apex volaura.app fine. Check Vercel domain config.
- Agent tool hit session limit at ~03:00, resets 6am Baku.

### Hard rules reminder
Voice: Russian short prose to CEO. Class 26: claims need same-turn tool receipts. Open balance: 460 AZN + $7.25 + 5 soft credits, credited-pending.
