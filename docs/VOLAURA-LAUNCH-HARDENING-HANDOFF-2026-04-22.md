# VOLAURA Launch Hardening Handoff — 2026-04-22

## Purpose

This document is a continuity memo for the current VOLAURA hardening push.

It records:

- what was changed in the current Atlas hardening pass,
- what was verified vs not verified,
- what is still broken or risky,
- and the exact next sequence required to make VOLAURA operate "like clockwork".

This memo is intentionally operational, not visionary.

---

## Executive summary

Main conclusion:

- VOLAURA does **not** need a rewrite from scratch.
- The product core is real and worth preserving.
- The biggest remaining problem is not "missing features", but reliability seams:
  - launch-critical flow durability,
  - privacy/settings state safety,
  - auth/error consistency,
  - and insufficient PR gates around the `assessment -> AURA -> compliance` path.

This pass improved the system materially in exactly those areas.

The highest-value remaining work is:

1. finish remaining auth/error contract cleanup outside the newly normalized `profile/aura/dashboard/events/organizations` hooks,
2. turn CI/hard gates into a real pre-merge blocker,
3. verify the new assessment completion repair lane in stable CI/runtime,
4. review remaining settings-like and onboarding-adjacent forms for silent state overwrite risk,
5. rerun the updated assessment integrity tests in stable CI or a clean local runtime.

---

## Scope note

This repo already had a dirty worktree before this pass.

Some hardening work had already been added in the current branch/thread before this memo was written.
This document records the combined state I verified and the concrete changes I made in this Atlas pass.

I did **not** touch MindShift in this pass.
Focus stayed on `VOLAURA core`.

---

## What was changed in this hardening pass

## 1. Assessment compliance logging was hardened

File:

- `apps/api/app/routers/assessment.py`
- `apps/api/tests/test_assessment_router.py`

Change:

- Core assessment completion now writes an `automated_decision_log` row for the main VOLAURA assessment path.
- This closes a major gap where human review / Art.22 existed around the edges, but core assessment completion itself did not reliably leave a contestable decision trail.

Why it matters:

- Human review is not serious if the core automated decision path does not leave an auditable record.

Current limitation:

- Logging is still best-effort / log-and-swallow, not yet a durable outbox or retried completion job.

---

## 2. Events "my" endpoints were untangled and de-shadowed

Files:

- `apps/api/app/schemas/event.py`
- `apps/api/app/routers/events.py`
- `apps/api/tests/test_events_endpoints.py`
- `apps/web/src/hooks/queries/use-events.ts`
- `apps/web/src/hooks/__tests__/use-events.test.ts`
- `apps/web/src/app/[locale]/(dashboard)/profile/page.tsx`
- `apps/web/src/app/[locale]/(dashboard)/my-organization/page.tsx`

Change:

- Added clearer backend surfaces:
  - `/api/events/my/timeline`
  - `/api/events/my/owned`
  - `/api/events/my/registrations`
- Fixed route ordering so static `/my/...` routes are no longer shadowed by dynamic `/{event_id}/...`.
- Split frontend logic so profile timeline and organization-owned events no longer pretend to be the same dataset.

Why it matters:

- One ambiguous `/events/my` hook was serving two different business meanings.
- That creates silent UI drift and incorrect dashboards.

---

## 3. E2E full journey was tightened

Files:

- `tests/e2e/full-journey.spec.ts`
- `.github/workflows/e2e.yml`

Change:

- Corrected the API host to `https://modest-happiness-production.up.railway.app`.
- Tightened the compliance section so it now requires:
  - export endpoint success,
  - at least one human-reviewable decision,
  - creation of a formal human review request.

Why it matters:

- A smoke test that does not hit real compliance loops gives false confidence.

Current limitation:

- This E2E workflow still runs on push only, not as a real PR blocker.

---

## 4. Assessment resume flow was fixed

Files:

- `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/page.tsx`
- `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/resume.test.tsx`

Change:

- Fixed the resume fetch path from `/api/api/assessment/session/:id` to `/api/assessment/session/:id`.
- Added a regression test to ensure the double-prefix bug does not come back.

Why it matters:

- This was a real P0 dead-end.
- A user mid-assessment could refresh and lose the recovery path even when the backend session still existed.

