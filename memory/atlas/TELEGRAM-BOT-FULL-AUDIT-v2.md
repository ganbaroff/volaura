# Telegram Bot Full Audit v2 — 2026-04-14

**Trigger:** CEO — "сделай наконец то полный аудит телеграмма. что есть. что просилось что должно быть чего не хватает".

**Why v2:** v1 (`telegram-bot-audit-2026-04-14.md`) covered the three P0 bugs I found in E2E smoke test. v2 is the capability/intent delta — asked vs shipped vs missing.

---

## 1. История CEO-хотелок — verbatim из journal

**Session 95 (2026-04-14/15)** — "Я хочу развить хотя бы одного агента до максимального уровня." + "не чатбот, персональный ассистент который учится". → self-learning deployed (atlas_learnings table + Groq extraction).

**Session 95 correction** — "нахрена мне знать про seed_questions_batch2.sql?" → rule: убирать filenames с расширениями из output к CEO.

**Session 105** — Atlas как executor, не болтун. `/execute` команда → `gh workflow run` → GH Actions исполняет. telegram-execute.yml workflow + telegram_ambassador.py созданы.

**Mega-plan 2026-04-14 Track 1 final row:** "Telegram bot: executor, not chatbot" — unchecked до сегодня.

**Session 111 wave 1 (12:05 UTC)** — "реши с корнем проблему агента в телеграм... и он это ты" → Atlas identity fix + memory loading + multi-provider.

**Session 111 wave 2 (12:30 UTC)** — "сначала все тесты провди всю картину посмотри всю экосистему что он умеет что он должен уметь и потом вернись глубокий аудит думай шикроко" → v1 audit + E2E smoke test → три P0 найдены и починены.

**Session 111 wave 3 (now)** — "сделай наконец то полный аудит телеграмма" → этот v2.

---

## 2. Что реально есть в коде сейчас (телеграм-webhook.py, 1848 строк)

24 функции. 15 command-dispatch веток. Источник: `apps/api/app/routers/telegram_webhook.py`.

**Chat / generic paths:**
- `_classify_and_respond` — free-text fallback, classify ideas/tasks/reports, NVIDIA-first chain.
- `_handle_atlas` — срабатывает на "Атлас"/"/atlas" + на любой non-command text, identity + memory + emotional-state aware.

**Команды (slash):**
- `/status` — live stats (users, sessions, orgs) из DB.
- `/ecosystem` — состояние 5 продуктов из heartbeat-файлов.
- `/proposals` — pending swarm proposals с inline-кнопками.
- `/backlog` — ceo_inbox ideas/tasks последние 30.
- `/skills` — product skills список.
- `/agents` — roster (13 perspectives + ~118 skill modules) с live-state из agent-state.json.
- `/agent {id} {task}` — делегирует задачу одному агенту (NVIDIA/Gemini через perspective).
- `/swarm {task}` — координатор, squads + синтез.
- `/queue` — autonomous-queue из memory/swarm/.
- `/findings [N]` — typed findings из blackboard.
- `/simulate` — 10-persona UX-friction simulation.
- `/ask {agent} {q}` — прямой вопрос одному агенту.
- `/help`, `/start` — справка.

**Inline-actions (callback queries):**
- Proposal buttons: `act/dismiss/defer {id}`.
- Text form: `act {id}`, `dismiss {id}`, `defer {id}`, `ask {id} {question}`.

**Special paths:**
- Voice messages → Groq Whisper transcription → text flow.
- `_execute_proposal` — GH Actions `workflow_dispatch` trigger на swarm-daily.yml с inputs={mode:"coordinator"}.

**Memory / persistence:**
- `ceo_inbox` table — conversation history (182 rows до сегодня, после smoke test растёт снова).
- `atlas_learnings` table — cross-session observations (6 rows total, 3 categories used; CHECK на 8 allowed; ZenBrain emotional_intensity 0-5).
- `_load_atlas_memory()` — читает `memory/atlas/{identity,heartbeat,journal-tail,relationships,lessons,cost-control-mode}.md` каждый запрос.
- `_atlas_extract_learnings()` — NVIDIA-first extraction → atlas_learnings INSERT после каждого turn.

