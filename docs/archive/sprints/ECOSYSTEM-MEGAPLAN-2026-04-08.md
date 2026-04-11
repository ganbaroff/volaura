# ECOSYSTEM MEGAPLAN — 5 Products, 22 Sprints

**Author:** VOLAURA-Claude (worktree blissful-lichterman) · **Date:** 2026-04-08
**Scope:** All 5 products (VOLAURA + MindShift + Life Simulator + BrandedBy + ZEUS) + swarm + integration layer
**Horizon:** 22 sprints (including 2 validation sprints) · **Realistic calendar:** 5-7 months
**Status:** **v3 FINAL** — 2 rounds of peer critique applied (Sprint 22 validation cycle complete)

## Glossary (read this BEFORE Sprint 0) — added v3

The git history mentions "Sprint E2.D.1" and "Sprint E2.D.2" — these do NOT appear in the 22-sprint list below. They were numbered under the old MindShift `mindshift-sprint-e2-plan.md` convention (ADR-006 Option D). Mapping:

- **Sprint E2.D.1** = migration `20260408000001_user_identity_map.sql` (committed `56d3337`) → now a **prerequisite deliverable for Sprint 1** in this megaplan
- **Sprint E2.D.2** = `apps/api/app/routers/auth_bridge.py` + config additions (committed `56d3337` + `9f7c173` hardened) → same, **prerequisite deliverable for Sprint 1**
- **Sprint E2.D.3-D.5** = MindShift-Claude's edge function + frontend bridge + e2e test → these are what Sprint 1 in THIS megaplan executes

So when you see "E2.D" in commit messages or MindShift-Claude handoff docs, read it as "work that happened before Sprint 1 and is consumed by Sprint 1". Sprint 1 itself is the integration + verification sprint that makes E2.D.1 through D.5 actually run end-to-end in production. No new "E2.D" identifier exists going forward.

Similarly: "Sprint S1 / S2 / S3 / S4" in older docs referred to the Session 91 VOLAURA swarm work (swarm_coder, safety_gate, daemon, decision debate). That work is **already committed** (`c1508de`, `8b71164`, `39b23d7`, `fb3b014`, `63dc930`) and is now referenced only as context. The "S4 Hybrid architecture decision" is implemented in **Sprint 17** of this megaplan.
**Supersedes:** `docs/MEGAPLAN-MINDSHIFT-LAUNCH-2026-04-08.md` is now Phase A (Sprints 1-4) of THIS plan

**CEO directive 2026-04-08:** "Мне нужен план общего развития всего проекта. Даже если 20 спринтов. Это же мегаплан. Все включено. Ключевые файлы залинкованы. Следующий чат не будет тупить."

---

## 🔴 READ-FIRST ANCHORS (paste these into new chat before reading anything else)

### Mandatory reading list before ANY action

1. **This file** — `C:/Projects/VOLAURA/docs/ECOSYSTEM-MEGAPLAN-2026-04-08.md`
2. **MindShift detail** — `C:/Projects/VOLAURA/docs/MEGAPLAN-MINDSHIFT-LAUNCH-2026-04-08.md` (Phase A detailed spec with v3 reality check)
3. **Handoff for new chat** — `C:/Projects/VOLAURA/docs/HANDOFF-NEW-CHAT-PROMPT.md`
4. **Sprint E2.D state** — `C:/Users/user/.claude/projects/C--Projects-VOLAURA/memory/mindshift-sprint-e2-plan.md` (UPDATES 1-5)
5. **Constitution** — `C:/Projects/VOLAURA/docs/ECOSYSTEM-CONSTITUTION.md` (5 Foundation Laws + Article 0 NEVER Anthropic)
6. **Shared context** — `C:/Projects/VOLAURA/memory/swarm/shared-context.md` (Session 91 section at top — what already exists, do NOT rebuild)
7. **Mistakes catalog** — `C:/Projects/VOLAURA/memory/context/mistakes.md` (CLASS 3 solo work, CLASS 12 self-inflicted complexity — main failure modes)
8. **User profile** — `C:/Users/user/.claude/projects/C--Projects-VOLAURA/memory/user_yusif.md` (CEO working style)
9. **Communication style** — `C:/Users/user/.claude/projects/C--Projects-VOLAURA/memory/feedback_adhd_communication.md` (NOT corporate reports, casual Russian, как друг)
10. **Sprint S4 debate** — `C:/Projects/VOLAURA/docs/SPRINT-S4-DEBATE-2026-04-08.md` (6-model team decision: Hybrid architecture)

### Current HEAD on main (2026-04-08 end of session)

```
63dc930 docs(megaplan): v3 reality check — opened actual MindShift repo
fb3b014 docs(megaplan): 4-sprint MindShift launch plan + peer-review hardening
9f7c173 fix(auth-bridge): apply 5-model peer critique — pagination, race, drift
56d3337 feat(auth-bridge): Sprint E2.D.1 + D.2 — cross-project identity bridge
39b23d7 feat(swarm): Sprint S3 — test gate + background daemon + batch mode
c1508de feat(swarm): Sprint S2 — autonomous coding loop via Aider + safety gate
156647a fix(telegram-bot): 6 bugs in ask_llm — bot was lying to CEO
36ce848 fix(swarm): 5 critical bugs + Session 91 knowledge transfer
```

### Key file links (grouped by product)

#### VOLAURA (this repo, `C:/Projects/VOLAURA/`)
- `apps/api/` — FastAPI backend (Python 3.11+, async, Supabase)
- `apps/api/app/main.py` — entrypoint, 121 routes
- `apps/api/app/deps.py` — JWT validation via admin.auth.get_user
- `apps/api/app/routers/character.py` — cross-product event bus (POST /events, GET /state, GET /crystals)
- `apps/api/app/routers/auth_bridge.py` — Sprint E2.D.2 cross-project identity bridge (new, 411 LOC)
- `apps/web/` — Next.js 14 App Router frontend
- `supabase/migrations/` — 67 migrations, latest `20260408000001_user_identity_map.sql`
- `packages/swarm/` — Python swarm engine (autonomous_run, coordinator, squad_leaders, shared_memory, telegram_ambassador, 44 agents)