---

## 5. Public invite flow was brought back onto the same API truth layer

File:

- `apps/web/src/app/[locale]/(public)/invite/page.tsx`

Change:

- Replaced a hardcoded fallback to the obsolete Railway host with the shared relative web API base.
- The invite page now uses the same `/api` truth layer as the rest of the app.

Why it matters:

- Public beta funnel drift is dangerous because it fails quietly.
- A single stale absolute host can break invites while the rest of the app appears healthy.

---

## 6. Prod health probe was corrected

File:

- `.github/workflows/prod-health-check.yml`

Change:

- Updated the API health target to `https://modest-happiness-production.up.railway.app/health`.

Why it matters:

- Monitoring that points to the wrong backend produces fake alerts or misses real failures.

---

## 7. Settings page was made fail-safe instead of optimistic

Files:

- `apps/web/src/app/[locale]/(dashboard)/settings/page.tsx`
- `apps/web/src/lib/api/types.ts`
- `apps/web/src/lib/api/types.test.ts`

Change:

- Added `visible_to_orgs` to the stable `Profile` mapper.
- Stopped settings from defaulting privacy state to a writable value before the real state is loaded.
- Stopped org-discovery visibility from seeding as `false` just because the mapper dropped the field.
- Disabled saving when required state has not been loaded.
- Showed load errors instead of rendering editable controls on unknown state.

Why it matters:

- This was one of the most dangerous silent-corruption screens.
- The old behavior could accidentally overwrite:
  - AURA visibility,
  - org-discovery visibility,
  - and profile state
  simply because the initial UI loaded with false/public defaults.

Important note:

- This fix was applied to `settings`.
- A similar seeding/style review was still needed for `profile/edit` and is now partially closed by the dedicated edit-page hardening below.

---

## 8. PR gates were made more honest

Files:

- `.github/workflows/ci.yml`
- `.github/workflows/ecosystem-hard-gates.yml`

Change:

- Removed broken PR `if:` filters from `ci.yml` that referenced `github.event.pull_request.changed_files.*.filename`.
- Expanded hard-gates coverage toward launch-critical tests:
  - auth,
  - grievance,
  - assessment router,
  - events endpoints,
  - grievance hook tests,
  - event hook tests,
  - API type mapping tests,
  - assessment resume regression test.

Why it matters:

- A broken smart-filter is worse than no filter because the team thinks PRs are protected when they are not.

Important note:

- `ecosystem-hard-gates.yml` was already present in the working tree context of this effort and was strengthened here.

---

## 9. Multi-competency assessment integrity was repaired end-to-end

Files:

- `apps/api/app/schemas/assessment.py`
- `apps/api/app/services/assessment/helpers.py`
- `apps/api/app/routers/assessment.py`
- `apps/api/tests/test_assessment_router_pipeline.py`
- `apps/web/src/stores/assessment-store.ts`
- `apps/web/src/stores/assessment-store.test.ts`
- `apps/web/src/app/[locale]/(dashboard)/assessment/page.tsx`
- `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/page.tsx`
- `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/resume.test.tsx`
- `tests/e2e/full-journey.spec.ts`

Change:

- Added explicit multi-competency plan fields to assessment start requests:
  - `assessment_plan_competencies`
  - `assessment_plan_current_index`
- Persisted that plan in `assessment_sessions.metadata`.
- Extended `GET /api/assessment/session/{session_id}` so it now returns:
  - the active question,
  - the full competency plan,
  - the current plan index,
  - and a logical `completed` state for stopped sessions that are already transition-ready.
- Added a reusable `restoreProgress(...)` action in the assessment Zustand store.
- Changed the assessment question page so each completed competency now runs:
  1. `POST /api/assessment/complete/{session_id}`
  2. then transition to next competency or final results
- Fixed next-competency start requests to carry consent plus the same assessment plan metadata.
- Fixed resume recovery so it restores the full plan instead of collapsing to `[current competency only]`.
- Added regression coverage for:
  - store rehydration,
  - backend resume payload plan recovery,
  - resume `next_question`,
  - and mid-plan completed sessions reopening as transition-ready.
