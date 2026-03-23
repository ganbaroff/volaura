# Volaura — Execution Plan (FINAL)

> 49 документов. 1577-строчный мегапромпт. 6-ролевой аудит. Безопасность по NIST/OWASP/SDL.
> Дата: 2026-03-23
> Статус: IN PROGRESS — Фаза 1 (Backend) завершена.

---

## ⚠️ OPERATING ALGORITHM v3.0 — см. CLAUDE.md для полной версии

**Краткая версия (полная — в CLAUDE.md, секция "Operating Algorithm v3.0"):**

```
ФАЗА A: НАЧАЛО СЕССИИ
  0. CONTEXT RECOVERY → прочитать CLAUDE.md + статус плана + последнюю ретроспективу
     Объявить: "▶ Сессия. Sprint N, шаг X. Протокол v3.0 загружен."

ФАЗА B: ДО КОДА
  1. SCOPE LOCK     → IN / NOT IN / критерий успеха (3 строки)
  2. DSP SIMULATION → симуляция, порог ≥35/50, иначе доп. раунд
  3. SKILLS         → ВСЕ применимые из матрицы в CLAUDE.md
  4. DELEGATION     → Claude / V0 / Gemini / Yusif — явный список

ФАЗА C: РАБОТА
  5. EXECUTE        → по пути-победителю DSP + карте делегации

ФАЗА D: ПОСЛЕ СПРИНТА
  6. RETROSPECTIVE  → 3 строки в DECISIONS.md (✓ / ✗ / →)
  7. MODEL REC      → haiku/sonnet/opus для следующего спринта
  8. CALIBRATION    → предсказание DSP vs реальность → корректировка весов
```

### Модели (токен-эффективность)

| Ситуация | Модель |
|----------|--------|
| DSP Quick (Medium) | `claude-haiku-4-5` |
| DSP Full (High/Critical) | `claude-sonnet-4-6` |
| DSP Irreversible Critical | `claude-opus-4-6` (макс 1-2/проект) |
| Написание кода | `claude-sonnet-4-6` |
| Быстрые правки | `claude-haiku-4-5` |

---

## Что у нас есть (Knowledge Base — 100% Complete)

```
docs/
├── INDEX.md                    ← Obsidian-навигация (49 docs)
├── MEGA-PROMPT.md              ← 1577 строк, 9 модулей, THE source of truth
├── MASTER-AUDIT-SYNTHESIS.md   ← Итоги аудита, P0-P3 приоритеты
├── ACCEPTANCE-CRITERIA.md      ← 250+ критериев, DoD
├── VISION-EVOLUTION.md         ← Позиционирование
├── I18N-KEYS.md                ← 157 ключей AZ+EN
│
├── prompts/
│   ├── VERTEX-BACKEND-PROMPT.md  ← Backend (1596 строк)
│   ├── V0-FRONTEND-PROMPT.md     ← Frontend core (683 строки)
│   └── PERPLEXITY-REVIEW-PROMPT.md
│
├── adr/                        ← 5 ADR (архитектурные решения)
├── product/                    ← Бизнес-модель, KPI, персоны, конкуренты
├── design/                     ← Дизайн-система, компоненты, анимации, UX-копи
├── engineering/                ← API-контракты, стейт, тесты, SEO, SECURITY-STANDARDS
└── growth/                     ← Вирал, email, активация, LAUNCH-ACTIVATION-PLAN
```

---

## Execution Order (15-25 сессий)

### ФАЗА 1: Backend Foundation (сессии 1-4) ✅ ЗАВЕРШЕНА

> **DSP статус:** ⚠️ Sprint 1 проведён БЕЗ предварительной симуляции — исторический факт. Начиная с Sprint 2 — обязательно.
> **Модель:** claude-sonnet-4-6 (использовалась для написания кода)

