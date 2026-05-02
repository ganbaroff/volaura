# Feature Inventory — Ground Truth Audit 2026-04-18

Audited by: Atlas (OpenManus body, Session 118)
Method: file-path evidence only. No training-data inference.
Time: ~60 minutes scan + write.

---

## 1. VOLAURA (apps/web + apps/api)

### BUILT (user-reachable, end-to-end wired)
- `apps/web/src/app/[locale]/(auth)/login/page.tsx` — Google OAuth + email login, PKCE flow
- `apps/web/src/app/[locale]/(auth)/signup/page.tsx` — registration with onboarding
- `apps/web/src/app/[locale]/(dashboard)/assessment/page.tsx` — competency picker, 8 domains
- `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/page.tsx` — IRT adaptive question engine, zustand-persisted
- `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/complete/page.tsx` — results with radar chart
- `apps/web/src/app/[locale]/(dashboard)/aura/page.tsx` — AURA score page with reflection hook (useReflection)
- `apps/web/src/app/[locale]/(dashboard)/dashboard/page.tsx` — main dashboard with life feed + stats
- `apps/web/src/app/[locale]/(dashboard)/profile/page.tsx` — user profile with AURA badge
- `apps/web/src/app/[locale]/(public)/u/[username]/page.tsx` — public profile (shareable AURA card)
- `apps/web/src/app/[locale]/admin/page.tsx` — admin overview with 5 KPI scorecard + live feed (M1 shipped)
- `apps/web/src/app/[locale]/admin/grievances/page.tsx` — grievance admin UI (261 lines)
- `apps/api/app/routers/assessment.py` — /start, /answer, /complete, IRT 3PL + BARS + anti-gaming
- `apps/api/app/services/cross_product_bridge.py:262` — VOLAURA→MindShift event bridge, live
- `apps/api/app/services/ghosting_grace.py:139` — idempotent, respects kill-switch
- `supabase/migrations/` — 93 migrations applied, crystal_ledger + character_events + RLS on 46 tables

### PARTIAL (code exists, incomplete)
- `apps/web/src/app/[locale]/(dashboard)/brandedby/page.tsx` — page exists, shows ProductPlaceholder ("Coming soon")
- `apps/web/src/app/[locale]/(dashboard)/mindshift/page.tsx` — ProductPlaceholder only, no real integration
- `apps/web/src/app/[locale]/(dashboard)/discover/page.tsx` — TODO T1-2 punted: AuthGuard blocks unauth, no public teaser
- `apps/web/src/app/[locale]/(dashboard)/aura/contest/page.tsx` — page renders but contest mechanic backend absent
- `apps/api/app/services/video_generation_worker.py:302` — worker code exists, Azure/ElevenLabs keys missing (blocked)
- `apps/api/app/services/email.py` — service exists, no SES/Resend transport configured (blocked on AWS keys)
- `apps/web/src/app/[locale]/(dashboard)/eventshift/` — 3 pages written, behind feature flag, DB seeded, API wired but Vercel deploy blocked
- `packages/ecosystem-compliance/` — 4 tables migrated, Python+TS SDK exists, but automated_decision_log only written by skills.py (1 of 27 routers)
- `apps/api/app/services/atlas_voice.py:75` — voice module exists, used only by telegram_webhook
- `apps/web/src/hooks/queries/use-community-signal.ts` — hook exists, no visible UI wiring found

### CLAIMED-NOT-FOUND
- `packages/swarm/agents/` — EMPTY directory. Claimed "44 specialised Python agents" in identity.md, README, Techstars draft. Real count: 13 perspectives in autonomous_run.py + 51 skill markdown files
- Push notifications — no web_push/send_push in FastAPI code (only in .venv dependencies). Frontend has notification page but no service worker push handler found
- "Score decay over time" — claimed in press brief and multiple docs. Zero implementation: no cron, no decay function, no migration column for decay_at
- consent_events table writes — migration 20260415230000 created table, grep shows ZERO writes from any router (only skills.py writes automated_decision_log)
- human_review_requests — table exists, no reader route in admin.py, no queue consumer anywhere
- "44 agents" in LinkedIn/YouTube/TikTok marketing drafts — actual runtime count is 13 registered perspectives per autonomous_run.py:132-255

### PENDING (explicit TODO/FIXME/BACKLOG in code)
- `apps/web/src/app/[locale]/(dashboard)/discover/page.tsx:1` — "TODO T1-2 PUNTED to Phase 1 Week 3"
- `apps/web/src/app/[locale]/(dashboard)/life/page.tsx` — TODO markers for atlas_learnings integration
- `apps/api/app/routers/organizations.py` — TODO for org approval workflow enhancements
- `apps/api/app/routers/skills.py` — TODO markers for additional competency skill handlers
- `apps/web/src/hooks/queries/use-auth-token.ts` — TODO for token refresh edge cases
- `apps/web/src/hooks/queries/use-public-stats.ts` — HACK/TODO markers
- `apps/web/src/lib/api/client.ts` — TODO for retry logic improvements

