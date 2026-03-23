# Component Library
## Volaura Design System

**Last Updated:** March 22, 2026
**Stack:** Next.js 14 App Router · shadcn/ui · Tailwind CSS 4 · Framer Motion
**Color System:** [[BRAND-IDENTITY#Color System|oklch]]

---

## Navigation Components

### Component: AppSidebar
**Status:** Existing
**File:** `components/navigation/app-sidebar.tsx`
**Tech:** shadcn/ui Sidebar primitive + Zustand state

#### Description
Desktop-only left sidebar providing main navigation, user profile access, and authentication state. Always visible on desktop (≥1024px). Hidden on mobile/tablet. Contains logo, nav links grouped by feature area, and collapsible user profile section at bottom.

#### Variants
| Variant | Use When |
|---------|----------|
| expanded | Desktop default, ≥80px width |
| collapsed | Hover/click to minimize, icon-only mode |
| loading | Initial page load, skeleton nav items |

#### Props
| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `isOpen` | boolean | true | No | Controls expanded/collapsed state |
| `onToggle` | (isOpen: boolean) => void | — | No | Callback when user toggles sidebar |
| `user` | User \| null | null | No | Current user object for profile section |
| `currentPath` | string | "/" | No | Active route for highlight |

#### States
| State | Visual | Behavior |
|-------|--------|----------|
| Expanded | Full width, labels visible | Shows all navigation labels and user name |
| Collapsed | Icon-only, 80px width | Tooltip on hover shows full label |
| Loading | Skeleton placeholders | Disabled interaction until hydrated |
| Empty auth | Login prompt instead of user | Directs unauthenticated to login |
| Hover (nav item) | Subtle background highlight | Not clickable until route changes |

#### Accessibility
- **Role:** navigation
- **Keyboard:** Arrow keys navigate, Enter/Space activate links
- **Screen reader:** Skip link provided, current page marked with aria-current="page"
- **Focus:** Visible focus ring on all interactive items
- **ARIA:** aria-expanded for collapsible sections

#### Code Example
```tsx
import { AppSidebar } from "@/components/navigation/app-sidebar";

export default function Layout({ children }) {
  return (
    <div className="flex min-h-screen">
      <AppSidebar />
      <main className="flex-1">{children}</main>
    </div>
  );
}
```

---

### Component: BottomNavV2
**Status:** Existing
**File:** `components/navigation/bottom-nav-v2.tsx`
**Tech:** Mobile-first, dismiss on scroll, badge support

#### Description
Mobile/tablet bottom tab navigation (visible <1024px only). Fixed to viewport bottom. 5 main sections: Home, Assessments, Leaderboard, Events, Profile. Active tab indicated by highlight and icon change. Shows unread badge count on relevant tabs.

#### Variants
| Variant | Use When |
|---------|----------|
| default | Regular tab bar with all 5 items visible |
| with-badge | Unread notifications/messages present |
| floating | Slightly lifted with shadow (future: spring physics) |

#### Props
| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `activeTab` | string | "home" | No | Currently active tab ID |
| `onTabChange` | (tab: string) => void | — | No | Fires when user taps a tab |
| `badges` | Record<string, number> | {} | No | Badge counts per tab (assessments: 2) |
| `hideOnScroll` | boolean | true | No | Auto-hide on downward scroll |

#### States
| State | Visual | Behavior |
|-------|--------|----------|
| Active | Primary color icon + label | Navigation to that section |
| Inactive | Gray icon + muted label | Tap to navigate |
| Badge | Red dot/circle with count | Shows notification count |
| Scrolling down | Slides below viewport | Auto-hide to maximize content space |
| Scrolling up | Slides above viewport | Auto-show when user scrolls up |

#### Accessibility
- **Role:** tablist
- **Keyboard:** Tab cycles through items, Enter/Space activate
- **Screen reader:** aria-selected for active tab, aria-label for badges
- **Touch:** Minimum 44px touch target per WCAG

#### Code Example
```tsx
import { BottomNavV2 } from "@/components/navigation/bottom-nav-v2";

export function MobileLayout() {
  const [active, setActive] = useState("home");
  return (
    <>
      <BottomNavV2 activeTab={active} onTabChange={setActive} badges={{ assessments: 2 }} />
    </>
  );
}
```

---

### Component: TopBarV2
**Status:** Existing
**File:** `components/navigation/top-bar-v2.tsx`
**Tech:** Sticky header, context-aware actions

#### Description
Mobile header bar (visible <1024px only). Fixed to top with subtle shadow. Left: back button (or menu toggle on root pages). Center: page title. Right: 1-2 action icons (search, menu, settings). Dismisses on scroll down, reappears on scroll up.

#### Variants
| Variant | Use When |
|---------|----------|
| default | Standard header with back button |
| root-page | Home/landing page, shows logo or menu icon |
| with-search | Pages that have search functionality |
| action-heavy | Up to 2 action icons on right |

#### Props
| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `title` | string | "" | No | Page title to display |
| `backHref` | string \| null | null | No | Link for back button; null hides it |
| `actions` | Action[] | [] | No | Array of icon actions on right |
| `sticky` | boolean | true | No | Stick to top or scroll with content |

#### States
| State | Visual | Behavior |
|-------|--------|----------|
| Visible | Solid background + shadow | Full interaction |
| Hidden (scroll down) | Slides above viewport | Content gains full height |
| Back button active | Icon highlighted | Navigates to previous page |
| Action button hover | Subtle background change | Ready to tap |

#### Accessibility
- **Role:** banner
- **Keyboard:** Tab to navigate actions, Enter to activate
- **Screen reader:** aria-label on back button, title read at top
- **Focus:** Visible ring on all buttons

#### Code Example
```tsx
import { TopBarV2 } from "@/components/navigation/top-bar-v2";

export function AssessmentPage() {
  return (
    <TopBarV2
      title="Communication Assessment"
      backHref="/assessments"
    />
  );
}
```

---

## Score & Badge Components

### Component: BadgeTierChip
**Status:** Existing
**File:** `components/badges/badge-tier-chip.tsx`
**Tech:** Conditional color styling, icon support

#### Description
Small colored badge/chip indicating credential tier: Platinum (≥90), Gold (≥75), Silver (≥60), Bronze (≥40), None (<40). Used on profiles, leaderboards, event listings, and AURA cards. Includes optional icon and animated pulse on achievement.

#### Variants
| Variant | Use When |
|---------|----------|
| Platinum | AURA score ≥ 90 |
| Gold | AURA score 75-89 |
| Silver | AURA score 60-74 |
| Bronze | AURA score 40-59 |
| None | AURA score < 40 |
| with-icon | Show verification/tier icon |
| compact | Small size for tables/lists |
| large | Hero display on profiles |

#### Props
| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `tier` | "platinum" \| "gold" \| "silver" \| "bronze" \| "none" | "none" | Yes | Badge tier level |
| `showIcon` | boolean | true | No | Display tier icon |
| `size` | "sm" \| "md" \| "lg" | "md" | No | Badge dimensions |
| `animated` | boolean | false | No | Show pulse animation on mount |
| `label` | string | undefined | No | Custom label (overrides tier name) |

#### States
| State | Visual | Behavior |
|-------|--------|----------|
| Platinum | [[BRAND-IDENTITY#Color System|oklch(0.85 0.05 270)]] + icon | Premium tier indicator |
| Gold | [[BRAND-IDENTITY#Color System|oklch(0.80 0.18 85)]] + icon | High achievement |
| Silver | [[BRAND-IDENTITY#Color System|oklch(0.75 0.03 260)]] + icon | Mid achievement |
| Bronze | [[BRAND-IDENTITY#Color System|oklch(0.65 0.12 55)]] + icon | Entry-level achievement |
| None | Gray neutral | Below threshold |
| Animated | Pulse effect 400ms | New badge unlock |

#### Accessibility
- **Role:** img or status depending on context
- **ARIA:** aria-label describes tier (e.g., "Platinum badge")
- **Color:** Not sole indicator, always has icon + text

#### Code Example
```tsx
import { BadgeTierChip } from "@/components/badges/badge-tier-chip";

export function ProfileCard({ score }) {
  const tier = getTierFromScore(score);
  return (
    <div>
      <BadgeTierChip tier={tier} size="lg" animated={true} />
    </div>
  );
}
```

---

### Component: CompetencyBar
**Status:** Existing
**File:** `components/competencies/competency-bar.tsx`
**Tech:** SVG progress bar, gradient fill

#### Description
Horizontal progress bar representing single competency score (0-100). Shows: competency icon, name, score number, and filled bar. Optional: trend arrow (↑/↓), comparison to personal best, target line.

#### Variants
| Variant | Use When |
|---------|----------|
| default | Standard competency progress display |
| with-trend | Show improvement/decline trend |
| with-target | Display target score line |
| compact | Minimal layout for lists |
| interactive | Tap to open competency detail modal |

#### Props
| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `competency` | Competency | — | Yes | Competency object (name, icon, color) |
| `score` | number | — | Yes | Current score 0-100 |
| `showTrend` | boolean | false | No | Display trend arrow if available |
| `targetScore` | number \| undefined | undefined | No | Show target line on bar |
| `maxScore` | number | 100 | No | Scale of bar |
| `color` | string | "var(--primary)" | No | Custom bar fill color |

#### States
| State | Visual | Behavior |
|-------|--------|----------|
| Low (0-40) | Minimal fill, gray color | Below threshold |
| Medium (40-70) | 40-70% fill, yellow/amber | Developing |
| High (70-90) | 70-90% fill, primary color | Strong |
| Excellence (90-100) | Full fill, primary gradient | Peak performance |
| Trending up | Green ↑ arrow | Recent improvement |
| Trending down | Red ↓ arrow | Recent decline |

#### Accessibility
- **Role:** progressbar
- **ARIA:** aria-valuenow, aria-valuemin, aria-valuemax
- **Screen reader:** "Communication: 78 out of 100"

#### Code Example
```tsx
import { CompetencyBar } from "@/components/competencies/competency-bar";

export function AssessmentResults() {
  return (
    <div className="space-y-4">
      {competencies.map((comp) => (
        <CompetencyBar
          key={comp.id}
          competency={comp}
          score={scores[comp.id]}
          showTrend={true}
        />
      ))}
    </div>
  );
}
```

---

### Component: RadarChart
**Status:** Existing
**File:** `components/visualizations/radar-chart.tsx`
**Tech:** Recharts, 8-axis polygon, animated on load

#### Description
Interactive 8-axis radar chart visualizing all AURA competencies: communication, reliability, english_proficiency, leadership, event_performance, tech_literacy, adaptability, empathy_safeguarding. Animated on mount. Colored regions show comparison (personal vs. peer average vs. target). Used on profile pages and dashboard.

#### Variants
| Variant | Use When |
|---------|----------|
| personal-only | Just user's scores |
| with-average | Compare to peer average benchmark |
| with-target | Show aspirational targets |
| interactive-hover | Hover axis to see details |
| static | No animation (initial page load optimization) |

#### Props
| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `data` | RadarData[] | — | Yes | Array of competency scores (8 items) |
| `comparison` | RadarData[] \| undefined | undefined | No | Benchmark/peer average data overlay |
| `target` | RadarData[] \| undefined | undefined | No | Target scores overlay |
| `animated` | boolean | true | No | Animate on mount (disable if page heavy) |
| `height` | number | 300 | No | Chart height in px |

#### States
| State | Visual | Behavior |
|-------|--------|----------|
| Loading | Skeleton outline | Placeholder until data loads |
| Mounted | Full opacity + animation | Chart animates from center out |
| Hover (axis) | Highlight that axis label + tooltip | Shows exact score for competency |
| Multiple overlays | 3 distinct fill colors | Personal (primary), average (secondary), target (tertiary) |

#### Accessibility
- **Role:** img
- **ARIA:** aria-label describing chart purpose
- **Alternative text:** Data table below chart for screen readers
- **Keyboard:** No interaction (visual-only for now)

#### Code Example
```tsx
import { RadarChart } from "@/components/visualizations/radar-chart";

export function ProfileDashboard({ userScores, peerAverage }) {
  const radarData = competencies.map((comp) => ({
    name: comp.name,
    value: userScores[comp.id],
  }));

  return (
    <RadarChart
      data={radarData}
      comparison={peerAverage}
      animated={true}
    />
  );
}
```

---

### Component: ScoreDisplay
**Status:** Existing
**File:** `components/visualizations/score-display.tsx`
**Tech:** Framer Motion, animated number counter, spring physics

#### Description
Large, prominent display of AURA score (0-100) with animated counter effect and optional pulse animation. Shows the score prominently during results reveal. Includes label ("Your AURA Score") and optional subtitle (badge tier).

#### Variants
| Variant | Use When |
|---------|----------|
| reveal | Results page, animates from 0 to final score |
| static | Profile display, no animation |
| large | Hero size (48-72px font) |
| compact | Smaller size for cards (24-30px font) |
| with-pulse | Newly achieved milestone |

#### Props
| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `score` | number | — | Yes | Score value 0-100 |
| `animate` | boolean | true | No | Animate counter from 0 to score |
| `duration` | number | 1.2 | No | Animation duration in seconds |
| `showPulse` | boolean | false | No | Add pulse effect after animation |
| `size` | "sm" \| "md" \| "lg" | "md" | No | Display size variant |
| `label` | string | "Your AURA Score" | No | Text label above number |
| `subtitle` | string \| undefined | undefined | No | Text below number (e.g., "Gold") |

#### States
| State | Visual | Behavior |
|-------|--------|----------|
| Animating | Counter increments 0→score | Spring easing, responsive to value |
| Idle | Static number display | No animation |
| Pulse active | Soft glow around number | Indicates achievement/milestone |

#### Accessibility
- **Role:** heading or status
- **ARIA:** aria-label="Your AURA score is 85"
- **Motion:** Respects prefers-reduced-motion, instant display if enabled

#### Code Example
```tsx
import { ScoreDisplay } from "@/components/visualizations/score-display";

export function ResultsPage({ finalScore }) {
  return (
    <ScoreDisplay
      score={finalScore}
      animate={true}
      duration={1.5}
      size="lg"
      showPulse={true}
    />
  );
}
```

---

### Component: SkillDNA
**Status:** Planned
**File:** `components/visualizations/skill-dna.tsx`
**Tech:** SVG double helix, animated strands, interactive labels

#### Description
Complex 3D-inspired visualization of competency relationships and interdependencies. Renders as DNA double helix where each base pair represents a competency node. Interaction: hover strands to highlight related competencies. Used on advanced profile pages and reports to show how skills reinforce each other.

**Note:** This is a planned component. Design and implementation TBD post-launch.

#### Variants
| Variant | Use When |
|---------|----------|
| overview | Show full competency network at glance |
| focused | Highlight one competency + related ones |
| interactive | Allow dragging/exploring connections |

#### Props (Proposed)
| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `competencies` | CompetencyNode[] | — | Yes | Network node data |
| `connections` | Connection[] | — | Yes | Edges between competencies |
| `highlightId` | string \| null | null | No | Competency to highlight |

---

## Assessment Components

### Component: QuestionCardV2
**Status:** Existing
**File:** `components/assessment/question-card-v2.tsx`
**Tech:** Conditional rendering per question type, form integration

#### Description
Renders a single assessment question supporting three types:
1. **BARS (Behavioural Anchored Rating Scale):** 1-5 Likert scale with descriptions
2. **MCQ (Multiple Choice):** 4 options, single selection
3. **Open Text:** Free-form text input with character counter

Integrates with React Hook Form for validation and state. Shows question number, competency label, and optional explanation/instruction text.

#### Variants
| Variant | Use When |
|---------|----------|
| BARS | Likert-style self-assessment |
| MCQ | Knowledge-based or scenario questions |
| Open Text | Short answer (evaluated by LLM) |
| readonly | Review mode, no interaction |
| submitted | After submission, show score |

#### Props
| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `question` | Question | — | Yes | Question object (type, text, options) |
| `questionNumber` | number | — | Yes | Position in assessment (1/20) |
| `value` | string \| number \| null | null | No | Current answer value |
| `onChange` | (value: any) => void | — | No | Form handler for answer |
| `disabled` | boolean | false | No | Disable interaction (readonly) |
| `showScore` | boolean | false | No | Display LLM evaluation score |
| `error` | string \| undefined | undefined | No | Validation error message |

#### States
| State | Visual | Behavior |
|-------|--------|----------|
| Unanswered | Empty state, no highlight | Awaiting user input |
| Focused | Input highlighted, cursor visible | Active interaction |
| Answered | Value selected/entered, saved | Shows checkmark or badge |
| Submitted | Grayed out, locked | Review mode only |
| Error | Red border + error message | Validation failed |

#### Accessibility
- **Role:** article or form field
- **Keyboard:** Tab to navigate, arrow keys for BARS, Enter for MCQ
- **Screen reader:** Full question text read, options enumerated
- **Labels:** Explicit `<label>` for form fields

#### Code Example
```tsx
import { QuestionCardV2 } from "@/components/assessment/question-card-v2";
import { useForm } from "react-hook-form";

export function AssessmentFlow() {
  const { watch, setValue } = useForm();
  const currentAnswer = watch(`questions.${index}`);

  return (
    <QuestionCardV2
      question={questions[index]}
      questionNumber={index + 1}
      value={currentAnswer}
      onChange={(val) => setValue(`questions.${index}`, val)}
    />
  );
}
```

---

### Component: CompetencyCard
**Status:** Existing
**File:** `components/competencies/competency-card.tsx`
**Tech:** Card layout, icon system, mini bar chart

#### Description
Overview card for a single competency showing: icon, name, current score, tier badge, trend (↑/↓), and optional description. Clickable to open detailed competency breakdown modal. Used on dashboard and competency list pages.

#### Variants
| Variant | Use When |
|---------|----------|
| compact | List view, minimal detail |
| expanded | Dashboard card, more information |
| interactive | Clickable to modal |
| locked | Competency not yet assessed |

#### Props
| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `competency` | Competency | — | Yes | Competency data (id, name, icon) |
| `score` | number \| null | null | No | Current score or null if locked |
| `trend` | "up" \| "down" \| null | null | No | Trend indicator |
| `previousScore` | number \| undefined | undefined | No | Last assessment score for trend calc |
| `onClick` | () => void | — | No | Handler for card click |
| `locked` | boolean | false | No | Show locked state |

#### States
| State | Visual | Behavior |
|-------|--------|----------|
| Unlocked + Scored | Full data visible | Click opens detail modal |
| Unlocked + Not Scored | Score shows as "—" | Can take assessment |
| Locked | Grayed out, lock icon | Must complete prerequisites |
| Trending up | Green ↑ indicator | Shows improvement |
| Trending down | Red ↓ indicator | Shows decline |
| Hover | Subtle lift/shadow | Ready for interaction |

#### Accessibility
- **Role:** article or button
- **ARIA:** aria-label describes competency and score
- **Keyboard:** Tab and Enter to interact

#### Code Example
```tsx
import { CompetencyCard } from "@/components/competencies/competency-card";

export function CompetenciesDashboard({ competencies, scores }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {competencies.map((comp) => (
        <CompetencyCard
          key={comp.id}
          competency={comp}
          score={scores[comp.id]}
          onClick={() => openModal(comp.id)}
        />
      ))}
    </div>
  );
}
```

---

### Component: AssessmentResults
**Status:** Existing
**File:** `components/assessment/assessment-results.tsx`
**Tech:** Framer Motion confetti, staggered reveal, share modal

#### Description
Full-page results screen shown after assessment completion. Includes: confetti animation, animated score reveal, badge tier display, competency breakdown, peer comparison radar chart, and prominent call-to-action buttons (share, print, continue).

#### Variants
| Variant | Use When |
|---------|----------|
| full-page | Desktop results page |
| modal | Mobile results dialog |
| summary | Quick view (no confetti) |
| printable | Print-optimized layout |

#### Props
| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `finalScore` | number | — | Yes | Total AURA score (0-100) |
| `competencyScores` | Record<string, number> | — | Yes | Per-competency scores |
| `assessmentId` | string | — | Yes | Assessment ID for tracking |
| `showConfetti` | boolean | true | No | Trigger confetti animation |
| `onShare` | () => void | — | No | Share button handler |
| `peerAverage` | number | undefined | No | Average score for comparison |

#### States
| State | Visual | Behavior |
|-------|--------|----------|
| Loading | Skeleton results layout | Data being fetched |
| Animating | Confetti + score counter | Results revealing in sequence |
| Ready | Full results visible | All interactions available |

#### Accessibility
- **Role:** main
- **ARIA:** aria-live="polite" for results announcement
- **Motion:** Respects prefers-reduced-motion, no confetti if reduced

#### Code Example
```tsx
import { AssessmentResults } from "@/components/assessment/assessment-results";

export function ResultsPage({ assessmentData }) {
  return (
    <AssessmentResults
      finalScore={assessmentData.totalScore}
      competencyScores={assessmentData.scores}
      assessmentId={assessmentData.id}
      showConfetti={true}
      onShare={() => openShareModal()}
    />
  );
}
```

---

## Event Components

### Component: EventCard
**Status:** Existing
**File:** `components/events/event-card.tsx`
**Tech:** Image handling, date formatting, registration state

#### Description
Event listing card showing: hero image, event title, date/time, location, AURA requirement badge, brief description, and register/registered button. Click card to view full event details. Used on event listings and search results.

#### Variants
| Variant | Use When |
|---------|----------|
| standard | Event listing view |
| compact | Grid view with minimal text |
| featured | Hero/featured event with larger image |
| registered | User has already registered |
| full-capacity | Event is full, registration disabled |

#### Props
| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `event` | Event | — | Yes | Event object (id, title, date, location) |
| `isRegistered` | boolean | false | No | User registration status |
| `canRegister` | boolean | true | No | Registration eligibility |
| `onRegister` | () => void | — | No | Registration button handler |
| `onClick` | () => void | — | No | Card click handler |
| `imageUrl` | string | undefined | No | Hero image URL |

#### States
| State | Visual | Behavior |
|-------|--------|----------|
| Available | Default card styling | Click to view, tap Register |
| Registered | Checkmark on button | Button shows "Registered" |
| Locked (low AURA) | Grayed out + lock icon | Tooltip explains AURA requirement |
| Full Capacity | Disabled state | "Event Full" message |
| Past Event | Grayed out + "Past Event" badge | No interaction |

#### Accessibility
- **Role:** article
- **ARIA:** aria-label includes event name, date, location
- **Keyboard:** Tab to card, Enter to expand, Tab to register button

#### Code Example
```tsx
import { EventCard } from "@/components/events/event-card";

export function EventsList({ events, registeredIds }) {
  return (
    <div className="grid gap-4">
      {events.map((event) => (
        <EventCard
          key={event.id}
          event={event}
          isRegistered={registeredIds.includes(event.id)}
          onClick={() => navigateTo(`/events/${event.id}`)}
        />
      ))}
    </div>
  );
}
```

---

### Component: EventRegistrationBadge
**Status:** Existing
**File:** `components/events/event-registration-badge.tsx`
**Tech:** Status-driven styling, tooltip support

#### Description
Small badge/chip indicating user's registration status for an event. States: "Registered" (checkmark), "Pending Approval" (hourglass), "Waitlisted" (queue position), "Not Registered" (empty). Optionally shows next action (e.g., "Leave Waitlist").

#### Variants
| Variant | Use When |
|---------|----------|
| registered | User confirmed for event |
| pending | Awaiting organizer approval |
| waitlisted | On queue, not yet confirmed |
| not-registered | No registration yet |
| with-action | Show secondary CTA (leave, cancel) |

#### Props
| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `status` | "registered" \| "pending" \| "waitlisted" \| "not_registered" | "not_registered" | Yes | Registration status |
| `position` | number \| undefined | undefined | No | Waitlist position if applicable |
| `onAction` | () => void | — | No | Handler for secondary action |
| `actionLabel` | string | "Cancel" | No | Label for secondary action |

#### States
| State | Visual | Behavior |
|-------|--------|----------|
| Registered | Green checkmark + "Registered" | Confirmed attendance |
| Pending | Yellow hourglass + "Pending" | Awaiting approval |
| Waitlisted | Blue queue + "Waitlist #2" | Shows queue position |
| Not Registered | Gray empty state | "Register" button shown elsewhere |

#### Accessibility
- **Role:** status
- **ARIA:** aria-label describes status (e.g., "Registered for Workshop on March 25")
- **Keyboard:** If action button, Tab and Enter activate

#### Code Example
```tsx
import { EventRegistrationBadge } from "@/components/events/event-registration-badge";

export function EventDetail({ registration }) {
  return (
    <EventRegistrationBadge
      status={registration.status}
      position={registration.waitlistPosition}
      onAction={() => cancelRegistration()}
      actionLabel="Leave Waitlist"
    />
  );
}
```

---

## Sharing Components

### Component: ShareButtons
**Status:** Existing
**File:** `components/sharing/share-buttons.tsx`
**Tech:** Social share intent URLs, native share API fallback

#### Description
Horizontal or vertical button set for sharing AURA score/badge. Platforms: LinkedIn (share to feed), Instagram Story (download badge image), copy link to clipboard. Each button has icon and optional label. Toast feedback on copy success.

#### Variants
| Variant | Use When |
|---------|----------|
| horizontal | Inline with content |
| vertical | Sidebar or compact column |
| icons-only | Minimal space, icon buttons |
| with-labels | Full clarity, button + label |
| compact | Small icon buttons, tight spacing |

#### Props
| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `shareUrl` | string | — | Yes | Full URL to share (badge/profile link) |
| `shareTitle` | string | "Check out my AURA badge" | No | Share title/caption |
| `shareImage` | string \| undefined | undefined | No | Image URL for share preview |
| `onCopy` | () => void | — | No | Callback when link copied |
| `showLabels` | boolean | true | No | Show text labels on buttons |
| `direction` | "horizontal" \| "vertical" | "horizontal" | No | Button layout direction |

#### States
| State | Visual | Behavior |
|-------|--------|----------|
| Default | Colored icons | Tap to share or copy |
| Hover | Subtle lift/shadow | Highlight action button |
| Copied | Toast notification | "Link copied to clipboard" |
| Error | Error toast | Failed share attempt |

#### Accessibility
- **Role:** group
- **ARIA:** aria-label="Share your AURA badge"
- **Keyboard:** Tab cycles, Enter activates button
- **Labels:** Icon buttons have title/aria-label

#### Code Example
```tsx
import { ShareButtons } from "@/components/sharing/share-buttons";

export function ProfileCard({ profileId, auraScore }) {
  const shareUrl = `${BASE_URL}/badges/${profileId}`;
  return (
    <ShareButtons
      shareUrl={shareUrl}
      shareTitle={`I just earned my verified AURA badge!`}
      onCopy={() => showToast("Link copied")}
    />
  );
}
```

---

### Component: AURACardPreview
**Status:** Existing
**File:** `components/sharing/aura-card-preview.tsx`
**Tech:** Canvas rendering or SVG generation for image export

#### Description
Shareable AURA score card preview (social-optimized dimensions 1200x630px or 1080x1080px). Shows: name, AURA score, badge tier, competency highlights, verification badge, QR code (optional), and brand footer. Used in share modal and download flows.

#### Variants
| Variant | Use When |
|---------|----------|
| horizontal | Facebook/LinkedIn 1200x630 |
| square | Instagram 1080x1080 |
| story | Instagram Story 1080x1920 |
| minimal | Text-only version (no QR) |
| with-qr | Include QR code linking to profile |

#### Props
| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `user` | User | — | Yes | User name, avatar, verified status |
| `score` | number | — | Yes | AURA score (0-100) |
| `tier` | Tier | — | Yes | Badge tier (Platinum/Gold/Silver/Bronze) |
| `topCompetencies` | Competency[] | — | Yes | Top 3 competencies with scores |
| `backgroundColor` | string | "oklch(0.98 0.005 270)" | No | Card background color |
| `includeQR` | boolean | false | No | Add QR code to card |

#### States
| State | Visual | Behavior |
|-------|--------|----------|
| Rendering | Skeleton layout | Image composing |
| Ready | Full card visible | Ready for download/share |
| Loading image | Placeholder | Avatar or background loading |

#### Accessibility
- **Role:** img
- **ARIA:** aria-label="AURA Score Card for [Name]: 85 Gold"
- **Alternative:** Always provide text version with data

#### Code Example
```tsx
import { AURACardPreview } from "@/components/sharing/aura-card-preview";

export function ShareModal({ user, assessment }) {
  return (
    <AURACardPreview
      user={user}
      score={assessment.finalScore}
      tier={getTierFromScore(assessment.finalScore)}
      topCompetencies={getTopThree(assessment.scores)}
      includeQR={true}
    />
  );
}
```

---

### Component: QRCodeBadge
**Status:** Existing
**File:** `components/sharing/qr-code-badge.tsx`
**Tech:** qrcode.react or zxing library

#### Description
SVG-rendered QR code that links to user's public profile or shared AURA badge. Embedded in AURA cards, printed certificates, and event materials. Customizable size and error correction level for reliability.

#### Variants
| Variant | Use When |
|---------|----------|
| default | Standard QR code |
| framed | QR with Volaura branding frame |
| small | Event/badge embeds (64px) |
| large | Print/poster (200px+) |

#### Props
| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `value` | string | — | Yes | URL to encode (public profile link) |
| `size` | number | 128 | No | QR code dimensions in px |
| `level` | "L" \| "M" \| "H" \| "Q" | "H" | No | Error correction level (H = 30% recovery) |
| `includeFrame` | boolean | false | No | Add Volaura brand frame |

#### Accessibility
- **Role:** img
- **ARIA:** aria-label="QR code linking to [user] profile"
- **Text:** Always include text link alternative

#### Code Example
```tsx
import { QRCodeBadge } from "@/components/sharing/qr-code-badge";

export function BadgeCard({ profileId }) {
  const profileUrl = `${BASE_URL}/badges/${profileId}`;
  return (
    <QRCodeBadge
      value={profileUrl}
      size={200}
      includeFrame={true}
    />
  );
}
```

---

## System Components

### Component: FloatingOrbs
**Status:** Existing
**File:** `components/decorative/floating-orbs.tsx`
**Tech:** Framer Motion, randomized animation, z-index management

#### Description
Decorative animated background element showing 3-5 glowing gradient orbs that float and drift across the viewport. Used on landing page hero, signup flow, and empty states. Non-interactive. Uses `fixed` positioning to create depth effect.

#### Variants
| Variant | Use When |
|---------|----------|
| landing-hero | Full landing page background |
| signin-page | Auth flow background |
| subtle | Lighter, smaller orbs (empty states) |
| dark | High-contrast for dark theme |

#### Props
| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `count` | number | 4 | No | Number of orbs to render |
| `animate` | boolean | true | No | Enable animation |
| `intensity` | "low" \| "medium" \| "high" | "medium" | No | Animation speed/opacity |
| `zIndex` | number | -10 | No | Z-index to render behind content |
| `colorScheme` | "primary" \| "accent" | "primary" | No | Color palette |

#### States
| State | Visual | Behavior |
|-------|--------|----------|
| Animating | Floating, drifting orbs with soft glow | Continuous smooth motion |
| Static | Orbs positioned, no movement | If animate=false |
| Responsive | Adjust size for mobile vs. desktop | Smaller on mobile |

#### Accessibility
- **Role:** presentation
- **ARIA:** aria-hidden="true" (purely decorative)
- **Motion:** Respects prefers-reduced-motion, minimal if enabled

#### Code Example
```tsx
import { FloatingOrbs } from "@/components/decorative/floating-orbs";

export function LandingHero() {
  return (
    <div className="relative w-full h-screen overflow-hidden">
      <FloatingOrbs count={5} intensity="high" />
      <div className="relative z-10">
        <h1>Volunteer Credentials, Verified</h1>
      </div>
    </div>
  );
}
```

---

### Component: LanguageSwitcher
**Status:** Existing
**File:** `components/system/language-switcher.tsx`
**Tech:** react-i18next, flag icons, dropdown menu

#### Description
Language toggle for AZ (Azerbaijani) / EN (English). Shown in top navigation or sidebar. Displays flag icon + language code. On selection, changes site language and reloads page or updates i18n context. Saves preference to localStorage.

#### Variants
| Variant | Use When |
|---------|----------|
| dropdown | Full menu (multiple languages, future) |
| toggle | Simple AZ/EN toggle |
| icon-only | Just flag in header |
| with-label | Flag + code text |

#### Props
| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `currentLanguage` | string | "az" | No | Current active language |
| `onLanguageChange` | (lang: string) => void | — | No | Callback when language changes |
| `showLabel` | boolean | true | No | Display language code label |
| `variant` | "dropdown" \| "toggle" | "dropdown" | No | UI style |

#### States
| State | Visual | Behavior |
|-------|--------|----------|
| Closed (dropdown) | Flag + code visible | Click to open menu |
| Open (dropdown) | Menu shows AZ, EN options | Select to change |
| Selected | Checkmark on current language | Applies i18n change |
| Mobile | Compact icon button | Touch-friendly |

#### Accessibility
- **Role:** button or combobox
- **ARIA:** aria-label="Change language", aria-expanded for dropdown
- **Keyboard:** Tab to button, arrow keys to navigate, Enter to select

#### Code Example
```tsx
import { LanguageSwitcher } from "@/components/system/language-switcher";

export function Header() {
  const { i18n } = useTranslation();
  return (
    <LanguageSwitcher
      currentLanguage={i18n.language}
      onLanguageChange={(lang) => i18n.changeLanguage(lang)}
    />
  );
}
```

---

### Component: NotificationDropdown
**Status:** Existing
**File:** `components/system/notification-dropdown.tsx`
**Tech:** Bell icon, popover, unread badge, dismiss actions

#### Description
Header notification center showing unread notifications in dropdown. Bell icon with red badge count. Popover menu lists recent notifications with action buttons (mark read, dismiss, view). Integration with backend notification system.

#### Variants
| Variant | Use When |
|---------|----------|
| default | Full notification list |
| compact | Mobile view, icons only |
| empty | No notifications, show empty state |
| loading | Fetching notifications |

#### Props
| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `notifications` | Notification[] | [] | No | List of notifications to display |
| `unreadCount` | number | 0 | No | Unread notification badge count |
| `onDismiss` | (id: string) => void | — | No | Handler to dismiss notification |
| `onMarkRead` | (id: string) => void | — | No | Handler to mark as read |
| `onViewNotification` | (id: string) => void | — | No | Handler to open notification detail |

#### States
| State | Visual | Behavior |
|-------|--------|----------|
| No notifications | Bell icon, gray, no badge | Show empty state text |
| Has unread | Bell icon + red badge count | Popover shows unread list |
| Dropdown open | Bell highlighted, popover visible | All interactions available |
| Notification hover | Subtle background highlight | Ready to dismiss/view |
| Dismissed | Notification removed from list | Slide out animation |

#### Accessibility
- **Role:** button (bell), menu (popover)
- **ARIA:** aria-label="Notifications", aria-expanded for dropdown, aria-label for badge
- **Keyboard:** Tab to bell, Enter opens, arrow keys navigate notifications

#### Code Example
```tsx
import { NotificationDropdown } from "@/components/system/notification-dropdown";

export function Header() {
  const { notifications, unreadCount } = useNotifications();
  return (
    <NotificationDropdown
      notifications={notifications}
      unreadCount={unreadCount}
      onDismiss={(id) => dismissNotification(id)}
    />
  );
}
```

---

### Component: OnboardingStep
**Status:** Existing
**File:** `components/system/onboarding-step.tsx`
**Tech:** Step indicator, form integration, progress bar

#### Description
Single step in multi-step onboarding flow. Shows: step number (1/5), progress bar, form fields for that step, and navigation buttons (Back/Next/Skip if allowed). Validates before advancing. Used in initial signup flow.

#### Variants
| Variant | Use When |
|---------|----------|
| form-step | Multi-field form step |
| choice-step | Single selection (e.g., role) |
| info-step | Display-only information |
| final-step | Last step with CTA (Complete) |

#### Props
| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `stepNumber` | number | — | Yes | Current step (1-indexed) |
| `totalSteps` | number | — | Yes | Total steps in flow |
| `title` | string | — | Yes | Step title/heading |
| `description` | string \| undefined | undefined | No | Optional step description |
| `onNext` | () => void | — | Yes | Handler for Next button |
| `onBack` | () => void | — | No | Handler for Back button |
| `canSkip` | boolean | false | No | Allow skip (if applicable) |
| `disabled` | boolean | false | No | Disable Next button |
| `children` | ReactNode | — | Yes | Form fields/content |

#### States
| State | Visual | Behavior |
|-------|--------|----------|
| Active | Full interaction, Next enabled if valid | Form input collected |
| Disabled | Next button grayed out | Validation pending |
| Validating | Loading spinner on Next | Async validation running |
| Completed | Checkmark shown, move to next step | Transition animation |

#### Accessibility
- **Role:** article or section
- **ARIA:** aria-label="Step 2 of 5: Enter your full name", aria-live for validation
- **Keyboard:** Tab through form, Enter submits if valid

#### Code Example
```tsx
import { OnboardingStep } from "@/components/system/onboarding-step";
import { useForm } from "react-hook-form";

export function OnboardingFlow() {
  const { register, handleSubmit, formState } = useForm();
  return (
    <OnboardingStep
      stepNumber={1}
      totalSteps={3}
      title="Tell us about yourself"
      onNext={handleSubmit(onNext)}
    >
      <input {...register("fullName", { required: true })} placeholder="Full Name" />
    </OnboardingStep>
  );
}
```

---

### Component: PageSkeleton
**Status:** Existing
**File:** `components/system/page-skeleton.tsx`
**Tech:** Shimmer animation, Tailwind placeholders, configurable layout

#### Description
Loading placeholder component that renders skeleton content while page data loads. Multiple variants: profile page, leaderboard, assessment flow, etc. Uses gray shimmer animation. Automatically replaced with real content when data arrives.

#### Variants
| Variant | Use When |
|---------|----------|
| profile | Profile page loading |
| leaderboard | Leaderboard table skeleton |
| assessment | Assessment questions skeleton |
| dashboard | Dashboard with cards skeleton |
| minimal | Simple content placeholder |

#### Props
| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `variant` | string | "minimal" | No | Skeleton layout template |
| `count` | number | 1 | No | Number of repeated items (list skeleton) |
| `animated` | boolean | true | No | Enable shimmer animation |

#### States
| State | Visual | Behavior |
|-------|--------|----------|
| Loading | Gray placeholder boxes with shimmer | Animated, shows data is loading |
| Replaced | Fades out as real content appears | Smooth transition |

#### Accessibility
- **Role:** presentation
- **ARIA:** aria-hidden="true" and aria-busy="true" on container
- **Text:** Hidden loading text for screen readers

#### Code Example
```tsx
import { PageSkeleton } from "@/components/system/page-skeleton";

export function ProfilePage() {
  const { data: profile, isLoading } = useProfile();

  if (isLoading) return <PageSkeleton variant="profile" />;

  return <ProfileContent profile={profile} />;
}
```

---

### Component: Toast
**Status:** Existing
**File:** `components/system/toast.tsx`
**Tech:** Headless UI or Radix UI, stacked queue, auto-dismiss

#### Description
Notification toast message appearing at bottom-right (or configurable corner). Types: success (green), error (red), info (blue), warning (yellow). Auto-dismisses after 3-5 seconds. Can be manually dismissed. Multiple toasts stack vertically.

#### Variants
| Variant | Use When |
|---------|----------|
| success | Action completed successfully |
| error | Action failed or error occurred |
| info | Neutral information message |
| warning | Caution/warning message |
| with-action | Toast with secondary action button |

#### Props
| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `type` | "success" \| "error" \| "info" \| "warning" | "info" | No | Toast type/color |
| `message` | string | — | Yes | Toast message text |
| `action` | { label: string; onClick: () => void } \| undefined | undefined | No | Optional action button |
| `duration` | number | 3000 | No | Auto-dismiss delay in ms (0 = manual only) |
| `position` | "top-left" \| "top-right" \| "bottom-left" \| "bottom-right" | "bottom-right" | No | Toast position |

#### States
| State | Visual | Behavior |
|-------|--------|----------|
| Entering | Slide/fade in from edge | Animation: 200ms |
| Visible | Full opacity, stacked above/below others | Visible and interactive |
| Dismissing | Fade out, slide away | Auto or manual dismiss |

#### Accessibility
- **Role:** alert or status (depending on type)
- **ARIA:** aria-label, aria-live="assertive" for alerts
- **Keyboard:** Esc to dismiss, Tab/Enter for actions
- **Motion:** Respects prefers-reduced-motion

#### Code Example
```tsx
import { useToast } from "@/hooks/use-toast";

export function MyComponent() {
  const { showToast } = useToast();

  const handleSubmit = async () => {
    try {
      await submitForm();
      showToast({ type: "success", message: "Saved successfully!" });
    } catch (error) {
      showToast({ type: "error", message: "Save failed. Try again." });
    }
  };

  return <button onClick={handleSubmit}>Save</button>;
}
```

---

### Component: EmptyState
**Status:** Existing
**File:** `components/system/empty-state.tsx`
**Tech:** Illustration asset, centered layout, CTA button

#### Description
Illustrated empty state shown when no data exists (no assessments, no events, empty leaderboard, etc.). Includes: SVG illustration, heading, descriptive text, and primary CTA button. Customizable per use case.

#### Variants
| Variant | Use When |
|---------|----------|
| no-assessments | User hasn't taken any assessments |
| no-events | No upcoming events matching filters |
| no-results | Search/filter returned no results |
| locked-feature | Feature requires higher AURA score |
| not-found | 404 page |
| no-connections | No network connections yet |

#### Props
| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `illustration` | ReactNode \| string | — | Yes | SVG or illustration component |
| `title` | string | — | Yes | Empty state heading |
| `description` | string | — | No | Detailed explanation text |
| `action` | { label: string; href?: string; onClick?: () => void } \| undefined | undefined | No | Primary CTA button |
| `secondaryAction` | Action \| undefined | undefined | No | Optional secondary link |

#### States
| State | Visual | Behavior |
|-------|--------|----------|
| Default | Illustration + text + CTA | Awaiting user action |
| With secondary action | Second link below primary | Multiple path options |

#### Accessibility
- **Role:** article or section
- **ARIA:** aria-label describes state
- **Illustration:** alt text or aria-label on SVG
- **Buttons:** Full keyboard support

#### Code Example
```tsx
import { EmptyState } from "@/components/system/empty-state";
import { EmptyAssessmentsIcon } from "@/components/icons";

export function AssessmentsList() {
  const { assessments } = useAssessments();

  if (assessments.length === 0) {
    return (
      <EmptyState
        illustration={<EmptyAssessmentsIcon />}
        title="No Assessments Yet"
        description="Start your first assessment to earn your AURA score."
        action={{ label: "Take Assessment", href: "/assessments/start" }}
      />
    );
  }

  return <AssessmentsTable assessments={assessments} />;
}
```

---

### Component: VerificationBadge
**Status:** Existing
**File:** `components/badges/verification-badge.tsx`
**Tech:** Status-driven icon, tooltip, color-coded

#### Description
Small icon badge indicating verification level: Self-assessed, Organization-verified, Peer-verified. Shows as small shield icon with color coding. Tooltip on hover explains meaning. Used alongside profile names, leaderboard entries, and event organizers.

#### Variants
| Variant | Use When |
|---------|----------|
| self | User self-assessed, not verified |
| org-verified | Verified by organization/employer |
| peer-verified | Peer-verified through assessment |
| multiple | User has multiple verification types |

#### Props
| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `verificationLevel` | "self" \| "org" \| "peer" | "self" | Yes | Verification type |
| `size` | "sm" \| "md" \| "lg" | "sm" | No | Icon size |
| `showTooltip` | boolean | true | No | Show explanation tooltip |
| `verified` | boolean | true | No | Whether verified or pending |

#### States
| State | Visual | Behavior |
|-------|--------|----------|
| Self | Gray shield | No external verification |
| Org Verified | Blue shield + checkmark | Verified by organization |
| Peer Verified | Green shield + multiple checkmarks | Verified by peers |
| Unverified | Outlined shield | Pending verification |
| Hover | Tooltip shows explanation | "Verified by [Org Name]" |

#### Accessibility
- **Role:** img
- **ARIA:** aria-label="Organization verified", aria-describedby for tooltip
- **Tooltip:** Title attribute fallback for screen readers

#### Code Example
```tsx
import { VerificationBadge } from "@/components/badges/verification-badge";

export function ProfileCard({ user }) {
  return (
    <div>
      <h3>
        {user.name}
        <VerificationBadge verificationLevel={user.verificationLevel} />
      </h3>
    </div>
  );
}
```

---

## Profile Components

### Component: ProfileHeader
**Status:** Existing
**File:** `components/profile/profile-header.tsx`
**Tech:** Avatar upload, header image, edit mode toggle

#### Description
Hero header section on user profile showing: large avatar (circular, editable), name, headline/role, AURA score with badge, verification level, and action buttons (Edit, Message, Share). Background image optional (blurred). Desktop and mobile-responsive.

#### Variants
| Variant | Use When |
|---------|----------|
| public-view | Viewing another user's profile |
| own-profile | Logged-in user viewing themselves |
| editing | User can edit avatar/header content |
| compact | Mobile view, condensed layout |

#### Props
| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `user` | User | — | Yes | User data (name, avatar, headline) |
| `auraScore` | number | — | Yes | Current AURA score |
| `tier` | Tier | — | Yes | Badge tier |
| `isOwnProfile` | boolean | false | No | Show edit controls if own profile |
| `onEdit` | () => void | — | No | Handler for Edit button |
| `onShare` | () => void | — | No | Handler for Share button |
| `backgroundImage` | string \| undefined | undefined | No | Optional header background URL |

#### States
| State | Visual | Behavior |
|-------|--------|----------|
| Public view | Profile info read-only | View and share buttons visible |
| Own profile | Edit button visible | Can edit profile fields |
| Editing | Avatar upload, text inputs enabled | Save/Cancel buttons shown |
| Loading | Skeleton placeholder | Data being fetched |

#### Accessibility
- **Role:** banner or region
- **ARIA:** aria-label describes profile
- **Keyboard:** Tab to Edit/Share buttons, Enter activates
- **Image:** alt text on avatar

#### Code Example
```tsx
import { ProfileHeader } from "@/components/profile/profile-header";

export function ProfilePage({ userId }) {
  const { user, score } = useUserProfile(userId);
  const isOwnProfile = useAuthStore((s) => s.userId === userId);

  return (
    <ProfileHeader
      user={user}
      auraScore={score}
      tier={getTier(score)}
      isOwnProfile={isOwnProfile}
      onEdit={() => setEditMode(true)}
    />
  );
}
```

---

### Component: AURAJourneyTimeline
**Status:** Planned
**File:** `components/profile/aura-journey-timeline.tsx`
**Tech:** Vertical timeline, milestone markers, animated reveals

#### Description
Timeline visualization showing user's AURA score progression over time. Each assessment appears as a milestone on the timeline with: date, score change (↑/↓), competencies improved, and optional achievements unlocked. Interactive: click milestone to view assessment details.

**Note:** Planned for post-launch. Requires assessment history data structure.

#### Variants
| Variant | Use When |
|---------|----------|
| full-history | Show all assessments in reverse chronological |
| last-90-days | Recent activity view |
| milestones-only | Show only significant jumps |

#### Props (Proposed)
| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `assessments` | Assessment[] | — | Yes | Historical assessment records |
| `highlightMilestones` | Milestone[] | [] | No | Special achievements to highlight |

---

### Component: CountdownWidget
**Status:** Existing
**File:** `components/widgets/countdown-widget.tsx`
**Tech:** Interval timer, formatted display, urgency colors

#### Description
Animated countdown to major launch event in Baku (May 2026). Shows: days, hours, minutes remaining. Used on landing page, dashboard, and signup CTAs. Color coding: green (plenty of time), yellow (getting close), red (very soon). Includes "Register" CTA.

#### Variants
| Variant | Use When |
|---------|----------|
| large | Landing page hero |
| compact | Sidebar widget |
| inline | In-text mention |
| urgent | Last week reminder |

#### Props
| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `targetDate` | Date | May 15, 2026 | No | Event date to count down to |
| `showCTA` | boolean | true | No | Display Register button |
| `size` | "sm" \| "md" \| "lg" | "md" | No | Display size |
| `format` | "full" \| "compact" \| "inline" | "full" | No | Layout variant |

#### States
| State | Visual | Behavior |
|-------|--------|----------|
| Plenty of time | Green numbers | Regular countdown |
| Getting close | Yellow numbers | Medium urgency |
| Very soon | Red numbers + pulse | High urgency |
| Event live | Static message "Event is live" | Disable countdown |
| Past event | "Event ended" message | Show archive view |

#### Accessibility
- **Role:** heading or region
- **ARIA:** aria-live="polite" for countdown updates
- **Text:** Readable countdown format for screen readers

#### Code Example
```tsx
import { CountdownWidget } from "@/components/widgets/countdown-widget";

export function LandingHero() {
  return (
    <section>
      <h1>Baku Launch Event</h1>
      <CountdownWidget
        targetDate={new Date("2026-05-15")}
        size="lg"
        showCTA={true}
      />
    </section>
  );
}
```

---

### Component: LeaderboardRow
**Status:** Existing
**File:** `components/leaderboard/leaderboard-row.tsx`
**Tech:** Table row component, avatar, optional chart sparkline

#### Description
Single row in leaderboard table. Shows: rank (1-100+), user avatar, name, verification badge, AURA score, tier badge, and optional trend sparkline (mini chart of last 3 scores). Click row to view full profile.

#### Variants
| Variant | Use When |
|---------|----------|
| normal | Standard leaderboard entry |
| highlighted | Current user's row (faint highlight) |
| top-3 | Top 3 special styling (gold/silver/bronze background) |
| compact | Mobile view, fewer columns |
| with-trend | Show score trend sparkline |

#### Props
| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `rank` | number | — | Yes | Leaderboard position (1-indexed) |
| `user` | User | — | Yes | User object (name, avatar, verified) |
| `score` | number | — | Yes | Current AURA score |
| `tier` | Tier | — | Yes | Badge tier |
| `trend` | number[] \| undefined | undefined | No | Last 3 scores for sparkline |
| `isCurrentUser` | boolean | false | No | Highlight current user |
| `onClick` | () => void | — | No | Handler for row click |

#### States
| State | Visual | Behavior |
|-------|--------|----------|
| Normal | Standard row styling | Tap to view profile |
| Top 3 | Gold/Silver/Bronze background | Special highlighting |
| Current user | Subtle background highlight | Click to navigate to own profile |
| Hover | Lift/shadow effect | Ready for interaction |

#### Accessibility
- **Role:** row
- **ARIA:** aria-label="Rank 5: [Name] - 87 AURA score"
- **Keyboard:** Tab through rows, Enter to navigate

#### Code Example
```tsx
import { LeaderboardRow } from "@/components/leaderboard/leaderboard-row";

export function Leaderboard({ users, currentUserId }) {
  return (
    <table>
      <tbody>
        {users.map((user, index) => (
          <LeaderboardRow
            key={user.id}
            rank={index + 1}
            user={user}
            score={user.auraScore}
            tier={getTier(user.auraScore)}
            isCurrentUser={user.id === currentUserId}
            onClick={() => navigateTo(`/profiles/${user.id}`)}
          />
        ))}
      </tbody>
    </table>
  );
}
```

---

## Component Status Summary

| Component | Status | Priority | Notes |
|-----------|--------|----------|-------|
| AppSidebar | Existing | High | Desktop nav — foundation |
| BottomNavV2 | Existing | High | Mobile nav — core experience |
| TopBarV2 | Existing | High | Mobile header — essential |
| BadgeTierChip | Existing | High | Badge display — everywhere |
| CompetencyBar | Existing | High | Score visualization — dashboard |
| RadarChart | Existing | High | 8-axis viz — profile page |
| ScoreDisplay | Existing | High | Results reveal — key moment |
| SkillDNA | Planned | Medium | Advanced viz — post-launch |
| QuestionCardV2 | Existing | High | Assessment UX — core flow |
| CompetencyCard | Existing | High | Dashboard cards — dashboard |
| AssessmentResults | Existing | High | Results page — goal moment |
| EventCard | Existing | Medium | Event listings — discovery |
| EventRegistrationBadge | Existing | Medium | Registration status — event pages |
| ShareButtons | Existing | High | Sharing UX — viral loop |
| AURACardPreview | Existing | High | Share image — social |
| QRCodeBadge | Existing | Medium | QR linking — physical materials |
| FloatingOrbs | Existing | Medium | Landing decoration — hero |
| LanguageSwitcher | Existing | Medium | i18n toggle — header |
| NotificationDropdown | Existing | Medium | Notifications — header |
| OnboardingStep | Existing | High | Signup flow — conversion |
| PageSkeleton | Existing | Medium | Loading — UX polish |
| Toast | Existing | High | Feedback — interactions |
| EmptyState | Existing | High | Empty screens — UX |
| VerificationBadge | Existing | Medium | Verification indicator — trust |
| ProfileHeader | Existing | High | Profile page — identity |
| AURAJourneyTimeline | Planned | Low | Historical viz — engagement |
| CountdownWidget | Existing | Medium | Launch event timer — urgency |
| LeaderboardRow | Existing | Medium | Leaderboard — gamification |

---

## Design Tokens Referenced

### Colors
- See [[BRAND-IDENTITY#Color System]] for oklch values
- Badge colors: Platinum, Gold, Silver, Bronze, None

### Typography
- See [[BRAND-IDENTITY#Typography]] for font families and scales

### Motion
- See [[BRAND-IDENTITY#Motion Principles]] for animation guidelines

### Icons
- Primary: Lucide icons (16/20/24px)
- Custom icons: AURA badge, competency symbols, verification shields

---

## Next Steps

1. **Generate API types:** `pnpm generate:api` after backend finalizes OpenAPI schema
2. **Set up Storybook:** Document component stories and visual regression
3. **Icon system:** Finalize custom icon set (AURA, competencies, verification)
4. **Tailwind tokens:** Migrate color/spacing to CSS variables for dynamic theming
5. **Motion library:** Create Framer Motion preset library for consistency
6. **Accessibility audit:** WCAG 2.1 AA compliance check across all components

---

**Document Version:** 1.0
**Last Updated:** 2026-03-22
**Maintained by:** Design System Team
**Related:** [[BRAND-IDENTITY]], DECISIONS.md, HANDOFF.md
