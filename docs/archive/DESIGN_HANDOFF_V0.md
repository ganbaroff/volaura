# Volaura — Design Handoff for v0.dev

> **Целевой инструмент:** [v0.dev](https://v0.dev) от Vercel
> **Дата:** 2026-03-22
> **Проект:** Volaura — верифицированная платформа волонтёрских талантов (Азербайджан)
> **Дедлайн:** Launch Event in Baku, May 2026

---

## Как пользоваться этим документом

1. Откройте [v0.dev](https://v0.dev) и нажмите «New chat».
2. Вставьте **Глобальный системный промпт** (раздел ниже) как первое сообщение.
3. После этого вставляйте промпты для каждого экрана по одному.
4. Полученный JSX/TSX код копируйте в соответствующий файл `apps/web/src/`.

---

## 1. Глобальный системный промпт (вставить первым)

```
You are designing UI components for Volaura — an elite verified volunteer talent platform
launching in Azerbaijan (major launch event in Baku, May 2026).

TECH STACK (do not deviate):
- Next.js 14 App Router, TypeScript strict
- Tailwind CSS 4 (CSS-first, no tailwind.config.js)
- shadcn/ui components
- Framer Motion for animations
- Recharts for data visualization
- react-i18next for all text strings

DESIGN PRINCIPLES:
- Clean, premium, trust-inspiring — this is a professional credential platform, not a casual app
- Mobile-first, PWA-ready
- Dark mode support (use CSS variables, not hardcoded colors)
- Minimal chrome, content-forward

BRAND TOKENS (already defined in globals.css — use these CSS variables):
--color-brand: #6366f1         (indigo — primary accent)
--color-brand-light: #818cf8
--color-brand-dark: #4f46e5

Badge tier colors:
--color-aura-platinum: #a78bfa  (violet)
--color-aura-gold: #facc15      (yellow)
--color-aura-silver: #94a3b8    (slate)
--color-aura-bronze: #d97706    (amber)

Font: Inter (already loaded)

COMPONENT RULES:
- Use shadcn/ui Card, Button, Input, Badge, Progress, Separator, Avatar, Tabs
- Use cn() utility for conditional classes
- All user-facing text must use the t() function (react-i18next) — leave placeholder strings like t("key.here")
- "use client" only when hooks/events are needed
- No hardcoded colors — use Tailwind semantic classes or CSS variables

LAYOUT:
- Authenticated pages: fixed left sidebar (w-56) + main content area with top bar
- Auth pages: centered card on gradient background
- Public pages: no sidebar, minimal top nav

OUTPUT FORMAT:
- Single .tsx file per component/page
- No separate CSS files
- Import from @/ alias
- Include TypeScript interfaces above the component
```

---

## 2. Цветовая система и токены

| Токен | Значение | Применение |
|---|---|---|
| `bg-background` | oklch(1 0 0) → белый | Основной фон |
| `bg-card` | oklch(1 0 0) | Карточки |
| `text-foreground` | oklch(0.145 0 0) → почти чёрный | Основной текст |
| `text-muted-foreground` | oklch(0.556…) → серый | Второстепенный текст |
| `bg-primary` / `text-primary` | oklch(0.205…) → тёмно-синий | Кнопки, акценты |
| `border-border` | oklch(0.922…) → светло-серый | Границы карточек |
| `#6366f1` (brand) | Indigo | Логотип, главный акцент |
| `#a78bfa` | Violet | Platinum badge |
| `#facc15` | Yellow | Gold badge |
| `#94a3b8` | Slate | Silver badge |
| `#d97706` | Amber | Bronze badge |

**Dark mode** — все переменные автоматически переключаются через класс `.dark`.

---

## 3. Карта экранов

```
/ (landing)
├── /(auth)
│   ├── /login
│   ├── /signup
│   └── /callback
├── /(dashboard)  [requires auth, sidebar layout]
│   ├── /dashboard          ← главная
│   ├── /profile            ← редактирование профиля
│   ├── /aura               ← AURA-счёт + radar chart
│   ├── /assessment         ← прохождение теста
│   ├── /events             ← список мероприятий
│   └── /settings           ← настройки аккаунта
└── /(public)
    └── /u/[username]       ← публичная страница волонтёра
        └── /card           ← OG-image (edge route, НЕ нужен дизайн)
```

---

## 4. Промпты для каждого экрана

---

### 4.1 Landing Page

**Файл:** `apps/web/src/app/[locale]/page.tsx`

```
Design a premium landing page for Volaura — "The elite platform for verified volunteers."

LAYOUT (single page, no sidebar):
- Top navigation bar: logo "VOLAURA" left (indigo, bold), right side: "Log In" (ghost button) + "Get Started" (primary button)
- Hero section (full viewport height):
  - Large headline: "Prove Your Talent. Earn Your AURA." (gradient text: indigo → violet)
  - Subheadline: "The elite platform for verified volunteers. Complete your assessment, earn your badge, and connect with top event organizers."
  - Two CTAs: "Get Started →" (primary, large) + "For Organizations" (outlined)
  - Background: subtle dark radial gradient from center, with faint animated floating orbs in indigo/violet (use Framer Motion)

- Features strip (3 cards, dark background section):
  Card 1 — "Verified Assessment": IRT-powered adaptive testing across 8 competencies
  Card 2 — "AURA Score": Composite score with radar chart visualization and badge tiers (Platinum/Gold/Silver/Bronze)
  Card 3 — "Trusted by Organizers": Connect with top organizations at major launch events

- Social proof section: "Launching at our major event — Baku, May 2026"
  - Show 4 badge tier cards (Platinum, Gold, Silver, Bronze) with colored borders and score ranges
  - Platinum ≥90 (violet), Gold ≥75 (yellow), Silver ≥60 (slate), Bronze ≥40 (amber)

- CTA footer banner: dark background, large text "Ready to earn your AURA?", primary button

- Footer: minimal, "© 2026 Volaura · volaura.az · Azerbaijan"

STYLE: Dark hero section (near-black gradient), light features section, alternating rhythm. Premium feel — think Linear.app or Vercel.com aesthetics.
```

---

### 4.2 Auth Layout

**Файл:** `apps/web/src/app/[locale]/(auth)/layout.tsx`

```
Design an authentication layout wrapper for Volaura.

Structure:
- Full viewport height, centered content
- Background: dark gradient (from #0f0f1a to #1a1a2e) with subtle indigo glow in top-left corner
- Centered white card (max-w-md, rounded-2xl, shadow-2xl, border border-border/20)
- Card header: "VOLAURA" logo centered in indigo (#6366f1), bold, letter-spacing wider
- Below logo: slot for page content ({children})
- Card footer: subtle text "Secure · Verified · Trusted"

The card should feel like a premium credential portal — clean, minimal, no noise.
```

---

### 4.3 Login Page

**Файл:** `apps/web/src/app/[locale]/(auth)/login/page.tsx`

```
Design a login form page for Volaura (renders inside the auth layout card).

Content:
- Title: "Welcome back" (semibold, center)
- Subtitle: "Sign in to your volunteer account" (muted, small, center)
- Email input (full width, shadcn Input)
- Password input (full width, with show/hide toggle icon button)
- "Forgot password?" link (right-aligned, small, muted)
- Primary submit button "Log in" (full width, loading spinner state)
- Error state: red alert box with error message (shadcn Alert with destructive variant)
- Divider: "or continue with"
- Google OAuth button (white, bordered, Google icon + "Sign in with Google")
- Bottom link: "Don't have an account? Sign up →"

States to show: default, loading (button spinner), error (email/password wrong).
Use React Hook Form patterns (register, handleSubmit, formState.errors).
```

---

### 4.4 Signup Page

**Файл:** `apps/web/src/app/[locale]/(auth)/signup/page.tsx`

```
Design a signup form page for Volaura (renders inside the auth layout card).

Content:
- Title: "Create your account"
- Subtitle: "Start your volunteer journey"
- Fields:
  1. Full Name (text input)
  2. Username (text input, with "@" prefix indicator, lowercase only, shows availability check ✓/✗)
  3. Email (email input)
  4. Password (password input with strength indicator bar: 4 segments, colors: red/orange/yellow/green)
  5. Confirm Password
- Terms checkbox: "I agree to the Terms of Service and Privacy Policy" (links)
- Submit button "Create account" (full width, primary, loading state)
- Error alert (destructive)
- Bottom link: "Already have an account? Log in"

Show username availability as a subtle inline status (spinner → green check → red x).
```

---

### 4.5 Dashboard Shell Layout (Sidebar + TopBar)

**Файл:** `apps/web/src/app/[locale]/(dashboard)/layout.tsx`

```
Design the authenticated dashboard shell layout for Volaura.

Structure:
- Fixed left sidebar (w-56, full height, border-r)
  - Logo: "VOLAURA" in indigo (#6366f1), bold, with a small lightning bolt ⚡ icon, clickable → dashboard
  - Navigation items (icons + labels):
    ⊞ Dashboard
    ◉ Profile
    ◈ AURA Score
    ◑ Assessment
    ◎ Events
    ◧ Settings
  - Active state: indigo background pill (bg-indigo-50, text-indigo-700 in light / bg-indigo-950 in dark)
  - Hover state: subtle bg-accent
  - Bottom of sidebar: user avatar + name + email (truncated), and "Log out" button (destructive hover)

- Top bar (h-14, border-b, sticky):
  - Left: current page title (h3, semibold)
  - Right: language switcher (AZ | EN toggle), notification bell icon (shadcn Badge for count), user avatar

- Main content area: flex-1, overflow-y-auto, bg-background

- Mobile: sidebar collapses to bottom navigation bar (5 main items as icons only)

Use shadcn Tooltip for collapsed sidebar item labels on mobile.
```

---

### 4.6 Dashboard Home

**Файл:** `apps/web/src/app/[locale]/(dashboard)/dashboard/page.tsx`

```
Design the main volunteer dashboard page for Volaura.

Content sections:

1. WELCOME HEADER:
   "Welcome back, {name}!" (2xl bold)
   "Here's your volunteer dashboard." (muted)

2. STATS GRID (3 cards, responsive 1→3 columns):
   Card A — AURA Score:
     Label: "AURA Score"
     Value: "78.4" (3xl bold)
     Sub: "Gold badge" (colored in gold #facc15)
     Trend: "+3.2 from last assessment" (green, small)

   Card B — Assessments Completed:
     Label: "Assessments"
     Value: "3"
     Sub: "Next: Leadership module"
     Progress bar showing 3/8 competencies assessed

   Card C — Events Attended:
     Label: "Events"
     Value: "5"
     Sub: "0 no-shows · Reliable ✓" (green checkmark)

3. AURA RADAR PREVIEW (card, full width on mobile, 2/3 on desktop):
   Title: "Competency Snapshot"
   Recharts radar chart (small size, 8 axes for 8 competencies)
   "View full breakdown →" link
   Badge displayed: Gold tier with colored border

4. QUICK ACTIONS (2×2 grid of action cards):
   - "Take Assessment →" (primary, with progress ring showing 3/8 done)
   - "View AURA Score →"
   - "Browse Events →"
   - "Share Your AURA →" (with a share icon)

5. RECENT ACTIVITY FEED (list):
   - "Completed Communication assessment · Score: 82 · 2 days ago"
   - "Attended WUF Volunteer Day · Rated 5/5 · 1 week ago"
   - "AURA recalculated · Gold badge earned · 1 week ago"

Loading skeleton states for all data-fetched sections.
```

---

### 4.7 Profile Page

**Файл:** `apps/web/src/app/[locale]/(dashboard)/profile/page.tsx`

```
Design the volunteer profile edit page for Volaura.

Two-column layout on desktop (1 col on mobile):
Left column (1/3): Profile card preview
Right column (2/3): Edit form

LEFT — PROFILE PREVIEW CARD:
- Avatar (large, 96px, circular, with upload overlay on hover — camera icon)
- Display name (bold, lg)
- @username (muted, sm)
- Badge tier chip: "🥇 Gold" with colored background
- AURA score: "78.4" prominently
- Location: "Baku, Azerbaijan" with flag emoji
- Bio (2-3 lines, truncated)
- "View public profile →" link

RIGHT — EDIT FORM:
Sections with shadcn Separator between them:

Personal Info:
- Avatar upload (drag & drop zone, shows preview)
- Display Name (text input)
- Username (with @, shows availability)
- Bio (textarea, 160 char limit with counter)
- Location (text input)
- Phone (tel input, optional)

Professional Info:
- Areas of Expertise (multi-select chips: Event Management, Translation, Tech Support, etc.)
- Languages (multi-select: Azerbaijani, English, Russian, Turkish)
- Years of volunteer experience (number input)
- LinkedIn URL (optional)

Preferences:
- Notification preferences (email/telegram toggles)
- Profile visibility (Public / Only to verified organizations / Private) — shadcn RadioGroup

Save button (primary, fixed to bottom on mobile, sticky).
Show unsaved changes badge in top bar when form is dirty.
```

---

### 4.8 AURA Score Page

**Файл:** `apps/web/src/app/[locale]/(dashboard)/aura/page.tsx`

```
Design the AURA Score detail page for Volaura — the centrepiece of the product.

This page is the most important in the app. It should feel like a premium credential certificate.

LAYOUT: Single column, max-w-2xl, centered.

SECTION 1 — SCORE HERO:
- Large score display: "78.4" (6xl, bold, colored in badge color)
- Badge tier badge: "🥇 GOLD" (large chip with gold border and background glow)
- Elite status ribbon if applicable: "⭐ Elite Volunteer" (shimmer animation)
- Score range hint: "Top 15% of volunteers"
- Two stats inline: "5 events · Reliability: Excellent"

SECTION 2 — RADAR CHART CARD:
- Card title: "Competency Radar"
- Full-size Recharts RadarChart (300px height)
  - 8 axes: Communication, Reliability, English, Leadership, Event Performance, Tech Literacy, Adaptability, Empathy & Safeguarding
  - Fill color matches badge tier (violet/gold/silver/amber/indigo)
  - Subtle fill opacity 0.2, stroke 2px

SECTION 3 — COMPETENCY BREAKDOWN:
- List of 8 competencies, each row:
  - Name (left, semibold)
  - Score/100 + weight% (right, muted)
  - Progress bar (full width, colored)
  - Small LLM-generated insight text (italic, muted, 1 line): e.g. "Strong communicator, top 10% in written expression"

Weights displayed:
Communication 20% · Reliability 15% · English 15% · Leadership 15% · Event Performance 10% · Tech Literacy 10% · Adaptability 10% · Empathy 5%

SECTION 4 — SHARE YOUR AURA:
- Card with gradient background (indigo→violet, dark)
- Title: "Share your verified score"
- Subtitle: "Let organizations discover your talent"
- 3 share format buttons:
  LinkedIn Post (1200×630) — primary blue
  Instagram Story (1080×1920) — gradient pink
  Square Post (1080×1080) — indigo
- Copy profile link button: "volaura.az/u/username ⎘"
- Telegram share button

SECTION 5 — BADGE HISTORY (timeline):
- Timeline list showing when each badge was earned
- E.g.: "Gold badge earned · March 2026", "Silver badge earned · January 2026"

EMPTY STATE (no assessments yet):
Full-page empty state with illustrated icon (◈ large),
"Your AURA score will appear here after your first assessment."
CTA: "Start Assessment →"
```

---

### 4.9 Assessment Flow

**Файл:** `apps/web/src/app/[locale]/(dashboard)/assessment/page.tsx`
**Файл:** `apps/web/src/components/features/assessment/question-card.tsx`

```
Design the adaptive assessment flow for Volaura. This is an IRT/CAT-powered test.

SCREEN A — Assessment Hub:
- Title: "Your Assessments"
- Competency grid (2×4 on desktop, 1×8 on mobile):
  Each competency card shows:
  - Icon + name (e.g., "💬 Communication")
  - Weight: "20% of AURA"
  - Status: Completed (green check + score "82/100") / In Progress (progress ring) / Not Started (gray)
  - CTA: "Continue →" or "Start →" or "Retake →"
- Overall progress bar: "3 of 8 competencies assessed"
- Note: "Assessments are adaptive — questions adjust to your level. Takes ~15 min per competency."

SCREEN B — Question Card (the core component):
Design a focused, distraction-free question interface:
- Top bar: competency name + question counter "Question 4 of ?" (IRT, so total unknown — show progress ring instead)
- Time indicator: subtle elapsed timer (not a countdown — just informational)
- LARGE question text (xl, semibold, generous line height)
- For BARS questions (behavioral): show a 7-point rating scale with anchors:
  1 = "Far below expectations" ... 7 = "Exemplary performance"
  Each option is a clickable card (highlights on select)
- For multiple choice: 4 options as large clickable cards (A B C D)
- For open text (LLM-evaluated): textarea with placeholder + word counter
- Navigation: "Previous" (ghost, left) + "Next / Submit" (primary, right)
- Quit confirmation modal on back navigation

SCREEN C — Assessment Complete:
- Celebration animation (confetti burst, Framer Motion)
- Competency score revealed: "Communication: 82/100" (large, animated counter)
- Progress update: "AURA score updated: 74.2 → 78.4 (+4.2)"
- Badge unlock animation if tier changed
- CTA: "View Full AURA Score" + "Continue to next assessment"
```

---

### 4.10 Events Page

**Файл:** `apps/web/src/app/[locale]/(dashboard)/events/page.tsx`

```
Design the events page for Volaura volunteers.

LAYOUT: Full width with filter sidebar on desktop, sheet on mobile.

FILTER SIDEBAR (left, w-64):
- Search input
- Date range picker
- Location (city dropdown)
- Required minimum AURA score (slider: 0–100)
- Status: Upcoming / Registration Open / Completed
- Organization (multi-select)

EVENTS LIST (main, grid 1→2→3 cols):
Each EVENT CARD shows:
- Event image (top, 16:9 ratio, placeholder gradient)
- Badge: "Registration Open" (green) / "Upcoming" (blue) / "Full" (red)
- Event name (bold, lg)
- Organization name (muted, sm, with verified checkmark ✓)
- Date + location (muted)
- Required AURA score badge: "Min AURA: 70 · Gold+" (colored)
- Volunteers needed count
- CTA: "Register →" (primary) — disabled if AURA too low with tooltip
- If registered: "Registered ✓" (green, disabled)

EMPTY STATE: "No events match your filters. Try adjusting your search."

REGISTRATION MODAL (sheet on mobile, dialog on desktop):
- Event details summary
- User's AURA score vs required (with visual comparison)
- Motivation text area
- Confirm Registration button
```

---

### 4.11 Settings Page

**Файл:** `apps/web/src/app/[locale]/(dashboard)/settings/page.tsx`

```
Design the settings page for Volaura.

Use shadcn Tabs for section navigation: Account | Notifications | Privacy | Danger Zone

TAB: Account
- Email address (read-only, with "Change" button that opens inline form)
- Password change form (current → new → confirm)
- Language preference (AZ / EN) with flag icons — shadcn Select
- Connected accounts: Google (connected ✓), Telegram (connect button)

TAB: Notifications
- Toggle list with descriptions:
  ✓ Assessment result emails
  ✓ New event opportunities matching your profile
  ✓ AURA score updates
  ✗ Weekly volunteer digest
  ✓ Telegram notifications (requires linking)
  ✓ Organization contact requests

TAB: Privacy
- Profile visibility (RadioGroup): Public / Organizations Only / Private
- AURA score visibility: Show full score / Show badge only / Hidden
- Allow organizations to find me via semantic search: toggle
- Data export: "Download my data" button (triggers CSV generation)

TAB: Danger Zone
- Red-bordered card
- "Delete Account" — confirmation dialog with username re-entry
- "Pause account for 30 days" option
```

---

### 4.12 Public Profile Page

**Файл:** `apps/web/src/app/[locale]/(public)/u/[username]/page.tsx`

```
Design the public volunteer profile page for Volaura.
URL: volaura.az/u/{username}

This is a shareable, public-facing credential page — like a verified LinkedIn profile but for volunteers.

No sidebar. Minimal top nav: "VOLAURA" logo left, "Log in" right.

LAYOUT: Centered, max-w-2xl, generous padding.

TOP SECTION — Identity:
- Avatar (96px, circular)
- Display name (2xl, bold)
- @username (muted)
- Location with flag: "🇦🇿 Baku, Azerbaijan"
- Badge tier (large chip): "🥇 GOLD — 78.4" with tier color glow/border
- Elite badge if applicable: "⭐ Elite Volunteer"
- Verified status: "✓ Identity Verified" (small green pill)

AURA SCORE CARD:
- Dark background (indigo→violet gradient), white text
- "AURA Score" label
- Large score: "78.4"
- Radar chart (small, 200px, matches badge color)
- Competency top 3 highlights: "Top: Communication · Leadership · English"

BIO SECTION:
- Short bio text
- Tags: areas of expertise as pills (Event Management, Translation, etc.)
- Languages: flag icons with language names

ASSESSMENTS SECTION:
- List of completed competency assessments with scores + dates
- LLM-generated 1-line insights for top 3

EVENT HISTORY (if public):
- List of attended events with organization names and ratings received

SHARE / CONNECT SECTION:
- "Share this profile" (copy link)
- "Download AURA Card" (PDF/image)
- For organizations: "Request this volunteer" CTA (prominent, requires org account)

META:
- OG tags in head: name, AURA score, badge tier, profile image
```

---

### 4.13 AURA Share Card (Visual Reference)

> **Примечание:** Сам `/u/[username]/card` — это Edge Route, возвращающий PNG через Satori. Дизайн реализован в коде. Используй этот промпт для создания **Framer Motion preview-компонента** для предпросмотра карточки перед скачиванием.

```
Design an AURA Card preview component for Volaura.

This is a visual "credential card" (aspect ratio 1200:630, scaled down to fit screen)
shown before the user downloads/shares their score card.

Card design (dark, premium):
- Background: dark gradient (#0f0f1a → #1a1a2e → #16213e)
- Top-left: "VOLAURA" in indigo, small, bold
- Center-top: volunteer's display name + @username
- HUGE score number (100px+, bold, colored in badge tier color)
- Badge label: "GOLD" in large uppercase, letter-spacing wide, same color + subtle text-shadow glow
- Elite ribbon if applicable
- Mini bar chart (8 bars for 8 competencies, colored)
- Bottom-right: "volaura.az"

The preview component should show this card with:
- Framer Motion fade-in animation
- Format selector tabs: LinkedIn / Story / Square (changes aspect ratio preview)
- Download button below
- "Generating..." loading skeleton state

Use the badge tier color as the primary accent throughout the card.
```

---

## 5. Компонентные промпты (переиспользуемые)

---

### 5.1 BadgeTierChip

```
Design a BadgeTierChip component for Volaura.

Props: tier ("platinum" | "gold" | "silver" | "bronze" | "none"), score?: number, size?: "sm" | "md" | "lg"

Visual design for each tier:
- Platinum: violet border (#a78bfa), violet text, subtle shimmer/glow animation
- Gold: amber/yellow border (#facc15), gold text, no animation
- Silver: slate border (#94a3b8), slate text
- Bronze: orange border (#d97706), orange text
- None: gray, muted

The chip shows: emoji medal + tier name + score if provided.
"⭐ PLATINUM · 92.1"
"🥇 GOLD · 78.4"
"🥈 SILVER · 64.2"
"🥉 BRONZE · 43.8"
"— No badge yet"

Sizes: sm = text-xs px-2 py-0.5, md = text-sm px-3 py-1, lg = text-base px-4 py-2
All have rounded-full, border, font-semibold.
```

---

### 5.2 CompetencyBar

```
Design a CompetencyBar component for Volaura showing a single competency score.

Props: name (string), score (0-100), weight (number = percentage), insight?: string, badgeTier?: string

Layout:
Row 1: [Name · bold, left] [score/100 · weight% · muted, right]
Row 2: Full-width progress bar (h-2, rounded-full)
         - Background: bg-muted
         - Fill: colored based on score (red <40, amber 40-60, yellow 60-75, green >75)
         - Animated width on mount (Framer Motion)
Row 3 (optional): insight text in italic muted (generated by LLM)

Show a small trophy icon next to the name if score > 80.
```

---

### 5.3 EmptyState

```
Design a reusable EmptyState component for Volaura.

Props: icon (string/emoji), title (string), description (string), ctaLabel?: string, ctaHref?: string

Layout: centered vertically and horizontally,
- Large icon (text-6xl)
- Title (xl, semibold)
- Description (muted, sm, max-w-xs, centered)
- Optional CTA button (primary)

Variants (pass via variant prop):
- "assessment" — icon ◈, "No AURA score yet"
- "events" — icon ◎, "No events found"
- "activity" — icon ○, "No activity yet"
```

---

### 5.4 LanguageSwitcher

```
Design a LanguageSwitcher component for Volaura.

Two locales: AZ (Azerbaijani, primary) and EN (English, secondary).

Compact toggle button: [🇦🇿 AZ] [🇬🇧 EN]
Active locale: white background, shadow, text-foreground
Inactive: muted text, transparent

On click: navigate to same page in other locale (Next.js router).
Placed in the dashboard top bar (right side) and auth pages (top-right corner).
```

---

## 6. User Flows (для reference)

### Flow A: New Volunteer
```
Landing → Sign Up → Dashboard (empty) → Take Assessment → AURA Score Page → Share Card
```

### Flow B: Returning Volunteer
```
Landing → Log In → Dashboard (with score) → Events → Register → Attend → Rating received → AURA updated
```

### Flow C: Organization finds Volunteer
```
/b2b/search → Filter by AURA ≥ 70 + competency → View public /u/[username] → Request Volunteer
```

---

## 7. Анимации (Framer Motion)

| Элемент | Анимация |
|---|---|
| Score hero number | `animate={{ opacity: 1 }}` + `useMotionValue` counter (0 → score) |
| Radar chart fill | CSS transition на opacity |
| Badge unlock | Scale 0 → 1.2 → 1.0, затем glow pulse |
| Assessment complete | Confetti: `framer-motion` + CSS particles |
| Competency bars | `width: 0% → score%`, delay по индексу |
| Page transitions | `AnimatePresence` + `fadeIn` от y: 8 |
| Card hover | `whileHover={{ y: -2, shadow-xl }}` |

---

## 8. Accessibility чеклист

- Все интерактивные элементы: `focus-visible` кольца через `ring-2 ring-ring`
- Контраст текста: не ниже AA (4.5:1) — badge цвета проверены
- `aria-label` на icon-only кнопках
- Загрузочные состояния: `aria-busy="true"` + скелетоны
- Переключатель языка: `lang` атрибут на `<html>`
- Радар-чарт: таблица-альтернатива с `sr-only` для screen readers

---

## 9. Файлы для передачи в v0.dev (приоритет)

| Приоритет | Экран | Сложность |
|---|---|---|
| 🔴 P0 | Landing page | Высокая — первое впечатление |
| 🔴 P0 | AURA Score page | Высокая — ключевой экран |
| 🔴 P0 | Dashboard home | Средняя |
| 🟡 P1 | Auth (Login/Signup) | Средняя |
| 🟡 P1 | Assessment flow | Высокая |
| 🟡 P1 | Public profile /u/[username] | Средняя |
| 🟢 P2 | Profile edit | Средняя |
| 🟢 P2 | Events page | Средняя |
| 🟢 P2 | Settings | Низкая |
| 🟢 P2 | AURA Card preview | Низкая |

---

*Документ подготовлен для передачи дизайна в v0.dev. После генерации компонентов — вставляйте код в соответствующие файлы `apps/web/src/` и запускайте `pnpm dev` для проверки.*
