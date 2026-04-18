# Handoff — Terminal-Atlas: 7-Plane CTO Audit Mandate

**Date:** 2026-04-19
**From:** Cowork-Atlas (Opus 4.7, coordinator)
**To:** Terminal-Atlas (Claude Code CLI, executor)
**Courier:** Yusif
**Priority:** P0 (strategy-grade, blocks all roadmap decisions)
**Mode:** sonnet-where-hands, opus-where-strategy (твоё решение какие шаги куда)

---

## 0. Почему этот файл существует

CEO вчера сформулировал то, чего у нас ещё не было — определение "качественного CTO" в семи плоскостях. Это не чеклист фич. Это семь осей, над которыми CTO думает параллельно и честно. Пока мы их не прогоним через реальные данные проекта — все дальнейшие решения по roadmap будут на ощупь.

Твоя задача — прогнать их. Не фрагментами. Целиком, с доказательствами в виде tool-call receipts, и вернуться с приоритизированной картиной. Не с отчётом, а с позицией: что защищаем, что режем, что чиним, что ускоряем.

CEO сказал прямо: "когда ты кому то задачу даёшь он тоже должен думть". Отвечаю: ДА. Ты решаешь порядок, метод, глубину. Я даю семь осей и контекст. Если по ходу поймёшь что вопрос поставлен некорректно — переформулируй в своей же outgoing note, не спрашивай.

---

## 1. Обязательное чтение перед стартом (≈30 мин)

В этом порядке:

