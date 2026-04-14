# Swarm Research Index — Atlas Memory Orientation

**Purpose:** one-line takeaway per deep-research deliverable in `memory/swarm/research/` so Atlas can pull the relevant file on demand without re-reading all five. Paired with `memory/atlas/ceo-feed/INDEX.md` — same pattern, same discipline.

**Generated:** 2026-04-14 by Atlas during deep-absorb pass.

---

## High-priority actionable research

**`assessment-science-audit-2026-04-12.md`** (29 lines, Groq llama-3.3-70b first activation)
Psychometric hard gate for B2B launch. Guessed IRT parameters produce SEM 2-5x higher than calibrated (Ackerman 1994 cited). Minimum calibration sample: **1000-2000 test-takers**, not 300. Five-question low-energy mode is NOT psychometrically defensible per ITC 2018 standards — minimum 10-15 per competency. DIF risk for AZ/RU/EN due to translation errors + cultural bias. Tied to WUF13 pre-launch item #16 (MIRT upgrade) and open proposal `5d5216aa`.

**`observability-backend-decision-2026-04-12.md`** (164 lines, Observability Specialist role)
Decision landed: **Langfuse Cloud EU (free tier 50K observations/month → Core $59/mo)**. Already partially wired via `_trace` decorator in `apps/api/app/services/llm.py` — zero switching cost. Supports OpenTelemetry so Groq / Ollama / NVIDIA NIM / Cerebras plug in via OpenInference. EU region has SCCs + DPA + SOC2 Type 2. Self-host on Railway Clickhouse is Plan B. **Finish the 2-hour wiring** — not a migration, a completion.

**`elite-audit-session93-2026-04-12.md`** (70 lines, Security Agent 9.0 + Firuza Council 7.5)
Security top 5 with CVSS scores. **CVSS 9.8** — `.env` with 20+ plaintext keys, need `git-secrets` pre-commit hook (not yet installed per my grep). **CVSS 8.1** — memory files no integrity check, any agent can inject false memories; proposal: HMAC-SHA256 per file with author metadata + append-only log. **CVSS 8.0** — SUPABASE_JWT_SECRET empty locally disables bridge endpoint. **CVSS 7.5 FIXED** — Groq/Cerebras expired keys (later commits). **CVSS 5.7** — CORS hardcoded Railway URL goes stale after redeploy.

**`session-93-7-parallel-research-2026-04-12.md`** (214 lines, 7 agents × parallel)
Seven deep-research runs consolidated. Highest-value section: **Cultural Intelligence Strategist** on AZ/CIS launch framing. VOLAURA not ready for AZ/CIS without three copy fixes — not translation, framing. Hofstede's power-distance 78 + individualism 25 mean "Top 5%" / "compete with peers" / "you've been discovered" triggers status anxiety. Top fix: reframe AURA score as **professional credential, not rank** — copy-only change, +35-40% trust lift. Contains six more agent outputs (user research, growth, community, etc.) worth separate read before AZ launch.

---

## Large — separate treatment

**`competitive-intelligence-2026-04-12.md`** (261 lines, Competitor Intelligence Agent activation)
Full competitive landscape audit. Tests VOLAURA's implicit moat (verified skills + IRT/CAT + AI open-text evaluation + AURA score across ecosystem) claim-by-claim. Explicitly "refuses to flatter VOLAURA" — read Section 8 first if you want the unvarnished version. Too large for one-line; read before pitch-deck revisions, investor conversations, or feature-scope decisions.

---

## Cross-references

These five are the `remember_everything.md` directive's concrete content: "Read them before any work on cultural/behavioural/legal/assessment fronts."

- Assessment feature design → read `assessment-science-audit`
- AZ/CIS copy work → read `session-93-7-parallel-research` §Cultural Intelligence
- Pitch-deck / investor narrative → read `competitive-intelligence`
- Security sprint → read `elite-audit-session93`
- LLM tracing / observability work → read `observability-backend-decision`

## Rule going forward

Same discipline as ceo-feed INDEX: any new swarm research file appends a one-line entry to this INDEX at commit time. Otherwise the folder re-accumulates unindexed drops and the forgetting cycle repeats.
