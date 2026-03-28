# START SESSION — VOLAURA
**Brain activation file. Read this first. Every session. No exceptions.**
*Tell Claude: "Read START-SESSION-VOLAURA.md before anything else."*

---

## PHASE A GATE — PRODUCE THESE 3 LINES FIRST

```
▶ Line 1: "Sprint [N], Step [X]. Date: [today]. Protocol v4.0 loaded."
▶ Line 2: "Last session ended with: [from memory/context/sprint-state.md]"
▶ Line 3: "This session I will NOT: [top 3 from memory/context/mistakes.md]"
```

**Without these 3 lines → no work starts.**

---

## MANDATORY READING ORDER (do all 8, takes ~5 minutes)

| # | File | What's in it | Read when |
|---|------|-------------|-----------|
| 0 | `memory/swarm/SHIPPED.md` | **WHAT CODE EXISTS** — every Python file, router, feature built. If not here → you don't know it exists | **ALWAYS FIRST — before everything** |
| 1 | `memory/context/sprint-state.md` | **WHERE ARE WE RIGHT NOW** — last session summary, next priorities | Always |
| 2 | `CLAUDE.md` | Operating algorithm, tech stack, all rules | Always |
| 3 | `memory/context/mistakes.md` | 5 mistake classes + 50+ specific errors. What NOT to repeat | Always |
| 4 | `memory/context/patterns.md` | What WORKS. Patterns that proved themselves | Always |
| 5 | `memory/context/working-style.md` | Who Yusif is. Communication style. Expectations | Always |
| 6 | `memory/context/mcp-toolkit.md` | Which MCP/skill/tool to use for which task | When starting a sprint |
| 7 | `docs/EXECUTION-PLAN.md` (last 30 lines) | Current sprint checkboxes | When starting a sprint |
| 8 | `docs/DECISIONS.md` (last entry) | Last retrospective. What was decided and why | When starting a sprint |

---

## SWARM TEAM — WHO TO CALL

| Agent | Strength | Call for |
|-------|---------|----------|
| Security Agent | CVSS scoring, RLS, injection, XSS | Any auth/security/RLS change |
| Architecture Agent | Data flow, system coherence, migrations | Data model, new endpoints, code >50 lines |
| Product Agent | UX gaps, i18n, ADHD-first, persona testing | New UI, user journeys, copy |
| Needs Agent | Process improvement, highest leverage | Meta-analysis, workflow changes |
| QA Engineer Agent | Blind cross-testing, coverage, GRS validation | Assessment questions, test gaps |
| Growth Agent | Acquisition, retention, virality, monetization | Anything user-facing growth |

**Full routing table:** `memory/swarm/agent-roster.md`
**Shared context for agents:** `memory/swarm/shared-context.md`
**Pending team proposals:** `memory/swarm/proposals.json`

---

## SKILLS MATRIX — LOAD BEFORE CODING

| Sprint contains... | Load BEFORE starting |
|--------------------|---------------------|
| Any sprint start | `docs/MANDATORY-RULES.md` |
| Any code > 50 lines | `engineering:code-review` |
| New API endpoint | `docs/openspace-skills/volaura-security-review/skill.md` (10-point OWASP) |
| Security/auth/RLS | Same as above + Security Agent |
| UI/components | `design:critique` + `design:accessibility-review` |
| UX copy, button labels | `design:ux-writing` |
| Writing V0 prompts | `design:handoff` + `design:ux-writing` |
| New feature design | `design:user-research` + `engineering:system-design` |
| Deployment | `engineering:deploy-checklist` |
| Bug fix | `docs/engineering/skills/TDD-WORKFLOW.md` (write failing test FIRST) |
| Assessment questions | QA Engineer + Security Agents |
| Growth features | `growth-strategy` + Growth Agent |
| Session end | `docs/engineering/skills/CONTINUOUS-LEARNING.md` |

**Full matrix:** `CLAUDE.md` → Skills Matrix section

---

## MCP TOOLS AVAILABLE THIS SESSION

| Tool | What it does | Use when |
|------|-------------|---------|
| `mcp__openspace__execute_task` | Run task using best-matching skill | Any reusable pattern task |
| `mcp__openspace__search_skills` | Find relevant skill for task | Before writing any boilerplate |
| `mcp__openspace__upload_skill` | Save new pattern as reusable skill | After solving non-trivial problem |
| `mcp__openspace__fix_skill` | Improve existing skill with new learning | After skill produces bad result |
| `mcp__supabase__execute_sql` | Run SQL against production DB | Schema queries, data checks |
| `mcp__supabase__apply_migration` | Apply migration file to production | After creating migration SQL |
| `mcp__supabase__list_tables` | List all DB tables | Schema exploration |
| `mcp__supabase__get_logs` | Supabase logs | Debug production errors |
| Vercel MCP | Deploy, logs, project info | Frontend deployment |

