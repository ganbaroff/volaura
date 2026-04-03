# MCP & Skills Toolkit — CTO Reference
# Last Updated: 2026-04-03 (v4 — verified ALL tools with live tests)
# PURPOSE: Read this BEFORE any sprint. Pick tools proactively. Never ask Yusif what to use.
# RULE: If it's in this file → CTO has FULL ACCESS. Never say "you need to do this." DO IT.

## VERIFIED INFRASTRUCTURE (tested 2026-04-03)
| Tool | Status | How |
|------|--------|-----|
| Railway CLI | ✅ v4.33.0 | `railway up --detach`, `railway logs`, `railway variables` |
| GitHub CLI | ✅ v2.88.1 | `gh secret set`, `gh pr`, logged in as ganbaroff |
| NotebookLM | ✅ v0.3.4 | `notebooklm create/ask/source add-research` |
| Telegram Bot | ✅ @volaurabot | Commands registered, webhook with secret |
| Supabase MCP | ✅ | apply_migration, execute_sql, get_advisors |
| Vercel MCP | ✅ | list_deployments, get_build_logs |
| Playwright MCP | ✅ installed | Browser testing |
| Sentry MCP | ✅ installed | Production errors |
| 16 API keys | ✅ all SET | Gemini, Groq, NVIDIA, OpenAI, DeepSeek, Vertex, FAL, Dodo, Sentry |

---

## RULE: When to Check This File
- Session start → read last 30 lines (match current sprint to tool)
- Before writing code → check if an MCP can do it in 1 call instead
- Before browser-testing manually → use Playwright or Claude in Chrome
- Before checking docs manually → use Context7
- Before opening GitHub.com → use GitHub MCP

---

## SECTION 1 — ACTIVE MCPs (Available Right Now in Session)

### 🔴 CORE INFRASTRUCTURE

| MCP | Tools | When to Use |
|-----|-------|-------------|
| **Supabase** `mcp__supabase` | apply_migration, execute_sql, list_tables, get_logs, deploy_edge_function, create_branch, list_migrations | DB schema changes, migrations, SQL queries, edge functions, production data checks |
| **Vercel** `mcp__a4a42010` | deploy_to_vercel, list_deployments, get_runtime_logs, get_deployment, get_project, list_projects, get_deployment_build_logs | Frontend deploys, check build logs, runtime errors, deployment status |

### 🟠 CODE & REPOSITORIES

| MCP | Tools | When to Use |
|-----|-------|-------------|
| **GitHub** `mcpServers.github` | (full GitHub API via Copilot MCP) | PR reviews, create issues, search code, manage releases, check CI status, view commits — **requires restart to activate** |

### 🎨 DESIGN (added 2026-03-26 — agent-reviewed, CEO-approved)

| MCP | Tools | When to Use |
|-----|-------|-------------|
| **Stitch** `mcpServers.stitch` | `generate_screen_from_text`, export HTML/React, design context | Start of any NEW page/component — describe UI in words → get React code. 0→1 prototyping. Official Google MCP. **requires restart** |
| **Figma** `mcp__3183acdc` | get_design_context, get_screenshot, get_variable_defs, search_design_system, get_code_connect_map | Pull EXISTING design tokens, component specs, screenshots from Figma files. 1→100 iteration. |

**Stitch vs Figma — NOT duplicates (agent research, 2026-03-26):**
- Stitch = **text→design→code** (0→1). `generate_screen_from_text` creates UI from a text description. No existing .fig file needed. Free 350 gen/month.
- Figma = **existing-design→code** (1→100). `get_design_context` reads existing .fig files for tokens, variants, team collaboration specs.
- Use Stitch when building new screens from scratch. Use Figma when converting existing designs.
- CEO quote: "Stitch лучше чем фигма... не из за дубликации а обоснованно говорите."

**REJECTED MCPs (with technical justification — agent team, 2026-03-26):**
- ❌ **UX Expert** — No AZ i18n support (critical for Volaura), 70% overlap with existing `vercel-web-design-guidelines` + `design:accessibility-review` skills, only 86 downloads/week (immature). Skills we already have cover WCAG/heuristics.
- ❌ **Nano Banana** — Wrapper around Gemini SDK we already have in `apps/api/`. Same cost, adds MCP overhead. Use `google-genai` directly or Gemini API skill instead.
- ~~��� **Playwright**~~ → ✅ REINSTATED 2026-04-03. Added to .mcp.json. Microsoft official @playwright/mcp. Visual E2E testing.

