---
name: v0Laura — the REAL product (not just VOLAURA assessment)
description: v0Laura = 1 platform + skill library + AI characters. Assessment is ONE skill, not THE product. CEO correction Session 86. READ EVERY SESSION.
type: project
---

## What v0Laura IS
One platform where AI skills (agents) create the entire user experience.
`POST /api/skills/{name}` — this is the engine. Everything else is a skill.

## Architecture (Session 51 decision)
- Life Simulator = `feed-curator` skill (NOT a game)
- MindShift = `behavior-pattern-analyzer` skill (NOT a separate app)
- BrandedBy = `ai-twin-responder` skill (NOT a separate platform)
- ZEUS = `assessment-generator` skill (NOT a separate engine)
- Assessment = one skill among many
- Coaching = another skill
- Career advice = another skill

## Agent = Skill = Character = Interface
The 44 agents are NOT backend workers hidden from users. They ARE the product:
- Each agent has a personality, visual appearance in the game world
- Users interact with them directly ("pro mode")
- Agents actually monitor and control the app
- If Security Agent finds a bug → character says "I found an issue, going to fix it"
- If BNE notices cognitive load too high → character simplifies the screen
- They sit in a virtual office, work, ask not to be disturbed

## What CTO kept doing wrong
Building an assessment form when v0Laura is a skill-powered platform.
Treating agents as internal tools when they're the user interface.
Reading the vision, writing it in code (`skills.py` line 6), and still building wrong.

**Why:** Knew the truth → agreed → continued doing the old thing. Not ignorance. Inertia.

## How to apply
Before ANY feature decision: "Is this a new skill in the v0Laura engine, or am I building a standalone form?"
The answer should almost always be: it's a skill. Wire it through `POST /api/skills/{name}`.

## Source
- `apps/api/app/routers/skills.py` line 6: "This is the v0Laura engine"
- `packages/swarm/autonomous_run.py` line 219-224: architecture shift
- `docs/VISION-FULL.md`: Phase 1→2→3 evolution
- CEO Session 86: "v0Laura ты хоть знаешь что это такое?"
