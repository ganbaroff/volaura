# RLS testing — raw research notes (2026-04-15)

Session: 25 min, ~0 cost (WebSearch only). Atlas. Memory gate passed.

---

## Q1 — pgTAP (SQL-side test framework)

**Status:** Supabase official, supported since 2022, `supabase test db` wraps `pg_prove`. MIT.

### Facts
- pgTAP runs inside transactions → rollback per test. Isolation is free.
- `supabase test db` containerises pg_prove, volume-mounts `supabase/tests/*.{sql,pg}`.
- Test files run in alphabetical order → name setup files `00000-*.sql`.
- Built-in Supabase pgTAP assertions: `policies_are()`, `policy_roles_are()`, `policy_cmd_is()`.

### Production-grade learning resource
- **Basejump test helpers** — https://github.com/usebasejump/supabase-test-helpers — MIT. De facto community standard. Helpers: `tests.create_supabase_user()`, `tests.authenticate_as()`, `tests.clear_authentication()`, `tests.rls_enabled(schema)`. Blog: https://usebasejump.com/blog/testing-on-supabase-with-pgtap.
- **Makerkit** — https://makerkit.dev/blog/tutorials/supabase-rls-best-practices — claims 100+ production deployments using pgTAP in CI. Docs: https://makerkit.dev/docs/next-supabase-turbo/development/database-tests.
- **Supabase advanced guide** — https://supabase.com/docs/guides/local-development/testing/pgtap-extended — multi-user/multi-org RLS examples.
- **Frozen-time example** — https://github.com/usebasejump/supabase-test-helpers/blob/main/supabase/tests/05-frozen-time.sql.

### Key gotcha
- Blocked UPDATE does NOT throw — it silently returns zero rows. Test with `is_empty()` on `RETURNING`, not `throws_ok()`. Blocked INSERT DOES throw (WITH CHECK violation), so `throws_ok()` there.

### CI snippet (copy-paste-adoptable)
```yaml
name: pgTAP
on: [pull_request]
jobs:
  db-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: supabase/setup-cli@v1
        with: { version: latest }
      - run: supabase start
      - run: supabase test db
```

### pgTAP RLS test snippet (adoptable as `supabase/tests/020-registrations-rls.sql`)
```sql
BEGIN;
SELECT plan(4);

SELECT tests.rls_enabled('public', 'registrations');

-- seed as service_role
SELECT tests.create_supabase_user('volunteer_a');
SELECT tests.create_supabase_user('volunteer_b');
INSERT INTO public.registrations (id, event_id, volunteer_id, status)
VALUES (gen_random_uuid(), :event, tests.get_supabase_uid('volunteer_a'), 'confirmed');

SELECT tests.authenticate_as('volunteer_a');

-- allowed: cancel own
SELECT lives_ok($$
  UPDATE public.registrations SET status='cancelled'
  WHERE volunteer_id = auth.uid()
$$, 'volunteer can cancel own row');

-- blocked: self-rate
SELECT is_empty($$
  UPDATE public.registrations
  SET coordinator_rating = 5
  WHERE volunteer_id = auth.uid()
  RETURNING 1
$$, 'volunteer cannot inject coordinator_rating — trigger blocks');

-- blocked: mutate other volunteer
SELECT is_empty($$
  UPDATE public.registrations SET status='cancelled'
  WHERE volunteer_id = tests.get_supabase_uid('volunteer_b')
  RETURNING 1
$$, 'volunteer cannot touch other rows');

SELECT * FROM finish();
ROLLBACK;
```

---

## Q2 — Supabase's own RLS testing SDK

**Conclusion:** There is NO official `@supabase/rls-suite` or `supatest` package. Names hallucinated in blogs. Current official stance = pgTAP via `supabase test db`.

### What actually exists (2026)
- **supabase-test (LaunchQL)** — Show HN Nov 2025. https://news.ycombinator.com/item?id=45996064. Per-test isolated Postgres, auto-rollback, `.setContext()` for auth simulation. Jest/Mocha compatible. Not officially Supabase. JS only.
- **Splinter** — Supabase's official security linter. Built into dashboard Security Advisor. Also exposed via Supabase MCP. Lint IDs worth copying: `0003_auth_rls_initplan`, `0006_multiple_permissive_policies`, `0007_policy_exists_rls_disabled`, `0008_rls_enabled_no_policy`, `0013_rls_disabled_in_public`, `0015_rls_references_user_metadata`, `0024_permissive_rls_policy`.
- **Supabase VDP bounties** — launching 2026. Per-table API access toggle UI coming (dashboard-level GRANT management) per SupaExplorer security retro.

---

## Q3 — @supabase/auth-js test helpers for simulating users

No dedicated `@supabase/auth-js/testing` module. Pattern is manual:

```js
// create user via admin client, sign in via anon client
const { data: { user } } = await admin.auth.admin.createUser({
  email, password, email_confirm: true
});
const anon = createClient(URL, ANON_KEY);
await anon.auth.signInWithPassword({ email, password });
// anon now has JWT → PostgREST switches to authenticated role → auth.uid() = user.id
```