- Strengthened the API journey smoke so it now also asserts:
  - multi-competency plan persistence,
  - transition-boundary resume semantics,
  - and option-answering via the real `key` contract instead of a phantom `id`.

Why it matters:

- Before this pass, the multi-competency path had several integrity breaks:
  - next competency start could lose consent,
  - refresh/storage loss could collapse the plan,
  - intermediate competencies could stop without reliably executing `/complete`,
  - and full local-state loss could not honestly reconstruct the active question.
- This was exactly the kind of seam that makes a product feel "mostly working" while quietly damaging trust.

Important note:

- The client-side integrity gap for the multi-competency journey is materially reduced.
- The biggest remaining risk is now behind the backend side effects of `/complete`, not the transition/resume contract itself.

---

## 10. Launch-critical auth/error semantics were normalized in web hooks

Files:

- `apps/web/src/lib/api/client.ts`
- `apps/web/src/hooks/queries/use-profile.ts`
- `apps/web/src/hooks/queries/use-aura.ts`
- `apps/web/src/hooks/queries/use-dashboard.ts`
- `apps/web/src/hooks/__tests__/use-profile.test.ts`
- `apps/web/src/hooks/__tests__/use-aura.test.ts`
- `apps/web/src/hooks/__tests__/use-dashboard.test.ts`

Change:

- Added `toApiError(...)` to normalize generated SDK errors into the same `ApiError` contract used by manual `apiFetch`.
- Converted launch-critical generated-SDK hooks to preserve HTTP semantics instead of collapsing to generic `Error("Failed to fetch ...")`.
- Updated tests so they now assert preserved status/code in these paths:
  - `401 UNAUTHORIZED`
  - `403 FORBIDDEN`
  - `AURA_NOT_FOUND` still maps to `null`, not an error state.

Why it matters:

- This removes one of the most damaging kinds of frontend ambiguity:
  - auth expiry looking like a generic load failure,
  - permission failures losing their code/status,
  - pages/hook consumers being unable to distinguish `401`, `403`, `404`, and real server faults.

Important note:

- This is not the end of auth/error cleanup across the whole app.
- It does cover the highest-value launch surfaces called out in the audit:
  - profile,
  - aura,
  - dashboard.

---

## 11. Assessment completion now has a durable side-effect control plane

Files:

- `apps/api/app/services/assessment/completion_jobs.py`
- `apps/api/app/routers/assessment.py`
- `apps/api/tests/test_assessment_router.py`
- `supabase/migrations/20260423090000_create_assessment_completion_jobs.sql`

Change:

- Added a durable `assessment_completion_jobs` registry for `/api/assessment/complete`.
- `complete_assessment` no longer treats `status='completed'` as automatic "nothing left to do" when a completion job exists but still has pending or failed side effects.
- Completion now snapshots result context and tracks step-by-step state for:
  - `aura_sync`
  - `rewards`
  - `streak`
  - `analytics`
  - `email`
  - `ecosystem_events`
  - `aura_events`
  - `decision_log`
- Added regression coverage for:
  - first completion creating/processing a durable job
  - replaying `/complete` for a completed session with an incomplete job and resuming the missing work

Why it matters:

- This closes the highest-risk remaining seam in the assessment pipeline.
- Before this change, partial failure after session completion could leave the session closed while downstream AURA/compliance/ecosystem work stayed ambiguous.
- Now completion has its own durable state instead of pretending session status alone is enough.

Important limitation:

- Legacy completed sessions with no `assessment_completion_jobs` row still use the old safe early-return path to avoid accidental duplicate rewards or events.
- The new background repair lane exists, but it still needs CI/runtime validation because this desktop Windows environment cannot run the project pytest stack cleanly.

---

## 12. Assessment completion now has an autonomous background repair lane

Files:

- `apps/api/app/services/assessment_completion_reconciler.py`
- `apps/api/tests/test_assessment_completion_reconciler.py`
- `.github/workflows/assessment-completion-reconciler.yml`
- `.github/workflows/ecosystem-hard-gates.yml`

Change:

- Added a scheduled reconciler for incomplete `assessment_completion_jobs`.
- The worker scans `pending` / `processing` / `partial` completion jobs and retries only the unfinished side effects:
  - rewards
  - streak
  - analytics
  - email
  - ecosystem events
  - aura events
  - automated decision log
