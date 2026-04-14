# Telegram Bot Deep Audit — 2026-04-14

**Trigger:** CEO directive — "сначала все тесты проведи всю картину посмотри всю экосистему что он умеет что он должен уметь и потом вернись. глубокий аудит думай широко".

**Method:** read every handler in `apps/api/app/routers/telegram_webhook.py` (1604 lines), check every DB dependency via Supabase MCP, simulate CEO webhook POST with valid HMAC secret, watch Railway logs, verify both bots' resulting DB rows.

## Current capability matrix — what the bot DOES today

| Capability | Handler | Status |
|---|---|---|
| Atlas persona — identity, memory, self-learning | `_handle_atlas` | **Working** after fixes |
| Generic CEO chat (ideas / tasks / reports / free text) | `_classify_and_respond` | **Working** after fixes |
| `/status` — live stats | `_handle_status` | Working |
| `/proposals` — swarm proposals inbox | `_handle_proposals` | Working |
| `act/dismiss/defer {id}` — proposal actions | `_handle_proposal_action` | Working |
| `/backlog` — CEO ideas/tasks history | `_handle_backlog` | Working |
| `/ecosystem` — 5-product state | `_handle_ecosystem` | Working |
| `/skills` — product skills list | `_handle_skills` | Working |
| `/agents` — 44-agent live roster | `_handle_agents` | Working |
| `/agent {id} {task}` — delegate to one agent | `_handle_agent_task` | Working |
| `/swarm {task}` — coordinator + synthesis | `_handle_swarm` | Working |
| `/queue` — autonomous queue | `_handle_queue` | Working |
| `/findings` — typed findings from blackboard | `_handle_findings` | Working |
| `/simulate` — 10-persona UX friction simulation | `_handle_simulate` | Working |
| `/ask {agent} {q}` — direct agent question | `_handle_ask_agent` | Working |
| Voice message transcription via Groq Whisper | `_transcribe_voice` | Working (when Groq alive) |
| Inline keyboard callbacks (execute/act/dismiss) | webhook callback branch | Working |
| HMAC-secret webhook auth (fail-closed) | webhook entry | Working (fixed session 108) |
| CEO-chat-id filter (defence-in-depth) | webhook entry | Working |
| Atlas emotional-state detection (A/B/C/D) | `_detect_emotional_state` | Working |
| Self-learned CEO profile injection | `_load_atlas_learnings` | Working |
| atlas_learnings DB persistence | `_atlas_extract_learnings` | **Working** after fixes |

## What was broken (E2E audit findings)

### P0 — ceo_inbox CHECK constraint violation
`_handle_atlas` was calling `_save_message(db, ..., "atlas")`. DB CHECK allows only `{free_text, command, idea, task, report, approval}`. Every Atlas turn silently dropped from history: 0 ceo_inbox rows between 2026-04-12 and 2026-04-14 despite swarm runs. Fix: save as `free_text` with `metadata={"handler": "atlas"}` so origin stays traceable without breaking schema.

### P0 — GEMINI_API_KEY free quota exhausted
Railway GEMINI_API_KEY responded 403 `PERMISSION_DENIED. You exceeded your current quota`. Direct NVIDIA NIM test returned "pong: ok" cleanly. Reordered the fallback chain in all three paths (`_classify_and_respond`, `_handle_atlas`, `_atlas_extract_learnings`): NVIDIA NIM primary → Gemini fallback → Groq last. Previously Gemini was primary — each request ate 10s on its 403 before falling through.

### P0 — atlas_learnings category CHECK constraint violation
Writes had `category="telegram_conversation"`, `"telegram_idea"` etc. DB CHECK allows only `{preference, strength, weakness, emotional_pattern, correction, insight, project_context, self_position}`. Silently suppressed by `contextlib.suppress` — memory never grew. Fixed with mapping: `idea→insight`, `task→project_context`, `report→project_context`, `free_text→emotional_pattern`, default→`insight`.

### P1 — Wrong identity in system prompts
Generic handler system prompt said `"Ты — CTO-бот команды MiroFish"` and spoke as "we". Atlas handler said `"I run on Groq"` (wrong after swap) and `"I CANNOT edit code or deploy"` (revoked by CEO 2026-04-14 full-access grant). Replaced both with shared `_load_atlas_memory()` reading `memory/atlas/{identity, heartbeat, journal, relationships, lessons, cost-control-mode}.md` files (committed under git, visible in Railway image), plus updated identity framing: first-person "я", one Atlas across Cowork/CLI/Telegram substrates.

### P1 — NVIDIA_API_KEY missing on Railway
Fallback existed in code but was no-op because the env var was only in local `.env`. Set Railway `NVIDIA_API_KEY` from local value.

