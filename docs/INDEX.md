# Volaura Knowledge Base

> Obsidian-compatible vault. Every document cross-references others.
> Read this file first to navigate the entire project.
>
> **Last Updated:** 2026-03-22 | 49 documents indexed

---

## Project Command Center

**Start here — these 4 documents define everything:**
- [[MEGA-PROMPT]] — Full-stack generation prompt (1577 lines, 9 modules). THE primary source of truth.
- [[../CLAUDE.md]] — Master instructions, tech stack, mandatory protocols, architecture patterns
- [[MASTER-AUDIT-SYNTHESIS]] — 6-role audit results, vulnerabilities, action plan, priorities
- [[ACCEPTANCE-CRITERIA]] — Definition of Done, per-module Given/When/Then, pre-launch checklist

---

## Generation Prompts (AI Handoff)

**These prompts are sent to AI code generators in this order:**
- [[prompts/VERTEX-BACKEND-PROMPT]] — FastAPI backend generation (DB + Auth + API). Send to Vertex/Gemini.
- [[prompts/V0-FRONTEND-PROMPT]] — Core UI generation (Assessment + Results + Dashboard). Send to V0.
- [[V0_SPRINT3_PROMPT]] — Profile + Events + Sharing
- [[V0_SPRINT4_PROMPT]] — Settings + Notifications + Advanced
- [[V0_SPRINT5_PROMPT]] — Landing page + Polish
- [[prompts/PERPLEXITY-REVIEW-PROMPT]] — Code review prompt for Perplexity

---

## Architecture Decision Records (ADRs)

- [[adr/ADR-001-system-architecture]] — Full stack, hosting, monorepo (Vercel, Railway, Turborepo)
- [[adr/ADR-002-database-schema]] — Tables, RLS, pgvector (Supabase PostgreSQL)
- [[adr/ADR-003-auth-verification]] — Auth strategy + 3-level verification (Supabase Auth)
- [[adr/ADR-004-assessment-engine]] — Pseudo-IRT, question types, scoring (adaptivetesting, Gemini)
- [[adr/ADR-005-aura-scoring]] — Composite score, weights, tiers, recalculation

---

## Product

- [[product/BUSINESS-MODEL]] — Revenue model, pricing tiers, monetization
- [[product/KPIs]] — North star metric, activation, engagement, retention
- [[product/USER-PERSONAS]] — Volunteer, Organization, Event attendee profiles
- [[product/COMPETITIVE-ANALYSIS]] — Competitive landscape (Credly, LinkedIn, local)
- [[VISION-EVOLUTION]] — Conceptual shift from "volunteer platform" to "verified competency + community"

---

## Design

- [[DESIGN_BLUEPRINT]] — Comprehensive design system specification for V0
- [[DESIGN_HANDOFF_V0]] — V0 design handoff to engineering team
- [[design/DESIGN-SYSTEM-AUDIT]] — Token coverage, component completeness, gaps
- [[design/COMPONENT-LIBRARY]] — All shadcn/ui components with states and variants
- [[design/UX-COPY-AZ-EN]] — Complete microcopy (AZ primary, EN secondary)
- [[design/ANIMATION-SYSTEM]] — Framer Motion implementation specs
- [[design/BRAND-IDENTITY]] — Logo, illustration system, voice & tone
- [[I18N-KEYS]] — 157 bilingual i18n keys across 7 namespaces

---

## Engineering

- [[engineering/API-CONTRACTS]] — FastAPI endpoints, request/response schemas
- [[engineering/STATE-MANAGEMENT]] — Zustand stores, TanStack Query keys, RSC strategy
- [[engineering/TESTING-STRATEGY]] — Test plan, Vitest, Playwright, coverage targets
- [[engineering/SEO-TECHNICAL]] — Structured data, OG tags, sitemap, Next.js
- [[engineering/DEPLOY-CHECKLIST]] — Pre-launch verification checklist
- [[engineering/SECURITY-STANDARDS]] — Microsoft SDL + NIST SSDF + OWASP ASVS Level 2
- [[AI-EVALUATION-QUESTION]] — LLM evaluation prompt design

---

## Growth

- [[growth/VIRAL-LOOP]] — Share mechanics, referral system, invite flow
- [[growth/EMAIL-STRATEGY]] — Transactional and lifecycle email sequences
- [[growth/EVENT-ACTIVATION]] — Generic event activation template (parameterized)
- [[growth/ORG-ACQUISITION]] — B2B onboarding, partnership outreach
- [[growth/LAUNCH-ACTIVATION-PLAN]] — Real channels: HR/WhatsApp, LinkedIn, TikTok, STEP IT

---

## Audit & Reports

- [[AUDIT-FULL-REPORT]] — First-round audit findings (Security 48, UX 23, Architecture 62)
- [[MASTER-AUDIT-SYNTHESIS]] — Final 6-role agency audit, action plan, priorities
- [[prompts/AUDIT-ARCHITECTURE]] — Architecture audit details
- [[prompts/AUDIT-ACCESSIBILITY]] — Accessibility audit details
- [[prompts/AUDIT-DESIGN-CRITIQUE]] — Design critique audit details
- [[prompts/AUDIT-UX-COPY]] — UX copy audit details

---

## Reference

- [[DECISIONS]] — Historic decision log and architectural choices
- [[HANDOFF]] — Design-to-developer handoff guide

---

## Navigation by Role

**Founder / PM:** [[MASTER-AUDIT-SYNTHESIS]] → [[ACCEPTANCE-CRITERIA]] → [[product/KPIs]]

**AI Code Generator (Backend):** [[MEGA-PROMPT]] → [[prompts/VERTEX-BACKEND-PROMPT]] → [[engineering/SECURITY-STANDARDS]]

**AI Code Generator (Frontend):** [[MEGA-PROMPT]] → [[prompts/V0-FRONTEND-PROMPT]] → [[I18N-KEYS]] → [[DESIGN_BLUEPRINT]]

**Growth / Marketing:** [[growth/LAUNCH-ACTIVATION-PLAN]] → [[growth/VIRAL-LOOP]] → [[growth/EMAIL-STRATEGY]]

**Security Review:** [[engineering/SECURITY-STANDARDS]] → [[MASTER-AUDIT-SYNTHESIS]] (V1-V5)

---

## Verification Summary

✓ 49 documents indexed:
- 5 ADRs
- 5 Product docs (incl. Vision Evolution)
- 8 Design docs (incl. i18n keys)
- 7 Engineering docs (incl. Security Standards)
- 6 Growth docs (incl. Launch Activation Plan)
- 6 Generation prompts
- 6 Audit reports
- 4 Core references + Mega-Prompt + Acceptance Criteria

Knowledge base is **complete and audited**. Ready for code generation.