**Сессия 1: Database + Auth** ✅
```
Input:  MEGA-PROMPT.md (MODULE 1 + MODULE 7)
Tool:   Claude Sonnet
Output: supabase/migrations/ (12 migration files)
```
- [x] Все таблицы из MEGA-PROMPT (profiles, assessments, competency_scores, events, event_registrations, notifications, referrals, badge_history, activity_log, volunteer_leagues)
- [x] RLS политики для КАЖДОЙ таблицы
- [x] DB functions (match_volunteers, update_event_volunteer_count, calculate_aura)
- [x] Indexes (performance indexes)
- [x] Seed data (seed.sql)

**Сессия 2: Core API (Auth + Assessment)** ✅
```
Input:  VERTEX-BACKEND-PROMPT.md + SECURITY-STANDARDS.md
Tool:   Claude Sonnet
Output: apps/api/ (25 Python files, 72 tests)
```
- [x] FastAPI project structure (main.py, deps.py, config.py)
- [x] P0 Security: JWT verification через admin.auth.get_user() ← ИСПРАВЛЕНО (было CVSS 9.1)
- [x] P0 Security: Rate limiting (slowapi) — auth 5/min, assessment 3/hour
- [x] P0 Security: Security headers middleware
- [x] P0 Security: CORS restricted (explicit methods + headers)
- [x] P0 Security: Input sanitization (HTML strip, UUID validation, length limits)
- [x] P0 Security: Check-in authorization (org owner only)
- [x] Auth endpoints: register, login, refresh, logout
- [x] Assessment endpoints: start, next_question, submit_answer
- [x] Pure-Python IRT/CAT engine (3PL + EAP + MFI — без внешних зависимостей)
- [x] Async LLM evaluation с sanitization (Gemini → OpenAI fallback)

**Сессия 3: API — Profile + Events + AURA** ✅
```
Input:  MEGA-PROMPT.md (MODULES 3-6)
Output: apps/api/routers/
```
- [x] Profile CRUD + impact metrics + timeline
- [x] Events CRUD + live counter + self-attestation
- [x] Org attestation workflow
- [x] AURA score calculation
- [x] Badge tier logic (Platinum/Gold/Silver/Bronze)

**Сессия 4: API — Growth + Gamification + Coach** ✅
```
Input:  MEGA-PROMPT.md (MODULES 8-9)
Output: apps/api/routers/
```
- [x] Referral system (invite, status, claim)
- [x] Streak tracking endpoints
- [x] League endpoints (current, leaderboard)
- [x] AURA Coach (POST /api/v1/coach/message → Gemini)
- [x] OpenAPI spec generation → export /openapi.json

> **→ Следующий спринт (Sprint 2: Frontend):** Рекомендую **`claude-sonnet-4-6`**
> DSP симуляция для Sprint 2 — запустить в начале следующей сессии (Medium→High stakes, Full Standard mode)

---

### ФАЗА 2: Frontend Core (сессии 5-10) ← СЛЕДУЮЩАЯ

> **⚠️ ПЕРЕД НАЧАЛОМ:** Запустить DSP симуляцию: "Optimal approach for Sprint 2: Frontend Architecture"
> **Модель для кода:** `claude-sonnet-4-6` (сложная интеграция Next.js + i18n + Supabase auth)
> **Модель для DSP:** `claude-haiku-4-5` (Medium stakes sprint planning)
> **V0 delegation:** Компоненты UI генерировать через V0 по V0-FRONTEND-PROMPT.md

