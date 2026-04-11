# EXECUTION_PLAN — Swarm-Orchestrated Path to World-Class State

**Version:** 1.0 (2026-04-12, Session 93)
**Scope:** The concrete P0/P1/P2 sequencing to move from the as-built state (see `docs/ARCHITECTURE_OVERVIEW.md`) to the target state described in `AI_Ecosystem_Architecture.docx`.
**Complement to:** `docs/EXECUTION-PLAN.md` (with hyphen — existing sprint-level file). This file (with underscore) is the ecosystem-level strategic plan; the existing one is the sprint-level execution log. They will be reconciled into one file per CEO decision #5.

---

## 0. GUIDING PRINCIPLES

1. **Working systems first, governance second, refactor third.** Anything currently in production stays working. No refactor may break the assessment → AURA → share flow that was verified end-to-end this session.
2. **Additive over replacive.** New governance, new infrastructure, new instrumentation is added alongside existing code. Nothing gets ripped out until its replacement has been running on prod for at least 7 days without a regression.
3. **Every P0 has a verification tool call.** An item cannot be marked "done" without an artifact (commit SHA, governance event ID, script output) that a future CTO could replay.
4. **CEO decisions precede CTO execution.** The 5 decisions listed at the end of this document must be answered before any item that depends on them can be started.
5. **Swarm does the repetitive work; CTO-Hands does the judgement calls.** If a task is mechanical (migration, test fixture, format fix, doc drafting), delegate to the Python swarm or a Claude Code sub-agent. Only touch it with the main CTO-Hands context when architectural judgement is required.

---

## 1. TOP-20 RECOMMENDATIONS (REPRISED FROM THE AI COUNCIL) — P0/P1/P2

These are the 20 items synthesised from the 7-source strategic brief, mapped against the as-built state.

### P0 — Must finish within the next 2 sessions (cannot ship trusted first user flow without these)

