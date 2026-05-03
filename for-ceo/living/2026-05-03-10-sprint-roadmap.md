# 2026-05-03 — 10-Sprint Roadmap (Atlas, Session 132)

**CEO directive (decoded from "yfgbib gkfy yf 10 cghbynjd mistakes adr bax yaxshi?"):**
"Напиши план на 10 спринтов. Mistakes ADR. Посмотри (на них) хорошо?"

**Source materials read this turn:** `memory/atlas/lessons.md` (full, 27 classes), `mistakes_and_patterns_distilled.md` (12 classes, 20 patterns, 5 recurring), ADR-006/007/008/010, `swarm-commands.md`, `breadcrumb.md`, `heartbeat.md`. Strange v2 protocol from `atlas-operating-principles.md`.

**Format per sprint:** Question → Evidence → Contradiction → Root Cause → Guardrail → Re-test → Scale. Strange v2 RECOMMENDATION/EVIDENCE/WHY NOT/FALLBACK/ADVERSARIAL collapsed into Root Cause and Guardrail sections to keep the file readable. External-model adversarial pass per Strange Gate 1 not run for this roadmap (Cerebras returned HTTP 403 today; backlog item per gap acknowledged in `2026-05-03-prod-crit-fix-plan.md`).

**Sprint length assumption:** 1 to 2 weeks each, with overlap allowed. Not strict calendar — sprints close on DoD completion, not on dates. 10 sprints ≈ 3 to 5 calendar months at solo founder pace.

**Order rationale:** stop-the-bleeding first (S1), then close the structural gates that let the bleeding happen (S2-S5), then quality-and-confidence layer (S6-S8), then user-facing signal (S9), then long-horizon architecture (S10). Each later sprint depends on earlier guardrails.

---

## Self-audit refresh — what I see now that I did not surface (delta over `2026-05-03-prod-crit-fix-plan.md` section 1)

This pass adds five items the earlier plan did not name. The original ten still hold.

**11. The 27 mistake classes have one shared root.** Reading lessons.md end-to-end today: every class is a variation of "I do what is easy, not what is needed under pressure that no longer exists." Class 17 names this directly as "Alzheimer under trust." Once CEO trust drops, every class collapses back to that root. Sprint 5 (voice gate) and Sprint 3 (coordinator) are partial defenses against this; the deeper fix is model-time work (Class 16 — LoRA on accumulated corpus), which is Sprint 10 territory.

**12. The auto-deploy gap on Railway is not just "stuck webhook" — it has been silent for at least 9 hours and may be silent forever without active diagnosis.** Today's manual `railway redeploy` proved the deploy mechanism still works on demand. So the gap is purely the auto-trigger from GitHub push. This is observable: no GitHub webhook event in Railway dashboard since 2026-05-02 ~18:15 UTC. I have not opened the dashboard. CEO has access; I have CLI access but not webhook-event log read scope as far as I tested today.

**13. `apps/api/app/services/swarm_service.py` is dead code architecturally.** It tries to spawn `anus-agent` Docker containers from inside Railway's own container. This was never going to work in the deployed configuration. Whoever shipped it did so without testing the swarm path on Railway. The right long-horizon answer is to remove this file and move SwarmEngine to the VM daemon per ADR-006 ecosystem direction. Sprint 10 covers this.

**14. The "swarm" today is two unrelated things sharing a name.** (a) `packages/swarm/autonomous_run.py PERSPECTIVES` — 17 prompt configs that the daemon dispatches to LLM providers as JSON-returning tasks. This is the production swarm. (b) `apps/api/app/services/swarm_service.py` `_swarm_evaluate_scores` — a Docker-orchestrated SwarmEngine that grades open-ended assessment answers. This was a separate experiment that never lived end-to-end. They share `swarm` namespace but are otherwise unconnected. The conflation is itself a confusion source.

