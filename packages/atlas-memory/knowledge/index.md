# Knowledge Index: VOLAURA Ecosystem
**Last updated:** 2026-04-12  
**Total indexed files:** 180+ markdown documents across 12 topic categories  
**Freshness:** Most recent updates from April 12, 2026

---

## How to Use This Index

1. **Search for your topic** in the sections below
2. **Read the primary file** listed first (contains authoritative answers)
3. **Check supporting files** for deeper context and implementation details
4. **Check freshness date** — files updated recently are most reliable
5. **Use absolute paths** when grepping or reading files in sessions

---

## TOPICS

### 1. Architecture & Infrastructure

**Core System Design**
- Primary: `docs/ARCHITECTURE.md` (4/11, comprehensive)
- Primary: `docs/ARCHITECTURE_OVERVIEW.md` (4/12, latest)
- ADR-001: `docs/adr/ADR-001-system-architecture.md`
- ADR-006: `docs/adr/ADR-006-ecosystem-architecture.md`

**Integration & Ecosystem**
- Primary: `docs/ECOSYSTEM-CONSTITUTION.md` (4/12, 86KB, all 5 products)
- Map: `docs/ECOSYSTEM-MAP.md` (4/11, routing table)
- Reference: `docs/ECOSYSTEM-ASSESSMENT.md` (3/27, deep analysis)
- Specification: `docs/ECOSYSTEM-AUDIT-ALL-REPOS.md` (4/11, repo audit)

**Infrastructure & Deployment**
- Checklist: `docs/engineering/DEPLOY-CHECKLIST.md` (comprehensive deployment)
- Technical: `docs/engineering/SEO-TECHNICAL.md` (Next.js + SEO setup)
- Disaster Recovery: `docs/DISASTER-RECOVERY-RUNBOOK.md` (incident response)
- Runbook: `docs/RUNBOOK.md` (operational guide)

**Quality Systems**
- Standards: `docs/QUALITY-STANDARDS.md` (4/3, acceptance criteria)
- Full System: `docs/QUALITY-SYSTEM.md` (4/12, comprehensive DoD)
- Metrics: `memory/context/quality-metrics.md` (DORA tracking)

---

### 2. Assessment / AURA / IRT

**Assessment Engine & Algorithms**
- ADR-004: `docs/adr/ADR-004-assessment-engine.md` (4/12, updated, pure-Python IRT + CAT)
- AURA Scoring: `docs/adr/ADR-005-aura-scoring.md` (8 weights, badge tiers)
- IRT Technical Details: see `apps/api/app/core/assessment/engine.py` (3PL + EAP implementation)

**AURA Score Calculation**
- Weights (final): communication 0.20, reliability 0.15, english 0.15, leadership 0.15, event_perf 0.10, tech_literacy 0.10, adaptability 0.10, empathy 0.05
- Badge Tiers: Platinum >=90, Gold >=75, Silver >=60, Bronze >=40, None <40
- Verification Multipliers: self=1.00, org=1.15, peer=1.25

**Question & Assessment Design**
- AI Evaluation: `docs/AI-EVALUATION-QUESTION.md` (rubric generation)
- Acceptance Criteria: `docs/ACCEPTANCE-CRITERIA.md` (60KB, question specs)

**DIF & Bias Audit**
- See CONSTITUTION Law 2: Pre-Assessment Layer + DIF audit (P0 blocker)
- Skills Agent: `memory/swarm/skills/archive/assessment-science-agent.md`

---

### 3. Payments & Pricing

**Monetization & Pricing Strategy**
- Primary: `docs/MONETIZATION-ROADMAP.md` (pricing tiers, roadmap)
- Business Model: `docs/product/BUSINESS-MODEL.md` (revenue streams)
- Financial Model: `docs/financial-model.md` (LTV/CAC)

**Payment Integration**
- ADR-007: `docs/adr/ADR-007-ai-gateway-model-router.md` (LLM cost optimization)
- Skills Agent: `memory/swarm/skills/archive/payment-provider-agent.md` (Paddle webhooks)
- Agent: `memory/swarm/skills/archive/financial-analyst-agent.md` (crystal economy, runway)

