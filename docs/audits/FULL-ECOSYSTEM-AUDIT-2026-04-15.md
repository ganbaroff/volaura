# VOLAURA Ecosystem Audit — Full Reality Report
**Date:** 2026-04-15 | **Auditor:** Atlas (Claude Opus 4.6, local)
**Method:** 4 parallel audit agents + direct prod probes + Supabase SQL + Sentry MCP
**Scope:** All 5 products, infrastructure, security, data, user journey

---

## EXECUTIVE SUMMARY

VOLAURA is a technically sophisticated pre-beta product with no real users. The codebase is surprisingly solid (119 endpoints, 95 production-ready, 749 tests passing), but the ecosystem around it is largely theater. Three of five products have zero cross-product integration. The database has 39 test users and 13 completed assessments. There are 2 critical security findings that must be fixed before any public launch.

**One-line verdict:** Good engine, no passengers.

---

## SECTION 1: HARD NUMBERS (Supabase prod, verified via SQL)

| Metric | Count | Verdict |
|--------|-------|---------|
| Auth users | 39 | All test accounts |
| Profiles | 27 | 12 users never completed profile |
| Organizations | 2 | Both test orgs |
| Assessment sessions | 20 | |
| Completed sessions | 13 | 65% completion rate (small sample) |
| AURA scores | 8 | 5 leaked (recovery script ready) |
| Questions in DB | 101 | 15 are placeholders |
| Competencies | 8 | All 8 with correct weights |
| Ecosystem events | 10 | Wired in session 97, minimal data |
| Real paying customers | 0 | |
| Real external users | 0 | |

---

## SECTION 2: VOLAURA (Core Product)

### Backend — 7.5/10
- **119 endpoints**, 95 production-ready, 20 works-with-issues, 4 stubs
- IRT/CAT assessment engine: research-grade 3PL + EAP, energy adaptation, anti-gaming
- LLM service: 4-tier fallback (Vertex → Gemini → Groq → OpenAI)
- Stripe subscription: fully wired with webhook + idempotency
- Open Badges 3.0: W3C-compliant credential endpoint

**Issues found:**
- `atlas_gateway.py` writes to filesystem — fails silently on Railway (read-only)
- `video_generation_worker.py` — stub, no backend connected
- `activity.py` queries wrong table name (`registrations` vs `event_registrations`)
- `telegram_webhook.py` — 800+ lines, needs decomposition
- `reeval_worker.py` — depends on cron trigger, no evidence it runs

### Frontend — 8/10
- **46 pages**, 36 real + wired, 3 intentional placeholders (atlas/life/mindshift)
- Assessment flow: 5 pages, fully wired (start → questions → complete → results + coaching)
- Auth: Supabase signIn, social buttons, forgot/reset, open-redirect protection
- Landing: 6 sections, i18n, OG metadata, skip-to-content
- Dashboard: AURA widget, stats, activity feed, crystal balance, tribe card
- BrandedBy pages: full CRUD for AI Twin

**Issues found:**
- ~10 hardcoded `aria-label="Loading"` (should be i18n)
- 3 placeholder pages have hardcoded English
- 15 placeholder questions still in seed.sql

### Database — 8/10
- **39 tables** across 75 migrations
- RLS enabled on all tables
- Schema well-designed: competencies, sessions, scores, events, tribes, crystals
- Character_events table exists with GIN index

**Issues found:**
- 15 placeholder questions with `needs_review=true`
- `org_volunteer_records` table referenced but never created (migration fixed session 97)

---

## SECTION 3: PRODUCTION INFRASTRUCTURE

### What works:
- `volaura.app` → HTTP 200, full HTML renders (114KB)
- Vercel → Railway rewrite: confirmed working (/api/auth/me returns 401 from Railway)
- Railway backend: /health 200, DB connected, LLM configured
- CI: green (ruff + tsc pass)
- Sentry: configured, 81 historical issues, 0 new in 9 days

### What doesn't:
- Leaderboard publicly shows test data ("Atlas E2E Test" rank 1, "Anonymous" users)
- No custom error pages on Vercel
- No CDN/caching layer
- No monitoring alerts (Sentry alerts not configured)
- In-memory rate limiter resets on every Railway deploy

---

## SECTION 4: SECURITY (P0-P3)

### P0 — CRITICAL (fix before any public access)
1. **Hardcoded Supabase anon key** in `apps/api/app/config.py` lines 20-25. Full JWT committed to git as fallback default.
2. **`/health/anon-key-check`** endpoint leaks key prefix (20 chars), key length, JWT format, Supabase URL — unauthenticated. Full reconnaissance endpoint.

### P1 — HIGH (fix before beta)
3. **Org creation unverified.** Any auth'd user → `POST /api/organizations` → instant org owner → search talent, send invites. No domain verification, no approval.
4. **`python-jose` unmaintained.** Last release 2022, CVE-2024-33663 (ECDSA key confusion). Replace with PyJWT or joserfc.

### P2 — MEDIUM
5. **CORS includes Railway backend URL** as allowed origin. Backend should never be its own origin.
6. **Rate limiter in-memory.** Resets on every deploy. Brute-force timing attack possible.

### P3 — LOW (acceptable for now)
7. Secrets management clean (.env, gcp-service-account.json gitignored)
8. RLS on all 38+ tables
9. Dependencies mostly current (Next.js 14.2, FastAPI 0.115+)

