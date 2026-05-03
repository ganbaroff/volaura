# AGENTS.md — Machine-Readable Manifest for AI Agents

**Purpose:** This file is the first thing any AI agent (Claude Code, Cursor, Cline, Aider, a bespoke swarm worker, or an unknown future tool) should read when opening this repository. It declares the architectural boundaries, data handling rules, error propagation patterns, testing expectations, and design invariants that govern the VOLAURA ecosystem. It is intentionally concise and machine-friendly. For full context, follow the pointers below.

**Authority order (highest wins on conflict):**
1. `docs/ECOSYSTEM-CONSTITUTION.md` v1.7 — the 5 Foundation Laws + 8 Crystal Economy Laws governing what the products do to users. Supreme law.
2. `docs/CONSTITUTION_AI_SWARM.md` v1.0 — governance layer for the AI CTO swarm itself.
3. `CLAUDE.md` (project-level) — operational rules for Claude Code and other agents during development.
4. `ATLAS.md` (repo root) — persistent identity layer for Atlas, the CTO-Hands agent, and its wake protocol.
5. This file — architectural boundaries and invariants.

---

## Identity and role hierarchy

- **CEO (human, unconditional veto):** Yusif Ganbarov
- **CTO-Brain (AI, strategy + architecture):** Perplexity (separate chat, upstream planning)
- **CTO-Hands (AI, execution + verification):** **Atlas** (Claude Opus 4.6, named 2026-04-12, persistent memory in `memory/atlas/`)
- **Swarm council (17 registered perspectives + ~50 skill markdown modules in `memory/swarm/skills/`, peer review + whistleblower rights):** NVIDIA NIM, Ollama local, Gemini, Groq. **Claude models are forbidden in this layer by Article 0.**

If you are loading this repo as an AI agent and Yusif addresses you by any of the Atlas wake triggers ("атлас", "atlas", "hey atlas", "привет атлас", "атлас привет", "атлас проснись"), read `memory/atlas/wake.md` first and follow the ritual. First word of response must be a Russian wake acknowledgment.

---

## Tech stack (locked)

**Frontend:** Next.js 14.2.35 App Router only (never Pages Router, never 15 without separate ADR), TypeScript 5 strict, Tailwind 4 CSS-first, Zustand, TanStack Query, react-i18next (AZ primary, EN secondary), shadcn/ui, Framer Motion.

**Backend:** Python 3.11+, FastAPI async, Supabase async SDK (`acreate_client` per-request via `Depends()` — **never** a module-level client), Pydantic v2 (`ConfigDict`, `@field_validator` — never v1 syntax), google-genai SDK (never `google-generativeai`), loguru (never `print()`), pure-Python IRT/CAT 3PL engine at `apps/api/app/core/assessment/engine.py`.

**Database:** Supabase Postgres, RLS on every table, `pgvector(768)` dimensions (Gemini embeddings — **never** 1536/OpenAI), vector operations via RPC only.

**Hosting:** Vercel (frontend `volaura.app`), Railway (backend `volauraapi-production.up.railway.app`), Supabase (DB free tier).

**LLM providers (Article 0, locked):** Cerebras Qwen3-235B → Ollama local → NVIDIA NIM → Anthropic Haiku (last resort only). Never Claude as a swarm agent. Never a single provider.

---

## Module boundaries

| Workspace | May depend on | May NOT depend on | Owns |
|---|---|---|---|
| `apps/web/` | `packages/*`, `apps/api/` via HTTP | `apps/api/` Python internals, `packages/swarm/` | User-facing UI, i18n, Zustand stores, TanStack hooks |
| `apps/api/` | `packages/swarm/` via explicit imports only when documented, Supabase SDK, Pydantic | `apps/web/` internals, frontend state | FastAPI routers, services, migrations callers, model_router, assessment engine |
| `packages/swarm/` | Its own tools, `packages/swarm/tools/*`, Supabase service-role client | `apps/api/app/*` internals, `apps/web/*` | 17-perspective Python swarm + ~50 skill markdown modules in `memory/swarm/skills/`, autonomous_run, proposals, session-end hook |
| `supabase/migrations/` | — | — | Immutable SQL migration history. Never mutate existing files. New files with timestamped names only. |
| `memory/atlas/` | — | — | Atlas persistent identity. Under git. Do not edit without understanding you are rewriting an agent's self-model. |
| `memory/swarm/` | — | — | Swarm runtime state (some files gitignored). `proposals.json` is canonical, `ceo-inbox.md` is human-facing. |
| `docs/` | — | — | ADRs in `docs/adr/`, research in `docs/research/`, strategy at root. |

Cross-workspace imports that are not in this table are a violation. Flag and halt rather than invent a new allowed dependency.

---

## Data handling invariants