---

## 2. MindShift (C:\Users\user\Downloads\mindshift)

### BUILT
- `src/features/focus/FocusScreen.tsx` — focus session with timer, Pomodoro-style
- `src/shared/hooks/useFocusRoom.ts:181` — full focus room logic with ambient audio
- `src/features/mochi/MochiChat.tsx` — AI chat agent (mochi-respond edge function backend)
- `src/features/economy/EconomyDashboard.tsx` — crystal economy visualization
- `src/features/community/CommunityScreen.tsx` — community feature with crystal-gated join
- `src/features/tasks/TasksPage.tsx` — task management with decompose-task AI
- `src/features/today/TodayPage.tsx` — daily dashboard
- `src/features/auth/AuthScreen.tsx` — auth with Supabase
- `src/features/calendar/DueDateScreen.tsx` — calendar with Google Cal sync (gcal-sync edge fn)
- `src/features/progress/ProgressPage.tsx` — progress tracking
- `src/features/settings/SettingsPage.tsx` — settings with GDPR cookie consent
- `supabase/functions/volaura-bridge-proxy/index.ts` — VOLAURA cross-product bridge endpoint
- `supabase/functions/` — 20 edge functions (excl _shared): focus, payments, GDPR, calendar, community, recovery

### PARTIAL
- `src/features/admin/AdminEconomyPage.tsx` — admin exists but unclear if wired in prod navigation
- `src/features/preview/PreviewScreen.tsx` — preview feature exists, scope unclear
- `src/features/audio/` — audio feature dir exists, likely ambient sounds integration
- `src/shared/hooks/useCalendarSync.ts` — hook exists, depends on gcal-store-token which requires OAuth consent

### CLAIMED-NOT-FOUND
- atlas_learnings consumption — VOLAURA writes to atlas_learnings table, MindShift grep shows zero reads from it. Bridge goes VOLAURA→MindShift via community-join + volaura-bridge-proxy, NOT through atlas_learnings
- Burnout detection / score — referenced in Cowork audit, no grep match for "burnout" in MindShift src/

### PENDING
- `src/app/useAuthInit.ts` — TODO markers for auth initialization edge cases
- `src/features/auth/AuthScreen.tsx` — TODO markers
- `src/shared/hooks/usePendingSessionRecovery.ts` — recovery logic with pending TODOs

---

## 3. Life Simulator (C:\Users\user\OneDrive\Desktop\BestGame\life-simulator-2026)

### BUILT
- `scripts/controllers/app_controller.gd` — autoloaded, initializes all subsystems
- `scripts/controllers/character_controller.gd` — 8 stats, serialization
- `scripts/controllers/event_queue_controller.gd` — priority event queue
- `scripts/controllers/career_controller.gd` — 5 careers with progression
- `scripts/controllers/relationship_controller.gd` — NPC memory system
- `scripts/controllers/idle_controller.gd` — passive income with upgrades
- `scripts/controllers/battle_pass_controller.gd` — 45-day seasons, 50 tiers
- `scripts/controllers/achievement_controller.gd` — 22 achievements
- `scripts/controllers/save_load_controller.gd` — 5 save slots
- `scripts/managers/api_client.gd` — VOLAURA API client with JWT login + character_state sync

### PARTIAL
- `scenes/menus/main_menu_simple.gd:9` — P0 BUG: VolauraAPIClient type not in scope on Godot 4.6.1 (parse-order issue). Game won't launch main scene
- `scripts/controllers/game_loop_controller.gd:21` — same VolauraAPIClient scope error cascades here
- VOLAURA character_events → Life Sim in-game events — api_client.gd reads state but character_events bus not consumed in game event logic

### CLAIMED-NOT-FOUND
- "Crystal economy in Life Sim" — CEO directive says crystals flow to LifeSim via same ledger. No grep match for crystal_ledger read in any .gd file. api_client.gd reads crystal_balance from VOLAURA but doesn't write to game currency

### PENDING
- Android export — guides written (ANDROID_EXPORT_STEP_BY_STEP.md etc) but no APK build output found

---

## 4. BrandedBy

### BUILT
- `apps/api/app/routers/brandedby.py` — 9 endpoints: /my-twin, /generation, /generations, CRUD
- `apps/api/app/services/brandedby_personality.py` — AI personality generation service
- `apps/api/app/schemas/brandedby.py` — Pydantic schemas for twin + generation
- `apps/web/src/hooks/queries/use-brandedby.ts` — useMyTwin() + useGeneration() hooks

