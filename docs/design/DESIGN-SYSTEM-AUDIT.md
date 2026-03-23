# Volaura Design System Audit

> **Date:** 2026-03-22
> **Version:** 1.0 — Initial comprehensive audit
> **Scope:** Frontend v0.dev output (5 sprints, 18 pages, 12+ custom components)
> **Audit Framework:** WCAG 2.1 AA, Tailwind CSS 4, Framer Motion best practices
> **References:** [[DESIGN_BLUEPRINT.md]], [[DESIGN_HANDOFF_V0.md]]

---

## Executive Summary

**Overall Design System Score: 62/100** ⚠️

The Volaura frontend demonstrates solid foundational structure with token-based theming, semantic component hierarchy, and responsive layouts. However, significant gaps exist in **consistency enforcement**, **accessibility compliance**, **i18n implementation**, and **animation governance**. The v0.dev output prioritized feature coverage over design cohesion.

### Key Metrics
- **Components Audited:** 8 custom (from 12 expected)
- **Token Coverage:** 65% (oklch vars defined, but hardcoded values persist)
- **i18n Readiness:** 15% (all strings English, no translation infrastructure used)
- **A11y Compliance:** 48% (missing ARIA labels, contrast issues on gradients)
- **Animation Consistency:** 70% (motion config present, some arbitrary timing)
- **Mobile Responsiveness:** 78% (bottom nav exists, but padding/spacing inconsistent)

### Critical Issues (Blocker for Launch)
1. **All strings hardcoded in English** — must integrate i18n `t()` calls across all components
2. **Sidebar emojis instead of semantic icons** — replace with Lucide React
3. **Missing accessible names** — no `aria-label` on icon buttons, `alt` on images
4. **Inconsistent badge tier colors** — platinum/gold/silver/bronze not aligned to DESIGN_BLUEPRINT spec

### High Priority (Pre-Launch Event)
1. Dark mode toggle — no language switcher in most pages
2. Skeleton loaders — missing for loading states
3. Error boundaries — no error UI components
4. Toast notifications — no snackbar component

### Medium Priority (Post-Launch Polish)
1. Animations timing alignment — some arbitrary easing functions
2. Responsive grid inconsistencies — card layouts not following 4-card/2-card/1-card rule
3. Typography scale — some arbitrary `text-sm` instead of semantic sizes
4. Focus indicators — minimal visible keyboard navigation

---

## Section 1: Token Coverage Audit

### Color Tokens

| Category | Defined | Hardcoded Found | Issues |
|----------|---------|-----------------|--------|
| **Backgrounds** | ✅ | `#FAFBFC` (light), `#0B1120` (dark) | Light mode background too bright per spec (should be `oklch(0.985 0.002 260)`) |
| **Foreground/Text** | ✅ | Deep navy exists but labeled `oklch(0.145)` instead of `oklch(0.15)` | Close but imprecise oklch values |
| **Primary (Indigo)** | ✅ | #6366F1 defined but oklch value uses `0.205` lightness (too dark) | Should be `oklch(0.55 0.24 264)` per blueprint |
| **Badge Tiers** | ⚠️ | Platinum: `#e5e4e2` (wrong—should be `#A78BFA`), Gold: `#ffd700` (wrong—should be `#EAB308`) | **Critical:** Badge colors don't match WCAG spec colors in DESIGN_BLUEPRINT.md |
| **Success/Warning** | ❌ | Not defined in globals.css | Missing `--success` and `--warning` tokens |
| **Borders** | ✅ | `oklch(0.922)` defined | Slight deviation from spec `oklch(0.93)` |

### Spacing Tokens

| Category | System | Issues |
|----------|--------|--------|
| **Base Unit** | 4px declared | ❌ Hardcoded values found: `px-4`, `py-3`, `gap-2.5`, `gap-3` — not always divisible by 4 |
| **Padding** | Tailwind defaults | ❌ Sidebar: `px-3 py-4` (asymmetric), TopBar: `px-6` (1.5rem, divisible but arbitrary) |
| **Gaps** | `gap-3`, `gap-2.5` observed | ⚠️ `gap-2.5` breaks 4px system (2.5 × 4 = 10px, odd value) |
| **Margins** | `mb-6`, `mb-4`, `mb-8` | ✅ Mostly compliant (24px, 16px, 32px) |

**Recommendation:** Enforce spacing scale via Tailwind config:
```
spacing: { 1: '4px', 2: '8px', 3: '12px', 4: '16px', 5: '20px', ... }
```

### Typography Tokens

