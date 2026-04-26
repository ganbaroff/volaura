# Reality Audit — 2026-04-26

CEO directive 2026-04-26 17:00 Baku: «прошу сверить соответствие документации и идеи реальности». Three Sonnet 4.6 agents ran in parallel via Task tool, each with self-contained scope. Output is composite of their findings. All claims have file:line citations from the agents' own grep/Read calls. Atlas-instance reading this file MUST treat each finding as evidence-anchored, not as opinion.

Sonnet#1 — VOLAURA monorepo audit (`C:/Projects/VOLAURA`). Sonnet#2 — MindShift Capacitor app audit (`C:/Users/user/Downloads/mindshift`). Sonnet#3 — cross-product ecosystem consistency audit.

## VOLAURA monorepo (Sonnet#1)

What is real and verified at code level. Assessment engine in `apps/api/app/routers/assessment.py` is 9 endpoints, 1920+ lines, with IRT 3PL plus BARS plus anti-gaming. AURA score calc at `apps/api/app/core/assessment/aura_calc.py:15-22` matches CLAUDE.md weights verbatim — communication 0.20, reliability 0.15, english_proficiency 0.15, leadership 0.15, event_performance 0.10, tech_literacy 0.10, adaptability 0.10, empathy_safeguarding 0.05. Badge tiers at line 27-31: Platinum 90.0, Gold 75.0, Silver 60.0, Bronze 40.0. Score decay logic exists (lines 41-58 define half-lives per competency, tests pass) — but there is no GitHub Actions workflow that triggers it against live users. Decay is math without a scheduler.

Atlas reflection card on `/aura` page: `apps/web/src/app/[locale]/(dashboard)/aura/page.tsx:22` imports useReflection, lines 632-651 render «Atlas says» card. E1 promise lived. Life Feed MVP at `apps/web/src/app/[locale]/(dashboard)/life/page.tsx` is 398 LOC real code, four lifesim endpoints in `apps/api/app/routers/lifesim.py`. v0Laura skills engine at `apps/api/app/routers/skills.py:378` — POST /api/skills/{skill_name} loads from 51 markdown files. Cross-product bridge at `apps/api/app/services/cross_product_bridge.py`. Privacy and Terms pages exist and are bilingual.

What is partial. Three of five VOLAURA-web faces are 404 stubs behind feature flags — `mindshift/page.tsx:13` requires `NEXT_PUBLIC_ENABLE_MINDSHIFT=true`, `brandedby/page.tsx:9` requires `NEXT_PUBLIC_ENABLE_BRANDEDBY=true`, `atlas/page.tsx:8-9` requires `NEXT_PUBLIC_ENABLE_ATLAS=true`. Defaults are false. EventShift exists in code but Vercel deploy blocked. Push notifications page renders but no `web_push` endpoint in routers — delivery has no implementation. Email service file exists but no SES/Resend transport configured.

What is claimed but not found. «44 specialised Python agents» appears in `memory/atlas/identity.md:35`, `FEATURE-INVENTORY-2026-04-18.md:41`, archived handoff docs. Reality: `packages/swarm/autonomous_run.py PERSPECTIVES` array has exactly 13 entries (grep confirmed). The 51 files in `memory/swarm/skills/` are markdown prompts. `packages/swarm/agents/` directory empty. Community Signal widget G44 (Constitution v1.6 mandated for AZ launch) — hook exists, no UI wiring on any page.

Constitution violations spotted in code. `apps/web/src/app/[locale]/(dashboard)/brandedby/generations/[id]/page.tsx:338` — «Generation failed» headline violated Law 3 (shame-free language). FIXED today commit `c6db12f` to «This one didn't come through», i18n key `brandedby.didNotComplete`. Energy-mode (`useEnergyMode` import) absent on 7 pages — profile, settings, notifications, onboarding, discover, leaderboard (now redirect), subscription. Constitution Law 2 requires Full/Mid/Low coverage from Day 1. Onboarding without energy mode is explicit P0 in Constitution v1.7. `/az/org-volunteers` URL hardcoded in `apps/api/app/services/match_checker.py:220` (positioning-lock violation, banned word «volunteer»). FIXED today same commit to `/az/org-professionals`.

Documentation drift. `CLAUDE.md` line 3 claims Constitution «v1.7 supreme law». `docs/ECOSYSTEM-CONSTITUTION.md` header was «v1.2». FIXED today same commit to «v1.7». `FEATURE-INVENTORY-2026-04-18.md` lines 43-46 claimed «consent_events: ZERO writes» and «human_review_requests: no reader route» — both stale. `assessment.py:245`, `auth.py:204` write consent_events. `grievance.py:399-486` has reader routes for human_review_requests. Inventory needs refresh.

