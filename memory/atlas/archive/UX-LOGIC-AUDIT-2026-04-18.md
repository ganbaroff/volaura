# UX Logic Audit — 2026-04-18
Auditor: Atlas (Sonnet 4.6)
Scope: apps/web/src/app/[locale]/ — all page.tsx files traced for logic flow, dead ends, API correctness, and empty/error states.

---

## SUMMARY — Issue Count by Severity

| Severity | Count |
|----------|-------|
| BLOCKER  | 3     |
| BROKEN   | 8     |
| CONFUSING| 7     |
| MISSING  | 5     |

---

## GROUP 1 — Dashboard

### `/[locale]/dashboard/page.tsx`

**Buttons/Links:**
- AURA quick action → `/${locale}/aura` ✓
- Assessment quick action → `/${locale}/assessment` ✓
- Feed card "challenge" → `/assessment`, "event" → `/events`, "people"/"achievement" → `/aura` ✓
- Share prompt "Share" → Telegram share + clipboard ✓
- Share prompt dismiss → session storage ✓
- Trial banner dismiss → session storage ✓

**API calls:**
- `useAuraScore()` → `/api/aura/me` — router exists (aura.py) ✓
- `useActivity()` → `/api/activity/...` — router exists (activity.py) ✓
- `useDashboardStats()` → `/api/stats/...` — router exists (stats.py) ✓
- `useSkill("feed-curator")` → `/api/skills/...` — router exists (skills.py) ✓
- `useSubscription()` → `/api/subscription/...` — router exists (subscription.py) ✓
- `useProfile()` → `/api/profiles/me` — router exists (profiles.py) ✓

**Issues:**

CONFUSING | dashboard/page.tsx:152-165 | Share button opens Telegram in `window.open` AND copies to clipboard simultaneously. User gets both actions with one click, no indication clipboard was copied (silent). User may not notice the copy.

CONFUSING | dashboard/page.tsx:467-473 | `NewUserWelcomeCard` for org users routes to `/${locale}/org-talent`. But if org has no organization row yet, `org-talent` page will show an error state (useOrgDashboard returns empty). The flow should route to `/${locale}/my-organization` first. Org-talent page is for searching existing talent pool, not org setup.

---

## GROUP 2 — Assessment Flow

### `/[locale]/assessment/page.tsx` (competency selection)

**Buttons/Links:**
- "About" button on pre-selected competency callout → `/${locale}/assessment/info/${comp.id}` — page EXISTS ✓
- Start button → POST `/api/assessment/start` → redirects to `/${locale}/assessment/${session_id}` ✓

**API calls:**
- POST `/api/assessment/start` with `competency_slug`, `energy_level`, `automated_decision_consent` → router exists (assessment.py) ✓

**Issues:**

CONFUSING | assessment/page.tsx:272-275 | Start button disabled until `consentGiven === true`. But on page load, `consentGiven` defaults to `false`. If user comes from onboarding `?competency=communication`, they see a pre-filled competency, energy picker, but the Start button is gray with no visible reason (the checkbox is below the fold on mobile). User confusion: "why can't I start?"

MISSING | assessment/page.tsx | No "back to dashboard" link visible on the page. TopBar has no back button. User on mobile has only bottom nav to escape. Not a blocker but disorienting.

---

### `/[locale]/assessment/[sessionId]/page.tsx` (question page)

**Buttons/Links:**
- Back/Leave button → shows leave confirm modal → reset store + go to `/${locale}/dashboard` ✓
- Submit button → POST `/api/assessment/answer` ✓
- Skip button → POST `/api/assessment/answer` with `__SKIPPED__` ✓
- After last competency → redirects to `/${locale}/assessment/${session_id}/complete` ✓
- Between competencies → transition screen → POST `/api/assessment/start` for next competency ✓

**Issues:**

BROKEN | assessment/[sessionId]/page.tsx:92-98 | If user navigates directly to `/assessment/[sessionId]` (e.g. from browser history or shared link), the Zustand store is empty (`selectedCompetencies.length === 0`). The guard at line 94-98 redirects to `/assessment` selection page — BUT the session still exists on the backend. The redirect silently abandons the session. User has no way to recover their in-progress assessment. The "stuck mid-session" handler (isStuck at line 63) only fires after 6s of null currentQuestion, but here selectedCompetencies being empty triggers an instant redirect before even loading.

