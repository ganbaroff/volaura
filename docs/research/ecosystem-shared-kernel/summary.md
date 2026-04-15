# Ecosystem shared kernel research — 2026-04-15

**Status:** research-only. No code. No migration started. Decision gate for CEO + Atlas after read.
**Raw notes:** `docs/research/ecosystem-shared-kernel/raw.md` (sources, verdict table, evidence grades).
**Memory gate line:** task-class=research-architecture · SYNC=✅ · BRAIN=❌(absent) · sprint-state=✅ · extras=[PORTABLE-BRIEF, ECOSYSTEM-REDESIGN-2026-04-15/STATE, research-first] · proceed

---

## TL;DR — Doctor Strange path

One recommendation, one architecture, five products, one solo founder.

> **Keep one Supabase project as the shared identity + event plane. Inside it, carve schemas per product (`volaura`, `mindshift`, `life_sim`, `branded_by`, `atlas`) and a `public` schema for the four truly cross-cutting tables: `profiles`, `character_events`, `consent_records`, `ai_decision_log`. Expose one OpenAPI source of truth from `apps/api` and generate both TS and Python SDKs into `packages/api-sdk-*`. Unify cross-product events on Supabase Realtime (free, works in all 5 runtimes) and add Inngest only for internal async jobs. Keep Turborepo + pnpm; don't migrate to Nx yet. Observe the whole thing in PostHog with Langfuse and Sentry feeding in. Write a `consent_records` ledger now to front-run the 2026 EU Digital Omnibus + AI Act obligations.**

Everything else in this doc argues for that shape and names what we should *not* share.

---

## What multi-product teams in 2024-2026 actually share

Looking at Cal.com (reference-grade public monorepo), create-t3-turbo (the community canonical pattern), and published Supabase/solo-founder advice, the shared-kernel surface converges on **six slots**, not four.

| Slot | Our package | What it owns |
|---|---|---|
| Types | `packages/api-sdk-ts` + `packages/api-sdk-py` | Generated from `apps/api` OpenAPI 3.1, TanStack Query hooks + Zod for TS, Pydantic for Python |
| DB | `packages/db` | Supabase schema + `.sql` migrations + generated TS types |
| Auth | `packages/auth` | Thin wrappers over Supabase SSR, session helpers, JWT verification for FastAPI and Godot |
| Events | `packages/events-schema` | JSON Schemas for `character_events` payloads — importable by TS, Python, Godot (runtime validator) |
| Consent | `packages/consent` | `hasConsent(user, purpose)` helper + `recordConsent()` + DPIA doc pointer. Fronts `public.consent_records` |
| UI | `packages/ui` | shadcn-ui + Tailwind v4 tokens, same design-system Atlas already runs |

Four (DB, Auth, Types, UI) match t3-turbo and Cal.com almost exactly. Two (Events, Consent) are ours because we're a 5-product ecosystem under EU AI Act reach — Cal.com and t3-turbo don't need them at our scope.

Sources: t3-turbo README; Cal.com handbook on monorepo + turborepo; FastAPI "Generating SDKs" docs.

---

## Top 3 migration paths

All three start from "everything in one monorepo, Supabase Auth kept, `character_events` kept." The fork is *how aggressive*.

**Path A — Absorb (recommended).** Pull MindShift + Life Sim + BrandedBy into the existing VOLAURA monorepo as `apps/mindshift/`, `apps/life-sim/`, `apps/branded-by/`. Keep Turborepo + pnpm. Build the six shared packages incrementally (db + auth + events-schema first, consent + types-py second, ui last). Migrate product-by-product, each product read-only from the shared kernel before writing. Cost: 4-6 weeks, ~0 AZN extra tooling. Adoption evidence: Cal.com, create-t3-turbo, Vercel's own monorepo templates all ship this shape. Risk: pulling three repos into one is a one-time destructive op; each product's git history either merges or is archived.

**Path B — Federate (middle path).** Keep repos separate. Publish the six shared packages to a private pnpm registry or git submodule. Each product pulls the kernel as a dependency. Cost: 2-3 weeks, requires CI to cut kernel releases. Adoption evidence: how Supabase's own tooling ships — one repo per service, shared SDKs. Risk: version drift — any product can lag behind the kernel and we lose the "change-one-place" guarantee that's the whole point.

