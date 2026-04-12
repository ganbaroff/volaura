# ZEUS Memory Architecture Research — 2026-04-14

**Researcher:** Atlas (via multi-source agent — WebSearch, GitHub Issues, HN, ArXiv, changelogs)
**Commissioned by:** CEO carte blanche for deep research
**Budget constraint:** $100/mo total LLM costs
**Existing stack:** Supabase pgvector (768-dim), Python 3.11, FastAPI, Ollama local

---

## Executive Summary

No single framework covers all 7 ZenBrain layers. The 7-layer model is original research beyond existing tools. Build custom on pgvector, steal ideas from Graphiti (temporal model) and HippoRAG (consolidation), ignore Mem0 (97.8% junk in production audit).

**Total infrastructure cost of recommended path: $0 incremental.**

---

## Framework Comparison

| Framework | Stars | Open Bugs | ZenBrain Layers | Verdict |
|-----------|-------|-----------|-----------------|---------|
| Mem0 | 52,770 | 218 | 2/7 | **REJECT** — 97.8% junk in prod audit (Issue #4573), graph paywalled $249/mo |
| Graphiti/Zep | 24,808 | 80 | 3/7 | **STEAL IDEAS** — bi-temporal model is real, Neo4j too heavy |
| Letta (MemGPT) | 22,019 | 4 | 4/7 | **REJECT** — every memory op = LLM call, budget-killer at 44 agents |
| Cognee | 15,153 | 58 | 2-3/7 | **MONITOR** — pgvector native, but 200 lines of custom code does same |
| Hindsight | 9,014 | 74 | 2/7 | **MONITOR** — best benchmarks + Ollama, but self-reported by vendor |
| MCP Memory Service | 1,648 | 13 | 3/7 | **USEFUL** — MCP interface pattern worth following |

### Critical Evidence

**Mem0 production audit (Issue #4573):** 10,134 entries over 32 days. 97.8% junk. 52.7% were boot file content re-extracted every session. Feedback loops amplified hallucinations — one false fact generated 808 copies. 5.2% were hallucinated user profiles. 2.1% security/privacy leaks (IP addresses, file paths in vector store). Memory leak on every `Memory.from_config()` call (Issue #3376). pgvector OSS mode crashes (Issue #4727). Multi-agent isolation broken — Agent A memories recalled for Agent B (Issue #3998).

**Graphiti temporal model (ArXiv 2501.13956v1):** Bi-temporal with T (event time) and T' (ingestion time). Four timestamps per fact. 94.8% on DMR benchmark. 18.5% accuracy improvement over baseline. BUT: Neo4j dependency heavy, Docker image frozen at v0.10, Ollama broken (Issue #868), 80 open bugs.

**Letta cost problem:** Every memory read/write = LLM inference call. With 44 agents × multiple reads per task = hundreds of LLM calls per session. Incompatible with $100/month unless all memory ops run on Ollama (untested at this scale).

**HN insight (item 46891715):** User evaluated Mem0, Letta, and similar. Finding: they all solve fact storage with semantic search but none learn behavioral patterns implicitly. User corrections are highest-fidelity training signal — no framework captures structured correction events. (Atlas's `mistakes.md` + `reflexions.md` IS this.)

---

## ZenBrain Layer Mapping — What to Build

| Layer | ZenBrain Name | Implementation | Status |
|-------|--------------|----------------|--------|
| 1 | Working | LLM context window | EXISTS (no change needed) |
| 2 | Short-term | Session-scoped KV in Supabase | EXISTS (agent-state.json) |
| 3 | Episodic | pgvector + timestamps + emotional_intensity | BUILD (Phase 1) |
| 4 | Semantic | Knowledge graph in PostgreSQL (triplets + embeddings) | BUILD (Phase 4) |
| 5 | Procedural | Skill files + distilled patterns | EXISTS (48 skills in packages/swarm/) |
| 6 | Base | Identity + constitution + operating rules | EXISTS (memory/atlas/identity.md) |
| 7 | Cross-context | character_events table (cross-product) | EXISTS (schema designed) |

**5 of 7 layers already exist in manual/semi-structured form.** The work is formalization, not adoption.

---

## Recommended 5-Phase Implementation

### Phase 1 — Formalize (0 dependencies, $0)

PostgreSQL table `memory_entries`:
```sql
CREATE TABLE memory_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    layer TEXT NOT NULL CHECK (layer IN ('working','short_term','episodic','semantic','procedural','base','cross_context')),
    content TEXT NOT NULL,
    embedding VECTOR(768),
    emotional_intensity FLOAT DEFAULT 0 CHECK (emotional_intensity BETWEEN 0 AND 5),
    created_at TIMESTAMPTZ DEFAULT now(),
    last_accessed_at TIMESTAMPTZ DEFAULT now(),
    access_count INT DEFAULT 1,
    source_agent_id TEXT,
    session_id TEXT,
    is_consolidated BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'
);
```

ZenBrain decay formula as PostgreSQL function:
```sql
CREATE FUNCTION memory_decay_score(
    age_hours FLOAT, emotional_intensity FLOAT, access_count INT
) RETURNS FLOAT AS $$
    SELECT exp(-0.1 * age_hours / (1.0 + emotional_intensity * 2.0)) * ln(1 + access_count);
$$ LANGUAGE SQL IMMUTABLE;
```

Retrieval scoring:
```sql
final_score = alpha * cosine_similarity + beta * memory_decay_score(...) + gamma * emotional_intensity
```

### Phase 2 — Consolidation Daemon ($0 with Ollama)

Python cron job every 30 minutes:
1. Read entries where `is_consolidated = false` AND `layer = 'episodic'`
2. Extract patterns using Ollama (Qwen 8B, $0 cost)
3. Deduplicate against existing semantic entries (cosine similarity > 0.92)
4. Score importance: `emotional_intensity * 0.4 + surprise * 0.3 + outcome_quality * 0.3`
5. Promote high-scoring → semantic layer
6. Prune low-scoring, old entries (REM equivalent)

### Phase 3 — Temporal Facts ($0, Graphiti's idea on pgvector)

Add columns to semantic entries: `t_valid`, `t_invalid`, `t_created`, `t_expired`.
When new fact contradicts existing → invalidate old fact's `t_invalid`. No Neo4j. LLM contradiction detection via Ollama.

### Phase 4 — Knowledge Graph in PostgreSQL ($0)

Table `memory_relations`: from_entity_id, to_entity_id, relation_type, strength (Hebbian — increment on co-activation), timestamps. Multi-hop via recursive CTEs.

### Phase 5 — Cross-context (ecosystem)

`character_events` table (already designed). Each product writes events. Consolidation daemon reads them.

---

## What is Genuinely Novel (Patent-Worthy)

1. **Emotional decay in vector retrieval** — `decayMultiplier = 1.0 + emotionalIntensity × 2.0` modifying temporal decay in retrieval scoring. No production system does this.

2. **7-layer memory hierarchy** — existing systems have 2-3 layers. Formal 7-layer with defined promotion/demotion rules is novel.

3. **Hippocampal replay as cron daemon** — concept exists in research, no open-source framework implements it as deployable service with emotional weighting.

4. **Cross-context memory via shared event sourcing** — no published system connects agent memory across 5 independent products through shared event table.

---

## Multi-Agent Shared Memory (44 agents)

No framework documented at 44+ agents with shared memory. Closest: Farnsworth swarm (11 agents, event-based). Recommended: **event sourcing on existing Supabase PostgreSQL.**

Table `agent_events`: agent_id, event_type, payload (JSONB), created_at, session_id. Each agent writes events. Consolidation daemon reads + builds shared knowledge. Agents query via pgvector at session start. Cost: $0 incremental.

---

## pgvector vs Dedicated Vector DB

At startup scale (<5M vectors), **pgvector and Qdrant have identical latency** (Medium benchmark by Aleksapolskyi: within 1ms at p50). No performance reason to add infrastructure. Supabase free tier = 500 MB = 100K+ vectors at 768-dim. Migrate to dedicated DB only when vector count exceeds 10M.

---

## Sources

- [Mem0 audit: 97.8% junk](https://github.com/mem0ai/mem0/issues/4573)
- [Mem0 memory leaks](https://github.com/mem0ai/mem0/issues/3376)
- [Graphiti ArXiv paper](https://arxiv.org/html/2501.13956v1)
- [HippoRAG NeurIPS 2024](https://arxiv.org/abs/2405.14831)
- [Self-Reflective Emotional RAG](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2025.1591618/full)
- [Memory survey arxiv:2512.13564](https://arxiv.org/abs/2512.13564)
- [CodeCRDT arxiv:2510.18893](https://arxiv.org/pdf/2510.18893)
- [pgvector vs Qdrant benchmark](https://nirantk.com/writing/pgvector-vs-qdrant/)
- [ICLR 2026 MemAgents Workshop](https://openreview.net/pdf?id=U51WxL382H)
- [Anthropic Knowledge Graph MCP](https://github.com/modelcontextprotocol/servers/tree/main/src/memory)
- [MCP Memory Service](https://github.com/doobidoo/mcp-memory-service)
- [Hindsight by Vectorize](https://hindsight.vectorize.io)
- [Cognee](https://github.com/topoteretes/cognee)
- [HN: Mem0 stores facts but doesn't learn](https://news.ycombinator.com/item?id=46891715)
