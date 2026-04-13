# MEGAPLAN — MindShift Launch to Google Play

**Author:** VOLAURA-Claude (worktree blissful-lichterman) · **Date:** 2026-04-08
**Horizon:** 4 sprints · **Optimistic:** 4 weeks · **Realistic:** 6-8 weeks (per peer critique consensus 2026-04-08)
**Status:** v2 — peer-review hardened (5-model critique 2026-04-08)
**CEO directive (2026-04-08):** "Сначала закончить входной элемент MindShift, потом VOLAURA, потом Life Sim. Философия: 'я не хочу чтобы ты покупал Pro' через голос Юсифа в 6 языках. MindShift = focused learning platform."

---

## 0. What is verified (before plan starts)

### ⚠️ v3 REALITY CHECK — 2026-04-08 late

After the v2 critique round, CEO pushed back: "проверь и обнови". I opened the
actual MindShift repo (found at `C:/Users/user/Downloads/mindshift/`) and
verified current state. Several v2 assumptions were wrong — ecosystem_audit was
12 days old and undercounting. Real state below.

### MindShift actual state (verified 2026-04-08 by reading MindShift repo directly)

| Thing | v2 megaplan assumed | v3 verified reality |
|-------|--------------------|--------------------|
| **Completion** | "92% PWA / 30% native" | **Production v1.0 LIVE**. Deployed at `mind-shift-git-main-yusifg27-3093s-projects.vercel.app`. Auto-deploys on `git push origin main`. |
| **Capacitor** | "need to set up in S8" | **Already installed**. `@capacitor/android` 8.3, `@capacitor/cli`, `@capacitor/core`. `capacitor.config.ts` fully wired (appId `com.mindshift.app`, SplashScreen, StatusBar, Keyboard, LocalNotifications, PushNotifications, Haptics plugins). |
| **Android platform** | "need S8 native build" | **Already exists** at `android/` with full gradle (build.gradle, gradlew, capacitor-cordova-android-plugins). Ready to `cap sync && cap open android`. |
| **iOS platform** | not addressed | `ios/` directory not present. Can be added via `npx cap add ios` when needed (post-Android launch). |
| **Sentry** | "extend from VOLAURA (S6 add)" | **Already installed**: `@sentry/react` 10.42 + `@sentry/cli` 2.42 in package.json. Need to verify DSN is set, not add the package. |
| **Stripe** | "schema exists, processor unclear" | **Fully wired via Supabase edge function `create-checkout`**. PlanSection.tsx calls `supabase.functions.invoke('create-checkout', {plan: 'pro_monthly'})` → returns `https://checkout.stripe.com/...` URL → redirect → webhook syncs `subscription_tier` column. |
| **Subscription states** | "need to build" | **Already exists**: `'free' \| 'pro_trial' \| 'pro'` in Zustand store. Trial system is live. |
| **volaura-bridge.ts** | "needs D.4 frontend work" | **Already exists — 211 lines**, uses `VITE_VOLAURA_API_URL`, 5-minute cache, fire-and-forget pattern, CharacterState/CrystalBalance/CharacterEvent types. Calls `/api/character/state`, `/api/character/events`, `/api/character/crystals`. Per MindShift-Claude's earlier audit, bridge code is READY — just needs auth working (= Sprint E2.D) to function end-to-end. |
| **Mochi mascot** | "use existing" | **Exists**: `src/features/mochi/mochiChatHelpers.ts` (84 LOC), `src/features/home/mochiMessages.ts` (36 LOC), `src/shared/lib/mochiDiscoveries.ts`. The humor+adaptive-personality work in S7 will extend these files, not build from scratch. |
| **Feature flags** | not addressed | **Not present**. `grep -r "feature_flag\|featureFlag"` in src returned zero. S6 remote config flag IS new work. |
| **Offline timer** | "verify works" | PWA via `vite-plugin-pwa` + IndexedDB via `idb-keyval`. Likely works but S6 includes explicit verification test. |
| **Focus timer framework** | "need to extend for learning" | FocusScreen + FocusSetup + PostSessionFlow already exist. Struggle→Release→Flow phases per Law 2. NO learning-goal concept — `grep learning` in `src/features/focus` returned zero. S6 learning mode IS new work, but integrates with existing FocusSetup. |
| **Constitution Laws** | referenced from VOLAURA | **Already enforced in MindShift**: Law 1 (NEVER RED palette — ESLint rule in commit `4300f9d`), Law 2 (energy adaptation: `isLowEnergy = energyLevel <= 2 || burnoutScore > 60`), Law 3 (invisible streaks, warm amber carry-over), Law 4 (`useMotion()` hook), Law 5 (one CTA per screen). |
| **Crystal economy** | "bridge via character_events" | Rules defined in `.claude/rules/crystal-shop-ethics.md` (8 rules). Transparent formula: 1 min focus = 5 crystals. 24h refund policy. No timers. |
| **Test infrastructure** | not addressed | Vitest unit + Playwright E2E. Per MindShift CLAUDE.md sprint history: **207/207 unit + 201/201 E2E passing** as of BATCH-2026-04-04-Q. E2E runs in CI after every Vercel deploy. |
| **Analytics** | not addressed | `@vercel/analytics` + `web-vitals` + custom `logEvent` system. Events like `app_first_open`, `burnout_alert_shown`, `room_created`, `social_session_feedback` already fire. First-day uninstall can be measured via Vercel + Sentry session data. |
| **Localization** | "6 locales" | `i18next` 25.1 + `react-i18next` 15.5, 6 locales confirmed, all messages keyed. |
| **Google Play** | "apply to store" | Per MindShift CLAUDE.md: "Google Play launch pending account verification". So CEO has NOT yet completed Developer account. Confirms my S5 Day 0 action item. |
| **Supabase project** | `awfoqycoltvhamtrsvxk` standalone | Confirmed via `.env` references in volaura-bridge.ts + migrations 001-015. |
| **MindShift git branch** | not tracked | On `main`, latest commits: `9d24e52 docs(shipped)`, `4300f9d feat(lint) Constitution Law 1 ESLint`, `bf33ca4 fix(ci) google auth`, `b54ec4b lint 30 errors unblock CI` |

