# Launch Blockers — Production Readiness Checklist

**Date:** 2026-03-29 | **Status:** NOT READY FOR 7000 USERS
**Overall readiness:** ~35%

---

## Must Fix Before ANY Users (Blockers 1-10)

| # | Blocker | Status | Requires | Time |
|---|---------|--------|----------|------|
| 1 | **Sentry DSN** — zero error visibility | ✅ RESOLVED (Session 69) | Sentry org: volaura, project: volaura-api, DSN on Railway | Done |
| 2 | **Groq API key** — LLM fallback chain broken | ✅ RESOLVED (Session 69) | All 27 env vars on Railway including GROQ_API_KEY | Done |
| 3 | ~~Connection pool~~ — httpx unlimited by default | ✅ FALSE POSITIVE | Verified: httpx.Limits() = None/None | N/A |
| 4 | **Assessment localStorage** — refresh loses progress | ✅ FIXED | sessionStorage → localStorage | Done |
| 5 | **Session expiry warning** — silent redirect | ✅ FIXED | Show message before redirect | Done |
| 6 | ~~Password reset~~ — FULLY BUILT (not a stub) | ✅ FALSE POSITIVE | forgot-password + reset-password pages complete | N/A |
| 7 | **Health check** — stub, doesn't check DB | ✅ FIXED | Now checks Supabase + LLM config | Done |
| 8 | **Rate limit restart risk** — in-memory resets | ✅ RESOLVED (Session 70) | Documented in rate_limit.py lines 8-10. Redis planned for 2+ instances. | Done |
| 9 | **Alerting** — nobody knows when API crashes | ✅ RESOLVED (Session 69) | ErrorAlertingMiddleware: 5xx → CEO Telegram (rate-limited 1/5min) | Done |
| 10 | **Results i18n** — competency names | ✅ FALSE POSITIVE | Already uses t() with fallback | N/A |

### CEO Actions Required:
1. Create Sentry project → give DSN → we set on Railway
2. Confirm GROQ_API_KEY is on Railway (or provide new one)
3. Verify OpenAI API key on Railway as tertiary fallback

---

## Must Fix Before 100+ Users

| # | Issue | Status | Time |
|---|-------|--------|------|
| 11 | Load test 100 concurrent users | 🔧 SCRIPT READY (Session 74) | `scripts/load_test.js` — k6 script ready. CEO runs: `k6 run scripts/load_test.js`. Needs: `npm install -g k6` + set `VOLAURA_TEST_JWT` env var for assessment flow. | CEO action |
| 12 | Mobile responsive fixes (375px) | ✅ FIXED (Session 74) | Dashboard skeleton grid-cols-1 sm:grid-cols-3, volunteer row hides competency col on mobile, filter buttons flex-wrap | Done |
| 13 | Signup button loading spinner | ✅ FIXED (Session 70) | Loader2 icon added | Done |
| 14 | Assessment retry button on error | ✅ FIXED (Session 74) | nextCompetency() deferred to after successful fetch; transition screen shows error alert + loading state on Continue button | Done |
| 15 | Network timeout messaging ("Still loading...") | ✅ FIXED (Session 70) | isSlowFetch state + 4s timer | Done |

---

## Must Fix Before 1000+ Users

| # | Issue | Status | Time |
|---|-------|--------|------|
| 16 | Redis rate limiter (replace in-memory) | ❌ | 4h |
| 17 | GIN index on character_events.payload | ✅ MIGRATION READY (Session 70) | 20260329060000_character_events_gin_index.sql — apply via supabase db push | Done |
| 18 | Assessment question pool expansion (11/competency → 20+) | ❌ | CEO content |
| 19 | Disaster recovery runbook | ✅ WRITTEN (Session 74) | `docs/DISASTER-RECOVERY-RUNBOOK.md` — covers API down, 504, auth, DB, LLM degraded, bad deploy, Telegram alert. Env var table + post-incident checklist. | Done |

---

## Capacity Math at 7000 Users

```
GEMINI: 15 RPM free tier
  7000 users × 8 questions × 20% open-ended = 11,200 LLM calls
  Over 8 hours = 23 RPM ← EXCEEDS 15 RPM LIMIT

  With Groq fallback (30 RPM + 14,400/day):
  23 RPM total ÷ 2 providers = 11.5 RPM each ← OK if both configured

  Without Groq: keyword_fallback for 35% of answers = inflated scores

DB CONNECTIONS:
  httpx default: 20 concurrent connections
  Peak: 100+ concurrent users in assessment = 504 errors

MEMORY:
  Base: ~200MB (uvicorn + deps)
  Per session: ~20KB × 7000 = 140MB
  Total: ~400MB ← fits 2GB Railway, but cascade risk
```

---

## Launch Sequence (recommended)

```
Week 1: Fix blockers 1-10 (code + CEO env vars)
Week 2: Load test + fix what breaks (11-15)
Week 3: Beta 50 users → monitor → fix
Week 4: Expand to 500 → monitor 1 week
Week 5: 7000 users (with all monitoring in place)
```