**Security:**
- HMAC-secret gate на webhook (fail-closed, commit 56803ea session 108).
- CEO_CHAT_ID filter как defence-in-depth.
- Constant-time compare_digest.

---

## 3. Что просилось vs что есть — Capability Matrix

| CEO запросил | Статус | Детали |
|---|---|---|
| Atlas identity (не "CTO-бот MiroFish", не "ambassador") | ✅ работает | First-person Russian, верифицирован E2E smoke test 12:28 UTC |
| Cross-substrate continuity (Cowork/CLI/Telegram = один Atlas) | ✅ в prompt | Identity explicitly "one Atlas across three substrates" |
| Self-learning от каждого разговора | ✅ работает | 3 новых observations за 90 секунд smoke test |
| Эмоциональная память с decay weighting | ✅ partial | emotional_intensity поле есть, но нет retrieval-time decay math (читается по intensity DESC, не по decayed score) |
| Читает memory/atlas/ на каждый запрос | ✅ работает | `_load_atlas_memory` каждый turn загружает 6 файлов |
| Multi-provider без Claude API direct | ✅ работает | NVIDIA NIM → Gemini → Groq chain; Haiku banned |
| Conversation history сохраняется | ✅ работает | ceo_inbox после CHECK-fix пишет `free_text` + metadata |
| Voice input от CEO (Whisper transcribe) | ✅ работает | Groq Whisper, `audio/ogg` upload |
| **Voice output от бота (TTS)** | ❌ отсутствует | Bot ответ только текст. ElevenLabs/Piper не подключены |
| Executor, не chatbot (session 105 intent + megaplan final row) | 🟡 partial | `/execute` есть ТОЛЬКО для proposal-id из proposals.json; generic "атлас задеплой X" → chat-ответ, не workflow_dispatch |
| Proactive messages (bot инициирует когда swarm нашёл) | ✅ работает | swarm-daily.yml + notifier.py с vacation + 6h cooldown |
| Reporting CEO — "ecosystem works, no problems" | 🟡 partial | daily digest cron 23 UTC есть; но generic proactive "всё хорошо" бот не шлёт если swarm молчит |
| Rate limiting | ❌ отсутствует | Нет specific rate limits на webhook endpoint, только global middleware |
| Admin bypass для debug команд (например CEO может test secret rotation) | ❌ отсутствует | Нет /admin или /debug команд |
| Langfuse tracing для each LLM call | ❌ закомментировано | "Langfuse keys are set but 'langfuse' package is not installed" — warning в логе |
| Emotional state-aware tone switching | ✅ работает | `_detect_emotional_state` A/B/C/D injected в system prompt |
| AZ/EN language auto-switch based on CEO | 🟡 partial | Bot отвечает русским всегда (хочет AZ — не пробовал) |
| Inline keyboard rich UI | ✅ работает | Proposal buttons act/dismiss/defer |
| `/execute` для произвольных задач CEO | ❌ отсутствует | Только для существующего proposal_id |
| Integration с MindShift через character_events | 🟡 partial | Code path exists (cross_product_bridge.py), но MINDSHIFT_URL не set |
| Swarm proposals ranking и summarization | ✅ работает | `_handle_proposals` показывает отсортированные по severity |

---

## 4. Gap-матрица — что реально отсутствует в порядке важности

### P0 — критично для "executor not chatbot"
1. **`/execute "free text task"` команда** — user говорит естественным языком "Атлас, задеплой миграцию X" или "Атлас, прогони ruff на apps/api", бот триггерит GH Actions workflow c task-payload. Сейчас workflow_dispatch доступен только через `/act {proposal_id}`. Мегаплан Session 105 row 1-3 помечен [x] но только для proposal-execute ветки. Generic `/execute` — отсутствует.

