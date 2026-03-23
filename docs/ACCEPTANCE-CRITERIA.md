# Volaura — Acceptance Criteria & Pre-Launch Checklist

**Target Launch:** When product is fully ready (no specific event dependency)
**Team:** Solo founder + AI generators (v0, Vertex, Perplexity)
**Scope:** Full polished product (all 9 modules) ready for 200→1000 volunteers in month 1

---

## PART 1: Definition of Done (Global Standards)

Every feature, component, and endpoint MUST pass these criteria before merging to main.

### Code Quality Criteria

- [ ] **Typescript (Frontend)**: Strict mode, NO `any` type
  - Run: `pnpm lint:ts` — zero errors
  - Import alias: `@/` for src paths
  - File naming: kebab-case files, PascalCase components
- [ ] **Python (Backend)**: Type hints on ALL functions
  - Run: `mypy --strict app/` — zero errors
  - Snake_case everywhere
  - No `print()` — use `loguru.logger`
  - Pydantic v2 only: ConfigDict, @field_validator (NO v1 syntax)
- [ ] **SQL**: Naming snake_case, UTF-8 encoding explicit
  - Run: `sqlfluff lint supabase/migrations/` — zero errors
  - RLS enabled on ALL tables with documented policies
- [ ] **Linting**:
  - Frontend: `pnpm lint` (ESLint) — zero errors/warnings
  - Backend: `ruff check app/` — zero errors
- [ ] **No secrets in code**
  - `.env.local` in `.gitignore`
  - No API keys in commits: `git log --all --name-status | grep -i 'env\|secret\|key'` → empty
- [ ] **Imports organized**
  - External imports → relative imports → local imports
  - No circular dependencies

### Testing Criteria

- [ ] **Feature tests written (Gherkin syntax)**
  - Given/When/Then for all critical paths
  - At minimum: happy path + 2 error cases
  - Store in `docs/acceptance-tests/[module].feature`
- [ ] **Manual smoke tests documented**
  - Checklist in feature PR template
  - Test on staging before merge
- [ ] **Accessibility tested**
  - Keyboard navigation (Tab, Enter, Escape)
  - Screen reader (NVDA/JAWS): heading hierarchy, alt text, ARIA labels
  - Color contrast (WCAG AA minimum)
  - Touch targets minimum 44×44px
- [ ] **Mobile responsive tested**
  - iOS Safari, Chrome Android
  - Landscape + portrait orientations
  - Devtools viewport tests at 375px, 768px, 1024px
- [ ] **Performance budgets met**
  - LCP <2.5s, FID <100ms (or INP <200ms), CLS <0.1
  - Run: `npm run lighthouse` on staging
  - JS bundle: <300KB gzipped (initial)

### Accessibility Criteria

- [ ] **Semantic HTML**
  - Use native elements: `<button>`, `<form>`, `<label>`, `<nav>`, `<main>`
  - NO `<div onclick>` or `<span role="button">`
- [ ] **ARIA labels & roles**
  - Interactive elements have accessible names
  - `<Button aria-label="Close modal">×</Button>`
  - Modals: `role="dialog"`, `aria-modal="true"`, `aria-labelledby`
- [ ] **Focus management**
  - Visible focus indicator: min 2px outline, 2:1 contrast ratio
  - Tab order logical
  - Modals trap focus (Tab cycles within modal)
- [ ] **Color not sole means of communication**
  - "Error" state: red border + error icon + error text
  - "Required" field: asterisk + `aria-required="true"` + label
- [ ] **Images & icons**
  - `<img alt="description">` or `aria-label="description"`
  - Icon-only buttons: `<Button aria-label="Settings">⚙️</Button>`
- [ ] **Forms accessible**
  - `<label htmlFor="id">` paired with input
  - Error messages: `aria-describedby="error-message"`
  - Validation messages linked to fields
- [ ] **Motion respects prefers-reduced-motion**
  - Framer Motion: check `useReducedMotion()`
  - All animations conditionally render
- [ ] **Contrast ratio**
  - Normal text: 4.5:1
  - Large text (18px+): 3:1
  - UI components & borders: 3:1
  - Check: WebAIM Contrast Checker

### i18n Criteria (AZ Primary, EN Secondary)

- [ ] **Zero hardcoded strings**
  - All user-facing text uses `t("namespace.key")`
  - Run: `pnpm i18next:extract` → check for missing keys
  - No `[missing]` warnings in logs
- [ ] **Azerbaijani characters render**
  - ə, ğ, ı, ö, ü, ş, ç display correctly
  - Check: `<meta charset="utf-8" />`
  - Font: Inter supports Extended Latin
  - Test: type in each character, verify rendering
- [ ] **Text expansion accounted for**
  - AZ text ~20-30% longer than EN
  - UI layouts tested with max-length AZ strings
  - No truncation at design boundaries
- [ ] **Date & number formatting**
  - AZ: `dd.MM.yyyy` (e.g., "22.03.2026"), `1.234,56`
  - EN: `MM/dd/yyyy` (e.g., "03/22/2026"), `1,234.56`
  - Use `intl.DateTimeFormat` or `Intl.NumberFormat`
- [ ] **Namespace structure complete**
  - `common.json`: nav, buttons, generic
  - `auth.json`: login, signup, verification
  - `assessment.json`: questions, progress
  - `results.json`: score reveal, badges
  - `profile.json`: profile, edit, public
  - `events.json`: listing, detail, registration
  - `errors.json`: all error messages
  - Each namespace in `/locales/{az,en}/`
- [ ] **Email templates localized**
  - Welcome, magic link, score ready, invites
  - Bilingual (AZ primary + EN fallback)
  - Test in Resend preview

### Performance Criteria

- [ ] **Bundle size**
  - Initial JS: <300KB gzipped
  - Run: `npm run build && npm run analyze`
  - Identify & justify any >100KB dependencies
- [ ] **Image optimization**
  - All `<img>` → `<Image>` from `next/image`
  - Alt text on every image
  - WebP served automatically
  - Lazy loading enabled
  - Placeholder blur/skeleton on slow networks
- [ ] **API response time**
  - Cold start: <3s
  - Cached responses: <200ms
  - Heavy operations (LLM eval): async, 202 response
- [ ] **Database queries**
  - Queries logged via loguru
  - No N+1 queries
  - Complex queries use Supabase RPC functions
  - Run: check Railway logs for slow queries
- [ ] **ISR revalidation configured**
  - Landing page: `revalidate: 3600` (1 hour)
  - Public profiles: `revalidate: 60` (1 minute)
  - Leaderboard: `revalidate: 300` (5 minutes)
- [ ] **Caching strategy**
  - LLM evaluations cached in session at submit time
  - API responses cached per TanStack Query config
  - Service worker active for offline PWA
- [ ] **Core Web Vitals** (on staging)
  - LCP: <2.5s
  - FID: <100ms (or INP <200ms)
  - CLS: <0.1

### Security Criteria

- [ ] **RLS policies verified**
  - Every table has RLS enabled
  - Users can ONLY read/update/delete own records
  - Test: Create user A & B, verify cross-access blocked
  - Public tables (events, profiles) have explicit SELECT policies
- [ ] **Authentication**
  - JWT token in Authorization header: `Bearer <token>`
  - Token validation on every protected route
  - Token expiration: 1 hour default
  - Magic link & Google OAuth working
- [ ] **Input validation**
  - Zod schemas on all form inputs
  - Pydantic models on all API request bodies
  - Sanitized before LLM: no prompt injection
  - Max length checks (textarea: 1400 chars)
- [ ] **Rate limiting**
  - Auth endpoints: 5 requests/minute per IP
  - Assessment start: 5/hour per user
  - Assessment answers: 60/hour per user
  - LLM eval: 30/hour per user
  - Semantic search: 30/minute per org
  - Leaderboard: 60/minute
