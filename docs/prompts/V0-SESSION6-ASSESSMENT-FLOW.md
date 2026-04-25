# V0 Prompt — Session 6: Assessment Flow UI

**Paste this entire prompt into v0.dev**

---

Build a multi-step competency assessment flow for Volaura, a verified talent platform in Azerbaijan. The assessment uses adaptive testing (IRT/CAT) — questions get harder/easier based on answers.

## Tech Stack (already set up — match exactly)
- Next.js 14 App Router, TypeScript strict
- Tailwind CSS 4 with `@theme` tokens
- shadcn/ui components
- Framer Motion for animations
- react-i18next (all text via `t()` — no hardcoded strings)
- Zustand for state
- TanStack Query for API calls

## Design System Tokens (use these exactly)
```css
--color-brand: #6366f1
--color-brand-light: #818cf8
--color-aura-platinum: #e5e4e2
--color-aura-gold: #ffd700
--color-aura-silver: #c0c0c0
--color-aura-bronze: #cd7f32
```

## Screens to Build

### Screen 1: Competency Selection (`/[locale]/assessment`)
- Grid of 8 competency cards (Communication, Reliability, English, Leadership, Event Performance, Tech Literacy, Adaptability, Empathy)
- Each card: icon + name + short description + "Select" toggle
- User selects 1-4 competencies to assess
- Selected state: brand color border + checkmark
- "Start Assessment" CTA (disabled until ≥1 selected)
- Show estimated time per competency (8-12 min each)
- Mobile-first: 2 columns on mobile, 4 on desktop

### Screen 2: Question Display (`/[locale]/assessment/[sessionId]`)
Layout:
- Top bar: competency name + progress bar (question X of estimated N) + timer countdown
- Question card (center, max-w-2xl):
  - Question text (large, readable)
  - 3 question types — build all 3:
    **Type A — MCQ**: 4 radio options, clean card layout
    **Type B — Open Text**: textarea with 5000 char limit + live counter
    **Type C — Rating Scale**: 5-point horizontal scale with labels
- Bottom: "Submit Answer" button (primary) + skip option (text link)
- Subtle difficulty indicator (easy/medium/hard — shown as dot color, not text)

Interactions:
- Smooth slide animation between questions (Framer Motion)
- Timer pulses red when < 30 seconds
- Answer selected → button activates
- Loading state after submit (spinner, button disabled)
- "Evaluating your answer..." state (202 Accepted from API)

### Screen 3: Between-Competency Transition
- Full-screen card: "Competency 1 of 3 complete ✓"
- Mini preview of score so far (blurred/locked until full assessment)
- "Continue to [next competency]" CTA
- Option to "Take a break" (saves progress)

### Screen 4: Assessment Complete (`/[locale]/assessment/[sessionId]/complete`)
- Celebration animation (confetti or particle burst — Framer Motion)
- "Processing your results..." with animated loader
- Auto-redirect to /aura after 3 seconds
- Manual "See my results" link

## API Integration
```typescript
// These endpoints are ready in the backend

// Start assessment
POST /api/v1/assessment/start
body: { competency_slug: string, language: "az" | "en" }
response: { session_id: string, question: Question }

// Get next question
POST /api/v1/assessment/answer
body: { session_id: string, answer: string, response_time_ms: number }
response: { question?: Question, completed?: boolean, competency_score?: number }

// Question type
interface Question {
  id: string
  text: string
  type: "mcq" | "open_text" | "rating_scale"
  options?: string[]  // for MCQ
  time_limit_seconds: number
  difficulty_level: "easy" | "medium" | "hard"
}
```

## i18n Keys (use these — don't hardcode)
```
t("assessment.title")
t("assessment.selectCompetencies")
t("assessment.start")
t("assessment.question")
t("assessment.of")
t("assessment.timeRemaining")
t("assessment.submit")
t("assessment.next")
t("assessment.complete")
t("assessment.viewResults")
t("assessment.resume")
t("common.loading")
t("common.cancel")
```

## State Management
```typescript
// Create this Zustand store: src/stores/assessment-store.ts
interface AssessmentState {
  sessionId: string | null
  currentQuestion: Question | null
  competencies: string[]  // selected slugs
  answeredCount: number
  isSubmitting: boolean
  setSession: (id: string) => void
  setQuestion: (q: Question) => void
  setCompetencies: (c: string[]) => void
  incrementAnswered: () => void
  setSubmitting: (v: boolean) => void
  reset: () => void
}
```

## File Structure to Create
```
src/app/[locale]/(dashboard)/assessment/
├── page.tsx                    ← Screen 1: Competency Selection
├── [sessionId]/
│   ├── page.tsx                ← Screen 2: Question Display
│   └── complete/page.tsx       ← Screen 4: Complete
src/components/assessment/
├── competency-card.tsx
├── question-card.tsx
├── mcq-options.tsx
├── open-text-answer.tsx
├── rating-scale.tsx
├── progress-bar.tsx
├── timer.tsx
└── transition-screen.tsx
src/stores/assessment-store.ts
```