### PARTIAL
- `apps/web/src/app/[locale]/(dashboard)/brandedby/page.tsx` — shows ProductPlaceholder, not functional UI
- `apps/web/src/app/[locale]/(dashboard)/brandedby/generations/[id]/page.tsx` — viewer page exists (was 419 lines per Cowork audit) but main page is placeholder
- Video generation — `apps/api/app/services/video_generation_worker.py:302` exists but blocked on Azure/ElevenLabs API keys

### CLAIMED-NOT-FOUND
- BrandedBy consuming Atlas context for twin personality — brandedby_personality.py generates personality but doesn't read atlas_learnings or user's cross-product context

---

## 5. ZEUS / Swarm (packages/swarm + .claude/agents/)

### BUILT
- `packages/swarm/autonomous_run.py` — PMAgent orchestrator, 13 perspectives across 4 waves
- `packages/swarm/agent_hive.py` — agent configuration + registered_perspectives_count() SSOT
- `packages/swarm/prompt_modules/` — ecosystem-map, skill files loaded at runtime
- `memory/swarm/skills/` — 51 skill markdown files, consumed by autonomous_run.py
- `.github/workflows/aura-reconciler.yml` — 10-min cron, AURA sync
- `.github/workflows/error-watcher.yml` — 10-min cron, nociceptive monitoring (just shipped Session 118)
- `.github/workflows/swarm-proposal-cards.yml` — hourly CEO proposal digest
- `apps/api/app/services/swarm_service.py` — FastAPI integration for /admin/swarm

### PARTIAL
- `packages/swarm/agents/` — EMPTY directory. Zero runtime agent files despite docs claiming 44
- `packages/swarm/archive/emotional_core.py` — 5D emotional engine exists in ARCHIVE, not activated
- `packages/swarm/archive/atlas_proactive.py` — proactive loop in archive, not in active code
- Error watcher — just shipped, first cron run failed on import (fix pushed dc4aa80, awaiting next tick)

### CLAIMED-NOT-FOUND
- "44 specialised Python agents" — found in 60+ files across repos. Real count: 13 perspectives + 51 skill files + 0 agent runtime files. identity.md already self-corrected this Session 112
- Agent autonomy / self-improvement — ANUS/ZEUS repos explored, OpenManus mapped as potential skeleton, but zero autonomous improvement loop running in production
- LoRA training for Atlas voice — mentioned in OPUS-47-NIGHT-HANDOFF.md, model.safetensors files exist in models/ (5GB), but training pipeline broken (commit 148a3c1)

---

## BLIND SPOTS

### Cannot verify from files alone
- **Deployed state vs code state**: Vercel frontend is 3+ commits behind due to 100/day deploy limit + module_not_found build error. Railway backend may also be stale
- **Supabase runtime data**: 107 auth.users vs 34 profiles (73 orphans backfilled in G2.5), but actual row health requires SQL queries not file reads
- **MindShift production**: separate Supabase project (awfoqycoltvhamtrsvxk), couldn't verify edge function deployment status or user count
- **Assessment engine accuracy**: IRT theta convergence, anti-gaming detection rates — requires running the engine with test data, not code reading
- **Energy mode visual rendering**: 33 files reference useEnergyMode, but visual output requires browser testing across Full/Mid/Low
- **EventShift Railway services**: eventhisft-production.up.railway.app was 200 earlier today, but whether new VOLAURA EventShift router deployment is live on Railway requires deploy log check

### Follow-up audit needs
- Supabase MCP: row counts for assessment_sessions, character_events, crystal_ledger, atlas_learnings
- Vercel deploy logs: why module_not_found persists (likely Node 24 vs pnpm workspace resolution)
- Railway deploy SHA comparison: code on disk vs what's running
- Browser E2E: signup → assessment → AURA → profile → public share path
- MindShift Play Store: current version, review status, crash rate

### Claim-vs-reality gap pathway
The "44 agents" drift originated in identity.md Session 93 (naming day), propagated unchecked through 60+ docs by multiple Atlas instances over 3 weeks. Session 112 caught it, Session 118 (this audit) confirmed 13 as ground truth. Root cause: identity.md was treated as canonical without periodic verification against packages/swarm/autonomous_run.py. Structural fix shipped: registered_perspectives_count() in __init__.py as single source of truth.

---

## TOTALS (across ecosystem)

| Bucket | VOLAURA | MindShift | LifeSim | BrandedBy | ZEUS | Total |
|--------|---------|-----------|---------|-----------|------|-------|
| BUILT | 15 | 13 | 10 | 4 | 8 | **50** |
| PARTIAL | 10 | 4 | 3 | 3 | 4 | **24** |
| CLAIMED-NOT-FOUND | 6 | 2 | 1 | 1 | 3 | **13** |
| PENDING | 7 | 3 | 1 | 0 | 0 | **11** |
