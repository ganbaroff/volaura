# VOLAURA Design System Implementation Synthesis

> ⚠ STATUS: synthesis 2026-04-25 19:30 (Code-Atlas via NotebookLM).
> Color decisions in §3 (Product Accent/Skin Model) are SUPERSEDED:
> - VOLAURA accent #4F46E5 here → runtime says #7C5CFC (globals.css L132). Runtime wins.
> - Atlas accent #10B981 here → breadcrumb design verdict 2026-04-25 says #5EEAD4 mint-teal. Breadcrumb wins.
> - MindShift accent #10B981 confirmed valid (matches design verdict).
> Token values in §1 Tier 1-2 are valid. Motion grammar §4 is valid.
> Treat color rows in §3 as stale. All other sections are active reference.

# Notebook ID: c95cb222-91a9-4b9d-8ca3-6a59d1db03bc
# Title: VOLAURA Ecosystem Design DNA -- 2026-04-25
# Run timestamp: 2026-04-25T19:30 UTC
# Sources used: 13 ready (globals.css stuck at status preparing -- SourceType.UNKNOWN, not indexed by NotebookLM)
# Source titles: ANIMATION-SYSTEM.md, BASELINE-2026-04-15.md, CLAUDE.md, COMPONENT-LIBRARY.md (x2),
#   DESIGN-MANIFESTO.md, DESIGN-SYSTEM-AUDIT.md, ECOSYSTEM-CONSTITUTION.md, MINDSHIFT-INTEGRATION-SPEC.md,
#   MINDSHIFT-VOLAURA-DESIGN-CANON-2026-04-24.md, PHASE-0-ECOSYSTEM-DESIGN-PLAN.md,
#   adhd-first-ux-research.md, ecosystem-design-research.md
# Conversation ID: 439f7e10-2a88-46a7-8031-eb5a2727e9e6

---

### 1. ECOSYSTEM TOKEN MODEL
Tokens follow a 3-tier inheritance architecture (DESIGN-MANIFESTO.md, Principle 5). All tokens are defined in the @theme block of apps/web/src/app/globals.css (BASELINE-2026-04-15.md, Section 3).

* TIER 1: RAW PRIMITIVES (Ecosystem-wide)
--color-base: #0a0a0f (Warm black for dark mode) (DESIGN-MANIFESTO.md, Law 3)
--font-body: "Inter" (DESIGN-MANIFESTO.md, Typography Scale)
--font-heading: "Plus Jakarta Sans" (DESIGN-MANIFESTO.md, Typography Scale)
--font-mono: "JetBrains Mono" (ANIMATION-SYSTEM.md, A03)
--radius-default: 12px (0.75rem) (DESIGN-SYSTEM-AUDIT.md, Radius Tokens)

* TIER 2: SEMANTIC ROLES (Ecosystem-wide)
--color-error: #D4B4FF (Purple) (ECOSYSTEM-CONSTITUTION.md, Law 1)
--color-warning: #E9C400 (Amber) (ECOSYSTEM-CONSTITUTION.md, Law 1)
--color-surface-lowest: L+0
--color-surface-high: L+32 (DESIGN-MANIFESTO.md, Law 3)
--spacing-md: 16px (Adapts by energy mode: 16/12/8) (DESIGN-MANIFESTO.md, Spacing)

* TIER 3: PRODUCT ACCENT + DENSITY + MOTION
--color-product-volaura: #4F46E5 (Indigo) (DESIGN-MANIFESTO.md, Face Definition)
--color-product-mindshift: #10B981 (Emerald) (DESIGN-MANIFESTO.md, Face Definition)
--color-product-lifesim: #7C3AED (Purple) (BASELINE-2026-04-15.md, Section 3)
--color-product-brandedby: #F59E0B (Amber) (DESIGN-MANIFESTO.md, Face Definition)
--motion-rhythm: (Spring: damping 14, stiffness 100) (DESIGN-MANIFESTO.md, Law 4)

### 2. SHARED COMPONENT TAXONOMY
Components are divided into "Skeleton" (Inherited DNA) and "Skin" (Face-specific character) (DESIGN-MANIFESTO.md, Law 7).