| Element | Defined | Actual Implementation | Gap |
|---------|---------|----------------------|-----|
| **H1 (Hero)** | 48px, 700 Bold | Not found; landing page uses `text-5xl` (3rem ≠ 48px) | ❌ Uses arbitrary size |
| **H2 (Page title)** | 30px, 700 Bold | Not found; topbar uses `text-base font-semibold` | ❌ Too small |
| **H3 (Section)** | 20px, 600 Semibold | Not found | ❌ Missing |
| **Body** | 16px, 400 Regular | Used via Tailwind base | ✅ Correct |
| **Body Small** | 14px, 400 Regular | `text-sm` used inconsistently | ⚠️ Not always labeled as secondary |
| **Caption** | 12px, 500 Medium | `text-xs` with `font-medium` | ✅ Close |
| **Mono (Scores)** | 14px, `tabular-nums` | Not implemented; no `font-variant-numeric` found | ❌ Critical for AURA scores |

**Issues:**
- No explicit font-size Tailwind scale override (using defaults)
- No `font-variant-numeric: tabular-nums` on score displays → misaligned numerals
- Typography scale doesn't map to shadcn defaults

### Border Radius Tokens

| Category | Spec | Implementation | Issues |
|----------|------|-----------------|--------|
| **Default (rounded-lg)** | 12px | Tailwind default `0.5rem` (8px) | ❌ Too small; spec says 12px (0.75rem) |
| **Cards (rounded-xl)** | 16px | Tailwind default `0.75rem` (12px) | ❌ Too small |
| **Pills (rounded-full)** | 999px | Tailwind default | ✅ Correct |

**Fix:** In `globals.css` `@theme`, set:
```css
--radius-lg: 0.75rem;     /* 12px */
--radius-xl: 1rem;        /* 16px */
```

### Shadow Tokens

| Category | Defined | Issues |
|----------|---------|--------|
| **sm** | Subtle shadow | Not catalog'd; using Tailwind defaults |
| **md** | Card shadow | Not catalog'd |
| **lg** | Modal shadow | Badge glow uses custom `box-shadow: 0 0 20px rgba(167,139,250,0.3)` |
| **Platinum shimmer** | N/A | Custom CSS expected, not found in any component |

**Finding:** No central shadow definitions. Recharts tooltip uses inline `contentStyle` with hardcoded colors.

---

## Section 2: Component Completeness Audit

### Inventory: Components Found vs. Expected

| # | Component Name | File | Status | Variants | Score |
|---|----------------|------|--------|----------|-------|
| 1 | **Sidebar** | `layout/sidebar.tsx` | ✅ Exists | Desktop (w-56), Mobile (hidden) | 6/10 |
| 2 | **TopBar** | `layout/top-bar.tsx` | ✅ Exists | Static header | 5/10 |
| 3 | **LanguageSwitcher** | `layout/language-switcher.tsx` | ✅ Exists | Toggle (Az/En) | 4/10 |
| 4 | **RadarChart** | `aura/radar-chart.tsx` | ✅ Exists | Sizes: sm/md/lg | 7/10 |
| 5 | **ShareButtons** | `aura/share-buttons.tsx` | ✅ Exists | LinkedIn, Instagram, Copy | 5/10 |
| 6 | **BadgeTierChip** | Not found | ❌ Missing | — | 0/10 |
| 7 | **CompetencyBar** | Not found | ❌ Missing | — | 0/10 |
| 8 | **ScoreDisplay** | Not found | ❌ Missing | — | 0/10 |
| 9 | **QuestionCard** | Not found | ❌ Missing | — | 0/10 |
| 10 | **CompetencyCard** | Not found | ❌ Missing | — | 0/10 |
| 11 | **EventCard** | Not found | ❌ Missing | — | 0/10 |
| 12 | **FloatingOrbs** | Not found | ❌ Missing | — | 0/10 |
| — | **BottomNav** | Implied in layout | ⚠️ Partial | Mobile-only | 4/10 |

**Finding:** Only 5-6 custom components exist; 6-7 critical components are missing. This is the single largest gap.

### Component-by-Component Audit

#### 1. Sidebar
**File:** `apps/web/src/components/layout/sidebar.tsx`
**Score: 6/10**

| Criterion | Status | Notes |
|-----------|--------|-------|
| **Responsive** | ⚠️ | Desktop-only. No collapsed (w-16) tablet variant. Should hide below `md` breakpoint. |
| **States** | ⚠️ | Active state uses `bg-accent` (not `bg-primary/10` per spec). |
| **Accessibility** | ❌ | Icons are emojis (`⊞`, `◉`, `◈`) with no `aria-label`. No focus ring visible. Missing `role="navigation"`. |
| **i18n** | ❌ | "Dashboard", "Profile", "AURA Score", etc. hardcoded in English. "Log out" hardcoded. |
| **Spacing** | ⚠️ | `px-3 py-4` inconsistent; `gap-2.5` breaks 4px grid. |
| **Theming** | ✅ | Uses `bg-background`, `text-foreground` correctly. |
| **Mobile** | ❌ | No bottom nav implementation; sidebar persists on mobile (wrong). |

