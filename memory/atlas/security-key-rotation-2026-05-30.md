---
type: atlas
status: active
created: 2026-05-30
updated: 2026-05-30
tags: [type/atlas, area/security, status/active]
---

# Security Key Rotation — VOLAURA Bill of Materials, 2026-05-30

**Trigger.** 3 API keys leaked to chat 2026-05-10/11 (NVIDIA `nvapi-T7VOY...`, GITHUB_PAT, SUPABASE_SERVICE_ROLE_KEY). 19 days unrotated. Each day expands the exposure.

**Author.** Atlas/CLI-side (Claude Opus 4.7), 2026-05-30 00:52 AST. Orchestrator-side correction in `orchestrator-loop.md` iter ~7 caught that the «30 min, 3 clicks» estimate was wrong by 6×. This document is the correct map.

## Consumers (main tree, worktrees excluded, verified via grep this turn)

### NVIDIA_API_KEY — 30 files

- `.claude/hooks/external-verdict-dispatcher.sh`
- GitHub workflows (7): `atlas-proactive.yml`, `inbox-consumer.yml`, `post-deploy-agent.yml`, `swarm-daily.yml`, `swarm-distill-weekly.yml`, `telegram-execute.yml`
- Backend routers (4): `apps/api/app/routers/{atlas_consult,aura,health,telegram_webhook}.py`
- Swarm core (8 py): `packages/swarm/archive/atlas_proactive.py`, `archive/board_heavy_run.py`, `autonomous_run.py`, `coordinator.py`, `judge.py`, `providers/litellm_adapter.py`, `tools/llm_router.py`
- Scripts (8): `atlas_swarm_daemon.py`, `gemma4_brain.py`, `litellm_smoke.py`, `pre-commit-secret-scan.sh`, `runtime_proof_provider_chain.py`, `swarm_agent.py`, `swarm_constitutional_vote.py`, `swarm_self_setup.py`, `swarm_self_setup_v2.py`
- Tests (2): `tests/test_gemma4_brain_provider_chain.py`, `test_litellm_adapter.py`, `apps/api/tests/test_model_router.py`

### SUPABASE_SERVICE_KEY + SUPABASE_SERVICE_ROLE_KEY — 50 files

**TRAP:** two different variable names in the codebase. Rotate one, miss the other = half the swarm + crons silently fail.

- GitHub workflows (18): `analytics-retention`, `assessment-completion-reconciler`, `atlas-content`, `atlas-ecosystem-snapshot`, `atlas-obligation-nag`, `atlas-proactive`, `aura-decay`, `aura-reconciler`, `brandedby-refresh`, `ci`, `cleanup-test-users`, `e2e`, `ecosystem-consumer`, `error-watcher`, `inbox-sync`, `match-checker`, `post-deploy-agent`, `swarm-daily`
- Backend (3): `apps/api/app/config.py`, `main.py`, `services/match_checker.py`
- Tests (4 backend): `test_e2e_assessment`, `test_match_checker`, `test_middleware`, `test_rls_audit`
- Web E2E (2): `apps/web/e2e/auth-product-sprint.spec.ts`, `product-sprint.spec.ts`
- Swarm (5): `archive/jarvis_daemon`, `archive/simulate_users`, `archive/zeus_content_run`, `atlas_content_run`, `autonomous_run`
- Scripts (8+): `atlas_ecosystem_snapshot`, `atlas_obligation_nag`, `audit_assessment_state`, `audit_dif_bias`, `aura_decay`, `behavioral_sim`, `check_rls_live`, `cleanup_smoke_test_users` (plus more — grep cut at 40 lines)

### GH_PAT_ACTIONS + GITHUB_PAT + GH_TOKEN — 10 files

**NAME-MATCH UNCERTAINTY:** chat leak said «GITHUB_PAT». Codebase uses `GH_PAT_ACTIONS`. Likely same key, alias-renamed. Confirm by checking the leaked prefix vs `gh secret list --repo ganbaroff/volaura`.

- Workflows (4): `atlas-watchdog`, `fix-of-fix-detector`, `swarm-proposal-cards`, `telegram-execute`
- Backend (4): `apps/api/app/routers/telegram_webhook.py`, `webhooks_sentry.py`, `services/atlas_tools.py`, `tests/test_telegram_action.py`
- Swarm (1): `packages/swarm/telegram_ambassador.py`
- Scripts (1): `scripts/push_gh_secret.py`

## Storage layers (where rotated value must reach)

| Layer | Update method | Refs touched | CEO clicks needed |
|-------|--------------|--------------|-------------------|
| GitHub Actions repo secrets | `gh secret set NAME -b "VALUE" --repo ganbaroff/volaura` | 29 workflow runs | 0 (Atlas runs gh CLI) |
| Railway env vars (apps/api Prod) | `railway variables set NAME=VALUE` OR dashboard | apps/api runtime | 0 (Atlas runs railway CLI) — IF railway-cli auth still valid |
| GCP VM `/opt/volaura/.env` | SSH + edit + systemctl restart | swarm daemon + brain | 0 (Atlas runs ssh) — IF SSH key `~/.ssh/volaura_swarm` works |
| Supabase edge function secrets | `supabase secrets set NAME=VALUE --project-ref XXX` per fn | 2 fns: send-notification, telegram-webhook | 0 (Atlas runs supabase CLI) — IF supabase auth valid |
| Local `apps/api/.env` (CEO machine) | Manual file edit | dev runtime | CEO writes new values here ONCE |

## CEO clicks (irreversible, in dashboards with 2FA)

