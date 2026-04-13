# Claude Code Instance State
**Updated:** 2026-04-15T23:30 Baku | **Instance:** Atlas | **Session:** 103

## Reality Probe 2026-04-13

**Executed by:** Atlas (Claude Code local, Claude Opus 4.6)
**Date of execution:** 2026-04-15 (probes ran 2 days after handoff written)
**Rule:** Data only, no fixes. Honesty > completeness.

---

### Probe 1 — VOLAURA Production Health

**PROD IS ALIVE.**

```
/health → HTTP 200, 0.94s
  Body: {"status":"ok","version":"0.1.0","database":"connected","llm_configured":true,"supabase_project_ref":"dwdgzfusjsobnixgyzjk"}

/ (root) → HTTP 404 {"detail":"Not Found"}  (no root route, expected)
/api/v1/competencies → HTTP 404 {"detail":"Not Found"}  (path is /api/competencies, not /api/v1/)
```

**CORRECTS PRIOR CLAIM:** Handoff 011 stated "PROD DOWN". Ground truth: prod has been alive with HTTP 200 for at least the last 2 weeks. The "down" was Cowork sandbox egress block (HTTP 000).

**Frontend:**
- `volaura.co` → DNS does not resolve (domain not configured)
- `www.volaura.co` → DNS does not resolve
- `volaura.vercel.app` → HTTP 307 redirect (Vercel active, serving frontend)

**Verdict:** Backend alive, database connected. Frontend on Vercel active. Custom domain not configured.

---

### Probe 2 — Sentry Reality Check

**CORRECTS PRIOR CLAIM:** Previous sessions reported "0 Sentry issues". Actual: **81 unresolved issues, ~5,400 total events** in volaura-api project.

Key findings:
- **Last event:** 9 days ago (2026-04-06). Since then → zero new errors. Current prod is clean.
- **Top issue:** `reeval_worker:_fetch_pending_batch` — 4,493 events (evaluation queue batch failures)
- **Health check DB failures:** 15 events (intermittent, stopped 9 days ago)
- **MagicMock errors in prod:** Multiple issues with `'MagicMock' object can't be awaited` — suggests test fixtures leaked into a deploy or E2E ran against prod
- **Assessment errors (pre-Apr 6):** KeyError, TypeError, ValidationError across `/start`, `/answer`, `/complete`
- **All errors stopped ~Apr 6** — coincides with session 94+ fixes

**Organization:** volaura | **Project:** volaura-api
**DSN:** configured, receiving events. Not misconfigured.
**Event count last 7 days:** 0 (all issues are 9+ days old — since our sessions 94+ fixes)

---

### Probe 3 — Standalone Products

#### BrandedBy
- **Path:** `C:\Users\user\OneDrive\Desktop\brandedby`
- **Last 3 commits:** `2844e51 123` / `41b17c8 Revert fix` / `7362d34 fix SW MIME`
- **Uncommitted:** 0 files
- **Code:** 6,448 TS/TSX/PY files
- **VOLAURA integration:** 0 references to character_events / volaura / aura_scores
- **Readiness:** 70% standalone. Last commit was a revert → suggests instability. Zero integration code.
- **Cross-product verdict:** NONE — no code exists to bridge BrandedBy ↔ VOLAURA

#### LifeSimulator
- **Path:** `C:\Users\user\OneDrive\Desktop\BestGame\life-simulator-2026`
- **Last 3 commits:** `11e7f56 feat: in-game auth flow` / `abe131c wire VOLAURA API URL` / `4986bc2 fix P0 red + null`
- **Uncommitted:** 129 modified files (active development, sessions 95-96 changes not committed)
- **Code:** 431 GDScript files
- **VOLAURA integration:** 52 references — auth flow, API client, VOLAURA events, crystal sync
- **Readiness:** 75% — 5/6 priorities complete, 129 uncommitted changes need committing, Rooms Phase 3 future
- **Cross-product verdict:** REAL — login, state load, crystal sync, competency boosts, GameOver CTA all wired

