# IMPLEMENTATION ROADMAP — Swarm 2.0 + Product Sprints
**Created:** 2026-04-01 | **Synthesized from:** ZEUS repo analysis + MindShift analysis + Claude Code architecture patterns + Swarm vote results
**Status:** PLANNING — awaiting CEO approval + session execution

---

## Context: Why This Roadmap Exists

After cross-analyzing three repositories (ZEUS, MindShift, Claude Code architecture patterns), four categories of improvements were identified that the current Volaura swarm is missing. Combined with the previous swarm vote winner (Predictive Suggestions, 42/50) and the product roadmap, this gives us 8 sprints of clear, ordered work.

**What each source contributed:**
- **MindShift (v6.0 TASK-PROTOCOL):** 5-step flow, GROWTH agent patterns, burnout detection, volaura-bridge.ts already built
- **ZEUS repo:** Context Intelligence Engine, Adaptive Execution Loop, Skill Evolution (60% done), Social Delivery Pipeline (40% done)
- **Claude Code patterns:** Heartbeat gate, 3-layer MEMORY-INDEX, Outcome Verification (Tier 1 + 2), Round-2 critique loop
- **Previous swarm vote:** Predictive Suggestions (42/50 score, wins by margin)

---

## Sprints Overview

| # | Name | Est. | Priority | Source |
|---|------|------|----------|--------|
| 1 | Swarm Infrastructure P0 | 3h | CRITICAL | Claude Code + MindShift |
| 2 | Predictive Suggestions | 2h | HIGH | Swarm vote winner |
| 3 | Adaptive Execution Loop | 3h | HIGH | ZEUS |
| 4 | Context Intelligence Engine | 3h | HIGH | ZEUS |
| 5 | Skill Evolution Completion | 2h | MEDIUM | ZEUS (60% done) |
| 6 | Social Delivery Pipeline | 1.5h | MEDIUM | ZEUS (40% done) |
| 7 | MindShift + Life Sim Integration | 4h | HIGH | MindShift |
| 8 | Org Saved Search + Match Notify | 3h | HIGH | Product roadmap |

**Total: ~21.5h across 8 sprints. Recommended pace: 2 sprints/session.**

---

## Sprint 1 — Swarm Infrastructure P0
**Goal:** Fix the three structural gaps that make swarm agents unreliable between sessions.
**Est:** 3h | **Model:** sonnet | **Priority:** CRITICAL — blocks all other sprints

### What's broken now
1. **Swarm runs even when nothing changed** — heartbeat has no KAIROS gate. Agents waste tokens proposing things that were shipped 2 sessions ago.
2. **Agents can claim anything about code** — no verification that cited files/functions actually exist. Groundedness = 0%.
3. **"Done" has no definition** — when an agent says "task complete", there's no Tier 1 (deterministic) or Tier 2 (LLM judge) check.
4. **Memory is a 200-line MEMORY.md** — everything in one flat file. Topics get truncated. Agents miss critical context.

### Tasks

**1.1 — Heartbeat Gate** (`packages/swarm/heartbeat_gate.py`)
```python
# New file — ~60 lines
def should_run_swarm(project_root: Path, hours_threshold: int = 4) -> tuple[bool, str]:
    """
    Returns (should_run, reason).
    Checks 3 conditions:
    - Urgent: HIGH/CRITICAL unacted proposals in memory/swarm/proposals.json
    - Active: Recent git activity in SESSION-DIFFS.jsonl (< 8h ago)
    - Floor: > N hours since last swarm run
    """
```
Wire into `.github/workflows/swarm-daily.yml` — skip run if `should_run_swarm() == False`.

**1.2 — Proposal Verifier** (`packages/swarm/proposal_verifier.py`)
```python
# New file — ~80 lines
def verify_proposal_references(proposal_content: str, project_root: Path) -> dict:
    """
    Extract file paths from proposal text → check existence.
    Returns: {claimed_files, valid_files, invalid_files, reference_score, is_grounded}
    Threshold: is_grounded = True if reference_score >= 0.7
    """
```
Add to `autonomous_run.py` post-generation: proposals with `is_grounded=False` get flagged, not dismissed.