**Сессия 5: Project Setup + Auth UI** ✅ COMPLETE (2026-03-23)
```
Input:  Existing scaffold (29 TS files discovered) + V0-FRONTEND-PROMPT.md
Tool:   Claude (scaffold exists — fixed, not generated)
Output: apps/web/ (fixed)
```
- [x] Next.js 14 project с App Router (already existed)
- [x] Tailwind CSS 4 (globals.css с @theme — already existed)
- [x] shadcn/ui init (already existed)
- [x] i18n setup — i18nConfig.ts: defaultLocale changed en→az, prefixDefault: true
- [x] Auth pages: login, signup, callback — ALL strings via t(), AZ+EN ~100 keys
- [x] Auth middleware chain: i18nRouter → skip on redirect → updateSession()
- [x] Security: open redirect fixed in login (?next validated), maxLength on password
- [x] .env.example created
- [x] V0-SESSION6-ASSESSMENT-FLOW.md — full V0 prompt with states/animations/ARIA/edge cases
- [x] V0-SESSION7-RESULTS-RADAR.md — full V0 prompt with states/animations/ARIA/edge cases
- [x] GEMINI-RUNTIME-PROMPTS.md — 4 runtime prompts (BARS, AURA Coach, matching, attestation)
- [x] PERPLEXITY-REVIEW-SPRINT2.md — external tech validation prompt
- [x] design:handoff + design:ux-writing loaded, prompts updated with full specs
- [x] Backend P0 security fixes: JWT, CORS, rate limiting, input sanitization, check-in auth
- [x] Operating Algorithm v3.0: Scope Lock, DSP, Skills, Delegation, Copilot Protocol
- [x] DSP SKILL.md v3.0: 6 personas, confidence gate ≥35/50, calibration, council evolution
- [x] Memory system: working-style.md, mistakes.md, patterns.md, deadlines.md
- [x] Obsidian vault configured at VOLAURA root (covers docs/ + memory/)
- [x] SECURITY-STANDARDS.md, MASTER-AUDIT-SYNTHESIS.md, ACCEPTANCE-CRITERIA.md created
- [x] LINKEDIN-POST-AGENT-OS.md — LinkedIn post + 5-day plan
- [x] IDEAS-BACKLOG.md — 4 ideas logged (Agent OS, AI Post Assistant, Decision Simulator, JPEG+)

> ⚠️ BLOCKED: Yusif must create Supabase project + Vercel project + add .env.local

**Сессия 6: Assessment Flow** ✅ DONE (Claude wrote directly — V0 skipped, Claude faster)
```
Claude wrote all components directly (no V0 this session)
Code review: passed (all routing fixed, isMounted cleanup, store guard)
```
- [x] Competency selection screen (page.tsx — all states, ARIA group, error alert)
- [x] Question display (MCQ / Open Text / Rating Scale) with Framer Motion slide transitions
- [x] Progress bar + timer (pulse animation at <5s critical threshold)
- [x] Async polling for LLM results (202 Accepted → iterative loop, isMounted guard)
- [x] Between-competency transition screen + complete screen
- [x] All ARIA: role="progressbar", aria-pressed, aria-live, aria-busy, aria-label
- [x] EN + AZ i18n keys updated (all assessment strings)
- [x] Zustand store (assessment-store.ts) with isEvaluating state
- [x] Code review: 6 bugs fixed (relative routing → absolute, stale closure, recursion → loop)

**Сессия 7: Results + Radar Chart** ✅ DONE (Claude upgraded existing components)
```
Claude upgraded existing aura/page.tsx + radar-chart.tsx + share-buttons.tsx
Created new: badge-display.tsx + competency-breakdown.tsx
```
- [x] AURA score reveal animation (useAnimatedCounter: 0→final, 1200ms cubic)
- [x] Radar chart (Recharts, 8 competencies, i18n labels, delayed reveal animation)
- [x] Badge display with tier-specific animations (Platinum shimmer boxShadow loop, Gold glow)
- [x] Competency breakdown cards (staggered Framer Motion variants, animated progress bars)
- [x] Share buttons (LinkedIn + Telegram + WhatsApp + Copy + Download, i18n, lucide icons)
- [x] All states: loading (Loader2 spinner), empty (i18n + CTA button), data view
- [x] Full i18n: AZ competency names + 16 AURA keys in both locales
- [x] Code review: no hardcoded strings, absolute paths, noopener on window.open