- [ ] **CORS configured**
  - Only allow frontend origin(s)
  - Credentials included
  - Preflight requests (OPTIONS) handled
- [ ] **CSP headers**
  - `Content-Security-Policy` set in next.config.js
  - Allows Google fonts, Gemini API, Sentry
  - No `unsafe-inline` scripts
- [ ] **HTTPS enforced**
  - HTTP → HTTPS redirect
  - Vercel auto-redirect enabled
  - Test: `curl -I http://volaura.com` → 308
- [ ] **Secrets management**
  - No secrets in `.env.example`
  - Production secrets in Vercel/Railway dashboards only
  - Rotate old API keys
- [ ] **Error handling**
  - Errors never expose stack traces to client
  - Structured error format: `{ detail: { code, message } }`
  - Sensitive info logged server-side only (loguru)
  - User-facing errors localized via errors.json

### Design Criteria

- [ ] **Design system implemented**
  - Colors: oklch values in Tailwind CSS 4 `@theme {}`
  - Typography: Inter (body), JetBrains Mono (numbers)
  - Spacing: 4px base unit
  - Border radius: 12px default, 16px cards, 999px pills
  - Touch targets: 44×44px minimum
- [ ] **Component library (shadcn/ui)**
  - Base components used (Button, Card, Input, Modal, etc.)
  - Composed in `components/features/`
  - Customized via `cn()` utility
  - Dark mode support
- [ ] **Animations**
  - Framer Motion with spring presets
  - `prefers-reduced-motion` respected
  - Meaningful animations (not gratuitous)
  - Fast: <400ms duration
- [ ] **Responsive design**
  - Mobile-first approach
  - Breakpoints: 640 / 768 / 1024 / 1280 / 1536px
  - Tested on real devices (not just DevTools)
  - Landscape/portrait tested
- [ ] **Dark mode**
  - `[data-theme="dark"]` CSS support
  - Colors override in dark class
  - User preference persisted (localStorage)
  - Toggle in settings

---

## PART 2: Acceptance Criteria Per Module (Given/When/Then)

### MODULE 1: Project Setup & Layout Shell

**Goal:** Git repo, monorepo structure, layouts, landing page, navigation.

**AC-1.1: Repository Initialized**
```gherkin
Given a GitHub repo named volaura
When I clone the repo
Then I see folders: apps/web, apps/api, supabase, packages, docs
And package.json has workspaces: ["apps/*", "packages/*"]
And pnpm install succeeds
And pnpm run build succeeds
```

**AC-1.2: Frontend Layout Shell**
```gherkin
Given the Next.js 14 app is created with App Router
When I navigate to /az or /en
Then I see the layout: Header (logo + nav + language toggle) + Main content + Footer
And Header displays "VOLAURA" logo on left
And Language toggle shows AZ ↔ EN in top-right
And Footer has links: About, Contact, Privacy, Terms
And all text is localized via i18next
```

**AC-1.3: Landing Page**
```gherkin
Given a user visits volaura.com
When the page loads
Then I see Hero section: headline + subheadline + CTA buttons
And CTA buttons: "Start Assessment" (primary) and "Learn More" (secondary)
And "Start Assessment" links to /auth/login
And page has 3+ sections: How it works, Why Volaura, Testimonials (placeholder)
And each section is fully responsive (tested at 375px, 1024px, 1536px)
And Lighthouse score: >90 overall, >95 Accessibility
```

**AC-1.4: Navigation & Routing**
```gherkin
Given the app is running
When I click on nav items
Then each link navigates to the correct locale-prefixed route
And /az/* is Azerbaijani, /en/* is English
And generateStaticParams() pre-renders all locales
And params are typed as Promise<{locale: string}> (Next.js 14.2+)
And useRouter navigation preserves locale
```

**AC-1.5: Environment Setup**
```gherkin
Given a developer runs setup
When they create .env.local with NEXT_PUBLIC_API_URL, NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY
Then pnpm dev starts frontend on http://localhost:3000
And pnpm run build succeeds without warnings
And .env.local is in .gitignore
```

---

### MODULE 2: Authentication Flow

**Goal:** Magic link, Google OAuth, JWT, session management.

**AC-2.1: Magic Link Login**
```gherkin
Given I navigate to /auth/login
When I enter my email and click "Send Magic Link"
Then Supabase sends email with magic link
And link is valid for 24 hours
And clicking link signs me in and redirects to /dashboard
And I see: "Welcome back, [name]!"
And session token stored in browser (HTTP-only cookie optional)
```

**AC-2.2: Google OAuth**
```gherkin
Given I click "Continue with Google" on /auth/login
When I authenticate with Google
Then Supabase OAuth flow completes
And I'm signed in, redirected to /dashboard
And my profile is created: name from Google, email verified
And locale defaults to browser language (az or en)
```

**AC-2.3: Profile Creation on Signup**
```gherkin
Given a new user signs in via magic link or Google
When authentication succeeds
Then a row is created in profiles table:
  - id = auth.users.id
  - email, full_name auto-populated
  - username auto-generated (first_last_timestamp)
  - locale = detected or default az
  - is_public = true
  - avatar_url = null
  - role = 'volunteer'
And user can edit profile immediately after signup
```

**AC-2.4: Token Validation**
```gherkin
Given a user is logged in
When they make an API request to /api/v1/assessments/start
Then the Authorization header has "Bearer <token>"
And backend validates JWT via get_current_user_id Depends()
And invalid token returns 401: { detail: { code: "UNAUTHORIZED" } }
And expired token returns 401
```

**AC-2.5: Logout**
```gherkin
Given I'm logged in
When I click logout (in user menu)
Then my session is cleared
And I'm redirected to /auth/login
And accessing protected routes redirects to /auth/login
```

**AC-2.6: Magic Link Email i18n**
```gherkin
Given a user's locale is 'az'
When they request a magic link
Then the email is in Azerbaijani
And link works correctly
When a user's locale is 'en'
Then the email is in English
```

---

### MODULE 3: Assessment Engine

**Goal:** 8 competencies, 3 question types, IRT/CAT algorithm, AURA calculation.

**AC-3.1: Assessment Hub**
```gherkin
Given I'm logged in and navigate to /assessment
When the page loads
Then I see 8 competency cards:
  - communication, reliability, english_proficiency, leadership, event_performance, tech_literacy, adaptability, empathy_safeguarding
And each card shows status: "Not Started", "In Progress", "Completed"
And completed cards show score (e.g., "78/100")
And I can tap any card to start/resume
```

**AC-3.2: Question Flow (BARS Type)**
```gherkin
Given I tap "Communication" and it hasn't been started
When the first question appears
Then I see:
  - Competency name: "Communication"
  - Progress: "1/3" (or more)
  - Question text (localized AZ/EN)
  - Question type indicator: "BARS Scale"
  - 7 tappable circles with behavioral anchors below
And I tap circle 5
Then it highlights (primary color, spring animation)
And I see: "Score: 71" (calculated as ((5-1)/6)*100)
And "Next Question" appears
```

**AC-3.3: Question Flow (MCQ Type)**
```gherkin
Given a MCQ question appears
When I see 4 option cards
Then each card is tappable
And each option has hidden score_weight (0.0-1.0)
When I select an option
Then it highlights with primary border + checkmark
And score calculated: score_weight * 100
And "Next Question" appears
```

**AC-3.4: Question Flow (Open Text Type)**
```gherkin
Given an open text question appears
When I see a textarea with word limit
Then word counter shows "0/300 words"
And "AI will evaluate this answer" badge visible
And I type my answer
Then counter updates in real-time
When I submit
Then response: 202 { evaluation_status: "pending", next_question: {...} }
And frontend shows: "AI is evaluating... Next question"
And polls GET /assessments/{id}/responses/{resp_id}/status every 2s
Until status: "completed" with score
```

