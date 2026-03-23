# V0 Prompt — Session 7: Results + AURA Radar Chart

**Paste this entire prompt into v0.dev**

---

Build the AURA Score results page for Volaura. This is the most important screen in the app — it's where volunteers see their verified competency badge and radar chart.

## Tech Stack (already set up — match exactly)
- Next.js 14 App Router, TypeScript strict
- Tailwind CSS 4 with `@theme` tokens
- Recharts for radar chart
- Framer Motion for animations
- react-i18next (all text via `t()`)
- shadcn/ui components

## Design Tokens
```css
--color-brand: #6366f1
--color-aura-platinum: #e5e4e2  /* score >= 90 */
--color-aura-gold: #ffd700      /* score >= 75 */
--color-aura-silver: #c0c0c0    /* score >= 60 */
--color-aura-bronze: #cd7f32    /* score >= 40 */
```

## Screens to Build

### Screen 1: AURA Score Reveal (`/[locale]/aura`)
Sequence (animate in order with Framer Motion):
1. Badge tier appears first (large, centered) — Platinum/Gold/Silver/Bronze/None
2. Score number counts up from 0 to final score (animated counter)
3. "Your AURA Score" label fades in
4. Radar chart draws itself (animated stroke)
5. Competency breakdown cards slide up
6. Action buttons appear

Layout:
```
┌─────────────────────────────┐
│     [BADGE ICON]             │
│      GOLD                   │
│       82                    │
│   Your AURA Score           │
├─────────────────────────────┤
│    [RADAR CHART - 8 axes]   │
│                             │
├─────────────────────────────┤
│  Competency Breakdown:      │
│  Communication    ████ 85   │
│  Leadership       ███  72   │
│  Reliability      ████ 90   │
│  ...                        │
├─────────────────────────────┤
│  [Share] [Retake] [Profile] │
└─────────────────────────────┘
```

### Radar Chart Component
```typescript
// Use Recharts RadarChart
// 8 competencies:
const competencies = [
  { key: "communication", label: "Communication", weight: 0.20 },
  { key: "reliability", label: "Reliability", weight: 0.15 },
  { key: "english_proficiency", label: "English", weight: 0.15 },
  { key: "leadership", label: "Leadership", weight: 0.15 },
  { key: "event_performance", label: "Event Perf.", weight: 0.10 },
  { key: "tech_literacy", label: "Tech", weight: 0.10 },
  { key: "adaptability", label: "Adaptability", weight: 0.10 },
  { key: "empathy_safeguarding", label: "Empathy", weight: 0.05 },
]
// Score range: 0-100
// Chart fill color = badge tier color
// Animated: draw from center outward on mount
```

### Badge Component
4 tiers, each with distinct design:
- **Platinum** (≥90): Silver/white gradient, diamond shape, sparkle animation
- **Gold** (≥75): Gold gradient, star burst, glow effect
- **Silver** (≥60): Silver gradient, shield shape
- **Bronze** (≥40): Bronze/copper gradient, circle

### Competency Breakdown Cards
- Horizontal bar for each competency (score 0-100)
- Bar color = tier color based on that competency's score
- Weight shown as small text
- Click to expand: shows sub-skills assessed

### Share Card (`/api/u/[username]/card`)
OG image style card (1200x630) for social sharing:
- Badge + Score + Name + "Verified by Volaura"
- "Share on LinkedIn" button → LinkedIn share with URL
- "Copy link" button
- Download as PNG option

## API
```typescript
// GET /api/v1/profile/aura
interface AuraResponse {
  total_score: number
  badge_tier: "platinum" | "gold" | "silver" | "bronze" | "none"
  competency_scores: Record<string, number>  // 0-100 per competency
  last_assessed: string
  assessments_count: number
}
```

## i18n Keys
```
t("aura.title"), t("aura.totalScore"), t("aura.badge")
t("aura.competencies"), t("aura.share"), t("aura.retake")
t("aura.platinum"), t("aura.gold"), t("aura.silver")
t("aura.bronze"), t("aura.none")
```

## Files to Create
```
src/app/[locale]/(dashboard)/aura/page.tsx    ← main results page
src/components/aura/
├── radar-chart.tsx        ← already exists, may need to enhance
├── badge.tsx              ← NEW: tier-aware badge component
├── score-counter.tsx      ← NEW: animated number counter
├── competency-bar.tsx     ← NEW: horizontal progress bar
├── share-card.tsx         ← NEW: social sharing component
└── share-buttons.tsx      ← already exists
```

## Component States (ALL required)

- **Loading** (waiting for `/api/v1/profile/aura`): skeleton placeholders for badge, chart, bars — `animate-pulse bg-muted`
- **Error** (API failure): centered card `t("aura.errorLoading")` + `t("common.retry")` button
- **Empty / not yet assessed** (`assessments_count === 0`): `t("aura.notAssessedYet")` + CTA `t("aura.startAssessment")` → `/[locale]/assessment`
- **Share loading**: Share button shows spinner while generating OG image

