# UNFULFILLED PROMISES — CTO Debt Register

**Created:** 2026-04-04
**Purpose:** Track everything CTO promised but did not deliver. CEO checks this.
**Rule:** Items leave this list ONLY when DONE and VERIFIED (not "started" or "planned").

| # | Promise | When | Status | Blocker |
|---|---------|------|--------|---------|
| 1 | Dodo Payments integration code | Session 83 | Waiting | CEO activates when company verified |
| 2 | CrewAI Phase 1 (Sprint Gate DSP) | ADR-009 | pip installed, 0 code | CTO chose other tasks |
| 3 | ClawOffice 3D agent office | Session 83 | Research only | Deferred to ZEUS product |
| 4 | Content factory (LinkedIn auto-publish) | Session 83 | Discussed | No LinkedIn API setup |
| 5 | Piper TTS (local, replace edge-tts) | Session 83 | Not installed | CTO forgot |
| 6 | MindShift REST API bridge | Session 83 | Architecture only | Different Supabase projects |
| 7 | 14 uncategorized agents cleanup | Session 83 | Started, stopped | CEO redirected |
| 8 | Customer Success agent (33L skeleton) | Session 83 | Skeleton | Not fleshed out |
| 9 | Onboarding Specialist agent (32L skeleton) | Session 83 | Skeleton | Not fleshed out |
| 10 | Trend Scout daily cron verification | Session 83 | Created | Never verified it runs |
| 11 | k6 load testing scripts | 500h plan | Zero | Never started |
| 12 | Playwright E2E tests | 500h plan | Zero | Never started |
| 13 | Staging environment | 500h plan | Zero | Never started |
| 14 | Community/Discord chat | Original brief | Zero | Deferred |
| 15 | Variable rewards / mystery drops | Original brief | Zero | Deferred |
| 16 | Push notifications (mobile) | Launch blocker | Zero | Not started |
| 17 | Email lifecycle (welcome, digest) | Identified | Zero | Not started |
| 18 | Dynamic OG image link in share flow | OG card exists | Not wired | Partially done |
| 19 | Langfuse traces verification | Keys set | Not verified | CTO didn't check |
| 20 | Telegram bot end-to-end test | Webhook fixed | Not verified | CTO didn't test |

---

## Session 91 additions (2026-04-07)