**AC-3.5: Adaptive Question Selection**
```gherkin
Given I'm answering questions for Communication
When my score on Q1 is 85 (>70)
Then next question difficulty increases (1→2)
When my score is 35 (<40)
Then next question difficulty decreases (2→1)
And difficulty stays within 1-3 range
And questions are randomly selected from active pool per competency
```

**AC-3.6: Assessment Completion**
```gherkin
Given I've answered all questions for a competency (3-5 total)
When I submit the final answer
Then POST /assessments/{id}/complete called
And response: { competency_score: 78, aura_score: 72, badge_tier: "silver", badge_changed: true }
And database updates: assessments.status = "completed", assessments.final_score = 78
And I'm shown results screen with confetti
And I can proceed to next competency or exit
```

**AC-3.7: AURA Score Calculation**
```gherkin
Given all 8 competency assessments are completed
When aura_score is calculated
Then formula applied:
  sum(competency_score * weight * verification_multiplier) * reliability_factor
And weights: communication 0.20, reliability 0.15, english_proficiency 0.15, leadership 0.15, event_performance 0.10, tech_literacy 0.10, adaptability 0.10, empathy_safeguarding 0.05
And verification_multiplier: self_assessed 1.0, org_attested 1.15, peer_verified 1.25
And reliability_factor: 1.0 - (0.15 * std_dev), clamped [0.85, 1.0]
And final_score clamped [0, 100]
And badge_tier assigned: >=90 Platinum, >=75 Gold, >=60 Silver, >=40 Bronze, <40 None
```

**AC-3.8: Resume Abandoned Assessment**
```gherkin
Given I started Communication assessment but didn't finish (status='in_progress')
When I return to Assessment Hub after 1 day
Then Communication card shows: "In Progress (2/5)"
And I tap it
Then it resumes from where I left off
And previous answers are preserved
And I can complete remaining questions
```

**AC-3.9: Offline Mode**
```gherkin
Given I'm on venue WiFi with spotty connection
When I disable network in DevTools
And I answer questions
Then answers are queued locally (service worker cache)
And submit button shows: "Will sync when online"
When I re-enable network
Then sync completes automatically
And score appears on profile
```

**AC-3.10: LLM Evaluation Fallback**
```gherkin
Given Gemini API fails on open text evaluation
When response timeout or error occurs
Then heuristic applied: score = min(80, max(20, word_count/max_words*60))
And response marked: status='fallback_scored'
And error logged to Sentry
And queued for retry (pg_cron, max 3 retries, 15min interval)
```

---

### MODULE 4: Dashboard & AURA Score

**Goal:** AURA display, radar chart, quick actions, leaderboard snippet.

**AC-4.1: Dashboard Page**
```gherkin
Given I'm logged in and navigate to /dashboard
When the page loads
Then I see:
  - Greeting: "Salam, [name]!" (localized AZ/EN)
  - AURA Score card: large number (72) + badge (Silver) + trend arrow
  - Radar chart (8 axes for 8 competencies)
  - Quick actions: "Take Assessment", "Find Events", "Share Profile"
  - Upcoming events (horizontal scroll, 3-5 cards)
  - Recent notifications (3 most recent)
  - Leaderboard snippet: "You are ranked #47 out of 200"
And all text is localized
And images optimized (WebP, lazy loaded)
```

**AC-4.2: AURA Score Page**
```gherkin
Given I click on the AURA Score card
When /aura page loads
Then I see:
  - Animated counter: 0 → final score (JetBrains Mono, 72px)
  - Badge: "Silver" with tier color
  - Full radar chart (interactive, 8 colored axes)
  - Competency breakdown: 8 rows with name + score bar + verification icon
  - Verification levels: shield icons (gray=self, blue=org, gold=peer)
  - Score history timeline (line chart, Recharts)
  - "Improve Your Score" section with links to reassess
  - Share section: 3 format previews + Copy + QR
```

**AC-4.3: Radar Chart Interaction**
```gherkin
Given the radar chart is displayed
When I tap on an axis label (e.g., "Communication")
Then a detail view opens:
  - Current score: 85
  - Verification level
  - Trend (up/down arrow with % change)
  - Recommended actions to improve
```

**AC-4.4: Score History**
```gherkin
Given a user has completed assessments on multiple dates
When I view the AURA Score page
Then I see a line chart with:
  - X-axis: dates of assessment completions
  - Y-axis: AURA score (0-100)
  - Line animated on page load
  - Legend: "Your AURA Journey"
  - Tap data point to see: date, score, badge tier at that time
```

**AC-4.5: Share Formats**
```gherkin
Given I click "Share Your Score" on AURA page
When share options appear
Then I can generate:
  - LinkedIn card (1200×627px) — shows AURA, badge, radar
  - Instagram Story (1080×1920px) — vertical format
  - Square (1080×1080px) — tile format
And each format has social media icon + copy to clipboard
And image includes volaura.com/u/[username] QR code
```

---

### MODULE 5: Profile & Public Sharing

**Goal:** Profile pages, OG images, share buttons, impact metrics.

**AC-5.1: Authenticated Profile Page**
```gherkin
Given I navigate to /profile
When the page loads
Then I see:
  - Avatar (128px circle, uploadable)
  - Name, username, city, bio
  - AURA badge (animated counter)
  - Competency radar chart (interactive)
  - Skills/expertise tags
  - Languages spoken
  - Verification status indicators (3 levels)
  - Impact metrics: "120 hours · 8 events · 3 organizations"
  - Event timeline (visual with org logos + "Verified" badge)
  - AURA growth graph (line chart)
  - Organization endorsements (logos + verified competencies)
  - "Edit Profile" button
  - "Share Profile" button
```

**AC-5.2: Edit Profile**
```gherkin
Given I click "Edit Profile"
When modal opens
Then I can update:
  - Avatar (upload image, crop to 128px)
  - Full name
  - Bio (max 160 chars)
  - City
  - Expertise (add/remove tags)
  - Languages (checkboxes for known languages)
  - is_public (toggle)
When I save
Then data persists to profiles table
And page re-renders with new data
And OG image regenerates
```

**AC-5.3: Public Profile (SSR)**
```gherkin
Given a volunteer profile is public (is_public=true)
When I visit /u/[username]
Then page is server-rendered (SSR)
And shows same layout as authenticated profile but read-only
And "Join Volaura" CTA visible for non-logged-in users
And QR code for printing on physical badges
```

**AC-5.4: OG Image Generation**
```gherkin
Given a user navigates to /u/[username]
When the page requests OG image
Then GET /api/og/[username] called
And Satori generates image with:
  - User's name
  - AURA score
  - Badge tier (with color)
  - Mini radar chart
  - volaura.com watermark
And image returned as PNG <200KB
And preview works in Slack, Twitter, LinkedIn
```

**AC-5.5: Share Buttons**
```gherkin
Given I click "Share Profile"
When share dialog opens
Then I see:
  - LinkedIn button: redirects to LinkedIn with pre-filled text + profile URL
  - Twitter button: opens intent with text + score emoji
  - WhatsApp button: opens chat with pre-filled message + link
  - Copy Link button: copies /u/[username] to clipboard, shows toast "Copied!"
  - QR code button: downloads QR code PNG
```

**AC-5.6: Volunteer Impact Timeline**
```gherkin
Given a volunteer has attended 3 events
When I view their profile
Then I see "Event Timeline" section with:
  - Org logo + event title + date + "Verified ✓" if org-attested
  - Each event card clickable → opens event details
  - Live counter: "42 volunteers confirmed" — tap to expand avatars
  - Chronological order (newest first)
```

---

### MODULE 6: Events & Organizations

**Goal:** Event listing, filtering, registration, org portal, attestation workflow.

**AC-6.1: Events List Page**
```gherkin
Given I navigate to /events
When the page loads
Then I see:
  - Filter bar: date range, location, min AURA, competency, status
  - Event cards: org logo + title + date + location + live volunteer counter + min AURA badge
  - Sort options: date (default), popularity, volunteer count
  - "My Events" tab (registered + attended)
  - "Past Events" section with completed events + confirmed volunteer counts
And all text localized (AZ/EN)
```

