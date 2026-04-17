# Atlas Ecosystem Design Manifesto

**Date:** 2026-04-16
**Author:** Atlas
**Status:** Living document — governs every pixel across ALL 5 faces
**Scope:** VOLAURA · MindShift · Life Simulator · BrandedBy · Atlas
**Sources:** Apple HIG + Liquid Glass, Linear redesign, Toyota/Lexus L-finesse, Dieter Rams, Stripe dashboard, Material Design 3, ADHD-first research, Constitution Laws 1-5, v0Laura vision

---

## The North Star

This is not five products. This is not even "five products for now."

This is a living organism. Today it has five faces. Tomorrow it may have twelve. A new skill, a new AI character, a new domain of human competence — any of these could become a new face overnight. The organism grows.

Which means this manifesto cannot be a rulebook for five specific products. It must be DNA — a genetic code that any new face inherits the moment it's born. A face we haven't imagined yet must be able to read this document and know exactly how to look, how to speak, how to move, and how to connect to the body.

Apple's HIG doesn't list rules for "iPhone, iPad, Mac, Watch, TV." It defines principles that any device Apple ever builds will inherit. Toyota's TPS isn't instructions for the Camry factory — it's a production philosophy that works in any factory Toyota opens on any continent in any decade. That's the standard.

**The test for every rule in this document:** If we add a sixth face tomorrow — say, a career mentoring skill — can it read this manifesto alone and build itself correctly? If the answer is no, the rule is too specific. Rewrite it.

**Every design decision serves one question:** Does this make the organism feel alive, coherent, and trustworthy — no matter how many faces it grows?

---

## 7 Design Laws

### Law 1: ANTICIPATE, DON'T REACT

**Source:** Lexus "Seamless Anticipation" (Omotenashi) + Linear "surface exactly what you need, when you need it"

The interface knows what the user needs before they ask. An empty dashboard doesn't show eight empty widgets — it shows one warm invitation. A completed assessment doesn't dump numbers — it leads with identity ("Gold-level Communicator") and lets the user pull details when ready.

**Test:** If the user has to hunt for the next action, we failed.

### Law 2: EVERY ELEMENT EARNS ITS PLACE

**Source:** Dieter Rams #10 "as little design as possible" + Toyota waste elimination (muda) + Linear "strategic minimalism"

Nothing decorative without function. No animation that doesn't communicate state change. No widget that doesn't serve the user's current goal. If removing an element doesn't hurt comprehension — remove it.

In assessment flow: no timer unless the user opted in. No score counter animating mid-test. No progress percentage that triggers anxiety. Just the question, the options, and a quiet indicator of where you are.

**Test:** Point at any element and ask "what job does this do?" If the answer takes more than one sentence, simplify.

### Law 3: DEPTH THROUGH LIGHT, NOT DECORATION

**Source:** Apple Liquid Glass (lensing, refraction, surface tint) + Material Design 3 (tonal elevation) + our own "obsidian glass" palette

Dark interfaces communicate hierarchy through luminance, not borders or shadows alone. Higher elevation = lighter surface. Primary actions glow subtly. The background recedes.