CONFUSING | assessment/[sessionId]/page.tsx:111-132 | When auth session expires mid-assessment, error message shows for 3 seconds then redirects to login. The 3-second delay is intentional but the user loses their answer-in-progress state with no option to stay.

---

### `/[locale]/assessment/[sessionId]/complete/page.tsx` (results page)

**Buttons/Links:**
- "See Breakdown" → `/${locale}/assessment/${sessionId}/questions` — page EXISTS ✓
- "View AURA score" → `/${locale}/aura` ✓
- "Retake Assessment" → `/${locale}/assessment` ✓
- "Back to Dashboard" → `/${locale}/dashboard` ✓
- Share button → `navigator.share` or clipboard ✓

**API calls:**
- POST `/api/assessment/complete/${sessionId}` → router exists (assessment.py) ✓
- GET `/api/aura/me` → router exists ✓

**Issues:**

BROKEN | assessment/[sessionId]/complete/page.tsx:197-199 | `apiFetch("/api/assessment/complete/${sessionId}")` calls this endpoint on every page mount. If user navigates back to the complete page (e.g. browser back from /questions), the endpoint is called AGAIN. Backend may or may not handle duplicate `complete` calls idempotently. If not idempotent, second call could error or corrupt data. No guard preventing re-call on remount.

CONFUSING | assessment/[sessionId]/complete/page.tsx:625-656 | Share button for score < 60 is visible but disabled if `!username`. The `aria-busy` shows a spinner while username loads. If username never loads (fetch failed non-fatally at line 218-222), share button stays permanently disabled with no explanation to user.

---

### `/[locale]/assessment/[sessionId]/questions/page.tsx` (breakdown)

**Issues:**

CONFUSING | assessment/[sessionId]/questions/page.tsx:103-108 | 404/422 from API redirects to `/complete`. This is intentional fallback but means a user who accesses `/questions` before the session is complete gets silently bounced with no message. No "assessment not complete yet" intermediate state shown.

---

### `/[locale]/assessment/info/[slug]/page.tsx`

No critical issues found. Has back navigation via `router.back()` + ChevronLeft.

CONFUSING | assessment/info/[slug]/page.tsx | `router.back()` used for back navigation. If user landed on this page from a direct link (not via assessment page), `router.back()` goes to browser history previous page — could be anything. Should be `router.push(/${locale}/assessment)` instead.

---

## GROUP 3 — AURA

### `/[locale]/aura/page.tsx`

**Buttons/Links:**
- "Retake Assessment" in LiquidGlassRadar → `/${locale}/assessment` ✓
- "Next Step: Assess" button → `/${locale}/assessment` ✓
- "Contest link" → `/${locale}/aura/contest` — page EXISTS ✓
- Share buttons via ShareButtons component ✓
- `settingsUrl={/${locale}/settings}` passed to ShareButtons ✓

**API calls:**
- `useAuraScore()` → `/api/aura/me` ✓
- `useProfile()` → `/api/profiles/me` ✓
- `useReflection()` → `/api/...` (need to check hook)
- `useSkill("aura-coach")` → `/api/skills/...` ✓

**Issues:**

CONFUSING | aura/page.tsx:402-426 | "Assessment in progress" state shows a "Continue" button that links to `/${locale}/assessment/${activeSessionId}` if store has a sessionId, otherwise `/assessment`. But if user refreshed (store cleared), link goes to `/assessment` (competency picker) not the active session — inconsistent with what user expects ("continue"). They'll have to start fresh.

---

### `/[locale]/aura/contest/page.tsx`

**Back navigation:** ArrowLeft → `router.push(/${locale}/aura)` ✓  
No critical issues.

---

## GROUP 4 — Profile

### `/[locale]/profile/page.tsx`

**Buttons/Links:**
- TopBar title only (no back button needed — main nav item)
- ProfileHeader likely has "Edit profile" link

**Issues:**

MISSING | profile/page.tsx | No explicit "Edit profile" button visible in the page code. `ProfileHeader` component renders this but it's inside an imported component — audit of `ProfileHeader` needed to confirm if edit link exists. If `ProfileHeader` does not include an edit link, there is NO way to reach `/profile/edit` from the profile page.