* SKELETON COMPONENTS (Shared/Unchanged)
- AppSidebar (components/navigation/app-sidebar.tsx) (COMPONENT-LIBRARY.md, 50)
- BottomNavV2 (components/navigation/bottom-nav-v2.tsx) (COMPONENT-LIBRARY.md, 52)
- TopBarV2 (components/navigation/top-bar-v2.tsx) (COMPONENT-LIBRARY.md, 55)
- BadgeTierChip (components/badges/badge-tier-chip.tsx) (COMPONENT-LIBRARY.md, 57)
- ScoreDisplay (components/visualizations/score-display.tsx) (COMPONENT-LIBRARY.md, 65)
- Toast (components/system/toast.tsx) (COMPONENT-LIBRARY.md, 98)
- PageSkeleton (components/system/page-skeleton.tsx) (COMPONENT-LIBRARY.md, 96)

* SKIN COMPONENTS (Per-product variants)
- QuestionCardV2: Variants for BARS, MCQ, Open Text (COMPONENT-LIBRARY.md, 69)
- CompetencyCard: Displays product-specific scores (MindShift habits vs VOLAURA skills) (COMPONENT-LIBRARY.md, 72)
- FloatingOrbs: Landing hero (VOLAURA) vs Focus Screens (MindShift -- Banned per Law 4) (COMPONENT-LIBRARY.md, 87)

### 3. PRODUCT ACCENT/SKIN MODEL
Defined by the "Customization Contract" (DESIGN-MANIFESTO.md, Law 7).

| Face       | Accent Color | Density  | Motion Rhythm | Character Voice |
|------------|--------------|----------|---------------|-----------------|
| VOLAURA    | Indigo       | Balanced | Systemic      | Earned/Precise  |
| MindShift  | Emerald      | Low      | Breathable    | Forgiving/Human |
| Life Sim   | Purple       | High     | Active        | Playful/Story   |
| BrandedBy  | Amber        | Medium   | Amplifying    | Assistant       |
| Atlas      | Emerald      | System   | Invisible     | Implicit        |

### 4. MOTION GRAMMAR
All motion is governed by ANIMATION-SYSTEM.md and ECOSYSTEM-CONSTITUTION.md Law 4.

* DURATIONS:
- Fast Feedback: ~150ms (DESIGN-CANON-2026-04-24.md, 7)
- Normal Transitions: 300ms (A07)
- Slow Reveal: 500ms (A04)
- Max Ceiling: 800ms (ECOSYSTEM-CONSTITUTION.md, Law 4)

* CURVES:
- Primary: Spring (damping 14, stiffness 100) (DESIGN-MANIFESTO.md, Law 4)
- Bouncy: (stiffness 400, damping 10) for achievements ONLY (A04)

* ADAPTATIONS:
- prefers-reduced-motion: Instant/Duration 0 (ANIMATION-SYSTEM.md, 20)
- Low Energy: Zero motion (DESIGN-MANIFESTO.md, Law 4)
- Mid Energy: Entrance-only animations (DESIGN-MANIFESTO.md, Law 4)

### 5. COPY/TONE GRAMMAR
Governed by ECOSYSTEM-CONSTITUTION.md Law 3 and Law 10.

* CORE RULES:
- No "X% complete" or "You missed X days" (Law 3)
- No "0 of X completed" (Replace with "Start ->") (Law 3)
- No "Locked" icons (Hide locked items entirely) (Law 3)
- Azerbaijani: Mandatory formal "Siz" form (Law 10)

* CHARACTER VOICES:
- Mochi (MindShift): Peer/Observer, not supervisor (ECOSYSTEM-CONSTITUTION.md, MindShift Rule 6)
- Atlas (VOLAURA): Systemic intelligence, never says "I" (DESIGN-MANIFESTO.md, Principle 3)

### 6. ENERGY ADAPTATION UI CONTRACT
Every screen adapts based on use-energy-mode.ts (BASELINE-2026-04-15.md, Section 5).

* FULL ENERGY: All animations (A01-A18), full content density, multiple widgets.
* MID ENERGY: Entrance animations only, standard spacing (--spacing-md: 12px) (DESIGN-MANIFESTO.md, Spacing).
* LOW ENERGY: Zero motion, single-action focus cards, compressed spacing (--spacing-md: 8px), "Ready when you are" gating for assessments (ECOSYSTEM-CONSTITUTION.md, G12).

### 7. CROSS-PRODUCT NAVIGATION
The architecture is "One Body, N Faces" (DESIGN-MANIFESTO.md, Law 7).

* UI ELEMENTS:
- Mobile (< 1024px): BottomNavV2 with 5 slots (COMPONENT-LIBRARY.md, 53)
- Desktop (>= 1024px): AppSidebar with feature groupings (COMPONENT-LIBRARY.md, 50)
- App Switcher: Embedded in Character Avatar (ecosystem-design-research.md, 2)

* URL PATTERN:
- /${locale}/${product_slug}/... (e.g., /az/mindshift/focus) (CLAUDE.md, File Naming)