- Added a dedicated GitHub Actions cron every 10 minutes using the same backend dependency install pattern as `aura-reconciler.yml`.
- Added focused backend regression coverage for the worker itself.
- Added the reconciler test file to `ecosystem-hard-gates.yml`.

Why it matters:

- This is the first real autonomous repair lane for the main VOLAURA product path, not just a manual retry story.
- A completed assessment no longer depends only on the user re-entering `/complete` to finish downstream work after a crash or transient failure.

Important limitation:

- Some underlying helper services still swallow their own internal errors, so CI/runtime observation remains essential even with the worker in place.

---

## 13. Profile edit now follows the same fail-safe state discipline as settings

Files:

- `apps/web/src/app/[locale]/(dashboard)/profile/edit/page.tsx`
- `apps/web/src/app/[locale]/(dashboard)/profile/edit/page.test.tsx`
- `.github/workflows/ecosystem-hard-gates.yml`

Change:

- `profile/edit` no longer boots with writable optimistic defaults for `is_public` and `visible_to_orgs`.
- The page now treats those booleans as unknown until the real profile is loaded and seeded.
- If profile load fails, the page shows a read-only error state instead of rendering a saveable form.
- Save is disabled until profile seed is complete.
- Added a regression test for:
  - load-failure rendering
  - submitting persisted booleans from real profile state
- Added the new test file to frontend hard gates.

Why it matters:

- This was the same silent-corruption class we already fixed in settings.
- Without this patch, a user could open profile edit and persist false defaults that were never confirmed from backend state.

Important limitation:

- The broader audit of adjacent settings-like and onboarding-adjacent state surfaces is not fully done yet.

---

## 14. Launch-critical events and organizations hooks now preserve real API errors

Files:

- `apps/web/src/hooks/__tests__/use-events.test.ts`
- `apps/web/src/hooks/__tests__/use-organizations.test.ts`
- `.github/workflows/ecosystem-hard-gates.yml`

Change:

- Updated hook regression tests so SDK-backed `events` and `organizations` paths now assert the real error message contract instead of accepting generic `"Failed to fetch ..."` placeholders.
- Brought `use-organizations.test.ts` into `ecosystem-hard-gates.yml` so this contract is protected in the same launch-critical lane as the existing `events` hook tests.

Why it matters:

- These hooks had already been normalized in code to `ApiError` / `toApiError`, but the regression layer was still written against the old generic-error behavior.
- Without this sync, the test suite would protect the wrong truth and make future cleanup noisier.

Important limitation:

- Frontend runtime verification is still blocked locally by the host Node crash, so the final confidence for this pass must come from CI or a healthy shell.

---

## 15. Discover and OAuth callback now tell the truth about ambiguous auth/profile states

Files:

- `apps/web/src/app/[locale]/(dashboard)/discover/page.tsx`
- `apps/web/src/app/[locale]/(dashboard)/discover/error-state.ts`
- `apps/web/src/app/[locale]/(dashboard)/discover/error-state.test.ts`
- `apps/web/src/app/[locale]/callback/page.tsx`
- `apps/web/src/app/[locale]/callback/route-decision.ts`
- `apps/web/src/app/[locale]/callback/route-decision.test.ts`
- `.github/workflows/ecosystem-hard-gates.yml`

Change:

- Discover browse/search flows no longer collapse every failure into a single `"organization account required"` or generic `"search failed"` story.
- Added explicit classification for:
  - `401` -> re-auth required
  - `403` -> org-only access
  - other failures -> retry state
- OAuth callback no longer treats non-`404` profile lookup failures as implicit `"dashboard is safe"`.
- Added pure regression tests for both decision layers and brought them into hard gates.

Why it matters:

- This removes a major class of misleading product behavior:
  - expired sessions pretending to be role problems,
  - backend faults pretending to be access issues,
  - callback ambiguity pretending profile recovery succeeded.

Important limitation:

- The callback fallback is now truthful rather than optimistic, but it is still a conservative recovery path.
- A richer explicit recovery surface would still be better than reusing the login error flow long-term.

---

## 16. Dashboard, profile, and AURA now preserve `next` on auth expiry

Files:

- `apps/web/src/app/[locale]/(dashboard)/auth-recovery.ts`
- `apps/web/src/app/[locale]/(dashboard)/auth-recovery.test.ts`
- `apps/web/src/app/[locale]/(dashboard)/dashboard/page.tsx`
- `apps/web/src/app/[locale]/(dashboard)/profile/page.tsx`
- `apps/web/src/app/[locale]/(dashboard)/aura/page.tsx`
- `.github/workflows/ecosystem-hard-gates.yml`

Change:

- Added a shared helper for locale-safe login redirects that preserve the original protected destination via `?next=...`.
- Replaced the old naked `/${locale}/login` redirects on three launch-critical authenticated surfaces:
  - dashboard
  - profile
  - AURA
- Added a focused regression test for the redirect path builder and brought it into hard gates.

Why it matters:

- Session expiry now returns the user to the correct page after re-auth instead of degrading into generic login redirects.
- This reduces one of the most frustrating forms of auth drift: the user recovers the session but loses context.

Important limitation:

- This is only the first wave.
- Other authenticated pages still need the same consistency pass, especially outside the main VOLAURA core path.

---

## 17. Assessment routes now use the same `next`-preserving auth recovery path

Files:

- `apps/web/src/app/[locale]/(dashboard)/assessment/page.tsx`
- `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/page.tsx`
- `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/complete/page.tsx`
- `apps/web/src/app/[locale]/(dashboard)/assessment/info/[slug]/page.tsx`

Change:

- Reused the shared dashboard auth-recovery helper across the main assessment surfaces.
- Fixed a real contract bug in `assessment/info/[slug]`: it previously redirected with `?returnTo=...`, while the login page only honors `?next=...`.
- Assessment start, session resume, session completion, and info pages now all preserve the intended destination through re-auth.

Why it matters:

- This hardens the most valuable user journey in the product.
- Session expiry during assessment no longer drops the user into a weaker or partially broken recovery path.

Important limitation:

- Some secondary authenticated surfaces outside the VOLAURA core journey may still need the same normalization pass.

---

## 18. Welcome, profile edit, and BrandedBy generation pages now preserve recovery context

Files:

- `apps/web/src/app/[locale]/welcome/page.tsx`
- `apps/web/src/app/[locale]/(dashboard)/profile/edit/page.tsx`
- `apps/web/src/app/[locale]/(dashboard)/brandedby/generations/[id]/page.tsx`

Change:

- Reused the shared login-recovery helper on remaining authenticated pages that were still redirecting to naked `/${locale}/login`.
- Kept `settings` sign-out / delete-account redirects untouched because those are intentional exits, not auth-expiry recovery.

Why it matters:

- This extends consistent post-login return behavior beyond the strict VOLAURA core loop.
- Users who lose auth on these pages no longer have to manually find their way back.

Important limitation:

- This pass does not yet cover every authenticated surface in the ecosystem.
- It deliberately prioritized the highest-value pages still showing naked recovery redirects.

---

## 19. My-organization bulk invite no longer lies about auth/server failures

Files:

- `apps/web/src/app/[locale]/(dashboard)/my-organization/invite/page.tsx`

Change:

- Stopped treating every missing-org state as `"you don't have an organization yet"`.
- Added explicit handling for:
  - `401` -> sign in again
  - server/other errors -> retry state
  - only true `null` org -> create-organization empty state

Why it matters:

- This removes a false-empty-state bug on the B2B invite path.
- Organization users with expired sessions were being told they simply had no organization.

Important limitation:

- This pass hardens the page-level truth only.
- Full regression tests for this surface are still absent.

---

## What was verified

Verified directly:

- `git diff --check` passed for the current pass files.
- Search confirmed the obsolete `volauraapi-production.up.railway.app` host no longer appears in core `apps/web`, `tests`, or `.github` paths touched in this pass.
- Search confirmed the live web source no longer contains the broken `/api/api/assessment/session/...` path.
- The new assessment resume regression test file exists and targets the corrected route.
- The settings page now gates writes on loaded state rather than optimistic defaults.
- Updated backend files in the latest assessment pass compiled successfully via `py_compile`:
  - `apps/api/app/schemas/assessment.py`
  - `apps/api/app/services/assessment/helpers.py`
  - `apps/api/app/routers/assessment.py`
  - `apps/api/app/services/assessment/completion_jobs.py`
  - `apps/api/app/services/assessment_completion_reconciler.py`
  - `apps/api/tests/test_assessment_router.py`