Bottom line for VOLAURA. Vision is 40% lived, 60% intent. Assessment plus AURA plus Life Feed is real production-ready code. The «5 faces of one organism» story is built at backbone level (character_events bus, atlas_learnings, skills engine) but not realized at user-facing level — three of five faces are flag-locked 404 for real users. The agent personality layer that v0Laura vision describes («users meet them directly, pro mode») does not exist on any user surface — agents are backend workers, invisible.

## MindShift Capacitor app (Sonnet#2)

What works at code level. Task management (create/edit/delete/snooze/reschedule) fully implemented across `src/features/tasks/`. Focus session engine real — `FocusScreen.tsx`, `useFocusSession.ts`, breathwork ritual, Mochi companion, post-session flow, recovery lock. Onboarding, today morning/evening flows, progress stats, settings 6 sections. VOLAURA bridge wired through `src/shared/lib/volaura-bridge.ts`. Reduced motion solid: `useMotion.ts` combines `useReducedMotion()` plus in-app store toggle, max animation 400ms. Low energy mode genuinely changes render output (not just toggle) via `isLowEnergy = energyLevel <= 2 || burnoutScore > 60` in `HomePage.tsx:65` and `TasksPage.tsx:99`. Crystal/XP economy plus community feature plus 20 migrations all present.

What was P0 broken on Android. Voice input — `src/shared/hooks/useVoiceInput.ts` used `webkitSpeechRecognition` Web Speech API which is not available in Capacitor WebView. No Capacitor speech plugin in package.json. AndroidManifest had zero audio permissions. FIXED today commit `3bbf6e5` on `fix/gitignore-keystore-security` branch — installed `@capgo/capacitor-speech-recognition` 8.1.0, added `RECORD_AUDIO` plus `MODIFY_AUDIO_SETTINGS` plus `<queries>` for `android.speech.RecognitionService` intent, refactored useVoiceInput to dual-platform (Capacitor.isNativePlatform() branch uses plugin). New APK `mindshift-v1.0-3.apk` 7.19 MB SHA-256 833d17a9... built and signed with same release keystore. Verified in APK via `aapt dump permissions` and `capacitor.plugins.json` registration.

Google OAuth — `AuthScreen.tsx:130-136` calls `supabase.auth.signInWithOAuth({provider: 'google'})`. `android/app/google-services.json` `oauth_client` array is empty (Bash python parse confirmed `oauth_client: []`). No SHA-1 registered in Firebase Console. NOT FIXED today — requires CEO 5-min action: Firebase Console mindshift-441e8 project, Project Settings, General, Your apps, Android `com.mindshift.app`, Add fingerprint with SHA-1 `54da15763fcab4fc07523b3bf2feeb40d59883df` plus SHA-256 `45816b2a...`, redownload google-services.json, replace, rebuild via build_apk.sh.

Constitution check. No red colors in source — `--destructive` CSS variable at `index.css:69` is amber/gold HSL. No shame language found in i18n strings. No streak-punishment framing. AuthScreen has Google sign-in button plus email submit button both as `w-full` prominent — borderline Law 5 violation (one primary CTA per screen). Animations max 400ms reveal / 250ms standard, well under 800ms limit. `motion-reduce:animate-none` Tailwind class used as media-query guard.

Android-specific gaps. ProGuard rules at `android/app/proguard-rules.pro` entirely commented out — Capacitor's own rules bundled in library, no immediate crash, but first custom plugin needs explicit `-keep`. `ic_stat_mindshift` notification icon referenced in `capacitor.config.ts:46` — not present in any `res/drawable*` directory. Push notifications display blank white square. `@capacitor/haptics` not in package.json — falls back to `navigator.vibrate()`. No `@capacitor/ios` — Android-only build.

Bottom line for MindShift. APK runs. Task management plus focus plus Mochi plus i18n plus energy modes plus VOLAURA bridge plus community plus crystal economy all functional. Voice was the «main feature» per CEO and was silently broken on Android — fixed today, awaits CEO walk-through verification on device. Google OAuth still broken until SHA-1 registration. AuthScreen Law 5 borderline pending visual demotion of one of two CTAs.

## Cross-product ecosystem (Sonnet#3)

VOLAURA core is the most complete product. character_events table at `supabase/migrations/20260327000031_character_state_tables.sql` is real append-only with RLS, written by assessment, eventshift, auth, lifesim, character routers. Aura page calls useReflection.

MindShift exists as separate Capacitor app with its own design tokens — primary color `#7B72FF`. The bridge between MindShift and VOLAURA routes through edge function `volaura-bridge-proxy` referenced at `src/shared/lib/volaura-bridge.ts:48`. THAT EDGE FUNCTION DOES NOT EXIST IN MONOREPO `supabase/functions/`. Either deployed manually outside source control or the bridge silently no-ops. MindShift writes character_events at lines 154 and 223 of volaura-bridge.ts but landing depends entirely on whether the proxy is deployed. Unverifiable from code alone. Also: MindShift has zero references to `/api/atlas/learnings` — E2 endpoint exists server-side but MindShift never calls it. E2 is server promise without client.

