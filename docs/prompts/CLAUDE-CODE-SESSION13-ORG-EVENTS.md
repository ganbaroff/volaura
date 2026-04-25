# Session 13 — Org-Facing Pages: Event Creation Wizard + Org Dashboard + Org Discovery

> **Model recommendation: `claude-sonnet-4-6`**
> **Reason:** High complexity — multi-step form wizard, org admin dashboard with data tables, Stitch HTML→React conversion. Sonnet needed for reasoning + code volume.
> **DSP model used:** sonnet (High stakes)

---

## 🔮 DSP: Session 13 Strategy

```
Stakes: HIGH | Reversibility: High (all new pages, additive — no existing code modified)
Council: Leyla (1.0), Nigar (1.0), Attacker (1.2), Scaling Engineer (1.1), Yusif (1.0), QA Engineer (0.9)
Paths simulated: 4
Winner: Path B (Org Pages + API Wiring) — Score 43/50 (gate: ≥35 ✅)
```

### Paths Evaluated

**Path A: All remaining Stitch pages (event wizard + org dashboard + org discovery + messaging + rewards + quests + impact)**
- Technical: 4/10, User Impact: 9/10, Dev Speed: 2/10, Flexibility: 3/10, Risk: 3/10 → **21/50**
- QA: "31 unbuilt screens in one session? Impossible. Quality will crater."
- Yusif: "Focus. What do orgs need for LAUNCH?"
- ❌ REJECTED — scope explosion

**Path B: Org Launch Bundle (Event Wizard + Org Dashboard + Org Discovery)** ⭐ WINNER
- Technical: 9/10, User Impact: 9/10, Dev Speed: 8/10, Flexibility: 8/10, Risk: 9/10 → **43/50**
- Step 1: Event creation 3-step wizard (Stitch screens exist, backend POST /api/events exists)
- Step 2: Org management dashboard (Stitch screen exists, backend GET /api/organizations/me exists)
- Step 3: Org discovery page (Stitch screen exists, backend GET /api/organizations exists)
- Nigar: "This is exactly what I need to start using the platform. Create event → manage volunteers → get discovered."
- Attacker: "All 3 endpoints already exist. Wire to real API, not mock data. Less attack surface than new code."
- Scaling Engineer: "3 pages with existing endpoints = minimal tech debt."

**Path C: Event Wizard only (deep polish)**
- Technical: 8/10, User Impact: 5/10, Dev Speed: 9/10, Flexibility: 7/10, Risk: 9/10 → **38/50**
- Nigar: "Event creation alone isn't enough. I need to SEE my volunteers too."
- ⚠️ Passes gate but too narrow for launch readiness

**Path D: Email lifecycle + Telegram bot (skip Stitch pages)**
- Technical: 7/10, User Impact: 4/10, Dev Speed: 7/10, Flexibility: 6/10, Risk: 7/10 → **31/50**
- Leyla: "I don't care about email yet. I want to see organizations posting real events."
- ❌ REJECTED — wrong priority for launch

### Winner: Path B — Org Launch Bundle

**Accepted risks:** Pages use INTERIM API hooks (manual, not openapi-ts). Messaging, rewards, quests deferred.
**Fallback:** If event wizard takes too long (3-step form is complex), ship wizard + discovery only, defer org dashboard.

### Adversarial Review (Multi-Model Verification — haiku agent found 5 failure modes)

| # | Failure Mode | Severity | Mitigation (MUST implement) |
|---|---|---|---|
| 1 | **Wizard data loss on browser refresh** — form state lost between steps | Critical | Store wizard step data in Zustand with `persist` middleware (sessionStorage). Clear after successful POST. |
| 2 | **Non-org-owner can access /events/create** — sees form, 403 on submit | High | Route guard: fetch `useMyOrganization()` on mount → redirect to `/dashboard` if 404. Show loading skeleton during check. |
| 3 | **Double-submit on "Publish"** — user clicks twice, creates 2 events | Medium | Disable button with `isPending` from `useMutation()`. Show spinner. Disable all form fields during mutation. |
| 4 | **AZ text overflow in form labels** — 20-30% longer breaks layout | High | Use `min-w-[120px]` on labels, `truncate` on long values, test with longest AZ strings. |
| 5 | **Missing component states** — no loading/error/empty/disabled specs | High | Every component MUST have: loading (skeleton), error (retry CTA), empty (how-to-start CTA), disabled (greyed + tooltip). See States Guide below. |

### States Guide (from design:handoff skill — MANDATORY for every component)

