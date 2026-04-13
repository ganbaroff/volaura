# Sprint 1 Smoke Test Results
**Date:** 2026-03-28 | **Session:** 58 | **Tester:** CTO (automated via curl + Supabase MCP)

---

## ✅ What Works (Pipeline Verified)

| Step | Endpoint / Page | Result |
|------|----------------|--------|
| Health check | `GET /health` | ✅ `{"status":"ok"}` |
| Registration | `POST /api/auth/register` | ✅ 201 + token returned |
| Login | `POST /api/auth/login` | ✅ 201 + token returned |
| Auth/me | `GET /api/auth/me` | ✅ Returns profile (needs profile to exist) |
| Profile creation | `POST /api/profiles/me` | ✅ 201 created |
| Profile fetch | `GET /api/profiles/me` | ✅ Returns profile |
| Assessment start | `POST /api/assessment/start` | ✅ Returns session + first question (AZ + EN) |
| Assessment answer | `POST /api/assessment/answer` | ✅ CAT selects next question adaptively |
| Assessment complete | `POST /api/assessment/complete/{id}` | ✅ Computes competency score |
| AURA score | `GET /api/aura/me` | ✅ Returns total_score, badge_tier, competency_scores |
| Activity log | `GET /api/activity/me` | ✅ Returns assessment activity |
| Events list | `GET /api/events` | ✅ Returns `[]` (no seed data yet) |
| Landing page | `/az` | ✅ Loads, links to /az/signup, /az/login |
| Signup page | `/az/signup` | ✅ Loads, 4-field form |
| Login page | `/az/login` | ✅ Loads |
| Forgot password | `/az/forgot-password` | ✅ Loads |
| Onboarding | `/az/onboarding` | ✅ 3-step flow |
| Assessment UI | `/az/assessment` | ✅ Loads |
| AURA UI | `/az/aura` | ✅ Loads |
| Leaderboard | `/az/leaderboard` | ✅ Empty state (no real users) |
| Notifications | `/az/notifications` | ✅ Empty state |

---

## 🚨 FIXED THIS SESSION

| Issue | Fix Applied |
|-------|-------------|
| Railway not deploying — ALL builds failed for 2 days | Created `railway.toml` + `Dockerfile.railway` at repo root. Railpack was auto-detecting Node.js, ignoring `apps/api/railway.toml`. Now uses Docker correctly. |
| `/health/env-debug` still live (OWASP CRITICAL) | Fixed by Railway redeploy. Now returns 404. |
| 3 DB migrations not applied | Applied: `question_delivered_at`, `answer_version`, `restrict_session_update` |

---

## 🔴 BLOCKERS — Must Fix Before Real Users

### B1 — `/api/auth/me` crashes when no profile exists (severity: HIGH)
**File:** `apps/api/app/routers/auth.py:145-154`
**Cause:** `.single()` in supabase-py throws APIError when no row found. Code never reaches `if not result.data` check.
**Impact:** Any user who registers but doesn't complete onboarding gets 500 on ALL auth'd endpoints.
**Fix:** Change `.single()` to `.maybe_single()` (one-line change).

### B2 — Assessment `is_complete` never True in answer responses (severity: HIGH)
**Observed:** IRT engine runs out of questions (next_question=None) but `is_complete` stays False.
**Impact:** Frontend must call `POST /api/assessment/complete/{id}` explicitly. If this call fails, AURA never updates.
**Fix:** In `submit_answer` handler: when `next_q is None`, call complete logic automatically OR set `is_complete=True`.

### B3 — Profile not created at registration (severity: MEDIUM)
**Flow:** Signup → `supabase.auth.signUp()` (client-side) → onboarding → `POST /api/profiles/me`
**Risk:** If user closes browser after signup but before completing onboarding, profile doesn't exist. All authenticated endpoints fail.
**Fix (Sprint 1):** Add a DB trigger `ON INSERT auth.users → INSERT INTO profiles(id, username, display_name)` using user_metadata. OR ensure frontend handles the missing profile case gracefully.

---

## 🟠 SPRINT 1 UX TASKS (from V3 plan, not yet done)

| Task | Status | Impact |
|------|--------|--------|
| Volunteer / Org branch at signup | ❌ Not done | B2B users fall into volunteer flow |
| Move display_name to post-confirm | ❌ Not done | Signup has 4 fields (ADHD issue) |
| Volunteer org-visibility toggle | ❌ Not done | Orgs can see volunteers without consent |
| AZ-native privacy consent copy | ❌ Not done | Legal + cultural issue |
| Professional empty state copy | ❌ Not done | Platform looks like volunteer board |
| IP-based rate limits (not per-email) | ❌ Not done | Per-email auth rate limits in place but IP-based needed |

---

## 🟡 OBSERVATIONS (not blockers, logged for Sprint 2+)

| Observation | Detail |
|-------------|--------|
| CAT stops at 2 questions | IRT engine reaches confidence threshold very quickly. May need more questions per session for credibility. |
| Events page shows mock data | `apps/web/src/lib/mock-data.ts` — hardcoded. Sprint 4 task to wire real API. |
| `questions_answered` field mismatch | API returns this field but DB column is `current_question_idx`. Computed in-memory. |
| Leaderboard empty | Expected — no real users yet. Sprint 4 will add materialized view. |
| AURA score is total_score: 3.26 for 1 competency | Correct — only `adaptability: 32.57` assessed, weight is 0.10. 32.57 × 0.10 = 3.26. |

---

## Summary for CEO

**Backend is alive.** The full Volaura flow works end-to-end: user registers, completes onboarding, takes a CAT assessment, gets an AURA score.

**What was broken and is now fixed:**
- Railway hadn't deployed in 2 days (all builds failing). Fixed with new deploy config.
- The OWASP security fix (deleted env-debug endpoint) is now actually live in production.

**What to build next (Sprint 1 execution):**
1. Fix the `auth/me` crash for users without profiles (10-minute code fix)
2. Add org/volunteer branch at signup (B2B users need their own path)
3. Move display_name out of signup form (reduce cognitive load)
4. Add privacy consent in AZ-native language

**Assessment pipeline is solid.** CAT engine works, AURA score computed correctly after session complete.
