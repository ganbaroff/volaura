# v0.dev Frontend Prompt — Volaura Full Stack Generation

> Ты уже работал над Volaura (Sprint 3-5). Это обновлённый и полный промпт с правильной архитектурой. Генерируй по модулям, начиная с Module A.

## CONTEXT: What is Volaura?

**Volaura** is a verified competency platform and community for the best volunteers. Volunteers take an adaptive assessment across 8 competencies, receive an AURA composite score (0-100) with a badge tier (Platinum/Gold/Silver/Bronze), and share their verified profile with organizations. Events are dynamic data (COP29, CIS Games, etc.) — NEVER hardcode specific event names.

This prompt covers FRONTEND ONLY — no Python/FastAPI/backend logic. For API calls, use mock data with the shapes provided. v0 is building a standalone Next.js 14 app (we handle monorepo setup separately).

---

## TECH STACK (MANDATORY)

- **Next.js 14** App Router (ONLY — never Pages Router)
- **TypeScript 5** strict mode (no `any`)
- **Tailwind CSS 4** (`@import "tailwindcss"` in globals.css, `@theme {}` block, NO tailwind.config.js)
- **shadcn/ui** (base components, use `cn()` for styling)
- **Framer Motion** (all animations)
- **Recharts** (radar chart, line chart)
- **react-i18next** (AZ primary, EN secondary)
- **Zustand** (client state)
- **TanStack Query v5** (server state & mutations)
- **React Hook Form + Zod** (form validation)
- **Lucide React** (icons)
- **Sonner** (toast notifications)
- **@ducanh2912/next-pwa** (PWA offline support)

---

## DESIGN SYSTEM

### Colors (OKLCH — COPY EXACTLY)

All colors are oklch() — CSS Variable values for `globals.css` `@theme {}` block:

```
Light mode (default):
  --background: oklch(0.985 0.002 260)      /* Off-white */
  --foreground: oklch(0.15 0.03 260)        /* Near black */
  --card: oklch(1 0 0)                      /* Pure white */
  --primary: oklch(0.55 0.24 264)           /* Indigo — main CTA */
  --primary-hover: oklch(0.48 0.24 264)     /* Darker indigo */
  --secondary: oklch(0.97 0.005 260)        /* Light gray */
  --muted: oklch(0.55 0.03 260)             /* Muted gray */
  --accent: oklch(0.65 0.20 264)            /* Purple accent */
  --destructive: oklch(0.58 0.24 27)        /* Red */
  --border: oklch(0.93 0.005 260)           /* Light border */
  --success: oklch(0.70 0.17 165)           /* Green */
  --warning: oklch(0.75 0.18 80)            /* Amber */
  --success-badge: #10B981                  /* Emerald for success */
  --info-badge: #3B82F6                     /* Blue for info */
  --warning-badge: #F59E0B                  /* Amber for warning */
  --error-badge: #EF4444                    /* Red for error */

Badge Tier Colors:
  --platinum: #A78BFA                       /* Purple */
  --gold: #EAB308                           /* Yellow */
  --silver: #94A3B8                         /* Slate */
  --bronze: #D97706                         /* Amber */

Dark mode:
  --background: oklch(0.13 0.03 260)        /* Deep navy */
  --foreground: oklch(0.93 0.01 260)        /* Off-white text */
  --card: oklch(0.18 0.02 260)              /* Darker card */
  --border: oklch(0.25 0.02 260)            /* Dark border */
  --primary: oklch(0.65 0.20 264)           /* Lighter indigo for dark mode */
```

### Typography

- **Body font:** Inter (Google Fonts, import in layout)
- **Monospace:** JetBrains Mono (for scores/numbers)
- **Font sizes:** 12, 14, 16, 18, 20, 24, 30, 36, 48, 60px
- **Default weight:** 400 (regular), 500 (medium), 600 (semibold), 700 (bold), 900 (black)

### Spacing & Layout

- **Base unit:** 4px (use Tailwind defaults)
- **Border radius:**
  - Buttons/inputs: `rounded-lg` (8px)
  - Cards: `rounded-2xl` (16px)
  - Pills: `rounded-full` (999px)
- **Breakpoints:** 640 / 768 / 1024 / 1280 / 1536px (Tailwind standard)
- **Touch targets:** minimum 44×44px on mobile

### Animation System (Framer Motion)

Use these spring configs for all animations:

