# Agent Feedback — Distilled Rules

**Fallback mode** (LLM unavailable) | Generated: 2026-04-14 11:33 UTC

---

## ❌ NEVER PROPOSE

- **API gateway / microservices** — rejected every time. Monolith works. Bring data (requests/sec, latency) if proposing this.
- **Redis** — not needed until 2+ Railway instances. Stop proposing.
- **ORM (SQLAlchemy, Prisma)** — Supabase SDK only. Non-negotiable.
- **Privacy by default (hidden scores)** — CEO reviewed and chose public by default. Don't re-litigate.
- **OpenAI as primary LLM** — Gemini is primary. OpenAI is fallback. This is cost decision.
- **FastAPI WebSocket / ANUS real-time layer** — DSP ran 2026-04-01 (Score 28/50 — too low). EXPLICIT DEFER: do NOT propose this before 2026-07-01 OR 500 active users (whichever comes first). Alternative chosen: Supabase Realtime (already implemented Sprint C). If re-proposing, bring: connection count data, Railway cost impact, specific user workflow that polling can't serve.
- **Single-word keywords in questions** — Proven gameable (Session 42). GRS gate enforces multi-word.
- **Self-assessment as evidence** — Circular by definition (Mistake #47). Use blind cross-testing.

## ✅ HIGH-VALUE PATTERNS

- **Specific security vulnerabilities with CVSS score** — always gets attention
- **Storage/cost math** — CTO missed the 14-43GB/year calculation; agent caught it
- **User journey gaps** — Leyla/Nigar persona reviews catch what code reviews miss
- **Concrete file paths** — "fix line 39 in aura.py" > "fix the auth issue"
- **Calibrated estimates** — "3 hours, not 3 days" with specific breakdown
- **Blind cross-testing methodology** — Session 42 proved its value (CEO validated)
- **GRS analysis on new questions** — compute_grs() before proposing any question
