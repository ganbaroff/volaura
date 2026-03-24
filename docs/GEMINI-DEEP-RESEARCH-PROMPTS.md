# Gemini Deep Research — 3 Prompts (ready to paste)

**Created:** 2026-03-25
**Purpose:** Each prompt is copy-paste ready for Gemini Deep Research. Output format specified so results are directly actionable.

---

## Prompt 1: AI Agent Memory Architecture (for MiroFish)

```
Research how human memory consolidation — specifically the hippocampus-to-neocortex transfer during sleep — can inform the design of memory systems for AI agent swarms.

CONTEXT:
I'm building MiroFish, a multi-model AI swarm engine where 14+ LLM agents (Gemini, DeepSeek, Llama, Qwen) work in parallel on decisions. Each agent runs independently, produces a result, then a synthesis agent combines everything.

CURRENT PROBLEM:
- Agents have no persistent memory between runs. Every swarm invocation starts from zero.
- We store results as JSON files, but there's no consolidation — no "what did the swarm learn?"
- The CTO (Claude) has a memory system with files, but agents inside the swarm don't.
- When we run the same type of decision twice, agents repeat the same mistakes.

WHAT I NEED FROM THIS RESEARCH:

1. NEUROSCIENCE MAPPING:
   - How does hippocampal replay work during sleep? (short-term → long-term consolidation)
   - What is "memory trace reactivation" and can it apply to AI agents reviewing past decisions?
   - How does the brain decide what to consolidate vs. forget? (relevance filtering)
   - What is "systems consolidation theory" and how would an AI version look?

2. EXISTING AI RESEARCH:
   - What papers exist on persistent memory for multi-agent systems? (2023-2026)
   - How do frameworks like AutoGen, CrewAI, LangGraph handle agent memory?
   - What is "experience replay" in reinforcement learning and can it apply to LLM agents?
   - Are there any implementations of "sleep cycles" for AI agent memory consolidation?

3. PRACTICAL ARCHITECTURE:
   - Design a memory consolidation pipeline for a 14-agent swarm:
     * After each run: what gets stored? (raw results, patterns, errors, innovations)
     * Consolidation cycle: when and how does "important" get separated from "noise"?
     * Retrieval: how does an agent access relevant past experience at runtime?
   - What storage format? (vector DB, structured JSON, graph DB, hybrid?)
   - What's the minimum viable version that adds real value with <100 lines of code?

4. COMPETITIVE LANDSCAPE:
   - Which AI labs are working on persistent agent memory? (Google DeepMind, Anthropic, OpenAI, Meta FAIR)
   - What's the state of the art as of 2026?
   - Where is the research gap that an independent team could publish in?

OUTPUT FORMAT:
- Executive summary (1 paragraph)
- Neuroscience → AI mapping table (brain structure → swarm equivalent)
- Architecture diagram description (text-based, I'll draw it)
- Implementation priority list (what to build first, second, third)
- 10 key papers with 1-sentence summaries
- 3 concrete code-level recommendations for MiroFish
```

---

## Prompt 2: AI Agent Delegation Patterns (for TeamLead system)

```
Research best practices for task delegation and routing in multi-model AI orchestration systems, specifically when different LLM models have different strengths.

CONTEXT:
I run a swarm with these models:
- Gemini 2.0 Flash (fast, good at content, weak at security)
- Gemini 2.5 Pro (slow, deep reasoning, best at architecture)
- DeepSeek Chat (cheap, great at finding specific risks, weak at creative tasks)
- Llama 3.3 70B via Groq (free, versatile, medium quality)
- Llama 3.1 8B via Groq (free, fast, low quality — good for volume)

Currently: round-robin allocation. All agents get the same prompt regardless of their strengths.
I've built a "TeamLead" system that routes tasks by domain (content → Gemini, security → DeepSeek, architecture → Gemini Pro). But it's based on manual observation, not systematic benchmarking.

WHAT I NEED FROM THIS RESEARCH:

1. DELEGATION FRAMEWORKS:
   - How do human organizations route tasks to specialists? (Taylorism, matrix management, Spotify model)
   - How does this translate to AI agent teams?
   - What's the difference between "routing" (pick the right agent) and "orchestration" (coordinate multiple agents)?
   - Mixture of Experts (MoE) at the system level — can we apply the MoE concept to a swarm of different LLMs?

2. MODEL CAPABILITY MAPPING:
   - What systematic methods exist to benchmark model strengths per domain?
   - How do companies like Anthropic, Google, and Meta evaluate model capabilities?
   - Is there a standard "capability card" format for LLMs?
   - How to detect model drift (a model that was good at X becomes worse after an update)?

3. ROUTING ALGORITHMS:
   - What are proven task-routing algorithms for heterogeneous compute?
   - Multi-armed bandit approaches for model selection — relevant?
   - Reinforcement learning for dynamic routing — overkill or practical?
   - What's the simplest routing that outperforms random allocation? (research evidence)

4. REAL IMPLEMENTATIONS:
   - How does Anthropic's internal routing work (Claude model family: Haiku vs Sonnet vs Opus)?
   - How does Google route between Gemini models?
   - Any open-source multi-model orchestrators that do smart routing?
   - What does the "Model Router" concept look like in production?

5. FAILURE MODES:
   - What happens when routing is wrong? How to detect and self-correct?
   - "Dead weight" problem: model seems to work but adds no value. Detection methods?
   - Overfitting to a specific model: always picking the same one. How to maintain diversity?

OUTPUT FORMAT:
- Executive summary (1 paragraph)
- Human delegation model → AI delegation mapping table
- Decision tree: "Given task X, route to model Y because Z"
- 3 routing algorithms ranked by complexity vs. value
- Implementation checklist for our TeamLead system (what to add next)
- 10 key papers/resources
- 5 anti-patterns to avoid
```

