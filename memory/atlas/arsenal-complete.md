# Arsenal Complete — Unified Ecosystem Inventory
**Created:** 2026-04-12 (Cowork Session 5, deep audit)
**Purpose:** One document that tells any Atlas instance (or Cowork session) exactly what tools, APIs, skills, agents, and infrastructure exist — and what's missing.
**Authority:** This is the SINGLE SOURCE OF TRUTH for "what do we have?" Updated by whoever adds or removes a capability.

---

## 1. MCP CONNECTORS (Available in Cowork)

| MCP | Tools | Status | Use Case |
|-----|-------|--------|----------|
| **Figma** | get_design_context, get_screenshot, get_metadata, get_variable_defs, search_design_system, create_design_system_rules, code_connect (6 tools) | ✅ Active | Design review, component audit, handoff specs |
| **Google Drive** | google_drive_search, google_drive_fetch | ✅ Active | Document retrieval, shared file access |
| **Claude in Chrome** | navigate, read_page, get_page_text, form_input, find, computer, javascript_tool, tabs_*, shortcuts_*, gif_creator, file_upload, upload_image, resize_window, read_console_messages, read_network_requests | ✅ Active | Browser automation, web scraping, visual QA |
| **Scheduled Tasks** | create_scheduled_task, list_scheduled_tasks, update_scheduled_task | ✅ Active | Cron jobs: content batches, monitoring |
| **Cowork Tools** | present_files, request_cowork_directory, allow_cowork_file_delete | ✅ Active | File management, workspace access |
| **MCP Registry** | search_mcp_registry, suggest_connectors | ✅ Active | Discover new MCPs on demand |
| **Plugins** | search_plugins, suggest_plugin_install | ✅ Active | Extend capabilities |
| **Session Info** | list_sessions, read_transcript | ✅ Active | Cross-session context recovery |

### MCP Gaps (NOT connected but needed)
| MCP | Why Needed | Priority |
|-----|-----------|----------|
| **Supabase MCP** | Direct SQL, migrations, RLS audit from Cowork | P1 — Atlas has it in Claude Code, Cowork doesn't |
| **Sentry MCP** | Real-time error monitoring without browser | P1 — errors visible only in Claude Code today |
| **Slack/Telegram MCP** | Send messages to team channels | P2 — currently only via Python bot |
| **GitHub MCP** | PR review, issue management | P2 — gh CLI not in sandbox either |
| **Langfuse MCP** | LLM trace inspection | P3 — cloud.langfuse.com accessible via browser |
| **PostHog MCP** | Analytics without browser | P3 — pre-launch, not urgent |

---

## 2. LLM PROVIDERS & API KEYS

### Active Providers (53 env vars total, 6 documented in .env.md)

| Provider | Key | Role in Ecosystem | Tier |
|----------|-----|-------------------|------|
| **Gemini (Google)** | GEMINI_API_KEY | Primary LLM — assessment evaluation, embeddings (768d) | Primary |
| **Cerebras** | CEREBRAS_API_KEY | Swarm primary — Qwen3-235B, 2000+ tok/s | Primary |
| **Groq** | GROQ_API_KEY | Swarm fast inference | Backup |
| **NVIDIA NIM** | NVIDIA_API_KEY | Swarm backup — Llama models | Backup |
| **OpenRouter** | OPENROUTER_API_KEY | Multi-model routing | Backup |
| **DeepSeek** | DEEPSEEK_API_KEY | R1 reasoning model | Backup |
| **Vertex AI** | VERTEX_API_KEY | Google enterprise tier | Reserve |
| **OpenAI** | OPENAI_API_KEY | Legacy fallback only | Last resort |
| **fal.ai** | FAL_API_KEY | Video generation (MuseTalk/Kling) for BrandedBy | Specialized |
| **D-ID** | DID_API_KEY | Video avatar generation ($5.90/mo lite) | Specialized |

### Infrastructure Keys
| Service | Keys | Purpose |
|---------|------|---------|
| **Supabase (VOLAURA)** | URL, SERVICE_KEY, ANON_KEY, PUBLISHABLE_KEY | Primary database |
| **Supabase (MindShift)** | URL_MINDSHIFT, ANON_KEY_MINDSHIFT, SERVICE_KEY_MINDSHIFT | Cross-product bridge |
| **Telegram** | BOT_TOKEN, CEO_CHAT_ID, WEBHOOK_SECRET | Agent→CEO notifications |
| **Sentry** | AUTH_TOKEN, DSN | Error tracking |
| **Langfuse** | PUBLIC_KEY, SECRET_KEY, HOST | LLM observability |
| **Stripe** | SECRET_KEY, WEBHOOK_SECRET, PRICE_ID | Payments (disabled) |
| **Dodo Payments** | API_KEY | Alt payment processor |
| **Resend** | API_KEY | Transactional email (disabled) |
| **Supernova** | AUTH_TOKEN | Design token sync Figma→Tailwind |
| **Mem0** | API_KEY | Memory MCP (free 10K/mo) |
| **GitHub OAuth** | CLIENT_ID, CLIENT_SECRET | Social login |
| **Google OAuth** | CLIENT_ID, CLIENT_SECRET | Social login |