**1.3 — Outcome Verifier** (`packages/swarm/outcome_verifier.py`)
```python
# New file — ~100 lines
# Tier 1 (deterministic): file path checks, test counts, import checks
# Tier 2 (LLM judge): pass proposal + code diff → "did the agent actually do what it claimed?"
def verify_outcome(task: dict, before_state: dict, after_state: dict) -> VerificationResult:
    tier1 = _deterministic_check(task, before_state, after_state)
    if tier1.confidence >= 0.9:
        return tier1  # deterministic result, skip LLM
    tier2 = _llm_judge(task, before_state, after_state)  # haiku call
    return merge(tier1, tier2)
```

**1.4 — 3-Layer MEMORY-INDEX** (refactor `memory/MEMORY.md`)
- Layer 1: `MEMORY.md` → pointer index only, max 150 chars/entry, stays in context
- Layer 2: `memory/topics/*.md` → topic files loaded on demand (already structured this way)
- Layer 3: `memory/transcripts/` → grep-only, not loaded automatically
- Add `memory/topics/swarm-state.md` → current sprint goal, open proposals, last 5 outcomes

**Files changed:** `packages/swarm/heartbeat_gate.py` (NEW), `packages/swarm/proposal_verifier.py` (NEW), `packages/swarm/outcome_verifier.py` (NEW), `.github/workflows/swarm-daily.yml` (UPDATE), `autonomous_run.py` (UPDATE), `memory/MEMORY.md` (RESTRUCTURE)

**Success criteria:** `swarm-daily.yml` skips run when no git activity. Proposals with invalid file refs are flagged (not silently used). Agents can declare outcomes with a confidence score.

---

## Sprint 2 — Predictive Suggestions
**Goal:** Agents proactively surface "what you'll probably need next" before CEO asks.
**Est:** 2h | **Model:** sonnet | **Priority:** HIGH — swarm vote winner (42/50)
**Source:** Swarm DSP session, Option E won

### What it means
When an agent completes a task, it doesn't just close the loop — it looks ahead. Based on what was just done + what's in the backlog + what patterns exist, it predicts the next 2-3 actions the CEO will want.

### Tasks

**2.1 — Suggestion Generator** (`packages/swarm/suggestion_engine.py`)
```python
# ~90 lines
def generate_suggestions(
    completed_task: dict,
    backlog: list[dict],
    session_findings: list[str],
    patterns: list[str]
) -> list[Suggestion]:
    """
    Returns 2-3 prioritized suggestions with:
    - title, description, estimated_effort
    - trigger_reason: why NOW (what just happened that makes this timely)
    - confidence: float 0-1
    - linked_files: what files this would touch
    """
```

**2.2 — Inject into CEO Inbox** (`memory/swarm/ceo-inbox.md`)
Suggestions section added after HIGH/CRITICAL proposals. Format:
```markdown
## 🔮 Predicted Next Actions (auto-generated)
1. **[Title]** (~Xh) — [Why now: trigger reason]
2. **[Title]** (~Xh) — [Why now: trigger reason]
```

**2.3 — Wire into autonomous_run.py**
After `batch_closes()` step, call `generate_suggestions()` → append to CEO inbox.

**Files changed:** `packages/swarm/suggestion_engine.py` (NEW), `autonomous_run.py` (UPDATE — call suggestion_engine after batch close), `memory/swarm/ceo-inbox.md` template (UPDATE)

**Success criteria:** After each swarm run, `ceo-inbox.md` has a "Predicted Next Actions" section with 2-3 actionable items, each with a `trigger_reason` that makes sense given what was just proposed.

---

## Sprint 3 — Adaptive Execution Loop
**Goal:** Agents that can recover from failures autonomously, without CTO intervention.
**Est:** 3h | **Model:** sonnet | **Priority:** HIGH — agents currently abort on first error
**Source:** ZEUS `adaptive_executor.py` pattern

### What's missing
Current agents: execute → success or fail. No retry, no state tracking, no recovery strategy.
ZEUS pattern: `ExecutionState` enum + screenshot hashing + auto-retry with strategy change.

### Tasks

**3.1 — Execution State Tracker** (`packages/swarm/execution_state.py`)
```python
# ~120 lines
from enum import Enum

class ExecutionState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    RETRYING = "retrying"
    RECOVERING = "recovering"
    FAILED = "failed"
    SUCCESS = "success"

class AgentExecutionTracker:
    """
    Tracks: current state, attempt count, last error, recovery strategy used.
    Serializable to JSON → can be resumed across context windows.
    """
    max_retries: int = 3
    recovery_strategies: list[str]  # ["retry", "simplify", "decompose", "escalate"]
```