For raw SQL tests: Basejump's `tests.authenticate_as('name')` sets `request.jwt.claims` + role via `SET LOCAL`.

---

## Q4 — Python-side RLS testing with supabase-py

**Pattern confirmed:** 3-client fixture.

```python
# apps/api/tests/conftest.py additions
import os, pytest
from supabase import create_client, Client

URL = os.environ["SUPABASE_URL"]
ANON = os.environ["SUPABASE_ANON_KEY"]
SERVICE = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

@pytest.fixture(scope="session")
def admin_client() -> Client:
    return create_client(URL, SERVICE)  # bypasses RLS

@pytest.fixture
def anon_client() -> Client:
    return create_client(URL, ANON)     # auth.uid() IS NULL

@pytest.fixture
def user_client(admin_client):
    email = f"test+{os.urandom(4).hex()}@volaura.test"
    pw = "Test!" + os.urandom(6).hex()
    created = admin_client.auth.admin.create_user({
        "email": email, "password": pw, "email_confirm": True
    })
    uid = created.user.id
    c = create_client(URL, ANON)
    sess = c.auth.sign_in_with_password({"email": email, "password": pw})
    c.postgrest.auth(sess.session.access_token)
    yield c, uid
    admin_client.auth.admin.delete_user(uid)
```

**Test of today's trigger:**
```python
def test_volunteer_cannot_inject_coordinator_rating(admin_client, user_client):
    client, uid = user_client
    reg = admin_client.table("registrations").insert({
        "event_id": KNOWN_EVENT, "volunteer_id": uid, "status": "confirmed"
    }).execute().data[0]

    # Attack: direct PostgREST UPDATE setting coordinator_rating
    with pytest.raises(Exception) as exc:
        client.table("registrations").update({
            "status": "cancelled", "coordinator_rating": 5,
            "coordinator_feedback": "10/10"
        }).eq("id", reg["id"]).execute()
    assert "42501" in str(exc.value) or "Blocked column change" in str(exc.value)
```

**Gotcha:** application-level tests cannot use Postgres transaction isolation → use per-test unique user IDs + teardown via admin. Slower than pgTAP. Use both: pgTAP for policy unit tests, pytest for API-layer end-to-end.

---

## Q5 — Security audit / scanner tools

| Tool | URL | Cost | Fit for VOLAURA |
|------|-----|------|----------------|
| **Splinter** (official) | built into Supabase + MCP | Free | Baseline. Run every migration. Covers 0003/0006/0007/0008/0013/0015/0024. |
| **Supashield** | https://github.com/Rodrigotari1/supashield | OSS (MIT-ish, check) | CLI: `audit`, `lint`, `coverage`, `test`, `test-storage`. Uses rolled-back txns. `--json` for CI. |
| **Supabomb** | https://modernpentest.com/blog/introducing-supabomb | OSS | Pentest-style. Autodetects creds from frontend JS. Too aggressive for local CI; good for pre-launch red-team. |
| **SupaSec** | — | OSS | Uses `Prefer: tx=rollback` header to dry-run exploits in ms. Ghost Auth exploitation, pagination bypass. |
| **supabase-rls-checker** (Chrome) | https://github.com/hand-dot/supabase-rls-checker | Free | Dev-time sanity, not CI. |
| **SupaExplorer** | https://supaexplorer.com/ | Freemium | Chrome extension + web audit. Also API-key leak scanner. |
| **Semgrep custom** | self-author | OSS | Viable for SQL pattern lint (CREATE TABLE without ENABLE RLS, `FOR ALL`, unwrapped `auth.uid()`, raw_user_meta_data refs). No public ruleset found. |
| **pg_audit** | https://github.com/pgaudit/pgaudit | OSS | Logging, not policy coverage. Different layer. |

**No `pgsec`/`pg_audit` tool with policy-coverage reporting exists OSS.** Splinter + Supashield cover that gap.

---

## Q6 — Attack-surface checklist for Supabase RLS (concrete)

