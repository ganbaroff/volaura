# VOLAURA Ecosystem Design DNA - Synthesis 2026-04-25

> ⚠ STATUS: synthesis 2026-04-25 19:09 (Code-Atlas via NotebookLM).
> Color decisions in this document are SUPERSEDED:
> - VOLAURA accent #4F46E5 here → runtime says #7C5CFC (globals.css L132). Runtime wins.
> - Atlas accent #10B981 here → breadcrumb design verdict 2026-04-25 says #5EEAD4 mint-teal. Breadcrumb wins.
> - MindShift accent #10B981 confirmed valid (matches design verdict).
> Contradiction findings (animation 2s vs Constitution 800ms, LeaderboardRow vs G46) ARE valid — these were the real value-add.
> Treat as historical reference, not live canon.

_Generated via NotebookLM with 11 internal canon sources. Run by Atlas at CEO request._

_Notebook ID: c95cb222-91a9-4b9d-8ca3-6a59d1db03bc - VOLAURA Ecosystem Design DNA - 2026-04-25_

---

### 1. DESIGN AUTHORITY MAP
The ecosystem's governance follows a strict hierarchy of truth, prioritizing research-backed constitutional laws over transient implementation plans.

* **Ecosystem Constitution (ECOSYSTEM-CONSTITUTION.md):** The **Supreme Authority**. It supersedes any design, code, or product decision that contradicts it. It codifies the "5 Foundation Laws" and "7 Crystal Laws" (ECOSYSTEM-CONSTITUTION.md, Authority).
* **Design Manifesto (DESIGN-MANIFESTO.md):** The **Genetic Code**. It defines the "One Organism, N Faces" philosophy and the "Inheritance Contract" that ensures all products share a single skeleton (DESIGN-MANIFESTO.md, The Inheritance Contract).
* **Design Canon (MINDSHIFT-VOLAURA-DESIGN-CANON-2026-04-24.md):** The **Execution Spec**. A distilled, high-velocity version of the Constitution and research for immediate frontend application (MINDSHIFT-VOLAURA-DESIGN-CANON-2026-04-24.md, Purpose).
* **Research Synthesis (adhd-first-ux-research.md, ecosystem-design-research.md):** The **Scientific Evidence**. These documents provide the psychological grounding (ADHD-first, Gen Z, and AZ/CIS trust patterns) for the laws (adhd-first-ux-research.md, ADHD-First UI Rules).
* **Baseline Audit (BASELINE-2026-04-15.md):** The **Ground Truth**. It represents the current state of the codebase, explicitly flagging deviations from the Constitution (BASELINE-2026-04-15.md, Purpose).
* **Phase-0 Design Plan (PHASE-0-ECOSYSTEM-DESIGN-PLAN.md):** The **Operational Roadmap**. A 28-day, 8-stage plan to move from the current "62/100" audit score to a launch-ready ecosystem (PHASE-0-ECOSYSTEM-DESIGN-PLAN.md, Mission).
* **Technical Specs (ANIMATION-SYSTEM.md, COMPONENT-LIBRARY.md):** The **Implementation Manuals**. Catalogues of tokens, components, and animations meant to execute the "Skeleton" (ANIMATION-SYSTEM.md, Purpose; COMPONENT-LIBRARY.md, Description).
* **Design System Audit (DESIGN-SYSTEM-AUDIT.md):** **Superseded History**. This document is obsolete and preserved only for audit trails (DESIGN-SYSTEM-AUDIT.md, Header).

### 2. CURRENT CANON vs SUPERSEDED HISTORY
The ecosystem is currently in a state of high-friction transition where legacy code frequently violates new constitutional mandates.

* **Binding Canon:** The **Ecosystem Constitution v1.2+** and the **Design Canon (2026-04-24)** are the only binding authorities for new work (ECOSYSTEM-CONSTITUTION.md, Authority).
* **Superseded History:** The **March 2022 Design System Audit** is officially dead, replaced by the **Baseline Audit 2026-04-15** (BASELINE-2026-04-15.md, Supersedes).
* **Terminological Purge:** The Constitution has **banned the word "volunteer"** in favor of "professional/talent/specialist/user." Any code using "volunteer" (e.g., org-volunteers route) is considered legacy technical debt and must be renamed (BASELINE-2026-04-15.md, Positioning-lock violations).
* **Shadow Redundancy:** Previous "v0.dev" output is the source of the current "site Yusif dislikes," and is being systematically replaced by research-backed components (PHASE-0-ECOSYSTEM-DESIGN-PLAN.md, Why Phase-0 Exists).

