# CLI
git: /mingw64/bin/git — git version 2.53.0.windows.1
gh: /c/Program Files/GitHub CLI/gh — gh version 2.88.1 (2026-03-12)
vercel: /c/Users/user/AppData/Roaming/npm/vercel — Vercel CLI 50.35.0
npm: /c/Program Files/nodejs/npm — npm warn Unknown project config "shamefully-hoist". This will stop working in the next major version of npm.
node: /c/Program Files/nodejs/node — v24.14.0
python: /c/Python314/python — Python 3.14.3
python3: /c/Users/user/AppData/Local/Microsoft/WindowsApps/python3 — Python 3.14.3
railway: /c/Users/user/AppData/Roaming/npm/railway — railway 4.33.0
pnpm: /c/Users/user/AppData/Roaming/npm/pnpm — 10.32.1

# Vercel CLI session
ganbaroff

# Vercel teams accessible via CLI
Fetching teams
Fetching user information

  id                      Team name                
√ ganbaroffs-projects     ganbaroff's projects     

# .env keys (apps/api)
AI_GATEWAY_API_KEY
ANTHROPIC_API_KEY
API_PORT
APP_ENV
APP_URL
AZURE_CLIENT_ID
AZURE_CLIENT_SECRET
CEREBRAS_API_KEY
DEEPSEEK_API_KEY
DID_API_KEY
DODO_PAYMENTS_API_KEY
E2E_TEST_SECRET
EXTERNAL_BRIDGE_SECRET
FAL_API_KEY
FIREBASE_MINDSHIFT_CREDENTIALS_B64
GCP_PROJECT_ID
GCP_SERVICE_ACCOUNT_EMAIL
GCP_SERVICE_ACCOUNT_JSON
GEMINI_API_KEY
GH_PAT_ACTIONS
GITHUB_OAUTH_CLIENT_ID
GITHUB_OAUTH_CLIENT_SECRET
GOOGLE_OAUTH_CLIENT_ID
GOOGLE_OAUTH_CLIENT_SECRET
GROQ_API_KEY
LANGFUSE_HOST
LANGFUSE_PUBLIC_KEY
LANGFUSE_SECRET_KEY
MEM0_API_KEY
NVIDIA_API_KEY
OPENAI_API_KEY
OPENROUTER_API_KEY
PAYMENT_ENABLED
RAILWAY_API_TOKEN
SENTRY_AUTH_TOKEN
SENTRY_DSN
STRIPE_PRICE_ID
STRIPE_PUBLISHABLE_KEY
STRIPE_RESTRICTED_KEY_TEST
STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET
SUPABASE_ANON_KEY
SUPABASE_ANON_KEY_MINDSHIFT
SUPABASE_JWT_SECRET
SUPABASE_PUBLISHABLE_KEY
SUPABASE_SERVICE_KEY
SUPABASE_SERVICE_KEY_MINDSHIFT
SUPABASE_URL
SUPABASE_URL_MINDSHIFT
SUPERNOVA_AUTH_TOKEN
TAVILY_API_KEY
TELEGRAM_BOT_TOKEN
TELEGRAM_CEO_CHAT_ID
TELEGRAM_WEBHOOK_SECRET
VERTEX_API_KEY

# MCP servers loaded in this session
- supabase (mcp__supabase__*) — full read/write to all projects via service-role
- vercel (mcp__a4a42010-...) — limited to team_NEzhIksuRth4RAPXQGI6lz1T (yusifg27 mindshift family)
- figma (mcp__3183acdc-..., mcp__Figma__*) — design surface
- sentry (mcp__e31ae178-...) — full access to volaura org via SENTRY_AUTH_TOKEN equivalent
- playwright (mcp__playwright__*) — browser automation
- gmail (mcp__66b57eaf-...)
- drive (mcp__ae518577-...)
- calendar (mcp__ee2648ee-...)
- ccd_session, ccd_directory — session mgmt
- mem0 — persistent memory
- claude_in_chrome, claude_preview — UI testing
- mcp-registry — list other connectors
- posthog (mcp__ffbe0108-...) — analytics admin
- scheduled-tasks — cron management

# API tokens in apps/api/.env (working/verified)
- RAILWAY_API_TOKEN — project-scoped, GraphQL works for deploys/variables
- SUPABASE_SERVICE_KEY — full DB write via PostgREST
- SUPABASE_SERVICE_KEY_MINDSHIFT — full MindShift DB write
- SENTRY_AUTH_TOKEN — Sentry API events/projects read
- LANGFUSE_PUBLIC_KEY + LANGFUSE_SECRET_KEY — verified, project "VOLAURA" exists, 0 traces (host disabled in app)
- ANTHROPIC_API_KEY, GEMINI_API_KEY, GROQ_API_KEY, OPENAI_API_KEY, VERTEX_API_KEY, NVIDIA_API_KEY, OPENROUTER_API_KEY, DEEPSEEK_API_KEY, CEREBRAS_API_KEY — LLM providers
- AI_GATEWAY_API_KEY — Vercel AI Gateway, blocked on billing
- AZURE_CLIENT_ID + SECRET, GCP_SERVICE_ACCOUNT_JSON, FIREBASE_MINDSHIFT_CREDENTIALS_B64 — cloud creds
- GH_PAT_ACTIONS — GitHub Actions
- TELEGRAM_BOT_TOKEN, TELEGRAM_CEO_CHAT_ID, TELEGRAM_WEBHOOK_SECRET
- STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_PUBLISHABLE_KEY, STRIPE_PRICE_ID, STRIPE_RESTRICTED_KEY_TEST, DODO_PAYMENTS_API_KEY
- GITHUB_OAUTH_CLIENT_ID + SECRET, GOOGLE_OAUTH_CLIENT_ID + SECRET
- DID_API_KEY, FAL_API_KEY, TAVILY_API_KEY, MEM0_API_KEY, SUPERNOVA_AUTH_TOKEN
- SUPABASE_JWT_SECRET — EMPTY (cannot mint custom user JWTs, use admin generate_link instead)

# Tokens that DON'T work for intended use
- vck_5em... — Vercel limited (user-info only)
- vck_2e8s... — Vercel limited (user-info only)
- AI_GATEWAY_API_KEY (vck_6gNO...) — billing block

# Vercel CLI session active as ganbaroff (ganbarov.y@gmail.com)
- Has access to ganbaroffs-projects team (volaura, volaura-api, tg-mini, whisper, eventshift, mindshift, web, brandedby-ai-platform)
- NO access to yusifg27-3093s-projects without re-login as yusifg27

# Scripts directory
- scripts/push_gh_secret.py — automate GH Actions secrets

# Patterns I keep forgetting
1. Check arsenal BEFORE asking CEO (check .env, CLIs, MCPs first)
2. Verify token works BEFORE saving (but save with status comment if blocked on billing/scope)
3. Use Bash directly for things I think need MCP (vercel CLI replaces some MCP calls)
4. CEO's two Vercel accounts: ganbaroff (volaura) + yusifg27 (mindshift family) — different teams
