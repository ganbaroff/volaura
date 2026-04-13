# Postiz Deployment Handoff — Atlas

**Owner:** Atlas (autonomous content agent)
**Reviewer:** CTO
**Status:** Ready to deploy
**Date:** 2026-04-13

---

## Why Postiz (vs. alternatives)

| Tool | License | Self-host? | Cost (5 channels) | Decision |
|------|---------|------------|-------------------|----------|
| **Postiz** | Apache 2.0 | Yes (Docker) | $0 self-hosted, $29/mo SaaS | **CHOSEN** |
| Mixpost | MIT | Yes (Docker) | $0 self-hosted | Slower release cadence, Laravel |
| Buffer | SaaS | No | $15/mo per channel = $75 | Rejected (cost) |
| Hootsuite | SaaS | No | $99/mo / 10 channels | Rejected (cost) |

Postiz wins on three axes: Apache 2.0 (vs. Buffer/Hootsuite SaaS lock-in), 28k+ stars
with active 2026 roadmap (vs. Mixpost's slower release cadence), and a clean REST API
that maps 1-to-1 onto our weekly batch JSON shape.

## Architecture

```
weekly-plan-2026-04-13.md
        │
        ▼ (Atlas reads, generates per-platform copy)
post-payloads.json   ← canonical artifact, one entry per (platform × post)
        │
        ▼ (POST /api/public/v1/posts to local Postiz)
Postiz Docker container (Railway)
        │
        ▼ (Postiz handles OAuth + scheduling + retry)
LinkedIn / X / TikTok / Instagram / YouTube
```

Postiz holds the OAuth tokens. Atlas never sees them. CTO never sees them.

## Deployment plan

### 1. Provision

- [ ] Railway project: `volaura-postiz` (separate from `volaura-api`)
- [ ] Add Postgres plugin (Postiz dependency)
- [ ] Add Redis plugin (Postiz queue)
- [ ] Deploy from `ghcr.io/gitroomhq/postiz-app:latest`
- [ ] Set env vars per Postiz docs:
  - `MAIN_URL=https://postiz.volaura.io`
  - `FRONTEND_URL=https://postiz.volaura.io`
  - `NEXT_PUBLIC_BACKEND_URL=https://postiz.volaura.io/api`
  - `JWT_SECRET=<gen>` (32 random bytes, base64)
  - `DATABASE_URL=<from Railway pg>`
  - `REDIS_URL=<from Railway redis>`
  - `STORAGE_PROVIDER=local` (upgrade to S3 only when assets > 5GB)
- [ ] Domain: `postiz.volaura.io` → Railway CNAME

### 2. Connect platforms (CEO does this — OAuth requires CEO consent)

- [ ] LinkedIn — VOLAURA company page
- [ ] X — `@volaura_io`
- [ ] TikTok — `@volaura.io`
- [ ] Instagram — `@volaura.io`
- [ ] YouTube — VOLAURA channel

CEO logs into Postiz UI → Settings → Integrations → click each platform → grant
OAuth scope. This is one-time. Tokens auto-refresh.

### 3. Issue Atlas an API key

- [ ] In Postiz UI: Settings → API Keys → Generate
- [ ] Save to `apps/api/.env`:
  ```
  POSTIZ_API_URL=https://postiz.volaura.io/api
  POSTIZ_API_KEY=<generated>
  ```
- [ ] Add row to `.env.md`

### 4. Wire Atlas

Atlas's `scripts/atlas/render_weekly.py` will gain a final step:

```python
# pseudocode — implementation lives in packages/swarm/postiz_client.py
client = PostizClient(
    base_url=os.environ["POSTIZ_API_URL"],
    api_key=os.environ["POSTIZ_API_KEY"],
)

for post in weekly_batch:
    payload = {
        "type": "schedule",
        "shortLink": False,
        "posts": [
            {
                "integration": {"id": INTEGRATION_IDS[post.platform]},
                "value": [
                    {
                        "content": post.copy,
                        "image": [{"path": p} for p in post.media_paths],
                    }
                ],
            }
        ],
        "publishDate": post.scheduled_at_iso,
    }
    client.create_post(payload)
```

Idempotency: each post carries a `dedupeKey` derived from `sha256(platform + slug + week)`.
Atlas refuses to re-schedule a key that already exists (read via `GET /api/public/v1/posts?search=<key>`).

## Acceptance criteria (Gherkin)

```gherkin
Scenario: Atlas schedules a weekly batch via Postiz
  Given Postiz is reachable at POSTIZ_API_URL
  And all 5 social integrations show "Connected" in Postiz UI
  And weekly-plan-YYYY-MM-DD.md contains 7 posts
  When Atlas runs `python -m scripts.atlas.render_weekly --week=2026-04-13`
  Then 7 POST requests succeed with 200/201
  And Postiz UI shows 7 posts in "Scheduled" state with correct datetimes
  And no duplicate posts exist for the same dedupeKey

Scenario: Postiz rejects a payload
  Given a malformed post payload (e.g. video > 60s for TikTok)
  When Atlas attempts to schedule it
  Then the response is 4xx with a structured error
  And Atlas writes the failure to memory/atlas/post-failures.md
  And Atlas does NOT mark that row as shipped in the weekly plan
```

## Health check (for swarm)

A new entry in `packages/swarm/tools/deploy_tools.py`:

```python
def check_postiz_health() -> dict:
    """GET /api/health — should return 200 with {"status": "ok"}."""
```

Swarm's daily run will alert if Postiz is down.

## Rollback

If Postiz misbehaves:
1. Set `POSTIZ_API_KEY=""` in Railway → Atlas falls back to writing post payloads
   to `apps/web/public/atlas-pending/` and Telegrams CEO with the queue.
2. CEO can post manually from those JSON files until Postiz is fixed.

## What CTO is NOT touching

- OAuth flows (CEO-only — privacy / account security)
- Posting on CEO's behalf without verified scheduling (every post is queued, not
  fired — CEO can review in Postiz UI before publish window)
- Production secrets in chat — all keys via Railway Secrets / GitHub Actions

## Estimated effort

- Railway provision + domain: 30 min
- OAuth connections (CEO): 20 min
- Atlas client + tests: 4 hours
- End-to-end smoke test: 1 hour

**Total: ~6 hours of CTO + 20 min CEO time. Zero monthly cost ceiling for v1.**
