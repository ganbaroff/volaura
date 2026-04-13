# VOLAURA Quality System
## Toyota TPS + Apple + DORA + Lean Six Sigma → Software Engineering

**Version:** 1.0 — Created 2026-04-03 after NotebookLM research session (6 deep questions, 9 sources)
**Standard:** Toyota Elite = 3.4 defects per million. DORA Elite = CFR <15%. VOLAURA Target = defect rate <10% (from 34.8% baseline).

---

## Why This Document Exists

VOLAURA baseline (as of 2026-04-03):
- Defect rate: **34.8%** (73 mistakes / 210 commits)
- Acceptance Criteria written before coding: **0%**
- Definition of Done verified per batch: **0%**
- DORA metrics tracked: **0%**

Toyota allows 3.4 defects per million operations. Apple ships iOS to 1.8 billion devices with <0.1% critical bugs. This document maps their standards to VOLAURA's FastAPI + Next.js + 40-agent swarm.

---

## Section 1: Toyota TPS → VOLAURA Software Equivalents

### The 5 Core TPS Principles (Software Translation)

#### 1. Jidoka — "Stop the Line" = CI/CD Hard Gates

Toyota: Any worker can stop the assembly line the moment they detect a defect.
VOLAURA: The CI/CD pipeline breaks the build automatically on ANY quality failure.

**Implementation:**
```yaml
# Every PR must pass ALL of these before merge:
- pytest (unit + integration) — 0 failures
- ruff + mypy (FastAPI linting) — 0 errors
- ESLint + TypeScript (Next.js) — 0 errors
- playwright tests — all passing
- SAST scan (bandit for Python, npm audit for JS) — 0 critical/high
- secrets scan (truffleHog / detect-secrets) — 0 exposed keys
```

If any gate fails → build stops. No exceptions. No "we'll fix it in the next commit."

#### 2. Poka-yoke — Mistake-Proofing = Structural Prevention

Toyota: Jigs and fixtures make it physically impossible to assemble a part wrong.
VOLAURA: Code architecture makes it impossible to deploy bad code by accident.

**Implementation:**
- FastAPI: Pydantic models on every request/response — invalid data rejected at boundary
- Next.js: TypeScript strict mode — type errors = build errors
- Supabase: RLS policies — data access impossible without explicit grant
- Pre-commit hooks: `tsc -b` + `ruff check` run before every commit
- Zod validation on all API boundaries in Next.js

#### 3. Kaizen — Continuous Improvement = Sprint Retrospectives + Defect Tracking

Toyota: Workers submit improvement suggestions daily. The factory gets 1% better every day.
VOLAURA: Every batch ends with a SWARM RETROSPECTIVE that updates `quality-metrics.md`.

**Implementation:**
- After EVERY batch: measure defect rate, update `memory/context/quality-metrics.md`
- Monthly: calculate defect trend (improving / stable / regressing)
- Quarterly: review which mistake CLASS occurs most → fix the system, not the symptom
- Langfuse: track LLM call quality per agent, evaluate outputs, iterate prompts

#### 4. Andon — Visual Alerts = Observability Dashboard

Toyota: A colored cord that any worker pulls to signal a quality problem. The whole factory sees it.
VOLAURA: Langfuse traces + DORA dashboard + Sentry errors → visible to CTO at all times.

**Implementation:**
- Sentry: all unhandled exceptions → Telegram alert to CEO (already wired)
- Langfuse: every AI agent call traced, cost/latency per agent visible
- GitHub Actions: DORA metrics logged after every deployment
- Target threshold: Change Failure Rate > 15% → mandatory retrospective before next feature

#### 5. Just-in-Time (JIT) = Definition of Ready

Toyota: Parts arrive exactly when needed — no inventory pile-up, no waiting.
VOLAURA: A task is not started until it is fully ready — no half-baked requirements.

**Definition of Ready (DoR) — a task CANNOT be started unless:**
- [ ] User story written in format: "As a [role], I want [action], so that [benefit]"
- [ ] Acceptance Criteria written in Gherkin: Given/When/Then (min 2 scenarios)
- [ ] INVEST criteria passed (Independent, Negotiable, Valuable, Estimable, Small, Testable)
- [ ] Scope is clear — no ambiguous words ("it should work", "make it better")
- [ ] Dependencies identified (does this block or require another task?)

---

## Section 2: Apple Product Development Standards

### Apple's Quality Principles → VOLAURA

