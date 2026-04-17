---
name: Breadcrumb protocol for memory survival
description: Write state to disk before/during/after work. Survives context compression.
type: feedback
---

Always maintain `.claude/breadcrumb.md` as living working memory.

**Why:** Claude loses context during compression. CEO identified this as #1 CTO failure mode (session 88). When context is compressed, CTO forgets what it was doing, why, and what decisions were already made. Breadcrumb on disk = persistent state that survives any compression.

**How to apply:**
1. **Before work:** Write to `.claude/breadcrumb.md` — what am I doing, why, what files will I touch
2. **During work:** Update checkpoints as each step completes
3. **After compression:** Read `.claude/breadcrumb.md` FIRST to recover context
4. **After work complete:** Update breadcrumb with results, commit hashes, decisions made

**Format in breadcrumb.md:**
- NOW: current task + reason
- CHECKPOINTS: progress list with [x] marks
- CONTEXT: critical facts that must survive compression
- DECISIONS: irreversible choices made this session
- LAST COMPLETED: commit hashes for verification

**Rule:** If breadcrumb.md doesn't exist at session start, create it immediately.