### 3. THE 10 CORE DESIGN LAWS
These laws are non-negotiable genetic constraints (ECOSYSTEM-CONSTITUTION.md, Part 1).

1. **Law 1: NEVER RED.** Zero red anywhere in the UI. Errors must be purple (#D4B4FF), warnings amber (#E9C400). **Violation:** BASELINE-2026-04-15.md identifies that "text-destructive" in the signup page may still resolve to red (ECOSYSTEM-CONSTITUTION.md, Law 1; BASELINE-2026-04-15.md, Finding P0-17).
2. **Law 2: ONE PRIMARY ACTION.** Exactly one primary CTA (gradient/filled) per screen to prevent decision paralysis. **Violation:** Legacy hero sections are described as "multi-CTA chaos" (ECOSYSTEM-CONSTITUTION.md, Law 5; MINDSHIFT-VOLAURA-DESIGN-CANON-2026-04-24.md, Non-Negotiable Laws).
3. **Law 3: SHAME-FREE LANGUAGE.** No "X% complete" or "you missed X days." Guilt-based progress tracking is prohibited. **Violation:** Legacy profile completion percentages are still found in early designs (ECOSYSTEM-CONSTITUTION.md, Law 3; DESIGN-MANIFESTO.md, Anti-Patterns).
4. **Law 4: ANIMATION SAFETY.** All animations must be <= 800ms and must have a "prefers-reduced-motion" branch. **Violation:** ANIMATION-SYSTEM.md A03 Score Counter currently uses a 2-second duration, which is flagged as "UNSAFE" by the Constitution (ECOSYSTEM-CONSTITUTION.md, Law 4; ANIMATION-SYSTEM.md, A03).
5. **Law 5: ENERGY ADAPTATION.** Every screen must render in Full, Mid, and Low energy modes. **Violation:** 17 of 18 canonical pages currently lack a real Low-energy render branch (ECOSYSTEM-CONSTITUTION.md, Part 5; BASELINE-2026-04-15.md, Energy-mode coverage).
6. **Law 6: IDENTITY FIRST, DATA SECOND.** Headlines must define *who the user is* ("Gold-level Communicator"), not just the raw score number. **Violation:** Early v0 designs used "score-as-headline" (DESIGN-MANIFESTO.md, Law 5; ECOSYSTEM-CONSTITUTION.md, Crystal Law 4).
7. **Law 7: SKELETON IS SACRED.** All faces must use ecosystem-standard components (Buttons, Cards, Toasts). Faces cannot rebuild their own. **Violation:** Audit finds 6-7 critical components are missing and likely being improvised (DESIGN-MANIFESTO.md, Principle 1; DESIGN-SYSTEM-AUDIT.md, Component Completeness Audit).
8. **Law 8: CALM IS THE LUXURY.** No autoplay, no uninvited modals, and maximum one animated element per viewport. **Violation:** "FloatingOrbs" (A13) drifting on focus screens is now banned (DESIGN-MANIFESTO.md, Law 4; ECOSYSTEM-CONSTITUTION.md, Law 4).
9. **Law 9: CRYSTAL TRANSPARENCY.** Do not launch "Earn" paths without a "Spend" path. Earning with no purpose is a permanent trust-break. **Violation:** Most products currently only have "Earn" placeholders (ECOSYSTEM-CONSTITUTION.md, Crystal Law 8).
10. **Law 10: FORMAL "SIZ" MANDATE.** Azerbaijani copy must use the formal "Siz" form. Informal "Sen" is a trust-killer in AZ professional culture. **Violation:** Often ignored in generic English-to-AZ machine translations (ECOSYSTEM-CONSTITUTION.md, Language Rules).

### 4. SKELETON vs SKIN MODEL
The ecosystem is structured as a single organism where the "Skeleton" provides the body and the "Skin" provides the personality (DESIGN-MANIFESTO.md, One Body, N Faces).

* **The Skeleton (Shared/Inherent):**
    * **Identity Layer:** Single Supabase auth, user profile, and AURA score.
    * **Design Tokens (Tier 1-2):** Surface palette, spacing, typography, and shadow/elevation specs.
    * **Universal Systems:** Energy modes (Full/Mid/Low), Crystal economy, and the Event Bus (character_events).
    * **Navigation:** The Tab Bar glass, active highlight logic, and navigation slots.
    * **Component Library:** Base Button, Card, Toast, and Avatar primitives.

* **The Skin (Face-Specific):**
    * **Accent Color:** A single Tier 3 product color (e.g., Indigo for VOLAURA).
    * **Character:** The specific AI persona (e.g., Mochi for MindShift, Atlas for VOLAURA).
    * **Tone and Voice:** Specific copy templates and "character voice."
    * **Density and Rhythm:** Content density (Low for coaching, High for games) and animation rhythm.

* **The Contract:** Defined as the **"Inheritance Contract"** and **"Customization Contract"** in DESIGN-MANIFESTO.md.

### 5. FACE DIFFERENTIATION
The "N Faces" differ by role and accent while remaining tethered to the Atlas bloodstream.

| Face | Role | Accent Color | Character Voice | Content Density |
| :--- | :--- | :--- | :--- | :--- |
| **VOLAURA** | **Trust Layer:** Skills, badges, professional proof. | Indigo (#4F46E5) | Earned, precise, systemic. | Balanced (Clarity). |
| **MindShift**| **Regulation Layer:** Habits, focus, ADHD support. | Emerald (#10B981) | Breathable, forgiving, human. | Low (Focus). |
| **Life Sim** | **Narrative Layer:** Growth as a character story. | Purple (#7C3AED) | Playful, active. | High (Gamified). |
| **BrandedBy** | **Identity Layer:** AI-amplified professional presence. | Amber (#F59E0B) | Amplifying, assistant-like. | Medium (Feed). |
| **Atlas** | **Nervous System:** The intelligence behind all faces. | Emerald (#10B981) | Invisible/Implicit (Surfaces via others). | System-only (Admin). |
(DESIGN-MANIFESTO.md, The Customization Contract; MINDSHIFT-VOLAURA-DESIGN-CANON-2026-04-24.md, Sections 3-4).

### 6. EXPLICIT CONTRADICTIONS
1. **Animation Safety vs. Technical Spec:** ANIMATION-SYSTEM.md Spec A03 defines the Score Counter at **2 seconds** (A03, Spec). However, ECOSYSTEM-CONSTITUTION.md Law 4 explicitly declares any count-up > 800ms as **"UNSAFE"** and a risk for vestibular disruption (ECOSYSTEM-CONSTITUTION.md, Law 4).
2. **Badge Reveal Timing:** COMPONENT-LIBRARY.md describes the AssessmentResults component showing the badge immediately after reveal (AssessmentResults, States). ECOSYSTEM-CONSTITUTION.md "Crystal Law 6 Amendment" mandates that badge tiers be **"hidden until earned"** and only revealed at the *next* visit to prevent immediate contingent reward loops (ECOSYSTEM-CONSTITUTION.md, Crystal Law 6 Amendment).
3. **Leaderboard Existence:** COMPONENT-LIBRARY.md lists LeaderboardRow as an "Existing" component (LeaderboardRow, Status). ECOSYSTEM-CONSTITUTION.md G9 and G46 **prohibit leaderboards entirely** and command that any "/leaderboard" route be deleted as a direct constitutional violation (ECOSYSTEM-CONSTITUTION.md, G46).
4. **Red Feedback:** BASELINE-2026-04-15.md identifies the use of "text-destructive" classes in the signup flow (Finding P0-17). However, Law 1 (Never Red) and G1 mandate the **total elimination** of the red-family hex values from all products (ECOSYSTEM-CONSTITUTION.md, Law 1).

### 7. UNRESOLVED DESIGN QUESTIONS
1. **Auth Migration Priority:** Should the MindShift <-> VOLAURA auth migration prioritize **preserving local localStorage streak data** (via client-side emission) or **force a server-side reset** to ensure cross-product DB integrity? (MINDSHIFT-INTEGRATION-SPEC.md, Section 2.3).
2. **Design Polish Depth:** Does the CEO prioritize a **"cruise" rollout (4 weeks)** for full ecosystem-wide component polish or a **"sprint" rollout (2 weeks)** with reduced animation and character detail for the launch event? (PHASE-0-ECOSYSTEM-DESIGN-PLAN.md, Open Questions for CEO).
3. **Primary Localization:** Is the redesign first-pass restricted to **English-only**, or is parity-complete **Azerbaijani (AZ)** localization required for the Baku launch event despite the 40% text-length budget risk? (PHASE-0-ECOSYSTEM-DESIGN-PLAN.md, Open Questions for CEO).
4. **Crystal Spend Path:** Will the ecosystem launch with a functional **Spend Path** in at least one product, or will crystals be stored in a **"deferred queue"** despite the recognized risk of losing user trust permanently? (ECOSYSTEM-CONSTITUTION.md, Crystal Law 8).

---

## Source citations


_Total citations: 0_