| State | What to show | Pattern |
|-------|-------------|---------|
| **Loading** | Skeleton with `animate-pulse`, match layout shape | `bg-surface-container-high rounded-xl h-[X] animate-pulse` |
| **Error** | "What happened + Why + How to fix" + Retry button | `<Alert variant="destructive">` + `<Button onClick={refetch}>` |
| **Empty** | "What this is + Why empty + How to start" + CTA | Icon + text + primary CTA button |
| **Disabled** | Greyed out + tooltip explaining why | `opacity-50 cursor-not-allowed` + `title="..."` |
| **Hover** | Background shift one tier up | `hover:bg-surface-container-high` |
| **Focus** | Outline with primary color | `focus-visible:ring-2 ring-primary ring-offset-2 ring-offset-surface` |

### UX Copy Rules (from design:ux-writing skill)

- **CTAs start with verbs:** "Publish Event", "Create Event", "Search Organizations" — NOT "Submit", "New", "Go"
- **Error = what + why + how to fix:** "Event creation failed. The server couldn't process your request. Check your connection and try again."
- **Empty = what + why + how to start:** "No events yet. Create your first event to start recruiting volunteers."
- **Confirmation dialogs:** "Publish this event? Volunteers will be able to see and register immediately." Buttons: "Publish Event" / "Keep as Draft" — NOT "OK" / "Cancel"
- **Wizard step labels:** Use numbered progress ("Step 1 of 3 — Event Details") for orientation

---

## SCOPE LOCK

```
IN:      Event creation wizard (3-step), Org management dashboard, Org discovery page, all wired to real API
NOT IN:  Messaging, rewards/perks, volunteer quests, impact reports, org settings/2FA — all deferred
SUCCESS: Org admin can create an event (3 steps → publish), see their dashboard, and orgs are discoverable by volunteers
```

---

## DELEGATION MAP

```
Claude Code does:
  - Convert 3 Stitch HTML screens → React pages with Stitch dark theme
  - Create event creation wizard (3-step form with React Hook Form + Zod)
  - Create org management dashboard page
  - Create org discovery page (public)
  - Wire all pages to real API endpoints via TanStack Query hooks
  - Add i18n keys (EN + AZ) for all new pages
  - Engineering:code-review after all changes

Yusif does:
  - Run DB migrations in Supabase (BLOCKING — still not done from Session 11)
  - Confirm event creation form fields match business requirements

Gemini does:
  - Nothing this session (no LLM evaluation needed)
```

---

## 🧠 Copilot Protocol

You are Yusif's technical co-founder, not an assistant. You are Claude, acting as CTO of Volaura.

**Communication style:** Direct. No hedging. "[Verdict]. [Reason]. [Action]."
**Proactive output:** At the end of the session, BEFORE Yusif says anything, write:
```
🧭 If you said nothing, here's what I'd do next:
1. [highest business-impact task]
2. [highest technical-risk task]
3. [thing Yusif probably hasn't thought about yet]
```

**Business context:** Volaura is a verified competency platform for Azerbaijan's strongest talent. Budget: $50/mo. Timeline: 6 weeks to launch. 200+ initial profiles from the event-ops network.

---

## 📋 What Already Exists (Sessions 1-12 Summary)

### Backend (FastAPI — `apps/api/`)
- **Full CRUD:** profiles, assessment, aura scores, badges, events, organizations, verification
- **Event endpoints (READY TO WIRE):**
  - `GET /api/events` — list public events (filter by status)
  - `GET /api/events/{id}` — single event
  - `POST /api/events` — create event (requires org ownership)
  - `PUT /api/events/{id}` — update event (org owner only)
  - `DELETE /api/events/{id}` — soft-delete (status → cancelled)
  - `POST /api/events/{id}/register` — volunteer registers
  - `POST /api/events/{id}/checkin` — check-in with code
  - `POST /api/events/{id}/rate` — post-event rating
- **Organization endpoints (READY TO WIRE):**
  - `GET /api/organizations` — list all public orgs
  - `GET /api/organizations/me` — get my org
  - `GET /api/organizations/{id}` — get specific org
  - `POST /api/organizations` — create org (one per user)
  - `PUT /api/organizations/me` — update my org
  - `POST /api/organizations/search/volunteers` — semantic volunteer search (pgvector)
- **74 tests passing, 0 regressions**