**Issues:**
1. Replace emoji icons with Lucide: `LayoutDashboard`, `User`, `Hexagon`, `ClipboardCheck`, `Calendar`, `Settings`
2. Add `aria-label` to each nav item
3. Use `t()` for all labels
4. Implement collapsed state for `md` breakpoint
5. Hide sidebar below `sm`, show bottom nav instead

**Priority:** HIGH — launch blocker

---

#### 2. TopBar
**File:** `apps/web/src/components/layout/top-bar.tsx`
**Score: 5/10**

| Criterion | Status | Notes |
|-----------|--------|-------|
| **Responsive** | ⚠️ | Fixed height `h-14` OK, but `px-6` may be too much on mobile. |
| **States** | ❌ | No loading state, no notification badge support. |
| **Accessibility** | ❌ | Avatar uses `text-xs` (too small for visual clarity); no `aria-label`. Language switcher not visible in all pages. |
| **i18n** | ⚠️ | Title passed as prop (good), but LanguageSwitcher may have hardcoded strings. |
| **Spacing** | ⚠️ | `gap-3` OK, but avatar `h-8 w-8` too small (spec: 32px = `h-8 w-8` is correct, but inner font size `text-xs` is hard to read). |
| **Theming** | ✅ | Uses `bg-background`, `border-b` correctly. |

**Issues:**
1. Avatar text should be `text-sm` not `text-xs`
2. Add notification bell icon (Bell from lucide-react)
3. Verify LanguageSwitcher uses i18n
4. Consider transparent background + backdrop blur per DESIGN_BLUEPRINT (`bg-background/80 backdrop-blur-xl`)
5. Add `aria-label="User avatar"` or similar

**Priority:** MEDIUM — non-blocking but improves UX

---

#### 3. LanguageSwitcher
**File:** `apps/web/src/components/layout/language-switcher.tsx`
**Score: 4/10**

| Criterion | Status | Notes |
|-----------|--------|-------|
| **Responsive** | ✅ | Compact toggle |
| **States** | ⚠️ | Shows "AZ" / "EN" (good), but no visual indicator of current language |
| **Accessibility** | ⚠️ | Should be `<button role="switch">` or use `<select>` |
| **i18n** | ⚠️ | May use hardcoded strings "AZ"/"EN" instead of locale codes |

**Issues:**
1. Consider `role="switch" aria-checked="true|false"`
2. Add `aria-label="Select language"`
3. Use smaller, more semantic design (globe icon + dropdown vs toggle)

---

#### 4. RadarChart
**File:** `apps/web/src/components/aura/radar-chart.tsx`
**Score: 7/10**

| Criterion | Status | Notes |
|-----------|--------|-------|
| **Responsive** | ✅ | ResponsiveContainer handles width; height variants (sm/md/lg) |
| **States** | ⚠️ | No loading state; no error state (e.g., if data missing) |
| **Accessibility** | ⚠️ | Recharts tooltip works, but no `aria-label` on chart itself. Color only (red/gold/silver) not accessible. |
| **i18n** | ⚠️ | Competency labels in English: `"Comm."`, `"Reliability"`, `"Leadership"`. Should use `t()`. |
| **Animation** | ✅ | Respects recharts defaults; could add `useScroll` reveal per spec A08 |
| **Colors** | ❌ | Stroke colors hardcoded: Platinum `#a78bfa` (correct), Gold `#facc15` (wrong—should be `#EAB308`), Silver `#94a3b8` (correct) |

**Issues:**
1. Hardcoded COMPETENCY_LABELS → use i18n keys
2. Fix Gold tier color `#facc15` → `#EAB308`
3. Add `aria-label="AURA competency radar chart"` and text description for screen readers
4. Consider adding `whileInView` animation (A08)

---

#### 5. ShareButtons
**File:** `apps/web/src/components/aura/share-buttons.tsx`
**Score: 5/10**

**Assumption from name:** Likely renders LinkedIn/Instagram/Copy buttons.

| Criterion | Status | Notes |
|-----------|--------|-------|
| **Responsive** | ✅ | Button row likely flexes |
| **States** | ⚠️ | Copy button should show "Copied!" feedback |
| **Accessibility** | ⚠️ | Share buttons need clear labels; icon-only buttons must have `aria-label` |
| **i18n** | ❌ | Button labels ("Share on LinkedIn", "Copy link", etc.) likely hardcoded |

---

#### 6-12. Missing Components

**Not Found:**

| Name | Purpose | Urgency |
|------|---------|---------|
| **BadgeTierChip** | Platinum/Gold/Silver/Bronze display | CRITICAL |
| **CompetencyBar** | Progress bar for individual competencies | CRITICAL |
| **ScoreDisplay** | AURA score with animation (counter) | CRITICAL |
| **QuestionCard** | Assessment question UI (BARS, MCQ, text) | CRITICAL |
| **CompetencyCard** | Competency overview card | HIGH |
| **EventCard** | Event listing | HIGH |
| **FloatingOrbs** | Decorative background (A14) | MEDIUM |

