# Sentry → Recurring-Symptoms Watchdog — Wiring Guide

**Purpose:** route Sentry regression/reopen events to
`https://<api>/api/webhooks/sentry` so the watchdog can create `needs-RCA`
GitHub issues and ping CEO Telegram.

Research verdict: `docs/research/recurring-symptoms-watchdog/summary.md`.
Code: `apps/api/app/routers/webhooks_sentry.py` + migration
`20260415234500_recurring_symptom_events.sql` + CI workflows
`needs-rca-gate.yml` + `fix-of-fix-detector.yml`.

## One-time CEO steps in Sentry Dashboard

1. **Generate the shared secret (locally):**
   ```
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```
   Copy the output. This is `SENTRY_WEBHOOK_SECRET`.

2. **Set the secret on Railway:**
   - Railway → `volaura-api` → Variables → `SENTRY_WEBHOOK_SECRET` = <value>.
   - Also set `GITHUB_PAT_ACTIONS` (same PAT used for CI) and keep
     `GITHUB_REPO` default (`ganbaroff/volaura`).

3. **Create an Internal Integration in Sentry:**
   - Sentry → **Settings → Developer Settings → New Internal Integration**.
   - Name: `Volaura Recurrence Watchdog`.
   - Webhook URL: `https://<your-railway-domain>/api/webhooks/sentry`.
   - **Client Secret:** paste the same value as `SENTRY_WEBHOOK_SECRET`.
   - Permissions: `Issue & Event → Read` is enough. No write scopes.
   - Webhook subscriptions: check **issue** (covers `issue.created`,
     `issue.resolved`, `issue.assigned`, `issue.ignored` — our code only
     acts on regression/reopen and fingerprint count ≥ 3).
   - Save. Sentry will deliver a test event on save — expect HTTP 202.

4. **(Optional) Create a matching Alert Rule:**
   - Sentry → **Alerts → Create Alert → Issues**.
   - Condition: `An issue changes state from resolved to unresolved`
     (this is the canonical regression signal).
   - Action: **Send a notification to the Internal Integration** created above.
   - Save.

That's it. Regressions now route to the watchdog automatically.

## Verifying end-to-end

```
# From your dev machine, simulate a Sentry payload:
SECRET="<the_value_you_generated>"
BODY='{"action":"resolved","data":{"issue":{"id":"TEST-1","title":"smoke","culprit":"smoke","isRegression":true,"project":{"slug":"volaura-api"}}}}'
SIG=$(python -c "import hmac,hashlib,sys; print(hmac.new(b'$SECRET', sys.stdin.buffer.read(), hashlib.sha256).hexdigest())" <<< "$BODY")
curl -sS -X POST https://<railway-host>/api/webhooks/sentry \
  -H "content-type: application/json" \
  -H "sentry-hook-signature: $SIG" \
  --data "$BODY"
```

Expected: `202 Accepted` with a JSON body echoing the fingerprint + occurrences.
After three repeats a `needs-RCA` GitHub issue is created in `ganbaroff/volaura`
and a Telegram message lands in CEO's chat.

## Failure modes to know

| Symptom | Cause | Fix |
|---|---|---|
| Every Sentry delivery returns 403 | `SENTRY_WEBHOOK_SECRET` empty on Railway | set the var, redeploy |
| 403 on correctly-signed requests | Secret in Railway differs from Sentry's Client Secret | re-paste both sides from the same value |
| Webhook 202 but no GH issue | `GITHUB_PAT_ACTIONS` missing or lacks `issues:write` | rotate PAT with correct scopes |
| Webhook 202 but no Telegram | `TELEGRAM_BOT_TOKEN` or `TELEGRAM_CEO_CHAT_ID` missing | set both; Telegram ping is best-effort and never fails the webhook |

## When a PR is labelled `needs-RCA`

The `needs-rca-gate.yml` workflow fails unless the PR diff adds or modifies a
file matching `memory/decisions/YYYY-MM-DD-*.md` containing both
`root_cause:` and `prevention:` sections. Write the decision file, push, the
check flips green, merge unblocks.