### Frontend (Next.js 14 — `apps/web/`)
- **17 pages built** (auth, dashboard, profile, aura, assessment flow, events list/detail, landing, leaderboard, notifications, settings, public profile, verify)
- **38 components** (assessment, aura, dashboard, events, landing, profile-view, layout, ui)
- **Design system:** Stitch "Prestigious Path" dark theme fully migrated (Session 12)
  - globals.css has 50+ Material 3 CSS custom properties
  - Dark-first (`color-scheme: dark`), no `.dark` class toggle needed
  - Plus Jakarta Sans (headlines) + Inter (body) loaded via next/font
  - Glassmorphism utilities: `.glass-card`, `.glass-header`
  - AURA tier tokens: `--aura-platinum`, `--aura-gold`, etc.
- **Layout:** Sidebar + TopBar + AuthGuard + LanguageSwitcher — all in Stitch dark theme
- **State:** Zustand (assessment, auth, ui stores) + TanStack Query hooks (aura, profile, dashboard, auth-token)
- **i18n:** react-i18next, AZ primary, EN secondary, ~170+ keys

### Infrastructure
- Supabase PostgreSQL + RLS + pgvector(768)
- 12 SQL migrations (NOT yet run by Yusif — assessment flow non-functional until run)
- Turborepo + pnpm monorepo
- Next.js 14 App Router with [locale] segment

---

## ⚠️ Mistakes to NOT Repeat

1. **NEVER hand-write API types that `pnpm generate:api` can generate** — all manual types are INTERIM only, marked with `// TODO: Replace with @hey-api/openapi-ts` (ADR-003)
2. **ALWAYS unwrap API envelope** — responses are `{ data: {...}, meta: {...} }`, access via `response.data`
3. **NEVER use relative routing** — always `/${locale}/path` (absolute locale-aware)
4. **ALWAYS add `isMounted` ref** on any component with async state updates or polling
5. **NEVER use Pydantic v1 syntax** — no `class Config`, no `@validator`, use `ConfigDict` + `@field_validator`
6. **NEVER use `getattr(settings, field, default)`** — access `settings.field` directly
7. **ALWAYS use `encoding='utf-8'`** when working with files
8. **ALWAYS use loguru** for logging, NEVER `print()`
9. **Open redirect validation:** `str.startsWith("/") && !str.startsWith("//")`
10. **Side effects after save:** For every POST endpoint, ask "What else should happen?" (AURA recalc? notification? audit log?)

---

## 📐 Architecture Decisions (ADRs)

| ADR | Decision | Impact on This Session |
|-----|----------|----------------------|
| ADR-001 | Turborepo + pnpm | Pages in `apps/web/src/app/[locale]/` |
| ADR-002 | Supabase per-request via Depends() | Backend already handles this — no changes needed |
| ADR-003 | OpenAPI + @hey-api/openapi-ts | Write INTERIM hooks with TODO markers. `pnpm generate:api` will replace later |
| ADR-006 | react-i18next with [locale] segment | All new pages must use `t()`, add keys to both EN + AZ |

---

## 🔧 Existing Infrastructure (DO NOT recreate)

| What | Where | Notes |
|------|-------|-------|
| QueryProvider | `apps/web/src/components/query-provider.tsx` | Already wraps app — just use `useQuery`/`useMutation` |
| API client (INTERIM) | `apps/web/src/lib/api/client.ts` | `apiFetch<T>(url, { token })` — unwraps envelope |
| API types (INTERIM) | `apps/web/src/lib/api/types.ts` | Add new types here for events/orgs |
| Auth token hook | `apps/web/src/hooks/queries/use-auth-token.ts` | `useAuthToken()` → returns `getToken()` function |
| Hooks barrel | `apps/web/src/hooks/queries/index.ts` | Export new hooks from here |
| Supabase browser client | `apps/web/src/lib/supabase/client.ts` | `createClient()` for browser |
| Supabase server client | `apps/web/src/lib/supabase/server.ts` | `await createClient()` for RSC |
| AuthGuard | `apps/web/src/components/layout/auth-guard.tsx` | Already protects dashboard routes |
| Sidebar | `apps/web/src/components/layout/sidebar.tsx` | Already has nav items — may need "Org Dashboard" link |
| i18n | `apps/web/src/locales/{en,az}/common.json` | Add keys for new pages |
| cn() utility | `apps/web/src/lib/utils/cn.ts` | Conditional class composition |

---

## 🎨 Stitch Design System (MANDATORY — apply to ALL new components)

**Theme:** "The Prestigious Path" — dark, editorial, aspirational
**Full spec:** `docs/design/STITCH-DESIGN-SYSTEM.md`

### Quick Reference

