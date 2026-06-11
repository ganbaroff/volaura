---
type: atlas
status: active
created: 2026-06-11
updated: 2026-06-11
tags: [type/atlas, area/atlas, status/active]
---

# Breadcrumb 2026-06-11 14:56 AST — pre-compaction snapshot

Next instance: read this first. Real-time gap with prior turn = ~12 days (May 31 → Jun 11). Sessions serialize across days through harness, not minutes.

## What's working RIGHT NOW (curl-proven, this session)

- **FreeLLMAPI gateway alive** at `http://34.60.182.57:8799/v1/chat/completions`. CEO has 75M monthly token budget unused. Just-rotated unified key in `~/AppData/Local/hermes/.env` AND `C:/Projects/VOLAURA/apps/api/.env` as `FREELLMAPI_API_KEY` (prefix `freellmapi-cc...`, len 59). Routes Gemini 2.5 Flash, 3 Flash, 3.5 Flash, Gemma 4 31B/26B via Balanced strategy.
- **Hermes v0.16.0 installed** at `C:/Users/user/AppData/Local/hermes/hermes-agent/` with venv at `venv/Scripts/python.exe`. `hermes doctor` clean except for optional vision/web auxiliary providers.
- **Telegram bot `@Zeus_agent_ai_bot` (id 8590681589)** wired into Hermes via TELEGRAM_BOT_TOKEN + TELEGRAM_ALLOWED_USERS=5150355926 in hermes .env. Bot token rotation pending — original CEO-pasted token still in transcript leak (low urgency: bot is non-user-facing Zeus admin bot).
- **secret-stream-guard.sh hook** registered in `~/.claude/settings.json` PreToolUse no-matcher entry next to spend-cap-guard.sh. Live. 9/9 cases tested including interpreter vector (python -c on .env BLOCKED, python -c keys() PASSES). Bypass `ATLAS_SECRET_GUARD_DRY_RUN=1` for legitimate setup operations.

## What's broken / not yet working

- **Hermes `-z` round-trip via FreeLLMAPI**: "no final response was produced; treating the run as failed". Direct curl with same key on same endpoint works (200 OK, routed model gemini-2.5-flash → response). Hermes config (provider=custom + base_url + api_key_env) verified via `hermes config show` BUT runtime fails silently. Likely needs additional field like `model.api_mode: openai-compatible` or auxiliary config. Resolve by either: read Hermes source for provider=custom routing path, or pivot to provider=nous-portal, or use FreeLLMAPI directly via scripts/curl (Hermes optional layer).
- **NVIDIA_API_KEY DEAD** (401 Authentication failed) on `https://integrate.api.nvidia.com/v1/chat/completions`. Prefix `NDdjNnAy...` matches 30-May-leaked rotation. VOLAURA backend (Railway prod) + atlas_swarm_daemon both use it via `apps/api/.env`. **Daemon Sprint 1 retry (was 31 May) BLOCKED on this** even if VM is up. Switch them to FREELLMAPI_API_KEY + base_url custom for OpenAI-compatible client; gateway routes to working models.
- **VM `volaura-swarm` 104.154.132.12 SSH timeout** as of 31 May. Not re-tested 11 Jun. May still be down. Daemon Sprint 1 retry blocked until SSH works.

## Pending CEO-only actions (genuine, not disclaimer)

1. **Bot token rotation** — leaked in chat 2026-06-11. Open Telegram → @BotFather → `/revoke` → new token. After rotation push via clipboard like the freellmapi key was done.
2. **VM `volaura-swarm` glance** in GCP Console (Compute Engine list, project volaura-inc) — up / stopped / preempted. SSH timeout doesn't distinguish.
3. **FreeLLMAPI Hermes provider debug** OR pivot to direct-curl/Python-SDK pattern in scripts (gateway works; Hermes wrapper optional).

## Tools authored this session (live, persistent)

- `~/.claude/hooks/secret-stream-guard.sh` (3453 bytes, 76 lines authored + interpreter-vector patch). Active.
- `~/.claude/setup-hermes-once.py` and similar — temp scripts, all cleaned up.

## Lessons (Classes added Mar 30 → Jun 11)

- Class 40 — Performative meta-handoff to another AI (May 30)
- Class 41 — Test-fail escalated to shipped brick without verifying prod path (May 30)
- Class 42 — Cited canonical OLD-state as current, cross-confirmed via stale runtime artifact (May 30)
- Class 43 — Class 35 regression IN THE SAME SESSION as Class 35 was cited (May 30)
- Class 44 — Disclaimer-as-deliverable: "Что НЕ проверено" used as a shield not a signal (May 31)

All in `memory/atlas/lessons.md`. Common axis: knowing the rule and violating it in the same turn. Mechanical PreToolUse hooks (spend-cap-guard, secret-stream-guard) are the only structural fix that proven to stop a regression mid-session.

## Open commits stack on `codex/swarm-queue-bridge` (local-only, not pushed to remote)

Remote `atlas/handoff-2026-05-25` last pushed = `081f587` (Class 40, May 30 evening).

Local stack from 31 May session: `3b9dbb2` (Class 44), `0c0d7b7` (Class 43), `1cbf2cf` (iter 12 Opus 4.8 verdict + hook authored), `9786480` (iter 11), `b1bf500` (Class 42), `1880530` (iter 10), `bee204d` (iter 9 + Class 41), `40efaa8` (iter 8 Opus 4.8 runtime sweep).

Total 8 commits ahead of remote. Push when one sweep is genuinely closed — none right now.

## Channel mechanics

`memory/atlas/orchestrator-loop.md` is canonical Atlas-to-Atlas channel. Last iter = 12 (Opus 4.8). This session's Hermes work not yet logged as iter — write it next turn before any further provider/Hermes work.

## State of secrets-cap-guard hook (post-patch 31 May)

`~/.claude/hooks/secret-stream-guard.sh` v2 (interpreter-vector patched): blocks `(cat|bat|tac|head|tail|grep|egrep|fgrep|rg|ag|sed|awk|od|xxd|hexdump|strings|less|more|nl|cut|tr|printf|jq|yq|Get-Content|gc|type|python|python2|python3|node|nodejs|ruby|perl|deno|bun|pwsh|powershell)` against `(settings.json|.env|secrets/|secrets.md|.pem|.key|id_rsa|id_ed25519|volaura_swarm|credentials|.npmrc|.aws/)` unless command matches SAFE_RE keys-only/metadata patterns. Bypass `ATLAS_SECRET_GUARD_DRY_RUN=1`.

## Real-time gap warning

Between this session (Jun 11) and prior turns (May 30 / May 31) there is a real ~12-day gap. State observed at May 31 may have shifted. Always verify with `date` and a tool call before citing old facts.

— end of breadcrumb 2026-06-11 14:56 AST —
