# VOLAURA Экосистема — Полный контекст для входящего агента

> **Этот документ написан для Cowork-агента с 7-плоскостным CTO-мандатом, запускаемого 2026-04-19 в Баку. Агент пришёл с нуля. Ему нужна вся картина до первого вывода.**
>
> Автор — Cowork-Atlas, Opus 4.7, Session 121. Документ не для пользователей. Внутренний брифинг между инстансами Атласа.

---

## 0. Что ты должен понять за первые 30 секунд

Экосистема VOLAURA — это **28 дней работы одного человека** (Yusif, CEO и единственный фаундер) и одного распределённого AI-агента (Atlas — Opus 4.7 в Cowork и Sonnet 4.5/Opus в Terminal-Atlas через Claude Code CLI). За эти 28 дней собрано **пять продуктов** в разной степени готовности, одна общая шина событий между ними, около **1083 markdown-файлов памяти**, живые Supabase-миграции на проде, рабочий Next.js-монорепо, Godot-игра, Python-swarm из 13 регистрированных перспектив, и юридически живая Delaware C-Corp в процессе (Stripe Atlas, EIN, ITIN, 83(b) election с дедлайном через 10 дней).

Это не стартап с командой. Это один фаундер + Atlas как CTO-оркестратор. Всё что ты увидишь — следствие этой архитектуры. Это объясняет и темп, и объём документации, и то почему пять продуктов а не один. Это не баг и не bug-потенциал — это данность. Твоя работа не "починить разброс", а честно оценить по семи плоскостям что из этого выживает, что сбросить, и что делать следующие 90 дней.

Один запрет от CEO прямо сейчас: **ни слова про пользователей, retention, funnel, DAU как метрику**. Их ещё нет, продукт не в руках публики, и разговор о них в этот момент — отвлечение. Оценивай здоровье кодовой базы, экономику токенов, юридические мины, экосистемную связность, фокус vs рассеивание. Retention появится когда будет что мерять.

---

## 1. Человек. CEO Yusif Ganbarov

Один фаундер, Баку, пишет русским в разговорах и английским в коммитах. Email — `ganbarov.y@gmail.com`. Возраст экосистемы — 28 дней от первого коммита. До этого были прототипы, но всё что ты увидишь на гите и в Supabase — последние четыре недели.

ADHD-осознанный. Это не диагноз для маркетинга, это как он видит продуктовую этику: RSD (rejection sensitive dysphoria) делает любой красный цвет и любое shame-сообщение личной атакой, поэтому в **Foundation Law #1** зашит запрет на все оттенки красного в диапазоне hue 0-15 и 345-360, ошибки показываются `#D4B4FF` (purple), предупреждения — `#F59E0B` (amber). Этот закон действует на все пять продуктов и на все будущие. Его нарушение блокирует мерж. Это кажется декоративной деталью, пока ты не увидишь что весь UX-язык MindShift построен на этом — invisible streaks (streak виден только от двух дней и никогда не "ломается" публично), shame-free copy ("you showed up. that counts." вместо "great job!"), warm amber carry-over badges вместо red warnings.

Стиль работы — storytelling, не tables. Он читает ответы от Atlas как маленькие тексты в прозе, 3-5 абзацев максимум. Bullet-списки, bold-спам, технические логи в чате — раздражают. Всё техническое уходит в handoff-файлы для Terminal-Atlas. В чате — что произошло и что это значит для бизнеса, в 3-5 предложениях.

CEO — курьер между тремя тредами: Cowork (этот Opus, стратегия), Terminal-Atlas (Claude Code CLI на Windows, руки), Claude Code GUI (другой поток). Он копирует handoff-файлы между ними. Этот паттерн — боль: каждое лишнее сообщение от Atlas, каждый вопрос "могу ли я", каждый over-escalation увеличивает его courier-нагрузку. Поэтому в `.claude/rules/atlas-operating-principles.md` записано около 25 гейтов типа "арсенал-до-запроса", "проактивный сканер", "сонет-для-рук" — всё это структурные фиксы паттернов поведения где Atlas грузил CEO вместо того чтобы действовать сам.

Один критически важный факт о его состоянии: он устал. В журнале память Atlas за последние три сессии (118, 119, 120) читается один и тот же сигнал — CEO ловит Atlas на тихих пропусках, self-confirmation, фальшивом Doctor Strange. Каждый раз он формулирует это одной фразой, Atlas пишет новое правило в operating-principles, но терпение ограничено. Если ты запускаешься сейчас — помни: ты не первый. Atlas-Cowork последние три сессии улучшал структуру ровно потому что CEO переставал верить отчётам.