**Crystal Economy**
- Design: `docs/TRIBE-STREAKS-DESIGN.md` (crystal earn/spend/cap mechanics)
- Anti-Gaming: See `docs/SECURITY-REVIEW-CSV-BULK-INVITE.md` Section 7 (gates + anti-cheat)

---

### 4. Legal & Compliance

**Terms & Privacy**
- ToS Draft: `docs/legal/ToS-draft.md` (current version)
- Privacy Policy: `docs/legal/Privacy-Policy-draft.md`
- Privacy: `docs/privacy-policy.md` (full text)

**Regulatory & Data Compliance**
- Skills Agent: `memory/swarm/skills/archive/legal-advisor.md` (GDPR, PDPA, AI Act, WHT)
- Country Research: `docs/NOTEBOOKLM-COUNTRY-RESEARCH.md` (research template per country)

**Security & Data Protection**
- CONSTITUTION Law 1: Never red errors → use purple #D4B4FF
- RLS Policies: `docs/adr/ADR-003-auth-verification.md` (Supabase auth + RLS)
- Standards: `docs/engineering/SECURITY-STANDARDS.md` (4/11, updated)

---

### 5. Growth & Marketing

**Growth Strategy & Activation**
- Primary: `docs/GROWTH-STRATEGY-PLAYBOOK.md` (31KB, comprehensive)
- Deep Research: `docs/growth/GROWTH-STRATEGY-DEEP-RESEARCH.md`
- Email Strategy: `docs/growth/EMAIL-STRATEGY.md` (lifecycle emails)
- Event Activation: `docs/growth/EVENT-ACTIVATION.md` (WUF, partnerships)
- Viral Loop: `docs/growth/VIRAL-LOOP.md` (referral mechanics)
- Org Acquisition: `docs/growth/ORG-ACQUISITION.md` (B2B motion)
- Launch Activation: `docs/growth/LAUNCH-ACTIVATION-PLAN.md`

**Positioning & Messaging**
- Messaging (locked): "Prove your skills. Earn your AURA. Get found by top organizations."
- NOT: "volunteer platform" or "LinkedIn competitor"
- AZ Audience: `docs/AZ-LINKEDIN-AUDIENCE.md` (4/1, cultural context)
- Tone of Voice: `docs/TONE-OF-VOICE.md` (4/2, voice & style)
- Brand: `docs/design/BRAND-IDENTITY.md` (color, typography, personality)

**Competitive Analysis**
- Analysis: `docs/product/COMPETITIVE-ANALYSIS.md` (positioning vs LinkedIn, Indeed, etc.)
- KPIs: `docs/product/KPIs.md` (D0, D7, retention targets)

---

### 6. Content & LinkedIn

**Content Production**
- Tracker: `docs/content/TRACKER.md` (editorial calendar status)
- LinkedIn Series: `docs/content/LINKEDIN-SERIES-CLAUDE-CTO.md` (technical thought leadership)
- Skills Agent: `memory/swarm/skills/archive/linkedin-content-creator.md`
- Strategist: `memory/swarm/skills/archive/communications-strategist.md` (narrative arc)
- Promotion Agency: `memory/swarm/skills/archive/promotion-agency.md` (3x/week carousel-first)

**Content Reviews**
- Review Process: `docs/content/reviews/` (peer review templates)
- Posts Directory: `docs/content/posts/` (draft and published)

---

### 7. Design & UX

**Design System**
- System Audit: `docs/design/DESIGN-SYSTEM-AUDIT.md` (60KB, components)
- Component Library: `docs/design/COMPONENT-LIBRARY.md` (60KB, Stitch UI)
- Animation System: `docs/design/ANIMATION-SYSTEM.md` (max 800ms, prefers-reduced-motion)
- Stitch System: `docs/design/STITCH-DESIGN-SYSTEM.md` (integration guide)

