# v0.dev Prompt — Sprint 3 Completion

## Instructions

Copy the ENTIRE content below (from "---START---" to "---END---") into a NEW v0.dev chat as a single message.

---START---

I need you to build the missing pages and components for my Volaura project. This is a verified volunteer credential platform (Next.js 14 + Tailwind CSS 4 + shadcn/ui + Recharts).

You already built Sprint 1-2 and parts of Sprint 3. Now I need these SPECIFIC missing pieces. Please generate ALL of them in one go.

## TECH CONTEXT (same as before)

- Next.js 14 App Router, TypeScript strict
- Tailwind CSS 4 with CSS variables (oklch)
- shadcn/ui components
- Recharts for charts
- Lucide React for icons
- Color tokens already defined:
  - Primary: #6366F1 (indigo), Dark bg: #0B1120
  - Badge: platinum=#A78BFA, gold=#EAB308, silver=#94A3B8, bronze=#D97706
  - Border radius: 0.75rem

---

## PIECE 1: AURA Score Page (THIS IS THE MOST IMPORTANT PAGE OF THE ENTIRE APP)

File: `app/(dashboard)/aura/page.tsx`

This is the centrepiece — where a volunteer sees their complete verified score. It should feel like a premium credential certificate.

Layout: single column, max-w-2xl mx-auto, p-6, space-y-8