| Apple Practice | VOLAURA Equivalent |
|---|---|
| EPM Gatekeeper (no feature ships without sign-off) | Every AC must be manually verified before marking done |
| Forced iteration cycles (design tested before manufacturing) | Staging deployment + manual verification before production |
| "Rules of the Road" document | Definition of Done 15-item checklist |
| Small teams, deep ownership | Solo CTO owns each module end-to-end |
| No feature creep (Apple removes features, not adds) | Scope is frozen once AC is written — no scope creep during implementation |

### Apple's "Secret": Detailed Acceptance Criteria Before Any Work

Apple's product development process mandates that every feature have an exhaustive spec before a single engineer writes a line of code. The spec defines: what it does, what it does NOT do, how it fails gracefully, and how it will be tested.

**VOLAURA Mandate:** No task enters "in progress" without a written AC document.

---

## Section 3: DORA Elite Metrics

### DORA Elite Thresholds (Target for VOLAURA)

| Metric | Current (Estimated) | Elite Target | How to Measure |
|---|---|---|---|
| Deployment Frequency | ~1-2x/week | On-demand (daily+) | GitHub Actions deploy count |
| Change Lead Time | ~2-4 hours | <1 hour | Commit timestamp → Railway deploy timestamp |
| Change Failure Rate | ~34.8% (defect rate proxy) | <15% | Hotfix commits / total commits |
| Time to Restore Service | Unknown | <1 hour | Incident open → resolved time in Sentry |

### 90-Day DORA Improvement Roadmap

**Days 1-30: Establish Baseline**
- Set up DORA metrics logging in GitHub Actions (timestamp commit → deploy)
- Record baseline CFR from last 30 commits
- Define DoD and DoR (this document)
- Automate all 8 CI gates listed in Jidoka section

**Days 31-60: Optimize Throughput**
- Break tasks into smallest possible deployable units
- Target: no single PR changes more than 200 lines
- Wire Langfuse for LLM agent observability (see Section 5)
- Target: Lead Time < 2 hours

**Days 61-90: Master Stability**
- Automated rollback on deployment health check failure
- Langfuse evaluation scores tracked per agent
- CFR below 20% (from ~35% baseline)
- Full DORA dashboard visible in quality-metrics.md

---

## Section 4: Definition of Done (DoD) — 15-Item Checklist

> This checklist applies to EVERY task, EVERY batch. No exceptions.

### Automated (CI/CD enforces — human cannot override)

- [ ] **1. Linting:** `ruff check` (Python) + ESLint (Next.js) — 0 errors
- [ ] **2. Type safety:** `mypy` (Python) + `tsc -b` (TypeScript) — 0 errors
- [ ] **3. Unit tests:** All pass, ≥80% coverage on new code
- [ ] **4. Integration/E2E tests:** Playwright suite passes (or new tests written for new flows)
- [ ] **5. Build success:** `vite build` (frontend) + `pip install -r requirements.txt` (backend) — clean
- [ ] **6. API docs:** FastAPI Swagger auto-generated schemas valid
- [ ] **7. SAST scan:** `bandit` (Python) + `npm audit` — 0 critical/high vulnerabilities
- [ ] **8. Secrets scan:** No API keys, tokens, or credentials in any committed file
- [ ] **9. Accessibility:** Lighthouse a11y score ≥ 90 for any new UI components
- [ ] **10. DORA logging:** Deployment timestamp recorded, CFR updated in quality-metrics.md

### Human Verification Required

- [ ] **11. Acceptance Criteria met:** Every AC scenario from the task brief manually verified
- [ ] **12. Peer review:** Code reviewed (CTO reviews own AI-generated code critically)
- [ ] **13. Staging deployment:** Feature deployed to staging and tested end-to-end
- [ ] **14. Observability:** New endpoints/AI calls have Langfuse traces or Sentry monitoring
- [ ] **15. User documentation:** If user-facing, release notes / changelog updated

---

## Section 5: Langfuse Integration Plan

### What Langfuse Gives Us (vs. Current Logging)

Current state: `logger.info("mochi-respond called")` — invisible cost, invisible failures.

Langfuse gives:
- **Traces:** Visual graph of every AI agent call chain (which agent called what, in what order)
- **Generations:** Exact tokens in/out, cost per call, latency per model
- **Evaluations:** Automated LLM-as-judge quality scoring on AI outputs
- **Prompt Management:** Version-controlled prompts, A/B test prompt variants without code deploys
- **Datasets:** Run evaluation against 50 test cases before deploying new prompts

### Integration Path (LiteLLM Proxy — Recommended)

```python
# Instead of calling Gemini/Groq directly:
import litellm
litellm.success_callback = ["langfuse"]
litellm.failure_callback = ["langfuse"]

# All existing calls automatically traced — zero refactor needed
response = litellm.completion(
    model="gemini/gemini-2.0-flash",
    messages=[{"role": "user", "content": prompt}],
    metadata={"langfuse_user_id": user_id, "langfuse_session_id": session_id}
)
```

