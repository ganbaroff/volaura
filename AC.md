## Acceptance Criteria

- [ ] analytics.py /event uses SupabaseUser (not SupabaseAdmin) — RLS enforced
- [ ] subscription.py GET /status uses SupabaseUser — user reads own profile via RLS
- [ ] subscription.py POST /create-checkout retains SupabaseAdmin — auth.admin + payment writes
- [ ] Webhook handlers retain raw acreate_client — no JWT context
- [ ] pnpm build (frontend) passes — no regressions