**Path C — Full polyglot monorepo with Nx (ambitious).** Same as Path A but switch from Turborepo to Nx to get first-class Python and cross-language affected-detection. Cost: 6-8 weeks (Path A time + Nx migration). Evidence: Nx's own blog + pkgpulse 2026 benchmark (Nx ~16% faster than Turbo at 4-machine CI scale; more importantly, Nx has UV/Poetry plugins, Turbo treats Python as opaque shell). Risk: high tooling-churn cost for a solo founder; the CI speedup doesn't matter at our volume yet.

**Call:** Path A now. Reconsider Path C only if `packages/swarm/` + `apps/api/` co-evolution starts hurting — not before.

---

## What we should NOT try to share

Sharing for sharing's sake is how good monorepos rot. Genuinely per-product decisions that should stay private:

- **Per-product UI screens, route handlers, business logic.** The 5 products have five voices — VOLAURA is rational/assessment, MindShift is reflective/ADHD-first, Life Sim is playful/Godot, BrandedBy is performative, Atlas is system. Forcing a "shared feature" layer would flatten that.
- **Per-product analytics events** beyond `character_events`. Each product has its own verbs (assessment_completed, reflection_logged, level_up, video_rendered, swarm_run_completed). Don't force them into a single taxonomy — let each product own its event namespace, only lift up to `character_events` when the event needs cross-product effects (crystal earn, badge tier change).
- **Per-product CI/deploy pipelines.** Turborepo gives us `turbo run deploy --filter=apps/web` per app. Don't build a uniform deploy workflow — Godot, Expo, Next.js, FastAPI each have different build hosts and that's fine.
- **Content, copy, i18n strings.** Each product has its own `locales/`. Constitution (Law 3 — shame-free language) is the shared rule, the actual strings stay product-local.
- **Per-product feature flags and experiments.** They diverge too fast. One shared flag system (PostHog feature flags — free) is enough plumbing; the *flags* themselves belong to each product.

Anti-pattern to avoid: "one `packages/features/` package with all domain logic" — Cal.com does this, but they're a single-company SaaS. We are five *products* with different mental models. Shared kernel = plumbing, not products.

---

## Specific event-bus recommendation

For the five-runtime mix (FastAPI Python, Next.js TS, Expo TS, Godot GDScript, `packages/swarm` Python) the answer is **hybrid — Supabase Realtime for cross-product broadcasts, Inngest for internal async jobs. No NATS, no Trigger.dev, no Kafka.**

Reasoning: Supabase Realtime is free, already deployed, speaks WebSocket — meaning Godot can subscribe to `character_events` inserts over WS with the addon or a 30-line HTTPRequest loop. Next.js/Expo subscribe via `supabase-js`. Python swarm subscribes via `realtime-py`. FastAPI publishes by writing to the `character_events` table; Realtime fans out. Zero extra infra.

Inngest covers the second job — durable async work inside one product: "after assessment submitted → score → notify Telegram → re-rank AURA." It's TS + Python, keeps compute on our side (we don't move execution off Railway), and retry/observability UI is the DX we actually want. Trigger.dev loses because it runs the compute itself — foreign runtime, foreign bill. NATS loses because solo founder ops cost is real.

Adoption evidence: Inngest's Python SDK is production-used; Supabase Realtime runs most indie Godot+web games on Supabase docs' own asset showcases.

---

## Specific shared-schema recommendation

**Single Supabase project (the existing VOLAURA one). Schemas per product: `volaura`, `mindshift`, `life_sim`, `branded_by`, `atlas`. Cross-cutting tables in `public`: `profiles`, `character_events`, `consent_records`, `ai_decision_log`, `crystals`, `badges`.**

Why not separate projects (the "obvious" option): separate projects mean separate `auth.users` tables. Same person in VOLAURA and MindShift becomes two identities. This breaks the entire ecosystem thesis — one user, five touchpoints, one AURA. Official Supabase docs confirm projects are *isolated server instances* — they don't share auth. Multi-project is the right answer for isolated products (e.g. client apps), not for an ecosystem with one identity graph.

