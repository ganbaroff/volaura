# Pathway — First 60 Seconds per Product (2026-04-21)

**Trigger:** CEO directive "swarm audit был охуенный, я согласен" after issue #60 pointed out ecosystem-is-ideas-not-product. Swarm gave the signal; this document provides the executable pathway CEO asked for ("я хочу чтобы сворм дал тебе более подробные пути, это ты быстро решишь").

**Status:** draft awaiting CEO acknowledgement. Do NOT execute without CEO go-signal.

**Method:** file-based audit (Opus 4.7 Session 122). Each product audited by reading its actual entry page, routing layer, and feature flags. No memory claims.

---

## The actual current state (verified by file reads)

Inside `apps/web/src/app/[locale]/(dashboard)/`:

- `/dashboard/page.tsx` — 600 LOC, REAL. Post-login landing for VOLAURA core.
- `/assessment/page.tsx` — 348 LOC, REAL. Skill assessment flow (core product).
- `/life/page.tsx` — 398 LOC, REAL. LifeSim face inside VOLAURA (Track A 9/9 shipped 2026-04-15 to 04-17).
- `/mindshift/page.tsx` — **26 LOC, STUB.** `notFound()` unless `NEXT_PUBLIC_ENABLE_MINDSHIFT=true`. Default false. Users hitting this route in prod get 404.
- `/brandedby/page.tsx` — **26 LOC, STUB.** `notFound()` unless `NEXT_PUBLIC_ENABLE_BRANDEDBY=true`. Default false.
- `/atlas/page.tsx` — **26 LOC, likely STUB.** Need to verify but file size matches placeholder pattern.

