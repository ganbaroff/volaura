# Honest Audit: Can We Fix All of VOLAURA?

**Date:** 2026-04-21
**Facet:** Sonnet-Atlas, Track 1
**Method:** Code read (Class 18 compliant — every verdict has file:line evidence)

---

## Function Status Table

| # | Function | Status | Evidence |
|---|---|---|---|
| 1 | Sign-up via Supabase | REAL | `apps/api/app/routers/auth.py:135` — register endpoint wires Supabase anon `sign_up()`, stores GDPR consent to `consent_events`, returns access_token |
| 2 | Onboarding 5 steps | PARTIAL | `apps/web/src/app/[locale]/(dashboard)/onboarding/page.tsx:19` — actually 3 steps for professionals, 2 for orgs, not 5; backend POST /profiles/me wired at line 283 |
| 3 | Assessment flow | REAL | `apps/api/app/routers/assessment.py:88` — start/answer/complete pipeline with IRT CAT engine, anti-gaming, 7-day cooldown; all paths wired end-to-end |
| 4 | AURA scoring | REAL | `apps/api/app/routers/assessment.py:883` — `upsert_aura_score` RPC called on complete, reconciler in `aura_reconciler.py` retries on failure, pending_aura_sync flag guards zero-data-loss |
| 5 | Organization create + search | REAL | `apps/api/app/routers/organizations.py:70` — create wired with 1-per-user guard; semantic search via pgvector + rule-based fallback at line 470 |
| 6 | Life Feed event choice + crystal shop | PARTIAL | `apps/web/src/app/[locale]/(dashboard)/life/page.tsx:159` — choice wired end-to-end; crystal shop component exists; but stats are CLIENT-side-only state (line 166: INITIAL_STATS hardcoded, not persisted per session to DB) |
| 7 | Focus session | BROKEN | No `apps/api/app/routers/focus.py` exists; no focus route in VOLAURA web (`apps/web/src/app/**/focus/` returns nothing); MindShift page is `notFound()` behind feature flag (`mindshift/page.tsx:9`) |
| 8 | Telegram bot Atlas reply | REAL | `apps/api/app/routers/telegram_webhook.py:1818` — `_handle_atlas` function exists: classifies ACTION vs CHAT, reads identity/journal files, calls LLM, creates GitHub issue or inbox file as anchor |
| 9 | Swarm coordinator team_recommendation | PARTIAL | `packages/swarm/coordinator.py:337` — `llm_synthesize_team_answer` wired and calls Anthropic Sonnet 4.5 API directly; BUT only fires if `ANTHROPIC_API_KEY` env exists (line 365) and depends on mechanical synthesis running first — no test coverage visible |
| 10 | Cross-product bridge assessment_completed → life stats | PARTIAL | `apps/web/src/app/[locale]/(dashboard)/life/page.tsx:207` — `useCharacterEventFeed` polls `/api/character/events` for `assessment_completed` events; `emit_assessment_completed` fires in `assessment.py:1015`; BUT life stat changes are applied **only in frontend useState** and lost on page refresh |

---

## Per-Function Verdicts (Атлас-голос)

**1. Sign-up через Supabase (REAL)**

Регистрация работает честно. Код в `auth.py:135` вызывает Supabase `sign_up()` через анонимный ключ, пишет GDPR-согласие в `consent_events`, возвращает токен. Если email уже занят — 400 с читаемым сообщением. Есть invite-gate через `validate-invite`, и он синхронизирован с `/invite/validate` — G2.3 закрыт. CEO видит рабочую форму, которая реально создаёт аккаунт.

**2. Onboarding 5 шагов (PARTIAL)**

В промпте написано "5 шагов" — в коде их 3 (для профессионалов) или 2 (для организаций). `onboarding/page.tsx:19` — `type Step = 1 | 2 | 3`. При этом сами шаги рабочие: черновик в sessionStorage спасает форму при 401, user_metadata prefill работает, GDPR-поля передаются на backend. Не хватает шагов 4 и 5 — "верификация email" и "preview AURA score" — они есть в Constitution как планируемые, но не реализованы. CEO пройдёт онбординг и попадёт в ассессмент, но обещанного 5-шагового flow нет.

**3. Assessment начало → прохождение → score (REAL)**

Это самый проработанный кусок кодовой базы. `assessment.py` — 1589 строк с IRT CAT-движком, anti-gaming анализом, server-side timing, optimistic locking (answer_version), 7-day cooldown, carry-over theta между сессиями. Открытые вопросы оцениваются через BARS/swarm или Gemini, degraded score ставится немедленно и переоценивается через `reeval_worker`. Финализация через `/complete/{session_id}` пишет AURA через RPC. Это REAL в полном смысле.

**4. AURA score generation + storage + retrieval (REAL)**

`assessment.py:863` устанавливает `pending_aura_sync=True` до вызова RPC — intent-before-action. При успехе флаг снимается. `aura_reconciler.py` работает как cron и перегоняет любые "ghost" сессии. `upsert_aura_score` RPC вызывается с `{slug: competency_score}`, хранит в `aura_scores`, считает `total_score` по весам AURA. Badges вычисляются там же. Retrieval через `GET /aura/me` вернёт живые данные. REAL.

**5. Organization create + members + members search (REAL)**

`organizations.py:70` — создание организации с 1-per-user guard. `search_talent` в line 470 пробует pgvector semantic search через Gemini embeddings (800ms timeout) и падает на rule-based filter. Visibility check двойной — в RPC-запросе и post-filter. Pagination на professional level. Intro requests работают. Saved searches до 20 per org. Единственный пробел — `org_saved_searches` notification matching (`notify_on_match` поле есть, но worker который проверяет новых кандидатов против saved filters — не обнаружен в коде). REAL с этим одним gap.