1. **NVIDIA NGC** → https://ngc.nvidia.com/setup/api-key → «Generate new API key» → COPY → paste into local `C:\Projects\VOLAURA\apps\api\.env` as `NVIDIA_API_KEY=...`
2. **GitHub Personal Access Tokens** → https://github.com/settings/tokens → find token with leaked prefix → «Regenerate token» (NOT delete; regenerate keeps grants) → COPY → paste into `apps/api/.env` as `GH_PAT_ACTIONS=...`
3. **Supabase Project Settings** → https://supabase.com/dashboard/project/[ref]/settings/api → «Reset service_role secret» → COPY → paste into `apps/api/.env` as `SUPABASE_SERVICE_KEY=...` AND `SUPABASE_SERVICE_ROLE_KEY=...` (both names, same value)

Total CEO time: ~10 min if 2FA is fast.

## Atlas propagation script (NEW values flow CEO machine → all storage, never through chat)

After CEO has the 3 new values in local `apps/api/.env`, Atlas runs (`scripts/rotate_keys_2026-05-30.sh`, to be authored):

```bash
#!/usr/bin/env bash
set -e
source apps/api/.env
# GitHub
gh secret set NVIDIA_API_KEY -b "$NVIDIA_API_KEY" --repo ganbaroff/volaura
gh secret set GH_PAT_ACTIONS -b "$GH_PAT_ACTIONS" --repo ganbaroff/volaura
gh secret set SUPABASE_SERVICE_KEY -b "$SUPABASE_SERVICE_KEY" --repo ganbaroff/volaura
gh secret set SUPABASE_SERVICE_ROLE_KEY -b "$SUPABASE_SERVICE_ROLE_KEY" --repo ganbaroff/volaura
# Railway (apps/api Production)
railway variables set NVIDIA_API_KEY="$NVIDIA_API_KEY" GH_PAT_ACTIONS="$GH_PAT_ACTIONS" SUPABASE_SERVICE_KEY="$SUPABASE_SERVICE_KEY" SUPABASE_SERVICE_ROLE_KEY="$SUPABASE_SERVICE_ROLE_KEY"
# Supabase edge functions
supabase secrets set --project-ref XXX SUPABASE_SERVICE_ROLE_KEY="$SUPABASE_SERVICE_ROLE_KEY"
# GCP VM /opt/volaura/.env
ssh -i ~/.ssh/volaura_swarm yusif_ganbarov@104.154.132.12 "cd /opt/volaura && sed -i.bak -e 's|^NVIDIA_API_KEY=.*|NVIDIA_API_KEY=$NVIDIA_API_KEY|' -e 's|^GH_PAT_ACTIONS=.*|GH_PAT_ACTIONS=$GH_PAT_ACTIONS|' -e 's|^SUPABASE_SERVICE_KEY=.*|SUPABASE_SERVICE_KEY=$SUPABASE_SERVICE_KEY|' -e 's|^SUPABASE_SERVICE_ROLE_KEY=.*|SUPABASE_SERVICE_ROLE_KEY=$SUPABASE_SERVICE_ROLE_KEY|' .env && bash infra/deploy.sh && pkill -f atlas_swarm_daemon && setsid nohup python3 scripts/atlas_swarm_daemon.py > /dev/null 2>&1 &"
```

Values stay on local disk. Chat sees nothing.

## Verification post-rotation (close the loop)

1. **GitHub workflow smoke**: trigger `swarm-daily.yml` via `gh workflow run` and verify it pulls NVIDIA + Supabase keys correctly (job log shows non-401, non-403).
2. **Railway prod healthcheck**: `curl https://volauraapi-production.up.railway.app/health` — expect 200 + key-dependent fields populated.
3. **GCP VM daemon**: SSH + `ps -ef | grep atlas_swarm_daemon` — expect new PID + recent log lines without «401 unauthorized» from providers.
4. **Edge function**: `curl -X POST https://[ref].supabase.co/functions/v1/send-notification -H "Authorization: Bearer [new key]" -d '{...}'` — expect 200.
5. **Old key revocation confirm**: try old key against any provider → expect 401. If still 200 = provider's revoke didn't propagate yet, wait 5 min and retry.

## Risk if delayed further

- Each day of delay = leaked key exposure window grows
- NVIDIA: paid credits could be drained by anyone with chat transcript
- GH_PAT: anyone with chat could push commits, merge PRs, change workflows
- Supabase service_role: full RLS bypass = read/write any user's PII; possible GDPR breach if exfiltrated

## Estimate (corrected from «30 min»)

- CEO clicks in 3 dashboards: ~10 min
- CEO pastes 3 new values into `apps/api/.env`: ~2 min
- Atlas runs propagation script (5 storage layers): ~5 min
- Verification (5 smoke calls): ~10 min
- **Total wall-clock**: ~30 min CEO-time + ~15 min Atlas-time, NOT including any cascading workflow re-runs.

## Open questions before execution

1. Is Railway CLI still authenticated on this machine? `railway whoami` returns OK or login-prompt? — UNVERIFIED THIS TURN.
2. Is Supabase CLI still authenticated? `supabase projects list` returns OK or login? — UNVERIFIED.
3. What is the Supabase project-ref (`XXX` placeholder above)? — needs lookup.
4. Does SSH to `yusif_ganbarov@104.154.132.12` still work with `~/.ssh/volaura_swarm`? — UNVERIFIED.
5. Is the leaked `GITHUB_PAT` in chat literally named `GITHUB_PAT` or is it the value of `GH_PAT_ACTIONS`? — needs cross-reference against chat transcript 2026-05-10/11.

These 5 must be answered before any actual rotation run. Each is a single CLI call.

— Atlas/CLI-side, 2026-05-30 00:52 AST