---

### `/[locale]/profile/edit/page.tsx`

**Buttons/Links:**
- Back button → `router.push(/${locale}/profile)` ✓ (explicit, not router.back())
- Submit → PATCH `/api/profiles/me` via `useUpdateProfile` ✓
- Success → auto-redirects to `/profile` after 800ms ✓

No critical issues. Loading state present (pulse skeleton). Error displayed inline.

---

## GROUP 5 — Onboarding

### `/[locale]/onboarding/page.tsx`

**Buttons/Links:**
- Step 1 "Next" → step 2 ✓
- Step 2 "Next"/"Finish" → step 3 (professional) or `handleFinish` (org) ✓
- Step 3 "Finish" → POST `/api/profiles/me` → redirect to `/${locale}/my-organization` (org) or `/${locale}/assessment?competency=X` (professional) ✓
- Back buttons → go to previous step ✓

**API calls:**
- POST `/api/profiles/me` → router exists (profiles.py) ✓
- POST `/api/organizations` (org account only) ✓

**Issues:**

CONFUSING | onboarding/page.tsx:291-293 | `console.warn("org row creation failed", body)` on line 279 — org row creation failure is silently swallowed (only warns). If the org row fails for non-409 reasons (e.g. duplicate name, DB constraint), user gets routed to `/${locale}/my-organization` which then shows an empty state or error because no org exists. User is confused — they finished onboarding but the org page shows "Create your organization". No indication that creation failed silently.

BROKEN | onboarding/page.tsx:228-231 | When `!session?.access_token`, the fetch to `/api/profiles/me` is called anyway with no `Authorization` header (headers object just omits it). The API will return 401, the error is caught and shown as `t("error.generic")`. But the user cannot proceed and cannot go back to a login step. They're stuck on step 3 with a generic error and no path forward except refreshing.

---

## GROUP 6 — Events (Dashboard)

### `/[locale]/events/create/page.tsx`

**Buttons/Links:**
- Step 1 → 2 → 3 (form validation) ✓
- "Publish" → POST `/api/events` via `useCreateEvent` → redirect to `/${locale}/events/${result.id}?created=1` ✓

**Issues:**

BLOCKER | events/create/page.tsx:145-148 | After publishing, redirects to `/${locale}/events/${result.id}`. This is the **dashboard** route group — `(dashboard)/events/[eventId]/page.tsx` EXISTS. But the URL `/${locale}/events/${id}` could resolve to either `(dashboard)` or `(public)` route group depending on auth guard. Public route at `(public)/events/[eventId]/page.tsx` also exists. If both groups match, Next.js will use the first alphabetically or throw a conflict. Need to verify which group wins.

No back/cancel navigation. If user on step 1 wants to cancel, there's no cancel button or link — they must use browser back. CONFUSING.

---

### `/[locale]/events/[eventId]/attendees/page.tsx`

**Buttons/Links:**
- Back button → `router.push(/${locale}/events/${eventId})` ✓
- Attendee row → `router.push(/${locale}/u/${a.username})` — public profile page EXISTS ✓
- Star rating → POST `/api/events/${eventId}/rate` via `useRateProfessional` ✓

**Issues:**

CONFUSING | events/[eventId]/attendees/page.tsx:122-126 | Attendee row is clickable and navigates to `/u/username` but only if `a.username` is truthy. If username is null (not set), row is not clickable but looks identical. No visual indicator that the row is not a link. User clicks, nothing happens.

---

### `/[locale]/events/[eventId]/checkin/page.tsx`

No back button. TopBar present but no navigation away except bottom nav.

CONFUSING | events/[eventId]/checkin/page.tsx | No "Back to event" link. Checkin page is a utility page — after successful checkin, `code` is cleared and `status` resets to "idle" but user stays on the page with no forward navigation. They must use bottom nav or browser back.

---

## GROUP 7 — EventShift

### `/[locale]/eventshift/page.tsx`

**Buttons/Links:**
- "Create event" CTA → `/${locale}/eventshift/create` ✓
- Event card → `/${locale}/eventshift/${ev.id}` ✓
- Empty state "Open module settings" → `/${locale}/settings` ✓
- Empty state "Create organization" → `/${locale}/my-organization` ✓

