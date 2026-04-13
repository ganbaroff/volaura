# ADR-009: CrewAI Adoption for Swarm Orchestration

**Date:** 2026-04-03
**Status:** APPROVED (pending implementation)
**Decision makers:** CTO + Gemini + Llama 405B + NotebookLM deep research
**Stakeholders reviewed:** Growth Hacker (against), Lean Startup (against), Y Combinator (against), NotebookLM (for)
**Related:** [[ADR-007-ai-gateway-model-router]] | [[ADR-008-zeus-governance-layer]] | [[../CONSTITUTION_AI_SWARM]] | [[../research/swarm-innovation-research]]

---

## Context

CTO (Claude) has committed CLASS 3 mistake (solo execution) 17 times in 12 days. Current swarm system: 40 markdown skill files, no enforcement of delegation. Rules exist but rely on willpower. Willpower fails 34.8% of the time.

## Decision

**ADOPT CrewAI** for Sprint Gate DSP and critical multi-agent workflows.

NOT full migration. Phased:
- Phase 1: CrewAI for Sprint Gate DSP (7 agents) — structural enforcement of delegation
- Phase 2: If Phase 1 reduces CLASS 3 to <5% → expand to all L4/L5 tasks
- Phase 3: If Phase 2 succeeds → full migration of swarm to CrewAI

## Why YES (NotebookLM analysis, cited)

1. **Separation of management and execution:** Flows manage, Crews execute. CTO cannot do both.
2. **Hardcoded task-to-agent delegation:** Tasks assigned to specific agents by role. Framework prevents one agent from doing everything.
3. **Hierarchical manager constraints:** CTO in hierarchical mode cannot execute ground-level tasks — only delegate, review, and request rework.

## Why NOT (initial critique)

- Gemini: "premature optimization, focus on revenue first"
- Lean Startup: "adds overhead for solo founder"
- Y Combinator: "building a Faberge egg while house is on fire"

## Why we override the critique

The critique assumed CrewAI is a feature. It's not. It's a **structural fix for a CLASS 3 defect that has recurred 17 times.** This is not optimization — this is Poka-yoke. Toyota would install a physical barrier to prevent a defect that happens 17 times, not write another rule.

## Implementation plan

1. `pip install crewai` in apps/api requirements
2. Create `packages/swarm/crewai_dsp.py` — Sprint Gate DSP as CrewAI Flow
3. 7 agents as CrewAI Agents with roles from existing skill files
4. CTO = Hierarchical Manager (cannot execute, only delegate)
5. Test with one real sprint before expanding

## Risks

- Learning curve: ~4 hours to understand CrewAI Flows
- Dependency: adds crewai to production deps
- Fallback: if CrewAI fails, markdown skills still work

## Success metric

CLASS 3 instances in next 50 hours: target <3 (from 17 in first 210 commits).
