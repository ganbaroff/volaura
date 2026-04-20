# Handoff — Path A: Life Simulator Beehave+LimboAI audit for show-stopper #52

## TARGET TOOL
Terminal-Atlas (Claude Code CLI) on the **local machine where the Godot 4.6.1 Life Simulator repo lives**.

## GOAL
Diagnose the VolauraAPIClient parse-order show-stopper on Godot 4.6.1, decide whether Beehave (behavior-tree) + LimboAI (FSM/HTN) adoption unblocks it, and if yes produce the minimal integration PR.

## PREREQUISITE — CONFIRMED 2026-04-18 Baku
```
GODOT_REPO_PATH=C:\Users\user\OneDrive\Desktop\BestGame\life-simulator-2026
```
Run Terminal-Atlas inside that directory:
```
cd "C:\Users\user\OneDrive\Desktop\BestGame\life-simulator-2026"
```

## GODOT 4.6.1 PARSE-ORDER INVESTIGATION HINTS
Before diving, probe these five 4.6.x regressions in this order (highest prior probability first):

1. **Autoload order vs `@tool` scripts executed at editor load.** 4.6 runs `@tool` scripts during project import BEFORE all autoloads resolve. If any Beehave/LimboAI node or `VolauraAPIClient`-adjacent script uses `@tool` and touches an autoload singleton in `_enter_tree()` / `_init()`, the parse fails with `Identifier not declared` or `Null instance`. Grep: `grep -rn "@tool" --include="*.gd"` cross-referenced with autoload references.

2. **`class_name` cycles.** 4.6 tightened circular-import detection across `class_name`-declared scripts. If `VolauraAPIClient` has `class_name` and references a project script that references back (even transitively), editor fails the parse silently. Check every `class_name` in `addons/` + `scripts/`, draw the dependency graph, look for cycles.

3. **GDScript 2.0 strict typed-dictionary syntax.** 4.6 rejects `Dictionary[String, Variant]` patterns that 4.5 accepted in certain positions (return types, const decls). LimboAI blackboards heavily use typed dictionaries. Grep: `grep -rn "Dictionary\[" --include="*.gd"`.

4. **`await` in `_ready()` before autoload is done.** 4.6 changed the timing of `child_entered_tree` / `ready` relative to autoloads. Any BTRoot or API client that awaits `get_tree().process_frame` in `_ready()` before the autoload finished its own `_ready()` now races. Grep: `grep -rnE "_ready|_enter_tree" --include="*.gd" | grep await`.

5. **Signal connection with wrong arity.** 4.6 strictly validates signal callback signatures at connect time. Any `tick_finished.connect(_on_finished)` where `_on_finished` has the wrong arg count fails loudly. Run the editor with `--verbose` and grep the log for `Expected X argument(s)`.

If none of the five match: `git bisect` between 4.5.x last-known-good and 4.6.1 on the Godot editor binary itself, running the project on each commit.

## CONTEXT

### What is broken (from task #52, VOLAURA backlog)
Life Simulator's `VolauraAPIClient` (GDScript) fails to parse on Godot 4.6.1. Likely symptoms (to be verified by repro):
- Autoload order bug — `VolauraAPIClient` references a singleton that isn't loaded yet
- `@tool` script executing in editor before deps are ready
- GDScript 2.0 type-checker rejection of dynamic typing pattern valid in 4.5 but not 4.6
- Signal connection race (connected before `ready`)

### Why Beehave + LimboAI matter here
- **Beehave** — Godot 4 behavior-tree addon. Separates agent decision logic (select-task, evaluate-condition, execute-action) from the monolithic API client.
- **LimboAI** — Godot 4 FSM + HTN addon. Explicit state machine for agent lifecycle (`idle → planning → acting → reflecting`).

If the show-stopper is caused by agent logic entangled with API-client lifecycle, migrating the agent-brain portion into Beehave/LimboAI may isolate the bug. If the show-stopper is purely a 4.6 API change, Beehave/LimboAI don't help — report back and we pivot.

### Ecosystem constraints (from VOLAURA/CLAUDE.md)
- Life Simulator is face #3 of Atlas (see DESIGN-MANIFESTO.md). Accent `#F59E0B`, density high, narrator character.
- Must write `character_events` to shared Supabase (same table as VOLAURA + MindShift).
- Must respect 3 energy modes (Full/Mid/Low).
- Foundation Law #1: no red hues. Error overlays `#D4B4FF` purple, warnings `#F59E0B` amber.

## TASKS

### T1. Reproduce the bug (NO fixes yet)
- Open repo in Godot 4.6.1.
- Capture editor errors, autoload-order warnings, and any parse errors verbatim.
- Save to `docs/life-simulator/2026-04-18-repro-log.md` (or in-repo docs path if different).

### T2. Root-cause analysis
- Identify the TRUE cause from three candidates:
  - Autoload order
  - GDScript 2.0 strictening in 4.6
  - Signal/ready race
  - Something else entirely
- Use `git bisect` between last-known-good Godot version and 4.6.1 if a regression boundary is findable.
- Do NOT attempt fix yet.

### T3. Beehave + LimboAI feasibility decision
Write a short section in the repro-log with:
- Would migrating agent-brain to Beehave + LimboAI isolate the cause? (yes/no/partial)
- If yes: which files move where, rough diff estimate.
- If no: what's the minimal fix without Beehave (e.g., reorder autoload, add null-guard, swap `@tool` for runtime-only).

### T4. Minimal fix — only the smallest change that unblocks
- Ship the SMALLEST diff that compiles clean on 4.6.1 and lets the scene load.
- Behavior-tree migration can be a follow-up PR, not this one.
- If Beehave/LimboAI truly is the correct first step (T3 says yes-and-smaller-than-alternatives), then do install both addons from their official GitHub releases into `addons/beehave/` and `addons/limboai/`, and migrate only the brain-of-one-agent as proof of concept — not all agents.

### T5. Character_events write verification
After the fix, open the scene, run one agent action, and verify a row lands in Supabase `character_events`:
```sql
SELECT * FROM character_events ORDER BY created_at DESC LIMIT 3;
```
If no row appears, the API client is still broken and fix is incomplete.

## NON-GOALS
- Do NOT upgrade Godot past 4.6.1.
- Do NOT rewrite the ZEUS integration.
- Do NOT add new ecosystem features (no new faces, no new event types).
- Do NOT change the ecosystem-design-gate (accent, density, motion).
- Do NOT touch the VOLAURA backend API — only the client side.

## ACCEPTANCE
1. `docs/life-simulator/2026-04-18-repro-log.md` exists with editor errors captured.
2. Root-cause identified and documented.
3. Beehave+LimboAI adoption decision documented (yes with scope, or no with alternative).
4. If fix applied: scene opens without errors on Godot 4.6.1, one character_event row appears in Supabase after manual agent trigger.
5. Commit message: `fix(life-sim): unblock Godot 4.6.1 parse-order (#52)` — local commit only, no push.

## RETURN CONTRACT
```
GODOT_REPO_PATH: <path>
REPRO STATUS: <reproduced | could not reproduce>
ROOT CAUSE: <one sentence>
BEEHAVE DECISION: <yes-scope | no-alternative | deferred>
FIX APPLIED: <yes | no>
COMMIT: <sha | skipped>
CHARACTER_EVENTS WRITE: <verified | not verified | N/A>
BLOCKERS: <list, or "none">
```
