# VOLAURA — 500-HOUR SPRINT PLAN

## STAKEHOLDER CRITIQUE SUMMARY (6 perspectives, 2 models, temp=1)

| Stakeholder | Model | #1 Priority | #2 | #3 |
|-------------|-------|-------------|----|----|
| **VC Investor** | Gemini | Token leak | Legal | Revenue |
| **HR Director (500 ppl)** | Llama 405B | Token leak | E2E tests | Performance |
| **SOC2 Auditor** | Gemini | Token leak | Legal | E2E + staging |
| **22yo User Baku** | Llama 405B | Token leak | Paddle | Load tests |
| **LinkedIn PM** | Gemini | Token leak | Revenue | Legal |
| **Data Lawyer** | Llama 405B | Token leak | ToS/PP legal | Data protection tests |

**Consensus: 6/6 = rotate .mcp.json token. 5/6 = Paddle. 4/6 = Legal + E2E.**

---

## PHASE 0 — EMERGENCY (hours 0-2)

### P0.1: Rotate .mcp.json Supabase token
- Revoke `sbp_33e367cc...` in Supabase dashboard
- Generate new token
- Move to environment variable, never commit
- Add `.mcp.json` to `.gitignore` or strip secrets
- Purge from git history (`git filter-branch` or BFG)
- **Owner:** CTO
- **Time:** 1 hour

### P0.2: Add pre-commit secret detection
- Install `detect-secrets` or `gitleaks` hook
- Prevent any future token commits
- **Time:** 30 min

---

## PHASE 1 — LAUNCH BLOCKERS (hours 2-50)

### 1.1: Paddle Payment Integration (20h)
Architecture already mapped (4 new files, 6 modified):
- `app/services/paddle.py` — Paddle SDK client, webhook HMAC-SHA256
- `app/routers/payment.py` — checkout, webhook, subscription status
- `app/schemas/payment.py` — Pydantic models
- Migration: `subscriptions` table + idempotency
- Frontend: pricing page, checkout flow, subscription status widget
- Tests: webhook signature verification, idempotency, subscription state machine

### 1.2: Legal Review (8h CTO + external counsel)
- Finalize ToS draft → send to AZ-licensed counsel (~$300-500)
- Finalize PP draft → GDPR + AZ PDPA compliance review
- Add consent checkboxes to signup flow
- Cookie banner (if not present)
- Data processing agreement template (for B2B orgs)

### 1.3: E2E Testing Suite (16h)
- Install Playwright
- Critical user journeys:
  1. Signup → onboarding → first assessment → AURA score
  2. Org signup → CSV invite → volunteer search → intro request
  3. Payment → subscription active → premium features
  4. Profile viewed → notification received
  5. Tribe pool → matched → streak tracking
- Add to CI pipeline
- Run against staging (see 1.4)

### 1.4: Staging Environment (6h)
- Supabase branch for staging
- Railway preview deployments
- Vercel preview deploys (already work)
- Separate env vars for staging

---

## PHASE 2 — QUALITY + SCALE PREP (hours 50-150)

### 2.1: Load Testing (12h)
- k6 scripts for critical endpoints:
  - Assessment start/answer/complete (CAT engine under load)
  - Volunteer search (pgvector under concurrent queries)
  - Tribe matching cron (with 12K users in pool)
- Baseline metrics: p50, p95, p99 latency
- Find breaking point (Railway single instance)

### 2.2: Performance Optimization (16h)
- Frontend:
  - Code-split large pages (assessment/complete 748 LOC)
  - Lazy load Recharts (AURA page)
  - Image optimization (OG cards, avatars)
  - Bundle size tracking in CI (Lighthouse)
- Backend:
  - Redis cache for rate limiting (multi-instance ready)
  - BARS evaluation cache → Redis (survives restart)
  - Connection pooling audit

### 2.3: Frontend Test Coverage (24h)
- Target: 30%+ coverage (from current 7%)
- Focus areas:
  - Assessment flow (session store, question rendering)
  - Auth flows (login, signup, OAuth callback)
  - AURA score display (correct tier, correct color)
  - Notification hooks (Realtime subscription)