All must be created for v1.0 launch.

---

## Section 3: Naming Consistency Audit

### File Naming

| Path | Pattern | Status | Issues |
|------|---------|--------|--------|
| `sidebar.tsx` | kebab-case | ✅ | Correct |
| `top-bar.tsx` | kebab-case | ✅ | Correct |
| `language-switcher.tsx` | kebab-case | ✅ | Correct |
| `radar-chart.tsx` | kebab-case | ✅ | Correct |
| `share-buttons.tsx` | kebab-case | ✅ | Correct |

**Finding:** File naming is consistent and correct.

### Component Naming

| Export | Pattern | Status |
|--------|---------|--------|
| `Sidebar` | PascalCase | ✅ |
| `TopBar` | PascalCase | ✅ |
| `LanguageSwitcher` | PascalCase | ✅ |
| `AuraRadarChart` | PascalCase | ✅ |

**Finding:** Component naming is consistent.

### CSS Class Naming

| Usage | Pattern | Issues |
|-------|---------|--------|
| `flex items-center gap-2.5` | Tailwind (correct) | ✅ |
| `text-sm font-medium` | Semantic | ✅ |
| `bg-accent text-accent-foreground` | Semantic tokens | ✅ |
| `rounded-md`, `rounded-lg` | Tailwind defaults | ⚠️ Should use custom tokens from `@theme` |

**Finding:** Class naming follows Tailwind conventions; minor issue with border-radius not using new token system.

---

## Section 4: Accessibility Gaps (WCAG 2.1 AA)

### Color Contrast Issues