```ts
const springs = {
  default: { stiffness: 260, damping: 20 },   /* Standard spring */
  gentle:  { stiffness: 120, damping: 14 },   /* Slower, more elegant */
  bouncy:  { stiffness: 400, damping: 10 },   /* Quick, playful */
  stiff:   { stiffness: 500, damping: 30 },   /* Fast & firm */
};
```

**ALL animations must respect `prefers-reduced-motion`:**
```tsx
const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const motionConfig = prefersReducedMotion ? { duration: 0.01 } : springs.default;
```

Common animations:
- Fade in/out: `opacity` transition
- Scale on hover: `whileHover={{ scale: 1.05 }}`
- Slide in: `x: -20` → `x: 0` with transition
- Confetti burst on AURA completion (use `react-confetti`)
- Progress bar fill: width animation
- Radar chart appears with staggered children

---

## i18N KEYS (CRITICAL — ZERO HARDCODED STRINGS)

### Namespace Structure
All user-facing strings MUST use the `t()` function from react-i18next. Complete reference in `/sessions/amazing-lucid-babbage/mnt/VOLAURA/docs/I18N-KEYS.md`

Namespaces:
```
locales/{az,en}/common.json       — nav, buttons, generic (~35 keys)
locales/{az,en}/auth.json         — login, signup, verification (~18 keys)
locales/{az,en}/assessment.json   — questions UI, progress, instructions (~45 keys)
locales/{az,en}/results.json      — score reveal, badges, sharing (~32 keys)
locales/{az,en}/profile.json      — profile page, edit, public (~28 keys)
locales/{az,en}/events.json       — event listing, detail, registration (~22 keys)
locales/{az,en}/errors.json       — all error messages (~18 keys)
```

Each key is bilingual: `{ "az": "...", "en": "..." }`

**CRITICAL:** Never hardcode user-facing text. Always use `t()` function. See I18N-KEYS.md for complete key reference.

---

## ACCESSIBILITY REQUIREMENTS (MANDATORY)

ALL interactive elements MUST have proper ARIA labels and keyboard navigation:

### ARIA & Labels
```tsx
// Button without visible text
<button aria-label={t("common.actions.close")}>
  <X size={20} />
</button>

// Form fields
<label htmlFor="email">{t("auth.login.email_placeholder")}</label>
<input id="email" type="email" {...} />

// Icon buttons
<button
  aria-label={t("common.actions.share")}
  title={t("common.actions.share")}
>
  <Share2 size={20} />
</button>

// Tabs
<div role="tablist">
  <button role="tab" aria-selected={active} aria-controls="panel-1">
    {t("assessment.hub.in_progress")}
  </button>
</div>
<div role="tabpanel" id="panel-1">...</div>
```

### Focus Visible (Keyboard Navigation)
```css
/* In globals.css or component.module.css */
button:focus-visible,
a:focus-visible,
input:focus-visible,
select:focus-visible,
textarea:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}
```

All interactive elements must be reachable via Tab key with visible focus indicator.

### Prefers Reduced Motion (CRITICAL)
```tsx
// Respect user's motion preferences in ALL animations
const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// In Framer Motion:
<motion.div
  animate={{ opacity: 1 }}
  transition={prefersReducedMotion ? { duration: 0 } : { duration: 0.3 }}
>
  ...
</motion.div>

// In CSS animations:
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Color Contrast & Indicators
- All text must pass WCAG AA (4.5:1 for normal text, 3:1 for large text)
- Never use color ALONE to convey meaning — combine with icons, text, or patterns
- Disabled states must be visually distinct (not just opacity change)

### Touch Targets
- Minimum 44×44px (CSS `touch-action: manipulation`)
- Button padding: `px-4 py-2` minimum (16px + 8px each side = 44px total)

---

## ASSESSMENT FLOW UPDATES

### Modified Question Selection (3-5 per competency, variable)

```typescript
// Per competency:
// Questions assigned based on difficulty:
//   Easy (e.g., empathy): 3 questions
//   Medium (e.g., communication): 4 questions
//   Hard (e.g., english_proficiency): 5 questions
//
// Adaptive within assessment:
// - Start at difficulty 1 (easy)
// - If score > 70 → next difficulty +1
// - If score < 40 → next difficulty -1
// - Stay within 1-3 range
// - Select random unused question at current difficulty

interface QuestionConfig {
  competency: string;
  total_questions: 3 | 4 | 5;
  current_question: number;
  difficulty: 1 | 2 | 3;
}
```

### Resume Assessment Flow (In-Progress Assessments)

When user navigates to assessment hub:

```typescript
// Check for in_progress assessments
// If status='in_progress':
//    Show "Continue" button with progress: "Question 3/4"
// If status='completed':
//    Show "Reassess" button
// If status='not_started':
//    Show "Start" button