- Vitest + React Testing Library

### 2.4: Backend Test Expansion (16h)
- API contract tests (OpenAPI spec vs actual responses)
- Assessment engine edge cases:
  - All 20 questions answered
  - SE convergence below threshold
  - Anti-gaming flag combinations
- LLM fallback chain tests (mock each tier)
- Rate limit integration tests

### 2.5: Accessibility Audit (12h)
- Systematic `useReducedMotion()` across all Framer Motion
- `aria-describedby` on all form validation errors
- Color contrast audit (AURA tier colors, especially gold)
- Screen reader testing on critical flows
- WCAG 2.1 AA compliance report

### 2.6: SDK Migration Completion (8h)
- Migrate manual `apiFetch()` calls to generated SDK:
  - Leaderboard
  - BrandedBy
  - Public stats
  - AURA explanation
- Sync OpenAPI spec with missing endpoints

### 2.7: Dead Code Cleanup (4h)
- Remove `timer.tsx`, `rating-scale.tsx` (unused)
- Clean empty `/features/` directories
- Remove deprecated prompt files from docs/archive

---

## PHASE 3 — PRODUCT POLISH (hours 150-300)

### 3.1: Design System Formalization (24h)
- Use Figma MCP to create component library
- Design tokens → CSS variables audit
- Component documentation (Storybook or similar)
- Responsive audit (375px mobile, 768px tablet, 1280px desktop)

### 3.2: Onboarding Flow Optimization (20h)
- UX research: walkthrough as Leyla (22yo, Baku, mobile)
- Reduce signup → first assessment time
- Progress indicators
- Empty states for new users
- First-run tutorial/tooltips

### 3.3: B2B Dashboard Polish (20h)
- Org volunteer search UX
- CSV export
- Assessment assignment flow
- Trust score visualization
- Saved searches with notifications

### 3.4: Assessment UX Enhancement (24h)
- Question type expansion (SJT with rating scale)
- Inter-competency transitions
- Results page improvement (coaching tips, action items)
- Retake flow (cooldown explanation, progress comparison)
- Question bank expansion (21 → 48 questions, 6 per competency)

### 3.5: Tribe System Polish (16h)
- Tribe card redesign
- Weekly streak visualization
- Crystal balance integration
- Kudos UI
- Tribe dissolution/renewal UX

### 3.6: Notification System Enhancement (12h)
- Push notifications (PWA + service worker)
- Email notifications (assessment complete, badge earned)
- In-app notification preferences
- Digest mode (daily/weekly summary)

### 3.7: PWA Hardening (12h)
- Offline fallback page
- App install prompt
- Background sync for offline actions
- Service worker cache strategy review
- Real device testing (Android + iOS)

### 3.8: Content & i18n (16h)
- RU translation (third language)
- AZ copy review with native speaker
- Marketing page copy polish
- SEO metadata for all pages
- OpenGraph cards for social sharing

---

## PHASE 4 — GROWTH INFRASTRUCTURE (hours 300-400)

### 4.1: Analytics Dashboard (20h)
- Internal analytics page (admin panel)
- Funnel visualization: signup → assessment → AURA → tribe → payment
- Cohort analysis: D0/D1/D7/D30 retention
- A/B testing framework foundation
- Event taxonomy finalization

### 4.2: Referral System (16h)
- Referral codes with tracking
- Referral rewards (crystals)
- Viral loop: share AURA badge → friend signs up → both earn crystals
- UTM tracking integration

### 4.3: Email Lifecycle (16h)
- Welcome email (post-signup)
- Assessment reminder (started but not completed)
- Badge earned notification
- Weekly digest (new matches, tribe activity)
- Re-engagement (inactive 7+ days)
- Transactional emails (password reset, invite)

### 4.4: SEO & Public Pages (12h)
- Landing page optimization
- Public profile SEO (structured data, OG tags)
- Sitemap generation
- Blog/content section foundation
- Organization directory page

