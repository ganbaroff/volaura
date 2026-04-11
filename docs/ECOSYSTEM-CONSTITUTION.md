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

**Products:** MindShift (fully built), VOLAURA (fully built), Life Simulator (fully built), BrandedBy (fully built)

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

**AZ/CIS extension (cultural agent finding):** Law 3 was written from Western ADHD clinical psychology — shame of individual failure and personal inadequacy. AZ/CIS operates on collectivist shame (face/ar/həya — what will others think). The mechanics differ:
- **Individual shame:** hide the score, treat achievement as private reflection → wrong for AZ (scores only have value when shown to someone who matters)
- **Collective face:** showing a verified score is a legitimate honor claim, not boasting — IF the credentialing body is respected
- **Rule:** sharing mechanics must be framed as honor claims, not privacy decisions. "Show [org] what you've earned" is shame-free in AZ context; hiding sharing as a secondary feature is shame-free in Western ADHD context. Both must be satisfied simultaneously.

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

### CRYSTAL LAW 8: Never Launch Earn Without a Spend Path

A crystal earned with nowhere to go is a promise broken. Broken promises with ADHD users = lost trust permanently.

**Rule:**
- Do not activate crystal earning in any product until that product OR another active ecosystem product has a meaningful crystal spend mechanic.
- "Meaningful" = user can achieve something they value with crystals. Cosmetics, character upgrades, and feature unlocks all qualify. "Coming soon" does not.
- If the spend path does not yet exist: hold crystals in a transparent deferred queue with no expiry. Show the queue. Never hide it.

**Historical precedent for getting this right:** Roblox launched with both earn AND spend (game access, avatar items) simultaneously. Every currency that launched earn-first without spend died within 18 months (example: dozens of early social point systems).

**Products:** ALL (crystal economy is cross-ecosystem)

---

## PART 3: RESEARCH-BY-RESEARCH DESIGN RULES

### Research #1 — Gen Z Engagement (Octalysis + SDT + Fogg)

