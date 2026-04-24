# Top-20 Claim Verification Ledger (Conservative)

**Date:** 2026-04-21  
**Method:** Doc claim vs implementation evidence (code/migrations/tests) with conservative confidence.  
**Rule:** If evidence is incomplete or ambiguous, status is `unclear` or `partial` (never assumed as implemented).

---

## Status Legend

- `implemented` — clear evidence in runtime code and supporting tests/migrations
- `partial` — meaningful implementation exists, but claim is broader than evidence
- `missing` — no implementation evidence found for claimed behavior
- `conflicting` — docs and implementation materially diverge
- `unclear` — evidence exists but is insufficient for confident verdict

---

## Verification Table

| # | Claim (from docs/memory) | Evidence (paths) | Verdict | Confidence |
|---|---|---|---|---|
| 1 | GDPR Art.22 explicit consent is required before automated assessment decisioning | `apps/api/app/routers/assessment.py`, `apps/api/app/schemas/assessment.py`, `apps/web/src/app/[locale]/(dashboard)/assessment/page.tsx`, `apps/api/tests/test_assessment_consent.py` | implemented | high |
| 2 | Consent events are logged with policy versioning | `supabase/migrations/20260415230000_ecosystem_compliance_schema.sql`, `supabase/migrations/20260419020000_seed_policy_versions.sql`, `apps/api/app/routers/auth.py`, `apps/api/app/routers/assessment.py` | partial | medium |
| 3 | Formal human-review path exists and is operationalized | `supabase/migrations/20260415230000_ecosystem_compliance_schema.sql`, `apps/api/app/routers/grievance.py` (`/api/aura/human-review*`, `/api/aura/human-review/decisions`), `apps/api/tests/test_grievance_router.py` (`TestHumanReviewRequests`), `apps/web/src/app/[locale]/(dashboard)/aura/contest/page.tsx`, `apps/web/src/hooks/queries/use-grievance.ts` | implemented (backend + UI loop) | high |
| 4 | Grievance mechanism is implemented end-to-end | `supabase/migrations/20260416030000_grievances_table.sql`, `apps/api/app/routers/grievance.py`, `apps/api/tests/test_grievance.py`, `apps/web/src/app/[locale]/admin/grievances/page.tsx` | implemented | high |
| 5 | Art.9-style health-data firewall exists at DB/output layer | `supabase/migrations/20260409000001_health_data_firewall.sql` | partial | medium |
| 6 | User right-to-erasure endpoint exists | `apps/api/app/routers/auth.py` (`DELETE /api/auth/me`), `apps/api/tests/test_auth.py` | implemented | medium |
| 7 | Data portability export endpoint is implemented | `apps/api/app/routers/auth.py` (`GET /api/auth/export`), `apps/api/tests/test_auth_router.py` (`TestExportMyData`), `apps/api/tests/test_auth.py` (`test_export_me_returns_machine_readable_bundle`), `apps/web/src/app/[locale]/(dashboard)/settings/page.tsx` | implemented (backend + user-triggered JSON export UI) | high |
| 8 | OpenBadge/VC-like badge payload endpoint exists | `apps/api/app/routers/badges.py`, `apps/api/tests/test_badges.py`, `apps/api/tests/test_badges_endpoints.py` | implemented (basic) | medium |
| 9 | Shared auth bridge from external project is implemented | `apps/api/app/routers/auth_bridge.py`, `supabase/migrations/20260408000001_user_identity_map.sql`, `apps/api/tests/test_auth_bridge.py` | implemented | high |
| 10 | One universal shared auth across all products is fully live | Bridge exists, but split-project bridge model is still present in docs/code | conflicting | high |
| 11 | `character_events` acts as ecosystem event bus | `apps/api/app/routers/character.py`, `apps/api/app/services/ecosystem_events.py`, `apps/api/app/services/assessment/rewards.py`, `apps/api/app/services/lifesim.py` | implemented (producer side) | high |
| 12 | Crystal economy has anti-abuse safeguards (idempotency/atomic spend/caps) | `apps/api/app/routers/character.py`, `supabase/migrations/20260328000040_atomic_crystal_deduction.sql`, `supabase/migrations/20260327000031_character_state_tables.sql`, `apps/api/tests/test_character_api.py` | implemented | high |
| 13 | MindShift outbound bridge push from VOLAURA is resilient | `apps/api/app/services/cross_product_bridge.py`, `apps/api/tests/test_cross_product_bridge.py` | implemented | medium |
| 14 | MindShift integration spec matches current API contract | `docs/MINDSHIFT-INTEGRATION-SPEC.md` vs `apps/api/app/routers/character.py` and related payload behavior | conflicting | medium |
| 15 | LifeSim integration exists in VOLAURA backend | `apps/api/app/routers/lifesim.py`, `apps/api/app/services/lifesim.py`, `supabase/migrations/20260416050000_lifesim_events_table.sql`, `apps/api/tests/test_lifesim_endpoints.py` | implemented (API module) | high |
| 16 | BrandedBy integration has active backend domain flows | `apps/api/app/routers/brandedby.py`, `supabase/migrations/20260327151415_create_brandedby_schema.sql`, `apps/api/tests/test_brandedby_router.py` | implemented | high |
| 17 | EventShift is activation-gated per organization | `supabase/migrations/20260417130100_module_catalogue.sql`, `apps/api/app/routers/eventshift.py` | implemented | high |
| 18 | Model/provider fallback routing is centralized | `apps/api/app/services/model_router.py` | implemented | high |
| 19 | Architecture docs represent current state consistently | `docs/adr/ADR-006-ecosystem-architecture.md`, `docs/ECOSYSTEM-MAP.md`, `docs/ECOSYSTEM-CONSTITUTION.md`, `docs/ECOSYSTEM-AUDIT-ALL-REPOS.md` | conflicting | high |
| 20 | Swarm governance mandatory gates are consistently enforced by automation | `memory/swarm/shared-context.md`, `memory/swarm/daily-health-log.md`, workflow/process docs show deviations/exceptions | partial / unclear | medium |

---

## Critical Gaps (Highest Impact)

1. **Compliance execution gap:** consent, grievance, human review, Art.20 export UI, and scheduled retention enforcement are present; next gap is strengthening retention observability/audit dashboards.
2. **Architecture truth gap:** shared-vs-bridge reality is not canonically represented in one current-state source.
3. **Contract drift gap:** MindShift integration spec and actual API behavior diverge.
4. **Governance enforcement gap:** swarm policy strictness and logged operational behavior are not fully synchronized.

---

## Recommended Next Audit Slice

To move from conservative verification to execution-ready remediation:

1. Build a **Top-10 compliance closure checklist** (endpoint/table/test per obligation).  
2. Publish **CURRENT vs TARGET architecture note** that supersedes contradictory map language.  
3. Regenerate and pin **integration contracts** for bridge/event payloads.  
4. Define which swarm gates are **policy-only** vs **hard-enforced in CI/workflows**.