### 4.5: B2B Acquisition Tooling (16h)
- Org self-serve signup flow
- Demo mode (try before subscribe)
- ROI calculator page
- Integration documentation
- API quick-start guide

---

## PHASE 5 — ECOSYSTEM + RESILIENCE (hours 400-500)

### 5.1: MindShift Integration (20h)
- Crystal bridge: assessment → crystal_earned → character events
- Cross-auth: shared Supabase session
- Habit → AURA score boost mechanic
- Cross-product navigation

### 5.2: Monitoring & Observability (16h)
- Sentry performance monitoring (transactions)
- Structured logging with correlation IDs
- Health dashboard (uptime, error rate, p95 latency)
- Alerting: Telegram + email on critical errors
- SLA definition (99.5% uptime target)

### 5.3: Disaster Recovery (12h)
- Database backup verification
- Runbook testing (from docs/DISASTER-RECOVERY-RUNBOOK.md)
- Point-in-time recovery drill
- Incident response practice
- Key rotation procedure

### 5.4: CI/CD Hardening (16h)
- Python dependency audit in CI
- Database migration staging validation
- Performance regression detection
- Automated rollback on deployment failure
- Preview environments for PRs

### 5.5: Documentation Consolidation (12h)
- Architecture decision records (ADR) audit
- API documentation (auto-generated from OpenAPI)
- Deployment guide
- On-call runbook
- New developer onboarding guide

### 5.6: Scale Preparation (24h)
- Redis integration (rate limiting + caching)
- Database connection pooling (PgBouncer)
- CDN configuration for static assets
- Multi-instance Railway deployment
- Horizontal scaling strategy document

---

## TIMELINE SUMMARY

| Phase | Hours | Focus | Outcome |
|-------|-------|-------|---------|
| **0** | 2h | Emergency security | Token rotated, secret detection |
| **1** | 50h | Launch blockers | Payments, legal, E2E tests, staging |
| **2** | 100h | Quality + scale | Load tests, perf, coverage 30%+, a11y |
| **3** | 150h | Product polish | Design system, onboarding, B2B, tribes |
| **4** | 100h | Growth infra | Analytics, referrals, email, SEO |
| **5** | 100h | Ecosystem + resilience | MindShift, monitoring, DR, CI/CD |
| **TOTAL** | **502h** | | |

---

## TOOLS & MCPs AVAILABLE

| Tool | Purpose | When |
|------|---------|------|
| **Figma MCP** | Design system, component audit, screenshots | Phase 3.1 |
| **Vercel MCP** | Deployment, build logs, preview URLs | Phase 1.4, ongoing |
| **Supabase MCP** | Migrations, SQL, advisors, branches | Phase 0-5 |
| **Claude Preview** | Live preview, screenshots, inspecting | Phase 3 |
| **Chrome MCP** | Browser testing, screenshots, E2E visual | Phase 2.5 |
| **Google Drive** | Document collaboration | Phase 1.2 |
| **Scheduled Tasks** | Recurring audits, monitoring | Phase 5.2 |
| **OpenSpace** | Skill execution, auto-evolution | Phase 2-5 |
| **NotebookLM** | Deep research (pricing, competitors) | Phase 4 |

---

## MULTI-MODEL ASSIGNMENT (Step 5.4)

| Task domain | Primary model | Fallback |
|-------------|---------------|----------|
| Security audit | DeepSeek R1 (NVIDIA NIM) | Gemini |
| Architecture review | Llama 405B (NVIDIA NIM) | Claude Sonnet |
| Product/UX critique | Gemini 2.0 Flash | Claude Haiku |
| Legal review | Llama 405B | Gemini |
| Performance analysis | DeepSeek R1 | Claude Sonnet |
| Growth strategy | Gemini | Claude Sonnet |
| Synthesis/Final | Claude Opus | — |

---

*Plan created: 2026-04-03*
*Stakeholder critique: 6 perspectives, 2 models (Gemini 2.0 Flash + Llama 3.1 405B), temperature 1*
*Project audit: 3 parallel agents (backend + frontend + infra)*
*Total files analyzed: 76 + 155 + 63 migrations + 79 memory = 373 files*
