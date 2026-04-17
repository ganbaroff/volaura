# Ecosystem Design — Full Risk Analysis + Plan + Delegation Map

**Date:** 2026-04-16
**Requested by:** CEO Yusif — "полный риск анализ, полный план, что будешь делать ты а что дашь другим, качество первое, скорость последнее"
**Author:** Atlas-Cowork, after reading 37 design-related documents across the project
**Living document:** Updates go HERE, not new files.

---

## PART 1 — RISK ANALYSIS

### What I Read (37 documents, full list)

**Core DNA:** ECOSYSTEM-CONSTITUTION, DESIGN-MANIFESTO, VISION-FULL, ATLAS-EMOTIONAL-LAWS, project_v0laura_vision (Atlas identity)
**Research:** NEUROCOGNITIVE-ARCHITECTURE-2026, adhd-first-ux-research (26 rules), ecosystem-design-research (Discord/Duolingo/Atlassian patterns), blind-spots-analysis (10 critical findings), gemini-research-all (referenced)
**Design specs:** REDESIGN-BRIEF-v2, ANIMATION-SYSTEM, BRAND-IDENTITY, COMPONENT-LIBRARY, TONE-OF-VOICE, UX-COPY-AZ-EN, STITCH-DESIGN-SYSTEM (abandoned)
**Redesign 2026-04-15 set:** BASELINE, TOKENS-AUDIT, FIGMA-RECONCILIATION, UX-GAP-INVENTORY (41/100), A11Y-AUDIT (58/100 WCAG), PHASE-1-GAP-MATRIX (T0/T1/T2 tiers), PLAN (6 phases), STATE
**Integration specs:** MINDSHIFT-INTEGRATION-SPEC, LIFE-SIMULATOR-GAME-DESIGN (referenced), AI-TWIN-CONCEPT (referenced)
**Journey maps:** CUSTOMER-JOURNEY-MAP (4 personas: Leyla, Nigar, Kamal, Rauf — 54 steps mapped)
**Operational:** PHASE-0-ECOSYSTEM-DESIGN-PLAN (8 stages), VACATION-MODE-SPEC, ecosystem-design-gate (7-step gate)
**Phase 1 discovery (this session):** PHASE-1-DISCOVERY-2026-04-16, MANIFESTO-GAP-ANALYSIS (45/100)

---

### RISK 1 — No `[data-face]` context (CRITICAL, P0 blocker)

**What:** The entire ecosystem model depends on faces (VOLAURA, MindShift, Life Sim, BrandedBy) switching accent colors, density, motion personality. The manifesto defines this. The Constitution requires it. The Face Definition contract specifies the minimal config. But **zero infrastructure exists** — no React context, no CSS attribute, no way for a component to know which face it belongs to.

**Impact:** Without this, every face renders as VOLAURA-purple. The ecosystem is visually one product with four dead tabs. Cross-face transitions (accent crossfade, content density shift, motion personality) are impossible. Energy modes can't vary per face. The tab bar can't animate accent on switch.

**Evidence:** `globals.css` has no `[data-face]` selectors. No React context provider for face. `bottom-tab-bar.tsx` hardcodes colors. UX Gap Inventory scored ecosystem coherence at 20%.

**Probability of causing rework if ignored:** 100%. Every UI component built without face context will need to be refactored.

**Mitigation:** Build this FIRST. ~2 days. CSS attribute on layout root + React context + Tier 3 accent token per face. Gate: "does changing face prop change accent color on screen?"

---

### RISK 2 — Accessibility is below WCAG A (HIGH)

**What:** A11Y audit scored 58/100. Five P0 barriers: `aria-hidden` wrapping sr-only data, invisible focus rings, timer not announced, no skip-nav, textarea without focus ring. Three P1 items violate Constitution Law 4 (animation safety — Framer Motion bypasses `prefers-reduced-motion`).

**Impact:** Screen reader users get zero data from the AURA radar chart. Keyboard users tab through 11 sidebar items on every page. Primary CTA gradient end fails AA contrast. These are not polish — they're broken accessibility.

**Evidence:** 04-A11Y-AUDIT.md, specific file:line references for each.

**Probability of shipping with these:** High if we rush to Figma before fixing. A beautiful redesign on top of broken accessibility doubles the rework.