// Resume Modal (if in_progress exists):
<Dialog open={showResume}>
  <DialogTitle>{t("assessment.resume.title")}</DialogTitle>
  <Button onClick={() => continueAssessment(assessmentId)}>
    {t("assessment.resume.yes")}
  </Button>
  <Button onClick={() => restartAssessment(competency)}>
    {t("assessment.resume.restart")}
  </Button>
</Dialog>
```

### Async LLM Evaluation (Open Text Questions)

Frontend polling pattern for 202 responses:

```typescript
// 1. User submits open text answer
// 2. Backend returns 202 (Accepted) with { evaluation_status: "pending", response_id: "uuid", next_question: {...} }
// 3. Show "AI is evaluating..." UI with animated loader
// 4. If next_question exists, display it to user
// 5. Poll GET /api/v1/assessments/{id}/responses/{response_id}/status every 2-3 seconds
// 6. On completion, update response with score and feedback
// 7. If fallback_scored status, apply heuristic score and show banner

const pollForEvaluation = async (assessmentId: string, responseId: string) => {
  const maxAttempts = 30;  // ~90 seconds
  let attempts = 0;

  const poll = async () => {
    try {
      const res = await fetch(
        `/api/v1/assessments/${assessmentId}/responses/${responseId}/status`
      );
      const { data } = await res.json();

      if (data.status === "completed") {
        updateResponseScore(responseId, data.score, data.feedback);
        return;
      }

      if (data.status === "fallback_scored") {
        updateResponseScore(responseId, data.score, data.feedback);
        toastWarning(t("errors.EVALUATION_PENDING"));
        return;
      }

      if (attempts < maxAttempts) {
        attempts++;
        setTimeout(poll, 2000);
      }
    } catch (error) {
      console.error("Poll error:", error);
      if (attempts < maxAttempts) {
        attempts++;
        setTimeout(poll, 3000);
      }
    }
  };

  poll();
};
```

---

## ERROR HANDLING WITH ERROR CODE CATALOG

All API errors: `{ detail: { code: "ERROR_CODE", message: "human-readable" } }`

Error codes and i18n messages in errors.json:
- UNAUTHORIZED, FORBIDDEN, PROFILE_NOT_FOUND, ASSESSMENT_NOT_FOUND, EVENT_NOT_FOUND
- EVENT_FULL, ALREADY_REGISTERED, INSUFFICIENT_AURA, ASSESSMENT_ALREADY_COMPLETE
- COMPETENCY_IN_PROGRESS, INVALID_ANSWER_FORMAT, RATE_LIMIT_EXCEEDED
- LLM_EVALUATION_FAILED, EVALUATION_PENDING, NETWORK_ERROR, GENERIC_ERROR

See I18N-KEYS.md for complete error message catalog.

```typescript
const handleApiError = (error: ApiError) => {
  const errorKey = `errors.${error.detail?.code || "GENERIC_ERROR"}`;
  const message = t(errorKey);

  switch (error.detail?.code) {
    case "UNAUTHORIZED":
      window.location.href = "/login";
      break;
    case "RATE_LIMIT_EXCEEDED":
      toastError(message);
      disableFormFor(60000);
      break;
    case "LLM_EVALUATION_FAILED":
      toastWarning(message);
      break;
    default:
      toastError(message);
  }
};
```

---

## ANALYTICS & TRACKING

### Core Analytics Events

```typescript
type AnalyticsEvent =
  | { name: "user_signup"; props: { source: "organic" | "referral" | "wuf13" | "google"; locale: "az" | "en" } }
  | { name: "assessment_started"; props: { competency: string; locale: string } }
  | { name: "assessment_completed"; props: { competency: string; score: number; time_seconds: number; question_count: number } }
  | { name: "aura_calculated"; props: { score: number; tier: string; old_score?: number } }
  | { name: "score_shared"; props: { platform: "linkedin" | "instagram" | "copy" | "qr"; score: number } }
  | { name: "profile_viewed"; props: { is_own: boolean; from_referral: boolean; username: string } }
  | { name: "event_registered"; props: { event_id: string; org_id: string; event_name: string } }
  | { name: "referral_sent"; props: { method: "email" | "link"; email?: string } }
  | { name: "referral_converted"; props: { referrer_id: string; referred_user_id: string } };