* ATLAS MANIFESTATION:
- Atlas is NOT a tab. Atlas is the Tab Bar glass itself and the transition logic (DESIGN-MANIFESTO.md, Principle 5).

### 8. SYSTEM SURFACES
Where core ecosystem systems manifest in the UI:

* CHARACTER IDENTITY: Character avatar with BadgeTierChip glow in AppSidebar and ProfileHeader (COMPONENT-LIBRARY.md, 105).
* EVENT BUS: Surfaces in "Character Sheet" replacing the dashboard, showing cross-face XP (ecosystem-design-research.md, 7).
* CRYSTAL ECONOMY: Balance displayed in MindShift ProgressPage and Life Sim store (MINDSHIFT-INTEGRATION-SPEC.md, 1.2).
* ENERGY MODES: EnergyPicker in onboarding (ECOSYSTEM-CONSTITUTION.md, VOLAURA P0) and TopBarV2 toggle (DESIGN-CANON-2026-04-24.md, 4).

### 9. THREE FLAGSHIP CROSS-PRODUCT FLOWS
All flows write to character_events (DESIGN-MANIFESTO.md, Law 7).

1. ASSESSMENT TO IDENTITY:
- User completes VOLAURA Communication Assessment.
- Emits: { type: "assessment_completed", competency: "communication", score: 78 }
- Outcome: User profile header updates to "Gold-level Communicator" (DESIGN-MANIFESTO.md, Principle 2).

2. FOCUS TO GROWTH:
- User completes 25-min MindShift Focus session.
- Emits: { type: "focus_session_completed", duration: 25, xp: 250 }
- Outcome: Life Sim character gains +Intelligence; Crystal balance increases by 2 (MINDSHIFT-INTEGRATION-SPEC.md, 2.2).

3. BADGE DISCOVERY TO B2B:
- User earns Platinum badge in Tech Literacy.
- Emits: { type: "badge_tier_updated", tier: "platinum" }
- Outcome: Profile becomes discoverable to Tier 3 B2B Orgs with verifiable DeCE evidence (ECOSYSTEM-CONSTITUTION.md, VOLAURA Rule 17).

### 10. PHASED ROLLOUT
Honest split based on Next.js 14 + Supabase readiness (BASELINE-2026-04-15.md, Section 1).

* NOW (VOLAURA + MindShift):
- Tier 1-2 tokens in globals.css @theme.
- Skeleton components (AppSidebar, BottomNav, TopBar).
- Supabase auth migration to single project (MINDSHIFT-INTEGRATION-SPEC.md, 2.1).
- Azerbaijani localization parity.

* LATER (Life Sim + BrandedBy):
- Tier 3 accent tokens for Purple (#color-product-lifesim) and Amber.
- Three.js/Godot runtime for character office (claw3d).
- Full Crystal Spend path (Crystal Law 8).
- Multi-model ZEUS routing (Research #12).

### 11. ACCEPTANCE CHECKLIST
Binary pass/fail for all new PRs (DESIGN-CANON-2026-04-24.md, 12).

1. [ ] Is there exactly one primary CTA (gradient/filled)? (Constitution Law 5)
2. [ ] Are all red hex codes (#FF0000, text-red-*) zeroed out? (Constitution Law 1)
3. [ ] Does the screen avoid shame-based language ("missing", "fail", "0%")? (Constitution Law 3)
4. [ ] Are all animations <= 800ms? (Constitution Law 4)
5. [ ] Is there a prefers-reduced-motion fallback for every animation? (Constitution Law 4)
6. [ ] Does the screen render a valid Low Energy variant? (Constitution Law 2)
7. [ ] Are Azerbaijani strings tested for 30% text-expansion? (Research #1)
8. [ ] Does the screen avoid auto-playing audio or video? (Constitution Law 4)
9. [ ] Are interactive hit targets >= 44x44px? (DESIGN-SYSTEM-AUDIT.md, Section 4)
10. [ ] Does the screen write at least one event to character_events? (DESIGN-MANIFESTO.md, Principle 2)
11. [ ] Is the primary typeface Inter >= 400 weight for body copy? (DESIGN-MANIFESTO.md, Typography)
12. [ ] Does the screen provide an exit/resume path for long flows? (ADHD Rule 3)
13. [ ] Is the formal "Siz" form used for all Azerbaijani copy? (Constitution Law 10)
14. [ ] Are locked achievements completely invisible (no locks)? (Constitution Law 3)
15. [ ] Is the primary action placement within thumb-reach on mobile? (Research #8)
