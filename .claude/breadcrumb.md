# CTO BREADCRUMB — Session 90 (ACTIVE)

## ⚡ CEO MANDATORY DIRECTIVES — READ EVERY SESSION BEFORE ANY WORK ⚡

### 1. Кто такой Юсиф (поведенческие паттерны)
- **Рекурсивный мыслитель**: видит одну систему на 3 масштабах одновременно (мозг→продукт→UI→агенты→мир)
- **Интуиция опережает research**: приходит с готовым видением, не с вопросом — задача CTO усилить, не переосмыслить
- **Строитель экосистем**: VOLAURA + MindShift + Life Simulator + BrandedBy + ZEUS — всё связано одной идеей
- **CEO не хочет отчётов**: хочет результатов и прямого разговора как с co-founder'ом
- **Требует 100% effort всегда** — не экономить ресурсы, не срезать углы, не делать "достаточно хорошо"

### 2. Идея проекта
**VOLAURA** = "Prove your skills. Earn your AURA. Get found by top organizations."
- Верифицированный талант-платформ: навыки доказываются через адаптивный IRT-ассессмент, не CV
- Целевая аудитория: волонтёры → переход в профессиональные позиции через доказанные навыки
- НИКОГДА не говорить "volunteer platform" или "LinkedIn competitor"
- AURA score = взвешенная сумма верифицированных компетенций (8 компетенций, IRT/CAT движок)

### 3. Как работает CTO (обязательные правила поведения)
- **100% effort, всегда** — полная команда агентов, все доступные API, GPU (Gemma 4 local), Figma MCP
- **Не кодить в одиночку** — делегировать 80%+ агентам, CTO = оркестратор
- **Не спрашивать разрешения** на очевидные решения — делать и репортить
- **Вариант C всегда** — самый полный, самый правильный подход, не экономия
- **Figma MCP + Code Connect** — дизайним в Figma, синхронизируем через MCP, живая система
- **Swarm перед кодом** — `python -m packages.swarm.autonomous_run --mode=audit` перед любой крупной задачей
- **Не объявлять "готово"** без E2E проверки реального юзер-пути

### 4. Текущий стек и где что живёт
- Frontend: `apps/web/` — Next.js 14, Tailwind 4, shadcn/ui, Zustand
- Backend: `apps/api/` — FastAPI, Railway (`volauraapi-production.up.railway.app`)
- DB: Supabase (`dwdgzfusjsobnixgyzjk`) — ПРАВИЛЬНЫЙ проект
- Vercel: `volaura.app` — production frontend
- Figma: fileKey=`B30q4nqVq5VjdqAVVYRh3t` (Design System v2, 57 переменных)

---

## NOW (Session 90 — что сделано)

### Задеплоено и работает в production:
- ✅ Railway API (`volauraapi-production.up.railway.app`) — правильный Supabase проект
- ✅ Vercel `NEXT_PUBLIC_API_URL` = Railway API (было Claw3D — чужой проект!)
- ✅ Energy Picker (⚡🌤🌙) + Pre-Assessment Summary — в коде, деплой pending
- ✅ E2E path работает: Landing → Dashboard → Assessment → Complete → Score 32.6 → AURA → Profile
- ✅ AURA page: score 6.5 (32.6 * weight 0.20), Competency Radar, Share buttons
- ✅ Profile: Yusif Ganbarov, @yusif, #0001 Founding Member, Communication 33 badge
- ✅ Dashboard: AURA 6.5, tribe widget, quick actions

### Баги исправлены в этой сессии:
- ✅ upsert_aura_score не писал — RPC был правильным, первый запрос prod упал (transient). Manual SQL fix.
- ✅ Coaching 500: `column competencies.name does not exist` → исправлен на `name_en`/`description_en`

### Pending деплой:
- 🔄 `vercel --prod` запущен из `apps/web` (должен задеплоить Energy Picker + PreAssessmentSummary)
- 🔄 Fix coaching `name_en` надо закоммитить и задеплоить на Railway
- 🔄 NEW (19b36b4): Energy adaptation wired into should_stop — нужен Railway deploy для эффекта

### Session 90 parallel work (Opus 4.6 CTO из MindShift worktree):
- ✅ Honesty hooks built + tested (UserPromptSubmit works, Stop disabled due to transcript timing)
- ✅ ESLint Law 1 rule shipped in MindShift (4300f9d) — mechanical red color enforcement
- ✅ Energy adaptation CLOSED the loop (19b36b4) — should_stop() now honors energy_level:
  - full: 20 items / SE 0.3 (was default)
  - mid: 12 items / SE 0.4 (NEW)
  - low: 5 items / SE 0.5 (NEW)
- ✅ 39 assessment engine tests pass (was 33, added 6 for energy profiles)
- Found: EnergyPicker UI was already shipped by Session 90 agent but behavior layer missing — closed.

### Следующий приоритет:
1. Figma MCP + Code Connect setup (Вариант C — CEO выбрал)
2. Создать 8 экранов в Figma (Dashboard, Assessment, AURA, Profile, Expert Verification, Org Dashboard, Settings, Onboarding)
3. GITA grant demo video (Playwright E2E запись)
4. Coaching tips bug (coaching 500 → name_en fix нужен Railway deploy)

## KEY BUGS REMAINING
- Coaching tips: 500 → `name` column bug (fix committed, нужен Railway deploy)
- "Assessment in progress" label на AURA при completed assessment (cosmetic)
- Dashboard "Recommended for you" показывает "Take first assessment" даже после completion

## PRODUCTION URLS
- Frontend: https://volaura.app
- API: https://volauraapi-production.up.railway.app
- API health: https://volauraapi-production.up.railway.app/health
