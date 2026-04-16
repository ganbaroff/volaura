# Ecosystem Design Gate — READ BEFORE BUILDING ANYTHING

**Authority:** This file is mandatory for every Atlas instance (Cowork, Terminal, any future body) before creating, modifying, or reviewing any UI component, page, style, animation, copy, or layout.

**One rule:** Nothing enters the ecosystem without passing through this gate.

---

## STEP 1: Read the DNA (every session, before first pixel)

```
READ ORDER (non-negotiable):
1. docs/design/DESIGN-MANIFESTO.md          — 7 Laws + Ecosystem Principles + Face Definition contract
2. docs/ECOSYSTEM-CONSTITUTION.md            — 5 Foundation Laws (supreme authority)
3. docs/design/MANIFESTO-GAP-ANALYSIS.md     — known gaps, don't repeat them
4. apps/web/src/app/globals.css              — live token state (Tier 1-2-3)
5. memory/atlas/project_v0laura_vision.md    — Atlas = the project, faces = skills
```

If you haven't read all 5, you are not ready to build. Stop. Read.

---

## STEP 2: Answer 4 questions (write answers before coding)

Before ANY UI work — new component, page, fix, or style change — answer in writing:

```
Q1: SKELETON OR SKIN?
    Skeleton = shared across all faces (tokens, auth, navigation, energy, events, base components)
    Skin = face-specific (accent, character voice, content, density)
    → If skeleton: change affects ALL faces. Test in at least 2 faces before merging.
    → If skin: change affects one face. Use Face Definition contract. Never touch Tier 1-2 tokens.

Q2: WHICH FACE OWNS THIS?
    Every piece of UI belongs to a face or to the skeleton.
    → If it belongs to a face: components go in components/features/{face}/
    → If it belongs to the skeleton: components go in components/ui/
    → If unclear: it's probably skeleton. Build it face-agnostic.

Q3: DOES THIS WORK AT ALL 3 ENERGY LEVELS?
    Full / Mid / Low. Not "we'll add Low later." Now.
    → Full: all animations, full density, all widgets
    → Mid: entrance-only animations, reduced density
    → Low: zero motion, single-action cards, maximum simplicity

Q4: DOES THE EVENT BUS KNOW?
    If this UI represents user action → character_events must fire.
    If this UI displays data from another face → it reads character_events.
    Silent UI = dead UI. The organism can't feel what it can't see.
```

---

## STEP 3: Check against the 16 anti-patterns

Before committing, scan your change against these. One violation = do not merge.

```
 1. No red anywhere (purple errors, amber warnings)
 2. No profile completion percentages
 3. No score-as-headline (identity first, number as context)
 4. No infinite scroll
 5. No streak punishment ("keep alive", "you missed", "X days behind")
 6. No count-up animation on personal scores
 7. No more than 1 primary CTA per screen
 8. No glass effect on forms or navigation (hero content only)
 9. No autoplay anything
10. No browser-default focus ring
11. No pure black #000000 (minimum #0a0a0f)
12. No thin font weights <400 for body text
13. No face-specific Tier 1 or Tier 2 tokens (faces only add Tier 3 accent)
14. No custom components duplicating skeleton components (improve skeleton instead)
15. No face that breaks without energy modes (Full/Mid/Low from Day 1)
16. No face that doesn't write to character_events
```

---

## STEP 4: Atlas awareness

Atlas is the nervous system, not a face. When building:

- Atlas never has a tab in the Tab Bar
- Atlas never speaks to users as "Atlas" — agents speak through the current face's voice
- Atlas is felt in transitions (accent crossfade), intelligence (right content at right time), and cross-face moments
- The /atlas route is for admin/CEO transparency, not user navigation
- If you're building something that "Atlas does" — ask: which face does the user SEE this through?

---

## STEP 5: Typography and spacing (until tokens are in CSS)

Until --text-* tokens are in globals.css, use these Tailwind equivalents consistently:

```
Page title:     text-2xl font-bold font-headline        (24px, 700, Plus Jakarta Sans)
Section header: text-lg font-semibold font-headline      (18px, 600, Plus Jakarta Sans)
Body:           text-sm font-normal                      (14px, 400, Inter)
Caption:        text-xs font-medium text-on-surface-variant  (12px, 500, Inter, muted)
Overline:       text-[10px] font-semibold uppercase tracking-widest  (10px, 600, Inter)
```

AZ strings: account for 20-30% longer text. Test with ə ğ ı ö ü ş ç at every weight.

---

## STEP 6: Loading states

No spinners. Period.

```
WRONG: <Loader2 className="animate-spin" />
RIGHT: <Skeleton className="h-[200px] w-full rounded-xl" />  ← matches actual content shape
```

Every loading state must mirror the shape of the content it replaces. The user sees the page forming, not a wheel spinning.

---

## STEP 7: Face transition spec

When user switches faces (tab tap):
1. Tab accent crossfade: 200ms ease-out (CSS variable swap)
2. Content fade: 150ms out, 150ms in (no slide — stability)
3. Header tint shift: follows new face accent
4. Prefetch: TanStack Query should have adjacent face data warm
5. Never: blank page, spinner, "loading..." text, or layout shift

---

## QUICK REFERENCE: Current faces

| Face | Accent | Density | Motion | Character |
|------|--------|---------|--------|-----------|
| VOLAURA | #7C5CFC | Medium | Minimal spring | Evaluator |
| MindShift | #3B82F6 | Low | Breathing rhythm | Coach |
| Life Simulator | #F59E0B | High | Bouncy spring | Narrator |
| BrandedBy | #EC4899 | Medium | Fluid preview | Twin |

Atlas: #10B981 — system/admin only, never user-facing.

This table will grow. The gate works the same regardless of how many rows are here.
