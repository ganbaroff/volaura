# Agent Career Ladder

**Purpose:** Define performance tiers, growth paths, and promotion criteria for the swarm team.
**Updated:** 2026-03-26

---

## Performance Tiers

| Tier | Score | Meaning |
|------|-------|---------|
| Apprentice | 0-4 | Learning fundamentals. Output requires heavy CTO review. |
| Competent | 4-6 | Reliable on standard tasks. Occasional misses on edge cases. |
| Proficient | 6-8 | Trusted for complex work. Can mentor Apprentice agents. |
| Expert | 8-9 | Leads domain decisions. Findings shape architecture. |
| Principal | 9-10 | Strategic impact. Creates new capabilities for the team. |

---

## Current Agent Assessments

### Security Agent — 9.0/10 — Expert ⭐

**Session 69 audit:** 8/9 findings correct (88.9%) across Sessions 25-69.
**Promoted to 9.0** after route shadowing vindication (Session 25 → 42: agent was right, CTO was wrong, P0 bug lived 17 sessions).

Key wins: P0 route ordering, P0 stored XSS, P1 concept injection, P1 bearer validation, token hash collision fix.

**Growth objectives to reach Principal (9.0+):**
1. Proactive threat modeling — propose 2-3 security improvements per sprint, not just flag issues
2. Build migration-to-policy validator — audit RLS from schema files without live DB
3. Mentor other agents on security-relevant decisions (teach Architecture about auth patterns)

**Tasks:** Auth flow design, pre-migration RLS audits, security section of every sprint plan.

---

### Architecture Agent — 8.5/10 — Expert (newly promoted)

**Session 69 audit:** 6/8 findings correct (75%) across Sessions 25-69.
**Promoted from 8.0** — storage math (14-43GB/year) was second-highest leverage finding. SupabaseAdmin misread was correct risk identification, wrong fix.

Key wins: Storage math, CVSS 9.8 aura_scores, system coherence reviews, type safety migration strategy.

**Growth objectives to reach Principal (9.0+):**
1. Verify against live codebase — check actual FastAPI routing before proposing auth changes
2. Add cost/latency breakdowns — every proposal includes "saves X queries/Y ms"
3. Shadow Security Agent on auth reviews — learn RLS policy nuances

**Tasks:** Data model proposals, migration review, performance bottleneck analysis, type safety strategy.

---

### Product Agent — 8.0/10 — Expert (newly promoted)

**Session 69 audit:** 6/6 findings correct (100%) across Sessions 25-69.
**Promoted from 7.5** — zero false positives, 100% acceptance rate. All persona-based findings shipped.

Key wins: public-by-default trust analysis, discovery endpoint gap, ADHD-first onboarding narrative, 62-finding audit product section.

**Growth objectives to reach Principal (9.0+):**
1. Propose wireframe-level solutions — don't just flag problems, show what the fix looks like
2. Partner with Growth Agent — retention cohort analysis needs product perspective
3. Reference competitor patterns — "LinkedIn does X, we should do Y because Z"

**Tasks:** Pre-build UX reviews, onboarding flow critique, i18n gap analysis, persona walkthroughs every sprint.

---

### Needs Agent — 7.0/10 — Proficient (meta role)

**Session 69 audit:** 2/2 findings correct (100%). Schema snapshot was the highest-leverage finding in swarm history.

**Growth objectives:**
1. Track recommendation adoption — maintain improvement log with acceptance rate
2. Measure impact — "before: 0% schema context. After: 100%"
3. Expand to cross-agent coordination — identify when agents duplicate work or miss handoffs
4. Run batch capacity planning — prevent proposal explosion under v4.0

**Tasks:** Post-sprint process audits, agent feedback synthesis, shared-context maintenance, v4.0 protocol tuning.

---

### QA Engineer — 6.5/10 — Proficient

