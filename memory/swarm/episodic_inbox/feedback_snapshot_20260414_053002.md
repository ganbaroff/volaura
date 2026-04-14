# Episodic Snapshot — 20260414_053002

Auto-saved by memory_consolidation.py before pruning.

---

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
| 48 | DSP-ScalingEngineer | B3-001 | D-ID video provider | rejected | D-ID Lite $5.90/mo = 20 vid/mo cap. Not scalable. CEO rejected: "серьёзно?" | Swarm correctly identified unit economics problem |
| 48 | DSP-Attacker | B3-002 | fal.ai R2 egress uncompressed | deferred | H.264 480p compression before R2 upload — to implement in video worker | Valid risk, not yet implemented |
| 48 | DSP-CTO | B3-003 | Modal GPU self-hosted | rejected | 29/50 — Docker environment hell for solo founder. Not the time. | Correct rejection |
| 48 | DSP-Hybrid | B3-004 | ZEUS + fal.ai MuseTalk | implemented (corrected) | Won 40/50 after correction: MuseTalk→SadTalker (portrait input), PlayAI→Kokoro (deprecated) | Final: fal.ai SadTalker + Kokoro |
| 49 | E2E-test | B3-005 | fal-ai/playai/tts wrong | fixed | Model deprecated. Switched to fal-ai/kokoro/american-english ($0.02/1k chars) | Only found during E2E — pre-validate next time |
| 49 | E2E-test | B3-006 | fal-ai/musetalk wrong input | fixed | MuseTalk needs MP4 video not portrait. Switched to fal-ai/sadtalker (source_image_url) | Only found during E2E — pre-validate next time |
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
| 25 | cleanup-agent | — | Delete 4 gitignored temp files | implemented | _tmp_* + decision-simulation-review.html + volaura-preview.jsx deleted | Agent correctly found only gitignored artifacts, no core files touched |
| 25 | cleanup-agent | — | README stubs for assessment/ + skills/ | implemented | 2 README stubs created | Good coverage — found real gaps |
| 25 | cleanup-agent | — | Archive swarm reports | skipped | Already organized | Correct — no action needed |

---

## Rejected Patterns (learn from these)

These types of proposals waste time. Avoid repeating:

1. **API gateway / microservices** — rejected every time. Monolith works. Bring data (requests/sec, latency) if proposing this.
2. **Redis** — not needed until 2+ Railway instances. Stop proposing.
3. **ORM (SQLAlchemy, Prisma)** — Supabase SDK only. Non-negotiable.
4. **Privacy by default (hidden scores)** — CEO reviewed and chose public by default. Don't re-litigate.
5. **OpenAI as primary LLM** — Gemini is primary. OpenAI is fallback. This is cost decision.
6. **FastAPI WebSocket / ANUS real-time layer** — DSP ran 2026-04-01 (Score 28/50 — too low). EXPLICIT DEFER: do NOT propose this before 2026-07-01 OR 500 active users (whichever comes first). Alternative chosen: Supabase Realtime (already implemented Sprint C). If re-proposing, bring: connection count data, Railway cost impact, specific user workflow that polling can't serve.

---

## High-Value Proposal Patterns (do more of these)

1. **Specific security vulnerabilities with CVSS score** — always gets attention
2. **Storage/cost math** — CTO missed the 14-43GB/year calculation; agent caught it
3. **User journey gaps** — Leyla/Nigar persona reviews catch what code reviews miss
4. **Concrete file paths** — "fix line 39 in aura.py" > "fix the auth issue"
5. **Calibrated estimates** — "3 hours, not 3 days" with specific breakdown

