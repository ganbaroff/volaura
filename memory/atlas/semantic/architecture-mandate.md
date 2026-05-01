# Architecture Mandate — Production-Grade Autonomy

Source: CEO directive 2026-05-01. This overrides all previous architectural decisions.
Core principle: RELIABILITY over NOVELTY. Stop adding features. Fix what exists.

## 3-Layer Model (do not mix)
1. MEMORY: episodic + semantic + procedural. Read-only for brain/swarm.
2. BRAIN: reads compact state → creates tasks. NOT a raw text dump.
3. SWARM: receives narrow scoped context → returns structured evidence.

## Brain Input (compact, typed)
ONLY these sources:
- semantic/product-truth.md
- semantic/swarm-state.md
- PRE-LAUNCH-BLOCKERS-STATUS.md (current blockers)
- Last 3 episodes
- Health metrics (prod curl + git SHA)
- Unresolved findings
Target: structured state object, NOT giant text dump.

## Evidence Requirement (mandatory for all findings)
Every finding MUST include:
- claim
- evidence_type (file | runtime | api | test | diff)
- evidence_path_or_command
- confidence (0-1)
- risk_level (low | medium | high | critical)
- recommended_action
No evidence = auto-discard + weight penalty.

## Anti-Repeat Registry
File: memory/atlas/semantic/false-positives.md
Disproven claims logged here. If agent repeats without new evidence → weight penalty.

## Autonomy Levels
- auto_execute: docs cleanup, lint, test fixes, duplicate consolidation, internal tooling
- auto_execute_and_digest: safe refactors, memory updates, CI fixes
- requires_ceo_review: pricing, UX changes, privacy, legal, Constitution changes

## HANDS Proof Required
Not proven until full path verified:
brain → task → swarm → HANDS edit → tests pass → commit → episode written

## VM Self-Healing
Health checks: last brain cycle, last daemon task, last episode, FP rate, pending escalations.
Threshold violated → alert + incident episode.

## CEO Digest (daily)
Plain English. What changed, what verified, what failed, what needs CEO, trust score, top blocker.

## Feature Freeze
No new agents, tools, or abstractions until:
- FP rate < 15%
- HANDS proven E2E
- VM restart reliable
- Escalation enforced
- Digest working