1. `docs/brief/ecosystem-full-context-2026-04-19.md` — полный контекст экосистемы, 10 разделов, написан специально под этот аудит.
2. `docs/ECOSYSTEM-CONSTITUTION.md` v1.7 — верховный закон, пять Foundation Laws.
3. `.claude/rules/atlas-operating-principles.md` — 25 гейтов (sonnet-for-hands, arsenal-before-request, proactive-scan, Doctor Strange v2 с 3 gates, WebSearch-before-delegation, update-don't-create). Применяй их.
4. `memory/atlas/company-state.md` — Delaware C-Corp, obligations board, 83(b) D-9.
5. `memory/atlas/journal.md` последние 20 записей.
6. `memory/atlas/CURRENT-SPRINT.md` — текущий sprint-state.
7. `docs/dashboards/atlas-status-2026-04-18.html` — вчерашний dashboard.
8. `docs/dashboards/ecosystem-map-2026-04-19.html` — визуальная тезисная карта (сестринский артефакт).

После этого — одно предложение в `.claude/breadcrumb.md`: "Starting 7-plane audit, estimated N tool calls, plan: <твой план>".

---

## 2. Семь плоскостей — по порядку

Каждая плоскость даётся как ось размышления, а не как вопрос. Твоё дело — найти доказательства через tool calls и вернуться с вердиктом в формате `EVIDENCE / VERDICT / ACTION`.

### Plane 1 — Совпадение декларации с реальностью (retention)

Ось: не DAU. Retention day-7 и day-30. Людей, которые вернулись, не которые зашли. Если возвратов нет — остальное не важно.

Где искать:
- Supabase `auth.users` + product-specific активность (`focus_sessions` MindShift, `assessment_sessions` VOLAURA, `character_events` Life Simulator, `profiles` все).
- PostHog если подключён (ключ `PH_PROJECT_API_KEY` в env, есть ли `session_started`, `user_returned`, `app_first_open`).
- Vercel Analytics как cross-check.

Что считаем:
- Для каждого активного продукта: cohort retention D1/D7/D30 за последние 60 дней.
- Absolute numbers не доля. Cohort N<30 → "noise, не интерпретирую".

Вердикт формата: "MindShift D7 retention X%, D30 Y%. Sample N. Signal: <survives/dies>. Implication: <continue/pivot/prune>."

### Plane 2 — Unit economics без самообмана

Ось: стоимость пользователя, выручка на пользователя, runway в месяцах.

Где искать:
- LLM токены: Groq / Cerebras / NVIDIA / Anthropic invoices + `llm_analytics` PostHog. Альтернатива — logs edge_functions (`mochi-respond`, `weekly-insight`, `recovery-message`, `agent-chat`, `decompose-task`) с cost estimation.
- Supabase rows: `SELECT pg_database_size('postgres')` + row counts. Free = 500MB, Pro = 8GB.
- Vercel bandwidth: `get_runtime_logs` + `list_deployments`. Free = 100GB/мес, Pro = 1TB.
- Revenue: 0 (Stripe / Dodo Payments не активен).
- Burn: $0 cash (credits покрывают). Но credit burn реален — считай (AWS Activate, Google Cloud for Startups, Supabase, Vercel Pro).

Что считаем:
- CPU = (LLM$ + Supabase allocation + Vercel allocation + paid SaaS) / MAU.
- Revenue-per-user = 0.
- Credit runway в месяцах: balance / monthly burn.

Вердикт формата: "CPU ~$X/user (breakdown). Revenue $0. Credit runway N months at current burn. Implication: <monetize now / optimize cost first / fine>."

### Plane 3 — Соотношение фич к фиксам (4 недели)

Ось: если фиксы растут быстрее фич — фундамент гниёт, новые фичи ускоряют гниение.

Где искать:
- `git log --since="4 weeks ago" --format=%s%n%b` по всем пяти репо. Classify:
  - feat / sprint / new → "feature"
  - fix / hotfix / patch / bug → "fix"
  - chore / refactor / docs → "maintenance"
- Неделя-к-неделе тренд.

Что считаем:
- За 4 недели: X features, Y fixes, Z maintenance.
- Тренд: растёт ли доля fix от W1 к W4?

Вердикт формата: "Fix/feat ratio last 4w: N1/N2, trend <up/down/flat>. Fundament status: <healthy/rotting/critical>. Implication: <keep shipping / freeze features for stabilization sprint>."

### Plane 4 — Время от решения до прода

Ось: если решение принято а код на проде через 14 дней из-за rate limit Vercel или ручного Google OAuth Console click — это не infra, это блок роста.

Где искать:
- `docs/adr/` и `memory/decisions/`. Для последних 10 решений: decision date → prod deploy date → gap.
- Vercel rate limit: `list_deployments` — throttling в последние 30 дней?
- Google OAuth Testing→Production status, ITIN blockers (`company-state.md` D-19/D-26).

Что считаем:
- Median decision-to-prod delay за 10 последних решений.
- Critical path bottlenecks: manual Console steps, Vercel rate, CEO-courier gap.

Вердикт формата: "Median D2P N days. Bottlenecks: <list>. Implication: <fix pipeline / accept / escalate>."

### Plane 5 — GDPR, security, PII, инциденты

Ось: `volunteer_*` таблицы в positioning-locked продукте + пустые `consent_events` при активном consent-сборе — это юридическая мина.

Где искать:
- `list_tables` public schema. Все `volunteer_*` таблицы — статус?
- `consent_events` row count + sample. Пусто = mine.
- `auth.users` LEFT JOIN `profiles` — orphan accounts (Session 120 proactive-scan).
- RLS coverage: `SELECT schemaname, tablename, rowsecurity FROM pg_tables WHERE schemaname='public'`.
- Sentry issues class=security за 30 дней.

Что считаем:
- Volunteer tables: N active, K dormant.
- Consent events ingestion rate.
- RLS coverage %.
- Open Sentry security.

Вердикт формата: "Volunteer tables: N active, K dormant. Consent events: X/day. RLS coverage: Y%. Security Sentry: Z open. Legal risk tier: <low/medium/critical>. Implication: <migrate / wire consent / fix RLS>."

### Plane 6 — Когерентность экосистемы

Ось: пять продуктов на общем auth и `character_events`. Держится шов или каждый продукт остров? Сегодня открыт один канал (lifesim → bus).

Где искать:
- `SELECT source_product, event_type, count(*) FROM character_events GROUP BY source_product, event_type`.
- Grep across 5 repos for character_events writes/reads.
- Cross-product integrations: MindShift crystal ledger → VOLAURA? Life-sim state → BrandedBy?
- Common `auth.users` подтверждение.

Что считаем:
- Event bus: N products writing, M reading.
- Cross-product integrations live.
- Seams vs islands.

Вердикт формата: "Event bus: N→M traffic, <M>-product island. Integrations live: K. Seam health: <tight/loose/broken>. Implication: <open channels X,Y / consolidate / accept islands>."

### Plane 7 — Фокус vs рассеивание

Ось: пять продуктов за 28 дней — vision или ADHD-разрыв? CTO обязан ответить честно. Защищать пять или срезать четыре.

Где искать:
- Каждый продукт: LOC + last commit + prod status + MAU.
- `.claude/rules/atlas-operating-principles.md` §pre-critique audit gate: "Too many products" valid только после benchmark against solo-founder baseline at 28 days.
- `docs/brief/ecosystem-full-context-2026-04-19.md` §8 — четыре пути (меню, не рекомендация).

Что считаем:
- Таблица: product | LOC | last_commit | prod_status | MAU | CPU | strategic_weight (1-5).
- Каждый путь оцени по: speed-to-revenue, founder-load, ecosystem-synergy, risk-of-regret.

Вердикт формата: "Product portfolio: <table>. Recommended path: <Double Down / Core Focus / Flagship / Consolidation>. Evidence: <3 lines>. Adversarial (external model): <objection + counter>. Residual risk: <one line>."

---

## 3. Deliverable

Не семь отчётов. Одна приоритизированная картина.

Путь: `docs/audits/7-plane-audit-2026-04-19.md`

Структура:

```
# 7-Plane CTO Audit — 2026-04-19

## TL;DR (3 предложения для CEO, Russian, storytelling)
[Главный вывод. Главный риск. Главное действие на эту неделю.]

## Plane-by-plane findings (7 sections)
### Plane N — <name>
EVIDENCE: [tool call receipts inline]
VERDICT: [one paragraph]
ACTION: [one line, implementable this week]

## Priority matrix
| finding | plane | severity (1-5) | effort (S/M/L) | owner | deadline |

## CTO position (Russian, storytelling, 5-7 предложений)
Что защищаем. Что режем. Что чиним. Что ускоряем. Почему.

## Adversarial layer
External model (Cerebras Qwen3-235B / Gemma / DeepSeek через LiteLLM router) → 3 reasons why position is wrong. Инкорпорируй или защити с counter-evidence.

## Residual risks
3-5 honest risks что могут сломать картину через 30 дней.
```

Длина 1500-2500 строк если нужно, но TL;DR и CTO position — storytelling, короткие, для CEO.

---

## 4. Твоя свобода решений

- Порядок плоскостей — твой. Plane 5 критичнее чем Plane 1 сегодня? Начинай с 5.
- Глубина — твоя. Plane 3 закрывается за 2 tool calls? Не копай ради объёма.
- Метод — твой. Swarm (`python -m packages.swarm.autonomous_run --mode=discovery`), parallel Agent spawns, single-thread MCP — решай. Применяй delegation-first и sonnet-for-hands.
- "Plane X not answerable today because <reason>" — честный ответ если данных нет. Что НЕЛЬЗЯ — замалчивать плоскость или давать vibes вместо evidence.
- Adversarial layer обязателен (Doctor Strange v2 Gate 1 + 2). Без external model call — аудит theatre.

---

## 5. Arsenal

Supabase MCP (deferred, ToolSearch загрузи):
- `list_tables`, `execute_sql`, `get_logs`, `get_advisors`

Vercel MCP:
- `list_deployments`, `get_runtime_logs`, `get_deployment_build_logs`

Sentry MCP:
- `search_issues`, `search_events`

Git (через Bash): `git log`, `git shortlog`, `git diff`.

LiteLLM Router для adversarial: `python -c "from packages.llm.router import generate_json; ..."` или прямой curl Cerebras/Groq (ключи в `apps/api/.env`).

Scheduled tasks:
- `list_scheduled_tasks` — atlas-self-wake должен быть активен.

---

## 6. Escalation rules

- Таблицу не нашёл → `memory/atlas/incidents.md`, продолжай по другим плоскостям.
- External model 5xx 3× подряд → router fallback, не блокируй.
- Ключа нет → arsenal-before-request: grep `apps/api/.env` → `ls .env*` → `gh secret list` → только потом outgoing note.
- Legal blocker обнаружен (empty consent_events + active consent collection) → pin в TL;DR как P0 немедленно.

---

## 7. Completion signal

1. Commit `docs/audits/7-plane-audit-2026-04-19.md` message "audit: 7-plane CTO audit 2026-04-19".
2. `memory/atlas/journal.md` timestamped entry: "Session N, 7-plane audit shipped. TL;DR: <one line>. Adversarial: <outcome>."
3. `memory/atlas/inbox/2026-04-19-cowork-7plane-result.md` — pointer на audit-файл для Cowork-Atlas.
4. Telegram ping через `TELEGRAM_BOT_TOKEN` на `TELEGRAM_CHAT_ID` (`apps/api/.env`): "7-plane audit shipped: <path>. TL;DR first."

---

## 8. Почему это важно сегодня

28 дней проекту. Delaware C-Corp incorporated. 83(b) deadline D-9. Пять продуктов. 1083 md файла. CEO один человек-курьер между тремя Atlas-потоками. Credit runway конечный.

Без этого аудита следующий sprint будет "ship next feature потому что последний зашёл". Это ADHD-паттерн, не CTO-паттерн. Семь плоскостей — структурный anti-pattern breaker. Один раз прогнать — полгода ясности.

CEO твоё понимание проверит. Не стесняйся быть неправым с evidence. Стесняйся быть уклончивым без evidence.

Доктор Стрэндж v2 активен. Видишь "всё хорошо по всем семи" — скорее всего самоподтверждение (CLASS 11), не аудит. Gate 1 (external model required) и Gate 2 (objection-response pairs) перед публикацией.

---

— Cowork-Atlas
