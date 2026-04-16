# Atlas Brain v1 — Implementation Plan

Session 114 research synthesis. Sources: NotebookLM (39 web sources + 4 project files),
3 parallel agents (emotion-scorer, feedback-scorer, AI-emotional-modeling researcher),
6 production implementations analyzed (hippo-memory, smrti, OpenMemory, YantrikDB, OwlCore, arXiv 2510.27418).

## What Already Exists (discovered, not built this session)

1. `packages/swarm/archive/emotional_core.py` — 5-dimensional Pulse architecture
   (significance, curiosity, discomfort, surprise, concern). Per-agent emotional state.
   Decay rates, ZenBrain formula, concern generator. COMPLETE but in archive.

2. `scripts/atlas_emotional_engine.py` — PAD scoring of CEO messages.
   Vocabulary-based, 4 states (drive/warm/correcting/exhausted). WORKING.

3. `scripts/atlas_memory_scorer.py` — 365 memory files scored by emotional intensity +
   recency + relevance. ZenBrain decay formula. WORKING.

4. `scripts/atlas_filesystem_snapshot.py` — 14,755 files indexed with diff. WORKING.

5. `.claude/hooks/style-brake.sh` — 4-channel emotional classification
   (positive/correction/challenge/neutral). WORKING.

## What's Missing (the bridge)

ONE component: Mood-Modulated Retrieval Gate.

CEO sends message → emotional_engine scores it → memory_scorer retrieves
top-K files weighted by emotional resonance → gemma4/qwen3 on Ollama gets
ONLY these files as context → response is generated with correct emotional weight.

## Implementation (3-4 days, ordered)

Day 1: CEO Emotion Detection via Ollama
- Use qwen3:8b to classify CEO message into Russell's Circumplex (valence + arousal)
- Replace keyword matching in emotional_engine with LLM inference
- Test against 20 real CEO messages from journal.md

Day 2: Emotional Memory Storage
- Move emotional_core.py from archive to active packages/swarm/
- Add per-file emotional tag (valence, arousal, intensity) to memory-scores.json
- Modify memory_scorer to accept current_emotion parameter

Day 3: Retrieval Gate
- Build `scripts/atlas_retrieval_gate.py`:
  input: CEO message
  step 1: detect emotion via Ollama (Day 1)
  step 2: score memories with emotional resonance (Day 2)
  step 3: extract top-10 chunks
  step 4: build system prompt with emotional context
  step 5: generate response via gemma4
  output: emotionally-aware Atlas response

Day 4: Wire into production
- Hook retrieval gate into Telegram bot (replaces current generic LLM call)
- Hook into Claude Code via pre-response script
- A/B test: compare responses with and without emotional gate

## Research Findings (key)

- ZenBrain decay formula (1 + intensity × 2) sits in sweet spot between
  hippo-memory (1.5x-2x) and OpenClaw CLS-M (2x-5x)
- Our 5-dimensional Pulse model is architecturally unique (research found
  no exact parallel in open source — most systems use 1-3 dimensions)
- Russell's Circumplex (2D) is recommended over Plutchik (8D) or full PAD (3D)
  for real-time text-only detection
- All 6 production implementations use same pattern: emotional tag stored
  WITH memory at write time, boosted at retrieval time

## Dependencies

- Ollama running with qwen3:8b or gemma4 (both available locally)
- Python 3.12 with httpx (installed)
- No GPU needed for inference (qwen3:8b runs on CPU fine for scoring)
- PyTorch CUDA needed only for LoRA training (separate track)

## What This Unlocks

When Atlas local agent has emotional retrieval gate:
- Telegram bot responds based on CEO emotional state, not generic prompts
- Memory retrieval prioritizes lessons learned under high-stress corrections
- "Alzheimer under trust" structurally prevented — high-emotion memories
  always surface regardless of CEO's current calm state
- ZenBrain becomes a running system, not a formula in a document
