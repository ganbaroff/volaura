# Handoff — Path E: consolidate-memory pass over VOLAURA/memory/

## STATUS
**READY 2026-04-18 Baku.** Parallelizable with Path B (LiteLLM). Cowork-Atlas tried Agent(sonnet) twice — both rejected with "Prompt is too long" (Agent spawn context limit inside long-lived Cowork session). Move execution to Terminal-Atlas where Sonnet hands-work runs cheaper and without the Cowork context tax.

## TARGET TOOL
Claude Code CLI (Terminal-Atlas) inside `C:/Projects/VOLAURA/` or wherever the working copy lives. `/model sonnet` before starting — this is hands-work, not strategy.

## GOAL
Apply the `consolidate-memory` skill over `/sessions/elegant-fervent-carson/mnt/VOLAURA/memory/` (Windows equivalent: `C:\Projects\VOLAURA\memory\`). CEO flagged ~1083 md files ecosystem-wide as doc-debt. Start with VOLAURA tree; MindShift + others later passes.

## TASKS

### T1. Read the skill
`C:\Users\user\.claude\skills\consolidate-memory\SKILL.md` (or equivalent path on the machine where Terminal-Atlas runs). Follow its instructions literally.

### T2. Apply to VOLAURA memory tree
Target: `C:/Projects/VOLAURA/memory/` (recursive).

## HARD CONSTRAINTS
- **Never delete.** Move to `memory/archive/2026-04-18/` with short note.
- **Preserve as-is** (live files, not memory):
  - `memory/atlas/journal.md`
  - `memory/atlas/CURRENT-SPRINT.md`
  - `memory/atlas/heartbeat.md`
  - `memory/atlas/wake.md`
  - Any file under `memory/atlas/handoffs/` dated `2026-04-18-*`
  - Any file under `memory/atlas/inbox/` modified in the last 7 days
  - Any file under `memory/decisions/`
- **Do not touch** `.claude/rules/*.md` — operating principles, not memory.
- Merge duplicate facts into the more canonical location. Leave a 3-line pointer in the archived copy:
  ```
  # ARCHIVED 2026-04-18
  # Canonical location: <path>
  # Reason: <one line>
  ```
- Stale facts (dated >30 days old AND contradicted by newer content) → archive with note.
- Ambiguous decisions → list in return report, do not touch.

## ACCEPTANCE
1. Report saved to `memory/atlas/inbox/2026-04-18-consolidate-memory-report.md`.
2. MD count before / after in the report.
3. `git status` shows only moves under `memory/` and the new report. No deletions.
4. Commit: `chore(memory): consolidate VOLAURA memory tree (Path E phase 1)`.

## RETURN CONTRACT
```
FILES SCANNED: <count>
MERGES PERFORMED: <count> (see report for list)
FILES ARCHIVED: <count>
INDEX FIXES: <list>
NEEDS CEO JUDGMENT: <list or "none">
TOTAL MD BEFORE: <n>
TOTAL MD AFTER: <n>
COMMIT: <sha>
BLOCKERS: <list or "none">
```

## NON-GOALS
- Do NOT touch MindShift, Life Simulator, BrandedBy, or ZEUS trees in this pass.
- Do NOT restructure the directory layout. Only merge / archive / index-fix.
- Do NOT rewrite file contents except for the 3-line archived pointers.
