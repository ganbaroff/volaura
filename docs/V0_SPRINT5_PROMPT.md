# v0.dev Prompt — Sprint 5: Landing V2 + Final Polish

## Instructions

Copy EVERYTHING between ---START--- and ---END--- into a NEW v0.dev chat as a single message.

---START---

I'm building Volaura — a verified volunteer credential platform (Next.js 14, Tailwind CSS 4, shadcn/ui, Recharts, Lucide icons). You already built the full app for me across 3 sprints. Now I need the FINAL sprint — Landing page V2 and polish components.

Same design system:
- Primary: #6366F1 (indigo). Dark bg: #0B1120 (deep navy). Light bg: #FAFBFC.
- Badge tiers: platinum=#A78BFA, gold=#EAB308, silver=#94A3B8, bronze=#D97706
- Border radius: 0.75rem. Font: Inter.
- shadcn/ui + Lucide React icons. "use client" on all.

Generate ALL 5 files below.

---

## FILE 1: Landing Page V2 (REPLACE existing app/page.tsx)

File: `app/page.tsx`

The current landing page is decent but needs to be WORLD CLASS for platform launch. Reference: Linear.app + Vercel.com + Stripe.com aesthetic.

### SECTION 1 — Fixed Navigation (h-16)
- Transparent on top, transitions to `bg-background/80 backdrop-blur-xl border-b border-border` on scroll (use useState + useEffect with scroll listener, threshold 50px)
- Left: "VOLAURA" logo in text-lg font-bold text-primary tracking-wider
- Right desktop (hidden md:flex): "Features" "How it Works" "For Organizations" (ghost links, scroll-to-section) + "Log In" (ghost) + "Get Started" (primary button with shadow glow: shadow-[0_0_20px_rgba(99,102,241,0.3)])
- Right mobile (md:hidden): hamburger Sheet with same links stacked vertically

### SECTION 2 — Hero (min-h-screen, dark gradient bg)
- Background: `bg-gradient-to-b from-[#0B1120] via-[#0F1729] to-[#0B1120]`
- 3 floating orbs (CSS animation, pointer-events-none):
  - Orb 1: w-[400px] h-[400px] bg-indigo-500/10 blur-[100px] top-1/4 left-1/4, float animation 20s
  - Orb 2: w-[300px] h-[300px] bg-violet-500/8 blur-[80px] top-1/3 right-1/4, float 25s reverse
  - Orb 3: w-[200px] h-[200px] bg-blue-500/6 blur-[60px] bottom-1/3 left-1/3, float 18s

- Centered content (max-w-3xl mx-auto text-center):
  - Eyebrow: "🚀 Join the verified volunteer community" — small Badge variant="outline" with subtle border-primary/30
  - Headline: "Prove Your Talent. Earn Your AURA." — text-5xl md:text-7xl font-black, gradient text:
    `bg-gradient-to-r from-white via-indigo-200 to-violet-300 bg-clip-text text-transparent`
  - Subtitle: "The elite platform for verified volunteers. Complete your assessment, earn your badge, and connect with top event organizers." — text-lg md:text-xl text-slate-400 max-w-xl mx-auto mt-6
  - CTA row (mt-8 flex gap-4 justify-center):
    - "Get Started →" — Button size="lg" with glow shadow + hover scale-105 transition
    - "For Organizations" — Button variant="outline" size="lg" border-slate-700 text-slate-300 hover:bg-slate-800
  - Trust line (mt-12): "Trusted by 500+ volunteers across Azerbaijan" — text-sm text-slate-500 with 5 small avatar circles overlapping (fake social proof)

- Scroll indicator (absolute bottom-8, center):
  - ChevronDown icon, animate-bounce, text-slate-500, opacity fades on scroll

### SECTION 3 — Features (py-24, bg shifted to lighter dark: #111827)
- Section title: "Everything you need to stand out" — text-3xl font-bold text-white text-center
- Subtitle: "From assessment to credential to opportunity" — text-slate-400 text-center

- 3 feature cards in grid (md:grid-cols-3 gap-8, max-w-5xl mx-auto):

  Card 1: "Verified Assessment"
  - Icon: ClipboardCheck in a circle (w-12 h-12 rounded-xl bg-indigo-500/10 text-indigo-400)
  - Title: "Adaptive Testing" text-lg font-semibold text-white
  - Description in text-slate-400
  - Mini bullet list (text-sm text-slate-500): "IRT-powered questions" · "8 competencies" · "~15 min each"

  Card 2: "AURA Score"
  - Icon: Hexagon
  - Title: "Your Verified Credential"
  - Desc + bullets: "Composite score" · "Radar chart" · "4 badge tiers"

  Card 3: "Matched to Events"
  - Icon: Users
  - Title: "Connect with Organizers"
  - Desc + bullets: "Dynamic event matching" · "Smart matching" · "Verified profiles"

  Each card: `bg-slate-900/50 border border-slate-800 rounded-2xl p-6 hover:border-slate-700 transition-colors`