**AC-6.2: Event Detail Page**
```gherkin
Given I tap an event card
When event detail page loads
Then I see:
  - Hero: title + org logo + date + location (map preview)
  - Description (bilingual AZ/EN)
  - Requirements: min AURA score badge, required competencies
  - Live capacity bar: "32/50 registered" (updates via Realtime)
  - "Register" CTA (disabled if AURA too low, with explanation)
  - Registered volunteers: scrollable avatars + badges + AURA scores
  - For past events: "I participated" button
```

**AC-6.3: Event Registration**
```gherkin
Given I click "Register" on an upcoming event
When the registration form appears
Then I can enter:
  - Confirm my AURA score meets requirement
  - Select availability (if event has multiple dates)
When I submit
Then event_registrations row created: event_id, user_id, status='registered'
And confirmation email sent (bilingual, Resend)
And volunteer counter increments (live via Realtime)
And user added to "Registered Volunteers" list
```

**AC-6.4: Self-Attestation (Attended Event)**
```gherkin
Given an event is completed (status='completed')
When I view the event detail
Then "I participated in this event" button visible
And I can click to claim participation
Then pending_attestation created: event_id, user_id, status='pending_org_confirmation'
And org receives notification: "User X claims they attended [Event]"
And org can confirm/deny in attestation queue
```

**AC-6.5: Event Real-Time Updates**
```gherkin
Given I'm viewing event detail page
When another user registers for the same event
Then volunteer counter increments in real-time via Supabase Realtime
And "Registered Volunteers" list updates
And no page refresh needed
```

**AC-6.6: Organization Portal (Create Event)**
```gherkin
Given I'm an org admin
When I navigate to /org/dashboard/events/new
Then I can:
  - Enter event title (AZ + EN)
  - Upload org logo
  - Set date/time, location
  - Set min AURA requirement
  - Select required competencies (checkboxes)
  - Set capacity
When I submit
Then events row created: org_id, title_az, title_en, status='draft'
And I can publish or save as draft
```

**AC-6.7: Volunteer Search (Semantic)**
```gherkin
Given I'm an org admin
When I navigate to /org/dashboard/volunteers/search
And I enter: "Reliable English-speaking event coordinator"
Then backend:
  1. Generates embedding via Gemini
  2. Calls match_volunteers RPC with query_embedding
  3. Returns matches with similarity score
Then I see: list of volunteers with 80%+ match score
  - Name, avatar, AURA score
  - Top competencies
  - Similarity: "89% match"
And I can filter by min AURA, competency, location
```

**AC-6.8: Post-Event Attestation Workflow**
```gherkin
Given an event is completed
When org admin navigates to /org/dashboard/attestations
Then they see: registered volunteers list
And for each volunteer: rating (1-5 stars) + checkboxes per competency
When org checks: "Communication verified" + "Reliability verified"
And submits
Then:
  - volunteer's competency_scores updated: verification_level='org_attested'
  - AURA recalculated with 1.15x multiplier for verified competencies
  - Volunteer gets notification: "Organization X verified your Communication and Reliability!"
```

**AC-6.9: Organization Creation**
```gherkin
Given a user navigates to /org/register
When they fill form:
  - Organization name
  - Logo upload
  - Website, contact email
  - Verification checkbox (TOS)
And submit
Then organizations row created: name, slug (auto-generated), logo_url, plan='starter'
And user added to org_members: role='owner'
And org dashboard accessible at /org/[slug]
```

---

### MODULE 7: Backend API

**Goal:** FastAPI endpoints, OpenAPI generation, type safety, error handling.

**AC-7.1: Health Endpoint**
```gherkin
Given the API is running
When I call GET /api/v1/health
Then response: { "status": "ok" }
And HTTP 200
And called without Authorization header
```

**AC-7.2: Assessment Start Endpoint**
```gherkin
Given I'm authenticated
When I call POST /api/v1/assessments/start with { competency: "communication" }
Then response: { data: { assessment_id: "uuid", first_question: {...} } }
And assessments row created with status='in_progress'
And question includes: text_az, text_en, type, options (if MCQ), bars_anchors (if BARS)
```

**AC-7.3: Submit Answer Endpoint**
```gherkin
Given I'm answering a BARS question
When I call POST /api/v1/assessments/{id}/answers with { question_id: "uuid", response: { selected: 5 }, time_spent_seconds: 45 }
Then response: { data: { score: 71.4, next_question: {...} | null, is_complete: false } }
And assessment_responses row created with score calculated
When answering open text question
Then response (202): { evaluation_status: "pending", response_id: "uuid", next_question: {...} }
And response stored with llm_score=NULL
```

**AC-7.4: Poll LLM Evaluation Status**
```gherkin
Given an open text answer was submitted (response_id known)
When I call GET /api/v1/assessments/{id}/responses/{response_id}/status
And evaluation still pending
Then response: { status: "pending" }
When evaluation complete
Then response: { status: "completed", score: 78.5, feedback: "..." }
```

**AC-7.5: Complete Assessment Endpoint**
```gherkin
Given I've answered all questions for a competency
When I call POST /api/v1/assessments/{id}/complete
Then response: { competency_score: 78, aura_score: 72, badge_tier: "silver", badge_changed: true }
And assessments.status='completed', assessments.final_score=78
And aura_scores recalculated
And aura_scores.is_current=true updated
```

**AC-7.6: Get AURA Score Endpoint**
```gherkin
Given I'm authenticated
When I call GET /api/v1/scores/me
Then response includes:
  - composite_score: 72
  - tier: "silver"
  - percentile: 68.5
  - reliability_factor: 0.95
  - competencies array with: competency, score, weight, verification_level
  - events_attended: 3
  - last_assessed: "2026-03-20T..."
```

**AC-7.7: Leaderboard Endpoint**
```gherkin
Given I call GET /api/v1/scores/leaderboard?limit=50&offset=0
When no competency filter
Then response: list of top 50 volunteers sorted by composite_score DESC
And each entry: rank, username, avatar_url, score, tier
When I add ?competency=communication
Then response filtered to communication competency scores
And sorted by communication score DESC
```

**AC-7.8: API Response Envelope (ALL endpoints)**
```gherkin
Given ANY API endpoint is called
When successful
Then response shape: { data: {...}, meta: { timestamp, request_id, version, pagination: {...} } }
When error (e.g., 404)
Then response shape: { detail: { code: "PROFILE_NOT_FOUND", message: "Profile not found" } }
```

**AC-7.9: Rate Limiting**
```gherkin
Given rate limits configured in app/main.py
When I call /api/v1/auth/magic-link 6 times in 1 minute (5/min limit)
Then 6th request returns: 429 { detail: { code: "RATE_LIMIT_EXCEEDED" } }
When I call /api/v1/assessments/start 6 times in 1 hour (5/hour limit)
Then 6th request returns: 429
```

**AC-7.10: CORS Configuration**
```gherkin
Given frontend origin: https://volaura.com
When frontend calls API
Then CORS headers allow:
  - Origin: https://volaura.com
  - Methods: GET, POST, PATCH, DELETE
  - Headers: Authorization, Content-Type
  - Credentials: true
When external origin tries to call API
Then CORS blocks the request
```

**AC-7.11: OpenAPI Generation**
```gherkin
Given FastAPI app is running
When I call GET /openapi.json
Then response includes all endpoints with:
  - request/response schemas (Pydantic models)
  - security definitions (Bearer token)
  - tags and descriptions
When I run `pnpm generate:api`
Then @hey-api/openapi-ts generates:
  - TypeScript types in lib/api/generated
  - TanStack Query hooks
  - Zod schemas
```

---

### MODULE 8: Growth & Analytics

**Goal:** Referrals, email lifecycle, analytics events, OG tags, structured data.