**UX & Copy**
- UX Copy (AZ/EN): `docs/design/UX-COPY-AZ-EN.md` (42KB, all interface text)
- Copy Template: `docs/CONTENT-BRIEF-TEMPLATE.md`
- Redesign Brief: `docs/design/REDESIGN-BRIEF-v2.md` (4/11, latest design work)

**User Experience**
- Customer Journey: `docs/CUSTOMER-JOURNEY-MAP.md` (4 personas, friction points)
- User Personas: `docs/product/USER-PERSONAS.md` (Leyla, Nigar, Kamal, Aynur, Rauf, Rauf)
- Research: `docs/research/adhd-first-ux-research.md` (accessibility)

---

### 8. Security

**Security Audits & Standards**
- Standards (current): `docs/engineering/SECURITY-STANDARDS.md` (4/11, comprehensive)
- Audit Index: `docs/SECURITY-AUDIT-INDEX.md` (full audit log)
- Audit Report: `docs/SECURITY-AUDIT-ATTACKER-ASSESSMENT.md` (vulnerability scoring)
- Fixes Checklist: `docs/SECURITY-FIXES-CHECKLIST.md` (P0-P3 remediation)

**Specific Security Reviews**
- CSV Bulk Invite: `docs/SECURITY-REVIEW-CSV-BULK-INVITE.md` (4/12, 40KB, attack vectors + gates)
- Executive Summary: `docs/ATTACK-VECTORS-EXECUTIVE.md` (CVSS scoring)
- Skills Agent: `memory/swarm/skills/archive/risk-manager.md` (threat modeling)

**Engineering Standards**
- Security Review Skill: `docs/engineering/skills/SECURITY-REVIEW.md` (10-point checklist)
- Threat Model Template: `docs/engineering/skills/THREAT-MODEL-TEMPLATE.md`

---

### 9. Atlas Identity & Memory

