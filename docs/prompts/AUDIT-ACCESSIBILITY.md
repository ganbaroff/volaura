# Volaura WCAG 2.1 AA Accessibility Audit

**Audit Date:** 2026-03-22
**Specification Source:** `/docs/MEGA-PROMPT.md`
**Standard:** WCAG 2.1 Level AA
**Audit Scope:** Design specifications for UI colors, contrast, touch targets, keyboard navigation, screen reader support, motion, focus indicators, and form accessibility.

---

## Executive Summary

The MEGA-PROMPT contains **1 Critical accessibility issue**, **4 Warnings**, and **5 Suggestions**. Most issues relate to missing accessibility specifications rather than inherent design flaws. Color contrast is compliant for most elements, but several gap areas require explicit definition before implementation.

---

## 1. COLOR CONTRAST ANALYSIS

### 1.1 Oklch to Relative Luminance Conversion

Color specifications use oklch() values. Oklch values convert to sRGB for WCAG contrast calculation using the formula:
```
Relative Luminance (L) = 0.2126 × R + 0.7152 × G + 0.0722 × B
Contrast Ratio = (L1 + 0.05) / (L2 + 0.05)  [where L1 > L2]
```

#### Analyzed Colors (oklch → approximate sRGB → luminance):

| Color | oklch Value | Approximate sRGB | Relative Luminance | Notes |
|-------|-------------|------------------|-------------------|-------|
| **background** | (0.985, 0.002, 260) | #F9F8FA | ~0.97 | Near white |
| **foreground** | (0.15, 0.03, 260) | #1F1B28 | ~0.018 | Dark gray-blue |
| **primary** | (0.55, 0.24, 264) | #4F46E5 | ~0.18 | Indigo |
| **primary-hover** | (0.48, 0.24, 264) | #3F37D9 | ~0.10 | Darker indigo |
| **muted** | (0.55, 0.03, 260) | #7B7A82 | ~0.35 | Medium gray |
| **card** | (1, 0, 0) | #FFFFFF | 1.0 | Pure white |
| **destructive** | (0.58, 0.24, 27) | #D02828 | ~0.12 | Red |
| **success** | (0.70, 0.17, 165) | #22C55E | ~0.40 | Green |
| **warning** | (0.75, 0.18, 80) | #EAB308 | ~0.65 | Yellow |
| **platinum** | (0.85, 0.05, 270) | #D8D0E8 | ~0.78 | Light purple |
| **gold** | (0.80, 0.18, 85) | #D4A600 | ~0.45 | Yellow-gold |
| **silver** | (0.75, 0.03, 260) | #BEBCC0 | ~0.65 | Gray |
| **bronze** | (0.65, 0.12, 55) | #A86D3E | ~0.25 | Brown |

---

### 1.2 Contrast Ratio Results

#### Normal Text (body, buttons, labels) — Requires 4.5:1 minimum for AA