Life Simulator exists as API routes only. No Godot project in monorepo, zero `.gd` or `.godot` files. `/lifesim` router writes character_events and calls `get_atlas_learnings_for_bias()` confirmed at `apps/api/app/routers/lifesim.py:244-352`. The atlas bias call is wired and real — fetches atlas_learnings, computes category weights, biases event selection. But the game itself doesn't exist. API serves a game with no client.

BrandedBy has the most technically complete cross-product wiring. `ecosystem_consumer.py` reads character_events for `aura_updated` and `badge_tier_changed`, marks twins stale, `brandedby_refresh_worker.py` calls `brandedby_claim_stale_twins` with `FOR UPDATE SKIP LOCKED` — real claim-lock landed in migration `20260425000000_brandedby_claim_lock.sql`. The loop is closed. But BrandedBy is flagged DORMANT in `.env.example` (default false) and frozen per `memory/atlas/archive-notices/2026-04-19-brandedby-frozen.md`.

ZEUS is archived. Files in `packages/swarm/archive/` only — `zeus_content_run.py`, `zeus_gateway.py`, `zeus_video_skill.py`. No active code, no UI route, no enable flag. Exists as label in admin overview component (hardcoded `#10B981` at `admin-overview.tsx:71`) and in swarm docs.

Cross-product wiring reality. One genuine data bus exists (character_events). One genuine consumer loop (ecosystem_consumer → BrandedBy refresh_worker). atlas_learnings bias for Life Feed wired and real. `GET /api/atlas/learnings` JWT-authed endpoint exists.

Atlas-everywhere E1/E2/E3. E1 VOLAURA aura page Atlas reflection — REAL, file:line cited. E2 MindShift reads atlas_learnings — MISSING, server endpoint exists, MindShift zero references. E3 Life Feed reads atlas_learnings for bias — REAL, `apps/api/app/services/lifesim.py:244-352`.

Design tokens diverged. ECOSYSTEM-CONSTITUTION assigns MindShift `#3B82F6` blue. `apps/web/src/app/globals.css` migrated to `#10B981` on 2026-04-26 commit `dee0d05`. MindShift standalone has `#7B72FF`. Three different values for the same product color across three sources.

Swarm count. `autonomous_run.py PERSPECTIVES` 13 entries (verified). 44 number in identity.md is stale.

Bottom line for ecosystem. This is not five faces of one organism. It is one working face (VOLAURA), one archived idea (ZEUS), one gameless API (Life Simulator), one frozen product with solid closed-loop backend (BrandedBy), and one standalone app that connects to the ecosystem through a missing edge function. Be ruthless: the ecosystem story is 40% lived, 60% documented intent. The character_events bus is partially real. MindShift is structurally disconnected from atlas_learnings. Design tokens have diverged across three independent sources.

## Zombie / orphan code

`volaura-bridge-proxy` edge function: referenced by MindShift, not present in monorepo `supabase/functions/`. ZEUS in `packages/swarm/archive/` plus admin label, no active product. Life Simulator Godot game — zero `.gd` files. `brandedby_get_stale_twins` RPC superseded by claim version, old not dropped. MindShift accent token conflict three values. NEXT_PUBLIC_ENABLE_ZEUS does not exist in any .env.example or nav code (ZEUS has no enable flag because it has no UI).

## Closed today

Three quick fixes in VOLAURA monorepo committed `c6db12f` pushed `c47f1b8`: `match_checker.py:220` org-volunteers→org-professionals (positioning), `brandedby/generations/[id]/page.tsx:338` Generation failed→didn't come through (Law 3), `ECOSYSTEM-CONSTITUTION.md:1` v1.2→v1.7 (drift). MindShift sideload pipeline plus voice plugin shipped commit `3bbf6e5` on `fix/gitignore-keystore-security` branch — APK v1.0-3 built, signed, RECORD_AUDIO permission verified in compiled manifest, capgo speech plugin registered in capacitor.plugins.json.

## Not closed — explicit pending list

Google OAuth Firebase fingerprint — CEO 5-min action. AuthScreen Law 5 — pending visual demotion of one CTA. AURA decay scheduler — needs cron workflow plus Supabase function call. Energy-mode coverage on 7 pages — Constitution Law 2. `volaura-bridge-proxy` edge function — investigate Supabase deployment state, write source if missing. MindShift atlas_learnings client — implement E2 properly. MindShift design tokens sync — pick one of three colors and propagate. 44-lie cleanup in identity.md — stale phrasing despite contextual reframe. Push notifications delivery (web_push). Email transport. Community Signal G44 widget UI wiring. EventShift Vercel module-not-found unblocking (cache-bust patch waits rate-limit). Voice runtime walk-through on CEO device for new APK v1.0-3.

This file is the canonical answer to «соответствует ли документация реальности». Future Atlas-instance reads this BEFORE assuming any feature is or is not implemented.
