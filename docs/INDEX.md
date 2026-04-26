# Volaura Knowledge Base

> Obsidian-compatible vault. Every document cross-references others.
> Read this file first to navigate the entire project.
>
> **Last Updated:** 2026-04-26 (Session 125 close) | ~140 active documents indexed
> **Vault Root:** `docs/`

## Atlas Memory Layer (canonical source of truth, lives outside docs/ but reads from here)

- [[../memory/atlas/identity|Atlas Identity]] — who I am, naming truth, blanket consent, federated memory role
- [[../memory/atlas/SESSION-124-WRAP-UP-2026-04-26|Session 124 Wrap-Up]] — first autonomous swarm vote (claim under correction post-Class 26), Vercel root cause, three structural gates landed
- [[../memory/atlas/SESSION-125-WRAP-UP-2026-04-26|Session 125 Wrap-Up]] — pre-compaction anchor: scope split with atlas-cli, DEBT-002 parallel-shipment miss, Class 26 fabrication-by-counting, MindShift voice plugin landed
- [[../memory/atlas/atlas-debts-to-ceo|Atlas Debts ledger]] — DEBT-001 230 AZN duplicate 83(b) + DEBT-002 230 AZN parallel-shipment miss = 460 AZN credited-pending
- [[../memory/atlas/lessons|Lessons]] — Class 19-26 condensed wisdom across sessions
- [[../memory/atlas/company-state|Company State]] — VOLAURA Inc. Delaware C-Corp legal canon, ITIN canonical path, EIN window
- [[../memory/atlas/CURRENT-SPRINT|Current Sprint pointer]] — 14 pointer-tasks Track A/B/C/D/E status

## CEO-Facing Hub (for-ceo/)

- [[../for-ceo/living/atlas-self-audit-2026-04-26|Atlas Self-Audit 2026-04-26]] — 12-section single source of truth answer to «кто ты, куда идём, какие проблемы»
- [[../for-ceo/living/reality-audit-2026-04-26|Reality Audit 2026-04-26]] — composite findings from 3 Sonnet agents on VOLAURA / MindShift / cross-product gaps
- [[../for-ceo/tasks/2026-04-26-itin-packet|ITIN Packet]] — bilingual ASAN script, Plan A/B fallback, pre-filled W-7 + DHL waybill template

## Cross-Instance Architecture (post-2026-04-26 scope split)

- [[architecture/cross-instance-courier-signing-protocol|Courier Signing Protocol v1]] — SHA-256 verification between Atlas-instances via CEO courier
- [[../memory/atlas/handoffs/2026-04-26-terminal-atlas-swarm-development|Swarm Development Handoff]] — Terminal-Atlas P0 task: fix save path, connect learning, diversify context+providers

---

## Supreme Law

**The [[ECOSYSTEM-CONSTITUTION]] governs all 5 products. It supersedes everything.**
- Law 1: Never Red — errors purple, warnings amber
- Law 2: Energy Adaptation — Full/Mid/Low modes everywhere
- Law 3: Shame-Free Language — no guilt mechanics
- Law 4: Animation Safety — max 800ms, prefers-reduced-motion mandatory
- Law 5: One Primary Action per screen

---

## Vision & Strategy

- [[VISION-FULL]] — CEO's real vision: from verified proof to durable professional identity
- [[MASTER-STRATEGY]] — Business model, grants, expansion roadmap, unit economics
- [[TONE-OF-VOICE]] — Tinkoff/Aviasales benchmark, shame-free voice
- [[ECOSYSTEM-MAP]] — All 5 products and their relationships
- [[ECOSYSTEM-ASSESSMENT]] — Cross-product dependencies
- [[500-HOUR-PLAN]] — Time allocation plan
- [[MONETIZATION-ROADMAP]] — Revenue timeline
- [[financial-model]] — Financial model with unit economics
- [[GITA-GRANT-APPLICATION-2026]] — Georgia GITA grant ($240K target)

---

## Research (CEO Originals)

- [[research/ECOSYSTEM-REDESIGN-BRIEF-2026-04-14]] — Redesign brief: 5 products, tokens, navigation, AURA radar
- [[research/NEUROCOGNITIVE-ARCHITECTURE-2026]] — ZEUS cognitive architecture (GWT, ZenBrain, Curiosity Engine)
- [[research/adhd-first-ux-research]] — 26 ADHD-first design rules
- [[research/ecosystem-design-research]] — Discord + Duolingo + Habitica navigation patterns
- [[research/blind-spots-analysis]] — 10 critical blind spots (TAM, debt bomb, LTV/CAC)
- [[research/gemini-research-all]] — AI memory, agile methodology, handoff protocols (140K words)
- [[research/geo-pricing-research]] — Regional pricing strategy
- [[research/swarm-innovation-research]] — Swarm architecture research
- [[research/ZEUS-MEMORY-ARCHITECTURE-RESEARCH-2026-04-14]] — ZEUS memory system design
- [[research/UNIVERSAL-WEAPON-RESEARCH-2026-04-04]] — Universal assessment weapon concept
- [[NOTEBOOKLM-COUNTRY-RESEARCH]] — Country expansion research via NotebookLM

