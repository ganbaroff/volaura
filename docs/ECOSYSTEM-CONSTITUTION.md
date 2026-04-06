# ECOSYSTEM CONSTITUTION v1.2
## The Governing Bible of the 5-Product Ecosystem

**Status:** LOCKED — Evidence-based. Built from 17 CEO research documents (~140,000 words), 258+ scientific articles.
**Date:** 2026-04-06
**v1.2 audit:** 3 specialist agents, 34 findings integrated. See REVISION HISTORY.
**Authority:** This document supersedes any design, code, or product decision that contradicts it.
**Scope:** VOLAURA · MindShift · Life Simulator · BrandedBy · ZEUS

> "Система должна знать что делает. Как отвечает. Чем занимается.
> Всё должно быть предельно ясно и только улучшаться."
> — CEO Directive, 2026-04-06

---

## PART 1: THE 5 FOUNDATION LAWS

These are non-negotiable. They cannot be overridden by feature requests, market research, or "competitor does it" arguments.

---

### LAW 1: NEVER RED

**Source:** Research #2 (Clinical ADHD UX), #6 (Sensory UX), #8 (Age-Based UX)
**Science:** Red triggers RSD (Rejection Sensitive Dysphoria) responses in ADHD users. Age-independent — affects Gen Z, Millennials, Gen X equally when RSD is present.

**Rule:**
- Zero red anywhere in the UI of any product
- Errors → purple (`#D4B4FF`, container `#3D1A6E`)
- Warnings → amber (`#E9C400`, container `#3A3000`)
- Destructive actions → amber (not red)
- Progress bar depletion → purple (not red)

**Prohibited:**
- `text-red-*`, `bg-red-*`, `border-red-*` in any Tailwind class
- `#FF0000`, `#DC2626`, `#EF4444` or any red-family hex
- "Danger" badges in red
- Error toasts in red

**Products:** ALL FIVE

---

### LAW 2: ENERGY ADAPTATION

**Source:** Research #2 (Clinical ADHD), #3 (Burnout Prevention), #6 (Sensory UX)
**Science:** ADHD users have highly variable energy states. Forcing full-complexity UI on a "red day" triggers executive dysfunction cascade. Energy-adaptive design = 40% higher retention.

**Rule:** Every product must have at minimum 2 UI modes:
- **Normal mode:** Full features, moderate animations
- **Low-energy mode:** Single-action card, fade-in only, warm non-directive copy

**Implementation:**
```
Full  (4-5 energy): Full UI, all animations, all widgets
Mid   (3 energy):   Reduced widgets, entrance-only animations, "Ready?" gate for assessments
Low   (1-2 energy): Single action card, fade-in only, assessments hidden
```
⚠️ User-facing labels MUST use Full/Mid/Low (or equivalent). NEVER show "Red day" to users —
this violates Law 1. Internal code constants may use green/yellow/red semantics only.
Visual representation of a low-energy state uses purple or amber, never red.

**Trigger:** User self-reports via EnergyPicker (1-5 scale). Never infer without consent.

**Products:** MindShift (fully built), VOLAURA (assessments gate), Life Simulator (quest complexity), BrandedBy (content volume)

---

### LAW 3: SHAME-FREE LANGUAGE

**Source:** Research #2 (Clinical ADHD), #10 (Overjustification), #16 (Neurocognitive Architecture)
**Science:** Shame activates the same neural pathways as physical pain in ADHD brains. "You haven't done X" language causes measurable cortisol spikes and 78% abandonment.

**Banned phrases across ALL products:**
| Banned | Replace with |
|--------|-------------|
| "You haven't done X yet" | (Remove entirely) |
| "Profile X% complete" | (Remove entirely) |
| "You're X days behind" | (Remove entirely) |
| "Unlock" | "Earn" or remove |
| "Remaining" in progress | "Completed" |
| "0 of X completed" | (Show nothing or "Start →") |
| "You failed" | "Try again" or "Something went wrong" |
| "Wrong answer" | "Different perspective" or no label |
| Streak shame on break | (No streak display when = 0 or 1) |
| Lock icons for achievements | (Hide locked achievements entirely) |

**Neuro-affirming framing:**
- Errors = system issues, not user mistakes ("Something didn't connect" not "You entered wrong")
- Empty states = one warm invitation, not a list of what's missing
- Return after absence = warm welcome, never guilt

**Products:** ALL FIVE — every user-facing string

---

### LAW 4: ANIMATION SAFETY

**Source:** Research #1 (Screen-shaking rejected), #2 (Clinical ADHD), #6 (Sensory UX)
**Science:** Inappropriate animation triggers vestibular disruption, sympathetic nervous system activation (fight-or-flight), and attention fragmentation in neurodivergent users.

**Safe/Unsafe Matrix:**
| Animation | Verdict | Specification |
|-----------|---------|---------------|
| Page fade 200ms | ✅ SAFE | Keep |
| Progress bar fill | ✅ SAFE | Keep |
| Button press 0.98 scale | ✅ SAFE | Keep |
| Spring entrance (damping ≥14) | ✅ SAFE | User-initiated only |
| Score counter 2s count-up | ❌ UNSAFE | Show instantly or max 800ms |
| Badge reveal (bounce+rotate+sparkle) | ❌ UNSAFE | Scale only, gentle spring |
| Confetti 50 particles | ❌ UNSAFE | 12 particles max, 1.5s, contained |
| Notification pulse (infinite) | ❌ UNSAFE | 3 pulses then stop |
| Floating orbs (15s loop) | ❌ UNSAFE | Remove from action screens |
| Screen shake | ❌ NEVER | Zero exceptions |