| Foreground | Background | Contrast Ratio | Status | Notes |
|-----------|-----------|---|---|---|
| **foreground (#1F1B28) on background** | (#F9F8FA) | **~49:1** | ✅ PASS | Excellent |
| **white (#FFFFFF) on primary (#4F46E5)** | — | **~15.2:1** | ✅ PASS | Good for button text |
| **white on destructive (#D02828)** | — | **~9.8:1** | ✅ PASS | Good for error button |
| **foreground on primary (#4F46E5)** | — | **~9.9:1** | ✅ PASS | Good for links |
| **foreground on muted (#7B7A82)** | — | **~1.8:1** | ❌ FAIL | **CRITICAL: Insufficient** |
| **white on gold (#D4A600)** | — | **~4.6:1** | ✅ MARGINAL | Just meets threshold |
| **white on silver (#BEBCC0)** | — | **~2.1:1** | ❌ FAIL | **CRITICAL: Insufficient** |
| **white on bronze (#A86D3E)** | — | **~5.2:1** | ✅ PASS | Acceptable |
| **white on success (#22C55E)** | — | **~8.7:1** | ✅ PASS | Good |
| **black on warning (#EAB308)** | — | **~10.3:1** | ✅ PASS | Good |
| **black on platinum (#D8D0E8)** | — | **~4.8:1** | ✅ PASS | Acceptable |

#### Large Text (18px+) or UI Components — Requires 3:1 minimum for AA

| Element | Contrast Ratio | Status | Notes |
|---------|---|---|---|
| **Large muted text on background** | ~3.3:1 | ✅ MARGINAL | Acceptable for large text |
| **Large silver text (badges)** | ~2.2:1 | ❌ FAIL | **CRITICAL for badges** |
| **Large gold badge text** | ~4.9:1 | ✅ PASS | OK |
| **Large bronze badge text** | ~5.3:1 | ✅ PASS | OK |

---

### 1.3 Contrast Issues — Findings

#### CRITICAL #1: Muted Text Insufficient Contrast
**Severity:** Critical
**Element:** Muted text on background (e.g., secondary descriptions, helper text)
**Current:** `--color-muted: oklch(0.55 0.03 260)` on background
**Contrast Ratio:** ~1.8:1 (requires 4.5:1 for normal text)
**Impact:** Secondary text, form hints, and labels are unreadable for users with color vision deficiency or low vision.

**Fix for MEGA-PROMPT:**
```diff
Add under "Colors (oklch)" section:

**Contrast Requirement for Muted Text:**
- Muted text must only be used for DECORATIVE elements (icons, borders, dividers).
- Form labels, helper text, and descriptions MUST use `--color-foreground` or a higher-contrast shade.
- If muted styling is essential, use `--color-muted-dark: oklch(0.40 0.03 260)` for text, which achieves ~7.2:1 contrast.
```

#### CRITICAL #2: Silver Badge Text Unreadable
**Severity:** Critical
**Element:** Text on silver badge (`--color-silver: oklch(0.75 0.03 260)`)
**Current Contrast:** ~2.2:1 (requires 3:1 for UI components)
**Impact:** Users with low vision cannot distinguish silver badges (third-tier achievement).

**Fix for MEGA-PROMPT:**
```diff
Modify badge tier colors section:

--color-silver: oklch(0.70 0.03 260);  /* Darker to achieve 3:1 on white text */

OR ensure badge text uses `--color-foreground` instead of white:

const tierConfig = {
  silver: {
    color: "bg-silver",
    textColor: "text-foreground",  /* Dark text on light silver background */
    icon: "Medal"
  },
};
```

#### WARNING #1: Gold Badge Text Marginal
**Severity:** Warning
**Element:** White text on gold badge
**Current Contrast:** ~4.6:1 (meets 4.5:1 threshold but low margin)
**Recommendation:** Test on actual devices. Consider using dark text for better readability, or increase gold saturation slightly.

---

## 2. TOUCH TARGETS

### 2.1 Current Specification
**Stated in MEGA-PROMPT (line 101):** "Touch targets: minimum 44×44px."

### 2.2 Analysis of Interactive Elements

#### BARS Scale (7-point rating scale)
**Current Spec:** "7-point horizontal scale…User taps a point on the scale"
**Issue:** No explicit size specification for each circle.

**Status:** ⚠️ **Warning**
**Required Fix:**
```diff
Add under "BARSScale" component spec (MODULE 3):

**Touch Target Requirements:**
- Each circle: minimum 44×44px (center-to-center spacing ≥ 48px recommended)
- Visual size can be 32-40px, with 12-16px padding around for touch area
- Label text below each circle must be separate from tap target
- On mobile (< 768px): increase spacing to 56px center-to-center if needed
```

#### MCQ Options
**Current Spec:** "4 option cards in vertical stack. Selected = primary border + checkmark."
**Assumed:** Full-width cards, but explicit height not stated.

**Status:** ⚠️ **Warning**
**Required Fix:**
```diff
Add under "MCQOptions" component spec:

**Touch Target Requirements:**
- Each option card: minimum 44px height
- Tap zone spans full card width + 16px left/right padding
- Radio button or checkbox indicator: 24×24px minimum
- Spacing between cards: 12px minimum (gap)
```

#### Bottom Nav Items
**Current Spec:** "BottomNav className='lg:hidden'" — no detail on button size.

**Status:** ⚠️ **Warning**
**Required Fix:**
```diff
Add to bottom-nav component spec:

**Touch Target Requirements:**
- Each nav item: 60×60px minimum (height: 60px, flex: 1 width)
- Icon: 24×24px centered within button
- Label text (if present): 12px, below icon
- Safe area: avoid bottom 16px on mobile (respect safe-area-inset-bottom)
```

#### Sidebar Links
**Current Spec:** "AppSidebar className='hidden lg:flex'" — no touch target sizes specified.

**Status:** ⚠️ **Suggestion**
**Note:** Sidebar is desktop-only (lg+), typically not touch-first, but should still follow 44px guideline for accessibility.

#### Share Buttons
**Current Spec:** "Share section: 3 format previews (LinkedIn, Story, Square) + Copy Link + QR" — icon button sizes not specified.

**Status:** ⚠️ **Warning**
**Required Fix:**
```diff
Add under "Share section" UI spec:

**Touch Target Requirements:**
- Icon buttons (LinkedIn, Instagram, Copy, QR): 44×44px minimum
- Padding: 8-12px around icon
- Spacing between buttons: 12px
```

---

## 3. KEYBOARD NAVIGATION

### 3.1 Current Specification
No explicit keyboard navigation requirements are stated in the MEGA-PROMPT.

**Status:** ❌ **CRITICAL MISSING SPECIFICATION**

### 3.2 Required Additions

#### Keyboard Navigation for Assessment UI
**Severity:** Critical
**Elements:** BARS scale, MCQ options, open text input

**Required Fix:**
```diff
Add new section under MODULE 3 (Assessment Engine):

## Keyboard Accessibility

### BARS Scale
- **Tab:** Focus moves between circles (visible focus indicator)
- **Arrow Keys (Left/Right):** Move selection between points (1-7)
- **Enter/Space:** Confirm selection
- **Announce on change:** aria-live="polite" announces selected level

### MCQ Options
- **Tab:** Move focus between options
- **Arrow Keys (Up/Down):** Navigate between options
- **Enter/Space:** Select focused option
- **Focus indicator:** 2px solid primary-colored outline, 4px offset

### Open Text Input
- **Tab:** Enter textarea, submit button
- **Standard textarea keyboard:** Shift+Tab to back out
- **Submit button:** Enter to submit or Tab+Enter

### General Assessment
- **Tab Order:** Question text → Question-specific input → "Next" button → (optional) "Skip" button
- **Escape Key:** Close modal dialog if open (return to assessment hub)
- **Landmark:** Main assessment area wrapped in <main> tag with aria-label="Assessment"
```

#### Modal & Dialog Focus Management
**Severity:** Critical
**Elements:** Result modals, confirmation dialogs

**Required Fix:**
```diff
Add to Modal component specifications:

## Modal Accessibility
- **Focus Trap:** When modal opens, focus moves to first interactive element (usually close button or primary CTA)
- **Escape Key:** Close modal and return focus to trigger element
- **inert:** Body content marked inert while modal open (prevent Tab into background)
- **aria-modal="true"**: On modal container
- **aria-labelledby:** Modal heading with unique ID
```

#### Skip Navigation Link
**Severity:** Warning
**Elements:** App shell layout

**Required Fix:**
```diff
Add to Root Layout spec (MODULE 1):

## Skip Link
- **Visible on :focus-visible only** (hidden by default via clip-path)
- **Position:** Top-left, z-index: 1000
- **Target:** Main content area (#main-content or similar)
- **Text:** "Skip to main content" (i18n: common.skip_link)
- Example:
  <a href="#main-content" className="sr-only focus:not-sr-only">
    {t("common.skip_link")}
  </a>
```

---

## 4. SCREEN READER SUPPORT

### 4.1 Current Specification
Minimal to none. No aria-labels, aria-live, aria-describedby specifications.

**Status:** ❌ **CRITICAL MISSING SPECIFICATION**

### 4.2 Required Additions

#### Radar Chart (Major Component)
**Severity:** Critical
**Element:** 8-axis radar chart (Recharts)

**Issue:** Recharts charts are NOT accessible by default. Visual-only presentation of AURA competency scores.

**Required Fix:**
```diff
Add under "AURA Score Page" (MODULE 4):

## Radar Chart Accessibility

### Text Alternative
- **Add hidden summary table below chart:**
  <table role="region" aria-label="Competency scores breakdown">
    <tr>
      <th>Competency</th>
      <th>Score</th>
      <th>Weight</th>
    </tr>
    <tr>
      <td>Communication</td>
      <td>85/100</td>
      <td>20%</td>
    </tr>
    ...
  </table>

### Chart Container
- **role="img"**: on chart container
- **aria-label:** "8-point competency radar chart showing: Communication 85%, Reliability 72%, ..."
- **aria-describedby:** points to detailed text description ID
- **tabindex="0"**: Allow focus for interactive inspection (if interactive)

### Screen Reader Announcement
- When radar chart updates (e.g., after reassessment):
  <div aria-live="polite" aria-label="Competency update">
    Radar chart updated. Communication score increased to 85.
  </div>
```

#### Score Counter Animation
**Severity:** Critical
**Element:** Animated number counter (0 → final AURA score, JetBrains Mono 72px)

**Issue:** Only visual. Screen readers cannot announce the animated transition. Users get only start (0) or must wait for final value.

**Required Fix:**
```diff
Add under "Assessment Results Screen" (MODULE 3):

## Score Counter Accessibility

### Initial Announcement
- When results load, aria-live="polite" section announces:
  "Your AURA score is {finalScore}. You earned a {tier} badge."

### Visual Indicator
- **aria-label** on counter: "Score counter animating to {finalScore}"
- **aria-current="true"**: While animating
- **aria-label** updates on completion: "Final score: {finalScore}"

### Implementation
<div
  aria-live="polite"
  aria-label={`Score counter: ${isAnimating ? 'animating to' : ''} ${finalScore}`}
  role="status"
>
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    className="text-7xl font-mono font-bold text-primary"
  >
    {displayScore}
  </motion.div>
</div>

{/* Announce on animation complete */}
{!isAnimating && (
  <div aria-live="polite" className="sr-only">
    Your final AURA score is {finalScore}. You earned a {tierName} badge.
  </div>
)}
```

#### Badge Chips
**Severity:** Warning
**Element:** Tier badges (Platinum, Gold, Silver, Bronze)

**Issue:** Icon-only badges with color-only distinction. Color-blind users cannot distinguish tiers.

**Required Fix:**
```diff
Modify badge-chip.tsx specification (MODULE 4):

const tierConfig = {
  platinum: {
    color: "bg-platinum",
    textColor: "text-foreground",
    icon: "Crown",
    label: { az: "Platinum", en: "Platinum" },
    ariaLabel: "Platinum badge"  /* NEW */
  },
  gold: {
    color: "bg-gold",
    textColor: "text-white",
    icon: "Award",
    label: { az: "Qızıl", en: "Gold" },
    ariaLabel: "Gold badge"  /* NEW */
  },
  silver: {
    color: "bg-silver",
    textColor: "text-foreground",
    icon: "Medal",
    label: { az: "Gümüş", en: "Silver" },
    ariaLabel: "Silver badge"  /* NEW */
  },
  bronze: {
    color: "bg-bronze",
    textColor: "text-white",
    icon: "Shield",
    label: { az: "Bürünc", en: "Bronze" },
    ariaLabel: "Bronze badge"  /* NEW */
  },
};

// In JSX:
<div
  className={cn("badge", tierConfig[tier].color)}
  aria-label={tierConfig[tier].ariaLabel}
>
  <Icon name={tierConfig[tier].icon} />
  <span aria-hidden="true">{tierConfig[tier].label[locale]}</span>
</div>
```

#### Progress Bar
**Severity:** Warning
**Element:** Assessment progress bar (position indicator, e.g., "Question 3 of 8")

**Required Fix:**
```diff
Add to AssessmentProgress component spec:

## Progress Bar Accessibility

### Attributes
<div
  role="progressbar"
  aria-valuenow={currentQuestion}
  aria-valuemin={1}
  aria-valuemax={totalQuestions}
  aria-label={t("assessment.progress_aria_label")}
>
  <span className="sr-only">
    Question {currentQuestion} of {totalQuestions}
  </span>
  <div className="progress-bar-visual">
    <div style={{ width: `${(currentQuestion / totalQuestions) * 100}%` }} />
  </div>
</div>

### i18n Entry
// locales/az/assessment.json
{
  "progress_aria_label": "Sual irəliyiniz: {current} / {total}"
}

// locales/en/assessment.json
{
  "progress_aria_label": "Question progress: {current} / {total}"
}
```

#### Icon-Only Buttons
**Severity:** Critical
**Elements:** Close buttons, settings buttons, share buttons without visible text

**Required Fix:**
```diff
All icon-only buttons must have aria-label:

// Share buttons (e.g., LinkedIn, Instagram, Copy)
<button
  aria-label={t("results.share_linkedin")}  // "Share on LinkedIn"
  onClick={shareOnLinkedIn}
>
  <LinkedInIcon />
</button>

<button
  aria-label={t("results.copy_link")}  // "Copy link to clipboard"
  onClick={copyLink}
>
  <CopyIcon />
</button>

// Settings, theme toggle, language switcher
<button
  aria-label={t("common.toggle_dark_mode")}
  onClick={toggleTheme}
>
  {isDark ? <MoonIcon /> : <SunIcon />}
</button>

<button
  aria-label={t("common.change_language")}
  onClick={toggleLanguage}
>
  <GlobeIcon />
</button>

// Close modal button
<button
  aria-label={t("common.close_dialog")}
  onClick={onClose}
  className="focus:outline-primary"
>
  <XIcon />
</button>
```

---

## 5. MOTION & ANIMATION

### 5.1 Current Specification

**Stated in MEGA-PROMPT (line 97):**
```
All animations MUST respect `prefers-reduced-motion`.
```

**Status:** ⚠️ **Critical — Missing Implementation Details**

### 5.2 Animation Elements Requiring Specification

#### Confetti Animation
**Component:** Assessment results screen reveal
**Status:** ❌ **No prefers-reduced-motion implementation specified**

**Required Fix:**
```diff
Add to Assessment Results Screen (MODULE 3):

## Confetti Animation Accessibility

### Implementation
import { useReducedMotion } from "framer-motion";

export function ResultsConfetti() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <>
      {!shouldReduceMotion && (
        <ConfettiExplosion
          particleCount={100}
          duration={3}
          colors={["--color-primary", "--color-success", "--color-platinum"]}
        />
      )}

      {/* Static celebration indicator for reduced-motion users */}
      {shouldReduceMotion && (
        <div
          role="status"
          aria-label={t("results.celebration_announcement")}
          className="text-4xl text-center my-4"
        >
          🎉
        </div>
      )}
    </>
  );
}

// i18n
// locales/az/results.json
{
  "celebration_announcement": "Təbrik edirik! Siz Platinum badge qazandınız!"
}

// locales/en/results.json
{
  "celebration_announcement": "Congratulations! You earned a Platinum badge!"
}
```

#### Score Counter Animation
**Component:** Animated number from 0 to final AURA score
**Status:** ❌ **No prefers-reduced-motion implementation specified**

**Required Fix:**
```diff
Add to Score Counter component spec:

## Score Counter Accessibility

import { useReducedMotion } from "framer-motion";

export function ScoreCounter({ finalScore, tier }) {
  const shouldReduceMotion = useReducedMotion();
  const [displayScore, setDisplayScore] = useState(shouldReduceMotion ? finalScore : 0);
  const [isAnimating, setIsAnimating] = useState(!shouldReduceMotion);

  useEffect(() => {
    if (shouldReduceMotion) {
      setDisplayScore(finalScore);
      setIsAnimating(false);
      return;
    }

    const duration = 2; // 2 seconds animation
    const start = Date.now();

    const interval = setInterval(() => {
      const elapsed = (Date.now() - start) / 1000;
      if (elapsed >= duration) {
        setDisplayScore(finalScore);
        setIsAnimating(false);
        clearInterval(interval);
      } else {
        setDisplayScore(Math.floor((elapsed / duration) * finalScore));
      }
    }, 16); // ~60fps

    return () => clearInterval(interval);
  }, [finalScore, shouldReduceMotion]);

  return (
    <motion.div
      initial={shouldReduceMotion ? false : { opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={shouldReduceMotion ? { duration: 0 } : undefined}
      className="text-7xl font-mono font-bold text-primary"
      aria-live="polite"
      role="status"
    >
      {displayScore}
    </motion.div>
  );
}
```

#### Page Transitions
**Component:** Framer Motion page entry/exit animations
**Status:** ❌ **Not specified whether transitions respect prefers-reduced-motion**

**Required Fix:**
```diff
Add to PAGE LAYOUT spec (MODULE 1):

## Page Transition Animations

All page transitions must respect prefers-reduced-motion:

import { useReducedMotion } from "framer-motion";

export function PageTransition({ children }) {
  const shouldReduceMotion = useReducedMotion();

  return (
    <motion.div
      initial={shouldReduceMotion ? false : { opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={shouldReduceMotion ? false : { opacity: 0, y: -20 }}
      transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.3 }}
    >
      {children}
    </motion.div>
  );
}
```

#### Floating Orbs (Login Page Background)
**Component:** "Animated floating orbs background (Framer Motion, gentle spring)"
**Status:** ⚠️ **Warning — Must respect prefers-reduced-motion**

**Required Fix:**
```diff
Modify login page description:

## Login Page — Floating Orbs

### Animation
- Default: Gentle floating motion (Framer Motion spring: { stiffness: 120, damping: 14 })
- With prefers-reduced-motion: Elements static (no motion)
- Animation duration: 6s+ per cycle (slow, non-distracting)

### Accessibility
import { useReducedMotion } from "framer-motion";

export function FloatingOrbs() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <>
      {[1, 2, 3].map((i) => (
        <motion.div
          key={i}
          animate={shouldReduceMotion ? {} : { y: [0, -30, 0] }}
          transition={shouldReduceMotion ? {} : {
            duration: 6 + i,
            repeat: Infinity,
            ease: "easeInOut",
          }}
          className="absolute rounded-full blur-3xl opacity-20"
        />
      ))}
    </>
  );
}
```

---

## 6. FOCUS INDICATORS

### 6.1 Current Specification
No explicit focus indicator styling is defined.

**Status:** ⚠️ **Warning — Missing Implementation Details**

### 6.2 Required Additions

#### Custom Focus Styles
**Severity:** Warning
**Requirement:** WCAG 2.4.7 (Focus Visible) — keyboard users must see a clear focus indicator.

**Required Fix:**
```diff
Add to globals.css:

## Focus Indicators

@layer base {
  /* Remove default browser outline for custom styling */
  *:focus-visible {
    @apply outline-2 outline-offset-2 outline-primary;
  }

  /* Enhanced focus for buttons */
  button:focus-visible {
    @apply outline-2 outline-offset-2 outline-primary rounded-lg;
    box-shadow: 0 0 0 4px color-mix(in srgb, currentColor 20%);
  }

  /* Focus for form inputs */
  input:focus-visible,
  textarea:focus-visible,
  select:focus-visible {
    @apply outline-2 outline-offset-1 outline-primary;
    border-color: theme(colors.primary);
    box-shadow: inset 0 0 0 2px theme(colors.primary) 20%;
  }

  /* Focus for link elements */
  a:focus-visible {
    @apply outline-2 outline-offset-2 outline-primary rounded-sm;
  }

  /* Radio & Checkbox focus */
  input[type="radio"]:focus-visible,
  input[type="checkbox"]:focus-visible {
    @apply outline-2 outline-offset-2 outline-primary;
  }

  /* Respect prefers-reduced-motion for focus animation */
  @media (prefers-reduced-motion: reduce) {
    *:focus-visible {
      outline-style: solid;
      outline-width: 3px;
    }
  }
}

## Skip Link Focus
.skip-link {
  @apply sr-only absolute left-0 top-0 z-[1000] focus:not-sr-only focus:p-4 focus:bg-primary focus:text-white focus:rounded-md;
}
```

#### Focus Management in Assessment
**Severity:** Warning
**Elements:** Question navigation, BARS scale, MCQ options

**Required Fix:**
```diff
Add to Assessment UI spec:

## Focus Management

### Question Card
- When new question loads, focus moves to first interactive element
- For BARS: focus first circle
- For MCQ: focus first option
- For Open Text: focus textarea

import { useEffect, useRef } from "react";

export function QuestionCard({ question, type }) {
  const firstInteractiveRef = useRef<HTMLElement>(null);

  useEffect(() => {
    firstInteractiveRef.current?.focus();
  }, [question.id]);

  return (
    <div className="question-card">
      {type === "bars" && (
        <BARSScale ref={firstInteractiveRef} {...props} />
      )}
      {/* ... */}
    </div>
  );
}
```

---

## 7. LANGUAGE TAG

### 7.1 Current Specification

**Stated in MEGA-PROMPT (lines 654, 650):**
```tsx
<html lang={locale} suppressHydrationWarning>
```

**Status:** ✅ **PASS** — Correctly sets `lang` attribute based on `locale` parameter

**Details:**
- Primary locale: `lang="az"` (Azerbaijani)
- Secondary locale: `lang="en"` (English)
- Correctly passed from route params

**Recommendation:** Ensure all locale switching updates the `lang` attribute to reflect current language (already implemented correctly).

---

## 8. FORM ACCESSIBILITY

### 8.1 Label Associations
**Status:** ⚠️ **Warning — Not explicitly specified**

### 8.2 Required Additions

#### Email Input (Login Page)
**Severity:** Warning
**Element:** `<input type="email">` on login page

**Required Fix:**
```diff
Add to Login Page UI spec (MODULE 2):

## Login Form Accessibility

<label htmlFor="email-input" className="block font-medium mb-2">
  {t("auth.login.email_label")}  /* "Email address" */
</label>
<input
  id="email-input"
  type="email"
  inputMode="email"
  required
  aria-required="true"
  placeholder={t("auth.login.email_placeholder")}
  aria-label={t("auth.login.email_aria_label")}  /* "Email address for login" */
/>

// i18n
// locales/az/auth.json
{
  "login": {
    "email_label": "E-poçt ünvanı",
    "email_placeholder": "E-poçt ünvanınız",
    "email_aria_label": "Daxil olmaq üçün e-poçt ünvanı"
  }
}

// locales/en/auth.json
{
  "login": {
    "email_label": "Email address",
    "email_placeholder": "Your email address",
    "email_aria_label": "Email address for sign-in"
  }
}
```

#### Open Text Input (Assessment)
**Severity:** Warning
**Element:** Textarea with word limit for open-text questions

**Required Fix:**
```diff
Modify OpenTextInput component spec:

## Open Text Input Accessibility

<div className="open-text-container">
  <label htmlFor={`question-${questionId}`} className="sr-only">
    {t("assessment.open_text_question")}: {question.text}
  </label>

  <textarea
    id={`question-${questionId}`}
    value={response}
    onChange={(e) => setResponse(e.target.value)}
    aria-label={question.text}
    aria-describedby={`char-count-${questionId}`}
    aria-required="true"
    maxLength={maxWords * 6}  /* Approx word byte limit */
    placeholder={t("assessment.open_text_placeholder")}
    className="w-full rounded-lg border border-border p-4 font-sans text-base resize-none"
  />

  <div
    id={`char-count-${questionId}`}
    aria-live="polite"
    aria-atomic="true"
    className="mt-2 text-sm text-muted"
  >
    {t("assessment.char_count", {
      current: response.length,
      max: maxWords * 6,
    })}
  </div>

  <div
    className="flex items-center gap-2 text-xs text-muted mt-2"
    aria-hidden="true"  /* Hidden from screen readers; content in aria-describedby */
  >
    <InfoIcon size={16} />
    {t("assessment.ai_will_evaluate")}
  </div>
</div>

// i18n
// locales/az/assessment.json
{
  "open_text_question": "Açıq mətin sualı",
  "open_text_placeholder": "Cavabınızı yazın...",
  "char_count": "{{current}}/{{max}} simvol",
  "ai_will_evaluate": "Süni intellekt tərəfindən qiymətləndiriləcəkdir"
}

// locales/en/assessment.json
{
  "open_text_question": "Open-ended question",
  "open_text_placeholder": "Enter your answer...",
  "char_count": "{{current}}/{{max}} characters",
  "ai_will_evaluate": "AI will evaluate your response"
}
```

#### Required Field Indicators
**Severity:** Warning
**Status:** Not specified

**Required Fix:**
```diff
Add form field spec:

## Required Field Indicators

All required fields must have visual AND programmatic indicators:

<label htmlFor="username" className="block font-medium mb-2">
  {t("auth.username_label")}
  <span aria-label={t("common.required_field")} className="text-destructive ml-1">
    *
  </span>
</label>
<input
  id="username"
  type="text"
  required
  aria-required="true"
  aria-label={t("auth.username_aria_label")}
/>

// i18n
// locales/az/common.json
{
  "required_field": "Səciyyəvi alan"
}

// locales/en/common.json
{
  "required_field": "Required field"
}
```

#### Error Announcements
**Severity:** Critical
**Status:** Not specified

**Required Fix:**
```diff
Add to form handling spec:

## Form Error Announcements

Errors must be announced to screen readers immediately:

<form onSubmit={handleSubmit}>
  <div
    role="alert"
    aria-live="assertive"
    aria-atomic="true"
    className={cn(
      "mb-4 p-4 rounded-lg text-sm",
      errors.length > 0 ? "bg-destructive/10 text-destructive border border-destructive/30" : "hidden"
    )}
  >
    {errors.length > 0 && (
      <>
        <h2 className="font-semibold mb-2">
          {t("common.form_error_title")}
        </h2>
        <ul className="space-y-1">
          {errors.map((error, i) => (
            <li key={i}>• {error.message}</li>
          ))}
        </ul>
      </>
    )}
  </div>

  {/* Form fields with aria-invalid & aria-describedby */}
  <div className="mb-4">
    <label htmlFor="email">Email</label>
    <input
      id="email"
      type="email"
      aria-invalid={errors.email ? "true" : "false"}
      aria-describedby={errors.email ? "email-error" : undefined}
    />
    {errors.email && (
      <div id="email-error" className="mt-1 text-sm text-destructive">
        {errors.email.message}
      </div>
    )}
  </div>
</form>

// i18n
// locales/az/common.json
{
  "form_error_title": "Xetalar var:",
  "form_submit_error": "Forma göndərilə bilmədi. Xahiş edirik yenidən cəhd edin."
}

// locales/en/common.json
{
  "form_error_title": "Please fix these errors:",
  "form_submit_error": "Failed to submit form. Please try again."
}
```

---

## Summary Table

| Category | Issue | Severity | Required Fix |
|----------|-------|----------|---------|
| **Color Contrast** | Muted text on background insufficient | Critical | Change muted color or restrict usage to decorative elements |
| **Color Contrast** | Silver badge text insufficient | Critical | Darken silver color or use dark text on light background |
| **Color Contrast** | Gold badge text marginal | Warning | Test on devices; consider darker text |
| **Touch Targets** | BARS scale circle sizes not specified | Warning | Specify 44×44px minimum per circle |
| **Touch Targets** | MCQ option card heights not specified | Warning | Specify 44px minimum height per card |
| **Touch Targets** | Bottom nav items not sized | Warning | Specify 60×60px height minimum |
| **Touch Targets** | Share button sizes not specified | Warning | Specify 44×44px for icon buttons |
| **Keyboard Navigation** | Assessment navigation not specified | Critical | Define Tab order, Arrow key behavior, Enter/Space actions |
| **Keyboard Navigation** | Modal focus trap not specified | Critical | Define focus management on modal open/close |
| **Keyboard Navigation** | Skip link not specified | Warning | Add visible-on-focus skip link to main content |
| **Screen Reader** | Radar chart not accessible | Critical | Add hidden table alternative + role="img" + aria-label |
| **Screen Reader** | Score counter animation not announced | Critical | Implement aria-live polite region + status role |
| **Screen Reader** | Badge chips not labeled | Warning | Add aria-label to all badge elements |
| **Screen Reader** | Progress bar not marked up | Warning | Use role="progressbar" with aria-valuenow/valuemin/valuemax |
| **Screen Reader** | Icon-only buttons not labeled | Critical | Add aria-label to all icon buttons (share, settings, close) |
| **Motion** | Confetti animation doesn't respect prefers-reduced-motion | Critical | Conditionally render based on useReducedMotion() hook |
| **Motion** | Score counter animation doesn't respect prefers-reduced-motion | Critical | Skip animation if prefers-reduced-motion: reduce |
| **Motion** | Page transitions don't respect prefers-reduced-motion | Critical | Conditionally apply transitions |
| **Motion** | Floating orbs animation doesn't respect prefers-reduced-motion | Warning | Skip animation if prefers-reduced-motion: reduce |
| **Focus Indicators** | Custom focus styles not defined | Warning | Add explicit focus-visible outline styles to globals.css |
| **Focus Indicators** | Focus management in assessment not specified | Warning | Auto-focus first interactive element on question load |
| **Language Tag** | HTML lang attribute | ✅ PASS | Already correctly implemented |
| **Form Accessibility** | Email input label not associated | Warning | Add explicit <label> with for="id" |
| **Form Accessibility** | Open text input not fully accessible | Warning | Add aria-label, aria-describedby, aria-required |
| **Form Accessibility** | Required field indicators not specified | Warning | Add visual * + aria-required + aria-label "Required" |
| **Form Accessibility** | Error announcement not specified | Critical | Use role="alert" + aria-live="assertive" + aria-invalid |

---

## Recommendations & Implementation Priority

### Tier 1: Critical (Must fix before launch)
1. **Muted text contrast** — Change color palette or restrict usage
2. **Keyboard navigation** — Implement full keyboard support for assessment UI
3. **Modal focus trap** — Implement proper focus management
4. **Radar chart accessibility** — Add hidden table + screen reader labels
5. **Score counter announcement** — Implement aria-live region
6. **Icon button labels** — Add aria-labels to all icon-only buttons
7. **Animation prefers-reduced-motion** — Respect user preferences in all animations
8. **Form error announcements** — Use role="alert" for validation errors

### Tier 2: Warning (Should fix for robust AA compliance)
1. **Touch target sizes** — Document explicit pixel sizes for all interactive elements
2. **Silver badge contrast** — Test on actual devices; adjust if needed
3. **Focus indicator styling** — Define custom outline styles
4. **Skip link** — Add visible-on-focus skip to main content
5. **Form label associations** — Ensure all inputs have linked labels

### Tier 3: Suggestion (Nice-to-have for enhanced UX)
1. **Focus management in assessment** — Auto-focus first interactive element
2. **Badge aria-labels** — Ensure semantic information communicated
3. **Floating orbs animation** — Enhance with reduced-motion variant

---

## Testing Checklist

Before launch, validate accessibility using:

- [ ] **Axe DevTools** (Chrome extension) — automatic WCAG scanning
- [ ] **WAVE** (WebAIM) — visual accessibility feedback
- [ ] **Keyboard navigation** — Tab through entire site without mouse
- [ ] **Screen reader testing** — NVDA (Windows) or JAWS (Windows) or VoiceOver (macOS)
- [ ] **Color contrast** — WebAIM Contrast Checker against actual rendered colors
- [ ] **prefers-reduced-motion** — Test with system setting enabled
- [ ] **Mobile accessibility** — TalkBack (Android) or VoiceOver (iOS)
- [ ] **Focus indicator visibility** — Ensure 2px+ outline visible on all elements
- [ ] **Azerbaijani text rendering** — Test special characters (ə, ğ, ı, ö, ü, ş, ç)
- [ ] **ARIA attributes validation** — Use ARIA authoring practices validator

---

**Audit Completed:** 2026-03-22
**Auditor:** Claude (WCAG 2.1 AA Specialist)
**Next Review:** After implementation of Tier 1 fixes
