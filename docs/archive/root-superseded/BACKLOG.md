# Volaura Product Backlog

> Groomed by 6-persona team. Format: User Story + T-shirt size + Business Value.
> Sizes: S (0.5d) | M (1d) | L (2-3d) | XL (5d+)
> Priority: P0 (this sprint) | P1 (next sprint) | P2 (backlog) | P3 (someday)

## P0 — Sprint 3 (2026-03-24 → 2026-03-31)

| ID | Story | Size | Value | Persona |
|----|-------|------|-------|---------|
| S3-01 | As Yusif, I need backend deployed on Railway so I can demo to Pasha Bank | M | Critical | Yusif |
| S3-02 | As Yusif, I need Vercel env vars so frontend connects to real API | S | Critical | Yusif |
| S3-03 | As Leyla, I need to take an assessment on my phone via real URL | L | Critical | Leyla |
| S3-04 | As Nigar, I need an organizations router so I can manage volunteers | L | High | Nigar |
| S3-05 | As Attacker, I need a Privacy Policy before any paying customer | M | Blocker | Attacker |
| S3-06 | As Scaling Eng, I need pgvector HNSW index before data grows | S | Medium | Scaling |
| S3-07 | As QA, I need LLM mock so tests don't call real API | M | High | QA |
| S3-08 | As Yusif, I need Pasha Bank pitch deck with live demo | L | Critical | Yusif |

## P1 — Sprint 4

| ID | Story | Size | Value | Persona |
|----|-------|------|-------|---------|
| S4-01 | As Nigar, I need bulk CSV volunteer invite (50+ at once) | M | High | Nigar |
| S4-02 | As Nigar, I need to assign assessments to specific volunteers | L | High | Nigar |
| S4-03 | As Nigar, I need to export results to PDF/Excel | M | Medium | Nigar |
| S4-04 | As Leyla, I need post-assessment results page (badge, rank, next steps) | M | High | Leyla |
| S4-05 | As Attacker, I need full RLS policy audit | M | High | Attacker |
| S4-06 | As Scaling Eng, I need request timing logs on all endpoints | S | Medium | Scaling |
| S4-07 | As QA, I need IRT engine unit tests with known input/output pairs | M | High | QA |
| S4-08 | As Yusif, I need first 10 beta testers onboarded | L | Critical | Yusif |

## P2 — Sprint 5-6

| ID | Story | Size | Value | Persona |
|----|-------|------|-------|---------|
| S5-01 | As Leyla, I need offline assessment progress save (PWA) | L | Medium | Leyla |
| S5-02 | As Leyla, I need push notifications when org views my profile | M | Medium | Leyla |
| S5-03 | As Nigar, I need API/webhook for HR system integration (1C/SAP) | XL | High | Nigar |
| S5-04 | As Scaling Eng, I need run_in_executor for CPU-bound IRT | M | Medium | Scaling |
| S5-05 | As Scaling Eng, I need frontend bundle analysis + optimization | M | Medium | Scaling |
| S5-06 | As Scaling Eng, I need cost-per-assessment documented | S | High | Scaling |
| S5-07 | As QA, I need test coverage reporting (target: 80% critical paths) | M | Medium | QA |

## P3 — Future

| ID | Story | Size | Value | Persona |
|----|-------|------|-------|---------|
| F-01 | As Leyla, I need organization discovery page (who's hiring, events) | L | High | Leyla |
| F-02 | As Attacker, I need automated security scanning in CI (Bandit + ESLint) | M | Medium | Attacker |
| F-03 | As Yusif, I need LinkedIn content automation from sprint output | L | Medium | Yusif |
| F-04 | As Yusif, I need grant application research (GIZ/UNDP/GITA) | M | High | Yusif |
| F-05 | As Leyla, I need AZ strings reviewed by native speaker | M | High | Leyla |

## Definition of Done

Every task is "done" when:
- [ ] Code written and working
- [ ] Unit test exists for new code
- [ ] Existing tests still pass (CI green)
- [ ] AZ locale tested (not just EN)
- [ ] Mobile tested (for UI changes)
- [ ] Security checklist passed (for auth/data changes)
- [ ] Decision logged in DECISIONS.md (for architecture changes)