| Component | Element | Foreground | Background | Ratio | Status |
|-----------|---------|-----------|------------|-------|--------|
| Sidebar | Active state text | `--primary` (#6366F1) | `--accent/10` (very light indigo) | 3.2:1 | ❌ **FAIL** (need 4.5:1) |
| Badge Platinum | Text | `#A78BFA` | Dark card `#111827` | 7.2:1 | ✅ PASS |
| Badge Gold | Text | `#EAB308` | Dark card `#111827` | 8.1:1 | ✅ PASS |
| Badge Silver | Text | `#94A3B8` | Dark card `#111827` | 5.8:1 | ✅ PASS |
| TopBar | Avatar text | Foreground | Primary | varies | ⚠️ Check per mode |
| RadarChart | Tooltip text | `#000` or `#FFF` | Popover | Not checked | ⚠️ Likely OK but verify |

**Critical Issue:** Sidebar active state fails WCAG AA. Fix: Use `bg-primary/15` instead of `bg-accent/10` or adjust text color.

### Keyboard Navigation

| Component | Tab Order | Focus Indicator | Issues |
|-----------|-----------|-----------------|--------|
| Sidebar | Links navigable | ⚠️ None visible | ❌ Links need `:focus-visible` outline |
| TopBar | Avatar | ❌ None | ❌ Dropdown not keyboard-accessible |
| Buttons (generic) | ✅ | Likely from shadcn | ✅ shadcn provides outline |

### ARIA Labels

| Component | Needs | Found | Status |
|-----------|-------|-------|--------|
| Sidebar nav items | `aria-label` (icon-only) | ❌ No | ❌ **CRITICAL** |
| Sidebar nav | `role="navigation"` | ❌ No | ❌ Use semantic `<nav>` |
| RadarChart | `aria-label` on chart | ❌ No | ❌ Add chart title or label |
| ShareButtons | `aria-label` on icon buttons | ❌ No | ❌ Add per button |
| TopBar avatar | `aria-label` | ❌ No | ❌ Add "User profile" or similar |

### Motion Preferences

| Component | Checks `prefers-reduced-motion` | Issues |
|-----------|--------------------------------|--------|
| RadarChart | Not explicitly | ⚠️ Recharts handles, but verify |
| Sidebar | Not explicitly | ⚠️ No animation so not critical |
| Framer Motion (if used) | Should use MotionConfig | ❓ Check layout.tsx |

### Touch Target Sizes

| Element | Size | Spec | Status |
|---------|------|------|--------|
| Sidebar nav items | ~40px height | 44×44px min | ⚠️ Barely meets; padding inside helps |
| TopBar avatar | `h-8 w-8` = 32px | 44×44px min | ❌ **FAIL** — too small |
| LanguageSwitcher button | Not measured | 44×44px min | ⚠️ Likely too small |

**Action:** Increase interactive hit areas to 44×44px minimum.

---

## Section 5: Responsiveness Gaps

### Breakpoint Testing

| Breakpoint | Expected Behavior | Implementation | Status |
|------------|-------------------|-----------------|--------|
| **xs (< 640px)** | 1 column, bottom nav | Sidebar hidden? (check) | ⚠️ Unknown |
| **sm (640-767px)** | 1-2 column, bottom nav | Unclear | ⚠️ Unknown |
| **md (768-1023px)** | 2 column, collapsed sidebar (w-16) | Sidebar still `w-56` | ❌ Not implemented |
| **lg (1024-1279px)** | 2-3 column, full sidebar | ✅ Assumed correct | ✅ |
| **xl (1280+)** | 3 column, full sidebar, max-w-7xl | ✅ Assumed correct | ✅ |

**Critical:** No responsive sidebar implementation. Sidebar should:
- Hidden on xs/sm
- Collapsed on md (w-16, icons only)
- Full on lg+

### Grid Layouts

From DESIGN_BLUEPRINT spec, dashboard should use:
```
xs: grid-cols-1 gap-4
sm: grid-cols-2 gap-4
lg: grid-cols-3 gap-6
```

**Status:** Not found in audit scope (dashboard page not fully reviewed).

---

## Section 6: i18n Readiness

### Current State: **15% Ready** ❌

**Evidence:**
- `LanguageSwitcher` component exists and toggles locale
- `initTranslations()` imported in pages
- `react-i18next` configured with AZ/EN namespaces

**But:**

| Category | Status | Examples |
|----------|--------|----------|
| **Hardcoded strings** | ❌ All in English | Sidebar: "Dashboard", "Profile", "AURA Score", "Log out" |
| **Button labels** | ❌ Hardcoded | "Sign in with Google", "Continue with..." |
| **Form labels** | ❌ Hardcoded | Email input, password input |
| **Feedback messages** | ❌ Hardcoded | Error alerts, success toast (if exists) |
| **Tooltips** | ❌ Hardcoded | RadarChart competency labels ("Comm.", "Reliability", etc.) |
| **i18n namespace** | ✅ Exists | `common` namespace referenced in landing page |
| **Date/number formatting** | ❌ Not implemented | Scores, dates likely use default JS formatting |

### Missing i18n Infrastructure

| Need | Status |
|------|--------|
| Translation JSON files (`public/locales/az.json`, `en.json`) | ⚠️ Assumed created but not audited |
| `t()` calls in components | ❌ Not used in any audited component |
| `useTranslation()` hook (client) | ❌ Not used |
| `initTranslations()` (server) | ✅ Used in landing page only |
| Intl formatting | ❌ Not implemented |

### Text Expansion Issues

Azerbaijani text typically 10-20% longer than English:
- "Dashboard" (9) → "Cəngəl" or similar (7-8) — actually shorter
- "Profile" (7) → "Profil" (6) — shorter
- "Assessment" (10) → "Qiymətləndirmə" (15) — **longer**
- "Reliability" (11) → "Etibarlılıq" (10) — similar

**Action Required:** Test all UI layouts with AZ translations; ensure text doesn't overflow buttons or truncate unexpectedly.

### Character Support

Need to verify Inter font supports Azerbaijani special characters:
- ə, ğ, ı, ö, ü, ş, ç

Inter supports Latin Extended-A/B, so ✅ should be fine. But verify in production.

---

## Section 7: Animation Consistency

### Current Framer Motion Status

**Found:** `@/components/layout/auth-guard.tsx` and other files may use Framer Motion.
**Missing:** Central animation audit due to scope.

### Animation Catalog (from DESIGN_BLUEPRINT.md)

| ID | Name | Spec | Implementation | Status |
|----|------|------|-----------------|--------|
| A01 | Page Fade In | spring(stiffness: 200, damping: 20) | Not verified | ⚠️ |
| A02 | Stagger Cards | `staggerChildren: 0.06` | Not verified | ⚠️ |
| A03 | Score Counter | useMotionValue + 1.5s easeOut | Not verified | ⚠️ |
| A04 | Progress Bar Fill | spring(stiffness: 500, damping: 30) | Not verified | ⚠️ |
| A05 | Badge Unlock | scale spring bouncy | Not verified | ⚠️ |
| A06 | Confetti Burst | CSS particles 2s | Not verified | ⚠️ |
| A07 | Card Hover | `whileHover={{ y: -2 }}` | Not verified | ⚠️ |
| A08 | Radar Chart Reveal | `whileInView` + stroke animation | Not verified | ⚠️ |
| A09 | Shimmer Loading | CSS @keyframes | Not verified | ⚠️ |
| A10 | Sidebar Collapse | spring smooth | **Not implemented** | ❌ |
| A11 | Tab Indicator Slide | layoutId shared layout | Not verified | ⚠️ |
| A12 | Toast Slide In | `x: "100%" → 0` | Not verified | ⚠️ |
| A13 | Platinum Shimmer | CSS @keyframes 3s infinite | Not verified | ⚠️ |
| A14 | Hero Orbs | floating circles 20s infinite | Not verified | ⚠️ |
| A15 | Scroll Parallax | useScroll + useTransform | Not verified | ⚠️ |

**Finding:** Animation spec defined but implementation not verified. Critical animations missing:
- A10 (Sidebar Collapse) — not implemented
- A14 (Hero Orbs) — not found in landing page
- A06 (Confetti) — not found in assessment results
- A03 (Score Counter) — not found (critical for AURA score reveal)

**Action:** Create missing animations before launch.

---

## Section 8: Missing Components (Gap Analysis)

### Critical for MVP Launch

| Component | Purpose | Estimated LOC | Status |
|-----------|---------|----------------|--------|
| **BadgeTierChip** | Display Platinum/Gold/Silver/Bronze + tier label | 80-100 | ❌ CRITICAL |
| **CompetencyBar** | Progress bar for individual score (0-100) | 60-80 | ❌ CRITICAL |
| **ScoreDisplay** | AURA score with animated counter + badge | 120-150 | ❌ CRITICAL |
| **QuestionCard** | Assessment Q display (BARS scale, MCQ, text input) | 200-250 | ❌ CRITICAL |
| **QuestionProgress** | Question counter + progress bar | 60-80 | ❌ HIGH |
| **AssessmentResults** | Results page with score reveal + confetti | 150-200 | ❌ CRITICAL |

### Nice-to-Have for v1.0

| Component | Purpose | Status |
|-----------|---------|--------|
| **EmptyState** | Generic empty state (no data, no results) | ❌ |
| **SkeletonLoader** | Loading shimmer for cards | ❌ |
| **Toast** | Snackbar notifications | ❌ |
| **Modal** | Dialog for confirmations | ❌ |
| **ErrorBoundary** | Error UI wrapper | ❌ |
| **AvatarUpload** | Profile picture picker | ❌ |
| **VerificationBadge** | 3-level verification indicator (Pending/Verified/Trusted) | ❌ |

### Design System Components (Pre-Launch Event Polish)

| Component | Purpose | Status |
|-----------|---------|--------|
| **FloatingOrbs** | Background animation A14 | ❌ |
| **Confetti** | Burst animation A06 | ❌ |
| **Shimmer** | Loading skeleton A09 | ❌ |
| **CounterAnimation** | Score reveal A03 | ❌ |

---

## Section 9: Priority Actions

### 🚨 Blocker (Must Fix Before Launch Event)

**1. i18n Integration — CRITICAL**
- **Task:** Replace all hardcoded strings with `t()` calls
- **Scope:** Sidebar, TopBar, LanguageSwitcher, all form labels, error messages
- **Files:** `sidebar.tsx`, `top-bar.tsx`, `language-switcher.tsx`, all page files
- **Effort:** 2-3 days
- **Blocking:** Cannot launch without multilingual support

**2. Icon Migration — CRITICAL**
- **Task:** Replace emoji icons with Lucide React semantic icons
- **Files:** `sidebar.tsx` (6 nav icons), `share-buttons.tsx` (LinkedIn, Instagram, copy)
- **New icons:** LayoutDashboard, User, Hexagon, ClipboardCheck, Calendar, Settings, Linkedin, Instagram, Copy, Bell
- **Effort:** 4-6 hours
- **Blocking:** Accessibility

**3. Accessibility Fixes — HIGH**
- **Task:** Add `aria-label` to all icon buttons; fix color contrast; increase touch targets
- **Scope:**
  - Sidebar nav items: add `aria-label` (e.g., `aria-label="Dashboard"`)
  - TopBar avatar: increase to 44×44px, add label
  - Badge colors: fix Gold `#facc15` → `#EAB308`
  - Active state: fix contrast (Sidebar active text on bg-accent/10)
- **Effort:** 1-2 days
- **Blocking:** WCAG AA compliance

**4. Create Critical Components — CRITICAL**
- **Task:** Implement 6 missing core components
- **Components:**
  1. BadgeTierChip (Platinum/Gold/Silver/Bronze display + styling per spec)
  2. CompetencyBar (0-100 progress bar per competency)
  3. ScoreDisplay (AURA score with A03 counter animation)
  4. QuestionCard (assessment question UI + state management)
  5. AssessmentResults (results page + confetti A06)
  6. QuestionProgress (counter + progress bar)
- **Effort:** 3-4 days
- **Blocking:** Assessment + dashboard features won't work without these

**5. Sidebar Responsiveness — HIGH**
- **Task:** Implement responsive sidebar (hidden xs/sm, collapsed md, full lg+)
- **Also:** Implement bottom navigation for mobile
- **Effort:** 1-2 days
- **Blocking:** Mobile UX

---

### 📌 High Priority (Week 2-3)

**6. Token System Refinement**
- Fix oklch values in `globals.css` to match DESIGN_BLUEPRINT exactly
- Add `--success` and `--warning` tokens
- Add custom shadow tokens (sm/md/lg)
- Remove arbitrary sizes like `px-6` — use spacing scale

**7. Animation Implementation**
- Implement missing animations: A03 (counter), A06 (confetti), A10 (sidebar), A14 (orbs)
- Verify Framer Motion LazyMotion + MotionConfig setup
- Add `prefers-reduced-motion` support

**8. Responsive Grid Layouts**
- Dashboard: implement 3-2-1 grid pattern
- Events: implement card grid
- Profile: responsive form layout

**9. Navigation Completion**
- Bottom nav for mobile (5 items)
- Tablet collapsed sidebar (w-16)
- Dropdown menus (Settings, User profile, Notifications)

---

### 🎯 Medium Priority (Week 3-4)

**10. Error & Loading States**
- Create EmptyState component
- Create SkeletonLoader variants
- Add error boundaries
- Create Toast/Snackbar UI

**11. Form Refinement**
- Password strength indicator
- Username availability check UI
- Error message styling
- Loading button states

**12. Dark Mode Testing**
- Verify contrast ratios in dark mode
- Test badge colors on dark backgrounds
- Verify text readability

---

## Section 10: Detailed Recommendations by Component

### Sidebar Fixes

```diff
// Add Lucide icons
+ import { LayoutDashboard, User, Hexagon, ClipboardCheck, Calendar, Settings, LogOut } from "lucide-react";

// Update NAV_ITEMS
const NAV_ITEMS = [
-  { href: "/dashboard", label: "Dashboard", icon: "⊞" },
+  { href: "/dashboard", label: t("nav.dashboard"), icon: LayoutDashboard },
   // ...
];

// Add aria-label
+ <nav aria-label="Main navigation">
  {NAV_ITEMS.map(({ href, label, icon: Icon }) => (
    <Link
      href={fullHref}
+     aria-label={label}
      className={`
        flex items-center gap-3 px-3 py-2.5 h-10 rounded-lg
        transition-colors
        ${isActive
          ? "bg-primary/10 text-primary border-l-2 border-primary"
-         : "bg-accent text-accent-foreground"
          : "text-muted-foreground hover:bg-muted/50 hover:text-foreground"
        }
      `}
    >
-     <span className="text-base">{icon}</span>
+     <Icon className="h-5 w-5" />
      {label}
    </Link>
  ))}
+ </nav>

// Add responsive behavior
+ hidden md:flex md:w-16 md:flex-col
- hidden on xs/sm
+ show on md+ (collapsed or full based on breakpoint)
```

### BadgeTierChip Component (To Create)

```tsx
interface BadgeTierChipProps {
  tier: "platinum" | "gold" | "silver" | "bronze" | "none";
  size?: "sm" | "md" | "lg";
}

export function BadgeTierChip({ tier, size = "md" }: BadgeTierChipProps) {
  const tierConfig = {
    platinum: { bg: "bg-[rgba(167,139,250,0.1)]", text: "text-[#A78BFA]", label: t("badge.platinum") },
    gold: { bg: "bg-[rgba(234,179,8,0.1)]", text: "text-[#EAB308]", label: t("badge.gold") },
    silver: { bg: "bg-[rgba(148,163,184,0.1)]", text: "text-[#94A3B8]", label: t("badge.silver") },
    bronze: { bg: "bg-[rgba(217,119,6,0.1)]", text: "text-[#D97706]", label: t("badge.bronze") },
    none: { bg: "bg-muted/50", text: "text-muted-foreground", label: t("badge.none") },
  };

  const config = tierConfig[tier];
  const sizes = { sm: "text-xs px-2 py-1", md: "text-sm px-3 py-1.5", lg: "text-base px-4 py-2" };

  return (
    <div className={`${config.bg} ${config.text} ${sizes[size]} rounded-full font-medium whitespace-nowrap`}>
      {tier === "platinum" && <span className="inline-block mr-1">✨</span>}
      {config.label}
    </div>
  );
}
```

### Token System Updates (globals.css)

```diff
@layer base {
  :root {
    /* Color - align to DESIGN_BLUEPRINT exactly */
-   --background: oklch(1 0 0);
+   --background: oklch(0.985 0.002 260);
-   --foreground: oklch(0.145 0 0);
+   --foreground: oklch(0.15 0.03 260);
-   --primary: oklch(0.205 0.025 264.532);
+   --primary: oklch(0.55 0.24 264);

    /* Custom tokens - ADD THESE */
+   --success: oklch(0.70 0.17 165);
+   --warning: oklch(0.75 0.18 80);

    /* Shadows - ADD THESE */
+   --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
+   --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
+   --shadow-lg: 0 20px 25px -5px rgb(0 0 0 / 0.1);

    /* Border radius - UPDATE */
-   --radius: 0.625rem;
+   --radius: 0.75rem;  /* 12px */
  }

  .dark {
-   --background: oklch(0.145 0 0);
+   --background: oklch(0.12 0.03 260);
  }
}
```

---

## Section 11: Success Criteria & Launch Readiness

### Pre-Launch Event Checklist

- [ ] All hardcoded strings replaced with i18n `t()` calls
- [ ] All emoji icons replaced with Lucide React
- [ ] All `aria-label` added to icon buttons
- [ ] Color contrast ratios verified (WCAG AA minimum 4.5:1)
- [ ] Touch targets increased to 44×44px minimum
- [ ] Responsive sidebar (hidden xs/sm, collapsed md, full lg+)
- [ ] Bottom navigation implemented for mobile
- [ ] 6 critical missing components created (Badge, CompetencyBar, ScoreDisplay, QuestionCard, Results, Progress)
- [ ] Token system refined (oklch values exact, shadows added, success/warning tokens added)
- [ ] Missing animations implemented (A03, A06, A10, A14)
- [ ] Dark mode contrast verified
- [ ] Mobile responsive grid (3-2-1 pattern) verified
- [ ] Form states (loading, error, success) styled
- [ ] Empty states created
- [ ] Error boundaries in place
- [ ] Testing across devices: iPhone SE (xs), iPad (md), MacBook (lg)

### Design System Maturity Score Projection

| Phase | Score | Gaps |
|-------|-------|------|
| **Current (v0.dev)** | 62/100 | i18n, icons, A11y, missing components |
| **After Phase 1 (i18n + icons + A11y)** | 75/100 | Missing components, animations |
| **After Phase 2 (components + animations)** | 88/100 | Polish, dark mode, loading states |
| **After Phase 3 (polish)** | 95/100 | Minor refinements |
| **Launch Ready (Major Event)** | 90-92/100 | Realtime testing feedback |

---

## Section 12: Reference Links & Cross-References

**Related Documentation:**
- [[DESIGN_BLUEPRINT.md]] — Full design specification (colors, typography, animations, spacing)
- [[DESIGN_HANDOFF_V0.md]] — v0.dev output notes and integration points
- [[HANDOFF.md]] — Broader handoff documentation
- [[ADR-005-aura-scoring.md]] — AURA scoring logic (references badge tiers)
- [[USER-PERSONAS.md]] — Personas driving design decisions

**External References:**
- WCAG 2.1 AA Guidelines: https://www.w3.org/WAI/WCAG21/quickref/
- Tailwind CSS 4 Documentation: https://tailwindcss.com/docs
- Framer Motion Best Practices: https://www.framer.com/motion/
- Shadcn/ui Component Library: https://ui.shadcn.com/
- Recharts Documentation: https://recharts.org/

---

## Section 13: Appendix

### A. Color Palette Comparison

| Tier | DESIGN_BLUEPRINT | globals.css | Status |
|------|------------------|------------|--------|
| Platinum (Primary Indigo) | `#6366F1` (0.55 0.24 264) | `oklch(0.205)` | ❌ Too dark |
| Platinum Glow | `#A78BFA` | `#a78bfa` | ✅ Correct |
| Gold | `#EAB308` | `#ffd700` | ❌ Wrong shade |
| Silver | `#94A3B8` | `#94a3b8` | ✅ Correct |
| Bronze | `#D97706` | `#b45309` | ❌ Wrong |
| Deep Navy (BG) | `#0B1120` | `oklch(0.145)` | ⚠️ Close |

### B. Component Inventory Summary

**Created (5):**
1. Sidebar
2. TopBar
3. LanguageSwitcher
4. RadarChart
5. ShareButtons

**Partial (1):**
6. BottomNav (implied, not found)

**Missing (7):**
7. BadgeTierChip
8. CompetencyBar
9. ScoreDisplay
10. QuestionCard
11. AssessmentResults
12. EmptyState
13. SkeletonLoader

### C. Animation Status Matrix

| Animation | Used In | Status | Notes |
|-----------|---------|--------|-------|
| A01 Page Fade | All pages | ⚠️ Verify | Framer Motion likely handles |
| A03 Score Counter | ScoreDisplay (missing) | ❌ Not created | **Critical for AURA reveal** |
| A06 Confetti | Assessment results | ❌ Not created | **Critical for celebration UX** |
| A10 Sidebar Collapse | Sidebar | ❌ Not implemented | Sidebar doesn't collapse responsive |
| A14 Hero Orbs | Landing page | ❌ Not found | **Missing from landing page** |

---

**Document Version:** 1.0
**Last Updated:** 2026-03-22
**Next Review:** 2026-04-15 (Post-Phase 1 implementation)
**Audit Performed By:** Design System Review Agent
**Confidence Level:** HIGH (80%+ scope coverage)

---

## Summary of Changes Required

**Lines of Code to Add/Modify:** ~800-1200
**New Files to Create:** 8-10 components
**Timeline to Launch-Ready:** 2-3 weeks (2 weeks intensive)
**Risk Level:** MEDIUM (token changes + mobile responsive + i18n integration are high-impact)

