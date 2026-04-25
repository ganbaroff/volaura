# Design System Specification

## 1. Overview & Creative North Star: "The Prestigious Path"
This design system is built to bridge the gap between high-stakes professional networking and the addictive, rewarding nature of gamified growth. Our Creative North Star is **"The Prestigious Path."** 

We reject the "flat" and "boxed-in" aesthetic of traditional SaaS. Instead, we embrace a high-end editorial feel that uses **intentional asymmetry** and **tonal depth** to guide the user. The experience should feel like an elite digital club in Baku—sophisticated, dark, and aspirational. We achieve this by prioritizing breathing room (whitespace) and using light as a material, rather than lines as a container.

---

## 2. Color & Atmospheric Theory
We utilize a sophisticated Material 3-inspired palette that prioritizes dark-mode depth. 

### Core Palette
- **Primary (Indigo Focus):** `#c0c1ff` (Primary) and `#8083ff` (Container). This is our "Action" color.
- **Secondary (Aura Glow):** `#bdc2ff`. Used for accentuating progress and achievement.
- **Surface Foundations:** 
  - `Background`: `#13131b` (The Void)
  - `Surface-Container-Low`: `#1b1b23`
  - `Surface-Container-High`: `#292932`
- **AURA Tier Tokens:** 
  - `Platinum`: `#e5e4e2` | `Gold`: `#ffd700` | `Silver`: `#c0c0c0` | `Bronze`: `#cd7f32`

### The "No-Line" Rule
**Strict Mandate:** Prohibit the use of 1px solid borders for sectioning content. Boundaries must be defined solely through background color shifts. 
*   *Example:* A `surface-container-low` card sitting on a `surface` background provides all the separation needed. If the UI feels "bleary," increase the contrast between surface tiers rather than adding a stroke.

### Surface Hierarchy & Nesting
Treat the UI as stacked sheets of obsidian glass. 
1.  **Level 0 (Base):** `surface` (`#13131b`)
2.  **Level 1 (Cards/Sections):** `surface-container-low` (`#1b1b23`)
3.  **Level 2 (Active Elements/Nested Cards):** `surface-container-high` (`#292932`)

### The "Glass & Gradient" Rule
To elevate the "Duolingo" gamification to a premium level:
- Use **Glassmorphism** for floating navigation or sticky headers: `background: rgba(31, 31, 39, 0.7)` with a `backdrop-blur: 12px`.
- Use **Signature Textures**: Apply a subtle linear gradient from `primary` to `primary_container` on main CTA buttons to provide a "lit from within" glow.

---

## 3. Typography: Editorial Authority
We pair **Plus Jakarta Sans** (Display) with **Inter** (Body) to balance personality with high-readability.

| Token | Font | Size | Weight | Usage |
| :--- | :--- | :--- | :--- | :--- |
| `display-lg` | Plus Jakarta Sans | 3.5rem | 700 | Hero headers, Achievement numbers |
| `headline-md` | Plus Jakarta Sans | 1.75rem | 600 | Page titles, Section headers |
| `title-md` | Inter | 1.125rem | 600 | Card titles, Navigation items |
| `body-md` | Inter | 0.875rem | 400 | Primary reading text |
| `label-sm` | Inter | 0.6875rem | 500 | Metadata, Overlines, Micro-copy |

**Editorial Note:** Use `display-lg` for counting animations (e.g., verified impact, completed sessions, earned crystals) to create a sense of monumental achievement.

---

## 4. Elevation & Depth: Tonal Layering
We do not use drop shadows to create "pop." We use light and layering.

*   **The Layering Principle:** Depth is achieved by stacking. Place a `surface-container-highest` element over a `surface-container-low` to create an "inner glow" effect.
*   **Ambient Shadows:** If an element must float (like a Modal), use a tinted shadow: `box-shadow: 0px 20px 40px rgba(0, 0, 0, 0.4)`. The shadow must never be pure black; it should feel like the background is occluded.
*   **The "Ghost Border" Fallback:** For input fields or essential accessibility, use the `outline_variant` token at **15% opacity**. It should be felt, not seen.

---

## 5. Components: Custom Professionalism

### Buttons & CTAs
- **Primary:** Gradient from `primary` to `primary_container`. Border radius: `md` (0.75rem).
- **Secondary:** Surface-tinted. No border. Use `on_secondary_container` text color.
- **States:** On hover, use a Framer Motion `whileHover: { scale: 1.02 }` and increase the saturation of the gradient.

### Cards & Lists
- **The Forbid Rule:** No divider lines between list items. Use `spacing-6` (1.5rem) to separate content blocks or subtle shifts in surface color.
- **Aura Tier Cards:** Cards representing user tiers (Gold, Platinum) should use a subtle 10% opacity background of the tier color and a `title-lg` header.

### Input Fields
- Avoid "box" looks. Use `surface-container-lowest` for the field background. On focus, animate a 1px `primary` glow using a Framer Motion layout transition rather than a standard CSS outline.

### Achievement Pulse (The "Aura" Component)
- For verified talents, use a Framer Motion `animate={{ scale: [1, 1.05, 1] }}` on a subtle radial gradient behind their profile picture to represent their "Aura."

---

## 6. Do’s and Don’ts

### Do
- **Do** use `display-lg` for "Big Numbers"—verified impact, progress scores, and talent rankings.
- **Do** utilize `xl` (1.5rem) corner radius for large hero sections to give a friendly, "Duolingo-like" softness.
- **Do** use asymmetrical layouts (e.g., a left-aligned headline with a right-aligned stats card that slightly overlaps the section below it).

### Don't
- **Don't** use `#000000` for backgrounds. It kills the depth. Stick to `surface` (`#13131b`).
- **Don't** use standard "LinkedIn Blue." Our Indigo is our signature; it is warmer, more modern, and more aspirational.
- **Don't** use 1px dividers. If you need to separate content, use a `surface-variant` block or simply more vertical space.

---

## 7. Motion & Interaction (Framer Motion)
Interaction is the heartbeat of this system. 

1.  **Entrance:** Staggered fade-ins with a `y: 20` offset. `transition: { type: "spring", stiffness: 100 }`.
2.  **The "Count Up":** Any numerical talent metric must animate from 0 to the final value over 1.5 seconds.
3.  **Haptic Feedback (Mobile):** Subtle scale-down (0.98) on tap for all buttons to simulate a physical "press" into the glass layers.
