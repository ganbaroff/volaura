# Full Ecosystem Audit — 2026-04-17 10:31 Baku, Session 115

Atlas self-audit. Honest. No decoration.

---

## ORGANISM STATUS

| Surface | Status | Evidence |
|---------|--------|----------|
| Frontend (Vercel) | ALIVE | volaura.app → 200, redirects to /az |
| Backend (Railway) | ALIVE | volauraapi-production.up.railway.app/health → 200, DB connected, LLM true |
| Telegram bot | ALIVE | @volaurabot getMe → 200 |
| CI Watchdog | GREEN | gh run list confirms success |
| CI Swarm Proposals | RED | `ModuleNotFoundError: No module named 'pydantic'` — workflow installs only httpx+loguru but swarm __init__.py imports pydantic |
| CI AURA Reconciler | RED | `column assessment_sessions.user_id does not exist` — column renamed to profile_id in a migration but reconciler not updated |
| Self-wake cron | UNKNOWN | Not verified this session |

## MEMORY STATE (155 files in memory/atlas/)

### Healthy
- wake.md, identity.md, heartbeat.md, journal.md, relationships.md, lessons.md — all current
- CURRENT-SPRINT.md — accurate, Track A 9/9 done, B 1/2, E 0/6
- company-state.md — updated session 114
- deadlines.md — 3 active (GITA May 27, WUF13 Jun 13, 83(b) TBD), patent provisional

### Stale
- memory/context/heartbeat.md — last updated 2026-04-05 Sprint E2 Session 85 (10 sessions behind)
- memory/context/sprint-state.md — says "2026-04-16 14:30" but doesn't reflect session 114 work
- memory/context/quality-metrics.md — 125 lines, no updates since early April
- memory/context/daily-log.md — 30 lines, appears abandoned

### Inbox
- 71 files in inbox/ (mostly heartbeat pings from cron)
- 7 epic files from 2026-04-14 (E1-E7) — unconsumed planning artifacts
- morning-report-2026-04-17.md — from wake loop

## SWARM PROPOSALS (10 total)
- 5 pending: Railway redeploy, Telegram HMAC, API security sweep, GDPR Art 22, PR readiness
- 5 dismissed: 3 duplicates, 1 informational, 1 hallucinated endpoint

## CODE TODOS
- Backend: 2 files with TODOs (organizations.py, skills.py) — minimal
- Frontend: 5 files with TODOs — api/client.ts (2), use-public-stats, use-auth-token, life/page.tsx, discover/page.tsx

## CI FAILURES — ROOT CAUSES

### Swarm Proposal Cards
- `packages/swarm/__init__.py` imports `agent_hive` which imports pydantic
- Workflow only installs `httpx loguru`
- Fix: add `pydantic` to workflow pip install, OR make telegram_proposal_cards importable without pulling full swarm

### AURA Reconciler
- `aura_reconciler.py:61` queries `assessment_sessions.user_id`
- Column was renamed to `profile_id` in a migration
- Fix: update column name in reconciler query

## HANDOFF AUDIT (from HANDOFF-AUDIT-TODO.md)
- 13 handoffs total
- 8 DONE, 3 PARTIAL, 1 NOT DONE (swarm/agents/ dir empty), 1 DONE
- Handoff 013 (Swarm & Agent Upgrade) — NOT DONE, packages/swarm/agents/ directory is EMPTY

## UNFULFILLED COMMITMENTS (from heartbeat.md "Open commitments")
1. Live test critique batch — blocked on ANTHROPIC_API_KEY credits
2. Task 2 (финансы + Азербайджан) — waiting for CEO
3. AZ translation quality pass — not started
4. Anti-cheat masks — deferred to separate sprint
5. Pre-redesign cosmetic fixes — on hold per CEO

## TRACK E — ATLAS EVERYWHERE (0/6)
- E1: Reflection card on /aura — NOT BUILT (backend endpoint exists per breadcrumb, frontend card missing)
- E2: MindShift → atlas_learnings read bridge — NOT BUILT
- E3: Life Feed consumes atlas_learnings — NOT BUILT
- E4: Style-brake unification (atlas_voice.py everywhere) — atlas_voice.py EXISTS but not connected to all surfaces
- E5: BrandedBy twin context — NOT BUILT
- E6: Memory sync heartbeat cron — NOT BUILT

