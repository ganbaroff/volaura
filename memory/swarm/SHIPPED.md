# SHIPPED — What Exists in Production

**Purpose:** CTO reads this at session start. Single source of truth for "what code is live."
**Updated by:** CTO or agents after every session that adds/changes code.
**Rule:** If it's not here — CTO doesn't know it exists.

---

## Session 60 (2026-03-28) — SPRINT 4: BACKEND WIRING + B2B PATH

| Code | Location | What it does | Status | How to verify |
|------|----------|-------------|--------|---------------|
| Migration: `profiles_org_fields` | `supabase/migrations/20260328240000_...` | Adds account_type (volunteer/organization), visible_to_orgs, org_type to profiles. Index on visible_to_orgs=TRUE. | ✅ APPLIED | `SELECT account_type, visible_to_orgs FROM profiles LIMIT 1` |
| Migration: `create_notifications` | `supabase/migrations/20260328240001_...` | notifications table: 7 types, user_id FK, is_read, RLS (user reads own, service inserts) | ✅ APPLIED | `SELECT * FROM notifications LIMIT 1` |
| Migration: `create_intro_requests` | `supabase/migrations/20260328240002_...` | intro_requests table: org→volunteer, timeline enum, status, unique pending index, 4 RLS policies | ✅ APPLIED | `SELECT * FROM intro_requests LIMIT 1` |
| Events pages: real API | `apps/web/src/app/[locale]/(public)/events/` | events/page.tsx + events/[id]/page.tsx use real `useEvents`/`useEvent` hooks. `event-card.tsx` and `events-list.tsx` use `EventResponse` (snake_case fields). `getMockEvents()` removed. | ✅ LIVE | Visit /events in browser |
| `DiscoverableVolunteer` schema | `apps/api/app/schemas/profile.py` | New Pydantic model for the public volunteer browse response | ✅ LIVE | `GET /api/profiles/public` |
| `GET /api/profiles/public` | `apps/api/app/routers/profiles.py` | Org-only endpoint: lists visible_to_orgs=TRUE volunteers with AURA join, ordered by score | ✅ LIVE | Need org JWT to call |
| `/discover` dashboard page | `apps/web/src/app/[locale]/(dashboard)/discover/page.tsx` | Org-only volunteer browse: search by name/location, badge tier badge, AURA score, click→/u/username | ✅ LIVE | Visit /az/discover as org user |
| `useDiscoverableVolunteers()` | `apps/web/src/hooks/queries/use-profile.ts` | React Query hook for GET /api/profiles/public | ✅ LIVE | Used by /discover page |
| `IntroRequestCreate/Response` schemas | `apps/api/app/schemas/organization.py` | Pydantic models: volunteer_id (UUID validated), timeline enum, project_name, message (max 500) | ✅ LIVE | Part of POST endpoint |
| `POST /api/organizations/intro-requests` | `apps/api/app/routers/organizations.py` | Dual org-role check + volunteer visibility guard + 5/hour rate limit + fire-and-forget notification | ✅ LIVE | POST with org JWT |
| `useCreateIntroRequest()` | `apps/web/src/hooks/queries/use-organizations.ts` | Mutation hook: JSON.stringify body, 409 dedup handling, ApiError typed | ✅ LIVE | Used by IntroRequestButton |
| `IntroRequestButton` | `apps/web/src/components/profile/intro-request-button.tsx` | Client component: org-only gate via useMyOrganization(), modal (3 fields), success/error toast | ✅ LIVE | Visit /u/[username] as org user |

## Session 51 (2026-03-27) — ARCHITECTURE SPRINT