### SECTION 4 — Interactive AURA Demo (py-24, bg: #0B1120)
- Title: "See your potential AURA score" — text-3xl font-bold text-white text-center
- Subtitle: "This is what a Gold-tier volunteer profile looks like" — text-slate-400

- Centered card (max-w-lg mx-auto): dark bg-slate-900/80 border-slate-800 rounded-2xl p-8
  - Score: "78.4" in text-5xl font-bold text-yellow-400 (gold)
  - Badge: "🥇 GOLD" chip
  - Radar chart (size "sm", gold colors) with demo data
  - Below chart: "Based on 8 verified competencies" text-xs text-slate-500

- CTA below card: "Start your assessment to get your real score →" Button primary

### SECTION 5 — Badge Tiers (py-24, bg: #111827)
- Title: "Four tiers of verified excellence"
- 4 cards in a row (md:grid-cols-4 gap-4):

  Platinum card: border-violet-500/30, bg-violet-500/5
  - "🏆 Platinum" text-violet-400 font-bold
  - "Score ≥ 90"
  - "Top 5% — Elite volunteer status"
  - Subtle shimmer animation on border

  Gold card: border-yellow-500/30, bg-yellow-500/5
  - "🥇 Gold" text-yellow-400
  - "Score ≥ 75"
  - "Proven skills across competencies"

  Silver card: border-slate-400/30, bg-slate-400/5
  - "🥈 Silver" text-slate-400
  - "Score ≥ 60"
  - "Solid foundation, growing skills"

  Bronze card: border-amber-600/30, bg-amber-600/5
  - "🥉 Bronze" text-amber-500
  - "Score ≥ 40"
  - "Starting your volunteer journey"

### SECTION 6 — How It Works (py-24, bg: #0B1120)
- Title: "How it works"
- 3 steps in a row (md:grid-cols-3):
  Step 1: number "01" in text-5xl font-black text-indigo-500/20 + "Sign Up" title + description
  Step 2: "02" + "Take Assessments" + description
  Step 3: "03" + "Earn & Connect" + description
  Connecting line between steps on desktop: `border-t-2 border-dashed border-slate-800`

### SECTION 7 — Upcoming Events (py-20, bg: gradient indigo-to-violet, vibrant)
- `bg-gradient-to-r from-indigo-600 to-violet-600`
- "Upcoming Verified Volunteer Events" in text-2xl font-bold text-white
- Event countdown timer (if events exist from DB): 4 boxes (days, hours, minutes, seconds) — each in bg-white/10 rounded-lg p-4
  - Number: text-3xl font-bold text-white
  - Label: text-xs text-indigo-200 uppercase
  - Target date: calculated from next upcoming event in database (or fallback placeholder date)
  - Use useEffect + setInterval, update every second
- "Explore events →" Button, white bg, text-indigo-600
- Fallback: If no events scheduled, show "Check back soon for upcoming volunteer opportunities" message

### SECTION 8 — CTA Footer (py-24, bg: #0B1120)
- "Ready to earn your AURA?" in text-4xl font-bold text-white text-center
- "Join verified volunteers ready for your next opportunity" in text-slate-400
- "Get Started — it's free" Button size="lg" primary with glow

### SECTION 9 — Footer (py-12, border-t border-slate-800)
- 3 columns: Product (Dashboard, Assessment, Events), Company (About, Blog, Contact), Legal (Privacy, Terms, Cookies)
- Bottom: "© 2026 Volaura · Built in Azerbaijan 🇦🇿" text-sm text-slate-600
- Socials: Telegram, LinkedIn, Instagram icons (Ghost buttons)

### Performance Notes:
- Intersection Observer or scroll listener for nav background transition
- Countdown: setInterval clearing on unmount
- Orbs: pure CSS animations (no JS)
- All links scroll smoothly to section (id anchors + scroll-behavior: smooth)

---

## FILE 2: Enhanced Top Bar with Language Switcher and Notifications

File: `components/layout/top-bar-v2.tsx`

Replace the current top-bar with an improved version that includes:

- Sticky: `sticky top-0 z-40 bg-background/80 backdrop-blur-xl border-b border-border`
- Height: h-14
- Left side:
  - SidebarTrigger button (hamburger icon, existing pattern)
  - Page title (text-lg font-semibold) — pass as prop
  - Breadcrumb support (optional): "Dashboard > AURA Score" for nested pages
- Right side (flex items-center gap-2):
  1. Language Switcher — compact pill toggle [🇦🇿 AZ] [EN]
     - Active: bg-background shadow-sm text-foreground rounded-full
     - Inactive: text-muted-foreground
     - Container: bg-muted/50 border border-border rounded-full p-0.5
  2. Notification Bell — popover with dropdown
     - Bell icon (20px)
     - Red badge with count if unread > 0
     - Popover content: list of 6 notifications with icons, titles, times
     - "Mark all read" action
     - Empty state
  3. User Avatar (32px) — DropdownMenu with:
     - Header: name + email
     - Items: "View Profile", "Settings", separator, "Log Out" (text-destructive)