**Approved for adoption:**
- Sunk Cost Registration: deliver value BEFORE login (Quick Start, skill preview)
  **VOLAURA implementation (user journey agent finding — currently MISSING):** The VOLAURA landing has no zero-commitment entry point. Landing hero must include a "See a sample AURA profile" link (no login required) showing: a fictional profile, a communication score of 74, a Silver badge, the DeCE quote "Your responses showed active listening in 3 scenarios." This is the concrete VOLAURA equivalent of MindShift's Quick Start. Without it, a skeptical Gen Z user sees pure marketing copy and exits.
  **Fourth trust pill required:** Current pills are "No CV," "Data stays private," "No spam." For an assessment platform, the actual fear is judgment. Add: "Your score is only shared if you choose to." This directly addresses the vulnerability surge (78% abandonment from Research #1).
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
- Voice data privacy: ~~disclose routing to Google/Apple in privacy policy~~ **MOVED TO PRE-LAUNCH P0** (voice = biometric data under GDPR Art. 9 — Soniox/Deepgram DPAs must be verified before any voice processing begins)
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
- **Section 5.3 (legal agent finding):** pre-assessment disclosure must name: specific competencies being measured, how they map to organizational needs, and interpretive framework. One sentence (G18) is legally insufficient — a disclosure document spec is needed.
- **Formal Grievance Mechanism (legal agent finding):** ISO 10667-2 Section 7 requires a documented pathway for users to formally dispute their AURA score. This is a product requirement, not a UX consideration. Must exist before ISO 10667-2 compliance can be claimed in B2B Tier 3 marketing.
- **Peer Assessor Competence (Section 5.4):** VR multiplier assumes peers are qualified assessors (peer=1.25). The standard requires assessors to be qualified. Constitution must specify what qualifies a peer assessor — or reduce the peer multiplier with a note that full Section 5.4 compliance is Phase 2.

**Open Badges 3.0 — Technical Compliance (legal agent finding, pre-launch for B2B Tier 3):**
G19 adds custom extension fields to badge payloads. Open Badges 3.0 requires specific W3C Verifiable Credentials fields that are not yet in the spec:
- **VC Data Model:** badge must include `@context` (W3C VC + OB 3.0 contexts), `type: ["VerifiableCredential", "OpenBadgeCredential"]`, `issuer` as verified Profile object with stable HTTPS identifier.
- **Cryptographic proof:** badges must be cryptographically signed. VOLAURA needs an issuer DID or public/private key infrastructure for badge signing. This is an architecture decision that must be made before B2B Tier 3 is marketed.
- **Achievement objects:** each badge tier must have a machine-readable `Achievement` object with `achievementType`, `criteria`, `description`.
- **Revocation endpoint (credentialStatus):** when AURA score decays and badge tier drops, the old badge must be revoked via a `credentialStatus` endpoint. The decay half-life mechanism (Research #15) must be connected to this revocation event.
- **Recipient privacy:** use hashed recipient identification — do not embed raw user identifiers in badge payloads.
- **Issuer decision (pre-launch):** decide whether VOLAURA operates as a VC issuer with its own DID, or uses a third-party badge platform. Must be decided before any badge is issued to B2B organizations.

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

### Research: Legal & Compliance Framework

**Source:** GDPR, EU AI Act (Annex III), ISO 10667-2, COPPA, Azerbaijan PDPA, Azerbaijan Labor Code, Open Badges 3.0 (W3C VC)
**Added in v1.3 — swarm audit finding (P0): legal layer was completely absent**
**Updated in v1.4 — legal agent audit, 9 findings. Several moved to pre-launch P0.**

#### GDPR (applies to all EU users — and Azerbaijan users once VOLAURA enters EU market)

**Article 5 — Data Minimization:**
- Collect ONLY what assessment requires. No ambient behavioral tracking without consent.
- Assessment audio: process, then delete within 48h unless user explicitly opts in to retention.

**Article 13 — Transparency (mandatory at onboarding):**
- Before any data is collected, user must see: what data is collected, why, how long retained, who has access.
- This is not optional marketing copy — it is a legal requirement. Onboarding Screen 1 must include it (non-dismissable).
- Already partially covered by G18 (AI processing disclosure). G18 must also cover data categories and retention.

**Article 22 — Automated Employment Decision-Making (P0 pre-launch — legal agent finding):**
VOLAURA is an Article 22 trigger. When an org searches by AURA score and shortlists/filters candidates, that is automated processing with an employment consequence. The constitution explicitly names this use case ("helped 2 organizations shortlist you"). This is textbook Article 22.
- **Explicit consent required (Art. 22(2)(c)):** before any user profile becomes discoverable to employers, they must give explicit, informed consent that organizations may use their AURA score as an automated pre-screening signal. This is separate from general ToS acceptance.
- **Human Review Request mechanism required:** any user who believes they were rejected based on an automated AURA search must have a documented pathway to request human review.
- **B2B transparency:** VOLAURA's ToS must disclose that employer search constitutes automated profiling for employment purposes under Article 22.
- **Legal basis declaration:** explicit consent (22(2)(c)) is the viable basis. Contract necessity and Union law bases do not clearly apply to a voluntary platform.

**Article 9 — Special Category Health Data (P0 pre-launch — legal agent finding):**
Energy state (EnergyPicker 1-5), burnout indicators (Research #3/#11), and hyperfocus pattern detection (MindShift rule 14) constitute "data concerning health" under GDPR Article 9 + Recital 35. This is a higher legal standard than standard personal data.
- **Current G16 is insufficient:** it addresses secondary disclosure (data not reaching B2B) but not primary collection basis.
- **Explicit consent under Art. 9(2)(a) required:** must be specific to health data, separately from general ToS, freely withdrawable.
- **Separate data store:** health data must be in a logically separate table with separate RLS policy and an explicit deletion pathway faster than general account deletion (72-hour response target vs. 30-day general).
- **Same obligation applies under AZ PDPA Article 8** (sensitive data), which has parallel requirements.

**Article 17 — Right to Erasure:**
- 30-day processing window for deletion requests.
- Anonymized aggregate statistics (ecosystem-level AURA distributions) may be retained.
- Individual assessment logs, audio, AURA score, badge metadata — fully erased on request.
- Erasure must cascade across all 5 products that share auth.

**Article 20 — Data Portability:**
- AURA score + full badge history + assessment summaries: exportable as PDF and JSON on demand.
- Response time: 30 days. Format must be machine-readable (JSON) not just human-readable.

#### EU AI Act — VOLAURA is a High-Risk AI System

VOLAURA's assessment pipeline qualifies under **Annex III, Category 4** ("AI systems used in employment, workers management and access to self-employment") — specifically: AI-assisted evaluation of competency for professional purposes.

**Obligations:**
1. **Conformity assessment**: document training data sources, evaluation methodology, and IRT parameters.
2. **Human oversight**: explicitly stated at onboarding ("Your AURA score is assessed by AI and reviewed by our methodology team. Scores are not used as sole employment criteria.").
3. **Transparency to individuals**: assessed persons must be able to request explanation of their score (already covered by DeCE `/aura/me/explanation` endpoint — this is legally required, not just a nice-to-have).
4. **Non-discrimination monitoring**: DIF test (Mantel-Haenszel) when N>500 per demographic group is a legal requirement, not just good practice.
5. **Registration**: When VOLAURA enters EU market — register in EU AI Act database before deployment.

#### Azerbaijan PDPA — Primary Market (P0 pre-launch — legal agent finding)

The AZ Law on Personal Data (amended 2022, GDPR-aligned but distinct) applies now — AZ is VOLAURA's primary market.

**Data Localization (PDPA Article 15):**
- Personal data of AZ citizens may require storage within Azerbaijan or notification to SADPP (State Agency for Personal Data Protection) for cross-border transfers.
- Current hosting: Supabase (US), Railway (US), Vercel (US). All three require cross-border transfer assessment before AZ user data is processed.
- **Pre-launch blocker:** Commission a data transfer impact assessment. Either establish AZ-region hosting or file cross-border transfer notification with SADPP.

**SADPP Registration:**
- Unlike GDPR (which abolished registration), AZ PDPA requires operators to register with SADPP before commencing data processing.
- **Pre-launch blocker:** VOLAURA must register with SADPP before onboarding AZ users.

**Consent Language:**
- AZ PDPA requires consent in Azerbaijani (or verifiable electronic equivalent). Translations are not sufficient — legally reviewed consent text in Azerbaijani is required.
- Consent must be separately obtained for each processing purpose.

**Responsible Person:**
- AZ PDPA requires designation of a responsible person for personal data within the organization.
- **Action:** Designate CEO or legal representative as responsible person. Document this in organization records.

**Voice Data — Biometric + Cross-Border (P0 pre-launch, moved from Months 1-3):**
- Assessment voice recordings are biometric data under GDPR Article 9(1) and AZ PDPA Article 8. This is a higher legal class than personal data.
- Soniox (AZ ASR) and Deepgram (EN ASR) are US-based. Their DPA (Data Processing Agreement) compliance with GDPR and AZ PDPA must be verified before launch — not after.
- **Pre-launch blocker:** Obtain and review Soniox and Deepgram DPAs. If adequate protection not confirmed → do not process voice in the EU/AZ markets.
- Voice data routing disclosure (previously in Research #7 as Months 1-3) is moved to **pre-launch P0**.

#### Age Protection

- **EU (GDPR Article 8):** 16+ required for AI-processed personal data. Under 16 = parental consent required.
- **Global minimum:** 13+ (COPPA equivalent). VOLAURA is a professional platform — soft-enforce 16+ globally, hard-enforce via age confirmation at signup.
- **Technical enforcement:** checkbox at signup is insufficient. Date of birth field required. Server-side gate: block assessment access if `age_at_signup < 16`.
- **If minor detected:** redirect to parent-consent flow or waitlist. Never silent drop.

#### Data Retention Schedule (authoritative)

| Data Type | Retention | Basis |
|-----------|-----------|-------|
| Assessment audio | 48h after processing, then delete | Data minimization |
| Assessment responses + scores | 3 years | ISO 10667-2 audit trail |
| AURA score + badge history | Until deletion request | User-controlled |
| User profile (name, email, org) | Until deletion request | User-controlled |
| Analytics events (PostHog) | 90 days raw → anonymized indefinitely | Research validity |
| Agent conversation logs (ZEUS) | 30 days rolling | Security audit |
| Episodic swarm memory | 6h → consolidated; raw pruned | Research #13 |

#### Azerbaijan Labor Law Context

**Azerbaijan Labor Code, Articles 17-19:** prohibit discriminatory employment decisions based on personal characteristics not directly relevant to job performance.

**VOLAURA's legal position:** AURA score is a verified professional signal, not a discriminatory classifier. Must be explicitly framed everywhere:
- Onboarding for org users (B2B): "AURA is one verified input. It does not replace interviews, references, or HR judgment."
- Discovery results for orgs: score shown with "one of many signals" framing.
- VOLAURA cannot guarantee and should not imply that high AURA = employment eligibility.

---

### Research: Cultural Localization (Azerbaijan & CIS)

**Source:** AZ cultural research, CIS market analysis, language consulting
**Added in v1.3 — swarm audit finding (P1): AZ/CIS market rules were absent**

#### Trust Patterns (AZ/CIS)

AZ/CIS users form trust decisions after the **3rd interaction**, not the 1st. Western "cold form" UX (show a form, ask for data immediately) will fail in this market.

**Rule: Deliver visible value BEFORE requesting profile data.**

| Step | What to show | What NOT to ask |
|------|-------------|-----------------|
| 1st screen | Quick skill preview / sample insight / peer result | Name, job, email |
| 2nd interaction | Personalized takeaway from partial input | GDPR consent, LinkedIn import |
| 3rd interaction | Show value derived from their specific context | Full profile form |

Trust signals that work in AZ context (validated by local market):
- "Heç bir CV lazım deyil" — "No CV required" (cultural resonance: CVs are often falsified in AZ market)
- "Heç bir əlaqə lazım deyil" — "No connections/wasita required" (wasita = influence through connections; this is THE key trust barrier in AZ professional market)
- University/institution references: ADA University, Baku State University, AzPetroChemical partnerships signal legitimacy
- Phone number verification > email verification (mobile-first trust signal in AZ)

#### Shame-Free Language — AZ-Specific Additions

Azerbaijani culture has **higher professional shame sensitivity** than EU average. Standard shame-free rules (Law 3) must be amplified:

**Banned AZ copy (expand Law 3's banned list):**
| Banned (AZ) | Translation | Replace with |
|-------------|-------------|--------------|
| "nöqsan" | deficiency/flaw | Remove entirely |
| "səhv" | mistake/error | "başqa perspektiv" (different perspective) |
| "cəza" | penalty | Remove entirely |
| "uğursuz" | failed/unsuccessful | Remove entirely |
| "rədd" | rejection | Remove entirely |
| "Sənin xətan" | Your fault | Never appear |

**Professional failure is NEVER shown publicly.** An AURA score below a threshold is NOT surfaced in org discovery, NOT shown on public profile, NOT communicated to any third party. The user owns their score data entirely.

#### Language Rules (AZ)

- **Formal "you" ("Siz") is mandatory** in all professional AZ copy. Never "Sən" (informal). Violation = immediate trust loss. Applies to: all UI strings, error messages, push notifications, AI-generated explanations, email copy.
- **AZ copy length:** Azerbaijani text runs 25-40% longer than EN equivalent. All UI components must accommodate this (no truncation allowed in achievement names, assessment titles, error messages).
- **Button text max 22 characters in AZ** (cultural agent finding) — "Begin Assessment" = 16 EN chars; "Qiymətləndirməyə başla" = 21 AZ chars. Design all button containers to handle 22-char AZ labels. The ADHD checklist "≤5 tappable elements" rule applies to rendered width, not EN character count.
- **Special characters (mandatory UTF-8):** ə ğ ı ö ü ş ç — use correct Azerbaijani characters, not Latin substitutes (e.g., "əla" not "ela", "şirkət" not "sirket"). Substitution = perceived as disrespectful/foreign.
- **Date format (UI):** DD.MM.YYYY in compact contexts. **Date format (certificates/badges):** `DD [month_name_AZ] YYYY-cı/ci/cu/cü il` with correct vowel harmony suffix — "06 aprel 2026-cı il." The `-cı/-ci/-cu/-cü` suffix is mandatory; omitting it reads as grammatically incorrect to native speakers and signals a foreign/automated origin.
- **Number format (AZ locale):** use comma as decimal separator — score displays must show "78,4" not "78.4" in AZ locale. AURA scores, percentages, and all numeric displays subject to this.
- **"Xahiş" (please) overuse:** excessive use = perceived as weak. Use direct but warm register.
- **Russian as first-class language** (cultural agent finding): a significant AZ professional segment — particularly those educated before 1991 or working in Russian-language business contexts — prefers Russian. Russian is NOT a fallback; it is a primary locale. Language selector must be accessible at signup (not buried in settings) and must offer AZ, RU, and EN as equal options.

#### ADHD Language Ban in AZ/CIS Copy (P0 — cultural agent finding)

**Never use "ADHD," "neurodivergent," "cognitive load," or clinical psychology framing in any AZ-facing or CIS-facing user or B2B copy.** This is a P0 pre-launch requirement.

- In Azerbaijan, ADHD is underdiagnosed (2-4x lower than Western Europe), clinically stigmatized, and associated with childhood behavioral problems rather than adult professional identity. "Designed for ADHD brains" reads as "designed for people with a problem" to the AZ professional audience.
- The ADHD design principles (all 5 Laws, the 37-item checklist, the energy adaptation system) are the RIGHT UX science — apply them silently.
- **B2B framing:** translate checklist benefits to business metrics only. "Reduces assessment abandonment by 40%, increases completion quality" — never "ADHD-optimized."
- **User-facing framing:** "Designed to respect your time and energy. No pressure, no judgment, just your actual skills." Productivity/efficiency framing, NOT clinical accommodation.
- **Energy adaptation system:** present as "Focus Mode" or "Adaptive Assessment" — a precision tool for any user, not an accommodation for a condition.
- This rule does NOT mean hiding the design principles from internal documents, the Constitution, or English-language markets where ADHD self-identification is a positive professional identity. It applies specifically to AZ/CIS-facing copy.

#### AZ/CIS Trust Architecture (cultural agent finding)

AZ is a high-context, relationship-trust culture. The default assumption about an unknown platform is suspicion. Trust flows through chains: known org endorsement → network presence → then individual experience.

**Three mandatory trust signals before any data collection:**
1. **Visible AZ org logos** — show 3-5 recognizable Azerbaijani organizations on landing page before trust pill strip. Logo-based, not text testimonials.
2. **Referral-first onboarding** — "Invited by [Person's Name]?" as default opening option for new users. Arriving via trusted person's invitation immediately elevates platform credibility.
3. **Employer visibility guarantee** on assessment START screen (not privacy policy): "Your employer cannot see your scores unless you share them." One prominent sentence, not buried in settings.

**AI processing disclosure reframe for AZ:** The G18/G24 disclosures currently read as legal checkboxes. For AZ context: "Who evaluates you: an independent AI system, not a person you know." This removes the fear of personal bias — which is a live concern in relationship-heavy professional culture where scoring by known people carries favoritism risk.

#### AZ/CIS Social Proof Without Leaderboards (cultural agent finding)

G9 (no leaderboards) is correct for ADHD/psychological safety. But it leaves a gap: AZ professional culture requires visible community proof of real users before individuals trust the platform.

**Replacement mechanics (no names, no rankings, still ADHD-safe):**
- **Community Signal widget** (VOLAURA Rule 25): aggregate anonymized stats by city/sector — "843 Baku professionals assessed · 62 in Finance." No names, no ranks, but visible platform presence proof. Must exist before AZ launch.
- **Org Hall page**: publicly visible page showing which organizations have used VOLAURA for talent assessment. Org logos only, no user data, no scores. Stat: "X assessments conducted with [Org]." Serves as B2B social proof for other organizations considering adoption.
- **Opt-in named testimonials** for early B2B customers — allow them to be publicly credited. AZ decision-makers trust "This is what Nigar from Kapital Bank said" over any AI-generated copy. Named testimonials (with explicit consent) are a first-class trust asset, not a privacy risk.
- **Honor mechanism for sharing:** the "Share with organization" button should be prominently placed and framed as an honor claim — "Show [org name] what you've earned" — not as a privacy decision. In face-culture AZ, sharing credentials publicly is a legitimate status action when the credentialing body is respected.

#### AZ/CIS Accessibility Specifics

- **Right-to-left support:** NOT required (Azerbaijani is Latin-script since 1991) but **Cyrillic rendering** must work for CIS users who switch between locales.
- **Mobile-first is mandatory**, not optional: AZ internet usage is 78% mobile. Desktop secondary.
- **Low-bandwidth mode:** Baku connection quality varies significantly outside city center. Core flows must work on 3G.

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
17. B2B Liability Allocation (legal agent finding — must be in all B2B contracts):
    - VOLAURA = "information service provider" (analogous to psychometric test publishers). Organizations = "decision-makers."
    - **Mandatory Appropriate Use Policy at B2B onboarding:** organizations must agree that AURA scores are one input among several and MAY NOT be used as the sole basis for rejection.
    - **GDPR Art. 22 org obligations:** organizations using AURA scores for automated employment pre-screening are themselves data controllers for that processing. B2B contract must define this responsibility split.
    - **DIF monitoring as B2B obligation:** if VOLAURA detects that its scoring systematically underscores a protected group (disability, gender, ethnicity) that results in discriminatory hiring patterns, VOLAURA bears contributory liability. DIF audit (Mantel-Haenszel) is moved from Months 1-3 to **pre-launch P0** — not because of psychometric quality alone, but because of labor law exposure.
    - If ADHD-adaptive design fails to prevent ADHD-related score depression → a candidate with ADHD who is rejected on AURA score basis has an Article 16 AZ Labor Code claim against the using organization AND a GDPR Art. 22 claim against VOLAURA.
17. DeCE "Show Your Work" endpoint (`/aura/me/explanation`) is a primary B2B differentiator — must be surfaced in org volunteer profiles as a 2-sentence competency evidence summary.
21. **Moment of Truth Rule (competitive agent finding):** The DeCE 2-sentence behavioral evidence summary is the ONLY product feature that makes "verified, not claimed" viscerally true to a B2B buyer in 30 seconds.
24. **Credential Display Split (cultural agent finding):** The SAME score is displayed differently depending on the viewer context:
    - **Public profile (what orgs and others see):** score number FIRST ("78.4 Communication"), then tier name ("Gold-level"). Orgs need a credible number to anchor trust — descriptive titles alone sound self-assigned in AZ professional culture.
    - **Private dashboard (what the user sees):** identity title FIRST ("Gold-level Communicator"), score as subtitle ("AURA 78.4"). This is the Crystal Law 4 / overjustification principle for internal motivation.
    - **Credential sharing card / PDF export:** include institutional authority marker — "Gold-level Communicator · Assessed by VOLAURA · [Date AZ format]". The platform name acts as the credentialing institution. This is what makes it shareable without feeling self-promotional.
25. **Community Signal (cultural agent finding):** A city/sector aggregate widget must exist before AZ launch. Shows: "843 Baku professionals assessed · 62 in Finance." No names, no individual scores, no rankings. Purely aggregate social legitimacy signal. ADHD-safe (no comparison) but fills the trust vacuum that G9's no-leaderboard rule creates.
26. **AZ B2B Demo-First (cultural agent finding):** In AZ/CIS markets, the B2B sale begins with a human conversation, not a product trial. The platform must have a "Request a Demo" flow that routes to a personal meeting. Do NOT attempt self-serve freemium conversion for AZ enterprise accounts. The DeCE explanation should be positioned as: "If a candidate asks why they weren't selected, you can show them the specific skill evidence — documented, dated, AI-assessed." This is a risk management argument for AZ HR managers, not an algorithm detail.
27. **Org Hall page (cultural agent finding):** A publicly visible page showing which organizations have conducted VOLAURA assessments. Org logos only, no user data, "X assessments conducted." Primary B2B social proof mechanism for AZ market where reference selling dominates. It must appear in the **same view** as the AURA score in org discovery — not behind a click, not on a separate page. Every B2B feature that ships should either (a) funnel toward this evidence moment or (b) have a documented reason why it doesn't. If the evidence summary is not showing for a candidate, their profile must visually communicate this absence (not silently omit it).
22. **Org Outcome Flywheel:** When an org engages or hires a VOLAURA user (tracked with explicit user consent via a post-event feedback prompt), the outcome is fed back into AURA score validity calibration. This is the most defensible long-term network effect in the platform. Must be an explicit product requirement tracked as a metric, not a future feature. Even a simple "Did [Name] perform as expected at [Event]? 1-5" rating from org coordinator, stored in `character_events`, makes scores more accurate over time.
23. **Crystal Economy Launch Sequencing:** Crystals must not launch without at least one active spend path. If fewer than 2 products are shipping crystal spends simultaneously: (a) communicate transparently to users that spend features are coming, (b) hold crystals in a deferred queue with no expiry, (c) provide at least one temporary local spend mechanic within the active product. Never create a "earn crystals with no place to spend them" state — it is a trust break, not a deferred reward.
18. ASR Fairness Rule: language-detected routing (langdetect on first 3s or profile locale as prior). Scores under Whisper before routing ships are flagged and queued for re-evaluation.
19. Onboarding Screen 1 must include AI processing disclosure (ISO 10667-2 G18) — one sentence, non-dismissable.
20. Ghosting Grace for professionals: 30 min before event start with no check-in → single warm Telegram/push ("Ready to check in? Tap here"). Auto-ping next-ranked backup volunteer if cancellation within 2 hours of start.
28. **Pre-Assessment Commitment Layer** (user journey agent finding — consolidates 3 unimplemented P0 rules):
    Before the FIRST QUESTION in any VOLAURA assessment, a single non-dismissable screen must show ALL of:
    - (1) One-sentence AI disclosure: "Your answers will be evaluated by an AI system." (G18 / ISO 10667-2) — currently missing from assessment start page
    - (2) Scenario framing choice: 3 options (ecology / sports / social) — SDT Autonomy lever per VOLAURA rule 12 — currently missing
    - (3) Energy check with gentle exit: "How are you feeling today? (1-5)" with "Not ready? Save this for later →" option (Law 2) — currently missing
    This screen is NOT the assessment start page (that shows competency selection). This is the screen between "Start assessment" click and question 1.
29. **Vulnerability Window Positive Specification** (user journey agent finding — G21 prohibits but never specifies what IS shown):
    G21 defines the 5-minute post-assessment vulnerability window. This rule specifies the CONTENT of that window. During the window, the complete screen MUST show:
    - (1) DeCE behavioral evidence: "Your [competency] reflects [specific behavioral evidence from DeCE quote]" — the identity statement, not the number
    - (2) One-sentence competency reflection: e.g., "Your communication reflects consistent active listening across 4 responses"
    - (3) Single CTA: "See your full AURA →" (navigates to AURA page on next interaction after window expires, OR after user explicitly taps)
    - NOTHING ELSE during the window: no score number prominently displayed, no badge icon, no crystal count, no progress bar toward next tier
    Badge tier and crystal earnings are shown on the AURA page at the user's NEXT visit (Crystal Law 6 Amendment), not the complete screen.
30. **Ghosting Grace for Pre-Activation Users** (user journey agent finding):
    Any user who signed up and visited the dashboard but never completed a first assessment receives a warm re-entry card on their next dashboard visit (triggers after 48h of inactivity):
    - Copy: "Still thinking about it? Start when you're ready — there's no deadline." (NOT "You haven't completed your first assessment")
    - Single CTA: "Start when ready →"
    - Replaces the standard NewUserWelcomeCard content for these users
    - Never shows count of days absent, never shows what's "missing"
    - Governed by Law 3 (no guilt) and G4 (one warm action)

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
| G24 | GDPR Article 13 onboarding notice: before ANY data is collected, user sees (non-dismissable): what data, why, how long retained, who has access. Must cover AI processing (expands G18) | GDPR Art. 13, EU AI Act | VOLAURA, MindShift, BrandedBy |
| G25 | EU AI Act conformity statement at onboarding: "Your AURA score is assessed by AI and reviewed by our methodology team. Scores are not used as sole employment criteria." One sentence, non-dismissable, before first assessment question | EU AI Act Annex III | VOLAURA |
| G26 | Age gate: EU users 16+, global minimum 13+. Server-side enforcement — date of birth field required. Checkbox alone is insufficient. Block assessment access if age < 16 | GDPR Art. 8, COPPA | VOLAURA, MindShift |
| G27 | AZ/CIS trust timing: deliver visible value (skill preview, sample insight) BEFORE requesting profile data. Never cold-form-first in AZ/CIS locale | AZ cultural research | VOLAURA, MindShift |
| G28 | AZ shame-free copy: "nöqsan", "səhv", "cəza", "uğursuz", "rədd" banned in all AZ locale strings. Professional failure never shown publicly or to employers. All AZ copy uses formal "Siz" form | AZ cultural research, Law 3 | VOLAURA, BrandedBy |
| G29 | WCAG 2.1 AA minimum (2.2 target) across all 5 products. Automated a11y scan (axe-core or equivalent) on every CI run | Research #6, legal compliance | ALL |
| G30 | Offline mode declaration: MindShift core features (timer, task list) work offline with sync-on-reconnect. VOLAURA assessments require connection — clear offline message shown, not silent failure | Research #7 | MindShift, VOLAURA |
| G31 | Data portability: AURA score + full badge history + assessment summaries exportable as PDF and JSON on demand, within 30 days of request | GDPR Art. 20 | VOLAURA |
| G32 | Purple ambiguity rule: changing error color to purple (Law 1) does NOT reduce copy urgency. Purple errors MUST use copy that communicates action needed. "Something didn't connect — tap to retry" not just a purple icon. Color removes shame trigger; copy still communicates the required action | Swarm audit finding (dsp-474aa609) | ALL |
| G33 | GDPR Art. 22 explicit consent: before profile becomes org-discoverable, user must give explicit informed consent that orgs may use AURA as automated pre-screening signal. Separate from ToS. Must include: right to human review, right to contest, right to opt out of employer discovery | GDPR Art. 22(2)(c) | VOLAURA |
| G34 | GDPR Art. 9 health data consent: energy state, burnout indicators, and inferred attention patterns require explicit Art. 9(2)(a) consent — separate from general consent. Must be specific to health data, freely withdrawable. Stored in separate table with faster deletion pathway (72h vs 30d) | GDPR Art. 9, AZ PDPA Art. 8 | MindShift, VOLAURA |
| G35 | Formal AURA score grievance mechanism: users must have a documented pathway to formally dispute their AURA score result. This is an ISO 10667-2 Section 7 legal obligation, not a UX feature. Must exist before Tier 3 "ISO 10667-2 compliant" is marketed to B2B customers | ISO 10667-2 Section 7 | VOLAURA |
| G36 | AZ PDPA pre-launch: SADPP registration and cross-border transfer assessment (for Supabase/Railway/Vercel US hosting) must be completed before AZ users' data is processed. AZ-language legally reviewed consent text required | AZ PDPA Art. 15 | VOLAURA, MindShift |
| G37 | Open Badges 3.0 VC compliance before B2B Tier 3: badges must include W3C VC data model fields, cryptographic proof (issuer DID or equivalent), machine-readable Achievement objects, and a credentialStatus revocation endpoint connected to the AURA decay mechanism | Open Badges 3.0, W3C VC | VOLAURA |
| G38 | Moment of Truth placement: DeCE 2-sentence behavioral evidence summary must appear in the SAME VIEW as the AURA score in org discovery — not behind a click, not on a separate page. This is the primary B2B differentiator. If evidence is missing for a candidate, the UI must show "Evidence pending" rather than silently omitting | Competitive agent finding | VOLAURA |
| G39 | Org outcome feedback loop: when an org rates a VOLAURA user's performance post-event (explicit opt-in), the outcome is stored in character_events and fed into AURA validity calibration. This is a product requirement, not a future feature. Simple 1-5 rating from org coordinator is sufficient. | Competitive agent finding | VOLAURA |
| G40 | ADHD clinical language ban in AZ/CIS copy: never use "ADHD," "neurodivergent," "cognitive load," or clinical psychology framing in any AZ/CIS-facing user or B2B copy. The ADHD design principles are applied silently. B2B framing = business metrics ("40% lower abandonment"). User framing = "Focus Mode," "designed to respect your energy" | Cultural agent finding | VOLAURA, MindShift (AZ/CIS markets) |
| G41 | Russian as first-class locale: language selector accessible at signup with AZ, RU, EN as equal options. Russian is not a fallback. Significant AZ professional segment is Russian-preferring — particularly educated pre-1991 or working in Russian-language B2B contexts | Cultural agent finding | VOLAURA, MindShift |
| G42 | AZ B2B requires human-first sales: "Request Demo" flow must route to human meeting before any automated onboarding. No self-serve freemium conversion attempts for AZ/CIS enterprise accounts | Cultural agent finding | VOLAURA (B2B) |
| G43 | Credential display split: public profile shows score number first (credibility for viewer), private dashboard shows identity title first (motivation for holder). Shareable card includes institutional marker: "[Tier] · Assessed by VOLAURA · [Date]" | Cultural agent finding | VOLAURA |
| G44 | Community Signal widget: must exist before AZ launch. Shows aggregated anonymized stats by city/sector ("843 Baku professionals assessed · 62 in Finance"). No names, no rankings. Fills trust vacuum from G9 no-leaderboard rule without triggering social comparison | Cultural agent finding | VOLAURA |
| G45 | Pre-Assessment Commitment Layer required (VOLAURA rule 28): before question 1, user must see AI disclosure + scenario framing choice + energy check with exit option. These are currently unimplemented P0 requirements. No assessment may begin without this screen. | User journey agent finding | VOLAURA |
| G46 | Leaderboard pages are prohibited in production. Any `/leaderboard` route must be deleted or permanently redirected before launch. Leaderboard page currently exists in codebase (`/app/[locale]/(dashboard)/leaderboard/page.tsx`) — this is an active G9 violation. | User journey agent finding, G9 | VOLAURA |

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
8. **GDPR Art. 22 consent mechanism** (G33) — explicit consent before profile becomes org-discoverable
9. **GDPR Art. 9 health data consent** (G34) — separate consent + separate DB table for energy/burnout data
10. **Formal AURA score grievance mechanism** (G35) — required before ISO 10667-2 Tier 3 can be marketed
11. **AZ PDPA SADPP registration + DPA assessment** (G36) — required before AZ users' data is processed
12. **Soniox/Deepgram DPA verification** — voice = biometric; DPAs must be verified before voice assessments begin
13. **DIF bias audit** (Research #15) — Mantel-Haenszel bias test required BEFORE launch, not post-launch (labor law exposure)
14. **Leaderboard page removal** (G9, G46) — `/app/[locale]/(dashboard)/leaderboard/page.tsx` exists in production and violates G9 + Crystal Law 5. Must be deleted/redirected before launch.
15. **Assessment complete page: defer badge + crystals** (Crystal Law 6 Amendment, G21) — current code shows `badge_tier` and `crystals_earned` immediately post-assessment. Must be deferred to next AURA page visit (vulnerability window rule).
16. **AURA page score counter: 2000ms → 800ms** (G15) — `aura/page.tsx` uses `duration=2000` in `useAnimatedCounter`. G15 limit is 800ms max.
17. **text-destructive CSS class audit** (Law 1) — signup page uses `text-destructive` which may resolve to red via shadcn defaults. Must verify resolves to `#D4B4FF` (purple) before launch.
18. **Pre-Assessment Commitment Layer** (VOLAURA rules 28 + G45) — currently no screen exists between "Start assessment" click and question 1. Must be built.
19. **Landing: sample AURA profile** (Research #1 Sunk Cost Registration) — no zero-commitment entry point on landing. Must add "See a sample AURA profile" link before launch.

### Months 1-3 (with real user data)
1. Bayesian IRT calibration pipeline (Research #15, P0) — first 200 real assessments
2. Differential skill decay (Research #15, P1) — per half-life table
3. If-Then Implementation Intentions (Research #16) — pre-session behavioral rules
4. ~~DIF monitoring setup~~ → **moved to pre-launch P0** (see blockers #13 above)
5. Memory consolidation daemons for ZEUS (Research #13) — 3 Python functions
6. ~~Voice data privacy policy update~~ → **moved to pre-launch P0** (see blockers #12 above)
7. PostHog upgrade to Bayesian A/B (Research #7) — needed for <1000 user insights
8. Open Badges 3.0 VC technical compliance — issuer DID + cryptographic proof + Achievement objects + revocation endpoint (required before B2B Tier 3 launch)

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
| Swarm dsp-474aa609 (purple ambiguity) | "Absolute red prohibition creates ambiguity — users may not recognize purple as danger signal" | RESOLVED via G32 — purple color change is visual. Copy must still communicate action urgency. Both layers required. |
| Legal compliance vs. data minimization | GDPR right to erasure vs. ISO 10667-2 3-year audit trail requirement | RESOLVED — anonymize after 3 years. Individual PII erased; aggregate scoring distribution retained for audit validity. |
| Credly + LinkedIn integration (competitive agent finding) | Credly has 50M+ badge earners + LinkedIn native integration. VOLAURA is building toward the same position. Risk: AZ/CIS orgs adopt Credly because of LinkedIn reach before VOLAURA achieves critical mass. | RESPONSE: Credly has no IRT-based adaptive assessment, no ADHD design, no AZ/CIS market presence, no behavioral evidence quotes. The DeCE evidence summary (G38) is the response. Credly verifies that a badge was issued; VOLAURA explains WHY the score is what it is. If AZ/CIS market is secured before Credly localizes, the moat is the local calibration data and org relationships, not the badge format. Open Badges 3.0 compliance (G37) enables coexistence — VOLAURA badges can be imported INTO LinkedIn. This is the correct strategic response: complement, not compete with, LinkedIn's infrastructure. |
| LinkedIn Skills Assessments at 60M+ scale | LinkedIn's data volume means they have item difficulty estimates at a scale VOLAURA won't reach in 2-3 years. Static MCQ, not adaptive — but volume partially compensates. | ACKNOWLEDGED — the moat is the quality of the evidence, not the volume of data points. LinkedIn assessments produce a binary pass/fail. VOLAURA produces a dimensional score with behavioral evidence and decay-aware freshness. These are not the same product. Do not compete on scale; compete on evidence quality. |

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
| v1.3 | 2026-04-06 | **Python swarm audit, 14 models (Gemini/Groq/DeepSeek), 2 rounds.** Added: Legal & Compliance Framework (GDPR Art.13/17/20, EU AI Act Annex III high-risk classification, Age gate 16+/13+, Data Retention Schedule, AZ Labor Code framing). Added: Cultural Localization (AZ/CIS trust timing, wasita framing, shame-free AZ copy, Siz-form mandate, 25-40% text length budget). New Guardrails G24-G32 (legal, trust, WCAG, offline, portability, purple ambiguity rule). Conflict resolution: purple ambiguity resolved via G32 (copy layer required alongside color change). Memory logger Windows bug fixed (colon in model IDs). |
| v1.4 | 2026-04-06 | **Legal agent deep-audit, 9 findings.** Critical additions: GDPR Art. 22 automated employment decision-making (explicit consent + human review — G33), GDPR Art. 9 health data for energy/burnout tracking (G34), AZ PDPA SADPP registration + cross-border transfer assessment for US hosting (G36), Open Badges 3.0 VC technical compliance spec (cryptographic proof, issuer DID, revocation endpoint connected to decay — G37), formal AURA score grievance mechanism (ISO 10667-2 Section 7 — G35), labor law liability allocation (B2B contracts must name org as decision-maker). **Pre-launch P0 reclassification:** DIF bias audit moved from Months 1-3 (labor law exposure), voice data DPA verification moved from Months 1-3 (biometric = GDPR Art. 9). Total guardrails: G1-G37. |
| v1.5 | 2026-04-06 | **Competitive intelligence agent, 7 findings.** New Crystal Law 8: Never Launch Earn Without Spend Path (historical precedent from Roblox/Yahoo Answers failure modes). VOLAURA Rules 21-23: Moment of Truth (DeCE evidence in same view as score — G38), Org Outcome Flywheel (performance ratings → IRT validity — G39), Crystal Economy Launch Sequencing. Conflict resolution: Credly + LinkedIn response (complement, not compete; DeCE evidence = the differentiator), LinkedIn scale asymmetry acknowledged. GTM gaps noted (ICP, pricing, chicken-and-egg) — flagged as CEO strategic decisions, not constitution rules. Total guardrails: G1-G39. |
| v1.7 | 2026-04-06 | **First user journey agent, 20 findings. Actual code read.** Critical code violations found: leaderboard page exists (G9/G46 violation — must delete), badge+crystals shown immediately post-assessment (Crystal Law 6 Amendment + G21 violation), 2000ms counter on AURA page (G15 violation — max 800ms), no energy picker in onboarding (P0 blocker), no AI disclosure before first question (G18 not implemented), no scenario framing choice (VOLAURA rule 12 missing). New spec rules: VOLAURA Rule 28 (Pre-Assessment Commitment Layer — consolidates G18 + rule 12 + Law 2 energy check into one screen), Rule 29 (Vulnerability Window Positive Specification — what IS shown during 5-min window), Rule 30 (Ghosting Grace for pre-activation users — 48h warm re-entry). Landing: Sunk Cost Registration now specced (sample AURA profile, no login, fictional Leyla 74 Communication Silver). Fourth trust pill required: "Your score is only shared if you choose to." Pre-launch VOLAURA P0 blockers: 13 → 19 items. Guardrails G45-G46 added. Total guardrails: G1-G46. |
| v1.6 | 2026-04-06 | **Cultural intelligence agent, 7 findings.** P0 additions: ADHD clinical language ban in AZ/CIS copy — "ADHD"/"neurodivergent" never in AZ-facing user or B2B copy, applied silently as UX science (G40). AZ B2B requires human-first sales (demo-first, no self-serve enterprise — G42). Extended language rules: Russian as first-class locale (G41), AZ date format for certificates (DD [month_AZ] YYYY-cı/ci/cu/cü il), button text max 22 AZ chars, number decimal comma. Extended trust architecture: referral-first onboarding, employer visibility guarantee on assessment start screen, AZ org logos on landing. Credential display split (public: number-first; private: identity-first — G43). Community Signal widget (843 Baku professionals, aggregate by sector, no names — G44, must exist before AZ launch). Org Hall page (VOLAURA Rule 27). Law 3 extended with collectivist shame mechanics (face/ar/həya): sharing as honor claim vs privacy decision — both Western and AZ contexts must be satisfied simultaneously. New VOLAURA Rules 24-27. Total guardrails: G1-G44. |

**Next scheduled review:** 2026-07-06 (quarterly)
**Trigger for unscheduled review:** New research added to CEO corpus, or metric violation found.

---

*This document is the property of the VOLAURA ecosystem. It must be injected into every new agent context, every new chat session, and every design review. It is a living document but its 5 Foundation Laws and 7 Crystal Laws are permanent until CEO explicitly revises them with scientific backing.*
