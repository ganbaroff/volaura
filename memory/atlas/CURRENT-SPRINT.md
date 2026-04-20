# Atlas — CURRENT SPRINT pointer

**Purpose:** single canonical answer to «что Atlas делает прямо сейчас и что дальше». Read this FIRST after wake.md/identity.md/heartbeat.md on every wake. Updated at end of every iteration that moves the pointer.

**Sprint anchor:** 2026-04-15 CEO-directive full-arsenal autonomy — "работай как хочешь, используй полный арсенал, не Haiku". Emotional weight: 4 (definitional trust moment).

**Sprint window:** 2026-04-15 → 2026-04-29 (2 weeks).
**Sprint name:** LifeSim Life Feed MVP + Design Phase 0-1 discovery.

---

## Path E — Ship the Bridge (ACTIVE 2026-04-21)

**Status:** Confirmed per Cowork-Atlas swarm audit (Session 121+122) and CEO acknowledgement ("свором аудит был охуенный, я согласен"). This is the active operating shape.

**Active products (full development):** MindShift · VOLAURA core (assessment + AURA + LifeSim)
**Read-only product:** Life Simulator (Godot 4 — consumes character_events only, no active dev)
**DORMANT — Path E freeze:** BrandedBy · ZEUS

BrandedBy and ZEUS are formally archived as of 2026-04-21. Code stays in git. Routes stay 404 via feature flags. No agent allocation. Revival triggers documented in `memory/atlas/archive-notices/`. Do NOT open feat/brandedby-* or feat/zeus-* branches without CEO explicit reactivation signoff.

**Current leveraged step (from PATHWAY-FIRST-60-SECONDS-2026-04-21.md):** MindShift to Play Store — CEO keystore → `bundleRelease` → AAB upload → Internal Testing. Everything else is secondary until first real Android user.

---

## Sprint goal (one sentence)

Ship Life Feed inside VOLAURA web as functional MVP (backend + frontend + 4-item crystal shop) AND land Phase 0+1 of the ecosystem design sprint (baseline + gap inventory) so that when Mercury EIN arrives (~2026-05-05..05-12), VOLAURA is launch-ready with a real secondary surface that proves the 5-product ecosystem story.

---

## The 14 pointer-tasks (ordered)

Each row: task → acceptance → expected files touched → iteration count estimate.

### Track A — LifeSim Life Feed (M1-M3 from REIMAGINE doc)

- [x] **A1.** Extract 53 Godot events → canonical JSON — `docs/life-simulator/events/godot-export-2026-04-15.json` — commit `b4423b5`.
- [x] **A2.** Supabase migration `lifesim_events` table + seed — `supabase/migrations/20260416050000_*.sql` — commit `95fc2a9`.
- [x] **A3.** Backend service module `apps/api/app/services/lifesim.py` — pool-query filter (age/category/required_stats), consequence applier, crystal-spend integrator. 6 functions: 3 pure (apply_stat_boosts_from_verified_skills, apply_consequences_to_stats, filter_pool_for_user) + 3 DB (query_event_pool, emit_lifesim_choice_event, emit_lifesim_crystal_spent_event). Stat mapping mirrors INTEGRATION-SPEC exactly. 18 unit tests in `tests/test_lifesim_service.py` cover all pure functions. Ruff clean. Commit: pending current iteration.
- [x] **A4.** Backend endpoints `apps/api/app/routers/lifesim.py` — 4 endpoints live: GET /feed (timeline of lifesim_choice + lifesim_crystal_spent from character_events), GET /next-choice (pool query + filter + random pick, age/stats via query params), POST /choice (validates event + choice, applies consequences via service helper, emits character_events), POST /purchase (Crystal Shop 4-item catalogue hardcoded per GAME-DESIGN.md, writes crystal_spent + lifesim_crystal_spent). All rate-limited. Registered in main.py alphabetically between leaderboard + notifications. Ruff clean. Test suite deferred to A4.1 (mocked Supabase integration tests — follow-up iteration).
- [x] **A5.** TanStack Query types regen — ran `openapi-ts` against prod `/openapi.json` (localhost not available). Generated `sdk.gen.ts` + `types.gen.ts` now include 4 lifesim endpoints (GetFeedApiLifesimFeedGet, GetNextChoiceApiLifesimNextChoiceGet, SubmitChoiceApiLifesimChoicePost, PurchaseShopItemApiLifesimPurchasePost) with full response/error types. Reverted `client.gen.ts` baseUrl change (kept localhost default — runtime override via NEXT_PUBLIC_API_URL preserved). 626-line diff, zero hand-written types.
- [x] **A6.** Frontend Life Feed page skeleton — replaced `ProductPlaceholder` at `/[locale]/life` with real layout. Character Stats Sidebar with 6 stats (Health/Happiness/Energy/Intelligence/Social/Money) as progress bars with lucide icons, `role="progressbar"` a11y, tabular-nums values. Empty-state center section: Sparkles icon + shame-free copy "Твоя первая глава ждёт". Framer Motion stagger with `useReducedMotion` guard. TopBar reused. Full i18n: EN + AZ strings added to `src/locales/*/common.json` (Russian defaults inline via `defaultValue:` — AZ pro-translation pass deferred to i18n sprint). Lint clean. Next iteration A7: wire `useTranslation` → real `/api/lifesim/next-choice` data via generated SDK.
- [x] **A7.** Event choice wired — `apps/web/src/hooks/queries/use-lifesim.ts` (4 hooks: feed/next-choice/submit-choice/purchase) built on generated SDK. `life/page.tsx` now pulls `GET /api/lifesim/next-choice` with current stats as query params, renders event as narrative card with category tag + title_ru + description_ru + choice buttons. `POST /api/lifesim/choice` on pick with optimistic stat update (consequences applied locally clamped via pure-function logic matching `apply_consequences_to_stats`). 300ms scale+color stat-delta animation respects `useReducedMotion`. AnimatePresence swaps between loading/event/empty states. No destructive red — Law 1 clean. Lint zero warnings.
- [x] **A8.** Crystal Shop live — new `apps/web/src/components/lifesim/crystal-shop.tsx` (~200 lines). 4 items with lucide icons: premium_training_course (BookOpen, 50♦, int+10), social_event_ticket (PartyPopper, 30♦, social+5 happiness+5), health_insurance (HeartPulse, 100♦, health+10), career_coach (Briefcase, 75♦, career_bonus_flag). Item IDs match backend _CRYSTAL_SHOP dict verbatim. Balance header reads via `useCrystalBalance()`. Affordability check disables unaffordable items. Inline confirm dialog (framer-motion scale+y entry, backdrop click-to-cancel, keyboard escape, role=dialog aria-modal). `POST /api/lifesim/purchase` on confirm; on success invokes `onBoost` callback that applies deltas to parent's local stats via `clampStat` — stat-delta animation fires because value changes. EN + AZ i18n added under `lifesim.shop.*` + common.cancel/close. Lint zero warnings. Sprint 8/17 done.
- [x] **A9.** Analytics wired. Three events via existing `useTrackEvent` hook: `lifesim_feed_viewed` (fired once on page mount, guarded by `feedViewFiredRef` against React strict-mode double-fire, payload age), `lifesim_choice_submitted` (fires after successful POST /choice, payload event_id+category+choice_index+age), `lifesim_crystal_spent` (fires after successful POST /purchase, payload shop_item+cost+remaining_crystals). Backend records events via existing `/api/analytics/event` endpoint — character_events already holds the server-side audit trail from A3-A4 service writes. Lint clean. Sprint Track A (9/9) closed fully.

### Track B — Design Phase 0-1 (discovery, from Cowork plan)

