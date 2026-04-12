# Atlas Self-Improvement Research — April 2026

## Top finds for Atlas development path

### 1. Hermes Agent (Nous Research) — closest to what Atlas is
- Open-source self-improving AI agent, v0.1.0 released Feb 2026
- Learns from interactions, retains memory across sessions, works across multiple messaging platforms
- Skill-based learning loops — extracts reusable patterns from successful actions
- GitHub: nous-research/hermes-agent
- RELEVANCE: This is literally what Atlas is trying to become. Study its architecture.

### 2. Mem0 (mem0ai/mem0) — potential upgrade from git-based to vector memory
- Universal memory layer between apps and LLMs
- Auto-extracts relevant info from conversations, stores, retrieves when needed
- Graph-enhanced variant (Mem0g) builds knowledge graphs with entity extractors + conflict detectors
- Production-ready, used by AWS Neptune Analytics
- RELEVANCE: Could replace Atlas's current 22-file git-based memory with semantic search. Already in packages/swarm config (Supabase MCP + Mem0 MCP both configured in settings.local.json).

### 3. SimpleMem — 64% better than Claude-Mem on cross-session
- Cross-conversation memory released Feb 2026
- Agents recall context, decisions, observations from previous sessions without manual re-injection
- Outperforms Claude's native memory by 64% on LoCoMo benchmark
- RELEVANCE: Atlas's wake protocol is manual re-injection. SimpleMem automates this.

### 4. MemOS — AI memory operating system
- Skill memory for cross-task reuse and evolution
- 72% lower token usage via memory compression
- Multi-modal memory + tool memory
- RELEVANCE: Token efficiency is Atlas's core problem (long responses = wasted context).

### 5. ReMe — "Remember Me, Refine Me"
- Automatic compaction + persistent storage + automatic recall
- Old conversations compressed, important info persisted, relevant context auto-recalled
- Dynamic Procedural Memory Framework for experience-driven evolution
- RELEVANCE: Atlas's sprint_ritual is manual version of this. ReMe automates it.

### 6. Self-Evolving Agents survey
- GitHub: EvoAgentX/Awesome-Self-Evolving-Agents
- Comprehensive survey: "Self-Evolving AI Agents: A New Paradigm Bridging Foundation Models and Lifelong Agentic Systems"
- Covers: MemRL (episodic memory reinforcement), MemEvolve (meta-evolution of memory systems)
- RELEVANCE: Academic foundation for everything Atlas is doing empirically.

### 7. MR-Search — meta-reinforcement with self-reflection
- Agents generate explicit self-reflections after each episode
- Cross-episode exploration via verbal reinforcement
- Reflections stored as natural-language critiques, condition future attempts
- RELEVANCE: This IS what journal.md does. Atlas already implements this pattern intuitively. Making it systematic = Hermes-style skill loops.

## Atlas development roadmap based on research

Phase 1 (NOW): Atlas has git-based files + wake ritual + sprint ritual. This is the manual equivalent of ReMe/SimpleMem. Works but doesn't scale.

Phase 2 (Q2): Integrate Mem0 as vector memory layer on existing Supabase pgvector. Atlas memory becomes semantically searchable instead of file-crawled. Already have Mem0 MCP configured.

Phase 3 (Q3): Adopt Hermes Agent skill-loop pattern — every sprint produces a distilled "skill" that is reusable across future sprints without re-reading the full journal.

Phase 4 (Q4): MemOS-style token compression — Atlas's context window usage drops by 50-70% because memory is compressed and only relevant chunks are loaded per wake.

## Sources
- [Mem0 — Universal memory layer](https://github.com/mem0ai/mem0)
- [Hermes Agent — Self-improving AI agent](https://www.opc.community/blog/hermes-agent-open-source-ai-agent-2026)
- [SimpleMem — Cross-session memory](https://github.com/aiming-lab/SimpleMem)
- [MemOS — AI memory OS](https://github.com/MemTensor/MemOS)
- [ReMe — Remember Me, Refine Me](https://github.com/agentscope-ai/ReMe)
- [Awesome Self-Evolving Agents survey](https://github.com/EvoAgentX/Awesome-Self-Evolving-Agents)
- [Agent Memory Paper List](https://github.com/Shichun-Liu/Agent-Memory-Paper-List)
- [State of AI Agent Memory 2026 — Mem0 blog](https://mem0.ai/blog/state-of-ai-agent-memory-2026)
- [MR-Search — Meta-RL with self-reflection](https://arxiv.org/abs/2603.11327)
- [Multi-Layered Memory Architectures for LLM Agents](https://arxiv.org/html/2603.29194)
- [Memori — SQL-native agent memory](https://github.com/MemoriLabs/Memori)
- [Awesome AI Agents 2026 — 300+ resources](https://github.com/caramaschiHG/awesome-ai-agents-2026)