Why not one flat `public` schema: at 5 products each with ~10-30 tables, `public` becomes 100+ tables with no separation. RLS policy review becomes unreadable. Schemas give us a natural boundary and let us revoke product X's access to product Y's data with `REVOKE USAGE ON SCHEMA mindshift FROM volaura_role;`.

Branching: use *one* persistent branch as staging. No per-PR branches — at our cash constraint they are a waste. Dev = local Supabase via Docker. Staging = persistent branch. Production = main.

Migration order: create schemas → migrate `character_events` from `public` if needed (it already lives in public, good) → move MindShift/Life Sim/BrandedBy products' own tables into their schemas at import time. Two days of SQL + RLS work per product.

---

## Proposed 1-month foundation plan

Four weeks to unify the ecosystem without breaking existing products. Each week ends with a working build.

**Week 1 — Shared kernel skeleton + MindShift absorption.**
Add `packages/events-schema` (JSON Schema for the 4-6 known events). Add `packages/consent` (table + helper). Add `packages/api-sdk-ts` (already wired partially via hey-api). Fix INC-019: write a real MindShift → `character_events` bridge using the new schema. Pull MindShift repo into `apps/mindshift/` via `git subtree`. No visible user-facing change.

**Week 2 — Auth unification + Godot bridge.**
Add `packages/auth` as Supabase SSR + JWT wrappers. Life Sim Godot build starts reading `public.character_events` via Realtime WebSocket. Godot HTML5 build uses `JavaScriptBridge` to pick up web session from localStorage — proven pattern, tested indie-game case. Consent ledger becomes live: every `ai_decision_log` insert checks `consent_records` has a current row for that purpose.

**Week 3 — Observability triad + Inngest.**
Wire PostHog as central pane. Langfuse → PostHog export (hourly, Enriched observations source). Sentry → PostHog native source. For Python, use sentry_sdk v2.x so it doesn't grab OTEL. Add Inngest for 2-3 known async jobs: post-assessment score recompute, Telegram message batching, daily Atlas digest.

**Week 4 — BrandedBy concept scaffold + docs.**
With the kernel live, `apps/branded-by/` becomes a 3-day scaffold (Next.js page + one API route + consent record). DPIA v1 written covering all 5 products. AI Decision Log active for AURA scoring (Art. 22 right-to-explanation baseline). Constitution cross-ref'd.

End of month: 5 products in one repo, one identity, one event bus, one consent ledger, one observability pane. Migration status: Absorbed (Path A). Cost: ~0 AZN tooling, ~4 weeks Atlas time. Gate G1 of ecosystem redesign partially lifted.

---

## Open risks

- **Cal.com + t3-turbo verification is Level 2, not Level 3.** I didn't open their actual `package.json` and CI files this session. Before writing Path A day 1, read at least `calcom/cal.com` repo top-level + one `@calcom/ui` package to confirm the pattern.
- **RLS performance across 5 schemas in one Supabase project is not benchmarked.** If `character_events` gets heavy cross-product traffic, RLS lookup cost could degrade reads. Mitigation: Supabase performance advisor + composite indexes + a 1-week load test before MindShift/Life Sim production writes.
- **EU AI Act high-risk classification of AURA scoring** is not legally confirmed. If AURA is classified high-risk (likely, given employment effect), DPIA + human review + right-to-explanation are not nice-to-haves — they are launch blockers. This research pass assumed high-risk as precaution. A real legal review is still owed.
- **Azerbaijan PDPA alignment** not researched. Our first market. Possibility GDPR-equivalence is close but non-identical; research blocked by this session's 25-min budget.
- **Godot-in-monorepo case studies** are thin. The pattern (Godot as a subfolder, not a Turborepo member) is logical but has no battle-tested example in the sources pulled. A 1-day spike to import Life Sim into `apps/life-sim/` and build it once is the cheap de-risking move.
- **Path A is destructive to three git histories.** MindShift, Life Sim, BrandedBy repos become archived after `git subtree add`. If one of them ever needs to spin out as a separate product (e.g. BrandedBy to an acquirer), the monorepo becomes the extraction friction. Mitigation: keep the three original repos as mirrors, re-push archival tags quarterly.
- **Inngest free tier** is generous but not infinite. At 5-product scale we'll cross it within 6-12 months. Budget conversation then, not now.

End of summary. Word count: ~1580.