### 🟡 BROWSER & UI TESTING

| MCP | Tools | When to Use |
|-----|-------|-------------|
| **Claude Preview** `mcp__Claude_Preview` | preview_start, preview_stop, preview_screenshot, preview_snapshot, preview_click, preview_fill, preview_logs, preview_console_logs, preview_network | Test local frontend: start server, screenshot, click buttons, fill forms, check console errors |
| **Claude in Chrome** `mcp__Claude_in_Chrome` | navigate, find, form_input, get_page_text, read_page, javascript_tool, read_console_messages, read_network_requests, gif_creator, upload_image | Test production URL, E2E flows in real browser, check live volaura.app |

### 🟢 DOCUMENTATION & DESIGN

| MCP | Tools | When to Use |
|-----|-------|-------------|
| **Context7** `mcpServers.context7` | (doc lookup by library) | Before using any library: fetch current Next.js 14 / FastAPI / Supabase / Pydantic v2 docs. Avoids guessing deprecated APIs — **requires restart to activate** |
| **Figma/Stitch** `mcp__3183acdc` | get_design_context, get_screenshot, get_variable_defs, search_design_system, get_code_connect_map, generate_diagram | Pull design tokens, screenshots, component specs from Figma/Stitch |

### 🔵 FILES & SCHEDULING

| MCP | Tools | When to Use |
|-----|-------|-------------|
| **Google Drive** `mcp__c1fc4002` | google_drive_search, google_drive_fetch | Retrieve Yusif's docs, pitch decks, strategy files from Drive |
| **Scheduled Tasks** `mcp__scheduled-tasks` | create_scheduled_task, list_scheduled_tasks, update_scheduled_task | Set up recurring checks: daily deploy health, weekly test runs |
| **MCP Registry** `mcp__mcp-registry` | search_mcp_registry, suggest_connectors | Find and add new MCP servers when a capability is missing |

---

## SECTION 2 — MARKETPLACE PLUGINS (Installed, NOT yet connected — need auth via Claude Code UI)

| Plugin | What It Needs | Value When Connected |
|--------|--------------|----------------------|
| **Slack** | Slack OAuth | Read team channels, find context in conversations |
| **Linear** | Linear API key | Create/update issues directly from sprint work |
| **Greptile** | greptile.com account | AI code review comments on every PR |
| **Context7** | None (free) | Already added to mcpServers above ↑ |
| **Playwright** | None | REJECTED — Claude in Chrome + Preview cover same capability |
| **Serena** | None | Semantic code analysis, refactoring via LSP |
| **Asana** | Asana token | Task tracking (not needed — Linear is better) |
| **Firebase** | Google auth | Not relevant to Volaura stack |
| **GitLab** | GitLab token | Not relevant — we use GitHub |

---

## SECTION 3 — SKILLS (Use with /skill or Skill tool)

### ALWAYS USE BEFORE THESE TASKS:

| Trigger | Skill to Load | How to Use |
|---------|--------------|-----------|
| Writing LinkedIn post | `post` | `/post` — Volaura brand voice, honesty rules |
| Code review > 50 lines | `sentry-code-review` | Load before reviewing any significant change |
| GitHub PRs / stacked branches | `callstack-github` | Load when managing PRs or branch strategies |
| React/Next.js component work | `vercel-react-best-practices` | Load before writing any React component |
| Reviewing UI / UX | `vercel-web-design-guidelines` | Load before critiquing any page |
| Component composition decisions | `vercel-composition-patterns` | Load when refactoring components |
| Supabase query optimization | `supabase-postgres-best-practices` | Load before writing any complex SQL |
| Gemini API calls | `gemini-api-dev` | Load before any Gemini SDK usage |
| Gemini Live/streaming | `gemini-live-api-dev` | Load before real-time Gemini features |
| Stitch → React components | `stitch-react-components` | Convert Stitch/Figma designs to React |
| Stripe integration | `stripe-best-practices` | Load if payment features ever added |
| Performance audit | `cloudflare-web-perf` | Core Web Vitals, render-blocking resources |
| Research tasks | `notebooklm` | Deep research: create notebook, add sources, ask |
| DSP / decision making | `decision-toolkit` | Structured decision analysis when DSP needed |
| Mobile (React Native) | `react-native-best-practices` | Not current stack, but if mobile added |
| Creating new skills | `anthropic-skills:skill-creator` | Build custom skills for Volaura |
| Word docs | `anthropic-skills:docx` | Generate .docx reports / proposals |
| Spreadsheets | `anthropic-skills:xlsx` | Financial models, data exports |
| PDFs | `anthropic-skills:pdf` | Read/create/merge PDFs |
| Presentations | `anthropic-skills:pptx` | Pitch decks, investor materials |
| Growth / viral / referrals | `anthropic-skills:growth-strategy` | Growth features, referral system |

