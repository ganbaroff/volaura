# Brand Identity
## Volaura Design System

**Last Updated:** March 22, 2026
**Audience:** Design, Marketing, Development Teams
**Scope:** Visual brand, voice, tone, and strategic positioning

---

## 1. Brand Story

### Mission
Make volunteer talent visible, measurable, and portable — transforming how organizations discover and verify competent volunteers across Azerbaijan and the CIS/MENA region.

### Vision
Every volunteer in CIS/MENA has a verified credential that opens doors to meaningful opportunities, lifelong learning, and recognized impact.

### Brand Name: Volaura
**Etymology:** Volunteer + Aura
- **Volunteer:** The person — committed, skilled, available
- **Aura:** The invisible glow of verified competence — what others *feel* about your abilities

**Tagline:** "Your Skills, Verified"

### Core Values
1. **Transparency** — Credentials are earned through rigorous, AI-powered assessment, not guesswork
2. **Inclusivity** — Every volunteer, regardless of background, can build a verified profile
3. **Empowerment** — Volunteers own their credentials and control who sees them
4. **Trustworthiness** — Peer and organization verification validates authenticity
5. **Progress** — AURA scores reflect growth; assessments happen on a journey, not once

### Brand Pillars
| Pillar | Meaning | Application |
|--------|---------|-------------|
| **Verified** | Trust through rigor | AURA badge, verification levels, transparent rubrics |
| **Visible** | Your work deserves recognition | Public profiles, shareable badges, leaderboards |
| **Valued** | You matter | Competency-based (not time-based) assessment, peer recognition |
| **Growing** | Skills develop over time | Assessment journey, milestone tracking, trend visualization |

---

## 2. Logo System

### Primary Logo
**Format:** Wordmark + Icon combination
**Typeface:** Inter Bold (wordmark) with gradient accent
**Icon:** Abstract "V" combined with radiating concentric aura rings

#### Wordmark Specifications
- Text: "Volaura" in Inter Bold
- The word "aura" within "Volaura" features a subtle gradient accent (primary → accent color)
- Full lockup: Icon + wordmark, horizontal arrangement
- Minimum height: 24px (for small uses, icon-only acceptable)
- Clear space: 1× the height of the "V" icon on all sides

