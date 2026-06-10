# ADR-017 — CV-Grounded Item Generation (Two-Layer Assessment Engine)

**Status:** Proposed (CEO directive 2026-06-10: "движок, который принимает резюме и создаёт тесты на основе этого резюме, работает постоянно, через рой")
**Date:** 2026-06-10
**Deciders:** CEO (vision + ratification), Atlas (architecture), Codex (review gate on LLM-touching code)
**Prereq reading:** `memory/atlas/ASSESSMENT-CONTENT-AUDIT-2026-06-10.md` (RC-3: static tiny bank, zero personalization)

## Context

The live item bank is static (117 items, 14–15/competency), event-domain, uncalibrated, and impersonal. The CEO's product vision is a continuously running engine that ingests a candidate's CV and generates assessment content from it. The hard constraint: **AURA must stay comparable between candidates**, and IRT/CAT comparability only holds on a shared calibrated item bank — per-candidate LLM items cannot feed theta directly without destroying cross-candidate meaning.

Industry precedent (researched 2026-06-10, not from memory): the Duolingo English Test runs AI item generation operationally with humans in the loop across construct definition, item review, and psychometric calibration ([DET assessment ecosystem](https://duolingo-testcenter.s3.amazonaws.com/media/resources/A+Theoretical+Assessment+Ecosystem+for+a+Digital-First+Assessment%E2%80%94The+Duolingo+English+Test.pdf), [Responsible AI case study](https://arxiv.org/pdf/2409.07476), [transformer AIG for reading items](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9354894/)). 2025 research converges on multi-agent AIG with embedded review roles ([LLM multi-agent AIG framework, J. Business & Psychology](https://link.springer.com/article/10.1007/s10869-025-10067-y)) and human-in-the-loop difficulty/bias control ([HITL exam generation](https://www.mdpi.com/2227-7102/15/8/1029)); comparative studies show LLM-only review is too permissive vs human reviewers ([CEUR study](https://ceur-ws.org/Vol-4006/paper8short.pdf)).

## Decision

### 1. Two layers, one engine
- **Layer 1 — Calibrated CAT core (exists, unchanged):** shared standardized bank → IRT 3PL/EAP → comparable AURA. The ONLY input to theta.
- **Layer 2 — Experience Interview (new):** CV-grounded situational items generated per candidate by the swarm. Probes the candidate's OWN claims (scale, tools, stakeholders, sequencing — familiar to someone who did it, hard for someone who faked it). Output = **verified-experience signals** on the profile (claim → probed → consistent/inconsistent), shown alongside AURA. **Never feeds theta.**

### 2. Continuous AIG pipeline (same machinery, two outputs)
The generation swarm runs as a persistent worker and produces BOTH:
- per-candidate Experience Interview sets (on CV upload), and
- **standardized bank candidates** (de-personalized variants) into the existing `is_ai_generated=true, needs_review=true` queue → human approval (CEO/expert) → servable → empirical calibration from the already-collected `times_shown/times_correct`.
This fixes RC-3 bank growth and the brand re-anchor (professional-workplace scenarios) with the same engine.

### 3. Multi-agent roles (one-shot generation is NOT enough — proven)
PoC (2026-06-10, `scripts/poc_cv_item_generation.py`, Groq `llama-3.3-70b-versatile`, free tier, 3,689 tokens ≈ $0, ~5 s): 8/8 items grounded in real CV claims across all 8 competencies — pipe works. But one-shot quality fails item-writing standards, e.g. the ClickUp item's correct option literally quotes the CV ("Overhaul the Gantt charts and standardize milestone tracking") — answerable by CV-echo, not judgment; several distractors are throwaways ("Do nothing and hope…"). Production therefore uses the researched multi-agent loop: **generator → content reviewer (anti-echo, distractor plausibility) → linguistic reviewer (per language) → bias/fairness reviewer → reviser**, then the human `needs_review` gate for anything entering the shared bank. Experience Interview items get the agent loop + spot-check sampling (not 100% human review — they don't affect AURA).

### 4. Infrastructure home
`apps/api` service + background worker on the proven `reeval_worker` enqueue/poll pattern (`app/services/reeval_worker.py`): new `cv_intake` table → worker generates → writes items with provenance (`source='cv_aig'`, `source_cv_hash`, `generator_model`, `review_state`). NOT ZEUS (Node WS event gateway — wrong layer); NOT the docker SwarmEngine (unavailable on Railway prod — `swarm_service.py:61-75` already documents that limitation).
Providers: free-first per ADR-013 precedence — Groq free tier (verified working today), freellmapi gateway (`http://34.60.182.57:8799`, OpenAI-compatible, LIVE — needs key provisioning), Gemini (quota). NVIDIA key currently dead. **No Anthropic in swarm (Article 0). All LLM-routing touchpoints go through Codex review (Class 3).**

### 5. Privacy
CV text is processed transiently for generation; stored items carry minimal claim references, not the CV. CV artifacts are deletable via the existing gdpr-delete path. CV content is sent only to providers already processing our assessment data.

## Consequences
+ CEO's vision shipped without breaking score comparability; honest "verify the CV" story for the deck (stronger than generic tests).
+ Bank grows continuously toward 30+/competency professional-workplace items; calibration becomes possible.
− More moving parts (worker, queue, review UI); generation latency on CV upload (~1–2 min with review passes — acceptable async UX).
− Free-tier rate limits cap throughput; fine pre-beta, revisit at scale.

## Implementation plan (each its own PR)
1. **PR-1:** `cv_intake` + item-provenance migration; upload endpoint (auth'd, size-capped).
2. **PR-2:** generation service with multi-agent passes via existing provider chain (**Codex review**).
3. **PR-3:** worker + Experience Interview session mode (separate from CAT sessions; LLM-graded via existing BARS/swarm path).
4. **PR-4:** profile "verified experience" signals UI + reviewer queue UI for bank candidates.
Order after FIX-1..FIX-3 of the content audit (broken texts + RU + D-4) — those gate ANY outreach.

## Evidence trail
PoC run + full 8-item output reviewed by eyes 2026-06-10 (2 items embedded below). Sample (grounded, good): *"You are the Venue Coordinator for the CIS Games 2025… one of the 30 venues is still under construction a week out — what do you do?"* Sample (echo-failure, why reviewer pass exists): the ClickUp item quoting its own CV claim as the correct option.
