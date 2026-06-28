# Hermes + Telegram Sprint — Handoff 2026-06-09

**Author:** Claude-instance for Atlas (Opus 4.8). **For:** CEO Yusif on return + next instance + Codex.
**CEO directive:** "большой спринт с агентами... я ухожу и хочу чтобы hermes работал наконец и телеграм мой работал."

## TL;DR (honest, no theatre)
Hermes does NOT yet run, and Telegram is NOT yet working — both are blocked on **two decisions only you can make**, not on engineering I skipped. Everything up to those two gates is done. The working asset (freellmapi gateway) was protected and is healthy.

## What is PROVEN working right now
- **freellmapi gateway LIVE + healthy** on GCP `freellmapi-gw` (e2-micro, $0/mo), IP `34.60.182.57:8799`, Docker `Up (healthy)`, real completions proven earlier (google/gemini-3.5-flash). Survived a hard reset, auto-restarted clean, same IP.
- Two research agents produced the full Hermes deploy recipe (config + Telegram + systemd) — captured below.

## The two gates (YOUR decisions — I will not take them unattended)

### Gate 1 — Hermes needs a bigger VM (+$24/mo). EVIDENCE-CONFIRMED, not estimate.
I installed Hermes on the e2-micro. The install alone drove free RAM to **73–90 MB** and stalled on the Node "browser tools" step, and it **degraded the live freellmapi gateway** (one endpoint started timing out). I killed the install and hard-reset the VM to protect freellmapi (now healthy again). Conclusion: a 969 MB e2-micro cannot even *install* Hermes cleanly, let alone run its always-on gateway. Hermes needs **e2-small (2 GB, ~+$24/mo)**.
- This is a spend commitment → your call (Constitution: Atlas is not the judge of financial commitments).
- Resize commands (keeps data; **note: stop/start changes the ephemeral IP — use a reserved IP first if you want to keep 34.60.182.57**, otherwise the gateway IP changes and must be re-read):
  ```bash
  gcloud compute instances stop freellmapi-gw --project volaura-inc --zone us-central1-a
  gcloud compute instances set-machine-type freellmapi-gw --machine-type e2-small --project volaura-inc --zone us-central1-a
  gcloud compute instances start freellmapi-gw --project volaura-inc --zone us-central1-a
  ```

### Gate 2 — Telegram needs a VALID bot token. The current one is DEAD.
The `TELEGRAM_BOT_TOKEN` in `apps/api/.env` returns **401 Unauthorized** (getMe, getUpdates, getWebhookInfo all 401). It is revoked/invalid. **This is almost certainly why your Telegram has been off.** A bot token can only be minted by you via **@BotFather** (your Telegram account). I cannot create a bot.
- Action: in Telegram, message @BotFather → `/newbot` (or `/revoke` + new token on the existing bot) → get a fresh token. Also get your numeric ID from @userinfobot for the allow-list.

## Resume steps once you've done the 2 gates (Atlas/next-instance can execute)
1. (If resized) confirm freellmapi container `Up (healthy)` + note the (possibly new) IP.
2. Re-run Hermes install on the VM: `curl -fsSL https://hermes-agent.nousresearch.com/install.sh | HERMES_NONINTERACTIVE=1 bash` (now has RAM headroom).
3. Configure model → gateway. `~/.hermes/config.yaml`:
   ```yaml
   model:
     provider: "custom"
     base_url: "http://localhost:8799/v1"
     api_key: "<freellmapi unified key — from the dashboard /keys page or container DB>"
     default: "<a model id the gateway serves, e.g. gemini-3.5-flash>"
   ```
   **Watch Hermes Issue #5161:** ensure no stale `OPENAI_BASE_URL` lingers in `~/.hermes/.env` after switching providers (it silently reroutes aux calls).
4. Telegram secrets in `~/.hermes/.env` (chmod 600):
   ```
   TELEGRAM_BOT_TOKEN=<fresh valid token>
   TELEGRAM_ALLOWED_USERS=<your numeric Telegram id>
   ```
5. Install + start the gateway as a systemd unit (survives disconnect + reboot):
   ```bash
   hermes gateway install      # writes ~/.config/systemd/user/hermes-gateway.service
   loginctl enable-linger "$USER"
   hermes gateway start
   hermes gateway status
   ```
   Add a memory cap so Hermes can never OOM-kill freellmapi (even on e2-small): in the unit `[Service]` add `MemoryMax=512M`, `OOMPolicy=kill`, `Restart=on-failure`.
6. Verify: `journalctl --user -u hermes-gateway -f` shows Telegram connected; you message the bot → it replies (routed via freellmapi at $0).

## Hermes state/config locations (for backup)
`~/.hermes/config.yaml` (settings), `~/.hermes/.env` (secrets), `~/.hermes/state.db` (sessions/memory/skills), `~/.hermes/logs/gateway.log`.

## Codex review items still open (separate tracks, NOT this sprint)
- D-1: add MIN_ITEMS guard to `/api/assessment/complete` (route guard + engine assert). Codex confirmed no gate exists.
- D-2: GDPR erasure — keep account-delete (`DELETE /api/auth/me`) immediate; anonymize audit via the retention pipeline (730/1095/2190 d). Do NOT cascade-delete. Codex verdict accepted.
- D-3/D-5: assessment errors-not-shown + results-review-list (frontend, Atlas can take).
- D-4: persist `selected_answer` (forward-only). Awaiting Codex on capture point.

## What I did NOT do (and why)
- Did NOT resize the VM ($24/mo spend = your call, you were away).
- Did NOT use the dead Telegram token (would 401 / conflict).
- Did NOT run a crash-prone Hermes gateway on the micro (would OOM-loop + endanger freellmapi).
- Did NOT touch the assessment scoring pipeline (D-1/D-4) solo (Class 3 — Codex reviewing).

## Cross-references
- `memory/atlas/ceo-feed/hermes-pilot-2026-06-09.md` (pilot plan, PR #115).
- `memory/atlas/ceo-feed/efficient-path-and-test-plan-2026-06-09.md` (gateway + tests, PR #116).
- `memory/atlas/codex-loop.md` (session log + D-3/D-4/D-5 + Codex review).
- freellmapi gateway: `http://34.60.182.57:8799` (live, $0, healthy).
