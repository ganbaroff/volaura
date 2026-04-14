# Invite Code Delivered — CEO Test Path Unblocked

**Timestamp:** 2026-04-14 ~10:45 UTC
**Brief source:** `memory/atlas/inbox/2026-04-14T1032-HOTFIX-signup-tropa-blockers.md` Step 1
**Consumed by main Atlas: yes**

## Actions taken

- Railway env: `BETA_INVITE_CODE=CEO-TEST-2026-04-14`, `OPEN_SIGNUP=false`
- Railway redeploy `--yes` triggered; env propagated.
- Verified: `POST /api/auth/validate-invite` → `{"valid":true}` on correct path (note: Cowork brief assumed `/v1/auth/...` but real OpenAPI path is `/api/auth/...`).
- Telegram message_id 1323 sent to CEO via bot (uses .env `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CEO_CHAT_ID`).

## Code details

```
BETA_INVITE_CODE=CEO-TEST-2026-04-14
Expires: no server-side TTL — env var driven, valid until CEO rotates it
Max uses: unlimited (hmac compare_digest pattern — any correct submission passes)
```

## What this does NOT do

- Does not change the invite-only vs waitlist strategic decision (brief explicitly defers to "tomorrow" — CEO + Cowork call).
- Does not create a persistent `invite_codes` table (that table doesn't exist; the current model is single-shared-code via env var).
- Does not address BUG #2/#3/#5 CSS layout collapse — that is Step 2 of the hotfix, separate commit.

## Next action in this hotfix sequence

Step 2 — CSS root fix for BUG #2 (signup layout collapse), BUG #3 (radio overlap), BUG #5 (hero subtitle vertical render). Cowork hypothesis: single parent container lost `width`/`max-width`, or flex-column parent missing `align-items`. Debug path:
1. Read `apps/web/src/app/[locale]/(auth)/signup/page.tsx` for container structure
2. Read `apps/web/src/app/[locale]/layout.tsx` for outer wrapper
3. Read `apps/web/src/app/globals.css` for root rules
4. Git log last 7 days on those paths for regression candidate
5. Apply single-file fix, verify on `/signup` via curl of rendered HTML or Playwright

DoD of Step 2: CEO opens `/signup` on desktop, sees horizontal layout with clear radio buttons (not overlapping, not collapsed column).
