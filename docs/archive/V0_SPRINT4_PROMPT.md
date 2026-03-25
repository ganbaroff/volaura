# v0.dev Prompt — Sprint 4: Identity + i18n + Missing Components

## Instructions

Copy EVERYTHING between ---START--- and ---END--- into a NEW v0.dev chat as a single message.

---START---

I'm building Volaura — a verified volunteer credential platform (Next.js 14, Tailwind CSS 4, shadcn/ui, Recharts, Lucide icons). You already built the base app for me. Now I need Sprint 4 — improvements and missing components.

Same design system:
- Primary: #6366F1 (indigo). Dark bg: #0B1120 (deep navy). Light bg: #FAFBFC.
- Badge tiers: platinum=#A78BFA, gold=#EAB308, silver=#94A3B8, bronze=#D97706
- Border radius: 0.75rem. Font: Inter.
- Use shadcn/ui (Card, Button, Input, Badge, Tabs, Dialog, Sheet, Avatar, Select, RadioGroup, Switch, Separator, Tooltip)
- Use Lucide React for ALL icons
- All components "use client"

I need these 6 files. Generate ALL of them.

---

## FILE 1: Enhanced Profile Page (REPLACE existing profile/page.tsx)

File: `app/(dashboard)/profile/page.tsx`

The current profile page works but needs major UX improvements:

### LEFT COLUMN (1/3 on lg, full on mobile) — Live Preview Card

This card updates IN REAL TIME as the user types in the edit form on the right.

- Avatar: 96px circle with `border-4 border-background shadow-lg`
  - Hover overlay: semi-transparent dark overlay with Camera icon and "Change photo" text
  - Click opens file input (accept="image/*")
  - Show image preview immediately after file selection (URL.createObjectURL)
- Display name: text-xl font-bold (updates live as user types)
- "@username" in text-sm text-muted-foreground (updates live)
- BadgeTierChip size="md" showing "🥇 Gold · 78.4"
- Location with MapPin icon
- Bio text (2-3 lines, updates live, truncated with line-clamp-3)
- Stats row: "5 events · 3 assessments · Reliable ✓" in text-xs text-muted-foreground
- "View public profile →" link at bottom

### RIGHT COLUMN (2/3 on lg, full on mobile) — Edit Form

Sections with Separator between them:

**Section 1: Personal Information**
- Display Name — Input with User icon
- Username — Input with:
  - "@" prefix (absolute positioned text inside input, pl-8)
  - Lowercase enforcement (onChange: value.toLowerCase().replace(/[^a-z0-9_]/g, ""))
  - Async availability check with debounce (simulate 800ms delay):
    - Typing: Loader2 icon spinning (text-muted-foreground)
    - Available: CheckCircle icon (text-green-500) + "Available"
    - Taken: XCircle icon (text-red-500) + "Already taken"
- Bio — Textarea with character counter:
  - Max 160 characters
  - Counter: "42/160" in text-xs, turns amber at 120+, red at 150+
  - Positioned bottom-right of textarea
- Location — Input with MapPin icon
- Phone — Input with Phone icon, optional badge

**Section 2: Professional**
- Areas of Expertise — toggleable Badge chips in a flex-wrap container:
  Options: Event Management, Translation, Tech Support, Protocol, Logistics, Security, Media, First Aid
  - Selected: bg-primary text-primary-foreground
  - Unselected: variant="outline"
  - Click toggles selection
- Languages — same toggleable chips pattern:
  Options: Azərbaycan dili, English, Русский, Türkçe, العربية
  - Show flag emoji before each: 🇦🇿 🇬🇧 🇷🇺 🇹🇷 🇸🇦
- Years of Experience — Input type="number" min={0} max={30}
- LinkedIn URL — Input with ExternalLink icon, placeholder="https://linkedin.com/in/..."

**Section 3: Notification Preferences**
- 4 Switch toggles with labels and descriptions:
  1. "Assessment results" — "Get notified when your scores are ready"
  2. "Event opportunities" — "Matching events based on your AURA profile"
  3. "AURA updates" — "When your score is recalculated"
  4. "Organization requests" — "When an organization wants to connect"