## Component States (build ALL — do not skip)

For every interactive element, implement ALL states:
- **Default**: resting state
- **Hover**: `transition-colors duration-150 ease-out` on cards/buttons
- **Active/Selected**: brand border + checkmark (competency cards), filled (radio options)
- **Disabled**: `opacity-50 cursor-not-allowed` — Start button when 0 competencies selected
- **Loading**: spinner inside button, button disabled, text → `t("common.loading")`
- **Error**: destructive style, message below input/card
- **Empty**: see Empty States below

## Empty States

Every screen that could be empty:
- **No competencies selected**: Start button disabled, helper text `t("assessment.selectAtLeastOne")` appears below grid
- **API error on question load**: full-screen error card `t("assessment.errorLoadingQuestion")` + retry button `t("common.retry")`
- **Session expired mid-assessment**: redirect to login with `?next=/[locale]/assessment`

## Error Messages (follow: what happened + why + how to fix)

These go into i18n files — add to `common.json`:
```
t("assessment.errorStartFailed")   → "Assessment couldn't start. Server is busy. Try again in a moment."
t("assessment.errorSubmitFailed")  → "Answer wasn't saved. Check your connection and tap Submit again."
t("assessment.errorLoadingQuestion") → "Couldn't load next question. Your progress is saved — tap Retry."
t("assessment.sessionExpired")     → "Your session expired. Log in again to continue where you left off."
t("assessment.timerExpired")       → "Time's up. Your answer was saved automatically."
```
AZ translations: add corresponding keys to `az/common.json`. AZ strings run ~25% longer — ensure all layouts accommodate this.

## Animation Specs (Framer Motion — use these exact values)

```typescript
// Question slide transition
const questionVariants = {
  enter: { x: 60, opacity: 0 },
  center: { x: 0, opacity: 1, transition: { duration: 0.25, ease: "easeOut" } },
  exit: { x: -60, opacity: 0, transition: { duration: 0.2, ease: "easeIn" } }
}

// Timer pulse when < 30s
// animate={{ scale: [1, 1.05, 1] }} transition={{ repeat: Infinity, duration: 0.8 }}
// text color: transition to text-destructive at < 30s, < 10s add bg-destructive/10

// Between-competency screen entrance
// initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}
```

## Accessibility (ARIA)

- `<form>` wraps each question card with `aria-label={t("assessment.questionForm")}`
- Radio options: use native `<input type="radio">` (not div) for keyboard nav
- Timer: `<time aria-live="polite" aria-atomic="true">` — announces every 30s, and at 30s/10s remaining
- Progress bar: `role="progressbar" aria-valuenow={answered} aria-valuemax={estimated} aria-label={t("assessment.progress")}`
- Submit button: `aria-busy={isSubmitting}` while loading
- Skip link: `aria-label={t("assessment.skipQuestion")}`
- Focus management: when new question loads, focus moves to question card `tabIndex={-1}` with `ref.focus()`

## Edge Cases

- **Timer hits 0**: auto-submit current answer (or empty string if nothing entered), show `t("assessment.timerExpired")` toast, load next question
- **Open text**: textarea `maxLength={5000}`, counter shows `{chars}/5000`, at 4900+ counter turns orange, at 5000 red
- **Long AZ text**: competency names in AZ can be 30+ chars — card layout must handle without overflow (use `line-clamp-2` or truncate)
- **Slow connection**: if API call >3s, show subtle skeleton pulse in question area (not full loading screen)
- **Rating scale on mobile**: 5 options must be tappable (min 44×44px touch target each)
- **Browser back during assessment**: block with `window.onbeforeunload` + `t("assessment.leaveWarning")`

## Additional i18n Keys

```
t("assessment.selectAtLeastOne")    → hint text below grid
t("assessment.estimatedTime")       → "{n} min" per competency card
t("assessment.questionProgress")    → "Question {current} of ~{total}"
t("assessment.skipQuestion")        → "Skip this question"
t("assessment.leaveWarning")        → "Your progress will be lost. Leave anyway?"
t("assessment.timerExpired")        → "Time's up — moving to next question"
t("assessment.takingBreak")         → "Progress saved. Come back anytime."
t("assessment.competencyComplete")  → "{name} complete ✓"
t("assessment.continueToNext")      → "Continue to {next}"
t("assessment.processingResults")   → "Processing your results..."
t("common.retry")                   → "Try again"
```

## Important Rules
- NO hardcoded strings — every user-facing text must use `t()`
- NO mock data — connect to real API endpoints listed above
- Import paths use `@/` alias (e.g., `import { cn } from "@/lib/utils/cn"`)
- `cn()` for conditional classes: `import { cn } from "@/lib/utils/cn"`
- Supabase client: `import { createClient } from "@/lib/supabase/client"`
- All pages are in `(dashboard)` route group which has auth guard
- Mobile-first responsive design
- ALL states must be implemented (default, hover, active, disabled, loading, error, empty)
- AZ strings are ~25% longer — test all layouts with AZ locale

