# ADR-008: ZEUS Governance Layer — Audit Log & Policy Introspection

**Date:** 2026-04-11 (migration), 2026-04-12 (documented)
**Status:** ACCEPTED
**Sprint:** Session 93
**Deciders:** CTO-Hands (Atlas, Claude Opus 4.6), CEO (Yusif Ganbarov)
**Related:** `docs/CONSTITUTION_AI_SWARM.md` Part 5, AI Council brief (Gemini Constitutional + Perplexity on ADR/event sourcing), migrations `20260411193900_zeus_governance.sql` + `20260411200500_zeus_harden.sql`

---

## Context

The swarm, the CTO-Hands role, and future agent hierarchies need a single immutable record of governance decisions — challenges, CEO vetoes, provider fallbacks, policy violations, reconciliations. Before this ADR, there was nothing structural. Agent decisions lived in scattered log files, `memory/swarm/proposals.json`, `memory/swarm/ceo-inbox.md`, and ephemeral stdout. Reconstructing "what happened when" required grep across files with no guarantee of completeness.

Additionally, live RLS policy introspection was blocked by PostgREST's refusal to expose `pg_catalog` (error PGRST106: "Only public and graphql_public schemas are exposed"). Any SDK-level call against `pg_policies` failed. P0 verification of `character_events` RLS policies was therefore impossible without manual SQL Editor access.

The AI council brief (Gemini Constitutional section) mandated an immutable event sourcing layer and a whistleblower-capable Auditor Agent outside the CTO hierarchy. Perplexity's ADR recommendations called for capturing architecturally significant decisions in a machine-readable audit trail. These two needs converged into a single piece of infrastructure.

---

## Decision

**Chosen:** A new `zeus` schema in Supabase Postgres containing:

1. **`zeus.governance_events`** — immutable append-only audit log table.
   - Columns: `id uuid pk`, `event_type text`, `severity text`, `source text`, `actor text nullable`, `subject text nullable`, `payload jsonb`, `created_at timestamptz default now()`.
   - RLS enabled, no user policies — only service role can read or write.
   - No UPDATE or DELETE triggers. Rows are written once.

2. **`public.inspect_table_policies(p_table_name text)`** — SECURITY DEFINER RPC that wraps `pg_catalog.pg_policies`.
   - Returns all RLS policies for a given table as a structured table.
   - Callable via Supabase SDK with the table name as argument.
   - Revoked from `PUBLIC`, `anon`, and `authenticated` roles. Granted only to `service_role`. Hardened in follow-up migration after security audit caught that `authenticated` default access was live for 27 minutes post-deploy.

3. **`public.log_governance_event(...)`** — SECURITY DEFINER RPC for structured insert.
   - Arguments: `p_event_type`, `p_severity`, `p_source`, `p_subject`, `p_payload jsonb`.
   - Same role-access hardening as `inspect_table_policies`.

4. **Unique partial index** on `(event_type, subject)` where `event_type = 'reconciliation'` — prevents duplicate reconciliation seeds across migration re-runs. Uses `ORDER BY created_at ASC LIMIT 1` pattern (not `MIN(uuid)` which Postgres does not support, hard-learned 2026-04-11).

### Alternatives considered

- **Use the existing `agent_memory_log` table** (migration 20260403000002) — rejected because that table is product-level, not governance-level. Mixing them would blur the audit boundary.
- **Use a separate append-only service (e.g. AWS EventBridge, Kafka)** — rejected because it adds infrastructure cost and latency for a use case that fits comfortably in Postgres with proper RLS.
- **Store governance events in flat JSON files in the repo** — rejected because immutability cannot be guaranteed and queryability is poor.
- **Wait for full event sourcing + CQRS architecture** — rejected as over-engineering for Q1. This layer is the minimal viable governance store; full event sourcing is a Q2-Q3 target per the AI council brief and is tracked separately.

---

## Consequences

**Positive:**
- Live RLS verification now works through the Supabase SDK via `inspect_table_policies`. P0-1 from Perplexity's proposal (RLS check on `character_events`) is closed structurally, not manually.
- Every governance decision has a permanent record. `docs/PERPLEXITY-RECONCILIATION-2026-04-11.md` is the first entry and links back via seed row.
- `emit_fallback_event` in `model_router.py` (ADR-007) has a real sink — no more fire-and-forget-into-void for production provider fallbacks.
- Future Auditor Agent (Constitution AI Swarm Part 3) has a table to read and write.
- Event retention policy is trivially implementable via partial indexes and a daily `DELETE WHERE created_at < now() - interval '14 days'` cron for short-term context rows.

**Negative:**
- The initial migration had a CRITICAL security hole — `authenticated` role could call both RPCs directly for 27 minutes post-deploy because I revoked from PUBLIC/anon but forgot authenticated. Caught by parallel security audit agent, fixed in follow-up migration. This is documented as a Class-1 mistake in `memory/context/mistakes.md` and in `memory/atlas/lessons.md`.
- `zeus` schema is not exposed through PostgREST by default, so applications cannot query the governance log directly via the SDK. Only service-role Python code can. This is by design but means CEO cannot view the log from a dashboard without custom tooling. Dashboard is Q2 work.
- First harden migration attempt used `MIN(uuid)` which does not exist in Postgres — entire transaction rolled back including the critical REVOKE. Re-wrote using `ORDER BY created_at ASC LIMIT 1`. Twelve minutes of production exposure between attempts. Lesson now in `memory/atlas/lessons.md`.

**Neutral:**
- `docs/DECISIONS.md` still contains historical decisions from before this ADR process. Not worth migrating — ADRs going forward, `DECISIONS.md` as legacy reference.

---

## Verification

- `supabase db push` applied both migrations successfully after the harden fix.
- `admin.rpc('inspect_table_policies', {'p_table_name': 'character_events'})` returned `[{'policyname': 'insert_own', 'cmd': 'INSERT', 'with_check': '(auth.uid() = user_id)'}, ...]` — live RLS verified.
- `admin.rpc('log_governance_event', {...})` returned fresh UUID `d9e258f1-...` on first call, `b05795a9-...` on second call after harden migration — both successful.
- Seed row for Session 93 reconciliation event is present exactly once in the table (verified via unique index enforcement on re-run).
- `authenticated` role EXECUTE permission on both RPCs was revoked in `20260411200500_zeus_harden.sql` and verified via `pg_proc` inspection — no untrusted role can call either function.

---

## Follow-ups

1. **Auditor Agent** — the whistleblower-path agent that runs outside CTO hierarchy and alerts CEO via Telegram on Level 0 violations. Described in `docs/CONSTITUTION_AI_SWARM.md` Part 3. Not yet built. Q2 target.
2. **Dashboard or CLI for CEO** — so CEO can `zeus events --severity high --last 7d` without writing Python. Low-priority, deferred until CEO volume of governance events grows.
3. **14-day retention cron** — `DELETE FROM zeus.governance_events WHERE severity = 'low' AND created_at < now() - interval '14 days'` as a Supabase cron job. Not yet scheduled.
4. **Event sourcing + CQRS** — full replay architecture per Gemini Constitutional Block 5. Target Q2-Q3, ADR to follow at time of decision.
5. **PII hashing** — ensure that any payload containing user data passes through a salted hash before insert, per the AI council brief (privacy-preserving logging). Enforcement is currently by convention, not by schema constraint. Q2 hardening.
