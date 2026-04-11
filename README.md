# VOLAURA

Verified Competency Platform — skills proven through adaptive assessment, not claimed on CVs.

## Products

| Product | Description | Status |
|---|---|---|
| **VOLAURA** | Adaptive assessments, AURA score, talent matching | Live — volaura.app |
| **MindShift** | ADHD-focused productivity + habit tracking | Live — mindshift.app |
| **Life Simulator** | Character progression game (Godot 4) | Dev |
| **BrandedBy** | AI video professional identity | Dev |
| **ZEUS** | Autonomous Python swarm agent | Local |

## Quick Start

```bash
pnpm install
pnpm dev                    # frontend on :3000
cd apps/api && uvicorn app.main:app --reload  # backend on :8000
```

See [docs/RUNBOOK.md](docs/RUNBOOK.md) for full setup including env vars.

## Architecture

- **Frontend:** Next.js 14 App Router + TypeScript + Tailwind v4
- **Backend:** FastAPI (Python 3.11) on Railway
- **Database:** Supabase PostgreSQL + pgvector (768-dim Gemini embeddings)
- **AI:** Gemini 2.5 Flash (primary) → Groq → OpenAI (fallback chain)
- **Swarm:** 8 autonomous NVIDIA/Groq agents, daily cron via GitHub Actions

→ [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — component diagram, ADRs  
→ [docs/ECOSYSTEM-MAP.md](docs/ECOSYSTEM-MAP.md) — 5-product data flows  
→ [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) — PR process, code rules

## Live Status

```bash
curl https://volauraapi-production.up.railway.app/health
```

| Service | URL |
|---|---|
| API | volauraapi-production.up.railway.app |
| Web | volaura.app |
| Docs | /docs (dev only) |