### Feature Flags
| Flag | Default | Purpose |
|------|---------|---------|
| PAYMENT_ENABLED | false | Stripe/Dodo gate |
| EMAIL_ENABLED | false | Resend gate |
| OPEN_SIGNUP | false | Invite-only beta |
| SWARM_ENABLED | false | Python swarm gate |

### Key Documentation Gap
**.env.md documents only 6 of 53 keys (11%).** Config.py is the real source of truth. This needs fixing — Atlas should update .env.md to match config.py.

---

## 3. SKILL INVENTORY (246 files across 4 layers)

### Layer 1: Cowork Skills (8)
| Skill | Purpose |
|-------|---------|
| docx | Word document creation/editing |
| pdf | PDF processing, extraction, merge/split |
| pptx | Presentation creation/editing |
| xlsx | Spreadsheet creation/data analysis |
| growth-strategy | Growth planning, viral loops, acquisition |
| schedule | Scheduled task creation |
| setup-cowork | Guided onboarding |
| skill-creator | Create/optimize/eval skills |

### Layer 2: Claude Code Skills (7) + Agents (116)
**Skills:** content-factory, product-strategy, promotion-agency, social-post, video-script, accelerator-grant-searcher, startup-registration-finder

**Active agents (15 proven):** a11y-scanner, sec, security-auditor, code-reviewer, guardrail-auditor, qa-quality-gate, build-error-resolver, bundle-analyzer, infra, liveops, architect, ecosystem-auditor, product-ux, growth, e2e-runner

**Legacy agents:** 101 files in 23 subdirectories (claude-flow framework, decision pending)

### Layer 3: Swarm Skills (51) + Python Modules (56)
**51 skill files** in memory/swarm/skills/ — one per agent specialization. Covers: assessment science, behavioral nudges, CEO reporting, community management, competitor intelligence, cultural intelligence, customer success, data engineering, DevOps/SRE, DORA metrics, financial analysis, investor reporting, legal advisory, LinkedIn content, onboarding, payment provider, performance engineering, PR/media, promotion, QA quality, risk management, sales strategy, technical writing, trend scouting, university partnerships, UX research.

**56 Python modules** in packages/swarm/ — core engine (engine.py, orchestrator.py, coordinator.py), memory layer (agent_memory.py, memory.py, memory_consolidation.py), reasoning (reasoning_graph.py, reasoning_store.py), execution (run_queue.py, scheduler.py, workflow.py), monitoring (telemetry.py, tracing.py, heartbeat_gate.py), plus 21 archived eval scripts.

### Layer 4: Engineering Skills (8)
TDD-WORKFLOW, SECURITY-REVIEW, CONTINUOUS-LEARNING, REACT-HOOKS-PATTERNS, RECURSIVE-CRITICISM, THREAT-MODEL-TEMPLATE, Decision-Simulation-Engine v4.0

---

## 4. SANDBOX CAPABILITIES

### Available Tools
| Tool | Path | Use |
|------|------|-----|
| Python 3 | /usr/bin/python3 | Scripts, data processing, API calls |
| Node.js | /usr/bin/node | JS/TS execution |
| npm | /usr/bin/npm | Package management |
| ffmpeg + ffprobe | /usr/bin/ | Audio/video processing |
| ImageMagick | /usr/bin/convert | Image manipulation |
| Pandoc | /usr/bin/pandoc | Document format conversion |
| LaTeX (pdflatex, xelatex) | /usr/bin/ | PDF generation |
| curl, jq, wget | /usr/bin/ | HTTP + JSON processing |

### Available Python Packages
pandas, numpy, openpyxl, python-pptx, python-docx, camelot-py, fal_client, edge-tts, beautifulsoup4, requests, Pillow (via imageio), graphviz, aiohttp

### NOT Available (Gaps)
| Tool | Impact | Fix |
|------|--------|-----|
| **playwright** | Cannot run E2E tests from Cowork | `pip install playwright && playwright install chromium` |
| **gh (GitHub CLI)** | Cannot manage PRs/issues | Download from github.com/cli |
| **docker** | Cannot run containers | Not fixable in sandbox |

---

## 5. SCHEDULED TASKS (Active)