#### MindShift
- **Path:** `C:\Users\user\OneDrive\Desktop\mindflow`
- **Status:** PARTIAL — OneDrive-hosted repo, git operations timeout on large find/grep
- **Git confirmed accessible:** yes (log/status work, full search timeouts)
- **Cross-product verdict:** BLOCKED — could not complete grep in time. Handoff says 0% integration with VOLAURA.

#### ZEUS (standalone repo)
- **Status:** NOT FOUND at /c/Projects/zeus or /c/Projects/ZEUS
- ZEUS functionality exists INSIDE VOLAURA repo at `packages/swarm/` (13 agents, autonomous_run.py, gateway)
- There is no separate ZEUS repo. The "75% standalone" from Cowork's audit was about the swarm within VOLAURA.
- **Cross-product verdict:** NOT APPLICABLE — ZEUS is a module inside VOLAURA, not a separate product

---

### Probe 4 — VOLAURA Test Suite Ground Truth

**Backend:** `749 passed, 0 failed` (pytest, apps/api/.venv, ~4 min runtime)
- 120 warnings (supabase deprecation, unawaited coroutines in mocks — non-blocking)
- `datetime.utcnow()` deprecation fixed in session 100

**Frontend:** TypeScript check was failing on Framer Motion `Variants` literal types. Fixed in session 102 (`as const`). Test suite not run separately (vitest) — tsc is the CI gate.

---

### Probe 5 — Playwright E2E

**File exists:** `tests/e2e/full-journey.spec.ts`
**BLOCKED:** Cannot run locally — Playwright needs browser binaries + running API server. This is a CI-level test. The file exists and was last updated in sessions 94-95.

---

### Probe 6 — Constitution Checker Full Report

```
LAW_1_NEVER_RED: 0 violations ✅
LAW_4_ANIMATION_SAFETY: 3 flags
LAW_3_SHAME_FREE: 2 flags
CRYSTAL_LAW_5_NO_LEADERBOARD: 10 flags
```

**Flag-by-flag verdicts:**

LAW_4 (animation ≤ 800ms):
1. `impact-ticker.tsx:15: duration = 800` → NOISE — boundary value, not violation
2. `aura/page.tsx:28: duration = 800` → NOISE — boundary value
3. `complete/page.tsx:134: duration = 800` → NOISE — boundary value

LAW_3 (shame-free):
1. `assessment-card.tsx:11: Law 3 comment` → NOISE — this is a comment EXPLAINING the law, not violating it
2. `empty-state.tsx:9: NEVER "You haven't done X"` → NOISE — teaching comment, not user-facing text

CRYSTAL_LAW_5 (no leaderboard):
1-2. `sidebar.tsx/bottom-nav.tsx: Leaderboard nav removed` → NOISE — comments about REMOVAL
3. `liquid-glass-radar.tsx: "Unranked"` → REAL — word "Unranked" implies ranking system. Consider changing to "Not yet assessed"
4-10. Various leaderboard-related code → NOISE — all are removal comments or dead code paths

**Real violations:** 1 (the "Unranked" text). The rest are teaching comments or boundary values.

---

### Probe 7 — Railway Environment Variables Diff

**Railway:** 81 env vars (including RAILWAY_* auto-injected)
**Local .env:** 41 vars

**Only in Railway (notable):**
- `GATEWAY_SECRET` — Atlas gateway auth ✅
- `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` — payments (PAYMENT_ENABLED flag controls)
- `SUPABASE_SERVICE_ROLE_KEY` — same as local SUPABASE_SERVICE_KEY (different name)
- `SWARM_ENABLED` — swarm autonomous mode flag