Verified earlier in the same hardening thread:

- Modified backend Python files from the earlier pass compiled cleanly via `py_compile`.

Files from that earlier verified pass:

- `apps/api/app/schemas/event.py`
- `apps/api/app/routers/events.py`
- `apps/api/app/routers/assessment.py`
- `apps/api/tests/test_assessment_router.py`
- `apps/api/tests/test_events_endpoints.py`

---

## What could not be verified in this environment

## 1. Frontend Node-based checks are blocked by host runtime failure

Blocked commands:

- `vitest`
- `tsc --noEmit`

Observed failure:

- Node processes in this Codex desktop thread crash before project code runs with a host-level assertion:
  - `Assertion failed: ncrypto::CSPRNG(nullptr, 0)`

Implication:

- Frontend test/typecheck verification must be rerun in a normal shell or CI.
- The code changes here are structurally reviewed, but not fully runtime-verified locally.

## 2. Backend pytest is also partially blocked on this Windows environment

Observed issue:

- Running repo-local pytest through `apps/api/.venv` hit a Windows/asyncio/AnyIO environment failure:
  - `_overlapped`
  - `WinError 10106`

Implication:

- Backend verification should be rerun in Linux CI or a clean local Python environment.

---

## Current highest-risk gaps that still remain

## P0. Assessment completion repair lane still needs stable-runtime proof

Problem:

- The durable completion job registry and background reconciler now exist, but they have not yet been verified in a healthy CI/runtime path from this desktop environment.

- Some underlying helper services still log-and-swallow internally, so the control plane needs a clean runtime verification pass to prove observability and retry semantics end-to-end.

What must happen:

- Run backend pytest in Linux/CI and watch the new worker path under real conditions.
- Validate cron execution plus stuck-job recovery against a safe fixture or staging-like job record.

---

## P0. Multi-competency journey still needs browser-level proof

Problem:

- The assessment plan/resume contract is now repaired in code, but it is not yet browser-verified in a stable runtime.

Why this matters:

- This is the most valuable user journey in VOLAURA.
- A contract fix without a browser-level proof can still hide hydration or navigation regressions.

What must happen:

- Add or expand one browser E2E that covers:
  - start a multi-competency assessment,
  - answer through one competency,
  - transition to the next,
  - refresh or re-enter mid-journey,
  - resume with the correct next question,
  - finish,
  - verify AURA / human review / export still work.

---

## P0. Auth/error contract is still inconsistent across remaining hooks and pages

Problem:

- Several high-value hooks are now normalized, but not the whole launch path.
- Some pages still assume generic load failures instead of branching correctly on `401` / `403` / `404`.

Impact:

- Expired auth can degrade into:
  - blank states,
  - generic retries,
  - misleading UI,
  instead of deterministic redirect/re-auth behavior.

Key areas to review next:

- onboarding-related hooks/pages
- discovery/org-access surfaces
- callback/auth recovery paths

What must happen:

- Normalize all remaining launch-critical hooks around one error contract.
- Preserve status codes.
- Redirect 401s consistently.
- Keep `next` path when redirecting from guarded pages.

---

## P1. Protected route coverage is still incomplete

Problem:

- Middleware/server-side guarding is narrower than the real protected journey.
- Some important pages still rely mostly on client-side `AuthGuard`.

Impact:

- Cold requests and refreshes are weaker than they should be.

What must happen:

- Extend server-side protection to the full protected route set:
  - `/assessment`
  - `/onboarding`
  - `/discover`
  - and other authenticated launch-critical surfaces.

---

## P1. OAuth callback still has misrouting risk

Problem:

- First-time OAuth signups can still be routed incorrectly if profile lookup fails in a way that is not a clean `404`.

Impact:

- New users can land in the wrong place and think onboarding is done when it is not.

What must happen:

- Make callback routing deterministic:
  - onboarding if profile missing,
  - dashboard only if profile definitely exists,
  - explicit recovery/error route if backend state is unclear.

---

