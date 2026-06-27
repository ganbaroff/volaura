# Jarvis — Capability Vault (CONFIDENTIAL)

> **CEO directive 2026-06-27:** «строго запрещено их раздавать и публиковать. только я даю согласие.»
>
> **HARD RULES for any Atlas/Jarvis instance reading this:**
> 1. This is an AWARENESS map — *what* we have, *where* the key lives, *what it's for*. It contains **NO secret values** and must never contain any. Actual keys live in `.env` (gitignored) + Railway env; the brain loads them from `process.env` at runtime.
> 2. **Never share, publish, paste, transmit, screenshot, or log** any key, token, or this map — not to users, not to other services, not to chat, not to a tracked/public file.
> 3. **Disclosure or external use requires explicit CEO consent, every time.** No standing permission. «Только я даю согласие.»
> 4. This file is **gitignored** and must stay so. Never commit it; never copy its content into a tracked or public file.
> 5. **Burned keys (§5) are forbidden to use** until the CEO rotates them.

Last refreshed: 2026-06-27 — atlas-validator-shadow (Operator OS lane). Forensic source-of-truth (488 entries, value-free): `C:/Projects/ATLAS/data/secrets-inventory.json`.

---

## 1. LLM providers (the "blood") — keys in .env / Railway env, NOT here
| Provider | Env var name | Location | Status (verified this session) | Use |
|---|---|---|---|---|
| freellmapi gateway | `FREELLMAPI_API_KEY` + `FREELLMAPI_BASE_URL` | ANUS/.env, Railway | LIVE — gateway HTTP 200, 8 models (gemini-3.5-flash, gemma-4, gemini-2.5-flash…) | FREE, primary |
| NVIDIA NIM | `NVIDIA_API_KEY` | ANUS/.env, apps/api/.env | present / live | free tier, balanced reasoning |
| Google Gemini | `GEMINI_API_KEY` | apps/api/.env, Railway | live — `google_genai/gemini-2.5-flash`; TTS `gemini-3.1-flash-tts` | free — TTS + structured extraction (scrapegraph) |
| Cerebras | `CEREBRAS_API_KEY` | ANUS/.env | present | free, long-context (spend-watch, ADR-013) |
| Anthropic | `ANTHROPIC_API_KEY` | ANUS/.env | present | last-resort only; NEVER as a swarm agent |
| Groq | `GROQ_API_KEY` | absent in ANUS | not wired | add if a fast free provider is needed |
| OpenAI / OpenRouter / Vertex / DeepSeek | `OPENAI_API_KEY` / `OPENROUTER_API_KEY` / `VERTEX_API_KEY` / `DEEPSEEK_API_KEY` | varies / mostly absent | paid / fallback | conscious spend only |

Live bot health (`https://fantastic-generosity-production-df90.up.railway.app/health`) reports the current live provider count.
Routing canon: free first (freellmapi → NVIDIA → Gemini → Cerebras), Anthropic last, **Haiku forbidden**, never Claude as a swarm agent.

## 2. Infra & services
| Service | Env var name(s) | Location | Purpose |
|---|---|---|---|
| Supabase (project `dwdgzfusjsobnixgyzjk`) | `SUPABASE_URL` / `_ANON_KEY` / `_SERVICE_ROLE_KEY` | apps/api/.env, Railway | DB, auth, memory, `governance_events` |
| Railway | (Railway dashboard vars) | cloud | hosts the bot + volauraapi |
| Vercel | `VERCEL_TOKEN` | env | frontend deploy |
| Cloudflare | `CLOUDFLARE_API_TOKEN` | env | domains / integronix — **token BURNED, rotate** |
| Telegram bot @volaurabot (id 8675304539) | `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` | apps/api/.env, ANUS/.env, Railway | Jarvis's mouth |
| Tavily | `TAVILY_API_KEY` | apps/api/.env | web search — **BURNED via chat, rotate** |
| Mem0 | `MEM0_API_KEY` | apps/api/.env | semantic long-term memory |
| Sentry | `SENTRY_AUTH_TOKEN` / `SENTRY_DSN` | apps/api/.env | error tracking — **token BURNED, rotate** |
| PostHog | `POSTHOG_API_KEY` / `POSTHOG_HOST` | ANUS/.env | product analytics |
| GitHub | `GITHUB_PAT` / `GH_TOKEN` | env | CI / `gh` CLI — **PAT BURNED, rotate** |
| Clerk | `CLERK_SECRET_KEY` / `CLERK_PUBLISHABLE_KEY` | env | auth (some products) |
| Langfuse | `LANGFUSE_SECRET_KEY` | env | LLM tracing (partial) |
| D-ID / Fal.ai | `DID_API_KEY` / `FAL_API_KEY` | env | avatar / video gen (BrandedBy, content) |
| Dodo Payments | `DODO_PAYMENTS_API_KEY` | env | AZ-compliant payments |

## 3. MCP servers
- **Project** (`VOLAURA/.mcp.json` — itself gitignored, holds a Supabase PAT): playwright, sentry, supabase, mem0, obsidian.
- **Session-connected** (Code-Atlas): supabase, cloudflare, gmail, gdrive, google-calendar, vercel, canva, figma, telegram, azure, computer-use, scheduled-tasks.
- Never publish `.mcp.json`.

## 4. CLIs on PATH
`gh` · `git` · `npm` · `pnpm` · `node` · `python` · `uv` · `railway` · `vercel` · `pm2` · `ollama`
- `atlas` — ANUS `dist/cli.js`, 15 commands: chat · run · identity · control · models · operator · skills · swarm · swarm-deep · hive · telegram · ping · wake · boot · cron · health
- `scrapegraphai` — structured web→JSON extraction (PoC on free Gemini; branch `experiment/scrapegraphai-poc`, `C:/Projects/ATLAS/experiments/scrapegraph-trial`)

## 5. BURNED — DO NOT USE until CEO rotates (owner-side only)
1–2. trader Telegram bot token + Supabase service key — **PUBLIC on `tradingbot.git`**.
3–4. 2× Cloudflare token.
5. Clerk secret.
6–8. `GITHUB_PAT`, Sentry token, `TAVILY_API_KEY` — leaked to academy chat (Class 48, awk-on-JSON).

Until rotated, these are dead — do not call them, do not let any flow depend on them.