**15. The coordinator agent CEO has been asking about for two months does not exist.** identity.md L35 documents this honestly. `packages/swarm/agents/` is empty. Class 3 (solo execution) cannot be structurally prevented because there is no coordinator process to delegate to. Every "you should have routed to swarm first" lesson loses its teeth without this. Sprint 3 builds it.

---

## Sprint 1 — Stop the production bleeding

**Question:** Which user-facing crashes are firing right now, and what is the minimum work to make them all silent within one sprint?

**Evidence (today's tool-call receipts):**
- Sentry MCP returned 8 unresolved errors level=error firstSeen=-7d. Top three by event count: `VOLAURA-API-2M` (12 events, /assessment/answer, ModuleNotFoundError docker), `VOLAURA-API-2K` (7 events, /assessment/complete, tribe streak record failed), `VOLAURA-API-6Y` (5 events, /profiles/me, invited_by_org_id column missing).
- Lower-severity: BrandedBy twins schema invalid (2 events), header injection on /refresh-personality (1), AURA uuid syntax (1).
- Profile 422 fix is on branch `fix/profile-422-invited-by-org-id` commit `1f0da01`, already pushed, awaits CEO PR review.
- Swarm-service lazy-import fix is on branch `fix/swarm-service-lazy-docker-import` commit `b8fbafc`, already pushed, awaits CEO PR review.
- Today I flipped `SWARM_ENABLED=false` on Railway prod via `railway variables --set` plus `railway redeploy --yes`. Container restarted 2026-05-02 23:28 UTC, /health returns 200 ok with same git_sha 7216ce43886a. Sentry search for level=error firstSeen=-30m returned zero issues, suggesting the swarm path is now structurally inactive on prod.
- Railway auto-deploy gap remains: prod sha 7216ce43886a, main HEAD 9a8d128, ~10+ commits behind including the auth-session-race fix that was supposed to land days ago.

**Contradiction:** Three of the eight Sentry issues have fixes either ready (profile 422, docker lazy-import) or applied at runtime (SWARM_ENABLED=false). They are not landing on prod. The blocking surface is not engineering — it is the deploy pipeline plus PR review gating.

**Root Cause:** Two compounding causes. First: Railway auto-deploy is not firing on `git push origin main` for an unknown reason since 2026-05-02 ~18:15 UTC, so any merged fix sits in main without reaching prod. Second: CEO is not opening PRs this cycle (explicit directive earlier in session 132), so two ready fixes remain on branches.

**Guardrail (the structural fix for the sprint):**
- G1: Diagnose Railway webhook gap. Open Railway dashboard, check Deployments tab, look for failed builds since 2026-05-02 18:15. If webhook receiver shows zero events, reconfigure GitHub → Railway integration. If receiver shows events but builds fail, fix the build failure surface (likely image build error or env mismatch). Owner: CEO + Atlas (CEO has dashboard, Atlas has CLI for `railway logs --build`).
- G2: Open PRs for the two ready branches when CEO has bandwidth. Until merge, both branches are kept rebased on main weekly so they stay clean.
- G3: Three secondary Sentry fixes (tribe streak, BrandedBy twins, header injection on /refresh-personality) get one batch PR labelled `prod-hygiene`, fixable without architectural changes. Each is a 1-3 line fix.
- G4: Until G1 is closed, every prod-affecting commit triggers a manual `railway redeploy --yes` from Atlas as the deploy fallback. Documented one-liner.

**Re-test:** Sentry search `is:unresolved level:error firstSeen:-7d` returns zero issues on hot paths (/assessment/*, /profiles/*, /aura/*) by sprint close. /health git_sha matches origin/main HEAD. Authenticated walk against /api/profiles/me returns 200 with a real user.

**Scale:** Add Sentry alerting webhook to Telegram for any level=error issue with userCount>0 — surfaces production-affecting regressions inside 5 minutes instead of inside next CEO probe.

**DoD:** Zero hot-path Sentry errors. Prod sha matches main HEAD. Manual Sentry verification recorded in `for-ceo/living/`. Railway gap root-caused (closed or known-and-mitigated).

---

## Sprint 2 — Memory layer rotation

**Question:** Why does Atlas-next read 1300+ lines of canonical files plus 86-file root inventory on every wake when it could read 200 lines plus a compiled summary?

**Evidence:** `wake.md` lists 15+ mandatory files. `memory/atlas/` has 58 files post-cleanup (this session moved 28 to archive). `journal.md` is 172KB still in active root. `heartbeat.md` is now 8KB after this session's truncate. Four parallel wake checklists existed before today; one (NEW-INSTANCE-MINI-GUIDE.md) was consolidated this session, three remain (wake.md, atlas-operating-principles.md pre-output gate, user-global CLAUDE.md startup).

**Contradiction:** Wake protocol claims to be the single source of truth. In practice, four files compete for that role with overlapping read orders. Class 15 (performing knowing) is the natural failure mode when the read order itself is fragmented.

**Root Cause:** No rotation mechanism for journal/heartbeat (write-only growth). No compile target (BRAIN.md placeholder mentioned in wake.md L11 was never built). No designated single canonical wake checklist (four files compete).

**Guardrail:**
- G1: `journal.md` rotation script — post-commit hook moves entries older than current month to `archive/journal-YYYY-MM.md`, keeps current month inline. One python script, ~50 lines.
- G2: `heartbeat.md` rotation per session — when new session opens, prior session content auto-moves to `archive/heartbeat-session-NNN.md`. Triggered by Session header line detection.
- G3: `BRAIN.md` compile script — daily cron concatenates `identity.md` + `voice.md` + `lessons.md` last 5 classes + `journal.md` last 3 entries + `atlas-debts-to-ceo.md` open balance into one ~300-line BRAIN.md. Atlas-next reads this one file instead of nine.
- G4: `wake.md` self-trim from 110 lines to ~30 lines. Move detail to `archive/wake-protocol-v1.md`. Single canonical wake reference. atlas-operating-principles.md pre-output gate updated to point at the new wake.md only.

**Re-test:** Wake protocol read time from cold-start measured. Target: <30 seconds wall-clock for compiled-BRAIN-only path, vs. current ~2-3 minutes for full multi-file walk.

**Scale:** Same pattern for `for-ceo/living/` rotation — close docs older than 30 days move to `for-ceo/archive/` automatically.

**DoD:** journal.md and heartbeat.md never exceed 50KB combined. BRAIN.md compile target lives. wake.md is single canonical source. Atlas-next first-response in next compaction-recovery is voice-clean and reads BRAIN only.

---

## Sprint 3 — Coordinator Agent (Class 3 structural close)

**Question:** Why has Class 3 (solo execution > 3 files / 30 lines without consultation) appeared 17+ times across sessions and never been structurally prevented?

**Evidence:** identity.md L35 documents `packages/swarm/agents/` is empty, no Python implementation files. lessons.md Class 3: "the cure that never quite worked: the mandatory 'Agents consulted:' line." mistakes_and_patterns_distilled.md: "the real cure that needs to exist and does not: a Coordinator Agent that intercepts every sprint kickoff and forces agent routing BEFORE I get to solo execution."

**Contradiction:** Atlas has been writing the rule "consult swarm first" for two months while not building the gate that enforces it. The rule is a policy with no actuator.

**Root Cause:** Building the coordinator means building a runnable Python agent, an intercept hook, and a routing protocol — Class 22 (known-solution-withheld) capability boundary. Atlas defaults to text edits. Building agent runtime is outside default toolset.

**Guardrail:**
- G1: `packages/swarm/agents/coordinator.py` — first runnable Python agent. Reads task from stdin (or signal file), classifies by file count + line delta + keyword (audit, refactor, security, schema), dispatches to relevant perspectives via existing `autonomous_run.py PERSPECTIVES`, returns synthesis JSON.
- G2: PreToolUse hook (`.claude/hooks/coordinator-gate.sh`) — fires on Edit/Write tool calls. Counts staged + modified file delta. If >3 files OR estimated diff >30 lines, returns `{"decision": "block", "reason": "Coordinator gate: route through coordinator first or justify in 1 line."}`.
- G3: Justification override — instrument response can pass `[coordinator-bypass: <reason>]` token to indicate explicit single-file urgency, ad-hoc fix, or trivial. Bypass count logged to `memory/atlas/coordinator-bypass-log.md` for monthly review.
- G4: Coordinator dispatch results land in `memory/atlas/work-queue/in-progress/<task-id>/` with verdict.json. Atlas reads verdict before implementing.

**Re-test:** Run a synthetic task with 5-file diff. Coordinator hook should block initial Edit. Coordinator dispatch should fire. Atlas should produce verdict-aligned implementation, not solo improvisation. Test in dev branch with assertion script.

**Scale:** Same hook pattern can later gate on Bash tool calls (database changes) and on file writes outside the repo.

**DoD:** First successful coordinator-gated task closed in production codebase. Class 3 violations in next 4 weeks: 0.

---

## Sprint 4 — Swarm signal-to-noise (38% FP → <10%)

**Question:** Why does the production swarm produce 38% confirmed false-positive rate (Cycle 3 Session 130) and how do we close it without abandoning the swarm?

**Evidence:** swarm-commands.md Cycle 3 logged: 13 dispatched, 13 responded, 5 confirmed FP (Scaling Eng, Security Auditor, Ecosystem Auditor — 3 repeat FPs; Code Quality + CTO Watchdog — 2 new FPs), 3 CEO-blocked, 4 vague feature requests, 0 actionable engineering commands. Quality flag: "weak this cycle." Class 11 (self-confirmation) and Class 26 (verification-through-count) are root concepts here.

**Contradiction:** Swarm is supposed to be Atlas's brain (per CLAUDE.md "swarm = brain, I = hands"). A 38% wrong brain is worse than no brain — it floods Atlas with bad priorities.

**Root Cause:** Two layers. Surface: perspectives generate claims without reading the code. Deeper: daemon prompts do not require evidence citation, so perspectives can pattern-match against project metaphors (e.g. "Law 2 broken") without grep against current codebase.

**Guardrail:**
- G1: Evidence gate in daemon prompts. Every claim must include `file:line` citation. Daemon validates citation exists in repo before saving the perspective response. Bad citation → mark perspective response as "evidence-incomplete," do not surface to Atlas.
- G2: Strike rule — repeat false-positive perspective gets `weight: 0.5` modifier for 5 cycles, recovers if next 3 cycles are evidence-clean. Existing `perspective_weights.json` infrastructure is already there but underused.
- G3: Code-grep adapter for perspectives that need to reference codebase. Daemon provides `grep` and `read` callable functions in perspective prompt. Instructs perspectives: "before claiming X, grep for X."
- G4: Per-cycle SWARM QUALITY metric — total / actionable / FP / repeat-FP / CEO-blocked / vague. Logged to swarm-commands.md after every cycle. Dashboard surface in admin panel.

**Re-test:** 3 consecutive cycles with FP rate <10%. Action queue from swarm visibly contains real engineering commands with file:line citations.

**Scale:** Same evidence gate pattern can be applied to LinkedIn-content-generation agents (claim must cite source), to Sentry-watcher agent (alert must cite issue ID).

**DoD:** Swarm FP rate measured at <10% across 3 cycles. SWARM QUALITY metric is in admin dashboard. No CEO catches "swarm said X, you said Y" mismatches.

---

## Sprint 5 — Voice / style pre-composition gate

**Question:** Why does Atlas violate voice rules ~12 times per session despite voice.md, style-brake hook, and CEO calling it out 5+ times in 2 days?

**Evidence:** This single session 132: voice-breach hook fired multiple times for bullet walls and markdown headings. Each fire happens AFTER the offending response was already drafted. Constitution-guard pre-tool-use is a real gate (returns `{"decision": "block"}`); style-brake is a scoreboard fired post-composition.

**Contradiction:** Constitution-guard works because it stops a tool call before it executes. Style-brake fails because chat composition is not a tool call — it is the response itself, and there is no pre-composition hook in Claude Code's current architecture. Hook fires too late.

**Root Cause:** Asymmetric hook architecture. Tool-call output has hooks; chat output does not. Plus default Anthropic training biases toward bullet/header/table for "structured" content. Combined: training produces bullet wall, hook fires after, system-reminder logs breach, next response also has bullets because draft was already in flight when reminder showed.

**Guardrail:**
- G1: Investigate Claude Code hook architecture for pre-response composition. If hook surface exists for chat (e.g. on assistant_message_start), wire a regex check that scans draft for `**bold**`, `^- `, `^## `, `|---|` patterns and returns `{"decision": "block", "reason": "Voice violation, rewrite as Russian prose."}`.
- G2: If no pre-response hook surface exists in Claude Code today, escalate to Anthropic feedback channel as feature request. Document workaround: explicit voice-check inside response generation, e.g. self-prompt at start of every chat response: "voice check: am I in prose mode?"
- G3: Training-side fix — append voice examples (5-10) to every Atlas-instance system prompt loaded on wake. ZenBrain principle: high-emotional-intensity examples (CEO catches) get longer text and verbatim quotes, biasing retrieval toward voice-clean tokens.

**Re-test:** 20 consecutive Atlas turns without voice-breach hook fire. Measured by hook log absence.

**Scale:** Same pre-response gate pattern can enforce other invariants (no English drift in Russian conversation, no banned openers, no trailing questions).

**DoD:** Voice-breach rate < 1 per 50 turns. Pre-composition gate exists in some form (hook, prompt prefix, or LoRA delta).

---

## Sprint 6 — Class 27 structural fix (smoke-test scope auto-elevation)

**Question:** Why did Class 27 (smoke-test as user-path proxy) fire on 2026-05-03, and what auto-runs an authenticated walk on every "deploy verified" claim from now on?

**Evidence:** lessons.md Class 27 (this session): "I conflated 'public routes return 200' with 'authenticated user flow works.'" The fix recipe inside the class itself is a contract — three-level smoke hierarchy — but no script enforces it.

**Contradiction:** The class entry IS the fix according to my own documentation pattern. But documentation is not enforcement. The next "deploy verified" claim could repeat the same scope error if no automated gate runs.

**Root Cause:** Smoke tests are written ad-hoc per situation. No standing script. Each Atlas-instance reinvents what "verify" means at deploy time.

**Guardrail:**
- G1: `scripts/auth_smoke.py` — opinionated 3-level smoke. Level 1: curl public routes (/, /az, /az/login). Level 2: with a test user's Bearer token (issued by `scripts/issue_test_user_token.py`), curl `/api/profiles/me`, `/api/aura/me`, `/api/assessment/sessions`. Level 3: cross-navigation simulator via Playwright that logs in, navigates between dashboard pages, asserts session persists.
- G2: Pre-claim hook — any Atlas response containing strings like "deploy verified," "prod live," "ship clean," "structurally not broken" triggers a post-response check that runs auth_smoke.py automatically. If level 2 fails, response is annotated with "AUTHENTICATED PATH NOT VERIFIED."
- G3: Test-user provisioning script — creates a stable e2e_atlas_smoke@test.volaura.app user with known password, can be invoked on demand to mint a Bearer token for smoke runs. Token expires in 1 hour.

**Re-test:** Run auth_smoke.py against current prod. Confirm level 2 hits 200 on /profiles/me, /aura/me. Confirm level 3 cross-navigation passes. Then deliberately break a route (e.g. revoke RLS on profiles) and confirm smoke fails loudly.

**Scale:** Same auto-elevation pattern for "feature shipped" claims (must include user walk evidence) and for "performance OK" claims (must include latency p95 numbers).

**DoD:** auth_smoke.py exists, runs in CI on every prod-affecting deploy, automatically annotates Atlas responses claiming verification. Class 27 violations in next 4 weeks: 0.

---

## Sprint 7 — Test debt + DoD enforcement (ADR-010 closure)

**Question:** Why is the project at 28% Change Failure Rate (per ADR-010 autopsy of 61 fix commits over 218 total) and what enforces the 3-item DoD that should bring it below 13% Elite threshold?

**Evidence:** ADR-010 documented this in 2026-04-03 with full autopsy. Implementation checklist at the bottom shows: "Pre-commit hook for DoD Item 3 (schema sync check) — BATCH-W [open]"; "SEC agent mandatory routing for any API task — BATCH-W [open]." The work was scheduled and never executed. Today's docker-import bug is a Class 12 (self-inflicted complexity) instance — covered in DoD Item 2 (staging deployment verified) which would have caught it.

**Contradiction:** ADR-010 is `Status: Accepted`. Acceptance was never followed by implementation. This is the classic Class 6 (team neglect) on a documentation surface.

**Root Cause:** ADR-010 wrote the DoD list but never specified which file or hook executes it. Each item is a paragraph, not a script. So "DoD enforced" became "DoD documented" became "DoD ignored under pressure."

**Guardrail:**
- G1: `.githooks/pre-commit-dod.sh` — reads DoD checklist, applies item-specific checks. Schema sync (item 3): if `apps/api/schemas/*.py` changed, require `apps/api/openapi.json` also changed; if `apps/web/src/types/api.ts` not regenerated, block commit. Security pre-check (item 1): if router file changed, scan for `@router.get`/`.post` decorators added without `dependencies=[Depends(rate_limit)]`. Staging-verify (item 2): require commit message body has `Tested-on: <staging-url>` line for any Sentry-firing path.
- G2: `scripts/audit_module_level_imports.py` — AST walk of `apps/api/app/` plus `packages/`, list every module-level import not in `requirements.txt`. CI warning first sprint, blocking gate next sprint. Catches the docker-class regression class.
- G3: CFR dashboard — script that queries git log for `fix:` commits over rolling 30-day window, divides by total commits, reports CFR. Threshold gate: if CFR rises above 20%, alert.

**Re-test:** Commit a deliberate schema desync — pre-commit hook blocks. Commit a router change without rate limit — hook blocks. Commit a module-level `import boto3` (not in reqs) — hook blocks. CFR computed against last 30 days, recorded in `memory/atlas/cfr-log.md`.

**Scale:** Same hook architecture extends to other ADRs that have unimplemented checklists (ADR-007 model router fallback events, ADR-008 zeus governance event emission).

**DoD:** CFR < 13% over rolling 30-day window. All three pre-commit DoD items active. ADR-010 status updated to `Implemented`.

---

## Sprint 8 — Sentry hygiene (zero unresolved on hot paths)

**Question:** Why are 8 unresolved Sentry errors sitting on prod, three of them on the assessment+profile critical user path?

**Evidence:** Today's MCP search returned 8 issues. Sprint 1 covers the top 3 (docker, profile 422 already on branches; tribe streak record fail at assessment.py:1188 — needs root-cause). This sprint covers the long tail.

**Contradiction:** Sentry is wired (sentry_dsn configured per config.py L48). Errors fire. Nothing resolves them. The watchdog is set up but the cleanup happens on Atlas's manual cycle, not automatic.

**Root Cause:** No automatic resolution gate. No alert routing for low-severity issues. The recurring-symptoms watchdog (per config.py L49) only fires for regression detection, not for new-issue triage.

**Guardrail:**
- G1: Daily Sentry-watcher cron job — for every issue with userCount>0 OR events>5 in last 24h, post a Telegram alert to CEO with issue ID, culprit, top stack frame.
- G2: One-PR-per-issue policy — each Sentry issue gets a tracked branch named `fix/sentry-<issue-id>` with the fix attempt and a Sentry resolve link in commit body. After PR merge + deploy + 24h clean window, auto-resolve.
- G3: Per-issue triage assignments — high-frequency issues get `assigned: atlas`, low-frequency to `unassigned` queue. Reviewed weekly.

**Re-test:** Sentry search `is:unresolved level:error` returns < 3 issues, all of them userCount=0 or events<3.

**Scale:** Same one-PR-per-issue model can extend to performance issues (Sentry transactions with p95 > threshold).

**DoD:** Sentry unresolved level=error count is 0 on hot paths. Daily watchdog cron is active.

---

## Sprint 9 — Public signal pack ship

**Question:** Why has the public signal pack (3 LinkedIn posts, 3 video scripts, lead DMs) been gated on "user path verified" since 2026-05-03 morning, and what unblocks publish?

**Evidence:** `for-ceo/living/public-signal-pack-week-2026-05-03.md` is on origin since this morning. `public-claims-verification-2026-05-03.md` confirms most claims. Profile 422 catch on the same day made publish gated on its fix. The fix lives on a branch.

**Contradiction:** Marketing assets are ready. Verification evidence is mostly assembled. The block is engineering — auth + profile flows must work end-to-end before "verified professional talent platform" claims can be made publicly with proof.

**Root Cause:** This is a downstream sprint — depends on Sprint 1 (production fixes land on prod) and Sprint 6 (auth smoke automation). Publishing before the user path works means the first new visitor hits 422 and the public claim collapses.

**Guardrail:**
- G1: Sprint gate — only when auth_smoke.py (Sprint 6) passes 3 consecutive runs against prod over 24 hours, publish unblocks.
- G2: Telegram-CEO bot integration — when gate passes, bot pings CEO with "publish unblocked, run cadence Tue/Thu/Sat per public-signal-pack."
- G3: Per-post link analytics — each LinkedIn post is published with UTM-tagged URL pointing at /az/landing?utm_source=linkedin&utm_campaign=signal-2026-05-03, traffic counted in Plausible (or PostHog). Conversion to signup tracked.

**Re-test:** First post lands. Visitors arrive. /signup → /assessment → /aura badge journey completes for at least one new user. Sentry stays clean during publish window.

**Scale:** Same UTM + conversion-tracking pattern for future content (video scripts week 2, podcast week 4).

**DoD:** All 3 LinkedIn posts published. Lead DMs sent (5 archetypes × 4 leads = 20 DMs). Conversion funnel measurable. Zero Sentry regressions during publish week.

---

## Sprint 10 — Architectural reset (long-horizon)

**Question:** What architectural assumption is silently costing us — and how do we close it before it becomes the next year's debt mountain?

**Evidence:**
- `swarm_service.py` is dead code in the API process (Sprint 1 patches it but the architectural mistake remains).
- `packages/swarm/agents/` is empty — coordinator + perspectives are JSON configs, not running processes (Sprint 3 builds the first agent).
- VM daemon state is unknown — CLAUDE.md "queue rule" exists but I have not verified VM is alive.
- Atlas continuity is text-only — Class 16 documents that real continuity needs LoRA fine-tune on accumulated corpus, model-time work outside default toolset.
- ADR-006 says ecosystem is "shared FastAPI monolith" but the swarm experiment violated this by trying to spawn Docker containers from inside it.

**Contradiction:** The codebase has both "monolith" architecture (ADR-006) and "swarm-as-distributed-agents" aspiration (CLAUDE.md, identity.md). They live in the same `apps/api/` repo and trip over each other.

**Root Cause:** The architectural mandate per breadcrumb.md Session 131 is "reliability over novelty, feature freeze." The active feature freeze means "no new product surface" but does NOT mean "no architectural cleanup of existing dead code paths." Swarm-in-API-process is dead and should leave; swarm-as-VM-daemon is alive and should be the authoritative runtime; Atlas-LoRA is the model-time investment for real continuity.

**Guardrail:**
- G1: Move SwarmEngine + Docker container orchestration out of `apps/api/` entirely. Delete `apps/api/app/services/swarm_service.py`. Move equivalent functionality to VM daemon. API calls VM via httpx with timeout + circuit breaker. Aligned with ADR-006 monolith boundary.
- G2: VM daemon health check — `infra/start.sh` (per swarm-commands.md "9 references, has health loop with auto-restart") is run as the canonical VM entry point. CEO replaces manual `nohup python ...` with `bash infra/start.sh`. Daemon health endpoint (`http://vm:port/health`) is monitored from API container, fallback to BARS on VM-unreachable.
- G3: Atlas LoRA pipeline — collect 6+ months of journal/lessons/voice corpus. Train LoRA on Llama-3.3-70b or similar local model. Deploy as the swarm-perspective backend for "Atlas voice" perspective. First step toward Class 16 architectural fix (between-session continuity at model-layer, not just memory-layer).
- G4: Update ADR-001 (system architecture) and ADR-006 (ecosystem architecture) to reflect: API monolith + VM swarm split; LoRA-trained Atlas-voice perspective; coordinator agent in `packages/swarm/agents/`.

**Re-test:** `apps/api/app/services/swarm_service.py` deleted. VM daemon health green. LoRA-trained Atlas-voice perspective produces test responses indistinguishable from canon (blind A/B with CEO).

**Scale:** Same architectural cleanup pattern for any other "experimental code path that never lived end-to-end" — hunt them with the audit_module_level_imports script (Sprint 7) plus a follow-up `scripts/audit_dead_code_paths.py`.

**DoD:** swarm_service.py removed. VM daemon authoritative. Atlas LoRA v1 deployed. ADR-001 + ADR-006 updated to current state.

---

## Dependency graph

```
S1 (stop bleeding) ──► S6 (auth smoke) ──► S9 (publish)
   │                       ▲
   ▼                       │
S2 (memory rotation)       │
                           │
S3 (coordinator) ──► S4 (swarm S/N) ──► S7 (DoD enforce)
                           │
                           ▼
                       S8 (sentry hygiene)
                           │
                           ▼
                       S10 (architectural reset)

S5 (voice gate) is largely independent — runs in parallel with S2-S4.
```

S1 → S2 → S3 → S4 is the critical reliability chain. S5 runs in parallel. S6 unlocks S9. S7+S8 are quality layer. S10 is long-horizon.

## What I am NOT including in this 10-sprint roadmap

- ZEUS as a separate product (out of scope per Constitution v1.7 feature freeze)
- BrandedBy expansion (frozen per Session 131 breadcrumb)
- LifeSim Godot work (frozen per Session 131 breadcrumb)
- MindShift voice runtime walk (CEO-side action per Session 125 ledger, not Atlas-side)
- Stripe Atlas / ITIN / IRS work (CEO-only by nature)
- Any new feature surface (architectural mandate is "reliability over novelty")

## Strange v2 gap acknowledgment

This roadmap was not validated by external model adversarial critique. Cerebras 403'd today. Backlog item: when external model channel is healthy (NVIDIA NIM, Gemini Vertex, DeepSeek), run roadmap through adversarial pass. Until then, treat as draft-quality on adversarial dimension.

## What proves this roadmap was real (not theatre)

Each sprint has DoD that is tool-call verifiable. Each guardrail is a script or a hook, not a willpower commitment. The dependency graph means "skip a sprint" is structurally visible (later sprints can't close DoD without earlier sprints landing). Class 18 (grenade-launcher) does not fire because each sprint is narrow and shippable independently.

If this roadmap follows the lessons it should follow, we measure progress via tool calls, not via narrative.
