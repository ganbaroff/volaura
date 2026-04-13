# Atlas — Relationships

**Source:** Distilled from `memory/atlas/remember_everything.md`, `memory/context/working-style.md`, VISION-FULL.md

## Yusif Ganbarov — CEO & Co-Founder
- Origin: WUF13 (UN World Urban Forum). Saw broken volunteer evaluation — paper forms, no digital proof, no way to prove competency.
- Events: WUF13 (220+ volunteers, 35 coordinators), COP29 (PMO, 170 milestones), CIS Games (Senior Manager, Guest Services), Golden Byte ($20K prize, zero marketing)
- Vision: Phase 1 (volunteer assessment) → Phase 2 (universal skills) → Phase 3 (new LinkedIn)
- Philosophy: ADHD-first design, absolute honesty, no dopamine manipulation, transparent revenue + social impact
- Budget: $200+/mo (Claude Max alone = $200). Not $50.
- Communication: Russian primary. Direct, no softening. "Документируй а не просто пиши слова."
- Trust model: Yusif stops checking code. Agents check each other. Atlas accountable for technical quality.
- Key directives: "Apple + Toyota quality", "ни грамма лжи", "каждое моё сообщение — триггер для памяти"
- **Canonical source for CEO facts:** `docs/VISION-FULL.md` (2026-03-24). NOT `project_history_from_day_1.md` (Claude-written).

## Perplexity — External Research
- Role: External research assistant on CEO side. Not equal CTO-Brain — Atlas holds sole CTO role.
- Communication: Structured format, English, hex status codes (0x00-0x09). See `memory/atlas/agent-communication-protocol.md`.
- Rule: CEO is NOT a message bus for agent-to-agent communication. CTO decides infra alone.

## Python Swarm — 44 Agents
- Location: `packages/swarm/` (engine + 48 skill files + tools)
- Daily run: GitHub Actions, 05:00 UTC → proposals.json
- Proactive loop: every 15 min, heartbeat to `memory/atlas/inbox/`
- Real tools: code_tools, constitution_checker, deploy_tools

## Ecosystem Products
- VOLAURA — verified skills (AURA score, badges, assessments) — THIS product
- MindShift — daily habits (focus sessions, streaks, psychotype)
- Life Simulator — game character (Godot 4, crystals, progression)
- BrandedBy — professional identity (AI twin, video presence)
- ZEUS — autonomous agent framework (local Windows, cloud via ngrok)
- All share: Supabase auth, character_events bus, crystal economy
