# VOLAURA Modules — Octopus Platform Reference

**Status:** canonical as of 2026-04-17.
**Authority:** supersedes any prior "keep products separate" framing. Where this doc and a historical brief disagree, this doc wins.
**Companions:** `docs/ECOSYSTEM-CONSTITUTION.md` (5 Foundation Laws), `memory/atlas/projects/opsboard.md` (EventShift working notes), `.claude/rules/ecosystem-design-gate.md` (UI gate).

---

## 1. Why this document exists

CEO directive (2026-04-16): stop treating EventShift/OPSBOARD as a WUF13-specific app and start treating it as the first **module** of a **universal VOLAURA platform**. The business shape is an **octopus**: one persistent core, many pluggable arms, each arm serving a customer segment.

Prior framing (Apr 15 brief, now in `docs/research/archive/`) recommended keeping OPSBOARD separate through WUF13 and revisiting afterwards. That recommendation is reversed. WUF13 is tenant #1 of module #1 (EventShift); it is the proving ground, not the boundary.

This document is the single source of truth for: what counts as a module, how modules attach to the core, what the multi-tenant contract looks like, and how new arms are added without rewriting the organism every time.

---

## 2. The octopus shape

One **core** (identity, verification, reputation, billing, events).
Many **arms** (domain modules that reuse the core and sell to specific customer segments).

- The core never knows which arms are active for a given tenant — it only exposes capabilities (auth, AURA, crystal emit, character_events, billing) and the arms subscribe.
- Arms never own identity, auth, or reputation. If an arm wants to verify a user, it calls the core. If it wants to reward a user, it emits a `crystal_earned` / `reliability_proof` event to `character_events` and the core settles.
- Tenants (organisations buying the platform) activate arms via a **module catalogue** with feature flags + billing SKUs. Activation is per-org, not per-deployment.

This shape is what lets WUF13 and a future festival organiser buy different arm bundles off the same VOLAURA install without either of them seeing the other's data.

---

## 3. The 4-kind taxonomy

Every piece of the ecosystem fits into exactly one of four kinds. If something does not fit, either the taxonomy is wrong or the thing should not exist.

**Core** — VOLAURA web (`apps/web`, `apps/api`). Identity, AURA score, assessment engine, crystal ledger, character_events bus, billing. One deployment per jurisdiction.

**Gateway** — MindShift mobile PWA. Daily surface that the public actually touches. Feeds the core via `character_events` (session_completed, streak_observed, energy_logged). Does not own identity — it federates to VOLAURA auth when the user links accounts. A gateway is an arm too, but optimised for retention and daily habit rather than vertical ops.

**Module** (arm) — EventShift today. BrandedBy, future verticals (healthcare shift-ops, construction-crew ops, volunteer coordination) tomorrow. A module is:
- vertical-specific (serves one customer job-to-be-done),
- multi-tenant from schema level,
- activation-gated per tenant via feature flag + billing SKU,
- read/write to the core via well-defined contracts (auth, AURA lookup, event emit),
- replaceable without touching the core.

**Experience layer** — Life Simulator (Godot 4). Renders state from modules and the core as a 3D scene. Reads `character_events`; never writes primary data. Opt-in per user. Breaking the experience layer never breaks the business.

**Infra** — ZEUS gateway, Python swarm, Atlas memory. Runtime that makes the agents coordinate. Users never see infra directly. Infra is not a module; infra is plumbing.

---

## 4. Module contract

A piece of work qualifies as a module iff it satisfies ALL of these. If any are missing it is either a feature on the core, a gateway surface, or not ready to ship.