| 42 | security-agent | P0-ROUTE | Route ordering: /me/explanation unreachable (shadowed by /{volunteer_id}) | implemented | Fixed — reordered routes in aura.py. Static before parameterized. | **Session 25 agent was RIGHT, CTO was WRONG.** Previously dismissed as "FastAPI handles it" — it doesn't. |
| 42 | security-agent | P0-XSS | Stored XSS via unescaped DeCE quotes from LLM | implemented | Fixed — html.escape() on all LLM-extracted quotes before storage | Correct — LLM output is untrusted data |
| 42 | security-agent | P1-INJECT | Concept ID injection via LLM returning arbitrary keys | implemented | Fixed — concept ID allowlist filter | Correct — LLM can hallucinate key names |
| 42 | qa-agent | CROSS-TEST | Blind cross-test proving keyword_fallback = vocabulary test | implemented | 33 tests, 3 personas. Buzzwords scored 0.77 vs experts 0.59-0.89. | Methodology was correct — CEO validated findings |
| 42 | qa-agent | SELF-ASSESS | Self-assessment was circular (Mistake #47) | acknowledged | Agents designed questions, knew keywords, scored their own answers. | CEO caught it: "they prepared the test and took it knowing answers" |
| 42 | swe-agent | VERB-REGEX | Expanded verb regex from 45 to 100+ verbs | implemented | Added assessment-domain verbs (explain, recognize, escalate, verify, protect). Fixed false positive: expert answer dropped 0.881 -> 0.485, restored to 0.65 ratio. | Correct diagnosis and fix |
| 42 | qa-agent | GRS-GATE | Generated 95 tests for decay + DeCE, 24 tests for quality gate | implemented | All tests passing (512 total, +220 new) | High quality output — tests caught real edge cases |

**— Sessions 43–74: See git history. Summary below captures class-level outcomes. —**

| 52–55 | security-agent | PAYWALL-FAILOPEN | Fail-open paywall gate: missing profile row = free unlimited access | implemented | Fixed to fail-closed: `if not sub_result.data OR status in blocked_states: RAISE 402` | Correct. Classic fail-open. Added to Mistake #57 — new security pattern. |
| 52–55 | qa-agent | MOCK-SHIFT | Adding new DB call before existing mocks shifted all call indexes | implemented | Fixed 9 tests in 3 files. Rule: search for mock sequences when adding new first DB call. | Mistake #58 — mock sequences are implicit schemas |
| 52–55 | security-agent | I18N-BRACE | Single-brace {var} silently fails in i18next (requires double {{var}}) | implemented | Audited all new keys. Rule: ALWAYS double-brace syntax. | Mistake #59 — CLASS 4 |
| 60 | security-agent | RISK-011 | assert_production_ready() RISK-011 guard bypassed on dev/staging | implemented | Guard moved BEFORE env check. Safety guards fire on ALL envs. Cost guards production-only. | Mistake #61 — CRITICAL env safety bug |
| 60 | arch-agent | GROQ-CHAIN | Groq wired in config but absent from LLM fallback chain | implemented | Added `_call_groq()` to llm.py chain (Vertex→Gemini→Groq→OpenAI). 14,400 free req/day recovered. | Mistake #62 — config update ≠ service update. Always grep service file. |
| 70–73 | needs-agent | TASK-PROTO-V5 | Team Proposes protocol formalised — CEO directive compliance | implemented | TASK-PROTOCOL v5.0. Flow detection added (v5.3). Session 72 wrong flow triggered v5.0. | Prevents Mistake #49 class recurrence. |
| 73 | arch-agent | TRIBE-STREAKS | Board (nemotron-ultra-253b ×2) killed AURA Leaderboard unanimously | implemented | ADR-008 locked: Leaderboard removed. Tribe Streaks + Collective AURA Ladders approved. Cultural mismatch in AZ/CIS confirmed. | Board agents carry authority over DSP for cultural decisions |
| 75 | nigar-agent | ORG-ONBOARD-BUG | org onboarding never creates organizations row — B2B launch blocker | implemented | Auto-create orgs row after profile creation. 409 silently ignored. | FINDING-026 — always create both rows on org signup |
| 75 | qa-agent | SINGLE-MAYBESINGLE | `.single()` throws 500 instead of 404 on 0 rows | implemented | Changed 5 calls to `.maybe_single()` in organizations.py | FINDING-027 — NEVER .single() unless row is guaranteed |
| 75 | qa-agent | DISCOVERY-LEAK | discovery.py used base aura_scores table (leaked private columns) | implemented | Changed to aura_scores_public view | FINDING-028 — ADR mandate: always use public view in multi-user endpoints |
| 75 | security-agent | SESSION-EXPIRY | expires_at never checked — sessions ran indefinitely | implemented | Added expiry check in submit_answer + complete_assessment → 410 SESSION_EXPIRED | FINDING-033 |
| 77 | arch-agent | VERTEX-LLM | Vertex Express added as primary LLM (before Gemini) | implemented | llm.py rewrite: Vertex→Gemini→Groq→OpenAI. Singleton clients with reset for tests. | LLM fallback chain now has 4 levels. |
| 77 | security-agent | HEALTH-SUPABASE-REF | /health leaks no project ref — wrong DB invisible until outage | implemented | supabase_project_ref added to HealthResponse. CEO can verify Railway→DB link. | S-02: "curl /health to see which DB is live" |
| 78 | arch-agent | SWARM-HEARTBEAT | Daily swarm always ran even with nothing to do | implemented | heartbeat_gate.py: 3-condition KAIROS gate. Exit 0=RUN, Exit 1=SKIP. | Stops noisy CI/CD waste. Rule: idle = skip. |
| 78 | arch-agent | CODE-INDEX | Agents launched blind — no file awareness | implemented | code_index.py indexes 530 files. task_binder.py maps task→files. Injected into every agent brief. | Mistake #60 class prevention. |
| 78 | arch-agent | PROPOSAL-VERIFIER | Agents propose files that don't exist | implemented | proposal_verifier.py: checks file paths. 96.7% grounded. Caught 1 hallucinated route path. | Prevents wasted sprint cycles |
| 79 | arch-agent | REALTIME-POLLING | Notification polling adds RTT on every dashboard visit | implemented | Supabase Realtime subscription. RealtimeNotificationsProvider in layout. WebSocket deferred to 2026-07-01 / 500 users. | DSP Score 28/50 for WebSocket — explicitly deferred |
| 79 | nigar-agent | SAVED-SEARCH-B2B | Orgs had no way to save talent search criteria | implemented | org_saved_searches table + 4 endpoints + match_checker.py daily cron + Telegram notifications | Sprint 8 — full B2B saved search stack |
| 79 | security-agent | SEARCH-CROSSORG | Cross-org saved search access not validated | implemented | `_assert_search_ownership()` in organizations.py. Org A cannot touch Org B's searches. | B2B privilege escalation blocked |
| 80 | cultural-agent | CIS-COMPETITIVE | "Top 5%" framing causes anxiety in AZ/CIS users | implemented | Replaced percentile with achievement level (Expert/Advanced/Proficient/Growing/Building/Starting). `getAchievementLevelKey()` utility. | CIS-001 fix. Cultural framing > competitive framing for AZ. |
| 80 | arch-agent | PROFILE-VIEW-NOTIFY | Orgs viewing profiles triggered no notification to volunteer | implemented | notify_profile_viewed() + partial index for 24h throttle. Org view → push notification. | Sprint D.1 — professional profile intelligence |
| 81 | security-agent | ADMIN-FAILCLOSED | Admin panel must fail-closed (non-admin → 403) | implemented | require_platform_admin dep. Checked service-role (bypasses RLS). Returns 403 if not admin. | 3 gate tests: non-admin, unauth, missing profile all → 403 |
| 81 | qa-agent | FULL-AUDIT | 5-agent parallel codebase audit: backend+frontend+infra+docs+arch | completed | Architecture health 72/100. CRIT-I01 (no body size limit) found. Docs CRITICALLY stale. All 20 migrations solid. | Audit-2026-04-02. See ARCHITECTURE.md (pending) for full synthesis. |

---

## Rejected Patterns (learn from these)

These types of proposals waste time. Avoid repeating:

1. **API gateway / microservices** — rejected every time. Monolith works.
2. **Redis** — not needed until 2+ Railway instances. Stop proposing.
3. **ORM (SQLAlchemy, Prisma)** — Supabase SDK only. Non-negotiable.
4. **Privacy by default (hidden scores)** — CEO chose public by default. Don't re-litigate.
5. **OpenAI as primary LLM** — Gemini is primary. OpenAI is fallback. Cost decision.
6. **Single-word keywords in questions** — Proven gameable (Session 42). GRS gate enforces multi-word.
7. **Self-assessment as evidence** — Circular by definition (Mistake #47). Use blind cross-testing.

---

## High-Value Proposal Patterns (do more of these)

1. **Specific security vulnerabilities with CVSS score** — always gets attention
2. **Storage/cost math** — CTO missed the 14-43GB/year calculation; agent caught it
3. **User journey gaps** — Leyla/Nigar persona reviews catch what code reviews miss
4. **Concrete file paths** — "fix line 39 in aura.py" > "fix the auth issue"
5. **Calibrated estimates** — "3 hours, not 3 days" with specific breakdown
6. **Blind cross-testing methodology** — Session 42 proved its value (CEO validated)
7. **GRS analysis on new questions** — compute_grs() before proposing any question

---

## Dismissed Findings Review (every 5 sessions — added Session 42)

**Why this exists:** Security Agent found route shadowing in Session 25. CTO dismissed it as "FastAPI handles it." It was a P0 bug that lived in production for 17 sessions until Session 42. Cost: unknown number of users hit dead /me/explanation endpoint.

**Rule:** Every 5 sessions, scan this log for `rejected` or `acknowledged` findings. Re-verify each one against current codebase. If the finding is still valid → fix it. Cost of re-checking: 5 minutes per finding. Cost of a missed P0: hours of debugging + user impact.

**Next review due:** Session 47

---

## Session 69 — Skill Activations (First-Time Findings)

| Session | Agent/Skill | Proposal ID | Short Title | Status | Outcome | Note |
|---------|-------------|-------------|-------------|--------|---------|------|
| 69 | Behavioral Nudge | BNE-001 | Assessment 8-select cognitive overload | open | 4 findings: single-path violation, no save messaging, time estimates missing | **FIRST ACTIVATION. HIGH impact.** |
| 69 | Cultural Intelligence | CIS-001 | Percentile framing = competitive, not collectivist | implemented | Session 80: "Top 5%" → achievement level labels (Expert/Advanced/Proficient/Growing/Building/Starting). Fixed in /u/[username] + assessment/complete pages. AZ translations: Ekspert/Peşəkar/Bilikli/İnkişaf Edir. | **FIXED Session 80.** |
| 69 | Cultural Intelligence | CIS-002 | Name field lacks patronymic hint | open | P1: "Adınız Soyadınız (məs. Yusif Eldar oğlu)" | **AZ UX friction.** |
| 69 | Firuza (v2.0) | FIR-v2-001 | Proactive scan protocol activated | implemented | Upgrade: reactive → proactive, influence 1.1 | **V2.0 shipped.** |
| 69 | Security | SEC-S69-001 | Route shadowing vindication | acknowledged | Score: 8.5 → 9.0 (Expert ⭐) | **CTO was wrong, agent was right.** |

---

## Notes for Next Review Cycle

- BUG-01 (swarm evaluation_log) needs agent proposal with specific code change
- Phase 3 scope needs product-agent input on discovery endpoint design
- Architecture agent should review team_leads.py wiring when it's planned (BUG-04)
- QA agent should run GRS audit on any new questions proposed by agents
- Security agent's route ordering finding deserves score upgrade (dismissed Session 25, proved correct Session 42)
