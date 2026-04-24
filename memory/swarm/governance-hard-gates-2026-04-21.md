# Governance Hard Gates Rollout — 2026-04-21

Scope completed in this pass:

- Added CI hard-gate workflow: `.github/workflows/ecosystem-hard-gates.yml`
- Added policy-vs-enforced matrix: `docs/SWARM-GATES-MATRIX-2026-04-21.md`
- Added canonical architecture truth source and contract lock docs.
- Added E2E smoke gate coverage for launch-critical + compliance loop in `tests/e2e/full-journey.spec.ts`.

Operational note:

- Governance moved from advisory-only to mixed mode:
  - hard enforced in CI for compliance/contract/launch-critical checks
  - policy-only items remain documented and promotable on repeated incidents

