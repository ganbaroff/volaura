# MindShift + VOLAURA Design Canon — 2026-04-24

**Purpose:** Short execution canon for design work across MindShift and VOLAURA.
**Audience:** Atlas, Claude Design, frontend builders.
**Authority:** Derived from `docs/ECOSYSTEM-CONSTITUTION.md`, `docs/research/adhd-first-ux-research.md`, `docs/TONE-OF-VOICE.md`, `docs/MINDSHIFT-INTEGRATION-SPEC.md`, `docs/research/ecosystem-design-research.md`, `docs/design/ANIMATION-SYSTEM.md`.

---

## 1. Core Truth

This ecosystem is not allowed to look "impressive" at the cost of nervous-system safety.

MindShift and VOLAURA are not generic SaaS dashboards.
They are cognitive environments.
Design must reduce shame, reduce overload, preserve continuity, and make progress feel real.

---

## 2. Non-Negotiable Laws

1. **Never red.**
   Errors use purple. Warnings use amber. Never use red as punishment or alarm styling.

2. **One primary action per screen.**
   No competing CTAs.

3. **Shame-free language.**
   Never guilt users. Never frame them as failing, behind, incomplete, lazy, or broken.

4. **Energy adaptation is mandatory.**
   Full / Mid / Low energy modes are product law, not a nice-to-have.

5. **State must survive interruption.**
   Especially in onboarding, assessment, habits, and profile flows.

6. **Motion must be meaningful.**
   Decorative excess is banned. Reduced-motion must always have a safe branch.

7. **No punishment loops.**
   No streak loss shame, no negative gamification, no manipulative urgency.

---

## 3. What VOLAURA Is

VOLAURA is the trust layer:
- verified skill assessment
- AURA score
- badges
- profile credibility
- organization discovery

Its visual job is:
- trust
- clarity
- measured confidence
- proof without arrogance

Color center:
- **Indigo** for trust and credibility

Tone center:
- earned
- specific
- honest
- systemic

VOLAURA should feel:
- calm
- precise
- slightly premium
- never noisy

---

## 4. What MindShift Is

MindShift is the regulation layer:
- habits
- focus
- energy
- consistency
- ADHD-aware daily support

Its visual job is:
- safety
- momentum
- non-judgment
- low-friction re-entry

Color center:
- **Emerald** for growth and health

MindShift should feel:
- breathable
- forgiving
- immediate
- alive but not overstimulating

---

## 5. Shared Ecosystem Rules

1. **Character is the identity anchor.**
   Cross-product continuity should feel like one life, not many apps.

2. **Navigation must be low-cognitive-load.**
   Visible destinations, clear headers, no hidden maze navigation.

3. **Snapshot-first clarity.**
   The user should always know:
   - where they are
   - what matters here
   - what the next action is

4. **Cross-product links must feel natural.**
   MindShift contributes behavioral truth.
   VOLAURA contributes verified truth.
   Do not visually imply they are the same thing.

5. **The ecosystem may be deep, but the screen must stay simple.**

---

## 6. ADHD-First UI Rules

From research, these are implementation-level laws:

1. One action per screen in onboarding and assessment.
2. Left-align all text.
3. Never hide time or orientation.
4. Always save progress.
5. Focus mode toggle is good design, not an edge feature.
6. Avoid hover-dependent meaning.
7. Avoid dense comparison grids as the primary surface.
8. Keep labels visible; do not rely on icon-only navigation for primary routes.
9. Use positive reinforcement only.
10. Re-entry after interruption must be gentle and obvious.

---

## 7. Motion Rules

From animation system + constitution:

- Fast feedback: around 150ms
- Normal transitions: around 300ms
- Slow reveal: around 500ms
- Hard ceiling for meaningful motion: 800ms
- Respect `prefers-reduced-motion`
- Motion should mark:
  - transition
  - achievement
  - state change
- Motion should not be used for:
  - decoration for decoration's sake
  - hover fireworks
  - endless drifting backgrounds
  - cognitive bait

---

## 8. Tone Rules In UI Copy

UI copy must sound:
- direct
- calm
- human
- equal

It must not sound:
- corporate
- salesy
- influencer-like
- falsely therapeutic
- artificially cheerful

Good:
- specific
- short
- honest
- grounded in real action

Bad:
- "We're excited to share"
- "innovative solution"
- "complete your profile now"
- "you're almost there"
- any guilt-shaped progress language

---

## 9. Product Split For Design Work

### VOLAURA surfaces to polish first
- onboarding
- assessment
- AURA/results
- profile/public proof
- organization discovery

### MindShift surfaces to polish first
- focus start
- post-session flow
- energy logging
- streak/consistency feedback
- re-entry after interruption

---

## 10. What Claude Design May Change

- layout
- spacing
- visual hierarchy
- iconography
- page rhythm
- safe animation details
- empty / loading / error / success states
- token usage

## 11. What Claude Design May NOT Invent

- new product truths
- new gamification laws
- manipulative urgency
- leaderboard-like social pressure
- red failure language
- multi-CTA hero chaos
- architecture claims that runtime does not support

---

## 12. Acceptance Checklist

Before any design pass is accepted:

1. Is there one clear primary action?
2. Is the screen shame-free?
3. Can a tired or interrupted user re-enter without stress?
4. Is motion useful and safe?
5. Does this fit the product's role:
   - VOLAURA = trust
   - MindShift = regulation
6. Does it reduce cognitive load instead of adding flair?
7. Does it preserve ecosystem continuity without collapsing product boundaries?

---

## 13. Current Strategic Read

The research is already here.
The problem is not lack of design philosophy.
The problem is turning this philosophy into one enforced canon so builders stop improvising.

This file is that canon.
