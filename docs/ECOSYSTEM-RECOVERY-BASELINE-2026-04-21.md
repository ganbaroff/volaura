# Ecosystem Recovery Baseline (Phase 0)

**Date:** 2026-04-21  
**Sprint:** Ecosystem Recovery Sprint (3+ Weeks)  
**Purpose:** lock a factual baseline, P0/P1 risk register, and freeze boundaries before broad changes.

## Baseline Snapshot

- Verification anchor: `docs/TOP-20-CLAIM-VERIFICATION-LEDGER-2026-04-21.md`
- Core unresolved gaps at sprint start:
  - retention enforcement not hard-implemented end-to-end
  - architecture truth conflict (shared-vs-bridge narrative)
  - MindShift contract drift (spec vs runtime payloads)
  - governance gates not consistently hard-enforced in CI
- Recently closed loops:
  - Art.22 human review API + UI
  - Art.20 data export API + UI trigger in settings

## P0 Risks (Blockers for launch-readiness)

1. **Retention enforcement gap**  
   Risk: compliance breach from policy/runtime mismatch.  
   Owner zone: `supabase/migrations/`, `apps/api/app/routers/auth.py`, backend tests.

2. **Architecture truth conflict**  
   Risk: wrong implementation decisions and repeated doc/code divergence.  
   Owner zone: `docs/ECOSYSTEM-MAP.md`, `docs/adr/ADR-006-ecosystem-architecture.md`.

3. **Contract drift (MindShift/event bridge)**  
   Risk: broken integration and silent data mismatch across products.  
   Owner zone: `docs/MINDSHIFT-INTEGRATION-SPEC.md`, `apps/api/app/routers/character.py`, API contracts.

4. **Governance enforcement gap**  
   Risk: policy theater (rules declared but not enforced).  
   Owner zone: `.github/workflows/`, `memory/swarm/`, governance docs.

## P1 Risks (High impact, not immediate blockers)

1. **Consent policy-version logging confidence is medium (partial).**
2. **Health-data firewall is present but only partially evidenced at output boundary.**
3. **OpenBadge/VC payload is basic and needs contract hardening for external verifiers.**
4. **End-to-end regression coverage for launch-critical flows is inconsistent.**

## Freeze Boundaries (Phase 0-1)

Until Phase 0 sign-off, the following require checklist review in PR description:

- `supabase/migrations/**`
- `apps/api/app/routers/auth.py`
- `apps/api/app/routers/grievance.py`
- `apps/api/app/routers/character.py`
- `docs/ECOSYSTEM-MAP.md`
- `docs/adr/ADR-006-ecosystem-architecture.md`
- `.github/workflows/**`

## Phase 0 Exit Criteria

- P0/P1 register is documented and owner zones are explicit.
- Freeze boundaries are published and referenced by CI/review checklist.
- A single execution sequence is confirmed:
  1) launch-critical loops  
  2) retention enforcement  
  3) architecture truth + contract sync  
  4) governance hardening