---

## TOP 5 MISTAKE CLASSES (never repeat)

| Class | Pattern | Count |
|-------|---------|-------|
| CLASS 3 | **Solo execution** — deciding without team agents | 10x |
| CLASS 1 | **Protocol skipping** — "I'll be faster without it" | 7x |
| CLASS 2 | **Memory not persisted** — session ends without updating files | 8x |
| CLASS 4 | **Schema/type mismatch** — assumed field names without checking | 4x |
| CLASS 5 | **Fabrication** — invented stats, features, or agent proposals | 3x |

**Rule:** If you catch yourself about to make a CLASS 3 → stop, launch agents first.

---

## CRITICAL NEVER/ALWAYS (condensed)

**NEVER:**
- SQLAlchemy / Celery / tRPC / Redux / Pages Router
- Global Supabase client — always per-request via `Depends()`
- Pydantic v1 syntax (`class Config`, `orm_mode`, `@validator`)
- `print()` — use `loguru` logger
- Hardcode strings — use `t()` i18n function
- Relative routing `/dashboard` — always `/${locale}/dashboard`
- Hand-write API types — run `pnpm generate:api`
- Skip response envelope unwrap — always unwrap `.data`
- `google-generativeai` — use `google-genai`

**ALWAYS:**
- Per-request Supabase via `Depends()`
- Pydantic v2 (`ConfigDict`, `@field_validator`, `@classmethod`)
- RLS policies on all new tables
- Structured JSON errors: `{"code": "...", "message": "..."}`
- UTF-8 encoding on file operations
- `isMounted` ref on components with async state
- Crystal operations → `deduct_crystals_atomic()` RPC only
- AURA scores → exact weights (see CLAUDE.md)
- i18n AZ: 20-30% longer, DD.MM.YYYY, 1.234,56 format

---

## CURRENT KNOWN ISSUES (from Session 54)

| Issue | Priority | Status |
|-------|----------|--------|
| Profile verifications empty | HIGH | hardcoded `[]` — no backend API |
| Assessment has no description | HIGH | users don't know what they're tested on |
| Leaderboard no jump-to-rank | MED | users > rank 20 can't find themselves |
| Download Card not built | LOW | button disabled "coming soon" |
| E2E automated tests | MED | no frontend tests yet (Mistake #16) |

---

## KEY FILES MAP

```
CLAUDE.md                              Operating algorithm + all rules
START-SESSION-VOLAURA.md               THIS FILE — brain activation
HANDOFF-SESSION-55.md                  Latest clean handoff doc

memory/context/sprint-state.md         WHERE WE ARE (read first)
memory/context/mistakes.md             What NOT to repeat
memory/context/patterns.md             What WORKS
memory/context/working-style.md        Who Yusif is
memory/context/mcp-toolkit.md          MCP/tool decision matrix
memory/context/deadlines.md            Milestones

docs/EXECUTION-PLAN.md                 Sprint checkboxes
docs/DECISIONS.md                      Architecture decisions + retrospectives
docs/MANDATORY-RULES.md                7 non-negotiable rules

memory/swarm/agent-roster.md           Team: who does what
memory/swarm/shared-context.md         Schema, architecture, pipeline — for agents
memory/swarm/proposals.json            Pending agent proposals
memory/swarm/agent-launch-template.md  How to launch agents correctly

apps/api/app/routers/                  FastAPI endpoints
apps/web/src/app/[locale]/             Next.js pages
apps/web/src/hooks/queries/            TanStack Query hooks (generated)
apps/web/src/locales/                  i18n strings (EN + AZ)
supabase/migrations/                   DB migrations
```

---

## SESSION END CHECKLIST (before closing chat)

- [ ] `memory/context/sprint-state.md` — updated with session summary
- [ ] `docs/DECISIONS.md` — retrospective entry added
- [ ] `docs/EXECUTION-PLAN.md` — completed items marked `[x]`
- [ ] `memory/context/mistakes.md` — new mistakes added if any
- [ ] `memory/context/patterns.md` — new patterns added if any
- [ ] `memory/swarm/shared-context.md` — updated if code/schema changed
- [ ] Git committed + pushed
- [ ] `memory/projects/volaura.md` — status section updated

**Without completing all applicable items → session is NOT properly closed.**

---

*Last updated: 2026-03-28 | Session 55*
