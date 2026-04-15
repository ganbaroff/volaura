# Research-first roadmap — where VOLAURA may have hand-built what already exists

**Created:** 2026-04-15 · **Author:** Terminal-Atlas after CEO directive "я показал тебе лишь одну ветвь, а у тебя целое дерево"
**Purpose:** map every place where we chose to hand-build without first checking if a production-proven solution exists. Triage by impact × unknown-area. Schedule research before future implementation work.

---

## Branches already researched (2026-04-15 session)

| Branch | Verdict | Decision |
|---|---|---|
| External agent systems (swarm frameworks, memory layers) | `docs/research/external-agent-systems/analysis-protocol.md` | Standing rubric written, applied to CrewAI/LangGraph candidates |
| Recurring-symptoms watchdog | `docs/research/recurring-symptoms-watchdog/` | Don't-buy-build: Sentry webhook + fix-of-fix GitHub Action |
| Agent action-layer frameworks | `docs/research/agent-action-layer/` | HYBRID — keep custom shell, absorb 3 patterns (circuit-breaker, HITL full-payload, @tool decorator) |

## Branches queued for research — ranked by impact × risk of hand-built drift

Priority math: `impact × (blast-radius if wrong) × unknown-area-factor`. Top items should gate implementation work until researched.

### P0 — core product risk

1. **IRT / CAT assessment engine** (`apps/api/app/core/assessment/engine.py`). We wrote pure-Python 3PL + EAP from papers. If a production-tested library (concert, pyIRT, catR-python, GIFT) exists with better numerical stability, calibration, DIF analysis — we're competing with hand-made while peers use battle-tested. This is our core moat; the cost of subtly wrong psychometrics is a brand failure at launch. **Research triggers:** IRT library adoption, anti-gaming research, adaptive testing production examples, published DIF analysis open datasets.

2. **RLS policy testing + bypass surface**. Migration landed today adding a trigger. But we have zero systematic RLS test suite. pgtap, Supabase's own test SDK, supatest — there is a pattern library we've skipped. Security audit P1 finding in ghost-audit §2.1 is a symptom: RLS drift keeps re-appearing because we don't test it. **Research triggers:** pgtap production setups, Supabase RLS testing blogs 2024-2026, attack-surface checklists, `pg_policies` introspection tools.

3. **GDPR Article 22 automated-decision consent** (ghost-audit flagged, Legal Advisor swarm raised). We process users' assessment → AURA score → algorithmic badge tier assignment. This is automated decision-making under GDPR. We have a consent checkbox at signup but no Article 22 explicit opt-in + explanation + human-review-right flow. SaaS like OneTrust, TermsFeed, iubenda have templated flows. Open-source: Cookiedough, GDPR-compliance-kit. Hand-rolling this is compliance risk AZ PDPA will eventually mirror. **Research triggers:** OSS GDPR Article 22 flow templates, AZ PDPA compliance vendors, EdTech companies' published consent UX.

### P1 — infrastructure risk

4. **Workflow engine (cron + jobs)**. We have 10+ GitHub Actions cron workflows (swarm-daily, atlas-self-wake, watchdog, digest, heartbeat, proposal-cards, distill-weekly, screenshot batches, health checks). Every one is custom YAML with bash commit-back patterns. At 20+ workflows the complexity breaks. Temporal.io (open-core), Inngest, Trigger.dev, Dagger — there is a workflow-engine category we haven't considered. **Research triggers:** solo-founder cron-stack case studies, Temporal free-tier pricing, Inngest vs Trigger.dev comparison 2026, GitHub Actions scalability war stories.

5. **LLM observability**. We ship LLM calls to 5 providers without systematic trace/cost monitoring. Langfuse partially wired (~50%). Phoenix (Arize), Helicone, Langsmith — each has different strengths. Ghost-audit found we don't know when an LLM chain silently fails on Railway because we don't have cost-per-user-session dashboards. **Research triggers:** self-hosted LLM observability 2026, Langfuse production case studies, cost-overrun patterns from AI startups.

6. **Proposals workflow**. Custom JSON file with atomic writes. GitHub Projects API, Linear API, Plane.so (OSS) handle proposal-queue + approval-lifecycle much better. Our judge+distiller landed today but lives on top of a JSON file that has TOCTOU races (ghost-audit P2). **Research triggers:** Plane.so feature match vs our JSON, Linear approval workflows, queue-on-Postgres patterns for approval.

7. **Design token pipeline**. globals.css 433 lines hand-written. Figma Variables → code sync (Supernova, Style Dictionary, Tokens Studio) is a mature category. We've already flagged three token-vs-Figma drifts today (02-FIGMA-RECONCILIATION). Doing it hand is fine for 20 tokens; at 80+ the drift never ends. **Research triggers:** Style Dictionary + Supabase stack, Figma API → globals.css automation, design-tokens-cli examples.