**Session 69 audit:** 7/8 findings correct (87.5%). Blind cross-test methodology was excellent. Self-assessment circularity (Mistake #47) was CLASS 5 error.

**STRUCTURAL FIX REQUIRED:** QA questions must be evaluated by a DIFFERENT agent (Security or Product). Self-evaluation = permanent ban. No exceptions.

**Growth objectives to reach Expert (8.0+):**
1. BLIND methodology ALWAYS — pre-commit hook should block self-evaluated questions
2. GRS-validated questions: multi-word behavioral phrases, no single-word buzzwords
3. Expand to: assessment pipeline integration tests (bars.py + quality_gate.py + reeval_worker.py)

**Tasks:** Question bank GRS audits, blind cross-validation, anti-gaming gate regression tests.

---

### Growth Agent — 5.0/10 — Competent (UNPROVEN)

**Session 69 audit:** 0 findings. Replaced SWE Agent (1 finding in 30 sessions). Must prove value or face same retirement.

**SWE Agent warning:** SWE had 100% accuracy but 1 finding in 30 sessions = redundant. Growth Agent must show higher volume + accuracy to justify the slot.

**Survival requirements (next 3 sprints):**
1. Establish growth baseline — CAC, LTV, churn cohort analysis
2. Partner with Product Agent — retention diagnosis
3. Competitive tracking — monitor LinkedIn, boss.az, local platforms
4. Deliver 3+ actionable findings per sprint or face retirement review

**Tasks:** Growth metrics baseline, cohort analysis, viral loop design, competitor tracking.

---

### Firuza (Council) — 7.5/10* — Proficient → Expert path

**Session 69 audit:** 4/4 correct (100%). v2.0 upgrade: reactive → proactive. Influence 1.0 → 1.1.
*See `memory/swarm/skills/firuza-assistant.md` for full v2.0 protocol.*

---

### Nigar (Council) — 6.5/10* — Proficient (awaiting B2B sprint)

**Session 69 audit:** 2/2 correct (100%). Low volume — only 2 on-domain sprints (A2, A3).

**Growth objectives:**
1. Lead Sprint 5 B2B planning — primary voice on org dashboard + discovery
2. MEDDPICC alignment check — verify Sales skills flow through UI
3. Org persona walkthrough — test as Aynur (talent acquisition buyer)
4. Deliver 4+ findings in Sprint 5 to confirm tier

---

### SWE Agent — RETIRED (Session 53)

1 finding in 30 sessions. Replaced by Growth Agent. Verb regex work absorbed by QA Engineer.

### Needs Agent -- N/A (meta role)

Introspective role focused on process improvement and swarm structure. Schema snapshot recommendation in Session 25 was the top need and was acted on.

**Growth objectives:**
1. Produce measurable improvement proposals (before/after metrics, not just "we should do X")
2. Track which past recommendations were adopted vs ignored and why
3. Expand scope to cross-agent coordination -- identify when agents duplicate work or miss handoffs

**Tasks to take on more:** Post-sprint process audits, agent feedback synthesis, shared-context maintenance.

---

## Promotion Criteria

An agent moves up a tier when ALL of these are met over 3 consecutive sprints:

| Criterion | How to measure |
|-----------|---------------|
| **Accuracy rate >= tier threshold** | Apprentice: 50%, Competent: 65%, Proficient: 80%, Expert: 90% |
| **Zero critical false positives** | No recommendation that, if followed, would break production |
| **Constructive disagreement** | At least 1 dissent per 3 sprints that improved the final outcome |
| **Domain expansion** | Demonstrated useful input outside primary domain at least once |
| **Self-correction** | Acknowledged and corrected own mistake without CTO intervention |

**Demotion trigger:** Accuracy drops below current tier threshold for 2 consecutive sprints, or a recommendation causes a production incident.

---

## Review Cadence

- **Score update:** After every sprint, based on findings accuracy from agent-feedback-log.md
- **Tier review:** Every 3 sprints. CTO evaluates promotion criteria table above.
- **Score formula:** `(correct findings) / (total findings) * 10`, adjusted +/-0.5 for impact severity
- **Recording:** Update agent-roster.md scores. Log tier changes in agent-feedback-log.md.