---

## Architecture Decision Records (ADRs)

- [[adr/ADR-001-system-architecture]] — Full stack: Vercel + Railway + Turborepo
- [[adr/ADR-002-database-schema]] — Tables, RLS, pgvector (Supabase)
- [[adr/ADR-003-auth-verification]] — Auth + 3-level verification
- [[adr/ADR-004-assessment-engine]] — IRT/CAT adaptive testing + Gemini evaluation
- [[adr/ADR-005-aura-scoring]] — AURA composite score, weights, tiers
- [[adr/ADR-006-ecosystem-architecture]] — Multi-product ecosystem structure
- [[adr/ADR-007-ai-gateway-model-router]] — LLM routing: Cerebras → Ollama → NVIDIA → Haiku
- [[adr/ADR-008-zeus-governance-layer]] — ZEUS agent governance
- [[adr/ADR-009-crewai-adoption]] — CrewAI evaluation and adoption decision
- [[adr/ADR-010-defect-autopsy]] — Defect analysis protocol

---

## Design System

- [[design/REDESIGN-BRIEF-v2]] — Current redesign brief (v2)
- [[design/STITCH-DESIGN-SYSTEM]] — Stitch design system specification
- [[design/DESIGN-SYSTEM-AUDIT]] — Token coverage, component gaps
- [[design/COMPONENT-LIBRARY]] — All shadcn/ui components with states
- [[design/ANIMATION-SYSTEM]] — Motion implementation specs (spring damping ≥14)
- [[design/BRAND-IDENTITY]] — Logo, illustrations, voice & tone
- [[design/UX-COPY-AZ-EN]] — Bilingual microcopy (AZ primary, EN secondary)
- [[I18N-KEYS]] — 157+ bilingual i18n keys

Related: [[research/adhd-first-ux-research]] | [[research/ecosystem-design-research]] | [[ECOSYSTEM-CONSTITUTION]]

---

## Engineering

- [[engineering/API-CONTRACTS]] — FastAPI endpoints, request/response schemas
- [[engineering/STATE-MANAGEMENT]] — Zustand + TanStack Query + RSC
- [[engineering/TESTING-STRATEGY]] — Vitest + Playwright + coverage
- [[engineering/SECURITY-STANDARDS]] — Microsoft SDL + NIST SSDF + OWASP ASVS L2
- [[engineering/DEPLOY-CHECKLIST]] — Pre-launch verification
- [[engineering/SEO-TECHNICAL]] — Structured data, OG tags, sitemap
- [[engineering/AI-ORCHESTRATION-GUIDE]] — Multi-model AI orchestration
- [[engineering/DECISION-SIMULATION-PROTOCOL]] — Decision simulation for agents
- [[API-REFERENCE]] — API reference documentation
- [[ARCHITECTURE]] — System architecture overview
- [[ARCHITECTURE_OVERVIEW]] — Architecture overview (alternative)

Related: [[adr/ADR-001-system-architecture]] | [[adr/ADR-004-assessment-engine]]

---

## Growth & Marketing

- [[growth/LAUNCH-ACTIVATION-PLAN]] — Real channels: HR/WhatsApp, LinkedIn, TikTok, STEP IT
- [[growth/VIRAL-LOOP]] — Share mechanics, referral system, invite flow
- [[growth/EMAIL-STRATEGY]] — Transactional and lifecycle emails
- [[growth/EVENT-ACTIVATION]] — Event activation template
- [[growth/ORG-ACQUISITION]] — B2B onboarding, partnership outreach
- [[growth/GROWTH-STRATEGY-DEEP-RESEARCH]] — Deep research on growth
- [[growth/LINKEDIN-POST-AGENT-OS]] — LinkedIn content strategy
- [[GROWTH-STRATEGY-PLAYBOOK]] — Growth playbook
- [[MASS-ACTIVATION-PLAN]] — Mass user activation
- [[AZ-LINKEDIN-AUDIENCE]] — Azerbaijan LinkedIn audience analysis
- [[CUSTOMER-JOURNEY-MAP]] — User journey mapping

Related: [[MASTER-STRATEGY]] | [[VISION-FULL]]

---

## Product Specs

- [[MINDSHIFT-INTEGRATION-SPEC]] — MindShift product integration
- [[LIFE-SIMULATOR-INTEGRATION-SPEC]] — Life Simulator integration
- [[LIFE-SIMULATOR-GAME-DESIGN]] — Life Simulator game design document
- [[AI-TWIN-CONCEPT]] — AI twin concept design
- [[CSV-BULK-INVITE-IMPLEMENTATION]] — Bulk invite feature
- [[PLAN-product-trust-architecture]] — Product trust architecture
- [[MEGAPLAN-SESSION-95-AUTONOMOUS]] — Autonomous mega-plan (Atlas + Cowork)