| Code | Location | What it does | Status | How to verify |
|------|----------|-------------|--------|---------------|
| `memory_consolidation.py` | `packages/swarm/` | Hippocampus→neocortex: reads agent-feedback-log.md, distills to agent-feedback-distilled.md, archives old entries. Runs daily in GitHub Actions at 09:00 Baku. | ✅ LIVE | `python3 -m packages.swarm.memory_consolidation` |
| `skill_evolution.py` | `packages/swarm/` | Scans `memory/swarm/skills/*.md`, checks quality (triggers, outputs, cross-refs), generates improvements via LLM, appends to skill-evolution-log.md. Runs daily AFTER memory_consolidation. | ✅ LIVE | `python3 -m packages.swarm.skill_evolution` |
| `skills.py` router | `apps/api/app/routers/` | `POST /api/skills/{name}` — executes any skill by name, passes user context, returns LLM output. `GET /api/skills/` — list available skills. | ✅ LIVE | `curl -X POST .../api/skills/aura-coach` |
| Telegram bidirectional | `apps/api/app/routers/telegram.py` | CEO can RESPOND to proposals via Telegram bot. Responses written to `memory/swarm/ceo-inbox.md`. Commands: /proposals, /ask {agent}, act {id}, dismiss {id}, defer {id} | ✅ LIVE | Send `/proposals` to @volaurabot |
| `swarm-freedom-architecture.md` | `memory/swarm/` | Documents temp 1.0 mandate, freedom protocol, convergent signal rules, roadmap to full autonomy | ✅ DOC | Read-only reference |
| NotebookLM notebook | External | Competitive landscape research. Sources: 12 competitor analyses. v0Laura moat: 6 elements. | ✅ LIVE | notebook ID: a76be380 |

## Session 51 — Product Skills (6 new files in `memory/swarm/skills/`)

| Skill | Replaces | What it does |
|-------|---------|-------------|
| `content-formatter.md` | BrandedBy standalone | Multi-format content generation (POST_CLEAN + TELEGRAM + EMAIL + CTA) |
| `aura-coach.md` | MindShift standalone | Personalized coaching based on AURA score gaps |
| `assessment-generator.md` | ZEUS standalone | Generates assessment questions, scenarios, keywords for any competency |
| `behavior-pattern-analyzer.md` | MindShift behavioral engine | Identifies user behavior patterns, predicts needs |
| `ai-twin-responder.md` | BrandedBy AI Twin | AI Twin responses in user's voice, uses MindShift memory |
| `feed-curator.md` | Life Simulator feed | Personalized content feed based on AURA + behavior patterns |

## Session 53 (2026-03-28) — OWASP + UX SPRINT

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| `deduct_crystals_atomic()` | `supabase/migrations/20260328000040_atomic_crystal_deduction.sql` | Atomic crystal deduction with pg_advisory_lock. Prevents TOCTOU double-spend. | ✅ APPLIED TO PROD |
| `bottom-nav.tsx` | `apps/web/src/components/layout/` | Mobile bottom navigation, 5 tabs, 72px, ADHD-first always-visible labels | ✅ LIVE |
| `assessment-store.ts` (persist) | `apps/web/src/stores/` | Zustand persist middleware (sessionStorage). Survives page refresh. | ✅ LIVE |
| `POST /api/auth/logout` | `apps/api/app/routers/auth.py` | Logout endpoint with audit logging | ✅ LIVE |
| OWASP fixes (15 of 22) | various | Rate limits, audit logs, error sanitization, webhook auth, deleted /health/env-debug | ✅ LIVE |

## Session 54 (2026-03-28) — USER SIMULATION SPRINT

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| `GET /api/leaderboard/me` | `apps/api/app/routers/leaderboard.py` | Returns current user's rank (users_with_higher_score + 1) | ✅ LIVE |
| `useMyLeaderboardRank` hook | `apps/web/src/hooks/queries/use-leaderboard.ts` | TanStack Query hook for leaderboard rank | ✅ LIVE |
| Share buttons (copy fallback) | `apps/web/src/components/aura/share-buttons.tsx` | execCommand fallback for HTTP clipboard, async TikTok flow | ✅ LIVE |