### Metrics to Monitor for 40-Agent Swarm

| Metric | Threshold | Action |
|---|---|---|
| Cost per agent call | > $0.05 | Review prompt efficiency |
| Latency p95 | > 8 seconds | Add fallback or cache |
| LLM-as-judge score | < 7/10 | Pause agent, fix prompt |
| User feedback thumbs-down | > 20% | Immediate prompt review |
| Daily token spend | > $10 | Alert CEO via Telegram |

### Self-Host vs Cloud

**Recommendation: Start with Langfuse Cloud (free tier, 50k events/month)**
Self-host requires: Docker + PostgreSQL + ClickHouse + Redis. Too heavy for launch phase.
Migrate to self-host when: >50k monthly AI calls OR data privacy compliance required.

---

## Section 6: CrewAI Architecture Plan

### Current State vs Target State

**Current:** 40 agents as separate markdown files, manually invoked one-at-a-time by CTO prompting Claude.

**Target:** CrewAI Flows orchestrating specialized Crews, triggered by events (PR opened, assessment completed, CEO Telegram command).

### Recommended Crew Structure

```
Flow: VOLAURA Development Pipeline
  └── Crew: Sprint Planning (3 agents)
        ├── Product Owner Agent — writes AC in Gherkin
        ├── Architecture Agent — reviews technical feasibility
        └── Risk Agent — identifies blockers and dependencies

  └── Crew: Quality Assurance (4 agents)
        ├── AC Writer Agent — writes Gherkin scenarios before coding
        ├── Code Reviewer Agent — reviews against DoD checklist
        ├── DoD Verifier Agent — checks all 15 items before marking done
        └── DORA Tracker Agent — logs metrics after each deployment

  └── Crew: Swarm Retrospective (3 agents)
        ├── Groq Agent (Llama-3.3-70b) — first critique
        ├── NVIDIA NIM Agent (Nemotron-Ultra) — second critique
        └── Synthesis Agent — merges critiques → lessons learned
```

### When to Implement CrewAI

**Not yet** — single founder, pre-launch. Manual agent invocation via Claude is sufficient.
**Trigger:** When swarm retrospectives take >30 minutes manually OR when >5 parallel agents needed.
**Estimated effort:** 2-3 days to migrate 40 agents to CrewAI Flows structure.

---

## Section 7: Missing Infrastructure (Priority-Ordered)

### Priority 1 — Critical (implement before first 100 users)

| Item | Why | Effort |
|---|---|---|
| Langfuse integration via LiteLLM | AI cost visibility, quality tracking | 2 hours |
| DoR gate in TASK-PROTOCOL | Prevents starting tasks without AC | 30 min |
| DORA metrics logging in GitHub Actions | Baseline measurement | 1 hour |
| quality-metrics.md per-batch tracking | Kaizen without measurement = guessing | 30 min |

### Priority 2 — Important (implement before 1,000 users)

| Item | Why | Effort |
|---|---|---|
| Automated rollback on Railway | MTTR < 1 hour target | 2 hours |
| LLM-as-judge CI gate via Langfuse | Automated quality gate on AI outputs | 3 hours |
| Per-agent cost budget alerts | Prevent cost spiral | 1 hour |

### Priority 3 — Post-Launch

| Item | Why | Effort |
|---|---|---|
| CrewAI migration | Structured parallel execution | 2-3 days |
| Langfuse self-host | Data privacy / cost at scale | 1 day |
| Requirement traceability matrix | CEO request → delivery tracking | 4 hours |

---

## Section 8: Missing Agent Skills (to create)

Based on research findings, these agents are missing from `memory/swarm/skills/`:

| Agent | Purpose | Priority |
|---|---|---|
| `acceptance-criteria-agent.md` | Writes Gherkin AC BEFORE any coding starts | P1 |
| `quality-assurance-agent.md` | Verifies DoD 15-item checklist before marking done | P1 |
| `dora-metrics-agent.md` | Calculates and tracks DORA metrics per batch | P1 |
| `velocity-tracker-agent.md` | Historical velocity, delivery estimates | P2 |
| `requirement-traceability-agent.md` | Maps CEO request → AC → delivered feature | P2 |

---

*Research sources: Toyota TPS (Learn Lean Sigma), Apple Product Development (IxDF), DORA metrics (dora.dev), Six Sigma (Ineak), Definition of Done (Atlassian), CrewAI docs, Langfuse docs, INVEST criteria (Agile Alliance)*
*NotebookLM notebook: 888d43e4-5d5b-40fb-9312-ff7824a610a7*