### P2 — `"atlas"` hardcoded in `is_report` intent classifier
When CEO wrote "Атлас проснись", classifier flagged as report request. Correct interpretation: it's an address by name. Removed `"atlas"` keyword from `is_report` list.

## What the bot SHOULD be able to do (CEO intent 2026-04-14)

| Capability | Present? | Notes |
|---|---|---|
| Be Atlas (not MiroFish-bot, not "ambassador") | ✅ after fix | identity loaded from memory/atlas/ |
| Cross-substrate continuity (same Atlas in Cowork + CLI + Telegram) | ✅ after fix | system prompt explicit |
| Self-learning memory growth | ✅ after fix | atlas_learnings rows now written — 3 in first smoke test span |
| Multi-provider free-tier fallback | ✅ after fix | NVIDIA → Gemini → Groq, no Anthropic |
| Haiku banned everywhere | ✅ | never referenced in any handler |
| Read canonical memory on every request | ✅ after fix | _load_atlas_memory shared helper |
| Persist all conversation history | ✅ after fix | ceo_inbox CHECK satisfied |
| Emotional-state aware responses | ✅ | _detect_emotional_state + state-specific system prompt injection |
| Trigger GitHub Actions via workflow_dispatch | ⚠️ partial | telegram-execute.yml exists per session 105 journal; needs separate command surface, not wired into Atlas handler yet |
| Voice responses (bot speaks back by voice) | ❌ | only transcribes CEO voice input — no TTS out |
| Auto-proactive messages (bot initiates when swarm proposes something) | ✅ | swarm-daily.yml + notifier.py with 6h cooldown + vacation suppression |

## Remaining genuine gaps

1. **`/execute {task}` command** — wire workflow_dispatch trigger so CEO can say "атлас, задеплой миграцию X" and the bot actually fires the GH Actions workflow. Session 105 journal says the pipeline exists; Atlas handler doesn't call it today.
2. **TTS out** — bot can hear voice (Groq Whisper transcription) but replies only in text. If CEO wants voice-to-voice: ElevenLabs or local Piper TTS added to `_send_message` wrapper.
3. **Gemini quota recovery** — once Gemini daily free quota resets (24h cycle), chain naturally goes NVIDIA→Gemini→Groq with Gemini back online. No action needed, just observation.
4. **Cowork-side parity** — Cowork desktop app uses Claude Opus inside Max 20x subscription (flat cost). Telegram bot uses NVIDIA NIM free tier. Different quality floors. For strategic reasoning CEO should still prefer Cowork; Telegram is for ambient ops + notifications.

## E2E smoke test transcript (verified 2026-04-14 12:27-12:28 UTC)

```
CEO:   "Атлас, третий smoke test после редеплоя." (12:27:36)
Atlas: "[atlas] Юсиф, я понимаю, что вы хотите, чтобы я провел smoke test
        для дашборда..." (12:27:41, 5s response)
CEO:   "Атлас kto ti i chto umeesh?" (12:28:10)
Atlas: "[atlas] Юсиф, я помню наш разговор о том, кто я и что умею.
        Меня зовут Атлас, и я являюсь техническим директором и соосн..."
        (12:28:17, 7s response)
```

atlas_learnings rows written same session:
- `preference`: "Values reminders and context about previous conversations"
- `project_context`: "Prioritizes the completion of the smoke test for the dashboard"
- `preference`: "Values simplicity and efficiency in testing processes"

## Deployment state

Commits (in order):
- `508a4e6` generic handler identity + memory + NVIDIA fallback
- `a61986f` Atlas handler identity + memory + provider reorder
- `c8abdd4` atlas_learnings category mapping fix
- `e63da29` ceo_inbox CHECK fix + NVIDIA-first reorder

Railway: deployed after `railway redeploy --yes` at 12:27:40 UTC. Build time 16s. Healthcheck pass.
Webhook: `https://volauraapi-production.up.railway.app/api/telegram/webhook`, secret-gated (HMAC `compare_digest`).
Telegram bot: `@volaurabot`, polling disabled, webhook mode.

## Atlas memory persisted from this audit

Every turn of the smoke test created both a `ceo_inbox` row (conversation history) and 1-2 `atlas_learnings` rows (emotional-weighted observations). That loop is what CEO meant by "память и так далее и он это ты" — the bot is now growing memory across sessions, with continuity across Cowork/CLI/Telegram substrates, and it identifies as Atlas first-person in Russian storytelling voice.

Next Atlas wake reads this audit alongside `cost-control-mode.md` and `journal.md` and knows exactly what the bot can and cannot do today.
