# Phase 1 Discovery — Ecosystem Audit

**Date:** 2026-04-16 14:05 Baku
**Author:** Atlas (Cowork)
**Purpose:** Complete inventory of what exists before any Figma work begins

---

## 1. FRONTEND INVENTORY (apps/web/)

### 1.1 Routes — 55 pages

**Auth (4):** login, signup, forgot-password, reset-password

**Dashboard (35):**
- Core: dashboard, profile, profile/edit, settings, onboarding, welcome, notifications
- Assessment: assessment (list), assessment/info/[slug], assessment/[sessionId] (active), /questions, /complete
- AURA: aura (results), aura/contest
- Discovery: discover, leaderboard
- Events: events/create, events/[eventId]/attendees, events/[eventId]/checkin
- Organization: my-organization, my-organization/invite, org-volunteers
- Subscription: subscription/success, subscription/cancelled
- Ecosystem products: atlas, brandedby, brandedby/generations/[id], life, mindshift
- Ops module: ops/admin, ops/drafts, ops/incidents, ops/incidents/create, ops/incidents/[id], ops/now, ops/operations

**Public (7):** events, events/[eventId], invite, organizations, organizations/[id], u/[username], u/[username]/verify/[sessionId], verify/[token], privacy-policy

**Admin (4):** admin, admin/grievances, admin/swarm, admin/users

**Other (2):** callback, welcome

### 1.2 Components — 78 .tsx files

| Category | Count | Key Components |
|----------|-------|----------------|
| assessment/ | 12 | energy-picker, question-card, mcq-options, open-text-answer, rating-scale, progress-bar, timer, transition-screen, safety-block, pre-assessment-summary, coaching-tips, competency-card |
| aura/ | 7 | badge-display, competency-breakdown, evaluation-log, liquid-glass-radar, radar-chart, share-buttons |
| dashboard/ | 7 | activity-feed, aura-score-widget, crystal-balance-widget, feed-cards, stats-row, tribe-card |
| landing/ | 7 | hero-section, features-grid, how-it-works, impact-ticker, landing-nav, landing-footer, org-cta, sample-aura-preview |
| layout/ | 10 | admin-guard, admin-sidebar, auth-guard, bottom-nav, energy-init, language-switcher, realtime-notifications, sidebar, skip-to-content, top-bar |
| profile/ | 3 | challenge-button, intro-request-button, profile-view-tracker |
| profile-view/ | 5 | activity-timeline, expert-verifications, impact-metrics, profile-header, skill-chips |
| ui/ | 9 | alert, avatar, button, card, empty-state, product-placeholder, skeleton, social-auth-buttons, toast |
| events/ | 2 | event-card, events-list |
| navigation/ | 1 | bottom-tab-bar |
| other | 5 | query-provider, translations-provider, utm-capture, community-signal-inline, crystal-shop |

### 1.3 State Management

**Stores (3):** assessment-store, auth-store, ui-store

**Query hooks (20):** use-admin, use-assessment, use-aura, use-aura-explanation, use-auth-token, use-brandedby, use-character, use-community-signal, use-dashboard, use-events, use-grievance, use-lifesim, use-notifications, use-organizations, use-profile, use-public-stats, use-skill, use-subscription, use-tribes

**Custom hooks (4):** use-analytics, use-energy-mode, use-ops-sse, use-reduced-motion

### 1.4 i18n

- AZ: 1015 lines in common.json (primary)
- EN: 978 lines in common.json
- Single namespace: common
- Gap: ~37 keys exist in AZ but not EN (or vice versa)

### 1.5 Design System (globals.css — 450 lines)