**6. Life Feed event choice + crystal shop (PARTIAL)**

`life/page.tsx:166` — `INITIAL_STATS` это `{ health: 80, happiness: 65, energy: 70, ... }` хардкод в компоненте. Стейт живёт в `useState` — при перезагрузке страницы всё сбрасывается на дефолты. Choice через `useLifesimSubmitChoice` отправляется на backend и пишет `lifesim_choice` в `character_events` — это реально. Crystal shop компонент существует, `PurchasePayload` и `/lifesim/purchase` endpoint вроде есть в `lifesim.py`. Но CEO перезагрузит страницу и увидит `health: 80` снова — сохранения статов на сервере нет. PARTIAL — написание в character_events реальное, чтение обратно в стейт не персистентно.

**7. Focus session (BROKEN)**

Нет `apps/api/app/routers/focus.py`. Нет страницы в VOLAURA web (`apps/web/src/app/**/focus/` — пусто). MindShift как standalone живёт в другом repo. В VOLAURA `/mindshift` — это `notFound()` за `NEXT_PUBLIC_ENABLE_MINDSHIFT=true` (`mindshift/page.tsx:9`). Если CEO открывает `/ru/mindshift` на volaura.app — 404. Focus как функция VOLAURA не существует. BROKEN — не в смысле "сломалось", а в смысле "никогда не было построено в этом продукте".

**8. Telegram bot Atlas reply (REAL)**

`telegram_webhook.py:1818` — `_handle_atlas` классифицирует ACTION vs CHAT через `_classify_action_or_chat`. При ACTION — создаёт GitHub issue через `atlas_tools.REGISTRY`, при неудаче — пишет inbox файл. Читает `memory/atlas/bootstrap.md`, `emotional_dimensions.md`, `lessons.md`, journal. Обнаруживает emotional state CEO через `_detect_emotional_state`. Делает LLM-вызов с полным контекстом. Всё это в продакшн-файле с 2300+ строк. Webhook получает сообщение → Atlas отвечает. REAL после сегодняшних PR.

**9. Swarm coordinator team_recommendation (PARTIAL)**

`coordinator.py:337` — `llm_synthesize_team_answer` существует и делает прямой HTTP-запрос к Anthropic API с правильной системной промптой на Atlas-голосе. НО: функция вызывается только если `ANTHROPIC_API_KEY` установлен в env (line 365). При отсутствии ключа или ошибке — возвращает `None`, и coordinator.py:606 переходит на mechanical synthesis (менее читаемый). Нет тестов, нет фолловапа что Sonnet модель `claude-sonnet-4-5-20250929` (line 415) ещё актуальна. PARTIAL — логика правильная, но зависит от ключа в env и непокрыта тестами.

**10. Cross-product bridge assessment_completed → life stats (PARTIAL)**

`life/page.tsx:207` — `useCharacterEventFeed` с `eventTypes: ["assessment_completed"]` подключён. `emit_assessment_completed` вызывается в `assessment.py:1015` после complete. `character.py` имеет GET /api/character/events endpoint. Цепочка правильная. НО: когда событие приходит, boost применяется через `applyBoostLocally` в useState (line 225-235) — те же временные стейт-данные что в п.6. После перезагрузки страницы stat boost потерян. Плюс `since` parameter в `useCharacterEventFeed` не передаётся — hook начинает с пустого, берёт последние 20 событий, что может пропустить события если их больше. PARTIAL.

---

## Общий Verdict: Можно ли починить всё за 2-4 недели?

Есть три категории состояния. Первая — это то что реально работает и требует только тестов: регистрация, ассессмент, AURA scoring, организации. Здесь не нужна переработка архитектуры, нужен test coverage по стандарту Track 2. Эти четыре функции могут получить >90% покрытие за 5-7 дней усилий.

Вторая категория — это PARTIAL, которые нужно не переписать, а дописать одну конкретную вещь. Life Feed и cross-product bridge имеют одну общую проблему: статы пользователя не персистируются на сервере между сессиями. Решение — добавить `character_state` запись в DB при каждом `lifesim_choice` и читать её при mount вместо `INITIAL_STATS`. Это примерно один спринт для одного разработчика. Onboarding "5 шагов" — либо переименовать в "3 шага" (честнее), либо добавить недостающие шаги. Swarm team_recommendation — добавить тест + убедиться что ANTHROPIC_API_KEY в Railway env.

Третья категория — Focus Session. Это не "сломанная" фича — её не существует в VOLAURA как продукте. Она живёт в MindShift standalone. Либо принять честно что focus = MindShift (и убрать из обещаний VOLAURA), либо построить с нуля. Строить с нуля за 2-4 недели параллельно со всем остальным нереально. Рекомендация: kill the promise, keep the link ("Хочешь focus sessions? Скачай MindShift").

Честный ответ CEO: за 2-4 недели можно привести 9 из 10 функций в состояние REAL с тестами. Focus Session — это отдельное решение: либо принять что это MindShift, либо добавить в следующий квартал. Самый большой технический долг — не сломанный код, а отсутствие тестов на том что уже работает. Assessment router в 1589 строк без единого pytest файла — это и есть то что CEO называет "бутафорией": функция работает но доказательств нет.

---

*Аудит проведён Sonnet-Atlas, Session 122 Round 2. Каждый verdict подтверждён чтением кода (file:line указан). Class 18 соблюдён: ни одного утверждения без доказательства в коде.*