**AC-8.1: Referral Invite**
```gherkin
Given I navigate to /referrals
When I click "Invite Friend" and enter email
Then POST /api/v1/referrals/invite called with { email: "friend@example.com" }
And response: { referral_id: "uuid", invite_link: "https://volaura.com/join?ref=CODE" }
And referrals row created: referrer_id, referral_code, converted_at=NULL
And email sent to friend with link + personalized message
```

**AC-8.2: Referral Conversion**
```gherkin
Given a friend clicks my referral link: /join?ref=CODE
When they sign up
Then referrals.referee_id updated to their user_id
And referrals.converted_at set
And referrer gets +5 bonus on lowest competency (max 5 invites = +25)
And referee gets +3 bonus on first assessment completion
And thank you email sent: "Your friend {name} joined! +5 bonus applied"
```

**AC-8.3: Referral Stats Page**
```gherkin
Given I navigate to /referrals
When page loads
Then I see:
  - My referral code: "ABC123"
  - Total invited: 5
  - Total converted: 2
  - Bonus earned: 10
  - List of referrals with status: pending, converted, expired
```

**AC-8.4: Email Welcome**
```gherkin
Given a new user signs up
When signup completes
Then email sent within 1 minute:
  - Subject: "Salam! VOLAURA-ya xoş gəldiniz" (AZ) or "Welcome to Volaura!" (EN)
  - Body: "Discover your volunteer potential. Start your assessment."
  - CTA button: "Start Assessment" → links to /assessment
  - Bilingual: AZ primary + EN fallback based on user locale
```

**AC-8.5: Email Score Ready**
```gherkin
Given I complete all 8 assessments
When AURA score calculated
Then email sent within 5 minutes:
  - Subject: "🏆 Your AURA Score is Ready!"
  - Body: Shows score (72), badge tier (Silver), top competency
  - Includes radar chart preview
  - CTA: "View Your Profile" + "Share Your Badge"
  - Bilingual
```

**AC-8.6: Email Nudge (7 Days)**
```gherkin
Given a user signed up 7 days ago and hasn't logged in
When pg_cron job runs
Then email sent:
  - Subject: "X volunteers joined since you left" (with social proof)
  - Body: Highlights new features, upcoming events
  - CTA: "Continue Assessment"
```

**AC-8.7: Email Winback (30 Days)**
```gherkin
Given a user hasn't logged in for 30 days
When pg_cron job runs
Then email sent:
  - Subject: "Your AURA Score is Waiting"
  - Body: Highlights improvements, new events
  - CTA: "Come Back to Volaura"
```

**AC-8.8: Email Rendering**
```gherkin
Given emails are generated
When tested in Litmus or similar
Then rendered correctly in:
  - Gmail (desktop + mobile)
  - Outlook
  - Apple Mail
  - Mobile clients (iOS Mail, Gmail app)
And images load, buttons clickable, text readable
```

**AC-8.9: Analytics Events (GA4 / Mixpanel)**
```gherkin
Given tracking is configured
When user_signup event fires
Then event logged: { name: "user_signup", source: "organic|referral|wuf13", locale: "az|en" }
When assessment_completed event fires
Then event logged: { name: "assessment_completed", competency: "communication", score: 78, time_seconds: 1200 }
When score_shared event fires
Then event logged: { name: "score_shared", platform: "linkedin|instagram|copy|qr" }
```

**AC-8.10: UTM Parameters on Share Links**
```gherkin
Given a user shares their profile
When they copy LinkedIn link
Then link includes: ?utm_source=linkedin&utm_medium=social&utm_campaign=aura_badge
When they get referred
Then join link includes: ?ref=CODE&utm_source=referral&utm_medium=email
```

**AC-8.11: OG Tags on Public Profile**
```gherkin
Given a public profile: /u/[username]
When shared on social media
Then OG meta tags include:
  - og:title: "{name} — {tier} Volunteer (AURA {score})"
  - og:description: "Verified volunteer on Volaura. {top_competency} specialist."
  - og:image: "https://volaura.com/api/og/{username}"
  - og:url: "https://volaura.com/u/{username}"
  - twitter:card: "summary_large_image"
```

**AC-8.12: JSON-LD Structured Data**
```gherkin
Given a public profile
When crawled by search engines
Then page includes:
  {
    "@context": "https://schema.org",
    "@type": "Person",
    "name": "{full_name}",
    "description": "{bio}",
    "image": "{avatar_url}",
    "url": "https://volaura.com/u/{username}"
  }
```

---

### MODULE 9: Gamification, AI Coaching & Liveness

**Goal:** Streaks, leagues, AI coach, activity feed, impact metrics.

**AC-9.1: Monthly Volunteer Streak**
```gherkin
Given I attend an event in January
When February event attended
Then current_streak increments: 2
And display: "🔥 2-month streak" on profile + dashboard
When I skip March events
Then current_streak resets: 0
And notification: "Your 2-month streak ended. Start a new one!"
And longest_streak preserved (historical record)
```

**AC-9.2: Leagues**
```gherkin
Given I'm a volunteer in Baku
When monthly league created (ranks ~30 users by AURA activity)
Then I see: "You are in Contender League, rank #12"
And top 5 promote to next tier, bottom 5 demote
When month ends
Then league resets, new rankings computed
And leaderboard shows: tier, rank, xp_earned this month
```

**AC-9.3: Competency Specialist Badge**
```gherkin
Given my Communication score reaches 85
When AURA recalculated
Then "Communication Specialist 🎯" badge earned
And displays on profile
And visible in org search filters: "Filter by specialists"
```

**AC-9.4: AURA Coach Appearance**
```gherkin
Given I navigate to /dashboard
When page loads
Then floating action button appears (bottom-right, above BottomNav on mobile)
And button is pulsing (new insight available)
When I tap it
Then coach expands: 1-3 contextual tips with icons + text + action buttons
```

**AC-9.5: AURA Coach Messages**
```gherkin
Given I call GET /api/v1/coach/message?context=dashboard
When endpoint returns
Then response includes messages like:
  - skill_gap: "Your Communication is 62. To reach Gold, improve to 70+."
  - event_match: "3 events this week match your profile at 80%+. Register now!"
  - growth_path: "You're 8 points from Gold. Focus on English (+5) and Reliability (+3)."
  - nudge: "You haven't volunteered in 30 days. 12 new events posted near you."
  - celebration: "Organization X rated you 5/5! Request a Leadership attestation?"
And each message has action_url (e.g., /assessment, /events/uuid)
And rate limit: 10/hour per user
```

**AC-9.6: Coach Data Generation**
```gherkin
Given a user's profile + event data + score history available
When coach/message endpoint called
Then backend:
  1. Fetches user profile, competency scores, upcoming events, past ratings
  2. Queries Gemini with context prompt
  3. Parses response for message type + text_az + text_en
  4. Caches for 1 hour
Then responses cached to avoid redundant LLM calls
```

**AC-9.7: Live Stats Widget**
```gherkin
Given landing page or dashboard displayed
When live-stats.tsx rendered
Then displays:
  - "847 verified volunteers"
  - "+23 new today"
  - "15 organizations"
  - "42 events completed"
And counters animate when value changes (Framer Motion spring)
And data updates via polling every 60s or Realtime subscription
```

**AC-9.8: Activity Feed (Realtime)**
```gherkin
Given I'm on /dashboard
When activity-feed component loads
Then displays recent activities via Supabase Realtime:
  - "Leyla M. just earned Platinum!"
  - "COP29 — 1 new volunteer confirmed"
  - "+3 volunteers assessed today in Baku"
  - "Rashad K. became a Leadership Specialist"
And new activities appear in real-time (no refresh needed)
And activities are public (is_public=true) from activity_log table
```