### Impact on sprint scope (v2 → v3)

**S6 — scope REDUCED**:
- Sentry install → already done. New: verify DSN, decide whether to share VOLAURA DSN or separate project.
- Offline timer verification → existing PWA likely handles it. Test one flight-mode session.
- Crash reporting analytics → already wired via Vercel + Sentry.
- Subscription tier infra → already done.
- Remote config flag → still new work (no feature_flag system present).
- Learning mode UI + catalog + course picker → still new work (confirmed zero learning code in src/features/focus).

**S7 — scope CLARIFIED**:
- Mochi extension for crystal click humor → builds on existing 120+ LOC mochi infrastructure. Less "new code" more "new call sites + new prompt templates".
- Voice player + disclosure UI → new component.
- Voice recording + ElevenLabs clone → still CEO-blocked.
- Adaptive vs standard onboarding toggle → new user setting.

**S8 — scope MAJORLY REDUCED**:
- Capacitor setup → **DONE**. Skip entire setup phase.
- Android platform add → **DONE**.
- What remains:
  1. Native in-app billing plugin integration (Stripe web flow must be disabled on Android build path)
  2. Build signed AAB for Play Console
  3. Play Console listing (description, screenshots, feature graphic — some already captured per BATCH-2026-04-04-R "feature graphic 1024×500")
  4. Data safety form
  5. Closed beta testers
  6. Review wait
- **Feature graphic already captured** (BATCH-2026-04-04-R commit `d20591c`). Screenshots captured (BATCH-2026-04-04-P refreshed 8 Play Store screenshots).
- Google Play Developer Account verification is the ONLY hard blocker left (CEO ops action). Start Day 0 of S5 as planned.