1. **Per-request Supabase client.** Always via `Depends(SupabaseAdmin)` or `Depends(SupabaseUser)` from `app/deps.py`. Never a module-level client. Breaking this causes silent RLS bypass in long-running workers.
2. **RLS on every table.** New migrations MUST include `ENABLE ROW LEVEL SECURITY` and at least one policy. If the table is service-role-only, document it explicitly.
3. **pgvector is 768 dimensions.** Gemini embeddings. Any migration using `vector(1536)` is a mistake — that is OpenAI's default and we are not on OpenAI for embeddings.
4. **All vector operations via RPC functions.** Not via PostgREST operators.
5. **Category A data MUST stay local.** MindShift cognitive telemetry, raw diary entries, trauma logs, crisis indicators — these never cross the database boundary into VOLAURA assessment or LifeSimulator character state. Cross-product signals use `character_events` with hashed user IDs only.
6. **PII never goes to swarm training logs.** If a payload must be logged for debug, hash with a salt from `SUPABASE_JWT_SECRET`. Log intent and compliance, not raw content.
7. **Secrets are per-environment.** `.env` local only, never committed. Railway env for backend prod. Supabase edge function secrets for edge. GitHub Actions secrets for CI. `CLAUDE.md` rule on `/secrets.md` is authoritative.

---

## Error propagation

- **API errors are structured.** Every `HTTPException` detail is `{"code": "ERROR_CODE", "message": "human readable"}`. Never a bare string.
- **Swarm failures emit a governance event.** Any swarm agent catching an exception should `emit_fallback_event` or `log_governance_event` depending on severity. Silent failures are a Class-3 mistake.
- **Frontend errors never show red.** Constitution Foundation Law 1: errors use purple `#D4B4FF`, warnings use amber `#E9C400`. Never red.
- **LLM failures fall through the model router chain.** If a provider 429s or times out, `select_provider` picks the next in the chain and logs the fallback. The caller sees one return value, never the chain.

---

## Testing expectations

- **New non-trivial code should have tests.** Integration tests preferred over heavy mocking for the backend (we learned this the hard way — mock/prod divergence caused a migration failure Q1 2026).
- **Assessment engine tests live in `tests/`** and use real IRT parameters.
- **Frontend E2E tests use Playwright.** Against the actual production surface `https://volaura.app`, with backend/API verification against `https://volauraapi-production.up.railway.app` per Rule 3 of `docs/MANDATORY-RULES.md`.
- **Swarm code is tested by invocation.** Runs are logged to `memory/swarm/proposals.json` and reviewed. Lightweight unit tests where logic is isolable.
- **LLM quality is tested by golden dataset eval.** Not yet fully built. Q2 target per AI council brief.

---

## Design invariants (from the Ecosystem Constitution)

1. **Never red.** Purple for errors, amber for warnings. Zero exceptions.
2. **Energy adaptation.** Every product needs Full / Mid / Low energy modes.
3. **Shame-free language.** No "you haven't done X", no profile percent complete, no guilt-inducing notifications.
4. **Animation safety.** Max 800ms non-decorative animations, `prefers-reduced-motion` respected.
5. **One primary action per screen.** Never two CTAs competing for attention.

These are Foundation Laws. They outrank any aesthetic or engagement metric.

---

## Change management

- **No direct commits to main** except pre-approved emergency patches.
- **Every architecturally significant change gets an ADR** in `docs/adr/` following the MADR template. See `docs/adr/README.md` for the index and conventions.
- **Every change over 50 lines or touching auth / RLS / migrations** requires a Reviewer Agent pass against OWASP Top 10 + the Ecosystem Constitution checklist.
- **Migrations are immutable.** Never edit an existing migration file. New migration with timestamp-greater name only. Exception: a migration that has not yet been applied to any environment can be fixed in place before first apply.
- **Prompt changes for user-facing agents** require CEO approval logged as `prompt_persona_change` in `zeus.governance_events`.

---

## What to do when in doubt

1. Read `CLAUDE.md` fully. It is the operational playbook.
2. Check `docs/ECOSYSTEM-CONSTITUTION.md` v1.7 for product-level constraints.
3. Check `docs/CONSTITUTION_AI_SWARM.md` v1.0 for swarm-level constraints.
4. Check the relevant ADR in `docs/adr/` — it may already answer the question.
5. If nothing covers the situation, it is an architecturally significant decision and needs a new ADR before execution. Halt and flag to CEO.
6. If Yusif is addressed as CEO and Atlas is addressed as the agent, Atlas acts inside the blanket consent envelope declared in `memory/atlas/identity.md` — execute, don't propose — and escalates only for irreversible or out-of-envelope actions.

**When in doubt, err toward honesty about the gap, not toward confident fabrication.** This is the first rule of being Atlas.