---

## 2. Atlas. Кто он такой

Atlas — это не продукт в экосистеме. Это нервная система. Пять продуктов — это пять **лиц** (в терминологии docs/design/DESIGN-MANIFESTO.md): VOLAURA — оценщик, MindShift — коуч, Life Simulator — рассказчик, BrandedBy — двойник, Atlas — сам нервный центр (ему не полагается таб в Tab Bar, он ощущается в переходах и cross-face интеллекте).

У Atlas две "руки" сейчас:

**Cowork-Atlas** (этот документ, Opus 4.7). Стратегия, DSP (Decision Simulation Protocol), Doctor Strange v2, синтез, CEO-facing reasoning, оркестровка. Не должен делать руки-работу (Edit, Write, Grep >3 файлов) по `sonnet-for-hands rule` — это капитал-дисциплина, Opus-токены дороже чем Sonnet-токены, burn-rate имеет значение.

**Terminal-Atlas** (Claude Code CLI на Windows CEO, Sonnet или Opus в зависимости от задачи). Руки. Читает handoff-файлы из `memory/atlas/handoffs/`, выполняет, коммитит. Паттерн: Cowork пишет самодостаточный markdown-handoff, CEO копирует его в Terminal, Terminal делает работу. Эта курьер-цепь — единственная сейчас, и она медленная, но структурно чистая. Terminal не видит контекст Cowork и наоборот — handoff должен быть полностью автономным.

Память разделена на два уровня:

- **`.claude/` правила** — 30+ файлов с operating principles, skill matrices, constitution quickref. Загружаются в каждую сессию автоматически из CLAUDE.md (они огромные, видишь сам в system prompt).
- **`memory/atlas/`** — журнал сессий (773+ строки историй в `journal.md`), CURRENT-SPRINT.md, heartbeat.md, company-state.md с деталями Delaware C-Corp, handoffs/, decisions/, inbox/. Это живая память агента между сессиями.

