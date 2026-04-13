# Ecosystem Redesign — Mega Plan

**Owner:** Cowork (design + components) | Atlas (integration + deploy)
**Source:** MEGAPLAN-SESSION-95-AUTONOMOUS.md Track 2 + ecosystem-redesign-analysis.md
**Scope:** 124 components, 43 pages, 5 products, 5 Constitution Laws

---

## PHASE 1: FOUNDATION (Tokens + Core Components + Energy System)

**Goal:** Every component in the ecosystem can use the design system. No more hardcoded colors, no more inconsistent spacing. Energy mode works globally.

### 1.1 Token System ✅ DONE
- [x] 3-tier tokens in globals.css (primitives → semantic → product)
- [x] Product accent colors: VOLAURA #7C5CFC, MindShift #3B82F6, Life Sim #F59E0B, BrandedBy #EC4899, ZEUS #10B981
- [x] Spacing scale (xs through 2xl)
- [x] Shadow/elevation tokens (sm/md/lg/glow)
- [x] Z-index scale (base through bottomnav)
- [x] Animation duration tokens (instant/fast/normal/slow/max=800ms)
- [x] Spring physics tokens (damping=14, stiffness=100)
- [x] Success color tokens (colorblind-safe green)
- [x] Liquid Glass utility class (CSS-only, backdrop-filter fallback)

### 1.2 Energy System ✅ DONE
- [x] CSS variables via `[data-energy]` attribute (spacing, density, animation, min-target)
- [x] `useEnergyMode()` hook (localStorage + Supabase stub)
- [x] Energy Picker: default + compact variants
- [x] `[data-energy="low"]` disables all animations
- [x] Energy-responsive utilities: .energy-gap, .energy-p, .energy-target

### 1.3 Navigation ✅ DONE
- [x] Bottom Tab Bar (Discord-style 5-product switcher)
- [x] Product accent on active tab
- [x] Inline SVG icons (0KB extra dependency)
- [x] glass-nav background

### 1.4 Core Components ✅ DONE
- [x] **Button System** — primary (gradient), secondary, ghost, destructive (purple), product accent, loading state
- [x] **Card System** — default/elevated/glass variants, energy-responsive padding
- [x] **Toast/Notification** — purple errors, amber warnings, top-center, auto-dismiss 5s
- [x] **Empty State** — shame-free language templates (Law 3)
- [x] **Avatar** — badge tier glows (bronze/silver/gold/platinum), initials fallback, CSS particles
- [x] **Liquid Glass Radar** — identity-first hero component wrapping AuraRadarChart
- [x] **Assessment Card** — energy-responsive question display with spring physics
- [x] **Product Placeholder** — "Coming soon" page for unreleased ecosystem products

---

## PHASE 2: SCREENS (Dashboard + Assessment + Profile + AURA + Landing)

**Goal:** Every user-facing page uses the new design system. Energy mode affects every screen. One primary CTA per screen enforced.

### 2.1 Dashboard Page ✅ DONE
- [x] BottomTabBar replaces old BottomNav in layout
- [x] EnergyInit component sets data-energy on mount
- [x] Toaster added to layout
- [x] TopBar with Avatar + compact EnergyPicker
- [x] Energy-responsive: tribe card + feed cards hidden in low energy mode
- [x] Error styling uses purple tokens (Law 1)

### 2.2 Assessment Flow ✅ DONE
- [x] QuestionCard: spring physics (damping=14, stiffness=100) replaces easeInOut
- [x] QuestionCard: energy-responsive padding (energy-p)
- [x] Assessment page: TopBar added, primary gradient button
- [x] Error styling uses purple tokens (Law 1)

### 2.3 AURA Results Page ✅ DONE
- [x] LiquidGlassRadar replaces old radar section (identity-first: name → score → tier → radar)
- [x] Retake Assessment CTA embedded in radar (Law 5: single CTA)
- [x] Shame-free growth hint in radar component (Law 3)

### 2.4 Profile Pages ✅ DONE
- [x] ProfileHeader: Avatar component replaces inline avatar div (badge tier glows)
- [x] Section animations: spring physics (damping=14, stiffness=100)

### 2.5 Landing Page ✅ DONE
- [x] Features grid: 3 cards (was 6 — ADHD reduction)
- [x] Spring physics on card entrance animations
- [x] Hero: font-headline, spring animation, gradient CTA button
- [x] Energy-responsive card padding