#### Swarm tooling (this repo, `C:/Projects/VOLAURA/scripts/`)
- `swarm_agent.py` — multi-provider LLM wrapper (Cerebras/Groq/Gemini/NVIDIA/OpenRouter + Ollama)
- `swarm_coder.py` — Aider + safety_gate autonomous coding loop (6-step pipeline)
- `safety_gate.py` — 4 risk levels + verify_commit_safe post-exec check
- `swarm_daemon.py` — background polling (rate-limited 5/hour, 20/session)
- `test_runner_gate.py` — targeted pytest + infra-broken-aware
- `dsp_debate.py` — 3-model debate pattern (propose + critique)
- `project_qa.py` — per-project Q&A indexer (384 .md files)
- `execute_proposal.py` — proposal → action bridge PoC

#### MindShift (separate repo, `C:/Users/user/Downloads/mindshift/`)
- `package.json` — React 19 + Vite + TypeScript + Capacitor 8.3 + @sentry/react 10.42
- `capacitor.config.ts` — appId `com.mindshift.app`, Android/iOS wired
- `android/` — full gradle project, ready for signed build
- `src/shared/lib/volaura-bridge.ts` — 211 LOC, CharacterState/CrystalBalance/CharacterEvent types, fire-and-forget
- `src/features/mochi/mochiChatHelpers.ts` — 84 LOC
- `src/features/home/mochiMessages.ts` — 36 LOC
- `src/shared/lib/mochiDiscoveries.ts`
- `src/features/settings/PlanSection.tsx` — Stripe web checkout via edge function `create-checkout`
- `supabase/functions/volaura-bridge-proxy/` — (Sprint 1 new, MindShift-Claude's D.3)
- `supabase/migrations/001-015_*.sql` — 15 tables (users, tasks, focus_sessions, subscriptions, achievements, energy_logs, etc.)
- `CLAUDE.md` — project instructions, Constitution Laws enforced
- `.claude/rules/crystal-shop-ethics.md` — 8 crystal rules
- Standalone Supabase project: `awfoqycoltvhamtrsvxk`
- Shared project (for VOLAURA bridge): `dwdgzfusjsobnixgyzjk`
- Live URL: `https://mind-shift-git-main-yusifg27-3093s-projects.vercel.app`

#### Life Simulator (separate repo, path unverified but referenced as Godot 4.4 game)
- Portrait mobile 1080×1920
- Character model with 8 stats, skills, history, serialization — COMPLETE
- Event system: 47 events, priority queue, consequences — COMPLETE
- TimeController 1s = 1 game year — COMPLETE
- **4 critical bugs (per ecosystem_audit 2026-03-27, must verify current)**:
  1. `event.check_requirements()` — method doesn't exist, should be `can_trigger()` → crash
  2. `EventModal` never shows — auto-selects choice 0
  3. `game_over.tscn` is 0-byte empty file
  4. `character.full_name` not defined (has first_name + last_name)
- MonetizationController simulated with `randf()` — no real SDK
- CloudSaveManager stub, `CLOUD_ENABLED=false`
- VOLAURA integration: 0%
- ~80 Cogito FPS framework files leftover from template (must delete)

#### BrandedBy (separate repo at `C:/Users/user/OneDrive/Documents/GitHub/brandedby`)
- React 19 + Cloudflare Workers + Hono + D1 (SQLite) + R2 + Stripe
- Celebrity catalog UI + ordering flow + payment page — real code
- **Critical holes (per ecosystem_audit)**:
  - Stripe PaymentIntent creates but card never tokenized (no Stripe Elements)
  - No webhook handler — payment confirmed client-side (security hole)
  - AI video generation 0% — "FaceMorphingDemo" is CSS slideshow, "AI Assistant" returns random strings
  - Celebrity data corrupted (all Cyrillic → `?????`)
  - After payment: project sits in DB with `status='processing'` forever
  - SIMA integration: 0%

#### ZEUS (separate repo at `C:/Users/user/OneDrive/Documents/GitHub/ANUS`)
- Python autonomous agent (Plan→Execute→Observe→Reflect→Replan)
- OpenAI-compatible API at `localhost:8000`
- Desktop control: PyAutoGUI + PyGetWindow + Pytesseract OCR
- CrewAI multi-agent, ChromaDB memory, FAISS RAG
- Selenium web automation + Telegram interface
- 83% test coverage
- **Blocker**: runs on local Windows machine, cloud swarm (Railway) cannot reach `localhost:8000` without ngrok tunnel
- Godot integration: enum exists but writes `.txt` files only (0% real bridge)

#### Cross-product integration layer
- `character_events` table (VOLAURA shared Supabase `dwdgzfusjsobnixgyzjk`)
- `game_crystal_ledger` table
- `game_character_rewards` table (idempotency for assessment rewards)
- `user_identity_map` table (NEW Sprint E2.D — cross-project identity bridge)
- `find_shared_user_id_by_email` RPC function (NEW Sprint E2.D)
- POST `/api/character/events`, GET `/api/character/state`, GET `/api/character/crystals`, POST `/api/auth/from_external` (NEW)

---

## Sprint structure — 22 sprints across 6 phases

**Legend:**
- 🟢 = unblocked, can start immediately
- 🟡 = blocked on CEO ops action (documented)
- 🔴 = blocked on another sprint completing
- ⚠️ = has external queue (Play Store review, account verification, etc)

### Sprint 0 — VOLAURA production smoke test (ADDED post-critique 2026-04-08)

**Reordered after critique (Kimi K2 + DeepSeek V3.1 consensus):** VOLAURA must be production-ready BEFORE we wire MindShift to it via Sprint 1 bridge. If VOLAURA core is broken, shared-project tables and identity bridge are useless and will need re-migration. This sprint was previously Sprint 5 in v1; DeepSeek and Kimi independently said it should come first.

**Goal:** CEO himself completes full VOLAURA flow end-to-end with a real email and real payment path, documents every friction/error, fixes blockers as an incident. Phase 0 gate from HANDOFF-SESSION-91 that has been pending for 2 weeks.

**Scope:** Signup → email verify → assessment start (8 questions) → LLM evaluation → AURA score → badge → share page → OG image. Run `scripts/prod_smoke_test.py` against Railway prod. Fix any P0/P1 blockers immediately. Kill condition: if 3+ blockers found in first attempt, pause S1-S4 until fixed.

**Output:** One real user profile with a real AURA score viewable at volaura.app/profile/{username}. Plus a list of friction points that feed into Phase B polish sprints.

**Why moved here**: Phase A Sprint 1 bridge writes to `character_events` table in VOLAURA shared project. If VOLAURA backend rejects those writes (because assessment router is broken, or RLS is misconfigured, or cron hasn't run), MindShift-Claude's D.5 test will fail in a confusing way. Smoke-testing VOLAURA first surfaces "is the core platform alive?" as a single yes/no gate.

**Expanded scope per v3 peer critique (Cerebras Qwen 235B):** the smoke test must ALSO include cross-project surface:

7. **Shared-project RLS verification** — write a mock `character_event` row to `dwdgzfusjsobnixgyzjk.character_events` via service role. If insert fails, migration is broken or RLS is mis-configured → surface BEFORE Sprint 1 rather than during MindShift-Claude's D.5.
8. **Verify `find_shared_user_id_by_email` RPC callable via service role** — `admin.rpc("find_shared_user_id_by_email", {"p_email": "test@example.com"}).execute()` — expect None (no user), not an error about missing function.
9. **Verify `user_identity_map` table readable via service role** — simple SELECT, confirms migration applied and grants are correct.

If any of 7-9 fails, Sprint 1 cannot start — the bridge's preconditions aren't met.

**⚠️ Sprint 1 explicit blocker**: Sprint 1 is blocked 🔴 on Sprint 0 completion, not just 🟡 on CEO ops. Do NOT start Sprint 1 until Sprint 0 steps 1-9 all pass. This is a v3 fix — v2 marked Sprint 1 only as 🟡 (CEO ops) and omitted the dependency on Sprint 0.

---

### Phase A — MindShift launch (Sprints 1-4)

These 4 sprints map 1:1 to the v3 MindShift megaplan (`MEGAPLAN-MINDSHIFT-LAUNCH-2026-04-08.md`). See that file for detailed deliverables and peer-critique-driven fixes. Summary here:

**Sprint 1** 🟡 — Ecosystem bridge end-to-end + Day 0 external ops kickoff
- Apply migration `20260408000001_user_identity_map.sql` to shared Supabase
- Set Railway env: `SUPABASE_JWT_SECRET`, `EXTERNAL_BRIDGE_SECRET`
- Same `EXTERNAL_BRIDGE_SECRET` on MindShift Supabase edge function env
- MindShift-Claude implements D.3 (volaura-bridge-proxy edge function) + D.4 (frontend bridge update) + D.5 (e2e test)
- VOLAURA-Claude writes negative test suite for `verify_commit_safe` (`apps/api/tests/test_safety_gate.py`) — Sprint S4 team-identified missing piece
- **Day 0 parallel** (no need to wait for bridge): CEO starts Google Play Developer account verification, CEO records voice clips (15s/30s/60s), voice consent doc signed
- Exit: one real `character_events` row in shared DB with `source_product='mindshift'`

**Sprint 2** 🔴 (needs S1) — MindShift Learning Mode MVP
- Add `learning_course_id` + `learning_goal` metadata to MindShift `focus_sessions` (existing table)
- Create `public.learning_courses` in shared VOLAURA project, seed 20 hand-curated free courses (CEO curates from 60-candidate shortlist)
- MindShift FocusSetup.tsx: add "что ты учишь?" step with course picker
- Completion emits `focus_session_completed` event with `learning_course_id` + `duration_minutes`
- VOLAURA character_events handler grants `crystal_earned` on learning (new source `mindshift_learning`)
- Psychotype → recommended course category mapping (Mochi surfaces 3 top picks)
- **New work verified**: remote config flag infrastructure (not present in MindShift codebase — confirmed by grep)
- Verify Sentry DSN actually set (installed but config unverified)
- Explicit flight-mode test for focus timer

**Sprint 3** 🔴 (needs CEO voice recording from S1 Day 0) — Voice + anti-Pro + Crystal humor + early Capacitor smoke test
- ElevenLabs voice clone ($22/mo) OR Coqui XTTS v2 local for AZ/TR/DE/ES variants
- Voice player component with honest AI disclosure text
- Replace Pro upsell screen (`PlanSection.tsx`) with voice player + anti-Pro message ("я не хочу чтобы ты покупал Pro, попробуй бесплатно учиться")
- Voice also plays on: first-streak-complete, post-onboarding welcome, weekly progress review
- Crystal click handler in `mochiChatHelpers.ts`: first 10 hardcoded variety, 11+ LLM-generated with time/name/streak/psychotype context
- 20th click Windows-error-style easter egg (royalty-free sound, custom)
- Adaptive vs standard onboarding toggle (default adaptive)
- Remote config flag `anti_pro_voice_enabled`
- **De-risk**: throw-away Capacitor internal track build EARLY in sprint (not wait for S4) to catch native billing issues

**Sprint 4** ⚠️ 🔴 (needs Google Play account approved from S1) — Google Play submission
- Native in-app billing plugin (replaces web Stripe on Android build path)
- Sign AAB, upload to Play Console Internal Testing track
- Data safety form + privacy policy + Terms URL
- Feature graphic 1024×500 (already captured per BATCH-2026-04-04-R)
- 8 screenshots (already refreshed per BATCH-2026-04-04-P)
- Closed beta 10 testers → 48h observation → production release
- **Fallback if Play rejects**: signed APK direct download from `mindshift.app/download`

### Phase B — VOLAURA polish + activation (Sprints 5-9)

**Sprint 5** 🟢 — VOLAURA E2E smoke test with first real user
- CEO walks the full flow: signup → email verify → assessment start → 8 questions answered → LLM evaluation → AURA score computed → badge displayed → share page generated → OG image served
- Document every friction point, broken link, silent error, shame-language violation
- Fix blockers immediately (treat as a live incident)
- Run `scripts/prod_smoke_test.py` against Railway prod
- This is Phase 0 gate from HANDOFF-SESSION-91. Until done, nothing else VOLAURA matters.
- Output: one real user profile with a real AURA score viewable publicly
- **Kill condition**: if 3+ blockers found, pause all other VOLAURA work until fixed
- Implement Energy Adaptation: add a low-energy mode that simplifies the UI and reduces the number of questions, and ensure that the mode is triggered by the user's energy level

**Sprint 6** 🔴 (needs S5) — VOLAURA assessment flow optimization + error recovery UX
- Resume flow (409 Conflict on re-start) already exists per Session 83 — verify works
- Add LLM rate-limit fallback: keyword scoring on Gemini 429, upgrade queue re-evaluates later (already exists? verify)
- Low-score scoreMeaning_justStarting copy (already fixed in worktree commit `7fec325`, needs merge)
- Energy picker integration fully wired (already in worktree, needs verification + merge)
- Constitution Law 2 enforcement in assessment start: low energy → shorter CAT stopping criteria (already exists, needs end-to-end smoke test)
- Error recovery UX: what happens on network drop mid-assessment? Local draft save + resume

**Sprint 7** 🟢 — Organization discovery + search UX
- `/api/discovery` endpoint pagination + search already exists per code audit — improve relevance ranking
- Add filters: skill, badge tier, location (AZ cities), language
- Pgvector HNSW index already in place (migration 14) — verify query performance <200ms at 10k profiles
- Organization dashboard: saved searches, notify on new matches (existing `org_saved_searches` migration 2026-04-01)
- Intro request flow: org sends → user accepts/declines → crystal cost for org, crystal reward for user

**Sprint 8** 🟢 — VOLAURA invite gate → open signup transition + referral system
- Currently `open_signup: bool = False` (per config.py RISK-014) — closed beta by invite code
- Design transition: open signup flag off → on, with referral code persistence
- Referral system: every signup can include `referral_code`, both referrer + new user get crystal bonus
- Rate limiting on register endpoint (already 5/minute per config) — may need tighter during public launch
- Email verification flow via Resend (kill switch still off per config; CEO activates)

**Sprint 9** 🟢 — VOLAURA Pro tier activation
- Currently `payment_enabled: bool = False` (kill switch)
- Stripe checkout session endpoint already exists — just needs env var flip
- Pro benefits design: what does Pro actually unlock? (Unlimited assessments? Priority org discovery? Extended coaching notes?)
- Subscription table already exists (migration 2026-03-29 subscription_system)
- Webhook handler exists (migration 2026-03-30 stripe_webhook_idempotency)
- Go-live checklist: webhook signing secret set, prices configured, test purchase in sandbox, incident response runbook

### ⚠️ Phase C — Life Simulator — DEFERRED post-critique (was Sprints 10-13)

**Deferred by consensus (Kimi K2 + DeepSeek V3.1):** "4 sprints to fix 4 Godot bugs and add fake monetization yields zero revenue and zero learning; reallocating the time gets MindShift to revenue two weeks earlier." — Kimi K2. "Fixing a Godot game isn't strategic when MindShift and VOLAURA aren't launched. Move these sprints to post-revenue." — DeepSeek V3.1.

**Decision**: Phase C (Life Sim Sprints 10-13) is REMOVED from the main critical path. The 4 sprints are reallocated:
- **Sprint 10 (was Life Sim bug fixes)** → New: **Post-MindShift-launch decision point + metrics review** (see Sprint 10 redefined below)
- **Sprint 11 (was Life Sim cloud save)** → Phase B additional VOLAURA work (discovery UX depth, assessment optimization continuation)
- **Sprint 12 (was Life Sim char state sub)** → Reserve for unforeseen blockers from Sprints 1-9 (carry-over bucket)
- **Sprint 13 (was Life Sim closed beta)** → Rolled into Phase D BrandedBy work

**Life Simulator work is postponed to a post-megaplan "Phase G" after MindShift and VOLAURA reach revenue.** The Godot game audit (12 days old) still needs verification at some point — assign to an agent in background daemon mode (Sprint 17 Hybrid swarm) so it can do bug triage while humans focus on revenue-generating products.

### Life Sim resurrection path (added v3 per Qwen 235B critique)

Qwen 235B flagged that "Phase C deferred" without a resumption path **hides Life Sim forever** — Sprint 10 decision is product-led, but Life Sim needs tech-led resurrection (Godot integration, Cogito cleanup, event bug fixes).

**Explicit resumption trigger:** if Sprint 10 decision point concludes Scenario A (MindShift retaining users) OR Scenario D (VOLAURA traction), AND runway math allows, then **insert "Phase G-Prequel" = Sprint 11-lifesim** as a 1-sprint exploration:
- Open Life Sim repo, verify ecosystem_audit bug list still accurate
- Fix the 4 critical bugs (check_requirements, EventModal, game_over.tscn, character.full_name)
- Delete ~80 unused Cogito FPS files
- Wire Godot CloudSaveManager to shared Supabase (flip CLOUD_ENABLED=true, add URL)
- PoC: one focus session in MindShift emits event, Life Sim character sees crystal update
- Exit: playable 5-minute demo OR decision to delete Life Sim entirely and kill the sub-product

If Sprint 10 concludes Scenarios B or C (middling or dead), Life Sim stays deferred. No resumption unless revenue explicitly justifies it.

**Alternative kill path:** if by Sprint 16 (BrandedBy first paying user) no one has touched Life Sim, officially delete the `lifesim` project from ecosystem docs, update Constitution to list 4 products not 5, archive the Godot repo. Don't let it rot forever.

### Sprint 10 — Post-MindShift-launch decision point (REDEFINED)

**Added by consensus (DeepSeek V3.1):** "Add a kill switch sprint after Sprint 4 to reassess priorities. After MindShift launch, metrics might demand pivoting."

**Goal:** Explicit go/no-go on continuing megaplan. Not auto-continue.

**Scope:**
1. Pull 2-week MindShift metrics: installs, day-1 retention, day-7 retention, completed focus sessions, learning sessions, paid Pro conversions, voice-play clicks, crystal clicks, crashes
2. Pull 2-week VOLAURA metrics: new signups (if open_signup flipped), assessments started/completed, AURA scores generated, org searches, intro requests
3. Compute: are we on the "real users complete the path" track, or stuck in "tech demo" territory?
4. Runway check: current cash, burn rate (Supabase + Railway + Vercel + ElevenLabs + Sentry + misc), months remaining
5. Decision tree:
   - **Scenario A — MindShift retaining users**: continue to Phase B completion (Sprints 11 new = VOLAURA depth, 12 = carry-over)
   - **Scenario B — MindShift installing but not retaining**: pivot to retention experiments, pause new feature work
   - **Scenario C — MindShift dead on arrival**: reconsider entire megaplan, consider enterprise pivot (white-label MindShift for ADHD clinic — Kimi suggested this as fast-cash path)
   - **Scenario D — VOLAURA showing traction, MindShift middling**: reallocate to VOLAURA open signup + Pro activation acceleration
6. Output: 1-page retrospective, 1-page next-phase commitment, 1-page risk update

**Why sprint, not task**: Decisions of this size deserve a week of focused analysis, not a 30-minute standup. Metrics compile, CEO reflects, Claude summarizes options, CEO chooses.

**Sprint 10** 🟢 — Life Sim 4 critical bug fixes (verify state first — audit is 12 days old)
- Verify repo location, open file, grep for the 4 bugs
- Fix: `event.check_requirements()` → `can_trigger()`
- Fix: EventModal wire to EventQueue (remove auto-select-choice-0)
- Fix: Create `game_over.tscn` scene (10 nodes, per ecosystem_audit)
- Fix: Add `character.full_name` getter (combine first_name + last_name)
- Delete ~80 leftover Cogito FPS framework files
- Smoke test: start new game, play 1 year of game time, trigger 1 event, see event modal, make choice, trigger game over, see game over scene

**Sprint 11** 🔴 (needs S1 bridge) — Life Sim CloudSaveManager wire to shared project
- Flip `CLOUD_ENABLED = true`
- Add Supabase URL + anon key to Godot project settings
- Implement save/load via character_state API: save = POST events for any new state, load = GET /character/state
- Handle auth: Godot needs to sign in via email+password (use shared project auth directly, or bridge via MindShift-style edge function proxy)
- Offline mode: local .save file continues to work, syncs on reconnect
- Migration: existing local saves get uploaded once on first cloud-enabled launch

**Sprint 12** 🔴 (needs S11 + VOLAURA character events populated) — Life Sim character_state subscription
- Life Sim subscribes to `character_events` via Supabase realtime OR polling
- Volaura assessment completes → emits `crystal_earned` → Life Sim character's crystal balance updates
- MindShift focus session completes → emits `focus_session_completed` → Life Sim character stat `focus_xp` increments
- In-game UI shows source of each crystal ("Earned 50 from completing Communication assessment")
- Two-way: Life Sim in-game actions can also emit events (e.g. `character_milestone_reached`) visible to other products

**Sprint 13** ⚠️ — Life Sim closed beta with 10 players
- Godot mobile build for Android (Life Sim is portrait mobile per audit)
- TestFlight or Play Store internal testing track
- 10 invited beta testers (CEO's network)
- Metrics: day-1 retention, events triggered, crystals earned, game over reached
- Feedback loop: weekly survey, Telegram group, fix iterations
- Success: 60% day-1, 30% day-7 retention; 3+ players report "wanting to keep playing"

### Phase D — BrandedBy MVP (Sprints 14-16)

**Sprint 14** 🟢 — BrandedBy foundation fixes
- Open `C:/Users/user/OneDrive/Documents/GitHub/brandedby` and verify current state vs audit (12 days stale)
- Fix celebrity data encoding (Cyrillic → UTF-8 re-encode + verify database collation)
- Stripe Elements integration (card tokenization that actually works)
- Stripe webhook handler (verify signature, update project status on `payment_intent.succeeded`)
- Remove client-side "payment confirmed" shortcut (security hole)
- Protect `/api/projects/create` with proper auth guard
- Add order status tracking UI (`pending → paid → processing → ready → delivered`)
- Implement Energy Adaptation: add a low-energy mode that simplifies the content generation process and reduces the number of AI-generated videos, and ensure that the mode is triggered by the user's energy level

**Sprint 15** 🔴 (needs S14) — BrandedBy real AI video generation
- Choose provider: HeyGen (established, $30/mo starter) or Runway Gen-2 (better quality, higher cost) or D-ID (cheapest, $5.90/mo Lite)
- Ecosystem_audit flagged D-ID Lite as Phase 1 via brandedby_video_research memory — start there
- Server-side processing queue (Cloudflare Workers Durable Objects or simple job table)
- Real video generation flow: user order → call provider API with celebrity image + script → poll for completion → store MP4 in R2 → email user with delivery link
- Failure handling: refund on provider error, retry on transient error
- **Do not ship**: replace FaceMorphingDemo (CSS slideshow) and "AI Assistant" (random strings) with actual AI-generated content

**Sprint 16** ⚠️ — BrandedBy first real paying user delivery
- Invite 3 beta users from CEO network
- End-to-end: order placed → payment succeeds → video generates → user receives link → user rates delivery
- Metrics: time from order to delivery, refund rate, user satisfaction
- Fix inevitable friction (timing, quality, email deliverability, video hosting)
- Success: 1 paying user actually pays money and receives a real video they find acceptable

### Phase E — ZEUS production + Swarm S4 implementation (Sprints 17-19)

**Sprint 17** 🟢 — VOLAURA-Swarm Sprint S4 Hybrid architecture (per debate decision)
- Per `docs/SPRINT-S4-DEBATE-2026-04-08.md` consensus: autonomous_run.py checks `verdict.can_auto_execute()` for AUTO-level proposals and bypasses /approve
- MEDIUM/HIGH proposals route to PR-with-merge flow (daemon pushes branch, opens GitHub PR via API, Telegram `/merge` command)
- New `execute_safe_proposal(proposal)` wrapper in autonomous_run.py
- Wire `swarm_coder.py` post-success to call `shared_memory.post_result()` so next autonomous_run sees implementations
- Adversarial test suite for `safety_gate.verify_commit_safe` (already listed in Sprint 1 — prerequisite to this sprint's confident rollout)
- Enable `/auto on` mode in telegram_ambassador with smaller daily budget (3 commits/day max initially)
- Monitor for 1 week: what did the swarm actually ship autonomously? Quality good? Ratio of revert to commit?

**Sprint 18** 🟢 — CLAUDE.md refactor + documentation cleanup
- Current `C:/Projects/VOLAURA/CLAUDE.md`: 750 lines (too big to fit in context on every session start)
- Target: 150 lines max, rest split into `.claude/rules/*.md` files loaded on-demand
- Merge/split docs/ folder: kill stale HANDOFF-SESSION-*.md files, consolidate into one HANDOFF.md + docs/HISTORY/
- Update breadcrumb.md protocol — every session must end with breadcrumb update (automation hook?)
- SHIPPED.md consolidation: session-level entries, archive old to SHIPPED-ARCHIVE.md when >200 lines
- Rules: keep `research-first.md`, `session-routing.md`, `swarm.md`, `never-always.md`, `secrets.md`
- Delete duplicates found during Session 91

**Sprint 19** ⚠️ — ZEUS Railway deploy + swarm bridge
- Per HANDOFF-SESSION-91 priority 6: "JWT WebSocket auth deploy + WEBHOOK_SECRETs in Railway"
- ZEUS currently runs on local Windows machine only
- Option A: Railway deploy (same as VOLAURA backend) — needs Dockerfile, needs WebSocket support on Railway plan
- Option B: ngrok tunnel from local → cloud swarm reaches `localhost:8000` via stable tunnel URL
- Option A is better long-term but harder. Option B is MVP.
- Once bridge works: swarm's llm_router.py adds ZEUS as a local Ollama-style provider for free fallback
- Godot integration: replace `.txt` file writing with HTTP POST to ZEUS localhost:8000 /godot/command

### Phase F — Cross-product validation + launch readiness (Sprints 20-22)

**Sprint 20** ⚠️ — Cross-product E2E smoke test
- One real user (CEO himself or a beta tester) walks the FULL ecosystem:
  1. Sign up at volaura.app (Sprint 5-8 polish should make this smooth)
  2. Complete Communication assessment → AURA score → crystal_earned event
  3. Open Life Sim (Sprint 10-13) → see crystals arrived → spend some on character upgrade
  4. Download MindShift from Play Store (Sprint 4) → sign in → start focus session
  5. Focus session completes → xp goes to Life Sim character
  6. Order a BrandedBy video (Sprint 14-16) → receive it
  7. All crystal events visible at one place (`/api/character/state` in VOLAURA)
- Document every broken handoff (there will be many)
- Fix or plan fixes
- **Success**: CEO can screenshot the full cross-product journey

**Sprint 21** 🟢 — Production launch gate: security + legal + GDPR
- Security audit: run `scripts/prod_smoke_test.py` + manual check of all `HIGH_RISK_PATTERNS` from `safety_gate.py`
- Supabase advisors check (`get_advisors` MCP if available): RLS gaps, missing indexes, slow queries
- Rate limits verification: every public endpoint has rate limit decorator
- Secrets audit: no secrets in git history, all env vars documented in `.env.md`
- Privacy policy + Terms of Service for each of 5 products (or shared policy covering all)
- GDPR compliance: data export endpoint (already exists per `gdpr_consent_columns` migration), right-to-delete flow
- Incident response runbook: who gets paged, how to roll back, how to inform users
- Sentry alerts configured for 5xx spikes, slow queries, failed payments

**Sprint 22** 🟢 — Validation: agent peer critique of the entire 22-sprint plan
- Run `scripts/dsp_debate.py` or inline multi-model critique on THIS FILE
- Participants: 5+ diverse families (Cerebras Qwen 235B, Groq Kimi K2, Gemini 2.5 Flash, NVIDIA DeepSeek V3.1 or Nemotron 120B, Ollama Gemma 4 local)
- 3-round debate: propose revisions → cross-critique → synthesis
- Apply consensus fixes
- Identify what was missed
- Document unknowns and surface them to CEO
- **Exit criteria**: CEO reads the critique summary and says "ok, proceed" or redirects

---

## Runway and burn tracking (ADDED post-critique)

**Flagged by Kimi K2 as TOP 1 missing risk:** "No budget line for infra burn. 5 Supabase projects + Railway + ElevenLabs + Cloudflare + Stripe + ngrok + Play-store fees will eat >$600/mo. CEO has no revenue until S4 or S9. Cash gap kills everything before Sprint 6."

### Estimated monthly infra burn (CEO to verify real numbers)

| Service | Tier | Est. $/mo |
|---------|------|-----------|
| Supabase shared (dwdgzfusjsobnixgyzjk) | Paid Pro | $25 |
| Supabase MindShift standalone (awfoqycoltvhamtrsvxk) | Free (for now) | $0 |
| Supabase BrandedBy (if separate) | TBD | $0-25 |
| Railway (VOLAURA backend) | Paid Hobby | $5-10 |
| Vercel (VOLAURA web + MindShift) | Hobby | $0-20 |
| Cloudflare Workers (BrandedBy) | Free | $0 |
| Sentry | Developer | $0-26 |
| Mem0 | Free | $0 |
| Gemini API | Pay-per-use | $0-50 (soft cap) |
| Groq API | Free tier | $0 |
| Cerebras API | Free tier | $0 |
| NVIDIA NIM | Free tier | $0 |
| OpenRouter | Pay-per-use | $0-20 |
| ElevenLabs (Sprint 3+) | Starter | $22 |
| D-ID / HeyGen (Sprint 15+) | Lite | $5-30 |
| Google Play Developer | One-time | $25 |
| Stripe | Per-transaction | 2.9% + $0.30 |
| Domain renewals | Annual | ~$2/mo amortized |
| Apple Developer (iOS future) | Annual | $99/yr ≈ $8.25/mo |
| Swarm runtime (Aider loops, LLM calls in `/auto on`) | Variable | $30-50 |
| Legal/privacy setup (initial) | One-time | ~$100 amortized $10/mo first year |
| **Total pre-launch (real floor per Qwen 235B)** | — | **$180-260/mo** |
| **Total post-launch (all products live)** | — | **$250-400/mo** |

**Cost attribution by product (per Qwen 235B critique — missing in v2):**

| Product | Direct monthly cost |
|---------|---------------------|
| VOLAURA | Supabase shared $25 + Railway $5-10 + Sentry share + Gemini API 50% ≈ **$45-65/mo** |
| MindShift | Supabase standalone $0 (free) + Vercel share + ElevenLabs $22 + 50% Gemini ≈ **$35-60/mo** |
| Life Sim | $0 direct (deferred) |
| BrandedBy | Cloudflare $0 + Stripe per-txn + D-ID/HeyGen $5-30 ≈ **$10-35/mo** |
| ZEUS | $0 direct (local only until Sprint 19) |
| Swarm/infra | $30-50/mo (LLM autonomous cycles) |
| **Total attributed** | **$120-210/mo + one-time fees** |

The attribution reveals that MindShift + VOLAURA account for ~70% of burn, so revenue from Sprint 4 (MindShift Pro) and Sprint 9 (VOLAURA Pro) must cover at least $80/mo combined by Sprint 10 decision point, or we're in trouble.

### Revenue milestones

- **Sprint 4 (MindShift Play Store)**: First possible revenue from in-app billing Pro subscription
- **Sprint 9 (VOLAURA Pro activation)**: Second revenue stream from VOLAURA Pro
- **Sprint 16 (BrandedBy first paying user)**: Third revenue stream

### Runway tracking

Every sprint retrospective must include:
- Current cash on hand (CEO provides)
- Estimated burn for next sprint (based on table above)
- Runway in months (cash / burn)
- Red flag if <3 months runway remaining → pause non-revenue sprints, accelerate revenue sprints

**CEO action**: before starting Sprint 1, provide starting cash number so this runway math is real instead of hypothetical. If starting cash is <$500, ElevenLabs + D-ID + Railway Pro must all wait for first revenue OR be replaced with free alternatives (Coqui XTTS local instead of ElevenLabs, ngrok instead of Railway paid tunnels, etc.).

---

## Anti-goals (explicitly NOT in this megaplan)

- ❌ VOLAURA major new features beyond Phase B polish (no new competency models, no new assessment types)
- ❌ Life Sim new game mechanics beyond critical bug fixes and integration (no new stats, no new events, no new controllers)
- ❌ BrandedBy beyond MVP video delivery (no celebrity licensing deals, no premium tiers, no mobile app)
- ❌ ZEUS new capabilities beyond deploy + bridge (no new desktop automation, no Selenium improvements)
- ❌ Swarm self-modification beyond the Sprint S4 Hybrid architecture
- ❌ AUTO_APPROVER rebuild (Sprint S4 debate REJECTED this — keep rejected)
- ❌ Refactoring the `packages/swarm/` module structure beyond bug fixes
- ❌ Switching any frontend framework (no React → Solid, no Next → Astro, no Vite → Turbopack)
- ❌ Switching any backend framework (no FastAPI → Litestar)
- ❌ Adding new Supabase projects beyond shared + standalone MindShift (consolidate toward single shared per ADR-006 long-term)
- ❌ New languages beyond existing 6 (EN/RU/AZ/TR/DE/ES)
- ❌ Hiring humans (this plan assumes 1 CEO + 2 Claude sessions as the whole team)

### Revised anti-goals (relaxed post-critique 2026-04-08)

**Kimi K2 flagged "no enterprise sales" as too restrictive:** "blocks the fastest path to cash: sell a white-label MindShift build to one ADHD clinic for upfront cash." This is valid for a cash-constrained startup.

**Allowed back in**:
- ✅ Exploratory enterprise conversations with ADHD clinics, therapists, coaches, schools for white-label MindShift licensing — at CEO discretion, time-boxed to 2 hours/week
- ✅ One-off paid custom builds if they require <5 days of work AND pay >$1000 upfront — counted as revenue toward runway
- ✅ Sponsorship inquiries from productivity tool companies for co-marketing — low effort, potentially high value

**Still blocked**:
- ❌ Multi-month enterprise deals with long sales cycles
- ❌ Custom feature development for specific enterprise asks that don't align with roadmap
- ❌ Fundraising / VC conversations (separate track, not in megaplan scope)

---

## Critical path and dependency graph

```
Sprint 1 (bridge)
  ├── Sprint 2 (learning) ──── Sprint 3 (voice) ──── Sprint 4 (Play Store)
  ├── Sprint 11 (Life Sim cloud save)
  └── Sprint 12 (Life Sim char state subscription)

Sprint 5 (VOLAURA smoke) ─── Sprint 6 (assessment polish) ─── Sprint 7 (discovery) ─── Sprint 8 (open signup) ─── Sprint 9 (Pro activation)

Sprint 10 (Life Sim bug fixes) ─── Sprint 11 ─── Sprint 12 ─── Sprint 13 (closed beta)

Sprint 14 (BrandedBy fixes) ─── Sprint 15 (real AI video) ─── Sprint 16 (first paying user)

Sprint 17 (Swarm S4 Hybrid) ─── (independent, parallel to others)
Sprint 18 (CLAUDE.md refactor) ─── (independent)
Sprint 19 (ZEUS deploy) ─── (independent)

Sprint 20 (cross-product E2E) ── needs: 4, 9, 13, 16 all complete
Sprint 21 (security/legal) ── needs: 20 complete
Sprint 22 (plan critique) ── needs: 21 complete
```

### Parallelism opportunities

- **Phase A + Phase B** can overlap: MindShift-Claude works Sprint 1-4 in her worktree, VOLAURA-Claude works Sprint 5-9 in main.
- **Phase C can start after Sprint 1** regardless of Phase A progress (Life Sim bug fixes don't need MindShift done).
- **Phase E (ZEUS + Swarm + docs) is always parallel** — single-track side quests.
- **Critical serial chain**: 1 → 2 → 3 → 4 → 20 → 21 → 22 (MindShift launch → cross-product test → launch gate)

---

## Known risks across the whole plan

From Sprint S4 debate + Sprint E2.D peer critique + v3 reality check:

1. **Bridge JWT acceptance** (Sprint 1 single point of failure) — if `admin.auth.get_user(minted_jwt)` rejects, entire ecosystem collapses. Fallback: service-role + `X-External-User-Id` header path (~30 LOC in `deps.py`).
2. **Google Play Developer account queue** — 2-14 days external queue, starts Day 0 or becomes Sprint 4 blocker.
3. **Voice clone legal (ElevenLabs commercial)** — must have written consent from CEO documented in `docs/voice-consent-ceo-2026-04-08.md` before first clone, or Play Store takedown risk.
4. **Aider non-determinism** — peer review of autonomous commits surfaces hallucinated edits (S7/S17). `verify_commit_safe` + negative test suite is the primary defense.
5. **Cross-product auth split** — MindShift uses standalone Supabase, VOLAURA uses shared. Sprint 1 Option D bridge. Long-term: full migration to shared (Phase G post-megaplan).
6. **Life Sim audit staleness** — 12 days old, 4 critical bugs may already be fixed or new bugs may have appeared. Sprint 10 starts with verification.
7. **BrandedBy video generation cost overruns** — real AI video APIs charge per minute. 100 users × 60s videos × $0.10/sec = $600/mo at launch. Monitor spend from day 0.
8. **Play Store policy drift** — 2026 may have stricter rules on anti-monetization language in voice-over. Remote config flag (`anti_pro_voice_enabled`) lets CEO kill instantly without app update.
9. **Context window exhaustion in single Claude session** — this entire plan cannot fit in one chat's working memory. Handoff protocol via this file + breadcrumb + memory files is the mitigation.
10. **Solo work regression** — CLASS 3 is my #1 failure mode. Every sprint's first action MUST be: check what agents/subagents/tools already exist for this task before writing new code.

---

## What "done" looks like for this megaplan

The entire 22-sprint plan is complete when:

1. A new MindShift user can download from Play Store, sign up, do a focus session, see crystals arrive in Life Sim, complete a VOLAURA assessment, get an AURA badge, and the shared character_state reflects all of it accurately.
2. Every VOLAURA kill switch (payment_enabled, email_enabled, open_signup) is flipped on OR explicitly deferred with a documented reason.
3. The swarm `/auto on` mode has shipped at least 5 autonomous commits with zero security incidents.
4. CEO does not need to open Supabase dashboard or Railway CLI for daily operations — everything is accessible through `@volaurabot` Telegram commands.
5. One paying BrandedBy user exists.
6. Sprint 22 peer critique is done and its findings are either fixed or tracked in a follow-up list.

**Timeline reality**: optimistic 3 months if nothing slips, realistic 5-7 months with normal slippage, worst case 9 months if 2+ Phase C/D sprints hit major blockers. Do not commit to 4 weeks. The v3 peer critique (Kimi K2 + DeepSeek V3.1) explicitly said that timeline was unrealistic.

---

## Update protocol

- After each sprint completes: update `memory/context/sprint-state.md` AND add entry to `memory/swarm/SHIPPED.md`
- After each sprint: brief Telegram notification to CEO (shipped, blocked, next)
- After Phase A complete: update `memory/swarm/shared-context.md` with "MindShift launched" + link to Play Store listing
- After Phase B complete: VOLAURA-specific retrospective, update `docs/STATE-OF-VOLAURA-POST-LAUNCH.md`
- After Phase F complete (Sprint 22): full ecosystem retrospective + public-facing Volaura State of the Ecosystem post
- This file (`ECOSYSTEM-MEGAPLAN-2026-04-08.md`) itself gets UPDATES 1, 2, 3 appended at the bottom as sprints complete. Do not rewrite — append. Future CTOs can read the full evolution.

---

## Meta-note to the next Claude

If you're a new chat reading this as your first context injection:

1. Don't start coding. Read every file in the mandatory reading list above first.
2. Verify the current HEAD commit on main matches what's in this file (commits may have advanced — run `git log --oneline -10`).
3. Check which sprint is "active" by reading `memory/context/sprint-state.md`. If it's stale, read the latest breadcrumb.
4. Before taking any action, check if an agent/subagent/tool already exists for the task. Use `guidance_recommend` MCP tool if available, or grep through `.claude/agents/` and `scripts/` manually.
5. When in doubt, ask CEO via the Telegram bot (`@volaurabot`) instead of guessing.
6. Write in casual Russian like a friend, not corporate English reports. CEO hates the bot voice.
7. Every claim of "done/готово/уверен" requires a tool call in THAT response — this is enforced by a hook.
8. CLASS 3 (solo work) and CLASS 12 (self-inflicted complexity) are my dominant failure modes — catch yourself doing them.
9. If this plan becomes obsolete (new priority from CEO, new audit, new blocker), create a v2 of THIS file with the changes justified in a new section, don't just edit in place.

---

*End of ECOSYSTEM MEGAPLAN v1 draft. Peer critique will follow before this becomes v2.*