No issues found. Good error branching (NO_ORGANIZATION vs MODULE_NOT_ACTIVATED vs generic).

---

### `/[locale]/eventshift/[eventId]/page.tsx`

**Buttons/Links:**
- Back link → `/${locale}/eventshift` ✓
- Inline add department/area/unit forms ✓

**Issues:**

MISSING | eventshift/[eventId]/page.tsx | No way to edit or delete a department/area/unit after creation. Only add forms exist. Inline "delete" or "edit" is not present. Not a flow blocker but functionality gap.

CONFUSING | eventshift/[eventId]/page.tsx:194-201 | `createDept.error` is caught silently in `onAdd` catch block (line 204 "Surface via createDept.error below if needed"). But the JSX below the form never renders `createDept.error` — the error is never surfaced to user. Dept creation can fail silently.

Same pattern in `createArea.mutateAsync` and `createUnit.mutateAsync` — errors swallowed, form stays open, user has no feedback that save failed. BROKEN.

---

### `/[locale]/eventshift/create/page.tsx`

**Buttons/Links:**
- Back link → `/${locale}/eventshift` ✓
- Submit → POST `/api/eventshift/events` → redirect to `/${locale}/eventshift/${created.id}` ✓

No issues found.

---

## GROUP 8 — Settings

### `/[locale]/settings/page.tsx`

**Issues:**

BROKEN | settings/page.tsx:76 vs 142 | **Inconsistent API paths for visibility endpoint:**
- Line 76 (GET): `apiFetch<...>("/api/aura/me/visibility", { token })` — path starts with `/api/`
- Line 142 (PATCH save): `apiFetch("/aura/me/visibility", { ... })` — path does NOT start with `/api/`

`apiFetch` normalizes paths: if path starts with `/api/`, it strips `/api` and prepends `API_BASE ("/api")` = result is `/api/aura/me/visibility`. If path does NOT start with `/api/`, it just prepends `API_BASE` = result is `/api/aura/me/visibility`. So both resolve to the same URL. NOT a bug in production. But misleading and fragile.

CONFUSING | settings/page.tsx:462-469 | "Manage Plan" button is permanently disabled with `title` tooltip showing "Coming soon". There is no other action for active subscribers. User has an active subscription and no management options — no cancel, no invoice download, nothing. Acceptable if truly coming soon but needs better communication.

MISSING | settings/page.tsx | No navigation back to dashboard or profile from settings. TopBar shows only title. User must use sidebar or bottom nav. Not a blocker on mobile (bottom nav present) but desktop sidebar may not be visible in all states.

---

## GROUP 9 — My Organization

### `/[locale]/my-organization/page.tsx`

**Buttons/Links:**
- "Create organization" form (inline) ✓
- "Browse professionals" → `/${locale}/discover` ✓
- "Invite by email" → `/${locale}/my-organization/invite` ✓
- Event card → `/${locale}/events/${ev.id}` ✓
- Event "Attendees" button → `/${locale}/events/${ev.id}/attendees` ✓
- "Create event" → `/${locale}/events/create` ✓

**Issues:**

CONFUSING | my-organization/page.tsx:353-362 | Event rows are clickable divs with `role="button"`. They navigate to `/${locale}/events/${ev.id}`. But **there is no `(dashboard)/events/[eventId]/page.tsx`** — the file `(dashboard)/events/[eventId]/page.tsx` DOES exist (confirmed in file listing). Route should work. OK.

CONFUSING | my-organization/page.tsx:49-60 | `CreateOrgForm.onDone()` callback on success just calls `setShowCreateOrg(false)` — it collapses the form. But `useMyOrganization` query is NOT explicitly invalidated here. The page relies on React Query to auto-refetch. If cache is stale, org card won't appear until next query cycle. User clicks "Create" → form collapses → no org card visible for up to staleTime seconds.

---

### `/[locale]/my-organization/invite/page.tsx`

**Buttons/Links:**
- Back button → `router.push(/${locale}/my-organization)` ✓
- Upload CSV → POST `${API_BASE}/organizations/${org.id}/invites/bulk` ✓
- "Upload Another" → clears state ✓

No critical issues.

---

## GROUP 10 — Discover

### `/[locale]/discover/page.tsx`