**Mandatory:** Every animation MUST have `prefers-reduced-motion` branch.
**Maximum:** 1 animated number per screen at any time.
**Forbidden:** Infinite loops on any action screen (celebration only, on separate screen).

**Products:** ALL FIVE

---

### LAW 5: ONE PRIMARY ACTION

**Source:** Research #2 (Clinical ADHD), #4 (Onboarding UX), #6 (Sensory UX)
**Science:** Working memory in ADHD = ~1.5 items (vs 7±2 neurotypical). Multiple simultaneous CTAs = decision paralysis = exit. Fogg Behavior Model: motivation collapses when activation energy is too high.

**Rule:**
- Every screen: exactly ONE primary CTA (gradient/filled button)
- Every screen: ≤5 tappable elements visible without scroll on mobile
- Empty states: ONE warm action card
- Dashboards: secondary actions are ghost/text links, never competing filled buttons
- Forms: no "Save and continue" + "Save draft" + "Cancel" at equal visual weight

**Products:** ALL FIVE

---

## PART 2: THE 7 CRYSTAL ECONOMY LAWS

**Source:** Research #10 (Overjustification Effect) — The most important research for all reward mechanics
**Science:** Aggressive gamification switches brain from empathy network (ACCg) to self-reward network (VTA). For intrinsically motivated users, this DESTROYS the original motivation. Examples of failures: Yahoo Answers (quality destroyed by points), Google News Badges (ignored), Strava deaths (performance pressure overrode safety).

---

### CRYSTAL LAW 1: Informational > Controlling

Feedback must tell users what they did, not what they should do next.
- ✅ "Your communication score reflects 3 strong examples of active listening"
- ❌ "Earn 50 crystals by completing 3 more assessments"

### CRYSTAL LAW 2: Unexpected > Expected

Rewards that are contingent ("do X → get Y") destroy intrinsic motivation faster than no rewards at all.
- ✅ Surprise crystal drop after session (user didn't know they'd earn crystals)
- ❌ "Complete this quiz → 10 crystals" shown before the quiz

### CRYSTAL LAW 3: Impact > Abstraction

Connect earnings to real-world meaning, not abstract numbers.
- ✅ "Your AURA score helped 2 organizations shortlist you"
- ❌ "You have 2,450 XP"

### CRYSTAL LAW 4: Identity > Currency

Status framing retains motivation. Currency framing destroys it.
- ✅ "Gold-level Communicator" as headline, AURA 78.4 as subtitle
- ❌ "78.4" as headline, "Gold" as decoration

### CRYSTAL LAW 5: Collaborative > Zero-Sum

Competition between users = social comparison = shame spiral. Collective wins are safe.
- ✅ "Focus Rooms" (shared presence, not rankings)
- ❌ Leaderboards of any kind

### CRYSTAL LAW 6: Gamify Admin, Not Mastery

Gamification of intrinsically rewarding tasks (deep work, genuine skill) corrupts the activity.
Gamification of boring admin tasks (filling profile, setting availability) is safe.
- ✅ Crystals for completing profile (admin task)
- ❌ Crystals visible during or immediately after an assessment (mastery task)

### CRYSTAL LAW 6 AMENDMENT: Badge Is Not An Immediate Contingent Reward

The original Crystal Law 6 bans gamifying mastery tasks. Agent audit found an internal contradiction: the badge tier display shown immediately after assessment completion IS a contingent reward for a mastery task — violating the law.

**Correct pattern:**
- Assessment ends → show competence explanation only ("Your communication reflects active listening in response 3")
- Badge tier update shown on Profile page at NEXT visit — as a surprise discovery
- Telegram notification 4 hours later: "Your AURA updated — see what changed." NEVER "You completed the assessment — here is your Gold badge"
- Badge tiers are never shown as a goal during or immediately after assessment

### CRYSTAL LAW 7: Monitor Metric Distortion

When metrics improve but underlying behavior degrades = overjustification.
Track: speed↑ but quality↓, completion↑ but depth↓, logins↑ but engagement↓
If distortion detected → remove the reward mechanic immediately.

---

## PART 3: RESEARCH-BY-RESEARCH DESIGN RULES

### Research #1 — Gen Z Engagement (Octalysis + SDT + Fogg)

**Approved for adoption:**
- Sunk Cost Registration: deliver value BEFORE login (Quick Start, skill preview)
- Three C's Framework (Community Impact + Connections + Careers) — VOLAURA landing framing
- Mentor pairing: Gold badge holders mentor Bronze (VOLAURA feature)
- Group quests for social proof (MindShift Focus Rooms + VOLAURA cohort challenges)

**Rejected (ADHD conflict):**
- BeReal 2-minute windows / FOMO mechanics — anxiety trigger
- Flash Impact timers — Black Hat Octalysis, scarcity-driven
- "68% open in 3 minutes" metric — task-switching costs 23 minutes to recover
- Screen-shaking celebrations — sensory overload
- No-context high-pressure challenges

---

### Research #2 — Clinical ADHD UX (Foundation Document)

**This is the foundational spec for MindShift. 90% already implemented.**

Critical rules for all products:
- Adenosine debt: hard-stop after 90-120 minutes of focus (prevent hyperfocus crash)
- 66% Principle: never fill more than 2/3 of any container (NOW≤3, NEXT≤6)
- Ghosting Grace: users can exit without guilt, warm re-entry card offered
- AI body doubler: observational companion, not evaluative supervisor
- Progressive disclosure: never show ≥8 settings sections nested
- One-primary-action screens: enforced especially on onboarding