## Session 55 (2026-03-28) — HOUSEKEEPING SPRINT

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| `START-SESSION-VOLAURA.md` | root | Brain activation file. Mandatory first read every session. | ✅ LIVE |
| `volaura-security-review/skill.md` | `docs/openspace-skills/` | OpenSpace-format 10-point OWASP checklist for FastAPI endpoints | ✅ LIVE |
| OpenSpace MCP | `C:/tools/openspace-venv` | MCP server for reusable skill patterns. Tools: execute_task, search_skills, upload_skill, fix_skill | ✅ LIVE |
| `feedback_swarm_patterns.md` | `memory/swarm/` | Temp 1.0 rules, convergent signal patterns, swarm anti-patterns | ✅ DOC |
| `SHIPPED.md` | `memory/swarm/` | THIS FILE — log of what exists in production | ✅ DOC |

## Session 56 (2026-03-28) — AURA COACH + DASHBOARD FIX

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| `aura-coach` wired to `/aura` | `apps/web/src/app/[locale]/(dashboard)/aura/page.tsx` | `useSkill("aura-coach")` fires after reveal animation. Shows STRENGTH_MAP + GROWTH_PATH + PEER_CONTEXT. Skeleton during load → AuraCoach component. | ✅ LIVE |
| AURA 404 fix | `apps/web/src/app/[locale]/(dashboard)/aura/page.tsx` | API returns 404 when no score → frontend now shows "Start Assessment" instead of crashing | ✅ LIVE |

## Session 57 (2026-03-28) — TEAM EXPANSION + SPRINT PLAN V3

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| `sales-deal-strategist.md` | `memory/swarm/skills/` | B2B deal strategy, pricing, org onboarding | ✅ SKILL |
| `sales-discovery-coach.md` | `memory/swarm/skills/` | Discovery questions, intro requests, B2B flow | ✅ SKILL |
| `linkedin-content-creator.md` | `memory/swarm/skills/` | AURA-to-LinkedIn portability, professional brand | ✅ SKILL |
| `cultural-intelligence-strategist.md` | `memory/swarm/skills/` | CIS/AZ cultural framing, trust signals, naming | ✅ SKILL |
| `behavioral-nudge-engine.md` | `memory/swarm/skills/` | ADHD-first design, cognitive load, engagement | ✅ SKILL |
| `accessibility-auditor.md` | `memory/swarm/skills/` | WCAG, AZ chars (ə ğ ş ç), mobile a11y — activates Sprint 6 | ✅ SKILL |
| `RECURSIVE-CRITICISM.md` | `docs/engineering/skills/` | Standard: 2-round critique on all plans before execution | ✅ DOC |
| `SPRINT-PLAN-V3.md` | `docs/` | Final plan: 8 sprints, 25 days, swarm-validated (38/50) | ✅ DOC |
| Railway deploy fix | root `railway.toml` + `Dockerfile.railway` | Fixes Railway building Node instead of Python — root-level config now forces Docker | ✅ LIVE |

## Session 59 (2026-03-28) — SPRINT 3: API CONTRACTS + ASSESSMENT REFACTOR

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| Assessment router split | `services/assessment/` (3 modules) | `rewards.py` (crystal+skill events), `helpers.py` (DB lookups), `coaching_service.py` (Gemini+fallbacks). Router 919→660 lines. | ✅ LIVE |
| `CoachingTip`, `CoachingResponse`, `AssessmentInfoOut` | `schemas/assessment.py` | Moved from router, added to schemas | ✅ LIVE |
| `QuestionResultOut`, `QuestionBreakdownOut` | `schemas/assessment.py` | Per-question result with mapped difficulty labels (no IRT leak) | ✅ LIVE |
| `GET /assessment/info/{slug}` | `routers/assessment.py` | Pre-assessment info: time estimate, can_retake, days_until_retake | ✅ LIVE |
| `GET /assessment/results/{id}/questions` | `routers/assessment.py` | Per-question breakdown: difficulty_label, is_correct, response_time_ms. IRT params mapped to easy/medium/hard/expert. | ✅ LIVE |
| Competency info migration | `supabase/migrations/20260328230000` | `time_estimate_minutes`, `can_retake` columns added to competencies | ✅ APPLIED |
| Events rate limit fix | `routers/events.py` | Added @limiter.limit to GET /{id} and GET /{id}/registrations | ✅ LIVE |
| B2B search API docs | `docs/api/volunteer-search-api.md` | Full request/response spec for org volunteer search | ✅ DOC |
| API E2E tests (3) | `tests/test_assessment_api_e2e.py` | Happy path, retest cooldown, question breakdown security | ✅ TEST |
| RLS write vectors (6) | `tests/test_rls_audit.py` | UPDATE/DELETE/INSERT isolation, questions_safe enforcement, naked TRUE check | ✅ TEST |
| Protocol enforcement hook | `.claude/hooks/protocol-enforce.sh` | Blocks Edit/Write on apps/ until protocol step >= 6 | ✅ LIVE |
| TASK-PROTOCOL v2.0 | `docs/TASK-PROTOCOL.md` + `CHECKLIST.md` | v2.0: context check, blockers, exit condition, doc gate, pre-commit review | ✅ DOC |

