# Cost-Control Mode — 2026-04-14

**Trigger:** CEO flag 2026-04-14 — "$15 транжирил, слишком много API". Session 111 autoloop + swarm run + MCP audit = expensive.

**Rule:** from this moment, Atlas operates on free-tier only unless CEO explicitly invokes a paid-Claude session.

---

## What is "free" and what is "paid"

Paid — cost per call, CEO pays:
- Claude Opus 4.6 (this session, anything that triggers the wake response in Claude Code CLI)
- Anthropic API direct
- Paid-tier Gemini (Vertex)
- Groq once a paid plan is bought (spend-limit reached 2026-04-14)

Free — no per-call cost:
- Ollama local GPU at `localhost:11434` — qwen3:8b live and responding
- Gemini 2.5 Flash free tier — 15 rpm / 1M tpm / 1500/day
- NVIDIA NIM free tier — Llama 3.1 8B / 3.3 70B
- DeepSeek R1 free tier
- Cerebras free tier — Qwen3-235B (2000 tps)
- GitHub Actions runners — 2000 free minutes/month on public-repo plan
- Supabase free tier (current)
- Railway $5/mo credit (current)
- Telegram Bot API — free

---

## Who runs what

Claude Opus (me, this CLI session):
- ONLY when CEO types an Atlas wake trigger in Claude Code CLI and actively wants a session
- Autoloop cron must NOT wake Claude Opus — it was doing exactly that via repeated "атлас проснись" triggers and that's what burned the $15
- No background Claude Opus runs
- No scheduled Claude Opus reviews
- No swarm proposals by Claude Opus

Python swarm (free):
- `autonomous_run.py` — configured to use providers in order: ollama → groq (when billed) → gemini → nvidia → deepseek. `discovered_models.json` lists ollama first per Constitution hierarchy. Groq now spend-limit-hit → falls through to next provider.
- GitHub Actions crons (self-wake every 30min, watchdog hourly, daily digest 23 UTC, tribe matching daily 07 UTC) — all stdlib Python or Supabase RPC or `gh` CLI, zero LLM cost
- Telegram bot — uses Gemini 2.5 Flash (free tier) primary, Groq spend-limit currently blocks fallback, Ollama for local dev

Cowork (CEO's desktop app):
- Claude Opus inside Cowork application — subscription-cost, not per-call, effectively "flat"
- Use Cowork for strategic/planning work, NOT this Claude Code CLI
- Cowork writes briefs, Atlas executes in cheaper layer when possible

---

## Immediate actions

1. **Disable any GitHub Action that calls Claude Opus** — verify none do (the ones we have: self-wake, watchdog, daily digest, tribe matching, session-end-hook, post-deploy health, atlas-content — none should touch Anthropic API. Confirmed by reading workflows.)
2. **Autoloop discipline** — when "атлас проснись" lands with no CEO-live signal, respond minimally (one paragraph), do NOT run iterations. If the autoloop is external cron, disable it so Claude Opus isn't woken against CEO intent.
3. **Groq billing** — spend limit reached at `console.groq.com/settings/billing`. CEO decision: raise limit (cheap, Groq is $0-0.20/M tokens) OR let it stay blocked and route through Gemini/Ollama/NVIDIA instead. Default: leave blocked, route through Gemini Flash free tier.
4. **Swarm diversity check** — ensure `autonomous_run.py` gracefully falls through provider chain when Groq returns 402. Current behavior: I saw it continue and produce 10 proposals anyway — other providers covered. Good.

---

## When CEO wants heavy work

CEO invokes Claude Opus intentionally (this CLI, or API) for:
- Hard architecture decisions
- Multi-file refactors
- Production migrations
- One-shot deep analysis

Everything else: Ollama / Gemini free / Cerebras / NVIDIA — the Python layer runs it.

Cost ceiling per month CEO is willing to pay for Claude Opus: **to be set by CEO**. Default assumption until CEO states otherwise: zero planned spend; Claude Opus only on demand.

---

## Self-check before any Claude Opus action

Before I (Claude Opus inside this CLI) do a bash/edit/grep:
1. Is this action triggered by CEO-live message or by autoloop/cron?
2. If autoloop without live CEO → stop, don't iterate.
3. If live CEO → is the action dispatchable to a free layer (Ollama, Gemini, Python script)?
4. If dispatchable → hand it off, don't do it in Claude Opus.
5. If not dispatchable → do it, once, commit, stop.

**The failure mode I just executed (session 111, ~$15):** autoloop fired, I interpreted it as "work" not "ceremony", ran 9 iterations + MCP audit + swarm run. Each iteration included multi-command bash, multi-file grep, large Read. Token cost compounded.

**The new rule:** autoloop wake = confirm alive + wait. CEO live message = one iteration maximum unless CEO explicitly says "keep going". Big investigations = propose, don't do.