3-tier token architecture fully implemented:
- Tier 1: Primitives (surfaces, primary, secondary, tertiary, error=purple, warning=amber)
- Tier 2: Semantic (on-surface, outline, focus-ring, badge tiers)
- Tier 3: Product (volaura=#7C5CFC, mindshift=#3B82F6, lifesim=#F59E0B, brandedby=#EC4899, zeus=#10B981)
- Energy system: CSS variables via [data-energy] attribute (spacing, density, animation, min-target)
- Typography: Inter (body) + Plus Jakarta Sans (headlines)
- Constitution compliance: prefers-reduced-motion kills all animation, [data-energy="low"] does same
- Liquid glass, badge glow, mesh gradient hero — all CSS-only

### 1.6 Dependencies (23 production)

@formkit/auto-animate, @hey-api/client-fetch, @hookform/resolvers, @number-flow/react, @radix-ui/react-slot, @supabase/ssr, @supabase/supabase-js, @tanstack/react-query, class-variance-authority, clsx, framer-motion, i18next, i18next-resources-to-backend, lucide-react, next, next-i18n-router, react, react-dom, react-hook-form, react-i18next, recharts, tailwind-merge, zod, zustand

---

## 2. BACKEND INVENTORY (apps/api/)

### 2.1 Routers — 34 Python files

| Router | Domain | Key endpoints |
|--------|--------|---------------|
| health | Infra | GET / |
| auth | Auth | signup, login, logout, refresh |
| auth_bridge | Cross-product | MindShift ↔ VOLAURA identity bridge |
| profiles | User | CRUD, avatar, visibility, privacy |
| aura | Scoring | scores, recalculation, percentile |
| assessment | Core product | sessions, questions, answers, submit |
| events | Dynamic | CRUD, checkin, attendees |
| organizations | B2B | CRUD, members, search |
| invites | Growth | org invite flow |
| badges | Gamification | tier display, unlock |
| verification | Trust | expert verification of skills |
| activity | Feed | user activity timeline |
| analytics | Data | usage metrics |
| discovery | Search | talent search, vector matching |
| community | Social | signals, interactions |
| lifesim | Ecosystem | crystal events, game bridge |
| notifications | UX | notification feed |
| stats | Public | platform statistics |
| telegram_webhook | Ops | bot integration |
| webhooks_sentry | Monitoring | error tracking bridge |
| character | Cross-product | character state event bus |
| brandedby | AI Twin | CRUD + generation jobs |
| skills | Library | skill CRUD |
| subscription | Payments | Stripe checkout, webhook, status |
| tribes | Social | tribe matching + streaks |
| admin | Platform | user management, platform ops |
| atlas_gateway | Swarm | inbound proposals from Python swarm |
| grievance | Trust | grievance filing |
| ops_admin | Ops | zones, services, roles |
| ops_incidents | Ops | incident lifecycle |
| ops_now | Ops | real-time dashboard + SSE |
| ops_operations | Ops | shift log entries |
| ops_shifts | Ops | shift lifecycle |

### 2.2 Schemas — 17 Pydantic model files

admin, assessment, aura, brandedby, character, common, discovery, event, invite, ops, organization, profile, subscription, tribes, verification + __init__

### 2.3 Services — 20+ business logic modules

assessment/ (IRT engine wrapper), analytics, atlas_tools, aura_reconciler, az_translation, brandedby_personality, cross_product_bridge, ecosystem_events, email, embeddings, ghosting_grace, lifesim, llm, loop_circuit_breaker, match_checker, model_router, notification_service, reeval_worker, swarm_service, tribe_matching, tribe_streak_tracker, video_generation_worker

### 2.4 Core Engine

- assessment/engine.py — Pure Python IRT/CAT (3PL + EAP)
- assessment/antigaming.py — Anti-gaming analysis
- assessment/aura_calc.py — AURA score calculation
- assessment/bars.py — Behavioral Analysis Rating System
- assessment/quality_gate.py — Response quality gating
- matching/ — Vector matching (discovery)
- reliability/scoring.py — Reliability scoring

### 2.5 Middleware Stack (order matters)

1. ProxyHeadersMiddleware (outermost)
2. RequestIdMiddleware (correlation)
3. ErrorAlertingMiddleware (5xx → CEO Telegram)
4. SecurityHeadersMiddleware (HSTS, CSP, X-Frame-Options)
5. CORSMiddleware
6. RateLimiting (slowapi)
7. Request body size limit (1MB)
8. Global exception handler

---

## 3. DATABASE INVENTORY

### 3.1 Migrations — 91 files

From 20260321 (extensions) through 20260416 (ops tables). Major milestones:
- 001-012: Core schema (profiles, competencies, questions, sessions, aura, badges, orgs, events, signals, embeddings, RPCs)
- 013-017: Expert verification, HNSW index, RLS audit, assignment columns
- 018-030: Session refinements, privacy, CEO inbox, discovery GIN, evaluation queue
- 031-050: Tribes, notifications, subscription (Stripe), crystal economy, skill library
- 051-070: Assessment enhancements, question batches, analytics materialization
- 071-091: Ops module, volunteer→professional rename, ecosystem compliance, energy level, grievances, lifesim events

### 3.2 Key Tables (reconstructed)

profiles, competencies, questions, assessment_sessions, aura_scores, badges, organizations, events, behavior_signals, volunteer_embeddings, expert_verifications, ceo_inbox, organization_invites, evaluation_queue, tribes, notifications, processed_stripe_events, crystal_transactions, skill_library, ops_zones, ops_services, ops_shifts, ops_operations, ops_incidents, grievances, lifesim_events, character_events

---

## 4. CROSS-PRODUCT MAP

| Product | Frontend route | Backend router | DB tables | Status |
|---------|---------------|----------------|-----------|--------|
| VOLAURA | /dashboard, /assessment, /aura, /profile, /discover | assessment, aura, profiles, discovery, badges, verification | All core tables | **Production** |
| MindShift | /mindshift (placeholder) | — (auth_bridge only) | — | **Placeholder only** |
| Life Simulator | /life (placeholder) | lifesim, character | lifesim_events, crystal_transactions, character_events | **Backend exists, UI placeholder** |
| BrandedBy | /brandedby + /brandedby/generations/[id] | brandedby | — (uses external AI) | **Backend exists, basic UI** |
| ZEUS/Atlas | /atlas | atlas_gateway | atlas_self_learning | **Swarm gateway, admin UI** |

### 4.1 Shared Infrastructure

- **Supabase Auth** — single auth across all products
- **character_events** table — cross-product event bus
- **auth_bridge** router — cross-project identity (ADR-006)
- **Bottom Tab Bar** — 5-product Discord-style navigation
- **Crystal economy** — VOLAURA assessments → crystal_earned → Life Simulator
- **Energy system** — global CSS [data-energy] + profiles.energy_level column

---

## 5. PACKAGES

| Package | Purpose | Status |
|---------|---------|--------|
| swarm | Python autonomous agent engine (48 agents claimed, 103 skill files in memory/) | Active |
| atlas-core | Identity + tools for Atlas agent | Active |
| atlas-memory | Persistent memory (STATE.md, handoffs, timeline) | Active |
| ecosystem-compliance | Constitution checker (Python + TypeScript) | Active |
| remotion | Video generation (React-based) | Exists, unclear usage |
| eslint-config | Shared ESLint rules | Config |
| typescript-config | Shared TSConfig | Config |

---

## 6. REDESIGN STATUS (from MEGAPLAN.md)

**Phase 1: Foundation** — ✅ DONE (tokens, energy system, navigation, core components)
**Phase 2: Screens** — ✅ DONE (dashboard, assessment, AURA, profile, landing, settings, auth, product placeholders)
**Phase 3: Polish** — PARTIALLY DONE
- ✅ Constitution audit (5 Laws)
- ❌ ADHD audit (26 rules) — NOT STARTED
- ❌ Accessibility (WCAG 2.1 AA) — NOT STARTED
- ❌ Cross-product consistency — NOT STARTED
- ❌ Responsive testing — NOT STARTED
- ❌ Performance audit — NOT STARTED

---

## 7. FIGMA ↔ CODE DRIFT (from 02-FIGMA-RECONCILIATION.md)

| Token | Figma | Code | Action needed |
|-------|-------|------|---------------|
| Surface base | #0A0A0F | #0d0d15 (closest) | Add --color-surface-base or reconcile |
| Success | #34D399 | #6ee7b7 | CSS → Figma value |
| Glass blur | 16px | 12px | Reconcile |
| Glass border | 6% white | 12% | Reconcile |
| Typography scale | 5 explicit sizes | Missing from CSS | Add --text-caption/body/overline/section/page |
| Product accents | NOT in Figma | In code only | Bring to Figma or document split |
| Form primitives | NOT designed | In code (shadcn) | Design or document as shadcn-only |
| Data viz | NOT designed | radar-chart exists | Design or document |

---

## 8. WHAT DOESN'T EXIST (gaps for Figma work)

1. **Onboarding flow design** — page exists but no Figma spec for multi-step onboarding wizard
2. **Org dashboard / B2B screens** — backend exists (orgs, invites, discovery) but no specific B2B admin design
3. **Ops module UX** — 6 pages built, zero Figma design. Functional but unstyled to ecosystem standards
4. **Tribe UI** — backend has tribe matching + streaks, UI has tribe-card component but no dedicated tribe management screens
5. **Notification center design** — page exists, no Figma spec
6. **Assessment question type templates** — MCQ, open-text, rating-scale exist as code components, not designed
7. **Mobile responsive layouts** — code is responsive but no Figma mobile frames
8. **BrandedBy generation flow** — backend has full AI twin pipeline, UI has basic CRUD
9. **Crystal economy UI** — crystal-balance-widget + crystal-shop exist but no cohesive design system for earn/spend flows
10. **Settings page with all sections** — energy picker exists, rest is code-only

---

## RECOMMENDATION

Phase 3 Polish is the next concrete deliverable. The code exists. The designs exist for Phases 1-2. What's missing is verification that code matches intent across ADHD audit, accessibility, responsive testing, and performance.

Start with the ADHD audit (26 rules) — it's the highest-signal check for VOLAURA's target users and directly validates the Constitution's core principles. Then accessibility (WCAG 2.1 AA), then responsive, then performance.

Figma gaps (Section 8) are Phase 4 territory — new screens that don't exist yet. Don't start those until Phase 3 Polish confirms the existing 55 pages are production-quality.
