# Google Stitch Prompt — Session 8: Dashboard + Profile

**Вставь этот промпт в Google Stitch 2.0**
**Export: React/JSX + Tailwind CSS**
**После экспорта:** скопируй в `apps/web/src/` — импорты и токены должны совпасть

---

## Context

Design two screens for **Volaura** — a verified talent platform in Azerbaijan.
The platform gives volunteers an AI-evaluated AURA Score (0-100) and badge tier (Platinum / Gold / Silver / Bronze).
Volunteers get verified by organizations, compete for elite status, and get discovered by event organizers.

**Design language:** Clean, dark-mode-friendly, mobile-first. Think Duolingo meets LinkedIn — gamified but professional. Not colorful/childish — confident and aspirational.

---

## Tech Stack (match exactly — do not invent new patterns)

```
Framework:   Next.js 14 App Router, TypeScript strict
Styling:     Tailwind CSS 4 (CSS-first, @theme tokens)
Components:  shadcn/ui (Button, Card, Badge, Avatar, Skeleton)
Animation:   Framer Motion
Icons:       lucide-react
i18n:        react-i18next — ALL text via t() — ZERO hardcoded strings
State:       Zustand (already set up)
Fonts:       Inter (system font)
```

## Design Tokens

```css
--color-brand:          #6366f1   /* indigo — primary */
--color-brand-light:    #818cf8
--color-aura-platinum:  #e5e4e2
--color-aura-gold:      #ffd700
--color-aura-silver:    #c0c0c0
--color-aura-bronze:    #cd7f32
--radius-card:          12px
--shadow-card:          0 1px 3px rgba(0,0,0,0.12)
```

---

## SCREEN 1: Dashboard (`/[locale]/dashboard`)

### Layout (mobile-first, max-width 640px centered)

```
┌─────────────────────────────────────────┐
│ TopBar: "İdarə Paneli" + notif bell     │
├─────────────────────────────────────────┤
│ Welcome Card                            │
│  "Salam, Leyla 👋"                      │
│  Subtitle: "Bugün 3 könüllü sizi..."   │
├─────────────────────────────────────────┤
│ AURA Score Widget (tappable → /aura)   │
│  ┌──────────────┬──────────────────┐   │
│  │  Score: 78.4 │  🥇 Gold Badge   │   │
│  │  ████████░░  │  Elite status    │   │
│  │  Progress bar│                  │   │
│  └──────────────┴──────────────────┘   │
├─────────────────────────────────────────┤
│ Stats Row (3 cards horizontal)         │
│  🔥 Streak  📅 Events  ⭐ League       │
│   7 days     12         Top 8%         │
├─────────────────────────────────────────┤
│ "Continue Assessment" CTA              │
│  (if assessment incomplete)            │
├─────────────────────────────────────────┤
│ Recent Activity Feed                   │
│  • Org "IEPF" viewed your profile (2h) │
│  • You earned +5 AURA points (1d)     │
│  • New event: COP30 needs volunteers  │
└─────────────────────────────────────────┘
```

### Component Details

**Welcome Card:**
- Background: subtle gradient from brand/5 to transparent
- Shows user's display_name or username
- Subtext: dynamic (org views, new events, score change) — use placeholder text
- Animated entrance: fade + slide up, delay 0ms

**AURA Score Widget:**
- The most important element on the page — make it PROMINENT
- Score: large number (48px bold), animates 0→score on mount (1200ms)
- Mini horizontal progress bar showing score/100
- Badge tier: colored pill (Platinum=violet, Gold=yellow, Silver=slate, Bronze=amber)
- Elite badge: small star icon next to tier name if elite
- Entire widget is clickable → navigates to /aura
- Hover state: slight scale(1.02) + shadow increase
- States: Loading (skeleton), NoScore (CTA to start assessment), HasScore (above)

**Stats Row:**
- 3 equal-width cards in a horizontal row
- Streak: flame icon + number + "days" — highlight if streak > 5 (brand color)
- Events: calendar icon + count
- League: trophy icon + percentage text
- Mobile: full width row, scrollable if needed

**Continue Assessment CTA:**
- Only shown if: user has started but not completed assessment
- Large button, brand color, full width
- Text: "Qiymətləndirməni davam et → 3 competency remaining"
- Framer Motion: pulse animation every 4 seconds to draw attention

**Activity Feed:**
- Max 5 items, "View all" link at bottom
- Each item: small icon (org view / aura / event) + text + time ago
- Icons: Eye (org viewed), Zap (AURA points), Calendar (event)
- Empty state: "Hələ heç bir fəaliyyət yoxdur. Qiymətləndirməyə başla!"
- Skeleton: 3 lines while loading

### States Required

| State | What to show |
|-------|-------------|
| Loading | TopBar visible, rest is skeleton (Skeleton component from shadcn) |
| No AURA score yet | Replace score widget with "Start Assessment" full-width card |
| Has score | Full dashboard as above |
| Has score + incomplete assessment | Show "Continue" CTA above activity feed |

### Animations

| Element | Trigger | Animation | Duration | Easing |
|---------|---------|-----------|----------|--------|
| Score number | Mount | Count 0→N | 1200ms | cubic-bezier |
| Welcome card | Mount | Fade + Y:16→0 | 400ms | ease-out |
| Stats cards | Mount | Stagger 80ms each | 300ms | ease-out |
| Activity items | Mount | Stagger 60ms | 250ms | ease-out |
| Continue CTA | Every 4s | Pulse glow | 800ms | ease-in-out |