**Section 4: Privacy**
- RadioGroup for profile visibility:
  - "Public" — "Anyone can view your profile and AURA score"
  - "Organizations only" — "Only verified organizations can see your full profile"
  - "Private" — "Your profile is hidden from search"

### Save Behavior
- "Unsaved changes" indicator: orange dot next to page title when form is dirty
- Compare initial state vs current state to detect dirty
- Save button:
  - Desktop: regular position at bottom of form
  - Mobile: sticky bottom-0 with bg-background/80 backdrop-blur, full-width button
  - States: "Save changes" → "Saving..." (spinner) → "Saved ✓" (2s, then revert)
- Discard button: ghost variant, resets form to initial state

---

## FILE 2: Language Switcher Component

File: `components/layout/language-switcher.tsx`

A compact locale toggle for the top bar.

Design: pill-shaped toggle with two options side by side

```
┌─────────────┐
│ [🇦🇿 AZ] [EN] │  ← AZ is active (filled)
└─────────────┘
```

- Container: `inline-flex rounded-full border border-border bg-muted/50 p-0.5`
- Each option: `px-3 py-1.5 rounded-full text-xs font-medium cursor-pointer transition-all`
- Active: `bg-background text-foreground shadow-sm`
- Inactive: `text-muted-foreground hover:text-foreground`
- Flag emoji before code: 🇦🇿 AZ and 🇬🇧 EN
- On click: call onLocaleChange(locale) prop
- Current locale from prop

Props:
```tsx
interface LanguageSwitcherProps {
  locale: "az" | "en"
  onLocaleChange: (locale: "az" | "en") => void
}
```

Small component, <50 lines.

---

## FILE 3: Notification Dropdown Component

File: `components/layout/notification-dropdown.tsx`

Replace the current basic notification bell with a rich dropdown.

### Bell Button
- Bell icon with red badge showing count (if > 0)
- Badge: `absolute -top-1 -right-1 w-4 h-4 rounded-full bg-red-500 text-[10px] text-white flex items-center justify-center`
- Subtle shake animation on new notification (CSS @keyframes shake)

### Dropdown Panel
- Use shadcn Popover (NOT DropdownMenu — we need richer content)
- Header: "Notifications" title + "Mark all read" link (right-aligned, text-xs text-primary)
- Scrollable list (max-h-80 overflow-y-auto)
- Each notification item:
  - Left: colored icon circle (bg-primary/10 text-primary for info, bg-green-500/10 for success, bg-amber-500/10 for warning)
  - Middle: title (font-medium text-sm) + description (text-xs text-muted-foreground) + time (text-xs text-muted-foreground)
  - Right: blue dot if unread
  - Hover: bg-accent/50
  - Click: navigates to relevant page
- Empty state: "No notifications yet" centered with BellOff icon
- Footer: "View all notifications →" link

### Mock Data (6 notifications):
1. 🟢 "Assessment Complete" — "Your Communication score is ready: 82/100" — "2 hours ago" — unread
2. 🔵 "New Event Available" — "Volunteer Corps is now accepting applications for upcoming event" — "5 hours ago" — unread
3. 🟡 "AURA Updated" — "Your AURA score increased to 78.4 (+4.2)" — "1 day ago" — unread
4. 🟢 "Registration Confirmed" — "You're registered for Event Prep Day" — "2 days ago" — read
5. 🔵 "New Assessment" — "Leadership assessment is now available" — "3 days ago" — read
6. 🟡 "Organization Interest" — "AzVolunteer viewed your profile" — "1 week ago" — read

Props:
```tsx
interface Notification {
  id: string
  type: "success" | "info" | "warning"
  title: string
  description: string
  time: string
  read: boolean
  href: string
}
```

---

## FILE 4: Onboarding Flow Component

File: `components/features/onboarding/onboarding-flow.tsx`

A first-time user experience wizard shown after signup. Multi-step modal/fullscreen.