## Error + Empty State Copy (follow: what happened + why + how to fix)

```
t("aura.errorLoading")       → "Couldn't load your AURA score. Check your connection and try again."
t("aura.notAssessedYet")     → "No score yet. Complete at least one competency assessment to get your AURA score."
t("aura.shareError")         → "Couldn't generate share card. Try again or copy your profile link."
t("aura.startAssessment")    → "Start Assessment"
```

## Animation Specs (exact values — do not approximate)

```typescript
// Badge entrance
// initial={{ scale: 0, opacity: 0 }}
// animate={{ scale: 1, opacity: 1 }}
// transition={{ type: "spring", stiffness: 200, damping: 15, delay: 0.1 }}

// Score counter (0 → final)
// useEffect: increment every 16ms (60fps), duration 1200ms total, ease-out curve
// i.e. step = (target / 75) * Math.pow(1 - progress, 2) per frame — decelerates near end

// Label fade-in
// initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.4, duration: 0.4 }}

// Radar chart draw
// Recharts does not animate stroke natively — use CSS clip-path trick:
// Wrap RadarChart in div with clipPath animation from 0% to 100% width+height over 800ms (delay 1.6s)

// Competency cards slide-up (staggered)
// Each card: initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }}
// transition={{ delay: 2.4 + index * 0.08, duration: 0.3, ease: "easeOut" }}

// Action buttons
// initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 3.2, duration: 0.3 }}

// Platinum sparkle: CSS @keyframes shimmer on pseudo-element, 2s infinite
// Gold glow: box-shadow pulse, animate({ boxShadow: ["0 0 8px #ffd700", "0 0 24px #ffd700", "0 0 8px #ffd700"] }), 2s repeat
```

## Accessibility (ARIA)

- Radar chart: `role="img" aria-label={t("aura.radarChartAlt", { name: displayName })}` (e.g. "Leyla's competency radar chart")
- Competency bars: `role="meter" aria-valuenow={score} aria-valuemin={0} aria-valuemax={100} aria-label={t(competency.key)}`
- Badge: `aria-label={t("aura.badgeAlt", { tier: badge_tier, score: total_score })}` (e.g. "Gold badge, AURA score 82")
- Score counter during animation: `aria-live="polite"` on the number — announces final value when animation ends
- Share buttons: `aria-label={t("aura.shareOnLinkedIn")}` (icon-only buttons need explicit labels)
- Skip animation: add `<button onClick={skipAnimation}>` for users with prefers-reduced-motion; check `window.matchMedia("(prefers-reduced-motion: reduce)")` and skip animation sequence if true

## Edge Cases

- **Score = 0**: badge = None tier, no radar fill, show `t("aura.scoreZero")` → "Keep going — complete more assessments"
- **One competency only**: radar chart with 1 data point looks broken — show bar chart fallback when `assessments_count < 3`
- **Long display name in AZ**: name field in share card — truncate at 24 chars with ellipsis
- **Share card on mobile**: LinkedIn share URL must use `window.open()` not `<a target="_blank">` (blocked on iOS)
- **PNG download**: use `html2canvas` on share card div, or server-side OG image at `/api/u/[username]/card.png`
- **`last_assessed` > 6 months ago**: show subtle banner `t("aura.scoreStale")` → "Your score is from 6+ months ago. Retake to update it."

## Additional i18n Keys

```
t("aura.errorLoading")        → see above
t("aura.notAssessedYet")      → see above
t("aura.shareError")          → see above
t("aura.startAssessment")     → "Start Assessment"
t("aura.scoreZero")           → "Keep going — complete more assessments to earn your score."
t("aura.scoreStale")          → "Your score is from {months} months ago. Retake to update it."
t("aura.radarChartAlt")       → "{name}'s competency radar chart"
t("aura.badgeAlt")            → "{tier} badge — AURA score {score}"
t("aura.shareOnLinkedIn")     → "Share on LinkedIn"
t("aura.copyLink")            → "Copy profile link"
t("aura.downloadPNG")         → "Download as image"
t("aura.linkCopied")          → "Link copied!"
t("aura.competencyWeight")    → "Weight: {weight}%"
t("aura.retakeAssessment")    → "Retake Assessment"
t("aura.viewProfile")         → "View Profile"
```

## Important Rules
- NO hardcoded strings
- Recharts is already in package.json — use it
- Animation must be progressive (not all at once) — exact timing above
- Badge must be visually impressive — this is the "wow moment"
- Mobile-first
- ALL states: loading skeleton, error, empty (not assessed), normal
- `prefers-reduced-motion`: skip all animations, show final state immediately
- AZ strings are ~25% longer — test share card and badge layout with AZ locale