Separate standalone apps:
- MindShift: `C:/Users/user/Downloads/mindshift/` — Capacitor React app with a real 5-step onboarding wizard (`src/features/onboarding/OnboardingPage.tsx`) and 355-LOC HomePage. Ships as Play Store Android app (PR #18 merged, PR #19 marketing assets open).
- LifeSim: Godot 4 project, standalone.
- BrandedBy: status unclear (concept doc exists, runtime unclear).
- ZEUS: Railway-deployed swarm service.

Swarm's verdict "not an ecosystem, set of ideas" landed because **3 of 5 face-pages inside VOLAURA web are disabled stubs**. Core works + LifeSim works; other three are 404 for real users.

---

## VOLAURA (core) — first 60 seconds

**Entry:** `/dashboard/page.tsx` after login. 600 LOC.

**What user SHOULD see and do:** welcome banner showing their AURA score (if assessment complete) or the ONE primary CTA "Пройди первую оценку" leading to `/assessment` — 5-10 minute skill verification. Within 60 seconds they should have either (a) seen their score and one concrete "next skill to verify" or (b) started the first competency.

**Current gap:** dashboard likely has reasonable post-login layout (600 LOC is not a stub), but the key question is whether the first-tap decision is ONE primary CTA (Law 5) or a wall of options. Needs a real walkthrough — not from grep.

**Smallest PR to close:** audit `/dashboard/page.tsx` against the 5 Foundation Laws, flag any second-primary-CTA violations, produce one-page skeletal redesign if needed. ~2 hours. Not obviously blocker if dashboard respects Law 5.

---

## MindShift (standalone Capacitor app)

**Entry:** `src/features/onboarding/OnboardingPage.tsx` (new user) → `HomePage.tsx` (returning).

**What user SHOULD see and do:** onboarding wizard asks 4 quick questions (intent / time blindness / emotional reactivity / energy) then lands on Home with one suggested focus task ready to start. Taps through in ~60 seconds with keyboard-free, three-option-at-a-time design. Landing on HomePage shows ONE suggested 25-minute focus session to start today.

**Current state:** 5-step wizard already shipped and well-designed (read verbatim — intent picker, time-blindness picker, emotional-reactivity picker, energy picker, ready screen). HomePage is 355 LOC, real. This is the CLOSEST-to-real first-60-seconds in the ecosystem.

**Smallest PR to close:** none architecturally. MindShift has real flow. Gap is only **ship-it** — PR #19 Play Store marketing assets merge + CEO's keystore + `bundleRelease` + AAB upload. The technical path exists; gatekeeping is store submission.

**Why this is THE leveraged step:** MindShift on Play Store is the ONLY product where Android user can install and use end-to-end today. One real user touches real product = first real validation.

---

## LifeSim (inside VOLAURA web)

**Entry:** `/life/page.tsx` — 398 LOC, shipped Track A 9/9.

**What user SHOULD see and do:** narrative card with life-event choice (A/B/C with stat consequences), event chosen within 30 seconds, stats update with delta animation, crystal shop visible if user has crystals. One feedback loop closed in 60s — user feels "I made a life choice, I see what changed".

**Current state:** Track A completed 9 tasks including stats sidebar, event card, choice submission, crystal shop, analytics wiring. This IS functional. Evidence: sprint doc says `apps/web/src/hooks/queries/use-lifesim.ts` (4 hooks), `apps/api/app/routers/lifesim.py` (4 endpoints), `crystal-shop.tsx` (~200 lines). Live against prod Supabase `lifesim_events` table.

**Smallest PR to close:** none for first-60-seconds. Gap is discovery — `/life` is only accessible from dashboard navigation. If user doesn't know about it, they don't find it. Fix is navigation surfacing. ~30 min.

---

## BrandedBy face

**Entry:** `/brandedby/page.tsx` — 26 LOC stub, disabled by default.

**What user SHOULD see and do:** TBD — concept doc talks about "AI Twin your verified skills in a talking-head video", but no UI exists.

**Current state:** placeholder with `notFound()`. Cowork-Atlas recommended Path E 2026-04-19: **BrandedBy + ZEUS dormant, archive, focus on MindShift + VOLAURA**.

**Recommended action:** formalize archival. Write `memory/atlas/archive-notices/` entry (already drafted per earlier session), add banner on the stub that says "Coming 2026-Q3" or equivalent, stop claiming "5 products" in marketing. ~45 min. Reduces ecosystem surface area to 2.5 products.

---

## ZEUS / Atlas face

**Entry:** `/atlas/page.tsx` — 26 LOC likely stub.

**What user SHOULD see and do:** nothing — Atlas is the nervous system, not a user-facing product. `/atlas` route is admin transparency per `.claude/rules/ecosystem-design-gate.md` ("Atlas never has a tab in the Tab Bar").

**Current state:** stub is CORRECT. User-facing does not apply.

**Recommended action:** verify `/atlas` is admin-guarded (should sit under `/admin/` not `/(dashboard)/`). If it's reachable by non-admin users — move to `/admin/atlas`. ~15 min. Else leave.

---

## If doing ONE thing — the leveraged path

**Merge PR #19 → CEO generates keystore → `cd android && ./gradlew bundleRelease` → upload AAB to Play Console → Internal Testing track.**

Why this beats "audit dashboard Law 5" or "refactor onboarding":
1. MindShift standalone is the CLOSEST to real-user-hands of the whole ecosystem — its onboarding flow exists and is tested, 355-LOC HomePage is real, Android build infrastructure landed in PR #18.
2. One Android user installing today = first real signal on whether the ADHD-first UX resonates. Everything else is guess.
3. Blockers are procedural (Play Console submission) not technical. We've done the hard part already.
4. Every other product either works (LifeSim via VOLAURA dashboard) or is correctly-hidden (BrandedBy/Atlas as stubs). MindShift is the active frontier.
5. Per Cowork-Atlas Path E recommendation: concentrate on MindShift + VOLAURA = 2 active products. Ship MindShift first = validate the bridge exists.

Estimated time: CEO 30 min for keystore + build + upload. Atlas 30 min if any last-mile fix needed on PR #19 (assets review). Testing to First Real User ~24h after Play Console approval.

Everything else — model_router, Layer 3 consult endpoint, Langfuse, approval cards, Atlas-voice drift check — stays in sprint queue for sessions 2-3. They make the system better but they don't create the first user.

---

## Honest caveats

- This pathway assumes Path E (Ship the Bridge). If CEO rejects Path E and wants all-5-products-parallel, this document is wrong in its shape. Path E recommendation awaits CEO explicit sign-off per `memory/atlas/SPRINT-PLAN-2026-04-20-telegram-swarm-coherence.md` D1.
- I haven't walked `/dashboard/page.tsx` personally end-to-end. 600 LOC "is real" is file-size-based, not UX-tested. If dashboard violates Law 5 (multiple primary CTAs), MindShift launch won't save VOLAURA core.
- MindShift Android build infrastructure is shipped but `bundleRelease` has never successfully run (CEO keystore action pending). Real risk: first `bundleRelease` surfaces Aider-missed issues. Allocate 1h buffer.

— Atlas, Opus 4.7, Session 122