### P1 — качество of life
2. **TTS voice responses** — CEO шлёт voice, Atlas понимает (Whisper). Но отвечает только текстом. Для mobile флоу это разрыв. ElevenLabs или локальный Piper + `sendVoice` Telegram API.
3. **Langfuse wiring** — keys set но package не installed. Значит каждый LLM call уходит без observability; нельзя дебажить quality/latency/cost per turn.
4. **Retrieval-time emotional decay** — сейчас `_load_atlas_learnings` делает `ORDER BY emotional_intensity DESC LIMIT 30`. Это не decay по времени. Правильный ZenBrain формуле нужно: `weight = 1.0 + emotional_intensity × 2.0`, `decayed_score = weight × exp(-Δdays/τ)`, `ORDER BY decayed_score DESC`. Сейчас старые high-intensity rows вытесняют свежие low-intensity — перевёрнутая логика для живой памяти.

### P2 — nice to have
5. **AZ/RU auto-switch** — detect CEO language from last message, match. Сейчас always RU.
6. **`/debug` или `/admin` команды** — CEO может попросить "покажи webhook secret head", "rotate CRON_SECRET", "trigger cron manually". Сейчас нет.
7. **MINDSHIFT_URL wiring** — cross-product bridge код есть, URL не set → push_crystal_earned skips.
8. **Rate limit на webhook endpoint** — если кто-то узнает secret + chat_id CEO, спам возможен. Сейчас защита только HMAC+chat_id filter.
9. **Proactive "all green" daily** — если swarm молчит 24h и ничего proposals не создал, CEO не получает подтверждения что bot жив. Daily digest покрывает это частично но formatted как summary, не как heartbeat.

### P3 — research phase
10. **Voice-to-voice полный loop** — STT + TTS cycle with Atlas-specific voice (не просто default). Нужна voice-consistency модель.
11. **Автоматическое suggest follow-ups** — бот предлагает 2-3 next actions после каждого ответа (inline keyboard). Сейчас кнопки только на /proposals.
12. **Bot-initiated conversations per ZenBrain decay** — если prior observation имеет intensity=5 и давно не cited, бот сам инициирует обсуждение.

---

## 5. Что уже done и верифицировано E2E (чтобы CEO знал чего не трогать)

- Atlas identity across ceo_inbox + atlas_learnings verified 2026-04-14 12:28 UTC
- NVIDIA NIM primary работает (direct test + production test)
- Memory loading работает — все 6 memory/atlas/ файлов инжектируются
- HMAC webhook security fail-closed
- Vacation mode integration live (notifier.py)
- Daily digest cron 23 UTC active

---

## 6. Priority order для следующей Atlas-волны

Если CEO даст зелёный на один batch:

1. **`/execute free-task`** — эта команда превращает бот из болтуна в executor. Мегаплан row "Telegram bot: executor, not chatbot" закрывается.
2. **Langfuse wire** — `pip install langfuse` в requirements + декоратор на каждый LLM call. 30 минут работы, даёт observability на все следующие итерации.
3. **Decay-correct retrieval** — поменять `ORDER BY emotional_intensity DESC` на computed `decayed_score` с time factor. Вопрос не "что самое интенсивное" а "что самое живое в памяти сейчас".

Остальное (TTS, admin commands, MindShift URL, rate limit) — отдельно когда CEO явно попросит.

---

## 7. Что следующая Atlas-волна НЕ должна делать

- Не дублировать v1 audit. Там bugs, тут capabilities. Разное.
- Не добавлять новые handlers без конкретной CEO-команды — 24 уже существуют.
- Не трогать HMAC/secret слой — он правильно fail-closed.
- Не переписывать identity prompts — они только что стабилизированы wave 1.
- Не переставлять provider chain — NVIDIA-first correct, tested, задокументировано.

---

Файл hardcoded в git, next Atlas wake будет видеть через `_load_atlas_memory()` тоже — aud auto-inject в system prompt when this file is added to the loader list.
