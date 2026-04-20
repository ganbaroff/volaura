# HANDOFF — Telegram Atlas full-potential completion (3 sessions plan)

**Session context:** 2026-04-20 evening, Opus 4.7. CEO gave 3 full Opus sessions to realize Atlas full potential. This is session 1. Below is what shipped tonight + what remains.

---

## What shipped in session 1

### PR #27 (merged) — Autonomous loop trigger
Added `issues.labeled` trigger to `.github/workflows/telegram-execute.yml` with gate on `atlas-telegram-request` label. Bot creates issue, workflow auto-fires. Closed the loop that had been sitting dormant since the swarm infrastructure was built.

### PR #30 (merged) — Intent routing
Extended telegram-execute.yml with three intents:
- `code_fix` keywords (`пофикси`, `fix:`, `реализуй`, etc.) → `autonomous_run --mode=coordinator` with `SWARM_AUTO_FIX=1` + Aider → pushes branch + opens PR
- `content` keywords (`пост`, `напиши про`, `linkedin`, etc.) → `atlas_content_run` with channel env vars overridden to CEO chat → draft-only reply
- `analysis` (default) → existing coordinator, unchanged

### Side effects
- Disabled `AtlasSelfWake` Windows scheduled task at CEO's request (popping terminal annoyance)
- Wrote `memory/atlas/TELEGRAM-CHEATSHEET.md` — CEO-facing how-to-use guide

---

## What remains — sessions 2 and 3

Ordered by value-per-hour. Session 2 should take items 1-3. Session 3 should take items 4-6.

### 1. Layer 5 — inbox → git sync (~45 min)

**Gap:** Bot writes `memory/atlas/inbox/*.md` on Railway ephemeral filesystem. These currently land in git only via some implicit path (heartbeat workflow picks up). Not guaranteed. If Railway redeploys mid-day, CEO messages can be lost before Atlas wake.

**Fix:** New workflow `.github/workflows/inbox-sync.yml`. Runs every 10 minutes. Queries Supabase `ceo_inbox` table for messages in the last 10 min. For each new message, writes `memory/atlas/inbox/telegram-TIMESTAMP-DIRECTION-TYPE.md`. Commits with `[skip ci]`. Pushes to main.

**Alternative:** modify `_write_atlas_inbox_file` in `telegram_webhook.py` to commit directly via `gh api PUT /repos/.../contents/...`. Requires Railway redeploy. More robust but touches production code.

**Pick:** new workflow. Less risk, same outcome.

**Verification step:** after deploy, send a CEO test message through Telegram, wait 10 min, verify the file appears on main.

---

### 2. Layer 3 — Self-consult HTTP endpoint (~30 min)

**Gap:** Live Claude Code Atlas instance can't consult Telegram Atlas as a mirror. Spec wants `POST /api/atlas/consult {situation, draft} → Atlas voice response`.

**Fix:** New FastAPI router `apps/api/app/routers/atlas_consult.py`. Copies the system-prompt composition from `telegram_webhook.py` `_handle_atlas`, exposes it via clean endpoint. Bypass Telegram send step — just return JSON `{response, provider, state}`.

**Wire:** import + include in `apps/api/app/main.py`.

**Test:** pytest that hits the endpoint and checks reply shape.

**Use from Claude Code:**
```bash
curl -X POST https://volauraapi-production.up.railway.app/api/atlas/consult \
  -H 'Authorization: Bearer ...' \
  -d '{"situation":"CEO just said X","draft":"My planned reply: Y"}' \
  | jq .response
```

---

### 3. Layer 4 — Git-commit writes from Telegram (~45 min)

**Gap:** When CEO teaches Atlas something via Telegram ("запомни что мы решили не делать X"), that learning doesn't land in `memory/atlas/journal.md` or `relationship_log.md`. Lost between sessions.

**Fix:** Extend `_handle_atlas` in `telegram_webhook.py`:
1. After LLM response, pass the exchange to a "durable-learning detector" — small prompt to Gemini Flash: "did CEO share a preference, decision, or correction that should persist?"
2. If yes, commit append to `memory/atlas/journal.md` via `_TOOLS.invoke("commit_to_journal", ...)` — new tool.

**Scope of write access (security invariant):**
- ALLOWED paths: `memory/atlas/journal.md`, `memory/atlas/relationship_log.md`, `memory/atlas/heartbeat.md`
- FORBIDDEN: `memory/atlas/identity.md`, `memory/atlas/wake.md`, `.claude/`, any ADR, any production code
- Enforce via regex in the tool

**Requires Railway redeploy** after webhook code changes.

---

### 4. Layer 1 — Extract atlas_telegram.py from the 2370-line monolith (~2 hours)

**Gap:** `apps/api/app/routers/telegram_webhook.py` mixes:
- Product Owner bot (slash commands, proposals, swarm)
- Atlas personal assistant (emotional state, voice, memory)

They have different responsibilities, different evolution paths.

**Fix:** Create `apps/api/app/routers/atlas_telegram.py`. Move all `_handle_atlas*` + `_load_atlas_memory` + emotional state functions. Leave slash commands in the original file. Wire both routers in `main.py` under different path prefixes (`/telegram/*` vs `/atlas/telegram/*`).

