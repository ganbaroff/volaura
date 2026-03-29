# Launch Blockers — Production Readiness Checklist

**Date:** 2026-03-29 | **Status:** NOT READY FOR 7000 USERS
**Overall readiness:** ~35%

---

## Must Fix Before ANY Users (Blockers 1-10)

| # | Blocker | Status | Requires | Time |
|---|---------|--------|----------|------|
| 1 | **Sentry DSN** — zero error visibility | ❌ NEEDS CEO | Railway env var `SENTRY_DSN` | 2h |
| 2 | **Groq API key** — LLM fallback chain broken | ❌ NEEDS CEO | Railway env var `GROQ_API_KEY` | 1h |
| 3 | ~~Connection pool~~ — httpx unlimited by default | ✅ FALSE POSITIVE | Verified: httpx.Limits() = None/None | N/A |
| 4 | **Assessment localStorage** — refresh loses progress | ✅ FIXED | sessionStorage → localStorage | Done |
| 5 | **Session expiry warning** — silent redirect | ✅ FIXED | Show message before redirect | Done |
| 6 | ~~Password reset~~ — FULLY BUILT (not a stub) | ✅ FALSE POSITIVE | forgot-password + reset-password pages complete | N/A |
| 7 | **Health check** — stub, doesn't check DB | ✅ FIXED | Now checks Supabase + LLM config | Done |
| 8 | **Rate limit restart risk** — in-memory resets | ❌ DOCUMENT | Document risk, plan Redis for v2 | 30min |
| 9 | **Alerting** — nobody knows when API crashes | ❌ TODO | Telegram bot alert on 5xx | 2h |
| 10 | **Results i18n** — competency names | ✅ FALSE POSITIVE | Already uses t() with fallback | N/A |

### CEO Actions Required:
1. Create Sentry project → give DSN → we set on Railway
2. Confirm GROQ_API_KEY is on Railway (or provide new one)
3. Verify OpenAI API key on Railway as tertiary fallback

---

## Must Fix Before 100+ Users

| # | Issue | Status | Time |
|---|-------|--------|------|
| 11 | Load test 100 concurrent users | ❌ | 4h |
| 12 | Mobile responsive fixes (375px) | ❌ | 2h |
| 13 | Signup button loading spinner | ❌ | 30min |
| 14 | Assessment retry button on error | ❌ | 30min |
| 15 | Network timeout messaging ("Still loading...") | ❌ | 1h |

---

## Must Fix Before 1000+ Users

| # | Issue | Status | Time |
|---|-------|--------|------|
| 16 | Redis rate limiter (replace in-memory) | ❌ | 4h |
| 17 | GIN index on character_events.payload | ❌ | 30min |
| 18 | Assessment question pool expansion (11/competency → 20+) | ❌ | CEO content |
| 19 | Disaster recovery runbook | ❌ | 2h |

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