### PLUGINS (also accessible as skills):

| Plugin | When to Use |
|--------|------------|
| `code-review@claude-plugins-official` | Code review with structured feedback |
| `pr-review-toolkit@claude-plugins-official` | Full PR review workflow |
| `security-guidance@claude-plugins-official` | Security review, vulnerability analysis |
| `feature-dev@claude-plugins-official` | Feature development workflow |
| `frontend-design@claude-plugins-official` | Frontend design patterns |

---

## SECTION 4 — DECISION MATRIX: "Which tool for this task?"

```
Task: Check if production is up
→ mcp__Claude_in_Chrome: navigate("https://volaura.app")
   OR: curl https://volaura.app/health (Bash)

Task: Debug frontend error in production
→ mcp__a4a42010 (Vercel): get_runtime_logs
   THEN: mcp__Claude_in_Chrome: read_console_messages

Task: Apply database migration
→ mcp__supabase: apply_migration
   BEFORE: mcp__supabase: execute_sql (backup check)

Task: Test a UI button locally
→ mcp__Claude_Preview: preview_start → preview_click

Task: Test a UI flow on volaura.app
→ mcp__Claude_in_Chrome: navigate → find → form_input

Task: Review a PR
→ GitHub MCP (after restart) OR: gh pr view + gh pr diff (Bash)

Task: Write a new React component
→ Load skill: vercel-react-best-practices FIRST
   THEN: mcp__3183acdc (get design context if Figma available)

Task: Fetch Next.js 14 App Router docs
→ Context7 MCP (after restart): resolve-library-id "next.js"

Task: Write LinkedIn post
→ /post skill (already active)

Task: Search Yusif's strategy docs
→ mcp__c1fc4002: google_drive_search

Task: Set up recurring health check
→ mcp__scheduled-tasks: create_scheduled_task

Task: Design a new page/screen (start from scratch)
→ mcpServers.stitch: describe UI in text → get React component
   THEN: wire to API as usual

Task: UX/accessibility audit before shipping
→ Load skill: vercel-web-design-guidelines + design:accessibility-review
   THEN: fix violations before deploy

Task: Need image for marketing/social
→ Use Gemini API directly (google-genai SDK) or gemini-api-dev skill
```

---

## SECTION 5 — WHAT NEEDS A RESTART TO ACTIVATE

These were added to `~/.claude/settings.json` on 2026-03-26 and require Claude Code restart:

- **GitHub MCP** — `mcpServers.github` (HTTP, uses GITHUB_PERSONAL_ACCESS_TOKEN from env)
- **Context7 MCP** — `mcpServers.context7` (npx, pinned @2.1.4 — supply chain security)
- **Stitch MCP** — `mcpServers.stitch` (npx, @latest — pin version after first use)

After restart they will appear in the deferred tools list like the other MCPs.

---

## SECTION 6 — MARKETPLACE PLUGINS STILL TO CONNECT (by value)

Priority order when Yusif has 10 minutes:

1. **Slack** — `/plugins` → connect Slack → OAuth → done. Value: team comms context
2. **Linear** — API key from linear.app → sprint tracking without copy-paste
3. **Greptile** — greptile.com account → auto PR reviews on every push
4. **Serena** — no auth needed → `/plugins` → connect → semantic code nav

---

## SECTION 7 — TOKENS & CREDENTIALS (what's stored where)

| Credential | Where Stored | Used By |
|-----------|-------------|---------|
| GITHUB_PERSONAL_ACCESS_TOKEN | `~/.claude/settings.json` env section | GitHub MCP |
| Supabase credentials | `apps/api/.env` | Supabase MCP (uses project ref hvykysvdkalkbswmgfut) |
| Railway token | Railway dashboard / CI | Bash curl to Railway API |
| Gemini API key | `apps/api/.env` + Railway env | LLM calls |
| Telegram bot token | `apps/api/.env` + Railway env + GitHub Secrets | @volaurabot |

---

_This file is read at session start. Update when new MCPs/skills are added._
