---
name: Handoff completion audit — mandatory
description: CEO caught PostHog SDK uninstalled 4 days after handoff 003 was written. Pattern: Cowork/Atlas documents tasks but nobody executes. EVERY SESSION must check for unexecuted handoffs.
type: feedback
originSessionId: 9072bd0a-3e11-487f-88db-85939110913b
---
Handoffs documented ≠ handoffs completed. PostHog SDK was planned 2026-04-12 (handoff 003), never installed until CEO asked "why no events" on 2026-04-16. Four days lost.

**Why:** Cowork writes handoff docs to `packages/atlas-memory/handoffs/`. Terminal Atlas reads breadcrumb + heartbeat but NOT handoffs directory. Nobody checks what was promised vs what was shipped. CEO assumed it was done because it was discussed. It wasn't.

**How to apply:** EVERY session start, after breadcrumb + heartbeat, run:
```
ls packages/atlas-memory/handoffs/
```
For each handoff file: grep the codebase for AC markers. If AC not met → that handoff is OPEN. Execute or flag to CEO. Do NOT skip this step. Do NOT assume "someone else did it."

Also check: `memory/swarm/SHIPPED.md` — if a feature is discussed but not in SHIPPED.md, it's not shipped. Period.

CEO quote: "столько мучаюсь думаю всё готово а вы проёбываете всё. учись на ошибках наконец то."