### P2 — quality-of-life / future work

8. **Persona-aware LLM voice consistency**. My voice-breach hook is regex. NeMo Guardrails, Guardrails-AI, Instructor library add structured second-model check ("does this response match Atlas tone?"). Agents can enforce voice via model-level rather than regex-level. **Research triggers:** persona-guardrails production case studies, second-LLM voice check cost.

9. **AZ translation QA pipeline**. Hand-edited common.json. Crowdin, Lokalise, Locize, Tolgee (OSS) handle translator workflows, key drift detection, MT-QA at scale. Not urgent at 200 keys, urgent at 2000. **Research triggers:** OSS translation QA for Next.js 14 + i18next, Tolgee self-hosted setup.

10. **Cross-product event bus MindShift↔VOLAURA** (INC-019). We use `character_events` Postgres table + manual writes from each app. Kafka, NATS, Redpanda, Supabase Realtime (already present partially) — the messaging-infra category. INC-019 MindShift half-broken is a symptom of no formal event schema or pub-sub abstraction. **Research triggers:** Supabase Realtime production case studies for event bus, NATS vs Postgres LISTEN/NOTIFY, EventCatalog.

11. **Mobile app template** (Expo future). We haven't started mobile but the ecosystem has Ignite, Bluesky's template, t3-turbo. Pre-research saves weeks. **Research triggers:** 2026 Expo Router monorepo templates, shadcn-native kit, cross-product identity flow on mobile.

12. **Payment integration depth**. Stripe Atlas incorporated yesterday. Stripe Connect / Treasury / Billing patterns — we know Stripe-standard. But AZ-local payments (Dodo approved in env vars but unused) + crypto — we haven't compared. **Research triggers:** Dodo Payments production case studies, multi-gateway architecture for AZ+global, subscription lifecycle OSS libs.

13. **Compliance surface beyond GDPR**: SOC 2, AZ PDPA specifics, AI Act classifier, DPIA templates. Relevant once B2B hiring orgs come. **Research triggers:** AI-Act high-risk-system checklist for hiring platforms, SOC 2 for solo founders, DPIA for psychometric scoring.

### P3 — background learning

14. **Conversational memory architectures**. Already partially covered in external-agent-systems/. Revisit when building ZEUS formally — Cognee, Letta, MemGPT, Zep, Graphiti, Hindsight.
15. **Anti-gaming adversarial LLM eval** (ghost-audit quality_gate finding). We have keyword_fallback + 3-style attack generator. Constitutional AI, HELM benchmarks, OpenAI's own adversarial eval libs — research.
16. **Accessibility automated testing**. We pay attention to a11y but no axe-core + Lighthouse CI in pipeline. `pa11y-ci`, `@axe-core/playwright`, `ACT-Rules` — research.
17. **Session replay / funnel analysis**. PostHog / Hotjar / LogRocket for watching actual user drop-off. Essential before launch, not urgent this week.

---

## Research-first rule extension (proposed addition to `.claude/rules/atlas-operating-principles.md`)

Current research-first rule (in `~/.claude/rules/research-first.md`) applies to any library/architecture decision. This roadmap extends it:

> **Tree-wide research posture:** before any implementation task estimated at >1 day of work, Atlas must cite either (a) a verdict from `docs/research/<branch>/summary.md` covering this area, OR (b) explicit rationale for "no pre-existing solution applies, building from scratch." If neither is provided, spawn a research agent first.

Enforcement: pre-sprint check in sprint-state.md asks "какая ветка research покрывает эту работу?" If answer is empty → research spawn before code.

---

## Next-session trigger list

When the next block of implementation work opens, run these 4 research spawns in parallel before coding:

1. P0.1 IRT/CAT library scan — look for `concert`, `pyIRT`, `catR-python`, `GIFT`, HuggingFace leaderboards for psychometric models. Output `docs/research/irt-cat-libraries/summary.md`.
2. P0.2 pgtap + Supabase RLS testing stack — look for production setups. Output `docs/research/rls-testing/summary.md`.
3. P0.3 GDPR Article 22 consent flow templates — OSS + compliance-vendor templates. Output `docs/research/gdpr-article-22/summary.md`.
4. P1.4 Workflow engine comparison (Temporal, Inngest, Trigger.dev) — solo-founder fit. Output `docs/research/workflow-engines/summary.md`.

Budget per research: 25 min, ~100K tokens, <$1 per topic via free-tier chain.

---

## Principle

CEO's directive is structural: stop hand-building when a mature solution exists. The reason it keeps happening is training weights bias me toward "write code" — I see a problem, I draft an implementation, I ship. Research-first inverts that: I see a problem, I spawn a researcher, I evaluate solutions, then I decide build/adopt/hybrid. Applies to every branch of the tree, not just the one CEO points at today.
