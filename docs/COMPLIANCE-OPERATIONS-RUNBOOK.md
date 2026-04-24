# Compliance Operations Runbook (Art.20 + Art.22 + Retention)

## Scope

This runbook covers the currently implemented compliance loops:

- Art.20 data portability (`GET /api/auth/export` + Settings UI trigger)
- Art.22 human review (`/api/aura/human-review*` + contest UI)
- Retention enforcement (`enforce_compliance_retention` RPC + scheduled workflow)

## Art.20 Data Portability

- Backend endpoint: `apps/api/app/routers/auth.py` (`GET /api/auth/export`)
- Frontend trigger: `apps/web/src/app/[locale]/(dashboard)/settings/page.tsx`
- Expected result: machine-readable JSON download with user-scoped sections.
- Verification:
  - `apps/api/tests/test_auth_router.py::TestExportMyData`
  - `apps/api/tests/test_auth.py::test_export_me_returns_machine_readable_bundle`

## Art.22 Human Review

- Backend endpoints:
  - `GET /api/aura/human-review/decisions`
  - `POST /api/aura/human-review`
  - `GET /api/aura/human-review`
  - admin transitions in `apps/api/app/routers/grievance.py`
- Frontend flow: `apps/web/src/app/[locale]/(dashboard)/aura/contest/page.tsx`
- SLA source: trigger/function in compliance schema migration.
- Verification:
  - `apps/api/tests/test_grievance_router.py::TestHumanReviewRequests`
  - `apps/web/src/hooks/__tests__/use-grievance.test.ts`

## Retention Enforcement

- SQL function:
  - `supabase/migrations/20260421120000_compliance_retention_enforcement.sql`
  - function: `public.enforce_compliance_retention(...)`
- Scheduler:
  - `.github/workflows/compliance-retention.yml`
  - cadence: monthly (1st day, 04:00 UTC)

### Defaults

- `automated_decision_log`: 730 days
- `human_review_requests`: 1095 days (resolved/escalated only)
- `consent_events`: 2190 days

## Incident and rollback notes

- If retention job fails: rerun workflow dispatch and inspect printed RPC error body.
- If retention policy must change: add a new migration and update workflow payload.
- Never edit old migrations in place.

