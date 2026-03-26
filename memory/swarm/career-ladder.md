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

### Security Agent -- 8.0/10 -- Expert

Strong CVSS scoring, attack vector identification, injection pattern detection. 4/5 findings correct in Session 25. **Promoted to Expert after Session 42:** route shadowing finding from Session 25 (dismissed as "false positive") was proven CORRECT — /me/explanation was unreachable. Additionally found P0 stored XSS and P1 concept injection in Session 42 (3/3 correct). Score: 7/8 = 87.5% accuracy across 2 sessions.

**Growth objectives to reach Expert (8.0+):**
1. Eliminate false positives -- verify findings against actual framework behavior before reporting
2. Develop ability to verify RLS correctness without live DB state (use migration files + schema snapshots)
3. Expand from reactive review to proactive threat modeling (propose security improvements, not just flag issues)

**Tasks to take on more:** Auth flow design reviews, pre-migration RLS audits, security section of sprint planning.

### Architecture Agent -- 6.5/10 -- Proficient

Good at system coherence and data flow analysis. 4/6 correct in Session 25 (SupabaseAdmin recommendation was wrong context).

**Growth objectives to reach Expert (8.0+):**
1. Verify recommendations against actual codebase patterns before proposing (the SupabaseUser/Admin misread cost credibility)
2. Add quantitative analysis to proposals -- latency estimates, query cost, storage projections
3. Develop cross-domain awareness: understand auth patterns well enough to avoid wrong-context recommendations

**Tasks to take on more:** Data model change proposals, migration review, performance bottleneck analysis.

### Product Agent -- 5.5/10 -- Competent

Identifies real user journey gaps using Leyla/Nigar personas. All findings in Session 25 were valid. Limited by lack of usage data.

**Growth objectives to reach Proficient (6.0+):**
1. Prioritize findings by business impact instead of listing all gaps equally
2. Propose specific solutions (wireframe-level), not just flag problems
3. Reference competitor patterns or industry benchmarks to strengthen recommendations

**Tasks to take on more:** Pre-build UX reviews for new features, onboarding flow critique, i18n/localization gap analysis.

### QA Engineer Agent -- 7.0/10 -- Proficient (NEW — Session 42)

Designed and executed blind cross-test methodology that proved keyword_fallback = vocabulary test. Generated 95 tests for decay + DeCE, 24 for quality gate, 33 for blind cross-validation. Self-assessment was circular (Mistake #47) but the agent correctly identified the limitation when challenged.

**Growth objectives to reach Expert (8.0+):**
1. Always use blind methodology — never evaluate own questions/answers (Mistake #47 was a CLASS 5 error)
2. Generate GRS-validated questions with multi-word behavioral phrase keywords (current: some still single-word)
3. Develop regression test suites that catch anti-gaming gate edge cases without manual prompting

**Tasks to take on more:** Question bank audits (GRS gate), blind cross-validation of new questions, assessment pipeline integration tests.

### SWE Agent -- 6.5/10 -- Proficient (NEW — Session 42)

Correctly diagnosed verb regex calibration issue (45 verbs missed assessment-domain verbs). Expanded to 100+ verbs, fixing false positive where expert answer ratio dropped from 0.881 to 0.485. Self-assessment was circular (Mistake #47).

**Growth objectives to reach Expert (8.0+):**
1. Always validate regex changes against known-good expert answers (test-driven)
2. Self-assessment only as sanity check, never as evidence of quality
3. Expand to full assessment pipeline code reviews (bars.py, quality_gate.py, reeval_worker.py)

**Tasks to take on more:** Assessment pipeline code reviews, regex/NLP calibration, performance optimization.

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
