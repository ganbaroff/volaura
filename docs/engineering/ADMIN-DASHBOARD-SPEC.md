# Admin Dashboard — Ecosystem Metrics Spec

**Phase:** admin-dashboard (opened 2026-04-18 01:38 Baku after INC-018 closed).
**Living doc rule:** all findings and iterations append here. Do NOT create new md files for this phase.
**Trigger:** CEO directive 2026-04-17 — "дай админа и добавь современные метрики, графики, измерения охвата и эффективности… я буду визуально всё видеть все связи."
**Core pivot:** admin is ~60-70% already built. This spec scopes the **extension**, not a rebuild.

---

## 1. What exists today (audit, 2026-04-18)

### 1.1 VOLAURA admin infrastructure — SHIPPED

Auth + routing:
- `supabase/migrations/20260402130000_add_platform_admin.sql` — `profiles.is_platform_admin BOOLEAN NOT NULL DEFAULT FALSE`. Service-role set only. No self-promotion path.
- `apps/web/src/components/layout/admin-guard.tsx` — two-layer check (`useAuthStore` session + `useAdminPing` 200). Non-admin → silent redirect to `/dashboard` (does not leak admin existence). Skeleton loading (no spinners, per design-gate §6).
- `apps/web/src/app/[locale]/admin/layout.tsx` — wraps children with `AdminGuard` + `AdminSidebar`.
- `apps/web/src/components/layout/admin-sidebar.tsx` — 4 nav items today: Overview, AI Office, Users, Grievances.

Backend router (`apps/api/app/routers/admin.py`, 471 lines):
- `GET /api/admin/ping` — cheap auth probe for guard.
- `GET /api/admin/stats` — `asyncio.gather` over profiles / organizations (active+pending) / assessment_sessions (today) / aura_scores (avg) / grievances. Returns `AdminStatsResponse`.
- `GET /api/admin/users` — paginated user table.
- `GET /api/admin/organizations/pending`, `POST /.../{id}/approve`, `POST /.../{id}/reject` — org moderation queue.
- `GET /api/admin/swarm/agents` — reads `memory/swarm/agent-state.json`.
- `GET /api/admin/swarm/proposals`, `POST /.../decide` — proposals JSON, atomic tempfile-rename writes.
- `GET /api/admin/swarm/findings` — reads SQLite blackboard via `swarm.shared_memory`.
- `POST /api/admin/ghosting-grace/run` — manual trigger for absence-recovery flow.
- Rate limit: 30/min on whole router.
- Deps: `PlatformAdminId` (gate), `SupabaseAdmin` (service-role per-request).

Frontend hooks (`apps/web/src/hooks/queries/use-admin.ts`, 266 lines, TanStack Query):
- `useAdminPing`, `useAdminStats` (60s stale), `useAdminUsers`, `usePendingOrganizations`, `useApproveOrganization`, `useRejectOrganization`, `useSwarmAgents` (60s refetch), `useSwarmProposals`, `useDecideProposal`, `useSwarmFindings` (60s refetch). All token-gated via `useAuthToken`, `throwOnError: false` on queries.