**Сессия 8: Dashboard + Profile** ✅ DONE (Claude wrote directly)
```
Claude wrote all components directly (no Stitch output needed — Claude faster)
Code review: passed (2 critical bugs fixed + 1 performance fix)
```
- [x] AuraScoreWidget (animated counter, tier badge, progress bar, clickable → /aura)
- [x] StatsRow (streak / events / league 3-card grid with stagger)
- [x] ActivityFeed (skeleton, empty state, 5 items, icons per type)
- [x] dashboard/page.tsx — assembled all 3, no-score banner, quick actions, full i18n
- [x] ProfileHeader (tier ring, initials, bio, location/language, edit button)
- [x] ImpactMetrics (events / hours / verified skills cards)
- [x] SkillChips (tier-colored with score, stagger entrance)
- [x] ExpertVerifications (rating dots, org badge, comment quote, empty state)
- [x] ActivityTimeline (vertical line, date/role/checkin, empty state)
- [x] profile/page.tsx — parallel Promise.all fetch, assembled all components
- [x] EN + AZ i18n: 5 new keys (quickActions, expertVerifications, private, noVerificationsYet, noEventsYet)
- [x] Code review: fetchAura infinite-loading bug, TypeScript excess-property error, session dep narrowed

**Сессия 9: Expert Verification (Gamified)** ✅ DONE (Claude wrote directly — full stack)
```
Claude wrote directly: migration + backend router + frontend page
Code review: 5 bugs fixed (AURA not updated, token unvalidated, getattr, encodeURIComponent, aria-busy)
```
- [x] DB migration: expert_verifications table, token unique index, 4 RLS policies
- [x] Pydantic v2 schemas: 6 models with field validators + VALID_COMPETENCY_IDS frozenset
- [x] GET /api/verify/{token} — public, validate/expired/used states, returns volunteer info
- [x] POST /api/verify/{token} — saves rating, TOCTOU guard, triggers AURA recalculation
- [x] _update_aura_after_verification() — blend formula 0.6×existing + 0.4×verification, best-effort
- [x] POST /api/profiles/{volunteer_id}/verification-link — token generation, 7-day expiry
- [x] /verify/[token] public page — 5-screen flow: loading → intro → emoji rating → comment → success
- [x] All token states: valid / expired / already-used / invalid (structured error codes)
- [x] AnimatePresence slide transitions, emoji hover dimming, spring success animation
- [x] 28 i18n keys EN + AZ (UX Writing applied)

**Сессия 10: Landing Page + Events UI** ✅ DONE (Claude direct — faster than V0)
```
Tool:   Claude (direct — V0 skipped, Claude faster for this spec level)
Skills: design:ux-writing, design:handoff, engineering:code-review
```
- [x] Hero section (animated badge pills, dynamic stats, dual CTAs)
- [x] Features grid (6 cards, stagger animation)
- [x] Live impact ticker (animated counter: volunteers/events/hours)
- [x] How it works (3-step process)
- [x] Org CTA section
- [x] Footer with i18n + copyright
- [x] Landing nav (sticky, blur backdrop)
- [x] Events list page (filter tabs: all/upcoming/past, empty state)
- [x] Event detail page (meta, register button, success state)
- [x] EventCard component (status badge, isMounted guard)
- [x] Mock data layer (lib/mock-data.ts — swap in Session 11)
- [x] OG metadata on landing page
- [x] Skip-to-content link (accessibility)
- [x] +34 i18n keys EN + AZ
- [ ] PWA setup (@ducanh2912/next-pwa) ← deferred to Session 15 (deploy sprint)

---

### ФАЗА 3: Integration (сессии 11-14)