| # | Item | Effort | Owner | Dependency |
|---|---|---|---|---|
| 1 | **LLM golden dataset tests** — build 50-100 curated (prompt, expected behaviour) pairs for assessment evaluator + AURA explanation + MindShift coaching. Run in CI via Promptfoo or LangFuse, assert minimum quality threshold on every prompt/agent change. | 1-2 sessions | CTO-Hands + swarm QA agent | CEO decision #5 (ADR process ratification — ADR-011 "LLM eval methodology") |
| 2 | **MindShift clinical safety thresholds** — hardcoded crisis keyword list + deterministic escalation to human resources, bypassing LLM entirely when triggered. Required before any public ADHD-user onboarding. | 1 session | CTO-Hands | CEO decision #3 (clinical safety threshold ratification) |
| 3 | **8-12 foundational ADRs** — MADR-format records for: monorepo structure, database strategy, auth/identity, AI gateway, swarm orchestration, observability stack, secrets strategy, prompt governance, positioning (verified-talent vs volunteer), governance layering (this plan's parent), LLM eval methodology, Ethics Advisory Board status. Written retroactively where decisions already exist, prospectively for open ones. | 1 session | CTO-Hands drafts, CEO ratifies | CEO decision #5 (ADR process) |
| 4 | **Shadow testing pipeline for LLM upgrades** — before a model cutover, route a sampled % of real prod requests to both the old and new model in parallel, diff the outputs, surface quality regressions in a governance event. | 2 sessions | swarm infra agent | item #1 (eval harness) |
| 5 | **Fix pre-existing CI red** — 10 consecutive commits failing on ruff UP041/N806/B904 violations in `bars.py`/`deps.py` and pnpm lockfile drift. Not caused by Session 93 — existed before. Three options: (a) auto-fix all ruff findings, (b) downgrade the lint rules that are firing, (c) fix by hand. Recommend (a) with `ruff check --fix` + review. | 1 session | swarm code-review mode auto-fix + CTO-Hands review | none — pre-existing mess |
| 6 | **Whistleblower Auditor Agent** — independent agent outside the CTO hierarchy with sole job of detecting Level 0 violations, generating cryptographic proof, and alerting CEO out-of-band via Telegram. Lives in `packages/swarm/auditor.py`, runs on every deploy + daily. | 1-2 sessions | CTO-Hands | `docs/CONSTITUTION_AI_SWARM.md` ratification (trivial) |
| 7 | **Apply the 2 migrations to staging (once staging env exists)** — currently we have only prod Supabase. Session 93 pushed migrations directly to prod. The industry norm is staging → prod. Creating a staging Supabase project and wiring the migration pipeline through it is a P0 governance gap. | 1 session | CTO-Hands, Supabase MCP | CEO decision #4 (budget for second Supabase project ~$0 free tier but another 512MB) |

### P1 — Next month, before scaling beyond ~100 users

| # | Item | Effort | Owner |
|---|---|---|---|
| 8 | **AGENTS.md manifest per workspace** — `apps/web/AGENTS.md`, `apps/api/AGENTS.md`, `packages/swarm/AGENTS.md` each declaring architectural boundaries, data flow rules, error handling patterns, test expectations. Machine-readable for future agents, human-readable for onboarding. | 1 session | swarm docs agent + CTO-Hands review |
| 9 | **OpenTelemetry instrumentation on all LLM + agent spans** — every LLM call wrapped in an OTel span with `model_name`, `prompt_tokens`, `completion_tokens`, `latency_ms`, `agent_role`, `trace_id`. Export to LangFuse or Phoenix. Prompt payloads sent only to the secure observability backend, never to standard logs. | 2 sessions | swarm infra agent |
| 10 | **Prompt semantic versioning** — every prompt gets an ID and a X.Y.Z version in a central registry (start with a directory `packages/swarm/prompts/` with one file per prompt). Each change requires a change-log entry. Production uses a pinned version; staging can use tip-of-main. | 2 sessions | CTO-Hands + swarm docs agent |
| 11 | **Reviewer Agent PR gate** — per-PR swarm that checks diff against Ecosystem Constitution, AI Swarm Constitution, and AGENTS.md rules. Blocks merge on Level 0 violations. Extends `session-end.yml` to also run `autonomous_run --mode=code-review` synchronously on the PR diff. | 1 session | CTO-Hands |
| 12 | **HITL Ring overrides** — PRs that touch `supabase/migrations/`, `CLAUDE.md`, `docs/ECOSYSTEM-CONSTITUTION.md`, `docs/CONSTITUTION_AI_SWARM.md`, or `.github/workflows/` require CEO approval before merge. Implemented as a GitHub Actions required-reviewer rule. | 0.5 session | CEO clicks in GitHub settings, CTO-Hands prepares the rule file |
| 13 | **Data classification matrix (A/B/C) formalised** — a table per Supabase table declaring which category its data falls in and which products may read/write it. Lives in `docs/DATA_CLASSIFICATION.md`. Blocks any new migration that declares a Category A column in a cloud-aggregated table. | 1 session | CTO-Hands + Supabase schema audit |
| 14 | **Swarm cooldown + quota awareness in model_router** — when Gemini 2.0 Flash hits free-tier quota (as it did this session), mark that provider as "hot" for N minutes and prefer the next entry in the chain. Prevents the current failure mode where 4 agents died on quota-exhausted Gemini. | 1 session | CTO-Hands |
| 15 | **Migrate pnpm lockfile drift + set up renovate/dependabot** — fix the `pnpm install --frozen-lockfile` CI failure by reconciling the lockfile, then set up Renovate / Dependabot to keep dependencies green automatically. | 1 session | swarm code-review auto-fix + CTO-Hands |

### P2 — Strategic, 3+ months out, requires CEO buy-in

| # | Item | Effort | Owner |
|---|---|---|---|
| 16 | **Event sourcing + CQRS for `zeus.governance_events`** — treat governance as an append-only event stream, build materialised views for read models (CEO dashboard, compliance audit, swarm introspection). | 3-5 sessions | CTO-Hands + schema agent |
| 17 | **Shapley-based blame attribution for multi-agent failures** — when a deploy fails or a proposal cycle produces nothing useful, mathematically distribute responsibility across the participating agents. Feeds into Dynamic Trust Scoring. | Research + 2-3 sessions | ML-oriented agent |
| 18 | **Privacy-preserving logging with hashed PII** — zero raw user payload in logs. All user content hashed with a rotating salt before ingestion. Zero-knowledge proofs for compliance audits. | 2-3 sessions | CTO-Hands |
| 19 | **Supervisor graph refactor (LangGraph or bespoke)** — migrate the current flat swarm to a supervisor pattern where a top-level agent routes tasks to specialists, state transitions are explicit, and the graph is introspectable. Alternative: stay with the current Python swarm and add formal graph visualisation. | 5+ sessions | CTO-Brain architecture proposal + CTO-Hands execution |
| 20 | **Ethics Advisory Board with institutional veto** — formal external board (clinical psychologists, data privacy experts, ND advocates) with documented veto power over feature launches that touch mental-health or volunteering surfaces. Not just an advisory group. | CEO action (recruitment + legal) | CEO |

---

## 2. SPRINT-LEVEL SEQUENCING (6 WEEKS)

The 20-item roadmap above is not a week-by-week plan; it's a backlog. This section sequences the P0 work into concrete 1-week sprints that can slot into the existing Sprint 0 / Sprint 1 structure of the repo.

### Sprint 0.5 — Post-Session-93 Stabilisation (this week)

**Goal:** close the P0 items that are architecturally trivial and unblock everything else.

1. Create this sprint's ADR: `docs/adr/011-llm-eval-methodology.md` (P0 #1 dependency).
2. Draft the other 7-8 foundational ADRs as skeletons (item #3).
3. Fix `ci.yml` ruff/lockfile red so main is green again (item #5).
4. Ratify `docs/CONSTITUTION_AI_SWARM.md` by CEO sign-off logged as governance event.
5. Start the LLM eval dataset with 20 seed entries for VOLAURA assessment evaluator.

**Done criteria:** CI green on main, CONSTITUTION_AI_SWARM v1.0 active, ADR skeletons linked from each relevant code area.

### Sprint 1 — Clinical Safety and Whistleblower (next week)

**Goal:** bring MindShift into a state where we can safely open it to any real user with ADHD / anxiety.

1. Item #2: hardcoded crisis keyword list + deterministic escalation path. Not an LLM decision — a match-and-route rule. Escalation target: Telegram bot alert to CEO + web link to AZ/global crisis hotlines.
2. Item #6: draft and deploy the Auditor Agent (item #6). Initial scope: monitor `zeus.governance_events` for Level 0 violations, check every commit for bypassed approvals, emit critical event + Telegram alert on detection.
3. First 50 entries in the LLM golden dataset (item #1 continuation).

**Done criteria:** MindShift crisis escalation path tested end-to-end (synthetic trigger). Auditor Agent running on daily cron, has produced at least one benign `auditor_scan_complete` event.

### Sprint 2 — Observability and Prompts (two weeks out)

**Goal:** see what the swarm is actually doing and make every prompt a versioned artifact.

1. Item #9: OpenTelemetry instrumentation + LangFuse/Phoenix backend.
2. Item #10: prompt registry with X.Y.Z versioning, staged promotion (dev → staging → prod).
3. Item #14: cooldown / quota awareness in model_router.
4. Complete the 50 → 100 golden dataset (item #1).

**Done criteria:** one full week of LLM traces visible in observability backend. Prompt registry contains at least 10 versioned prompts. Model router no longer selects rate-limited providers.

### Sprint 3 — Staging Environment and Shadow Testing (three weeks out)

**Goal:** separate prod from experimental work.

1. Item #7: staging Supabase project + migration pipeline through staging → prod.
2. Item #4: shadow testing pipeline for LLM upgrades.
3. Item #8: AGENTS.md manifests for apps/web, apps/api, packages/swarm.
4. Item #11: Reviewer Agent per-PR gate.

**Done criteria:** a migration can be applied to staging, verified, then promoted to prod via a single command. Shadow testing catches at least one synthetic regression.

### Sprint 4 — Governance and Data Classification (four weeks out)

**Goal:** finish the P1 governance work before scaling beyond ~100 users.

1. Item #12: HITL Ring override GitHub Action rule.
2. Item #13: Data Classification Matrix formalised.
3. Item #15: Dependency auto-update via Renovate.
4. Complete remaining ADRs from the foundational batch.

**Done criteria:** ~12 ADRs active. HITL rule blocks self-modification attempts. Data classification audit of every Supabase table complete.

### Sprint 5 — P2 Strategic Work Starts (five weeks out, ongoing)

**Goal:** begin the architecturally deep work that pays off over months.

1. Item #19: CTO-Brain writes the supervisor-graph refactor ADR; CTO-Hands drafts migration path.
2. Item #16: event sourcing proof-of-concept on `zeus.governance_events`.
3. Item #18: privacy-preserving logging proof-of-concept.
4. Item #20: CEO begins Ethics Advisory Board recruitment.

**Done criteria:** ADRs drafted, experiments running in a sandbox, no prod impact.

---

## 3. WHAT BLOCKS WHAT

```
CEO decision #1 (positioning)    →  ADR-009 (positioning)  →  all user-facing copy ADR
CEO decision #2 (dual-runtime)   →  ADR-012 (MindShift runtime)  →  Sprint 1 clinical safety scope
CEO decision #3 (crisis threshold) →  Sprint 1 clinical safety  →  MindShift first-user onboarding
CEO decision #4 (staging budget)   →  Sprint 3 staging env  →  all future migration safety
CEO decision #5 (ADR process)      →  Sprint 0.5 ADR batch  →  everything below
```

Without CEO decisions #3 and #5, Sprint 0.5 cannot properly start. Without #1 and #2, Sprint 1 risks touching copy or architecture that is under dispute.

---

## 4. THE 5 CEO DECISIONS

These five items are the **only** strategic calls that are currently blocking CTO work. Each has a short context, a recommended choice, and a reversibility note. CEO is free to pick any option; these are recommendations from CTO-Hands, not directives.

### Decision #1 — VOLAURA positioning: "verified talent platform" OR "volunteer platform"?

- **Context.** Sprint E1 locked decision (2026-03-29) sets VOLAURA as "verified talent platform, never volunteer platform" in `memory/context/patterns.md` and the Ecosystem Constitution. The recent briefing uses "волонтёрская платформа" in shorthand. The two framings target different market segments (B2B compliance talent search vs corporate CSR volunteer matching) and imply different landing copy, different ADR, different revenue model.
- **Recommendation (CTO-Hands).** **Keep "verified talent platform" as external positioning** because the existing AURA score + adaptive assessment infrastructure is already built against that narrative. Add "volunteer marketplace" as a **sub-product** or **monetisation stream** (a specific kind of placement offered to verified-talent users).
- **Reversibility.** Low — position can be re-framed, but every user-facing string, landing page, marketing asset, and legal doc is built against the current frame. A reversal is 1-2 weeks of copy work plus a website redesign.
- **Required from CEO.** One line: ratify the current lock OR explicitly supersede it with a new ADR.

### Decision #2 — Dual-runtime mandate for MindShift (on-device SLM vs cloud Gemini)?

- **Context.** The AI council brief (Gemini-3 section) mandates on-device Small Language Model execution for all MindShift cognitive data to eliminate cloud monetisation risk. Reality: current MindShift uses Supabase + Gemini cloud. A dual-runtime architecture is technically feasible (local Ollama + cloud fallback) but imposes a hardware minimum on users (RAM / GPU) that limits the addressable market.
- **Recommendation (CTO-Hands).** **Adopt a tiered model.** Non-sensitive features (UI coaching, habit summaries) use cloud Gemini. Sensitive features (raw journal entries, crisis detection, trauma logs) are gated behind a "privacy mode" that defaults to local Ollama when available and refuses execution when not. This preserves the growth path while protecting the highest-sensitivity data.
- **Reversibility.** Medium — a full cloud-only architecture is an easy rebuild; on-device adoption requires ongoing Ollama support which is non-trivial to retract once users are depending on it.
- **Required from CEO.** Yes/no/tiered. If tiered, CEO defines the cutoff between "cloud-OK" and "local-only" features.

### Decision #3 — MindShift crisis escalation thresholds

- **Context.** Blocking Sprint 1 entirely. We need specific keyword/phrase lists + behavioural patterns that deterministically trigger crisis routing, bypassing the LLM. The current code has none. CTO cannot define these — they are clinical decisions.
- **Recommendation (CTO-Hands).** Two options: (a) use a published list from an established organisation (e.g. Crisis Text Line's public protocol), ratify the list as an ADR, revise with a clinical advisor before Sprint 1. (b) delay Sprint 1 until a licensed clinician signs off on the list.
- **Reversibility.** Zero — once shipped and a user is routed, we're in a liability zone. Get it right the first time.
- **Required from CEO.** Choose (a) or (b), and if (a), nominate the source list.

### Decision #4 — Staging Supabase environment: spin up now or defer?

- **Context.** Session 93 applied migrations directly to prod because there is no staging. This is a real governance gap — any future migration with a bug will hit users. Cost: a second Supabase free-tier project (free for 512 MB), plus ~1 hour of wiring.
- **Recommendation (CTO-Hands).** **Yes, spin up now.** Free tier covers it. The cost is CTO time, not money. Blocking P1 reviewer-agent gate and shadow testing work.
- **Reversibility.** Trivial — project can be deleted if unused.
- **Required from CEO.** Go / no-go.

### Decision #5 — ADR process ratification (MADR template, `docs/adr/` directory, link from every PR)?

- **Context.** We have `docs/adr/009-crewai-adoption.md` and `010-defect-autopsy.md` — exactly 2 ADRs in a project with 70+ architectural docs. Perplexity recommends 8-12 foundational + 1-2 per quarter. CTO-Hands recommends adopting MADR as the template and making ADRs a PR requirement for architecturally significant changes.
- **Recommendation (CTO-Hands).** **Adopt MADR, write the 8-12 foundational batch this sprint, make ADR links part of the PR template.** Overhead is low (one 30-line markdown per major decision), payoff is large (prevents context drift like the Perplexity incident of 2026-04-11).
- **Reversibility.** Trivial — can be dropped at any time, ADRs remain as historical record.
- **Required from CEO.** Go / no-go. On go, CTO-Hands drafts the 8-12 skeletons this sprint.

---

## 5. SUCCESS METRICS

This plan succeeds if, by end of Sprint 5 (6 weeks):

1. **CI green on main** for at least 10 consecutive commits.
2. **All 5 Foundation Laws + 8 Crystal Laws + 12 Swarm Principles** are represented by at least one automated check (test, ruff rule, governance event, or reviewer agent rule).
3. **LLM golden dataset** contains 100+ entries and runs on every prompt change.
4. **Staging environment** is wired and has caught at least one migration regression before prod.
5. **Every PR** over 50 lines has an ADR link OR a justification for why one isn't needed.
6. **Whistleblower Auditor Agent** has completed 30+ daily scans and detected at least one benign `auditor_scan_complete` event per day.
7. **zero real users affected by a production bug** during the 6 weeks (Session 93 E2E established the baseline).
8. **CEO spent fewer than 2 hours per week on CTO-level decisions** (the whole point of CTO-Brain + CTO-Hands is to keep CEO in CEO-level work).

---

## REVISION HISTORY

| Version | Date | Change | Author |
|---|---|---|---|
| 1.0 | 2026-04-12 | Initial sequenced plan derived from `AI_Ecosystem_Architecture.docx` top-20 + Session 93 as-built state | Claude Opus 4.6 (CTO-Hands) |
