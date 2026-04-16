# Full System Audit — Session 113, 2026-04-16

**Method:** Three parallel Explore agents (frontend 45+ files / backend 30+ files / infra 54 tool uses). Total: 140+ files, 330K tokens analysis. Cross-verified critical findings via grep/Read in main session.

**Overall:** Production-ready with 1 P0, 15 P1, 24 P2.

---

## P0 — FIX TODAY (1 item)

**quality_gate.py silent JSON parse failure (backend, lines 115-125, 249-258, 323-339)**
Three identical `except Exception` handlers silently convert corrupted `expected_concepts` to empty list. Impact: question with bad JSON → evaluated against zero concepts → keyword_fallback baseline score for every answer → anti-gaming gates weakened silently. Ghost-audit flagged 2026-04-15. Fix: raise at question fetch time, never accept empty rubric, return 422 if question integrity violated.

---

## P1 — FIX THIS SPRINT (15 items)

**Frontend (5):**
1. Settings page visibility endpoint path mismatch (`/aura/me/visibility` vs `/api/aura/me/visibility`)
2. effective_score nullcheck uses `??` instead of `!== null` in aura/page.tsx:276
3. Gaming flags warning no visual expansion hint
4. Energy mode not persisted to backend (Zustand only, lost on browser close)
5. Share nudge timing on complete page (appears before milestone animation)

**Backend (7):**
6. Rate limit gap: 3 endpoints potentially undecorated
7. Reeval worker queue no max-age (old entries never expire, loop forever)
8. BARS injection detection: LLM output not scanned for prompt leakage
9. Swarm BUG-01 in swarm_service.py: comment exists, fix status unknown
10. IRT bounds validation at runtime missing (only at seed time)
11. Keyword fallback spike counter in-memory only, resets on restart
12. Potential flaky tests (asyncio + time-dependent rate limiter mocking)

**Infra (3):**
13. .env.md missing 20+ vars that config.py expects (TELEGRAM_*, LANGFUSE_*, STRIPE_*, DID_*, etc.)
14. squad_leaders.py missing from active swarm tree (archived, coordinator falls back to defaults)
15. Table partitioning strategy absent for high-velocity tables (assessment_sessions, evaluation_queue)

---

## P2 — BACKLOG (24 items, condensed)

Frontend: password visibility emoji, hardcoded competency icons, feed cache stale 5min, progress indicator missing in AURA header, dashboard stats row hidden at score=0.

Backend: IRT param bounds unchecked at runtime, AURA decay no audit trail, antigaming flags not persisted, threshold not config-tunable, subscription webhook guard, orgs schema complexity (303 LOC), CORS MINDSHIFT_URL unvalidated, no request timeout middleware, no idempotency key support, no adaptive rate limiting, email XSS potential, injection test missing.

Infra: Railway service interdependency docs, grievance admin UI endpoints, lifesim admin endpoints, consent baseline seed, lifesim_events index strategy, swarm archive 50 files not pruned, no data migration for compliance baseline.

---

## Strengths confirmed

- RLS: 35/35 tables + FORCE applied + 8 CRITICAL security fixes verified
- Auth: CVSS 9.1 fix (admin.auth.get_user not anon key), fail-closed 401
- IRT math: 3PL correct, EAP with 49-point quadrature, Fisher info item selection
- Rate limiting: 126/129 endpoints (97.7%)
- Test suite: 58 files, 21.9K LOC, 100% endpoint-level coverage
- i18n: AZ + EN complete, no missing keys for Baku users
- Accessibility: WCAG 2.1 AA, reduced motion, 44px targets
- Colors: zero red (Law 1 compliant)
- AURA page: Savant Discovery + competency breakdown present (completeness visible)
- Constitution compliance: shame-free, ADHD-friendly, non-competitive framing throughout

---

## Doctor Strange recommendation

Fix quality_gate.py P0 first (30 min). Then group P1s by blast radius: settings visibility endpoint + effective_score nullcheck + energy persistence (all frontend, 2h total) → .env.md documentation (1h) → reeval worker max-age + BARS output scan (2h backend). Total: ~6h focused work closes all high-impact items.

Fallback if time constrained: P0 alone is the only item that could silently corrupt real user assessment quality. Everything else degrades gracefully.