Related: [[ECOSYSTEM-CONSTITUTION]] | [[ECOSYSTEM-MAP]] | [[adr/ADR-006-ecosystem-architecture]]

---

## Quality & Security

- [[QUALITY-STANDARDS]] — Quality standards and metrics
- [[QUALITY-SYSTEM]] — Quality assurance system
- [[COMPREHENSIVE-TEST-PLAN]] — Full test plan
- [[FUNCTIONAL-TEST-STRATEGY]] — Functional testing strategy
- [[BETA-CHECKLIST]] — Beta launch checklist
- [[LAUNCH-BLOCKERS]] — Pre-launch blockers (19 from Constitution)
- [[PRODUCTION-READINESS-PLAN]] — Production readiness
- [[ATTACK-VECTORS-EXECUTIVE]] — Security attack vectors
- [[SECURITY-AUDIT-INDEX]] — Security audit index
- [[DISASTER-RECOVERY-RUNBOOK]] — DR runbook

---

## Sprints & Execution

- [[SPRINT-ATLAS-AUTONOMY-2026-04-12]] — Atlas autonomy sprint
- [[SPRINT-AUDIT-CONSOLIDATED]] — Sprint audit results
- [[SPRINT-S4-DEBATE-2026-04-08]] — Sprint S4 debate
- [[MEGAPLAN-MINDSHIFT-LAUNCH-2026-04-08]] — MindShift launch megaplan
- [[EXECUTION-PLAN]] — Execution plan
- [[IMPLEMENTATION-ROADMAP]] — Implementation roadmap
- [[BACKLOG]] — Product backlog

---

## AI & Swarm

- [[memory/atlas/wake]] — Atlas wake protocol (Code-Atlas / CLI)
- [[memory/atlas/wake-browser]] — Atlas wake protocol (browser-Atlas / Obsidian)
- [[CONSTITUTION_AI_SWARM]] — AI swarm constitution
- [[MODEL-ROSTER]] — Active model roster
- [[CEO-PERFORMANCE-REVIEW-SWARM]] — CEO review of swarm performance
- [[EXTERNAL-AUDIT-GPT54-2026-04-04]] — External GPT-5.4 audit
- [[PERPLEXITY-RECONCILIATION-2026-04-11]] — Perplexity reconciliation
- [[SKILL-AUDIT-FINDINGS]] — Skill audit findings

Related: [[research/NEUROCOGNITIVE-ARCHITECTURE-2026]] | [[adr/ADR-007-ai-gateway-model-router]]

---

## Content & Outreach

- Content posts: `content/posts/draft/` | `content/posts/ready/` | `content/posts/published/`
- [[CONTENT-BRIEF-TEMPLATE]] — Content brief template
- [[BETA-INVITE-TEMPLATES]] — Beta invite templates
- Correspondence: `correspondence/`

---

## Templates & Process

- [[ACCEPTANCE-CRITERIA-TEMPLATES]] — AC templates
- [[ACCEPTANCE-CRITERIA]] — Definition of Done
- [[AGENT-BRIEFING-TEMPLATE]] — Agent briefing template
- [[BEST-PRACTICES]] — Development best practices
- [[CONTRIBUTING]] — Contribution guide
- [[MANDATORY-RULES]] — Mandatory rules
- [[TASK-PROTOCOL-QUICKREF]] — Task protocol quick reference
- [[CULTURAL-AUDIT-CHECKLIST]] — Cultural audit checklist
- [[DECISIONS]] — Historic decision log

---

## Navigation by Role

**CEO:** [[ECOSYSTEM-CONSTITUTION]] → [[VISION-FULL]] → [[MASTER-STRATEGY]] → [[LAUNCH-BLOCKERS]]

**CTO (Atlas):** [[ECOSYSTEM-CONSTITUTION]] → [[ARCHITECTURE]] → [[adr/ADR-001-system-architecture]] → [[engineering/DEPLOY-CHECKLIST]]

**Research (Cowork):** [[research/ECOSYSTEM-REDESIGN-BRIEF-2026-04-14]] → [[research/adhd-first-ux-research]] → [[research/blind-spots-analysis]]

**Design:** [[design/REDESIGN-BRIEF-v2]] → [[design/COMPONENT-LIBRARY]] → [[design/ANIMATION-SYSTEM]] → [[ECOSYSTEM-CONSTITUTION]]

**Growth:** [[growth/LAUNCH-ACTIVATION-PLAN]] → [[growth/VIRAL-LOOP]] → [[growth/EMAIL-STRATEGY]] → [[MASTER-STRATEGY]]

---

## Archive

Superseded documents moved to `archive/`. Not indexed here.
Browse: `archive/root-superseded/` | `archive/handoffs/` | `archive/sprints/` | `archive/audits/`