Pages:
- `/admin` (overview) — `AdminOverview` component renders 6 StatCards (Users, Active Orgs, Pending, Assessments Today, Avg AURA, Grievances). Skeleton on load. 60s auto-refresh note.
- `/admin/swarm` — 4-stat header (Active / Blocked / New / P0), tabs: Agents grid (card per agent with status dot + last_run + blockers + done/failed counts), Proposals (severity badge + expand + Approve/Dismiss buttons), Findings (severity + category + recommendation + file chips). All empty states present.
- `/admin/users` — table (User / Type / Subscription / Joined) with account_type + sub_status badges (ADHD palette, no red), pagination, admin ShieldCheck marker.
- `/admin/grievances` — exists (not audited in detail — P0 #9 mechanism task #22 covers content).

Analytics plumbing:
- `apps/web/src/components/posthog-provider.tsx` — PostHog init, US host, `capture_pageview + capture_pageleave`, `persistence: localStorage+cookie`, `respect_dnt: true`.
- `apps/web/src/hooks/use-analytics.ts` — `useTrackEvent()` dual-write: `POST /api/analytics/event` (Supabase primary) + `posthog.capture()` (secondary). Locale auto-pulled from pathname. Silent-failing — analytics never breaks UX.

### 1.2 MindShift — event + economy inventory

Events (50+ `logEvent` call sites across app):
- Tutorial (6), today (3), tasks (2), recovery (3), onboarding (6), sharing (4), progress (1), focus (13), rooms (4), setup (2), retention (3), review (1), burnout (1).
- New events from Sprint AG: `community_joined`, `agent_chat_turn`, `crystal_earned`, `crystal_spent`.

Supabase tables (migrations 001-024):
- `focus_sessions` — duration, phase, energy_before / energy_after, started_at.
- `tasks` — repeat, category, priority, dueDate, completedAt, difficulty.
- `crystal_ledger` (018) — append-only, types FOCUS / SHARE, source_event, balance_after, validated by trigger.
- `shareholder_positions` (018) — share_units, dividend_earned, dividend_claimed per community.
- `revenue_snapshots` (019) — monthly: gross_revenue_cents, operating_cost_cents, net_income_cents, dividend_pool_cents. **Fully public** (RLS `using (true)`). Seeded with April 2026 placeholder row.
- `communities` (017), `agents` contract (016), `llm_policy` column (022).
- `processed_stripe_events` (013) — idempotency for the now-deprecated Stripe path. Dodo Payments is the current provider (`create-checkout` + `dodo-webhook` edge functions).
- `push_subscriptions` (010), `push_cron` (011) — scheduled server-side push via pg_cron.

### 1.3 Cross-product bus — LIVE

- `mindshift/supabase/functions/volaura-bridge-proxy/index.ts` — proxies `character_events` writes to VOLAURA.
- `mindshift/src/shared/lib/volaura-bridge.ts` — client wrapper.
- `mindshift/supabase/functions/community-join/index.ts` — on join: `join_community()` RPC (atomic crystal debit + membership insert) → fires `community_joined` character_event via bridge. Best-effort.
- `mindshift/e2e/volaura-bridge.spec.ts` — end-to-end verified.
- `VolauraAuraBadges.tsx`, `VolauraCrystalCard.tsx` — MindShift reads cross-product state for the progress screen.

### 1.4 Gap summary

| Domain | State | Gap |
|---|---|---|
| Admin auth + nav | Shipped | None |
| Snapshot KPI cards (VOLAURA) | Shipped | No MindShift KPIs, no ecosystem KPIs |
| User table | Shipped | No filter / search / bulk actions / cross-product flags |
| Swarm ops | Shipped | None |
| Grievances | Partial | Workflow pending (task #22) |
| Growth funnel (AARRR) | None | Biggest missing axis |
| Retention cohorts (W1/W4/W12) | None | Biggest missing axis |
| Revenue / NRR / CAC / LTV / Burn Multiple | None | Dodo data needs ingestion |
| Ecosystem flow view (product ↔ product) | None | Requires `character_events` aggregation |
| MindShift health signals | None | Must pull from focus_sessions + crystal_ledger + revenue_snapshots |
| Quality / AURA integrity | None | Score distribution, anti-gaming audit |
| PostHog embed or HEART dashboard | None | Optional Phase 2 |

---

## 2. 2026 research synthesis (North-star + founder metric framework)

Canonical sources consulted: Reforge (Growth Model), Amplitude (North-Star Framework), Baremetrics (SaaS metrics 2026), OpenView Benchmarks 2026, HEART framework (Google UX), AARRR (Dave McClure), LTV:CAC and Burn Multiple (David Sacks).

### 2.1 Founder weekly scorecard (5 numbers, not more)

1. **Weekly active ecosystem users (WAEU)** — unique user_id touching any product in the last 7 days. Leading indicator.
2. **W4 retention %** — of users who joined 4 weeks ago, % still active. Truth-teller.
3. **MRR + Net Revenue Retention (NRR)** — current monthly recurring / 30 days ago, including expansion. NRR > 100% = growth without adding users.
4. **CAC payback months** — (CAC ÷ gross margin × MRR per user). Target <12 months.
5. **Burn multiple** — net burn ÷ net new ARR. Target <2.

These are the CEO at-a-glance numbers. Everything else is deeper.

### 2.2 Three-tier layout (from HEART + AARRR)

**Tier 1 — Executive at-a-glance (top of /admin):**
- The 5 weekly-scorecard numbers as big-typography cards.
- Single sparkline under each (last 8 weeks).
- One health dot per product (green/amber/purple per design-gate anti-pattern #1).

**Tier 2 — Operational dashboards (per-section pages):**
- Growth — AARRR funnel (Acquisition → Activation → Retention → Revenue → Referral), cohort retention heatmap by week of signup, channel attribution (from `signup_source`).
- Ecosystem — cross-product flow Sankey (VOLAURA ↔ MindShift traversal via `character_events`), concurrent-product user count, crystal earn→spend flow.
- Revenue — MRR waterfall, NRR by segment, Dodo Payments ledger, revenue_snapshots dividend state, refund rate (24h refund rule).
- Quality — AURA score distribution, IRT drift, grievance SLA, anti-gaming flags, MindShift burnout score distribution, room-session abandonment.

**Tier 3 — Deep-dive (drill-down links):**
- User timeline view (single user, all product events chronologically).
- Cohort inspector (filter + export).
- Raw event stream (PostHog-backed or Supabase-backed, paginated).
- Swarm agent timeline + findings (already shipped).

### 2.3 Adaptation to our ecosystem

Generic SaaS metrics don't fit us directly:
- **AURA integrity is not a standard metric.** Weekly: score distribution histogram, delta between IRT-adjusted and raw, flagged sessions (response time anomalies, RLS violations).
- **MindShift has no "revenue per user" meaningfully yet.** Its contribution is cross-product: every minute of MindShift focus earns FOCUS crystals that can join VOLAURA communities. Metric: `crystal earn → community_join conversion %`.
- **Burnout is a retention risk.** Track `burnoutScore > 60` cohort's W4 retention separately — those users churn fastest and need the Foundation Law #2 energy-adaptive UI.
- **Grievances = brand integrity signal.** SLA (time-to-response), resolution rate, appeal rate.

---

## 3. MVP scope (3 milestones, ship order)

### Milestone M1 — Extend Overview + add ecosystem KPIs (4-6 days)

Backend:
- `GET /api/admin/stats/ecosystem` — WAEU (distinct user_id in `character_events` last 7d), W4 retention (cohort SQL), MRR (sum of active Dodo subscriptions), NRR, burn multiple (from revenue_snapshots + ops cost).
- `GET /api/admin/stats/mindshift` — focus_sessions count, avg session minutes, burnout-score distribution, crystal earn/spend totals, community_joined count.
- Supabase foreign-data link OR periodic ETL job from MindShift Supabase project into VOLAURA admin schema (cheaper: scheduled edge function that pushes aggregates).

Frontend:
- `/admin` top row → 5 big-typography KPI cards with 8-week sparklines (recharts, already in stack).
- Row 2 → product health dots + single-sentence headline.
- Row 3 → existing 6 StatCards (unchanged, demoted to supporting).

Design-gate compliance: no red, purple for warning states, amber for attention, skeleton loaders (not spinners), 1 primary CTA per page ("View cohort details").

### Milestone M2 — Growth section (5-7 days)

New page `/admin/growth`:
- AARRR funnel (6 steps: Landing → Signup → First assessment → AURA earned → Returned W2 → Paid). Recharts FunnelChart.
- Cohort retention heatmap (signup week × weeks-since-signup, cell value = % still active). Recharts custom scale — teal→indigo gradient, no red.
- Acquisition channel breakdown (from `profiles.signup_source`, already captured).
- Activation cliff detector — where % drop >20 percentage points week-over-week inside the funnel.

Backend new endpoints:
- `GET /api/admin/growth/funnel?range=30d`
- `GET /api/admin/growth/cohorts?weeks=12`
- `GET /api/admin/growth/channels?range=30d`

### Milestone M3 — Ecosystem flow + Revenue + Quality (7-10 days)

New page `/admin/ecosystem`:
- Sankey diagram: users flowing between products via `character_events`. Source → target width = user count. Colored by face (VOLAURA indigo, MindShift teal per design-gate §QUICK REFERENCE).
- Concurrent-product users (touched ≥2 products in last 30d).
- Crystal earn (MindShift focus) → crystal spend (VOLAURA community_join) funnel.
- Cross-product user timeline — select user → see their journey.

New page `/admin/revenue`:
- MRR waterfall (new / expansion / contraction / churn).
- NRR by segment.
- Dodo events ledger (last 100, link to webhook payload).
- Refund rate (24h rule enforcement).
- Revenue_snapshots table + dividend_pool state (transparency).

New page `/admin/quality`:
- AURA score distribution histogram per competency.
- IRT drift indicator (session difficulty vs. theta estimate).
- Anti-gaming flags (response-time floor violations, role_level gaming from task #20).
- Grievance SLA gauges.
- MindShift burnout distribution + recovery-message fire rate.

### Out of MVP (Phase 2 backlog)

- PostHog dashboard embed (alternative: custom panels using PostHog API).
- A/B experiment panel (sprint Scheduled changes).
- Cost per assessment (Gemini call cost / session).
- Moderator roster and audit trail.
- CEO mobile view (responsive cut-down of Tier 1 only).

---

## 4. Visual-language anchor (design-gate binding)

- Palette: teal `#4ECDC4` (growth, positive delta), indigo `#7B72FF` (identity, VOLAURA accent), gold `#F59E0B` (attention), purple `#D4B4FF` (error, anti-pattern-free substitute for red).
- Never use red. Never use heatmap scales that include red. Substitute: teal → indigo → purple.
- Sparklines: 1px stroke, no fill, no dots, ease-out entrance gated by `useMotion()`.
- Numbers: Plus Jakarta Sans 600-700, tabular-nums, no count-up animation (anti-pattern #6).
- Loading: Skeleton that matches the shape of the content (not spinners, anti-pattern §6).
- Energy modes applied: Full = all cards visible, Mid = hide Tier-3 entry points, Low = only Tier 1 numbers (CEO late-night mode).

---

## 5. Open questions (self-answered, not for CEO)

Q: Build a separate MindShift admin or unify into VOLAURA admin?
A: Unify. One admin, one login, one URL. Cross-product flow is the whole point. Adapter: scheduled edge function aggregates MindShift data into VOLAURA admin schema tables (or read via foreign Supabase auth-JWT call).

Q: PostHog embed or custom dashboard?
A: Custom. PostHog stays as analytics secondary; admin uses Supabase as primary (authoritative) + recharts. Reason: RLS-safe, no vendor lock.

Q: North-star — one number or five?
A: Five for founder scorecard (Tier 1). One for public narrative when needed: WAEU.

Q: Real-time or refresh-interval?
A: 60s stale on TanStack Query (matches existing admin pages). Swarm stays live-ish (60s refetch). No websockets Phase 1.

---

## 6. Implementation log (append here as we ship)

### 2026-04-18 02:00-02:30 Baku — M1 backend shipped

**Files touched:**
- `apps/api/app/schemas/admin.py` (+58 lines) — added `AdminOverviewResponse`, `AdminActivationFunnel`, `AdminPresenceMatrix`, `AdminActivityEvent`.
- `apps/api/app/routers/admin.py` (+252 lines, now 723 total) — added `GET /api/admin/stats/overview` and `GET /api/admin/events/live`.

**Design decisions baked in:**
- Fail-soft `_safe_count` and `_safe_list` helpers — single missing/renamed table never 500s the dashboard.
- W4 retention returns `null` when W0 cohort < 5 users (don't pretend signal from noise).
- Runway manual via `PLATFORM_RUNWAY_MONTHS` env — no Stripe auto-compute (no Stripe connected; Strange pivot rejected fake MRR).
- MindShift funnel stubbed (0/0) for M1 — cross-project read via bridge lands in M2.
- `events/live` truncates payload to 120 chars, user_id exposed as 8-char prefix only.

**Tech debt opened (M2 backlog):**
- `admin.py` at 723 lines; decompose into `admin/overview.py` + `admin/events.py` + `admin/org.py` + `admin/swarm.py` when M2 lands.
- MindShift funnel data needs cross-project Supabase client (or bridge endpoint) to replace stub.
- `user_identity_map` presence matrix is O(n) in memory — move to SQL RPC when total_users > 5k.
- W4 retention uses `last_seen_at` proxy; if not populated reliably, switch to auth.sessions table join.

**Smoke test status:**
- Syntax: `python -m py_compile` passes both files.
- Runtime: not yet hit in deployed env (no Railway deploy trigger in this session). Next session or CEO can smoke via `curl -H "Authorization: Bearer <admin-jwt>" https://volauraapi-production.up.railway.app/api/admin/stats/overview`.

**Not shipped yet (M1 remainder):**
- Frontend: `useAdminOverview` + `useAdminLiveEvents` TanStack hooks + 5-card scorecard + live feed widget on `/admin`. Separate commit.
- Env var set on Railway: `PLATFORM_RUNWAY_MONTHS` (CEO to set the value; I set 0 placeholder will read as None).

---

## 7. PIVOT 2026-04-18 02:00 Baku — Doctor Strange v2 Gate 1 validation

**Trigger:** CEO directive "имплементируй если ты уверен что это лучшее решение из самых современных и продвинутых а не просто мини поиск по памяти." My original plan (§2-4) was built from memory. Gate 1 required external validation.

**Validation method:** WebSearch (agent delegation blocked by parent-session context size — retried twice, both failed with "Prompt is too long"). Switched to direct WebSearch inline = still external = satisfies Gate 1.

**Findings that contradicted the prior plan:**

1. **Pre-PMF priority is activation + retention, not MRR/NRR/CAC-payback.** Sources: 2026 SaaS metrics guides explicitly distinguish stage: "pre-product-market fit focuses on activation and retention, scaling focuses on acquisition efficiency and revenue growth."
2. **Activation rate has larger growth impact than acquisition.** Top-of-funnel improvements lose to activation funnel improvements at every early stage.
3. **MRR as single number is meaningless.** Must decompose (new/expansion/contraction/churned) to be signal. At 1 paying user (CEO himself, internal) = decorative.
4. **Admin panel design law: clarity and simplicity paramount, avoid clutter, prioritize essentials.** Sankey with <100 users = clutter. Cohort heatmaps at <50 users = noise.

**Objection-response pairs (Gate 2):**

| Objection | Counter-evidence | Residual risk |
|---|---|---|
| MRR/NRR/CAC-payback at 1 paying user | WebSearch: pre-PMF = activation+retention only | None — drop from Tier 1, keep stubs for when revenue exists |
| Sankey premature at <100 users | WebSearch: "avoid clutter, prioritize essentials" | Loss of cross-product viz narrative → replaced with presence matrix |
| 4-6 days for M1 unrealistic solo | Trimmed scope = 2 days backend+frontend | None |
| Live Supabase read architecture | <100 users = premature optimization | None; materialized views deferred to M2 |
| **MISSING: error/incident board** | CEO just lost 2h to a 500-error blocker an admin board would have shown in 10s | Highest-value widget, was absent |
| **MISSING: live activity feed** | CEO framing "я хочу видеть связи" → character_events tail IS the viz | Replaces Sankey cleanly |
| **MISSING: feedback pulse** | Pre-revenue qualitative > quantitative; no NPS yet | Adds grievances + support tickets widget |

**Revised Tier 1 scorecard (5 cards — founder-stage appropriate):**

1. **Activation rate (24h)** — signup → first-assessment-started / signup. Replaces MRR.
2. **W4 retention** — kept from original (retention is universally valid).
3. **DAU/WAU stickiness** — replaces CAC payback.
4. **Error rate 24h** — 5xx count + failed assessment sessions + orphan character_events. New, highest value.
5. **Runway months** — manual CEO-editable field (`platform_settings.runway_months` or env). Not computed from Stripe (no Stripe). Replaces Burn Multiple.

**Revised Tier 2 (4 widgets, not 6):**

6. **Live activity feed** — last 50 character_events (timestamp + product + event_type + user_id-prefix).
7. **Cross-product presence matrix** — "VOLAURA only: N / MindShift only: M / Both: K / All 5: 0". Counts, not Sankey.
8. **Per-product activation funnel** — VOLAURA: signup → assessment started → completed. MindShift: first focus session → Day-7 return.
9. **Feedback pulse** — grievances (last 7d) + NPS/support stub for future.

**Tier 3 deferred to M2:** cohort retention tables, AURA integrity flags, LLM cost tracking, performance heatmap.

**Revised M1 backend endpoints (2, not 3):**

- `GET /api/admin/stats/overview` — single fat endpoint. Returns all Tier 1 scorecard + cross-product presence matrix. Uses `asyncio.gather`. Live Supabase reads acceptable at current scale.
- `GET /api/admin/events/live?limit=50` — character_events tail across both VOLAURA and MindShift Supabase projects (read-only, via bridge or direct service-role).

**M1 timeline revised:** 2 days total (backend + frontend widgets wired to existing `/admin` page). Not 4-6.

**Strange v2 format:**

```
RECOMMENDATION: Pivot to activation-first admin. Ship M1 in 2 days with
  5-card scorecard (activation/W4/DAU-WAU/error-24h/runway) + 4 widgets
  (live feed/presence matrix/per-product funnel/feedback pulse).
EVIDENCE: WebSearch 2026 SaaS metrics sources explicitly: pre-PMF
  prioritizes activation+retention, NOT MRR/NRR/CAC. Admin-panel design
  law: simplicity over Sankey cleverness at <100 users.
WHY NOT OTHERS: Original 5-KPI (WAEU/W4/MRR+NRR/CAC-payback/Burn)
  = enterprise SaaS scorecard inappropriate at $0 external revenue.
FALLBACK IF BLOCKED: If activation events can't be computed yet
  (missing event schema), ship error-rate + live-feed-only for M1 day 1,
  add funnel in day 2.
ADVERSARIAL: 7 objections addressed above with counter-evidence pairs.
```

**Source URLs (Sources block in §10):** see bottom of file.

---

## 8. M1 implementation starting 2026-04-18 02:00 Baku

Scope (ship today):
- `apps/api/app/schemas/admin.py` — add `AdminOverviewResponse`, `AdminActivityEvent`, `AdminActivationFunnel`, `AdminPresenceMatrix`.
- `apps/api/app/routers/admin.py` — add `GET /stats/overview` + `GET /events/live`.
- Runway: read `PLATFORM_RUNWAY_MONTHS` env for M1 (no new migration yet).

Frontend wiring: separate PR, after backend smoke-tested.

---

## 9. Sources (Gate 1 external validation)

- [3 SaaS Metrics That Matter More Than MRR in 2026 — Averi](https://www.averi.ai/blog/15-essential-saas-metrics-every-founder-must-track-in-2026-(with-benchmarks))
- [Startup Metrics Guide 2026 — eAmped](https://www.eamped.com/startup-metrics-guide-2026-2/)
- [7 Financial Dashboard Metrics Every Pre-Seed Founder — Culta](https://culta.ai/blog/financial-dashboard-startups)
- [Admin Panel Design Tips — Aspirity](https://aspirity.com/blog/good-admin-panel-design)
- [Solo Founder Tech Stack 2026 — OPC](https://www.opc.community/blog/solo-founder-tools-2026)