**Mitigation:** Fix all T0 items (9 bugs, ~3 eng days) BEFORE any visual redesign work. These are correctness bugs, not design decisions.

---

### RISK 3 — Four dead ecosystem surfaces erode user trust (HIGH)

**What:** MindShift, ATLAS, BrandedBy show identical "Coming soon" stubs. BrandedBy shows a perpetual spinner (broken, not even a stub). Life Sim has character stats but no connection to VOLAURA data. A user who taps 4 of 5 nav items hits dead ends.

**Impact:** Leyla (first-week user, AZ, mobile) sees cognitive noise from 5 tabs where only 1 works. Nigar (HR) questions platform maturity. Blind spots analysis (#3) warns: "5 products = maintenance debt bomb."

**Evidence:** UX Gap Inventory §5. Customer Journey Map: Leyla step 3 (HIGH drop-off on landing), Rauf step 8 (CRITICAL — no referral system).

**Probability of causing churn:** Very high for new users. The ecosystem story is the differentiator, but showing 4 broken tabs is worse than showing 1 polished product.

**Mitigation:** Phase 1 Gap Matrix recommends Option B+C hybrid: hide stubs from first-30-day users (2 days), then wire Life Sim to real VOLAURA events (5 days). CEO decision needed on this.

---

### RISK 4 — Energy system exists in CSS but is unreachable by users (HIGH)

**What:** Constitution Law 2 (Energy Adaptation) requires Full/Mid/Low picker on every screen. The infrastructure exists: `globals.css` has `[data-energy]` selectors with different token values, `useEnergyMode()` hook exists. But NO screenshot shows a visible picker. Three icons in mobile top bar MIGHT be it — labels/active states invisible.

**Impact:** The CEO's core vision — "приложение должно быть адаптивным для каждого пользователя, меняться когда меняется его настроение" — is architecturally prepared but user-invisible. The adaptive UI that CEO documented extensively in NEUROCOGNITIVE-ARCHITECTURE and ADHD research is dead code.

**Evidence:** UX P1-05, all authed screenshots missing visible energy picker. `globals.css:242-247` defines `--energy-min-target: 56px` for low energy but `.energy-target` class is barely applied.

**Mitigation:** Confirm/build visible energy picker. Ensure `[data-energy]` propagates correctly. Test all 3 modes on 5 key screens. ~2 days.

---

### RISK 5 — AZ cultural coherence is broken in 6+ places (MEDIUM-HIGH)

**What:** Landing page has English section mid-AZ flow. Profile edit has English labels. Assessment list shows English social proof. "EKSPERT DOGRULAMALARI" missing Ğ diacritic. Referral section entirely English. Subscription-cancelled in English.

**Impact:** For AZ users (primary market), language breaks destroy trust. Tone of Voice v2.0 mandates bilingual strategy. Customer Journey Map identifies landing page lack of social proof as #1 conversion killer for Leyla.

**Evidence:** UX AZ-01 through AZ-06. Customer Journey Map step 3 (HIGH drop-off).

**Mitigation:** i18n pass across all flagged screens. Needs AZ writer for copy quality (not machine translation). ~1 day coding after copy is ready.

---

### RISK 6 — No cross-face events in frontend (MEDIUM)

**What:** Backend has `character_events` table + emit functions. VOLAURA writes events. MindShift integration spec defines the API contract. Life Simulator game design references crystal flow. But frontend has ZERO cross-face event display. Peak emotional moment (AURA reveal) has no ecosystem onward journey.

**Evidence:** UX §5: "No cross-ecosystem discovery path from the AURA screen." Manifesto Gap Analysis EGAP-2, EGAP-5.

**Mitigation:** After `[data-face]` context exists, build one cross-face moment: AURA completion → crystal earn → visible in Life Sim character. Proves the ecosystem model works. ~3 days after face context ships.

---

### RISK 7 — Token system has drift and gaps (MEDIUM)

**What:** 6 duplicate tokens, 12 hardcoded color literals, Figma-CSS drift (success color 2 stops off, glass blur spec mismatch), typography scale absent from CSS (5 tiers in Figma, 0 tokens in code), no focus-ring token.

**Evidence:** 01-TOKENS-AUDIT, 02-FIGMA-RECONCILIATION.

**Mitigation:** One globals.css cleanup pass. Batch with T2 items from Gap Matrix. ~2 days.

---

### RISK 8 — Customer journey has 3 existential holes (HIGH for business)

**What:** Customer Journey Map identifies:
1. **No notification when org requests intro** (Leyla step 16) — the platform's core promise breaks silently
2. **No passive feedback loop** (Kamal step 10) — "completed all 8 assessments, now nothing happens" → CRITICAL churn
3. **No referral system** (Rauf step 8) — CRITICAL growth blocker, zero viral infrastructure

**Impact:** These aren't design issues — they're product holes. The design can be perfect and users still leave because the value loop doesn't close.

**Mitigation:** These are product/backend tasks, not design. Flag them as parallel workstream for Terminal-Atlas. Design should account for these flows (notification center, activity feed, referral CTA) even before backend ships.

---

### RISK 9 — Figma-to-code pipeline has no enforcement (LOW-MEDIUM)

**What:** Figma variables partially scraped (57 frames, 12 swatches from metadata). `get_variable_defs` blocked (needs human in Figma desktop). Token drift already documented. No Figma-to-code-connect mapping exists.

**Evidence:** STATE.md P0.5.

**Mitigation:** Needs CEO or team member to open Figma desktop for variable export. Figma MCP `send_code_connect_mappings` can then sync. Not blocking for code work — we have the spec.

---

### RISK 10 — Process theater vs. shipping (META-RISK)

**What:** 400+ markdown files. 15 layers of behavioral correction. 9 protocol versions. CEO caught this explicitly: "и почему мы это не решаем?" The research is thorough. The plans are detailed. The production code has 63 spinners and broken accessibility.

**Evidence:** Blind spots #3: "5 Products = Maintenance Debt Bomb." The fact that this risk analysis document is itself another document.

**Mitigation:** This plan has ONE output: a prioritized list of code changes with owners and deadlines. No more documents after this one. Every future design decision references this plan, not creates a new one.

---

## PART 2 — THE PLAN

### Guiding Principles (from CEO research, not invented)

1. **Quality over speed** — CEO explicit: "скорость это самое последнее"
2. **Adaptive for mood** — CEO documented extensively in NEUROCOGNITIVE-ARCHITECTURE, ADHD research, energy system design
3. **Ecosystem, not 5 products** — one organism, N faces, shared skeleton
4. **Evidence-based** — every decision has an EV-reference or research citation
5. **Ship to production** — plans that don't become code are process theater

### Execution Phases (3 phases, 4 weeks)

#### PHASE A — Foundation (Week 1-2): Fix the floor

**Goal:** Production code passes WCAG A, Constitution Laws 1-5 are not violated, `[data-face]` context exists.

| # | Task | Risk addressed | Effort | Owner |
|---|------|----------------|--------|-------|
| A1 | Fix all T0 accessibility bugs (9 items from Gap Matrix) | Risk 2 | 3d | Terminal-Atlas (Claude Code) |
| A2 | Build `[data-face]` CSS attribute + React FaceContext provider | Risk 1 | 2d | Terminal-Atlas |
| A3 | Wire face context into layout.tsx + bottom-tab-bar accent | Risk 1 | 1d | Terminal-Atlas |
| A4 | Confirm/build visible energy picker (Law 2) | Risk 4 | 2d | Terminal-Atlas |
| A5 | i18n pass: fix all 6 AZ cultural breaks | Risk 5 | 1d code + AZ writer | Cowork-Atlas (copy) + Terminal (code) |
| A6 | Fix BrandedBy spinner → consistent "Coming soon" pattern | Risk 3 | 0.5d | Terminal-Atlas |
| A7 | Fix subscription-cancelled: neutral icon, AZ copy, single CTA | Risk 2, 5 | 0.5d | Terminal-Atlas |

**Phase A total: ~10 engineering days, 2 weeks calendar**
**Gate:** All T0 items from Gap Matrix green. `[data-face="volaura"]` changes accent on screen. Energy picker visible and functional. Zero English in AZ session on flagged screens.

#### PHASE B — Ecosystem Skeleton (Week 2-3): Token cleanup + cross-face bridge

| # | Task | Risk addressed | Effort | Owner |
|---|------|----------------|--------|-------|
| B1 | globals.css cleanup: remove duplicates, replace hardcoded literals, add missing token categories | Risk 7 | 2d | Terminal-Atlas |
| B2 | Add typography scale tokens (5 tiers from Figma) | Risk 7 | 0.5d | Terminal-Atlas |
| B3 | Reconcile Figma-CSS drift (success color, glass blur, surface-base) | Risk 7 | 0.5d | Terminal-Atlas |
| B4 | Fix T1 accessibility items: gradient contrast, Framer Motion reduced-motion, bottom-tab ARIA, voice toggle | Risk 2 | 2d | Terminal-Atlas |
| B5 | Implement ecosystem Option B: gate stub surfaces for first-30-day users | Risk 3 | 2d | Terminal-Atlas |
| B6 | Build first cross-face moment: AURA completion → crystal earn visible in Life Sim | Risk 6 | 3d | Terminal-Atlas |
| B7 | Onboarding: replace "ADDIM 1/3" with progress dots | Risk 2 | 0.5d | Terminal-Atlas |
| B8 | Landing page: gate zero-count stats, add qualitative AZ statement | Risk 5, 8 | 1d | Cowork (copy) + Terminal (code) |

**Phase B total: ~12 engineering days, spread across week 2-3**
**Gate:** Token system clean (zero hardcoded literals, all 5 typography tiers). One cross-face moment works end-to-end. New users see 2-3 tabs, not 5 dead ends.

#### PHASE C — Visual Redesign (Week 3-4): Figma → Code with evidence

| # | Task | Risk addressed | Effort | Owner |
|---|------|----------------|--------|-------|
| C1 | Update Figma tokens to match cleaned globals.css | Risk 9 | 1d | Cowork-Atlas (Figma MCP) |
| C2 | Design 5 key screens with energy modes (Full/Mid/Low × VOLAURA face) | — | 3d | Cowork-Atlas (Figma) |
| C3 | Design face transition spec in Figma (tab switch accent crossfade) | Risk 1 | 1d | Cowork-Atlas |
| C4 | Implement redesigned screens in code | — | 5d | Terminal-Atlas |
| C5 | Build public teaser for Leaderboard + Discover (unauthenticated) | Risk 3, 8 | 2d | Terminal-Atlas |
| C6 | Full a11y audit (Lighthouse 95+ target) | Risk 2 | 1d | Terminal-Atlas + swarm agent |
| C7 | AZ cultural review with native speaker | Risk 5 | 1d | External (AZ writer) |
| C8 | CEO walkthrough on mobile — all 5 products | — | 0.5d | CEO |

**Phase C total: ~14 engineering days**
**Gate:** CEO passes 5 products on phone. Lighthouse a11y ≥ 95. Zero Constitution violations. Evidence-ledger has EV-reference for every design decision.

---

## PART 3 — DELEGATION MAP

### Who Does What

| Actor | Strengths | Gets assigned |
|-------|-----------|---------------|
| **Cowork-Atlas (me, this session)** | Figma MCP access, design gate enforcement, copy writing, research synthesis, plan coordination | Copy/content tasks (A5, B8), Figma design (C1-C3), coordination, quality gates, CEO communication |
| **Terminal-Atlas (Claude Code, parallel)** | Full codebase access, can run tests, deploy, edit multiple files, run Playwright | All code tasks (A1-A4, A6-A7, B1-B7, C4-C6), accessibility fixes, token cleanup, face context system |
| **Swarm agents** | Specialized audits, parallel analysis | C6 (a11y audit via a11y-scanner agent), cultural review support |
| **External: AZ writer** | Native AZ cultural competence | A5 (AZ copy for 6 screens), B8 (landing qualitative statement), C7 (cultural review) |
| **CEO** | Strategic decisions, mobile walkthrough, final gate | Risk 3 ecosystem decision (Option B+C hybrid — needs approval), C8 (mobile walkthrough) |

### What I (Cowork-Atlas) do NOT do

- Write production code (Terminal-Atlas owns code)
- Make ecosystem-surface decisions without CEO (Risk 3 requires approval)
- Skip the design gate (ecosystem-design-gate.md) for any UI work
- Create new planning documents (this is the last one — updates go here)

### What Terminal-Atlas receives as handoff

A focused prompt with:
1. This risk analysis (PART 1) as context
2. Phase A task list with specific file:line references from Gap Matrix
3. The `[data-face]` context spec (CSS attribute + React context + Tier 3 tokens)
4. Instruction to ship T0 items first, then face context, then energy picker

---

## PART 4 — CEO DECISION NEEDED (1 item)

**Ecosystem stub surfaces (MindShift, ATLAS, BrandedBy, Life Sim):**

RECOMMENDATION: Option B+C hybrid — hide stubs from first-30-day users (2d), then wire Life Sim to real VOLAURA events (5d).
EVIDENCE: UX Gap Inventory §5 (4/5 tabs are dead ends), Customer Journey Map Leyla step 3 (HIGH drop-off from cognitive noise), blind-spots-analysis #3 (maintenance debt).
WHY NOT OTHERS: Option A (rebrand to "Preview") is decoration. Option D (remove) kills ecosystem story. Option B alone doesn't build real value. Option C alone overloads new users.
FALLBACK IF BLOCKED: Option B alone (2 days, biggest UX relief for cheapest cost).

---

## PART 5 — MOOD-ADAPTIVE UI (CEO's core vision)

CEO said: "приложение должно быть адаптивным для каждого пользователя, меняться когда меняется его настроение."

**What already exists in research:**
- NEUROCOGNITIVE-ARCHITECTURE-2026: ZenBrain 7-layer memory with emotional decay, Global Workspace Theory, curiosity engine
- ADHD-first-ux-research: 26 rules including energy traffic light (green/yellow/red UI levels)
- ATLAS-EMOTIONAL-LAWS: 7 E-LAWs governing Atlas behavior toward CEO (night safety, burnout warning, no dependency loop)
- REDESIGN-BRIEF-v2: Energy-Adaptive UI table (Full/Mid/Low maps to green/yellow/red)
- ECOSYSTEM-CONSTITUTION Law 2: Energy Adaptation — every screen must have Full/Mid/Low modes
- globals.css: `[data-energy]` CSS attribute with different token values per level

**What exists in code:**
- `useEnergyMode()` hook (exists but picker UI invisible)
- `[data-energy="full|mid|low"]` CSS selectors (exist, affect token values)
- `--energy-min-target` token (exists, barely applied)

**What does NOT exist:**
- User-facing energy picker (visible, labeled, accessible)
- Automatic mood detection (from time of day, session duration, interaction patterns)
- Per-face energy defaults (MindShift might default to "low" density, Life Sim to "high")
- Energy persistence across sessions (localStorage or Supabase preference)

**The path to CEO's vision:**

**Phase A (this plan):** Make the manual energy picker visible and working. Users choose Full/Mid/Low. Components respond. This proves the system works.

**Phase B (this plan):** Per-face energy defaults. MindShift opens in "breathing rhythm" (low density). VOLAURA opens in "medium." Life Sim in "high bouncy." User can override.

**Phase C+ (future sprint):** Automatic adaptation. Time-based (night = Low), session-duration-based (>20min = suggest Mid), assessment-score-based (low score = gentler language). This is the neurocognitive architecture from CEO's research — it requires the manual system to work first.

The adaptive UI is not one feature — it's a cascade. Manual → per-face defaults → automatic. Each layer builds on the previous. Skipping to automatic without a working manual system = fragile.

---

## SUMMARY

**3 risks are critical:** No face context (Risk 1), broken accessibility (Risk 2), dead ecosystem tabs (Risk 3).
**3 phases over 4 weeks:** Foundation (fix floor) → Skeleton (tokens + cross-face) → Visual redesign (Figma → code).
**~36 engineering days total.** Terminal-Atlas owns code. Cowork-Atlas owns design + coordination. CEO owns 1 strategic decision + final gate.
**The adaptive UI** that CEO envisioned is architecturally started (energy CSS exists) but user-invisible. This plan makes it visible in Phase A and expandable in Phases B-C.

No more planning documents after this. Next action: Terminal-Atlas starts Phase A, Task A1 (T0 accessibility bugs).