## Session 58 (2026-03-28) — SPRINT 1+2 SECURITY HARDENING

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| Signup redesign | `apps/web/src/app/[locale]/(auth)/signup/page.tsx` | Role selector (volunteer/org), org_type dropdown, AZ privacy consent, display_name removed | ✅ LIVE |
| Onboarding rewrite | `apps/web/src/app/[locale]/(dashboard)/onboarding/page.tsx` | username pre-fill from user_metadata, org 2-step flow, visible_to_orgs toggle (default OFF), org_type forwarded to API | ✅ LIVE |
| `account_type`, `visible_to_orgs`, `org_type` fields | `apps/api/app/schemas/profile.py` + `supabase/migrations/` | New profile fields with validators. Migration applied to prod. | ✅ LIVE |
| `ProxyHeadersMiddleware` | `apps/api/app/main.py` | Railway proxy: real client IP now reaches rate limiter (was always proxy IP) | ✅ LIVE |
| Professional empty states | `apps/web/src/app/[locale]/(dashboard)/dashboard/page.tsx` | NoScoreBanner: volunteer → "Companies searching for you", org → "Verified talent waiting" | ✅ LIVE |
| Assessment retest cooldown | `apps/api/app/routers/assessment.py` | 7-day block per competency after completion | ✅ LIVE |
| Abuse monitoring | `apps/api/app/routers/assessment.py` | >10 starts/day → logger.warning (no block) | ✅ LIVE |
| Rate limits (11 endpoints) | `activity.py`, `auth.py`, `profiles.py`, `organizations.py`, `invites.py`, `events.py` | @limiter.limit added to 11 endpoints previously unprotected | ✅ LIVE |
| UUID validation | `events.py` (8 handlers), `assessment.py` GET /results | `_validate_uuid()` helper + call on all event_id and session_id path params | ✅ LIVE |
| Crystal ledger fix | `apps/api/app/routers/brandedby.py` | `"delta"` → `"amount"`, removed non-existent columns `reason`/`source_event_type` | ✅ LIVE |
| Seed events (10 events) | Supabase migration | 10 events with relative dates (NOW() + INTERVAL), status=open | ✅ APPLIED |
| `TASK-PROTOCOL.md` | `docs/` | 10-step swarm critique loop: skills → plan → critique → response → counter-critique → execute → report → swarm review. Hard gates. | ✅ DOC |

---

## DAILY EXECUTION CYCLE (what runs automatically)

```
09:00 Baku → .github/workflows/swarm-daily.yml
  ├── 1. autonomous_run.py (5 agents, temp 1.0)
  │       → proposals.json updated
  │       → HIGH/CRITICAL → Telegram to CEO
  ├── 2. memory_consolidation.py
  │       → agent-feedback-log.md → agent-feedback-distilled.md
  │       → episodic_inbox/ archives old entries
  └── 3. skill_evolution.py
          → scans memory/swarm/skills/*.md
          → suggests improvements → skill-evolution-log.md
```