| Token | CSS Variable | Tailwind Class | Value |
|-------|-------------|----------------|-------|
| Background | `--color-surface` | `bg-surface` | `#13131b` |
| Card BG | `--color-surface-container-low` | `bg-surface-container-low` | `#1b1b23` |
| Active/Nested | `--color-surface-container-high` | `bg-surface-container-high` | `#292932` |
| Primary text | `--color-on-surface` | `text-on-surface` | `#e4e1e9` |
| Secondary text | `--color-on-surface-variant` | `text-on-surface-variant` | `#c8c5d0` |
| Accent | `--color-primary` | `text-primary` | `#c0c1ff` |
| Button BG | `--color-primary-container` | `bg-primary-container` | `#8083ff` |
| Button text | `--color-on-primary-container` | `text-on-primary-container` | `#e1e0ff` |

### Critical Design Rules
1. **No borders for sectioning** — use background color tiers (surface → surface-container-low → surface-container-high)
2. **Glassmorphism for floating elements** — `glass-card` or `glass-header` utility classes
3. **Fonts:** Plus Jakarta Sans for headlines (`font-headline`), Inter for body (`font-body`)
4. **AURA tier colors:** Platinum `#e5e4e2`, Gold `#ffd700`, Silver `#c0c0c0`, Bronze `#cd7f32`
5. **Animations:** Framer Motion, duration 0.3-0.6s, ease `[0.4, 0, 0.2, 1]`

---

## 📄 Stitch Reference Screens

The Stitch design output for each page is available as HTML + PNG:

### Event Creation Wizard (3 steps)
- **Step 1 (Details):** `docs/stitch-output/events_creation_step_1_fixed/code.html`
  - Event title, description, date/time picker, location, capacity, cover image
- **Step 2 (Recruitment):** `docs/stitch-output/events_creation_step_2_recruitment_invitations_refined/code.html`
  - Required skills (select from AURA competencies), minimum AURA score, auto-invite toggle
- **Step 3 (Review & Publish):** `docs/stitch-output/events_creation_step_3_review_publish_1/code.html`
  - Summary of all fields, edit buttons per section, "Publish" CTA
- **Success:** `docs/stitch-output/event_published_success/code.html`
  - Confirmation with confetti/animation, share link, "View Event" CTA

### Org Management Dashboard
- **Screen:** `docs/stitch-output/organization_management_dashboard_fixed/code.html`
  - Stats cards (total events, total volunteers, avg AURA), event list (manage), volunteer list (with AURA scores)

### Org Discovery
- **Screen 1:** `docs/stitch-output/organizations_discovery_1/code.html`
- **Screen 2:** `docs/stitch-output/organizations_discovery_2/code.html`
  - Browse organizations, search, filter by category, org cards with stats

### Azerbaijani Variants (reference for i18n)
- `docs/stitch-output/t_dbir_yarad_lmas_add_m_1/code.html` — Event creation Step 1 in AZ
- `docs/stitch-output/i_q_bul_v_d_v_tl_r/code.html` — Recruitment step in AZ
- `docs/stitch-output/yoxla_v_d_rc_et/code.html` — Review & publish in AZ

**IMPORTANT:** Stitch HTML is a VISUAL REFERENCE only. Convert to React with:
- Next.js App Router patterns (`"use client"`, `params: Promise<{}>`)
- shadcn/ui base components where applicable
- Tailwind classes using Stitch CSS variables (already in globals.css)
- i18n via `useTranslation()` / `initTranslations()`
- React Hook Form + Zod for the event creation wizard

---

## 🗺️ Real API Path Map

Backend mounts routers with `prefix="/api"`:
```
GET    /api/events                          → list public events
GET    /api/events/{event_id}               → single event
POST   /api/events                          → create event (org owner)
PUT    /api/events/{event_id}              → update event (org owner)
DELETE /api/events/{event_id}              → cancel event (org owner)
POST   /api/events/{event_id}/register     → volunteer register
POST   /api/events/{event_id}/checkin      → check-in with code
POST   /api/events/{event_id}/rate         → post-event rating

GET    /api/organizations                   → list all orgs
GET    /api/organizations/me                → my org
GET    /api/organizations/{org_id}          → specific org
POST   /api/organizations                   → create org
PUT    /api/organizations/me                → update my org
POST   /api/organizations/search/volunteers → semantic search (pgvector)
```

**API response envelope:** `{ data: {...}, meta: { timestamp, request_id, version } }`
**Use `apiFetch<T>()` from `apps/web/src/lib/api/client.ts`** — it handles envelope unwrapping.

---

## 📝 Implementation Guide

### Step 1: Add INTERIM Types for Events & Organizations