**Not yet built (backlog):**
- On-device phenotyping (Year 2+)
- Dyslexia-friendly font size control (pre-scale Sprint)
- Privacy panel with granular data sharing toggles (pre-org-search blocker)

---

### Research #3 — Burnout Prevention

**Key patterns (75% already in MindShift):**

| Season | UI Level | Assessment/Tasks |
|--------|----------|-----------------|
| Launch | Full | Available |
| Maintain | Normal | Normal gate |
| Recover | Simplified | Optional only |
| Sandbox | Minimal | Exploration only |

**Not yet built across ecosystem:**
- Next Tiny Action prompt (reactive-to-proactive bridge)
- Quarterly Review (90-day analytics, not weekly)
- Anti-Resolution protection (January behavioral change prevention)
- Routine Resetter (LEGO metaphor for rebuilding after disruption)

**Rule:** Never block (except hard 90-min stop). Always nudge. User retains autonomy.

---

### Research #5 — Market Intelligence

**Positioning (LOCKED):**
- ADHD app market: $2.22B (2025) → $10B (2035), CAGR 15-16%
- MindShift position: FREE entry product to 5-product ecosystem
- Monetize via: crystal economy, Life Simulator cosmetics, VOLAURA B2B
- This is the Duolingo model — massive free base, premium on top

**Competitive moats:**
- Body doubling: Focus Rooms (free vs Focusmate $10/mo)
- ADHD ethics: no red, no punishment, no lock icons
- Ecosystem: single auth across 5 products
- Portability: AURA Score is your professional "Fast Pass"

---

### Research #6 — Sensory UX

**Audio architecture rules:**
- Default noise: pink (not brown/white) — g=0.249 effect size for ADHD
- 16 Hz amplitude modulation > binaural beats for focus (119% beta power increase)
- Haptic: 0.2 BPM sustained rhythm for sustained attention, not just discrete events
- AudioWorklet: pre-render server-side to avoid 128-sample mobile distortion

**Visual rules:**
- Dark mode: `#0F1117` default (OLED-safe cool gray)
- Contrast: WCAG 4.5:1 minimum BUT adjustable — >14:1 harmful for dyslexia
- Reduced motion: `prefers-reduced-motion` on every animated element (non-optional)

---

### Research #7 — PWA Architecture

**Our architecture is validated at every layer:**
- Zustand + idb-keyval + partialize = correct pattern
- Offline queue = optimistic mutations + outbox (correct for current scale)
- Event sourcing via `character_events` table = cross-product validated
- AI i18n = inject locale into LLM prompt (exact match)

**Known gaps to address:**
- Voice data privacy: disclose routing to Google/Apple in privacy policy
- PostHog: upgrade to Bayesian A/B testing (< 1000 users = Bayesian > frequentist)
- CSS Container Queries: tablet readiness quick win
- WHISK context hygiene: CLAUDE.md pruning schedule needed

---

### Research #9 — B2B Volunteer/Professional Framework

**VOLAURA B2B rules:**
- AURA Score = portable skill Fast Pass (not just credential, not just badge)
- Adaptive UI per user type: volunteer sees events, HR sees dashboard, ADHD user sees focus
- Ghosting Grace in VOLAURA context: 41% industry ghosting solved by warm re-engagement
- Micro-shift architecture: 30-60 min volunteer slots align with MindShift focus model

**WTP by sector (pricing guidance):**
- Healthcare/Disaster relief: highest
- Education/Youth: high (child protection mandates)
- Sports mega-events: high (volume)
- Corporate CSR: medium
- Tech/Cultural events: entry

---

### Research #10 — Overjustification Effect

**CRITICAL for all reward design. See Part 2 (Crystal Economy Laws).**

