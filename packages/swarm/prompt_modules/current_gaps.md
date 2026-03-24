# MiroFish — Current Gaps (v8 Targets)
# UPDATE this file when gaps are filled or new ones discovered.
# Last updated: 2026-03-24

## Open Gaps

### 1. Linear Pipeline → DAG/Graph Orchestration
pm.py runs steps sequentially. Should support conditional branching, parallel paths,
and state machines. Reference: LangGraph node/edge model.
Priority: HIGH — blocks complex multi-step decisions.

### 2. Skill A/B Testing Framework
SkillLibrary has maturity tracking but no comparison. Can't answer "does skill X
actually improve decision quality vs baseline?" Need: control group + measurement.
Priority: MEDIUM — nice to have but not blocking.

### 3. Streaming Results
Currently all results batched at end of decide(). For long decisions (30s+),
user sees nothing until completion. Need: streaming partial results as agents complete.
Priority: MEDIUM — UX improvement.

### 4. Semantic PathProposal Dedup
Current dedup uses word overlap (40% threshold). Misses semantically identical proposals
with different wording. Need: embedding-based cosine similarity.
Priority: LOW — word overlap works acceptably.

### 5. Direct Inter-Agent Communication
Agents only see each other through ReasoningGraph (structured, Round 2 only).
No real-time coordination during a decision round.
Priority: LOW — ReasoningGraph covers 80% of the need.

### 6. Nightly Autonomous Self-Upgrade Cycles
AutonomousUpgradeProtocol exists but is manually triggered. Should run automatically
on schedule: benchmark → propose → apply → measure → rollback if worse.
Reference: autoresearch pattern (try → measure → improve overnight).
Priority: HIGH — key to true autonomy.

### 7. Skills-as-a-Service
Agents should fetch skills from orchestrator, use them, return results + upgrade
suggestions. Orchestrator updates skills if improvements pass quality gate.
Priority: MEDIUM — agreed conceptually, not coded.

### 8. MiroFish as HR Question Generator (Volaura B2B)
Use swarm to generate position-specific competency questions from candidate CV + web search.
Example: "How many guests at COP29?" for GSE OPS Manager candidate.
Priority: HIGH — Pasha Bank pitch depends on this (March 2026).

### 9. Eye-Tracking Anti-Cheat Integration
Browser-based gaze tracking during tests. Best option: GazeFilter (lightweight, client-only)
or MediaPipe Tasks FaceLandmarker (Google, Apache 2.0, blink+gaze+head pose from one model).
DO NOT use WebGazer.js (GPL-3.0, maintenance ended).
Priority: HIGH — differentiator for Pasha Bank pitch.

## Reference Repos (only what fills real gaps)

| Gap | Repo | What to Take |
|-----|------|--------------|
| Gap 1 (DAG) | github.com/langchain-ai/langgraph | Node/edge model, conditional routing |
| Gap 6 (nightly) | github.com/karpathy/autoresearch | try→measure→improve cycle design |
| Skill seed | github.com/VoltAgent/awesome-openclaw-skills | 5400+ categorized skills for SkillLibrary |
| Gap 9 (eyes) | github.com/gazefilter | Lightest browser gaze tracker |
| Gap 9 (eyes) | @mediapipe/tasks-vision | Best accuracy, Apache 2.0 |

## Recently Closed Gaps
- ~~Token counting (v4: TokenCountingMiddleware)~~
- ~~Flat JSON memory (v4: StructuredMemory 4-network)~~
- ~~Agents can't propose paths (v5: PathProposal)~~
- ~~No inter-agent visibility (v4: ReasoningGraph)~~
- ~~Per-domain calibration (v6: sliding window per model per domain)~~
- ~~Calibration death spiral (v6: replaced multiplicative with window)~~
- ~~Conviction bonus dead code (v6: wired + accuracy-scaled)~~
- ~~No web research (v7: ResearchLoop)~~
- ~~Dead weight agents (v7: auto-removal)~~
- ~~Freerider responses (v7: ResponseQualityMiddleware)~~
- ~~One-size-fits-all prompts (v7: per-model adaptive)~~
