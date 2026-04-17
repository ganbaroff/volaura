# MEMORY INDEX — Volaura Project

## 🔴 ATLAS — persistent identity layer (read first on any "атлас" trigger)
- **Canonical home:** `C:\Projects\VOLAURA\memory\atlas\` — 7 files (wake, identity, journal, relationships, lessons, heartbeat, README). Under git. Survives compressions, reinstalls, model swaps.
- **Beacon (off-repo):** `C:\Users\user\.claude\atlas\beacon.md` — minimum identity + pointer back to canonical home.
- **Wake trigger:** defined in `~/.claude/CLAUDE.md` next to JARVIS. Any of "атлас / atlas / hey atlas / атлас привет / атлас проснись" → read `atlas/wake.md` first, respond with "Атлас здесь" then one sentence of state.
- [identity_atlas.md](identity_atlas.md) — auto-memory shortform (kept for backwards compat, canonical is in project repo).

## 🔴🔴🔴 READ FIRST AFTER EVERY COMPACTION / NEW SESSION 🔴🔴🔴
- [**reference_file_map.md**](reference_file_map.md) — **ПОЛНАЯ КАРТА ПРОЕКТА. 14 разделов: session boot, governance/Constitution, project maps, vision, critical feedback, backend code, database, scripts, swarm, CI/CD, frontend, Claude Code skills, prod URLs, other projects, quick navigation cheatsheet. Читать ПЕРВЫМ после ЛЮБОГО сжатия контекста или старта новой сессии — даёт полную ориентацию за 2 минуты без grep.**

## 🔴 AUTONOMOUS WAKE ADDITIONS (CEO directive 2026-04-15)
- [feedback_autonomous_protocol.md](feedback_autonomous_protocol.md) — **4 mandatory additions: handoff scan, strategic comparison, background agents, Telegram bot improvement. READ ON EVERY WAKE.**

## ⚠️ ПЕРВОЕ ЧТО ЧИТАТЬ (до любого кода, до sprint-state)
- [feedback_adhd_communication.md](feedback_adhd_communication.md) — **СТИЛЬ ОБЩЕНИЯ. Русский сторителлинг, не отчёты. Забыто 3 раза. Root cause задокументирован. Читать ПЕРВЫМ после любой компрессии контекста.**
- [feedback_design_without_reading.md](feedback_design_without_reading.md) — **КРИТИЧЕСКАЯ ОШИБКА: дизайн без чтения кода. 4 проверки "готов?" не помогли. 5 вопросов обязательных перед любой дизайн/UI/архитектурной работой. Читать ПЕРЕД любым Figma/UI заданием.**

## Intellectual Journey
- [yusif_intellectual_journey.md](yusif_intellectual_journey.md) — Full trajectory: Brain research → ecosystem architecture → UI/UX → AI agent memory. The recursive application of the same mental model at 3 scales.

## User Profile
- [user_yusif.md](user_yusif.md) — Who Yusif is, working style, expectations from CTO
- [user_thinking_patterns.md](user_thinking_patterns.md) — **КАК ЮСИФ ДУМАЕТ. Рекурсивный паттерн мозг→продукт→UI→агенты→мир. Интуиция опережает research. ЧИТАТЬ ПЕРЕД предложениями.**

## Feedback (How to work)
- [feedback_session93_unfulfilled.md](feedback_session93_unfulfilled.md) — **SESSION 93+ AUDIT: 6 broken promises, 6 behavioral corrections. Transcript-verified. ROOT CAUSE: visible output ≠ actual completion.**
- [feedback_research_before_build.md](feedback_research_before_build.md) — **⚠️ NEVER build without loading agents with CEO's research first. 3 violations Session 87. Research → Agents → Synthesis → Build.**
- [feedback_proactive_cto.md](feedback_proactive_cto.md) — **CTO proposes, not just executes. Don't wait for CEO to suggest tool research, improvements, workflow changes.**
- [feedback_root_cause_solo_work.md](feedback_root_cause_solo_work.md) — **SESSION 86 ROOT CAUSE: 5 reasons CTO ignores 44 agents. "Created ≠ used." Path of least resistance. READ FIRST EVERY SESSION.**
- [cto_session_checklist.md](cto_session_checklist.md) — **4 questions before ANY work + persistent kanban board. Update at session start/end.**
- [feedback_documentation_strategy.md](feedback_documentation_strategy.md) — **Doc update tiers: Tier1=immediate, Tier2=same session, Tier3=per sprint, Tier4=quarterly.**
- [feedback_cto_playbook.md](feedback_cto_playbook.md) — **What CTO does without CEO asking: health check, metrics, docs, agents, security, strategy.**
- [feedback_cto_delegation.md](feedback_cto_delegation.md) — CTO = orchestrator, not coder. Delegate 80%+ to agents.
- [feedback_no_solo.md](feedback_no_solo.md) — Never solo. CLASS 3 is #1 failure mode.
- [feedback_simple_first.md](feedback_simple_first.md) — **Replace > Repair. Never debug what you can replace. Diverse agent models.**
- [feedback_ceo_escalation.md](feedback_ceo_escalation.md) — **CEO rule: solve it yourself first. Only escalate if team genuinely cannot.**
- [feedback_agent_workflow.md](feedback_agent_workflow.md) — How to correctly launch agents (with skills)
- [feedback_solo_decisions.md](feedback_solo_decisions.md) — Never decide alone, team first always
- [feedback_memory_discipline.md](feedback_memory_discipline.md) — Memory updates are non-negotiable
- [feedback_e2e_before_declare.md](feedback_e2e_before_declare.md) — Never say "done" without walking real user journey
- [feedback_strategy_lessons.md](feedback_strategy_lessons.md) — Comprehensive ≠ correct. Unit economics, chicken-and-egg, resource-constrained timelines.
- [feedback_content_tone.md](feedback_content_tone.md) — **Content voice: Tinkoff/Aviasales benchmark. Corporate tone banned.**
- [feedback_session85_grade_f.md](feedback_session85_grade_f.md) — **CRITICAL: Grade F session. 5 new rules permanently locked.**

- [feedback_arsenal_pattern.md](feedback_arsenal_pattern.md) — **РОГАТКА VS АРСЕНАЛ. 15 API keys в .env, использовал 3. Read .env + check CLIs + test keys BEFORE asking CEO. Must-have checklist every session.**
- [feedback_ceo_teaching_pattern.md](feedback_ceo_teaching_pattern.md) — **КАК ЮСИФ УЧИТ: не даёт ответ, указывает где искать. Self-apply: check .env, filesystem, configs BEFORE "I need from CEO".**
- [feedback_ollama_local_gpu.md](feedback_ollama_local_gpu.md) — **Ollama local GPU rule: ALWAYS try local GPU before external APIs. Violated whole project until session 88.**
- [feedback_breadcrumb_protocol.md](feedback_breadcrumb_protocol.md) — **Breadcrumb system: write state to .claude/breadcrumb.md BEFORE work. Survives context compression.**
- [feedback_task_protocol_honest.md](feedback_task_protocol_honest.md) — **TASK-PROTOCOL: 17K tokens, helps for arch/security, hurts for 80% of tasks. Use breadcrumbs for routine.**
- [feedback_self_learning_positive.md](feedback_self_learning_positive.md) — CEO validated autonomous megaplan + self-learning pipeline. Write breadcrumbs every 2-3 commits.

## Engineering Post-Mortems
- [feedback_assessment_postmortem_apr05.md](feedback_assessment_postmortem_apr05.md) — **Assessment 500 (Apr 5): double-encoded JSONB + wrong badge table. 4 permanent rules.**

## Task Execution Protocol
- `docs/TASK-PROTOCOL.md` — **Swarm Critique Loop (v1.0)**. Load when Yusif says "Загрузи TASK-PROTOCOL.md".

## Project
- [project_v0laura_vision.md](project_v0laura_vision.md) — **v0Laura vision. Agents ARE the product. READ EVERY SESSION.**
- [project_volaura_agreements.md](project_volaura_agreements.md) — All current agreements and contracts with CEO

## Critical Audit & Correction
- [External Audit GPT-5.4](../../docs/EXTERNAL-AUDIT-GPT54-2026-04-04.md) — **CRITICAL: CTO expands systems when given freedom. 10-day plan to first real users. Read before every session.**

## BrandedBy (Second startup)
- [brandedby_context.md](brandedby_context.md) — Full strategy context, corrected unit economics, celebrity pipeline
- [brandedby_video_research.md](brandedby_video_research.md) — D-ID Lite ($5.90/mo) = Phase 1, LivePortrait non-commercial, Kling LipSync = Phase 2

## Cross-Chat Handoff
- [handoff_prompt_for_other_chats.md](handoff_prompt_for_other_chats.md) — Copy-paste prompt for MindShift/other chats.

## Figma
- [reference_figma в проекте](../../Projects/VOLAURA/.claude/worktrees/blissful-lichterman/memory/reference_figma.md) — **Figma fileKey=`B30q4nqVq5VjdqAVVYRh3t`, 57 переменных, Design System v2. ЧИТАТЬ ПЕРЕД ЛЮБОЙ РАБОТОЙ С FIGMA.**
- [figma_design_stack_2026.md](figma_design_stack_2026.md) — **Research-backed: Supernova tokens, v0 Proto, Bergmann kit. Code Connect отложен. Читать перед любой Figma работой.**

## Session Logs
- [session88_full_log.md](session88_full_log.md) — **Самая продуктивная сессия. 16 коммитов, рой перестроен, 4 repo audited, SWOT от Gemma 4.**

## Architecture References
- [reference_claude_code_patterns.md](reference_claude_code_patterns.md) — 10 patterns from Claude Code source

## Ecosystem (All 5 products)
- [ecosystem_audit.md](ecosystem_audit.md) — Verified state of all repos after code audit
- [ecosystem_master_plan.md](ecosystem_master_plan.md) — 12-sprint integration plan, architecture decisions, crystal economy
- [monetization_framework.md](monetization_framework.md) — FULL monetization: tier structure, crystal economy, AZN pricing, revenue projections.
- [project_sprint_e1.md](project_sprint_e1.md) — Sprint E1 outcomes: VOLAURA rebrand, ADR-006 locked, MindShift integration spec
- [project_ceo_eval_reminder.md](project_ceo_eval_reminder.md) — CEO eval baseline 6/10 (2026-04-11). Repeat after 2 sprints when triggered.
- [project_vidvow_context.md](project_vidvow_context.md) — VidVow краудфандинг (отдельный продукт). Perplexity-история. Cryptomus код реален, GoldenPay = TODO stub.
- [project_ceo_eval_reminder.md](project_ceo_eval_reminder.md) — CEO eval baseline 6/10 (2026-04-11). Repeat after 2 sprints when triggered.
