# Supabase RLS tests (pgTAP)

Minimum viable test suite. Grows with every new policy.

Research: `docs/research/rls-testing/summary.md`.

## Run locally

```bash
supabase start
supabase test db
```

`supabase test db` executes every `*.test.sql` file in this directory inside a transaction
that is rolled back, so tests do not mutate the local database.

## Adding a new test

1. Name the file `NN_short_description.test.sql` (two-digit prefix = run order).
2. Start with `BEGIN;` and `SELECT plan(<number_of_assertions>);`.
3. Use `pgtap` assertions: `is`, `ok`, `throws_ok`, `lives_ok`, `results_eq`.
4. End with `SELECT * FROM finish();` and `ROLLBACK;`.
5. For RLS tests, switch roles with `SET LOCAL ROLE authenticated` / `anon` and set the
   JWT claim with `SELECT set_config('request.jwt.claim.sub', '<uuid>', true);` —
   or adopt `supabase-test-helpers` (Basejump) when the suite grows past ~10 files.

## Policy pair rule

Every new RLS policy needs BOTH an allow test (happy path) and a deny test
(privilege escalation blocked). No policy PR merges without a pgTAP pair.

## Existing tests

- `01_baseline_rls_enabled.test.sql` — every critical table has `relrowsecurity` AND
  `relforcerowsecurity`. Catches "forgot ENABLE" and "forgot FORCE" regressions.
- `02_registrations_trigger.test.sql` — asserts the 20260415124500 trigger blocks the
  ghost-audit §2.1 injection pattern (volunteer updating `coordinator_rating` under
  cover of a `status='cancelled'` UPDATE).

## CI

`.github/workflows/rls-tests.yml` runs these on every PR that touches
`supabase/migrations/**` or `supabase/tests/**`.
