# Volaura — Execution Plan (FINAL)

> 49 документов. 1577-строчный мегапромпт. 6-ролевой аудит. Безопасность по NIST/OWASP/SDL.
> Дата: 2026-03-23
> Статус: IN PROGRESS — Sprint 9. Фазы 1-3 завершены. Фазы 4-5 частично. LIVE: Railway + Vercel + volaura.app.
> Last synced: 2026-03-26 Session 42 (assessment hardening + keyword redesign)

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

**Сессия 13: Org Launch Bundle — Event Wizard + Org Dashboard + Org Discovery** ✅ PARTIALLY DONE
```
Tool:   Claude Code (claude-sonnet-4-6)
DSP:    Path B (Org Pages + API Wiring) — 43/50
Skills: design:handoff, design:ux-writing, design:critique, engineering:code-review
```
- [x] INTERIM types for EventResponse, EventCreate, OrganizationResponse, RegistrationResponse
- [x] TanStack Query hooks: useEvents, useEvent, useCreateEvent, useMyOrganization, useOrganizations
- [x] Event creation wizard (3-step: details → recruitment → review & publish) with RHF + Zod
- [x] Org management dashboard (stats cards, my events list, create event CTA)
- [x] Org discovery page (public, org cards grid, search)
- [x] Update Sidebar with org nav items (conditional)
- [x] i18n: ~30 new keys EN + AZ for all 3 pages
- [x] engineering:code-review
- [ ] All pages in Stitch dark theme ← DEFERRED (dark theme is live, Stitch token migration done)

**Сессия 14 (merged into 14a-14d): Integration + Deploy + Security** ✅ DONE
```
Spanned Sessions 14a through 14d (2026-03-24)
```
- [x] ⚠️ Infrastructure milestone: DB migrations ran + seed data loaded (SAFE_MIGRATION.sql + idempotent seed)
- [x] Embedding pipeline: trigger on profile create/update (apps/api/app/services/embeddings.py)
- [x] Deploy to Vercel: ✅ LIVE at volaura.app
- [x] Deploy to Railway: ✅ LIVE at modest-happiness-production.up.railway.app
- [x] Activity feed wiring: `/api/activity/me` + `/api/activity/stats/me` endpoints, useActivity() hook
- [x] V0 removed from delegation map (Claude writes all UI directly — confirmed Session 6-13)
- [x] Architecture audit by 18 agents: `fix_api_client_first` won (11/18 votes)
- [x] Security hardening: LLM timeout 15s, CSP headers, auth error leak fixed
- [x] Backend P2 fixes: register error leak, AssessmentResultOut schema, loguru
- [ ] Talent Matching UI ← DEFERRED to post-beta (backend pgvector ready, frontend not built)
- [ ] E2E automated tests ← DEFERRED (manual testing done, Playwright not set up)

---

### SPRINT 3-9 WORK (Sessions 15-37, 2026-03-24 → 2026-03-26) — NOT IN ORIGINAL PLAN

> Sprints 3-9 emerged from real-world priorities. Original Phase 4-6 plan is partially superseded.
> See `memory/context/sprint-state.md` for full session-by-session log.

**Sprint 3-4 (Sessions 15-18): Testing + MiroFish Swarm** ✅
- [x] 18 backend test files (pytest-asyncio)
- [x] 11 frontend test files (Vitest + Testing Library)
- [x] MiroFish v4-v7.1 complete (13 providers, research loop, adaptive prompts, dead weight auto-removal)
- [x] Sliding-window calibration, accuracy-scaled conviction, ResponseQualityMiddleware

**Sprint 5-6 (Sessions 19-25): Deploy + Security + Agent Autonomy** ✅
- [x] Railway deploy LIVE + Vercel LIVE + volaura.app domain
- [x] Supabase production migrations applied (000001-000023)
- [x] GROQ_API_KEY + TELEGRAM tokens on Railway
- [x] Agent autonomy system: inbox_protocol.py, autonomous_run.py, swarm-daily.yml
- [x] @volaurabot LIVE on Telegram (CEO notifications)
- [x] Privacy Policy page (/en/privacy-policy)
- [x] 7 CRITICAL + HIGH security issues fixed
- [x] Rate limiting on /aura/{id}

**Sprint 7-8 (Sessions 26-36): Production Polish + 47 Routes** ✅
- [x] 47 backend routes (was 31 at Session 14)
- [x] All frontend 404 nav links fixed
- [x] Real data everywhere (no more mock data)
- [x] Migration 000027 applied
- [x] LinkedIn Post #1 published, Post #2 in pipeline
- [x] Mega-retrospective → MANDATORY-RULES.md, SPRINT-REVIEW-TEMPLATE.md, CONTINUOUS-LEARNING.md
- [x] DSP v4.0 (real parallel agents instead of single-model pseudo-debate)
- [x] Claude Code config: 7 hooks, permissions hardened, /post skill

