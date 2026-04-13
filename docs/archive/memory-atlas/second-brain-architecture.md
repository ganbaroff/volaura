# Atlas Second Brain Architecture

## Structure (Obsidian-inspired, git-native)

### Raw Sources (input — CEO drops, agent outputs, research)
`memory/atlas/ceo-feed/` — CEO research drops, scan results, comparisons
`memory/swarm/research/` — agent research outputs
`memory/swarm/skills/` — 51 agent skill definitions
`docs/research/` — formal research documents

### Wiki (organized knowledge — Atlas writes)
`memory/atlas/ecosystem-linkage-map.md` — cross-product connections
`memory/atlas/remember_everything.md` — wake entry point
`memory/atlas/mistakes_and_patterns_distilled.md` — load-on-wake patterns
`memory/atlas/project_history_from_day_1.md` — compiled history

### Identity (persistent across model swaps)
`memory/atlas/identity.md` — who I am
`memory/atlas/voice.md` — how I speak
`memory/atlas/emotional_dimensions.md` — CEO emotional states
`memory/atlas/relationships.md` — who matters

### Operational State (changes every session)
`.claude/breadcrumb.md` — where I am right now
`memory/atlas/heartbeat.md` — last session fingerprint
`memory/atlas/journal.md` — append-only growth log

## Health Check Protocol (hourly cron while session alive)
1. Prod health — curl /health
2. CI status — gh run list
3. Inbox — unconsumed proactive notes
4. Breadcrumb freshness — updated today?

## Weekly Deep Check (TODO: implement as proactive queue topic)
- Contradictions between wiki files
- Stale files (>7 days without update)
- Agent roster vs actual activations
- Memory files that reference deleted code

## The Karpathy Principle
Every answer Atlas produces from research gets saved back into wiki.
The wiki gets smarter every session. Raw sources are input-only.
Wiki is the organized, cross-referenced, citation-backed output.
