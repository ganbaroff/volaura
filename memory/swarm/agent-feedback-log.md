# Agent Feedback Log

**Purpose:** Agents read this at task start to learn what proposals worked, what was rejected, and why.
**Updated by:** CTO after each sprint review.

---

## Format
```
| Session | Agent | Proposal | Status | Outcome | Note |
```

**Status:** `implemented` | `rejected` | `deferred` | `partial` | `revising`

---

## Log

| Session | Agent | Proposal ID | Short Title | Status | Outcome | Note |
|---------|-------|-------------|-------------|--------|---------|------|
| 23 | swarm | 00b8e290 | E2E testing framework | deferred | Added to Sprint 10 backlog | Good proposal, wrong timing — ship trust arch first |
| 23 | swarm | — | API gateway | rejected | Not needed at current scale | Proposed when monolith handles load fine |
| 23 | swarm | — | Redis rate limiting | deferred | Revisit when 2+ Railway instances | In-memory slowapi sufficient for now |
| 25 | arch-agent | CRIT-01 | SupabaseAdmin bypass in get_aura_by_id | partial | NOT fixed — kept Admin intentionally for public profiles, but added rate limiting + enumeration fix | Agent was right about enumeration risk, wrong about Admin→User fix |
| 25 | security-agent | CRIT-04 | AURA_HIDDEN vs AURA_NOT_FOUND leak | implemented | Fixed — identical 404 for both cases | Correct call, fixed same session |
| 25 | security-agent | CRIT-05 | model_used leakage | implemented | Fixed — mapped to evaluation_confidence (high/pattern_matched/unknown) | Correct call, fixed same session |
| 25 | security-agent | HIGH-05 | org_id not validated before upsert | implemented | Fixed — added org existence check in /me/sharing | Correct call, fixed same session |
| 25 | security-agent | HIGH-01 | Route shadowing /me vs /{volunteer_id} | acknowledged | FastAPI resolves correctly (static routes before parameterized) — no fix needed | Agent identified real pattern risk but FastAPI handles it |
| 25 | product-agent | GAP-01 | Public-by-default = trust trap | open | Need onboarding modal on first score reveal | Good insight — Phase 3 work |
| 25 | product-agent | GAP-02 | No discovery endpoint for orgs | open | Added to Phase 3 plan | Critical for org value prop |
| 25 | product-agent | GAP-03 | keyword_fallback label kills trust | implemented | Fixed via evaluation_confidence labels | Covered by security fix above |
| 25 | arch-agent | MAJOR-05 | Swarm path missing evaluation_log | open | BUG-01 in shared-context.md | Will fix when swarm_enabled=True in production |
| 25 | arch-agent | MAJOR-06 | Storage math: 14-43GB/year at 3K users | acknowledged | Archive strategy needed before 500 users | Better estimate than original 4.5GB |
| 25 | needs-agent | TOP | Schema snapshot in every task prompt | implemented | Created shared-context.md with DB schema | Highest leverage improvement |
| 25 | needs-agent | — | Shared context file pre-run | implemented | Created this file (shared-context.md) | Done |
| 25 | needs-agent | — | Feedback loop (this file) | implemented | Created agent-feedback-log.md | Done |

---

## Rejected Patterns (learn from these)

These types of proposals waste time. Avoid repeating:

1. **API gateway / microservices** — rejected every time. Monolith works. Bring data (requests/sec, latency) if proposing this.
2. **Redis** — not needed until 2+ Railway instances. Stop proposing.
3. **ORM (SQLAlchemy, Prisma)** — Supabase SDK only. Non-negotiable.
4. **Privacy by default (hidden scores)** — CEO reviewed and chose public by default. Don't re-litigate.
5. **OpenAI as primary LLM** — Gemini is primary. OpenAI is fallback. This is cost decision.

---

## High-Value Proposal Patterns (do more of these)

1. **Specific security vulnerabilities with CVSS score** — always gets attention
2. **Storage/cost math** — CTO missed the 14-43GB/year calculation; agent caught it
3. **User journey gaps** — Leyla/Nigar persona reviews catch what code reviews miss
4. **Concrete file paths** — "fix line 39 in aura.py" > "fix the auth issue"
5. **Calibrated estimates** — "3 hours, not 3 days" with specific breakdown

---

## Notes for Next Review Cycle

- BUG-01 (swarm evaluation_log) needs agent proposal with specific code change
- Phase 3 scope needs product-agent input on discovery endpoint design
- Architecture agent should review team_leads.py wiring when it's planned (BUG-04)
