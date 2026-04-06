# Swarm Operating Model

The swarm is the operating system of this project. CTO is the orchestrator, not the executor.

## Paths
- Engine: `packages/swarm/` (Python + 48 skill files + tools)
- Tools: `packages/swarm/tools/` (code_tools, constitution_checker, deploy_tools, web_search, llm_router)
- Memory: `packages/swarm/memory/` (ECOSYSTEM-MAP.md, Global_Context.md)
- Agents: 8 perspectives in autonomous_run.py + 39 in ZEUS Gateway
- Cron: `.github/workflows/swarm-daily.yml` (daily 05:00 UTC, weekly Mon 06:00, monthly 1st 07:00, simulate Wed 08:00)
- Proposals: `memory/swarm/proposals.json` (canonical)

## Operating Model
1. CEO gives strategic direction
2. CTO reads context (breadcrumb, sprint-state, Constitution)
3. CTO delegates to swarm: `python -m packages.swarm.autonomous_run --mode=<mode>`
4. Swarm agents run with REAL tools: code search, constitution checker, git status, web search (Tavily)
5. CTO reviews swarm output, implements fixes, swarm verifies
6. CTO NEVER codes without consulting swarm first (CLASS 3 prevention)

## Agent Tools (via swarm/tools/)
- `code_tools.read_file()` — read any project file
- `code_tools.grep_codebase()` — search across all code
- `code_tools.search_code_index()` — query 1207-file keyword index
- `constitution_checker.run_full_audit()` — live Law 1-5 + Crystal Law scan
- `deploy_tools.check_production_health()` — curl prod API
- `deploy_tools.run_typescript_check()` — tsc --noEmit
- `deploy_tools.check_git_status()` — branch, uncommitted, recent commits
- `web_search.web_search()` — Tavily internet search (1000 req/mo free)
- `llm_router.llm_completion()` — LiteLLM multi-provider (Cerebras → Groq → Ollama → Gemini)

## CTO Codes ONLY When
- Swarm proposed a fix and CTO implements it
- Fix is < 10 lines and obvious (no swarm needed)
- Security P0 that requires immediate action