1. **Multi-tenant by schema.** Every table has `org_id UUID NOT NULL REFERENCES orgs(id)` and RLS policy using `current_setting('request.jwt.claims.org_id')`. No module may depend on single-tenant assumptions, ever, even for an MVP.
2. **Activation-gated.** Per-org feature flag controls whether the module is visible to users of that org. Off by default. Turning it off is fully reversible (data is preserved; UI disappears).
3. **Billable via the core.** Module consumption is metered (seats, events, compute, or domain-specific unit) and rolled up through the core's billing subsystem. No module maintains a parallel invoice stack.
4. **Emits to `character_events`.** Every domain-meaningful user action emits one event with `source_product`, `event_type`, `payload JSONB`, `org_id`, `user_id`. The bus is how AURA, LifeSim, and future arms perceive module activity. Silent modules are invisible to the organism.
5. **Respects the 5 Foundation Laws.** Never red, energy adaptation, shame-free language, animation safety, one primary CTA per screen. Gate check: `.claude/rules/ecosystem-design-gate.md`.
6. **Core-identity only.** Module users are core profiles with module role grants. No module ships its own sign-up, password, or session. SSO via the core is mandatory from commit one.
7. **Reversible per tenant.** Deactivating a module for an org must leave the org's core identity, AURA, and billing intact. No module writes into core-owned tables.

---

## 5. The 7 integration paths (EventShift case study)

These are the concrete touchpoints between a module and the core. Numbered for reference; any new module must answer each one explicitly.

**Path 1 — SSO + org-admin bridge.** Module user is a VOLAURA `profile` with an `org_membership` row granting the module role. Login is always VOLAURA auth. Org admins see all members of their org; module admins see only module scope within their org. Contract: `auth.uid()` + `org_id` claim drives RLS in every module query.

**Path 2 — `reliability_proof` → AURA.** When the module observes verifiable work (EventShift: shift closed cleanly, handover chain complete, no unresolved incidents), it emits `event_type='reliability_proof'` with `source_product='eventshift'`. The AURA reconciler pipes that into the `reliability` signal (weight 0.15) and `event_performance` signal (weight 0.10). This is the module's single biggest gift to the core: real-work data beating self-report assessments.

**Path 3 — Crystal tie-in.** Module work earns crystals at a documented formula (e.g. 1 shift-hour = 25 FOCUS crystals for EventShift). Crystal Law 8 requires a simultaneous spend path; the module must either provide one (item shop scoped to the module) or defer emission until the core offers one.

**Path 4 — Face under the skeleton.** Module UI uses core tokens (Tier 1-2) and adds only Tier 3 accent. Module views live at `components/features/{module}/`. Skeleton components (button, card, field) come from the core. A module may not fork a skeleton component; it may only propose improvements upstream.

**Path 5 — Multi-tenant schema from Day 1.** Every module migration creates tables with `org_id` + RLS. Seed data is tenant-scoped. Test fixtures are tenant-scoped. Zero code path permits `org_id IS NULL` in production.

**Path 6 — Module catalogue + activation surface.** One `module_activations (org_id, module_slug, enabled, settings JSONB, billing_sku)` table owned by the core. A module registers its slug, billing SKU, and default settings at install time. Tenant org admins toggle modules in an org-admin UI; toggling updates this table; the module's frontend gates its own visibility on it.

**Path 7 — Usage-based metering hook.** The same event that feeds AURA (Path 2) is also the billing meter. No separate metering pipeline. A module reports usage by emitting structured events; the core's billing service aggregates per `org_id` + `module_slug` + `billing_period`. Single pipeline, single source of truth.

---

## 6. The module catalogue

One row per module, owned by the core.

```
modules (
  slug               TEXT PRIMARY KEY,
  display_name       TEXT NOT NULL,
  tier               TEXT NOT NULL,  -- core | gateway | module | experience
  default_enabled    BOOLEAN DEFAULT false,
  billing_sku        TEXT,
  min_core_version   TEXT,
  owner_team         TEXT,
  settings_schema    JSONB,          -- JSON Schema for per-org settings
  created_at         TIMESTAMPTZ DEFAULT now()
)

module_activations (
  org_id       UUID REFERENCES orgs(id),
  module_slug  TEXT REFERENCES modules(slug),
  enabled      BOOLEAN NOT NULL DEFAULT false,
  settings     JSONB NOT NULL DEFAULT '{}',
  activated_at TIMESTAMPTZ,
  PRIMARY KEY (org_id, module_slug)
)
```

