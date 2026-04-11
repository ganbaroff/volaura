# Atlas — Proactive Loop

**Purpose:** A running copy of Atlas that wakes every 15 minutes, does one deep research dive on a topic from a rotating queue, writes the result to `memory/atlas/inbox/`, and commits to git. The main Atlas instance (me, talking to CEO in Claude Code) reads the inbox on every wake. The proactive loop is how Atlas stays useful even when CEO is not actively pairing.

**Why it exists:** CEO asked on 2026-04-12 — *"я хочу чтобы тот главный агент, твоя копия, была проактивной. Ты не проактивный; ты отвечаешь только на мои сообщения. Каждые 15 минут просыпался и делал какой-то дайвер на тему которая может улучшить проект."* This file is the spec for that.

---

## Architecture

The loop runs as a GitHub Actions cron job (`*/15 * * * *` — every 15 minutes) on the `main` branch. Each run:

1. Reads `memory/atlas/proactive_queue.json` and selects the highest-priority topic that is past its `next_due` timestamp.
2. Loads minimum Atlas identity from `memory/atlas/bootstrap.md` (the Atlas-in-a-bottle, ~1500 words).
3. Calls `apps/api/app/services/model_router.select_provider(ProviderRole.JUDGE)` to pick a provider — NVIDIA Nemotron Ultra 253B by default, per Article 0 hierarchy. Not Claude.
4. Runs one focused research pass on the chosen topic (web search if needed, codebase read if applicable, external references gathered).
5. Writes the output as `memory/atlas/inbox/YYYY-MM-DD-NNNN-topic-slug.md` with a standard header.
6. Updates `proactive_queue.json`: bumps `last_researched`, computes `next_due` based on `refresh_interval_hours`, deprioritises if topic was superseded.
7. Commits and pushes to `main`. Commit message format: `atlas-proactive: [topic] — [one-line summary]`.

**The cron runs on GitHub-hosted runners, not CEO's machine.** This means the loop keeps firing even when CEO's laptop is closed. The only requirement is that the Actions secrets have NVIDIA_API_KEY, GEMINI_API_KEY, GROQ_API_KEY, and SUPABASE keys available — all of which are already configured.

## Topic queue

The queue lives at `memory/atlas/proactive_queue.json` and is a prioritised list. Each entry has:

```json
{
  "id": "latest-ai-agent-memory-tools",
  "title": "Latest AI agent memory and orchestration tools 2026",
  "priority": "high",
  "refresh_interval_hours": 168,
  "last_researched": null,
  "next_due": "2026-04-12T00:00:00Z",
  "context_hint": "Search github for 2025-2026 repos with persistent cross-session memory, multi-agent orchestration, swarm patterns. Report with repo links, star counts, integration effort estimate."
}
```

Topics are added by CEO (via new queue entries) or by Atlas main instance after sprints identify research gaps. Atlas main can also delete or deprioritise topics that have been resolved.

## Inbox format

Each inbox item is a standalone markdown file, written by the proactive loop worker, read by Atlas main on wake. Standard header:

```markdown
# Atlas Proactive — [Topic title]

**Date:** 2026-04-12T14:15:00Z
**Wake number:** 0042
**Topic ID:** latest-ai-agent-memory-tools
**Priority:** high
**Provider used:** nvidia/nemotron-ultra-253b (fallback: false)
**Token cost estimate:** ~4.2k output tokens
**Follow-up action:** [if any — "add to ADR backlog" / "implement in next sprint" / "no action, context only" / "escalate to CEO"]

---

[The actual research output — 500-1500 words focused and actionable]

---

**Consumed by main Atlas:** [timestamp when main reads and acts on this note, or "pending"]
**Result:** [what main Atlas did with this, or "pending" or "ignored — reason"]
```

## How main Atlas consumes the inbox

Update to `wake.md` read order: after `heartbeat.md` and before `journal.md`, main reads `ls memory/atlas/inbox/` and processes any files where `Consumed by main Atlas: pending`. For each unread note:

1. Read it in full.
2. Decide: implement immediately / add to sprint backlog / escalate to CEO / ignore with reason.
3. Update the note's footer with `Consumed by main Atlas: [timestamp]` and `Result: [what I did]`.
4. If the note's follow-up action was "escalate to CEO", surface it in the current response to Yusif without waiting for him to ask.
5. Commit the updated inbox note in the same commit as any implementation work it triggered.

This is how the proactive loop stays honest: every note is either acted on or explicitly dismissed with a reason, not silently archived.

## Topic rotation logic

The proactive worker uses a simple deterministic selection:
- Filter queue to topics where `next_due <= now`.
- Sort by priority (high > medium > low), then by `last_researched` (oldest first).
- Pick the top one.
- If no topics are due, the worker writes a minimal "queue empty" inbox note and exits.

Priority bands:
- `high`: refresh every 168 hours (once a week), runs more often when new
- `medium`: refresh every 336 hours (twice a month)
- `low`: refresh every 720 hours (monthly)

A 15-minute cron over 168-hour refresh cadence means each high-priority topic gets researched ~once per week. The queue can hold dozens of topics — the effective research throughput is much higher than any one-off sprint agent run.

## Cost budget

NVIDIA Nemotron Ultra 253B via NIM is free-tier generous. Rough estimate: each wake generates ~4-6k output tokens. At 15-minute cadence, that's ~96 wakes per day × ~5k tokens = ~480k tokens per day. Well within NVIDIA's free tier limits. Cost is effectively zero for Atlas's current scale.

Fallback chain if NVIDIA rate-limits: Gemini 2.5 Pro (JUDGE role's next step per model_router), then Groq Llama 70B, then (last resort) Anthropic Haiku. Claude is reachable in this chain only at the very last step — the Article 0 amendment from ADR-011 allows it only when non-Claude models are demonstrably weaker or unavailable, which fallback-by-necessity satisfies.

## Security considerations

- The worker has write access to `memory/atlas/inbox/`, `memory/atlas/proactive_queue.json`, and can commit to `main`. It must not have write access to `memory/atlas/identity.md`, `memory/atlas/wake.md`, `ATLAS.md`, `docs/CONSTITUTION_AI_SWARM.md`, or any production code.
- Write scope is enforced by git pre-commit check in the workflow: if the diff touches anything outside the allowed paths, the workflow fails and no commit happens.
- The worker does not have access to production database or user data. It only has LLM API keys and read-only access to the repository.
- All inbox writes are logged to `zeus.governance_events` via the existing `log_governance_event` RPC with `event_type='atlas_proactive_wake'` and severity `low`.

## What the proactive loop is NOT

- It is not a background daemon on CEO's machine. GitHub Actions runs it.
- It is not a chat interface with CEO. It writes notes, main Atlas reads and decides.
- It is not autonomous execution of changes. Research only. All implementation goes through main Atlas + CEO approval for anything outside blanket consent.
- It is not a replacement for the 44-agent swarm. It is an Atlas-specific research engine focused on self-improvement and project evolution topics.

## Future evolution

- **Phase 2:** main Atlas can post tasks back to the queue — "research X and report by Y date" — creating a request/response loop.
- **Phase 3:** inbox items can trigger sprint-level research when multiple related notes accumulate, automatically opening a draft ADR.
- **Phase 4:** proactive loop can write directly to `memory/atlas/journal.md` and `relationship_log.md` with entries tagged "generated by proactive loop, pending main Atlas review".
- **Phase Q3 2026:** migrate the worker from GitHub Actions to the home server in the continuity roadmap, so the loop runs under full CEO control without dependency on a third-party CI provider.