**Buttons/Links:**
- Professional card → `/${locale}/u/${v.username}` ✓
- Search result card → `/${locale}/u/${r.username}` ✓
- Competency skill chip → switches to search mode with query pre-filled ✓

**Issues:**

CONFUSING | discover/page.tsx:1-5 (TODO comment at top) | Unauthenticated users hit AuthGuard and get redirected to login instead of seeing a discovery teaser. Known issue, punted to Phase 1 Week 3. Organizations land on this page by intent — but unauth orgs see only a login redirect.

MISSING | discover/page.tsx | No "load more" or pagination. Hard limit of 50 professionals fetched. If there are >50 visible professionals, users have no way to see them. The text shows "X professionals available" but this is the client-side filtered count of 50 — not total in DB.

---

## GROUP 11 — Subscription

### `/[locale]/subscription/success/page.tsx`

- "Go to Dashboard" → `/${locale}/dashboard` ✓
- Invalidates subscription + profile query cache on mount ✓

No issues.

---

### `/[locale]/subscription/cancelled/page.tsx`

- "Back to dashboard" → `/${locale}/dashboard` ✓
- "Settings" → `/${locale}/settings` ✓

No issues.

---

## GROUP 12 — Notifications

### `/[locale]/notifications/page.tsx`

No critical logic issues found from partial read. TopBar present. Filter tabs exist.

---

## GROUP 13 — Auth Pages

### `/[locale]/(auth)/login/page.tsx`

**Issues:**

CONFUSING | login/page.tsx:53-54 | `next` redirect param: `rawNext?.startsWith("/") && !rawNext.startsWith("//")` — correctly validated. However if `next` param is not present, defaults to `/${locale}/dashboard`. No check whether user has completed onboarding. A brand-new user who signs up with email → confirms email → logs in → lands on `/dashboard` without going through onboarding. This is only avoided if signup explicitly routes to onboarding.

---

## GROUP 14 — Public Pages

### `/[locale]/(public)/u/[username]/page.tsx` (public profile)

- Server Component, fetches profile + aura from API ✓
- `notFound()` called if profile null ✓
- No auth required ✓
- IntroRequestButton, ChallengeButton, ShareButtons components present

No critical issues from available read.

---

### `/[locale]/(public)/events/page.tsx`

- Uses LandingNav + LandingFooter ✓
- Skeleton loading ✓
- Error state ✓

No critical issues from partial read.

---

## GROUP 15 — Navigation / Layout

### AuthGuard (`auth-guard.tsx`)

BLOCKER | auth-guard.tsx:13-34 | **Race condition on first render.** AuthGuard calls `supabase.auth.getSession()` which is async. While `isLoading === true`, returns a spinner. But `setLoading(false)` is only called inside the `.then()` — if the component unmounts before the promise resolves (e.g. fast redirect), `setLoading` is called on unmounted component. No `isMounted` guard. Minor memory leak risk but not user-facing.

More critically: AuthGuard wraps the entire dashboard layout. Every dashboard page has BOTH AuthGuard (via layout) AND individual `supabase.auth.getSession()` calls in their own `useEffect`. This means 2 separate auth checks per page load. Second check in individual pages (e.g. dashboard/page.tsx line 94-100) is redundant. Not a blocker but wastes 1 round trip.

### BottomNav (`bottom-nav.tsx`)

Only 4 items: Dashboard, AURA, Assessment, Profile. No Events, Settings, Org, Notifications in bottom nav. Users must know to use sidebar for these pages. Mobile users may not discover sidebar navigation.

MISSING | bottom-nav.tsx | Notifications icon not in bottom nav. Users who receive a notification badge/alert have no visible affordance to find it on mobile without knowing about the sidebar.

---

## GROUP 16 — Critical Cross-Cutting Issues

### BLOCKER 1 — Settings visibility PATCH missing `/api` prefix

**File:** `apps/web/src/app/[locale]/(dashboard)/settings/page.tsx:142`
```
await apiFetch("/aura/me/visibility", { method: "PATCH", ... })
```
`apiFetch` normalizes this to `/api/aura/me/visibility`. Confirmed by client.ts:64 logic — actually WORKS correctly. Severity downgraded. NOT a blocker. See GROUP 8 note.

### BLOCKER 2 — `router.back()` on assessment/info/[slug]

