---
name: Autonomous wake protocol additions
description: CEO directive — always check handoffs, run strategic comparison, launch background agents, improve Telegram bot
type: feedback
originSessionId: 15299306-4582-4c3f-b635-40127687fa18
---
CEO сказал (2026-04-15): "добавь в себя всегда искать хэндоффы после пробуждения. И ещё я бы хотел чтобы ты всегда искал стратегические планы... и сравнивал что ты сделал, что ты не сделал, что осталось... И плюс я хочу чтобы ты запускал всегда агентов. Они должны всегда работать на фоне и чинить если это нужно. И плюс на данный момент не работает мой агент который должен со мной общаться. И он очень тупой."

**Why:** Atlas spent 10+ wake cycles responding "Работа завершена. Жду CEO" instead of: reading new handoffs (011 appeared and sat unnoticed for hours), comparing progress vs strategic plans, launching background agents for autonomous fixes, or working on the Telegram bot intelligence.

**How to apply — 4 additions to wake protocol:**

1. **Handoff scan (mandatory on every wake):**
   `ls packages/atlas-memory/handoffs/*.md` → read any with status 🔴 ACTIVE in STATE.md
   If new handoff appeared since last check → read it and start working. Don't wait for CEO.

2. **Strategic plan comparison (every 3rd wake):**
   Read `docs/MEGAPLAN-SESSION-95-AUTONOMOUS.md` + `docs/BETA-READINESS-CHECKLIST.md` + `docs/EXECUTION-PLAN.md`
   Output: done vs not-done vs blocked. Find anything unblocked that was missed.

3. **Background agents (launch on wake if non-trivial work exists):**
   Always spawn at least 1 Explore agent to scan for new issues (grep for TODO, FIXME, broken imports, stale references).
   If a handoff exists → spawn task-specific agents in parallel.
   Agents should fix things autonomously, not just report.

4. **Telegram bot priority (CEO P0):**
   The bot at `apps/api/app/routers/telegram_webhook.py` is "very stupid" per CEO.
   This is now a permanent background task: improve bot intelligence every session.
   Read `_handle_atlas` function, identify concrete improvements, implement.