| # | Promise | When | Status | Blocker |
|---|---------|------|--------|---------|
| 21 | Telegram digest CEO actual receipt | Session 91 | API ok:True ×2, message_id 1042. **CEO never /start'ed bot** — bot can't send to user without first message from user. Item #20 manifestation. | CEO must open https://t.me/volaurabot and press /start |
| 22 | Telegram Mini App live in bot Menu Button | Session 91 | apps/tg-mini built (dist/), .vercel/project.json linked, **NOT deployed**, Bot config `has_main_web_app: false` | Run `cd apps/tg-mini && vercel --prod` + @BotFather → Menu Button → URL |
| 23 | scripts/execute_proposal.py (Sprint S1 Step 7) | Session 91 | NOT BUILT. 62 proposals approved in proposals.json, 0 implemented. Pipeline `approved → diff → PR` missing. | Next chat: build ~150 lines Python |
| 24 | Squad routing keyword fix | Session 91 | Bug: "audit security of signup flow" → routes to PRODUCT (matches "signup/flow") instead of QUALITY+SECURITY. Discovered when testing --mode=coordinator. | Add `security/audit/vulnerability` keywords to QUALITY squad in squad_leaders.py |
| 25 | asyncio.run() from running event loop bug | Session 91 | autonomous_run.py:1170 calls suggestion_engine.generate_suggestions which internally asyncio.run() inside already-running event loop → RuntimeError. Marked "non-blocking" but suggestion engine never runs. | Refactor generate_suggestions to async + await |
| 26 | AURA scoreMeaning_justStarting fix | Session 91 | Fix applied to worktree (3 files), NOT committed, NOT pushed to main, NOT deployed | Next chat: cd worktree && git add + commit + push to claude/blissful-lichterman + PR |
| 27 | Vertex/Gemini judge fallback | Session 91 | autonomous_run uses Vertex for judge_proposal — fails 429 RESOURCE_EXHAUSTED daily quota. No fallback. | Add Cerebras/Groq fallback to _judge_proposal function |
| 28 | CLAUDE.md refactor (750 lines → 150) | Session 91 | MindShift-Claude analysis: "Убить CLAUDE.md и пересоздать до 150 строк. 2000 строк — гарантия что файл не читается." | Split CLAUDE.md into core (150 lines) + 5 referenced docs |
| 29 | Agent-first check in protocol-enforce.sh | Session 91 | MindShift-Claude recommendation: before each Edit/Write hook should ask "Какой агент это делает? (или solo: причина)" | Add to protocol-enforce.sh |
| 30 | Delegation rate metric in session-end-check.sh | Session 91 | MindShift-Claude rec: track "Tasks delegated to agents: X / Total tasks: Y → goal >60%" | Add to session-end-check.sh |
| 31 | External evaluation every 3 sessions | Session 91 | MindShift-Claude rec: Gemini + DeepSeek audit, not Claude self-eval. CEO-EVALUATION.md exists but not used. | Schedule via swarm-daily.yml cron |
| 32 | Per-project Q&A agent for MindShift / Life Sim / BrandedBy / ZEUS | Session 91 | scripts/project_qa.py BUILT for VOLAURA (verified live, 384 files indexed, Kimi K2 answers in 3.4s). NOT yet copied to other 4 projects. | Copy script to each project, adjust PROJECT_ROOT auto-detection |
| 33 | mem0 cross-chat memory failed write retry | Session 91 | 1 of 4 mem0 add_memory calls failed with Cloudflare 520. The 12 critical rules memory was lost. | Retry next chat when mem0 server back |
| 34 | Wave 2 internal agent reports — final findings | Session 88+ | CTO read top of agent-feedback-distilled.md but never the Wave 2 final findings sections. MindShift-Claude noted this gap. | Read full memory/swarm/agent-feedback-distilled.md |
| 35 | Ecosystem Constitution v1.7 final text — full read | Session 91 | CTO knows Article 0 + 5 Foundation Laws + Crystal Laws but never read full 85KB ECOSYSTEM-CONSTITUTION.md cover-to-cover. MindShift-Claude noted this gap. | Read full file in chunks via project_qa.py or direct |
| 36 | Everything after PR 11 / Session 88 — full review | Session 91 | CTO reads sprint-state.md + SHIPPED.md latest entries but never PRs 11 → 18 commit-by-commit. MindShift-Claude noted this gap. | `git log main --since="2026-04-01"` and read each merge |
| 37 | "Театр vs механика" — 4 instances unfixed | Session 91 (MindShift-Claude analysis) | (1) coordinator.py created — bypassed. FIXED Session 91 (verified --mode=coordinator works). (2) 48 skill files routed by names not content — UNFIXED. (3) Hooks sometimes don't fire — Stop hook v4 fixed; others not audited. (4) Grade F lessons recurring — UNFIXED structurally. | Audit each, fix 2/3 next chat |

---

## Sprint S1 SHIPPED (Session 91 — these are NOT broken promises, they're DONE)

| # | What | Verification |
|---|------|--------------|
| S1 | scripts/swarm_agent.py multi-provider wrapper | Smoke test 6 models, 3 reliable |
| S2 | scripts/dsp_debate.py 3-model parallel cross-critique | Tested on AURA bug fix, 4.8s, 5738 tokens |
| S3 | autonomous_run.py LIVE end-to-end | First run 20:03, second run 20:13, both Health GREEN, 8 proposals each |
| S4 | --mode=coordinator squad routing | Tested live, 1 finding [P1] Security vulnerability |
| S5 | scripts/project_qa.py per-project Q&A agent | 384 files indexed, Kimi K2 answers in 3.38s, sources cited |
| S6 | Stop hook v4 (stderr + full-turn + system-reminder isolation) | 4 test scenarios pass |
| S7 | jarvis-wake.sh wake phrase auto-injection | Registered in settings.local.json UserPromptSubmit chain |
| S8 | Cerebras key saved to apps/api/.env (3rd time CEO gave) | grep verifies |
| S9 | swarm-daily.yml + PYTHONIOENCODING=utf-8 | env section updated |
| S10 | Unicode ✓/✗/⚠ → ASCII [OK]/[FAIL]/[WARN] in autonomous_run.py | Committed `f05637a` to main |
| S11 | Documentation: sprint-state + SHIPPED + mistakes (#86-#91) + patterns + breadcrumb | All 5 files updated |
| S12 | mem0 cross-chat persistence | 3 of 4 memories saved (1 failed Cloudflare 520) |
| S13 | LESSONS-LEARNED-SESSION-91.md (~24KB) + HANDOFF-SESSION-91.md (~12KB) | Files created in docs/ |
