# VOLAURA Web Checker — MVP Phase 1

Batch Playwright-based page tester for E2E audits. Single-threaded, deploys to Railway.

## Quick Start (Local)

```bash
cd tools/volaura_web_checker
pip install -r requirements.txt
python -m playwright install  # Download browser binaries
python app.py
```

Server runs on `http://localhost:8080`

## Test the Service

```bash
curl -X POST http://localhost:8080/check \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      {
        "url": "https://volaura.app/az/dashboard",
        "flow": "dashboard-load",
        "assertions": [
          {"selector": "text=İdarəetmə paneli", "expect": "paneli"}
        ]
      }
    ],
    "return_screenshots": true
  }'
```

## Deploy to Railway

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Authenticate
railway login

# 3. Create new Railway project
railway init

# 4. Deploy
railway up
```

Railway will:
- Detect Python + Procfile
- Install dependencies from requirements.txt
- Run: `python -m playwright install && gunicorn ...`
- Expose service at `https://volaura-web-checker-*.railway.app`

## Architecture

**Single-threaded MVP:**
- One Playwright browser instance (long-lived)
- Per-request page context (closed after check)
- Screenshots on failure (base64 encoded)
- JSON response: `{results: [...], summary: {total, passed, failed}}`

**Scaling (Phase 2):**
- Will migrate to Node.js + browser pool (4-8 concurrent contexts)
- Cloud Run deployment
- Persists current JSON contract

## Integration with Claude

Claude calls this tool via tools API with schema:

```json
{
  "name": "volaura_web_checker",
  "input_schema": {
    "tasks": [{"url": "...", "flow": "...", "assertions": [...]}],
    "return_screenshots": true
  }
}
```

Claude batches related checks into single call → tool returns JSON → Claude analyzes and reports.

## Known Limitations (Phase 1)

- ⚠️ Single-threaded: 50 pages ≈ 2.5 min execution (acceptable for audit)
- ⚠️ Browser not released between requests (no pooling)
- ⚠️ Railway process restarts daily (mitigates memory leaks)
- ✅ Works offline (no API dependencies, pure browser automation)
- ✅ Bypasses CORS (unlike XHR/Fetch)

## Phase 2 (Week 1)

- Node.js + Playwright pool
- Cloud Run (auto-scaling)
- Persistent state (Redis for task queues)
- MCP integration
