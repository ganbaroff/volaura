# Critical Bugs — VOLAURA (verified 2026-04-18 13:50 Baku)

All items verified via SQL, Grep, Read, or Bash in this session.

---

## P0 — Blocks real usage

### 1. Google OAuth consent screen (Testing mode)
Every login shows consent screen. Refresh tokens capped at 7 days.
Fix: Google Cloud Console → OAuth consent screen → Publish to Production.
Needs: privacy policy URL (volaura.app/privacy) + terms URL.
Verified: CEO session last_sign_in stuck at April 8 (SQL auth.users).

### 2. Two CEO accounts, split data
- `ganbarov.y@gmail.com` (id 5a01f0ce, email/password, admin=true, has profile "yusif")
- `yusif.ganbarov@gmail.com` (id d4594150, Google OAuth, NOW admin=true, profile "yusifganbarov")
Assessment data on one account, profile on another. Should be merged or linked.
Fix: either merge accounts in Supabase (link identities), or CEO picks one account.
Fixed this session: both now have is_platform_admin=true.

### 3. Assessment UX: multi-select misleading
User selects 8 competencies but test starts only with first one (line 124: `competencyList[0]`).
No visual indicator that remaining 7 are queued. User expects 8-competency test, gets 1.
Fix: either queue-progress indicator or limit selection to 1 at a time.

### 4. Two abandoned assessment sessions in DB
3 sessions total, 1 completed, 2 in_progress forever.
INC-019 (tab switch) was the cause, code fixed (zustand hydration guard).
Dead sessions not cleaned up — will block user from starting new assessment
for same competency (409 conflict on re-start).
Fix: cron or admin endpoint to expire stale sessions (>24h in_progress → expired).

---

## P1 — Important gaps

### 5. Score decay: formulas exist, execution missing
aura_calc.py defines half-lives per competency (730-1640 days).
Tests exist (test_decay_and_dece.py).
No `apply_decay()` function. No cron job. Scores never actually decay.
Claimed in docs/pitch materials.

### 6. Email/notifications: zero transport
email.py service file exists, no SES/Resend keys configured.
No `send_email` or `send_notification` in any router.
2 notifications in DB (likely seed). Users get no emails ever.

### 7. GDPR compliance tables empty
consent_events: 0 rows. human_review_requests: 0 rows. automated_decision_log: 0 rows.
Tables created, RLS exists, but no router writes to them.
Assessment asks for consent (automated_decision_consent flag) but doesn't LOG it.

### 8. Three "volunteer" tables in schema
volunteer_badges, volunteer_behavior_signals, volunteer_embeddings.
Positioning says NEVER use "volunteer". DB schema violates this.
Fix: rename tables via migration (breaking if code references old names).

---

## P2 — Should fix before launch

### 9. Public profile with no AURA score
/u/[username] renders for all 14 users. 13 have no AURA score.
Likely shows empty or broken card. Not verified visually.

### 10. UX dead ends and missing navigation (found 2026-04-18 19:30 Baku)
- /en/brandedby/generations → 404 (viewer exists at /generations/[id] but no list page)
- /en/admin/obligations → 404 (file written, Vercel rate limit blocks deploy until tomorrow)
- No breadcrumbs component anywhere in the dashboard — navigation relies entirely on browser back button and tab bar. User clicks into assessment/[sessionId]/complete → no way back except browser back. Same for profile/edit, events/create, onboarding steps.
- router.back() used in 6 places but fails if user arrived via direct link (back goes to previous site, not to dashboard)
- MindShift and BrandedBy tabs visible in nav but lead to placeholder-like pages with no real content
- Assessment completion page has no clear "return to dashboard" CTA

### 11. Crystal economy nearly empty
game_crystal_ledger: 1 transaction. Crystal shop exists in code
but no users have crystals. Economy is a ghost town.

---

## Database reality snapshot

| Metric | Count |
|--------|-------|
| profiles | 14 |
| auth.users | 14 |
| admins | 2 (fixed this session) |
| assessments total | 3 |
| assessments completed | 1 |
| AURA scores | 1 |
| questions | 123 |
| organizations | 1 |
| character_events | 2 |
| analytics_events | 35 |
| grievances | 0 |
| consent_events | 0 |
| notifications | 2 |