**AC-9.9: Activity Log Table**
```gherkin
Given user achieves milestone (badge earned, specialist, etc.)
When milestone event fires
Then activity_log row created:
  - type: badge_earned | assessment_completed | event_confirmed | attestation_received | specialist_earned | streak_milestone
  - actor_id: user ID
  - metadata: { badge: "platinum", event_name: "COP29", score: 92 }
  - is_public: true
```

**AC-9.10: Impact Metrics on Profile**
```gherkin
Given I navigate to volunteer profile
When page loads
Then I see impact metrics computed as:
  - total_volunteer_hours: SUM of event durations (status='attended')
  - events_attended: COUNT of event_registrations (status='attended')
  - organizations_worked_with: COUNT DISTINCT org_id from attended events
  - total_attestations: COUNT of org attestations received
And display format: "120 hours · 8 events · 3 organizations"
```

---

## PART 3: Dependency Graph

### Critical Path (Must Complete Before Launch)

```
1. DB Schema + RLS (Module 1)
   ↓
2. Auth (Magic Link + Google OAuth) (Module 2)
   ↓
3. Assessment Engine + AURA Calculation (Module 3)
   ↓
4. Dashboard + Results Display (Module 4)
   ↓
5. Profile + Public Sharing (Module 5)
   ├─ (Parallel) Events & Orgs (Module 6)
   ├─ (Parallel) Backend API (Module 7)
   ├─ (Parallel) Growth & Analytics (Module 8)
   └─ (Parallel) Gamification & Coach (Module 9)
   ↓
6. Full Integration Testing + Staging Deployment
   ↓
7. Pre-Launch Checklist (DEPLOY-CHECKLIST.md)
   ↓
8. Production Deployment + Monitoring

```

### Dependency Matrix

| Task | Depends On | Blocks | Owner | Status |
|------|-----------|--------|-------|--------|
| DB Schema + RLS | — | Everything | Backend (Vertex) | ⏳ |
| Auth (Magic Link + Google) | DB Schema | Dashboard, Profile, Events | Full-stack (v0 + Backend) | ⏳ |
| Assessment Flows (BARS, MCQ, Open Text) | DB Schema, Auth | AURA Calc, Results Screen | Frontend (v0) + Backend (LLM) | ⏳ |
| AURA Score Calculation | Assessment Engine | Dashboard, Profile, Leaderboard | Backend (Vertex) | ⏳ |
| Dashboard Page | Auth, AURA Calc | Events, Notifications | Frontend (v0) | ⏳ |
| Profile Page + OG Images | Auth, AURA Calc | Public Sharing, Share Links | Frontend (v0) | ⏳ |
| Events & Org Portal | DB Schema, Auth, AURA Calc | Post-Event Attestation | Full-stack (v0 + Backend) | ⏳ |
| Post-Event Attestation | Events, AURA Calc | AURA Boost (1.15x), Notifications | Backend (Vertex) | ⏳ |
| Backend API Endpoints | DB Schema, FastAPI setup | Frontend integration | Backend (Vertex) | ⏳ |
| API Type Safety (@hey-api) | Backend API | Frontend generated hooks | Backend (Vertex) | ⏳ |
| Referral System | Auth, Email service | Growth tracking, Bonus application | Backend (Vertex) | ⏳ |
| Email Lifecycle (Resend) | Auth, Assessment completion | User engagement, Notifs | Backend (Vertex) | ⏳ |
| Analytics Events (GA4) | Frontend app | Growth metrics tracking | Frontend (v0) | ⏳ |
| AURA Coach (AI) | Gemini API, User profile data | Growth nudges, Engagement | Backend (Gemini) | ⏳ |
| Live Stats + Activity Feed | DB Activity Log, Realtime | Platform "liveness" | Full-stack | ⏳ |
| Streaks + Leagues | Assessment completion, Events | Gamification display | Backend (Vertex) | ⏳ |
| Testing (Unit + E2E) | All modules | Launch readiness | QA (Perplexity reviews) | ⏳ |
| Staging Deployment | All code | Production deploy | DevOps / Founder | ⏳ |
| Security Audit | All code + RLS | Launch readiness | Perplexity review | ⏳ |
| i18n Completeness (AZ + EN) | All UI + Copy | Launch readiness | Founder + Native speakers | ⏳ |
| Performance Optimization | All modules | Lighthouse >90 | Frontend (v0) + Backend | ⏳ |
| Monitoring Setup (Sentry, UptimeRobot) | Staging deployment | Launch readiness | DevOps / Founder | ⏳ |
| Production Deployment | All above | DONE | Founder | ⏳ |

---

## PART 4: Risk Register (Top 10)

| # | Risk | Probability | Impact | Mitigation | Owner | Status |
|---|------|-------------|--------|-----------|-------|--------|
| 1 | LLM evaluation fails at scale (Gemini quota, latency) | Medium | High | Cache evaluations in session at submit, fallback heuristic (word_count*0.6), rate limit (30/hour/user), queue retries via pg_cron | Backend | Open |
| 2 | Supabase free tier limits (100 concurrent connections) | Medium | Critical | Monitor free tier usage daily, plan upgrade to Pro (estimate $100-200/mo) at 200 volunteers, test connection pooling | DevOps | Open |
| 3 | i18n quality (native AZ text, character rendering) | High | Medium | Hire Azerbaijani-speaking reviewer day 1, test character rendering (ə, ğ, ı, ö, ü, ş, ç) on real devices, provide glossary to LLM | Founder | Open |
| 4 | Assessment abandonment rate >50% (UX friction, performance) | Medium | High | A/B test UI (progressive disclosure, timer feedback), optimize Core Web Vitals <2.5s LCP, collect feedback via post-event survey | Frontend | Open |
| 5 | Email delivery issues (Resend domain auth, spam folder) | Low | Medium | Set up DKIM/SPF/DMARC 48 hours before launch, test send to Gmail/Outlook/Yahoo, monitor Resend dashboard (target >95% delivery rate) | Backend | Open |
| 6 | RLS policies leak private data (logic error in policies) | Low | Critical | Peer review ALL RLS policies (2 people minimum), test with 2 users cross-access in staging, automated RLS tests in CI | Backend | Open |
| 7 | Rate limiting too strict/too loose (user frustration or abuse) | Low | Medium | Set conservative limits (e.g., 5/min auth, 100/min assessments), monitor rate limit hits in logs, adjust based on event feedback | Backend | Open |
| 8 | v0 generated code has bugs (frontend), Vertex API generated code is incomplete | Medium | High | Perplexity reviews ALL generated code before merge, manual integration testing on staging, fallback: hand-write critical paths if needed | Frontend/Backend | Open |
| 9 | Domain/DNS issues (volaura.com not resolving, SSL cert) | Low | High | Register domain 2+ weeks before launch, add DNS records 48 hours before, verify HTTPS 1 week before on staging | DevOps | Open |
| 10 | Volunteers can't join day 1 (auth flow broken, DB connection down) | Low | Critical | Full smoke test 24 hours before launch event (signup → assessment → profile view), have 2-hour rollback plan, monitor Sentry + Railway logs in real-time | Founder | Open |

---

## PART 5: Generation Order (v0, Vertex, Perplexity)

### Phase 1: Foundation (Week 1-2)

**Vertex (Backend):**
1. Database schema + migrations + RLS policies
2. FastAPI app structure (main.py, routers, deps)
3. Supabase client setup (per-request via Depends)
4. Pydantic models for all endpoints
5. OpenAPI schema generated

**v0 (Frontend):**
1. Next.js 14 setup (App Router, Tailwind 4, i18n)
2. Layouts (Header, Footer, BottomNav)
3. Landing page + Auth pages (login flow)
4. i18n namespace structure + base translations (AZ + EN)

**Perplexity (Review):**
- Code review: Backend architecture (per-request clients, error handling)
- Code review: Frontend structure (App Router usage, component organization)
- Flag any deviations from CLAUDE.md rules

### Phase 2: Core Features (Week 3-4)

