---
name: VOLAURA file map — все важные линковки в одном месте
description: Полная карта критичных файлов проекта. Читать при каждой сессии для быстрой ориентации. Обновлять когда появляются новые ключевые файлы.
type: reference
originSessionId: 15299306-4582-4c3f-b635-40127687fa18
---
# VOLAURA — File Map (2026-04-11, Session 93)

Всё что важно, в одном списке. Читается за 2 минуты, даёт полную ориентацию без grep'а.

---

## 0. Session Boot — читать ПЕРВЫМ на старте сессии

| Файл | Зачем |
|---|---|
| `C:\Projects\VOLAURA\.claude\breadcrumb.md` | Где мы ПРЯМО СЕЙЧАС. Last commit, что сделано, что дальше. Обновляется в конце каждой сессии. |
| `C:\Projects\VOLAURA\memory\context\sprint-state.md` | Current sprint + Next Session Priorities. Gitignored, локальный. |
| `C:\Projects\VOLAURA\memory\context\mistakes.md` | Что НЕ повторять. CLASS 1-12 ошибки, последние 30 строк читать всегда. |
| `C:\Projects\VOLAURA\memory\context\patterns.md` | Что работает. Applied patterns. |
| `C:\Projects\VOLAURA\memory\swarm\SHIPPED.md` | Единственный source of truth "какой код существует на проде". CTO читает ПЕРВЫМ перед любой работой (правило после Session 51 missing builds). |
| `C:\Projects\VOLAURA\docs\DECISIONS.md` | Ретроспективы + ADR trail. |

---

## 1. Governance — Supreme Law

| Файл | Зачем |
|---|---|
| `C:\Projects\VOLAURA\docs\ECOSYSTEM-CONSTITUTION.md` | **v1.2/v1.7**, 1156 строк. 5 Foundation Laws (no red, energy, shame-free, animation, one action) + 8 Crystal Laws + Research-based design rules. Supersedes CLAUDE.md при конфликте. |
| `C:\Projects\VOLAURA\CLAUDE.md` | Project instructions. Article 0 указывает на Constitution. Operating Algorithm v3.0. Rules + Skills Matrix. |
| `C:\Projects\VOLAURA\docs\MANDATORY-RULES.md` | 7 non-negotiable rules, читать при каждом sprint start. |
| `C:\Projects\VOLAURA\.claude\rules\backend.md` | FastAPI patterns — per-request Supabase, Pydantic v2, loguru. |
| `C:\Projects\VOLAURA\.claude\rules\frontend.md` | Next.js 14 App Router, i18n AZ/EN, Tailwind v4. |
| `C:\Projects\VOLAURA\.claude\rules\database.md` | Migrations, RLS patterns, pgvector 768-dim (не 1536). |
| `C:\Projects\VOLAURA\.claude\rules\secrets.md` | Key recognition + immediate save protocol. |
| `C:\Projects\VOLAURA\.claude\rules\ceo-protocol.md` | Когда звать CEO, когда НЕ звать. Outcome-only reporting. |
| `C:\Users\user\.claude\CLAUDE.md` | Global user instructions. Caveman mode rules. JARVIS trigger. Ruflo MCP hint. |
| `C:\Users\user\.claude\rules\research-first.md` | 4-level depth ladder (surface → real usage → source → landscape). NEVER build without research. |

---

## 2. Project Maps — что где живёт

| Файл | Зачем |
|---|---|
| `C:\Projects\VOLAURA\README.md` | One-page overview. 5 products table, quick start, live URLs. |
| `C:\Projects\VOLAURA\docs\ECOSYSTEM-MAP.md` | 5-product architecture, shared Supabase, data flows, crystal economy, shared secrets. |
| `C:\Projects\VOLAURA\docs\RUNBOOK.md` | Local setup, required ENV vars, deploy steps, health check. |
| `C:\Projects\VOLAURA\docs\CONTRIBUTING.md` | Commit style, PR process, code rules NEVER/ALWAYS. |
| `C:\Projects\VOLAURA\memory\swarm\shared-context.md` | Consolidated swarm knowledge, updated by session-end.yml. |
| `C:\Projects\VOLAURA\memory\swarm\ECOSYSTEM-MAP.md` | Swarm's own map of the 5-product ecosystem (separate from docs/ one). |
| `C:\Projects\VOLAURA\packages\swarm\memory\ECOSYSTEM-MAP.md` | Constitution summary + routing table injected into every agent run. |

---

## 3. Vision & Identity — кто мы и зачем