### Verified via tool calls this session

| Claim | Proof |
|-------|-------|
| 5 critical swarm bugs fixed + committed (`36ce848`) | `git log --oneline --since="1 day ago"` |
| Sprint S2 (swarm_coder + safety_gate) committed (`c1508de`) | git log |
| Sprint S2 real autonomous commit `287ea13` in SHIPPED.md | git log |
| Sprint S3 (test_gate + daemon + /auto) committed (`39b23d7`) | git log |
| Sprint E2.D.1+D.2 initial committed (`56d3337`) | git log |
| Sprint E2.D hardening after peer review committed (`9f7c173`) | git log |
| `scripts/swarm_agent.py` 15KB on main | `ls -la` |
| `scripts/swarm_coder.py` 28KB on main | `ls -la` |
| `scripts/safety_gate.py` 20KB on main | `ls -la` |
| `scripts/swarm_daemon.py` 13KB on main | `ls -la` |
| `scripts/test_runner_gate.py` 10KB on main | `ls -la` |
| `scripts/project_qa.py` 14KB on main | `ls -la` |
| `scripts/execute_proposal.py` 13KB on main | `ls -la` |
| `scripts/dsp_debate.py` 10KB on main (copied from worktree today) | `ls -la` |
| `apps/api/app/routers/auth_bridge.py` 16KB on main | `ls -la` |
| `supabase/migrations/20260408000001_user_identity_map.sql` 6KB on main | `ls -la` |
| `packages/swarm/telegram_ambassador.py` 26KB on main | `ls -la` |
| Bridge endpoint imports cleanly, JWT mint roundtrip works, app.main loads 121 routes | `.venv/Scripts/python.exe` live test |
| Ollama Gemma 4 LOCAL responds via `http://localhost:11434/api/generate` | curl test + peer critique call |
| HANDOFF docs exist on main: `HANDOFF-NEW-CHAT-PROMPT.md`, `SPRINT-S4-DEBATE-2026-04-08.md`, `HANDOFF-SESSION-91.md`, `LESSONS-LEARNED-SESSION-91.md`, `UNFULFILLED-PROMISES.md`, `ECOSYSTEM-CONSTITUTION.md` | find docs/ -maxdepth 1 -name "*.md" |
| MindShift 92% PWA / 30% native per ecosystem_audit (12 days old) | Read ecosystem_audit.md |
| MindShift has Mochi mascot with `mochi-respond` accepting psychotype/energy/streak/sessions | Read ecosystem_audit.md |
| Sprint E2 Option D is CEO-approved plan | Read mindshift-sprint-e2-plan.md UPDATE 3 |
| MindShift-Claude ready for D.3+D.4+D.5 after my `D2_BACKEND_HARDENED_9F7C173` marker | Edit to mindshift-sprint-e2-plan.md UPDATE 5 |

### NOT verified — assumptions this plan makes

- Real MindShift completion % today (memory is 12 days old)
- Whether Capacitor is already set up in MindShift repo or not
- Current Stripe integration state in MindShift (schema exists per audit, processor status unclear)
- Actual Supabase `admin.auth.get_user(minted_jwt)` acceptance (will discover on first D.3 test call)
- ElevenLabs vs Coqui XTTS v2 quality for Azerbaijani/Turkish (not benchmarked)
- Google Play policy for Bubblewrap/TWA with in-app subscriptions (referenced from general knowledge, not 2026 docs)
- What CEO already recorded as voice material (may or may not exist)

---

## 1. Assumptions this plan is built on