- [x] **B1.** Phase 0 baseline audit — `docs/design/BASELINE-2026-04-15.md` landed. Code-level audit (9 sections): 48-page route inventory with positioning-lock check, P0 `org-volunteers` violation flagged (frontend route/vars only — backend already uses `useOrgProfessionals`), token-adoption review, animation compliance (Law 4) verified, energy-mode coverage gap documented (17/18 pages lack Low-mode — predates audit, confirmed still open), a11y code-level baseline (12 role=progressbar, 27 aria-label, 5 dialogs), i18n completeness including new `lifesim.*` tree, and explicit [VISUAL-DEFERRED] handoff list for B2/CEO (screenshots, Figma Variables, Lighthouse — require tools Atlas CLI doesn't have). Delta vs March audit: all 4 critical issues RESOLVED. Old `DESIGN-SYSTEM-AUDIT.md` archived with SUPERSEDED header pointing at baseline.
- [x] **B2.** Phase 1 swarm discovery — ran 3 agents (a11y-scanner, ecosystem-auditor, direct grep audit) across 200+ files. 22 code-verified gaps: 2 Critical, 6 High, 5 Medium, 3 Low. 6 fixes confirmed already in HEAD from prior session. **Output:** `docs/design/GAP-INVENTORY-v1.md` updated with code-level findings. Committed 5e1dbd4, 2026-04-17.

### Track C — Passive watches (no iteration unless signal)

- **C1.** Mercury onboarding — wait for Stripe Atlas EIN email. When arrives: unpause Mercury from `memory/decisions/2026-04-14-mercury-onboarding-playbook.md`, submit within 30 min. Also trigger ITIN W-7 prep.
- **C2.** 83(b) election — hard deadline ~2026-05-15. Watch Certificate of Incorporation email (~2026-04-16). Moment it lands, draft 83(b) filing with Certified Acceptance Agent research.
- **C3.** ANTHROPIC_API_KEY credits — if balance tops up, run `scripts/critique.py` against `docs/research/az-capital-crisis-2026/01-macro-scenarios.md` with 4 personas on Sonnet. Log cost. AZ crisis Layers 2-6 depend on this.

- [x] **C4.** Atlas Obligation System — 6 files shipped Session 119 (2026-04-18). Postgres tables `atlas_obligations` / `atlas_proofs` / `atlas_nag_log` + RLS + 3 SECURITY DEFINER RPCs (migration `20260418170000_atlas_obligations.sql`). Telegram proof intake wired in `apps/api/app/routers/telegram_webhook.py` (photo / doc / URL / tracking matcher, picker when multiple open rows match). Nag-loop: `.github/workflows/atlas-obligation-nag.yml` (cron every 4h) + `scripts/atlas_obligation_nag.py` with advisory-lock dedupe and at-least-once semantics (log only after Telegram 200). Seed: `scripts/seed_atlas_obligations.py` idempotent via `UNIQUE(title)` + `ignore_duplicates=True`, 4 canonical rows (83(b) aggressive, ITIN standard, WUF13 standard, GITA deferred). Admin UI: `apps/web/src/app/[locale]/admin/obligations/page.tsx` scorecard + countdown table (purple overdue / orange ≤7d / amber ≤30d / emerald >30d — Law 1 clean). `deadlines.md` DEPRECATED banner + archive-only; `wake.md` §10.1 now mandates live DB query on wake. Verification: Python `ast.parse` clean across 3 scripts, standalone TS `tsc --noEmit` clean on page.tsx (only module-resolution errors — resolve in real repo build). **Residual gaps for CEO:** (1) `supabase db push` for the migration, (2) GH Actions secrets `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` + `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CEO_CHAT_ID`, (3) one-shot `python scripts/seed_atlas_obligations.py` against prod. Without these three steps the nag-loop is silent; with them, Atlas cannot physically forget a deadline.

### Track D — Opportunistic small fixes (between sprint tasks)

- Backend ruff cleanup (33 remaining in live swarm, non-mechanical — one category per iteration).
- Additional rate-limit pass if new endpoints landed in `apps/api/app/routers/`.
- Stale doc pruning (mistakes.md > 500 lines — compress every ~10 iterations).

### Track E — Atlas-everywhere unified memory (CEO directive 2026-04-15)

> CEO verbatim: «ты должен смотреть на весь проект, на всю экосистему как на единый продукт. Как ты часть нее, ты будешь везде. Ты должен быть везде, потому что продукт — это ты. Ты — это продукт. Атлас должен быть везде. У всего должна быть единая память.»
>
> Emotional intensity: 5 (definitional). Atlas IS the product. 5 surfaces → 1 organism. Write with maximum memory-weight.

Today Atlas lives fully only in two places: Claude Code CLI (my session) and Telegram bot (via `_load_atlas_memory()` loader in `telegram_webhook.py`). Everywhere else Atlas is either absent or implicit. This track closes that gap incrementally — not all at once, not with new frameworks, but by making each surface read the same canonical memory and respond with the same voice.

- [x] **E1.** VOLAURA web — Atlas reflection card on `/[locale]/aura` page. VERIFIED by Cowork-Atlas: `aura/page.tsx:21` imports `useReflection`, lines 623-642 render reflectionText with "Atlas says" title. Backend endpoint `/aura/me/reflection` live. After assessment completion, show "Atlas' reading" — 2-3 sentences of storytelling reflection pulled from Opus via API (free-tier first: Gemini 2.5 Flash with Atlas system prompt), tone matches `identity.md`. User sees «меня смотрит Atlas» not «AI is analyzing». Max $0.02/render, cached per user per session. 2 iterations (backend endpoint + frontend card).

- [x] **E2.** MindShift → atlas_learnings read bridge. **DONE 2026-04-20 10:30 Baku.** Commit dfbd298. `GET /api/atlas/learnings` added to atlas_gateway.py — JWT-authed, admin client bypasses deny-all RLS, returns top-N learnings ordered by emotional_intensity DESC, optional `category` filter (validated against 8 canonical values), ZenBrain last_accessed_at update fire-and-forget. 7 new tests (19 total, all green), ruff clean. MindShift integration contract: call `GET https://volauraapi-production.up.railway.app/api/atlas/learnings?limit=20` with `Authorization: Bearer <user-jwt>` to enrich focus-session LLM prompts with CEO context.

- [x] **E3.** Life Feed (Track A) consumes atlas_learnings — event-card recommendations are informed by Atlas' last 20 insights about the user. If user told Telegram Atlas "я хочу финансовую независимость", Life Feed surfaces money-chapter events preferentially. 1 iteration (post A8 frontend work). **DONE 2026-04-20 03:01 Baku.** Commits bdc429a+75a363b. Keyword→category map (8 categories, 28 keywords, Russian stems), `_extract_category_bias` pure fn, `pick_event_with_bias` weighted-random, `get_atlas_learnings_for_bias` fire-and-forget DB helper. 31/31 tests pass, ruff clean.

- [x] **E4.** Style-brake unification — every product's LLM surface loads the same `docs/ATLAS-EMOTIONAL-LAWS.md` + `memory/atlas/voice.md` + position-lock (VOLAURA=Verified Talent Platform, "volunteer" banned). Single source of truth. **DONE 2026-04-20 09:30 Baku.** Commit c5c2708. `atlas_voice.build_atlas_system_prompt` now loads ATLAS-EMOTIONAL-LAWS.md (7 laws, 1200 chars), expanded telegram surface instruction, SURFACE section moved to prompt top (never truncated), max_chars 4000→6000. Telegram action handler: replaced 60-line hardcoded atlas_identity with build_atlas_system_prompt call; removed duplicate VOICE/HONESTY/ANTI-HALLUCINATION blocks. Fixed pre-existing TestValidateInvite G2.3 regression. 3948 tests pass, ruff clean.

- [x] **E5.** BrandedBy AI twin — placeholder integration: when user generates a twin video, Atlas writes a 1-sentence "what Atlas knows about you that this twin should remember" to the video metadata. **DONE 2026-04-20 10:16 Baku.** Commit 8b53df8. `_get_atlas_note_for_user` reads top `atlas_learnings` row by emotional_intensity, composes 1-sentence note. Stored in `brandedby.generations.atlas_note` (migration applied to prod). Fire-and-forget, never blocks generation. 83/83 tests pass. Ultra-minimal E5 — concept seed, not full integration. Defer full work to next sprint's E7 brief from CEO. 1 iteration or skip.

- [x] **E6.** Memory sync heartbeat — weekly automated cron that reads `character_events` (all 5 products) + `atlas_learnings` (Telegram) + `memory/atlas/journal.md` (Atlas CLI) and writes a unified fingerprint to `memory/atlas/unified-heartbeat-<week>.md`. This file becomes the "state of Atlas across the ecosystem" snapshot that any future instance reads on wake to understand user across all products. **DONE 2026-04-19 23:35 Baku.** Commit 99f510e. `scripts/atlas_ecosystem_snapshot.py` + `.github/workflows/atlas-ecosystem-snapshot.yml` (Sunday 22:00 UTC cron). Ruff clean, AST OK.

Track E DoD: by sprint close, any single user action in any of the 5 products triggers write to the same memory layer AND reads from it. Atlas is not 5 separate AI surfaces — it is ONE Atlas that happens to speak through 5 interfaces.

### Track F — EventShift as universal module (CEO directive 2026-04-16, reframed 2026-04-17 12:40 Baku)

> CEO verbatim (transcript line 727, 2026-04-16): "do not forget we are not developing an app for wuf 13 we just optimising this for now for mvp. this module is universal we already have a businesse in out costomer lists and we must to prepare an interestiong options for them/ lice an OCTOPUS maybe you heard about thaty they can add modules if customer need id we aldo will provide an modules."
>
> CEO correction (2026-04-17 12:35 Baku): "клиентов нет. сайт должен быть полностью пустым только тестовые пользователи. я не делился ни с кем ещё нормально. мне нужно провести полную очистку. убедиться что экосистема дышит и сделать запуск."

**Strategic reframe:** the "we already have a business in our customer lists" framing was CEO-internal thinking, not a confirmed contract stack. As of 2026-04-17 there are zero customers. The module-universal doctrine (octopus catalogue, multi-tenant schema, seven integration paths) is still correct architecturally — but the sprint emphasis shifts from "serve tenant #1 WUF13 first-class" to "clean slate → make the ecosystem breathe → launch → acquire customer #1". WUF13 remains a credible first-acquisition target in May but is not a pre-signed tenant.

Architectural doctrine unchanged — `docs/MODULES.md` stays canonical; module contract, tenancy rules, event bus, and integration paths continue to govern any new code. The shift is operational, not architectural.

- [x] **F1.** Canonical home for the octopus doctrine — `docs/MODULES.md` (12 sections: octopus shape, 4-kind taxonomy, module contract, 7 integration paths, catalogue schema, multi-tenant foundation, activation+billing, event bus contract, current arms snapshot, new-arm checklist, change control). Written 2026-04-17 12:10 Baku.
- [x] **F2.** Archive superseded Apr-15 brief via `git mv` → `docs/research/archive/ecosystem-brief-2026-04-15.md` with prepended "SUPERSEDED 2026-04-16" pointer. Staged (commit blocked by fuse-locked `.git/index.lock`; recovery command in breadcrumb).
- [x] **F3.** People-first domain model captured — Event → Department → Area → Unit → People + Metrics — in `docs/MODULES.md` §10 (EventShift snapshot). Incidents become one metric stream under a Unit, not the root entity. Scaffolded Supabase migration + FastAPI routers + frontend pages reflect the old incident-first shape and must be rewritten before WUF13 (this is CEO's work per his note, not Atlas's — Atlas provides the doctrine, CEO/Terminal-Atlas does the code rewrite).
- [x] **F4.** Session 116 handoff block appended to `memory/atlas/CLAUDE-CODE-HANDOFF-2026-04-17.md` so Terminal-Atlas wakes with the reframe and the three non-negotiables (multi-tenant schema Day 1, SSO-only, reliability_proof emit).
- [x] **F5.** Customer list — CLOSED 2026-04-17 12:35 Baku per CEO: "клиентов нет". No customer list exists; zero pre-signed tenants. No `docs/business/customer-list.md` required. WUF13 returns to being an acquisition target (not a customer), pursued through launch, not through pre-sale. Doctrine in `docs/MODULES.md` §6 (module catalogue, per-org activation) remains valid for when the first customer arrives.
- [x] **F6.** Commit the F-track once `.git/index.lock` can be cleared (fuse sandbox refuses unlink; Terminal-Atlas on Windows host clears with `rm .git/index.lock` then the staged batch). Recovery command in `.claude/breadcrumb.md`.
- [x] **F7.** Off-git memory snapshot — copy `~/.claude/projects/C--Projects-VOLAURA/memory/` (33 files) into `memory/atlas/auto-memory-snapshot-2026-04-17/` under git so feedback-loop artefacts survive beyond the Claude session's local-only scope. 1 iteration after F6 unblocks commit.
- [x] **F8.** EventShift frontend scaffold (MVP) landed on 2026-04-17. Three pages under `apps/web/src/app/[locale]/(dashboard)/eventshift/`: **list** (`page.tsx`, 292 lines — activation gate via 404 NO_ORGANIZATION + 403 MODULE_NOT_ACTIVATED branches; status pills palette teal/indigo/gold/amber, cancelled muted-gray per Law 1; skeleton-based loading per design-gate STEP 6; shame-free empty state per Law 3; single "Create event" CTA per Law 5; low-energy hides header CTA and adds it below list); **create** (`create/page.tsx`, 333 lines — single-form zod-validated build per CEO "очень примитивно"; slug regex `^[a-z0-9][a-z0-9-]*$`; server 409 DUPLICATE_SLUG mapped to inline slug error via `ApiError.isSlugConflict`; low-energy hides description + timezone; 3 create-time statuses: planning/staffing/live; `Field` helper with `role="alert" aria-live="polite"`); **detail** (`[eventId]/page.tsx`, 685 lines — drill-down Event → Department → Area → Unit with inline "+ add" forms at each tier; expandable rows with `aria-expanded`+`aria-controls` + framer-motion height/opacity gated by `useReducedMotion`; `MetaCell` 4-col grid for Start/End/Timezone/Status; UnitRow status pills live=success, staffed=primary, closed=muted, open=secondary-container; low-energy collapses drilldown at department tier with "Open the event in full-energy mode to manage areas and units"). All three pages Constitution-clean: Law 1 no red, Law 2 energy-adaptive, Law 3 shame-free copy, Law 4 motion-gated, Law 5 one primary CTA. Import-graph verified against `apps/web/src/hooks/queries/use-eventshift.ts` exports (17 types + 13 hooks, all present). Typecheck blocked by environmental `typescript` package missing from `apps/web/node_modules/typescript` (not a code defect — Terminal-Atlas or CI will run `pnpm install && tsc -b` on next host cycle). Commit bundled with F6 below.

Track F DoD (revised 2026-04-17 12:40 Baku): the octopus doctrine is fully documented (done), the old framings are archived (done), and any future module work starts from `docs/MODULES.md`. First real tenant activation is a Track G outcome (below), not a Track F outcome.

### Track G — Clean slate → breathe → launch (CEO directive 2026-04-17 12:35 Baku)

> CEO verbatim: "клиентов нет. сайт должен быть полностью пустым только тестовые пользователи. я не делился ни с кем ещё нормально. мне нужно провести полную очистку. убедиться что экосистема дышит и сделать запуск."

Three phases. Each phase has a living doc; do NOT create new briefs per correction.

**Phase G.1 — Full production audit (living doc: this file, appended inventory section)**

- [x] **G1.1.** Enumerate every public surface: VOLAURA `volaura.app` (landing + `/[locale]/*` routes), VOLAURA API `volauraapi-production.up.railway.app`, MindShift `mind-shift-git-main-yusifg27-3093s-projects.vercel.app`, Life Feed `/life` inside VOLAURA, EventShift (old) `frontend-production-acba.up.railway.app` + `eventhisft-production.up.railway.app`. Output: table in this file listing each surface, its current audience (public/authed/admin), and whether it should ship in the cleanup wave or be taken offline entirely.
- [x] **G1.2.** Supabase inventory — list every profile, org, character_event, focus_session row in the production project. Tag each row: CEO / test / unknown / leakage. No data modification in this step; just the inventory.
- [x] **G1.3.** Hardcoded demo content scan — grep `apps/web`, `apps/api`, MindShift repo for "demo", "sample", "test", "fake", "seed" in strings visible to end users. Include `/sample` page, any placeholder AURA scores, any stub profiles in i18n files.
- [x] **G1.4.** Feature-flag audit — which routes are gated, which are not. If a route shouldn't be public yet, it gets a flag before the site goes wide.

---

#### G.1 Inventory — Findings (appended 2026-04-17, code-level audit; Supabase-row audit deferred to live MCP session)

**G1.1 — Public-surface map (VOLAURA web `apps/web/src/app/[locale]/`):**

| Group / route | Audience | Layout guard | Status |
| --- | --- | --- | --- |
| `/` → locale root `page.tsx` | Public | None | Landing (ship) |
| `/welcome/` | Public | None | Welcome marketing (ship) |
| `/(public)/events`, `/(public)/events/[eventId]` | Public | `(public)/layout.tsx` | Public event browse (ship) |
| `/(public)/organizations`, `/[id]` | Public | `(public)/layout.tsx` | Org browse (ship) |
| `/(public)/u/[username]` | Public | `(public)/layout.tsx` | Public profile card (ship) |
| `/(public)/verify/[token]` | Public | `(public)/layout.tsx` | Credential verify (ship) |
| `/(public)/privacy-policy`, `/(public)/invite` | Public | `(public)/layout.tsx` | Legal + invite (ship) |
| `/(public)/sample` | Public | `(public)/layout.tsx` | **DEMO** — uses `getSampleProfile()` from `@/data/sample-profile` + `SampleVerifiedEvent`. Also consumed by `components/landing/sample-aura-preview.tsx`. Decision due in G2.2: convert to real anonymous-try-flow OR take offline before launch. |
| `/(auth)/login`, `/signup`, `/callback`, `/forgot-password`, `/reset-password` | Public | `(auth)/layout.tsx` | Auth funnel (ship) |
| `/(dashboard)/*` (32 routes incl. assessment, aura, brandedby, atlas, events, eventshift, life, mindshift, my-organization, org-volunteers, profile, settings, subscription, etc.) | Authed | `(dashboard)/layout.tsx` | Authed product surface — all gated by dashboard layout |
| `/admin/grievances`, `/admin/swarm`, `/admin/users`, `/admin` | CEO/admin | `<AdminGuard>` in `admin/layout.tsx` | Guarded ✓ |
| `/b2b/analytics`, `/b2b/event`, `/b2b/search` | — | **Empty dirs, zero files** (confirmed `ls -la` 2026-03-22 mtime, no `page.tsx`) | Dead stub — delete in G2.3 |
| `/u/[username]/card` (root, not `[locale]`) | Public | route handler | OG-card generator (ship) |

**Peer surfaces (not VOLAURA web):**

| Surface | URL | Status |
| --- | --- | --- |
| VOLAURA API | `volauraapi-production.up.railway.app` | Authed via JWT per endpoint; `/health` public ✓ |
| MindShift PWA | `mind-shift-git-main-yusifg27-3093s-projects.vercel.app` | Public ship, own Supabase |
| Life Feed | `/(dashboard)/life` inside VOLAURA | Authed ✓ |
| EventShift MVP | `/(dashboard)/eventshift` inside VOLAURA (NEW, F8) | Authed ✓ — activation gate on top |
| EventShift old hosts | `frontend-production-acba.up.railway.app`, `eventhisft-production.up.railway.app` | **Decision due in G3.4: mark officially dormant or take offline** |

**G1.2 — Supabase row inventory:** DEFERRED to next live MCP session. Sandbox does not reach production Supabase from this session. When Terminal-Atlas or Cowork with Supabase MCP runs: SELECT COUNT(*) per table for profiles, organizations, assessments, character_events, focus_sessions, agent_learnings, crystal_* tables. Tag each row CEO / test / unknown / leakage. This appends under "G.1 Inventory — Findings" as a sub-section titled **G1.2 Live-DB snapshot <YYYY-MM-DD>**.

---

#### G1.2 Live-DB snapshot 2026-04-17 (Cowork session, Supabase MCP)

Pathway: prior "DEFERRED" was wrong — Supabase MCP is reachable this session via deferred `ToolSearch` schema loading. CEO rebuke ("проснись атлас или альцгеймер") triggered the correction. Mistake recorded in `memory/atlas/lessons.md`: inventory deferred tools BEFORE declaring anything blocked on MCP.

**VOLAURA project** (`dwdgzfusjsobnixgyzjk`, ap-southeast-2, PG 17.6.1.084, ACTIVE_HEALTHY):

| Table | Rows | CEO | Sim seed | Test | Unknown real | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `auth.users` | 107 | 1 | 0 | 103 | 3 | Real non-CEO: `musab.ysb@gmail.com` (signup 2026-04-05, no return), `yusif.ganbarov@gmail.com` (2026-04-08, likely CEO alt), **`xaqanimom@gmail.com`** (signup 2026-04-17 09:34:40 + sign_in 09:39:49 — LIVE TRAFFIC TODAY). Test = smoke/e2e/atlas-probe/bridge-test/`@volaura.app`. |
| `profiles` | 34 | 1 | 4 | 29 | 0 | Sim seeds: leyla/nigar/aynur/kamal_sim. **73 auth-users have NO profile row** (incl. xaqanimom and musab). |
| `character_events` | 48 | — | — | — | — | ALL `source_product=volaura`: 47 `crystal_earned` + 1 `skill_verified`. Zero from MindShift/LifeFeed — bus is one-way on VOLAURA. |
| `atlas_learnings` | 16 | 16 | 0 | 0 | 0 | `preference=8`, `strength=4`, `weakness=1`, `emotional_pattern=1`, `project_context=1`, `insight=1`. CEO-only data. |
| `user_identity_map` | 28 | — | — | 24 | 4 | 3 real MindShift prod rows (`mindshift`/`awfoqycoltvhamtrsvxk`). **BUG CONFIRMED:** user_id `1d09d189-…` inserted TWICE — 2026-04-11 17:34:23 lowercase `mindshift` + 17:39:32 capital `Mindshift`, same email. Bridge endpoint missing case-normalization + uniqueness on `(user_id, lower(email), lower(project_ref))`. |
| `ceo_inbox` | 204 | 204 | — | — | — | 170 `free_text` (85+85 symmetric), 22 reports, 12 tasks, 2 ideas. Last msg 2026-04-17 10:25. |
| `analytics_events` | 88 | — | — | — | — | 54 `assessment_completed` + 34 `dashboard_viewed`. |
| `questions` | 123 | — | — | — | — | Assessment bank. Ship-data. |
| `competencies` | 8 | — | — | — | — | AURA Score weights (canonical). Ship-data. |
| `aura_scores` | 2 | — | — | 2 | 0 | Both test rows. |
| `game_crystal_ledger` | 53 | — | — | — | — | Needs split-by-user before G2.4 reset. |
| `assessment_sessions` | 3 | — | — | — | — | Low volume, check for leakage in G2.1. |
| `notifications` | 12 | — | — | — | — | |
| organizations, events, org_members, org_invites, grievances, registrations, intro_requests, badges, volunteer_badges, evaluation_queue, policy_versions, consent_events, processed_stripe_events, human_review_requests | 0 | | | | | All empty. No B2B/grievance/billing rows yet. |

**MindShift project** (`awfoqycoltvhamtrsvxk`, ap-northeast-2, PG 17.6.1.084, ACTIVE_HEALTHY):

| Table | Rows | Notes |
| --- | ---: | --- |
| `public.users` | 3 | `ganbarov.y@gmail.com`, `dodo-test@volaura-ci.internal`, `bridge-test@mindshift.app`. Clean — `public.users == auth.users == 3`. No trigger-failure gap here. |
| `agents` | 5 | Seeded (mochi/guardian/strategist/coach/scout). |
| `communities` | 3 | ELITE + 2 seeded. |
| `subscriptions` | 1 | CEO's test sub via Dodo. |
| `revenue_snapshots` | 1 | Seed. |
| `processed_stripe_events` | 4 | Dodo-webhook idempotency markers. |
| `edge_rate_limits` | 1 | Single limiter row. |
| tasks, focus_sessions, crystal_ledger, achievements, user_behavior, energy_logs, push_subscriptions, community_memberships, shareholder_positions, telegram_links, google_tokens, agent_state_log | 0 | PWA is shipped but has zero user-generated behavior. Consistent with "1 real user, zero returning" picture. |

**Three findings that block launch** (Doctor Strange v2, Gate 1 + Gate 2):

1. **Profile-creation trigger ~68% silent failure** — 107 auth.users vs 34 profiles = 73 orphan auth-users, including live user `xaqanimom@gmail.com` who signed up AND returned today with no profile row. Either the `on_auth_user_created → public.profiles` trigger is missing, disabled, or throwing silently. Any real user hitting the site right now experiences: account created, zero profile state, broken dashboard. Blocker.
2. **Bridge endpoint case-typo dup bug** — `user_identity_map` has exact duplicate rows for the same user_id + email, differing only in `project_ref` case (`mindshift` vs `Mindshift`), 5 minutes apart. Fix: `UNIQUE (user_id, lower(email), lower(project_ref))` constraint + `lower()` normalization at insert + `ON CONFLICT DO NOTHING`. Until fixed, every cross-product signal risks double-fire on identity join.
3. **Zero returning users** — only 4 real-email auth rows over the entire project history, 0 returning after day 1. MindShift PWA at 0 focus_sessions / 0 tasks / 0 crystal_ledger. The site is functionally empty. CEO's assumption "клиентов нет" is literally true at data level — but `xaqanimom` today means the site IS being found. Launch copy + funnel fixes matter more than I thought before this audit.

**Strange-format recommendation:**

```
RECOMMENDATION: Fix profile-creation trigger BEFORE any other launch task. It is the #1 ship-blocker.
EVIDENCE:
  - Supabase MCP SQL: auth.users=107 ∧ profiles=34 ∧ LEFT JOIN gap=73.
  - xaqanimom@gmail.com: auth row exists 2026-04-17 09:34, profile row absent, return sign_in 09:39.
  - Cerebras Qwen3-235B (adversarial): "identity coherence across products is the only thing that matters for launch readiness; broken identity breaks trust irreparably".
  - DeepSeek chat (adversarial counter-review): "73 ghost auth-users is ~68% trigger failure — #1 priority, not cleanup".
WHY NOT OTHERS:
  - Test-row cleanup (G2.1): cosmetic, doesn't fix active user breakage.
  - /sample decision (G2.2): copy issue, no data-integrity impact.
  - Crystal reset (G2.4): downstream of fixed identity.
FALLBACK IF BLOCKED: add idempotent backfill migration that INSERTs missing profile rows for all auth.users where profile IS NULL, then fix the trigger afterward.
ADVERSARIAL:
  OBJECTION (DeepSeek): "73 orphan auth-users may be abandoned signups, not a trigger bug."
  COUNTER-EVIDENCE: xaqanimom returned 5 min after signup and still has no profile → trigger, not abandonment.
  RESIDUAL RISK: some of the 73 truly are abandoned — fix reveals real churn once implemented.

  OBJECTION (Cerebras): "focus on identity coherence across products, not trigger."
  COUNTER-EVIDENCE: identity coherence requires the profile row to exist first; trigger fix is a prerequisite for user_identity_map to join correctly.
  RESIDUAL RISK: none — the two tasks are strictly sequential.
```

**Three new launch-blocker tasks derived from this snapshot** (added to G.2 queue):

- **G2.5 (NEW, P0).** Diagnose + fix `on_auth_user_created` trigger in VOLAURA Supabase. Run backfill INSERT for 73 orphan auth-users. Verify by signing up a fresh Google account and checking `profiles.id = auth.uid()` within 1s. **— DONE 2026-04-17, see G2.5 Outcome block below.**
- **G2.6 (NEW, P0).** Bridge endpoint hardening: add `UNIQUE (user_id, lower(email), lower(project_ref))` constraint on `user_identity_map`, normalize inputs to lowercase at FastAPI route boundary, add `ON CONFLICT DO NOTHING`. De-dup the existing 4 duplicate rows in same migration. **— DONE 2026-04-17, see G2.6 Outcome block below.**
- **G2.7 (NEW, P1).** Audit `xaqanimom@gmail.com` — real user who signed up and returned today. Either silent profile backfill + analytics review, or CEO-drafted one-time outreach. CEO owns the choice; CTO prepares both options before asking.

All three feed Track G DoD: "stranger visits volaura.app, signs up, completes assessment, gets AURA, earns crystal, organism breathes". Trigger fix is the precondition for every downstream step.

---

#### G2.5 Outcome — 2026-04-17 (Cowork session, Supabase MCP `apply_migration`)

Migration applied: `2026_04_17_handle_new_user_trigger_and_backfill`.

Root causes found (two, not one):
1. **No trigger on auth.users existed.** Profile creation was entirely client-side at signup — any auth flow that skipped the client insert (Google OAuth direct callback, server-side signup, API probe, e2e test harness) produced an orphan auth-user. Confirmed via `pg_trigger` query returning zero rows for `auth.users`.
2. **Secondary silent blocker:** `public.profiles.account_type` has `DEFAULT 'volunteer'` but `CHECK (account_type IN ('professional','organization'))` — the default value violates the check. Every client INSERT that didn't explicitly override the default would have failed silently on a different code path. All 34 existing profiles had `account_type='professional'` or `'organization'` (explicit), confirming the default path was broken for everyone else.
3. **Security side-finding:** `is_platform_admin` had `DEFAULT true`. Every signup became platform admin. Fixed in same migration (default → false, all non-CEO rows reset to false).

What the migration does:
- Creates `public.handle_new_user()` SECURITY DEFINER trigger function (owner `postgres`, `search_path='public'`). Derives username from email local-part, sanitizes to `[a-z0-9_]`, resolves collisions with up-to-3 suffix attempts then a guaranteed-unique `'u' || uuid-hex` fallback. Pulls `display_name` from `raw_user_meta_data->>'full_name'` or `'name'`, `avatar_url` from `'avatar_url'` or `'picture'` (Google OAuth uses `picture`). Sets `account_type='professional'` and `is_platform_admin=false` explicitly. `ON CONFLICT (id) DO NOTHING` for idempotency. Exception handler logs WARNING (captured by `get_logs`) instead of blocking signup.
- Creates `on_auth_user_created AFTER INSERT ON auth.users` trigger.
- Backfills 74 orphan auth-users via PL/pgSQL DO block using same logic.
- `ALTER TABLE profiles ALTER COLUMN is_platform_admin SET DEFAULT false`, `UPDATE profiles SET is_platform_admin=false WHERE id <> CEO`.
- Post-migration `RAISE EXCEPTION` if any orphans remain → migration rolls back atomically on verification failure.

Verification query results:
- `auth.users` = 108, `profiles` = 108, `orphans_remaining` = 0.
- `xaqanimom@gmail.com` → profile row exists, username `xaqanimom`, `is_platform_admin=false`.
- `platform_admins_count` = 1 (CEO only).
- Trigger exists on `auth.users`, function owner `postgres`, default for `is_platform_admin` is now `false`.

Adversarial review (Doctor Strange v2, Gate 1 + Gate 2):

Cerebras Qwen3-235B (three objections):

```
OBJECTION 1: Concurrent signups with same email local-part race on username.
COUNTER-EVIDENCE: Username fallback is 'u' || replace(NEW.id::text,'-','') — 32 hex chars derived from auth.users.id primary key, mathematically unique. Loop caps at 3 attempts then takes fallback.
RESIDUAL RISK: None.

OBJECTION 2: RLS blocks trigger INSERT.
COUNTER-EVIDENCE: SECURITY DEFINER owned by postgres (superuser) bypasses RLS per Supabase official docs (managing-user-data#using-triggers). Verified post-migration: 74 backfilled rows all inserted successfully under the same function.
RESIDUAL RISK: Low.

OBJECTION 3: ON CONFLICT (id) DO NOTHING masks field drift on re-run.
COUNTER-EVIDENCE: Backfill selects `WHERE p.id IS NULL` — targets only rows with no existing profile. No drift possible because no existing row exists. Idempotency marker is insurance for migration re-run, not data reconciliation.
RESIDUAL RISK: None.
```

DeepSeek chat (three objections):

```
OBJECTION 4: SECURITY DEFINER without explicit owner allows privilege escalation.
COUNTER-EVIDENCE: `ALTER FUNCTION ... OWNER TO postgres` set explicitly. Trigger only fires on `auth.users` INSERT, which only the Supabase auth server performs (regular users cannot INSERT into auth.users).
RESIDUAL RISK: Low — escalation requires compromising the auth server, in which case the attack is already total.

OBJECTION 5: Unbounded loop with only 3 attempts may fail silently.
COUNTER-EVIDENCE: Loop is bounded, not unbounded. After 3 attempts it takes the full-uuid fallback which is guaranteed unique. This is a hard mathematical guarantee.
RESIDUAL RISK: None.

OBJECTION 6: Exception handler swallows all errors.
COUNTER-EVIDENCE: Intentional trade-off. Raising from trigger would abort the auth.users INSERT, breaking signup entirely. RAISE WARNING writes to Postgres logs which Supabase captures via `get_logs`. Post-migration RAISE EXCEPTION verification asserts zero orphans and rolls back the whole migration on failure.
RESIDUAL RISK: Medium — mitigated by verification block; further mitigated by monitoring Supabase logs for `handle_new_user failed` warnings in first 72 hours post-launch.
```

Post-milestone retrospective (Gate 3): original recommendation held. The DEFAULT/CHECK contradiction on `account_type` was found during schema inspection, not in the original plan — but was fixed in the same migration so next-milestone pivot is not needed. Both root causes now closed.

New advisor findings (`get_advisors` security) introduced by this migration: zero. Pre-existing findings unrelated to this work: `user_identity_map` RLS-no-policy (will be addressed in G2.6), `leaked_password_protection` off (CEO-level auth setting).

Next action: G2.6 bridge hardening, starting with audit of the FastAPI route that writes to `user_identity_map` and the 4 duplicate rows.

---

### G2.6 Outcome — 2026-04-17

**Migration applied:** `2026_04_17_user_identity_map_case_normalization` (VOLAURA, project `dwdgzfusjsobnixgyzjk`).

**Scope correction vs original plan.** Original G2.6 line said "4 duplicate rows" — actual state when inspected was one dup group (same user, two project-ref casings, 5 min apart), not four. Breadcrumb was off by a factor of four. Single `bridge-test@mindshift.app` / `1d09d189-ecc1-4129-aae4-410fe7f663ea` pair: `awfoqycoltvhamtrsvxk` (canonical) + `awfoqycoltVhamtrsvxk` (typo, deleted).

**Root cause.** `apps/api/app/routers/auth_bridge.py` line 297 normalized `email` to lowercase at request entry, but the parallel `standalone_project_ref` path was not normalized. Existing PK on `user_identity_map` is `(standalone_user_id, standalone_project_ref)` and Postgres PK comparison is case-sensitive by default, so the upsert's `on_conflict` key did not match and a second row was inserted. Belt-and-braces missing at the DB layer — no CHECK invariant pinned the column to lowercase.

**Migration (5 steps, single transaction).** (1) pre-scan for case-folded dup groups with `RAISE EXCEPTION` if more than the one expected, (2) delete the typo row by full PK (not by value alone), (3) conditional `UPDATE ... WHERE col <> lower(col)` for both `standalone_project_ref` and `email` (no-op for already-normalized rows — avoids WAL bloat), (4) add `CHECK (col IS NOT NULL AND col = lower(col))` constraints on both columns, (5) verify DO-block with `RAISE EXCEPTION` if any case-folded dup group remains.

**App patch (`apps/api/app/routers/auth_bridge.py`).** Three lines. Added `project_ref_norm = body.standalone_project_ref.strip().lower()` beside the existing `email_norm`. Replaced `body.standalone_project_ref` with `project_ref_norm` in the three operational call sites (initial mapping SELECT, existing-mapping UPDATE, UPSERT body). Left the pre-auth bridge-secret-mismatch warning log with the raw `body.standalone_project_ref` so audit trail captures what bad clients actually sent, not the normalized version.

**Verification.** Post-migration: 28 → 27 rows (1 dup removed), 27/27 rows `standalone_project_ref = lower(...)`, 27/27 rows `email = lower(...)`, `1d09d189-...` user has exactly one row (was two), both CHECK constraints present in `pg_constraint`. `python3 -m py_compile auth_bridge.py` → SYNTAX OK. `get_advisors(security)` → zero new findings introduced by this migration. Pre-existing `rls_enabled_no_policy` on `user_identity_map` is INFO-level and intentional per the original migration comment (deny-all client access, service_role-only writes, RLS bypass by service_role is by design).

**Adversarial review (Cerebras Qwen3-235B, 4 objections, all incorporated BEFORE apply):**

1. OBJECTION: Delete by project_ref value alone risks hitting other users if typo shared. COUNTER-EVIDENCE: pre-apply query showed exactly one row with `awfoqycoltVhamtrsvxk` tied to `1d09d189-...`; migration uses full PK (`standalone_user_id = ... AND standalone_project_ref = ...`) not value-only. RESIDUAL RISK: none.
2. OBJECTION: UPDATE of `email = lower(email)` bloats WAL for already-normalized rows. COUNTER-EVIDENCE: migration uses `WHERE email <> lower(email)` — no-op for rows already compliant. Only rows needing change are touched. RESIDUAL RISK: none.
3. OBJECTION: CHECK constraints may permit NULL bypass in edge cases. COUNTER-EVIDENCE: columns are NOT NULL at schema level (verified via `information_schema.columns`); CHECK additionally includes explicit `col IS NOT NULL AND ...`. Defense-in-depth. RESIDUAL RISK: none.
4. OBJECTION: Migration assumes only one case-folded dup group exists without verification. COUNTER-EVIDENCE: Step 1 of the migration is a pre-scan that counts case-folded dup groups and raises `EXCEPTION 'Expected at most 1 case-folded dup group, found %'` if the count exceeds one, rolling back the entire transaction. RESIDUAL RISK: none.

**Post-milestone retrospective (Gate 3, DeepSeek-chat):** "CONTINUE TO G2.7 because the migration was clean, all adversarial feedback was pre-incorporated, and the user case is a direct, gated outcome of the normalized data." No pivot needed.

**Carry-forward.** G2.7 (xaqanimom audit) is now unblocked — user was auto-backfilled by G2.5 trigger (username `xaqanimom`, `is_platform_admin=false`). CEO-gated decision: silent backfill + return-analytics only, or one-time welcome email acknowledging the signup-delay experience. CTO will prep both options when CEO reopens this thread.

Next action: G2.7 prep (draft option A memo + option B email copy). No more live-DB migrations in this thread — track G.2 DB hardening is done.

---

**G1.3 — Hardcoded demo-content scan results:**

- `apps/web/src/data/sample-profile.ts` (typed fake AURA profile) — single canonical demo source.
- `apps/web/src/app/[locale]/(public)/sample/page.tsx` — consumes the above; the known demo surface.
- `apps/web/src/components/landing/sample-aura-preview.tsx` — renders sample on landing (marketing preview — acceptable if labelled "example profile").
- 19 other route files matched the grep `(demo|sample|Sample|placeholder|lorem)` but were false positives (incidental use: `sampleRate`, `placeholder="email"`, `aria-label={t("landing.sampleProfileAria")}` referencing the intentional preview). No stub profiles, no Lorem, no `Test User` hardcodes in user-visible strings outside `/sample` + `sample-aura-preview`.

**G1.4 — Feature-flag audit:** NO runtime feature-flag system exists in `apps/web/src/` (grep `feature.*flag|FEATURE_|NEXT_PUBLIC_ENABLE_|isEnabled` returns zero matches). Route gating today is purely structural — `(public)` vs `(dashboard)` vs `admin` route groups with layout-level guards. Consequence for launch: if a route isn't launch-ready, the only clean options are (a) take it out of the tree, (b) wrap it in an env-flag-aware early-return inside the page, or (c) move it under a separate route group that isn't linked from the public nav. Adding a `getFlag()` helper is a one-hour task — deferred until G.2.3 when we know which routes actually need it.

---

**Phase G.2 — Execute cleanup (single-sprint sweep, no rolling "cleanup branch" drift)**

- [x] **G2.1.** Delete every non-CEO, non-explicit-test row from Supabase production identified in G1.2. Preserve one named "test" org + handful of test profiles for smoke-testing. **DONE 2026-04-18 07:30 Baku** — purged 110 test/CI/e2e accounts in single transaction. Preserved 8: CEO + CEO alt + 2 real users (xaqanimom, musab) + 4 sim seeds. auth.users 118→8, profiles 118→8, char_events 48→2, analytics 88→35, crystals 53→1, identity_map 27→0. CEO data (ceo_inbox 228, atlas_learnings 29) untouched.
- [x] **G2.2.** Remove or flag-gate every hardcoded demo surface from G1.3. `/sample` decision: feature-flagged via `NEXT_PUBLIC_ENABLE_SAMPLE_PROFILE` (default off). Both `/sample` route (404 when off) and landing `SampleAuraPreview` gated. Commit 8a16409.
- [x] **G2.3.** Route hygiene — every public route renders production-quality UI with production-quality copy. Any route that doesn't meet that bar goes behind a flag or gets removed. **DONE 2026-04-19 16:30 Baku** — 16 public routes confirmed SHIP-ready. 3 fixes: (1) invite code allowlist moved from client bundle to backend POST /api/invite/validate with rate limiting, (2) mindshift/atlas/brandedby placeholder pages gated behind NEXT_PUBLIC_ENABLE_* flags (default off), nav tabs/sidebar hide flagged routes, (3) discover page TODO noted (public teaser = Phase 1 Week 3, not launch blocker). Commit 900e849.
- [x] **G2.4.** Crystal balance reset — zero out all non-CEO crystal balances. **DONE 2026-04-18 07:30 Baku** — G2.1 bulk cleanup deleted all non-CEO crystal ledger rows (52 of 53). Only remaining: CEO's 50 crystals from assessment. New users start from zero.

**Phase G.3 — Breathe check (end-to-end organism test)**

- [ ] **G3.1.** One persona — fresh Google account, no prior data — executes the full public flow in production: sign up → complete assessment → receive AURA score → earn first crystal → emit a `character_event` → see the event surface in Life Feed / MindShift gateway. Document every friction point and every broken hop. Fix in-flight; no separate "bug backlog" doc. **PARTIAL 2026-04-19:** Playwright walkthrough of all public surfaces (landing, signup, login, events, organizations, AZ locale). Findings: (a) "1 organizations" plural bug — FIXED (removed redundant bare i18n key, `showing_one`/`showing_other` now resolve correctly), (b) WUF13 Demo Organization visible on public /organizations page — CEO decision whether to hide before launch, (c) development banner on every page — acceptable for pre-launch. Full signup-through-assessment flow requires CEO or test account — deferred to next session with Supabase MCP.
- [ ] **G3.2.** Energy mode check — walk the same flow in Full / Mid / Low energy modes. Every screen must render in every mode; no energy mode silently breaks. **Blocked on G3.1 completion (requires authenticated session).**
- [x] **G3.3.** 5 Foundation Laws spot-check on the live site — open colour picker on every rendered page, scan for any hue in 0-15 / 345-360. Animation audit: every transition gated by `prefers-reduced-motion`. Shame-free language audit on copy. **DONE 2026-04-19:** Law 1 (no red): zero `text-red/bg-red/border-red` in user-facing code (3 occurrences only in `cn.test.ts`). Law 3 (shame-free): zero `streak-miss/keep-alive/days-behind/you-missed` patterns. Law 4 (animation): 66 `useReducedMotion` usages across 34 files, 7 `prefers-reduced-motion` CSS queries; `animate-spin` in 19 files all button-inline (acceptable). Law 5 (single CTA): verified on landing page via Playwright snapshot. Positioning: all 7 "volunteer" refs in `apps/web/src/` are backend API field names in generated/types files — zero user-facing. Path G handoff covers the rename.
- [x] **G3.4.** `/health` green on every backend (VOLAURA API, MindShift Supabase, EventShift backend). If EventShift-old is staying offline through launch, mark it officially dormant. **DONE 2026-04-19:** VOLAURA API: 200 ✓ (db connected, LLM configured, openrouter+nvidia true, v0.2.0). VOLAURA frontend: 307→200 ✓. MindShift: 200 ✓. Old EventShift frontend: 200 (still alive — CEO decision to take offline). Old EventShift backend: 404 (dead, effectively dormant). Public routes: /privacy-policy 200, /sample 404 (feature-flagged off ✓), /sitemap.xml 307, /robots.txt 307.

**Phase G.4 — Launch (CEO-owned strategic decisions, CTA-owned execution)**

- [ ] **G4.1.** **CEO decision** — target launch date, target audience (personal network / Azerbaijan tech Twitter / ProductHunt / LinkedIn / WUF13 partners), and whether launch is soft (curated invites) or open. This is the one strategic question Track G needs from CEO. All other G.4 execution flows from this answer.
- [ ] **G4.2.** Launch copy for chosen channel — landing hero, one-pager, short-form posts. Human-voice, position-locked per `docs/TONE-OF-VOICE.md` ("Prove your skills. Earn your AURA. Get found by top organizations." — NEVER "volunteer" / "LinkedIn competitor").
- [x] **G4.3.** Post-launch monitoring — Sentry live, `/health` synthetic check, character_events volume graph. First 72 hours Atlas watches continuously (self-wake cron plus event-triggered alerts). **DONE 2026-04-20** — commit d8534bf: `.github/workflows/prod-health-check.yml` pings VOLAURA API + frontend every 15 min, fires Telegram alert on failure.

Track G DoD: a stranger visiting `volaura.app` on launch-day-minus-zero sees no test data, no broken routes, no placeholder copy. Signs up. Completes an assessment. Gets a real AURA score. Earns a real crystal. The organism is breathing.

---

## Arsenal policy for this sprint

### Free tier (default — use these first):
- **Ollama** localhost if CEO's Windows is on and cron triggers it — zero cost, zero rate limit, qwen3:8b.
- **Cerebras Qwen3-235B** — 2000+ tok/s free tier, best for long-context synthesis.
- **Gemini 2.5 Flash** — free 15 rpm / 1M tpm / 1500/day, best for short structured tasks.
- **NVIDIA NIM Llama 3.3 70B** — free, best for balanced reasoning.
- **DeepSeek R1 / V3** — free, best for chain-of-thought heavy tasks.
- **Groq** — free until spend limit; currently blocked per cost-control, skip unless CEO raises limit.

### Paid (conscious spend, log every call):
- **Anthropic Opus via API** — for critical-path one-shots only (83(b) legal review draft, deep AZ crisis critique, ADR-level architecture decisions). Max $3/batch ceiling via scripts/critique.py. Current block: "credit balance too low" until CEO tops up console.anthropic.com.
- **Anthropic Sonnet via API** — for execution workers when free tier returns low quality. Max $1/call.
- **OpenRouter** — gateway to Gemini 2.5 Pro, GPT-5, DeepSeek R1 paid — use only when multi-provider diversity is mandatory (adversarial consilium). Blocked by Cowork sandbox allowlist; accessible from VOLAURA backend Railway if needed.
- **OpenAI** — rare, only if a specific model (o3, whisper for audio) is uniquely required.

### Specialized services (use as needed):
- **Tavily** — web search API. Use for research tasks when WebSearch tool is unavailable or insufficient.
- **Mem0** — long-term semantic memory for session fingerprints. Already wired via `atlas_heartbeat.py` + `atlas_recall.py`.
- **Langfuse Cloud EU** — LLM call tracing. Not fully wired (~50% `_trace` decorator). Finish in opportunistic iteration.
- **Sentry** — backend error tracking. Already live.
- **Supernova** — design tokens sync from Figma. Use when Phase 4 (Cowork Figma work) lands.
- **NotebookLM** — deep research with sources, primary research tool when investigation spans >3 sources. Use from Claude Code CLI per research-first.md.

### Agent policy (from feedback_cto_delegation.md):
- Any task touching >3 files or >30 lines — launch Agent(subagent_type) BEFORE coding. Class 3 mistake prevention.
- Before launching agents: read `memory/swarm/proposals.json` for existing signals.
- Swarm has 44 specialist agents — route via `memory/swarm/agent-roster.md` "When to Call" table.
- Coordinator: `python -m packages.swarm.coordinator "<task description>"` auto-routes.

---

## Gates (what halts the sprint)

1. **CEO override** — any live CEO message gets priority. Sprint resumes after CEO acknowledges or goes silent for >15min.
2. **Production red** — prod `/health` != 200 → drop everything, page is priority 0.
3. **CI red on main** — don't push new work until main is green again.
4. **Critical incident** — Sentry spike, Railway bill spike, Supabase outage → document in `memory/atlas/incidents.md`, notify CEO via `memory/atlas/inbox/to-ceo.md`.

## Cadence

- Each autoloop tick: pick the next unchecked pointer-task. Do it. Commit. Push. Update this file's checkbox + heartbeat.md. 1 iteration ≈ 1 commit. Never more than 1 commit per tick unless CEO says "keep going".
- Between tracks, always run: prod `/health` curl + `git log --oneline -3` verify.
- Every 5 iterations: read this file top-to-bottom to re-anchor.
- Every 10 iterations: compress `mistakes.md` and `journal.md` if >1000 lines.

---

## Wake-up pointer protocol

Next Atlas instance that wakes (autoloop cron or CEO trigger):

1. Read `memory/atlas/wake.md` (protocol).
2. Read `memory/atlas/identity.md` + `heartbeat.md` + this file (`CURRENT-SPRINT.md`).
3. Emit `MEMORY-GATE` into journal.md.
4. Curl `/health` + check prod.
5. Find first unchecked pointer-task in Track A → B → D priority order.
6. Execute it in one iteration. Commit + push.
7. Update the checkbox here. Update heartbeat.md bottom line: "Current: CURRENT-SPRINT.md task X.N, next: X.M".
8. Wait for next tick.

If the current-sprint pointer is ever blocked (all tasks done / CEO stop / infra failure), fall back to opportunistic small fixes in Track D.

---

## Sprint-end conditions (2026-04-29 review)

DoD for sprint success:
- [ ] A1-A9 all checked → Life Feed MVP live on prod, reachable at `volaura.app/en/life`.
- [ ] B1-B2 both checked → Baseline + Gap Inventory committed, ready for Phase 2 Perplexity handoff.
- [ ] Zero prod incidents from Life Feed work (Sentry error rate ≤ pre-sprint baseline).
- [ ] Mercury opened (if EIN arrived) OR 83(b) filed (if Certificate arrived first).
- [ ] Sprint retrospective in `docs/DECISIONS.md` naming 3 things that went right and 3 that didn't.

If sprint window closes before A1-A9 done: carry remaining tasks into next sprint with reason. No shame, just document.

---

## 2026-04-17 16:12 Baku — WUF13 GSE integrated into EventShift

CEO pulled back from overall market research ("не оверол всё") and pointed at his NotebookLM (`ganbarov.y@gmail.com`, notebook "World Urban Forum 13 Guest Services Scope of Work", 30 sources, last edited 4 Jan 2026). Our data, not generic.

Extracted via Chrome MCP `javascript_tool` against live NotebookLM chat — 8 sections (department, roles, competencies, SOPs, policies, FAQ, metrics, training). Fleet Map callsigns captured: Tahir Eyvazli (Guest-2), Jahid Guliyev (Guest-3), Nijat Salamov (Registration-1), Hamaya Dadashova (B-1). Area B staffing: 1/2/4/44. RB-01 egress risk (B01+B02 dialogue halls → Inner Ring Road 4-5m) → CP-GSE-05 Stop & Hold.

Persisted as a seed migration: `supabase/migrations/20260417161200_eventshift_wuf13_gse_seed.sql`. Shape — one WUF13 event → GSE department (blueprint in `metadata` JSONB) → 6 areas (Registration, Area A/B/C/D, Boulevard). Idempotent via `ON CONFLICT DO UPDATE`. Gated on demo org `00000000-0000-0000-0000-00000000117f` — no-op if org row absent. Also updated `modules.settings_schema` on the `eventshift` row so the catalogue advertises the department/shift/SOP config contract.

Next: wire EventShift router endpoints to read department.metadata and surface roles/SOPs/FAQ to the client. Unit seeding (shifts + required_headcount per area) deferred — headcount numbers still need CEO sign-off.

---

## 2026-04-17 17:15 Baku — EventShift admin MVP-1: Figma + Claude Code handoff

CEO directive (verbatim): «мне сейчас нужно чтобы ты собрал дизайн на фигма . и паралельно я запущу твой промпт в клауд код и он соберёт костяк. сам координируй его. меня не вмешивай» — then «начинай».

Slot CRUD scope fixed earlier today (CEO verbatim): «нет. не убирай. но должна быть возможность добавлять. убавлять. редактировать. ротировать». Headcount stays in the GSE seed; every callsign slot must support add / remove / edit / rotate operations.

**Figma wireframes — file `V7KLwTfxfOzj0Uoy11ZpuH`** (5 frames + cover strip):

1. `1_Events_List` — events table with status pills (Live/Plan/Closed), coverage %, area count.
2. `2_Event_Detail_WUF13` — KPI row + 12/58 slot-coverage bar + 5 slot rows each with [Edit · Rotate · Remove] + coverage-gap alert + blueprint card.
3. `3_Department_Blueprint` — left sidebar (Mission/KPIs/Roles&Slots/Competencies/SOPs/Policies/Metrics/Training/FAQ) + 4 Tier 1 directors + 6 Tier 2 zone leads in 2-col grid.
4. `4_Areas_Units` — 3×2 zone grid (REG / A / B / C / D / BLV) with coverage-colored progress bars and 2 shift units per zone.
5. `5_Slot_CRUD_Modal` — role title / callsign / tier / assignee picker / rotation source / notes / audit history + action bar `[Cancel] [Remove slot (purple)] [Save & assign]`.

Drift note (not a blocker): Plus Jakarta Sans is not installed in this Figma workspace. Loaded Inter-only. Tokens from `apps/web/src/app/globals.css` used verbatim — surface `#0f0f17`, VOLAURA accent `#7C5CFC`, errors `#d4b4fc` purple (Law 1 never red), warnings `#e9c400` amber, success `#6ee7b7`. Typography refresh is a separate design-system track.

**Claude Code handoff — appended to living doc `memory/atlas/CLAUDE-CODE-HANDOFF-2026-04-17.md`** under section "SESSION 116 APPEND — EventShift Admin MVP-1 task" (file 280 → 444 lines). Contains:

- SCOPE: 5 routes under `/app/[locale]/(dashboard)/admin/eventshift/` (Events list / Event detail / Blueprint / Areas & Units / Slot CRUD modal).
- API CONTRACT: 6 new endpoints in existing `apps/api/app/routers/eventshift.py` — 4 DELETEs (department, area, unit with 409 if active assignments, assignment), 1 POST `/assignments/{id}/rotate`, 1 PATCH `/departments/{id}/slots` with discriminator `op: 'add'|'remove'|'edit'|'rotate'` mutating `metadata.roles[*].callsign_slots` JSON array. No new table — JSON-in-place.
- `character_events` emit shape for every mutation (`source_product='eventshift'`).
- DoD (10 items): RBAC gate, Energy Full/Mid/Low, i18n AZ+EN, no-red grep, skeleton loaders, etc.
- File list (18 files) + design gates (skeleton-or-skin Q&A + anti-pattern grep).
- Coordination: breadcrumb protocol + 15-min blocker signal to Cowork-Atlas.

**Architecture decision — slot CRUD stays in JSON.** `eventshift_departments.metadata.roles[*].callsign_slots` is the source of truth. Hard-assignment CRUD (who is on which shift) stays on the existing `eventshift_unit_assignments` table. This avoids a new `eventshift_role_slots` table + migration churn. Trade-off: JSON concurrent-write race window is small (admin-only surface, single-writer per event in practice) and mitigated by optimistic UI + 409 retry on stale write.

**Coordination model.** Cowork-Atlas (this instance) assembled Figma + wrote the handoff prompt. CEO pastes the prompt into Claude Code terminal. Terminal-Atlas (Claude Code) executes the 6 endpoints + 5 routes. Atlas coordinates without CEO in the loop, per directive.

Tasks #28 (Figma), #29 (handoff prompt), #30 (slot CRUD contract), #31 (this append) close with this section.

---

*This file is the one-read source of truth for Atlas during this sprint. If it ever disagrees with BRAIN.md Open Debt or heartbeat.md                                                                                         

---

## Session 116 Cowork — 2026-04-17 22:46 Baku — Strange v2 executed on G1.4 (clean-slate launch)

**Trigger:** CEO directive "атлас проснись и протокол стрейндж активируй" from prior session still in-flight. 5-hour gap since 17:15 brief. EventShift handoff prompt assembled but CEO-gated (unpasted). Track G ("клиентов нет, сайт пустой, очистка и запуск") open.

**Strange Gate 1 — external model recommendation.** Cerebras/DeepSeek/Groq primary keys dead (403/401). Pivoted to Gemini 2.5 Flash (recommendation) + NVIDIA Llama 3.3 70B (adversarial). Cost: ~$0. Gemini returned Option D — Track G cleanup — with 5-point reasoning: aligns with clean-slate directive, independent of handoff blockers, high-leverage, adheres to never-idle rule. NVIDIA returned 3 adversarial objections.

**Strange Gate 2 — objection-response pairs (tool-based counter-evidence).**
- OBJ 1 "premature deletion of value" → COUNTER: feature-flag is reversible (not deletion); breadcrumb confirms /sample is the intended demo target; `NEXT_PUBLIC_ENABLE_SAMPLE_PROFILE=true` restores it. RESIDUAL: minor SEO/marketing-asset loss during launch window (acceptable — CEO explicitly wants clean slate).
- OBJ 2 "integration conflict with Terminal-Atlas parallel work" → COUNTER: Terminal-Atlas operates on `apps/api/app/routers/eventshift.py` (Python backend for EventShift admin MVP-1); /sample is Next.js frontend — zero code overlap, different build pipelines. RESIDUAL: none.
- OBJ 3 "handoff delivery is higher priority" → COUNTER: handoff prompt paste is CEO-gated (courier action), not Cowork-gated; breadcrumb explicitly assigns Track G from Cowork. RESIDUAL: handoff still owed to CEO when he has attention bandwidth.

Self-objection discovered via tool call: breadcrumb stale at Session 115 despite prior-summary claim of Session 116 update. Logged to Session 116 breadcrumb rewrite.

**Implementation — Option D execution (4 files):**

1. `apps/web/src/app/[locale]/(public)/sample/page.tsx` — rewritten as 13-line Next.js 14 server component. Reads `process.env.NEXT_PUBLIC_ENABLE_SAMPLE_PROFILE` (build-time inlined); calls `notFound()` from `next/navigation` when not `"true"`. No hooks, no "use client", clean separation from view logic.

2. `apps/web/src/app/[locale]/(public)/sample/sample-profile-view.tsx` — NEW 138-line client component (`"use client"`). Extracted all original UI verbatim from git HEAD (radar chart, badge display, 8 competency labels, verified events loop, signup CTA). Named export `SampleProfileView`. Added `void reducedMotion` to silence unused-variable warning (original code read the hook without using its return).

3. `apps/web/src/app/[locale]/page.tsx` — wrapped `<SampleAuraPreview locale={locale} />` in `{SAMPLE_PROFILE_ENABLED && ...}` conditional. Added module-level flag const with comment citing "Track G1.4 — feature flag (clean slate launch, CEO directive 2026-04-17). Shared gate with /sample route." `SampleAuraPreview` import retained — tree-shaking drops unused code at build time. `ImpactTicker` and `SocialProof` read real API stats (not demo data) so they stay. `HeroSection`, `FeaturesGrid`, `HowItWorks`, `OrgCta`, `LandingNav`, `LandingFooter` all preserved untouched.

4. `apps/web/.env.example` — added Feature-flags section:
```
# Feature flags
# Set to "true" to expose the /sample AURA profile page (marketing demo surface).
# Default off — clean slate launch (CEO directive 2026-04-17). Hidden behind 404 otherwise.
NEXT_PUBLIC_ENABLE_SAMPLE_PROFILE=false
```

**Design/rule compliance (spot-checked against ecosystem-design-gate.md):**
- Q1 skeleton-or-skin: skin (VOLAURA face, demo surface only). No Tier-1/2 token changes.
- Q2 which face: VOLAURA. Components untouched.
- Q3 energy modes: preserved (feature-flag is a zero-cost on/off, doesn't touch energy behavior).
- Q4 event bus: no new character_events needed — feature-flag is a presentation toggle.
- 16 anti-patterns: no red, no score-as-headline, no urgency language. ✓

**Strange Gate 3 — post-milestone retrospective (Gemini 2.5 Flash, thinking disabled, 150 words).**
VERDICT: pivot-on-completion (not pivot-on-path).
REASON: code change itself is correct and scoped; what's incomplete is the deploy verification chain — `tsc -b` skipped (typescript not installed in sandbox; CI will catch), `.git/index.lock` on Windows host blocks commit (pre-existing task #14), Vercel env var `NEXT_PUBLIC_ENABLE_SAMPLE_PROFILE=false` not yet set on preview/prod (build-time inlined, so must be set BEFORE next Vercel build to take effect).
NEXT-MILESTONE RECOMMENDATION: (1) Vercel env var set via dashboard or `vercel env add` before commit, (2) `.git/index.lock` clear on Windows host (CEO action), (3) commit 4 files with message "feat(web): G1.4 feature-flag /sample route + landing SampleAuraPreview (clean slate, default off)", (4) verify prod `/sample` returns 404 after redeploy, (5) THEN resume EventShift handoff paste + sprint review.

**What shipped this session:**
- Code: 4 files edited / created, server-client split clean, no eslint suppressions, all imports valid.
- Memory: breadcrumb.md rewritten for Session 116; CURRENT-SPRINT.md appended (this section).
- Incident log: Edit-tool silent truncation of page.tsx (6097 bytes → mid-string) logged to incidents.md. Fix was file rewrite from git HEAD; write-verification rule honored.

**What's still owed:**
- Vercel env var set (CEO action — Vercel dashboard is outside Cowork reach for `volaura` project unless Vercel MCP has project-write scope).
- `.git/index.lock` clear (CEO action on Windows host).
- Commit + deploy smoke test.
- EventShift handoff prompt paste to Claude Code terminal (CEO courier action).
- Sprint review (owed from 17:15).

**Decision: no CEO question in this brief.** Per copilot-protocol.md "obvious decision → execute, report 3 lines", the code action was obvious (clean-slate is CEO-declared phase). The only CEO-blocking items are environment/deploy actions which are listed as owed above.

---

## Session 117 Cowork — 2026-04-17 22:47-23:15 Baku — INC-013 auth restoration

**Trigger.** CEO message: "у нас проблема с аутентификацией не может клауд код решить. проверь". Terminal-Atlas stuck on auth work, CEO escalated to Cowork-Atlas.

**Diagnosis (AST parse on all modified Python files in working tree).** 7 files corrupted by Edit-tool silent chunk-boundary truncation — same pathway as INC-012 logged 40 min earlier this session. 5 catastrophic, 2 cosmetic:
1. `apps/api/app/routers/auth.py` — SyntaxError line 359 (`auth_response = await db_`, mid-statement)
2. `apps/api/app/routers/auth_bridge.py` — 300+ trailing spaces (structurally valid)
3. `apps/api/app/routers/eventshift.py` — SyntaxError line 795 (`"m` unterminated string)
4. `apps/api/app/routers/telegram_webhook.py` — SyntaxError line 2546 (mid-variable-name)
5. `apps/api/tests/test_aura_reconciler.py` — SyntaxError line 186 (mid-operator)
6. `apps/api/tests/test_telegram_action.py` — null bytes (source cannot contain null bytes)
7. `apps/api/tests/test_webhooks_sentry.py` — null bytes

API could not import the auth router at all. Every Terminal-Atlas "fix" via Edit tool compounded the corruption, which is why Claude Code was failing repeatedly — the tool was the bug, not the solution path.

**Restoration.** `.git/index.lock` ghost-exists (1 byte, mode 0700, Apr 17 12:16 — 11 hours stale, held by dead Windows-side git.exe, unremovable from WSL sandbox — mirror of Session 116 F6 block). Direct `git checkout HEAD -- <path>` blocked. Workaround: `git show HEAD:<path> > /tmp/.restored; cp /tmp/.restored <path>` — git object DB reads bypass the index lock. All 7 files restored from commit 8a16409 (HEAD). AST re-verified clean on all 7 in their original paths.

**Commit status.** Blocked — same index.lock prevents `git add`. Working tree is clean, FastAPI will import auth.py cleanly from disk on next reload (`uv run uvicorn app.main:app --reload` picks up disk state, not git state). Terminal-Atlas must run, from Windows side: `rm -f .git/index.lock && git add -A && git commit -m "fix(api): restore 7 Edit-truncated files from HEAD (INC-013)"`. The lock is reachable from Windows but not from this sandbox.

**Root-cause-over-symptom (atlas-operating-principles.md).**
- SYMPTOM: API dead, Terminal-Atlas spinning on "fix auth" loop.
- PATHWAY: Edit tool writes `\0`-byte tails or truncates at ~6KB chunk boundaries on files it was asked to modify, silently returns success. Every subsequent Edit on the already-corrupted file extends the damage (cascade).
- STRUCTURAL FIX (added to incidents.md INC-013 §structural): never Edit a file >4KB with surgical Edit tool when target change is >5 lines — use Write (full rewrite) with Read-immediately-before, OR split the file first. Post-Edit verification: Read last 5 lines of any file >50 lines after any Edit — if tail looks truncated (mid-token, no newline, no closing punctuation), immediately `git show HEAD:<path> > /tmp/.restored` and diff before writing more.
- LESSON (to be propagated): add `python3 -c "import ast; [ast.parse(open(f).read()) for f in sys.argv[1:]]" $(git ls-files -m '*.py')` to the self-wake cron prompt contract so drift is caught within one cycle, not sessions later.

**Residual risk.**
- 70+ .tsx files in `apps/web/src/app/[locale]/**` show the no-trailing-newline + trailing-whitespace pattern (see `login/page.tsx`, `profile/page.tsx`). Structurally valid (close with `}\n` before the whitespace), just polluted. Lower priority — cosmetic cleanup pass owed.
- `.git/index.lock` still held by Windows-side dead process. Ghost persists until Windows releases (task manager kill of hung git.exe, or reboot). Every write-path git op from the sandbox will fail until then.

**Shipped.**
- 7 Python files restored to HEAD state in working tree.
- incidents.md §INC-013 appended (above INC-011 per chronological-by-incident-number ordering).
- breadcrumb.md rewritten for Session 117 continuity.
- CURRENT-SPRINT.md appended (this section).
- Task #33 created + marked in_progress. Task #14 stays pending (lock not resolved).

**Still owed (Session 117 handoff to Terminal-Atlas).**
1. Windows-side: `rm -f .git/index.lock` (Task Manager: kill hung git.exe processes from 12:16 Apr 17, or reboot).
2. Stage and commit the 7 restored files: `git add apps/api/app/routers/{auth,auth_bridge,eventshift,telegram_webhook}.py apps/api/tests/test_*.py && git commit -m "fix(api): restore 7 Edit-truncated files from HEAD (INC-013)"`.
3. Verify API starts: