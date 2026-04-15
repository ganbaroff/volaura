# RLS testing stack research — 2026-04-15

Author: Atlas. Memory gate: passed. Inputs read: `20260324000015_rls_audit_fixes.sql`, `20260415124500_registrations_tighten_volunteer_update.sql`, `apps/api/tests/conftest.py`, ghost-audit 2026-04-15 §2.1.

## TL;DR (Doctor Strange)

Adopt **pgTAP + Basejump test-helpers** as the primary RLS test framework, driven by `supabase test db` in GitHub Actions, and complement with **Splinter** (official Supabase linter, via Supabase MCP) in the same CI pipeline. Keep a thin pytest layer using supabase-py with a 3-client fixture (admin / anon / authenticated-user) for end-to-end attack tests that must travel through FastAPI + PostgREST. Phase-2: Semgrep custom rules over `supabase/migrations/**/*.sql` to catch anti-patterns pre-commit.

Evidence: pgTAP is the tool Supabase themselves ship (`supabase test db`), Basejump helpers are the de-facto community standard since 2022, and Makerkit reports running this stack across 100+ production SaaS deployments. No other tool has that depth of production exposure. Splinter is already running inside every Supabase project — wiring it into CI is zero-cost.

## Current VOLAURA state

- 0 RLS tests. 1 trigger landed today (`20260415124500_registrations_tighten_volunteer_update.sql`).
- 86 migrations total; the RLS-relevant baseline is `20260324000015_rls_audit_fixes.sql` (C1–C8, H1–H3, L1–L3 fixes).
- Existing test infra: pytest + httpx ASGI (`apps/api/tests/conftest.py`). No Supabase CLI in CI. No pgTAP suite. No Splinter pre-merge check.
- Ghost-audit 2026-04-15 §2.1 found the volunteer self-rating injection path because no test existed for "UPDATE with allowed status + tampered other columns". Trigger patches the symptom; missing test is the root cause.

## Top options analyzed

| Option | Setup cost | Test-writing cost | CI integration | Verdict |
|--------|-----------:|------------------:|----------------|---------|
| **pgTAP + Basejump helpers** | 10 min (drop helper file into `supabase/tests/`) | ~15 min per policy pair (allow + deny) | `supabase/setup-cli@v1` + `supabase start && supabase test db`. ~3 min per PR. | **Adopt. Primary.** |
| **Splinter (official linter)** | 0 (already runs in project). Add check via Supabase MCP or API call. | 0 — static check. | One curl job in GitHub Actions; fail PR if new high-severity lint. | **Adopt alongside pgTAP.** |
| **pytest + supabase-py (3-client fixture)** | ~1 h (fixture + env vars in CI) | ~20 min per attack case | Runs in existing pytest job against a Supabase branch DB or local stack. | **Adopt, scoped to end-to-end attack tests only (5–10 tests max).** |
| **Supashield CLI** | 15 min | Generates tests automatically | `supashield test --json` in CI. | Useful for bootstrapping test suite + second-opinion audit. Don't make it the only layer — it's a single-author OSS, smaller community. |
| **Supabomb / SupaSec (pentest tools)** | 30 min | N/A (exploit-driven) | Pre-launch red-team only; too noisy for per-PR. | Occasional, not CI. |
| **supabase-test (LaunchQL, JS)** | Medium | JS-only | Doesn't fit FastAPI stack. | Skip. |
| **Semgrep custom SQL rules** | 1 d author + 0.5 d maintenance/quarter | Rules capture intent once, apply to every migration. | `semgrep --config ./semgrep-rls.yml` in pre-commit + CI. | **Adopt Phase 2 after pgTAP is live.** |
| Hypothetical `@supabase/rls-suite`/`supatest` | — | — | — | **Do not pursue — does not exist** (confirmed: no official package of these names). |

## Attack-surface checklist (audit our existing policies against this)

Concrete drift points. For each, the file `20260324000015_rls_audit_fixes.sql` should be re-reviewed and a pgTAP test written.

1. RLS enabled AND `FORCE ROW LEVEL SECURITY` on every `public.*` table. Owner bypass otherwise. **Verify on all 12 audited tables — the migration does not include FORCE.**
2. No `FOR ALL` policy survives. H3 already split events; audit the remaining tables for lurking FOR ALL.
3. UPDATE policies have both `USING` and `WITH CHECK`.
4. Partial-column UPDATE restrictions use BEFORE UPDATE trigger with `IS DISTINCT FROM` per column — the idiomatic Postgres workaround, because RLS `WITH CHECK` cannot reference `OLD`. Today's trigger is the template — generalise wherever a policy comment says "enforced at application layer too" (that phrase is a code smell).
5. SECURITY DEFINER functions set `search_path = public, pg_temp` (today's trigger does; audit `upsert_aura_score`, `match_volunteers`).
6. SECURITY DEFINER RPCs that are NOT intentional RLS-bypasses re-check `auth.uid()` inside.
7. Views use `security_invoker = TRUE` on PG15+, not just `security_barrier`. Check `aura_scores_public`, `questions_safe`.
8. No policy references `raw_user_meta_data` or `user_metadata` (user-mutable → privesc). Splinter lint 0015.
9. `auth.uid()` calls wrapped as `(SELECT auth.uid())` (initPlan caching). Splinter lint 0003.
10. No multiple permissive policies on same table+cmd hiding a `TRUE` dominator. Splinter lint 0006.
11. Every column referenced in a policy predicate is indexed.
12. No `BYPASSRLS` on app roles.
13. `service_role` key present only in `apps/api/**` and CI secrets — never in `apps/web/**`. One-line grep check in CI.
14. Policies explicitly `TO authenticated` / `TO anon` — no implicit role.
15. Trigger-disable events monitored: `pg_trigger` row change = Sentry alert.
16. Any `USING (TRUE)` policy is justified in a SQL comment (policy IS the open door — intent must be documented).

## Proposed 1-week adoption path

**Day 1 — Baseline pgTAP (CTO + 1 swarm engineer).**
- Drop `https://github.com/usebasejump/supabase-test-helpers` into `supabase/tests/00000-supabase_test_helpers.sql`.
- Create `supabase/tests/000-setup.sql` with shared fixtures (known org, known volunteer, known event).
- Write `supabase/tests/001-rls-enabled.sql`: one-liner `SELECT tests.rls_enabled('public')` asserting every table has RLS on. This alone catches future "forgot ENABLE" regressions.
- Run locally: `supabase start && supabase test db`. Commit.

**Day 2 — First 10 policy tests, centred on today's fix.**
- `010-registrations-volunteer-update.sql` — both positive (cancel allowed) and negative (inject coordinator_rating blocked). This is the test that would have caught the ghost-audit finding.
- `011-aura-scores-write.sql` — user cannot INSERT/UPDATE own aura_scores (FIX H1).
- `012-volunteer-embeddings-read.sql` — authenticated cannot SELECT (FIX C3).
- `013-questions-base-table.sql` — authenticated cannot read raw questions (FIX C4).
- `014-volunteer-behavior-signals-insert.sql` — user cannot forge for others (FIX C1).
- `015-registrations-delete.sql` — volunteer cannot DELETE (FIX C7 tail).
- `016-expert-verifications-volunteer-id.sql` — cannot insert for non-existent volunteer (FIX H2).
- `017-events-draft-visibility.sql` — drafts hidden from anon/other orgs (FIX H3).
- `018-volunteer-badges-public-profile.sql` — hidden for non-public profiles (FIX C8).
- `019-organization-ratings-anonymity.sql` — authenticated never reads raw ratings.

**Day 3 — Wire CI.**
- `.github/workflows/pgtap.yml` — runs on every PR that touches `supabase/migrations/**` or `supabase/tests/**`. `supabase/setup-cli@v1` (≥1.11.4), `supabase start`, `supabase test db`.
- Add Splinter job: query Supabase API for advisors, fail on high-severity net-new lint vs main baseline.
- Branch protection: require pgTAP + Splinter checks green before merge to main.

**Day 4 — Python E2E layer (apps/api/tests/).**
- Add 3-client fixture to `conftest.py` (admin / anon / user_client).
- Write 5 pytest attack tests hitting FastAPI endpoints (not DB directly) that use PostgREST under the hood — confirms auth layer + RLS agree.
- Critical test: the ghost-audit §2.1 scenario end-to-end via PATCH /registrations/{id}.

**Day 5 — Checklist audit pass + docs.**
- Walk the 16-point attack-surface checklist against `20260324000015_rls_audit_fixes.sql`. For each gap, open a swarm proposal.
- Verify `FORCE ROW LEVEL SECURITY` on all tables (likely missing — typical Supabase migration style skips FORCE).
- Document in `docs/engineering/skills/RLS-TESTING.md`: "for every new policy, write the allow test AND the deny test before merge. No policy merges without a pgTAP pair."
- Retrospective entry to `docs/DECISIONS.md`.

**Phase 2 (week 2, optional):** author Semgrep custom SQL rules mirroring Splinter lint IDs 0003/0006/0007/0008/0013/0015/0024 for pre-commit speed. Nice-to-have, not blocking.

## Specific test patterns we'd miss without adoption

- **Silent UPDATE denials.** Blocked UPDATE returns zero rows, not an error. Without `is_empty()` on `RETURNING`, a policy that silently drops writes passes every API-layer smoke test while the attack succeeds from the client's view. This is the exact class of the ghost-audit §2.1 miss.
- **WITH CHECK column scope.** `WITH CHECK (status = 'cancelled')` allowed volunteers to also set `coordinator_rating`. Only a test that writes disallowed columns catches it; code review missed it for ~3 weeks.
- **View bypass on PG15+.** `aura_scores_public` uses `security_barrier = TRUE`, which stops predicate leakage but still runs as the view owner. Missing `security_invoker = TRUE` → underlying RLS not re-applied. A pgTAP test querying the view as an unauthorised user catches this in one line.
- **SECURITY DEFINER drift.** Someone adds a SECURITY DEFINER RPC for a new feature and forgets `SET search_path`. No lint will catch it after merge. A pgTAP test that calls the RPC as `authenticated` with a path-poisoning schema surfaces it.
- **`TO authenticated` missing.** A policy intended for signed-in users matches `anon` in edge cases. pgTAP negative test with `clear_authentication()` catches every time.
- **`FORCE ROW LEVEL SECURITY` absence.** Table owner (migrations run as postgres) can SELECT rows that RLS denies to others. Test: `SET ROLE postgres; SELECT ...` as a guarded pgTAP check returns non-empty when FORCE is off.

## Sources

- [Basejump — Testing on Supabase with pgTAP](https://usebasejump.com/blog/testing-on-supabase-with-pgtap)
- [Basejump test helpers (GitHub)](https://github.com/usebasejump/supabase-test-helpers)
- [Supabase — Testing overview](https://supabase.com/docs/guides/local-development/testing/overview)
- [Supabase — Advanced pgTAP testing](https://supabase.com/docs/guides/local-development/testing/pgtap-extended)
- [Supabase — CI testing with GitHub Actions](https://supabase.com/docs/guides/deployment/ci/testing)
- [Makerkit — Supabase RLS best practices (Jan 2026)](https://makerkit.dev/blog/tutorials/supabase-rls-best-practices)
- [Makerkit — Database tests (Next-Supabase-Turbo)](https://makerkit.dev/docs/next-supabase-turbo/development/database-tests)
- [Supashield CLI (GitHub)](https://github.com/Rodrigotari1/supashield)
- [Supabomb (ModernPentest)](https://modernpentest.com/blog/introducing-supabomb)
- [Supabase — Database advisors / Splinter lints](https://supabase.com/docs/guides/database/database-advisors)
- [Supabase RLS testing on Hacker News (Nov 2025)](https://news.ycombinator.com/item?id=45996064)
- [Aaron Blondeau — Playwright RLS tests (2024)](https://aaronblondeau.com/posts/march_2024/supabase_rls_testing/)
- [SupaExplorer — Supabase Security Retro 2025/2026](https://supaexplorer.com/dev-notes/supabase-security-2025-whats-new-and-how-to-stay-secure.html)
- [Bytebase — Postgres RLS footguns](https://www.bytebase.com/blog/postgres-row-level-security-footguns/)

Raw notes: `docs/research/rls-testing/raw.md`.