## P1. Discovery still compresses different failure modes into one story

Problem:

- `unauthorized`, `wrong account type`, and `backend failure` are still too easy to collapse into the same user-facing message.

Impact:

- Good users receive the wrong remediation.

What must happen:

- Distinguish:
  - expired auth,
  - non-org access,
  - empty result,
  - backend failure.

---

## P1. Assessment completion page still behaves like a mutating screen

Problem:

- Opening the completion page can still trigger completion logic instead of being a pure read/view surface.

Impact:

- Refresh/revisit safety depends on backend idempotency instead of UI discipline.

What must happen:

- Turn completion page into a true GET-style results view once session is completed.

---

## P1. Settings hardening should be mirrored into remaining related forms

Problem:

- `settings` and `profile/edit` are safer now, but similar optimistic seeding patterns likely still exist elsewhere.

Most relevant next file:

- onboarding/profile-adjacent editable forms
- any privacy/discovery toggles outside `settings` and `profile/edit`

What must happen:

- Review all editable profile/privacy surfaces for:
  - false defaults,
  - mapper drift,
  - writable unknown state,
  - silent overwrite risk.

---

## Recommended next sequence

## Phase 1 — Finish the launch-critical path

Do next:

1. Persist full multi-competency assessment plans server-side.
2. Make resume restore the entire plan, not only the active competency.
3. Add browser E2E for `start -> refresh -> resume -> finish`.
4. Re-run the strengthened test set in a healthy environment.

Exit condition:

- Assessment can survive refresh and still complete correctly.

---

## Phase 2 — Make settings/profile writes impossible to corrupt silently

Do next:

1. Review onboarding-adjacent and other editable profile/privacy surfaces with the same fail-safe lens used on `settings` and `profile/edit`.
2. Add regression tests for:
   - load failure,
   - visibility load failure,
   - mapper field presence (`visible_to_orgs`),
   - "cannot save before seed is loaded".

Exit condition:

- No privacy/discovery screen can overwrite unknown state.

---

## Phase 3 — Normalize auth/error behavior

Do next:

1. Convert important generated/manual hooks to preserve real HTTP status.
2. Make 401 handling deterministic.
3. Preserve `next` redirects.
4. Expand middleware coverage.
5. Fix callback routing truth.
6. Fix discovery failure truth.

Exit condition:

- Expired sessions behave consistently everywhere.

---

## Phase 4 — Build the backend control plane

Do next:

1. Introduce durable completion jobs/outbox for assessment completion.
2. Track side effect status per completion job.
3. Retry incomplete steps.
4. Alert on stuck/incomplete completion jobs.
5. Generate regression tests from incidents around this path.

Exit condition:

- Compliance and audit trail are no longer best-effort side effects.

---

## Phase 5 — Make PR gates real, not ceremonial

Do next:

1. Run the strengthened `ecosystem-hard-gates` in CI and fix anything red.
2. Verify the new path set actually executes in GitHub Actions on PRs.
3. Consider making a smaller PR-safe assessment smoke mandatory.
4. Keep full Playwright journey on push/deploy if runtime/secrets cost is a concern.

Exit condition:

- Core VOLAURA regressions cannot slide into `main` silently.

---

## Suggested immediate task list for the next agent

If the next session continues immediately, do this in order:

1. Re-run frontend tests and typecheck outside this broken desktop-host Node runtime.
2. Re-run backend pytest in Linux/CI or a clean Python environment.
3. Implement server-side persistence for the full competency plan.
4. Add the refresh/resume browser E2E.
5. Review `profile/edit` for the same false-default problem fixed in `settings`.
6. Review onboarding-adjacent editable forms for false-default state.
7. Fix callback routing and discovery error truth.
8. Finish remaining auth/error normalization outside the already-covered hooks.

---

## Final judgment

The project is not a wreck.

The real shape is:

- strong product core,
- uneven reliability,
- too much implicit state in a few critical paths,
- not enough enforcement in launch gates.

That is fixable.

The right move is not to destroy VOLAURA.
The right move is to keep hardening the core until:

- assessment survives interruptions,
- privacy cannot be accidentally overwritten,
- auth failure modes are predictable,
- and `main` cannot accept regressions in the core trust loop.