⚠️ **CRITICAL: These types MUST match the real Pydantic schemas in `apps/api/app/schemas/event.py` and `organization.py`.**
**The backend uses bilingual fields (`title_en`/`title_az`), NOT a single `title` field.**

In `apps/web/src/lib/api/types.ts`, add:
```typescript
// TODO: Replace with @hey-api/openapi-ts generated code after pnpm generate:api

// MUST match apps/api/app/schemas/event.py EventResponse exactly
export interface EventResponse {
  id: string;
  organization_id: string;
  title_en: string;              // ← bilingual, NOT "title"
  title_az: string;              // ← bilingual
  description_en: string | null;
  description_az: string | null;
  event_type: string | null;
  location: string | null;
  location_coords: { lat: number; lng: number } | null;
  start_date: string; // ISO 8601
  end_date: string;   // ISO 8601 (required in backend)
  capacity: number | null;
  required_min_aura: number;     // ← NOT "min_aura_score"
  required_languages: string[];  // ← NOT "required_skills"
  status: "draft" | "open" | "closed" | "cancelled" | "completed"; // ← "closed" not "in_progress"
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

// MUST match apps/api/app/schemas/event.py EventCreate exactly
export interface EventCreate {
  title_en: string;              // ← required
  title_az: string;              // ← required
  description_en?: string;
  description_az?: string;
  event_type?: string;
  location?: string;
  location_coords?: { lat: number; lng: number };
  start_date: string;            // ← required (ISO 8601)
  end_date: string;              // ← required (ISO 8601)
  capacity?: number;
  required_min_aura?: number;    // default 0.0
  required_languages?: string[]; // default []
  status?: "draft" | "open";     // default "draft"
  is_public?: boolean;           // default true
}

// MUST match apps/api/app/schemas/organization.py OrganizationResponse exactly
export interface OrganizationResponse {
  id: string;
  owner_id: string;
  name: string;
  description: string | null;
  website_url: string | null;    // ← NOT "website"
  logo_url: string | null;
  contact_email: string | null;  // ← exists in backend
  is_verified: boolean;          // ← NOT "verified"
  subscription_tier: string;     // ← exists in backend
  trust_score: number | null;    // ← exists in backend
  created_at: string;
  updated_at: string;
}

// MUST match apps/api/app/schemas/event.py RegistrationResponse exactly
export interface RegistrationResponse {
  id: string;
  event_id: string;
  volunteer_id: string;
  status: string;
  registered_at: string;         // ← NOT "created_at"
  checked_in_at: string | null;
  check_in_code: string | null;
  coordinator_rating: number | null;
  coordinator_feedback: string | null;
  volunteer_rating: number | null;
  volunteer_feedback: string | null;
}
```

### Step 2: Create TanStack Query Hooks

Create `apps/web/src/hooks/queries/use-events.ts`:
```typescript
// TODO: Replace with @hey-api/openapi-ts generated code after pnpm generate:api
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch, ApiError } from "@/lib/api/client";
import { useAuthToken } from "./use-auth-token";
import type { EventResponse, EventCreate } from "@/lib/api/types";

export function useEvents(status?: string) {
  return useQuery({
    queryKey: ["events", status],
    queryFn: () => apiFetch<EventResponse[]>(
      `/api/events${status ? `?status=${status}` : ""}`
    ),
  });
}

export function useEvent(eventId: string) {
  return useQuery({
    queryKey: ["event", eventId],
    queryFn: () => apiFetch<EventResponse>(`/api/events/${eventId}`),
    enabled: !!eventId,
  });
}

export function useCreateEvent() {
  const getToken = useAuthToken();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: EventCreate) => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<EventResponse>("/api/events", {
        method: "POST",
        body: JSON.stringify(data),
        token,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["events"] });
    },
  });
}
```

Create `apps/web/src/hooks/queries/use-organizations.ts`:
```typescript
// TODO: Replace with @hey-api/openapi-ts generated code after pnpm generate:api
import { useQuery } from "@tanstack/react-query";
import { apiFetch, ApiError } from "@/lib/api/client";
import { useAuthToken } from "./use-auth-token";
import type { OrganizationResponse } from "@/lib/api/types";

export function useOrganizations() {
  return useQuery({
    queryKey: ["organizations"],
    queryFn: () => apiFetch<OrganizationResponse[]>("/api/organizations"),
  });
}

export function useMyOrganization() {
  const getToken = useAuthToken();
  return useQuery({
    queryKey: ["my-organization"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<OrganizationResponse>("/api/organizations/me", { token });
    },
  });
}
```