## CONSTITUTION P0 BLOCKERS (from deadlines.md WUF13 section)
- 4 of 8 Atlas items done
- 4 still open: grievance admin UI, landing sample profile, ghosting grace, Art. 9 legal

## WHERE ATLAS ACTUALLY LIVES IN CODE
Backend (14 files): telegram_webhook, atlas_voice.py, atlas_tools.py, atlas_gateway.py, skills.py, aura.py, lifesim.py, lifesim service, model_router, ecosystem_events, video_generation_worker, loop_circuit_breaker, main.py, config.py
Frontend (10 files): /atlas page, /aura page, use-reflection hook, i18n en+az, bottom-tab-bar, globals.css, generated types+sdk, product-placeholder

## PRIORITY ACTION LIST
1. **P0 FIX:** AURA Reconciler — change user_id → profile_id in aura_reconciler.py
2. **P0 FIX:** Swarm Proposal Cards — add pydantic to pip install in workflow
3. **P1:** Build E1 reflection card (backend endpoint ready, frontend missing)
4. **P1:** Update stale memory/context/ files (heartbeat, sprint-state, quality-metrics)
5. **P2:** Consume 7 epic inbox files
6. **P2:** Telegram HMAC validation (swarm proposal pending)
7. **P2:** Security sweep of new endpoints (lifesim, grievance, community)

---

## Verification pass — 2026-04-17 10:49 Baku (Cowork-Atlas)

Scope: re-verify the 10:31 audit's claims against filesystem evidence 18 minutes later. Same day, same session class, different instance (Cowork vs Terminal). Findings below are corrections and confirmations, not a new audit.

### Items the 10:31 audit called wrong (now verified shipped)

1. **E1 Atlas Reflection card — BUILT, not "NOT BUILT".**
   Evidence: `apps/web/src/app/[locale]/(dashboard)/aura/page.tsx:21` imports `useReflection` from `@/hooks/queries/use-reflection`; lines 623–642 render `{reflectionText}` with loading skeleton, "Atlas says" title (i18n key `aura.reflectionTitle`), and markdown body. Hook hits `/aura/me/reflection` at `apps/web/src/hooks/queries/use-reflection.ts:15`. Track E count should be 1/6, not 0/6.

2. **Grievance admin UI (Constitution P0) — BUILT, not "still open".**
   Evidence: `apps/web/src/app/[locale]/admin/grievances/page.tsx` is 261 lines, real implementation. Uses `useAdminPendingGrievances`, `useAdminHistoryGrievances`, `useTransitionGrievance` hooks, renders grievance cards with status transitions (pending → reviewing → resolved/rejected), resolution textarea, admin notes field. P0 remaining = 3, not 4.

3. **Ghosting grace — backend BUILT.**
   Evidence: `apps/api/app/services/ghosting_grace.py` (class header quoted): "Ghosting Grace worker — Constitution VOLAURA Rule 30, WUF13 P0 #14. After signup, if a user has not completed any assessment within 48 hours, send ONE warm re-entry email and mark the user so we never nudge twice." Idempotent, kill-switch aware, batch size 50. Unknown: whether scheduling is wired to pg_cron or a workflow.

### Items the 10:31 audit called right (confirmed still failing)

4. **AURA Reconciler CI red — confirmed, scope larger than audit said.**
   `apps/api/app/services/aura_reconciler.py` references `assessment_sessions` at lines 61, 111, 139, 161 — four call sites, not one. Fix is rename at all four.

5. **Swarm Proposal Cards CI red — confirmed.**
   `.github/workflows/swarm-proposal-cards.yml:36` reads literally: `python -m pip install httpx loguru`. Pydantic absent. All other swarm workflows (swarm-daily, swarm-distill-weekly, swarm-adas) correctly install pydantic.

6. **E2/E3/E5/E6 — absent.** Grep confirms no `atlas_learnings` consumer in frontend outside Telegram webhook. No memory-sync cron in `.github/workflows/`. No `twin_context` module in BrandedBy area.

7. **Ambient UI, command palette, voice triage, focus companion, morning brief — absent.** Zero grep hits for any of: `AtlasAmbient`, `CommandPalette`, `cmdk`, `FocusCompanion`, `MorningBrief`, `daily-brief`.

8. **E4 atlas_voice — partial.** Used in `apps/api/app/routers/aura.py` and `apps/api/app/services/atlas_voice.py`. Not yet threaded through lifesim, skills, grievance, telegram_webhook surfaces (those have the service file adjacent but no import).