1. **CEO agrees with sequential focus** — MindShift → VOLAURA → Life Sim, not parallel. CEO confirmed 2026-04-08 "я решил не распыляться".
2. **"Input element" philosophy** — MindShift is the low-friction entry point into the 5-product ecosystem. Habits are the hook, learning is the value, crystals bridge to Life Sim, Pro (anti-pitched) monetizes.
3. **Ecosystem event bus must work before MindShift launches publicly** — Sprint E2.D backend is done (9f7c173), MindShift-Claude does D.3+D.4+D.5, ops applies migration + sets secrets. Without this, MindShift is standalone and CEO's "входной элемент" premise breaks.
4. **Gemini 2.5 Flash is sufficient for Mochi** — MindShift already uses it, `mochi-respond` endpoint already accepts psychotype context. No model switch needed for adaptive humor.
5. **Ollama Gemma 4 local is available for local peer critique between sprints** — verified today, runs on CEO's RTX 5060, free.
6. **CEO will record base voice in Russian** — most fluent, cleanest clone source. If CEO prefers Azerbaijani as base, swap.
7. **1-month timeline is aspirational** — real calendar may stretch depending on CEO review cadence, ops actions (migration, Railway secrets, Google Play account), MindShift-Claude availability in other sessions.

---

## 2. The four sprints

### Sprint S5 — Ecosystem bridge end-to-end + blocking external ops kickoff (Week 1)

**Goal:** A real MindShift user writes a real `character_events` row in the shared VOLAURA project by clicking one button. No more theoretical integration. ALSO: start every external ops action that can block later sprints — Google Play Developer account, CEO voice recording, ElevenLabs/Coqui commercial consent chain.

**CRITICAL — peer critique consensus (Kimi K2 + DeepSeek V3.1):** S5 JWT bridge is the SINGLE biggest assumption. If `admin.auth.get_user(minted_jwt)` rejects the JWT AND the fallback (service-role + X-External-User-Id) is also rejected by CEO, the entire megaplan collapses — no cross-product events, no crystal bridge, no "входной элемент" premise. This is why S5 is labelled FIRST and why we have two-layer fallback.

**Owner split:**
- **VOLAURA-Claude (next chat):** apply migration, set Railway secrets, verify live `admin.auth.get_user(minted_jwt)` acceptance, fix if rejected (fallback to service-role + X-External-User-Id), negative test suite for `safety_gate.verify_commit_safe` (was flagged as the "thing the team missed" in S4 debate).
- **MindShift-Claude (bold-jones worktree, her session):** D.3 (edge function proxy), D.4 (frontend volaura-bridge update), D.5 (end-to-end test with a test user + verify character_events row landed).
- **CEO ops:** apply migration to shared project (supabase db push or dashboard SQL), set SUPABASE_JWT_SECRET + EXTERNAL_BRIDGE_SECRET on Railway + MindShift edge function env, verify Railway redeploy picks up new router.

**Deliverables:**
1. Migration `20260408000001_user_identity_map.sql` applied to shared project (verify via `list_tables` MCP or dashboard)
2. `/api/auth/from_external` returns 200 + JWT for a real test email (not 503)
3. Test JWT passes `admin.auth.get_user()` on VOLAURA backend (reach `/api/character/state` → 200 not 401)
4. Edge function `volaura-bridge-proxy` deployed to MindShift Supabase
5. One real `character_events` row in shared project with `source_product='mindshift'` and `event_type='focus_session_completed'`
6. VOLAURA-Claude adds negative test suite for `verify_commit_safe` in `apps/api/tests/test_safety_gate.py` (adversarial paths, embedded SQL in .md, path traversal, oversized diffs) — Sprint S4 team consensus said this was missing

**Day-0 parallel unblocking (per peer critique) — CEO ACTIONS:**

7. **START Google Play Developer Account verification on Day 0** (DeepSeek V3.1 flagged: 48h+ review + tax paperwork, hard blocker if deferred to S8). $25 one-time fee. Tax form (W8/W9 equivalent). Identity doc. Timeline: 2-14 days until approved. Put CEO on this Day 0.

