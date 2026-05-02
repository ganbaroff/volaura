# Ecosystem Readiness Audit — 2026-04-16 Session 113

**Method:** Live prod probes + DB queries + code grep + 3-agent audit synthesis. All 5 products + shared spine.

---

## VOLAURA — Verified Professional Talent Platform (75%)

SHOULD BE: signup → multi-competency assessment → weighted AURA score → badge tier → org discovers talent by score → hire/collaborate. Payment via Stripe. Email notifications. 200+ professionals invited.

WHAT IS:
- Frontend live (volaura.app → Vercel, FRA1 region, GDPR compliant)
- Backend live (Railway, health 200, DB connected, LLM configured)
- 79 profiles (77 "volunteer" type — positioning drift in DB enum!, 2 org), ~50 are E2E smoke test junk
- 43 assessments completed, all single-competency, max AURA 14.3/100 (weighted average — math correct, 1/8 competencies = max ~20 score)
- All 43 badge tiers = "none" (Bronze starts at 40, unreachable with 1 competency)
- 0 organizations registered. 0 events. 0 grievances.
- 47 character_events (46 crystal_earned, 1 skill_verified)
- Crystal economy: ledger table exists, double-entry, but thin (47 events total)
- Payments: subscription.py router ready (505 LOC), Stripe SDK in requirements, kill-switch off. NO Stripe keys.
- Email: resend integration ready, kill-switch off. NO Resend key.
- i18n: AZ + EN complete. No missing keys for Baku users.

WHAT NEEDS (to reach 100%):
1. AURA UX: "1/8 competencies assessed" progress indicator on AURA page header (users see 3.76 and think they failed)
2. Stripe activation: CEO provides sk_test, Atlas creates product + webhook + Railway env (ready to execute, blocked on key)
3. Email activation: CEO creates Resend account, pastes RESEND_API_KEY
4. DB positioning: "volunteer" → "professional" enum migration (three-layer split: locales clean, code mixed, DB still original)
5. Test user cleanup: remove ~50 "E2E Test User" profiles from prod
6. Org onboarding: 0 orgs registered — need first B2B user
7. Multi-competency demo: CEO should complete 3+ assessments to show AURA working properly (score will jump from ~4 to ~40+)

---

## MINDSHIFT — ADHD Productivity Companion (unknown from this repo)

SHOULD BE: daily habits, focus sessions, streaks, psychotype analysis, crystal spend. Flutter mobile app. Bridge to VOLAURA via shared Supabase auth + character_events.

WHAT IS:
- Separate Flutter repo (not in VOLAURA monorepo)
- Separate Supabase project (SUPABASE_URL_MINDSHIFT + SUPABASE_ANON_KEY_MINDSHIFT in .env)
- Cross-product bridge endpoint exists (apps/api/app/routers/auth_bridge.py, 1 endpoint, secret-gated)
- cross_product_bridge.py service (262 LOC) — JWT minting for MindShift users
- mindshift.app — curl returned empty (may need HTTPS redirect or DNS check)
- Status per heartbeat: LIVE (Flutter mobile)

WHAT NEEDS:
1. Verify MindShift app is actually serving (curl empty could mean DNS or hosting issue)
2. Cross-product bridge E2E test: MindShift user → auth_bridge → VOLAURA profile creation → character_events written
3. Crystal spend flow: MindShift consuming crystals earned in VOLAURA (character_events event_type=crystal_spent — currently 0 in DB)
4. Behavioral data isolation verification: MindShift cognitive data NEVER crosses to VOLAURA (Constitution Principle 1)

---

## LIFE SIMULATOR — Godot 4 Life Game (30%)

SHOULD BE: Godot 4 client. Life as RPG. Crystals from VOLAURA = progression currency. NPCs make decisions via neuroscience (Ramachandran 7 principles). Stats, events, choices.

WHAT IS:
- Backend: 4 API endpoints (feed, next-choice, choice, purchase) in lifesim.py, auth+rate-limited
- DB: lifesim_events table (53 events seeded, RLS + FORCE), read-only for users
- Godot client: NOT in VOLAURA repo (separate repo or not built yet)
- Status per heartbeat: DEV 65%, 4 P0 bugs

WHAT NEEDS:
1. Godot client location: verify if separate repo exists or if 65% refers to backend only
2. Crystal purchase flow: lifesim /purchase endpoint → character_events crystal_spent
3. Event feed integration: /feed endpoint → render in Godot client
4. NPC decision engine: neuroscience logic from CEO's research (Ramachandran principles)

---

## BRANDEDBY — AI Video Twin (15%)

SHOULD BE: AI twin generates video of user for professional contexts (interviews, presentations). D-ID for avatar, FAL for lip sync, personality from character_state.

WHAT IS:
- Backend: 8 API endpoints in brandedby.py, auth+rate-limited
- Personality refresh: get_character_state RPC → generate personality via LLM
- D-ID + FAL API keys in .env (present, not verified live)
- brandedby.xyz: curl returned empty (domain exists but no frontend deployed)
- Video generation worker: video_generation_worker.py (302 LOC) exists
- Status per heartbeat: DEV 15%