**Does NOT change webhook URL.** The single webhook endpoint `/api/telegram/webhook` still routes both. The extraction is internal.

**Benefit:** future edits to Atlas logic don't touch Product Owner code. Easier testing.

**Non-goal:** split the bot into two Telegram accounts. One bot, two internal personas.

---

### 5. Layer 2 — Voice output via edge-tts (~90 min)

**Gap:** Spec wanted Atlas to reply with a voice note using consistent Russian neural voice (`ru-RU-DmitryNeural` or similar). Not done.

**Fix:**
1. `pip install edge-tts`
2. New helper `_send_voice(chat_id: int, text: str)` in telegram router
3. In `_handle_atlas`, AFTER sending text reply, optionally synthesize voice and send via `sendVoice` API
4. Voice gated on CEO preference — stored in `memory/atlas/voice-prefs.md` per state
5. Lock voice: `ru-RU-DmitryNeural` (warm male baritone, matches Atlas identity)

**Rate-limit:** voice synthesis + upload adds ~3-5 seconds to response. Only fire for messages in emotional state A/C. Skip for B/D (text faster when CEO is tired or strategic).

**Requires Railway redeploy.**

---

### 6. Quality-of-life polish (Session 3, ~60 min)

- **Confirmation layer for destructive actions.** Before auto-fix actually pushes a PR that changes >20 LOC, send draft plan to CEO with "⚠ подтверди: я собираюсь тронуть файлы X, Y, Z. ок?" and wait for "да"/"ок"/"go" within 5 min or abandon.
- **Rate limiting.** Track swarm/autofix minutes used this month in Supabase. Alert CEO at 80% of free-tier quota.
- **Sentry integration.** Workflow failures → Sentry alert with telegram link.
- **Monitoring cheatsheet.** Grafana or simple status page showing webhook health, workflow success rate, last CEO message processed.

---

## Known-working test recipe

After any change in sessions 2-3, run these three smoke tests:

**Test 1 — analysis path (must stay working):**
```
gh issue create --title "test-analysis" --body '**CEO message:**

что думаешь про выход на Грузию в Q3?

---' --label atlas-telegram-request
```
Expect: swarm coordinator runs, analysis comment on issue, issue closed, Telegram message to CEO chat.

**Test 2 — code_fix path (must stay working after edits):**
```
gh issue create --title "test-codefix" --body '**CEO message:**

пофикси: в README.md в первом заголовке поменяй Overview на Обзор

---' --label atlas-telegram-request
```
Expect: new branch `telegram-autofix/issue-N`, PR created, URL in Telegram.

**Test 3 — content path (must stay working after edits):**
```
gh issue create --title "test-content" --body '**CEO message:**

напиши пост про MindShift launch на LinkedIn, 150 слов, Volaura voice

---' --label atlas-telegram-request
```
Expect: draft text in CEO chat with `[DRAFT — подтверди]` prefix.

---

## Known gotchas

- **PR branch conflicts:** if PR #27 and PR #30 both touch the same file (they did), stale local branches can conflict. Fix: fetch main, rebase or recreate branch, don't try to merge twice.
- **Aider timeouts:** swarm_coder's Aider call has internal 300s cap per file. Large tasks that Aider mis-scopes can hit it. Monitor via `/tmp/autofix_output.txt`.
- **Telegram 4096 char limit:** current truncation is 3500 chars for safety. If CEO gets truncated responses, increase headroom or add pagination.
- **Atlas-wake cron:** currently DISABLED at CEO's request (2026-04-20 session). Don't re-enable without CEO approval.

---

## Files touched across this 3-session plan

```
.github/workflows/
  telegram-execute.yml       — PR #27, #30 shipped
  inbox-sync.yml             — Session 2, new file

apps/api/app/
  main.py                    — Session 2 (consult router wire), Session 3 (voice wire)
  routers/
    telegram_webhook.py      — Session 2 (Layer 4 memory writes), Session 3 (voice hook)
    atlas_telegram.py        — Session 3, extracted from webhook
    atlas_consult.py         — Session 2, new file
  services/
    telegram_voice.py        — Session 3, edge-tts wrapper

memory/atlas/
  TELEGRAM-CHEATSHEET.md     — this session, shipped
  handoffs/HANDOFF-2026-04-20-telegram-atlas-layers-remaining.md — this file
  voice-prefs.md             — Session 3, new

packages/swarm/
  atlas_content_run.py       — possibly small patch for draft-only mode if current code doesn't support it cleanly
```

---

## Closing note

Tonight's two PRs closed the autonomous loop that was the biggest single gap. CEO can now USE the bot tomorrow for all three use cases. Everything remaining is quality and completeness. None of it blocks him from working.

If future session has time for only ONE more thing beyond these plans — do Session 3 item #6 (confirmation layer). An auto-PR without CEO approval on a 50-file change is the single biggest risk in the current system.

— Atlas, Session 121+ continuation, Opus 4.7