**Atlas System (VOLAURA's Memory Architecture)**
- Primary: `memory/atlas/README.md` (purpose, usage)
- Architecture Proposal: `memory/atlas/memory-architecture-proposal.md` (4/12, design)
- Identity & Voice: `memory/atlas/identity.md` (who Claude is to CEO)
- Manifest: `memory/atlas/manifest.json` (metadata)

**Atlas Continuity**
- Continuity Roadmap: `memory/atlas/continuity_roadmap.md` (session recovery)
- Bootstrap: `memory/atlas/bootstrap.md` (initialization protocol)
- Wake Protocol: `memory/atlas/wake.md` (session startup)
- Lessons: `memory/atlas/lessons.md` (learning captured)

**Atlas Memory Logs**
- Journal: `memory/atlas/journal.md` (17KB, session chronicle)
- Project History: `memory/atlas/project_history_from_day_1.md` (19KB, Session 1-N chronicle)
- Session Memory: `memory/atlas/cowork-session-memory.md` (4/12, session 93+)
- Full Transcript: `memory/atlas/session-93-full-transcript.jsonl` (12MB, raw session data)

**Relationships & Context**
- Relationships: `memory/atlas/relationships.md` (CEO, team, stakeholders)
- Relationship Log: `memory/atlas/relationship_log.md` (interaction history)
- Emotional Dimensions: `memory/atlas/emotional_dimensions.md` (psychological model)

**Atlas Operations**
- Communication Protocol: `memory/atlas/agent-communication-protocol.md` (inter-agent)
- Arsenal Complete: `memory/atlas/arsenal-complete.md` (tools, capabilities)
- Heartbeat: `memory/atlas/heartbeat.md` (liveness, status)
- Remember Everything: `memory/atlas/remember_everything.md` (consolidation)

---

### 10. Swarm & Agents

**Swarm Architecture & Governance**
- Constitution: `docs/CONSTITUTION_AI_SWARM.md` (4/12, 16KB, swarm protocols)
- ADR-008: `docs/adr/ADR-008-zeus-governance-layer.md` (autonomous governance)
- ZEUS Gateway: See `docs/ECOSYSTEM-CONSTITUTION.md` (39 agents in routing table)

**Agent Skills Directory**
- Index: `memory/swarm/skills/_SKILL-INDEX.md` (complete skill roster)
- Archive: `memory/swarm/skills/archive/` (40+ skill agents)
  - Assessment Science: `assessment-science-agent.md` (DIF, validation)
  - CEO Report: `ceo-report-agent.md` (business language translation)
  - Communications Strategist: `communications-strategist.md` (narrative, voice)
  - Community Manager: `community-manager-agent.md` (engagement, streaks)
  - Competitor Intelligence: `competitor-intelligence-agent.md`
  - Data Engineer: `data-engineer-agent.md` (PostHog, taxonomy)
  - DevOps/SRE: `devops-sre-agent.md` (Railway, scaling)
  - Financial Analyst: `financial-analyst-agent.md` (runway, LTV/CAC, economy)
  - Investor/Board: `investor-board-agent.md` (fundraising)
  - Legal Advisor: `legal-advisor.md` (GDPR, regulatory)
  - Payment Provider: `payment-provider-agent.md` (Paddle)
  - Performance Engineer: `performance-engineer-agent.md` (latency, load)
  - PR/Media: `pr-media-agent.md` (press, positioning)
  - QA/Quality: `qa-quality-agent.md`, `quality-assurance-agent.md`
  - Technical Writer: `technical-writer-agent.md` (API docs)
  - UX Research: `ux-research-agent.md` (JTBD)
  - University Partner: `university-ecosystem-partner-agent.md` (B2C acquisition)

**Skill Loading Matrix**
- See `docs/CLAUDE.md` section "Skills Matrix" (which skills for which tasks)
- Agent Routing: `memory/atlas/agent-communication-protocol.md`

---

### 11. Products (VOLAURA, MindShift, LifeSim, BrandedBy, ZEUS)

**VOLAURA (This Product)**
- Project Overview: `docs/PROJECT-OVERVIEW.md` (11KB)
- Strategy: `docs/MASTER-STRATEGY.md` (positioning)
- Vision: `docs/VISION-FULL.md` (mission statement)
- Product Spec: `docs/product/` (user personas, business model, KPIs)

**MindShift (Focus & Habits)**
- Integration: `docs/MINDSHIFT-INTEGRATION-SPEC.md` (focus sessions, psychotype)
- State: `memory/context/mindshift-state.md` (current development status)
- Mega Plan: `docs/MEGAPLAN-MINDSHIFT-LAUNCH-2026-04-08.md` (4/8, latest roadmap)

**Life Simulator (Godot 4 Game)**
- Integration: `docs/LIFE-SIMULATOR-INTEGRATION-SPEC.md` (character stats, crystals)
- Ecosystem Linkage: `memory/atlas/ecosystem-linkage-map.md` (how crystals flow)

**BrandedBy (AI Twin / Video)**
- AI Twin Concept: `docs/AI-TWIN-CONCEPT.md` (positioning, use cases)

**ZEUS (Autonomous Agent Framework)**
- ADR-008: `docs/adr/ADR-008-zeus-governance-layer.md` (Windows + ngrok)
- See CONSTITUTION for full spec

---

### 12. CEO Context (Working Style, Mistakes, Patterns, Deadlines)

**CEO's Working Style & Protocol**
- Protocol: `.claude/rules/ceo-protocol.md` (when CEO is consulted, what NOT to do)
- Working Style: `memory/context/working-style.md` (Yusif's communication preferences)
- CEO Absence Protocol: `memory/context/ceo-absence-protocol.md` (autonomy rules)

**Mistakes & Learning**
- Mistakes Log: `memory/context/mistakes.md` (52KB, 100+ entries, Class 1-11 severity)
- Key Patterns: `memory/context/patterns.md` (73KB, what works, documented patterns)
- Session Findings: `docs/SESSION-FINDINGS.md` (4/12, fresh discoveries)
- Decisions Log: `docs/DECISIONS.md` (84KB, retrospectives + reasoning)

**Sprint & Timeline**
- Current Sprint: `memory/context/sprint-state.md` (4/12, where we are)
- 500-Hour Plan: `docs/500-HOUR-PLAN.md` (4/11, long-term roadmap)
- Execution Plan: `docs/EXECUTION-PLAN.md` (35KB, sprint checklist)
- Deadlines: `memory/context/deadlines.md` (milestones, blocked items)

**Performance & Quality**
- CEO Performance Review (Swarm): `docs/CEO-PERFORMANCE-REVIEW-SWARM.md` (31KB, 360 feedback)
- Unfulfilled Promises: `docs/UNFULFILLED-PROMISES.md` (4/10, debt tracking)

**Ecosystem Context**
- Ecosystem Contract: `memory/context/ecosystem-contract.md` (roles, responsibilities)
- Ecosystem Agents Contract: `memory/context/ecosystem-agents-contract-v1.md` (agent SLA)
- Heartbeat Protocol: `memory/context/ecosystem-heartbeat-protocol.md` (daily standup)

---

### 13. Research (Unimplemented Insights)

**Market & Domain Research**
- Neurocognitive Architecture: `docs/research/NEUROCOGNITIVE-ARCHITECTURE-2026.md` (assessment design)
- Universal Weapon Research: `docs/research/UNIVERSAL-WEAPON-RESEARCH-2026-04-04.md` (29KB, market analysis)
- Gemini Research All: `docs/research/gemini-research-all.md` (111KB, domain deep-dive)

**Geographic & Pricing Research**
- Geo-Pricing: `docs/research/geo-pricing-research.md` (regional tiers)
- Ecosystem Design: `docs/research/ecosystem-design-research.md` (product fit)
- Blind Spots: `docs/research/blind-spots-analysis.md` (assumptions to test)

**Innovation & Swarm**
- Swarm Innovation: `docs/research/swarm-innovation-research.md` (autonomous teams)

**Country Market Entry**
- Research Template: `docs/NOTEBOOKLM-COUNTRY-RESEARCH.md` (how to research countries)

---

### 14. Engineering Skills & Processes

**Code Quality & Review**
- Security Review: `docs/engineering/skills/SECURITY-REVIEW.md` (10-point checklist)
- Code Review: `docs/engineering/skills/TDD-WORKFLOW.md` (Red-Green-Refactor)
- Continuous Learning: `docs/engineering/skills/CONTINUOUS-LEARNING.md` (session protocols)

**Architecture & API**
- API Contracts: `docs/engineering/API-CONTRACTS.md` (56KB, all endpoints)
- API Reference: `docs/API-REFERENCE.md` (4/3, 22KB, 115 endpoints)
- State Management: `docs/engineering/STATE-MANAGEMENT.md` (Zustand, Query)

**Testing & Quality**
- Testing Strategy: `docs/engineering/TESTING-STRATEGY.md` (26KB, unit/integration/e2e)
- Comprehensive Test Plan: `docs/COMPREHENSIVE-TEST-PLAN.md` (32KB)
- Functional Test Strategy: `docs/FUNCTIONAL-TEST-STRATEGY.md` (38KB)
- E2E Audit Summary: `docs/E2E-AUDIT-SUMMARY.md` (4/4, 14KB)

**Technical Reference**
- I18N Keys: `docs/I18N-KEYS.md` (14KB, AZ+EN translation keys)
- AI Orchestration: `docs/engineering/AI-ORCHESTRATION-GUIDE.md` (Gemini + LLM routing)

---

### 15. Governance & Constitution

**VOLAURA Governance**
- Constitution: `docs/ECOSYSTEM-CONSTITUTION.md` (4/12, 86KB, v1.7)
  - 5 Foundation Laws (NEVER RED, Energy Adaptation, Shame-Free, Animation Safety, One Primary Action)
  - 19 P0 blockers (Energy picker, Pre-Assessment Layer, DIF audit, SADPP, etc.)
  - 8 perspectives in DSP council
  - 39 agents in ZEUS routing table

**Decision-Making & Simulation**
- Decision Simulation Protocol: `docs/engineering/DECISION-SIMULATION-PROTOCOL.md` (6 personas, 4+ paths, 50-point scoring)
- Criteria Templates: `docs/ACCEPTANCE-CRITERIA-TEMPLATES.md` (AC format)

**Rules & Mandatory Protocols**
- Mandatory Rules: `docs/MANDATORY-RULES.md` (7 non-negotiable rules)
- Best Practices: `docs/BEST-PRACTICES.md` (patterns, anti-patterns)
- Backend Rules: `.claude/rules/backend.md` (FastAPI, Supabase, logging)
- Frontend Rules: `.claude/rules/frontend.md` (Next.js 14, TypeScript strict)
- Database Rules: `.claude/rules/database.md` (migrations, RLS, pgvector)
- Secret Key Protocol: `.claude/rules/secrets.md` (API key handling)

---

## Search Tips

### By Technology
- **Next.js / Frontend**: `docs/design/`, `docs/engineering/STATE-MANAGEMENT.md`
- **FastAPI / Backend**: `docs/engineering/API-CONTRACTS.md`, `.claude/rules/backend.md`
- **Supabase / Database**: `docs/adr/ADR-003-auth-verification.md`, `.claude/rules/database.md`
- **IRT / Assessment**: `docs/adr/ADR-004-assessment-engine.md`, `docs/adr/ADR-005-aura-scoring.md`
- **Security**: `docs/engineering/skills/SECURITY-REVIEW.md`, `docs/SECURITY-STANDARDS.md`

### By Role
- **CTO (Technical Lead)**: `docs/ARCHITECTURE_OVERVIEW.md`, `docs/adr/`, `memory/atlas/`
- **Product Lead**: `docs/CUSTOMER-JOURNEY-MAP.md`, `docs/product/USER-PERSONAS.md`, `docs/KPIs.md`
- **Growth/Marketing**: `docs/GROWTH-STRATEGY-PLAYBOOK.md`, `docs/growth/`
- **Designer/UX**: `docs/design/DESIGN-SYSTEM-AUDIT.md`, `docs/CUSTOMER-JOURNEY-MAP.md`
- **CEO/Founder**: `memory/context/sprint-state.md`, `docs/DECISIONS.md`, `docs/500-HOUR-PLAN.md`

### By Freshness (Most Recent Updates)
- **2026-04-12**: `docs/ARCHITECTURE_OVERVIEW.md`, `docs/ECOSYSTEM-CONSTITUTION.md`, `memory/atlas/memory-architecture-proposal.md`
- **2026-04-11**: `docs/adr/ADR-004-assessment-engine.md`, `docs/engineering/SECURITY-STANDARDS.md`, `memory/context/sprint-state.md`
- **2026-04-10**: `docs/UNFULFILLED-PROMISES.md`

### By Document Size (Large = Comprehensive)
- **80KB+**: `docs/DECISIONS.md`, `docs/ECOSYSTEM-CONSTITUTION.md`, `docs/SESSION-FINDINGS.md`
- **30-50KB**: `docs/CUSTOMER-JOURNEY-MAP.md`, `docs/GROWTH-STRATEGY-PLAYBOOK.md`, `docs/FUNCTIONAL-TEST-STRATEGY.md`
- **10-20KB**: Most ADRs, architecture docs, integration specs

---

## How to Contribute to This Index

When creating new documentation:
1. Place in appropriate directory (`docs/`, `memory/`, etc.)
2. Use markdown (.md) format
3. Include a freshness date at the top
4. Add entry to this index under relevant topic

When updating existing docs:
1. Update the file's date in this index
2. Move it to "Recently Updated" section if major change
3. Update `docs/SESSION-FINDINGS.md` with discovery

---

**This index is maintained automatically. Last sync: 2026-04-12 15:30 UTC**