const trackEvent = (event: AnalyticsEvent) => {
  if (window.gtag) window.gtag("event", event.name, event.props);
};
```

Emit events at:
- assessment_started: Click "Start" / "Continue"
- assessment_completed: POST /api/v1/assessments/{id}/complete success
- aura_calculated: AURA score updates
- score_shared: Click share button
- event_registered: POST /api/v1/events/{id}/register success

---

## UTM TRACKING ON SHARE LINKS

All share links include UTM parameters:

```typescript
const generateShareUrl = (username: string, platform: string) => {
  const baseUrl = `https://volaura.com/u/${username}`;
  const params = new URLSearchParams({
    utm_source: platform,
    utm_medium: "social",
    utm_campaign: "aura_badge",
    utm_content: "share_result",
  });
  return `${baseUrl}?${params.toString()}`;
};

const generateReferralUrl = (referralCode: string) => {
  const params = new URLSearchParams({
    ref: referralCode,
    utm_source: "referral",
    utm_medium: "email",
    utm_campaign: "invite_v1",
    utm_content: "friend_invite",
  });
  return `https://volaura.com/join?${params.toString()}`;
};
```

---

## OG TAGS & STRUCTURED DATA (JSON-LD)

### Dynamic OG Tags (Public Profile Pages)

```tsx
// app/(public)/u/[username]/page.tsx
export async function generateMetadata({ params }): Promise<Metadata> {
  const { username } = await params;
  const profile = await fetchUserProfile(username);
  const tier = getTierFromScore(profile.aura_score);

  return {
    title: `${profile.full_name} — ${tier} Volunteer (AURA ${profile.aura_score})`,
    description: `Verified volunteer on Volaura. ${profile.bio || ""}`,

    openGraph: {
      title: `${profile.full_name} — ${tier} Volunteer`,
      description: profile.bio || "Verified volunteer",
      images: [
        {
          url: `https://volaura.com/api/og/${username}?tier=${tier}&score=${profile.aura_score}`,
          width: 1200,
          height: 627,
          alt: `${profile.full_name}'s AURA Badge`,
        },
      ],
      url: `https://volaura.com/u/${username}`,
      type: "profile",
    },

    twitter: {
      card: "summary_large_image",
      title: `${profile.full_name} — ${tier} Volunteer`,
      images: [`https://volaura.com/api/og/${username}`],
    },
  };
}
```

### Dynamic OG Image Generation

```tsx
// app/api/og/[username]/route.tsx
import { ImageResponse } from "@vercel/og";

