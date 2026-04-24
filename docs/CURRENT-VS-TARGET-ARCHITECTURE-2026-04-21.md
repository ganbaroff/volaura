# CURRENT vs TARGET Architecture (Canonical Snapshot)

**Date:** 2026-04-21  
**Status:** CURRENT source of truth for architecture-reality alignment.  
**Supersedes conflicting language in:** `docs/ECOSYSTEM-MAP.md`, `docs/MINDSHIFT-INTEGRATION-SPEC.md`, historical sections of `docs/adr/ADR-006-ecosystem-architecture.md`.

## Current (Implemented Reality)

1. **Auth topology is bridge-based, not fully unified.**
   - VOLAURA has primary Supabase project.
   - MindShift still has separate Supabase project bridged via `auth_bridge`.
   - Evidence: bridge router/tests and dual-project references in current docs.

2. **Shared backend monolith is live for ecosystem endpoints.**
   - `apps/api/` hosts character, grievance, compliance, and product adapters.

3. **Character event bus is active in VOLAURA backend.**
   - `character_events` producers are implemented for VOLAURA/LifeSim/MindShift bridge paths.

4. **Compliance loops now operationalized in product surfaces.**
   - Art.20 export: API + settings UI trigger.
   - Art.22 human review: API + contest UI flow.
   - Retention enforcement: SQL RPC + scheduled workflow.

## Target (Planned End-State)

1. **True unified auth across products** (single identity plane, no bridge shim).
2. **Pinned contract synchronization** between API schemas, integration specs, and frontend hooks.
3. **Governance hard gates in CI** for compliance + contract drift + swarm policy classes.
4. **Observability for compliance operations** (retention and review SLA dashboards).

## Material Gaps (Current → Target)

1. **Auth gap:** bridge model remains active.
2. **Contract gap:** MindShift integration spec includes payload/rate-limit assumptions not fully pinned to current runtime schemas.
3. **Governance gap:** policy language outpaces strict CI enforcement.
4. **Operations gap:** compliance runs are enforced, but audit visualization/reporting is thin.

## Immediate Rules for Contributors

- If this file conflicts with another architecture document, this file wins until that document is updated.
- Do not declare "unified auth fully live" while bridge-based identity flow is still in use.
- Do not treat historical ADR assumptions as runtime truth without code/test evidence.

