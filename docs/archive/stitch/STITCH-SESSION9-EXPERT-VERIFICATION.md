# Google Stitch Prompt — Session 9: Expert Verification (Gamified)

**Вставь этот промпт в Google Stitch 2.0**
**Export: React/JSX + Tailwind CSS**
**Важно:** Эта страница ПУБЛИЧНАЯ — без авторизации. Эксперт открывает ссылку и сразу видит форму.

---

## Context

This is the **Expert Verification Flow** for Volaura — the most viral feature of the platform.

**How it works:**
1. Organization (e.g. "IEPF Azerbaijan") sends a one-time link to an expert: `volaura.az/verify/[jwt-token]`
2. Expert opens link on mobile (no account needed)
3. Sees volunteer's name + photo + which competencies to rate
4. Swipes through 4-6 gamified cards — takes **30 seconds max**
5. Gets confetti celebration + thank-you screen
6. Optionally: "Learn more about Volaura" CTA

**Design principle:** This is NOT a form. It's a game. The expert should feel delighted, not burdened. Think Tinder card swipe + Duolingo celebration. Every interaction must feel instant and satisfying.

**Psychology used:**
- **Progress momentum**: "3 of 6 done ✓" — can't leave unfinished
- **Instant feedback**: Each card swipe = micro-animation + checkmark sound feel
- **Social proof**: "Join 47 experts who verified volunteers this week"
- **Reciprocity**: Expert feels good about helping → likely to share Volaura

---

## Tech Stack

```
Framework:   Next.js 14 App Router, TypeScript strict
Styling:     Tailwind CSS 4
Components:  shadcn/ui
Animation:   Framer Motion (CRITICAL — all interactions must be animated)
Icons:       lucide-react
i18n:        react-i18next — all text via t()
```

**Note:** This page is at `/verify/[token]` — NOT inside `/(dashboard)`. No auth guard. No TopBar/nav.

---

## Design Tokens

```css
--color-brand:       #6366f1
--color-brand-light: #818cf8
--color-success:     #22c55e
--color-aura-gold:   #ffd700
--radius-card:       20px   /* bigger radius = friendlier feel */
```

---

## SCREEN 1: Verification Landing (`/verify/[token]`)

### States

**State A: Loading (token validation)**
```
┌────────────────────────────┐
│         [spinner]          │
│   "Yoxlanılır..."          │
└────────────────────────────┘
```
- Centered spinner, brand color
- Validate JWT token server-side (fetch to `/api/verify/validate`)

**State B: Invalid/Expired Token**
```
┌────────────────────────────┐
│     ⚠️  (icon, 48px)       │
│  "Bu link etibarsızdır"    │
│  "Link 7 gün ərzində       │
│   keçərlidir. Yeni link    │
│   üçün təşkilatla əlaqə    │
│   saxlayın."               │
│                            │
│  [Volaura haqqında]        │
└────────────────────────────┘
```

**State C: Already Used**
```
┌────────────────────────────┐
│     ✅  (icon)              │
│  "Siz artıq bu könüllünü   │
│   qiymətləndirdiniz!"      │
│  [Qiymətləndirmənizi gör]  │
└────────────────────────────┘
```

**State D: Valid — Intro Screen (show first)**
```
┌────────────────────────────┐
│   [Volunteer photo, 80px]  │
│   Leyla Həsənova           │
│   @leyla_h · Gold AURA     │
│                            │
│  ─────────────────────     │
│                            │
│  "IEPF Azərbaycan sizi     │
│   Leyla-nı 4 bacarıq       │
│   üzrə qiymətləndirməyə   │
│   dəvət edir."             │
│                            │
│  ⏱ Təxminən 30 saniyə     │
│                            │
│  [👥 Bu həftə 47 ekspert   │
│   qiymətləndirdi]          │
│                            │
│  ┌──────────────────────┐  │
│  │  Başla →             │  │
│  └──────────────────────┘  │
└────────────────────────────┘
```

- Volunteer photo: shadcn Avatar, 80px, with AURA badge color ring
- Badge ring color: Gold=yellow, Platinum=violet, etc.
- Social proof: small pill at bottom, updates in real-time via fetch
- "Başla" button: large, brand color, full width, with right arrow
- Tap "Başla" → slides to Card Swipe Flow

---

## SCREEN 2: Card Swipe Flow (CORE EXPERIENCE)

### Layout — one card at a time, full screen

```
┌────────────────────────────┐
│ ● ● ● ○ ○ ○               │ ← Progress dots (filled = done)
│ "3 / 6"                   │
│                            │
│ ┌──────────────────────┐   │
│ │                      │   │
│ │   Kommunikasiya      │   │ ← Competency name (24px bold)
│ │                      │   │
│ │   "Bu könüllü        │   │ ← Short description (what to rate)
│ │   tədbir zamanı      │   │
│ │   ünsiyyəti necə     │   │
│ │   qururdu?"          │   │
│ │                      │   │
│ └──────────────────────┘   │ ← Card (rounded 20px, shadow)
│                            │
│  😕   😐   🙂   😊   🔥   │ ← Rating row (1-5, emoji above)
│  [1]  [2]  [3]  [4]  [5]  │ ← Tap to select
│                            │
└────────────────────────────┘
```