export async function GET(request: Request, { params }: { params: { username: string } }) {
  const profile = await fetchUserProfile(params.username);
  const tier = getTierFromScore(profile.aura_score);
  const tierColor = { platinum: "#A78BFA", gold: "#EAB308", silver: "#94A3B8", bronze: "#D97706", none: "#6B7280" }[tier];

  return new ImageResponse(
    (
      <div style={{ width: "1200px", height: "627px", background: `linear-gradient(135deg, ${tierColor}33 0%, ${tierColor}99 100%)`, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", color: "white", fontFamily: "Inter" }}>
        <div style={{ fontSize: "48px", fontWeight: "bold" }}>{profile.full_name}</div>
        <div style={{ fontSize: "56px", fontWeight: "900", fontFamily: "JetBrains Mono" }}>{profile.aura_score}</div>
        <div style={{ fontSize: "28px", marginTop: "8px" }}>{tier} Volunteer</div>
      </div>
    ),
    { width: 1200, height: 627 }
  );
}
```

---

## REFERRAL UI

### Referral Components

```tsx
// components/features/referral/referral-card.tsx
// Display: referral_code + copy button, stats (invited/converted), bonus info, "Send Invite" button

// components/features/referral/invite-modal.tsx
// Form: email input, optional message, send button

// components/features/referral/referral-banner.tsx
// On results page: "Invite friends and earn bonus" with CTA

// Add to i18n: referral.invite_friends, referral.your_code, referral.invited, referral.converted, referral.bonus_info, referral.send_invite, referral.share_success, referral.banner_text
```

---

## FILE STRUCTURE

```
src/
  app/
    [locale]/
      layout.tsx
      page.tsx
      (auth)/
        login/page.tsx
        callback/page.tsx
      (app)/
        layout.tsx
        dashboard/page.tsx
        assessment/page.tsx
        assessment/[id]/page.tsx
        assessment/results/page.tsx
        profile/page.tsx
        profile/edit/page.tsx
        settings/page.tsx
        notifications/page.tsx
        leaderboard/page.tsx
        events/page.tsx
        events/[id]/page.tsx
      (public)/
        u/[username]/page.tsx
    i18n.ts
    globals.css
    api/
      og/[username]/route.tsx
  components/
    ui/
      [shadcn components]
    features/
      navigation/
        app-sidebar.tsx
        bottom-nav.tsx
        top-bar.tsx
        language-switcher.tsx
        notification-dropdown.tsx
        theme-toggle.tsx
      assessment/
        question-card.tsx
        bars-scale.tsx
        mcq-options.tsx
        open-text-input.tsx
        assessment-progress.tsx
      score/
        aura-display.tsx
        radar-chart.tsx
        badge-chip.tsx
        score-counter.tsx
      profile/
        profile-header.tsx
        competency-breakdown.tsx
        share-buttons.tsx
        verification-badges.tsx
      referral/
        referral-card.tsx
        invite-modal.tsx
        referral-banner.tsx
      events/
        event-card.tsx
        event-list.tsx
        event-detail.tsx
        event-filter.tsx
      common/
        empty-state.tsx
        loading-skeleton.tsx
        confetti.tsx
        notification-toast.tsx
    providers/
      translations-provider.tsx
      theme-provider.tsx
      query-provider.tsx
      analytics-provider.tsx
  lib/
    utils/
      cn.ts
      analytics.ts
      error-handler.ts
      share.ts
    api/
      mock-data.ts
      types.ts
      client.ts
  stores/
    auth-store.ts
    assessment-store.ts
    referral-store.ts
  locales/
    az/
      common.json
      auth.json
      assessment.json
      results.json
      profile.json
      events.json
      errors.json
      referral.json
    en/
      [same]
```

---

## MODULES A-H (GENERATION CHECKLIST)

### MODULE A: Project Setup & Tailwind 4
- app/[locale]/layout.tsx
- app/globals.css (Tailwind 4 with @theme {})
- app/i18n.ts
- components/providers/*.tsx (Query, Theme, Translations, Analytics)
- lib/utils/cn.ts, analytics.ts, error-handler.ts, share.ts
- lib/api/mock-data.ts, types.ts, client.ts
- stores/auth-store.ts, assessment-store.ts, referral-store.ts

### MODULE B: Navigation & Layout
- components/features/navigation/* (6 components)
- app/(app)/layout.tsx

### MODULE C: Authentication
- app/(auth)/login/page.tsx, callback/page.tsx
- stores/auth-store.ts
- lib/api/client.ts

### MODULE D: Dashboard & Score
- app/(app)/dashboard/page.tsx
- components/features/score/* (6 components)
- stores/assessment-store.ts

### MODULE E: Assessment
- app/(app)/assessment/page.tsx
- app/(app)/assessment/[id]/page.tsx
- components/features/assessment/* (7 components)

### MODULE F: Results & Sharing
- app/(app)/assessment/results/page.tsx
- app/(app)/profile/page.tsx
- app/(app)/profile/edit/page.tsx
- app/(public)/u/[username]/page.tsx
- app/api/og/[username]/route.tsx
- components/features/profile/* (6 components)

### MODULE G: Events & Leaderboard
- app/(app)/events/page.tsx
- app/(app)/events/[id]/page.tsx
- app/(app)/leaderboard/page.tsx
- components/features/events/* (4 components)

### MODULE H: Settings, Notifications & Polish
- app/(app)/settings/page.tsx
- app/(app)/notifications/page.tsx
- components/features/referral/* (3 components)
- components/common/* (6+ components)
- lib/utils/error-handler.ts, analytics.ts
- components/providers/analytics-provider.tsx
- app/error.tsx

---

## TESTING CHECKLIST

1. Responsive: 360px, 768px, 1440px
2. Dark mode: All colors work
3. i18n: AZ/EN switch, text expands properly
4. Animations: prefers-reduced-motion disables animations
5. Keyboard: Tab navigation, focus-visible on all interactive elements
6. Touch: 44×44px minimum buttons
7. Loading: Skeleton states visible
8. Empty: No data states render
9. Errors: Error toasts with correct messages
10. Performance: Lighthouse 90+
11. Async LLM: Polling for 202 responses works
12. Resume: Continue in_progress assessments
13. Referral: Code copy, invite form, bonus display

---

**THIS PROMPT IS SELF-CONTAINED. Copy everything and send to v0.dev. Generate one module at a time. Test each module before moving to the next.**