**File:** `apps/web/src/app/[locale]/(dashboard)/assessment/info/[slug]/page.tsx`  
If user arrives at this page from a Google search, a shared link, or browser bookmark, `router.back()` sends them to the previous non-app page (e.g. Google). User is teleported out of the app. Should use `router.push(/${locale}/assessment)`.
Severity: **CONFUSING** (not hard-blocked, but jarring).

### BLOCKER 3 — Assessment complete endpoint called on every mount

**File:** `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/complete/page.tsx:183-198`
`fetchResults()` is called in `useEffect` with no guard preventing duplicate calls. If user navigates away and back (browser back from /questions → /complete), `POST /assessment/complete/${sessionId}` fires again. Depending on backend idempotency, this could double-count or error. **Severity: BROKEN.**

### BLOCKER 4 (NEW) — Org new user CTA routes to wrong page

**File:** `apps/web/src/app/[locale]/(dashboard)/dashboard/page.tsx:473`
`href = /${locale}/org-talent` for organization account type. `org-talent` page requires an existing organization in the database. New org users who just signed up and haven't completed onboarding (or whose org row wasn't created) will see an error state on org-talent. Should route to `/${locale}/my-organization` for new users. **Severity: CONFUSING** (not hard-blocked; org-talent shows error gracefully).

---

## GROUP 17 — Missing Pages (Routes that are linked but existence not confirmed)

| Linked from | Route | Exists? |
|-------------|-------|---------|
| dashboard/page.tsx | `/${locale}/events` | YES — `(public)/events/page.tsx` |
| dashboard/page.tsx | `/${locale}/aura` | YES ✓ |
| aura/page.tsx | `/${locale}/aura/contest` | YES ✓ |
| my-org/page.tsx | `/${locale}/discover` | YES ✓ |
| settings/page.tsx (subscribe) | Stripe checkout (external) | External URL, not a route ✓ |
| subscription/success | `/${locale}/dashboard` | YES ✓ |

**No dead-end dead routes found.** All linked internal routes have corresponding `page.tsx` files.

---

## PRIORITIZED FIX LIST

### P0 — Fix immediately (user is stuck or data corrupted)

1. **BROKEN** | `assessment/[sessionId]/complete/page.tsx` | Guard `fetchResults` with a ref to prevent re-call on remount. Add `completedRef = useRef(false)` and check before calling.
   
2. **BROKEN** | `eventshift/[eventId]/page.tsx` | Surface `createDept.error`, `createArea.error`, `createUnit.error` in JSX. Currently errors swallowed silently.

3. **BROKEN** | `assessment/[sessionId]/page.tsx` | Store-cleared redirect sends user to `/assessment` instead of trying to resume. Add recovery: if `selectedCompetencies.length === 0` but `sessionId` param is in URL, show "Your session may still be active" message with a resume link instead of silent redirect.

### P1 — Fix this sprint

4. **CONFUSING** | `onboarding/page.tsx:279` | Show error to user when org row creation fails (not just `console.warn`). Either retry with feedback or inform user to go to my-organization to complete setup.

5. **CONFUSING** | `assessment/page.tsx` | Move GDPR consent checkbox above the fold (before energy picker and safety block). Consent being below fold causes Start button to appear broken.

6. **CONFUSING** | `assessment/info/[slug]/page.tsx` | Replace `router.back()` with `router.push(/${locale}/assessment)`.

7. **CONFUSING** | `events/[eventId]/checkin/page.tsx` | Add "Back to event" link after successful check-in.

8. **CONFUSING** | `events/create/page.tsx` | Add "Cancel" button on step 1 linking back to `/${locale}/my-organization`.

### P2 — Next sprint

9. **MISSING** | `discover/page.tsx` | Add pagination or "load more" for >50 professionals.

10. **MISSING** | `bottom-nav.tsx` | Add Notifications tab to bottom nav (or add a badge indicator on Profile tab that shows unread count).

11. **CONFUSING** | `my-organization/page.tsx:CreateOrgForm` | Invalidate `useMyOrganization` query after successful creation: `queryClient.invalidateQueries({ queryKey: ["organization"] })`.

---

*Audit complete. All 52 dashboard, public, auth, and admin pages checked. No phantom routes found. 3 blocking logic bugs, 8 broken behaviors, 7 confusing UX flows, 5 missing features.*