| Task | Schedule | Purpose |
|------|----------|---------|
| weekly-content-batch | Monday 10:00 UTC | Generate weekly content batch |
| content-post-prep | Tue/Thu 16:00 UTC | Prepare content for posting |

### Missing Scheduled Tasks (should exist)
| Task | Schedule | Purpose |
|------|----------|---------|
| stale-doc-audit | Weekly | Flag memory files not updated in >7 days |
| swarm-health-check | Daily | Verify Python swarm cron ran, check proposals.json |
| production-smoke | Every 6h | Hit volaura.app + API, report failures to Telegram |

---

## 6. PRODUCTION INFRASTRUCTURE

| Service | URL | Status |
|---------|-----|--------|
| Frontend | https://volaura.app | Vercel (free tier) |
| Backend API | https://volauraapi-production.up.railway.app | Railway (~$8/mo) |
| Database | Supabase PostgreSQL | Free tier |
| Swarm Cron | .github/workflows/swarm-daily.yml | Daily 05:00 UTC |
| Error Tracking | Sentry | Active |
| LLM Observability | Langfuse (cloud.langfuse.com) | Free tier 50K/mo |

**Stale reference:** e2e-runner.md still says `modest-happiness-production` — needs update to `volauraapi-production`.

---

## 7. COORDINATION MODEL

```
CEO (Yusif) — strategic direction, veto, values
    │
    ├── Cowork (this chat) — planning, visualization, content, orchestration
    │       │
    │       ├── Claude in Chrome — browser automation, visual QA
    │       ├── Figma MCP — design review
    │       ├── Google Drive MCP — document access
    │       └── Scheduled Tasks — cron automation
    │
    ├── Atlas (Claude Code) — code execution, migrations, E2E, deploys
    │       │
    │       ├── 15 active agents — security, QA, a11y, infra, etc.
    │       ├── Supabase MCP — direct SQL
    │       ├── Sentry MCP — error monitoring
    │       └── GitHub — PRs, commits, CI/CD
    │
    ├── Perplexity (CTO-Brain) — research, architecture, strategy critique
    │
    ├── NotebookLM — deep analytics, source-grounded research
    │
    └── Python Swarm (44 agents) — autonomous background work
            │
            ├── Cerebras Qwen3-235B (primary)
            ├── Ollama qwen3:8b (local)
            ├── NVIDIA NIM (backup)
            └── Groq (fast inference)
```

---

## 8. GAP ANALYSIS — WHAT'S MISSING

### Critical (P0)
1. **.env.md documentation** — 88% of keys undocumented. Config.py is source of truth but .env.md should match.
2. **Playwright in sandbox** — blocks E2E testing from Cowork. Atlas can run in Claude Code but Cowork can't verify.
3. **3 stale documents** — deadlines.md (Apr 3), volaura.md (Session 50), EXECUTION-PLAN.md (Session 42). All 40+ sessions behind.

### Important (P1)
4. **Supabase MCP for Cowork** — Atlas has direct SQL, Cowork doesn't. Limits database visibility.
5. **Sentry MCP for Cowork** — production errors only visible in Claude Code or browser.
6. **Agent activation rate** — 44 agents in roster, ~6 ever activated. 86% idle. Root cause: skills loaded as 500-char snippets.
7. **Content pipeline not implemented** — handoff written (memory/atlas/content-pipeline-handoff.md), needs Atlas execution.

### Nice to Have (P2)
8. **GitHub CLI in sandbox** — would enable PR/issue management from Cowork.
9. **Ecosystem graph v2** — CEO wants better version in admin panel. Current HTML is MVP.
10. **Scheduled stale-doc audit** — no automated detection of outdated memory files.

---

## 9. CROSS-REFERENCE: WHO OWNS WHAT

| Domain | Owner | Tools |
|--------|-------|-------|
| Code changes | Atlas (Claude Code) | git, agents, Supabase MCP |
| Planning & orchestration | Cowork (this chat) | MCPs, browser, skills, scheduling |
| Architecture research | Perplexity | Web search, papers |
| Deep analytics | NotebookLM | Source notebooks |
| Daily autonomous work | Python Swarm | Cerebras, NVIDIA, Groq, Ollama |
| Visual QA | Cowork + Chrome MCP | Browser automation |
| Design review | Cowork + Figma MCP | Component audit |
| Content creation | Cowork + content-factory skill | 6-step pipeline |
| Deployment | Atlas + infra agent | Railway, Vercel, GitHub Actions |
| Security audit | Atlas + sec agent | OWASP, RLS, auth review |
| User testing | Atlas + e2e-runner | Playwright (when installed) |

---

*Last updated: 2026-04-12 by Cowork Session 5. Next update: whenever a capability is added or removed.*