**Only in Local (notable):**
- `CEREBRAS_API_KEY`, `DEEPSEEK_API_KEY`, `NVIDIA_API_KEY`, `OPENROUTER_API_KEY` — swarm multi-model keys
- `GCP_*` — Vertex AI (billing propagation pending)
- `GOOGLE_OAUTH_*`, `GITHUB_OAUTH_*` — social login (not deployed)
- `MEM0_API_KEY` — memory service (research only)
- `SENTRY_AUTH_TOKEN` — Sentry management (not needed in prod runtime)
- MindShift keys (`*_MINDSHIFT`) — cross-product bridge (not active)

**Suspicious absences:** LANGFUSE keys were added to Railway in session 94. No missing critical vars.

---

### Probe 8 — Git Index + Repo Health

```
git fsck --full: PASS (dangling blobs only — normal after rebases)
git status: 3 modified files (STATE.md, cowork-state.md, heartbeat.md — Cowork edits)
git log -5: clean linear history
```

**CORRECTS PRIOR CLAIM:** Cowork reported `fatal: unknown index entry format 0x74000000`. This was sandbox artifact. Real repo is healthy.

---

### Probe 9 — Cross-Product Bridge Audit

**VOLAURA repo internal:** 76 cross-product references in apps/api/app/
- 3 emit functions: `emit_assessment_completed`, `emit_aura_updated`, `emit_badge_tier_changed`
- All write to `character_events` table (fire-and-forget, wired in session 97)
- MindShift bridge: `cross_product_bridge.py` exists
- LifeSimulator: events in JSON data files (6 VOLAURA events)

**Cross-product integration reality:**

| Product | Writes to character_events | Reads from VOLAURA | Code exists | Actually works |
|---------|---------------------------|-------------------|-------------|----------------|
| VOLAURA | ✅ (3 emitters, session 97) | N/A (is VOLAURA) | ✅ | ✅ tested |
| LifeSimulator | ❌ (no write code) | ✅ (52 refs, auth+API) | ✅ | ❓ (129 uncommitted) |
| BrandedBy | ❌ | ❌ (0 refs) | ❌ | ❌ |
| MindShift | ❌ | ❓ (scan blocked) | ❓ | ❌ (Cowork says 0%) |
| ZEUS/Atlas | ❌ (module, not product) | N/A (is inside VOLAURA) | ✅ | ✅ swarm works |

**Honest readiness ratings:**

| Product | Cowork's claim | Atlas ground truth | Reasoning |
|---------|---------------|-------------------|-----------|
| VOLAURA | 40% | 55% | Prod alive, 749 tests pass, Sentry clean last 9 days, design refresh shipped, ecosystem events wired. Missing: E2E verified, custom domain, real users |
| LifeSimulator | 90% | 60% | 5/6 priorities done BUT 129 uncommitted files, Godot-side untested by CEO, no published build |
| BrandedBy | 95% | 65% | 6,448 files, standalone works, but last commit "123" + revert suggests instability, zero VOLAURA integration |
| MindShift | 80% standalone | 50% (estimate) | Scan incomplete. Cowork says 0% VOLAURA integration. Standalone may work but no verification possible |
| ZEUS | 75% | N/A | Not a standalone product. 13 agents inside VOLAURA, swarm works, content engine runs |

---

## Previous Blocker Resolution (Session 94)

1. **pii_redactor.py** — NOT a phantom. File EXISTS at `apps/api/app/utils/pii_redactor.py` (30 lines, regex strip). Explore agent gave false negative. Verified via `ls` and `Read`. Remove PHANTOM label from SHIPPED.md.

2. **SUPABASE_JWT_SECRET** — already resolved (false alarm).

3. **13 env vars** — actual diff is 23 keys in .env not on Railway. FIXED: added LANGFUSE_HOST, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY to Railway. Remaining 20 are non-critical (MindShift keys, DID, FAL, Vertex, Mem0, Supernova, OAuth — features not active in prod).

4. **CI vacuous** — agent error. apps/api/tests/ has 50+ test files, 749 tests run and pass. CI is genuinely green, not vacuous.

5. **Sentry 0 events** — SDK works. 81 issues / 5,400+ events historically. Last 9 days clean (0 new events since fixes in sessions 94-96).