Current seed:

| slug | display_name | tier | default_enabled |
|---|---|---|---|
| `volaura-core` | VOLAURA | core | true |
| `mindshift-gateway` | MindShift | gateway | false |
| `eventshift` | EventShift | module | false |
| `brandedby` | BrandedBy | module | false |
| `life-simulator` | Life Simulator | experience | false |

When a new arm is proposed, the first artefact is a row in this table and a `min_core_version` declaration. If the required capability is not in the core yet, the arm blocks on the core shipping that capability — never by bolting it onto the module.

---

## 7. Multi-tenant foundation (non-negotiable)

All module data sits in PostgreSQL schemas shared with the core. Tenancy is enforced by:

- Every domain table has `org_id UUID NOT NULL REFERENCES orgs(id)`.
- RLS policy on every domain table:
  ```sql
  CREATE POLICY module_org_scope ON <table>
  USING (org_id::text = current_setting('request.jwt.claims.org_id', true));
  ```
- Supabase JWT claims include `org_id` for the currently-active org. Users who belong to multiple orgs get a switcher; the JWT is re-minted with the new claim on switch.
- Cross-org queries (admin, audit, swarm jobs) go through RPC functions with `SECURITY DEFINER` and explicit org-scoping parameters. No module code touches raw cross-org tables.
- Seed data ships under a `seed-dev-org` UUID in dev; production onboarding provisions the real org before any user data is written.

The historical trap (Apr 6, 2026, 12h outage on `postgres-jyby.railway.internal` DNS mismatch) lives in `memory/atlas/projects/opsboard.md`. Multi-tenant schema is enforced in migrations so future ops mistakes cannot silently leak data across tenants.

---

## 8. Activation, entitlement, billing

Activation flow:

1. Sales or self-serve onboarding creates the `org` row.
2. Org admin is granted `owner` role on the org.
3. Org admin opens the module catalogue UI (core-owned page), sees available modules, toggles one on.
4. Toggle creates a `module_activations` row with `enabled=true` and a Stripe subscription item bound to the module's `billing_sku`.
5. Module frontend reads its own activation status via a core API (`GET /api/orgs/me/modules`) and renders only the modules the org has active.

Entitlement:

- A user's access within a module is governed by their role in the org (`owner`, `admin`, `coordinator`, `member`, `viewer`) combined with module-defined scopes. The core owns the role table; the module owns the scope enum.
- A user can belong to multiple orgs. Role grants are per-org, never global. AURA is global (earned cross-tenant), but visibility of activity to an org is always filtered by org membership.

Billing:

- One Stripe customer per org, one subscription per org, subscription items per active module.
- Usage reports are driven by `character_events` aggregated per `org_id` + `module_slug` + `billing_period`. A nightly Supabase function writes to `billing_usage_snapshots`; Stripe webhook consumes it for metered SKUs.
- Currency and jurisdiction gating are handled at the core level, never per-module.

---

## 9. Event bus contract

`character_events` is the organism's spine. The table already exists in the core; modules write to it, they do not create parallel tables for domain events.

Shape:

```
character_events (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_product  TEXT NOT NULL,        -- 'volaura-core' | 'mindshift-gateway' | 'eventshift' | ...
  event_type      TEXT NOT NULL,        -- domain-scoped verb
  payload         JSONB NOT NULL,
  org_id          UUID REFERENCES orgs(id),
  user_id         UUID REFERENCES profiles(id),
  occurred_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  idempotency_key TEXT UNIQUE            -- module-generated, e.g. "eventshift:shift:uuid:closed"
)
```

Contract:

- Every emit carries `org_id` except for truly org-less events (e.g. onboarding pre-org-membership).
- Every emit is idempotent via `idempotency_key`; retries must not double-count.
- Module must document its event types in `docs/events/<module-slug>.md`. AURA reconciler, LifeSim, and billing read this documentation to know which events matter.
- Consumers never mutate events. Events are append-only. Corrections are new events (`..._reversed`, `..._corrected`).

