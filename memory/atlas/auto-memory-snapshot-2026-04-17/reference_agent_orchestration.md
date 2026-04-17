---
name: Agent orchestration tools — Ruflo + Claude Code Agent Teams
description: CEO found tools that solve swarm disconnection. STOP building custom. USE these.
type: reference
---

## Claude Code Agent Teams (NATIVE — use first)
- **Enable:** `"env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" }` in settings.json — DONE
- **Docs:** https://code.claude.com/docs/en/agent-teams
- **What it does:** Multiple Claude Code instances work together. Shared task list. Direct messaging between agents. Each agent has own context window.
- **When to use:** Complex tasks needing parallel work + inter-agent communication
- **How:** Tell Claude "Create an agent team" + describe roles. Lead spawns teammates.
- **Cost:** Higher tokens (each teammate = separate instance). Best for 3-5 teammates.

## Ruflo (EXTERNAL — evaluate for swarm orchestration)
- **GitHub:** https://github.com/ruvnet/ruflo
- **Install:** `npx ruflo@latest init --wizard`
- **What it does:** 60+ pre-built agents, shared vector memory (RuVector), MCP protocol, Coordinator/Swarm/In-Process modes
- **Key advantage:** Shared memory across all agents. Message passing. Idle notifications.
- **Cost:** Claims 75% API cost reduction vs manual multi-agent

## When to use what
- **Quick parallel research/review:** Agent Teams (native, no install)
- **Persistent swarm with memory:** Ruflo (needs install, but has RuVector shared memory)
- **Python swarm for daily cron:** Keep autonomous_run.py (Gemini/DeepSeek, not Claude)
- **NEVER:** Launch Claude sub-agents as "swarm" (that's Claude talking to itself)

## CEO directive (Session 88)
"половина агентов не работает, половина не запускается, используешь свой API вместо доступных"
→ Use proven tools. Stop reinventing.