### Card Interaction (CRITICAL — must feel great)

**Rating buttons (1-5):**
- 5 equal buttons in a row
- Above each: emoji (😕 😐 🙂 😊 🔥)
- Tap any rating:
  1. Selected button: scale(1.3) + brand background, 150ms spring
  2. All others: slightly dim
  3. After 300ms delay → card slides LEFT off screen (x: 0→-100%, opacity 0→0, 250ms)
  4. Next card slides in from RIGHT (x: 100%→0, 250ms ease-out)
  5. Progress dot fills in

**Card entrance animation:**
- First card: fade in + scale(0.95→1), 300ms
- Subsequent cards: slide from right, 250ms ease-out

**No swipe needed** — tap rating → auto-advance. (Swipe gesture optional, tap is primary)

**Haptic feel:** Button press → brief scale down(0.95) then back up, 80ms. Makes it feel physical.

### Progress indicator

- 6 dots at top (or fewer if less competencies)
- Filled: brand color
- Current: pulsing brand color
- Empty: muted color
- Text: "3 / 6" — updates live

### Optional comment (after last rating, before submit)

```
┌────────────────────────────┐
│  Əlavə fikir? (İstəyə      │
│  görə)                     │
│                            │
│  ┌──────────────────────┐  │
│  │ Leyla çox səy göstər │  │
│  │ ...                  │  │
│  └──────────────────────┘  │
│  Max 200 simvol            │
│                            │
│  [Keç →]  [Göndər →]      │
└────────────────────────────┘
```

- Textarea: auto-resize, max 200 chars, char counter
- "Keç" (Skip): ghost button, smaller
- "Göndər" (Submit): primary button
- Both lead to completion screen

---

## SCREEN 3: Completion / Celebration

```
┌────────────────────────────┐
│                            │
│    🎉  ← confetti burst    │
│                            │
│   ✅ (animated checkmark   │
│       spring scale-in)     │
│                            │
│   "Təşəkkür edirik!"       │  (24px bold)
│                            │
│   "Leyla-nın AURA Balı     │
│    yeniləndi.              │
│    Sizin qiymətiniz        │
│    onun profilinə          │
│    əlavə edildi."          │
│                            │
│  ─────────────────────     │
│                            │
│  "Volaura haqqında daha    │
│   çox öyrən →"             │
│  [volaura.az]              │
│                            │
│  [Paylaş: "Mən könüllü    │
│   qiymətləndirdim"] 📤    │
└────────────────────────────┘
```

### Celebration animation sequence

1. **t=0ms:** Screen appears (fade in)
2. **t=100ms:** Checkmark draws itself (stroke animation, 400ms, green)
3. **t=300ms:** Confetti burst (use CSS particles or canvas — 20-30 particles, 1.5s)
4. **t=500ms:** "Təşəkkür edirik!" text fades + slides up (300ms)
5. **t=700ms:** Description text fades in (200ms)
6. **t=1000ms:** CTA buttons fade in (200ms)

**Confetti implementation:**
```tsx
// Simple CSS confetti — no library needed
// Absolute positioned spans, randomized:
// - colors: brand, gold, success, violet, red, orange
// - sizes: 6-12px squares/circles
// - animation: fall + rotate, 1.5-2s, random delay 0-500ms
// - 24 particles total
```

**Share button:**
- Opens native share sheet on mobile (`navigator.share()`)
- Fallback: copy text to clipboard
- Share text: "Mən Volaura-da könüllü qiymətləndirdim! Peşəkar könüllüləri kəşf et: volaura.az"

---

## CRITICAL RULES

1. **NO auth guard** — this page is public. Anyone with the link can open it.
2. **Mobile-ONLY design** — verification links are sent via WhatsApp/Telegram. Design for 375px. Desktop is secondary.
3. **30 seconds max** — every unnecessary element adds friction and drops completion rate. Keep it ruthlessly simple.
4. **Zero form fields on the rating screens** — only 5 tappable buttons per card. The optional comment is after ALL ratings, not between.
5. **All text via t()** — no hardcoded strings. Use keys like `t("verify.intro.title")`, `t("verify.card.ratingLabel")`.
6. **Framer Motion on everything** — card transitions, button presses, progress dots, completion screen.
7. **Handle all error states** — expired token, already used, network error.

## File Structure to Output

```
apps/web/src/
├── app/
│   └── verify/
│       └── [token]/
│           └── page.tsx          ← Main page (all states)
└── components/
    └── verify/
        ├── intro-screen.tsx      ← Volunteer info + Start button
        ├── rating-card.tsx       ← Single competency card + 1-5 buttons
        ├── progress-dots.tsx     ← Dot progress indicator
        ├── optional-comment.tsx  ← Text field after last card
        └── completion-screen.tsx ← Confetti + thank you
```

## API Endpoints (already specced in docs/engineering/API-CONTRACTS.md)

```
GET  /api/verify/validate?token={jwt}     → { volunteer, competencies, org, status }
POST /api/verify/submit                   → { token, ratings: [{competency, score}], comment? }
```

JWT payload: `{ volunteer_id, org_id, competencies: string[], exp, iat, jti (one-use) }`