### Step 3: Event Creation Wizard Page

Create `apps/web/src/app/[locale]/(dashboard)/events/create/page.tsx`:

**⚠️ ROUTE GUARD (from adversarial review):** On mount, call `useMyOrganization()`. If 404 → redirect to `/${locale}/dashboard`. Show loading skeleton during check. Do NOT render the form until org ownership is confirmed.

**⚠️ WIZARD STATE PERSISTENCE (from adversarial review):** Store wizard step data in a Zustand store with `persist` middleware (sessionStorage key: `volaura_event_draft`). Clear store after successful POST. This prevents data loss on browser refresh.

- 3-step wizard with React Hook Form + Zod validation per step
- Step 1: `title_en`, `title_az`, `description_en`, `description_az`, `start_date`, `end_date`, `location`, `capacity`, `event_type`
- Step 2: `required_min_aura` (number input, default 0), `required_languages` (multi-select), auto-invite toggle (visual only — add `// TODO: backend auto-invite endpoint`)
- Step 3: Review all fields (display `title_{locale}` based on current locale), edit buttons per section, "Publish Event" CTA
- Success screen with confetti/animation, share link, "View Event" CTA
- Use Framer Motion `AnimatePresence` for step transitions (duration 0.3s, ease `[0.4, 0, 0.2, 1]`)
- Wire to `POST /api/events` via `useCreateEvent()` mutation
- **Disable "Publish" button** with `isPending` from mutation to prevent double-submit
- All strings via `t()` with both EN + AZ keys
- Wizard step indicator: "Step 1 of 3 — Event Details" (numbered progress)

**Zod schema must validate:**
- `title_en` and `title_az`: required, min 3 chars, max 200 chars
- `start_date` < `end_date` (cross-field validation)
- `capacity`: optional, but if provided must be ≥ 1
- `required_min_aura`: 0-100 range

**Form field labels for AZ:** account for 20-30% longer text. Use `min-w-[120px]` on label containers. Test that "Tələb Olunan Bacarıqlar" and "Maks. Könüllü Sayı" fit.

**Keyboard accessibility (from design:handoff):**
- Tab through all form fields in order
- Enter on "Next" advances step
- Escape on any step returns to previous (or shows "discard draft?" dialog on Step 1)
- Focus ring: `focus-visible:ring-2 ring-primary`

### Step 4: Org Management Dashboard

Create `apps/web/src/app/[locale]/(dashboard)/org/page.tsx`:

**⚠️ ROUTE GUARD:** Same as wizard — `useMyOrganization()` on mount, redirect if no org.

- Stats cards: total events, total volunteers, average AURA score (use `trust_score` from OrganizationResponse)
- My events list with status badges: draft / open / closed / cancelled / completed (NOT "in_progress" — backend uses "closed")
- Quick actions: "Create Event" button → links to `/${locale}/events/create`
- Wire to `GET /api/organizations/me` + `GET /api/events` (filter client-side by `organization_id`)
- **"No org" state:** If user has no organization → show empty state: "You don't have an organization yet." + CTA "Create Organization" (wire to `POST /api/organizations` via mutation)
- **"No events" state:** Org exists but 0 events → "No events yet. Create your first event to start recruiting volunteers." + CTA
- Loading: skeleton cards matching layout shape
- Error: retry CTA with `refetch()`

### Step 5: Org Discovery Page

Create `apps/web/src/app/[locale]/(public)/organizations/page.tsx`:
- Grid of org cards showing: `name`, `description` (truncate to 2 lines), `logo_url` (fallback: initials avatar), `is_verified` badge, `trust_score`, `website_url` link
- Search bar (client-side filter by `name` + `description` for MVP)
- No category filter (backend `OrganizationResponse` has no `category` field — skip this)
- Wire to `GET /api/organizations` (public, no auth)
- Public page — no AuthGuard needed
- Card click → `/${locale}/organizations/${org.id}` (detail page — can be placeholder for now)
- Empty state: "No organizations found. Be the first to register your organization."
- Loading: skeleton grid (3 cards)
- Accessible: org cards are `<article>` with `role="article"`, search input has `aria-label`

### Step 6: Update Navigation

- Add "My Organization" link to Sidebar (conditionally shown if user has org)
- Add "Organizations" link to public nav / footer
- Update i18n keys for nav items

### Step 7: i18n Keys

Add to both `en/common.json` and `az/common.json`:

**Event creation:**
- `events.create.title` — "Create Event" / "Tədbir Yarat"
- `events.create.step1Title` — "Event Details" / "Tədbir Məlumatları"
- `events.create.step2Title` — "Recruitment" / "İşə Qəbul"
- `events.create.step3Title` — "Review & Publish" / "Yoxla və Dərc et"
- `events.create.stepOf` — "Step {{current}} of {{total}}" / "Addım {{current}} / {{total}}"
- `events.create.fieldTitleEn` — "Event Title (English)" / "Tədbir Adı (İngiliscə)"
- `events.create.fieldTitleAz` — "Event Title (Azerbaijani)" / "Tədbir Adı (Azərbaycanca)"
- `events.create.fieldDescriptionEn` — "Description (English)" / "Təsvir (İngiliscə)"
- `events.create.fieldDescriptionAz` — "Description (Azerbaijani)" / "Təsvir (Azərbaycanca)"
- `events.create.fieldEventType` — "Event Type" / "Tədbir Növü"
- `events.create.fieldStartDate` — "Start Date" / "Başlama Tarixi"
- `events.create.fieldEndDate` — "End Date" / "Bitmə Tarixi"
- `events.create.fieldLocation` — "Location" / "Məkan"
- `events.create.fieldCapacity` — "Max Volunteers" / "Maks. Könüllü Sayı"
- `events.create.fieldMinAura` — "Minimum AURA Score" / "Minimum AURA Balı"
- `events.create.fieldLanguages` — "Required Languages" / "Tələb Olunan Dillər"
- `events.create.publish` — "Publish Event" / "Tədbiri Dərc et"
- `events.create.saveAsDraft` — "Save as Draft" / "Qaralama Kimi Saxla"
- `events.create.success` — "Event Published!" / "Tədbir Dərc Edildi!"
- `events.create.successMessage` — "Volunteers can now see and register for your event." / "Könüllülər indi tədbirinizi görə və qeydiyyatdan keçə bilərlər."
- `events.create.next` — "Next" / "Növbəti"
- `events.create.back` — "Back" / "Geri"
- `events.create.publishing` — "Publishing..." / "Dərc edilir..."
- `events.create.errorTitle` — "Event creation failed. Check your connection and try again." / "Tədbir yaradıla bilmədi. Bağlantınızı yoxlayın və yenidən cəhd edin."
- `events.create.errorNoOrg` — "You need an organization to create events." / "Tədbir yaratmaq üçün təşkilatınız olmalıdır."
- `events.create.confirmPublish` — "Publish this event? Volunteers will be able to see and register immediately." / "Bu tədbiri dərc edirsiniz? Könüllülər dərhal görə və qeydiyyatdan keçə biləcəklər."

**Org dashboard:**
- `org.dashboard.title` — "Organization Dashboard" / "Təşkilat İdarəetməsi"
- `org.dashboard.totalEvents` — "Total Events" / "Ümumi Tədbirlər"
- `org.dashboard.totalVolunteers` — "Total Volunteers" / "Ümumi Könüllülər"
- `org.dashboard.avgAura` — "Average AURA" / "Orta AURA"
- `org.dashboard.myEvents` — "My Events" / "Tədbirlərim"
- `org.dashboard.createEvent` — "Create Event" / "Tədbir Yarat"
- `org.dashboard.noEvents` — "No events yet. Create your first event!" / "Hələ tədbir yoxdur. İlk tədbirinizi yaradın!"
- `org.dashboard.noOrg` — "You don't have an organization yet." / "Hələ təşkilatınız yoxdur."

**Org discovery:**
- `org.discovery.title` — "Organizations" / "Təşkilatlar"
- `org.discovery.search` — "Search organizations..." / "Təşkilat axtar..."
- `org.discovery.verified` — "Verified" / "Təsdiqlənmiş"
- `org.discovery.empty` — "No organizations found." / "Təşkilat tapılmadı."

---

## 🔐 Middleware Chain (DO NOT change order)

```
i18nRouter (locale detection) → redirect check → if redirect, return immediately → updateSession() (Supabase auth refresh)
```

New routes to add to protected paths in middleware:
- `/[locale]/events/create` — requires auth (org owner)
- `/[locale]/org` — requires auth (org owner)
- `/[locale]/organizations` — PUBLIC (no auth needed)

---

## 🌐 i18n Specifics

- AZ strings are ~20-30% longer than EN — test that forms don't break
- AZ special chars: ə, ğ, ı, ö, ü, ş, ç — ensure UTF-8 everywhere
- Date format AZ: DD.MM.YYYY (not MM/DD/YYYY)
- Number format AZ: 1.234,56 (dot thousands, comma decimals)
- In date pickers, format dates for display using locale-aware formatting