### Section 1 — Score Hero
- HUGE score number: "78.4" in text-7xl font-black, colored by badge tier (gold = #EAB308)
- Below: BadgeTierChip showing "🥇 GOLD" in large size with subtle box-shadow glow (0 0 40px rgba(234,179,8,0.15))
- If elite: "⭐ Elite Volunteer" text with subtle shimmer animation
- Below: "Top 15% of volunteers" in text-sm text-muted-foreground
- Two inline stats: "5 events attended · Reliability: Excellent" separated by dot

### Section 2 — Radar Chart Card
- Card with title "Competency Radar" (uppercase tracking-wider text-sm font-semibold text-muted-foreground)
- Full Recharts RadarChart, height 320px, 8 axes:
  Comm, Reliability, English, Leadership, Events, Tech, Adaptability, Empathy
- Fill: gold color (#EAB308) at opacity 0.15, stroke gold at 2px
- PolarGrid with 4 concentric circles
- Custom tooltip showing full competency name + score on hover
- Use this mock data: { communication: 82, reliability: 71, english_proficiency: 89, leadership: 65, event_performance: 74, tech_literacy: 78, adaptability: 70, empathy_safeguarding: 85 }

### Section 3 — Competency Breakdown
- 8 rows, each showing:
  - Left: Lucide icon + competency name (font-medium) + weight %
  - Right: score/100 in tabular-nums text-muted-foreground
  - Below: progress bar (h-2 rounded-full) — fill colored by score:
    >=80 green (#10B981), >=60 yellow (#EAB308), >=40 orange (#D97706), <40 red (#EF4444)
  - Below bar (optional): italic insight text in text-xs text-muted-foreground
    Example: "Strong communicator, top 10% in written expression"
  - Trophy icon (12px, amber) next to name if score > 80
- Animate bars: transition-all duration-700 ease-out on width

Use these competencies and weights:
communication (20%), reliability (15%), english_proficiency (15%), leadership (15%), event_performance (10%), tech_literacy (10%), adaptability (10%), empathy_safeguarding (5%)

Use these Lucide icons: MessageCircle, Shield, Languages, Crown, Star, Laptop, RefreshCw, Heart

### Section 4 — Share Your AURA
- Card with dark gradient background (from-[#0B1120] to-[#1a1a3e]), white text
- Title: "Share your verified score"
- Subtitle: "Let organizations discover your talent"
- 3 format buttons in a row:
  - "LinkedIn" (blue bg)
  - "Story" (pink/gradient bg)
  - "Square" (indigo bg)
- Copy link button: "volaura.az/u/murad" with clipboard icon, shows "Copied!" on click
- Telegram share button with Telegram icon

### Section 5 — Badge History (Timeline)
- Simple vertical timeline with colored dots:
  - "🥇 Gold badge earned · March 2026" (gold dot)
  - "🥈 Silver badge earned · January 2026" (silver dot)
  - "🥉 Bronze badge earned · November 2025" (bronze dot)
- Use border-l-2 + pl-4 pattern, dots positioned with absolute

### Empty State (when no assessments done)
- Show when a toggle/flag indicates no data
- Centered: large "◈" icon (text-6xl text-muted-foreground)
- "Your AURA score will appear here"
- "Complete at least one assessment to earn your score."
- Button: "Start Assessment →" (primary, links to /assessments)

---

## PIECE 2: Improved Question Card with BARS Scale + Open Text

File: `components/features/assessment/question-card-v2.tsx`

Replace the current question-card with an enhanced version that supports 3 question types:

### Type A: Multiple Choice (MCQ)
- 4 option cards (A, B, C, D) — large clickable cards, not small radio buttons
- Selected state: bg-primary/10 border-primary ring-1 ring-primary
- Letter prefix in a circle (bg-muted, w-8 h-8 rounded-full flex items-center justify-center)

### Type B: BARS Scale (Behaviorally Anchored Rating Scale)
- 7-point scale, each as a full-width clickable card
- Labels for each point:
  1 = "Far below expectations"
  2 = "Below expectations"
  3 = "Slightly below expectations"
  4 = "Meets expectations"
  5 = "Above expectations"
  6 = "Well above expectations"
  7 = "Exemplary performance"
- Number circle on the left (same style as MCQ letters)
- Selected: same style as MCQ selected
- Cards should be slightly smaller than MCQ (py-3 not py-4) because there are 7

### Type C: Open Text
- Large textarea (min-h-[160px])
- Placeholder: "Describe your approach in detail..."
- Word counter below right: "42 / 300 words" in text-xs text-muted-foreground
- Character limit indicator that turns amber at 80% and red at 100%

### Progress — use DOTS not bar
- Instead of a progress bar, show dots: ●●●○○○○ (filled for answered, empty for remaining)
- Since IRT means unknown total, show: "Question 4 of ~12" (approximate with tilde)
- Dots container: flex gap-1.5, each dot w-2 h-2 rounded-full
  - Answered: bg-primary
  - Current: bg-primary animate-pulse
  - Remaining: bg-muted

### Timer
- Bottom-left: "⏱ 4:32" in text-xs text-muted-foreground
- NOT a countdown — just elapsed time (informational only)
- Use a simple useEffect with setInterval

### Navigation
- "← Previous" (ghost variant, left) — disabled on first question
- "Next →" (primary, right) — disabled when nothing selected
- On last question: "Submit" instead of "Next" with CheckCircle icon

### Keyboard shortcuts
- For BARS: press 1-7 to select
- For MCQ: press A/B/C/D to select
- ArrowLeft = previous, ArrowRight = next (when something is selected)

### Props interface:
```tsx
interface Question {
  id: string
  type: "mcq" | "bars" | "open_text"
  text: string
  options?: { label: string; value: string }[] // for MCQ
  anchors?: string[] // for BARS (7 items)
}

interface QuestionCardV2Props {
  question: Question
  questionNumber: number
  approximateTotal: number
  answeredCount: number
  elapsed: string // "4:32"
  selectedValue: string | null
  onSelect: (value: string) => void
  onPrevious: () => void
  onNext: () => void
  onSubmit: () => void
  isFirst: boolean
  isLast: boolean
}
```

Include demo usage at the bottom showing all 3 question types.

---

## PIECE 3: Assessment Results with Confetti

File: `components/features/assessment/assessment-results.tsx`

### Confetti Effect
- On mount, burst 60 confetti particles from center-top
- Each particle: random color from [#6366F1, #818CF8, #A78BFA, #EAB308, #10B981, #F59E0B]
- Random sizes (4-8px), random rotation, random x-velocity, gravity y-velocity
- Duration: 3 seconds, fade out in last 0.5s
- Use pure CSS @keyframes (no heavy library) — generate particles as span elements
- pointer-events-none, z-50, fixed positioning

### Score Reveal
- Animated counter: 0 → 82 over 2 seconds (requestAnimationFrame with easeOut)
- Text: text-6xl font-black, colored by tier
- Below: competency name "Communication" in text-xl font-semibold
- Below: "/100" in text-muted-foreground

### AURA Update
- Card showing: "AURA updated: 74.2 → 78.4"
- Visual: two numbers with animated arrow between them
- Delta: "+4.2" in text-success (green)
- Progress bar showing old score (muted) and new score (primary) overlay

### Badge Unlock (conditional)
- If tier changed: show badge animation
- Badge scales from 0 → 1.15 → 1.0 (spring effect via CSS)
- Gold glow pulse animation
- Text: "🥇 Gold Badge Earned!"

### CTAs
- "View AURA Score" (primary button, links to /aura)
- "Next Assessment" (outline button, links to /assessments)

---

## PIECE 4: AURA Card Preview Component

File: `components/aura/card-preview.tsx`

A component that shows a preview of the shareable AURA card before downloading.

### Card Visual (dark, premium design)
- Container: aspect-[1200/630] for LinkedIn format (switchable)
- Background: gradient from #0B1120 to #1a1a2e to #16213e (135deg)
- Top-left: "VOLAURA" in #818CF8, text-sm font-bold
- Center: volunteer name "Murad Hasanov" in text-2xl font-bold white
- Below: "@murad" in text-sm #94A3B8
- HUGE score: "78.4" in text-[80px] font-black, colored gold (#EAB308)
- Below: "GOLD" in uppercase, letter-spacing widest, same gold color, text-shadow glow
- Mini bar chart: 8 thin vertical bars (one per competency), heights proportional to scores, colored gold
- Bottom-right: "volaura.az" in text-xs #475569

### Format Switcher
- Tabs above card: LinkedIn (1200×630) / Story (1080×1920) / Square (1080×1080)
- Card preview changes aspect ratio based on selection
- Active tab: animated underline indicator

### Actions
- "Download" button (primary) with Download icon
- "Share" button (outline) with Share2 icon
- Loading state: skeleton shimmer while "generating"

### Props:
```tsx
interface AuraCardPreviewProps {
  username: string
  displayName: string
  score: number
  badgeTier: "platinum" | "gold" | "silver" | "bronze" | "none"
  competencyScores: Record<string, number>
}
```

---

## IMPORTANT NOTES FOR ALL PIECES:

1. Use the SAME design tokens as the rest of the app (bg-background, text-foreground, bg-card, etc.)
2. Use shadcn/ui components where possible (Card, Button, Badge, Tabs, Tooltip)
3. Use Lucide React for ALL icons
4. Dark mode support (all colors via CSS variables)
5. Responsive: works on mobile (360px) through desktop (1440px)
6. TypeScript strict — proper interfaces, no `any`
7. All components should be "use client" since they use hooks/state

Generate ALL 4 pieces in one response. Each as a separate file.

---END---