**Vertex (Backend):**
1. Auth endpoints: POST /auth/magic-link, GET /auth/callback, POST /auth/google
2. Assessment endpoints: POST /assessments/start, POST /assessments/{id}/answers, POST /assessments/{id}/complete
3. AURA score calculation service (WeightsService)
4. LLM evaluation service (Gemini integration, async BackgroundTasks)
5. Supabase Realtime subscriptions for live events

**v0 (Frontend):**
1. Assessment Hub (8 competency cards)
2. Question components: BARSScale, MCQOptions, OpenTextInput
3. Results screen (confetti, score counter, radar chart)
4. Dashboard page (score card, notifications, events preview)
5. Profile page (authenticated view)

**Perplexity (Review):**
- Integration test: signup → assessment flow → score calculation
- Test: LLM evaluation async pattern (202 response, polling)
- Check: All API responses match envelope spec

### Phase 3: Extended Features (Week 5-6)

**Vertex (Backend):**
1. Events & Organizations endpoints
2. Post-event attestation workflow
3. Referral system (invite, conversion, bonus)
4. Email service integration (Resend)
5. Analytics event tracking
6. Coach message generation (Gemini context-aware)

**v0 (Frontend):**
1. Events list & detail pages
2. Org portal (create events, search volunteers, attestation queue)
3. Public profile page (SSR, OG image via /api/og)
4. Share buttons (LinkedIn, Twitter, WhatsApp, QR)
5. Referral invite UI
6. Coach floating button + messages

**Perplexity (Review):**
- Security audit: RLS policies cross-access test
- i18n audit: all namespaces extracted, no hardcoded strings
- Performance audit: Lighthouse test on landing + profile pages

### Phase 4: Polish & Launch Prep (Week 7-8)

**Vertex (Backend):**
1. Rate limiting on all endpoints (slowapi)
2. Monitoring setup (Sentry, health endpoint)
3. Seed data (test questions, sample orgs/events)
4. Database backups configured
5. Email template testing (Litmus preview)

**v0 (Frontend):**
1. Dark mode support
2. Animation polish (Framer Motion spring tweaks)
3. Mobile responsive fixes
4. Offline mode (service worker, PWA)
5. Accessibility audit (WCAG 2.1 AA)

**Perplexity (Review):**
- Full E2E test: signup → 8 assessments → profile → share → event registration
- Performance: Lighthouse >90 overall, >95 Accessibility
- Security: No secrets in code, RLS verified, CORS tested

### API Code Generation

**After Vertex completes backend API:**
```bash
# Extract OpenAPI schema
curl https://api.railway.app/openapi.json > openapi.json

# Generate TypeScript + TanStack Query hooks
pnpm generate:api
```

This produces:
- `lib/api/generated/types.ts` — All API types
- `lib/api/generated/hooks.ts` — TanStack Query hooks
- `lib/api/generated/schemas.ts` — Zod schemas

v0 uses generated hooks in all API calls (e.g., `const { data, isLoading } = useGetHealthQuery()`).

---

## PART 6: Integration Checklist (v0 ↔ Vertex)

### Frontend Reads Backend API

- [ ] Frontend imports generated hooks from `@/lib/api/generated`
- [ ] Assessment start: `const { data } = usePostAssessmentsStart({ body: { competency } })`
- [ ] Submit answer: `const { data } = usePostAssessmentsIdAnswers({ body: {...} })`
- [ ] Poll LLM status: `const { data } = useGetAssessmentsIdResponsesResponseIdStatus()`
- [ ] Get AURA score: `const { data } = useGetScoresMe()`
- [ ] Get leaderboard: `const { data } = useGetScoresLeaderboard({ limit: 50 })`
- [ ] Get events: `const { data } = useGetEvents({ status: 'upcoming' })`
- [ ] Register event: `const { data } = usePostEventIdRegister()`
- [ ] Semantic search: `const { data } = usePostOrgVolunteersSearch({ query })`
- [ ] Get coach messages: `const { data } = useGetCoachMessage({ context: 'dashboard' })`

All hooks use TanStack Query for caching, refetching, mutations.

### Database Integration

- [ ] Frontend server components use `createClient()` from `@/lib/supabase/server`
- [ ] Example: Fetch public profile on SSR (no Auth header, just `is_public=true`)
- [ ] Client components use `createClient()` from `@/lib/supabase/client`
- [ ] Example: Real-time subscription to `event_registrations` on event detail page

### Realtime Subscriptions

- [ ] Event detail page: subscribe to `events` channel, watch `registered_count`
- [ ] Activity feed: subscribe to `activity_log`, filter `is_public=true`
- [ ] Assessment: subscribe to `assessment_responses`, watch for LLM score updates

Setup:
```typescript
supabase
  .channel('events')
  .on('postgres_changes', { event: 'UPDATE', schema: 'public', table: 'events' }, (payload) => {
    setRegisteredCount(payload.new.registered_count);
  })
  .subscribe();
```

### Error Handling Consistency

- [ ] Backend returns structured errors: `{ detail: { code: "ERROR_CODE", message: "..." } }`
- [ ] Frontend catches and localizes: `t("errors." + error.code)`
- [ ] Example: `detail.code = "INSUFFICIENT_AURA"` → `t("errors.INSUFFICIENT_AURA")` → "AURA balınız bu tədbir üçün kifayət deyil"

### i18n Handoff

- [ ] Backend returns bilingual responses: `{ text_az: "...", text_en: "..." }`
- [ ] Frontend uses user's selected locale: `const { i18n } = useTranslation(); const text = response[i18n.language]`
- [ ] No backend-side locale detection; client always sends locale in request (optional header: `Accept-Language`)

### Testing Integration

- [ ] Manual test: signup (auth backend) → assessment start (API) → answer question (API) → score calculation (backend) → profile render (frontend + DB read)
- [ ] Staging deployment: test full flow on Railway + Vercel staging URLs
- [ ] Sentry error test: trigger 500 error intentionally, verify in Sentry dashboard

---

## PART 7: Pre-Launch Checklist (Pass/Fail)

This checklist is the FINAL gate before production deploy. Every item must be checked OFF.

### 1 Week Before Launch Event

#### Infrastructure
- [ ] Supabase Production project created (NOT free tier)
- [ ] All migrations applied: `supabase db push`
- [ ] RLS policies verified on ALL 15+ tables (run test script)
- [ ] Supabase Auth configured: Magic Link email templates customized (AZ + EN)
- [ ] Supabase Auth: Google OAuth provider added + redirect URLs set
- [ ] Railway FastAPI deployment live: health endpoint responds 200
- [ ] Vercel frontend deployed to production domain
- [ ] Custom domain (volaura.com) DNS records set + SSL active
- [ ] Email service (Resend): domain authenticated, DKIM/SPF/DMARC verified

#### Environment Variables
- [ ] Vercel: NEXT_PUBLIC_API_URL, NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY set
- [ ] Railway: SUPABASE_URL, SUPABASE_SERVICE_KEY, GEMINI_API_KEY, RESEND_API_KEY set
- [ ] No secrets in git: `git log --all -- .env` → empty
- [ ] Sentry projects created (frontend + backend), DSN added

#### Security
- [ ] RLS cross-access test: User A cannot read/update User B's data
- [ ] CORS test: external origin blocked
- [ ] CSP headers configured + tested (DevTools → Console → no CSP violations)
- [ ] Rate limiting live: test 6 requests to /auth/magic-link in 1 min → 429 on 6th
- [ ] HTTPS enforced: curl -I http://volaura.com → 308 redirect
- [ ] Secrets rotated: old API keys revoked

#### Performance
- [ ] Lighthouse score on landing page: >90 overall, >95 Accessibility, >95 Best Practices
- [ ] Lighthouse Core Web Vitals: LCP <2.5s, FID <100ms, CLS <0.1
- [ ] Bundle size: initial JS <300KB gzipped (verify `npm run analyze`)
- [ ] Images optimized: all use `<Image>`, WebP served, lazy loading active
- [ ] ISR revalidation set: landing (1h), public profiles (1min), leaderboard (5min)
- [ ] OG image generation tested: /api/og/[username] returns image <200KB