#### Icon Specifications
- Shape: Stylized "V" at center, surrounded by 3 concentric rings (aura effect)
- Stroke width: 2px
- Color: [[#Color System|oklch(0.65 0.25 275)]] — deep indigo-violet
- Square aspect ratio (24px × 24px minimum)
- Scalable to any size; maintain proportions

#### Logo Variations
| Variation | Use When |
|-----------|----------|
| **Full Lockup** | Primary usage, heading, hero sections |
| **Icon Only** | Favicon, app icon, small spaces, social media avatar |
| **Horizontal** | Wide layouts, headers, banners |
| **Vertical** | Stacked layouts, narrow sidebars |
| **White Reverse** | Dark backgrounds, inverse contrast |
| **Monochrome** | Printing, black/white situations |

#### Logo Don'ts
- Never distort or stretch the icon
- Never change the color (unless monochrome for printing)
- Never add drop shadows or outlines (plain/simple only)
- Never place on busy backgrounds without sufficient contrast
- Never rotate or tilt the logo
- Never separate the icon from the wordmark at full size (combine as lockup)

### Favicon
- **File:** `public/favicon.ico` + Apple touch icon
- **Size:** 32×32px (favicon), 180×180px (Apple)
- **Design:** Simplified aura icon, indigo on white or vice versa
- **Format:** PNG or ICO (favicon.ico is converted from PNG)

### Visual Language

#### Style Characteristics
- **Modern:** Clean, geometric, minimal ornamentation
- **Trustworthy:** Confident, measured, professional
- **Humanistic:** Warm, approachable, inclusive
- **Dynamic:** Motion and growth implied through rings/curves
- **Global:** Culturally neutral, works across CIS/MENA markets

---

## 3. Color System

### Primary Colors (oklch)

**Primary Brand Color:**
```
--primary:        oklch(0.65 0.25 275)    /* Deep indigo-violet */
--primary-light:  oklch(0.75 0.20 275)    /* Lighter indigo (hover states) */
--primary-dark:   oklch(0.45 0.25 275)    /* Darker indigo (press states) */
```
**Usage:** Primary buttons, active states, accent highlights, icon fills

**Accent Color (Complementary):**
```
--accent:         oklch(0.70 0.22 300)    /* Soft violet */
```
**Usage:** Secondary buttons, decorative accents, hover effects on secondary elements

### Semantic Colors

**Success (Validation, Completion):**
```
--success:        oklch(0.72 0.20 160)    /* Emerald green */
--success-light:  oklch(0.82 0.15 160)    /* Light emerald (backgrounds) */
--success-dark:   oklch(0.55 0.20 160)    /* Dark emerald (text on light) */
```
**Usage:** Success messages, checkmarks, passed assessments, positive trends

**Warning (Caution, Attention):**
```
--warning:        oklch(0.80 0.18 85)     /* Amber/gold */
--warning-light:  oklch(0.90 0.12 85)     /* Light amber (backgrounds) */
--warning-dark:   oklch(0.60 0.18 85)     /* Dark amber (text) */
```
**Usage:** Warnings, caution states, pending items, incomplete assessments

**Error (Failure, Blocking):**
```
--error:          oklch(0.65 0.25 25)     /* Rose red */
--error-light:    oklch(0.80 0.15 25)     /* Light rose (backgrounds) */
--error-dark:     oklch(0.50 0.25 25)     /* Dark rose (text) */
```
**Usage:** Error messages, failed validation, blocking states, critical alerts

### Badge Tier Colors

**Platinum Tier (AURA ≥ 90):**
```
--badge-platinum: oklch(0.85 0.05 270)    /* Cool silver-lavender */
```
**Visual:** Shimmering, premium appearance with subtle purple tint
**Usage:** Top-tier achievement badge

**Gold Tier (AURA 75-89):**
```
--badge-gold:     oklch(0.80 0.18 85)     /* Rich gold */
```
**Visual:** Warm, luxurious, celebratory
**Usage:** High-achievement badge

**Silver Tier (AURA 60-74):**
```
--badge-silver:   oklch(0.75 0.03 260)    /* Silver */
```
**Visual:** Neutral, professional, solid achievement
**Usage:** Mid-achievement badge

**Bronze Tier (AURA 40-59):**
```
--badge-bronze:   oklch(0.65 0.12 55)     /* Warm bronze */
```
**Visual:** Warm, accessible, beginning achievement
**Usage:** Entry-level achievement badge

**None/Below Threshold (AURA < 40):**
```
--badge-none:     oklch(0.60 0.02 260)    /* Neutral gray */
```
**Visual:** Neutral, no emphasis
**Usage:** Below-threshold state

### Neutral/Background Colors

**Surface Background (Page):**
```
--surface-bg:     oklch(0.98 0.005 270)   /* Near-white with slight purple tint */
```
**Usage:** Main page background, provides subtle brand cohesion

**Card/Surface (Elevated):**
```
--surface-card:   oklch(1.0 0 0)          /* Pure white */
```
**Usage:** Card backgrounds, elevated surfaces, maximum contrast

**Border (Subtle):**
```
--border:         oklch(0.90 0.01 270)    /* Light gray with purple cast */
```
**Usage:** Card borders, dividers, subtle boundaries

**Text Primary (Foreground):**
```
--text-primary:   oklch(0.15 0.02 270)    /* Near-black */
```
**Usage:** Body text, headings, primary content

**Text Secondary (Muted):**
```
--text-secondary: oklch(0.45 0.02 270)    /* Muted gray-purple */
```
**Usage:** Helper text, captions, secondary content, placeholder text

**Text Tertiary (Very Muted):**
```
--text-tertiary:  oklch(0.65 0.01 270)    /* Light muted gray */
```
**Usage:** Disabled text, very subtle labels

### Gradient: Aurora Effect

**Primary Gradient (Brand Hero):**
```
--aurora-gradient: linear-gradient(
  135deg,
  oklch(0.65 0.25 275),    /* Primary indigo */
  oklch(0.70 0.22 300),    /* Mid violet */
  oklch(0.75 0.18 325)     /* Light lavender */
)
```
**Usage:** Hero sections, AURA badge backgrounds, premium CTAs, landing page accents

**Success Gradient:**
```
linear-gradient(
  to right,
  oklch(0.72 0.20 160),    /* Dark green */
  oklch(0.82 0.15 160)     /* Light green */
)
```

**Warning Gradient:**
```
linear-gradient(
  to right,
  oklch(0.80 0.18 85),     /* Amber */
  oklch(0.90 0.12 85)      /* Light amber */
)
```

### Color Accessibility Ratios
- Text on backgrounds must meet WCAG AA (4.5:1 for normal text, 3:1 for large)
- All semantic colors chosen for sufficient contrast with white and near-white surfaces
- Badge colors tested for distinguishability by colorblind users
- Error and success never used as sole indicators; paired with icons/labels

### Dark Mode (Future Consideration)
Dark mode is **not shipped in MVP** but brand system supports future implementation:
- Surface colors invert (dark bg, light text)
- Primary colors become more saturated in dark mode for contrast
- All oklch color specs can be dynamically adjusted via CSS variables
- Tailwind config enables easy dark mode toggle

---

## 4. Typography

### Font Families

**Headings (Display & Hierarchy):**
- **Font:** Inter Bold (font-weight: 700) or Inter SemiBold (font-weight: 600)
- **Use:** H1 (60/48px), H2 (36/30px), H3 (24/20px), hero text, badge labels
- **Characteristics:** Modern, clean, geometric

**Body Copy (Readability):**
- **Font:** Inter Regular (font-weight: 400) or Inter Medium (font-weight: 500)
- **Use:** Paragraphs, form labels, navigation, UI text
- **Characteristics:** Highly legible, neutral, professional

**Monospace (Scores & Data):**
- **Font:** JetBrains Mono Regular (for alignment and technical feel)
- **Use:** AURA scores, competency numbers, countdown timers, data tables
- **Characteristics:** Fixed-width for alignment, technical authority

### Type Scale

Pixels (desktop) / rem values:

| Role | Size | Weight | Line Height | Letter Spacing | Example |
|------|------|--------|-------------|----------------|---------|
| Display | 72px / 4.5rem | Bold | 1.1 | -0.02em | Launch Event Hero |
| H1 | 60px / 3.75rem | Bold | 1.2 | -0.01em | Page Titles |
| H2 | 48px / 3rem | Bold | 1.2 | 0 | Section Titles |
| H3 | 36px / 2.25rem | SemiBold | 1.3 | 0 | Card Headers |
| H4 | 30px / 1.875rem | SemiBold | 1.4 | 0 | Subsection |
| H5 | 24px / 1.5rem | SemiBold | 1.4 | 0 | Feature Title |
| H6 | 20px / 1.25rem | SemiBold | 1.5 | 0 | Label |
| Body L | 18px / 1.125rem | Regular | 1.6 | 0 | Large body |
| Body | 16px / 1rem | Regular | 1.6 | 0 | Standard body |
| Body S | 14px / 0.875rem | Regular | 1.5 | 0 | Small text |
| Caption | 12px / 0.75rem | Regular | 1.4 | 0.01em | Helper text |
| Overline | 12px / 0.75rem | SemiBold | 1.2 | 0.1em | Labels, tags |
| Score | 72px / 4.5rem | Bold (JetBrains Mono) | 1 | -0.02em | Large score display |
| Number | 24px / 1.5rem | Regular (JetBrains Mono) | 1 | 0 | Data tables |

### Font Loading & Performance
- **Strategy:** System fonts for fast load (inter-var fallback to system stack)
- **WebFonts:** Hosted via Google Fonts or self-hosted via Vercel
- **font-display:** swap (show fallback immediately, swap when ready)
- **Subsetting:** Cyrillic for Azerbaijani support

### Font Stack (CSS fallback)
```css
/* Headings */
font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;

/* Monospace */
font-family: "JetBrains Mono", "Courier New", monospace;
```

---

## 5. Illustration System

### Style Guidelines

**Aesthetic:**
- Flat design with subtle gradients (no photorealism)
- Geometric, modern, minimal detail
- Warm but professional (not cartoonish)
- Consistent stroke widths and spacing

**Color Palette:**
- Use brand colors ([[#Color System|oklch-based palette]])
- Never introduce external colors
- Maintain 70% color saturation maximum (soft, not neon)
- Ensure illustrations work at various sizes (responsive)

**Illustration Set:**
1. **Character Archetypes:** Diverse (gender, age, ethnicity), geometric style, no detailed faces
   - Community leader
   - Event organizer
   - Young volunteer
   - Mentor/coach
   - Peer evaluator

2. **Scenario Scenes:**
   - Handshake (trust, partnership)
   - Podium/award (recognition, achievement)
   - Rising graph (growth, progress)
   - Globe with pins (geographic reach, expansion)
   - Open doors (opportunity, access)
   - Network nodes (connection, community)

3. **Empty States:**
   - No assessments → blank slate with lightbulb
   - No events → empty calendar with star
   - No connections → isolated node with hand reaching
   - Search no results → magnifying glass with "?"

4. **Iconography within Illustrations:**
   - Use Lucide icons embedded in scenes
   - Scale icons 2-4× normal size for prominence
   - Maintain consistent stroke weight

### Asset Organization
```
/public/illustrations/
  ├── characters/
  │   ├── leader.svg
  │   ├── organizer.svg
  │   ├── volunteer.svg
  │   └── mentor.svg
  ├── scenes/
  │   ├── handshake.svg
  │   ├── achievement.svg
  │   ├── growth.svg
  │   └── global.svg
  ├── empty-states/
  │   ├── no-assessments.svg
  │   ├── no-events.svg
  │   └── no-results.svg
  └── abstract/
      ├── wave.svg
      ├── blob.svg
      └── dots.svg
```

### Illustration Usage Guidelines
- **Hero sections:** Large, full-width scenes with characters
- **Empty states:** Medium-sized, centered, paired with text + CTA
- **Cards:** Small icons or simple scenes (avoid cluttering)
- **Backgrounds:** Use abstract shapes, keep subtle (not dominant)
- **Loading screens:** Animated simple shapes or skeleton illustrations

---

## 6. Iconography

### Primary Icon Set: Lucide Icons
- **Library:** lucide-react for consistency
- **Standard Sizes:** 16px (small), 20px (default), 24px (large)
- **Stroke Weight:** 2px (default Lucide preset)
- **Color Inheritance:** Icons inherit text color or use semantic colors

### Icon Usage Patterns

| Context | Size | Weight | Color | Example |
|---------|------|--------|-------|---------|
| Navigation | 24px | 2px | --text-secondary or --primary when active | home, list, settings |
| Buttons | 20px | 2px | Inherit from button text color | search, plus, trash |
| Alerts/Status | 24px | 2px | Semantic color (success/error/warning) | check-circle, alert-circle |
| Tables | 16px | 2px | --text-secondary | sort-asc, filter |
| Forms | 20px | 2px | --text-secondary | eye (toggle), check |
| Loading | 24px | 2px | --primary (animated rotation) | loader, spinner |

### Custom Icons (Beyond Lucide)

**Competency Symbols:** 8 unique icons for AURA competencies
- **Communication:** Speech bubbles or megaphone (custom)
- **Reliability:** Clock or checkmark (from Lucide, styled)
- **English Proficiency:** Globe with "EN" (custom)
- **Leadership:** Crown or upward arrow (custom)
- **Event Performance:** Presentation stage (custom)
- **Tech Literacy:** Laptop or code brackets (custom)
- **Adaptability:** Branches or flexibility symbol (custom)
- **Empathy & Safeguarding:** Heart with shield (custom)

**Verification Badges:** 3 custom shield icons
- **Self-assessed:** Outlined shield
- **Organization-verified:** Filled shield with checkmark
- **Peer-verified:** Shield with multiple checkmarks

**AURA Badge:** Custom star or aura-ring icon (matches logo rings)

### Icon Design Principles
- **Consistency:** All custom icons use 2px strokes, rounded corners (4px)
- **Clarity:** Recognizable at 16px minimum
- **Accessibility:** Icons always paired with text labels or descriptive aria-labels
- **Animation:** Icons can rotate (loading), scale (hover), or fade (state change)

---

## 7. Voice & Tone

### Voice (Consistent Personality)

**Volaura's Voice is:**
- **Formal but warm** — Professional without being cold; respectful but human
- **Empowering** — Positions user as the subject, not object of assessment
- **Inclusive** — Gender-neutral language, culturally respectful
- **Action-oriented** — Clear, direct CTAs using strong verbs
- **Transparent** — Honest about what AURA does; no overselling

**Brand Voice Pillars:**
1. We *help you shine*, not judge you
2. Your skills *matter* — they're verified because they matter
3. We're *clear* about how it works
4. We *respect* your cultural context (AZ-first, EN second)
5. We're *here for the journey*, not just the destination

### Tone (Contextual Variation)

| Context | Tone | Example |
|---------|------|---------|
| **Welcome/Onboarding** | Encouraging, warm, inviting | "Welcome to Volaura! Let's discover what makes you exceptional." |
| **Assessment** | Focused, supportive, neutral | "Take your time. Be honest. This assessment is just for you." |
| **Results** | Celebratory, constructive | "Great work! You've earned your Gold badge. Here's where to grow next." |
| **Error/Failure** | Helpful, non-blaming | "Something went wrong. Here's what we suggest..." |
| **Empty State** | Friendly, motivating | "No assessments yet? Let's change that in 10 minutes." |
| **Notifications** | Concise, actionable | "Your peer review is ready. [View]" |
| **Profile/Public** | Professional, confident | "Communication Master. Certified by Org + 5 peers." |
| **Help/Support** | Accessible, patient | "New to Volaura? We're here to help. [See FAQ]" |

### Language Specifics

#### Azerbaijani (AZ)
- **Register/Form Level:** Formal "siz" (not informal "sən")
- **Direction:** Right-to-left support ready (future: RTL CSS)
- **Dates:** Use European format (DD/MM/YYYY) or contextual ("3 gün əvvəl")
- **Punctuation:** Follow standard Azerbaijani conventions
- **Culturally sensitive:** Avoid gendered assumptions, use gender-neutral terms where possible
- **Example:** "Siz haqqında ətraflı məlumat" (About you in detail)

#### English (EN)
- **Register/Form Level:** Standard, professional
- **Pronouns:** Use singular "they" when gender unknown; specify "you" when clear
- **Formality:** Slightly higher than colloquial (but not stiff)
- **Example:** "Tell us about yourself. What makes you an exceptional volunteer?"

### Word Choices (Preferred vs. Avoid)

| Preferred | Avoid | Why |
|-----------|-------|-----|
| Assessment | Test, Quiz, Exam | Less intimidating; emphasizes growth |
| Competency | Skill, Ability | Technical, precise AURA term |
| AURA Score | Rating, Points, Rank | Brand-specific, holistic not competitive |
| Verify / Verification | Validate, Confirm | Stronger trust signal |
| Earn | Get, Obtain | Implies effort and achievement |
| Insight | Data, Info | More humanistic, actionable |
| Journey | Process, Path | Implies growth and continuity |
| Share | Broadcast, Post | Respects user agency and intent |
| Discover | Find, Search | More aspirational, sense of exploration |
| Opportunity | Job, Role, Position | Broader than employment; includes volunteering |

### CTAs (Call-to-Action Verbs)

**Strong, Direct Verbs:**
- Start Assessment
- Share Badge
- View Profile
- Join Event
- Explore Opportunities
- Unlock Growth
- Verify Now
- Continue Journey

**Avoid:**
- "Click here"
- "Learn more" (alone; pair with subject)
- "Submit" (when "Save" or "Continue" clearer)
- "Maybe later" (don't offer procrastination)

### Writing Checklist
- [ ] Uses action verbs (Start, Share, Join, not just View)
- [ ] Respects user (positions them as agent, not object)
- [ ] Clear and concise (no jargon unexplained)
- [ ] Gender-neutral where possible
- [ ] Translated to both AZ and EN (not auto-translated)
- [ ] Tested with users from CIS/MENA region for cultural appropriateness

---

## 8. Photography Guidelines

### When to Use Photography
- Event listings (volunteer opportunities in action)
- Team/organizer profiles (faces build trust)
- Case studies or impact stories
- "Real volunteer" moments (not stock imagery)
- Event galleries (documentation, social proof)

### Photography Principles

**Authenticity:**
- Real volunteers, real events, real impact
- Avoid staged "perfection" — real moments preferred
- Diverse representation: gender, age, ethnicity, ability
- Geographic diversity (multiple countries in CIS/MENA)

**Settings:**
- Community events, workshops, meetups
- Outdoor volunteer activities (cleanup, planting, etc.)
- Professional settings (training, presentations)
- Candid team moments
- Avoid: Office cubicles, studio backdrops, overly polished setups

**Composition:**
- Focus on human faces and genuine emotion
- Rule of thirds for balance
- Strong focal point (usually a face or meaningful action)
- Environmental context visible (where is this happening?)
- Lighting: Natural is preferred; avoid harsh shadows on faces

**Editing & Treatment:**
- Subtle brand color overlay (primary indigo at 5-10% opacity) on hero images
- Warm color temperature (not cold/blue-tinted)
- High contrast and saturation (vivid, not muted)
- Consistent filter/preset applied across campaign
- No heavily filtered or "Instagram-style" effects

### Rights & Ethics
- **Consent:** Model releases for all recognizable faces
- **Attribution:** Credit volunteers when possible ("Featuring Ali from Baku, Community Leader")
- **Diversity:** Intentionally source photos representing CIS/MENA communities
- **Avoid:** Stereotypes, "white savior" imagery, homogeneous group shots
- **Storage:** Organize in `/public/images/` with metadata tags (date, event, location, photographer)

### Sizing & Formats
- **Web images:** AVIF/WebP with JPG fallback
- **Mobile:** Optimized for 16:9 landscape or 1:1 square
- **Hero banner:** 1920×1080px (desktop), 768×576px (tablet), 390×300px (mobile)
- **Event card image:** 400×300px (cards) or 1200×630px (social preview)
- **Profile avatar:** 200×200px (minimum), 400×400px (preferred)

---

## 9. Motion Principles

### Philosophy
**Purposeful, not decorative:** Every animation communicates a state change, provides feedback, or guides attention. Random motion creates cognitive load.

### Key Principles

| Principle | Description | Example |
|-----------|-------------|---------|
| **Purposeful** | Motion has a reason — state change, feedback, guidance | Button press → color change + bounce |
| **Quick** | Micro-interactions max 400ms; transitions 200-300ms | Fade in/out: 300ms |
| **Consistent** | Same motion patterns everywhere (spring params standardized) | All modals slide in from same direction/speed |
| **Accessible** | Respects `prefers-reduced-motion` media query | If enabled, instant or minimal animation |
| **Responsive** | Staggered reveals on list items; slower on mobile | On mobile, reduce duration by 20% |
| **Contextual** | Heavy animations for delightful moments; subtle for routine | Confetti on results, subtle fade on tab switch |

### Standard Motion Parameters (Framer Motion)

```javascript
// Spring physics (default for everything except fades)
const SPRING = {
  type: "spring",
  damping: 12,
  stiffness: 100,
  mass: 1,
  duration: 0.4, // fallback if spring calc > 400ms
};

// Fade/opacity transitions (quick, no overshoot)
const FADE = {
  duration: 0.3,
  ease: "easeInOut",
};

// Enter animations (slightly slower, more visible)
const ENTER = {
  ...SPRING,
  damping: 10,
  stiffness: 80,
};

// Stagger children in lists
const STAGGER = 0.05; // 50ms between items
```

### Motion Use Cases

| Interaction | Type | Duration | Ease | Example |
|-------------|------|----------|------|---------|
| **Button press** | Scale + color | 150ms | spring | Badge unlock |
| **Page transition** | Fade + slide | 300ms | easeInOut | Route change |
| **Modal open** | Slide up + fade | 300ms | spring | Share modal |
| **List item reveal** | Fade + stagger | 300ms + 50ms per item | easeInOut | Leaderboard load |
| **Score reveal** | Number counter + pulse | 1200ms | spring | Results page |
| **Hover feedback** | Lift + shadow | 200ms | spring | Card hover |
| **Loading** | Rotate/pulse | Continuous | linear | Spinner |
| **Notification toast** | Slide in/out | 250ms | spring | Toast appear/dismiss |
| **Confetti** | Burst then fall | 2000ms | easeOut | Achievement |
| **Scroll reveal** | Fade in from below | 400ms | easeOut | On intersection |

### Animation Library: Framer Motion

**Import pattern:**
```tsx
import { motion } from "framer-motion";

// Staggered list
<motion.div
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
  transition={{ staggerChildren: 0.05 }}
>
  {items.map((item) => (
    <motion.div
      key={item.id}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={SPRING}
    >
      {item.name}
    </motion.div>
  ))}
</motion.div>
```

### Accessibility Compliance

**prefers-reduced-motion:**
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

**or in Framer Motion:**
```tsx
const isReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

<motion.div
  animate={{ opacity: 1 }}
  transition={isReducedMotion ? { duration: 0 } : SPRING}
/>
```

### Timing Guidelines
- **Mobile:** Reduce duration by 20% (slower devices, human factors)
- **Nested animations:** Parent duration ≥ child duration + stagger sum
- **Continuous animations:** Use `ease: "linear"` for spinners/loaders
- **Lazy animations:** Avoid heavy animations if page already heavy (large lists, charts)

---

## 10. Design Tokens & Variables

### CSS Custom Properties (Tailwind Integration)

All colors defined as CSS variables for easy theming:

```css
:root {
  /* Primary */
  --primary: oklch(0.65 0.25 275);
  --primary-light: oklch(0.75 0.20 275);
  --primary-dark: oklch(0.45 0.25 275);

  /* Semantic */
  --success: oklch(0.72 0.20 160);
  --warning: oklch(0.80 0.18 85);
  --error: oklch(0.65 0.25 25);

  /* Badges */
  --badge-platinum: oklch(0.85 0.05 270);
  --badge-gold: oklch(0.80 0.18 85);
  --badge-silver: oklch(0.75 0.03 260);
  --badge-bronze: oklch(0.65 0.12 55);

  /* Surface */
  --surface-bg: oklch(0.98 0.005 270);
  --surface-card: oklch(1.0 0 0);
  --border: oklch(0.90 0.01 270);

  /* Text */
  --text-primary: oklch(0.15 0.02 270);
  --text-secondary: oklch(0.45 0.02 270);
  --text-tertiary: oklch(0.65 0.01 270);

  /* Spacing (8px base) */
  --space-xs: 0.25rem;  /* 4px */
  --space-sm: 0.5rem;   /* 8px */
  --space-md: 1rem;     /* 16px */
  --space-lg: 1.5rem;   /* 24px */
  --space-xl: 2rem;     /* 32px */
  --space-2xl: 3rem;    /* 48px */

  /* Border Radius */
  --radius-sm: 0.25rem;
  --radius-md: 0.5rem;
  --radius-lg: 1rem;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
  --shadow-lg: 0 10px 15px rgba(0,0,0,0.15);
  --shadow-xl: 0 20px 25px rgba(0,0,0,0.2);
}

/* Dark mode (future) */
@media (prefers-color-scheme: dark) {
  :root {
    --surface-bg: oklch(0.12 0.01 270);
    --surface-card: oklch(0.18 0.01 270);
    --text-primary: oklch(0.95 0.02 270);
    --text-secondary: oklch(0.70 0.02 270);
  }
}
```

### Tailwind Config Integration

```js
module.exports = {
  theme: {
    colors: {
      primary: "var(--primary)",
      "primary-light": "var(--primary-light)",
      "primary-dark": "var(--primary-dark)",
      success: "var(--success)",
      warning: "var(--warning)",
      error: "var(--error)",
      "badge-platinum": "var(--badge-platinum)",
      "badge-gold": "var(--badge-gold)",
      "badge-silver": "var(--badge-silver)",
      "badge-bronze": "var(--badge-bronze)",
      surface: "var(--surface-bg)",
      card: "var(--surface-card)",
      border: "var(--border)",
      "text-primary": "var(--text-primary)",
      "text-secondary": "var(--text-secondary)",
      "text-tertiary": "var(--text-tertiary)",
    },
    spacing: {
      xs: "var(--space-xs)",
      sm: "var(--space-sm)",
      md: "var(--space-md)",
      lg: "var(--space-lg)",
      xl: "var(--space-xl)",
      "2xl": "var(--space-2xl)",
    },
    borderRadius: {
      sm: "var(--radius-sm)",
      md: "var(--radius-md)",
      lg: "var(--radius-lg)",
      full: "var(--radius-full)",
    },
  },
};
```

### Responsive Breakpoints
```
sm: 640px   (small phones)
md: 768px   (tablets)
lg: 1024px  (desktops)
xl: 1280px  (large desktops)
2xl: 1536px (ultra-wide)
```

**Strategy:** Mobile-first design; add complexity on larger screens. `BottomNavV2` and `TopBarV2` hidden at `lg` breakpoint; `AppSidebar` shown at `lg+` only.

---

## 11. Accessibility Standards

### WCAG 2.1 Compliance Target: **AA**

**Color Contrast:**
- Normal text: 4.5:1 (text on background)
- Large text (18px+ bold): 3:1
- UI components/borders: 3:1
- All semantic colors meet these ratios

**Typography:**
- Minimum font size: 12px (captions only; body ≥14px)
- Line height: 1.4-1.6 for readability
- Letter spacing: Avoid extreme compression
- Font rendering: Smooth, no pixelation at small sizes

**Motion:**
- All animations respect `prefers-reduced-motion`
- Auto-playing videos/animations have pause controls
- No flashing content (>3 flashes per second)

**Forms:**
- All inputs have associated `<label>` or aria-label
- Required fields marked visually + via aria-required
- Error messages tied to fields via aria-describedby
- Keyboard: Tab/Shift+Tab, Arrow keys, Enter/Space activate

**Components:**
- See [[COMPONENT-LIBRARY|Component Library]] for per-component accessibility specs
- All interactive elements keyboard-accessible
- Screen reader testing for complex components

---

## 12. Brand Asset Checklist

### Essentials (MVP)
- [x] Logo (wordmark + icon)
- [x] Favicon (32×32px + apple touch icon)
- [x] Color palette (oklch specifications)
- [x] Typography system (fonts + scale)
- [x] Illustration style guide (flat, geometric)
- [x] Icon set (Lucide + 11 custom icons)
- [x] Voice & tone guidelines
- [x] Motion library (Framer Motion presets)

### Phase 2 (Post-Launch)
- [ ] Photography guidelines (detailed)
- [ ] Video style guide (opening titles, testimonials)
- [ ] Animation library (preset library export)
- [ ] Dark mode theme (CSS variables)
- [ ] Marketing email templates
- [ ] Social media templates (LinkedIn, Instagram, Telegram)
- [ ] Presentation deck template (Figma)
- [ ] Print guidelines (business cards, certificates, badges)

### Phase 3 (CIS/MENA Expansion)
- [ ] Localized brand guidelines (Russian, Kazakh, etc.)
- [ ] RTL design system (for Arabic future)
- [ ] Cultural adaptation guide (imagery, messaging)
- [ ] Regional color preferences (CIS vs. MENA)

---

## 13. Brand Usage Examples

### Do's ✓

**Logo:**
- Use full lockup (icon + wordmark) at standard size
- Apply consistent clear space (1× icon height)
- Maintain aspect ratio, never distort

**Colors:**
- Use oklch values exactly as specified
- Apply aurora gradient to hero sections for premium feel
- Use semantic colors for status/feedback

**Typography:**
- Inter for everything (headings + body)
- Maintain hierarchy with consistent scale
- Use JetBrains Mono for scores/data

**Motion:**
- Spring physics for natural feel
- Respect prefers-reduced-motion
- Keep duration under 400ms for micro-interactions

**Tone:**
- Empowering, formal but warm
- Action-oriented CTAs
- Transparent about capabilities

---

### Don'ts ✗

**Logo:**
- Don't distort, rotate, or skew
- Don't add drop shadows or outlines
- Don't place on busy backgrounds
- Don't use old version if updated

**Colors:**
- Don't invent new colors
- Don't use hex/rgb equivalent (oklch only)
- Don't use all semantics at once (avoid rainbow UI)

**Typography:**
- Don't use different fonts (Inter + JetBrains Mono only)
- Don't justify-align body text (creates rivers)
- Don't use all caps for body copy

**Motion:**
- Don't animate for decoration only
- Don't exceed 400ms for standard interactions
- Don't ignore prefers-reduced-motion

**Tone:**
- Don't use corporate jargon without explanation
- Don't make assumptions about user gender
- Don't overpromise what AURA does

---

## 14. Resources & Documentation

### Brand Files Location
```
/public/brand/
├── logo/
│   ├── volaura-logo.svg (full lockup)
│   ├── volaura-icon.svg (icon only)
│   └── volaura-favicon.ico
├── illustrations/
│   ├── characters/
│   ├── scenes/
│   └── empty-states/
├── icons/
│   ├── competencies/
│   └── verification/
└── colors/
    └── color-palette.json (oklch specs)
```

### Related Documents
- [[COMPONENT-LIBRARY]] — All UI components with specs
- [[../DECISIONS]] — Design decisions and rationale
- [[../HANDOFF]] — Developer handoff guide

### Tools & Software
- **Design Tool:** Figma (primary), Penpot (backup)
- **Icons:** Lucide Icons + custom SVGs in Figma
- **Fonts:** Google Fonts (Inter, JetBrains Mono)
- **Color Tool:** oklch.space (color picker)
- **Accessibility Check:** WCAG Contrast Checker, axe DevTools
- **Motion:** Framer Motion (React), springs: https://www.framer.com/motion/

### Team Contacts
- **Design Lead:** [TBD — DRI for design system]
- **Brand Manager:** [TBD — CIS/MENA localization]
- **Accessibility:** [TBD — WCAG compliance oversight]

---

## 15. Brand Evolution & Updates

### When to Update Brand Guidelines
- Major feature launches (new component types)
- Significant color/typography changes
- Regional expansion (new locales, cultural adaptation)
- Accessibility compliance requirements
- User feedback or A/B test results

### Version History
| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-22 | Initial brand guidelines for MVP launch |

### Change Request Process
1. Propose change in [[../DECISIONS]] document
2. Get feedback from Design Lead + Brand Manager
3. Update this document + [[COMPONENT-LIBRARY]]
4. Notify frontend/backend teams of any technical impact
5. Update Figma components if visual changes
6. Version bump + changelog entry

---

## Appendix: Color Reference Chart

### Quick Copy-Paste (oklch values)

```
PRIMARY:          oklch(0.65 0.25 275)
PRIMARY-LIGHT:    oklch(0.75 0.20 275)
PRIMARY-DARK:     oklch(0.45 0.25 275)
SUCCESS:          oklch(0.72 0.20 160)
WARNING:          oklch(0.80 0.18 85)
ERROR:            oklch(0.65 0.25 25)
BADGE-PLATINUM:   oklch(0.85 0.05 270)
BADGE-GOLD:       oklch(0.80 0.18 85)
BADGE-SILVER:     oklch(0.75 0.03 260)
BADGE-BRONZE:     oklch(0.65 0.12 55)
SURFACE-BG:       oklch(0.98 0.005 270)
SURFACE-CARD:     oklch(1.0 0 0)
TEXT-PRIMARY:     oklch(0.15 0.02 270)
TEXT-SECONDARY:   oklch(0.45 0.02 270)
```

### Brand Hex Approximations (Reference Only — Use oklch)
```
PRIMARY:          #6D28D9
BADGE-GOLD:       #CCA600
SUCCESS:          #10B981
ERROR:            #EF4444
```
*Note: Hex is approximate; always use oklch for exact colors.*

---

**Document Version:** 1.0
**Last Updated:** 2026-03-22
**Maintained by:** Design System Team
**Related:** [[COMPONENT-LIBRARY]], DECISIONS.md, HANDOFF.md
**Archive:** Previous versions available in git history
