# E2E Bug List — Prod (2026-04-12)

## BUG-1: Question text empty on assessment start
NOT REPRODUCIBLE on clean user. Clean test (atlas-clean-test@volaura.app)
returned question correctly: type=open_ended, text present, id present.
Original failure was on dirty test user with prior sessions + rapid-restart.
Status: NOT A BUG — test artifact from stale session state

## BUG-2: /api/health returns 404
FALSE BUG — correct path is /health (no /api prefix). Health router mounted without prefix.
Status: NOT A BUG — test was wrong

## BUG-3: /api/badges/me returns 404
FALSE BUG — route is /{volunteer_id}/credential, not /me. By design.
Status: NOT A BUG — test used wrong path

## BUG-4: /api/activity returns 404
FALSE BUG — correct path is /api/activity/me. Works: 200 OK.
Status: NOT A BUG — test was wrong

## BUG-5: /api/leaderboard/current returns 404
FALSE BUG — correct path is /api/leaderboard (no /current). Works: 200 OK.
Status: NOT A BUG — test was wrong

## BUG-6: AURA score=17.5 with badge=none after completing reliability+communication
Severity: P1 — score seems too low for 2 competencies completed
Status: NEEDS INVESTIGATION — is this correct math or broken calculation?

## BUG-7: Gemini 429 on Telegram bot (free tier exhausted)
Severity: P1 — bot can't respond
Fix: Groq fallback added (commit 23218c4)
Status: FIXED in code, awaiting deploy

## BUG-8: Webhook URL was pointing to dead domain
Fix: corrected to volauraapi-production (commit 75f9fa7)
Status: FIXED and verified
