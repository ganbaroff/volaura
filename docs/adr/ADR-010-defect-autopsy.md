# ADR-010: Defect Autopsy — Top 3 Root Causes → 3-Item Enforced DoD

**Date:** 2026-04-03
**Status:** Accepted
**Context:** 61 fix commits out of 218 total = 28% Change Failure Rate (DORA Elite target: <15%).
**Prescription from:** Swarm retrospective (Groq Llama-3.3-70b, BATCH-V critique)

---

## The Problem

Previous quality sessions built elaborate DoD checklists (15 items) without knowing what actually caused the defects. This ADR categorizes all 61 fix commits to find the real root causes, then derives 3 enforceable DoD items from evidence — not from theory.

---

## Defect Autopsy: 61 Fix Commits Categorized

### Category 1: Security Vulnerabilities (12 commits — 20%)

**Commits:**
- `d1649e8` fix(security): OWASP audit — 3 CRITICAL + 3 MEDIUM fixed
- `30dc264` fix(security): OWASP HIGH findings — rate limits, audit logging, ownership checks
- `b0d9d26` fix(security): OWASP MEDIUM + LOW batch — 6 more findings fixed
- `7e8acd1` fix(security): TOCTOU crystal race + missing rate limit on /my/registrations
- `7a387fc` fix(security): UUID validation + crystal ledger column mismatch
- `ab60784` fix(security): resolve 2 CRITICAL blockers from swarm council review
- `ffe8696` fix(security): HIGH-01 race condition via optimistic locking
- `c3b6aa0` fix(security): resolve HIGH-02 and HIGH-03 vulnerabilities
- `63175cc` fix(security): resolve all 3 CRITICAL vulnerabilities from audit
- `03aeb2a` fix(security): patch 4 vulnerabilities found in agent review
- `73437d4` fix(security): purge all next@14.2.29 references from lockfile
- `4eeadf6` fix(security): upgrade next.js 14.2.29 → 14.2.35

**Root cause:** Security review ran AFTER shipping. None of these endpoints/tables had a security check during design or implementation. The endpoint was built, shipped, then a security audit found the problem.

**What AC would have prevented:** Every one of these. If AC included "rate limit present?" + "ownership check?" + "RLS policy?" the fixes would have been caught before writing a line of code.

---

### Category 2: Deploy/Infrastructure Failures (10 commits — 16%)

**Commits:**
- `d0359aa` fix(vercel): use pnpm --filter for monorepo build
- `a549fd8` fix(vercel): correct build config
- `f5f0da0` fix(vercel): set rootDirectory to apps/web
- `9b8fd97` fix(ci): remove duplicate pnpm version
- `5079f60` fix(vercel): fix trailing comma in vercel.json
- `48e551a` fix(vercel): remove secret refs from vercel.json
- `b9cdcbb` fix(deploy): unblock Vercel builds
- `14a12d7` fix(production): Sentry configured + all API keys deployed
- `7b59c36` fix(production): error alerting + false positives resolved
- `6d97ea5` fix(production): 3 critical launch blockers + readiness checklist

**Root cause:** Code was written locally, committed, then discovered to not work in the actual deployment environment. Staging was never tested before production.

**What AC would have prevented:** "Feature deployed to staging and verified" as a DoD item would have caught every infrastructure mismatch before it touched production.

---

### Category 3: API Schema/Field Name Mismatches (9 commits — 15%)

**Commits:**
- `5630c17` fix(api): align AuraScoreResponse fields (total_score not overall_score)
- `d10c0cd` fix(api): use maybe_single() in aura endpoints
- `ab316de` fix(api): catch SupabaseUser client errors
- `f96f425` fix(api): response_model on auth endpoints + rate limit skills list
- `da46d2a` fix(cors): expose X-Request-ID response header
- `19502fe` fix(perf+correctness): stats O(users), skills JSONB table mismatch
- `1584b77` fix(db): upsert_aura_score now merges competency_scores instead of overwriting
- `19db2b7` fix(schema): sync openapi.json + generated types
- `f802cbe` fix(s-05): pnpm generate:api - sync TypeScript SDK