---

## SCREEN 2: Profile (`/[locale]/profile`)

### Layout

```
┌─────────────────────────────────────────┐
│ TopBar: "Profil" + Edit button          │
├─────────────────────────────────────────┤
│ Profile Header                          │
│  Avatar (80px) + Name + Username        │
│  Badge tier pill                        │
│  Bio text (2 lines max, expandable)    │
│  "Profili redaktə et" button           │
├─────────────────────────────────────────┤
│ Impact Metrics (2×2 grid)              │
│  📅 12 Events  ⏱ 86h Volunteered      │
│  ✅ 8 Skills   🌟 Gold Tier           │
├─────────────────────────────────────────┤
│ Verified Skills chips                  │
│  [Communication ✓] [Leadership ✓] ...  │
│  Chips: brand border, checkmark icon   │
├─────────────────────────────────────────┤
│ Expert Verifications                   │
│  "Verified by 3 organizations"         │
│  Org avatars (stacked, max 5)          │
│  [Org logo] IEPF · "Excellent comms"  │
├─────────────────────────────────────────┤
│ Activity Timeline                      │
│  Vertical timeline, 5 events max       │
│  • [Event] COP29 — Nov 2024           │
│  • [Assessment] Gold badge earned      │
│  • [Event] COP28 — Dec 2023           │
│  "View all history"                    │
└─────────────────────────────────────────┘
```

### Component Details

**Profile Header:**
- Avatar: 80px circle, shadcn Avatar with fallback initials
- Name: 20px semibold, Username: 14px muted
- Badge tier: colored pill using AURA token colors
- Bio: 2 lines clamped with "Daha çox" expand button
- Edit button: outline variant, top-right or below bio
- No avatar? → gradient background with initials (brand gradient)

**Impact Metrics 2×2:**
- 4 cards in a 2-column grid
- Each card: icon (24px) + large number (24px bold) + label (12px muted)
- Animate numbers on mount (count up, 600ms)
- Card hover: subtle lift

**Verified Skills:**
- Horizontal scrollable chip row
- Each chip: competency name + checkmark icon
- Unverified competency: muted style (no checkmark)
- Max visible: 6, overflow scrollable
- Tap → tooltip or modal: "Verified by AI + IEPF organization"

**Expert Verifications block:**
- Show count: "3 təşkilat tərəfindən təsdiq edilib"
- Stacked avatar row: org logos overlap (like GitHub contributors row)
- Below: most recent 2 verifications as cards:
  - Org name + logo + date + quote text (max 100 chars)
  - Star rating visual (1-5)
- Empty state: "Hələ heç bir ekspert təsdiqi yoxdur. Təşkilatdan link istəyin."

**Timeline:**
- Vertical line with dots (brand color for assessment events, muted for events)
- Event types: assessment (brain icon), event (calendar), badge (star), verification (shield)
- Date on right, description on left
- "Bütün tarixi gör" link at bottom

### Edge Cases

- **Empty profile (new user):** Show onboarding prompt in each empty section — not blank space
- **Long name:** Truncate at 24 chars with ellipsis
- **Long bio:** Clamp at 2 lines, expand toggle
- **No events attended:** "Hələ heç bir tədbirə qatılmamısınız"
- **No verifications:** Show CTA explaining how to get verified

### Accessibility

- Avatar image: `alt={name}`
- Skill chips: `role="listitem"` inside `role="list"`
- Timeline items: `aria-label="[date]: [event description]"`
- Impact metric cards: `aria-label="12 tədbirə qatılmısınız"`
- Edit button: `aria-label="Profili redaktə et"`

---

## CRITICAL RULES (read before generating)

1. **NO hardcoded strings** — every user-facing text must be inside `t("key")` call. Use realistic i18n key names like `t("dashboard.welcome")`, `t("profile.editProfile")`.
2. **NO inline styles** — Tailwind classes only. Use `cn()` for conditional classes.
3. **NO axios or custom fetch** — use native `fetch()` with async/await.
4. **NO hardcoded colors** — use CSS variables (`text-primary`, `bg-muted`, etc.) or AURA tokens above.
5. **AZ text is 20-30% longer than EN** — all text containers must handle wrapping gracefully. Test with longest strings.
6. **Mobile-first** — design for 375px viewport. Desktop is secondary.
7. **Loading states mandatory** — every data-dependent section needs a Skeleton or Loader2 spinner.
8. **Framer Motion** — use for all entrance animations. Import from `"framer-motion"`.

## File Structure to Output

```
apps/web/src/
├── app/[locale]/(dashboard)/
│   ├── dashboard/page.tsx        ← Screen 1
│   └── profile/page.tsx          ← Screen 2
└── components/
    ├── dashboard/
    │   ├── aura-score-widget.tsx
    │   ├── stats-row.tsx
    │   └── activity-feed.tsx
    └── profile/
        ├── profile-header.tsx
        ├── impact-metrics.tsx
        ├── skill-chips.tsx
        ├── expert-verifications.tsx
        └── activity-timeline.tsx
```