**3.2 — Auto-Recovery Logic** (`packages/swarm/recovery_strategies.py`)
```python
# ~80 lines
def choose_recovery_strategy(error: Exception, attempt: int, task: dict) -> RecoveryStrategy:
    """
    Maps error types to recovery strategies:
    - FileNotFoundError → "decompose" (break task into smaller steps)
    - APIError (rate limit) → "retry" with backoff
    - ImportError → "escalate" (agent can't resolve this alone)
    - Timeout → "simplify" (reduce scope, attempt partial completion)
    """
```

**3.3 — Wire into Agent Base** (`packages/swarm/agent_base.py` — UPDATE or NEW if doesn't exist)
All agents inherit `AgentBase` which wraps `execute()` with the tracker loop.

**3.4 — Failure Report Format** (update `autonomous_run.py`)
On escalate, write to `memory/swarm/escalations.md`:
```markdown
## [timestamp] ESCALATION: [agent] → [task]
- Attempts: N
- Final error: [error]
- Recovery strategies tried: [list]
- Recommended action: [human-readable]
```

**Files changed:** `packages/swarm/execution_state.py` (NEW), `packages/swarm/recovery_strategies.py` (NEW), `packages/swarm/agent_base.py` (NEW or UPDATE), `autonomous_run.py` (UPDATE), `memory/swarm/escalations.md` (NEW template)

**Success criteria:** Agent that hits a FileNotFoundError automatically decomposes its task. Agent that hits rate limit waits with backoff. Escalations are written to `escalations.md`, not silently dropped.

---

## Sprint 4 — Context Intelligence Engine
**Goal:** Agents understand semantic commands + know which files/components map to which concepts.
**Est:** 3h | **Model:** sonnet | **Priority:** HIGH — makes code-aware agents possible
**Source:** ZEUS `context_intelligence_test.py`, `smart_command_processor.py`

### What's missing
Current agents get a text description of the task. They have to guess which files to read, which functions exist, which components are affected. This causes the "citing files that don't exist" problem.

ZEUS pattern: semantic command → element binding. "Fix the login button" → `{file: apps/web/src/app/[locale]/(auth)/login/page.tsx, component: LoginContent, line: 139, type: button}`.

### Notes on ZEUS → Railway port
ZEUS `context_intelligence_test.py` uses `win32gui` (Windows-only). The Railway backend runs Linux. This means the GUI binding layer is not portable, but the **semantic mapping** layer (command → code element) is fully portable.

### Tasks

**4.1 — Code Element Index** (`packages/swarm/code_index.py`)
```python
# ~150 lines
# Builds a searchable index of the codebase:
# {file_path: {functions, components, classes, exports, imports}}
# Lightweight: parse via ast.parse (Python) + regex (TypeScript — no full TS parser)
# Refreshes on git commit via session-end.yml hook

def build_index(project_root: Path) -> CodeIndex:
    """Scans apps/api + apps/web. Returns serialized index at memory/swarm/code-index.json."""

def find_elements(query: str, index: CodeIndex) -> list[CodeElement]:
    """Semantic search: 'login button' → matching components/functions."""
```

**4.2 — Task → File Binding** (`packages/swarm/task_binder.py`)
```python
# ~80 lines
def bind_task_to_files(task_description: str, code_index: CodeIndex) -> BoundTask:
    """
    Returns task with:
    - primary_files: list[str] (agents MUST read these)
    - secondary_files: list[str] (agents SHOULD read these)
    - affected_tests: list[str] (agents must run these)
    - binding_confidence: float
    """
```

**4.3 — Inject into Agent Briefing Template** (`docs/AGENT-BRIEFING-TEMPLATE.md` UPDATE)
Add `BOUND FILES` section to the template — agents get pre-computed file list, not guessing.

**4.4 — Wire into autonomous_run.py**
Before launching agents: call `bind_task_to_files()` per task → inject bound files into each agent's context block.

**Files changed:** `packages/swarm/code_index.py` (NEW), `packages/swarm/task_binder.py` (NEW), `.github/workflows/session-end.yml` (UPDATE — rebuild index on push), `docs/AGENT-BRIEFING-TEMPLATE.md` (UPDATE), `autonomous_run.py` (UPDATE), `memory/swarm/code-index.json` (GENERATED)

**Success criteria:** Agent briefing contains `BOUND FILES: [list]`. Proposals reference only files that exist in the index. Reference score in `proposal_verifier.py` improves from baseline.

---

## Sprint 5 — Skill Evolution Loop Completion
**Goal:** Skills that improve themselves based on what worked.
**Est:** 2h | **Model:** haiku | **Priority:** MEDIUM — 60% already built in ZEUS
**Source:** ZEUS — trajectory logging exists, missing applier + A/B tester

### What exists (from ZEUS analysis)
- ✅ Trajectory logging: skill outcomes are recorded
- ✅ Suggestion generation: system generates skill improvement candidates
- ❌ Skill applier: no code that actually updates skill files based on suggestions
- ❌ A/B tester: no mechanism to compare old vs new skill performance

### Tasks

**5.1 — Skill Applier** (`packages/swarm/skill_applier.py`)
```python
# ~100 lines
def apply_skill_improvement(skill_file: Path, suggestion: SkillSuggestion) -> ApplyResult:
    """
    Reads current skill file → applies targeted edit based on suggestion type:
    - "add_example": append example to Examples section
    - "sharpen_rule": update vague rule with specific constraint
    - "remove_obsolete": delete section marked as outdated
    - "add_anti_pattern": append to NEVER DO section
    Returns: diff of what changed + backup of original
    """
```

**5.2 — A/B Tester** (`packages/swarm/skill_ab_tester.py`)
```python
# ~60 lines
# Simple: run same task twice — once with old skill, once with new skill
# Score both outputs using existing outcome_verifier.py
# Keep the winner, discard the loser
# This is cheap (haiku model) + produces measurable signal

def compare_skill_versions(task: dict, skill_v1: str, skill_v2: str) -> ABTestResult:
    """Returns: winner, score_delta, confidence"""
```

**5.3 — Wire into session-end hook** (`packages/swarm/session_end_hook.py` UPDATE)
After batch closes: run skill evolution check. For each skill with ≥5 trajectory entries → generate suggestions → apply if confidence > 0.8 → A/B test → merge winner.

**Files changed:** `packages/swarm/skill_applier.py` (NEW), `packages/swarm/skill_ab_tester.py` (NEW), `packages/swarm/session_end_hook.py` (UPDATE)

**Success criteria:** After 5 uses of any skill, `session_end_hook.py` checks if improvements exist. Skills folder shows git commits from auto-improvement runs.

---

## Sprint 6 — Social Delivery Pipeline
**Goal:** Task completion triggers multi-channel delivery (Telegram + formatted reports).
**Est:** 1.5h | **Model:** haiku | **Priority:** MEDIUM — 40% already in ZEUS codebase
**Source:** ZEUS — social delivery 40% complete, not connected to agent completion

### What exists (from ZEUS analysis)
- ✅ Telegram notifications (already wired in Volaura — `notification_service.py`)
- ✅ Basic batch close report in `autonomous_run.py`
- ❌ Formatted Word/PDF reports (ZEUS has this, Volaura doesn't)
- ❌ Per-task completion summary with evidence

### Tasks

**6.1 — Report Generator** (`packages/swarm/report_generator.py`)
```python
# ~80 lines
def generate_batch_report(batch_results: list[TaskResult]) -> BatchReport:
    """
    Structured report with:
    - Executive summary (3 lines — CEO protocol format)
    - Per-task: what changed, files modified, test delta
    - Risk flags: any escalations, any low-confidence outcomes
    - Next predicted actions (from Sprint 2 suggestion engine)
    """
```

**6.2 — Telegram Formatter** (update `notification_service.py`)
Current: plain text. New: structured with emoji sections, code blocks for file diffs, inline keyboard for "approve/defer" on suggested next actions.

**6.3 — Wire CEO inbox generation into report**
`ceo-inbox.md` auto-generated from `generate_batch_report()` output — not hand-written.

**Files changed:** `packages/swarm/report_generator.py` (NEW), `apps/api/app/services/notification_service.py` (UPDATE — richer Telegram format), `autonomous_run.py` (UPDATE — call report_generator at batch close)

**Success criteria:** After every swarm run, CEO gets a Telegram message with: summary line + changed files count + any escalations + 2-3 predicted next actions with inline buttons.

---

## Sprint 7 — MindShift + Life Sim Integration
**Goal:** Cross-product event bus live. Actions in Volaura create events visible in MindShift + Life Simulator.
**Est:** 4h | **Model:** sonnet | **Priority:** HIGH — foundation of ecosystem value prop
**Source:** MindShift `volaura-bridge.ts` already built, `rewards.py` already emits events

### What exists
- ✅ `apps/api/app/routers/rewards.py` — already emits `crystal_earned`, `skill_verified`, `xp_earned` to `character_events` table
- ✅ MindShift `volaura-bridge.ts` — fire-and-forget calls to Volaura API
- ✅ `character_events` table — cross-product event bus schema exists in migrations
- ❌ Volaura → MindShift direction not wired (bridge is MindShift → Volaura only)
- ❌ Life Sim has no bridge (Godot 4, needs REST polling)
- ❌ Assessment completion doesn't trigger crystal award (rewards.py not called from assessment.py)

### Tasks

**7.1 — Wire assessment completion → crystal award** (`apps/api/app/routers/assessment.py`)
In `complete_assessment()`, after AURA score saved:
```python
from app.routers.rewards import emit_character_event
await emit_character_event(user_id, "skill_verified", {
    "competency": session.competency_slug,
    "score": aura_score,
    "crystals": _compute_crystal_reward(aura_score)
})
```

**7.2 — VOLAURA → MindShift push** (`apps/api/app/services/cross_product_bridge.py`)
```python
# New file — ~60 lines
async def notify_mindshift(user_id: str, event_type: str, payload: dict) -> None:
    """
    Fire-and-forget POST to MindShift API when Volaura user earns XP/crystals.
    Uses shared Supabase auth token (both apps share same auth project).
    Fails silently — never blocks the main request.
    """
```

**7.3 — Life Sim polling endpoint** (`apps/api/app/routers/character.py`)
```python
# New file — ~80 lines
GET /api/character/events?since={timestamp}&user_id={uid}
# Returns: list of character_events for Godot 4 to poll
# Auth: service_role key (Life Sim is not a user-facing app, it's a client app)
# RLS: service_role bypasses — Life Sim pulls its own user's events
```

**7.4 — Crystal ledger display** (`apps/web/src/app/[locale]/(dashboard)/dashboard/page.tsx`)
Add crystal balance widget: reads from `character_events` aggregate. Small, non-intrusive. Links to Life Simulator (when ready).

**7.5 — MindShift Supabase auth sync** (`apps/api/app/routers/auth.py`)
When user registers on Volaura, also create profile stub in MindShift Supabase (`SUPABASE_URL_MINDSHIFT`). Silent — doesn't block registration.

**Files changed:** `apps/api/app/routers/assessment.py` (UPDATE — wire rewards), `apps/api/app/services/cross_product_bridge.py` (NEW), `apps/api/app/routers/character.py` (NEW), `apps/web/src/app/[locale]/(dashboard)/dashboard/page.tsx` (UPDATE — crystal widget), `apps/api/app/routers/auth.py` (UPDATE — MindShift profile sync), locale files (UPDATE — crystal i18n keys)

**Success criteria:** Complete an assessment on volaura.app → `character_events` row appears. MindShift can query Volaura events. Life Sim Godot client can poll `/api/character/events`.

---

## Sprint 8 — Org Saved Search + Match Notifications
**Goal:** Organizations save search filters → get notified when new talent matches.
**Est:** 3h | **Model:** sonnet | **Priority:** HIGH — B2B retention + repeat activation
**Source:** Previous swarm proposals (Option E, not yet implemented)

### Tasks

**8.1 — Saved Search Schema** (migration)
```sql
CREATE TABLE org_saved_searches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    filters JSONB NOT NULL,  -- same structure as discovery query params
    notify_on_match BOOLEAN DEFAULT true,
    last_checked_at TIMESTAMPTZ DEFAULT now(),
    created_at TIMESTAMPTZ DEFAULT now()
);
```

**8.2 — Save Search API** (`apps/api/app/routers/organizations.py`)
```
POST /api/organizations/{org_id}/saved-searches
GET  /api/organizations/{org_id}/saved-searches
DELETE /api/organizations/{org_id}/saved-searches/{search_id}
```

**8.3 — Match Checker** (`apps/api/app/services/match_checker.py`)
```python
# Runs as pg_cron or via GitHub Actions daily
# For each saved search with notify_on_match=True:
#   Run the same discovery query
#   Compare with last_checked_at → find new matches
#   If new matches: send Telegram + email notification to org admin
```

**8.4 — Frontend: Save Search Button** in discovery page
After applying filters, "Save this search" button → modal to name it. Saved searches list in org settings.

**8.5 — Match notification format** (Telegram)
```
🎯 New talent match for "Your saved search name"
3 new professionals match your criteria:
• Leyla A. — AURA 82 | Communication + Leadership
• Kamal R. — AURA 78 | Tech + Reliability
[View all matches →]
```

**Files changed:** `supabase/migrations/[timestamp]_org_saved_searches.sql` (NEW), `apps/api/app/routers/organizations.py` (UPDATE), `apps/api/app/services/match_checker.py` (NEW), `apps/api/app/schemas/organizations.py` (UPDATE), `apps/web/src/app/[locale]/(org)/org-discover/page.tsx` (UPDATE — save button), `apps/web/src/app/[locale]/(org)/settings/page.tsx` (UPDATE — saved searches list), locale files (UPDATE)

**Success criteria:** Org creates a saved search. When a new user completes assessment matching the filters, org receives Telegram notification within 24h. Org can view/delete saved searches in settings.

---

## TASK-PROTOCOL v6.0 Changes

Based on MindShift's more mature v6.0 protocol, these additions to TASK-PROTOCOL.md are recommended:

### Changes from v5.3 → v6.0

1. **Step 0 becomes "Detect + Read"** (not just "read required files")
   - Read SESSION-DIFFS.jsonl → understand WHAT CHANGED since last run
   - Read `memory/swarm/code-index.json` → know what files exist
   - Explicitly: "I am aware of X changes since last batch. Relevant to this sprint: Y."

2. **Step 2 "Propose" includes trigger-reason** (from Predictive Suggestions)
   Each proposal must state WHY NOW: what recent event makes this timely.

3. **Step 4 "Debate" has a Round-2 gate** (from Claude Code patterns)
   If top proposal < 35/50 confidence AND delta to #2 < 5 points → mandatory Round 2 debate.

4. **Step 5 "Execute" includes outcome verification** (Sprint 1 outcome_verifier)
   Agent cannot mark task DONE without running `verify_outcome()` or writing explicit manual verification steps.

5. **New: Session-End Skill Evolution Check** (from Sprint 5 above)
   After batch closes: check if any skill has ≥5 trajectories → auto-suggest improvements.

---

## Documentation Updates Required (this session)

| File | What to update | Priority |
|------|---------------|----------|
| `docs/TASK-PROTOCOL.md` | v5.3 → v6.0 changes above | HIGH |
| `memory/swarm/shared-context.md` | Add sprint-level tracking for Sprints 1-8 | MEDIUM |
| `memory/swarm/SHIPPED.md` | Add session notes from this planning session | MEDIUM |
| `memory/context/sprint-state.md` | Current position → Sprint 1 planning done | HIGH |
| `docs/DECISIONS.md` | Retrospective: session findings → this roadmap | HIGH |

---

## Execution Order Recommendation

```
Session N (today):     Sprint 1 (Swarm Infrastructure P0)
Session N+1:          Sprint 2 (Predictive Suggestions) + Sprint 3 (Adaptive Execution)
Session N+2:          Sprint 4 (Context Intelligence) + Sprint 5 (Skill Evolution)
Session N+3:          Sprint 6 (Social Delivery) + Sprint 7 (MindShift Integration)
Session N+4:          Sprint 8 (Org Saved Search)
```

**Parallelism notes:**
- Sprints 1-6 are swarm infrastructure — can run in parallel within a session if multiple agents used
- Sprint 7 requires Sprint 1 (outcome verification needed before cross-product events go live)
- Sprint 8 is independent of 1-7 — can start any time

---

## Open Questions for CEO (1 decision needed)

**Q: Should Sprint 7 (ecosystem integration) use the MindShift Supabase project for cross-product auth sync?**

Context: MindShift uses `awfoqycoltvhamtrsvxk` (separate Supabase project). Volaura uses `dwdgzfusjsobnixgyzjk`. Currently they're separate with no shared session state.

Options:
- **A (migrate):** Move MindShift to use Volaura's Supabase project. One auth, full user sharing. More complex migration.
- **B (bridge):** Keep separate projects. When user registers on Volaura, call MindShift's API to create stub profile using service key. Lower risk, slightly redundant.
- **C (defer):** Skip auth sync for now. Just emit events. MindShift pulls events from Volaura by user ID.

**CTO recommendation: Option C** — emit events first, prove the value, migrate auth later when both products have real users. Reversible. Option A is a production migration that can't be undone without downtime.