8. **CEO records base voice clips on Day 0** (don't defer to S7). 3 clips: 15s quick pitch, 30s with personal story, 60s full rationale. Russian or Azerbaijani — whichever is most natural. Save as WAV (uncompressed) at 44.1kHz mono. If CEO is travelling, phone recording is acceptable for MVP. These clips get banked and consumed in S7.

9. **ElevenLabs written consent chain documentation** (Kimi K2 flagged: commercial voice clone without documented consent = Play Store takedown risk). Create `docs/voice-consent-ceo-2026-04-08.md` with: CEO full name, statement "I consent to my voice being cloned via ElevenLabs for use in MindShift / Volaura commercial products for the duration of my active involvement, with right of revocation via written request to [email]", date, signature (typed name is acceptable as electronic signature). CEO confirms and I store it.

**Success criteria:** Query `SELECT * FROM character_events WHERE source_product='mindshift' ORDER BY created_at DESC LIMIT 1` returns a real row. AND Google Play Developer account is In Review. AND voice clips exist on disk. AND consent doc exists.

**Risks:**
- JWT minting may be rejected by admin.auth.get_user — fallback plan documented in mindshift-sprint-e2-plan.md UPDATE 4
- Migration apply may hit RLS conflicts on auth schema — REVOKE/GRANT statements may need adjusting
- Edge function cold starts may add 200-500ms latency — acceptable for bridge pattern, not for click-time UI

**Exit condition:** One real flow ends with a real row in shared DB. Then S6 starts.

---

### Sprint S6 — MindShift Learning Mode MVP (Week 2)

**Goal:** User opens MindShift, taps "Focus", is asked "what are you learning today?", picks from curated 20-course catalog, timer starts, session ends with a crystal reward that flows through the bridge to VOLAURA.

**Owner split:**
- **MindShift-Claude:** UI for "what are you learning" step, course picker component, learning session type in `focus_sessions` schema (metadata field, not new table), catalog display, session completion flow that emits event through volaura-bridge.
- **VOLAURA-Claude (next chat):** course catalog data model + seed (20 curated free courses across 5 categories), optional RPC for recommendations based on psychotype.
- **CEO:** curate the 20 courses. Curation philosophy: 4 per category × 5 categories (Language, Programming, Soft Skills, Math, Design). All free (YouTube / Coursera audit / Khan / freeCodeCamp / edX audit). Each with 1-sentence pitch.

**Deliverables:**
1. MindShift `focus_sessions` rows can store `learning_course_id` metadata
2. New `public.learning_courses` table (in VOLAURA shared project) with 20 seeded rows
3. MindShift start-focus screen has "What are you learning?" step with course picker (searchable)
4. Completion emits `focus_session_completed` event with `learning_course_id` + `duration_minutes` payload
5. VOLAURA character_events handler grants `crystal_earned` on learning completion (reuse existing `volaura_assessment` pattern but new source=`mindshift_learning`)
6. One-sentence justification for each course visible on picker (reduces decision paralysis)
7. Psychotype-based recommendations (Mochi suggests "based on your achiever psychotype, these 3 are most popular...")

**Non-goals (explicitly NOT this sprint):**
- Full LMS with progress tracking, quizzes, certificates
- Course content hosted in MindShift
- AI tutor
- Paid courses
- User-generated course submission

**Must-haves added per peer critique (Kimi K2):**

- **Crash reporting** — extend existing VOLAURA Sentry DSN to MindShift frontend. 1-line integration via `@sentry/react` or `@sentry/browser`. Without crash reporting, first-day uninstalls will be invisible. CEO's Sentry account already exists per VOLAURA config.
- **Offline timer** — focus timer MUST work in airplane mode. Service worker is already in MindShift PWA. Verify timer uses local time tracking only, persists session state to IndexedDB, syncs on reconnect. Kimi: "learning mode that dies when aeroplane-mode is on feels broken".
- **Remote config flag** — `feature_flags` row in MindShift users table OR Supabase config table. First flag: `anti_pro_voice_enabled` (default true, CEO can flip to false without app update if Play Store complains or users revolt). Kimi: "to kill the anti-Pro voice instantly if Play policy or users revolt".

**Success criteria:** CEO himself uses MindShift for one learning session end-to-end and says "it feels focused, not bloated".

**Risks:**
- Course list curation is CEO-blocking — if CEO doesn't pick 20, sprint stalls. Mitigation: I generate candidate list of 60, CEO picks 20.
- YouTube ToS for embedding vs external link — external link is safe, embed is gray zone per 2026 guidelines. Use external link for MVP.
- Mochi recommendations may feel generic until we have training data. Start with hardcoded psychotype → category mapping; upgrade later.

---

### Sprint S7 — Voice + anti-Pro + Crystal humor + Capacitor smoke test (Week 3)

**Goal:** User approaches Pro upsell, hears CEO's actual voice in their language saying "I don't want you to buy Pro, try learning for free for a week first". User also discovers crystal-click easter eggs that feel alive.

**Owner split:**
- **CEO:** record base voice in Russian (or chosen native language), 3 clips (15s quick pitch, 30s with personal story, 60s full rationale). Transcript per clip.
- **MindShift-Claude:** integrate voice player component, mute toggle, skip button, subtitle display, disclosure text ("это мой голос через ИИ, я не знаю этот язык"). Crystal-click handler that calls `mochi-respond` with `trigger=crystal_spam` + click count. 20th click Windows-error easter egg (locally hardcoded, custom sound to dodge copyright). Adaptive vs standard onboarding toggle.
- **VOLAURA-Claude (next chat):** adaptive_mode field in user preferences table (stored in MindShift side OR shared project). Click count / joke history (if kept in VOLAURA). Audit log of voice plays (for analytics).
- **Tooling:** ElevenLabs voice clone setup (or Coqui XTTS v2 local as fallback) — generate clones for AZ, TR, DE, ES. English is CEO-recordable directly if desired.

**Deliverables:**
1. 3 Russian base recordings (15s/30s/60s)
2. 15 cloned variants (3 clips × 5 target languages)
3. Honest disclosure text below every player: "Это мой настоящий голос, но я не знаю [язык], поэтому ИИ озвучивает мою речь. Идея работает на любом языке"
4. Pro upsell screen replaced with voice player + anti-Pro message
5. Voice played on 3 additional triggers: first-streak-complete, post-onboarding welcome, weekly progress review
6. Crystal-click Mochi integration: first 10 clicks hardcoded variety, 11+ clicks LLM-generated with time/name/streak/psychotype context
7. 20th click easter egg with custom Windows-error-style sound (royalty-free) + "шучу, я знаю это тебя бесит"
8. Adaptive vs standard onboarding question with default="adaptive", single toggle, clear copy
9. Name memory: Mochi uses user's name in jokes after first 3 clicks

**De-risk action per peer critique (Kimi K2):** In parallel with voice integration, create a throw-away Capacitor internal track build EARLY in S7 (not wait for S8). Goal: catch Capacitor + native billing integration issues before S8 deadline pressure. Build produces an AAB artifact uploaded to Internal Testing track for 1-2 CEO devices only. If build breaks, S8 has a full week's buffer to fix. If build works, S8 becomes "ship what's already validated".

**Fallback plan** (if Play Store rejects the final submission in S8): ship MindShift as a **signed APK with direct download link** from `mindshift.app/download`. Keep Stripe web billing for this path (no Play Billing required). This guarantees users can install regardless of Play review outcome.

**Success criteria:** CEO clicks crystal 20 times, gets easter egg, laughs. Plus 3 beta users report "this app feels alive".

**Risks:**
- ElevenLabs $22/mo → real cost. Coqui XTTS v2 local is free but slower/lower quality. For MVP: test Coqui first, upgrade to ElevenLabs if quality gap is too big for Azerbaijani.
- Voice copyright (CEO's own voice is fine; cloning needs CEO's explicit consent chain documented).
- Crystal click LLM latency — Mochi must respond <1.5s or click feels stuck. Cache tight. If Gemini 2.5 Flash latency is >1.5s at click time, fall back to Cerebras Qwen Fast (~1.6s).
- Cultural fit of humor in Azerbaijani — 1 native speaker beta test before shipping.

---

### Sprint S8 — Google Play submission (Week 4)

**Goal:** MindShift has a Play Store listing that actual humans (not just CEO) can download and try.

**CRITICAL — per peer critique (Kimi K2 + DeepSeek V3.1):** S8 is the most likely to slip because it depends on THREE external queues (Play Console verification, Google's 2-day review, possible rejection rounds). The pre-S7 internal track build below is the mitigation — do NOT leave Capacitor + billing integration for S8 first test.

**Owner split:**
- **CEO:** Google Play Developer account verification (if not already done), app listing copy, screenshots, privacy policy URL, data safety form.
- **MindShift-Claude:** Capacitor native build (iOS deferred), native in-app billing wiring (replaces Stripe for Play Store compliance since Google Play requires Play Billing Library for digital goods), Android-specific auth callbacks (if OAuth providers), notification permissions, deep links for voice recording replay.
- **VOLAURA-Claude:** Privacy policy + terms of service pages (if not already on volaura.app). Data safety form content (what we collect, what we share, retention).
- **Tooling:** Capacitor plugins (@capacitor/preferences, @capacitor/app, @capacitor/splash-screen, @capgo/capacitor-native-billing or equivalent for Play Billing).

**Deliverables:**
1. Capacitor Android build passes `pnpm cap build android` locally (AAB artifact)
2. Native in-app billing integration for Pro subscription (SKU created in Play Console)
3. Play Console listing filled: description, 6 screenshots (3 phone + 3 tablet), feature graphic, app icon
4. Privacy policy + Terms URL live at volaura.app (or mindshift.app)
5. Data safety form submitted
6. Closed beta track with 10 testers
7. Production release gated on 48h of closed beta with no P1 bugs

**Non-goals (NOT this sprint):**
- iOS App Store (separate sprint S9 later)
- Paid acquisition campaigns
- Translation localization push beyond existing 6 locales

**Success criteria:** 10 real beta users can install MindShift from Play Store (invite link), use it for 3 days, complete 1 learning session each. CEO can screenshot Play Console live listing.

**Risks:**
- Google Play Developer account verification can take 1-14 days. This is CEO-blocking; start day 0 of sprint.
- Native billing integration is the riskiest piece. If Stripe was already wired, billing code swap is non-trivial.
- Play Store review can reject for various reasons (content, privacy, data safety inconsistencies). Build buffer for 1 rejection round.
- Adaptive mode humor / Windows error may trigger Play policy "deceptive behavior" concerns. Needs clear disclaimer in listing.

---

## 3. Cross-sprint dependencies and critical path

```
S5 (ecosystem bridge)  →  S6 (learning mode needs bridge for crystals)  →  S7 (voice + humor layers on top)  →  S8 (Play Store wraps it all)

Any sprint blocks the next. Parallelism is limited because all sprints work on the same MindShift codebase.

Exception: VOLAURA-Claude's negative test suite for safety_gate (part of S5) is independent of MindShift-Claude's work and can run in parallel to free MindShift-Claude to focus on D.3/D.4.

Exception: CEO voice recording can happen any time after S5 starts, can be banked for S7.
```

---

## 4. Known anti-goals (do NOT do during these 4 sprints)

- ❌ Do NOT start VOLAURA new feature work. Maintenance only (bug fixes, safety). Daemon on `/auto on` for low-risk docs/tests.
- ❌ Do NOT touch Life Simulator or BrandedBy. They get no attention this month.
- ❌ Do NOT add auto_approver.py (Sprint S4 debate REJECTED this architecture).
- ❌ Do NOT build new swarm coordination features. The S1/S2/S3 infrastructure is enough.
- ❌ Do NOT rewrite MindShift frontend in React Native or other framework. Capacitor wraps the existing PWA.
- ❌ Do NOT refactor CLAUDE.md from 750 → 150 lines during these sprints. Do it after S8.

---

## 5. Weekly CEO check-ins (keep CEO informed without distracting)

- **End of each sprint:** One Telegram message with: shipped, blocked, next. Max 400 chars.
- **Mid-sprint:** NO check-ins unless blocker requires CEO action (voice recording, secret setting, course curation, Play Console).
- **Daily swarm runs:** Still happen via GitHub Actions cron (already live). Bot reports high-severity proposals only. Most will be dismissed.

---

## 6. What this plan does NOT address (scope-out)

- **Funding / paying customers.** Subscription revenue is NOT a goal this month. Target is shipping, retention signal, and user reality check.
- **SEO / marketing / ad campaigns.** Not during these sprints.
- **Team hiring.** 1 CEO + 2 Claude sessions (VOLAURA-Claude + MindShift-Claude) is the team.
- **VOLAURA web polish.** Maintenance only.
- **BrandedBy launch.** Completely out of scope.
- **ZEUS production deployment.** Still local-only per ecosystem_audit.

---

## 7. Kill conditions

This plan should be reconsidered if:

1. Sprint E2.D live test (S5) reveals `admin.auth.get_user()` rejects minted JWT AND the fallback (service-role + X-External-User-Id) is rejected by CEO as too fragile. → Re-evaluate architecture, potentially pivot to full auth migration (Option B from E2 debate).
2. MindShift PWA → Capacitor build has fundamental blockers (service worker conflicts, IndexedDB corruption on Android). → Pivot to Bubblewrap/TWA OR postpone Play Store submission.
3. Google Play Developer account verification takes >14 days. → Parallel: submit to F-Droid or APK direct download while waiting.
4. ElevenLabs + Coqui both fail to produce acceptable Azerbaijani voice clones. → Ship with single-language Russian voice + English subtitle translations, add more languages later.
5. CEO changes priority to VOLAURA or another product mid-sprint. → Finish current sprint's committed work, then reassess.

---

## 8. First concrete action (what the NEXT chat does first)

1. Read `docs/HANDOFF-NEW-CHAT-PROMPT.md` and this megaplan.
2. Read `memory/mindshift-sprint-e2-plan.md` UPDATE 4 + UPDATE 5 for exact handoff state.
3. Check Railway env vars status: is `SUPABASE_JWT_SECRET` set? Is `EXTERNAL_BRIDGE_SECRET` set? (If CEO has not done ops yet, ping him with the 2-var list.)
4. Check if migration 20260408000001 has been applied to shared project (ask via `mcp__supabase__list_tables` if Supabase MCP is connected, or ask CEO to verify in dashboard).
5. If prerequisites are met: write negative test suite for `verify_commit_safe` in `apps/api/tests/test_safety_gate.py` (Sprint S4 team-identified missing piece).
6. If prerequisites are NOT met: wait, do maintenance on existing code (`swarm_daemon.py` fixes, additional peer critique of other untested code paths).

---

## 9. Status of this plan itself

- **Drafted by:** VOLAURA-Claude (worktree blissful-lichterman), 2026-04-08
- **Peer review:** PENDING — will be sent to 4+ diverse models (Cerebras Qwen 235B, Ollama Gemma 4 LOCAL, Gemini 2.5 Flash, NVIDIA Nemotron/DeepSeek) for brutal critique before committing.
- **CEO approval:** PENDING — this is a draft. CEO can redirect any sprint to a different focus.
- **Will be superseded by:** each sprint's own kickoff doc when that sprint starts.

*End of megaplan draft.*