**Immediate changes needed:**
1. Crystal chip: move from post-session view to Progress page (don't show in vulnerability window)
2. XP total: replace "2,450 XP" with "Level 3 · Grower" everywhere
3. Locked achievements: hide entirely (not lock icon — invisible until earned)
4. VR multiplier: keep math, hide formula from user
5. Language audit: "earned" replaces "unlock", "contributed" replaces "completed for reward"

---

### Research #12 — Multi-Model AI Routing

**ZEUS model routing table (authoritative):**

| Task Type | Model | Rationale |
|-----------|-------|-----------|
| Volume/formatting/linting | Llama 8B (Groq) | Free, fast, correct for rote work |
| Security/risk analysis | DeepSeek Chat | Specialized edge-case reasoning |
| Creative/content/copy | Gemini 2.0 Flash | Speed + fluency |
| General reasoning/code | Llama 3.3 70B (Groq) | Balanced, free tier |
| Architecture/deep synthesis | Gemini 2.5 Pro | Reserved for high-value only |

**5 anti-patterns found in current ZEUS — must fix:**
1. All-same-model routing (partially fixed via PM agent)
2. State in markdown files → needs structured DB (long-term)
3. Agents fully constrained or fully autonomous — no gradient
4. Data passes through agents that don't transform it (wasteful)
5. 47 agents before 100 users (scope creep)

---

### Research #13 — Persistent Memory Architecture

**ZEUS memory mapping (neuroscience → code):**

| Brain | ZEUS Equivalent | Status |
|-------|----------------|--------|
| Hippocampus (fast encoding) | memory/swarm/episodic_inbox/ | ✅ Basic |
| Neocortex (semantic storage) | memory/swarm/shared-context.md | ✅ Manual |
| SWS Replay (offline reactivation) | GitHub Actions daily 09:00 | ✅ No extraction |
| REM Pruning (forgetting noise) | NOT IMPLEMENTED | ❌ Critical gap |
| Amygdala (salience tagging) | Career ladder scoring | ✅ Partial |

**3 functions needed (<100 lines Python each):**
1. `log_episodic_memory()` — non-blocking JSON dump per agent run
2. `sleep_cycle_consolidation()` — cron every 6h, PEI filter, ECHO hindsight, prune
3. `initialize_agent_with_memory()` — inject Global_Context.md into every agent system prompt

**Security:** GTG-1002 pattern — shared memory across agents = attack surface. Safety boundaries required.

---

### Research #14 — Human-AI Team Dynamics

**Bottleneck is CEO validation time, not AI generation speed.**

**Sprint template (both products):**
- Day 1: CEO writes FEATURE.md → AI generates SPEC.md + STATE.md
- Days 2-4: Execution bursts, CEO reviews at mid-day gates
- Day 5: Validation + retrospective + memory compaction

**Model routing (calibrated per task):**
| Task | Model |
|------|-------|
| UI tweaks, linting | Haiku / Llama 8B |
| Core logic, API integration | Sonnet |
| Architecture, irreversible decisions | Opus |

---

### Research #15 — VOLAURA Assessment Architecture (Critical)

**8 critical fixes before beta:**

| # | Fix | Priority |
|---|-----|----------|
| 1 | MIRT upgrade: 8 independent 1D CAT → 1 multidimensional test (θ vector + Σ matrix) | P0 |
| 2 | Bayesian IRT calibration from real user data (MMLE pipeline) | P0 |
| 3 | ASR routing: Soniox (7.9% WER) for Azerbaijani, Deepgram for English (Whisper = 19.5% WER on AZ) | P0 |
| 4 | Prosodic features: F0, intensity, articulation rate → add to BARS scoring | P1 |
| 5 | Differential skill decay half-life (see table below) | P1 |
| 6 | Agent-to-agent JSON Schema contracts (AgentAssert pattern) | P1 |
| 7 | DIF monitoring: Mantel-Haenszel test when N>500 per language | P1 |
| 8 | SDT gamification: autonomy choice + competence explanation + relatedness via peer calibration | P1 |

**AURA Score Decay Half-Life Table (authoritative):**
| Category | Competencies | Half-life |
|----------|-------------|-----------|
| Technical/Procedural | tech_literacy, event_performance | 730 days (2 years) |
| Linguistic | english_proficiency | 1095 days (3 years) |
| Fundamental Soft Skills | communication, reliability, adaptability | 1460 days (4 years) |
| Deep Social Patterns | empathy_safeguarding, leadership | 1640 days (4.5 years) |

**ISO 10667-2 Compliance Gaps:**
- Informed consent must disclose AI processing explicitly
- Open Badges 3.0 payload needs: model version, IRT params, SE, confidence intervals
- DeCE scoring: every score needs extracted_concept + quote + confidence

---

### Research #16 — Neurocognitive Architecture

**New feature from this research — NOT YET BUILT:**
Implementation Intentions ("If-Then" plans):
- "If I open social media during work → I close it and take 3 breaths"
- Pre-committed behavioral rules that bypass executive function
- Research shows: significant improvement in impulse suppression for ADHD
- UX: before each focus session, user sets 1-2 "If-Then" rules

**Everything else confirmed already built.**

---

### Research #17 — AI-Assisted Development

**Skeleton vs Tissue pattern (formalize immediately):**
- SKELETON files: human writes, defines interfaces + security + auth contracts (e.g., `useAuthInit.ts`)
- TISSUE files: AI fills business logic within skeleton constraints (e.g., `PostSessionFlow`)
- Action: mark files in CLAUDE.md as SKELETON (human-only) or TISSUE (AI-safe)

**Context hygiene (WHISK adoption needed):**
- Isolate: each task = separate session, don't accumulate context
- Keep compressed: CLAUDE.md pruning schedule (quarterly)
- Measure: track CEO hours spent on validation per sprint

---

## PART 4: PRODUCT-SPECIFIC IMPLICATIONS

### VOLAURA — Verified Competency Platform

**Core promise:** "Prove your skills. Earn your AURA. Get found by top organizations."

**Design rules specific to VOLAURA:**
1. Achievement display: "Gold-level Communicator" headline, AURA 78.4 subtitle (NEVER reverse)
2. Assessment UX: one question per screen, ≤4 answers without scroll, no timer visible
3. Break every 5 questions (ADHD cognitive load limit)
4. Interim scores HIDDEN (shown only on final results screen)
5. Badge tiers as surprises — hidden until earned, NO lock icons. NEVER shown immediately post-assessment (Crystal Law 6 Amendment).
6. Low energy → assessment HIDDEN or shown with "Ready when you are" card
7. Profile discovery toggle = visible in edit profile, default OFF (user chooses)
8. Org search = data firewall — ADHD/health data NEVER reaches employer side
9. AURA score decay = differential by competency (Research #15 half-life table)
10. Voice assessment: Soniox for Azerbaijani, Deepgram for English (NOT Whisper). Existing Whisper sessions tagged `evaluation_mode: whisper_legacy` and queued for re-evaluation.
11. MIRT architecture: engine must maintain `theta_vector: list[float]` (8 dimensions) + `sigma_matrix: 8×8` covariance. Item bank schema requires `mirt_a_vector: list[float]`. Prior Sigma estimates: communication↔leadership≈0.6, tech↔event_performance≈0.4, communication↔empathy≈0.55.
12. Assessment onboarding must offer scenario framing choice (3 domains: ecology/sports/social) before first question — SDT Autonomy lever, IRT validity unchanged.
13. Score explanation must produce: "Your [competency] reflects [specific behavioral evidence from DeCE quote]" — never a number alone.
14. VR multiplier (self=1.00, org=1.15, peer=1.25): disclose in general terms to users ("Scores verified by your org carry additional weight") but never the exact formula. Satisfies ISO 10667-2 without transactional framing.
15. Org discovery results show: "Leadership: 82 · Assessed 3 months ago · v2.1" — score + date + assessment version always together.
16. B2B Tier Architecture:
    - Tier 1 (Verify): basic discovery, AURA search, intro requests — free/freemium
    - Tier 2 (Manage): QR check-in (5-sec vs 30-sec manual), roster management, Telegram bulk messaging — per-event pricing
    - Tier 3 (Certify): ISO 10667-2 package, DIF audit reports, SLA, audit trail export — annual per-seat
17. DeCE "Show Your Work" endpoint (`/aura/me/explanation`) is a primary B2B differentiator — must be surfaced in org volunteer profiles as a 2-sentence competency evidence summary.
18. ASR Fairness Rule: language-detected routing (langdetect on first 3s or profile locale as prior). Scores under Whisper before routing ships are flagged and queued for re-evaluation.
19. Onboarding Screen 1 must include AI processing disclosure (ISO 10667-2 G18) — one sentence, non-dismissable.
20. Ghosting Grace for professionals: 30 min before event start with no check-in → single warm Telegram/push ("Ready to check in? Tap here"). Auto-ping next-ranked backup volunteer if cancellation within 2 hours of start.

**Color system:**
```
Surface base:    #0A0A0F
Surface 1:       #13131B
Card:            #1B1B23
Elevated:        #1F1F27
High:            #292932
Highest:         #34343D

Primary:         #C0C1FF
Primary Deep:    #8083FF
Success:         #34D399
Warning:         #E9C400
Error:           #D4B4FF (PURPLE — NEVER RED)
Gold:            #FFD700
```

---

### MindShift — Daily Focus & Habit Platform

**Core promise:** "Focus tools designed for ADHD brains."

**Design rules specific to MindShift:**
1. Hard stop at 90 minutes — with 3-stage graceful warning: 80min subtle progress shift → 85min Mochi "let's start wrapping up" → 90min session ends. NO sudden cutoffs.
2. 66% capacity guardrail: NOW≤3 tasks, NEXT≤6 tasks
3. Streaks: invisible when 0 or 1. Show cumulatively, not as current streak
4. Season system: Launch/Maintain/Recover/Sandbox modes
5. Recovery Protocol: archive overdue, micro-win, never shame
6. AI companion Mochi: observer not evaluator, peer not authority
7. Audio defaults: pink noise (not brown/white) — highest ADHD effect size (g=0.249)
8. Crystal chip: show on Progress page ONLY, never in NatureBuffer or post-session screen
9. XP display: "Level 3 · Grower" not "2,450 XP"
10. Focus Rooms: collaborative presence, anonymous, never ranked
11. Onboarding Screen 1 must include a proactive shame-free contract: "No streaks lost, no red badges, no penalties — ever." (clinical trust signal, not marketing copy)
12. Onboarding must ask: "What usually breaks your flow?" — 3-4 options (Burnout / Too many tasks / Blank page fear / Distractions). Seeds Mochi's initial tone and SpicinessPicker default.
13. If-Then Implementation Intentions: prompt appears BEFORE session start (not on dashboard). Mochi reads back the rule at session confirmation. If user exits early, Mochi references it once, non-judgmentally.
14. Hyperfocus pattern detection: track skipped transition buffers across sessions. Flag after 3 consecutive skips → offer Recovery Week prompt (never force).
15. Tab churn monitoring via Page Visibility API: after 3 tab switches within 10 minutes → Mochi offers 2-min micro-intervention (never a lecture).

---

### Life Simulator + claw3d — 3D Agent Office & Character Progression

**Core promise:** "Your real-world growth becomes your character's story. The agents you work with become your living team."

**Architecture (as of 2026-04-06):**
- Runtime: Next.js + Three.js + React Three Fiber (`claw3d-fork/`)
- Dev: `http://localhost:3000`
- Repo: `https://github.com/ganbaroff/Claw3D` (branch: `main`)

**10-State Agent Model (Phase 1 — DONE):**
```typescript
type OfficeAgentState =
  | "idle"       // no task, available          → #f59e0b, no ring
  | "focused"    // deep work / just finished   → #06b6d4, slow cyan ring
  | "working"    // actively processing         → #22c55e, fast green ring
  | "waiting"    // awaiting input/approval     → #eab308, medium yellow ring
  | "blocked"    // dependency unresolved       → #f97316, fast orange ring
  | "overloaded" // too many tasks              → #c084fc, very fast PURPLE ring  ← Law 1: no red
  | "recovering" // after error                 → #a855f7, slow purple ring
  | "degraded"   // partial functionality      → #6b7280, very slow ring
  | "meeting"    // in standup                  → #3b82f6, steady blue ring
  | "error";     // critical error             → #f97316, fast orange ring        ← Law 1: no red
```
**Law 1 applies here.** `#ef4444` is prohibited. Purple (`#c084fc`) = overloaded. Orange (`#f97316`) = error.

**Phase 2 open tasks (P1):**
- Ready Player Me avatars via `useGLTF`
- Wire `agent.wake` events → explicit state transitions
- `blocked/overloaded/recovering` state derivation in `deriveOfficeState()`
- RemoteAgentChatPanel: sync agent responses to cloud (Z-02)

**Design rules specific to Life Simulator:**
1. Character progression = reflection of real activities (not arbitrary grinding)
2. Crystal spends are player-chosen, never coerced by mechanics
3. Low-energy mode: simpler quests, no timed events
4. Achievements: always surprise drops, never visible countdowns
5. Character skills map to VOLAURA competency weights
6. Social: collaborative guilds/focus rooms (no PvP leaderboards)
7. Game difficulty: user-set Spiciness level (easy/medium/hard = teal/gold/purple)
8. Agent states reflect human rhythms: fatigue, attention, recovery ("они как я")

---

### BrandedBy — AI Professional Identity

**Core promise:** "Your professional presence, amplified by AI."

**Design rules specific to BrandedBy:**
1. Content generation: never auto-post without explicit approval
2. AI twin framing: assistant, not replacement ("Your AI amplifies you")
3. Low-energy mode: pause scheduling, no pressure to create
4. Video volume: default ≤3 per week, user-controlled cadence
5. Identity language: "Your voice, your perspective" — AI as tool not author

---

### ZEUS — Autonomous Agent Framework

**Core promise:** "The autonomous backbone of the ecosystem."

**Architecture (as of 2026-04-06) — TWO DISCONNECTED SYSTEMS:**

⚠️ The Python swarm and Node.js gateway share ONLY the filesystem. Zero WebSocket connections, zero HTTP calls between them. This is the current reality — not the target architecture.

| System | Location | Agents | Trigger | Memory |
|--------|----------|--------|---------|--------|
| Node.js Gateway | `claw3d-fork/server/` | 39 (static) | Real-time events (Railway/GitHub/Sentry webhooks) | `claw3d-fork/memory/session-context.md` |
| Python Swarm | `packages/swarm/` | 44 (hive lifecycle) | GitHub Actions cron (09:00 Baku daily) | `memory/swarm/shared-context.md` |

**Planned bridge (20 lines Python):** Python swarm sends HIGH/CRITICAL findings to Node.js `/event` endpoint → unified real-time visibility.

**Node.js Gateway:**
- Deployed: Railway `wss://zeus-gateway-production.up.railway.app` + pm2 locally
- WebSocket protocol: `chat.send` / `swarm.run` / `swarm.auto`

**Provider hierarchy (authoritative — Research #12):**
```
Cerebras Qwen3-235B     (primary, 2000+ tokens/sec)
  → Gemma4 via Ollama   (local GPU, zero rate limit)
  → NVIDIA NIM          (backup, Nemotron 253B)
  → Anthropic Haiku     (last resort only)
```

**Event-driven architecture (NOT cron):**
```
Railway/GitHub/Sentry → POST /webhook (HMAC verified)
  → classifyEvent() → wakeAgent() → finding → kanban
```
Cron replaced by events — agents idle until real signal arrives.

**Shared brain (session-context.md injection):**
- Every agent receives: `session-context.md` + `cto-kanban.md` + `AGILE-RULES.md`
- After each audit cycle `swarm-synthesizer` updates `session-context.md`
- User memory: `memory/users/{userId}.md` — max 800 chars, injected per request
- Session debriefer: writes `memory/debriefs/` after 4+ exchanges, last 3 injected into all agents

**Rules specific to ZEUS:**
1. Never show agent computation cost/tokens to user (overjustification risk)
2. Memory consolidation: 6-hour cron, PEI filter, ECHO hindsight (Research #13)
3. Safety boundary: agents cannot weaponize shared memory (GTG-1002 pattern)
4. Model routing: Cerebras → Gemma4 → NVIDIA → Anthropic (never all-same)
5. Dead weight tracking: tokens consumed vs findings produced per agent
6. Epsilon-greedy exploration: 5% random routing to prevent overfitting
7. Agents must flag if their context is >7 days old
8. Hard ban: agent must NEVER say "как языковая модель" or "я не могу" (instant fail)
9. pm2 manages gateway — `pm2 restart zeus-gateway --update-env` (never kill)

**ZEUS Product API (missing — must be defined before calling ZEUS "a product"):**
Until these exist, ZEUS is a batch pipeline, not a product:
- Authenticated API endpoint per ecosystem product (MindShift, VOLAURA, Life Sim)
- Request/response protocol (not fire-and-forget)
- SLA definition (response time per request type)
- Fallback behavior when ZEUS unavailable

**Two-swarm bridge (P1, ~20 lines Python):**
Python `autonomous_run.py` → POST HIGH/CRITICAL findings to Node.js `/event` endpoint (authenticated with `GATEWAY_SECRET`). Makes Python findings visible in 3D office in real-time.

**Python swarm also needs:**
- `initialize_agent_with_memory()`: inject last 3 entries from `agent-feedback-distilled.md` into each agent's system prompt (~15 lines in `_build_agent_prompt()`)
- Extract model routing table from gateway into `server/zeus-config.js` (SKELETON file)

**P0 open tasks:**
- JWT auth in WebSocket handshake (code ready in `memory/agent-findings/`, needs deploy)
- WEBHOOK_SECRET setup in Railway for GitHub/Sentry/Railway webhooks
- GTG-1002 defense: define which agents can write to which files, sanitize agent responses before writing to shared-context.md (this is a P0 security requirement, not just a guardrail)

---

## PART 5: 37-ITEM ADHD DESIGN CHECKLIST

**Run this checklist on EVERY screen before shipping.**

### Cognitive Load (every screen)
- [ ] Exactly ONE primary CTA
- [ ] ≤5 tappable elements visible without scroll (mobile)
- [ ] Zero comparison language
- [ ] Zero red color
- [ ] Errors framed as system issues, not user mistakes
- [ ] Zero "you haven't done X yet" language
- [ ] Zero countdown timers or deadline urgency
- [ ] Locked achievements HIDDEN (no lock icons)
- [ ] Streak hidden when 0 or 1
- [ ] Works on "red energy day" (reducible to single action)

### Animation Safety (every animated element)
- [ ] Respects prefers-reduced-motion
- [ ] Duration under 800ms for non-decorative
- [ ] Zero infinite loops on action screens
- [ ] Zero simultaneous animations on different elements
- [ ] Particle count under 15
- [ ] Bouncy spring ONLY for user-initiated, never entrance
- [ ] No floating/drifting on focus screens
- [ ] Score counter under 1 second

### Shame-Free Language (every string)
- [ ] No "unlock" (use "earn" or remove)
- [ ] No "remaining" in progress (use "completed")
- [ ] No profile completion percentage
- [ ] Badges as surprises, not visible goals
- [ ] Empty state = one warm action, not a list
- [ ] Return-after-absence = warm, not guilt
- [ ] Errors say what happened, not what user did wrong

### Assessment-Specific (VOLAURA)
- [ ] One question per screen
- [ ] ≤4 answer options without scroll
- [ ] Timer hidden
- [ ] Progress shows "X of ~Y completed" (filled, not depleted)
- [ ] Break point every 5 questions
- [ ] Interim scores hidden
- [ ] Exit + resume within 24h without loss
- [ ] Micro-confirmations subtle (checkmark fade, no sound, no score)

### Energy Adaptation (every product)
- [ ] Energy detection or manual input available
- [ ] Low energy: assessment hidden or gated with "Ready when you are"
- [ ] Low energy: fade-in only animations
- [ ] Low energy: single card dashboard
- [ ] Low energy: warm non-directive copy

---

## PART 6: UNIVERSAL GUARDRAILS TABLE

These 17 guardrails apply to all 5 products. No exceptions.

| # | Guardrail | Source | Products |
|---|-----------|--------|---------|
| G1 | Zero red anywhere in UI | Research #2, #6, #8 | ALL |
| G2 | Every animation has prefers-reduced-motion branch | Research #1, #6 | ALL |
| G3 | One primary CTA per screen | Research #2, #4 | ALL |
| G4 | Empty states = one warm action, never a list | Research #1, ADHD Specialist | ALL |
| G5 | No streak display when value = 0 or 1 | Research #2, #3 | MindShift, VOLAURA |
| G6 | Achievement identity first, score as context | Research #10 | VOLAURA |
| G7 | Crystal/reward not shown in vulnerability window | Research #10 | MindShift, VOLAURA, Life Sim |
| G8 | No lock icons — locked = invisible | Research #10 | ALL |
| G9 | No leaderboards of any kind | Research #10, #5 | ALL |
| G10 | No comparison language ("you vs others") | Research #10, #2 | ALL |
| G11 | Errors = system issue framing, not user mistake | Research #2, #16 | ALL |
| G12 | Low energy = assessment hidden or "Ready?" gated | Research #2, #3 | VOLAURA, MindShift |
| G13 | Infinite animation loops banned on action screens | Research #1, #6 | ALL |
| G14 | Particle count ≤12 (celebrations) | Research #1 | ALL |
| G15 | Score counter: max 800ms, never 2s count-up | Research #10 | VOLAURA, MindShift |
| G16 | Data firewall: ADHD/health data never reaches B2B | Research #2, #9 | VOLAURA |
| G17 | Agent shared memory safety boundary — sanitize before writing to shared-context.md | Research #13 | ZEUS |
| G18 | Every assessment session start must include a one-sentence AI processing disclosure (non-dismissable, before first question) | ISO 10667-2, Research #15 | VOLAURA |
| G19 | Every AURA badge payload must include: `model_version`, `irt_parameters_version`, `theta_se`, `confidence_interval_95` | ISO 10667-2, Research #15 | VOLAURA |
| G20 | No score stored without complete `evaluation_log` (DeCE: concept + quote + confidence). Keyword-fallback scores tagged `evaluation_mode: degraded` — excluded from badge issuance | ISO 10667-2, Research #15 | VOLAURA |
| G21 | Vulnerability window = 5 minutes after session end. No crystals, XP numbers, or badge reveals during this window. Only reflection prompts, breathwork, PostSessionFlow | Research #10 | MindShift, VOLAURA |
| G22 | Org discovery results must show score freshness: "Leadership: 82 · Assessed 3 months ago · v2.1" — never raw number only | Research #15, Research #9 | VOLAURA |
| G23 | Comorbidity safety on all screens: font size user-adjustable, contrast between 4.5:1–12:1 (never >14:1), no all-caps text | Research #6, Research #2 | ALL |

---

## PART 7: IMPLEMENTATION ROADMAP

### ECOSYSTEM STATE (2026-04-06)

| Product | Status | Repo |
|---------|--------|------|
| VOLAURA web app | Active development | `C:\Projects\VOLAURA\apps\web\` |
| MindShift PWA | v1.0 production, Google Play pending | `C:\Users\user\Downloads\mindshift\` |
| ZEUS Gateway | Live on Railway, 39 agents, event-driven | `C:\Users\user\Downloads\claw3d-fork\server\` |
| claw3d 3D office | Phase 1 done, Phase 2 in progress | `C:\Users\user\Downloads\claw3d-fork\` |
| BrandedBy | Concept phase | — |

### Pre-Launch Blockers (ZEUS — P0)
1. **JWT auth in WebSocket handshake** — code in `memory/agent-findings/`, needs Railway deploy
2. **WEBHOOK_SECRET in Railway** — 3 secrets: WEBHOOK_SECRET_RAILWAY, _GITHUB, _SENTRY
3. **ANTHROPIC_API_KEY in Railway** — currently empty (Cerebras is primary but fallback needs key)

### Pre-Launch Blockers (VOLAURA — P0)
1. **MIRT assessment upgrade** (Research #15) — 8 independent → 1 multidimensional
2. **ASR routing** (Research #15) — Soniox for AZ, Deepgram for EN
3. **Achievement hide** (Research #10) — remove lock icons, make locked invisible
4. **Crystal vulnerability window fix** (Research #10) — move from NatureBuffer to Progress
5. **Purple error system** (Research #2, #6) — zero red, error = `#D4B4FF`
6. **ADHD checklist audit on every live screen** (all research) — 37 items
7. **Energy picker in onboarding** (Research #2) — gate assessments on low-energy

### Months 1-3 (with real user data)
1. Bayesian IRT calibration pipeline (Research #15, P0) — first 200 real assessments
2. Differential skill decay (Research #15, P1) — per half-life table
3. If-Then Implementation Intentions (Research #16) — pre-session behavioral rules
4. DIF monitoring setup (Research #15) — run Mantel-Haenszel when N>500
5. Memory consolidation daemons for ZEUS (Research #13) — 3 Python functions
6. Voice data privacy policy update (Research #7) — disclose Google/Apple routing
7. PostHog upgrade to Bayesian A/B (Research #7) — needed for <1000 user insights

### Months 4-6 (at scale)
1. ZEUS model routing matrix (Research #12) — replace all-haiku with specialist models
2. ZEUS dead weight tracking (Research #12) — tokens vs value per agent
3. Prosodic features in BARS scoring (Research #15, P1) — F0, intensity, articulation
4. CSS Container Queries (Research #7) — tablet readiness
5. Coordinator burnout score (Research #11) — MindShift feature in VOLAURA org dashboard
6. If-Then plans UI polish (Research #16) — post initial MVP
7. Privacy panel (Research #2) — granular data sharing toggles pre-org-search

---

## PART 8: CONFLICT RESOLUTION

When a product decision conflicts with this Constitution:

1. **Identify the conflict explicitly.** Name which Law or Guardrail is at stake.
2. **Check if the research supports an exception.** Does the underlying science allow a specific context where the rule doesn't apply?
3. **Default: Constitution wins.** The research is the authority.
4. **Exception process:** CEO reviews + documents in docs/DECISIONS.md with:
   - Which law conflicts
   - Scientific justification for exception
   - Time-limited scope (e.g., "A/B test for 30 days, then review")
5. **Update Constitution if evidence changes.** This document improves — it doesn't freeze.

### Known Legitimate Conflicts

| Research | Conflict | Resolution |
|----------|----------|-----------|
| R#3 (Traffic light = red) | Research suggests red for hard tasks | REJECTED — RSD is age-independent. Purple for hard tasks. |
| R#8 (Gen X prefers red errors) | Age-based recommendation conflicts with Law 1 | REJECTED — NEVER RED applies to all age groups. |
| R#3 (AI auto-hides dashboards) | Paternalistic feature | REJECTED — user controls visibility, not AI. Autonomy = SDT core. |
| R#5 (VR variable ratio XP) | Praised by market but conflicts with R#10 | RESOLVED — keep math, hide formula. Display identity not currency. |

---

## PART 9: METRICS FOR CONSTITUTION COMPLIANCE

These are measured monthly:

| Metric | Target | Source |
|--------|--------|--------|
| Red instances in production UI | 0 | Automated CSS audit |
| Screens with >1 primary CTA | 0 | Design review |
| Shame language instances | 0 | i18n string audit |
| Animations without reduced-motion | 0 | Automated a11y scan |
| ADHD checklist compliance rate | 100% | Pre-ship review |
| Lock icon instances | 0 | Visual QA |
| Post-session crystal visibility | 0 | Flow audit |
| User energy → assessment availability | Correct gating | Playwright E2E |

---

## REVISION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2026-04-06 | Initial document — synthesized from 17 CEO research documents (~140,000 words) |
| v1.1 | 2026-04-06 | Merged MindShift/ZEUS handoff: Node.js gateway architecture, 10-state Life Simulator model, provider hierarchy, P0 task list |
| v1.2 | 2026-04-06 | **3-agent audit, 34 findings.** Critical fixes: Life Simulator #ef4444→purple/orange (Law 1 self-contradiction), "Red day"→"Low" naming, vulnerability window defined (5 min), ZEUS two-swarm split documented honestly. New: 6 Guardrails (G18-G23), MIRT spec, B2B tier architecture, Crystal Law 6 amendment (badge not immediate), proactive shame contract, 90-min warning protocol, ASR Fairness Rule, two-swarm bridge spec, ZEUS product API requirement. |

**Next scheduled review:** 2026-07-06 (quarterly)
**Trigger for unscheduled review:** New research added to CEO corpus, or metric violation found.

---

*This document is the property of the VOLAURA ecosystem. It must be injected into every new agent context, every new chat session, and every design review. It is a living document but its 5 Foundation Laws and 7 Crystal Laws are permanent until CEO explicitly revises them with scientific backing.*