---

## Prompt 3: Agile for AI-Human Teams (for our sprint process)

```
Research how Agile methodologies need to be adapted when one "team member" is an AI agent with context window limitations, and the team size is 2 (human CEO + AI CTO).

CONTEXT:
Our team: Yusif (human CEO, non-technical, vision + orchestration) and Claude (AI CTO, handles all code + architecture + deployment). We run 1-week sprints. Problem: standard Agile was designed for 5-9 humans. Our reality:

- CTO loses all context every session (context window compaction)
- Sprint velocity is 10x a human team but consistency is 0.3x (some sessions = perfect, some = repeated mistakes)
- "Standup" doesn't make sense when CTO doesn't remember yesterday
- Story points calibrated for humans — our velocity breaks the scale
- Retrospectives work great but insights get lost between sessions
- CEO ends up micromanaging because CTO's memory is unreliable

WHAT I NEED FROM THIS RESEARCH:

1. EXISTING FRAMEWORKS:
   - Are there any documented Agile adaptations for AI-human teams? (2024-2026)
   - How do AI-first companies (Cognition/Devin, Cursor, Replit) structure their dev process?
   - "AI pair programming" literature — what processes emerged?
   - Is there a "Scrum for AI agents" or equivalent?

2. MEMORY AND CONTINUITY:
   - How to maintain sprint continuity when the "developer" forgets everything?
   - State management patterns: what must be persisted between sessions?
   - "Handoff documents" — best format for AI-to-AI handoff (next session of same agent)?
   - How much overhead is acceptable for context recovery? (currently 5-10% of session)

3. VELOCITY AND ESTIMATION:
   - How to measure velocity for an AI agent? (tokens? deliverables? story points still work?)
   - How to set realistic sprint goals when capability varies session-to-session?
   - "AI capacity planning" — predicting what Claude can do in a 4-hour session
   - When to use Haiku (fast, cheaper) vs Sonnet (better) vs Opus (best) for sprint tasks?

4. RETROSPECTIVE FORMATS:
   - What retrospective formats work for AI teams? (standard retro assumes shared memory)
   - How to make retrospective insights STICK across sessions? (our retros are high quality but forgotten)
   - Automated retrospective: can AI generate its own performance review?
   - "Failure pattern database" — how to build one that actually prevents repeat errors?

5. CEO-CTO DYNAMICS:
   - When human CEO works with AI CTO, what's the optimal communication pattern?
   - How to prevent "CEO as tech support" anti-pattern?
   - Delegation frameworks: what should CEO NEVER have to think about?
   - Trust calibration: when should CEO verify AI's work vs. trust blindly?

OUTPUT FORMAT:
- Executive summary (1 paragraph)
- "Modified Agile Manifesto for AI-Human Teams" (4 principles, adapted)
- Sprint template designed for 2-person AI-human team
- Retrospective format that survives context loss
- Velocity measurement framework
- 10 key resources (papers, blog posts, case studies)
- 5 immediate process improvements we can implement this week
```

---

## How to Use

1. Go to gemini.google.com → Deep Research mode
2. Paste one prompt at a time
3. Let Gemini research (takes 5-15 minutes per prompt)
4. Save output → create NotebookLM notebook per topic
5. CTO reads results and implements recommendations

**Priority order:** Prompt 3 (Agile) first — fixes our process NOW. Then Prompt 1 (Memory) — core MiroFish innovation. Then Prompt 2 (Delegation) — enhances existing TeamLead system.