| Файл | Зачем |
|---|---|
| `C:\Users\user\.claude\projects\C--Projects-VOLAURA\memory\project_v0laura_vision.md` | **v0Laura truth** — agents ARE the product, not backend workers. `POST /api/skills/{name}` is the engine. Читать каждую сессию. |
| `C:\Users\user\.claude\projects\C--Projects-VOLAURA\memory\yusif_intellectual_journey.md` | Brain research → ecosystem → UI → agents → world. Рекурсивный паттерн мышления. |
| `C:\Users\user\.claude\projects\C--Projects-VOLAURA\memory\user_yusif.md` | Profile, ADHD rules, communication style, expectations. |
| `C:\Users\user\.claude\projects\C--Projects-VOLAURA\memory\user_thinking_patterns.md` | Как Юсиф думает — интуиция опережает research. |
| `C:\Projects\VOLAURA\memory\context\working-style.md` | Project-level dup of above. Speed, mindset, communication, decision patterns. |
| `C:\Users\user\.claude\projects\C--Projects-VOLAURA\memory\project_volaura_agreements.md` | Текущие договорённости с CEO. |
| `C:\Users\user\.claude\projects\C--Projects-VOLAURA\memory\project_ceo_eval_reminder.md` | CEO eval baseline 6/10 (2026-04-11). Trigger через 2 спринта. |

---

## 4. Critical Feedback — чему научились (auto-memory)

⚠️ Эти файлы читать ПЕРЕД любой не-тривиальной работой. Они существуют потому что ошибка была повторена.

| Файл | Суть |
|---|---|
| `feedback_adhd_communication.md` | Russian storytelling, не bullet reports. Забыто 3 раза. Читать ПЕРВЫМ после компрессии. |
| `feedback_design_without_reading.md` | 5 обязательных вопросов перед дизайн/UI работой. |
| `feedback_research_before_build.md` | Research → Agents → Synthesis → Build. NEVER solo build. |
| `feedback_proactive_cto.md` | CTO proposes, не ждёт указаний. |
| `feedback_root_cause_solo_work.md` | 5 причин почему CTO игнорирует 44 агентов. Path of least resistance. |
| `feedback_no_solo.md` | CLASS 3 = #1 failure mode. 15 instances. |
| `feedback_simple_first.md` | Replace > Repair. Diverse agent models. |
| `feedback_ceo_escalation.md` | Solve yourself first. Only escalate if team cannot. |
| `feedback_e2e_before_declare.md` | Никогда "done" без walkthrough реального user journey. |
| `feedback_memory_discipline.md` | Memory updates non-negotiable. |
| `feedback_ollama_local_gpu.md` | ALWAYS try local GPU first before external APIs. |
| `feedback_breadcrumb_protocol.md` | Write state BEFORE work, survives compression. |
| `feedback_task_protocol_honest.md` | TASK-PROTOCOL 17K tokens — для arch/security only. Breadcrumbs для routine. |
| `feedback_no_premature_users.md` | **STOP saying "нужны реальные пользователи"** — CEO deliberately holding them. CEO decides when. |
| `feedback_session85_grade_f.md` | 5 permanent rules. F-grade session. |
| `feedback_assessment_postmortem_apr05.md` | Double-encoded JSONB + wrong badge table. 4 permanent rules. |
| `cto_session_checklist.md` | 4 questions + kanban. Update at session start/end. |
| `feedback_cto_playbook.md` | What CTO does без CEO asking: health, metrics, docs, agents, security, strategy. |
| `feedback_cto_delegation.md` | CTO = orchestrator, не coder. 80%+ delegate. |
| `feedback_strategy_lessons.md` | Comprehensive ≠ correct. Unit economics, chicken-and-egg. |