9. **Landing sample profile — absent.** No `apps/web/src/app/*/profile/sample/`, no `SampleProfile` component, no `public-profile` route grep hit.

10. **Article 9 legal — drafts only.** `docs/legal/` contains `Privacy-Policy-draft.md`, `ToS-draft.md`, `PRIVACY-POLICY-DE-CCORP-DIFF.md` (Delaware C-Corp diff). Drafts are not shipped disclosures; Article 9 special-category handling not traced to a concrete consent flow in `apps/web/src/`.

### Terminal-Atlas overnight (03:02–10:49 Baku)

11. **Tier 0 handoff audit matrix — untouched.** `memory/atlas/handoff-audit-2026-04-17.md` is 3824 bytes, last mod 03:51. All 13 rows still `(to fill)`. Counts still 0/13.

12. **§3.1 `proof_gate.py` — not started.** `memory/atlas/execution-log.md:16` reads `status: not started`.

13. **§3.1.b hook firing — not started.** `execution-log.md:23`: `status: not started`, decision field empty.

14. **§3.11 morning report — not started** per execution-log, though `memory/atlas/inbox/morning-report-2026-04-17.md` exists — verified as the letter I (Cowork-Atlas) wrote at 02:58, not a Terminal-Atlas overnight report.

15. **Blocker honest-acknowledged:** commit `148a3c1 atlas(wake-loop): LoRA model broken — honest status update` — 36 examples corrupted the Gemma 2B base per breadcrumb. Tier 2 §3.6/§3.7 (LoRA → Ollama, retrieval gate) deferred by this; Tier 0 does not depend on LoRA.

### Drift window: 10:31 → 10:49 Baku

`find apps/web/src/ -type f -newermt "2026-04-17 10:30"` returned **zero files**. `find apps/api/app/ -type f -newermt "2026-04-17 10:30"` likewise zero (no commits since Session 114 FINAL at commit `ca0a9f5`). Nothing shipped between audits; divergence between the two audits is interpretation drift, not code drift.

### Revised priority list (supersedes section above)

| # | Priority | Item | Why it moved |
|---|----------|------|--------------|
| 1 | P0 | AURA Reconciler: 4-site rename user_id → profile_id | Same, scope corrected |
| 2 | P0 | Swarm Proposal Cards: add `pydantic` to workflow pip install | Same |
| 3 | P0 | Landing sample profile page | Only unbuilt P0 without any backend prep |
| 4 | P1 | Article 9 disclosure flow — promote drafts to production legal pages + consent copy | Launch blocker for EU |
| 5 | P1 | Thread atlas_voice through lifesim/skills/grievance/telegram routers (E4 unification) | Already imported in 2 places, finishing is cheap |
| 6 | P1 | Terminal-Atlas Tier 0 (proof_gate + handoff audit matrix + gate_b) — the structural cure for 22 error classes | Deferred overnight, remains the highest-leverage meta-work |
| 7 | P2 | E2 MindShift → atlas_learnings read bridge | Needed for cross-face organism feel |
| 8 | P2 | Memory-sync cron (E6) + heartbeat/sprint-state staleness | Chain: E6 writes, context/ files stop rotting |
| 9 | P2 | E3 Life Feed consumer, E5 BrandedBy twin context | Not launch-critical, shape-of-organism work |
| 10 | P2 | Ambient UI, command palette, voice triage, focus companion, morning brief (5 UI surfaces) | These are "Atlas felt across faces" — aspiration, not launch |

### Ecosystem chronology summary (from PROJECT-EVOLUTION-MAP.md, verified)

27 days from Mar 21 to Apr 17. 1,367 commits. 14,755 files. Peak single-day 349 commits (Apr 14 — deep memory + autonomy phase). Eight phases: birth → swarm+security → assessment engine → production hardening → atlas awakening (naming Apr 12) → deep memory + autonomy → session 113 shipping → session 114 business + brain → now (session 115 stability pass + Cowork wake-loop + this re-verification).

Metrics snapshot: 128 backend endpoints · 810+ tests · 48 frontend pages · 79 components · 90 migrations · 853 EN / 886 AZ i18n keys · 365 memory files · 51 swarm skills · 22→1 error classes consolidated · $405K perks submitted · ~$520 spent.