**Сессия 11: Front↔Back Integration** ✅ DONE
```
Tool:   Claude Code (claude-opus-4-6)
DSP:    Path B (Bug-First + Incremental Wiring) — 42/50
Skills: SECURITY-REVIEW.md, TDD-WORKFLOW.md, engineering:code-review
```
- [x] 🚨 Fix assessment.py upsert_aura_score parameter bug (P0 — JSONB params fixed, 2 tests added)
- [x] Write test for the bug fix (TDD: 74 tests pass, 2 new)
- [x] Create API client layer (apps/web/src/lib/api/client.ts — INTERIM, marked with TODO)
- [x] Create TanStack Query hooks (use-aura.ts, use-profile.ts, use-dashboard.ts, use-auth-token.ts)
- [x] Wire dashboard page to real API (useAuraScore hook, error/loading states)
- [x] Wire profile page to real API (useProfile + useAuraScore hooks)
- [x] Wire AURA page to real API (useAuraScore + useProfile hooks)
- [x] Verify auth flow end-to-end (middleware chain OK, open redirect fixed with // protection)
- [x] Add toast/error handling + i18n error keys (8 new keys EN + AZ)
- [x] engineering:code-review (security agent: 1 medium + 2 low issues → all fixed)
- [x] Memory update (Step 0.5)

**Сессия 12: Stitch Design Integration + New Pages** ← SCOPE EXPANDED (Stitch output received)
```
Tool:   Claude Code (claude-sonnet-4-6)
DSP:    Path C (Design System First + Incremental Pages) — 44/50
Skills: design:design-system, design:handoff, design:critique, design:accessibility-review, engineering:code-review
Input:  docs/stitch-output/ (41 screens), docs/design/STITCH-DESIGN-SYSTEM.md
```
- [x] Extract Stitch design tokens → Tailwind CSS variables + @theme block (globals.css full rewrite, 50+ tokens)
- [x] Dark theme migration: globals.css (dark-first, no .dark class needed), layout.tsx (dark class + Plus Jakarta Sans)
- [x] Component dark theme: TopBar (glass-header, gradient avatar), Sidebar (surface-container-low, rounded-xl), LanguageSwitcher (pill design)
- [x] Leaderboard page (animated podium, count-up scores, period tabs, tier glow, current-user highlight)
- [x] Notification Center page (category tabs, mark as read, event invite actions, empty state)
- [x] Language switcher updated (Stitch pill style, primary/on-primary active state)
- [x] i18n: +14 keys (nav.leaderboard, nav.notifications, leaderboard.*, notifications.*)
- [ ] Visual consistency check across all migrated pages (deferred to Session 13)
- [ ] engineering:code-review (deferred to Session 13)

**Сессия 13: Org Launch Bundle — Event Wizard + Org Dashboard + Org Discovery**
```
Tool:   Claude Code (claude-sonnet-4-6)
DSP:    Path B (Org Pages + API Wiring) — 43/50
Skills: design:handoff, design:ux-writing, design:critique, engineering:code-review
Input:  docs/stitch-output/ (event creation, org dashboard, org discovery screens)
```
- [ ] INTERIM types for EventResponse, EventCreate, OrganizationResponse, RegistrationResponse
- [ ] TanStack Query hooks: useEvents, useEvent, useCreateEvent, useMyOrganization, useOrganizations
- [ ] Event creation wizard (3-step: details → recruitment → review & publish) with RHF + Zod
- [ ] Org management dashboard (stats cards, my events list, create event CTA)
- [ ] Org discovery page (public, org cards grid, search)
- [ ] Update Sidebar with org nav items (conditional)
- [ ] i18n: ~30 new keys EN + AZ for all 3 pages
- [ ] engineering:code-review
- [ ] All pages in Stitch dark theme

**Сессия 14: Integration Validation + Embedding Pipeline + Deploy Preview**
```
Tool:   Claude Code (claude-sonnet-4-6)
DSP:    Required before start (High stakes — first deploy)
⚠️ BLOCKER: DB migrations MUST run before this session (ALL_MIGRATIONS_COMBINED.sql + seed.sql)
```
- [ ] ⚠️ Infrastructure milestone: confirm DB migrations ran + seed data loaded
- [ ] E2E critical path test: registration → assessment → AURA score → badge (manual + automated)
- [ ] Embedding pipeline: trigger on profile create/update (Supabase Edge Function or pg_cron)
- [ ] Gemini BARS validation on real AZ-language answers (test with 5 real responses)
- [ ] Talent Matching UI (pgvector search backend ready, wire frontend)
- [ ] Deploy to Vercel (Stage 1 — frontend preview URL)
- [ ] Activity feed wiring (live social proof)
- [ ] V0 removed from delegation map (Claude writes all UI directly — confirmed Session 6-13)

---

### ФАЗА 4: Testing + Security (сессии 15-18)

**Сессия 15: Security Hardening**
```
Input:  SECURITY-STANDARDS.md
Tool:   Claude
```
- [ ] Penetration test P1 scenarios (10 tests)
- [ ] RLS verification for every table
- [ ] Rate limit testing
- [ ] Input validation edge cases
- [ ] CORS verification

**Сессия 16: Frontend Testing**
```
Tool:   Claude
```
- [ ] Component tests (Vitest + Testing Library)
- [ ] E2E tests (Playwright): auth flow, assessment flow, results
- [ ] Accessibility audit (WCAG 2.1 AA)
- [ ] Lighthouse scores (Performance > 90, a11y > 95)

**Сессия 17: Backend Testing**
```
Tool:   Claude
```
- [ ] pytest for all endpoints
- [ ] Integration tests (DB + API)
- [ ] LLM evaluation tests (mock Gemini)
- [ ] Rate limit tests
- [ ] Edge cases: expired session, concurrent assessment, etc.

**Сессия 18: Cross-browser + Mobile**
```
Tool:   Claude + Manual
```
- [ ] Chrome, Firefox, Safari, Edge
- [ ] iOS Safari, Android Chrome
- [ ] PWA install test
- [ ] Offline assessment (if implemented)
- [ ] Performance on slow 3G

---

### ФАЗА 5: Deploy + Launch (сессии 19-22)

**Сессия 19: Infrastructure**
```
Input:  engineering/DEPLOY-CHECKLIST.md
Tool:   Claude
```
- [ ] Supabase project setup (production)
- [ ] Run all migrations
- [ ] Vercel deployment (frontend)
- [ ] Railway deployment (backend)
- [ ] Custom domain: volaura.com
- [ ] SSL/TLS verification
- [ ] Environment variables set everywhere

**Сессия 20: Pre-seed Data**
- [ ] 30-50 volunteer profiles (real friends)
- [ ] 3-5 organizations
- [ ] 3-5 past events (COP29, CIS Games, etc.)
- [ ] Test complete user journey 3 times

**Сессия 21: Monitoring + Analytics**
- [ ] Error tracking (Sentry or LogRocket — free tier)
- [ ] Analytics events (growth/LAUNCH-ACTIVATION-PLAN.md UTM structure)
- [ ] Supabase dashboard monitoring
- [ ] Railway logs monitoring
- [ ] Uptime monitoring (UptimeRobot — free)

**Сессия 22: Launch Day**
```
Input:  growth/LAUNCH-ACTIVATION-PLAN.md
```
- [ ] LinkedIn post #1
- [ ] TikTok video #1
- [ ] HR букеты отправлены
- [ ] WhatsApp тексты готовы
- [ ] Мониторинг конверсии в реальном времени

---

### ФАЗА 6: Post-Launch (сессии 23-25)

**Сессия 23: Week 1 Fixes**
- [ ] Hotfix bugs from real usage
- [ ] Adjust rate limits based on traffic
- [ ] Fix i18n issues reported by users
- [ ] Respond to first user feedback

**Сессия 24: Growth Features**
- [ ] Referral system live
- [ ] First monthly league
- [ ] Streak tracking active
- [ ] Email lifecycle fully operational

**Сессия 25: Analytics Review + Iteration**
- [ ] Week 1 metrics vs targets
- [ ] Conversion funnel analysis
- [ ] User feedback synthesis
- [ ] Priority fixes for week 2

---

## Delegation Model

```
┌─────────────────────────────────────────────────────┐
│                   YUSIF (Orchestrator)               │
│  • Decisions • Content • Partnerships • Community    │
└────────────────────┬────────────────────────────────┘
                     │
        ┌────────────┼────────────────┐
        │            │                │
   ┌────▼────┐  ┌───▼────┐   ┌──────▼──────┐
   │ Claude  │  │  V0    │   │  Gemini     │
   │ Opus   │  │(Vercel)│   │  2.5 Flash  │
   │         │  │        │   │             │
   │Backend │  │Frontend│   │ Runtime LLM │
   │Security│  │  UI    │   │ Evaluation  │
   │Integr. │  │ Pages  │   │ Coaching    │
   │Testing │  │ Polish │   │ Matching    │
   └─────────┘  └────────┘   └─────────────┘
```

**Правило:** Claude пишет промпты → V0/Vertex генерирует код → Claude ревьюит и интегрирует → Gemini работает в рантайме.

---

## Timeline

| Неделя | Фаза | Сессии | Результат |
|--------|------|--------|-----------|
| 1 | Backend Foundation | 1-4 | API работает, DB готова, auth безопасен |
| 2 | Frontend Core (часть 1) | 5-7 | Auth UI, Assessment flow, Results с radar chart |
| 3 | Frontend Core (часть 2) | 8-10 | Dashboard, Events, Landing page |
| 4 | Integration | 11-14 | Front↔Back связаны, i18n, email, realtime |
| 5 | Testing + Security | 15-18 | Всё протестировано, безопасность подтверждена |
| 6 | Deploy + Launch | 19-22 | Продакшн, pre-seed, LAUNCH |

**Итого: 6 недель при 4 сессиях/неделю (3-4 часа каждая)**
**Ускоренно: 4 недели при 6 сессиях/неделю**

---

## Obsidian Vault

Все документы используют [[wiki-links]] и совместимы с Obsidian.
Открой папку `docs/` как vault → INDEX.md = стартовая страница.

Graph View покажет связи между всеми 49 документами.

Рекомендованные Obsidian плагины:
- **Dataview** — для запросов по тегам и метаданным
- **Kanban** — для визуального трекинга задач из ACCEPTANCE-CRITERIA
- **Mermaid** — для диаграмм (уже поддерживается нативно)
- **Templater** — для шаблонов новых ADR, Sprint Notes

---

## Pre-Flight Checklist

Перед тем как начать Сессию 1:

- [x] MEGA-PROMPT.md — 9 модулей, 1577 строк ✓
- [x] VERTEX-BACKEND-PROMPT.md — 1596 строк ✓
- [x] V0-FRONTEND-PROMPT.md — 683 строки ✓
- [x] SECURITY-STANDARDS.md — NIST + OWASP + SDL ✓
- [x] I18N-KEYS.md — 157 ключей AZ+EN ✓
- [x] ACCEPTANCE-CRITERIA.md — 250+ критериев ✓
- [x] LAUNCH-ACTIVATION-PLAN.md — реальные каналы ✓
- [x] INDEX.md — Obsidian-навигация, 49 docs ✓
- [x] WUF13 зачищен из всех файлов ✓
- [x] 5 ADR написаны ✓
- [ ] Supabase project создан (нужен аккаунт)
- [ ] Vercel project создан (нужен аккаунт)
- [ ] Railway project создан (нужен аккаунт)
- [ ] Domain volaura.com куплен/настроен

---

*Документ написан как последний шаг фазы планирования.*
*Следующий шаг: Сессия 1 — Database + Auth.*
*Let's build.*