Все лежат в `C:\Users\user\.claude\projects\C--Projects-VOLAURA\memory\`.

---

## 5. Backend Code — FastAPI entry points

| Файл | Зачем |
|---|---|
| `C:\Projects\VOLAURA\apps\api\app\main.py` | FastAPI app, middleware chain, global error handler (`INTERNAL_ERROR` line 145). |
| `C:\Projects\VOLAURA\apps\api\app\config.py` | Settings, ENV vars, provider keys (Gemini, Groq, OpenAI, Supabase). |
| `C:\Projects\VOLAURA\apps\api\app\deps.py` | `SupabaseAdmin`, `SupabaseUser`, `CurrentUserId` — ALWAYS per-request. |
| `C:\Projects\VOLAURA\apps\api\app\routers\auth.py` | Register (email confirm required), login. |
| `C:\Projects\VOLAURA\apps\api\app\routers\auth_bridge.py` | **POST /api/auth/from_external** — MindShift → VOLAURA. Session 93 fix: creates profiles row. |
| `C:\Projects\VOLAURA\apps\api\app\routers\assessment.py` | start / answer / complete. Session 93 fix: submit_answer не pre-marks completed. |
| `C:\Projects\VOLAURA\apps\api\app\routers\aura.py` | /api/aura/me — AURA score + tier. Public read policy. |
| `C:\Projects\VOLAURA\apps\api\app\routers\character.py` | character_events для crystal economy. Uses SupabaseUser (bridged JWT). |
| `C:\Projects\VOLAURA\apps\api\app\routers\skills.py` | v0Laura engine — POST /api/skills/{name}. Line 6 документирует truth. |
| `C:\Projects\VOLAURA\apps\api\app\routers\zeus_gateway.py` | /api/zeus/proposal — Python swarm → Railway bridge. |
| `C:\Projects\VOLAURA\apps\api\app\core\assessment\engine.py` | IRT/CAT 3PL + EAP. `theta_to_score`, `should_stop`, `select_next_item`. |
| `C:\Projects\VOLAURA\apps\api\app\core\assessment\antigaming.py` | Gaming flags + penalty multiplier. |
| `C:\Projects\VOLAURA\apps\api\app\services\reeval_worker.py` | LLM re-eval of degraded answers. Calls upsert_aura_score. |
| `C:\Projects\VOLAURA\apps\api\app\schemas\assessment.py` | StartAssessment / SubmitAnswer / SessionOut / AssessmentResultOut. |

---

## 6. Database — Supabase

| Путь | Зачем |
|---|---|
| `C:\Projects\VOLAURA\supabase\migrations\` | Все миграции. Формат `YYYYMMDDHHMMSS_description.sql`. |
| `...20260321000002_create_profiles.sql` | profiles — FK target для всего. `id REFERENCES auth.users(id)`, username UNIQUE NOT NULL. |
| `...20260321000005_create_assessment_sessions.sql` | volunteer_id REFERENCES profiles(id). RLS: auth.uid() = volunteer_id. |
| `...20260321000006_create_aura_scores.sql` | UNIQUE volunteer_id. Public SELECT policy. |
| `...20260321000012_create_rpc_functions.sql` | calculate_aura_score (weights: communication 0.20, reliability 0.15, ...). get_badge_tier (platinum≥90, gold≥75, silver≥60, bronze≥40). |
| `...20260327190500_fix_upsert_aura_merge_competencies.sql` | upsert_aura_score SECURITY DEFINER — merges existing competency_scores. |
| `...20260408000001_user_identity_map.sql` | Bridge mapping (standalone_user_id, standalone_project_ref) → shared_user_id. find_shared_user_id_by_email RPC. |
| `...20260409000001_health_data_firewall.sql` | Cross-product data isolation. |
| `C:\Projects\VOLAURA\supabase\seed.sql` | Dev seed — 8 competencies, sample IRT questions. |

**Shared Supabase project:** `dwdgzfusjsobnixgyzjk` (VOLAURA + cross-product bridge)
**MindShift Supabase:** `awfoqycoltvhamtrsvxk` (separate, bridged via edge function `volaura-bridge-proxy`)

---

## 7. Scripts — incident response + verification toolkit

| Файл | Зачем |
|---|---|
| `C:\Projects\VOLAURA\scripts\prod_smoke_test.py` | Health + auth-gate smoke. 10/10 checks infra only, не user journey. |
| `C:\Projects\VOLAURA\scripts\prod_smoke_e2e.py` | **Session 93 NEW** — real user journey через bridge → assessment → AURA. Поймал 2 прод бага. |
| `C:\Projects\VOLAURA\scripts\debug_aura_rpc.py` | **Session 93 NEW** — admin-direct upsert_aura_score test. Изолирует "RPC broken" vs "complete endpoint broken". |
| `C:\Projects\VOLAURA\scripts\audit_assessment_state.py` | **Session 93 NEW** — quantifies impact of Session 93 bugs. `--backfill` re-runs RPC for orphaned sessions. |
| `C:\Projects\VOLAURA\scripts\cleanup_smoke_test_users.py` | **Session 93 NEW** — deletes rows owned by Session 93 scripts only. Safe for MindShift fixtures. |
| `C:\Projects\VOLAURA\scripts\project_qa.py` | Q&A index of project (1207-file keyword index). |
| `C:\Projects\VOLAURA\scripts\audit_seed_questions.py` | Seed validation for IRT parameters + keyword coverage. |

---

## 8. Swarm System — the operating system

| Файл / путь | Зачем |
|---|---|
| `C:\Projects\VOLAURA\packages\swarm\autonomous_run.py` | Main swarm entry. 8 perspectives + CTO watchdog + Ecosystem auditor. --mode=code-review для post-push. |
| `C:\Projects\VOLAURA\packages\swarm\engine.py` | Agent runner. Injects ECOSYSTEM-MAP.md + Global_Context.md + Constitution compliance report. |
| `C:\Projects\VOLAURA\packages\swarm\tools\code_tools.py` | read_file, grep_codebase, search_code_index (1207-file index). |
| `C:\Projects\VOLAURA\packages\swarm\tools\constitution_checker.py` | Live Law 1-5 + Crystal Law scan. |
| `C:\Projects\VOLAURA\packages\swarm\tools\deploy_tools.py` | check_production_health, run_typescript_check, check_git_status. |
| `C:\Projects\VOLAURA\packages\swarm\social_reaction.py` | `simulate_reactions()` — MANDATORY before LinkedIn publish. |
| `C:\Projects\VOLAURA\memory\swarm\proposals.json` | **Canonical proposals** (gitignored). Structure: `{schema_version, description, proposals: [...]}`. Statuses lowercase. |
| `C:\Projects\VOLAURA\memory\swarm\ceo-inbox.md` | HIGH/CRITICAL escalations для CEO. |
| `C:\Projects\VOLAURA\memory\swarm\agent-roster.md` | 44 agents + scores + routing "When to Call" table. |
| `C:\Projects\VOLAURA\memory\swarm\agent-pairings-table.md` | Tier 1/2 mandatory agent pairs per task type. |
| `C:\Projects\VOLAURA\memory\swarm\skills\` | 48 skill files. Each has ## Trigger + ## Output. |
| `C:\Projects\VOLAURA\memory\swarm\career-ladder.md` | Agent promotions/demotions. |
| `C:\Projects\VOLAURA\memory\swarm\skill-evolution-log.md` | Skill file change history. |
| `C:\Projects\VOLAURA\memory\swarm\daily-health-log.md` | Daily swarm run outputs. |
| `C:\Projects\VOLAURA\memory\swarm\task_ledger.jsonl` | Unified agent activity registry (commit aa7e9aa). |

---

## 9. CI/CD — GitHub Actions

| Файл | Зачем |
|---|---|
| `C:\Projects\VOLAURA\.github\workflows\ci.yml` | Type check + pytest + lint on every PR. |
| `C:\Projects\VOLAURA\.github\workflows\swarm-daily.yml` | Daily 05:00 UTC (09:00 Baku). 5 agents → proposals.json. |
| `C:\Projects\VOLAURA\.github\workflows\session-end.yml` | **Git-diff injection** (L1 из sprint-state — DONE). On push to main: SESSION-DIFFS.jsonl append + shared-context.md rebuild + code-index rebuild + mini-swarm review. |
| `C:\Projects\VOLAURA\.github\workflows\post-deploy-agent.yml` | Post-deploy verification. |
| `C:\Projects\VOLAURA\.github\workflows\swarm-adas.yml` | Adversarial swarm runs. |
| `C:\Projects\VOLAURA\.github\workflows\analytics-retention.yml` | Retention metrics cron. |
| `C:\Projects\VOLAURA\.github\workflows\tribe-matching.yml` | Tribe matching cron. |
| `C:\Projects\VOLAURA\.github\workflows\zeus-content.yml` | ZEUS content cron. |

---

## 10. Frontend — Next.js 14 App Router

| Путь | Зачем |
|---|---|
| `C:\Projects\VOLAURA\apps\web\src\app\[locale]\` | App Router pages. Все роуты `/${locale}/path`. |
| `C:\Projects\VOLAURA\apps\web\src\components\features\` | Feature components (composed from shadcn/ui base). |
| `C:\Projects\VOLAURA\apps\web\src\stores\` | Zustand stores. |
| `C:\Projects\VOLAURA\apps\web\src\lib\api\generated\` | @hey-api/openapi-ts generated SDK. Run `pnpm generate:api` after backend schema change. |
| `C:\Projects\VOLAURA\apps\web\src\lib\supabase\client.ts` | Browser Supabase client. |
| `C:\Projects\VOLAURA\apps\web\src\lib\supabase\server.ts` | Server Component Supabase client. |

---

## 11. Claude Code Skills — global (`~/.claude/skills/`)

| Skill | Зачем |
|---|---|
| `jarvis` | **Boot protocol**. Trigger: "хей джарвис" / "jarvis" / "boot". 7 шагов. |
| `skill-router` | Keyword → skill auto-load mapping. |
| `decision-toolkit` | DSP support. |
| `deep-research` | Multi-source research compiler. |
| `notebooklm` | NotebookLM integration for deep sourced research. |
| `fastapi-best-practices` | Backend patterns. |
| `pydantic-v2` | Schema validation. |
| `nextjs-app-router` | Frontend patterns. |
| `tailwind-v4` | Styling. |
| `railway-deployment` | Deploy to Railway. |
| `gemini-api-dev` | Gemini integration. |
| `sentry-commit` / `sentry-code-review` | Commit + review via Sentry. |
| `post` | LinkedIn / content publish flow. |
| `awesome-agent-skills` | Skill discovery. |

---

## 12. Production — live URLs & secrets (references, не сами значения)

| Service | URL / Ref |
|---|---|
| API | `https://volauraapi-production.up.railway.app` |
| Frontend | `https://volaura.app` |
| Supabase shared | `dwdgzfusjsobnixgyzjk.supabase.co` |
| Supabase MindShift | `awfoqycoltvhamtrsvxk.supabase.co` |
| GitHub repo | `ganbaroff/volaura` |
| Telegram bot | `@volaurabot` |