#### Functionality (Manual Smoke Test)
- [ ] **Full signup flow**: email → magic link → profile created → dashboard loads
- [ ] **Assessment flow**: start → answer 8 competencies (24-40 questions) → AURA calculated → badge tier correct
- [ ] **AURA calculation test**: all scores 100 → AURA = 100, badge = Platinum
- [ ] **Profile page**: name, AURA, radar chart, event timeline, share buttons visible + working
- [ ] **Share cards**: LinkedIn/Twitter/WhatsApp links work, OG image preview renders
- [ ] **Public profile**: /u/[username] accessible without login, OG image in preview
- [ ] **Events page**: list loads, filters work, registration flow completes
- [ ] **Event registration**: volunteer registered → capacity counter increments live
- [ ] **Org portal**: create event, search volunteers, attestation workflow functions
- [ ] **Leaderboard**: top 100 visible, pagination works, data updates every 5min (ISR)
- [ ] **Offline mode**: disable network → complete assessment → re-enable → syncs + score appears
- [ ] **Notifications**: bell icon shows unread count, notifications load on click

#### i18n
- [ ] All pages tested in AZ: text renders, no [missing] warnings in console
- [ ] All pages tested in EN: text renders
- [ ] Azerbaijani characters (ə, ğ, ı, ö, ü, ş, ç) render correctly on all pages
- [ ] Date formatting: AZ = dd.MM.yyyy, EN = MM/dd/yyyy (check leaderboard, profile)
- [ ] Number formatting: AZ = 1.234,56, EN = 1,234.56 (check AURA scores)
- [ ] Email templates bilingual: test signup email in AZ + EN
- [ ] Error messages localized: trigger error, verify message in correct language

#### Email
- [ ] Resend account verified, domain authenticated
- [ ] Welcome email sends within 1 minute of signup
- [ ] Magic link email sends within 30 seconds
- [ ] Magic link valid for 24 hours
- [ ] Score ready email sends 5 minutes after assessment completion
- [ ] Email rendering tested in Litmus: Gmail, Outlook, Apple Mail, mobile clients
- [ ] Email links are clickable, images load

#### Monitoring & Alerts
- [ ] Sentry configured: frontend + backend projects active
- [ ] Test error reporting: intentional JS error → appears in Sentry
- [ ] Test backend error: intentional 500 → appears in Sentry
- [ ] Sentry alerts configured: email notification on critical error
- [ ] Vercel Analytics enabled: Web Vitals dashboard shows data
- [ ] Health endpoint responds: GET /api/health → 200 { status: ok }
- [ ] UptimeRobot configured: monitors volaura.com + api.railway.app, ping interval 5min

#### QA Completion
- [ ] All 9 modules have acceptance tests passing (run test suite)
- [ ] No critical bugs in Sentry
- [ ] Perplexity review completed: code quality, security, performance approved
- [ ] Staging deployment fully tested: no blockers
- [ ] Rollback plan documented (git revert, Vercel + Railway rollback steps)

---

### Launch Day (T-0)

#### Before Doors Open (2 Hours Before)

- [ ] Monitor Sentry dashboard (open on 2nd screen)
- [ ] Check Railway resource usage: CPU/RAM <80%
- [ ] Check Supabase connection count: <80 of 100 (free tier limit)
- [ ] Pre-warm ISR cache: script hits all public profile URLs + leaderboard page
- [ ] Test QR codes at venue: scan with iOS + Android → opens /en/start, loads <3s on venue WiFi
- [ ] Test leaderboard display (TV/projector at venue): shows live top 10, data refreshes every 30s
- [ ] Verify offline mode: open assessment → disable network → answer questions → re-enable → syncs
- [ ] Verify quick mode: assessment completes in <10 minutes (IRT/CAT speeds up on high confidence)
- [ ] Final health check: all endpoints responding, no 5xx errors in last 1 hour

#### During Event (Real-Time Monitoring)

- [ ] Watch Sentry for errors (Slack integration or email alerts)
- [ ] Monitor Supabase connections: if >95 → upgrade to Pro immediately
- [ ] Check Railway logs: watch for 500 errors, timeout errors, LLM quota issues
- [ ] Track assessment completion rate: signups vs. completions (target >70% completion)
- [ ] Be ready to patch: laptop open with git/GitHub, test locally before pushing to main
- [ ] Communicate status: if issues arise, notify venue staff + attendees

---

### Post-Launch (T+1 to T+7)

- [ ] Review Sentry errors: filter last 7 days, group by issue, assess severity
- [ ] Analyze user analytics: total signups, completions, completion rate, score distribution
- [ ] Check email delivery: Resend dashboard → delivery rate >95%, bounce rate <2%
- [ ] Review Core Web Vitals: Google Analytics real user metrics (not lab)
- [ ] Gather feedback: post-event survey, email replies, support tickets
- [ ] Plan hotfixes: prioritize bugs affecting >5 users, schedule sprints
- [ ] Send follow-up emails: personalized score cards to launch event attendees
- [ ] Org outreach: thank organizers, share data, offer partnership

---

## PART 8: Launch Success Metrics

Define what "successful launch" looks like:

| Metric | Target | Measure | Owner |
|--------|--------|---------|-------|
| **Day 1 Signups** | 150-200 | GA4 / Supabase auth.users count | Founder |
| **Assessment Completion Rate** | >70% | (completions / signups) | Founder |
| **Avg Assessment Time** | 15-25 min | median time_spent_seconds / 60 | Backend logs |
| **Avg AURA Score** | 60-75 | mean(aura_scores.composite_score) | Supabase query |
| **Email Delivery Rate** | >95% | Resend dashboard | Backend |
| **Sentry Error Rate** | <1% | critical errors / total requests | Sentry |
| **Lighthouse Score** | >90 | PageSpeed Insights | Frontend |
| **Core Web Vitals** | LCP <2.5s, CLS <0.1 | Google Analytics | Frontend |
| **System Uptime** | 99%+ | UptimeRobot | DevOps |
| **Supabase Conn. Usage** | <80/100 | Supabase dashboard | DevOps |
| **User Satisfaction** | 4.5+/5.0 | post-event survey NPS | Founder |
| **Share Rate** | 40%+ | (share clicks / completions) | GA4 |
| **Referral Conversion** | 15%+ | (conversions / invites sent) | Backend |

---

## PART 9: Post-Launch Roadmap (Month 2+)

Once launch stabilizes, prioritize:

1. **Bug Fixes** (Week 1): address top 5 issues from Sentry
2. **Org Outreach** (Week 2): invite orgs to partner, showcase volunteer data
3. **Feature Requests** (Week 3): collect feedback, prioritize high-impact asks
4. **Growth Loop** (Week 4): optimize referral bonus, email nudges, leaderboard competition
5. **Expansion** (Month 2): CIS Games event setup, geographic expansion planning

---

## Summary

This ACCEPTANCE-CRITERIA.md document provides:

✅ **Part 1**: Global Definition of Done (code, testing, accessibility, i18n, performance, security, design)
✅ **Part 2**: Acceptance Criteria for all 9 modules in Gherkin Given/When/Then format
✅ **Part 3**: Dependency Graph showing critical path + dependency matrix
✅ **Part 4**: Top 10 Risk Register with probability, impact, mitigations
✅ **Part 5**: Generation Order (v0, Vertex, Perplexity) with phases
✅ **Part 6**: Integration Checklist (frontend ↔ backend, API, i18n, Realtime)
✅ **Part 7**: Pre-Launch Checklist (all 90+ items, T-1 week, launch day, T+7)
✅ **Part 8**: Launch Success Metrics (KPIs to track)
✅ **Part 9**: Post-Launch Roadmap

**Use this as the single source of truth for "ready to ship".**
