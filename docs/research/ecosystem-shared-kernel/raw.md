# Raw research — ecosystem shared kernel — 2026-04-15

Input task: CEO directive 2026-04-15 "мысли широко в рамках экосистемы а не только volaura". Research how single-founder multi-product ecosystems share their foundation in 2024-2026, across 10 dimensions.

Memory gate: task-class=research-architecture · SYNC=✅ · BRAIN=❌(absent, PORTABLE-BRIEF substituted) · sprint-state=✅ · extras=[PORTABLE-BRIEF, ECOSYSTEM-REDESIGN-2026-04-15/STATE, research-first rule].

Context recap (from memory):
- 5 products: VOLAURA (Next.js+FastAPI, main repo), MindShift (separate repo, PWA), Life Simulator (Godot 4, separate), BrandedBy (concept, no code), ZEUS/Atlas (`packages/swarm/` inside VOLAURA).
- Shared today: one Supabase Auth project (VOLAURA's). `character_events` table nominally shared but only VOLAURA writes. MindShift bridge = INC-019 "half-broken".
- Constraint: solo founder + ADHD + ~1000 AZN to month-end. 3-filter rule (free path / 10× result / cash).
- Constitution supreme; never-red, energy adaptation, shame-free language are shared foundations already.

Research method: WebSearch across 10 questions, parallelized. Sources cited inline. Where I didn't reach Level 3 (GitHub Issues, CHANGELOG) I mark as Level 1-2 and flag as "needs deeper verify before adoption".

---

## Q1. Monorepo for polyglot multi-product (Python + Next.js + Godot + Expo)

**Key finding:** Turborepo vs Nx is a real fork for polyglot. Turborepo officially supports only JS/TS — Python is treated as opaque shell-exec. Nx has first-party Python plugins (UV, Poetry) and a cross-language dependency graph.

- Turborepo: minimal, pnpm-native, fast for TS-only. Poor fit once Python is first-class. Source: Aviator, stevekinney.com, Nx docs.
- Nx: heavier, first-party Python/Rust/Go/.NET plugins, task sandboxing, tag-based module boundaries. In 4-machine distributed CI benchmark Nx was ~16% faster than Turborepo. Source: pkgpulse 2026 benchmark, nx.dev.
- pnpm workspaces alone: only viable for small repos. No task graph.
- Bazel/Pants: correct for true polyglot but operational burden too high for solo.

**Community conclusion (2026):** "start with Turborepo, migrate to Nx when cross-language affected detection matters." For us, Python is first-class (FastAPI + `packages/swarm/`), so Nx is the more honest pick — but migration cost from current Turborepo + pnpm is non-trivial.

**Godot/Expo angle:** no search result treated Godot as a monorepo member. Godot typically lives as its own project (standalone repo or `apps/game/` directory used only as a checkout — Nx/Turbo don't manage GDScript builds). Practical pattern: keep Godot project as a subfolder (`apps/life-sim/`) with its own build via Godot CLI, ignored by task graph, and only share `packages/events` + `packages/types` as JSON schemas.

Sources: https://www.aviator.co/blog/monorepo-tools/ , https://nx.dev/docs/guides/adopting-nx/nx-vs-turborepo , https://www.pkgpulse.com/blog/turborepo-vs-nx-monorepo-2026 , https://daily.dev/blog/monorepo-turborepo-vs-nx-vs-bazel-modern-development-teams

---

## Q2. Shared Supabase schema across products

**Official Supabase guidance (2025):** for *environments* of one product → single project + branching. For *distinct products* → separate Supabase projects.

Key quote (supabase docs + GitHub discussions): "projects are separate server instances... each runs on a server with its own database, PostgREST, gotrue, storage."

**Implication for VOLAURA ecosystem:** if all 5 products want shared *identity* + shared *event stream*, separate projects is the wrong shape — it fragments auth.users and means `character_events` can't exist as one cross-product table.

**Recommended pattern for multi-product sharing one identity:** single Supabase project, **schema separation** (`volaura.*`, `mindshift.*`, `life_sim.*`, `branded_by.*`, `atlas.*` schemas) with **public** schema holding the cross-cutting tables: `public.profiles`, `public.character_events`, `public.crystals`, `public.consent_records`. RLS policies per-schema. Branching used per-PR for each product's schema.

**Migration risk:** Supabase self-host discussion (#38048) flagged that "each project duplicates services" which is expensive — validating the shared-project pattern for solo founders.

**Cost:** branches are billed as full instances. Solo founder should run at most 1-2 persistent branches (dev + staging) and kill ephemeral per-PR branches within 24h.

Sources: https://supabase.com/docs/guides/deployment/branching , https://github.com/orgs/supabase/discussions/27860 , https://github.com/orgs/supabase/discussions/38048 , https://supabase.com/docs/guides/deployment/managing-environments

**Needs Level 3 verify:** RLS performance across 5 schemas in one project. Not researched yet.

---

## Q3. Event bus for 5-runtime polyglot (Python/TS/GDScript/Expo/FastAPI)

**Finding:** Inngest, Trigger.dev, and NATS serve different jobs. None of them natively speak GDScript or Expo — they all require an HTTP or WS client.

- **Inngest** — event-driven durable step functions. Compute stays on your side (Vercel, Lambda, FastAPI container). Inngest owns event ingestion, retries, state. TS + Python SDKs (Python SDK is official). Good fit when you want existing FastAPI handlers to stay FastAPI handlers.
- **Trigger.dev v3** — runs the compute itself (their infra). Great DX but less control. TS-first. Python SDK exists but less mature.
- **NATS/JetStream** — true pub/sub bus. Low latency. No built-in retry UI, no observability UI. Self-host burden. Overkill for 5-product solo founder.
- **Supabase Realtime** (not in search, prior knowledge) — postgres-changes broadcast. Already available to us free. For event fan-out between 5 products it can work: each product `SUBSCRIBE` to `character_events` inserts via Realtime.

**Best fit for our stack:** Hybrid — **Supabase Realtime for cross-product broadcasts** (free, already paid for, works in Godot via WebSocket, works in Next.js/Expo via `@supabase/supabase-js`, works in Python via `realtime-py`), **Inngest for internal async jobs** (assessment evaluation, AURA recompute, Telegram webhook follow-ups).

NATS rejected for solo founder — operational burden.

Sources: https://www.inngest.com/ , https://trigger.dev/ , https://trybuildpilot.com/610-trigger-dev-vs-inngest-vs-temporal-2026 , https://openalternative.co/compare/inngest/vs/trigger

---

## Q4. Shared TypeScript + Python type definitions

**Finding:** OpenAPI is the canonical interchange for polyglot type sharing in 2025. FastAPI auto-generates OpenAPI 3.1; `@hey-api/openapi-ts` is officially recommended in FastAPI docs for TS codegen, and it generates TanStack Query hooks + Zod schemas.

We already do this (partially) in VOLAURA main repo. The missing piece: **MindShift, Life Sim, BrandedBy don't consume the same `openapi.json`.** Each reimplements types by hand.

**tRPC rejected:** TS-only, excludes Python backend.
**Protobuf/gRPC rejected:** too heavy, bad DX for Godot, no real gain over OpenAPI for our scale.
**Prisma-style cross-runtime:** no polyglot story.

**Recommended pattern:** publish `packages/api-sdk-ts` (generated from `apps/api` openapi.json) + `packages/api-sdk-py` (for swarm/ZEUS/any Python caller) + `packages/events-schema` (JSON Schema for `character_events` payloads, language-neutral). All 5 products depend on these.

**Godot consumption:** Godot doesn't run npm; it can import JSON Schema files at build time for validation. Types are still human-typed in GDScript but the runtime validator ensures agreement.

Sources: https://fastapi.tiangolo.com/advanced/generate-clients/ , https://github.com/hey-api/openapi-ts , https://openapi-generator.tech/docs/generators/

---

## Q5. Cross-product identity + consent

**Finding:** No published "ecosystem consent kit" architecture exists as an off-the-shelf product. WorkOS AuthKit and Clerk both ship *authentication*, not *consent ledger*. Consent is GDPR-scoped and needs your own table.

- **WorkOS AuthKit** — enterprise SSO focus, 1M MAU free, $125/connection for SSO. Overkill for B2C ecosystem today.
- **Clerk** — polished consumer auth, Next.js-optimal, multi-session/multi-org built-in. $25/mo after 10k MAU.
- **Supabase Auth** (our current) — free, RLS-native, supports third-party JWT trust (Clerk/Auth0/Firebase can issue JWTs Supabase trusts).

**Recommendation:** keep Supabase Auth as the shared identity plane for all 5 products (it's already working, free, and all products talk to Supabase anyway). Add a `public.consent_records` table (user_id, purpose, granted_at, revoked_at, version, product_scope) as the shared consent ledger. Each product checks `consent_records` before processing — not each maintains its own.

**Migration:** zero churn — we already have Supabase Auth project. Add consent table + RLS policies + shared TS/Python helper `hasConsent(userId, purpose)`.

Sources: https://workos.com/compare/clerk , https://clerk.com/articles/the-best-apis-for-secure-user-authentication , https://supabase.com/docs/guides/auth/third-party/overview

---

## Q6. t3-turbo / SST / Vercel templates — canonical shared packages

**Finding (t3-turbo):** canonical shared-kernel packages are exactly 4:
- `packages/api` — tRPC routers (we'd substitute OpenAPI SDK)
- `packages/auth` — Better Auth (we'd substitute Supabase helpers)
- `packages/db` — Drizzle schema (we'd substitute Supabase types + schema)
- `packages/ui` — shadcn-ui components (applicable 1:1)

Plus `tooling/`: eslint, prettier, tailwind, typescript.

**Apps:** `apps/nextjs`, `apps/expo`, `apps/tanstack-start` — note Expo is a first-class citizen. This is evidence that the **pattern of "one monorepo holds web + mobile + shared kernel" is industry-standard in 2025-2026.**

**Gap in t3-turbo for our case:** no Python app, no Godot app. But the *pattern* transfers: adopt the 4-package shared kernel shape and extend with `packages/events-schema` + `packages/consent` + `packages/types-py` (Python-importable mirror of `packages/types`).

Source: https://github.com/t3-oss/create-t3-turbo

**Cal.com cross-check:** Cal.com's monorepo uses `@calcom/prisma`, `@calcom/trpc`, `@calcom/features`, `@calcom/app-store`, `@calcom/ui`, `@calcom/lib` — same 4-core pattern plus domain packages. Cited as reference-grade monorepo. Source: https://handbook.cal.com/engineering/codebase/monorepo-turborepo , https://cal.com/docs/developing/open-source-contribution/contributors-guide

---

## Q7. Observability across 5 products, one founder

**Finding:** Industry pattern is **PostHog as central pane**, **Langfuse for LLM traces feeding into PostHog**, **Sentry for errors feeding into PostHog** via native data pipeline sources.

Integration specifics:
- Langfuse → PostHog: hourly batch export, "Enriched observations" source recommended, AI Metrics template dashboard prebuilt.
- Sentry → PostHog: native Data Pipeline source.
- Sentry + Langfuse coexistence: both claim global OTEL provider, conflict. Solo-founder fix: `sentry_sdk` v2.x for Python (doesn't use OTEL), `skipOpenTelemetrySetup: true` for Node.
- Langfuse multi-project: experimental multi-project support documented.

**Project layout:** one org per tool + one project per product = 5 projects in each of PostHog/Sentry/Langfuse. Free tiers work: PostHog 1M events/mo, Sentry 5k errors/mo, Langfuse 50k traces/mo.

Sources: https://posthog.com/docs/ai-engineering/langfuse-posthog , https://posthog.com/docs/cdp/sources/sentry , https://langfuse.com/faq/all/existing-sentry-setup , https://langfuse.com/docs/analytics/posthog

---

## Q8. GDPR Art.22 + AI Act as shared foundation

**Finding:** the AI Act is intentionally *thin* on consent — it leans on GDPR. So consent is a GDPR mechanism; AI Act mandates *human oversight* (Art. 14) and *right to explanation* (Art. 86) for high-risk systems. These are parallel regimes and **both** need shared infra.

Key architecture implications for our ecosystem:
1. **Per-product data segregation required**: data cannot be pooled freely across products without separate lawful bases. I.e. MindShift reflection data ≠ VOLAURA assessment data, even for the same user, unless consent is explicit and purpose-specific.
2. **November 2025 Digital Omnibus** proposed Art. 88b: machine-readable preference/consent signalling — if adopted, this becomes the standard for cross-product consent exchange. Future-proofing argument for a structured consent ledger today.
3. **Low/minimal risk AI systems still trigger Art. 22** if they make solely-automated decisions with significant effect. Our AURA score influences employment matching → likely significant → Art. 22 + right to human review required.
4. **Auditability is architectural**: logs of (input, output, decision, human override) must be retained.

**Shared foundation minimum:** `consent_records` table, `ai_decision_log` table, `human_review_queue` table — all in `public` schema, shared across 5 products. One DPIA covering the whole ecosystem, versioned in `docs/compliance/DPIA-vX.md`.

Sources: https://www.taylorwessing.com/en/global-data-hub/2025/eu-digital-laws-and-gdpr/gdh---the-eu-ai-act-and-the-gdpr , https://www.tandfonline.com/doi/full/10.1080/23311886.2025.2560654 , https://www.tandfonline.com/doi/full/10.1080/17579961.2026.2633677 , https://www.euaiact.com/key-issue/6

**Needs Level 3 verify:** Azerbaijan PDPA overlap with GDPR — we serve AZ market first. Not researched in this batch.

---

## Q9. Actual companies with 5+ products, published architecture

**Cal.com** — open-source, ~1 company with multiple products (Cal Video, Cal Insights, Cal Routing, Cal.ai, Cal Atoms). All in one monorepo, `@calcom/*` namespace, 4-core shared packages + domain packages. Reference-grade public example.

**Supabase itself** — Auth, Storage, Realtime, Edge Functions, Database are all one project scope — not different products but different services behind one API. Each has its own repo under `supabase/*` GitHub org, but deployed as coordinated services.

**Others** (PostHog, Raycast, Plausible) — not deeply researched in this batch.

Key transferable: Cal.com model (monorepo + shared kernel + domain packages) is the closest to what we want. They make `@calcom/prisma` the "high in tree" package because DB touches everything. Our equivalent = `packages/db` (Supabase schema + generated types).

Source: https://github.com/calcom/cal.com , https://handbook.cal.com/engineering/codebase/monorepo-turborepo

**Needs Level 3:** direct read of Cal.com `package.json` + workflow files. Flagged for follow-up.

---

## Q10. Godot ↔ Next.js ↔ FastAPI ↔ Expo ↔ Python swarm

**Finding:** no one-template-fits-all exists for this exact combo. The pattern that emerges from 5 sources:

1. **Identity shared via Supabase JWT** — Godot speaks REST with `Bearer <JWT>` header, Expo/Next use supabase-js, FastAPI verifies JWT server-side, swarm fetches service-role key. Single auth.users table. This is proven and used by multiple indie devs.
2. **Events shared via one of:**
   - Supabase Realtime `postgres_changes` on `character_events` (free, works in all 5 runtimes via WebSocket)
   - Webhook fan-out from FastAPI (explicit, traceable, costs nothing)
   - Inngest for Python/TS, HTTP callback for Godot (over-engineered for our scale today)
3. **Types shared via JSON Schema files** that live in `packages/events-schema` and are consumed by: TS (Zod), Python (Pydantic model_validate), Godot (runtime validator), FastAPI (at endpoint boundary).
4. **Godot in HTML5 build** can read the web app's `localStorage` via `JavaScriptBridge` to piggyback the existing session — proven pattern.

**Migration cost:** Godot side mostly untouched — just add `Supabase.auth` addon OR hand-written HTTPRequest helper. Expo and Python swarm already talk to Supabase. Only new build artifact: `packages/events-schema`.

Sources: https://supabase.com/docs/guides/auth/architecture , https://godotengine.org/asset-library/asset/1552 , https://github.com/supabase/auth , https://supabase.com/docs/guides/auth/third-party/overview

---

## Cross-cutting verdicts

| Pattern / tool | Verdict | Evidence quality | Migration cost |
|---|---|---|---|
| Turborepo (kept) | **keep for now, reconsider at 10k LOC Python** | L1-L2 | n/a |
| Nx | **learn-only**, migrate only if cross-language affected-detection blocks us | L1-L2 | 2-4 weeks |
| Supabase branching (per-product env) | **adopt** on our existing single project | L2 | 1 day |
| Supabase multi-project (separate per product) | **reject** — fragments identity | L2 | n/a |
| Schema-per-product inside one Supabase project | **adopt** — canonical pattern | L2 | 2-3 days migrations |
| Inngest | **adopt for internal async jobs** | L1 | 2 days wiring |
| Trigger.dev | **learn-only** — hosted-runtime risk | L1 | n/a |
| NATS | **reject** — ops burden | L1 | n/a |
| Supabase Realtime as event bus | **adopt** for cross-product fan-out | L1 + prior | 1 day |
| `@hey-api/openapi-ts` | **keep (already used) + extend to MindShift/BrandedBy** | L2 | 1 day per product |
| tRPC / Protobuf | **reject** — polyglot mismatch | L1 | n/a |
| `packages/events-schema` (JSON Schema) | **adopt** — new package | L1 | 2 days |
| Clerk / WorkOS | **reject for now** — Supabase Auth sufficient | L2 | n/a |
| `public.consent_records` ledger | **adopt** | L3 (regulatory) | 1 day |
| PostHog + Sentry + Langfuse triad | **adopt** — all free tier | L2 | 1 day per product |
| Cal.com monorepo pattern (4-core + domain packages) | **absorb-pattern** | L2 | ongoing |
| t3-turbo package layout | **absorb-pattern** | L2 | ongoing |

---

## Evidence-quality gaps to close before committing

- L3 check on Cal.com actual package.json + turborepo pipeline — read `calcom/cal.com` repo directly.
- L3 check on Supabase RLS performance when 5 schemas share one project (find 1 real production postmortem).
- L3 check on Nx Python plugin (UV) in a FastAPI + Next.js repo — find at least 1 case study.
- L3 check on Azerbaijan PDPA vs GDPR overlap — our jurisdiction.
- Real-world Godot-in-monorepo case study (not marketing).

If any of the above flip red, specific line-items in the summary must be revisited.