**Secret names** (значения в `apps/api/.env` локально + Railway + Supabase edge secrets):
- `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_JWT_SECRET`
- `EXTERNAL_BRIDGE_SECRET` (Railway + MindShift edge fn)
- `GATEWAY_SECRET` (Railway + local ZEUS)
- `GEMINI_API_KEY`, `GROQ_API_KEY`, `OPENAI_API_KEY`
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CEO_CHAT_ID`

---

## 13. Other Projects (same user, separate repos)

| Project | Path | Status |
|---|---|---|
| VidVow crowdfunding | `C:\Users\user\Downloads\vidvow` | Orphaned prod-grade. React 19 + Hono + Cloudflare Workers + D1. Real Cryptomus USDT code, Stripe real, GoldenPay TODO stub. Context: `memory/project_vidvow_context.md`. |
| MindShift | (separate repo) | Live at mindshift.app. Next.js + Capacitor + Supabase `awfoqycoltvhamtrsvxk`. Bridges to VOLAURA via `volaura-bridge-proxy` edge fn. |
| Life Simulator | `life-simulator-2026` branch master | Godot 4. volaura_login_screen.tscn ready (Session 92). |
| BrandedBy | (same monorepo, brandedby router) | Dev. D-ID Lite Phase 1 planned. |
| ZEUS | `packages/swarm/` + local ngrok | Gateway running locally, exposed via ngrok. |

---

## 14. Quick Navigation Cheatsheet

Чтобы не grep'ать каждый раз:

- **"Что сейчас происходит?"** → `.claude\breadcrumb.md` + `memory\context\sprint-state.md`
- **"Какой код есть на проде?"** → `memory\swarm\SHIPPED.md`
- **"Можно ли делать Х?"** → `docs\ECOSYSTEM-CONSTITUTION.md` + `docs\MANDATORY-RULES.md`
- **"Есть ли такой баг уже?"** → `memory\context\mistakes.md`
- **"Есть ли такой паттерн?"** → `memory\context\patterns.md`
- **"Какой агент на это?"** → `memory\swarm\agent-roster.md` + `memory\swarm\agent-pairings-table.md`
- **"Какая схема БД?"** → `supabase\migrations\` — искать по таблице
- **"Какой endpoint?"** → `apps\api\app\routers\` — имя файла = router prefix
- **"Кто такой Юсиф?"** → `user_yusif.md` + `user_thinking_patterns.md` + `yusif_intellectual_journey.md`
- **"Что за v0Laura?"** → `project_v0laura_vision.md` — agents ARE the product
- **"Почему не звать юзеров?"** → `feedback_no_premature_users.md`
- **"Почему не solo?"** → `feedback_no_solo.md` + `feedback_root_cause_solo_work.md`

---

## Maintenance rule

Этот файл обновляется **когда:**
- Появляется новый critical feedback файл в auto-memory
- Меняется архитектура (новый router, новая таблица-FK target, новый workflow)
- Добавляется продукт в ecosystem
- Перемещается/удаляется что-то из разделов 1-10

**НЕ обновляется** на каждый мелкий commit. Stale OK для 1-2 недель. Главное — точки входа верные.