### Step 1: Welcome
- Large "Welcome to Volaura! 👋" title
- "Let's set up your volunteer profile in 2 minutes."
- Illustration: Hexagon icon (text-6xl text-primary) with subtle glow
- "Let's go →" primary button

### Step 2: Basic Info
- Avatar upload (circular drop zone, click to upload)
- Display Name input
- Location select (Baku, Ganja, Sumgait, Other)
- "Continue →" button

### Step 3: Skills & Languages
- Expertise chips (toggleable, same as profile page): Event Management, Translation, Tech Support, Protocol, Logistics, Security, Media, First Aid
- Language chips with flags: 🇦🇿 Azərbaycan dili, 🇬🇧 English, 🇷🇺 Русский, 🇹🇷 Türkçe
- "Continue →" button

### Step 4: Ready to Start
- "You're all set! 🎉" large title
- Mini preview card showing their profile (avatar + name + location + selected skills)
- "Your first step: take an assessment to earn your AURA score."
- Two buttons: "Take Assessment →" (primary) + "Go to Dashboard" (outline)

### Layout
- Fullscreen overlay (fixed inset-0 z-50 bg-background)
- Centered content (max-w-md)
- Step indicator at top: 4 dots with connecting lines (filled = completed, outline = current, muted = upcoming)
- Smooth transition between steps (opacity + translateX slide)
- Step indicator: `flex items-center gap-2` with `w-2 h-2 rounded-full` dots

### Props:
```tsx
interface OnboardingFlowProps {
  onComplete: (data: {
    displayName: string
    location: string
    expertise: string[]
    languages: string[]
    avatarFile?: File
  }) => void
  onSkip: () => void
}
```

Include "Skip for now" link at bottom of each step.

---

## FILE 5: Loading Skeletons for Key Pages

File: `components/ui/page-skeletons.tsx`

Export multiple skeleton components for loading states:

### DashboardSkeleton
- Welcome section: `h-8 w-64 rounded bg-muted animate-pulse` for title, `h-4 w-48` for subtitle
- Stats grid: 4 cards, each with `h-24 rounded-xl bg-muted animate-pulse`
- Chart area: `h-64 rounded-xl bg-muted animate-pulse`
- Quick actions: 4 cards, `h-20 rounded-xl bg-muted animate-pulse`

### AuraPageSkeleton
- Score: centered `h-20 w-32 rounded bg-muted animate-pulse`
- Badge chip: `h-8 w-24 rounded-full bg-muted animate-pulse`
- Radar chart: `h-80 rounded-xl bg-muted animate-pulse`
- Competency bars: 8 rows of `h-12 rounded bg-muted animate-pulse` with stagger delay

### ProfileSkeleton
- Left card: Avatar circle + 3 text lines
- Right form: 6 input skeletons

### EventsSkeleton
- Search bar skeleton
- 6 event card skeletons (image + 3 text lines)

All skeletons use:
- `animate-pulse` base
- Stagger pattern using `style={{ animationDelay: "${index * 100}ms" }}`
- Rounded corners matching actual content
- Export as named exports: `DashboardSkeleton`, `AuraPageSkeleton`, `ProfileSkeleton`, `EventsSkeleton`

---

## FILE 6: 404 Not Found Page

File: `app/not-found.tsx`

A styled 404 page matching the Volaura brand.

- Dark gradient background (same as auth layout: #0B1120 → #0F1729)
- Centered content:
  - "404" in text-[120px] font-black, gradient text (indigo → violet), opacity 0.3
  - "Page not found" in text-2xl font-semibold text-white
  - "The page you're looking for doesn't exist or has been moved." in text-muted-foreground
  - Two buttons: "Go to Dashboard" (primary) + "Go Home" (outline)
- FloatingOrbs (if available) or 2 CSS blur circles for atmosphere
- VOLAURA logo top-left, small, text-primary

---

IMPORTANT: Generate ALL 6 files. Use the same design system, same component imports, same styling patterns as the existing app. Every file should be "use client" and fully typed with TypeScript.

---END---