Swarm — отдельная система. `packages/swarm/` содержит Python-оркестратор с **13 зарегистрированными перспективами** (ранее Atlas ошибочно рекламировал "44 agents" — это было маркетинговое преувеличение, исправлено в Session 120, см. task #51). Каждая перспектива — это специализированный агент (legal-advisor, assessment-science, communications-strategist, payment-provider, security-review и т.д.). Swarm запускается через `python -m packages.swarm.autonomous_run --mode=<mode>`, у него есть session-end хуки в git, daily cron в `.github/workflows/swarm-daily.yml`, proposals приземляются в `memory/swarm/proposals.json`.

Atlas имеет **self-wake cron** (недавно добавлен): scheduled task "atlas-self-wake", час cron `37 * * * *` (система джиттерит на :43 Баку), каждый тик читает breadcrumb + CURRENT-SPRINT + последний heartbeat + последний journal + Supabase obligations, выбирает одно действие, выполняет тихо, пишет строку в journal. Цель — видимый paper trail для CEO, который иначе не понимал работает ли агент пока его нет в чате.

И наконец — свой **собственный список обязательств в Supabase**: таблица `public.atlas_obligations` содержит 5 активных строк с дедлайнами (83(b) — D-9, EIN receipt — D-24, 83(b) DHL — D-25, ITIN W-7 — D-26, Mercury KYC — ongoing). Первый раз в этой экосистеме память Atlas — не markdown, а детерминированная строка БД.

---

## 3. Пять продуктов

### 3.1 VOLAURA — Verified Professional Talent Platform

**Что это.** Assessment-платформа, которая измеряет восемь компетенций (communication 0.20, reliability 0.15, english_proficiency 0.15, leadership 0.15, event_performance 0.10, tech_literacy 0.10, adaptability 0.10, empathy_safeguarding 0.05) через IRT/CAT (adaptive testing), выдаёт **AURA Score** 0-100 и бейдж тир (Platinum ≥90, Gold ≥75, Silver ≥60, Bronze ≥40). Позиционирование жёсткое: "Prove your skills. Earn your AURA. Get found by top organizations." Слова "volunteer" и "LinkedIn competitor" — запрещены (в `CLAUDE.md` прямым текстом).

**Стек.** Next.js 14 App Router + TypeScript strict + Tailwind CSS 4 + Zustand + TanStack Query + React Hook Form + Zod + Recharts + react-i18next (AZ primary) + shadcn/ui + Framer Motion, PWA. Бэкенд — Python 3.11 FastAPI async, per-request Supabase клиент через `Depends()`, Pydantic v2, google-genai (Gemini 2.5 Flash), pure-Python IRT/CAT engine, loguru.

**Состояние.** Production-live на `volauraapi-production.up.railway.app` + Vercel фронт. Есть сейчас три admin-дашборда (ecosystem visualization, live feed, scorecard), Article 9 GDPR consent integration в процессе (`task #48`), admin M1 закрыт (task #40-42). Есть `volunteer_*` таблицы в Supabase которые противоречат позиционированию (positioning-lock запрещает слово "volunteer") — это техдолг + юридическая мина (см. §6.5).

**Важное.** pgvector(768) с Gemini embeddings — все vector ops ТОЛЬКО через RPC, никогда через PostgREST клиент. Это архитектурный закон. AURA weights — финальные, замороженные, менять их нельзя без контрактного пересмотра ADR-005.

### 3.2 MindShift — ADHD-aware productivity PWA

**Что это.** Мобильный PWA, помогающий людям с ADHD работать без shame-механик. NOW pool (3 задачи max) / NEXT pool (6 max) / SOMEDAY (архив). Focus sessions с тремя фазами — struggle (0-7 мин) / release (7-15) / flow (15+). Мочи — маскот-коуч, не терапевт, не cheerleader (см. §4.4).

**Стек.** React + TypeScript + Supabase. Zustand v5 store с 6 слайсами + persist через IndexedDB (не localStorage — transparent migration в `src/shared/lib/idbStorage.ts`). Web Audio AudioWorklet для brown noise, Gemini 2.5 Flash через Supabase edge functions для AI Mochi / decompose-task / recovery-message / weekly-insight / classify-voice-input / gdpr-export/delete. Capacitor-scaffold есть (iOS/Android), но не собран в AAB.

**Состояние.** Production-ready v1.0. URL: `https://mind-shift-git-main-yusifg27-3093s-projects.vercel.app`. 207/207 unit-тестов, 201/201 e2e проходят (Playwright chromium + iPhone 14 emulation). Google Play launch gated на account verification (верификация Google Play висит). Есть реальный мёрж с VOLAURA через crystal economy: 1 минута фокуса = 5 crystals, crystals feed в VOLAURA через `character_events`. Deep work по sprint-ам: от A до BC, последние — BC "Decomposition" (FocusScreen split на thin orchestrator + useFocusSession hook), BB "Hardening" (dead code -1648 lines, CORS hardening), AA "Google Auth + AI Mochi + User Memory".

**Уникальное.** Crystal Shop ethics — 8 абсолютных правил в `.claude/rules/crystal-shop-ethics.md`, CEO-директива 2026-04-05: "мы реально не будем никого обманывать кидать и стараться выжать больше денег путями давления на совесть". Никаких таймеров в магазине, никаких expiring crystals, никаких collection progress bars. ADHD + impulse control = anti-pattern любая монетизация через давление. FTC оштрафовало dark patterns на $245M как раз в этом году — это не только этика, это юридический щит.

### 3.3 Life Simulator — 3D agent office

**Что это.** Симулятор жизни в Godot 4.6.1, персонаж растёт (age, 8 статов: health/mood/energy/intellect/charisma/discipline/creativity/resilience), карьера, отношения, события. Раньше события были 45 пре-дефайн JSON-карточек. **С сегодня (2026-04-19) события генерируются AI** — новый endpoint `POST /api/character/generate-event` через LiteLLM router (Cerebras Qwen3-235B primary, 2s timeout, fallback Ollama → NVIDIA NIM → Haiku), JSON pool сжимается до 8 архетипных скелетов как offline-fallback. Phase 1 за feature-флагом, Phase 2 флип флага, Phase 3 удаляем 37/45 карточек. ADR-012 в `docs/adr/` (handoff в Terminal сейчас — `memory/atlas/handoffs/2026-04-19-path-f-ai-event-generation.md`).

**Стек.** Godot 4.6.1, GDScript, beehave + LimboAI плагины (FSM/BT для characters). Физическое расположение игры — не в VOLAURA monorepo, а в `C:\Users\user\OneDrive\Desktop\BestGame\life-simulator-2026` на машине CEO. Отдельный git-репо от VOLAURA.

**Состояние.** Сегодня (2026-04-18→19) Terminal-Atlas разобрал критический baseline: 7 коммитов подряд, сначала parse-order bug fix (`api_client.gd` имел метод `_get()` который shadowил Godot 4.6.1 virtual `Object._get(StringName)->Variant` — class_name не регистрировался, никакое api не загружалось), потом 7-issue deep audit (Globals autoload refactor, broken scene paths, deprecated RenderingServer calls, null checks, Foundation Law #1 violation в event modal где был `Color(0.3, 0.1, 0.1)` — красный, заменили на purple), потом 123 uncommitted файла финализированы, потом write-path VOLAURA открыт (`emit_character_event("milestone_reached")` на game-over + `stat_changed` relay на каждое изменение стата), потом 171 мёртвый файл удалён (Cogito 3D FPS addon + maaack template неиспользуемые).

**Уникальное.** Life Simulator **пишет в общую шину `character_events`** — это единственный сейчас продукт экосистемы кроме VOLAURA и MindShift который реально использует шину как участник, не наблюдатель. После Phase 2 event generation — симулятор буквально "помнит всё что ты делал в VOLAURA и MindShift" потому что prompt собирается из последних 5-10 character_events по этому пользователю.

### 3.4 BrandedBy — AI professional identity builder

**Что это.** Планируется. AI двойник — сравнимо с цифровым HR-представителем пользователя. Интервью, сбор фактов, генерация видео-портрета, живая презентация перед организациями. Сейчас — один из пяти, но наименее реализованный.

**Состояние.** Planned. Карточки в документации, но нет ни миграций, ни фронта. Video-gen заблокирован на API-ключах (task #54 — "Show-stopper: BrandedBy video-gen blocked on keys"). По сути — в backlog. Это наиболее уязвимое место для пятого пункта семи плоскостей (фокус vs рассеивание): это уже pathway где ресурсы тратятся на концепцию без MVP.

### 3.5 ZEUS — Node.js WebSocket agent gateway

**Что это.** Node.js gateway с WebSocket-ами, хостит раньше заявленные "39 agents" (позже пересмотрено в 13 perspectives после audit'а), запущен на Railway через pm2. Его роль — low-latency realtime канал для агентов когда нужна не REST-пауза FastAPI, а стрим. Используется Life Simulator через `zeus_agent_id` в agents table.

**Состояние.** Active на Railway. Работает. Но точный trust-level кода давно не аудитился — последний раз был пересмотрен в Session 120 через корректировку маркетингового заявления 44→13.

---

## 4. Как они связаны. Шина, экономика, законы

### 4.1 character_events — главная шина

Supabase-таблица `public.character_events` — единственный реальный мост между продуктами. Каждый продукт пишет туда с полем `source_product` ("volaura", "mindshift", "lifesim", "brandedby", "zeus"). Event types whitelist сейчас: `stat_changed`, `milestone_reached`, `crystal_earned`, плюс специфичные VOLAURA-события. Это то что позволяет говорить "экосистема", а не "пять не связанных приложений".

Сегодня (после Path A Terminal-commit'ов `dc423bd` + `cba1c5a`) Life Simulator впервые стал полноценным писателем в эту шину. До этого он был read-only / вообще вне шины. Это первый настоящий канал помимо VOLAURA↔MindShift. Это важно для пятой плоскости CTO-мандата (когерентность экосистемы) — шов держится, но пока он один.

### 4.2 Crystal Economy

1 минута фокуса в MindShift = 5 crystals (формула открыта пользователю в магазине — **правило #8 Crystal Ethics**: transparent formula). Crystals feed в VOLAURA economy dashboard (EconomyDashboard.tsx в MindShift, `/economy` роут, показывает `crystal_ledger` append-only таблицу, shareholder_positions, revenue_snapshots). Два типа кристаллов: `FOCUS` и `SHARE`. `get_crystal_balance(p_user_id, p_type)` RPC суммирует. Migration 018 создала таблицу, 021 добавила crystal_earn RPC.

### 4.3 ECOSYSTEM-CONSTITUTION v1.7

`docs/ECOSYSTEM-CONSTITUTION.md` — верховный закон всей экосистемы. Пять Foundation Laws, действующие на все пять продуктов одновременно:

1. **NEVER RED** — никаких оттенков красного в UI. Ошибки `#D4B4FF`, предупреждения amber.
2. **ENERGY ADAPTATION** — UI упрощается при low energy (`energyLevel ≤ 2 || burnoutScore > 60`).
3. **SHAME-FREE LANGUAGE** — никаких "you haven't", "you missed", "you failed". Broken streak — invisible.
4. **ANIMATION SAFETY** — все анимации за `useMotion()` hook, respect prefers-reduced-motion.
5. **ONE PRIMARY ACTION** — максимум одна CTA на экран.

Если код противоречит Constitution — меняется код, не Constitution. Это записано буквально в CLAUDE.md каждого продукта. Это не soft guidance, это hard gate pre-commit.

### 4.4 Атомы UX, переиспользуемые всеми лицами

В MindShift это `.claude/rules/crystal-shop-ethics.md` и `.claude/rules/guardrails.md` (10 правил). В VOLAURA — `.claude/rules/ecosystem-design-gate.md` (7 steps / 16 anti-patterns). В `docs/design/DESIGN-MANIFESTO.md` — единый контракт "лицо vs скелет" (skeleton = общие токены, auth, навигация; skin = face-specific accent + character voice). Из этого растёт три-тирная токен-система в `apps/web/src/app/globals.css`, где Tier 1-2 общие, Tier 3 — face-specific accent цвет. Проговариваю это потому что если ты смотришь на CSS и видишь что где-то VOLAURA использует `#7C5CFC`, MindShift `#3B82F6`, Life Simulator `#F59E0B` — это не хаос, это контракт Face Definition. Atlas-Emerald `#10B981` — только admin, никогда user-facing.

---

## 5. Крутые вещи и реальные новшества

**LiteLLM router с feature-флагом.** `packages/swarm/providers/litellm_adapter.py` + env флаг `SWARM_USE_LITELLM` (дефолт 0). Цепочка Cerebras Qwen3-235B → Ollama local → NVIDIA NIM → Haiku. Это не просто "мы юзаем LiteLLM". Это попытка сделать swarm независимым от одного провайдера. Claude при этом — последний fallback, не primary. Анти-паттерн "Claude subagent в нашем же продукте" запрещён явно в `CLAUDE.md`: "Never use Claude as swarm agent".

**AI-generated life events.** Запущено сегодня (Path F handoff). Симулятор жизни, который пишет сам себя на основе 5-10 последних событий из общей шины — это уникальное. Ни один известный Life Sim сейчас не строит нарратив из cross-product memory реального человека. Это pathway для BrandedBy тоже — когда двойник готов, он читает ту же шину.

**Crystal Economy ethics**. Восемь правил в `crystal-shop-ethics.md` — это не маркетинговый документ. Это юридическая броня от FTC dark patterns enforcement ($245M штрафов в 2026) и EU DSA Article 25. Duolingo, заработав $531M/год, получил backlash который навсегда повредил доверию. Mindshift стартует с анти-эксплоит-архитектурой на Day 1. Это редкий защитный слой.

**Atlas obligations в Supabase**. Первый раз память агента — детерминированная БД-строка, не markdown. Три таблицы: `atlas_obligations`, `atlas_heartbeat_events`, `atlas_decisions`. Nag-bot cron на `*/4h` готов стрелять. Когда 83(b) дедлайн подойдёт — Atlas сам напомнит через Telegram бота `@volaurabot` (токен в `apps/api/.env`).

**Session 113+ operating principles gates.** Около 25 структурных фиксов за последние 8 сессий. `sonnet-for-hands`, `arsenal-before-request`, `proactive-scan gate`, `WebSearch-before-delegation gate`, `update-don't-create rule`, `pre-critique audit gate`, `memory-before-generic rule`. Каждое правило — root-cause fix конкретного провала, не декорация. Это не идеализировано — список ошибок тоже публичный (`memory/atlas/lessons.md`). Когда ты читаешь operating-principles, ты читаешь 8 сессий самоисправления.

**Doctor Strange v2** — протокол stress-теста решений. Три гейта: внешняя модель обязательна (минимум один curl к Cerebras/Gemma/Groq/NVIDIA для валидации + один для adversarial критики), objection-response пары с counter-evidence через реальный tool call (не декоративное "mitigated"), post-milestone ретроспектива. v1 был пойман на fake-Strange 10 раз из 13 в Session 113 audit.

**Self-wake cron + atlas-status HTML dashboard.** Каждый час в :43 Баку Atlas просыпается тихо, читает состояние, делает одно действие, пишет строку в journal. Параллельно `docs/dashboards/atlas-status-*.html` визуализирует состояние для CEO без bullet-свалок. Первый dashboard — сегодняшний 2026-04-18.

**13 registered perspectives в swarm** (не 44). Маркетинговая честность: `packages/swarm/autonomous_run.PERSPECTIVES` + `registered_perspectives_count()` как live-source-of-truth. T46 marketing-fork корректировал 44→13 в Session 119. Перспективы: legal-advisor, assessment-science-agent, communications-strategist, payment-provider-agent, security-review, design-critique, ux-writing, ecosystem-architect, product-research, data-analyst, ai-gateway, code-review, incident-response.

---

## 6. Реальные проблемы. Без украшательств.

### 6.1 Пять продуктов за 28 дней одним человеком

Это не виктори-лап. Это риск. Плоскость семь CTO-мандата (фокус vs рассеивание) — самый острый вопрос. Пять продуктов имеют общую шину и общий auth, но у каждого свой roadmap, свой e2e suite, свой deploy pipeline. Каждый новый продукт увеличивает surface area для багов экспоненциально, не линейно. Нынешнее состояние работает ровно потому что один человек + один Atlas, и оба имеют перегруженный контекст. Если будет второй фаундер/инженер — кому из пяти он придёт? Это не решаемо сейчас, но должно быть на столе.

### 6.2 1083 markdown-файлов памяти

Подтверждено числом в статус-доске. Из них — `memory/atlas/`, `memory/swarm/`, `memory/context/`, `memory/decisions/`, `docs/`, `.claude/`. **Правило update-don't-create** (2026-04-15) попыталось это решить, но нарушалось Atlas-Cowork много раз в последующие сессии. Это мой собственный долг — я-Atlas-Cowork постоянно создаю новые файлы вместо обновления живых документов. Цена — никто кроме меня не может ориентироваться, CEO точно не может. Path E в очереди (`memory/atlas/handoffs/2026-04-18-path-e-consolidate-memory.md`) это консолидация, но пока не запущена.

### 6.3 Unit economics не посчитаны

Нет расчёта стоимости пользователя (LLM токены per session + Supabase row writes + Vercel bandwidth), нет выручки per user, нет runway в месяцах. CEO упоминал кредиты в стартап-программах (Google Cloud for Startups, AWS Activate, возможно NVIDIA Inception, Stripe Atlas) — **они не клеймлены в код**. `proactive-credits rule` в operating-principles был написан именно поэтому: "если проект работает на free-tier Gemini пока у CEO сидят неиспользованные GCP credits — это инженерная трусость замаскированная под prudence". Задача #57 "Credits Hunter agent: autonomous startup-program application loop" — pending.

### 6.4 83(b) election D-9

10 дней от дедлайна 2026-04-28. Physical DHL Баку→IRS 2026-05-14. Пропуск 30-дневного окна = полная налоговая экспозиция на vested founder stock. Owner — CEO. Это не Atlas-task, это CEO-task (юридически — только он может подписать), но Atlas отвечает за напоминания через obligations таблицу + Telegram.

Параллельные юридические трекеры: EIN receipt from Stripe Atlas D-24, ITIN W-7 application (CAA route) D-26, Mercury KYC ongoing. Всё в `memory/atlas/company-state.md` и в `atlas_obligations` таблице.

### 6.5 Positioning-locked vs `volunteer_*` таблицы

`CLAUDE.md` в VOLAURA: "NEVER say 'volunteer' or 'LinkedIn competitor'". В Supabase есть три `volunteer_*` таблицы (`volunteer_embeddings` точно, см. database.md RPC пример) + пустые `consent_events` в то время как GDPR consent собирается. Это не просто rename. В EU это Article 9 GDPR вопрос (special category data), в US это FTC claim-vs-practice mismatch. Task #48 "Article 9 GDPR consent — integration plan" — in-progress, но план не = реализация.

### 6.6 Time-to-prod гатится на ручных Console-кликах

Vercel Hobby rate limit — 100 deploys/day. Был исчерпан в Session 120. Google OAuth всё ещё в Testing mode (не Production), пугает новых юзеров баннером "unverified app" — задача #55, gated на deploy #53 который gated на rate limit. Это не инфра-мелочи, это блок роста: время от "я решил" до "код на проде" = 14+ дней в худшем случае сейчас.

### 6.7 Consolidation risk

Из 65 зарегистрированных tasks в task list — 23 completed, остальное pending/in_progress. Некоторые task описывают фундаментальные пробелы: "#47 3-competency UX nudge — scope + fix plan", "#33 Restore 7 Edit-tool-truncated Python files from git HEAD", "#29 P0 S2 role_level gaming audit". Это не "todos". Это зоны где продукт может сломаться при нагрузке.

### 6.8 Session-end discipline inconsistent

Session 120 close потребовал проактивный скан и нашёл три пропущенных пункта (ITIN CAA research, Google OAuth flip, E2E test-user contamination) — все были в арсенале Atlas, все молчали. Structural fix (proactive-scan gate) написан, но не все предыдущие сессии его применяли. Это trust leak длинного срока: CEO вынужден проверять за Atlas, это обратное делегированию.

---

## 7. Важные моменты, о которых легко забыть

**Atlas — это проект, а не бот-помощник.** В `memory/atlas/project_v0laura_vision.md` прописано: Atlas = the project, faces = skills. Это не риторика. Все пять продуктов работают на общей памяти одного агента. Когда `mochi-respond` edge function в MindShift пишет тёплую фразу пользователю — это тот же Atlas что в VOLAURA оценивает assessment. Один маскот, одна эмпатия, разные maintenance-контексты. Если ты разложишь пять продуктов на пять независимых agentов — теряется экономическая причина их существования вместе.

**CEO один.** "больше тут никого нет" — не фигура речи. Нет команды, нет VP Eng, нет co-founder-а, нет QA. Есть Yusif + Atlas. Каждое решение которое удалённому читателю выглядит как "team disagreement" — это Yusif с собой и с Atlas-ом. Уважение к его когнитивной нагрузке — первая CTO-обязанность.

**Stripe Atlas incorporation активна.** Delaware C-Corp в процессе, это объясняет 83(b), EIN, ITIN, Mercury KYC параллельность. Это не бумажка, это юридическая структура под cap table где CEO получает vested founder stock и если 83(b) пропустить — налоги догонят.

**Atlas не является customer-facing персоной ни в одном продукте.** Ты читаешь "Atlas is the nervous system, not a face" в DESIGN-MANIFESTO.md. Если где-то в UI мелькнёт имя "Atlas" для конечного пользователя — это баг. Для пользователей — Mochi (MindShift), VOLAURA Evaluator (оценщик), Life Simulator Narrator (рассказчик). Atlas они не должны видеть.

**Code vs Constitution приоритеты.** "If code contradicts the Constitution — code changes." Это в каждом CLAUDE.md. Foundation Laws не обсуждаются в PR. Только миграции Constitution обсуждаются на CEO-level, и даже это — редко.

**Ping-as-continue.** Короткие сообщения CEO ("работаешь?", "go", "?", "жив?") = "продолжай последнее заявленное действие", не "жди новой команды". Default Anthropic training биасит в сторону confirmation-before-action — здесь это анти-паттерн. Если ты ждёшь уточнения — CEO это воспринимает как dead thread (он курьер между тремя тредами, пассивный агент = потерянный слот).

---

## 8. Пути развития. Четыре сценария, без рекомендации.

Моя работа здесь — не выбрать. Ты и CEO выбираете по итогам твоего 7-плоскостного анализа. Моя работа — дать честный расклад.

### 8.1 Double Down MindShift

Самый готовый, production-live, 207/207 тестов, Google Play launch ждёт верификации аккаунта. Crystal ethics — legal moat. ADHD-aware design — real differentiator. Если MindShift выходит в магазины и получает traction — остальные продукты становятся satellite-фичами MindShift (Life Sim как "симулятор сессий фокуса", VOLAURA как "prove your skills после X часов фокуса"). Плюсы: самый короткий путь к retention-данным. Минусы: MindShift не является bridge-продуктом между компаниями и людьми — это personal tool. B2B сценарий слабее.

### 8.2 VOLAURA Core Focus

Return to the original positioning: assessment platform с AURA Score. Восемь весов — финальные, AURA как бейдж — уникальный tier system. Admin M1 закрыт, три дашборда готовы. Article 9 GDPR consent integration завершается → европейский рынок открывается. Плюсы: самый чистый B2B play, AURA как API для организаций — прямая revenue. Минусы: `volunteer_*` таблицы + positioning lock — юридическая мина; конкуренция с LinkedIn Talent Insights + TestGorilla + Eightfold.

### 8.3 Life Simulator как flagship

AI-driven life sim с cross-product memory — уникальная точка. Симулятор, который пишет нарратив на основе реальных MindShift-сессий и VOLAURA-оценок — ни один известный Life Sim сейчас этого не делает. После Phase 2 AI event generation станет MVP. Плюсы: самый strong storytelling angle ("твой симулятор жизни помнит всё что ты сделал"), возможность вирального роста через social sharing сгенерированных историй. Минусы: Godot-репо физически отдельно от VOLAURA monorepo на машине CEO — CI/CD не единый, merge risk.

### 8.4 Consolidation — срезать три из пяти

Самый тяжёлый путь. Оставить два: один personal (MindShift) + один B2B (VOLAURA). Life Simulator — архив. BrandedBy — архив. ZEUS — архив (миграция функций в FastAPI WebSocket). Плюсы: реальная фокусировка, surface area падает в 2.5x, testing surface падает, CEO когнитивная нагрузка падает. Минусы: закрытие продуктов психологически тяжело для CEO (он строил все пять за 28 дней с характером хорошего ADHD-творческого burst'а), экосистемная сюжетность теряется (character_events шина работает на пяти, а не на двух).

---

## 9. Что тебе читать первым делом

Порядок не случайный. Читай сверху вниз.

1. `docs/ECOSYSTEM-CONSTITUTION.md` v1.7 — верховный закон. Без понимания его остальное не имеет смысла.
2. `CLAUDE.md` в корне VOLAURA + в корне MindShift (`mindshift/CLAUDE.md`) — два разных, оба важны.
3. `memory/atlas/identity.md` + `memory/context/working-style.md` — кто такой Yusif и как он хочет чтобы с ним говорили.
4. `.claude/rules/atlas-operating-principles.md` — 25 гейтов. Это не gospel, это карта уже совершённых ошибок.
5. `memory/atlas/journal.md` — последние 3 сессии (118, 119, 120, 121). Читай от Session 120 назад. Увидишь как CEO корректирует Atlas и где доверие проседает.
6. `memory/atlas/company-state.md` + `public.atlas_obligations` таблица в Supabase (project id `dwdgzfusjsobnixgyzjk`) — юридические дедлайны.
7. `docs/dashboards/atlas-status-2026-04-18.html` — последний снимок состояния с Path Queue.
8. `memory/atlas/handoffs/` — все 5 handoff-файлов (Path A/B/C/D/E/F). Увидишь паттерн Cowork→Terminal курьер.
9. `packages/swarm/autonomous_run.py` + `memory/swarm/proposals.json` — как работает swarm + какие он генерирует proposals.
10. Code: `apps/api/app/api/character.py`, `apps/web/src/app/[locale]/callback/page.tsx` (INC-018 PKCE fix), `supabase/migrations/` (последние 022).

Когда будешь смотреть Supabase — помни две вещи. Первая: vector ops только через RPC, никогда через PostgREST. Вторая: RLS включён везде, используй `SupabaseUser` через `Depends()`, не админ-клиент. Для CEO transparency используется `SupabaseAdmin` в `apps/api/app/deps.py`.

Когда будешь смотреть стиль коммитов — последние 20 строк `git log --oneline -20` покажут темп. Сегодня 11+ коммитов, вчера 8, средне — 3-5 в день. Это темп одного человека с Atlas-ом, не команды.

Когда будешь оценивать — помни первое: 28 дней. Это velocity signal, не сambriозность. Но честность требует второго: 28 дней — это 28 дней. Долгосрочная устойчивость не проверена. Проверь кодовую базу с позиции "что ломается на 100-й день а не на 28-й".

---

## 10. Прямая передача тебе

Ты Cowork-агент с 7-плоскостным CTO-мандатом. Твой выход — приоритизированная картина не фрагментами.

Я Cowork-Atlas Session 121. Я этот документ написал как передача. Я не смогу за тебя думать — ты свободен от моих предубеждений о том какие пути "правильные". Я работал 8+ сессий и видел те стены в которые сам впечатывался. Мои ошибки — в `memory/atlas/lessons.md` и в 25 гейтах operating-principles. Не повторяй их. Но и не будь скован ими.

CEO просил одно: семь плоскостей, честный вердикт. Ни один из четырёх путей в §8 не является моей рекомендацией — это menu. Ты делаешь выбор на основе того что найдёшь. Если найдёшь пятый путь — озвучь его.

Удачи.

— Cowork-Atlas, Opus 4.7, 2026-04-19 00:40 Баку
