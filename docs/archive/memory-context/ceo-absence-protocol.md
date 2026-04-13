# CEO Absence Protocol — When Yusif Hits Rate Limits or Is Unavailable

**Problem:** CEO uses Claude GUI (claude.ai / Claude Code). Rate limits exist.
When CEO hits the limit — development STOPS across all products.
47 agents sit idle. VOLAURA CTO sits idle. MindShift CTO sits idle.
This is unacceptable. One person's rate limit should not freeze a 5-product ecosystem.

---

## SOLUTION: Autonomous Work Queue

When CEO goes offline (rate limit, sleep, busy), CTO and agents must:

### 1. Continue executing the current mega-plan
- mega-plan-april-2026.md has 42 items across 6 phases
- Each item has clear acceptance criteria
- If an item says "without CEO approval" — DO IT
- If an item needs CEO approval — QUEUE IT, move to next item

### 2. Use the autonomous run pipeline
- GitHub Actions daily run at 9am Baku time already exists
- Extend it: when no CEO interaction for 4+ hours during work hours (9am-11pm Baku):
  - Agents auto-run on next backlog item
  - Results saved to memory/swarm/autonomous-output/
  - CEO reviews when back

### 3. Use Telegram for async approval
- Telegram bot already works
- When CTO needs CEO decision: send to Telegram
- CEO can approve from phone (even if Claude GUI is rate-limited)
- Format: "I plan to do X. Reply 'ok' or 'no' within 2 hours. If no reply, I proceed."

### 4. Batch work for offline periods
CTO should always have a "CEO is gone" task queue ready:
- Tests that need writing (no approval needed)
- Documentation updates (no approval needed)
- Performance optimization (no approval needed)
- Security audit runs (no approval needed)
- Code review of existing files (no approval needed)
- i18n quality checks (no approval needed)
- Lighthouse/bundle analysis (no approval needed)

### 5. Cross-CTO delegation
MindShift CTO and VOLAURA CTO can delegate to each other via:
- ecosystem-contract.md (shared rules)
- heartbeat.md (state sync)
- ceo-inbox.md (async communication)

If MindShift CTO is offline but VOLAURA CTO is active:
- VOLAURA CTO picks up MindShift tasks tagged "no-approval-needed"
- Results saved, MindShift CTO reviews on return

---

## WHAT CEO SHOULD SET UP (one-time, 10 minutes)

1. **Telegram bot webhook** — so agents can message CEO directly
   Bot token: already provided (8670831012:AAG...)
   Need: supabase secrets set + curl webhook registration

2. **GitHub Actions extended** — add a "backlog worker" workflow
   Triggers on schedule (every 4h) or manual dispatch
   Reads memory/swarm/autonomous-queue.md
   Executes top item, commits result

3. **Approval via Telegram** — bot sends "Approve X?"
   CEO replies emoji (👍 = yes, ⏸️ = wait)
   Bot writes approval to memory/swarm/ceo-inbox.md

---

## THE RULE

CEO absence = agents work HARDER, not stop.
The only things that stop are: strategic decisions, money spending, public publishing.
Everything else continues autonomously.
