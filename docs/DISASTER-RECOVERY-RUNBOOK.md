# Disaster Recovery Runbook — VOLAURA

**Last updated:** 2026-03-29
**Owner:** CTO (Yusif)
**Target:** Single Railway instance + Supabase
**RTO target:** 15 minutes | **RPO target:** 0 (Supabase is source of truth)

---

## Quick Reference

| Symptom | Most likely cause | Jump to |
|---------|-----------------|---------|
| API returning 502/503 | Railway instance crashed | [Section 1](#1-api-down--502503) |
| API returning 504 | LLM timeout or DB timeout | [Section 2](#2-api-timeout--504) |
| Users can't log in | Supabase Auth down | [Section 3](#3-auth-down) |
| DB queries failing | Supabase DB down or connection pool | [Section 4](#4-database-down) |
| Assessment scores wrong | LLM fallback activated | [Section 5](#5-llm-degraded) |
| Sentry flooded with errors | Bug in recent deploy | [Section 6](#6-bad-deploy--rollback) |
| Telegram alert fires | 5xx rate spike | [Section 7](#7-telegram-alert-fires) |

---

## Monitoring Checklist (first 30 seconds)

```
1. Railway Dashboard   → https://railway.app/dashboard
   Look for: instance status, recent restarts, memory usage

2. Sentry              → https://sentry.io/organizations/volaura/
   Look for: error spikes, new issues in last 5 min

3. Supabase Dashboard  → https://supabase.com/dashboard/project/[project-id]
   Look for: DB status, API health, auth service status

4. Health endpoint     → GET https://volaura-api.up.railway.app/health
   Expected: {"status":"ok","database":"connected","llm_configured":true}
```

---

## 1. API Down — 502/503

**Symptoms:** Railway down indicator, Telegram alert fired, health check unreachable.

```
Step 1: Railway Dashboard → Project → Deployments
  → Check if instance is running
  → Check logs for crash reason (OOM, startup error, etc.)

Step 2: If crashed with OOM (memory exceeded 2GB):
  → Railway Dashboard → Settings → Resources → bump to 4GB RAM ($8/mo)
  → Redeploy

Step 3: If crashed with startup error:
  → Railway logs → copy error → fix in code → push to main → Railway auto-deploys

Step 4: If no obvious reason (Railway infra issue):
  → Wait 2 min, Railway auto-restarts
  → If still down: Railway Status Page → https://status.railway.app

Step 5: Manual redeploy:
  → Railway Dashboard → Deployments → [latest deploy] → Redeploy
```

**Estimated resolution: 5-10 minutes**

---

## 2. API Timeout — 504

**Symptoms:** Requests return after 30s with 504, assessment answers fail, `isSlowFetch` fires.

### 2a. LLM timeout (most common)

```
Cause: Gemini / Groq API slow or rate-limited

Step 1: Check /health → if llm_configured=true but DB=connected, LLM is the issue

Step 2: Check Gemini quota:
  → https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com
  → Quotas → "Requests per minute" — if at limit, wait or upgrade

Step 3: Check Groq fallback is configured:
  → Railway env vars → GROQ_API_KEY must be set
  → If missing: add GROQ_API_KEY from https://console.groq.com/keys

Step 4: keyword_fallback activates automatically if both LLMs fail
  Assessment still works, scores slightly less accurate (±5% per architecture audit)
  Acceptable for < 1 hour outage
```

### 2b. Database timeout

```
Cause: Supabase connection limit, slow query, or RLS policy timeout

Step 1: Supabase Dashboard → Database → Performance Advisor
  → Check for slow queries (> 1000ms)

Step 2: Supabase Dashboard → Project → Settings → Database
  → Connection pooling: ensure mode = Transaction (not Session) for Railway

Step 3: If character_events GIN index not applied:
  → Run: supabase db push (applies migration 20260329060000_character_events_gin_index.sql)
  → This resolves JSONB scan timeouts under 1000+ users
```

**Estimated resolution: 5-30 minutes**

---

## 3. Auth Down

**Symptoms:** Login returns error, signup fails, "Your session has ended" appears for all users.

```
Step 1: Test Supabase Auth directly:
  → Supabase Dashboard → Authentication → Users → "Send magic link" test
  → If that fails: Supabase Auth service is down (not our code)

Step 2: Check Supabase status: https://status.supabase.com
  → If incident in progress: wait, nothing to do

Step 3: If Auth works in Dashboard but not in app:
  → Check SUPABASE_URL + SUPABASE_ANON_KEY in Railway env vars
  → Ensure NEXT_PUBLIC_SUPABASE_URL is set in Vercel env vars (frontend)

Step 4: Emergency — users lose session JWT:
  → Users will see "Your session has ended" with 3s countdown to login
  → This is expected behavior (BLOCKER-5 fixed)
  → No data loss — all tasks/sessions are in Supabase
```

**User impact:** Cannot log in. Existing sessions work until JWT expires (1hr).

---

## 4. Database Down

**Symptoms:** /health returns `"database":"error: ..."`, all API calls fail.

```
Step 1: Supabase Dashboard → Project → Overview
  → Check DB status indicator

Step 2: Check Supabase status: https://status.supabase.com
  → Region: closest to Railway region (us-east-1 / eu-west-1)

Step 3: If Supabase is up but DB returns errors:
  → Supabase Dashboard → Database → Logs → look for connection errors
  → Check connection count: Settings → Database → "Current connections"
  → If at max (default 50 for free tier, 200 for Pro):
    → Railway → scale down to 1 instance (single instance = ~20 connections)
    → OR: Supabase Dashboard → Database → Connection Pooling → enable PgBouncer

Step 4: Data integrity check (after outage):
  → No action needed — Supabase is PostgreSQL with WAL
  → All committed transactions are durable
  → In-flight assessment sessions may show partial state (users can restart assessment)
```

**Data loss risk: Zero** (PostgreSQL ACID guarantees)

---

## 5. LLM Degraded

**Symptoms:** Assessment scoring returns `keyword_fallback=true`, scores slightly off.

```
The system has 3-tier fallback built in:
  Tier 1: Gemini 2.0 Flash (primary)
  Tier 2: Groq (fallback if Gemini fails or rate-limited)
  Tier 3: keyword_fallback (local scoring, ±5% accuracy, no API calls)

No action required for < 4 hour outage.

For extended LLM outage (> 4 hours):
Step 1: Check Gemini API status: https://cloud.google.com/status
Step 2: Check Groq status: https://status.groq.com
Step 3: If both down:
  → keyword_fallback is active automatically
  → Assessment still works, scores still stored
  → Inform users via Telegram channel / app banner (optional)
  → When LLMs recover: no re-scoring needed (scores are stored as-is)
```

---

## 6. Bad Deploy — Rollback

**Symptoms:** Sentry shows new error type not seen before deploy, Telegram alerts firing.

```
Step 1: Confirm the deploy caused it:
  → Sentry → Issues → filter "Last seen: last 1 hour" → new issues correlate with deploy time?

Step 2: Railway rollback:
  → Railway Dashboard → Deployments → [previous successful deploy] → Redeploy
  → Takes ~2 minutes to switch

Step 3: Hotfix if rollback not possible:
  → git log --oneline -5    (find last good commit)
  → git revert HEAD         (if last commit is bad)
  → git push origin main    (Railway auto-deploys)

Step 4: After rollback:
  → Fix root cause in a branch
  → Test locally: uvicorn app.main:app --reload
  → Push to main when confirmed fixed

Step 5: Clear Sentry:
  → Sentry → Issues → Resolve all issues from bad deploy
  → Add comment: "Rolled back — deploying fix"
```

---

## 7. Telegram Alert Fires

**Symptoms:** CEO receives Telegram message: "🚨 VOLAURA API: N × 5xx errors in last 5 minutes"

```
ErrorAlertingMiddleware sends this when 5xx rate > threshold (1 alert per 5 min max).

Step 1: Don't panic — rate-limited alerts mean burst, not sustained
Step 2: Open Sentry immediately — error should already be there
Step 3: GET /health → check which component is degraded
Step 4: Follow relevant section above (1-6)
Step 5: After resolving: send brief Telegram reply "Resolved — [1 sentence]"

What it's NOT: a false positive is almost impossible (middleware tracks real 5xx)
What it IS: likely real traffic hitting a real bug
```

---

## Environment Variables (Quick Reference)

All set on Railway. If a key is missing, check with:
```bash
# In Railway CLI:
railway variables list
```

| Variable | Purpose | Where to get |
|----------|---------|-------------|
| `SUPABASE_URL` | DB + Auth | Supabase Dashboard → Settings → API |
| `SUPABASE_ANON_KEY` | Public API key | Supabase Dashboard → Settings → API |
| `SUPABASE_SERVICE_KEY` | Admin operations | Supabase Dashboard → Settings → API |
| `GEMINI_API_KEY` | LLM scoring (primary) | console.cloud.google.com |
| `GROQ_API_KEY` | LLM scoring (fallback) | console.groq.com/keys |
| `SENTRY_DSN` | Error tracking | sentry.io → volaura project |
| `TELEGRAM_BOT_TOKEN` | CEO alerts | @BotFather on Telegram |
| `TELEGRAM_CHAT_ID` | CEO chat ID | Telegram → send /start to bot |

---

## Post-Incident Checklist

After resolving any incident:

```
□ Confirm /health returns {"status":"ok","database":"connected"}
□ Test a signup + assessment flow manually (5 min smoke test)
□ Check Sentry — no new errors in last 10 min
□ Document in docs/SESSION-FINDINGS.md:
    - What happened
    - Root cause
    - How we fixed it
    - What we'll do to prevent recurrence
□ Update LAUNCH-BLOCKERS.md if a new blocker was discovered
```

---

## When to Page the CEO

| Situation | Do this |
|-----------|---------|
| API down > 5 min | Telegram message: what's down, what you're doing |
| Data loss suspected | Call immediately |
| Auth down > 15 min during active hours | Telegram message |
| Security breach suspected | Call + take API offline |
| Everything resolved < 5 min | No message needed |