WHAT NEEDS:
1. Verify D-ID Lite activation ($5.90/mo — CEO purchase)
2. Frontend UI: no BrandedBy frontend pages exist in apps/web (only backend router)
3. Video pipeline E2E: upload photo → D-ID avatar → FAL lip sync → deliverable video
4. Consent flow: multi-step consent before AI twin creation (Constitution BrandedBy Level 1)

---

## ZEUS / ATLAS — Autonomous Agent Framework (60%)

SHOULD BE: self-organizing swarm OS. Agent coordination via coordinator. Autonomous daily runs. Cross-product governance via zeus.governance_events. Telegram bot as CEO interface.

WHAT IS:
- Swarm engine: autonomous_run.py functional, 9 modes, 6 providers (Gemini, Groq, OpenAI, DeepSeek + Ollama dynamic + NVIDIA)
- Engine v5-v7: auto-discovery, tournament mode, skill augmentation, agent memory, structured memory (4-network system)
- 13 scheduled GitHub Actions workflows (self-wake, daily-digest, watchdog, content, daily-swarm, etc.)
- Atlas gateway: 2 endpoints (health + proposal), secret-gated
- Telegram bot: 2485 LOC, 16 commands, NVIDIA→Gemini→Groq chain, emotional state detection, self-learning
- zeus.governance_events: DB schema live, log_governance_event + inspect_table_policies RPCs deployed + hardened
- Proposals system: proposals.json pipeline (10 pending triaged this session)

WHAT NEEDS:
1. squad_leaders.py restoration: coordinator imports it, archived version exists, need active version
2. Agent utilization: 7 active of claimed 44 — grow activation rate
3. Coordinator runtime: make_plan + route + run_parallel exists but squad routing falls back to defaults
4. Telegram bot anti-loop: semantic repeat detection (current: literal duplicate only)
5. Cross-product agent routing: agents currently VOLAURA-only, no MindShift/LifeSim/BrandedBy agents active

---

## SHARED SPINE — Cross-Product Infrastructure (50%)

SHOULD BE: one user identity → one event bus (character_events) → one crystal economy → shared Supabase auth → all 5 products read/write to same graph. Crystal flow: VOLAURA assessment → crystal_earned → LifeSim/MindShift crystal_spent.

WHAT IS:
- character_events: 47 rows total (46 crystal_earned from VOLAURA, 1 skill_verified). ALL from VOLAURA, ZERO from other products.
- get_character_state: RPC function (not table) — computes state from events. Works.
- game_crystal_ledger: double-entry accounting table with UNIQUE index on (user_id, reference_id). Exists.
- game_character_rewards: idempotency table for crystal issuance. Exists.
- Supabase auth: shared across VOLAURA. MindShift has separate project.
- Crystal widget: dashboard shows balance when > 0. Widget exists and works.

WHAT NEEDS:
1. Cross-product event flow: MindShift + LifeSim + BrandedBy should write to character_events (currently 0 events from non-VOLAURA sources)
2. Crystal spend path: no crystal_spent events exist. Economy is one-directional (earn only).
3. Auth bridge E2E: VOLAURA ↔ MindShift JWT bridge tested backend-only (Session 93), never with real MindShift client
4. Event volume: 47 events for 79 profiles = 0.6 events/user. Too thin for character_state to be meaningful.
5. DB enum migration: profiles.account_type still uses "volunteer" — needs "professional" migration

---

## ECOSYSTEM READINESS SCORE

| Product | Score | Blocking for launch |
|---------|-------|-------------------|
| VOLAURA | 75% | Stripe keys, AURA UX indicator, org onboarding |
| MindShift | ??? | Need live state verification |
| LifeSim | 30% | Godot client, crystal spend flow |
| BrandedBy | 15% | D-ID activation, frontend UI |
| ZEUS/Atlas | 60% | squad_leaders restoration, coordinator activation |
| Shared Spine | 50% | Cross-product event flow, crystal spend, auth bridge E2E |

**Overall ecosystem: ~50%**

For WUF13 MVP (May 15-17): VOLAURA alone can demo with 3 fixes (Stripe, AURA UX, multi-competency demo). Other 4 products are aspirational slides, not live demos. Shared spine is plumbing that only activates when 2+ products have real users.

---

## PRIORITY SEQUENCE (Doctor Strange)

Recommendation: VOLAURA-first launch path. Get first 10 real users through complete assessment flow (3+ competencies each → meaningful AURA scores → visible badges) before touching other products. Crystal economy and cross-product spine only matter when there's flow to carry.

Phase 1 (this week): Stripe activation + AURA UX completeness + multi-competency demo + test user cleanup
Phase 2 (next week): Org onboarding + email notifications + invite wave to 200 professionals
Phase 3 (WUF13 prep): PR narrative + video demo + landing social proof
Phase 4 (post-WUF13): MindShift bridge E2E + LifeSim crystal spend + BrandedBy MVP