**Sprint 9 (Sessions 37+): COMPLETE** ✅ (2026-03-27)
- [x] CSV bulk volunteer invite (max 500 rows, batches of 50, audit log) — Session 39
- [x] Assessment flow fixes (6 files rewritten, URL/body/field mismatches) — Session 40
- [x] Assessment hardening (DeCE, anti-gaming, GRS, reeval worker) — Session 42
- [x] 9 Supabase migrations applied via MCP — Sessions 43-44
- [x] Question bank: 0 placeholders, 90 real scenarios across 8 competencies — Session 44
- [x] Railway production fix: anon key hardcoded fallback (Mistake #53) — Session 44
- [x] E2E verified on production: auth → AURA 12.47 → assessment → answer — Session 44
- [ ] `pnpm generate:api` → replace 7 TODO hooks (ADR-003 compliance) ← Sprint 10
- [ ] Post #3 — needs new angle (Antigravity rejected as Mistake #40) ← CEO decision
- [ ] Vitest Node v20 fix (nvm use 20) ← Sprint 10

**Sprint 10 (Sessions 44+): Starting — Org Dashboard + Frontend Polish**
- [ ] `pnpm generate:api` → replace 7 TODO hooks with generated TypeScript
- [ ] Org dashboard: aggregate volunteer scores + B2B matching endpoint
- [ ] Post #3 rewrite (new angle from CEO)
- [ ] Vitest Node v20 fix

---

### ФАЗА ECOSYSTEM: Cross-Product Integration (Sessions 45+)

> Parallel to Volaura Track 10. 3 tracks (A/B/C). Full plan: memory/ecosystem_master_plan.md
> Monetization: docs/MONETIZATION-ROADMAP.md | AI Twin: docs/AI-TWIN-CONCEPT.md

**Last synced: 2026-03-27 Session 46**

**Track A: Core Integration (CTO leads)**

Sprint A0 ✅ DONE (Session 45) — character_state as Thalamus
- [x] Migration 000031: character_events + game_crystal_ledger + game_character_rewards (RLS on all)
- [x] Migration 000032: audit fixes — CHECK constraints, BIGINT, search_path, regex guards, skill_unverified
- [x] schemas/character.py: EventType (8 types), SourceProduct, DAILY_CRYSTAL_CAP, CharacterEventCreate/Out/StateOut
- [x] routers/character.py: POST /api/character/events, GET /api/character/state, GET /api/character/events
- [x] main.py: character router registered at /api prefix
- [x] E2E verified: 6/6 smoke tests pass, 9/9 audit fixes confirmed on production
- [x] Monetization framework documented (docs/MONETIZATION-ROADMAP.md, docs/AI-TWIN-CONCEPT.md)

Sprint A1 ✅ DONE (Session 46) — Volaura Crystal Bridge
- [x] Hook into POST /api/assessment/complete → emit crystal_earned + skill_verified events
- [x] Idempotency: game_character_rewards (one claim per competency per user)
- [x] Anti-farming: check game_character_rewards BEFORE INSERT
- [x] Acceptance: crystal_balance 100→150, verified_skills=[communication silver 62.33] on production

Sprint A0.5: character_state architecture hardening ← NEXT (added 2026-03-27 after ecosystem assessment)
- [ ] character_state → read-only aggregation layer (materialized view, not write bus)
- [ ] Each product owns its own data, character_state = computation layer
- [ ] Single point of failure eliminated BEFORE scale
- Reason: Нигяр + Scaling Engineer both flagged. One bad migration = all 5 products down.

Sprint ZEUS-1: Autonomous Content Engine (2–3 weeks from now) ← HIGH PRIORITY
- [ ] Supabase webhook on character_events INSERT (event_type = skill_verified, milestone_reached)
- [ ] FastAPI endpoint: receive webhook → Claude API → generate channel-specific post
- [ ] Content moderation layer: Claude classifies safe/unsafe before publish
- [ ] Pyrogram (not Telethon) with human-like delays (random 60–180s)
- [ ] Rate limiter: max 8 posts/day per channel
- [ ] zeus_publications log table in Supabase
- [ ] n8n REMOVED — replaced by Supabase webhooks + FastAPI + APScheduler
- Reason: World practices show zero-CAC flywheel determines A vs C scenario. $730K revenue difference.

Sprint A2: MindShift → feature inside Volaura (NOT standalone product)
- [ ] MindShift focus features integrated as "Focus Mode" section in Volaura
- [ ] Shared auth (same Supabase instance)
- [ ] Focus sessions → character_state xp_earned events
- Note: mindshift.app → 301 redirect to volaura.az/focus (check traffic first)

Sprint A3: Life Simulator → Career Path inside Volaura (NOT standalone)
- [ ] Life Sim bug fixes (10 P0-P2: event_queue_controller.gd:202, game_loop_controller.gd:91)
- [ ] Career Path view inside Volaura (post-assessment unlock)
- [ ] "RPG where real skills matter" framing, NOT "gamified productivity" (Habitica lesson)

Sprint A4: Voice AI Twin (Kokoro, queue infrastructure)
Sprint A5: Stripe integration (crystal purchase)
Sprint A6: Pro tier billing

**Track B: BrandedBy (parallel chat) ← REVISED PRIORITY**
> ⚠️ CRITICAL: BrandedBy share mechanic = difference between $110K and $840K ARR at Month 18.
> This is the highest-leverage sprint in the entire ecosystem. Runs parallel to ZEUS-1.

- Brief: memory/brandedby_implementation_brief.md (ready)
- Pivot confirmed: Regular users first (AI Twin), celebrities later
- Domain: brandedby.xyz ✅

Sprint B1: Foundation (Supabase migration, auth, basic UI)
Sprint B2: AI Twin MVP (text-only avatar, character_state integration)
Sprint B3: Video pipeline + SHARE MECHANIC ← THE MOST IMPORTANT SPRINT
  - [ ] AI Twin video generation (SadTalker/Wav2Lip or Replicate)
  - [ ] Delivery screen: ONE button "Share on LinkedIn / TikTok"
  - [ ] Video: 15 seconds, user face, subtle "Made with BrandedBy" watermark
  - [ ] K-factor 0.40 target (viral coefficient)
  - [ ] Crystal redemption flow: Volaura crystals → BrandedBy queue skip
  - [ ] Monthly AI Twin refresh (AURA updated → new video → share again) = churn prevention

**Never-Revoke List (write now, enforce forever)** ← Added 2026-03-27
Based on Replika collapse analysis — these features once active for a user CANNOT be removed without 90-day notice + full refund:
- crystal_balance earned (never expires, never removed)
- verified_skills in character_state (once verified, baseline never removed)
- AURA tier achieved (baseline tier never decremented without user consent)
- Crystal purchases (queue skips valid until used, no expiry)

---

### ФАЗА 4: Testing + Security — PARTIALLY COMPLETE (merged into Sprints 3-8)

- [x] Security hardening: 7 CRITICAL+HIGH fixed, CSP, LLM timeout, rate limiting, auth error leak
- [x] RLS policies on all tables
- [x] Backend tests: 18 test files (pytest-asyncio) — auth, profiles, AURA, assessment, security, RLS
- [x] Frontend tests: 11 test files (Vitest + Testing Library)
- [x] LLM evaluation tests (mock Gemini in test_llm_mock.py)
- [ ] E2E tests (Playwright) ← NOT DONE — using Claude in Chrome + Preview instead
- [ ] Accessibility audit (WCAG 2.1 AA) ← NOT DONE formally
- [ ] Lighthouse scores ← NOT DONE
- [ ] Cross-browser testing ← NOT DONE
- [ ] PWA setup ← DEFERRED

---

### ФАЗА 5: Deploy + Launch — PARTIALLY COMPLETE (merged into Sprints 5-8)

**Infrastructure** ✅
- [x] Supabase project setup (production) — hvykysvdkalkbswmgfut
- [x] Run all migrations (27 total, 000001-000027)
- [x] Vercel deployment — volaura.app LIVE
- [x] Railway deployment — modest-happiness-production.up.railway.app LIVE
- [x] Custom domain: volaura.app (not .com — domain choice was CEO decision)
- [x] Environment variables set everywhere (Railway, Vercel, .env, GitHub Secrets)

**Pre-seed Data** ⚠️ PARTIAL
- [ ] 30-50 volunteer profiles (real friends) ← NOT DONE — seed.sql has test data only
- [ ] 3-5 organizations ← NOT DONE
- [ ] 3-5 past events ← NOT DONE
- [x] User journey tested manually multiple times

**Monitoring** ⚠️ PARTIAL
- [ ] Error tracking (Sentry/LogRocket) ← NOT SET UP
- [ ] Analytics events ← NOT SET UP
- [x] Supabase dashboard available
- [x] Railway logs available (get_runtime_logs via Vercel MCP)
- [ ] Uptime monitoring ← NOT SET UP

**Launch** 🔄 IN PROGRESS
- [x] LinkedIn post #1 published
- [ ] LinkedIn post #2 (in pipeline)
- [ ] LinkedIn post #3 (needs new angle — Antigravity rejected)
- [ ] TikTok, WhatsApp, HR букеты ← NOT STARTED

---

### ФАЗА 6: Post-Launch / Growth — BLOCKED (waiting for beta testers)

**Pre-requisites before Phase 6:**
- [ ] CSV bulk invite shipped (Sprint 9) — enables batch onboarding
- [ ] `supabase db push` for 3 pending migrations (CEO action)
- [ ] Email confirmation disabled in Supabase (CEO action)
- [ ] 30-50 real volunteer profiles seeded

**When unblocked:**
- [ ] Hotfix bugs from real usage
- [ ] Referral system activated
- [ ] First monthly league
- [ ] Streak tracking active
- [ ] Email lifecycle
- [ ] Week 1 metrics vs targets

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
