# INC-019 — Railway backend frozen 4 days, 18 deploys silently failed

**Severity:** P0 (silent loss)
**Detected:** 2026-04-25 ~21:00 Baku, during BrandedBy refresh telemetry verification
**Root cause landed:** 2026-04-25 22:42 Baku, commit `986f7cf`
**Author:** Atlas (Code instance, this session)
**Class:** silent infrastructure failure — production divergence with no surfaced error

## Symptom

BrandedBy refresh worker had been merged + migration applied to prod hours earlier (2b01d09 → 4eabd8e → 1c546d7). Smoke run via `workflow_dispatch` showed `provider=vertex, latency_ms=18986, prompt_len=1021` in GitHub Actions logs. But Railway deploy logs for the most recent SHA showed nothing the API was actually serving. Health probe `/api/v1/health` returned old build SHA. Discrepancy.

## Diagnostic path

1. Pulled Railway deployments via GraphQL using `RAILWAY_API_TOKEN`:
   ```graphql
   query { project(id: "<id>") { services { edges { node { deployments(first: 30) { edges { node { id status meta createdAt } } } } } } } }
   ```
   Output: 18 of last 18 deployments since 2026-04-21 status=`FAILED`. Last `SUCCESS` was on `917d3a2`, 4 days prior.

2. Pulled `buildLogs` and `deploymentLogs` for one FAILED deploy. Build phase was clean — Docker image built fine. Deploy phase showed Python traceback at container startup:
   ```
   File "/app/app/routers/atlas_consult.py", line N, in <module>
     _REPO_ROOT = Path(__file__).resolve().parents[4]
   IndexError: tuple index out of range
   ```

3. Railway runs the API in a Docker container where the file path is `/app/app/routers/atlas_consult.py`. `Path(__file__).resolve()` gives `/app/app/routers/atlas_consult.py`. `.parents` is a sequence of length 4 (`/app/app/routers`, `/app/app`, `/app`, `/`). `.parents[4]` raises `IndexError` because the tree has only 4 ancestors. Locally on Windows the file lives much deeper in the path, so `.parents[4]` resolves fine. **The bug only manifests inside the Docker layout used by Railway.** Local tests, local dev server, and CI all passed because none of them mirror the Docker mount layout.

4. The IndexError fired at module-import time, so the FastAPI app never reached `Uvicorn started` — Railway's healthcheck never got a 200, deploy was marked FAILED, container was rolled back to the last successful image. Railway's UI showed the deploy as failed but did not surface a Slack/email alert because we have no failure-routing wired. Each new commit triggered a fresh deploy that failed in exactly the same place.

5. Vercel deploys for the frontend were independent and continued shipping new builds, masking the issue: prod URL felt alive (frontend was fresh) while every backend commit since 2026-04-21 was effectively a no-op behind a stale container.

## Fix

Three files used the same pattern. All wrapped in `try/except IndexError` with a sensible default:

- `apps/api/app/routers/atlas_consult.py` — commit `c062828`
- `apps/api/app/services/atlas_voice.py` — commit `986f7cf`
- `apps/api/app/routers/telegram_webhook.py` — commit `986f7cf`

```python
try:
    _REPO_ROOT = Path(__file__).resolve().parents[4]
except IndexError:
    # Docker container layout has fewer parents — repo-root climb is local-only.
    _REPO_ROOT = Path("/app").resolve()
```

After `986f7cf` landed, healthcheck went green on the next deploy. Subsequent commits (`b1b5465` ecosystem DLQ, `372e67b` watcher 4th signal, `1482772` watcher emit FK fix) all deployed clean and Railway is back in sync.

## Why this was silent for 4 days

1. **No deploy-failure alert routing.** Railway shows red in the UI; no Slack hook, no email, no PagerDuty. Atlas-Code looked at GitHub Actions success and Vercel success and assumed the chain was green.
2. **Healthcheck not actually checked from external monitor.** We have a `/api/v1/health` endpoint but no Uptime Robot / Better Stack / Railway native alert that pings it and fires on regression. Railway's own healthcheck stops the deploy but doesn't escalate.
3. **CI green, prod broken.** Tests run in pytest under Linux but in a `pytest` working directory, not the `/app` Docker mount. The `.parents[4]` walk gives a different absolute path under pytest than under Docker startup. CI was structurally blind to this class of bug.
4. **Frontend masking.** Vercel's independent pipeline keeps the user-visible surface fresh, hiding backend staleness from "smoke test by visiting the URL" verification.
5. **No build-SHA assertion in regression pack.** The post-thaw regression pack was rebuilt from scratch in this session (`memory/atlas/wuf13-regression-pack-2026-04-25.md`); prior runs assumed Railway was tracking main. They were wrong.

## Permanent mitigations

| # | Action | Status |
|---|--------|--------|
| 1 | Wrap every `Path(__file__).resolve().parents[N]` with `try/except IndexError` and a Docker-aware fallback | Done in 3 files (c062828, 986f7cf). Sweep remaining files: open task. |
| 2 | Add Railway deploy-failure → Telegram alert via `TELEGRAM_BOT_TOKEN` already in `.env` | Open. ~30 min work. |
| 3 | Add `/api/v1/health` external probe (Better Stack free tier) firing every 1 min, alert on 2 consecutive fails | Open. ~10 min setup. |
| 4 | Add SHA assertion to regression pack: `curl https://volauraapi-production.up.railway.app/api/v1/health` must return `git_sha` matching the latest `origin/main` commit | Open. Add to `wuf13-regression-pack` doc. |
| 5 | Add `pytest` test that runs the import chain under a simulated `/app` Docker layout via `monkeypatch` on `__file__` resolution | Open. Class of bug needs CI coverage. |
| 6 | Add this incident to error_watcher as a 5th signal: "Railway last deploy status != SUCCESS for >2h" | Open. ~50 lines code + tests. |

## Lessons

**Symptom:** "I declared backend healthy because GitHub Actions and Vercel were green" — proxy signals, not the actual signal.

**Pathway:** Default Anthropic-trained chain ("CI passes + frontend deploys = production healthy") missed the middle hop because the middle hop has its own pipeline with its own failure mode and no routing.

**Root-cause fix (per atlas-operating-principles.md):** the lesson is not "I'll be more careful". The lesson is mitigation #4 — add SHA assertion to regression pack so that future Atlas instances cannot declare "backend healthy" without a tool-call receipt showing the deployed SHA matches the desired SHA. Structural, not behavioral.

**Class:** matches Class 8 (proxy-signal-as-truth) from `lessons.md`. Logged into incidents library as INC-019. Cross-reference from `lessons.md` next time it gets edited.

## Cross-references

- Commits: `c062828`, `986f7cf`
- Related observability work this session: `b1b5465` (ecosystem DLQ — same class of silent loss), `372e67b` + `1482772` (watcher emit FK fix — also silent since day one)
- Regression pack: `memory/atlas/wuf13-regression-pack-2026-04-25.md` (built post-thaw, 9-of-9 green on `1482772`)
- Observability state: `memory/atlas/wuf13-observability-state-2026-04-25.md`