### 2.6 Settings Page ✅ DONE
- [x] Full-size EnergyPicker added (default variant)
- [x] Energy mode description text
- [x] font-headline on section headers
- [x] Error styling: purple tokens (Law 1)

### 2.7 Auth Pages ✅ DONE
- [x] Login: purple error styling, font-headline, gradient CTA button
- [x] Signup: purple error styling

### 2.8 Product Pages ✅ DONE
- [x] ProductPlaceholder component: reusable, product accent colors, liquid-glass badge
- [x] MindShift: /mindshift route, blue accent, brain icon
- [x] Life Simulator: /life route, amber accent, game icon
- [x] ZEUS: /zeus route, green accent, bolt icon
- [x] All accessible via BottomTabBar navigation

---

## PHASE 3: POLISH (Audits + Testing + Verification)

**Goal:** Every component and page passes Constitution, ADHD audit, and accessibility checks. Production-ready.

### 3.1 Constitution Audit (5 Laws) ✅ DONE
- [x] Law 1: `--color-destructive` mapped to `--color-error-container` (purple) — all destructive= usages automatically purple
- [x] Law 1: toast system uses error-container/warning-container tokens
- [x] Law 2: energy system fully wired (CSS variables, useEnergyMode hook, data-energy attribute, EnergyInit component)
- [x] Law 2: dashboard hides non-essential widgets in low energy mode
- [x] Law 3: EmptyState component enforces shame-free language patterns
- [x] Law 4: all animations ≤800ms, spring physics (damping=14, stiffness=100), prefers-reduced-motion in globals.css
- [x] Law 5: LiquidGlassRadar has single CTA, assessment page has single primary CTA

### 3.2 ADHD Audit (26 rules from adhd-first-ux-research.md)
- [ ] One action per screen — verified in Law 5
- [ ] Floor mechanic <2min — measure time from login to first assessment question
- [ ] No infinite scroll — grep for "InfiniteScroll", "onScroll", "IntersectionObserver"
- [ ] No streak punishment — review MindShift copy when built
- [ ] Clear structure — every page follows consistent layout grid
- [ ] Variable reward magnitude — crystal earn amounts randomized within range
- [ ] Immediate feedback — every interactive element has :active/:focus state
- [ ] Self-aware humor — spot-check microcopy
- [ ] Max 3-5 items visible per section — audit all list renders

### 3.3 Accessibility (WCAG 2.1 AA)
- [ ] Color contrast: all text meets 4.5:1 ratio against surface tokens
- [ ] Focus indicators: visible focus ring on all interactive elements
- [ ] Screen reader: all images have alt text, all icons have aria-label
- [ ] Keyboard navigation: entire app navigable without mouse
- [ ] Landmarks: header, main, nav, footer on every page
- [ ] Form labels: every input has associated label
- [ ] Error announcements: aria-live regions for validation messages
- [ ] Radar chart: sr-only data table (already exists ✅)

### 3.4 Cross-Product Consistency
- [ ] Bottom tab renders consistently across all product pages
- [ ] Product accent color changes correctly when switching tabs
- [ ] Energy mode persists across page navigation
- [ ] Liquid glass renders consistently on all backgrounds
- [ ] Avatar component shows correct tier across all placements

### 3.5 Responsive Testing
- [ ] 375px (iPhone SE) — primary breakpoint, everything must work
- [ ] 390px (iPhone 14) — standard
- [ ] 768px (iPad) — two-column where appropriate
- [ ] 1024px+ (desktop) — centered layout, max-width containers

### 3.6 Performance
- [ ] Lighthouse score ≥90 on landing page
- [ ] First Contentful Paint <1.5s
- [ ] No layout shift from energy mode toggle
- [ ] Total JS bundle: track and minimize
- [ ] All images: next/image with proper sizing

---

## EXECUTION ORDER

```
NOW → Phase 1.4 (remaining core components)
  → Phase 2.1 (Dashboard — highest visibility)
  → Phase 2.2 (Assessment flow — core product value)
  → Phase 2.3 (AURA results — Liquid Glass showcase)
  → Phase 2.4 (Profile — identity-first)
  → Phase 2.5 (Landing — first impression)
  → Phase 2.6 (Settings — energy picker home)
  → Phase 2.7 (Auth — clean and minimal)
  → Phase 2.8 (Placeholders — quick wins)
  → Phase 3 (Full audit sweep)
```

**Estimated effort:** ~50 component files to create/modify, ~15 page files to update
**No CEO involvement needed.** All decisions are within Constitution + research + resolved questions.