**Root cause:** Field names, DB column names, and API schemas assumed rather than verified. Code shipped with `overall_score` when the DB column was `total_score`. Frontend SDK not regenerated after backend schema changes.

**What AC would have prevented:** "Run generate:api and verify schema matches DB" as a DoD item. Combined with TypeScript strict mode — many of these would have been compile errors.

---

### Remaining Categories (30 commits — 49%)

| Category | Count | Examples |
|---|---|---|
| Multi-bug batches (post-ship audits) | 10 | fix(bugs) × 3, fix(audit-p1-p2) |
| Assessment domain bugs | 5 | fix(assessment) × 4, fix(aura) |
| Frontend/UI bugs | 5 | fix(frontend), fix(web), hydration errors |
| Auth/profile bugs | 4 | fix(auth), fix(profiles) |
| Swarm/memory bugs | 4 | fix(swarm), fix(context) |
| Test/CI fixes | 2 | fix(tests), fix(ci) |

---

## Decision: 3-Item Enforced DoD (replaces 15-item checklist)

Based on the autopsy, 3 categories account for 51% of all defects (31/61). These become the mandatory DoD items, enforced by pre-commit hook and/or agent gate — not willpower.

### DoD Item 1: Security pre-check (catches 20%)

**Gate:** Before ANY task touching API endpoints, DB tables, or edge functions:
```
□ Every new endpoint has rate limiting (slowapi or Supabase RLS-level)
□ Every endpoint that returns user data has ownership check (eq("user_id", current_user_id))
□ Every new Supabase table has RLS policy in migration file
□ Input validated via Pydantic model (not raw dict access)
```
**Enforcement:** SEC agent mandatory for L2+ tasks. Takes 2 min. Cannot self-certify.

### DoD Item 2: Staging deployment verified (catches 16%)

**Gate:** Before marking any task DONE:
```
□ Feature deployed to Railway staging or local Docker (not "works on my machine")
□ At least 1 manual test of the happy path in staging environment
□ No new Vercel/Railway build warnings
```
**Enforcement:** QA agent checks for "tested in staging" evidence. If missing → task stays in_progress.

### DoD Item 3: Schema sync verified (catches 15%)

**Gate:** For any task touching API responses or DB schema:
```
□ pnpm generate:api run and no new TypeScript errors
□ DB column names match Pydantic model field names (grep check)
□ openapi.json committed alongside schema changes
```
**Enforcement:** Pre-commit hook checks that if `schemas/*.py` changed, `openapi.json` was also updated.

---

## Expected Impact

If these 3 items had been enforced from day 1:
- 31 of 61 fix commits would have been prevented = CFR drops from 28% → ~13% (Elite threshold)
- Combined with the existing tsc -b gate (type errors caught at commit): CFR likely ~10%
- Time saved: 31 fix commits × ~45 min average = ~23 hours of rework eliminated

---

## Rejected Alternatives

**15-item DoD:** Rejected — proven to achieve 0% compliance under pressure. More items = lower compliance. Three items at 100% beats fifteen items at 0%.

**Automated SAST only:** Insufficient — SAST catches code patterns, not architectural decisions (missing ownership checks, wrong field names, no RLS policy).

**Post-ship audit:** Root cause of 51% of defects. Eliminated by shift-left: verify before shipping, not after.

---

## Implementation

- [ ] Pre-commit hook for DoD Item 3 (schema sync check) — BATCH-W
- [ ] SEC agent mandatory routing for any API task — TASK-PROTOCOL update — BATCH-W
- [ ] Staging deployment evidence required in QA agent verdict — already in quality-assurance-agent.md

**Reviewed by:** Groq Llama-3.3-70b (swarm critique, BATCH-V), NVIDIA NIM (swarm critique, BATCH-V)