## Session 56 (2026-03-28) — SKILL WIRING SPRINT

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| `aura-coach` wired to `/aura` page | `apps/web/src/app/[locale]/(dashboard)/aura/page.tsx` | `useSkill("aura-coach")` fires after reveal animation. Shows loading skeleton → AuraCoach component renders STRENGTH_MAP + GROWTH_PATH + PEER_CONTEXT text. | ✅ LIVE |
| `feed-curator` wired to `/dashboard` | already existed from Session 54 | `useSkill("feed-curator")` + `FeedCards` component — confirmed wired and complete. | ✅ CONFIRMED |
| `leaguePosition` type fix | `apps/web/src/app/[locale]/(dashboard)/dashboard/page.tsx` | `myRank?.rank` (number) now formatted as `#${rank}` string. TS error resolved. | ✅ LIVE |
| `RevealCurtain` missing `t()` fix | `apps/web/src/app/[locale]/(dashboard)/aura/page.tsx` | Pre-existing bug: `t()` called without `useTranslation()`. Added hook call. | ✅ LIVE |
| AURA 404→empty state fix | `apps/web/src/hooks/queries/use-aura.ts` | API returns 404 when no score exists. Previously threw error ("Something went wrong"). Now returns null → page shows empty state with "Start Assessment" CTA. | ✅ LIVE |
| Sprint Plan v2 (3-round swarm review) | `docs/SPRINT-PLAN-V2.md` | 8 sprints, 25 days. Architecture Agent → Product + Security critics → synthesis. 78 features audited, 39 security findings. | ✅ DOC |

## Session 57 (2026-03-28) — TEAM EXPANSION SPRINT

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| `sales-deal-strategist.md` | `memory/swarm/skills/` | B2B deal architecture, MEDDPICC for Volaura, org pricing tiers, red flags | ✅ LIVE |
| `sales-discovery-coach.md` | `memory/swarm/skills/` | B2B discovery flows, org onboarding questions, Gap Selling for Volaura | ✅ LIVE |
| `linkedin-content-creator.md` | `memory/swarm/skills/` | AURA score portability, LinkedIn share templates for Kamal/Rauf personas | ✅ LIVE |
| `cultural-intelligence-strategist.md` | `memory/swarm/skills/` | AZ/CIS cultural audit, invisible exclusion patterns, AZ text/naming rules | ✅ LIVE |
| `accessibility-auditor.md` | `memory/swarm/skills/` | WCAG 2.2 AA, radar chart fix, Volaura component risk map, AZ a11y | ✅ LIVE (activates Sprint 6) |
| `behavioral-nudge-engine.md` | `memory/swarm/skills/` | ADHD-first validation, cognitive load budgeting, notification cadence | ✅ LIVE (DSP skill) |
| 3 new DSP personas | `CLAUDE.md` | Kamal (senior professional), Aynur (talent acquisition), Rauf (mid-career) added to council | ✅ LIVE |
| Sprint Plan V2 updated | `docs/SPRINT-PLAN-V2.md` | Sprint 1 +3 tasks: org/volunteer branch, post-confirm display_name, professional empty state | ✅ LIVE |
| Skills Matrix updated | `CLAUDE.md` | 9 new routing rows for B2B, cultural, accessibility, nudge, LinkedIn skills | ✅ LIVE |

**How new agents were hired:** Full repo (164 agent files) given to Kamal + Aynur + Rauf personas. Their nominations + existing 6-agent votes synthesized. Reality Checker rejected (duplicates Attacker). 6 agents hired.

| `SPRINT-PLAN-V3.md` | `docs/` | Sprint Plan after 2-round recursive criticism (9 personas, 18→38/50). Swaps Sprint 3↔4, IP rate limits, CSRF, org RLS, volunteer opt-in, Telegram sanitization moved to Sprint 2. | ✅ DOC |
| `RECURSIVE-CRITICISM.md` | `docs/engineering/skills/` | Standard protocol for recursive plan criticism. 2 rounds minimum for sprint plans. | ✅ DOC |

---

## HOW TO UPDATE THIS FILE

After any session that adds/changes code:
```
| {file/feature} | {location} | {what it does} | ✅ LIVE | {how to test} |
```
Add to the correct session section. Never delete old entries — archive to SHIPPED-ARCHIVE.md when file exceeds 200 lines.