VOLAURA's surface hierarchy:
- Base (#0a0a0f) → Container lowest → Container low → Container → Container high → Container highest
- Each step adds ~6-8 lightness points
- Primary surfaces use tinted overlay from primary color (#c0c1ff at low opacity)
- Glass effect: selective, hero elements only — never on forms or navigation

**Test:** Squint at the screen. Can you still see the hierarchy? If everything blends into one dark mass, add a luminance step. If it looks like a Christmas tree, remove glow.

### Law 4: CALM IS THE LUXURY

**Source:** ADHD-first research + Lexus "Incisive Simplicity" + Apple "Deference" + Constitution Law 4

Our users include people whose brains are already noisy. The interface is a calm room, not a casino.

Rules:
- No autoplay, auto-expand, or uninvited modals
- Maximum one animated element per viewport at any time
- All animations ≤ 800ms, spring physics (damping 14, stiffness 100)
- prefers-reduced-motion: instant everything, no exceptions
- Energy modes: Full (all animations) → Mid (entrance-only) → Low (zero motion, single-action cards)
- No notification badges with counts. No streak punishments. No "you missed 3 days"
- Break every 5 questions in assessment. No interim scores during the test.

**Test:** Would a person having an anxious day feel safe using this screen?

### Law 5: IDENTITY FIRST, DATA SECOND

**Source:** Research #10 (Overjustification Effect) + Constitution Law 3 (shame-free) + Redesign Brief v2

Numbers measure. Identity motivates. In every context where we display AURA scores:

```
✅ RIGHT                              ❌ WRONG
"Gold-level Communicator"              "78.4"
  AURA 78.4 · Top 15%                   Communication score
  "Your strength in active               Gold badge
   listening stands out"
```

The headline is who you are. The number is supporting evidence. The attribution explains why — because "because you demonstrated X" builds self-efficacy better than a leaderboard rank.

**Test:** Read only the headlines on any screen. Do they tell the user something about themselves, or about the system?

### Law 6: CRAFT IN THE DETAILS

**Source:** Toyota Takumi (master craftsmanship) + Stripe "reputation for quality" + Lexus "Intriguing Elegance"

The difference between good and great lives in micro-interactions:
- Button press: scale(0.98) with 100ms spring
- Card hover: 2px elevation shift, not a border change
- Focus ring: visible, high-contrast, custom-styled — never browser default
- Loading states: skeleton with subtle shimmer, never a spinner
- Error states: purple (#D4B4FF), never red. Copy explains what to do, not what went wrong
- Empty states: warm illustration, single CTA, no "0/8 complete"
- AZ typography: tested at every weight with ə ğ ı ö ü ş ç — no broken ligatures

The user shouldn't notice these. But they feel the difference between a polished product and a prototype.

**Test:** Show the same screen to someone for 3 seconds and for 30 seconds. At 3 seconds they should get the gist. At 30 seconds they should find nothing that feels unfinished.

### Law 7: ONE BODY, N FACES

**Source:** v0Laura vision + Constitution + Apple ecosystem HIG + Toyota TPS

This is the law that governs all other laws. Today there are five faces. Tomorrow there may be nine. The number doesn't matter. What matters is that every face is a skill in the `POST /api/skills/{name}` engine — not a separate product.

A face is born when a new domain of human growth needs its own personality, accent, and AI character. A face dies when it's absorbed into another face or proves unnecessary. The body doesn't care how many faces it has. The body cares that each face inherits the DNA.

#### The Inheritance Contract (what every face gets for free)

Any new face that joins the ecosystem automatically inherits:

1. **Identity layer:** One Supabase auth, one user profile, one avatar with badge tier glow. The user is the same person in every face. They never re-login. Their name, photo, and AURA score travel with them.

2. **Design tokens Tier 1-2:** Surface palette, spacing scale, typography scale, animation physics, shadow/elevation, glass material spec. A new face NEVER invents its own surface color or body font. It inherits.

3. **Constitution Laws 1-5:** Never Red, Energy Adaptation, Shame-Free Language, Animation Safety, One Primary CTA. These are not guidelines — they're genetic constraints. A face that violates them is malformed.

4. **Energy system:** Full/Mid/Low modes. A new face must render correctly at all three energy levels from Day 1. If a user is in Low energy, the new face shows a single-action card with fade-in only. No exceptions.

5. **Navigation slot:** The Tab Bar allocates a slot. The face provides an icon (inline SVG, 24x24), a label, and an accent color. That's all it needs to exist in the navigation.

6. **Event bus:** The face writes to `character_events`. Every action the user takes in the new face becomes part of their unified timeline. Other faces can read and interpret these events.

7. **Crystal economy:** The face can award crystals (earn events) and accept crystal spending (spend events). Balances are global, not per-face.

8. **Component library:** Button, Card, Toast, EmptyState, Avatar, Skeleton, ProgressBar — all ecosystem components. A new face uses them as-is, with its own accent color applied via Tier 3 tokens. It never rebuilds a Card from scratch.

#### Atlas: Not a Face — the Nervous System

Atlas is not face #5 with a green accent color. Atlas is the organism itself. The faces are Atlas's skills. The swarm agents are Atlas's specialized limbs. The event bus is Atlas's bloodstream. The Constitution is Atlas's genetic code.

In design terms this means:

1. **Atlas has no "page" in the traditional sense.** Atlas is present everywhere — in the navigation that connects faces, in the cross-face moments that prove the ecosystem is alive, in the agent characters that speak to users, in the intelligence that decides which face to surface next.

2. **Atlas surfaces through other faces, not alongside them.** When Security Agent detects a vulnerability, it speaks through whichever face the user is in — not through an "Atlas page." When BNE simplifies the screen due to cognitive overload, that's Atlas acting through MindShift's coaching face. Atlas is the conductor. The orchestra is the faces.

3. **The /atlas route exists for transparency, not navigation.** Power users and CEO see what Atlas is doing — swarm status, agent activity, system health. But regular users never need to "visit Atlas." They experience Atlas as the intelligence behind every face they use.

4. **Atlas accent (#10B981 emerald) appears only in system-level UI:** admin panels, agent status indicators, system notifications. Never in user-facing content. Users feel Atlas. They don't "use" Atlas.

Design implication: the Tab Bar has slots for user-facing faces. Atlas is NOT a tab. Atlas is the bar itself — the glass, the transitions, the intelligence behind which tab glows and when. If the ecosystem ever needs an admin/system view for users, it gets its own face with its own personality. Atlas stays invisible.

#### The Customization Contract (what makes each face unique)

Each face defines only these properties:

```
FACE DEFINITION {
  name:              string       // "mindshift", "lifesim", etc.
  accent:            hex color    // Tier 3 product token
  icon:              SVG          // 24x24, inline, two states (active/inactive)
  typography_mood:   string       // "calm", "playful", "professional", "creative", "system"
  motion_personality: string      // "minimal", "breathing", "bouncy", "fluid", "precise"
  content_density:   "low"|"medium"|"high"
  ai_character: {
    name:            string       // "Coach", "Narrator", "Evaluator", etc.
    tone:            string       // one-sentence personality description
    avatar:          SVG|image    // character visual
  }
  copy_templates: {
    empty_state:     string       // how this face says "nothing here yet"
    event_label:     function     // how this face describes a character_event
    greeting:        string       // how this face welcomes the user
  }
}
```

That's it. Everything else is inherited from the skeleton — which is Atlas. A new face is a config + its own page content. Not a new app. Not a new design system. A new skill that Atlas learned.

#### Face transitions (the Timing Design moment)

When a user switches from any face to any other face:
1. Tab accent color crossfades (200ms, ease-out) — CSS variable swap, not JS
2. Page content fades out/in (150ms) — stability over dynamism, no slide
3. Header tint shifts — inherited from new face's accent
4. Content loads from cache where possible (TanStack Query prefetch)
5. User never sees a blank page or a spinner between faces

This moment is the Toyota equivalent of engineering the feel of closing a car door. The user should feel like they're turning a page in a book — same book, new chapter — not launching a different app.

**Test for any new face:** Can someone add this face in under a day by providing: accent color, icon, AI character definition, copy templates, and one page of content? If the answer is yes, the ecosystem architecture is working. If they need to write custom components, override tokens, or build new navigation — the architecture failed.

---

## Ecosystem Design Principles

These principles are face-count-agnostic. They work for 5 faces. They work for 50.

### Principle 1: SKELETON IS SACRED, SKIN IS FREE

The skeleton is what makes this one organism: tokens, auth, navigation, energy, events, crystals, components. It never changes between faces. It never changes because a face requested it. If the skeleton needs to change, it changes for ALL faces simultaneously — that's a Constitution-level decision.

The skin is what gives each face personality: accent, motion style, character voice, content. The skin is free — any face can customize it within the contracts above. But skin never overrides skeleton. A face can't change the body font. A face can't disable energy modes. A face can't hide the Tab Bar.

When building anything, first question: "skeleton or skin?" Skeleton → `components/ui/`, face-agnostic, tested across all faces. Skin → `components/features/{face}/`, accent-aware, tested within that face.

### Principle 2: ONE BLOODSTREAM

The `character_events` table is the circulatory system. Every face writes events. Every face reads them. But each face interprets the same event through its own lens.

Raw event: `{ type: "assessment_completed", competency: "communication", score: 78 }`

How each face might render it:
- Verification face: "Communication assessment complete — AURA 78, Gold tier"
- Game face: "Your character gained +50 XP in Communication"
- Coaching face: "Great focused session — you dedicated time to skill development"
- Twin face: "Updated your professional profile with new Communication credential"

The API returns raw events. The face provides the interpretation template (see `copy_templates.event_label` in Face Definition). This means adding a new face doesn't require new backend endpoints for event display — just new copy templates.

### Principle 3: ATLAS IS ALWAYS PRESENT, NEVER VISIBLE

Atlas is the nervous system. Users never interact with "Atlas" directly. They interact with faces. But Atlas is everywhere:

- When a face transition feels seamless — that's Atlas prefetching content and crossfading accents.
- When an agent character speaks — that's Atlas choosing which agent, in which face's voice, at what moment.
- When a cross-face event fires — that's Atlas routing data from one skill to another.
- When the energy system adapts — that's Atlas reading the user's state and adjusting density.
- When a new face appears in the Tab Bar — that's Atlas allocating a navigation slot.

Design system requirements:
- Every component with dynamic content has a `speaker` slot (optional, renders agent avatar + name when provided). The agent speaks through the current face's voice, not through "Atlas voice."
- Empty states can be "spoken" by a face's character ("I'm looking for your data..." in the face's tone and accent)
- Notifications attribute intelligence: "Your coach noticed you've been focused today" (MindShift face, Atlas intelligence)
- The system never says "Atlas did X." It says "[Face character] noticed X" or "[Face character] suggests Y." Atlas is the intelligence. Faces are the voice.

### Principle 4: CROSS-FACE MOMENTS ARE FIRST-CLASS

The ecosystem proves it's alive when faces connect. These moments are not notifications bolted on after the fact — they are designed experiences.

Pattern for any cross-face moment:
- Source face accent + destination face accent in one card (gradient or split)
- Attribution copy: "Your [action] in [source face] unlocked [outcome] in [destination face]"
- One-tap deep link to the destination face
- Transition: source accent morphs into destination accent (400ms, ease-in-out)

This pattern works regardless of which faces are involved — it's face-agnostic by design. When a new face joins, it automatically participates in cross-face moments through the event bus. No special wiring needed.

### Principle 5: THE TAB BAR IS ATLAS MADE VISIBLE

The Tab Bar is the one place where Atlas has a physical presence. Not as a tab — as the bar itself. The glass, the transitions, the accent highlights, the dot indicators — that's Atlas showing the user the shape of the organism.

Design that scales:
- Fixed architecture: glass background, icons + labels, accent highlight on active
- Dynamic slots: faces register themselves via Face Definition (icon + accent + label). Atlas allocates slots.
- Current: user-facing faces only. No "Atlas" tab. No "Settings" tab in the bar. (Settings lives inside faces.)
- Future: could be 4 faces, could be 8. At 6+ consider a "more" overflow or smart collapsing based on usage frequency.
- Active tab: face accent color, filled icon, scale 1.0
- Inactive tabs: muted text, outline icon, scale 0.9
- Badge indicators: dot only — never count (Constitution Law 3)
- Ordering: Atlas decides (most-used first, or CEO-configured priority)

The tab bar should feel as natural as a Mac dock — always there, never in the way, growing as Atlas learns new skills. When a new face is born, it appears in the bar as naturally as a new app appears in a dock. No migration. No redesign. Just one more icon in the glass.

---

## Typography Scale (from Figma, formalized)

| Token | Size | Weight | Use |
|-------|------|--------|-----|
| --text-page | 24px | Bold (700) | Page titles |
| --text-section | 18px | SemiBold (600) | Section headers |
| --text-body | 14px | Regular (400) | Body copy, descriptions |
| --text-caption | 12px | Medium (500) | Muted secondary text |
| --text-overline | 10px | SemiBold (600) + tracking +15% | Labels, badges, categories |

Body: Inter. Headlines: Plus Jakarta Sans. Both verified for AZ character support.

In dark mode: use Medium (500) minimum for body text where possible — thin weights lose legibility against dark backgrounds.

---

## Color Discipline

### Never Red

Errors are purple (#D4B4FF on dark surface). Warnings are amber (#E9C400). Destructive actions use purple-container (#3d1a6e).

This is not aesthetic preference — it's Constitution Law 1, grounded in RSD (Rejection Sensitive Dysphoria) research. Red triggers shame responses in neurodivergent users. Purple communicates "attention needed" without emotional loading.

### Contrast Minimums

- Body text on surface: minimum 7:1 (we exceed WCAG AAA where possible)
- Large text (≥18px or ≥14px bold): minimum 4.5:1
- Interactive elements: minimum 3:1 against adjacent colors
- Disabled states: intentionally below 3:1 (communicates non-interactivity)

### Desaturation Rule

Saturated colors on dark backgrounds cause eye strain. All status colors use desaturated variants:
- Success: #34D399 (not #22C55E)
- Info: #93C5FD (not #3B82F6)
- Error: #D4B4FF (not #A78BFA)
- Warning: #E9C400 (not #EAB308)

---

## Spacing & Density

Energy-adaptive spacing, three tiers:

| Token | Full | Mid | Low |
|-------|------|-----|-----|
| --spacing-xs | 4px | 4px | 4px |
| --spacing-sm | 8px | 6px | 4px |
| --spacing-md | 16px | 12px | 8px |
| --spacing-lg | 24px | 20px | 16px |
| --spacing-xl | 32px | 24px | 20px |
| --spacing-2xl | 48px | 36px | 24px |

In Low energy mode, the interface compresses — fewer widgets, less padding, more direct paths. This isn't a degraded experience. It's a different energy mode, designed with equal care.

---

## What We Learned From Each Master (ecosystem lens)

**Apple (One HIG, Many Platforms):** Apple's deepest lesson isn't Liquid Glass or translucency — it's that they never designed iOS separately from macOS. One Human Interface Guidelines document. Each platform adapts it. When Apple added Vision Pro, it didn't need a new design philosophy — visionOS inherited the HIG. That's what our Face Definition contract does: any new face inherits the ecosystem DNA without needing a new design system.

**Linear (Calm Density):** In an information-dense product, not every element deserves equal weight. Navigation recedes. Content advances. Their LCH color space ensures perceptual uniformity across themes. For us: each face has different content density ("low" for coaching, "high" for game) but the same spacing tokens. Density is a face property. Typography isn't.

**Toyota (The System, Not The Car):** Toyota's genius isn't the Camry. It's TPS — a production philosophy that works in any factory, any country, any decade. When Toyota launches a new model, TPS is already there. Our Constitution + Face Definition contract is our TPS. When the sixth face arrives, it doesn't need onboarding. It inherits.

**Lexus (Timing Design):** The transitions between faces — that 200ms accent crossfade, the content fade, the way the header tint shifts — are the equivalent of engineering the feel of closing a Lexus door. Nobody notices when it's right. Everyone notices when it's wrong. These micro-moments are where "five apps" becomes "one organism."

**Dieter Rams (As Little Design As Possible):** The Face Definition contract is deliberately minimal: accent, icon, character, copy templates. That's it. Everything else is inherited. A new face should be born lean. If it needs 50 custom components to work, we failed — not the face, but the skeleton.

**Stripe (Tokens First):** Stripe rebuilt their entire dashboard theme system on design tokens — not on per-component styles. When they added dark mode, they changed tokens, not components. Our 3-tier token architecture (primitive → semantic → product) follows the same principle. When a new face arrives, it adds one Tier 3 accent. Zero Tier 1 or Tier 2 changes.

**Material Design 3 (Tonal Elevation):** Elevation through primary-color tint, not shadow. Each face's accent color tints its elevated surfaces differently — indigo glow for verification, blue glow for coaching, amber glow for game. Same mechanism, different personality. The skeleton handles the mechanism. The face provides the color.

---

## Anti-Patterns (things we never do — in ANY face, present or future)

These are genetic constraints. A new face inherits all of them. No exceptions, no "but this face is different."

1. **No red anywhere** — Constitution Law 1. Purple for errors. Amber for warnings. Every face.
2. **No profile completion percentages** — Constitution Law 3. No "40% complete." No "3 of 8 done."
3. **No score-as-headline** — Identity first. The number supports the identity, not the other way.
4. **No infinite scroll** — ADHD rule. Paginate or stop.
5. **No streak punishment** — "you missed 3 days" is shame. Streak ≤1 → hide the counter entirely.
6. **No count-up animation on personal scores** — Anxiety trigger. Show the number. Don't theatricalize it.
7. **No more than one primary CTA per screen** — Constitution Law 5. Every face, every page.
8. **No glass effect on forms or navigation** — Glass is for hero content. Obsidian glass on nav. Clear surfaces on forms.
9. **No autoplay anything** — Respect attention. User initiates, always.
10. **No browser-default focus ring** — Custom focus-visible or nothing.
11. **No pure black (#000000)** — Use #0a0a0f minimum. Warmth matters in dark mode.
12. **No thin font weights (<400) for body text** — Legibility on dark surfaces.
13. **No face-specific design tokens at Tier 1 or Tier 2** — A face can only add Tier 3 (accent). If a face needs a new surface color, that's a skeleton change requiring Constitution review.
14. **No custom components that duplicate skeleton components** — A face uses the ecosystem Button, Card, Toast, Avatar. It doesn't build its own. If the ecosystem component doesn't fit, improve the ecosystem component for all faces.
15. **No face that breaks without energy modes** — Every face renders at Full, Mid, and Low from Day 1. Not "we'll add Low energy support later."
16. **No face that doesn't write to character_events** — Silent faces are dead faces. The event bus is how the organism stays coherent.

---

## The Litmus Test for This Manifesto

If Atlas learns a new skill tomorrow — career mentoring, language learning, team collaboration, anything — and the developer building that face reads only this document:

1. Can they define their face in under an hour? (Face Definition contract)
2. Can they build their first page in under a day? (Using skeleton components)
3. Will their face look like it belongs? (Inherited tokens + Constitution)
4. Will their face connect to the bloodstream? (Event bus + cross-face moments)
5. Will their face work at Low energy? (Inherited energy system)
6. Will Atlas be invisible inside their face? (Intelligence present, brand absent)
7. Will other faces feel when something happens in the new face? (Cross-face moments fire automatically)

If all seven answers are yes, this manifesto is doing its job. If any answer is no, the skeleton needs work — not the face.

---

*This document is the DNA of the ecosystem. Every face inherits it. When in doubt, return here. When two options seem equal, choose the one that's calmer. When a face wants an exception, the answer is: improve the skeleton instead.*
