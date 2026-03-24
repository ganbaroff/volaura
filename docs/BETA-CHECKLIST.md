# Beta Launch Checklist — Yusif Actions Required

> Run these BEFORE inviting the first 10 beta testers.
> Each action is under 5 minutes. All are in dashboards, no code.

---

## 1. Railway — Set Production Environment Variables

Go to Railway → volaura-api project → Variables

Set these (if not already set):

| Variable | Value |
|----------|-------|
| `APP_ENV` | `production` |
| `APP_URL` | `https://volaura.app` |
| `GEMINI_API_KEY` | (already set — verify it's there) |
| `SUPABASE_URL` | (already set — verify) |
| `SUPABASE_SERVICE_KEY` | (already set — verify) |

**Why `APP_ENV=production` matters:** Without it, the API defaults to development mode and only allows `localhost:3000` in CORS. Every user on `volaura.app` gets a silent network error.

After saving → Railway will redeploy automatically. Wait ~2 min then test:
```
curl https://modest-happiness-production.up.railway.app/health
```
Should return `{"status":"ok","version":"0.1.0"}`.

---

## 2. Supabase — Disable Email Confirmation

Go to Supabase → Authentication → Settings → Email Auth

Toggle OFF: **"Enable email confirmations"**

**Why:** With confirmation on, every new user gets stuck on "check your email" and can't log in. Zero beta testers will get through registration.

After disabling — test registration on volaura.app with a real email.

---

## 3. Supabase — Apply Pending Migrations

In your terminal from the project root:

```bash
supabase db push
```

This applies 4 pending migrations:
- `20260324000014_hnsw_index.sql` — vector search index (HNSW, works at 0 rows)
- `20260324000015_rls_audit_fixes.sql` — RLS security fixes
- `20260324000016_assessment_assignment_columns.sql` — assessment session columns
- `20260324000017_seed_all_competency_questions.sql` — **70 questions across 7 competencies**

**Why:** Without migration 17, only the `communication` competency has questions. All other assessments return "no questions available".

After pushing — test via the API:
```
GET https://modest-happiness-production.up.railway.app/api/assessment/start
```
Should return a first question, not a 422 error.

---

## 4. Supabase — Configure Password Reset Redirect URL

Go to Supabase → Authentication → URL Configuration

Add to "Redirect URLs":
```
https://volaura.app/en/reset-password
https://volaura.app/az/reset-password
```

**Why:** When users click "Forgot password?", Supabase sends them a magic link. The link redirects to your reset-password page. Without these in the allowlist, Supabase blocks the redirect.

---

## 5. Verify End-to-End (5 minutes)

After completing 1-4:

1. Go to `https://volaura.app`
2. Register with your real email
3. Log in immediately (no email confirmation step)
4. Go to Assessment → pick "Communication"
5. Answer 5-10 questions
6. See your AURA score

If all 5 work → platform is beta-ready. Invite the first tester.

---

## Status Tracker

| Action | Status | Done by |
|--------|--------|---------|
| Railway `APP_ENV=production` | ⬜ Pending | Yusif |
| Railway `APP_URL=https://volaura.app` | ⬜ Pending | Yusif |
| Supabase email confirmation OFF | ⬜ Pending | Yusif |
| `supabase db push` | ⬜ Pending | Yusif |
| Supabase redirect URL added | ⬜ Pending | Yusif |
| End-to-end test passed | ⬜ Pending | Yusif |