Props:
```tsx
interface TopBarV2Props {
  title?: string
  breadcrumbs?: { label: string; href: string }[]
}
```

Include all notification mock data inline. The component should be self-contained.

---

## FILE 3: Event Countdown Widget Component

File: `components/features/countdown.tsx`

A reusable countdown timer component for upcoming events.

Target: Accepts a dynamic `targetDate` prop from event data. Defaults to a placeholder date if none provided.

Display:
```
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│  64  │ │  12  │ │  34  │ │  56  │
│ days │ │hours │ │ mins │ │ secs │
└──────┘ └──────┘ └──────┘ └──────┘
```

- Each box: `bg-white/10 backdrop-blur rounded-xl p-3 md:p-4 min-w-[64px] text-center`
- Number: `text-2xl md:text-3xl font-bold text-white tabular-nums`
- Label: `text-[10px] md:text-xs text-indigo-200 uppercase tracking-wider mt-1`
- Separator between boxes: ":" in text-2xl font-bold text-white/30

- Seconds flip animation: when second changes, subtle scale pulse (CSS transition)
- Use useEffect + setInterval(1000), clean up on unmount
- If past target date: show "🎉 Event is happening NOW!" message instead

Two variants via `variant` prop:
- "hero" — large, for landing page (default)
- "compact" — smaller, for dashboard widget or banner

Props:
```tsx
interface CountdownProps {
  targetDate: Date // required: event date from database or props
  eventName?: string // optional: event title for the "NOW" message
  variant?: "hero" | "compact"
  className?: string
}
```

---

## FILE 4: Mobile App Shell Improvements

File: `components/layout/bottom-nav-v2.tsx`

Replace the current bottom-nav with an improved version:

- Fixed bottom, full width, md:hidden
- `bg-background/90 backdrop-blur-xl border-t border-border`
- `pb-[env(safe-area-inset-bottom)]` for iPhone safe area
- Height: h-16 (content) + safe area

5 items (NOT 6 — Settings goes inside Profile):
1. LayoutDashboard — "Home"
2. Hexagon — "AURA"
3. ClipboardCheck — "Assess" (center, slightly elevated or primary-colored)
4. Calendar — "Events"
5. User — "Profile"

Each item:
- `flex flex-col items-center justify-center gap-0.5`
- Icon: 20px
- Label: text-[10px] font-medium
- Active: text-primary, icon has subtle bg-primary/10 rounded-lg p-1.5
- Inactive: text-muted-foreground
- Tap feedback: active:scale-95 transition

Center item (Assess) special treatment:
- Slightly larger icon circle (w-10 h-10 rounded-full bg-primary text-white -mt-3 shadow-lg)
- Makes it the prominent CTA in the nav
- Label "Assess" in text-primary font-semibold

Add a subtle top progress bar showing AURA completion:
- `h-0.5 bg-primary` width proportional to competencies completed (3/8 = 37.5%)
- Positioned at very top of the nav bar

---

## FILE 5: Toast Notification Styles

File: `components/ui/volaura-toast.tsx`

Custom styled toasts for Volaura using sonner/shadcn toast system.

Export helper functions for common toast patterns:

```tsx
// Success toast with confetti icon
export function toastAssessmentComplete(competency: string, score: number) {}

// Info toast
export function toastAuraUpdated(oldScore: number, newScore: number) {}

// Success toast for event registration
export function toastEventRegistered(eventName: string) {}

// Warning toast
export function toastAuraInsufficient(required: number, current: number) {}

// Success toast for profile save
export function toastProfileSaved() {}

// Info toast for link copied
export function toastLinkCopied() {}

// Error toast
export function toastError(message: string) {}
```

Each function calls `toast()` from sonner with:
- Custom icon (colored circle with Lucide icon inside)
- Title (bold)
- Description (muted)
- Duration: 4000ms for info, 5000ms for success, 6000ms for error
- Position: "bottom-right" on desktop, "top-center" on mobile

Visual style per type:
- Success: green left-border accent, CheckCircle icon in green
- Info: indigo left-border, Info icon in indigo
- Warning: amber left-border, AlertTriangle icon in amber
- Error: red left-border, XCircle icon in red

Example rendered toast:
```
┌─ ─────────────────────────────────┐
│ 🟢│ Assessment Complete!           │
│   │ Communication: 82/100          │
│   │                    [dismiss]   │
└───────────────────────────────────┘
```

---

IMPORTANT: Generate ALL 5 files. Same design system, same imports pattern. "use client" on all. Fully typed TypeScript. Responsive (360px → 1440px). Dark mode via CSS variables.

---END---