---

## SECTION 5: ECOSYSTEM — THE HARD TRUTH

### Product Integration Reality

| Product | Repo exists | Deploys | VOLAURA integration | Real readiness |
|---------|------------|---------|---------------------|---------------|
| VOLAURA | ✅ | ✅ volaura.app + Railway | N/A (is core) | 55% |
| Life Simulator | ✅ 431 GDScript files | ❌ no published build | 52 VOLAURA refs, auth wired | 40% (129 uncommitted files) |
| BrandedBy | ✅ 6,448 files | ❓ unknown | **0 VOLAURA refs** | 35% (last commit "123" + revert) |
| MindShift | ✅ but git broken | ❓ unknown | **0 VOLAURA refs** | 15% (git: "current branch broken") |
| Atlas/Swarm | Inside VOLAURA | ✅ via GitHub Actions | N/A (is infra) | 60% |

### What "5-product ecosystem" actually means today:
- VOLAURA backend + frontend: **REAL, working**
- Life Simulator: **code exists, not shipped, 129 uncommitted changes**
- BrandedBy: **standalone, zero connection to VOLAURA**
- MindShift: **git corrupted, status unknown**
- Atlas swarm: **13 agents, runs on cron, produces proposals but no one acts on them**

### Swarm reality:
- 81 Python files, ~30% archived
- autonomous_run.py and atlas_content_run.py exist
- Daily cron configured (.github/workflows/swarm-daily.yml)
- 154 proposals generated, all decided, 0 pending
- **Actual value produced:** proposals sit in JSON, minimal direct code impact

### Telegram bot:
- Webhook handler: 800+ lines, functional
- Self-learning: atlas_learnings table exists, Groq extraction coded
- Identity: hardcoded (Railway has no git filesystem)
- **Actual usage:** minimal, bot is deployed but rarely messaged

---

## SECTION 6: THE GAP — CODE vs REALITY

| What we say | What's true |
|-------------|------------|
| "5-product ecosystem" | 1 product works. 1 has code. 3 are disconnected or broken. |
| "AURA score system" | Works technically. 8 scores in DB. 0 real users have one. |
| "749 tests passing" | True. But tests mock Supabase — they verify logic, not integration. |
| "Sentry monitoring" | 81 historical issues. No alerts configured. We found 0 issues because we searched wrong timeframe. |
| "13 AI agents" | Python scripts that run on cron. Output goes to JSON file. Not agentic in any meaningful sense. |
| "Crystal economy" | 10 events in character_events. No user has ever earned or spent a crystal. |
| "Ecosystem events bus" | 3 emitters coded (session 97). character_events table has 10 rows. No consumer exists. |
| "B2B org dashboard" | Code exists. 2 test orgs. Any user can create an org with no verification. |
| "CI green" | True as of today. Was broken for 2 days before we fixed it. |

---

## SECTION 7: PLAN — WHAT TO FIX AND IN WHAT ORDER

### Phase 0: SECURITY (do before anything else, ~2 hours)
1. Remove hardcoded anon key from config.py — env var only, crash if missing
2. Delete /health/anon-key-check endpoint
3. Replace python-jose with PyJWT
4. Add org creation approval gate (admin must approve)
5. Remove Railway URL from CORS origins

### Phase 1: FIRST REAL USER (days 1-7)
6. Clean leaderboard of test data (or hide leaderboard until 10+ users)
7. Apply Phase 1 migration (professional_id columns)
8. Run AURA recovery script (5 orphan sessions)
9. Remove 15 placeholder questions from seed
10. Fix activity.py table name mismatch
11. Configure Sentry email alerts for 5xx errors
12. Walk the user journey personally: signup → profile → assessment → results → public profile

### Phase 2: SHIP TO 10 FRIENDS (days 8-14)
13. Set up custom domain volaura.app analytics (PostHog or Vercel Analytics)
14. Add real onboarding flow (welcome page → first assessment CTA)
15. Write 20 more real assessment questions (reach 120 total, remove placeholders)
16. Commit Life Simulator 129 files and publish Godot build
17. Fix MindShift git (likely: delete local, re-clone from remote)

### Phase 3: HONEST ECOSYSTEM (days 15-30)
18. BrandedBy: either connect to VOLAURA (character_events consumer) or stop calling it part of the ecosystem
19. MindShift: either connect or remove from marketing
20. Add at least one character_events consumer (Life Simulator stat boost on assessment_completed)
21. Replace in-memory rate limiter with Redis/Supabase-backed
22. Decompose telegram_webhook.py (800 lines → router + service + handler)

### Phase 4: REAL USERS (days 30-60)
23. Invite 10 real professionals to take assessments
24. Invite 1 real organization to search talent
25. Measure: signup → assessment completion rate, time-to-first-AURA
26. Fix what breaks when real humans touch the product

---

## METHODOLOGY

This audit was performed by:
- 4 parallel code analysis agents (backend, frontend+DB, security, ecosystem)
- Direct curl probes to volaura.app and Railway endpoints
- Supabase SQL queries against production database
- Sentry MCP API (81 issues found)
- Git status and log on all accessible repos
- Railway CLI for env var comparison

Every claim is backed by a tool call. No assumptions, no "should work."