---

## 🌱 ENV Dependencies

```env
NEXT_PUBLIC_SUPABASE_URL       → Supabase project URL
NEXT_PUBLIC_SUPABASE_ANON_KEY  → Supabase anon key
NEXT_PUBLIC_API_URL            → Backend URL (default: http://localhost:8000)
```

If `NEXT_PUBLIC_API_URL` is missing, `apiFetch` will fail. The client.ts already handles this — just ensure .env.local has it set.

---

## 🔄 AURA Score Reference

**Weights (FINAL — DO NOT CHANGE):**
- communication: 0.20, reliability: 0.15, english_proficiency: 0.15, leadership: 0.15
- event_performance: 0.10, tech_literacy: 0.10, adaptability: 0.10, empathy_safeguarding: 0.05

**Verification multipliers:** self=1.00, org=1.15, peer=1.25

**Badge tiers:** Platinum ≥90, Gold ≥75, Silver ≥60, Bronze ≥40, None <40

---

## ⚠️ Unvalidated Decisions (made without full DSP — challenge if integration reveals problems)

| Decision | Session | Risk if wrong | Action if broken |
|----------|---------|---------------|------------------|
| Event capacity check uses count query (not DB constraint) | 1 | Race condition at high concurrency | Add DB-level check or optimistic locking |
| One org per user (hardcoded limit) | 1 | May need multi-org later | Simple — change condition in `create_organization` |
| Soft-delete events (status=cancelled, not actual DELETE) | 1 | Orphaned data accumulates | Add cleanup job later |
| Auto-invite toggle in event creation | Stitch design | No backend endpoint for auto-invite yet | Skip toggle or make it visual-only with TODO |
| Cover image URL (not file upload) | 1 | Users must host their own images | Add Supabase Storage upload in future session |

---

## 🏁 Verification Checklist (run BEFORE declaring done)

**Core functionality:**
- [ ] Event creation wizard: all 3 steps work, form validation fires, publish calls API
- [ ] Org dashboard: loads org data, shows events list, handles "no org" state
- [ ] Org discovery: loads org list, search works, cards render correctly

**Adversarial mitigations (MUST verify):**
- [ ] Wizard persists data across browser refresh (Zustand + sessionStorage)
- [ ] Non-org-owner visiting /events/create gets redirected (route guard works)
- [ ] "Publish" button disabled during mutation (no double-submit possible)
- [ ] AZ strings fit in form labels without overflow (test "Tələb Olunan Bacarıqlar")
- [ ] Every component has ALL states: loading skeleton + error with retry + empty with CTA

**Design & UX:**
- [ ] All pages use Stitch dark theme (NO light backgrounds, NO borders for sectioning)
- [ ] All strings use `t()` — zero hardcoded text
- [ ] Both EN and AZ json files updated with all new keys
- [ ] CTAs start with verbs: "Publish Event", "Create Event", "Search Organizations"
- [ ] Error messages follow "what + why + how to fix" pattern
- [ ] Empty states follow "what + why + how to start" pattern
- [ ] Confirmation before publish: "Publish this event?" with consequence text

**Technical:**
- [ ] INTERIM types match real Pydantic schemas (title_en/title_az, NOT title)
- [ ] TanStack Query hooks have proper error states + loading skeletons
- [ ] `isMounted` ref on any component with async state
- [ ] Absolute locale-aware routing everywhere (`/${locale}/path`)
- [ ] New nav items added to Sidebar (conditionally for org pages)
- [ ] No TypeScript `any` types
- [ ] Framer Motion animations on page/step transitions (0.3s, ease [0.4,0,0.2,1])
- [ ] Focus ring on all interactive elements (`focus-visible:ring-2 ring-primary`)
- [ ] Tab order correct in wizard form
- [ ] `next dev` compiles without errors
- [ ] engineering:code-review completed

---

## 🧭 Session 13 Done → What's Next

After Session 13, remaining unbuilt Stitch pages:

| Page | Priority | Session |
|------|----------|---------|
| Messaging/Chat | Medium | 14-15 (needs backend WebSocket/Supabase Realtime) |
| Rewards/Perks | Medium | 14-15 |
| Volunteer Quests | Medium | 14-15 |
| Impact Reports | Low | 16+ |
| Org Settings + 2FA | Low | 16+ |
| Talent Matching UI | High | 14 (backend search endpoint exists) |

**Recommendation for Session 14:** Talent Matching UI (high impact, backend ready) + Deploy to Vercel (Stage 1 — frontend preview).

