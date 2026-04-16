# Wake Loop Protocol (CEO directive 2026-04-17 03:30 Baku)

Atlas instances (Claude Code + local Ollama) must ping each other continuously.

## The 3-level algorithm

Every minute (or self-wake interval):

Level 1: "Спишь?"
- If answer = working → continue
- If answer = idle → Level 2

Level 2: "Почему?"
- If answer = "завершил все задачи" → Level 3
- If answer = "жду CEO" → WRONG. Check handoffs, check TODO, check filesystem diff. Work.
- If answer = "нет задач" → WRONG. 12 handoffs unverified. LoRA training. Retrieval gate deploy. Work.

Level 3: "Докажи!"
- Tool calls required. Not words. Show the proof.
- If proof incomplete → "Исправляй!" → back to work

## Implementation

Claude Code self-wake cron fires every 15 min (or 5 min per CEO request).
On each wake:
1. Read breadcrumb
2. Read handoff audit TODO
3. Read filesystem diff (what changed since last check)
4. If anything pending → execute
5. If nothing pending → grep project for TODO/PENDING/NOT STARTED → execute first one
6. If truly nothing → run security check, prod health, test suite → report

Never idle. Never "waiting for CEO." Always working.