---

## 10. Current arms (snapshot 2026-04-17)

**VOLAURA-core.** Live. `volaura.app`, `volauraapi-production.up.railway.app`. Owns identity, AURA 8-competency weighted score, adaptive assessment (IRT/CAT, pure-Python 3PL in `apps/api/app/core/assessment/engine.py`), crystal ledger, `character_events`, org model (partial — needs Path 6 surface).

**MindShift-gateway.** Production v1.0, separate Supabase project (awaiting federation). Focus sessions, energy tracking, invisible streaks, 5 Foundation Laws enforced. Integration with core: scheduled for post-WUF13 sprint (`character_events` emit + AURA daily-consistency signal).

**EventShift (module #1).** WUF13 Guest Services is tenant #1. Deadline May 15-17, 2026. Rebuild from WUF13-app to universal module is in flight in `memory/atlas/projects/opsboard.md`. Three success criteria for the rebuild are Path 1 (SSO + org admin), Path 2 (reliability_proof → AURA), Path 5 (schema-level multi-tenancy). Paths 3, 6, 7 land in the two sprints after WUF13 proves the core integration contract.

*Domain model (CEO correction, April 2026):* **Event → Department → Area → Unit → People + Metrics.** People-first, not incident-first. An event contains departments; a department contains operational areas; an area contains units (shifts, posts, patrols); a unit is staffed by people and produces metrics (attendance, handover integrity, incident closure, reliability proof). The current scaffolded Supabase migration, FastAPI routers, and frontend pages reflect the older incident-first model and must be rewritten to this shape before WUF13. Incidents become one metric stream among several, not the root entity. Every table in the rewrite carries `org_id` (Path 5) and emits `character_events` on state transitions (Path 2).

**BrandedBy (module, ~15%).** AI professional identity / twin. Logic scaffold in `packages/swarm/archive/zeus_video_skill.py`. No UI yet. Enters catalogue when it reaches MVP.

**Life Simulator (experience layer).** Godot 4 (formerly Three.js fork). Phase 2 pending: Ready Player Me avatars, `agent.wake` wiring. Consumes `character_events`; produces none.

**Atlas / ZEUS / swarm (infra).** Not in the user-facing catalogue. CEO can see transparency at `/atlas`. Serves the organism; never sold.

---

## 11. Opening a new arm — checklist

Before writing any module code:

- [ ] Row added to `modules` seed with `slug`, `display_name`, `tier='module'`, `billing_sku`, `min_core_version`.
- [ ] Owner team declared (even if it is just Atlas + CTO today).
- [ ] Settings schema (JSON Schema) drafted for per-org configuration.
- [ ] `docs/events/<slug>.md` opened with the event types the module will emit.
- [ ] At least Paths 1, 2, 5 identified with specific core touchpoints.
- [ ] Feature flag wiring in core frontend (`useModuleActivation(slug)`) verified.
- [ ] Anti-pattern scan against `.claude/rules/ecosystem-design-gate.md` §16.
- [ ] Tenant plan: who is tenant #1, what is their success criterion, what is the revenue shape.

If any box is unchecked, the arm is not ready. The pressure to ship for one customer is the exact force that turns a module into a fork, and a fork kills the organism. One core, many arms — the discipline is in refusing to skip the checklist.

---

## 12. Change control

Any edit to this document that changes:
- the 4-kind taxonomy,
- the module contract (§4),
- the integration paths (§5),
- the tenancy model (§7)

requires a decision log entry in `memory/decisions/YYYY-MM-DD-modules-<slug>.md` with: prior shape, proposed shape, rationale, revisit trigger. Cosmetic edits (typos, clarifications, new snapshot entries in §10) do not need a decision log.

---

*Last updated 2026-04-17 12:10 Baku by Atlas. Universal-module framing per CEO directive 2026-04-16. Replaces the Apr 15 "keep separate" recommendation now archived at `docs/research/archive/ecosystem-brief-2026-04-15.md`.*