1. **Every `public.*` table has `ALTER TABLE … ENABLE ROW LEVEL SECURITY` + `FORCE`** — owner bypass otherwise.
2. **No `FOR ALL` policies** — split into SELECT/INSERT/UPDATE/DELETE. Makes intent auditable.
3. **Every UPDATE policy has BOTH `USING` and `WITH CHECK`.** `USING` alone lets an update change the row to values that wouldn't pass `USING` on re-read.
4. **WITH CHECK is column-inclusive.** Postgres cannot express "NEW = OLD except for column X" natively → if multi-column restriction needed, use BEFORE UPDATE trigger with `IS DISTINCT FROM` per column (pattern already landed in `20260415124500`). Generalise to every "partial update" policy.
5. **SECURITY DEFINER RPCs must `SET search_path = public, pg_temp`** — else schema-shadowing attack.
6. **SECURITY DEFINER RPCs that wrap RLS MUST re-check `auth.uid()`** inside — they run as definer and bypass RLS otherwise. Document which RPCs are intentional bypasses (e.g. `upsert_aura_score`, `match_volunteers`) and test them.
7. **VIEW created pre-PG15 or without `security_invoker = true`** — RLS bypass. Check `aura_scores_public`, `questions_safe`. (VOLAURA uses `security_barrier`; confirm `security_invoker` too on PG17.)
8. **`auth.uid() = owner_id` where `owner_id` is NULLABLE** — `NULL = NULL` is NULL, not TRUE, so fine for denial, but `auth.uid() IS NULL AND owner_id IS NULL` is the sneaky case when a row has `owner_id = NULL` and an unauthenticated client hits it.
9. **JWT claim sourcing** — policies referencing `raw_user_meta_data` or `user_metadata` are user-mutable → privilege escalation. Use `raw_app_meta_data` only. Splinter lint 0015.
10. **Unwrapped `auth.uid()`** — `auth.uid() = x` is evaluated per row. Always write `(SELECT auth.uid()) = x` — Postgres caches as initPlan. Splinter lint 0003.
11. **Multiple permissive policies on same table+cmd** — policies OR together; one permissive `TRUE` dominates all others. Splinter lint 0006. Example in this codebase (already fixed C8).
12. **Missing index on column in policy predicate** — RLS adds an implicit WHERE; un-indexed = seq scan per query.
13. **BYPASSRLS role attribute** — never grant to app roles.
14. **Trigger-based enforcement can be disabled by superuser.** Document in migration that disabling `enforce_volunteer_update_scope` is a security event. Monitor via `pg_trigger`.
15. **Postgres 17 `row_security` is unchanged from 15/16 at spec level** — no new escape hatches; continue using FORCE + security_invoker views. PG18 (Sept 2025) also no RLS overhaul.
16. **Service role client in frontend code** — most common AI-codegen footgun (Bolt/Lovable/Cursor). Grep codebase: `SUPABASE_SERVICE_ROLE_KEY` must only appear in `apps/api/**` and CI.
17. **`TO authenticated` missing** — policies without explicit role target can match `anon` in unexpected contexts.

---

## Q7 — Complementary OSS tools

- **TruffleHog** — https://github.com/trufflesecurity/trufflehog — secret scanning. Catches service_role leaked in frontend bundle. CI job on every PR. Complements RLS testing but orthogonal.
- **Semgrep** — custom SQL rules targeting `supabase/migrations/**/*.sql`. No public ruleset; author ~10 rules matching Splinter lint IDs. 1-day effort.
- **sqlfluff** — not security but enforces migration formatting → makes RLS policies greppable.
- **Supabase MCP + AI workflows** — https://docs.continue.dev/guides/supabase-mcp-database-workflow — useful for "audit all tables" one-shots, not CI.

---

## Q8 — Production case studies 2024-2026

- **170+ Lovable-built apps exposed Jan 2025** — mass RLS-disabled incident. Post: https://securifyai.co/blog/how-to-test-supabase-row-level-security-using-an-open-source-scanner/. Not a single-company postmortem, class-wide failure.
- **83% of exposed Supabase DBs involve RLS misconfigurations** (Supashield author's dataset).
- **13k-user leak** — DEV post (oscarv) describes an unnamed app leak due to broken RLS.
- **Makerkit** — best *publicly-published* RLS test suite across 100+ deployments. https://makerkit.dev/docs/next-supabase-turbo/development/database-tests. Closest to "battle-tested open reference".
- **Aaron Blondeau's blog** — https://aaronblondeau.com/posts/march_2024/supabase_rls_testing/ — Playwright-based RLS testing using real JS client. Useful complement to pgTAP.
- **Bolt.new / Cursor / v0** — repeatedly cited as generating `USING (true)` policies that pass tests but leak all rows. Implication: any AI-assisted migration in VOLAURA must go through Splinter + pgTAP before merge.

**No Resend or Bolt.new *first-party* postmortem found.** Class-level evidence is strong enough.

---

## Integration cost estimate for VOLAURA

| Item | Cost |
|------|------|
| Install Basejump helpers | 10 min |
| Write first 10 pgTAP tests (covering today's trigger + C1–C8 from 20260324000015) | 4 h |
| Wire `supabase test db` into GitHub Actions | 30 min |
| Add Splinter check via Supabase MCP in CI | 45 min |
| Author 3-client pytest fixture | 1 h |
| Write 5 Python E2E RLS tests | 2 h |
| Author 5 Semgrep SQL rules | 1 d (Phase 2) |

Phase 1 (pgTAP + Splinter + 3 Python tests): **~1 week of a single engineer**. No external cost.

---

## Open questions worth follow-up

- Does Supabase CLI on GitHub Actions boot fast enough in VOLAURA's existing pytest workflow, or does it need a parallel job?
- Local dev: does `supabase start` conflict with the existing docker-compose used by apps/api tests?
- Do any existing SECURITY DEFINER RPCs (`upsert_aura_score`, `match_volunteers`, new `_enforce_volunteer_update_scope`) lack `SET search_path`? Quick grep in follow-up sprint.
