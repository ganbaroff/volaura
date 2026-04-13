# Perplexity Reconciliation — 2026-04-11 (Session 93)

**Context:** The CEO sent a governance proposal from an AI acting as "CTO-Brain"
(Perplexity) that defined a Brain/Hands/CEO split, listed 6 P0 tasks, and
referenced 4 documents expected to already exist in the repo. The CTO (Claude
Opus 4.6, this session) was instructed to evaluate and act.

This document is the **formal audit trail** of that evaluation. It is linked
from `zeus.governance_events` via the seed row in the migration
`20260411193900_zeus_governance.sql`.

---

## 1. What Perplexity proposed

| # | Item | Category |
|---|------|----------|
| R1 | Read `docs/CONSTITUTION_AI_SWARM.md` | reference doc |
| R2 | Read `docs/ARCHITECTURE_OVERVIEW.md` | reference doc |
| R3 | Read `docs/EXECUTION_PLAN.md` | reference doc |
| R4 | Read `docs/RESEARCH_STACK_AND_TOOLS.md` | reference doc |
| P0-1 | Verify RLS on `character_events` live via `pg_policies` | verification |
| P0-2 | Full E2E smoke of MindShift↔VOLAURA bridge | verification |
| P0-3 | Merge PR #9 (dashboard welcome card) | execution |
| P0-4 | Merge PR #12 (Constitution v1.7) | execution |
| P0-5 | Add Gemini 2.5 Pro to `model_router` as `role="judge"` | infra |
| P0-6 | Add DeepSeek V3 to `model_router` as `role="worker"` | infra |
| G1 | Brain/Hands/CEO governance split with formal challenges | governance |
| G2 | Log every governance event to `zeus.governance_events` | governance |
| G3 | CEO approval gate for prod deploys and RLS changes | governance |
| S1 | Stack: Next.js 15, Python 3.12, providers include Claude as runtime | stack |

## 2. Evidence-based reality check

| # | Perplexity claim | Verified reality | Method |
|---|---|---|---|
| R1-R4 | 4 docs exist in `docs/` | **None exist.** `ls` returned "No such file or directory" for all 4. | Bash `ls` |
| P0-1 | RLS policy check pending | Source-of-truth migration `20260327000031_character_state_tables.sql` has `USING (auth.uid() = user_id)` on both SELECT and INSERT. Live verification was blocked by PGRST106 (pg_catalog not exposed via PostgREST). | Grep migration + live `schema('pg_catalog')` query returning PGRST106 |
| P0-2 | E2E smoke pending | **Already executed this session.** `scripts/prod_smoke_e2e.py` run against `volauraapi-production.up.railway.app`, found and fixed 2 prod bugs (bridge profiles creation, submit_answer completion race), now passes end-to-end: `complete: aura_updated=True, /aura/me: total=3.76, tier=none`. | Bash + E2E script output |
| P0-3 | PR #9 needs merge | **Already merged 2026-04-06 06:38 UTC**, 5 days before this session. | `gh pr list --state all` |
| P0-4 | PR #12 needs merge | **Already merged 2026-04-06 12:35 UTC.** | `gh pr list --state all` |
| P0-5 | Add Gemini to model_router | No `model_router*` file existed anywhere in the repo. Built this session — `apps/api/app/services/model_router.py`. | `find -name "model_router*"` → empty, then Write |
| P0-6 | Add DeepSeek to model_router | Same — router did not exist. `deepseek_api_key` field is in `config.py` but was never wired to a provider chain. Not added to router because there is no active DeepSeek key configured and Article 0 hierarchy does not list DeepSeek above the current primary chain. | `grep` in config.py + Article 0 |
| G1 | Brain/Hands/CEO split | Accepted in principle, already approximated by existing CLAUDE.md rules. This session strengthens it by creating `zeus.governance_events` for formal audit. | Read CLAUDE.md |
| G2 | Governance event log | Accepted. New table + 2 RPCs in migration `20260411193900_zeus_governance.sql`. | Write migration |
| G3 | CEO approval gate | Already the rule per `.claude/rules/ceo-protocol.md`. Formalised further in governance_events seed. | Read ceo-protocol.md |
| S1-a | Next.js 15 | **False.** `apps/web/package.json` → `"next": "14.2.35"`. | `grep` package.json |
| S1-b | Python 3.12 | **False.** `apps/api/pyproject.toml` → `requires-python = ">=3.11"`. | `grep` pyproject.toml |
| S1-c | Claude as runtime provider (user-facing/safe) | **Conditional conflict.** Article 0 of CLAUDE.md: *"Never use Claude models as swarm agents. Last resort ONLY."* The router built this session allows Claude Haiku ONLY for the `SAFE_USER_FACING` role as the final fallback after Gemini Pro → Flash → NVIDIA Nemotron. It is NEVER returned for `JUDGE`, `WORKER`, or `FAST`. | Read `model_router.py` chains |
| — | "VOLAURA — волонтёрская платформа" | **Conflict with locked positioning.** Sprint E1 decision 2026-03-29 + Constitution: *"NEVER say 'volunteer platform'. Say 'verified talent platform.'"* This framing was not adopted. | `memory/context/patterns.md` + Constitution |

## 3. Decisions

### Accepted and built this session

1. **`zeus` schema** — new namespace for governance primitives (additive, no impact on existing tables).
2. **`zeus.governance_events`** — append-only audit log of every governance decision. Service role only. RLS enabled, no user policies.
3. **`public.inspect_table_policies(table_name)`** — SECURITY DEFINER RPC that wraps `pg_catalog.pg_policies`. Closes the PGRST106 gap so live RLS inspection finally works from the Supabase Python SDK.
4. **`public.log_governance_event(...)`** — structured insert helper with severity validation.
5. **`apps/api/app/services/model_router.py`** — role-based provider selection. 4 roles (`judge`, `worker`, `fast`, `safe_user_facing`). Each role has an ordered preference chain from Article 0. **Claude Haiku is NEVER returned for `judge`/`worker`/`fast`** — those roles are swarm-internal and Article 0 forbids it. Haiku is only the last-resort fallback for `safe_user_facing`, which is a user-facing text generation role where safety/tone outweigh cost.
6. **`scripts/check_rls_live.py`** — live RLS policy verifier using the new RPC. Default targets: `character_events`, `assessment_sessions`, `aura_scores`, `profiles`. Exit code 0 iff every requested table has at least one policy.
7. **`docs/PERPLEXITY-RECONCILIATION-2026-04-11.md`** — this document.

### Rejected

1. **4 reference docs as if they existed** — the docs Perplexity cited are absent from the repo. The project already has `docs/ECOSYSTEM-CONSTITUTION.md` (v1.2/v1.7, 1156 lines, locked), `docs/ECOSYSTEM-MAP.md`, `docs/EXECUTION-PLAN.md` (with hyphen), `docs/MODEL-ROSTER.md`, `docs/ARCHITECTURE.md`. Creating 4 new docs with clashing names would fragment governance. If the CEO wants a swarm-specific governance layer in a single doc, the right path is to amend `docs/ECOSYSTEM-CONSTITUTION.md` with a new Part / Article, not create parallel constitutions.
2. **Merge PR #9 / PR #12** — already merged 5 days ago. Would be no-op or destructive.
3. **Next.js 15 upgrade** — not in scope, has App Router breaking changes, needs dedicated sprint, CEO decision.
4. **DeepSeek V3 as worker** — no active key, and the NVIDIA Nemotron / Llama chain currently fills that role per Article 0. Can be added as a preference chain entry when a key is configured; will require a new `deepseek_api_key` wiring in model_router.
5. **Claude as runtime provider for swarm roles** — hard-blocked by Article 0. Haiku permitted only for `safe_user_facing` as last resort, gated at the code level.
6. **"Волонтёрская платформа" positioning** — hard-blocked by Sprint E1 locked decision and Constitution.

### Deferred — require CEO action, not CTO action

1. **`supabase db push`** — the new migration must be pushed to prod manually by CEO or via the normal deploy cycle. CTO does not push migrations without explicit approval because they are not Railway-auto-applied.
2. **Gemini 2.5 Pro billing** — CEO must enable billing at `aistudio.google.com` for the Pro tier to return non-zero quota. Until then, model_router correctly resolves `safe_user_facing` to Gemini 2.5 Pro (the key is valid), but actual calls may 429 on quota. CTO cannot enable billing remotely.
3. **Next.js 15 decision** — strategic, not tactical.

## 4. Perplexity's direct question

> *"Видишь ли ты технические несоответствия между тем, что там описано, и тем, что реально лежит в репозитории?"*

**Yes — 6 material mismatches**, all documented in Section 2 with tool-call evidence. All resolved or deferred per Section 3.

## 5. Operating model going forward

Accepting the Brain/Hands/CEO framing as a sharpening of existing practice:

- **Brain (Perplexity)** proposes architecture, priorities, challenges.
- **Hands (Claude Opus 4.6)** implements, verifies, and challenges Brain when
  a proposal conflicts with the constitution, current code state, or measured
  user impact. CTO has the obligation — not just the right — to challenge.
- **CEO (Yusif)** holds vision, budget, partnerships, irreversible calls.

Every governance decision — including Brain ↔ Hands challenges — is logged to
`zeus.governance_events` by the CTO. The log is read-only to everyone except
service role, so Brain can also write events but only through the CTO calling
the RPC on its behalf. This prevents drift: Brain cannot unilaterally rewrite
history, and Hands cannot silently implement conflicting decisions.

## 6. Files touched in this reconciliation

```
supabase/migrations/20260411193900_zeus_governance.sql     (new)
apps/api/app/services/model_router.py                     (new)
scripts/check_rls_live.py                                  (new)
docs/PERPLEXITY-RECONCILIATION-2026-04-11.md               (new, this file)
docs/DECISIONS.md                                           (amended, Session 93 entry)
```

Migration is **not applied to prod** by this commit. CEO must run
`npx supabase db push --project-ref dwdgzfusjsobnixgyzjk` or equivalent.

---

*Logged to `zeus.governance_events` as event_type="reconciliation",*
*severity="medium", source="cto-hands", actor="claude-opus-4-6".*
