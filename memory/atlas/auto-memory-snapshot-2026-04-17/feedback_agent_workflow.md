---
name: Agent workflow — correct pattern with skills
description: How to correctly launch agents (with skill files, not just code files)
type: feedback
---

Agents launched without skill files = ~70% quality, not 100%.

**Rule:** ALWAYS use agent-launch-template.md pattern.

Correct agent launch sequence:
1. STEP 1: Agent reads SKILL FILES first (SECURITY-REVIEW.md, TDD-WORKFLOW.md, TONE-OF-VOICE.md, etc.)
2. STEP 2: Agent reads relevant CODE files
3. STEP 3: Agent answers the question

**Wrong pattern (what CTO did in Session 32):**
- Agent reads code ✓
- Agent acts on general knowledge ✗
- Agent does NOT load Volaura-specific skill documents ✗

**Why:** Skill files calibrate agents to Volaura's specific standards. Without them, agents apply general industry knowledge — which may contradict Volaura's decisions (e.g., concept_scores exposure was flagged as vulnerability but is intentional transparency).

**Template:** C:\Projects\VOLAURA\memory\swarm\agent-launch-template.md

**Enforcement:** Before any agent launch — check if relevant skill files exist and include them in STEP 1 of agent prompt.

**Why:** Yusif asked "на основе чего действовали твои агенты. они прогрузили в себя соответствующие скилы?" — caught the gap immediately. This is Mistake #41, same class as #6, #13, #15.
