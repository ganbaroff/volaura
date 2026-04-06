# Volaura Redesign Brief v2
## Informed by 17 CEO Research Documents + 3 Specialist Agents

**Date:** 2026-04-06
**Status:** Team-reviewed, ready for Figma build

---

## 1. Design System Amendments (Stitch ABANDONED — build from scratch per Constitution)

### Error Colors: Red → Purple/Amber
**Source:** Research #2 (RSD), #6 (Sensory UX), #8 (Age-based)
```
OLD: error #ffb4ab, error-container #93000a (red family)
NEW: error #d4b4ff, error-container #3d1a6e (purple family)
NEW: warning #e9c400, warning-container #3a3000 (amber)
```
**Rule:** Zero red anywhere in the UI. Errors = purple. Warnings = amber.

### Achievement Display: Numbers → Identity
**Source:** Research #10 (Overjustification Effect)
```
WRONG: "78.4" as headline, badge as decoration
RIGHT: "Gold-level Communicator" as headline, "AURA 78.4" as context
```
**Rule:** Identity is the headline, score is the subtitle. Never animate personal scores with count-up.

### Animation Safety
**Source:** Research #1 (rejected screen-shaking), #6 (sensory), ADHD Specialist audit

| Animation | Verdict | Fix |
|-----------|---------|-----|
| Page Fade 200ms | SAFE | Keep |
| Score Counter 2s | UNSAFE | Show instantly or max 800ms, one number at a time |
| Badge Reveal (bounce+rotate+sparkle) | UNSAFE | Scale only, gentle spring (damping:14) |
| Confetti 50 particles | UNSAFE | 12 particles max, 1.5s, contained area |
| Notification Pulse (infinite) | UNSAFE | 3 pulses then stop |
| Floating Orbs (15s loop) | UNSAFE | Remove from action screens |
| Progress Bar Fill | SAFE | Keep |
| Button Press 0.98 | SAFE | Keep |

**Rule:** Every animation MUST have `prefers-reduced-motion` branch. Max 1 animated number per screen.

### Empty States: First-Class Design
**Source:** Research #1 (78% abandon without trust), ADHD Specialist

**Pattern:** Single warm card, one action, no quantified incompleteness.
```
DO:   "Start your first assessment — 5 minutes, 1 skill" [Begin →]
DON'T: "Profile 40% complete" + 6 empty widget slots
```
**Rule:** Dashboard grows WITH the user. Each widget appears only after the action that generates its data.

### Energy-Adaptive UI
**Source:** Research #2, #3 (Energy Traffic Light)

| Energy | UI Level | Assessment |
|--------|----------|------------|
| Green (4-5) | Full UI, all animations | Available |
| Yellow (3) | Reduced widgets, entrance-only animations | Gated with "Ready?" |
| Red (1-2) | Single-action card, fade-in only, warm copy | Hidden |

---

## 2. Screen Priority Order (by conversion funnel)

1. **Dashboard Empty State** — first thing new user sees after onboarding
2. **Signup** — build from Constitution rules: glass hero, trust pills, role selection, GDPR (no Stitch reference)
3. **Assessment Flow** — core product, ADHD-optimized (break every 5 Qs, no timer, no interim scores)
4. **Results Celebration** — identity framing, NOT number-as-headline
5. **Profile** — credential display, discoverable indicator
6. **Dashboard Populated** — returning user with data

---

## 3. Technical Implementation

### Token Migration (globals.css)
- Replace 4 error tokens (red → purple)
- Add warning tokens (amber)
- Add `@media (prefers-reduced-motion)` CSS block
- Add mesh-gradient-hero, noise-overlay, badge-glow utilities
- Approach: parallel tokens → alias → migrate → remove legacy

### shadcn Strategy
- **DO NOT replace** — override visually via CSS tokens + wrapper components
- Keep Radix accessibility primitives (keyboard nav, focus management, ARIA)
- Add `caution` variant to Alert and Button (amber warnings)

### New Dependencies (total +11KB gzipped)
```
@number-flow/react  (~5KB) — digit-by-digit animated score transitions
@formkit/auto-animate (~6KB) — zero-config list/DOM animations
```

### Visual Effects (all CSS-only, 0KB added)
- Mesh gradients: radial-gradient stacking on #13131b base
- Badge glow: box-shadow stacking + conic-gradient metallic sheen
- Noise texture: inline SVG feTurbulence at 4% opacity
- Aurora background: CSS blur on pseudo-elements
- Gradient text: background-clip technique

### New Hook
```
hooks/use-reduced-motion.ts — wraps Framer Motion useReducedMotion
Returns: transition, entrance, hoverScale, tapScale, shouldReduceMotion
```

---

## 4. ADHD Design Checklist (37 items)

### Cognitive Load (every screen)
- [ ] Exactly ONE primary CTA
- [ ] ≤5 tappable elements visible without scroll (mobile)
- [ ] Zero comparison language
- [ ] Zero red color
- [ ] Errors framed as system issues, not user mistakes
- [ ] Zero "you haven't done X yet" language
- [ ] Zero countdown timers / deadline urgency
- [ ] Locked achievements HIDDEN (no lock icons)
- [ ] Streak hidden when 0 or 1
- [ ] Works on "red energy day" (reducible to one action)

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
- [ ] Empty state = one warm action, not list
- [ ] Return-after-absence = warm, not guilt

### Assessment-Specific
- [ ] One question per screen
- [ ] ≤4 answer options without scroll
- [ ] Timer hidden
- [ ] Progress shows "X of ~Y completed" (filled, not depleted)
- [ ] Break point every 5 questions
- [ ] Interim scores hidden
- [ ] Exit + resume within 24h without loss
- [ ] Micro-confirmations subtle (checkmark fade, no sound, no score)

### Energy Adaptation
- [ ] Energy detection or manual input
- [ ] Low energy: assessment hidden/gated
- [ ] Low energy: fade-in only animations
- [ ] Low energy: single card dashboard
- [ ] Low energy: warm non-directive copy

---

## 5. Signup Must-Keeps (validated by research — DO NOT LOSE)

- Trust signal pills ("No CV", "Data private", "No spam") — Research #1 validated
- Volunteer/Organization role selection — Research #9 validated
- GDPR age confirmation checkbox — legal requirement
- Invite code gate — controlled rollout mechanism
- Password hint text — reduces anxiety
- Disabled-button UX hint — accessibility fix from this session

---

## 6. Reference Design Direction

**Aesthetic:** Linear's restraint + Brilliant's smart gamification + Raycast's glass accents
**Color:** Purple accent (not LinkedIn blue), dark obsidian base
**Typography:** Inter (body) + Plus Jakarta Sans (headlines)
**Glass:** Selective — hero cards, score display. NOT on nav, forms, tables.
**Animations:** Fade entrances, spring physics, staggered reveals. No confetti, no infinite loops.

**3 reference apps:**
1. Linear — surface hierarchy, minimal color, keyboard-first
2. Brilliant.org — score presentation, progress indicators, adult gamification
3. Raycast — card design, glassmorphism accents, achievement metadata
